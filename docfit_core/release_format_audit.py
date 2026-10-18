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
        for section_name in section_names:
            section = ET.fromstring(archive.read(section_name))
            for paragraph in section.findall(".//hp:p", NS):
                text = _text(paragraph)
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
                    from .xml_hanging_indent import reference_hanging_indent_pair
                    expected = reference_hanging_indent_pair(text, reference_pairs)
                    if expected is not None and (left, indent) == expected:
                        findings.append(ParagraphFinding(text, para_id, left, indent, "pass", "matches reference HWPX"))
                    elif expected is not None:
                        findings.append(ParagraphFinding(
                            text, para_id, left, indent, "fail",
                            f"reference mismatch: expected left={expected[0]}, intent={expected[1]}"))
                    elif TOP_LEVEL_MARKER.match(text):
                        if left == 0 and indent == 0:
                            findings.append(ParagraphFinding(text, para_id, left, indent, "pass"))
                        else:
                            findings.append(ParagraphFinding(text, para_id, left, indent, "fail", "top-level ㅁ/□ heading must have no paragraph indent"))
                    elif indent < 0 and left > 0 and left + indent >= 0:
                        findings.append(ParagraphFinding(text, para_id, left, indent, "pass"))
                    else:
                        findings.append(ParagraphFinding(text, para_id, left, indent, "fail", "reference style unavailable and safe hanging geometry missing"))
                elif TOP_LEVEL_MARKER.match(text):
                    if left == 0 and indent == 0:
                        findings.append(ParagraphFinding(text, para_id, left, indent, "pass"))
                    else:
                        findings.append(ParagraphFinding(
                            text, para_id, left, indent, "fail", "top-level ㅁ/□ heading must have no paragraph indent"))
                elif indent >= 0:
                    findings.append(ParagraphFinding(text, para_id, left, indent, "fail", "required hanging indent is missing"))
                elif left <= 0 or left + indent < 0:
                    findings.append(ParagraphFinding(text, para_id, left, indent, "fail", "negative indent has no compensating left margin"))
                else:
                    findings.append(ParagraphFinding(text, para_id, left, indent, "pass"))
    failures = [finding for finding in findings if finding.status != "pass"]
    return {
        "status": "pass" if findings and not failures else "fail",
        "marker_paragraph_count": len(findings),
        "checked_count": len(findings),
        "failed_count": len(failures),
        "findings": [asdict(finding) for finding in findings],
        "scope": ("HWPX marker paragraph left-margin/first-line-indent geometry; exact reference values compared"
                  if reference_pairs else
                  "HWPX marker paragraph left-margin/first-line-indent geometry; visual rendering not assessed"),
    }
