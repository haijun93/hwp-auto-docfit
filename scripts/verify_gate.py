# -*- coding: utf-8 -*-

"""
============================================================
HWP Auto DocFit - 정확도 회귀 게이트 (accuracy gate)
============================================================
kwakseongjae/auto-hwp의 scripts/verify-local.sh 철학을 이식한 것이다:

    "오늘 이 엔진이 내는 값을 그대로 못 박은 회귀 금지선일 뿐이다."

즉 "한/글의 참값"과 비교하는 게 아니라(그러려면 실제 HWP가 필요하다),
**엔진을 같은 입력에 반복 적용해도 결과가 항상 안정적인지**를 검증한다.
자간/장평을 조정한 문서에 엔진을 한 번 더 돌렸을 때 줄 수·문단 수가
계속 줄어들거나 늘어나면(불안정하면) 회귀로 간주하고 실패한다.

CI(.github/workflows/ci.yml)가 push/PR마다 이 게이트를 실행한다.
로컬에서 머지 전에 직접 돌리려면:

    python3 scripts/verify_gate.py
============================================================
"""

import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from hwpx_engine import fit_hwpx_package  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "test(자간조정).hwpx"

NS_P = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def count_lines_and_paragraphs(hwpx_path: Path) -> tuple[int, int]:
    """HWPX 문서 전체의 총 lineseg(줄) 수와 문단 수를 센다."""
    total_linesegs = 0
    total_paragraphs = 0

    with zipfile.ZipFile(hwpx_path, "r") as z:
        section_names = sorted(
            n for n in z.namelist()
            if n.startswith("Contents/section") and n.endswith(".xml")
        )
        for name in section_names:
            tree = ET.fromstring(z.read(name))
            for p in tree.iter(f"{NS_P}p"):
                t_elems = [t for t in p.iter(f"{NS_P}t") if t.text]
                full_text = "".join(t.text for t in t_elems).strip()
                if not full_text:
                    continue
                total_paragraphs += 1
                lsa = p.find(f"{NS_P}linesegarray")
                if lsa is not None:
                    total_linesegs += len(lsa.findall(f"{NS_P}lineseg"))

    return total_linesegs, total_paragraphs


def run_gate() -> bool:
    print("=" * 70)
    print("HWP Auto DocFit - 정확도 회귀 게이트")
    print("=" * 70)

    if not FIXTURE.is_file():
        print(f"❌ 게이트 실패: 기준 픽스처를 찾을 수 없습니다: {FIXTURE}")
        return False

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        pass1_out = tmp_path / "pass1.hwpx"
        pass2_out = tmp_path / "pass2.hwpx"

        shutil.copy2(FIXTURE, pass1_out)

        result1 = fit_hwpx_package(str(pass1_out), str(pass1_out))
        lines1, paras1 = count_lines_and_paragraphs(pass1_out)
        print(f"\n[1회차] 조정 문단 {result1['adjusted_count']}개, "
              f"총 줄 수 {lines1}, 총 문단 수 {paras1}")

        shutil.copy2(pass1_out, pass2_out)
        result2 = fit_hwpx_package(str(pass2_out), str(pass2_out))
        lines2, paras2 = count_lines_and_paragraphs(pass2_out)
        print(f"[2회차] 조정 문단 {result2['adjusted_count']}개, "
              f"총 줄 수 {lines2}, 총 문단 수 {paras2}")

        ok = True

        if paras1 != paras2:
            print(f"❌ 게이트 실패: 문단 수가 재실행 사이에 바뀌었습니다 "
                  f"({paras1} → {paras2})")
            ok = False

        if lines2 < lines1:
            print(f"❌ 게이트 실패: 재실행 후 줄 수가 더 줄었습니다 "
                  f"({lines1} → {lines2}) — 엔진이 안정 상태(fixed point)에 "
                  f"도달하지 못했습니다.")
            ok = False
        elif lines2 > lines1:
            print(f"❌ 게이트 실패: 재실행 후 줄 수가 늘었습니다 "
                  f"({lines1} → {lines2}) — 회귀입니다.")
            ok = False

        if ok:
            print(f"\n✅ 게이트 통과: 재실행해도 줄 수({lines1})·문단 수({paras1})가 "
                  f"안정적으로 유지됩니다.")

    print("=" * 70)
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_gate() else 1)
