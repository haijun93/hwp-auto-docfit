"""알파 보고서 서식: 단순 본문은 XML 일괄 적용, 컨트롤은 기존 COM 경로.

원본 모양을 수정하지 않고 새 모양 ID를 만들어 참조한다. 알려지지 않은
컨트롤·텍스트 요소·중복 문장은 COM에 맡기며, 조판/내어쓰기는 추측하지 않는다.
"""

from __future__ import annotations

from collections import Counter
import copy
from dataclasses import dataclass, field
import io
from pathlib import Path
import re
import tempfile
import os
from html import escape

from defusedxml import ElementTree as ET

from .fidelity.package import PackageSnapshot, build_package
from .hwpx import validate_hwpx


class BatchUnsupported(ValueError):
    """기존 COM 서식 경로로 처리해야 하는 문서 구조."""


def tag(element):
    return element.tag.rsplit("}", 1)[-1]


def child(element, name):
    return next((x for x in element if tag(x) == name), None)


def plain_text(paragraph):
    """컴포넌트 위치를 잃지 않고 처리할 수 있는 단순 문단만 반환한다."""
    if any(tag(x) not in ("run", "linesegarray") for x in paragraph):
        return None
    parts = []
    for run in paragraph:
        if tag(run) != "run":
            continue
        if len(run) != 1 or tag(run[0]) != "t" or len(run[0]):
            return None
        parts.append(run[0].text or "")
    return "".join(parts)


def _identity_text(paragraph):
    # COM GetText가 개체의 위치만 반환하는 문단도 동일 본문 충돌 검사에 포함.
    return "".join("".join(t.itertext()) for run in paragraph if tag(run) == "run"
                   for t in run if tag(t) == "t")


@dataclass(frozen=True)
class ParagraphStyle:
    text: str
    font: str | None = None
    font_type: str | None = None
    size_pt: float | None = None
    bold: bool | None = None
    ratio: int | None = None
    line_percent: int | None = None
    prev_pt: float | None = None
    bold_spans: tuple = ()


@dataclass
class BatchResult:
    formatted_texts: set = field(default_factory=set)
    paragraph_spacing: dict = field(default_factory=dict)
    applied: int = 0
    fallback: int = 0
    char_styles: int = 0
    paragraph_styles: int = 0


def _serialize(root, original):
    """Ignorable 같은 속성 값에서만 참조하는 네임스페이스도 보존한다."""
    namespaces = {}
    for _, pair in ET.iterparse(io.BytesIO(original), events=("start-ns",)):
        prefix, uri = pair
        if prefix in namespaces and namespaces[prefix] != uri:
            raise BatchUnsupported("중첩 네임스페이스 재정의는 COM 경로로 처리해야 합니다.")
        namespaces[prefix] = uri
    registry = ET.tostring.__globals__.get("_namespace_map")
    before = dict(registry) if isinstance(registry, dict) else None
    try:
        if before is None:
            raise BatchUnsupported("원본 XML 접두사를 보존할 수 없습니다.")
        for prefix, uri in namespaces.items():
            if re.fullmatch(r"ns\d+", prefix):
                raise BatchUnsupported("자동 생성 접두사를 포함한 문서는 COM 경로로 처리합니다.")
            for key, value in list(registry.items()):
                if key == uri or value == prefix:
                    del registry[key]
            registry[uri] = prefix
        value = ET.tostring(root, encoding="unicode")
        end = value.index(">")
        opening = value[:end]
        for prefix, uri in namespaces.items():
            attr = "xmlns:" + prefix if prefix else "xmlns"
            if not re.search(r"\s" + re.escape(attr) + r"=", opening):
                opening += " " + attr + '="' + escape(uri, quote=True) + '"'
        return ('<?xml version="1.0" encoding="utf-8"?>\n' + opening + value[end:]).encode("utf-8")
    finally:
        if before is not None:
            registry.clear()
            registry.update(before)


class StylePool:
    def __init__(self, header):
        self.header = header
        self.groups = {name: next((x for x in header.iter() if tag(x) == name), None)
                       for name in ("charProperties", "paraProperties")}
        if any(x is None for x in self.groups.values()):
            raise BatchUnsupported("글자/문단 모양 목록이 없습니다.")
        self.fonts = {x.get("lang", "").lower(): x for x in header.iter() if tag(x) == "fontface"}
        self.characters, self.paragraphs = {}, {}
        self.sources = {name: {x.get("id"): x for x in group}
                        for name, group in self.groups.items()}

    def check(self, paragraph, spec):
        base = self.sources["paraProperties"].get(paragraph.get("paraPrIDRef"))
        if base is None:
            return False
        if spec.line_percent is not None and not any(tag(x) == "lineSpacing" for x in base.iter()):
            return False
        if spec.prev_pt is not None and not any(tag(x) == "prev" for x in base.iter()):
            return False
        for run in paragraph:
            if tag(run) != "run":
                continue
            shape = self.sources["charProperties"].get(run.get("charPrIDRef"))
            if shape is None:
                return False
            if spec.ratio is not None and child(shape, "ratio") is None:
                return False
            if spec.font:
                ref = child(shape, "fontRef")
                if ref is None or not ref.attrib:
                    return False
                if any(lang not in self.fonts or not len(self.fonts[lang]) for lang in ref.attrib):
                    return False
        return True

    def _append(self, name, shape):
        group = self.groups[name]
        shape.set("id", str(1 + max((int(x.get("id")) for x in group), default=-1)))
        group.append(shape)
        group.set("itemCnt", str(len(group)))
        return shape.get("id")

    def _font(self, lang, face, font_type):
        group = self.fonts[lang]
        found = next((x for x in group if x.get("face") == face
                      and (font_type is None or x.get("type", "TTF") == font_type)), None)
        if found is None:
            found = copy.deepcopy(group[0])
            found.set("id", str(1 + max(int(x.get("id")) for x in group)))
            found.set("face", face)
            found.set("type", font_type or "TTF")
            found.set("isEmbedded", "0")
            # 원본 글꼴의 파일 경로나 대체 글꼴을 새 글꼴에 복사하지 않는다.
            for element in list(found):
                if tag(element) != "typeInfo":
                    found.remove(element)
            group.append(found)
            group.set("fontCnt", str(len(group)))
        return found.get("id")

    def char(self, base_id, spec, force_bold):
        key = (base_id, spec.font, spec.font_type, spec.size_pt, spec.bold, spec.ratio, force_bold)
        if key not in self.characters:
            source = self.sources["charProperties"][base_id]
            shape = copy.deepcopy(source)
            if spec.size_pt is not None:
                shape.set("height", str(round(spec.size_pt * 100)))
            if spec.font:
                ref = child(shape, "fontRef")
                for lang in ref.attrib:
                    ref.set(lang, self._font(lang, spec.font, spec.font_type))
            if spec.ratio is not None:
                ratio = child(shape, "ratio")
                for lang in ratio.attrib:
                    ratio.set(lang, str(spec.ratio))
            bold = child(shape, "bold")
            if force_bold or spec.bold is True:
                if bold is None:
                    ns = shape.tag.rsplit("}", 1)[0] + "}"
                    element = type(shape)(ns + "bold", {})
                    index = next((i for i, x in enumerate(shape) if tag(x) in (
                        "underline", "strikeout", "outline", "shadow", "emboss", "engrave", "supscript", "subscript")), len(shape))
                    shape.insert(index, element)
            elif spec.bold is False and bold is not None:
                shape.remove(bold)
            # 같은 기존 모양은 참조만 바꿔 불필요한 ID 증가를 막는다.
            comparable = copy.deepcopy(shape)
            comparable.set("id", base_id)
            self.characters[key] = base_id if ET.tostring(comparable) == ET.tostring(source) else self._append("charProperties", shape)
        return self.characters[key]

    def para(self, base_id, spec):
        key = (base_id, spec.line_percent, spec.prev_pt)
        if key not in self.paragraphs:
            source = self.sources["paraProperties"][base_id]
            shape = copy.deepcopy(source)
            def walk(element, multiplier=1):
                name = tag(element)
                if name == "default":
                    multiplier = 2
                if name == "lineSpacing" and spec.line_percent is not None:
                    element.set("type", "PERCENT")
                    element.set("value", str(spec.line_percent))
                if name == "prev" and spec.prev_pt is not None:
                    element.set("value", str(round(spec.prev_pt * 100) * multiplier))
                    element.set("unit", "HWPUNIT")
                for sub in element:
                    walk(sub, multiplier)
            walk(shape)
            self.paragraphs[key] = base_id if ET.tostring(shape) == ET.tostring(source) else self._append("paraProperties", shape)
        return self.paragraphs[key]


def _rewrite_runs(paragraph, spec, pool):
    runs = [x for x in paragraph if tag(x) == "run"]
    original = "".join(x[0].text or "" for x in runs)
    # 문두 공백과 기호만 바꾼다. 본문의 run 경계·강조·색은 보존한다.
    old_prefix = len(original) - len(original.lstrip())
    new_prefix = len(spec.text) - len(spec.text.lstrip())
    if len(original.lstrip()) != len(spec.text.lstrip()):
        raise ValueError("본문 글자 수를 바꾸는 계획은 적용할 수 없습니다.")
    position = 0
    built = []
    leading_added = False
    for run in runs:
        raw = run[0].text or ""
        start = max(0, old_prefix - position)
        text = raw[start:]
        source_start = position + start
        position += len(raw)
        if not text and raw:
            continue
        if not leading_added:
            text = spec.text[:new_prefix] + text
            global_start = 0
            leading_added = True
        else:
            global_start = source_start - old_prefix + new_prefix
        if global_start <= new_prefix < global_start + len(text):
            local = new_prefix - global_start
            text = text[:local] + spec.text[new_prefix] + text[local + 1:]
        cuts = {0, len(text)}
        for a, b in spec.bold_spans:
            cuts.update(max(0, min(len(text), x - global_start)) for x in (a, b))
        ordered = sorted(cuts)
        for a, b in zip(ordered, ordered[1:]):
            if a == b:
                continue
            clone = copy.deepcopy(run)
            clone[0].text = text[a:b]
            force = any(lo <= global_start + a and global_start + b <= hi for lo, hi in spec.bold_spans)
            clone.set("charPrIDRef", pool.char(run.get("charPrIDRef"), spec, force))
            built.append(clone)
    for run in runs:
        paragraph.remove(run)
    for index, run in enumerate(built):
        paragraph.insert(index, run)
    for element in list(paragraph):
        if tag(element) == "linesegarray":
            paragraph.remove(element)  # 오래된 실측값을 지워 한/글이 다시 조판하게 한다.
    if plain_text(paragraph) != spec.text:
        raise ValueError("문두 외의 글자가 바뀌었습니다. 결과를 저장하지 않습니다.")


def apply_batch(source, target, planner):
    """planner(text, paragraph) -> ParagraphStyle|None. 미지원 문단은 그대로 둔다.

    planner는 본문 문단을 순서대로 받는다(None은 복잡한 문단). 복잡한 문단도
    문맥 추적에 포함하지만 XML 적용은 단순하고 유일한 문단에 한정한다.
    """
    if target is not None and Path(source).resolve() == Path(target).resolve():
        raise ValueError("원본과 다른 출력 경로가 필요합니다.")
    metadata = validate_hwpx(source)
    snapshot = PackageSnapshot.load(source)
    header_bytes = snapshot.read("Contents/header.xml")
    header = ET.fromstring(header_bytes)
    pool = StylePool(header)
    sections = {name: ET.fromstring(snapshot.read(name)) for name in metadata["section_names"]}
    paragraphs = [(name, p, plain_text(p)) for name, root in sections.items() for p in root if tag(p) == "p"]
    # 표·머리말·각주와 같은 문장이 있어도 COM이 혼동하지 않도록 전역을 센다.
    counts = Counter(_identity_text(p) for root in sections.values() for p in root.iter() if tag(p) == "p")
    result = BatchResult()
    changed = set()
    for name, paragraph, text in paragraphs:
        spec = planner(text, paragraph)
        if (text is None or not text.strip() or spec is None or counts[text] != 1
                or not pool.check(paragraph, spec)):
            result.fallback += 1
            continue
        _rewrite_runs(paragraph, spec, pool)
        paragraph.set("paraPrIDRef", pool.para(paragraph.get("paraPrIDRef"), spec))
        result.formatted_texts.add(spec.text)
        if spec.prev_pt is not None:
            result.paragraph_spacing[spec.text] = spec.prev_pt
        result.applied += 1
        changed.add(name)
    # 변환 뒤 중복된 문장은 COM으로 재처리한다. 본문 번호는 추측하지 않는다.
    final_counts = Counter(_identity_text(p) for root in sections.values() for p in root.iter() if tag(p) == "p")
    result.formatted_texts = {t for t in result.formatted_texts if final_counts[t] == 1}
    result.paragraph_spacing = {t: v for t, v in result.paragraph_spacing.items() if t in result.formatted_texts}
    result.char_styles = len(pool.groups["charProperties"]) - len(pool.sources["charProperties"])
    result.paragraph_styles = len(pool.groups["paraProperties"]) - len(pool.sources["paraProperties"])
    replacements = {name: _serialize(sections[name], snapshot.read(name)) for name in changed}
    if changed:
        replacements["Contents/header.xml"] = _serialize(header, header_bytes)
    if target is None:
        return result
    content = build_package(snapshot, replacements)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".batch-", suffix=".hwpx", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        validate_hwpx(temporary)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return result
