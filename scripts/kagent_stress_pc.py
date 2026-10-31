"""K에이전트 누수 스트레스 측정 스크립트.

지속적인 클립보드 복사(글·그림·파일), 팝업 열기/닫기, 설정 변경 및 감시 재시작,
타임라인 파일 생성/삭제를 반복하며 메모리·핸들·GDI/USER 리소스 누수를 검사합니다.

사용:
    python scripts/kagent_stress_pc.py kagent/target/release/kagent.exe [--minutes 10] [--quick]
"""
from __future__ import annotations

import argparse
import ctypes
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from docfit_app.kagent_client import KAgentClient  # noqa: E402

if sys.platform == "win32":
    import ctypes.wintypes as wt
    from scripts.kagent_benchmark_pc import (  # noqa: E402
        CF_DIB,
        CF_HDROP,
        CF_UNICODETEXT,
        PMC,
        dib,
        get_text,
        hdrop,
        k32,
        open_clip,
        psapi,
        set_clip,
        set_text,
        u32,
    )
else:
    # 비 Windows 환경(Linux/macOS 단위 테스트용) 스텁
    wt = None
    k32 = None
    u32 = None
    psapi = None
    CF_UNICODETEXT, CF_DIB, CF_HDROP = 13, 8, 15

    class PMC:
        WorkingSetSize = 0
        PrivateUsage = 0

    def open_clip():
        pass

    def set_clip(fmt, data):
        pass

    def set_text(text):
        pass

    def get_text():
        return None

    def dib(width, height):
        return b""

    def hdrop(paths):
        return b""


def wait_condition(cond, timeout=5.0, interval=0.01):
    """조건이 참이 될 때까지 대기. 타임아웃 이후에도 마지막으로 한 번 더 확인."""
    t0 = time.perf_counter()
    while (time.perf_counter() - t0) < timeout:
        val = cond()
        if val:
            return val
        time.sleep(interval)
    return cond()


def check_existing_instance() -> bool:
    """기존 kagent 인스턴스가 실행 중인지 확인(단일 인스턴스 격리 보호)."""
    if sys.platform != "win32":
        return False
    # 1. 명명된 뮤텍스 검사
    synchronize = 0x00100000
    h_mutex = k32.OpenMutexW(synchronize, False, "Local\\HwpAutoDocFit.kagent")
    if h_mutex:
        k32.CloseHandle(h_mutex)
        return True
    # 2. 메인 창 클래스 검사
    hwnd = u32.FindWindowW("HwpAutoDocFit.KAgent", None)
    if hwnd:
        return True
    return False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="K에이전트 누수 스트레스 측정")
    parser.add_argument("exe", type=Path, help="kagent.exe 경로")
    parser.add_argument("--minutes", type=int, default=10, help="측정 지속 시간(분, 기본값: 10)")
    parser.add_argument("--quick", action="store_true", help="빠른 측정 모드(1분 측정, 초기 표본 대비 종료 표본 판정)")
    return parser.parse_args(argv)


def private_bytes(pid: int) -> int:
    snap = snapshot(pid)
    return snap.get("private", 0)


def handle_count(pid: int) -> int:
    snap = snapshot(pid)
    return snap.get("handles", 0)


def gui_resources(pid: int) -> tuple[int, int]:
    snap = snapshot(pid)
    return (snap.get("gdi", 0), snap.get("user", 0))


def snapshot(pid: int) -> dict[str, int | float | bool | str | None]:
    """지정 프로세스의 자원(작업 집합, 개인 메모리, 핸들, GDI, USER)을 측정."""
    if sys.platform != "win32":
        return {
            "timestamp": time.time(),
            "working_set": 0,
            "private": 0,
            "handles": 0,
            "gdi": 0,
            "user": 0,
            "valid": True,
            "error": None,
        }

    h = k32.OpenProcess(0x1000 | 0x0400, False, pid)
    if not h:
        err = ctypes.GetLastError()
        return {
            "timestamp": time.time(),
            "working_set": 0,
            "private": 0,
            "handles": 0,
            "gdi": 0,
            "user": 0,
            "valid": False,
            "error": f"OpenProcess failed (pid={pid}, error={err})",
        }

    try:
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        if not psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb):
            return {
                "timestamp": time.time(),
                "working_set": 0,
                "private": 0,
                "handles": 0,
                "gdi": 0,
                "user": 0,
                "valid": False,
                "error": f"GetProcessMemoryInfo failed (error={ctypes.GetLastError()})",
            }

        count = wt.DWORD()
        if not k32.GetProcessHandleCount(h, ctypes.byref(count)):
            return {
                "timestamp": time.time(),
                "working_set": 0,
                "private": 0,
                "handles": 0,
                "gdi": 0,
                "user": 0,
                "valid": False,
                "error": f"GetProcessHandleCount failed (error={ctypes.GetLastError()})",
            }

        # GetGuiResources: 실패 시 0 반환 및 GetLastError() 확인
        ctypes.set_last_error(0)
        gdi = u32.GetGuiResources(h, 0)
        gdi_err = ctypes.get_last_error()
        if gdi == 0 and gdi_err != 0:
            return {
                "timestamp": time.time(),
                "working_set": 0,
                "private": 0,
                "handles": 0,
                "gdi": 0,
                "user": 0,
                "valid": False,
                "error": f"GetGuiResources(GDI) failed (error={gdi_err})",
            }

        ctypes.set_last_error(0)
        user = u32.GetGuiResources(h, 1)
        user_err = ctypes.get_last_error()
        if user == 0 and user_err != 0:
            return {
                "timestamp": time.time(),
                "working_set": 0,
                "private": 0,
                "handles": 0,
                "gdi": 0,
                "user": 0,
                "valid": False,
                "error": f"GetGuiResources(USER) failed (error={user_err})",
            }

        return {
            "timestamp": time.time(),
            "working_set": int(pmc.WorkingSetSize),
            "private": int(pmc.PrivateUsage),
            "handles": int(count.value),
            "gdi": int(gdi),
            "user": int(user),
            "valid": True,
            "error": None,
        }
    finally:
        k32.CloseHandle(h)


def send_esc() -> None:
    """팝업 창에 Esc를 직접 보낸다(SendInput은 앞 창이 아니면 팝업에 닿지 않는다)."""
    if sys.platform != "win32":
        return
    hwnd = ctypes.windll.user32.FindWindowW("HwpAutoDocFit.KAgentPopup", None)
    if hwnd:
        ctypes.windll.user32.PostMessageW(hwnd, 0x0100, 0x1B, 0)  # WM_KEYDOWN, VK_ESCAPE


def evaluate_samples(
    samples: list[dict],
    quick: bool,
    minutes: int,
    stress_counts: dict[str, int] | None = None,
    errors: list[str] | None = None,
) -> dict:
    """표본 데이터를 평가하여 PASS/FAIL을 판정.

    판정 기준:
    - quick 모드: 30초 준비 구간 뒤 표본(baseline)과 60초 종료 표본(end) 비교
    - 일반 모드: 60초 시점 기준 표본(baseline)과 마지막 종료 표본(end) 비교
    - PrivateUsage 증가량 < 1 MiB (1,048,576 B)
    - HandleCount 증가량 < 20
    - GdiObjects 증가량 < 20
    - 자원 수집 API 실패 없어야 함
    - 필수 스트레스 단계 수행 요건 충족 및 예외 없어야 함
    - 표본 간격 편차가 정상 범위(15~45초) 내에 있어야 함
    """
    failures = []

    if not samples:
        return {
            "parameters": {"minutes": 1 if quick else minutes, "quick": quick},
            "passed": False,
            "failures": ["no_samples_collected"],
            "samples": [],
            "sample_intervals": [],
            "stress_counts": stress_counts or {},
            "errors": errors or [],
        }

    # 1. 자원 수집 유효성 검사 (API 실패 확인)
    for i, s in enumerate(samples):
        if not s.get("valid", True) or s.get("error"):
            failures.append(f"자원 측정 API 호출 실패 (표본 #{i}): {s.get('error')}")

    # 2. 기준 표본(baseline) 및 종료 표본(end) 선택
    quick_baseline_info = None
    if quick:
        # quick 모드: 시작 직후 30초는 스레드·감시·팝업 창이 처음 만들어지는 준비 구간이라 기준에서 뺀다.
        baseline = next((s for s in samples if s.get("elapsed_sec", 0) >= 25.0), None)
        end = samples[-1] if len(samples) >= 2 else None
        quick_baseline_info = "after_warmup_30s"
        if end is None:
            failures.append("quick 모드 최소 표본 부족 (초기 표본 및 1분 종료 표본 필요)")
        elif end.get("elapsed_sec", 0) < 45.0:
            failures.append(f"quick 모드 측정 지속 시간 미달 ({end.get('elapsed_sec', 0):.1f}초 < 45초)")
        elif baseline is None or end is baseline:
            failures.append("quick 모드 최소 표본 부족 (준비 구간 뒤 표본과 1분 종료 표본 필요)")
    else:
        # 일반 모드: 처음 1분(60초) 시점 이후 첫 표본을 baseline으로 삼고 마지막 표본과 비교
        baseline = next((s for s in samples if s.get("elapsed_sec", 0) >= 60.0), None)
        end = samples[-1] if samples else None
        if baseline is None:
            failures.append("60초 시점 기준 표본 부재 (측정 지속 시간 60초 미만)")
        elif end is None or end is baseline or end.get("elapsed_sec", 0) <= baseline.get("elapsed_sec", 0):
            failures.append("60초 이후 유효 종료 표본 부재 (baseline 이후 측정 구간 필요)")

    # 3. 필수 스트레스 단계 수행 횟수 검증
    if stress_counts is not None:
        min_clips = 50 if quick else 500
        min_popups = 1 if quick else 10
        min_settings = 1 if quick else 5
        min_timeline = 1 if quick else 5

        if stress_counts.get("clip_success", 0) < min_clips:
            failures.append(f"클립보드 복사 부하 횟수 미달 ({stress_counts.get('clip_success', 0)} < {min_clips})")
        if stress_counts.get("popup_success", 0) < min_popups:
            failures.append(f"팝업 열기/닫기 횟수 미달 ({stress_counts.get('popup_success', 0)} < {min_popups})")
        if stress_counts.get("settings_success", 0) < min_settings:
            failures.append(f"설정 재시작 횟수 미달 ({stress_counts.get('settings_success', 0)} < {min_settings})")
        if stress_counts.get("timeline_success", 0) < min_timeline:
            failures.append(f"타임라인 파일 변경 횟수 미달 ({stress_counts.get('timeline_success', 0)} < {min_timeline})")

    # 4. 필수 단계 에러 확인
    if errors:
        for err in errors[:5]:
            failures.append(f"스트레스 작업 오류: {err}")

    # 5. 표본 수집 간격 편차 검증 (목표 30초, 중간 표본 허용 간격 15~45초)
    sample_intervals = []
    for i in range(1, len(samples)):
        dt = samples[i].get("elapsed_sec", 0) - samples[i - 1].get("elapsed_sec", 0)
        sample_intervals.append(round(dt, 2))
        if i < len(samples) - 1 and (dt < 15.0 or dt > 45.0):
            failures.append(f"표본 수집 주기 편차 초과 (#{i}: {dt:.1f}초, 허용 15~45초)")

    # 6. 자원 증가량 판정 (baseline과 end가 유효할 때)
    diff_private = 0
    diff_handles = 0
    diff_gdi = 0
    diff_user = 0
    if baseline and end and end is not baseline:
        diff_private = end["private"] - baseline["private"]
        diff_handles = end["handles"] - baseline["handles"]
        diff_gdi = end["gdi"] - baseline["gdi"]
        diff_user = end["user"] - baseline["user"]

        if diff_private >= 1024 * 1024:
            failures.append(f"PrivateUsage 증가량 {diff_private} 바이트 (한도 1MB 미만)")
        if diff_handles >= 20:
            failures.append(f"HandleCount 증가량 {diff_handles} (한도 20 미만)")
        if diff_gdi >= 20:
            failures.append(f"GdiObjects 증가량 {diff_gdi} (한도 20 미만)")

    res_dict = {
        "parameters": {"minutes": 1 if quick else minutes, "quick": quick},
        "baseline": baseline,
        "end": end,
        "diff": {
            "private": diff_private,
            "handles": diff_handles,
            "gdi": diff_gdi,
            "user": diff_user,
        },
        "passed": len(failures) == 0,
        "failures": failures,
        "samples": samples,
        "sample_intervals": sample_intervals,
        "stress_counts": stress_counts or {},
        "errors": errors or [],
    }
    if quick_baseline_info is not None:
        res_dict["quick_baseline"] = quick_baseline_info
    return res_dict


def run(exe: Path, minutes: int, quick: bool) -> dict:
    """스트레스 측정을 실행."""
    exe = exe.resolve()
    # quick 모드는 1분(60초) 측정, 일반 모드는 지정된 분(기본 10분)
    effective_minutes = 1 if quick else minutes
    total_seconds = effective_minutes * 60

    # 1. 단일 인스턴스 격리 확인: 기존 실행 중인 kagent가 있으면 즉시 중단
    if check_existing_instance():
        raise RuntimeError(
            "기존 kagent 인스턴스가 실행 중입니다. "
            "사용자 데이터 보호 및 격리를 위해 기존 에이전트를 먼저 종료한 후 다시 실행하십시오."
        )

    data_dir = Path(tempfile.mkdtemp(prefix="kagent-stress-data-"))
    shots_dir = Path(tempfile.mkdtemp(prefix="kagent-stress-shots-"))
    fixture_dir = data_dir / "timeline_fixture"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    test_file = fixture_dir / "stress_item.txt"
    test_file.write_text("initial", encoding="utf-8")

    orig_data = os.environ.get("KAGENT_DATA")
    orig_shots = os.environ.get("KAGENT_SCREENSHOTS")
    os.environ["KAGENT_DATA"] = str(data_dir)
    os.environ["KAGENT_SCREENSHOTS"] = str(shots_dir)

    original_text = None
    try:
        original_text = get_text()
    except Exception:
        pass

    client = KAgentClient(data_dir)
    proc: subprocess.Popen | None = None
    samples: list[dict] = []
    stress_counts = {
        "clip_success": 0,
        "popup_success": 0,
        "settings_success": 0,
        "timeline_success": 0,
    }
    errors: list[str] = []
    orig_timeline_roots: list[str] = []
    cur_settings: dict = {}

    try:
        proc = subprocess.Popen([str(exe)], env=dict(os.environ))

        status = wait_condition(lambda: client.status_file(), 10.0)
        if not status:
            raise RuntimeError("K에이전트가 정상 시작되지 않았습니다")

        # 타임라인 설정에 fixture 등록 및 반영 검증
        cur_res = client.request("settings_get")
        if not cur_res or not cur_res.get("ok"):
            raise RuntimeError("초기 settings_get 요청 실패")

        cur_settings = cur_res.get("settings", {})
        orig_timeline_roots = list(cur_settings.get("timeline_roots", []))
        roots = list(orig_timeline_roots)
        if str(fixture_dir) not in roots:
            roots.append(str(fixture_dir))
        client.request("settings_set", settings=dict(cur_settings, timeline_roots=roots))

        # 반영 확인
        verify_res = client.request("settings_get")
        verify_settings = verify_res.get("settings", {}) if verify_res else {}
        if str(fixture_dir) not in verify_settings.get("timeline_roots", []):
            raise RuntimeError("타임라인 fixture 감시 등록 확인 실패")

        t0 = time.perf_counter()
        init_snap = snapshot(proc.pid)
        init_snap["elapsed_sec"] = 0.0
        samples.append(init_snap)

        next_snap = 30.0
        next_popup = 30.0
        next_settings = 30.0 if quick else 60.0
        next_timeline = 30.0 if quick else 60.0
        cycle = 0

        while (time.perf_counter() - t0) < total_seconds:
            # 80ms 간격으로 글·그림·파일 경로 복사 순환
            mod = cycle % 3
            try:
                if mod == 0:
                    set_text(f"stress text #{cycle} " + "가" * 50)
                elif mod == 1:
                    set_clip(CF_DIB, dib(32, 32))
                else:
                    set_clip(CF_HDROP, hdrop([str(test_file)]))
                stress_counts["clip_success"] += 1
            except Exception as e:
                errors.append(f"clip_operation_error: {type(e).__name__}")

            cycle += 1
            time.sleep(0.08)

            elapsed = time.perf_counter() - t0

            # 30초마다 팝업 열기/닫기 (두 번째 실행 -> 팝업 감지 -> Esc -> 닫힘 확인)
            if elapsed >= next_popup:
                try:
                    pop_proc = subprocess.run([str(exe)], timeout=5)
                    if pop_proc.returncode == 0:
                        popup_hwnd = wait_condition(
                            lambda: (
                                u32.FindWindowW("HwpAutoDocFit.KAgentPopup", None)
                                if sys.platform == "win32" and u32.IsWindowVisible(u32.FindWindowW("HwpAutoDocFit.KAgentPopup", None))
                                else (1 if sys.platform != "win32" else None)
                            ),
                            timeout=2.0,
                            interval=0.02,
                        )
                        if popup_hwnd:
                            send_esc()
                            closed = wait_condition(
                                lambda: (
                                    sys.platform != "win32"
                                    or not u32.FindWindowW("HwpAutoDocFit.KAgentPopup", None)
                                    or not u32.IsWindowVisible(u32.FindWindowW("HwpAutoDocFit.KAgentPopup", None))
                                ),
                                timeout=2.0,
                                interval=0.02,
                            )
                            if closed:
                                stress_counts["popup_success"] += 1
                            else:
                                errors.append("popup_close_timeout")
                        else:
                            errors.append("popup_window_not_visible")
                    else:
                        errors.append(f"popup_proc_returncode: {pop_proc.returncode}")
                except Exception as e:
                    errors.append(f"popup_error: {type(e).__name__}")
                while next_popup <= elapsed:
                    next_popup += 30.0

            # 설정 재호출 (감시 재시작)
            if elapsed >= next_settings:
                try:
                    cur = client.request("settings_get")
                    if cur and cur.get("ok"):
                        client.request("settings_set", settings=cur.get("settings", {}))
                        stress_counts["settings_success"] += 1
                    else:
                        errors.append("settings_get_empty_in_loop")
                except Exception as e:
                    errors.append(f"settings_error: {type(e).__name__}")
                while next_settings <= elapsed:
                    next_settings += (30.0 if quick else 60.0)

            # 타임라인 파일 생성/삭제
            if elapsed >= next_timeline:
                try:
                    if test_file.exists():
                        test_file.unlink()
                    else:
                        test_file.write_text(f"content {cycle}", encoding="utf-8")
                    stress_counts["timeline_success"] += 1
                except Exception as e:
                    errors.append(f"timeline_error: {type(e).__name__}")
                while next_timeline <= elapsed:
                    next_timeline += (30.0 if quick else 60.0)

            # 30초마다 스냅샷 수집
            if elapsed >= next_snap:
                snap = snapshot(proc.pid)
                snap["elapsed_sec"] = round(elapsed, 1)
                samples.append(snap)
                while next_snap <= elapsed:
                    next_snap += 30.0

        # 루프 종료 시 마지막 스냅샷
        final_snap = snapshot(proc.pid)
        final_snap["elapsed_sec"] = round(time.perf_counter() - t0, 1)
        samples.append(final_snap)

    finally:
        if proc is not None:
            # 원 설정 복원 및 감시 재시작 확인
            try:
                if cur_settings:
                    client.request("settings_set", settings=dict(cur_settings, timeline_roots=orig_timeline_roots))
                    wait_condition(
                        lambda: (
                            (client.request("settings_get") or {}).get("settings", {}).get("timeline_roots") == orig_timeline_roots
                        ),
                        timeout=3.0,
                    )
            except Exception:
                pass
            try:
                client.request("quit")
            except Exception:
                pass
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                proc.kill()

        if original_text is not None:
            try:
                set_text(original_text)
            except Exception:
                pass

        if orig_data is not None:
            os.environ["KAGENT_DATA"] = orig_data
        else:
            os.environ.pop("KAGENT_DATA", None)

        if orig_shots is not None:
            os.environ["KAGENT_SCREENSHOTS"] = orig_shots
        else:
            os.environ.pop("KAGENT_SCREENSHOTS", None)

        shutil.rmtree(data_dir, ignore_errors=True)
        shutil.rmtree(shots_dir, ignore_errors=True)

    result = evaluate_samples(
        samples,
        quick=quick,
        minutes=minutes,
        stress_counts=stress_counts,
        errors=errors,
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        res = run(args.exe, minutes=args.minutes, quick=args.quick)
    except Exception as e:
        print(f"\n[오류로 스트레스 측정 중단]: {e}")
        return 1

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = reports_dir / f"kagent-stress-{stamp}.json"
    report_path.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"\n[보고서 저장]: {report_path}")

    if res.get("passed"):
        print("\n판정: PASS")
        return 0
    else:
        print("\n판정: FAIL")
        for fail in res.get("failures", []):
            print(f" - {fail}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
