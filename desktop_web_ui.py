"""Tk 기반 문서 처리 기능을 반응형 WebView 화면에 연결한다."""

from __future__ import annotations

import importlib.util
import logging
import os
import subprocess
import threading
from concurrent.futures import Future, TimeoutError
from pathlib import Path
from types import SimpleNamespace

from docfit_core.progress_guide import guide_state
from docfit_core.stage_selection import STAGE_EXAMPLES, default_choice, stages_for_mode

# 화면에서 바로 켜고 끄는 공통 설정(이름 → 앱의 Tk 변수 속성). 값을 바꾸면 앱이 설정 파일에 저장한다.
def _format_coverage(analysis):
    try:
        from docfit_core.format_elements import coverage
        return coverage(analysis)
    except Exception:
        return None


QUICK_OPTIONS = {
    "autoclose": "autoclose_var",
    "verify": "verify_var",
    "check_updates": "check_updates_on_start_var",
    "developer_mode": "developer_mode_var",
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

    def _tk(self, callback, timeout=120, front=False):
        result = Future()

        def run():
            if result.cancelled():
                return
            if front:
                try:
                    # 파일 선택 등 기본 창을 부모로 쓰는 대화상자가 웹 화면 뒤에 뜨지 않게 한다.
                    self.gui.root.lift()
                    self.gui.root.focus_force()
                except Exception:
                    pass
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

    def _profiles(self):
        """서식 목록: 표시 이름(기관 포함), 이름·기관, 기본 서식 여부, 예시 파일 이름, 사용 중 여부."""
        gui = self.gui
        profiles = getattr(gui, "_프로파일들", {}) or {}
        ids = getattr(gui, "_프로파일_ids", None) or list(profiles)
        active = getattr(gui, "_활성_서식_프로파일", "")
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
                "coverage": _format_coverage(analysis) if analysis else None,
            })
        return items

    def _format_task(self):
        gui = self.gui
        return {"busy": bool(getattr(gui, "_서식분석중", False)),
                "file": str(getattr(gui, "_서식분석_파일", "") or "")}

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
                "stages": self._stages(mode),
                "profiles": self._profiles(),
                "profile": getattr(gui, "_활성_서식_프로파일", ""),
                "format_task": self._format_task(),
                "drop_target": self.drop_target,
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
                "can_start": bool(gui.files) and not gui.running,
                "version": APP_VERSION,
            }

        return self._tk(snapshot)

    def add_files(self):
        self._tk(self.gui.파일선택, timeout=None, front=True)
        return self.get_state()

    def add_folder(self):
        self._tk(self.gui._폴더선택, timeout=None, front=True)
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

    def _include_spacing(self):
        variable = getattr(self.gui, "include_spacing_var", None)
        return True if variable is None else bool(variable.get())

    def _mode_selected(self):
        if hasattr(self.gui, "_모드_선택됨"):
            self.gui._모드_선택됨()

    def set_mode(self, mode):
        """작업 카드를 고른다. 카드는 세 장이며 '한 번에 적용'(all)은 '자간 조정 포함'을 끄면
        서식 적용(format)으로 실행한다. 예전 화면이 보내는 format은 자간 조정을 끈 한 번에 적용이다."""
        if mode not in {"spacing", "unify", "format", "all"}:
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
            if gui.running:
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
            ids = list(getattr(gui, "_프로파일_ids", []) or [])
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
            if gui.running or getattr(gui, "_서식분석중", False):
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
        return self.add_paths(paths)

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
        return self._tk(close, timeout=None, front=True)


class _BrowserApi:
    """Expose commands only: pywebview recursively inspects public attributes."""

    def __init__(self, bridge):
        for name in (
            "get_state", "add_files", "add_folder", "add_paths", "remove_file",
            "clear_files", "set_mode", "set_range", "start", "stop",
            "open_settings", "text_input", "open_stages", "open_log",
            "open_results", "next_job", "run_tool", "open_result",
            "show_result", "set_stage", "reset_stages", "set_stage_default",
            "set_profile", "set_option", "set_include_spacing", "set_reset_spacing", "set_table_spacing",
            "set_exclude_tables", "set_card_option",
            "set_drop_target", "add_format_file", "write_format_example", "rename_profile", "delete_profile",
            "edit_profile", "show_format_example",
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
        tk_stopped.set()
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

    webview.start(initialize_webview, args=[window], gui="edgechromium", http_server=True)
    return True


# Application values are injected by the entry point after import.
APP_VERSION = ""
APP_NAME = ""
STAGE_ORDER = ("열기", "서식", "자간", "줄 병합", "페이지 배치", "저장")
