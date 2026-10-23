"""Compatibility exports for formatter definitions split by feature.

Raw exports retain this module's globals for existing patch targets. Runtime
exports are still rebound by bind_function into each invocation's RunContext.
"""
from docfit_engine.runtime import bind_function, bind_class, _plain_bind
from . import formatter_utils
from . import formatter_analysis
from . import formatter_titles
from . import formatter_tables

_SPLIT_INSTALLERS = {}
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_utils.SYMBOLS, formatter_utils._install))
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_analysis.SYMBOLS, formatter_analysis._install))
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_titles.SYMBOLS, formatter_titles._install))
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_tables.SYMBOLS, formatter_tables._install))


def _export_split_function(function, namespace):
    # A raw re-export must look up dependencies through formatter.X, so patches
    # of that path continue to affect calls across feature module boundaries.
    exported = _plain_bind(function, globals())
    exported.__qualname__ = function.__qualname__
    globals()[function.__name__] = exported
    return exported


def _bind_split_function(function, namespace):
    return bind_function(_export_split_function(function, namespace), namespace)


def __getattr__(name):
    installer = _SPLIT_INSTALLERS.get(name)
    if installer is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return installer(_docfit_namespace=globals(), _docfit_symbol=name,
                     bind_function=_export_split_function)


def _install(*, _docfit_namespace, _docfit_symbol):
    global _내어쓰기_여백쌍_설정
    global _표준서식_문단위간격_표, 기본_계층_스타일, 표준서식_문단위간격_찾기, 기호글꼴_적용, 표글꼴_적용, _hwp_설치폴더_후보_레지스트리, _hwp_설치폴더_후보_공통경로, 한글_폰트_폴더_자동감지, _ttf_패밀리이름, 한글_폰트_목록, 한컴_번들_폰트_폴더_목록, 한글_폰트_목록_전체, 서식_기본값_전역_복원, 프로그램_폴더, 번들_리소스_폴더, 기본_서식프로파일, 서식프로파일_목록, _제목뒤간격_다시재기, _표_텍스트, _표_서명, _정밀표_프로필_추출, hwpx_서식_분석, 보고서머리_프로필_반영, 보고서머리_hwpx_처리, 예시문서_기본이름, _분석본_보관, 한글파일_서식_분석, 교정용_hwpx_준비, 분석용_hwpx_준비, 스타일분석_파일생성, 스타일분석_요약, 서식프로파일_표시이름, 문서_markdown_내보내기, 복사_문단모양_적용, 계층_추가서식_값, 복사_간격_규칙_적용, 계층_추가서식_적용, 개요붙임_원본자료, 붙임_유형판별, 붙임_대상찾기, 중제목_글칸들, 중제목_유형판별, 중제목_대상찾기, 중제목_원본자료, _구역_본문폭, _예정_좌우여백, _최종_본문폭, _빈_문단인가, _문단사이_빈줄_삭제, _문단_본문글, _서식표_뒤_빈줄_삭제, _서식표_가로맞춤, _중제목_번호굵게_적용, 중제목_표서식_복사, _중제목_글자치수, _중제목_문단폭, _중제목_칸폭_맞춤, 개요_표인가, 제목_xml이름, 제목_자식, 제목_셀들, 제목_문단들, 제목_문자열, _한칸_제목글인가, _기타_제목표인가, _한칸_제목표인가, 제목_유형판별, 제목_대상찾기, 서식표_종류판별, _서식표_예시, 제목2행1열_원본자료, 제목_원본자료, 제목_참조병합, 날짜칸인가, 표_날짜칸_한줄, 표날짜칸_hwpx_처리, 두글자칸_hwpx_처리, 빈줄서식_hwpx_처리, 강조낱말_hwpx_처리, 개요첫칸_hwpx_처리, 제목_날짜칸_한줄, 제목_표서식_복사, _정밀표_매칭점수, _정밀표_셀서식_복사, _정밀표_글자위치_복사, _표_글_그대로, _정밀표_같은표만, _정밀표_글같음, 정밀표_서식_적용, 제목_문단_가운데정렬, 제목_괄호부연_축소, 제목_hwpx_처리, _제목_임시hwpx_저장, 이전_작업_임시폴더_정리, _제목_임시폴더_정리, 서식구조_조사, 제목4종_현재문서_조사, 제목4종_현재문서_적용, 붙임_hwpx_처리, 중제목_hwpx_처리, 제목_부제_크기_해석, 제목_부제_크기_반영, 제목_담당자_글_반영, _설정_담당자_글인가, _서식표_기준, 제목_부제_크기, _칸_글_지우기, _칸_날짜_현행화, _빈칸_서식_참조_변환, _칸_글_넣기, 서식표_생성, _제목개요_빈줄_정리, _서식표_글, _서식표_글_확인, 라벨_서식표_적용, _문서_표번호, _서식표_번호_부여, _hwpx_안전_저장, _문단_일반글, _문단_준말_판별, _문단_준말_제외사유, _문단_글_바꾸기, 준말_hwpx_처리, 제목개요폭_hwpx_처리, 연결부호탭_hwpx_처리, 콜론라벨_hwpx_처리, 상자서식_hwpx_처리, 쪽번호_hwpx_처리, 준말_사용표_만들기, 준말_선행적용, 기본표서식, _기본표서식_대상인가, 기본표서식_hwpx_처리, 표너비_hwpx_처리, 기본표서식_선행적용, _위첨자_글자모양, _문단_별표_대상, 별표위첨자_hwpx_처리, 별표위첨자_선행적용, _한글_글꼴표, _글꼴_확보, _글자모양_글꼴크기, _본문기호_글꼴, 붙임글꼴_hwpx_처리, 글자서식_선행적용, 붙임2종_현재문서_조사, 제목붙임_선행적용, 정밀표_선행적용, 붙임2종_현재문서_적용, 설정_폴더, 서식프로파일_폴더, 서식예시_정보_폴더, 서식예시_폴더, 첫쪽_그림_만들기, 번들_서식예시_찾기, _json_파일_읽기, 서식예시_서명, 설정_파일_경로, 설정_불러오기, 설정_저장, 진행률, 단계시간_시작, _단계시간_닫기, 단계시간_구간, 단계시간_끝, 단계시간_분류, 단계시간_요약줄, 단계초기화, 중단_요청됨, _문서_편집_시도, hwp_run, _문두보호_줄건너뜀, 번들_상용구_파일_찾기, 글자상용구_폴더, 본문상용구_폴더, 번들_본문상용구_폴더, 상용구_폴더_준비, 상용구_전용폴더_찾기, 텍스트_삽입, 문자모양_적용_현재선택, _다른_글꼴형식으로_재실행, 문단_줄간격_적용_현재선택, HwpUnit_pt, HwpUnit_mm, 문단_위간격_적용_현재선택, 문단_아래간격_pt_현재문단, 문단_아래간격_적용_현재선택, 텍스트_너비_em, _문단_공백_건너뛰기, 복사_내어쓰기_규칙, 문단_내어쓰기_기준_오프셋, _여는낫표_건너뛰기, _문단_기호뒤_오프셋, _문단_본문시작_오프셋, 문단_자간보호_선행부_오프셋, 문단_내어쓰기_적용_현재선택, _반각전각_폭배수, 문단_선행부_폭_HWPUNIT, _내어쓰기_값_설정, 내어쓰기_기호선택_허용, 재검사_대상인가, 재검사_영역인가, 문단_내어쓰기_전체_갱신, _내어쓰기_한문단, _붙임목록_내어쓰기_대상수집, _붙임번호_기준위치_실측, _붙임목록_번호_내어쓰기_적용, 문단_내어쓰기_적용, _부모문단_유형, _부연설명_문단인가, _선행공백_길이, _캐럿위치_폭_실측, 부연설명_앞빈칸_수, _부연설명_앞빈칸_적용, _부연설명_한문단, 부연설명_들여쓰기_전체_적용, _별표_위치_실측, _별표_정렬_적용, _별표_한문단, 별표_정렬_전체_적용, _mm_hwpunit, _현재_쪽여백, _표준_또는_원본여백, 페이지_여백_설정, 용지_다르면_알림, 들여쓰기_공백_맞추기, 표준서식_기호규칙_찾기, 본문형_일반문장인가, _사용자서식인가, 알파_일괄서식_가능, 사용자서식_XML추가값, _GDI_글꼴인가, _알파_글꼴형식, _알파_라벨_굵게범위, 표준서식_hwpx_처리, _알파_한줄문단인가, 표준서식_문단_처리, 빈문단_분류, 항목기호문장_사이_빈문단_찾기, 본문_컨트롤_문단번호, 항목기호문장_사이_빈줄_삭제, 글꼴형식_모으기, 글꼴형식_등록, _서식통일_문두요소_범위, _서식통일_글자모양, _서식통일_공백제거, _서식통일_HWPX_분석, _서식통일_run_text, _서식통일_XML문단, _서식통일_위치텍스트, _서식통일_음영값, 서식통일_표본, _서식통일_그룹키, _서식통일_현재_HWPX, _서식통일_불일치_구간, _서식통일_부연괄호_불일치_구간, _서식통일_굵기_불일치_구간, 서식통일_대표, _서식통일_표지인가, _서식통일_제목표_표본, _서식통일_체계경계, _서식통일_참고표_이웃대표_보완, _서식통일_대표값_사용자검토, _서식통일_적용영역_사용자검토, 서식통일_결과창_반영, _결과창_띄우는가, _서식통일_최종결과_사용자확인, _서식통일_미확정_항목, _서식통일_미확정_빨간표시, _서식통일_문단앞간격_적용, _서식통일_내어쓰기_필요, _서식통일_내어쓰기_상태, _서식통일_문단서식_적용, _서식통일_글자요소_적용, _서식통일_색값, _서식통일_색_적용, _서식통일_문단내어쓰기_적용, _서식통일_문단자간_조정, _서식통일_글꼴크기만, _서식통일_글꼴크기_대표, _서식통일_XML_조사, _서식통일_COM_조사, 서식통일_전체_적용, 서식통일_자간조정_반영, 서식통일_문장_마무리, _서식통일_마무리_위치로, 서식통일_보류자간_재조정, _서식통일_표모형, 서식통일_표_전체_적용, 표준서식_전체_적용, 괄호_안쪽, 대괄호인가, 괄호_문두_라벨인가, 괄호_뒤_콜론인가, 세트후속_범위괄호_라벨인가, 문단_범위_선택, 선택범위_현재크기_pt, 괄호_축소량_pt, 대괄호_축소_제외, 괄호_텍스트_크기_축소_현재선택, 문두_라벨_굵게_제외_문단인가, 항목기호_키, 일관성_굵게_머리말_범위, 문두_라벨_굵게_선반영, 괄호_및_라벨_텍스트_문단_처리, 라벨괄호_계획, 라벨괄호_hwpx_처리, 표안_문단_구분, 공백규칙_글변환, 문장부호뒤공백_글변환, 글규칙_hwpx_처리, 현재문서_XML단계_적용, 괄호_텍스트_크기_축소_전체_적용, _셀_안쪽여백_단계축소, 표_셀_안쪽여백_전체_적용, 본문_가용너비_mm, 표_전체너비_mm, 현재셀_너비_mm, 표_열너비_순서대로_설정, 표_열너비_본문맞춤_시도, 표_열너비_본문맞춤_전체_적용, 표_셀_테두리_적용, 표_테두리_삼선표_적용, 표_테두리_전체_적용, 넓은_표칸_줄인가, 컨트롤_내부_자간조정, 한칸표_자간조정, 컨트롤_내부_문장부호_처리, 끝위치추출, 다음_문단으로_진행, 쪽표시, 절약시간_표시, 절약시간_분초_표시, 번들_고양이_그림_찾기, 번들_앱아이콘_찾기, _앱아이콘_적용, 처리_쪽수_구하기, 쪽범위_사용중, 쪽범위_안인가, 쪽범위_끝지남, 순회_시작, 범위_다음_문단으로_진행, 현재_표셀인가, 숫자_표칸인가, 표셀_자간_제외인가, 컨트롤_줄병합_대상인가, 쪽범위_계산, 저장파일명, 표준서식_선행_적용, 문서_처리_1회, _문서_처리_1회, 문서_전체_자간_초기화, 바이너리_HWP_파일인가, 텍스트파일_읽기, 텍스트_hwpx로_변환, 라벨블록_한글삽입, AI답변_개조식_변환, 텍스트_hwpx_단독변환, 외부문서_hwpx로_변환, PDF_서식_이식, _박스그림표_한글표_삽입, _박스그림_줄인가, _박스그림_남은_문단, _박스그림표_교체, 박스그림_전체_적용, 저장결과_규칙검수
    installer = _SPLIT_INSTALLERS.get(_docfit_symbol)
    if installer is not None:
        return installer(_docfit_namespace=_docfit_namespace, _docfit_symbol=_docfit_symbol,
                         bind_function=_bind_split_function)
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
    if _docfit_symbol == '텍스트_너비_em':
        def 텍스트_너비_em(text):
            총 = 0.0
            for ch in text:
                폭 = unicodedata.east_asian_width(ch)
                총 += 1.0 if 폭 in ("W", "F") else 0.5
            return 총
        return bind_function(텍스트_너비_em, _docfit_namespace)
    if _docfit_symbol == '_문단_공백_건너뛰기':
        def _문단_공백_건너뛰기(text, idx):
            """문단 내 실제 문자 오프셋을 유지하면서 공백류만 건너뛴다."""
            while idx < len(text) and text[idx] in (" ", "\t", "\u00a0", "\u3000"):
                idx += 1
            return idx
        return bind_function(_문단_공백_건너뛰기, _docfit_namespace)
    if _docfit_symbol == '복사_내어쓰기_규칙':
        def 복사_내어쓰기_규칙(text):
            """서식 복사한 예시 보고서에서 이 문단 계층의 내어쓰기 기준. 서식 복사가 아니거나 규칙이 없으면 None.

            after_marker(기호 뒤 글 시작)·fixed(복사한 고정 값)·none(내어쓰기 없음). 예전 프로필의 after_label(라벨 규칙)은
            폐지돼(2026-10-10) 규칙 없음으로 읽는다: 기본 동작(콜론 라벨은 콜론 뒤 본문, 괄호 라벨은 기호 뒤)이 이전
            after_label과 같은 결과다.
            """
            rules = 표준서식_설정.get("내어쓰기_규칙") or {}
            if not rules:
                return None
            scheme = globals().get('활성_항목기호_체계')
            marker, _ = leading_marker(scheme.style_text(text) if scheme else text)
            rule = rules.get(marker) or rules.get(서식요소.unify_marker(text)[0])
            if rule is None and marker == "**":
                # ** 전용 규칙이 없으면 대표 기호 *의 내어쓰기 규칙을 그대로 상속한다.
                rule = rules.get("*")
            return None if rule == "after_label" else rule
        return bind_function(복사_내어쓰기_규칙, _docfit_namespace)
    if _docfit_symbol == '문단_내어쓰기_기준_오프셋':
        def 문단_내어쓰기_기준_오프셋(text):
            """문단 첫 화면줄에서 Shift+Tab을 실행할 본문 시작 문자 위치.

            서식 복사한 계층 규칙이 '기호 뒤'면 라벨을 글에 포함해 기호 뒤 글 시작으로, '고정 값'·'없음'이면 내어쓰기
            규칙이 손대지 않도록 None(복사한 첫 줄 값을 그대로 씀)이다. 규칙이 없을 때는 콜론 라벨이면 콜론 뒤 본문,
            괄호 라벨 '( )'이면 라벨 뒤가 아니라 기호 뒤 첫 글자(2026-10-10 개정)에 맞춘다.
            """
            규칙 = 복사_내어쓰기_규칙(text)
            if 규칙 in ("fixed", "none"):
                return None
            if 규칙 == "after_marker":
                # 콜론 라벨은 예시 규칙과 관계없이 콜론 뒤 본문 첫 글자 기준(불변 규칙, 2026-10-17). 콜론이 없으면
                # 기본 판정도 기호 뒤(괄호 라벨은 '(')라 예전 결과와 같다.
                return _여는낫표_건너뛰기(text, _문단_본문시작_오프셋(text))
            return _여는낫표_건너뛰기(text, _문단_본문시작_오프셋(text))
        return bind_function(문단_내어쓰기_기준_오프셋, _docfit_namespace)
    if _docfit_symbol == '_여는낫표_건너뛰기':
        def _여는낫표_건너뛰기(text, offset):
            """본문이 '「법령」'처럼 여는 낫표로 시작하면 낫표 다음 글자 위치로 옮긴다."""
            if offset is None:
                return None
            body = text.rstrip("\r\n")
            if (offset + 1 < len(body) and body[offset] in _내어쓰기_건너뛸_여는낫표
                    and not body[offset + 1].isspace()):
                return offset + 1
            return offset
        return bind_function(_여는낫표_건너뛰기, _docfit_namespace)
    if _docfit_symbol == '_문단_기호뒤_오프셋':
        def _문단_기호뒤_오프셋(text):
            """항목기호(□·ㅇ·-·* 등)와 뒤 빈칸을 건너뛴 글 시작 문자 위치. 괄호·콜론 라벨은 글에 포함한다.

            기호로 시작하지 않는 문단이거나 기호 뒤에 글이 없으면 None.
            """
            if not text:
                return None
            text = text.rstrip("\r\n")
            start = _문단_공백_건너뛰기(text, 0)
            if start >= len(text):
                return None
            tail = text[start:]
            scheme = globals().get('활성_항목기호_체계')
            mapped = scheme.canonical(text) if scheme else None
            if not (mapped or tail[0] in 공문서_기호 or tail[0] in "*＊☞ㅁ" or any(p.match(tail) for p in 항목_패턴)):
                return None
            from docfit_core.xml_hanging_indent import marker_end_offset
            marker_end = mapped[1] if mapped else marker_end_offset(text)
            if marker_end is None:
                marker_end = start + 1
            idx = _문단_공백_건너뛰기(text, marker_end)
            if idx >= len(text) or text[idx] in "\r\n":
                return None
            return idx
        return bind_function(_문단_기호뒤_오프셋, _docfit_namespace)
    if _docfit_symbol == '_문단_본문시작_오프셋':
        def _문단_본문시작_오프셋(text, 괄호라벨_뒤=False):
            """내어쓰기 기준이 되는 글 시작 문자 위치.

            - 콜론 라벨('일시:', '- 추진부서 :', '(방식) :')이 있으면 콜론 뒤 본문(현행 유지).
            - 괄호 라벨 '( )'만 있으면 라벨 뒤가 아니라 항목기호 뒤 첫 글자 — 라벨의 '('(2026-10-10 개정:
              괄호라벨 뒤 첫 글자 기준 폐지). 대괄호 '[ ]'는 원래부터 라벨로 보지 않아 같은 기준이다.
            - 괄호라벨_뒤=True는 옛 동작(괄호 라벨 뒤까지)이며 자간·장평 조정이 건드리지 않을 선행부의 끝을
              찾는 데만 쓴다(`문단_자간보호_선행부_오프셋`).
            """
            if not text:
                return None
            # 문단 끝 개행만 제외. 내부 강제 줄바꿈 뒤 문장은 라벨 탐색하지 않는다.
            text = text.rstrip("\r\n")
            start = _문단_공백_건너뛰기(text, 0)
            if start >= len(text):
                return None
            tail = text[start:]
            # 일반 문장의 구두점은 대상으로 삼지 않는다.
            scheme = globals().get('활성_항목기호_체계')
            구조마커 = ((scheme.canonical(text) if scheme else None) or tail[0] in 공문서_기호 or tail[0] in "*＊☞ㅁ"
                        or any(p.match(tail) for p in 항목_패턴))
            if not 구조마커:
                # 기존 세트 후속 라벨: '(6~16번) : 본문'
                m = re.match(r"[（(][^()（）\r\n]+[)）][ \t]*[:：][ \t]*(?=\S)", tail)
                return start + m.end() if m else None
            idx = _문단_기호뒤_오프셋(text)
            if idx is None:
                return None
            # 균형 괄호만 문두 라벨로 인정한다. 붙어 있는 '(연도)지명'은 제외.
            pairs = {"(": ")", "（": "）"}
            if text[idx] in pairs:
                stack = []
                close = None
                for j in range(idx, len(text)):
                    ch = text[j]
                    if ch in "\r\n":
                        break
                    if ch in pairs:
                        stack.append(pairs[ch])
                    elif ch in ")）":
                        if not stack or stack.pop() != ch:
                            break
                        if not stack:
                            close = j
                            break
                if close is not None:
                    label = text[idx + 1:close].strip()
                    after = _문단_공백_건너뛰기(text, close + 1)
                    separated = after > close + 1
                    if after < len(text) and text[after] in ":：":
                        after = _문단_공백_건너뛰기(text, after + 1)
                        separated = True
                    year = re.fullmatch(r"['’‘]?[0-9]{2,4}(?:년|[./-][0-9]{1,2})*\.?", label)
                    # '(개요)「법령명」…'처럼 문두 라벨 바로 뒤에 여는 인용부호가
                    # 붙는 공문서 표기도 라벨과 본문의 경계다. 공백만 요구하면
                    # 기준 오프셋이 괄호 앞에 머물러 둘째 줄이 '(개요)' 아래로 간다.
                    quote_boundary = (after < len(text)
                                      and text[after] in "「『‘“'\"")
                    # 라벨 뒤에 콜론이 오면 콜론 라벨('(방식) :')이라 현행대로 콜론 뒤 본문이 기준이다.
                    콜론라벨 = text[_문단_공백_건너뛰기(text, close + 1):][:1] in (":", "：")
                    if (label and not year and (separated or quote_boundary)
                            and after < len(text) and text[after] not in "\r\n"
                            and (콜론라벨 or 괄호라벨_뒤)):
                        return after
                return idx
            m = re.match(r"([^\n\r:：]{1,30}?)[ \t]*[:：][ \t]+(?=\S)", text[idx:])
            # 콜론 라벨은 '일    시', '교육내용'처럼 짧은 항목명이다. 공백을 뺀 12자를 넘으면
            # 문장 속 콜론('… 지원 규모 : (’25)…')이라 라벨로 보면 둘째 줄이 문장 중간까지 밀린다.
            if (m and len("".join(m.group(1).split())) <= 12
                    and not re.search(r"[/\\]|https?$|^\d+$", m.group(1).strip(), re.I)):
                return idx + m.end()
            return idx
        return bind_function(_문단_본문시작_오프셋, _docfit_namespace)
    if _docfit_symbol == '문단_내어쓰기_적용_현재선택':
        def 문단_내어쓰기_적용_현재선택(들여쓰기_pt):
            """구형 수치 기반 보정용 함수.

            v1.10부터 표준서식의 주 내어쓰기 경로에서는 사용하지 않는다.
            Shift+Tab 실행이 불가능한 특수 상황의 호환성을 위해 함수 자체만 유지한다.
            """
            if hwp is None:
                return
            try:
                act = hwp.HAction
                pset = hwp.HParameterSet.HParaShape
                act.GetDefault("ParagraphShape", pset.HSet)
                여백 = hwp.PointToHwpUnit(들여쓰기_pt)
                pset.LeftMargin = 여백
                pset.Indentation = -여백
                act.Execute("ParagraphShape", pset.HSet)
            except Exception as e:
                로그(f"내어쓰기 적용 실패(무시): {e}")
        return bind_function(문단_내어쓰기_적용_현재선택, _docfit_namespace)
    if _docfit_symbol == '_반각전각_폭배수':
        def _반각전각_폭배수(ch):
            """글자 한 개의 가로 폭 배수를 반환한다(전각=1.0, 반각=0.5)."""
            w = unicodedata.east_asian_width(ch)
            if w in ("W", "F"):
                return 1.0
            if w == "A":
                # 가운데점(·) 등 폭이 모호한 문자는 공문서 문맥상 전각으로 본다.
                return 1.0
            if ch in _좁은문장부호:
                return _좁은문장부호_폭배수
            # Na/H(스페이스, 라틴 등)
            return 0.5
        return bind_function(_반각전각_폭배수, _docfit_namespace)
    if _docfit_symbol == '문단_선행부_폭_HWPUNIT':
        def 문단_선행부_폭_HWPUNIT(문단_시작위치, text, 오프셋):
            """문단 시작부터 본문 첫 글자(오프셋) 직전까지 '선행부'의 가로 폭을
            HWPUNIT으로 계산한다.

            선행부 각 글자의 실제 글자모양(크기·장평)을 한글에서 읽어 폭을 합산하므로
            실행 시점·정렬·재시도와 무관하게 항상 같은 값이 나온다(결정적). 이 값이
            둘째 줄 내어쓰기 위치가 된다.
            """
            if 오프셋 <= 0:
                return 0
            총 = 0.0
            for i in range(오프셋):
                ch = text[i]
                높이 = None
                장평 = 100.0
                try:
                    문단_범위_선택(문단_시작위치, i, i + 1)
                    act = hwp.HAction
                    pset = hwp.HParameterSet.HCharShape
                    act.GetDefault("CharShape", pset.HSet)
                    hwp_run("Cancel")
                    높이 = float(pset.Height)
                    try:
                        장평 = float(pset.RatioHangul)
                    except Exception:
                        장평 = 100.0
                except Exception:
                    try:
                        hwp_run("Cancel")
                    except Exception:
                        pass
                if not 높이 or 높이 <= 0:
                    # 글자모양을 못 읽으면 기본 크기(가장 흔한 15pt)로 근사한다.
                    높이 = 1500.0
                    장평 = 100.0
                총 += 높이 * (장평 / 100.0) * _반각전각_폭배수(ch)
            return int(round(총))
        return bind_function(문단_선행부_폭_HWPUNIT, _docfit_namespace)
    if _docfit_symbol == '_내어쓰기_값_설정':
        def _내어쓰기_값_설정(value):
            """다른 문단 속성을 덮어쓰지 않고 첫 줄 값만 바꾼다."""
            action = hwp.CreateAction("ParagraphShape")
            params = action.CreateSet()
            params.SetItem("Indentation", value)
            if action.Execute(params) is False:
                raise RuntimeError("첫 줄 내어쓰기 값 설정 실패")
        return bind_function(_내어쓰기_값_설정, _docfit_namespace)
    if _docfit_symbol == '_내어쓰기_여백쌍_설정':
        def _내어쓰기_여백쌍_설정(left, indentation):
            """왼쪽 여백과 내어쓰기를 한 번에 설정한다.

            한/글 내어쓰기(Indentation<0)는 첫 줄을 LeftMargin에 두고 둘째 줄부터 |Indentation|만큼 더 민다
            (기본 서식.hwpx·v1.78 결과로 확인, 2026-10-21). 예전 설명(첫 줄 = LeftMargin+Indentation)은 거꾸로였다.
            """
            action = hwp.CreateAction("ParagraphShape")
            params = action.CreateSet()
            params.SetItem("LeftMargin", int(left))
            params.SetItem("Indentation", int(indentation))
            if action.Execute(params) is False:
                raise RuntimeError("왼쪽 여백·내어쓰기 쌍 설정 실패")
        return bind_function(_내어쓰기_여백쌍_설정, _docfit_namespace)
    if _docfit_symbol == '내어쓰기_기호선택_허용':
        def 내어쓰기_기호선택_허용(text):
            """서식 프로파일의 기호별 '내어쓰기' 선택이 꺼진 기호 문단이면 False."""
            매칭 = 표준서식_기호규칙_찾기(text) if text else None
            if not 매칭:
                return True
            return 표준서식_설정.get("스타일_속성선택", {}).get(매칭[0], {}).get("indent", True)
        return bind_function(내어쓰기_기호선택_허용, _docfit_namespace)
    if _docfit_symbol == '재검사_대상인가':
        def 재검사_대상인가(pos):
            """2차 이후 재검사에서 이 위치의 문단을 검사해야 하는지."""
            return 재검사_대상문단 is None or tuple(pos[:2]) in 재검사_대상문단
        return bind_function(재검사_대상인가, _docfit_namespace)
    if _docfit_symbol == '재검사_영역인가':
        def 재검사_영역인가(area):
            """2차 이후 재검사에서 이 컨트롤 영역(리스트)을 검사해야 하는지."""
            return 재검사_대상문단 is None or any(key[0] == area for key in 재검사_대상문단)
        return bind_function(재검사_영역인가, _docfit_namespace)
    if _docfit_symbol == '문단_내어쓰기_전체_갱신':
        def 문단_내어쓰기_전체_갱신(대상문단=None):
            """최종 문자 서식/자간으로 본문 내어쓰기만 재계산한다.

            대상문단((리스트, 문단) 번호 집합)을 주면 그 문단만 계산한다.
            값이 실제로 바뀐 문단은 내어쓰기_변경문단에 모아 다음 재검사 범위로 쓴다.
            """
            내어쓰기_변경문단.clear()
            if 대상문단 is not None and not 대상문단:
                return True
            붙임번호_대상 = _붙임목록_내어쓰기_대상수집()
            붙임번호_기준점들 = {}
            순회_시작()
            while True:
                if 중단_요청됨():
                    return False
                hwp_run("MoveParaBegin")
                if 대상문단 is not None and tuple(hwp.GetPos()[:2]) not in 대상문단:
                    if not 범위_다음_문단으로_진행():
                        break
                    continue
                text = 현재문단_텍스트()
                if 현재_한칸표인가():
                    if not 범위_다음_문단으로_진행():
                        break
                    continue
                _내어쓰기_한문단(text, 붙임번호_대상, 붙임번호_기준점들)
                if not 범위_다음_문단으로_진행():
                    break
            return True
        return bind_function(문단_내어쓰기_전체_갱신, _docfit_namespace)
    if _docfit_symbol == '_내어쓰기_한문단':
        def _내어쓰기_한문단(text, 붙임번호_대상, 붙임번호_기준점들):
            """커서가 있는 문단(문단 시작)의 내어쓰기를 계산해 적용한다(문단_내어쓰기_전체_갱신·문단 세트 공용)."""
            정규키 = (text or '').lstrip(' \t\u00a0\u3000').rstrip('\r\n')
            if (_알파_일괄서식_문서 and any(
                    item.lstrip(' \t\u00a0\u3000').rstrip('\r\n') == 정규키
                    for item in globals().get('_표준서식_XML기준확정', ()))):
                return  # 예시와 같은 문장만 예시의 문단 여백을 지킨다. 그 밖은 1.78처럼 Shift+Tab 실측(2026-10-21).
            현재키 = tuple(hwp.GetPos()[:2])
            if re.match(r'^\s*(?:ㅁ|□)\s+\S', text or ''):
                # 최상위 항목 제목(ㅁ/□)은 하위 설명 문장처럼 매달지 않는다.
                # 기존 값도 초기화해 앞선 단계에서 적용된 들여쓰기가 남지 않게 한다.
                _내어쓰기_여백쌍_설정(0, 0)
                return
            if 현재키 in 붙임번호_대상:
                기준문단, _ = 붙임번호_대상[현재키]
                기준키 = 기준문단[0]
                if 기준키 not in 붙임번호_기준점들:
                    붙임번호_기준점들[기준키] = _붙임번호_기준위치_실측(*기준문단)
                    if 붙임번호_기준점들[기준키] is None:
                        로그(f"[붙임 내어쓰기] 첫 번호 기준점 측정 실패: {기준문단[1].strip()[:60]}")
                기준값 = 붙임번호_기준점들[기준키]
                if 기준값 is None:
                    로그(f"[붙임 내어쓰기] 번호 기준을 측정하지 못했습니다: {text.strip()[:60]}")
                # 숫자와 점으로 된 어절은 다음 줄의 번호와 세로로 같은 위치다(계단식으로 밀지 않는다).
                elif not _붙임목록_번호_내어쓰기_적용(hwp.GetPos(), text, 기준값[0]):
                    로그(f"[붙임 내어쓰기] 번호 정렬을 건너뜀: {text.strip()[:60]}")
            elif (문단_내어쓰기_기준_오프셋(text) is not None
                    and 내어쓰기_기호선택_허용(text)):
                문단_내어쓰기_적용(hwp.GetPos(), text)
        return bind_function(_내어쓰기_한문단, _docfit_namespace)
    if _docfit_symbol == '_붙임목록_내어쓰기_대상수집':
        def _붙임목록_내어쓰기_대상수집():
            """문서 맨 끝의 번호 붙임 묶음만 훑어 번호 세로 정렬 대상을 수집한다."""
            paragraphs = []
            original = hwp.GetPos()
            try:
                순회_시작()
                while True:
                    paragraphs.append((tuple(hwp.GetPos()[:2]), 현재문단_텍스트()))
                    if not 범위_다음_문단으로_진행():
                        break
            finally:
                try:
                    hwp.SetPos(*original)
                except Exception:
                    pass
            blocks = 끝붙임번호묶음_찾기([text for _, text in paragraphs])
            targets = {}
            for start, end in blocks:
                anchor = paragraphs[start]
                for 단계, index in enumerate(range(start, end + 1)):
                    key = paragraphs[index][0]
                    targets[key] = (anchor, 단계)
            return targets
        return bind_function(_붙임목록_내어쓰기_대상수집, _docfit_namespace)
    if _docfit_symbol == '_붙임번호_기준위치_실측':
        def _붙임번호_기준위치_실측(문단_시작위치, text):
            """첫 번호 위치(와 번호 앞 빈칸 폭)를 글꼴 기준으로 실측한다."""
            offset = 붙임번호_오프셋(text)
            if offset is None:
                return None
            # 수집 단계의 위치는 (리스트, 문단) 두 값뿐이다. SetPos는 (리스트, 문단, 위치) 세 값이 필요하다.
            문단_시작위치 = tuple(문단_시작위치)[:3]
            if len(문단_시작위치) == 2:
                문단_시작위치 += (0,)
            original_pos = hwp.GetPos()
            begin = None
            original_indent = None
            try:
                hwp_run("Cancel")
                hwp.SetPos(*문단_시작위치)
                hwp_run("MoveParaBegin")
                begin = hwp.GetPos()
                original_indent = hwp.ParaShape.Item("Indentation")
                left = int(hwp.ParaShape.Item("LeftMargin"))
                _내어쓰기_값_설정(0)
                hwp.SetPos(*begin)
                hwp_run("MoveLineEnd")
                end = hwp.GetPos()
                # 양쪽 정렬 첫 줄은 빈칸이 늘어난다. 줄 끝에서 바로 SetPos로 옮기면 한/글이 늘기 전 글자 위치로 Shift+Tab을 계산하므로(둘째 줄이 기준 글자보다 왼쪽), 이동 명령으로 줄 배치를 먼저 반영시킨다.
                hwp_run("MoveParaBegin")
                units = len(text[:offset].encode("utf-16-le")) // 2
                target = (begin[0], begin[1], begin[2] + units)
                if end[:2] != begin[:2] or target[2] >= end[2]:
                    return None
                if hwp.SetPos(*target) is False or tuple(hwp.GetPos()) != target:
                    return None
                if hwp_run("ParagraphShapeIndentAtCaret") is False:
                    return None
                prefix_width = _캐럿위치_폭_실측(begin, offset)
                prefix_without_gap = len(text[:offset].rstrip(" \t\u00a0\u3000"))
                label_width = _캐럿위치_폭_실측(begin, prefix_without_gap)
                if prefix_width is None or label_width is None or prefix_width <= label_width:
                    return None
                return left + prefix_width, prefix_width - label_width
            except Exception as e:
                로그(f"붙임 번호 기준점 실측 실패: {e}")
                return None
            finally:
                if original_indent is not None and begin is not None:
                    try:
                        hwp.SetPos(*begin)
                        _내어쓰기_값_설정(original_indent)
                    except Exception:
                        pass
                try:
                    hwp.SetPos(*original_pos)
                except Exception:
                    pass
        return bind_function(_붙임번호_기준위치_실측, _docfit_namespace)
    if _docfit_symbol == '_붙임목록_번호_내어쓰기_적용':
        def _붙임목록_번호_내어쓰기_적용(문단_시작위치, text, 기준위치):
            """번호 위치를 기준 번호와 세로로 같게 맞추고 꺾인 줄은 내용에 맞춘다."""
            offset = 붙임번호_오프셋(text)
            if hwp is None or offset is None:
                return False
            original_pos = None
            original_indent = None
            original_left = None
            begin = None
            changed = False
            try:
                original_pos = hwp.GetPos()
                hwp_run("Cancel")
                if hwp.SetPos(*문단_시작위치) is False:
                    raise RuntimeError("붙임 항목 문단 이동 실패")
                hwp_run("MoveParaBegin")
                begin = hwp.GetPos()
                original_indent = hwp.ParaShape.Item("Indentation")
                original_left = hwp.ParaShape.Item("LeftMargin")
                _내어쓰기_값_설정(0)
                changed = True
                prefix_width = _캐럿위치_폭_실측(begin, offset) if offset else 0
                marker_end = text.find(".", offset) + 1
                marker_width = _캐럿위치_폭_실측(begin, marker_end)
                if marker_width is None or marker_width <= 0 or prefix_width is None:
                    raise RuntimeError("번호 마커 폭 실측 실패")
                # 한/글 내어쓰기는 첫 줄을 왼쪽여백에 그대로 두고 둘째 줄부터 |값|만큼 더 민다.
                # 첫 줄 번호가 기준 번호 위치에 오도록 왼쪽여백을 잡고, 꺾인 줄은 번호 뒤 내용에 맞춘다.
                # 첫 줄은 LeftMargin에서 시작하고 번호 글자는 그 뒤 prefix 폭만큼 진행한 위치다(v1.78 방식).
                # 예전(a95fd54~)에는 번호 폭을 더해 붙임 묶음이 밀리고 둘째 번호가 첫 번호와 어긋났다(2026-10-21).
                target_left = 기준위치 - prefix_width
                target_indent = -marker_width
                if target_left < 0:
                    raise RuntimeError("붙임 번호 첫 줄 위치가 본문 왼쪽 경계를 벗어남")
                action = hwp.CreateAction("ParagraphShape")
                params = action.CreateSet()
                params.SetItem("LeftMargin", target_left)
                params.SetItem("Indentation", target_indent)
                if action.Execute(params) is False:
                    raise RuntimeError("붙임 번호 내어쓰기 설정 실패")
                if (int(hwp.ParaShape.Item("LeftMargin")) != target_left
                        or int(hwp.ParaShape.Item("Indentation")) != target_indent):
                    raise RuntimeError("붙임 번호 내어쓰기 값 검증 실패")
                if (int(original_left) != target_left or int(original_indent) != target_indent):
                    내어쓰기_변경문단.add(tuple(begin[:2]))
                진단로그(f"[붙임 내어쓰기] 번호 오프셋 {offset}: {text.strip()[:60]}")
                return True
            except Exception as e:
                if changed and original_indent is not None and begin is not None:
                    try:
                        hwp.SetPos(*begin)
                        action = hwp.CreateAction("ParagraphShape")
                        params = action.CreateSet()
                        params.SetItem("LeftMargin", original_left)
                        params.SetItem("Indentation", original_indent)
                        action.Execute(params)
                    except Exception as restore_error:
                        로그(f"붙임 내어쓰기 원래 값 복원 실패: {restore_error}")
                로그(f"붙임 번호 내어쓰기 실패(건너뜀): {e}")
                return False
            finally:
                if original_pos is not None:
                    try:
                        hwp.SetPos(*original_pos)
                    except Exception:
                        pass
        return bind_function(_붙임목록_번호_내어쓰기_적용, _docfit_namespace)
    if _docfit_symbol == '문단_내어쓰기_적용':
        def 문단_내어쓰기_적용(문단_시작위치, text, 폰트크기_pt=None, 폰트=None, 굵게=None):
            """실제 Shift+Tab 폭을 재서 여백·내어쓰기를 쌍으로 적용한다.

            글꼴·굵기·장평·자간·탭 폭은 한글이 계산한다. 긴 라벨로 기준점이
            첫 화면줄 밖에 있으면 잘못된 내어쓰기를 적용하지 않고 로그를 남긴다.
            선택된 텍스트나 탭을 삽입하지 않는다. 음수 내어쓰기만 설정하면 첫 줄이
            페이지 왼쪽 밖으로 밀리므로, 기존 첫 줄 좌표를 유지하도록 LeftMargin도 보정한다.
            """
            if 현재_한칸표인가():
                return False
            offset = 문단_내어쓰기_기준_오프셋(text)
            if hwp is None or offset is None or offset <= 0:
                return False
            original_pos = None
            original_indent = None
            original_left = None
            begin = None
            changed = False
            try:
                original_pos = hwp.GetPos()
                hwp_run("Cancel")
                if hwp.SetPos(*문단_시작위치) is False:
                    raise RuntimeError("대상 문단 이동 실패")
                hwp_run("MoveParaBegin")
                begin = hwp.GetPos()
                original_indent = hwp.ParaShape.Item("Indentation")
                original_left = int(hwp.ParaShape.Item("LeftMargin"))
                # 종전 결함 산출물은 LeftMargin=0, Indentation<0으로 저장됐다. 이를 다시
                # 입력해도 음수 기준점을 물려받지 않도록 잘못된 쌍은 원점으로 복구한다.
                # 한/글은 첫 줄을 LeftMargin에 둔다. 왼쪽 여백은 그대로 두고 내어쓰기 값만 바꾼다(v1.78 방식).
                # 다만 예전 결함(a95fd54~)이 남긴 (LeftMargin = -Indentation) 쌍은 첫 줄을 그만큼 밀었으므로 0으로 되돌린다.
                baseline_left = max(0, original_left)
                if int(original_indent) < 0 and original_left == -int(original_indent):
                    baseline_left = 0
                # 기존 내어쓰기를 지운 동일한 첫 줄 상태에서 매번 계산한다.
                _내어쓰기_값_설정(0)
                changed = True
                hwp.SetPos(*begin)
                hwp_run("MoveLineEnd")
                line_end = hwp.GetPos()
                # 양쪽 정렬 첫 줄은 빈칸이 늘어난다. 줄 끝에서 바로 SetPos로 옮기면 한/글이 늘기 전 글자 위치로 Shift+Tab을 계산하므로(둘째 줄이 기준 글자보다 왼쪽), 이동 명령으로 줄 배치를 먼저 반영시킨다.
                hwp_run("MoveParaBegin")
                # 한글 위치값은 UTF-16 코드 단위. 보조평면 문자도 올바르게 이동.
                units = len(text[:offset].encode("utf-16-le")) // 2
                target = (begin[0], begin[1], begin[2] + units)
                if line_end[:2] != begin[:2] or target[2] >= line_end[2]:
                    raise RuntimeError("본문 시작점이 첫 화면줄 안에 없습니다")
                if hwp.SetPos(*target) is False or tuple(hwp.GetPos()) != target:
                    raise RuntimeError("본문 시작점 이동 실패")
                if hwp_run("ParagraphShapeIndentAtCaret") is False:
                    raise RuntimeError("Shift+Tab 명령 실패")
                value = hwp.ParaShape.Item("Indentation")
                if value >= 0:
                    raise RuntimeError("Shift+Tab 실행 후 내어쓰기 값이 설정되지 않았습니다")
                target_left = baseline_left
                _내어쓰기_여백쌍_설정(target_left, int(value))
                actual_left = int(hwp.ParaShape.Item("LeftMargin"))
                actual_indent = int(hwp.ParaShape.Item("Indentation"))
                if actual_left != target_left or actual_indent != int(value):
                    raise RuntimeError("왼쪽 여백·내어쓰기 쌍 검증 실패")
                if actual_left != original_left or actual_indent != int(original_indent):
                    내어쓰기_변경문단.add(tuple(begin[:2]))
                진단로그(f"[내어쓰기] 기준 {offset}, 왼쪽 여백 {actual_left}, 첫 줄 {actual_indent}: {text.strip()[:60]}")
                return True
            except Exception as e:
                if changed and original_indent is not None and original_left is not None and begin is not None:
                    try:
                        hwp.SetPos(*begin)
                        _내어쓰기_여백쌍_설정(original_left, original_indent)
                    except Exception as restore_error:
                        로그(f"내어쓰기 원래 값 복원 실패: {restore_error}")
                로그(f"내어쓰기 적용 실패(건너뜀): {e}")
                return False
            finally:
                if original_pos is not None:
                    try:
                        hwp.SetPos(*original_pos)
                    except Exception:
                        pass
        return bind_function(문단_내어쓰기_적용, _docfit_namespace)
    if _docfit_symbol == '_부모문단_유형':
        def _부모문단_유형(text):
            """제목/본문/내용이면 그 유형 문자열, 아니면 None."""
            s = (text or "").lstrip()
            if not s:
                return None
            scheme = globals().get('활성_항목기호_체계')
            if scheme and scheme.is_excluded(text):
                return None
            mapped = scheme.canonical(text) if scheme else None
            if mapped:
                return {'□': '제목', 'ㅇ': '본문', '-': '내용'}[mapped[0]]
            c = s[0]
            if c in _제목_기호:
                return "제목"
            if c in _본문_기호:
                return "본문"
            if c in _내용_기호:
                return "내용"
            return None
        return bind_function(_부모문단_유형, _docfit_namespace)
    if _docfit_symbol == '_부연설명_문단인가':
        def _부연설명_문단인가(text):
            """*, **, ※ 로 시작하면 부연설명."""
            s = (text or "").lstrip()
            return bool(s) and (s[0] == "*" or s[0] == "※")
        return bind_function(_부연설명_문단인가, _docfit_namespace)
    if _docfit_symbol == '_선행공백_길이':
        def _선행공백_길이(text):
            i = 0
            while i < len(text) and text[i] in (" ", "\t", "\u00a0", "\u3000"):
                i += 1
            return i
        return bind_function(_선행공백_길이, _docfit_namespace)
    if _docfit_symbol == '_캐럿위치_폭_실측':
        def _캐럿위치_폭_실측(문단_시작, 글자수):
            """문단 첫 줄에서 앞 글자수(문자열 길이)만큼의 가로 폭을 한/글에 실측시킨다.

            첫 줄 값을 0으로 두고 그 위치에서 실제 Shift+Tab을 실행해 생긴 내어쓰기
            값을 읽은 뒤, 문단의 원래 첫 줄 값으로 되돌린다. 문단 모양 단위(왼쪽여백과
            같은 단위)로 돌려주며, 위치가 첫 화면줄 밖이거나 실패하면 None.
            """
            original_pos = hwp.GetPos()
            begin = None
            original = None
            try:
                hwp_run("Cancel")
                hwp.SetPos(*문단_시작)
                hwp_run("MoveParaBegin")
                begin = hwp.GetPos()
                original = hwp.ParaShape.Item("Indentation")
                _내어쓰기_값_설정(0)
                hwp.SetPos(*begin)
                hwp_run("MoveLineEnd")
                line_end = hwp.GetPos()
                # 양쪽 정렬 첫 줄은 빈칸이 늘어난다. 줄 끝에서 바로 SetPos로 옮기면 한/글이 늘기 전 글자 위치로 Shift+Tab을 계산하므로(둘째 줄이 기준 글자보다 왼쪽), 이동 명령으로 줄 배치를 먼저 반영시킨다.
                hwp_run("MoveParaBegin")
                text = 현재문단_텍스트()
                units = len(text[:글자수].encode("utf-16-le")) // 2
                target = (begin[0], begin[1], begin[2] + units)
                if line_end[:2] != begin[:2] or target[2] >= line_end[2]:
                    return None
                if hwp.SetPos(*target) is False or tuple(hwp.GetPos()) != target:
                    return None
                if hwp_run("ParagraphShapeIndentAtCaret") is False:
                    return None
                value = hwp.ParaShape.Item("Indentation")
                return -int(value) if value < 0 else None
            except Exception as e:
                진단로그(f"[부연설명 들여쓰기] 폭 실측 실패: {e}")
                return None
            finally:
                if begin is not None and original is not None:
                    try:
                        hwp.SetPos(*begin)
                        _내어쓰기_값_설정(original)
                    except Exception:
                        pass
                try:
                    hwp.SetPos(*original_pos)
                except Exception:
                    pass
        return bind_function(_캐럿위치_폭_실측, _docfit_namespace)
    if _docfit_symbol == '부연설명_앞빈칸_수':
        def 부연설명_앞빈칸_수(부모_유형, marker):
            """위 문단 유형(제목/본문/내용/None)과 부연설명 기호로 앞 빈칸 수를 정한다. 규칙 밖이면 None.

            서식 복사 프로필이 예시에서 배운 위 문단별 칸 수(fmt["부연설명_앞빈칸"], 위 문단 없음은 "")가 있으면
            그 값을 먼저 쓰고, 예시에 없는 조합은 기본표(부연설명_앞빈칸)로 대신한다.
            """
            배운표 = 표준서식_설정.get("부연설명_앞빈칸")
            if isinstance(배운표, dict):
                값 = (배운표.get(부모_유형 or "") or {}).get(marker)
                if 값 is not None:
                    return int(값)
            return 부연설명_앞빈칸.get(부모_유형, {}).get(marker)
        return bind_function(부연설명_앞빈칸_수, _docfit_namespace)
    if _docfit_symbol == '_부연설명_앞빈칸_적용':
        def _부연설명_앞빈칸_적용(문단_시작, text, 칸수, 왼쪽여백=None):
            """부연설명 문단 앞 빈칸을 칸수만큼으로 바꾸고 왼쪽여백을 맞춘다.

            바뀌었으면 True, 이미 같으면 False, 실패하면 None.
            """
            if 현재_한칸표인가():
                return False
            lead = _선행공백_길이(text)
            try:
                hwp.SetPos(*문단_시작)
                hwp_run("MoveParaBegin")
                기존_여백 = int(hwp.ParaShape.Item("LeftMargin"))
                빈칸_같음 = text[:lead] == " " * 칸수
                여백_같음 = 왼쪽여백 is None or 기존_여백 == int(왼쪽여백)
                if 빈칸_같음 and 여백_같음:
                    return False
                if not 빈칸_같음:
                    if lead > 0:
                        if 문단_범위_선택(문단_시작, 0, lead) is False or hwp_run("Delete") is False:
                            raise RuntimeError("앞 빈칸 삭제 실패")
                    hwp.SetPos(*문단_시작)
                    텍스트_삽입(" " * 칸수)
                if not 여백_같음:
                    hwp.SetPos(*문단_시작)
                    act = hwp.CreateAction("ParagraphShape")
                    pset = act.CreateSet()
                    pset.SetItem("LeftMargin", int(왼쪽여백))
                    if act.Execute(pset) is False:
                        raise RuntimeError("왼쪽여백 설정 실패")
                hwp.SetPos(*문단_시작)
                cur_text = 현재문단_텍스트()
                진단로그(f"[부연설명 들여쓰기] 앞 빈칸 {lead} → {칸수}칸: {cur_text.strip()[:50]}")
                # 앞 빈칸이 바뀌면 글 시작 위치도 바뀌므로 내어쓰기(Shift+Tab)를 다시 맞춘다.
                if 표준서식_내어쓰기_사용 and stage_enabled(선택_세부작업, 'hanging_indent'):
                    hwp.SetPos(*문단_시작)
                    문단_내어쓰기_적용(문단_시작, cur_text)
                return True
            except Exception as e:
                로그(f"부연설명 들여쓰기 적용 실패(무시): {e}")
                return None
        return bind_function(_부연설명_앞빈칸_적용, _docfit_namespace)
    if _docfit_symbol == '_부연설명_한문단':
        def _부연설명_한문단(문단_시작, text, 상태, 부모대상=None):
            """부연설명 들여쓰기의 문단 하나 처리(상태['부모']에 위 제목/본문 문단을 이어 받는다). 적용했으면 True."""
            결과 = False
            if text and text.strip():
                정규키 = text.lstrip(' \t\u00a0\u3000').rstrip('\r\n')
                유형 = _부모문단_유형(text)
                부모 = 상태.get('부모')
                if 유형 is not None:
                    상태['부모'] = (문단_시작, 유형)
                elif (_알파_일괄서식_문서 and any(
                        item.lstrip(' \t\u00a0\u3000').rstrip('\r\n') == 정규키
                        for item in _표준서식_XML텍스트)):
                    return False  # XML 단계에서 이미 항목별 공백·여백을 확정했다.
                elif _부연설명_문단인가(text):
                    marker, _ = leading_marker(text)
                    들여쓰기_선택 = 표준서식_설정.get("스타일_속성선택", {}).get(marker, {}).get("indent", True)
                    대상 = 부모대상 is None or (부모 is not None and tuple(부모[0][:2]) in 부모대상)
                    칸수 = 부연설명_앞빈칸_수(부모[1] if 부모 else None, marker)
                    if 대상 and 들여쓰기_선택 and 칸수 is not None:
                        왼쪽여백 = None
                        if 부모 is not None:
                            hwp.SetPos(*부모[0])
                            왼쪽여백 = int(hwp.ParaShape.Item("LeftMargin"))
                        if _부연설명_앞빈칸_적용(문단_시작, text, 칸수, 왼쪽여백):
                            결과 = True
                            내어쓰기_변경문단.add(tuple(문단_시작[:2]))
                    hwp.SetPos(*문단_시작)
                else:
                    # 제목/본문/내용도 부연설명도 아닌 일반 문단(번호 항목 등)이 끼면 연결이 끊긴다.
                    상태['부모'] = None
            return 결과
        return bind_function(_부연설명_한문단, _docfit_namespace)
    if _docfit_symbol == '부연설명_들여쓰기_전체_적용':
        def 부연설명_들여쓰기_전체_적용(부모대상=None):
            """각 부연설명(*, **, ※)의 앞 빈칸을 위 문단 유형별 칸 수로 맞춘다(부연설명_앞빈칸).

            왼쪽여백은 위 제목/본문/내용 문단과 같게 둔다. 부모대상((리스트, 문단) 집합)을 주면
            그 부모에 딸린 부연설명만 다시 맞춘다. 옮긴 부연설명은 내어쓰기_변경문단에 더한다.
            """
            if not (부연설명_들여쓰기_사용 or 표준서식_설정.get("부연설명_앞빈칸")):
                return True
            if 중단_요청됨():
                return False
            if 부모대상 is not None and not 부모대상:
                return True
            if 부모대상 is None:
                로그("부연설명(*, **, ※) 들여쓰기 적용 시작")
            순회_시작()
            부모 = None        # (부모 문단 시작 위치, 유형)
            적용수 = 0
            while True:
                if 중단_요청됨():
                    return False
                hwp_run("MoveParaBegin")
                문단_시작 = hwp.GetPos()
                text = 현재문단_텍스트()

                상태 = {'부모': 부모}
                if _부연설명_한문단(문단_시작, text, 상태, 부모대상):
                    적용수 += 1
                부모 = 상태['부모']

                if not 범위_다음_문단으로_진행():
                    break
            if 부모대상 is None or 적용수:
                로그(f"부연설명 들여쓰기 적용 완료 (적용 {적용수}건)")
            return True
        return bind_function(부연설명_들여쓰기_전체_적용, _docfit_namespace)
    if _docfit_symbol == '_별표_위치_실측':
        def _별표_위치_실측(문단_시작, text):
            """* 문단에서 별표(*) 기호의 실제 가로 위치를 측정한다(왼쪽여백 + 선행 공백 폭)."""
            if hwp is None or not text:
                return None
            try:
                hwp.SetPos(*문단_시작)
                hwp_run("MoveParaBegin")
                left_margin = int(hwp.ParaShape.Item("LeftMargin"))
                lead = _선행공백_길이(text)
                w_lead = 0
                if lead > 0:
                    w_lead = _캐럿위치_폭_실측(문단_시작, lead)
                    if w_lead is None:
                        return None
                return left_margin + w_lead
            except Exception as e:
                진단로그(f"[별표 위치 실측 실패]: {e}")
                return None
        return bind_function(_별표_위치_실측, _docfit_namespace)
    if _docfit_symbol == '_별표_정렬_적용':
        def _별표_정렬_적용(문단_시작, text, 목표_별표_위치):
            """** 문단의 둘째 별표 위치를 바로 앞줄 *의 목표_별표_위치에 맞춘다.

            필요시 앞 빈칸을 삭제하고, 남은 차이는 왼쪽여백으로 보정한다.
            바뀌었으면 True, 이미 같으면 False, 실패하면 None.
            """
            if hwp is None or 현재_한칸표인가():
                return False
            try:
                hwp.SetPos(*문단_시작)
                hwp_run("MoveParaBegin")
                cur_text = 현재문단_텍스트() or text
                lead = _선행공백_길이(cur_text)
                w_lead = _캐럿위치_폭_실측(문단_시작, lead + 1)
                if w_lead is None:
                    return None

                필요_여백 = int(목표_별표_위치) - int(w_lead)
                공백_삭제됨 = False

                # 선행 공백이 있고, 필요 여백이 음수이면(두 번째 별표가 오른쪽에 치우침) 앞 빈칸 삭제.
                # 단, 글꼴의 미세 폭 오차(예: 공백 693 vs 별표 774의 수십 HWPUNIT 차이)로
                # 정상 공백이 과도하게 삭제되지 않도록, 공백 1칸의 절반(약 300 HWPUNIT) 이상 음수일 때만 삭제한다.
                while 필요_여백 <= -300 and _선행공백_길이(cur_text) > 0:
                    if cur_text and cur_text[0] in (" ", "\u00a0"):
                        if 문단_범위_선택(문단_시작, 0, 1) is False:
                            break
                        if hwp_run("Delete") is False:
                            break
                        공백_삭제됨 = True
                        hwp.SetPos(*문단_시작)
                        cur_text = 현재문단_텍스트()
                        lead = _선행공백_길이(cur_text)
                        w_lead = _캐럿위치_폭_실측(문단_시작, lead + 1)
                        if w_lead is None:
                            break
                        필요_여백 = int(목표_별표_위치) - int(w_lead)
                    else:
                        break

                margin = max(0, 필요_여백)
                hwp.SetPos(*문단_시작)
                hwp_run("MoveParaBegin")
                기존_여백 = int(hwp.ParaShape.Item("LeftMargin"))
                여백_변경됨 = False
                if 기존_여백 != margin:
                    act = hwp.CreateAction("ParagraphShape")
                    pset = act.CreateSet()
                    pset.SetItem("LeftMargin", margin)
                    if act.Execute(pset) is False:
                        raise RuntimeError("왼쪽여백 설정 실패")
                    여백_변경됨 = True

                if 공백_삭제됨 or 여백_변경됨:
                    진단로그(f"[별표(**) 정렬] 목표 {목표_별표_위치}, 폭 {w_lead} → 여백 {margin}"
                             f"{'(앞 공백 삭제)' if 공백_삭제됨 else ''}: {cur_text.strip()[:40]}")
                    # 공백이나 여백이 바뀌었으면 내어쓰기(Shift+Tab)도 새 본문 시작점에 맞게 갱신
                    if 표준서식_내어쓰기_사용 and stage_enabled(선택_세부작업, 'hanging_indent'):
                        hwp.SetPos(*문단_시작)
                        문단_내어쓰기_적용(문단_시작, cur_text)
                    return True
                return False
            except Exception as e:
                로그(f"별표(**) 정렬 적용 실패(무시): {e}")
                return None
        return bind_function(_별표_정렬_적용, _docfit_namespace)
    if _docfit_symbol == '_별표_한문단':
        def _별표_한문단(문단_시작, text, 상태):
            """별표(**) 정렬의 문단 하나 처리(상태['별표']에 바로 앞 * 문단의 별표 위치를 이어 받는다). 적용했으면 True."""
            결과 = False
            if text and text.strip():
                정규키 = text.lstrip(' \t\u00a0\u3000').rstrip('\r\n')
                if (_알파_일괄서식_문서 and any(
                        item.lstrip(' \t\u00a0\u3000').rstrip('\r\n') == 정규키
                        for item in _표준서식_XML텍스트)):
                    상태['별표'] = None
                    return False  # XML 기준 이후 COM 별표 정렬이 문단 여백을 덮지 않게 한다.
                marker, _ = leading_marker(text)
                if marker == "*":
                    상태['별표'] = _별표_위치_실측(문단_시작, text)
                elif marker == "**":
                    if 상태.get('별표') is not None and _별표_정렬_적용(문단_시작, text, 상태['별표']):
                        결과 = True
                        내어쓰기_변경문단.add(tuple(문단_시작[:2]))
                    상태['별표'] = None
                else:
                    # 일반 본문이나 다른 구조 기호(※, -, □ 등)가 끼면 별표 연쇄를 끊는다
                    상태['별표'] = None
            # 빈 문단(공백 줄)은 줄바꿈 여백이므로 상태['별표']를 유지한다.
            return 결과
        return bind_function(_별표_한문단, _docfit_namespace)
    if _docfit_symbol == '별표_정렬_전체_적용':
        def 별표_정렬_전체_적용():
            """문서 내 *(주석1) 바로 뒤에 오는 **(주석2)의 둘째 별표 위치를 *에 맞춘다.

            '부연설명 들여쓰기' 설정(기본 꺼짐)과 분리하여 항상 실행하며,
            필요시 ** 앞의 선행 공백을 지워 정확히 정렬한다.
            문단 사이의 빈 문단(줄바꿈 공백줄)은 단락 간 여백이므로 별표 연쇄를 끊지 않는다.
            """
            if hwp is None:
                return True
            if 중단_요청됨():
                return False
            if (표준서식_설정 or {}).get("별표_정렬") is False:
                # 예시를 복사한 서식에서 예시가 ** 문장을 * 아래에 맞추지 않았으면 그대로 둔다(서식 재연 시험, 2026-10-16).
                로그("별표(**) 정렬: 서식 예시가 둘째 별표를 맞추지 않아 건너뜀")
                return True
            순회_시작()
            직전_별표_위치 = None
            적용수 = 0

            while True:
                if 중단_요청됨():
                    return False
                hwp_run("MoveParaBegin")
                문단_시작 = hwp.GetPos()
                text = 현재문단_텍스트()

                상태 = {'별표': 직전_별표_위치}
                if _별표_한문단(문단_시작, text, 상태):
                    적용수 += 1
                직전_별표_위치 = 상태['별표']

                if not 범위_다음_문단으로_진행():
                    break

            if 적용수:
                로그(f"별표(**) 정렬 완료 (적용 {적용수}건)")
            return True
        return bind_function(별표_정렬_전체_적용, _docfit_namespace)
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
    if _docfit_symbol == '_서식통일_문두요소_범위':
        def _서식통일_문두요소_범위(text):
            """항목기호와 바로 뒤 괄호라벨의 (시작, 끝) 문자 오프셋을 돌려준다."""
            if not text:
                return None, None
            시작 = len(text) - len(text.lstrip(" \t\u00a0\u3000"))
            marker_end = 문장부호_마커_끝위치(text)
            if marker_end is None or marker_end <= 시작:
                return None, None
            marker_range = (시작, marker_end)
            label_start = _문단_공백_건너뛰기(text, marker_end)
            if label_start >= len(text) or text[label_start] not in "(（":
                return marker_range, None
            pairs = {"(": ")", "（": "）"}
            stack = []
            for index in range(label_start, len(text)):
                char = text[index]
                if char in "\r\n":
                    break
                if char in pairs:
                    stack.append(pairs[char])
                elif char in ")）":
                    if not stack or stack.pop() != char:
                        return marker_range, None
                    if not stack:
                        return marker_range, (label_start, index + 1)
            return marker_range, None
        return bind_function(_서식통일_문두요소_범위, _docfit_namespace)
    if _docfit_symbol == '_서식통일_글자모양':
        def _서식통일_글자모양(pos):
            """pos 글자 하나의 (글꼴, 크기 HWPUNIT). 실패 시 None."""
            try:
                nxt = _단어모드_다음위치(pos)
                if not nxt:
                    return None
                단어모드_범위선택(pos, nxt)
                pset = hwp.HParameterSet.HCharShape
                hwp.HAction.GetDefault("CharShape", pset.HSet)
                return (str(pset.FaceNameHangul), int(pset.Height))
            except Exception:
                return None
            finally:
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
        return bind_function(_서식통일_글자모양, _docfit_namespace)
    if _docfit_symbol == '_서식통일_공백제거':
        def _서식통일_공백제거(text):
            return "".join(str(text or "").split())
        return bind_function(_서식통일_공백제거, _docfit_namespace)
    if _docfit_symbol == '_서식통일_HWPX_분석':
        def _서식통일_HWPX_분석(문서경로):
            """HWPX의 글자·문단 모양과 본문 직속 문단 목록을 한 번만 읽어 재사용한다.

            서식통일은 문단마다 원본 HWPX를 참조한다. 문단마다 ZIP을 다시 풀면 큰 문서에서
            조사만 수 분이 걸리므로, 경로·수정 시각·크기가 같으면 분석 결과를 재사용한다.
            """
            from zipfile import ZipFile
            from defusedxml import ElementTree as ET
            from docfit_core.style_inventory import _sections, _parse_fonts, _parse_char, _parse_para, _tag
            path = Path(문서경로)
            stat = path.stat()
            key = (str(path), stat.st_mtime_ns, stat.st_size)
            if _서식통일_HWPX_캐시.get("key") == key:
                return _서식통일_HWPX_캐시["value"]
            with open_hwpx_safely(path) as archive:
                header = ET.fromstring(archive.read("Contents/header.xml"))
                fonts = _parse_fonts(header)
                글꼴형식_등록(글꼴형식_모으기(header))
                chars = {item.get("id"): _parse_char(item, fonts)
                         for item in header.iter() if _tag(item) == "charPr"}
                paras = {item.get("id"): _parse_para(item)
                         for item in header.iter() if _tag(item) == "paraPr"}
                문단들 = []
                for name in _sections(archive):
                    section = ET.fromstring(archive.read(name))
                    # GetPos()[1]는 본문 리스트의 문단 번호다. section.iter()를 쓰면
                    # 표 셀·글상자 안의 하위 문단까지 끼어들어 뒤쪽 문단 인덱스가 밀리고,
                    # 다른 쪽 문장의 서식을 읽거나 수정하게 된다. 본문 직속 문단만 센다.
                    문단들.extend(item for item in section if _tag(item) == "p")
            value = {"chars": chars, "paras": paras, "paragraphs": 문단들}
            _서식통일_HWPX_캐시.clear()
            _서식통일_HWPX_캐시.update(key=key, value=value)
            return value
        return bind_function(_서식통일_HWPX_분석, _docfit_namespace)
    if _docfit_symbol == '_서식통일_run_text':
        def _서식통일_run_text(run):
            """(글자, 위치 확실 여부). 표·그림·필드처럼 글자 사이 개체가 있으면 위치를 확신할 수 없다."""
            from docfit_core.style_inventory import _tag
            parts, 확실 = [], True
            for child in run:
                if _tag(child) != "t":
                    확실 = False
                    continue
                parts.append(child.text or "")
                for sub in child:
                    기호 = _서식통일_글자요소.get(_tag(sub))
                    if 기호 is None:
                        확실 = False
                    else:
                        parts.append(기호)
                    parts.append(sub.tail or "")
            return "".join(parts), 확실
        return bind_function(_서식통일_run_text, _docfit_namespace)
    if _docfit_symbol == '_서식통일_XML문단':
        def _서식통일_XML문단(pos):
            """본문 문단 위치의 (HWPX 분석, 문단 요소, HWPX 원문 텍스트, 위치 확실 여부). 없으면 None."""
            문서경로 = _서식통일_현재_HWPX()
            if 문서경로 is None or pos[0] != 0:
                return None
            try:
                from docfit_core.style_inventory import _tag
                분석 = _서식통일_HWPX_분석(문서경로)
                para = 분석["paragraphs"][pos[1]]
                조각 = [_서식통일_run_text(run) for run in para if _tag(run) == "run"]
                return 분석, para, "".join(text for text, _ in 조각), all(확실 for _, 확실 in 조각)
            except Exception:
                return None
        return bind_function(_서식통일_XML문단, _docfit_namespace)
    if _docfit_symbol == '_서식통일_위치텍스트':
        def _서식통일_위치텍스트(pos, text):
            """글자 위치와 맞는 문단 텍스트.

            한/글 GetText는 고정폭·묶음 빈칸을 빼고 돌려준다(' ㅇ  본문' → ' ㅇ본문'). 그러면
            항목기호를 찾지 못해 문단이 조사에서 빠지고, 글자 위치도 어긋난다. 공백을 뺀 글자가
            같을 때만 HWPX 원문을 쓰고, 다르면(다른 문단을 읽은 경우) 한/글 텍스트를 쓴다.
            """
            found = _서식통일_XML문단(pos)
            if found and _서식통일_공백제거(found[2]) == _서식통일_공백제거(text):
                return found[2]
            return text
        return bind_function(_서식통일_위치텍스트, _docfit_namespace)
    if _docfit_symbol == '_서식통일_음영값':
        def _서식통일_음영값(value):
            value = str(value or "").strip().upper()
            return "없음" if value in ("", "NONE", "#FFFFFF") else value
        return bind_function(_서식통일_음영값, _docfit_namespace)
    if _docfit_symbol == '서식통일_표본':
        def 서식통일_표본(시작, text):
            """항목기호·라벨·본문의 기준 서식과 보호할 괄호 구간을 분리해 표본을 만든다."""
            body = (text or "").rstrip("\r\n")
            found = _서식통일_XML문단(시작)
            if found is None or not body.strip():
                return None
            분석, para, 원문, 위치확실 = found
            # 같은 번호의 HWPX 문단이 이 문단이 아니면(앞 단계에서 문단이 지워지는 등) 다른 문장의
            # 서식을 읽게 되므로 건너뛴다. 글자 위치는 HWPX 원문 기준이다(한/글 텍스트는 고정폭
            # 빈칸이 빠져 위치가 밀린다).
            if _서식통일_공백제거(원문) != _서식통일_공백제거(body):
                진단로그(f"[서식통일] HWPX 원문과 문단 글자가 달라 건너뜀: {body.strip()[:40]}")
                return None
            if not 위치확실:
                진단로그(f"[서식통일] 문장 안에 표·그림 등 개체가 있어 글자 위치를 확신할 수 없어 건너뜀: "
                         f"{body.strip()[:40]}")
                return None
            body = 원문.rstrip("\r\n")

            def utf16길이(value):
                return len(value.encode("utf-16-le")) // 2

            # 항목기호와 바로 뒤 라벨은 문장 표준 크기에 포함한다. 문장 중간의
            # 부연괄호는 본문과 별도 규칙(본문보다 2pt 작게)으로 조사·적용한다.
            본문끝 = utf16길이(body)
            marker_span, label_span = _서식통일_문두요소_범위(body)
            marker_span16 = tuple(utf16길이(body[:i]) for i in marker_span) if marker_span else None
            label_span16 = tuple(utf16길이(body[:i]) for i in label_span) if label_span else None
            보호괄호 = tuple(span for span in (marker_span, label_span) if span)
            부연괄호 = 서식통일_부연괄호(body, 보호괄호, include_trailing=True)
            # 문장 안 ※ 참고(예: 'ㅇ 모집기간: … 마감시  ※ 일부 프로그램 상이')는 문서가 본문보다
            # 작게 쓰는 부연이다(실측: 정책회의의 11~13pt ※ 참고가 15pt로 커짐). 조사·교정 범위를
            # ※ 앞에서 끝내 원래 서식을 둔다. 괄호 안 ※는 괄호 규칙을 따른다.
            앞요소끝 = max((span[1] for span in 보호괄호), default=0)
            참고 = body.find("※", 앞요소끝)
            if (참고 > 0 and body[앞요소끝:참고].strip()
                    and not any(left <= 참고 < right for left, right in 부연괄호)):
                본문끝 = utf16길이(body[:참고].rstrip())
                부연괄호 = tuple(span for span in 부연괄호 if span[1] <= 참고)
            부연괄호16 = tuple(tuple(utf16길이(body[:i]) for i in span) for span in 부연괄호)
            try:
                from docfit_core.style_inventory import _tag
                chars, paras = 분석["chars"], 분석["paras"]
                문단모양 = paras.get(para.get("paraPrIDRef"), {})
                cursor = 0
                runs = []
                text_colors = []
                color_runs, shade_runs = [], []
                # 기울임·밑줄·취소선도 글자색처럼 구간별 값을 모아 문장 대부분이 쓰는 값만 비교한다.
                italic_runs, underline_runs, strike_runs = [], [], []
                marker_bold_runs, label_bold_runs, aside_runs = [], [], []
                장평빈도 = Counter()
                for run in (item for item in para if _tag(item) == "run"):
                    run_text = _서식통일_run_text(run)[0]
                    run_length = len(run_text.encode("utf-16-le")) // 2
                    end_offset = cursor + run_length
                    start_selected = cursor
                    end_selected = min(end_offset, 본문끝)
                    char = chars.get(run.get("charPrIDRef"))
                    if char and run_text.strip() and end_selected > start_selected:
                        text_colors.append(str(char.get("color", "")).upper())
                        구간 = ((시작[0], 시작[1], 시작[2] + start_selected),
                                (시작[0], 시작[1], 시작[2] + end_selected))
                        글자수 = len(run_text.strip()) or 1
                        color_runs.append(구간 + (str(char.get("color", "")).upper(), 글자수))
                        shade_runs.append(구간 + (_서식통일_음영값(char.get("shade")), 글자수))
                        italic_runs.append(구간 + (bool(char.get("italic")), 글자수))
                        underline_runs.append(구간 + (str(char.get("underline") or "NONE").upper(), 글자수))
                        # 한/글은 취소선 없는 글자에도 shape="3D"를 저장한다(실측). 선 모양만 취소선으로 본다.
                        strike_runs.append(구간 + (str(char.get("strikeout") or "NONE").upper() not in ("NONE", "3D"),
                                                   글자수))
                        장평빈도[int(char.get("ratio", 100))] += end_selected - start_selected
                        shape = (char["font"].get("hangul"), round(char["size_pt"] * 100))
                        구간들 = [(left, right, False)
                                 for left, right in 서식통일_범위분리(
                                     start_selected, end_selected, 부연괄호16)]
                        구간들.extend((max(start_selected, left), min(end_selected, right), True)
                                      for left, right in 부연괄호16
                                      if right > start_selected and left < end_selected)
                        # 괄호 안도 대표 글꼴 판정·적용 대상이다. 다만 크기는 별도
                        # 규칙(-2pt)이므로 기본 크기 표본/적용에서는 제외한다.
                        for left, right, is_aside in sorted(구간들):
                            if right > left:
                                run_start = (시작[0], 시작[1], 시작[2] + left)
                                run_end = (시작[0], 시작[1], 시작[2] + right)
                                runs.append((run_start, run_end, shape, max(1, right - left), is_aside))
                        for span, bold_runs in ((marker_span16, marker_bold_runs),
                                                (label_span16, label_bold_runs)):
                            if span:
                                left, right = max(start_selected, span[0]), min(end_selected, span[1])
                                if right > left:
                                    bold_runs.append(((시작[0], 시작[1], 시작[2] + left),
                                                      (시작[0], 시작[1], 시작[2] + right),
                                                      bool(char.get("bold")), right - left))
                        for left, right in 부연괄호16:
                            left, right = max(start_selected, left), min(end_selected, right)
                            if right > left:
                                aside_runs.append(((시작[0], 시작[1], 시작[2] + left),
                                                   (시작[0], 시작[1], 시작[2] + right),
                                                   round(char["size_pt"] * 100), right - left))
                    cursor = end_offset
                if cursor < 본문끝:
                    return None
            except Exception as exc:
                진단로그(f"[서식통일] HWPX 문자모양 분석 실패 — 안전을 위해 해당 문단 건너뜀: {exc}")
                return None
            if not runs and not aside_runs:
                return None

            def 문단_요소별_표본값(index):
                빈도 = Counter()
                for run in runs:
                    shape, 길이 = run[2], run[3]
                    is_aside = bool(run[4]) if len(run) > 4 else False
                    if index == 1 and is_aside:
                        continue
                    value = shape[index]
                    if value is not None:
                        빈도[value] += 길이
                전체 = sum(빈도.values())
                if not 전체:
                    return None
                최빈값, 최빈길이 = 빈도.most_common(1)[0]
                if 최빈길이 / 전체 < 서식통일_최소비율:
                    return None
                if sum(1 for count in 빈도.values() if count == 최빈길이) > 1:
                    return None
                return 최빈값

            def weighted_bold(values):
                total = sum(item[3] for item in values)
                if not total:
                    return None
                bold = sum(item[3] for item in values if item[2])
                plain = total - bold
                if max(bold, plain) / total < 서식통일_최소비율:
                    return None
                return bold > plain

            표본모양 = (문단_요소별_표본값(0), 문단_요소별_표본값(1), tuple(runs), {
                "indentation": 문단모양.get("indent"),
                "left_margin": 문단모양.get("left"),
                # HWPX의 음수 first-line offset은 내어쓰기 상태를 뜻한다. 정확한
                # 폭은 문두 라벨마다 다르므로 대표값은 '적용/미적용'으로 집계하고,
                # 적용 단계에서는 한/글 Shift+Tab으로 각 문장의 폭을 실측한다.
                "hanging_indent": int(문단모양.get("indent") or 0) < -20,
                # 한/글이 저장한 줄 배치(lineseg) 수. 내어쓰기는 둘째 줄이 있어야 드러난다.
                "line_count": sum(1 for item in para if _tag(item) == "linesegarray"
                                  for _ in item) or 1,
                # 문단 전체에 쓰이는 장평·문단 위 간격도 문서 대표값과 비교한다. 줄 간격은 쪽 배치를
                # 위해 구역별로 일부러 조정하는 레이아웃 값이라 서식통일 비교 대상에서 뺀다.
                "ratio": 장평빈도.most_common(1)[0][0] if 장평빈도 else None,
                "prev_spacing": 문단모양.get("prev"),
                "marker_bold": weighted_bold(marker_bold_runs),
                "label_bold": weighted_bold(label_bold_runs),
                "marker_bold_runs": tuple(marker_bold_runs),
                "label_bold_runs": tuple(label_bold_runs),
                "parenthetical_size_runs": tuple(aside_runs),
                "red_marked": bool(text_colors) and all(color == "#FF0000" for color in text_colors),
                # 글자색·음영은 문장 대부분(60% 이상)이 쓰는 값을 문장 값으로 본다. 한두 낱말의
                # 강조색은 문장 값을 바꾸지 못하므로 서식통일이 건드리지 않는다.
                "color": 서식통일_우세값((run[2], run[3]) for run in color_runs),
                "shade": 서식통일_우세값((run[2], run[3]) for run in shade_runs),
                "color_runs": tuple(color_runs),
                "shade_runs": tuple(shade_runs),
                "italic": 서식통일_우세값((run[2], run[3]) for run in italic_runs),
                "underline": 서식통일_우세값((run[2], run[3]) for run in underline_runs),
                "strike": 서식통일_우세값((run[2], run[3]) for run in strike_runs),
                "italic_runs": tuple(italic_runs),
                "underline_runs": tuple(underline_runs),
                "strike_runs": tuple(strike_runs),
                # 문단 정렬·좌우 여백. 왼쪽 여백은 항목기호 앞 빈칸으로 들여 쓴 문서와 섞일 수 있어
                # 기호 앞 빈칸 수가 대표값과 같은 문장끼리만 비교한다.
                "align": 문단모양.get("align"),
                "right_margin": 문단모양.get("right"),
                "lead_spaces": len(body) - len(body.lstrip(" \t 　")),
                "position_text": body,
            })
            return 표본모양, 시작, (시작[0], 시작[1], 시작[2] + 본문끝)
        return bind_function(서식통일_표본, _docfit_namespace)
    if _docfit_symbol == '_서식통일_그룹키':
        def _서식통일_그룹키(marker, text, pos):
            """같은 계층(번호 계열을 묶은 항목기호·보고서 역할)의 문장끼리 대표 서식을 비교한다."""
            기호, 역할, 원래기호 = 서식통일_항목기호(text)
            role = 항목기호_역할표().get(원래기호) or 역할 or 보고서_문단역할(text) or "미분류"
            return 기호 or marker, role, "문서 공통"
        return bind_function(_서식통일_그룹키, _docfit_namespace)
    if _docfit_symbol == '_서식통일_현재_HWPX':
        def _서식통일_현재_HWPX():
            """현재 열려 있는 문서의 HWPX 원본 경로를 반환한다."""
            후보 = []
            try:
                후보.append(str(hwp.Path))
            except Exception:
                pass
            try:
                후보.append(str(hwp.XHwpDocuments.Item(0).FullName))
            except Exception:
                pass
            for 경로 in 후보:
                path = Path(경로.strip('"'))
                if path.is_file() and path.suffix.lower() == ".hwpx":
                    return path
            return None
        return bind_function(_서식통일_현재_HWPX, _docfit_namespace)
    if _docfit_symbol == '_서식통일_불일치_구간':
        def _서식통일_불일치_구간(모양, 시작, 끝, 글꼴, 크기):
            """표준과 다른 연속 run만 모아 강조서식 등 기존 속성을 보존한다."""
            runs = 모양[2] if len(모양) > 2 else ()
            문단기본 = (모양[0], 모양[1])
            변경, 현재 = [], None
            for run in runs:
                run_start, run_end, run_shape = run[:3]
                is_aside = bool(run[4]) if len(run) > 4 else False
                # 표준 서식이 기준을 정하는 작업에서는 괄호 축소 규칙이 줄인 글자(본문 -2pt)를
                # 서식통일의 '중간 괄호' 판정과 관계없이 정상으로 본다.
                if (not 서식통일_빨간표시_사용 and 괄호_축소_사용 and 크기 is not None
                        and run_shape[1] == 크기 - int(round(float(괄호_축소_pt) * 100))):
                    is_aside = True
                # 대표 글꼴·크기와 다른 run만 교정한다. 글꼴·크기와 무관한 강조 속성은
                # 문자모양 적용 단계에서 기존 값을 보존한다.
                mismatch = ((글꼴 is not None and run_shape[0] != 글꼴)
                            or (크기 is not None and not is_aside and run_shape[1] != 크기))
                if mismatch:
                    if 현재 and 현재[1] == run_start:
                        현재[1] = run_end
                    else:
                        if 현재:
                            변경.append(tuple(현재))
                        현재 = [run_start, run_end]
                elif 현재:
                    변경.append(tuple(현재))
                    현재 = None
            if 현재:
                변경.append(tuple(현재))
            return 변경
        return bind_function(_서식통일_불일치_구간, _docfit_namespace)
    if _docfit_symbol == '_서식통일_부연괄호_불일치_구간':
        def _서식통일_부연괄호_불일치_구간(모양, 표준크기):
            """본문 크기보다 2pt 작은 규칙을 벗어난 중간 괄호만 교정한다."""
            if 표준크기 is None or len(모양) < 4 or not isinstance(모양[3], dict):
                return [], None
            차이 = (서식통일_괄호크기차이 if 서식통일_괄호크기차이 is not None
                    else int(round(float(괄호_축소_pt) * 100)))
            목표크기 = int(표준크기) - 차이
            if 목표크기 <= 0:
                return [], None
            runs = 모양[3].get("parenthetical_size_runs", ())
            변경 = [(run_start, run_end) for run_start, run_end, size, _ in runs
                    if size != 목표크기]
            return list(서식통일_범위병합(변경)), 목표크기
        return bind_function(_서식통일_부연괄호_불일치_구간, _docfit_namespace)
    if _docfit_symbol == '_서식통일_굵기_불일치_구간':
        def _서식통일_굵기_불일치_구간(모양, 요소, 표준):
            """항목기호/괄호라벨 안에서 굵기만 다른 연속 run을 반환한다."""
            if 표준 is None or len(모양) < 4 or not isinstance(모양[3], dict):
                return []
            runs = 모양[3].get(f"{요소}_bold_runs", ())
            변경, 현재 = [], None
            for run_start, run_end, bold, _ in runs:
                if bold != 표준:
                    if 현재 and 현재[1] == run_start:
                        현재[1] = run_end
                    else:
                        if 현재:
                            변경.append(tuple(현재))
                        현재 = [run_start, run_end]
                elif 현재:
                    변경.append(tuple(현재))
                    현재 = None
            if 현재:
                변경.append(tuple(현재))
            return 변경
        return bind_function(_서식통일_굵기_불일치_구간, _docfit_namespace)
    if _docfit_symbol == '서식통일_대표':
        def 서식통일_대표(모양들):
            """신뢰도 기준을 통과한 문단 빈도 대표값을 속성별로 독립 산출한다."""
            결과 = {}
            for 항목, 추출 in (
                ("font", lambda 모양: 모양[0]),
                ("size", lambda 모양: 모양[1]),
                ("marker_bold", lambda 모양: 모양[3].get("marker_bold")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
                ("label_bold", lambda 모양: 모양[3].get("label_bold")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
                # 내어쓰기 대표값은 여러 줄 문장으로만 정한다(한 줄 항목의 내어쓰기는 보이지 않는다).
                ("hanging_indent", lambda 모양: 모양[3].get("hanging_indent")
                 if len(모양) > 3 and isinstance(모양[3], dict) and 모양[3].get("line_count", 2) > 1
                 else None),
                ("ratio", lambda 모양: 모양[3].get("ratio")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
                ("color", lambda 모양: 모양[3].get("color")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
                ("shade", lambda 모양: 모양[3].get("shade")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
                # 서식 요소 분석 고도화(2026-10-03): 기울임·밑줄·취소선·정렬·좌우 여백·기호 앞 빈칸.
                ("italic", lambda 모양: 모양[3].get("italic")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
                ("underline", lambda 모양: 모양[3].get("underline")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
                ("strike", lambda 모양: 모양[3].get("strike")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
                ("align", lambda 모양: 모양[3].get("align")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
                ("left", lambda 모양: 모양[3].get("left_margin")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
                ("right", lambda 모양: 모양[3].get("right_margin")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
                ("lead", lambda 모양: 모양[3].get("lead_spaces")
                 if len(모양) > 3 and isinstance(모양[3], dict) else None),
            ):
                값들 = [추출(모양) for 모양 in 모양들 if 모양]
                # 표본이 두 개뿐인 희소 기호(예: ※)도 두 표본이 완전히 일치하면
                # 빈도 100%의 대표값으로 인정한다. 둘이 다르면 동률이라 자동 보정하지 않는다.
                최소표본 = max(2, min(서식통일_최소문단수, len(모양들)))
                대표값, 빈도, _ = 서식통일_최빈값(
                    값들, minimum=최소표본, ratio=서식통일_최소비율)
                결과[항목] = (대표값, 빈도 if 대표값 is not None else 0)
            return 결과
        return bind_function(서식통일_대표, _docfit_namespace)
    if _docfit_symbol == '_서식통일_표지인가':
        def _서식통일_표지인가(첫쪽_문단번호, 본문크기):
            """1쪽이 표지인지 HWPX로 판정한다(표 안 제목 글자까지 포함, 읽기 전용).

            본문 대표 크기보다 확연히 큰 가운데 정렬 글자가 있고 본문형 문장(ㅇ·- 등)이
            거의 없으면 표지로 보고 서식통일에서 뺀다.
            """
            문서경로 = _서식통일_현재_HWPX()
            if 문서경로 is None or not 첫쪽_문단번호 or not 본문크기:
                return False
            try:
                from docfit_core.style_inventory import _tag, _run_text
                분석 = _서식통일_HWPX_분석(문서경로)
                항목들 = []
                for 번호 in 첫쪽_문단번호:
                    문단 = 분석["paragraphs"][번호]
                    for p in (item for item in 문단.iter() if _tag(item) == "p"):
                        글자 = "".join(_run_text(run) for run in p if _tag(run) == "run")
                        if not 글자.strip():
                            continue
                        크기들 = [round(분석["chars"][run.get("charPrIDRef")]["size_pt"] * 100)
                                  for run in p if _tag(run) == "run" and _run_text(run).strip()
                                  and run.get("charPrIDRef") in 분석["chars"]]
                        크기 = max(크기들, default=0)
                        가운데 = 분석["paras"].get(p.get("paraPrIDRef"), {}).get("align") == "CENTER"
                        본문형 = (서식통일_항목기호(글자)[1] in ("본문", "내용", "부연설명")
                                  and 크기 <= 본문크기 * 1.15)
                        항목들.append((글자, 크기, 가운데, 본문형))
                return 서식통일_표지판정(항목들, 본문크기)
            except Exception as exc:
                진단로그(f"[서식통일] 표지 판정 실패 — 1쪽도 일반 쪽으로 처리: {exc}")
                return False
        return bind_function(_서식통일_표지인가, _docfit_namespace)
    if _docfit_symbol == '_서식통일_제목표_표본':
        def _서식통일_제목표_표본(제외문단=()):
            """1칸 표(제목 상자) 안 항목기호 문장의 (본문 문단 번호, 그룹키, 표본 모양) 목록.

            장·절 제목은 흔히 1칸 표 안에 있고, 같은 계층 제목이 본문에 표 없이 한두 번
            나오기도 한다. 본문 표본이 부족한 계층의 대표값을 정할 때만 읽기 전용으로 참고한다.
            """
            문서경로 = _서식통일_현재_HWPX()
            if 문서경로 is None:
                return []
            try:
                from docfit_core.style_inventory import _tag, _run_text
                분석 = _서식통일_HWPX_분석(문서경로)
            except Exception:
                return []
            결과 = []
            for 번호, 문단 in enumerate(분석["paragraphs"]):
                if 번호 in 제외문단:
                    continue
                for 표 in (item for item in 문단.iter() if _tag(item) == "tbl"):
                    if 표.get("rowCnt") != "1" or 표.get("colCnt") != "1":
                        continue
                    for p in (item for item in 표.iter() if _tag(item) == "p"):
                        글자 = "".join(_run_text(run) for run in p if _tag(run) == "run")
                        if not 서식통일_항목기호(글자)[0]:
                            continue
                        값들 = []
                        for run in (item for item in p if _tag(item) == "run"):
                            char = 분석["chars"].get(run.get("charPrIDRef"))
                            길이 = len(_run_text(run).strip())
                            if char and 길이:
                                값들.append((char["font"].get("hangul"), round(char["size_pt"] * 100),
                                            str(char.get("color", "")).upper(),
                                            _서식통일_음영값(char.get("shade")), 길이))
                        if not 값들:
                            continue
                        모양 = (서식통일_우세값((v[0], v[4]) for v in 값들),
                                서식통일_우세값((v[1], v[4]) for v in 값들), (), {
                                    "color": 서식통일_우세값((v[2], v[4]) for v in 값들),
                                    "shade": 서식통일_우세값((v[3], v[4]) for v in 값들),
                                    "table_heading": True})
                        결과.append((번호, _서식통일_그룹키("", 글자, None), 모양))
            return 결과
        return bind_function(_서식통일_제목표_표본, _docfit_namespace)
    if _docfit_symbol == '_서식통일_체계경계':
        def _서식통일_체계경계(표본, 위치텍스트):
            """서식 체계가 바뀌는 (본문 문단 번호, 영역 이름) 목록.

            붙임·별첨 제목(본문 문단이나 제목 표 안)은 구조 경계로, 여러 계층이 같은 곳에서 함께
            서식을 바꾸는 큰 전환점은 서식 경계로 본다. 작은 구간의 다른 서식은 경계가 아니다.
            """
            경계 = {}
            문서경로 = _서식통일_현재_HWPX()
            if 문서경로 is not None:
                try:
                    from docfit_core.style_inventory import _tag
                    분석 = _서식통일_HWPX_분석(문서경로)
                    for 번호, 문단 in enumerate(분석["paragraphs"]):
                        for p in (item for item in 문단.iter() if _tag(item) == "p"):
                            글자 = "".join(_서식통일_run_text(run)[0] for run in p if _tag(run) == "run")
                            if 글자.strip():
                                이름 = 서식통일_붙임제목(글자)
                                if 이름 and 번호 > 0:
                                    경계[번호] = 이름
                                break
                except Exception as exc:
                    진단로그(f"[서식통일] 붙임 구역 판별 실패 — 문서 전체를 한 체계로 봄: {exc}")
            순서열 = defaultdict(list)
            for marker, 항목들 in 표본.items():
                for 모양, 시작, _, text in 항목들:
                    키 = _서식통일_그룹키(marker, 위치텍스트.get(tuple(시작), text), 시작)[:2]
                    값 = (모양[0], 모양[1]) if 모양[0] is not None and 모양[1] is not None else None
                    순서열[키].append((시작[1], 값))
            for 위치 in 서식통일_체계전환점(순서열):
                if not any(abs(위치 - 기존) <= 5 for 기존 in 경계):
                    경계[위치] = f"서식 전환 {len(경계) + 1}"
            return sorted(경계.items())
        return bind_function(_서식통일_체계경계, _docfit_namespace)
    if _docfit_symbol == '_서식통일_참고표_이웃대표_보완':
        def _서식통일_참고표_이웃대표_보완(그룹별_표본, 프로필):
            """※ 대표값이 미확정이면 앞뒤 문장이 모두 표준인 ※의 값을 대표값으로 본다."""
            필드추출 = {
                "font": lambda 모양: 모양[0],
                "size": lambda 모양: 모양[1],
                "marker_bold": lambda 모양: 모양[3].get("marker_bold"),
                "label_bold": lambda 모양: 모양[3].get("label_bold"),
                "hanging_indent": lambda 모양: 모양[3].get("hanging_indent"),
            }

            def 추출(모양, 필드):
                if 필드 not in ("font", "size") and (len(모양) < 4 or not isinstance(모양[3], dict)):
                    return None
                return 필드추출[필드](모양)

            def 표준문장인가(그룹키, 모양):
                대표 = 프로필.get(그룹키) or {}
                for 필드 in 필드추출:
                    표준 = 대표.get(필드, (None, 0))[0]
                    if 필드 in ("font", "size") and 표준 is None:
                        return False
                    if 표준 is not None and 추출(모양, 필드) not in (None, 표준):
                        return False
                return True

            순서 = sorted(((항목[1], 그룹키, 항목[0])
                          for 그룹키, 항목들 in 그룹별_표본.items() for 항목 in 항목들),
                         key=lambda item: item[0])
            후보 = {}
            for i, (_, 그룹키, 모양) in enumerate(순서):
                대표 = 프로필.get(그룹키)
                if 그룹키[0] != "※" or not 대표:
                    continue
                if not 0 < i < len(순서) - 1:
                    continue
                미확정 = [필드 for 필드 in 필드추출 if 대표.get(필드, (None, 0))[0] is None]
                if not 미확정:
                    continue
                앞, 뒤 = 순서[i - 1], 순서[i + 1]
                if not (표준문장인가(앞[1], 앞[2]) and 표준문장인가(뒤[1], 뒤[2])):
                    continue
                for 필드 in 미확정:
                    값 = 추출(모양, 필드)
                    if 값 is not None:
                        후보.setdefault((그룹키, 필드), []).append(값)
            보완수 = 0
            for (그룹키, 필드), 값들 in 후보.items():
                값 = max(값들, key=값들.count)
                # 이웃 기준 ※ 가운데 과반이 같은 값일 때만 채택한다(실측: 5개 중 2개뿐인 글꼴을
                # 대표로 삼아 다수 글꼴 ※ 6개를 바꾸려 함).
                if 값들.count(값) * 2 <= len(값들):
                    continue
                프로필[그룹키][필드] = (값, 값들.count(값))
                보완수 += 1
                로그(f"[서식통일] ※ 대표값 보완: {그룹키[0]}/{그룹키[1]} {필드}={값} "
                     f"(앞뒤 문장이 표준인 ※ {len(값들)}개 기준)")
            return 보완수
        return bind_function(_서식통일_참고표_이웃대표_보완, _docfit_namespace)
    if _docfit_symbol == '_서식통일_대표값_사용자검토':
        def _서식통일_대표값_사용자검토(그룹별_표본):
            """조사된 대표 서식을 사용자 확인 없이 자동 승인한다."""
            로그(f"[서식통일] 대표 서식 {len(그룹별_표본)}개 그룹 자동 승인(사용자 확인 생략)")
            return True
        return bind_function(_서식통일_대표값_사용자검토, _docfit_namespace)
    if _docfit_symbol == '_서식통일_적용영역_사용자검토':
        def _서식통일_적용영역_사용자검토(계획):
            """불일치 영역을 적용 전에 사용자에게 보여 주고 선택된 계획만 돌려준다."""
            후보 = [index for index, item in enumerate(계획) if item.get("mismatch")]
            if _서식통일_대표값_검토콜백 is None:
                로그("[서식통일] 사용자 검토 UI가 없어 시험 모드에서 불일치 영역 전체 승인")
                return {"approved": True, "selected": 후보}
            요청 = _서식통일_대표값_검토콜백("regions", 계획)
            return 요청 or {"approved": False, "selected": []}
        return bind_function(_서식통일_적용영역_사용자검토, _docfit_namespace)
    if _docfit_symbol == '서식통일_결과창_반영':
        def 서식통일_결과창_반영(value):
            """설정값을 '작업 결과 확인' 창 사용 여부 전역값에 반영하고 반영한 값을 돌려준다."""
            global 서식통일_결과창_사용
            서식통일_결과창_사용 = bool(value)
            return 서식통일_결과창_사용
        return bind_function(서식통일_결과창_반영, _docfit_namespace)
    if _docfit_symbol == '_결과창_띄우는가':
        def _결과창_띄우는가(total):
            """저장 결과 검수 뒤 '작업 결과 확인' 창을 띄우는지: 문서 하나를 처리할 때, 설정에서 켰을 때만."""
            return total == 1 and 서식통일_결과창_사용
        return bind_function(_결과창_띄우는가, _docfit_namespace)
    if _docfit_symbol == '_서식통일_최종결과_사용자확인':
        def _서식통일_최종결과_사용자확인(결과):
            """저장 후 읽기 전용 검수 결과를 GUI에 보여 준다.

            결과는 읽기 전용이라 확인을 기다릴 이유가 없다. 예전에는 작업 스레드가 '결과 확인'을 누를
            때까지 멈춰, 여러 문서를 맡기고 자리를 비우면 첫 문서 뒤에서 일괄 작업이 서 있었다.
            """
            if _서식통일_대표값_검토콜백 is None:
                return
            gui_queue.put(("style_unify_result_review",
                           {"payload": 결과, "done": threading.Event(), "approved": False}))
        return bind_function(_서식통일_최종결과_사용자확인, _docfit_namespace)
    if _docfit_symbol == '_서식통일_미확정_항목':
        def _서식통일_미확정_항목(대표, text):
            """실제로 존재하는 요소의 대표값만 요구한다(라벨 없는 문장 등 제외).

            내어쓰기는 문장 서식이 아니라 줄 배치 값이다. 한 줄 항목은 내어쓰기가 보이지 않아
            문서마다 제각각이므로(실측: '-' 한 줄 항목 57:39), 대표값이 없다고 빨간 표시하지 않고
            내어쓰기만 건드리지 않는다.
            """
            marker, label = _서식통일_문두요소_범위(text)
            fields = ["font", "size"]
            if not _서식통일_글꼴크기만():
                if marker:
                    fields.append("marker_bold")
                if label:
                    fields.append("label_bold")
            return [field for field in fields if 대표.get(field, (None, 0))[0] is None]
        return bind_function(_서식통일_미확정_항목, _docfit_namespace)
    if _docfit_symbol == '_서식통일_미확정_빨간표시':
        def _서식통일_미확정_빨간표시(시작, 끝):
            """대표값 미확정 문단은 글자색만 변경한다. 혼합 자간은 읽거나 쓰지 않는다."""
            try:
                단어모드_범위선택(시작, 끝)
                action = hwp.CreateAction("CharShape")
                params = action.CreateSet()
                params.SetItem("TextColor", hwp.RGBColor(255, 0, 0))
                if action.Execute(params) is False:
                    raise RuntimeError("대표값 미확정 문단의 빨간색 표시 실패")
            finally:
                hwp_run("Cancel")
        return bind_function(_서식통일_미확정_빨간표시, _docfit_namespace)
    if _docfit_symbol == '_서식통일_문단앞간격_적용':
        def _서식통일_문단앞간격_적용(pos, hwpunit):
            """현재 문단의 문단 위(앞) 간격만 대표값으로 바꾼다."""
            원래위치 = hwp.GetPos()
            try:
                if hwp.SetPos(*pos) is False:
                    raise RuntimeError("대상 문단 이동 실패")
                action = hwp.HAction
                params = hwp.HParameterSet.HParaShape
                action.GetDefault("ParagraphShape", params.HSet)
                # 실측상 HWPX의 prevSpacing 값은 COM HParaShape.PrevSpacing보다
                # 절반으로 직렬화된다(예: COM 1100 → HWPX 550). 표본과 동일한
                # HWPX 대표값을 저장하려면 COM에는 2배 값을 지정해야 한다.
                요청COM값 = int(hwpunit) * 2
                params.PrevSpacing = 요청COM값
                if action.Execute("ParagraphShape", params.HSet) is False:
                    raise RuntimeError("문단 앞 간격 적용 결과가 False입니다")
                actual = int(hwp.ParaShape.Item("PrevSpacing"))
                if abs(actual - 요청COM값) > 1:
                    raise RuntimeError(f"문단 앞 간격 적용 후 확인 실패: 요청 {요청COM값}, 실제 {actual} COMUNIT")
                return True
            except Exception as exc:
                로그(f"[서식통일] 문단 앞 간격 적용 실패(건너뜀): {exc}")
                return False
            finally:
                try:
                    hwp.SetPos(*원래위치)
                except Exception:
                    pass
        return bind_function(_서식통일_문단앞간격_적용, _docfit_namespace)
    if _docfit_symbol == '_서식통일_내어쓰기_필요':
        def _서식통일_내어쓰기_필요(pos, text):
            """읽기 전용으로 문단에 내어쓰기가 빠져 있는지 판정한다.

            문두 라벨마다 글자 폭이 달라 음수 내어쓰기의 절대값은 문장별로 다르다.
            따라서 임의 폭 추정값과 비교해 이미 적용된 내어쓰기를 다시 쓰지 않고,
            문단 모양의 Indentation이 사실상 0인 경우에만 누락으로 판정한다.
            """
            offset = 문단_내어쓰기_기준_오프셋(text)
            if hwp is None or offset is None or offset <= 0:
                return False
            original_pos = None
            try:
                original_pos = hwp.GetPos()
                if hwp.SetPos(*pos) is False:
                    return None
                hwp_run("MoveParaBegin")
                current = int(hwp.ParaShape.Item("Indentation"))
                # 20 HWPUNIT = 0.2pt. 작은 반올림 잔차도 이미 적용된 상태로 취급한다.
                return current >= -20
            except Exception as exc:
                진단로그(f"[서식통일] 내어쓰기 판정 실패 — 안전을 위해 건너뜀: {exc}")
                return None
            finally:
                try:
                    hwp_run("Cancel")
                    if original_pos is not None:
                        hwp.SetPos(*original_pos)
                except Exception:
                    pass
        return bind_function(_서식통일_내어쓰기_필요, _docfit_namespace)
    if _docfit_symbol == '_서식통일_내어쓰기_상태':
        def _서식통일_내어쓰기_상태(pos, text):
            """문단의 내어쓰기 적용 여부를 읽기 전용으로 반환한다 (불명은 None)."""
            offset = 문단_내어쓰기_기준_오프셋(text)
            if hwp is None or offset is None or offset <= 0:
                return None
            original_pos = None
            try:
                original_pos = hwp.GetPos()
                if hwp.SetPos(*pos) is False:
                    return None
                hwp_run("MoveParaBegin")
                return int(hwp.ParaShape.Item("Indentation")) < -20
            except Exception as exc:
                진단로그(f"[서식통일] 내어쓰기 상태 조사 실패 — 안전을 위해 건너뜀: {exc}")
                return None
            finally:
                try:
                    hwp_run("Cancel")
                    if original_pos is not None:
                        hwp.SetPos(*original_pos)
                except Exception:
                    pass
        return bind_function(_서식통일_내어쓰기_상태, _docfit_namespace)
    if _docfit_symbol == '_서식통일_문단서식_적용':
        def _서식통일_문단서식_적용(item):
            """한 문단 안에서 대표값과 다른 문자 속성만 적용한다."""
            operations = (
                (item["font_runs"], {"폰트": item["font"]}),
                (item["size_runs"], {"크기_pt": item["size"] / 100 if item["size"] else None}),
                (item["aside_runs"], {"크기_pt": item["aside_size"] / 100 if item["aside_size"] else None}),
                (item["marker_bold_runs"], {"굵게": item["marker_bold"]}),
                (item["label_bold_runs"], {"굵게": item["label_bold"]}),
            )
            for ranges, options in operations:
                for start, end in ranges:
                    try:
                        단어모드_범위선택(start, end)
                        문자모양_적용_현재선택(**options, 자간_유지=True)
                    finally:
                        hwp_run("Cancel")
            if item.get("ratio_fix") is not None:
                try:
                    단어모드_범위선택(item["start"], item["end"])
                    문자모양_적용_현재선택(장평=item["ratio_fix"], 자간_유지=True)
                finally:
                    hwp_run("Cancel")
            for ranges, 필드, 값 in ((item.get("color_runs", ()), "TextColor", item.get("color")),
                                    (item.get("shade_runs", ()), "ShadeColor", item.get("shade"))):
                for start, end in ranges:
                    try:
                        단어모드_범위선택(start, end)
                        _서식통일_색_적용(필드, 값)
                    finally:
                        hwp_run("Cancel")
            for 필드, ranges in (item.get("char_runs") or {}).items():
                if ranges:
                    _서식통일_글자요소_적용(필드, (item.get("char_values") or {}).get(필드),
                                           (item.get("char_examples") or {}).get(필드), ranges)
            예시 = item.get("para_examples") or {}
            if 예시:
                # 문서 안에서 대표값을 가진 실제 문단의 값을 읽어 그대로 복사한다(단위 변환 없음).
                값들 = {}
                for 종류, 위치 in 예시.items():
                    if 위치 is None:
                        continue
                    hwp.SetPos(*위치)
                    모양 = hwp.HParameterSet.HParaShape
                    hwp.HAction.GetDefault("ParagraphShape", 모양.HSet)
                    if 종류 == "indent":
                        값들["Indentation"] = int(모양.Indentation)
                        값들["LeftMargin"] = int(모양.LeftMargin)
                    elif 종류 == "align":
                        값들["AlignType"] = int(모양.AlignType)
                    elif 종류 == "left":
                        값들["LeftMargin"] = int(모양.LeftMargin)
                    elif 종류 == "right":
                        값들["RightMargin"] = int(모양.RightMargin)
                    else:
                        값들["PrevSpacing"] = int(모양.PrevSpacing)
                if 값들:
                    hwp.SetPos(*item["start"])
                    action = hwp.CreateAction("ParagraphShape")
                    params = action.CreateSet()
                    for key, value in 값들.items():
                        params.SetItem(key, value)
                    if action.Execute(params) is False:
                        raise RuntimeError("대표 문단모양 복사 실패")
        return bind_function(_서식통일_문단서식_적용, _docfit_namespace)
    if _docfit_symbol == '_서식통일_글자요소_적용':
        def _서식통일_글자요소_적용(필드, 표준, 예시구간, 구간들):
            """기울임·밑줄·취소선을 대표값으로 맞춘다.

            없애는 경우(기울임 끄기, 밑줄·취소선 없음)는 종류 항목만 0으로 둔다. 넣는 경우에는 대표값을 쓴
            다른 문장 구간(예시구간)의 선 종류·모양·색을 읽어 그대로 복사한다(값 대응을 추정하지 않는다).
            """
            항목들 = _서식통일_글자요소_항목[필드]
            if 필드 == "italic":
                값들 = {"Italic": 1 if 표준 else 0}
            elif 표준 in ("NONE", False):
                값들 = {항목들[0]: 0}
            else:
                if not 예시구간:
                    return
                try:
                    단어모드_범위선택(*예시구간)
                    모양 = hwp.HParameterSet.HCharShape
                    hwp.HAction.GetDefault("CharShape", 모양.HSet)
                    값들 = {항목: int(getattr(모양, 항목)) for 항목 in 항목들}
                finally:
                    hwp_run("Cancel")
            for start, end in 구간들:
                try:
                    단어모드_범위선택(start, end)
                    action = hwp.CreateAction("CharShape")
                    params = action.CreateSet()
                    for 항목, 값 in 값들.items():
                        params.SetItem(항목, 값)
                    if action.Execute(params) is False:
                        raise RuntimeError(f"서식통일 {필드} 적용 실패")
                finally:
                    hwp_run("Cancel")
        return bind_function(_서식통일_글자요소_적용, _docfit_namespace)
    if _docfit_symbol == '_서식통일_색값':
        def _서식통일_색값(value):
            """'#RRGGBB'는 한/글 색 값으로, '없음'(음영 없음)은 0xFFFFFFFF로 바꾼다."""
            text = str(value or "").strip().lstrip("#")
            if len(text) != 6:
                return 0xFFFFFFFF
            return hwp.RGBColor(int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
        return bind_function(_서식통일_색값, _docfit_namespace)
    if _docfit_symbol == '_서식통일_색_적용':
        def _서식통일_색_적용(필드, 값):
            """선택 영역의 글자색(TextColor) 또는 음영색(ShadeColor)만 바꾼다."""
            action = hwp.CreateAction("CharShape")
            params = action.CreateSet()
            params.SetItem(필드, _서식통일_색값(값))
            if action.Execute(params) is False:
                raise RuntimeError(f"서식통일 {필드} 적용 실패")
        return bind_function(_서식통일_색_적용, _docfit_namespace)
    if _docfit_symbol == '_서식통일_문단내어쓰기_적용':
        def _서식통일_문단내어쓰기_적용(item):
            """해당 문단의 자간 처리가 끝난 실제 글자 폭으로 내어쓰기를 확정한다."""
            expected = item["expected_hanging"]
            원문 = item.get("position_text") or item["text"]
            if expected is None or 문단_내어쓰기_기준_오프셋(원문) is None:
                return
            if expected:
                if not 문단_내어쓰기_적용(item["start"], 원문):
                    검수_문제_기록(현재_처리파일, "[서식통일 내어쓰기 미적용] " + item["text"].strip())
            elif item["hanging_mismatch"]:
                if hwp.SetPos(*item["start"]) is False:
                    raise RuntimeError("대상 문단 이동 실패")
                hwp_run("MoveParaBegin")
                _내어쓰기_값_설정(0)
        return bind_function(_서식통일_문단내어쓰기_적용, _docfit_namespace)
    if _docfit_symbol == '_서식통일_문단자간_조정':
        def _서식통일_문단자간_조정(start, end):
            """예외 문단만 검사. 분리 어절을 ±10% 이내에서 조정하고 실패 시 복원."""
            if start[:2] != end[:2] or start[2] >= end[2]:
                raise ValueError("자간 처리 범위는 같은 문단이어야 합니다")
            anchor = start
            seen = set()
            limit = max(0, min(10, int(자간_최대시도_본문)))
            while anchor[:2] == start[:2] and anchor[2] < end[2]:
                if 중단_요청됨():
                    return False
                if anchor in seen:
                    break
                seen.add(anchor)
                hwp.SetPos(*anchor)
                info = 단어모드_분리정보(anchor)
                if info:
                    line_start, boundary, word_start, word_end, left, right = info
                    positions = (line_start, boundary, word_start, word_end)
                    if any(pos[:2] != start[:2] or not start[2] <= pos[2] <= end[2] for pos in positions):
                        raise RuntimeError("자간 조정 범위가 대상 문단을 벗어났습니다")
                    shrink = 어절분리_앞줄당김인가(left, right, 단어모드_마지막줄_짧은잔여인가(boundary))
                    success = False
                    for direction in ((-1, 1) if shrink else (1, -1)):
                        target_end = word_end if direction < 0 else word_start
                        if target_end[2] <= line_start[2] or word_start[2] < line_start[2]:
                            continue
                        runs = 단어모드_자간보관(line_start, target_end)
                        if runs is None:
                            return False
                        if not runs:
                            continue
                        values = [value for _, _, items in runs for value in items]
                        # 이미 압축된 자간을 반복 실행 때 더 누적 축소하지 않는다.
                        budget = min(limit, 10 + min(values) if direction < 0 else 10 - max(values))
                        changed = False
                        try:
                            for step in range(1, max(0, budget) + 1):
                                if 중단_요청됨():
                                    return False
                                changed = True
                                단어모드_자간적용(runs, direction * step)
                                _, previous_end = 단어모드_줄범위(anchor)
                                if direction < 0:
                                    success = previous_end[:2] == end[:2] and previous_end[2] >= word_end[2]
                                else:
                                    next_start, next_end = 단어모드_줄범위(word_start)
                                    success = (previous_end[2] <= word_start[2] and
                                               next_start[:2] == end[:2] == next_end[:2] and
                                               next_start[2] <= word_start[2] and next_end[2] >= word_end[2])
                                if success:
                                    진단로그(f"[서식통일 자간] 문단 {start[:2]}, {direction * step:+d}%p")
                                    break
                        finally:
                            if changed and not success:
                                단어모드_자간적용(runs, 0)
                        if success:
                            break
                    if not success:
                        검수_문제_기록(현재_처리파일, f"[서식통일 자간 미해결] 문단 {start[:2]}, 경계 {boundary[2]}: 안전 한도 내 조정 불가")
                hwp.SetPos(*anchor)
                hwp_run("MoveLineEnd")
                line_end = hwp.GetPos()
                if line_end[:2] != end[:2] or line_end[2] >= end[2]:
                    break
                hwp_run("MoveNextChar")
                next_pos = hwp.GetPos()
                if next_pos[:2] != end[:2] or next_pos[2] <= anchor[2]:
                    break
                anchor = next_pos
            hwp_run("Cancel")
            return True
        return bind_function(_서식통일_문단자간_조정, _docfit_namespace)
    if _docfit_symbol == '_서식통일_글꼴크기만':
        def _서식통일_글꼴크기만():
            """서식 통일 카드에서 '전체 서식 맞추기'를 켜지 않았으면 글꼴·크기만 맞춘다(2026-10-11 사용자 결정).

            글꼴·크기에는 항목기호·라벨 굵게와 괄호 크기 규칙을 포함한다. 한 번에 적용·서식 적용의 서식통일은 그대로다.
            """
            return 작업_모드 == "unify" and not stage_enabled(선택_세부작업, "unify_full_format", 작업_모드)
        return bind_function(_서식통일_글꼴크기만, _docfit_namespace)
    if _docfit_symbol == '_서식통일_글꼴크기_대표':
        def _서식통일_글꼴크기_대표(대표):
            """대표값에서 글꼴·크기(+항목기호·라벨 굵게)만 남긴 사본. 나머지 항목은 비교하지 않는다."""
            if not 대표:
                return 대표
            return {키: 값 for 키, 값 in 대표.items() if 키 in _서식통일_글꼴크기_필드}
        return bind_function(_서식통일_글꼴크기_대표, _docfit_namespace)
    if _docfit_symbol == '_서식통일_XML_조사':
        def _서식통일_XML_조사():
            """HWPX 스냅숏에서 표본을 모은다. 한/글은 문단 번호 대응 확인과 1쪽 끝 찾기에만 쓴다.

            돌려주는 값은 _서식통일_COM_조사와 같다. 쓸 수 없으면 None(예전 순회로 대신한다).
            """
            if not 알파_서식통일_XML조사_사용:
                return None
            문서경로 = _서식통일_현재_HWPX()
            if 문서경로 is None:
                return None
            try:
                from docfit_core.style_inventory import _tag
                문단들 = _서식통일_HWPX_분석(문서경로)["paragraphs"]
                글들 = ["".join(_서식통일_run_text(run)[0] for run in para if _tag(run) == "run") for para in 문단들]
                if not 문단들:
                    return None
                # 한/글 본문 문단 번호와 HWPX 직속 문단 번호가 맞는지 확인한다(끝 번호 + 글이 있는 문단 3곳).
                hwp_run("MoveDocEnd")
                끝 = tuple(hwp.GetPos())
                if 끝[0] != 0 or 끝[1] != len(문단들) - 1:
                    진단로그(f"[서식통일] 문단 번호가 HWPX와 맞지 않아(한/글 {끝[1] + 1}개, HWPX {len(문단들)}개) 예전 조사 방식으로 진행")
                    return None
                글있음 = [번호 for 번호, 글 in enumerate(글들) if 글.strip()]
                for 번호 in sorted({글있음[0], 글있음[len(글있음) // 2], 글있음[-1]}) if 글있음 else ():
                    hwp.SetPos(0, 번호, 0)
                    hwp_run("MoveParaBegin")
                    if _서식통일_공백제거(현재문단_텍스트()) != _서식통일_공백제거(글들[번호]):
                        진단로그(f"[서식통일] {번호 + 1}번째 문단 글이 HWPX와 달라 예전 조사 방식으로 진행")
                        return None
                # 1쪽에 속한 문단(표지 판정용). 쪽 번호는 문단 순서대로 늘므로 이분 탐색으로 1쪽의 끝을 찾는다.
                def 쪽(번호):
                    hwp.SetPos(0, 번호, 0)
                    hwp_run("MoveParaBegin")
                    return 현재_페이지번호()
                첫쪽끝, 첫쪽끝위치 = False, len(문단들)
                if 쪽(len(문단들) - 1) > 1:
                    첫쪽끝 = True
                    낮, 높 = 0, len(문단들) - 1
                    while 낮 < 높:
                        가운데 = (낮 + 높) // 2
                        if 쪽(가운데) > 1:
                            높 = 가운데
                        else:
                            낮 = 가운데 + 1
                    첫쪽끝위치 = 낮
                표본, 문맥, 위치텍스트 = {}, {}, {}
                직전기호 = None
                for 번호, 글 in enumerate(글들):
                    if 중단_요청됨():
                        return False
                    pos = (0, 번호, 0)
                    marker = 서식통일_항목기호(글)[0] if 글.strip() else ""
                    if marker:
                        결과 = 서식통일_표본(pos, 글)
                        if 결과:
                            표본.setdefault(marker, []).append(결과 + (글,))
                            문맥[pos] = 직전기호
                            위치텍스트[pos] = 글
                        직전기호 = marker
                    elif 글.strip():
                        직전기호 = None
                hwp_run("MoveDocBegin")
                return 표본, 문맥, 위치텍스트, list(range(첫쪽끝위치)), 첫쪽끝
            except Exception as 오류:
                진단로그(f"[서식통일] HWPX 조사 실패, 예전 조사 방식으로 진행: {오류}")
                return None
        return bind_function(_서식통일_XML_조사, _docfit_namespace)
    if _docfit_symbol == '_서식통일_COM_조사':
        def _서식통일_COM_조사():
            """본문 문단을 한/글로 하나씩 돌며 표본을 모은다(예전 방식). 중단하면 False."""
            표본 = {}
            # 쪽 범위는 수정 대상을 제한하지만, 대표서식은 같은 문서의 정상 문장까지
            # 포함해 산출해야 한다. 선택 쪽에서만 표본을 모으면 그 쪽의 이상 서식이
            # 대표값으로 채택되어 검출이 0건이 되는 문제가 생긴다.
            문맥 = {}        # 문단 시작 위치 → 바로 앞 문장의 항목기호(문단 위 간격 기준)
            위치텍스트 = {}  # 문단 시작 위치 → 글자 위치와 맞는 원문(고정폭 빈칸 포함)
            첫쪽문단 = []    # 표지 판정용 1쪽 본문 문단 번호
            첫쪽끝 = False
            직전기호 = None
            hwp_run("MoveDocBegin")
            while True:
                if 중단_요청됨():
                    return False
                hwp_run("MoveParaBegin")
                pos = hwp.GetPos()
                if pos[0] == 0:
                    if not 첫쪽끝:
                        if 현재_페이지번호() == 1:
                            첫쪽문단.append(pos[1])
                        else:
                            첫쪽끝 = True
                    text = 현재문단_텍스트()
                    본문 = _서식통일_위치텍스트(pos, text) if text.strip() else text
                    # 번호 계열('1.' '2.' …)은 한 그룹으로 묶고, 고정폭 빈칸 뒤 항목기호도 인식한다.
                    marker = 서식통일_항목기호(본문)[0] if 본문.strip() else ""
                    if marker:
                        결과 = 서식통일_표본(pos, text)
                        if 결과:
                            표본.setdefault(marker, []).append(결과 + (text,))
                            문맥[tuple(pos)] = 직전기호
                            위치텍스트[tuple(pos)] = 본문
                        직전기호 = marker
                    elif text.strip():
                        직전기호 = None
                    hwp.SetPos(*pos)
                if not 다음_문단으로_진행():
                    break
            return 표본, 문맥, 위치텍스트, 첫쪽문단, 첫쪽끝
        return bind_function(_서식통일_COM_조사, _docfit_namespace)
    if _docfit_symbol == '서식통일_전체_적용':
        def 서식통일_전체_적용(고정_프로필_재적용=False, 검증만=False):
            global _서식통일_문서대표프로필, _서식통일_최종감사, 서식통일_괄호크기차이
            if 중단_요청됨():
                return False
            범위표시 = (f"{쪽범위_실제[0]}~{쪽범위_실제[1]}쪽" if 쪽범위_실제 is not None
                       else "전체 문서")
            기준설명 = ("최초 문서 표본에서 고정한 대표 프로필로 후속 변경을 재검증"
                       if 고정_프로필_재적용 else "항목기호·보고서 계층별 문서 표본에서 대표 서식 산출")
            작업설명 = "저장 결과를 읽기 전용으로 검증" if 검증만 else "표준과 다른 구간만 보정"
            글꼴크기만 = _서식통일_글꼴크기만()
            if 검증만:
                단계표시("서식통일 검수")
            elif not 고정_프로필_재적용:
                단계표시("서식통일 조사")
            로그(f"서식통일 시작: 수정 범위 {범위표시}, {기준설명}, {작업설명}, "
                 "표준 문장은 무변경, 괄호(문두 라벨 제외)는 본문 크기 기준 -2pt, 자간 초기화 없음")
            로그("[서식통일] 비교 범위: " + ("글꼴·크기(항목기호·라벨 굵게, 괄호 크기 포함)만 맞춤" if 글꼴크기만
                                            else "전체 서식(글자색·기울임·밑줄·정렬·여백·위 간격·내어쓰기 포함)"))
            if (not 검증만 and (고정_프로필_재적용 or 작업_모드 != "unify")
                    and _서식통일_현재_HWPX() is not None):
                # 앞선 단계(공백 정리·표준 서식 등)가 문서를 바꿨으면 디스크의 HWPX와 문단 번호·글자
                # 위치가 다르다. 조사 전에 현재 상태를 스냅숏으로 저장해 원문·서식을 정확히 읽는다.
                try:
                    _제목_임시hwpx_저장(Path(tempfile.mkdtemp(prefix="hwp_format_first_")) / "서식통일.hwpx")
                except Exception as exc:
                    로그(f"[서식통일] 현재 상태 스냅숏 저장 실패 — 원문이 다른 문단은 건너뜀: {exc}")
            조사 = _서식통일_XML_조사()
            XML조사 = 조사 is not None and 조사 is not False
            if 조사 is None:
                조사 = _서식통일_COM_조사()
            if 조사 is False:
                return False
            표본, 문맥, 위치텍스트, 첫쪽문단, 첫쪽끝 = 조사
            # 쪽 범위는 수정 대상을 제한하지만, 대표서식은 같은 문서의 정상 문장까지
            # 포함해 산출해야 한다. 선택 쪽에서만 표본을 모으면 그 쪽의 이상 서식이
            # 대표값으로 채택되어 검출이 0건이 되는 문제가 생긴다.
            # 1쪽이 표지(본문보다 확연히 큰 가운데 정렬 제목)이면 표본·수정 대상에서 뺀다.
            본문크기 = 서식통일_우세값(((모양[1], 1) for 항목들 in 표본.values()
                                     for 모양, *_ in 항목들 if 모양[1]), ratio=0)
            표지문단 = set()
            if 첫쪽끝 and 첫쪽문단 and _서식통일_표지인가(첫쪽문단, 본문크기):
                표지문단 = set(첫쪽문단)
                제외수 = 0
                for marker in list(표본):
                    남김 = [항목 for 항목 in 표본[marker] if 항목[1][1] not in 표지문단]
                    제외수 += len(표본[marker]) - len(남김)
                    if 남김:
                        표본[marker] = 남김
                    else:
                        del 표본[marker]
                로그(f"[서식통일] 1쪽을 표지로 판단해 제외: 본문({본문크기 / 100:g}pt)보다 큰 가운데 정렬 제목, "
                     f"항목기호 문장 {제외수}개 제외")
            교정수 = 0
            확인문단수 = 0
            불일치목록 = []
            판정불가그룹 = []
            미확정문단 = []
            그룹별_표본 = {}
            # 한 문서에 서식 체계가 둘 이상일 수 있다(본문과 붙임 등). 붙임·별첨 제목과, 여러 계층이
            # 함께 서식을 바꾸는 큰 전환점에서 영역을 나누고 영역마다 대표 서식을 따로 정한다.
            경계 = _서식통일_체계경계(표본, 위치텍스트)

            def 영역키(번호):
                이름 = "본문" if 경계 else "문서 공통"
                for 위치, 경계이름 in 경계:
                    if 번호 >= 위치:
                        이름 = 경계이름
                return 이름

            for marker, 항목들 in 표본.items():
                for 항목 in 항목들:
                    모양, 시작, 끝, text = 항목
                    그룹키 = (_서식통일_그룹키(marker, 위치텍스트.get(tuple(시작), text), 시작)[:2]
                              + (영역키(시작[1]),))
                    그룹별_표본.setdefault(그룹키, []).append(항목)
            제목표_표본 = [(번호, 키[:2] + (영역키(번호),), 모양)
                           for 번호, 키, 모양 in _서식통일_제목표_표본(표지문단)]
            if 경계:
                로그(f"[서식통일] 서식 체계 {len(경계) + 1}개로 나눠 영역마다 대표 서식을 정함: 본문 / "
                     + " / ".join(f"{이름}(문단 {위치 + 1}부터)" for 위치, 이름 in 경계))
            # 문서 체계: 본문 문장과 제목 표의 항목기호를 문서 순서로 늘어놓아 바깥 → 안쪽 계층을 추정한다.
            순서 = sorted([(시작[1], 그룹키[:2]) for 그룹키, 항목들 in 그룹별_표본.items()
                          for _, 시작, _, _ in 항목들]
                         + [(번호, 그룹키[:2]) for 번호, 그룹키, _ in 제목표_표본])
            체계 = 서식통일_계층순서([그룹키 for _, 그룹키 in 순서])
            로그("[서식통일] 문서 체계(바깥 → 안쪽): "
                 + " > ".join(f"{i}단계 {키[0]}({키[1]})" for i, 키 in enumerate(체계, 1)))
            로그(f"[서식통일] 1/5 표본 조사 완료: {sum(map(len, 그룹별_표본.values()))}개 문장, "
                 f"{len(그룹별_표본)}개 그룹, 제목 표 {len(제목표_표본)}개 — 문서 변경 0건(읽기 전용)")
            if 검수_사용 and not 검증만 and not 고정_프로필_재적용 and _서식통일_현재_HWPX() is not None:
                # 검수 모드에서는 서식 요소 전수 분석(계층별·서식 표 칸별 대표값)을 작업 로그에 함께 남긴다.
                try:
                    요소분석 = 서식요소.analyze_format_elements(_서식통일_현재_HWPX(), 서식표_종류판별)
                    for 줄 in 서식요소.summary_lines(요소분석, limit=20):
                        진단로그("[서식통일 요소 분석] " + 줄)
                except Exception as exc:
                    진단로그(f"[서식통일] 서식 요소 분석 실패(무시): {exc}")
            # 괄호 크기 규칙도 문서 관행을 따른다. 괄호를 본문보다 작게 쓰는 문서만 그 차이를 적용하고,
            # 본문과 같은 크기로 쓰는 문서는 괄호도 본문 크기로 본다. 단, 표준서식이 기준이고 문두 라벨·괄호
            # 단계가 괄호를 줄이면 그 설정값이 기준이다(표준서식 직후 관행은 보통 0pt라 서로 되돌리게 된다).
            괄호설정_기준 = (표준서식_사용 and 작업_모드 in ("format", "all") and 괄호_축소_사용
                           and stage_enabled(선택_세부작업, "parenthesis", 작업_모드))
            if not 고정_프로필_재적용 and 괄호설정_기준:
                서식통일_괄호크기차이 = int(round(float(괄호_축소_pt) * 100))
                로그(f"[서식통일] 괄호 크기 기준: 설정값(본문보다 {괄호_축소_pt:g}pt 작게, 문두 라벨·괄호 서식과 같음)")
            elif not 고정_프로필_재적용:
                차이빈도 = Counter()
                for 항목들 in 그룹별_표본.values():
                    for 모양, *_ in 항목들:
                        본문크기 = 모양[1]
                        if 본문크기 is None or len(모양) < 4 or not isinstance(모양[3], dict):
                            continue
                        for _, _, size, 길이 in 모양[3].get("parenthetical_size_runs", ()):
                            차이빈도[int(본문크기) - int(size)] += 1
                서식통일_괄호크기차이 = 차이빈도.most_common(1)[0][0] if 차이빈도 else None
                if 서식통일_괄호크기차이 is not None:
                    로그(f"[서식통일] 괄호 크기 관행: 본문보다 {서식통일_괄호크기차이 / 100:g}pt 작게")
            # 프로필은 모든 표본 수집이 끝난 뒤 한 번에 확정한다. 이 구간에는
            # COM 서식 쓰기 호출이 없어 문서의 현재 서식을 조사값으로 보존한다.
            보충표본 = {}
            for 그룹키, 항목들 in 그룹별_표본.items():
                # 본문 표본이 적은 계층만 같은 기호의 제목 표 문장을 함께 본다.
                if len(항목들) < 서식통일_최소문단수:
                    보충 = [모양 for _, 키, 모양 in 제목표_표본 if 키 == 그룹키]
                    if 보충:
                        보충표본[그룹키] = 보충
                        로그(f"[서식통일] '{그룹키[0]}' 본문 표본 {len(항목들)}개 — 같은 계층 제목 표 "
                             f"{len(보충)}개를 대표 서식 조사에 참고")
                if 고정_프로필_재적용:
                    대표 = _서식통일_문서대표프로필.get(그룹키)
                else:
                    대표 = 서식통일_대표([모양 for 모양, *_ in 항목들] + 보충표본.get(그룹키, []))
                    _서식통일_문서대표프로필[그룹키] = 대표
            전체수 = Counter()   # 영역을 합친 같은 계층 문장 수(비교 기준이 있는지 판단)
            for 그룹키, 항목들 in 그룹별_표본.items():
                전체수[그룹키[:2]] += len(항목들) + len(보충표본.get(그룹키, []))
            if 경계 and not 고정_프로필_재적용:
                # 영역 안 표본이 부족해 정하지 못한 값은 문서 전체의 같은 계층 대표값을 따른다.
                전체모양 = defaultdict(list)
                for 그룹키, 항목들 in 그룹별_표본.items():
                    전체모양[그룹키[:2]].extend([모양 for 모양, *_ in 항목들] + 보충표본.get(그룹키, []))
                전체대표 = {키: 서식통일_대표(모양들) for 키, 모양들 in 전체모양.items()}
                for 그룹키 in 그룹별_표본:
                    대표값, 기준 = _서식통일_문서대표프로필.get(그룹키), 전체대표.get(그룹키[:2])
                    for 필드, 값 in (기준 or {}).items():
                        if 대표값 is not None and 대표값.get(필드, (None, 0))[0] is None and 값[0] is not None:
                            대표값[필드] = 값
            if not 고정_프로필_재적용:
                # 엄격한 다수(60%)에 못 미친 글꼴·크기·색은, 최다값이 문서의 다른 계층도 대표로 쓰는
                # 값이면 채택한다(예: ※ 글꼴이 6:4:2로 갈렸지만 최다 글꼴이 ㅇ 대표 글꼴과 같은 경우).
                # 이웃 기준 ※ 보완보다 먼저 한다: 이웃 표본은 몇 개뿐이라 그룹 안 소수 글꼴이 대표가
                # 될 수 있다(실측: 정책회의 ※ 11개 중 2개만 쓰는 글꼴).
                필드위치 = {"font": lambda 모양: 모양[0], "size": lambda 모양: 모양[1],
                            "color": lambda 모양: 모양[3].get("color") if len(모양) > 3 else None,
                            "shade": lambda 모양: 모양[3].get("shade") if len(모양) > 3 else None}
                어휘 = defaultdict(set)
                for 대표값 in _서식통일_문서대표프로필.values():
                    for 필드 in 필드위치:
                        값 = (대표값 or {}).get(필드, (None, 0))[0]
                        if 값 is not None:
                            어휘[필드].add(값)
                for 그룹키, 항목들 in 그룹별_표본.items():
                    대표값 = _서식통일_문서대표프로필.get(그룹키)
                    if not 대표값:
                        continue
                    모양들 = [모양 for 모양, *_ in 항목들] + 보충표본.get(그룹키, [])
                    for 필드, 추출 in 필드위치.items():
                        if 대표값.get(필드, (None, 0))[0] is not None:
                            continue
                        값 = 서식통일_문서어휘_대표([추출(모양) for 모양 in 모양들], 어휘[필드])
                        if 값 is not None:
                            대표값[필드] = (값, sum(1 for 모양 in 모양들 if 추출(모양) == 값))
                            로그(f"[서식통일] '{그룹키[0]}' {필드} 대표값 보조 판정: {값} "
                                 f"(최다값이 문서의 다른 계층 대표값과 같음)")
                _서식통일_참고표_이웃대표_보완(그룹별_표본, _서식통일_문서대표프로필)
                # 괄호 라벨 굵기는 문서 전체의 관행이다. 그룹 안에 라벨 문장이 적어 기준이 없으면
                # 다른 그룹들의 라벨 굵기 다수값을 따른다(예: ※ 라벨 문장이 하나뿐인 경우).
                라벨관행 = Counter()
                for 대표값 in _서식통일_문서대표프로필.values():
                    값, 수 = (대표값 or {}).get("label_bold", (None, 0))
                    if 값 is not None:
                        라벨관행[값] += 수
                if 라벨관행:
                    (관행값, 관행수), *나머지 = 라벨관행.most_common()
                    if not 나머지 or 나머지[0][1] < 관행수:
                        for 그룹키, 대표값 in _서식통일_문서대표프로필.items():
                            if 대표값 and 대표값.get("label_bold", (None, 0))[0] is None:
                                대표값["label_bold"] = (관행값, 관행수)
                                로그(f"[서식통일] '{그룹키[0]}' 괄호 라벨 굵기는 문서 전체 관행({관행값})을 따름")
            # 문단 위 간격은 앞 문장 기호에 따라 달라지므로(□ 다음 ㅇ, ㅇ 다음 ㅇ 등) 문맥별 대표값을
            # 구하고, 대표값을 가진 실제 문단을 예시로 삼아 그 값을 그대로 복사한다.
            위간격모음 = defaultdict(list)
            for 그룹키, 항목들 in 그룹별_표본.items():
                for 모양, 시작, 끝, text in 항목들:
                    위간격모음[(그룹키, 문맥.get(tuple(시작)))].append((모양[3].get("prev_spacing"), 시작))
            위간격대표 = {}
            for key, pairs in 위간격모음.items():
                값, _, _ = 서식통일_최빈값([v for v, _ in pairs if v is not None],
                                       minimum=max(2, min(서식통일_최소문단수, len(pairs))),
                                       ratio=서식통일_최소비율)
                if 값 is not None:
                    위간격대표[key] = (값, next(pos for v, pos in pairs if v == 값))
            로그("[서식통일] 2/5 문서 전체 표본으로 대표값 확정 완료(읽기 전용)")

            # 실제 적용 전에 추정 대표값을 사용자가 확인·수정한다. 특히 ※ 표본이
            # 동률/소수라 대표값이 없을 때는 * 계열과 함께 화면에 제시하고 사용자가
            # 선택하거나 직접 값을 입력해야 보정 계획에 반영된다.
            if not 검증만 and not 고정_프로필_재적용:
                로그("[서식통일] 2/5 조사된 대표 서식 확인")
                if not _서식통일_대표값_사용자검토(그룹별_표본):
                    로그("[서식통일] 사용자가 대표 서식 검토를 취소하여 문서 수정 전 작업 중단")
                    return False

            계획 = []
            for 그룹키, 항목들 in 그룹별_표본.items():
                marker, role, level = 그룹키
                if 고정_프로필_재적용:
                    대표 = _서식통일_문서대표프로필.get(그룹키)
                    if 대표 is None:
                        로그(f"[서식통일] '{marker}/{role}' 후속 단계에서 새로 생긴 그룹은 "
                             "최초 표본이 없어 안전을 위해 건너뜀")
                        continue
                else:
                    대표 = _서식통일_문서대표프로필.get(그룹키)
                if 전체수[그룹키[:2]] < 2:
                    # 같은 계층 문장이 하나뿐이면 '다른 문장'을 가릴 기준이 없다. 고치거나 표시하지 않는다.
                    진단로그(f"[서식통일] '{marker}/{role}' 문장이 하나뿐이라 비교 대상이 없어 건너뜀: "
                             f"{항목들[0][3].strip()[:60]}")
                    continue
                if 글꼴크기만:
                    대표 = _서식통일_글꼴크기_대표(대표)
                글꼴, 글꼴수 = 대표["font"]
                크기, 크기수 = 대표["size"]
                색표준 = 대표.get("color", (None, 0))[0]
                음영표준 = 대표.get("shade", (None, 0))[0]
                문두굵게, 문두굵게수 = 대표.get("marker_bold", (None, 0))
                라벨굵게, 라벨굵게수 = 대표.get("label_bold", (None, 0))
                내어쓰기표준, 내어쓰기수 = 대표.get("hanging_indent", (None, 0))
                if 최종_내어쓰기_예정 and not 검증만:
                    # 뒤의 '최종 서식 기준 내어쓰기' 단계가 항목기호 문장의 내어쓰기를 모두 다시 정한다.
                    # 여기서 대표값대로 넣거나 빼면 그 단계가 곧바로 덮으므로 비교하지 않는다.
                    내어쓰기표준 = None
                그룹미판정 = set()
                for 모양, 시작, 끝, text in 항목들:
                    # 쪽 범위는 대표값 표본에 적용하지 않고 실제 수정 단계에서만 적용한다.
                    if not 쪽범위_안인가(시작):
                        continue
                    # 한/글 텍스트는 문장을 다시 찾는 열쇠로만 쓰고, 기호·위치 판정은 원문으로 한다.
                    원문 = 위치텍스트.get(tuple(시작), text)
                    미판정필드 = _서식통일_미확정_항목(대표, 원문)
                    그룹미판정.update(미판정필드)
                    if 미판정필드:
                        미확정문단.append({"text": text.strip()[:100], "fields": 미판정필드,
                                           "start": 시작, "marker": marker,
                                           "red_marked": bool(모양[3].get("red_marked", False))})
                    글꼴불일치구간 = _서식통일_불일치_구간(모양, 시작, 끝, 글꼴, None)
                    크기불일치구간 = _서식통일_불일치_구간(모양, 시작, 끝, None, 크기)
                    불일치구간 = 서식통일_범위병합(글꼴불일치구간 + 크기불일치구간)
                    문두굵기구간 = _서식통일_굵기_불일치_구간(모양, "marker", 문두굵게)
                    라벨굵기구간 = _서식통일_굵기_불일치_구간(모양, "label", 라벨굵게)
                    괄호크기구간, 괄호목표크기 = _서식통일_부연괄호_불일치_구간(모양, 크기)
                    paragraph_offset = 문단_내어쓰기_기준_오프셋(원문)
                    문단시작 = 시작
                    부가 = 모양[3] if len(모양) > 3 and isinstance(모양[3], dict) else {}
                    # 내어쓰기 상태는 조사한 HWPX 문단 모양에 이미 있다. 문장마다 한/글에 다시 묻지 않는다.
                    if paragraph_offset is None or paragraph_offset <= 0:
                        현재내어쓰기 = None
                    elif "hanging_indent" in 부가:
                        현재내어쓰기 = bool(부가["hanging_indent"])
                    elif 내어쓰기표준 is None:
                        현재내어쓰기 = None     # 비교 기준이 없으면 한/글에 물을 필요가 없다
                    else:
                        현재내어쓰기 = _서식통일_내어쓰기_상태(문단시작, 원문)
                    # 기준 미정 문단은 내어쓰기를 일부러 건너뛰고 빨간 표시로 보고하므로 불일치로 세지 않는다.
                    # 한 줄 문장은 내어쓰기가 보이지 않으므로 비교하지 않는다(서식을 고친 뒤 줄이 늘면
                    # 마무리 단계가 대표값대로 내어쓴다).
                    내어쓰기_불일치 = (내어쓰기표준 is not None and 현재내어쓰기 is not None
                                       and 부가.get("line_count", 2) > 1
                                       and 내어쓰기표준 != 현재내어쓰기 and not 미판정필드)
                    장평표준 = 대표.get("ratio", (None, 0))[0]
                    장평_불일치 = 장평표준 is not None and 부가.get("ratio") not in (None, 장평표준)
                    위간격 = None if 글꼴크기만 else 위간격대표.get((그룹키, 문맥.get(tuple(시작))))
                    위간격_불일치 = 위간격 is not None and 부가.get("prev_spacing") != 위간격[0]
                    # 글자색·음영: 문장 값이 대표값과 다르면 그 값을 쓴 구간만 대표값으로 바꾼다
                    # (다른 색으로 강조한 낱말은 그대로 둔다). 대표값 미확정 문장은 빨간 표시가 우선이다.
                    색구간, 음영구간 = [], []
                    if not 미판정필드:
                        문장색 = 부가.get("color")
                        if 색표준 is not None and 문장색 not in (None, 색표준):
                            색구간 = list(서식통일_범위병합(
                                (run[0], run[1]) for run in 부가.get("color_runs", ()) if run[2] == 문장색))
                        문장음영 = 부가.get("shade")
                        if 음영표준 is not None and 문장음영 not in (None, 음영표준):
                            음영구간 = list(서식통일_범위병합(
                                (run[0], run[1]) for run in 부가.get("shade_runs", ()) if run[2] == 문장음영))
                    # 기울임·밑줄·취소선: 글자색과 같이 문장 대부분의 값이 대표값과 다를 때 그 값을 쓴 구간만 고친다.
                    # 밑줄·취소선을 새로 넣을 때는 대표값을 쓴 다른 문장의 선 모양·색을 그대로 복사한다.
                    글자구간, 글자예시 = {}, {}
                    if not 미판정필드:
                        for 필드 in ("italic", "underline", "strike"):
                            표준 = 대표.get(필드, (None, 0))[0]
                            문장값 = 부가.get(필드)
                            if 표준 is None or 문장값 in (None, 표준):
                                continue
                            글자구간[필드] = list(서식통일_범위병합(
                                (run[0], run[1]) for run in 부가.get(f"{필드}_runs", ()) if run[2] == 문장값))
                            if 필드 != "italic" and 표준 not in ("NONE", False):
                                글자예시[필드] = next(((run[0], run[1]) for 예시모양, *_ in 항목들
                                                       for run in (예시모양[3].get(f"{필드}_runs", ())
                                                                   if len(예시모양) > 3 else ())
                                                       if run[2] == 표준), None)
                                if 글자예시[필드] is None:
                                    글자구간.pop(필드)
                    # 정렬·좌우 여백: 대표값을 가진 같은 계층 문장의 값을 그대로 복사한다(단위 변환 없음).
                    # 왼쪽 여백은 기호 앞 빈칸 수가 대표값과 같고 내어쓰기를 따로 맞추지 않는 문장만 고친다.
                    정렬표준 = 대표.get("align", (None, 0))[0]
                    왼쪽표준 = 대표.get("left", (None, 0))[0]
                    오른쪽표준 = 대표.get("right", (None, 0))[0]
                    빈칸표준 = 대표.get("lead", (None, 0))[0]
                    정렬_불일치 = 정렬표준 is not None and 부가.get("align") not in (None, 정렬표준)
                    왼쪽_불일치 = (왼쪽표준 is not None and 부가.get("left_margin") not in (None, 왼쪽표준)
                                  and 빈칸표준 is not None and 부가.get("lead_spaces") == 빈칸표준
                                  and not 내어쓰기_불일치)
                    오른쪽_불일치 = 오른쪽표준 is not None and 부가.get("right_margin") not in (None, 오른쪽표준)
                    문단모양_예시 = {}
                    for 종류, 불일치, 필드, 표준 in (("align", 정렬_불일치, "align", 정렬표준),
                                                 ("left", 왼쪽_불일치, "left_margin", 왼쪽표준),
                                                 ("right", 오른쪽_불일치, "right_margin", 오른쪽표준)):
                        if not 불일치:
                            continue
                        예시위치 = next((예시시작 for 예시모양, 예시시작, *_ in 항목들
                                         if len(예시모양) > 3 and 예시모양[3].get(필드) == 표준
                                         and (종류 != "left" or 예시모양[3].get("lead_spaces") == 빈칸표준)), None)
                        if 예시위치 is not None:
                            문단모양_예시[종류] = 예시위치
                    if 위간격_불일치:
                        문단모양_예시["prev"] = 위간격[1]
                    if 내어쓰기_불일치 and 내어쓰기표준:
                        # 한 줄짜리 문장은 실측 내어쓰기가 되지 않으므로, 같은 그룹에서 라벨(본문 앞부분)이
                        # 같고 내어쓰기가 된 문장의 들여쓰기 값을 예시로 복사한다.
                        앞부분 = 원문.lstrip()[:max(0, paragraph_offset - (len(원문) - len(원문.lstrip())))]
                        for 예시모양, 예시시작, _, 예시text in 항목들:
                            예시text = 위치텍스트.get(tuple(예시시작), 예시text)
                            예시offset = 문단_내어쓰기_기준_오프셋(예시text)
                            if (예시시작 != 시작 and 예시offset is not None
                                    and 예시모양[3].get("hanging_indent")
                                    and 예시text.lstrip()[:max(0, 예시offset - (len(예시text) - len(예시text.lstrip())))] == 앞부분):
                                문단모양_예시["indent"] = 예시시작
                                break
                    현재불일치 = (불일치구간 or 문두굵기구간 or 라벨굵기구간
                                or 괄호크기구간 or 내어쓰기_불일치 or 장평_불일치 or 문단모양_예시
                                or 색구간 or 음영구간 or 글자구간)
                    item_plan = {"marker": marker, "role": role, "level": level,
                                 "shape": 모양, "start": 문단시작, "end": 끝, "text": text,
                                 "position_text": 원문,
                                 "color": 색표준, "color_runs": 색구간,
                                 "shade": 음영표준, "shade_runs": 음영구간,
                                 "unresolved_fields": 미판정필드,
                                 "font": 글꼴, "size": 크기,
                                 "font_runs": 글꼴불일치구간, "size_runs": 크기불일치구간,
                                 "aside_runs": 괄호크기구간, "aside_size": 괄호목표크기,
                                 "marker_bold_runs": 문두굵기구간, "marker_bold": 문두굵게,
                                 "label_bold_runs": 라벨굵기구간, "label_bold": 라벨굵게,
                                 "hanging_mismatch": 내어쓰기_불일치,
                                 "ratio_fix": 장평표준 if 장평_불일치 else None,
                                 "char_runs": 글자구간, "char_examples": 글자예시,
                                 "char_values": {필드: 대표.get(필드, (None, 0))[0] for 필드 in 글자구간},
                                 "para_examples": 문단모양_예시,
                                 "expected_hanging": 내어쓰기표준,
                                 "mismatch": bool(현재불일치)}
                    계획.append(item_plan)
                    if 검증만:
                        확인문단수 += 1
                        if 현재불일치:
                            항목 = {"text": text.strip()[:100], "fields": [], "expected_actual": {}}
                            if 글꼴불일치구간:
                                항목["fields"].append("font")
                                항목["expected_actual"]["font"] = {
                                    "expected": 글꼴,
                                    "actual": sorted({run[2][0] for run in (모양[2] if len(모양) > 2 else ())
                                                      if run[2][0] is not None}),
                                }
                            if 크기불일치구간:
                                항목["fields"].append("size")
                                항목["expected_actual"]["size"] = {
                                    "expected": 크기,
                                    "actual": sorted({run[2][1] for run in (모양[2] if len(모양) > 2 else ())
                                                      if run[2][1] is not None}),
                                }
                            if 괄호크기구간:
                                항목["fields"].append("parenthetical_size")
                                항목["expected_actual"]["parenthetical_size"] = {
                                    "expected": 괄호목표크기,
                                    "actual": sorted({run[2] for run in 모양[3].get("parenthetical_size_runs", ())}),
                                }
                            if 문두굵기구간:
                                항목["fields"].append("marker_bold")
                            if 라벨굵기구간:
                                항목["fields"].append("label_bold")
                            if 장평_불일치:
                                항목["fields"].append("ratio")
                            if 색구간:
                                항목["fields"].append("color")
                                항목["expected_actual"]["color"] = {"expected": 색표준, "actual": 부가.get("color")}
                            if 음영구간:
                                항목["fields"].append("shade")
                                항목["expected_actual"]["shade"] = {"expected": 음영표준, "actual": 부가.get("shade")}
                            if 위간격_불일치:
                                항목["fields"].append("prev_spacing")
                            for 필드 in 글자구간:
                                항목["fields"].append(필드)
                                항목["expected_actual"][필드] = {"expected": 대표.get(필드, (None, 0))[0],
                                                               "actual": 부가.get(필드)}
                            for 종류, 필드, 불일치 in (("align", "align", 정렬_불일치),
                                                     ("left_margin", "left_margin", 왼쪽_불일치),
                                                     ("right_margin", "right_margin", 오른쪽_불일치)):
                                if 불일치:
                                    항목["fields"].append(종류)
                                    항목["expected_actual"][종류] = {
                                        "expected": {"align": 정렬표준, "left_margin": 왼쪽표준,
                                                     "right_margin": 오른쪽표준}[종류],
                                        "actual": 부가.get(필드)}
                            if 내어쓰기_불일치:
                                항목["fields"].append("hanging_indent")
                                항목["expected_actual"]["hanging_indent"] = {
                                    "expected": 내어쓰기표준, "actual": 현재내어쓰기,
                                }
                            불일치목록.append(항목)
                if 그룹미판정:
                    판정불가그룹.append({"marker": marker, "role": role,
                                         "samples": len(항목들), "fields": sorted(그룹미판정)})
                글꼴표시 = f"{글꼴} ({글꼴수})" if 글꼴 is not None else "판정 보류"
                크기표시 = f"{크기 / 100:g}pt ({크기수})" if 크기 is not None else "판정 보류"
                진단로그(f"[서식통일] '{marker}/{role}' 대표값({len(항목들)}문장): 글꼴 {글꼴표시}, "
                         f"크기 {크기표시}, 글자색 {색표준 or '판정 보류'}, 음영 {음영표준 or '판정 보류'}, "
                         f"문두 굵기 {문두굵게}, 괄호라벨 굵기 {라벨굵게}, 내어쓰기 {내어쓰기표준} ({내어쓰기수}), "
                         f"기울임 {대표.get('italic', (None, 0))[0]}, 밑줄 {대표.get('underline', (None, 0))[0]}, "
                         f"취소선 {대표.get('strike', (None, 0))[0]}, 정렬 {대표.get('align', (None, 0))[0]}, "
                         f"왼쪽 여백 {대표.get('left', (None, 0))[0]}(기호 앞 빈칸 {대표.get('lead', (None, 0))[0]}), "
                         f"오른쪽 여백 {대표.get('right', (None, 0))[0]}")
                continue

            후보수 = sum(1 for p in 계획 if p["mismatch"])
            로그(f"[서식통일] 3/5 예외 영역 자동 검출: 수정 후보 {후보수}개 / "
                 f"대표값 미확정 {len(미확정문단)}개 — 개별 승인 없이 적용")
            if 검증만:
                for item in (미확정문단 if 서식통일_빨간표시_사용 else ()):
                    if not item["red_marked"]:
                        불일치목록.append({"text": item["text"], "fields": ["unresolved_red_marking"]})
                if not 확인문단수 and not 판정불가그룹 and not 불일치목록:
                    # 검사할 항목기호 문장이 없는 문서(서식·표만 있는 문서)는 '해당 없음'이다. 예전에는 '미완료'로 0점이 되어
                    # 서식 통일 판정이 '부분 달성'으로 나왔다(2026-10-04 범정부오피스 서식 9종).
                    status = "not_applicable"
                elif not 확인문단수:
                    status = "incomplete"
                elif 판정불가그룹 and not 불일치목록 and 서식통일_빨간표시_사용:
                    status = "incomplete"
                else:
                    status = "failed" if 불일치목록 else "passed"
                _서식통일_최종감사 = {"status": status, "checked": 확인문단수,
                                     "issues": 불일치목록, "not_checkable": 판정불가그룹,
                                     "unresolved": 미확정문단,
                                     "hierarchy": [f"{키[0]}({키[1]})" for 키 in 체계],
                                     "systems": ["본문"] + [이름 for _, 이름 in 경계],
                                     "cover_excluded": bool(표지문단)}
                로그(f"5/5 저장 결과 서식통일 검수(읽기 전용): {status} / 확인 {확인문단수}개 / "
                     f"불일치 {len(불일치목록)}개 / 보류 그룹 {len(판정불가그룹)}개")
                if 불일치목록:
                    항목별 = Counter(field for issue in 불일치목록 for field in issue["fields"])
                    로그("[서식통일] 불일치 항목별 문장 수: "
                         + ", ".join(f"{field} {count}" for field, count in 항목별.most_common()))
                return _서식통일_최종감사

            if XML조사:
                # XML 조사는 HWPX 글로 표본을 만들었다. 이어지는 자간·내어쓰기 단계는 한/글이 읽는 글을 열쇠로 쓰므로,
                # 실제로 고칠 문장만 한/글에서 글을 다시 읽어 바꾼다(HWPX 글과 다르면 그 문장은 건드리지 않는다).
                for item in 계획:
                    if not (item["mismatch"] or item["unresolved_fields"]):
                        continue
                    한글 = None
                    try:
                        hwp.SetPos(*item["start"])
                        hwp_run("MoveParaBegin")
                        한글 = 현재문단_텍스트()
                    except Exception:
                        pass
                    if 한글 is not None and _서식통일_공백제거(한글) == _서식통일_공백제거(item["position_text"]):
                        item["text"] = 한글
                    else:
                        진단로그(f"[서식통일] 한/글 글이 HWPX와 달라 이 문장은 건너뜀: {item['position_text'].strip()[:60]}")
                        item["mismatch"] = False
                        item["unresolved_fields"] = []
            # 4단계: 문서 순서로 한 문단의 서식 → 자간 → 내어쓰기를 끝낸다.
            로그("[서식통일] 4/5 문장별 자동 처리: 서식 → 자간 → 내어쓰기")
            if not 고정_프로필_재적용:
                단계표시("서식통일 적용")
            for item in sorted(계획, key=lambda entry: entry["start"]):
                if 중단_요청됨():
                    return False
                if not item["mismatch"] and not item["unresolved_fields"]:
                    continue
                if item["mismatch"]:
                    진단로그(f"[서식통일 문장] 시작 {item['start']}: {item['text'].strip()[:100]}")
                    _서식통일_문단서식_적용(item)
                    # 기준이 미확정된 문장은 확정된 항목만 고치고 빨간 표시한다.
                    # 불완전한 기준으로 자간/내어쓰기를 연쇄 변경하지 않는다.
                    if not item["unresolved_fields"]:
                        if item["hanging_mismatch"] and not item["expected_hanging"]:
                            _서식통일_문단내어쓰기_적용(item)   # 대표값이 '내어쓰기 없음'이면 여기서 해제
                        # 내어쓰기 → 자간 → 외톨이 당기기는 모든 문장의 서식을 맞춘 뒤 한 묶음으로 한다.
                        _서식통일_자간보류문단[item["text"].strip()] = item["expected_hanging"]
                        _서식통일_위치텍스트_보관[item["text"].strip()] = item["position_text"]
                        _서식통일_보류위치[item["text"].strip()] = item["start"]
                    elif not 서식통일_빨간표시_사용:
                        _서식통일_자간보류문단[item["text"].strip()] = item["expected_hanging"]
                        _서식통일_위치텍스트_보관[item["text"].strip()] = item["position_text"]
                        _서식통일_보류위치[item["text"].strip()] = item["start"]
                    교정수 += 1
                    진단로그(f"[서식통일 문장] 완료 {item['start']}")
                if item["unresolved_fields"] and not 서식통일_빨간표시_사용:
                    진단로그(f"[서식통일] 대표값 미확정은 뒤이은 표준 서식이 결정하여 빨간 표시 생략: "
                             f"{item['text'].strip()[:100]}")
                elif item["unresolved_fields"]:
                    _서식통일_미확정_빨간표시(item["start"], item["end"])
                    진단로그(f"[서식통일] 대표값 미확정 빨간 표시 ({', '.join(item['unresolved_fields'])}): "
                             f"{item['text'].strip()[:100]}")
            로그(f"[서식통일] 4/5 문장별 처리 완료; 미확정 문단 {len(미확정문단)}개 "
                 f"{'빨간 표시' if 서식통일_빨간표시_사용 else '표준 서식에 맡김'}, "
                 "저장 후 5/5 결과 검수 예정")
            if 서식통일_빨간표시_사용 and not 고정_프로필_재적용:
                # 표준 서식이 뒤따르지 않으면 서식통일이 고친 문장만 지금 자간을 조정한다.
                if 서식통일_보류자간_재조정() is False:
                    return False
            로그(f"서식통일 완료 (교정 {교정수}개 문단)")
            return True
        return bind_function(서식통일_전체_적용, _docfit_namespace)
    if _docfit_symbol == '서식통일_자간조정_반영':
        def 서식통일_자간조정_반영(사용):
            """서식통일이 고친 문장의 자간 조정 사용 여부를 반영하고 반영한 값을 돌려준다."""
            global 서식통일_자간조정_사용
            서식통일_자간조정_사용 = bool(사용)
            return 서식통일_자간조정_사용
        return bind_function(서식통일_자간조정_반영, _docfit_namespace)
    if _docfit_symbol == '서식통일_문장_마무리':
        def 서식통일_문장_마무리(시작, text, 내어쓰기):
            """한 문장의 마무리 묶음: 내어쓰기 → 자간 → 마지막 줄 외톨이 글자 당기기.

            내어쓰기를 먼저 확정해야 자간 조정 뒤 줄 폭이 다시 바뀌지 않고, 외톨이 글자 당기기는
            자간 조정으로 확정된 줄바꿈을 기준으로 해야 하므로 이 순서로 한 문장씩 끝낸다.
            """
            if 내어쓰기 and 문단_내어쓰기_기준_오프셋(text) is not None:
                문단_내어쓰기_적용(시작, text)
            hwp.SetPos(*시작)
            hwp_run("MoveParaEnd")
            끝 = hwp.GetPos()
            if 서식통일_자간조정_사용 and 끝[:2] == 시작[:2] and 끝[2] > 시작[2]:
                if _서식통일_문단자간_조정(시작, 끝) is False:
                    return False
                if 서식통일_줄병합_사용:
                    hwp.SetPos(*시작)
                    지난 = set()
                    while True:
                        if 중단_요청됨():
                            return False
                        pos = hwp.GetPos()
                        if pos[:2] != 시작[:2] or pos in 지난:
                            break
                        지난.add(pos)
                        문장부호_줄병합_시도()
                        hwp_run("MoveLineEnd")
                        hwp_run("MoveNextChar")
            hwp.SetPos(*시작)
            return True
        return bind_function(서식통일_문장_마무리, _docfit_namespace)
    if _docfit_symbol == '_서식통일_마무리_위치로':
        def _서식통일_마무리_위치로(대상):
            """계획 위치로 바로 가서 글이 같은 문장을 마무리한다. 마무리한 수를 돌려준다(중단 요청이면 False).

            서식 적용·내어쓰기·자간은 문단 수를 바꾸지 않아 계획 위치가 그대로 맞는다. 그래도 위치의 글이 열쇠와
            다르면(다른 단계가 문단을 바꾼 경우) 그 문장은 대상에 남겨 예전 순회가 글로 찾게 한다.
            """
            조정수 = 0
            위치순 = sorted((위치, key) for key, 위치 in _서식통일_보류위치.items() if key in 대상 and 위치)
            for 위치, key in 위치순:
                if 중단_요청됨():
                    return False
                try:
                    if hwp.SetPos(*위치) is False:
                        continue
                    hwp_run("MoveParaBegin")
                    시작 = hwp.GetPos()
                    text = 현재문단_텍스트()
                except Exception:
                    continue
                if 시작[0] != 0 or text.strip() != key:
                    continue
                원문 = _서식통일_위치텍스트_보관.get(key, text)
                if _서식통일_공백제거(원문) != _서식통일_공백제거(text):
                    원문 = text
                if 서식통일_문장_마무리(시작, 원문, bool(대상.pop(key))) is False:
                    return False
                조정수 += 1
            return 조정수
        return bind_function(_서식통일_마무리_위치로, _docfit_namespace)
    if _docfit_symbol == '서식통일_보류자간_재조정':
        def 서식통일_보류자간_재조정():
            """(표준 서식 없음) 서식통일이 고친 문장에 마무리 묶음을 적용한다."""
            if not _서식통일_자간보류문단:
                return True
            단계표시("서식통일 마무리")
            대상 = dict(_서식통일_자간보류문단)
            조정수 = 0
            if 알파_서식통일_위치마무리_사용:
                조정수 = _서식통일_마무리_위치로(대상)
                if 조정수 is False:
                    return False
                if 대상:
                    진단로그(f"[서식통일] 계획 위치에서 찾지 못한 문장 {len(대상)}개는 문서를 순회해 찾음")
            if 대상:
                hwp_run("MoveDocBegin")
            while 대상:
                if 중단_요청됨():
                    return False
                hwp_run("MoveParaBegin")
                시작 = hwp.GetPos()
                if 시작[0] == 0:
                    text = 현재문단_텍스트()
                    key = text.strip()
                    if key in 대상:
                        원문 = _서식통일_위치텍스트_보관.get(key, text)
                        if _서식통일_공백제거(원문) != _서식통일_공백제거(text):
                            원문 = text
                        if 서식통일_문장_마무리(시작, 원문, bool(대상.pop(key))) is False:
                            return False
                        조정수 += 1
                if not 다음_문단으로_진행():
                    break
            로그(f"[서식통일] 교정 문장 마무리(내어쓰기→자간→외톨이 당기기): {조정수}개"
                 + (f" / 위치를 찾지 못한 문장 {len(대상)}개" if 대상 else ""))
            for text in 대상:
                검수_문제_기록(현재_처리파일, "[서식통일 자간 미조정] 문장 위치를 찾지 못함: " + text[:60])
            return True
        return bind_function(서식통일_보류자간_재조정, _docfit_namespace)
    if _docfit_symbol == '_서식통일_표모형':
        def _서식통일_표모형(제외문단=()):
            """HWPX의 표를 표 서식통일 판정용 모형으로 읽는다(읽기 전용).

            한/글의 목록 번호는 문서 순서의 subList(표 칸·머리말·캡션 등) 순번 + 2다(실측: 업무계획 문서
            46개, 정책회의 1,179개가 COM 목록 수와 일치). 칸 글자 위치를 확신할 수 없는 문단(칸 안
            표·그림)은 비교에서 뺀다.
            """
            문서경로 = _서식통일_현재_HWPX()
            if 문서경로 is None:
                return []
            from docfit_core.style_inventory import _tag
            분석 = _서식통일_HWPX_분석(문서경로)
            목록번호 = {}
            for 문단 in 분석["paragraphs"]:
                for item in 문단.iter():
                    if _tag(item) == "subList":
                        목록번호[id(item)] = len(목록번호) + 2
            표들 = []
            for 번호, 문단 in enumerate(분석["paragraphs"]):
                if 번호 in 제외문단:
                    continue
                for 표 in (item for item in 문단.iter() if _tag(item) == "tbl"):
                    칸들 = []
                    for tc in (item for tr in 표 if _tag(tr) == "tr" for item in tr if _tag(item) == "tc"):
                        sub = next((item for item in tc if _tag(item) == "subList"), None)
                        주소 = next((item for item in tc if _tag(item) == "cellAddr"), None)
                        if sub is None or id(sub) not in 목록번호:
                            continue
                        문단들 = []
                        for 칸문단번호, p in enumerate(item for item in sub if _tag(item) == "p"):
                            조각 = [(run, *_서식통일_run_text(run)) for run in p if _tag(run) == "run"]
                            글자 = "".join(text for _, text, _ in 조각)
                            runs = []
                            if all(확실 for _, _, 확실 in 조각):
                                cursor = 0
                                for run, text, _ in 조각:
                                    길이 = len(text.encode("utf-16-le")) // 2
                                    char = 분석["chars"].get(run.get("charPrIDRef"))
                                    if char and text.strip():
                                        runs.append((cursor, cursor + 길이, char["font"].get("hangul"),
                                                     round(char["size_pt"] * 100),
                                                     str(char.get("color", "")).upper(), bool(char.get("bold"))))
                                    cursor += 길이
                            문단들.append({"index": 칸문단번호, "text": 글자, "runs": runs})
                        칸들.append({"area": 목록번호[id(sub)],
                                     "header": 주소 is not None and 주소.get("rowAddr") == "0",
                                     "fill": tc.get("borderFillIDRef"), "paras": 문단들})
                    첫글자 = next((para["text"] for 칸 in 칸들 for para in 칸["paras"] if para["text"].strip()), "")
                    표들.append({"index": len(표들), "cells": 칸들,
                                 "box": 표.get("rowCnt") == "1" and 표.get("colCnt") == "1",
                                 "marker": 서식통일_항목기호(첫글자)[0]})
            return 표들
        return bind_function(_서식통일_표모형, _docfit_namespace)
    if _docfit_symbol == '서식통일_표_전체_적용':
        def 서식통일_표_전체_적용(검증만=False):
            """같은 종류(같은 모양 칸·같은 기호 제목 상자)의 표끼리 글자 서식을 맞춘다.

            판정은 docfit_core.table_unify가 HWPX만 보고 하며, 한/글에서는 고칠 칸 문단의 글자가
            HWPX와 같은지 확인한 뒤 그 구간만 바꾼다. 검증만=True면 읽기 전용으로 남은 불일치를 센다.
            """
            from docfit_core.table_unify import plan_table_fixes
            if 중단_요청됨():
                return False
            if not 검증만:
                단계표시("표 서식통일")
            표들 = _서식통일_표모형()
            고칠것, 요약 = plan_table_fixes(표들)
            검사표수 = len(표들)
            if 쪽범위_사용중():
                # 대표값은 문서 전체에서 얻되 수정·검수 대상은 선택한 쪽의 칸으로 제한한다.
                고칠것 = [fix for fix in 고칠것
                         if 쪽범위_안인가((fix['area'], fix['para'], fix['start']))]
                검사표수 = sum(any(쪽범위_안인가((칸['area'], 0, 0)) for 칸 in 표['cells'])
                             for 표 in 표들)
            if 검증만:
                issues = [{"text": fix["text"].strip()[:100], "fields": [f"table_{fix['field']}"],
                           "expected_actual": {fix["field"]: {"expected": fix["value"], "actual": fix["was"]}}}
                          for fix in 고칠것]
                status = "failed" if issues else "passed"
                로그(f"[표 서식통일] 저장 결과 검수(읽기 전용): {status} / 표 {검사표수}개 / 불일치 구간 {len(issues)}개")
                return {"status": status, "checked": 검사표수, "issues": issues}
            로그(f"[표 서식통일] 표 {len(표들)}개 조사 — 고칠 구간 {len(고칠것)}개 "
                 + (", ".join(f"{이름} {수}" for 이름, 수 in 요약.items()) or "(없음)"))
            적용, 건너뜀 = 0, 0
            확인됨 = {}
            for fix in sorted(고칠것, key=lambda item: (item["area"], item["para"], item["start"])):
                if 중단_요청됨():
                    return False
                문단키 = (fix["area"], fix["para"])
                if 문단키 not in 확인됨:
                    # 목록 번호가 어긋나면 다른 칸을 고치게 되므로, 칸 문단 글자가 HWPX와 같은지 확인한다.
                    try:
                        hwp.SetPos(fix["area"], fix["para"], 0)
                        같은칸 = (tuple(hwp.GetPos()[:2]) == 문단키
                                  and _서식통일_공백제거(현재문단_텍스트()) == _서식통일_공백제거(fix["text"]))
                    except Exception:
                        같은칸 = False
                    확인됨[문단키] = 같은칸
                    if not 같은칸:
                        진단로그(f"[표 서식통일] 칸 위치를 확인하지 못해 건너뜀: {fix['text'].strip()[:40]}")
                if not 확인됨[문단키]:
                    건너뜀 += 1
                    continue
                시작 = (fix["area"], fix["para"], fix["start"])
                끝 = (fix["area"], fix["para"], fix["end"])
                try:
                    단어모드_범위선택(시작, 끝)
                    # 항목별로 따로 분기한다(사전 리터럴은 값을 모두 계산해 글꼴 이름 / 100에서 멈춤).
                    if fix["field"] == "color":
                        _서식통일_색_적용("TextColor", fix["value"])
                    elif fix["field"] == "font":
                        문자모양_적용_현재선택(폰트=fix["value"], 자간_유지=True)
                    elif fix["field"] == "size":
                        문자모양_적용_현재선택(크기_pt=fix["value"] / 100, 자간_유지=True)
                    else:
                        문자모양_적용_현재선택(굵게=fix["value"], 자간_유지=True)
                    적용 += 1
                    진단로그(f"[표 서식통일] {fix['reason']}: {fix['field']} {fix['was']} → {fix['value']} "
                             f"'{fix['text'].strip()[:30]}'")
                finally:
                    hwp_run("Cancel")
            hwp_run("MoveDocBegin")
            로그(f"[표 서식통일] 완료: {적용}개 구간 수정"
                 + (f", 칸 위치 확인 실패로 {건너뜀}개 건너뜀" if 건너뜀 else ""))
            return True
        return bind_function(서식통일_표_전체_적용, _docfit_namespace)
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
    if _docfit_symbol == '괄호_안쪽':
        def 괄호_안쪽(match):
            return match.group(1) if match.group(1) is not None else match.group(2)
        return bind_function(괄호_안쪽, _docfit_namespace)
    if _docfit_symbol == '대괄호인가':
        def 대괄호인가(match):
            return match.group(0).startswith("[")
        return bind_function(대괄호인가, _docfit_namespace)
    if _docfit_symbol == '괄호_문두_라벨인가':
        def 괄호_문두_라벨인가(text, match):
            """실제 문두/문장부호 직후의 첫 괄호만 라벨로 판정한다.

            '- (이동도서관) ...' -> 라벨
            '- 예산 편성(차량 운영비...)' -> 부연설명(라벨 아님)
            """
            if not text or match is None:
                return False

            앞부분 = text[:match.start()]
            if not _문두_무시문자_정규식.sub("", 앞부분):
                return True

            마커_끝 = 문장부호_마커_끝위치(text)
            if 마커_끝 is None or 마커_끝 > match.start():
                return False

            사이 = text[마커_끝:match.start()]
            return not _문두_무시문자_정규식.sub("", 사이)
        return bind_function(괄호_문두_라벨인가, _docfit_namespace)
    if _docfit_symbol == '괄호_뒤_콜론인가':
        def 괄호_뒤_콜론인가(text, 끝_offset):
            idx = 끝_offset
            while idx < len(text) and (text[idx].isspace() or text[idx] in "\u200b\u2060\ufeff"):
                idx += 1
            return idx < len(text) and text[idx] in (":", "：")
        return bind_function(괄호_뒤_콜론인가, _docfit_namespace)
    if _docfit_symbol == '세트후속_범위괄호_라벨인가':
        def 세트후속_범위괄호_라벨인가(text, match, 세트후속문단=False):
            """※ 세트의 후속 '(6~16번) :' 같은 범위 괄호를 라벨로 판정한다.

            이 라벨은 상위 문장부호 바로 뒤의 첫 괄호가 아니더라도 같은 세트의
            계층 라벨이므로 부연설명 괄호처럼 2pt 축소하면 안 된다.
            """
            if not 세트후속문단:
                return False

            앞부분 = text[:match.start()]
            if _문두_무시문자_정규식.sub("", 앞부분):
                return False
            if not 괄호_뒤_콜론인가(text, match.end()):
                return False
            return bool(괄호_범위라벨_정규식.fullmatch(괄호_안쪽(match)))
        return bind_function(세트후속_범위괄호_라벨인가, _docfit_namespace)
    if _docfit_symbol == '문단_범위_선택':
        def 문단_범위_선택(문단_시작위치, 시작offset, 끝offset):
            """문단 안의 [시작offset, 끝offset) 구간을 한 번의 SelectText 호출로 선택한다.

            v1.11 효율성 개선: 예전에는 이 구간을 MoveSelRight로 한 글자씩 반복
            이동하며 선택했다. 글자 수만큼 COM 호출이 발생해 라벨/괄호가 길수록
            느려졌는데, SelectText는 시작·끝 좌표만 지정하면 한 번에 선택되므로
            결과는 같고 호출 횟수만 크게 줄어든다.
            """
            try:
                시작offset, 끝offset = (문단_위치(문단_시작위치, 시작offset),
                                      문단_위치(문단_시작위치, 끝offset, 끝쪽=True) if 끝offset > 시작offset else None)
            except RuntimeError as e:
                # 숨은 글자로 위치를 맞출 수 없는 문단: 아무것도 선택하지 않고 실패를 돌려준다(호출한 곳은 고치지 않는다).
                진단로그(f"[문단 위치] {e}")
                hwp.SetPos(*문단_시작위치)
                return False
            if 끝offset is None:
                끝offset = 시작offset
            hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2])
            return hwp.SelectText(
                문단_시작위치[1], 문단_시작위치[2] + 시작offset,
                문단_시작위치[1], 문단_시작위치[2] + 끝offset,
            )
        return bind_function(문단_범위_선택, _docfit_namespace)
    if _docfit_symbol == '선택범위_현재크기_pt':
        def 선택범위_현재크기_pt(문단_시작위치, 시작offset, 끝offset):
            if 끝offset <= 시작offset:
                return None
            try:
                문단_범위_선택(문단_시작위치, 시작offset, 끝offset)
                act = hwp.HAction
                pset = hwp.HParameterSet.HCharShape
                act.GetDefault("CharShape", pset.HSet)
                hwp_run("Cancel")
                return pset.Height / 100.0
            except Exception:
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
                return None
        return bind_function(선택범위_현재크기_pt, _docfit_namespace)
    if _docfit_symbol == '괄호_축소량_pt':
        def 괄호_축소량_pt(text):
            """이 문단의 괄호 안 글자를 줄일 크기(pt). 서식 예시가 계층마다 정한 값이 있으면 그 값(0이면 줄이지 않음)."""
            기호별 = (표준서식_설정 or {}).get("괄호_축소_기호별") or {}
            if 기호별:
                기호 = 서식통일_항목기호(text)[0]
                if 기호 in 기호별:
                    return float(기호별[기호] or 0)
                if not 기호:
                    # 항목기호 없는 문단(개요 상자 글 등)은 예시가 줄인 근거가 없으면 줄이지 않는다. 대표 폭으로 줄이면
                    # 예시 자신도 재연하지 못했다(서식 재연 시험, 2026-10-16).
                    return 0.0
            return float(괄호_축소_pt)
        return bind_function(괄호_축소량_pt, _docfit_namespace)
    if _docfit_symbol == '대괄호_축소_제외':
        def 대괄호_축소_제외():
            """예시를 복사한 서식(계층별 괄호 줄임 값이 있음)이면 대괄호 [ ] 안 글자는 줄이지 않는다.

            서식 분석은 둥근 괄호의 글자 크기만 재서 줄임 값을 배운다. 예시에서 '[중요 부분은 …]'처럼 줄이지 않은
            대괄호까지 같은 폭으로 줄여 예시 자신에 서식을 입혀도 원본과 달라졌다(서식 재연 시험, 2026-10-16).
            기본 서식은 예전처럼 대괄호도 줄인다.
            """
            return bool((표준서식_설정 or {}).get("괄호_축소_기호별"))
        return bind_function(대괄호_축소_제외, _docfit_namespace)
    if _docfit_symbol == '괄호_텍스트_크기_축소_현재선택':
        def 괄호_텍스트_크기_축소_현재선택(축소_pt=None):
            if hwp is None:
                return
            try:
                기존_pt = hwp.CharShape.Item("Height") / 100.0
                if 기존_pt:
                    새_pt = max(1, 기존_pt - (괄호_축소_pt if 축소_pt is None else 축소_pt))
                    문자모양_적용_현재선택(크기_pt=새_pt)
            except Exception as e:
                로그(f"괄호 텍스트 크기 축소 실패(무시): {e}")
        return bind_function(괄호_텍스트_크기_축소_현재선택, _docfit_namespace)
    if _docfit_symbol == '문두_라벨_굵게_제외_문단인가':
        def 문두_라벨_굵게_제외_문단인가(text):
            text = (text or '').lstrip()
            symbol = '**' if text.startswith('**') else (text[:1] or '기타')
            if symbol not in 문두라벨_기호설정:
                symbol = '기타'
            return not 문두라벨_기호설정.get(symbol, True)
        return bind_function(문두_라벨_굵게_제외_문단인가, _docfit_namespace)
    if _docfit_symbol == '항목기호_키':
        def 항목기호_키(text):
            """항목기호별 설정·일관성 규칙에서 쓰는 기호 키('**', '-', 'ㅇ' 등)."""
            text = (text or '').lstrip()
            return '**' if text.startswith('**') else (text[:1] or '기타')
        return bind_function(항목기호_키, _docfit_namespace)
    if _docfit_symbol == '일관성_굵게_머리말_범위':
        def 일관성_굵게_머리말_범위(text):
            """'- 조례제정 (설명)'에서 굵게 맞출 머리말 '조례제정'의 [시작, 끝) 위치.

            항목기호 바로 뒤의 짧은 머리말 다음에 부연설명 괄호가 이어지는 문단만
            대상으로 한다. 콜론 라벨·괄호 라벨 문단(기존 규칙이 처리), 머리말이
            길거나 쉼표·마침표가 있는 일반 문장은 None.
            """
            if not text or not 문장부호_시작인가(text):
                return None
            마커_끝 = 문장부호_마커_끝위치(text)
            if 마커_끝 is None:
                return None
            idx = 마커_끝
            while idx < len(text) and text[idx] in (" ", "\t"):
                idx += 1
            나머지 = text[idx:].rstrip("\r\n")
            if not 나머지 or 나머지[0] in "(（" or re.match(r"^[^\n\r:：]{1,25}?[ \t]*[:：][ \t]+\S", 나머지):
                return None
            m = re.match(r"^([^()（）:：,，.。\r\n]+?)[ \t]*[(（][^()（）]{3,}[)）]", 나머지)
            if not m:
                return None
            머리말 = m.group(1).strip()
            if not 머리말 or len(머리말) > _일관성_머리말_최대글자수 or not any(c.isalpha() for c in 머리말):
                return None
            시작 = idx + 나머지.find(머리말)
            return 시작, 시작 + len(머리말)
        return bind_function(일관성_굵게_머리말_범위, _docfit_namespace)
    if _docfit_symbol == '문두_라벨_굵게_선반영':
        def 문두_라벨_굵게_선반영(문단_시작위치, text):
            """Shift+Tab 내어쓰기 계산 직전, 오프셋에 포함되는 문두 라벨(콜론 라벨
            또는 괄호 라벨)을 미리 굵게 처리해 첫 줄의 실제 폭을 확정한다.

            v1.12 버그수정: 기존에는 표준서식적용(Shift+Tab 내어쓰기 포함) 단계가
            끝난 뒤에야 별도 단계(괄호_텍스트_크기_축소_전체_적용)에서 '(개요)',
            '추진부서 :' 같은 문두 라벨을 굵게 처리했다. Shift+Tab
            (ParagraphShapeIndentAtCaret)은 실행 시점의 커서 '화면 X좌표'를 그대로
            둘째 줄 내어쓰기 값으로 굳히는데, 라벨이 굵어지지 않은 상태로 그 좌표를
            캡처한 뒤 나중에 라벨이 굵어져 첫 줄 폭이 늘어나면, 이미 확정된 내어쓰기
            값은 따라서 넓어지지 않아 첫 줄 본문 시작 글자와 둘째 줄 내어쓰기 위치가
            어긋난다(예: 'ㅇ (개요) 특정 사업에...' 문단에서 '특'과 다음 줄
            '통'의 위치가 달라지는 현상). 이 함수가 미리 굵게 처리를 해서 Shift+Tab이
            이미 최종 폭을 기준으로 커서 좌표를 캡처하게 만든다.

            표준서식_문단_처리는 자체 기호(□/ㅇ/-/※)로 시작하는 문단만 대상으로
            하므로(세트 후속 상속 문단은 이 함수에 도달하지 않는다) 세트 후속 여부는
            고려하지 않는다. 이후 전체 문서 패스인 괄호_및_라벨_텍스트_문단_처리가
            동일 라벨을 다시 굵게 처리하지만, 이미 굵은 텍스트에 굵게를 한 번 더
            적용하는 것뿐이라 결과에 영향이 없다(멱등).
            """
            if not 괄호_라벨_볼드_사용 or not text or hwp is None:
                return
            # □ 문단은 문두 라벨 굵게 제외.
            if 문두_라벨_굵게_제외_문단인가(text):
                return
            try:
                if not 문장부호_시작인가(text):
                    return
                마커_끝 = 문장부호_마커_끝위치(text)
                if 마커_끝 is None:
                    return

                idx = 마커_끝
                while idx < len(text) and text[idx] in (" ", "\t"):
                    idx += 1
                if idx < len(text):
                    나머지 = text[idx:]
                    콜론_매치 = re.match(r"^([^\n\r:：]{1,25}?)[ \t]*([:：])[ \t]+(\S.*)$", 나머지)
                    if 콜론_매치:
                        라벨_텍스트 = 콜론_매치.group(1).strip()
                        if 라벨_텍스트:
                            라벨_시작 = idx + 나머지.find(라벨_텍스트)
                            라벨_끝 = 라벨_시작 + len(라벨_텍스트)
                            문단_범위_선택(문단_시작위치, 라벨_시작, 라벨_끝)
                            문자모양_적용_현재선택(굵게=True)
                            hwp_run("Cancel")
                            return

                if "(" in text:
                    for match in 괄호_정규식.finditer(text):
                        if 대괄호인가(match):
                            continue
                        if 괄호_문두_라벨인가(text, match):
                            문단_범위_선택(문단_시작위치, match.start(), match.end())
                            문자모양_적용_현재선택(굵게=True)
                            hwp_run("Cancel")
                            return
            except Exception as e:
                로그(f"문두 라벨 선반영 굵게 실패(무시): {e}")
        return bind_function(문두_라벨_굵게_선반영, _docfit_namespace)
    if _docfit_symbol == '괄호_및_라벨_텍스트_문단_처리':
        def 괄호_및_라벨_텍스트_문단_처리(세트후속문단=False):
            """
            현재 문단에 대해:
            1) 문두 라벨(콜론 앞 텍스트 or 괄호 라벨) 굵게 처리
            2) 문장 중간·끝의 부연설명 괄호 크기 2pt 축소

            주의: 이 함수는 한 칸 표(제목 박스·요지 박스 등) 안의 문단에도 적용된다.
            한 칸 표 보호(현재_한칸표인가)는 표 헤더/본문 서식적용처럼 "행 역할"에
            의존하는 로직에만 의미가 있고, 괄호 축소·라벨 굵게는 문단 텍스트 패턴만
            보므로 한 칸 표라고 해서 건너뛸 이유가 없다. 이 가드가 있으면 요지 박스처럼
            한 칸 표로 만들어진 본문성 문단의 부연설명 괄호가 전혀 축소되지 않는다.
            """
            text = 현재문단_텍스트()
            if not text:
                return 0

            # 서식 예시가 이 계층의 괄호를 줄이지 않았으면(0pt) 줄이지 않는다.
            축소_pt = 괄호_축소량_pt(text)
            축소_사용 = 괄호_축소_사용 and 축소_pt > 0
            if not 괄호_라벨_볼드_사용 and (not 축소_사용 or ("(" not in text and "[" not in text)):
                return 0

            문단_시작위치 = hwp.GetPos()
            적용_횟수 = 0

            # --------------------------------------------------------
            # 1. 문두 콜론 라벨 굵게 ("- 추진부서 : 내용", "ㅇ (추진부서) : 내용")
            # --------------------------------------------------------
            if 괄호_라벨_볼드_사용 and 문장부호_시작인가(text) and not 문두_라벨_굵게_제외_문단인가(text):
                마커_끝 = 문장부호_마커_끝위치(text)
                if 마커_끝 is not None:
                    idx = 마커_끝
                    while idx < len(text) and text[idx] in (" ", "\t"):
                        idx += 1
                    if idx < len(text):
                        나머지 = text[idx:]
                        콜론_매치 = re.match(r"^([^\n\r:：]{1,25}?)[ \t]*([:：])[ \t]+(\S.*)$", 나머지)
                        if 콜론_매치:
                            라벨_텍스트 = 콜론_매치.group(1).strip()
                            if 라벨_텍스트:
                                라벨_시작 = idx + 나머지.find(라벨_텍스트)
                                라벨_끝 = 라벨_시작 + len(라벨_텍스트)
                                try:
                                    문단_범위_선택(문단_시작위치, 라벨_시작, 라벨_끝)
                                    문자모양_적용_현재선택(굵게=True)
                                    hwp_run("Cancel")
                                    적용_횟수 += 1
                                    _일관성_굵게_적용기호.add(항목기호_키(text))
                                    진단로그(f"[문두라벨굵게] '{라벨_텍스트}' 굵게 적용")
                                except Exception as e:
                                    로그(f"문두 라벨 굵게 적용 중 오류(무시): {e}")

            # --------------------------------------------------------
            # 2. 괄호 처리 (문두 라벨 괄호 굵게 / 본문 부연설명 괄호 축소)
            # --------------------------------------------------------
            if "(" in text or "[" in text:
                for match in 괄호_정규식.finditer(text):
                    앞부분 = text[:match.start()]
                    시작_offset = match.start()
                    끝_offset = match.end()

                    if 대괄호인가(match) and 괄호_문두_라벨인가(text, match):
                        continue
                    범위_세트라벨 = 세트후속_범위괄호_라벨인가(
                        text, match, 세트후속문단=세트후속문단
                    )
                    if 괄호_문두_라벨인가(text, match) or 범위_세트라벨:
                        if 범위_세트라벨:
                            진단로그(f"[세트후속라벨] '{match.group(0)}' 괄호 2pt 축소 제외")
                        # □ 문단의 문두 라벨 괄호는 굵게 제외 — 라벨이므로 축소도 하지
                        # 않고 원형 그대로 둔다.
                        if 괄호_문두_라벨인가(text, match) and 문두_라벨_굵게_제외_문단인가(text):
                            진단로그(f"[문두라벨굵게제외] □ 문단 '{match.group(0)}' 굵게 미적용")
                            continue
                        if not 괄호_라벨_볼드_사용:
                            continue
                        try:
                            문단_범위_선택(문단_시작위치, 시작_offset, 끝_offset)
                            문자모양_적용_현재선택(굵게=True)
                            hwp_run("Cancel")
                            적용_횟수 += 1
                            if 괄호_문두_라벨인가(text, match):
                                _일관성_굵게_적용기호.add(항목기호_키(text))
                            진단로그(f"[괄호굵게] '{match.group(0)}' 굵게 적용")
                        except Exception as e:
                            로그(f"괄호 라벨 굵게 적용 중 오류(무시): {e}")
                        continue

                    if not 축소_사용:
                        continue
                    if 대괄호인가(match) and 대괄호_축소_제외():
                        continue

                    if 시작_offset > 0:
                        주변_pt = 선택범위_현재크기_pt(문단_시작위치, 시작_offset - 1, 시작_offset)
                    elif 끝_offset < len(text):
                        주변_pt = 선택범위_현재크기_pt(문단_시작위치, 끝_offset, 끝_offset + 1)
                    else:
                        주변_pt = None

                    괄호_pt = 선택범위_현재크기_pt(문단_시작위치, 시작_offset, 끝_offset)

                    if 괄호_pt is not None and 주변_pt is not None and 괄호_pt < 주변_pt - 0.4:
                        continue

                    try:
                        문단_범위_선택(문단_시작위치, 시작_offset, 끝_offset)
                        괄호_텍스트_크기_축소_현재선택(축소_pt)
                        hwp_run("Cancel")
                        적용_횟수 += 1
                        진단로그(f"[괄호축소] '{match.group(0)}' 글자 크기 {축소_pt:g}pt 축소")
                    except Exception as e:
                        로그(f"괄호 텍스트 축소 중 오류(무시): {e}")

            try:
                hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2])
            except Exception:
                pass

            return 적용_횟수
        return bind_function(괄호_및_라벨_텍스트_문단_처리, _docfit_namespace)
    if _docfit_symbol == '라벨괄호_계획':
        def 라벨괄호_계획(text, 세트후속문단=False, 크기=None):
            """문단 글에서 굵게 할 문두 라벨과 줄일 부연설명 괄호 구간을 고른다(순수 함수, 알파 1-b).

            괄호_및_라벨_텍스트_문단_처리(한/글 경로)와 같은 판정이다. 크기(시작, 끝) → 그 구간 글자 크기(pt, 모르면 None).
            ([(시작, 끝, {"bold": True} | {"shrink_pt": n})], 문두 라벨을 굵게 했는지)를 돌려준다."""
            구간, 라벨적용 = [], False
            if not text:
                return 구간, 라벨적용
            축소_pt = 괄호_축소량_pt(text)
            축소_사용 = 괄호_축소_사용 and 축소_pt > 0
            if not 괄호_라벨_볼드_사용 and (not 축소_사용 or ("(" not in text and "[" not in text)):
                return 구간, 라벨적용
            if 괄호_라벨_볼드_사용 and 문장부호_시작인가(text) and not 문두_라벨_굵게_제외_문단인가(text):
                마커_끝 = 문장부호_마커_끝위치(text)
                if 마커_끝 is not None:
                    idx = 마커_끝
                    while idx < len(text) and text[idx] in (" ", "\t"):
                        idx += 1
                    if idx < len(text):
                        나머지 = text[idx:]
                        콜론_매치 = re.match(r"^([^\n\r:：]{1,25}?)[ \t]*([:：])[ \t]+(\S.*)$", 나머지)
                        if 콜론_매치 and 콜론_매치.group(1).strip():
                            라벨_텍스트 = 콜론_매치.group(1).strip()
                            라벨_시작 = idx + 나머지.find(라벨_텍스트)
                            구간.append((라벨_시작, 라벨_시작 + len(라벨_텍스트), {"bold": True}))
                            라벨적용 = True
            if "(" in text or "[" in text:
                for match in 괄호_정규식.finditer(text):
                    시작, 끝 = match.start(), match.end()
                    if 대괄호인가(match) and 괄호_문두_라벨인가(text, match):
                        continue
                    범위_세트라벨 = 세트후속_범위괄호_라벨인가(text, match, 세트후속문단=세트후속문단)
                    if 괄호_문두_라벨인가(text, match) or 범위_세트라벨:
                        if 괄호_문두_라벨인가(text, match) and 문두_라벨_굵게_제외_문단인가(text):
                            continue
                        if not 괄호_라벨_볼드_사용:
                            continue
                        구간.append((시작, 끝, {"bold": True}))
                        if 괄호_문두_라벨인가(text, match):
                            라벨적용 = True
                        continue
                    if not 축소_사용:
                        continue
                    if 대괄호인가(match) and 대괄호_축소_제외():
                        continue
                    # 날짜 바로 뒤 요일 괄호('26. 10. 11.(일)')는 날짜의 일부라 줄이지 않는다(한/글 경로 결과와 같게, 2026-10-11 실측).
                    if re.fullmatch(r'[월화수목금토일]', 괄호_안쪽(match) or '') and re.search(r'\d\s*[.\-/]?\s*$', text[:시작]):
                        continue
                    크기 = 크기 or (lambda a, b: None)
                    주변_pt = 크기(시작 - 1, 시작) if 시작 > 0 else (크기(끝, 끝 + 1) if 끝 < len(text) else None)
                    괄호_pt = 크기(시작, 끝)
                    if 괄호_pt is not None and 주변_pt is not None and 괄호_pt < 주변_pt - 0.4:
                        continue
                    구간.append((시작, 끝, {"shrink_pt": 축소_pt}))
            return 구간, 라벨적용
        return bind_function(라벨괄호_계획, _docfit_namespace)
    if _docfit_symbol == '라벨괄호_hwpx_처리':
        def 라벨괄호_hwpx_처리(source, target=None, selections=None):
            """모든 문단(표·글상자 안 포함)의 문두 라벨을 굵게, 부연설명 괄호 글자를 줄인다(라벨괄호_계획과 같은 판정)."""
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
                return {n: [0] for n in names}
            if not any(selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            styles = 글자구간모듈.CharStyles(header)
            전 = {n: 제목_문자열(roots[n]) for n in names}
            총, 굵게기호, 일관성_후보 = 0, set(), []
            _, 여러칸표_문단 = 표안_문단_구분(roots.values())     # 한/글 경로처럼 여러 칸 표 안 문단은 다루지 않는다
            for n in names:
                활성_세트_들여쓰기 = None
                for para in [x for x in roots[n].iter() if 제목_xml이름(x) == 'p' and id(x) not in 여러칸표_문단]:
                    text = 글자구간모듈.paragraph_text(para)
                    if (괄호_라벨_볼드_사용 and 항목기호_굵게_일관성_사용 and not 문두_라벨_굵게_제외_문단인가(text)):
                        범위 = 일관성_굵게_머리말_범위(text)
                        if 범위:
                            일관성_후보.append((para, text, 범위))
                    세트후속 = False
                    if 활성_세트_들여쓰기 is not None and 세트문장_후속문단인가(활성_세트_들여쓰기, text):
                        세트후속 = True
                    else:
                        활성_세트_들여쓰기 = 세트문장_선행들여쓰기_폭(text) if 세트문장_시작인가(text) else None

                    def 크기(a, b, para=para):
                        값 = {styles.height_pt(글자구간모듈.char_id_at(para, i)) for i in range(max(0, a), b)}
                        값.discard(None)
                        return min(값) if 값 else None

                    구간, 라벨적용 = 라벨괄호_계획(text, 세트후속, 크기)
                    if 라벨적용:
                        굵게기호.add(항목기호_키(text))
                    총 += 글자구간모듈.apply_ranges(para, 구간, styles)
            일관성 = 0
            for para, text, (시작, 끝) in 일관성_후보:
                if 항목기호_키(text) in 굵게기호:
                    일관성 += 글자구간모듈.apply_ranges(para, [(시작, 끝, {"bold": True})], styles)
            if any(제목_문자열(roots[n]) != 전[n] for n in names):
                raise RuntimeError('문두 라벨/괄호 서식 중 글 보존 검사에 실패했습니다.')
            if not (총 + 일관성):
                shutil.copyfile(source, target)
                로그("문두 라벨/괄호 서식(XML): 바꿀 곳 없음")
                return 0
            for n in names:
                contents[n] = ET.tostring(roots[n], encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"문두 라벨 / 괄호 처리 완료(XML) (총 {총 + 일관성}건, 항목기호 굵게 일관성 {일관성}건)")
            return 총 + 일관성
        return bind_function(라벨괄호_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '표안_문단_구분':
        def 표안_문단_구분(roots):
            """(한 칸 표 안 문단 id 집합, 여러 칸 표 안 문단 id 집합). 한/글 경로의 문단 순회(MoveParaEnd·MoveNextChar)는
            본문과 한 칸 표 안 문단만 돌고 여러 칸 표 안 문단은 돌지 않는다(2026-10-11 test4 실측: 제목 표 날짜·담당자 칸,
            일반 표 머리글 '구  분'은 손대지 않음). XML 글 규칙·라벨 처리도 같은 범위만 다룬다."""
            한칸, 여러칸 = set(), set()
            for root in roots:
                for tbl in [x for x in root.iter() if 제목_xml이름(x) == 'tbl']:
                    대상 = 한칸 if tbl.get('rowCnt') == '1' and tbl.get('colCnt') == '1' else 여러칸
                    대상.update(id(x) for x in tbl.iter() if 제목_xml이름(x) == 'p')
            return 한칸 - 여러칸, 여러칸
        return bind_function(표안_문단_구분, _docfit_namespace)
    if _docfit_symbol == '공백규칙_글변환':
        def 공백규칙_글변환(text, 한칸표=False):
            """문장 내 공백 정규화 10개 규칙을 한/글 경로(_문장내_공백_정규화_순회)와 같은 순서로 문단 글에 적용한다(순수 함수, 알파 1-c).

            한칸표(1행 1열 표 안 문단)이면 문두 ㅁ·괄호 안 공백·쉼표·콜론·연속 공백 규칙을 건너뛴다(한/글 경로와 같음)."""
            s = text or ""
            if not s:
                return s
            if not 한칸표:
                off = 문두_미음_기호_위치(s)
                if off is not None:
                    s = s[:off] + "□" + s[off + 1:]
            for m in reversed(list(YEAR_QUOTE_PATTERN.finditer(s))):
                s = s[:m.start()] + "’" + s[m.end():]
            for i, r in reversed(straight_double_quote_replacements(s)):
                s = s[:i] + r + s[i + 1:]
            for i, r in reversed(curly_single_quote_replacements(s)):
                s = s[:i] + r + s[i + 1:]
            s = normalize_date_range_marks(s)
            if not 한칸표:
                # 한/글 경로: 한 칸 표가 있는 문서는 문서 전체 바꾸기를 하지 않고, 문단 보정은 한 칸 표 안 문단을 건너뛴다.
                s = 괄호_안쪽_공백_패턴.sub("", s)
                for a, b in reversed(쉼표_공백_보정_대상(s) or []):
                    s = s[:a] + ", " + s[b:]
                for a, b, 교체 in reversed(콜론_공백_보정_대상(s) or []):
                    s = s[:a] + (교체 or "") + s[b:]
                for a, b in reversed(단어사이_연속공백_정리_대상(s) or []):
                    s = s[:a] + " " + s[b:]
                낫표 = 항목기호_낫표_빈칸_구간(s)
                if 낫표:
                    s = s[:낫표[0]] + s[낫표[1]:]     # ' ㅇ 「법령」' → ' ㅇ「법령」'(사용자 규칙 2026-10-17)
            공문 = normalize_official_spacing(s)
            if normalize_attachment_list_header(s) != s:
                공문 = normalize_attachment_list_header(공문)
            return 공문
        return bind_function(공백규칙_글변환, _docfit_namespace)
    if _docfit_symbol == '문장부호뒤공백_글변환':
        def 문장부호뒤공백_글변환(text, 한칸표=False):
            """항목기호 뒤 공백을 표준 반각 한 칸으로(문장부호_뒤_공백_보정_문단_처리와 같은 판정, 순수 함수)."""
            if 한칸표 or not text:
                return text
            마커_끝 = 문장부호_마커_끝위치(text)
            조치 = marker_space_fix(text, 마커_끝)
            if 조치 is None:
                return text
            if 조치 == "replace":
                return text[:마커_끝] + " " + text[마커_끝 + 1:]
            return text[:마커_끝] + " " + text[마커_끝:]
        return bind_function(문장부호뒤공백_글변환, _docfit_namespace)
    if _docfit_symbol == '글규칙_hwpx_처리':
        def 글규칙_hwpx_처리(source, target=None, selections=None):
            """_글규칙_XML_구성에 따라 공백 규칙 → 문장부호 뒤 공백 → 문두 라벨/괄호 서식을 모든 문단에 적용한다."""
            구성 = dict(_글규칙_XML_구성)
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            names = sorted((n for n in contents if re.fullmatch(r'Contents/section\d+\.xml', n)),
                           key=lambda n: int(re.search(r'section(\d+)', n).group(1)))
            if selections is None:
                return {n: [0] for n in names}
            if not any(selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            roots = {n: safe_xml_fromstring(contents[n]) for n in names}
            # 한 칸 표 안 문단은 공백·문장부호 규칙 일부를 건너뛰고(한칸표_보호영역), 여러 칸 표 안 문단은 다루지 않는다.
            한칸표_문단, 여러칸표_문단 = 표안_문단_구분(roots.values())
            공백수 = 기호수 = 0
            for n in names:
                for para in [x for x in roots[n].iter() if 제목_xml이름(x) == 'p' and id(x) not in 여러칸표_문단]:
                    글 = 글고치기모듈.paragraph_text(para)
                    if 구성["punct"] and not id(para) in 한칸표_문단:
                        # 항목기호 바로 뒤 고정폭 빈칸은 지우고 아래 규칙이 일반 빈칸 1칸으로 맞춘다(사용자 규칙 검사, 2026-10-17)
                        마커_끝 = 문장부호_마커_끝위치(글)
                        빈칸끝 = 마커_끝 + len(글[마커_끝:]) - len(글[마커_끝:].lstrip()) if 마커_끝 is not None else None
                        if 마커_끝 is not None and 글고치기모듈.drop_spaces_at(para, 마커_끝, 빈칸끝):
                            기호수 += 1
                    새글 = 글
                    한칸 = id(para) in 한칸표_문단
                    if 구성["space"]:
                        새글 = 공백규칙_글변환(새글, 한칸표=한칸)
                    if 새글 != 글:
                        공백수 += 1
                    if 구성["punct"]:
                        기호뒤 = 문장부호뒤공백_글변환(새글, 한칸표=한칸)
                        기호수 += 기호뒤 != 새글
                        새글 = 기호뒤
                    if 새글 != 글:
                        글고치기모듈.apply_text(para, 새글)
            for n in names:
                contents[n] = ET.tostring(roots[n], encoding='utf-8', xml_declaration=True)
            중간 = Path(str(target) + '.text.hwpx')
            _hwpx_안전_저장(contents, 중간)
            로그(f"글 규칙(XML): 공백 정규화 문단 {공백수}개 · 문장부호 뒤 공백 {기호수}개")
            try:
                if 구성["label"]:
                    결과 = 라벨괄호_hwpx_처리(중간, target, 라벨괄호_hwpx_처리(중간))
                    if not 결과:
                        shutil.copyfile(중간, target)
                else:
                    shutil.copyfile(중간, target)
            finally:
                try:
                    중간.unlink()
                except OSError:
                    pass
            return 1
        return bind_function(글규칙_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '현재문서_XML단계_적용':
        def 현재문서_XML단계_적용(이름, 처리함수, 파일명):
            """지금 열린 문서를 HWPX로 저장해 XML 처리기를 적용하고 결과를 다시 연다(알파 1-b). 실패하면 False."""
            결과 = 제목붙임_선행적용(현재_처리파일 or '', 현재문서_기준=True, 처리목록=((True, 이름, 처리함수, 파일명),))
            # 다시 연 문서는 문단 위치·글이 바뀌었을 수 있으므로 읽어 둔 문단 글·위치표를 버린다.
            global _최근_문단글
            _문단글_캐시_비우기()
            _최근_문단글 = None
            _문단_위치표_저장.clear()
            return 결과 is not False
        return bind_function(현재문서_XML단계_적용, _docfit_namespace)
    if _docfit_symbol == '괄호_텍스트_크기_축소_전체_적용':
        def 괄호_텍스트_크기_축소_전체_적용():
            if 중단_요청됨():
                return False
            if 알파_라벨괄호_XML_사용 and 쪽범위_요청 is None:
                return 현재문서_XML단계_적용('문두 라벨/괄호 서식', 라벨괄호_hwpx_처리, 'label_paren.hwpx')
            로그("문두 라벨(콜론/괄호) 굵게 및 부연설명 괄호 크기 축소 처리 시작")
            순회_시작()
            총_적용_횟수 = 0
            활성_세트_들여쓰기 = None
            _일관성_굵게_적용기호.clear()
            일관성_후보 = []

            while True:
                if 중단_요청됨():
                    return False

                text = 현재문단_텍스트()
                세트후속문단 = False
                if (괄호_라벨_볼드_사용 and 항목기호_굵게_일관성_사용
                        and not 문두_라벨_굵게_제외_문단인가(text)):
                    범위 = 일관성_굵게_머리말_범위(text)
                    if 범위:
                        일관성_후보.append((hwp.GetPos(), text, 범위))

                # 순차 문단 문맥을 유지해 '※ ...' 다음의 더 깊게 들여쓴
                # '(6~16번) : ...' 등을 같은 세트의 후속 문단으로 인식한다.
                if 활성_세트_들여쓰기 is not None and 세트문장_후속문단인가(활성_세트_들여쓰기, text):
                    세트후속문단 = True
                else:
                    활성_세트_들여쓰기 = None
                    if 세트문장_시작인가(text):
                        활성_세트_들여쓰기 = 세트문장_선행들여쓰기_폭(text)

                결과 = 괄호_및_라벨_텍스트_문단_처리(세트후속문단=세트후속문단)
                if 결과:
                    총_적용_횟수 += 결과
                if not 범위_다음_문단으로_진행():
                    break

            # 문서 전체를 본 뒤에야 어떤 항목기호에 라벨 굵게가 적용됐는지 알 수 있다.
            일관성_적용 = 0
            for 위치, text, (시작, 끝) in 일관성_후보:
                if 중단_요청됨():
                    return False
                if 항목기호_키(text) not in _일관성_굵게_적용기호:
                    continue
                try:
                    문단_범위_선택(위치, 시작, 끝)
                    문자모양_적용_현재선택(굵게=True)
                    hwp_run("Cancel")
                    일관성_적용 += 1
                    진단로그(f"[항목기호 굵게 일관성] '{text[시작:끝]}' 굵게 적용 "
                             f"('{항목기호_키(text)}' 기호 라벨 굵게와 통일, 괄호 설명 제외)")
                except Exception as e:
                    로그(f"항목기호 굵게 일관성 적용 중 오류(무시): {e}")
            총_적용_횟수 += 일관성_적용

            로그(f"문두 라벨 / 괄호 처리 완료 (총 {총_적용_횟수}건, 항목기호 굵게 일관성 {일관성_적용}건)")
            return True
        return bind_function(괄호_텍스트_크기_축소_전체_적용, _docfit_namespace)
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
    if _docfit_symbol == '텍스트_hwpx로_변환':
        def 텍스트_hwpx로_변환(텍스트, 대상경로):
            """현재 hwp에 새 빈 문서를 만들어 텍스트를 문단 단위로 넣고 HWPX로 저장한다.

            FileNew는 새 문서 창을 하나 더 연다. 한/글 시작 때의 빈 문서가 뒤에 남으면, 이후 문서를 닫고 다시 여는
            단계에서 그 빈 문서가 활성 문서가 되어 최종 SaveAs가 빈 문서를 저장했다(txt 입력에서만 간헐 발생,
            2026-10-21 재현). 새 문서를 만든 뒤 다른 문서 창은 저장하지 않고 닫아 창을 하나만 둔다.
            """
            if hwp.Run("FileNew") is False:
                raise RuntimeError("빈 문서를 만들지 못했습니다.")
            try:
                문서들 = hwp.XHwpDocuments
                활성ID = 문서들.Active_XHwpDocument.DocumentID
                for 번호 in reversed(range(int(문서들.Count))):
                    문서 = 문서들.Item(번호)
                    if 문서.DocumentID != 활성ID:
                        문서.Close(False)
            except Exception as error:   # 시험용 가짜 객체·구버전 한/글은 건너뛴다
                진단로그(f"[빈 문서 정리] 다른 문서 창을 닫지 못함(무시): {error}")
            from docfit_core.labeled_text import mixes_report_lines
            # 제목:/개요: 라벨에 □ ㅇ - * 항목 줄이 섞인 TXT는 v1.73처럼 줄마다 넣고 준말 단계가 라벨을 서식 표로 바꾼다.
            # 라벨 해석기에 넘기면 항목이 한 문단으로 합쳐지고 '* 용어:' 주석이 'ㅇ (* 용어)'로 바뀌었다(v1.76 회귀).
            if looks_labeled(텍스트) and not mixes_report_lines(텍스트):
                블록들 = parse_labeled_text(텍스트)
                라벨블록_한글삽입(hwp, 블록들)
                if hwp.SaveAs(str(대상경로), "HWPX", "") is False:
                    raise RuntimeError("텍스트를 HWPX로 저장하지 못했습니다.")
                if any(b["kind"] in _라벨_블록_종류 for b in 블록들):
                    if hwp.Clear(1) is False:
                        raise RuntimeError("서식 표 후처리를 위해 작업 문서를 닫지 못했습니다.")
                    라벨_서식표_적용(대상경로)
                    return False  # 후처리 대상으로 COM 문서를 닫았음
                return True
            줄들 = 텍스트.replace("\r\n", "\n").replace("\r", "\n").split("\n")
            for 순번, 줄 in enumerate(줄들):
                if 줄:
                    텍스트_삽입(줄)
                if 순번 < len(줄들) - 1:
                    hwp_run("BreakPara")
            if hwp.SaveAs(str(대상경로), "HWPX", "") is False:
                raise RuntimeError("텍스트를 HWPX로 저장하지 못했습니다.")
            return True  # SaveAs 후 현재 한글 문서가 대상 HWPX를 계속 편집 중
        return bind_function(텍스트_hwpx로_변환, _docfit_namespace)
    if _docfit_symbol == '라벨블록_한글삽입':
        def 라벨블록_한글삽입(한글, 블록들):
            """labeled_text 블록을 한/글 문서 끝에 차례로 넣는다(A4 제목 상자 표 템플릿).

            제목·개요(상자)·참고는 1×1 표로 넣는다. 1×1 제목 표는 제목 서식(제목_hwpx_처리)의
            대상이 아니므로(유형 삭제) 제목 서식이 자동으로 적용되지 않는다. 제목1·제목2·개요 라벨은
            표식을 붙여 넣고 저장 뒤 라벨_서식표_적용이 각각의 서식 표로 바꾼다.
            """
            def 글쓰기(내용):
                act = 한글.HAction
                pset = 한글.HParameterSet.HInsertText
                act.GetDefault("InsertText", pset.HSet)
                pset.Text = 내용
                act.Execute("InsertText", pset.HSet)

            def 표넣기(행들, 소제목=False):
                열수 = max(len(행) for 행 in 행들)
                act = 한글.HAction
                pset = 한글.HParameterSet.HTableCreation
                act.GetDefault("TableCreate", pset.HSet)
                pset.Rows = len(행들)
                pset.Cols = 열수
                pset.WidthType = 0   # 단 너비에 맞춤(2는 임의 너비라 글자 폭만큼 좁아진다)
                pset.HeightType = 0  # 자동 높이
                pset.TableProperties.TreatAsChar = 1
                if 소제목 and 열수 == 2:
                    # 번호 칸은 좁게, 제목 칸은 글 길이만큼. 현재 용지 본문 폭을 넘지 않는다.
                    page = 한글.HParameterSet.HSecDef
                    act.GetDefault("PageSetup", page.HSet)
                    전체폭 = int(page.PageDef.PaperWidth - page.PageDef.LeftMargin - page.PageDef.RightMargin)
                    번호폭 = min(전체폭 // 4, max(1600, len(행들[0][0]) * 900))
                    제목폭 = min(전체폭 - 번호폭, max(3000, len(행들[0][1]) * 900 + 1200))
                    pset.WidthType = 2
                    pset.CreateItemArray("ColWidth", 2)
                    pset.ColWidth.SetItem(0, 번호폭)
                    pset.ColWidth.SetItem(1, 제목폭)
                act.Execute("TableCreate", pset.HSet)
                칸들 = [칸 for 행 in 행들 for 칸 in (행 + [""] * (열수 - len(행)))]
                for 순번, 칸 in enumerate(칸들):
                    if 칸:
                        글쓰기(칸)
                    if 순번 < len(칸들) - 1:
                        한글.Run("TableRightCell")
                한글.Run("Cancel")
                한글.MovePos(3, 0, 0)  # 문서 끝(표 다음 문단)으로 나온다

            처음 = True
            for 블록 in 블록들:
                if not 처음:
                    한글.Run("BreakPara")
                처음 = False
                종류 = 블록["kind"]
                if 종류 == "blank":
                    continue
                if 종류 in _라벨_블록_종류:
                    # 제목1·제목2·개요는 표식을 붙여 넣고, 저장 뒤 라벨_서식표_적용이 서식 표로 바꾼다.
                    표넣기([[_라벨_표식[_라벨_블록_종류[종류]] + 블록["text"]]])
                elif 종류 in ("title", "ref"):
                    표넣기([[블록["text"] if 종류 != "ref" else f"참고  {블록['text']}"]])
                elif 종류 == "table":
                    표넣기(블록["rows"], 소제목=블록.get("role") == "heading")
                else:
                    글쓰기(f"{블록['marker']} {블록['text']}".strip())
        return bind_function(라벨블록_한글삽입, _docfit_namespace)
    if _docfit_symbol == 'AI답변_개조식_변환':
        def AI답변_개조식_변환(텍스트, 라벨형식=False, 마크다운문서=False):
            """AI 답변으로 보이면 (변환한 글, True), 아니면 (원문, False). 라벨형식=True면 제목:/개요:/네모:/원: 라벨 글로 바꾼다."""
            if (not 마크다운문서 and not 알파_AI답변변환_사용) or not looks_like_ai_answer(텍스트, markdown_document=마크다운문서):
                return 텍스트, False
            try:
                if 라벨형식:
                    변환 = ai_answer_to_labeled_text(텍스트, markdown_document=마크다운문서)
                    if looks_labeled(변환):
                        return 변환, True
                변환 = ai_answer_to_outline_text(텍스트, markdown_document=마크다운문서)
            except Exception as 오류:
                로그(f"AI 답변 변환 실패(글을 그대로 넣음): {오류}")
                return 텍스트, False
            return (변환, True) if 변환.strip() else (텍스트, False)
        return bind_function(AI답변_개조식_변환, _docfit_namespace)
    if _docfit_symbol == '텍스트_hwpx_단독변환':
        def 텍스트_hwpx_단독변환(텍스트, 대상경로, 라벨_해석=True, AI_변환=True):
            """'텍스트 붙여넣기'에서 저장 즉시 HWPX로 바꿀 때 쓰는, 배치 작업(작업_실행)과
            완전히 독립된 한/글 세션.

            전역 hwp는 작업_실행 전용이라 배치가 실행 중일 때 그 세션을 건드리면
            RPC_E_WRONG_THREAD 류 오류가 난다. 이 함수는 자기 몫의 한/글 인스턴스를
            새로 띄우고 끝나면 바로 종료해, 배치가 동시에 있어도 서로 간섭하지
            않는다. COM은 생성한 스레드에서 정리해야 하므로 반드시 전용 스레드
            (daemon Thread)에서만 호출한다.
            """
            if AI_변환 and 라벨_해석 and not looks_labeled(텍스트):
                텍스트, 변환됨 = AI답변_개조식_변환(텍스트, 라벨형식=True)
                if 변환됨:
                    로그("AI 답변으로 보고 개조식(제목·개요·□ ㅇ - 항목)으로 변환해 문서를 만듭니다.")
            pythoncom.CoInitialize()
            단독_hwp = None
            서식표_후처리 = False
            try:
                단독_hwp = 한글_COM_인스턴스_생성(독립=True)
                try:
                    단독_hwp.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE)
                except Exception:
                    pass  # 새 문서를 만들어 텍스트만 적으므로 보안 모듈 등록 실패는 무시해도 된다.
                if 단독_hwp.Run("FileNew") is False:
                    raise RuntimeError("빈 문서를 만들지 못했습니다.")
                if 라벨_해석 and looks_labeled(텍스트):
                    # 라벨 형식(제목:/네모:/원: …)이면 제목·개요·참고를 1×1 상자 표로, 표: 줄을 표로 넣는다.
                    블록들 = parse_labeled_text(텍스트)
                    라벨블록_한글삽입(단독_hwp, 블록들)
                    if 단독_hwp.SaveAs(str(대상경로), "HWPX", "") is False:
                        raise RuntimeError("HWPX로 저장하지 못했습니다.")
                    서식표_후처리 = any(b["kind"] in _라벨_블록_종류 for b in 블록들)
                else:
                    줄들 = 텍스트.replace("\r\n", "\n").replace("\r", "\n").split("\n")
                    for 순번, 줄 in enumerate(줄들):
                        if 줄:
                            act = 단독_hwp.HAction
                            pset = 단독_hwp.HParameterSet.HInsertText
                            act.GetDefault("InsertText", pset.HSet)
                            pset.Text = 줄
                            act.Execute("InsertText", pset.HSet)
                        if 순번 < len(줄들) - 1:
                            단독_hwp.Run("BreakPara")
                    if 단독_hwp.SaveAs(str(대상경로), "HWPX", "") is False:
                        raise RuntimeError("HWPX로 저장하지 못했습니다.")
            finally:
                if 단독_hwp is not None:
                    try:
                        # 중간에 실패해 저장 안 된 문서가 남아도 '저장할까요?' 창 없이 닫는다.
                        단독_hwp.Clear(1)
                    except Exception:
                        pass
                    try:
                        단독_hwp.Quit()
                    except Exception:
                        pass
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
            if 서식표_후처리:
                # 한/글이 저장 파일을 놓은 뒤에 표식 표를 제목1·개요 서식 표로 바꾼다.
                라벨_서식표_적용(대상경로)
        return bind_function(텍스트_hwpx_단독변환, _docfit_namespace)
    if _docfit_symbol == '외부문서_hwpx로_변환':
        def 외부문서_hwpx로_변환(원본경로, 확장자, 대상경로):
            """.txt/.md/.doc/.docx/.pdf를 자간·서식 처리에 쓸 작업용 HWPX로 변환한다.

            .md/.doc/.docx/.pdf는 선택형 kordoc 엔진(Node.js)이 있어야 문단·표·
            글머리 구조를 살려 변환한다. 없으면 .md는 서식 없이 텍스트로라도
            변환하고, .doc/.docx/.pdf는 이 엔진 없이는 읽을 방법이 없어 오류로
            알린다.

            PDF는 텍스트층이 없는 스캔 페이지만 내장 OCR로 인식해(--ocr) 이미지만
            있는 문서도 글자를 뽑아낸다. 추출된 이미지는 kordoc이 마크다운 옆
            images/ 폴더에 저장하는데, generate 단계에 --image-dir로 그 폴더를
            알려줘야 실제 이미지 데이터가 결과 HWPX에 그대로 임베드된다(지정하지
            않으면 자리표시만 남고 이미지가 사라진다).
            """
            if 확장자 == ".txt":
                원문 = 텍스트파일_읽기(원본경로)
                # 복사한 AI 답변은 단순 기호문자 대신 라벨 블록으로 변환한다.
                # 그래야 텍스트_hwpx로_변환이 제목·개요·표를 스타일 표로 넣고 저장된 서식을 적용한다.
                원문, 변환됨 = AI답변_개조식_변환(원문, 라벨형식=True)
                if 변환됨:
                    로그(f"AI 답변으로 보고 개조식 항목기호로 변환해 서식 작업에 넘깁니다: {Path(원본경로).name}")
                문서열림 = 텍스트_hwpx로_변환(원문, 대상경로)
                # 텍스트_hwpx로_변환은 현재 한글 문서에서 FileNew→SaveAs를 수행한다.
                # 호출 뒤 이미 대상 HWPX가 활성 문서이므로 pipeline에서 같은 파일을 다시
                # Open하면 중복 문서/활성 창 혼선이 생길 수 있다. True는 "대상 문서가 열려 있음".
                return bool(문서열림)
            if 확장자 == ".md":
                # 이미지가 없는 AI 답변형 마크다운은 엔진 대신 라벨 블록으로 변환해 서식 적용 경로에 넘긴다. 이미지가 있으면 엔진이 처리한다.
                try:
                    원문 = 텍스트파일_읽기(원본경로)
                    if looks_labeled(원문):
                        return bool(텍스트_hwpx로_변환(원문, 대상경로))
                    변환문, 변환됨 = ("", False) if re.search(r"!\[[^\]]*\]\(", 원문) else AI답변_개조식_변환(원문, 라벨형식=True, 마크다운문서=True)
                except Exception:
                    변환문, 변환됨 = "", False
                if 변환됨:
                    로그(f"AI 답변형 마크다운을 개조식 항목기호로 변환해 서식 작업에 넘깁니다: {Path(원본경로).name}")
                    return bool(텍스트_hwpx로_변환(변환문, 대상경로))
                try:
                    generate_hwpx(str(원본경로), "보고서", str(대상경로), image_dir=Path(원본경로).parent)
                    return False
                except KordocUnavailableError as e:
                    로그(f"고급 문서 엔진을 쓸 수 없어 서식 없이 텍스트로만 변환합니다: {e}")
                    원문, 변환됨 = AI답변_개조식_변환(텍스트파일_읽기(원본경로))
                    return bool(텍스트_hwpx로_변환(원문, 대상경로))
            from docfit_core.file_conversion import IMAGE_INPUT_EXTENSIONS, convert_image_to_hwpx
            if 확장자 in IMAGE_INPUT_EXTENSIONS:
                convert_image_to_hwpx(원본경로, 대상경로)
                return False
            # 파일 추가·독립 변환에서 허용한 오피스 입력을 후처리에서도 동일하게 받는다.
            # TXT/MD의 기존 한/글 라벨 경로와 PDF 서식 이식은 위·아래 분기를 유지한다.
            from docfit_core.kordoc_bridge import SUPPORTED_INPUT_EXTENSIONS, convert_to_hwpx
            if 확장자 in SUPPORTED_INPUT_EXTENSIONS - {".docx", ".pdf", ".hwp", ".hwpx"}:
                convert_to_hwpx(원본경로, 대상경로)
                return False
            if 확장자 in (".doc", ".docx", ".pdf"):
                with tempfile.TemporaryDirectory(prefix="docfit_변환_") as 임시폴더:
                    임시_md = Path(임시폴더) / f"{Path(원본경로).stem}.md"
                    parse_document(str(원본경로), str(임시_md), output_format="markdown", ocr=(확장자 == ".pdf"))
                    generate_hwpx(str(임시_md), "보고서", str(대상경로), image_dir=임시폴더)
                if 확장자 == ".pdf":
                    PDF_서식_이식(원본경로, 대상경로)
                return False
            raise ValueError(f"지원하지 않는 변환 형식입니다: {확장자}")
        return bind_function(외부문서_hwpx로_변환, _docfit_namespace)
    if _docfit_symbol == 'PDF_서식_이식':
        def PDF_서식_이식(원본경로, 대상경로):
            if not 알파_PDF서식이식_사용:
                return None
            try:
                from docfit_core.pdf_style_transfer import transfer_pdf_style
                통계 = transfer_pdf_style(원본경로, 대상경로)
                로그(f"[PDF 서식 이식] 글자 {통계['matched']}/{통계['pdf_chars']}개 짝지음, 글자 모양 {통계['new_char_shapes']}개·"
                     f"셀 배경 {통계['cells_filled']}칸 적용")
                return 통계
            except Exception as e:
                로그(f"[PDF 서식 이식] 건너뜀(kordoc 변환 결과 그대로 사용): {e}")
                return None
        return bind_function(PDF_서식_이식, _docfit_namespace)
    if _docfit_symbol == '_박스그림표_한글표_삽입':
        def _박스그림표_한글표_삽입(행들):
            """현재 커서 위치(빈 문단)에 행렬(rows)로 실제 한/글 표를 만든다.

            라벨 입력 모드의 '표:' 삽입(라벨블록_한글삽입/표넣기)과 같은 HTableCreation
            설정을 쓴다 — 단 너비 맞춤(WidthType 0)·자동 높이(HeightType 0)·글자처럼
            취급(TreatAsChar 1). 표 뒤 후속 서식 단계(표 머리글/본문 서식 등)가 그대로
            적용될 수 있도록 첫 행을 머리글로 가정한 별도 서식은 여기서 넣지 않는다.
            """
            열수 = max(len(행) for 행 in 행들)
            act = hwp.HAction
            pset = hwp.HParameterSet.HTableCreation
            act.GetDefault("TableCreate", pset.HSet)
            pset.Rows = len(행들)
            pset.Cols = 열수
            pset.WidthType = 0   # 단 너비에 맞춤(2는 임의 너비라 글자 폭만큼 좁아진다)
            pset.HeightType = 0  # 자동 높이
            pset.TableProperties.TreatAsChar = 1
            act.Execute("TableCreate", pset.HSet)
            칸들 = [칸 for 행 in 행들 for 칸 in (행 + [""] * (열수 - len(행)))]
            for 순번, 칸 in enumerate(칸들):
                if 칸:
                    텍스트_삽입(칸)
                if 순번 < len(칸들) - 1:
                    hwp_run("TableRightCell")
            hwp_run("Cancel")
        return bind_function(_박스그림표_한글표_삽입, _docfit_namespace)
    if _docfit_symbol == '_박스그림_줄인가':
        def _박스그림_줄인가(text):
            return bool(_박스그림_줄시작.match(text or ''))
        return bind_function(_박스그림_줄인가, _docfit_namespace)
    if _docfit_symbol == '_박스그림_남은_문단':
        def _박스그림_남은_문단(시작문단, 줄수):
            """시작문단부터 줄수만큼 본문 문단 가운데 선 문자 표 줄이 남은 첫 문단 번호. 없으면 None."""
            for 번호 in range(시작문단, 시작문단 + 줄수):
                try:
                    hwp.SetPos(0, 번호, 0)
                except Exception:
                    return None
                if tuple(hwp.GetPos()[:2]) != (0, 번호):
                    return None
                if _박스그림_줄인가(현재문단_텍스트()):
                    return 번호
            return None
        return bind_function(_박스그림_남은_문단, _docfit_namespace)
    if _docfit_symbol == '_박스그림표_교체':
        def _박스그림표_교체(시작문단, 끝문단, 행들):
            """문단 [시작문단, 끝문단](둘 다 본문, list id 0) 구간의 텍스트를 지우고
            그 자리에 실제 표를 삽입한다.

            2026-10-11 실측: 한/글 범위 선택이 실제로 잡히지 않았는데 실패를 돌려주지 않아, 원래 선 문자 줄 8개가 그대로
            남은 채 표만 들어간 결과가 있었다. 지운 뒤 선 문자 줄이 남았으면 문단 단위로 다시 지우고, 그래도 남으면 표를
            넣지 않고 예외로 알린다(부르는 곳이 원래 글을 그대로 두고 건너뛴다)."""
            줄수 = 끝문단 - 시작문단 + 1
            hwp.SetPos(0, 끝문단, 0)
            hwp_run('MoveParaEnd')
            끝위치 = hwp.GetPos()
            hwp.SetPos(0, 시작문단, 0)
            if hwp.SelectText(시작문단, 0, 끝위치[1], 끝위치[2]) is False:
                raise RuntimeError('박스 그림 표 범위 선택 실패')
            if hwp_run('Delete') is False:
                raise RuntimeError('박스 그림 표 텍스트 삭제 실패')
            hwp_run('Cancel')
            남은 = _박스그림_남은_문단(시작문단, 줄수)
            if 남은 is not None:
                로그(f"텍스트 표(박스 그림) 변환: 원래 줄이 지워지지 않아 문단 단위로 다시 지웁니다({남은 + 1}번째 문단).")
                for _ in range(줄수):
                    남은 = _박스그림_남은_문단(시작문단, 줄수)
                    if 남은 is None:
                        break
                    hwp.SetPos(0, 남은, 0)
                    hwp_run('MoveParaEnd')
                    문단끝 = hwp.GetPos()
                    다음 = (남은 + 1, 0) if 남은 < 시작문단 + 줄수 - 1 else (문단끝[1], 문단끝[2])
                    if hwp.SelectText(남은, 0, 다음[0], 다음[1]) is False or hwp_run('Delete') is False:
                        break
                    hwp_run('Cancel')
                if _박스그림_남은_문단(시작문단, 줄수) is not None:
                    raise RuntimeError('박스 그림 표의 원래 줄을 지우지 못해 표를 넣지 않음')
            hwp.SetPos(0, 시작문단, 0)
            _박스그림표_한글표_삽입(행들)
        return bind_function(_박스그림표_교체, _docfit_namespace)
    if _docfit_symbol == '박스그림_전체_적용':
        def 박스그림_전체_적용():
            """문서 본문에서 박스 그림(┌─┬─┐ 등)으로 그려진 표를 찾아 실제 한/글
            표로 바꾼다. AI 채팅 답변을 붙여넣을 때 흔히 딸려오는 형태다.

            본문(list id 0) 문단 텍스트를 먼저 전부 모아 docfit_core.text_table로
            블록을 찾은 뒤, 뒤에 있는 표부터 차례로 바꾼다(항목기호문장_사이_빈줄_삭제와
            같은 이유 — 뒤에서부터 바꿔야 앞쪽에서 찾아 둔 문단 번호가 바뀌지 않는다).
            """
            if 중단_요청됨():
                return False
            hwp_run('MoveDocBegin')
            문단텍스트들 = []
            while True:
                if 중단_요청됨():
                    return False
                문단텍스트들.append(현재문단_텍스트())
                hwp_run('MoveNextParaBegin')
                새위치 = hwp.GetPos()
                if 새위치[0] != 0 or 새위치[1] != len(문단텍스트들):
                    break

            매치들 = find_box_tables(문단텍스트들)
            if not 매치들:
                로그("텍스트 표(박스 그림) 변환: 대상 없음")
                hwp_run('MoveDocBegin')
                return True

            변환수 = 0
            for 시작, 끝, 행들 in reversed(매치들):
                if 중단_요청됨():
                    return False
                try:
                    _박스그림표_교체(시작, 끝, 행들)
                    변환수 += 1
                except Exception as e:
                    로그(f"텍스트 표(박스 그림) 변환 중 오류(건너뜀, {시작 + 1}~{끝 + 1}번째 문단): {e}")
                    # 선 문자 표가 글로 남았으므로 최종 검수에 알린다(예전에는 기록이 없어 점수에 반영되지 않았다).
                    검수_문제_기록(현재_처리파일, f"[박스 그림 표 변환 실패] {시작 + 1}~{끝 + 1}번째 문단: {e}")
                    try:
                        hwp_run('Cancel')
                    except Exception:
                        pass
            로그(f"텍스트 표(박스 그림) 변환 완료: {변환수}개")
            hwp_run('MoveDocBegin')
            return True
        return bind_function(박스그림_전체_적용, _docfit_namespace)
    if _docfit_symbol == '저장결과_규칙검수':
        def 저장결과_규칙검수(파일, 저장파일, 결과창=True):
            """저장 결과를 한 번 열어 선택된 읽기 전용 검사를 각각 독립 실행한다.

            결과창이 거짓이면(여러 문서 일괄 처리) 서식통일 결과 창을 띄우지 않는다. 결과는 로그와
            최종검수 보고서에 남는다.
            """
            결과 = {}
            검사들 = {}
            서식검수 = stage_enabled(선택_세부작업, 'style_unify', 작업_모드)
            if 서식검수:
                if not _서식통일_문서대표프로필:
                    결과['style_unify'] = {
                        'status': 'not_applicable', 'checked': 0, 'issues': [],
                        'reason': '항목기호 문장이 없어 대표 스타일이 없습니다(검사할 문장 없음).',
                    }
                else:
                    def 서식_검사():
                        if not 서식통일_빨간표시_사용:
                            # 표준서식이 뒤이어 기준을 정했으면 최종 대표값을 조사한다.
                            _서식통일_문서대표프로필.clear()
                        return 서식통일_전체_적용(
                            고정_프로필_재적용=서식통일_빨간표시_사용, 검증만=True)
                    검사들['style_unify'] = 서식_검사
                # 표만 있는 문서도 검수한다. 본문 대표값 유무·검사 실패와 독립이다.
                if 작업_모드 == 'unify' and stage_enabled(선택_세부작업, 'table_unify', 작업_모드):
                    검사들['table_unify'] = lambda: 서식통일_표_전체_적용(검증만=True)
            if 검수_사용:
                if 작업_모드 in ('format', 'all') and stage_enabled(선택_세부작업, 'page_group'):
                    검사들['page_group'] = 문단글_캐시_구간(보고서_페이지배치_최종검사)
                if 작업_모드 in ('spacing', 'all'):
                    if stage_enabled(선택_세부작업, 'word_check'):
                        검사들['word_check'] = 문단글_캐시_구간(보고서_단어분리_최종검사)
                    if stage_enabled(선택_세부작업, 'control_word_check'):
                        검사들['control_word_check'] = 문단글_캐시_구간(lambda: 보고서_단어분리_최종검사(컨트롤=True))
            if 중단_요청됨():
                return False
            if 검사들:
                try:
                    if 한글_문서_열기(hwp, 저장파일, 'HWPX', 'forceopen:true') is False:
                        raise RuntimeError('저장 결과 재열기 실패')
                except Exception as exc:
                    for key in 검사들:
                        결과[key] = {'status': 'error', 'checked': 0, 'issues': [], 'error': str(exc)}
                    검수_문제_기록(파일, f'[저장 결과 재열기 실패] {exc}')
                else:
                    기록_경계 = len(검수_문제목록)
                    for key, 검사 in 검사들.items():
                        if 중단_요청됨():
                            return False
                        try:
                            항목 = 검사()
                            if 항목 is False:
                                return False
                            결과[key] = 항목
                            로그(f"저장 결과 {key} 검수: {항목['status']} / 검사 {항목['checked']}건 / 오류 {len(항목['issues'])}건")
                            if key in ('style_unify', 'table_unify') and 항목['status'] not in ('passed', 'not_applicable'):
                                검수_문제_기록(파일, f"[저장 결과 {key} 검증 {항목['status']}] "
                                                     f"불일치 {len(항목['issues'])}개, "
                                                     f"판정 보류 그룹 {len(항목.get('not_checkable', []))}개")
                        except Exception as exc:
                            결과[key] = {'status': 'error', 'checked': 0, 'issues': [], 'error': str(exc)}
                            검수_문제_기록(파일, f'[최종 {key} 검사 실패] {exc}')
                            로그(f'저장 결과 {key} 검수 실패: {exc}')
                    완료된_검사 = {key for key, value in 결과.items()
                                if value.get('status') in ('passed', 'failed')}
                    대체수 = 처리중_기록_대체(파일, 완료된_검사, 기록_경계)
                    if 대체수:
                        로그(f"처리 중 미해결 기록 {대체수}건을 저장 결과 검사로 대체")
            if 서식검수:
                로그("[서식통일] 5/5 저장된 결과 읽기 전용 검수 종료")
                if 결과창:
                    _서식통일_최종결과_사용자확인(dict(결과['style_unify'], file=Path(파일).name))
            return 결과
        return bind_function(저장결과_규칙검수, _docfit_namespace)
    raise KeyError(_docfit_symbol)
