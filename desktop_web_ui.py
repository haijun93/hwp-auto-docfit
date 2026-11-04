"""Tk 湲곕컲 臾몄꽌 泥섎━ 湲곕뒫??諛섏쓳??WebView ?붾㈃???곌껐?쒕떎."""

from __future__ import annotations

import base64
import importlib.util
import logging
import os
import subprocess
import shutil
import threading
import time
import tempfile
import uuid
import re
from concurrent.futures import Future, TimeoutError
from pathlib import Path
from types import SimpleNamespace

from docfit_core.progress_guide import guide_state, progress_view
from docfit_core.stage_selection import STAGE_EXAMPLES, default_choice, stages_for_mode
from docfit_app.api_contract import response
from docfit_app.app_state import STAGE_ORDER
from docfit_core.file_conversion import IMAGE_INPUT_EXTENSIONS
from docfit_core.file_conversion import CONVERSION_INPUTS as SUPPORTED_INPUT_EXTENSIONS, CONVERSION_OUTPUTS
from docfit_core.file_conversion import HANCOM_PDF_DIRECT, IMAGE_FORMATS, SAME_FORMAT_SUFFIXES

_TABLE_UNITS_COM_LOCK = threading.Lock()

# ?붾㈃?먯꽌 諛붾줈 耳쒓퀬 ?꾨뒗 怨듯넻 ?ㅼ젙(?대쫫 ???깆쓽 Tk 蹂???띿꽦). 媛믪쓣 諛붽씀硫??깆씠 ?ㅼ젙 ?뚯씪????ν븳??
def _format_coverage(analysis):
    try:
        from docfit_core.format_elements import coverage
        return coverage(analysis)
    except Exception:
        return None


QUICK_OPTIONS = {
    "autoclose": "autoclose_var",
    "unify_result_window": "unify_result_window_var",
    "verify": "verify_var",
    "integrity_report_file": "integrity_report_file_var",
    "final_review_file": "final_review_file_var",
    "log_file": "log_file_var",
    "check_updates": "check_updates_on_start_var",
    "developer_mode": "developer_mode_var",
    "always_on_top": "always_on_top_var",
}


def _profile_trace(message):
    """?쒖떇 ?좏깮 ?묐룞 湲곕줉: DOCFIT_PROFILE_TRACE???뚯씪 寃쎈줈媛 ?덉쓣 ?뚮쭔 ?④릿???ъ슜???쒗뿕??."""
    target = os.environ.get("DOCFIT_PROFILE_TRACE")
    if not target:
        return
    try:
        from datetime import datetime
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(f"{datetime.now():%H:%M:%S} {message}\n")
    except OSError:
        pass


class PendingGui:
    """Tk ?붾㈃??留뚮뱶???숈븞 癒쇱? ??李쎌쓣 ?꾩슦湲??꾪븳 ?由?媛앹껜(2.0.5 ?쒖옉 ?띾룄).

    ?④릿 Tk ?붾㈃(HwpAutoDocFitGUI)??留뚮뱶????1~2珥덇? 嫄몃젮 ??李쎌씠 洹몃쭔????쾶 ?대떎. ??李쎌? 諛붾줈 留뚮뱾怨?
    ?붾㈃ ?붿껌(釉뚮━吏 ?몄텧)? Tk 以鍮꾧? ?앸궇 ?뚭퉴吏 湲곕떎?몃떎媛 ?ㅼ젣 ?붾㈃?쇰줈 ?섍릿??"""

    def __init__(self, ready: threading.Event, holder: dict, timeout: float = 30.0):
        object.__setattr__(self, "_ready", ready)
        object.__setattr__(self, "_holder", holder)
        object.__setattr__(self, "_timeout", timeout)

    def resolve(self):
        if not self._ready.wait(self._timeout):
            raise RuntimeError("???명꽣?섏씠?ㅻ? ?쒖옉?섏? 紐삵뻽?듬땲??")
        if "?ㅻ쪟" in self._holder:
            raise RuntimeError("???명꽣?섏씠?ㅻ? ?쒖옉?섏? 紐삵뻽?듬땲??") from self._holder["?ㅻ쪟"]
        return self._holder["gui"]

    def __getattr__(self, name):
        return getattr(self.resolve(), name)

    def __setattr__(self, name, value):
        setattr(self.resolve(), name, value)


def _real_gui(gui):
    return gui.resolve() if isinstance(gui, PendingGui) else gui


class DesktopWebBridge:
    """WebView?먯꽌 ?몄텧?섎뒗 API. 紐⑤뱺 Tk ?묎렐? Tk ?대깽??猷⑦봽???꾩엫?쒕떎."""

    def __init__(self, gui):
        self.gui = gui
        from docfit_app.native_file_dialog_service import NativeFileDialogService
        self._file_dialogs = NativeFileDialogService()
        self.window = None
        self.sidebar_controller = None
        self.sidebar_active = False
        self.tk_stopped = None
        # ?ъ슜?먭? ??李쎌쓣 ?レ븘 醫낅즺?섎뒗 以묒씤吏. ?대븣??李쎌씠 ?ㅼ뒪濡??ロ엳誘濡?
        # 醫낅즺 媛먯떆 ?ㅻ젅?쒓? destroy()瑜??ㅼ떆 遺瑜대㈃ ???쒕떎(pywebview ?댁쨷 ?ロ옒 ?ㅻ쪟).
        self.user_closing = False
        # 李쎌뿉 ?뚯뼱 ?볦? ?뚯씪???대뵒???ｌ쓣吏: documents(?뺣━??臾몄꽌 紐⑸줉) ?먮뒗 format(?덉떆 ?쒖떇 蹂듭젣).
        # ?붾㈃??'?쒖떇 愿由? 李쎌씠 ?대젮 ?덈뒗 ?숈븞 format?대떎.
        self.drop_target = "documents"
        self._document_drop_revision = 0
        self._request_lock = threading.Lock()
        self._requests = set()
        self._closed = False
        self.conversion_target = "hwpx"
        self._conversion_prerequisites_checked = 0.0
        self._conversion_prerequisites_cache = None
        self._conversion_prerequisites_lock = threading.Lock()
        self._coverage_cache = {}
        self._close_lock = threading.Lock()
        self._close_protocol = False
        self._close_request = None
        self._close_timer = None
        self._library_bridge = None

    def _shutdown(self):
        """Tk 醫낅즺 ???湲걔룹떎??以??붿껌???몄텧?먮? 醫낅즺 ?ㅻ쪟濡??댁젣?쒕떎."""
        with self._close_lock:
            self._cancel_close_timer()
        manager = getattr(self.gui, '_job_manager', None)
        if manager is not None:
            threading.Thread(target=manager.shutdown, daemon=True).start()
        self._file_dialogs.close()
        self._cancel_pending_drop()
        with self._request_lock:
            self._closed = True
            if self.tk_stopped is not None:
                self.tk_stopped.set()
            for request in self._requests:
                if not request.done():
                    request.set_exception(RuntimeError("?깆씠 醫낅즺 以묒엯?덈떎."))
            self._requests.clear()

    def _ux(self):
        from docfit_core.app_state import AppState
        if not hasattr(self, "_ux_data"):
            self._ux_data = self.gui.state if isinstance(getattr(self.gui, "state", None), AppState) else AppState()
        return self._ux_data

    def _quick_option(self, name):
        variable = getattr(self.gui, QUICK_OPTIONS[name], None)
        return True if variable is None else bool(variable.get())

    def _cancel_pending_drop(self):
        self._ux().zero_click = {}

    def _update_document_hints(self):
        from docfit_core.doc_inspector import inspect_documents
        ux = self._ux()
        ux.doc_hints = inspect_documents(list(self.gui.files))
        if not self.gui.files:
            ux.user_overrode_mode = False
        elif not ux.user_overrode_mode and not self.gui.running:
            mode = ux.doc_hints["recommended_mode"]
            self._page_fit_card = False  # ?ㅻⅨ 移대뱶瑜?怨좊Ⅴ硫??섏씠吏 留욎땄 移대뱶 ?댁젣
            self.gui.selected_mode.set("format" if mode == "all" and not self._include_spacing() else mode)
            self._mode_selected()
            self.gui.status_var.set(ux.doc_hints["reason"])

    def _zero_click_snapshot(self):
        # 臾몄꽌 異붽???紐⑸줉 ?깅줉留??쒕떎. ?묒뾽? ?ъ슜?먭? 吏곸젒 ?쒖옉?쒕떎.
        self._cancel_pending_drop()
        return {"pending": False}

    def cancel_zero_click(self):
        self._tk(self._cancel_pending_drop)
        return self.get_state()

    def start_zero_click(self, token):
        # ?댁쟾 ?꾨윴?몄뿏?쒕굹 ????ㅼ젙?먯꽌 ??吏???ㅽ뻾 ?붿껌??臾댁떆?쒕떎.
        self._tk(self._cancel_pending_drop)
        return self.get_state()

    def set_profile_drop_bounds(self, bounds):
        import math
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 4 or any(
                isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in bounds):
            raise ValueError("?쒖떇 諛곗? ?곸뿭???щ컮瑜댁? ?딆뒿?덈떎.")
        self._profile_drop_bounds = tuple(bounds)
        if self.window is not None and hasattr(self.window, "run_js"):
            self.window.run_js(f"window.docfitProfileDropRect = {list(bounds)!r};")
        return True

    def quick_register_and_activate_profile(self, path):
        path = Path(str(path))
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in {".hwp", ".hwpx"}:
            return self._with_notice("HWP ?먮뒗 HWPX ?덉떆 ?뚯씪???볦븘 二쇱꽭??")
        def register():
            self._cancel_pending_drop()
            if self.gui.running or self._profile_state().analyzing_format:
                return "?묒뾽?대굹 ?쒖떇 遺꾩꽍???앸궃 ???ㅼ떆 ?볦븘 二쇱꽭??"
            name = re.sub(r"[_\s]+", " ", path.stem).strip()[:120] or "???쒖떇"
            parts = re.split(r"[_\s]+", path.stem, maxsplit=1)
            organization = (parts[0][:60] if len(parts) == 2 and parts[0].endswith(
                ("援?, "??, "援?, "泥?, "怨듭궗", "怨듬떒", "?곌뎄??)) else None)
            self._quick_watch = {"ids": set(self._profile_state().profiles), "name": name}
            self._quick_notice = {"id": uuid.uuid4().hex, "message": f"{name} 쨌 ?쒖떇 遺꾩꽍 以?}
            self.gui._quick_registration = True
            try:
                self.gui._?쒖떇_遺꾩꽍_?쒖옉(str(path.resolve()), ?대쫫臾산린=False, 湲곕낯?대쫫=name, 湲곌?=organization)
            except Exception:
                self.gui._quick_registration = False
                self._quick_watch = None
                raise
            return f"{name} 쨌 ?쒖떇 遺꾩꽍 ???먮룞?쇰줈 ?깅줉쨌?좏깮?⑸땲??"
        return self._with_notice(self._tk(register))

    def drop_format_file(self, path):
        return self.quick_register_and_activate_profile(path)

    def _tk(self, callback, timeout=120, front=False):
        result = Future()
        with self._request_lock:
            if self._closed or (self.tk_stopped is not None and self.tk_stopped.is_set()):
                raise RuntimeError("?깆씠 醫낅즺 以묒엯?덈떎.")
            self._requests.add(result)

        def complete(value=None, error=None):
            with self._request_lock:
                self._requests.discard(result)
                # 醫낅즺媛 癒쇱? ?몄텧?먮? ?댁젣?덉쑝硫?callback??寃곌낵瑜??ㅼ떆 ?곗? ?딅뒗??
                if not result.done():
                    if error is not None:
                        result.set_exception(error)
                    else:
                        result.set_result(value)

        def run():
            with self._request_lock:
                # ?쒓컙 珥덇낵쨌醫낅즺 ???먯뿉 ?⑥? callback? ?ㅽ뻾?섏? ?딅뒗??
                if result.done():
                    self._requests.discard(result)
                    return
                if not result.set_running_or_notify_cancel():
                    self._requests.discard(result)
                    return
            temporary_host = False
            if front:
                try:
                    if getattr(self.gui.root, "_docfit_hidden_backend", False):
                        self.gui.root.overrideredirect(True)
                        self.gui.root.attributes("-alpha", 0.0)
                        self.gui.root.attributes("-topmost", True)
                        self.gui.root.minsize(1, 1)
                        self.gui.root.geometry("1x1+0+0")
                        self.gui.root.deiconify()
                        temporary_host = True
                    # ?뚯씪 ?좏깮 ??湲곕낯 李쎌쓣 遺紐⑤줈 ?곕뒗 ??붿긽?먭? ???붾㈃ ?ㅼ뿉 ?⑥? ?딄쾶 ?쒕떎.
                    self.gui.root.lift()
                    self.gui.root.focus_force()
                except Exception:
                    pass
            try:
                complete(value=callback())
            except BaseException as exc:
                complete(error=exc)
            finally:
                if temporary_host:
                    try:
                        self.gui.root.withdraw()
                        self.gui.root.attributes("-topmost", False)
                        self.gui.root.attributes("-alpha", 1.0)
                        self.gui.root.overrideredirect(False)
                        self.gui.root.minsize(*self.gui.root._docfit_min_size)
                    except Exception:
                        pass

        try:
            callbacks = getattr(self.gui, "_bridge_callbacks", None)
            if callbacks is not None:
                callbacks.put(run)
            else:
                self.gui.root.after(0, run)
        except Exception as exc:
            complete(error=RuntimeError("?깆씠 醫낅즺 以묒엯?덈떎."))
            raise RuntimeError("?깆씠 醫낅즺 以묒엯?덈떎.") from exc
        try:
            return result.result(timeout=timeout)
        except TimeoutError as exc:
            # callback ?먯껜媛 ??TimeoutError瑜????묐떟 ?쒓컙 珥덇낵濡?諛붽씀吏 ?딅뒗??
            with self._request_lock:
                if result.done():
                    return result.result()
                cancelled = result.cancel()
                if cancelled:
                    self._requests.discard(result)
            if not cancelled:
                raise RuntimeError("紐낅졊???대? ?ㅽ뻾 以묒엯?덈떎. 以묐났 ?ㅽ뻾?섏? 留먭퀬 吏꾪뻾 ?곹깭瑜??뺤씤??二쇱꽭??") from exc
            raise RuntimeError("???묐떟 ?쒓컙??珥덇낵?섏뿀?듬땲??") from exc

    def _stages(self, mode):
        choices = self.gui.stage_choices.get(mode, {})
        return [
            {
                "key": key,
                "label": label,
                "example": STAGE_EXAMPLES.get(key, ""),
                "on": bool(choices.get(key, default_choice(key, mode))),
                "default": default_choice(key, mode),
            }
            for key, label in stages_for_mode(mode)
        ]

    def _profile_state(self):
        from docfit_core.app_state import AppState
        if isinstance(getattr(self.gui, "state", None), AppState):
            return self.gui.state
        # Compatibility for third-party legacy GUI hosts; real GUI owns AppState.
        gui = self.gui
        state = AppState()
        try:
            state.profiles = gui._?꾨줈?뚯씪??or {}
            state.profile_ids = gui._?꾨줈?뚯씪_ids or []
            state.active_profile_id = gui._?쒖꽦_?쒖떇_?꾨줈?뚯씪
        except AttributeError:
            pass
        try:
            state.analyzing_format = gui._?쒖떇遺꾩꽍以?
            state.analyzing_file = gui._?쒖떇遺꾩꽍_?뚯씪
        except AttributeError:
            pass
        return state

    def _cached_coverage(self, identifier, analysis):
        if not analysis:
            self._coverage_cache.pop(identifier, None)
            return None
        cached = self._coverage_cache.get(identifier)
        if cached is None or cached[0] is not analysis:
            cached = (analysis, _format_coverage(analysis))
            self._coverage_cache[identifier] = cached
        from copy import deepcopy
        return deepcopy(cached[1])

    def invalidate_format_coverage(self, identifier=None):
        if identifier is None:
            self._coverage_cache.clear()
        else:
            self._coverage_cache.pop(identifier, None)

    def _profiles(self):
        """?쒖떇 紐⑸줉: ?쒖떆 ?대쫫(湲곌? ?ы븿), ?대쫫쨌湲곌?, 湲곕낯 ?쒖떇 ?щ?, ?덉떆 ?뚯씪 ?대쫫, ?ъ슜 以??щ?."""
        gui = self.gui
        state = self._profile_state()
        profiles = state.profiles
        ids = state.profile_ids or list(profiles)
        active = state.active_profile_id
        for stale in self._coverage_cache.keys() - profiles.keys():
            self._coverage_cache.pop(stale, None)
        items = []
        for identifier in ids:
            profile = profiles.get(identifier) or {}
            name = str(profile.get("name") or "湲곕낯 ?쒖떇")
            organization = str(profile.get("organization") or "").strip()
            source = profile.get("source")
            analysis = profile.get("element_analysis")
            items.append({
                "id": identifier,
                "name": f"[{organization}] {name}" if organization else name,
                "title": name,
                "organization": organization,
                "builtin": not identifier,
                "source": str(source.get("filename") or "") if isinstance(source, dict) else "",
                "active": identifier == active,
                # ?덉떆 蹂닿퀬?쒖뿉??遺꾩꽍???쒖떇 ?붿냼 媛?대뜲 ?뺣━???곕뒗 ???쒖떇 愿由?李쎌쓽 蹂듭젣 踰붿쐞 ?붿빟)
                "coverage": self._cached_coverage(identifier, analysis),
            })
        return items

    def _format_task(self):
        gui = self.gui
        state = self._profile_state()
        return {"busy": bool(state.analyzing_format), "file": str(state.analyzing_file or "")}

    def _live_progress(self, gui, mode):
        started = getattr(gui, "_?묒뾽?쒖옉?쒓컖", None)
        ended = getattr(gui, "_?묒뾽醫낅즺?쒓컖", None)
        elapsed = None
        if started is not None:
            elapsed = max(0.0, (time.monotonic() if gui.running or ended is None else ended) - started)
        return progress_view(
            mode,
            getattr(gui, "_?덈궡??, None),
            getattr(gui, "_?덈궡吏??, ()),
            selection=getattr(gui, "_吏꾪뻾_?몃??묒뾽", None),
            running=bool(gui.running),
            files=list(gui.files),
            doc=getattr(gui, "_吏꾪뻾臾몄꽌", None),
            results=[{"source": Path(item.get("?먮낯", "")).name, "name": Path(item.get("寃곌낵", "")).name}
                     for item in getattr(gui, "_寃곌낵紐⑸줉", [])],
            failures=getattr(gui, "_?ㅽ뙣紐⑸줉", {}),
            target=self.conversion_target,
            elapsed=elapsed,
        )

    def check_update(self):
        service = self._tk(lambda: self.gui._?낅뜲?댄듃_?쒕퉬??))
        threading.Thread(target=service.check, daemon=True, name="manual-update-check").start()
        return {"ok": True}

    def start_update(self):
        def begin():
            from docfit_app.api_contract import ServiceError
            if self.gui.running:
                raise ServiceError("JOB_RUNNING", "臾몄꽌 ?묒뾽???앸궃 ???낅뜲?댄듃??二쇱꽭??")
            service = self.gui._?낅뜲?댄듃_?쒕퉬??)
            if service.state()["step"] in ("checking", "downloading", "installing"):
                raise ServiceError("BUSY", "?낅뜲?댄듃 ?묒뾽??吏꾪뻾 以묒씠?먯슂.")
            threading.Thread(target=service.start_update, daemon=True, name="manual-update-download").start()
            return {"ok": True}
        return self._tk(lambda: response(begin))

    def open_update_page(self):
        service = self._tk(lambda: self.gui._?낅뜲?댄듃_?쒕퉬??))
        return {"ok": service.open_download_page()}

    def get_state(self):
        # ?뚯씪紐??쒕퉬?ㅻ? 泥섏쓬 留뚮뱾 ??Tk ?몄텧??湲곕떎由щ?濡?Tk ?ㅻ젅??諛뽰뿉??泥섎━?쒕떎.
        rename_open = self._drain_rename_paths()

        def snapshot():
            gui = self.gui
            mode = gui.selected_mode.get()
            if mode == "spacing" and getattr(self, "_page_fit_card", False):
                mode = "pagefit"  # '?섏씠吏 留욎땄' 移대뱶: ?대????먭컙 ?뺣━ ?먮쫫??履?留욎땄留?
            watched = getattr(self, "_quick_watch", None)
            if watched and not self._profile_state().analyzing_format:
                active = self._profile_state().active_profile_id
                self._quick_notice = {"id": uuid.uuid4().hex, "message": (
                    f"{watched['name']} 쨌 ???쒖떇???깅줉?섍퀬 ?좏깮?덉뼱??" if active not in watched["ids"]
                    else "?쒖떇???깅줉?섏? 紐삵뻽?댁슂. 泥섎━ ?곹깭瑜??뺤씤??二쇱꽭??")}
                self._quick_watch = None
            return {
                "job": self._jobs().latest(),
                "_open_completed_result": False,
                "files": [
                    {"name": Path(path).name, "path": path, "folder": str(Path(path).parent),
                     "size": _file_size(path)}
                    for path in gui.files
                ],
                "count": len(gui.files),
                "mode": mode,
                "quick_notice": getattr(self, "_quick_notice", {}),
                "doc_hints": dict(self._ux().doc_hints),
                "user_overrode_mode": self._ux().user_overrode_mode,
                "zero_click": self._zero_click_snapshot(),
                "instant_run_on_drop": False,
                "auto_open_result": False,
                "include_spacing": self._include_spacing(),
                "reset_spacing": self._reset_spacing(),
                "table_spacing": self._table_spacing(),
                "exclude_tables": self._exclude_tables(),
                "card_options": self._card_options(),
                "status": gui.status_var.get(),
                "running": bool(gui.running),
                "completion": dict(getattr(gui, "_flutter_completion", {}) or {}),
                "format_review": dict(getattr(gui, "_flutter_format_review", {}) or {}),
                "failures": dict(getattr(gui, "_?ㅽ뙣紐⑸줉", {}) or {}),
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
                    {
                        "name": Path(item.get("寃곌낵", "")).name,
                        "path": item.get("寃곌낵", ""),
                        "source": Path(item.get("?먮낯", "")).name,
                        "pages": item.get("履쎌닔"),
                    }
                    for item in getattr(gui, "_寃곌낵紐⑸줉", [])
                ],
                "default_saved": bool(gui._?몃??묒뾽_湲곕낯???get(mode, False)),
                "stages": [] if mode == "file_format" else self._stages(mode),
                "profiles": self._profiles(),
                "profile": self._profile_state().active_profile_id,
                "format_task": self._format_task(),
                "pending_dialog": self._pending_dialog(),
                "drop_target": self.drop_target,
                "rename_open": rename_open,
                "sidebar_collapsed": self._sidebar_collapsed_value(),
                "developer_mode": bool(self.gui._以留??쒕퉬??).settings.read().get('developer_mode', False)),
                "always_on_top": bool(self.gui._以留??쒕퉬??).settings.read().get('always_on_top', False)),
                "sidebar_mode": self.sidebar_active,
                "document_drop_revision": self._document_drop_revision,
                "options": {
                    name: bool(getattr(gui, attribute).get())
                    for name, attribute in QUICK_OPTIONS.items()
                    if hasattr(gui, attribute)
                },
                "guide": guide_state(
                    mode,
                    getattr(gui, "_?덈궡??, None),
                    getattr(gui, "_?덈궡吏??, ()),
                ),
                # 湲곕뒫蹂?留욎땄 吏꾪뻾 ?붾㈃(?뚰뙆): ?④퀎쨌臾몄꽌 ?湲곗뿴쨌寃쎄낵 ?쒓컙????踰덉뿉 蹂대궦??
                "live": self._live_progress(gui, mode),
                "conversion_target": self.conversion_target,
                "conversion_targets": [],
                "can_start": self._can_start(mode, gui.files, gui.running) if mode != "file_format" else False,
                "version": APP_VERSION,
                "update": gui._?낅뜲?댄듃_?쒕퉬??).state() if hasattr(gui, "_?낅뜲?댄듃_?쒕퉬??) else {},
            }

        state = self._tk(snapshot)
        if state.pop("_open_completed_result", False):
            try:
                self.open_result(0)
            except OSError:
                logging.getLogger(__name__).warning("寃곌낵 ?먮룞 ?닿린 ?ㅽ뙣", exc_info=True)
        if state["mode"] == "file_format":
            # ?몃? ?꾧뎄 踰꾩쟾 議고쉶瑜?Tk ?대깽??猷⑦봽?먯꽌 ?ㅽ뻾?섎㈃ ?붾㈃??硫덉텣??
            # GUI ?곹깭瑜??쎌? ??WebView ?붿껌 ?ㅻ젅?쒖뿉??以鍮??곹깭瑜??뺤씤?쒕떎.
            files = [item["path"] for item in state["files"]]
            targets = self._conversion_targets(files)
            state["conversion_targets"] = targets
            state["can_start"] = self._can_start(state["mode"], files, state["running"], targets)
        bulk_state = getattr(self, "_bulk_state", None)
        state["hwp_bulk"] = bulk_state.as_dict() if bulk_state else None
        return state

    def _can_start(self, mode, files, running, conversion_targets=None):
        if not files or running:
            return False
        if mode == "spacing":
            options = self._card_options()
            if not options["spacing_enabled"] and options["spacing_exclude_pagefit"]:
                return False
        suffixes = [Path(path).suffix.lower() for path in files]
        if mode == "file_format":
            targets = {item["format"]: item for item in (conversion_targets or self._conversion_targets(files))}
            return all(suffix in SUPPORTED_INPUT_EXTENSIONS for suffix in suffixes) and bool(
                targets.get(self.conversion_target, {}).get("enabled")
            )
        return all(suffix in {".hwp", ".hwpx", ".txt", ".md", ".doc", ".docx", ".pdf"}
                   for suffix in suffixes)

    @staticmethod
    def _hwp_com_available():
        """??湲???꾩슦吏 ?딄퀬 湲곕낯쨌32鍮꾪듃쨌64鍮꾪듃 COM ?깅줉 蹂닿린瑜??뺤씤?쒕떎."""
        if os.name != "nt":
            return False
        try:
            import winreg
        except ImportError:
            return False
        for view in dict.fromkeys((0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY)):
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "HwpFrame.HwpObject",
                                    0, winreg.KEY_READ | view):
                    return True
            except OSError:
                continue
        return False

    def _conversion_prerequisites(self):
        with self._conversion_prerequisites_lock:
            now = time.monotonic()
            cached = self._conversion_prerequisites_cache
            if cached is not None and now - self._conversion_prerequisites_checked < 30:
                return cached
            from docfit_core.kordoc_bridge import engine_status
            from docfit_core.kordoc_runtime import pandoc_available
            pandoc_path = shutil.which("pandoc.exe") or shutil.which("pandoc")
            from docfit_core.kordoc_bridge import ocr_available
            self._conversion_prerequisites_cache = {
                "kordoc": engine_status(),
                "ocr": ocr_available(),
                "pandoc": bool(pandoc_path) or pandoc_available(),
                "hwp_com": self._hwp_com_available(),
            }
            self._conversion_prerequisites_checked = time.monotonic()
            return self._conversion_prerequisites_cache

    def _conversion_targets(self, files):
        """寃곌낵 ?뺤떇 紐⑸줉. ?ｌ? ?뚯씪??紐⑤몢 ?대? 洹??뺤떇?대㈃(?? PDF?뭁DF) 洹??뺤떇? 怨좊? ???녾쾶 ?쒕떎(2026-10-22)."""
        suffixes = [Path(path).suffix.lower() for path in files]
        targets = self._conversion_targets_raw(files, suffixes)
        if suffixes:
            for target in targets:
                same = SAME_FORMAT_SUFFIXES.get(target["format"])
                if same and all(suffix in same for suffix in suffixes):
                    target["enabled"] = False
                    target["reason"] = f"?대? {target['label']} ?뚯씪?대씪 媛숈? ?뺤떇?쇰줈??諛붽? ???놁뼱??
        return targets

    def _conversion_targets_raw(self, files, suffixes):
        valid =bool(suffixes) and all(suffix in SUPPORTED_INPUT_EXTENSIONS for suffix in suffixes)
        prerequisites = self._conversion_prerequisites()
        kordoc = prerequisites["kordoc"]
        kordoc_ready = bool(kordoc.get("available"))
        pandoc_ready = prerequisites["pandoc"]
        hwp_ready = prerequisites["hwp_com"]
        engine_reason = str(kordoc.get("reason") or "蹂???붿쭊???ъ슜?????놁뒿?덈떎")
        # 洹몃┝ ?낅젰? 湲???몄떇(OCR)???꾩슂?섎떎. ?먯뇙留?袁몃윭誘몄뿉??OCR???놁쑝誘濡?誘몃━ 留됯퀬 ?댁쑀瑜?蹂댁씤??
        if valid and kordoc_ready and not prerequisites.get("ocr", True) and any(
                suffix in IMAGE_INPUT_EXTENSIONS for suffix in suffixes):
            kordoc_ready = False
            engine_reason = "洹몃┝ ?뚯씪? 湲???몄떇(OCR)???꾩슂??蹂?섑븷 ???놁뒿?덈떎(?먯뇙留?袁몃윭誘몄뿉 OCR 誘명룷??"
        # HWP쨌HWPX????湲??吏곸젒 PDF濡???ν븳?? ?ㅻⅨ ?낅젰留?kordoc 以묎컙 蹂?섏씠 ?꾩슂?섎떎.
        # ?대? PDF???뚯씪? PDF 蹂?섏뿉??嫄대꼫?곕?濡?蹂???붿쭊???꾩슂 ?녿떎.
        pdf_needs_kordoc = any(suffix not in HANCOM_PDF_DIRECT and suffix != ".pdf" for suffix in suffixes)
        pdf_ready = hwp_ready and (not pdf_needs_kordoc or kordoc_ready)
        invalid_reason = "蹂?섑븷 ???녿뒗 ?뚯씪 ?뺤떇???덉뒿?덈떎"
        pdf_reason = (invalid_reason if not valid else
                      "??湲 PDF ???湲곕뒫???ъ슜?????놁뒿?덈떎" if not hwp_ready else
                      engine_reason if pdf_needs_kordoc and not kordoc_ready else
                      "??湲 ?댁옣 PDF ????ъ슜 쨌 異붽? 蹂?섍린 ?ㅼ튂 ?놁쓬" if not pdf_needs_kordoc else
                      "蹂???붿쭊 + ??湲 PDF ???以鍮꾨맖")
        # 洹몃┝? ??湲 PDF ??λ낯??履쎈쭏???뚮뜑留곹븯誘濡?PDF? 以鍮?議곌굔??媛숇떎.
        hwpx_needs_kordoc = any(suffix != ".hwp" for suffix in suffixes)
        hwpx_needs_com = any(suffix == ".hwp" for suffix in suffixes)
        hwpx_ready = (not hwpx_needs_kordoc or kordoc_ready) and (not hwpx_needs_com or hwp_ready)
        hwpx_reason = (invalid_reason if not valid else
                       "??湲 HWP ???湲곕뒫???ъ슜?????놁뒿?덈떎" if hwpx_needs_com and not hwp_ready else
                       engine_reason if hwpx_needs_kordoc and not kordoc_ready else
                       "??湲 ?댁옣 HWP?묱WPX ???쨌 ?먮낯 蹂댁〈" if not hwpx_needs_kordoc else
                       "蹂??以鍮꾨맖")
        pdf_only = all(suffix == ".pdf" for suffix in suffixes)
        merge_direct = all(suffix == ".pdf" or suffix in IMAGE_INPUT_EXTENSIONS for suffix in suffixes)
        # ?⑹튂湲곗뿉??PDF쨌洹몃┝? 洹몃?濡??곌퀬, HWP쨌HWPX????湲, 洹?諛뽰쓽 ?뺤떇留?蹂???붿쭊?????꾩슂?섎떎.
        merge_converted = [s for s in suffixes if s != ".pdf" and s not in IMAGE_INPUT_EXTENSIONS]
        merge_ready = merge_direct or (hwp_ready and (kordoc_ready or all(s in HANCOM_PDF_DIRECT for s in merge_converted)))
        image_reason = (pdf_reason if not (valid and pdf_ready) else
                        "??湲 PDF ?????履쎈쭏??洹몃┝ ???쨌 ?щ윭 履쎌? ?대뜑濡????)
        pandoc_only = all(suffix in {".html", ".htm", ".md", ".txt"} for suffix in suffixes)
        pandoc_targets_ready = pandoc_ready and (kordoc_ready or pandoc_only)
        text_targets_ready = (all(suffix == ".hwpx" for suffix in suffixes) or
                              pandoc_ready and (kordoc_ready or pandoc_only))
        return [
            {"format": "hwpx", "label": "HWPX", "enabled": valid and hwpx_ready,
             "reason": hwpx_reason},
            {"format": "pdf", "label": "PDF", "enabled": valid and pdf_ready, "reason": pdf_reason},
            # PDF ?섎굹濡??⑹튂湲? ?щ윭 ?뚯씪(PDF쨌洹몃┝? 洹몃?濡? HWP쨌HWPX ?깆? ??湲 PDF ????????쒖꽌?濡???PDF濡?臾띕뒗??
            {"format": "pdfm", "label": "PDF ?섎굹濡??⑹튂湲?,
             "enabled": valid and len(suffixes) >= 2 and merge_ready,
             "reason": (invalid_reason if not valid else
                        "?뚯씪??2媛??댁긽 ?ｌ쑝硫??섎굹??PDF濡??⑹튌 ???덉뼱?? if len(suffixes) < 2 else
                        pdf_reason if not merge_ready else
                        "?ｌ? ?쒖꽌?濡???PDF濡??⑹묠 쨌 ?뚯씪留덈떎 梨낃컝??쨌 ?뷀샇 PDF???쒖쇅")},
            # PDF ?뺤텞? ??湲쨌蹂???붿쭊 ?놁씠 PDF ?덉쓽 洹몃┝쨌?ㅽ듃由쇰쭔 ?ㅼ떆 ??ν븳??蹂댁븞 PDF??媛숈? 沅뚰븳 ?좎?).
            {"format": "pdfz", "label": "PDF ?뺤텞", "enabled": valid and all(s == ".pdf" for s in suffixes),
             "reason": (invalid_reason if not valid else
                        "PDF ?뚯씪?먮쭔 ?????덉뒿?덈떎" if any(s != ".pdf" for s in suffixes) else
                        "湲?먃룹そ? 洹몃?濡? 洹몃┝留??ㅼ떆 ???쨌 蹂댁븞 PDF??媛숈? 沅뚰븳 ?좎?")},
            *({"format": kind, "label": kind.upper(), "enabled": valid and text_targets_ready,
               "reason": invalid_reason if not valid else engine_reason if not text_targets_ready and not kordoc_ready else "?띿뒪??異붿텧 以鍮꾨맖"} for kind in ("txt", "md")),
            *({"format": kind, "label": kind.upper(), "enabled": valid and pandoc_targets_ready,
               "reason": invalid_reason if not valid else engine_reason if not kordoc_ready and not pandoc_only else
                        "?댁옣 Pandoc???ъ슜?????놁쓬" if not pandoc_ready else "?댁옣 Pandoc 以鍮꾨맖"} for kind in ("docx", "epub", "html")),
            # PDF留??ｌ쑝硫???湲쨌蹂???붿쭊 ?놁씠 履쎈쭏??諛붾줈 洹몃┛??
            *({"format": kind, "label": kind.upper(), "enabled": valid and (pdf_only or pdf_ready),
               "reason": "PDF 履쎈쭏??洹몃┝ ???쨌 ??湲 遺덊븘?? if valid and pdf_only else image_reason}
              for kind in IMAGE_FORMATS),
        ]

    def select_files(self, payload):
        self._file_dialogs.submit_selection(**payload)
        return self._file_dialogs.selection_status(payload['request_id'])

    def selection_status(self, request_id):
        return self._file_dialogs.selection_status(request_id)

    def register_selection(self, payload):
        return self._file_dialogs.register_selection(**payload)

    def _selection_path(self, payload, purpose, key='input_selection_id'):
        from docfit_app.api_contract import ServiceError
        token = payload.get(key)
        if not token:
            raise ServiceError('FILE_SELECTION_REQUIRED', 'Select a file first.')
        return self._file_dialogs.resolve_selection(token, purpose)[0]

    def add_files(self, selection_id=None):
        if not selection_id:
            return {'ok': False, 'error': 'FILE_SELECTION_REQUIRED'}
        return self.add_paths(self._file_dialogs.resolve_selection(selection_id, 'add_files'))

    def add_folder(self):
        return {'ok': False, 'error': 'FILE_SELECTION_REQUIRED'}

    def add_directory(self, selection_id, recursive=False):
        paths = self._file_dialogs.resolve_selection(selection_id, 'add_folder')
        return self.add_paths(self._file_dialogs.directory_files(paths, recursive))

    def add_paths(self, paths, *, from_drop=False):
        if not isinstance(paths, (list, tuple)):
            return self.get_state()
        if len(paths) > 1000:
            return self.get_state()

        if paths:
            from docfit_app.api_contract import ServiceError
            try:
                selection = self._file_dialogs.register_selection('add_files', paths)
                paths = self._file_dialogs.resolve_selection(selection['selection_id'], 'add_files')
            except ServiceError:
                return self.get_state()

        def add():
            if self.gui.running:
                return
            self._cancel_pending_drop()
            added = 0
            for value in paths:
                path = str(value or "").strip()
                if len(path) > 32767:
                    continue
                if not path:
                    continue
                try:
                    candidate = Path(path)
                    if candidate.is_symlink():
                        continue
                    candidate = candidate.resolve(strict=True)
                    path = str(candidate)
                    if candidate.is_file() and candidate.suffix.lower() not in (
                        set(SUPPORTED_INPUT_EXTENSIONS) | {".txt", ".md", ".doc"}
                    ):
                        continue
                    if Path(path).is_dir():
                        added += self.gui.?대뜑異붽?(path)
                    elif self.gui.?뚯씪異붽?(path):
                        added += 1
                except (OSError, ValueError):
                    continue
            if added:
                if from_drop:
                    self._document_drop_revision += 1
                self.gui.status_var.set(f"{added}媛?異붽? 쨌 珥?{len(self.gui.files)}媛?臾몄꽌")
                self.gui.濡쒓렇?쒖떆(f"{added}媛?臾몄꽌 異붽?")
                self._update_document_hints()
                self._cancel_pending_drop()

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
                self.gui._?좏깮??젣()
                self._update_document_hints()

        self._tk(remove)
        return self.get_state()

    def clear_files(self):
        self._tk(self.gui.紐⑸줉吏?곌린)
        self._tk(self._update_document_hints)
        return self.get_state()

    def _include_spacing(self):
        variable = getattr(self.gui, "include_spacing_var", None)
        return True if variable is None else bool(variable.get())

    def _mode_selected(self):
        if hasattr(self.gui, "_紐⑤뱶_?좏깮??):
            self.gui._紐⑤뱶_?좏깮??)

    def set_mode(self, mode):
        """?묒뾽 移대뱶瑜?怨좊Ⅸ?? 移대뱶?????μ씠硫?'??踰덉뿉 ?곸슜'(all)? '?먭컙 議곗젙 ?ы븿'???꾨㈃
        ?쒖떇 ?곸슜(format)?쇰줈 ?ㅽ뻾?쒕떎. ?덉쟾 ?붾㈃??蹂대궡??format? ?먭컙 議곗젙??????踰덉뿉 ?곸슜?대떎."""
        if mode not in {"spacing", "unify", "format", "all", "file_format", "pagefit"}:
            raise ValueError("吏?먰븯吏 ?딅뒗 ?묒뾽 諛⑹떇?낅땲??")

        def select():
            if self.gui.running:
                return
            self._ux().user_overrode_mode = True
            self._cancel_pending_drop()
            # '?섏씠吏 留욎땄' 移대뱶(2026-10-30): 履?留욎땄留??섎뒗 ?묒뾽. ?대????먭컙 ?뺣━ ?먮쫫?먯꽌 ?먭컙???꾧퀬 履?留욎땄留?耳좊떎.
            self._page_fit_card = mode == "pagefit"
            internal = "spacing" if mode == "pagefit" else mode
            if mode in ("all", "format"):
                variable = getattr(self.gui, "include_spacing_var", None)
                if mode == "format" and variable is not None:
                    variable.set(False)
                internal = "all" if self._include_spacing() else "format"
            self.gui.selected_mode.set(internal)
            self._mode_selected()

        self._tk(select)
        return self.get_state()

    def set_conversion_target(self, target):
        target = str(target or "").lower()
        if target not in CONVERSION_OUTPUTS:
            raise ValueError("寃곌낵 ?뺤떇? HWPX, PDF, PDF ?뺤텞, DOCX, EPUB, HTML, JPG, PNG, TXT ?먮뒗 MD留??좏깮?????덉뒿?덈떎.")
        def update():
            if not self.gui.running:
                self.conversion_target = target
        self._tk(update)
        return self.get_state()

    def start_single_file_conversion(self, file_index, target):
        """?꾩옱 怨듯넻 蹂??媛?μ꽦 ?먮떒???곸슜???좏깮???낅젰 ?섎굹瑜?怨좎젙?섏뿬 蹂?섑븳??"""
        from docfit_app.api_contract import ServiceError
        target = str(target or "").lower()
        if target not in CONVERSION_OUTPUTS:
            raise ValueError("吏?먰븯吏 ?딅뒗 寃곌낵 ?뺤떇?낅땲??")

        def begin():
            gui = self.gui
            if gui.running:
                raise ServiceError('JOB_RUNNING', '臾몄꽌 ?묒뾽??吏꾪뻾 以묒엯?덈떎.')
            try:
                index = int(file_index)
            except (TypeError, ValueError):
                raise ValueError("?뚯씪 ?좏깮???щ컮瑜댁? ?딆뒿?덈떎.")
            current_files = list(gui.files)
            if not 0 <= index < len(current_files):
                raise ValueError("?뚯씪??李얠쓣 ???놁뒿?덈떎.")
            source_snapshot = str(current_files[index])
            targets = {item["format"]: item for item in self._conversion_targets([source_snapshot])}
            chosen = targets.get(target)
            if chosen is None or not chosen.get("enabled"):
                reason = (chosen or {}).get("reason") or "吏?먰븯吏 ?딅뒗 寃곌낵 ?뺤떇?낅땲??
                raise ValueError(f"{target.upper()} 蹂?섏쓣 ?쒖옉?????놁뒿?덈떎: {reason}")

            return self._start_single_conversion_snapshot(source_snapshot, target)

        return self._tk(begin)

    def _start_single_conversion_snapshot(self, source_snapshot, target):
        """紐⑸줉/?꾩옱 ?源?UI ?곹깭瑜??곗? ?딄퀬 ?⑥씪 寃쎈줈 snapshot?쇰줈 runner瑜??쒖옉?쒕떎."""
        from docfit_app.api_contract import ServiceError
        from docfit_app.jobs import manager_for, prepare_legacy
        from docfit_app.conversion_runner import start_conversion_job
        gui = self.gui
        if gui.running:
            raise ServiceError('JOB_RUNNING', '臾몄꽌 ?묒뾽??吏꾪뻾 以묒엯?덈떎.')
        runtime = getattr(gui, '_docfit_runtime_namespace', None)
        if runtime is None:
            runtime = getattr(gui, '?뚯씪?щ㎎_蹂寃??쒖옉').__globals__
        stop_event = runtime.get('以묐떒_event')
        gui_queue = runtime.get('gui_queue')
        if stop_event is None or gui_queue is None:
            raise ServiceError('JOB_NOT_STARTED', '蹂???묒뾽 ?ㅽ뻾 ?섍꼍??以鍮꾪븯吏 紐삵뻽?듬땲??')
        identifier = prepare_legacy(gui).begin(
            'file_format', {'target': target, 'files': [source_snapshot]}, stop_event=stop_event,
        )
        gui._job_id = identifier
        manager = manager_for(gui)
        manager.report(identifier, 'started', {})
        gui._flutter_completion = {}
        gui._flutter_format_review = {}
        gui.running = True
        gui.closing = False
        stop_event.clear()
        gui.selected_mode.set('file_format')
        gui._寃곌낵_珥덇린??寃곌낵紐⑸줉??吏?곌린=True)
        gui._?덈궡?? gui._?덈궡吏??= None, set()
        gui._吏꾪뻾臾몄꽌, gui._?ㅽ뙣紐⑸줉, gui._吏꾪뻾_?몃??묒뾽 = None, {}, None
        gui._?묒뾽?쒖옉?쒓컖, gui._?묒뾽醫낅즺?쒓컖 = time.monotonic(), None
        gui.status_var.set('?뚯씪 蹂??以?쨌 1媛?)
        gui._?덈궡_?ㅼ젙(0)
        gui.踰꾪듉_?묒뾽以?)
        gui.濡쒓렇?쒖떆("")
        gui.濡쒓렇?쒖떆(f"?뚯씪 蹂???쒖옉 쨌 1媛?쨌 寃곌낵 {target.upper()}")
        gui._job_managed_conversion = identifier
        start_conversion_job(
            manager, [source_snapshot], target, job_id=identifier,
            progress=gui_queue.put, stop_event=stop_event,
            runtime_factory=lambda: runtime, log=gui.濡쒓렇?쒖떆,
        )
        gui.worker = manager.thread(identifier)
        return identifier

    def set_include_spacing(self, on):
        """'??踰덉뿉 ?곸슜'??'?먭컙 議곗젙 ?ы븿'??諛붽씀怨?洹?移대뱶瑜?怨좊Ⅸ???ㅼ젙 ?뚯씪????λ맂??."""
        def update():
            gui = self.gui
            variable = getattr(gui, "include_spacing_var", None)
            if gui.running or variable is None:
                return
            variable.set(bool(on))
            self._page_fit_card = False  # ?ㅻⅨ 移대뱶瑜?怨좊Ⅴ硫??섏씠吏 留욎땄 移대뱶 ?댁젣
            gui.selected_mode.set("all" if on else "format")
            self._mode_selected()

        self._tk(update)
        return self.get_state()

    def _reset_spacing(self):
        return not bool(getattr(self.gui, "spacing_exclude_reset_var", None).get()) if getattr(self.gui, "spacing_exclude_reset_var", None) is not None else bool(self.gui.stage_choices.get("spacing", {}).get("reset_spacing", True))

    def set_reset_spacing(self, on):
        """湲곗〈 ?명솚 ?몄텧????珥덇린???쒖쇅 移대뱶 ?듭뀡???곌껐?쒕떎."""
        def update():
            gui = self.gui
            if gui.running:
                return
            variable = getattr(gui, "spacing_exclude_reset_var", None)
            if variable is not None:
                variable.set(not bool(on))
            else:
                gui.stage_choices["spacing"]["reset_spacing"] = bool(on)
            self._page_fit_card = False  # ?ㅻⅨ 移대뱶瑜?怨좊Ⅴ硫??섏씠吏 留욎땄 移대뱶 ?댁젣
            gui.selected_mode.set("spacing")
            self._mode_selected()

        self._tk(update)
        return self.get_state()

    def _table_spacing(self):
        variable = getattr(self.gui, "table_spacing_var", None)
        return True if variable is None else bool(variable.get())

    def set_table_spacing(self, on):
        """'?먭컙 ?뺣━'??'?????먭컙 ?뺣━'(?ㅼ젙 table_spacing)瑜?諛붽씀怨?洹?移대뱶瑜?怨좊Ⅸ??

        ?꾨㈃ ??移???臾몄옣? ?먭컙 珥덇린?붋룹옄媛?議곗젙쨌以?蹂묓빀쨌?⑥뼱 寃????곸뿉??鍮좎쭊?? ?ㅼ젙李쎌쓽
        '???쒖떇 ??臾몄옣???먭컙議곗젙?섍린'? 媛숈? 媛믪씠硫??ㅼ젙 ?뚯씪????λ맂??
        """
        def update():
            gui = self.gui
            variable = getattr(gui, "table_spacing_var", None)
            if gui.running or variable is None:
                return
            variable.set(bool(on))
            self._page_fit_card = False  # ?ㅻⅨ 移대뱶瑜?怨좊Ⅴ硫??섏씠吏 留욎땄 移대뱶 ?댁젣
            gui.selected_mode.set("spacing")
            self._mode_selected()

        self._tk(update)
        return self.get_state()

    def _exclude_tables(self):
        variable = getattr(self.gui, "exclude_tables_var", None)
        return False if variable is None else bool(variable.get())

    def set_exclude_tables(self, on):
        """'??踰덉뿉 ?곸슜'??'???쒖쇅'(?ㅼ젙 all_exclude_tables)瑜?諛붽씀怨?洹?移대뱶瑜?怨좊Ⅸ??

        耳쒕㈃ ??愿???몃? ?묒뾽??紐⑤몢 鍮쇨퀬 ??移???臾몄옣???먭컙 ?묒뾽?먯꽌 類?? ?ㅼ젙 ?뚯씪????λ맂??
        """
        def update():
            gui = self.gui
            variable = getattr(gui, "exclude_tables_var", None)
            if gui.running or variable is None:
                return
            variable.set(bool(on))
            self._page_fit_card = False  # ?ㅻⅨ 移대뱶瑜?怨좊Ⅴ硫??섏씠吏 留욎땄 移대뱶 ?댁젣
            gui.selected_mode.set("all" if self._include_spacing() else "format")
            self._mode_selected()

        self._tk(update)
        return self.get_state()

    # 移대뱶 ?듭뀡(?ㅼ젙 ?????붾㈃ 蹂?? 怨좊Ⅴ??移대뱶): ??踰덉뿉 ?곸슜??'?섏씠吏 留욎땄 ?쒖쇅', ?쒖떇 ?듭씪??'???쒖쇅'쨌
    # '?먭컙 ?뺣━ ?쒖쇅'쨌'?섏씠吏 留욎땄 ?쒖쇅'. ?ㅼ젙 ?뚯씪????λ릺硫? 諛붽씀硫??깆쓽 蹂??媛먯떆媛 洹?移대뱶??愿???몃? ?묒뾽??
    # 媛숈씠 耳쒓퀬 ?덈떎(?쒖떇 ?듭씪??履?留욎땄? ?몃? ?묒뾽 湲곕낯媛믪씠 爰쇱쭚?대씪 '?섏씠吏 留욎땄 ?쒖쇅'媛 湲곕낯 耳쒖쭚).
    _CARD_OPTIONS = {
        "spacing_enabled": ("spacing_enabled_var", "spacing"),
        "spacing_exclude_pagefit": ("spacing_exclude_pagefit_var", "spacing"),
        "spacing_exclude_reset": ("spacing_exclude_reset_var", "spacing"),
        "spacing_cell_image_to_bg": ("spacing_cell_image_to_bg_var", "spacing"),
        "all_cell_image_to_bg": ("all_cell_image_to_bg_var", "all"),
        "all_exclude_pagefit": ("all_exclude_pagefit_var", "all"),
        "all_exclude_linespacing": ("all_exclude_linespacing_var", "all"),
        "unify_exclude_tables": ("unify_exclude_tables_var", "unify"),
        "unify_exclude_spacing": ("unify_exclude_spacing_var", "unify"),
        "unify_exclude_pagefit": ("unify_exclude_pagefit_var", "unify"),
        "unify_keep_layout": ("unify_keep_layout_var", "unify"),
        "unify_quick_mode": ("unify_quick_mode_var", "unify"),
    }

    def _card_options(self):
        result = {}
        for key, (name, _) in self._CARD_OPTIONS.items():
            variable = getattr(self.gui, name, None)
            defaults = {"spacing_enabled": True, "spacing_exclude_pagefit": True,
                        "spacing_exclude_reset": False, "all_exclude_linespacing": False}
            result[key] = defaults.get(key, False) if variable is None else bool(variable.get())
        return result

    def set_card_option(self, key, on):
        """移대뱶 ?듭뀡 ?섎굹瑜?諛붽씀怨?洹?移대뱶瑜?怨좊Ⅸ??"""
        if key not in self._CARD_OPTIONS:
            raise ValueError("吏?먰븯吏 ?딅뒗 移대뱶 ?듭뀡?낅땲??")
        name, card = self._CARD_OPTIONS[key]

        def update():
            gui = self.gui
            variable = getattr(gui, name, None)
            if gui.running or variable is None:
                return
            variable.set(bool(on))
            if card == "all":
                self._page_fit_card = False  # ?ㅻⅨ 移대뱶瑜?怨좊Ⅴ硫??섏씠吏 留욎땄 移대뱶 ?댁젣
                gui.selected_mode.set("all" if self._include_spacing() else "format")
            else:
                self._page_fit_card = False  # ?ㅻⅨ 移대뱶瑜?怨좊Ⅴ硫??섏씠吏 留욎땄 移대뱶 ?댁젣
                gui.selected_mode.set(card)
            self._mode_selected()

        self._tk(update)
        return self.get_state()

    def set_range(self, enabled, start="1", end="1"):
        def update():
            if self.gui.running:
                return
            self.gui.range_mode_var.set("pages" if enabled else "all")
            self.gui.page_range_var.set(bool(enabled))
            self.gui.range_start_var.set(str(start or "1"))
            self.gui.range_end_var.set(str(end or start or "1"))
            self.gui._踰붿쐞_?앹쭅?묒꽕??= bool(enabled)
            self.gui._踰붿쐞_?곹깭_媛깆떊()

        self._tk(update)
        return self.get_state()

    def _jobs(self):
        from docfit_app.jobs import manager_for
        return manager_for(self.gui)

    def start_job(self, kind, params=None):
        from docfit_app.api_contract import ServiceError
        if params is not None and not isinstance(params, dict):
            raise ServiceError('INVALID_INPUT', '?묒뾽 ?낅젰???뺤씤??二쇱꽭??')
        params = params or {}
        if kind == 'table_copy':
            return self._jobs().start(kind, params, lambda report, cancelled:
                self._table_copy_job(params, report, cancelled))
        if kind not in {'format', 'spacing', 'unify', 'all', 'file_format', 'pagefit'}:
            raise ServiceError('INVALID_INPUT', '吏?먰븯吏 ?딅뒗 ?묒뾽 醫낅쪟?낅땲??')
        if kind == 'file_format' and 'target' in params and not params.get('single_file'):
            self.set_conversion_target(params['target'])
        if kind == 'file_format' and params.get('single_file'):
            self._single_conversion_target = str(params['target']).lower()
        try:
            return self._start_legacy(kind, params.get('range_enabled', False),
                                  params.get('start', '1'), params.get('end', '1'),
                                  file_order=params.get('file_order'), _strict=True,
                                  single_file=bool(params.get('single_file')))
        finally:
            if kind == 'file_format' and params.get('single_file'):
                self._single_conversion_target = None

    def _table_copy_job(self, params, report, cancelled):
        if cancelled():
            return None
        result = self._table_units_command('copy', params)
        if not result.get('ok'):
            error = result.get('error') or {}
            from docfit_app.api_contract import ServiceError
            raise ServiceError(error.get('code', 'JOB_FAILED'), error.get('message', '??蹂듭궗 ?ㅽ뙣'))
        report('item_done', result.get('data') or {})
        return result.get('data')

    def cancel_job(self, job_id):
        state = self._jobs().cancel(job_id)
        if self._tk(lambda: getattr(self.gui, '_job_id', None)) == job_id:
            self._tk(self.gui.?묒뾽以묐떒)
        return state

    def get_events(self, after_seq=0, max=200):
        return self._jobs().events(after_seq, max)

    def start(self, mode, range_enabled=False, start="1", end="1", file_order=None):
        from docfit_app.api_contract import ServiceError
        try:
            self.start_job(mode, dict(range_enabled=range_enabled, start=start, end=end, file_order=file_order))
        except ServiceError as exc:
            # 湲곗〈 start???뚯씪 ?놁쓬쨌?대? ?ㅽ뻾 以???GUI媛 ?쒖옉?섏? ?딆? 寃쎌슦?먮룄 ?곹깭瑜??뚮젮以??
            if exc.code not in {'JOB_NOT_STARTED', 'JOB_RUNNING'}:
                raise
        return self.get_state()

    def _start_legacy(self, mode, range_enabled=False, start="1", end="1", *, file_order=None,
                      _strict=False, single_file=False):
        from docfit_app.api_contract import ServiceError
        def started(previous):
            identifier = getattr(self.gui, '_job_id', None)
            if _strict and (not identifier or identifier == previous):
                raise ServiceError('JOB_NOT_STARTED', '?낅젰 臾몄꽌? ?묒뾽 ?ㅼ젙???뺤씤??二쇱꽭??')
            return identifier
        if file_order is not None and (mode != "file_format" or
                                       (self.conversion_target != "pdfm" and not single_file)):
            raise ValueError("?뚯씪 ?쒖꽌??PDF ?섎굹濡??⑹튂湲곗뿉?쒕쭔 吏?뺥븷 ???덉뒿?덈떎.")

        if mode not in {"spacing", "unify", "format", "all", "file_format", "pagefit"}:
            raise ValueError("吏?먰븯吏 ?딅뒗 ?묒뾽 諛⑹떇?낅땲??")

        if mode == "file_format":
            # ?붾㈃? 以鍮꾨릺吏 ?딆? ?뺤떇???쒖옉 踰꾪듉???꾩?留? ??쾶 ???붿껌???ш린??留됰뒗??
            files = self._tk(lambda: list(self.gui.files))
            target = getattr(self, '_single_conversion_target', self.conversion_target) if single_file else self.conversion_target
            targets = {item["format"]: item for item in self._conversion_targets(files)}
            chosen = targets.get(target)
            if files and (chosen is None or not chosen.get("enabled")):
                reason = (chosen or {}).get("reason") or "吏?먰븯吏 ?딅뒗 寃곌낵 ?뺤떇?낅땲??
                raise ValueError(f"{target.upper()} 蹂?섏쓣 ?쒖옉?????놁뒿?덈떎: {reason}")
            if file_order is not None:
                if not isinstance(file_order, (list, tuple)):
                    raise ValueError("?뚯씪 ?쒖꽌 紐⑸줉???щ컮瑜댁? ?딆뒿?덈떎.")
                def _norm(p):
                    try:
                        return os.path.normcase(os.path.normpath(str(p)))
                    except Exception:
                        return str(p)
                if (single_file and (len(file_order) != 1 or file_order[0] not in files) or
                        not single_file and (len(file_order) != len(files) or
                                             set(map(_norm, file_order)) != set(map(_norm, files)))):
                    raise ValueError("吏?뺥븳 ?뚯씪 ?쒖꽌 紐⑸줉???꾩옱 臾몄꽌 紐⑸줉怨??쇱튂?섏? ?딆뒿?덈떎.")
            def begin_conversion():
                if self.gui.running:
                    raise ServiceError('JOB_RUNNING', '臾몄꽌 ?묒뾽??吏꾪뻾 以묒엯?덈떎.')
                previous = getattr(self.gui, '_job_id', None)
                self.gui._flutter_completion = {}
                self.gui._flutter_format_review = {}
                if single_file:
                    gui = self.gui
                    target_files = list(file_order or [])
                    if gui.running or not target_files:
                        raise ServiceError('JOB_RUNNING' if gui.running else 'JOB_NOT_STARTED',
                                           '?낅젰 臾몄꽌? ?묒뾽 ?ㅼ젙???뺤씤??二쇱꽭??')
                    from docfit_app.jobs import manager_for, prepare_legacy
                    from docfit_app.conversion_runner import start_conversion_job
                    gui._flutter_completion = {}
                    gui._flutter_format_review = {}
                    runtime = getattr(gui, '_docfit_runtime_namespace', None)
                    if runtime is None:
                        runtime = getattr(gui.?뚯씪?щ㎎_蹂寃??쒖옉, '__globals__', {})
                    以묐떒_event = runtime.get('以묐떒_event')
                    gui_queue = runtime.get('gui_queue')
                    if 以묐떒_event is None or gui_queue is None:
                        raise ServiceError('JOB_NOT_STARTED', '蹂???묒뾽 ?ㅽ뻾 ?섍꼍??以鍮꾪븯吏 紐삵뻽?듬땲??')
                    gui._job_id = prepare_legacy(gui).begin(
                        'file_format', {'target': target}, stop_event=以묐떒_event,
                    )
                    identifier = gui._job_id
                    manager = manager_for(gui)
                    manager.report(identifier, 'started', {})
                    gui.running = True
                    gui.closing = False
                    以묐떒_event.clear()
                    gui.selected_mode.set('file_format')
                    gui._寃곌낵_珥덇린??寃곌낵紐⑸줉??吏?곌린=True)
                    gui._?덈궡?? gui._?덈궡吏??= None, set()
                    gui._吏꾪뻾臾몄꽌, gui._?ㅽ뙣紐⑸줉, gui._吏꾪뻾_?몃??묒뾽 = None, {}, None
                    gui._?묒뾽?쒖옉?쒓컖, gui._?묒뾽醫낅즺?쒓컖 = time.monotonic(), None
                    gui.status_var.set(f"?뚯씪 蹂??以?쨌 1媛?)
                    gui._?덈궡_?ㅼ젙(0)
                    gui.踰꾪듉_?묒뾽以?)
                    gui.濡쒓렇?쒖떆("")
                    gui.濡쒓렇?쒖떆(f"?뚯씪 蹂???쒖옉 쨌 1媛?쨌 寃곌낵 {target.upper()}")
                    gui._job_managed_conversion = identifier
                    start_conversion_job(
                        manager, list(target_files), target, job_id=identifier,
                        progress=gui_queue.put, stop_event=以묐떒_event,
                        runtime_factory=lambda: runtime,
                        log=gui.濡쒓렇?쒖떆,
                    )
                    gui.worker = manager.thread(identifier)
                elif file_order:
                    original_files = list(self.gui.files)
                    try:
                        self.gui.files = list(file_order)
                        self.gui.?뚯씪?щ㎎_蹂寃??쒖옉(target)
                    finally:
                        self.gui.files = original_files
                else:
                    self.gui.?뚯씪?щ㎎_蹂寃??쒖옉(self.conversion_target)
                return started(previous)
            identifier = self._tk(begin_conversion)
            return identifier if _strict else self.get_state()

        def begin():
            if self.gui.running:
                raise ServiceError('JOB_RUNNING', '臾몄꽌 ?묒뾽??吏꾪뻾 以묒엯?덈떎.')
            previous = getattr(self.gui, '_job_id', None)
            options = self._card_options()
            if mode == "spacing" and not options["spacing_enabled"] and options["spacing_exclude_pagefit"]:
                raise ValueError("?먭컙 ?뺣━瑜??꾧퀬 ?섏씠吏 留욎땄???쒖쇅?섎㈃ ???쇱씠 ?놁뒿?덈떎.")
            page_fit_only = mode == "pagefit"
            run_mode = "spacing" if page_fit_only else mode
            self.gui.selected_mode.set(run_mode)
            self.gui.range_mode_var.set("pages" if range_enabled else "all")
            self.gui.page_range_var.set(bool(range_enabled))
            self.gui.range_start_var.set(str(start or "1"))
            self.gui.range_end_var.set(str(end or start or "1"))
            self.gui._踰붿쐞_?앹쭅?묒꽕??= bool(range_enabled)
            self.gui._踰붿쐞_?곹깭_媛깆떊()
            self.gui._flutter_completion = {}
            self.gui._flutter_format_review = {}
            if not page_fit_only:
                self.gui.?묒뾽?쒖옉(mode)
                return started(previous)
            # ?묒뾽?쒖옉???듭뀡??洹??먮━?먯꽌 ?쎌뼱 ?먮?濡? ?좉퉸 '?먭컙 ?붋룹そ 留욎땄 耳??쇰줈 諛붽엥?ㅺ? ?먭컙 ?뺣━ 移대뱶 ?ㅼ젙???섎룎由곕떎.
            gui = self.gui
            saved = (gui.spacing_enabled_var.get(), gui.spacing_exclude_pagefit_var.get(), gui.spacing_exclude_reset_var.get())
            try:
                gui.spacing_enabled_var.set(False)
                gui.spacing_exclude_pagefit_var.set(False)
                gui.spacing_exclude_reset_var.set(True)
                gui.?묒뾽?쒖옉("spacing")
            finally:
                gui.spacing_enabled_var.set(saved[0])
                gui.spacing_exclude_pagefit_var.set(saved[1])
                gui.spacing_exclude_reset_var.set(saved[2])
            return started(previous)

        identifier = self._tk(begin)
        return identifier if _strict else self.get_state()

    def stop(self):
        job = self._jobs().latest()
        identifier = job['id'] if job and job['state'] not in {'done', 'failed', 'cancelled'} else None
        if identifier:
            self.cancel_job(identifier)
        else:
            self._tk(self.gui.?묒뾽以묐떒)
        return self.get_state()

    def _configuration(self):
        from docfit_app.configuration_service import ConfigurationService
        return ConfigurationService(self.gui._以留??쒕퉬??).settings)

    def _settings_snapshot(self):
        from docfit_app.shell_menu import status
        snapshot = self._configuration().snapshot(running=self.gui.running)
        snapshot['values']['shell_menu'] = status()['registered']
        return snapshot

    def get_settings(self):
        return self._tk(lambda: response(self._settings_snapshot))

    def save_settings(self, values, revision):
        def save():
            self._configuration().save(values, revision, running=self.gui.running)
            if 'shell_menu' in values:
                from docfit_app.shell_menu import register, unregister, launch_command
                if values['shell_menu']:
                    register(launch_command())
                else:
                    unregister()
            self.gui._Flutter?ㅼ젙_諛섏쁺(values)
            if self.window is not None and 'always_on_top' in values:
                self.window.set_on_top(bool(values['always_on_top']))
                self._saved_window['topmost'] = bool(values['always_on_top'])
            return self._settings_snapshot()
        return self._tk(lambda: response(save))

    def _tk_fallback_enabled(self):
        var = getattr(self.gui, "ui_tk_fallback_var", None)
        if var is not None and hasattr(var, "get"):
            return bool(var.get())
        fallback = getattr(self.gui, "ui_tk_fallback", None)
        if fallback is not None:
            return bool(fallback)
        try:
            service = getattr(self.gui, "_以留??쒕퉬??, None)
            if callable(service):
                settings = service().settings.read()
                if isinstance(settings, dict) and "ui_tk_fallback" in settings:
                    return bool(settings["ui_tk_fallback"])
        except Exception:
            pass
        try:
            settings = getattr(self.gui, "settings", None)
            if isinstance(settings, dict) and "ui_tk_fallback" in settings:
                return bool(settings["ui_tk_fallback"])
        except Exception:
            pass
        from docfit_app.settings_schema import DEFAULTS
        return bool(DEFAULTS.get("ui_tk_fallback", False))

    def open_settings(self):
        if not self._tk_fallback_enabled():
            return {"ok": False, "error": "FLUTTER_ONLY"}
        self._tk(self.gui.?ㅼ젙李??닿린, timeout=None, front=True)
        return True

    def text_input(self):
        if not self._tk_fallback_enabled():
            return {"ok": False, "error": "FLUTTER_ONLY"}
        self._tk(self.gui._?띿뒪?몃줈_臾몄꽌異붽?_?닿린, timeout=None, front=True)
        return self.get_state()

    def open_stages(self):
        if not self._tk_fallback_enabled():
            return {"ok": False, "error": "FLUTTER_ONLY"}
        self._tk(lambda: self.gui._?몃??묒뾽_?닿린(
            self.gui.selected_mode.get(), self.gui._?몃??묒뾽_湲곕낯???get(self.gui.selected_mode.get(), True)
        ), timeout=None, front=True)
        return True

    def open_log(self):
        if not self._tk_fallback_enabled():
            return {"ok": False, "error": "FLUTTER_ONLY"}
        self._tk(lambda: (self.gui.log_window.deiconify(), self.gui.log_window.lift()), front=True)
        return True

    def get_log(self):
        """?묒뾽 濡쒓렇 蹂몃Ц? ?ъ슜?먭? ?댁뿀???뚮쭔 ?쎌뼱 蹂대궦??"""
        def read():
            widget = getattr(self.gui, "log_text", None)
            return widget.get("1.0", "end-1c") if widget is not None else ""

        return self._tk(read)

    def clear_log(self):
        """湲곕줉 李쎄낵 媛숈? 洹쒖튃?쇰줈, ?묒뾽 以묒뿉??濡쒓렇瑜?吏?곗? ?딅뒗??"""
        def clear():
            widget = getattr(self.gui, "log_text", None)
            if widget is not None and not self.gui.running:
                widget.delete("1.0", "end")
            return widget.get("1.0", "end-1c") if widget is not None else ""

        return self._tk(clear)

    def _pending_dialog(self):
        pending = getattr(self.gui, "_flutter_dialog", None)
        if not pending:
            with self._close_lock:
                return dict(self._close_request) if self._close_request else None
        return {key: pending[key] for key in (
            "id", "kind", "type", "title", "message", "confirm", "choices", "fields",
            "ok_label", "cancel_label", "styles", "areas", "result", "error"
        ) if key in pending}

    def get_pending_dialog(self):
        return self._tk(self._pending_dialog)

    def enable_close_guard(self):
        with self._close_lock:
            self._close_protocol = True
        return {"ok": True}

    def _cancel_close_timer(self):
        if self._close_timer is not None:
            self._close_timer.cancel()
            self._close_timer = None

    def acknowledge_close(self, identifier):
        # Explicitly acknowledge before opening save/discard dialogs. Polling
        # state alone does not prove Flutter can handle the close request.
        with self._close_lock:
            if self._close_request is None or self._close_request["id"] != identifier:
                return {"ok": False}
            self._cancel_close_timer()
        return {"ok": True}

    def _close_unanswered(self, identifier):
        with self._close_lock:
            if self._close_request is None or self._close_request["id"] != identifier:
                return
            # Delivery and the timeout race under the same lock.
            if self._close_timer is None:
                return
            self._close_request = None
            self._cancel_close_timer()
        self._force_close(native_event=False)

    def _force_close(self, *, native_event):
        """Release callers and stop owned work without waiting on JavaScript/Tk."""
        self.user_closing = native_event
        self._shutdown()

        def cleanup():
            from docfit_core.hwp_process import kill_owned
            try:
                kill_owned()
            finally:
                try:
                    self.gui.root.after(0, self.gui.root.destroy)
                except Exception:
                    logging.getLogger(__name__).exception("Could not stop the Tk message pump")

        threading.Thread(target=cleanup, name="webview-close-cleanup", daemon=True).start()
        return True

    def resolve_dialog(self, identifier, accepted, selection=None, fields=None):
        with self._close_lock:
            host_close = self._close_request is not None and self._close_request["id"] == identifier
            if host_close:
                if not isinstance(accepted, bool):
                    raise ValueError("醫낅즺 ?묐떟???뺤씤??二쇱꽭??")
                self._close_request = None
                self._cancel_close_timer()
        if host_close:
            if not accepted:
                return {"accepted": False}
            def finish_close():
                # The original OS event was vetoed; the watcher must now destroy
                # the host after Tk stops (unlike the legacy synchronous close).
                self.user_closing = False
                self.gui.醫낅즺()
                try:
                    closed = not bool(self.gui.root.winfo_exists())
                except Exception:
                    closed = True  # Tk commands no longer exist after destroy.
                return {"accepted": closed or bool(getattr(self.gui, "closing", False))}
            try:
                return self._tk(finish_close, timeout=None)
            except RuntimeError:
                if self.tk_stopped is not None and self.tk_stopped.is_set():
                    return {"accepted": True}
                raise
        def resolve():
            pending = getattr(self.gui, "_flutter_dialog", None)
            if pending and pending["id"] == identifier and isinstance(accepted, bool):
                allowed = {item["id"] for item in pending.get("choices", [])}
                if selection is not None and (not isinstance(selection, list) or any(item not in allowed for item in selection)):
                    raise ValueError("寃????ぉ???ㅼ떆 ?좏깮??二쇱꽭??")
                allowed_fields = {item["id"] for item in pending.get("fields", [])}
                if fields is not None and (not isinstance(fields, dict) or any(key not in allowed_fields or not isinstance(value, str) for key, value in fields.items())):
                    raise ValueError("寃??媛믪쓣 ?뺤씤??二쇱꽭??")
                pending["selection"] = selection if selection is not None else list(allowed)
                pending["values"] = fields or {}
                pending["answer"] = accepted
                pending["done"].set(True)
        self._tk(resolve)
        return {"ok": True}

    def flow_export(self, payload):
        from docfit_app.api_contract import ServiceError
        if not isinstance(payload, dict) or payload.get('format') not in {'png', 'hwpx'}:
            raise ServiceError('INVALID_INPUT', 'Choose PNG or HWPX.')
        return self.flow_editor('export_' + payload['format'], payload)

    def flow_editor(self, action, payload):
        from docfit_app.flow_service import FlowService
        from docfit_app.api_contract import ServiceError
        if not isinstance(payload, dict):
            raise ServiceError("INVALID_INPUT", "?낅젰???뺤씤??二쇱꽭??")
        store = self._tk(lambda: self.gui._以留??쒕퉬??).settings)
        service = FlowService(store._path.parent, store)
        if action == "copy_result":
            from docfit_app.clipboard_service import copy_result
            return self._tk(lambda: copy_result(payload))
        if action == "select_output":
            import uuid
            purpose = {"png": "flow_png", "hwpx": "flow_hwpx"}.get(payload.get("format"))
            if purpose is None:
                raise ServiceError("INVALID_INPUT", "??ν븷 ?뚯씪 ?뺤떇???뺤씤??二쇱꽭??")
            return self._file_dialogs.select_files(uuid.uuid4().hex, purpose, "save")
        if action == "export_png":
            import os
            import tempfile
            data = service.png_bytes(payload.get("base64"))
            raw_name = payload.get("name", "???ㅼ씠?닿렇??)
            name = "".join(c for c in str(raw_name)[:120] if c.isalnum() or c in " _-") or "???ㅼ씠?닿렇??
            selected = self._selection_path(payload, 'flow_png', 'output_selection_id')
            target = Path(selected)
            if target.suffix.lower() != ".png":
                raise ServiceError("INVALID_PATH", "PNG ?뚯씪濡???ν빐 二쇱꽭??")
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".tmp", delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, target)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            return {"path": str(target)}
        if action == "export_hwpx":
            # ???ㅼ씠?닿렇???몄쭛湲곗쓽 ?먮쫫?쑣룰린蹂??쒕? ??湲 HWPX 臾몄꽌濡???ν븳??docfit_core.table_builder).
            import os
            import sys
            import tempfile
            from docfit_core.table_builder import TableSpecError, build_table_hwpx, normalize
            from docfit_app.table_template_service import TableTemplateService
            spec = payload.get("spec")
            if not isinstance(spec, dict) or spec.get("kind") not in {"flow", "grid"}:
                raise ServiceError("TABLE_KIND_DISABLED", "?뚰뙆 踰꾩쟾?먯꽌???먮쫫?쒖? 湲곕낯 ?쒕쭔 留뚮뱾 ???덉뒿?덈떎.")
            try:
                normalize(spec)
            except TableSpecError as exc:
                raise ServiceError("INVALID_TABLE", str(exc)) from exc
            raw_name = payload.get("name", "??)
            name = "".join(c for c in str(raw_name)[:120] if c.isalnum() or c in " _-") or "??
            selected = self._selection_path(payload, 'flow_hwpx', 'output_selection_id')
            target = Path(selected)
            if target.suffix.lower() != ".hwpx":
                raise ServiceError("INVALID_PATH", "HWPX ?뚯씪濡???ν빐 二쇱꽭??")
            base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "resources" / "?쒖떇?덉떆" / "湲곕낯 ?쒖떇.hwpx"
            # 湲곕낯 ?쒕뒗 ?깆쓽 湲곕낯 ???쒖떇(以留?'??, ?덉떆 ???숈뒿 寃곌낵)??洹몃?濡??낇엺??
            basic = self._tk(lambda: TableTemplateService(self.gui._以留??쒕퉬??)).snapshot().get("preview"))
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".tmp", delete=False) as stream:
                    temporary = Path(stream.name)
                build_table_hwpx(spec, base, temporary, basic_style=basic)
                os.replace(temporary, target)
            except TableSpecError as exc:
                raise ServiceError("INVALID_TABLE", str(exc)) from exc
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            return {"path": str(target)}
        if action == "catalog_list":
            raise ServiceError("FEATURE_DISABLED", "???쒖떇 紐⑥쓬? ?꾩옱 ?뚰뙆 踰꾩쟾?먯꽌 鍮꾪솢?깊솕?섏뼱 ?덉뒿?덈떎.")
        if action == "catalog_copy":
            raise ServiceError("FEATURE_DISABLED", "???쒖떇 紐⑥쓬? ?꾩옱 ?뚰뙆 踰꾩쟾?먯꽌 鍮꾪솢?깊솕?섏뼱 ?덉뒿?덈떎.")
        if action == "catalog_export":
            raise ServiceError("FEATURE_DISABLED", "???쒖떇 紐⑥쓬? ?꾩옱 ?뚰뙆 踰꾩쟾?먯꽌 鍮꾪솢?깊솕?섏뼱 ?덉뒿?덈떎.")
        if action == "list":
            return service.list()
        if action == "load":
            return service.load(payload.get("id"))
        if action == "save":
            return service.save(payload.get("id"), payload.get("name"), payload.get("snapshot"), payload.get("revision"))
        if action == "delete":
            return service.delete(payload.get("id"))
        raise ServiceError("INVALID_ACTION", "?먮쫫???묒뾽???뺤씤??二쇱꽭??")

    def document_tool(self, name, payload):
        from docfit_app.document_tools_service import DocumentToolsService
        def execute():
            settings = self.gui._以留??쒕퉬??).settings
            service = DocumentToolsService(settings._path.parent)
            if name == "add_text":
                if self.gui.running:
                    from docfit_app.api_contract import ServiceError
                    raise ServiceError("JOB_RUNNING", "?묒뾽 ?꾨즺 ??臾몄꽌瑜?異붽???二쇱꽭??")
                result = service.command(name, payload)
                self.gui.?뚯씪異붽?(result["path"])
                return result
            return service.command(name, payload)
        if name != "add_text":
            folder = self._tk(lambda: self.gui._以留??쒕퉬??).settings._path.parent)
            return response(lambda: DocumentToolsService(folder).command(name, payload))
        return self._tk(lambda: response(execute))

    def stage_config(self, action, payload):
        def execute():
            if self.gui.running:
                return
            mode = self.gui.selected_mode.get()
            if mode not in self.gui.stage_choices:
                return  # ?뚯씪 蹂?섏뿉???몃? ?묒뾽???녿떎
            choices = self.gui.stage_choices[mode]
            if action == "all":
                if not isinstance(payload.get("enabled"), bool):
                    raise ValueError("?묒뾽 ?좏깮 媛믪쓣 ?뺤씤??二쇱꽭??")
                for key in choices:
                    choices[key] = payload["enabled"]
            elif action == "defaults":
                for key in choices:
                    choices[key] = default_choice(key, mode)
            else:
                raise ValueError("吏?먰븯吏 ?딅뒗 ?④퀎 紐낅졊?낅땲??")
            self._stages_changed(mode)
        self._tk(execute)
        return self.get_state()

    def format_profile(self, action, payload):
        from copy import deepcopy
        from hashlib import sha256
        import json
        import uuid
        from docfit_core import format_elements as elements
        from docfit_app.api_contract import ServiceError
        def execute():
            if not isinstance(payload, dict):
                raise ServiceError("INVALID_INPUT", "?쒖떇 ?낅젰???뺤씤??二쇱꽭??")
            identifier = payload.get("id", "")
            profiles = self._profile_state().profiles
            if identifier not in profiles:
                raise ServiceError("NOT_FOUND", "?쒖떇???ㅼ떆 ?좏깮??二쇱꽭??")
            original = profiles[identifier]
            revision = sha256(json.dumps(original, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            profile = deepcopy(original)
            analysis = profile.setdefault("element_analysis", {})
            if not analysis and not identifier:
                import sys
                source = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "resources" / "?쒖떇?덉떆" / "湲곕낯 ?쒖떇.hwpx"
                if source.is_file():
                    analysis = elements.analyze_format_elements(source)
                    profile["element_analysis"] = analysis
            if action in ("save", "restore"):
                if self.gui.running:
                    raise ServiceError("JOB_RUNNING", "?묒뾽 以묒뿉???쒖떇???섏젙?????놁뒿?덈떎.")
                if payload.get("revision") != revision:
                    raise ServiceError("PROFILE_CONFLICT", "?쒖떇??諛붾뚯뿀?듬땲?? ?ㅼ떆 遺덈윭? 二쇱꽭??")
                edits = payload.get("edits", [])
                if not isinstance(edits, list) or len(edits) > 2000:
                    raise ServiceError("INVALID_INPUT", "?쒖떇 ?섏젙 紐⑸줉???뺤씤??二쇱꽭??")
                if action == "restore" and not edits:
                    edits = [{"path": list(path), "key": key} for path, _, _ in elements.detail_nodes(analysis)
                             for key, item in elements.element_map(analysis, path).items()
                             if "analyzed" in item and elements.element_editable(key)]
                if edits:
                    try:
                        for edit in edits:
                            path, key = tuple(edit["path"]), edit["key"]
                            item = elements.element_map(analysis, path).get(key)
                            if item is None or not elements.element_editable(key):
                                raise ValueError("?섏젙?????녿뒗 ?붿냼?낅땲??")
                            value = (item.get("analyzed", item["value"]) if action == "restore"
                                     else elements.parse_value(key, edit["value"]))
                            elements.set_value(analysis, path, key, value)
                        elements.apply_to_profile(profile)
                    except (ValueError, KeyError, TypeError) as exc:
                        raise ServiceError("INVALID_STYLE", str(exc)) from exc
                    if not identifier:
                        identifier = uuid.uuid4().hex
                        profile["name"] = profile.get("name", "湲곕낯 ?쒖떇") + " (?ъ슜???섏젙)"
                    try:
                        self.gui._?쒖떇_?뚯씪_???identifier, profile)
                    except OSError as exc:
                        raise ServiceError("PROFILE_SAVE_FAILED", "?쒖떇 ?뚯씪????ν븯吏 紐삵뻽?듬땲??") from exc
                    profiles[identifier] = profile
                    self.gui._?쒖꽦_?쒖떇_?꾨줈?뚯씪 = identifier
                    self.gui._?꾨줈?뚯씪_紐⑸줉媛깆떊()
                    self.gui._?꾨줈?뚯씪_?좏깮()
                    self.invalidate_format_coverage(identifier)
                    revision = sha256(json.dumps(profile, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            elif action != "get":
                raise ServiceError("INVALID_ACTION", "吏?먰븯吏 ?딅뒗 ?쒖떇 紐낅졊?낅땲??")
            nodes = []
            for path, parent, label in elements.detail_nodes(analysis):
                fields = []
                for key, item in elements.element_map(analysis, path).items():
                    fields.append({"key": key, "label": elements.element_label(key),
                        "value": elements.format_value(key, item.get("value")),
                        "editable": elements.element_editable(key),
                        "choices": elements.element_choices(key)})
                if fields:
                    nodes.append({"path": list(path), "label": label, "fields": fields})
            return {"id": identifier, "name": profile.get("name"), "revision": revision,
                    "coverage": self._cached_coverage(identifier, analysis), "nodes": nodes}
        return self._tk(lambda: response(execute))

    def hangul_fonts(self, action, payload=None):
        """??湲???곕뒗 湲瑗???湲 ?꾩슜 ?대뜑 + Windows 湲瑗? 紐⑸줉怨? 誘몃━蹂닿린媛 ??湲瑗??뚯씪(base64).

        ???붾㈃? ??湲 ?꾩슜 湲瑗??대㉫紐낆“쨌?쒖뺨?뗭? ????紐⑤Ⅴ誘濡?誘몃━蹂닿린媛 ???뚯씪??諛쏆븘 FontFace濡??щ┛??
        """
        import base64
        from docfit_core import hangul_fonts
        if action == "list":
            return {"fonts": [{"name": e["name"], "source": e["source"]} for e in hangul_fonts.catalog()],
                    **hangul_fonts.summary()}
        if action == "data":
            name = str((payload or {}).get("name") or "")[:80]
            path = hangul_fonts.font_file(name)
            # 誘몃━蹂닿린?⑹씠???덈Т ??湲瑗??쒖뺨?뗭? ??24MB ??? 蹂대궡吏 ?딅뒗???泥?湲瑗대줈 洹몃┛??.
            if path is None or path.stat().st_size > 15 * 1024 * 1024:
                return {"name": name, "base64": None}
            return {"name": name, "base64": base64.b64encode(path.read_bytes()).decode("ascii")}
        raise ValueError("吏?먰븯吏 ?딅뒗 湲瑗??묒뾽?낅땲??")

    def idioms(self, action, payload):
        """?ㅼ젙??湲???곸슜援?룸낯臾??곸슜援?愿由?docfit_app.idiom_service). ??湲???쎈뒗 ?ъ슜???대뜑 ?뚯씪??怨좎튇??"""
        import sys
        from docfit_app.api_contract import ServiceError
        from docfit_app.idiom_service import IdiomService
        from docfit_core.format_samples import CHAR_IDIOM_FOLDER_NAME, app_subfolder
        from docfit_core.hwp_idioms import IDO_NAME

        def app_copy():
            folder_copy = app_subfolder(CHAR_IDIOM_FOLDER_NAME) / IDO_NAME
            bundled = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "resources" / IDO_NAME
            return folder_copy if folder_copy.is_file() else bundled

        def execute():
            service = IdiomService(app_copy=app_copy(), config_root=Path(r"C:\HWP_AUTODOCFIT"))
            data = dict(payload) if isinstance(payload, dict) else payload
            if action == "open_config":
                import os
                snapshot = service.snapshot()
                kind = str((data or {}).get("kind") or "text")
                key = "body" if kind == "body" else "text"
                path = Path(snapshot.get("config_files", {}).get(key, ""))
                if snapshot.get("source") != "hwpx" or not path.is_file():
                    raise ServiceError("INVALID_IDIOM", "?곸슜援?HWPX ?ㅼ젙 臾몄꽌瑜?李얠? 紐삵뻽?댁슂.")
                os.startfile(str(path))
                return snapshot
            if action == "apply_hwpx":
                from docfit_core.hwpx_idioms import create_template

                snapshot = service.snapshot()
                config = Path(snapshot.get("config_files", {}).get("body", ""))

                def convert_body(text, output):
                    if not config.is_file():
                        raise ServiceError("CONFIG_MISSING", "蹂몃Ц?곸슜援?HWPX ?ㅼ젙 臾몄꽌媛 ?놁뒿?덈떎.")
                    source = Path(output).with_suffix(".hwpx")
                    create_template(config, source, [{"key": "蹂몃Ц", "value": text}])
                    self._hwpx_to_hwp(source, output)

                return service.apply_hwpx(convert_body)
            if action == "open_body":
                import os
                key = str((data or {}).get("key") or "")
                snapshot = service.snapshot()
                if not snapshot.get("available") or key not in {item["key"] for item in snapshot["body"]}:
                    raise ServiceError("INVALID_IDIOM", "蹂몃Ц ?곸슜援щ? 李얠? 紐삵뻽?댁슂.")
                if snapshot.get("source") == "hwpx":
                    path = Path(snapshot["config_files"]["body"])
                    if not path.is_file():
                        raise ServiceError("INVALID_IDIOM", "蹂몃Ц?곸슜援?HWPX ?ㅼ젙 臾몄꽌瑜?李얠? 紐삵뻽?댁슂.")
                    os.startfile(str(path))
                    return snapshot
                from docfit_core.hwp_idioms import IdiomStore
                path = IdiomStore(snapshot["folder"]).body_path(key)
                if not path.is_file():
                    raise ServiceError("INVALID_IDIOM", "??蹂몃Ц ?곸슜援ъ쓽 臾몄꽌 ?뚯씪???놁뼱??")
                os.startfile(str(path))   # ??湲?먯꽌 ?댁뼱 ?댁슜??怨좎튇??
                return snapshot
            if action == "add_body" and isinstance(data, dict):
                if data.get('input_selection_id') or not data.get('path'):
                    data['path'] = self._selection_path(data, 'idioms')
                source = Path(str(data["path"]))
                if source.suffix.lower() == ".hwpx" and source.is_file():
                    # ??湲 蹂몃Ц ?곸슜援щ뒗 HWP 臾몄꽌????湲濡?諛붽퓭 ?ｋ뒗??
                    import tempfile
                    with tempfile.TemporaryDirectory(prefix="docfit_idiom_") as folder:
                        converted = Path(folder) / (source.stem + ".hwp")
                        self._hwpx_to_hwp(source, converted)
                        data["path"] = str(converted)
                        return service.command(action, data)
            return service.command(action, data)
        return response(execute)

    def _hwpx_to_hwp(self, source, target):
        """??湲 COM(蹂꾨룄 ?몄뒪?댁뒪)?쇰줈 HWPX瑜?HWP濡???ν븳??"""
        import pythoncom
        import win32com.client
        from docfit_core.format_samples import REGISTRY_VALUE
        pythoncom.CoInitialize()
        app = None
        try:
            app = win32com.client.DispatchEx("HWPFrame.HwpObject")
            app.RegisterModule("FilePathCheckDLL", REGISTRY_VALUE)
            try:
                app.Visible = False
            except Exception:
                pass
            if not app.Open(str(source), "HWPX", "forceopen:true") or not app.SaveAs(str(target), "HWP", ""):
                raise RuntimeError("??湲濡?HWP 臾몄꽌瑜?留뚮뱾吏 紐삵뻽?댁슂.")
        finally:
            if app is not None:
                try:
                    app.Clear(1)
                    app.Quit()
                except Exception:
                    pass
            pythoncom.CoUninitialize()

    def table_template(self, action, payload):
        from docfit_app.table_template_service import TableTemplateService
        def execute():
            if action != "get":
                self.gui._以留??쒕퉬??)._editable(self.gui.running)
            data = dict(payload) if isinstance(payload, dict) else payload
            if action == 'learn' and isinstance(data, dict):
                if data.get('input_selection_id') or not data.get('path'):
                    data['path'] = self._selection_path(data, 'table_template')
            result = TableTemplateService(self.gui._以留??쒕퉬??)).command(
                action, data, running=self.gui.running)
            return result
        return self._tk(lambda: response(execute))

    def _table_units_hwp(self):
        """?깆씠 ?곕뒗 諛⑹떇 洹몃?濡??낅┰ ??湲??留뚮뱾怨?蹂댁븞 紐⑤뱢???깅줉???④릿??"""
        # 2.0.5 ?ㅻ쪟: ?쒖옉??鍮좊Ⅴ寃??섎젮怨????由?媛앹껜(PendingGui)??type???쎌뼱 ??湲 蹂듭궗媛 紐⑤몢 ?ㅽ뙣?덈떎.
        namespace = type(_real_gui(self.gui)).?뚯씪?щ㎎_蹂寃??쒖옉.__globals__
        app = namespace["?쒓?_COM_?몄뒪?댁뒪_?앹꽦"](?낅┰=True)
        try:
            registered = app.RegisterModule(namespace["REGISTER_MODULE_NAME"], namespace["REGISTER_MODULE_VALUE"])
        except Exception:
            registered = False
        if registered is False:
            try:
                app.Quit()   # ?깅줉???ㅽ뙣?대룄 ?⑥? ??湲???⑥? ?딄쾶 ?ル뒗??
            except Exception:
                pass
            raise RuntimeError("?깆뿉 ?ы븿????湲 蹂댁븞 紐⑤뱢???깅줉?섏? 紐삵뻽?듬땲??")
        try:
            app.XHwpWindows.Item(0).Visible = False
        except Exception:
            pass
        return app

    def hwp_bulk(self, action, payload=None):
        """HWP ??HWPX ?쇨큵 蹂??2.0.7): drives 쨌 start 쨌 stop 쨌 status 쨌 open_report 쨌 show_report."""
        from docfit_core import hwp_bulk as bulk
        payload = payload if isinstance(payload, dict) else {}
        state = getattr(self, "_bulk_state", None)
        running = bool(state and state.phase in {"scan", "convert"})

        def status(ok=True, message=""):
            return {"ok": ok, "message": message, "bulk": state.as_dict() if state else None}
        if action == "drives":
            return {"ok": True, "drives": bulk.local_drives()}
        if action == "status":
            return status()
        if action == "stop":
            stop = getattr(self, "_bulk_stop", None)
            if stop is not None:
                stop.set()
            return status()
        if action in {"open_report", "show_report"}:
            path = state.report if state else ""
            opener = self._open_path if action == "open_report" else self._reveal
            self._tk(lambda: opener(path, "蹂??寃곌낵?쒓? ?꾩쭅 ?놁뒿?덈떎."))
            return status()
        if action != "start":
            return status(False, "吏?먰븯吏 ?딅뒗 紐낅졊?낅땲??")
        if running:
            return status(False, "HWPX ?쇨큵 蹂?섏씠 ?대? 吏꾪뻾 以묒엯?덈떎.")
        if self._tk(lambda: self.gui.running):
            return status(False, "?ㅻⅨ 臾몄꽌 ?묒뾽???앸궃 ???쒖옉??二쇱꽭??")
        roots, passwords = payload.get("roots"), payload.get("passwords") or []
        if (not isinstance(roots, list) or not 1 <= len(roots) <= 20 or not isinstance(passwords, list)
                or len(passwords) > 20 or not all(isinstance(x, str) and 0 < len(x) <= 128 for x in passwords)):
            return status(False, "李얠쓣 ?꾩튂? ?뷀샇 紐⑸줉???뺤씤??二쇱꽭??")
        clean = []
        for value in roots:
            path = Path(str(value or ""))
            if not path.is_absolute() or path.is_symlink() or not (
                    path.is_dir() or (path.is_file() and path.suffix.lower() == ".hwp")):
                return status(False, f"李얠쓣 ?꾩튂瑜??????놁뒿?덈떎: {value}")
            clean.append(path.resolve())
        documents = Path(os.path.expanduser("~")) / "Documents"
        report_dir = (documents if documents.is_dir() else Path(tempfile.gettempdir())) / "HWP_AutoDocFit" / "HWPX蹂??寃곌낵??
        state = self._bulk_state = bulk.BulkState(phase="scan")
        stop = self._bulk_stop = threading.Event()

        def factory():
            import pythoncom
            pythoncom.CoInitialize()
            return self._table_units_hwp()

        def work():
            try:
                bulk.run_bulk(clean, app_factory=factory, state=state, stop=stop, passwords=list(passwords),
                              report_dir=report_dir, recursive=payload.get("recursive", True) is not False)
            except Exception as exc:  # ??湲 ?놁쓬 ?? ?붾㈃???댁쑀瑜?蹂댁씤??
                logging.getLogger(__name__).warning("HWPX ?쇨큵 蹂???ㅽ뙣", exc_info=True)
                state.error, state.phase = str(exc), "error"
            finally:
                passwords.clear()  # ?뷀샇???묒뾽???앸굹硫?踰꾨┛????Β룰린濡앺븯吏 ?딆쓬).
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
        threading.Thread(target=work, name="hwp-bulk", daemon=True).start()
        return status()

    def _file_rename_service(self):
        service = getattr(self, "_rename_service", None)
        if service is None:
            from docfit_app.file_rename_service import FileRenameService
            folder = self._tk(lambda: getattr(self.gui, "_以留??쒕퉬??)().settings._path.parent)
            service = self._rename_service = FileRenameService(folder, dialogs=self._file_dialogs)
        return service

    def _timemachine_service(self):
        service = getattr(self, "_timemachine_service_instance", None)
        if service is None:
            from docfit_app.timemachine_service import TimemachineService
            folder = self._tk(lambda: getattr(self.gui, "_以留??쒕퉬??)().settings._path.parent)
            service = self._timemachine_service_instance = TimemachineService(
                folder, feature_api=self._timemachine_send_to_feature
            )
        return service

    def _timemachine_send_to_feature(self, feature, paths):
        """??꾨㉧?좎뿉??蹂대궦 ?뱀씤???뚯씪 紐⑸줉???ㅼ젣 湲곕뒫 ?湲곗뿴???곌껐?쒕떎."""
        if feature == "rename_batch":
            return self._file_rename_service().add_paths(paths)
        if feature in ("convert", "document_edit"):
            if len(paths) > 1:
                return {"ok": False, "code": "FEATURE_LIMIT", "message": "臾몄꽌?몄쭛/?뚯씪蹂?섏? ??踰덉뿉 ???뚯씪留?吏?먰빀?덈떎."}
            def add_to_gui():
                if self.gui.running:
                    return {"ok": False, "code": "JOB_RUNNING", "message": "臾몄꽌 ?묒뾽??吏꾪뻾 以묒엯?덈떎."}
                if feature == "convert":
                    self.gui.selected_mode.set("file_format")
                    self._mode_selected()
                else:
                    if self.gui.selected_mode.get() == "file_format":
                        self.gui.selected_mode.set("spacing")
                        self._mode_selected()
                added = self.add_paths(paths, from_drop=False)
                if not added:
                    return {"ok": False, "code": "FEATURE_FAILED", "message": "?뚯씪??異붽??섏? 紐삵뻽?듬땲??"}
                self.gui.status_var.set(f"??꾨㉧?좎뿉??臾몄꽌 異붽? 쨌 珥?{len(self.gui.files)}媛?)
                self._update_document_hints()
                return {"ok": True}
            return self._tk(add_to_gui)
        return {"ok": False, "code": "FEATURE_UNAVAILABLE", "message": "?대떦 湲곕뒫???ъ슜?????놁뒿?덈떎."}

    def timemachine(self, action, payload=None):
        """??꾨㉧???붾㈃ 紐낅졊??泥섎━?쒕떎."""
        try:
            return self._timemachine_service().command(action, payload)
        except Exception:
            logging.getLogger(__name__).exception("??꾨㉧??泥섎━ ?ㅽ뙣")
            return {"ok": False, "code": "TM_FAILED", "message": "??꾨㉧???묒뾽???꾨즺?섏? 紐삵뻽?듬땲??"}

    def kclip(self, action, payload=None):
        """紐쎈븙?대┰蹂대뱶: ?곸＜ ?꾨줈洹몃옩(kagent.exe) 耳쒓린쨌?꾧린? 紐⑸줉쨌?ㅼ젙(?뚯씠??紐낅졊)."""
        try:
            from docfit_app.kclip_service import KClipService
            service = getattr(self, "_kclip_service", None)
            if service is None:
                service = self._kclip_service = KClipService()
            return service.command(action, payload)
        except Exception as exc:
            logging.getLogger(__name__).warning("紐쎈븙?대┰蹂대뱶 泥섎━ ?ㅽ뙣", exc_info=True)
            return {"ok": False, "message": str(exc) or "紐쎈븙?대┰蹂대뱶瑜?泥섎━?섏? 紐삵뻽?듬땲??"}

    def file_rename(self, action, payload=None):
        """?뚯씪?대쫫 ?? 紐⑸줉쨌誘몃━蹂닿린쨌?곸슜쨌?섎룎由ш린(寃쎈줈???몄뒪?몄뿉留??붾떎)."""
        try:
            return self._file_rename_service().command(action, payload)
        except Exception as exc:
            logging.getLogger(__name__).warning("?뚯씪?대쫫 泥섎━ ?ㅽ뙣", exc_info=True)
            return {"ok": False, "message": str(exc) or "?대쫫 諛붽씀湲곕? 泥섎━?섏? 紐삵뻽?듬땲??"}

    def new_document(self, action, payload=None):
        from docfit_app.new_document_service import create_copy, user_documents
        payload = payload if isinstance(payload, dict) else {}
        def execute():
            profiles = self._profile_state().profiles or {}
            def snapshot_path(identifier):
                try:
                    pair = self.gui._?쒖떇?덉떆_寃쎈줈(identifier)
                    source = Path(pair[0])
                    return source if source.is_file() else None
                except Exception:
                    return None
            if action == 'list':
                items = []
                for identifier, profile in profiles.items():
                    if not isinstance(profile, dict): continue
                    source = snapshot_path(identifier)
                    if source:
                        preview = None
                        try:
                            pair = self.gui._?쒖떇?덉떆_寃쎈줈(identifier)
                            candidates = [Path(pair[1])] if len(pair) > 1 and pair[1] else []
                            candidates += [source.with_suffix('.png'), source.with_name(source.stem + '_preview.png')]
                            preview = next((str(item.resolve()) for item in candidates if item.is_file()), None)
                        except Exception:
                            pass
                        items.append({'id': str(identifier), 'name': str(profile.get('name') or source.stem), 'preview': preview})
                return {'ok': True, 'items': items}
            if action != 'create': return {'ok': False, 'message': '吏?먰븯吏 ?딅뒗 ?덈Ц??紐낅졊?낅땲??'}
            profile = profiles.get(payload.get('id'))
            if not isinstance(profile, dict): return {'ok': False, 'message': '?쒖떇???ㅼ떆 ?좏깮??二쇱꽭??'}
            source = snapshot_path(payload.get('id'))
            if not source: return {'ok': False, 'message': '???쒖떇???먮낯 HWPX 寃쎈줈瑜??뺤씤?????놁뒿?덈떎.'}
            target = create_copy(source, user_documents(), profile.get('name'))
            try: os.startfile(str(target))
            except OSError as exc:
                target.unlink(missing_ok=True)
                return {'ok': False, 'message': f'??湲?먯꽌 臾몄꽌瑜??댁? 紐삵뻽?듬땲?? {exc}'}
            return {'ok': True, 'path': str(target), 'name': target.name}
        return self._tk(execute)

    def sidebar_mode(self, enabled):
        from docfit_app.sidebar_mode import SidebarModeController
        def execute():
            config = self._configuration().snapshot(running=self.gui.running)
            values = config.get('values', {})
            if not values.get('developer_mode', False):
                return {'ok': False, 'message': '?ъ씠?쒕찓??紐⑤뱶??媛쒕컻??紐⑤뱶?먯꽌留??ъ슜?????덉뒿?덈떎.'}
            if self.sidebar_controller is None:
                if self.window is None:
                    return {'ok': False, 'message': '李쎌씠 ?꾩쭅 以鍮꾨릺吏 ?딆븯?듬땲??'}
                self.sidebar_controller = SidebarModeController(
                    _Win32WindowApi(), _PyWebViewWindow(self.window, self.gui._以留??쒕퉬??).settings, lambda: self._saved_window), True,
                    values.get('sidebar_mode_side', 'right'))
            else:
                self.sidebar_controller.developer_mode = True
                self.sidebar_controller.saved = self._saved_window
            result = self.sidebar_controller.toggle(bool(enabled))
            self.sidebar_active = bool(enabled)
            return result
        try:
            return self._tk(execute)
        except Exception as exc:
            return {'ok': False, 'message': str(exc)}

    def always_on_top(self, enabled):
        def execute():
            config = self._configuration().snapshot(running=self.gui.running)
            if not config.get('values', {}).get('developer_mode', False):
                return {'ok': False, 'message': '??긽 ???ㅼ젙? 媛쒕컻??紐⑤뱶?먯꽌留??ъ슜?????덉뒿?덈떎.'}
            self.gui._以留??쒕퉬??).settings.update(lambda current: current.update({'always_on_top': bool(enabled)}))
            if self.window is not None:
                self.window.set_on_top(bool(enabled))
            return {'ok': True, 'enabled': bool(enabled)}
        return self._tk(execute)

    def _drain_rename_paths(self):
        """?먯깋湲?蹂대궡湲?--rename)濡?諛쏆? 寃쎈줈瑜?紐⑸줉???ｊ퀬, ?붾㈃????쓣 ?대룄濡?True瑜??뚮젮以??
        ?쒖옉 ???몄텧???섎━吏 ?딆쑝???대? ?ㅺ????곹깭 議고쉶???밸뒗??"""
        queue = getattr(self.gui, "_rename_startup_paths", None)
        if not isinstance(queue, list) or not queue:
            return False
        paths, queue[:] = list(queue), []
        try:
            self._file_rename_service().add_paths(paths[:10000])
        except Exception:
            logging.getLogger(__name__).exception("rename startup paths failed")
        window = self.window
        if window is not None and hasattr(window, "run_js"):
            # ?곹깭 議고쉶??Tk ?ㅻ젅?쒖뿉???뚯븘 ?붾㈃ ?몄텧??湲곕떎由щ㈃ ?쒕줈 留됲엺??
            threading.Thread(
                target=window.run_js,
                args=("window.dispatchEvent(new Event('docfit-rename-files-dropped'));",),
                daemon=True,
            ).start()
        return True

    def table_sketch(self, action, payload=None):
        """Table sketch conversion, storage and clipboard API."""
        from docfit_app.table_sketch_service import TableSketchService
        try:
            if action == "copy" and self.gui.running:
                return {"ok": False, "message": "臾몄꽌 ?묒뾽???앸궃 ???ㅼ떆 ?뚮윭 二쇱꽭??"}
            folder = self._tk(lambda: getattr(self.gui, "_以留??쒕퉬??)().settings._path.parent)
            if action == "take_drop":
                dropped, self._sketch_drop = getattr(self, "_sketch_drop", None), None
                return dropped or {"ok": False, "message": "?볦? 洹몃┝???놁뒿?덈떎."}
            if action == "clipboard_image":
                from docfit_app import sketch_image_input
                try:
                    return sketch_image_input.from_clipboard()
                except Exception as exc:
                    return {"ok": False, "message": str(exc) or "?대┰蹂대뱶 ?ъ쭊???쎌? 紐삵뻽?듬땲??"}
            if action != "copy":
                return TableSketchService(folder).command(action, payload)
            if not _TABLE_UNITS_COM_LOCK.acquire(blocking=False):
                return {"ok": False, "message": "???묒뾽??吏꾪뻾 以묒엯?덈떎. ?좎떆 ???ㅼ떆 ?뚮윭 二쇱꽭??"}
            try:
                return TableSketchService(folder, self._table_units_hwp).command(action, payload)
            finally:
                _TABLE_UNITS_COM_LOCK.release()
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    def table_units(self, action, payload=None):
        if action != 'copy':
            return self._table_units_command(action, payload)

    def library_drop(self, paths, x, y, box_id, space=None):
        """OS 파일 끌어놓기: 경로 목록을 item_add 요청으로 순차 등록한다.

        space를 주면(core/basis/reference/temp) x, y는 그 사분면 캔버스의 로컬 픽셀 좌표
        (Flutter globalToLocal 결과, 0 이상 유한 실수)이며 item_add에 그대로 전달한다.
        space를 생략하면 x, y는 보드 전체 0~1 정규화 좌표로 보고 사분면(0.5 경계는
        오른쪽/아래)만 판정하며 item_add에는 받은 값을 전달한다.
        box_id는 정수 또는 정수 문자열만 허용하며 int로 변환해 전달한다.
        """
        import math
        if os.environ.get("DOCFIT_LIBRARY_BRIDGE", "").strip().lower() not in {"1", "true", "yes", "on"}:
            return {"ok": False, "message": "자료함 브리지가 비활성화되어 있습니다."}
        valid_spaces = {"core", "basis", "reference", "temp"}
        if space is not None and space not in valid_spaces:
            return {"ok": False, "message": "자료함 공간이 올바르지 않습니다."}
        try:
            if isinstance(x, bool) or isinstance(y, bool):
                raise ValueError("bool")
            norm_x = float(x)
            norm_y = float(y)
            if not (math.isfinite(norm_x) and math.isfinite(norm_y) and norm_x >= 0.0 and norm_y >= 0.0):
                raise ValueError("range")
            if space is None and not (norm_x <= 1.0 and norm_y <= 1.0):
                raise ValueError("range")
        except (TypeError, ValueError):
            return {"ok": False, "message": "놓은 위치 좌표가 올바르지 않습니다."}
        try:
            if isinstance(box_id, bool) or not isinstance(box_id, (str, int)):
                raise ValueError("type")
            box = int(box_id.strip() if isinstance(box_id, str) else box_id)
        except ValueError:
            return {"ok": False, "message": "자료함 번호가 올바르지 않습니다."}
        added, skipped, failed = [], [], []
        if paths is None:
            items = []
        elif isinstance(paths, (str, bytes, os.PathLike)):
            items = [paths]
        else:
            try:
                items = list(paths)
            except TypeError:
                return {"ok": False, "added": added, "skipped": skipped,
                        "failed": [{"path": str(paths), "message": "경로 목록 형식이 올바르지 않습니다."}]}
        if space is None:
            left = norm_x < 0.5
            top = norm_y < 0.5
            space = {(True, True): "core", (False, True): "basis",
                     (True, False): "reference", (False, False): "temp"}[(left, top)]
        seen = set()
        for raw in items:
            text = str(raw)
            try:
                text = os.fspath(raw)
                if not isinstance(text, str):
                    text = os.fsdecode(text)
                if not text.strip():
                    continue
                path = Path(text)
                if path.is_file():
                    kind = "file"
                elif path.is_dir():
                    kind = "folder"
                else:
                    failed.append({"path": text, "message": "존재하지 않거나 파일·폴더가 아닌 경로입니다."})
                    continue
                key = os.path.normcase(str(path.resolve(strict=True)))
            except (TypeError, ValueError, OSError, RuntimeError) as exc:
                failed.append({"path": text, "message": str(exc) or "경로 형식이 올바르지 않습니다."})
                continue
            if key in seen:
                skipped.append({"path": text, "message": "중복 경로"})
                continue
            seen.add(key)
            result = self.library({
                "cmd": "item_add",
                "box_id": box,
                "kind": kind,
                "source_path": str(path),
                "display_name": path.name,
                "space": space,
                "x": norm_x,
                "y": norm_y,
            })
            if isinstance(result, dict) and result.get("ok") is True:
                added.append(result)
            else:
                message = result.get("message", "") if isinstance(result, dict) else str(result)
                failed.append({"path": text, "message": message})
        return {"ok": not failed, "added": added, "skipped": skipped, "failed": failed}

    def library(self, request):
        """Forward one allowlisted library JSON request when the opt-in flag is set."""
        if os.environ.get("DOCFIT_LIBRARY_BRIDGE", "").strip().lower() not in {"1", "true", "yes", "on"}:
            return {"ok": False, "message": "?먮즺??釉뚮━吏媛 鍮꾪솢?깊솕?섏뼱 ?덉뒿?덈떎."}
        if self._library_bridge is None:
            from docfit_app.library_bridge import LibraryBridge
            self._library_bridge = LibraryBridge()
        try:
            return self._library_bridge.request(request)
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
        def execute():
            manager = self._jobs()
            identifier = manager.begin('table_copy', payload)
            manager.report(identifier, 'started', {})
            try:
                result = self._table_units_command(action, payload)
                if result.get('ok'):
                    manager.report(identifier, 'item_done', result.get('data') or {})
                    manager.report(identifier, 'done', result.get('data') or {})
                else:
                    manager.report(identifier, 'failed', result.get('error') or {})
                return result
            except Exception as exc:
                manager.report(identifier, 'failed', {'code':'JOB_FAILED', 'message':str(exc)})
                raise
        # 湲곗〈 ?묐떟 遊됲닾瑜?洹몃?濡??좎??쒕떎.
        result = response(execute)
        return result['data'] if result['ok'] else result

    def _table_units_command(self, action, payload=None):
        """???쒗뵆由? ?ㅻ깄??紐⑸줉쨌?뺣낫?⑥쐞 誘몃━蹂닿린쨌??湲 遺숈뿬?ｊ린??蹂듭궗(2026-10-22).

        ??湲???곕뒗 ?ㅻ깄?력룸났?щ뒗 ?쒓컙??嫄몃━誘濡?Tk ?붾㈃ ?ㅻ젅?쒓? ?꾨땲???몄텧 ?ㅻ젅?쒖뿉???곕줈 COM???곕떎.
        """
        from docfit_app.table_units_service import TableUnitsService
        from docfit_app.api_contract import ServiceError

        def execute():
            if action in ("copy", "thumbnails") and self.gui.running:
                raise ServiceError("JOB_RUNNING", "臾몄꽌 ?묒뾽???앸궃 ???ㅼ떆 ?뚮윭 二쇱꽭??")
            if action not in ("copy", "thumbnails"):
                settings = self._tk(lambda: self.gui._以留??쒕퉬??).settings)
                return TableUnitsService(settings=settings).command(action, payload)
            # ?ㅻ깄???앹꽦 以묒뿉 蹂듭궗媛 寃뱀튂硫???湲쨌?대┰蹂대뱶媛 ?됲궎誘濡???踰덉뿉 ?섎굹留??쒕떎.
            if not _TABLE_UNITS_COM_LOCK.acquire(blocking=False):
                raise ServiceError("BUSY", "???쒗뵆由??묒뾽??吏꾪뻾 以묒씠?먯슂. ?앸궃 ???ㅼ떆 ?뚮윭 二쇱꽭??")
            import pythoncom
            try:
                pythoncom.CoInitialize()
                try:
                    settings = self._tk(lambda: self.gui._以留??쒕퉬??).settings)
                    return TableUnitsService(self._table_units_hwp, settings=settings).command(action, payload)
                finally:
                    pythoncom.CoUninitialize()
            finally:
                _TABLE_UNITS_COM_LOCK.release()
        return response(execute)

    def get_abbreviations(self):
        return self._tk(lambda: response(lambda: self.gui._以留??쒕퉬??).snapshot(running=self.gui.running)))

    def save_abbreviation(self, key, kind, value, original_key=""):
        return self._tk(lambda: response(lambda: self.gui._以留??쒕퉬??).save(
            key, kind, value, original_key, running=self.gui.running)))

    def delete_abbreviation(self, key):
        return self._tk(lambda: response(lambda: self.gui._以留??쒕퉬??).delete(key, running=self.gui.running)))

    def set_abbreviation_defaults(self, enabled):
        return self._tk(lambda: response(lambda: self.gui._以留??쒕퉬??).set_defaults(enabled, running=self.gui.running)))

    def abbreviation_document(self, action):
        """以留?愿由?HWPX 臾몄꽌 留뚮뱾湲걔룹뿴湲걔룸떎???쎄린쨌異쒖쿂 ?꾪솚(1.80.3)."""
        return self._tk(lambda: response(lambda: self.gui._以留??쒕퉬??).document_command(
            action, running=self.gui.running)))

    def open_results(self):
        self._tk(self.gui._寃곌낵?뚯씪_?닿린, timeout=None, front=True)
        return True

    def _result_path(self, index):
        try:
            return getattr(self.gui, "_寃곌낵紐⑸줉", [])[int(index)].get("寃곌낵", "")
        except (IndexError, TypeError, ValueError):
            return ""

    def open_result(self, index):
        """寃곌낵 ?뚯씪 ?섎굹瑜??곌껐???꾨줈洹몃옩(??湲)?쇰줈 ?곕떎."""
        def open_one():
            path = self._result_path(index)
            if path and os.path.isfile(path):
                self.gui._寃쎈줈_?닿린(path)
            else:
                self.gui.status_var.set("寃곌낵 ?뚯씪??李얠쓣 ???놁뒿?덈떎. ??린嫄곕굹 吏?곗? ?딆븯?붿? ?뺤씤??二쇱꽭??")

        self._tk(open_one, timeout=None, front=True)
        return self.get_state()

    def _reveal(self, path, missing):
        if path and os.path.isfile(path) and os.name == "nt":
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        elif path and os.path.isdir(os.path.dirname(path)):
            self.gui._寃쎈줈_?닿린(os.path.dirname(path))
        else:
            self.gui.status_var.set(missing)

    def _open_path(self, path, missing):
        if path and os.path.isfile(path):
            self.gui._寃쎈줈_?닿린(path)
        else:
            self.gui.status_var.set(missing)

    def _source_path(self, index):
        try:
            return str(list(self.gui.files)[int(index)])
        except (IndexError, TypeError, ValueError):
            return ""

    def open_source_file(self, index):
        """?뚯씪蹂???붾㈃ ?ㅻⅨ履?踰꾪듉 硫붾돱: ?щ┛ ?뚯씪???곌껐???꾨줈洹몃옩?쇰줈 ?곕떎(2.0.7)."""
        self._tk(lambda: self._open_path(self._source_path(index), "?뚯씪??李얠쓣 ???놁뒿?덈떎."), timeout=None, front=True)
        return self.get_state()

    def show_source_file(self, index):
        """?щ┛ ?뚯씪???먯깋湲곗뿉??怨⑤씪 蹂댁씤??2.0.7)."""
        self._tk(lambda: self._reveal(self._source_path(index), "?뚯씪 ?대뜑瑜?李얠쓣 ???놁뒿?덈떎."), timeout=None, front=True)
        return self.get_state()

    def open_result_source(self, index):
        """寃곌낵???먮낯 ?뚯씪???곕떎(2.0.7)."""
        def source():
            try:
                return getattr(self.gui, "_寃곌낵紐⑸줉", [])[int(index)].get("?먮낯", "")
            except (IndexError, TypeError, ValueError, AttributeError):
                return ""
        self._tk(lambda: self._open_path(source(), "?먮낯 ?뚯씪??李얠쓣 ???놁뒿?덈떎."), timeout=None, front=True)
        return self.get_state()

    def show_result(self, index):
        """?먯깋湲곗뿉??寃곌낵 ?뚯씪???덈뒗 ?대뜑瑜??닿퀬 洹??뚯씪???좏깮???붾떎."""
        def reveal():
            path = self._result_path(index)
            if path and os.path.isfile(path) and os.name == "nt":
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            elif path and os.path.isdir(os.path.dirname(path)):
                self.gui._寃쎈줈_?닿린(os.path.dirname(path))
            else:
                self.gui.status_var.set("寃곌낵 ?대뜑瑜?李얠쓣 ???놁뒿?덈떎.")

        self._tk(reveal, timeout=None, front=True)
        return self.get_state()

    def open_diff(self, index=0):
        """?먮낯쨌寃곌낵??湲???섎???鍮꾧탳??HTML??留뚮뱾??湲곕낯 釉뚮씪?곗?濡??곕떎(2.0.6).

        ?덉쟾?먮뒗 ?낅┰ ??湲 鍮꾧탳 酉곗뼱媛 遺숈쓣 ?뚭퉴吏 '以鍮?以? ?ㅻ쪟留?蹂댁????ъ슜??蹂닿퀬)."""
        if self._tk_fallback_enabled():
            self._tk(self.gui.鍮꾧탳李?以鍮? timeout=None, front=True)
            return {**self.get_state(), "ok": True, "tk_fallback": True}
        from docfit_app.result_compare import build_report
        try:
            item = getattr(self.gui, "_寃곌낵紐⑸줉", [])[int(index)]
            original, result = item.get("?먮낯", ""), item.get("寃곌낵", "")
        except (IndexError, TypeError, ValueError, AttributeError):
            original = result = ""
        if not (original and os.path.isfile(original) and result and os.path.isfile(result)):
            return {"ok": False, "code": "DIFF_FILE_MISSING",
                    "error": "?먮낯?대굹 寃곌낵 ?뚯씪??李얠쓣 ???놁뼱 鍮꾧탳?섏? 紐삵뻽?댁슂. ??린嫄곕굹 吏?곗? ?딆븯?붿? ?뺤씤??二쇱꽭??"}
        try:
            folder = Path(tempfile.gettempdir()) / "HWP_AutoDocFit_compare"
            report = build_report(original, result, folder / f"鍮꾧탳_{Path(result).stem[:60]}.html")
        except Exception as exc:
            return {"ok": False, "code": "DIFF_UNSUPPORTED", "error": str(exc) or "鍮꾧탳?섏? 紐삵뻽?댁슂."}
        opener = getattr(os, "startfile", None)
        if opener:
            opener(str(report))   # noqa: S606 ???깆씠 留뚮뱺 HTML??湲곕낯 釉뚮씪?곗?濡??곕떎
        return {**self.get_state(), "ok": True, "report": str(report)}

    def compare_result(self, index=0):
        return self.open_diff(index)

    def launch_external_hwp_diff(self, index=0):
        return self.open_diff(index)

    def _stages_changed(self, mode):
        """?몃? ?묒뾽??諛붽씔 ??洹?移대뱶 ?듭뀡(???쒖쇅쨌?섏씠吏 留욎땄 ?쒖쇅 ?????몃? ?묒뾽??留욎텣??"""
        if hasattr(self.gui, "_?몃??묒뾽_?듭뀡_留욎땄"):
            self.gui._?몃??묒뾽_?듭뀡_留욎땄(mode)

    def set_stage(self, key, on):
        """?꾩옱 ?묒뾽 ?좏삎???몃? ?묒뾽 ?섎굹瑜?耳쒓퀬 ?덈떎. 湲곕낯媛???μ쓣 耳??좏삎?대㈃ 諛붾줈 ??ν븳??

        移대뱶 ?듭뀡怨??곕룞???묒뾽?대㈃ ?듭뀡??諛붾먮떎(?? ???묒뾽???섎굹?쇰룄 耳쒕㈃ '???쒖쇅'媛 爰쇱쭊??.
        """
        def update():
            gui = self.gui
            mode = gui.selected_mode.get()
            if gui.running or key not in gui.stage_choices.get(mode, {}):
                return
            gui.stage_choices[mode][key] = bool(on)
            if gui._?몃??묒뾽_湲곕낯???get(mode):
                gui._?몃??묒뾽_湲곕낯媛????mode)
            self._stages_changed(mode)
            gui._?붿빟媛깆떊()

        self._tk(update)
        return self.get_state()

    def reset_stages(self):
        """?꾩옱 ?묒뾽 ?좏삎???몃? ?묒뾽??泥섏쓬 湲곕낯媛믪쑝濡??섎룎由곕떎(移대뱶 ?듭뀡??洹몄뿉 留욎텣??."""
        def reset():
            gui = self.gui
            mode = gui.selected_mode.get()
            if gui.running or mode not in gui.stage_choices:
                return
            gui.stage_choices[mode] = {key: default_choice(key, mode) for key, _ in stages_for_mode(mode)}
            if gui._?몃??묒뾽_湲곕낯???get(mode):
                gui._?몃??묒뾽_湲곕낯媛????mode)
            self._stages_changed(mode)
            gui._?붿빟媛깆떊()

        self._tk(reset)
        return self.get_state()

    def set_stage_default(self, save):
        """?꾩옱 援ъ꽦???ㅼ쓬 ?ㅽ뻾?먮룄 ?몄? ?뺥븳?? ?꾨㈃ ??ν븳 援ъ꽦??吏??泥섏쓬 湲곕낯媛믪쑝濡??쒖옉?쒕떎."""
        def update():
            if not self.gui.running:
                self.gui._?몃??묒뾽_湲곕낯媛????self.gui.selected_mode.get(), bool(save))

        self._tk(update)
        return self.get_state()

    def set_profile(self, identifier):
        """?쒖떇 ?곸슜?????쒖떇(?꾨줈?뚯씪)??怨좊Ⅸ?? 湲곗〈 肄ㅻ낫 ?좏깮怨?媛숈? 寃쎈줈濡?諛섏쁺?쒕떎."""
        def select():
            gui = self.gui
            ids = list(self._profile_state().profile_ids or [])
            if not ids and hasattr(gui, "_?꾨줈?뚯씪_紐⑸줉媛깆떊"):
                gui._?꾨줈?뚯씪_紐⑸줉媛깆떊()   # ?쒖떇 ?쒖꽌媛 ?꾩쭅 ?놁쑝硫?癒쇱? 梨꾩슫???놁쑝硫?紐⑤뱺 ?좏깮??臾댁떆??
                ids = list(self._profile_state().profile_ids or [])
            combo = getattr(gui, "main_profile_combo", None)
            before = self._profile_state().active_profile_id
            if gui.running or identifier not in ids or combo is None:
                _profile_trace(f"臾댁떆 ?붿껌={identifier!r} ?묒뾽以?{gui.running} 紐⑸줉={ids} 肄ㅻ낫={combo is not None}")
                return
            combo.current(ids.index(identifier))
            gui._?꾨줈?뚯씪_?좏깮(SimpleNamespace(widget=combo))
            _profile_trace(f"?좏깮 ?붿껌={identifier!r} ?댁쟾={before!r} ?댄썑={self._profile_state().active_profile_id!r}")

        self._tk(select)
        return self.get_state()

    # ---- ?쒖떇 愿由??덉떆 蹂닿퀬?쒕줈 ?쒖떇 蹂듭젣쨌?대쫫 諛붽씀湲걔룹꽭遺 ?섏젙쨌??젣) ----
    def _sidebar_collapsed_value(self):
        """?쇱そ 硫붾돱 ?묓옒 ??κ컪(?놁쑝硫?None). ?곹깭 議고쉶媛 ??븘 ??踰덈쭔 ?쎈뒗??"""
        if not hasattr(self, "_sidebar_collapsed"):
            try:
                self._sidebar_collapsed = self.gui._以留??쒕퉬??).settings.read().get("sidebar_collapsed")
            except Exception:
                self._sidebar_collapsed = None
        return self._sidebar_collapsed

    def set_sidebar_collapsed(self, collapsed):
        """?곗쓣 ?뚮????뚮쭔 ?쇱そ 硫붾돱 ?묓옒 ?곹깭瑜??ㅼ젙 ?뚯씪????ν븳??"""
        value = bool(collapsed)
        self._sidebar_collapsed = value
        self.gui._以留??쒕퉬??).settings.update(lambda current: current.update({"sidebar_collapsed": value}))
        return value

    def set_drop_target(self, target):
        """?뚯뼱 ?볦? ?뚯씪???ｌ쓣 怨녹쓣 諛붽씔?? documents(臾몄꽌 紐⑸줉) ?먮뒗 format(?덉떆 ?쒖떇 蹂듭젣)."""
        if target not in ("documents", "manual_documents", "format", "quick_format", "sketch_image", "paint_image",
                          "rename_files"):
            raise ValueError("吏?먰븯吏 ?딅뒗 ?볤린 ??곸엯?덈떎.")
        self.drop_target = target
        if target == "format":   # ?쒖떇 愿由?李쎌쓣 ?????쒖떇?덉떆 ?대뜑???덈줈 ?ｌ? ?덉떆瑜?李얠븘 ?깅줉?쒕떎
            detect = getattr(self.gui, "_?쒖떇?덉떆_?먮룞媛먯?", None)
            if detect is not None:
                self._tk(detect)
        window = self.window
        if window is not None and hasattr(window, "run_js"):
            text = ("?ш린???볦쑝硫???蹂닿퀬?쒖쓽 ?쒖떇??蹂듭젣?⑸땲?? if target == "format"
                    else "??移??꾩뿉 ?볦쑝硫?移?諛곌꼍 洹몃┝?쇰줈 ?ｌ뒿?덈떎" if target == "sketch_image"
                    else "?ш린???볦쑝硫?洹몃┝??諛곌꼍 ?ъ쭊?쇰줈 ?ｌ뒿?덈떎" if target == "paint_image"
                    else "?ш린???뚯씪???볦쑝硫??대쫫 紐⑸줉??異붽??⑸땲?? if target == "rename_files"
                    else "?ш린???볦쑝硫?臾몄꽌 紐⑸줉??異붽??⑸땲??)
            try:
                window.run_js(f"window.docfitDropText = {text!r};")
            except Exception:
                logging.getLogger(__name__).debug("drop text update failed", exc_info=True)
        return self.get_state()

    def add_format_paths(self, paths):
        """?뚯뼱 ?볦? ?덉떆 蹂닿퀬??HWP/HWPX) 以?泥??뚯씪???쒖떇??遺꾩꽍?????쒖떇?쇰줈 蹂듭젣?쒕떎."""
        from docfit_app.api_contract import ServiceError
        candidates = [str(p) for p in (paths or []) if Path(str(p)).suffix.lower() in {'.hwp', '.hwpx'}]
        if candidates:
            try:
                selection = self._file_dialogs.register_selection('add_format_file', candidates)
                candidates = self._file_dialogs.resolve_selection(selection['selection_id'], 'add_format_file')
            except ServiceError:
                return self.get_state()

        def start():
            gui = self.gui
            if gui.running or self._profile_state().analyzing_format:
                gui.status_var.set("?묒뾽?대굹 ?쒖떇 遺꾩꽍???앸궃 ???ㅼ떆 ?볦븘 二쇱꽭??")
                return
            if not candidates:
                gui.status_var.set("?쒖떇??蹂듭젣?섎젮硫?HWP ?먮뒗 HWPX ?덉떆 蹂닿퀬?쒕? ?볦븘 二쇱꽭??")
                return
            if len(candidates) > 1:
                gui.濡쒓렇?쒖떆(f"?덉떆 蹂닿퀬?쒕뒗 ??踰덉뿉 ?섎굹??蹂듭젣?⑸땲?? {Path(candidates[0]).name}")
            gui._?쒖떇_遺꾩꽍_?쒖옉(candidates[0], ?대쫫臾산린=False)

        self._tk(start)
        return self.get_state()

    def receive_drop(self, paths, client_x=None, client_y=None):
        """李쎌뿉 ?뚯뼱 ?볦? ?뚯씪: '?쒖떇 愿由? 李쎌씠 ?대젮 ?덉쑝硫??덉떆 ?쒖떇 蹂듭젣, ?꾨땲硫?臾몄꽌 紐⑸줉??異붽?."""
        if self.drop_target == "format":
            return self.add_format_paths(paths)
        if self.drop_target == "sketch_image":
            return self._receive_sketch_image(paths, client_x, client_y)
        if self.drop_target == "paint_image":
            return self._receive_sketch_image(paths, client_x, client_y, event="docfit-paint-image-dropped")
        if self.drop_target == "rename_files":
            return self._receive_rename_paths(paths)
        bounds = getattr(self, "_profile_drop_bounds", None)
        on_badge = (bounds is not None and isinstance(client_x, (int, float)) and isinstance(client_y, (int, float)))
        if on_badge:
            left, top, right, bottom = bounds
            on_badge = left <= client_x < right and top <= client_y < bottom
        if self.drop_target == "quick_format" or on_badge:
            return self.quick_register_and_activate_profile(paths[0]) if len(paths) == 1 else self._with_notice("?덉떆 ?쒖떇? ??媛쒖뵫 ?볦븘 二쇱꽭??")
        if self.drop_target == "manual_documents":
            return self.add_paths(paths, from_drop=False)
        return self.add_paths(paths, from_drop=True)

    def _receive_rename_paths(self, paths):
        """?뚯씪?대쫫 ??뿉 ?뚯뼱 ?볦? ?뚯씪쨌?대뜑(?대뜑??諛붾줈 ?꾨옒 ?뚯씪留?: 紐⑸줉???뷀븯怨??붾㈃???뚮┛??"""
        try:
            result = self._file_rename_service().add_paths(list(paths or [])[:10000])
        except Exception as exc:
            return self._with_notice(str(exc) or "?뚯씪??異붽??섏? 紐삵뻽?듬땲??")
        window = self.window
        if window is not None and hasattr(window, "run_js"):
            try:
                window.run_js("window.dispatchEvent(new Event('docfit-rename-files-dropped'));")
            except Exception:
                logging.getLogger(__name__).debug("rename drop event failed", exc_info=True)
        if result.get("skipped_count"):
            return self._with_notice(f"{result['skipped_count']}媛??뚯씪? 紐⑸줉???ｌ? ?딆븯?듬땲?? "
                                     f"{result['skipped'][0]['reason']}")
        return self.get_state()

    def _receive_sketch_image(self, paths, client_x, client_y, event="docfit-sketch-image-dropped"):
        """?쒓렇由쇳뙋쨌洹몃┝?먯뿉 ?뚯뼱 ?볦? ?ъ쭊: ?뚮쭪? ?ш린濡?諛붽퓭 ?먭퀬 ?붾㈃???뚮┛???붾㈃??take_drop?쇰줈 媛?멸컙??."""
        from docfit_app import sketch_image_input
        try:
            image = sketch_image_input.from_path(paths[0]) if paths else None
            if image is None:
                raise ValueError("洹몃┝ ?뚯씪???볦븘 二쇱꽭??")
        except Exception as exc:
            return self._with_notice(str(exc) or "洹몃┝???쎌? 紐삵뻽?듬땲??")
        self._sketch_drop_seq = getattr(self, "_sketch_drop_seq", 0) + 1
        self._sketch_drop = dict(image, client_x=client_x, client_y=client_y, seq=self._sketch_drop_seq)
        window = self.window
        if window is not None and hasattr(window, "run_js"):
            try:
                window.run_js(f"window.dispatchEvent(new Event({event!r}));")
            except Exception:
                logging.getLogger(__name__).debug("sketch drop notify failed", exc_info=True)
        return self.get_state()

    def add_format_file(self, selection_id=None):
        if not selection_id:
            return {'ok': False, 'error': 'FILE_SELECTION_REQUIRED'}
        return self.add_format_paths(self._file_dialogs.resolve_selection(selection_id, 'add_format_file'))

    def write_format_example(self):
        """鍮???湲 臾몄꽌???덉떆瑜?吏곸젒 ?⑥꽌 ?쒖떇??留뚮뱺??"""
        self._tk(self.gui._?쒖떇_?덉떆?몄쭛_?쒖옉, timeout=None, front=True)
        return self.get_state()

    def _with_notice(self, message):
        state = self.get_state()
        if message:
            state["notice"] = message
        return state

    def rename_profile(self, identifier, name, organization=""):
        """?쒖떇 ?대쫫(怨?湲곌?)??諛붽씔?? ???섎㈃ notice???댁쑀瑜??댁븘 ?뚮젮以??"""
        return self._with_notice(self._tk(lambda: self.gui._?쒖떇_?대쫫_???str(identifier or ""), name, organization)))

    def delete_profile(self, identifier):
        """?쒖떇????젣?쒕떎(?뺤씤? ?붾㈃???쒕떎). 湲곕낯 ?쒖떇? ??젣?섏? ?딅뒗??"""
        return self._with_notice(self._tk(lambda: self.gui._?쒖떇_??젣(str(identifier or ""))))

    def edit_profile(self, identifier):
        """?쒖떇 ?몃??ы빆 李쎌쓣 ?댁뼱 ??쒓컪??怨좎튇??李쎌쓣 ?レ쓣 ?뚭퉴吏 湲곕떎由곕떎)."""
        self._tk(lambda: self.gui._?쒖떇_?섏젙?섍린(str(identifier or "")), timeout=None, front=True)
        return self.get_state()

    def show_format_example(self):
        """吏湲?怨좊Ⅸ ?쒖떇???낇엺 ?덉떆 蹂닿퀬?쒕? 留뚮뱾????湲濡?蹂댁뿬 以??留뚮뱶???숈븞 ?묒뾽 吏꾪뻾???붾㈃??蹂댁씤??."""
        self._tk(self.gui._?쒖떇?덉떆_?뺤씤)
        return self.get_state()

    def format_gallery(self):
        """?ㅼ삤?ㅽ겕???쒖떇 怨좊Ⅴ湲? ?쒖떇留덈떎 ?덉떆 泥?履?洹몃┝(?ㅽ떥而? JPEG data URI ?먮뒗 None)怨??대쫫쨌湲곌?쨌?ъ슜 以??щ?."""
        def collect():
            items = []
            still = getattr(self.gui, "_?쒖떇_?ㅽ떥而?, None)
            make = getattr(self.gui, "_?몃꽕??留뚮뱾湲??쒖옉", None)
            need = getattr(self.gui, "_?몃꽕???꾩슂???쒖떇", None)
            if make is not None and need is not None:
                make(need())          # 誘몃━蹂닿린 洹몃┝???녿뒗 ?덉떆??諛깃렇?쇱슫?쒖뿉???몃꽕?쇱쓣 留뚮뱺???ㅼ쓬??????蹂댁엫)
            for item in self._profiles():
                data = still(item["id"], 300, "JPEG") if still is not None else None
                image = "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii") if data else None
                items.append(dict(item, image=image))
            return items

        return self._tk(collect)

    def open_format_samples(self):
        """?쒖떇?덉떆 ?대뜑(C:\\HWP_AUTODOCFIT\\?쒖떇?덉떆)瑜??먯깋湲곕줈 ?곕떎(?뚰뙆). ?덉떆 ?뚯씪??怨좎튂硫?'??踰덉뿉 ?곸슜' ??諛섏쁺?쒕떎."""
        opener = getattr(self.gui, "_?쒖떇?덉떆_?대뜑_?닿린", None)
        if opener is not None:
            self._tk(opener)
        return self.get_state()

    def set_option(self, name, value):
        """鍮좊Ⅸ ?ㅼ젙??耳쒓린쨌?꾧린 媛믪쓣 諛붽씔?? ???ㅼ젙 蹂?섏쓽 蹂寃?媛먯떆媛 ?ㅼ젙 ?뚯씪????ν븳??"""
        attribute = QUICK_OPTIONS.get(name)
        if attribute is None:
            raise ValueError("吏?먰븯吏 ?딅뒗 ?ㅼ젙?낅땲??")

        def update():
            variable = getattr(self.gui, attribute, None)
            if variable is not None and not self.gui.running:
                variable.set(bool(value))

        self._tk(update)
        return self.get_state()

    def next_job(self):
        def reset():
            if self.gui.running:
                return
            self.gui.紐⑸줉吏?곌린()
            self._cancel_pending_drop()
            self._update_document_hints()
            self.gui._寃곌낵_珥덇린??)
            self.gui._?덈궡?? self.gui._?덈궡吏??= None, set()
            self.gui.status_var.set("??臾몄꽌瑜??좏깮?섏꽭??")
            self._page_fit_card = False  # ?ㅻⅨ 移대뱶瑜?怨좊Ⅴ硫??섏씠吏 留욎땄 移대뱶 ?댁젣
            self.gui.selected_mode.set("spacing")
            self.gui._紐⑤뱶_?좏깮??)

        self._tk(reset)
        return self.get_state()

    def run_tool(self, name):
        commands = {"paste": self.gui._?띿뒪?몃줈_臾몄꽌異붽?_?닿린}
        command = commands.get(name)
        if command is None:
            raise ValueError("吏?먰븯吏 ?딅뒗 ?꾧뎄?낅땲??")
        if not self._tk_fallback_enabled():
            return {"ok": False, "error": "FLUTTER_ONLY"}
        self._tk(command, timeout=None, front=True)
        return True

    def request_close(self):
        """OS 李??リ린 ?꾩뿉 湲곗〈 ?깆쓽 醫낅즺 ?뺤씤쨌?묒뾽 以묐떒 ?덉감瑜??섑뻾?쒕떎."""
        if self.tk_stopped is not None and self.tk_stopped.is_set():
            return True
        force = False
        with self._close_lock:
            if self._close_protocol:
                if self._close_request is not None:
                    self._close_request = None
                    self._cancel_close_timer()
                    force = True
                else:
                    self._close_request = {"id": uuid.uuid4().hex, "kind": "app_close"}
                    self._close_timer = threading.Timer(
                        5.0, self._close_unanswered, args=(self._close_request["id"],))
                    self._close_timer.daemon = True
                    self._close_timer.start()
                    return False  # Never block the native closing event for JS.
        if force:
            return self._force_close(native_event=True)
        def defer_confirmation():
            if not (getattr(self.gui.root, "_docfit_hidden_backend", False) and self.gui.running):
                return False
            if not getattr(self, "_close_prompt_queued", False):
                self._close_prompt_queued = True
                def ask_after_os_close_returns():
                    try:
                        self.gui.醫낅즺()
                    finally:
                        self._close_prompt_queued = False
                self.gui.root.after(0, ask_after_os_close_returns)
            return True
        # Veto the OS close immediately, then show Flutter's confirmation.
        # Holding the native closing event until JS answers can block WebView.
        if getattr(self.gui, "_bridge_callbacks", None) is not None and self._tk(defer_confirmation):
            return False
        def close():
            try:
                if not self.gui.root.winfo_exists():
                    return True
            except Exception:
                return True
            self.user_closing = True
            self.gui.醫낅즺()
            try:
                closed = not bool(self.gui.root.winfo_exists())
            except Exception:
                closed = True
            if not closed:
                self.user_closing = False   # ?묒뾽 以?醫낅즺瑜?痍⑥냼??寃쎌슦
            return closed

        # ?묒뾽 以묒씠硫?醫낅즺 ?뺤씤 李쎌씠 ?좎꽌 ?ъ슜?먯쓽 ?듭쓣 湲곕떎由곕떎.
        try:
            return self._tk(close, timeout=None, front=True)
        except RuntimeError:
            # 醫낅즺 callback??root.destroy瑜??몄텧?섎㈃ ?먯떊??Future??醫낅즺?쒕떎.
            if self.tk_stopped is not None and self.tk_stopped.is_set():
                return True
            raise


def _cancel_before_edit(method):
    """?ㅼ젙쨌臾몄꽌쨌?쒖떇 蹂寃쎌? 媛숈? Tk ?먯뿉???덉빟 ?좏겙??癒쇱? 臾댄슚?뷀븳??"""
    from functools import wraps
    @wraps(method)
    def call(self, *args, **kwargs):
        self._tk(self._cancel_pending_drop)
        return method(self, *args, **kwargs)
    return call


for _edit_name in (
    "add_files", "add_folder", "remove_file", "clear_files", "set_range", "start", "set_profile",
    "set_include_spacing", "set_reset_spacing", "set_table_spacing", "set_exclude_tables", "set_card_option",
    "set_stage", "reset_stages", "set_option", "save_settings", "set_drop_target", "add_format_file",
    "add_format_paths", "get_settings", "next_job", "text_input",
    "open_settings", "open_stages", "stage_config", "format_profile", "rename_profile", "delete_profile",
):
    setattr(DesktopWebBridge, _edit_name, _cancel_before_edit(getattr(DesktopWebBridge, _edit_name)))


def smoke_cdp_port(environ=None):
    """Return the loopback CDP port requested by the frozen-EXE smoke test, if any.

    pywebview's own AdditionalBrowserArguments replaces WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS
    on some WebView2 runtimes, so the smoke test asks the app for the port explicitly.
    """
    value = (os.environ if environ is None else environ).get("DOCFIT_SMOKE_CDP_PORT", "")
    if value.isdigit() and 1024 <= int(value) <= 65535:
        return int(value)
    return None


def _file_size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return None


class _Win32WindowApi:
    """Monitor work-area and SetWindowPos wrapper; isolated for fake-driven tests."""
    SPI_GETWORKAREA = 0x0030
    HWND_TOPMOST = -1
    HWND_NOTOPMOST = -2
    SWP_NOACTIVATE = 0x0010

    def __init__(self, user32=None):
        self._ctypes = None
        if user32 is None:
            import ctypes
            self._ctypes = ctypes
            user32 = ctypes.windll.user32
        self.user32 = user32

    def work_area(self, hwnd):
        if self._ctypes is None:
            import ctypes
        else:
            ctypes = self._ctypes
        from ctypes import wintypes
        try:
            class MONITORINFO(ctypes.Structure):
                _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT), ('rcWork', wintypes.RECT), ('dwFlags', wintypes.DWORD)]
            monitor_from_window = getattr(self.user32, 'MonitorFromWindow', None)
            get_monitor_info = getattr(self.user32, 'GetMonitorInfoW', None)
            monitor = monitor_from_window(hwnd, 2) if monitor_from_window else None
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(info)
            if monitor and get_monitor_info and get_monitor_info(monitor, ctypes.byref(info)):
                r = info.rcWork
                return r.left, r.top, r.right, r.bottom
        except Exception:
            pass
        # 紐⑤땲?곕퀎 API媛 ?녿뒗 ?섍꼍?먯꽌??湲곕낯 ?붾㈃ ?묒뾽 ?곸뿭???ъ슜?쒕떎.
        rect = wintypes.RECT()
        if not self.user32.SystemParametersInfoW(self.SPI_GETWORKAREA, 0, ctypes.byref(rect), 0):
            raise OSError('?붾㈃ ?묒뾽 ?곸뿭???뺤씤?섏? 紐삵뻽?듬땲??')
        return rect.left, rect.top, rect.right, rect.bottom

    def set_window_pos(self, hwnd, x, y, width, height, topmost):
        insert_after = self.HWND_TOPMOST if topmost else self.HWND_NOTOPMOST
        if not self.user32.SetWindowPos(hwnd, insert_after, x, y, width, height, self.SWP_NOACTIVATE):
            raise OSError('??李??꾩튂瑜?諛붽씀吏 紐삵뻽?듬땲??')
        return True


class _PyWebViewWindow:
    def __init__(self, window, settings=None, saved_state=None):
        self.window = window
        self.settings = settings
        self.saved_state = saved_state

    def handle(self):
        return self.window.native.Handle.ToInt64()

    def geometry(self):
        if self.saved_state and self.window.width < 250:
            saved = self.saved_state()
            return saved['x'], saved['y'], saved['width'], saved['height']
        return self.window.x, self.window.y, self.window.width, self.window.height

    def topmost(self):
        return bool(self.saved_state()['topmost']) if self.saved_state else bool(getattr(self.window, '_on_top', False))

    def set_sidebar_only(self, enabled):
        self.window.resize(190 if enabled else self.saved_state()['width'], self.saved_state()['height'])

    def save_side(self, side):
        if self.settings is not None:
            self.settings.update(lambda current: current.update({'sidebar_mode_side': side}))


class _BrowserApi:
    """Expose commands only: pywebview recursively inspects public attributes."""

    def __init__(self, bridge):
        for name in (
            "cancel_zero_click", "start_zero_click", "quick_register_and_activate_profile", "drop_format_file", "set_profile_drop_bounds",
            "get_state", "add_files", "add_folder", "add_paths", "remove_file",
            "clear_files", "set_mode", "set_range", "start", "stop", "start_job", "cancel_job", "get_events",
            "open_settings", "get_settings", "save_settings", "text_input", "open_stages", "open_log", "get_log", "clear_log",
            "get_pending_dialog", "resolve_dialog", "enable_close_guard", "acknowledge_close", "format_profile", "flow_editor", "document_tool", "stage_config", "table_template", "idioms", "hangul_fonts", "get_abbreviations", "save_abbreviation", "delete_abbreviation", "set_abbreviation_defaults", "abbreviation_document", "table_units", "table_sketch", "timemachine", "library",
            "file_rename", "kclip", "new_document", "hwp_bulk", "open_results", "next_job", "run_tool", "open_result",
            "sidebar_mode", "always_on_top",
            "show_result", "open_source_file", "show_source_file", "open_result_source", "open_diff", "compare_result", "launch_external_hwp_diff", "set_stage", "reset_stages", "set_stage_default",
            "set_profile", "set_option", "set_include_spacing", "set_reset_spacing", "set_table_spacing",
            "set_exclude_tables", "set_card_option",
            "set_sidebar_collapsed", "set_drop_target", "add_format_file", "write_format_example", "rename_profile", "delete_profile",
            "edit_profile", "show_format_example", "open_format_samples", "format_gallery",
            "set_conversion_target", "start_single_file_conversion", "check_update", "start_update", "open_update_page",
        ):
            setattr(self, name, getattr(bridge, name))


def _resource_path():
    import sys

    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    flutter_page = base / "desktop_web" / "flutter" / "index.html"
    if flutter_page.is_file() and (flutter_page.parent / "main.dart.js").is_file():
        return flutter_page
    return base / "desktop_web" / "index.html"


_FILE_DROP_SCRIPT = """
(() => {
  if (window.docfitFileDropInstalled) return;
  window.docfitFileDropInstalled = true;
  let depth = 0;
  const overlay = document.createElement('div');
  overlay.id = 'docfit-file-drop';
  overlay.textContent = window.docfitDropText || '?ш린???볦쑝硫?臾몄꽌 紐⑸줉??異붽??⑸땲??;
  overlay.style.cssText = 'display:none;position:fixed;box-sizing:border-box;inset:16px;z-index:2147483647;'
    + 'pointer-events:none;align-items:center;justify-content:center;border:3px dashed #2563eb;'
    + 'border-radius:24px;background:rgba(239,246,255,.94);color:#1e40af;'
    + 'font:600 20px sans-serif;text-align:center;padding:24px;';
  document.body.appendChild(overlay);
  const files = e => Array.from(e.dataTransfer?.types || []).includes('Files');
  const hide = () => { depth = 0; overlay.style.display = 'none'; };
  document.addEventListener('dragenter', e => {
    if (!files(e)) return;
    overlay.textContent = window.docfitDropText || '?ш린???볦쑝硫?臾몄꽌 紐⑸줉??異붽??⑸땲??;
    e.preventDefault(); depth++; overlay.style.display = 'flex';
  }, true);
  document.addEventListener('dragover', e => {
    if (!files(e)) return;
    e.preventDefault(); e.dataTransfer.dropEffect = 'copy';
    const r = window.docfitProfileDropRect;
    const badge = r && e.clientX >= r[0] && e.clientX < r[2] && e.clientY >= r[1] && e.clientY < r[3];
    overlay.textContent = badge ? '???ш린???볦븘 ???쒖떇?쇰줈 諛붾줈 ?깅줉쨌?곸슜' : (window.docfitDropText || '?ш린???볦쑝硫?臾몄꽌 紐⑸줉??異붽??⑸땲??);
    Object.assign(overlay.style, badge ? {left:r[0]+'px', top:r[1]+'px', right:'auto', bottom:'auto', width:(r[2]-r[0])+'px', height:(r[3]-r[1])+'px', fontSize:'9px',padding:'2px'} : {left:'0',top:'0',right:'0',bottom:'0',width:'auto',height:'auto',fontSize:'20px',padding:'24px'});
    overlay.style.display = 'flex';
  }, true);
  document.addEventListener('dragleave', () => {
    depth = Math.max(0, depth - 1); if (!depth) hide();
  }, true);
  document.addEventListener('drop', e => {
    if (files(e)) e.preventDefault();
    hide();
    // Keep bubbling: pywebview's DOM handler resolves native Windows paths.
  }, true);
  window.addEventListener('blur', hide);
  document.addEventListener('dragend', hide, true);
})();
"""


def _bind_file_drop(web_window, bridge):
    """Enable file drops above Flutter's canvas and retain native path resolution."""
    from webview.dom import DOMEventHandler

    def dropped(event):
        try:
            transfer = event.get("dataTransfer") or event.get("domTransfer") or {}
            files = transfer.get("files", [])
            paths = [item.get("pywebviewFullPath") for item in files if isinstance(item, dict)]
            paths = [path for path in paths if path]
            if paths:
                if event.get("clientX") is not None and event.get("clientY") is not None:
                    bridge.receive_drop(paths, client_x=event["clientX"], client_y=event["clientY"])
                else:
                    bridge.receive_drop(paths)
                # ?꾨윴?몄뿏?쒓? ?ㅼ쓬 ?대쭅 二쇨린瑜?湲곕떎由ъ? ?딄퀬 理쒖떊 ?곹깭瑜??ㅼ떆 ?쎄쾶 ?쒕떎.
                web_window.run_js("window.dispatchEvent(new Event('docfit-documents-dropped'));")
            elif files:
                bridge._tk(lambda: bridge.gui.status_var.set(
                    "?쒕∼???뚯씪 寃쎈줈瑜??쎌? 紐삵뻽?듬땲?? 臾몄꽌 ?좏깮 踰꾪듉???댁슜??二쇱꽭??"))
                logging.getLogger(__name__).warning("File drop received without native paths")
        except Exception:
            logging.getLogger(__name__).exception("File drop failed")

    # Register with pywebview (not plain JS) so WebView2 supplies full file paths.
    web_window.dom.document.events.drop += DOMEventHandler(
        dropped, prevent_default=True, stop_propagation=True)
    web_window.run_js(_FILE_DROP_SCRIPT)


def _guard_pywebview_form_closed():
    """pywebview 6.2.1 may dispatch WinForms FormClosed twice during a close race.

    Its handler deletes BrowserView.instances[uid] without checking whether the
    first FormClosed callback already removed it. pythonnet then surfaces the
    resulting KeyError through WinForms as an unhandled JIT dialog.
    """
    if os.name != "nt":
        return
    try:
        from webview.platforms import winforms
    except ImportError:
        return
    form_type = winforms.BrowserView.BrowserForm
    if getattr(form_type, "_docfit_close_guarded", False):
        return
    original = form_type.on_close

    def close_once(form, *args):
        if getattr(form, "_docfit_form_closed_handled", False):
            return
        form._docfit_form_closed_handled = True
        return original(form, *args)

    form_type.on_close = close_once
    form_type._docfit_close_guarded = True


_WEBVIEW_RENDERING_ARGUMENTS = (
    "--disable-renderer-backgrounding",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-features=CalculateNativeWinOcclusion",
)


def _append_webview_rendering_arguments(arguments):
    """Merge renderer keep-alive switches into pywebview's WebView2 arguments."""
    tokens = str(arguments or "").split()
    features = []
    remaining = []
    for token in tokens:
        if token.startswith("--disable-features="):
            features.extend(part for part in token.partition("=")[2].split(",") if part)
        else:
            remaining.append(token)
    features.extend(
        argument.partition("=")[2]
        for argument in _WEBVIEW_RENDERING_ARGUMENTS
        if argument.startswith("--disable-features=")
    )
    for argument in _WEBVIEW_RENDERING_ARGUMENTS:
        if not argument.startswith("--disable-features=") and argument not in remaining:
            remaining.append(argument)
    unique_features = list(dict.fromkeys(features))
    if unique_features:
        remaining.append("--disable-features=" + ",".join(unique_features))
    return " ".join(remaining)


def _install_webview_rendering_guard(edgechromium_module=None):
    """Prevent the visible WebView2 renderer from being background-throttled.

    pywebview 6.2.1 sets AdditionalBrowserArguments itself, so the usual
    WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS environment variable is not reliable.
    A small WebView2 subclass adds the flags immediately before initialization.
    """
    if edgechromium_module is None:
        if os.name != "nt":
            return False
        try:
            from webview.platforms import edgechromium as edgechromium_module
        except ImportError:
            return False
    if getattr(edgechromium_module, "_docfit_rendering_guarded", False):
        return True

    webview_type = edgechromium_module.WebView2

    class RenderingGuardWebView2(webview_type):
        def EnsureCoreWebView2Async(self, *args, **kwargs):
            properties = self.CreationProperties
            properties.AdditionalBrowserArguments = _append_webview_rendering_arguments(
                properties.AdditionalBrowserArguments
            )
            try:
                try:
                    from System import EventHandler
                except ImportError:
                    EventHandler = lambda callback: callback

                def initialized(sender, event):
                    try:
                        # A persistently crashing renderer must not turn recovery
                        # into an unbounded Reload loop. Keep a rolling one-minute
                        # budget per WebView instance.
                        reload_times = []

                        def renderer_failed(_sender, _event):
                            try:
                                now = time.monotonic()
                                while reload_times and now - reload_times[0] >= 60:
                                    reload_times.pop(0)
                                if len(reload_times) >= 3:
                                    logging.getLogger(__name__).error(
                                        "WebView2 renderer recovery stopped after 3 reloads in 60 seconds"
                                    )
                                    return
                                reload_times.append(now)
                                self.CoreWebView2.Reload()
                            except Exception:
                                logging.getLogger(__name__).exception(
                                    "Could not reload WebView2 after renderer exit"
                                )

                        self.CoreWebView2.ProcessFailed += EventHandler(renderer_failed)
                    except Exception:
                        logging.getLogger(__name__).exception(
                            "Could not monitor WebView2 renderer process"
                        )

                self.CoreWebView2InitializationCompleted += EventHandler(initialized)
            except Exception:
                logging.getLogger(__name__).debug(
                    "WebView2 initialization event unavailable", exc_info=True
                )
            result = super().EnsureCoreWebView2Async(*args, **kwargs)
            return result

    edgechromium_module.WebView2 = RenderingGuardWebView2
    edgechromium_module._docfit_rendering_guarded = True
    return True


def run_webview(gui):
    """湲곗〈 Tk 諛깆뿏?쒕? ?④꺼 ?ㅽ뻾?섍퀬 WebView2瑜?二?UI濡??쒖떆?쒕떎."""
    if importlib.util.find_spec("webview") is None:
        return False

    import webview
    _guard_pywebview_form_closed()
    try:
        _install_webview_rendering_guard()
    except Exception:
        logging.getLogger(__name__).exception("Could not disable WebView2 idle rendering throttling")

    bridge = DesktopWebBridge(gui)
    page = _resource_path()
    if not page.is_file():
        raise FileNotFoundError(f"??UI ?뚯씪??李얠쓣 ???놁뒿?덈떎: {page}")

    if isinstance(gui, PendingGui):
        # Tk瑜?湲곕떎由ъ? ?딄퀬 李??ш린瑜??뺥븳??pywebview ?붾㈃ ?뺣낫??Tk? 媛숈? ?쇰━ ?쎌?).
        try:
            screen = webview.screens[0]
            screen_width, screen_height = int(screen.width), int(screen.height)
        except Exception:
            screen_width, screen_height = bridge._tk(
                lambda: (gui.root.winfo_screenwidth(), gui.root.winfo_screenheight())
            )
    else:
        screen_width, screen_height = bridge._tk(
            lambda: (gui.root.winfo_screenwidth(), gui.root.winfo_screenheight())
        )
    width = min(1040, max(700, screen_width - 40))
    # Reserve space for the title bar and taskbar; center the window so it
    # remains fully reachable even when Tk reports a logical (DPI-scaled) size.
    height = min(800, max(400, screen_height - 220))
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)

    window = webview.create_window(
        f"{APP_NAME} 쨌 v{APP_VERSION}",
        # A filesystem path activates pywebview's local HTTP asset server;
        # file:// URLs bypass it and cannot load Flutter's WASM/font assets.
        url=str(page),
        js_api=_BrowserApi(bridge),
        width=width,
        height=height,
        x=x,
        y=y,
        min_size=(min(260, width), min(180, height)),
        text_select=True,
    )
    bridge.window = window
    bridge._saved_window = {'x': x, 'y': y, 'width': width, 'height': height, 'topmost': False}
    try:
        initial_settings = bridge._tk(lambda: bridge._configuration().snapshot(running=bridge.gui.running).get('values', {}))
        window.set_on_top(bool(initial_settings.get('always_on_top', False)))
        bridge._saved_window['topmost'] = bool(initial_settings.get('always_on_top', False))
    except Exception:
        logging.getLogger(__name__).debug('Could not apply saved always-on-top setting', exc_info=True)
    tk_stopped = threading.Event()
    bridge.tk_stopped = tk_stopped
    window.events.closing += bridge.request_close

    def track_tk_destroy():
        try:
            real = _real_gui(gui)
            # Tk 以鍮꾧? ?앸굹硫?釉뚮━吏???由?媛앹껜 ????ㅼ젣 ?붾㈃???대떎(type쨌isinstance 寃?щ룄 ?ㅼ젣 ?붾㈃ 湲곗?).
            bridge.gui = real
            root = real.root
        except Exception:
            # Tk ?붾㈃??留뚮뱾吏 紐삵뻽?? ??李쎌쓣 ?リ퀬 ?쒖옉 ?ㅻ쪟???몄텧??履쎌씠 ?뚮┛??
            tk_stopped.set()
            return
        original_destroy = root.destroy

        def tracked_destroy():
            bridge._shutdown()
            original_destroy()

        root.destroy = tracked_destroy

    if isinstance(gui, PendingGui):
        threading.Thread(target=track_tk_destroy, name="tk-ready-watch", daemon=True).start()
    else:
        track_tk_destroy()

    def bind_file_drop(web_window):
        try:
            _bind_file_drop(web_window, bridge)
        except Exception:
            logging.getLogger(__name__).exception("Could not enable file drag and drop")

    def stop_webview_when_app_exits(web_window):
        tk_stopped.wait()
        if bridge.user_closing:
            # ?ъ슜?먭? ??李쎌쓣 ?ル뒗 以묒씠硫?李쎌씠 ?ㅼ뒪濡??ロ엺?? ?ш린??destroy()瑜???遺瑜대㈃
            # pywebview媛 ?ロ옒 泥섎━瑜???踰??ㅽ뻾??.NET '泥섎━?섏? ?딆? ?덉쇅' 李쎌씠 ?щ떎.
            return
        try:
            web_window.destroy()
        except Exception:
            pass

    def _dismiss_splash():
        try:
            import pyi_splash
            if pyi_splash.is_alive():
                pyi_splash.close()
        except Exception:
            pass

    window.events.loaded += lambda *_args: (_dismiss_splash(), bind_file_drop(window))

    def initialize_webview(web_window):
        _dismiss_splash()
        threading.Thread(
            target=stop_webview_when_app_exits,
            args=(web_window,),
            name="webview-shutdown-watch",
            daemon=True,
        ).start()

    # 李??꾩씠肄? 吏?뺥븯吏 ?딆쑝硫??ㅽ뻾 ?뚯씪(python.exe ?먮뒗 exe)???꾩씠肄섏쓣 ?대떎.
    ?꾩씠肄?= {"icon": APP_ICON} if APP_ICON and Path(APP_ICON).is_file() else {}
    smoke_port = smoke_cdp_port()
    if smoke_port is not None:
        webview.settings["REMOTE_DEBUGGING_PORT"] = smoke_port
    webview.start(initialize_webview, args=[window], gui="edgechromium", http_server=True, **?꾩씠肄?
    return True


# Application values are injected by the entry point after import.
APP_VERSION = ""
APP_NAME = ""
APP_ICON = ""
