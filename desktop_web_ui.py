"""Tk 기반 문서 처리 기능을 반응형 WebView 화면에 연결한다."""

from __future__ import annotations

import base64
import importlib.util
import logging
import os
import subprocess
import shutil
import threading
import time
from concurrent.futures import Future, TimeoutError
from pathlib import Path
from types import SimpleNamespace

from docfit_core.progress_guide import guide_state
from docfit_core.stage_selection import STAGE_EXAMPLES, default_choice, stages_for_mode
from docfit_app.api_contract import response
from docfit_app.app_state import STAGE_ORDER
from docfit_core.kordoc_bridge import IMAGE_INPUT_EXTENSIONS, SUPPORTED_INPUT_EXTENSIONS
from docfit_core.file_conversion import HANCOM_PDF_DIRECT, IMAGE_FORMATS

# 화면에서 바로 켜고 끄는 공통 설정(이름 → 앱의 Tk 변수 속성). 값을 바꾸면 앱이 설정 파일에 저장한다.
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


class DesktopWebBridge:
    """WebView에서 호출하는 API. 모든 Tk 접근은 Tk 이벤트 루프에 위임한다."""

    def __init__(self, gui):
        self.gui = gui
        self.window = None
        self.tk_stopped = None
        # 사용자가 웹 창을 닫아 종료하는 중인지. 이때는 창이 스스로 닫히므로
        # 종료 감시 스레드가 destroy()를 다시 부르면 안 된다(pywebview 이중 닫힘 오류).
        self.user_closing = False
        # 창에 끌어 놓은 파일을 어디에 넣을지: documents(정리할 문서 목록) 또는 format(예시 서식 복제).
        # 화면의 '서식 관리' 창이 열려 있는 동안 format이다.
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

    def _shutdown(self):
        """Tk 종료 시 대기·실행 중 요청의 호출자를 종료 오류로 해제한다."""
        with self._request_lock:
            self._closed = True
            if self.tk_stopped is not None:
                self.tk_stopped.set()
            for request in self._requests:
                if not request.done():
                    request.set_exception(RuntimeError("앱이 종료 중입니다."))
            self._requests.clear()

    def _tk(self, callback, timeout=120, front=False):
        result = Future()
        with self._request_lock:
            if self._closed or (self.tk_stopped is not None and self.tk_stopped.is_set()):
                raise RuntimeError("앱이 종료 중입니다.")
            self._requests.add(result)

        def complete(value=None, error=None):
            with self._request_lock:
                self._requests.discard(result)
                # 종료가 먼저 호출자를 해제했으면 callback의 결과를 다시 쓰지 않는다.
                if not result.done():
                    if error is not None:
                        result.set_exception(error)
                    else:
                        result.set_result(value)

        def run():
            with self._request_lock:
                # 시간 초과·종료 후 큐에 남은 callback은 실행하지 않는다.
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
                    # 파일 선택 등 기본 창을 부모로 쓰는 대화상자가 웹 화면 뒤에 뜨지 않게 한다.
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
            complete(error=RuntimeError("앱이 종료 중입니다."))
            raise RuntimeError("앱이 종료 중입니다.") from exc
        try:
            return result.result(timeout=timeout)
        except TimeoutError as exc:
            # callback 자체가 낸 TimeoutError를 큐 응답 시간 초과로 바꾸지 않는다.
            with self._request_lock:
                if result.done():
                    return result.result()
                cancelled = result.cancel()
                if cancelled:
                    self._requests.discard(result)
            if not cancelled:
                raise RuntimeError("명령이 이미 실행 중입니다. 중복 실행하지 말고 진행 상태를 확인해 주세요.") from exc
            raise RuntimeError("앱 응답 시간이 초과되었습니다.") from exc

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
            state.profiles = gui._프로파일들 or {}
            state.profile_ids = gui._프로파일_ids or []
            state.active_profile_id = gui._활성_서식_프로파일
        except AttributeError:
            pass
        try:
            state.analyzing_format = gui._서식분석중
            state.analyzing_file = gui._서식분석_파일
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
        """서식 목록: 표시 이름(기관 포함), 이름·기관, 기본 서식 여부, 예시 파일 이름, 사용 중 여부."""
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
            name = str(profile.get("name") or "기본 서식")
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
                # 예시 보고서에서 분석한 서식 요소 가운데 정리에 쓰는 수(서식 관리 창의 복제 범위 요약)
                "coverage": self._cached_coverage(identifier, analysis),
            })
        return items

    def _format_task(self):
        gui = self.gui
        state = self._profile_state()
        return {"busy": bool(state.analyzing_format), "file": str(state.analyzing_file or "")}

    def get_state(self):
        def snapshot():
            gui = self.gui
            mode = gui.selected_mode.get()
            return {
                "files": [
                    {"name": Path(path).name, "path": path, "folder": str(Path(path).parent)}
                    for path in gui.files
                ],
                "count": len(gui.files),
                "mode": mode,
                "include_spacing": self._include_spacing(),
                "reset_spacing": self._reset_spacing(),
                "table_spacing": self._table_spacing(),
                "exclude_tables": self._exclude_tables(),
                "card_options": self._card_options(),
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
                    {
                        "name": Path(item.get("결과", "")).name,
                        "path": item.get("결과", ""),
                        "source": Path(item.get("원본", "")).name,
                        "pages": item.get("쪽수"),
                    }
                    for item in getattr(gui, "_결과목록", [])
                ],
                "default_saved": bool(gui._세부작업_기본저장.get(mode, False)),
                "stages": [] if mode == "file_format" else self._stages(mode),
                "profiles": self._profiles(),
                "profile": self._profile_state().active_profile_id,
                "format_task": self._format_task(),
                "pending_dialog": self._pending_dialog(),
                "drop_target": self.drop_target,
                "document_drop_revision": self._document_drop_revision,
                "options": {
                    name: bool(getattr(gui, attribute).get())
                    for name, attribute in QUICK_OPTIONS.items()
                    if hasattr(gui, attribute)
                },
                "guide": guide_state(
                    mode,
                    getattr(gui, "_안내키", None),
                    getattr(gui, "_안내지남", ()),
                ),
                "conversion_target": self.conversion_target,
                "conversion_targets": [],
                "can_start": self._can_start(mode, gui.files, gui.running) if mode != "file_format" else False,
                "version": APP_VERSION,
            }

        state = self._tk(snapshot)
        if state["mode"] == "file_format":
            # 외부 도구 버전 조회를 Tk 이벤트 루프에서 실행하면 화면이 멈춘다.
            # GUI 상태를 읽은 뒤 WebView 요청 스레드에서 준비 상태를 확인한다.
            files = [item["path"] for item in state["files"]]
            targets = self._conversion_targets(files)
            state["conversion_targets"] = targets
            state["can_start"] = self._can_start(state["mode"], files, state["running"], targets)
        return state

    def _can_start(self, mode, files, running, conversion_targets=None):
        if not files or running:
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
        """한/글을 띄우지 않고 COM ProgID 등록만 확인한다."""
        if os.name != "nt":
            return False
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "HwpFrame.HwpObject"):
                return True
        except (ImportError, OSError):
            return False

    def _conversion_prerequisites(self):
        with self._conversion_prerequisites_lock:
            now = time.monotonic()
            cached = self._conversion_prerequisites_cache
            if cached is not None and now - self._conversion_prerequisites_checked < 30:
                return cached
            from docfit_core.kordoc_bridge import engine_status
            pandoc_path = shutil.which("pandoc.exe") or shutil.which("pandoc")
            from docfit_core.kordoc_bridge import ocr_available
            self._conversion_prerequisites_cache = {
                "kordoc": engine_status(),
                "ocr": ocr_available(),
                "pandoc": bool(pandoc_path),
                "hwp_com": self._hwp_com_available(),
            }
            self._conversion_prerequisites_checked = time.monotonic()
            return self._conversion_prerequisites_cache

    def _conversion_targets(self, files):
        suffixes = [Path(path).suffix.lower() for path in files]
        valid = bool(suffixes) and all(suffix in SUPPORTED_INPUT_EXTENSIONS for suffix in suffixes)
        prerequisites = self._conversion_prerequisites()
        kordoc = prerequisites["kordoc"]
        kordoc_ready = bool(kordoc.get("available"))
        pandoc_ready = prerequisites["pandoc"]
        hwp_ready = prerequisites["hwp_com"]
        engine_reason = str(kordoc.get("reason") or "kordoc 사용 불가")
        # 그림 입력은 글자 인식(OCR)이 필요하다. 폐쇄망 꾸러미에는 OCR이 없으므로 미리 막고 이유를 보인다.
        if valid and kordoc_ready and not prerequisites.get("ocr", True) and any(
                suffix in IMAGE_INPUT_EXTENSIONS for suffix in suffixes):
            kordoc_ready = False
            engine_reason = "그림 파일은 글자 인식(OCR)이 필요해 변환할 수 없습니다(폐쇄망 꾸러미에 OCR 미포함)"
        # HWP·HWPX는 한/글이 직접 PDF로 저장한다. 다른 입력만 kordoc 중간 변환이 필요하다.
        pdf_needs_kordoc = any(suffix not in HANCOM_PDF_DIRECT for suffix in suffixes)
        pdf_ready = hwp_ready and (not pdf_needs_kordoc or kordoc_ready)
        invalid_reason = "kordoc 지원 형식만 가능"
        pdf_reason = (invalid_reason if not valid else
                      "한/글 PDF 저장 기능을 사용할 수 없습니다" if not hwp_ready else
                      engine_reason if pdf_needs_kordoc and not kordoc_ready else
                      "한/글 내장 PDF 저장 사용 · 추가 변환기 설치 없음" if not pdf_needs_kordoc else
                      "kordoc + 한/글 COM 준비됨")
        # 그림은 한/글 PDF 저장본을 쪽마다 렌더링하므로 PDF와 준비 조건이 같다.
        image_reason = (pdf_reason if not (valid and pdf_ready) else
                        "한/글 PDF 저장 후 쪽마다 그림 저장 · 여러 쪽은 폴더로 저장")
        return [
            {"format": "hwpx", "label": "HWPX", "enabled": valid and kordoc_ready,
             "reason": invalid_reason if not valid else engine_reason},
            {"format": "pdf", "label": "PDF", "enabled": valid and pdf_ready, "reason": pdf_reason},
            {"format": "docx", "label": "DOCX", "enabled": valid and kordoc_ready and pandoc_ready,
             "reason": invalid_reason if not valid else engine_reason if not kordoc_ready else
                      "Pandoc 설치 필요" if not pandoc_ready else "kordoc + Pandoc 준비됨"},
            {"format": "epub", "label": "EPUB", "enabled": valid and kordoc_ready and pandoc_ready,
             "reason": invalid_reason if not valid else engine_reason if not kordoc_ready else
                      "Pandoc 설치 필요" if not pandoc_ready else "kordoc + Pandoc 준비됨"},
            *({"format": kind, "label": kind.upper(), "enabled": valid and pdf_ready, "reason": image_reason}
              for kind in IMAGE_FORMATS),
        ]

    def add_files(self):
        self._tk(self.gui.파일선택, timeout=None, front=True)
        return self.get_state()

    def add_folder(self):
        self._tk(self.gui._폴더선택, timeout=None, front=True)
        return self.get_state()

    def add_paths(self, paths, *, from_drop=False):
        if not isinstance(paths, (list, tuple)):
            return self.get_state()
        if len(paths) > 100:
            return self.get_state()

        def add():
            if self.gui.running:
                return
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
                        added += self.gui.폴더추가(path)
                    elif self.gui.파일추가(path):
                        added += 1
                except (OSError, ValueError):
                    continue
            if added:
                if from_drop:
                    self._document_drop_revision += 1
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

    def _include_spacing(self):
        variable = getattr(self.gui, "include_spacing_var", None)
        return True if variable is None else bool(variable.get())

    def _mode_selected(self):
        if hasattr(self.gui, "_모드_선택됨"):
            self.gui._모드_선택됨()

    def set_mode(self, mode):
        """작업 카드를 고른다. 카드는 세 장이며 '한 번에 적용'(all)은 '자간 조정 포함'을 끄면
        서식 적용(format)으로 실행한다. 예전 화면이 보내는 format은 자간 조정을 끈 한 번에 적용이다."""
        if mode not in {"spacing", "unify", "format", "all", "file_format"}:
            raise ValueError("지원하지 않는 작업 방식입니다.")

        def select():
            if self.gui.running:
                return
            internal = mode
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
        if target not in {"hwpx", "pdf", "docx", "epub", *IMAGE_FORMATS}:
            raise ValueError("결과 형식은 HWPX, PDF, DOCX, EPUB, JPG 또는 PNG만 선택할 수 있습니다.")
        def update():
            if not self.gui.running:
                self.conversion_target = target
        self._tk(update)
        return self.get_state()

    def set_include_spacing(self, on):
        """'한 번에 적용'의 '자간 조정 포함'을 바꾸고 그 카드를 고른다(설정 파일에 저장된다)."""
        def update():
            gui = self.gui
            variable = getattr(gui, "include_spacing_var", None)
            if gui.running or variable is None:
                return
            variable.set(bool(on))
            gui.selected_mode.set("all" if on else "format")
            self._mode_selected()

        self._tk(update)
        return self.get_state()

    def _reset_spacing(self):
        return bool(self.gui.stage_choices.get("spacing", {}).get("reset_spacing", True))

    def set_reset_spacing(self, on):
        """'자간 정리'의 '기존 자간 초기화'(세부 작업 01)를 바꾸고 그 카드를 고른다(설정 파일에 저장된다)."""
        def update():
            gui = self.gui
            if gui.running:
                return
            variable = getattr(gui, "reset_spacing_var", None)
            if variable is not None:
                variable.set(bool(on))   # 변경 감시가 세부 작업 값과 설정 파일을 함께 바꾼다
            else:
                gui.stage_choices["spacing"]["reset_spacing"] = bool(on)
            gui.selected_mode.set("spacing")
            self._mode_selected()

        self._tk(update)
        return self.get_state()

    def _table_spacing(self):
        variable = getattr(self.gui, "table_spacing_var", None)
        return True if variable is None else bool(variable.get())

    def set_table_spacing(self, on):
        """'자간 정리'의 '표 내 자간 정리'(설정 table_spacing)를 바꾸고 그 카드를 고른다.

        끄면 표 칸 안 문장은 자간 초기화·자간 조정·줄 병합·단어 검사 대상에서 빠진다. 설정창의
        '표 서식 내 문장도 자간조정하기'와 같은 값이며 설정 파일에 저장된다.
        """
        def update():
            gui = self.gui
            variable = getattr(gui, "table_spacing_var", None)
            if gui.running or variable is None:
                return
            variable.set(bool(on))
            gui.selected_mode.set("spacing")
            self._mode_selected()

        self._tk(update)
        return self.get_state()

    def _exclude_tables(self):
        variable = getattr(self.gui, "exclude_tables_var", None)
        return False if variable is None else bool(variable.get())

    def set_exclude_tables(self, on):
        """'한 번에 적용'의 '표 제외'(설정 all_exclude_tables)를 바꾸고 그 카드를 고른다.

        켜면 표 관련 세부 작업을 모두 빼고 표 칸 안 문장도 자간 작업에서 뺀다. 설정 파일에 저장된다.
        """
        def update():
            gui = self.gui
            variable = getattr(gui, "exclude_tables_var", None)
            if gui.running or variable is None:
                return
            variable.set(bool(on))
            gui.selected_mode.set("all" if self._include_spacing() else "format")
            self._mode_selected()

        self._tk(update)
        return self.get_state()

    # 카드 옵션(설정 키 → 화면 변수, 고르는 카드): 한 번에 적용의 '페이지 맞춤 제외', 서식 통일의 '표 제외'·
    # '자간 정리 제외'·'페이지 맞춤 제외'. 설정 파일에 저장되며, 바꾸면 앱의 변수 감시가 그 카드의 관련 세부 작업을
    # 같이 켜고 끈다(서식 통일의 쪽 맞춤은 세부 작업 기본값이 꺼짐이라 '페이지 맞춤 제외'가 기본 켜짐).
    _CARD_OPTIONS = {
        "all_exclude_pagefit": ("all_exclude_pagefit_var", "all"),
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
            result[key] = False if variable is None else bool(variable.get())
        return result

    def set_card_option(self, key, on):
        """카드 옵션 하나를 바꾸고 그 카드를 고른다."""
        if key not in self._CARD_OPTIONS:
            raise ValueError("지원하지 않는 카드 옵션입니다.")
        name, card = self._CARD_OPTIONS[key]

        def update():
            gui = self.gui
            variable = getattr(gui, name, None)
            if gui.running or variable is None:
                return
            variable.set(bool(on))
            if card == "all":
                gui.selected_mode.set("all" if self._include_spacing() else "format")
            else:
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
            self.gui._범위_끝직접설정 = bool(enabled)
            self.gui._범위_상태_갱신()

        self._tk(update)
        return self.get_state()

    def start(self, mode, range_enabled=False, start="1", end="1"):
        if mode not in {"spacing", "unify", "format", "all", "file_format"}:
            raise ValueError("지원하지 않는 작업 방식입니다.")

        if mode == "file_format":
            # 화면은 준비되지 않은 형식의 시작 버튼을 끄지만, 늦게 온 요청도 여기서 막는다.
            files = self._tk(lambda: list(self.gui.files))
            targets = {item["format"]: item for item in self._conversion_targets(files)}
            chosen = targets.get(self.conversion_target)
            if files and (chosen is None or not chosen.get("enabled")):
                reason = (chosen or {}).get("reason") or "지원하지 않는 결과 형식입니다"
                raise ValueError(f"{self.conversion_target.upper()} 변환을 시작할 수 없습니다: {reason}")
            self._tk(lambda: self.gui.파일포맷_변경_시작(self.conversion_target))
            return self.get_state()

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

    def _configuration(self):
        from docfit_app.configuration_service import ConfigurationService
        return ConfigurationService(self.gui._준말_서비스().settings)

    def get_settings(self):
        return self._tk(lambda: response(lambda: self._configuration().snapshot(running=self.gui.running)))

    def save_settings(self, values, revision):
        def save():
            self._configuration().save(values, revision, running=self.gui.running)
            self.gui._Flutter설정_반영(values)
            return self._configuration().snapshot(running=self.gui.running)
        return self._tk(lambda: response(save))

    def open_settings(self):
        self._tk(self.gui.설정창_열기, timeout=None, front=True)
        return True

    def text_input(self):
        self._tk(self.gui._텍스트로_문서추가_열기, timeout=None, front=True)
        return self.get_state()

    def open_stages(self):
        self._tk(lambda: self.gui._세부작업_열기(
            self.gui.selected_mode.get(), self.gui._세부작업_기본저장.get(self.gui.selected_mode.get(), True)
        ), timeout=None, front=True)
        return True

    def open_log(self):
        self._tk(lambda: (self.gui.log_window.deiconify(), self.gui.log_window.lift()), front=True)
        return True

    def get_log(self):
        """작업 로그 본문은 사용자가 열었을 때만 읽어 보낸다."""
        def read():
            widget = getattr(self.gui, "log_text", None)
            return widget.get("1.0", "end-1c") if widget is not None else ""

        return self._tk(read)

    def clear_log(self):
        """기록 창과 같은 규칙으로, 작업 중에는 로그를 지우지 않는다."""
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
        return {key: pending[key] for key in ("id", "title", "message", "confirm", "choices", "fields")}

    def get_pending_dialog(self):
        return self._tk(self._pending_dialog)

    def enable_close_guard(self):
        with self._close_lock:
            self._close_protocol = True
        return {"ok": True}

    def resolve_dialog(self, identifier, accepted, selection=None, fields=None):
        with self._close_lock:
            host_close = self._close_request is not None and self._close_request["id"] == identifier
            if host_close:
                if not isinstance(accepted, bool):
                    raise ValueError("종료 응답을 확인해 주세요.")
                self._close_request = None
        if host_close:
            if not accepted:
                return {"accepted": False}
            def finish_close():
                # The original OS event was vetoed; the watcher must now destroy
                # the host after Tk stops (unlike the legacy synchronous close).
                self.user_closing = False
                self.gui.종료()
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
                allowed = {item["id"] for item in pending["choices"]}
                if selection is not None and (not isinstance(selection, list) or any(item not in allowed for item in selection)):
                    raise ValueError("검토 항목을 다시 선택해 주세요.")
                allowed_fields = {item["id"] for item in pending["fields"]}
                if fields is not None and (not isinstance(fields, dict) or any(key not in allowed_fields or not isinstance(value, str) for key, value in fields.items())):
                    raise ValueError("검토 값을 확인해 주세요.")
                pending["selection"] = selection if selection is not None else list(allowed)
                pending["values"] = fields or {}
                pending["answer"] = accepted
                pending["done"].set(True)
        self._tk(resolve)
        return {"ok": True}

    def flow_editor(self, action, payload):
        from docfit_app.flow_service import FlowService
        from docfit_app.api_contract import ServiceError
        if not isinstance(payload, dict):
            raise ServiceError("INVALID_INPUT", "입력을 확인해 주세요.")
        store = self._tk(lambda: self.gui._준말_서비스().settings)
        service = FlowService(store._path.parent, store)
        if action == "export_png":
            import os
            import tempfile
            from tkinter import filedialog
            data = service.png_bytes(payload.get("base64"))
            raw_name = payload.get("name", "업무 흐름도")
            name = "".join(c for c in str(raw_name)[:120] if c.isalnum() or c in " _-") or "업무 흐름도"
            selected = self._tk(lambda: filedialog.asksaveasfilename(
                parent=self.gui.root, title="흐름도 PNG 저장", initialfile=name + ".png",
                defaultextension=".png", filetypes=[("PNG 이미지", "*.png")],
            ), front=True)
            if not selected:
                return {"cancelled": True}
            target = Path(selected)
            if target.suffix.lower() != ".png":
                raise ServiceError("INVALID_PATH", "PNG 파일로 저장해 주세요.")
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
        if action == "list":
            return service.list()
        if action == "load":
            return service.load(payload.get("id"))
        if action == "save":
            return service.save(payload.get("id"), payload.get("name"), payload.get("snapshot"), payload.get("revision"))
        if action == "delete":
            return service.delete(payload.get("id"))
        raise ServiceError("INVALID_ACTION", "흐름도 작업을 확인해 주세요.")

    def document_tool(self, name, payload):
        from docfit_app.document_tools_service import DocumentToolsService
        def execute():
            settings = self.gui._준말_서비스().settings
            service = DocumentToolsService(settings._path.parent)
            if name == "add_text":
                if self.gui.running:
                    from docfit_app.api_contract import ServiceError
                    raise ServiceError("JOB_RUNNING", "작업 완료 후 문서를 추가해 주세요.")
                result = service.command(name, payload)
                self.gui.파일추가(result["path"])
                return result
            return service.command(name, payload)
        if name != "add_text":
            folder = self._tk(lambda: self.gui._준말_서비스().settings._path.parent)
            return response(lambda: DocumentToolsService(folder).command(name, payload))
        return self._tk(lambda: response(execute))

    def stage_config(self, action, payload):
        def execute():
            if self.gui.running:
                return
            mode = self.gui.selected_mode.get()
            if mode not in self.gui.stage_choices:
                return  # 파일포맷 변경에는 세부 작업이 없다
            choices = self.gui.stage_choices[mode]
            if action == "all":
                if not isinstance(payload.get("enabled"), bool):
                    raise ValueError("작업 선택 값을 확인해 주세요.")
                for key in choices:
                    choices[key] = payload["enabled"]
            elif action == "defaults":
                for key in choices:
                    choices[key] = default_choice(key, mode)
            else:
                raise ValueError("지원하지 않는 단계 명령입니다.")
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
                raise ServiceError("INVALID_INPUT", "서식 입력을 확인해 주세요.")
            identifier = payload.get("id", "")
            profiles = self._profile_state().profiles
            if identifier not in profiles:
                raise ServiceError("NOT_FOUND", "서식을 다시 선택해 주세요.")
            original = profiles[identifier]
            revision = sha256(json.dumps(original, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            profile = deepcopy(original)
            analysis = profile.setdefault("element_analysis", {})
            if not analysis and not identifier:
                import sys
                source = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "resources" / "서식예시" / "기본 서식.hwpx"
                if source.is_file():
                    analysis = elements.analyze_format_elements(source)
                    profile["element_analysis"] = analysis
            if action in ("save", "restore"):
                if self.gui.running:
                    raise ServiceError("JOB_RUNNING", "작업 중에는 서식을 수정할 수 없습니다.")
                if payload.get("revision") != revision:
                    raise ServiceError("PROFILE_CONFLICT", "서식이 바뀌었습니다. 다시 불러와 주세요.")
                edits = payload.get("edits", [])
                if not isinstance(edits, list) or len(edits) > 2000:
                    raise ServiceError("INVALID_INPUT", "서식 수정 목록을 확인해 주세요.")
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
                                raise ValueError("수정할 수 없는 요소입니다.")
                            value = (item.get("analyzed", item["value"]) if action == "restore"
                                     else elements.parse_value(key, edit["value"]))
                            elements.set_value(analysis, path, key, value)
                        elements.apply_to_profile(profile)
                    except (ValueError, KeyError, TypeError) as exc:
                        raise ServiceError("INVALID_STYLE", str(exc)) from exc
                    if not identifier:
                        identifier = uuid.uuid4().hex
                        profile["name"] = profile.get("name", "기본 서식") + " (사용자 수정)"
                    try:
                        self.gui._서식_파일_저장(identifier, profile)
                    except OSError as exc:
                        raise ServiceError("PROFILE_SAVE_FAILED", "서식 파일을 저장하지 못했습니다.") from exc
                    profiles[identifier] = profile
                    self.gui._활성_서식_프로파일 = identifier
                    self.gui._프로파일_목록갱신()
                    self.gui._프로파일_선택()
                    self.invalidate_format_coverage(identifier)
                    revision = sha256(json.dumps(profile, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            elif action != "get":
                raise ServiceError("INVALID_ACTION", "지원하지 않는 서식 명령입니다.")
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

    def table_template(self, action, payload):
        from docfit_app.table_template_service import TableTemplateService
        def execute():
            if action != "get":
                self.gui._준말_서비스()._editable(self.gui.running)
            data = dict(payload) if isinstance(payload, dict) else payload
            if action == "learn" and isinstance(data, dict) and not data.get("path"):
                from tkinter import filedialog
                path = filedialog.askopenfilename(parent=self.gui.root,
                    title="기본 데이터 표 서식 학습", filetypes=[("HWPX 문서", "*.hwpx")])
                if not path:
                    return TableTemplateService(self.gui._준말_서비스()).snapshot()
                data["path"] = path
            result = TableTemplateService(self.gui._준말_서비스()).command(
                action, data, running=self.gui.running)
            return result
        return self._tk(lambda: response(execute), front=action == "learn")

    def get_abbreviations(self):
        return self._tk(lambda: response(lambda: self.gui._준말_서비스().snapshot(running=self.gui.running)))

    def save_abbreviation(self, key, kind, value, original_key=""):
        return self._tk(lambda: response(lambda: self.gui._준말_서비스().save(
            key, kind, value, original_key, running=self.gui.running)))

    def delete_abbreviation(self, key):
        return self._tk(lambda: response(lambda: self.gui._준말_서비스().delete(key, running=self.gui.running)))

    def set_abbreviation_defaults(self, enabled):
        return self._tk(lambda: response(lambda: self.gui._준말_서비스().set_defaults(enabled, running=self.gui.running)))

    def open_results(self):
        self._tk(self.gui._결과파일_열기, timeout=None, front=True)
        return True

    def _result_path(self, index):
        try:
            return getattr(self.gui, "_결과목록", [])[int(index)].get("결과", "")
        except (IndexError, TypeError, ValueError):
            return ""

    def open_result(self, index):
        """결과 파일 하나를 연결된 프로그램(한/글)으로 연다."""
        def open_one():
            path = self._result_path(index)
            if path and os.path.isfile(path):
                self.gui._경로_열기(path)
            else:
                self.gui.status_var.set("결과 파일을 찾을 수 없습니다. 옮기거나 지우지 않았는지 확인해 주세요.")

        self._tk(open_one, timeout=None, front=True)
        return self.get_state()

    def show_result(self, index):
        """탐색기에서 결과 파일이 있는 폴더를 열고 그 파일을 선택해 둔다."""
        def reveal():
            path = self._result_path(index)
            if path and os.path.isfile(path) and os.name == "nt":
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            elif path and os.path.isdir(os.path.dirname(path)):
                self.gui._경로_열기(os.path.dirname(path))
            else:
                self.gui.status_var.set("결과 폴더를 찾을 수 없습니다.")

        self._tk(reveal, timeout=None, front=True)
        return self.get_state()

    def _stages_changed(self, mode):
        """세부 작업을 바꾼 뒤 그 카드 옵션(표 제외·페이지 맞춤 제외 등)을 세부 작업에 맞춘다."""
        if hasattr(self.gui, "_세부작업_옵션_맞춤"):
            self.gui._세부작업_옵션_맞춤(mode)

    def set_stage(self, key, on):
        """현재 작업 유형의 세부 작업 하나를 켜고 끈다. 기본값 저장을 켠 유형이면 바로 저장한다.

        카드 옵션과 연동된 작업이면 옵션도 바뀐다(예: 표 작업을 하나라도 켜면 '표 제외'가 꺼진다).
        """
        def update():
            gui = self.gui
            mode = gui.selected_mode.get()
            if gui.running or key not in gui.stage_choices.get(mode, {}):
                return
            gui.stage_choices[mode][key] = bool(on)
            if gui._세부작업_기본저장.get(mode):
                gui._세부작업_기본값_저장(mode)
            self._stages_changed(mode)
            gui._요약갱신()

        self._tk(update)
        return self.get_state()

    def reset_stages(self):
        """현재 작업 유형의 세부 작업을 처음 기본값으로 되돌린다(카드 옵션도 그에 맞춘다)."""
        def reset():
            gui = self.gui
            mode = gui.selected_mode.get()
            if gui.running or mode not in gui.stage_choices:
                return
            gui.stage_choices[mode] = {key: default_choice(key, mode) for key, _ in stages_for_mode(mode)}
            if gui._세부작업_기본저장.get(mode):
                gui._세부작업_기본값_저장(mode)
            self._stages_changed(mode)
            gui._요약갱신()

        self._tk(reset)
        return self.get_state()

    def set_stage_default(self, save):
        """현재 구성을 다음 실행에도 쓸지 정한다. 끄면 저장한 구성을 지워 처음 기본값으로 시작한다."""
        def update():
            if not self.gui.running:
                self.gui._세부작업_기본값_저장(self.gui.selected_mode.get(), bool(save))

        self._tk(update)
        return self.get_state()

    def set_profile(self, identifier):
        """서식 적용에 쓸 서식(프로파일)을 고른다. 기존 콤보 선택과 같은 경로로 반영한다."""
        def select():
            gui = self.gui
            ids = list(self._profile_state().profile_ids or [])
            combo = getattr(gui, "main_profile_combo", None)
            if gui.running or identifier not in ids or combo is None:
                return
            combo.current(ids.index(identifier))
            gui._프로파일_선택(SimpleNamespace(widget=combo))

        self._tk(select)
        return self.get_state()

    # ---- 서식 관리(예시 보고서로 서식 복제·이름 바꾸기·세부 수정·삭제) ----
    def set_drop_target(self, target):
        """끌어 놓은 파일을 넣을 곳을 바꾼다: documents(문서 목록) 또는 format(예시 서식 복제)."""
        if target not in ("documents", "format"):
            raise ValueError("지원하지 않는 놓기 대상입니다.")
        self.drop_target = target
        window = self.window
        if window is not None and hasattr(window, "run_js"):
            text = ("여기에 놓으면 이 보고서의 서식을 복제합니다" if target == "format"
                    else "여기에 놓으면 문서 목록에 추가됩니다")
            try:
                window.run_js(f"window.docfitDropText = {text!r};")
            except Exception:
                logging.getLogger(__name__).debug("drop text update failed", exc_info=True)
        return self.get_state()

    def add_format_paths(self, paths):
        """끌어 놓은 예시 보고서(HWP/HWPX) 중 첫 파일의 서식을 분석해 새 서식으로 복제한다."""
        candidates = [str(value or "").strip() for value in (paths or [])]
        candidates = [path for path in candidates if Path(path).suffix.lower() in (".hwp", ".hwpx")]

        def start():
            gui = self.gui
            if gui.running or self._profile_state().analyzing_format:
                gui.status_var.set("작업이나 서식 분석이 끝난 뒤 다시 놓아 주세요.")
                return
            if not candidates:
                gui.status_var.set("서식을 복제하려면 HWP 또는 HWPX 예시 보고서를 놓아 주세요.")
                return
            if len(candidates) > 1:
                gui.로그표시(f"예시 보고서는 한 번에 하나씩 복제합니다: {Path(candidates[0]).name}")
            gui._서식_분석_시작(candidates[0], 이름묻기=False)

        self._tk(start)
        return self.get_state()

    def receive_drop(self, paths):
        """창에 끌어 놓은 파일: '서식 관리' 창이 열려 있으면 예시 서식 복제, 아니면 문서 목록에 추가."""
        if self.drop_target == "format":
            return self.add_format_paths(paths)
        return self.add_paths(paths, from_drop=True)

    def add_format_file(self):
        """예시 보고서 파일을 골라 서식을 복제한다."""
        self._tk(self.gui._서식_파일에서_추가, timeout=None, front=True)
        return self.get_state()

    def write_format_example(self):
        """빈 한/글 문서에 예시를 직접 써서 서식을 만든다."""
        self._tk(self.gui._서식_예시편집_시작, timeout=None, front=True)
        return self.get_state()

    def _with_notice(self, message):
        state = self.get_state()
        if message:
            state["notice"] = message
        return state

    def rename_profile(self, identifier, name, organization=""):
        """서식 이름(과 기관)을 바꾼다. 안 되면 notice에 이유를 담아 돌려준다."""
        return self._with_notice(self._tk(lambda: self.gui._서식_이름_저장(str(identifier or ""), name, organization)))

    def delete_profile(self, identifier):
        """서식을 삭제한다(확인은 화면이 한다). 기본 서식은 삭제하지 않는다."""
        return self._with_notice(self._tk(lambda: self.gui._서식_삭제(str(identifier or ""))))

    def edit_profile(self, identifier):
        """서식 세부사항 창을 열어 대표값을 고친다(창을 닫을 때까지 기다린다)."""
        self._tk(lambda: self.gui._서식_수정하기(str(identifier or "")), timeout=None, front=True)
        return self.get_state()

    def show_format_example(self):
        """지금 고른 서식을 입힌 예시 보고서를 만들어 한/글로 보여 준다(만드는 동안 작업 진행이 화면에 보인다)."""
        self._tk(self.gui._서식예시_확인)
        return self.get_state()

    def format_gallery(self):
        """키오스크식 서식 고르기: 서식마다 예시 첫 쪽 그림(스틸컷, JPEG data URI 또는 None)과 이름·기관·사용 중 여부."""
        def collect():
            items = []
            still = getattr(self.gui, "_서식_스틸컷", None)
            make = getattr(self.gui, "_썸네일_만들기_시작", None)
            need = getattr(self.gui, "_썸네일_필요한_서식", None)
            if make is not None and need is not None:
                make(need())          # 미리보기 그림이 없는 예시는 백그라운드에서 썸네일을 만든다(다음에 열 때 보임)
            for item in self._profiles():
                data = still(item["id"], 300, "JPEG") if still is not None else None
                image = "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii") if data else None
                items.append(dict(item, image=image))
            return items

        return self._tk(collect)

    def open_format_samples(self):
        """서식예시 폴더(C:\\HWP_AUTODOCFIT\\서식예시)를 탐색기로 연다(알파). 예시 파일을 고치면 '한 번에 적용' 때 반영된다."""
        opener = getattr(self.gui, "_서식예시_폴더_열기", None)
        if opener is not None:
            self._tk(opener)
        return self.get_state()

    def set_option(self, name, value):
        """빠른 설정의 켜기·끄기 값을 바꾼다. 앱 설정 변수의 변경 감시가 설정 파일에 저장한다."""
        attribute = QUICK_OPTIONS.get(name)
        if attribute is None:
            raise ValueError("지원하지 않는 설정입니다.")

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
            self.gui.목록지우기()
            self.gui._결과_초기화()
            self.gui._안내키, self.gui._안내지남 = None, set()
            self.gui.status_var.set("새 문서를 선택하세요.")
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
        developer = getattr(self.gui, "developer_mode_var", None)
        if developer is not None and not developer.get():
            raise ValueError("문서 도구는 설정에서 개발자 모드를 켜야 사용할 수 있습니다.")
        self._tk(command, timeout=None, front=True)
        return True

    def request_close(self):
        """OS 창 닫기 전에 기존 앱의 종료 확인·작업 중단 절차를 수행한다."""
        if self.tk_stopped is not None and self.tk_stopped.is_set():
            return True
        with self._close_lock:
            if self._close_protocol:
                if self._close_request is None:
                    import uuid
                    self._close_request = {"id": uuid.uuid4().hex, "kind": "app_close"}
                return False  # Never block the native closing event for JS.
        def defer_confirmation():
            if not (getattr(self.gui.root, "_docfit_hidden_backend", False) and self.gui.running):
                return False
            if not getattr(self, "_close_prompt_queued", False):
                self._close_prompt_queued = True
                def ask_after_os_close_returns():
                    try:
                        self.gui.종료()
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
            self.gui.종료()
            try:
                closed = not bool(self.gui.root.winfo_exists())
            except Exception:
                closed = True
            if not closed:
                self.user_closing = False   # 작업 중 종료를 취소한 경우
            return closed

        # 작업 중이면 종료 확인 창이 떠서 사용자의 답을 기다린다.
        try:
            return self._tk(close, timeout=None, front=True)
        except RuntimeError:
            # 종료 callback이 root.destroy를 호출하면 자신의 Future도 종료된다.
            if self.tk_stopped is not None and self.tk_stopped.is_set():
                return True
            raise


class _BrowserApi:
    """Expose commands only: pywebview recursively inspects public attributes."""

    def __init__(self, bridge):
        for name in (
            "get_state", "add_files", "add_folder", "add_paths", "remove_file",
            "clear_files", "set_mode", "set_range", "start", "stop",
            "open_settings", "get_settings", "save_settings", "text_input", "open_stages", "open_log", "get_log", "clear_log",
            "get_pending_dialog", "resolve_dialog", "enable_close_guard", "format_profile", "flow_editor", "document_tool", "stage_config", "table_template", "get_abbreviations", "save_abbreviation", "delete_abbreviation", "set_abbreviation_defaults",
            "open_results", "next_job", "run_tool", "open_result",
            "show_result", "set_stage", "reset_stages", "set_stage_default",
            "set_profile", "set_option", "set_include_spacing", "set_reset_spacing", "set_table_spacing",
            "set_exclude_tables", "set_card_option",
            "set_drop_target", "add_format_file", "write_format_example", "rename_profile", "delete_profile",
            "edit_profile", "show_format_example", "open_format_samples", "format_gallery",
            "set_conversion_target",
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
  overlay.textContent = window.docfitDropText || '여기에 놓으면 문서 목록에 추가됩니다';
  overlay.style.cssText = 'display:none;position:fixed;inset:16px;z-index:2147483647;'
    + 'pointer-events:none;align-items:center;justify-content:center;border:3px dashed #2563eb;'
    + 'border-radius:24px;background:rgba(239,246,255,.94);color:#1e40af;'
    + 'font:600 20px sans-serif;text-align:center;padding:24px;';
  document.body.appendChild(overlay);
  const files = e => Array.from(e.dataTransfer?.types || []).includes('Files');
  const hide = () => { depth = 0; overlay.style.display = 'none'; };
  document.addEventListener('dragenter', e => {
    if (!files(e)) return;
    overlay.textContent = window.docfitDropText || '여기에 놓으면 문서 목록에 추가됩니다';
    e.preventDefault(); depth++; overlay.style.display = 'flex';
  }, true);
  document.addEventListener('dragover', e => {
    if (!files(e)) return;
    e.preventDefault(); e.dataTransfer.dropEffect = 'copy';
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
                bridge.receive_drop(paths)
            elif files:
                bridge._tk(lambda: bridge.gui.status_var.set(
                    "드롭한 파일 경로를 읽지 못했습니다. 문서 선택 버튼을 이용해 주세요."))
                logging.getLogger(__name__).warning("File drop received without native paths")
        except Exception:
            logging.getLogger(__name__).exception("File drop failed")

    # Register with pywebview (not plain JS) so WebView2 supplies full file paths.
    web_window.dom.document.events.drop += DOMEventHandler(
        dropped, prevent_default=True, stop_propagation=True)
    web_window.run_js(_FILE_DROP_SCRIPT)


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
        # A filesystem path activates pywebview's local HTTP asset server;
        # file:// URLs bypass it and cannot load Flutter's WASM/font assets.
        url=str(page),
        js_api=_BrowserApi(bridge),
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
        bridge._shutdown()
        original_destroy()

    gui.root.destroy = tracked_destroy

    def bind_file_drop(web_window):
        try:
            _bind_file_drop(web_window, bridge)
        except Exception:
            logging.getLogger(__name__).exception("Could not enable file drag and drop")

    def stop_webview_when_app_exits(web_window):
        tk_stopped.wait()
        if bridge.user_closing:
            # 사용자가 웹 창을 닫는 중이면 창이 스스로 닫힌다. 여기서 destroy()를 또 부르면
            # pywebview가 닫힘 처리를 두 번 실행해 .NET '처리되지 않은 예외' 창이 뜬다.
            return
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

    # 창 아이콘: 지정하지 않으면 실행 파일(python.exe 또는 exe)의 아이콘을 쓴다.
    아이콘 = {"icon": APP_ICON} if APP_ICON and Path(APP_ICON).is_file() else {}
    webview.start(initialize_webview, args=[window], gui="edgechromium", http_server=True, **아이콘)
    return True


# Application values are injected by the entry point after import.
APP_VERSION = ""
APP_NAME = ""
APP_ICON = ""
