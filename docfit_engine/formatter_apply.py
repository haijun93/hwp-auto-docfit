"""표준서식·문자/문단 적용 및 XML 선행 처리 — formatter의 호환 전역으로 바인딩할 원본 정의."""

SYMBOLS = ('_표준서식_문단위간격_표', '기본_계층_스타일', '표준서식_문단위간격_찾기', '기호글꼴_적용', '표글꼴_적용', '복사_문단모양_적용', '계층_추가서식_값', '복사_간격_규칙_적용', '계층_추가서식_적용', '빈줄서식_hwpx_처리', '개요첫칸_hwpx_처리', '강조낱말_hwpx_처리', '_문단_일반글', '_문단_준말_판별', '_문단_준말_제외사유', '_문단_글_바꾸기', '준말_hwpx_처리', '연결부호탭_hwpx_처리', '콜론라벨_hwpx_처리', '준말_사용표_만들기', '준말_선행적용', '_위첨자_글자모양', '_문단_별표_대상', '별표위첨자_hwpx_처리', '별표위첨자_선행적용', '_한글_글꼴표', '_글꼴_확보', '_글자모양_글꼴크기', '_본문기호_글꼴', '붙임글꼴_hwpx_처리', '글자서식_선행적용', '문자모양_적용_현재선택', '_다른_글꼴형식으로_재실행', '문단_줄간격_적용_현재선택', 'HwpUnit_pt', 'HwpUnit_mm', '문단_위간격_적용_현재선택', '문단_아래간격_pt_현재문단', '문단_아래간격_적용_현재선택', '_mm_hwpunit', '_현재_쪽여백', '_표준_또는_원본여백', '페이지_여백_설정', '용지_다르면_알림', '들여쓰기_공백_맞추기', '표준서식_기호규칙_찾기', '본문형_일반문장인가', '_사용자서식인가', '알파_일괄서식_가능', '사용자서식_XML추가값', '_GDI_글꼴인가', '_알파_글꼴형식', '_알파_라벨_굵게범위', '표준서식_hwpx_처리', '_알파_한줄문단인가', '표준서식_문단_처리', '빈문단_분류', '항목기호문장_사이_빈문단_찾기', '본문_컨트롤_문단번호', '항목기호문장_사이_빈줄_삭제', '글꼴형식_모으기', '글꼴형식_등록', '표준서식_전체_적용', '표준서식_선행_적용')

def _install(*, _docfit_namespace, _docfit_symbol, bind_function):
    global _표준서식_문단위간격_표, 기본_계층_스타일, 표준서식_문단위간격_찾기, 기호글꼴_적용, 표글꼴_적용, 복사_문단모양_적용, 계층_추가서식_값, 복사_간격_규칙_적용, 계층_추가서식_적용, 빈줄서식_hwpx_처리, 개요첫칸_hwpx_처리, 강조낱말_hwpx_처리, _문단_일반글, _문단_준말_판별, _문단_준말_제외사유, _문단_글_바꾸기, 준말_hwpx_처리, 연결부호탭_hwpx_처리, 콜론라벨_hwpx_처리, 준말_사용표_만들기, 준말_선행적용, _위첨자_글자모양, _문단_별표_대상, 별표위첨자_hwpx_처리, 별표위첨자_선행적용, _한글_글꼴표, _글꼴_확보, _글자모양_글꼴크기, _본문기호_글꼴, 붙임글꼴_hwpx_처리, 글자서식_선행적용, 문자모양_적용_현재선택, _다른_글꼴형식으로_재실행, 문단_줄간격_적용_현재선택, HwpUnit_pt, HwpUnit_mm, 문단_위간격_적용_현재선택, 문단_아래간격_pt_현재문단, 문단_아래간격_적용_현재선택, _mm_hwpunit, _현재_쪽여백, _표준_또는_원본여백, 페이지_여백_설정, 용지_다르면_알림, 들여쓰기_공백_맞추기, 표준서식_기호규칙_찾기, 본문형_일반문장인가, _사용자서식인가, 알파_일괄서식_가능, 사용자서식_XML추가값, _GDI_글꼴인가, _알파_글꼴형식, _알파_라벨_굵게범위, 표준서식_hwpx_처리, _알파_한줄문단인가, 표준서식_문단_처리, 빈문단_분류, 항목기호문장_사이_빈문단_찾기, 본문_컨트롤_문단번호, 항목기호문장_사이_빈줄_삭제, 글꼴형식_모으기, 글꼴형식_등록, 표준서식_전체_적용, 표준서식_선행_적용
    if _docfit_symbol == '_표준서식_문단위간격_표':
        def _표준서식_문단위간격_표():
            return {"chapter": 표준서식_문단위간격_chapter_pt,
                    "midtitle": 표준서식_문단위간격_midtitle_pt,
                    "box": 표준서식_문단위간격_box_pt,
                    "circle": 표준서식_문단위간격_circle_pt,
                    "dash": 표준서식_문단위간격_dash_pt,
                    "note": 표준서식_문단위간격_note_pt}
        return bind_function(_표준서식_문단위간격_표, _docfit_namespace)
    if _docfit_symbol == '기본_계층_스타일':
        def 기본_계층_스타일(fmt):
            """분석한 문서가 없는 서식(기본 보고서 서식)의 '계층별 문서 스타일 검토' 행.

            1 제목 · 2 장 · 3 중제목(로마자) · 4~6 □·ㅇ·- · 부연설명 순서다. 문단 위 여백은 서식이 복사한 값이 있으면
            그 값, 없으면 계층별 문단 위 여백 설정값(pt)을 쓴다(2026-10-05: 장·중제목 행과 여백 값이 빠져 있었다).
            """
            복사 = fmt.get("복사_문단모양", {}) or {}
            장 = fmt.get("장_규칙") or _표준서식_설정_기본값["장_규칙"]
            간격 = _표준서식_문단위간격_표()
            행들 = [("제목", "(없음)", fmt["제목_문단"]["font"], fmt["제목_문단"]["size_pt"], None),
                   ("장", 장[0], 장[2], 장[3], "chapter"),
                   # 중제목 기준 서식은 내장 중제목 표(번호·글 HY견고딕 20pt)다.
                   ("중제목", "Ⅰ", "HY견고딕", 20, "midtitle")]
            for rule in fmt["기호_규칙"]:
                marker = str(rule[0])
                role = leading_marker(marker + " 항목")[1] or "미분류"
                행들.append((role, marker, rule[2], rule[3], paragraph_level(marker + " 항목")))
            결과 = []
            for role, marker, font, size, 계층 in 행들:
                모양 = 복사.get(marker, {})
                if "PrevSpacing" in 모양:
                    위여백 = 모양["PrevSpacing"]
                else:
                    위여백 = int(round(float(간격.get(계층) or 0) * 100)) if 계층 else 0
                결과.append({"role": role, "marker": marker, "count": 1, "kind": "기본값",
                           "font": font, "size_pt": size,
                           "left_hwpunit": 모양.get("LeftMargin", 0),
                           "first_line_hwpunit": 모양.get("Indentation", 0),
                           "prev_spacing_hwpunit": 위여백})
            return 결과
        return bind_function(기본_계층_스타일, _docfit_namespace)
    if _docfit_symbol == '표준서식_문단위간격_찾기':
        def 표준서식_문단위간격_찾기(text, 계층=None):
            """문단 위 간격(pt). 계층을 주면 글 대신 그 계층으로 정한다(표 첫 칸 로마자 중제목 표)."""
            if 계층:
                return _표준서식_문단위간격_상태.spacing_for_level(
                    계층, _표준서식_문단위간격_표(), 표준서식_문단위간격_복귀배율)
            scheme = globals().get('활성_항목기호_체계')
            return _표준서식_문단위간격_상태.spacing_for(
                scheme.style_text(text) if scheme else text, _표준서식_문단위간격_표(), 표준서식_문단위간격_복귀배율)
        return bind_function(표준서식_문단위간격_찾기, _docfit_namespace)
    if _docfit_symbol == '기호글꼴_적용':
        def 기호글꼴_적용(설정딕셔너리=None):
            """저장된 symbol_fonts 값을 표준서식_설정["기호_규칙"]에 반영한다.

            사용자가 설정창에서 직접 지정한 문장기호별 글꼴·크기는 어떤 문서 서식
            프로파일을 고르든 항상 우선 적용되는 개인 설정으로 취급한다.
            """
            global 표준서식_설정
            # 이전 버전의 점 계열 규칙도 대표 기호 • 하나로 합친다.
            규칙들 = 표준서식_설정.setdefault("기호_규칙", [])
            대표규칙 = next((rule for rule in 규칙들 if rule[0] == "•"), None)
            if 대표규칙 is None:
                대표규칙 = next(rule for rule in _표준서식_설정_기본값["기호_규칙"] if rule[0] == "•")
            규칙들[:] = [rule for rule in 규칙들 if rule[0] not in DOT_MARKERS] + [대표규칙]
            글꼴맵 = (설정딕셔너리 or 기본_설정).get("symbol_fonts") or {}
            글꼴맵 = {**글꼴맵, "•": 글꼴맵.get("•") or next(
                (글꼴맵[key] for key in ("·", "‧", "∙", "⋅", "ㆍ", "●") if key in 글꼴맵), {})}
            if not 글꼴맵:
                return
            새규칙 = []
            for rule in 표준서식_설정.get("기호_규칙", []):
                기호 = rule[0]
                값 = 글꼴맵.get(기호)
                if 값 and (값.get("font") or 값.get("size")):
                    폰트 = str(값.get("font") or rule[2]).strip() or rule[2]
                    try:
                        크기 = int(값.get("size") or rule[3])
                    except (TypeError, ValueError):
                        크기 = rule[3]
                    새규칙.append((기호, rule[1], 폰트, 크기, rule[4], rule[5]))
                else:
                    새규칙.append(rule)
            표준서식_설정["기호_규칙"] = 새규칙
        return bind_function(기호글꼴_적용, _docfit_namespace)
    if _docfit_symbol == '표글꼴_적용':
        def 표글꼴_적용(table_fonts=None):
            """설정창의 표 머리글·본문 글꼴·크기를 표 서식 값에 반영한다.

            비어 있거나 잘못된 값(1~200pt 밖의 크기 등)은 현재 값을 그대로 둔다.
            """
            global 표_헤더서식_헤더_폰트, 표_헤더서식_헤더_크기
            global 표_헤더서식_본문_폰트, 표_헤더서식_본문_크기
            fonts = table_fonts or {}

            def 값(part, current_font, current_size):
                item = fonts.get(part) or {}
                font = str(item.get("font") or "").strip() or current_font
                try:
                    size = float(str(item.get("size", "")).strip())
                    if not 1 <= size <= 200:
                        raise ValueError
                    size = int(size) if size.is_integer() else size
                except (TypeError, ValueError):
                    size = current_size
                return font, size

            표_헤더서식_헤더_폰트, 표_헤더서식_헤더_크기 = 값(
                "header", 표_헤더서식_헤더_폰트, 표_헤더서식_헤더_크기)
            표_헤더서식_본문_폰트, 표_헤더서식_본문_크기 = 값(
                "body", 표_헤더서식_본문_폰트, 표_헤더서식_본문_크기)
        return bind_function(표글꼴_적용, _docfit_namespace)
    if _docfit_symbol == '복사_문단모양_적용':
        def 복사_문단모양_적용(symbol):
            values = 표준서식_설정.get("복사_문단모양", {}).get(symbol)
            if not values: return
            selected = 표준서식_설정.get("스타일_속성선택", {}).get(symbol, {})
            action = hwp.CreateAction("ParagraphShape")
            params = action.CreateSet()
            applied = 0
            for key, value in values.items():
                if key in ("LeftMargin", "Indentation") and selected.get("indent") is False: continue
                if key in ("PrevSpacing", "NextSpacing") and selected.get("spacing") is False: continue
                if key in ("LineSpacing", "LineSpacingType") and not 표준서식_줄간격_사용: continue
                if key in ("PrevSpacing", "NextSpacing") and not 표준서식_문단위간격_사용: continue
                # 예전에는 case 값을 그대로 넣어 예시 문서의 여백·간격이 절반으로 들어갔다.
                두배 = key in _문단여백_COM항목 or (key == "LineSpacing" and int(values.get("LineSpacingType", 0) or 0) != 0)
                params.SetItem(key, int(value) * 2 if 두배 else value)
                applied += 1
            if not applied:
                return
            if action.Execute(params) is False:
                raise RuntimeError("복사한 문단 서식적용 실패")
        return bind_function(복사_문단모양_적용, _docfit_namespace)
    if _docfit_symbol == '계층_추가서식_값':
        def 계층_추가서식_값(values, 장평_사용=True):
            """계층 추가 서식(예시 분석값)을 (글자 모양 COM 항목, 문단 모양 COM 항목)으로 바꾼다.

            영문 글꼴·장평·자간·정렬·줄 나눔 기준은 예시 값으로 맞춘다. 기울임·밑줄·취소선·글자색·음영은 예시가 쓴
            경우에만 넣는다(예시에 없다고 정리할 문서의 강조를 지우지 않는다).
            """
            글자, 문단 = {}, {}
            latin = values.get("font_latin")
            if latin:
                형식 = _글꼴형식.get(latin, "TTF")
                try:
                    타입 = hwp.FontType(형식) if hwp is not None else {"TTF": 1, "HFT": 2}.get(형식, 1)
                except Exception:
                    타입 = {"TTF": 1, "HFT": 2}.get(형식, 1)
                글자.update(FaceNameLatin=latin, FontTypeLatin=타입)
            if 장평_사용 and values.get("ratio") is not None:
                글자.update({필드: max(50, min(200, int(round(float(values["ratio"]))))) for 필드 in _언어별_장평})
            if 장평_사용 and values.get("spacing") is not None:
                글자.update({필드: max(-50, min(50, int(round(float(values["spacing"]))))) for 필드 in _언어별_자간})
            if values.get("italic"):
                글자["Italic"] = 1
            if values.get("underline") in _밑줄_COM:
                글자["UnderlineType"] = _밑줄_COM[values["underline"]]
            if values.get("strikeout"):
                글자["StrikeOutType"] = 1
            for 키, 필드 in (("color", "TextColor"), ("shade", "ShadeColor")):
                색 = str(values.get(키) or "")
                if re.fullmatch(r"#[0-9A-Fa-f]{6}", 색) and not (키 == "color" and 색.upper() == "#000000"):
                    글자[필드] = 색.upper()
            if values.get("align") in _정렬_COM:
                문단["AlignType"] = _정렬_COM[values["align"]]
            if values.get("break_word") in ("KEEP_WORD", "BREAK_WORD"):
                문단["BreakNonLatinWord"] = 1 if values["break_word"] == "KEEP_WORD" else 0
            return 글자, 문단
        return bind_function(계층_추가서식_값, _docfit_namespace)
    if _docfit_symbol == '복사_간격_규칙_적용':
        def 복사_간격_규칙_적용(symbol, text):
            """서식 복사한 간격 규칙으로 지금 항목기호 문단의 문단 위 간격을 정한다(복사한 문단 모양 다음에 부름).

            - 제목·개요 표 다음 첫 항목기호 문장: 예시에서 잰 표 아래~첫 문장 간격(빈 줄 없이 이 간격만큼 띄움)
            - 깊은 항목 다음 얕은 항목(계층 복귀): 예시에서 그 계층이 복귀할 때 쓴 문단 위 간격
            """
            scheme = globals().get('활성_항목기호_체계')
            깊이 = 서식요소.ROLE_DEPTH.get(보고서_문단역할(scheme.style_text(text) if scheme else text) or "")
            직전 = _간격규칙_상태["직전깊이"]
            if 깊이 is not None:
                _간격규칙_상태["직전깊이"] = 깊이
            if hwp is None or not 표준서식_문단위간격_사용:
                return None
            값 = None
            if not _간격규칙_상태["첫문장"]:
                _간격규칙_상태["첫문장"] = True
                if _문서_제목표_있음 and 표준서식_설정.get("제목뒤_간격") is not None:
                    값 = 표준서식_설정["제목뒤_간격"]
            elif 깊이 is not None and 직전 is not None and 깊이 < 직전:
                값 = (표준서식_설정.get("복귀_간격") or {}).get(symbol)
            if 값 is None:
                return None
            action = hwp.CreateAction("ParagraphShape")
            params = action.CreateSet()
            params.SetItem("PrevSpacing", int(값) * 2)       # COM은 HWPX case 값의 두 배
            if action.Execute(params) is False:
                로그(f"[서식 복사] 간격 규칙 적용 실패(무시): {text.strip()[:30]}")
                return None
            return int(값)
        return bind_function(복사_간격_규칙_적용, _docfit_namespace)
    if _docfit_symbol == '계층_추가서식_적용':
        def 계층_추가서식_적용(symbol):
            """예시 보고서에서 복사한 계층별 추가 서식을 지금 문단에 입힌다(서식 복사 전면 복제 1단계)."""
            values = (표준서식_설정.get("계층_추가서식") or {}).get(symbol)
            if not values or hwp is None:
                return
            글자, 문단 = 계층_추가서식_값(values, 표준서식_장평_사용)
            if 글자:
                hwp_run("MoveParaBegin")
                hwp_run("MoveSelParaEnd")
                try:
                    action = hwp.CreateAction("CharShape")

                    def 실행(항목):
                        params = action.CreateSet()
                        for key, value in 항목.items():
                            params.SetItem(key, _서식통일_색값(value) if key in ("TextColor", "ShadeColor") else value)
                        return params, action.Execute(params) is not False

                    params, 됨 = 실행(글자)
                    latin = 글자.get("FaceNameLatin")
                    if not 됨 and latin:
                        # 영문 글꼴 형식이 이 PC와 맞지 않으면 다른 형식으로, 그래도 안 되면 영문 글꼴 없이 장평·자간·글자색
                        # 등 나머지라도 입힌다(예전에는 한 번 실패하면 계층 추가 서식 전체가 빠졌다).
                        됨 = _다른_글꼴형식으로_재실행(action, params, latin, ("FontTypeLatin",))
                        if not 됨:
                            _, 됨 = 실행({k: v for k, v in 글자.items() if k not in ("FaceNameLatin", "FontTypeLatin")})
                            if 됨:
                                로그(f"[서식 복사] '{symbol}' 계층 영문 글꼴 '{latin}'은 이 PC에서 입힐 수 없어 빼고 적용")
                    if not 됨:
                        로그(f"[서식 복사] '{symbol}' 계층 글자 서식 적용 실패(무시)")
                finally:
                    hwp_run("Cancel")
            if 문단:
                action = hwp.CreateAction("ParagraphShape")
                params = action.CreateSet()
                for key, value in 문단.items():
                    params.SetItem(key, value)
                if action.Execute(params) is False:
                    로그(f"[서식 복사] '{symbol}' 계층 문단 서식 적용 실패(무시)")
        return bind_function(계층_추가서식_적용, _docfit_namespace)
    if _docfit_symbol == '빈줄서식_hwpx_처리':
        def 빈줄서식_hwpx_처리(source, target=None, selections=None):
            """서식 프로필이 예시에서 배운 빈 줄 모양을 같은 자리(앞뒤 요소)의 빈 줄에 입힌다(선행 서식 단계)."""
            from docfit_core import blank_lines
            배운값 = (표준서식_설정 or {}).get("빈줄_서식") or {}
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            names = sorted((n for n in contents if re.fullmatch(r'Contents/section\d+\.xml', n)),
                           key=lambda n: int(re.search(r'section(\d+)', n).group(1)))
            roots = {n: safe_xml_fromstring(contents[n]) for n in names}
            if selections is None:
                return {n: [i for i, _ in enumerate(blank_lines.slots(roots[n], 서식표_종류판별))] if 배운값 else []
                        for n in names}
            if not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            전 = {n: 제목_문자열(roots[n]) for n in names}
            count = blank_lines.apply(header, [roots[n] for n in names], 배운값, 서식표_종류판별)
            if any(제목_문자열(roots[n]) != 전[n] for n in names):
                raise RuntimeError('빈 줄 서식 처리 중 글 보존 검사에 실패했습니다.')
            for n in names:
                contents[n] = ET.tostring(roots[n], encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"빈 줄 서식: 예시와 같은 자리 빈 줄 {count}개에 예시 빈 줄 모양을 입힘")
            return count
        return bind_function(빈줄서식_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '개요첫칸_hwpx_처리':
        def 개요첫칸_hwpx_처리(source, target=None, selections=None):
            """개요 표(제목 표 바로 다음 1×1 상자) A1 칸 본문의 첫 글자 앞에 빈칸 1칸을 둔다(사용자 서식 규칙, 2026-10-17).

            첫 글자 앞에 이미 빈칸이 있으면 그대로 둔다(2칸이 되지 않게). 빈 문단은 건드리지 않는다.
            """
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            names = sorted((n for n in contents if re.fullmatch(r'Contents/section\d+\.xml', n)),
                           key=lambda n: int(re.search(r'section(\d+)', n).group(1)))
            roots = {n: safe_xml_fromstring(contents[n]) for n in names}

            def 대상문단(root):
                결과, 앞표 = [], None
                for p in (x for x in root if 제목_xml이름(x) == 'p'):
                    표들 = [t for r in p if 제목_xml이름(r) == 'run' for t in r if 제목_xml이름(t) == 'tbl']
                    if not 표들:
                        if 제목_문자열(p).strip():
                            앞표 = None        # 글 문단이 끼면 제목 표와 이어진 개요가 아니다(빈 줄은 건너뜀)
                        continue
                    for 표 in 표들:
                        종류 = 서식표_종류판별(표) or ''
                        if 종류 == 'box' and (앞표 or '').startswith('title'):
                            칸 = 제목_셀들(표)[0]
                            sub = 제목_자식(칸, 'subList')
                            for q in (x for x in (sub if sub is not None else ()) if 제목_xml이름(x) == 'p'):
                                글 = 제목_문자열(q)
                                if 글.strip() and not 글[0].isspace():
                                    결과.append(q)
                        앞표 = 종류
                return 결과

            if selections is None:
                return {n: list(range(len(대상문단(roots[n])))) for n in names}
            if not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            count = 0
            for n in names:
                for q in 대상문단(roots[n]):
                    t = next((t for r in q if 제목_xml이름(r) == 'run' for t in r
                              if 제목_xml이름(t) == 't' and (t.text or '').strip()), None)
                    if (t is None or not (t.text or '').lstrip() or t.text != t.text.lstrip()
                            or 제목_문자열(q).index(t.text.strip()[0]) != 0):
                        continue           # 첫 글자가 이 글 요소의 맨 앞이 아닌 복잡한 문단은 두지 않고 그대로 둔다
                    t.text = ' ' + t.text
                    for cache in [x for x in q if 제목_xml이름(x) == 'linesegarray']:
                        q.remove(cache)
                    count += 1
                contents[n] = ET.tostring(roots[n], encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"개요 표 첫 빈칸: 개요 A1 칸 문단 {count}개의 첫 글자 앞에 빈칸 1칸")
            return count
        return bind_function(개요첫칸_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '강조낱말_hwpx_처리':
        def 강조낱말_hwpx_처리(source, target=None, selections=None):
            """서식 프로필이 예시에서 배운 강조 낱말을 같은 계층 문장의 같은 낱말에 입힌다(선행 서식 단계)."""
            from docfit_core import emphasis
            배운값 = (표준서식_설정 or {}).get("강조_낱말") or []
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            names = sorted((n for n in contents if re.fullmatch(r'Contents/section\d+\.xml', n)),
                           key=lambda n: int(re.search(r'section(\d+)', n).group(1)))
            if selections is None:
                return {n: ([0] if 배운값 else []) for n in names}
            if not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            roots = {n: safe_xml_fromstring(contents[n]) for n in names}
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            전 = {n: 제목_문자열(roots[n]) for n in names}
            count = emphasis.apply(header, [roots[n] for n in names], 배운값)
            if any(제목_문자열(roots[n]) != 전[n] for n in names):
                raise RuntimeError('강조 낱말 처리 중 글 보존 검사에 실패했습니다.')
            for n in names:
                contents[n] = ET.tostring(roots[n], encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"강조 낱말: 서식 예시의 강조 낱말 {count}곳에 같은 강조를 입힘")
            return count
        return bind_function(강조낱말_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '_문단_일반글':
        def _문단_일반글(p):
            """표·그림·필드가 없는 일반 글 문단이면 글 요소(t) 목록을, 아니면 None을 돌려준다.

            구역·쪽 설정 컨트롤은 글 위치를 차지하지 않으므로 허용한다(실측: 첫 문단에 쪽 번호
            컨트롤이 있으면 '제목:' 준말을 찾지 못해 제목 표가 만들어지지 않았다).
            """
            texts = []
            for run in p:
                if 제목_xml이름(run) == 'linesegarray':
                    continue
                if 제목_xml이름(run) != 'run':
                    return None
                for child in run:
                    name = 제목_xml이름(child)
                    if name == 't':
                        if len(child):  # 탭·강제 줄바꿈 등이 섞인 글은 건드리지 않는다.
                            return None
                        texts.append(child)
                    elif name == 'secPr':
                        continue
                    elif name == 'ctrl':
                        if any(제목_xml이름(x) not in _문단_설정컨트롤 for x in child):
                            return None
                    else:
                        return None
            return texts
        return bind_function(_문단_일반글, _docfit_namespace)
    if _docfit_symbol == '_문단_준말_판별':
        def _문단_준말_판별(p):
            texts = _문단_일반글(p)
            if not texts:
                return None
            found = 준말_줄_판별(''.join(t.text or '' for t in texts), 준말_줄변환표(준말_등록표))
            return (texts, found) if found else None
        return bind_function(_문단_준말_판별, _docfit_namespace)
    if _docfit_symbol == '_문단_준말_제외사유':
        def _문단_준말_제외사유(p):
            """준말 줄처럼 시작하지만 글 사이에 표·필드·탭 같은 요소가 있어 바꾸지 않는 문단이면 알림 문구를, 아니면 None.

            실측(2026-09-30): 첫 문단의 쪽 번호 컨트롤 때문에 '제목:' 줄이 아무 기록 없이 건너뛰어져
            원인을 찾기 어려웠다. 바꾸지 않는 이유를 작업 로그에 남긴다. 공문 붙임 목록('붙임 : 1. … 1부.  끝.')처럼
            규칙상 바꾸지 않는 줄도 이유를 남긴다.
            """
            texts = _문단_일반글(p)
            if texts is not None:
                줄 = ''.join(t.text or '' for t in texts)
                사유 = 준말_제외사유(줄, 준말_줄변환표(준말_등록표)) if texts else ''
                return f"[준말 제외] '{줄.strip()[:40]}': {사유}" if 사유 else None
            글, 요소 = [], []
            for run in p:
                이름 = 제목_xml이름(run)
                if 이름 == 'linesegarray':
                    continue
                if 이름 != 'run':
                    요소.append(이름)
                    continue
                for child in run:
                    name = 제목_xml이름(child)
                    if name == 't':
                        글.append(''.join(child.itertext()))
                        요소.extend(제목_xml이름(x) for x in child)
                    elif name == 'ctrl':
                        요소.extend(제목_xml이름(x) for x in child if 제목_xml이름(x) not in _문단_설정컨트롤)
                    elif name != 'secPr':
                        요소.append(name)
            줄 = ''.join(글)
            if not 요소 or not 준말_줄_판별(줄, 준말_줄변환표(준말_등록표)):
                return None
            이름들 = ', '.join(dict.fromkeys(_준말_제외요소_이름.get(x, x) for x in 요소))
            return f"[준말 제외] '{줄.strip()[:40]}': 줄 안에 있는 {이름들} 때문에 본말로 바꾸지 않습니다."
        return bind_function(_문단_준말_제외사유, _docfit_namespace)
    if _docfit_symbol == '_문단_글_바꾸기':
        def _문단_글_바꾸기(p, texts, remove, insert):
            """문단 앞의 remove 글자를 지우고 그 자리에 insert를 넣는다(나머지 글의 글자 모양은 유지)."""
            left = remove
            for t in texts:
                value = t.text or ''
                cut = min(left, len(value))
                t.text = value[cut:]
                left -= cut
            texts[0].text = insert + (texts[0].text or '')
            for lineseg in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                p.remove(lineseg)
        return bind_function(_문단_글_바꾸기, _docfit_namespace)
    if _docfit_symbol == '준말_hwpx_처리':
        def 준말_hwpx_처리(source, target=None, selections=None):
            """줄 첫 어절이 등록한 준말이고 콜론이 이어지면 본말로 바꾼다.

            서식 표 본말은 콜론 뒤 글을 표 A1 칸에 넣고 준말 줄의 글을 지운다. 문구 본말은
            준말과 콜론을 본말로 바꾸고 나머지 글은 그대로 둔다. 본문(구역 바로 아래) 문단만 대상이다.
            """
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
            body = {n: [c for c in root if 제목_xml이름(c) == 'p'] for n, root in sections.items()}
            if selections is None:
                result = {}
                for name, paras in body.items():
                    result[name] = [(i, found[1][0], found[1][1]) for i, p in enumerate(paras)
                                    for found in [_문단_준말_판별(p) or (None, None)] if found[1]]
                    for p in paras:
                        사유 = _문단_준말_제외사유(p)
                        if 사유:
                            로그(사유)
                return result
            if not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            para_group = next((x for x in header.iter() if 제목_xml이름(x) == 'paraProperties'), None)
            has_default_para = para_group is not None and any(x.get('id') == '0' for x in para_group)
            cache, ids, count = {}, _문서_표번호(sections), 0
            for name, items in selections.items():
                변환목록 = []
                for index, key, _ in items:
                    p = body[name][index]
                    judged = _문단_준말_판별(p)
                    if judged is None or judged[1][0] != key:
                        raise RuntimeError('처리 중 준말 줄이 바뀌어 준말 변환을 중단했습니다.')
                    texts, (_, rest, prefix_len) = judged
                    spec = 준말_등록표[key]
                    if spec['type'] == 'text':
                        replacement = spec['value'] + (' ' if rest else '')
                        expected = replacement + rest
                        _문단_글_바꾸기(p, texts, prefix_len, replacement)
                        if ''.join(t.text or '' for t in texts) != expected:
                            raise RuntimeError('준말 문구 바꾸기 검사 실패')
                    else:
                        base_char = next((r.get('charPrIDRef') for r in p if 제목_xml이름(r) == 'run'
                                          and any(제목_xml이름(c) == 't' for c in r)), '0')
                        numeral = 준말_로마자(key) if spec['value'] == 'midtitle' else None
                        table = 서식표_생성(header, spec['value'], rest, cache, numeral, _구역_본문폭(sections[name]),
                                           _최종_본문폭(sections[name]))
                        _서식표_글_확인(spec['value'], table, rest, numeral)
                        _서식표_번호_부여(table, ids)
                        for run in [r for r in p if 제목_xml이름(r) == 'run']:
                            had_text = any(제목_xml이름(c) == 't' for c in run)
                            for t in [c for c in run if 제목_xml이름(c) == 't']:
                                run.remove(t)
                            if had_text and not len(run):
                                p.remove(run)
                        for lineseg in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                            p.remove(lineseg)
                        holder = XML_자식_추가(p, p, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}run',
                                               attrib={'charPrIDRef': base_char})
                        holder.append(table)
                        XML_자식_추가(holder, p, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}t')
                        if has_default_para:  # 들여쓰기·내어쓰기가 표 위치를 밀지 않도록 기본 문단 모양을 쓴다.
                            p.set('paraPrIDRef', '0')
                        p.set('styleIDRef', '0')
                        변환목록.append((p, spec['value']))
                    count += 1
                # '제목1:' 줄과 '개요:' 줄 사이의 빈 줄은 두 서식 표 사이 빈 줄이 되므로 지운다.
                _제목개요_빈줄_정리(sections[name], 변환목록)
                contents[name] = ET.tostring(sections[name], encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            return count
        return bind_function(준말_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '연결부호탭_hwpx_처리':
        def 연결부호탭_hwpx_처리(source, target=None, selections=None):
            """연속된 연결 부호 문장(목차·일정표)을 한/글 목차 점선처럼 채울 모양이 있는 왼쪽 정렬 탭으로 맞춘다(알파, 2026-10-10).

            오른쪽 글의 첫 글자가 내어쓰기처럼 한 세로선에 서고, 점·선의 길이와 개수는 한/글이 줄마다 채운다.
            여러 칸 빈칸 연결 부호는 채울 모양 없이 탭 위치만 맞춘다. 글자는 연결 부호만 탭으로 바뀐다.
            """
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            names = sorted((n for n in contents if re.fullmatch(r'Contents/section\d+\.xml', n)),
                           key=lambda n: int(re.search(r'section(\d+)', n).group(1)))
            roots = {n: safe_xml_fromstring(contents[n]) for n in names}
            if selections is None:
                if not 알파_연결부호_탭정렬_사용:
                    return {n: [] for n in names}
                return {n: [i for i, _ in enumerate(
                    [g for c in [root] + [x for x in root.iter() if 제목_xml이름(x) == 'subList'] for g in 연결부호탭.groups_in(c)])]
                    for n, root in roots.items()}
            if not any(selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            본문폭 = {n: _최종_본문폭(root) or _구역_본문폭(root) for n, root in roots.items()}
            부모구역 = {}
            for n, root in roots.items():
                for x in root.iter():
                    if 제목_xml이름(x) == 'subList':
                        부모구역[id(x)] = n

            def 폭(container):
                if 제목_xml이름(container) != 'subList':
                    return next((본문폭[n] for n, r in roots.items() if r is container), 0)
                cell = next((tc for r in roots.values() for tc in r.iter() if 제목_xml이름(tc) == 'tc' and container in list(tc)), None)
                if cell is None:
                    return 0
                sz, mg = 제목_자식(cell, 'cellSz'), 제목_자식(cell, 'cellMargin')
                try:
                    return int(sz.get('width')) - (int(mg.get('left', 0)) + int(mg.get('right', 0)) if mg is not None else 0)
                except (TypeError, ValueError, AttributeError):
                    return 0

            통계 = 연결부호탭.align_connectors(header, [roots[n] for n in names], 폭)
            if not 통계.get("paragraphs"):
                shutil.copyfile(source, target)
                return 0
            for n in names:
                contents[n] = ET.tostring(roots[n], encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"연결 부호 탭 정렬: 묶음 {통계['groups']}개·문단 {통계['paragraphs']}개를 목차 점선(왼쪽 정렬 탭)으로 맞춤"
                 + (f"(본문 폭 때문에 탭을 앞으로 당긴 묶음 {통계['pulled']}개)" if 통계.get('pulled') else ""))
            return 통계["paragraphs"]
        return bind_function(연결부호탭_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '콜론라벨_hwpx_처리':
        def 콜론라벨_hwpx_처리(source, target=None, selections=None):
            """연속된 '항목기호 + 짧은 라벨(10자 미만) + 콜론' 문장의 콜론을 세로로 맞춘다(알파, 2026-10-10 사용자 규칙).

            가장 긴 라벨을 기준으로 짧은 라벨 글자의 자간(한도 50%까지)과 장평을 늘려 가로 길이를 맞춘다. 글은 바꾸지 않는다.
            """
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            names = sorted((n for n in contents if re.fullmatch(r'Contents/section\d+\.xml', n)),
                           key=lambda n: int(re.search(r'section(\d+)', n).group(1)))
            roots = {n: safe_xml_fromstring(contents[n]) for n in names}
            if selections is None:
                if not 알파_콜론라벨_정렬_사용:
                    return {n: [] for n in names}
                return {n: list(range(sum(len(콜론라벨.groups_in(c)) for c in
                                          [root] + [x for x in root.iter() if 제목_xml이름(x) == 'subList'])))
                        for n, root in roots.items()}
            if not any(selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            전 = {n: 제목_문자열(roots[n]) for n in names}
            통계 = 콜론라벨.align_colons(header, [roots[n] for n in names], allow_ratio=장평_줄이기_사용)
            # 짧은 라벨 글자 사이에 빈칸을 넣을 수 있으므로 빈칸을 뺀 글로 보존을 확인한다.
            if any(re.sub(r'\s', '', 제목_문자열(roots[n])) != re.sub(r'\s', '', 전[n]) for n in names):
                raise RuntimeError('콜론 라벨 정렬 중 글 보존 검사에 실패했습니다.')
            if not 통계.get("stretched"):
                shutil.copyfile(source, target)
                return 0
            for n in names:
                contents[n] = ET.tostring(roots[n], encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"콜론 라벨 정렬: 묶음 {통계['groups']}개에서 짧은 라벨 {통계['stretched']}개를 늘려 콜론을 세로로 맞춤")
            return 통계["stretched"]
        return bind_function(콜론라벨_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '준말_사용표_만들기':
        def 준말_사용표_만들기(설정):
            """준말 사용표. 출처가 준말 관리 HWPX 문서이면 부를 때마다 문서를 다시 읽고(1.80.3),
            앱 설정이면 설정의 준말 등록과 기본 준말(제목1·제목2·개요·붙임·로1~로10)을 합친다. 같은 준말은 사용자 등록이 우선한다."""
            if 설정.get('abbreviation_source') != 'document':
                return 준말_기본_병합(설정.get('abbreviations'), 설정.get('abbreviation_defaults', True))
            from docfit_core.abbreviation_doc import effective_registry
            사용표, 오류들, 출처 = effective_registry(설정, HWP_AUTOMATION_DIR)
            for 오류 in 오류들[:20]:
                로그(f"준말 문서: {오류}")
            if 출처 == 'document':
                로그(f"준말 문서에서 준말 {len(사용표)}개를 읽었습니다.")
            return 사용표
        return bind_function(준말_사용표_만들기, _docfit_namespace)
    if _docfit_symbol == '준말_선행적용':
        def 준말_선행적용(원본문서경로, 현재문서_기준=True, 변경알림=None):
            """문서의 준말 줄을 본말로 바꾼 결과를 한 번만 다시 연다(사용표가 비면 아무것도 안 함).

            현재문서_기준이 아니면(앞 단계가 문서를 바꾸지 않았으면) 원본 HWPX를 직접 읽어 확인하므로
            바꿀 줄이 없을 때는 저장·다시 열기도 하지 않는다. 변경알림 dict에 changed를 채워 준다.
            """
            if not 준말_등록표:
                return True
            return 제목붙임_선행적용(원본문서경로, 현재문서_기준=현재문서_기준,
                                    처리목록=((True, '준말 변환', 준말_hwpx_처리, 'abbrev.hwpx'),), 변경알림=변경알림)
        return bind_function(준말_선행적용, _docfit_namespace)
    if _docfit_symbol == '_위첨자_글자모양':
        def _위첨자_글자모양(header, char_id, cache):
            """글자모양 char_id에 위첨자만 더한 사본의 ID를 돌려준다(이미 위첨자면 그대로, 같은 원본은 사본 하나를 공유)."""
            if char_id in cache:
                return cache[char_id]
            group = next(x for x in header.iter() if 제목_xml이름(x) == 'charProperties')
            source = next((x for x in group if x.get('id') == char_id), None)
            if source is None or any(제목_xml이름(x) == 'supscript' for x in source):
                cache[char_id] = char_id
                return char_id
            clone = copy.deepcopy(source)
            for sub in [x for x in clone if 제목_xml이름(x) == 'subscript']:
                clone.remove(sub)
            XML_자식_추가(clone, source, tag=source.tag.rsplit('}', 1)[0] + '}supscript')
            new_id = str(max([int(x.get('id')) for x in group if (x.get('id') or '').isdigit()] + [-1]) + 1)
            clone.set('id', new_id)
            group.append(clone)
            group.set('itemCnt', str(len(group)))
            cache[char_id] = new_id
            return new_id
        return bind_function(_위첨자_글자모양, _docfit_namespace)
    if _docfit_symbol == '_문단_별표_대상':
        def _문단_별표_대상(p, header_super_ids):
            """(글 요소 목록, 새로 위첨자로 만들 별표 글자 위치 집합)을 돌려준다. 대상이 없으면 None."""
            texts = _문단_일반글(p)
            if not texts:
                return None
            full = ''.join(t.text or '' for t in texts)
            spans = 별표_위치(full)
            if not spans:
                return None
            return texts, spans
        return bind_function(_문단_별표_대상, _docfit_namespace)
    if _docfit_symbol == '별표위첨자_hwpx_처리':
        def 별표위첨자_hwpx_처리(source, target=None, selections=None):
            """항목기호 문장의 단어 뒤 * / **를 위첨자로 바꾼다(글은 그대로, 별표 글자모양에 위첨자만 더함)."""
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
            super_ids = {x.get('id') for x in header.iter() if 제목_xml이름(x) == 'charPr'
                         and any(제목_xml이름(c) == 'supscript' for c in x)}
            body = {n: [c for c in root if 제목_xml이름(c) == 'p'] for n, root in sections.items()}

            def plan(p):
                """별표 위치 중 아직 위첨자가 아닌 것만 글 요소별 (요소, 시작, 끝) 조각으로 나눈다."""
                found = _문단_별표_대상(p, super_ids)
                if found is None:
                    return []
                texts, spans = found
                pieces, offset = [], 0
                for t in texts:
                    length = len(t.text or '')
                    for start, end in spans:
                        lo, hi = max(start, offset), min(end, offset + length)
                        if lo < hi:
                            pieces.append((t, lo - offset, hi - offset))
                    offset += length
                return pieces

            def already(p, piece):
                run = next(r for r in p if piece[0] in list(r))
                return run.get('charPrIDRef') in super_ids

            if selections is None:
                result = {}
                for name, paras in body.items():
                    result[name] = [(i, sum(1 for pc in plan(p) if not already(p, pc)))
                                    for i, p in enumerate(paras)
                                    if any(not already(p, pc) for pc in plan(p))]
                return result
            if not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            cache, count = {}, 0
            for name, items in selections.items():
                for index, _ in items:
                    p = body[name][index]
                    by_text = {}
                    for piece in plan(p):
                        by_text.setdefault(id(piece[0]), []).append(piece)
                    before = ''.join(제목_문자열(r) for r in p if 제목_xml이름(r) == 'run')
                    for pieces in by_text.values():
                        t = pieces[0][0]
                        run = next(r for r in p if t in list(r))
                        if len(run) != 1 or any(제목_xml이름(x) != 't' for x in run) or len(t):
                            continue  # 다른 요소가 섞인 글 묶음은 건드리지 않는다.
                        if run.get('charPrIDRef') in super_ids:
                            continue
                        text, cuts, position = t.text or '', [], 0
                        for _, lo, hi in sorted(pieces, key=lambda x: x[1]):
                            cuts += [(position, lo, False), (lo, hi, True)]
                            position = hi
                        cuts.append((position, len(text), False))
                        at = list(p).index(run)
                        p.remove(run)
                        for lo, hi, mark in [c for c in cuts if c[0] < c[1]]:
                            piece_run = XML_요소_생성(run, tag=run.tag, attrib=dict(run.attrib))
                            if mark:
                                piece_run.set('charPrIDRef', _위첨자_글자모양(header, run.get('charPrIDRef'), cache))
                                count += 1
                            XML_자식_추가(piece_run, t, tag=t.tag, attrib=dict(t.attrib)).text = text[lo:hi]
                            p.insert(at, piece_run)
                            at += 1
                    if ''.join(제목_문자열(r) for r in p if 제목_xml이름(r) == 'run') != before:
                        raise RuntimeError('별표 위첨자 적용 중 문장 글이 바뀌어 중단했습니다.')
                    for lineseg in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                        p.remove(lineseg)
                contents[name] = ET.tostring(sections[name], encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            return count
        return bind_function(별표위첨자_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '별표위첨자_선행적용':
        def 별표위첨자_선행적용(원본문서경로, 현재문서_기준=True, 변경알림=None):
            """문서의 별표(*, **)를 위첨자로 바꾼 결과를 한 번만 다시 연다(바꿀 별표가 없으면 다시 열지 않음)."""
            return 제목붙임_선행적용(원본문서경로, 현재문서_기준=현재문서_기준,
                                    처리목록=((True, '별표 위첨자', 별표위첨자_hwpx_처리, 'asterisk.hwpx'),), 변경알림=변경알림)
        return bind_function(별표위첨자_선행적용, _docfit_namespace)
    if _docfit_symbol == '_한글_글꼴표':
        def _한글_글꼴표(header):
            """언어별 글꼴 ID → 글꼴 이름 표({언어(소문자): {id: 이름}})."""
            return {ff.get('lang', '').lower(): {f.get('id'): f.get('face') for f in ff}
                    for ff in header.iter() if 제목_xml이름(ff) == 'fontface'}
        return bind_function(_한글_글꼴표, _docfit_namespace)
    if _docfit_symbol == '_글꼴_확보':
        def _글꼴_확보(header, face, cache):
            """모든 언어 글꼴 그룹에 face가 있게 하고 {언어(소문자): ID}를 돌려준다(없으면 첫 글꼴을 본떠 추가)."""
            if face in cache:
                return cache[face]
            result = {}
            for ff in [x for x in header.iter() if 제목_xml이름(x) == 'fontface']:
                found = next((f for f in ff if f.get('face') == face), None)
                if found is None:
                    found = copy.deepcopy(next(iter(ff)))
                    found.set('face', face)
                    found.set('id', str(max([int(f.get('id')) for f in ff if (f.get('id') or '').isdigit()] + [-1]) + 1))
                    ff.append(found)
                    ff.set('fontCnt', str(len(ff)))
                result[ff.get('lang', '').lower()] = found.get('id')
            cache[face] = result
            return result
        return bind_function(_글꼴_확보, _docfit_namespace)
    if _docfit_symbol == '_글자모양_글꼴크기':
        def _글자모양_글꼴크기(char, faces):
            """글자모양의 (언어별 글꼴 이름 집합, 크기 pt)."""
            ref = next((x for x in char if 제목_xml이름(x) == 'fontRef'), None)
            names = {faces.get(lang, {}).get(fid) for lang, fid in (ref.attrib.items() if ref is not None else [])}
            return names, int(char.get('height', '0')) / 100
        return bind_function(_글자모양_글꼴크기, _docfit_namespace)
    if _docfit_symbol == '_본문기호_글꼴':
        def _본문기호_글꼴(header, paras):
            """붙임 묶음에 맞출 (글꼴 이름, 크기 pt). 기호 서식을 쓰면 표준서식의 ㅇ 규칙, 아니면 문서 ㅇ 문장의 대표 글꼴."""
            if 표준서식_기호_사용:
                for rule in 표준서식_설정.get('기호_규칙', []):
                    if rule[0] == 'ㅇ':
                        return rule[2], float(rule[3])
            faces = _한글_글꼴표(header)
            chars = {x.get('id'): x for x in header.iter() if 제목_xml이름(x) == 'charPr'}
            tally = {}
            for p in paras:
                texts = _문단_일반글(p)
                if not texts or leading_marker(''.join(t.text or '' for t in texts))[0] != 'ㅇ':
                    continue
                for run in [r for r in p if 제목_xml이름(r) == 'run']:
                    length = sum(len(t.text or '') for t in run if 제목_xml이름(t) == 't')
                    char = chars.get(run.get('charPrIDRef'))
                    if length and char is not None:
                        _, size = _글자모양_글꼴크기(char, faces)
                        ref = next(x for x in char if 제목_xml이름(x) == 'fontRef')
                        key = (faces.get('hangul', {}).get(ref.get('hangul')), size)
                        tally[key] = tally.get(key, 0) + length
            return max(tally, key=tally.get) if tally else None
        return bind_function(_본문기호_글꼴, _docfit_namespace)
    if _docfit_symbol == '붙임글꼴_hwpx_처리':
        def 붙임글꼴_hwpx_처리(source, target=None, selections=None):
            """'붙임 …'부터 '끝.'까지 묶음의 모든 문장을 항목기호 ㅇ와 같은 글꼴 종류·크기로 맞춘다(글은 그대로)."""
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
            body = {n: [c for c in root if 제목_xml이름(c) == 'p'] for n, root in sections.items()}
            goal = _본문기호_글꼴(header, [p for paras in body.values() for p in paras])
            faces = _한글_글꼴표(header)
            chars = {x.get('id'): x for x in header.iter() if 제목_xml이름(x) == 'charPr'}

            def paragraph_text(p):
                texts = _문단_일반글(p)
                return None if texts is None else ''.join(t.text or '' for t in texts)

            def runs_with_text(p):
                return [r for r in p if 제목_xml이름(r) == 'run' and any(제목_xml이름(t) == 't' and (t.text or '') for t in r)]

            def needs_change(p):
                for run in runs_with_text(p):
                    char = chars.get(run.get('charPrIDRef'))
                    if char is not None:
                        names, size = _글자모양_글꼴크기(char, faces)
                        if names != {goal[0]} or abs(size - goal[1]) > 0.001:
                            return True
                return False

            if selections is None:
                if goal is None:
                    return {n: [] for n in body}
                return {n: [(s, e) for s, e in 붙임묶음_찾기([paragraph_text(p) for p in paras])
                            if any(needs_change(p) for p in paras[s:e + 1])]
                        for n, paras in body.items()}
            if goal is None or not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            font_cache, char_cache, count = {}, {}, 0
            group = next(x for x in header.iter() if 제목_xml이름(x) == 'charProperties')
            for name, items in selections.items():
                for start, end in items:
                    for p in body[name][start:end + 1]:
                        before = 제목_문자열(p)
                        for run in runs_with_text(p):
                            old = run.get('charPrIDRef')
                            if old not in char_cache:
                                source_char = chars.get(old)
                                names, size = _글자모양_글꼴크기(source_char, faces) if source_char is not None else ({None}, 0)
                                if source_char is None or (names == {goal[0]} and abs(size - goal[1]) < 0.001):
                                    char_cache[old] = old
                                else:
                                    clone = copy.deepcopy(source_char)
                                    clone.set('height', str(int(round(goal[1] * 100))))
                                    ids = _글꼴_확보(header, goal[0], font_cache)
                                    ref = next(x for x in clone if 제목_xml이름(x) == 'fontRef')
                                    for lang in list(ref.attrib):
                                        if lang.lower() in ids:
                                            ref.set(lang, ids[lang.lower()])
                                    new_id = str(max([int(x.get('id')) for x in group if (x.get('id') or '').isdigit()] + [-1]) + 1)
                                    clone.set('id', new_id)
                                    group.append(clone)
                                    group.set('itemCnt', str(len(group)))
                                    chars[new_id] = clone
                                    faces = _한글_글꼴표(header)
                                    char_cache[old] = new_id
                            run.set('charPrIDRef', char_cache[old])
                        if 제목_문자열(p) != before:
                            raise RuntimeError('붙임 글꼴 통일 중 문장 글이 바뀌어 중단했습니다.')
                        for lineseg in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                            p.remove(lineseg)
                        count += 1
                contents[name] = ET.tostring(sections[name], encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            return count
        return bind_function(붙임글꼴_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '글자서식_선행적용':
        def 글자서식_선행적용(원본문서경로, 별표위첨자=True, 붙임글꼴=True, 현재문서_기준=True, 변경알림=None):
            """별표 위첨자·붙임 글꼴 통일을 한 번에 처리해 결과를 한 번만 다시 연다(둘 다 글자 모양만 바꾸는 단계)."""
            return 제목붙임_선행적용(
                원본문서경로, 현재문서_기준=현재문서_기준, 변경알림=변경알림,
                처리목록=((별표위첨자, '별표 위첨자', 별표위첨자_hwpx_처리, 'asterisk.hwpx'),
                          (붙임글꼴, '붙임 글꼴', 붙임글꼴_hwpx_처리, 'attach_font.hwpx')))
        return bind_function(글자서식_선행적용, _docfit_namespace)
    if _docfit_symbol == '문자모양_적용_현재선택':
        def 문자모양_적용_현재선택(폰트=None, 크기_pt=None, 굵게=None, 장평=None, 자간=None,
                                자간_유지=False):
            if hwp is None:
                return
            try:
                # 일부 한컴오피스 버전은 글꼴/크기만 지정한 CharShape 부분 적용에서도
                # 선택 영역의 자간을 기본값으로 돌린다. 서식통일처럼 기존 자간을 보존해야
                # 하는 작업은 선택 영역의 언어별 자간을 먼저 읽어 다시 명시적으로 넣는다.
                보존할_자간 = {}
                if 자간_유지 and 자간 is None and (폰트 or 크기_pt or 굵게 is not None):
                    try:
                        기존 = hwp.HParameterSet.HCharShape
                        hwp.HAction.GetDefault("CharShape", 기존.HSet)
                        for 필드 in ("SpacingHangul", "SpacingLatin", "SpacingHanja", "SpacingJapanese",
                                     "SpacingOther", "SpacingSymbol", "SpacingUser"):
                            값 = getattr(기존, 필드, None)
                            if 값 is not None:
                                보존할_자간[필드] = int(값)
                    except Exception as e:
                        로그(f"자간 보존값 읽기 실패: {e}")
                # GetDefault로 HCharShape 전체를 채운 뒤 Execute하면 선택 영역에
                # 서로 다른 서식이 섞여 있을 때 지정하지 않은 속성(특히 Bold)이
                # 기본값으로 덮인다. 빈 파라미터셋에 변경할 항목만 넣어 실행한다.
                act = hwp.CreateAction("CharShape")
                pset = act.CreateSet()
                if 폰트:
                    # v1.12 버그수정: FaceName* 만 SetItem하면 한글 오토메이션에서
                    # 실제로는 글꼴이 반영되지 않는다(Height/Bold는 정상 반영되는데
                    # 글꼴명만 조용히 무시됨 - 실제 출력 hwpx를 열어 charPr을 비교해
                    # 확인한 사실). 언어별 FaceName은 반드시 같은 언어의 FontType과
                    # 짝을 지어 지정해야 한글이 그 이름을 실제 폰트로 등록/적용한다.
                    # (한컴디벨로퍼 포럼·pyhwpx 예제 등에서 공통적으로 FaceName*와
                    # FontType*를 항상 함께 SetItem하는 이유와 동일)
                    # 형식은 문서 헤더에 적힌 대로(HFT 글꼴을 TTF로 지정하면 조용히 무시됨).
                    형식 = _글꼴형식.get(폰트, "TTF")
                    try:
                        ttf_타입 = hwp.FontType(형식)
                    except Exception:
                        ttf_타입 = {"TTF": 1, "HFT": 2}.get(형식, 1)  # FontType 호출 실패 시 관례값
                    for 필드, 타입필드 in (
                        ("FaceNameHangul", "FontTypeHangul"),
                        ("FaceNameLatin", "FontTypeLatin"),
                        ("FaceNameHanja", "FontTypeHanja"),
                        ("FaceNameJapanese", "FontTypeJapanese"),
                        ("FaceNameOther", "FontTypeOther"),
                        ("FaceNameSymbol", "FontTypeSymbol"),
                        ("FaceNameUser", "FontTypeUser"),
                    ):
                        try:
                            pset.SetItem(필드, 폰트)
                            pset.SetItem(타입필드, ttf_타입)
                        except Exception:
                            pass
                if 크기_pt:
                    try:
                        pset.SetItem("Height", hwp.PointToHwpUnit(크기_pt))
                    except Exception:
                        pass
                if 굵게 is not None:
                    try:
                        pset.SetItem("Bold", 1 if 굵게 else 0)
                    except Exception:
                        pass
                # 분석한 서식 프로필은 장평·자간을 100.0처럼 실수로 담는다. COM에 실수를 넘기면
                # 정수 항목이 0으로 들어가 글자가 완전히 눌리므로 정수로 바꾸고 허용 범위로 제한한다.
                if 장평 is not None:
                    장평 = max(50, min(200, int(round(float(장평)))))
                if 자간 is not None:
                    자간 = max(-50, min(50, int(round(float(자간)))))
                if 장평 is not None:
                    for 필드 in ("RatioHangul", "RatioLatin", "RatioHanja", "RatioJapanese",
                                 "RatioOther", "RatioSymbol", "RatioUser"):
                        try:
                            pset.SetItem(필드, 장평)
                        except Exception:
                            pass
                if 자간 is not None:
                    for 필드 in ("SpacingHangul", "SpacingLatin", "SpacingHanja", "SpacingJapanese",
                                 "SpacingOther", "SpacingSymbol", "SpacingUser"):
                        try:
                            pset.SetItem(필드, 자간)
                        except Exception:
                            pass
                elif 보존할_자간:
                    for 필드, 값 in 보존할_자간.items():
                        try:
                            pset.SetItem(필드, 값)
                        except Exception:
                            pass
                if act.Execute(pset) is False:
                    # 글꼴 형식(TTF·HFT)이 이 PC의 글꼴과 맞지 않으면 실패한다(같은 이름이 두 형식으로 든 문서 등). 다른 형식으로
                    # 한 번 더 해 보고, 되면 그 형식을 기억한다(2026-10-04 범정부오피스 서식: HCI Poppy가 TTF·HFT 둘 다 있음).
                    if not (폰트 and _다른_글꼴형식으로_재실행(act, pset, 폰트, _언어별_글꼴형식)):
                        raise RuntimeError("CharShape 부분 적용 결과가 False입니다.")
            except Exception as e:
                로그(f"문자모양 적용 실패(무시): {e}")
        return bind_function(문자모양_적용_현재선택, _docfit_namespace)
    if _docfit_symbol == '_다른_글꼴형식으로_재실행':
        def _다른_글꼴형식으로_재실행(action, params, 글꼴, 형식필드):
            """글꼴 형식만 반대(TTF↔HFT)로 바꿔 글자 모양을 다시 실행한다. 되면 그 형식을 기억하고 True."""
            다른 = "HFT" if _글꼴형식.get(글꼴, "TTF") == "TTF" else "TTF"
            try:
                코드 = hwp.FontType(다른)
            except Exception:
                코드 = {"TTF": 1, "HFT": 2}[다른]
            try:
                for 필드 in 형식필드:
                    params.SetItem(필드, 코드)
                if action.Execute(params) is False:
                    return False
            except Exception:
                return False
            _글꼴형식[글꼴] = 다른
            return True
        return bind_function(_다른_글꼴형식으로_재실행, _docfit_namespace)
    if _docfit_symbol == '문단_줄간격_적용_현재선택':
        def 문단_줄간격_적용_현재선택(퍼센트):
            if 현재_한칸표인가():
                return
            if hwp is None:
                return
            # 줄간격 조정은 설정 범위(기본 140~200%)를 벗어날 수 없다.
            퍼센트 = max(세트문장_최소줄간격_퍼센트, min(세트문장_최대줄간격_퍼센트, 퍼센트))
            try:
                act = hwp.HAction
                pset = hwp.HParameterSet.HParaShape
                act.GetDefault("ParagraphShape", pset.HSet)
                try:
                    pset.LineSpacingType = hwp.LineSpacingMethod("Percent")
                except Exception:
                    pass
                pset.LineSpacing = 퍼센트
                act.Execute("ParagraphShape", pset.HSet)
            except Exception as e:
                로그(f"줄간격 적용 실패(무시): {e}")
        return bind_function(문단_줄간격_적용_현재선택, _docfit_namespace)
    if _docfit_symbol == 'HwpUnit_pt':
        def HwpUnit_pt(hwpunit):
            """HwpUnit(1/7200인치) 값을 포인트로 변환한다.

            hwp.PointToHwpUnit()은 실제 한/글 자동화 API에 있는 메서드지만,
            그 반대 방향인 HwpUnitToPoint()는 그렇지 않다 — pyhwpx가 자기
            래퍼 클래스에서 순수 파이썬 나눗셈(HwpUnit/100)으로 흉내만 낸
            편의 메서드였을 뿐, win32com으로 직접 붙는 이 코드베이스의 raw
            HwpFrame.HwpObject에는 없다. 실사용 로그에서
            "HwpFrame.HwpObject.HwpUnitToPoint" 오류로 확인됨. 같은 비율
            (100 HwpUnit = 1pt)로 직접 계산한다.
            """
            if not hwpunit:
                return 0.0
            return hwpunit / 100
        return bind_function(HwpUnit_pt, _docfit_namespace)
    if _docfit_symbol == 'HwpUnit_mm':
        def HwpUnit_mm(hwpunit):
            """HwpUnit(1/7200인치) 값을 밀리미터로 변환한다. HwpUnit_pt와 같은
            이유로 hwp.HwpUnitToMili()도 존재하지 않아 직접 계산한다.
            """
            if not hwpunit:
                return 0.0
            return hwpunit / 7200 * 25.4
        return bind_function(HwpUnit_mm, _docfit_namespace)
    if _docfit_symbol == '문단_위간격_적용_현재선택':
        def 문단_위간격_적용_현재선택(pt):
            if 현재_한칸표인가():
                return
            if hwp is None:
                return
            try:
                act = hwp.HAction
                pset = hwp.HParameterSet.HParaShape
                act.GetDefault("ParagraphShape", pset.HSet)
                # COM ParaShape 문단 간격은 실제 HWPUNIT의 두 배다(_문단여백_COM항목 참고). 예전에는 그대로 넣어
                # 기본 문단 위 여백(□ 15pt 등)이 절반(7.5pt)으로 들어갔다(2026-10-04 실측).
                pset.PrevSpacing = hwp.PointToHwpUnit(pt) * 2
                act.Execute("ParagraphShape", pset.HSet)
            except Exception as e:
                로그(f"문단 위 간격 적용 실패(무시): {e}")
        return bind_function(문단_위간격_적용_현재선택, _docfit_namespace)
    if _docfit_symbol == '문단_아래간격_pt_현재문단':
        def 문단_아래간격_pt_현재문단():
            """현재 캐럿이 있는 문단의 '문단 아래 간격' 값을 pt로 읽는다."""
            if hwp is None:
                return None
            try:
                return HwpUnit_pt(hwp.ParaShape.Item("NextSpacing")) / 2      # COM은 실제 HWPUNIT의 두 배
            except Exception as e:
                로그(f"문단 아래 간격 읽기 실패(무시): {e}")
                return None
        return bind_function(문단_아래간격_pt_현재문단, _docfit_namespace)
    if _docfit_symbol == '문단_아래간격_적용_현재선택':
        def 문단_아래간격_적용_현재선택(pt):
            if 현재_한칸표인가():
                return
            if hwp is None:
                return
            try:
                act = hwp.HAction
                pset = hwp.HParameterSet.HParaShape
                act.GetDefault("ParagraphShape", pset.HSet)
                pset.NextSpacing = hwp.PointToHwpUnit(max(0.0, pt)) * 2      # COM은 실제 HWPUNIT의 두 배
                act.Execute("ParagraphShape", pset.HSet)
            except Exception as e:
                로그(f"문단 아래 간격 적용 실패(무시): {e}")
        return bind_function(문단_아래간격_적용_현재선택, _docfit_namespace)
    if _docfit_symbol == '_mm_hwpunit':
        def _mm_hwpunit(mm):
            """mm → HWPUNIT(반올림). 한/글 MiliToHwpUnit은 소수를 버려 예시 여백 4252가 4251로 들어갔다(2026-10-04)."""
            return int(round(float(mm) * 7200 / 25.4))
        return bind_function(_mm_hwpunit, _docfit_namespace)
    if _docfit_symbol == '_현재_쪽여백':
        def _현재_쪽여백():
            """지금 문서 첫 구역의 쪽 여백 {항목: HWPUNIT}. 모르면 None."""
            if hwp is None:
                return None
            try:
                pset = hwp.HParameterSet.HSecDef
                hwp.HAction.GetDefault("PageSetup", pset.HSet)
                return {k: int(getattr(pset.PageDef, k)) for k in
                        ("LeftMargin", "RightMargin", "TopMargin", "BottomMargin", "HeaderLen", "FooterLen")}
            except Exception:
                return None
        return bind_function(_현재_쪽여백, _docfit_namespace)
    if _docfit_symbol == '_표준_또는_원본여백':
        def _표준_또는_원본여백(항목, 표준값, 원본=None):
            """표준 여백과 원본 여백 중 좁은 값. 원본 여백이 더 좁으면 원본을 둔다(사용자 결정, 2026-10-09:
            여백을 넓히면 본문 폭이 줄어 원본 쪽 구성이 깨짐. 실측: 좌우 18mm → 20mm로 14쪽 문서가 17쪽)."""
            if 작업_모드 != 'unify':
                return 표준값      # 원본 여백 유지는 쪽 구성 동일 원칙(서식 통일 전용)의 일부다
            원본 = _현재_쪽여백() if 원본 is None else 원본
            if not 원본 or 항목 not in 원본 or 원본[항목] <= 0:
                return 표준값
            return min(표준값, 원본[항목])
        return bind_function(_표준_또는_원본여백, _docfit_namespace)
    if _docfit_symbol == '페이지_여백_설정':
        def 페이지_여백_설정(여백_mm):
            if hwp is None:
                return
            try:
                원본 = _현재_쪽여백()
                act = hwp.HAction
                pset = hwp.HParameterSet.HSecDef
                act.GetDefault("PageSetup", pset.HSet)
                for 항목, 키 in (("LeftMargin", "left"), ("RightMargin", "right"), ("TopMargin", "top"),
                               ("BottomMargin", "bottom"), ("HeaderLen", "header"), ("FooterLen", "footer")):
                    setattr(pset.PageDef, 항목, _표준_또는_원본여백(항목, _mm_hwpunit(여백_mm[키]), 원본))
                if "gutter" in 여백_mm:
                    pset.PageDef.GutterLen = _mm_hwpunit(여백_mm["gutter"])
                act.Execute("PageSetup", pset.HSet)
            except Exception as e:
                로그(f"표준서식 여백 설정 실패(무시): {e}")
        return bind_function(페이지_여백_설정, _docfit_namespace)
    if _docfit_symbol == '용지_다르면_알림':
        def 용지_다르면_알림():
            """서식 복사한 예시 보고서와 정리할 문서의 용지 크기·방향이 다르면 작업 로그에 알린다(용지는 바꾸지 않음)."""
            용지 = 표준서식_설정.get("용지_mm")
            if not 용지 or hwp is None:
                return None
            try:
                pset = hwp.HParameterSet.HSecDef
                hwp.HAction.GetDefault("PageSetup", pset.HSet)
                너비 = float(pset.PageDef.PaperWidth) * 25.4 / 7200
                높이 = float(pset.PageDef.PaperHeight) * 25.4 / 7200
                가로 = bool(pset.PageDef.Landscape)
            except Exception:
                return None
            if abs(너비 - 용지["width"]) <= 1 and abs(높이 - 용지["height"]) <= 1 and 가로 == bool(용지.get("landscape")):
                return False

            def 글(w, h, l):
                return f"{w:g}×{h:g}mm{' 가로' if l else ''}"
            로그(f"[서식 복사] 예시 보고서 용지({글(용지['width'], 용지['height'], 용지.get('landscape'))})와 이 문서 용지"
                 f"({글(round(너비, 1), round(높이, 1), 가로)})가 다릅니다. 용지 크기·방향은 바꾸지 않았습니다.")
            return True
        return bind_function(용지_다르면_알림, _docfit_namespace)
    if _docfit_symbol == '들여쓰기_공백_맞추기':
        def 들여쓰기_공백_맞추기(목표_공백수):
            try:
                hwp_run("MoveParaBegin")
                문단_시작위치 = hwp.GetPos()
                text = 현재문단_텍스트()
                # 표준서식_기호규칙_찾기와 동일하게 스페이스뿐 아니라 탭 등
                # 모든 선행 공백류 길이를 기준으로 삼아야 탭 들여쓰기 문단에서도
                # 목표 공백수로 정확히 교체된다.
                벗긴텍스트 = text.lstrip()
                기존_공백수 = len(text) - len(벗긴텍스트)
                hwp.SetPos(*문단_시작위치)
                if 기존_공백수 == 목표_공백수:
                    return
                if 기존_공백수 > 0:
                    if 문단_범위_선택(문단_시작위치, 0, 기존_공백수) is False:
                        raise RuntimeError("앞 공백 선택 실패")
                    hwp_run("Delete")
                    hwp.SetPos(*문단_시작위치)
                if 목표_공백수 > 0:
                    텍스트_삽입(" " * 목표_공백수)
            except Exception as e:
                로그(f"들여쓰기 보정 실패(무시): {e}")
        return bind_function(들여쓰기_공백_맞추기, _docfit_namespace)
    if _docfit_symbol == '표준서식_기호규칙_찾기':
        def 표준서식_기호규칙_찾기(text):
            if not text:
                return None
            # v1.11 버그수정: 기존에는 lstrip(" ")로 '일반 공백'만 제거했다.
            # 그러나 공문서 문단은 탭(Tab)으로 들여쓰기된 뒤 □/ㅇ/-/※ 기호가
            # 오는 경우가 매우 흔한데, 그 경우 벗긴텍스트가 여전히 탭으로
            # 시작해 아래 startswith() 비교가 모든 규칙에서 실패했다. 즉
            # □/ㅇ/-/※ 4종 폰트 규칙이 "전혀 작동하지 않는" 현상의 근본 원인이다.
            # 문장부호_마커_끝위치 등 다른 판정 함수들과 동일하게 모든 공백류
            # (스페이스/탭 등)를 제거하도록 통일한다.
            벗긴텍스트 = text.lstrip()
            if not 벗긴텍스트:
                return None
            scheme = globals().get('활성_항목기호_체계')
            if scheme and scheme.is_excluded(text):
                return None
            mapped = scheme.canonical(text) if scheme else None
            if mapped:
                return next((rule for rule in 표준서식_설정['기호_규칙'] if rule[0] == mapped[0]), None)
            detected_marker, detected_role = leading_marker(벗긴텍스트)
            if detected_role == "장":
                return ((표준서식_설정.get("논리역할_규칙") or {}).get("장")
                        or 표준서식_설정.get("장_규칙") or _표준서식_설정_기본값.get("장_규칙"))
            if 표준서식_설정.get("논리역할_규칙"):
                for 규칙 in 표준서식_설정["기호_규칙"]:
                    if 규칙[0] == detected_marker:
                        return 규칙
                if detected_role in 표준서식_설정["논리역할_규칙"]:
                    return 표준서식_설정["논리역할_규칙"][detected_role]
            if 벗긴텍스트[0] in DOT_MARKERS:
                return next((규칙 for 규칙 in 표준서식_설정["기호_규칙"] if 규칙[0] == "•"), None)
            for 규칙 in 표준서식_설정["기호_규칙"]:
                if 벗긴텍스트.startswith(규칙[0]):
                    return 규칙
            for 별칭_기호, 원본_기호 in 표준서식_기호_별칭.items():
                if 벗긴텍스트.startswith(별칭_기호):
                    for 규칙 in 표준서식_설정["기호_규칙"]:
                        if 규칙[0] == 원본_기호:
                            return 규칙
            return None
        return bind_function(표준서식_기호규칙_찾기, _docfit_namespace)
    if _docfit_symbol == '본문형_일반문장인가':
        def 본문형_일반문장인가(text):
            """지금 문단(항목기호 없음)이 본문 문장인가. 서식 요소 분석의 '일반 문장'과 같은 기준(15자 이상, 18pt 미만,
            가운데·오른쪽 정렬 아님)으로, 제목·날짜·서명 줄에는 예시의 본문 서식을 입히지 않는다."""
            try:
                hwp_run("MoveParaBegin")
                정렬 = _정렬_이름.get(int(hwp.ParaShape.Item("AlignType")))
                크기 = int(hwp.CharShape.Item("Height"))
            except Exception:
                return False
            return 서식요소.is_body_sentence(text, 크기, 정렬)
        return bind_function(본문형_일반문장인가, _docfit_namespace)
    if _docfit_symbol == '_사용자서식인가':
        def _사용자서식인가():
            return any(표준서식_설정.get(key) for key in _사용자서식_키)
        return bind_function(_사용자서식인가, _docfit_namespace)
    if _docfit_symbol == '알파_일괄서식_가능':
        def 알파_일괄서식_가능():
            return bool(알파_HWPX_일괄서식_사용 and 작업_모드 in ('format', 'all')
                        and 표준서식_선행_사용 and 쪽범위_요청 is None
                        and stage_enabled(선택_세부작업, 'standard_format', 작업_모드)
                        and (알파_사용자서식_XML_사용 or not _사용자서식인가()))
        return bind_function(알파_일괄서식_가능, _docfit_namespace)
    if _docfit_symbol == '사용자서식_XML추가값':
        def 사용자서식_XML추가값(symbol, rule_symbol):
            """복사한 문단 모양·계층 추가 서식을 (글자 추가값, 문단 추가값) 튜플로(한/글 경로 복사_문단모양_적용·계층_추가서식_값과 같은
            선택 규칙). XML로 확실히 옮길 수 없는 값(취소선 등)이 있으면 None(그 문단은 한/글 경로)."""
            copied = 표준서식_설정.get("복사_문단모양", {}) or {}
            extra = 표준서식_설정.get("계층_추가서식") or {}
            para_values = copied.get(symbol if symbol in copied else rule_symbol) or {}
            values = extra.get(symbol if symbol in extra else rule_symbol) or {}
            selected = 표준서식_설정.get("스타일_속성선택", {}).get(rule_symbol, {})
            para = {}
            for key, value in para_values.items():
                if key in ("LeftMargin", "Indentation") and selected.get("indent") is False: continue
                if key in ("PrevSpacing", "NextSpacing") and selected.get("spacing") is False: continue
                if key in ("LineSpacing", "LineSpacingType") and not 표준서식_줄간격_사용: continue
                if key in ("PrevSpacing", "NextSpacing") and not 표준서식_문단위간격_사용: continue
                if key in _문단여백_HWPX:
                    para[_문단여백_HWPX[key]] = int(value)
                elif key == "LineSpacing":
                    종류 = _줄간격_종류_HWPX.get(int(para_values.get("LineSpacingType", 0) or 0))
                    if 종류 is None:
                        return None
                    para["line_type"], para["line_value"] = 종류, int(value)
                elif key != "LineSpacingType":
                    return None
            char = {}
            if values.get("strikeout"):
                return None
            latin = values.get("font_latin")
            if latin:
                char["latin_font"], char["latin_type"] = latin, _글꼴형식.get(latin, "TTF")
            if 표준서식_장평_사용 and values.get("ratio") is not None:
                char["ratio"] = max(50, min(200, int(round(float(values["ratio"])))))
            if 표준서식_장평_사용 and values.get("spacing") is not None:
                char["spacing"] = max(-50, min(50, int(round(float(values["spacing"])))))
            if values.get("italic"):
                char["italic"] = True
            if values.get("underline") in ("BOTTOM", "CENTER", "TOP"):
                char["underline"] = values["underline"]
            for key in ("color", "shade"):
                color = str(values.get(key) or "")
                if re.fullmatch(r"#[0-9A-Fa-f]{6}", color) and not (key == "color" and color.upper() == "#000000"):
                    char[key] = color.upper()
            if values.get("align") in ("JUSTIFY", "LEFT", "RIGHT", "CENTER", "DISTRIBUTE", "DISTRIBUTE_SPACE"):
                para["align"] = values["align"]
            if values.get("break_word") in ("KEEP_WORD", "BREAK_WORD"):
                para["break_non_latin"] = values["break_word"]
            return tuple(sorted(char.items())), tuple(sorted(para.items()))
        return bind_function(사용자서식_XML추가값, _docfit_namespace)
    if _docfit_symbol == '_GDI_글꼴인가':
        def _GDI_글꼴인가(글꼴):
            """Windows 글꼴(GDI) 목록에 있는지. 처음 한 번만 읽는다(한글 이름으로 비교된다)."""
            global _GDI_글꼴
            if _GDI_글꼴 is None:
                이름들 = set()
                hdc = win32gui.GetDC(0)
                try:
                    win32gui.EnumFontFamilies(hdc, None, lambda lf, tm, ft, data: 이름들.add(lf.lfFaceName) or 1, None)
                finally:
                    win32gui.ReleaseDC(0, hdc)
                _GDI_글꼴 = 이름들
            return 글꼴 in _GDI_글꼴
        return bind_function(_GDI_글꼴인가, _docfit_namespace)
    if _docfit_symbol == '_알파_글꼴형식':
        def _알파_글꼴형식(글꼴):
            """XML 일괄 서식에 쓸 글꼴 형식(TTF/HFT). 알 수 없으면 None(그 문단은 기존 COM 경로가 형식을 확인해 처리).

            COM 경로는 TTF로 해 보고 실패하면 HFT로 다시 하지만 XML은 다시 해 볼 수 없다. 예전에는 늘 TTF로 넣어
            한/글 전용 글꼴(휴먼명조·한양신명조 등 HFT, Windows 글꼴 목록에 없음)을 잘못된 형식으로 등록했다(2026-10-09 검토).
            Windows 글꼴 목록에 있으면 TTF, 없으면 HFT로 본다(COM 경로가 다시 시도해 얻는 결과와 같다).
            """
            if not 글꼴:
                return None
            if _글꼴형식.get(글꼴):
                return _글꼴형식[글꼴]
            try:
                return "TTF" if _GDI_글꼴인가(글꼴) else "HFT"
            except Exception:
                return None
        return bind_function(_알파_글꼴형식, _docfit_namespace)
    if _docfit_symbol == '_알파_라벨_굵게범위':
        def _알파_라벨_굵게범위(text):
            if not 괄호_라벨_볼드_사용 or 문두_라벨_굵게_제외_문단인가(text):
                return ()
            end = 문장부호_마커_끝위치(text)
            if end is None:
                return ()
            while end < len(text) and text[end] in (' ', '\t'):
                end += 1
            rest = text[end:]
            match = re.match(r'^([^\n\r:：]{1,25}?)[ \t]*([:：])[ \t]+(\S.*)$', rest)
            if match and match.group(1).strip():
                label = match.group(1).strip()
                start = end + rest.find(label)
                return ((start, start + len(label)),)
            if '(' in text:
                for match in 괄호_정규식.finditer(text):
                    if 괄호_문두_라벨인가(text, match):
                        return (match.span(),)
            return ()
        return bind_function(_알파_라벨_굵게범위, _docfit_namespace)
    if _docfit_symbol == '표준서식_hwpx_처리':
        def 표준서식_hwpx_처리(source, target=None, selections=None):
            """기본 본문 서식을 XML에서 일괄 적용하고 COM 중복 적용을 막는다."""
            global _알파_일괄서식_문서, _표준서식_XML텍스트, _표준서식_XML간격
            if not 알파_일괄서식_가능():
                return {} if target is None else 0
            from docfit_core.marker_scheme import detect_hwpx_scheme
            scheme = detect_hwpx_scheme(source)
            globals()['활성_항목기호_체계'] = scheme
            tracker = ParagraphSpacingTracker()
            def _xml_문단_키(value):
                return (value or '').lstrip(' \t\u00a0\u3000').rstrip('\r\n')

            _xml_내어쓰기_기준쌍 = None
            _xml_내어쓰기_기준확인 = False
            _xml_문장순번 = {}        # 같은 문장이 몇 번째로 나왔는지(예시에 같은 문장이 서식만 달리 반복될 때)
            _xml_기준확정 = set()     # 예시와 같은 문장이라 예시의 내어쓰기를 그대로 받은 문단 글
            _xml_부연_부모 = None      # 부연설명(*, **, ※)의 위 문단 유형(제목/본문/내용) — _부연설명_한문단과 같은 규칙

            def plan(text, paragraph):
                nonlocal _xml_내어쓰기_기준쌍, _xml_내어쓰기_기준확인, _xml_부연_부모
                # 컨트롤 문단도 위계 상태에는 포함한다. 그 문단의 실제 서식은 COM에 맡긴다.
                readable = _문단_본문글(paragraph) if text is None else text
                if scheme and scheme.is_excluded(readable):
                    _xml_부연_부모 = None
                    return None
                if not (scheme and scheme.canonical(readable)):
                    readable = normalize_leading_dot(readable)
                style_text = scheme.style_text(readable) if scheme else readable
                부연_부모 = _xml_부연_부모
                if readable.strip():
                    유형 = _부모문단_유형(readable)
                    if 유형 is not None:
                        _xml_부연_부모 = 유형
                    elif not _부연설명_문단인가(readable):
                        _xml_부연_부모 = None   # 번호 항목 등 다른 문단이 끼면 연결이 끊긴다
                prev = None
                사용자서식 = _사용자서식인가()
                if 표준서식_문단위간격_사용 and not 표준서식_설정.get("복제_들여쓰기_유지"):
                    prev = tracker.spacing_for(style_text, _표준서식_문단위간격_표(), 표준서식_문단위간격_복귀배율)
                    if not readable.strip():
                        tables = [x for x in paragraph.iter() if 제목_xml이름(x) == 'tbl']
                        if any(중제목_유형판별(x) for x in tables):
                            tracker.spacing_for_level('midtitle', _표준서식_문단위간격_표(), 표준서식_문단위간격_복귀배율)
                if text is None or not text.strip():
                    return None
                rule = 표준서식_기호규칙_찾기(readable) if 표준서식_기호_사용 else None
                if rule is None:
                    # 일반 본문·제목은 원래의 글자 모양을 보존한다. 사용자 서식의 본문 서식 복제는 한/글 경로에 맡긴다.
                    if 사용자서식:
                        return None
                    return ParagraphStyle(text=readable, prev_pt=prev) if prev is not None else None
                symbol, lead, font, size, paragraph_bold, marker_bold = rule
                if readable.lstrip().startswith('**') and symbol != '**':
                    lead = max(0, lead - 1)   # '*' 규칙을 빌려 쓸 때만 한 칸 적게('**' 규칙을 배운 프로필은 그 값 그대로)
                # 부연설명(*, **, ※)은 위 문단 유형별 칸 수(예시에서 배운 값 → 부연설명_앞빈칸 기본표)를 쓴다.
                # 예전에는 기호 규칙의 고정 칸 수(* 3, ** 2)만 넣고 뒤 단계(_부연설명_한문단)가 XML 처리 문단을
                # 건너뛰어 '-' 아래 * 6·** 5가 3·2로 남았다(2026-10-20, 135f937 회귀).
                if _부연설명_문단인가(readable) and (부연설명_들여쓰기_사용 or 표준서식_설정.get("부연설명_앞빈칸")):
                    부연_본문 = readable.lstrip(' \t 　')
                    칸 = 부연설명_앞빈칸_수(부연_부모, "**" if 부연_본문.startswith("**") else 부연_본문[0])
                    if 칸 is not None:
                        lead = 칸
                # 문두 공백은 내어쓰기 left/intent 계산에 반영되어야 하므로 문단모양을 만들기 전에 정한다.
                # 서식 복사(복제) 프로필도 예시에서 배운 칸 수로 맞춘다(v1.64 동작 복원, 2026-10-20). 예전에는
                # 복제_들여쓰기_유지면 원문 앞 빈칸을 그대로 둬 txt 입력(앞 빈칸 0)의 ㅇ·-가 0칸이 됐다.
                formatted = ' ' * lead + readable.lstrip(' \t 　')
                추가 = ((), ())
                if 사용자서식:
                    추가 = 사용자서식_XML추가값(leading_marker(readable)[0], symbol)
                    if 추가 is None:
                        return None
                selected = 표준서식_설정.get('스타일_속성선택', {}).get(symbol, {})
                글꼴형식 = _알파_글꼴형식(font) if selected.get('font', True) else None
                if selected.get('font', True) and font and 글꼴형식 is None:
                    return None      # 글꼴 형식을 모르면 기존 COM 경로(TTF↔HFT 확인)로 처리한다
                enabled = 표준서식_기호_굵게.get(symbol, True)
                bold = bool(paragraph_bold and enabled)
                spans = list(_알파_라벨_굵게범위(formatted))
                if marker_bold and enabled and not bold:
                    기호위치 = len(formatted) - len(formatted.lstrip())
                    mapped = scheme.canonical(formatted) if scheme else None
                    spans.append((기호위치, mapped[1] if mapped else 기호위치 + 1))
                보통 = ()
                if bold and symbol in (표준서식_설정.get("기호_보통") or ()):
                    기호위치 = len(formatted) - len(formatted.lstrip())
                    mapped = scheme.canonical(formatted) if scheme else None
                    끝 = mapped[1] if mapped else 기호위치 + len(symbol)
                    끝 += len(formatted[끝:]) - len(formatted[끝:].lstrip(' \t'))   # 기호 뒤 빈칸도 보통('□ ')
                    보통 = ((기호위치, 끝),)
                문단추가 = dict(추가[1])
                if (globals().get('표준서식_내어쓰기_사용', False)
                        and selected.get('indent', True)
                        and not (사용자서식 and 'intent' in 문단추가)):
                    from docfit_core.xml_hanging_indent import (
                        hanging_indent_pair, paragraph_wraps,
                        consistent_reference_pair, next_occurrence, reference_marker_indent_pairs,
                        safe_reference_hanging_indent_pair,
                    )
                    from pathlib import Path
                    if not _xml_내어쓰기_기준확인:
                        _xml_내어쓰기_기준확인 = True
                        candidates = []
                        active_sample = globals().get('활성_서식예시_파일')
                        if active_sample:
                            try:
                                candidates.append(Path(active_sample))
                            except Exception:
                                pass
                        if not 사용자서식:
                            sample_folder = globals().get('서식예시_폴더')
                            if callable(sample_folder):
                                try:
                                    candidates.append(Path(sample_folder()) / '기본 서식.hwpx')
                                except Exception:
                                    pass
                            app_home = globals().get('HWP_AUTOMATION_DIR')
                            if app_home:
                                candidates.append(Path(app_home) / '서식예시' / '기본 서식.hwpx')
                            program_folder = globals().get('프로그램_폴더')
                            if callable(program_folder):
                                try:
                                    candidates.append(Path(program_folder()) / 'resources' / '서식예시' / '기본 서식.hwpx')
                                except Exception:
                                    pass
                            bundle_folder = globals().get('번들_리소스_폴더')
                            if callable(bundle_folder):
                                try:
                                    bundle = bundle_folder()
                                    if bundle:
                                        candidates.append(Path(bundle) / 'resources' / '서식예시' / '기본 서식.hwpx')
                                except Exception:
                                    pass
                            try:
                                candidates.append(Path(__file__).resolve().parent / 'resources' / '서식예시' / '기본 서식.hwpx')
                            except Exception:
                                pass
                        reference = next((item for item in candidates if item.is_file()), None)
                        if reference is not None:
                            try:
                                _xml_내어쓰기_기준쌍 = reference_marker_indent_pairs(reference)
                                로그(f'[알파 XML 내어쓰기] 기준 서식 {reference} / '
                                     f'기호·라벨 대표값 {len(_xml_내어쓰기_기준쌍)}개')
                            except Exception as error:
                                로그(f'[알파 XML 내어쓰기] 기준 서식 분석 실패, 폭 계산 폴백: {error}')
                    내어쓰기쌍 = (
                        consistent_reference_pair(
                            formatted, _xml_내어쓰기_기준쌍,
                            size_pt=(size if selected.get('size', True) and size else 15.0),
                            occurrence=next_occurrence(_xml_문장순번, formatted), scheme=scheme,
                        )
                        if _xml_내어쓰기_기준쌍
                        else None
                    )
                    if 내어쓰기쌍 is not None:
                        _xml_기준확정.add(formatted)   # 예시와 같은 문장: 예시 값 그대로(뒤 COM Shift+Tab이 덮지 않음)
                    elif _xml_내어쓰기_기준쌍:
                        # 예시에 같은 문장이 없으면 여백을 비워 두고 '최종 서식 기준 내어쓰기'(한/글 Shift+Tab 실측)에 맡긴다.
                        # 추정 여백을 먼저 넣으면 그 위에서 실측이 겹쳐 문단 전체가 오른쪽으로 밀렸다(2026-10-21 화면 대조).
                        내어쓰기쌍 = (0, 0)
                    if 내어쓰기쌍 is None:
                        내어쓰기쌍 = hanging_indent_pair(
                            formatted,
                            size_pt=(size if selected.get('size', True) and size else 15.0),
                            ratio=(표준서식_설정['기본_장평'] if 표준서식_장평_사용 else 100),
                            spacing=(표준서식_설정.get('기본_자간', 0) or 0),
                        )
                    if 내어쓰기쌍 is not None:
                        문단추가['left'], 문단추가['intent'] = 내어쓰기쌍
                return ParagraphStyle(
                    plain_spans=보통,
                    text=formatted, font=font if selected.get('font', True) else None,
                    font_type=글꼴형식,
                    size_pt=size if selected.get('size', True) else None,
                    bold=bold if '복사_문단모양' in 표준서식_설정 else (True if bold else None),
                    ratio=표준서식_설정['기본_장평'] if 표준서식_장평_사용 else None,
                    line_percent=표준서식_설정['기본_줄간격_퍼센트'] if 표준서식_줄간격_사용 else None,
                    prev_pt=prev, bold_spans=tuple(spans), char_extra=추가[0],
                    para_extra=tuple(sorted(문단추가.items())))

            try:
                result = apply_batch(source, target, plan)
            except Exception as error:
                # 미지원 구조(BatchUnsupported·UnsupportedPackage)뿐 아니라 예상 밖 오류(_rewrite_runs의 글자 보존 검사 등)도
                # 기존 COM 경로로 돌린다. 알파 새 기능의 오류로 베타에서 되던 문서 처리가 실패하면 안 된다(2026-10-09 검토).
                if not isinstance(error, (BatchUnsupported, UnsupportedPackage)):
                    로그(f'[알파 일괄 서식] 예상 밖 오류({type(error).__name__}) — 기존 COM 경로로 처리')
                로그(f'[알파 일괄 서식] 기존 COM 경로 사용: {error}')
                if target is not None:
                    shutil.copyfile(source, target)
                    _표준서식_XML텍스트 = set()
                    _표준서식_XML간격 = {}
                    _알파_일괄서식_문서 = False
                return {} if target is None else 0
            if target is None:
                return {'본문': list(range(result.applied))}
            _표준서식_XML텍스트 = set(result.formatted_texts)
            _표준서식_XML간격 = dict(result.paragraph_spacing)
            globals()['_표준서식_XML기준확정'] = {t for t in _xml_기준확정 if t in result.formatted_texts}
            _알파_일괄서식_문서 = bool(result.applied)
            로그(f'[알파 일괄 서식] XML 적용 {result.applied}문단 / 기존 경로 {result.fallback}문단 / '
                 f'새 글자 모양 {result.char_styles}개·문단 모양 {result.paragraph_styles}개')
            return result.applied
        return bind_function(표준서식_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '_알파_한줄문단인가':
        def _알파_한줄문단인가(pos):
            """현재 실제 조판이 한 줄이면 자간·짧은 마지막 줄 보정이 필요 없다.

            오래된 XML lineseg나 글자 폭 추정값으로 문단을 제외하지 않는다.
            컨트롤, 측정 실패는 기존 전수 검사로 돌린다.
            """
            if not _알파_일괄서식_문서 or pos[0] != 0:
                return False
            try:
                hwp_run('MoveParaBegin')
                begin = hwp.GetPos()
                hwp_run('MoveParaEnd')
                end = hwp.GetPos()
                hwp_run('MoveLineBegin')
                last_line = hwp.GetPos()
                return (tuple(begin) == tuple(last_line) and tuple(begin[:2]) == tuple(pos[:2])
                        and tuple(end[:2]) == tuple(pos[:2]) and begin[2] == 0)
            except Exception:
                return False
            finally:
                hwp.SetPos(*pos)
        return bind_function(_알파_한줄문단인가, _docfit_namespace)
    if _docfit_symbol == '표준서식_문단_처리':
        def 표준서식_문단_처리(문단_순번, 헤더_역할=None, 상속_기호_매칭=None):
            """현재 문단에 보고서 표준서식을 적용한다.

            v1.5:
            - □/ㅇ/-/※ 구조 기호가 제목/일자 판정보다 우선한다.
            - 세트 후속문단은 상위 문장부호의 폰트/크기 규칙을 상속한다.
              예: '※ (1~5번)...' 다음 '(6~16번)...'도 ※ 규칙(한컴돋움 13pt)을 적용한다.
            - 상속 문단은 원래의 더 깊은 들여쓰기를 유지한다.
            """
            if 현재_한칸표인가():
                return
            text = 현재문단_텍스트()
            if not text or not text.strip():
                if 표준서식_장평_사용:
                    hwp_run("MoveParaBegin")
                    hwp_run("MoveSelParaEnd")
                    문자모양_적용_현재선택(장평=표준서식_설정["기본_장평"])
                    hwp_run("Cancel")
                if 표준서식_줄간격_사용:
                    hwp_run("MoveParaBegin")
                    hwp_run("MoveSelParaEnd")
                    # 예시가 빈 줄에 따로 쓴 줄 간격이 있으면 그 값(예시 빈 줄 170%·본문 160%)
                    문단_줄간격_적용_현재선택(표준서식_설정.get("빈줄_줄간격_퍼센트") or 표준서식_설정["기본_줄간격_퍼센트"])
                    hwp_run("Cancel")
                return

            scheme = globals().get('활성_항목기호_체계')
            통일텍스트 = text if scheme and scheme.canonical(text) else normalize_leading_dot(text)
            if 통일텍스트 != text:
                시작 = hwp.GetPos()
                hwp_run("MoveParaBegin")
                문단시작 = hwp.GetPos()
                기호위치 = len(text) - len(text.lstrip())
                if 문단_범위_선택(문단시작, 기호위치, 기호위치 + 1) is not False:
                    텍스트_삽입("•")
                hwp.SetPos(*시작)
                text = 통일텍스트

            자체_기호_매칭 = 표준서식_기호규칙_찾기(text) if 표준서식_기호_사용 else None
            # 기호 서식 규칙이 없는 *·- 문단도 위계 추적에 포함해야 복귀를 판정할 수 있다.
            if 표준서식_문단위간격_사용 and not 표준서식_설정.get("복제_들여쓰기_유지"):
                간격_pt = 표준서식_문단위간격_찾기(text)
                if 간격_pt is not None and not (
                        any(item.lstrip(' \t\u00a0\u3000').rstrip('\r\n') == text.lstrip(' \t\u00a0\u3000').rstrip('\r\n')
                            for item in _표준서식_XML텍스트)
                        and next((value for item, value in _표준서식_XML간격.items()
                                  if item.lstrip(' \t\u00a0\u3000').rstrip('\r\n') == text.lstrip(' \t\u00a0\u3000').rstrip('\r\n')),
                                 None) == 간격_pt and hwp.GetPos()[0] == 0):
                    hwp_run("MoveParaBegin")
                    hwp_run("MoveSelParaEnd")
                    문단_위간격_적용_현재선택(간격_pt)
                    hwp_run("Cancel")
            if (any(item.lstrip(' \t\u00a0\u3000').rstrip('\r\n') == text.lstrip(' \t\u00a0\u3000').rstrip('\r\n')
                    for item in _표준서식_XML텍스트) and hwp.GetPos()[0] == 0):
                # XML 배치 경로는 기준 HWPX의 기호별 left/intent까지 이미 확정했다.
                # 다시 COM Shift+Tab을 적용하면 글자폭 추정 산식이 기준값을 덮어써서
                # 기호별 위치가 달라진다(2026-10-19 회귀 원인 수정).
                if 자체_기호_매칭 and _사용자서식인가():
                    # 알파 1-d: 서식 복사 간격 규칙(제목 뒤 첫 문장·계층 복귀)은 문단 순서 상태가 있어 한/글 경로에서 이어 간다.
                    hwp_run('MoveParaBegin')
                    실제기호, _ = leading_marker(text)
                    복사_간격_규칙_적용(실제기호 if 실제기호 in (표준서식_설정.get("복귀_간격") or {}) else 자체_기호_매칭[0], text)
                return
            # 보고서 표준서식은 문장부호(□/ㅇ/-/※ 등)로 시작하는 문단만 대상으로
            # 한다. 제목·일자·일반 본문에는 장평/줄간격/폰트/내어쓰기를 적용하지
            # 않아 원문 서식을 보존한다.
            if 자체_기호_매칭 is None:
                본문규칙 = 표준서식_설정.get("본문_문단") if 표준서식_설정.get("복제_본문서식") else None
                # 서식 예시의 본문 서식은 본문 문장에만 입힌다. 예전에는 제목·날짜 줄까지 본문 글꼴·크기로 바꿨다(2026-10-04).
                if 본문규칙 and 본문형_일반문장인가(text):
                    hwp_run("MoveParaBegin")
                    hwp_run("MoveSelParaEnd")
                    문자모양_적용_현재선택(
                        폰트=본문규칙.get("font"),
                        크기_pt=본문규칙.get("size_pt"),
                        굵게=True if 본문규칙.get("bold") else None,
                        장평=표준서식_설정["기본_장평"] if 표준서식_장평_사용 else None,
                        자간=표준서식_설정.get("기본_자간") if 표준서식_장평_사용 else None,
                    )
                    hwp_run("Cancel")
                    hwp_run("MoveParaBegin")
                    if 서식요소.PLAIN_KEY in 표준서식_설정.get("복사_문단모양", {}):
                        # 예시 '일반 문장'의 여백·문단 간격·줄 간격과 영문 글꼴·장평·자간·정렬 등을 그대로 입힌다.
                        복사_문단모양_적용(서식요소.PLAIN_KEY)
                        계층_추가서식_적용(서식요소.PLAIN_KEY)
                    elif 표준서식_줄간격_사용:
                        hwp_run("MoveSelParaEnd")
                        문단_줄간격_적용_현재선택(표준서식_설정["기본_줄간격_퍼센트"])
                        hwp_run("Cancel")
                if (표준서식_내어쓰기_사용 and not 최종_내어쓰기_예정
                        and 문단_내어쓰기_기준_오프셋(text) is not None):
                    hwp_run("MoveParaBegin")
                    문단_내어쓰기_적용(hwp.GetPos(), text)
                진단로그(f"[표준서식 제외] 문장부호로 시작하지 않음: {text.strip()[:80]}")
                return
            기호_매칭 = 자체_기호_매칭 or 상속_기호_매칭

            제목_문단인가 = bool(
                not 기호_매칭 and 표준서식_제목_사용 and 헤더_역할 == "title"
            )
            일자담당자_문단인가 = bool(
                not 기호_매칭 and 표준서식_일자담당자_사용 and 헤더_역할 == "dateinfo"
            )

            # v1.64 절차 복원: 자체 항목기호 문단은 복제 서식 프로필이어도
            # 앞 공백류를 실측해 규칙값과 다르면 선행부만 교체한다.
            # **(주석2)는 둘째 별표가 *(주석1)의 별표와 같은 가로 위치에 오도록 선행 공백을 1칸 적게(공백수 - 1) 둔다.
            if 자체_기호_매칭:
                목표_공백수 = 자체_기호_매칭[1]
                if text.lstrip().startswith("**") and 자체_기호_매칭[0] != "**":
                    목표_공백수 = max(0, 목표_공백수 - 1)
                들여쓰기_공백_맞추기(목표_공백수)

            if 표준서식_장평_사용:
                hwp_run("MoveParaBegin")
                hwp_run("MoveSelParaEnd")
                문자모양_적용_현재선택(장평=표준서식_설정["기본_장평"])
                hwp_run("Cancel")

            if 표준서식_줄간격_사용:
                hwp_run("MoveParaBegin")
                hwp_run("MoveSelParaEnd")
                문단_줄간격_적용_현재선택(표준서식_설정["기본_줄간격_퍼센트"])
                hwp_run("Cancel")

            if 제목_문단인가:
                규칙 = 표준서식_설정["제목_문단"]
                선택 = 표준서식_설정.get("스타일_속성선택", {}).get("(제목)", {})
                hwp_run("MoveParaBegin")
                hwp_run("MoveSelParaEnd")
                문자모양_적용_현재선택(
                    폰트=규칙["font"] if 선택.get("font", True) else None,
                    크기_pt=규칙["size_pt"] if 선택.get("size", True) else None,
                    굵게=표준서식_제목_굵게
                )
                hwp_run("Cancel")
                복사_문단모양_적용("(제목)")
            elif 일자담당자_문단인가:
                규칙 = 표준서식_설정["일자담당자_문단"]
                hwp_run("MoveParaBegin")
                hwp_run("MoveSelParaEnd")
                문자모양_적용_현재선택(
                    폰트=규칙["font"], 크기_pt=규칙["size_pt"], 굵게=표준서식_일자담당자_굵게
                )
                hwp_run("Cancel")
            elif 기호_매칭:
                기호, 공백수, 폰트, 크기, 문단굵게_기본값, 기호만굵게_기본값 = 기호_매칭
                선택 = 표준서식_설정.get("스타일_속성선택", {}).get(기호, {})
                굵게_허용 = 표준서식_기호_굵게.get(기호, True)
                문단굵게 = 문단굵게_기본값 and 굵게_허용
                기호만굵게 = 기호만굵게_기본값 and 굵게_허용

                hwp_run("MoveParaBegin")
                hwp_run("MoveSelParaEnd")
                # 규칙이 굵게인 경우만 굵게를 추가한다. False를 문단 전체에 강제로
                # 적용하면 원문에서 강조된 일부 텍스트까지 일반체로 풀리므로,
                # 굵게 해제는 하지 않고 기존 강조를 보존한다.
                문자모양_적용_현재선택(
                    폰트=폰트 if 선택.get("font", True) else None,
                    크기_pt=크기 if 선택.get("size", True) else None,
                    굵게=문단굵게 if "복사_문단모양" in 표준서식_설정 else (True if 문단굵게 else None),
                )
                hwp_run("Cancel")

                # 내어쓰기(실제 Shift+Tab) 방식을 적용하기 전에 커서를
                # 반드시 문단 시작으로 옮겨 정확한 문단 기준 위치를 잡는다. 이 위치를
                # 기준으로 오프셋을 더해 선택하므로, 앞 단계(굵게 처리 등)가 커서를
                # 어디에 두었든 영향을 받지 않는다.
                hwp_run("MoveParaBegin")
                문단_기준위치 = hwp.GetPos()
                현재_text = 현재문단_텍스트()

                # 문두 라벨을 미리 굵게 해 첫 줄 폭을 확정한다.
                문두_라벨_굵게_선반영(문단_기준위치, 현재_text)

                실제기호, _ = leading_marker(현재_text)
                복사_문단모양_적용(실제기호 if 실제기호 in 표준서식_설정.get("복사_문단모양", {}) else 기호)
                계층_추가서식_적용(실제기호 if 실제기호 in (표준서식_설정.get("계층_추가서식") or {}) else 기호)
                복사_간격_규칙_적용(실제기호 if 실제기호 in (표준서식_설정.get("복귀_간격") or {}) else 기호, 현재_text)

                # 기호 자체 bold는 실제 기호가 존재하는 문단에만 적용한다.
                if 자체_기호_매칭 and 기호만굵게 and not 문단굵게:
                    hwp_run("MoveParaBegin")
                    문단_시작 = hwp.GetPos()
                    기호위치 = len(현재_text) - len(현재_text.lstrip())
                    mapped = scheme.canonical(현재_text) if scheme else None
                    문단_범위_선택(문단_시작, 기호위치, mapped[1] if mapped else 기호위치 + 1)
                    문자모양_적용_현재선택(굵게=True)
                    hwp_run("Cancel")
                # 예시가 본문은 굵게·기호는 보통으로 썼으면 기호만 보통으로 되돌린다(2026-10-17, XML 경로와 같음).
                elif 자체_기호_매칭 and 문단굵게 and 기호 in (표준서식_설정.get("기호_보통") or ()):
                    hwp_run("MoveParaBegin")
                    문단_시작 = hwp.GetPos()
                    기호위치 = len(현재_text) - len(현재_text.lstrip())
                    mapped = scheme.canonical(현재_text) if scheme else None
                    끝 = mapped[1] if mapped else 기호위치 + len(기호)
                    끝 += len(현재_text[끝:]) - len(현재_text[끝:].lstrip(' \t'))   # 기호 뒤 빈칸도 보통
                    문단_범위_선택(문단_시작, 기호위치, 끝)
                    문자모양_적용_현재선택(굵게=False)
                    hwp_run("Cancel")

                # 문단 모양 복사·계층 서식·간격·기호 글자 서식이 끝난 뒤 내어쓰기를 확정한다.
                # 앞서 적용하면 복사_문단모양_적용이 LeftMargin/Indentation을 덮어쓸 수 있다.
                hwp_run("MoveParaBegin")
                최종_문단_기준위치 = hwp.GetPos()
                최종_문단_text = 현재문단_텍스트()
                if (표준서식_내어쓰기_사용 and 선택.get("indent", True) and not 최종_내어쓰기_예정
                        and not any(item.lstrip(' \t\u00a0\u3000').rstrip('\r\n')
                                    == 최종_문단_text.lstrip(' \t\u00a0\u3000').rstrip('\r\n')
                                    for item in _표준서식_XML텍스트)
                        and 문단_내어쓰기_기준_오프셋(최종_문단_text) is not None):
                    문단_내어쓰기_적용(
                        최종_문단_기준위치, 최종_문단_text,
                        폰트크기_pt=크기, 폰트=폰트, 굵게=문단굵게)
        return bind_function(표준서식_문단_처리, _docfit_namespace)
    if _docfit_symbol == '빈문단_분류':
        def 빈문단_분류(text, begin, end):
            """'blank'(공백만 있는 빈 문단), 'marker'(항목기호 문장), 'other'.

            표·그림 같은 컨트롤은 글자 없이 위치만 차지하므로, 위치 길이가 공백
            글자 수와 같을 때만 빈 문단으로 본다. 표 하나만 있는 문단은
            MoveParaBegin이 표 뒤(pos 8)에 멈춰 시작·끝이 같아 보이므로, 시작
            위치가 0이 아니면 빈 문단이 아니다(실측: 공고문 표 5개가 지워짐).
            """
            body = (text or '').rstrip('\r\n')
            if not body.strip():
                if begin[2] != 0:
                    return 'other'
                units = len(body.encode('utf-16-le')) // 2
                return 'blank' if end[2] - begin[2] == units else 'other'
            # 날짜 줄('2026. 9. 24.')처럼 번호로 보이는 머리 문단은 항목기호 문장이 아니다.
            if not 보고서_문단역할(body):
                return 'other'
            # 'ㅇ'·'*'처럼 기호만 있고 내용이 빈 문단은 제출서식의 작성란이다. 그
            # 앞뒤 빈 줄은 작성 여백이므로 지우지 않는다(실측: 공고문 '□ (자유작성)'
            # 아래 작성란 여백이 모두 지워짐).
            marker_end = 문장부호_마커_끝위치(body)
            if marker_end is not None and not body[marker_end:].strip():
                return 'template'
            return 'marker'
        return bind_function(빈문단_분류, _docfit_namespace)
    if _docfit_symbol == '항목기호문장_사이_빈문단_찾기':
        def 항목기호문장_사이_빈문단_찾기(kinds):
            """분류 목록에서 지울 빈 문단의 인덱스.

            - 앞뒤 가장 가까운 비어 있지 않은 문단이 모두 항목기호 문장인 빈 문단
            - 문서 끝의 빈 문단(뒤에 아무 내용도 없음). 문서 끝 빈 문단 하나가 다음
              쪽으로 넘어가면 내용 없는 빈 쪽이 인쇄된다(실측: 4쪽이 빈 문단 하나).
            """
            result = []
            for index, kind in enumerate(kinds):
                if kind != 'blank':
                    continue
                before = next((k for k in reversed(kinds[:index]) if k != 'blank'), None)
                after = next((k for k in kinds[index + 1:] if k != 'blank'), None)
                if before == 'marker' and after == 'marker':
                    result.append(index)
                elif before is not None and after is None:
                    result.append(index)
            return result
        return bind_function(항목기호문장_사이_빈문단_찾기, _docfit_namespace)
    if _docfit_symbol == '본문_컨트롤_문단번호':
        def 본문_컨트롤_문단번호():
            """본문(리스트 0)에서 표·그림·글상자 등 컨트롤이 놓인 문단 번호.

            빈 줄 삭제가 컨트롤 문단을 빈 문단으로 오인해 표를 통째로 지우지
            않도록 막는 이중 안전장치다. 읽지 못하면 빈 집합을 돌려준다.
            """
            result = set()
            try:
                ctrl = hwp.HeadCtrl
                while ctrl:
                    try:
                        anchor = ctrl.GetAnchorPos(0)
                        if anchor.Item("List") == 0:
                            result.add(anchor.Item("Para"))
                    except Exception:
                        pass
                    ctrl = ctrl.Next
            except Exception as e:
                진단로그(f'본문 컨트롤 위치 확인 실패(무시): {e}')
            return result
        return bind_function(본문_컨트롤_문단번호, _docfit_namespace)
    if _docfit_symbol == '항목기호문장_사이_빈줄_삭제':
        def 항목기호문장_사이_빈줄_삭제(붙임_빈줄_넣기=False):
            """항목기호 문장 사이·문서 끝 빈 줄과 붙임 앞 여분 빈 줄을 지운다.

            붙임_빈줄_넣기=True이면 지우지 않고, 위에 글이 있는데 빈 줄이 없는 붙임 앞에 빈 줄 1줄만 넣는다.
            문단을 늘리는 작업이라 항목기호 서식(앞 빈칸 맞춤)이 끝난 뒤에 따로 부른다(실측 2026-10-08:
            앞에서 넣으면 뒤따르는 앞 빈칸 맞춤의 삭제가 일부 문단에서 실패해 빈칸이 늘었다).
            """
            global 쪽범위_본문_문단
            if hwp is None:
                return True
            original = hwp.GetPos()
            paragraphs = []
            texts = []
            컨트롤문단 = 본문_컨트롤_문단번호()
            try:
                hwp_run('MoveDocBegin')
                while True:
                    if 중단_요청됨():
                        return False
                    hwp_run('MoveParaBegin')
                    begin = hwp.GetPos()
                    text = 현재문단_텍스트()
                    hwp.SetPos(*begin)
                    hwp_run('MoveParaEnd')
                    end = hwp.GetPos()
                    kind = 'other' if begin[1] in 컨트롤문단 else 빈문단_분류(text, begin, end)
                    paragraphs.append((begin, end, kind))
                    texts.append(None if begin[1] in 컨트롤문단 else text)
                    hwp.SetPos(*begin)
                    hwp_run('MoveNextParaBegin')
                    after = hwp.GetPos()
                    if after == begin or after[0] != 0 or after[1] <= begin[1]:
                        break

                kinds = [p[2] for p in paragraphs]
                targets = set()
                붙임_삭제, 붙임_삽입 = 붙임_앞빈줄_계획(texts, kinds)
                if 붙임_빈줄_넣기:
                    붙임_삭제 = []
                else:
                    붙임_삽입 = []
                    if 항목기호문장_빈줄_삭제_사용:
                        targets.update(항목기호문장_사이_빈문단_찾기(kinds))
                targets.update(붙임_삭제)
                targets = {index for index in targets if index > 0 and 쪽범위_안인가(paragraphs[index][0])}
                붙임_삽입 = [index for index in 붙임_삽입 if 쪽범위_안인가(paragraphs[index][0])]
                삭제수 = 0
                삽입수 = 0
                # 뒤에서부터 고쳐야 앞 문단의 위치가 바뀌지 않는다. 빈 문단은 바로 앞
                # 문단 끝에 합쳐 지운다 — 뒤 문단에 합치면 항목기호 문장의 문단 모양이
                # 빈 문단의 모양으로 바뀐다. 붙임 앞 빈 줄은 바로 앞 문단 끝에서 문단을 나눠 넣는다.
                for index in sorted(targets | set(붙임_삽입), reverse=True):
                    if 중단_요청됨():
                        return False
                    prev_end = paragraphs[index - 1][1]
                    if index not in targets:
                        try:
                            hwp.SetPos(*prev_end)
                            if hwp_run('BreakPara') is False:
                                raise RuntimeError('문단 나누기 실패')
                            삽입수 += 1
                        except Exception as e:
                            로그(f'붙임 앞 빈 줄 넣기 중 오류(건너뜀): {e}')
                        continue
                    blank_end = paragraphs[index][1]
                    try:
                        hwp.SetPos(*prev_end)
                        if hwp.SelectText(prev_end[1], prev_end[2], blank_end[1], blank_end[2]) is False:
                            raise RuntimeError('빈 줄 범위 선택 실패')
                        hwp_run('Delete')
                        삭제수 += 1
                    except Exception as e:
                        로그(f'항목기호 문장 사이 빈 줄 삭제 중 오류(건너뜀): {e}')
                    finally:
                        hwp_run('Cancel')
                if (삭제수 or 삽입수) and 쪽범위_본문_문단 is not None:
                    # 지우거나 넣은 빈 문단은 모두 범위 안이라 그만큼 뒤 문단 번호가 바뀐다. 고정한 범위 끝을 같이
                    # 옮기지 않으면 뒤 단계가 다음 쪽(범위 밖) 문단까지 고친다.
                    시작, 끝 = 쪽범위_본문_문단
                    쪽범위_본문_문단 = (시작, max(시작, 끝 - 삭제수 + 삽입수))
                if 붙임_빈줄_넣기:
                    if 삽입수:
                        로그(f'붙임 앞 빈 줄 넣기: {삽입수}개')
                else:
                    로그(f'항목기호 문장 사이·문서 끝 빈 줄 삭제: {삭제수}개')
                return True
            finally:
                try:
                    hwp_run('MoveDocBegin')
                except Exception:
                    try:
                        hwp.SetPos(*original)
                    except Exception:
                        pass
        return bind_function(항목기호문장_사이_빈줄_삭제, _docfit_namespace)
    if _docfit_symbol == '글꼴형식_모으기':
        def 글꼴형식_모으기(header):
            """HWPX 헤더 글꼴 목록의 {글꼴 이름: 형식(TTF·HFT)}. 같은 이름이 두 형식으로 있으면 설치된 TTF를 쓴다."""
            형식들 = {}
            for item in header.iter():
                if item.tag.rsplit("}", 1)[-1] != "font":
                    continue
                이름, 형식 = item.get("face"), (item.get("type") or "").upper()
                if 이름 and 형식 and 형식들.get(이름) != "TTF":
                    형식들[이름] = 형식
            return 형식들
        return bind_function(글꼴형식_모으기, _docfit_namespace)
    if _docfit_symbol == '글꼴형식_등록':
        def 글꼴형식_등록(형식들):
            """서식 프로필(예시 보고서)·문서에서 읽은 글꼴 형식을 글꼴 지정에 쓰는 표에 더한다(TTF가 우선)."""
            for 이름, 형식 in (형식들 or {}).items():
                if 이름 and 형식 and _글꼴형식.get(이름) != "TTF":
                    _글꼴형식[이름] = str(형식).upper()
        return bind_function(글꼴형식_등록, _docfit_namespace)
    if _docfit_symbol == '표준서식_전체_적용':
        def 표준서식_전체_적용():
            if 중단_요청됨():
                return False
            _표준서식_문단위간격_상태.reset()
            로그("표준서식적용 시작")
            if 표준서식_여백_사용:
                if 쪽범위_사용중():
                    로그("쪽 범위 지정: 편집 여백은 구역 전체에 적용되는 설정이라 이번 작업에서는 건드리지 않습니다.")
                else:
                    페이지_여백_설정(표준서식_설정["여백_mm"])
                    용지_다르면_알림()

            if not 항목기호문장_사이_빈줄_삭제():
                return False

            # 표 첫 칸에 로마자 숫자가 있는 중제목 표 문단(글 없음)도 3단계 중제목 문단 위 여백을 받는다.
            표문단 = 본문_표_문단번호() if 표준서식_문단위간격_사용 and not 표준서식_설정.get("복제_들여쓰기_유지") else {}
            _표칸영역.clear()
            hwp_run("MoveDocBegin")
            문단_순번 = 0
            구조_시작됨 = False
            _간격규칙_상태.update(첫문장=False, 직전깊이=None)
            상단_비기호_문단수 = 0
            활성_세트_들여쓰기 = None
            활성_세트_기호규칙 = None

            while True:
                if 중단_요청됨():
                    return False
                if 쪽범위_끝지남():
                    break

                문단_순번 += 1
                text = 현재문단_텍스트()
                헤더_역할 = None
                상속_기호_매칭 = None

                if text and text.strip():
                    자체_기호_매칭 = 표준서식_기호규칙_찾기(text) if 표준서식_기호_사용 else None

                    if (
                        not 자체_기호_매칭
                        and 활성_세트_들여쓰기 is not None
                        and 활성_세트_기호규칙 is not None
                        and 세트문장_후속문단인가(활성_세트_들여쓰기, text)
                    ):
                        상속_기호_매칭 = 활성_세트_기호규칙
                    else:
                        활성_세트_들여쓰기 = None
                        활성_세트_기호규칙 = None

                        if 자체_기호_매칭:
                            구조_시작됨 = True
                            활성_세트_들여쓰기 = 자체_기호_매칭[1]
                            활성_세트_기호규칙 = 자체_기호_매칭
                        elif not 구조_시작됨:
                            상단_비기호_문단수 += 1
                            if 상단_비기호_문단수 == 1:
                                헤더_역할 = "title"
                            elif 상단_비기호_문단수 == 2:
                                헤더_역할 = "dateinfo"

                위치 = hwp.GetPos()
                if (not (text and text.strip()) and 위치[0] == 0 and 위치[1] in 표문단
                        and 로마자_중제목_표인가(표문단[위치[1]])):
                    간격_pt = 표준서식_문단위간격_찾기("", 계층="midtitle")
                    if 쪽범위_안인가() and 간격_pt is not None:
                        hwp.SetPos(0, 위치[1], 0)
                        hwp_run("MoveParaBegin")
                        hwp_run("MoveSelParaEnd")
                        문단_위간격_적용_현재선택(간격_pt)
                        hwp_run("Cancel")
                        hwp.SetPos(*위치)
                # 제목·일자 판정 등 문맥은 문서 처음부터 읽어 이어 가되, 서식은 쪽 범위 안 문단에만 적용한다.
                if 쪽범위_안인가():
                    표준서식_문단_처리(
                        문단_순번,
                        헤더_역할=헤더_역할,
                        상속_기호_매칭=상속_기호_매칭,
                    )
                if not 다음_문단으로_진행():
                    break

            if not 항목기호문장_사이_빈줄_삭제(붙임_빈줄_넣기=True):
                return False
            로그("표준서식적용 완료")
            return True
        return bind_function(표준서식_전체_적용, _docfit_namespace)
    if _docfit_symbol == '표준서식_선행_적용':
        def 표준서식_선행_적용(파일명):
            """보고서 표준서식을 입힌다. 입혔으면 True, 꺼져 있으면 None, 실패·중단이면 False.

            뒤에 최종 내어쓰기 단계가 있으면 문단별 내어쓰기를 그 단계로 미룬다(최종_내어쓰기_예정).
            """
            global 최종_내어쓰기_예정
            if not (표준서식_선행_사용 and stage_enabled(선택_세부작업, 'standard_format', 작업_모드)):
                return None
            단계표시("보고서 표준서식")
            상태(f"{파일명} : 보고서 표준서식")
            최종_내어쓰기_예정 = bool(
                작업_모드 in ('format', 'all') and 표준서식_내어쓰기_사용
                and stage_enabled(선택_세부작업, 'hanging_indent'))
            try:
                hwp_run('Cancel')
                순회_시작()
                if 표준서식_전체_적용() is False:
                    return False
            finally:
                최종_내어쓰기_예정 = False
            return True
        return bind_function(표준서식_선행_적용, _docfit_namespace)
    raise KeyError(_docfit_symbol)
