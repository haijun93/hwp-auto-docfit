"""HWPX 순수 XML 내어쓰기(Hanging Indent) 계산 및 일괄 적용 모듈.

한/글 COM(`ParagraphShapeIndentAtCaret` / `GetPosBySet`)을 호출하지 않고,
문단 텍스트와 글자 모양(글꼴 크기·장평·자간)만으로 내어쓰기 기준 오프셋과
HWPUNIT 단위의 `(left, intent)` 여백 쌍을 계산해 HWPX `Contents/header.xml` 및
`Contents/section*.xml`에 직접 기록한다.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from xml.sax.saxutils import escape as xml_escape

from defusedxml import ElementTree as ET

from .attachment_block import (
    find_blocks as find_attachment_blocks,
    find_trailing_numbered_blocks,
    numbered_item_offset,
)
from .batch_format import (
    ParagraphStyle,
    StylePool,
    _rewrite_runs,
    _serialize,
    plain_text,
    tag,
)
from .document_rules import ParagraphSpacingTracker
from .fidelity.package import PackageSnapshot, build_package
from .hwpx import validate_hwpx
from .style_hierarchy import DOT_MARKERS, leading_marker, normalize_leading_dot


OFFICIAL_SYMBOLS: frozenset[str] = frozenset({
    "※", "ㅁ", "□", "■", "○", "●", "◎", "◇", "◆", "△", "▲", "▽", "▼",
    "▷", "▶", "◁", "◀", "▪", "▫", "ㆍ", "·", "‧", "•", "∙", "⋅", "‣", "⁃", "ㅇ",
    "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
    "❶", "❷", "❸", "❹", "❺", "❻", "❼", "❽", "❾", "❿",
    "➊", "➋", "➌", "➍", "➎", "➏", "➐", "➑", "➒", "➓",
    "㉠", "㉡", "㉢", "㉣", "㉤", "㉥", "㉦", "㉧", "㉨", "㉩", "㉪",
    "→", "←", "↑", "↓", "⇒", "⇐", "―", "–", "—", "-", "‒", "−",
})

ITEM_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*\d+(?:-\d+)+\s*[.)]"),
    re.compile(r"^\s*\d+\."),
    re.compile(r"^\s*\d+\)"),
    re.compile(r"^\s*[가-힣]\."),
    re.compile(r"^\s*[가-힣]\)"),
    re.compile(r"^\s*\([가-힣]\)"),
    re.compile(r"^\s*\(\d+\)"),
    re.compile(r"^\s*\[[가-힣]\]"),
)

_OPENING_BRACKET_QUOTE = frozenset("([{\"'“‘「『《〈（〔【")
_COLON_LABEL_RE = re.compile(r"([^\n\r:：]{1,30}?)[ \t]*[:：][ \t]+(?=\S)")
_BOLD_COLON_LABEL_RE = re.compile(r"^([^\n\r:：]{1,25}?)[ \t]*([:：])[ \t]+(\S.*)$")
_PAREN_LABEL_RE = re.compile(r"\(([^()]+)\)|\[([^\[\]]+)\]")

# 행정안전부 개조식 보고서 작성 표준 기본 기호 규칙:
# (symbol, lead_spaces, font, size_pt, paragraph_bold, marker_bold)
DEFAULT_SYMBOL_RULES: tuple[tuple[str, int, str, float, bool, bool], ...] = (
    ("□", 0, "HY견고딕", 17.0, False, True),
    ("ㅇ", 1, "한컴돋움", 15.0, True, False),
    ("-", 3, "휴먼명조", 14.0, False, False),
    ("※", 3, "한컴돋움", 13.0, False, False),
    ("*", 3, "한컴돋움", 13.0, False, False),
    ("•", 3, "한컴돋움", 13.0, False, False),
)

DEFAULT_SYMBOL_ALIASES: dict[str, str] = {
    "☞": "ㅇ",
    "○": "ㅇ",
    "ㅁ": "□",
    "**": "*",
    **{marker: "•" for marker in DOT_MARKERS if marker != "•"},
}

DEFAULT_FONT_TYPES: dict[str, str] = {
    "HY견고딕": "TTF",
    "HY헤드라인M": "TTF",
    "한컴돋움": "TTF",
    "휴먼명조": "TTF",
    "맑은 고딕": "TTF",
    "함초롬바탕": "TTF",
    "함초롬돋움": "TTF",
}


@dataclass
class ParagraphIndentAudit:
    index: int
    original_text: str
    formatted_text: str
    marker: str
    offset: int | None
    left: int
    intent: int
    size_pt: float
    font: str | None
    para_pr_id: str


@dataclass
class XmlHangingIndentResult:
    applied: int = 0
    fallback: int = 0
    char_styles: int = 0
    paragraph_styles: int = 0
    paragraphs: list[ParagraphIndentAudit] = field(default_factory=list)


def char_width_factor(ch: str) -> float:
    """한 글자의 글꼴 높이 대비 가로 폭 배수(COM 예비폭 계산 규칙과 동일)."""
    if not ch:
        return 0.5
    if ch in "()[]{}<>":
        return 0.42
    if unicodedata.east_asian_width(ch) in ("W", "F", "A"):
        return 1.0
    return 0.5


def prefix_width_hwpunit(
    text: str,
    offset: int,
    *,
    size_pt: float = 15.0,
    ratio: int = 100,
    spacing: int = 0,
) -> int:
    """문단 첫 글자부터 ``offset``까지의 가로 폭을 HWPUNIT 정수로 계산한다."""
    if not text or offset is None or offset <= 0:
        return 0
    height = round(float(size_pt) * 100)
    ratio_scale = (ratio if ratio else 100) / 100.0
    spacing_scale = (spacing or 0) / 100.0
    total = 0.0
    for ch in text[:offset]:
        total += height * char_width_factor(ch) * ratio_scale + height * spacing_scale
    return max(0, round(total))


def marker_end_offset(text: str | None) -> int | None:
    """문단 선행 항목기호(별표·번호·공문서 기호)가 끝나는 문자 인덱스를 반환한다."""
    if not text:
        return None
    stripped = text.lstrip()
    if not stripped:
        return None
    lead_len = len(text) - len(stripped)
    star_match = re.match(r"[*＊]+", stripped)
    if star_match:
        return lead_len + star_match.end()
    for pattern in ITEM_PATTERNS:
        m = pattern.match(stripped)
        if m:
            return lead_len + m.end()
    first = stripped[0]
    if first in OFFICIAL_SYMBOLS:
        return lead_len + 1
    if first in _OPENING_BRACKET_QUOTE:
        return None
    category = unicodedata.category(first)
    if category.startswith("P") or category.startswith("S"):
        return lead_len + 1
    return None


def _skip_spaces(text: str, index: int) -> int:
    while index < len(text) and text[index] in (" ", "\t"):
        index += 1
    return index


def _skip_corner_quote(text: str, index: int | None) -> int | None:
    if not text or index is None or index <= 0 or index >= len(text):
        return index
    while index < len(text) and text[index] in ("「", "『"):
        index += 1
    return index if index < len(text) else None


def hanging_indent_offset(text: str | None, *, rule: str = "body_start") -> int | None:
    """문단에서 내어쓰기 정렬 기준이 되는 문자 오프셋을 반환한다.

    - 최상위 항목 제목(``ㅁ``/``□``)은 내어쓰기하지 않으므로 ``0``을 반환한다.
    - ``* 항세기: 기후가...``처럼 항목기호 뒤 짧은 콜론 라벨(공백 제외 1~12자)이 있으면
      콜론과 뒤 공백 다음 첫 글자 오프셋을 반환한다.
    - 일반 항목기호(``ㅇ (삼체 행성 상황) ...``, ``- 항세기*와 ...``)는 기호와 뒤 공백
      다음 첫 글자 오프셋을 반환한다(괄호 라벨은 건너뛰지 않음, 2026-10-10 규칙).
    - 본문 첫 글자가 여는 낫표(``「``/``『``)이면 그 안쪽 첫 글자 오프셋을 반환한다.
    """
    if not text or rule in ("fixed", "none"):
        return None
    stripped = text.lstrip()
    if not stripped:
        return None
    if stripped[0] in ("ㅁ", "□") and (len(stripped) == 1 or stripped[1].isspace()):
        return 0
    marker_end = marker_end_offset(text)
    if marker_end is None:
        return None
    idx = _skip_spaces(text, marker_end)
    if idx >= len(text):
        return None
    if rule == "after_marker":
        return _skip_corner_quote(text, idx)
    colon_match = _COLON_LABEL_RE.match(text[idx:])
    if colon_match:
        label_chars = re.sub(r"\s+", "", colon_match.group(1))
        if 1 <= len(label_chars) <= 12:
            after_colon = idx + colon_match.end()
            if after_colon < len(text):
                idx = after_colon
    return _skip_corner_quote(text, idx)


def hanging_indent_pair(
    text: str | None,
    *,
    size_pt: float = 15.0,
    ratio: int = 100,
    spacing: int = 0,
    base_left: int = 0,
    rule: str = "body_start",
) -> tuple[int, int] | None:
    """문단의 XML ``(left, intent)`` HWPUNIT 여백 쌍을 반환한다."""
    offset = hanging_indent_offset(text, rule=rule)
    if offset is None:
        return None
    if offset <= 0:
        return (0, 0)
    width = prefix_width_hwpunit(
        text,
        offset,
        size_pt=size_pt,
        ratio=ratio,
        spacing=spacing,
    )
    if width <= 0:
        return None
    left = max(0, int(base_left)) + width
    intent = -width
    return (left, intent)


def _reference_marker_key(text: str) -> str | None:
    """기준 서식의 기호+라벨 유형 키를 만든다(기호별 서로 다른 원본값 보존)."""
    if not text:
        return None
    stripped = text.lstrip()
    if not stripped:
        return None
    if stripped.startswith(("**", "＊＊")):
        marker = "**"
    elif stripped.startswith(("*", "＊")):
        marker = "*"
    elif stripped.startswith(("ㅁ", "□")) and (len(stripped) == 1 or stripped[1].isspace()):
        return "□"
    elif stripped.startswith(("ㅇ", "○")) and (len(stripped) == 1 or stripped[1].isspace()):
        marker = "ㅇ"
    elif stripped.startswith(("-", "–", "—")):
        marker = "-"
    elif stripped.startswith("※"):
        marker = "※"
    else:
        return None
    offset = marker_end_offset(text)
    if offset is None:
        return marker
    idx = _skip_spaces(text, offset)
    match = _COLON_LABEL_RE.match(text[idx:]) if idx < len(text) else None
    if match and 1 <= len(re.sub(r"\s+", "", match.group(1))) <= 12:
        label = re.sub(r"\s+", "", match.group(1)).casefold()
        return f"{marker}:label:{label}"
    return marker


def reference_marker_indent_pairs(path: str | Path) -> dict[str, tuple[int, int]]:
    """기준 HWPX의 항목별 대표 case `(left, intent)`를 빈도 최빈값으로 추출한다.

    기본 서식은 기호·콜론 라벨별로 실제 여백 값이 다르므로 일반 글자폭 산식으로
    재구성하지 않는다. 저장된 case 값을 그대로 참조한다. 반환값은 키별 최빈값이며
    동률이면 문서에서 먼저 나온 값을 사용한다.
    """
    from collections import Counter
    from zipfile import ZipFile

    namespaces = {
        "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
        "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    }
    with ZipFile(path) as archive:
        header = ET.fromstring(archive.read("Contents/header.xml"))
        styles = {node.get("id", ""): node for node in header.findall(".//hh:paraPr", namespaces)}
        samples: dict[str, list[tuple[int, int]]] = {}
        section_names = sorted(
            name for name in archive.namelist()
            if re.fullmatch(r"Contents/section\d+\.xml", name)
        )
        for section_name in section_names:
            section = ET.fromstring(archive.read(section_name))
            for paragraph in section.findall(".//hp:p", namespaces):
                text = "".join(
                    (node.text or "")
                    for node in paragraph.iter()
                    if node.tag.rsplit("}", 1)[-1] == "t"
                )
                key = _reference_marker_key(text)
                if key is None:
                    continue
                style = styles.get(paragraph.get("paraPrIDRef", ""))
                if style is None:
                    continue
                case = style.find(".//hp:case", namespaces)
                if case is None:
                    continue
                margin = next(
                    (node for node in case.iter() if node.tag.rsplit("}", 1)[-1] == "margin"),
                    None,
                )
                if margin is None:
                    continue
                values = {
                    node.tag.rsplit("}", 1)[-1]: node.get("value")
                    for node in margin
                }
                try:
                    pair = (int(values["left"]), int(values["intent"]))
                except (KeyError, TypeError, ValueError):
                    continue
                samples.setdefault(key, []).append(pair)
                if ":label:" in key:
                    samples.setdefault(key.split(":label:", 1)[0] + ":label", []).append(pair)
    result: dict[str, tuple[int, int]] = {}
    for key, values in samples.items():
        counts = Counter(values)
        result[key] = max(dict.fromkeys(values), key=lambda value: counts[value])
    return result


def reference_hanging_indent_pair(
    text: str | None,
    reference_pairs: dict[str, tuple[int, int]],
) -> tuple[int, int] | None:
    """기준 HWPX에서 추출한 동일 기호/라벨 문단의 대표 여백을 반환한다."""
    key = _reference_marker_key(text or "")
    if key is None:
        return None
    if key in reference_pairs:
        return reference_pairs[key]
    # 라벨이 기준문서에 없으면 해당 기호의 일반 문단 대표값만 안전하게 대체한다.
    if ":label:" in key:
        generic_label_key = key.split(":label:", 1)[0] + ":label"
        if generic_label_key in reference_pairs:
            return reference_pairs[generic_label_key]
    marker = key.split(":", 1)[0]
    return reference_pairs.get(marker)


def restore_reference_indent_geometry(
    source: str | Path,
    reference: str | Path,
    target: str | Path | None = None,
) -> dict[str, int]:
    """Restore only marker paragraphs' left/intent geometry from the reference HWPX.

    This is intended as a final saved-artifact guard: later COM/page-fit operations may
    alter paragraph margins after the initial XML formatting pass. All text, runs,
    character styles, spacing, and other paragraph properties remain untouched.
    """
    source_path = Path(source)
    target_path = Path(target) if target is not None else source_path

    reference_pairs = reference_marker_indent_pairs(reference)
    snapshot = PackageSnapshot.load(source_path)
    if snapshot.format != "hwpx":
        raise ValueError("reference indent restoration requires an HWPX package")
    header_bytes = snapshot.read("Contents/header.xml")
    header = ET.fromstring(header_bytes)
    pool = StylePool(header)
    metadata = validate_hwpx(source_path)
    sections = {name: ET.fromstring(snapshot.read(name)) for name in metadata["section_names"]}
    changed: set[str] = set()
    checked = repaired = missing = 0

    for name, root in sections.items():
        for paragraph in root.iter():
            if tag(paragraph) != "p":
                continue
            text = plain_text(paragraph) or ""
            pair = reference_hanging_indent_pair(text, reference_pairs)
            if pair is None:
                continue
            checked += 1
            base_id = paragraph.get("paraPrIDRef", "")
            base = pool.sources["paraProperties"].get(base_id)
            if base is None:
                missing += 1
                continue
            if not any(tag(node) == "left" for node in base.iter()) or not any(
                tag(node) == "intent" for node in base.iter()
            ):
                missing += 1
                continue
            spec = ParagraphStyle(
                text=text,
                para_extra=(("left", pair[0]), ("intent", pair[1])),
            )
            new_id = pool.para(base_id, spec)
            if new_id != base_id:
                paragraph.set("paraPrIDRef", new_id)
                repaired += 1
                changed.add(name)

    if checked == 0:
        return {"checked": 0, "repaired": 0, "missing": 0}
    if missing:
        raise ValueError(f"reference indent restoration lacks paragraph properties for {missing} paragraph(s)")
    if not changed:
        return {"checked": checked, "repaired": 0, "missing": 0}

    replacements = {name: _serialize(sections[name], snapshot.read(name)) for name in changed}
    replacements["Contents/header.xml"] = _serialize(header, header_bytes)
    payload = build_package(snapshot, replacements)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".reference-indent-", suffix=".hwpx", dir=target_path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
        validate_hwpx(temporary)
        os.replace(temporary, target_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"checked": checked, "repaired": repaired, "missing": 0}


def attachment_numbered_pair(
    text: str | None,
    anchor_width: int,
    *,
    size_pt: float = 15.0,
    ratio: int = 100,
    spacing: int = 0,
) -> tuple[int, int] | None:
    """번호 붙임 목록('붙임 : 1. ...' / '   2. ...')의 세로 번호 정렬 + 본문 내어쓰기 여백 쌍을 계산한다.

    첫 항목의 번호 시작 가로폭(``anchor_width``)에 후속 항목의 번호 시작 위치를 맞추고,
    줄바꿈된 둘째 줄 이후는 번호 뒤 본문 시작 위치에 맞춘다.
    """
    if not text:
        return None
    offset = numbered_item_offset(text)
    if offset is None:
        return None
    dot_index = text.find(".", offset)
    if dot_index < 0:
        return None
    marker_end = _skip_spaces(text, dot_index + 1)
    if marker_end <= offset:
        marker_end = dot_index + 1
    prefix_width = (
        prefix_width_hwpunit(text, offset, size_pt=size_pt, ratio=ratio, spacing=spacing)
        if offset > 0
        else 0
    )
    marker_width = prefix_width_hwpunit(
        text,
        marker_end,
        size_pt=size_pt,
        ratio=ratio,
        spacing=spacing,
    )
    if marker_width <= 0:
        return None
    effective_anchor = max(anchor_width, prefix_width)
    target_left = effective_anchor + marker_width - prefix_width
    target_indent = -marker_width
    if target_left <= 0 or target_left + target_indent < 0:
        return None
    return (target_left, target_indent)


def find_symbol_rule(
    text: str | None,
    rules: tuple[tuple[str, int, str, float, bool, bool], ...] = DEFAULT_SYMBOL_RULES,
    aliases: dict[str, str] = DEFAULT_SYMBOL_ALIASES,
) -> tuple[str, int, str, float, bool, bool] | None:
    """문단 선행 기호에 해당하는 표준서식 기호 규칙을 반환한다."""
    if not text:
        return None
    stripped = text.lstrip()
    if not stripped:
        return None
    detected_marker, detected_role = leading_marker(stripped)
    if detected_role == "장":
        return ("(장)", 0, "HY헤드라인M", 20.0, True, False)
    if stripped[0] in DOT_MARKERS:
        return next((r for r in rules if r[0] == "•"), None)
    for rule in rules:
        if stripped.startswith(rule[0]):
            return rule
    for alias, target in aliases.items():
        if stripped.startswith(alias):
            for rule in rules:
                if rule[0] == target:
                    return rule
    return None


def detect_label_bold_spans(text: str | None) -> tuple[tuple[int, int], ...]:
    """문두 콜론 라벨 또는 괄호 라벨의 굵게 범위 ``((start, end),)``를 반환한다."""
    if not text:
        return ()
    stripped = text.lstrip()
    if stripped.startswith(("*", "**", "※")):
        return ()
    end = marker_end_offset(text)
    if end is None:
        return ()
    end = _skip_spaces(text, end)
    rest = text[end:]
    colon_match = _BOLD_COLON_LABEL_RE.match(rest)
    if colon_match and colon_match.group(1).strip():
        label = colon_match.group(1).strip()
        start = end + rest.find(label)
        return ((start, start + len(label)),)
    if "(" in rest:
        paren_match = _PAREN_LABEL_RE.match(rest)
        if paren_match:
            return ((end + paren_match.start(), end + paren_match.end()),)
    return ()


def _char_size_pt(header, paragraph, default_pt: float = 15.0) -> float:
    chars = {x.get("id"): x for x in header.iter() if tag(x) == "charPr"}
    for run in paragraph:
        if tag(run) != "run":
            continue
        c = chars.get(run.get("charPrIDRef") or "0")
        if c is not None and (c.get("height") or "").isdigit():
            return int(c.get("height")) / 100.0
    return default_pt


def build_hwpx_from_text_file(
    txt_path: str | Path,
    target_hwpx_path: str | Path,
    *,
    template_hwpx_path: str | Path | None = None,
) -> Path:
    """UTF-8/CP949 텍스트 파일의 각 줄을 HWPX 문단으로 담아 유효한 HWPX 패키지를 생성한다."""
    txt_file = Path(txt_path)
    text_content = None
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            text_content = txt_file.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if text_content is None:
        raise ValueError(f"텍스트 인코딩을 읽을 수 없습니다: {txt_file}")

    lines = text_content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if template_hwpx_path is None:
        candidate = Path(__file__).resolve().parents[1] / "resources" / "서식예시" / "기본 서식.hwpx"
        if candidate.is_file():
            template_hwpx_path = candidate

    target = Path(target_hwpx_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if template_hwpx_path is not None and Path(template_hwpx_path).is_file():
        snapshot = PackageSnapshot.load(template_hwpx_path)
        sec_bytes = snapshot.read("Contents/section0.xml")
        sec_root = ET.fromstring(sec_bytes)

        proto_p = next(x for x in sec_root.iter() if tag(x) == "p")
        proto_run = next(x for x in sec_root.iter() if tag(x) == "run")
        proto_t = next(x for x in sec_root.iter() if tag(x) == "t")

        setup_children = []
        if len(sec_root) > 0:
            for run in sec_root[0]:
                if tag(run) == "run":
                    for child in run:
                        if tag(child) in ("secPr", "ctrl"):
                            setup_children.append(copy.deepcopy(child))
                    break

        for child in list(sec_root):
            sec_root.remove(child)

        for idx, line in enumerate(lines):
            p_elem = copy.deepcopy(proto_p)
            for child in list(p_elem):
                p_elem.remove(child)
            p_elem.attrib.clear()
            p_elem.attrib.update({
                "id": "0",
                "paraPrIDRef": "0",
                "styleIDRef": "0",
                "pageBreak": "0",
                "columnBreak": "0",
                "merged": "0",
            })
            run_elem = copy.deepcopy(proto_run)
            for child in list(run_elem):
                run_elem.remove(child)
            run_elem.attrib.clear()
            run_elem.set("charPrIDRef", "0")
            if idx == 0 and setup_children and find_symbol_rule(line) is None and hanging_indent_offset(line) is None:
                for sc in setup_children:
                    run_elem.append(copy.deepcopy(sc))
            t_elem = copy.deepcopy(proto_t)
            for child in list(t_elem):
                t_elem.remove(child)
            t_elem.attrib.clear()
            t_elem.text = line
            t_elem.tail = None
            run_elem.append(t_elem)
            p_elem.append(run_elem)
            sec_root.append(p_elem)

        replacements = {
            "Contents/section0.xml": _serialize(sec_root, sec_bytes),
            "Preview/PrvText.txt": "\r\n".join(lines).encode("utf-8"),
        }
        payload = build_package(snapshot, replacements)
        target.write_bytes(payload)
        validate_hwpx(target)
        return target

    raise FileNotFoundError("HWPX 템플릿 파일을 찾을 수 없습니다.")


def apply_xml_hanging_indent(
    source: str | Path,
    target: str | Path | None = None,
    *,
    format_markers: bool = True,
    ratio: int = 100,
    line_percent: int = 160,
) -> XmlHangingIndentResult:
    """HWPX 문서의 모든 항목기호 문단과 끝 붙임 번호 목록에 순수 XML 내어쓰기를 일괄 적용한다."""
    source_path = Path(source)
    target_path = Path(target) if target is not None else None
    if target_path is not None and source_path.resolve() == target_path.resolve():
        raise ValueError("원본 HWPX와 출력 경로가 같으면 안 됩니다.")

    metadata = validate_hwpx(source_path)
    snapshot = PackageSnapshot.load(source_path)
    header_bytes = snapshot.read("Contents/header.xml")
    header = ET.fromstring(header_bytes)
    pool = StylePool(header)
    sections = {name: ET.fromstring(snapshot.read(name)) for name in metadata["section_names"]}

    result = XmlHangingIndentResult()
    changed: set[str] = set()
    spacing_table = {"chapter": 15, "midtitle": 15, "box": 15, "circle": 8, "dash": 4, "note": 0}

    for name in metadata["section_names"]:
        root = sections[name]
        paragraphs = [child for child in root if tag(child) == "p"]
        raw_texts = [plain_text(p) for p in paragraphs]

        # 1. 붙임 묶음('붙임 ...' ~ '끝.')과 끝 번호 붙임 목록 파악
        attach_blocks = find_attachment_blocks(raw_texts)
        attach_indices = {idx for start, end in attach_blocks for idx in range(start, end + 1)}
        trailing_blocks = find_trailing_numbered_blocks(raw_texts)
        trailing_map: dict[int, int] = {}
        for start, end in trailing_blocks:
            for idx in range(start, end + 1):
                trailing_map[idx] = start

        # 붙임 묶음은 항목기호 ㅇ 글꼴·크기(한컴돋움 15pt)와 맞춘다.
        circle_rule = next((r for r in DEFAULT_SYMBOL_RULES if r[0] == "ㅇ"), None)
        attach_font = circle_rule[2] if circle_rule else "한컴돋움"
        attach_size = float(circle_rule[3]) if circle_rule else 15.0

        # 끝 번호 붙임 목록의 첫 번호('1.') 가로 기준폭 계산
        anchor_widths: dict[int, int] = {}
        for start, _ in trailing_blocks:
            first_text = raw_texts[start] or ""
            num_off = numbered_item_offset(first_text)
            size_for_anchor = attach_size if format_markers else _char_size_pt(header, paragraphs[start], attach_size)
            anchor_widths[start] = (
                prefix_width_hwpunit(first_text, num_off, size_pt=size_for_anchor, ratio=ratio)
                if num_off is not None
                else 0
            )

        tracker = ParagraphSpacingTracker()

        for idx, paragraph in enumerate(paragraphs):
            original_text = raw_texts[idx]
            if original_text is None or not original_text.strip():
                tracker.spacing_for(original_text or "", spacing_table, 150)
                continue

            readable = normalize_leading_dot(original_text)
            prev_pt = tracker.spacing_for(readable, spacing_table, 150) if format_markers else None
            rule = find_symbol_rule(readable) if format_markers else None

            formatted = readable
            font_name: str | None = None
            font_type: str | None = None
            size_pt: float | None = None
            bold: bool | None = None
            bold_spans: tuple[tuple[int, int], ...] = ()
            plain_spans: tuple[tuple[int, int], ...] = ()
            indent_pair: tuple[int, int] | None = None
            marker_label = ""

            if rule is not None:
                symbol, lead, r_font, r_size, para_bold, marker_bold = rule
                if readable.lstrip().startswith("**"):
                    lead = max(0, lead - 1)
                formatted = " " * lead + readable.lstrip()
                font_name = r_font
                font_type = DEFAULT_FONT_TYPES.get(r_font, "TTF")
                size_pt = float(r_size)
                bold = True if para_bold else None
                spans = list(detect_label_bold_spans(formatted))
                if marker_bold and not para_bold:
                    marker_pos = len(formatted) - len(formatted.lstrip())
                    spans.append((marker_pos, marker_pos + 1))
                bold_spans = tuple(spans)
                marker_label = leading_marker(formatted)[0] or symbol
                indent_pair = hanging_indent_pair(
                    formatted,
                    size_pt=size_pt,
                    ratio=ratio,
                )
            elif idx in trailing_map:
                anchor_idx = trailing_map[idx]
                anchor_w = anchor_widths.get(anchor_idx, 0)
                if format_markers:
                    font_name = attach_font
                    font_type = DEFAULT_FONT_TYPES.get(attach_font, "TTF")
                    size_pt = attach_size
                effective_size = size_pt or _char_size_pt(header, paragraph, attach_size)
                indent_pair = attachment_numbered_pair(
                    formatted,
                    anchor_w,
                    size_pt=effective_size,
                    ratio=ratio,
                )
                marker_label = "붙임번호"
            else:
                if idx in attach_indices and format_markers:
                    font_name = attach_font
                    font_type = DEFAULT_FONT_TYPES.get(attach_font, "TTF")
                    size_pt = attach_size
                effective_size = size_pt or _char_size_pt(header, paragraph, 15.0)
                indent_pair = hanging_indent_pair(
                    formatted,
                    size_pt=effective_size,
                    ratio=ratio,
                )
                if indent_pair is not None:
                    marker_label = leading_marker(formatted)[0] or formatted.lstrip().split()[0]

            if rule is None and indent_pair is None and prev_pt is None and font_name is None:
                result.fallback += 1
                continue

            para_extra: list[tuple[str, object]] = []
            if indent_pair is not None:
                para_extra.extend([("left", indent_pair[0]), ("intent", indent_pair[1])])

            spec = ParagraphStyle(
                text=formatted,
                font=font_name,
                font_type=font_type,
                size_pt=size_pt,
                bold=bold,
                ratio=ratio if (rule is not None or idx in attach_indices) else None,
                line_percent=line_percent if (rule is not None or idx in attach_indices) else None,
                prev_pt=prev_pt,
                bold_spans=bold_spans,
                plain_spans=plain_spans,
                para_extra=tuple(sorted(para_extra)),
            )

            if not pool.check(paragraph, spec):
                result.fallback += 1
                continue

            _rewrite_runs(paragraph, spec, pool)
            new_para_id = pool.para(paragraph.get("paraPrIDRef"), spec)
            paragraph.set("paraPrIDRef", new_para_id)

            final_text = plain_text(paragraph)
            if (final_text or "").strip() != original_text.strip():
                raise ValueError("XML 내어쓰기 적용 중 본문 글자가 손실되었습니다.")

            eff_size = size_pt or _char_size_pt(header, paragraph, 15.0)
            eff_offset = (
                numbered_item_offset(final_text)
                if marker_label == "붙임번호"
                else hanging_indent_offset(final_text)
            )
            result.paragraphs.append(
                ParagraphIndentAudit(
                    index=idx,
                    original_text=original_text,
                    formatted_text=final_text or "",
                    marker=marker_label,
                    offset=eff_offset,
                    left=indent_pair[0] if indent_pair is not None else 0,
                    intent=indent_pair[1] if indent_pair is not None else 0,
                    size_pt=eff_size,
                    font=font_name,
                    para_pr_id=new_para_id,
                )
            )
            result.applied += 1
            changed.add(name)

    result.char_styles = len(pool.groups["charProperties"]) - len(pool.sources["charProperties"])
    result.paragraph_styles = len(pool.groups["paraProperties"]) - len(pool.sources["paraProperties"])
    if target_path is None:
        return result

    replacements = {name: _serialize(sections[name], snapshot.read(name)) for name in changed}
    if changed:
        replacements["Contents/header.xml"] = _serialize(header, header_bytes)
    content = build_package(snapshot, replacements)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".indent-", suffix=".hwpx", dir=target_path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        validate_hwpx(temporary)
        os.replace(temporary, target_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return result
