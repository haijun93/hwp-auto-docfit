"""kordoc 4.24.9 기반 기관별·프리셋별 예시 전종 HWPX 생성 및 규범 기준본 구축 스크립트.
불변 규칙: 항목기호와 본문 사이 일반 스페이스 1개, 탭 금지.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docfit_core.marker_spacing import normalize_hwpx

NODE_EXE = r"C:\Users\haiju\AppData\Local\HwpAutoDocFit\kordoc-runtime\4.24.9\node\node.exe"
CLI_JS = r"C:\Users\haiju\AppData\Local\HwpAutoDocFit\kordoc-runtime\4.24.9\app\node_modules\kordoc\dist\cli.js"

BASE_DIR = Path(r"C:\HWP_AUTODOCFIT\테스트예시\kordoc_generated_20261025")
RAW_DIR = BASE_DIR / "raw"
NORM_DIR = BASE_DIR / "normative"
INPUT_MD = BASE_DIR / "sample_input.md"

PRESETS = [
    ("01_기안문", ["--preset", "기안문"]),
    ("02_보고서", ["--preset", "보고서"]),
    ("03_계획서", ["--preset", "계획서"]),
    ("04_통지", ["--preset", "통지"]),
    ("05_회의록", ["--preset", "회의록"]),
    ("06_개조식", ["--preset", "개조식"]),
    ("07_업무보고", ["--preset", "업무보고"]),
    ("08_서울방침", ["--preset", "서울방침"]),
    ("09_보도자료", ["--preset", "보도자료"]),
    ("10_보고서_국세청", ["--preset", "보고서", "--agency", "국세청"]),
    ("11_보고서_교육부", ["--preset", "보고서", "--agency", "교육부"]),
    ("12_보고서_과학기술정보통신부", ["--preset", "보고서", "--agency", "과학기술정보통신부"]),
    ("13_보고서_행정안전부", ["--preset", "보고서", "--agency", "행정안전부"]),
    ("14_업무보고_고용노동부", ["--preset", "업무보고", "--agency", "고용노동부"]),
    ("15_계획서_보건복지부", ["--preset", "계획서", "--agency", "보건복지부"]),
    ("16_보도자료_행정안전부", ["--preset", "보도자료", "--agency", "행정안전부"]),
    ("17_서울방침_서울시", ["--preset", "서울방침", "--org", "서울특별시"]),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    NORM_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_MD.exists():
        print(f"오류: 입력 마크다운 파일이 없습니다: {INPUT_MD}")
        return 1

    print("=== kordoc 전종 생성 시작 (kordoc 4.24.9) ===")
    raw_manifest = {
        "kordoc_version": "4.24.9",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_markdown": str(INPUT_MD),
        "source_sha256": sha256_file(INPUT_MD),
        "files": [],
    }

    norm_manifest = {
        "kordoc_version": "4.24.9",
        "normalized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rule": "항목기호 뒤 일반 빈칸 1개, 탭 금지, 앞 빈칸 규범화",
        "files": [],
    }

    success_count = 0
    for name, args in PRESETS:
        raw_hwpx = RAW_DIR / f"{name}.hwpx"
        norm_hwpx = NORM_DIR / f"{name}.hwpx"

        cmd = [NODE_EXE, CLI_JS, "generate", str(INPUT_MD), "-o", str(raw_hwpx)] + args
        print(f"[생성] {name} ... ", end="", flush=True)

        t0 = time.time()
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        dt = time.time() - t0

        if res.returncode != 0:
            err_msg = res.stderr.strip() or res.stdout.strip()
            print(f"실패 (코드 {res.returncode}): {err_msg[:120]}")
            continue

        raw_size = raw_hwpx.stat().st_size
        raw_hash = sha256_file(raw_hwpx)
        print(f"성공 ({dt:.2f}s, {raw_size:,} bytes)")

        raw_manifest["files"].append({
            "name": raw_hwpx.name,
            "args": args,
            "size": raw_size,
            "sha256": raw_hash,
        })

        if norm_hwpx.exists():
            norm_hwpx.unlink()

        norm_changes = normalize_hwpx(raw_hwpx, norm_hwpx)
        norm_size = norm_hwpx.stat().st_size
        norm_hash = sha256_file(norm_hwpx)

        norm_manifest["files"].append({
            "name": norm_hwpx.name,
            "raw_sha256": raw_hash,
            "sha256": norm_hash,
            "size": norm_size,
            "marker_tab_changes": norm_changes,
        })
        print(f"  └ [규범본] 치환된 항목기호 탭/공백: {norm_changes}건")
        success_count += 1

    (RAW_DIR / "manifest.json").write_text(json.dumps(raw_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (NORM_DIR / "manifest.json").write_text(json.dumps(norm_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n전체 {len(PRESETS)}종 중 {success_count}종 생성 및 규범화 완료!")
    print(f"Raw 저장 위치: {RAW_DIR}")
    print(f"Normative 저장 위치: {NORM_DIR}")
    return 0 if success_count == len(PRESETS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
