"""K에이전트 폴더 감시 실측(Windows PC): 타임머신 색인(앱 스키마 호환)·스크린샷 폴더·서식(HTML) 보존·팝업 찾기.

사용: .venv\\Scripts\\python.exe scripts\\kagent_watch_check_pc.py kagent\\target\\release\\kagent.exe [화면저장폴더]
임시 폴더만 쓴다(실제 문서·스크린샷 폴더는 건드리지 않음). 시험 중 클립보드가 바뀌며 끝나면 원래 글로 돌려놓는다.
"""
from __future__ import annotations

import ctypes
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import kagent_benchmark_pc as b  # noqa: E402
from docfit_app.kagent_client import KAgentClient  # noqa: E402
from docfit_core.timemachine import Store  # noqa: E402


def tiny_png():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"\x00\xff\x00\x00"
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def html_clip(fragment):
    head = "Version:0.9\r\nStartHTML:{:010d}\r\nEndHTML:{:010d}\r\nStartFragment:{:010d}\r\nEndFragment:{:010d}\r\n"
    body = f"<html><body><!--StartFragment-->{fragment}<!--EndFragment--></body></html>"
    pre = len(head.format(0, 0, 0, 0))
    start_frag = pre + body.index(fragment)
    text = head.format(pre, pre + len(body.encode()), start_frag, start_frag + len(fragment.encode())) + body
    return text.encode("utf-8") + b"\0"


def set_text_and_html(text, fragment):
    fmt = ctypes.windll.user32.RegisterClipboardFormatW("HTML Format")
    b.open_clip()
    try:
        ctypes.windll.user32.EmptyClipboard()
        for f, data in ((b.CF_UNICODETEXT, (text + "\0").encode("utf-16-le")), (fmt, html_clip(fragment))):
            h = b.k32.GlobalAlloc(0x0002, len(data))
            p = b.k32.GlobalLock(h)
            ctypes.memmove(p, data, len(data))
            b.k32.GlobalUnlock(h)
            b.u32.SetClipboardData(f, h)
    finally:
        b.u32.CloseClipboard()


def has_html():
    fmt = ctypes.windll.user32.RegisterClipboardFormatW("HTML Format")
    return bool(ctypes.windll.user32.IsClipboardFormatAvailable(fmt))


def main():
    exe = Path(sys.argv[1]).resolve()
    shot_out = sys.argv[2] if len(sys.argv) > 2 else None
    base = Path(tempfile.mkdtemp(prefix="kagent-watch-"))
    data, shots, docs = base / "data", base / "shots", base / "문서"
    for d in (data, shots, docs / "하위"):
        d.mkdir(parents=True)
    (docs / "기존 보고서.hwpx").write_bytes(b"x")
    env = dict(os.environ, KAGENT_DATA=str(data), KAGENT_SCREENSHOTS=str(shots))
    os.environ["KAGENT_DATA"] = str(data)
    original = b.get_text()
    client = KAgentClient(data)
    proc = subprocess.Popen([str(exe)], env=env)
    out = {}
    try:
        assert b.wait(client.status_file, 10)
        # 1) 타임머신: 조사 폴더 지정 → 첫 색인 → 새 파일·삭제가 실시간 반영(앱 Store로 읽어 스키마 호환 확인)
        client.request("settings_set", settings={"timeline_roots": [str(docs)]})
        db = data / "timeline.db"
        assert b.wait(lambda: db.exists() and Store(db).stats()["files"] == 1, 10), "첫 색인 실패"
        t = time.perf_counter()
        (docs / "하위" / "새 계획.pdf").write_bytes(b"pdf")
        ok = b.wait(lambda: Store(db).stats()["files"] == 2, 5)
        out["timeline_new_file_ms"] = round((time.perf_counter() - t) * 1000) if ok else None
        rows = Store(db).range(0, 2e10)
        out["timeline_rows"] = sorted(r["name"] for r in rows)
        (docs / "~$임시.docx").write_bytes(b"x")
        shutil.rmtree(docs / "하위")
        out["timeline_after_delete"] = b.wait(lambda: Store(db).stats()["files"] == 1, 5) is not None
        out["timeline_temp_ignored"] = all(not r["name"].startswith("~$") for r in Store(db).range(0, 2e10))

        # 2) 스크린샷 폴더: 새 PNG → 그림 항목(캡처)
        time.sleep(3.2)  # 직전 클립보드 그림과 겹침 방지 창(3초) 밖
        (shots / "스크린샷 2026-10-31.png").write_bytes(tiny_png())
        ok = b.wait(lambda: client.request("list", limit=1)["items"][:1]
                    and client.request("list", limit=1)["items"][0]["preview"].startswith("캡처"), 5)
        out["screenshot_recorded"] = bool(ok)

        # 3) 서식 보존: 글+HTML 복사 → 다른 것 복사 → 되돌리면 HTML도 다시 올라옴
        set_text_and_html("굵은 제목", "<b>굵은 제목</b>")
        b.wait(lambda: client.request("list", limit=1)["items"][0]["preview"] == "굵은 제목", 5)
        item = client.request("list", limit=1)["items"][0]
        out["html_kept"] = client.request("get", id=item["id"]).get("formats") == ["HTML Format"]
        b.set_text("다른 글")
        time.sleep(0.3)
        client.request("restore", id=item["id"])
        out["html_restored"] = bool(b.wait(lambda: has_html() and b.get_text() == "굵은 제목", 3))

        # 4) 팝업 찾기: 열고 한글 글자 입력(유니코드 입력) → 화면 저장
        if shot_out:
            for t2 in ["회의록 초안", "예산 요구서", "회의실 예약"]:
                b.set_text(t2)
                time.sleep(0.2)
            ctypes.windll.user32.SetCursorPos(300, 300)
            subprocess.run([str(exe)], env=env)
            time.sleep(0.5)
            send_unicode("회의")
            time.sleep(0.4)
            from PIL import ImageGrab
            ImageGrab.grab(bbox=(280, 280, 900, 640)).save(shot_out)
            send_vk(0x1B)
            send_vk(0x1B)
        st = b.process_stats(proc.pid)
        time.sleep(5)
        st2 = b.process_stats(proc.pid)
        out["idle_cpu_percent_5s_with_watchers"] = round((st2["cpu"] - st["cpu"]) / 5 * 100, 4)
        out["private_mb"] = round(st2["private"] / 2**20, 2)
        out["status"] = {k: v for k, v in client.status_file().items() if k.startswith(("timeline", "screen"))}
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
            b.set_text(original)
        shutil.rmtree(base, ignore_errors=True)
    print(json.dumps(out, ensure_ascii=False, indent=1))


class KI(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.c_size_t)]


class INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", KI), ("pad", ctypes.c_byte * 32)]
    _fields_ = [("type", ctypes.c_ulong), ("u", _U)]


def _send(items):
    arr = (INPUT * len(items))(*items)
    ctypes.windll.user32.SendInput(len(items), arr, ctypes.sizeof(INPUT))


def send_unicode(text):
    items = []
    for ch in text:
        for flags in (0x0004, 0x0004 | 0x0002):  # KEYEVENTF_UNICODE (+KEYUP)
            i = INPUT(type=1)
            i.u.ki = KI(0, ord(ch), flags, 0, 0)
            items.append(i)
    _send(items)


def send_vk(vk):
    down, up = INPUT(type=1), INPUT(type=1)
    down.u.ki = KI(vk, 0, 0, 0, 0)
    up.u.ki = KI(vk, 0, 0x0002, 0, 0)
    _send([down, up])


if __name__ == "__main__":
    main()
