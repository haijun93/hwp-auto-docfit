"""Tk 기반 문서 처리 기능을 반응형 WebView 화면에 연결한다."""

from __future__ import annotations

import importlib.util
import threading
from concurrent.futures import Future, TimeoutError
from pathlib import Path


class DesktopWebBridge:
    """WebView에서 호출하는 API. 모든 Tk 접근은 Tk 이벤트 루프에 위임한다."""

    def __init__(self, gui):
        self.gui = gui
        self.window = None
        self.tk_stopped = None

    def _tk(self, callback, timeout=120):
        result = Future()

        def run():
            if result.cancelled():
                return
            try:
                result.set_result(callback())
            except BaseException as exc:
                result.set_exception(exc)

        try:
            self.gui.root.after(0, run)
        except Exception as exc:
            raise RuntimeError("앱이 종료 중입니다.") from exc
        try:
            return result.result(timeout=timeout)
        except TimeoutError as exc:
            raise RuntimeError("앱 응답 시간이 초과되었습니다.") from exc

    def get_state(self):
        def snapshot():
            gui = self.gui
            return {
                "files": [
                    {"name": Path(path).name, "path": path}
                    for path in gui.files
                ],
                "count": len(gui.files),
                "mode": gui.selected_mode.get(),
                "status": gui.status_var.get(),
                "running": bool(gui.running),
                "range": {
                    "enabled": gui.range_mode_var.get() == "pages",
                    "start": gui.range_start_var.get(),
                    "end": gui.range_end_var.get(),
                },
                "progress": {
                    "steps": list(STAGE_ORDER),
                    "active": getattr(gui.stage_board, "active", None),
                    "visited": list(getattr(gui.stage_board, "visited", set())),
                    "outcome": getattr(gui.stage_board, "outcome", None),
                    "detail": getattr(gui.stage_board, "detail", ""),
                },
                "results": [
                    {"name": Path(item.get("結果", "")).name, "path": item.get("결과", "")}
                    for item in getattr(gui, "_결과목록", [])
                ],
                "default_saved": bool(gui._세부작업_기본저장.get(gui.selected_mode.get(), True)),
                "can_start": bool(gui.files) and not gui.running,
                "version": APP_VERSION,
            }

        return self._tk(snapshot)

    def add_files(self):
        self._tk(self.gui.파일선택)
        return self.get_state()

    def add_folder(self):
        self._tk(self.gui._폴더선택)
        return self.get_state()

    def add_paths(self, paths):
        if not isinstance(paths, (list, tuple)):
            return self.get_state()

        def add():
            if self.gui.running:
                return
            added = 0
            for value in paths:
                path = str(value or "").strip()
                if not path:
                    continue
                try:
                    if Path(path).is_dir():
                        added += self.gui.폴더추가(path)
                    elif self.gui.파일추가(path):
                        added += 1
                except (OSError, ValueError):
                    continue
            if added:
                self.gui.status_var.set(f"{added}개 추가 · 총 {len(self.gui.files)}개 문서")
                self.gui.로그표시(f"{added}개 문서 추가")

        self._tk(add)
        return self.get_state()

    def remove_file(self, index):
        def remove():
            try:
                index_value = int(index)
            except (TypeError, ValueError):
                return
            if not self.gui.running and 0 <= index_value < len(self.gui.files):
                self.gui.file_list.selection_clear(0, "end")
                self.gui.file_list.selection_set(index_value)
                self.gui._선택삭제()

        self._tk(remove)
        return self.get_state()

    def clear_files(self):
        self._tk(self.gui.목록지우기)
        return self.get_state()

    def set_mode(self, mode):
        if mode not in {"spacing", "unify", "format", "all"}:
            raise ValueError("지원하지 않는 작업 방식입니다.")

        def select():
            if not self.gui.running:
                self.gui.selected_mode.set(mode)
                self.gui._모드_선택됨()

        self._tk(select)
        return self.get_state()

    def set_range(self, enabled, start="1", end="1"):
        def update():
            if self.gui.running:
                return
            self.gui.range_mode_var.set("pages" if enabled else "all")
            self.gui.page_range_var.set(bool(enabled))
            self.gui.range_start_var.set(str(start or "1"))
            self.gui.range_end_var.set(str(end or start or "1"))
            self.gui._범위_끝직접설정 = bool(enabled)
            self.gui._범위_상태_갱신()

        self._tk(update)
        return self.get_state()

    def start(self, mode, range_enabled=False, start="1", end="1"):
        if mode not in {"spacing", "unify", "format", "all"}:
            raise ValueError("지원하지 않는 작업 방식입니다.")

        def begin():
            if self.gui.running:
                return
            self.gui.selected_mode.set(mode)
            self.gui.range_mode_var.set("pages" if range_enabled else "all")
            self.gui.page_range_var.set(bool(range_enabled))
            self.gui.range_start_var.set(str(start or "1"))
            self.gui.range_end_var.set(str(end or start or "1"))
            self.gui._범위_끝직접설정 = bool(range_enabled)
            self.gui._범위_상태_갱신()
            self.gui.작업시작(mode)

        self._tk(begin)
        return self.get_state()

    def stop(self):
        self._tk(self.gui.작업중단)
        return self.get_state()

    def open_settings(self):
        self._tk(self.gui.설정창_열기)
        return True

    def text_input(self):
        self._tk(self.gui._텍스트로_문서추가_열기)
        return self.get_state()

    def open_stages(self):
        self._tk(lambda: self.gui._세부작업_열기(
            self.gui.selected_mode.get(), self.gui._세부작업_기본저장.get(self.gui.selected_mode.get(), True)
        ))
        return True

    def open_log(self):
        self._tk(lambda: (self.gui.log_window.deiconify(), self.gui.log_window.lift()))
        return True

    def open_results(self):
        self._tk(self.gui._결과파일_열기)
        return True

    def next_job(self):
        def reset():
            if self.gui.running:
                return
            self.gui.목록지우기()
            self.gui.selected_mode.set("spacing")
            self.gui._모드_선택됨()

        self._tk(reset)
        return self.get_state()

    def run_tool(self, name):
        commands = {
            "review": self.gui._문서검토_열기,
            "proofread": self.gui._공공언어_검토,
            "paste": self.gui._텍스트로_문서추가_열기,
            "polish": self.gui._붙여넣기_정리_열기,
            "outline": self.gui._아웃라이너_열기,
            "writing": self.gui._작성도우미_열기,
            "markdown": self.gui.Markdown_내보내기,
            "advanced": self.gui.고급문서도구_열기,
        }
        command = commands.get(name)
        if command is None:
            raise ValueError("지원하지 않는 도구입니다.")
        self._tk(command)
        return True

    def request_close(self):
        """OS 창 닫기 전에 기존 앱의 종료 확인·작업 중단 절차를 수행한다."""
        if self.tk_stopped is not None and self.tk_stopped.is_set():
            return True
        def close():
            try:
                if not self.gui.root.winfo_exists():
                    return True
            except Exception:
                return True
            self.gui.종료()
            try:
                return not bool(self.gui.root.winfo_exists())
            except Exception:
                return True

        return self._tk(close)


def _resource_path():
    import sys

    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "desktop_web" / "index.html"


def run_webview(gui):
    """기존 Tk 백엔드를 숨겨 실행하고 WebView2를 주 UI로 표시한다."""
    if importlib.util.find_spec("webview") is None:
        return False

    import webview

    bridge = DesktopWebBridge(gui)
    page = _resource_path()
    if not page.is_file():
        raise FileNotFoundError(f"웹 UI 파일을 찾을 수 없습니다: {page}")

    screen_width, screen_height = bridge._tk(
        lambda: (gui.root.winfo_screenwidth(), gui.root.winfo_screenheight())
    )
    width = min(1040, max(420, screen_width - 40))
    # Reserve space for the title bar and taskbar; center the window so it
    # remains fully reachable even when Tk reports a logical (DPI-scaled) size.
    height = min(800, max(400, screen_height - 220))
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)

    window = webview.create_window(
        f"{APP_NAME} · v{APP_VERSION}",
        url=page.as_uri(),
        js_api=bridge,
        width=width,
        height=height,
        x=x,
        y=y,
        min_size=(min(520, width), min(440, height)),
        text_select=True,
    )
    bridge.window = window
    tk_stopped = threading.Event()
    bridge.tk_stopped = tk_stopped
    window.events.closing += bridge.request_close
    original_destroy = gui.root.destroy

    def tracked_destroy():
        tk_stopped.set()
        original_destroy()

    gui.root.destroy = tracked_destroy

    def bind_file_drop(web_window):
        try:
            from webview.dom import DOMEventHandler

            def dropped(event):
                transfer = event.get("domTransfer") or event.get("dataTransfer") or {}
                files = transfer.get("files", [])
                paths = [item.get("pywebviewFullPath") for item in files]
                bridge.add_paths([path for path in paths if path])

            web_window.dom.document.events.drop += DOMEventHandler(
                dropped, prevent_default=True, stop_propagation=True
            )
        except Exception:
            # 드롭 이벤트를 지원하지 않는 환경에서도 파일 선택 버튼은 사용 가능하다.
            return

    def stop_webview_when_app_exits(web_window):
        tk_stopped.wait()
        try:
            web_window.destroy()
        except Exception:
            pass

    window.events.loaded += lambda *_args: bind_file_drop(window)

    def initialize_webview(web_window):
        threading.Thread(
            target=stop_webview_when_app_exits,
            args=(web_window,),
            name="webview-shutdown-watch",
            daemon=True,
        ).start()

    webview.start(initialize_webview, args=[window], gui="edgechromium")
    return True


# Application values are injected by the entry point after import.
APP_VERSION = ""
APP_NAME = ""
STAGE_ORDER = ("열기", "서식", "자간", "줄 병합", "페이지 배치", "저장")
