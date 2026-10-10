"""연속된 '항목기호 + 짧은 라벨 + 콜론' 문장의 콜론을 세로로 맞춘다(알파, 2026-10-10 사용자 규칙).

예) - 공사명: 현수식 안내판 철거
    - 공사기간: 2026. 10. 11. ~ 2026. 10. 20.
    - 계약방식: 수의계약
라벨(항목기호와 콜론 사이 글, 7자 미만)이 2줄 이상 이어질 때이 가장 긴 줄('공사기간')을 기준으로, 짧은 라벨('공사명')의 글자 자간을
늘리고 모자라면 장평도 늘려 가로 길이를 맞춘다. 그러면 콜론 위치가 세로로 일치한다. 콜론 글자는 늘리지 않는다.
"""

from __future__ import annotations

import copy
import re

from .connector_tabs import char_em

LABEL = re.compile(r"^(\s*(?:[-‐–□■ㅇ○◦●•·∙※*▪▶◆◇☞]|\d{1,2}[.)]|[가-하][.)]|\(\d{1,2}\)|[①-⑳])\s*)([^:：\s][^:：]{0,7}?)\s*([:：])")
MAX_LABEL = 7          # 항목기호와 콜론 사이 글자 수 상한(미만만 대상, 사용자 규칙 2026-10-10)
MAX_SPACING = 50       # 한/글 자간 최대(%)
LONG_LABEL = re.compile(r"^\s*(?:[-‐–□■ㅇ○◦●•·∙※*▪▶◆◇☞]|\d{1,2}[.)]|[가-하][.)]|\(\d{1,2}\)|[①-⑳])\s*[^:：\s][^:：]{6,19}[:：]")
MAX_RATIO = 200        # 한/글 장평 최대(%)


def _tag(e) -> str:
    return e.tag.rsplit("}", 1)[-1]


def label_of(text: str):
    """(라벨 시작, 라벨 끝, 콜론 위치) 또는 None. 라벨은 공백 제외 7자 미만이다(순수 함수)."""
    m = LABEL.match(text or "")
    if not m:
        return None
    label = m.group(2)
    if len(label.replace(" ", "")) >= MAX_LABEL or not label.strip():
        return None
    return m.start(2), m.start(2) + len(label.rstrip()), m.start(3)


SPACE_EM = 0.5        # 빈칸 폭 추정(글자 크기 대비)


def plan(label: str, target_em: float):
    """라벨을 target_em 폭으로 맞추는 계획 (글자 사이 빈칸 수, 자간 %, 장평 %)(순수 함수).

    사용자 규칙(2026-10-10): 조정 대상과 기준 라벨의 글자 수 홀짝이 다르고 자간만으로 맞출 수 있으면(예: 3자 → 4자)
    자간만 늘린다. 그 밖(예: 2자 → 4자 '장   소', 3자 → 6자 '행 사 명')은 글자 사이에 빈칸을 넣고, 남는 폭은 자간으로
    미세 조정한다. 자간은 마지막 글자를 뺀 글자에만 준다(마지막 글자는 콜론에 붙임)."""
    base = sum(char_em(c) for c in label)
    if not label or base >= target_em - 1e-6:
        return 0, 0, 100
    n, gaps = len(label), len(label) - 1
    target_n = round(target_em)          # 기준 라벨 글자 수(한글 1글자 = 1em)
    extra = target_em - base
    spaces = 0
    if gaps > 0 and not ((n % 2 != target_n % 2) and extra <= MAX_SPACING / 100 * sum(char_em(c) for c in label[:-1])):
        spaces = max(1, int(extra / (gaps * SPACE_EM)))
        while spaces > 1 and spaces * gaps * SPACE_EM > extra - 1e-6:
            spaces -= 1
    spaced = base + spaces * gaps * SPACE_EM
    spacing, ratio = stretch(label, target_em, spaced_base=spaced)
    return spaces, spacing, ratio


def stretch(label: str, target_em: float, spaced_base=None):
    """라벨 글자의 폭 합을 target_em으로 늘리는 (자간 %, 장평 %). 이미 같거나 넓으면 (0, 100)(순수 함수).

    한/글 실측(2026-10-10): 자간은 장평을 적용한 글자 폭 기준이다. 자간은 마지막 글자를 뺀 글자에만 준다.
    자간을 한도(50%)까지 먼저 쓰고, 모자라면 장평으로 채운다. spaced_base는 글자 사이 빈칸을 넣은 뒤의 폭."""
    base = sum(char_em(c) for c in label)
    inner = sum(char_em(c) for c in label[:-1])
    current = spaced_base if spaced_base is not None else base
    if not label or current >= target_em - 1e-6:
        return 0, 100
    gap = target_em - current
    if inner > 0 and gap <= MAX_SPACING / 100 * inner:
        return round(gap / inner * 100), 100
    spacing = MAX_SPACING if inner > 0 else 0
    fixed = current - base                       # 넣은 빈칸 폭(장평 영향 없음으로 본다)
    return spacing, min(MAX_RATIO, round((target_em - fixed) / (base + spacing / 100 * inner) * 100))


def _single_t(p):
    ts = [t for r in p if _tag(r) == "run" for t in r if _tag(t) == "t"]
    with_text = [t for t in ts if (t.text or "") or len(t)]
    if len(with_text) != 1 or len(with_text[0]):
        return None
    return with_text[0]


def groups_in(container):
    """같은 부모 안에서 '항목기호 + 짧은 라벨 + 콜론' 문단이 2개 이상 이어진 묶음."""
    out, run = [], []
    for p in list(container):
        if _tag(p) != "p":
            continue
        t = _single_t(p)
        found = label_of(t.text) if t is not None else None
        if found and not any(_tag(x) == "tbl" for x in p.iter()):
            run.append((p, t, found))
        elif run and t is not None and LONG_LABEL.match(t.text or ""):
            continue            # 7자 이상 예외 줄: 이 줄만 빼고 묶음은 이어 간다(사용자 규칙, 2026-10-10)
        else:
            if len(run) >= 2:
                out.append(run)
            run = []
    if len(run) >= 2:
        out.append(run)
    return out


class _Chars:
    def __init__(self, header):
        self.group = next((x for x in header.iter() if _tag(x) == "charProperties"), None)
        self.chars = {x.get("id"): x for x in header.iter() if _tag(x) == "charPr"}
        self.made = {}

    def stretched(self, char_id, spacing, ratio):
        key = (char_id, spacing, ratio)
        if key in self.made:
            return self.made[key]
        source = self.chars.get(char_id)
        if source is None or self.group is None:
            return char_id
        clone = copy.deepcopy(source)
        new_id = str(1 + max((int(x.get("id")) for x in self.group if (x.get("id") or "").isdigit()), default=-1))
        clone.set("id", new_id)
        for child in clone:
            if _tag(child) == "spacing":
                for lang in list(child.attrib):
                    child.set(lang, str(max(-50, min(MAX_SPACING, int(child.get(lang, "0")) + spacing))))
            elif _tag(child) == "ratio":
                for lang in list(child.attrib):
                    child.set(lang, str(max(50, min(MAX_RATIO, round(int(child.get(lang, "100")) * ratio / 100)))))
        self.group.append(clone)
        self.group.set("itemCnt", str(len(self.group)))
        self.chars[new_id] = clone
        self.made[key] = new_id
        return new_id


def align_colons(header_root, sections) -> dict:
    """모든 구역·칸의 콜론 라벨 묶음을 맞춘다. 통계를 돌려준다."""
    chars = _Chars(header_root)
    stats = {"groups": 0, "stretched": 0}
    containers = []
    for root in sections:
        containers.append(root)
        containers += [x for x in root.iter() if _tag(x) == "subList"]
    for container in containers:
        for group in groups_in(container):
            target = max(sum(char_em(c) for c in t.text[s:e]) for _, t, (s, e, _) in group)
            done = False
            for p, t, (s, e, colon) in group:
                label = t.text[s:e]
                spaces, spacing, ratio = plan(label, target)
                if (spaces, spacing, ratio) == (0, 0, 100):
                    continue
                run = next(r for r in p if _tag(r) == "run" and t in list(r))
                if any(_tag(x) != "t" for x in run):
                    continue            # 구역 정의·컨트롤이 든 run은 나누지 않는다
                base = run.get("charPrIDRef")
                text = t.text
                parent = p
                index = list(parent).index(run)
                사이 = " " * spaces
                늘린 = chars.stretched(base, spacing, ratio)
                끝글자 = chars.stretched(base, 0, ratio)
                # 글자 사이에 빈칸(필요하면), 자간은 마지막 글자를 뺀 라벨 글자에, 장평은 라벨 전체에.
                pieces = [(text[:s], base)]
                for i, ch in enumerate(label):
                    if i < len(label) - 1:
                        pieces.append((ch, 늘린))
                        if 사이:
                            pieces.append((사이, base))
                    else:
                        pieces.append((ch, 끝글자))
                pieces.append((text[e:], base))
                merged = []
                for piece, cid in pieces:
                    if not piece:
                        continue
                    if merged and merged[-1][1] == cid:
                        merged[-1] = (merged[-1][0] + piece, cid)
                    else:
                        merged.append((piece, cid))
                parent.remove(run)
                for offset, (piece, cid) in enumerate(merged):
                    new = copy.deepcopy(run)
                    for child in list(new):
                        new.remove(child)
                    new_t = type(t)(t.tag, dict(t.attrib))
                    new_t.text = piece
                    new.append(new_t)
                    new.set("charPrIDRef", cid)
                    parent.insert(index + offset, new)
                for cache in [x for x in p if _tag(x) == "linesegarray"]:
                    p.remove(cache)
                stats["stretched"] += 1
                done = True
            if done:
                stats["groups"] += 1
    return stats
