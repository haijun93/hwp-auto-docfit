"""문서 전체 자간 초기화를 HWPX XML에서 한다(알파 1-a, 2026-10-11 설계 `docs/알파_신기능설계_2026-10-11.md`).

한/글 방식(문단마다 본문 범위를 선택해 자간 0)과 같은 결과를 XML로 낸다.
- 대상: 본문과 표·글상자 안의 모든 문단. 문단마다 보호 구간(항목기호·라벨 등, protect_of(글)이 돌려주는 글자 수)
  뒤의 글자만 자간을 0으로 한다. 보호 구간 글자는 그대로 둔다.
- 방법: 자간이 0이 아닌 run에, 같은 글자 모양에서 자간만 0으로 바꾼 새 글자 모양을 만들어 붙인다.
  보호 구간에 걸친 run은 글만 든 run(hp:t 하나, 안에 자식 요소 없음)이면 둘로 나누고, 그렇지 않으면 건드리지 않는다.
- 바꾼 문단의 낡은 줄 배치(linesegarray)는 지워 한/글이 다시 배치하게 한다.
"""

from __future__ import annotations

import copy


def _tag(e) -> str:
    return e.tag.rsplit("}", 1)[-1]


def run_text(run) -> str:
    """run의 글(hp:t 글과 그 안 자식 요소 뒤 글). 자식 요소(고정폭 빈칸·탭 등)는 글자로 세지 않는다."""
    out = []
    for t in run:
        if _tag(t) != "t":
            continue
        out.append(t.text or "")
        for c in t:
            out.append(c.tail or "")
    return "".join(out)


def _plain_run(run) -> bool:
    """hp:t 하나만 있고 그 안에 자식 요소가 없는 run(글자 위치로 안전하게 나눌 수 있음)."""
    kids = list(run)
    return len(kids) == 1 and _tag(kids[0]) == "t" and len(kids[0]) == 0


class _Chars:
    def __init__(self, header):
        self.group = next((x for x in header.iter() if _tag(x) == "charProperties"), None)
        self.chars = {x.get("id"): x for x in header.iter() if _tag(x) == "charPr"}
        self.made = {}

    def spacing_nonzero(self, char_id) -> bool:
        c = self.chars.get(char_id)
        if c is None:
            return False
        sp = next((x for x in c if _tag(x) == "spacing"), None)
        return sp is not None and any(v not in ("0", "", None) for v in sp.attrib.values())

    def zero(self, char_id):
        if char_id in self.made:
            return self.made[char_id]
        source = self.chars.get(char_id)
        if source is None or self.group is None:
            return char_id
        clone = copy.deepcopy(source)
        new_id = str(1 + max((int(x.get("id")) for x in self.group if (x.get("id") or "").isdigit()), default=-1))
        clone.set("id", new_id)
        for child in clone:
            if _tag(child) == "spacing":
                for lang in list(child.attrib):
                    child.set(lang, "0")
        self.group.append(clone)
        self.group.set("itemCnt", str(len(self.group)))
        self.chars[new_id] = clone
        self.made[char_id] = new_id
        return new_id


def reset_spacing(header_root, sections, protect_of) -> dict:
    """모든 구역의 문단(표·글상자 안 포함) 본문 자간을 0으로. protect_of(문단 글) → 보호할 앞 글자 수(없으면 0).

    통계 {"paragraphs": 바꾼 문단 수, "runs": 바꾼 run 수, "split": 나눈 run 수, "skipped": 걸쳐서 건너뛴 run 수}."""
    chars = _Chars(header_root)
    stats = {"paragraphs": 0, "runs": 0, "split": 0, "skipped": 0}
    for root in sections:
        for p in [x for x in root.iter() if _tag(x) == "p"]:
            runs = [r for r in p if _tag(r) == "run"]
            if not any(chars.spacing_nonzero(r.get("charPrIDRef")) for r in runs):
                continue
            texts = [run_text(r) for r in runs]
            protect = max(0, int(protect_of("".join(texts)) or 0))
            pos, changed = 0, 0
            for run, text in zip(runs, texts):
                start, end = pos, pos + len(text)
                pos = end
                cid = run.get("charPrIDRef")
                if not chars.spacing_nonzero(cid):
                    continue
                if start >= protect:
                    run.set("charPrIDRef", chars.zero(cid))
                    changed += 1
                elif end <= protect:
                    continue
                elif _plain_run(run):
                    cut = protect - start
                    t = run[0]
                    tail = copy.deepcopy(run)
                    tail[0].text = (t.text or "")[cut:]
                    t.text = (t.text or "")[:cut]
                    tail.set("charPrIDRef", chars.zero(cid))
                    p.insert(list(p).index(run) + 1, tail)
                    changed += 1
                    stats["split"] += 1
                else:
                    stats["skipped"] += 1
            if changed:
                for cache in [x for x in p if _tag(x) == "linesegarray"]:
                    p.remove(cache)
                stats["paragraphs"] += 1
                stats["runs"] += changed
    return stats
