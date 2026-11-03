"""DOCX, PPTX, XLSX 및 XLS 문서 추출기 (보안 한도 및 defusedxml 파싱)."""
from __future__ import annotations

import posixpath
import re
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile, ZipInfo
from defusedxml import ElementTree as ET

from .extractors import ExtractionError, ExtractionRecord

# HWPX와 동일한 수준의 압축 한도 상수
MAX_ENTRIES: int = 10_000
MAX_TOTAL_SIZE: int = 512 * 1024 * 1024
MAX_FILE_SIZE: int = 128 * 1024 * 1024
MAX_COMPRESSION_RATIO: int = 1_000

OLE_HEADER: bytes = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _safe_member_name(info: ZipInfo) -> str:
    name = info.filename.replace("\\", "/")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", name):
        raise ExtractionError("corrupt", f"안전하지 않은 압축 경로: {info.filename}")
    if ((info.external_attr >> 16) & 0o170000) == 0o120000:
        raise ExtractionError("corrupt", f"심볼릭 링크 압축 항목 거부: {info.filename}")
    return name


def _open_zip_safely(path: Path) -> ZipFile:
    """보안 제한을 검사하며 읽기 전용 ZipFile을 연다."""
    if not path.is_file():
        raise ExtractionError("corrupt", f"파일을 찾을 수 없음: {path}")

    # OLE 암호화 패키지 검사
    try:
        header = path.read_bytes()[:512]
        if header.startswith(OLE_HEADER):
            if b"EncryptedPackage" in header or b"EncryptionInfo" in header:
                raise ExtractionError("encrypted", "암호화된 Office 복합 문서(OLE)")
    except ExtractionError:
        raise
    except Exception:
        pass

    try:
        archive = ZipFile(path, "r")
    except BadZipFile as exc:
        raise ExtractionError("corrupt", f"올바른 ZIP 오피스 문서가 아님: {exc}") from exc
    except OSError as exc:
        raise ExtractionError("corrupt", f"압축 파일 열기 실패: {exc}") from exc

    infos = archive.infolist()
    if len(infos) > MAX_ENTRIES:
        archive.close()
        raise ExtractionError("corrupt", f"압축 항목 수 초과: {len(infos)}")

    total_size = 0
    names: set[str] = set()
    for info in infos:
        if info.flag_bits & 0x1:
            archive.close()
            raise ExtractionError("encrypted", f"암호화된 ZIP 항목: {info.filename}")

        norm_name = _safe_member_name(info)
        if norm_name in names:
            archive.close()
            raise ExtractionError("corrupt", f"중복된 압축 항목: {info.filename}")
        names.add(norm_name)

        if info.file_size > MAX_FILE_SIZE:
            archive.close()
            raise ExtractionError("corrupt", f"단일 파일 크기 초과: {info.filename}")

        total_size += info.file_size
        if total_size > MAX_TOTAL_SIZE:
            archive.close()
            raise ExtractionError("corrupt", f"총 압축 해제 크기 초과: {total_size}")

        if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
            archive.close()
            raise ExtractionError("corrupt", f"비정상 압축률 감지: {info.filename}")

    return archive


def extract_docx(path: Path | str) -> list[ExtractionRecord]:
    """DOCX 문서에서 본문 및 머리글/바닥글 문단 위치를 추출한다."""
    file_path = Path(path)
    archive = _open_zip_safely(file_path)
    records: list[ExtractionRecord] = []
    seq = 1

    with archive:
        namelist = archive.namelist()
        if "word/document.xml" not in namelist:
            raise ExtractionError("corrupt", "DOCX 필수 파일(word/document.xml) 누락")

        # 1. 본문 문단 추출
        try:
            doc_root = ET.fromstring(archive.read("word/document.xml"))
        except Exception as exc:
            raise ExtractionError("corrupt", f"DOCX 본문 XML 파싱 실패: {exc}") from exc

        p_num = 1
        for elem in doc_root.iter():
            if _local_name(elem.tag) == "p":
                text = "".join(elem.itertext()).strip()
                if text:
                    records.append(
                        ExtractionRecord(
                            text=text,
                            location_kind="paragraph",
                            location_label=f"문단 {p_num}",
                            sequence=seq,
                            section="본문",
                        )
                    )
                    p_num += 1
                    seq += 1

        # 2. 머리글/바닥글 문단 추출 (본문 뒤에 위치 표기해 추가)
        header_footer_names = [
            n for n in namelist
            if (n.startswith("word/header") or n.startswith("word/footer")) and n.endswith(".xml")
        ]

        def _hf_sort_key(name: str) -> tuple[int, int]:
            is_footer = 1 if "footer" in name else 0
            m = re.search(r"\d+", name)
            num = int(m.group()) if m else 0
            return (is_footer, num)

        header_footer_names.sort(key=_hf_sort_key)

        for hf_name in header_footer_names:
            stem = Path(hf_name).stem  # 예: header1, footer1
            is_header = "header" in stem
            section_label = "머리글" if is_header else "바닥글"
            m = re.search(r"\d+", stem)
            hf_index = m.group() if m else ""
            label_prefix = f"{section_label} {hf_index}".strip()

            try:
                hf_root = ET.fromstring(archive.read(hf_name))
            except Exception as exc:
                raise ExtractionError("corrupt", f"DOCX 머리글/바닥글 XML 파싱 실패 ({hf_name}): {exc}") from exc

            hf_p_num = 1
            for elem in hf_root.iter():
                if _local_name(elem.tag) == "p":
                    text = "".join(elem.itertext()).strip()
                    if text:
                        records.append(
                            ExtractionRecord(
                                text=text,
                                location_kind="paragraph",
                                location_label=f"{label_prefix} 문단 {hf_p_num}",
                                sequence=seq,
                                section=label_prefix,
                            )
                        )
                        hf_p_num += 1
                        seq += 1

    if not records:
        raise ExtractionError("empty", "추출 가능한 DOCX 본문 텍스트가 없음")

    return records


def extract_pptx(path: Path | str) -> list[ExtractionRecord]:
    """PPTX 프레젠테이션에서 슬라이드별 문단 위치를 추출한다."""
    file_path = Path(path)
    archive = _open_zip_safely(file_path)
    records: list[ExtractionRecord] = []
    seq = 1

    with archive:
        namelist = archive.namelist()
        slide_names = [
            n for n in namelist
            if n.startswith("ppt/slides/slide") and n.endswith(".xml")
        ]
        if not slide_names:
            raise ExtractionError("empty", "PPTX에 슬라이드가 없음")

        def _slide_sort_key(name: str) -> int:
            m = re.search(r"slide(\d+)\.xml", name)
            return int(m.group(1)) if m else 0

        slide_names.sort(key=_slide_sort_key)

        for s_name in slide_names:
            m = re.search(r"slide(\d+)\.xml", s_name)
            slide_num = int(m.group(1)) if m else 0
            section_name = f"슬라이드 {slide_num}"

            try:
                root = ET.fromstring(archive.read(s_name))
            except Exception as exc:
                raise ExtractionError("corrupt", f"PPTX 슬라이드 XML 파싱 실패 ({s_name}): {exc}") from exc

            p_idx = 1
            for elem in root.iter():
                if _local_name(elem.tag) == "p":
                    text = "".join(elem.itertext()).strip()
                    if text:
                        records.append(
                            ExtractionRecord(
                                text=text,
                                location_kind="paragraph",
                                location_label=f"슬라이드 {slide_num} 문단 {p_idx}",
                                sequence=seq,
                                section=section_name,
                            )
                        )
                        p_idx += 1
                        seq += 1

    if not records:
        raise ExtractionError("empty", "추출 가능한 PPTX 텍스트가 없음")

    return records


def _resolve_rel_path(base_dir: str, target: str) -> str:
    """OPC 관계 타깃 경로를 ZIP 엔트리 경로로 정규화하고 경로 밖(..) 탈출을 거부한다."""
    t = target.replace("\\", "/").strip()
    if t.startswith("/"):
        norm = posixpath.normpath(t.lstrip("/"))
    else:
        norm = posixpath.normpath(posixpath.join(base_dir, t))
    if not norm or norm == "." or norm.startswith("../") or norm == ".." or norm.startswith("/"):
        raise ExtractionError("corrupt", f"허용되지 않는 상대 경로 탈출: {target}")
    return norm


def extract_xlsx(path: Path | str) -> list[ExtractionRecord]:
    """XLSX 스프레드시트에서 시트명과 행 번호 위치를 추출한다."""
    file_path = Path(path)
    archive = _open_zip_safely(file_path)
    records: list[ExtractionRecord] = []
    seq = 1

    with archive:
        namelist = set(archive.namelist())

        # 1. 공유 문자열(sharedStrings.xml) 파싱
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in namelist:
            try:
                sst_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                for si in sst_root.iter():
                    if _local_name(si.tag) == "si":
                        # <si> 내 모든 <t> 요소 텍스트 합치기
                        t_parts = [t.text for t in si.iter() if _local_name(t.tag) == "t" and t.text]
                        shared_strings.append("".join(t_parts))
            except Exception as exc:
                raise ExtractionError("corrupt", f"XLSX sharedStrings.xml 파싱 실패: {exc}") from exc

        # 2. 관계 파일(workbook.xml.rels) 파싱하여 rId -> 타깃 경로 매핑
        rels_map: dict[str, str] = {}
        if "xl/_rels/workbook.xml.rels" in namelist:
            try:
                rels_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
                for rel in rels_root.iter():
                    if _local_name(rel.tag) == "Relationship":
                        r_id = rel.attrib.get("Id")
                        target = rel.attrib.get("Target")
                        if r_id and target:
                            resolved = _resolve_rel_path("xl", target)
                            rels_map[r_id] = resolved
            except Exception as exc:
                raise ExtractionError("corrupt", f"XLSX workbook.xml.rels 파싱 실패: {exc}") from exc

        # 3. 워크북(workbook.xml)에서 시트 목록 및 시트명 추출
        sheets_info: list[tuple[str, str]] = []  # (시트명, 타깃 xml 경로)
        if "xl/workbook.xml" in namelist:
            try:
                wb_root = ET.fromstring(archive.read("xl/workbook.xml"))
                for sheet_elem in wb_root.iter():
                    if _local_name(sheet_elem.tag) == "sheet":
                        name = sheet_elem.attrib.get("name", "Sheet")
                        # r:id 속성 (네임스페이스 주의)
                        r_id = None
                        for attr_name, attr_val in sheet_elem.attrib.items():
                            if _local_name(attr_name) == "id":
                                r_id = attr_val
                                break
                        target_path = rels_map.get(r_id) if r_id else None
                        if target_path and target_path in namelist:
                            sheets_info.append((name, target_path))
            except Exception as exc:
                raise ExtractionError("corrupt", f"XLSX workbook.xml 파싱 실패: {exc}") from exc

        # 워크북 파싱으로 시트를 못 찾은 경우 대체 검색
        if not sheets_info:
            ws_names = [n for n in namelist if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]

            def _ws_sort_key(name: str) -> int:
                m = re.search(r"sheet(\d+)\.xml", name)
                return int(m.group(1)) if m else 0

            ws_names.sort(key=_ws_sort_key)
            for ws_name in ws_names:
                m = re.search(r"sheet(\d+)\.xml", ws_name)
                s_idx = m.group(1) if m else "1"
                sheets_info.append((f"Sheet{s_idx}", ws_name))

        if not sheets_info:
            raise ExtractionError("empty", "XLSX 워크시트를 찾을 수 없음")

        # 4. 각 워크시트에서 row 단위 셀 텍스트 추출
        for sheet_name, sheet_xml_path in sheets_info:
            try:
                ws_root = ET.fromstring(archive.read(sheet_xml_path))
            except Exception as exc:
                raise ExtractionError("corrupt", f"XLSX 시트 XML 파싱 실패 ({sheet_xml_path}): {exc}") from exc

            row_counter = 1
            for row_elem in ws_root.iter():
                if _local_name(row_elem.tag) == "row":
                    row_r = row_elem.attrib.get("r")
                    row_num = int(row_r) if (row_r and row_r.isdigit()) else row_counter
                    row_counter = row_num + 1

                    cell_texts: list[str] = []
                    for c_elem in row_elem:
                        if _local_name(c_elem.tag) != "c":
                            continue
                        t_attr = c_elem.attrib.get("t", "")
                        v_elem = next((child for child in c_elem if _local_name(child.tag) == "v"), None)
                        val_str = (v_elem.text or "").strip() if v_elem is not None else ""

                        if t_attr == "s" and val_str.isdigit():
                            idx = int(val_str)
                            if 0 <= idx < len(shared_strings):
                                cell_texts.append(shared_strings[idx].strip())
                        elif t_attr == "inlineStr":
                            is_elem = next((child for child in c_elem if _local_name(child.tag) == "is"), None)
                            if is_elem is not None:
                                t_parts = [t.text for t in is_elem.iter() if _local_name(t.tag) == "t" and t.text]
                                cell_texts.append("".join(t_parts).strip())
                        else:
                            # 수식 셀(<f>)인 경우에도 캐시된 값 <v>만 읽음
                            if val_str:
                                cell_texts.append(val_str)

                    # 비어 있지 않은 셀 텍스트들 결합
                    non_empty = [c for c in cell_texts if c]
                    if non_empty:
                        row_line = " ".join(non_empty)
                        records.append(
                            ExtractionRecord(
                                text=row_line,
                                location_kind="sheet_row",
                                location_label=f"{sheet_name} {row_num}행",
                                sequence=seq,
                                section=sheet_name,
                            )
                        )
                        seq += 1

    if not records:
        raise ExtractionError("empty", "추출 가능한 XLSX 데이터가 없음")

    return records


def extract_xls(path: Path | str, xlrd_module=None) -> list[ExtractionRecord]:
    """XLS 스프레드시트에서 xlrd를 통해 시트명과 1-based 행 번호 위치를 추출한다."""
    file_path = Path(path)
    if not file_path.is_file():
        raise ExtractionError("corrupt", f"파일을 찾을 수 없음: {file_path}")

    try:
        if xlrd_module is not None:
            xlrd = xlrd_module
        else:
            import xlrd
    except ImportError as exc:
        raise ExtractionError("runtime_unavailable", f"XLS 지원에 필요한 xlrd 라이브러리 없음: {exc}") from exc

    try:
        book = xlrd.open_workbook(filename=str(file_path), on_demand=True)
    except Exception as exc:
        msg = str(exc).lower()
        if any(term in msg for term in ("password", "protected", "encrypt", "암호")):
            raise ExtractionError("encrypted", f"암호화된 XLS 파일: {exc}") from exc
        raise ExtractionError("corrupt", f"손상된 XLS 파일: {exc}") from exc

    records: list[ExtractionRecord] = []
    seq = 1

    try:
        sheet_count = book.nsheets
        for s_idx in range(sheet_count):
            sheet = book.sheet_by_index(s_idx)
            for r_idx in range(sheet.nrows):
                row_vals = sheet.row_values(r_idx)
                non_empty = [str(val).strip() for val in row_vals if val != "" and str(val).strip()]
                if non_empty:
                    row_text = " ".join(non_empty)
                    records.append(
                        ExtractionRecord(
                            text=row_text,
                            location_kind="sheet_row",
                            location_label=f"{sheet.name} {r_idx + 1}행",
                            sequence=seq,
                            section=sheet.name,
                        )
                    )
                    seq += 1
    finally:
        if hasattr(book, "release_resources"):
            book.release_resources()

    if not records:
        raise ExtractionError("empty", "추출 가능한 XLS 데이터가 없음")

    return records
