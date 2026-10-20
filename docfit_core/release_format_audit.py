"""Fail-closed, deterministic HWPX checks for the release formatting contract.

These checks are structural safeguards, not a substitute for rendering in Hancom.
All XML is parsed with defusedxml and the input archive is never modified.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import re
from zipfile import ZipFile

from defusedxml import ElementTree as ET


HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HH = "http://www.hancom.co.kr/hwpml/2011/head"
NS = {"hp": HP, "hh": HH}
MARKER = re.compile(
    r"^\s*(?:□|ㅁ|ㅇ|○|●|◦|▪|▫|■|◆|◇|※|\*\*?|-|\d+[.)])"
    r"(?:\s+|(?=[(\[（]))\S"
)
TOP_LEVEL_MARKER = re.compile(r"^\s*(?:ㅁ|□)\s+\S")


@dataclass
class ParagraphFinding:
    text: str
    para_id: str
    left: int | None
    indent: int | None
    status: str
    reason: str = ""


def _text(paragraph: ET.Element) -> str:
    out: list[str] = []
    for node in paragraph.iter():
        name = node.tag.rsplit("}", 1)[-1]
        if name == "t":
            if node.text:
                out.append(node.text)
            for child in node:
                if child.tag.rsplit("}", 1)[-1] in {"fwSpace", "nbSpace"}:
                    out.append(" ")
                if child.tail:
                    out.append(child.tail)
        elif name == "tab":
            out.append("\t")
        elif name in {"fwSpace", "nbSpace"}:
            out.append(" ")
    return "".join(out).strip("\r\n")


def _paragraph_margins(para_pr: ET.Element) -> tuple[int | None, int | None]:
    # Hancom stores both unit-specific case and default values under switch.
    # Prefer HWPUnitChar case; otherwise use the default case.
    cases = list(para_pr.findall(".//hp:case", NS))
    defaults = list(para_pr.findall(".//hp:default", NS))
    candidates = cases + defaults
    for candidate in candidates:
        margin = candidate.find(".//hh:margin", NS)
        if margin is None:
            margin = candidate.find(".//hp:margin", NS)
        if margin is None:
            continue
        values: dict[str, int] = {}
        for child in margin:
            key = child.tag.rsplit("}", 1)[-1]
            if key in {"left", "intent"}:
                try:
                    values[key] = int(child.get("value", ""))
                except (TypeError, ValueError):
                    return None, None
        if "left" in values and "intent" in values:
            return values["left"], values["intent"]
    return None, None


def inspect_hanging_indent(path: str | Path, reference_path: str | Path | None = None) -> dict:
    """Inspect marker geometry, optionally comparing exact pairs with a reference HWPX."""
    source = Path(path)
    reference_pairs = {}
    if reference_path is not None:
        from .xml_hanging_indent import reference_marker_indent_pairs
        reference_pairs = reference_marker_indent_pairs(reference_path)
    with ZipFile(source) as archive:
        header = ET.fromstring(archive.read("Contents/header.xml"))
        para_styles = {
            node.get("id", ""): node
            for node in header.findall(".//hh:paraPr", NS)
        }
        section_names = sorted(
            (name for name in archive.namelist()
             if re.fullmatch(r"Contents/section\d+\.xml", name)),
            key=lambda name: int(re.search(r"\d+", name).group()),
        )
        if not section_names or not para_styles:
            raise ValueError("HWPX has no readable section or paragraph-style table")
        findings: list[ParagraphFinding] = []
        all_paragraphs: list[tuple[str, ET.Element, str]] = []
        seen_texts: dict[str, int] = {}
        for section_name in section_names:
            section = ET.fromstring(archive.read(section_name))
            for paragraph in section.findall(".//hp:p", NS):
                text = _text(paragraph)
                all_paragraphs.append((text, paragraph, paragraph.get("paraPrIDRef", "")))
                if not text.strip() or not MARKER.match(text):
                    continue
                para_id = paragraph.get("paraPrIDRef", "")
                para_pr = para_styles.get(para_id)
                if para_pr is None:
                    findings.append(ParagraphFinding(text, para_id, None, None, "fail", "paragraph style reference missing"))
                    continue
                left, indent = _paragraph_margins(para_pr)
                if left is None or indent is None:
                    findings.append(ParagraphFinding(text, para_id, left, indent, "fail", "left/indent values unavailable"))
                elif reference_pairs:
                    from .xml_hanging_indent import next_occurrence, paragraph_wraps, safe_reference_hanging_indent_pair
                    expected = safe_reference_hanging_indent_pair(
                        text, reference_pairs, wrapped=paragraph_wraps(paragraph),
                        occurrence=next_occurrence(seen_texts, text), exact_only=True,
                    )
                    if expected is not None and (left, indent) == expected:
                        findings.append(ParagraphFinding(text, para_id, left, indent, "pass", "matches reference HWPX"))
                    elif expected is not None:
                        findings.append(ParagraphFinding(
                            text, para_id, left, indent, "fail",
                            f"reference mismatch: expected left={expected[0]}, intent={expected[1]}"))
                    elif TOP_LEVEL_MARKER.match(text):
                        if (left == 0 and indent == 0) or (left >= 0 and indent < 0):
                            findings.append(ParagraphFinding(text, para_id, left, indent, "pass"))
                        else:
                            findings.append(ParagraphFinding(text, para_id, left, indent, "fail", "top-level ㅁ/□ heading must have no paragraph indent"))
                    elif indent < 0 and left >= 0:
                        findings.append(ParagraphFinding(text, para_id, left, indent, "pass"))
                    else:
                        findings.append(ParagraphFinding(text, para_id, left, indent, "fail", "reference style unavailable and safe hanging geometry missing"))
                elif TOP_LEVEL_MARKER.match(text):
                    if (left == 0 and indent == 0) or (left >= 0 and indent < 0):
                        findings.append(ParagraphFinding(text, para_id, left, indent, "pass"))
                    else:
                        findings.append(ParagraphFinding(
                            text, para_id, left, indent, "fail", "top-level ㅁ/□ heading must have no paragraph indent"))
                elif indent >= 0:
                    findings.append(ParagraphFinding(text, para_id, left, indent, "fail", "required hanging indent is missing"))
                elif left < 0:
                    findings.append(ParagraphFinding(text, para_id, left, indent, "fail", "negative indent has no compensating left margin"))
                else:
                    findings.append(ParagraphFinding(text, para_id, left, indent, "pass"))
        from .attachment_block import find_trailing_numbered_blocks, numbered_item_offset
        from .xml_hanging_indent import _char_size_pt, prefix_width_hwpunit
        for start, end in find_trailing_numbered_blocks([item[0] for item in all_paragraphs]):
            first_text, _, first_id = all_paragraphs[start]
            first_style = para_styles.get(first_id)
            first_left, first_indent = _paragraph_margins(first_style) if first_style is not None else (None, None)
            if (not first_text.startswith("붙임") or first_left is None or first_indent is None
                    or first_left != 0):   # 한/글 첫 줄은 LeftMargin에서 시작한다(2026-10-21)
                findings.append(ParagraphFinding(
                    first_text, first_id, first_left, first_indent, "fail",
                    "trailing attachment must start with 붙임 at the body margin"))
            origins: list[tuple[str, str, int]] = []
            for text, paragraph, para_id in all_paragraphs[start:end + 1]:
                style = para_styles.get(para_id)
                offset = numbered_item_offset(text)
                if style is None or offset is None:
                    continue
                left, indent = _paragraph_margins(style)
                if left is None or indent is None:
                    continue
                origin = left + prefix_width_hwpunit(   # 첫 줄 시작 = LeftMargin
                    text, offset, size_pt=_char_size_pt(header, paragraph)
                )
                origins.append((text, para_id, origin))
            if len(origins) != end - start + 1:
                findings.append(ParagraphFinding(
                    all_paragraphs[start][0], all_paragraphs[start][2], None, None,
                    "fail", "attachment number position could not be measured"))
            elif max(item[2] for item in origins) - min(item[2] for item in origins) > 100:
                findings.append(ParagraphFinding(
                    origins[0][0], origins[0][1], None, None, "fail",
                    "attachment numbers are not vertically aligned: "
                    + ", ".join(str(item[2]) for item in origins)))
    failures = [finding for finding in findings if finding.status != "pass"]
    return {
        "status": "pass" if findings and not failures else "fail",
        "marker_paragraph_count": len(findings),
        "checked_count": len(findings),
        "failed_count": len(failures),
        "findings": [asdict(finding) for finding in findings],
        "scope": ("HWPX marker paragraph left-margin/first-line-indent geometry and trailing attachment-number alignment; exact reference values compared"
                  if reference_pairs else
                  "HWPX marker paragraph left-margin/first-line-indent geometry and trailing attachment-number alignment; visual rendering not assessed"),
    }
