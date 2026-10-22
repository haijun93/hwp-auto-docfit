"""준말 관리 HWPX 문서(사용자가 한/글에서 직접 고치는 준말·본말 목록).

형식: ``#준말`` 문단 다음부터 다음 ``#`` 표식 직전까지가 본말이다(``#+``는 상용구 표식이라 제외).
본말의 첫 문단이 ``[서식:제목1]`` 같은 서식 표 표식이면 서식 표 준말, 아니면 문구 준말이다.
문구 본말은 빈 문단을 빼고 남은 문단을 빈칸 하나로 이어 한 줄로 쓴다.
첫 표식 앞 문단과 ``※``로 시작하는 문단은 설명으로 보고 무시한다.

작업을 시작할 때마다 문서를 다시 읽는다(캐시하지 않음). XML은 defusedxml만 쓴다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from . import abbreviations as registry

DOCUMENT_FOLDER = "준말관리"
DOCUMENT_NAME = "준말관리.hwpx"
SOURCES = ("document", "settings")

# 문서의 서식 표식 → 등록표의 서식 표 종류
FORMAT_MARKERS: dict[str, str] = {
    "제목1": "title1",
    "제목2": "title2",
    "개요": "overview",
    "중제목": "midtitle",
    "붙임1": "attach1",
    "붙임2": "attach2",
    "표": "table",
}
_MARKER_OF_KIND = {kind: marker for marker, kind in FORMAT_MARKERS.items()}
_KEY_LINE = re.compile(r"^\s*#(?!\+)\s*(.*?)\s*$")
_FORMAT_LINE = re.compile(r"^\s*\[\s*서식\s*:\s*(.*?)\s*\]\s*$")

GUIDE_LINES = [
    "준말 관리 문서 — 이 파일을 한/글에서 직접 고치고 저장하세요.",
    "※ '서식 적용'·'한 번에 적용'을 시작할 때마다 앱이 이 문서를 다시 읽습니다.",
    "※ 항목은 # 뒤에 준말을 적은 문단으로 시작하고, 바로 아래 문단에 본말을 씁니다. 다음 # 문단 전까지가 본말입니다.",
    "※ 문서에서 '준말: 내용' 줄은 본말로 바뀝니다. 본말이 여러 문단이면 빈칸 하나로 이어 한 줄이 됩니다.",
    "※ 서식 표로 바꾸려면 본말에 [서식:제목1] [서식:제목2] [서식:개요] [서식:중제목] [서식:붙임1] [서식:붙임2] [서식:표] 중 하나를 씁니다.",
    "※ 이 ※ 문단과 첫 # 앞의 문단은 설명이라 읽지 않습니다. 준말은 12자 이내, 같은 준말은 한 번만 씁니다.",
]


def document_path(root: str | Path) -> Path:
    return Path(root) / DOCUMENT_FOLDER / DOCUMENT_NAME


def default_base_hwpx() -> Path | None:
    """문서 뼈대로 쓸 앱 내장 기본 서식 HWPX."""
    candidates = [Path(__file__).resolve().parents[1] / "resources" / "서식예시" / "기본 서식.hwpx"]
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        candidates.append(Path(bundle) / "resources" / "서식예시" / "기본 서식.hwpx")
    return next((path for path in candidates if path.is_file()), None)


def _paragraphs(path: Path) -> list[str]:
    from defusedxml import ElementTree as ET

    from .hwpx import open_hwpx_safely
    from .hwpx_idioms import _local_name, _paragraph_text

    with open_hwpx_safely(path) as archive:
        names = sorted(
            (name for name in archive.namelist() if re.fullmatch(r"Contents/section\d+\.xml", name)),
            key=lambda name: int(re.search(r"section(\d+)", name).group(1)),
        )
        paragraphs: list[str] = []
        for name in names:
            root = ET.fromstring(archive.read(name))
            # 표 안 문단도 문서 순서대로 읽는다. 표 칸 안의 문단은 바깥 문단의 글에 섞이지 않게
            # 가장 안쪽 문단 단위로 모은다.
            for node in root.iter():
                if _local_name(node.tag) != "p":
                    continue
                if any(_local_name(child.tag) == "p" for child in node.iter() if child is not node):
                    continue
                paragraphs.append(_paragraph_text(node))
    return paragraphs


def parse_lines(lines: list[str]) -> tuple[dict[str, dict], list[str]]:
    """문단 글 목록을 등록표와 오류 목록으로 바꾼다. 잘못된 항목만 빼고 나머지는 쓴다."""
    blocks: list[tuple[str, list[str]]] = []
    for line in lines:
        text = line.replace("\n", " ").replace("\t", " ")
        marker = _KEY_LINE.fullmatch(text)
        if marker:
            blocks.append((marker.group(1), []))
        elif blocks and not text.strip().startswith("※"):
            blocks[-1][1].append(text)

    entries: dict[str, dict] = {}
    errors: list[str] = []
    seen: set[str] = set()
    for raw_key, body in blocks:
        raw = raw_key.strip()
        if not raw:
            errors.append("# 뒤에 준말이 없습니다.")
            continue
        if len(raw) > registry._MAX_KEY:
            errors.append(f"'{raw}': 준말은 {registry._MAX_KEY}자 이내로 써 주세요.")
            continue
        key = registry.clean_key(raw)
        if not key:
            errors.append(f"'{raw}': 준말에는 빈칸이나 콜론(:)을 쓸 수 없습니다.")
            continue
        if key in seen:
            errors.append(f"'{key}': 같은 준말이 두 번 있습니다(뒤 항목은 쓰지 않음).")
            continue
        seen.add(key)
        values = [item.strip() for item in body if item.strip()]
        if not values:
            errors.append(f"'{key}': 본말이 비어 있습니다.")
            continue
        format_marker = _FORMAT_LINE.fullmatch(values[0])
        if format_marker:
            kind = FORMAT_MARKERS.get(format_marker.group(1).replace(" ", ""))
            if kind is None:
                errors.append(f"'{key}': 알 수 없는 서식 표식 [서식:{format_marker.group(1)}] — "
                              + ", ".join(FORMAT_MARKERS) + " 중 하나를 써 주세요.")
                continue
            if kind == "midtitle" and not registry.roman_of_key(key):
                errors.append(f"'{key}': 중제목 준말은 끝에 번호(1~12)가 있어야 합니다(예: 로1).")
                continue
            entries[key] = {"type": "format", "value": kind}
            continue
        value = " ".join(values)
        if len(value) > registry._MAX_TEXT:
            errors.append(f"'{key}': 본말은 {registry._MAX_TEXT}자 이내로 써 주세요.")
            continue
        entries[key] = {"type": "text", "value": value}
    return entries, errors


def parse_document(path: str | Path) -> tuple[dict[str, dict], list[str]]:
    """준말 문서를 읽어 (등록표, 오류 목록)을 돌려준다. 파일이 없거나 깨졌으면 빈 등록표와 오류 1건."""
    source = Path(path)
    if not source.is_file():
        return {}, [f"준말 문서가 없습니다: {source}"]
    try:
        lines = _paragraphs(source)
    except Exception as exc:  # 손상·잠금·형식 오류는 작업을 막지 않고 알린다.
        return {}, [f"준말 문서를 읽지 못했습니다({source.name}): {exc}"]
    return parse_lines(lines)


def document_lines(entries: dict) -> list[str]:
    lines = list(GUIDE_LINES)
    for key, spec in registry.normalize(entries).items():
        lines.append("#" + key)
        if spec["type"] == "format":
            lines.append(f"[서식:{_MARKER_OF_KIND[spec['value']]}]")
        else:
            lines.append(str(spec["value"]))
    return lines


def create_document(base_hwpx: str | Path, target: str | Path, entries: dict) -> Path:
    """준말 문서를 만든다. 이미 있으면 덮어쓰지 않고 그대로 돌려준다."""
    from .hwpx_idioms import write_paragraph_document

    def verify(temp: Path) -> None:
        parsed, errors = parse_document(temp)
        if errors or set(parsed) != set(registry.normalize(entries)):
            raise ValueError("만든 준말 문서를 다시 읽은 결과가 다릅니다: " + "; ".join(errors))

    return write_paragraph_document(base_hwpx, target, document_lines(entries), verify)


def initial_entries(settings: dict) -> dict[str, dict]:
    """처음 만드는 문서에 넣을 항목: 기본 준말 + 설정에 저장된 사용자 준말(설정 값은 지우지 않음)."""
    entries = registry.merge_with_defaults(settings.get("abbreviations"), True)
    return registry.normalize(entries)


def source_of(settings: dict) -> str:
    """설정의 준말 출처. 앱 기본값(settings_schema)은 "document"이고, 키가 없는 옛 설정 묶음은 "settings"."""
    value = settings.get("abbreviation_source", "settings")
    return value if value in SOURCES else "settings"


def ensure_document(settings: dict, root: str | Path, base_hwpx: str | Path | None = None) -> Path | None:
    """문서가 없으면 만들어 준다. 만들 수 없으면 None."""
    target = document_path(root)
    if target.is_file():
        return target
    base = Path(base_hwpx) if base_hwpx else default_base_hwpx()
    if base is None or not base.is_file():
        return None
    try:
        return create_document(base, target, initial_entries(settings))
    except Exception:
        return None


def effective_registry(settings: dict, root: str | Path | None, base_hwpx: str | Path | None = None):
    """작업에 쓸 준말 등록표. (등록표, 오류 목록, 실제 출처 "document"|"settings")를 돌려준다.

    출처가 문서이면 매번 문서를 새로 읽는다. 문서를 만들 수도 읽을 수도 없으면 설정 값으로 동작한다.
    """
    use_defaults = settings.get("abbreviation_defaults", True)
    settings_registry = registry.merge_with_defaults(settings.get("abbreviations"), use_defaults)
    if source_of(settings) != "document" or root is None:
        return settings_registry, [], "settings"
    path = ensure_document(settings, root, base_hwpx)
    if path is None:
        return settings_registry, ["준말 문서를 만들 수 없어 앱 설정의 준말을 씁니다."], "settings"
    entries, errors = parse_document(path)
    if not entries and errors and not path.is_file():
        return settings_registry, errors, "settings"
    saved = registry.normalize(settings.get("abbreviations"))
    for key, spec in entries.items():
        # 문서로 표현할 수 없는 '배운 표 서식'은 설정에 저장된 같은 준말의 값을 이어 쓴다.
        old = saved.get(key)
        if spec == {"type": "format", "value": "table"} and old and old.get("style"):
            spec["style"] = old["style"]
    merged = registry.normalize(registry.DEFAULT_ENTRIES) if use_defaults else {}
    merged.update(entries)
    return merged, errors, "document"
