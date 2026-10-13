"""Optional bridge to the MIT-licensed kordoc v4 document engine.

The desktop editor and direct HWPX-to-PDF remain functional without Node.js.
Advanced parsing/generation uses Node 20+ and an explicitly installed engine.

2026-10-10 실행 계약 정리(벤치마킹 kordoc 폐쇄망 설치 문서 참고):
- 버전 범위(^4) 대신 정확한 버전을 고정한다(실행 시점마다 다른 버전이 받아지지 않게).
- Node.js 20 이상을 확인한다(kordoc 4.21.x의 engines 조건).
- 폐쇄망: DOCFIT_KORDOC_BIN 또는 설정 폴더의 설치본을 우선한다. npx 다운로드는 명시적 허용 시에만 사용한다.
- patch의 반환 코드 2(일부 미적용)는 성공과 구분해 결과 이름에 표시한다.
"""

from __future__ import annotations

import difflib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from docfit_core.hwpx import validate_hwpx

KORDOC_VERSION = "4.21.30"
KORDOC_PACKAGE = f"kordoc@{KORDOC_VERSION}"
NODE_MIN_MAJOR = 20

# kordoc v4.21.30의 상세 사용법(지원 포맷 표)에 명시된 입력 형식.
# 일반 정리 파이프라인의 지원_확장자와 분리해, kordoc 전용 파일포맷 변경에서만 사용한다.
SUPPORTED_INPUT_EXTENSIONS = frozenset({
    ".hwp", ".hwpx", ".hml", ".pdf", ".xls", ".xlsx", ".docx", ".pptx",
    ".png", ".jpg", ".jpeg", ".webp",
})


class KordocUnavailableError(RuntimeError):
    pass


def _node_major() -> int | None:
    node = _node_executable()
    if not node:
        return None
    try:
        out = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=20,
                             startupinfo=_startupinfo(),
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0).stdout
        return int(out.strip().lstrip("v").split(".")[0])
    except Exception:
        return None


def _node_executable() -> str | None:
    return shutil.which("node.exe") or shutil.which("node")


def _local_kordoc() -> str | None:
    r"""폐쇄망용 미리 설치한 kordoc 실행 파일(환경 변수 DOCFIT_KORDOC_BIN 또는 %APPDATA%\HwpAutoDocFit\kordoc)."""
    후보 = []
    if os.environ.get("DOCFIT_KORDOC_BIN"):
        후보.append(Path(os.environ["DOCFIT_KORDOC_BIN"]))
    appdata = os.environ.get("APPDATA")
    if appdata:
        bin_dir = Path(appdata) / "HwpAutoDocFit" / "kordoc" / "node_modules" / ".bin"
        후보 += [bin_dir / "kordoc.cmd", bin_dir / "kordoc"]
    on_path = shutil.which("kordoc.cmd") or shutil.which("kordoc")
    if on_path:
        후보.append(Path(on_path))
    return next((str(x) for x in 후보 if x.is_file()), None)


def _npx_command() -> list[str]:
    command = shutil.which("npx.cmd") or shutil.which("npx")
    if not command:
        raise KordocUnavailableError(
            f"고급 문서 엔진을 사용하려면 Node.js {NODE_MIN_MAJOR} 이상이 필요합니다. "
            "https://nodejs.org 에서 LTS 버전을 설치해 주세요."
        )
    path = Path(command)
    if path.suffix.lower() in {".cmd", ".bat"}:
        # npm이 제공하는 JS 진입점을 Node에 인자 배열로 전달해
        # Windows 배치 래퍼에서 문서 경로가 셸 문법으로 해석되는 일을 피한다.
        node = _node_executable()
        candidates = (
            path.parent / "node_modules" / "npm" / "bin" / "npx-cli.js",
            path.parent / "node_modules" / "npm" / "bin" / "npx.js",
        )
        script = next((candidate for candidate in candidates if candidate.is_file()), None)
        if not node or script is None:
            raise KordocUnavailableError(
                "Windows npx 실행 파일의 JavaScript 진입점을 찾지 못했습니다. "
                "Node.js를 복구 설치한 뒤 다시 실행해 주세요."
            )
        return [node, str(script)]
    return [command]


def _local_kordoc_command(path: str) -> list[str]:
    executable = Path(path)
    if executable.suffix.lower() in {".cmd", ".bat"}:
        node = _node_executable()
        candidates = (
            executable.parent.parent / "kordoc" / "dist" / "cli.js",  # local .bin
            executable.parent / "node_modules" / "kordoc" / "dist" / "cli.js",  # global npm
        )
        cli = next((candidate for candidate in candidates if candidate.is_file()), None)
        if not node or cli is None:
            raise KordocUnavailableError(
                f"설치된 kordoc 실행 파일을 확인할 수 없습니다: {executable}"
            )
        return [node, str(cli)]
    if executable.suffix.lower() in {".js", ".mjs", ".cjs"}:
        node = _node_executable()
        if not node:
            raise KordocUnavailableError(f"kordoc 실행에 Node.js {NODE_MIN_MAJOR}+가 필요합니다.")
        return [node, str(executable)]
    return [path]


def _kordoc_command() -> list[str]:
    """실행 명령: 미리 설치한 kordoc이 있으면 그것, 없으면 고정 버전을 npx로."""
    major = _node_major()
    if major is None or major < NODE_MIN_MAJOR:
        raise KordocUnavailableError(
            f"고급 문서 엔진(kordoc {KORDOC_VERSION})은 Node.js {NODE_MIN_MAJOR} 이상이 필요합니다"
            f"{f'(지금 {major})' if major else ''}. https://nodejs.org 에서 LTS 버전을 설치해 주세요."
        )
    local = _local_kordoc()
    if local:
        return _local_kordoc_command(local)
    if os.environ.get("DOCFIT_ALLOW_NPX_DOWNLOAD") != "1":
        raise KordocUnavailableError(
            "kordoc이 설치되어 있지 않습니다. 보안을 위해 실행 중 자동 다운로드는 기본 차단됩니다. "
            "공식 Node.js/npm으로 kordoc을 미리 설치하거나, 신뢰할 수 있는 환경에서만 "
            "DOCFIT_ALLOW_NPX_DOWNLOAD=1을 설정하세요."
        )
    return [*_npx_command(), "--yes", "--ignore-scripts", KORDOC_PACKAGE]


def engine_status() -> dict[str, str | bool]:
    """UI preflight: report a locally installed, explicitly downloadable kordoc engine."""
    local = _local_kordoc()
    if not local and os.environ.get("DOCFIT_ALLOW_NPX_DOWNLOAD") != "1":
        # 사용할 엔진이 없는 경우 버전 조회 프로세스를 매번 실행할 필요가 없다.
        return {
            "available": False,
            "reason": f"kordoc {KORDOC_VERSION} 설치 필요 (Node.js {NODE_MIN_MAJOR}+)"
            if _node_executable() else f"Node.js {NODE_MIN_MAJOR}+ 설치 필요",
        }
    major = _node_major()
    if major is None:
        return {
            "available": False,
            "reason": f"Node.js {NODE_MIN_MAJOR}+ 설치 필요",
        }
    if major < NODE_MIN_MAJOR:
        return {
            "available": False,
            "reason": f"Node.js {NODE_MIN_MAJOR}+ 필요 (현재 {major})",
        }
    if local:
        try:
            _local_kordoc_command(local)
        except KordocUnavailableError as exc:
            return {"available": False, "reason": str(exc)}
        return {"available": True, "reason": "로컬 kordoc 준비됨"}
    if os.environ.get("DOCFIT_ALLOW_NPX_DOWNLOAD") == "1":
        try:
            _npx_command()
        except KordocUnavailableError as exc:
            return {"available": False, "reason": str(exc)}
        return {"available": True, "reason": f"kordoc {KORDOC_VERSION} (첫 실행 시 다운로드)"}
    return {
        "available": False,
        "reason": f"kordoc {KORDOC_VERSION} 설치 필요 (Node.js {NODE_MIN_MAJOR}+)",
    }


def _startupinfo():
    if os.name != "nt":
        return None
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = 0
    return info


def run_kordoc(arguments: list[str], timeout: int = 600,
                acceptable_codes: tuple[int, ...] = (0, 2)) -> subprocess.CompletedProcess[str]:
    command = [*_kordoc_command(), *map(str, arguments)]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        startupinfo=_startupinfo(),
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    # patch는 일부 미적용 항목이 있으면 2를 반환하지만 결과 파일은 정상 생성한다.
    if completed.returncode not in acceptable_codes:
        message = (completed.stderr or completed.stdout or "kordoc 실행 실패").strip()
        raise RuntimeError(message)
    return completed


def engine_version() -> str:
    return run_kordoc(["--version"], timeout=120).stdout.strip()


def parse_document(source: str | Path, target: str | Path, *, output_format: str = "markdown",
                   pages: str | None = None, ocr: bool = False) -> Path:
    args = [str(source), "--format", output_format, "-o", str(target), "--silent"]
    if pages:
        args.extend(["--pages", pages])
    if ocr:
        # 텍스트층이 없는 페이지만 내장 OCR로 인식한다(스캔 PDF 대응). 텍스트층이
        # 있으면 건드리지 않으므로 일반 PDF에도 안전하게 항상 켤 수 있다.
        args.append("--ocr")
    run_kordoc(args)
    return Path(target)


def convert_to_hwpx(source: str | Path, target: str | Path, *, preset: str = "보고서") -> Path:
    """kordoc이 지원하는 문서를 Markdown으로 파싱한 뒤 HWPX로 생성한다.

    임시 산출물은 시스템 임시 폴더에만 두고 원본은 수정하지 않는다.
    결과 경로는 호출자가 충돌 없는 새 파일로 지정해야 한다.
    """
    source, target = Path(source), Path(target)
    if source.is_symlink() or not source.is_file():
        raise ValueError("변환 원본이 일반 파일이 아니거나 심볼릭 링크입니다.")
    if source.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
        raise ValueError(f"kordoc이 지원하지 않는 입력 형식입니다: {source.suffix or '(확장자 없음)'}")
    if target.suffix.lower() != ".hwpx":
        raise ValueError("HWPX 결과 파일 확장자는 .hwpx여야 합니다.")
    if source.resolve() == target.resolve():
        raise ValueError("원본 파일을 덮어쓸 수 없습니다.")
    if target.exists():
        raise FileExistsError(f"결과 파일이 이미 있습니다: {target.name}")

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="docfit_kordoc_convert_") as folder:
        temp_dir = Path(folder)
        markdown = temp_dir / "document.md"
        parse_document(source, markdown, output_format="markdown", ocr=source.suffix.lower() == ".pdf")
        if not markdown.is_file():
            raise RuntimeError("kordoc 파싱 결과 Markdown 파일이 생성되지 않았습니다.")
        # 같은 볼륨에 임시 결과를 두어 OneDrive/다른 드라이브에서도 원자적으로
        # 최종 이름을 확보할 수 있게 한다. hard link가 기존 결과를 덮어쓰지 않는다.
        with tempfile.NamedTemporaryFile(prefix=".docfit_", suffix=".hwpx", dir=target.parent, delete=False) as stream:
            generated = Path(stream.name)
        generated.unlink()
        try:
            generate_hwpx(markdown, preset, generated, image_dir=temp_dir)
            if not generated.is_file() or generated.stat().st_size == 0:
                raise RuntimeError("kordoc이 유효한 HWPX 결과를 생성하지 못했습니다.")
            try:
                validate_hwpx(generated)
            except (OSError, ValueError) as exc:
                raise RuntimeError(f"kordoc 결과가 올바른 HWPX 문서가 아닙니다: {exc}") from exc
            os.link(generated, target)
        finally:
            generated.unlink(missing_ok=True)
    if not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError("kordoc이 유효한 HWPX 결과를 생성하지 못했습니다.")
    return target


def export_advanced_markdown(source: str | Path, pages: str | None = None) -> Path:
    source = Path(source)
    suffix = ".pages.md" if pages else ".advanced.md"
    return parse_document(source, source.with_name(source.stem + suffix), pages=pages)


def export_common_ir(source: str | Path) -> Path:
    source = Path(source)
    return parse_document(source, source.with_name(source.stem + ".document.json"), output_format="json")


def export_rag_chunks(source: str | Path) -> Path:
    source = Path(source)
    return parse_document(source, source.with_name(source.stem + ".chunks.json"), output_format="chunks")


def analyze_tables(source: str | Path) -> Path:
    source = Path(source)
    target = source.with_name(source.stem + ".tables.json")
    run_kordoc(["tables", str(source), "--cells", "--visual", "none", "-o", str(target), "--silent"])
    return target


def analyze_form(source: str | Path) -> Path:
    source = Path(source)
    target = source.with_name(source.stem + ".form-fields.txt")
    completed = run_kordoc(["fill", str(source), "--dry-run", "--silent"])
    target.write_text((completed.stdout or completed.stderr).strip(), encoding="utf-8")
    return target


def render_preview(source: str | Path) -> Path:
    source = Path(source)
    output_dir = source.with_name(source.stem + "_preview")
    output_dir.mkdir(parents=True, exist_ok=True)
    run_kordoc(["render", str(source), "--format", "png", "-d", str(output_dir), "--silent"])
    return output_dir


def _flatten_blocks(value: Any, prefix: str = "") -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    if isinstance(value, dict):
        kind = str(value.get("type", ""))
        text = value.get("text") or value.get("markdown") or value.get("content")
        if kind and isinstance(text, str):
            blocks.append({"path": prefix, "type": kind, "text": text})
        for key, child in value.items():
            if key not in {"text", "markdown", "content", "images"}:
                blocks.extend(_flatten_blocks(child, f"{prefix}/{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            blocks.extend(_flatten_blocks(child, f"{prefix}/{index}"))
    return blocks


def compare_documents(source_a: str | Path, source_b: str | Path, target: str | Path | None = None) -> Path:
    """Create a block/cell-aware JSON diff from kordoc's common document IR."""
    source_a, source_b = Path(source_a), Path(source_b)
    target = Path(target) if target else source_b.with_name(source_b.stem + ".comparison.json")
    with tempfile.TemporaryDirectory(prefix="docfit_kordoc_diff_") as folder:
        a_path, b_path = Path(folder) / "a.json", Path(folder) / "b.json"
        parse_document(source_a, a_path, output_format="json")
        parse_document(source_b, b_path, output_format="json")
        a_blocks = _flatten_blocks(json.loads(a_path.read_text(encoding="utf-8")))
        b_blocks = _flatten_blocks(json.loads(b_path.read_text(encoding="utf-8")))
    a_text = [f"{b['type']}\t{b['text']}" for b in a_blocks]
    b_text = [f"{b['type']}\t{b['text']}" for b in b_blocks]
    matcher = difflib.SequenceMatcher(None, a_text, b_text, autojunk=False)
    changes = []
    for operation, a1, a2, b1, b2 in matcher.get_opcodes():
        if operation != "equal":
            changes.append({"operation": operation, "before": a_blocks[a1:a2], "after": b_blocks[b1:b2]})
    report = {
        "version": 1,
        "before": str(source_a),
        "after": str(source_b),
        "blocks_before": len(a_blocks),
        "blocks_after": len(b_blocks),
        "similarity": matcher.ratio(),
        "changes": changes,
    }
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def fill_form(source: str | Path, fields: str, target: str | Path | None = None) -> Path:
    source = Path(source)
    target = Path(target) if target else source.with_name(source.stem + "(양식채움).hwpx")
    run_kordoc(["fill", str(source), "--fields", fields, "--require-unique", "-o", str(target), "--silent"])
    return target


def patch_document(source: str | Path, edited_markdown: str | Path,
                   target: str | Path | None = None) -> Path:
    source = Path(source)
    target = Path(target) if target else source.with_name(source.stem + "(텍스트패치)" + source.suffix)
    completed = run_kordoc(["patch", str(source), str(edited_markdown), "-o", str(target), "--silent"])
    if completed.returncode == 2 and target.exists():
        # 일부 문단은 적용되지 않았다(kordoc 반환 코드 2). 성공으로 보이지 않게 결과 이름에 표시한다.
        partial = target.with_name(target.stem + "(일부미적용)" + target.suffix)
        if partial.exists():
            partial.unlink()
        target.rename(partial)
        return partial
    return target


def lint_document(source: str | Path) -> Path:
    source = Path(source)
    report = source.with_name(source.stem + ".lint.json")
    with tempfile.TemporaryDirectory(prefix="docfit_kordoc_lint_") as folder:
        markdown = Path(folder) / "document.md"
        parse_document(source, markdown)
        completed = run_kordoc(["lint", str(markdown), "--json", "--munche"], acceptable_codes=(0, 1))
        report.write_text(completed.stdout or "[]", encoding="utf-8")
    return report


PRESET_NAMES = {"보고서": "보고서", "계획서": "계획서", "기안문": "기안문"}


def generate_hwpx(markdown: str | Path, preset: str, target: str | Path | None = None,
                   *, image_dir: str | Path | None = None) -> Path:
    markdown = Path(markdown)
    if preset not in PRESET_NAMES:
        raise ValueError(f"지원하지 않는 프리셋입니다: {preset}")
    target = Path(target) if target else markdown.with_name(markdown.stem + f"({preset}).hwpx")
    args = ["generate", str(markdown), "-o", str(target), "--preset", PRESET_NAMES[preset], "--silent"]
    if image_dir:
        # kordoc generate는 --image-dir을 줘야만 마크다운의 이미지 참조를 실제
        # 바이트로 읽어 HWPX에 임베드한다(없으면 자리표시만 남고 이미지가 사라짐).
        args.extend(["--image-dir", str(image_dir)])
    run_kordoc(args)
    return target
