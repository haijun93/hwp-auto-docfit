"""Extracted docfit_ui.legacy definitions; installed into the compatibility session.

Original algorithms and comments are preserved. Runtime bindings are session-local;
see docfit_engine.runtime. This module does not import the application bootstrap.
"""
from docfit_engine.runtime import bind_function, bind_class

def _install(*, _docfit_namespace, _docfit_symbol):
    global 창_맨앞으로, 색_rgb, LiveStageBoard, HwpAutoDocFitGUI, _새창_맨앞으로, 웹모드_기본창_숨김, 웹모드_기본창_복원
    if _docfit_symbol == '창_맨앞으로':
        def 창_맨앞으로(window):
            """대화상자를 한글·웹 화면 창에 가려지지 않게 맨 앞으로 올린다.

            웹 화면 모드에서는 Tk 기본 창이 숨겨져 있어 그 창에 딸린(transient) 대화상자도 보이지 않으므로
            딸림을 풀고 올린다.
            """
            try:
                if window._root().state() == "withdrawn":
                    window.wm_transient("")
                window.deiconify()
                window.lift()
                window.attributes("-topmost", True)
                window.after(300, lambda: window.attributes("-topmost", False))
                window.focus_force()
            except tk.TclError:
                pass
        return bind_function(창_맨앞으로, _docfit_namespace)
    if _docfit_symbol == '색_rgb':
        def 색_rgb(color):
            """Tk 진행 표시용 #RGB/#RRGGBB 색상을 정수 RGB 튜플로 바꾼다."""
            value = str(color).strip().lstrip("#")
            if len(value) == 3:
                value = "".join(character * 2 for character in value)
            if len(value) != 6:
                raise ValueError(f"잘못된 색상 값: {color}")
            return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))
        return bind_function(색_rgb, _docfit_namespace)
    if _docfit_symbol == 'LiveStageBoard':
        class LiveStageBoard(_docfit_namespace['tk'].Canvas):
            """실제 단계 이벤트를 표시. 점멸은 실행 표시이며 완료율 추정이 아니다."""
            def __init__(self, parent):
                super().__init__(parent, height=50, bg=UI_COLORS['bg'], highlightthickness=0)
                self.active = None
                self.visited = set()
                self.started = time.monotonic()
                self.last_signal = self.started
                self.detail = '작업 대기'
                self.outcome = None
                self.ended = None
                self.result_message = None   # 작업이 모두 끝났을 때 보여 줄 메시지(예: 절약된 시간)
                self.job = None
                self._draw_error_reported = False
                self.bind('<Destroy>', self._destroy, add='+')
                self._frame()

            def reset(self):
                self.active = None
                self.visited.clear()
                self.outcome = None
                self.ended = None
                self.result_message = None
                self.detail = '문서 처리 준비'
                self.signal()
                self.draw()

            def signal(self, detail=None):
                self.last_signal = time.monotonic()
                if detail is not None:
                    self.detail = str(detail)

            def activate(self, stage):
                if stage not in 진행단계_순서:
                    return
                if stage != self.active:
                    if self.active:
                        self.visited.add(self.active)
                    self.active = stage
                    self.started = time.monotonic()
                self.outcome = None
                self.ended = None
                self.signal()
                self.draw()

            def set_result_message(self, message):
                self.result_message = message
                self.draw()

            def finish(self, outcome):
                self.outcome = outcome
                self.ended = time.monotonic()
                self.signal()
                self.draw()

            def _destroy(self, event):
                if event.widget is self and self.job is not None:
                    self.after_cancel(self.job)
                    self.job = None

            def _frame(self):
                self.job = None
                try:
                    mapped = self.winfo_ismapped()
                    if mapped:
                        self.draw()
                        self._draw_error_reported = False
                except Exception as exc:
                    # 진행 표시 오류가 Tk의 예약 콜백을 끊어 GUI 이벤트 큐까지
                    # 멈추게 하지 않도록 진단만 남기고 다음 프레임을 계속 예약한다.
                    if not self._draw_error_reported:
                        진단로그(f"[진행 표시] 다시 그리기 실패(작업 계속): {exc}")
                        self._draw_error_reported = True
                    mapped = False
                try:
                    self.job = self.after(66 if mapped else 250, self._frame)
                except tk.TclError:
                    self.job = None

            def draw(self):
                self.delete('all')
                now = time.monotonic()
                width = max(1, self.winfo_width())
                for i, stage in enumerate(진행단계_순서):
                    left, right = i*width/6+2, (i+1)*width/6-2
                    current = self.active == stage
                    busy = current and self.outcome is None
                    # 처리한 단계는 진한 색 바탕 + 흰 글씨로 표시한다(아직 처리 전 단계만 연한 색).
                    # 색은 모두 앱 테마 청록(UI_COLORS['teal'])에서 이어 받는다.
                    #   처리한 칸 = 테마 청록 / 완료 = 진한 청록 / 진행 중 = 진한 청록↔더 진한 청록 깜빡임
                    fill, prefix, text_color = '#f0ece8', '', UI_COLORS['ink']
                    if stage in self.visited:
                        fill, prefix, text_color = UI_COLORS['teal'], '· ', 'white'
                    if current:
                        text_color = 'white'
                        if self.outcome:
                            fill = '#B85A22' if self.outcome != '완료' else UI_COLORS['teal_dark']
                            prefix = '✓ ' if self.outcome == '완료' else '■ '
                        else:
                            mix = .5 + .5*math.sin(now*3)
                            low = 색_rgb(UI_COLORS['teal_dark'])
                            high = tuple(round(v*0.72) for v in low)
                            fill = '#'+''.join(f'{round(a+(b-a)*mix):02x}' for a,b in zip(low, high))
                    self.create_rectangle(left,2,right,27,fill=fill,outline='')
                    self.create_text((left+right)/2+6,14,text=prefix+stage,fill=text_color,font=('맑은 고딕',8,'bold' if current else 'normal'))
                    if busy:
                        angle = (now*230)%360
                        self.create_arc(left+5,8,left+16,19,start=angle,extent=265,style='arc',outline='white',width=2)
                if self.active:
                    elapsed = int((self.ended or now)-self.started)
                    silent = int(now-self.last_signal)
                    message = f'{self.active} · {self.outcome or "실행 중"} · {elapsed}초'
                    if self.outcome is None and silent >= 15:
                        message += f'   |   한글 응답 대기 {silent}초 · 중단은 현재 호출 반환 후 적용'
                    elif self.outcome is None:
                        message += f'   |   마지막 처리 신호 {silent}초 전'
                else:
                    message = self.outcome or ''
                font = ('맑은 고딕',8)
                if self.outcome == '완료' and self.result_message:
                    message, font = self.result_message, ('맑은 고딕',9,'bold')
                self.create_text(5,39,anchor='w',text=message,fill=UI_COLORS['teal_dark'],font=font)


        # ============================================================
        # GUI 클래스
        # ============================================================
                self.scale('all', 0, 0, .6, .6)
                for item in self.find_all():
                    if self.type(item) == 'text':
                        self.itemconfigure(item, font=('맑은 고딕', 7), width=66)
        return bind_class(LiveStageBoard, _docfit_namespace)
    if _docfit_symbol == 'HwpAutoDocFitGUI':
        class HwpAutoDocFitGUI:

            @property
            def state(self):
                from docfit_core.app_state import AppState
                if "_app_state" not in self.__dict__:
                    self._app_state = AppState()
                return self._app_state

            @property
            def files(self):
                return self.state.files

            @files.setter
            def files(self, value):
                self.state.files = value

            @property
            def running(self):
                return self.state.running

            @running.setter
            def running(self, value):
                self.state.running = value

            @property
            def stage_choices(self):
                return self.state.stage_choices

            @stage_choices.setter
            def stage_choices(self, value):
                self.state.stage_choices = value

            @property
            def _세부작업_기본저장(self):
                return self.state.default_saved

            @_세부작업_기본저장.setter
            def _세부작업_기본저장(self, value):
                self.state.default_saved = value

            @property
            def _프로파일들(self):
                return self.state.profiles

            @_프로파일들.setter
            def _프로파일들(self, value):
                self.state.profiles = value

            @property
            def _프로파일_ids(self):
                return self.state.profile_ids

            @_프로파일_ids.setter
            def _프로파일_ids(self, value):
                self.state.profile_ids = value

            @property
            def _활성_서식_프로파일(self):
                return self.state.active_profile_id

            @_활성_서식_프로파일.setter
            def _활성_서식_프로파일(self, value):
                self.state.active_profile_id = value

            @property
            def _서식분석중(self):
                return self.state.analyzing_format

            @_서식분석중.setter
            def _서식분석중(self, value):
                self.state.analyzing_format = value

            @property
            def _서식분석_파일(self):
                return self.state.analyzing_file

            @_서식분석_파일.setter
            def _서식분석_파일(self, value):
                self.state.analyzing_file = value

            @property
            def _결과목록(self):
                return self.state.results

            @_결과목록.setter
            def _결과목록(self, value):
                self.state.results = value

            FOOTER_NOTE_DEFAULT = "정리된 HWPX는 원본 폴더에 저장되며, 같은 이름의 기존 결과를 바꿉니다."

            def __init__(self, root):
                global _서식통일_대표값_검토콜백
                self.root = root
                from docfit_ui.scheduler import install_scheduler
                install_scheduler(self)
                _서식통일_대표값_검토콜백 = self._서식통일_대표값_검토_요청
                self.files = []
                self.worker = None
                self.running = False
                self.stage_choices = {mode: {key: stage_default(key, mode) for key, _ in stages_for_mode(mode)}
                                      for mode in ("spacing", "unify", "format", "all")}
                self._세부작업_기본저장 = {mode: False for mode in self.stage_choices}
                self.closing = False

                self.compare_toplevel = None
                self.compare_left_frame = None
                self.compare_right_frame = None

                root.title(f"{APP_NAME} · v{APP_VERSION}")
                # 화면 해상도와 Windows 배율에 맞춰 초기 크기와 최소 크기를 산정한다.
                self._반응형_예약 = None
                screen_width = root.winfo_screenwidth()
                screen_height = root.winfo_screenheight()
                try:
                    scale = float(root.tk.call("tk", "scaling"))
                except (tk.TclError, ValueError, TypeError):
                    scale = 1.0
                self._ui_scale = max(0.85, min(1.6, scale / (96 / 72)))
                safe_width = max(440, screen_width - max(32, round(48 * self._ui_scale)))
                safe_height = max(420, screen_height - max(64, round(96 * self._ui_scale)))
                width = min(round(960 * self._ui_scale), safe_width)
                height = min(round(760 * self._ui_scale), safe_height)
                root.geometry(f"{width}x{height}")
                self._minimum_width = min(round(520 * self._ui_scale), safe_width)
                self._minimum_height = min(round(480 * self._ui_scale), safe_height)
                root.minsize(self._minimum_width, self._minimum_height)
                root.resizable(True, True)
                self._테마_적용()
                root.grid_columnconfigure(0, weight=1)
                root.grid_rowconfigure(1, weight=1)
                pad = max(12, round(24 * self._ui_scale))
                header = ttk.Frame(root, padding=(pad, max(10, round(18 * self._ui_scale)), pad,
                                                 max(8, round(14 * self._ui_scale))), style="Header.TFrame")
                header.grid(row=0, column=0, sticky="ew")
                header.grid_columnconfigure(0, weight=1)
                ttk.Label(header, text="문서 정리", style="AppTitle.TLabel").grid(row=0, column=0, sticky="w")
                ttk.Label(header, text="파일을 고르고 정리 방식을 선택하세요.",
                          style="HeaderHint.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 0))
                self.header_status = ttk.Label(header, text="새 작업", style="HeaderStatus.TLabel")
                self.header_status.grid(row=0, column=1, rowspan=2, sticky="e", padx=(18, 0))
                main_host = ttk.Frame(root, style="Main.TFrame")
                main_host.grid(row=1, column=0, sticky="nsew")
                main_host.grid_columnconfigure(0, weight=1)
                main_host.grid_rowconfigure(0, weight=1)
                main_canvas = tk.Canvas(main_host, bg=UI_COLORS["bg"], highlightthickness=0)
                main_canvas.grid(row=0, column=0, sticky="nsew")
                main_scrollbar = ttk.Scrollbar(main_host, orient="vertical", command=main_canvas.yview)
                main_scrollbar.grid(row=0, column=1, sticky="ns")
                main_canvas.configure(yscrollcommand=main_scrollbar.set)
                main = ttk.Frame(main_canvas, padding=(pad, 0, pad, 0), style="Main.TFrame")
                main_window = main_canvas.create_window((0, 0), window=main, anchor="nw")
                main.bind("<Configure>", lambda _e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
                main_canvas.bind("<Configure>", lambda e: main_canvas.itemconfigure(main_window, width=e.width))
                self.main_canvas = main_canvas
                self.main_scrollbar = main_scrollbar
                main.grid_columnconfigure(0, weight=1)
                main.grid_rowconfigure(0, weight=3, minsize=round(170 * self._ui_scale))
                main.grid_rowconfigure(1, weight=0)
                main.grid_rowconfigure(2, weight=2, minsize=round(105 * self._ui_scale))
                card_padding = max(8, round(14 * self._ui_scale))
                file_frame = ttk.LabelFrame(main, text="문서", padding=card_padding, style="Card.TLabelframe")
                file_frame.grid(row=0, column=0, sticky="nsew")
                self.file_frame = file_frame
                file_frame.grid_columnconfigure(0, weight=1)
                file_frame.grid_rowconfigure(1, weight=1)
                self.drop_label = ttk.Label(file_frame, text="파일 또는 폴더를 끌어 놓거나 ‘파일 추가’를 선택하세요  ·  HWP, HWPX, TXT, MD, DOC(X), PDF", anchor="center", padding=(10, 10), style="Drop.TLabel")
                self.drop_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))
                self.drop_label.drop_target_register(DND_FILES)
                self.drop_label.dnd_bind("<<Drop>>", self.파일_드롭)
                self.drop_label.bind("<Button-1>", lambda e: self.파일선택())
                list_frame = ttk.Frame(file_frame)
                list_frame.grid(row=1, column=0, sticky="nsew")
                list_frame.grid_columnconfigure(0, weight=1)
                list_frame.grid_rowconfigure(0, weight=1)
                scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
                scrollbar.grid(row=0, column=1, sticky="ns")
                self.file_list = tk.Listbox(list_frame, font=("맑은 고딕", 10), height=6,
                    background=UI_COLORS["surface"], foreground=UI_COLORS["ink"], selectbackground=UI_COLORS["teal"],
                    selectforeground="white", relief="flat", highlightthickness=1,
                    highlightbackground=UI_COLORS["separator"], selectmode="extended", exportselection=False,
                    yscrollcommand=scrollbar.set)
                self.file_list.grid(row=0, column=0, sticky="nsew")
                scrollbar.config(command=self.file_list.yview)
                xscroll = ttk.Scrollbar(list_frame, orient="horizontal", command=self.file_list.xview)
                xscroll.grid(row=1, column=0, sticky="ew")
                self.file_list.config(xscrollcommand=xscroll.set)
                self.file_list.drop_target_register(DND_FILES)
                self.file_list.dnd_bind("<<Drop>>", self.파일_드롭)
                self.file_list.bind("<Double-Button-1>", self._문서_열기)
                file_actions = ttk.Frame(file_frame)
                self.file_actions = file_actions
                file_actions.grid(row=2, column=0, sticky="ew", pady=(4, 0))
                self.file_buttons = []
                for title, command in (("파일 추가", self.파일선택), ("폴더 추가", self._폴더선택)):
                    button = ttk.Button(file_actions, text=title, command=command)
                    button.pack(side="left", padx=(0, 6))
                    self.file_buttons.append(button)
                self.file_manage_button = ttk.Menubutton(file_actions, text="목록 관리 ▾")
                self.file_manage_menu = tk.Menu(self.file_manage_button, tearoff=False)
                self.file_manage_menu.add_command(label="선택 항목 제거", command=self._선택삭제)
                self.file_manage_menu.add_command(label="목록 비우기", command=self.목록지우기)
                self.file_manage_button["menu"] = self.file_manage_menu
                self.file_manage_button.pack(side="left", padx=(0, 6))
                self.file_buttons.append(self.file_manage_button)
                self.file_count = ttk.Label(file_actions, text="0개 문서", style="Hint.TLabel")
                self.file_count.pack(side="right")

                # 설정 변수
                저장된_설정 = 설정_불러오기()
                저장된_세부작업 = 저장된_설정.get("stage_choices", {})
                if isinstance(저장된_세부작업, dict):
                    for mode, stages in self.stage_choices.items():
                        저장값 = 저장된_세부작업.get(mode, {})
                        if isinstance(저장값, dict):
                            self._세부작업_기본저장[mode] = True
                            for key in stages:
                                if isinstance(저장값.get(key), bool):
                                    stages[key] = 저장값[key]
                self.review_document_kind = 저장된_설정.get("review_document_kind", "보고서")
                self.review_reading_purpose = 저장된_설정.get("review_reading_purpose", "상세 설명용")
                self._활성_서식_프로파일 = str(저장된_설정.get("active_format_profile", ""))
                self._프로파일_콤보_이름목록 = ["profile_combo", "main_profile_combo"]
                self.prevent_word_split_var = tk.BooleanVar(value=bool(저장된_설정["prevent_word_split"]))
                self.ratio_shrink_var = tk.BooleanVar(value=bool(저장된_설정.get("ratio_shrink", 기본_설정["ratio_shrink"])))
                self.punctuation_var = tk.BooleanVar(value=bool(저장된_설정["punctuation"]))
                self.punctuation_threshold_var = tk.StringVar(value=str(저장된_설정["punctuation_threshold"]))
                self.keep_punctuation_set_var = tk.BooleanVar(value=bool(저장된_설정["keep_punctuation_set_together"]))
                self.color_mark_on_var = tk.BooleanVar(value=bool(저장된_설정["color_mark_on"]))
                self.color_var = tk.StringVar(value=str(저장된_설정["color"]))
                self.autoclose_var = tk.BooleanVar(value=bool(저장된_설정["autoclose"]))
                self.unify_result_window_var = tk.BooleanVar(value=bool(저장된_설정.get("unify_result_window", False)))
                서식통일_결과창_반영(self.unify_result_window_var.get())
                self.stdformat_var = tk.BooleanVar(value=bool(저장된_설정["stdformat"]))
                self.verify_var = tk.BooleanVar(value=bool(저장된_설정["verify"]))
                self.integrity_report_file_var = tk.BooleanVar(
                    value=bool(저장된_설정.get("integrity_report_file", False)))
                self.final_review_file_var = tk.BooleanVar(
                    value=bool(저장된_설정.get("final_review_file", False)))
                self.two_pass_var = tk.BooleanVar(value=bool(저장된_설정.get("two_pass_processing", False)))
                self.table_spacing_var = tk.BooleanVar(value=bool(저장된_설정.get("table_spacing", True)))
                self.log_file_var = tk.BooleanVar(value=bool(저장된_설정.get("log_file", False)))
                self.check_updates_on_start_var = tk.BooleanVar(
                    value=bool(저장된_설정.get("check_updates_on_start", True))
                )
                self.developer_mode_var = tk.BooleanVar(value=bool(저장된_설정.get("developer_mode", False)))
                # 켜고 끄면 문서 도구 메뉴를 바로 보이거나 숨긴다.
                self.developer_mode_var.trace_add(
                    "write", lambda *_: hasattr(self, "tools_button") and self._반응형_배치())
                # 작업 범위는 작업마다 정하는 값이라 저장하지 않고, 실행할 때마다 '문서 전체'로 시작한다.
                # 쪽 표시: 숫자 문자열 또는 '마지막쪽'(내부값 0). 종료쪽 기본값은 시작쪽이다.
                self.range_mode_var = tk.StringVar(value="all")
                self.range_start_var = tk.StringVar(value="1")
                self.range_end_var = tk.StringVar(value="1")
                self._범위_동기중 = False          # 프로그램이 값을 바꾸는 중(사용자 변경과 구분)
                self._범위_끝직접설정 = False      # 사용자가 종료쪽을 직접 바꿨는지
                self.retry_body_var = tk.StringVar(value=str(저장된_설정["retry_body"]))
                self.retry_table_var = tk.StringVar(value=str(저장된_설정["retry_table"]))
                self.linespacing_min_var = tk.StringVar(value=str(저장된_설정["linespacing_min"]))
                self.linespacing_max_var = tk.StringVar(value=str(저장된_설정["linespacing_max"]))
                self.font_folder_var = tk.StringVar(value=str(저장된_설정.get("hwp_font_folder", "")))
                self.paste_add_folder_var = tk.StringVar(value=str(저장된_설정.get("paste_add_folder", "")))
                저장된_기호글꼴 = 저장된_설정.get("symbol_fonts", {})
                self.symbol_font_vars = {}
                for 기호 in 문장기호_목록:
                    항목 = {**기본_설정["symbol_fonts"].get(기호, {}), **저장된_기호글꼴.get(기호, {})}
                    self.symbol_font_vars[기호] = {
                        "font": tk.StringVar(value=str(항목.get("font", ""))),
                        "size": tk.StringVar(value=str(항목.get("size", ""))),
                    }
                저장된_표글꼴 = 저장된_설정.get("table_fonts") or {}
                self.table_font_vars = {}
                for part in ("header", "body"):
                    항목 = {**기본_설정["table_fonts"][part], **(저장된_표글꼴.get(part) or {})}
                    self.table_font_vars[part] = {
                        "font": tk.StringVar(value=str(항목.get("font", ""))),
                        "size": tk.StringVar(value=str(항목.get("size", ""))),
                    }
                if not self.font_folder_var.get():
                    self.font_folder_var.set(한글_폰트_폴더_자동감지())
                self._한글_폰트_목록_캐시 = 한글_폰트_목록_전체(self.font_folder_var.get())
                기호글꼴_적용(저장된_설정)
                self.paren_shrink_var = tk.BooleanVar(value=bool(저장된_설정["paren_shrink"]))
                self.paren_label_bold_var = tk.BooleanVar(value=bool(저장된_설정["paren_label_bold"]))
                label_keys = ['□', 'ㅁ', 'ㅇ', '○', '-', '※', '*', '**'] + sorted(공문서_기호 - set('□ㅁㅇ○-※')) + ['기타']
                self.label_symbol_vars = {key: tk.BooleanVar(value=bool(저장된_설정['label_symbols'].get(key, True))) for key in label_keys}
                for var in self.label_symbol_vars.values():
                    var.trace_add('write', self._설정_변경됨)


                self.std_bool_keys = [
                    "std_margin", "std_ratio", "std_linespacing", "std_title", "std_title_bold", "std_title_auto", "std_attachment_auto", "std_midtitle_auto", "std_midtitle_bold",
                    "std_dateinfo", "std_dateinfo_bold", "std_symbols", "std_symbol_box_bold",
                    "std_symbol_o_bold", "std_symbol_dash_bold", "std_symbol_note_bold",
                    "std_marker_bold_consistency",
                    "std_remove_blank_lines",
                    "std_hanging_indent",
                    "std_supplement_indent",
                    "std_parspace", "std_table_header",
                ]
                self.std_bool_vars = {키: tk.BooleanVar(value=bool(저장된_설정[키])) for 키 in self.std_bool_keys}

                # 숫자 설정(문단 위 간격·복귀 배율·제목 부제 크기). 저장·기본값 초기화·서식 프로필 반영을 함께 쓴다.
                self.std_parspace_str_keys = ["std_parspace_chapter", "std_parspace_midtitle",
                                              "std_parspace_box", "std_parspace_circle", "std_parspace_dash",
                                              "std_parspace_note", "std_parspace_return_percent", "std_title_subtitle_pt"]
                self.std_parspace_vars = {키: tk.StringVar(value=str(저장된_설정[키])) for 키 in self.std_parspace_str_keys}
                # 부제 크기는 붙여넣은 글 변환(작업 실행 밖)에서도 쓰므로 바뀌는 즉시 전역값에 반영한다.
                제목_부제_크기_반영(저장된_설정["std_title_subtitle_pt"])
                self.std_parspace_vars["std_title_subtitle_pt"].trace_add(
                    "write", lambda *_: 제목_부제_크기_반영(self.std_parspace_vars["std_title_subtitle_pt"].get()))
                # 제목 표 담당자 칸(B2) 글: 사용자 고유 글이라 서식 프로필을 골라도 바꾸지 않는다. 바뀌면 바로 반영·저장한다.
                self.title_owner_var = tk.StringVar(value=str(저장된_설정.get("title_owner_text", "") or ""))
                제목_담당자_글_반영(self.title_owner_var.get())
                self.title_owner_var.trace_add("write", lambda *_: 제목_담당자_글_반영(self.title_owner_var.get()))
                self.title_owner_var.trace_add("write", self._설정_변경됨)

                for 변수 in ([self.prevent_word_split_var, self.ratio_shrink_var, self.punctuation_var, self.punctuation_threshold_var, self.keep_punctuation_set_var,
                             self.color_mark_on_var, self.color_var,
                             self.autoclose_var, self.unify_result_window_var,
                             self.stdformat_var, self.verify_var, self.integrity_report_file_var,
                             self.final_review_file_var, self.two_pass_var,
                             self.table_spacing_var, self.log_file_var, self.check_updates_on_start_var,
                             self.developer_mode_var,
                             self.retry_body_var, self.retry_table_var, self.paren_shrink_var,
                             self.linespacing_min_var, self.linespacing_max_var, self.font_folder_var,
                             self.paste_add_folder_var,
                             self.paren_label_bold_var] + list(self.std_bool_vars.values()) + list(self.std_parspace_vars.values())
                            + [v for 항목 in self.symbol_font_vars.values() for v in 항목.values()]
                            + [v for 항목 in self.table_font_vars.values() for v in 항목.values()]):
                    변수.trace_add("write", self._설정_변경됨)

                self.color_radios = []
                self.std_detail_checks = []
                self.std_parspace_spins = []
                self.settings_toplevel = None

                self.selected_mode = tk.StringVar(value="spacing")
                self.always_on_top_var = tk.BooleanVar(value=bool(저장된_설정.get("always_on_top", True)))
                # 카드는 세 장이다. '한 번에 적용'에서 자간 조정을 빼면 내부 작업 유형은 서식 적용(format)이다.
                self.include_spacing_var = tk.BooleanVar(value=bool(저장된_설정.get("all_include_spacing", True)))
                self.include_spacing_var.trace_add("write", self._설정_변경됨)
                # '한 번에 적용'의 '표 제외'. 켜면 표 관련 세부 작업을 모두 뺀다(설정 파일에 저장).
                self.exclude_tables_var = tk.BooleanVar(value=bool(저장된_설정.get("all_exclude_tables", False)))
                # '한 번에 적용'의 '페이지 맞춤 제외'와 '서식 통일' 카드의 표 제외·자간 정리 제외·페이지 맞춤 제외. 세부 작업과
                # 연동한다(_카드옵션_연동_시작).
                self.all_exclude_pagefit_var = tk.BooleanVar(value=bool(저장된_설정.get("all_exclude_pagefit", False)))
                self.unify_exclude_tables_var = tk.BooleanVar(value=bool(저장된_설정.get("unify_exclude_tables", False)))
                self.unify_exclude_spacing_var = tk.BooleanVar(value=bool(저장된_설정.get("unify_exclude_spacing", False)))
                self.unify_exclude_pagefit_var = tk.BooleanVar(value=bool(저장된_설정.get("unify_exclude_pagefit", True)))
                self.unify_keep_layout_var = tk.BooleanVar(value=bool(저장된_설정.get("unify_keep_layout", True)))
                self.unify_full_format_var = tk.BooleanVar(value=bool(저장된_설정.get("unify_full_format", False)))
                self.unify_quick_mode_var = tk.BooleanVar(value=not self.unify_full_format_var.get())
                def sync_full_format(*_):
                    target = not self.unify_quick_mode_var.get()
                    if self.unify_full_format_var.get() != target:
                        self.unify_full_format_var.set(target)
                def sync_quick_mode(*_):
                    target = not self.unify_full_format_var.get()
                    if self.unify_quick_mode_var.get() != target:
                        self.unify_quick_mode_var.set(target)
                self.unify_quick_mode_var.trace_add("write", sync_full_format)
                self.unify_full_format_var.trace_add("write", sync_quick_mode)
                for 변수 in (self.exclude_tables_var, self.all_exclude_pagefit_var, self.unify_exclude_tables_var,
                             self.unify_exclude_spacing_var, self.unify_exclude_pagefit_var, self.unify_keep_layout_var,
                             self.unify_full_format_var):
                    변수.trace_add("write", self._설정_변경됨)
                    변수.trace_add("write", self._요약갱신)
                # '자간 정리' 카드의 '기존 자간 초기화'. 세부 작업 01(문서 전체 자간 초기화)과 같은 값이며 설정 파일에 저장한다.
                저장된_초기화 = 저장된_설정.get("spacing_reset_existing")
                if isinstance(저장된_초기화, bool):
                    self.stage_choices["spacing"]["reset_spacing"] = 저장된_초기화
                self.reset_spacing_var = tk.BooleanVar(value=bool(self.stage_choices["spacing"]["reset_spacing"]))
                self.reset_spacing_var.trace_add("write", self._자간초기화_값변경)
                self.spacing_enabled_var = tk.BooleanVar(value=bool(저장된_설정.get("spacing_enabled", True)))
                self.spacing_page_fit_var = tk.BooleanVar(value=bool(저장된_설정.get("spacing_page_fit", False)))
                self.instant_run_on_drop_var = tk.BooleanVar(value=bool(저장된_설정.get("instant_run_on_drop", True)))
                self.auto_open_result_var = tk.BooleanVar(value=bool(저장된_설정.get("auto_open_result", True)))
                for 변수 in (self.spacing_enabled_var, self.spacing_page_fit_var,
                             self.instant_run_on_drop_var, self.auto_open_result_var):
                    변수.trace_add("write", self._설정_변경됨)
                    변수.trace_add("write", self._요약갱신)
                # '자간 정리' 카드의 '표 제외'는 설정 table_spacing(표 안 문장 자간조정)의 반대 값이다. 바꾸면 카드 요약
                # 문구도 고친다(저장은 설정 변경 감시가 한다).
                self.table_spacing_var.trace_add("write", self._요약갱신)
                self.card_mode_var = tk.StringVar(value="spacing")   # 카드 표시용(format도 '한 번에 적용' 카드)
                choose = ttk.LabelFrame(main, text="처리 방식", padding=card_padding, style="Card.TLabelframe")
                choose.grid(row=1, column=0, sticky="ew", pady=6)
                self.choose_frame = choose
                self.mode_buttons = []
                self.mode_cards = {}
                self.card_option_checks = {}   # 카드별 옵션 체크(선택한 카드 배경색을 같이 바꾼다)
                for i, (title, mode, desc) in enumerate((
                    ("자간 정리", "spacing", "줄 끝의 끊긴 단어와 자간을 정리합니다."),
                    ("서식 통일", "unify", "문서에서 많이 쓰인 서식으로 맞춥니다."),
                    ("한 번에 적용", "all", "공문서 서식을 입히고 자간까지 정리합니다."))):
                    choose.grid_columnconfigure(i, weight=1, uniform="modes")
                    card = tk.Frame(choose, bg=UI_COLORS["separator"], padx=1, pady=1, cursor="hand2")
                    card.grid(row=1, column=i, sticky="nsew", padx=max(2, round(4 * self._ui_scale)))
                    inner = tk.Frame(card, bg=UI_COLORS["surface"], padx=max(7, round(12 * self._ui_scale)),
                                     pady=max(6, round(10 * self._ui_scale)), cursor="hand2")
                    inner.pack(fill="both", expand=True)
                    rb = ttk.Radiobutton(inner, text=title, value=mode, variable=self.card_mode_var,
                                         command=lambda m=mode: self._카드_클릭(m), style="Mode.TRadiobutton")
                    rb.pack(anchor="w")
                    description = tk.Label(inner, text=desc.replace("\n", " "), bg=UI_COLORS["surface"],
                                           fg=UI_COLORS["muted"], justify="left", anchor="w",
                                           wraplength=max(100, round(160 * self._ui_scale)),
                                           font=("맑은 고딕", 9), cursor="hand2")
                    description.pack(anchor="w", fill="x", pady=(5, 8))
                    self.mode_buttons.append(rb)

                    def 카드_체크(text, variable, command, m=mode, inner=inner, **옵션):
                        check = tk.Checkbutton(
                            inner, text=text, variable=variable, command=command, bg=UI_COLORS["surface"],
                            activebackground=UI_COLORS["surface"], fg=UI_COLORS["ink"], font=("맑은 고딕", 9),
                            anchor="w", cursor="hand2", **옵션)
                        check.pack(anchor="w", pady=(0, 4))
                        self.mode_buttons.append(check)
                        self.card_option_checks.setdefault(m, []).append(check)
                        return check
                    if mode == "spacing":
                        카드_체크("자간 정리", self.spacing_enabled_var, lambda: self._카드옵션_변경("spacing"))
                        카드_체크("페이지 맞춤", self.spacing_page_fit_var, lambda: self._카드옵션_변경("spacing"))
                        # 끄면 문서에 이미 있는 자간을 0%로 되돌리지 않고 그 위에서 정리한다.
                        self.reset_spacing_check = tk.Checkbutton(
                            inner, text="기존 자간 초기화", variable=self.reset_spacing_var,
                            command=self._자간초기화_변경, bg=UI_COLORS["surface"], activebackground=UI_COLORS["surface"],
                            fg=UI_COLORS["ink"], font=("맑은 고딕", 9), anchor="w", cursor="hand2")
                        self.reset_spacing_check.pack(anchor="w", pady=(0, 4))
                        self.mode_buttons.append(self.reset_spacing_check)
                        self.card_option_checks.setdefault(mode, []).append(self.reset_spacing_check)
                        # '표 제외'(기본 꺼짐): 켜면 표 칸 안 문장은 자간 초기화·자간 조정·줄 병합·단어 검사 대상에서 뺀다.
                        # 설정 table_spacing(설정창 '표 서식 내 문장도 자간조정하기')의 반대 값이라 켜면 False를 넣는다
                        # (2026-10-04 사용자 요청: '표 내 자간 정리'를 '표 제외'로 바꿈).
                        self.table_spacing_card_check = 카드_체크(
                            "표 제외", self.table_spacing_var, self._자간초기화_변경, onvalue=False, offvalue=True)
                    if mode == "unify":
                        # 켜면 기본 표 서식·표 서식통일을 뺀다.
                        self.unify_exclude_tables_check = 카드_체크(
                            "표 제외", self.unify_exclude_tables_var, lambda: self._카드옵션_변경("unify"))
                        # 켜면 서식통일이 고친 문장의 자간 조정·외톨이 글자 당기기를 뺀다(내어쓰기는 맞춘다).
                        self.unify_exclude_spacing_check = 카드_체크(
                            "자간 정리 제외", self.unify_exclude_spacing_var, lambda: self._카드옵션_변경("unify"))
                        # 켜면 문단 아래 간격 페이지 맞춤·관련 문단 페이지 배치를 뺀다.
                        self.unify_exclude_pagefit_check = 카드_체크(
                            "페이지 맞춤 제외", self.unify_exclude_pagefit_var, lambda: self._카드옵션_변경("unify"))
                        # 켜면 결과의 쪽 구성(보고서별 쪽 수·시작 쪽, 전체 쪽 수)을 원본과 같게 맞춘다.
                        self.unify_keep_layout_check = 카드_체크(
                            "원본 쪽 구성 유지", self.unify_keep_layout_var, lambda: self._카드옵션_변경("unify"))
                        # 끄면(기본) 글꼴·크기만, 켜면 글자색·정렬·여백·위 간격·내어쓰기까지 전체 서식을 맞춘다.
                        self.unify_full_format_check = 카드_체크(
                            "퀵모드 (글꼴 종류·크기만)", self.unify_quick_mode_var, lambda: self._카드옵션_변경("unify"))
                    if mode == "all":
                        # 끄면 기존 자간을 그대로 두고 서식만 입힌다(결과 파일 이름은 '서식적용').
                        self.include_spacing_check = tk.Checkbutton(
                            inner, text="자간 조정 포함", variable=self.include_spacing_var,
                            command=self._자간포함_변경, bg=UI_COLORS["surface"], activebackground=UI_COLORS["surface"],
                            fg=UI_COLORS["ink"], font=("맑은 고딕", 9), anchor="w", cursor="hand2")
                        self.include_spacing_check.pack(anchor="w", pady=(0, 4))
                        self.mode_buttons.append(self.include_spacing_check)
                        self.card_option_checks.setdefault(mode, []).append(self.include_spacing_check)
                        # 켜면 표 관련 작업(텍스트 표 변환·기본 표 서식·표 칸 너비·표 정밀 서식·표 머리글 서식·
                        # 표 안 자간·줄·단어 작업)을 모두 빼고 실행한다. 제목·개요 서식 표는 그대로 정리한다.
                        self.exclude_tables_check = 카드_체크("표 제외", self.exclude_tables_var, self._표제외_변경)
                        # 켜면 문단 아래 간격 페이지 맞춤·관련 문단 페이지 배치를 뺀다.
                        self.all_exclude_pagefit_check = 카드_체크(
                            "페이지 맞춤 제외", self.all_exclude_pagefit_var, self._표제외_변경)
                    self.mode_cards[mode] = (card, inner, description)
                    for surface in (card, inner, description):
                        surface.bind("<Button-1>", lambda e, m=mode: self._카드_클릭(m))
                quick = ttk.Frame(choose)
                self.quick_actions = quick
                quick.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(max(3, round(5 * self._ui_scale)), 0))
                self.settings_button = ttk.Button(quick, text="설정", command=self.설정창_열기)
                self.settings_button.pack(side="right")
                self.stage_details_button = ttk.Button(
                    quick, text="작업 항목", command=lambda: self._세부작업_열기(self.selected_mode.get()))
                self.stage_details_button.pack(side="right", padx=(0, 6))
                self.tools_button = ttk.Menubutton(quick, text="도구 ▾")
                self.tools_menu = tk.Menu(self.tools_button, tearoff=False)
                for label, command in (("문서 구조 검토…", self._문서검토_열기),
                                       ("맞춤법 검토…", self._공공언어_검토),
                                       ("텍스트 붙여넣기 정리…", self._텍스트로_문서추가_열기),
                                       ("붙여넣은 문장 다듬기…", self._붙여넣기_정리_열기),
                                       ("아웃라이너로 작성…", self._아웃라이너_열기),
                                       ("작성 도우미…", self._작성도우미_열기),
                                       ("Markdown 내보내기…", self.Markdown_내보내기),
                                       ("고급 문서 도구…", self.고급문서도구_열기)):
                    self.tools_menu.add_command(label=label, command=command)
                self.tools_button["menu"] = self.tools_menu
                self.tools_button.pack(side="right", padx=(0, 6))
                self._보조_도구들 = [self.tools_button]
                self.document_review_button = ttk.Button(quick, text="문서 구조 검토", command=self._문서검토_열기)
                self.proofread_button = ttk.Button(quick, text="맞춤법 검토", command=self._공공언어_검토)
                self.options_summary = ttk.Label(quick, style="Hint.TLabel", wraplength=540, justify="left")
                self.options_summary.pack(side="left")

                # 실행창에서 바로 사용할 서식 선택과 예시 문서 드롭 분석.
                format_quick = ttk.Frame(choose)
                self.format_quick = format_quick
                format_quick.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(max(4, round(6 * self._ui_scale)), 0))
                ttk.Label(format_quick, text="적용 서식", font=("맑은 고딕", 9, "bold")).pack(side="left", padx=(0, 6))
                self.main_profile_combo = ttk.Combobox(format_quick, state="readonly", width=20)
                self.main_profile_combo.pack(side="left")
                self.main_profile_combo.bind("<<ComboboxSelected>>", self._프로파일_선택)
                # 고른 서식을 예시 보고서에 입혀 한/글로 미리 보여 준다(2026-10-04 사용자 요청).
                self.format_example_button = ttk.Button(format_quick, text="서식 예시 확인", command=self._서식예시_확인)
                self.format_example_button.pack(side="left", padx=(6, 0))
                if 알파_서식예시폴더_사용:
                    # 키오스크에서 메뉴 사진을 보고 고르듯, 서식 예시의 첫 쪽 그림(스틸컷)을 보며 고른다(알파, 2026-10-10).
                    self.format_kiosk_button = ttk.Button(format_quick, text="썸네일로 선택", command=self._서식_키오스크_열기)
                    self.format_kiosk_button.pack(side="left", padx=(4, 0))
                    # 서식예시 폴더(C:\\HWP_AUTODOCFIT\\서식예시)를 열어 예시 파일을 직접 고친다(알파, 2026-10-10).
                    self.format_samples_button = ttk.Button(format_quick, text="서식예시 폴더", command=self._서식예시_폴더_열기)
                    self.format_samples_button.pack(side="left", padx=(4, 0))
                self.format_drop_label = ttk.Label(
                    format_quick,
                    text="예시 HWP/HWPX를 여기에 놓으면 분석 후 바로 선택합니다",
                    style="Drop.TLabel",
                    padding=(8, 4),
                    anchor="center",
                )
                self.format_drop_label.pack(side="left", fill="x", expand=True, padx=(8, 0))
                self.format_drop_label.drop_target_register(DND_FILES)
                self.format_drop_label.dnd_bind("<<Drop>>", self.서식파일_드롭)

                # 작업 범위: 기본은 문서 전체. 쪽을 지정하면 그 쪽에 놓인 내용만 처리한다.
                scope = ttk.Frame(choose)
                self.scope_frame = scope
                scope.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(max(4, round(6 * self._ui_scale)), 0))
                self.range_all_radio = ttk.Radiobutton(scope, text="문서 전체", value="all", variable=self.range_mode_var)
                self.range_pages_radio = ttk.Radiobutton(scope, text="쪽 지정", value="pages", variable=self.range_mode_var)
                self.page_range_var = tk.BooleanVar(value=False)
                self.page_range_toggle = ttk.Checkbutton(
                    scope, text="특정 쪽만 정리", variable=self.page_range_var, command=self._쪽범위_토글)
                self.page_range_toggle.pack(side="left")
                self.page_range_details = ttk.Frame(scope)
                ttk.Label(self.page_range_details, text="시작").pack(side="left", padx=(12, 4))
                self.range_start_spin = ttk.Spinbox(self.page_range_details, values=self._쪽_목록(), wrap=False, width=8, justify="center",
                                                    textvariable=self.range_start_var, state="disabled")
                self.range_start_spin.pack(side="left")
                ttk.Label(self.page_range_details, text="종료").pack(side="left", padx=(10, 4))
                self.range_end_spin = ttk.Spinbox(self.page_range_details, values=self._쪽_목록(1), wrap=False, width=8, justify="center",
                                                  textvariable=self.range_end_var, state="disabled")
                self.range_end_spin.pack(side="left")
                self.range_hint = ttk.Label(self.page_range_details, text="1의 아래는 ‘마지막쪽’", style="Hint.TLabel")
                self.range_hint.pack(side="left", padx=(8, 0))
                self.range_mode_var.trace_add("write", self._범위_상태_갱신)
                self.range_start_var.trace_add("write", self._범위_시작_변경)
                self.range_end_var.trace_add("write", self._범위_끝_변경)
                status_frame = ttk.LabelFrame(main, text="진행 상황", padding=card_padding, style="Card.TLabelframe")
                status_frame.grid(row=2, column=0, sticky="ew")
                self.status_var = tk.StringVar(value="")
                ttk.Label(status_frame, textvariable=self.status_var, wraplength=540, style="Status.TLabel").pack(anchor="w")
                self.STEP_IDLE_BG = UI_COLORS["rose"]
                self.STEP_ACTIVE_BG = UI_COLORS["teal"]
                self.STEP_IDLE_FG = UI_COLORS["ink"]
                self.STEP_ACTIVE_FG = "white"
                self.step_boxes = {}  # 이전 설정 코드와의 호환
                self._안내키, self._안내지남 = None, set()   # 진행 화면 단계 안내 상태
                # 맞춤 진행 화면(알파): 지금 문서 (순번, 전체), 실패한 원본 {경로: 이유}, 이번 작업의 실제 세부 작업
                self._진행문서, self._실패목록, self._진행_세부작업 = None, {}, None
                self._작업종료시각 = None
                self.stage_board = LiveStageBoard(status_frame)
                self.stage_board.pack(fill="x", pady=(2, 0))
                # '03 진행 상황' 바로 아래 결과 줄: 결과 버튼 두 개(작업 결과가 나오기 전에는 비활성)와,
                # 그 오른쪽 옆에 저장 안내 / '[작업 결과]' 문구를 둔다.
                self._결과목록 = []
                self._재개_대기중 = False    # 중단 버튼으로 멈춘 작업이 있어 실행 버튼으로 이어서 진행할 수 있는 상태
                self._재개_시작_인덱스 = 1
                self._재개_모드 = None
                self._작업시작시각 = None
                self._작업모드 = "all"
                self.result_bar = ttk.Frame(main, height=40)
                self.result_bar.grid(row=3, column=0, sticky="ew", pady=5)
                self.result_bar.pack_propagate(False)
                self.open_folder_button = ttk.Button(self.result_bar, text="원본 폴더 열기", command=self._원본폴더_열기, state="disabled")
                self.open_folder_button.pack(side="left")
                self.open_result_button = ttk.Button(self.result_bar, text="결과파일 열기", command=self._결과파일_열기, state="disabled")
                self.open_result_button.pack(side="left", padx=(8, 0))
                self.footer_note_var = tk.StringVar(value=self.FOOTER_NOTE_DEFAULT)
                self.footer_note = ttk.Label(self.result_bar, textvariable=self.footer_note_var, style="Hint.TLabel",
                                             wraplength=440, justify="left")
                self.footer_note.pack(side="left", padx=(12, 0))
                self.log_window = tk.Toplevel(root)
                self.log_window.title(f"처리 기록 · {APP_NAME}")
                self.log_window.geometry("780x360")
                self.log_window.minsize(500, 240)
                self.log_window.protocol("WM_DELETE_WINDOW", self._기록닫기)
                self.log_frame = ttk.LabelFrame(self.log_window, text="처리 기록 · 문제가 생기면 여기서 확인하세요", padding=10)
                self.log_frame.pack(fill="both", expand=True)
                self.log_frame.grid_columnconfigure(0, weight=1)
                self.log_frame.grid_rowconfigure(0, weight=1)
                log_scroll = ttk.Scrollbar(self.log_frame)
                log_scroll.grid(row=0, column=1, sticky="ns")
                self.log_text = tk.Text(self.log_frame, height=5, font=("맑은 고딕", 9), wrap="word",
                    bg="white", fg=UI_COLORS["ink"], relief="flat", yscrollcommand=log_scroll.set)
                self.log_text.grid(row=0, column=0, sticky="nsew")
                log_scroll.config(command=self.log_text.yview)
                self.log_text.bind("<Key>", self._로그_키입력_차단)
                self.log_window.withdraw()
                self._log_visible = False
                footer = ttk.Frame(root, padding=(12, 4, 12, 6))
                footer.grid(row=2, column=0, sticky="ew")
                footer.grid_columnconfigure(0, weight=1)
                # 창 닫기는 운영체제 제목 표시줄에 맡기고, 하단에는 작업 동작만 둔다.
                right = ttk.Frame(footer)
                right.grid(row=0, column=1, sticky="e")
                for col in range(2):
                    right.grid_columnconfigure(col, uniform="footer_btn")
                # 중단은 보조 동작, 문서 정리는 화면의 단일 주요 동작이다.
                def 버튼_칸(열):
                    칸 = tk.Frame(right, bg=UI_COLORS["bg"], padx=2, pady=2)
                    칸.grid(row=0, column=열, sticky="ew", padx=1)
                    return 칸
                self.stop_button = ttk.Button(버튼_칸(0), text="중단", width=10, command=self.작업중단, state="disabled")
                self.stop_button.pack(fill="x")
                self.start_wrap = 버튼_칸(1)
                self.start_button = ttk.Button(self.start_wrap, text="정리 시작", width=14, style="Start.TButton",
                    command=lambda: self.작업시작(self.selected_mode.get()), state="disabled")
                self.start_button.pack(fill="x")
                self.run_buttons = [self.start_button]
                self.selected_mode.trace_add("write", self._요약갱신)
                self.selected_mode.trace_add("write", self._모드카드_외관갱신)
                self.always_on_top_var.trace_add("write", self._항상위_변경)
                for var in (self.stdformat_var, *self.std_bool_vars.values()):
                    var.trace_add("write", self._요약갱신)
                self._카드옵션_연동_시작()
                self._요약갱신()
                self._모드카드_외관갱신()
                self._안내_설정(1)     # 처음에는 '01 정리할 문서'부터 안내한다.

                file_frame.drop_target_register(DND_FILES)
                file_frame.dnd_bind("<<Drop>>", self.파일_드롭)

                self._프로파일들 = 서식프로파일_목록()
                if self._활성_서식_프로파일 not in self._프로파일들:
                    self._활성_서식_프로파일 = ""
                self._프로파일_전역반영(self._프로파일들[self._활성_서식_프로파일])
                self._서식예시_폴더_준비()
                try:
                    상용구_폴더_준비()
                except Exception as exc:
                    self.로그표시(f"상용구 폴더를 준비하지 못했습니다: {exc}")
                self._설정창_생성()
                self._항상위_적용()

                self._queue_after_id = root.after(100, self.queue_처리)
                root.bind("<Destroy>", self._루트_파괴시_예약취소, add="+")
                root.bind("<Control-o>", lambda e: self.파일선택())
                root.bind("<Configure>", self._메인_크기조정, add="+")
                root.protocol("WM_DELETE_WINDOW", self.종료)
                root.after_idle(self._창_최소높이_보정)
                if getattr(sys, "frozen", False):
                    업데이트_시작신호()
                    # 지난 업데이트가 남긴 구버전 백업과 내려받기 잔여물을 정리한다(교체가 끝난 다음 실행에서).
                    threading.Thread(target=업데이트_잔여정리, daemon=True, name="update-cleanup").start()
                if getattr(sys, "frozen", False) and self.check_updates_on_start_var.get():
                    root.after(1500, self._자동업데이트_확인_시작)


            def _자동업데이트_확인_시작(self, 수동=False):
                from docfit_core.network_policy import offline_mode
                if offline_mode():
                    # 폐쇄망 모드: 외부 서버에 접속하지 않는다. 새 버전은 담당자가 전달한 실행 파일로 바꾼다.
                    if 수동:
                        self._알림(messagebox.showinfo, APP_NAME,
                                   "폐쇄망 모드에서는 인터넷으로 업데이트를 확인하지 않습니다.\n\n"
                                   "새 버전은 담당자가 전달한 실행 파일로 바꿔 주세요. 인터넷이 되는 PC라면 "
                                   "설정에서 '폐쇄망 모드'를 끄면 업데이트를 확인할 수 있습니다.",
                                   parent=self.settings_toplevel or self.root)
                        self.status_var.set("폐쇄망 모드: 업데이트 확인을 하지 않았어요.")
                    return
                if 수동:
                    버튼 = getattr(self, "update_button", None)
                    if 버튼 is not None:
                        버튼.config(state="disabled")
                    self.status_var.set("새 업데이트가 있는지 확인하고 있어요…")

                def 결과_표시(릴리스=None, 오류=None):
                    버튼 = getattr(self, "update_button", None)
                    if 버튼 is not None and not self.running:
                        버튼.config(state="normal")
                    if 오류 is not None:
                        if 수동:
                            self._알림(messagebox.showerror,
                                APP_NAME,
                                f"업데이트 정보를 확인하지 못했습니다.\n\n{오류}",
                                parent=self.settings_toplevel or self.root,
                            )
                            self.status_var.set("업데이트 확인에 실패했어요.")
                        return
                    최신버전 = str((릴리스 or {}).get("tag_name") or (릴리스 or {}).get("name") or APP_VERSION)
                    if not 릴리스 or _버전_튜플(최신버전) <= _버전_튜플(APP_VERSION):
                        if 수동:
                            self._알림(messagebox.showinfo,
                                APP_NAME,
                                "현재 최신버전입니다.",
                                parent=self.settings_toplevel or self.root,
                            )
                            self.status_var.set("현재 최신버전입니다.")
                        return
                    self._자동업데이트_안내(릴리스)

                def 확인():
                    try:
                        릴리스 = _최신_릴리스_통합_조회()
                    except Exception as exc:
                        # 네트워크가 없거나 GitLab이 응답하지 않아도 앱 사용은 막지 않는다.
                        if 수동:
                            try:
                                self.root.after(0, lambda 오류=str(exc): 결과_표시(오류=오류))
                            except Exception:
                                pass
                        return
                    try:
                        self.root.after(0, lambda: 결과_표시(릴리스=릴리스))
                    except Exception:
                        pass

                threading.Thread(target=확인, daemon=True, name="release-update-check").start()

            def _자동업데이트_안내(self, 릴리스):
                if self.closing or self.running:
                    return
                자산 = _업데이트_자산_선택(릴리스)
                버전 = str(릴리스.get("tag_name") or 릴리스.get("name") or "새 버전")
                if not 자산 or not 자산.get("browser_download_url"):
                    self._알림(messagebox.showinfo,
                        APP_NAME,
                        f"{버전} 정식 버전이 출시되었지만 Windows EXE 파일이 없습니다.\n"
                        f"Release에 {UPDATE_ASSET_NAME}를 첨부해 주세요.",
                        parent=self.root,
                    )
                    return
                if not self._알림(messagebox.askyesno,
                    APP_NAME,
                    f"새 정식 버전 {버전}이 출시되었습니다.\n\n"
                    "지금 다운로드하고 앱을 자동으로 업데이트할까요?",
                    parent=self.root,
                ):
                    return
                self.status_var.set(f"{버전} 업데이트를 다운로드하고 있어요…")
                threading.Thread(
                    target=self._자동업데이트_다운로드,
                    args=(릴리스, 자산),
                    daemon=True,
                    name="release-update-download",
                ).start()

            def _자동업데이트_다운로드(self, 릴리스, 자산):
                """'.part'로 받고 크기·EXE 머리·SHA-256(자산 digest 또는 릴리스 노트)을 확인한 뒤 확정한다."""
                임시 = None
                try:
                    업데이트_폴더 = 설정_폴더() / "updates"
                    업데이트_폴더.mkdir(parents=True, exist_ok=True)
                    버전 = re.sub(r"[^0-9A-Za-z._-]+", "_", str(릴리스.get("tag_name", "latest")))
                    다운로드_경로 = 업데이트_폴더 / f"HWP_AutoDocFit-{버전}.exe"
                    임시 = 다운로드_경로.with_name(다운로드_경로.name + ".part")
                    다운로드_URL = _업데이트_URL_검증(자산["browser_download_url"])
                    예상해시 = 업데이트_예상해시(릴리스, 자산)
                    해시 = hashlib.sha256()
                    크기 = 0
                    머리 = b""
                    응답 = _업데이트_HTTP_GET(다운로드_URL,
                                            {"User-Agent": f"HWP-AutoDocFit/{APP_VERSION}"}, 30)
                    try:
                        with open(임시, "wb") as 출력:
                            while True:
                                조각 = 응답.read(1024 * 1024)
                                if not 조각:
                                    break
                                if len(머리) < 2:
                                    머리 += 조각[:2]
                                출력.write(조각)
                                해시.update(조각)
                                크기 += len(조각)
                    finally:
                        응답._docfit_connection.close()
                    문제 = 업데이트_파일검증(크기, 머리, 해시.hexdigest(), int(자산.get("size") or 0) or None, 예상해시)
                    if 문제:
                        raise RuntimeError(문제)
                    os.replace(임시, 다운로드_경로)
                    임시 = None
                    _업데이트_기록(f"내려받기 완료: {다운로드_경로.name} {크기:,}바이트, SHA-256 확인")
                    self.root.after(0, lambda: self._자동업데이트_설치(다운로드_경로, 예상해시))
                except Exception as exc:
                    _업데이트_기록(f"내려받기 실패: {exc}")
                    try:
                        self.root.after(0, lambda 오류=str(exc): self._알림(messagebox.showerror,
                            APP_NAME, f"자동 업데이트를 다운로드하지 못했습니다.\n\n{오류}", parent=self.root
                        ))
                    except Exception:
                        pass
                finally:
                    if 임시 is not None:
                        try:
                            Path(임시).unlink()
                        except OSError:
                            pass

            def _자동업데이트_설치(self, 다운로드_경로, 예상해시=None):
                """구버전을 '.old'로 바꾸고 신버전을 원래 이름으로 넣는 교체 스크립트를 띄운 뒤 앱을 끝낸다.

                PyInstaller 단일 EXE는 부트로더(부모)와 Python(자식) 두 프로세스로 돈다. 예전에는 자식만 기다려 부모가 EXE를
                잡고 있는 동안 복사가 실패했고, 그러면 내려받은 파일을 그 자리에서 실행해 구버전이 남았다(2026-10-09).
                """
                현재_실행파일 = Path(sys.executable).resolve()
                폴더 = 현재_실행파일.parent
                try:
                    시험 = 폴더 / f".docfit_update_test_{os.getpid()}"
                    시험.write_bytes(b"")
                    시험.unlink()
                except OSError:
                    _업데이트_기록(f"설치 폴더에 쓸 수 없음: {폴더}")
                    self._알림(messagebox.showwarning,
                        APP_NAME,
                        f"설치 폴더에 쓸 권한이 없어 자동으로 바꿀 수 없습니다.\n{폴더}\n\n"
                        f"내려받은 새 버전으로 직접 바꿔 주세요:\n{다운로드_경로}",
                        parent=self.root,
                    )
                    try:
                        os.startfile(str(다운로드_경로.parent))
                    except Exception:
                        pass
                    return
                스크립트 = 다운로드_경로.with_suffix(".ps1")
                스크립트.write_text(업데이트_교체스크립트(), encoding="utf-8-sig")
                기다릴 = [os.getpid()]
                try:
                    부모 = os.getppid()
                    if 부모 and 부모 != os.getpid():
                        기다릴.append(부모)
                except Exception:
                    pass
                try:
                    subprocess.Popen(
                        [
                            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                            "-File", str(스크립트), "-WaitPidList", " ".join(str(x) for x in 기다릴),
                            "-Downloaded", str(다운로드_경로), "-Target", str(현재_실행파일),
                            "-Log", str(다운로드_경로.parent / "update.log"), "-Sha256", str(예상해시 or ""),
                            "-StartedFlag", str(다운로드_경로.parent / UPDATE_STARTED_FLAG),
                            "-BusyFlag", str(다운로드_경로.parent / UPDATE_BUSY_FLAG),
                        ],
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                        env=업데이트_실행환경(os.environ),
                    )
                except Exception:
                    try:
                        스크립트.unlink()
                    except OSError:
                        pass
                    raise
                _업데이트_기록(f"교체 스크립트 시작: {현재_실행파일.name} ← {다운로드_경로.name}")
                self.closing = True
                self.root.destroy()

            def _항상위_적용(self):
                """실행창(및 함께 쓰는 처리 기록·설정 창)을 항상 위에 둘지 반영한다."""
                try:
                    켜짐 = bool(self.always_on_top_var.get())
                except Exception:
                    켜짐 = True
                for 창 in (self.root, getattr(self, "log_window", None), getattr(self, "settings_toplevel", None)):
                    try:
                        if 창 is not None and 창.winfo_exists():
                            창.attributes("-topmost", 켜짐)
                    except Exception:
                        pass

            def _항상위_변경(self, *args):
                self._항상위_적용()
                self._설정_변경됨()

            def _창_최소높이_보정(self):
                """화면 해상도와 Windows 논리 배율을 반영한 최소 창 크기를 적용한다."""
                self.root.update_idletasks()
                screen_width, screen_height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                scale = getattr(self, "_ui_scale", 1.0)
                min_width = min(max(self._minimum_width, round(520 * scale)), screen_width - 24)
                min_height = min(max(self._minimum_height, round(480 * scale)), screen_height - 48)
                if not getattr(self.root, "_docfit_hidden_backend", False):
                    self.root.minsize(max(420, min_width), max(400, min_height))
                self._반응형_배치()

            def _테마_적용(self):
                c = UI_COLORS
                self.root.configure(bg=c["bg"])
                self.root.option_add("*Font", ("맑은 고딕", 10))
                style = ttk.Style()
                try:
                    style.theme_use("clam")
                except tk.TclError:
                    pass
                style.configure(".", background=c["bg"], foreground=c["ink"], font=("맑은 고딕", 10))
                style.configure("Header.TFrame", background=c["surface"])
                style.configure("Main.TFrame", background=c["bg"])
                style.configure("AppTitle.TLabel", background=c["surface"], foreground=c["ink"], font=("맑은 고딕", 20, "bold"))
                style.configure("HeaderHint.TLabel", background=c["surface"], foreground=c["muted"], font=("맑은 고딕", 10))
                style.configure("HeaderStatus.TLabel", background=c["teal_tint"], foreground=c["teal_dark"], padding=(11, 5), font=("맑은 고딕", 9, "bold"))
                style.configure("TButton", padding=(10, 5), borderwidth=0, background=c["surface"])
                style.map("TButton", background=[("active", c["teal_tint"]), ("disabled", c["bg"])], foreground=[("disabled", "#8E8E93")])
                style.configure("Start.TButton", background=c["teal"], foreground="white", padding=(14, 6), font=("맑은 고딕", 10, "bold"))
                style.map("Start.TButton", background=[("disabled", c["separator"]), ("active", c["teal_dark"])], foreground=[("disabled", c["muted"])])
                style.configure("TLabelframe", background=c["surface"], bordercolor=c["separator"], relief="solid")
                style.configure("Card.TLabelframe", background=c["surface"], bordercolor=c["separator"], relief="solid")
                # 다음 행동만 파란 테두리로 보인다. 색만으로 오류·우선순위를 전달하지 않는다.
                style.configure("Guide.TLabelframe", background=c["surface"], bordercolor=c["teal"], relief="solid")
                style.configure("TLabelframe.Label", background=c["surface"], foreground=c["ink"], font=("맑은 고딕", 11, "bold"))
                style.configure("Section.TLabel", background=c["surface"], foreground=c["ink"], font=("맑은 고딕", 9, "bold"))
                style.configure("Hint.TLabel", background=c["surface"], foreground=c["muted"], font=("맑은 고딕", 9))
                style.configure("Status.TLabel", background=c["surface"], foreground=c["teal_dark"])
                style.configure("Result.TLabel", background=c["surface"], foreground=c["success"], font=("맑은 고딕", 9, "bold"))
                style.configure("Drop.TLabel", background=c["teal_tint"], foreground=c["ink"])
                style.configure("Mode.TRadiobutton", background=c["surface"], font=("맑은 고딕", 10, "bold"))
                style.configure("Stage.TCheckbutton", font=("맑은 고딕", 10, "bold"))
                style.configure("TNotebook", borderwidth=0)
                style.configure("TNotebook.Tab", padding=(12, 9), background=c["rose"])
                style.map("TNotebook.Tab", background=[("selected", c["lavender"]), ("active", "#E5E1F4")], foreground=[("selected", c["ink"])])
                style.map("TCheckbutton", indicatorbackground=[("selected", c["teal"]), ("disabled", c["rose"])])

            def _자간정리_항목_상세(self, parent, key, *, 주설정탭):
                """'자간 정리' 세부 설정 탭과 세부 작업 창이 함께 쓰는 항목별 상세 위젯.

                같은 변수(self.xxx_var)에 새 위젯을 만들어 값은 항상 공유한다.
                주설정탭=True(세부 설정 탭)일 때만 작업 중 비활성화 등에 쓰이는
                단일 속성(self.prevent_word_split_check 등)에 연결한다.
                """
                if key == "reset_spacing":
                    # 이 단계 자체가 곧 "자간 초기화 여부"라서 위 번호 체크박스 하나로
                    # 충분하다(설명은 그 체크박스 옆 "예:" 문구로 이미 나옴). 별도 on/off를
                    # 더 두면 같은 뜻의 체크박스가 중복된다.
                    pass
                elif key == "body_spacing":
                    체크 = ttk.Checkbutton(parent, text="줄 끝에서 단어가 끊기지 않게 정리하기", variable=self.prevent_word_split_var)
                    체크.pack(anchor="w")
                    ttk.Label(parent, text="04. 표·컨트롤 자간 조정에도 함께 적용됩니다.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(0, 2))
                    ttk.Checkbutton(parent, text="장평 줄이기 사용(글자 가로 비율을 줄여 단어를 한 줄에 모음)",
                                    variable=self.ratio_shrink_var).pack(anchor="w")
                    ttk.Label(parent, text="기본은 끔: 자간 줄이기·늘리기만으로 맞춥니다. 켜면 자간으로 부족할 때 장평을 90%까지 줄입니다.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(0, 2))
                    if 주설정탭:
                        self.prevent_word_split_check = 체크
                elif key == "short_line":
                    체크 = ttk.Checkbutton(parent, text="문장부호로 시작하는 문장의 짧은 줄 병합 사용", variable=self.punctuation_var)
                    체크.pack(anchor="w")
                    행 = ttk.Frame(parent)
                    행.pack(anchor="w", fill="x", pady=(2, 0))
                    ttk.Label(행, text="마지막 줄").pack(side="left")
                    스핀 = ttk.Spinbox(행, from_=1, to=20, width=3, textvariable=self.punctuation_threshold_var, justify="center")
                    스핀.pack(side="left", padx=(4, 4))
                    ttk.Label(행, text="자 이하일 때 합쳐요 (05. 표·컨트롤 줄 병합에도 함께 적용)").pack(side="left")
                    if 주설정탭:
                        self.punctuation_check = 체크
                        self.punctuation_threshold_spin = 스핀
                elif key == "control_spacing":
                    체크 = ttk.Checkbutton(parent, text="표 서식 내 문장도 자간조정하기", variable=self.table_spacing_var)
                    체크.pack(anchor="w")
                    ttk.Label(parent, text="끄면 표(셀) 안의 문장은 04·05단계에서 제외됩니다. 기본값은 켜짐입니다.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(0, 2))
                    if 주설정탭:
                        self.table_spacing_check = 체크

            def _준말_서비스(self):
                """Flutter·Tk가 같은 설정 파일과 UI 독립 준말 서비스를 사용한다."""
                from docfit_app.abbreviation_service import AbbreviationService
                from docfit_app.settings_service import SettingsService
                if not hasattr(self, "_준말서비스"):
                    self._준말서비스 = AbbreviationService(SettingsService(설정_파일_경로))
                return self._준말서비스

            def _서식정리_항목_상세(self, parent, key, *, 주설정탭):
                """'서식 정리'·'내어쓰기' 세부 설정 탭과 세부 작업 창이 함께 쓰는
                항목별 상세 위젯. _자간정리_항목_상세와 동일한 방식으로 동작한다.
                """
                def 준말창_열기():
                    from docfit_core.abbreviation_dialog import open_abbreviation_dialog

                    서비스 = self._준말_서비스()
                    open_abbreviation_dialog(
                        parent.winfo_toplevel(), 서비스.user_entries,
                        lambda 등록표: 서비스.replace_entries(등록표, running=self.running),
                        서비스.defaults_enabled,
                        lambda 사용: 서비스.set_defaults(사용, running=self.running))
                if key == "pre_format":
                    title_auto = ttk.Checkbutton(parent, text="제목 모양 자동 정리 · 제목표가 있을 때",
                                                  variable=self.std_bool_vars["std_title_auto"])
                    title_auto.pack(anchor="w")
                    ttk.Label(parent, text="문서 앞부분의 제목과 개요를 인식해 알맞은 모양을 적용합니다. 제목표가 없으면 건너뜁니다.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w")
                    부제_행 = ttk.Frame(parent)
                    부제_행.pack(anchor="w", padx=(18, 0), pady=(2, 0))
                    ttk.Label(부제_행, text="제목 부제 크기 (제목 글의 첫 쉼표 앞 글):").pack(side="left")
                    부제_스핀 = ttk.Spinbox(부제_행, from_=5, to=40, increment=1, width=4, justify="center",
                                           textvariable=self.std_parspace_vars["std_title_subtitle_pt"])
                    부제_스핀.pack(side="left", padx=(4, 0))
                    ttk.Label(부제_행, text="pt (기본 15)").pack(side="left", padx=(2, 0))
                    ttk.Label(parent, text="'제목: 부제, 제목'처럼 쉼표가 있으면 쉼표 앞 글을 이 크기의 부제로 윗줄에 넣습니다. "
                                           "서식 프로필의 예시 제목 표를 쓰면 그 표의 크기를 따릅니다.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w", padx=(18, 0))
                    담당자_행 = ttk.Frame(parent)
                    담당자_행.pack(anchor="w", fill="x", padx=(18, 0), pady=(6, 0))
                    ttk.Label(담당자_행, text="제목 표 담당자 칸(B2) 글:").pack(side="left")
                    담당자_입력 = ttk.Entry(담당자_행, textvariable=self.title_owner_var, width=58)
                    담당자_입력.pack(side="left", padx=(4, 0), fill="x", expand=True)
                    ttk.Label(parent, text="준말(제목:)·라벨로 새로 만드는 제목 표의 담당자 칸(2행1열 표는 A2)에 이 글을 넣습니다. "
                                           "비우면 기본 글(○○과장/담당관 : ◎◎◎☎2133-0000 …)을 넣고, 문서에 이미 있는 제목 표는 바꾸지 않습니다.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w", padx=(18, 0))
                    attachment_auto = ttk.Checkbutton(parent, text="붙임서식적용 (붙임 2종 자동 판별)",
                                                       variable=self.std_bool_vars["std_attachment_auto"])
                    attachment_auto.pack(anchor="w", pady=(6, 0))
                    ttk.Label(parent, text="쪽 첫부분의 '붙임' 표를 1행3열/1행2열 구조로 판별하여 해당 기준서식을 적용.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w")
                    midtitle_auto = ttk.Checkbutton(parent, text="중제목표 서식 적용 (Ⅰ·Ⅱ 번호 표)",
                                                     variable=self.std_bool_vars["std_midtitle_auto"])
                    midtitle_auto.pack(anchor="w", pady=(6, 0))
                    ttk.Label(parent, text="로마자 번호 칸 뒤에 글이 오는 1행 표를 중제목으로 판별해 번호·글을 HY견고딕 20pt 서식으로 정리.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w")
                    midtitle_bold = ttk.Checkbutton(parent, text="중제목 로마자 번호 굵게 (기본)",
                                                     variable=self.std_bool_vars["std_midtitle_bold"])
                    midtitle_bold.pack(anchor="w", padx=(18, 0))
                    if 주설정탭:
                        self.std_detail_checks += [title_auto, 부제_스핀, 담당자_입력, attachment_auto, midtitle_auto,
                                                   midtitle_bold]
                elif key == "table_style":
                    설정 = 설정_불러오기()
                    서식 = 준말_표서식(준말_사용표_만들기(설정))
                    ttk.Label(parent, text=("현재 기본 표 서식: " + 표서식_설명(서식)) if 서식 else
                              "준말 '표'가 없어 기본 표 서식을 쓰지 않습니다(아래 '표 머리글·본문 서식'을 씁니다).",
                              wraplength=610).pack(anchor="w")
                    ttk.Button(parent, text="준말 등록·관리 (표 서식 학습)…", command=준말창_열기).pack(anchor="w", pady=(4, 0))
                    ttk.Label(parent, text="준말 '표'의 본말에 담긴 예시 표처럼 문서의 일반 표(2행 2열 이상)에 칸 위치별 테두리·바탕색·"
                                           "글꼴·크기를 입힙니다. 제목·중제목·붙임 서식 표와 한 칸 상자는 두며, 문서의 '표:' 줄은 바꾸지 않습니다. "
                                           "준말 창의 '표 서식 학습…'으로 다른 예시 문서의 표를 배울 수 있습니다.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(2, 0))
                elif key == "abbreviation":
                    ttk.Button(parent, text="준말 등록·관리…", command=준말창_열기).pack(anchor="w")
                    ttk.Label(parent, text="기본 준말(제목1:·제목2:·개요:·붙임:·로1 : …)은 등록하지 않아도 바뀝니다. 콜론 앞에 준말을 적은 줄만 바꾸며, "
                                           "쪽 범위 작업에서는 건너뜁니다. 끄려면 이 단계의 체크를 해제하세요.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(2, 0))
                elif key == "precise_table":
                    profile_row = ttk.Frame(parent)
                    profile_row.pack(anchor="w", fill="x")
                    ttk.Label(profile_row, text="문서 스타일(계층구조)").pack(side="left")
                    콤보 = ttk.Combobox(profile_row, state="readonly", width=24)
                    콤보.pack(side="left", padx=6)
                    콤보.bind("<<ComboboxSelected>>", self._프로파일_선택)
                    복사버튼 = ttk.Button(profile_row, text="서식 복사하기…", command=self._서식_복사하기)
                    복사버튼.pack(side="left")
                    ttk.Button(profile_row, text="편집하여 추가…", command=self._서식_예시편집_시작).pack(side="left", padx=(6, 0))
                    ttk.Button(profile_row, text="이름 바꾸기…", command=self._서식_이름바꾸기).pack(side="left", padx=(6, 0))
                    수정버튼 = ttk.Button(profile_row, text="상세 수정…", command=self._서식_수정하기)
                    수정버튼.pack(side="left", padx=(6, 0))
                    삭제버튼 = ttk.Button(profile_row, text="삭제", command=self._서식_삭제하기)
                    삭제버튼.pack(side="left", padx=(6, 0))
                    삭제버튼.config(state="normal" if self._활성_서식_프로파일 else "disabled")
                    ttk.Label(parent, text="예시 문서를 복사하면 항목기호 문장의 계층별 서식과 제목·개요·중제목·붙임 표의 칸별(A1·A2·B2 …) "
                                           "글자·문단·테두리·배경 값을 모두 분석해 대표값을 정합니다. 이름과 세부값은 ‘상세 수정…’에서 고칩니다.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(2, 0))
                    if 주설정탭:
                        self.profile_combo = 콤보
                        self.copy_format_button = 복사버튼
                        self.edit_format_button = 수정버튼
                        self.delete_format_button = 삭제버튼
                    else:
                        self._팝업_profile_combo = 콤보
                        if "_팝업_profile_combo" not in self._프로파일_콤보_이름목록:
                            self._프로파일_콤보_이름목록.append("_팝업_profile_combo")
                    self._프로파일_목록갱신()
                elif key == "standard_format":
                    stdformat_check = ttk.Checkbutton(
                        parent, text="서식 옵션 사용 · 아래에서 바꿀 항목을 선택하세요", variable=self.stdformat_var)
                    stdformat_check.pack(anchor="w")
                    self.stdformat_var.set(True)  # 실행 모드가 서식 적용 여부를 결정하므로 중복된 전체 토글은 숨긴다.

                    std_detail = ttk.Frame(parent)
                    std_detail.pack(anchor="w", fill="x", pady=(4, 0))
                    기본항목_행 = ttk.Frame(std_detail)
                    기본항목_행.pack(anchor="w", fill="x")
                    기본항목_체크들 = []
                    for 문구, 설정_키, 여백 in [("편집 여백", "std_margin", 0), ("글자 가로폭", "std_ratio", 10), ("줄 사이 간격", "std_linespacing", 10)]:
                        체크 = ttk.Checkbutton(기본항목_행, text=문구, variable=self.std_bool_vars[설정_키])
                        체크.pack(side="left", padx=(여백, 0))
                        기본항목_체크들.append(체크)

                    문단위간격_체크 = ttk.Checkbutton(std_detail, text="항목 사이 간격 맞추기 · 문단 위 여백", variable=self.std_bool_vars["std_parspace"])
                    문단위간격_체크.pack(anchor="w", pady=(8, 0))

                    문단위간격_행 = ttk.Frame(std_detail)
                    문단위간격_행.pack(anchor="w", fill="x", padx=(18, 0), pady=(2, 0))
                    문단위간격_스핀들 = []
                    for 라벨, 설정_키 in [("장", "std_parspace_chapter"), ("중제목 Ⅰ", "std_parspace_midtitle"),
                                        ("□", "std_parspace_box"), ("ㅇ·○·☞", "std_parspace_circle"), ("-", "std_parspace_dash"),
                                        ("*·※·→", "std_parspace_note")]:
                        ttk.Label(문단위간격_행, text=f"{라벨}:").pack(side="left", padx=(0 if 라벨 == "장" else 10, 0))
                        스핀 = ttk.Spinbox(문단위간격_행, from_=0, to=99, width=3, textvariable=self.std_parspace_vars[설정_키], justify="center")
                        스핀.pack(side="left", padx=(4, 0))
                        ttk.Label(문단위간격_행, text="pt").pack(side="left", padx=(2, 0))
                        문단위간격_스핀들.append(스핀)
                    ttk.Label(문단위간격_행, text="깊은 항목에서 복귀할 때:").pack(side="left", padx=(12, 0))
                    복귀배율_스핀 = ttk.Spinbox(
                        문단위간격_행, from_=100, to=400, increment=10, width=4,
                        textvariable=self.std_parspace_vars["std_parspace_return_percent"], justify="center")
                    복귀배율_스핀.pack(side="left", padx=(4, 0))
                    ttk.Label(문단위간격_행, text="% (100% = 기존 간격)").pack(side="left", padx=(2, 0))
                    문단위간격_스핀들.append(복귀배율_스핀)

                    빈줄삭제_체크 = ttk.Checkbutton(
                        std_detail, text="항목기호 문장 사이·문서 끝 빈 줄 삭제 (빈 줄로 띄운 간격은 문단 위 여백으로 대신하고, 문서 끝 빈 줄로 생기는 빈 쪽을 없앰)",
                        variable=self.std_bool_vars["std_remove_blank_lines"])
                    빈줄삭제_체크.pack(anchor="w", pady=(6, 0))

                    if 주설정탭:
                        self.stdformat_check = stdformat_check
                        self.std_detail_checks += 기본항목_체크들 + [문단위간격_체크, 빈줄삭제_체크]
                        self.std_parspace_spins = 문단위간격_스핀들
                elif key == "parenthesis":
                    기호_체크 = ttk.Checkbutton(parent, text="기호별 글꼴·크기·시작 위치 맞추기 (□ / ㅇ / - / ※ / •; 점 계열은 •로 통일)",
                                              variable=self.std_bool_vars["std_symbols"])
                    기호_체크.pack(anchor="w")

                    기호_굵게_행 = ttk.Frame(parent)
                    기호_굵게_행.pack(anchor="w", fill="x", pady=(2, 0))
                    ttk.Label(기호_굵게_행, text="굵게:").pack(side="left")
                    기호_굵게_체크들 = []
                    for 기호_텍스트, 설정_키 in [("□", "std_symbol_box_bold"), ("ㅇ", "std_symbol_o_bold"), ("-", "std_symbol_dash_bold"), ("※", "std_symbol_note_bold")]:
                        체크 = ttk.Checkbutton(기호_굵게_행, text=기호_텍스트, variable=self.std_bool_vars[설정_키])
                        체크.pack(side="left", padx=(6, 0))
                        기호_굵게_체크들.append(체크)

                    기호글꼴_틀 = ttk.LabelFrame(parent, text="문장기호별 글꼴 · 크기", padding=8)
                    기호글꼴_틀.pack(anchor="w", fill="x", pady=(6, 0))

                    폰트폴더_행 = ttk.Frame(기호글꼴_틀)
                    폰트폴더_행.pack(anchor="w", fill="x", pady=(0, 6))
                    ttk.Label(폰트폴더_행, text="글꼴 폴더").pack(side="left")
                    폰트폴더_입력 = ttk.Entry(폰트폴더_행, textvariable=self.font_folder_var, width=40)
                    폰트폴더_입력.pack(side="left", padx=(6, 4))
                    ttk.Button(폰트폴더_행, text="찾아보기…", command=self._폰트폴더_찾아보기).pack(side="left", padx=(0, 4))
                    ttk.Button(폰트폴더_행, text="새로고침", command=self._폰트목록_새로고침).pack(side="left")

                    ttk.Label(
                        기호글꼴_틀,
                        text="기본은 윈도우 글꼴 폴더(C:\\Windows\\Fonts)이며, 이 폴더에서 글꼴 목록을 불러옵니다. "
                             "한컴오피스 전용 번들(HFT) 글꼴은 설치 경로에서 자동으로 찾아 목록에 함께 더합니다. "
                             "목록에 없는 이름도 직접 입력할 수 있습니다.",
                        style="Hint.TLabel", wraplength=520
                    ).pack(anchor="w", pady=(0, 6))

                    글꼴_콤보들, 크기_스핀들 = {}, {}
                    for 기호 in 문장기호_목록:
                        행 = ttk.Frame(기호글꼴_틀)
                        행.pack(anchor="w", fill="x", pady=(2, 0))
                        ttk.Label(행, text=기호, width=3).pack(side="left")
                        콤보 = ttk.Combobox(
                            행, textvariable=self.symbol_font_vars[기호]["font"],
                            values=self._한글_폰트_목록_캐시, width=22
                        )
                        콤보.pack(side="left", padx=(4, 8))
                        self._휠_콤보박스_바인딩(콤보)
                        글꼴_콤보들[기호] = 콤보
                        ttk.Label(행, text="크기").pack(side="left")
                        크기스핀 = ttk.Spinbox(
                            행, from_=1, to=200, width=4, justify="center",
                            textvariable=self.symbol_font_vars[기호]["size"]
                        )
                        크기스핀.pack(side="left", padx=(4, 2))
                        ttk.Label(행, text="pt").pack(side="left")
                        크기_스핀들[기호] = 크기스핀

                    표글꼴_틀 = ttk.LabelFrame(parent, text="표 안 글꼴 · 크기", padding=8)
                    표글꼴_틀.pack(anchor="w", fill="x", pady=(6, 0))
                    ttk.Label(
                        표글꼴_틀,
                        text="'표 머리글·본문 서식' 작업에서 표의 첫 행(머리글)과 나머지 행(본문)에 적용합니다. "
                             "한 칸짜리 표(제목·개요 상자)는 바꾸지 않습니다.",
                        style="Hint.TLabel", wraplength=520
                    ).pack(anchor="w", pady=(0, 4))
                    for part, 이름 in (("header", "머리글"), ("body", "본문")):
                        행 = ttk.Frame(표글꼴_틀)
                        행.pack(anchor="w", fill="x", pady=(2, 0))
                        ttk.Label(행, text=이름, width=6).pack(side="left")
                        콤보 = ttk.Combobox(
                            행, textvariable=self.table_font_vars[part]["font"],
                            values=self._한글_폰트_목록_캐시, width=22
                        )
                        콤보.pack(side="left", padx=(4, 8))
                        self._휠_콤보박스_바인딩(콤보)
                        # 글꼴 목록 새로고침이 문장기호 글꼴 상자와 함께 갱신하도록 같이 보관한다.
                        글꼴_콤보들[f"표_{part}"] = 콤보
                        ttk.Label(행, text="크기").pack(side="left")
                        크기스핀 = ttk.Spinbox(
                            행, from_=1, to=200, width=4, justify="center",
                            textvariable=self.table_font_vars[part]["size"]
                        )
                        크기스핀.pack(side="left", padx=(4, 2))
                        ttk.Label(행, text="pt").pack(side="left")
                        크기_스핀들[f"표_{part}"] = 크기스핀

                    paren_shrink_check = ttk.Checkbutton(
                        parent,
                        text="괄호 안 부연설명 글자 크기 축소\n(문장 중간·끝에 오는 괄호 안 글자를 2pt 작게 표시)",
                        variable=self.paren_shrink_var,
                    )
                    paren_shrink_check.pack(anchor="w", pady=(10, 0))

                    label_bold_frame = ttk.LabelFrame(parent, text="항목 이름 강조", padding=10)
                    label_bold_frame.pack(fill="x", pady=(10, 0))
                    paren_label_bold_check = ttk.Checkbutton(
                        label_bold_frame,
                        text="문두 라벨(괄호 및 콜론 라벨) 굵게\n(\"ㅇ (운영방식)\"의 괄호 또는 \"- 추진부서 :\"처럼 문장부호 뒤 콜론 앞 텍스트 굵게)",
                        variable=self.paren_label_bold_var,
                    )
                    paren_label_bold_check.pack(anchor="w")
                    symbol_frame = ttk.LabelFrame(label_bold_frame, text='↳ 강조할 기호 선택', padding=6)
                    symbol_frame.pack(fill='x', pady=(6, 0))
                    label_symbol_checks = []
                    for index, (skey, svar) in enumerate(self.label_symbol_vars.items()):
                        check = ttk.Checkbutton(symbol_frame, text=skey, variable=svar)
                        check.grid(row=index // 8, column=index % 8, sticky='w', padx=4)
                        label_symbol_checks.append(check)
                    # 문두 라벨 굵게가 켜져 있을 때만 의미가 있으므로 기호 선택과 같이
                    # 활성/비활성된다.
                    consistency_check = ttk.Checkbutton(
                        label_bold_frame,
                        text="항목기호별 굵게 일관성 적용\n(같은 기호의 라벨이 굵게 되면 \"- 조례제정 (설명)\"의 \"조례제정\"처럼 "
                             "다른 문단 머리말도 굵게 맞춤, 괄호 설명은 제외)",
                        variable=self.std_bool_vars["std_marker_bold_consistency"],
                    )
                    consistency_check.pack(anchor="w", pady=(6, 0))
                    label_symbol_checks.append(consistency_check)

                    if 주설정탭:
                        self.std_detail_checks += [기호_체크] + 기호_굵게_체크들
                        self.symbol_font_combos = 글꼴_콤보들
                        self.symbol_size_spins = 크기_스핀들
                        self.font_folder_entry = 폰트폴더_입력
                        self.paren_shrink_check = paren_shrink_check
                        self.paren_label_bold_check = paren_label_bold_check
                        self.label_symbol_checks = label_symbol_checks
                elif key == "supplement_indent":
                    체크 = ttk.Checkbutton(
                        parent,
                        text="부연설명 문단 전체를 위 문단에 맞추기\n*, **, ※의 시작 위치를 위 문단의 본문 첫 글자 아래로 옮깁니다.\n‘내어쓰기’는 같은 문단의 둘째 줄 이후만 맞추므로 역할이 다릅니다.",
                        variable=self.std_bool_vars["std_supplement_indent"])
                    체크.pack(anchor="w")
                    if 주설정탭:
                        self.std_detail_checks.append(체크)
                elif key == "table_format":
                    체크 = ttk.Checkbutton(
                        parent,
                        text="표 헤더/본문 서식적용\n(1행: 한컴돋움 13pt 굵게 / 나머지 행: 휴먼명조 12pt)",
                        variable=self.std_bool_vars["std_table_header"],
                    )
                    체크.pack(anchor="w")
                    if 주설정탭:
                        self.std_detail_checks.append(체크)
                elif key == "hanging_indent":
                    체크 = ttk.Checkbutton(parent, text="내어쓰기 · 둘째 줄부터 본문 시작 위치에 맞추기",
                                          variable=self.std_bool_vars["std_hanging_indent"])
                    체크.pack(anchor="w")
                    ttk.Label(parent, text="예: ㅇ (개요) 본문 → 다음 줄은 ‘본문’ 아래부터 시작\n기호별 글꼴 옵션을 켜지 않아도 적용됩니다.",
                              style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(1, 0))
                    if 주설정탭:
                        self.std_detail_checks.append(체크)

            def _세부작업_열기(self, mode, save_default=None):
                if mode not in self.stage_choices:
                    return  # 파일포맷 변경 등 세부 작업이 없는 작업
                titles = {"spacing": "자간 정리", "unify": "서식 통일", "format": "한 번에 적용(자간 조정 제외)",
                          "all": "한 번에 적용"}
                dialog = tk.Toplevel(self.root)
                dialog.title(f"{titles[mode]} · 세부 작업")
                dialog.geometry({"spacing": "520x650", "unify": "520x320"}.get(mode, "720x700"))
                dialog.transient(self.root)
                dialog.grab_set()
                frame = ttk.Frame(dialog, padding=14)
                frame.pack(fill="both", expand=True)
                ttk.Label(frame, text="실행 순서대로 표시합니다. 체크를 끄면 해당 단계는 건너뜁니다.\n"
                                      "기존 설정에서 꺼진 기능은 여기서 켜도 실행되지 않습니다. 아래 상세 항목은 "
                                      "세부 설정 창의 내용과 같은 값을 그대로 공유합니다.",
                          style="Hint.TLabel", wraplength=680).pack(anchor="w", pady=(0, 8))
                canvas = tk.Canvas(frame, highlightthickness=0)
                scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
                canvas.configure(yscrollcommand=scrollbar.set)
                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
                content = ttk.Frame(canvas)
                window = canvas.create_window((0, 0), window=content, anchor="nw")
                content.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
                canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window, width=event.width))
                choices = {key: tk.BooleanVar(value=self.stage_choices[mode][key])
                           for key, _ in stages_for_mode(mode)}
                for number, (key, label) in enumerate(stages_for_mode(mode), 1):
                    item = ttk.Frame(content)
                    item.pack(fill="x", pady=(4, 7))
                    ttk.Checkbutton(item, text=f"{number:02d}. {label}", style="Stage.TCheckbutton",
                                    variable=choices[key]).pack(anchor="w")
                    ttk.Label(item, text=STAGE_EXAMPLES[key], style="Hint.TLabel",
                              wraplength=610, justify="left").pack(anchor="w", padx=(25, 0), pady=(1, 0))
                    detail = ttk.Frame(item)
                    detail.pack(anchor="w", padx=(25, 0), pady=(4, 0), fill="x")
                    self._자간정리_항목_상세(detail, key, 주설정탭=False)
                    self._서식정리_항목_상세(detail, key, 주설정탭=False)

                기본저장_var = tk.BooleanVar(value=(
                    self._세부작업_기본저장.get(mode, True) if save_default is None else bool(save_default)
                ))

                def cleanup():
                    if "_팝업_profile_combo" in self._프로파일_콤보_이름목록:
                        self._프로파일_콤보_이름목록.remove("_팝업_profile_combo")
                    if hasattr(self, "_팝업_profile_combo"):
                        del self._팝업_profile_combo

                def close():
                    cleanup()
                    dialog.destroy()

                def save():
                    self.stage_choices[mode] = {key: variable.get() for key, variable in choices.items()}
                    self._세부작업_기본저장[mode] = bool(기본저장_var.get())
                    if 기본저장_var.get():
                        self._세부작업_기본값_저장(mode)
                    self._세부작업_옵션_맞춤(mode)   # 관련 작업을 바꿨으면 카드 옵션(표 제외 등)도 맞춘다
                    self._요약갱신()
                    close()
                buttons = ttk.Frame(dialog, padding=(14, 4, 14, 12))
                buttons.pack(fill="x")
                ttk.Checkbutton(buttons, text="이 구성 다음에도 기본값으로 사용",
                                variable=기본저장_var).pack(side="left")
                ttk.Button(buttons, text="취소", command=close).pack(side="right")
                ttk.Button(buttons, text="적용", command=save).pack(side="right", padx=8)
                dialog.protocol("WM_DELETE_WINDOW", close)

            def _세부작업_기본값_저장(self, mode, 저장=True):
                """작업 유형의 세부 작업 구성을 다음 실행에도 쓰도록 저장한다. 저장=False면 저장값을 지운다."""
                if mode not in self.stage_choices:
                    return
                self._세부작업_기본저장[mode] = bool(저장)
                저장값 = 설정_불러오기()
                저장된_세부작업 = 저장값.get("stage_choices", {})
                if not isinstance(저장된_세부작업, dict):
                    저장된_세부작업 = {}
                if 저장:
                    저장된_세부작업[mode] = dict(self.stage_choices[mode])
                elif mode in 저장된_세부작업:
                    del 저장된_세부작업[mode]
                else:
                    return
                저장값["stage_choices"] = 저장된_세부작업
                설정_저장(저장값)

            def _요약갱신(self, *args):
                # 세부 작업 창·설정창·웹 화면에서 바꾼 '01 문서 전체 자간 초기화'를 카드의 '기존 자간 초기화'에도 맞춘다.
                초기화 = bool(self.stage_choices["spacing"].get("reset_spacing", True))
                if hasattr(self, "reset_spacing_var") and bool(self.reset_spacing_var.get()) != 초기화:
                    self.reset_spacing_var.set(초기화)
                if not hasattr(self, "options_summary"):
                    return
                mode = self.selected_mode.get()
                if mode not in self.stage_choices:
                    # 파일포맷 변경은 세부 작업이 없는 변환 작업이다(세부 작업 표를 찾지 않는다).
                    self.options_summary.configure(
                        text="문서를 다른 파일 형식으로 바꿔 새 파일로 저장합니다. 원본은 바꾸지 않습니다.")
                    return
                if mode == "spacing":
                    summary = ("줄 끝의 끊긴 단어와 자간을 정리합니다." if 초기화
                               else "기존 자간을 초기화하지 않고 그 위에서 줄 끝의 끊긴 단어를 정리합니다.")
                    자간켜짐 = getattr(self, "spacing_enabled_var", None)
                    쪽켜짐 = getattr(self, "spacing_page_fit_var", None)
                    if 자간켜짐 is not None and not 자간켜짐.get():
                        summary = "자간 변경 없이 페이지 맞춤만 실행합니다." if 쪽켜짐.get() else "자간 정리 또는 페이지 맞춤을 켜 주세요."
                    elif 쪽켜짐 is not None and 쪽켜짐.get():
                        summary += " · 페이지 맞춤 포함"
                    if ((자간켜짐 is None or 자간켜짐.get())
                            and hasattr(self, "table_spacing_var") and not self.table_spacing_var.get()):
                        summary += " · 표 제외"
                elif mode == "unify":
                    summary = "항목기호별로 문서에서 많이 쓰인 서식을 적용합니다."
                    for 이름, 문구 in (("unify_exclude_tables_var", "표 제외"), ("unify_exclude_spacing_var", "자간 정리 제외"),
                                     ("unify_exclude_pagefit_var", "페이지 맞춤 제외"),
                                     ("unify_keep_layout_var", "원본 쪽 구성 유지"),
                                     ("unify_full_format_var", "전체 서식 맞추기")):
                        if hasattr(self, 이름) and getattr(self, 이름).get():
                            summary += f" · {문구}"
                elif mode == "format":
                    summary = "자간 조정 제외: 기존 자간은 그대로 두고 공문서 서식만 적용합니다."
                else:
                    summary = "공문서 서식을 입히고 자간까지 함께 정리합니다."
                if mode in ("all", "format") and hasattr(self, "exclude_tables_var") and self.exclude_tables_var.get():
                    summary += " · 표 제외"
                if mode in ("all", "format") and hasattr(self, "all_exclude_pagefit_var") and self.all_exclude_pagefit_var.get():
                    summary += " · 페이지 맞춤 제외"
                choices = self.stage_choices[mode]
                # 카드 옵션으로 끈 작업(자간 정리의 자간 초기화, 표 제외·페이지 맞춤 제외 등)은 위 문구로 이미 알린다.
                카드로_끈작업 = 카드옵션_끈작업(self._카드옵션값_목록(), mode)
                disabled = sum(not value for key, value in choices.items()
                               if stage_default(key) and key not in 카드로_끈작업)
                if choices.get("style_unify") and mode != "unify":
                    summary += " · 서식 통일 포함"
                if disabled:
                    summary += f" · 세부 작업 {disabled}개 제외"
                self.options_summary.configure(text=summary)

            def _범위_상태_갱신(self, *args):
                """'쪽 지정'일 때만 시작·끝 쪽 입력칸을 켠다(작업 중에는 항상 끔)."""
                상태 = "normal" if (self.range_mode_var.get() == "pages" and not self.running) else "disabled"
                for 위젯 in (self.range_start_spin, self.range_end_spin):
                    위젯.config(state=상태)

            def _쪽범위_토글(self):
                """기본 화면에는 문서 전체만 표시하고, 요청 시에만 쪽 입력을 펼친다."""
                지정 = bool(self.page_range_var.get())
                self.range_mode_var.set("pages" if 지정 else "all")
                if 지정:
                    self.page_range_details.pack(side="left", fill="x", expand=True)
                elif self.page_range_details.winfo_manager() == "pack":
                    self.page_range_details.pack_forget()
                self._범위_상태_갱신()

            # ---- 사용 순서 안내(테두리 강조) ----------------------------------
            def _안내_설정(self, 단계):
                """1=문서 추가, 2=작업 선택, 3=실행, 0=안내 없음. 지금 할 차례인 영역의 테두리를 강조한다."""
                self._안내단계 = 단계
                self.file_frame.configure(style="Guide.TLabelframe" if 단계 == 1 else "TLabelframe")
                self.choose_frame.configure(style="Guide.TLabelframe" if 단계 == 2 else "TLabelframe")
                self.start_wrap.configure(bg=UI_COLORS["teal"] if 단계 == 3 else UI_COLORS["bg"])
                labels = {1: "1 / 3  문서 선택", 2: "2 / 3  방식 선택", 3: "3 / 3  실행 준비", 0: "새 작업"}
                self.header_status.configure(text=labels.get(단계, "새 작업"))

            def _모드카드_외관갱신(self, *args):
                """선택한 처리 방식만 분명하게 드러낸다.

                라디오 버튼의 작은 표시만으로 선택 상태를 전달하지 않고 카드 테두리와
                배경을 함께 바꾼다. 키보드로 선택해도 같은 피드백을 받는다.
                """
                selected = self._카드키(self.selected_mode.get())
                if hasattr(self, "card_mode_var") and self.card_mode_var.get() != selected:
                    self.card_mode_var.set(selected)
                for mode, (card, inner, description) in getattr(self, "mode_cards", {}).items():
                    active = mode == selected
                    border = UI_COLORS["teal"] if active else UI_COLORS["separator"]
                    surface = UI_COLORS["teal_tint"] if active else UI_COLORS["surface"]
                    card.configure(bg=border)
                    inner.configure(bg=surface)
                    description.configure(bg=surface)
                    for check in getattr(self, "card_option_checks", {}).get(mode, ()):
                        check.configure(bg=surface, activebackground=surface)

            def _메인_크기조정(self, event=None):
                """창 크기가 바뀔 때 UI 밀도를 폭에 맞춰 조정한다."""
                if event is not None and getattr(event, "widget", self.root) is not self.root:
                    return
                예약 = getattr(self, "_반응형_예약", None)
                if 예약 is not None:
                    try:
                        self.root.after_cancel(예약)
                    except tk.TclError:
                        pass
                self._반응형_예약 = self.root.after(120, self._반응형_배치)

            def _반응형_배치(self):
                self._반응형_예약 = None
                if not self.root.winfo_exists():
                    return
                def 배치해제(widget):
                    manager = widget.winfo_manager()
                    if manager == "pack":
                        widget.pack_forget()
                    elif manager == "grid":
                        widget.grid_forget()
                width, height = self.root.winfo_width(), self.root.winfo_height()
                scale = getattr(self, "_ui_scale", 1.0)
                cards = list(self.mode_cards.items())
                columns = 2 if width < 1000 * scale else len(cards)
                for index, (_mode, (card, _inner, _desc)) in enumerate(cards):
                    card.grid_configure(row=1 + index // columns, column=index % columns,
                                        sticky="nsew", padx=3, pady=3)
                rows = (len(cards) + columns - 1) // columns
                for column in range(4):
                    self.choose_frame.grid_columnconfigure(column, weight=1 if column < columns else 0,
                                                           uniform="modes" if column < columns else "")
                for row in range(1, 5):
                    self.choose_frame.grid_rowconfigure(row, weight=1 if row < 1 + rows else 0)
                self.quick_actions.grid_configure(row=1 + rows, column=0, columnspan=columns)
                self.format_quick.grid_configure(row=2 + rows, column=0, columnspan=columns)
                self.scope_frame.grid_configure(row=3 + rows, column=0, columnspan=columns)
                # 문서 버튼은 작은 창에서 줄바꿈 없이 노출되도록 2×2로 바꾼다.
                file_columns = 2 if width < 760 * scale else 4
                for button in self.file_buttons:
                    배치해제(button)
                배치해제(self.file_count)
                for index, button in enumerate(self.file_buttons):
                    button.grid(row=index // file_columns, column=index % file_columns,
                                sticky="ew", padx=(0, 6), pady=2)
                for column in range(4):
                    self.file_actions.grid_columnconfigure(column, weight=1 if column < file_columns else 0)
                self.file_count.grid(row=(len(self.file_buttons) + file_columns - 1) // file_columns,
                                     column=0, columnspan=file_columns, sticky="e")
                compact = width < 760 * scale
                배치해제(self.tools_button)
                # 문서 도구 메뉴는 개발자 모드에서만 보인다.
                quick_widgets = ((self.tools_button,) if self.developer_mode_var.get() else ()) + (
                    self.stage_details_button, self.settings_button)
                for widget in quick_widgets:
                    배치해제(widget)
                배치해제(self.options_summary)
                if compact:
                    for index, widget in enumerate(quick_widgets):
                        widget.grid(row=0, column=index, sticky="ew", padx=(0, 4), pady=2)
                        self.options_summary.grid(row=1, column=0, columnspan=len(quick_widgets), sticky="w")
                else:
                    for widget in quick_widgets:
                        widget.pack(side="right", padx=(0, 6))
                    self.options_summary.pack(side="left", fill="x", expand=True)
                wrap = max(360, width - round(80 * scale))
                for widget in (getattr(self, "options_summary", None), getattr(self, "footer_note", None)):
                    if widget is not None:
                        widget.configure(wraplength=wrap)

            def _모드_선택됨(self):
                """작업 종류를 고르면(이미 선택된 것을 다시 눌러도) 다음 차례인 '실행'을 안내한다."""
                self._요약갱신()
                if self._안내단계 == 2 and not self.running:
                    self._안내_설정(3)

            @staticmethod
            def _카드키(mode):
                """내부 작업 유형이 놓이는 카드. 서식 적용(format)은 '한 번에 적용'에서 자간 조정을 뺀 것이다."""
                return "all" if mode == "format" else mode

            def _한번에_모드(self):
                """'한 번에 적용' 카드의 내부 작업 유형: 자간 조정 포함이면 all, 아니면 format."""
                return "all" if self.include_spacing_var.get() else "format"

            # 작업 카드 옵션(stage_selection.CARD_OPTION_STAGES 키) → (화면 변수, 변수가 옵션의 반대 값인가).
            # 자간 정리의 '표 제외'는 설정 table_spacing(표 안 문장 자간조정)의 반대 값이다.
            _카드옵션_변수 = {
                "spacing_enabled": ("spacing_enabled_var", False),
                "spacing_page_fit": ("spacing_page_fit_var", False),
                "spacing_reset_existing": ("reset_spacing_var", False),
                "spacing_exclude_tables": ("table_spacing_var", True),
                "unify_exclude_tables": ("unify_exclude_tables_var", False),
                "unify_exclude_spacing": ("unify_exclude_spacing_var", False),
                "unify_exclude_pagefit": ("unify_exclude_pagefit_var", False),
                "unify_keep_layout": ("unify_keep_layout_var", False),
                "unify_quick_mode": ("unify_quick_mode_var", False),
                "all_include_spacing": ("include_spacing_var", False),
                "all_exclude_tables": ("exclude_tables_var", False),
                "all_exclude_pagefit": ("all_exclude_pagefit_var", False),
            }

            def _카드옵션값(self, 옵션):
                """카드 옵션 값(화면 변수가 아직 없으면 None)."""
                이름, 반대 = self._카드옵션_변수[옵션]
                변수 = getattr(self, 이름, None)
                return None if 변수 is None else bool(변수.get()) != 반대

            def _카드옵션값_목록(self):
                return {옵션: self._카드옵션값(옵션) for 옵션 in self._카드옵션_변수}

            def _세부작업_값_넣기(self, mode, 값들):
                """세부 작업 값을 바꾸고 바뀐 것이 있었는지 돌려준다."""
                선택 = self.stage_choices[mode]
                바뀜 = any(선택.get(key) != 값 for key, 값 in 값들.items())
                선택.update(값들)
                return 바뀜

            def _세부작업_연동_마무리(self, modes):
                """연동으로 바뀐 세부 작업 구성을 저장하고(기본값 저장을 켠 유형만) 설정창의 단계 체크에도 반영한다."""
                for mode in modes:
                    if self._세부작업_기본저장.get(mode):
                        self._세부작업_기본값_저장(mode)
                for 이름, mode in (("spacing_stage_vars", "spacing"), ("format_stage_vars", "format"),
                                  ("indent_stage_vars", "format")):
                    if mode not in modes:
                        continue
                    for key, var in getattr(self, 이름, {}).items():
                        값 = bool(self.stage_choices[mode].get(key, True))
                        if bool(var.get()) != 값:
                            var.set(값)

            def _카드옵션_세부작업_반영(self, 옵션):
                """카드 옵션을 바꾸면 그 카드의 세부 작업 가운데 관련 작업을 모두 같이 켜고 끈다(2026-10-04 사용자 요청).

                실행창 카드·웹 화면·설정창 어디서 바꿔도 같은 변수 감시로 반영한다. 세부 작업에 맞춰 옵션을 고치는
                중(_세부작업_옵션_맞춤)에는 사용자가 고른 세부 작업을 덮지 않도록 건너뛴다.
                """
                if getattr(self, "_카드옵션_맞추는중", False):
                    return
                옵션값 = self._카드옵션값_목록()
                바뀐_유형 = [mode for mode in 카드옵션_세부작업[옵션][0]
                           if self._세부작업_값_넣기(mode, 카드옵션_세부작업값(옵션, 옵션값[옵션], 옵션값, mode))]
                if 옵션 == "spacing_enabled" and not 옵션값[옵션]:
                    self.stage_choices["spacing"]["style_unify"] = False
                self._세부작업_연동_마무리(바뀐_유형)

            def _세부작업_옵션_맞춤(self, mode):
                """세부 작업 구성에 맞게 그 카드의 옵션을 맞춘다(세부 작업 창·화면 목록·설정창에서 바꾼 뒤).

                '제외' 옵션은 관련 작업이 모두 꺼지면 켜지고 하나라도 켜면 꺼진다. 옵션이 관련 작업을 끄는 쪽으로 바뀌면
                같은 카드의 다른 구성(한 번에 적용의 자간 조정 포함 all·제외 format)에서도 관련 작업을 끈다. 한 번에 적용에서
                자간 작업을 모두 끄면 '자간 조정 포함'이 꺼지고 서식 적용(format)으로 바뀐다.
                """
                바뀐_옵션 = []
                self._카드옵션_맞추는중 = True
                try:
                    for 옵션 in 카드옵션_세부작업:
                        값, 현재 = 카드옵션_판정(옵션, self.stage_choices[mode], mode), self._카드옵션값(옵션)
                        if 값 is None or 현재 is None or 값 == 현재:
                            continue
                        이름, 반대 = self._카드옵션_변수[옵션]
                        getattr(self, 이름).set(값 != 반대)
                        바뀐_옵션.append(옵션)
                finally:
                    self._카드옵션_맞추는중 = False
                옵션값 = self._카드옵션값_목록()
                바뀐_유형 = set()
                for 옵션 in 바뀐_옵션:
                    if not 카드옵션_끄는값(옵션, 옵션값[옵션]):
                        continue
                    for 다른_유형 in 카드옵션_세부작업[옵션][0]:
                        if 다른_유형 != mode and self._세부작업_값_넣기(
                                다른_유형, 카드옵션_세부작업값(옵션, 옵션값[옵션], 옵션값, 다른_유형)):
                            바뀐_유형.add(다른_유형)
                self._세부작업_연동_마무리(바뀐_유형)
                if "all_include_spacing" in 바뀐_옵션 and self.selected_mode.get() in ("all", "format"):
                    self.selected_mode.set(self._한번에_모드())

            def _카드옵션_연동_시작(self):
                """카드 옵션과 세부 작업을 처음 맞추고 옵션 변수에 연동 감시를 건다(화면 변수를 모두 만든 뒤).

                켜 둔 '제외' 옵션은 저장된 세부 작업 구성보다 우선해 관련 작업을 끄고, 나머지 옵션은 세부 작업 구성을
                따른다(예: 서식 통일의 쪽 맞춤은 기본 꺼짐이라 '페이지 맞춤 제외'가 켜져 보인다). 감시는 기존 감시보다 나중에
                걸어 먼저 실행되므로, 요약 문구·설정 저장은 바뀐 세부 작업을 본다.
                """
                self._카드옵션_맞추는중 = False
                # 새 포함 옵션의 저장된 OFF도 기본 단계보다 우선한다.
                for 옵션 in ("spacing_enabled", "spacing_page_fit"):
                    값 = self._카드옵션값(옵션)
                    if 값 is False or (옵션 == "spacing_page_fit" and 값 is True and not any(
                            self.stage_choices["spacing"].get(key) for key in ("page_fit", "page_group"))):
                        self._카드옵션_세부작업_반영(옵션)
                for 옵션, (_, _, 제외) in 카드옵션_세부작업.items():
                    if 제외 and self._카드옵션값(옵션):
                        self._카드옵션_세부작업_반영(옵션)
                for mode in ("spacing", "unify", self._한번에_모드()):
                    self._세부작업_옵션_맞춤(mode)
                for 옵션, (이름, _) in self._카드옵션_변수.items():
                    getattr(self, 이름).trace_add("write", lambda *_, 옵션=옵션: self._카드옵션_세부작업_반영(옵션))

            def _설정탭_세부작업_변경(self, mode, key, var):
                """설정창의 단계 체크를 세부 작업 구성에 반영하고, 바뀌었으면 카드 옵션도 맞춘다."""
                값 = bool(var.get())
                if self.stage_choices[mode].get(key) == 값:
                    return
                self.stage_choices[mode][key] = 값
                self._세부작업_옵션_맞춤(mode)

            def _카드옵션_변경(self, mode):
                """카드 옵션 체크를 바꾸면 그 카드를 고른다(값 저장·요약은 변경 감시가 한다)."""
                if self.running:
                    return
                self.selected_mode.set(self._한번에_모드() if mode in ("all", "format") else mode)
                self._모드_선택됨()

            def _표제외_변경(self):
                """'표 제외'를 바꾸면 '한 번에 적용' 카드를 고른다(값 저장·요약은 변경 감시가 한다)."""
                if self.running:
                    return
                self.selected_mode.set(self._한번에_모드())
                self._모드_선택됨()

            def _카드_클릭(self, mode):
                if self.running:
                    self._모드카드_외관갱신()
                    return
                self.selected_mode.set(self._한번에_모드() if mode in ("all", "format") else mode)
                self._모드_선택됨()

            def _자간포함_변경(self):
                """'자간 조정 포함'을 바꾸면 '한 번에 적용' 카드를 고르고 내부 작업 유형을 맞춘다."""
                if self.running:
                    return
                self.selected_mode.set(self._한번에_모드())
                self._모드_선택됨()

            def _자간초기화_값변경(self, *args):
                """'기존 자간 초기화' 값을 자간 정리 세부 작업 01에 반영하고 설정 파일에 저장한다."""
                self.stage_choices["spacing"]["reset_spacing"] = bool(self.reset_spacing_var.get())
                self._설정_변경됨()
                self._요약갱신()

            def _자간초기화_변경(self):
                """'기존 자간 초기화'·'표 내 자간 정리'를 바꾸면 '자간 정리' 카드를 고른다."""
                if self.running:
                    return
                self.selected_mode.set("spacing")
                self._모드_선택됨()

            # ---- 문서·결과 열기 / 작업 결과 표시 ------------------------------
            def _경로_열기(self, path):
                """파일이나 폴더를 연결된 프로그램(탐색기·한글)으로 연다."""
                try:
                    if hasattr(os, "startfile"):
                        os.startfile(str(path))
                    else:  # Windows가 아닌 환경(시험용)
                        import subprocess
                        subprocess.Popen(["xdg-open", str(path)])
                    return True
                except Exception as e:
                    self._알림(messagebox.showerror, APP_NAME, f"열지 못했습니다.\n{path}\n\n{e}", parent=self.root)
                    return False

            def _문서_열기(self, event):
                """'01 정리할 문서' 목록에서 파일을 더블클릭하면 그 문서를 연다."""
                if not self.files:
                    return
                순번 = self.file_list.nearest(event.y)
                상자 = self.file_list.bbox(순번) if 0 <= 순번 < len(self.files) else None
                if not 상자 or not (상자[1] <= event.y <= 상자[1] + 상자[3]):
                    return  # 항목이 없는 빈 곳을 더블클릭한 경우
                경로 = self.files[순번]
                if not os.path.isfile(경로):
                    self._알림(messagebox.showwarning, APP_NAME, f"파일을 찾을 수 없습니다.\n{경로}", parent=self.root)
                    return
                self._경로_열기(경로)

            def _원본폴더_버튼_갱신(self):
                """'원본 폴더 열기'는 문서가 하나라도 추가되어 있으면 켜고, 목록이 비면 끈다."""
                self.open_folder_button.config(state="normal" if self.files else "disabled")

            def _원본폴더_열기(self):
                폴더들 = []
                원본들 = list(self.files) or [항목["원본"] for 항목 in self._결과목록]
                for 원본 in 원본들:
                    폴더 = str(Path(원본).parent)
                    if 폴더 not in 폴더들 and os.path.isdir(폴더):
                        폴더들.append(폴더)
                if not 폴더들:
                    self._알림(messagebox.showwarning, APP_NAME, "원본 폴더를 찾을 수 없습니다.", parent=self.root)
                    return
                if len(폴더들) > 3 and not self._알림(messagebox.askyesno, APP_NAME, f"원본 폴더가 {len(폴더들)}곳입니다. 모두 여시겠습니까?", parent=self.root):
                    return
                for 폴더 in 폴더들:
                    self._경로_열기(폴더)

            def _결과파일_열기(self):
                파일들 = [항목["결과"] for 항목 in self._결과목록 if os.path.isfile(항목["결과"])]
                if not 파일들:
                    self._알림(messagebox.showwarning, APP_NAME, "결과 파일을 찾을 수 없습니다. 옮기거나 지우지 않았는지 확인해 주세요.", parent=self.root)
                    return
                if len(파일들) > 1 and not self._알림(messagebox.askyesno, APP_NAME, f"결과 파일 {len(파일들)}개를 모두 여시겠습니까?", parent=self.root):
                    return
                for 파일 in 파일들:
                    self._경로_열기(파일)

            def _결과_초기화(self, 결과목록도_지우기=True):
                """이전 작업 결과 표시(결과 버튼 비활성화·작업 결과 문구·절약 시간 메시지)를 되돌린다.

                결과목록도_지우기=False면 '재개 대기' 상태(중단된 작업을 실행 버튼으로
                이어서 진행하는 상태)의 완료 기록을 남겨 둔다.
                """
                if 결과목록도_지우기:
                    self._결과목록 = []
                    self._재개_대기중 = False
                    self._재개_시작_인덱스 = 1
                self.open_result_button.config(state="disabled")
                self._원본폴더_버튼_갱신()      # 원본 폴더 버튼은 목록에 문서가 있으면 계속 켜 둔다.
                self.footer_note_var.set(self.FOOTER_NOTE_DEFAULT)
                self.footer_note.configure(style="Hint.TLabel")
                self._단계_초기화()

            def _작업결과_표시(self, 모두_성공):
                """작업이 끝난 뒤: 결과 버튼, '[작업 결과]' 문구, (모두 성공하면) 절약된 시간을 보여 준다."""
                if not self._결과목록:
                    return
                self._원본폴더_버튼_갱신()
                self.open_result_button.config(state="normal")
                이름들 = [Path(항목["결과"]).name for 항목 in self._결과목록]
                문구 = 이름들[0] if len(이름들) == 1 else f"{이름들[0]} 외 {len(이름들) - 1}개"
                self.footer_note_var.set(f"[작업 결과] : {문구}")
                self.footer_note.configure(style="Result.TLabel")
                if 모두_성공:
                    총쪽 = sum(항목["쪽수"] for 항목 in self._결과목록)
                    수작업분 = 총쪽 * 절약시간_쪽당_분.get(self._작업모드, 5.0)
                    걸린분 = (time.monotonic() - (self._작업시작시각 or time.monotonic())) / 60
                    self._절약초 = max(0.0, (수작업분 - 걸린분) * 60)
                    절약 = 절약시간_표시(수작업분 - 걸린분)
                    self.stage_board.set_result_message(f"이번 작업을 통해 절약된 귀하의 시간은 총 {절약} 입니다.")

            # ---- 작업 범위(쪽 지정) ----------------------------------------
            @staticmethod
            def _쪽_표시(n):
                return "마지막쪽" if n == 0 else str(n)

            @staticmethod
            def _쪽_읽기(text):
                """'마지막쪽'·'0'은 0, 숫자는 그 값, 그 밖에는 None."""
                t = str(text).strip()
                if t in ("마지막쪽", "0"):
                    return 0
                try:
                    n = int(t)
                except ValueError:
                    return None
                return n if n >= 1 else None

            @staticmethod
            def _쪽_목록(시작=1):
                """스핀박스 목록: '마지막쪽' 다음에 시작~999. 1의 아래 단계가 '마지막쪽'이다."""
                return ["마지막쪽"] + [str(i) for i in range(시작, max(시작, 999) + 1)]

            def _범위_끝_설정(self, n):
                """종료쪽을 프로그램이 바꾼다(사용자가 직접 바꾼 것으로 보지 않는다)."""
                self._범위_동기중 = True
                try:
                    self.range_end_var.set(self._쪽_표시(n))
                finally:
                    self._범위_동기중 = False

            def _범위_값목록_갱신(self):
                """종료쪽 선택 범위는 '시작쪽 ~ 마지막쪽'이다."""
                시작 = self._쪽_읽기(self.range_start_var.get())
                if 시작 is None:
                    return
                self.range_end_spin.configure(values=["마지막쪽"] if 시작 == 0 else self._쪽_목록(시작))

            def _범위_시작_변경(self, *args):
                if self._범위_동기중:
                    return
                시작 = self._쪽_읽기(self.range_start_var.get())
                if 시작 is None:
                    return  # 입력 도중(빈 칸 등)에는 종료쪽을 건드리지 않는다.
                self._범위_값목록_갱신()
                끝 = self._쪽_읽기(self.range_end_var.get())
                if not self._범위_끝직접설정:
                    self._범위_끝_설정(시작)            # 종료쪽 기본값 = 시작쪽
                elif 시작 == 0:
                    self._범위_끝_설정(0)               # 시작이 마지막쪽이면 종료도 마지막쪽
                elif 끝 not in (None, 0) and 끝 < 시작:
                    self._범위_끝_설정(시작)            # 종료쪽은 시작쪽보다 작을 수 없다.

            def _범위_끝_변경(self, *args):
                if not self._범위_동기중:
                    self._범위_끝직접설정 = True        # 이후로는 사용자가 정한 값을 유지한다.

            def _작업범위_초기화(self):
                """작업 범위를 기본값(문서 전체, 시작쪽·종료쪽 1)으로 되돌린다."""
                self._범위_동기중 = True
                try:
                    self.range_mode_var.set("all")
                    self.page_range_var.set(False)
                    self.range_start_var.set("1")
                    self.range_end_var.set("1")
                finally:
                    self._범위_동기중 = False
                self._범위_끝직접설정 = False
                if self.page_range_details.winfo_manager() == "pack":
                    self.page_range_details.pack_forget()
                self._범위_값목록_갱신()
                self._범위_상태_갱신()

            def _작업범위_읽기(self):
                """실행할 때마다 작업 범위를 확인한다.

                반환: (성공 여부, 값). 값은 None=문서 전체, (시작쪽, 종료쪽)=쪽 지정이며 0은 '마지막쪽'이다.
                """
                if self.range_mode_var.get() != "pages":
                    return True, None
                시작 = self._쪽_읽기(self.range_start_var.get())
                if 시작 is None:
                    self._알림(messagebox.showwarning, APP_NAME, "시작쪽은 ‘마지막쪽’ 또는 1 이상의 숫자로 입력해 주세요.", parent=self.root)
                    return False, None
                끝_원문 = str(self.range_end_var.get()).strip()
                if not 끝_원문:
                    끝 = 시작                           # 종료쪽 기본값은 시작쪽
                else:
                    끝 = self._쪽_읽기(끝_원문)
                    if 끝 is None:
                        self._알림(messagebox.showwarning, APP_NAME, "종료쪽은 ‘마지막쪽’ 또는 1 이상의 숫자로 입력해 주세요.", parent=self.root)
                        return False, None
                if 시작 == 0 and 끝 != 0:
                    self._알림(messagebox.showwarning, APP_NAME, "시작쪽이 ‘마지막쪽’이면 종료쪽도 ‘마지막쪽’이어야 합니다.", parent=self.root)
                    return False, None
                if 시작 != 0 and 끝 != 0 and 끝 < 시작:
                    self._알림(messagebox.showwarning, APP_NAME, "종료쪽은 시작쪽보다 작을 수 없습니다.", parent=self.root)
                    return False, None
                # 화면 표시를 확인한 값으로 정리한다(예: 0 → 마지막쪽, 빈 칸 → 시작쪽).
                self._범위_동기중 = True
                try:
                    self.range_start_var.set(self._쪽_표시(시작))
                    self.range_end_var.set(self._쪽_표시(끝))
                finally:
                    self._범위_동기중 = False
                return True, (시작, 끝)

            def _빠른설정(self, name):
                if self.running:
                    return
                # 현재 체크 상태를 명시적으로 대체하는 사용자 선택 작업이다.
                self.stdformat_var.set(True)
                if name == "indent":
                    for var in self.std_bool_vars.values():
                        var.set(False)
                    self.std_bool_vars["std_hanging_indent"].set(True)
                    self.paren_shrink_var.set(False)
                    self.paren_label_bold_var.set(False)
                    self.keep_punctuation_set_var.set(False)
                else:
                    for key, var in self.std_bool_vars.items():
                        var.set(기본_설정[key])
                    self.std_bool_vars["std_hanging_indent"].set(True)
                    self.paren_shrink_var.set(True)
                    self.paren_label_bold_var.set(True)
                    self.keep_punctuation_set_var.set(True)
                self.selected_mode.set(self._한번에_모드())
                if self._안내단계 == 2:
                    self._안내_설정(3)
                self._표준서식_하위옵션_상태_갱신()
                self._설정_변경됨()
                self.status_var.set("내어쓰기 옵션을 선택했어요. 설정창을 닫고 실행하세요." if name == "indent" else "보고서 기본 옵션을 선택했어요. 설정창을 닫고 실행하세요.")

            def _폴더선택(self):
                if self.running:
                    return
                folder = askdirectory(parent=self.root, title="한글 문서가 있는 폴더 선택 (현재 폴더의 파일만 추가)")
                if folder:
                    added = self.폴더추가(folder)
                    self.status_var.set(f"{added}개 추가 · 총 {len(self.files)}개 문서")

            def _선택삭제(self):
                if self.running:
                    return
                for index in reversed(self.file_list.curselection()):
                    del self.files[index]
                    self.file_list.delete(index)
                self.file_count.configure(text=f"{len(self.files)}개 문서")
                self._실행버튼_상태("normal" if self.files else "disabled")
                self._원본폴더_버튼_갱신()
                self._재개_대기중 = False     # 목록이 바뀌면 이전 중단 지점은 더 이상 유효하지 않음
                if not self.files:
                    self._안내_설정(1)     # 목록이 비면 다시 문서 추가부터 안내

            def _기록토글(self):
                self._log_visible = not self._log_visible
                if self._log_visible:
                    self.log_window.deiconify()
                    self.log_window.lift()
                else:
                    self.log_window.withdraw()
                self.log_toggle.configure(text="처리 기록 닫기" if self._log_visible else "▸ 처리 기록 보기")

            def _기록닫기(self):
                self._log_visible = False
                self.log_window.withdraw()
                self.log_toggle.configure(text="▸ 처리 기록 보기")

            def _프로파일_전역반영(self, profile):
                global 표준서식_설정
                global 표_헤더서식_헤더_폰트, 표_헤더서식_헤더_크기, 표_헤더서식_헤더_굵게
                global 표_헤더서식_본문_폰트, 표_헤더서식_본문_크기, 표_헤더서식_본문_굵게
                global 활성_정밀표_프로필, 활성_서식표_프로필, 활성_표서식_프로필
                서식_기본값_전역_복원()
                표준서식_설정 = copy.deepcopy(profile["format"])
                table = profile.get("table_format", {})
                표_헤더서식_헤더_폰트 = table.get("header_font", 표_헤더서식_헤더_폰트)
                표_헤더서식_헤더_크기 = table.get("header_size", 표_헤더서식_헤더_크기)
                표_헤더서식_헤더_굵게 = table.get("header_bold", 표_헤더서식_헤더_굵게)
                표_헤더서식_본문_폰트 = table.get("body_font", 표_헤더서식_본문_폰트)
                표_헤더서식_본문_크기 = table.get("body_size", 표_헤더서식_본문_크기)
                표_헤더서식_본문_굵게 = table.get("body_bold", 표_헤더서식_본문_굵게)
                활성_정밀표_프로필 = copy.deepcopy(profile.get("precise_tables"))
                활성_서식표_프로필 = copy.deepcopy(profile.get("form_tables")) or None
                활성_표서식_프로필 = copy.deepcopy(profile.get("table_style")) or None
                globals()["활성_머리서식_프로필"] = copy.deepcopy(profile.get("report_header")) or None
                global 괄호_축소_pt
                괄호_축소_pt = float(profile["format"].get("괄호_축소_pt", 2) or 2)
                글꼴형식_등록(profile["format"].get("글꼴형식"))

            def _프로파일_목록갱신(self):
                # 기본 서식을 맨 앞에 두고 기관별로 묶어 이름순으로 보인다(A3).
                ids = [k for k in self._프로파일들 if k]
                ids.sort(key=lambda k: (str(self._프로파일들[k].get("organization") or "￿"), self._프로파일들[k]["name"]))
                self._프로파일_ids = ([""] if "" in self._프로파일들 else []) + ids
                이름들 = [서식프로파일_표시이름(self._프로파일들[k]) for k in self._프로파일_ids]
                현재 = self._프로파일_ids.index(self._활성_서식_프로파일)
                for 콤보이름 in self._프로파일_콤보_이름목록:
                    콤보 = getattr(self, 콤보이름, None)
                    if 콤보 is not None:
                        콤보["values"] = 이름들
                        콤보.current(현재)
                삭제버튼 = getattr(self, "delete_format_button", None)
                if 삭제버튼 is not None:
                    삭제버튼.config(state="normal" if self._활성_서식_프로파일 else "disabled")
                수정버튼 = getattr(self, "edit_format_button", None)
                if 수정버튼 is not None:
                    수정버튼.config(state="normal")

            def _프로파일_선택(self, event=None):
                if self.running: return
                콤보 = event.widget if event is not None and isinstance(event.widget, ttk.Combobox) else self.profile_combo
                self._활성_서식_프로파일 = self._프로파일_ids[콤보.current()]
                profile = self._프로파일들[self._활성_서식_프로파일]
                self._프로파일_전역반영(profile)
                options = profile["options"]
                for key, var in {**self.std_bool_vars, **self.std_parspace_vars}.items():
                    var.set(options.get(key, 기본_설정[key]))
                self.paren_shrink_var.set(options.get("paren_shrink", True))
                self.paren_label_bold_var.set(options.get("paren_label_bold", True))
                for symbol, values in options.get("symbol_fonts", {}).items():
                    if symbol in self.symbol_font_vars:
                        self.symbol_font_vars[symbol]["font"].set(str(values.get("font", "")))
                        self.symbol_font_vars[symbol]["size"].set(str(values.get("size", "")))
                self.table_font_vars["header"]["font"].set(str(표_헤더서식_헤더_폰트))
                self.table_font_vars["header"]["size"].set(str(표_헤더서식_헤더_크기))
                self.table_font_vars["body"]["font"].set(str(표_헤더서식_본문_폰트))
                self.table_font_vars["body"]["size"].set(str(표_헤더서식_본문_크기))
                for key, var in self.label_symbol_vars.items():
                    var.set(options.get("label_symbols", 기본_설정["label_symbols"]).get(key, True))
                self._설정_변경됨()
                self._프로파일_목록갱신()
                self._표준서식_하위옵션_상태_갱신()
                삭제버튼 = getattr(self, "delete_format_button", None)
                if 삭제버튼 is not None:
                    삭제버튼.config(state="normal" if self._활성_서식_프로파일 else "disabled")

            def _서식_이름바꾸기(self):
                """저장된 서식의 이름을 언제든 바꾼다(TODO 6순위). 기본 서식은 바꾸지 않는다."""
                if self.running:
                    return
                parent = self.settings_toplevel if self.settings_toplevel and self.settings_toplevel.winfo_viewable() else self.root
                identifier = self._활성_서식_프로파일
                if not identifier:
                    self._알림(messagebox.showinfo, APP_NAME, "기본 문서 서식은 이름을 바꿀 수 없습니다.", parent=parent)
                    return
                profile = self._프로파일들[identifier]
                새이름 = simpledialog.askstring(APP_NAME, "서식 이름", parent=parent, initialvalue=profile["name"])
                if 새이름 is None:
                    return
                새이름 = 새이름.strip()
                if not 새이름:
                    self._알림(messagebox.showwarning, APP_NAME, "비어 있지 않은 이름을 입력해 주세요.", parent=parent)
                    return
                if any(p["name"] == 새이름 for k, p in self._프로파일들.items() if k != identifier):
                    self._알림(messagebox.showwarning, APP_NAME, "이미 사용 중인 서식 이름입니다.", parent=parent)
                    return
                새기관 = simpledialog.askstring(APP_NAME, "기관 이름(선택, 비워 두면 기관 없음)", parent=parent,
                                              initialvalue=str(profile.get("organization") or ""))
                if 새기관 is None:
                    return
                오류 = self._서식_이름_저장(identifier, 새이름, 새기관)
                if 오류:
                    self._알림(messagebox.showerror, APP_NAME, 오류, parent=parent)

            def _웹화면_모드(self):
                """웹 화면(WebView)이 주 화면이라 Tk 기본 창이 숨겨져 있는지."""
                try:
                    return bool(getattr(self.root, "_docfit_hidden_backend", False) or self.root.state() == "withdrawn")
                except tk.TclError:
                    return False

            def _서식창_부모(self):
                """서식 관리 대화상자의 부모 창: 열린 설정창, 없으면 기본 창."""
                if self.settings_toplevel and self.settings_toplevel.winfo_exists() and self.settings_toplevel.winfo_viewable():
                    return self.settings_toplevel
                return self.root

            def _서식_파일_저장(self, identifier, profile):
                folder = 서식프로파일_폴더()
                folder.mkdir(parents=True, exist_ok=True)
                temp = folder / (identifier + ".tmp")
                temp.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
                os.replace(temp, folder / (identifier + ".json"))

            def _서식_이름_저장(self, identifier, 이름, 기관=''):
                """서식 이름(과 기관)을 바꿔 저장한다. 성공하면 None, 아니면 사용자에게 보일 오류 문구."""
                if self.running:
                    return "작업 중에는 서식을 바꿀 수 없습니다."
                if not identifier or identifier not in self._프로파일들:
                    return "기본 문서 서식은 이름을 바꿀 수 없습니다."
                이름, 기관 = str(이름 or "").strip(), str(기관 or "").strip()
                if not 이름:
                    return "비어 있지 않은 이름을 입력해 주세요."
                if any(p["name"] == 이름 for k, p in self._프로파일들.items() if k != identifier):
                    return "이미 사용 중인 서식 이름입니다."
                바뀐 = dict(self._프로파일들[identifier], name=이름)
                if 기관:
                    바뀐["organization"] = 기관
                else:
                    바뀐.pop("organization", None)
                예전예시, 정보경로 = self._서식예시_경로(identifier)
                try:
                    self._서식_파일_저장(identifier, 바뀐)
                except Exception as exc:
                    return f"서식 이름 저장 실패: {exc}"
                self._프로파일들[identifier] = 바뀐
                if 알파_서식예시폴더_사용 and 예전예시.is_file():
                    새예시 = 예전예시.with_name(서식예시모듈.file_name_for(이름))
                    try:
                        if 새예시 != 예전예시 and not 새예시.exists():
                            예전예시.rename(새예시)
                            정보 = _json_파일_읽기(정보경로)
                            정보["file"] = 새예시.name
                            정보경로.write_text(json.dumps(정보, ensure_ascii=False, indent=2), encoding="utf-8")
                    except Exception as exc:
                        self.로그표시(f"서식예시 파일 이름을 바꾸지 못했습니다(서식은 바꿈): {exc}")
                self._프로파일_목록갱신()
                self.status_var.set(f"서식 이름을 '{이름}'(으)로 바꿨습니다.")
                return None

            def _서식_삭제(self, identifier):
                """서식을 삭제한다(확인은 부른 쪽이 한다). 쓰던 서식이면 기본 서식으로 돌린다. 성공하면 None."""
                if self.running:
                    return "작업 중에는 서식을 바꿀 수 없습니다."
                if not identifier or identifier not in self._프로파일들:
                    return "기본 문서 서식은 삭제할 수 없습니다."
                이름 = self._프로파일들[identifier].get("name") or identifier
                try:
                    경로 = 서식프로파일_폴더() / (identifier + ".json")
                    if 경로.is_file():
                        경로.unlink()
                    예시경로, 정보경로 = self._서식예시_경로(identifier)
                    for 예시 in (예시경로, 정보경로, self._서식예시_원본사본(정보경로),
                                 self._서식예시_썸네일경로(정보경로)):   # 보관한 서식 예시·썸네일도 함께 지운다
                        if 예시.is_file():
                            예시.unlink()
                except Exception as exc:
                    return f"서식 삭제 실패: {exc}"
                self._프로파일들.pop(identifier, None)
                if self._활성_서식_프로파일 == identifier:
                    self._활성_서식_프로파일 = ""
                    self._프로파일_목록갱신()
                    self._프로파일_선택()
                else:
                    self._프로파일_목록갱신()
                self.status_var.set(f"'{이름}' 서식을 삭제했습니다.")
                return None

            def _서식예시_경로(self, identifier):
                """서식마다 하나씩 보관하는 예시 파일과 그 정보 파일의 경로.

                알파(서식예시 폴더): 예시 파일은 C:\\HWP_AUTODOCFIT\\서식예시\\<서식 이름>.hwpx(기본 서식은 '기본 서식.hwpx'),
                정보 파일은 설정 폴더 format_examples에 서식 식별자로 둔다. 끄면 둘 다 설정 폴더에 식별자로 둔다(예전 방식)."""
                이름 = re.sub(r'[\/:*?"<>|\s]+', "_", identifier or "").strip("_") or "_기본"
                if not 알파_서식예시폴더_사용:
                    폴더 = 서식예시_폴더()
                    return 폴더 / f"서식예시_{이름}.hwpx", 폴더 / f"서식예시_{이름}.json"
                정보경로 = 서식예시_정보_폴더() / f"서식예시_{이름}.json"
                파일 = _json_파일_읽기(정보경로).get("file")
                if not 파일:
                    profile = (getattr(self, "_프로파일들", None) or {}).get(identifier) or {}
                    파일 = 서식예시모듈.file_name_for(profile.get("name") or "", standard=not identifier)
                return 서식예시_폴더() / 파일, 정보경로

            def _서식예시_원본사본(self, 정보경로):
                """사용자가 고치기 전 예시 파일의 사본(바뀐 값을 가려내는 비교 기준)."""
                return Path(정보경로).with_suffix(".원본.hwpx")

            def _서식예시_기록(self, 예시경로, 정보경로, 정보):
                """지금 예시 파일을 비교 기준으로 삼는다: 원본 사본을 새로 두고 해시·파일 이름을 기록한다."""
                정보경로 = Path(정보경로)
                정보경로.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(예시경로, self._서식예시_원본사본(정보경로))
                정보 = dict(정보, file=Path(예시경로).name, sha256=서식예시모듈.digest(예시경로),
                          기록때=f"{_datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
                정보경로.write_text(json.dumps(정보, ensure_ascii=False, indent=2), encoding="utf-8")
                return 정보

            def _서식예시_원본_보관(self, identifier, 표본):
                """새로 추가한 서식의 예시 문서(분석한 HWPX)를 서식예시 폴더에 넣는다. 같은 이름 파일이 있으면 번호를 붙인다."""
                try:
                    예시경로, 정보경로 = self._서식예시_경로(identifier)
                    후보, 순번 = 예시경로, 2
                    while 후보.exists():
                        후보 = 예시경로.with_name(f"{예시경로.stem} ({순번}).hwpx")
                        순번 += 1
                    후보.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(표본, 후보)
                    self._서식예시_기록(후보, 정보경로, {"kind": "source", "식별자": identifier})
                    self.로그표시(f"서식예시 폴더에 예시 문서를 넣었습니다: {후보}")
                    if 서식예시모듈.still_cut(후보, 40) is None:
                        self._썸네일_만들기_시작([identifier])
                except Exception as exc:
                    self.로그표시(f"서식예시 폴더에 예시 문서를 넣지 못했습니다(서식은 저장함): {exc}")

            def _서식예시_폴더_준비(self):
                """앱을 켤 때 서식예시 폴더를 만들고, 예전 설정 폴더의 예시를 옮기고, 기본 서식 예시가 없으면 넣는다.

                기본 서식 예시 파일을 사용자가 지웠으면 고친 기본 서식(formats/_standard.json)도 지워 처음 기본 서식으로 되돌린다."""
                if not 알파_서식예시폴더_사용:
                    return
                try:
                    서식예시_폴더().mkdir(parents=True, exist_ok=True)
                except Exception as exc:
                    self.로그표시(f"서식예시 폴더를 만들지 못했습니다: {서식예시_폴더()} ({exc})")
                    return
                for 식별자 in list(self._프로파일들):
                    예시경로, 정보경로 = self._서식예시_경로(식별자)
                    예전 = 서식예시_정보_폴더() / 정보경로.with_suffix(".hwpx").name
                    if 예전 == 예시경로 or 예시경로.exists() or not 예전.is_file():
                        continue
                    try:
                        shutil.copyfile(예전, 예시경로)
                        self._서식예시_기록(예시경로, 정보경로, dict(_json_파일_읽기(정보경로), kind="generated"))
                        예전.unlink()
                    except Exception as exc:
                        self.로그표시(f"예전 서식 예시를 옮기지 못했습니다: {예전.name} ({exc})")
                예시경로, 정보경로 = self._서식예시_경로("")
                if 예시경로.is_file():
                    return
                덮어쓰기 = 서식프로파일_폴더() / f"{기본서식_덮어쓰기_식별자}.json"
                try:
                    if 덮어쓰기.is_file():
                        덮어쓰기.unlink()
                        self._프로파일들[""] = 기본_서식프로파일()
                        if not self._활성_서식_프로파일:
                            self._프로파일_전역반영(self._프로파일들[""])
                        self.로그표시("기본 서식 예시 파일이 없어 기본 서식을 처음 값으로 되돌렸습니다.")
                    for 옛 in (정보경로, self._서식예시_원본사본(정보경로)):
                        if 옛.is_file():
                            옛.unlink()
                    번들 = 번들_서식예시_찾기()
                    if 번들 is not None:
                        shutil.copyfile(번들, 예시경로)
                        self._서식예시_기록(예시경로, 정보경로, {"kind": "bundled", "식별자": ""})
                except Exception as exc:
                    self.로그표시(f"기본 서식 예시를 넣지 못했습니다: {exc}")

            def _서식_스틸컷(self, identifier, width=240, fmt='PNG'):
                """서식의 예시 파일(서식예시 폴더) 첫 쪽 그림. 예시 파일 안 미리보기 그림이 없으면 한/글로 만들어 둔 썸네일
                (예시 파일이 바뀌지 않았을 때만). 둘 다 없으면 None."""
                if not 알파_서식예시폴더_사용:
                    return None
                예시경로, 정보경로 = self._서식예시_경로(identifier)
                if not 예시경로.is_file():
                    return None
                그림 = 서식예시모듈.still_cut(예시경로, width, fmt)
                if 그림 is None and self._썸네일_최신인가(예시경로, 정보경로):
                    그림 = 서식예시모듈.image_cut(self._서식예시_썸네일경로(정보경로), width, fmt)
                return 그림

            def _서식예시_썸네일경로(self, 정보경로):
                return Path(정보경로).with_suffix(".thumb.png")

            def _썸네일_최신인가(self, 예시경로, 정보경로):
                그림 = self._서식예시_썸네일경로(정보경로)
                return 그림.is_file() and _json_파일_읽기(정보경로).get("thumb_sha") == 서식예시모듈.digest(예시경로)

            def _썸네일_필요한_서식(self):
                """예시 파일은 있는데 미리보기 그림도, 최신 썸네일도 없는 서식 식별자 목록."""
                필요 = []
                for identifier in list(getattr(self, "_프로파일_ids", []) or []):
                    예시경로, 정보경로 = self._서식예시_경로(identifier)
                    if (예시경로.is_file() and 서식예시모듈.still_cut(예시경로, 40) is None
                            and not self._썸네일_최신인가(예시경로, 정보경로)):
                        필요.append(identifier)
                return 필요

            def _썸네일_만들기_시작(self, 식별자들, 끝나면=None):
                """미리보기 그림이 없는 예시의 첫 쪽 썸네일을 백그라운드에서 한/글로 만든다(작업 중이거나 이미 만드는 중이면 안 함)."""
                if not 식별자들 or self.running or getattr(self, "_썸네일_만드는중", None):
                    return False
                대상 = []
                for identifier in 식별자들:
                    예시경로, 정보경로 = self._서식예시_경로(identifier)
                    대상.append((identifier, 예시경로, 정보경로))
                self._썸네일_만드는중 = set(식별자들)
                결과 = {"끝": False, "만듦": 0, "오류": []}

                def 만들기():
                    for identifier, 예시경로, 정보경로 in 대상:
                        try:
                            sha = 서식예시모듈.digest(예시경로)
                            첫쪽_그림_만들기(예시경로, self._서식예시_썸네일경로(정보경로))
                            정보 = _json_파일_읽기(정보경로)
                            정보["thumb_sha"] = sha
                            Path(정보경로).parent.mkdir(parents=True, exist_ok=True)
                            Path(정보경로).write_text(json.dumps(정보, ensure_ascii=False, indent=2), encoding="utf-8")
                            결과["만듦"] += 1
                        except Exception as exc:
                            결과["오류"].append(f"{Path(예시경로).name}: {exc}")
                    결과["끝"] = True

                # 작업 스레드에서는 Tk를 부르지 않고 화면 스레드가 끝났는지 살핀다.
                def 살피기():
                    if not 결과["끝"]:
                        self.root.after(300, 살피기)
                        return
                    self._썸네일_만드는중 = None
                    if 결과["만듦"]:
                        self.로그표시(f"썸네일: 미리보기 그림이 없는 예시 {결과['만듦']}개의 첫 쪽 그림을 한/글로 만들었습니다.")
                    for 오류 in 결과["오류"]:
                        self.로그표시(f"썸네일을 만들지 못했습니다(글 카드로 보임): {오류}")
                    if 끝나면 is not None:
                        끝나면()

                threading.Thread(target=만들기, daemon=True).start()
                self.root.after(300, 살피기)
                return True

            def _서식_키오스크_고르기(self, identifier):
                """키오스크 카드에서 고른 서식을 실행창 서식 선택과 같은 경로로 반영한다. 반영하면 True."""
                ids = list(getattr(self, "_프로파일_ids", []) or [])
                콤보 = getattr(self, "main_profile_combo", None)
                if self.running or identifier not in ids or 콤보 is None:
                    return False
                콤보.current(ids.index(identifier))
                self._프로파일_선택(type("콤보선택", (), {"widget": 콤보})())
                이름 = (self._프로파일들.get(identifier) or {}).get("name") or "기본 서식"
                self.status_var.set(f"'{이름}' 서식을 골랐습니다.")
                return True

            def _서식_키오스크_열기(self):
                """키오스크에서 메뉴 사진을 보며 고르듯, 서식마다 예시 첫 쪽 그림(스틸컷)과 이름을 카드로 늘어놓고 눌러 고르게 한다.

                그림은 서식예시 폴더의 예시 HWPX 안 미리보기(Preview/PrvImage.png)를 쓴다(한/글을 열지 않음).
                예시 파일이 아직 없는 서식은 글 카드로 보이고, '서식 예시 확인'으로 예시를 만들면 그림이 생긴다."""
                if self.running:
                    self.status_var.set("작업이 끝난 뒤 서식을 골라 주세요.")
                    return
                이전 = getattr(self, "_서식_키오스크_창", None)
                if 이전 is not None:
                    try:
                        if 이전.winfo_exists():
                            이전.destroy()
                    except Exception:
                        pass
                창 = tk.Toplevel(self.root)
                self._서식_키오스크_창 = 창
                창.title("서식 고르기")
                창.geometry("960x720")
                창.transient(self.root)
                창_맨앞으로(창)
                ttk.Label(창, text="서식 고르기", font=("맑은 고딕", 14, "bold")).pack(anchor="w", padx=14, pady=(12, 0))
                ttk.Label(창, text="예시 보고서 첫 쪽 그림을 보고 원하는 서식 카드를 누르세요. 누르면 바로 그 서식으로 바뀝니다.",
                          style="Hint.TLabel").pack(anchor="w", padx=14, pady=(2, 8))
                틀 = ttk.Frame(창)
                틀.pack(fill="both", expand=True, padx=10)
                캔버스 = tk.Canvas(틀, highlightthickness=0, bg="#F3F6FB")
                막대 = ttk.Scrollbar(틀, orient="vertical", command=캔버스.yview)
                캔버스.configure(yscrollcommand=막대.set)
                막대.pack(side="right", fill="y")
                캔버스.pack(side="left", fill="both", expand=True)
                안쪽 = tk.Frame(캔버스, bg="#F3F6FB")
                캔버스.create_window((0, 0), window=안쪽, anchor="nw")
                안쪽.bind("<Configure>", lambda e: 캔버스.configure(scrollregion=캔버스.bbox("all")))
                창.bind("<MouseWheel>", lambda e: 캔버스.yview_scroll(int(-e.delta / 120), "units"))
                self._키오스크_그림들 = []
                활성 = self._활성_서식_프로파일 or ""

                def 고르기(identifier):
                    if self._서식_키오스크_고르기(identifier):
                        창.destroy()

                for 번호, identifier in enumerate(list(getattr(self, "_프로파일_ids", []) or [])):
                    profile = self._프로파일들.get(identifier) or {}
                    이름 = str(profile.get("name") or "기본 서식")
                    기관 = str(profile.get("organization") or "").strip()
                    고름 = identifier == 활성
                    카드 = tk.Frame(안쪽, bg="#FFFFFF", highlightthickness=3,
                                  highlightbackground="#2563EB" if 고름 else "#D5DCE8", cursor="hand2")
                    카드.grid(row=번호 // 3, column=번호 % 3, padx=10, pady=10, sticky="n")
                    그림자료 = self._서식_스틸컷(identifier, 260)
                    if 그림자료:
                        그림 = tk.PhotoImage(data=base64.b64encode(그림자료).decode("ascii"))
                        self._키오스크_그림들.append(그림)
                        그림칸 = tk.Label(카드, image=그림, bg="#FFFFFF", cursor="hand2")
                    elif identifier in (getattr(self, "_썸네일_만드는중", None) or ()):
                        그림칸 = tk.Label(카드, text="썸네일 만드는 중…\n\n예시 문서의 첫 쪽을\n그림으로 만들고 있어요",
                                       width=26, height=20, wraplength=220, bg="#EEF2F7", fg="#1E3A8A", cursor="hand2")
                    else:
                        그림칸 = tk.Label(카드, text="예시 그림 없음\n\n'서식 예시 확인'을 누르면\n예시를 만들어 그림이 생겨요",
                                       width=26, height=20, wraplength=220, bg="#EEF2F7", fg="#5B6475", cursor="hand2")
                    그림칸.pack(padx=6, pady=(6, 2))
                    제목 = tk.Label(카드, text=("✔ " if 고름 else "") + 이름 + (f"\n{기관}" if 기관 else ""),
                                  font=("맑은 고딕", 11, "bold"), bg="#FFFFFF", fg="#1E3A8A" if 고름 else "#111827",
                                  wraplength=250, cursor="hand2")
                    제목.pack(padx=6, pady=(0, 8))
                    for 위젯 in (카드, 그림칸, 제목):
                        위젯.bind("<Button-1>", lambda e, i=identifier: 고르기(i))
                아래 = ttk.Frame(창)
                아래.pack(fill="x", padx=14, pady=10)
                ttk.Button(아래, text="닫기", command=창.destroy).pack(side="right")

                def 다시그리기():
                    지금창 = getattr(self, "_서식_키오스크_창", None)
                    try:
                        if 지금창 is not None and 지금창.winfo_exists():
                            self._서식_키오스크_열기()
                    except tk.TclError:
                        pass
                # 미리보기 그림이 없는 예시(한/글 2018 저장본 등)는 한/글로 첫 쪽 썸네일을 만들어 다 되면 창을 다시 그린다.
                if self._썸네일_만들기_시작(self._썸네일_필요한_서식(), 다시그리기):
                    self.status_var.set("미리보기 그림이 없는 서식의 썸네일을 만드는 중입니다(서식마다 처음 한 번).")
                    다시그리기_필요 = True
                else:
                    다시그리기_필요 = False
                if 다시그리기_필요:
                    창.after(50, 다시그리기)
                ttk.Button(아래, text="서식예시 폴더 열기", command=self._서식예시_폴더_열기).pack(side="right", padx=6)

            def _서식예시_폴더_열기(self):
                """서식예시 폴더를 탐색기로 연다(사용자가 예시 파일을 직접 고칠 수 있게)."""
                self._서식예시_폴더_준비()
                폴더 = 서식예시_폴더()
                try:
                    폴더.mkdir(parents=True, exist_ok=True)
                    os.startfile(str(폴더))
                    self.status_var.set(f"서식예시 폴더를 열었습니다: {폴더}  (예시 파일을 고쳐 저장하면 '한 번에 적용' 때 반영됩니다)")
                except Exception as exc:
                    self.status_var.set(f"서식예시 폴더를 열지 못했습니다: {exc}")

            def _서식예시_동기화(self, identifier=None):
                """고른 서식의 예시 파일이 사용자에 의해 바뀌었으면 바뀐 서식 값을 서식 설정에 옮긴다.

                (옮긴 값 경로 목록, 로그 문장)을 돌려준다. 바뀌지 않았으면 ([], None). 예시 파일을 읽지 못하면 설정은 그대로 둔다."""
                if not 알파_서식예시폴더_사용:
                    return [], None
                identifier = self._활성_서식_프로파일 if identifier is None else identifier
                profile = self._프로파일들.get(identifier)
                if profile is None:
                    return [], None
                예시경로, 정보경로 = self._서식예시_경로(identifier)
                정보 = _json_파일_읽기(정보경로)
                지금 = 서식예시모듈.digest(예시경로)
                if 지금 is None or 지금 == 정보.get("sha256"):
                    return [], None
                이름 = profile.get("name") or "기본 서식"
                원본사본 = self._서식예시_원본사본(정보경로)
                if not 원본사본.is_file():
                    self._서식예시_기록(예시경로, 정보경로, dict(정보, kind=정보.get("kind") or "user"))
                    return [], f"서식예시 '{예시경로.name}'를 '{이름}' 서식의 비교 기준으로 기록했습니다."
                try:
                    기준 = 서식예시모듈.snapshot(hwpx_서식_분석(원본사본))
                    새값 = 서식예시모듈.snapshot(hwpx_서식_분석(예시경로))
                except Exception as exc:
                    return [], f"서식예시 '{예시경로.name}'를 읽지 못해 서식 설정을 바꾸지 않았습니다: {exc}"
                바뀐 = copy.deepcopy(profile)
                옮김 = 서식예시모듈.merge_changes(바뀐, 기준, 새값)
                if 옮김:
                    self._서식_파일_저장(identifier or 기본서식_덮어쓰기_식별자, 바뀐)
                    self._프로파일들[identifier] = 바뀐
                    if identifier == self._활성_서식_프로파일:
                        self._프로파일_전역반영(바뀐)
                        if hasattr(self, "std_bool_vars"):
                            self._프로파일_선택()
                self._서식예시_기록(예시경로, 정보경로, 정보)
                if not 옮김:
                    return [], f"서식예시 '{예시경로.name}'가 바뀌었지만 서식 값은 그대로입니다(글 내용만 바뀜)."
                return 옮김, (f"서식예시 '{예시경로.name}'에서 바뀐 서식 {len(옮김)}개를 '{이름}' 서식에 반영했습니다: "
                             f"{서식예시모듈.describe(옮김)}")

            def _서식예시_확인(self):
                """지금 고른 서식을 예시 보고서에 입혀 한/글로 보여 준다('서식 예시 확인', 2026-10-04 사용자 요청).

                서식마다 예시 파일을 하나씩 만들어 보관하고(설정 폴더 format_examples), 다시 확인할 때는 그 파일을 바로 연다.
                서식 값·예시 글·앱 판이 바뀌어 보관한 예시가 지금 서식과 다르면(서식예시_서명) 새로 만든다.
                새로 만들 때는 예시 글(서식예시_글)을 독립 한/글 세션에서 HWPX로 만든 뒤 '한 번에 적용'(서식 + 자간 정리, 서식예시_작업모드) 작업으로 처리한다.
                정리할 문서 목록과 이전 결과 목록은 바꾸지 않는다.
                """
                if self.running or getattr(self, "_서식예시_준비중", False) or getattr(self, "_서식분석중", False):
                    self.status_var.set("지금 하는 작업이 끝난 뒤 서식 예시를 확인해 주세요.")
                    return
                identifier = self._활성_서식_프로파일 or ""
                profile = self._프로파일들.get(identifier) or {}
                이름 = str(profile.get("name") or "기본 서식")
                서명 = 서식예시_서명(profile)
                예시경로, 정보경로 = self._서식예시_경로(identifier)
                try:
                    정보 = json.loads(정보경로.read_text(encoding="utf-8")) if 정보경로.is_file() else {}
                except Exception:
                    정보 = {}
                if 알파_서식예시폴더_사용 and 예시경로.is_file() and (
                        정보.get("kind") in ("source", "bundled", "user")
                        or (정보.get("sha256") and 서식예시모듈.digest(예시경로) != 정보.get("sha256"))):
                    # 사용자가 넣은 예시 문서·기본 서식 예시·사용자가 고친 예시는 새로 만들어 덮어쓰지 않고 그대로 연다.
                    self.로그표시(f"서식 예시 확인: 서식예시 폴더의 '{예시경로.name}'를 엽니다 — {예시경로}")
                    self.status_var.set(f"'{이름}' 서식 예시를 한/글로 열었습니다(고쳐 저장하면 '한 번에 적용' 때 반영).")
                    self._경로_열기(str(예시경로))
                    return
                if 예시경로.is_file() and 정보.get("서명") == 서명:
                    self.로그표시(f"서식 예시 확인: 보관한 '{이름}' 서식 예시를 엽니다 — {예시경로}")
                    self.status_var.set(f"'{이름}' 서식 예시를 한/글로 열었습니다.")
                    self._경로_열기(str(예시경로))
                    return
                안전이름 = re.sub(r'[\/:*?"<>|\s]+', "_", 이름).strip("_")[:40] or "서식"
                폴더 = (Path(tempfile.gettempdir()) / "HwpAutoDocFit_서식예시"
                        / f"{안전이름}_{_datetime.datetime.now():%Y%m%d-%H%M%S}")
                폴더.mkdir(parents=True, exist_ok=True)
                원본 = 폴더 / f"서식예시_{안전이름}.hwpx"
                self._서식예시_준비중 = True
                self.status_var.set(f"'{이름}' 서식 예시를 만드는 중입니다(처음 한 번만 1분쯤 걸려요)…")
                self.로그표시(f"서식 예시 확인: '{이름}' 서식을 예시 보고서에 입혀 보관합니다.")
                결과 = {}

                def 만들기():
                    try:
                        텍스트_hwpx_단독변환(서식예시_글, 원본, 라벨_해석=False)
                    except Exception as exc:
                        결과["오류"] = str(exc) or type(exc).__name__
                    결과["끝"] = True

                # 작업 스레드에서는 Tk를 부르지 않고, 화면 스레드가 끝났는지 살핀다(스레드에서 부른 after는 실행되지 않을 수 있다).
                def 살피기():
                    if not 결과.get("끝"):
                        self.root.after(200, 살피기)
                        return
                    self._서식예시_시작(원본, {"이름": 이름, "식별자": identifier, "서명": 서명,
                                            "예시경로": 예시경로, "정보경로": 정보경로}, 결과.get("오류"))

                threading.Thread(target=만들기, daemon=True).start()
                self.root.after(200, 살피기)

            def _서식예시_시작(self, 원본, 예시, 오류):
                """만든 예시 문서를 '한 번에 적용'(서식 + 자간 정리)으로 처리한다(정리할 문서 목록은 그대로 두고 예시 문서만 넘긴다)."""
                self._서식예시_준비중 = False
                if 오류 or not Path(원본).is_file():
                    self.status_var.set(f"서식 예시 문서를 만들지 못했습니다: {오류 or '파일 없음'}")
                    return
                if self.running:
                    self.status_var.set("다른 작업이 시작되어 서식 예시 확인을 취소했습니다.")
                    return
                이전파일 = list(self.files)
                self._서식예시_작업 = dict(예시, 결과목록=list(self._결과목록))
                self._재개_대기중 = False
                self.files = [str(원본)]
                try:
                    self.작업시작(서식예시_작업모드)
                finally:
                    self.files = 이전파일
                if not self.running:
                    self._서식예시_작업 = None

            def _서식예시_완료(self, item, 중단=False):
                """예시 작업이 끝나면 결과를 서식 예시로 보관해 열고, 작업 상태와 이전 결과 목록을 되돌린다."""
                작업 = self._서식예시_작업
                self._서식예시_작업 = None
                self.running = False
                self._안내_설정(0)
                self.버튼_대기중()
                결과 = [r.get("결과") for r in self._결과목록 if r.get("결과")]
                self.stage_board.finish("중단" if 중단 else ("완료" if 결과 else "오류"))
                self._결과목록 = 작업["결과목록"]
                self.open_result_button.config(state="normal" if self._결과목록 else "disabled")
                if 중단 or not 결과:
                    self.status_var.set("서식 예시를 만들지 못했습니다. 작업 로그를 확인해 주세요.")
                    return
                경로 = Path(결과[-1])
                try:
                    예시경로 = Path(작업["예시경로"])
                    예시경로.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(경로, 예시경로)
                    정보 = {"서명": 작업["서명"], "이름": 작업["이름"], "식별자": 작업["식별자"], "앱판": APP_VERSION,
                          "만든때": f"{_datetime.datetime.now():%Y-%m-%d %H:%M:%S}"}
                    if 알파_서식예시폴더_사용:
                        self._서식예시_기록(예시경로, 작업["정보경로"], dict(정보, kind="generated"))
                    else:
                        Path(작업["정보경로"]).write_text(json.dumps(정보, ensure_ascii=False, indent=2), encoding="utf-8")
                    경로 = 예시경로
                except Exception as exc:
                    self.로그표시(f"서식 예시를 보관하지 못했습니다(이번 결과만 엽니다): {exc}")
                self.로그표시(f"서식 예시 확인: {경로}")
                if self.autoclose_var.get():
                    self.status_var.set(f"'{작업['이름']}' 서식 예시를 한/글로 열었습니다.")
                    self._경로_열기(str(경로))
                else:
                    self.status_var.set(f"'{작업['이름']}' 서식 예시를 한/글 창에서 확인해 주세요(보관: {경로.name}).")


            def _서식_파일에서_추가(self):
                """예시 HWP/HWPX 파일을 골라 서식을 복제한다(이름은 분석 뒤 세부사항 창에서 고친다)."""
                if self.running or getattr(self, "_서식분석중", False):
                    return
                path = askopenfilename(parent=self._서식창_부모(), title="서식을 복제할 예시 보고서",
                                       filetypes=[("한글파일", "*.hwp *.hwpx")])
                if path:
                    self._서식_분석_시작(path, 이름묻기=False)

            def _서식_예시편집_시작(self):
                """빈 한/글 문서를 열어 사용자가 예시 문서를 직접 쓰게 하고, '분석 시작'을
                누르면 그 문서를 분석해 새 서식으로 등록한다(TODO 6순위)."""
                if self.running or getattr(self, "_서식분석중", False):
                    return
                기존창 = getattr(self, "_예시편집_창", None)
                if 기존창 is not None and 기존창.winfo_exists():
                    기존창.lift()
                    return
                parent = self.settings_toplevel if self.settings_toplevel and self.settings_toplevel.winfo_viewable() else self.root
                try:
                    pythoncom.CoInitialize()
                    보안모듈_초기화()
                    app = 한글_COM_인스턴스_생성(독립=True)
                    if not app.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE):
                        raise RuntimeError("한글 보안 모듈을 등록하지 못했습니다.")
                    app.XHwpWindows.Item(0).Visible = True
                except Exception as exc:
                    self._알림(messagebox.showerror, APP_NAME, f"한글을 열지 못했습니다.\n{exc}", parent=parent)
                    return
                self._예시편집_hwp = app
                창 = tk.Toplevel(parent)
                self._예시편집_창 = 창
                창.title("서식 예시 문서 편집")
                창.attributes("-topmost", True)
                창.resizable(False, False)
                ttk.Label(창, text="열린 한/글 창에서 예시 문서를 작성하세요.", font=("맑은 고딕", 11, "bold")).pack(
                    anchor="w", padx=14, pady=(12, 2))
                ttk.Label(창, text="□·ㅇ·-·※ 같은 항목기호를 섞어 원하는 계층 구조로 쓰면, 기호별로 가장 많이 쓴 "
                                  "글꼴·크기·들여쓰기가 그 기호의 서식이 됩니다. 다 쓰면 '분석 시작'을 누르세요.\n"
                                  "서식 이름은 첫 문장의 앞 8글자로 정하며 나중에 '이름 바꾸기…'로 고칠 수 있습니다.",
                          style="Hint.TLabel", wraplength=420, justify="left").pack(anchor="w", padx=14)
                안내 = tk.StringVar(value="")
                ttk.Label(창, textvariable=안내, foreground="#b03030", wraplength=420).pack(anchor="w", padx=14, pady=(6, 0))
                버튼줄 = ttk.Frame(창)
                버튼줄.pack(fill="x", padx=14, pady=12)

                def 한글닫기():
                    한글 = getattr(self, "_예시편집_hwp", None)
                    self._예시편집_hwp = None
                    if 한글 is not None:
                        try:
                            한글.Clear(1)
                            한글.Quit()
                        except Exception:
                            pass

                def 취소():
                    한글닫기()
                    창.destroy()
                    self._예시편집_창 = None

                def 분석시작():
                    한글 = self._예시편집_hwp
                    if 한글 is None:
                        return
                    임시 = Path(tempfile.mkdtemp(prefix="docfit_example_")) / "예시.hwpx"
                    try:
                        if 한글.SaveAs(str(임시), "HWPX", "") is False:
                            raise RuntimeError("예시 문서를 임시 파일로 저장하지 못했습니다.")
                        문단들 = [b.text for b in inspect_hwpx(임시).blocks if b.type == "paragraph"]
                    except Exception as exc:
                        안내.set(f"예시 문서를 읽지 못했습니다: {exc}")
                        return
                    if not any(leading_marker(t)[0] for t in 문단들):
                        안내.set("항목기호(□·ㅇ·-·※ 등)로 시작하는 문단이 없습니다. 기호를 붙인 문단을 한두 개 이상 써 주세요.")
                        return
                    이름 = 예시문서_기본이름(문단들)
                    한글닫기()
                    창.destroy()
                    self._예시편집_창 = None
                    self._서식_분석_시작(str(임시), 이름묻기=False, 기본이름=이름)

                ttk.Button(버튼줄, text="분석 시작", command=분석시작).pack(side="left")
                ttk.Button(버튼줄, text="취소", command=취소).pack(side="right")
                창.protocol("WM_DELETE_WINDOW", 취소)

            def _서식_삭제하기(self):
                if self.running:
                    return
                if not self._활성_서식_프로파일:
                    self._알림(messagebox.showinfo, APP_NAME, "기본 문서 서식은 삭제할 수 없습니다.", parent=self.settings_toplevel)
                    return
                profile = self._프로파일들.get(self._활성_서식_프로파일)
                이름 = profile["name"] if profile else self._활성_서식_프로파일
                if not self._알림(messagebox.askyesno,
                    APP_NAME, f"'{이름}' 서식을 삭제하시겠습니까?\n삭제하면 되돌릴 수 없습니다.",
                    parent=self.settings_toplevel
                ):
                    return
                오류 = self._서식_삭제(self._활성_서식_프로파일)
                if 오류:
                    self._알림(messagebox.showerror, APP_NAME, 오류, parent=self.settings_toplevel)

            def _서식_수정하기(self, identifier=None):
                """서식의 세부값을 고친다(identifier가 없으면 지금 쓰는 서식). 기본 서식을 고치면 새 서식으로 저장한다."""
                if self.running:
                    return
                if identifier is None:
                    identifier = self._활성_서식_프로파일
                if identifier not in self._프로파일들:
                    return
                parent = self._서식창_부모()
                profile = copy.deepcopy(self._프로파일들[identifier])
                if not identifier:
                    profile["name"] = "기본 보고서 서식 (사용자 수정)"
                if profile.get("element_analysis"):
                    다른이름 = {p["name"] for k, p in self._프로파일들.items() if k != identifier}
                    if not self._서식_세부사항_확인(profile, parent, 다른이름):
                        return
                elif not self._서식_구조_확인(profile, parent):
                    return
                try:
                    if not identifier:
                        identifier = uuid.uuid4().hex
                    self._서식_파일_저장(identifier, profile)
                except Exception as exc:
                    self.status_var.set(f"서식 수정 저장 실패: {exc}")
                    if not self._웹화면_모드():
                        self._알림(messagebox.showerror, APP_NAME, f"서식 수정 저장 실패\n{exc}", parent=parent)
                    return
                self._프로파일들[identifier] = profile
                self._활성_서식_프로파일 = identifier
                self._프로파일_목록갱신()
                self._프로파일_선택()
                self.status_var.set(f"'{profile['name']}' 서식을 수정했습니다.")

            def _문서검토_열기(self):
                """원본을 변경하지 않는 구조·표현 검토 결과와 계층별 훑어보기를 표시한다."""
                if self.running or getattr(self, "_서식분석중", False):
                    return
                existing = getattr(self, "_문서검토_창", None)
                if existing is not None and existing.winfo_exists():
                    existing.lift()
                    return
                source = self._고급도구_대상()
                if source is None:
                    self._알림(messagebox.showinfo, APP_NAME, "먼저 검토할 HWP/HWPX 파일을 추가해 주세요.", parent=self.root)
                    return
                window = tk.Toplevel(self.root)
                self._문서검토_창 = window
                window.title("문서 구조·가독성 검토 · 읽기 전용")
                window.geometry("1120x740")
                window.transient(self.root)
                body = ttk.Frame(window, padding=12)
                body.pack(fill="both", expand=True)
                ttk.Label(body, text=f"검토 문서: {source.name}", font=("맑은 고딕", 13, "bold")).pack(anchor="w")
                ttk.Label(body, text="원본을 수정하거나 외부로 전송하지 않습니다. 의미 판단은 사용자가 확인해 주세요.",
                          style="Hint.TLabel").pack(anchor="w", pady=(2, 8))
                options = ttk.Frame(body)
                options.pack(fill="x", pady=(0, 8))
                saved = 설정_불러오기()
                kind = tk.StringVar(value=saved.get("review_document_kind", "보고서"))
                purpose = tk.StringVar(value=saved.get("review_reading_purpose", "상세 설명용"))
                if kind.get() not in DOCUMENT_KINDS: kind.set("보고서")
                if purpose.get() not in PURPOSES: purpose.set("상세 설명용")
                ttk.Label(options, text="문서 유형").pack(side="left")
                ttk.Combobox(options, textvariable=kind, values=DOCUMENT_KINDS, state="readonly", width=12).pack(side="left", padx=(5, 15))
                ttk.Label(options, text="읽기 목적").pack(side="left")
                ttk.Combobox(options, textvariable=purpose, values=PURPOSES, state="readonly", width=17).pack(side="left", padx=5)
                status = tk.StringVar(value="검토를 시작하세요.")
                start_button = ttk.Button(options, text="검토 시작")
                start_button.pack(side="right")
                result_box = {"value": None}
                def export_result():
                    if result_box["value"] is None:
                        return
                    path = asksaveasfilename(parent=window, title="검토 결과 저장",
                                             initialfile=source.stem + "(문서검토).json",
                                             defaultextension=".json", filetypes=[("JSON", "*.json")])
                    if not path:
                        return
                    try:
                        Path(path).write_text(json.dumps(result_box["value"], ensure_ascii=False, indent=2), encoding="utf-8")
                        status.set(f"검토 결과 저장: {path}")
                    except OSError as exc:
                        self._알림(messagebox.showerror, APP_NAME, f"검토 결과를 저장하지 못했습니다.\n{exc}", parent=window)
                export_button = ttk.Button(options, text="결과 JSON 저장…", command=export_result, state="disabled")
                export_button.pack(side="right", padx=(0, 6))
                notebook = ttk.Notebook(body)
                notebook.pack(fill="both", expand=True)
                issue_frame = ttk.Frame(notebook, padding=4)
                outline_frame = ttk.Frame(notebook, padding=4)
                notebook.add(issue_frame, text="검토 후보")
                notebook.add(outline_frame, text="계층 훑어보기")
                columns = ("severity", "category", "location", "message", "context")
                issue_tree = ttk.Treeview(issue_frame, columns=columns, show="headings", selectmode="browse")
                for key, title, width in zip(columns, ("구분", "항목", "위치", "확인할 내용", "원문"),
                                             (90, 140, 135, 385, 290)):
                    issue_tree.heading(key, text=title)
                    issue_tree.column(key, width=width, anchor="w")
                issue_scroll = ttk.Scrollbar(issue_frame, orient="vertical", command=issue_tree.yview)
                issue_tree.configure(yscrollcommand=issue_scroll.set)
                issue_tree.pack(side="left", fill="both", expand=True)
                issue_scroll.pack(side="right", fill="y")
                outline = ttk.Treeview(outline_frame, columns=("location", "role", "text"), show="headings")
                for key, title, width in (("location", "위치", 145), ("role", "계층", 100), ("text", "내용", 780)):
                    outline.heading(key, text=title)
                    outline.column(key, width=width, anchor="w")
                outline_scroll = ttk.Scrollbar(outline_frame, orient="vertical", command=outline.yview)
                outline.configure(yscrollcommand=outline_scroll.set)
                outline.pack(side="left", fill="both", expand=True)
                outline_scroll.pack(side="right", fill="y")
                ttk.Label(body, textvariable=status, style="Hint.TLabel").pack(anchor="w", pady=(8, 0))

                def completed(result=None, error=None):
                    if not window.winfo_exists():
                        return
                    start_button.config(state="normal")
                    if error:
                        status.set("검토 실패")
                        self._알림(messagebox.showerror, APP_NAME, f"문서 검토에 실패했습니다.\n{error}", parent=window)
                        return
                    result_box["value"] = result
                    export_button.config(state="normal")
                    issue_tree.delete(*issue_tree.get_children())
                    outline.delete(*outline.get_children())
                    for item in result["issues"]:
                        issue_tree.insert("", "end", values=(item["severity"], item["category"],
                                          item["location"], item["message"], item["context"]))
                    for item in result["outline"]:
                        outline.insert("", "end", values=(item["location"], item["role"], item["text"]))
                    status.set(f"본문 {result['body_count']}개 · 표 셀 문단 {result['cell_count']}개 · "
                               f"검토 후보 {len(result['issues'])}건 · 원문은 변경되지 않았습니다.")

                def start():
                    start_button.config(state="disabled")
                    status.set("문서 구조와 서식을 분석하고 있습니다…")
                    settings = 설정_불러오기()
                    settings.update(review_document_kind=kind.get(), review_reading_purpose=purpose.get())
                    self.review_document_kind, self.review_reading_purpose = kind.get(), purpose.get()
                    설정_저장(settings)
                    profile = copy.deepcopy(self._프로파일들.get(self._활성_서식_프로파일))
                    selected_kind, selected_purpose = kind.get(), purpose.get()
                    def worker():
                        try:
                            with tempfile.TemporaryDirectory(prefix="docfit_review_") as folder:
                                snapshot = 교정용_hwpx_준비(source, folder)
                                result = review_document(snapshot, profile, selected_purpose, selected_kind)
                            gui_queue.put(("document_review_done", completed, result, None))
                        except Exception as exc:
                            gui_queue.put(("document_review_done", completed, None, str(exc)))
                    threading.Thread(target=worker, daemon=True, name="document-review").start()

                start_button.config(command=start)
                start()

            @staticmethod
            def _아웃라인_깊이(줄):
                """한 줄의 계층 깊이와 본문을 읽는다.

                저장 형식: 0단계는 "# 본문"(들여쓰기 없음), N단계(N≥1)는
                ((N-1)*2)칸 들여쓰기 + "- 본문". 이 형식은 outline_pasted_text가
                그대로 읽어 0단계→ㅁ, 1→ㅇ, 2→-, 3단계 이후는 모두 •로 바꾼다.
                """
                본문시작 = 줄.lstrip(" ")
                들여쓰기 = len(줄) - len(본문시작)
                if 본문시작.startswith("# "):
                    return 0, 본문시작[2:]
                if 본문시작.startswith("- "):
                    return (들여쓰기 // 2) + 1, 본문시작[2:]
                return 0, 본문시작

            @staticmethod
            def _아웃라인_접두(깊이, 본문):
                if 깊이 <= 0:
                    return f"# {본문}"
                return " " * ((깊이 - 1) * 2) + f"- {본문}"

            def _아웃라이너_열기(self):
                """워크플로위류 아웃라이너로 새 글을 쓴다.

                Tab/Shift+Tab으로 계층을 넣고 빼며, 저장 형식 자체가 계층 구조를
                그대로 담은 마크다운이다(0단계 "# ", 그 아래는 "- "를 들여쓰기
                깊이만큼 겹쳐 표시). '개조식 텍스트로 추가'는 이 마크다운을
                outline_pasted_text로 ㅁ/ㅇ/-/• 공문서 항목기호로 바꿔 문서
                목록에 추가하고, '마크다운으로 추가'는 원본 그대로 추가해
                고급 문서 엔진(kordoc)이 있을 때 서식을 살려 변환하게 한다.

                1.68 Alpha 6(TODO 5순위): 접기/펼치기(Ctrl+↑/↓), 확대(Alt+→/←),
                항목 이동(Alt+Shift+↑/↓), 완료 표시(Ctrl+Enter, "[x] "), 메모
                (Shift+Enter, "> "), 검색 걸러 보기(Ctrl+F), 저장·열기(Ctrl+S/O)와
                닫을 때 자동 저장한 글을 다음에 이어 쓰기. 줄 계산은
                docfit_core.outline_ops의 순수 함수가 맡는다.
                """
                if self.running:
                    return
                existing = getattr(self, "_아웃라이너_창", None)
                if existing is not None and existing.winfo_exists():
                    existing.lift()
                    return
                window = tk.Toplevel(self.root)
                self._아웃라이너_창 = window
                window.title("아웃라이너로 새 글 작성")
                window.geometry("1020x660")
                window.minsize(680, 440)
                window.transient(self.root)
                임시저장_경로 = Path(설정_파일_경로()).with_name("outliner_draft.md")

                body = ttk.Frame(window, padding=12)
                body.pack(fill="both", expand=True)
                ttk.Label(body, text="워크플로위처럼 항목을 쓰고 Tab/Shift+Tab으로 계층을 넣고 빼세요.",
                          font=("맑은 고딕", 12, "bold")).pack(anchor="w")
                ttk.Label(body,
                          text="Enter: 같은 계층의 새 항목 · Tab/Shift+Tab: 들여쓰기/내어쓰기 · "
                               "Ctrl+↑/↓: 접기/펼치기 · Alt+→/←: 확대/전체 보기 · Alt+Shift+↑/↓: 항목 이동 · "
                               "Ctrl+Enter: 완료 표시 · Shift+Enter: 메모 · Ctrl+F: 검색 · Ctrl+S/O: 저장/열기. "
                               "0단계는 ㅁ, 1단계는 ㅇ, 2단계는 -, 3단계 이후는 •, 메모는 ※로 바뀝니다.",
                          style="Hint.TLabel", wraplength=980, justify="left").pack(anchor="w", pady=(2, 6))

                toolbar = ttk.Frame(body)
                toolbar.pack(fill="x", pady=(0, 6))
                ttk.Label(toolbar, text="검색").pack(side="left")
                search_var = tk.StringVar()
                search_entry = ttk.Entry(toolbar, textvariable=search_var, width=22)
                search_entry.pack(side="left", padx=(4, 10))

                panes = ttk.Frame(body)
                panes.pack(fill="both", expand=True)
                panes.grid_columnconfigure(0, weight=1)
                panes.grid_columnconfigure(1, weight=1)
                panes.grid_rowconfigure(1, weight=1)

                ttk.Label(panes, text="아웃라인").grid(row=0, column=0, sticky="w")
                ttk.Label(panes, text="공문서 개조식 미리보기").grid(row=0, column=1, sticky="w", padx=(8, 0))

                outline_frame = ttk.Frame(panes)
                outline_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
                outline_frame.grid_columnconfigure(0, weight=1)
                outline_frame.grid_rowconfigure(0, weight=1)
                outline_text = tk.Text(outline_frame, wrap="word", undo=True, font=("맑은 고딕", 11))
                outline_text.grid(row=0, column=0, sticky="nsew")
                outline_scroll = ttk.Scrollbar(outline_frame, orient="vertical", command=outline_text.yview)
                outline_scroll.grid(row=0, column=1, sticky="ns")
                outline_text.configure(yscrollcommand=outline_scroll.set)
                # 접기·확대·검색은 줄을 화면에서만 숨긴다(저장 내용은 그대로).
                for 태그 in ("hidden_fold", "hidden_zoom", "hidden_filter"):
                    outline_text.tag_configure(태그, elide=True)
                outline_text.tag_configure("done", overstrike=True, foreground="#8a8a8a")
                outline_text.tag_configure("note", foreground="#6b6b6b", font=("맑은 고딕", 10, "italic"))
                outline_text.tag_configure("folded", background="#eef3fb")
                outline_text.tag_configure("found", background="#fff1a8")

                preview_frame = ttk.Frame(panes)
                preview_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 0))
                preview_frame.grid_columnconfigure(0, weight=1)
                preview_frame.grid_rowconfigure(0, weight=1)
                preview_text = tk.Text(preview_frame, wrap="word", font=("맑은 고딕", 10), background="#f7f7f7")
                preview_text.grid(row=0, column=0, sticky="nsew")
                preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_text.yview)
                preview_scroll.grid(row=0, column=1, sticky="ns")
                preview_text.configure(yscrollcommand=preview_scroll.set)

                status = tk.StringVar(value="항목을 입력하고 Enter로 다음 항목을 이어가세요.")

                def 줄목록():
                    return outline_text.get("1.0", "end-1c").split("\n")

                def 현재줄번호():
                    return int(outline_text.index("insert").split(".")[0]) - 1

                def 줄범위(시작, 끝):
                    return f"{시작 + 1}.0", f"{끝 + 1}.0"

                def 모양_갱신(event=None):
                    줄들 = 줄목록()
                    for 태그 in ("done", "note"):
                        outline_text.tag_remove(태그, "1.0", "end")
                    for i, 줄 in enumerate(줄들):
                        if outline_ops.is_done(줄):
                            outline_text.tag_add("done", f"{i + 1}.0", f"{i + 1}.end")
                        elif outline_ops.parse(줄)[0] == "note":
                            outline_text.tag_add("note", f"{i + 1}.0", f"{i + 1}.end")

                def 숨김_해제():
                    for 태그 in ("hidden_fold", "hidden_zoom", "hidden_filter", "folded", "found"):
                        outline_text.tag_remove(태그, "1.0", "end")

                def 내용_바꾸기(줄들, 커서줄=None, 커서칸="end"):
                    숨김_해제()
                    outline_text.edit_separator()
                    outline_text.delete("1.0", "end")
                    outline_text.insert("1.0", "\n".join(줄들))
                    outline_text.edit_separator()
                    if 커서줄 is not None:
                        outline_text.mark_set("insert", f"{커서줄 + 1}.{커서칸}")
                        outline_text.see("insert")
                    모양_갱신()

                def 현재줄범위():
                    return outline_text.index("insert linestart"), outline_text.index("insert lineend")

                def 이전줄_깊이(줄시작):
                    행 = int(줄시작.split(".")[0])
                    if 행 <= 1:
                        return None
                    return outline_ops.depth(줄목록(), 행 - 2)

                def 엔터처리(event=None):
                    줄시작, 줄끝 = 현재줄범위()
                    전체줄 = outline_text.get(줄시작, 줄끝)
                    if outline_ops.parse(전체줄)[0] == "note":
                        # 메모 줄에서 Enter는 메모가 딸린 항목과 같은 계층의 새 항목을 연다.
                        깊이 = outline_ops.depth(줄목록(), 현재줄번호())
                        새프리픽스 = self._아웃라인_접두(깊이, "")
                        outline_text.insert(줄끝, "\n" + 새프리픽스)
                        outline_text.mark_set("insert", f"{int(줄시작.split('.')[0]) + 1}.{len(새프리픽스)}")
                        return "break"
                    깊이, 본문 = self._아웃라인_깊이(전체줄)
                    프리픽스길이 = len(전체줄) - len(본문)
                    커서컬럼 = int(outline_text.index("insert").split(".")[1])
                    분할지점 = max(프리픽스길이, 커서컬럼)
                    앞부분 = 전체줄[프리픽스길이:분할지점]
                    뒷부분 = 전체줄[분할지점:]
                    outline_text.delete(줄시작, 줄끝)
                    outline_text.insert(줄시작, self._아웃라인_접두(깊이, 앞부분))
                    새프리픽스 = self._아웃라인_접두(깊이, "")
                    outline_text.insert("insert", "\n" + 새프리픽스 + 뒷부분)
                    행 = int(줄시작.split(".")[0]) + 1
                    outline_text.mark_set("insert", f"{행}.{len(새프리픽스)}")
                    return "break"

                def 들여쓰기(event=None):
                    줄시작, 줄끝 = 현재줄범위()
                    전체줄 = outline_text.get(줄시작, 줄끝)
                    if outline_ops.parse(전체줄)[0] == "note":
                        return "break"
                    깊이, 본문 = self._아웃라인_깊이(전체줄)
                    이전깊이 = 이전줄_깊이(줄시작)
                    최대깊이 = 0 if 이전깊이 is None else 이전깊이 + 1
                    새깊이 = min(깊이 + 1, max(최대깊이, 0), 8)
                    if 새깊이 == 깊이:
                        return "break"
                    이전프리픽스길이 = len(전체줄) - len(본문)
                    커서오프셋 = max(0, int(outline_text.index("insert").split(".")[1]) - 이전프리픽스길이)
                    새줄 = self._아웃라인_접두(새깊이, 본문)
                    outline_text.delete(줄시작, 줄끝)
                    outline_text.insert(줄시작, 새줄)
                    새프리픽스길이 = len(새줄) - len(본문)
                    outline_text.mark_set("insert", f"{줄시작.split('.')[0]}.{새프리픽스길이 + 커서오프셋}")
                    return "break"

                def 내어쓰기(event=None):
                    줄시작, 줄끝 = 현재줄범위()
                    전체줄 = outline_text.get(줄시작, 줄끝)
                    if outline_ops.parse(전체줄)[0] == "note":
                        return "break"
                    깊이, 본문 = self._아웃라인_깊이(전체줄)
                    새깊이 = max(깊이 - 1, 0)
                    if 새깊이 == 깊이:
                        return "break"
                    이전프리픽스길이 = len(전체줄) - len(본문)
                    커서오프셋 = max(0, int(outline_text.index("insert").split(".")[1]) - 이전프리픽스길이)
                    새줄 = self._아웃라인_접두(새깊이, 본문)
                    outline_text.delete(줄시작, 줄끝)
                    outline_text.insert(줄시작, 새줄)
                    새프리픽스길이 = len(새줄) - len(본문)
                    outline_text.mark_set("insert", f"{줄시작.split('.')[0]}.{새프리픽스길이 + 커서오프셋}")
                    return "break"

                def 접기(event=None):
                    줄들 = 줄목록()
                    i = outline_ops.item_start(줄들, 현재줄번호())
                    끝 = outline_ops.subtree_end(줄들, i)
                    if 끝 <= i + 1:
                        status.set("접을 하위 항목이 없습니다.")
                        return "break"
                    outline_text.tag_add("hidden_fold", *줄범위(i + 1, 끝))
                    outline_text.tag_add("folded", f"{i + 1}.0", f"{i + 1}.end")
                    outline_text.mark_set("insert", f"{i + 1}.end")
                    status.set(f"접음 · 하위 {끝 - i - 1}줄 (Ctrl+↓로 펼치기)")
                    return "break"

                def 펼치기(event=None):
                    줄들 = 줄목록()
                    i = outline_ops.item_start(줄들, 현재줄번호())
                    끝 = outline_ops.subtree_end(줄들, i)
                    outline_text.tag_remove("hidden_fold", *줄범위(i + 1, 끝))
                    outline_text.tag_remove("folded", f"{i + 1}.0", f"{i + 1}.end")
                    status.set("펼침")
                    return "break"

                def 확대(event=None):
                    줄들 = 줄목록()
                    i = outline_ops.item_start(줄들, 현재줄번호())
                    끝 = outline_ops.subtree_end(줄들, i)
                    outline_text.tag_remove("hidden_zoom", "1.0", "end")
                    if i > 0:
                        outline_text.tag_add("hidden_zoom", "1.0", f"{i + 1}.0")
                    if 끝 < len(줄들):
                        outline_text.tag_add("hidden_zoom", f"{끝}.end", "end")
                    status.set(f"확대: {outline_ops.parse(줄들[i])[2][:30]} (Alt+←로 전체 보기)")
                    return "break"

                def 전체보기(event=None):
                    outline_text.tag_remove("hidden_zoom", "1.0", "end")
                    status.set("전체 보기")
                    return "break"

                def 이동(up):
                    줄들 = 줄목록()
                    결과 = outline_ops.move_block(줄들, 현재줄번호(), up)
                    if 결과 is None:
                        status.set("같은 계층에서 더 옮길 수 없습니다.")
                        return "break"
                    새줄들, 새번호 = 결과
                    내용_바꾸기(새줄들, 새번호)
                    status.set("항목을 옮겼습니다.")
                    return "break"

                def 완료표시(event=None):
                    줄들 = 줄목록()
                    i = outline_ops.item_start(줄들, 현재줄번호())
                    새줄 = outline_ops.toggle_done(줄들[i])
                    if 새줄 != 줄들[i]:
                        outline_text.delete(f"{i + 1}.0", f"{i + 1}.end")
                        outline_text.insert(f"{i + 1}.0", 새줄)
                        모양_갱신()
                        status.set("완료 표시" if outline_ops.is_done(새줄) else "완료 표시 해제")
                    return "break"

                def 메모추가(event=None):
                    줄들 = 줄목록()
                    i = outline_ops.item_start(줄들, 현재줄번호())
                    j = i + 1
                    while j < len(줄들) and outline_ops.parse(줄들[j])[0] == "note":
                        j += 1
                    접두 = outline_ops.note_prefix(줄들[i])
                    outline_text.insert(f"{j}.end", "\n" + 접두)
                    outline_text.mark_set("insert", f"{j + 1}.end")
                    모양_갱신()
                    status.set("메모를 입력하세요(개조식으로 바꿀 때 ※ 부연설명이 됩니다).")
                    return "break"

                def 검색(*args):
                    outline_text.tag_remove("hidden_filter", "1.0", "end")
                    outline_text.tag_remove("found", "1.0", "end")
                    검색어 = search_var.get().strip()
                    if not 검색어:
                        status.set("검색을 지웠습니다.")
                        return
                    줄들 = 줄목록()
                    보일줄 = outline_ops.filter_visible(줄들, 검색어)
                    for i in range(len(줄들)):
                        if i not in 보일줄:
                            outline_text.tag_add("hidden_filter", *줄범위(i, i + 1))
                    시작 = "1.0"
                    while True:
                        위치 = outline_text.search(검색어, 시작, stopindex="end", nocase=True)
                        if not 위치:
                            break
                        끝 = f"{위치}+{len(검색어)}c"
                        outline_text.tag_add("found", 위치, 끝)
                        시작 = 끝
                    status.set(f"검색: '{검색어}' — {len([i for i in 보일줄 if 검색어.lower() in 줄들[i].lower()])}줄 (Esc로 해제)")

                def 검색해제(event=None):
                    search_var.set("")
                    outline_text.focus_set()
                    return "break"

                search_var.trace_add("write", 검색)
                search_entry.bind("<Escape>", 검색해제)
                search_entry.bind("<Return>", lambda e: (outline_text.focus_set(), "break")[1])

                outline_text.bind("<Return>", 엔터처리)
                outline_text.bind("<Tab>", 들여쓰기)
                outline_text.bind("<Shift-Tab>", 내어쓰기)
                outline_text.bind("<ISO_Left_Tab>", 내어쓰기)  # 일부 배치에서 Shift+Tab이 이 키심볼로 옴
                outline_text.bind("<Control-Up>", 접기)
                outline_text.bind("<Control-Down>", 펼치기)
                outline_text.bind("<Alt-Right>", 확대)
                outline_text.bind("<Alt-Left>", 전체보기)
                outline_text.bind("<Alt-Shift-Up>", lambda e: 이동(True))
                outline_text.bind("<Alt-Shift-Down>", lambda e: 이동(False))
                outline_text.bind("<Control-Return>", 완료표시)
                outline_text.bind("<Shift-Return>", 메모추가)
                outline_text.bind("<Escape>", 검색해제)
                outline_text.bind("<KeyRelease>", 모양_갱신)
                for 위젯 in (outline_text, search_entry):
                    위젯.bind("<Control-f>", lambda e: (search_entry.focus_set(), "break")[1])

                def 기본파일명(내용, 확장자):
                    for 줄 in 내용.splitlines():
                        _, 본문 = self._아웃라인_깊이(줄)
                        본문 = 본문.strip()
                        if 본문:
                            안전한줄 = re.sub(r'[\\/:*?"<>|]', " ", 본문).strip()
                            return (안전한줄[:40] or "아웃라이너 글") + 확장자
                    return f"아웃라이너 글{확장자}"

                def 미리보기():
                    원문 = outline_text.get("1.0", "end-1c")
                    if not 원문.strip():
                        status.set("작성한 항목이 없습니다.")
                        return None
                    try:
                        결과 = outline_pasted_text(outline_ops.export_markdown(원문.split("\n")))
                    except Exception as e:
                        self._알림(messagebox.showerror, APP_NAME, f"개조식 변환 중 오류가 발생했습니다.\n\n{e}", parent=window)
                        return None
                    preview_text.delete("1.0", "end")
                    preview_text.insert("1.0", 결과)
                    status.set(f"미리보기 완료 · {len(결과)}자")
                    return 결과

                def 개조식으로추가():
                    결과 = 미리보기()
                    if not 결과:
                        return
                    경로 = asksaveasfilename(
                        parent=window, title="개조식 텍스트를 저장할 위치",
                        initialfile=기본파일명(outline_text.get("1.0", "end-1c"), ".txt"),
                        defaultextension=".txt", filetypes=[("텍스트 파일", "*.txt")],
                    )
                    if not 경로:
                        return
                    try:
                        Path(경로).write_text(결과, encoding="utf-8")
                    except OSError as e:
                        self._알림(messagebox.showerror, APP_NAME, f"파일 저장 중 오류가 발생했습니다.\n\n{e}", parent=window)
                        return
                    if self.파일추가(경로):
                        status.set(f"개조식 문서로 추가했습니다 · {Path(경로).name}")
                        self.status_var.set(f"{len(self.files)}개 문서 선택")
                        self.로그표시(f"아웃라이너 글을 개조식 문서로 추가: {Path(경로).name}")
                    else:
                        status.set("이미 목록에 있는 파일입니다.")

                def 마크다운으로추가():
                    원문 = outline_text.get("1.0", "end-1c")
                    if not 원문.strip():
                        status.set("작성한 항목이 없습니다.")
                        return
                    경로 = asksaveasfilename(
                        parent=window, title="마크다운을 저장할 위치",
                        initialfile=기본파일명(원문, ".md"),
                        defaultextension=".md", filetypes=[("Markdown", "*.md")],
                    )
                    if not 경로:
                        return
                    try:
                        Path(경로).write_text(원문, encoding="utf-8")
                    except OSError as e:
                        self._알림(messagebox.showerror, APP_NAME, f"파일 저장 중 오류가 발생했습니다.\n\n{e}", parent=window)
                        return
                    if self.파일추가(경로):
                        status.set(f"마크다운 문서로 추가했습니다 · {Path(경로).name}")
                        self.status_var.set(f"{len(self.files)}개 문서 선택")
                        self.로그표시(f"아웃라이너 글을 마크다운 문서로 추가: {Path(경로).name}")
                    else:
                        status.set("이미 목록에 있는 파일입니다.")

                def 저장(event=None):
                    원문 = outline_text.get("1.0", "end-1c")
                    경로 = asksaveasfilename(
                        parent=window, title="아웃라인을 저장할 위치(나중에 '열기'로 이어 쓰기)",
                        initialfile=기본파일명(원문, ".md"),
                        defaultextension=".md", filetypes=[("Markdown", "*.md")],
                    )
                    if not 경로:
                        return "break"
                    try:
                        Path(경로).write_text(원문, encoding="utf-8")
                        status.set(f"저장했습니다 · {Path(경로).name}")
                    except OSError as e:
                        self._알림(messagebox.showerror, APP_NAME, f"파일 저장 중 오류가 발생했습니다.\n\n{e}", parent=window)
                    return "break"

                def 열기(event=None):
                    경로 = askopenfilename(parent=window, title="이어 쓸 아웃라인 열기",
                                           filetypes=[("Markdown", "*.md"), ("텍스트 파일", "*.txt")])
                    if not 경로:
                        return "break"
                    try:
                        내용 = Path(경로).read_text(encoding="utf-8-sig")
                    except (OSError, UnicodeDecodeError) as e:
                        self._알림(messagebox.showerror, APP_NAME, f"파일을 열지 못했습니다.\n\n{e}", parent=window)
                        return "break"
                    내용_바꾸기(내용.split("\n"), len(내용.split("\n")) - 1)
                    status.set(f"불러왔습니다 · {Path(경로).name}")
                    return "break"

                def 지우기():
                    숨김_해제()
                    outline_text.delete("1.0", "end")
                    outline_text.insert("1.0", "# ")
                    outline_text.mark_set("insert", "1.2")
                    preview_text.delete("1.0", "end")
                    try:
                        임시저장_경로.unlink()
                    except OSError:
                        pass
                    status.set("항목을 입력하고 Enter로 다음 항목을 이어가세요.")

                def 닫기():
                    # 닫을 때 쓰던 글을 자동 저장해 다음에 창을 열면 이어 쓸 수 있게 한다.
                    원문 = outline_text.get("1.0", "end-1c")
                    try:
                        if 원문.strip() and 원문.strip() != "#":
                            임시저장_경로.write_text(원문, encoding="utf-8")
                        elif 임시저장_경로.exists():
                            임시저장_경로.unlink()
                    except OSError:
                        pass
                    window.destroy()
                    self._아웃라이너_창 = None

                window.protocol("WM_DELETE_WINDOW", 닫기)
                for 위젯 in (outline_text, search_entry):
                    위젯.bind("<Control-s>", 저장)
                    위젯.bind("<Control-o>", 열기)

                for 이름, 명령 in (("접기", 접기), ("펼치기", 펼치기), ("확대", 확대), ("전체 보기", 전체보기),
                                 ("위로", lambda: 이동(True)), ("아래로", lambda: 이동(False)),
                                 ("완료", 완료표시), ("메모", 메모추가), ("열기…", 열기), ("저장…", 저장)):
                    ttk.Button(toolbar, text=이름, command=명령).pack(side="left", padx=(0, 4))

                actions = ttk.Frame(body)
                actions.pack(fill="x", pady=(8, 0))
                ttk.Button(actions, text="미리보기", command=미리보기).pack(side="left")
                ttk.Button(actions, text="개조식 문서로 추가", command=개조식으로추가).pack(side="left", padx=(6, 0))
                ttk.Button(actions, text="마크다운으로 추가", command=마크다운으로추가).pack(side="left", padx=(6, 0))
                ttk.Button(actions, text="지우기", command=지우기).pack(side="left", padx=(6, 0))
                ttk.Button(actions, text="닫기", command=닫기).pack(side="right")
                ttk.Label(body, textvariable=status, style="Hint.TLabel").pack(anchor="w", pady=(6, 0))

                이전글 = ""
                try:
                    if 임시저장_경로.exists():
                        이전글 = 임시저장_경로.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    이전글 = ""
                if 이전글.strip():
                    내용_바꾸기(이전글.split("\n"), len(이전글.split("\n")) - 1)
                    status.set("지난번 작성하던 글을 불러왔습니다(닫을 때 자동 저장). 새로 쓰려면 '지우기'.")
                else:
                    outline_text.insert("1.0", "# ")
                    outline_text.mark_set("insert", "1.2")
                outline_text.focus_set()

            def _텍스트로_문서추가_열기(self):
                """붙여넣은 텍스트를 파일로 저장해 '01 정리할 문서' 목록에 바로 추가한다.

                자동 저장 폴더를 지정해 두면, 저장 즉시 그 폴더에 HWPX로 변환해
                추가한다(배치 작업과 독립된 한/글 세션 사용). 지정하지 않으면
                기존처럼 저장 위치를 직접 골라 .txt로 추가한다.
                """
                if self.running:
                    return
                existing = getattr(self, "_텍스트추가_창", None)
                if existing is not None and existing.winfo_exists():
                    existing.lift()
                    return
                window = tk.Toplevel(self.root)
                self._텍스트추가_창 = window
                window.title("텍스트 붙여넣기로 문서 추가")
                window.geometry("640x520")
                window.minsize(420, 360)
                window.transient(self.root)

                진행중 = {"value": False}

                def closed():
                    self._텍스트추가_창 = None

                def 닫기_요청():
                    if 진행중["value"]:
                        return
                    window.destroy()
                    closed()
                window.protocol("WM_DELETE_WINDOW", 닫기_요청)

                body = ttk.Frame(window, padding=12)
                body.pack(fill="both", expand=True)
                ttk.Label(body, text="추가할 문서 내용을 붙여넣거나 입력하세요.",
                          font=("맑은 고딕", 12, "bold")).pack(anchor="w")
                ttk.Label(body,
                          text="자동 저장 폴더를 지정하면 저장 즉시 그 폴더에 HWPX로 변환해 문서 목록에 추가합니다. "
                               "비워두면 저장 위치를 직접 골라 .txt로 추가합니다.",
                          style="Hint.TLabel", wraplength=600, justify="left").pack(anchor="w", pady=(2, 8))

                folder_row = ttk.Frame(body)
                folder_row.pack(fill="x", pady=(0, 8))
                ttk.Label(folder_row, text="자동 저장 폴더").pack(side="left")
                folder_entry = ttk.Entry(folder_row, textvariable=self.paste_add_folder_var, width=40)
                folder_entry.pack(side="left", padx=(6, 4), fill="x", expand=True)

                def 폴더_찾아보기():
                    시작 = self.paste_add_folder_var.get() or str(Path.home())
                    폴더 = askdirectory(title="자동 저장 폴더 선택", initialdir=시작 if Path(시작).exists() else None,
                                        parent=window)
                    if 폴더:
                        self.paste_add_folder_var.set(폴더)

                ttk.Button(folder_row, text="찾아보기…", command=폴더_찾아보기).pack(side="left", padx=(0, 4))
                ttk.Button(folder_row, text="지정 안 함", command=lambda: self.paste_add_folder_var.set("")).pack(side="left")

                text_frame = ttk.Frame(body)
                text_frame.pack(fill="both", expand=True)
                text_frame.grid_columnconfigure(0, weight=1)
                text_frame.grid_rowconfigure(0, weight=1)
                input_text = tk.Text(text_frame, wrap="word", undo=True, font=("맑은 고딕", 10))
                input_text.grid(row=0, column=0, sticky="nsew")
                scroll = ttk.Scrollbar(text_frame, orient="vertical", command=input_text.yview)
                scroll.grid(row=0, column=1, sticky="ns")
                input_text.configure(yscrollcommand=scroll.set)

                status = tk.StringVar(value="텍스트를 붙여넣고 ‘문서로 추가’를 눌러 주세요.")
                ai_convert_var = tk.BooleanVar(value=알파_AI답변변환_사용)

                def 기본이름(내용):
                    for 줄 in 내용.splitlines():
                        줄 = 줄.strip()
                        if 줄:
                            안전한줄 = re.sub(r'[\\/:*?"<>|]', " ", 줄).strip()
                            return 안전한줄[:40] or "붙여넣은 텍스트"
                    return "붙여넣은 텍스트"

                def 겹치지않는경로(폴더, 이름, 확장자):
                    대상 = Path(폴더) / f"{이름}{확장자}"
                    번호 = 2
                    while 대상.exists():
                        대상 = Path(폴더) / f"{이름} ({번호}){확장자}"
                        번호 += 1
                    return 대상

                추가_버튼 = None
                지우기_버튼 = None
                닫기_버튼 = None

                def 버튼상태(상태):
                    for 위젯 in (추가_버튼, 지우기_버튼, 닫기_버튼, folder_entry):
                        if 위젯 is not None:
                            위젯.config(state=상태)

                def 완료(오류, 대상경로):
                    진행중["value"] = False
                    if not window.winfo_exists():
                        return
                    버튼상태("normal")
                    if 오류:
                        self._알림(messagebox.showerror, APP_NAME, f"HWPX 변환 중 오류가 발생했습니다.\n\n{오류}", parent=window)
                        status.set("HWPX 변환에 실패했습니다.")
                        return
                    if self.파일추가(str(대상경로)):
                        status.set(f"HWPX 문서로 추가했습니다 · {대상경로.name}")
                        self.status_var.set(f"{len(self.files)}개 문서 선택")
                        self.로그표시(f"텍스트를 HWPX 문서로 추가: {대상경로.name}")
                    else:
                        status.set("이미 목록에 있는 파일입니다.")

                def 문서로추가():
                    내용 = input_text.get("1.0", "end-1c")
                    if not 내용.strip():
                        status.set("붙여넣은 텍스트가 없습니다.")
                        return
                    폴더 = self.paste_add_folder_var.get().strip()
                    if 폴더:
                        if not Path(폴더).is_dir():
                            self._알림(messagebox.showerror, APP_NAME, f"자동 저장 폴더를 찾을 수 없습니다.\n\n{폴더}", parent=window)
                            return
                        if self.running:
                            self._알림(messagebox.showinfo, APP_NAME, "다른 작업이 실행 중입니다. 완료 후 다시 시도해 주세요.",
                                                parent=window)
                            return
                        AI변환 = bool(ai_convert_var.get())
                        대상경로 = 겹치지않는경로(폴더, 기본이름(AI답변_개조식_변환(내용)[0] if AI변환 else 내용), ".hwpx")
                        진행중["value"] = True
                        버튼상태("disabled")
                        status.set("HWPX로 변환하는 중입니다… (한/글이 잠시 열립니다)")

                        def 작업():
                            오류 = None
                            try:
                                텍스트_hwpx_단독변환(내용, 대상경로, AI_변환=AI변환)
                            except Exception as e:
                                오류 = str(e)
                            self.root.after(0, 완료, 오류, 대상경로)
                        threading.Thread(target=작업, daemon=True, name="paste-add-hwpx").start()
                        return
                    내용, AI변환됨 = AI답변_개조식_변환(내용) if ai_convert_var.get() else (내용, False)
                    if AI변환됨:
                        status.set("AI 답변으로 보고 개조식 항목기호(□ ㅇ -)로 변환했습니다.")
                    경로 = asksaveasfilename(
                        parent=window, title="텍스트를 저장할 위치",
                        initialfile=기본이름(내용) + ".txt", defaultextension=".txt",
                        filetypes=[("텍스트 파일", "*.txt")],
                    )
                    if not 경로:
                        return
                    try:
                        Path(경로).write_text(내용, encoding="utf-8")
                    except OSError as e:
                        self._알림(messagebox.showerror, APP_NAME, f"파일 저장 중 오류가 발생했습니다.\n\n{e}", parent=window)
                        return
                    if self.파일추가(경로):
                        status.set(f"문서로 추가했습니다 · {Path(경로).name}")
                        self.status_var.set(f"{len(self.files)}개 문서 선택")
                        self.로그표시(f"텍스트를 문서로 추가: {Path(경로).name}")
                    else:
                        status.set("이미 목록에 있는 파일입니다.")

                def 지우기():
                    input_text.delete("1.0", "end")
                    status.set("텍스트를 붙여넣고 ‘문서로 추가’를 눌러 주세요.")

                # 입력칸보다 먼저 아래쪽에 자리를 잡아야 화면 배율이 커도 버튼이 가려지지 않는다.
                status_label = ttk.Label(body, textvariable=status, style="Hint.TLabel")
                status_label.pack(side="bottom", anchor="w", pady=(6, 0), before=text_frame)
                actions = ttk.Frame(body)
                actions.pack(side="bottom", fill="x", pady=(8, 0), before=status_label)
                추가_버튼 = ttk.Button(actions, text="문서로 추가", command=문서로추가)
                추가_버튼.pack(side="left")
                지우기_버튼 = ttk.Button(actions, text="지우기", command=지우기)
                지우기_버튼.pack(side="left", padx=(6, 0))
                닫기_버튼 = ttk.Button(actions, text="닫기", command=닫기_요청)
                닫기_버튼.pack(side="right")
                ttk.Checkbutton(body, text="AI 답변이면 구조를 개조식(제목·개요·□ ㅇ - 항목기호)으로 자동 변환",
                                variable=ai_convert_var).pack(side="bottom", anchor="w", before=text_frame)

                try:
                    붙여넣기 = window.clipboard_get()
                except tk.TclError:
                    붙여넣기 = ""
                if 붙여넣기.strip():
                    input_text.insert("1.0", 붙여넣기)
                input_text.focus_set()

            def _붙여넣기_정리_열기(self):
                """제미나이·클로드·챗GPT 등에서 복사한 답변을 정리한다. 파일을 건드리지 않는다."""
                existing = getattr(self, "_붙여넣기_창", None)
                if existing is not None and existing.winfo_exists():
                    existing.lift()
                    return
                window = tk.Toplevel(self.root)
                self._붙여넣기_창 = window
                window.title("붙여넣은 텍스트 정리")
                window.geometry("900x600")
                window.minsize(560, 380)
                window.transient(self.root)

                def closed():
                    self._붙여넣기_창 = None
                window.protocol("WM_DELETE_WINDOW", lambda: (window.destroy(), closed()))

                body = ttk.Frame(window, padding=12)
                body.pack(fill="both", expand=True)
                ttk.Label(body, text="제미나이·클로드·챗GPT 채팅창에서 복사한 답변을 붙여넣으세요.",
                          font=("맑은 고딕", 12, "bold")).pack(anchor="w")
                ttk.Label(body,
                          text="‘한 번에 정리’는 마크다운 기호(**, #, - 등)를 지우고 보기 좋은 문장으로 바꾸고,\n"
                               "‘개조식으로 변환’은 제목·번호·글머리·들여쓰기·표 구조를 읽어 제목·개요·□/ㅇ/-/• 항목기호로 바꿉니다(AI 답변은 복사한 그대로).\n"
                               "‘제목: / 네모: / 원: / 바:’ 라벨 형식은 라벨 그대로 바꿉니다(‘AI 프롬프트…’로 이 형식의 답을 받을 수 있음).",
                          style="Hint.TLabel", justify="left").pack(anchor="w", pady=(2, 8))

                panes = ttk.Frame(body)
                panes.pack(fill="both", expand=True)
                panes.grid_columnconfigure(0, weight=1)
                panes.grid_columnconfigure(1, weight=1)
                panes.grid_rowconfigure(1, weight=1)

                ttk.Label(panes, text="붙여넣은 텍스트").grid(row=0, column=0, sticky="w")
                ttk.Label(panes, text="정리된 결과").grid(row=0, column=1, sticky="w", padx=(8, 0))

                input_frame = ttk.Frame(panes)
                input_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
                input_frame.grid_columnconfigure(0, weight=1)
                input_frame.grid_rowconfigure(0, weight=1)
                input_text = tk.Text(input_frame, wrap="word", undo=True, font=("맑은 고딕", 10))
                input_text.grid(row=0, column=0, sticky="nsew")
                input_scroll = ttk.Scrollbar(input_frame, orient="vertical", command=input_text.yview)
                input_scroll.grid(row=0, column=1, sticky="ns")
                input_text.configure(yscrollcommand=input_scroll.set)

                output_frame = ttk.Frame(panes)
                output_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 0))
                output_frame.grid_columnconfigure(0, weight=1)
                output_frame.grid_rowconfigure(0, weight=1)
                output_text = tk.Text(output_frame, wrap="word", font=("맑은 고딕", 10), background="#f7f7f7")
                output_text.grid(row=0, column=0, sticky="nsew")
                output_scroll = ttk.Scrollbar(output_frame, orient="vertical", command=output_text.yview)
                output_scroll.grid(row=0, column=1, sticky="ns")
                output_text.configure(yscrollcommand=output_scroll.set)

                status = tk.StringVar(value="텍스트를 붙여넣고 ‘한 번에 정리’를 눌러 주세요.")

                def 변환실행(변환함수, 완료문구):
                    원문 = input_text.get("1.0", "end-1c")
                    if not 원문.strip():
                        status.set("붙여넣은 텍스트가 없습니다.")
                        return
                    try:
                        결과 = 변환함수(원문)
                    except Exception as e:
                        self._알림(messagebox.showerror, APP_NAME, f"텍스트 정리 중 오류가 발생했습니다.\n\n{e}", parent=window)
                        return
                    output_text.delete("1.0", "end")
                    output_text.insert("1.0", 결과)
                    status.set(f"{완료문구} · {len(결과)}자")

                def 정리하기():
                    변환실행(clean_pasted_text, "정리 완료")

                def 개조식으로변환():
                    # 제목:/네모:/원: 같은 라벨 형식이면 계층을 추론하지 않고 라벨대로 바꾼다(A1).
                    원문 = input_text.get("1.0", "end-1c")
                    if looks_labeled(원문):
                        변환실행(label_outline_text, "라벨 형식을 개조식으로 변환 완료")
                    elif 알파_AI답변변환_사용 and looks_like_ai_answer(원문):
                        # 표제·번호 표제·굵은 줄·들여쓰기 목록·표를 읽어 제목·개요·□ ㅇ - • 항목기호로 바꾼다(들여쓰기 칸 수와 무관).
                        변환실행(ai_answer_to_outline_text, "AI 답변 구조를 개조식으로 변환 완료")
                    else:
                        변환실행(outline_pasted_text, "개조식 변환 완료")

                def 결과복사():
                    결과 = output_text.get("1.0", "end-1c")
                    if not 결과.strip():
                        status.set("복사할 정리 결과가 없습니다.")
                        return
                    window.clipboard_clear()
                    window.clipboard_append(결과)
                    status.set("정리된 텍스트를 클립보드에 복사했습니다.")

                def 지우기():
                    input_text.delete("1.0", "end")
                    output_text.delete("1.0", "end")
                    status.set("텍스트를 붙여넣고 ‘한 번에 정리’를 눌러 주세요.")

                actions = ttk.Frame(body)
                actions.pack(fill="x", pady=(8, 0))
                ttk.Button(actions, text="한 번에 정리", command=정리하기).pack(side="left")
                ttk.Button(actions, text="개조식으로 변환", command=개조식으로변환).pack(side="left", padx=(6, 0))
                ttk.Button(actions, text="결과 복사", command=결과복사).pack(side="left", padx=(6, 0))
                ttk.Button(actions, text="AI 프롬프트…", command=lambda: self._AI_프롬프트_열기(window)).pack(side="left", padx=(6, 0))
                ttk.Button(actions, text="지우기", command=지우기).pack(side="left", padx=(6, 0))
                ttk.Button(actions, text="닫기", command=lambda: (window.destroy(), closed())).pack(side="right")
                ttk.Label(body, textvariable=status, style="Hint.TLabel").pack(anchor="w", pady=(6, 0))

                try:
                    붙여넣기 = window.clipboard_get()
                except tk.TclError:
                    붙여넣기 = ""
                if 붙여넣기.strip():
                    input_text.insert("1.0", 붙여넣기)
                input_text.focus_set()

            def _AI_프롬프트_열기(self, parent=None):
                """생성형 AI에게 공문서 초안을 라벨 형식으로 받는 프롬프트를 만들어 복사한다(A2).

                앱은 AI 서비스에 아무것도 보내지 않는다. 프롬프트를 클립보드에 복사하고
                원하면 브라우저로 AI 사이트를 열 뿐이다.
                """
                parent = parent or self.root
                window = tk.Toplevel(parent)
                window.title("AI 프롬프트 만들기")
                window.geometry("860x600")
                window.minsize(620, 420)
                window.transient(parent)
                body = ttk.Frame(window, padding=12)
                body.pack(fill="both", expand=True)
                ttk.Label(body, text="AI에게 공문서 초안을 받는 프롬프트", font=("맑은 고딕", 12, "bold")).pack(anchor="w")
                ttk.Label(body, text="메모를 적고 서식을 고른 뒤 ‘프롬프트 복사’를 누르세요. AI 답변을 ‘붙여넣은 텍스트 정리’나 "
                                     "‘텍스트 붙여넣기’에 넣으면 라벨대로 개조식·제목 상자로 바뀝니다. 앱은 AI에 아무것도 전송하지 않습니다.",
                          style="Hint.TLabel", wraplength=820, justify="left").pack(anchor="w", pady=(2, 8))
                panes = ttk.Frame(body)
                panes.pack(fill="both", expand=True)
                panes.grid_columnconfigure(1, weight=1)
                panes.grid_rowconfigure(1, weight=1)
                panes.grid_rowconfigure(3, weight=2)
                ttk.Label(panes, text="서식").grid(row=0, column=0, sticky="w")
                목록 = ai_prompts.all_prompts()
                listbox = tk.Listbox(panes, exportselection=False, width=24, font=("맑은 고딕", 10))
                for 이름, 설명, _, 라벨 in 목록:
                    listbox.insert("end", 이름 + ("" if 라벨 else "  (문장)"))
                listbox.grid(row=1, column=0, rowspan=3, sticky="nsw", padx=(0, 8))
                ttk.Label(panes, text="메모(업무 내용·일시·장소·대상 등)").grid(row=0, column=1, sticky="w")
                memo = tk.Text(panes, height=6, wrap="word", undo=True, font=("맑은 고딕", 10))
                memo.grid(row=1, column=1, sticky="nsew")
                ttk.Label(panes, text="만들어진 프롬프트").grid(row=2, column=1, sticky="w", pady=(6, 0))
                preview = tk.Text(panes, wrap="word", font=("맑은 고딕", 9), background="#f7f7f7")
                preview.grid(row=3, column=1, sticky="nsew")
                status = tk.StringVar(value="서식을 고르세요.")

                def 갱신(event=None):
                    선택 = listbox.curselection()
                    if not 선택:
                        return
                    이름 = 목록[선택[0]][0]
                    preview.delete("1.0", "end")
                    preview.insert("1.0", ai_prompts.build_prompt(이름, memo.get("1.0", "end-1c")))
                    status.set(f"{이름} · {목록[선택[0]][1]}")

                def 복사():
                    갱신()
                    내용 = preview.get("1.0", "end-1c")
                    if not 내용.strip():
                        status.set("먼저 서식을 고르세요.")
                        return
                    window.clipboard_clear()
                    window.clipboard_append(내용)
                    status.set("프롬프트를 복사했습니다. AI 채팅창에 붙여넣으세요.")

                def 사이트열기(주소):
                    복사()
                    import webbrowser
                    webbrowser.open(주소)

                listbox.bind("<<ListboxSelect>>", 갱신)
                memo.bind("<KeyRelease>", 갱신)
                actions = ttk.Frame(body)
                actions.pack(fill="x", pady=(8, 0))
                ttk.Button(actions, text="프롬프트 복사", command=복사).pack(side="left")
                for 이름, 주소 in ai_prompts.AI_SITES.items():
                    ttk.Button(actions, text=f"복사 후 {이름} 열기", command=lambda u=주소: 사이트열기(u)).pack(side="left", padx=(6, 0))
                ttk.Button(actions, text="닫기", command=window.destroy).pack(side="right")
                ttk.Label(body, textvariable=status, style="Hint.TLabel").pack(anchor="w", pady=(6, 0))
                listbox.selection_set(0)
                갱신()
                memo.focus_set()

            def _작성도우미_열기(self):
                """금액·날짜·표 계산·나이·번호·회신공문·기관 서식 도구(B1~B6, A5, A3).

                문서 파일을 직접 바꾸지 않는다. 붙여넣은 텍스트에 적용한 결과를 복사해 쓰게 한다.
                """
                existing = getattr(self, "_작성도우미_창", None)
                if existing is not None and existing.winfo_exists():
                    existing.lift()
                    return
                window = tk.Toplevel(self.root)
                self._작성도우미_창 = window
                window.title("작성 도우미")
                window.geometry("900x640")
                window.minsize(640, 480)
                window.transient(self.root)

                def 닫기():
                    window.destroy()
                    self._작성도우미_창 = None
                window.protocol("WM_DELETE_WINDOW", 닫기)
                body = ttk.Frame(window, padding=10)
                body.pack(fill="both", expand=True)
                notebook = ttk.Notebook(body)
                notebook.pack(fill="both", expand=True)
                self._작성도우미_탭 = notebook
                status = tk.StringVar(value="탭을 고르고 텍스트를 붙여넣은 뒤 버튼을 누르세요. 결과는 오른쪽에 나옵니다.")
                self._작성도우미_입출력 = {}

                def 입출력탭(제목, 안내, 버튼들, 위쪽=None):
                    """왼쪽 입력·오른쪽 결과 텍스트와 변환 버튼 줄로 된 공통 탭."""
                    tab = ttk.Frame(notebook, padding=8)
                    notebook.add(tab, text=제목)
                    ttk.Label(tab, text=안내, style="Hint.TLabel", wraplength=840, justify="left").pack(anchor="w")
                    if 위쪽:
                        위쪽(tab)
                    panes = ttk.Frame(tab)
                    panes.pack(fill="both", expand=True, pady=(6, 0))
                    panes.grid_columnconfigure(0, weight=1)
                    panes.grid_columnconfigure(1, weight=1)
                    panes.grid_rowconfigure(0, weight=1)
                    src = tk.Text(panes, wrap="word", undo=True, font=("맑은 고딕", 10))
                    src.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
                    dst = tk.Text(panes, wrap="word", font=("맑은 고딕", 10), background="#f7f7f7")
                    dst.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
                    row = ttk.Frame(tab)
                    row.pack(fill="x", pady=(6, 0))

                    def 실행(함수, 이름):
                        try:
                            결과 = 함수(src.get("1.0", "end-1c"))
                        except Exception as exc:
                            self._알림(messagebox.showerror, APP_NAME, f"{이름} 중 오류가 발생했습니다.\n\n{exc}", parent=window)
                            return
                        dst.delete("1.0", "end")
                        dst.insert("1.0", 결과)
                        status.set(f"{이름} 완료")

                    def 복사():
                        내용 = dst.get("1.0", "end-1c")
                        if 내용.strip():
                            window.clipboard_clear()
                            window.clipboard_append(내용)
                            status.set("결과를 복사했습니다.")

                    명령 = {}
                    for 이름, 함수 in 버튼들:
                        명령[이름] = lambda f=함수, n=이름: 실행(f, n)
                        ttk.Button(row, text=이름, command=명령[이름]).pack(side="left", padx=(0, 6))
                    ttk.Button(row, text="결과 복사", command=복사).pack(side="right")
                    self._작성도우미_입출력[제목] = (src, dst, 명령)
                    return src, dst

                wa = writing_aids

                # B1·B4 금액·숫자
                입출력탭("금액·숫자",
                         "금액(예: 1,500,000원)에 한글 금액을 병기하거나 천 단위 쉼표·단위를 바꿉니다.",
                         [("한글 금액 병기", wa.hangulize_amounts),
                          ("쉼표 넣기", wa.add_commas), ("쉼표 빼기", wa.remove_commas),
                          ("원 → 천원(÷1,000)", lambda t: wa.scale_numbers(t, "0.001")),
                          ("천원 → 원(×1,000)", lambda t: wa.scale_numbers(t, 1000)),
                          ("숫자만 한글로", lambda t: re.sub(r"\d{1,3}(?:,\d{3})+|\d+",
                                                             lambda m: wa.number_to_hangul(int(m.group(0).replace(",", ""))), t))])

                # B2 날짜
                날짜형식 = tk.StringVar(value="full")

                def 날짜옵션(tab):
                    box = ttk.Frame(tab)
                    box.pack(anchor="w", pady=(4, 0))
                    ttk.Label(box, text="표기").pack(side="left")
                    for 값, 이름 in (("full", "2025. 7. 25.(금)"), ("short", "’25. 7. 25.(금)"), ("plain", "2025. 7. 25.")):
                        ttk.Radiobutton(box, text=이름, value=값, variable=날짜형식).pack(side="left", padx=(6, 0))

                def 기준일(t):
                    return wa.parse_date(t) or _datetime.date.today()

                def 금요일들(t, offset):
                    d = 기준일(t)
                    return "\n".join(wa.format_date(x, 날짜형식.get()) for x in wa.weekdays_in_month(d, 4, offset))

                def 기간(t, kind, offset):
                    d = 기준일(t)
                    if kind == "week":
                        a, b = wa.week_of(d, offset)
                    elif kind == "month":
                        a, b = wa.month_bounds(d, offset)
                    else:
                        a, b = _datetime.date(d.year + offset, 1, 1), _datetime.date(d.year + offset, 12, 31)
                    return wa.date_range_text(a, b, 날짜형식.get())

                def 날짜차이(t):
                    찾은 = [wa.parse_date(m.group(0)) for m in wa._DATE.finditer(t)]
                    찾은 = [x for x in 찾은 if x]
                    if len(찾은) < 2:
                        return "날짜 두 개를 입력하세요. 예: 2025. 7. 1. ~ 2025. 7. 25."
                    a, b = 찾은[:2]
                    return (f"{wa.format_date(a, 날짜형식.get())} ~ {wa.format_date(b, 날짜형식.get())}: "
                            f"{wa.days_between(a, b)}일 차이(양 끝 포함 {wa.days_between(a, b, True)}일)")

                입출력탭("날짜",
                         "문장 속 날짜에 요일을 붙이거나(틀린 요일은 고침), 입력한 날짜(없으면 오늘)를 기준으로 날짜를 만듭니다.",
                         [("요일 붙이기·고치기", wa.add_weekdays),
                          ("오늘", lambda t: wa.format_date(_datetime.date.today(), 날짜형식.get())),
                          ("이번 달 금요일", lambda t: 금요일들(t, 0)), ("다음 달 금요일", lambda t: 금요일들(t, 1)),
                          ("다음 주", lambda t: 기간(t, "week", 1)), ("이번 달 기간", lambda t: 기간(t, "month", 0)),
                          ("다음 달 기간", lambda t: 기간(t, "month", 1)), ("올해 기간", lambda t: 기간(t, "year", 0)),
                          ("날짜 차이", 날짜차이)], 날짜옵션)

                # B3 표 계산
                def 표계산(op):
                    return lambda t: wa.table_to_text(wa.calc_table(wa.parse_table(t), op))
                입출력탭("표 계산",
                         "한/글·엑셀 표를 복사해 붙여넣으세요(칸은 탭 또는 |). 첫 행·첫 열이 글자면 머리글로 보고 계산에서 뺍니다. "
                         "결과를 복사해 한/글 표에 붙여넣으면 됩니다.",
                         [("열 합계", 표계산("col_sum")), ("열 평균", 표계산("col_avg")),
                          ("행 합계", 표계산("row_sum")), ("구성비(%)", 표계산("col_ratio"))])

                # B5 나이·주민번호
                입출력탭("나이·주민번호",
                         "줄마다 생년월일이나 주민등록번호를 찾아 만 나이를 붙입니다. 주민등록번호는 결과에서 뒷자리를 가립니다.",
                         [("만 나이 붙이기", wa.ages_for_lines), ("주민번호 → 생년월일", wa.rrn_to_birth_lines),
                          ("주민번호 가리기", wa.mask_rrn)])

                # B6 번호
                번호형식 = tk.StringVar(value="1.")

                def 번호옵션(tab):
                    box = ttk.Frame(tab)
                    box.pack(anchor="w", pady=(4, 0))
                    ttk.Label(box, text="번호 모양").pack(side="left")
                    ttk.Combobox(box, textvariable=번호형식, values=list(wa.NUMBER_STYLES), width=6,
                                 state="readonly").pack(side="left", padx=(6, 0))
                입출력탭("번호",
                         "줄마다 기존 번호를 지우고 새 번호를 차례로 붙입니다(빈 줄은 건너뜀).",
                         [("번호 다시 매기기", lambda t: wa.renumber_lines(t, 번호형식.get())),
                          ("번호 지우기", lambda t: "\n".join(wa._EXISTING_NUMBER.sub("", l) for l in t.splitlines()))], 번호옵션)

                # A5 회신공문
                tab = ttk.Frame(notebook, padding=8)
                notebook.add(tab, text="회신공문")
                ttk.Label(tab, text="요청 공문 정보를 넣으면 ‘관련 → 제출 → 붙임 … 끝.’ 형식의 회신 공문 본문을 만듭니다.",
                          style="Hint.TLabel").pack(anchor="w")
                form = ttk.Frame(tab)
                form.pack(fill="x", pady=(6, 0))
                form.grid_columnconfigure(1, weight=1)
                값들 = {}
                for 순번, (키, 이름, 예시) in enumerate((
                        ("title", "요청 공문 제목", "2025년 하반기 교육 실적 자료 제출 요청"),
                        ("sender", "요청 기관·부서", "행정안전부 인재개발과"),
                        ("doc_no", "문서번호", "인재개발과-1234"),
                        ("doc_date", "시행일", "2025. 7. 1."),
                        ("attachment", "붙임 이름(선택)", ""),
                        ("contact", "문의처(선택)", ""))):
                    ttk.Label(form, text=이름).grid(row=순번, column=0, sticky="w", pady=2)
                    var = tk.StringVar()
                    ttk.Entry(form, textvariable=var).grid(row=순번, column=1, sticky="ew", padx=(8, 0), pady=2)
                    if 예시:
                        ttk.Label(form, text=f"예: {예시}", style="Hint.TLabel").grid(row=순번, column=2, sticky="w", padx=(8, 0))
                    값들[키] = var
                회신결과 = tk.Text(tab, wrap="word", font=("맑은 고딕", 10), background="#f7f7f7", height=10)
                회신결과.pack(fill="both", expand=True, pady=(6, 0))

                def 회신만들기():
                    if not 값들["title"].get().strip():
                        status.set("요청 공문 제목을 입력하세요.")
                        return
                    결과 = wa.reply_document(값들["title"].get(), 값들["sender"].get().strip(), 값들["doc_no"].get().strip(),
                                            값들["doc_date"].get().strip(), 값들["attachment"].get(), 값들["contact"].get())
                    회신결과.delete("1.0", "end")
                    회신결과.insert("1.0", 결과)
                    status.set("회신공문 본문을 만들었습니다.")

                def 회신복사():
                    window.clipboard_clear()
                    window.clipboard_append(회신결과.get("1.0", "end-1c"))
                    status.set("회신공문 본문을 복사했습니다.")
                self._작성도우미_회신 = (값들, 회신결과, 회신만들기)
                row = ttk.Frame(tab)
                row.pack(fill="x", pady=(6, 0))
                ttk.Button(row, text="회신공문 만들기", command=회신만들기).pack(side="left")
                ttk.Button(row, text="결과 복사", command=회신복사).pack(side="right")

                # A3 기관 서식
                tab = ttk.Frame(notebook, padding=8)
                notebook.add(tab, text="기관 서식")
                ttk.Label(tab, text="기관 문서(HWP/HWPX)의 모든 스타일 요소를 분석해 보고서와 예시 서식 HWPX를 원본 옆에 만들고, "
                                    "기관 이름을 붙여 문서 서식으로 등록합니다. 등록한 서식은 서식 목록에 ‘[기관] 이름’으로 보입니다.",
                          style="Hint.TLabel", wraplength=840, justify="left").pack(anchor="w")
                기관문서 = tk.StringVar()
                기관이름 = tk.StringVar()
                form = ttk.Frame(tab)
                form.pack(fill="x", pady=(8, 0))
                form.grid_columnconfigure(1, weight=1)
                ttk.Label(form, text="기관 문서").grid(row=0, column=0, sticky="w")
                ttk.Entry(form, textvariable=기관문서).grid(row=0, column=1, sticky="ew", padx=(8, 4))

                def 문서고르기():
                    경로 = askopenfilename(parent=window, title="기관 문서", filetypes=[("한글파일", "*.hwp *.hwpx")])
                    if 경로:
                        기관문서.set(경로)
                        예시경로["path"] = None
                ttk.Button(form, text="찾아보기…", command=문서고르기).grid(row=0, column=2)
                ttk.Label(form, text="기관 이름").grid(row=1, column=0, sticky="w", pady=(4, 0))
                ttk.Entry(form, textvariable=기관이름).grid(row=1, column=1, sticky="ew", padx=(8, 4), pady=(4, 0))
                분석결과 = tk.Text(tab, wrap="word", font=("맑은 고딕", 10), background="#f7f7f7", height=14)
                분석결과.pack(fill="both", expand=True, pady=(8, 0))
                예시경로 = {"path": None, "report": None}

                def 분석하기(등록=False):
                    경로 = 기관문서.get().strip()
                    if not 경로 or not Path(경로).exists():
                        status.set("기관 문서를 고르세요.")
                        return
                    if self.running:
                        status.set("다른 작업이 끝난 뒤 다시 시도하세요.")
                        return
                    status.set("스타일을 분석하는 중입니다… (HWP는 한/글로 임시 변환)")

                    def worker():
                        try:
                            결과 = 스타일분석_파일생성(경로)
                            self.root.after(0, 분석완료, 결과, 등록, None)
                        except Exception as exc:
                            self.root.after(0, 분석완료, None, False, str(exc))
                    threading.Thread(target=worker, daemon=True, name="style-inventory").start()

                def 분석완료(결과, 등록, error):
                    if not window.winfo_exists():
                        return
                    if error:
                        status.set("스타일 분석 실패")
                        self._알림(messagebox.showerror, APP_NAME, f"스타일 분석 실패\n{error}", parent=window)
                        return
                    inventory, stats, report, sample = 결과
                    예시경로.update(path=sample, report=report)
                    분석결과.delete("1.0", "end")
                    분석결과.insert("1.0", 스타일분석_요약(inventory, stats, report, sample))
                    status.set("스타일 분석 완료")
                    if 등록:
                        등록하기()

                def 등록하기():
                    if not 예시경로["path"]:
                        분석하기(등록=True)
                        return
                    기관 = 기관이름.get().strip()
                    줄기 = Path(기관문서.get()).stem
                    기본 = f"{기관} {줄기}" if 기관 and 기관 not in 줄기 else 줄기
                    self._서식_분석_시작(str(예시경로["path"]), 이름묻기=True, 기본이름=기본[:40], 기관=기관)

                def 보고서열기():
                    if 예시경로["report"]:
                        os.startfile(str(예시경로["report"]))

                row = ttk.Frame(tab)
                row.pack(fill="x", pady=(6, 0))
                ttk.Button(row, text="스타일 분석", command=분석하기).pack(side="left")
                ttk.Button(row, text="기관 서식으로 등록", command=등록하기).pack(side="left", padx=(6, 0))
                ttk.Button(row, text="보고서 열기", command=보고서열기).pack(side="left", padx=(6, 0))

                bottom = ttk.Frame(body)
                bottom.pack(fill="x", pady=(6, 0))
                ttk.Label(bottom, textvariable=status, style="Hint.TLabel").pack(side="left")
                ttk.Button(bottom, text="닫기", command=닫기).pack(side="right")

            def _공공언어_검토(self):
                if getattr(self, "_교정_창", None) is not None:
                    self._교정_창.lift()
                    return
                if self.running or getattr(self, "_서식분석중", False) or getattr(self, "_교정_작업중", False):
                    return
                if not self.files:
                    self._알림(messagebox.showinfo, APP_NAME, "먼저 검토할 HWP/HWPX 파일을 추가해 주세요.", parent=self.root)
                    return
                try:
                    제외경로 = 설정_폴더() / "proofreading_exclusions.json"
                    self._교정_제외 = load_exclusions(제외경로)
                except Exception as exc:
                    self._알림(messagebox.showerror, APP_NAME, f"교정 제외 목록을 읽지 못했습니다.\n{exc}", parent=self.root)
                    return
                dialog = tk.Toplevel(self.root)
                dialog.title("공공언어 바로쓰기 · 한국어 문서 교정")
                dialog.geometry("1050x610")
                dialog.transient(self.root)
                self._교정_창 = dialog
                self._교정_임시폴더 = tempfile.TemporaryDirectory(prefix="docfit_proofread_")
                self._교정_후보 = []
                self._교정_대상 = {}
                body = ttk.Frame(dialog, padding=12)
                body.pack(fill="both", expand=True)
                ttk.Label(body, text="로컬 공공언어·맞춤법 검토", font=("맑은 고딕", 14, "bold")).pack(anchor="w")
                ttk.Label(body, text="문서를 외부에 전송하지 않습니다. 교정안은 제안이며, 선택한 항목만 원본과 별도 HWPX로 저장합니다.",
                          style="Hint.TLabel").pack(anchor="w", pady=(2, 8))
                frame = ttk.Frame(body)
                frame.pack(fill="both", expand=True)
                columns = ("file", "category", "source", "suggestion", "count", "reason", "context")
                labels = ("파일", "유형", "검출 표현", "교정 제안", "횟수", "검토 이유", "문맥")
                tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
                self._교정_목록 = tree
                for key, label in zip(columns, labels):
                    tree.heading(key, text=label)
                    tree.column(key, width=270 if key in ("file", "context") else 100, anchor="w")
                ybar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
                xbar = ttk.Scrollbar(body, orient="horizontal", command=tree.xview)
                tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
                tree.pack(side="left", fill="both", expand=True)
                ybar.pack(side="right", fill="y")
                xbar.pack(fill="x")
                상태 = tk.StringVar(value="선택한 문서를 검사하고 있습니다…")
                self._교정_상태 = 상태
                ttk.Label(body, textvariable=상태, style="Hint.TLabel").pack(anchor="w", pady=(8, 4))
                controls = ttk.Frame(body)
                controls.pack(fill="x")
                ttk.Button(controls, text="모두 선택", command=lambda: tree.selection_set(*tree.get_children())).pack(side="left")
                ttk.Button(controls, text="선택 해제", command=lambda: tree.selection_remove(*tree.selection())).pack(side="left", padx=5)
                ttk.Button(controls, text="선택 표현 이후 검색에서 제외", command=self._교정_선택제외).pack(side="left", padx=5)
                ttk.Button(controls, text="제외 목록 관리", command=self._교정_제외관리).pack(side="left", padx=5)
                ttk.Button(controls, text="선택 교정 승인·새 파일 저장", command=self._교정_승인).pack(side="right")
                def close():
                    if getattr(self, "_교정_작업중", False):
                        self._알림(messagebox.showinfo, APP_NAME, "검사 또는 저장이 끝난 뒤 닫아 주세요.", parent=dialog)
                        return
                    self._교정_임시폴더.cleanup()
                    self._교정_창 = None
                    dialog.destroy()
                dialog.protocol("WM_DELETE_WINDOW", close)
                self._교정_작업중 = True
                sources = list(self.files)
                def worker():
                    candidates, snapshots, errors = [], {}, []
                    for source in sources:
                        try:
                            snapshot = 교정용_hwpx_준비(source, self._교정_임시폴더.name)
                            snapshots[source] = snapshot
                            for item in scan_hwpx(snapshot, self._교정_제외):
                                candidates.append({**item, "source_path": source})
                        except Exception as exc:
                            errors.append((source, str(exc)))
                    gui_queue.put(("proofread_scan_done", candidates, snapshots, errors))
                threading.Thread(target=worker, daemon=True).start()

            def _교정_목록갱신(self):
                tree = self._교정_목록
                children = tree.get_children()
                if children:
                    tree.delete(*children)
                for index, item in enumerate(self._교정_후보):
                    tree.insert("", "end", iid=str(index), values=(
                        Path(item["source_path"]).name, item["category"], item["source"],
                        item["suggestion"], item["count"], item["reason"],
                        item["examples"][0] if item["examples"] else ""))

            def _교정_선택제외(self):
                if getattr(self, "_교정_작업중", False): return
                selected = {int(item) for item in self._교정_목록.selection()}
                if not selected:
                    self._알림(messagebox.showinfo, APP_NAME, "제외할 표현을 선택해 주세요.", parent=self._교정_창)
                    return
                expressions = {self._교정_후보[index]["source"] for index in selected}
                updated = self._교정_제외 | expressions
                try:
                    save_exclusions(설정_폴더() / "proofreading_exclusions.json", updated)
                except Exception as exc:
                    self._알림(messagebox.showerror, APP_NAME, f"제외 목록 저장 실패\n{exc}", parent=self._교정_창)
                    return
                self._교정_제외 = updated
                self._교정_후보 = [item for item in self._교정_후보 if item["source"] not in updated]
                self._교정_목록갱신()
                self._교정_상태.set(f"{len(expressions)}개 표현을 이후 검색에서 제외합니다. 남은 후보 {len(self._교정_후보)}개")

            def _교정_제외관리(self):
                if getattr(self, "_교정_작업중", False): return
                dialog = tk.Toplevel(self._교정_창)
                dialog.title("교정 제외 목록")
                dialog.geometry("430x420")
                dialog.transient(self._교정_창)
                dialog.grab_set()
                body = ttk.Frame(dialog, padding=10)
                body.pack(fill="both", expand=True)
                ttk.Label(body, text="검색에서 제외한 표현을 선택해 다시 포함할 수 있습니다.").pack(anchor="w")
                listing = tk.Listbox(body, selectmode="extended")
                listing.pack(fill="both", expand=True, pady=8)
                for item in sorted(self._교정_제외): listing.insert("end", item)
                def restore():
                    chosen = {listing.get(index) for index in listing.curselection()}
                    if not chosen: return
                    try:
                        save_exclusions(설정_폴더() / "proofreading_exclusions.json", self._교정_제외 - chosen)
                    except Exception as exc:
                        self._알림(messagebox.showerror, APP_NAME, str(exc), parent=dialog)
                        return
                    self._교정_제외 -= chosen
                    dialog.destroy()
                    self._알림(messagebox.showinfo, APP_NAME, "복원한 표현은 다음 검사부터 다시 검색됩니다.", parent=self._교정_창)
                ttk.Button(body, text="선택 표현 다시 검색", command=restore).pack(side="right")

            def _교정_승인(self):
                if getattr(self, "_교정_작업중", False): return
                selected = [self._교정_후보[int(index)] for index in self._교정_목록.selection()]
                if not selected:
                    self._알림(messagebox.showinfo, APP_NAME, "승인할 교정 항목을 선택해 주세요.", parent=self._교정_창)
                    return
                grouped = defaultdict(set)
                for item in selected:
                    grouped[item["source_path"]].add(item["rule_id"])
                self._교정_작업중 = True
                self._교정_상태.set("승인한 교정안을 새 HWPX 파일에 저장하고 있습니다…")
                def worker():
                    results, errors = [], []
                    for source, rule_ids in grouped.items():
                        try:
                            original = Path(source)
                            base = original.with_name(original.stem + "_공공언어교정.hwpx")
                            target = base
                            number = 2
                            while target.exists():
                                target = base.with_name(base.stem + f" ({number})" + base.suffix)
                                number += 1
                            count = apply_approved_hwpx(self._교정_대상[source], target, rule_ids, self._교정_제외)
                            results.append((str(target), count))
                        except Exception as exc:
                            errors.append((source, str(exc)))
                    gui_queue.put(("proofread_apply_done", results, errors))
                threading.Thread(target=worker, daemon=True).start()

            def _서식_복사하기(self):
                if self.running or getattr(self, "_서식분석중", False): return
                path = askopenfilename(parent=self.settings_toplevel, title="서식을 복사할 한글파일",
                                       filetypes=[("한글파일·PDF", "*.hwp *.hwpx *.pdf")])
                if not path: return
                self._서식_분석_시작(path, 이름묻기=True)

            def _서식_분석_시작(self, path, 이름묻기=False, 기본이름=None, 기관=None):
                if self.running or getattr(self, "_서식분석중", False):
                    return
                parent = self.settings_toplevel if self.settings_toplevel and self.settings_toplevel.winfo_viewable() else self.root
                name = 기본이름 or Path(path).stem
                if 이름묻기:
                    name = simpledialog.askstring(APP_NAME, "새 문서 서식 이름", parent=parent, initialvalue=name)
                if name is None: return
                name = name.strip()
                if not name:
                    self._알림(messagebox.showwarning, APP_NAME, "비어 있지 않은 이름을 입력해 주세요.", parent=parent)
                    return
                if 이름묻기:
                    기관 = simpledialog.askstring(APP_NAME, "기관 이름(선택, 비워 두면 기관 없음)", parent=parent,
                                                 initialvalue=기관 or "")
                    if 기관 is None: return
                기관 = (기관 or "").strip()
                기존이름 = {p["name"] for p in self._프로파일들.values()}
                if name in 기존이름:
                    if 이름묻기:
                        self._알림(messagebox.showwarning, APP_NAME, "이미 사용 중인 서식 이름입니다.", parent=parent)
                        return
                    기본이름, 순번 = name, 2
                    while name in 기존이름:
                        name = f"{기본이름} ({순번})"
                        순번 += 1
                self._서식분석중 = True
                self._서식분석_파일 = Path(path).name
                if getattr(self, "copy_format_button", None) is not None:
                    self.copy_format_button.config(state="disabled")
                if hasattr(self, "format_drop_label"):
                    self.format_drop_label.configure(text=f"분석 중 · {Path(path).name}")
                self.status_var.set("문서 서식을 분석하고 있습니다…")
                def worker():
                    보관 = None
                    try:
                        보관 = (Path(tempfile.mkdtemp(prefix="docfit_sample_")) / "sample.hwpx"
                              if 알파_서식예시폴더_사용 else None)
                        result = 한글파일_서식_분석(path, 보관)
                        if 보관 is not None and 보관.is_file():
                            result["_서식예시_원본"] = str(보관)     # 저장할 때 서식예시 폴더로 옮긴다(서식 JSON에는 넣지 않음)
                            보관 = None                             # 이후 정리는 _서식_복사완료가 맡는다
                        result["name"] = name
                        if 기관:
                            result["organization"] = 기관
                        gui_queue.put(("format_copied", result))
                    except Exception as exc:
                        gui_queue.put(("format_copy_error", str(exc)))
                    finally:
                        if 보관 is not None:   # 표본을 만들지 못했거나 분석이 실패하면 빈 임시 폴더를 남기지 않는다
                            shutil.rmtree(보관.parent, ignore_errors=True)
                threading.Thread(target=worker, daemon=True).start()

            def 서식파일_드롭(self, event):
                if self.running or getattr(self, "_서식분석중", False):
                    return
                try:
                    items = self.root.tk.splitlist(event.data)
                except Exception:
                    items = [event.data]
                candidates = [str(item).strip() for item in items if Path(str(item).strip()).suffix.lower() in (".hwp", ".hwpx", ".pdf")]
                if not candidates:
                    self._알림(messagebox.showwarning, APP_NAME, "HWP 또는 HWPX 예시 문서를 놓아 주세요.", parent=self.root)
                    return
                self.selected_mode.set(self._한번에_모드())
                self._서식_분석_시작(candidates[0], 이름묻기=False)

            def _서식_복사완료(self, profile=None, error=None):
                표본 = profile.pop("_서식예시_원본", None) if isinstance(profile, dict) else None
                try:
                    self._서식_복사완료_처리(profile, error, 표본)
                finally:
                    self._quick_registration = False
                    if 표본:
                        shutil.rmtree(Path(표본).parent, ignore_errors=True)

            def _서식_복사완료_처리(self, profile, error, 표본):
                self._서식분석중 = False
                self._서식분석_파일 = ""
                if getattr(self, "copy_format_button", None) is not None:
                    self.copy_format_button.config(state="normal")
                parent = self._서식창_부모()
                if error:
                    self.status_var.set(f"서식 분석 실패: {error}")
                    if hasattr(self, "format_drop_label"):
                        self.format_drop_label.configure(text="예시 HWP/HWPX를 여기에 놓으면 분석 후 바로 선택합니다")
                    if not self._웹화면_모드():
                        self._알림(messagebox.showerror, APP_NAME, f"서식 복사 실패\n{error}", parent=parent)
                    return
                # 예시 문서의 서식 요소 분석 결과가 있으면 이름·세부값을 고치는 세부사항 창을 먼저 보인다
                # (계층 구조 검토는 그 창의 버튼으로 연다).
                if self._웹화면_모드():
                    확인됨 = True
                elif profile.get("element_analysis"):
                    확인됨 = self._서식_세부사항_확인(profile, parent, {p["name"] for p in self._프로파일들.values()})
                else:
                    확인됨 = self._서식_구조_확인(profile, parent)
                if not 확인됨:
                    self.status_var.set("서식 추가를 취소했습니다.")
                    return
                identifier = uuid.uuid4().hex
                folder = 서식프로파일_폴더()
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                    temp = folder / (identifier + ".tmp")
                    temp.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
                    os.replace(temp, folder / (identifier + ".json"))
                except Exception as exc:
                    self._알림(messagebox.showerror, APP_NAME, f"서식 저장 실패\n{exc}", parent=parent)
                    return
                self._프로파일들[identifier] = profile
                if 표본:
                    self._서식예시_원본_보관(identifier, 표본)
                self._활성_서식_프로파일 = identifier
                self._프로파일_목록갱신()
                self._프로파일_선택()
                if not (getattr(self, "_quick_registration", False) and self.state.user_overrode_mode):
                    self.selected_mode.set(self._한번에_모드())
                if hasattr(self, "format_drop_label"):
                    self.format_drop_label.configure(text=f"적용 준비 완료 · {profile['name']}")
                self.status_var.set(f"새 문서 서식 추가: {profile['name']}")
                if not self._웹화면_모드():
                    self._알림(messagebox.showinfo, APP_NAME, f"'{profile['name']}' 서식을 저장하고 선택했습니다.\n\n{profile['summary']}",
                                        parent=parent)

            def _서식_세부사항_확인(self, profile, parent, 다른이름=()):
                """예시 문서에서 분석한 서식 요소의 대표값을 보여 주고, 서식 이름과 세부값을 고치게 한다.

                왼쪽은 영역(쪽 여백·항목기호 문장 계층·서식 표의 칸(A1·A2·B2 …)과 칸 문단·일반 표), 오른쪽은 그
                영역의 요소별 대표값·표본 수·다른 값이다. '확인하고 서식 저장'을 누르면 고친 값을 서식 적용 값과
                보관한 서식 표 예시에 반영한다. 취소하면 profile을 바꾸지 않는다.
                """
                작업본 = copy.deepcopy(profile)
                analysis = 작업본.setdefault("element_analysis", {})
                dialog = tk.Toplevel(parent)
                dialog.title(f"서식 세부사항 검토·수정 · {profile.get('name', '')}")
                dialog.geometry("1120x720")
                dialog.transient(parent)
                dialog.grab_set()
                창_맨앞으로(dialog)
                body = ttk.Frame(dialog, padding=14)
                body.pack(fill="both", expand=True)
                ttk.Label(body, text="서식 세부사항", font=("맑은 고딕", 14, "bold")).pack(anchor="w")
                ttk.Label(body, text="예시 문서에서 가장 많이 쓴 값이 대표값입니다. 왼쪽에서 영역을 고르고 항목 값을 바꾸면, "
                                     "이 서식으로 문서를 정리할 때 바꾼 값을 씁니다. 글자·문단 크기는 pt, 표·칸 치수는 mm입니다.",
                          style="Hint.TLabel", wraplength=1080, justify="left").pack(anchor="w", pady=(2, 8))
                이름줄 = ttk.Frame(body)
                이름줄.pack(fill="x")
                ttk.Label(이름줄, text="서식 이름").pack(side="left")
                이름 = tk.StringVar(value=str(profile.get("name") or ""))
                ttk.Entry(이름줄, textvariable=이름, width=32).pack(side="left", padx=(6, 18))
                ttk.Label(이름줄, text="기관(선택)").pack(side="left")
                기관 = tk.StringVar(value=str(profile.get("organization") or ""))
                ttk.Entry(이름줄, textvariable=기관, width=22).pack(side="left", padx=6)

                panes = ttk.PanedWindow(body, orient="horizontal")
                panes.pack(fill="both", expand=True, pady=(10, 0))
                왼쪽, 오른쪽 = ttk.Frame(panes), ttk.Frame(panes)
                panes.add(왼쪽, weight=1)
                panes.add(오른쪽, weight=3)
                영역목록 = ttk.Treeview(왼쪽, show="tree", selectmode="browse")
                영역목록.column("#0", width=330)
                영역바 = ttk.Scrollbar(왼쪽, orient="vertical", command=영역목록.yview)
                영역목록.configure(yscrollcommand=영역바.set)
                영역목록.pack(side="left", fill="both", expand=True)
                영역바.pack(side="right", fill="y")
                목록틀 = ttk.Frame(오른쪽)
                목록틀.pack(fill="both", expand=True)
                columns = ("label", "value", "mode", "share", "others")
                요소목록 = ttk.Treeview(목록틀, columns=columns, show="headings", selectmode="browse")
                요소바 = ttk.Scrollbar(목록틀, orient="vertical", command=요소목록.yview)
                요소목록.configure(yscrollcommand=요소바.set)
                for key, heading, width in (("label", "항목", 210), ("value", "대표값", 180), ("mode", "적용 방식", 80),
                                            ("share", "표본(같은 값/전체)", 120), ("others", "다른 값(횟수)", 260)):
                    요소목록.heading(key, text=heading)
                    요소목록.column(key, width=width, anchor="w")
                요소목록.pack(side="left", fill="both", expand=True)
                요소바.pack(side="right", fill="y")
                편집 = ttk.LabelFrame(오른쪽, text="선택한 항목 값 바꾸기", padding=8)
                편집.pack(fill="x", pady=(8, 0))
                항목이름 = tk.StringVar(value="오른쪽 목록에서 항목을 고르세요")
                ttk.Label(편집, textvariable=항목이름, width=30).grid(row=0, column=0, sticky="w")
                값 = tk.StringVar()
                값상자 = ttk.Combobox(편집, textvariable=값, width=34, state="disabled")
                값상자.grid(row=0, column=1, padx=6)
                현재 = {"path": None, "key": None}
                경로들 = {}

                def 노드키(경로):
                    return "/".join(map(str, 경로))

                for 경로, 상위, 글 in 서식요소.detail_nodes(analysis):
                    경로들[노드키(경로)] = 경로
                    영역목록.insert(노드키(상위) if 상위 else "", "end", iid=노드키(경로), text=글,
                                   open=len(경로) <= 2)

                def 요소_표시(path, 고를=None):
                    요소목록.delete(*요소목록.get_children())
                    for key, item in 서식요소.element_map(analysis, path).items():
                        기준값 = item.get("analyzed", item["value"])
                        다른값 = ", ".join(f"{서식요소.format_value(key, v)}({n})"
                                          for v, n in item.get("variants", []) if v != 기준값)
                        표본 = f"{item.get('votes', 0)}/{item.get('total', 0)} ({item.get('share', 0):.0%})"
                        표시 = 서식요소.format_value(key, item["value"])
                        if item.get("edited"):
                            표시 += f"  (분석값 {서식요소.format_value(key, 기준값)})"
                        이름글 = 서식요소.element_label(key) + ("" if 서식요소.element_editable(key) else " · 표시만")
                        요소목록.insert("", "end", iid=key,
                                        values=(이름글, 표시, 서식요소.element_mode(key, path), 표본, 다른값))
                    if 고를 and 요소목록.exists(고를):
                        요소목록.selection_set(고를)

                def 영역_선택(event=None):
                    picked = 영역목록.selection()
                    if not picked:
                        return
                    현재.update(path=경로들[picked[0]], key=None)
                    요소_표시(현재["path"])
                    항목이름.set("오른쪽 목록에서 항목을 고르세요")
                    값.set("")
                    값상자.configure(state="disabled", values=())

                def 요소_선택(event=None):
                    picked = 요소목록.selection()
                    if not picked or 현재["path"] is None:
                        return
                    key = picked[0]
                    item = 서식요소.element_map(analysis, 현재["path"]).get(key)
                    if item is None:
                        return
                    현재["key"] = key
                    항목이름.set(서식요소.element_label(key))
                    선택지 = 서식요소.element_choices(key)
                    if key.startswith("border_"):
                        선택지 = ("없음", "실선 0.12 mm #000000", "실선 0.4 mm #000000", "이중 실선 0.5 mm #000000")
                    elif not 선택지:
                        선택지 = tuple(서식요소.format_value(key, v) for v, _ in item.get("variants", []))
                    상태값 = ("disabled" if not 서식요소.element_editable(key)
                             else "readonly" if 서식요소.element_choices(key) else "normal")
                    값상자.configure(values=선택지, state=상태값)
                    값.set(서식요소.format_value(key, item["value"]))

                def 값_바꾸기(event=None):
                    key, path = 현재["key"], 현재["path"]
                    if key is None or path is None or not 서식요소.element_editable(key):
                        return
                    try:
                        새값 = 서식요소.parse_value(key, 값.get())
                    except ValueError as exc:
                        self._알림(messagebox.showerror, APP_NAME, str(exc), parent=dialog)
                        return
                    서식요소.set_value(analysis, path, key, 새값)
                    요소_표시(path, key)

                def 분석값으로():
                    key, path = 현재["key"], 현재["path"]
                    item = 서식요소.element_map(analysis, path).get(key) if key else None
                    if item and "analyzed" in item:
                        서식요소.set_value(analysis, path, key, item["analyzed"])
                        요소_표시(path, key)
                        값.set(서식요소.format_value(key, item["value"]))

                영역목록.bind("<<TreeviewSelect>>", 영역_선택)
                요소목록.bind("<<TreeviewSelect>>", 요소_선택)
                값상자.bind("<Return>", 값_바꾸기)
                ttk.Button(편집, text="값 바꾸기", command=값_바꾸기).grid(row=0, column=2, padx=(0, 6))
                ttk.Button(편집, text="분석값으로 되돌리기", command=분석값으로).grid(row=0, column=3)
                첫영역 = next((iid for iid, path in 경로들.items() if 서식요소.element_map(analysis, path)), None)
                if 첫영역:
                    영역목록.see(첫영역)
                    영역목록.selection_set(첫영역)
                    영역_선택()
                result = {"confirmed": False}

                def 계층검토():
                    이전 = copy.deepcopy((작업본.get("style_hierarchy") or {}).get("styles", []))
                    if self._서식_구조_확인(작업본, dialog):
                        서식요소.sync_from_hierarchy(작업본, 이전)
                        if 현재["path"] is not None:
                            요소_표시(현재["path"], 현재["key"])

                def 닫기(confirmed=False):
                    if confirmed:
                        새이름 = 이름.get().strip()
                        if not 새이름:
                            self._알림(messagebox.showwarning, APP_NAME, "서식 이름을 입력해 주세요.", parent=dialog)
                            return
                        if 새이름 in set(다른이름):
                            self._알림(messagebox.showwarning, APP_NAME, "이미 사용 중인 서식 이름입니다.", parent=dialog)
                            return
                        작업본["name"] = 새이름
                        if 기관.get().strip():
                            작업본["organization"] = 기관.get().strip()
                        else:
                            작업본.pop("organization", None)
                        try:
                            서식요소.apply_to_profile(작업본)
                        except Exception as exc:
                            self._알림(messagebox.showerror, APP_NAME, f"세부사항을 서식에 반영하지 못했습니다.\n{exc}", parent=dialog)
                            return
                        앞부분 = str(작업본.get("summary", "")).split("\n\n서식 요소 대표값", 1)[0]
                        작업본["summary"] = (앞부분 + "\n\n서식 요소 대표값\n"
                                           + "\n".join(서식요소.summary_lines(analysis)))
                        profile.clear()
                        profile.update(작업본)
                        result["confirmed"] = True
                    dialog.destroy()

                buttons = ttk.Frame(body)
                buttons.pack(fill="x", pady=(10, 0))
                ttk.Button(buttons, text="계층 구조 검토…", command=계층검토).pack(side="left")
                ttk.Button(buttons, text="취소", command=닫기).pack(side="right")
                ttk.Button(buttons, text="확인하고 서식 저장", command=lambda: 닫기(True)).pack(side="right", padx=8)
                dialog.protocol("WM_DELETE_WINDOW", 닫기)
                parent.wait_window(dialog)
                return result["confirmed"]

            def _서식_구조_확인(self, profile, parent):
                """Review and edit every repeated or one-off hierarchy style before saving."""
                hierarchy = profile.setdefault("style_hierarchy", {"styles": []})
                if not hierarchy.get("styles") and (
                        not hierarchy.get("variants")
                        or (not hierarchy.get("reviewed")
                            and all(row.get("kind") == "기본값" for row in hierarchy["variants"]))):
                    # 아직 검토·저장하지 않은 기본값 행은 매번 새로 만든다(예전에 장·중제목 없이 만든 행도 바로잡힌다).
                    hierarchy["variants"] = 기본_계층_스타일(profile["format"])
                if not hierarchy.get("variants"):
                    hierarchy["variants"] = [
                        {"role": item["role"], "marker": item["marker"],
                         "count": item["count"], "kind": "반복" if item["count"] > 1 else "비반복",
                         "font": item.get("font"), "size_pt": item.get("size_pt") or 12,
                         "left_hwpunit": item.get("left_hwpunit", 0),
                         "first_line_hwpunit": item.get("first_line_hwpunit", 0),
                         "prev_spacing_hwpunit": item.get("prev_spacing_typical") or 0}
                        for item in hierarchy.get("styles", [])]
                rows = copy.deepcopy(hierarchy["variants"])
                dialog = tk.Toplevel(parent)
                dialog.title(f"서식 구조 검토·수정 · {profile['name']}")
                dialog.geometry("1050x690")
                dialog.transient(parent)
                dialog.grab_set()
                창_맨앞으로(dialog)
                body = ttk.Frame(dialog, padding=14)
                body.pack(fill="both", expand=True)
                ttk.Label(body, text="계층별 문서 스타일 검토",
                          font=("맑은 고딕", 14, "bold")).pack(anchor="w")
                ttk.Label(body, text="반복·비반복 스타일을 모두 표시합니다. 항목을 선택해 수정하고, 적용할 속성만 체크하세요. 값의 단위는 pt입니다.",
                          style="Hint.TLabel").pack(anchor="w", pady=(2, 10))
                frame = ttk.Frame(body)
                frame.pack(fill="both", expand=True)
                columns = ("kind", "count", "role", "marker", "font", "size", "left", "indent", "spacing")
                headings = ("유형", "횟수", "계층", "항목기호", "글꼴", "크기", "왼쪽 여백", "첫 줄 들여쓰기", "문단 위 여백")
                details = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
                bar = ttk.Scrollbar(frame, orient="vertical", command=details.yview)
                details.configure(yscrollcommand=bar.set)
                for key, heading in zip(columns, headings):
                    details.heading(key, text=heading)
                    details.column(key, width=110 if key == "font" else 85, anchor="center")
                details.pack(side="left", fill="both", expand=True)
                bar.pack(side="right", fill="y")
                def display(index):
                    row = rows[index]
                    return (row["kind"], row["count"], display_role(row["role"]), row["marker"], row.get("font") or "",
                            f"{float(row.get('size_pt') or 0):g}",
                            f"{float(row.get('left_hwpunit') or 0) / 100:g}",
                            f"{float(row.get('first_line_hwpunit') or 0) / 100:g}",
                            f"{float(row.get('prev_spacing_hwpunit') or 0) / 100:g}")
                for index in range(len(rows)):
                    details.insert("", "end", iid=str(index), values=display(index))
                editor = ttk.LabelFrame(body, text="선택한 스타일 수정 및 속성별 적용", padding=8)
                editor.pack(fill="x", pady=(8, 0))
                variables = {key: tk.StringVar() for key in ("role", "font", "size", "left", "indent", "spacing")}
                selection = {key: tk.BooleanVar(value=True) for key in STYLE_FIELDS}
                ttk.Label(editor, text="계층").grid(row=0, column=0, padx=3)
                ttk.Combobox(editor, textvariable=variables["role"], values=tuple(map(display_role, STYLE_ROLES)),
                             state="readonly", width=10).grid(row=1, column=0, padx=3)
                labels = (("font", "글꼴"), ("size", "크기"), ("left", "왼쪽 여백"),
                          ("indent", "첫 줄 들여쓰기"), ("spacing", "문단 위 여백"))
                for column, (key, label) in enumerate(labels, 1):
                    ttk.Label(editor, text=label).grid(row=0, column=column, padx=3)
                    ttk.Entry(editor, textvariable=variables[key], width=14).grid(row=1, column=column, padx=3)
                for column, (key, label) in enumerate((("font", "글꼴 적용"), ("size", "크기 적용"),
                                                       ("indent", "들여쓰기 적용"), ("spacing", "문단 위 여백 적용"))):
                    ttk.Checkbutton(editor, text=label, variable=selection[key]).grid(row=2, column=column + 1, sticky="w", pady=6)
                ttk.Label(body, text="같은 항목기호에 여러 변형이 있으면 가장 많이 사용된 변형이 적용 기준입니다. 비반복 항목도 검토·수정할 수 있습니다.",
                          style="Hint.TLabel").pack(anchor="w", pady=(5, 0))
                유형 = hierarchy.get("document_type")
                if 유형:
                    ttk.Label(body, text=f"문서 유형: {유형} — {DOCUMENT_TYPES.get(유형, '')} "
                                         "(계층: 1 제목 · 2 장 · 3 중제목 · 4 소제목 □ · 5 ㅇ · 6 -)",
                              style="Hint.TLabel").pack(anchor="w", pady=(3, 0))
                warnings = hierarchy.get("warnings", [])
                if warnings:
                    ttk.Label(body, text=f"논리 구조 확인 필요: {len(warnings)}건 · {warnings[0]}",
                              style="Hint.TLabel").pack(anchor="w", pady=(3, 0))
                result = {"confirmed": False}
                current = {"index": None}
                def save_current():
                    index = current["index"]
                    if index is None: return
                    row = rows[index]
                    row.update(role=stored_role(variables["role"].get()), font=variables["font"].get(),
                               size_pt=variables["size"].get(),
                               left_hwpunit=str(float(variables["left"].get()) * 100),
                               first_line_hwpunit=str(float(variables["indent"].get()) * 100),
                               prev_spacing_hwpunit=str(float(variables["spacing"].get()) * 100),
                               apply={key: var.get() for key, var in selection.items()})
                    details.item(str(index), values=display(index))
                def choose(event=None):
                    picked = details.selection()
                    if not picked: return
                    try:
                        save_current()
                    except ValueError:
                        self._알림(messagebox.showerror, APP_NAME, "여백과 크기는 숫자로 입력해 주세요.", parent=dialog)
                        return
                    index = int(picked[0])
                    current["index"] = index
                    row = rows[index]
                    shown = display(index)
                    for key, value in zip(("role", "font", "size", "left", "indent", "spacing"),
                                          (shown[2], shown[4], shown[5], shown[6], shown[7], shown[8])):
                        variables[key].set(value)
                    for key in STYLE_FIELDS:
                        selection[key].set(row.get("apply", {}).get(key, True))
                details.bind("<<TreeviewSelect>>", choose)
                if rows:
                    details.selection_set("0")
                    choose()
                buttons = ttk.Frame(body)
                buttons.pack(fill="x", pady=(10, 0))
                def close(confirmed=False):
                    if confirmed:
                        try:
                            save_current()
                            edited = apply_reviewed_styles(profile, rows)
                        except ValueError as exc:
                            self._알림(messagebox.showerror, APP_NAME, str(exc), parent=dialog)
                            return
                        previous_summary = profile.get("summary", "")
                        summary_prefix = previous_summary.split("\n\n들여쓰기 →", 1)[0]
                        edited["summary"] = (summary_prefix + "\n\n" if summary_prefix else "") + hierarchy_summary(edited["style_hierarchy"])
                        profile.clear()
                        profile.update(edited)
                        result["confirmed"] = True
                    dialog.destroy()
                ttk.Button(buttons, text="취소", command=close).pack(side="right")
                ttk.Button(buttons, text="확인하고 서식 저장", command=lambda: close(True)).pack(side="right", padx=8)
                dialog.protocol("WM_DELETE_WINDOW", close)
                parent.wait_window(dialog)
                return result["confirmed"]

            def _색상표시_상태_갱신(self, *args):
                """'자간을 수정한 글자를 색으로 표시하기' On/Off에 따라 색상 선택 라디오를 활성화/비활성화한다."""
                if getattr(self, "running", False):
                    return
                활성 = bool(self.color_mark_on_var.get())
                상태 = "normal" if 활성 else "disabled"
                for 위젯 in getattr(self, "color_radios", []):
                    try:
                        위젯.config(state=상태)
                    except Exception:
                        pass

            def _표준서식_하위옵션_상태_갱신(self, *args):
                """
                '보고서 표준서식적용' On/Off에 따라
                편집 여백 ~ 표 헤더/본문 서식 하위 옵션을 활성화/비활성화한다.
                """
                if getattr(self, "running", False):
                    return

                활성 = bool(self.stdformat_var.get())
                상태 = "normal" if 활성 else "disabled"
                # 사용자의 선택값은 보존한다. 실제 실행 여부는 작업_실행에서 제한한다.
                for name in ('paren_label_bold_check', 'paren_shrink_check'):
                    widget = getattr(self, name, None)
                    if widget is not None: widget.config(state=상태)
                for widget in getattr(self, 'label_symbol_checks', []):
                    widget.config(state='normal' if 활성 and self.paren_label_bold_var.get() else 'disabled')

                for 위젯 in getattr(self, "std_detail_checks", []):
                    try:
                        위젯.config(state=상태)
                    except Exception:
                        pass

                for 스핀 in getattr(self, "std_parspace_spins", []):
                    try:
                        스핀.config(state=상태)
                    except Exception:
                        pass

            def _설정창_생성(self):
                self.settings_toplevel = tk.Toplevel(self.root)
                self.settings_toplevel.title("내 문서에 맞게 설정하기")
                sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                scale = getattr(self, "_ui_scale", 1.0)
                settings_width = min(round(900 * scale), sw - 48)
                settings_height = min(round(760 * scale), sh - 72)
                self.settings_toplevel.geometry(f"{settings_width}x{settings_height}")
                self.settings_toplevel.minsize(min(round(560 * scale), sw - 24),
                                              min(round(460 * scale), sh - 48))
                self.settings_toplevel.configure(bg=UI_COLORS["bg"])
                self.settings_toplevel.transient(self.root)
                self.settings_toplevel.protocol("WM_DELETE_WINDOW", self.settings_toplevel.withdraw)
                heading = ttk.Frame(self.settings_toplevel, padding=(9, 4))
                heading.pack(fill="x")
                heading.columnconfigure(0, weight=1)
                ttk.Label(heading, text="내 문서에 맞게 골라요", font=("맑은 고딕", 20, "bold")).grid(row=0, column=0, sticky="w")
                ttk.Label(heading, text="선택은 자동 저장돼요. 작업 중에는 설정을 바꿀 수 없어요.", style="Hint.TLabel").grid(row=1, column=0, sticky="w")
                notebook = ttk.Notebook(self.settings_toplevel)
                notebook.pack(fill="both", expand=True, padx=18)
                self.settings_notebook = notebook
                tabs = {}
                for key, title in (("spacing", "간격"), ("format", "서식"),
                                   ("layout", "문서"), ("advanced", "고급"),
                                   ("log", "기록")):
                    frame = ttk.Frame(notebook)
                    notebook.add(frame, text=title)
                    canvas = tk.Canvas(frame, bg=UI_COLORS["bg"], highlightthickness=0)
                    scroll = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
                    canvas.configure(yscrollcommand=scroll.set)
                    scroll.pack(side="right", fill="y")
                    canvas.pack(side="left", fill="both", expand=True)
                    body = ttk.Frame(canvas, padding=12)
                    window = canvas.create_window((0, 0), window=body, anchor="nw")
                    body.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
                    canvas.bind("<Configure>", lambda e, c=canvas, w=window: c.itemconfigure(w, width=e.width))
                    tabs[key] = body
                # 내어쓰기 단계와 상세 옵션은 서식 적용 설정 안에서 함께 찾도록 통합한다.
                tabs["indent"] = tabs["format"]
                def wheel(event):
                    selected = notebook.nametowidget(notebook.select())
                    for child in selected.winfo_children():
                        if isinstance(child, tk.Canvas):
                            child.yview_scroll(-1 if event.delta > 0 or getattr(event, "num", 0) == 4 else 1, "units")
                            return "break"
                self.settings_toplevel.bind("<MouseWheel>", wheel)
                self.settings_toplevel.bind("<Button-4>", wheel)
                self.settings_toplevel.bind("<Button-5>", wheel)
                ttk.Label(tabs["spacing"], text="글자 사이 간격을 조절하는 기능이에요.\n실행창에서 ‘자간 정리’ 또는 ‘한 번에 적용’을 선택하세요.",
                          style="Hint.TLabel", wraplength=700).pack(anchor="w", pady=(0, 12))
                ttk.Label(tabs["format"],
                          text="서식 적용과 내어쓰기 작업을 함께 설정합니다. "
                               "여기서 켜고 끄면 세부 작업 창에도 그대로 반영됩니다.\n서식 작업의 기본 공백 정리도 함께 실행됩니다.",
                          style="Hint.TLabel", wraplength=700).pack(anchor="w", pady=(0, 8))
                presets = ttk.Frame(tabs["format"])
                presets.pack(fill="x", pady=(0, 12))
                self.preset_buttons = []
                button = ttk.Button(presets, text="보고서 기본 서식 선택", command=lambda: self._빠른설정("report"))
                button.pack(side="left", padx=(0, 8))
                self.preset_buttons.append(button)

                indent_presets = ttk.Frame(tabs["indent"])
                indent_presets.pack(fill="x", pady=(0, 12))
                indent_button = ttk.Button(indent_presets, text="내어쓰기만 선택", command=lambda: self._빠른설정("indent"))
                indent_button.pack(side="left", padx=(0, 8))
                self.preset_buttons.append(indent_button)
                ttk.Label(tabs["advanced"], text="처리 속도와 세부 강조 규칙을 조절해요. 처음에는 기본값을 유지해도 됩니다.",
                          style="Hint.TLabel", wraplength=700).pack(anchor="w", pady=(0, 12))
                update_box = ttk.LabelFrame(tabs["advanced"], text="앱 업데이트", padding=10)
                update_box.pack(fill="x", pady=(0, 12))
                self.check_updates_on_start_check = ttk.Checkbutton(
                    update_box,
                    text="앱 시작 시 업데이트 확인",
                    variable=self.check_updates_on_start_var,
                )
                self.check_updates_on_start_check.pack(anchor="w")
                developer_box = ttk.LabelFrame(tabs["advanced"], text="개발자 모드", padding=10)
                developer_box.pack(fill="x", pady=(0, 12))
                ttk.Checkbutton(developer_box, text="개발자 모드 켜기 (문서 도구 사용)",
                                variable=self.developer_mode_var).pack(anchor="w")
                ttk.Label(developer_box, text="기본값은 꺼짐입니다. 켜면 문서 구조 검토·맞춤법 검토·작성 도우미·Markdown 내보내기·"
                                              "고급 문서 도구 등 문서 도구 메뉴가 나타납니다.",
                          style="Hint.TLabel", wraplength=650).pack(anchor="w", padx=(22, 0), pady=(2, 0))
                ttk.Label(
                    update_box,
                    text="기본값은 켜짐입니다. 끄더라도 설정 창의 ‘업데이트 확인’ 버튼으로 직접 확인할 수 있습니다.",
                    style="Hint.TLabel",
                    wraplength=650,
                ).pack(anchor="w", padx=(22, 0), pady=(2, 0))
                window_options = ttk.LabelFrame(tabs["advanced"], text="창 표시", padding=10)
                window_options.pack(fill="x", pady=(0, 12))
                ttk.Checkbutton(window_options, text="앱 창을 항상 위에 표시",
                                variable=self.always_on_top_var).pack(anchor="w")

                idiom_box = ttk.LabelFrame(tabs["advanced"], text="상용구 파일저장", padding=10)
                idiom_box.pack(fill="x", pady=(0, 12))
                ttk.Label(
                    idiom_box,
                    text=("C:\\HWP_AUTODOCFIT\\글자상용구의 상용구 파일(HWP.IDO)과 본문상용구 폴더의 본문 상용구를\n"
                          if 알파_서식예시폴더_사용 else "앱에 포함된 상용구 파일(HWP.IDO)을 ")
                         + "한/글의 상용구 전용 폴더에 저장합니다.\n"
                         "(예: 한/글 2020 → %AppData%\\HNC\\User\\Hwp\\60)\n"
                         "진행 전에 한/글을 완전히 종료해 주세요.",
                    style="Hint.TLabel",
                    wraplength=650,
                    justify="left",
                ).pack(anchor="w", pady=(0, 6))
                상용구_줄 = ttk.Frame(idiom_box)
                상용구_줄.pack(anchor="w")
                ttk.Button(상용구_줄, text="상용구 파일저장", command=self._상용구파일_저장_클릭).pack(side="left")
                if 알파_서식예시폴더_사용:
                    ttk.Button(상용구_줄, text="앱 폴더 열기(C:\\HWP_AUTODOCFIT)", command=self._앱폴더_열기).pack(side="left", padx=(6, 0))
                container = tabs["spacing"]
                ttk.Label(container,
                          text=f"실행창의 ‘자간 정리 · 세부 작업’과 같은 {len(stages_for_mode('spacing'))}단계입니다. 여기서 켜고 끄면 세부 작업 창에도 그대로 반영됩니다.",
                          style="Hint.TLabel", wraplength=680).pack(anchor="w", pady=(0, 10))

                self.spacing_stage_vars = {}
                for number, (key, label) in enumerate(stages_for_mode("spacing"), 1):
                    if key == "reset_spacing":
                        var = self.reset_spacing_var   # 실행창 카드의 '기존 자간 초기화'와 같은 값
                    else:
                        var = tk.BooleanVar(value=self.stage_choices["spacing"].get(key, stage_default(key)))
                        var.trace_add("write", lambda *_, k=key, v=var: self._설정탭_세부작업_변경("spacing", k, v))
                    self.spacing_stage_vars[key] = var
                    item = ttk.Frame(container)
                    item.pack(fill="x", pady=(4, 7))
                    ttk.Checkbutton(item, text=f"{number:02d}. {label}", style="Stage.TCheckbutton",
                                    variable=var).pack(anchor="w")
                    ttk.Label(item, text=STAGE_EXAMPLES[key], style="Hint.TLabel",
                              wraplength=650, justify="left").pack(anchor="w", padx=(25, 0), pady=(1, 0))
                    detail = ttk.Frame(item)
                    detail.pack(anchor="w", padx=(25, 0), pady=(4, 0), fill="x")
                    self._자간정리_항목_상세(detail, key, 주설정탭=True)

                self.keep_punctuation_set_check = ttk.Checkbutton(
                    tabs["layout"],
                    text="문단 묶음 분리 및 제목 고립 방지\nㅇ 본문과 이어지는 - 내용·부연설명을 묶고, □·ㅁ 제목은 첫 ㅇ 묶음에 연결합니다.\n쪽별 줄 수로 배치를 조정하며, 저장할 때 문단 페이지 보호를 해제하고 다시 검사합니다.",
                    variable=self.keep_punctuation_set_var,
                )
                self.keep_punctuation_set_check.pack(anchor="w", pady=(6, 0))

                linespacing_range_frame = ttk.Frame(tabs["layout"])
                linespacing_range_frame.pack(anchor="w", fill="x", pady=(4, 0), padx=(18, 0))
                ttk.Label(linespacing_range_frame, text="줄간격 조정 범위").pack(side="left")
                self.linespacing_min_spin = ttk.Spinbox(
                    linespacing_range_frame, from_=50, to=500, increment=10, width=4,
                    textvariable=self.linespacing_min_var, justify="center"
                )
                self.linespacing_min_spin.pack(side="left", padx=(4, 4))
                ttk.Label(linespacing_range_frame, text="% ~").pack(side="left")
                self.linespacing_max_spin = ttk.Spinbox(
                    linespacing_range_frame, from_=50, to=500, increment=10, width=4,
                    textvariable=self.linespacing_max_var, justify="center"
                )
                self.linespacing_max_spin.pack(side="left", padx=(4, 4))
                ttk.Label(linespacing_range_frame, text="% (이 범위를 벗어나는 조정은 하지 않습니다)").pack(side="left")

                color_frame = ttk.LabelFrame(tabs["layout"], text="수정한 곳 확인하기", padding=10)
                color_frame.pack(anchor="w", fill="x", pady=(6, 0))
                self.color_mark_check = ttk.Checkbutton(
                    color_frame, text="자간을 수정한 글자를 색으로 표시하기", variable=self.color_mark_on_var
                )
                self.color_mark_check.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 2))

                self.color_radios = []
                for 순번, (키, 이름, rgb) in enumerate(COLOR_OPTIONS):
                    행 = (순번 // 5) + 1
                    열 = 순번 % 5
                    항목 = ttk.Frame(color_frame)
                    항목.grid(row=행, column=열, sticky="w", padx=(0, 8))
                    라디오 = ttk.Radiobutton(항목, text=이름, value=키, variable=self.color_var)
                    라디오.pack(side="left")
                    self.color_radios.append(라디오)
                    if rgb:
                        tk.Label(항목, text="●", fg=색상_미리보기_hex(rgb)).pack(side="left")

                self.color_mark_on_var.trace_add("write", self._색상표시_상태_갱신)
                self._색상표시_상태_갱신()

                retry_frame = ttk.LabelFrame(tabs["advanced"], text="정밀 조정 횟수 · 높일수록 시간이 늘어날 수 있어요", padding=10)
                retry_frame.pack(anchor="w", fill="x", pady=(6, 0))
                self.two_pass_check = ttk.Checkbutton(
                    retry_frame,
                    text="전체 작업 절차를 2회 반복 (기본 1회)",
                    variable=self.two_pass_var,
                )
                self.two_pass_check.pack(side="right", padx=(12, 0))
                ttk.Label(retry_frame, text="본문:").pack(side="left")
                self.retry_body_spin = ttk.Spinbox(
                    retry_frame, from_=1, to=99, width=3, textvariable=self.retry_body_var, justify="center"
                )
                self.retry_body_spin.pack(side="left", padx=(4, 12))
                ttk.Label(retry_frame, text="표/글상자 안:").pack(side="left")
                self.retry_table_spin = ttk.Spinbox(
                    retry_frame, from_=1, to=99, width=3, textvariable=self.retry_table_var, justify="center"
                )
                self.retry_table_spin.pack(side="left", padx=(4, 0))

                # 그룹 2: 보고서 서식
                # 실행창 '서식 정리 · 세부 작업'과 같은 10단계(내어쓰기는 별도 탭)를
                # 번호 순서로 나열하고, 각 단계에 딸린 상세 설정을 그 아래 중첩한다.
                # 자간 정리 탭과 마찬가지로 self.stage_choices["format"]을 그대로
                # 읽고 쓰므로, 실행창의 '세부 작업…'과 항상 같은 값을 공유한다.
                format_container = tabs["format"]
                self.format_stage_vars = {}
                self.std_detail_checks = []
                서식_단계 = list(stages_for_mode("format"))
                내어쓰기_번호 = next(i for i, (key, _) in enumerate(서식_단계) if key == "hanging_indent")
                for number, (key, label) in enumerate(서식_단계[:내어쓰기_번호], 1):
                    var = tk.BooleanVar(value=self.stage_choices["format"].get(key, stage_default(key)))
                    var.trace_add("write", lambda *_, k=key, v=var: self._설정탭_세부작업_변경("format", k, v))
                    self.format_stage_vars[key] = var
                    item = ttk.Frame(format_container)
                    item.pack(fill="x", pady=(4, 7))
                    ttk.Checkbutton(item, text=f"{number:02d}. {label}", style="Stage.TCheckbutton",
                                    variable=var).pack(anchor="w")
                    ttk.Label(item, text=STAGE_EXAMPLES[key], style="Hint.TLabel",
                              wraplength=650, justify="left").pack(anchor="w", padx=(25, 0), pady=(1, 0))
                    detail = ttk.Frame(item)
                    detail.pack(anchor="w", padx=(25, 0), pady=(4, 0), fill="x")
                    self._서식정리_항목_상세(detail, key, 주설정탭=True)

                # 표준서식/문두 라벨 굵게 토글에 따른 하위 옵션 활성화 이벤트 연결.
                self.stdformat_var.trace_add("write", self._표준서식_하위옵션_상태_갱신)
                self.paren_label_bold_var.trace_add('write', self._표준서식_하위옵션_상태_갱신)
                self._표준서식_하위옵션_상태_갱신()

                # 10. 최종 서식 기준 내어쓰기 — 별도 탭('내어쓰기')에 배치.
                self.indent_stage_vars = {}
                hanging_key, hanging_label = 서식_단계[내어쓰기_번호]
                indent_var = tk.BooleanVar(value=self.stage_choices["format"].get(hanging_key, True))
                indent_var.trace_add(
                    "write", lambda *_, k=hanging_key, v=indent_var: self._설정탭_세부작업_변경("format", k, v))
                self.indent_stage_vars[hanging_key] = indent_var
                indent_item = ttk.Frame(tabs["indent"])
                indent_item.pack(fill="x", pady=(4, 7))
                ttk.Checkbutton(indent_item, text=f"{내어쓰기_번호 + 1:02d}. {hanging_label}", style="Stage.TCheckbutton",
                                variable=indent_var).pack(anchor="w")
                ttk.Label(indent_item, text=STAGE_EXAMPLES[hanging_key], style="Hint.TLabel",
                          wraplength=650, justify="left").pack(anchor="w", padx=(25, 0), pady=(1, 0))
                indent_sub = ttk.Frame(indent_item)
                indent_sub.pack(anchor="w", padx=(25, 0), pady=(4, 0), fill="x")
                self._서식정리_항목_상세(indent_sub, hanging_key, 주설정탭=True)


                # 그룹 3: 완료 후 처리
                group3 = ttk.LabelFrame(tabs["layout"], text="검토와 작업 완료", padding=12)
                group3.pack(fill="x", pady=(0, 8))
                self.autoclose_check = ttk.Checkbutton(group3, text="작업 완료 후 한글 문서 창 닫기", variable=self.autoclose_var)
                self.autoclose_check.pack(anchor="w")
                self.unify_result_window_check = ttk.Checkbutton(
                    group3, text="서식통일 후 '작업 결과 확인' 창 띄우기 · 꺼 두면 결과는 처리 기록과 최종 검수 보고서에 남아요",
                    variable=self.unify_result_window_var)
                self.unify_result_window_check.pack(anchor="w", pady=(6, 0))
                self.verify_check = ttk.Checkbutton(
                    group3, text="상세 진단 및 문서 무결성 검사 · 본문·표·이미지·섹션 변화를 확인해요", variable=self.verify_var
                )
                self.verify_check.pack(anchor="w", pady=(6, 0))

                # 처리 기록: 기록 창 열기/닫기, 복사, 지우기
                log_tab = tabs["log"]
                ttk.Label(log_tab, text="작업 중에 일어난 일을 기록한 창이에요. 문제가 생기면 여기서 확인하세요.\n작업 중에도 이 탭은 열 수 있어요.",
                          style="Hint.TLabel", wraplength=700).pack(anchor="w", pady=(0, 12))
                log_buttons = ttk.Frame(log_tab)
                log_buttons.pack(anchor="w")
                self.log_toggle = ttk.Button(log_buttons, text="처리 기록 닫기" if self._log_visible else "▸ 처리 기록 보기",
                                             command=self._기록토글)
                self.log_toggle.pack(side="left")
                self.log_copy_button = ttk.Button(log_buttons, text="기록 복사", command=self.로그전체복사)
                self.log_copy_button.pack(side="left", padx=(8, 0))
                self.clear_button = ttk.Button(log_buttons, text="기록 지우기", command=lambda: self.log_text.delete("1.0", tk.END))
                self.clear_button.pack(side="left", padx=(8, 0))
                if self.running:
                    self.clear_button.config(state="disabled")
                log_file_box = ttk.LabelFrame(log_tab, text="로그 파일", padding=10)
                log_file_box.pack(fill="x", pady=(16, 0))
                self.log_file_check = ttk.Checkbutton(log_file_box, text="작업로그 파일 만들기", variable=self.log_file_var)
                self.log_file_check.pack(anchor="w")
                ttk.Label(log_file_box, text="기본값은 꺼짐입니다. 켜면 다음 작업부터 처리 기록을 ‘문서이름(작업로그-날짜시간).log’ 파일로\n첫 번째 문서와 같은 폴더에 저장합니다. 작업 중에는 바꿀 수 없어요.",
                          style="Hint.TLabel", wraplength=680).pack(anchor="w", padx=(22, 0), pady=(2, 0))
                if self.running:
                    self.log_file_check.config(state="disabled")
                report_box = ttk.LabelFrame(log_tab, text="검사·검수 보고서", padding=10)
                report_box.pack(fill="x", pady=(12, 0))
                self.integrity_report_file_check = ttk.Checkbutton(
                    report_box, text="무결성검사 JSON 파일 만들기", variable=self.integrity_report_file_var)
                self.integrity_report_file_check.pack(anchor="w")
                ttk.Label(
                    report_box,
                    text="문서 탭의 ‘상세 진단 및 문서 무결성 검사’를 켰을 때 검사 결과를 저장합니다.\n"
                         "기본값은 꺼짐입니다. 끄면 검사는 수행해도 (무결성검사).json 파일은 만들지 않습니다.",
                    style="Hint.TLabel", wraplength=680).pack(anchor="w", padx=(22, 0), pady=(2, 8))
                self.final_review_file_check = ttk.Checkbutton(
                    report_box, text="최종검수 JSON 파일 만들기", variable=self.final_review_file_var)
                self.final_review_file_check.pack(anchor="w")
                ttk.Label(
                    report_box,
                    text="기본값은 꺼짐입니다. 켜면 작업 목표 기준의 평가 파일을 저장합니다. 끄더라도 앱 안의 완료 결과·점수 표시는 유지됩니다.",
                    style="Hint.TLabel", wraplength=680).pack(anchor="w", padx=(22, 0), pady=(2, 0))
                if self.running:
                    self.integrity_report_file_check.config(state="disabled")
                    self.final_review_file_check.config(state="disabled")
                footer = ttk.Frame(self.settings_toplevel, padding=(18, 12))
                footer.pack(fill="x")
                ttk.Label(footer, text="만든 이 : 도토리만두", style="Hint.TLabel").pack(side="left")
                ttk.Button(footer, text="완료 · 닫기", style="Start.TButton", command=self.settings_toplevel.withdraw).pack(side="right")
                self.reset_button = ttk.Button(footer, text="기본값으로 되돌리기", command=self._설정_초기화_클릭)
                self.reset_button.pack(side="right", padx=8)
                self.update_button = ttk.Button(
                    footer,
                    text="업데이트 확인",
                    command=lambda: self._자동업데이트_확인_시작(수동=True),
                )
                self.update_button.pack(side="right")

                self.settings_toplevel.withdraw()

            def _설정탭_상태_갱신(self):
                """작업 중에는 '처리 기록' 탭만 쓸 수 있게 하고, 작업이 끝나면 모든 탭을 연다."""
                notebook = getattr(self, "settings_notebook", None)
                if notebook is None:
                    return
                try:
                    탭들 = notebook.tabs()
                    for 순번, 탭 in enumerate(탭들):
                        notebook.tab(탭, state="normal" if (not self.running or 순번 == len(탭들) - 1) else "disabled")
                    if self.running and 탭들:
                        notebook.select(탭들[-1])
                except tk.TclError:
                    pass

            def 설정창_열기(self):
                if self.settings_toplevel is None or not self.settings_toplevel.winfo_exists():
                    self._설정창_생성()
                    self._항상위_적용()
                self._설정탭_상태_갱신()
                self._자간정리탭_갱신()
                self._서식정리탭_갱신()
                self.settings_toplevel.deiconify()
                self.settings_toplevel.lift()

            def _자간정리탭_갱신(self):
                """실행창의 '세부 작업…'에서 바꾼 값을 설정창의 '자간 정리' 탭에도 반영한다."""
                for key, var in getattr(self, "spacing_stage_vars", {}).items():
                    var.set(self.stage_choices["spacing"].get(key, True))

            def _서식정리탭_갱신(self):
                """실행창의 '세부 작업…'에서 바꾼 값을 설정창의 '서식 정리'·'내어쓰기' 탭에도 반영한다."""
                for key, var in getattr(self, "format_stage_vars", {}).items():
                    var.set(self.stage_choices["format"].get(key, True))
                for key, var in getattr(self, "indent_stage_vars", {}).items():
                    var.set(self.stage_choices["format"].get(key, True))

            def _Flutter설정_반영(self, values):
                from docfit_app.settings_schema import VARIABLE_BINDINGS
                self._설정_반영중 = True
                previous_mode = self.selected_mode.get()
                try:
                    for key, value in values.items():
                        parts = key.split('.')
                        root = parts[0]
                        if len(parts) == 3 and root in ('symbol_fonts', 'table_fonts'):
                            group = self.symbol_font_vars if root == 'symbol_fonts' else self.table_font_vars
                            variable = group.get(parts[1], {}).get(parts[2])
                        elif len(parts) == 2 and root == 'label_symbols':
                            variable = self.label_symbol_vars.get(parts[1])
                        else:
                            variable = getattr(self, VARIABLE_BINDINGS.get(root, ''), None)
                            if variable is None:
                                variable = self.std_bool_vars.get(root, self.std_parspace_vars.get(root))
                        if root == 'unify_full_format':
                            self.unify_quick_mode_var.set(not bool(value))
                        elif variable is not None:
                            variable.set(value)
                        elif root in ('review_document_kind', 'review_reading_purpose'):
                            setattr(self, root, value)
                        if root == 'spacing_reset_existing':
                            self.stage_choices['spacing']['reset_spacing'] = bool(value)
                            self.reset_spacing_var.set(bool(value))
                    self.selected_mode.set(self._한번에_모드() if previous_mode in ('all','format') else previous_mode)
                    self._요약갱신()
                    self._항상위_적용()
                finally:
                    self._설정_반영중 = False
                # Do not rewrite all settings: the service already saved only changed fields.
                saved = 설정_불러오기()
                기호글꼴_적용(saved)
                표글꼴_적용(saved.get('table_fonts'))

            def _설정_변경됨(self, *args):
                if getattr(self, "_설정_반영중", False):
                    return
                try:
                    설정값 = {
                        "prevent_word_split": bool(self.prevent_word_split_var.get()),
                        "ratio_shrink": bool(self.ratio_shrink_var.get()),
                        "punctuation": bool(self.punctuation_var.get()),
                        "punctuation_threshold": str(self.punctuation_threshold_var.get()),
                        "keep_punctuation_set_together": bool(self.keep_punctuation_set_var.get()),
                        "color_mark_on": bool(self.color_mark_on_var.get()),
                        "color": str(self.color_var.get()),
                        "autoclose": bool(self.autoclose_var.get()),
                        "unify_result_window": bool(self.unify_result_window_var.get()),
                        "stdformat": bool(self.stdformat_var.get()),
                        "verify": bool(self.verify_var.get()),
                        "integrity_report_file": bool(self.integrity_report_file_var.get()),
                        "final_review_file": bool(self.final_review_file_var.get()),
                        "two_pass_processing": bool(self.two_pass_var.get()),
                        "table_spacing": bool(self.table_spacing_var.get()),
                        "log_file": bool(self.log_file_var.get()),
                        "check_updates_on_start": bool(self.check_updates_on_start_var.get()),
                        "developer_mode": bool(self.developer_mode_var.get()),
                        "review_document_kind": getattr(self, "review_document_kind", "보고서"),
                        "review_reading_purpose": getattr(self, "review_reading_purpose", "상세 설명용"),
                        "retry_body": str(self.retry_body_var.get()),
                        "retry_table": str(self.retry_table_var.get()),
                        "linespacing_min": str(self.linespacing_min_var.get()),
                        "linespacing_max": str(self.linespacing_max_var.get()),
                        "hwp_font_folder": str(self.font_folder_var.get()),
                        "paste_add_folder": str(self.paste_add_folder_var.get()),
                        "symbol_fonts": {
                            기호: {"font": v["font"].get(), "size": v["size"].get()}
                            for 기호, v in self.symbol_font_vars.items()
                        },
                        "table_fonts": {
                            part: {"font": v["font"].get(), "size": v["size"].get()}
                            for part, v in self.table_font_vars.items()
                        },
                        "label_symbols": {k: v.get() for k, v in self.label_symbol_vars.items()},
                        "paren_shrink": bool(self.paren_shrink_var.get()),
                        "paren_label_bold": bool(self.paren_label_bold_var.get()),
                    }
                    for 키, 변수 in self.std_bool_vars.items():
                        설정값[키] = bool(변수.get())
                    for 키, 변수 in self.std_parspace_vars.items():
                        설정값[키] = str(변수.get())
                    설정값["always_on_top"] = bool(self.always_on_top_var.get()) if hasattr(self, "always_on_top_var") else True
                    설정값["all_include_spacing"] = (bool(self.include_spacing_var.get())
                                                   if hasattr(self, "include_spacing_var") else True)
                    설정값["all_exclude_tables"] = (bool(self.exclude_tables_var.get())
                                                  if hasattr(self, "exclude_tables_var") else False)
                    for 키, 이름 in (("all_exclude_pagefit", "all_exclude_pagefit_var"),
                                   ("unify_exclude_tables", "unify_exclude_tables_var"),
                                   ("unify_exclude_spacing", "unify_exclude_spacing_var"),
                                   ("unify_exclude_pagefit", "unify_exclude_pagefit_var"),
                                   ("unify_keep_layout", "unify_keep_layout_var"),
                                   ("unify_full_format", "unify_full_format_var")):
                        설정값[키] = bool(getattr(self, 이름).get()) if hasattr(self, 이름) else False
                    설정값["spacing_reset_existing"] = bool(self.stage_choices["spacing"].get("reset_spacing", True))
                    설정값["spacing_enabled"] = bool(self.spacing_enabled_var.get())
                    설정값["spacing_page_fit"] = bool(self.spacing_page_fit_var.get())
                    설정값["instant_run_on_drop"] = bool(self.instant_run_on_drop_var.get())
                    설정값["auto_open_result"] = bool(self.auto_open_result_var.get())
                    설정값["active_format_profile"] = getattr(self, "_활성_서식_프로파일", "")
                    기존_설정 = 설정_불러오기()
                    기존_세부작업 = 기존_설정.get("stage_choices", {})
                    if isinstance(기존_세부작업, dict) and 기존_세부작업:
                        설정값["stage_choices"] = 기존_세부작업
                    설정값["abbreviations"] = 기존_설정.get("abbreviations", {})
                    설정값["abbreviation_defaults"] = 기존_설정.get("abbreviation_defaults", True)
                    설정값["label_symbols_rev"] = 2
                    설정값["report_files_rev"] = 2
                    설정값["title_owner_text"] = (str(self.title_owner_var.get())
                                                if hasattr(self, "title_owner_var") else "")
                    설정_저장(설정값)
                    기호글꼴_적용(설정값)
                    표글꼴_적용(설정값.get("table_fonts"))
                except Exception:
                    pass

            def _휠_콤보박스_바인딩(self, 콤보):
                """아래아 한글의 글꼴 상자처럼, 마우스 휠로 목록을 오르내리며 고를 수 있게 한다."""
                def _이동(방향):
                    값목록 = list(콤보["values"])
                    if not 값목록:
                        return
                    현재값 = 콤보.get()
                    try:
                        idx = 값목록.index(현재값)
                    except ValueError:
                        idx = -1 if 방향 > 0 else len(값목록)
                    새idx = max(0, min(len(값목록) - 1, idx + 방향))
                    콤보.set(값목록[새idx])
                    콤보.event_generate("<<ComboboxSelected>>")

                def _휠(event):
                    방향 = -1 if getattr(event, "delta", 0) > 0 else 1
                    _이동(방향)
                    return "break"

                콤보.bind("<MouseWheel>", _휠)
                콤보.bind("<Button-4>", lambda e: (_이동(-1), "break"))
                콤보.bind("<Button-5>", lambda e: (_이동(1), "break"))

            def _폰트목록_새로고침(self):
                self._한글_폰트_목록_캐시 = 한글_폰트_목록_전체(self.font_folder_var.get())
                for 콤보 in getattr(self, "symbol_font_combos", {}).values():
                    콤보["values"] = self._한글_폰트_목록_캐시
                if not self._한글_폰트_목록_캐시:
                    self._알림(messagebox.showinfo,
                        APP_NAME,
                        "지정한 폴더와 한컴오피스 번들(HFT) 글꼴 폴더에서 글꼴 파일(ttf/ttc/otf/hft)을 "
                        "찾지 못했습니다.\n"
                        "한/글 글꼴 폴더를 '찾아보기'로 직접 지정해 주세요. "
                        "폴더를 몰라도 이름을 직접 입력해서 쓸 수 있습니다.",
                        parent=self.settings_toplevel or self.root,
                    )

            def _폰트폴더_찾아보기(self):
                시작 = self.font_folder_var.get() or str(Path.home())
                폴더 = askdirectory(title="한/글 글꼴 폴더 선택", initialdir=시작 if Path(시작).exists() else None,
                                    parent=self.settings_toplevel or self.root)
                if 폴더:
                    self.font_folder_var.set(폴더)
                    self._폰트목록_새로고침()

            def _상용구파일_저장_클릭(self):
                """상용구 파일(HWP.IDO)과 본문 상용구(*.HWP)를 한/글의 상용구 전용 폴더에 복사한다.

                알파: 앱 폴더(C:\\HWP_AUTODOCFIT)의 글자상용구·본문상용구 폴더 파일을 쓴다(사용자가 바꿔 둔 파일 포함).
                글자상용구 폴더에 HWP.IDO가 없으면 앱에 포함된 파일을 쓴다."""
                부모창 = self.settings_toplevel or self.root
                try:
                    상용구_폴더_준비()
                except Exception as e:
                    self.로그표시(f"상용구 폴더 준비 실패(앱에 포함된 파일로 진행): {e}")
                글자 = 글자상용구_폴더()
                원본 = (글자 / 상용구_파일명) if 글자 is not None and (글자 / 상용구_파일명).is_file() else 번들_상용구_파일_찾기()
                본문 = 본문상용구_폴더()
                본문_파일들 = [f for f in 본문.iterdir() if f.is_file()] if 본문 is not None and 본문.is_dir() else []
                if 원본 is None:
                    self._알림(messagebox.showerror,
                        APP_NAME,
                        f"앱에 포함된 {상용구_파일명} 파일을 찾을 수 없습니다.",
                        parent=부모창,
                    )
                    return
                대상_폴더 = 상용구_전용폴더_찾기()
                if 대상_폴더 is None:
                    self._알림(messagebox.showerror,
                        APP_NAME,
                        "한/글 상용구 전용 폴더를 찾지 못했습니다.\n"
                        "한컴오피스 한/글을 한 번 이상 실행한 뒤 다시 시도해 주세요.\n"
                        "(예상 위치: %AppData%\\HNC\\User\\Hwp\\버전폴더, "
                        "탐색기에서 '숨긴 항목'을 켜야 보입니다)",
                        parent=부모창,
                    )
                    return
                대상_경로 = 대상_폴더 / 상용구_파일명
                if 대상_경로.exists():
                    if not self._알림(messagebox.askyesno,
                        APP_NAME,
                        f"이미 상용구 파일이 있습니다.\n{대상_경로}\n\n"
                        "앱에 포함된 상용구 파일로 덮어쓸까요?\n"
                        "(진행 전에 한/글을 완전히 종료해 주세요)",
                        parent=부모창,
                    ):
                        return
                try:
                    대상_폴더.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(원본, 대상_경로)
                    if 본문_파일들:
                        (대상_폴더 / "IDIOM").mkdir(parents=True, exist_ok=True)
                        for 파일 in 본문_파일들:
                            shutil.copy2(파일, 대상_폴더 / "IDIOM" / 파일.name)
                except Exception as e:
                    self._알림(messagebox.showerror, APP_NAME, f"상용구 파일 저장에 실패했습니다: {e}", parent=부모창)
                    return
                본문_안내 = f"\n본문 상용구 {len(본문_파일들)}개: {대상_폴더 / 'IDIOM'}" if 본문_파일들 else ""
                self._알림(messagebox.showinfo,
                    APP_NAME,
                    f"상용구 파일을 저장했습니다.\n{대상_경로}{본문_안내}\n\n한/글을 다시 시작하면 적용됩니다.",
                    parent=부모창,
                )

            def _앱폴더_열기(self):
                """앱 폴더(C:\\HWP_AUTODOCFIT: dll·서식예시·글자상용구·본문상용구)를 탐색기로 연다."""
                try:
                    상용구_폴더_준비()
                    HWP_AUTOMATION_DIR.mkdir(parents=True, exist_ok=True)
                    os.startfile(str(HWP_AUTOMATION_DIR))
                except Exception as e:
                    self._알림(messagebox.showerror, APP_NAME, f"앱 폴더를 열지 못했습니다: {e}", parent=self.settings_toplevel or self.root)

            def _설정_초기화_클릭(self):
                if self.running:
                    return
                if not self._알림(messagebox.askyesno, APP_NAME, "모든 설정을 기본값으로 초기화하시겠습니까?"):
                    return
                try:
                    설정_저장(dict(기본_설정))
                except Exception as e:
                    self._알림(messagebox.showerror, APP_NAME, f"설정 초기화 오류: {e}")
                    return

                self.always_on_top_var.set(기본_설정["always_on_top"])
                self.prevent_word_split_var.set(기본_설정["prevent_word_split"])
                self.ratio_shrink_var.set(기본_설정["ratio_shrink"])
                self.punctuation_var.set(기본_설정["punctuation"])
                self.punctuation_threshold_var.set(기본_설정["punctuation_threshold"])
                self.keep_punctuation_set_var.set(기본_설정["keep_punctuation_set_together"])
                self.color_mark_on_var.set(기본_설정["color_mark_on"])
                self.color_var.set(기본_설정["color"])
                self.autoclose_var.set(기본_설정["autoclose"])
                self.unify_result_window_var.set(기본_설정["unify_result_window"])
                self.stdformat_var.set(기본_설정["stdformat"])
                self.verify_var.set(기본_설정["verify"])
                self.integrity_report_file_var.set(기본_설정["integrity_report_file"])
                self.final_review_file_var.set(기본_설정["final_review_file"])
                self.two_pass_var.set(기본_설정["two_pass_processing"])
                self.table_spacing_var.set(기본_설정["table_spacing"])
                self.log_file_var.set(기본_설정["log_file"])
                self.check_updates_on_start_var.set(기본_설정["check_updates_on_start"])
                self.developer_mode_var.set(기본_설정["developer_mode"])
                self.review_document_kind = 기본_설정["review_document_kind"]
                self.review_reading_purpose = 기본_설정["review_reading_purpose"]
                self.retry_body_var.set(기본_설정["retry_body"])
                self.retry_table_var.set(기본_설정["retry_table"])
                self.linespacing_min_var.set(기본_설정["linespacing_min"])
                self.linespacing_max_var.set(기본_설정["linespacing_max"])
                self.font_folder_var.set(기본_설정.get("hwp_font_folder", "") or 한글_폰트_폴더_자동감지())
                self._한글_폰트_목록_캐시 = 한글_폰트_목록_전체(self.font_folder_var.get())
                self.paste_add_folder_var.set(기본_설정.get("paste_add_folder", ""))
                for 기호, v in self.symbol_font_vars.items():
                    기본항목 = 기본_설정.get("symbol_fonts", {}).get(기호, {})
                    v["font"].set(기본항목.get("font", ""))
                    v["size"].set(기본항목.get("size", ""))
                    if hasattr(self, "symbol_font_combos") and 기호 in self.symbol_font_combos:
                        self.symbol_font_combos[기호]["values"] = self._한글_폰트_목록_캐시
                for part, v in self.table_font_vars.items():
                    v["font"].set(기본_설정["table_fonts"][part]["font"])
                    v["size"].set(기본_설정["table_fonts"][part]["size"])
                    콤보 = getattr(self, "symbol_font_combos", {}).get(f"표_{part}")
                    if 콤보 is not None:
                        콤보["values"] = self._한글_폰트_목록_캐시
                for key, var in self.label_symbol_vars.items():
                    var.set(기본_설정["label_symbols"].get(key, True))
                self.paren_shrink_var.set(기본_설정["paren_shrink"])
                self.paren_label_bold_var.set(기본_설정["paren_label_bold"])

                for 키 in self.std_bool_keys:
                    self.std_bool_vars[키].set(기본_설정[키])
                for 키 in self.std_parspace_str_keys:
                    self.std_parspace_vars[키].set(기본_설정[키])
                self.title_owner_var.set(기본_설정["title_owner_text"])

                서식_기본값_전역_복원()
                self._활성_서식_프로파일 = ""
                self._프로파일_목록갱신()
                self._설정_변경됨()
                self._색상표시_상태_갱신()
                self._표준서식_하위옵션_상태_갱신()
                self._알림(messagebox.showinfo, APP_NAME, "모든 설정을 기본값으로 초기화했습니다.")

            def 로그표시(self, message):
                self.로그_여러줄_표시([str(message)])

            def 로그_여러줄_표시(self, 줄들):
                if not 줄들:
                    return
                try:
                    self.log_text.insert(tk.END, "\n".join(줄들) + "\n")
                    총줄수 = int(self.log_text.index("end-1c").split(".")[0])
                    if 총줄수 > 로그_최대_줄수:
                        self.log_text.delete("1.0", f"{총줄수 - 로그_최대_줄수}.0")
                    self.log_text.see(tk.END)
                except tk.TclError:
                    pass

            def _로그_키입력_차단(self, event):
                허용_키셋 = ("Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next")
                if event.state & 0x4 or event.keysym in 허용_키셋:
                    return None
                return "break"

            def 로그전체복사(self):
                try:
                    내용 = self.log_text.get("1.0", "end-1c")
                    self.root.clipboard_clear()
                    self.root.clipboard_append(내용)
                    self.status_var.set("로그를 클립보드에 복사했습니다")
                except Exception as e:
                    self._알림(messagebox.showerror, APP_NAME, f"로그 복사 중 오류가 발생했습니다.\n\n{e}", parent=self.root)

            def 파일추가(self, file_path):
                try:
                    file_path = str(Path(file_path).resolve())
                except Exception:
                    return False

                if not os.path.isfile(file_path):
                    return False
                if Path(file_path).suffix.lower() not in 지원_확장자:
                    return False
                if file_path in self.files:
                    return False

                self.files.append(file_path)
                self.file_count.configure(text=f"{len(self.files)}개 문서")
                self.file_list.insert(tk.END, file_path)
                self._원본폴더_버튼_갱신()
                if not self.running:
                    self._실행버튼_상태("normal")
                    self._작업범위_초기화()      # 새 문서를 추가하면 작업 범위는 기본값(문서 전체)으로
                    self._결과_초기화()
                    if self._안내단계 in (0, 1):
                        self._안내_설정(2)   # 문서를 추가했으니 '02 원하는 작업'을 안내
                return True

            def 폴더추가(self, folder_path):
                folder = Path(folder_path)
                if not folder.is_dir():
                    return 0
                count = 0
                try:
                    items = sorted(folder.iterdir(), key=lambda p: p.name.lower())
                except Exception:
                    return 0

                for path in items:
                    if path.is_file() and path.suffix.lower() in 지원_확장자:
                        if self.파일추가(path):
                            count += 1
                return count

            def 파일_드롭(self, event):
                if self.running:
                    return
                try:
                    items = self.root.tk.splitlist(event.data)
                except Exception:
                    items = [event.data]

                added = 0
                for item in items:
                    item = str(item).strip()
                    if os.path.isdir(item):
                        added += self.폴더추가(item)
                    elif os.path.isfile(item):
                        if self.파일추가(item):
                            added += 1

                if added:
                    self.status_var.set(f"{len(self.files)}개 문서 선택")
                    self.로그표시(f"{added}개 문서 추가")

            def 파일선택(self):
                if self.running:
                    return
                files = askopenfilenames(
                    parent=self.root,
                    title="처리할 문서를 선택하세요.",
                    initialdir=os.getcwd(),
                    filetypes=[
                        ("지원하는 모든 문서", "*.hwp *.hwpx *.hml *.pdf *.xls *.xlsx *.docx *.pptx *.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff *.gif *.txt *.md *.doc"),
                        ("변환할 수 있는 문서", "*.hwp *.hwpx *.hml *.pdf *.xls *.xlsx *.docx *.pptx *.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff *.gif *.txt *.md"),
                        ("한/글 파일", "*.hwp *.hwpx *.hml"), ("HWP 파일", "*.hwp"), ("HWPX 파일", "*.hwpx"),
                        ("텍스트/Markdown", "*.txt *.md"), ("MS Word", "*.doc *.docx"), ("PDF", "*.pdf"),
                        ("Excel", "*.xls *.xlsx"), ("PowerPoint", "*.pptx"), ("이미지", "*.png *.jpg *.jpeg *.webp"),
                    ]
                )
                if not files:
                    return
                added = 0
                for file in files:
                    if self.파일추가(file):
                        added += 1
                self.status_var.set(f"{len(self.files)}개 문서 선택")
                if added:
                    self.로그표시(f"{added}개 문서 추가")

            def Markdown_내보내기(self):
                if self.running or not self.files:
                    return
                선택 = list(self.file_list.curselection())
                대상들 = [self.files[index] for index in 선택] if 선택 else list(self.files)
                self.status_var.set(f"Markdown 변환 중 · {len(대상들)}개 문서")
                for button in self.file_buttons:
                    button.config(state="disabled")

                def worker():
                    성공, 실패 = [], []
                    for source in 대상들:
                        try:
                            성공.append(str(문서_markdown_내보내기(source)))
                        except Exception as exc:
                            실패.append((str(source), str(exc)))
                    gui_queue.put(("markdown_exported", 성공, 실패))

                threading.Thread(target=worker, daemon=True, name="markdown-export").start()

            def _고급도구_대상(self):
                선택 = list(self.file_list.curselection())
                if 선택:
                    return Path(self.files[선택[0]])
                if self.files:
                    return Path(self.files[0])
                return None

            def _고급도구_비동기(self, 이름, 작업):
                if self.running:
                    return
                self.status_var.set(f"{이름} 실행 중")
                def worker():
                    try:
                        result = 작업()
                        self.root.after(0, lambda: self._고급도구_완료(이름, result))
                    except Exception as exc:
                        self.root.after(0, lambda error=str(exc): self._고급도구_실패(이름, error))
                threading.Thread(target=worker, daemon=True, name="kordoc-advanced-tool").start()

            def _고급도구_완료(self, 이름, result):
                self.status_var.set(f"{이름} 완료")
                self.로그표시(f"{이름} 완료: {result}")
                self._알림(messagebox.showinfo, APP_NAME, f"{이름}을 완료했습니다.\n\n{result}", parent=self.root)

            def _고급도구_실패(self, 이름, error):
                self.status_var.set(f"{이름} 실패")
                self.로그표시(f"{이름} 실패: {error}")
                self._알림(messagebox.showerror, APP_NAME, f"{이름}을 완료하지 못했습니다.\n\n{error}", parent=self.root)

            def 고급문서도구_열기(self):
                if self.running:
                    return
                if getattr(self, "advanced_tools_toplevel", None) is not None:
                    try:
                        self.advanced_tools_toplevel.lift()
                        return
                    except tk.TclError:
                        self.advanced_tools_toplevel = None
                window = tk.Toplevel(self.root)
                self.advanced_tools_toplevel = window
                window.title("고급 문서 도구")
                window.geometry("620x570")
                window.resizable(True, True)
                window.transient(self.root)
                body = ttk.Frame(window, padding=18)
                body.pack(fill="both", expand=True)
                ttk.Label(body, text="구조 분석 · 비교 · 생성", font=("맑은 고딕", 16, "bold")).pack(anchor="w")
                engine_text = tk.StringVar(value="문서 엔진 확인 중…")
                ttk.Label(body, textvariable=engine_text, style="Hint.TLabel").pack(anchor="w", pady=(2, 12))
                def check_engine():
                    try: value = f"문서 변환 엔진 {kordoc_engine_version()} 준비됨"
                    except Exception as exc: value = str(exc)
                    self.root.after(0, lambda: engine_text.set(value))
                threading.Thread(target=check_engine, daemon=True).start()

                target = self._고급도구_대상()
                target_text = tk.StringVar(value=str(target) if target else "문서 목록에서 대상 파일을 먼저 선택하세요.")
                ttk.Label(body, textvariable=target_text, wraplength=570).pack(anchor="w", pady=(0, 12))
                grid = ttk.Frame(body)
                grid.pack(fill="x")
                for column in range(2): grid.grid_columnconfigure(column, weight=1)

                def require_target():
                    selected = self._고급도구_대상()
                    if selected is None:
                        raise ValueError("문서 목록에서 대상 파일을 먼저 선택해 주세요.")
                    return selected
                def page_export():
                    pages = simpledialog.askstring(APP_NAME, "페이지 범위를 입력하세요. 예: 1-3, 5", parent=window)
                    if pages: self._고급도구_비동기("페이지별 Markdown", lambda: export_advanced_markdown(require_target(), pages))
                def compare_tool():
                    other = askopenfilename(parent=window, title="비교할 문서 선택")
                    if other: self._고급도구_비동기("블록·셀 신구대조", lambda: compare_documents_advanced(require_target(), other))
                def fill_tool():
                    fields = simpledialog.askstring(APP_NAME, "채울 값을 입력하세요.\n예: 성명=홍길동,전화=02-123-4567", parent=window)
                    if fields: self._고급도구_비동기("양식 자동 채우기", lambda: fill_form(require_target(), fields))
                def patch_tool():
                    edited = askopenfilename(parent=window, title="편집한 Markdown 선택", filetypes=[("Markdown", "*.md")])
                    if edited: self._고급도구_비동기("서식 보존 텍스트 패치", lambda: patch_document(require_target(), edited))

                tools = (
                    ("고급 Markdown", lambda: self._고급도구_비동기("고급 Markdown", lambda: export_advanced_markdown(require_target()))),
                    ("페이지별 Markdown", page_export),
                    ("RAG 구조 청크", lambda: self._고급도구_비동기("RAG 구조 청크", lambda: export_rag_chunks(require_target()))),
                    ("공통 문서 IR(JSON)", lambda: self._고급도구_비동기("공통 문서 IR", lambda: export_common_ir(require_target()))),
                    ("표 추출·분류", lambda: self._고급도구_비동기("표 추출·분류", lambda: analyze_tables(require_target()))),
                    ("양식 필드 분석", lambda: self._고급도구_비동기("양식 필드 분석", lambda: analyze_form(require_target()))),
                    ("블록·셀 신구대조", compare_tool),
                    ("양식 자동 채우기", fill_tool),
                    ("서식 보존 텍스트 패치", patch_tool),
                    ("공문서 표기법 검수", lambda: self._고급도구_비동기("공문서 표기법 검수", lambda: lint_document(require_target()))),
                    ("페이지 이미지 미리보기", lambda: self._고급도구_비동기("페이지 이미지 미리보기", lambda: render_preview(require_target()))),
                )
                for index, (label, command) in enumerate(tools):
                    ttk.Button(grid, text=label, command=command).grid(
                        row=index // 2, column=index % 2, sticky="ew", padx=4, pady=4
                    )

                separator = ttk.Separator(body)
                separator.pack(fill="x", pady=14)
                generate_frame = ttk.LabelFrame(body, text="Markdown → HWPX 생성", padding=10)
                generate_frame.pack(fill="x")
                preset = tk.StringVar(value="보고서")
                ttk.Label(generate_frame, text="프리셋").pack(side="left")
                ttk.Combobox(generate_frame, textvariable=preset, values=("보고서", "계획서", "기안문"),
                             state="readonly", width=10).pack(side="left", padx=8)
                def generate_tool():
                    markdown = askopenfilename(parent=window, title="생성할 Markdown 선택", filetypes=[("Markdown", "*.md")])
                    if markdown:
                        selected_preset = preset.get()
                        self._고급도구_비동기(
                            f"{selected_preset} HWPX 생성",
                            lambda: generate_hwpx(markdown, selected_preset),
                        )
                ttk.Button(generate_frame, text="HWPX 생성…", command=generate_tool).pack(side="left")
                requirement_frame = ttk.LabelFrame(body, text="고급 문서 도구 필수 구성", padding=10)
                requirement_frame.pack(fill="x", pady=(12, 0))
                from docfit_core.kordoc_bridge import engine_status
                from docfit_core.kordoc_runtime import RUNTIME_PACK_NAME
                ttk.Label(
                    requirement_frame,
                    text=("고급 문서 도구는 앱에 포함된 변환 엔진으로 인터넷 없이 동작합니다. "
                          f"실행 파일과 같은 폴더에 {RUNTIME_PACK_NAME}을 두세요. "
                          f"지금 상태: {engine_status()['reason']}"),
                    style="Hint.TLabel",
                    wraplength=520,
                ).pack(side="left", fill="x", expand=True)
                window.protocol("WM_DELETE_WINDOW", lambda: (setattr(self, "advanced_tools_toplevel", None), window.destroy()))

            def 목록지우기(self):
                if self.running:
                    return
                self.files.clear()
                self.file_count.configure(text="0개 문서")
                self.file_list.delete(0, tk.END)
                self.status_var.set("")
                self._실행버튼_상태("disabled")
                self._작업범위_초기화()          # 목록을 비우면 작업 범위는 기본값(문서 전체)으로
                self._결과_초기화()
                self._안내_설정(1)

            def 작업기록지우기(self):
                """하단 '작업기록 지우기' — 처리 내역(로그)과 문서 목록을 함께 비운다.
                (기존 '문서목록 비우기' 기능을 이 버튼에 통합했다.)"""
                if self.running:
                    return
                # 1) 처리 내역(로그) 비우기
                try:
                    self.log_text.config(state="normal")
                    self.log_text.delete("1.0", tk.END)
                except Exception:
                    pass
                # 2) 진행 다이어그램 초기화
                try:
                    self._단계_초기화()
                except Exception:
                    pass
                # 3) 문서 목록 비우기
                self.files.clear()
                self.file_count.configure(text="0개 문서")
                self.file_list.delete(0, tk.END)
                self.status_var.set("")
                self._실행버튼_상태("disabled")
                self._작업범위_초기화()
                self._결과_초기화()
                self._안내_설정(1)

            def 버튼_작업중(self):
                for widget in self.mode_buttons + self.file_buttons + self.preset_buttons + [self.tools_button, self.proofread_button, self.stage_details_button, self.reset_button, self.update_button]:
                    widget.configure(state="disabled")
                self.profile_combo.config(state="disabled")
                self.main_profile_combo.config(state="disabled")
                self.copy_format_button.config(state="disabled")
                self._설정탭_상태_갱신()   # 세부 설정 버튼은 켜 둔다(처리 기록 탭만 사용 가능)
                self.keep_punctuation_set_check.config(state="disabled")
                self._실행버튼_상태("disabled")
                self.stop_button.config(state="normal")
                self.clear_button.config(state="disabled")
                self.document_review_button.config(state="disabled")
                self.prevent_word_split_check.config(state="disabled")
                self.punctuation_check.config(state="disabled")
                self.punctuation_threshold_spin.config(state="disabled")
                self.table_spacing_check.config(state="disabled")
                self.log_file_check.config(state="disabled")
                for 위젯 in (self.page_range_toggle, self.range_all_radio, self.range_pages_radio,
                             self.range_start_spin, self.range_end_spin):
                    위젯.config(state="disabled")
                self.retry_body_spin.config(state="disabled")
                self.retry_table_spin.config(state="disabled")
                self.two_pass_check.config(state="disabled")
                self.color_mark_check.config(state="disabled")
                for 라디오 in self.color_radios:
                    라디오.config(state="disabled")
                for 체크 in self.std_detail_checks:
                    체크.config(state="disabled")
                for 스핀 in self.std_parspace_spins:
                    스핀.config(state="disabled")
                self.autoclose_check.config(state="disabled")
                self.stdformat_check.config(state="disabled")
                self.paren_shrink_check.config(state="disabled")
                self.paren_label_bold_check.config(state="disabled")
                for check in self.label_symbol_checks:
                    check.config(state="disabled")
                self.verify_check.config(state="disabled")
                self.integrity_report_file_check.config(state="disabled")
                self.final_review_file_check.config(state="disabled")

            def 버튼_대기중(self):
                for widget in self.mode_buttons + self.file_buttons + self.preset_buttons + [self.tools_button, self.proofread_button, self.stage_details_button, self.reset_button, self.update_button]:
                    widget.configure(state="normal")
                self._요약갱신()
                self.profile_combo.config(state="readonly")
                self.main_profile_combo.config(state="readonly")
                self.copy_format_button.config(state="normal")
                self.settings_button.config(state="normal")
                self._설정탭_상태_갱신()
                self.keep_punctuation_set_check.config(state="normal")
                self._실행버튼_상태("normal" if self.files else "disabled")
                self.stop_button.config(state="disabled")
                self.clear_button.config(state="normal")
                self.document_review_button.config(state="normal")
                self.prevent_word_split_check.config(state="normal")
                self.punctuation_check.config(state="normal")
                self.punctuation_threshold_spin.config(state="normal")
                self.table_spacing_check.config(state="normal")
                self.log_file_check.config(state="normal")
                self.page_range_toggle.config(state="normal")
                self.range_all_radio.config(state="normal")
                self.range_pages_radio.config(state="normal")
                self._범위_상태_갱신()
                self.retry_body_spin.config(state="normal")
                self.retry_table_spin.config(state="normal")
                self.two_pass_check.config(state="normal")
                self.color_mark_check.config(state="normal")

                self.autoclose_check.config(state="normal")
                self.stdformat_check.config(state="normal")
                self.paren_shrink_check.config(state="normal")
                self.paren_label_bold_check.config(state="normal")
                self.verify_check.config(state="normal")
                self.integrity_report_file_check.config(state="normal")
                self.final_review_file_check.config(state="normal")
                self._색상표시_상태_갱신()
                self._표준서식_하위옵션_상태_갱신()

            def 비교창_준비(self):
                if self.compare_toplevel is not None and self.compare_toplevel.winfo_exists():
                    self.compare_toplevel.deiconify()
                    self.compare_toplevel.lift()
                    self.compare_toplevel.update_idletasks()
                    return (self.compare_left_frame.winfo_id(), self.compare_right_frame.winfo_id())

                self.compare_toplevel = tk.Toplevel(self.root)
                self.compare_toplevel.title("원본·결과 비교 보기 (왼쪽: 원본 / 오른쪽: 자간조정 중)")
                화면너비 = self.root.winfo_screenwidth()
                화면높이 = self.root.winfo_screenheight()
                self.compare_toplevel.geometry(f"{화면너비}x{화면높이}+0+0")
                self.compare_toplevel.minsize(640, 360)

                self.compare_toplevel.grid_rowconfigure(1, weight=1)
                self.compare_toplevel.grid_columnconfigure(0, weight=1)
                self.compare_toplevel.grid_columnconfigure(1, weight=1)

                ttk.Label(self.compare_toplevel, text="원본", anchor="center").grid(row=0, column=0, sticky="ew")
                ttk.Label(self.compare_toplevel, text="자간조정 중", anchor="center").grid(row=0, column=1, sticky="ew")

                self.compare_left_frame = tk.Frame(self.compare_toplevel, bg="#202020")
                self.compare_left_frame.grid(row=1, column=0, sticky="nsew")
                self.compare_right_frame = tk.Frame(self.compare_toplevel, bg="#202020")
                self.compare_right_frame.grid(row=1, column=1, sticky="nsew")

                self.compare_left_frame.bind("<Configure>", self._비교_왼쪽_리사이즈)
                self.compare_right_frame.bind("<Configure>", self._비교_오른쪽_리사이즈)
                self.compare_toplevel.protocol("WM_DELETE_WINDOW", self._비교창_닫기시도)
                self.compare_toplevel.update_idletasks()

                return (self.compare_left_frame.winfo_id(), self.compare_right_frame.winfo_id())

            def _실행_창핸들(self, name):
                """실행 중이면 그 실행 컨텍스트의 한/글 창 핸들을, 아니면 호환 전역값을 돌려준다."""
                실행 = getattr(self, "_run_context", None)
                if 실행 is not None and self.running:
                    return 실행.state.get(name)
                return globals().get(name)

            def _비교_왼쪽_리사이즈(self, event):
                hwnd = self._실행_창핸들("원본_hwp_hwnd")
                if hwnd:
                    창_임베드_크기조정(hwnd, self.compare_left_frame.winfo_id())

            def _비교_오른쪽_리사이즈(self, event):
                hwnd = self._실행_창핸들("작업_hwp_hwnd")
                if hwnd:
                    창_임베드_크기조정(hwnd, self.compare_right_frame.winfo_id())

            def _비교창_닫기시도(self):
                if self.running:
                    self._알림(messagebox.showinfo, APP_NAME, "작업이 진행 중일 때는 비교 보기 창을 닫을 수 없습니다.", parent=self.compare_toplevel)
                    return
                if self.compare_toplevel is not None:
                    self.compare_toplevel.withdraw()

            def _실행버튼_상태(self, state):
                for button in self.run_buttons:
                    button.config(state=state)

            def _단계_초기화(self):
                if hasattr(self, 'stage_board'):
                    self.stage_board.reset()

            def _단계_강조(self, 단계):
                if hasattr(self, 'stage_board'):
                    self.stage_board.activate(단계)

            def 파일포맷_변경_시작(self, target_format='hwpx'):
                """HWP·HWPX→PDF·그림은 한/글 내장 저장, 그 외 변환은 필요한 문서 엔진을 사용한다."""
                from docfit_core.file_conversion import (
                    IMAGE_FORMATS, CONVERSION_INPUTS, CONVERSION_OUTPUTS, convert_input_to_hwpx, convert_hwpx_to_text, convert_hwp_to_hwpx, convert_to_images, convert_to_pandoc_format, convert_to_pdf, output_path_for,
                )
                from docfit_core.kordoc_bridge import SUPPORTED_INPUT_EXTENSIONS, convert_to_hwpx

                if self.running or not self.files:
                    return
                target_format = str(target_format or "").lower()
                if target_format not in CONVERSION_OUTPUTS:
                    raise ValueError("결과 형식은 HWPX, PDF, DOCX, EPUB, JPG, PNG, TXT 또는 MD만 선택할 수 있습니다.")
                files = list(self.files)
                if any(Path(path).suffix.lower() not in CONVERSION_INPUTS for path in files):
                    raise ValueError("지원하는 입력 형식만 변환할 수 있습니다.")

                self.running = True
                self.closing = False
                중단_event.clear()
                self.selected_mode.set("file_format")
                self._결과_초기화(결과목록도_지우기=True)
                self._안내키, self._안내지남 = None, set()
                self._진행문서, self._실패목록, self._진행_세부작업 = None, {}, None
                self._작업시작시각, self._작업종료시각 = time.monotonic(), None
                self.status_var.set(f"파일포맷 변경 중 · {len(files)}개")
                self._안내_설정(0)
                self.버튼_작업중()
                self.로그표시("")
                self.로그표시(f"파일포맷 변경 시작 · {len(files)}개 · 결과 {target_format.upper()}")

                def worker():
                    successes, failures = 0, 0
                    app = None
                    com_initialized = False
                    try:
                        if target_format == "pdf" or target_format in IMAGE_FORMATS or (target_format == "hwpx" and any(Path(f).suffix.lower() == ".hwp" for f in files)):
                            pythoncom.CoInitialize()
                            com_initialized = True
                            app = 한글_COM_인스턴스_생성(독립=True)
                            if app.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE) is False:
                                raise RuntimeError("앱에 포함된 한/글 보안 모듈을 등록하지 못했습니다.")
                            try:
                                app.Visible = False
                            except Exception:
                                pass
                        for number, source_text in enumerate(files, 1):
                            if 중단_event.is_set():
                                break
                            source = Path(source_text)
                            gui_queue.put(("doc_begin", number, len(files), source.name))
                            try:
                                target = output_path_for(source, target_format)
                                if target_format == "hwpx":
                                    if source.suffix.lower() == ".hwp":
                                        convert_hwp_to_hwpx(app, source, target)
                                    else:
                                        convert_input_to_hwpx(source, target)
                                elif target_format in {"txt", "md"}:
                                    convert_hwpx_to_text(source, target)
                                elif target_format in {"docx", "epub"}:
                                    convert_to_pandoc_format(source, target)
                                elif target_format in IMAGE_FORMATS:
                                    target = convert_to_images(app, source, target)
                                else:
                                    convert_to_pdf(app, source, target)
                                successes += 1
                                gui_queue.put(("saved", str(source), str(target), None))
                                로그(f"파일포맷 변경 완료: {source.name} → {target.name}")
                            except Exception as exc:
                                failures += 1
                                if app is not None:
                                    try:
                                        app.Clear(1)
                                    except Exception:
                                        pass
                                gui_queue.put(("document_error", str(source), str(exc)))
                                로그(f"파일포맷 변경 실패: {source.name} — {exc}")
                        if 중단_event.is_set():
                            gui_queue.put(("file_conversion_stopped", successes, failures))
                        else:
                            gui_queue.put(("file_conversion_finished", successes, failures))
                    except Exception as exc:
                        gui_queue.put(("fatal_error", str(exc)))
                    finally:
                        if app is not None:
                            try:
                                app.Clear(1)
                                app.Quit()
                            except Exception:
                                pass
                        if com_initialized:
                            pythoncom.CoUninitialize()

                self.worker = threading.Thread(target=worker, daemon=True, name="file-format-conversion")
                self.worker.start()

            def 작업시작(self, mode='all'):
                if mode == "spacing" and not self.spacing_enabled_var.get() and not self.spacing_page_fit_var.get():
                    self._알림(messagebox.showinfo, APP_NAME, "자간 정리 또는 페이지 맞춤을 하나 이상 켜 주세요.")
                    return
                if getattr(self, "_서식분석중", False):
                    self._알림(messagebox.showinfo, APP_NAME, "서식 분석이 끝난 뒤 실행해 주세요.")
                    return
                if getattr(self, "_교정_창", None) is not None:
                    self._알림(messagebox.showinfo, APP_NAME, "공공언어·맞춤법 검토 창을 닫은 뒤 실행해 주세요.", parent=self.root)
                    return
                if self.running:
                    return
                if not self.files:
                    self._알림(messagebox.showwarning, APP_NAME, "먼저 문서(HWP/HWPX/TXT/MD/DOC(X)/PDF)를 선택하거나 끌어다 놓으세요.", parent=self.root)
                    return

                범위_확인, 작업범위 = self._작업범위_읽기()
                if not 범위_확인:
                    return

                if mode in ("format", "all"):
                    self.stdformat_var.set(True)

                # 알파: 적용할 서식의 예시 파일(서식예시 폴더)을 사용자가 고쳤으면 바뀐 서식 값을 먼저 설정에 옮긴다.
                서식예시_알림 = None
                if mode in ("format", "all") and not getattr(self, "_서식예시_작업", None):
                    try:
                        _, 서식예시_알림 = self._서식예시_동기화()
                    except Exception as exc:
                        서식예시_알림 = f"서식예시 파일 검사 실패(서식 설정은 그대로): {exc}"

                # 중단 버튼으로 멈춘 작업과 같은 모드로 다시 실행하면, 이미 끝낸
                # 문서는 건너뛰고 그 다음 문서부터 이어서 진행한다. 모드가 다르면
                # 새 작업으로 보고 처음부터 다시 시작한다.
                이어서_진행 = self._재개_대기중 and self._재개_모드 == mode
                시작_인덱스 = self._재개_시작_인덱스 if 이어서_진행 else 1
                self._재개_대기중 = False

                self.running = True

                self.settings_toplevel.withdraw()
                self.closing = False
                중단_event.clear()
                self._결과_초기화(결과목록도_지우기=not 이어서_진행)   # 이어서 진행할 때는 이전 결과 기록을 남긴다
                if not 이어서_진행:
                    self._작업시작시각 = time.monotonic()
                    self._실패목록 = {}
                self._진행문서, self._작업종료시각 = None, None
                self._작업모드 = mode
                self.버튼_작업중()

                self.로그표시("")
                if 이어서_진행:
                    self.로그표시(f"중단된 작업을 이어서 진행합니다 ({시작_인덱스}/{len(self.files)}번째 문서부터).")
                self.로그표시("=" * 45)
                self.로그표시(f"{APP_NAME} 작업 시작 — {dict(spacing='자간조정', unify='서식통일', format='서식적용', all='일괄적용')[mode]}")
                self.로그표시(f"문서: {len(self.files)}개")
                if 서식예시_알림:
                    self.로그표시(서식예시_알림)
                if 작업범위 is None:
                    self.로그표시("작업 범위: 문서 전체")
                else:
                    self.로그표시(f"작업 범위: {쪽표시(작업범위[0])} ~ {쪽표시(작업범위[1])}")

                try:
                    둘째줄기준값 = max(1, int(self.punctuation_threshold_var.get()))
                except Exception:
                    둘째줄기준값 = 5
                    self.punctuation_threshold_var.set("5")

                try:
                    본문재시도값 = max(1, int(self.retry_body_var.get()))
                except Exception:
                    본문재시도값 = 30
                    self.retry_body_var.set("30")

                try:
                    표재시도값 = max(1, int(self.retry_table_var.get()))
                except Exception:
                    표재시도값 = 5
                    self.retry_table_var.set("5")

                try:
                    줄간격최소값 = max(10, int(self.linespacing_min_var.get()))
                except Exception:
                    줄간격최소값 = 140
                    self.linespacing_min_var.set("140")

                try:
                    줄간격최대값 = max(10, int(self.linespacing_max_var.get()))
                except Exception:
                    줄간격최대값 = 200
                    self.linespacing_max_var.set("200")

                if 줄간격최소값 > 줄간격최대값:
                    줄간격최소값, 줄간격최대값 = 줄간격최대값, 줄간격최소값
                    self.linespacing_min_var.set(str(줄간격최소값))
                    self.linespacing_max_var.set(str(줄간격최대값))

                문단위간격_기본값 = {"std_parspace_chapter": 15, "std_parspace_midtitle": 15, "std_parspace_box": 15,
                                "std_parspace_circle": 8, "std_parspace_dash": 4, "std_parspace_note": 0}
                문단위간격_값 = {}
                for 키, 기본값 in 문단위간격_기본값.items():
                    try:
                        문단위간격_값[키] = max(0, int(self.std_parspace_vars[키].get()))
                    except Exception:
                        문단위간격_값[키] = 기본값
                        self.std_parspace_vars[키].set(str(기본값))
                try:
                    복귀배율 = int(self.std_parspace_vars["std_parspace_return_percent"].get())
                except (TypeError, ValueError):
                    복귀배율 = 150
                복귀배율 = max(100, min(400, 복귀배율))
                self.std_parspace_vars["std_parspace_return_percent"].set(str(복귀배율))
                문단위간격_값["std_parspace_return_percent"] = 복귀배율

                선택_색상 = COLOR_MAP.get(self.color_var.get()) if self.color_mark_on_var.get() else None
                표준서식_세부_전달 = {키: var.get() for 키, var in self.std_bool_vars.items()}
                표준서식_세부_전달["std_title_subtitle_pt"] = 제목_부제_크기_반영(
                    self.std_parspace_vars["std_title_subtitle_pt"].get())
                self.std_parspace_vars["std_title_subtitle_pt"].set(str(제목_부제_크기_pt))   # 잘못된 값은 고친 값으로 보여 준다
                표준서식_세부_전달["title_owner_text"] = 제목_담당자_글_반영(self.title_owner_var.get())
                표준서식_세부_전달["unify_result_window"] = 서식통일_결과창_반영(self.unify_result_window_var.get())
                표준서식_세부_전달["table_fonts"] = {
                    part: {"font": v["font"].get(), "size": v["size"].get()}
                    for part, v in self.table_font_vars.items()
                }
                # 카드 옵션: '표 제외'(한 번에 적용·서식 통일)는 표 관련 세부 작업을 모두 끄고 표 칸 안 문장도 자간 작업에서
                # 빼고, '페이지 맞춤 제외'는 문단 아래 간격 페이지 맞춤·관련 문단 페이지 배치를 끈다. 서식 통일의 '자간 정리
                # 제외'는 서식통일이 고친 문장의 자간 조정을 끈다.
                if mode == "unify":
                    표제외, 쪽맞춤제외 = self.unify_exclude_tables_var.get(), self.unify_exclude_pagefit_var.get()
                elif mode in ("all", "format"):
                    표제외, 쪽맞춤제외 = self.exclude_tables_var.get(), self.all_exclude_pagefit_var.get()
                else:
                    표제외 = 쪽맞춤제외 = False
                from docfit_core.app_state import RunOptions
                self.state.options = RunOptions(
                    mode=mode, include_spacing=bool(self.include_spacing_var.get()),
                    spacing_enabled=bool(self.spacing_enabled_var.get()),
                    spacing_page_fit=bool(self.spacing_page_fit_var.get()),
                    reset_spacing=bool(self.stage_choices[mode].get("reset_spacing", True)),
                    table_spacing=bool(self.table_spacing_var.get()), exclude_tables=bool(표제외),
                    verify_result=bool(self.verify_var.get()), autoclose=bool(self.autoclose_var.get()),
                    developer_mode=bool(self.developer_mode_var.get()),
                    page_range=(f"{self.range_start_var.get()}-{self.range_end_var.get()}"
                                if self.range_mode_var.get() == "pages" else ""))
                세부작업 = self.state.options.resolve_stages(self.stage_choices)
                # 서식 통일의 '자간 정리 제외'는 세부 작업 '서식통일 문장 자간 정리'를 끈 것과 같다(서로 연동).
                자간제외 = mode == "unify" and (bool(self.unify_exclude_spacing_var.get())
                                             or not stage_enabled(세부작업, "unify_spacing", mode))
                if 표제외:
                    세부작업 = 표작업_제외(세부작업)
                    self.로그표시("표 제외: 표 관련 작업(텍스트 표 변환·기본 표 서식·표 칸 너비·표 정밀 서식·표 머리글 서식·"
                               "표 서식통일·표 안 자간·줄·단어 작업)을 빼고, 표 칸 안 문장도 자간 작업에서 뺍니다. "
                               "제목·개요 서식 표는 정리합니다.")
                if 쪽맞춤제외:
                    세부작업 = 페이지맞춤_제외(세부작업)
                    self.로그표시("페이지 맞춤 제외: 문단 아래 간격 페이지 맞춤과 관련 문단 페이지 배치를 뺍니다.")
                if 자간제외:
                    self.로그표시("자간 정리 제외: 서식통일이 고친 문장의 자간 조정·외톨이 글자 당기기를 하지 않습니다.")
                표준서식_세부_전달["unify_exclude_spacing"] = 자간제외

                self._진행_세부작업 = dict(세부작업)   # 진행 화면이 끈 단계를 목록에서 뺄 때 쓴다
                from docfit_engine.runtime import session_for
                self._run_context = session_for(globals()).new_context(
                    options=self.state.options, profile=표준서식_세부_전달, cancellation=중단_event)
                self.worker = threading.Thread(
                    target=작업_실행,
                    args=(
                        list(self.files),
                        self.punctuation_var.get(),
                        선택_색상,
                        False,
                        None,
                        None,
                        self.autoclose_var.get(),
                        self.stdformat_var.get(),
                        self.verify_var.get(),
                        둘째줄기준값,
                        본문재시도값,
                        표재시도값,
                        self.paren_shrink_var.get(),
                        표준서식_세부_전달,
                        문단위간격_값,
                        self.paren_label_bold_var.get(),
                        self.keep_punctuation_set_var.get(),
                        self.prevent_word_split_var.get(),
                        mode,
                        {k: v.get() for k, v in self.label_symbol_vars.items()},
                        줄간격최소값,
                        줄간격최대값,
                        self.table_spacing_var.get() and not 표제외,
                        작업범위,
                        self.log_file_var.get(),
                        세부작업,
                        2 if self.two_pass_var.get() else 1,
                        시작_인덱스,
                        None,
                        self.integrity_report_file_var.get(),
                        self.final_review_file_var.get(),
                    ),
                    kwargs={"context": self._run_context, "callbacks": self._run_context.callbacks},
                    daemon=True
                )
                self.worker.start()

            def 작업중단(self):
                if not self.running:
                    return
                중단_event.set()
                self.stop_button.config(state="disabled")
                self.status_var.set("작업 중단 처리 중...")
                self.로그표시("사용자가 작업 중단을 요청했습니다.")

            def _서식통일_대표값_검토_요청(self, kind, payload):
                from docfit_engine.context import current_context
                실행 = current_context()
                요청 = {"payload": payload, "done": threading.Event(), "approved": False,
                      "profile": None if 실행 is None else 실행.state.get("_서식통일_문서대표프로필")}
                event = f"style_unify_{kind}_review"
                gui_queue.put((event, 요청))
                while not 요청["done"].wait(0.1):
                    if 중단_요청됨() or self.closing:
                        return {"approved": False, "selected": []}
                return 요청

            def _대화상자_부모(self):
                """숨겨진 기본 창 대신 맨 앞에 뜨는 임시 부모를 돌려준다."""
                if (self.root.state() != "withdrawn"
                        and not getattr(self.root, "_docfit_hidden_backend", False)):
                    return self.root, None
                임시 = tk.Toplevel(self.root)
                임시.wm_transient("")
                임시.overrideredirect(True)
                임시.attributes("-alpha", 0.0)
                임시.attributes("-topmost", True)
                임시.geometry(f"1x1+{임시.winfo_screenwidth() // 2}+{임시.winfo_screenheight() // 3}")
                임시.deiconify()
                임시.lift()
                임시.focus_force()
                return 임시, 임시

            def _절약_완료창(self, 성공, 실패):
                if getattr(self.root, "_docfit_hidden_backend", False):
                    return
                """작업 완료창(개발자 모드 끔): 검은 고양이 그림과 '당신의 소중한 시간 00분 00초가 절약되었습니다!'만 보인다.

                실패한 문서가 있으면 절약 시간 대신 처리하지 못한 문서 수를 알린다(자세한 내용은 처리 기록·개발자 모드)."""
                창 = tk.Toplevel(self.root)
                창.title(APP_NAME)
                창.resizable(False, False)
                창.configure(bg="#FFFFFF")
                창.transient(self.root)
                그림경로 = 번들_고양이_그림_찾기()
                if 그림경로 is not None:
                    try:
                        그림 = tk.PhotoImage(file=str(그림경로))
                        창._고양이 = 그림            # 그림이 사라지지 않게 창에 붙잡아 둔다
                        tk.Label(창, image=그림, bg="#FFFFFF").pack(padx=40, pady=(24, 4))
                    except tk.TclError:
                        pass
                if 실패 == 0:
                    문구 = f"당신의 소중한 시간 {절약시간_분초_표시(self._절약초 or 0)}가 절약되었습니다!"
                else:
                    문구 = f"문서 {실패}개를 처리하지 못했습니다. 처리 기록을 확인해 주세요. (성공 {성공}개)"
                tk.Label(창, text=문구, bg="#FFFFFF", fg="#111827", font=("맑은 고딕", 14, "bold"),
                         wraplength=560, justify="center").pack(padx=32, pady=(4, 16))
                확인 = ttk.Button(창, text="확인", command=창.destroy)
                확인.pack(pady=(0, 22))
                창.bind("<Return>", lambda e: 창.destroy())
                창.bind("<Escape>", lambda e: 창.destroy())
                창.update_idletasks()
                x = 창.winfo_screenwidth() // 2 - 창.winfo_reqwidth() // 2
                y = 창.winfo_screenheight() // 3 - 창.winfo_reqheight() // 3
                창.geometry(f"+{max(0, x)}+{max(0, y)}")
                창_맨앞으로(창)
                확인.focus_set()
                return 창

            def _알림(self, 함수, *args, **kwargs):
                """웹 화면 모드에서도 메시지 창이 보이도록 임시 부모로 띄운다."""
                if getattr(self.root, "_docfit_hidden_backend", False):
                    import uuid
                    done = tk.BooleanVar(master=self.root, value=False)
                    pending = {"id": uuid.uuid4().hex, "title": str(args[0]) if args else APP_NAME,
                               "message": str(args[1]) if len(args) > 1 else "",
                               "confirm": 함수 in (messagebox.askyesno, messagebox.askokcancel),
                               "choices": kwargs.pop("flutter_choices", []),
                               "fields": kwargs.pop("flutter_fields", []),
                               "done": done, "answer": False}
                    self._flutter_dialog = pending
                    try:
                        self.root.wait_variable(done)
                        self._flutter_selection = pending.get("selection", [])
                        self._flutter_values = pending.get("values", {})
                        return pending["answer"]
                    except tk.TclError:
                        return False
                    finally:
                        if getattr(self, "_flutter_dialog", None) is pending:
                            self._flutter_dialog = None
                if "parent" in kwargs:
                    return 함수(*args, **kwargs)
                부모, 임시 = self._대화상자_부모()
                try:
                    return 함수(*args, parent=부모, **kwargs)
                finally:
                    if 임시 is not None:
                        임시.destroy()

            def _검토창_앞으로(self, window):
                """한글 창에 가려지지 않도록 검토 창을 맨 앞으로 올린다."""
                창_맨앞으로(window)

            def _서식통일_대표서식_검토창(self, 요청):
                """표본 조사값을 보여 주고 적용 전 문서별 표준값을 편집하게 한다."""
                # 엔진은 실행 컨텍스트마다 대표 프로필을 따로 가진다. 요청에 실린 그 객체를 읽고 고쳐야
                # 사용자가 고친 값이 실제 작업에 반영된다(실행 밖 호환 경로에서만 전역값을 쓴다).
                대표프로필 = 요청.get("profile")
                if 대표프로필 is None:
                    대표프로필 = _서식통일_문서대표프로필
                if getattr(self.root, "_docfit_hidden_backend", False):
                    fields, mapping = [], {}
                    for index, (key, values) in enumerate(대표프로필.items()):
                        for field, pair in values.items():
                            if field not in ("font", "size", "marker_bold", "label_bold", "italic", "underline"):
                                continue
                            value = pair[0]
                            identity = f"{index}:{field}"
                            shown = "" if value is None else str(value / 100 if field == "size" else value if field == "font" else bool(value))
                            labels = {"font": "글꼴", "size": "크기", "marker_bold": "기호 굵게", "label_bold": "라벨 굵게", "italic": "기울임", "underline": "밑줄"}
                            fields.append({"id": identity, "label": f"{key[0]} {labels[field]}" + (" (pt)" if field == "size" else ""),
                                           "type": "text" if field in ("font", "size") else "bool", "value": shown})
                            mapping[identity] = (key, field)
                    from math import isfinite
                    while True:
                        approved = self._알림(messagebox.askyesno, "대표 서식 검토", "빈 값은 판정을 보류합니다. 대표값을 확인한 뒤 진행하세요.", flutter_fields=fields)
                        if not approved:
                            break
                        try:
                            updates = []
                            for identity, raw in self._flutter_values.items():
                                key, field = mapping[identity]
                                value = raw.strip() or None
                                if value is not None and field == "size":
                                    number = float(value)
                                    if not isfinite(number) or not 0 < number <= 4000:
                                        raise ValueError("글자 크기를 확인해 주세요.")
                                    value = round(number * 100)
                                elif value is not None and field != "font":
                                    if value.lower() not in ("true", "false"):
                                        raise ValueError("강조 값은 True/False 또는 빈칸으로 입력하세요.")
                                    value = value.lower() == "true"
                                elif value is not None and len(value) > 100:
                                    raise ValueError("글꼴 이름이 너무 깁니다.")
                                updates.append((key, field, value))
                            for key, field, value in updates:
                                prior = 대표프로필[key][field]
                                대표프로필[key][field] = (value, prior[1])
                            break
                        except (ValueError, KeyError, TypeError) as exc:
                            self._알림(messagebox.showerror, APP_NAME, str(exc))
                    요청["approved"] = approved
                    요청["done"].set()
                    return
                그룹별_표본 = 요청["payload"]
                window = tk.Toplevel(self.root)
                window.title("서식통일 2/5 · 대표 서식 확인")
                window.transient(self.root)
                window.geometry("900x680")
                window.minsize(700, 480)
                host = ttk.Frame(window, padding=16)
                host.pack(fill="both", expand=True)
                ttk.Label(host, text="문서에서 조사한 대표 서식", font=("맑은 고딕", 15, "bold")).pack(anchor="w")
                ttk.Label(host, text="대표값을 확인하면 불일치 부분을 추가 승인 없이 자동 교정합니다. 빈 값은 보정하지 않으며, 필요한 대표값이 없는 문단은 결과 문서에 빨간색으로 표시합니다.",
                          wraplength=850).pack(anchor="w", pady=(5, 10))

                # ※ 표본이 우세값을 만들지 못한 경우 * 표본의 크기와 후보를 함께
                # 제시하되 자동으로 복사하지 않는다. 최종 선택은 사용자가 한다.
                stars = [key for key in 그룹별_표본 if key[0] in ("*", "**")]
                star_sizes = []
                for key in stars:
                    profile = 대표프로필.get(key, {})
                    value = profile.get("size", (None, 0))[0]
                    if value is not None:
                        star_sizes.append(f"{key[0]} {value / 100:g}pt")
                if any(key[0] == "※" and any(v[0] is None for v in 대표프로필.get(key, {}).values())
                       for key in 그룹별_표본):
                    note = "※ 대표값이 불명확합니다. *·** 계열의 크기 유사성은 참고 후보일 뿐이며, 자동 선택하지 않습니다."
                    if star_sizes:
                        note += " 후보: " + ", ".join(star_sizes)
                    ttk.Label(host, text=note, foreground="#9a3412", wraplength=850).pack(anchor="w", pady=(0, 8))
                    ambiguous = next(key for key in 그룹별_표본 if key[0] == "※"
                                     and any(v[0] is None for v in 대표프로필.get(key, {}).values()))
                    candidate_keys = [key for key in stars
                                      if 대표프로필.get(key, {}).get("font", (None, 0))[0] is not None
                                      or 대표프로필.get(key, {}).get("size", (None, 0))[0] is not None]
                    if candidate_keys:
                        choice_row = ttk.Frame(host)
                        choice_row.pack(fill="x", pady=(0, 8))
                        choice = ttk.Combobox(choice_row, state="readonly", width=26,
                                              values=[f"{key[0]} 대표값 사용" for key in candidate_keys])
                        choice.current(0)
                        choice.pack(side="left")

                        def use_candidate():
                            selected = candidate_keys[max(0, choice.current())]
                            source = 대표프로필.get(selected, {})
                            for field, control in editors.get(ambiguous, {}).items():
                                value = source.get(field, (None, 0))[0]
                                if field == "font":
                                    control.delete(0, "end")
                                    if value is not None:
                                        control.insert(0, str(value))
                                elif field == "size":
                                    control.delete(0, "end")
                                    if value is not None:
                                        control.insert(0, f"{value / 100:g}")
                                elif value is not None:
                                    control.set(("굵게" if value else "보통") if field.endswith("bold")
                                                else ("적용" if value else "미적용"))
                            self.로그표시(f"※ 대표값 후보로 {selected[0]} 그룹 값을 선택했습니다. 확인 후 필요하면 개별 수정하세요.")

                        ttk.Button(choice_row, text="선택한 후보를 ※에 채우기", command=use_candidate).pack(side="left", padx=8)

                canvas = tk.Canvas(host, highlightthickness=0)
                scrollbar = ttk.Scrollbar(host, orient="vertical", command=canvas.yview)
                body = ttk.Frame(canvas)
                body.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
                canvas.create_window((0, 0), window=body, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)
                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

                editors = {}
                필드 = (("font", "글꼴"), ("size", "크기(pt)"), ("marker_bold", "문두 굵게"),
                        ("label_bold", "괄호라벨 굵게"), ("hanging_indent", "내어쓰기"))
                for row, (key, 항목들) in enumerate(그룹별_표본.items()):
                    marker, role, level = key
                    frame = ttk.LabelFrame(body, text=f"{marker}  ·  {role}  ·  표본 {len(항목들)}개", padding=8)
                    frame.grid(row=row, column=0, sticky="ew", padx=4, pady=4)
                    body.grid_columnconfigure(0, weight=1)
                    profile = 대표프로필.get(key, {})
                    editors[key] = {}
                    for col, (field, label) in enumerate(필드):
                        ttk.Label(frame, text=label).grid(row=0, column=col, sticky="w", padx=4)
                        pair = profile.get(field, (None, 0))
                        value = pair[0]
                        if field == "font":
                            shown = "" if value is None else str(value)
                            control = ttk.Entry(frame, width=18)
                            control.insert(0, shown)
                        elif field == "size":
                            shown = "" if value is None else f"{value / 100:g}"
                            control = ttk.Entry(frame, width=9)
                            control.insert(0, shown)
                        else:
                            options = ("판정 보류", "굵게", "보통") if field in ("marker_bold", "label_bold") else ("판정 보류", "적용", "미적용")
                            shown = "판정 보류" if value is None else (("굵게" if value else "보통") if field.endswith("bold") else ("적용" if value else "미적용"))
                            control = ttk.Combobox(frame, values=options, state="readonly", width=10)
                            control.set(shown)
                        control.grid(row=1, column=col, sticky="ew", padx=4, pady=(2, 4))
                        editors[key][field] = control
                buttons = ttk.Frame(host)
                buttons.pack(fill="x", pady=(10, 0))

                def finish(approved):
                    if approved:
                        for key, controls in editors.items():
                            prior = 대표프로필.get(key, {})
                            updated = dict(prior)
                            for field, control in controls.items():
                                raw = control.get().strip()
                                old_count = prior.get(field, (None, 0))[1]
                                if not raw or raw == "판정 보류":
                                    value = None
                                elif field == "font":
                                    value = raw
                                elif field == "size":
                                    try:
                                        value = int(round(float(raw) * 100))
                                        if value <= 0:
                                            raise ValueError
                                    except ValueError:
                                        self._알림(messagebox.showerror, APP_NAME, f"{key[0]} 크기는 0보다 큰 pt 숫자여야 합니다.", parent=window)
                                        return
                                elif field.endswith("bold"):
                                    value = raw == "굵게"
                                else:
                                    value = raw == "적용"
                                updated[field] = (value, old_count)
                            대표프로필[key] = updated
                    요청["approved"] = approved
                    요청["done"].set()
                    window.destroy()

                ttk.Button(buttons, text="취소", command=lambda: finish(False)).pack(side="right")
                ttk.Button(buttons, text="확인한 대표값으로 진행", style="Primary.TButton",
                           command=lambda: finish(True)).pack(side="right", padx=(0, 8))
                window.protocol("WM_DELETE_WINDOW", lambda: finish(False))
                window.grab_set()
                self._검토창_앞으로(window)
                window.focus_set()

            def _서식통일_적용영역_검토창(self, 요청):
                계획 = 요청["payload"]
                if getattr(self.root, "_docfit_hidden_backend", False):
                    choices = [{"id": index, "label": str(item.get("text", item.get("reason", item)))[:300]}
                               for index, item in enumerate(계획) if item.get("mismatch")]
                    approved = self._알림(messagebox.askyesno, "서식 적용 영역 검토", "선택한 불일치 영역만 적용합니다.", flutter_choices=choices)
                    요청["approved"] = approved
                    요청["selected"] = self._flutter_selection if approved else []
                    요청["done"].set()
                    return
                후보 = [(index, item) for index, item in enumerate(계획) if item.get("mismatch")]
                window = tk.Toplevel(self.root)
                window.title("서식통일 3/5 · 편집 영역 확인")
                window.transient(self.root)
                window.geometry("1040x700")
                window.minsize(760, 500)
                host = ttk.Frame(window, padding=14)
                host.pack(fill="both", expand=True)
                ttk.Label(host, text="대표 서식 미적용 영역", font=("맑은 고딕", 15, "bold")).pack(anchor="w")
                ttk.Label(host, text="체크된 문장만 적용합니다. 문장을 선택하면 전체 내용과 적용 예정 속성을 확인할 수 있습니다.",
                          wraplength=980).pack(anchor="w", pady=(4, 10))
                columns = ("apply", "marker", "fields", "text")
                tree = ttk.Treeview(host, columns=columns, show="headings", selectmode="browse", height=13)
                for column, title, width in (("apply", "적용", 48), ("marker", "기호/유형", 105),
                                             ("fields", "변경 예정", 250), ("text", "문장 미리보기", 560)):
                    tree.heading(column, text=title)
                    tree.column(column, width=width, minwidth=45, stretch=column == "text", anchor="w")
                tree_scroll = ttk.Scrollbar(host, orient="vertical", command=tree.yview)
                tree.configure(yscrollcommand=tree_scroll.set)
                tree.pack(side="top", fill="both", expand=True)
                tree_scroll.place(in_=tree, relx=1.0, rely=0, relheight=1.0, anchor="ne")
                selected = {index for index, _ in 후보}

                def changed_fields(item):
                    fields = []
                    if item.get("font_runs"):
                        fields.append(f"글꼴 {len(item['font_runs'])}영역 → {item.get('font') or '판정 보류'}")
                    if item.get("size_runs"):
                        fields.append(f"크기 {len(item['size_runs'])}영역 → {item.get('size') / 100:g}pt")
                    if item.get("aside_runs"):
                        fields.append(f"괄호 {len(item['aside_runs'])}영역 → {item.get('aside_size') / 100:g}pt")
                    if item.get("marker_bold_runs"):
                        fields.append(f"문두 굵기 {len(item['marker_bold_runs'])}영역 → {'굵게' if item.get('marker_bold') else '보통'}")
                    if item.get("label_bold_runs"):
                        fields.append(f"라벨 굵기 {len(item['label_bold_runs'])}영역 → {'굵게' if item.get('label_bold') else '보통'}")
                    if item.get("hanging_mismatch"):
                        fields.append(f"내어쓰기 → {'적용' if item.get('expected_hanging') else '미적용'}")
                    return fields

                for index, item in 후보:
                    tree.insert("", "end", iid=str(index), values=("☑", f"{item['marker']} / {item['role']}",
                                ", ".join(changed_fields(item)), item.get("text", "").strip()))

                details = tk.Text(host, height=7, wrap="word", state="disabled")
                details.pack(fill="x", pady=(8, 0))

                def show_detail(_event=None):
                    current = tree.selection()
                    if not current:
                        return
                    index = int(current[0])
                    item = 계획[index]
                    lines = [f"항목기호: {item['marker']}   유형: {item['role']}   계층: {item['level']}",
                             "적용 예정: " + ("; ".join(changed_fields(item)) or "변경 없음"),
                             "문장 전체:", item.get("text", "").strip()]
                    details.configure(state="normal")
                    details.delete("1.0", "end")
                    details.insert("1.0", "\n".join(lines))
                    details.configure(state="disabled")

                def toggle(event):
                    if tree.identify_column(event.x) != "#1":
                        return
                    row = tree.identify_row(event.y)
                    if row:
                        index = int(row)
                        if index in selected:
                            selected.remove(index)
                            mark = "☐"
                        else:
                            selected.add(index)
                            mark = "☑"
                        values = list(tree.item(row, "values"))
                        values[0] = mark
                        tree.item(row, values=values)
                        count.set(f"선택 {len(selected)} / 후보 {len(후보)}개")

                tree.bind("<<TreeviewSelect>>", show_detail)
                tree.bind("<Button-1>", toggle, add="+")
                if 후보:
                    tree.selection_set(str(후보[0][0]))
                    show_detail()
                else:
                    ttk.Label(host, text="대표 서식과 다른 적용 영역이 없습니다. 문서는 변경하지 않습니다.").pack(anchor="w", pady=10)
                footer = ttk.Frame(host)
                footer.pack(fill="x", pady=(10, 0))
                count = tk.StringVar(value=f"선택 {len(selected)} / 후보 {len(후보)}개")
                ttk.Label(footer, textvariable=count).pack(side="left")

                def finish(approved):
                    요청["selected"] = sorted(selected) if approved else []
                    요청["approved"] = approved
                    요청["done"].set()
                    window.destroy()

                ttk.Button(footer, text="취소", command=lambda: finish(False)).pack(side="right")
                ttk.Button(footer, text="선택 영역만 적용", style="Primary.TButton",
                           command=lambda: finish(True)).pack(side="right", padx=(0, 8))
                window.protocol("WM_DELETE_WINDOW", lambda: finish(False))
                window.grab_set()
                self._검토창_앞으로(window)
                window.focus_set()

            def _서식통일_결과_확인창(self, 요청):
                if getattr(self.root, "_docfit_hidden_backend", False):
                    self._알림(messagebox.showinfo, "서식통일 결과", str(요청["payload"]))
                    요청["done"].set()
                    return
                result = 요청["payload"] or {}
                window = tk.Toplevel(self.root)
                window.title("서식통일 5/5 · 작업 결과 확인" + (f" · {result['file']}" if result.get("file") else ""))
                window.transient(self.root)
                window.geometry("760x560")
                window.minsize(600, 400)
                host = ttk.Frame(window, padding=16)
                host.pack(fill="both", expand=True)
                status = result.get("status", "error")
                status_text = {"passed": "검수 통과", "failed": "불일치 남음",
                               "incomplete": "일부 판정 보류", "error": "검수 오류",
                               "not_applicable": "검사할 문장 없음"}.get(status, status)
                ttk.Label(host, text=f"저장 결과 확인 · {status_text}",
                          font=("맑은 고딕", 15, "bold")).pack(anchor="w")
                ttk.Label(host, text=f"검사 문장 {result.get('checked', 0)}개 · 불일치 {len(result.get('issues', []))}개 · 판정 보류 그룹 {len(result.get('not_checkable', []))}개",
                          ).pack(anchor="w", pady=(5, 10))
                report = tk.Text(host, wrap="word", state="normal")
                report.pack(fill="both", expand=True)
                report.insert("end", "[남은 불일치]\n")
                for issue in result.get("issues", [])[:100]:
                    report.insert("end", f"• {issue.get('text', '')}\n  항목: {', '.join(issue.get('fields', []))}\n")
                if not result.get("issues"):
                    report.insert("end", "남은 불일치가 없습니다.\n")
                report.insert("end", "\n[판정 보류]\n")
                for group in result.get("not_checkable", [])[:100]:
                    report.insert("end", f"• {group.get('marker')} / {group.get('role')} — {', '.join(group.get('fields', []))}\n")
                if not result.get("not_checkable"):
                    report.insert("end", "판정 보류 그룹이 없습니다.\n")
                if result.get("error"):
                    report.insert("end", "\n오류: " + str(result["error"]))
                report.insert("end", "\n[대표값 미확정 문단 · 빨간색 표시]\n")
                for item in result.get("unresolved", []):
                    marked = "빨간 표시 확인" if item.get("red_marked") else "빨간 표시 미확인"
                    report.insert("end", f"• {item.get('text', '')}\n  미확정: {', '.join(item.get('fields', []))} · {marked}\n")
                report.configure(state="disabled")

                def finish():
                    요청["approved"] = True
                    요청["done"].set()
                    window.destroy()

                ttk.Button(host, text="결과 확인", style="Primary.TButton", command=finish).pack(anchor="e", pady=(10, 0))
                window.protocol("WM_DELETE_WINDOW", finish)
                # 작업은 이 창을 기다리지 않고 이어지므로 모달로 잡지 않는다(중단 단추·완료 안내를 막지 않게).
                self._검토창_앞으로(window)
                window.focus_set()

            def queue_처리(self):
                모인_로그 = []
                deadline = time.monotonic() + .012
                try:
                    for _ in range(150):
                        if time.monotonic() >= deadline:
                            break
                        item = gui_queue.get_nowait()
                        event = item[0]
                        if event in ("style_unify_profile_review", "style_unify_regions_review",
                                     "style_unify_result_review"):
                            try:
                                if event == "style_unify_profile_review":
                                    self._서식통일_대표서식_검토창(item[1])
                                elif event == "style_unify_regions_review":
                                    self._서식통일_적용영역_검토창(item[1])
                                else:
                                    self._서식통일_결과_확인창(item[1])
                            except Exception as exc:
                                로그(f"[서식통일] 사용자 확인창 오류: {exc}")
                                item[1]["approved"] = False
                                item[1]["selected"] = []
                                item[1]["done"].set()
                        elif event == "format_copied":
                            self._서식_복사완료(profile=item[1])
                        elif event == "document_review_done":
                            item[1](result=item[2], error=item[3])
                        elif event == "format_copy_error":
                            self._서식_복사완료(error=item[1])
                        elif event == "proofread_scan_done":
                            self._교정_작업중 = False
                            if getattr(self, "_교정_창", None) is not None:
                                self._교정_후보, self._교정_대상 = item[1], item[2]
                                self._교정_목록갱신()
                                self._교정_상태.set(f"교정 후보 {len(item[1])}개 표현 · 검사 실패 {len(item[3])}개 파일")
                                if item[3]:
                                    self._알림(messagebox.showwarning, APP_NAME, "검사하지 못한 파일:\n" + "\n".join(
                                        f"{Path(path).name}: {error}" for path, error in item[3]), parent=self._교정_창)
                        elif event == "proofread_apply_done":
                            self._교정_작업중 = False
                            if getattr(self, "_교정_창", None) is not None:
                                self._교정_상태.set(f"저장 완료 {len(item[1])}개 파일 · 실패 {len(item[2])}개")
                                details = "\n".join(f"{path} ({count}건 교정)" for path, count in item[1])
                                details += "\n" + "\n".join(f"실패: {Path(path).name}: {error}" for path, error in item[2])
                                self._알림(messagebox.showinfo, APP_NAME, details.strip() or "저장된 결과가 없습니다.", parent=self._교정_창)
                        elif event == "markdown_exported":
                            성공, 실패 = item[1], item[2]
                            for button in self.file_buttons:
                                button.config(state="normal")
                            for path in 성공:
                                self.로그표시(f"Markdown 저장 완료: {path}")
                            for source, error in 실패:
                                self.로그표시(f"Markdown 변환 실패: {source}\n{error}")
                            self.status_var.set(f"Markdown 변환 완료 · 성공 {len(성공)}개 / 실패 {len(실패)}개")
                            if 실패:
                                self._알림(messagebox.showwarning,
                                    APP_NAME,
                                    f"Markdown 변환을 마쳤습니다.\n\n성공: {len(성공)}개\n실패: {len(실패)}개\n처리 기록을 확인해 주세요.",
                                    parent=self.root,
                                )
                            else:
                                self._알림(messagebox.showinfo, APP_NAME, f"Markdown 파일 {len(성공)}개를 원본 폴더에 저장했습니다.", parent=self.root)
                        elif event == "log":
                            self.stage_board.signal()
                            모인_로그.append(str(item[1]))
                            continue
                        if 모인_로그:
                            self.로그_여러줄_표시(모인_로그)
                            모인_로그 = []

                        if event == "status":
                            self.stage_board.signal(item[1])
                            self.status_var.set(item[1])
                        elif event == "step":
                            self._단계_강조(item[1])
                        elif event == "step_reset":
                            self._단계_초기화()
                            self._안내키, self._안내지남 = None, set()
                        elif event == "guide":
                            key = 진행안내_키(item[1])
                            if key and key != self._안내키:
                                if self._안내키:
                                    self._안내지남.add(self._안내키)
                                self._안내키 = key
                        elif event == "doc_begin":
                            self._진행문서 = (int(item[1]), int(item[2]))
                        elif event == "progress":
                            pass  # 긴 진행 바는 없앴다. 단계 표시(LiveStageBoard)가 진행 상황을 보여 준다.
                        elif event == "saved":
                            self._결과목록.append({"원본": item[1], "결과": item[2], "쪽수": item[3]})
                        elif event == "document_error":
                            self._실패목록[str(item[1])] = str(item[2])
                            self.stage_board.finish("오류")
                            self.로그표시(f"문서 처리 실패: {item[1]}\n{item[2]}")
                        elif event == "file_conversion_stopped":
                            self._작업종료시각 = time.monotonic()
                            self.running = False
                            self._안내_설정(0)
                            self.버튼_대기중()
                            self.stage_board.finish("중단")
                            self.status_var.set(f"변환 중단 · 성공 {item[1]}개 / 실패 {item[2]}개")
                            if not self.closing:
                                self._알림(messagebox.showinfo, APP_NAME, self.status_var.get(), parent=self.root)
                        elif event == "file_conversion_finished":
                            self._작업종료시각 = time.monotonic()
                            self.running = False
                            self._안내_설정(0)
                            self.버튼_대기중()
                            self.stage_board.finish("완료" if item[2] == 0 else "오류")
                            if self._결과목록:
                                self.open_result_button.config(state="normal")
                                first = Path(self._결과목록[0]["결과"]).name
                                self.footer_note_var.set(f"[변환 결과] : {first} 외 {len(self._결과목록) - 1}개")
                                self.footer_note.configure(style="Result.TLabel")
                            self.status_var.set(f"변환 완료 · 성공 {item[1]}개 / 실패 {item[2]}개")
                            self.로그표시("=" * 45 + f"\n{self.status_var.get()}\n" + "=" * 45)
                            if not self.closing:
                                self._알림(messagebox.showinfo, APP_NAME, self.status_var.get(), parent=self.root)
                        elif event in ("stopped", "finished") and getattr(self, "_서식예시_작업", None):
                            self._서식예시_완료(item, 중단=event == "stopped")
                        elif event == "stopped":
                            self._작업종료시각 = time.monotonic()
                            self.running = False
                            self._안내_설정(0)
                            self.버튼_대기중()
                            self.stage_board.finish("중단")
                            완료수 = len(self._결과목록)
                            # 완료된 문서 수가 전체와 같으면(마지막 문서 저장 직후 중단) 더 이어갈 게 없다.
                            if 0 < 완료수 < len(self.files):
                                self._재개_대기중 = True
                                self._재개_시작_인덱스 = 완료수 + 1
                                self._재개_모드 = self._작업모드
                                안내 = f"작업이 중단되었습니다. ({완료수}/{len(self.files)}개 완료 — 실행을 누르면 이어서 진행합니다.)"
                            else:
                                self._재개_대기중 = False
                                안내 = "작업이 중단되었습니다."
                            self.status_var.set(안내)
                            self.로그표시("=" * 45 + f"\n{안내}\n" + "=" * 45)
                            if not self.closing:
                                self._알림(messagebox.showinfo, APP_NAME, 안내, parent=self.root)
                        elif event == "finished":
                            self._작업종료시각 = time.monotonic()
                            self.running = False
                            self._안내_설정(0)   # 작업이 끝나면 강조를 기본값으로 되돌린다.
                            self.버튼_대기중()
                            self.stage_board.finish("완료" if item[2] == 0 else "오류")
                            if self._안내키:
                                self._안내지남.add(self._안내키)
                            self._안내키 = "done" if item[2] == 0 else self._안내키
                            self._절약초 = None
                            self._작업결과_표시(item[2] == 0)
                            최종검수 = item[6] if len(item) >= 8 else None
                            if 최종검수:
                                self.status_var.set(
                                    f"처리 완료 · 수행 점수 {최종검수['score']:.1f}/100 · {최종검수['verdict']}"
                                )
                                self.stage_board.set_result_message(
                                    f"최종 검수: 수행 점수 {최종검수['score']:.1f}/100 · {최종검수['verdict']}"
                                )
                            else:
                                self.status_var.set(f"처리 완료 · 성공 {item[1]}개 / 실패 {item[2]}개")
                            self.로그표시("=" * 45 + f"\n작업 완료 - 성공 {item[1]}개 / 실패 {item[2]}개\n" + "=" * 45)
                            if not self.closing and not self.developer_mode_var.get():
                                # 개발자 모드가 꺼져 있으면 절약한 시간만 귀여운 검은 고양이와 함께 보여 준다(2026-10-11 사용자 요청).
                                # 자세한 완료 안내(성공·실패 건수·세부 작업·최종 검수)는 개발자 모드에서만 보인다.
                                self._절약_완료창(item[1], item[2])
                            elif not self.closing:
                                안내문 = f"문서 처리가 완료되었습니다.\n\n성공: {item[1]}개\n실패: {item[2]}개"
                                if len(item) >= 6:
                                    안내문 += (
                                        f"\n\n(세부 작업 항목 기준)\n"
                                        f"총 작업건수: {item[3]}건\n"
                                        f"성공: {item[4]}건\n"
                                        f"실패: {item[5]}건"
                                    )
                                if 최종검수:
                                    안내문 += (
                                        f"\n\n[목표 기준 최종 검수]\n"
                                        f"수행 점수: {최종검수['score']:.1f}/100 (규칙 준수율과 별도)\n"
                                        f"판정: {최종검수['verdict']}"
                                    )
                                    if 최종검수["blockers"]:
                                        안내문 += "\n확인사항: " + ", ".join(최종검수["blockers"])
                                    if item[7]:
                                        안내문 += f"\n보고서: {item[7]}"
                                    else:
                                        안내문 += "\n최종 검수 파일은 저장하지 않았습니다."
                                self._알림(messagebox.showinfo, APP_NAME, 안내문)
                        elif event == "fatal_error":
                            self.running = False
                            self._안내_설정(0)
                            self.버튼_대기중()
                            self.stage_board.finish("오류")
                            self.status_var.set("오류 발생 · 처리 기록을 확인해 주세요")
                            self.로그표시(f"치명적 오류:\n{item[1]}")
                            if not self.closing:
                                self._알림(messagebox.showerror, APP_NAME, f"작업 중 오류가 발생했습니다.\n\n{item[1]}")
                except queue.Empty:
                    pass
                except Exception as exc:
                    # 이벤트 하나의 UI 오류가 큐 polling 자체를 영구 중단하지 않게 한다.
                    진단로그(f"[GUI 이벤트] 처리 중 예외(다음 이벤트부터 계속): {exc}")

                if 모인_로그:
                    self.로그_여러줄_표시(모인_로그)

                try:
                    self._queue_after_id = self.root.after(20 if not gui_queue.empty() else 100, self.queue_처리)
                except tk.TclError:
                    pass

            def _루트_파괴시_예약취소(self, event):
                if event.widget is not self.root:
                    return
                job = getattr(self, "_queue_after_id", None)
                if job is not None:
                    try:
                        self.root.after_cancel(job)
                    except tk.TclError:
                        pass
                    self._queue_after_id = None

            def 종료(self):
                if self.closing:
                    return
                if self.running:
                    if not self._알림(messagebox.askyesno, APP_NAME, "현재 자간 조정 작업이 진행 중입니다.\n\n작업을 중단하고 종료하시겠습니까?"):
                        return
                    self.closing = True
                    중단_event.set()
                    self.status_var.set("프로그램 종료 처리 중...")
                    self.버튼_작업중()
                    self.worker_종료확인()
                    return
                self._비교창_분리_후_보존()
                self.root.destroy()

            def _비교창_분리_후_보존(self):
                원본_뷰어_분리()
                작업창_분리()

            def worker_종료확인(self):
                if self.worker is not None and self.worker.is_alive():
                    self.root.after(200, self.worker_종료확인)
                    return
                self._비교창_분리_후_보존()
                self.root.destroy()
        return bind_class(HwpAutoDocFitGUI, _docfit_namespace)
    if _docfit_symbol == '_새창_맨앞으로':
        def _새창_맨앞으로(event_or_window):
            """웹 화면 뒤에 설정·검토 창이 숨지 않도록 새로 뜬 Tk 창을 앞으로 올린다."""
            window = getattr(event_or_window, "widget", event_or_window)
            try:
                if window.winfo_toplevel() is not window or window.overrideredirect():
                    return
                window.lift()
                window.attributes("-topmost", True)
                window.after(300, lambda: window.winfo_exists() and window.attributes("-topmost", False))
                window.focus_force()
            except Exception:
                pass
        return bind_function(_새창_맨앞으로, _docfit_namespace)
    if _docfit_symbol == '웹모드_기본창_숨김':
        def 웹모드_기본창_숨김(root):
            """Flutter host: Tk owns only the hidden message pump and file dialogs."""
            root._docfit_min_size = root.minsize()
            root._docfit_hidden_backend = True
            root.withdraw()
        return bind_function(웹모드_기본창_숨김, _docfit_namespace)
    if _docfit_symbol == '웹모드_기본창_복원':
        def 웹모드_기본창_복원(root):
            """웹 화면을 쓸 수 없을 때 기존 Tk 화면을 정상 창으로 되돌린다."""
            root._docfit_hidden_backend = False
            root.maxsize(root.winfo_screenwidth(), root.winfo_screenheight())
            root.minsize(*(getattr(root, "_docfit_min_size", None) or (420, 400)))
            root.overrideredirect(False)
            root.attributes("-alpha", 1.0)
            root.geometry("1040x760")
            root.deiconify()
            root.lift()
        return bind_function(웹모드_기본창_복원, _docfit_namespace)
    raise KeyError(_docfit_symbol)
