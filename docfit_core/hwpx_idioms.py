"""사용자가 한/글에서 직접 편집하는 HWPX 상용구 설정 파일 파서.

형식: ``#+준말`` 문단 다음부터 다음 ``#+`` 문단 직전까지를 본말로 읽는다.
빈 문단은 본말 안의 줄바꿈으로 보존한다. XML은 반드시 defusedxml을 사용한다.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

from defusedxml import ElementTree as ET

from .hwpx import open_hwpx_safely


class HwpxIdiomError(ValueError):
    """상용구 HWPX 파일의 형식 또는 항목이 잘못된 경우."""


_MARKER = re.compile(r"^\s*#\+\s*(.*?)\s*$")
_MAX_ENTRIES = 2000
_MAX_KEY = 20
_MAX_VALUE = 100_000


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _paragraph_text(paragraph: ET.Element) -> str:
    parts: list[str] = []

    def visit(node: ET.Element) -> None:
        name = _local_name(node.tag)
        if name == "t" and node.text:
            parts.append(node.text)
        elif name in {"lineBreak", "br"}:
            parts.append("\n")
        elif name == "tab":
            parts.append("\t")
        elif name in {"fwSpace", "nbSpace"}:
            parts.append(" ")
        for child in node:
            visit(child)
            if name == "t" and child.tail:
                parts.append(child.tail)

    visit(paragraph)
    return "".join(parts)


def parse_hwpx(path: str | Path) -> list[dict[str, str]]:
    """HWPX를 ``[{key, value}, ...]``로 읽는다.

    표 안의 문단도 문서 순서대로 읽으며, ``#+``가 아닌 일반 문단은 무시한다.
    이는 사용자가 제목·설명 문단을 넣어도 설정 항목에 섞이지 않게 하기 위함이다.
    """
    source = Path(path)
    try:
        with open_hwpx_safely(source) as archive:
            names = sorted(
                (name for name in archive.namelist()
                 if re.fullmatch(r"Contents/section\d+\.xml", name)),
                key=lambda name: int(re.search(r"section(\d+)", name).group(1)),
            )
            paragraphs: list[str] = []
            for name in names:
                root = ET.fromstring(archive.read(name))
                paragraphs.extend(_paragraph_text(node) for node in root.iter()
                                  if _local_name(node.tag) == "p")
    except Exception as exc:
        if isinstance(exc, HwpxIdiomError):
            raise
        raise HwpxIdiomError(f"상용구 HWPX를 읽지 못했습니다: {source.name}: {exc}") from exc

    entries: list[dict[str, str]] = []
    current_key: str | None = None
    value_lines: list[str] = []

    def finish() -> None:
        nonlocal current_key, value_lines
        if current_key is None:
            return
        value = "\n".join(value_lines).strip("\n")
        if not value.strip():
            raise HwpxIdiomError(f"'{current_key}' 준말 아래에 본말이 없습니다.")
        entries.append({"key": current_key, "value": value})
        current_key, value_lines = None, []

    for line in paragraphs:
        marker = _MARKER.fullmatch(line)
        if marker:
            finish()
            current_key = marker.group(1).strip()
            if not current_key:
                raise HwpxIdiomError("#+ 뒤에 준말을 입력해 주세요.")
            if len(current_key) > _MAX_KEY or any(ord(ch) < 32 for ch in current_key):
                raise HwpxIdiomError(f"준말은 제어문자 없이 {_MAX_KEY}자 이내여야 합니다.")
        elif current_key is not None:
            value_lines.append(line)
    finish()

    if len(entries) > _MAX_ENTRIES:
        raise HwpxIdiomError(f"상용구는 {_MAX_ENTRIES}개까지 사용할 수 있습니다.")
    seen: set[str] = set()
    for item in entries:
        if item["key"] in seen:
            raise HwpxIdiomError(f"준말이 중복되었습니다: {item['key']}")
        seen.add(item["key"])
        if len(item["value"]) > _MAX_VALUE:
            raise HwpxIdiomError(f"'{item['key']}' 본말이 너무 깁니다.")
    if not entries:
        raise HwpxIdiomError("#+준말 형식의 상용구 항목을 찾지 못했습니다.")
    return entries


def compile_native_idiom_file(text_path: str | Path, body_path: str | Path):
    """HWPX 설정 두 개를 한/글이 읽는 HWP.IDO 자료형으로 변환한다."""
    from .hwp_idioms import BODY_SECTION, Idiom, IdiomFile

    text = parse_hwpx(text_path) if Path(text_path).is_file() else []
    body = parse_hwpx(body_path) if Path(body_path).is_file() else []
    if not text and not body:
        raise HwpxIdiomError("글자·본문 상용구 HWPX 설정 파일을 찾지 못했습니다.")
    return IdiomFile(
        text=[Idiom(item["key"], item["value"], 0) for item in text],
        body=[Idiom(item["key"], item["key"], 1) for item in body],
        has_body_section=bool(body) or bool(text),
    )


def create_template(base_hwpx: str | Path, target: str | Path, entries: list[dict[str, str]]) -> Path:
    """기존 정상 HWPX의 문서 구조를 재사용해 간단한 상용구 편집 문서를 만든다.

    대상 파일이 이미 있으면 절대 덮어쓰지 않는다. 글꼴/문단 정의와 구역 설정은
    기본 서식 예시에서 가져오고, 본문은 ``#+준말``-값 문단만 남긴다.
    """
    source, destination = Path(base_hwpx), Path(target)
    if destination.exists():
        return destination
    if not entries:
        raise HwpxIdiomError("초기 상용구 항목이 비어 있습니다.")
    validated = []
    for item in entries:
        key, value = str(item.get("key", "")).strip(), str(item.get("value", ""))
        if not key or not value.strip() or len(key) > _MAX_KEY or len(value) > _MAX_VALUE:
            raise HwpxIdiomError("초기 상용구 항목의 준말 또는 본말이 올바르지 않습니다.")
        validated.append((key, value))

    template_lines = [
        "상용구 설정 문서 — 이 파일을 한/글에서 직접 수정하세요.",
        "항목은 준말 표식 뒤에 준말을 적은 한 줄로 시작합니다.",
        "그 바로 다음 줄부터 본말을 입력하고, 항목을 바꿀 때 새 표식을 씁니다.",
        "예) +#+ㅁ 다음 줄에 □ 를 입력하면 ㅁ → □ 로 정의됩니다.",
        "안내 문단은 설정에서 무시되며, +#+로 시작하는 문단만 항목입니다.",
    ]
    for key, value in validated:
        template_lines.extend(["#+" + key, *value.split("\n")])
    return write_paragraph_document(source, destination, template_lines, parse_hwpx)


def write_paragraph_document(base_hwpx: str | Path, target: str | Path, lines: list[str], verify) -> Path:
    """기본 HWPX의 구역·글자 서식을 재사용해 ``lines``를 한 줄씩 문단으로 쓴 문서를 만든다.

    대상 파일이 이미 있으면 덮어쓰지 않는다. ``verify(임시경로)``가 예외 없이 끝나야 대상 파일로 옮긴다.
    """
    source, destination = Path(base_hwpx), Path(target)
    if destination.exists():
        return destination
    try:
        with open_hwpx_safely(source) as archive:
            names = archive.namelist()
            section_name = next(name for name in names if re.fullmatch(r"Contents/section\d+\.xml", name))
            root = ET.fromstring(archive.read(section_name))
            direct_paragraphs = [child for child in root if _local_name(child.tag) == "p"]
            if not direct_paragraphs:
                raise HwpxIdiomError("기본 HWPX에서 문단 서식을 찾지 못했습니다.")
            first = direct_paragraphs[0]
            sec_run = next((run for run in first if _local_name(run.tag) == "run" and
                            any(_local_name(node.tag) == "secPr" for node in run.iter())), None)
            sample = next((node for node in root.iter() if _local_name(node.tag) == "p" and
                           any(_local_name(child.tag) == "run" and
                               any(_local_name(part.tag) == "t" for part in child)
                               for child in node)), None)
            if sec_run is None or sample is None:
                raise HwpxIdiomError("기본 HWPX에서 구역 또는 글자 서식을 찾지 못했습니다.")

            # 보존할 구역 설정 문단 하나만 남기고 원본 표·본문은 제거한다.
            for child in list(root):
                root.remove(child)
            clean_first = copy.deepcopy(first)
            clean_sec_run = next(run for run in clean_first if _local_name(run.tag) == "run" and
                                 any(_local_name(node.tag) == "secPr" for node in run.iter()))
            for child in list(clean_first):
                if child is not clean_sec_run:
                    clean_first.remove(child)
            clean_run = clean_sec_run
            for child in list(clean_run):
                if _local_name(child.tag) != "secPr":
                    clean_run.remove(child)
            root.append(clean_first)

            template_p = copy.deepcopy(sample)
            for child in list(template_p):
                if _local_name(child.tag) != "run":
                    template_p.remove(child)
            template_run = next(child for child in template_p if _local_name(child.tag) == "run")
            text_node = next((node for node in template_run if _local_name(node.tag) == "t"), None)
            if text_node is None:
                raise HwpxIdiomError("기본 HWPX에서 글자 서식을 복제하지 못했습니다.")
            for child in list(template_run):
                if child is not text_node:
                    template_run.remove(child)

            for line in lines:
                    paragraph = copy.deepcopy(template_p)
                    run = next(child for child in paragraph if _local_name(child.tag) == "run")
                    node = next(child for child in run if _local_name(child.tag) == "t")
                    node.text = line
                    root.append(paragraph)
            section_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temp = destination.with_name(destination.name + ".tmp")
            with ZipFile(source) as original, ZipFile(temp, "w") as output:
                for info in original.infolist():
                    data = section_bytes if info.filename == section_name else original.read(info.filename)
                    output.writestr(info, data, compress_type=ZIP_STORED if info.filename == "mimetype"
                                    else info.compress_type)
        # Output is validated and parsed before it becomes the active setting file.
        verify(temp)
        temp.replace(destination)
        return destination
    except HwpxIdiomError:
        try:
            temp.unlink(missing_ok=True)
        except (OSError, UnboundLocalError):
            pass
        raise
    except Exception as exc:
        try:
            temp.unlink(missing_ok=True)
        except (OSError, UnboundLocalError):
            pass
        raise HwpxIdiomError(f"상용구 HWPX 템플릿을 만들지 못했습니다: {exc}") from exc


def create_default_configs(config_root: str | Path, base_hwpx: str | Path) -> tuple[Path, Path]:
    """앱 첫 실행 시 예시 글자·본문 HWPX 설정을 비파괴적으로 준비한다."""
    root = Path(config_root)
    text_path = root / "글자상용구" / "글자상용구.hwpx"
    body_path = root / "본문상용구" / "본문상용구.hwpx"
    create_template(base_hwpx, text_path, [
        {"key": "ㅁ", "value": "□"},
        {"key": "ㄱ", "value": "그러므로"},
    ])
    create_template(base_hwpx, body_path, [
        {"key": "ㅂㄱ", "value": "본문상용구 예시입니다. 이 문단을 원하는 본문으로 바꾸세요."},
    ])
    return text_path, body_path
