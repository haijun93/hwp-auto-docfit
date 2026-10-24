"""서식통일 표본·대표값·조사·적용 — formatter의 호환 전역으로 바인딩할 원본 정의."""

SYMBOLS = ('_서식통일_문두요소_범위', '_서식통일_글자모양', '_서식통일_공백제거', '_서식통일_HWPX_분석', '_서식통일_run_text', '_서식통일_XML문단', '_서식통일_위치텍스트', '_서식통일_음영값', '서식통일_표본', '_서식통일_그룹키', '_서식통일_현재_HWPX', '_서식통일_불일치_구간', '_서식통일_부연괄호_불일치_구간', '_서식통일_굵기_불일치_구간', '서식통일_대표', '_서식통일_표지인가', '_서식통일_제목표_표본', '_서식통일_체계경계', '_서식통일_참고표_이웃대표_보완', '_서식통일_대표값_사용자검토', '_서식통일_적용영역_사용자검토', '서식통일_결과창_반영', '_결과창_띄우는가', '_서식통일_최종결과_사용자확인', '_서식통일_미확정_항목', '_서식통일_미확정_빨간표시', '_서식통일_문단앞간격_적용', '_서식통일_내어쓰기_필요', '_서식통일_내어쓰기_상태', '_서식통일_문단서식_적용', '_서식통일_글자요소_적용', '_서식통일_색값', '_서식통일_색_적용', '_서식통일_문단내어쓰기_적용', '_서식통일_문단자간_조정', '_서식통일_글꼴크기만', '_서식통일_글꼴크기_대표', '_서식통일_XML_조사', '_서식통일_COM_조사', '서식통일_전체_적용', '서식통일_자간조정_반영', '서식통일_문장_마무리', '_서식통일_마무리_위치로', '서식통일_보류자간_재조정', '_서식통일_표모형', '서식통일_표_전체_적용')

def _install(*, _docfit_namespace, _docfit_symbol, bind_function):
    global _서식통일_문두요소_범위, _서식통일_글자모양, _서식통일_공백제거, _서식통일_HWPX_분석, _서식통일_run_text, _서식통일_XML문단, _서식통일_위치텍스트, _서식통일_음영값, 서식통일_표본, _서식통일_그룹키, _서식통일_현재_HWPX, _서식통일_불일치_구간, _서식통일_부연괄호_불일치_구간, _서식통일_굵기_불일치_구간, 서식통일_대표, _서식통일_표지인가, _서식통일_제목표_표본, _서식통일_체계경계, _서식통일_참고표_이웃대표_보완, _서식통일_대표값_사용자검토, _서식통일_적용영역_사용자검토, 서식통일_결과창_반영, _결과창_띄우는가, _서식통일_최종결과_사용자확인, _서식통일_미확정_항목, _서식통일_미확정_빨간표시, _서식통일_문단앞간격_적용, _서식통일_내어쓰기_필요, _서식통일_내어쓰기_상태, _서식통일_문단서식_적용, _서식통일_글자요소_적용, _서식통일_색값, _서식통일_색_적용, _서식통일_문단내어쓰기_적용, _서식통일_문단자간_조정, _서식통일_글꼴크기만, _서식통일_글꼴크기_대표, _서식통일_XML_조사, _서식통일_COM_조사, 서식통일_전체_적용, 서식통일_자간조정_반영, 서식통일_문장_마무리, _서식통일_마무리_위치로, 서식통일_보류자간_재조정, _서식통일_표모형, 서식통일_표_전체_적용
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
    raise KeyError(_docfit_symbol)
