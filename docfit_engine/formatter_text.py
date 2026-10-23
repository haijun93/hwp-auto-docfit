"""괄호·라벨·글 규칙·변환·저장 후 검수 — formatter의 호환 전역으로 바인딩할 원본 정의."""

SYMBOLS = ('괄호_안쪽', '대괄호인가', '괄호_문두_라벨인가', '괄호_뒤_콜론인가', '세트후속_범위괄호_라벨인가', '문단_범위_선택', '선택범위_현재크기_pt', '괄호_축소량_pt', '대괄호_축소_제외', '괄호_텍스트_크기_축소_현재선택', '문두_라벨_굵게_제외_문단인가', '항목기호_키', '일관성_굵게_머리말_범위', '문두_라벨_굵게_선반영', '괄호_및_라벨_텍스트_문단_처리', '라벨괄호_계획', '라벨괄호_hwpx_처리', '표안_문단_구분', '공백규칙_글변환', '문장부호뒤공백_글변환', '글규칙_hwpx_처리', '현재문서_XML단계_적용', '괄호_텍스트_크기_축소_전체_적용', '텍스트_hwpx로_변환', '라벨블록_한글삽입', 'AI답변_개조식_변환', '텍스트_hwpx_단독변환', '외부문서_hwpx로_변환', 'PDF_서식_이식', '_박스그림표_한글표_삽입', '_박스그림_줄인가', '_박스그림_남은_문단', '_박스그림표_교체', '박스그림_전체_적용', '저장결과_규칙검수')

def _install(*, _docfit_namespace, _docfit_symbol, bind_function):
    global 괄호_안쪽, 대괄호인가, 괄호_문두_라벨인가, 괄호_뒤_콜론인가, 세트후속_범위괄호_라벨인가, 문단_범위_선택, 선택범위_현재크기_pt, 괄호_축소량_pt, 대괄호_축소_제외, 괄호_텍스트_크기_축소_현재선택, 문두_라벨_굵게_제외_문단인가, 항목기호_키, 일관성_굵게_머리말_범위, 문두_라벨_굵게_선반영, 괄호_및_라벨_텍스트_문단_처리, 라벨괄호_계획, 라벨괄호_hwpx_처리, 표안_문단_구분, 공백규칙_글변환, 문장부호뒤공백_글변환, 글규칙_hwpx_처리, 현재문서_XML단계_적용, 괄호_텍스트_크기_축소_전체_적용, 텍스트_hwpx로_변환, 라벨블록_한글삽입, AI답변_개조식_변환, 텍스트_hwpx_단독변환, 외부문서_hwpx로_변환, PDF_서식_이식, _박스그림표_한글표_삽입, _박스그림_줄인가, _박스그림_남은_문단, _박스그림표_교체, 박스그림_전체_적용, 저장결과_규칙검수
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
