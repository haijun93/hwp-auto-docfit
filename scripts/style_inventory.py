"""문서 스타일 전수 분석 보고서와 예시 서식 HWPX를 만든다.

사용법:
    python scripts/style_inventory.py 문서.hwp [--out 폴더]

결과(기본: 원본과 같은 폴더):
    <이름>_스타일분석.md    사람이 읽는 보고서
    <이름>_스타일분석.json  전체 분석 데이터
    <이름>_서식예시.hwpx    스타일 유형별 대표 문단·표 종류별 대표 표만 남긴 예시 서식 문서

HWP는 원본을 건드리지 않고 임시 사본을 한/글로 HWPX 변환해 분석한다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import runpy
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docfit_core.style_inventory import analyze_style_inventory, build_style_sample, inventory_markdown  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    source = args.source.resolve()
    out = (args.out or source.parent).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="hwp_style_inventory_") as folder:
        if source.suffix.lower() == ".hwpx" and zipfile.is_zipfile(source):
            snapshot = source
        else:
            # HWP, 또는 확장자만 .hwpx인 HWP는 한/글로 임시 변환한다.
            ns = runpy.run_path(str(ROOT / "hwp-auto-docfit.py"), run_name="style_inventory")
            snapshot = ns["분석용_hwpx_준비"](source, folder)
        inventory = analyze_style_inventory(snapshot)
        inventory["source"] = source.name
        report = out / f"{source.stem}_스타일분석.md"
        data = out / f"{source.stem}_스타일분석.json"
        sample = out / f"{source.stem}_서식예시.hwpx"
        report.write_text(inventory_markdown(inventory), encoding="utf-8")
        data.write_text(json.dumps(inventory, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        stats = build_style_sample(snapshot, sample, inventory)

    s = inventory["summary"]
    print(f"문자 모양 {s['chars_used']}/{s['chars_defined']} · 문단 모양 {s['paras_used']}/{s['paras_defined']} "
          f"· 스타일 유형 {s['types']} · 표 {s['table_types']}종")
    print(f"예시 서식: 본문 {stats['paragraphs']}문단, 표 {stats['tables']}개")
    for path in (report, data, sample):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
