#!/usr/bin/env python3
"""시험 전용 KAgent 창을 메시지와 격리 저장소 상태로 판정한다."""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import sqlite3
import subprocess
import tempfile
import time
import unittest
from ctypes import wintypes
from pathlib import Path


user32 = ctypes.WinDLL("user32", use_last_error=True) if os.name == "nt" else None
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True) if os.name == "nt" else None
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008
WM_NCLBUTTONDOWN = 0x00A1
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_MOUSEMOVE = 0x0200
WM_KEYDOWN = 0x0100
VK_ESCAPE = 0x1B
WM_SHOW = 0x8004


class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def require_test_pid(hwnd: int, test_pid: int) -> None:
    """어떤 메시지를 보내기 전에도 대상 HWND의 소유 PID를 확인한다."""
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not hwnd or pid.value != test_pid:
        raise RuntimeError(f"시험 PID 불일치: hwnd={hwnd}, owner={pid.value}, test={test_pid}")


def send_test_message(hwnd: int, test_pid: int, message: int, wparam: int = 0, lparam: int = 0) -> None:
    require_test_pid(hwnd, test_pid)
    if not user32.PostMessageW(hwnd, message, wparam, lparam):
        raise ctypes.WinError(ctypes.get_last_error())


def enum_windows():
    found = []
    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visit(hwnd, _):
        title = ctypes.create_unicode_buffer(512)
        cls = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title, len(title))
        user32.GetClassNameW(hwnd, cls, len(cls))
        found.append((int(hwnd), title.value, cls.value, bool(user32.IsWindowVisible(hwnd))))
        return True
    user32.EnumWindows(visit, 0)
    return found


def window_pid(hwnd: int) -> int:
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def wait_popup(pid: int, timeout: float = 12) -> int:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        for hwnd, title, cls, visible in enum_windows():
            if visible and window_pid(hwnd) == pid and title == "몽땅클립보드" and cls == "HwpAutoDocFit.KAgentPopup":
                require_test_pid(hwnd, pid)
                return hwnd
        time.sleep(.1)
    raise RuntimeError("시험 팝업 창을 찾지 못했습니다")


def client(hwnd: int, pid: int):
    require_test_pid(hwnd, pid)
    rc = RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rc)):
        raise ctypes.WinError(ctypes.get_last_error())
    origin = POINT(0, 0)
    if not user32.ClientToScreen(hwnd, ctypes.byref(origin)):
        raise ctypes.WinError(ctypes.get_last_error())
    return rc.right, rc.bottom, origin.x, origin.y


def click_client(hwnd: int, pid: int, x: int, y: int, right: bool = False):
    lp = ((int(y) & 0xFFFF) << 16) | (int(x) & 0xFFFF)
    send_test_message(hwnd, pid, WM_MOUSEMOVE, 0, lp)
    send_test_message(hwnd, pid, WM_RBUTTONUP if right else WM_LBUTTONUP, 0, lp)
    time.sleep(.25)


def wait_for(predicate, timeout: float = 4) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(.08)
    return bool(predicate())


def record(results, name, verdict, detail):
    results.append({"항목": name, "판정": verdict, "근거": detail})


def run_item(exe: Path, name: str, action):
    root = Path(tempfile.mkdtemp(prefix="kagent-v229-window-"))
    env = os.environ.copy()
    env["KAGENT_TEST_ROOT"] = str(root)
    proc = subprocess.Popen([str(exe), "--test-window"], env=env, cwd=str(exe.parent),
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    try:
        hwnd = wait_popup(proc.pid)
        require_test_pid(hwnd, proc.pid)
        action(proc, root, hwnd)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)


def test_pid_guard():
    """현재 PID가 소유한 숨김 HWND에 다른 PID를 지정하면 전송 전에 거부한다."""
    hwnd = int(user32.CreateWindowExW(0, "STATIC", "pid-guard-test", 0, 0, 0, 1, 1,
                                      None, None, kernel32.GetModuleHandleW(None), None))
    if not hwnd:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        send_test_message(hwnd, os.getpid() + 1, WM_MOUSEMOVE)
    except RuntimeError:
        user32.DestroyWindow(hwnd)
        return
    user32.DestroyWindow(hwnd)
    raise AssertionError("PID가 다른 창으로 메시지가 전달될 수 있음")


def scenarios():
    def initial(p, root, h):
        w, height, _, _ = client(h, p.pid)
        s = json.loads((root / "settings.json").read_text(encoding="utf-8"))
        dbpath = root / "clip.db"
        with sqlite3.connect(dbpath) as db:
            count = db.execute("SELECT count(*) FROM items").fetchone()[0]
        top = bool(user32.GetWindowLongPtrW(h, GWL_EXSTYLE) & WS_EX_TOPMOST)
        ok = p.poll() is None and w > 0 and height > 0 and top and s.get("always_on_top") is True and count > 0
        record(results, "초기 창·격리 저장소", "합격" if ok else "불합격",
               {"client_rect": [w, height], "WS_EX_TOPMOST": top, "settings": s, "db": str(dbpath), "items": count})

    def collapse(p, root, h):
        dpi = user32.GetDpiForWindow(h) or 96
        w, _, _, _ = client(h, p.pid)
        x = w - (30 + 76 + 54 + 54 + 17) * dpi // 96
        click_client(h, p.pid, x, 15 * dpi // 96)
        _, height, _, _ = client(h, p.pid)
        s = json.loads((root / "settings.json").read_text(encoding="utf-8"))
        ok = height <= 40 * dpi // 96 + 5 and s.get("popup_collapsed") is True
        record(results, "접기", "합격" if ok else "불합격", {"client_height": height, "popup_collapsed": s.get("popup_collapsed")})

    def expand(p, root, h):
        dpi = user32.GetDpiForWindow(h) or 96
        before = client(h, p.pid)[1]
        w = client(h, p.pid)[0]
        # 접기 경계는 폭 기준 우측 30+76+54+54+34 DIP, 내부 클릭점은 그 구간 중앙.
        right_edge_offset = (30 + 76 + 54 + 54) * dpi // 96
        collapse_width = 34 * dpi // 96
        x = w - right_edge_offset - collapse_width // 2
        click_client(h, p.pid, x, 15 * dpi // 96)
        after = client(h, p.pid)[1]
        s = json.loads((root / "settings.json").read_text(encoding="utf-8"))
        ok = after > before + 100 * dpi // 96 and s.get("popup_collapsed") is False
        record(results, "펼치기", "합격" if ok else "불합격", {"접힘/펼침 높이": [before, after], "popup_collapsed": s.get("popup_collapsed")})

    def pin(p, root, h):
        dpi = user32.GetDpiForWindow(h) or 96
        w = client(h, p.pid)[0]
        # 클라이언트 폭은 DPI 반영 픽셀, 버튼 치수는 DIP이다.
        # Pin은 닫기 버튼 바로 왼쪽에 있다.
        click_client(h, p.pid, w - (30 + 76 // 2) * dpi // 96, 15 * dpi // 96)
        wait_for(lambda: not (user32.GetWindowLongPtrW(h, GWL_EXSTYLE) & WS_EX_TOPMOST), 1)
        top = bool(user32.GetWindowLongPtrW(h, GWL_EXSTYLE) & WS_EX_TOPMOST)
        s = json.loads((root / "settings.json").read_text(encoding="utf-8"))
        ok = not top and s.get("always_on_top") is False and s.get("sticky_popup") is True
        record(results, "항상 위 토글", "합격" if ok else "수동 확인 필요",
               {"WS_EX_TOPMOST": top, "always_on_top": s.get("always_on_top"), "sticky_popup": s.get("sticky_popup")})

    def database(p, root, h):
        dpi = user32.GetDpiForWindow(h) or 96
        w, _, _, _ = client(h, p.pid)
        dbpath = root / "clip.db"
        with sqlite3.connect(dbpath) as db:
            item = db.execute("SELECT id,pinned FROM items ORDER BY used DESC LIMIT 1").fetchone()
        y = (30 + 15) * dpi // 96
        click_client(h, p.pid, w - 42 * dpi // 96, y)
        with sqlite3.connect(dbpath) as db:
            value = db.execute("SELECT pinned FROM items WHERE id=?", (item[0],)).fetchone()
        ok = bool(value and value[0] == 1)
        record(results, "줄 고정(DB)", "합격" if ok else "불합격", {"item_id": item[0], "pinned": value[0] if value else None})

    def menu(p, root, h):
        dpi = user32.GetDpiForWindow(h) or 96
        before = {x[0] for x in enum_windows()}
        click_client(h, p.pid, 100 * dpi // 96, 45 * dpi // 96, right=True)
        # TrackPopupMenu는 동기적으로 실행되며 시험 프로세스의 UI 스레드를 막는다.
        seen = wait_for(lambda: any(hwnd not in before and cls == "#32768" and visible and window_pid(hwnd) == p.pid
                                    for hwnd, _, cls, visible in enum_windows()), 2)
        record(results, "오른쪽 클릭 메뉴", "합격" if seen else "불합격", {"시험 PID 메뉴 표시": seen})
        # 메뉴 닫기는 오버레이처럼 전역 키 입력이 필요하므로 수동 확인 대상으로 남긴다.
        record(results, "메뉴 닫기", "수동 확인 필요", "메뉴 활성 상태에서 Esc 처리는 전역 키 입력 금지로 자동 검증할 수 없음")

    def manual_resize(p, root, h):
        record(results, "비클라이언트 크기 조절·저장", "수동 확인 필요", "WM_NCLBUTTONDOWN만으로 시스템 크기 조절 루프의 마우스 이동을 재현할 수 없음")

    def manual_capture(p, root, h):
        record(results, "캡처 오버레이 표시·종료", "수동 확인 필요", "오버레이 HWND는 메시지 관찰만으로 표시 내용을 판정할 수 없고 Esc도 전역 입력 금지")

    return [("초기 창·격리 저장소", initial), ("접기", collapse), ("펼치기", expand),
            ("항상 위 토글", pin), ("줄 고정(DB)", database), ("오른쪽 클릭 메뉴", menu),
            ("비클라이언트 크기 조절·저장", manual_resize), ("캡처 오버레이 표시·종료", manual_capture)]


class PidGuardTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Win32 창 PID 검사")
    def test_rejects_window_owned_by_different_pid_before_post(self):
        test_pid_guard()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=Path(__file__).resolve().parents[1] / "kagent" / "target" / "debug" / "kagent.exe")
    parser.add_argument("--test-window", action="store_true", help="KAGENT_TEST_ROOT 격리 폴더에서 시험 창 실행")
    args = parser.parse_args()
    if not args.test_window:
        parser.error("안전상 --test-window 옵션이 필요합니다")
    if os.name != "nt":
        parser.error("이 스크립트는 Windows 전용입니다")
    if not args.exe.is_file():
        parser.error(f"시험 실행 파일이 없습니다: {args.exe}")
    if not user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2):
        raise ctypes.WinError(ctypes.get_last_error())
    global results
    results = []
    # 접기와 펼치기는 같은 시험 창에서 순서대로 실행해야 한다.
    # 처음부터 펼쳐진 창에 펼치기 토글을 보내면 오히려 접히는 회귀를 잡는다.
    actions = scenarios()
    collapse_index = next(i for i, (name, _) in enumerate(actions) if name == "접기")
    expand_index = next(i for i, (name, _) in enumerate(actions) if name == "펼치기")
    pin_index = next(i for i, (name, _) in enumerate(actions) if name == "항상 위 토글")
    collapse_action, expand_action, pin_action = actions[collapse_index][1], actions[expand_index][1], actions[pin_index][1]
    for index in sorted((collapse_index, expand_index, pin_index), reverse=True):
        del actions[index]
    for name, action in actions:
        try:
            run_item(args.exe.resolve(), name, action)
        except Exception as exc:
            record(results, name, "불합격", f"{type(exc).__name__}: {exc}")
    try:
        def collapse_then_expand(proc, root, hwnd):
            collapse_action(proc, root, hwnd)
            expand_action(proc, root, hwnd)
            pin_action(proc, root, hwnd)
        run_item(args.exe.resolve(), "접기 후 펼치기 및 항상 위 토글", collapse_then_expand)
    except Exception as exc:
        record(results, "접기 후 펼치기 및 항상 위 토글", "불합격", f"{type(exc).__name__}: {exc}")
    payload = {"결과": results,
               "총괄": "불합격" if any(r["판정"] == "불합격" for r in results) else
                      ("수동 확인 필요" if any(r["판정"] == "수동 확인 필요" for r in results) else "합격")}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["총괄"] == "불합격" else 0


if __name__ == "__main__":
    raise SystemExit(main())
