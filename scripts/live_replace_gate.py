"""실제 한/글 COM 표·선택 자간 교체 Undo 게이트 측정 스크립트.
\r
docs/V3_PLUGIN_DESIGN.md §3의 되돌리기(Ctrl+Z) 기준을 실제 한/글 COM에서 측정하고,
결과를 reports/live-replace-gate.json에 원자적으로 기록한다.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import sys
from typing import Callable, ContextManager, Mapping, Sequence
from zipfile import BadZipFile, ZipFile

from defusedxml import ElementTree as ET
from docfit_core.save_guard import com_test_lock


_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_FIXTURE_ROOT = _REPO_ROOT / "tests" / "fixtures"
_DEFAULT_TABLE_FIXTURE = _REPO_ROOT / "resources" / "서식예시" / "표 서식모음.hwpx"
_DEFAULT_SELECTION_FIXTURE = _DEFAULT_FIXTURE_ROOT / "selection_spacing_sample.hwpx"
_DEFAULT_WORK_DIR = _REPO_ROOT / "reports" / "live-replace-gate"
_DEFAULT_EVIDENCE_PATH = _REPO_ROOT / "reports" / "live-replace-gate.json"
_DEFAULT_COM_LOCK_PATH = Path(r"C:\HWP_AUTODOCFIT\.com-test.lock")

_TARGET_SPACING_TEXT = "[SPACING_TARGET]"
_SENTINEL_START_TEXT = "[SENTINEL_START]"
_SENTINEL_END_TEXT = "[SENTINEL_END]"


@dataclass(frozen=True)
class GateCaseResult:
    name: str
    status: str                  # PASS | FAIL | SKIP
    undo_steps: int | None       # 정상 복원은 1
    source_sha256: str
    working_copy: str
    before_sha256: str
    after_sha256: str
    restored_sha256: str | None
    action: str                  # 관측된 GetTextFile/SetTextFile 인자 및 결과 요약
    error: str | None
    evidence_files: tuple[str, ...]


@dataclass(frozen=True)
class GateEvidence:
    schema_version: int          # 1
    gate: str                    # live_replace
    status: str                  # PASS는 모든 case PASS 및 undo_steps==1일 때만
    undo_steps: int | None
    generated_at: str            # UTC ISO-8601
    hwp_version: str
    cases: tuple[GateCaseResult, ...]
    evidence_files: tuple[str, ...]


def _build_parser() -> argparse.ArgumentParser:
    """CLI 인자 파서를 생성한다.

    사용자 원본 문서는 인자로 받지 않으며, 저장소 내부 fixture와 reports 경로만 사용한다.
    """
    parser = argparse.ArgumentParser(
        description="실제 한/글 COM 표·선택 자간 교체 Undo 게이트 측정"
    )
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=_DEFAULT_FIXTURE_ROOT,
        help="시험 fixture 루트 디렉터리 (기본값: tests/fixtures)",
    )
    parser.add_argument(
        "--table-fixture",
        type=Path,
        default=_DEFAULT_TABLE_FIXTURE,
        help="표 단위 변환 시험 fixture (기본값: resources/서식예시/표 서식모음.hwpx)",
    )
    parser.add_argument(
        "--selection-fixture",
        type=Path,
        default=_DEFAULT_SELECTION_FIXTURE,
        help="선택 자간 시험 fixture (기본값: tests/fixtures/selection_spacing_sample.hwpx)",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=_DEFAULT_WORK_DIR,
        help="임시 작업 및 복사본 보관 디렉터리 (기본값: reports/live-replace-gate)",
    )
    parser.add_argument(
        "--evidence",
        type=Path,
        default=_DEFAULT_EVIDENCE_PATH,
        help="최종 게이트 증거 JSON 출력 경로 (기본값: reports/live-replace-gate.json)",
    )
    return parser


def _sha256(path: Path) -> str:
    """파일의 SHA-256 해시를 반환한다."""
    if not path.is_file():
        return ""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _copy_fixture(source: Path, work_dir: Path) -> Path:
    """원본 fixture를 수정하지 않도록 작업 디렉터리로 복사한다."""
    if not source.is_file():
        raise FileNotFoundError(f"Fixture 파일을 찾을 수 없습니다: {source}")
    work_dir.mkdir(parents=True, exist_ok=True)
    target = work_dir / f"{source.stem}_work{source.suffix}"
    shutil.copy2(source, target)
    return target


def _inspect_table_fixture(path: Path) -> tuple[bool, str]:
    """표 단위 시험 fixture의 적격성(반복 구조의 표 존재 여부)을 검증한다.

    설계 기준:
    - 반드시 유효한 .hwpx 파일이어야 함.
    - HWPX ZIP 및 XML 파싱 오류 시 fallback 없이 즉시 FAIL 처리.
    - 내부에 최소 2개 이상의 행(hp:tr)을 가진 반복 구조의 표(hp:tbl)가 존재해야 함.
    """
    if not path.is_file():
        return False, f"표 fixture 파일이 존재하지 않습니다: {path}"
    if path.suffix.lower() != ".hwpx":
        return False, f"표 fixture는 반드시 .hwpx 형식이어야 합니다: {path.name}"

    try:
        with ZipFile(path, "r") as archive:
            section_names = [
                name for name in archive.namelist()
                if name.startswith("Contents/section") and name.endswith(".xml")
            ]
            if not section_names:
                return False, "표 fixture HWPX 내에 section XML 파일이 존재하지 않습니다."

            hp = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
            found_repeat_table = False

            for sname in section_names:
                raw_xml = archive.read(sname)
                root = ET.fromstring(raw_xml)
                tables = root.findall(f".//{hp}tbl")
                for tbl in tables:
                    rows = tbl.findall(f".//{hp}tr")
                    if len(rows) >= 2:
                        found_repeat_table = True
                        break
                if found_repeat_table:
                    break

            if found_repeat_table:
                return True, "적격 표 fixture (반복 행 포함 표 검증 완료)"
            return False, "표 fixture 내에 반복 구조의 표(hp:tbl 및 2개 이상의 hp:tr)가 없습니다."
    except BadZipFile as bzf:
        return False, f"표 fixture가 유효한 ZIP/HWPX 아카이브가 아닙니다: {bzf}"
    except ET.ParseError as pe:
        return False, f"표 fixture XML 파싱 오류: {pe}"
    except Exception as exc:
        return False, f"표 fixture 적격성 검사 중 오류 발생: {exc}"


def _inspect_selection_fixture(path: Path) -> tuple[bool, str]:
    """선택 자간 시험 fixture의 적격성(명시 대상 문자열 및 선택 외 sentinel 존재)을 검증한다.

    설계 기준:
    - 반드시 유효한 .hwpx 파일이어야 함.
    - HWPX ZIP 및 XML 파싱 오류 시 fallback 없이 즉시 FAIL 처리.
    - 본문 내에 정확한 _TARGET_SPACING_TEXT, _SENTINEL_START_TEXT, _SENTINEL_END_TEXT가 모두 존재해야 함.
    """
    if not path.is_file():
        return False, f"선택 자간 fixture 파일이 존재하지 않습니다: {path}"
    if path.suffix.lower() != ".hwpx":
        return False, f"선택 자간 fixture는 반드시 .hwpx 형식이어야 합니다: {path.name}"

    try:
        with ZipFile(path, "r") as archive:
            section_names = [
                name for name in archive.namelist()
                if name.startswith("Contents/section") and name.endswith(".xml")
            ]
            if not section_names:
                return False, "선택 자간 fixture HWPX 내에 section XML 파일이 존재하지 않습니다."

            hp = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
            all_texts: list[str] = []

            for sname in section_names:
                raw_xml = archive.read(sname)
                root = ET.fromstring(raw_xml)
                for node in root.findall(f".//{hp}t"):
                    if node.text:
                        all_texts.append(node.text)

            full_text = "".join(all_texts)
            has_target = _TARGET_SPACING_TEXT in full_text
            has_sentinel_start = _SENTINEL_START_TEXT in full_text
            has_sentinel_end = _SENTINEL_END_TEXT in full_text

            if has_target and has_sentinel_start and has_sentinel_end:
                return True, "적격 자간 fixture (대상 문자열 및 sentinel 검증 완료)"

            missing: list[str] = []
            if not has_target:
                missing.append(_TARGET_SPACING_TEXT)
            if not has_sentinel_start:
                missing.append(_SENTINEL_START_TEXT)
            if not has_sentinel_end:
                missing.append(_SENTINEL_END_TEXT)
            return False, f"선택 자간 fixture에 필수 문자열이 누락되었습니다: {missing}"
    except BadZipFile as bzf:
        return False, f"선택 자간 fixture가 유효한 ZIP/HWPX 아카이브가 아닙니다: {bzf}"
    except ET.ParseError as pe:
        return False, f"선택 자간 fixture XML 파싱 오류: {pe}"
    except Exception as exc:
        return False, f"선택 자간 fixture 적격성 검사 중 오류 발생: {exc}"


def _validate_case_result(c_dict: Mapping[str, object], resolved_root: Path) -> None:
    """개별 case 결과의 계약을 fail-closed 검증한다."""
    name = c_dict.get("name")
    if name not in {"table_unit", "selection_spacing"}:
        raise ValueError(f"유효하지 않은 case 이름: {name}")

    status = c_dict.get("status")
    if status == "PASS":
        if c_dict.get("undo_steps") != 1:
            raise ValueError(f"PASS case의 undo_steps는 1이어야 합니다: {name}")

        source_sha = c_dict.get("source_sha256")
        if not isinstance(source_sha, str) or len(source_sha) != 64:
            raise ValueError(f"case의 source_sha256가 유효한 64글자 해시가 아닙니다: {name}")

        working_copy = c_dict.get("working_copy")
        if not isinstance(working_copy, str) or not working_copy.strip():
            raise ValueError(f"case의 working_copy 경로가 누락되었습니다: {name}")
        wc_path = Path(working_copy).resolve()
        try:
            wc_path.relative_to(resolved_root)
        except ValueError:
            raise ValueError(f"working_copy가 저장소 외부로 탈출했습니다: {working_copy}")
        if not wc_path.is_file():
            raise ValueError(f"working_copy 파일이 실존하지 않습니다: {working_copy}")

        b_hash = c_dict.get("before_sha256")
        a_hash = c_dict.get("after_sha256")
        r_hash = c_dict.get("restored_sha256")
        if not b_hash or not a_hash or not r_hash:
            raise ValueError(f"case의 해시 정보가 누락되었습니다: {name}")
        if b_hash == a_hash:
            raise ValueError(f"적용 전후 해시가 동일하여 실제 변경이 일어나지 않았습니다: {name}")

        # 복원 판정: 바이트 해시 일치 또는 (비결정적 메타데이터 차이 시) 유효한 의미 구조 완전 일치
        if r_hash != b_hash:
            # 해시가 다르면 action에 의미 복원 성공 증거가 명시되어 있어야 함
            action_text = str(c_dict.get("action", ""))
            if "semantic_restored=True" not in action_text:
                raise ValueError(
                    f"Undo 후 해시({r_hash})가 적용 전 해시({b_hash})와 불일치하며 "
                    f"의미 복원 증거도 부족합니다: {name}"
                )

        action = c_dict.get("action")
        if not isinstance(action, str) or not action.strip():
            raise ValueError(f"case의 액션 로그가 비어 있습니다: {name}")

        if c_dict.get("error") is not None:
            raise ValueError(f"PASS case에는 error가 없어야 합니다: {name}")

        case_ev_files = c_dict.get("evidence_files")
        if not isinstance(case_ev_files, (list, tuple)) or not case_ev_files:
            raise ValueError(f"case의 evidence_files가 비어 있습니다: {name}")

        for cef in case_ev_files:
            if not isinstance(cef, str) or not cef.strip():
                raise ValueError(f"case 증거 파일 경로는 비어 있지 않은 문자열이어야 합니다: {name}")
            cef_path = Path(cef)
            resolved_cef = cef_path.resolve() if cef_path.is_absolute() else (resolved_root / cef_path).resolve()
            try:
                resolved_cef.relative_to(resolved_root)
            except ValueError:
                raise ValueError(f"case 증거 파일이 저장소 외부로 탈출했습니다: {cef}")
            if not resolved_cef.is_file():
                raise ValueError(f"case 증거 파일이 실제로 존재하지 않습니다: {cef}")


def _validate_evidence(payload: Mapping[str, object], repo_root: Path) -> None:
    """증거 데이터가 G2 is_undo_gate_passed 계약과 일치하는지 fail-closed 검증한다."""
    if not isinstance(payload, Mapping):
        raise ValueError("Payload는 Mapping 객체여야 합니다.")
    if payload.get("schema_version") != 1:
        raise ValueError("schema_version은 1이어야 합니다.")
    if payload.get("gate") != "live_replace":
        raise ValueError("gate는 'live_replace'여야 합니다.")

    status = payload.get("status")
    resolved_root = repo_root.resolve()

    if status == "PASS":
        if payload.get("undo_steps") != 1:
            raise ValueError("PASS 증거의 undo_steps는 정수 1이어야 합니다.")

        cases = payload.get("cases")
        if not isinstance(cases, (list, tuple)) or len(cases) != 2:
            raise ValueError("PASS 증거는 정확히 2개의 cases(table_unit, selection_spacing)를 포함해야 합니다.")

        case_names = set()
        for c in cases:
            c_dict = asdict(c) if hasattr(c, "__dataclass_fields__") else (c if isinstance(c, dict) else {})
            name = c_dict.get("name")
            case_names.add(name)
            if c_dict.get("status") != "PASS":
                raise ValueError(f"모든 case가 PASS여야 합니다: {name}")
            _validate_case_result(c_dict, resolved_root)

        if case_names != {"table_unit", "selection_spacing"}:
            raise ValueError(f"cases는 'table_unit'과 'selection_spacing'이어야 합니다: {case_names}")

        evidence_files = payload.get("evidence_files")
        if not isinstance(evidence_files, (list, tuple)) or not evidence_files:
            raise ValueError("PASS 증거는 실존하는 evidence_files를 포함해야 합니다.")

        for ef in evidence_files:
            if not isinstance(ef, str) or not ef.strip():
                raise ValueError("증거 파일 경로는 비어 있지 않은 문자열이어야 합니다.")
            ef_path = Path(ef)
            resolved_ef = ef_path.resolve() if ef_path.is_absolute() else (resolved_root / ef_path).resolve()
            try:
                resolved_ef.relative_to(resolved_root)
            except ValueError:
                raise ValueError(f"증거 파일이 저장소 외부로 탈출했습니다: {ef}")
            if not resolved_ef.is_file():
                raise ValueError(f"증거 파일이 실제로 존재하지 않습니다: {ef}")
    else:
        # FAIL 증거에 대해서도 기본적인 경로 탈출 방어
        evidence_files = payload.get("evidence_files")
        if isinstance(evidence_files, (list, tuple)):
            for ef in evidence_files:
                if isinstance(ef, str) and ef.strip():
                    ef_path = Path(ef)
                    resolved_ef = ef_path.resolve() if ef_path.is_absolute() else (resolved_root / ef_path).resolve()
                    try:
                        resolved_ef.relative_to(resolved_root)
                    except ValueError:
                        raise ValueError(f"증거 파일이 저장소 외부로 탈출했습니다: {ef}")


def _atomic_write_json(path: Path, payload: GateEvidence, repo_root: Path = _REPO_ROOT) -> None:
    """원자적으로 임시 파일을 거쳐 JSON 증거를 쓴다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(payload)
    if payload.status == "PASS":
        _validate_evidence(data, repo_root)

    tmp_path = path.with_name(f"{path.name}.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def _make_hwp_dispatch(dispatch_ex: Callable[[str], object] | None = None) -> object:
    """격리된 HWPFrame.HwpObject 인스턴스를 생성한다.

    Dispatch, ROT, GetActiveObject는 일절 사용하지 않으며 DispatchEx만 사용한다.
    비Windows 환경에서는 dispatch_ex가 주어지지 않은 경우 COM 생성을 차단한다.
    보안 모듈 등록 실패 시 모달 대기 방지를 위해 즉시 예외를 발생시킨다.
    """
    if dispatch_ex is not None:
        app = dispatch_ex("HWPFrame.HwpObject")
    else:
        if sys.platform != "win32":
            raise RuntimeError("macOS 및 비Windows 환경에서는 실제 한/글 COM을 실행할 수 없습니다.")
        import win32com.client
        app = win32com.client.DispatchEx("HWPFrame.HwpObject")

    try:
        if hasattr(app, "XHwpWindows") and hasattr(app.XHwpWindows, "Item"):
            app.XHwpWindows.Item(0).Visible = False
    except Exception:
        pass

    module_name = "HwpAutoDocFitSecurity"
    try:
        from docfit_core.format_samples import LEGACY_REGISTRY_VALUE, REGISTRY_VALUE, APP_HOME
        dll_path = APP_HOME / "dll" / "HwpAutoDocFitSecurity.dll"
        module_name = REGISTRY_VALUE if dll_path.is_file() else LEGACY_REGISTRY_VALUE
    except Exception:
        pass

    if hasattr(app, "RegisterModule"):
        reg_ok = False
        try:
            reg_ok = bool(app.RegisterModule("FilePathCheckDLL", module_name))
        except Exception as exc:
            raise RuntimeError(
                f"한/글 보안 모듈 등록 중 예외 발생({module_name}): {exc}. "
                "파일 열기 모달 대기 위험 방지를 위해 자동 FAIL 처리합니다."
            ) from exc

        if not reg_ok:
            raise RuntimeError(
                f"한/글 보안 모듈 등록 실패(반환값={reg_ok}, 모듈={module_name}). "
                "파일 열기 모달 대기 위험 방지를 위해 자동 FAIL 처리합니다."
            )

    return app


def _open_isolated_copy(app: object, path: Path) -> None:
    """시험 복사본 문서를 연다. 실패 시 사람 입력을 기다리지 않고 예외를 던진다."""
    if not path.is_file():
        raise FileNotFoundError(f"열려는 복사본 파일이 없습니다: {path}")
    ext = path.suffix.lower()
    fmt = "HWPX" if ext == ".hwpx" else ("HWP" if ext == ".hwp" else "")
    opened = False
    if hasattr(app, "Open"):
        try:
            opened = app.Open(str(path), fmt, "forceopen:true")
        except Exception as exc:
            raise RuntimeError(f"격리 복사본 열기 중 예외 발생: {exc}") from exc
    if opened is False:
        raise RuntimeError(f"한/글이 격리 복사본을 열지 못했습니다: {path}")


def _extract_hwpx_semantics(path: Path) -> dict[str, object]:
    """HWPX 아카이브에서 텍스트, 표 구조, 자간 속성을 신뢰성 있게 추출한다."""
    if not path.is_file() or path.suffix.lower() != ".hwpx":
        return {"is_valid": False}
    try:
        with ZipFile(path, "r") as archive:
            section_names = [n for n in archive.namelist() if n.startswith("Contents/section") and n.endswith(".xml")]
            if not section_names:
                return {"is_valid": False}
            tables_summary = []
            char_spacings = []
            all_texts = []
            hp = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"

            for sname in section_names:
                root = ET.fromstring(archive.read(sname))
                for t_node in root.findall(f".//{hp}t"):
                    if t_node.text:
                        all_texts.append(t_node.text)

                for tbl_idx, tbl in enumerate(root.findall(f".//{hp}tbl")):
                    rows = tbl.findall(f".//{hp}tr")
                    row_cells = []
                    for r in rows:
                        cells = r.findall(f".//{hp}tc")
                        cell_texts = []
                        for c in cells:
                            ctexts = [tn.text for tn in c.findall(f".//{hp}t") if tn.text]
                            cell_texts.append("".join(ctexts))
                        row_cells.append(cell_texts)
                    tables_summary.append({
                        "tbl_index": tbl_idx,
                        "rows_count": len(rows),
                        "grid": row_cells,
                    })

            # header.xml에서 charPr spacing 추출 시도
            if "Contents/header.xml" in archive.namelist():
                hroot = ET.fromstring(archive.read("Contents/header.xml"))
                hh = "{http://www.hancom.co.kr/hwpml/2011/head}"
                for cp in hroot.findall(f".//{hh}charPr"):
                    cid = cp.attrib.get("id", "")
                    sp = cp.attrib.get("spacing", "0")
                    char_spacings.append(f"{cid}:{sp}")

            full_text = "".join(all_texts)
            has_sentinel_start = _SENTINEL_START_TEXT in full_text
            has_sentinel_end = _SENTINEL_END_TEXT in full_text
            has_target = _TARGET_SPACING_TEXT in full_text

            is_valid = bool(full_text or tables_summary)

            return {
                "is_valid": is_valid,
                "text": full_text,
                "tables": tables_summary,
                "char_spacings": char_spacings,
                "has_sentinel_start": has_sentinel_start,
                "has_sentinel_end": has_sentinel_end,
                "has_target": has_target,
            }
    except Exception:
        return {"is_valid": False}


def _capture_semantic_snapshot(app: object, path: Path) -> dict[str, object]:
    """문서의 의미적 상태(본문 텍스트, 표 구조, 자간 속성, 문맥)를 신뢰성 검증과 함께 캡처한다."""
    text_content = ""
    if hasattr(app, "GetTextFile"):
        try:
            text_content = str(app.GetTextFile("TEXT", ""))
        except Exception:
            text_content = ""
    if not text_content and hasattr(app, "_state"):
        text_content = str(getattr(app, "_state"))

    in_table = False
    try:
        parent = getattr(app, "ParentCtrl", None)
        if parent is not None and getattr(parent, "CtrlID", "") == "tbl":
            in_table = True
    except Exception:
        in_table = False

    selected = False
    try:
        selected = bool(getattr(app, "SelectionMode", 0))
    except Exception:
        selected = False

    # HWPX 파일 수준의 상세 의미 구조 추출
    hwpx_meta = _extract_hwpx_semantics(path) if path.is_file() else {"is_valid": False}
    file_valid = hwpx_meta.get("is_valid", False)

    effective_text = text_content or str(hwpx_meta.get("text", ""))
    is_valid = bool(effective_text) or file_valid

    return {
        "is_valid": is_valid,
        "text": effective_text,
        "in_table": in_table,
        "selected": selected,
        "tables": hwpx_meta.get("tables", []),
        "char_spacings": hwpx_meta.get("char_spacings", []),
        "has_sentinel_start": hwpx_meta.get("has_sentinel_start", False),
        "has_sentinel_end": hwpx_meta.get("has_sentinel_end", False),
    }


def _capture_document_state(app: object, path: Path, label: str) -> tuple[Path, str, dict[str, object]]:
    """현재 문서의 상태를 스냅샷 파일로 저장하고 SHA-256 해시 및 의미 상태를 반환한다."""
    snapshot_path = path.parent / f"{path.stem}_{label}{path.suffix}"
    saved = False
    if hasattr(app, "SaveAs"):
        try:
            res = app.SaveAs(str(snapshot_path), "", "")
            if res is not False and snapshot_path.is_file():
                saved = True
        except Exception:
            saved = False

    if not saved:
        semantic = _capture_semantic_snapshot(app, path)
        text_content = str(semantic.get("text", ""))
        if text_content:
            snapshot_path.write_text(text_content, encoding="utf-8")
        elif path.is_file():
            shutil.copy2(path, snapshot_path)
        else:
            snapshot_path.write_text("", encoding="utf-8")

    h = _sha256(snapshot_path)
    from zipfile import is_zipfile
    ref_path = snapshot_path if (snapshot_path.is_file() and is_zipfile(snapshot_path)) else path
    semantic = _capture_semantic_snapshot(app, ref_path)
    return snapshot_path, h, semantic


def _run_undo_once(
    app: object,
    expected_semantic: dict[str, object],
    working_copy: Path,
) -> tuple[bool, int, dict[str, object]]:
    """app.HAction.Run('Undo')를 정확히 1회 호출하고 필수 의미 복원을 엄격히 검증한다.

    지적 4 반영:
    - 필수 의미 추출 항목(is_valid)이 신뢰 가능하게 존재할 때만 의미 비교를 인정한다.
    - 추출 실패로 인한 빈 값과 빈 값의 일치는 복원 성공으로 인정하지 않는다.
    """
    undo_count = 0
    if hasattr(app, "HAction") and hasattr(app.HAction, "Run"):
        app.HAction.Run("Undo")
        undo_count = 1
    elif hasattr(app, "Run"):
        app.Run("Undo")
        undo_count = 1
    else:
        return False, 0, {"is_valid": False}

    current_semantic = _capture_semantic_snapshot(app, working_copy)

    # 필수 의미 항목 신뢰성 검사: 둘 다 유효한 데이터가 존재해야 함
    if not expected_semantic.get("is_valid", False) or not current_semantic.get("is_valid", False):
        return False, undo_count, current_semantic

    # 본문 텍스트 또는 표 데이터가 전혀 비어있으면 인정 불가
    if not expected_semantic.get("text") and not expected_semantic.get("tables"):
        return False, undo_count, current_semantic

    # 텍스트, 표 구조, 자간 속성, 문맥 의미 복원 검증
    text_ok = current_semantic.get("text") == expected_semantic.get("text")
    table_ok = current_semantic.get("tables") == expected_semantic.get("tables")
    spacings_ok = current_semantic.get("char_spacings") == expected_semantic.get("char_spacings")
    context_ok = (
        current_semantic.get("in_table") == expected_semantic.get("in_table")
        and current_semantic.get("selected") == expected_semantic.get("selected")
    )
    sentinel_ok = (
        current_semantic.get("has_sentinel_start") == expected_semantic.get("has_sentinel_start")
        and current_semantic.get("has_sentinel_end") == expected_semantic.get("has_sentinel_end")
    )

    restored = text_ok and table_ok and spacings_ok and context_ok and sentinel_ok
    return restored, undo_count, current_semantic


def _move_cursor_to_table(app: object) -> bool:
    """문서 내의 대상 표로 커서를 이동하고 표 내부 위치(ParentCtrl.CtrlID == 'tbl')를 확보한다.

    지적 3 반영:
    - 새 격리 인스턴스에서 fixture를 연 후, 커서를 명시적으로 대상 표 내부로 이동시킨다.
    - 표 내부 커서 상태를 확보하지 못하면 False를 반환한다.
    """
    # 1. 이미 커서가 표 안에 있는 경우
    try:
        parent = getattr(app, "ParentCtrl", None)
        if parent is not None and getattr(parent, "CtrlID", "") == "tbl":
            return True
    except Exception:
        pass

    # 2. Fake COM 또는 모의 객체의 명시적 move_to_table 훅 지원
    if hasattr(app, "move_to_table") and callable(app.move_to_table):
        return bool(app.move_to_table())

    # 3. 한/글 COM Action을 통한 표 탐색 및 커서 이동
    # 문서 시작으로 이동
    if hasattr(app, "HAction") and hasattr(app.HAction, "Run"):
        try:
            app.HAction.Run("MoveDocBegin")
        except Exception:
            pass
    elif hasattr(app, "Run"):
        try:
            app.Run("MoveDocBegin")
        except Exception:
            pass

    # FindCtrl을 통해 다음 컨트롤(표)로 이동 시도
    if hasattr(app, "FindCtrl"):
        for _ in range(10):
            found = False
            try:
                found = bool(app.FindCtrl())
            except Exception:
                break
            if not found:
                break

            # 컨트롤 내부로 진입 (TableCellBlock 등)
            for act in ("TableCellBlock", "MoveDown", "MoveRight"):
                try:
                    if hasattr(app, "HAction") and hasattr(app.HAction, "Run"):
                        app.HAction.Run(act)
                    elif hasattr(app, "Run"):
                        app.Run(act)
                except Exception:
                    pass

                try:
                    parent = getattr(app, "ParentCtrl", None)
                    if parent is not None and getattr(parent, "CtrlID", "") == "tbl":
                        # 블록 선택 상태 해제
                        if hasattr(app, "Run"):
                            app.Run("Cancel")
                        return True
                except Exception:
                    pass

    # 최종 검증
    try:
        parent = getattr(app, "ParentCtrl", None)
        return bool(parent is not None and getattr(parent, "CtrlID", "") == "tbl")
    except Exception:
        return False


def _setup_selection_in_app(app: object, target_text: str = _TARGET_SPACING_TEXT) -> bool:
    """한/글 COM에서 대상 문자열을 찾아 정확한 선택 범위를 설정한다.

    지적 2 반영:
    - 대상 검색/선택 성공 여부를 엄격히 확인하고 반환한다.
    """
    if hasattr(app, "select_target_text") and callable(app.select_target_text):
        return bool(app.select_target_text(target_text))

    # COM FindReplace 액션을 통한 검색 및 블록 선택
    if hasattr(app, "HAction") and hasattr(app, "HParameterSet"):
        try:
            hset = getattr(app.HParameterSet, "HFindReplace", None)
            if hset is not None:
                app.HAction.GetDefault("RepeatFind", hset.HSet)
                hset.FindString = target_text
                hset.Direction = 0
                hset.IgnoreMessage = 1
                if app.HAction.Execute("RepeatFind", hset.HSet):
                    return bool(getattr(app, "SelectionMode", 0))
        except Exception:
            pass

    return bool(getattr(app, "SelectionMode", 0))


def _run_table_unit_case(
    app: object,
    fixture: Path,
    work_dir: Path,
    table_transformer: Callable[[bytes | str], bytes | str] | None = None,
) -> GateCaseResult:
    """표 단위 1단위 변환 및 단일 교체 후 Undo 1회 복원을 계측한다.

    지적 1, 3 반영:
    - fixture 사본을 연 뒤 표 내부로 커서를 이동하고 실제 대상 표 구조를 검증.
    - 임의의 문자열/바이트(_unit+1) 덧붙이기 금지.
    - 운영 어댑터 실측 인자·응답을 계측하되, 운영 변환 엔진을 적용할 수 없으면 해당 case를 FAIL로 종료.
    """
    name = "table_unit"
    case_dir = work_dir / name
    case_dir.mkdir(parents=True, exist_ok=True)
    case_json_path = work_dir / f"{name}.json"
    ev_files: list[str] = [str(case_json_path.resolve())]

    source_hash = _sha256(fixture)
    working_copy = _copy_fixture(fixture, case_dir)
    ev_files.append(str(working_copy.resolve()))

    action_record = ""
    error_msg = None
    status = "FAIL"
    undo_steps = None
    before_hash = ""
    after_hash = ""
    restored_hash = None

    try:
        _open_isolated_copy(app, working_copy)

        # 1. 대상 표로 커서 이동 및 표 내부 구조 검증 (지적 3)
        moved = _move_cursor_to_table(app)
        if not moved:
            error_msg = "열린 fixture 사본에서 대상 표 내부로 커서를 이동하지 못했습니다 (NOT_IN_TABLE)."
            status = "FAIL"
            action_record = "Cursor move to table failed: NOT_IN_TABLE"
        else:
            before_path, before_hash, before_semantic = _capture_document_state(app, working_copy, "before")
            ev_files.append(str(before_path.resolve()))

            action_parts = []
            replaced = False

            # 2. G2 어댑터 및 운영 변환 엔진 실측 호출 계측 (지적 1)
            raw_block: bytes | str | None = None
            try:
                from docfit_live import link as live_link
                from docfit_live.link import LiveLinkError
                try:
                    block = live_link.export_table_block(app)
                    raw_block = block
                    action_parts.append(f"live_link.export_table_block(app) -> {len(block)} bytes")
                except NotImplementedError as nie:
                    action_parts.append(f"live_link.export_table_block(app) -> NotImplementedError({nie})")
                except LiveLinkError as lle:
                    action_parts.append(f"live_link.export_table_block error: {lle.code} - {lle}")
            except Exception as exc:
                action_parts.append(f"live_link import/call failed: {exc}")

            if raw_block is None:
                error_msg = "docfit_live.link 표 블록 export가 구현되지 않아 게이트를 닫았습니다."

            # 3. 표 단위 변환 엔진 적용 (임의 알고리즘 금지)
            transformed_block: bytes | str | None = None
            if table_transformer is not None and raw_block:
                try:
                    transformed_block = table_transformer(raw_block)
                    action_parts.append("table_transformer(raw_block) applied")
                except Exception as exc:
                    action_parts.append(f"table_transformer failed: {exc}")
                    error_msg = f"주입된 표 변환기 실행 실패: {exc}"
            elif raw_block:
                # 운영 docfit_live.service 또는 docfit_core 엔진 적용 시도
                try:
                    from docfit_live.service import LiveLinkService
                    svc = LiveLinkService(sessions=lambda: [], titles=lambda: [], com_init=False)
                    transformed_block = svc._transform_table_block(raw_block, delta=1)
                    action_parts.append("LiveLinkService._transform_table_block(delta=1) applied")
                except NotImplementedError as nie:
                    action_parts.append(f"LiveLinkService._transform_table_block -> NotImplementedError({nie})")
                    # 임의 알고리즘 대체 금지 -> 명시적 FAIL
                    error_msg = (
                        "표 단위 변환 운영 엔진 미구현 (NotImplementedError). "
                        "설계에 따라 임의 알고리즘으로 대체하지 않고 FAIL로 종료합니다."
                    )
                except Exception as exc:
                    action_parts.append(f"LiveLinkService._transform_table_block failed: {exc}")
                    error_msg = str(exc)

            # 4. 단일 교체 적용 (SetTextFile)
            if transformed_block and not error_msg:
                # G2 live_link.replace_table_block 시도
                try:
                    from docfit_live import link as live_link
                    res = live_link.replace_table_block(app, transformed_block, expected=live_link.context(app))
                    action_parts.append(f"live_link.replace_table_block(app, ...) -> {res}")
                    replaced = bool(res.get("ok", True))
                except Exception as exc:
                    action_parts.append(f"live_link.replace_table_block -> {type(exc).__name__}({exc})")
                    error_msg = str(exc)

            if not replaced and not error_msg:
                error_msg = "표 단위 변환 및 단일 교체 API 미실측 또는 미구현 (FAIL closed)"

            action_record = "; ".join(action_parts)

            if replaced:
                after_path, after_hash, after_semantic = _capture_document_state(app, working_copy, "after")
                ev_files.append(str(after_path.resolve()))

                if after_hash == before_hash:
                    status = "FAIL"
                    error_msg = "표 교체 실행 후 문서 상태가 변경되지 않았습니다 (no-op)."
                else:
                    restored, steps, restored_semantic = _run_undo_once(app, before_semantic, working_copy)
                    undo_steps = steps
                    restored_path, restored_hash, _ = _capture_document_state(app, working_copy, "restored")
                    ev_files.append(str(restored_path.resolve()))

                    if steps == 1 and restored:
                        status = "PASS"
                        error_msg = None
                        action_record += f"; undo_steps=1; semantic_restored=True"
                    else:
                        status = "FAIL"
                        if steps != 1:
                            error_msg = f"Undo 호출 횟수가 1이 아닙니다: {steps}"
                        else:
                            error_msg = "Undo 1회 실행 후 적용 전 상태로 온전히 복원되지 않았습니다 (의미적 불일치)."
            else:
                status = "FAIL"

    except Exception as exc:
        error_msg = str(exc)
        status = "FAIL"

    case_result = GateCaseResult(
        name=name,
        status=status,
        undo_steps=undo_steps,
        source_sha256=source_hash,
        working_copy=str(working_copy.resolve()),
        before_sha256=before_hash,
        after_sha256=after_hash,
        restored_sha256=restored_hash,
        action=action_record,
        error=error_msg,
        evidence_files=tuple(ev_files),
    )

    with open(case_json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(case_result), f, indent=2, ensure_ascii=False)

    return case_result


def _run_selection_spacing_case(
    app: object,
    fixture: Path,
    work_dir: Path,
    selection_transformer: Callable[[bytes | str], bytes | str] | None = None,
) -> GateCaseResult:
    """선택 자간 변환 및 단일 교체 후 Undo 1회 복원을 계측한다.

    지적 1, 2 반영:
    - _setup_selection_in_app 반환값을 반드시 확인하고, 실제 추출된 선택 블록이 명시 대상과 일치하는지 검증.
    - 불일치 시 교체 없이 FAIL 종료.
    - 임의의 문자열/바이트(_spacing-1) 덧붙이기 금지.
    - 운영 자간 엔진을 명시적 적용할 수 없으면 해당 case를 FAIL로 종료.
    """
    name = "selection_spacing"
    case_dir = work_dir / name
    case_dir.mkdir(parents=True, exist_ok=True)
    case_json_path = work_dir / f"{name}.json"
    ev_files: list[str] = [str(case_json_path.resolve())]

    source_hash = _sha256(fixture)
    working_copy = _copy_fixture(fixture, case_dir)
    ev_files.append(str(working_copy.resolve()))

    action_record = ""
    error_msg = None
    status = "FAIL"
    undo_steps = None
    before_hash = ""
    after_hash = ""
    restored_hash = None

    try:
        _open_isolated_copy(app, working_copy)

        # 1. 대상 문자열의 선택 설정 및 검증 (지적 2)
        selection_ok = _setup_selection_in_app(app, _TARGET_SPACING_TEXT)
        if not selection_ok:
            error_msg = "열린 fixture 사본에서 명시된 문자열 선택 범위를 잡지 못했습니다 (_setup_selection_in_app 실패)."
            status = "FAIL"
            action_record = "Selection setup failed: _setup_selection_in_app returned False"
        else:
            # 선택된 실제 블록 내용 추출 및 명시 대상 일치 확인
            extracted_text = ""
            if hasattr(app, "GetTextFile"):
                try:
                    extracted_text = str(app.GetTextFile("TEXT", "saveblock") or "")
                except Exception:
                    extracted_text = ""

            # 추출된 텍스트가 대상과 일치하지 않는 경우 불일치 처리
            if extracted_text and _TARGET_SPACING_TEXT not in extracted_text:
                error_msg = (
                    f"선택 영역 내용이 대상 문자열('{_TARGET_SPACING_TEXT}')과 일치하지 않습니다: "
                    f"'{extracted_text[:50]}'"
                )
                status = "FAIL"
                action_record = f"Selection content mismatch: got '{extracted_text[:50]}'"
            else:
                before_path, before_hash, before_semantic = _capture_document_state(app, working_copy, "before")
                ev_files.append(str(before_path.resolve()))

                action_parts = []
                replaced = False

                # 2. G2 어댑터 및 운영 자간 엔진 계측 (지적 1)
                raw_block: bytes | str | None = None
                try:
                    from docfit_live import link as live_link
                    from docfit_live.link import LiveLinkError
                    try:
                        block = live_link.export_selection_block(app)
                        raw_block = block
                        action_parts.append(f"live_link.export_selection_block(app) -> {len(block)} bytes")
                    except NotImplementedError as nie:
                        action_parts.append(f"live_link.export_selection_block -> NotImplementedError({nie})")
                    except LiveLinkError as lle:
                        action_parts.append(f"live_link.export_selection_block error: {lle.code} - {lle}")
                except Exception as exc:
                    action_parts.append(f"live_link import/call failed: {exc}")

                if raw_block is None:
                    error_msg = "docfit_live.link 선택 블록 export가 구현되지 않아 게이트를 닫았습니다."

                # 3. 자간 변환 엔진 적용 (임의 알고리즘 금지)
                transformed_block: bytes | str | None = None
                if selection_transformer is not None and raw_block:
                    try:
                        transformed_block = selection_transformer(raw_block)
                        action_parts.append("selection_transformer(raw_block) applied")
                    except Exception as exc:
                        action_parts.append(f"selection_transformer failed: {exc}")
                        error_msg = f"주입된 자간 변환기 실행 실패: {exc}"
                elif raw_block:
                    # 운영 LiveLinkService 자간 엔진 적용 시도
                    try:
                        from docfit_live.service import LiveLinkService
                        svc = LiveLinkService(sessions=lambda: [], titles=lambda: [], com_init=False)
                        transformed_block = svc._transform_selection_block(raw_block)
                        action_parts.append("LiveLinkService._transform_selection_block applied")
                    except NotImplementedError as nie:
                        action_parts.append(f"LiveLinkService._transform_selection_block -> NotImplementedError({nie})")
                        # 임의 알고리즘 대체 금지 -> 명시적 FAIL
                        error_msg = (
                            "선택 자간 변환 운영 엔진 미구현 (NotImplementedError). "
                            "설계에 따라 임의 알고리즘으로 대체하지 않고 FAIL로 종료합니다."
                        )
                    except Exception as exc:
                        action_parts.append(f"LiveLinkService._transform_selection_block failed: {exc}")
                        error_msg = str(exc)

                # 4. 단일 교체 적용 (SetTextFile)
                if transformed_block and not error_msg:
                    # G2 live_link.replace_selection_block 시도
                    try:
                        from docfit_live import link as live_link
                        res = live_link.replace_selection_block(
                            app, transformed_block, expected=live_link.context(app)
                        )
                        action_parts.append(f"live_link.replace_selection_block(app, ...) -> {res}")
                        replaced = bool(res.get("ok", True))
                    except Exception as exc:
                        action_parts.append(f"live_link.replace_selection_block -> {type(exc).__name__}({exc})")
                        error_msg = str(exc)

                if not replaced and not error_msg:
                    error_msg = "선택 자간 변환 및 단일 교체 API 미실측 또는 미구현 (FAIL closed)"

                action_record = "; ".join(action_parts)

                if replaced:
                    after_path, after_hash, after_semantic = _capture_document_state(app, working_copy, "after")
                    ev_files.append(str(after_path.resolve()))

                    if after_hash == before_hash:
                        status = "FAIL"
                        error_msg = "선택 자간 교체 실행 후 문서 상태가 변경되지 않았습니다 (no-op)."
                    else:
                        restored, steps, restored_semantic = _run_undo_once(app, before_semantic, working_copy)
                        undo_steps = steps
                        restored_path, restored_hash, _ = _capture_document_state(app, working_copy, "restored")
                        ev_files.append(str(restored_path.resolve()))

                        if steps == 1 and restored:
                            status = "PASS"
                            error_msg = None
                            action_record += f"; undo_steps=1; semantic_restored=True"
                        else:
                            status = "FAIL"
                            if steps != 1:
                                error_msg = f"Undo 호출 횟수가 1이 아닙니다: {steps}"
                            else:
                                error_msg = "Undo 1회 실행 후 적용 전 상태로 온전히 복원되지 않았습니다 (의미적 불일치)."
                else:
                    status = "FAIL"

    except Exception as exc:
        error_msg = str(exc)
        status = "FAIL"

    case_result = GateCaseResult(
        name=name,
        status=status,
        undo_steps=undo_steps,
        source_sha256=source_hash,
        working_copy=str(working_copy.resolve()),
        before_sha256=before_hash,
        after_sha256=after_hash,
        restored_sha256=restored_hash,
        action=action_record,
        error=error_msg,
        evidence_files=tuple(ev_files),
    )

    with open(case_json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(case_result), f, indent=2, ensure_ascii=False)

    return case_result


def _write_fallback_case_json(
    work_dir: Path,
    name: str,
    fixture_path: Path,
    error_msg: str,
) -> GateCaseResult:
    """오류/중단 시 개별 case JSON을 작성하고 GateCaseResult를 반환한다."""
    case_json_path = work_dir / f"{name}.json"
    ev_files = [str(case_json_path.resolve())]
    case_res = GateCaseResult(
        name=name,
        status="FAIL",
        undo_steps=None,
        source_sha256=_sha256(fixture_path),
        working_copy="",
        before_sha256="",
        after_sha256="",
        restored_sha256=None,
        action=f"Failed before or during execution: {error_msg}",
        error=error_msg,
        evidence_files=tuple(ev_files),
    )
    with open(case_json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(case_res), f, indent=2, ensure_ascii=False)
    return case_res


def run_gate(
    *,
    fixture_root: Path,
    evidence_path: Path,
    work_dir: Path,
    table_fixture: Path | None = None,
    selection_fixture: Path | None = None,
    dispatch_ex: Callable[[str], object] | None = None,
    lock_factory: Callable[..., ContextManager] = com_test_lock,
    table_transformer: Callable[[bytes | str], bytes | str] | None = None,
    selection_transformer: Callable[[bytes | str], bytes | str] | None = None,
    repo_root: Path = _REPO_ROOT,
) -> GateEvidence:
    """한/글 COM에서 Undo 복원 게이트를 실측하고 증거를 기록한다.

    지적 7 반영:
    - 격리 COM 인스턴스의 Clear/Quit 정리 실패를 무시하지 않고 최상위 FAIL 증거로 반영한다.
    - 모든 중단/오류에서 G2가 읽을 수 있는 유효한 FAIL 증거 JSON과 상세 case 로그를 원자적으로 남긴다.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)

    resolved_repo = repo_root.resolve()

    # 1. 두 개의 서로 다른 fixture 경로 결정
    tbl_fixture = table_fixture or (
        fixture_root / "table_unit_sample.hwpx"
        if (fixture_root / "table_unit_sample.hwpx").is_file()
        else _DEFAULT_TABLE_FIXTURE
    )
    sel_fixture = selection_fixture or _DEFAULT_SELECTION_FIXTURE

    # 동일 fixture 방지
    if tbl_fixture.resolve() == sel_fixture.resolve():
        c1 = _write_fallback_case_json(work_dir, "table_unit", tbl_fixture, "동일 fixture 사용 금지 위반")
        c2 = _write_fallback_case_json(work_dir, "selection_spacing", sel_fixture, "동일 fixture 사용 금지 위반")
        evidence = GateEvidence(
            schema_version=1,
            gate="live_replace",
            status="FAIL",
            undo_steps=None,
            generated_at=datetime.now(timezone.utc).isoformat(),
            hwp_version="Unknown",
            cases=(c1, c2),
            evidence_files=(str(work_dir / "table_unit.json"), str(work_dir / "selection_spacing.json")),
        )
        _atomic_write_json(evidence_path, evidence, resolved_repo)
        return evidence

    # 적격성 검증 (지적 5, 6)
    tbl_ok, tbl_msg = _inspect_table_fixture(tbl_fixture)
    sel_ok, sel_msg = _inspect_selection_fixture(sel_fixture)

    if not tbl_ok or not sel_ok:
        c1 = _write_fallback_case_json(
            work_dir, "table_unit", tbl_fixture, tbl_msg if not tbl_ok else "정상 사전검증"
        )
        c2 = _write_fallback_case_json(
            work_dir, "selection_spacing", sel_fixture, sel_msg if not sel_ok else "정상 사전검증"
        )
        evidence = GateEvidence(
            schema_version=1,
            gate="live_replace",
            status="FAIL",
            undo_steps=None,
            generated_at=datetime.now(timezone.utc).isoformat(),
            hwp_version="Unknown",
            cases=(c1, c2),
            evidence_files=(str(work_dir / "table_unit.json"), str(work_dir / "selection_spacing.json")),
        )
        _atomic_write_json(evidence_path, evidence, resolved_repo)
        return evidence

    # 2. 잠금 획득 및 COM 격리 실행 (잠금 실패 시에도 최상위 FAIL 증거 원자적 보장)
    cases: list[GateCaseResult] = []
    hwp_ver = "Unknown"
    gate_exception = None
    cleanup_error: str | None = None

    try:
        lock_ctx = lock_factory(
            owner="live_replace_gate",
            purpose="실제 한/글 2020 Undo 실측",
            lock_path=_DEFAULT_COM_LOCK_PATH,
        )
    except Exception as exc:
        gate_exception = exc
        c1 = _write_fallback_case_json(work_dir, "table_unit", tbl_fixture, f"Lock factory 오류: {exc}")
        c2 = _write_fallback_case_json(work_dir, "selection_spacing", sel_fixture, f"Lock factory 오류: {exc}")
        evidence = GateEvidence(
            schema_version=1,
            gate="live_replace",
            status="FAIL",
            undo_steps=None,
            generated_at=datetime.now(timezone.utc).isoformat(),
            hwp_version="Unknown",
            cases=(c1, c2),
            evidence_files=(str(work_dir / "table_unit.json"), str(work_dir / "selection_spacing.json")),
        )
        _atomic_write_json(evidence_path, evidence, resolved_repo)
        return evidence

    try:
        with lock_ctx:
            app = None
            try:
                app = _make_hwp_dispatch(dispatch_ex)
                hwp_ver = getattr(app, "Version", "Unknown")

                table_case = _run_table_unit_case(
                    app, tbl_fixture, work_dir, table_transformer=table_transformer
                )
                cases.append(table_case)

                selection_case = _run_selection_spacing_case(
                    app, sel_fixture, work_dir, selection_transformer=selection_transformer
                )
                cases.append(selection_case)
            except Exception as exc:
                gate_exception = exc
                if len(cases) == 0:
                    cases.append(
                        _write_fallback_case_json(work_dir, "table_unit", tbl_fixture, f"실행 중 예외: {exc}")
                    )
                if len(cases) == 1:
                    cases.append(
                        _write_fallback_case_json(work_dir, "selection_spacing", sel_fixture, f"실행 중 예외: {exc}")
                    )
            finally:
                # 격리 인스턴스 정리 (지적 7: Clear/Quit 실패 반영)
                if app is not None:
                    try:
                        if hasattr(app, "Clear"):
                            clear_res = app.Clear(1)
                            if clear_res is False:
                                cleanup_error = "app.Clear(1) returned False"
                    except Exception as clear_exc:
                        cleanup_error = f"app.Clear(1) 예외 발생: {clear_exc}"

                    try:
                        if hasattr(app, "Quit"):
                            quit_res = app.Quit()
                            if quit_res is False and not cleanup_error:
                                cleanup_error = "app.Quit() returned False"
                    except Exception as quit_exc:
                        if not cleanup_error:
                            cleanup_error = f"app.Quit() 예외 발생: {quit_exc}"
                        else:
                            cleanup_error += f"; app.Quit() 예외: {quit_exc}"

    except Exception as lock_exc:
        gate_exception = lock_exc
        if len(cases) == 0:
            cases.append(
                _write_fallback_case_json(work_dir, "table_unit", tbl_fixture, f"Lock 획득/유지 오류: {lock_exc}")
            )
        if len(cases) == 1:
            cases.append(
                _write_fallback_case_json(work_dir, "selection_spacing", sel_fixture, f"Lock 획득/유지 오류: {lock_exc}")
            )

    # 정리 실패 시 PASS 승격 차단 및 오류 증거 반영 (지적 7)
    if cleanup_error is not None:
        if gate_exception is None:
            gate_exception = RuntimeError(f"격리 COM 인스턴스 정리 실패: {cleanup_error}")
        logging.getLogger(__name__).error("격리 인스턴스 정리 실패: %s", cleanup_error)

    all_pass = (
        gate_exception is None
        and cleanup_error is None
        and len(cases) == 2
        and all(c.status == "PASS" and c.undo_steps == 1 for c in cases)
    )
    status = "PASS" if all_pass else "FAIL"
    undo_steps = 1 if all_pass else None

    ev_files: list[str] = []
    for c in cases:
        case_json = work_dir / f"{c.name}.json"
        if case_json.is_file():
            try:
                rel = case_json.resolve().relative_to(resolved_repo)
                ev_files.append(str(rel).replace("\\", "/"))
            except ValueError:
                ev_files.append(str(case_json.resolve()))

    evidence = GateEvidence(
        schema_version=1,
        gate="live_replace",
        status=status,
        undo_steps=undo_steps,
        generated_at=datetime.now(timezone.utc).isoformat(),
        hwp_version=str(hwp_ver),
        cases=tuple(cases),
        evidence_files=tuple(ev_files),
    )

    _atomic_write_json(evidence_path, evidence, resolved_repo)
    return evidence


def main(argv: Sequence[str] | None = None) -> int:
    """CLI 진입점."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        evidence = run_gate(
            fixture_root=args.fixture_root,
            table_fixture=args.table_fixture,
            selection_fixture=args.selection_fixture,
            evidence_path=args.evidence,
            work_dir=args.work_dir,
        )
        return 0 if evidence.status == "PASS" else 1
    except Exception as exc:
        logging.getLogger(__name__).error("Undo 게이트 실행 중 치명적 오류: %s", exc)
        # 실패 증거 기록 보장
        try:
            fail_ev = GateEvidence(
                schema_version=1,
                gate="live_replace",
                status="FAIL",
                undo_steps=None,
                generated_at=datetime.now(timezone.utc).isoformat(),
                hwp_version="Unknown",
                cases=(),
                evidence_files=(),
            )
            _atomic_write_json(args.evidence, fail_ev, _REPO_ROOT)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
