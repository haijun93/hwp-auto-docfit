"""Offline, approval-based public-language and Korean spelling review for HWPX."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import tempfile
from zipfile import ZipFile

from defusedxml import ElementTree as ET

from .hwpx import validate_hwpx


@dataclass(frozen=True)
class CorrectionRule:
    id: str
    category: str
    source: str
    suggestion: str
    reason: str
    reference: str


PUBLIC_REFERENCE = "https://www.korean.go.kr/common/download.do?c_file_name=d2a561f4-ad8b-4400-826d-4e4e886e2c3d.pdf&file_path=etcData"
SPELLING_REFERENCE = "https://www.korean.go.kr/front/onlineQna/onlineQnaView.do?mn_id=90&pageIndex=1&qna_seq=328160"

# These short, independently curated suggestions are not a complete spelling
# dictionary. Public-language alternatives are review suggestions, not errors.
RULES = (
    CorrectionRule("public.geumbeon", "공공언어", "금번", "이번", "쉬운 표현 제안", PUBLIC_REFERENCE),
    CorrectionRule("public.geumil", "공공언어", "금일", "오늘", "쉬운 표현 제안(잘못된 말은 아님)", PUBLIC_REFERENCE),
    CorrectionRule("public.myeongil", "공공언어", "명일", "내일", "쉬운 표현 제안", PUBLIC_REFERENCE),
    CorrectionRule("public.jagil", "공공언어", "작일", "어제", "쉬운 표현 제안", PUBLIC_REFERENCE),
    CorrectionRule("public.igil", "공공언어", "익일", "다음 날", "기준일을 확인한 뒤 선택", PUBLIC_REFERENCE),
    CorrectionRule("public.ilhwaneuro", "공공언어", "일환으로", "하나로", "문맥에 따라 검토", PUBLIC_REFERENCE),
    CorrectionRule("public.dong_system", "공공언어", "동 시스템", "이 시스템", "가리키는 대상을 확인", PUBLIC_REFERENCE),
    CorrectionRule("public.gosubuji", "공공언어", "고수부지", "둔치", "쉬운 표현 제안", PUBLIC_REFERENCE),
    CorrectionRule("public.bulcheoljuya", "공공언어", "불철주야", "밤낮없이", "쉬운 표현 제안", PUBLIC_REFERENCE),
    CorrectionRule("public.nohu_siseol", "공공언어", "노후 시설", "낡은 시설", "문맥에 따라 검토", PUBLIC_REFERENCE),
    CorrectionRule("spelling.myeochil", "맞춤법", "몇일", "며칠", "한글 맞춤법 표기", SPELLING_REFERENCE),
    CorrectionRule("spelling.myeot_il", "맞춤법", "몇 일", "며칠", "날짜·기간 표현일 때만 선택", SPELLING_REFERENCE),
    CorrectionRule("spelling.gaetsu", "맞춤법", "갯수", "개수", "표준 표기 확인", "https://stdict.korean.go.kr/"),
    CorrectionRule("spelling.doetda", "맞춤법", "됬다", "됐다", "되었다의 준말", "https://stdict.korean.go.kr/"),
    CorrectionRule("spelling.doetseumnida", "맞춤법", "됬습니다", "됐습니다", "되었습니다의 준말", "https://stdict.korean.go.kr/"),
    CorrectionRule("spelling.wenmanhamyeon", "맞춤법", "왠만하면", "웬만하면", "표준 표기 확인", "https://stdict.korean.go.kr/"),
    CorrectionRule("spelling.eoieopda", "맞춤법", "어의없다", "어이없다", "표준 표기 확인", "https://stdict.korean.go.kr/"),
    CorrectionRule("spelling.dwaeyo", "맞춤법", "되요", "돼요", "되어요의 준말", "https://stdict.korean.go.kr/"),
)
RULE_BY_ID = {rule.id: rule for rule in RULES}
_PARTICLE = r"(?:으로|부터|까지|동안|이나|은|는|이|가|을|를|에|의|도|만|로|과|와|간)"
_BOUNDARY = r"(?=(?:" + _PARTICLE + r")?(?![가-힣A-Za-z0-9]))"
_PATTERNS = {rule.id: re.compile(r"(?<![가-힣A-Za-z0-9])" + re.escape(rule.source) +
                                     _BOUNDARY) for rule in RULES}
_SECTION = re.compile(r"Contents/section\d+\.xml$")


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _paragraph_nodes(root):
    for paragraph in root.iter():
        if _local(paragraph.tag) != "p":
            continue
        # Nested table-cell paragraphs must not be counted through their
        # enclosing table run and then counted again as their own paragraph.
        nodes = [node for run in paragraph if _local(run.tag) == "run"
                 for node in run if _local(node.tag) == "t"]
        if nodes:
            yield nodes


def _matches(text, excluded, allowed=None):
    found = []
    for rule in RULES:
        if rule.source in excluded or (allowed is not None and rule.id not in allowed):
            continue
        for match in _PATTERNS[rule.id].finditer(text):
            found.append((match.start(), match.end(), rule))
    # Longer, more specific expressions win on overlap.
    found.sort(key=lambda value: (value[0], -(value[1] - value[0])))
    result = []
    last_end = -1
    for item in found:
        if item[0] >= last_end:
            result.append(item)
            last_end = item[1]
    return result


def scan_hwpx(path, excluded=()):
    """Return grouped candidates with counts and a short in-document context."""
    validation = validate_hwpx(path)
    found = {}
    with ZipFile(path) as archive:
        for section in validation["section_names"]:
            root = ET.fromstring(archive.read(section))
            for nodes in _paragraph_nodes(root):
                text = "".join(node.text or "" for node in nodes)
                for start, end, rule in _matches(text, set(excluded)):
                    item = found.setdefault(rule.id, {"rule_id": rule.id,
                                                       "category": rule.category,
                                                       "source": rule.source,
                                                       "suggestion": rule.suggestion,
                                                       "reason": rule.reason,
                                                       "count": 0, "examples": []})
                    item["count"] += 1
                    if len(item["examples"]) < 3:
                        item["examples"].append(text[max(0, start - 24):min(len(text), end + 24)].strip())
    return list(found.values())


def _replace_span(nodes, start, end, replacement):
    positions = []
    offset = 0
    for node in nodes:
        value = node.text or ""
        positions.append((offset, offset + len(value), node, value))
        offset += len(value)
    touched = [(a, b, node, value) for a, b, node, value in positions if b > start and a < end]
    if not touched:
        return
    first_a, _, first_node, first_text = touched[0]
    last_a, _, last_node, last_text = touched[-1]
    prefix = first_text[:start - first_a]
    suffix = last_text[end - last_a:]
    if first_node is last_node:
        first_node.text = prefix + replacement + suffix
    else:
        first_node.text = prefix + replacement
        for _, _, node, _ in touched[1:-1]:
            node.text = ""
        last_node.text = suffix


def apply_approved_hwpx(source, destination, approved_rule_ids, excluded=()):
    """Write a new HWPX; never modify the source or an existing destination."""
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve() or destination.exists():
        raise FileExistsError("교정 결과 파일이 이미 있습니다. 다른 이름을 선택해 주세요.")
    validation = validate_hwpx(source)
    allowed = set(approved_rule_ids) & RULE_BY_ID.keys()
    if not allowed:
        raise ValueError("승인한 교정 항목이 없습니다.")
    changes = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix="docfit_proofread_", suffix=".hwpx",
                                         dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
        with ZipFile(source) as original, ZipFile(temporary, "w") as output:
            sections = set(validation["section_names"])
            for info in original.infolist():
                data = original.read(info.filename)
                if info.filename in sections:
                    root = ET.fromstring(data)
                    section_changed = False
                    for nodes in _paragraph_nodes(root):
                        text = "".join(node.text or "" for node in nodes)
                        matches = _matches(text, set(excluded), allowed)
                        for start, end, rule in reversed(matches):
                            _replace_span(nodes, start, end, rule.suggestion)
                            changes += 1
                            section_changed = True
                    if section_changed:
                        data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                output.writestr(info, data)
        validate_hwpx(temporary)
        # os.link prevents a race from silently overwriting another result.
        os.link(temporary, destination)
        return changes
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def load_exclusions(path):
    source = Path(path)
    if not source.exists():
        return set()
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise ValueError("교정 제외 목록 형식이 올바르지 않습니다.")
    return set(data)


def save_exclusions(path, expressions):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(sorted(set(expressions)), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, target)
