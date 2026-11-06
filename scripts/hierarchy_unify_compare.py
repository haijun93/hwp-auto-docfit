"""HWIRE3: 서식통일 문단 수준 판정의 위계 엔진 켬/끔 비교표(실제 hierarchy 실행 파일 사용, 한/글 COM 없음).

끔 = 현재 서식통일 그룹키 규칙(style_unify.unify_marker의 역할, 원문자 ①류는 '원문자'로 남음).
켬 = 같은 규칙 + 엔진 보조(역할이 '원문자'·'미분류'인 문단만 엔진 판정으로 교체).
사용: python scripts/hierarchy_unify_compare.py [hierarchy 실행 파일]
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from docfit_app import hierarchy_bridge as hb  # noqa: E402
from docfit_core.style_unify import unify_marker  # noqa: E402

FIXTURES = ["ai_answer_chatgpt.txt", "ai_answer_claude.txt", "ai_answer_gemini.txt", "ai_answer_mapo_pots.txt",
            "beomgov_markdown.txt", "c23_continuation.txt", "gemini_bench_reply.txt"]
GOLDEN_ROLE = {"square": "소제목", "circle": "본문", "dash": "내용", "asterisk": "부연설명"}
ON = {"hierarchy_engine": True}


def off_role(text):
    marker, role, _ = unify_marker(text)
    return (role or "미분류") if marker else None


def on_roles(texts, exe):
    items = [(i, t) for i, t in enumerate(texts)]
    engine = hb.engine_roles(items, ON, executable=exe)
    return [(engine.get(i) or off_role(t)) if off_role(t) in ("원문자", "미분류") else off_role(t)
            for i, t in items]


def main():
    exe = Path(sys.argv[1]) if len(sys.argv) > 1 else hb.find_executable()
    if exe is None:
        sys.exit("hierarchy 실행 파일이 없습니다(cargo build --release).")
    print(f"엔진: {exe}\n")
    print("| 샘플 | 문단 | 항목기호 문단 | 끔: 원문자 | 켬: 판정 바뀜 | 켬: 원문자 잔존 | 켬 역할 분포(바뀐 것) |")
    print("|---|---|---|---|---|---|---|")
    tot = Counter()
    for name in FIXTURES:
        texts = [t for t in (Path(ROOT, "tests/fixtures", name).read_text(encoding="utf-8").splitlines()) if t.strip()]
        off = [off_role(t) for t in texts]
        on = on_roles(texts, exe)
        marked = sum(1 for r in off if r)
        circ = sum(1 for r in off if r == "원문자")
        changed = [(a, b) for a, b in zip(off, on) if a != b]
        left = sum(1 for r in on if r == "원문자")
        dist = Counter(b for _, b in changed)
        print(f"| {name} | {len(texts)} | {marked} | {circ} | {len(changed)} | {left} | "
              f"{', '.join(f'{k} {v}' for k, v in sorted(dist.items())) or '-'} |")
        tot.update(paras=len(texts), marked=marked, circ=circ, changed=len(changed), left=left)
    print(f"| **합계** | {tot['paras']} | {tot['marked']} | {tot['circ']} | {tot['changed']} | {tot['left']} | |")

    # 정답이 있는 표본(hierarchy/tests/golden.json): 끔/켬이 정답 역할과 맞는 개수.
    cases = json.loads((ROOT / "hierarchy/tests/golden.json").read_text(encoding="utf-8"))["cases"]
    cases = [c for c in cases if c["expected"] in GOLDEN_ROLE and off_role(c["text"])]
    texts = [c["text"] for c in cases]
    off, on = [off_role(t) for t in texts], on_roles(texts, exe)
    want = [GOLDEN_ROLE[c["expected"]] for c in cases]
    print(f"\n정답 있는 표본(golden, 항목기호가 있는 □ㅇ-※ 문단) {len(cases)}개")
    print("| | 정답과 일치 | 불일치 |")
    print("|---|---|---|")
    for label, got in (("끔(현재 규칙)", off), ("켬(엔진 보조)", on)):
        ok = sum(1 for a, b in zip(got, want) if a == b)
        print(f"| {label} | {ok} | {len(want) - ok} |")
    for t, a, b, w in zip(texts, off, on, want):
        if a != b or b != w:
            print(f"- `{t[:30]}` 끔={a} 켬={b} 정답={w}")


if __name__ == "__main__":
    main()
