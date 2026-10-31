"""K에이전트 실측(Windows PC): 시작 시간·상주 메모리·유휴 CPU·복사 1건 처리·중복·복원·그림·파일.

사용: .venv\\Scripts\\python.exe scripts\\kagent_benchmark_pc.py kagent\\target\\release\\kagent.exe
시험용 데이터 폴더(임시)를 쓰고 끝나면 지운다. 시험 중 클립보드 내용이 바뀌며, 끝나면 원래 텍스트를 돌려놓는다.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from docfit_app.kagent_client import KAgentClient  # noqa: E402

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
psapi = ctypes.WinDLL("psapi")
k32.GlobalAlloc.restype = wt.HGLOBAL
k32.GlobalLock.restype = ctypes.c_void_p
k32.GlobalLock.argtypes = [wt.HGLOBAL]
k32.GlobalUnlock.argtypes = [wt.HGLOBAL]
u32.SetClipboardData.argtypes = [wt.UINT, wt.HANDLE]
u32.SetClipboardData.restype = wt.HANDLE
u32.GetClipboardData.restype = wt.HANDLE
k32.OpenProcess.restype = wt.HANDLE
CF_UNICODETEXT, CF_DIB, CF_HDROP = 13, 8, 15


class PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t), ("PrivateUsage", ctypes.c_size_t)]


def open_clip():
    for _ in range(50):
        if u32.OpenClipboard(None):
            return
        time.sleep(0.01)
    raise RuntimeError("clipboard busy")


def set_clip(fmt, data: bytes):
    open_clip()
    try:
        u32.EmptyClipboard()
        h = k32.GlobalAlloc(0x0002, len(data))
        p = k32.GlobalLock(h)
        ctypes.memmove(p, data, len(data))
        k32.GlobalUnlock(h)
        u32.SetClipboardData(fmt, h)
    finally:
        u32.CloseClipboard()


def set_text(text):
    set_clip(CF_UNICODETEXT, (text + "\0").encode("utf-16-le"))


def get_text():
    open_clip()
    try:
        h = u32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return None
        p = k32.GlobalLock(h)
        try:
            return ctypes.wstring_at(p)
        finally:
            k32.GlobalUnlock(h)
    finally:
        u32.CloseClipboard()


def dib(width, height):
    header = (40).to_bytes(4, "little") + width.to_bytes(4, "little") + height.to_bytes(4, "little", signed=True)
    header += (1).to_bytes(2, "little") + (32).to_bytes(2, "little") + bytes(24)
    return header + bytes([40, 120, 220, 255]) * (width * height)


def hdrop(paths):
    body = b"".join(p.encode("utf-16-le") + b"\0\0" for p in paths) + b"\0\0"
    return (20).to_bytes(4, "little") + bytes(8) + (0).to_bytes(4, "little") + (1).to_bytes(4, "little") + body


def process_stats(pid):
    h = k32.OpenProcess(0x1000 | 0x0400, False, pid)
    pmc = PMC()
    pmc.cb = ctypes.sizeof(PMC)
    psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb)
    c, e, kt, ut = wt.FILETIME(), wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
    k32.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(kt), ctypes.byref(ut))
    k32.CloseHandle(h)
    to = lambda f: ((f.dwHighDateTime << 32) | f.dwLowDateTime) / 1e7  # noqa: E731
    return dict(ws=pmc.WorkingSetSize, private=pmc.PrivateUsage, cpu=to(kt) + to(ut))


def wait(cond, timeout=5.0):
    end = time.perf_counter() + timeout
    while time.perf_counter() < end:
        value = cond()
        if value:
            return value
        time.sleep(0.005)
    return None


def main():
    exe = Path(sys.argv[1]).resolve()
    data = Path(tempfile.mkdtemp(prefix="kagent-bench-"))
    os.environ["KAGENT_DATA"] = str(data)
    original = get_text()
    client = KAgentClient(data)
    results = {"exe_bytes": exe.stat().st_size}
    t0 = time.perf_counter()
    proc = subprocess.Popen([str(exe)], env=dict(os.environ))
    status = wait(lambda: client.status_file(), 10)
    results["start_to_ready_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    assert status, "에이전트가 시작하지 않았습니다"
    try:
        time.sleep(1.0)
        idle0 = process_stats(proc.pid)
        time.sleep(10.0)
        idle1 = process_stats(proc.pid)
        results["idle_cpu_percent_10s"] = round((idle1["cpu"] - idle0["cpu"]) / 10.0 * 100, 4)
        results["working_set_idle_mb"] = round(idle1["ws"] / 2**20, 2)
        results["private_idle_mb"] = round(idle1["private"] / 2**20, 2)

        # 텍스트 1건: 복사 → 목록에 보일 때까지(읽기 지연 60ms 포함)
        lat = []
        for i in range(20):
            text = f"측정 텍스트 {i} " + "가" * 50
            t = time.perf_counter()
            set_text(text)
            ok = wait(lambda: client.request("list", limit=1)["items"][:1] and
                      client.request("list", limit=1)["items"][0]["preview"].startswith(f"측정 텍스트 {i} "))
            lat.append((time.perf_counter() - t) * 1000)
            assert ok, "기록되지 않았습니다"
        results["text_copy_to_saved_ms_median"] = round(sorted(lat)[len(lat) // 2], 1)

        # 100건 연속(사이 80ms) CPU 시간
        before = process_stats(proc.pid)["cpu"]
        for i in range(100):
            set_text(f"대량 {i} " + "나" * 200)
            time.sleep(0.08)
        time.sleep(0.5)
        after = process_stats(proc.pid)
        results["cpu_ms_per_text_copy"] = round((after["cpu"] - before) * 1000 / 100, 2)
        results["working_set_after_100_mb"] = round(after["ws"] / 2**20, 2)

        st = client.request("status")
        results["items_after_limit"] = st["items"]  # 기본 50개 한도
        # 중복: 같은 내용을 다시 복사해도 개수 그대로, 맨 앞으로
        first = client.request("list", limit=50)["items"][-1]
        payload = client.request("get", id=first["id"])
        set_text(payload["data"])
        time.sleep(0.3)
        lst = client.request("list", limit=50)["items"]
        results["dedupe_moves_to_top"] = lst[0]["id"] == first["id"] and len(lst) == 50

        # 그림(1920×1080 비트맵) → PNG 저장
        t = time.perf_counter()
        set_clip(CF_DIB, dib(1920, 1080))
        ok = wait(lambda: client.request("list", limit=1)["items"][0]["kind"] == "image", 10)
        results["image_1080p_copy_to_saved_ms"] = round((time.perf_counter() - t) * 1000, 1)
        results["image_preview"] = client.request("list", limit=1)["items"][0]["preview"] if ok else None

        # 파일 목록
        set_clip(CF_HDROP, hdrop([r"C:\\업무\\보고서.hwpx", r"C:\\업무\\붙임1.pdf"]))
        wait(lambda: client.request("list", limit=1)["items"][0]["kind"] == "files")
        results["files_preview"] = client.request("list", limit=1)["items"][0]["preview"]

        # 복원: 오래된 텍스트를 클립보드로(다시 기록되지 않아야 함)
        target = next(i for i in client.request("list", limit=50)["items"] if i["kind"] == "text")
        count_before = client.request("status")["items"]
        client.request("restore", id=target["id"])
        restored = wait(lambda: (get_text() or "").startswith(target["preview"][:10]))
        time.sleep(0.3)
        results["restore_ok"] = bool(restored)
        results["restore_not_recorded_again"] = client.request("status")["items"] == count_before
        results["restored_item_on_top"] = client.request("list", limit=1)["items"][0]["id"] == target["id"]

        # 일시정지 중에는 기록하지 않음
        client.request("pause")
        time.sleep(0.2)
        set_text("일시정지 중 복사")
        time.sleep(0.3)
        results["pause_skips"] = not client.request("list", limit=1)["items"][0]["preview"].startswith("일시정지")
        client.request("resume")
        time.sleep(0.2)

        # DB에 평문이 없는지
        raw = (data / "clip.db").read_bytes() + ((data / "clip.db-wal").read_bytes()
                                                 if (data / "clip.db-wal").exists() else b"")
        results["db_has_no_plaintext"] = "측정 텍스트".encode("utf-8") not in raw and \
            "측정 텍스트".encode("utf-16-le") not in raw
        results["db_bytes"] = (data / "clip.db").stat().st_size
    finally:
        try:
            client.request("quit")
        except Exception:
            pass
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
        if original is not None:
            set_text(original)
        shutil.rmtree(data, ignore_errors=True)
    results["quit_clean"] = proc.returncode == 0
    print(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
