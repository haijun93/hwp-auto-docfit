"""Codex 실행 및 사용 한도 소진 자동 감지·스케줄 워치독 도구.

- 코덱스 실행 중 '한도 소진(usage limit / rate limit)' 발생 시 자동 감지
- 리셋 시간(기본 사용자 지정 02:06 am 또는 출력 메시지의 시간)을 추출하여 codex_status.json에 기록
- 한도 소진 시 fallback 신호를 표준 출력 및 JSON으로 반환하여 제미나이 워커가 작업을 인수하고,
  지정된 리셋 시점에 코덱스를 즉시 재투입할 수 있도록 지원.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

CODEX_BIN = r"C:\Users\haiju\AppData\Local\OpenAI\Codex\bin\37f54d68e5533a51\codex.exe"
STATUS_FILE = Path(r"C:\HWP_AUTODOCFIT\v1803\sec\codex_status.json")


def parse_reset_time(text: str) -> datetime.datetime:
    """텍스트에서 리셋 시간을 파싱하거나 기본 02:06 am을 반환."""
    now = datetime.datetime.now()
    # 02:06 am 패턴 검색
    m = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?", text, re.I)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        ampm = (m.group(3) or "").lower()
        if ampm == "pm" and h < 12:
            h += 12
        elif ampm == "am" and h == 12:
            h = 0
        target = now.replace(hour=h, minute=mn, second=0, microsecond=0)
        if target <= now:
            target += datetime.timedelta(days=1)
        return target

    # 사용자 명시 기본값: 익일 02:06 AM
    target = now.replace(hour=2, minute=6, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return target


def run_codex(prompt: str, workdir: str | Path | None = None) -> dict:
    workdir = str(workdir or Path.cwd())
    cmd = [
        CODEX_BIN,
        "exec",
        "--cd", workdir,
        "--dangerously-bypass-approvals-and-sandbox",
        "-",
    ]

    print(f"[*] Codex 실행 시작 (작업 디렉터리: {workdir})...")
    start_time = datetime.datetime.now()

    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        combined = stdout + "\n" + stderr
        exit_code = proc.returncode
    except subprocess.TimeoutExpired as e:
        combined = f"TimeoutExpired: {e}"
        exit_code = -1

    # 한도 소진 패턴 검사
    exhausted_pattern = re.compile(
        r"(usage\s+limit|rate\s+limit|too\s+many\s+requests|quota\s+exceeded|429\s+Too\s+Many|한도\s*소진|사용량\s*초과)",
        re.I,
    )

    is_exhausted = bool(exhausted_pattern.search(combined))

    result = {
        "timestamp": start_time.isoformat(),
        "exit_code": exit_code,
        "is_exhausted": is_exhausted,
        "output": combined[:4000],
    }

    if is_exhausted:
        reset_time = parse_reset_time(combined)
        sec_until_reset = max(0, int((reset_time - datetime.datetime.now()).total_seconds()))
        result["status"] = "EXHAUSTED"
        result["reset_at"] = reset_time.isoformat()
        result["seconds_until_reset"] = sec_until_reset
        print(f"\n[!] [CODEX_EXHAUSTED] 사용 한도 소진 감지됨!")
        print(f"    - 리셋 예정 시각: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    - 남은 대기 시간: {sec_until_reset}초 ({sec_until_reset/3600:.2f}시간)")
        print(f"    - 제미나이 워커(제미나이 1/3)로 자동 인계됩니다.")
    else:
        result["status"] = "SUCCESS" if exit_code == 0 else "FAILED"
        print(f"[*] Codex 정상 완료 (exit_code={exit_code}).")

    STATUS_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Codex Watchdog Runner")
    parser.add_argument("--prompt", "-p", type=str, default="", help="Prompt text")
    parser.add_argument("--file", "-f", type=str, default="", help="Prompt file path")
    parser.add_argument("--workdir", "-w", type=str, default="", help="Working directory")
    args = parser.parse_args()

    prompt_text = args.prompt
    if args.file and os.path.exists(args.file):
        prompt_text = Path(args.file).read_text(encoding="utf-8")

    if not prompt_text.strip():
        # 기본 헬스체크
        prompt_text = "echo 'Codex status check'"

    run_codex(prompt_text, args.workdir or None)
