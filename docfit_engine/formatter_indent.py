"""기호·본문 위치 측정과 내어쓰기/부연설명 정렬 — formatter의 호환 전역으로 바인딩할 원본 정의."""

SYMBOLS = ('텍스트_너비_em', '_문단_공백_건너뛰기', '복사_내어쓰기_규칙', '문단_내어쓰기_기준_오프셋', '_여는낫표_건너뛰기', '_문단_기호뒤_오프셋', '_문단_본문시작_오프셋', '문단_내어쓰기_적용_현재선택', '_반각전각_폭배수', '문단_선행부_폭_HWPUNIT', '_내어쓰기_값_설정', '_내어쓰기_여백쌍_설정', '내어쓰기_기호선택_허용', '재검사_대상인가', '재검사_영역인가', '문단_내어쓰기_전체_갱신', '_내어쓰기_한문단', '_붙임목록_내어쓰기_대상수집', '_붙임번호_기준위치_실측', '_붙임목록_번호_내어쓰기_적용', '문단_내어쓰기_적용', '_부모문단_유형', '_부연설명_문단인가', '_선행공백_길이', '_캐럿위치_폭_실측', '부연설명_앞빈칸_수', '_부연설명_앞빈칸_적용', '_부연설명_한문단', '부연설명_들여쓰기_전체_적용', '_별표_위치_실측', '_별표_정렬_적용', '_별표_한문단', '별표_정렬_전체_적용')

def _install(*, _docfit_namespace, _docfit_symbol, bind_function):
    global 텍스트_너비_em, _문단_공백_건너뛰기, 복사_내어쓰기_규칙, 문단_내어쓰기_기준_오프셋, _여는낫표_건너뛰기, _문단_기호뒤_오프셋, _문단_본문시작_오프셋, 문단_내어쓰기_적용_현재선택, _반각전각_폭배수, 문단_선행부_폭_HWPUNIT, _내어쓰기_값_설정, _내어쓰기_여백쌍_설정, 내어쓰기_기호선택_허용, 재검사_대상인가, 재검사_영역인가, 문단_내어쓰기_전체_갱신, _내어쓰기_한문단, _붙임목록_내어쓰기_대상수집, _붙임번호_기준위치_실측, _붙임목록_번호_내어쓰기_적용, 문단_내어쓰기_적용, _부모문단_유형, _부연설명_문단인가, _선행공백_길이, _캐럿위치_폭_실측, 부연설명_앞빈칸_수, _부연설명_앞빈칸_적용, _부연설명_한문단, 부연설명_들여쓰기_전체_적용, _별표_위치_실측, _별표_정렬_적용, _별표_한문단, 별표_정렬_전체_적용
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
    raise KeyError(_docfit_symbol)
