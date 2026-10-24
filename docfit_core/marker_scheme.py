"""문서 안의 변형 항목기호를 표준 서식 키에 연결한다. 원문은 바꾸지 않는다."""

from collections import defaultdict
from dataclasses import dataclass, field
import re
import unicodedata

from .attachment_block import find_blocks


_LEVELS = ("□", "ㅇ", "-")
_OFFICIAL_LEVEL = {"□": "□", "ㅁ": "□", "ㅇ": "ㅇ", "○": "ㅇ", "-": "-"}
_NOTES = frozenset(("*", "**", "※"))
_LEGACY_SYMBOLS = frozenset("◦☞•·∙‧⋅ㆍ")
_HANGUL = "가나다라마바사아자차카타파하"
_LABEL = re.compile(r"^\s*(?:제목|개요|요약|부제|중제목)\s*[:：]")
_MULTI = re.compile(r"([0-9]+(?:[.．][0-9]+)+)[.．]?(?=\s|$)")
_HYPHEN = re.compile(r"([0-9]+(?:-[0-9]+)+)[.．]?(?=\s|$)")
_NUMBER = re.compile(r"(?:[0-9]+[.．)]|\([0-9]+\))(?=\s|$)")
_KOREAN = re.compile(r"(?:[가나다라마바사아자차카타파하][.．)]|\([가나다라마바사아자차카타파하]\))(?=\s|$)")
_ROMAN = re.compile(r"(?:[Ⅰ-Ⅿ]+[.．]?|(?:[IVX]|[IVXLCDM]{2,})[.．])(?=\s|$)")
_LETTER = re.compile(r"(?:[A-Za-z][.．)]|\([A-Za-z]\))(?=\s|$)")
_OFFICIAL_ORDER = {name: i for i, name in enumerate(("1.", "가.", "1)", "가)", "(1)", "(가)", "①", "㉮"))}


def classify_marker(text) -> tuple[str, int] | None:
    """문두 모양 계열과 원문 기호 끝. 번호 값·전각 마침표는 계열에 영향을 주지 않는다.

    분류는 어휘 판정이며 실제 목록인지(연속 번호·문맥)는 detect_scheme에서 판단한다.
    토큰 끝은 앞 공백을 포함하고 뒤 공백은 포함하지 않는다.
    """
    stripped = (text or "").lstrip()
    if not stripped:
        return None
    if re.match(r"[0-9]{4}[.．][0-9]{1,2}[.．][0-9]{1,2}[.．]?(?=\s|$)", stripped):
        return None  # 문두 날짜를 다단 개요 번호로 학습하지 않는다.
    lead = len(text) - len(stripped)
    for pattern, separator in ((_MULTI, "."), (_HYPHEN, "-")):
        match = pattern.match(stripped)
        if match:
            depth = len(re.split(r"[.．-]", match.group(1)))
            return separator.join(["1"] * depth) + ".", lead + match.end()
    for pattern, representative in ((_NUMBER, "1"), (_KOREAN, "가"), (_ROMAN, "Ⅰ"), (_LETTER, "")):
        match = pattern.match(stripped)
        if match:
            token = match.group().replace("．", ".")
            if pattern is _ROMAN:
                family = ("I" if token[0].isascii() else "Ⅰ") + ("." if token.endswith(".") else "")
            else:
                representative = representative or ("A" if token.lstrip("(")[0].isupper() else "a")
                family = re.sub(r"[0-9]+|[가나다라마바사아자차카타파하]|[A-Za-z]", representative, token)
            return family, lead + match.end()
    first = stripped[0]
    if first in "❶❷❸❹❺❻❼❽❾❿" and (len(stripped) == 1 or stripped[1].isspace()):
        return "-", lead + 1
    if first in "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉠㉡㉢㉣㉤㉥㉦㉧㉨㉩㉪㉫㉬㉭㉮㉯㉰㉱㉲㉳㉴㉵㉶㉷㉸㉹㉺㉻":
        if len(stripped) == 1 or stripped[1].isspace():
            family = "①" if "①" <= first <= "⑳" else "㉠" if "㉠" <= first <= "㉭" else "㉮"
            return family, lead + 1
    if stripped.startswith("**") and (len(stripped) == 2 or stripped[2].isspace()):
        return "**", lead + 2
    if (len(stripped) == 1 or stripped[1].isspace()) and (
            first in _OFFICIAL_LEVEL or first in _NOTES or first in _LEGACY_SYMBOLS
            or unicodedata.category(first) in {"So", "Sm", "Po"}):
        return first, lead + 1
    return None


def _ordinal(family, token):
    """연속 번호 확인용 값. 도형은 None, 다단 번호는 경로 튜플."""
    token = token.strip().replace("．", ".")
    if family.startswith("1") or family == "(1)":
        return tuple(map(int, re.findall(r"[0-9]+", token)))
    if "가" in family:
        return (_HANGUL.index(token.strip(".()")),)
    if family in {"①", "㉠", "㉮"}:
        return (ord(token) - ord(family),)
    if family.startswith(("Ⅰ", "I")):
        roman = unicodedata.normalize("NFKC", token).rstrip(".")
        values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
        return (sum(-values[c] if i + 1 < len(roman) and values[c] < values[roman[i + 1]] else values[c]
                    for i, c in enumerate(roman)),)
    if family.strip(".()") in {"A", "a"}:
        return (ord(token.strip(".()")),)
    return None


@dataclass
class MarkerScheme:
    decimal: bool = False
    symbols: dict[str, str] = field(default_factory=dict)
    excluded: frozenset[str] = frozenset()
    paragraph_count: int = 0
    family_levels: dict[str, int] = field(default_factory=dict)

    def __bool__(self):
        return self.decimal or bool(self.symbols) or bool(self.family_levels)

    def is_excluded(self, text):
        return bool(text) and text.strip() in self.excluded

    def canonical(self, text) -> tuple[str, int] | None:
        """(표준 서식 키, 원문 기호 끝 오프셋). 붙임과 일반 문단은 None."""
        if not text or self.is_excluded(text) or _LABEL.match(text):
            return None
        found = classify_marker(text)
        if found:
            family, end = found
            level = self.family_levels.get(family)
            # 감지된 다단 체계의 더 깊은 번호도 같은 상대 깊이로 조회한다(C6 조회 API 유지).
            separator = "-" if family.startswith("1-") else "." if family.startswith("1.") else None
            if level is None and separator:
                depth = family.count(separator) + (1 if separator == "-" else 0)
                anchors = [(f.count(separator) + (1 if separator == "-" else 0), n)
                           for f, n in self.family_levels.items()
                           if f.startswith("1-" if separator == "-" else "1.")]
                if anchors:
                    anchor_depth, anchor_level = min(anchors)
                    if depth >= anchor_depth:
                        level = anchor_level + depth - anchor_depth
            if level is not None:
                return _LEVELS[min(level, 3) - 1], end
            if family in self.symbols:
                return self.symbols[family], end
        return None

    def style_text(self, text):
        """위계·간격·기준 예시 조회 전용 문자열. 저장할 글로 사용하지 않는다."""
        mapped = self.canonical(text)
        if mapped is None:
            return text
        marker, end = mapped
        start = len(text) - len(text.lstrip())
        return text[:start] + marker + text[end:]

    def log_message(self):
        table = ", ".join(f"{family}={key}" for family, key in self.summary.items())
        return f"[항목기호 체계] 계열→단계: {table} (문단 {self.paragraph_count}개)"

    @property
    def summary(self):
        return {family: _LEVELS[min(level, 3) - 1] for family, level in self.family_levels.items()}


def detect_scheme(texts) -> MarkerScheme:
    """연속 번호·여러 계열의 문맥을 확인한 뒤 최초 단계가 고정되는 문서 순서 스택을 만든다."""
    texts = list(texts)
    excluded_indices = {i for start, end in find_blocks(texts) for i in range(start, end + 1)}
    excluded = frozenset(texts[i].strip() for i in excluded_indices if texts[i])
    body = [text for i, text in enumerate(texts) if i not in excluded_indices and text and text.strip()]
    found = [(text, classify_marker(text)) for text in body if not _LABEL.match(text)]
    occupied = {_OFFICIAL_LEVEL[marker[0]] for _, marker in found if marker and marker[0] in _OFFICIAL_LEVEL}
    has_box = "□" in occupied
    candidates = []
    ordinals = defaultdict(list)
    for text, marker in found:
        if not marker:
            continue
        family, end = marker
        if family in _OFFICIAL_LEVEL or family in _NOTES:
            continue
        if family in _LEGACY_SYMBOLS and occupied:
            continue
        if has_box and family in {"가.", "Ⅰ", "Ⅰ.", "I."}:
            continue  # 공식 네모가 있으면 기존 중제목 역할 유지.
        ordinal = _ordinal(family, text[:end])
        ordinals[family].append(ordinal)
        candidates.append((text, family, end))
    sequential = {family for family, values in ordinals.items() if any(
        a is not None and b is not None and a[:-1] == b[:-1] and b[-1] == a[-1] + 1
        for a, b in zip(values, values[1:]))}
    shapes = {family for family, values in ordinals.items() if values[0] is None}
    multi = {family for family in ordinals if family.startswith(("1.1", "1-1"))}
    ranks = [_OFFICIAL_ORDER.get(family) for family in ordinals]
    official_chain = len(ranks) > 1 and all(rank is not None for rank in ranks) and all(
        a < b for a, b in zip(ranks, ranks[1:]))
    supported = len(ordinals) > 1 and bool(sequential or shapes or multi or official_chain)
    eligible = sequential | shapes | multi
    if supported:
        eligible.update(family for family, values in ordinals.items() if len(set(values)) == 1)
    levels, stack = {}, []
    available = [i + 1 for i, key in enumerate(_LEVELS) if key not in occupied] or [3]
    for text, family, end in candidates:
        if family not in eligible:
            continue
        indent = len(text[:len(text) - len(text.lstrip())].expandtabs(4))
        if family in levels:
            # 다른 문맥에서 다시 나와도 최초 단계는 변경하지 않는다.
            stack = [entry for entry in stack if levels[entry[0]] < levels[family]]
        else:
            # 명시적으로 내어쓴 새 계열은 형제/상위로 복귀한다. 같은 무들여쓰기 문단은 순서 스택을 쓴다.
            if stack and indent < stack[-1][1]:
                while stack and indent <= stack[-1][1]:
                    stack.pop()
            elif stack and indent == stack[-1][1] and indent > 0:
                # 동일 들여쓰기에서 공식 번호 순서가 되돌아오면 형제 항목으로 본다.
                rank = _OFFICIAL_ORDER.get(family)
                while stack and rank is not None and indent == stack[-1][1] and rank <= _OFFICIAL_ORDER.get(stack[-1][0], -1):
                    stack.pop()
            proposed = levels[stack[-1][0]] + 1 if stack else available[0]
            while proposed < 3 and _LEVELS[proposed - 1] in occupied:
                proposed += 1
            levels[family] = proposed
        stack.append((family, indent))
    symbols = {family: _LEVELS[min(level, 3) - 1] for family, level in levels.items()
               if len(family) == 1 and _ordinal(family, family) is None}
    scheme = MarkerScheme(any(f.startswith("1.1") for f in levels), symbols, excluded,
                          family_levels=levels)
    scheme.paragraph_count = sum(scheme.canonical(text) is not None for text in body)
    return scheme


def detect_hwpx_scheme(source) -> MarkerScheme:
    """본문 최상위 문단만 읽는다. 표·개체 안의 번호는 체계 감지에 넣지 않는다."""
    from defusedxml import ElementTree as ET
    from .batch_format import tag
    from .fidelity.package import PackageSnapshot

    snapshot = PackageSnapshot.load(source)
    texts = []
    names = sorted((name for name in snapshot.entries if re.fullmatch(r"Contents/section\d+\.xml", name)),
                   key=lambda name: int(re.search(r"section(\d+)", name).group(1)))
    for name in names:
        root = ET.fromstring(snapshot.read(name))
        for paragraph in root:
            if tag(paragraph) == "p":
                texts.append("".join("".join(t.itertext()) for run in paragraph if tag(run) == "run"
                                     for t in run if tag(t) == "t"))
    return detect_scheme(texts)
