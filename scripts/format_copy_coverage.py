"""서식 복사 복제 범위 측정: 폴더의 HWPX 예시 보고서마다 서식 요소 분석 결과 가운데 서식 적용에 쓰는 요소의
비율(값 복사·규칙 복사)과 표시만 하는 요소를 센다(FORMAT_COPY_DESIGN.md 8장).

사용: python scripts/format_copy_coverage.py <폴더> [--json 결과.json]
문서는 읽기만 한다.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import runpy
import sys
import zipfile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    namespace = runpy.run_path(str(repo / "hwp-auto-docfit.py"), run_name="format_copy_coverage")
    elements = namespace["서식요소"]
    classify = namespace["서식표_종류판별"]
    totals, shown_keys, results = Counter(), Counter(), []
    for path in sorted(args.folder.glob("*.hwpx")):
        if not zipfile.is_zipfile(path):
            continue
        try:
            analysis = elements.analyze_format_elements(path, classify)
        except Exception as exc:  # 손상·지원하지 않는 문서는 건너뛰고 알린다
            results.append({"file": path.name, "error": str(exc)})
            continue
        found = elements.coverage(analysis)
        for node, _, _ in elements.detail_nodes(analysis):
            for key in elements.element_map(analysis, node):
                area = node[0]
                mode = elements.element_mode(key, node)
                totals[(area, mode)] += 1
                if mode == elements.MODE_SHOW:
                    shown_keys[f"{area}.{key}"] += 1
        results.append({"file": path.name, **found,
                        "box_sample": "box" in analysis.get("samples", {}),
                        "page_number": bool(analysis.get("page_number")),
                        "gap_rule": "overview_to_first" in (analysis.get("spacing_rules") or {})})
    areas = sorted({area for area, _ in totals})
    print(f"문서 {sum(1 for r in results if 'error' not in r)}개")
    for area in areas:
        total = sum(n for (a, _), n in totals.items() if a == area)
        applied = total - totals[(area, elements.MODE_SHOW)]
        print(f"  {area:7} 요소 {total:5}개 · 적용 {applied:5}개 ({applied / total:.0%}) "
              f"[값 복사 {totals[(area, elements.MODE_VALUE)]} · 규칙 복사 {totals[(area, elements.MODE_RULE)]}]")
    total = sum(totals.values())
    applied = total - sum(n for (_, m), n in totals.items() if m == elements.MODE_SHOW)
    print(f"  전체    요소 {total:5}개 · 적용 {applied:5}개 ({applied / max(1, total):.0%})")
    print("  표시만(상위):", ", ".join(f"{k} {n}" for k, n in shown_keys.most_common(8)))
    print(f"  한 칸 상자 예시 보관: {sum(r.get('box_sample', False) for r in results)}개 문서 · "
          f"쪽 번호 모양: {sum(r.get('page_number', False) for r in results)}개 · "
          f"제목~첫 문장 간격: {sum(r.get('gap_rule', False) for r in results)}개")
    if args.json:
        args.json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
