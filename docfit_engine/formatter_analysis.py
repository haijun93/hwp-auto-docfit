"""서식 프로필·예시 분석과 내보내기 — formatter의 호환 전역으로 바인딩할 원본 정의."""

SYMBOLS = ('기본_서식프로파일', '서식프로파일_목록', '_제목뒤간격_다시재기', 'hwpx_서식_분석', '보고서머리_프로필_반영', '보고서머리_hwpx_처리', '예시문서_기본이름', '_분석본_보관', '한글파일_서식_분석', '교정용_hwpx_준비', '분석용_hwpx_준비', '스타일분석_파일생성', '스타일분석_요약', '서식프로파일_표시이름', '문서_markdown_내보내기')

def _install(*, _docfit_namespace, _docfit_symbol, bind_function):
    global 기본_서식프로파일, 서식프로파일_목록, _제목뒤간격_다시재기, hwpx_서식_분석, 보고서머리_프로필_반영, 보고서머리_hwpx_처리, 예시문서_기본이름, _분석본_보관, 한글파일_서식_분석, 교정용_hwpx_준비, 분석용_hwpx_준비, 스타일분석_파일생성, 스타일분석_요약, 서식프로파일_표시이름, 문서_markdown_내보내기
    if _docfit_symbol == '기본_서식프로파일':
        def 기본_서식프로파일():
            return {"version": 1, "name": "기본 보고서 서식",
                    "format": copy.deepcopy(_표준서식_설정_기본값),
                    "options": {k: copy.deepcopy(v) for k, v in 기본_설정.items()
                                if k.startswith("std_") or k in ("paren_shrink", "paren_label_bold", "label_symbols")}}
        return bind_function(기본_서식프로파일, _docfit_namespace)
    if _docfit_symbol == '서식프로파일_목록':
        def 서식프로파일_목록():
            result = {"": 기본_서식프로파일()}
            folder = 서식프로파일_폴더()
            if folder.exists():
                for path in sorted(folder.glob("*.json")):
                    try:
                        data = json.loads(path.read_text(encoding="utf-8"))
                        if data.get("version") != 1 or not isinstance(data.get("name"), str):
                            raise ValueError("지원하지 않는 서식 파일")
                        fmt = data["format"]
                        if not isinstance(fmt, dict) or not isinstance(data.get("options"), dict):
                            raise ValueError("잘못된 서식 데이터")
                        for key in _표준서식_설정_기본값:
                            if key not in fmt:
                                raise ValueError("필수 서식값 누락")
                        for rule in fmt["기호_규칙"]:
                            if len(rule) != 6 or not 0 < float(rule[3]) <= 1000:
                                raise ValueError("잘못된 글자 크기")
                        # 예전 서식(v4 이하)도 서식 요소 분석이 있으면 지금 복사 범위(계층 추가 서식·규칙)로 적용 값을
                        # 다시 만든다. 파일은 바꾸지 않는다(일반 표 서식처럼 예시가 다시 필요한 것은 예시를 다시 넣어야 함).
                        if data.get("element_analysis") and int(data.get("profile_version") or 0) < 5:
                            서식요소.apply_to_profile(data)
                        if int(data.get("gap_rev") or 0) < 2 and fmt.get("제목뒤_간격") is not None:
                            _제목뒤간격_다시재기(path, data)
                        if path.stem == 기본서식_덮어쓰기_식별자:
                            if 알파_서식예시폴더_사용:
                                result[""] = data        # 기본 서식 예시 파일을 고쳐 바뀐 기본 서식
                            continue
                        result[path.stem] = data
                    except Exception as exc:
                        if _콘솔_출력_가능:
                            print(f"서식 파일 제외: {path.name}: {exc}")
            return result
        return bind_function(서식프로파일_목록, _docfit_namespace)
    if _docfit_symbol == '_제목뒤간격_다시재기':
        def _제목뒤간격_다시재기(path, data):
            """예전 분석의 '제목·개요 표 아래~첫 문장 간격'을 서식예시 파일에서 다시 잰다(한 번만, 프로필 파일에 저장).

            예전 분석은 개요 상자와 첫 □ 사이의 중제목 표(Ⅰ 추진 배경)까지 간격으로 재어, 중제목 아래 첫 □의 문단 위
            간격이 31pt로 벌어졌다(사용자 신고, 2026-10-17, 기본 서식.hwpx). 예시 파일이 없으면 이 값만 버리고 기본
            문단 위 여백 규칙을 쓴다.
            """
            fmt = data["format"]
            표준 = path.stem == 기본서식_덮어쓰기_식별자
            예시 = 서식예시_폴더() / (서식예시모듈.STANDARD_FILE if 표준 else 서식예시모듈.file_name_for(data.get("name")))
            새값 = None
            try:
                if 예시.is_file():
                    새값 = (서식요소.analyze_format_elements(예시, 서식표_종류판별).get("spacing_rules") or {}).get(
                        "overview_to_first")
            except Exception as exc:
                진단로그(f"제목 아래 간격 다시 재기 실패(값을 버림): {path.name}: {exc}")
            if 새값 is None:
                fmt.pop("제목뒤_간격", None)
            else:
                fmt["제목뒤_간격"] = int(새값)
            data["gap_rev"] = 2
            try:
                임시 = path.with_suffix(".tmp")
                임시.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                os.replace(임시, path)
            except OSError as exc:
                진단로그(f"제목 아래 간격 보정 저장 실패(불러올 때마다 다시 보정): {path.name}: {exc}")
        return bind_function(_제목뒤간격_다시재기, _docfit_namespace)
    if _docfit_symbol == 'hwpx_서식_분석':
        def hwpx_서식_분석(path):
            """HWPX의 대표 페이지·문단·문자·표 서식을 분석해 재사용 프로필로 만든다."""
            profile = 기본_서식프로파일()
            fmt = profile["format"]
            def tag(e): return e.tag.rsplit("}", 1)[-1]
            def child(e, name):
                return next((x for x in e.iter() if tag(x) == name), None)
            with open_hwpx_safely(path) as z:
                header = safe_xml_fromstring(z.read("Contents/header.xml"))
                fonts = {}
                for face in header.iter():
                    if tag(face) == "fontface" and face.get("lang") == "HANGUL":
                        fonts.update({f.get("id"): f.get("face") for f in face if tag(f) == "font"})
                # 예시 글꼴의 형식(TTF·HFT)을 함께 남긴다. 한/글은 HFT 글꼴(HCI Poppy·한양중고딕 등)을 TTF로 지정하면
                # 오류 없이 무시하는데, 예전에는 서식통일 때만 형식을 읽어 서식 적용에서 예시 글꼴이 빠졌다(2026-10-04).
                fmt["글꼴형식"] = 글꼴형식_모으기(header)
                chars = {e.get("id"): e for e in header.iter() if tag(e) == "charPr"}
                paras = {e.get("id"): e for e in header.iter() if tag(e) == "paraPr"}
                groups = {r[0]: Counter() for r in fmt["기호_규칙"]}
                body_styles = Counter()
                first_styles = []
                ratios, spacing, letter_spacings = Counter(), Counter(), Counter()
                paragraphs = {k: Counter() for k in groups}
                marker_shapes = defaultdict(Counter)
                hierarchy_paragraphs = []
                aliases = {"ㅁ": "□", "○": "ㅇ", "☞": "ㅇ", "*": "※", "→": "※"}
                count = 0
                margins = False
                빈줄_종류 = []   # 본문 문단마다 blank·marker·other — 예시가 항목기호 문장 사이 빈 줄을 쓰는지 본다
                빈줄_줄간격 = Counter()   # 빈 줄의 줄 간격(%)은 본문과 따로 배운다
                별표_정렬표 = Counter()   # '*' 다음 '**' 문장: 둘째 별표를 첫째 별표 아래에 맞췄는지(앞 빈칸 한 칸 적음)
                앞_별표 = None
                부연_부모 = None
                부연_앞칸 = defaultdict(Counter)   # (위 문단 유형 또는 "", 부연설명 기호) → 앞 빈칸 수 빈도
                개체 = {"tbl", "pic", "rect", "ellipse", "line", "container", "equation", "ole", "polygon", "curve",
                      "arc", "textart", "connectLine"}
                sections = sorted((n for n in z.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)),
                                  key=lambda n: int(re.search(r"section(\d+)", n).group(1)))
                from docfit_core.marker_scheme import detect_scheme
                # 정리할 문서의 전역 체계와 분리하여 예시 자체의 최상위 문단에서 배운다.
                section_roots = {name: safe_xml_fromstring(z.read(name)) for name in sections}
                reference_scheme = detect_scheme(
                    "".join("".join(t.itertext()) for run in para if tag(run) == "run"
                            for t in run if tag(t) == "t")
                    for root in section_roots.values() for para in root if tag(para) == "p")
                for name in sections:
                    root = section_roots[name]
                    if not margins:
                        page = child(root, "pagePr")
                        m = child(page, "margin") if page is not None else None
                        if m is not None:
                            for key in fmt["여백_mm"]:
                                if m.get(key) is not None:
                                    fmt["여백_mm"][key] = round(float(m.get(key)) * 25.4 / 7200, 3)
                            margins = True
                    # section의 직접 자식 p만: 표 셀/각주 등의 중첩 문단을 섞지 않는다.
                    for para in root:
                        if tag(para) != "p": continue
                        runs = []
                        for run in para:
                            if tag(run) != "run": continue
                            text = "".join("".join(t.itertext()) for t in run if tag(t) == "t")
                            if text.strip(): runs.append((run, text))
                        text = "".join(t for _, t in runs).lstrip()
                        if any(tag(e) in 개체 for e in para.iter()):
                            빈줄_종류.append("other")
                        elif not text:
                            빈줄_종류.append("blank")
                            빈pp = paras.get(para.get("paraPrIDRef"))
                            빈ls = child(빈pp, "lineSpacing") if 빈pp is not None else None
                            if 빈ls is not None and 빈ls.get("type") == "PERCENT":
                                빈줄_줄간격[float(빈ls.get("value"))] += 1
                        else:
                            빈줄_종류.append("marker" if leading_marker(text, reference_scheme)[1] else "other")
                        if not text: continue
                        원문 = "".join(t for _, t in runs)
                        앞칸 = len(원문) - len(원문.lstrip())
                        if text.startswith("**") and 앞_별표 is not None:
                            별표_정렬표[앞칸 + 1 == 앞_별표] += 1
                        앞_별표 = 앞칸 if text.startswith("*") and not text.startswith("**") else (
                            앞_별표 if text.startswith("**") else None)
                        # 부연설명(*, **, ※) 앞 빈칸을 위 문단 유형별로 배운다(_부연설명_한문단과 같은 연결 규칙).
                        예시_기호, 예시_역할 = leading_marker(원문, reference_scheme)
                        유형 = {"소제목": "제목", "본문": "본문", "내용": "내용"}.get(예시_역할)
                        if 유형 is not None:
                            부연_부모 = 유형
                        elif _부연설명_문단인가(text):
                            부연_앞칸[(부연_부모 or "", "**" if text.startswith("**") else text[0])][앞칸] += 1
                        else:
                            부연_부모 = None
                        count += 1
                        mapped = reference_scheme.canonical(원문)
                        symbol = mapped[0] if mapped else aliases.get(text[0], text[0])
                        if reference_scheme and reference_scheme.is_excluded(원문):
                            symbol = ""
                        # 가장 긴 텍스트 런을 사용해 짧은 라벨 강조가 본문 서식을 압도하지 않도록 한다.
                        run, _ = max(runs, key=lambda item: len(item[1]))
                        char = chars.get(run.get("charPrIDRef"))
                        if char is None: continue
                        fontref = child(char, "fontRef")
                        font = fonts.get(fontref.get("hangul")) if fontref is not None else None
                        height = float(char.get("height", "0")) / 100
                        ratio = child(char, "ratio")
                        if ratio is not None: ratios[float(ratio.get("hangul", "100"))] += max(1, len(text))
                        letter_spacing = child(char, "spacing")
                        if letter_spacing is not None and letter_spacing.get("hangul") is not None:
                            # 예전에는 문단마다 덮어써 마지막 문단의 자간이 기본 자간이 됐다(2026-10-04 수정).
                            try: letter_spacings[float(letter_spacing.get("hangul"))] += max(1, len(text))
                            except (TypeError, ValueError): pass
                        pp = paras.get(para.get("paraPrIDRef"))
                        ls = child(pp, "lineSpacing") if pp is not None else None
                        if ls is not None and ls.get("type") == "PERCENT":
                            spacing[float(ls.get("value"))] += max(1, len(text))
                        bold = child(char, "bold") is not None
                        pm = child(pp, "margin") if pp is not None else None
                        def margin_value(key):
                            item = child(pm, key) if pm is not None else None
                            return int(item.get("value", "0")) if item is not None and item.get("unit", "HWPUNIT") == "HWPUNIT" else 0
                        hierarchy_paragraphs.append({"text": 원문, "font": font,
                                                     "size_pt": height, "left": margin_value("left"),
                                                     "indent": margin_value("intent"),
                                                     "prev_spacing": margin_value("prev")})
                        detected_marker, detected_role = 예시_기호, 예시_역할
                        if detected_marker and font and height > 0:
                            marker_shapes[(detected_role, detected_marker)][(font, height, bold)] += 1
                        if font and height > 0:
                            body_styles[(font, height, bold)] += max(1, len(text))
                            if len(first_styles) < 2:
                                first_styles.append((font, height, bold))
                        if symbol not in groups or not font or height <= 0: continue
                        groups[symbol][(font, height, bold)] += 1
                        if pp is not None:
                            pm = child(pp, "margin")
                            vals = {}
                            if pm is not None:
                                for xmlkey, key in (("left", "LeftMargin"), ("right", "RightMargin"),
                                                    ("intent", "Indentation"), ("prev", "PrevSpacing"), ("next", "NextSpacing")):
                                    e = child(pm, xmlkey)
                                    if e is not None and e.get("unit", "HWPUNIT") == "HWPUNIT":
                                        vals[key] = int(e.get("value", "0"))
                            if ls is not None and ls.get("type") == "PERCENT":
                                vals["LineSpacingType"] = 0
                                vals["LineSpacing"] = int(float(ls.get("value")))
                            paragraphs[symbol][tuple(sorted(vals.items()))] += 1
                # 첫 표의 첫 행과 나머지 행에서 대표 문자 서식을 추출한다. 일반 본문이
                # 없는 표 전용 문서는 표 본문(없으면 머리글)을 대표 본문 대체값으로 쓴다.
                # 글이 있는 첫 표를 쓴다. 빈 테두리 표(1칸 틀 등)가 맨 앞에 있는 서식은 예전에 첫 표만 보다가
                # '복제할 문자 서식이 없다'며 서식 등록이 실패했다(범정부오피스 용인 쪽지 서식, 2026-10-04).
                table_header_styles, table_body_styles = Counter(), Counter()
                for name in sections:
                    root = safe_xml_fromstring(z.read(name))
                    for table in (e for e in root.iter() if tag(e) == "tbl"):
                        rows = [e for e in table.iter() if tag(e) == "tr"]
                        for row_index, row in enumerate(rows):
                            counter = table_header_styles if row_index == 0 else table_body_styles
                            for run in (e for e in row.iter() if tag(e) == "run"):
                                text = "".join("".join(t.itertext()) for t in run if tag(t) == "t").strip()
                                char = chars.get(run.get("charPrIDRef"))
                                if not text or char is None:
                                    continue
                                fontref = child(char, "fontRef")
                                font = fonts.get(fontref.get("hangul")) if fontref is not None else None
                                height = float(char.get("height", "0")) / 100
                                if font and height > 0:
                                    counter[(font, height, child(char, "bold") is not None)] += len(text)
                        if table_header_styles or table_body_styles:
                            break
                    if table_header_styles or table_body_styles:
                        break
                본문_대체출처 = None
                if not body_styles:
                    fallback_styles = table_body_styles or table_header_styles
                    if not fallback_styles:
                        raise ValueError("본문 또는 표 셀에서 복제할 수 있는 문자 서식을 찾지 못했습니다. "
                                         "글이 없는 문서(그림·워터마크만 있는 문서)는 서식 예시로 쓸 수 없습니다. "
                                         "글이 들어 있는 예시 보고서를 넣어 주세요.")
                    body_styles.update(fallback_styles)
                    본문_대체출처 = "표 본문 셀" if table_body_styles else "표 머리글 셀"
                if ratios: fmt["기본_장평"] = ratios.most_common(1)[0][0]
                if letter_spacings: fmt["기본_자간"] = letter_spacings.most_common(1)[0][0]
                if spacing: fmt["기본_줄간격_퍼센트"] = spacing.most_common(1)[0][0]
                if 빈줄_줄간격: fmt["빈줄_줄간격_퍼센트"] = 빈줄_줄간격.most_common(1)[0][0]
                if 별표_정렬표: fmt["별표_정렬"] = 별표_정렬표.most_common(1)[0][0]
                if 부연_앞칸:
                    배운표 = {}
                    for (부모, 기호), 빈도 in 부연_앞칸.items():
                        배운표.setdefault(부모, {})[기호] = 빈도.most_common(1)[0][0]
                    fmt["부연설명_앞빈칸"] = 배운표
                if first_styles:
                    font, size, bold = first_styles[0]
                    fmt["제목_문단"] = {"font": font, "size_pt": size, "bold": bold}
                if len(first_styles) > 1:
                    font, size, bold = first_styles[1]
                    fmt["일자담당자_문단"] = {"font": font, "size_pt": size, "bold": bold}
                fmt["복사_문단모양"] = {}
                found, missing = [], []
                for i, rule in enumerate(fmt["기호_규칙"]):
                    symbol = rule[0]
                    if groups[symbol]:
                        font, size, bold = groups[symbol].most_common(1)[0][0]
                        fmt["기호_규칙"][i] = (symbol, rule[1], font, size, bold, False)
                        key = {"□": "box", "ㅇ": "o", "-": "dash", "※": "note"}.get(symbol)
                        if key:
                            profile["options"][f"std_symbol_{key}_bold"] = bold
                        if paragraphs[symbol]:
                            fmt["복사_문단모양"][symbol] = dict(paragraphs[symbol].most_common(1)[0][0])
                        found.append(f"{symbol}: {font} {size:g}pt, 굵게 {'ON' if bold else 'OFF'}")
                    else: missing.append(symbol)
                대표폰트, 대표크기, 대표굵게 = body_styles.most_common(1)[0][0]
                fmt["본문_문단"] = {"font": 대표폰트, "size_pt": 대표크기, "bold": 대표굵게}
                # 기본 프로필은 기존처럼 일반 본문을 보존한다. 분석해서 만든 프로필만
                # 대표 본문 글꼴·크기를 일반 문단에도 적용한다.
                fmt["복제_본문서식"] = True

                section_payloads = {name: z.read(name) for name in sections}
                profile["precise_tables"] = _정밀표_프로필_추출(header, section_payloads)
                # 서식 요소 전수 분석: 항목기호 문장은 계층별로, 제목·개요·중제목·붙임 표는 칸(A1·A2·B2 …)별로
                # 모든 글자·문단·칸 요소의 대표값을 구하고, 서식 표는 예시로 보관해 서식 적용에 쓴다.
                # 사용자는 서식 세부사항 창에서 대표값을 고칠 수 있다.
                요소분석 = 서식요소.analyze_format_elements(path, 서식표_종류판별)
                # 일반 표 서식은 데이터 표(본문이 시작된 뒤의 격자 표, 제목처럼 큰 글자 없음)에서만 배운다. 문서 머리의
                # 결재란·보도자료 머리·보고자 표는 데이터 표가 아니라 그 서식을 정리할 문서의 표에 입히지 않는다. 표 머리글·본문
                # 글자(table_format)도 apply_to_profile이 데이터 표 대표값으로만 채우고, 데이터 표가 없으면 기본 표 서식을
                # 쓴다(2026-10-04 범정부오피스 서식 시험). 예전에는 첫 표(문서 머리 표가 흔함)의 글자를 썼다.
                데이터표 = 요소분석.get("tables", {})
                # 데이터 표 가운데 일반 표 대표값과 가장 많이 같은 표에서 기본 표 서식을 배운다(같으면 칸이 많은 표).
                # 예전처럼 칸이 가장 많은 표에서 배우면 모양이 다른 표 하나의 서식이 모든 일반 표에 퍼졌다.
                표번호 = set(데이터표.get("data_tables", []))
                일반표들 = [t for 번호, t in enumerate(서식요소.top_level_tables(
                              safe_xml_fromstring(section_payloads[name]) for name in sections), 1) if 번호 in 표번호]
                if 일반표들:
                    대표_일반표 = 요소분석.get("tables", {})
                    기준표 = max(일반표들, key=lambda t: (서식요소.general_table_agreement(t, header, 대표_일반표),
                                                     len(제목_셀들(t))))
                    try:
                        profile["table_style"] = 표서식_한표학습(header, 기준표, Path(path).name)
                    except ValueError as exc:
                        로그(f"예시 보고서의 일반 표 서식을 배우지 못했습니다(준말 '표' 서식을 씁니다): {exc}")
                profile["style_hierarchy"] = analyze_hierarchy(hierarchy_paragraphs)
                fmt["논리역할_규칙"] = {}
                for item in profile["style_hierarchy"]["styles"]:
                    role, marker = item["role"], item["marker"]
                    if role not in ("장", "중제목", "소제목", "본문", "내용", "부연설명") or marker == "(없음)":
                        continue
                    shape = marker_shapes.get((role, marker))
                    font, size, bold = shape.most_common(1)[0][0] if shape else (item["font"], item["size_pt"], False)
                    if not font or not size:
                        continue
                    if role == "장":
                        # 장 문두(제1장·제2장 …)는 문서마다 달라 기호 규칙에 넣지 않고 역할 규칙 '(장)'으로 둔다.
                        fmt["논리역할_규칙"].setdefault("장", ("(장)", 0, font, size, bold, False))
                        fmt["복사_문단모양"].setdefault("(장)", {
                            "LeftMargin": item["left_hwpunit"],
                            "Indentation": item["first_line_hwpunit"],
                            "PrevSpacing": item["prev_spacing_typical"] or 0,
                        })
                        continue
                    rule = (marker, 0, font, size, bold, False)
                    fmt["논리역할_규칙"].setdefault(role, rule)
                    if marker not in {r[0] for r in fmt["기호_규칙"]}:
                        fmt["기호_규칙"].append(rule)
                    fmt["복사_문단모양"].setdefault(marker, {
                        "LeftMargin": item["left_hwpunit"],
                        "Indentation": item["first_line_hwpunit"],
                        "PrevSpacing": item["prev_spacing_typical"] or 0,
                    })
                fmt["복제_들여쓰기_유지"] = True
                # 빈 줄(간격용 줄)의 모양을 자리별로 배운다(docfit_core.blank_lines).
                from docfit_core import blank_lines
                빈줄 = blank_lines.learn(header, [safe_xml_fromstring(section_payloads[n]) for n in sections], 서식표_종류판별)
                if 빈줄:
                    fmt["빈줄_서식"] = 빈줄
                # 항목기호 문장 안 강조 낱말(일부 낱말만 굵게·다른 글꼴)도 배운다(docfit_core.emphasis, 2026-10-16 사용자 결정).
                from docfit_core import emphasis
                강조 = emphasis.learn(header, [safe_xml_fromstring(section_payloads[n]) for n in sections])
                if 강조:
                    fmt["강조_낱말"] = 강조
                profile["profile_version"] = 5
                profile["gap_rev"] = 2        # 제목 아래 간격을 중제목 표를 건너 재지 않는 분석(2026-10-17)
                profile["storage_format"] = "json"
                profile["source"] = {"filename": Path(path).name, "paragraphs_analyzed": count,
                                     "body_style_fallback": 본문_대체출처}
                profile["options"]["symbol_fonts"] = {
                    rule[0]: {"font": rule[2], "size": str(rule[3])} for rule in fmt["기호_규칙"]
                }
                # 복사한 글자 강조/문단 여백을 다른 후처리로 덮지 않는다.
                profile["options"].update(paren_shrink=False, paren_label_bold=False,
                                           std_hanging_indent=False, std_supplement_indent=False)
                # 예시가 항목기호 문장 사이(또는 문서 끝)에 빈 줄을 두었으면 그 빈 줄도 서식이다. 빈 줄 삭제를 켜 두면
                # 예시 자신에 서식을 입혀도 빈 줄이 사라져 원본과 달라졌다(서식 재연 시험, 2026-10-16).
                if 항목기호문장_사이_빈문단_찾기(빈줄_종류):
                    profile["options"]["std_remove_blank_lines"] = False
                profile["form_tables"] = dict(요소분석.pop("samples"))
                # 중제목을 표 첫 칸의 로마자 숫자로 쓴 문서도 중제목(3단계)이 있는 것으로 보고 문서 유형(A·B·C형)을 정한다.
                profile["style_hierarchy"]["document_type"] = 문서유형_판정(
                    profile["style_hierarchy"]["role_sequence"],
                    any(k.startswith("midtitle") for k in profile["form_tables"]))
                profile["element_analysis"] = 요소분석
                서식요소.apply_to_profile(profile)
                # 항목기호 없는 개요 상자 글의 괄호 줄임도 예시에서 배운다(무기호 문단 '' 계층).
                개요_줄임 = emphasis.overview_paren_delta(header, [safe_xml_fromstring(section_payloads[n]) for n in sections],
                                                       서식표_종류판별)
                if 개요_줄임 is not None:
                    fmt.setdefault("괄호_축소_기호별", {})[""] = 개요_줄임
                머리요약 = 보고서머리_프로필_반영(z, profile)
                표글자 = profile.get("table_format") or {}
                profile["summary"] = (
                    f"대표 본문: {대표폰트} {대표크기:g}pt, 굵게 {'ON' if 대표굵게 else 'OFF'}\n"
                    + (f"대표 본문 대체 분석: {본문_대체출처}\n" if 본문_대체출처 else "")
                    + ("\n".join(found) + "\n" if found else "")
                    + "미검출 기호(기본값 유지): " + (", ".join(missing) or "없음")
                    + (f"\n표 머리글: {표글자.get('header_font')} {float(표글자.get('header_size') or 0):g}pt / "
                       f"표 본문: {표글자.get('body_font')} {float(표글자.get('body_size') or 0):g}pt"
                       if 표글자.get("header_font") or 표글자.get("body_font")
                       else "\n표 머리글·본문: 예시에 데이터 표가 없어 기본 표 서식을 씁니다")
                    + f"\n정밀 표 프로필: {len(profile['precise_tables']['tables'])}개"
                    + (f"\n일반 표 서식: {표서식_설명(profile['table_style'])}" if profile.get("table_style") else "")
                    + (f"\n서식 표 예시: {', '.join(서식요소.FORM_LABELS[k] for k in profile['form_tables'])}"
                       if profile["form_tables"] else "")
                    + (f"\n{머리요약}" if 머리요약 else "")
                    + "\n\n" + hierarchy_summary(profile["style_hierarchy"])
                    + "\n페이지 여백·장평·자간·줄간격·문단 모양과 셀별 표 서식을 함께 복제합니다."
                )
                return profile
        return bind_function(hwpx_서식_분석, _docfit_namespace)
    if _docfit_symbol == '보고서머리_프로필_반영':
        def 보고서머리_프로필_반영(z, profile):
            """예시 HWPX의 보고서 머리(제목·보고 주체·개요) 구성을 프로필에 저장하고 요약 글을 돌려준다.

            예전에는 '표 밖 첫 두 문단'을 제목·일자담당자로 보아, 제목이 표(1×1 상자) 안에 있는 중앙부처 보고서에서
            작성일 줄을 제목으로, 개요를 일자담당자로 잘못 잡았다(korean-report-hwpx 129종 실측, 2026-10-10).
            """
            try:
                names = sorted((n for n in z.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)),
                               key=lambda n: int(re.search(r"section(\d+)", n).group(1)))
                header_root = safe_xml_fromstring(z.read("Contents/header.xml"))
                spec = 보고서머리.build_spec(header_root, safe_xml_fromstring(z.read(names[0])))
            except Exception as exc:
                로그(f"보고서 머리 분석 실패(무시): {exc}")
                return ""
            if not spec:
                return ""
            profile["report_header"] = spec
            fmt = profile["format"]
            title = spec["title"]
            if title.get("char", {}).get("font"):
                fmt["제목_문단"] = {"font": title["char"]["font"], "size_pt": title["char"]["size_pt"],
                                  "bold": bool(title["char"].get("bold"))}
            문단정보 = [i for i in spec["info"] if i["container"] == "paragraph"]
            if 문단정보 and 문단정보[0].get("char", {}).get("font"):
                c = 문단정보[0]["char"]
                fmt["일자담당자_문단"] = {"font": c["font"], "size_pt": c["size_pt"], "bold": bool(c.get("bold"))}
            담는곳 = {"paragraph": "상자 없는 제목 문단"}.get(title["container"]) or (
                title["container"].replace("table", "").replace("x", "×") + " 제목 표")
            줄 = [f"보고서 머리: {담는곳} ({title['char'].get('font')} {title['char'].get('size_pt', 0):g}pt, "
                 f"{_정렬이름.get(title.get('align'), title.get('align') or '-')})"]
            for i in spec["info"]:
                위치 = "제목 표 칸" if i["container"] == "cell" else ("제목 위 문단" if i.get("position") == "before_title" else "제목 아래 문단")
                줄.append(f"보고 주체({위치}): {i['text']}  → 틀 {i['template']}")
            if spec.get("overview"):
                줄.append("개요 상자: 있음(예시 상자 서식으로 복사)")
            return "\n".join(줄)
        return bind_function(보고서머리_프로필_반영, _docfit_namespace)
    if _docfit_symbol == '보고서머리_hwpx_처리':
        def 보고서머리_hwpx_처리(source, target=None, selections=None):
            """서식 프로필의 보고서 머리(제목·보고 주체·개요) 구성과 표기 방식을 대상 문서에 옮긴다(알파, 2026-10-10).

            대상의 제목 글·개요 글은 그대로 두고, 날짜·기관·부서·담당자 값은 예시의 표기 틀로 다시 쓴다.
            제목 표 안 날짜 칸은 한 줄로 입력(lineWrap=SQUEEZE)으로 둔다.
            """
            spec = 활성_머리서식_프로필 if 알파_머리서식복사_사용 else None
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            names = sorted((n for n in contents if re.fullmatch(r'Contents/section\d+\.xml', n)),
                           key=lambda n: int(re.search(r'section(\d+)', n).group(1)))
            first = names[0] if names else None
            def 시작들(root):
                # 여러 보고서를 묶은 문서: 보고서마다(제목 표마다) 머리를 맞춘다. 제목 표는 서식 적용과 같은 판정을 쓴다.
                tables = [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']
                제목표 = {id(tables[i]) for i, _ in 제목_대상찾기(root, header) if i < len(tables)}
                return 보고서머리.report_starts(root, lambda t: id(t) in 제목표)

            if selections is None:
                if not spec or first is None:
                    return {}
                root = safe_xml_fromstring(contents[first])
                found = [i for i in 시작들(root) if 보고서머리.analyze(header, root, i)["title"]]
                if len(found) > 1 and (spec.get("title") or {}).get("container") == "paragraph":
                    # 여러 보고서를 묶은 문서는 제목 표가 보고서 경계다(쪽 맞춤·쪽 나누기). 예시 제목이 상자 없는 문단이면
                    # 경계를 잃으므로 머리 서식 복사를 하지 않는다(2026-10-10).
                    로그(f"보고서 머리 서식 복사: 건너뜀(보고서 {len(found)}개 문서에 문단 제목 서식을 쓰면 보고서 경계가 사라짐)")
                    return {first: []}
                return {first: found}
            if not spec or not any(selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            root = safe_xml_fromstring(contents[first])
            본문폭 = _구역_본문폭(root, None)
            합계 = Counter()
            병합 = {}

            def 한번_병합(h, sample_header):
                # 보고서가 여러 개여도 예시 서식 정의는 문서 header에 한 번만 더한다.
                if 'maps' not in 병합:
                    병합['maps'] = 제목_참조병합(h, sample_header)
                return 병합['maps']

            # 뒤 보고서부터 바꿔 앞 보고서의 문단 번호가 흔들리지 않게 한다.
            for start in sorted(시작들(root), reverse=True):
                통계 = 보고서머리.apply_header(header, root, spec, 한번_병합, start=start,
                                           fit_table=(lambda t: _서식표_가로맞춤(t, 본문폭, 비례=True)) if 본문폭 else None)
                합계.update({k: v for k, v in 통계.items() if isinstance(v, int)})
            if not 합계.get("applied"):
                로그("보고서 머리 서식 복사: 바꿀 머리 없음")
                shutil.copyfile(source, target)
                return 0
            contents[first] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"보고서 머리 서식 복사: 보고서 {합계['applied']}개 · 제목 {합계['title']}·보고 주체 {합계['info']}·개요 "
                 f"{합계['overview']}개를 예시 구성으로 맞춤(날짜 칸 한 줄 {합계['squeezed']}개)")
            return 합계['applied']
        return bind_function(보고서머리_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '예시문서_기본이름':
        def 예시문서_기본이름(문단들):
            """직접 편집한 예시 문서의 기본 서식 이름: 첫 문장의 앞 8글자(TODO 6순위).

            첫 번째 비어 있지 않은 문단을 첫 문장으로 보고, 항목기호(□·ㅇ·- 등)와 앞 공백은
            빼며 첫 마침표(. ! ?) 앞까지만 쓴다. 쓸 글자가 없으면 '새 서식'.
            """
            for text in 문단들:
                body = (text or "").strip()
                if not body:
                    continue
                marker_end = 문장부호_마커_끝위치(body)
                if marker_end:
                    body = body[marker_end:].strip()
                끝 = re.search(r"[.!?。]", body)
                if 끝:
                    body = body[:끝.start()]
                body = re.sub(r"\s+", " ", body).strip()
                if body:
                    return body[:8].strip()
            return "새 서식"
        return bind_function(예시문서_기본이름, _docfit_namespace)
    if _docfit_symbol == '_분석본_보관':
        def _분석본_보관(hwpx, 보관):
            """분석한 HWPX를 서식예시 폴더에 넣을 수 있게 보관 경로로 복사한다(보관이 없으면 하지 않음)."""
            if 보관:
                Path(보관).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(hwpx, 보관)
        return bind_function(_분석본_보관, _docfit_namespace)
    if _docfit_symbol == '한글파일_서식_분석':
        def 한글파일_서식_분석(path, 보관=None):
            """예시 문서(HWP·HWPX·PDF)를 분석한다. 보관을 주면 분석한 HWPX를 그 경로에 복사한다(서식예시 폴더용)."""
            if Path(path).suffix.lower() == ".hwpx":
                _분석본_보관(path, 보관)
                return hwpx_서식_분석(path)
            if Path(path).suffix.lower() == ".pdf":
                # PDF 예시: kordoc으로 HWPX를 만든 뒤 PDF 서식을 옮겨 심고 분석한다(원본은 읽기만 함).
                with tempfile.TemporaryDirectory(prefix="pdf_format_") as folder:
                    target = Path(folder) / "source.hwpx"
                    외부문서_hwpx로_변환(Path(path), ".pdf", target)
                    _분석본_보관(target, 보관)
                    return hwpx_서식_분석(target)
            # 원본을 복사한 뒤 독립 한글 인스턴스에서 임시 HWPX로 변환한다.
            with tempfile.TemporaryDirectory(prefix="hwp_format_") as folder:
                source = Path(folder) / "source.hwp"
                target = Path(folder) / "source.hwpx"
                shutil.copy2(path, source)
                app = None
                pythoncom.CoInitialize()
                try:
                    보안모듈_초기화()
                    app = 한글_COM_인스턴스_생성(독립=True)
                    if not app.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE):
                        raise RuntimeError("한글 보안 모듈을 등록하지 못했습니다.")
                    if not 한글_문서_열기(app, source, "HWP"):
                        raise RuntimeError("한글파일을 열지 못했습니다.")
                    if not app.SaveAs(str(target), "HWPX", ""):
                        raise RuntimeError("HWPX 변환 실패. 한글에서 HWPX로 저장한 파일을 선택해 주세요.")
                    _분석본_보관(target, 보관)
                    return hwpx_서식_분석(target)
                finally:
                    if app is not None:
                        try: app.Quit()
                        except Exception: pass
                    pythoncom.CoUninitialize()
        return bind_function(한글파일_서식_분석, _docfit_namespace)
    if _docfit_symbol == '교정용_hwpx_준비':
        def 교정용_hwpx_준비(path, folder):
            """Return an HWPX snapshot; HWP conversion touches only a temporary copy."""
            source = Path(path)
            if source.suffix.lower() == ".hwpx":
                return source
            copied = Path(folder) / (uuid.uuid4().hex + ".hwp")
            target = copied.with_suffix(".hwpx")
            shutil.copy2(source, copied)
            app = None
            pythoncom.CoInitialize()
            try:
                보안모듈_초기화()
                app = 한글_COM_인스턴스_생성(독립=True)
                if not app.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE):
                    raise RuntimeError("한글 보안 모듈을 등록하지 못했습니다.")
                if 한글_문서_열기(app, copied, "HWP") is False:
                    raise RuntimeError("HWP 파일을 열지 못했습니다.")
                if app.SaveAs(str(target), "HWPX", "") is False:
                    raise RuntimeError("HWPX 임시 변환에 실패했습니다.")
                return target
            finally:
                if app is not None:
                    try: app.Quit()
                    except Exception: pass
                pythoncom.CoUninitialize()
        return bind_function(교정용_hwpx_준비, _docfit_namespace)
    if _docfit_symbol == '분석용_hwpx_준비':
        def 분석용_hwpx_준비(path, folder):
            """분석할 HWPX 스냅숏. 확장자만 .hwpx인 HWP(ZIP이 아님)도 HWP로 보고 임시 변환한다."""
            source = Path(path)
            if source.suffix.lower() == ".hwpx" and not zipfile.is_zipfile(source):
                copied = Path(folder) / (uuid.uuid4().hex + ".hwp")
                shutil.copy2(source, copied)
                source = copied
            return 교정용_hwpx_준비(source, folder)
        return bind_function(분석용_hwpx_준비, _docfit_namespace)
    if _docfit_symbol == '스타일분석_파일생성':
        def 스타일분석_파일생성(경로):
            """문서 스타일 전수 분석 보고서(.md)와 예시 서식 HWPX를 원본 옆에 만든다(A3).

            HWP는 원본을 건드리지 않고 임시 사본을 HWPX로 바꿔 분석한다.
            """
            source = Path(경로)
            with tempfile.TemporaryDirectory(prefix="docfit_inventory_") as folder:
                snapshot = 분석용_hwpx_준비(source, folder)
                inventory = analyze_style_inventory(snapshot)
                inventory["source"] = source.name
                report = source.with_name(f"{source.stem}_스타일분석.md")
                sample = source.with_name(f"{source.stem}_서식예시.hwpx")
                report.write_text(inventory_markdown(inventory), encoding="utf-8")
                stats = build_style_sample(snapshot, sample, inventory)
            return inventory, stats, report, sample
        return bind_function(스타일분석_파일생성, _docfit_namespace)
    if _docfit_symbol == '스타일분석_요약':
        def 스타일분석_요약(inventory, stats, report, sample):
            s = inventory["summary"]
            줄 = [f"문자 모양 {s['chars_used']}/{s['chars_defined']} · 문단 모양 {s['paras_used']}/{s['paras_defined']} "
                 f"· 본문 스타일 유형 {s['types']} · 표 {s['table_types']}종 · 글자 음영색 {s['shade_colors']}",
                 f"예시 서식: 본문 {stats['paragraphs']}문단, 표 {stats['tables']}개", "",
                 f"보고서: {report}", f"예시 서식: {sample}", ""]
            for t in inventory["types"]:
                c = inventory["definitions"]["chars"].get(t["main_char"]) or {}
                효과 = ", ".join(t["effects"]) or "-"
                줄.append(f"{t['marker']:>4}  {c.get('font', {}).get('hangul')} {c.get('size_pt', 0):g}pt"
                         f"{' 굵게' if c.get('bold') else ''} · {t['count']}문단 · 부분 서식: {효과}")
            return "\n".join(줄)
        return bind_function(스타일분석_요약, _docfit_namespace)
    if _docfit_symbol == '서식프로파일_표시이름':
        def 서식프로파일_표시이름(profile):
            """서식 목록에 보일 이름. 기관을 지정한 서식은 '[기관] 이름'."""
            기관 = str(profile.get("organization") or "").strip()
            return f"[{기관}] {profile['name']}" if 기관 else profile["name"]
        return bind_function(서식프로파일_표시이름, _docfit_namespace)
    if _docfit_symbol == '문서_markdown_내보내기':
        def 문서_markdown_내보내기(path):
            """HWP/HWPX를 같은 이름의 UTF-8 Markdown 파일로 내보낸다."""
            source = Path(path)
            target = source.with_suffix(".md")
            if source.suffix.lower() == ".hwpx":
                validate_hwpx(source)
                return export_markdown(source, target)
            if source.suffix.lower() != ".hwp":
                raise ValueError("HWP 또는 HWPX 문서만 Markdown으로 내보낼 수 있습니다.")

            with tempfile.TemporaryDirectory(prefix="hwp_markdown_") as folder:
                copied = Path(folder) / "source.hwp"
                snapshot = Path(folder) / "source.hwpx"
                shutil.copy2(source, copied)
                app = None
                pythoncom.CoInitialize()
                try:
                    보안모듈_초기화()
                    app = 한글_COM_인스턴스_생성(독립=True)
                    if not app.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE):
                        raise RuntimeError("한글 보안 모듈을 등록하지 못했습니다.")
                    if not 한글_문서_열기(app, copied, "HWP"):
                        raise RuntimeError("한글파일을 열지 못했습니다.")
                    if not app.SaveAs(str(snapshot), "HWPX", ""):
                        raise RuntimeError("Markdown 변환용 HWPX 스냅샷을 만들지 못했습니다.")
                    return export_markdown(snapshot, target)
                finally:
                    if app is not None:
                        try:
                            app.Quit()
                        except Exception:
                            pass
                    pythoncom.CoUninitialize()
        return bind_function(문서_markdown_내보내기, _docfit_namespace)
    raise KeyError(_docfit_symbol)
