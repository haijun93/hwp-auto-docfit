"""Extracted docfit_engine.page_fit definitions; installed into the compatibility session.

Original algorithms and comments are preserved. Runtime bindings are session-local;
see docfit_engine.runtime. This module does not import the application bootstrap.
"""
from docfit_engine.runtime import bind_function, bind_class

def _install(*, _docfit_namespace, _docfit_symbol):
    global 세트문장_선행들여쓰기_폭, 세트문장_후속문단인가, 세트문장_끝위치_찾기, 위치_페이지번호, 현재문단_줄간격_퍼센트, 항목기호_역할표, 보고서_문단역할, 보고서_본문묶음_수집, 보고서_단어분리_최종검사, 보고서_페이지배치_최종검사, 보고서_묶음_쪽별줄수, 쪽_본문줄수, 쪽첫줄_시작인가, 쪽보다_긴_묶음인가, 문서_쪽나누기_전체해제, 쪽나눔_설정, _묶음_쪽나눔_이동, 보고서_압축조건, 보고서_줄간격_보관, 보고서_줄간격_적용, 보고서_페이지보호_전체해제, 쪽맞춤_논리단위, 쪽맞춤_뒤로밀기인가, 보고서_소제목묶음_수집, 문단_첫줄_쪽, 소제목묶음_뒤_표인가, 소제목묶음_쪽맞춤_대상, _묶음_위간격_축소_당김, _묶음_같은쪽_이동, 소제목묶음_단위경계_앞쪽우선, 소제목묶음_같은쪽_시도, 본문_표_문단번호, 본문_쪽나눔_기억, 표_칸영역_범위, 표_쪽범위, 보고서_표묶음_수집, 표묶음_같은쪽_시도, 세트문장_같은쪽_시도, 로마자_중제목_표인가, 중제목_다음글문단, 쪽나눔_켜짐, 중제목_묶음_문단, 중제목_묶음_쪽, 중제목_외톨이_정리, 세트문장_같은쪽_전체_적용, 마지막쪽_화면줄수, 쪽맞춤_계측_시작, 쪽맞춤_계측_끝, 쪽맞춤_계측_더하기, 쪽맞춤_계측_복사, 쪽맞춤_계측_차이, 쪽맞춤_계측_단계문구, 쪽맞춤_계측_합계문구, 문단_위간격_pt_현재문단, 구조문단_간격_일괄조정, 구조문단_아래간격_일괄조정, 구조문단_간격_복원, 셀_세로여백_읽기, 셀_세로여백_현재선택, 표_셀_세로여백_일괄조정, _표_셀_대상_순회, 표_셀_세로여백_복원, 쪽맞춤_묶음분리_있음, 쪽맞춤_대상_조사, 쪽맞춤_레벨_적용, _보고서_페이지수_맞춤_고속, 보고서_페이지수_맞춤_시도, _보고서_페이지수_맞춤_시도_본체, _칸_문단글들, 제목표인가_현재, _한칸_제목표인가_현재, _기타_제목표인가_현재, _보고서_끝내용, 쪽맞춤_보고서_끝쪽, 쪽맞춤_보고서_목록, _쪽맞춤_줄간격_되돌리기, 보고서_1쪽_맞춤, 문단_화면줄수, 문단_자간_읽기, 문단_자간_적용, _문단_줄시작들, 문단_줄수_원본맞춤, 보고서_새쪽_시작인가, _대표_줄간격, 쪽맞춤_원본_보고서_기록, _보고서_내부_쪽나눔_해제, _문서유형별_쪽맞춤, _쪽맞춤_바꾼문단_단어분리_재검사, _문서유형별_쪽맞춤_본체, 보고서_페이지수_맞춤_전체_적용, 전체_찾아바꾸기, 괄호_안쪽_공백_정리_AllReplace, 괄호_안쪽_공백_정리_문단_처리, 쉼표_공백_보정_대상, 쉼표_공백_정리_문단_처리, _콜론_한글인가, 콜론_공백_보정_대상, 콜론_공백_정리_문단_처리, 쉼표_앞_공백_보정_대상, 쉼표_앞_공백_정리_문단_처리, _균등라벨_범위, 단어사이_연속공백_정리_대상, 단어사이_연속공백_정리_문단_처리, 문두_미음_기호_위치, 문두_미음_기호_정리, 연도_따옴표_정리_문단_처리, 곧은따옴표_통일_문단_처리, 작은따옴표_통일_문단_처리, 날짜_구분자_정리_문단_처리, 공문_띄어쓰기_정리_문단_처리, 공문_띄어쓰기_전체_적용, 문장내_공백_정규화_전체_적용, _문장내_공백_정규화_순회, 괄호_안쪽_공백_정리_전체_적용, 문장부호_뒤_공백_보정_문단_처리, 문장부호_뒤_공백_보정_전체_적용, 문단글_캐시_구간, _문단글_캐시_비우기, 현재문단_텍스트, _문단_위치표_계산, 문단_위치, _현재문단_텍스트_본체, _현재문단_텍스트_읽기, _현재문단_텍스트_읽기_상태, 실제_엔터_포함, 두_위치_사이_줄바꿈_문자인가, 문장부호_대상문장인가, 현재_화면줄_텍스트, 다음_줄_판정, 줄_목록_수집, 문장부호_줄병합_시도, _문장부호_줄병합_시도_본체, 본문_문장부호_처리, 현재_셀_주소_행번호, 현재_셀_행번호, 현재_한칸표인가, 현재_표_키, 표칸_묶음_수집, 표칸_묶음_키별, 한칸표_영역_목록, 디자인표_영역_목록, 디자인표_보호영역_갱신, _문서에_표_있음, _서식표_칸_확인, 표_헤더서식_현재셀_처리, 표_헤더서식_현재줄_처리, 표_헤더서식_표단위_처리, 서식표_영역_목록, 서식표_보호영역_조사, 표_헤더서식_전체_적용, 표_목록_수집, 셀_화면줄수, 셀_안쪽여백_읽기, 셀_안쪽여백_현재선택, 셀_안쪽여백_축소_시도
    if _docfit_symbol == '세트문장_선행들여쓰기_폭':
        def 세트문장_선행들여쓰기_폭(text):
            """문단 앞 공백의 상대 폭을 계산한다. 탭은 공백 4칸으로 본다."""
            if not text:
                return 0
            폭 = 0
            for ch in text:
                if ch == " ":
                    폭 += 1
                elif ch == "\t":
                    폭 += 4
                else:
                    break
            return 폭
        return bind_function(세트문장_선행들여쓰기_폭, _docfit_namespace)
    if _docfit_symbol == '세트문장_후속문단인가':
        def 세트문장_후속문단인가(상위_들여쓰기, text):
            """상위 문장부호 문단에 종속된 연속 설명 문단인지 판정한다.

            예) '     ※ ...' 다음의 '         (6~16번) ...'은 포함하지만,
                ' ㅇ ...', '   - ...', '□ ...'처럼 독립 구조 항목은 새 세트로 본다.
            """
            if not text or not text.strip():
                return False

            현재_들여쓰기 = 세트문장_선행들여쓰기_폭(text)
            if 현재_들여쓰기 <= 상위_들여쓰기:
                return False

            벗긴텍스트 = text.lstrip(" \t")
            if not 벗긴텍스트:
                return False

            # 공문서 구조 기호(□/ㅇ/-/※ 등)는 들여쓰기가 더 깊어도 별도 항목이다.
            if 벗긴텍스트[0] in 공문서_기호:
                return False

            # '1.', '(1)', '가.' 등 명시적 항목 번호 역시 별도 항목으로 본다.
            # '(6~16번)'처럼 범위 설명 라벨은 항목_패턴과 일치하지 않으므로 후속문단으로 유지된다.
            for pattern in 항목_패턴:
                if pattern.match(벗긴텍스트):
                    return False

            return True
        return bind_function(세트문장_후속문단인가, _docfit_namespace)
    if _docfit_symbol == '세트문장_끝위치_찾기':
        def 세트문장_끝위치_찾기(시작위치, 시작텍스트):
            """세트문장의 마지막 문단 끝 위치와 포함 문단 수를 반환한다."""
            원래위치 = hwp.GetPos()
            상위_들여쓰기 = 세트문장_선행들여쓰기_폭(시작텍스트)
            마지막끝 = 시작위치
            문단수 = 1

            try:
                hwp.SetPos(*시작위치)
                hwp_run("MoveParaEnd")
                마지막끝 = hwp.GetPos()

                hwp.SetPos(*시작위치)
                while True:
                    현재시작 = hwp.GetPos()
                    hwp_run("MoveNextParaBegin")
                    다음시작 = hwp.GetPos()
                    if 다음시작 == 현재시작 or 다음시작[0] != 시작위치[0]:
                        break

                    다음텍스트 = 현재문단_텍스트()
                    if not 세트문장_후속문단인가(상위_들여쓰기, 다음텍스트):
                        break

                    문단수 += 1
                    hwp_run("MoveParaEnd")
                    마지막끝 = hwp.GetPos()
                    hwp.SetPos(*다음시작)

                return 마지막끝, 문단수
            finally:
                try:
                    hwp.SetPos(*원래위치)
                except Exception:
                    pass
        return bind_function(세트문장_끝위치_찾기, _docfit_namespace)
    if _docfit_symbol == '위치_페이지번호':
        def 위치_페이지번호(pos):
            """지정 위치의 현재 인쇄 페이지 번호를 반환한다."""
            원래위치 = hwp.GetPos()
            try:
                hwp.SetPos(*pos)
                return 현재_페이지번호()
            finally:
                try:
                    hwp.SetPos(*원래위치)
                except Exception:
                    pass
        return bind_function(위치_페이지번호, _docfit_namespace)
    if _docfit_symbol == '현재문단_줄간격_퍼센트':
        def 현재문단_줄간격_퍼센트():
            """현재 문단의 줄간격 값을 읽는다. 읽지 못하면 None을 반환한다."""
            try:
                act = hwp.HAction
                pset = hwp.HParameterSet.HParaShape
                act.GetDefault("ParagraphShape", pset.HSet)
                값 = int(getattr(pset, "LineSpacing", 0) or 0)
                return 값 if 값 > 0 else None
            except Exception:
                return None
        return bind_function(현재문단_줄간격_퍼센트, _docfit_namespace)
    if _docfit_symbol == '항목기호_역할표':
        def 항목기호_역할표():
            """서식 프로필의 항목기호별 역할. 예전 프로필은 '항목기호_역할' 키로 저장했다(용어 변경, 2026-10-10)."""
            return 표준서식_설정.get("항목기호_역할") or 표준서식_설정.get("문두기호_역할") or {}
        return bind_function(항목기호_역할표, _docfit_namespace)
    if _docfit_symbol == '보고서_문단역할':
        def 보고서_문단역할(text):
            marker, role = leading_marker(text)
            role = 항목기호_역할표().get(marker, role)
            return role or None
        return bind_function(보고서_문단역할, _docfit_namespace)
    if _docfit_symbol == '보고서_본문묶음_수집':
        def 보고서_본문묶음_수집(시작위치):
            """본문과 직속 내용·부연설명을 묶고, 소제목은 첫 본문 묶음에 연결한다.

            ㅇ 다음의 - 항목들은 다음 ㅇ/□ 전까지 한 묶음이다. □는 첫 ㅇ 묶음까지만
            연결하므로 여러 ㅇ 묶음을 포함하는 안 전체를 한 쪽으로 강제하지 않는다.
            빈 문단이나 다른 역할·텍스트 영역은 묶음 경계다.
            """
            original = hwp.GetPos()
            try:
                hwp.SetPos(*시작위치)
                hwp_run('MoveParaBegin')
                start = hwp.GetPos()
                role = 보고서_문단역할(현재문단_텍스트())
                if role not in ('소제목', '본문', '내용', '부연설명'):
                    return []
                hwp_run('MoveParaEnd')
                result = [(start, hwp.GetPos(), role)]
                body_attached = role == '본문'
                while True:
                    if 중단_요청됨():
                        return []
                    hwp_run('MoveNextParaBegin')
                    next_start = hwp.GetPos()
                    if next_start[0] != start[0] or next_start[1] <= result[-1][0][1]:
                        break
                    next_role = 보고서_문단역할(현재문단_텍스트())
                    if role == '소제목' and not body_attached and next_role == '본문':
                        body_attached = True
                    elif next_role == '부연설명':
                        pass
                    elif body_attached and next_role == '내용':
                        pass
                    else:
                        break
                    hwp_run('MoveParaEnd')
                    result.append((next_start, hwp.GetPos(), next_role))
                return result
            finally:
                hwp.SetPos(*original)
        return bind_function(보고서_본문묶음_수집, _docfit_namespace)
    if _docfit_symbol == '보고서_단어분리_최종검사':
        def 보고서_단어분리_최종검사(컨트롤=False):
            """저장 후 화면줄 경계의 의미 단위 분리를 읽기 전용으로 검사한다."""
            original = hwp.GetPos()
            checked = 0
            issues = []
            # 줄 첫머리부터 넘치는 칸 폭보다 긴 단어는 문제 대신 적용 제외로 적는다.
            exempt = []
            areas = []
            try:
                if 컨트롤:
                    area = 2
                    while True:
                        if 중단_요청됨():
                            return False
                        hwp.SetPos(area, 0, 0)
                        if hwp.GetPos()[0] != area:
                            break
                        if ((not 쪽범위_사용중() or area in 쪽범위_컨트롤영역)
                                and not 표셀_자간_제외인가() and not 숫자_표칸인가()):
                            areas.append(area)
                        area += 1
                else:
                    areas = [0]
                for area in areas:
                    hwp.SetPos(area, 0, 0)
                    if area == 0:
                        순회_시작()
                    seen = set()
                    while True:
                        if 중단_요청됨():
                            return False
                        pos = tuple(hwp.GetPos())
                        if pos[0] != area or (area == 0 and 쪽범위_끝지남(pos)):
                            break
                        if pos in seen:
                            # 문단 앞 컨트롤 뒤 등에서 MoveLineEnd가 제자리로 돌아오면 같은
                            # 위치를 다시 밟는다. 검사 전체를 실패시키지 말고 다음 문단으로
                            # 넘어간다(실측: 보도자료 (0, 25, 9)에서 검사 중단).
                            진단로그(f'[단어 검수] 같은 위치 반복 {pos}: 다음 문단으로 넘어감')
                            hwp_run('MoveNextParaBegin')
                            moved = tuple(hwp.GetPos())
                            if moved in seen or moved[:2] == pos[:2]:
                                break
                            continue
                        seen.add(pos)
                        hwp_run('MoveLineEnd')
                        boundary = tuple(hwp.GetPos())
                        page = 현재_페이지번호()
                        hwp_run('MoveParaEnd')
                        end = tuple(hwp.GetPos())
                        if boundary[:2] != pos[:2] or end[:2] != pos[:2]:
                            raise RuntimeError(f'단어 검수 줄 경계 측정 실패: {pos}')
                        if boundary[2] < end[2]:
                            checked += 1
                            info = 단어모드_분리정보(pos)
                            if info and 칸폭보다_긴_단어인가(info):
                                단어모드_범위선택(info[2], info[3])
                                word = 현재선택영역_텍스트()
                                hwp_run('Cancel')
                                exempt.append({'text': f'[칸 폭보다 긴 단어] {word!r}',
                                               'page': page, 'position': pos})
                                hwp.SetPos(*pos)
                            elif info:
                                단어모드_범위선택(info[2], info[3])
                                word = 현재선택영역_텍스트()
                                hwp_run('Cancel')
                                message = f'[저장 결과 단어 분리] {word!r}'
                                issues.append({'text': message, 'page': page, 'position': pos})
                                hwp.SetPos(*pos)
                                검수_문제_기록(현재_처리파일, message)
                        hwp.SetPos(*boundary)
                        hwp_run('MoveNextChar')
                        if tuple(hwp.GetPos()) == boundary:
                            break
                return {'status': 'failed' if issues else 'passed', 'checked': checked,
                        'measurement': '화면줄 경계', 'areas': areas, 'issues': issues,
                        'exempt': exempt}
            finally:
                hwp_run('Cancel')
                hwp.SetPos(*original)
        return bind_function(보고서_단어분리_최종검사, _docfit_namespace)
    if _docfit_symbol == '보고서_페이지배치_최종검사':
        def 보고서_페이지배치_최종검사():
            """문서를 수정하지 않고 제목 고립과 문단 내부 쪽 분리를 검사한다."""
            original = hwp.GetPos()
            checked = 0
            issues = []
            # 한 쪽에 다 들어갈 수 없는 묶음은 규칙 위반이 아니라 적용 제외로 따로 적는다.
            exempt = []
            표문단 = 본문_표_문단번호()
            본문_쪽나눔_기억(표문단)
            _표칸영역.clear()
            try:
                순회_시작()
                while True:
                    if 중단_요청됨():
                        return False
                    pos = hwp.GetPos()
                    # 로마자 중제목 + □ + 첫 ㅇ 단위는 한 쪽에 있어야 한다(중제목_외톨이_정리).
                    if pos[0] == 0 and pos[1] in 표문단 and 로마자_중제목_표인가(표문단[pos[1]]):
                        다음 = 중제목_다음글문단(pos[1], 표문단)
                        묶음 = 중제목_묶음_문단(다음[0]) if 다음 else []
                        if 묶음 and all(쪽범위_안인가(p[0]) for p in 묶음):
                            counts, 표쪽 = 중제목_묶음_쪽({'표키': 표문단[pos[1]]}, 묶음)
                            if counts:
                                checked += 1
                                쪽들 = sorted(set(counts) | set(표쪽))
                                if len(쪽들) > 1:
                                    message = f'[중제목 묶음 쪽 분리] {다음[1].strip()[:60]}'
                                    issues.append({'text': message, 'pages': 쪽들, 'paragraph': pos[1]})
                                    검수_문제_기록(현재_처리파일, message)
                        hwp.SetPos(*pos)
                        if not 범위_다음_문단으로_진행():
                            break
                        continue
                    text = 현재문단_텍스트()
                    # 표 묶음: 제목 문장은 표가 시작하는 쪽에, 주석은 표가 끝나는 쪽에 있어야 한다.
                    표묶음 = (보고서_표묶음_수집(pos, 표문단)
                              if 보고서_문단역할(text) in ('소제목', '본문') else None)
                    if 표묶음 and all(쪽범위_안인가(p[0]) for p in 표묶음[0]):
                        lead, 표항목, notes, 표키 = 표묶음
                        lead_counts = 보고서_묶음_쪽별줄수(lead)
                        notes_counts = 보고서_묶음_쪽별줄수(notes) if notes else {}
                        표쪽 = 표_쪽범위(표키)
                        if lead_counts and 표쪽 and notes_counts is not None:
                            checked += 1
                            제목_홀로 = max(lead_counts) < 표쪽[0]
                            주석_홀로 = bool(notes_counts) and min(notes_counts) > 표쪽[1]
                            if 제목_홀로 or 주석_홀로:
                                message = (f'[표 묶음 쪽 분리] {text.strip()[:60]} '
                                           f'({"제목 문장" if 제목_홀로 else "주석"}이 표와 다른 쪽)')
                                issues.append({'text': message, 'pages': sorted(set(lead_counts) | set(표쪽)
                                                                                 | set(notes_counts)),
                                               'paragraph': pos[1]})
                                검수_문제_기록(현재_처리파일, message)
                        hwp.SetPos(*(notes or [표항목])[-1][0])
                        if not 범위_다음_문단으로_진행():
                            break
                        continue
                    # 논리단위 5개 이하 □ 묶음은 묶음 전체가 한 쪽에 있어야 한다.
                    group_target = (소제목묶음_쪽맞춤_대상(pos, 표문단)
                                    if 보고서_문단역할(text) == '소제목' else None)
                    if group_target and all(쪽범위_안인가(p[0]) for p in group_target[0]):
                        counts = 보고서_묶음_쪽별줄수(group_target[0])
                        if not counts:
                            raise RuntimeError('최종 페이지 검사의 화면줄 측정 실패')
                        checked += 1
                        if len(counts) > 1 and 쪽보다_긴_묶음인가(group_target[0], counts):
                            exempt.append({'text': f'[한 쪽보다 긴 묶음] {text.strip()[:80]}',
                                           'pages': sorted(counts), 'paragraph': pos[1]})
                        elif len(counts) > 1 and 소제목묶음_단위경계_앞쪽우선(*group_target):
                            exempt.append({'text': f'[ㅇ 단위 경계에서 나눈 소제목 묶음(앞쪽 단위가 많아 밀지 않음)] '
                                                   f'{text.strip()[:60]}', 'pages': sorted(counts), 'paragraph': pos[1]})
                        elif len(counts) > 1:
                            message = f'[소제목 묶음 쪽 분리] {text.strip()[:80]}'
                            issues.append({'text': message, 'pages': sorted(counts), 'paragraph': pos[1]})
                            검수_문제_기록(현재_처리파일, message)
                        hwp.SetPos(*pos)
                        if not 범위_다음_문단으로_진행():
                            break
                        continue
                    paragraphs = 보고서_본문묶음_수집(pos)
                    if paragraphs and all(쪽범위_안인가(p[0]) for p in paragraphs):
                        counts = 보고서_묶음_쪽별줄수(paragraphs)
                        if not counts:
                            raise RuntimeError('최종 페이지 검사의 화면줄 측정 실패')
                        checked += 1
                        if len(counts) > 1 and 쪽보다_긴_묶음인가(paragraphs, counts):
                            exempt.append({'text': f'[한 쪽보다 긴 묶음] {text.strip()[:80]}',
                                           'pages': sorted(counts), 'paragraph': pos[1]})
                        elif counts and len(counts) > 1:
                            kind = ('상위·하위 문단 묶음 분리' if len(paragraphs) > 1
                                    else '문단 내부 페이지 분리')
                            message = f'[{kind}] {text.strip()[:80]}'
                            issues.append({'text': message, 'pages': sorted(counts), 'paragraph': pos[1]})
                            검수_문제_기록(현재_처리파일, message)
                    hwp.SetPos(*pos)
                    if not 범위_다음_문단으로_진행():
                        break
                return {'status': 'passed' if not issues else 'failed',
                        'checked': checked, 'issues': issues, 'exempt': exempt}
            finally:
                hwp.SetPos(*original)
        return bind_function(보고서_페이지배치_최종검사, _docfit_namespace)
    if _docfit_symbol == '보고서_묶음_쪽별줄수':
        def 보고서_묶음_쪽별줄수(문단들):
            """문단 개수가 아닌 실제 배치된 화면줄을 페이지별로 센다."""
            original = hwp.GetPos()
            counts = {}
            try:
                for start, end, _ in 문단들:
                    hwp.SetPos(*start)
                    previous = None
                    while True:
                        if 중단_요청됨():
                            return None
                        hwp_run('MoveLineEnd')
                        line_end = hwp.GetPos()
                        if line_end[:2] != start[:2] or line_end == previous:
                            raise RuntimeError('묶음의 화면줄 위치 확인 실패')
                        page = 현재_페이지번호()
                        if page is None:
                            raise RuntimeError('묶음의 페이지 번호 확인 실패')
                        counts[page] = counts.get(page, 0) + 1
                        if line_end[2] >= end[2]:
                            break
                        previous = line_end
                        hwp_run('MoveNextChar')
                        if hwp.GetPos() == line_end:
                            raise RuntimeError('묶음의 다음 화면줄 이동 실패')
                return counts
            finally:
                hwp.SetPos(*original)
        return bind_function(보고서_묶음_쪽별줄수, _docfit_namespace)
    if _docfit_symbol == '쪽_본문줄수':
        def 쪽_본문줄수(위치):
            """위치가 있는 쪽의 본문 화면줄 수(그 쪽에 들어가는 줄 수의 근사값)."""
            original = hwp.GetPos()
            try:
                hwp.SetPos(*위치)
                page = 현재_페이지번호()
                hwp_run('MovePageBegin')
                count = 0
                while True:
                    if 중단_요청됨():
                        return None
                    hwp_run('MoveLineEnd')
                    line_end = hwp.GetPos()
                    if line_end[0] != 0 or 현재_페이지번호() != page:
                        break
                    count += 1
                    hwp_run('MoveNextChar')
                    if hwp.GetPos() == line_end:
                        break
                return count
            finally:
                hwp.SetPos(*original)
        return bind_function(쪽_본문줄수, _docfit_namespace)
    if _docfit_symbol == '쪽첫줄_시작인가':
        def 쪽첫줄_시작인가(시작위치):
            """묶음 첫 문단이 쪽의 첫 줄에서 시작하는지."""
            original = hwp.GetPos()
            try:
                hwp.SetPos(*시작위치)
                hwp_run('MovePageBegin')
                return tuple(hwp.GetPos()) == tuple(시작위치)
            finally:
                hwp.SetPos(*original)
        return bind_function(쪽첫줄_시작인가, _docfit_namespace)
    if _docfit_symbol == '쪽보다_긴_묶음인가':
        def 쪽보다_긴_묶음인가(문단들, counts):
            """한 쪽에 다 들어갈 수 없는 묶음이면 True. 쪽 배치 규칙을 적용하지 않는다.

            쪽 첫 줄에서 시작하는데도 쪽을 넘거나, 전체 줄 수가 앞쪽(꽉 찬 쪽)의 본문
            줄 수보다 많으면 어떤 배치로도 한 쪽에 모을 수 없다(실측: 34줄 묶음을
            줄간격으로 옮기려다 실패하고 미해결로 남음).
            """
            if not counts or len(counts) < 2:
                return False
            if 쪽첫줄_시작인가(문단들[0][0]):
                return True
            capacity = 쪽_본문줄수(문단들[0][0])
            return bool(capacity) and sum(counts.values()) > capacity
        return bind_function(쪽보다_긴_묶음인가, _docfit_namespace)
    if _docfit_symbol == '문서_쪽나누기_전체해제':
        def 문서_쪽나누기_전체해제(보존=()):
            """본문 문단의 '문단 앞 쪽 나눔'(쪽 나누기)을 모두 푼다(보존에 든 문단 번호는 둔다). 푼 개수(실패하면 None)."""
            if hwp is None:
                return 0
            원위치 = hwp.GetPos()
            해제 = 0
            try:
                번호 = 0
                while not 중단_요청됨():
                    try:
                        hwp.SetPos(0, 번호, 0)
                    except Exception:
                        break
                    if tuple(hwp.GetPos()[:2]) != (0, 번호):
                        break
                    act = hwp.CreateAction('ParagraphShape')
                    pset = act.CreateSet()
                    act.GetDefault(pset)
                    if 번호 not in 보존 and int(pset.Item('PagebreakBefore') or 0):
                        쪽나눔_설정((0, 번호, 0), False)
                        해제 += 1
                    번호 += 1
                return 해제
            except Exception as e:
                로그(f"쪽 나누기 해제 실패(무시): {e}")
                return None
            finally:
                try:
                    hwp_run('Cancel')
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
        return bind_function(문서_쪽나누기_전체해제, _docfit_namespace)
    if _docfit_symbol == '쪽나눔_설정':
        def 쪽나눔_설정(위치, 켜기):
            hwp.SetPos(*위치)
            act = hwp.CreateAction('ParagraphShape')
            pset = act.CreateSet()
            pset.SetItem('PagebreakBefore', 1 if 켜기 else 0)
            if act.Execute(pset) is False:
                raise RuntimeError('문단 앞 쪽 나눔 설정 실패')
        return bind_function(쪽나눔_설정, _docfit_namespace)
    if _docfit_symbol == '_묶음_쪽나눔_이동':
        def _묶음_쪽나눔_이동(시작위치, 문단들, counts, summary, 표키=None, 표까지만=False):
            """줄간격으로 옮기지 못한 묶음을 '문단 앞에서 쪽 나눔'으로 다음 쪽에 보낸다.

            앞쪽에 남은 줄이 한 쪽의 쪽나눔_최대_앞쪽비율 이하일 때만 한다(큰 빈 공간
            방지). 옮긴 뒤에도 쪽을 넘으면 되돌린다. 성공 True.
            표키를 주면 표 첫 칸도 같은 쪽이어야 하고, 표까지만=False면 표 끝까지 같은 쪽이어야 한다
            (한 쪽보다 긴 표는 제목 문장이 표 시작과 같은 쪽에 오기만 하면 된다).
            """
            if not 쪽나누기_사용:
                return False
            pages = sorted(counts)
            capacity = 쪽_본문줄수(시작위치)
            if not capacity or counts[pages[0]] > capacity * 쪽나눔_최대_앞쪽비율:
                return False
            original = hwp.GetPos()
            try:
                쪽나눔_설정(시작위치, True)
                new_counts = 보고서_묶음_쪽별줄수(문단들)
                표쪽 = 표_쪽범위(표키) if 표키 is not None else None
                같은쪽 = bool(new_counts) and len(new_counts) == 1
                if 같은쪽 and 표키 is not None:
                    쪽 = next(iter(new_counts))
                    같은쪽 = bool(표쪽) and 표쪽[0] == 쪽 and (표까지만 or 표쪽[1] == 쪽)
                if 같은쪽:
                    if 시작위치[0] == 0:
                        쪽배치_쪽나눔문단.add(시작위치[1])
                    로그(f'문장 묶음 쪽 나눔으로 다음 쪽 배치: {summary} '
                         f'(앞쪽 {counts[pages[0]]}줄/쪽당 약 {capacity}줄)')
                    return True
                쪽나눔_설정(시작위치, False)
                return False
            finally:
                hwp_run('Cancel')
                hwp.SetPos(*original)
        return bind_function(_묶음_쪽나눔_이동, _docfit_namespace)
    if _docfit_symbol == '보고서_압축조건':
        def 보고서_압축조건(counts):
            if not counts or len(counts) != 2:
                return False
            pages = sorted(counts)
            return pages[1] == pages[0] + 1 and counts[pages[0]] >= counts[pages[1]]
        return bind_function(보고서_압축조건, _docfit_namespace)
    if _docfit_symbol == '보고서_줄간격_보관':
        def 보고서_줄간격_보관(시작, 끝):
            """앞쪽 전체부터 묶음 끝까지 문단별 줄간격 형식/값을 보관한다.

            줄간격은 문단 속성이므로 페이지 경계에 걸친 문단은 문단 전체에
            적용된다. 포인트/고정값 등 비율 이외 줄간격은 변경하지 않는다.
            """
            result = []
            if 시작[0] != 끝[0]:
                raise RuntimeError('페이지와 묶음의 텍스트 영역이 다릅니다.')
            hwp.SetPos(*시작)
            hwp_run('MoveParaBegin')
            while True:
                if 중단_요청됨():
                    return None
                pos = hwp.GetPos()
                if pos[0] != 끝[0] or pos[1] > 끝[1]:
                    raise RuntimeError('압축 범위 문단 순회 실패')
                pset = hwp.HParameterSet.HParaShape
                hwp.HAction.GetDefault('ParagraphShape', pset.HSet)
                result.append((pos, int(pset.LineSpacingType), int(pset.LineSpacing)))
                if pos[1] == 끝[1]:
                    return result
                hwp_run('MoveNextParaBegin')
                if hwp.GetPos()[1] <= pos[1]:
                    raise RuntimeError('압축 범위의 다음 문단 이동 실패')
        return bind_function(보고서_줄간격_보관, _docfit_namespace)
    if _docfit_symbol == '보고서_줄간격_적용':
        def 보고서_줄간격_적용(보관, 단계, 확대=False):
            percent = hwp.LineSpacingMethod('Percent')
            changed = False
            for pos, kind, value in 보관:
                if kind != percent:
                    continue
                if 확대:
                    if value >= 세트문장_최대줄간격_퍼센트:
                        continue
                    target = min(세트문장_최대줄간격_퍼센트, value + 10 * 단계)
                else:
                    if value <= 세트문장_최소줄간격_퍼센트:
                        continue
                    target = max(세트문장_최소줄간격_퍼센트, value - 10 * 단계)
                hwp.SetPos(*pos)
                act = hwp.CreateAction('ParagraphShape')
                pset = act.CreateSet()
                pset.SetItem('LineSpacingType', kind)
                pset.SetItem('LineSpacing', target)
                if act.Execute(pset) is False:
                    raise RuntimeError('보고서 묶음 줄간격 적용 실패')
                if target != value:
                    changed = True
            return changed
        return bind_function(보고서_줄간격_적용, _docfit_namespace)
    if _docfit_symbol == '보고서_페이지보호_전체해제':
        def 보고서_페이지보호_전체해제():
            """작업 범위 안 문단의 '다음 문단과 함께'(KeepWithNext)를 해제한다.

            이어진 문단 묶음이 통째로 다음 쪽으로 밀리면 쪽 배치 판정이 틀어지므로 처리 전과 저장 직전에 푼다.
            한/글의 '문단 보호' 항목 이름은 KeepLinesTogether다(KeepLines는 없는 항목이라 읽으면 None,
            쓰면 무시된다 — 실측 2026-10-01). 문단 보호는 한 문단만 옮기므로 원문 설정을 그대로 둔다.
            """
            original = hwp.GetPos()
            changed = 0
            try:
                순회_시작()
                visited = set()
                while True:
                    if 중단_요청됨():
                        return False
                    hwp_run('MoveParaBegin')
                    pos = hwp.GetPos()
                    if 쪽범위_끝지남(pos):
                        break
                    if pos in visited:
                        break
                    visited.add(pos)
                    if pos[0] == 0 and 쪽범위_안인가(pos):
                        pset = hwp.HParameterSet.HParaShape
                        hwp.HAction.GetDefault('ParagraphShape', pset.HSet)
                        if int(getattr(pset, 'KeepWithNext', 0) or 0):
                            act = hwp.CreateAction('ParagraphShape')
                            clear_set = act.CreateSet()
                            clear_set.SetItem('KeepWithNext', 0)
                            if act.Execute(clear_set) is False:
                                raise RuntimeError('최종 문단 페이지 보호 해제 실패')
                            changed += 1
                    before = hwp.GetPos()
                    hwp_run('MoveNextParaBegin')
                    after = hwp.GetPos()
                    if after == before or after[0] != 0 or after[1] <= pos[1]:
                        break
                로그(f'최종 문단 페이지 보호 해제 완료 ({changed}개 문단)')
                return True
            finally:
                try:
                    hwp.SetPos(*original)
                except Exception:
                    pass
        return bind_function(보고서_페이지보호_전체해제, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_논리단위':
        def 쪽맞춤_논리단위(roles):
            """문단 역할 목록을 논리단위(문단 인덱스 목록)로 나눈다."""
            units = []
            for index, role in enumerate(roles):
                if role in ('소제목', '본문') or not units:
                    units.append([index])
                else:
                    units[-1].append(index)
            return units
        return bind_function(쪽맞춤_논리단위, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_뒤로밀기인가':
        def 쪽맞춤_뒤로밀기인가(unit_pages, pages):
            """논리단위 시작 쪽 목록으로 방향을 정한다. 뒤쪽 단위가 더 많을 때만 민다."""
            앞쪽 = sum(1 for page in unit_pages if page == pages[0])
            뒤쪽 = sum(1 for page in unit_pages if page == pages[1])
            return 앞쪽 < 뒤쪽, 앞쪽, 뒤쪽
        return bind_function(쪽맞춤_뒤로밀기인가, _docfit_namespace)
    if _docfit_symbol == '보고서_소제목묶음_수집':
        def 보고서_소제목묶음_수집(시작위치):
            """□ 문단부터 다음 □ 전까지의 ㅇ/-/* 문단을 모은다. □가 아니면 []."""
            original = hwp.GetPos()
            try:
                hwp.SetPos(*시작위치)
                hwp_run('MoveParaBegin')
                start = hwp.GetPos()
                if 보고서_문단역할(현재문단_텍스트()) != '소제목':
                    return []
                hwp_run('MoveParaEnd')
                result = [(start, hwp.GetPos(), '소제목')]
                while True:
                    if 중단_요청됨():
                        return []
                    hwp_run('MoveNextParaBegin')
                    next_start = hwp.GetPos()
                    if next_start[0] != start[0] or next_start[1] <= result[-1][0][1]:
                        break
                    next_role = 보고서_문단역할(현재문단_텍스트())
                    if next_role not in ('본문', '내용', '부연설명'):
                        break
                    hwp_run('MoveParaEnd')
                    result.append((next_start, hwp.GetPos(), next_role))
                return result
            finally:
                hwp.SetPos(*original)
        return bind_function(보고서_소제목묶음_수집, _docfit_namespace)
    if _docfit_symbol == '문단_첫줄_쪽':
        def 문단_첫줄_쪽(start):
            """문단 첫 화면줄이 놓인 쪽 번호."""
            original = hwp.GetPos()
            try:
                hwp.SetPos(*start)
                hwp_run('MoveLineEnd')
                return 현재_페이지번호()
            finally:
                hwp.SetPos(*original)
        return bind_function(문단_첫줄_쪽, _docfit_namespace)
    if _docfit_symbol == '소제목묶음_뒤_표인가':
        def 소제목묶음_뒤_표인가(group, 표문단):
            """□ 묶음 바로 뒤(빈 문단 하나 건너뛰어도 됨)에 마지막 ㅇ 단위의 표(로마자 중제목 표 제외)가 오는지."""
            if not 표문단 or not group:
                return False
            번호 = group[-1][0][1] + 1
            if 번호 not in 표문단:
                if 번호 + 1 not in 표문단:
                    return False
                original = hwp.GetPos()
                try:
                    hwp.SetPos(0, 번호, 0)
                    if tuple(hwp.GetPos()[:2]) != (0, 번호) or 현재문단_텍스트().strip():
                        return False
                except Exception:
                    return False
                finally:
                    hwp.SetPos(*original)
                번호 += 1
            return not 로마자_중제목_표인가(표문단[번호])
        return bind_function(소제목묶음_뒤_표인가, _docfit_namespace)
    if _docfit_symbol == '소제목묶음_쪽맞춤_대상':
        def 소제목묶음_쪽맞춤_대상(시작위치, 표문단=None):
            """(묶음, 논리단위) 또는 None. 논리단위가 최대 개수를 넘으면 None.

            마지막 ㅇ 단위 뒤에 표가 오면(그 ㅇ는 표의 제목 문장) 표까지 한 쪽에 모아야 하므로 묶음 전체 규칙을 쓰지 않고
            ㅇ 단위·표 묶음 배치에 맡긴다(None). 2026-10-04 실측: 서식 예시 'Ⅱ 추진 계획' 묶음을 1쪽으로 당기자
            'ㅇ (3단계)'만 1쪽, 그 표는 2쪽에 남음 — 사용자 기대는 1쪽에 'ㅇ (2단계)'까지, 2쪽에 'ㅇ (3단계)'와 표.
            """
            group = 보고서_소제목묶음_수집(시작위치)
            if not group:
                return None
            units = 쪽맞춤_논리단위([role for _, _, role in group])
            if len(units) > 쪽맞춤_묶음_최대단위:
                return None
            if 소제목묶음_뒤_표인가(group, 표문단):
                return None
            return group, units
        return bind_function(소제목묶음_쪽맞춤_대상, _docfit_namespace)
    if _docfit_symbol == '_묶음_위간격_축소_당김':
        def _묶음_위간격_축소_당김(보관, paragraphs, target_page, 표키, summary):
            """보관(쪽 시작~묶음 끝 문단) 문단의 문단 위 간격을 줄여 묶음을 target_page로 당긴다.

            성공 True(줄인 간격 유지), 실패 False(원래 간격 복원), 중단·오류 None.
            """
            원래 = []
            for pos, _, _ in 보관:
                hwp.SetPos(*pos)
                값 = 문단_위간격_pt_현재문단()
                if 값 and 값 > 0:
                    원래.append((pos, 값))
            if not 원래:
                return False

            def 적용(비율):
                for pos, 값 in 원래:
                    hwp.SetPos(*pos)
                    hwp_run('MoveParaBegin')
                    hwp_run('MoveSelParaEnd')
                    문단_위간격_적용_현재선택(round(값 * 비율, 1))
                    hwp_run('Cancel')

            단계수 = int(round(쪽맞춤_위간격_최대축소비율 * 10))
            for step in range(1, 단계수 + 1):
                if 중단_요청됨():
                    적용(1.0)
                    return None
                적용(1 - 0.1 * step)
                세트문장_통계['축소횟수'] = 세트문장_통계.get('축소횟수', 0) + 1
                new_counts = 보고서_묶음_쪽별줄수(paragraphs)
                if new_counts is None:
                    적용(1.0)
                    return None
                if set(new_counts) == {target_page} and (표키 is None or 표_쪽범위(표키) == (target_page, target_page)):
                    로그(f'문장 묶음 {target_page}쪽 배치 완료: {summary} (줄간격 최소라 문단 위 간격 {step * 10}% 축소)')
                    return True
            적용(1.0)
            진단로그(f'[문장 묶음] 문단 위 간격 {단계수 * 10}% 축소로도 당기지 못함 / {summary}')
            return False
        return bind_function(_묶음_위간격_축소_당김, _docfit_namespace)
    if _docfit_symbol == '_묶음_같은쪽_이동':
        def _묶음_같은쪽_이동(시작위치, paragraphs, counts, 먼저_확대, summary, 표키=None, 한방향=False):
            """묶음 전체를 두 쪽 중 한 쪽으로 옮긴다.

            먼저_확대로 정한 방향을 먼저 시도하고, 줄간격이 이미 한계값이라
            움직일 수 없거나 실패하면 반대 방향으로 보완한다(한방향=True면 보완하지 않음).
            표키를 주면 그 표의 첫 칸·마지막 칸도 목표 쪽에 있어야 성공이다(표 묶음).
            '성공', '실패'(원래 줄간격 복원), '건너뜀', 중단/오류는 None.
            """
            pages = sorted(counts)
            backup = None
            attempted = False
            success = False
            expand = False
            try:
                hwp.SetPos(*시작위치)
                hwp_run('MovePageBegin')
                page_start = hwp.GetPos()
                if 쪽범위_사용중() and not 쪽범위_안인가(page_start):
                    진단로그(f'[문장 묶음] 쪽 시작이 작업 쪽 범위 밖이라 건너뜀 / {summary}')
                    return '건너뜀'

                def 방향_시도(expand):
                    """성공 True, 실패 False(원래 줄간격 복원), 중단/오류 None."""
                    nonlocal backup, attempted, success
                    direction = "확대" if expand else "축소"
                    target_page = pages[1] if expand else pages[0]
                    진단로그(f'[문장 묶음] 쪽별 줄 수 {counts}: {direction}하여 {target_page}쪽으로 이동 / {summary}')
                    # 확대는 묶음 앞의 문단만 변경한다. 이동할 묶음 자체는 제외.
                    # 페이지 첫 문단에 묶음이 시작하면 확대할 앞부분이 없어 해결 불가.
                    backup = 보고서_줄간격_보관(
                        page_start, 시작위치 if expand else paragraphs[-1][1])
                    if backup is None:
                        return None
                    if expand:
                        backup = [item for item in backup if item[0][1] < 시작위치[1]]
                    # 처음 확정한 범위만 변경하며 재배치 후 유입된 문단은 포함하지 않는다.
                    for step in range(1, 세트문장_페이지줄간격_최대시도 + 1):
                        if 중단_요청됨():
                            return None
                        if not 보고서_줄간격_적용(backup, step, 확대=expand):
                            # 이미 최소/최대 줄간격이라 더 바꿀 수 없다.
                            break
                        attempted = True
                        count_key = '확대횟수' if expand else '축소횟수'
                        세트문장_통계[count_key] = 세트문장_통계.get(count_key, 0) + 1
                        new_counts = 보고서_묶음_쪽별줄수(paragraphs)
                        if new_counts is None:
                            return None
                        success = (set(new_counts) == {target_page}
                                   and (표키 is None or 표_쪽범위(표키) == (target_page, target_page)))
                        if success:
                            로그(f'문장 묶음 {target_page}쪽 배치 완료: {summary} (줄간격 {step}단계 {direction})')
                            return True
                    if not expand:
                        # 줄간격(최소 한계)으로 못 당기면 줄인 줄간격 위에 문단 위 간격을 더 줄여 본다.
                        당김 = _묶음_위간격_축소_당김(backup, paragraphs, target_page, 표키, summary)
                        if 당김 is None:
                            return None
                        if 당김:
                            success = True
                            return True
                    # 페이지 보호 속성은 최종 문서에 남기지 않는다. 줄간격 범위 안에서
                    # 해결되지 않으면 원래 값을 복원한다.
                    if attempted:
                        보고서_줄간격_적용(backup, 0, 확대=expand)
                        attempted = False
                    진단로그(f'[문장 묶음] {direction} 방향 줄간격 범위 내 이동 불가 / {summary}')
                    return False

                for expand in ((먼저_확대,) if 한방향 else (먼저_확대, not 먼저_확대)):
                    result = 방향_시도(expand)
                    if result is None:
                        return None
                    if result:
                        return '성공'
                return '실패'
            finally:
                try:
                    if attempted and not success:
                        # 단계 0은 혼합 줄간격을 문단마다 원래 값으로 돌린다.
                        보고서_줄간격_적용(backup, 0, 확대=expand)
                finally:
                    hwp_run('Cancel')
                    hwp.SetPos(*시작위치)
        return bind_function(_묶음_같은쪽_이동, _docfit_namespace)
    if _docfit_symbol == '소제목묶음_단위경계_앞쪽우선':
        def 소제목묶음_단위경계_앞쪽우선(group, units):
            """두 쪽에 걸친 □ 묶음이 ㅇ 단위 경계에서만 나뉘고 앞쪽 단위가 뒤쪽 이상인지(당기지 못해 단위별로 나눈 결과)."""
            쪽들 = []
            for unit in units:
                counts = 보고서_묶음_쪽별줄수([group[index] for index in unit])
                if not counts or len(counts) != 1:
                    return False
                쪽들.append(next(iter(counts)))
            pages = sorted(set(쪽들))
            # 앞쪽에 □와 ㅇ 단위가 하나 이상 함께 있어야 한다(□만 홀로 남은 것은 위반).
            return (len(pages) == 2 and 쪽들.count(pages[0]) >= 2
                    and 쪽들.count(pages[0]) >= 쪽들.count(pages[1]))
        return bind_function(소제목묶음_단위경계_앞쪽우선, _docfit_namespace)
    if _docfit_symbol == '소제목묶음_같은쪽_시도':
        def 소제목묶음_같은쪽_시도(시작위치, text, 머리=None, 표문단=None):
            """논리단위 5개 이하인 □ 묶음 전체를 한 쪽에 모은다.

            머리(로마자 중제목 {'위치', '표키'})를 주면 중제목 표도 묶음의 맨 앞(첫 단위)으로 보고, 줄간격·쪽 나눔은
            중제목부터 옮긴다(□ 앞에서 쪽을 나누면 중제목만 앞쪽에 남는다. 실측: 서식 예시 'Ⅱ 추진 계획').

            ('처리', 묶음): 이미 한 쪽이거나 옮겼음 — 묶음 안 문단은 다시 보지 않는다.
            ('단위별', 묶음): 대상이 아니거나 옮기지 못함 — ㅇ 단위별 처리로 넘긴다.
            None: 중단/오류.
            """
            summary = text.strip().replace('\r', ' ').replace('\n', ' ')[:50]
            target = 소제목묶음_쪽맞춤_대상(시작위치, 표문단)
            if target is None:
                return '단위별', []
            group, units = target
            if 쪽범위_사용중() and any(not 쪽범위_안인가(item[0]) for item in group):
                return '단위별', group
            counts = 보고서_묶음_쪽별줄수(group)
            if counts is None:
                return None
            이동시작, 표키, 표쪽 = 시작위치, None, None
            if 머리:
                표쪽 = 표_쪽범위(머리['표키'])
                if 표쪽:
                    이동시작, 표키 = 머리['위치'], 머리['표키']
                    for page in set(표쪽):      # 중제목 표는 한 줄로 센다
                        counts[page] = counts.get(page, 0) + 1
            pages = sorted(counts)
            if len(pages) == 1:
                return '처리', group
            if len(pages) != 2 or pages[1] != pages[0] + 1:
                return '단위별', group
            if 쪽보다_긴_묶음인가(group, counts):
                진단로그(f'[쪽 맞춤 묶음] 한 쪽보다 긴 묶음(총 {sum(counts.values())}줄): 묶음 규칙 제외, '
                         f'ㅇ 단위별 배치로 진행 / {summary}')
                return '단위별', group
            unit_pages = []
            for unit in units:
                page = 문단_첫줄_쪽(group[unit[0]][0])
                if page is None:
                    return '단위별', group
                unit_pages.append(page)
            # 앞쪽에 □와 함께 남은 ㅇ 단위 수(□만 앞쪽 끝에 홀로 있으면 0)
            앞쪽_ㅇ단위 = sum(1 for page in unit_pages[1:] if page == pages[0])
            if 표쪽 and 표쪽[0] < unit_pages[0]:
                unit_pages.insert(0, 표쪽[0])     # □ 앞쪽에 홀로 남은 중제목도 한 단위로 센다
            먼저_확대, 앞쪽, 뒤쪽 = 쪽맞춤_뒤로밀기인가(unit_pages, pages)
            세트문장_통계['대상'] += 1
            진단로그(f'[쪽 맞춤 묶음] 논리단위 {len(units)}개(앞쪽 {앞쪽}/뒤쪽 {뒤쪽}): '
                     f'{"뒤쪽으로 밈" if 먼저_확대 else "앞쪽으로 당김"} / {summary}')
            # 앞쪽 단위가 많아 당기기로 했고 앞쪽에 □와 ㅇ 단위가 함께 있으면 당기기만 한다. 줄간격이 이미 최소라
            # 못 당겨도 묶음 전체를 뒤쪽으로 밀지 않는다 — 앞쪽에 둔 중제목·□·ㅇ가 모두 다음 쪽으로 밀려나 앞쪽이
            # 크게 빈다(2026-10-04 사용자 지적: 서식 예시 'Ⅱ 추진 계획 … ㅇ (2단계)'가 1쪽에 있어야 하는데 2쪽으로
            # 밀림). 이때는 ㅇ 단위 경계에서 나뉘도록 단위별 배치로 넘긴다. □만 앞쪽에 남았으면 예전처럼 민다.
            당김만 = not 먼저_확대 and 앞쪽_ㅇ단위 >= 1
            result = _묶음_같은쪽_이동(이동시작, group, counts, 먼저_확대, summary, 표키=표키, 한방향=당김만)
            if result is None:
                return None
            if result == '성공':
                세트문장_통계['성공'] += 1
                return '처리', group
            if result == '실패' and 당김만:
                세트문장_통계['대상'] -= 1
                로그(f'[쪽 맞춤 묶음] 앞쪽 단위가 많은데 줄간격으로 당기지 못함 — 묶음을 밀지 않고 ㅇ 단위 경계에서 '
                     f'나누도록 단위별 배치로 진행: {summary}')
                return '단위별', group
            if result == '실패' and _묶음_쪽나눔_이동(이동시작, group, counts, summary, 표키=표키):
                세트문장_통계['성공'] += 1
                return '처리', group
            if result == '실패':
                세트문장_통계['실패'] += 1
                검수_문제_기록(현재_처리파일, f'[소제목 묶음 쪽 분리] {summary}')
                로그(f'소제목 묶음 배치 미해결(축소·확대 모두 불가) — ㅇ 단위별 배치로 진행: {summary}')
            return '단위별', group
        return bind_function(소제목묶음_같은쪽_시도, _docfit_namespace)
    if _docfit_symbol == '본문_표_문단번호':
        def 본문_표_문단번호():
            """{본문 문단 번호: 표 키(앵커 위치)}. 본문(리스트 0)에 놓인 표만."""
            result = {}
            try:
                ctrl = hwp.HeadCtrl
                남은수 = 100000   # 컨트롤 목록이 끝나지 않는 비정상 상황 방지
                while ctrl and 남은수 > 0:
                    남은수 -= 1
                    try:
                        if ctrl.CtrlID == 'tbl':
                            anchor = ctrl.GetAnchorPos(0)
                            if anchor.Item('List') == 0:
                                result[anchor.Item('Para')] = (0, anchor.Item('Para'), anchor.Item('Pos'))
                    except Exception:
                        pass
                    ctrl = ctrl.Next
            except Exception as e:
                진단로그(f'본문 표 위치 확인 실패(무시): {e}')
            return result
        return bind_function(본문_표_문단번호, _docfit_namespace)
    if _docfit_symbol == '본문_쪽나눔_기억':
        def 본문_쪽나눔_기억(표문단):
            """지금 문서에서 쪽 나눔으로 새 쪽을 시작하는 본문 문단 번호를 _쪽나눔문단에 기억한다.

            한/글 문단 모양에는 이 쪽 나눔이 보이지 않으므로(PagebreakBefore=0, 실측: 10월 확대간부회의
            자료) 지금 문서의 HWPX 원본에서 본문 직속 문단의 pageBreak를 읽는다. HWPX의 표 문단 번호가
            한/글의 본문 표 문단 번호와 다르면(저장 뒤 문단이 바뀜) 번호가 어긋나므로 쓰지 않는다.
            """
            _쪽나눔문단.clear()
            문서경로 = _서식통일_현재_HWPX()
            if 문서경로 is None or not 표문단:
                return
            try:
                from docfit_core.style_inventory import _sections
                문단들 = []
                with open_hwpx_safely(문서경로) as archive:
                    for name in _sections(archive):
                        문단들.extend(p for p in safe_xml_fromstring(archive.read(name)) if 제목_xml이름(p) == 'p')
            except Exception as e:
                진단로그(f'쪽 나눔 위치 확인 실패(무시): {e}')
                return
            표번호 = {i for i, p in enumerate(문단들)
                      if any(제목_xml이름(x) == 'tbl' for run in p if 제목_xml이름(run) == 'run' for x in run)}
            if 표번호 != set(표문단):
                진단로그('쪽 나눔 위치 확인 생략: 저장된 HWPX와 지금 문서의 표 위치가 다름')
                return
            _쪽나눔문단.update(i for i, p in enumerate(문단들) if p.get('pageBreak') == '1')
        return bind_function(본문_쪽나눔_기억, _docfit_namespace)
    if _docfit_symbol == '표_칸영역_범위':
        def 표_칸영역_범위(표키):
            """표 칸 목록 번호의 (처음, 끝). 처음 부를 때 문서의 표 칸을 한 번 훑어 기억한다."""
            if not _표칸영역:
                original = hwp.GetPos()
                try:
                    area = 2
                    while not 중단_요청됨():
                        try:
                            hwp.SetPos(area, 0, 0)
                        except Exception:
                            break
                        if hwp.GetPos()[0] != area:
                            break
                        키 = 현재_표_키()
                        if 키:
                            처음, 끝 = _표칸영역.get(키, (area, area))
                            _표칸영역[키] = (min(처음, area), max(끝, area))
                        area += 1
                finally:
                    hwp.SetPos(*original)
            return _표칸영역.get(tuple(표키)) if 표키 is not None else None
        return bind_function(표_칸영역_범위, _docfit_namespace)
    if _docfit_symbol == '표_쪽범위':
        def 표_쪽범위(표키):
            """표 첫 칸 시작과 마지막 칸 끝이 놓인 (첫 쪽, 끝 쪽). 모르면 None."""
            범위 = 표_칸영역_범위(표키)
            if not 범위:
                return None
            original = hwp.GetPos()
            try:
                hwp.SetPos(범위[0], 0, 0)
                첫쪽 = 현재_페이지번호()
                hwp.SetPos(범위[1], 0, 0)
                hwp_run('MoveListEnd')
                끝쪽 = 현재_페이지번호()
                return (첫쪽, 끝쪽) if 첫쪽 and 끝쪽 else None
            except Exception:
                return None
            finally:
                hwp.SetPos(*original)
        return bind_function(표_쪽범위, _docfit_namespace)
    if _docfit_symbol == '보고서_표묶음_수집':
        def 보고서_표묶음_수집(시작위치, 표문단):
            """(제목 문장 묶음, 표 문단 위치, 주석 문단들, 표 키) 또는 None.

            제목 문장 묶음(□ 또는 ㅇ와 딸린 -·*) 바로 뒤에 표가 오면 표와, 표 바로 뒤의
            부연설명(*, **, ※)까지 한 묶음이다. 사이의 빈 문단 하나는 묶음에 넣는다.
            """
            if not 표문단:
                return None
            lead = 보고서_본문묶음_수집(시작위치)
            if not lead:
                return None
            original = hwp.GetPos()

            def 문단(번호):
                """(시작, 끝, 글자) 또는 None."""
                try:
                    hwp.SetPos(0, 번호, 0)
                except Exception:
                    return None
                if tuple(hwp.GetPos()[:2]) != (0, 번호):
                    return None
                start = hwp.GetPos()
                text = 현재문단_텍스트()
                hwp.SetPos(*start)
                hwp_run('MoveParaEnd')
                return start, hwp.GetPos(), text

            try:
                번호 = lead[-1][0][1] + 1
                사이빈줄 = []
                if 번호 not in 표문단:
                    빈 = 문단(번호)
                    if not 빈 or 빈[2].strip() or 번호 + 1 not in 표문단:
                        return None
                    사이빈줄.append((빈[0], 빈[1], '빈 줄'))
                    번호 += 1
                # 쪽 나눔으로 새 쪽에서 시작하는 표(다음 보고서의 제목 표 등)는 앞 문장과 한 쪽에 놓일 수 없다.
                if any(n in _쪽나눔문단 for n in range(lead[-1][0][1] + 1, 번호 + 1)):
                    return None
                # 처리 중에 넣은 보고서 경계 쪽 나누기는 저장된 HWPX(_쪽나눔문단)에 없으므로 지금 문서에서도 본다.
                # 보고서 제목 표는 쪽 나눔이 없어도 앞 보고서 문장의 표가 아니다(2026-10-09 실측: 오판정 3건).
                if 번호 in 쪽맞춤_제목문단 or 쪽나눔_켜짐((0, 번호, 0)):
                    hwp.SetPos(*original)
                    return None
                표 = 문단(번호)
                if not 표 or 표[2].strip():
                    return None      # 표 옆에 글자가 있는 문단은 표 묶음으로 보지 않는다.
                if 로마자_중제목_표인가(표문단[번호]):
                    return None      # 로마자 중제목 표는 앞 문장의 표가 아니라 다음 □ 묶음의 머리다(중제목_외톨이_정리).
                표항목 = (표[0], 표[1], '표')
                notes = []
                다음 = 번호 + 1
                while not 중단_요청됨():
                    item = 문단(다음)
                    if not item:
                        break
                    role = 보고서_문단역할(item[2]) if item[2].strip() else None
                    if role == '부연설명':
                        notes.append((item[0], item[1], role))
                    elif not item[2].strip() and 다음 not in 표문단 and not notes:
                        뒤 = 문단(다음 + 1)
                        if not 뒤 or 보고서_문단역할(뒤[2]) != '부연설명':
                            break
                        notes.append((item[0], item[1], '빈 줄'))
                    else:
                        break
                    다음 += 1
                return lead + 사이빈줄, 표항목, notes, 표문단[번호]
            finally:
                hwp.SetPos(*original)
        return bind_function(보고서_표묶음_수집, _docfit_namespace)
    if _docfit_symbol == '표묶음_같은쪽_시도':
        def 표묶음_같은쪽_시도(시작위치, text, 표문단):
            """제목 문장 + 표 + 주석 묶음을 배치한다. 표 묶음이 아니면 None, 처리했으면 묶음 끝 위치,
            중단·오류면 False.

            - 묶음이 한 쪽에 들어가면 표가 시작하는 쪽에 모은다. 제목 문장만 앞쪽에 남았으면 뒤로 밀고
              (줄간격 확대 → 안 되면 제목 앞 쪽 나눔), 표는 앞쪽에 있고 주석만 넘쳤으면 앞으로 당긴다.
            - 표가 한 쪽보다 길면 표가 쪽을 넘는 것은 두되, 제목 문장이 표 시작과 다른 쪽에 홀로
              남지 않게 한다. 표가 앞쪽에서 시작했으면 앞쪽을 크게 비우는 쪽 나눔은 하지 않는다.
            """
            묶음 = 보고서_표묶음_수집(시작위치, 표문단)
            if 묶음 is None:
                return None
            lead, 표항목, notes, 표키 = 묶음
            끝위치 = (notes or [표항목])[-1][0]
            summary = text.strip().replace('\r', ' ').replace('\n', ' ')[:50]
            전체 = lead + [표항목] + notes
            if 쪽범위_사용중() and any(not 쪽범위_안인가(item[0]) for item in 전체):
                진단로그(f'[표 묶음] 작업 쪽 범위 밖으로 이어져 건너뜀 / {summary}')
                return 끝위치
            글문단 = lead + [item for item in notes if item[2] != '빈 줄']
            lead_counts = 보고서_묶음_쪽별줄수(lead)
            notes_counts = 보고서_묶음_쪽별줄수(notes) if notes else {}
            표쪽 = 표_쪽범위(표키)
            if lead_counts is None or notes_counts is None or not 표쪽:
                진단로그(f'[표 묶음] 쪽 측정 실패로 건너뜀 / {summary}')
                return 끝위치
            tf, tl = 표쪽
            쪽들 = set(lead_counts) | {tf, tl} | set(notes_counts)
            if len(쪽들) == 1:
                return 끝위치
            제목끝쪽 = max(lead_counts)
            세트문장_통계['대상'] += 1
            진단로그(f'[표 묶음] 제목 {sorted(lead_counts)}쪽 · 표 {tf}~{tl}쪽 · 주석 {sorted(notes_counts) or "-"}쪽 '
                     f'/ {summary}')
            앞쪽 = min(쪽들)
            결과 = '실패'
            if len(쪽들) == 2 and max(쪽들) == 앞쪽 + 1:
                counts = {앞쪽: 1, 앞쪽 + 1: 1}
                # 표가 앞쪽에서 시작해 끝나고 주석만 넘쳤으면 앞으로 당기고, 그 밖에는 뒤로 민다.
                당김 = tf == tl == 앞쪽 and notes_counts and min(notes_counts) > 앞쪽
                결과 = _묶음_같은쪽_이동(lead[0][0], 글문단, counts, not 당김, summary, 표키=표키,
                                     한방향=not 당김 and tf == 앞쪽)
                if 결과 is None:
                    return False
                if 결과 == '실패' and tf > 앞쪽:
                    # 제목 문장만 앞쪽 끝에 남은 경우: 제목 앞에서 쪽을 나눠 표와 함께 보낸다.
                    if _묶음_쪽나눔_이동(lead[0][0], 글문단, lead_counts, summary, 표키=표키):
                        결과 = '성공'
            if 결과 != '성공' and 제목끝쪽 < tf:
                # 한 쪽에 다 모으지 못해도 제목 문장이 표와 다른 쪽에 홀로 남지는 않게 한다.
                if _묶음_쪽나눔_이동(lead[0][0], lead, lead_counts, summary, 표키=표키, 표까지만=True):
                    로그(f'[표 묶음] 표보다 길어 한 쪽에 모으지 못함 — 제목 문장을 표 시작 쪽으로 옮김: {summary}')
                    결과 = '성공'
            if 결과 == '성공':
                세트문장_통계['성공'] += 1
            else:
                세트문장_통계['실패'] += 1
                검수_문제_기록(현재_처리파일, f'[표 묶음 쪽 분리] {summary} (제목 {sorted(lead_counts)}쪽, '
                                      f'표 {tf}~{tl}쪽, 주석 {sorted(notes_counts) or "-"}쪽)')
                로그(f'표 묶음 배치 미해결 — 원래 줄간격 유지: {summary}')
            return 끝위치
        return bind_function(표묶음_같은쪽_시도, _docfit_namespace)
    if _docfit_symbol == '세트문장_같은쪽_시도':
        def 세트문장_같은쪽_시도(시작위치, text):
            """문단 하나의 쪽별 줄 수를 비교해 앞쪽으로 당기거나 뒤쪽으로 민다."""
            if 중단_요청됨():
                return False
            if 보고서_문단역할(text) not in ('소제목', '본문', '내용', '부연설명'):
                return True
            summary = text.strip().replace('\r', ' ').replace('\n', ' ')[:50]
            paragraphs = 보고서_본문묶음_수집(시작위치)
            if not paragraphs:
                return not 중단_요청됨()
            if 쪽범위_사용중() and any(not 쪽범위_안인가(item[0]) for item in paragraphs):
                # 묶음이 작업 쪽 범위 밖까지 이어지면 범위 밖 문단의 줄간격을 건드리게 되므로 건너뛴다.
                진단로그(f'[문장 묶음] 작업 쪽 범위 밖으로 이어져 건너뜀 / {summary}')
                return not 중단_요청됨()
            counts = 보고서_묶음_쪽별줄수(paragraphs)
            pages = sorted(counts) if counts else []
            if len(pages) == 1:
                return not 중단_요청됨()
            if len(pages) != 2 or pages[1] != pages[0] + 1:
                진단로그(f'[문장 묶음] 인접한 두 쪽 조건 미충족: 쪽별 줄 수 {counts} / {summary}')
                if len(pages) > 1:
                    검수_문제_기록(현재_처리파일, f'[문장 묶음 페이지 분리] {summary}')
                return not 중단_요청됨()
            if 쪽보다_긴_묶음인가(paragraphs, counts):
                진단로그(f'[문장 묶음] 한 쪽보다 긴 묶음(총 {sum(counts.values())}줄): 쪽 배치 제외 / {summary}')
                return not 중단_요청됨()
            세트문장_통계['대상'] += 1
            # 쪽별 줄 수로 정한 방향을 먼저 시도하고, 안 되면 반대 방향으로 보완한다.
            # 예: 앞쪽 4줄/뒤쪽 1줄이지만 줄간격이 이미 최소(기본 140%)라 당길 수
            # 없으면, 앞 문단들의 줄간격을 넓혀 묶음 전체를 뒤쪽으로 민다.
            result = _묶음_같은쪽_이동(시작위치, paragraphs, counts,
                                     not 보고서_압축조건(counts), summary)
            if result is None:
                return False
            if result == '실패' and _묶음_쪽나눔_이동(시작위치, paragraphs, counts, summary):
                result = '성공'
            if result == '성공':
                세트문장_통계['성공'] += 1
            elif result == '실패':
                세트문장_통계['실패'] += 1
                검수_문제_기록(현재_처리파일, f'[문장 묶음 페이지 분리] {summary}')
                로그(f'문장 묶음 배치 미해결(축소·확대 모두 불가) — 원래 줄간격 복원: {summary}')
            return True
        return bind_function(세트문장_같은쪽_시도, _docfit_namespace)
    if _docfit_symbol == '로마자_중제목_표인가':
        def 로마자_중제목_표인가(표키):
            """본문 표가 1행 2~3칸이고 첫 칸 글이 로마자 번호(Ⅰ, Ⅱ …)뿐인 중제목 표인지."""
            범위 = 표_칸영역_범위(표키)
            if not 범위 or not 2 <= 범위[1] - 범위[0] + 1 <= 3:
                return False
            original = hwp.GetPos()
            try:
                hwp.SetPos(범위[0], 0, 0)
                if hwp.GetPos()[0] != 범위[0]:
                    return False
                return bool(_로마자_중제목_번호.match(현재문단_텍스트().strip()))
            except Exception:
                return False
            finally:
                hwp.SetPos(*original)
        return bind_function(로마자_중제목_표인가, _docfit_namespace)
    if _docfit_symbol == '중제목_다음글문단':
        def 중제목_다음글문단(표문단번호, 표문단):
            """중제목 표 뒤 첫 글 문단의 (시작 위치, 글). 사이 빈 문단은 건너뛰고, 표·끝이면 None."""
            original = hwp.GetPos()
            try:
                for 번호 in range(표문단번호 + 1, 표문단번호 + 4):
                    if 번호 in 표문단:
                        return None
                    try:
                        hwp.SetPos(0, 번호, 0)
                    except Exception:
                        return None
                    if tuple(hwp.GetPos()[:2]) != (0, 번호):
                        return None
                    start = hwp.GetPos()
                    text = 현재문단_텍스트()
                    if text.strip():
                        return start, text
                return None
            finally:
                hwp.SetPos(*original)
        return bind_function(중제목_다음글문단, _docfit_namespace)
    if _docfit_symbol == '쪽나눔_켜짐':
        def 쪽나눔_켜짐(위치):
            """위치 문단에 '문단 앞에서 쪽 나눔'이 켜져 있는지."""
            original = hwp.GetPos()
            try:
                hwp.SetPos(*위치)
                pset = hwp.HParameterSet.HParaShape
                hwp.HAction.GetDefault('ParagraphShape', pset.HSet)
                return bool(int(getattr(pset, 'PagebreakBefore', 0) or 0))
            except Exception:
                return False
            finally:
                hwp.SetPos(*original)
        return bind_function(쪽나눔_켜짐, _docfit_namespace)
    if _docfit_symbol == '중제목_묶음_문단':
        def 중제목_묶음_문단(다음위치):
            """중제목과 한 쪽에 있어야 하는 글 문단들: □ + 첫 ㅇ 단위(딸린 -·*). □가 아니면 그 문단의 묶음."""
            group = 보고서_소제목묶음_수집(다음위치)
            if group:
                units = 쪽맞춤_논리단위([role for _, _, role in group])
                return group[:units[min(1, len(units) - 1)][-1] + 1]
            return 보고서_본문묶음_수집(다음위치) or []
        return bind_function(중제목_묶음_문단, _docfit_namespace)
    if _docfit_symbol == '중제목_묶음_쪽':
        def 중제목_묶음_쪽(중제목, 문단들):
            """(묶음 글 문단의 쪽별 줄 수, 중제목 표 쪽 범위). 재지 못하면 (None, None)."""
            counts = 보고서_묶음_쪽별줄수(문단들) if 문단들 else None
            표쪽 = 표_쪽범위(중제목['표키'])
            return (counts, 표쪽) if counts and 표쪽 else (None, None)
        return bind_function(중제목_묶음_쪽, _docfit_namespace)
    if _docfit_symbol == '중제목_외톨이_정리':
        def 중제목_외톨이_정리(중제목):
            """중제목 + □ + 첫 ㅇ 단위가 두 쪽에 걸쳤으면 한 쪽에 모은다. 옮겼으면 True, 중단·오류는 None.

            소제목 묶음처럼 앞쪽 줄이 더 많으면 줄간격을 줄여 당기고, 아니면 앞 문단 줄간격을 넓혀 민다.
            안 되면 중제목 앞에서 쪽을 나눈다(뒤 □에 쪽 나눔이 있었으면 중제목으로 옮긴다).
            """
            문단들 = 중제목_묶음_문단(중제목['다음'])
            counts, 표쪽 = 중제목_묶음_쪽(중제목, 문단들)
            if counts is None:
                return False
            쪽들 = set(counts) | set(표쪽)
            if len(쪽들) == 1:
                return False
            if 쪽범위_사용중() and not all(쪽범위_안인가(item[0]) for item in [(중제목['위치'],)] + 문단들):
                return False
            summary = 중제목['요약']
            세트문장_통계['대상'] += 1
            앞쪽 = min(쪽들)
            original = hwp.GetPos()
            # 뒤 □가 이미 '문단 앞 쪽 나눔'으로 다음 쪽에 갔으면 그 쪽 나눔부터 푼다
            # (둘 다 켜면 □가 한 쪽 더 밀린다. 실측: 서식 예시 'Ⅱ 추진 계획').
            글쪽나눔 = 쪽나눔_켜짐(중제목['다음'])
            성공 = False
            try:
                if 글쪽나눔:
                    쪽나눔_설정(중제목['다음'], False)
                    hwp_run('Cancel')
                    counts, 표쪽 = 중제목_묶음_쪽(중제목, 문단들)
                    if counts is None:
                        return False
                    쪽들 = set(counts) | set(표쪽)
                    앞쪽 = min(쪽들)
                    성공 = len(쪽들) == 1
                if not 성공 and len(쪽들) == 2 and max(쪽들) == 앞쪽 + 1:
                    앞줄 = counts.get(앞쪽, 0) + (1 if 표쪽[0] == 앞쪽 else 0)
                    뒷줄 = counts.get(앞쪽 + 1, 0) + (1 if 표쪽[1] == 앞쪽 + 1 else 0)
                    결과 = _묶음_같은쪽_이동(중제목['위치'], 문단들, {앞쪽: 1, 앞쪽 + 1: 1}, 앞줄 < 뒷줄, summary,
                                         표키=중제목['표키'])
                    if 결과 is None:
                        return None
                    성공 = 결과 == '성공'
                    if not 성공:
                        성공 = _묶음_쪽나눔_이동(중제목['위치'], 문단들, {앞쪽: 앞줄, 앞쪽 + 1: 뒷줄}, summary,
                                             표키=중제목['표키'])
                if 성공:
                    세트문장_통계['성공'] += 1
                    로그(f'[중제목 쪽 배치] 중제목·□·첫 ㅇ 묶음을 한 쪽에 모음: {summary}')
                    return True
                if 글쪽나눔:
                    쪽나눔_설정(중제목['다음'], True)
                    hwp_run('Cancel')
                세트문장_통계['실패'] += 1
                검수_문제_기록(현재_처리파일, f'[중제목 묶음 쪽 분리] {summary}')
                return False
            finally:
                hwp.SetPos(*original)
        return bind_function(중제목_외톨이_정리, _docfit_namespace)
    if _docfit_symbol == '세트문장_같은쪽_전체_적용':
        def 세트문장_같은쪽_전체_적용():
            if not 세트문장_같은쪽_사용:
                return True
            if 중단_요청됨():
                return False

            로그("문장부호 세트문장 동일 페이지 유지 처리 시작")
            # 표 묶음(제목 문장 + 표 + 주석) 판정용: 본문에 놓인 표의 문단 번호. 표 칸 범위는 새로 잰다.
            표문단 = 본문_표_문단번호()
            본문_쪽나눔_기억(표문단)
            _표칸영역.clear()
            순회_시작()
            대기_중제목 = None      # 뒤 □ 묶음 배치가 끝나면 외톨이인지 볼 로마자 중제목
            중제목_머리 = {}         # □ 문단 번호 → 그 □의 머리인 로마자 중제목(□ 묶음 배치를 중제목부터 한다)

            while True:
                if 중단_요청됨():
                    return False

                시작위치 = hwp.GetPos()
                # 본문(리스트 0) 문단만 대상으로 한다. 표/글상자 등은 기존 컨트롤 처리와 충돌하지 않게 제외한다.
                if 시작위치[0] == 0 and 시작위치[1] in 표문단 and 로마자_중제목_표인가(표문단[시작위치[1]]):
                    다음 = 중제목_다음글문단(시작위치[1], 표문단)
                    묶음 = 중제목_묶음_문단(다음[0]) if 다음 else []
                    if 묶음:
                        대기_중제목 = {'위치': (0, 시작위치[1], 0), '표키': 표문단[시작위치[1]], '다음': 다음[0],
                                  '끝문단': 묶음[-1][0][1],
                                  '요약': 다음[1].strip().replace('\r', ' ').replace('\n', ' ')[:30]}
                        중제목_머리[다음[0][1]] = 대기_중제목
                elif 시작위치[0] == 0:
                    text = 현재문단_텍스트()
                    role = 보고서_문단역할(text)
                    처리됨 = False
                    if role in ('소제목', '본문'):
                        끝위치 = 표묶음_같은쪽_시도(시작위치, text, 표문단)
                        if 끝위치 is False:
                            return False
                        if 끝위치 is not None:
                            # 표 묶음 안의 문단(표·주석)은 다시 보지 않는다.
                            hwp.SetPos(*끝위치)
                            처리됨 = True
                    if not 처리됨 and role == '소제목':
                        result = 소제목묶음_같은쪽_시도(시작위치, text, 중제목_머리.get(시작위치[1]), 표문단)
                        if result is None:
                            return False
                        상태값, group = result
                        if 상태값 == '처리' and group:
                            # 묶음 전체가 한 쪽에 있으므로 안의 ㅇ 단위는 다시 보지 않는다.
                            hwp.SetPos(*group[-1][0])
                            처리됨 = True
                    if not 처리됨 and role in ('소제목', '본문', '내용', '부연설명'):
                        if 세트문장_같은쪽_시도(시작위치, text) is False:
                            return False
                        try:
                            hwp.SetPos(*시작위치)
                        except Exception:
                            pass
                    # □ 묶음과 첫 ㅇ 단위의 배치가 끝나면(묶음 끝 문단까지 왔으면) 중제목 묶음을 본다.
                    if 대기_중제목 and max(시작위치[1], hwp.GetPos()[1]) >= 대기_중제목['끝문단']:
                        중제목 = 대기_중제목
                        대기_중제목 = None
                        결과 = 중제목_외톨이_정리(중제목)
                        if 결과 is None:
                            return False
                        # 중제목을 옮기면 뒤 □ 묶음이 중제목 높이만큼 밀리므로 그 묶음을 한 번 더 배치한다.
                        if 결과:
                            hwp.SetPos(*중제목['다음'])
                            continue

                if not 범위_다음_문단으로_진행():
                    break

            로그(
                "문장부호 세트문장 동일 페이지 유지 완료 "
                f"(대상 {세트문장_통계['대상']} / 성공 {세트문장_통계['성공']} / "
                f"미해결 {세트문장_통계['실패']} / 줄간격 축소 {세트문장_통계['축소횟수']}회, 확대 {세트문장_통계.get('확대횟수', 0)}회)"
            )
            return True
        return bind_function(세트문장_같은쪽_전체_적용, _docfit_namespace)
    if _docfit_symbol == '마지막쪽_화면줄수':
        def 마지막쪽_화면줄수():
            """문서 끝이 있는 쪽 번호와, 그 쪽에 걸린 화면줄 수를 반환한다.

            실패하면 (None, None). 본문(리스트 0)만 대상으로 한다 — 표/글상자
            안 텍스트는 별도 리스트라 MovePageBegin 등 쪽 이동 명령이 기대한
            대로 동작하지 않는다.
            """
            if hwp is None:
                return None, None
            원위치 = hwp.GetPos()
            try:
                hwp_run('MoveDocEnd')
                문서끝 = hwp.GetPos()
                if 문서끝[0] != 0:
                    return None, None
                마지막쪽 = 현재_페이지번호()
                if 마지막쪽 is None:
                    return None, None
                hwp.SetPos(*문서끝)
                hwp_run('MovePageBegin')
                줄수 = 0
                이전줄끝 = None
                while True:
                    if 중단_요청됨():
                        return None, None
                    hwp_run('MoveLineEnd')
                    줄끝 = hwp.GetPos()
                    if 줄끝 == 이전줄끝:
                        break
                    줄수 += 1
                    if (줄끝[1], 줄끝[2]) >= (문서끝[1], 문서끝[2]):
                        break
                    이전줄끝 = 줄끝
                    hwp_run('MoveNextChar')
                    if hwp.GetPos() == 줄끝:
                        break
                return 마지막쪽, 줄수
            except Exception as e:
                로그(f"마지막 쪽 줄 수 확인 실패(무시): {e}")
                return None, None
            finally:
                try:
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
        return bind_function(마지막쪽_화면줄수, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_계측_시작':
        def 쪽맞춤_계측_시작():
            global 쪽맞춤_계측값
            쪽맞춤_계측값 = {}
        return bind_function(쪽맞춤_계측_시작, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_계측_끝':
        def 쪽맞춤_계측_끝():
            global 쪽맞춤_계측값
            값, 쪽맞춤_계측값 = 쪽맞춤_계측값, None
            return 값 or {}
        return bind_function(쪽맞춤_계측_끝, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_계측_더하기':
        def 쪽맞춤_계측_더하기(키, 초, 건수=0):
            if 쪽맞춤_계측값 is None:
                return
            누적 = 쪽맞춤_계측값.setdefault(키, [0.0, 0])
            누적[0] += 초
            누적[1] += 건수
        return bind_function(쪽맞춤_계측_더하기, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_계측_복사':
        def 쪽맞춤_계측_복사():
            return {키: list(v) for 키, v in (쪽맞춤_계측값 or {}).items()}
        return bind_function(쪽맞춤_계측_복사, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_계측_차이':
        def 쪽맞춤_계측_차이(이전):
            """이전 복사본 이후에 쌓인 (초, 건수)."""
            차이 = {}
            for 키, (초, 건수) in (쪽맞춤_계측값 or {}).items():
                앞초, 앞건수 = (이전 or {}).get(키, (0.0, 0))
                차이[키] = (초 - 앞초, 건수 - 앞건수)
            return 차이
        return bind_function(쪽맞춤_계측_차이, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_계측_단계문구':
        def 쪽맞춤_계측_단계문구(이름, 회, 차이, 단계초, 마지막쪽):
            초 = lambda k: 차이.get(k, (0.0, 0))[0]
            건 = lambda k: 차이.get(k, (0.0, 0))[1]
            표기타 = max(0.0, 초('표합계') - 초('표스캔') - 초('표셀읽기') - 초('표셀쓰기'))
            return (
                f"[쪽 수 맞춤 계측] {이름} {회}단계: "
                f"문단 간격 {초('문단합계'):.1f}초(순회 {초('문단순회'):.1f} + 쓰기 {초('문단쓰기'):.1f}, 훑은 문단 {건('문단순회')}개·바꾼 {건('문단쓰기')}곳) / "
                f"표 여백 {초('표합계'):.1f}초(표 스캔 {초('표스캔'):.1f} + 셀 읽기 {초('표셀읽기'):.1f} + 셀 쓰기 {초('표셀쓰기'):.1f} + 기타 {표기타:.1f}, "
                f"읽은 셀 {건('표셀읽기')}개·바꾼 {건('표셀쓰기')}개) / "
                f"쪽 측정 {초('쪽측정'):.1f}초 → 단계 합계 {단계초:.1f}초, 현재 {마지막쪽}쪽"
            )
        return bind_function(쪽맞춤_계측_단계문구, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_계측_합계문구':
        def 쪽맞춤_계측_합계문구(값, 전체초, 결과):
            # 고속 방식은 '문단합계'·'표합계'를 따로 재지 않으므로 세부 구간의 합으로 채운다.
            값 = dict(값)
            for 합계, 세부 in (('문단합계', ('문단순회', '문단쓰기')), ('표합계', ('표스캔', '표셀읽기', '표셀쓰기'))):
                세부합 = sum(값.get(k, (0.0, 0))[0] for k in 세부)
                if 값.get(합계, (0.0, 0))[0] < 세부합:
                    값[합계] = (세부합, 값.get(합계, (0.0, 0))[1])
            초 = lambda k: 값.get(k, (0.0, 0))[0]
            건 = lambda k: 값.get(k, (0.0, 0))[1]
            알려진 = sum(초(k) for k in ('문단합계', '표합계', '쪽측정', '묶음검사', '원복'))
            return (
                f"[쪽 수 맞춤 계측 합계] 총 {전체초:.1f}초, 결과 {'성공' if 결과 else '실패/원복'}, 쪽 측정 {건('쪽측정')}회 / "
                f"문단 간격 {초('문단합계'):.1f}초(순회 {초('문단순회'):.1f} + 쓰기 {초('문단쓰기'):.1f}) / "
                f"표 여백 {초('표합계'):.1f}초(스캔 {초('표스캔'):.1f} + 셀 읽기 {초('표셀읽기'):.1f} + 셀 쓰기 {초('표셀쓰기'):.1f}) / "
                f"쪽 측정 {초('쪽측정'):.1f}초 / 묶음 검사 {초('묶음검사'):.1f}초({건('묶음검사')}회) / "
                f"원복·재적용 {초('원복'):.1f}초 / 위에 없는 시간 {max(0.0, 전체초 - 알려진):.1f}초"
            )
        return bind_function(쪽맞춤_계측_합계문구, _docfit_namespace)
    if _docfit_symbol == '문단_위간격_pt_현재문단':
        def 문단_위간격_pt_현재문단():
            """현재 캐럿이 있는 문단의 '문단 위 간격' 값을 pt로 읽는다."""
            if hwp is None:
                return None
            try:
                return HwpUnit_pt(hwp.ParaShape.Item("PrevSpacing")) / 2      # COM은 실제 HWPUNIT의 두 배
            except Exception as e:
                로그(f"문단 위 간격 읽기 실패(무시): {e}")
                return None
        return bind_function(문단_위간격_pt_현재문단, _docfit_namespace)
    if _docfit_symbol == '구조문단_간격_일괄조정':
        def 구조문단_간격_일괄조정(delta_pt, 최소쪽=None, 위간격=False, 원래값=None):
            """문서 전체(본문 리스트만)에서 항목기호(□/ㅇ/-/*/※/• 등)로 시작하는
            문단의 '문단 아래 간격'(위간격이면 '문단 위 간격')을 delta_pt만큼
            조정한다(0pt 아래로는 내려가지 않음). 본문 줄간격은 건드리지 않는다.
            실제로 값이 바뀐 문단 수를 반환한다.

            원래값(dict)을 주면 처음 바꾸는 문단의 원래 pt를 (리스트, 문단) 번호로
            기록해 구조문단_간격_복원으로 되돌릴 수 있게 한다.

            최소쪽을 주면 그 이전 쪽의 문단은 손대지 않는다 — 페이지 수 맞춤은
            항상 마지막 몇 쪽만 조정하면 충분한데, 문단마다 현재문단_텍스트()를
            부르면 COM 왕복이 여러 번(약 8회) 드니, 저렴한 쪽 번호 확인(1회)을
            먼저 해서 대상이 아닌 문단은 비싼 텍스트 읽기 자체를 건너뛴다. 긴
            문서일수록 이 필터의 효과가 커진다.
            """
            if hwp is None or 중단_요청됨():
                return 0
            읽기 = 문단_위간격_pt_현재문단 if 위간격 else 문단_아래간격_pt_현재문단
            쓰기 = 문단_위간격_적용_현재선택 if 위간격 else 문단_아래간격_적용_현재선택
            원위치 = hwp.GetPos()
            순회_시작()
            적용수 = 0
            정체 = 0
            계측_시작 = time.perf_counter()
            계측_쓰기초 = 0.0
            계측_문단수 = 0
            try:
                while True:
                    if 중단_요청됨():
                        break
                    시작위치 = hwp.GetPos()
                    계측_문단수 += 1
                    if 시작위치[0] == 0 and not 현재_한칸표인가():
                        쪽번호 = 현재_페이지번호() if 최소쪽 is not None else None
                        if 최소쪽 is None or 쪽번호 is None or 쪽번호 >= 최소쪽:
                            text = 현재문단_텍스트()
                            if paragraph_level(text) is not None:
                                현재값 = 읽기()
                                if 현재값 is not None:
                                    새값 = max(0.0, round(현재값 + delta_pt, 1))
                                    if abs(새값 - 현재값) >= 0.05:
                                        if 원래값 is not None:
                                            원래값.setdefault(tuple(hwp.GetPos()[:2]), 현재값)
                                        계측_쓰기_시작 = time.perf_counter()
                                        hwp_run('MoveParaBegin')
                                        hwp_run('MoveSelParaEnd')
                                        쓰기(새값)
                                        hwp_run('Cancel')
                                        계측_쓰기초 += time.perf_counter() - 계측_쓰기_시작
                                        적용수 += 1
                    if not 범위_다음_문단으로_진행():
                        break
                    if hwp.GetPos() == 시작위치:
                        정체 += 1
                        if 정체 >= 2:
                            break
                    else:
                        정체 = 0
            finally:
                쪽맞춤_계측_더하기('문단쓰기', 계측_쓰기초, 적용수)
                쪽맞춤_계측_더하기('문단순회', time.perf_counter() - 계측_시작 - 계측_쓰기초, 계측_문단수)
                try:
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
            return 적용수
        return bind_function(구조문단_간격_일괄조정, _docfit_namespace)
    if _docfit_symbol == '구조문단_아래간격_일괄조정':
        def 구조문단_아래간격_일괄조정(delta_pt, 최소쪽=None):
            return 구조문단_간격_일괄조정(delta_pt, 최소쪽=최소쪽)
        return bind_function(구조문단_아래간격_일괄조정, _docfit_namespace)
    if _docfit_symbol == '구조문단_간격_복원':
        def 구조문단_간격_복원(원래값, 위간격=False):
            """구조문단_간격_일괄조정이 기록한 원래 간격으로 되돌린다."""
            if hwp is None or not 원래값:
                return 0
            쓰기 = 문단_위간격_적용_현재선택 if 위간격 else 문단_아래간격_적용_현재선택
            원위치 = hwp.GetPos()
            복원수 = 0
            try:
                for (list_id, para_id), 값 in 원래값.items():
                    try:
                        hwp.SetPos(list_id, para_id, 0)
                        hwp_run('MoveParaBegin')
                        hwp_run('MoveSelParaEnd')
                        쓰기(값)
                        hwp_run('Cancel')
                        복원수 += 1
                    except Exception as e:
                        로그(f"문단 간격 복원 실패(무시): {e}")
            finally:
                try:
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
            return 복원수
        return bind_function(구조문단_간격_복원, _docfit_namespace)
    if _docfit_symbol == '셀_세로여백_읽기':
        def 셀_세로여백_읽기():
            """캐럿이 있는 셀의 (셀 여백 사용 여부, 위, 아래) 원래 값(HWPUNIT). 실패 시 None."""
            if hwp is None:
                return None
            try:
                pset = hwp.HParameterSet.HShapeObject
                hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
                cell = pset.ShapeTableCell
                return int(cell.HasMargin), int(cell.MarginTop), int(cell.MarginBottom)
            except Exception as e:
                로그(f"셀 세로 여백 읽기 실패(무시): {e}")
                return None
        return bind_function(셀_세로여백_읽기, _docfit_namespace)
    if _docfit_symbol == '셀_세로여백_현재선택':
        def 셀_세로여백_현재선택(top_hwpunit=None, bottom_hwpunit=None, 원래값=None):
            """캐럿이 있는 셀의 상하 안쪽 여백을 HWPUNIT으로 설정한다(원래값을 주면 그 값으로 복원)."""
            if hwp is None:
                return False
            try:
                pset = hwp.HParameterSet.HShapeObject
                hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
                pset.HSet.SetItem("ShapeType", 3)
                pset.HSet.SetItem("ShapeCellSize", 0)
                if 원래값 is not None:
                    pset.ShapeTableCell.HasMargin = int(원래값[0])
                    pset.ShapeTableCell.MarginTop = int(원래값[1])
                    pset.ShapeTableCell.MarginBottom = int(원래값[2])
                else:
                    pset.ShapeTableCell.HasMargin = 1
                    if top_hwpunit is not None:
                        pset.ShapeTableCell.MarginTop = int(top_hwpunit)
                    if bottom_hwpunit is not None:
                        pset.ShapeTableCell.MarginBottom = int(bottom_hwpunit)
                return hwp.HAction.Execute("TablePropertyDialog", pset.HSet) is not False
            except Exception as e:
                로그(f"셀 세로 여백 적용 실패(무시): {e}")
                return False
        return bind_function(셀_세로여백_현재선택, _docfit_namespace)
    if _docfit_symbol == '표_셀_세로여백_일괄조정':
        def 표_셀_세로여백_일괄조정(스텝, 최소쪽=None, 원래값=None):
            """최소쪽 이후의 표를 대상으로 셀 세로 여백(위·아래)을 원래 여백에 비례하여
            스텝(1단계당 페이지맞춤_스텝_pt / 페이지맞춤_최대_pt 비율)만큼 축소한다.
            실제로 값이 바뀐 셀 수를 반환한다.

            원래값(dict)을 주면 처음 바꾸는 셀의 원래 여백(HasMargin, MarginTop, MarginBottom)을
            셀 area 번호로 기록해 표_셀_세로여백_복원으로 되돌릴 수 있게 한다.
            한 칸 표(제목·개요 상자)는 보호하여 건드리지 않는다.
            """
            if hwp is None or 중단_요청됨() or not 페이지맞춤_표셀세로여백_사용:
                return 0
            if not hasattr(hwp, 'HParameterSet'):
                return 0
            최대_pt = max(0.1, float(페이지맞춤_최대_pt))
            스텝_pt = max(0.1, float(페이지맞춤_스텝_pt))
            축소비율 = min(1.0, max(0.0, float(스텝) * (스텝_pt / 최대_pt)))
            최소_hwpunit = max(0, int(round(페이지맞춤_표셀세로여백_최소_pt * 100)))

            def 읽기_계측():
                시작 = time.perf_counter()
                값 = 셀_세로여백_읽기()
                쪽맞춤_계측_더하기('표셀읽기', time.perf_counter() - 시작, 1)
                return 값

            def 쓰기_계측(**kw):
                시작 = time.perf_counter()
                결과 = 셀_세로여백_현재선택(**kw)
                쪽맞춤_계측_더하기('표셀쓰기', time.perf_counter() - 시작, 1)
                return 결과

            적용수 = 0
            for area in _표_셀_대상_순회(최소쪽):
                현재 = 읽기_계측()
                if 현재 is None:
                    continue
                if 원래값 is not None:
                    원래값.setdefault(area, 현재)
                원래 = 원래값.get(area, 현재) if 원래값 is not None else 현재
                원래_has, 원래_top, 원래_bottom = 원래
                새_top = max(최소_hwpunit, int(round(원래_top * (1.0 - 축소비율))))
                새_bottom = max(최소_hwpunit, int(round(원래_bottom * (1.0 - 축소비율))))
                if abs(새_top - 현재[1]) >= 5 or abs(새_bottom - 현재[2]) >= 5:
                    if 쓰기_계측(top_hwpunit=새_top, bottom_hwpunit=새_bottom):
                        적용수 += 1
            return 적용수
        return bind_function(표_셀_세로여백_일괄조정, _docfit_namespace)
    if _docfit_symbol == '_표_셀_대상_순회':
        def _표_셀_대상_순회(최소쪽=None, 문단범위=None):
            """쪽 수 맞춤이 셀 세로 여백을 줄일 표 셀의 area를 차례로 내준다(캐럿은 그 셀에 둔다).

            최소쪽 이전 쪽의 표와 한 칸 표(제목·개요 상자)는 뺀다. 문단범위를 주면 그 본문 문단에 놓인 표만 본다.
            끝나면 캐럿을 원래 자리로 돌린다.
            """
            def 범위안(키):
                return 문단범위 is None or (bool(키) and 키[0] == 0 and 키[1] in 문단범위)

            원위치 = None
            try:
                원위치 = hwp.GetPos()
            except Exception:
                pass

            계측_스캔시작 = time.perf_counter()
            캐시 = _쪽맞춤_표캐시
            if 캐시 is not None and '묶음' in 캐시:
                한칸영역, 묶음 = 캐시['한칸'], 캐시['묶음']
            else:
                한칸영역 = set()
                try:
                    목록 = 한칸표_영역_목록()
                    if 목록:
                        한칸영역 = set(목록)
                except Exception:
                    pass
                try:
                    묶음 = 표칸_묶음_키별()
                except Exception:
                    묶음 = None
                if 캐시 is not None:
                    캐시.update(한칸=한칸영역, 묶음=묶음)

            try:
                쪽맞춤_계측_더하기('표스캔', time.perf_counter() - 계측_스캔시작)

                if 묶음 is not None:
                    for 키, 칸들 in 묶음.items():
                        if 중단_요청됨():
                            break
                        if not 칸들:
                            continue
                        if len(칸들) == 1 and 칸들[0][1] == "A1":
                            continue
                        if 칸들[0][0] in 한칸영역 or not 범위안(키):
                            continue
                        첫칸 = 칸들[0][0]
                        try:
                            hwp.SetPos(첫칸, 0, 0)
                        except Exception:
                            continue
                        쪽 = 현재_페이지번호() if 최소쪽 is not None else None
                        if 최소쪽 is not None and 쪽 is not None and 쪽 < 최소쪽:
                            continue
                        for area, 주소, 행 in 칸들:
                            if 중단_요청됨():
                                break
                            try:
                                hwp.SetPos(area, 0, 0)
                            except Exception:
                                continue
                            yield area
                else:
                    area = 1
                    while True:
                        if 중단_요청됨():
                            break
                        area += 1
                        try:
                            hwp.SetPos(area, 0, 0)
                        except Exception:
                            break
                        try:
                            pos = hwp.GetPos()
                            if pos[0] != area:
                                break
                        except Exception:
                            break
                        if area in 한칸영역 or not 범위안(현재_표_키()):
                            continue
                        쪽 = 현재_페이지번호() if 최소쪽 is not None else None
                        if 최소쪽 is not None and 쪽 is not None and 쪽 < 최소쪽:
                            continue
                        yield area
            finally:
                if 원위치 is not None:
                    try:
                        hwp.SetPos(*원위치)
                    except Exception:
                        pass
        return bind_function(_표_셀_대상_순회, _docfit_namespace)
    if _docfit_symbol == '표_셀_세로여백_복원':
        def 표_셀_세로여백_복원(원래값):
            """표_셀_세로여백_일괄조정이 기록한 원래 여백으로 되돌린다."""
            if hwp is None or not 원래값:
                return 0
            원위치 = None
            try:
                원위치 = hwp.GetPos()
            except Exception:
                pass
            복원수 = 0
            try:
                for area, 값 in 원래값.items():
                    try:
                        hwp.SetPos(area, 0, 0)
                        if 셀_세로여백_현재선택(원래값=값):
                            복원수 += 1
                    except Exception as e:
                        로그(f"셀 세로 여백 복원 실패(무시): {e}")
            finally:
                if 원위치 is not None:
                    try:
                        hwp.SetPos(*원위치)
                    except Exception:
                        pass
            return 복원수
        return bind_function(표_셀_세로여백_복원, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_묶음분리_있음':
        def 쪽맞춤_묶음분리_있음(최소쪽=None, 최대쪽=None):
            """쪽 배치 규칙을 어기고 쪽 경계에 걸린 묶음이 있는지 읽기 전용으로 본다.

            최종 쪽 배치 검사와 같은 기준이다: 논리단위 5개 이하 □ 묶음은 묶음
            전체, 그 밖에는 ㅇ 단위(ㅇ와 -·*)와 □+첫 ㅇ 단위. 처음 발견하면 멈춘다.

            최소쪽을 주면 (최소쪽-1)쪽보다 앞에서 시작하는 묶음은 보지 않는다.
            페이지 수 맞춤은 최소쪽부터만 간격을 바꾸므로 그 앞의 쪽 나눔은 그대로다.
            앞쪽에 원래부터 풀 수 없는 긴 묶음이 걸려 있으면 매 단계 '걸림'으로 판정돼
            헛되이 더 줄였다(실측: 10쪽 회의자료에서 단계마다 약 30초).

            로마자 중제목 + □ + 첫 ㅇ 단위 묶음도 본다(2026-10-04 실측: 서식 예시에서 쪽 수 맞춤이 2쪽부터 문단 위
            간격을 줄여 'Ⅱ 추진 계획 · □ · ㅇ (1단계)'만 1쪽으로 올라오고 '- 입자가속기 …'는 2쪽에 남음).
            ㅇ 단위 경계에서 나뉘고 앞쪽 단위가 많은 □ 묶음은 쪽 배치가 일부러 그렇게 둔 것이라 걸림으로 보지 않는다.
            """
            original = hwp.GetPos()
            표문단 = 본문_표_문단번호()
            try:
                순회_시작()
                while True:
                    if 중단_요청됨():
                        return False
                    pos = hwp.GetPos()
                    쪽 = 현재_페이지번호() if ((최소쪽 or 최대쪽) and pos[0] == 0) else None
                    if 최대쪽 and 쪽 and 쪽 > 최대쪽:
                        return False
                    최소쪽 = 최소쪽 or 1
                    if (pos[0] == 0 and (쪽 is None or 쪽 >= 최소쪽 - 1) and pos[1] in 표문단
                            and 로마자_중제목_표인가(표문단[pos[1]])):
                        다음 = 중제목_다음글문단(pos[1], 표문단)
                        묶음 = 중제목_묶음_문단(다음[0]) if 다음 else []
                        if 묶음 and all(쪽범위_안인가(p[0]) for p in 묶음):
                            counts, 표쪽 = 중제목_묶음_쪽({'표키': 표문단[pos[1]]}, 묶음)
                            if counts and len(set(counts) | set(표쪽)) > 1:
                                진단로그(f'[쪽 수 맞춤] 쪽 경계에 걸린 중제목 묶음: {다음[1].strip()[:40]}')
                                return True
                        hwp.SetPos(*pos)
                    elif pos[0] == 0 and (쪽 is None or 쪽 >= 최소쪽 - 1):
                        text = 현재문단_텍스트()
                        role = 보고서_문단역할(text)
                        if role in ('소제목', '본문', '내용', '부연설명'):
                            target = 소제목묶음_쪽맞춤_대상(pos, 표문단) if role == '소제목' else None
                            paragraphs = target[0] if target else 보고서_본문묶음_수집(pos)
                            if paragraphs and all(쪽범위_안인가(p[0]) for p in paragraphs):
                                counts = 보고서_묶음_쪽별줄수(paragraphs)
                                if (counts and len(counts) > 1
                                        and not 쪽보다_긴_묶음인가(paragraphs, counts)
                                        and not (target and 소제목묶음_단위경계_앞쪽우선(*target))):
                                    진단로그(f'[쪽 수 맞춤] 쪽 경계에 걸린 묶음: {text.strip()[:40]}')
                                    return True
                        hwp.SetPos(*pos)
                    if not 범위_다음_문단으로_진행():
                        return False
            finally:
                hwp.SetPos(*original)
        return bind_function(쪽맞춤_묶음분리_있음, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_대상_조사':
        def 쪽맞춤_대상_조사(최소쪽, 문단범위=None):
            """쪽 수 맞춤이 바꿀 문단·표 셀과 원래 값을 한 번만 모은다(값은 바꾸지 않는다).

            문단: {(list_id, para_id): [원래 아래 pt, 원래 위 pt]}, 셀: {area: (HasMargin, 위, 아래)}.
            """
            문단 = {}
            원위치 = hwp.GetPos()
            # 보고서 범위가 있으면 그 첫 문단부터 보고 범위를 지나면 멈춘다(예전에는 보고서마다 문서 전체를 처음부터 훑었다).
            try:
                if 문단범위 is None:
                    raise ValueError
                hwp.SetPos(0, 문단범위.start, 0)
                if tuple(hwp.GetPos()[:2]) != (0, 문단범위.start):
                    raise ValueError
            except Exception:
                순회_시작()
            시작 = time.perf_counter()
            훑은수 = 0
            정체 = 0
            try:
                while not 중단_요청됨():
                    시작위치 = hwp.GetPos()
                    if 문단범위 is not None and 시작위치[0] == 0 and 시작위치[1] >= 문단범위.stop:
                        break
                    훑은수 += 1
                    if (시작위치[0] == 0 and (문단범위 is None or 시작위치[1] in 문단범위)
                            and not 현재_한칸표인가()):
                        쪽번호 = 현재_페이지번호()
                        if 쪽번호 is None or 쪽번호 >= 최소쪽:
                            if paragraph_level(현재문단_텍스트()) is not None:
                                아래, 위 = 문단_아래간격_pt_현재문단(), 문단_위간격_pt_현재문단()
                                if 아래 is not None and 위 is not None:
                                    문단[tuple(hwp.GetPos()[:2])] = [아래, 위]
                    if not 범위_다음_문단으로_진행():
                        break
                    if hwp.GetPos() == 시작위치:
                        정체 += 1
                        if 정체 >= 2:
                            break
                    else:
                        정체 = 0
            finally:
                쪽맞춤_계측_더하기('문단순회', time.perf_counter() - 시작, 훑은수)
                try:
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
            셀 = {}
            if 페이지맞춤_표셀세로여백_사용 and hasattr(hwp, 'HParameterSet'):
                for area in _표_셀_대상_순회(최소쪽, 문단범위):
                    시작 = time.perf_counter()
                    값 = 셀_세로여백_읽기()
                    쪽맞춤_계측_더하기('표셀읽기', time.perf_counter() - 시작, 1)
                    if 값 is not None:
                        셀.setdefault(area, 값)
            return {'문단': 문단, '셀': 셀, '문단현재': {k: list(v) for k, v in 문단.items()}, '셀현재': dict(셀)}
        return bind_function(쪽맞춤_대상_조사, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_레벨_적용':
        def 쪽맞춤_레벨_적용(조사, 레벨, 위간격_0=False):
            """조사한 문단·셀을 레벨만큼 줄인 절대값으로 맞춘다(레벨 0은 원래 값). 바뀐 곳만 쓴다.

            위간격_0이면 문단 위 간격을 모두 0pt로 한다(1쪽 보고서 맞춤의 마지막 수단).
            """
            아래줄임, 위줄임, 비율 = 쪽맞춤_레벨_줄임량(
                레벨, half=max(1, int(round(페이지맞춤_최대_pt / 페이지맞춤_스텝_pt))), step_pt=페이지맞춤_스텝_pt)
            원위치 = hwp.GetPos()
            바꾼문단 = 바꾼셀 = 0
            try:
                문단시작 = time.perf_counter()
                for 위치, (원아래, 원위) in 조사['문단'].items():
                    현재 = 조사['문단현재'][위치]
                    for 칸, 원값, 줄임, 쓰기 in ((0, 원아래, 아래줄임, 문단_아래간격_적용_현재선택),
                                            (1, 원위, 위줄임, 문단_위간격_적용_현재선택)):
                        새값 = 원값 if 줄임 <= 0 else max(0.0, round(원값 - 줄임, 1))
                        if 위간격_0 and 칸 == 1:
                            새값 = 0.0
                        if abs(새값 - 현재[칸]) < 0.05:
                            continue
                        hwp.SetPos(위치[0], 위치[1], 0)
                        hwp_run('MoveParaBegin')
                        hwp_run('MoveSelParaEnd')
                        쓰기(새값)
                        hwp_run('Cancel')
                        현재[칸] = 새값
                        바꾼문단 += 1
                        쪽맞춤_바꾼문단.add(tuple(위치[:2]))
                쪽맞춤_계측_더하기('문단쓰기', time.perf_counter() - 문단시작, 바꾼문단)
                최소_hwpunit = max(0, int(round(페이지맞춤_표셀세로여백_최소_pt * 100)))
                셀시작 = time.perf_counter()
                for area, 원래 in 조사['셀'].items():
                    if 비율 <= 0:
                        목표 = 원래
                    else:
                        목표 = (1, max(최소_hwpunit, int(round(원래[1] * (1.0 - 비율)))),
                               max(최소_hwpunit, int(round(원래[2] * (1.0 - 비율)))))
                    현재 = 조사['셀현재'][area]
                    if 목표 == 현재 or (비율 > 0 and abs(목표[1] - 현재[1]) < 5 and abs(목표[2] - 현재[2]) < 5):
                        continue
                    hwp.SetPos(area, 0, 0)
                    성공 = (셀_세로여백_현재선택(원래값=원래) if 비율 <= 0
                          else 셀_세로여백_현재선택(top_hwpunit=목표[1], bottom_hwpunit=목표[2]))
                    if 성공:
                        조사['셀현재'][area] = 목표
                        바꾼셀 += 1
                쪽맞춤_계측_더하기('표셀쓰기', time.perf_counter() - 셀시작, 바꾼셀)
            finally:
                try:
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
            return 바꾼문단, 바꾼셀
        return bind_function(쪽맞춤_레벨_적용, _docfit_namespace)
    if _docfit_symbol == '_보고서_페이지수_맞춤_고속':
        def _보고서_페이지수_맞춤_고속(목표_페이지수):
            """대상 조사 1회 + 레벨 이분 탐색으로 쪽 수를 맞춘다. 결과는 기존 방식과 같은 뜻의 True/False.

            탐색이 어긋나면(측정 실패, 다시 잰 쪽 수가 다름) 원래 값으로 되돌리고 None을 돌려줘 기존 방식을 쓰게 한다.
            """
            global 쪽맞춤_묶음_확인됨, 쪽맞춤_묶음이동_결정
            최소쪽 = max(1, 목표_페이지수 - 페이지맞춤_뒤쪽범위_쪽수)
            반레벨 = max(1, int(round(페이지맞춤_최대_pt / 페이지맞춤_스텝_pt)))
            최대레벨 = 2 * 반레벨
            로그(f"페이지 수 맞춤 시도(고속): 목표 {목표_페이지수}쪽 (문단 아래·위 간격 및 표 셀 여백 최대 "
                 f"{페이지맞춤_최대_pt:g}pt, {최소쪽}쪽부터, 레벨 1~{최대레벨} 이분 탐색, 묶음 규칙 확인)")
            시작 = time.perf_counter()
            조사 = 쪽맞춤_대상_조사(최소쪽)
            로그(f"[쪽 수 맞춤 고속] 대상 조사: 문단 {len(조사['문단'])}개·표 셀 {len(조사['셀'])}개 "
                 f"({time.perf_counter() - 시작:.1f}초)")
            if not 조사['문단'] and not 조사['셀']:
                로그("페이지 수 맞춤: 줄일 문단 간격 및 표 셀 여백이 없음")
                return False

            def 측정(레벨):
                if 중단_요청됨():
                    return None
                단계시작 = time.perf_counter()
                바꾼문단, 바꾼셀 = 쪽맞춤_레벨_적용(조사, 레벨)
                구간시작 = time.perf_counter()
                마지막쪽, _ = 마지막쪽_화면줄수()
                쪽맞춤_계측_더하기('쪽측정', time.perf_counter() - 구간시작, 1)
                로그(f"[쪽 수 맞춤 고속] 레벨 {레벨}: {마지막쪽}쪽 (바꾼 간격 {바꾼문단}곳·셀 {바꾼셀}개, "
                     f"{time.perf_counter() - 단계시작:.1f}초)")
                return 마지막쪽

            def 묶음걸림(레벨):
                쪽맞춤_레벨_적용(조사, 레벨)
                구간시작 = time.perf_counter()
                try:
                    return 쪽맞춤_묶음분리_있음(최소쪽=최소쪽)
                finally:
                    쪽맞춤_계측_더하기('묶음검사', time.perf_counter() - 구간시작, 1)

            완료 = False
            try:
                결과 = 쪽맞춤_레벨_탐색(측정, 목표_페이지수, 최대레벨, bundle_split=묶음걸림,
                                  extra_levels=페이지맞춤_묶음확인_추가단계)
                if 결과['status'] == 'error':
                    if 중단_요청됨():
                        return False
                    로그("페이지 수 맞춤(고속): 쪽 번호 확인 실패 — 기존 방식으로 다시 시도")
                    return None
                if 결과['status'] == 'fail':
                    로그(f"페이지 수 맞춤 실패: 문단 아래·위 간격 및 표 셀 여백을 최대 {페이지맞춤_최대_pt:g}pt까지 줄여도 "
                         f"목표({목표_페이지수}쪽) 미달 — 바꾼 간격·여백을 원래 값으로 되돌림")
                    return False
                레벨 = 결과['level']
                쪽맞춤_레벨_적용(조사, 레벨)
                마지막쪽, _ = 마지막쪽_화면줄수()
                if 마지막쪽 is None or 마지막쪽 > 목표_페이지수:
                    로그(f"페이지 수 맞춤(고속): 레벨 {레벨}을 다시 재니 {마지막쪽}쪽 — 쪽 수가 레벨 순서대로 줄지 않아 "
                         "기존 방식으로 다시 시도")
                    return None
                아래, 위, _ = 쪽맞춤_레벨_줄임량(레벨, half=반레벨, step_pt=페이지맞춤_스텝_pt)
                문구 = f"레벨 {레벨}(아래 간격 {아래:g}pt·위 간격 {위:g}pt, 표 셀 여백 연동, 측정 {len(결과['measured'])}회)"
                완료 = True
                if 결과['status'] == 'ok':
                    쪽맞춤_묶음_확인됨 = True
                    로그(f"페이지 수 맞춤 완료: {문구} 축소로 {목표_페이지수}쪽 달성, 쪽 경계에 걸린 묶음 없음")
                else:
                    쪽맞춤_묶음이동_결정 = True
                    로그(f"페이지 수 맞춤: 묶음 규칙을 함께 지키는 레벨이 없어 처음 {목표_페이지수}쪽에 닿은 {문구}로 두고, "
                         "걸린 묶음은 쪽 배치에서 다음 쪽으로 옮김")
                return True
            finally:
                if not 완료:
                    구간시작 = time.perf_counter()
                    try:
                        쪽맞춤_레벨_적용(조사, 0)
                    finally:
                        쪽맞춤_계측_더하기('원복', time.perf_counter() - 구간시작)
        return bind_function(_보고서_페이지수_맞춤_고속, _docfit_namespace)
    if _docfit_symbol == '보고서_페이지수_맞춤_시도':
        def 보고서_페이지수_맞춤_시도(목표_페이지수):
            """페이지 수 맞춤 본체를 부르며 구간별 소요 시간을 작업 로그에 남긴다(동작은 같다)."""
            쪽맞춤_계측_시작()
            시작 = time.perf_counter()
            결과 = False
            try:
                if 페이지맞춤_고속_사용 and hwp is not None and 목표_페이지수 and 목표_페이지수 > 0:
                    try:
                        결과 = _보고서_페이지수_맞춤_고속(목표_페이지수)
                    except Exception as e:
                        로그(f"페이지 수 맞춤(고속) 오류: {e} — 기존 방식으로 다시 시도")
                        결과 = None
                    if 결과 is not None:
                        return 결과
                결과 = _보고서_페이지수_맞춤_시도_본체(목표_페이지수)
                return 결과
            finally:
                전체초 = time.perf_counter() - 시작
                값 = 쪽맞춤_계측_끝()
                if 값:
                    로그(쪽맞춤_계측_합계문구(값, 전체초, 결과))
        return bind_function(보고서_페이지수_맞춤_시도, _docfit_namespace)
    if _docfit_symbol == '_보고서_페이지수_맞춤_시도_본체':
        def _보고서_페이지수_맞춤_시도_본체(목표_페이지수):
            """본문 줄간격은 그대로 둔 채 항목기호 문단의 간격과 표의 셀 세로 여백을
            단계별로 비례 축소하여 실제 페이지 수를 목표에 맞춘다.

            먼저 '문단 아래 간격'과 표 셀 여백을 연동해 줄이고, 그래도 안 되면
            '문단 위 간격'과 표 셀 여백을 줄인다. 각각 페이지맞춤_최대_pt까지만
            줄이며, 매 단계 실제 페이지 수를 다시 잰다.

            묶음 규칙도 확인한다. 목표 쪽 수에 닿았을 때 쪽 경계에 걸린 묶음이
            없으면 그대로 끝낸다. 걸린 묶음이 있으면 몇 단계 더 줄여 보고, 끝내
            둘 다 만족하지 못하면 처음 목표에 닿았던 단계로 되돌려 둔다 — 그 뒤
            쪽 배치가 걸린 묶음 전체를 다음 쪽으로 옮긴다(사용자 결정: 마지막 쪽에
            본문 1줄만 남기는 것보다 묶음 전체를 옮기는 편을 택함).
            목표 쪽 수에 한 번도 닿지 못하면 바꾼 간격과 여백을 모두 원래 값으로 되돌린다.
            """
            global 쪽맞춤_묶음_확인됨, 쪽맞춤_묶음이동_결정
            쪽맞춤_묶음_확인됨 = False
            쪽맞춤_묶음이동_결정 = False
            if hwp is None or not 목표_페이지수 or 목표_페이지수 <= 0:
                return False
            최대반복 = max(1, int(round(페이지맞춤_최대_pt / 페이지맞춤_스텝_pt)))
            최소쪽 = max(1, 목표_페이지수 - 페이지맞춤_뒤쪽범위_쪽수)
            로그(
                f"페이지 수 맞춤 시도: 목표 {목표_페이지수}쪽 (문단 아래·위 간격 및 표 셀 여백 최대 "
                f"{페이지맞춤_최대_pt:g}pt 비례 축소, {최소쪽}쪽부터만 검사, 묶음 규칙 확인)"
            )
            원래값 = {False: {}, True: {}}
            표셀_원래값 = {}
            적용기록 = []          # 적용한 단계 순서(위간격 여부) — 되돌린 뒤 다시 적용할 때 쓴다
            첫_도달 = None         # 처음 목표 쪽 수에 닿았을 때의 적용기록 길이
            추가단계 = 0

            def 원래대로():
                시작 = time.perf_counter()
                try:
                    return (구조문단_간격_복원(원래값[True], 위간격=True)
                            + 구조문단_간격_복원(원래값[False])
                            + 표_셀_세로여백_복원(표셀_원래값))
                finally:
                    쪽맞춤_계측_더하기('원복', time.perf_counter() - 시작)

            for 위간격 in (False, True):
                이름 = "문단 위 간격" if 위간격 else "문단 아래 간격"
                for 회 in range(1, 최대반복 + 1):
                    if 중단_요청됨():
                        return False
                    단계시작 = time.perf_counter()
                    계측_이전 = 쪽맞춤_계측_복사()
                    구간시작 = time.perf_counter()
                    조정수 = 구조문단_간격_일괄조정(
                        -페이지맞춤_스텝_pt, 최소쪽=최소쪽, 위간격=위간격, 원래값=원래값[위간격])
                    쪽맞춤_계측_더하기('문단합계', time.perf_counter() - 구간시작)
                    표조정수 = 0
                    if 페이지맞춤_표셀세로여백_사용:
                        스텝 = len(적용기록) + 1
                        구간시작 = time.perf_counter()
                        표조정수 = 표_셀_세로여백_일괄조정(
                            스텝, 최소쪽=최소쪽, 원래값=표셀_원래값)
                        쪽맞춤_계측_더하기('표합계', time.perf_counter() - 구간시작)
                    if 조정수 == 0 and 표조정수 == 0:
                        로그(f"페이지 수 맞춤: 더 줄일 {이름} 및 표 셀 여백이 없음")
                        break
                    적용기록.append(위간격)
                    구간시작 = time.perf_counter()
                    마지막쪽, _ = 마지막쪽_화면줄수()
                    쪽맞춤_계측_더하기('쪽측정', time.perf_counter() - 구간시작, 1)
                    로그(쪽맞춤_계측_단계문구(이름, 회, 쪽맞춤_계측_차이(계측_이전),
                                          time.perf_counter() - 단계시작, 마지막쪽))
                    if 마지막쪽 is None:
                        로그("페이지 수 맞춤 중단: 쪽 번호 확인 실패")
                        break
                    if 마지막쪽 > 목표_페이지수:
                        continue
                    구간시작 = time.perf_counter()
                    묶음걸림 = 쪽맞춤_묶음분리_있음(최소쪽=최소쪽)
                    쪽맞춤_계측_더하기('묶음검사', time.perf_counter() - 구간시작, 1)
                    if not 묶음걸림:
                        쪽맞춤_묶음_확인됨 = True
                        로그(f"페이지 수 맞춤 완료: {이름} {회}단계({회 * 페이지맞춤_스텝_pt:g}pt, 표 셀 여백 연동) 축소로 "
                             f"{목표_페이지수}쪽 달성, 쪽 경계에 걸린 묶음 없음")
                        return True
                    if 첫_도달 is None:
                        첫_도달 = len(적용기록)
                        로그(f"페이지 수 맞춤: {목표_페이지수}쪽에 닿았지만 쪽 경계에 걸린 묶음이 있어 "
                             f"최대 {페이지맞춤_묶음확인_추가단계}단계 더 줄여 봄")
                    else:
                        추가단계 += 1
                    if 추가단계 >= 페이지맞춤_묶음확인_추가단계:
                        break
                else:
                    continue
                if 첫_도달 is not None and 추가단계 >= 페이지맞춤_묶음확인_추가단계:
                    break

            if 첫_도달 is None:
                복원수 = 원래대로()
                로그(
                    f"페이지 수 맞춤 실패: 문단 아래·위 간격 및 표 셀 여백을 최대 {페이지맞춤_최대_pt:g}pt까지 줄여도 "
                    f"목표({목표_페이지수}쪽) 미달 — 바꾼 간격·여백 {복원수}곳을 원래 값으로 되돌림"
                )
                return False

            # 묶음 규칙까지 지키는 단계는 없었다. 처음 목표에 닿았던 단계로 되돌려 두면
            # 쪽 배치가 걸린 묶음 전체를 다음 쪽으로 옮긴다.
            원래대로()
            재적용시작 = time.perf_counter()
            for 위간격 in 적용기록[:첫_도달]:
                구조문단_간격_일괄조정(-페이지맞춤_스텝_pt, 최소쪽=최소쪽, 위간격=위간격)
            if 페이지맞춤_표셀세로여백_사용 and 첫_도달 > 0:
                표_셀_세로여백_일괄조정(첫_도달, 최소쪽=최소쪽, 원래값=표셀_원래값)
            쪽맞춤_계측_더하기('원복', time.perf_counter() - 재적용시작)
            쪽맞춤_묶음이동_결정 = True
            로그(f"페이지 수 맞춤: 묶음 규칙을 함께 지키는 단계가 없어 처음 {목표_페이지수}쪽에 닿은 "
                 f"단계({첫_도달}단계)로 두고, 걸린 묶음은 쪽 배치에서 다음 쪽으로 옮김")
            return True
        return bind_function(_보고서_페이지수_맞춤_시도_본체, _docfit_namespace)
    if _docfit_symbol == '_칸_문단글들':
        def _칸_문단글들(area, 최대=6):
            """표 칸(area)의 문단 글 목록. 칸으로 옮기지 못하면 None."""
            hwp.SetPos(area, 0, 0)
            if hwp.GetPos()[0] != area:
                return None
            글들 = []
            for _ in range(최대):
                이전 = hwp.GetPos()
                글들.append(현재문단_텍스트())
                hwp.SetPos(*이전)
                hwp_run('MoveNextParaBegin')
                지금 = hwp.GetPos()
                # 칸의 마지막 문단에서는 같은 문단에 머문다(실측: 한 문단 칸을 여섯 번 읽음).
                if 지금[0] != area or 지금[1] <= 이전[1]:
                    break
            return 글들
        return bind_function(_칸_문단글들, _docfit_namespace)
    if _docfit_symbol == '제목표인가_현재':
        def 제목표인가_현재(표키):
            """본문 표가 보고서 제목 표인지 한/글 화면에서 본다(보고서 경계 판정용).

            칸이 2~3개이고 첫 칸이 제목, 나머지 칸 중 하나 이상이 담당자 칸(과장·팀장·☎ 등)이다. 2×2의 날짜 칸,
            3행1열의 두 담당자 칸(실측: 마포문화재단), '- … -' 부제 줄(실측: 고용협력과)도 받는다. 제목 칸은
            □·ㅇ 등 계층 기호로 시작하지 않는 1~3문단이고 '붙임'으로 시작하지 않는다. 날짜·담당자 칸이 모두 빈 표도 제목 표다.
            """
            범위 = 표_칸영역_범위(표키)
            if 범위 and 범위[1] == 범위[0]:
                return _한칸_제목표인가_현재(범위[0])
            if 범위 and 4 <= 범위[1] - 범위[0] + 1 <= 16:
                return _기타_제목표인가_현재(범위)
            if not 범위 or 범위[1] - 범위[0] + 1 not in (2, 3):
                return False
            original = hwp.GetPos()
            try:
                칸글 = [_칸_문단글들(area) for area in range(범위[0], 범위[1] + 1)]
            except Exception:
                return False
            finally:
                hwp.SetPos(*original)
            if any(글 is None for 글 in 칸글):
                return False
            제목 = [t.strip() for t in 칸글[0] if t.strip()]
            if not 1 <= len(제목) <= 3 or any(re.match(r'^[□ㅁㅇ○※*]', t) for t in 제목):
                return False
            합 = ' '.join(제목)
            if len(합) > 160 or 합.startswith('붙임'):
                return False
            정보 = [' '.join(글).strip() for 글 in 칸글[1:]]
            if not any(정보):
                return True
            return any(_제목표_담당자.search(t) or _설정_담당자_글인가(t) for t in 정보)
        return bind_function(제목표인가_현재, _docfit_namespace)
    if _docfit_symbol == '_한칸_제목표인가_현재':
        def _한칸_제목표인가_현재(area):
            """한 칸 표(칸 목록 번호 area)가 1×1 제목 상자인지: 제목다운 글이고 글자가 한칸_제목_최소크기_pt 이상."""
            original = hwp.GetPos()
            try:
                글들 = _칸_문단글들(area)
                if not 글들 or not _한칸_제목글인가(글들):
                    return False
                hwp.SetPos(area, 0, 0)
                hwp_run('MoveSelParaEnd')
                크기 = float(hwp.CharShape.Item('Height') or 0) / 100
                hwp_run('Cancel')
                return 크기 >= 한칸_제목_최소크기_pt
            except Exception:
                return False
            finally:
                try:
                    hwp.SetPos(*original)
                except Exception:
                    pass
        return bind_function(_한칸_제목표인가_현재, _docfit_namespace)
    if _docfit_symbol == '_기타_제목표인가_현재':
        def _기타_제목표인가_현재(범위):
            """여러 칸 장식 제목 상자인지(화면 판정, _기타_제목표인가와 같은 기준)."""
            original = hwp.GetPos()
            try:
                칸글 = [(area, _칸_문단글들(area)) for area in range(범위[0], 범위[1] + 1)]
                if any(글 is None for _, 글 in 칸글):
                    return False
                글칸 = [(a, 글) for a, 글 in 칸글 if any(t.strip() for t in 글)]
                제목칸 = [a for a, 글 in 글칸 if _한칸_제목글인가(글)]
                if len(제목칸) != 1:
                    return False
                if any(not 보고서머리.parse_info(' '.join(글).strip()) for a, 글 in 글칸 if a != 제목칸[0]):
                    return False
                hwp.SetPos(제목칸[0], 0, 0)
                hwp_run('MoveSelParaEnd')
                크기 = float(hwp.CharShape.Item('Height') or 0) / 100
                hwp_run('Cancel')
                return 크기 >= 한칸_제목_최소크기_pt
            except Exception:
                return False
            finally:
                try:
                    hwp.SetPos(*original)
                except Exception:
                    pass
        return bind_function(_기타_제목표인가_현재, _docfit_namespace)
    if _docfit_symbol == '_보고서_끝내용':
        def _보고서_끝내용(시작문단, 끝문단, 표문단):
            """보고서 문단 범위에서 마지막 내용: (끝 위치, None) 또는 표로 끝나면 (None, 표키). 없으면 (None, None)."""
            for 번호 in range(끝문단, 시작문단 - 1, -1):
                if 번호 in 표문단:
                    return None, 표문단[번호]
                hwp.SetPos(0, 번호, 0)
                if tuple(hwp.GetPos()[:2]) != (0, 번호):
                    continue
                if 현재문단_텍스트().strip():
                    hwp_run('MoveParaEnd')
                    return tuple(hwp.GetPos()), None
            return None, None
        return bind_function(_보고서_끝내용, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_보고서_끝쪽':
        def 쪽맞춤_보고서_끝쪽(끝):
            """보고서 끝 내용의 (쪽, 그 쪽에 걸린 줄 수). 표로 끝나면 줄 수는 None, 모르면 (None, None)."""
            위치, 표키 = 끝
            if 표키 is not None:
                범위 = 표_쪽범위(표키)
                return (범위[1] if 범위 else None), None
            if 위치 is None:
                return None, None
            원위치 = hwp.GetPos()
            try:
                hwp.SetPos(*위치)
                쪽 = 현재_페이지번호()
                hwp_run('MovePageBegin')
                줄수 = 0
                이전줄끝 = None
                while not 중단_요청됨():
                    hwp_run('MoveLineEnd')
                    줄끝 = hwp.GetPos()
                    if 줄끝 == 이전줄끝 or 줄끝[0] != 0:
                        break
                    줄수 += 1
                    if (줄끝[1], 줄끝[2]) >= (위치[1], 위치[2]):
                        break
                    이전줄끝 = 줄끝
                    hwp_run('MoveNextChar')
                    if hwp.GetPos() == 줄끝:
                        break
                return 쪽, 줄수
            except Exception as e:
                로그(f"보고서 끝 쪽 확인 실패(무시): {e}")
                return None, None
            finally:
                try:
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
        return bind_function(쪽맞춤_보고서_끝쪽, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_보고서_목록':
        def 쪽맞춤_보고서_목록(제목문단=None, 대상=None):
            """제목 표마다 나눈 보고서 목록과 제목 표 문단 번호.

            보고서: dict(문단범위, 끝, start, end, overflow, 제목). 첫 제목 표 앞 내용(표지 등)은 첫 보고서에 넣는다.
            대상(보고서 번호)을 주면 그 보고서의 쪽만 재고 나머지 자리는 None이다(쪽 측정이 보고서마다 반복되지 않게).
            """
            _표칸영역.clear()
            표문단 = 본문_표_문단번호()
            원위치 = hwp.GetPos()
            try:
                if 제목문단 is None:
                    제목문단 = sorted(번호 for 번호, 키 in 표문단.items() if 제목표인가_현재(키))
                쪽맞춤_제목문단.clear()
                쪽맞춤_제목문단.update(제목문단)
                hwp_run('MoveDocEnd')
                끝문단 = hwp.GetPos()[1] if hwp.GetPos()[0] == 0 else max(list(표문단) + [0])
                시작들 = 제목문단 or [0]
                if 시작들[0] != 0:
                    시작들 = [0] + 시작들[1:]
                보고서 = []
                for i, 시작 in enumerate(시작들):
                    if 대상 is not None and i != 대상:
                        보고서.append(None)
                        continue
                    끝 = (시작들[i + 1] - 1) if i + 1 < len(시작들) else 끝문단
                    hwp.SetPos(0, 시작, 0)
                    첫쪽 = 현재_페이지번호()
                    끝내용 = _보고서_끝내용(시작, 끝, 표문단)
                    끝쪽, 줄수 = 쪽맞춤_보고서_끝쪽(끝내용)
                    if 첫쪽 is None or 끝쪽 is None:
                        return None, 제목문단
                    보고서.append({'문단범위': range(시작, 끝 + 1), '끝': 끝내용, 'start': 첫쪽, 'end': 끝쪽,
                                 'overflow': 줄수 if 끝쪽 > 첫쪽 else 0})
                return 보고서, 제목문단
            finally:
                try:
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
        return bind_function(쪽맞춤_보고서_목록, _docfit_namespace)
    if _docfit_symbol == '_쪽맞춤_줄간격_되돌리기':
        def _쪽맞춤_줄간격_되돌리기(보관):
            for pos, kind, value in 보관:
                hwp.SetPos(*pos)
                act = hwp.CreateAction('ParagraphShape')
                pset = act.CreateSet()
                pset.SetItem('LineSpacingType', kind)
                pset.SetItem('LineSpacing', value)
                act.Execute(pset)
        return bind_function(_쪽맞춤_줄간격_되돌리기, _docfit_namespace)
    if _docfit_symbol == '보고서_1쪽_맞춤':
        def 보고서_1쪽_맞춤(보고서, 번호=1, 목표쪽수=1, 원본줄간격=None, 원본줄자간=None):
            """보고서를 첫 쪽부터 목표쪽수 쪽 안에 담는다. 성공하면 True, 못 하면 바꾼 값을 모두 되돌리고 False.

            1) 문단 아래·위 간격과 표 셀 여백을 레벨 이분 탐색으로 줄인다(보고서 쪽 범위 안 묶음이 쪽 경계에 걸리지 않는
            레벨을 고른다). 2) 최대로 줄여도 넘치면 마지막 수단으로 문단 위 간격을 모두 0pt, 표 셀 여백을 최소로 하고,
            그때 넘친 줄이 4줄 미만이면 줄간격을 설정 최솟값(기본 140%, 2026-10-15 사용자 지시로 160%에서 낮춤)까지 낮춘다. 3) 그래도 넘치고 원본의 줄간격이
            더 좁았으면(원본줄간격: 원본 문단별 줄간격 목록) 문단마다 원본 값으로 되돌리고, 문단 수가 다르면 원본 대표 줄간격까지
            낮춘다(사용자 결정, 2026-10-09: 결과의 쪽 구성은 원본과 같아야 한다).
            """
            global 세트문장_최소줄간격_퍼센트
            목표쪽 = 보고서['start'] + max(1, 목표쪽수) - 1
            범위 = 보고서['문단범위']
            시작 = time.perf_counter()
            조사 = 쪽맞춤_대상_조사(1, 문단범위=범위)
            로그(f"[쪽 수 맞춤] 보고서 {번호}({보고서['start']}~{보고서['end']}쪽 → {목표쪽수}쪽): 대상 문단 "
                 f"{len(조사['문단'])}개·표 셀 {len(조사['셀'])}개 ({time.perf_counter() - 시작:.1f}초)")
            반레벨 = max(1, int(round(페이지맞춤_최대_pt / 페이지맞춤_스텝_pt)))
            최대레벨 = 2 * 반레벨

            def 끝쪽():
                return 쪽맞춤_보고서_끝쪽(보고서['끝'])

            def 측정(레벨):
                if 중단_요청됨():
                    return None
                쪽맞춤_레벨_적용(조사, 레벨)
                return 끝쪽()[0]

            def 묶음걸림(레벨):
                쪽맞춤_레벨_적용(조사, 레벨)
                return 쪽맞춤_묶음분리_있음(최소쪽=보고서['start'], 최대쪽=목표쪽)

            줄간격보관 = []
            자간보관 = []
            완료 = False
            try:
                if 조사['문단'] or 조사['셀']:
                    결과 = 쪽맞춤_레벨_탐색(측정, 목표쪽, 최대레벨, bundle_split=묶음걸림,
                                      extra_levels=페이지맞춤_묶음확인_추가단계)
                    if 결과['status'] in ('ok', 'bundle_moved'):
                        쪽맞춤_레벨_적용(조사, 결과['level'])
                        if (끝쪽()[0] or 목표쪽 + 1) <= 목표쪽:
                            완료 = True
                            로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 레벨 {결과['level']} 축소(측정 {len(결과['measured'])}회"
                                 f"{', 쪽 경계 묶음 있음' if 결과['status'] == 'bundle_moved' else ''})")
                            return True
                if 중단_요청됨():
                    return False
                # 마지막 수단: 위 간격 0pt, 표 셀 여백 최소(최대 레벨의 아래 간격 축소는 그대로).
                쪽맞춤_레벨_적용(조사, 최대레벨, 위간격_0=True)
                쪽, 줄수 = 끝쪽()
                if 쪽 is not None and 쪽 <= 목표쪽:
                    완료 = True
                    로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 마지막 수단(문단 위 간격 0pt·표 셀 여백 최소)")
                    return True
                # 자간 초기화 등으로 원본보다 줄이 늘어난 문단은 마지막 줄 어절을 자간을 줄여 앞 줄로 당긴다(사용자 결정,
                # 2026-10-09. 실측: 원본 1줄 '기간' 문단이 자간 0%로 2줄이 되어 큰 표가 다음 쪽으로 밀림).
                자간_허용 = 작업_모드 != 'spacing' or any(stage_enabled(선택_세부작업, key, 작업_모드)
                                                    for key in ('body_spacing', 'word_check'))
                if 자간_허용 and 원본줄자간 and len(원본줄자간) == len(범위) and not 중단_요청됨():
                    맞춘수 = 0
                    for 문단번호, (원줄, _) in zip(범위, 원본줄자간):
                        지금줄 = 문단_화면줄수(문단번호) if 원줄 else None
                        if 지금줄 and 지금줄 > 원줄 and 문단_줄수_원본맞춤(문단번호, 원줄):
                            맞춘수 += 1
                    if 맞춘수:
                        쪽, 줄수 = 끝쪽()
                        if 쪽 is not None and 쪽 <= 목표쪽:
                            완료 = True
                            로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 마지막 수단 + 줄이 늘어난 문단 {맞춘수}개를 어절 당김으로 원본 줄 수에 맞춤")
                            return True
                if 쪽 == 목표쪽 + 1 and 줄수 is not None and 줄수 < 4:
                    hwp.SetPos(0, 범위.start, 0)
                    첫위치 = hwp.GetPos()
                    hwp.SetPos(0, 범위.stop - 1, 0)
                    줄간격보관 = 보고서_줄간격_보관(첫위치, hwp.GetPos()) or []
                    for 단계 in range(1, 11):
                        if 중단_요청됨() or not 보고서_줄간격_적용(줄간격보관, 단계):
                            break
                        쪽, 줄수 = 끝쪽()
                        if 쪽 is not None and 쪽 <= 목표쪽:
                            완료 = True
                            로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 마지막 수단(위 간격 0pt·표 셀 여백 최소) + 줄간격 "
                                 f"{단계 * 10}%p 축소(최소 {세트문장_최소줄간격_퍼센트}%)")
                            return True
                if 원본줄간격 and not 중단_요청됨():
                    if not 줄간격보관:
                        hwp.SetPos(0, 범위.start, 0)
                        첫위치 = hwp.GetPos()
                        hwp.SetPos(0, 범위.stop - 1, 0)
                        줄간격보관 = 보고서_줄간격_보관(첫위치, hwp.GetPos()) or []
                    if len(원본줄간격) == len(줄간격보관):
                        # 원본보다 넓어진 문단만 원본 줄간격으로 되돌린다(표를 담은 문단은 줄간격이 표 높이에 곱해져
                        # 분량을 크게 늘렸다. 실측: 145% → 160%).
                        바꾼수 = 0
                        for (pos, kind, value), (원형식, 원값) in zip(줄간격보관, 원본줄간격):
                            if 원형식 == kind and 0 < 원값 < value:
                                쪽맞춤_바꾼문단.add(tuple(pos[:2]))
                                hwp.SetPos(*pos)
                                act = hwp.CreateAction('ParagraphShape')
                                pset = act.CreateSet()
                                pset.SetItem('LineSpacingType', kind)
                                pset.SetItem('LineSpacing', 원값)
                                act.Execute(pset)
                                바꾼수 += 1
                        쪽, 줄수 = 끝쪽()
                        if 쪽 is not None and 쪽 <= 목표쪽:
                            완료 = True
                            로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 마지막 수단 + 넓어진 줄간격 {바꾼수}곳을 원본 값으로 되돌림")
                            return True
                    try:
                        percent = hwp.LineSpacingMethod('Percent')
                    except Exception:
                        percent = 0
                    값들 = [v for k, v in 원본줄간격 if k == percent and v >= 100]
                    원본줄간격 = min(값들) if 값들 else None
                if 원본줄간격 and 원본줄간격 < 세트문장_최소줄간격_퍼센트 and not 중단_요청됨():
                    if not 줄간격보관:
                        hwp.SetPos(0, 범위.start, 0)
                        첫위치 = hwp.GetPos()
                        hwp.SetPos(0, 범위.stop - 1, 0)
                        줄간격보관 = 보고서_줄간격_보관(첫위치, hwp.GetPos()) or []
                    기존하한 = 세트문장_최소줄간격_퍼센트
                    세트문장_최소줄간격_퍼센트 = int(원본줄간격)
                    try:
                        for 단계 in range(1, 16):
                            if 중단_요청됨() or not 보고서_줄간격_적용(줄간격보관, 단계):
                                break
                            쪽, 줄수 = 끝쪽()
                            if 쪽 is not None and 쪽 <= 목표쪽:
                                완료 = True
                                로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 마지막 수단 + 줄간격을 원본 최소 줄간격 {원본줄간격}%까지 낮춤"
                                     f"({단계 * 10}%p)")
                                return True
                    finally:
                        세트문장_최소줄간격_퍼센트 = 기존하한
                로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 실패: 마지막 수단으로도 {목표쪽}쪽 안에 담지 못함(넘친 줄 {줄수}) — 원래 값으로 되돌림")
                return False
            finally:
                if not 완료:
                    if 줄간격보관:
                        _쪽맞춤_줄간격_되돌리기(줄간격보관)
                    for 문단번호, 이전자간 in reversed(자간보관):
                        문단_자간_적용(문단번호, 이전자간)
                    쪽맞춤_레벨_적용(조사, 0)
        return bind_function(보고서_1쪽_맞춤, _docfit_namespace)
    if _docfit_symbol == '문단_화면줄수':
        def 문단_화면줄수(번호):
            """본문 문단의 화면줄 수(모르면 None)."""
            원위치 = hwp.GetPos()
            try:
                hwp.SetPos(0, 번호, 0)
                if tuple(hwp.GetPos()[:2]) != (0, 번호):
                    return None
                hwp_run('MoveParaEnd')
                끝 = hwp.GetPos()
                hwp.SetPos(0, 번호, 0)
                줄 = 0
                이전 = None
                while 줄 < 200:
                    hwp_run('MoveLineEnd')
                    줄끝 = hwp.GetPos()
                    if 줄끝 == 이전 or 줄끝[1] != 번호:
                        break
                    줄 += 1
                    if 줄끝[2] >= 끝[2]:
                        break
                    이전 = 줄끝
                    hwp_run('MoveNextChar')
                return 줄
            except Exception:
                return None
            finally:
                try:
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
        return bind_function(문단_화면줄수, _docfit_namespace)
    if _docfit_symbol == '문단_자간_읽기':
        def 문단_자간_읽기(번호):
            """본문 문단 전체를 선택했을 때의 자간 {항목: 값}(섞여 있으면 한/글이 주는 값). 실패하면 None."""
            원위치 = hwp.GetPos()
            try:
                hwp.SetPos(0, 번호, 0)
                hwp_run('MoveParaBegin')
                hwp_run('MoveSelParaEnd')
                act = hwp.CreateAction('CharShape')
                pset = act.CreateSet()
                act.GetDefault(pset)
                return {k: pset.Item(k) for k in _자간_항목}
            except Exception:
                return None
            finally:
                try:
                    hwp_run('Cancel')
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
        return bind_function(문단_자간_읽기, _docfit_namespace)
    if _docfit_symbol == '문단_자간_적용':
        def 문단_자간_적용(번호, 자간):
            """본문 문단 전체에 자간 {항목: 값}을 입힌다."""
            원위치 = hwp.GetPos()
            try:
                hwp.SetPos(0, 번호, 0)
                hwp_run('MoveParaBegin')
                hwp_run('MoveSelParaEnd')
                act = hwp.CreateAction('CharShape')
                pset = act.CreateSet()
                act.GetDefault(pset)
                for k, v in 자간.items():
                    if v is not None:
                        pset.SetItem(k, v)
                return act.Execute(pset) is not False
            except Exception:
                return False
            finally:
                try:
                    hwp_run('Cancel')
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
        return bind_function(문단_자간_적용, _docfit_namespace)
    if _docfit_symbol == '_문단_줄시작들':
        def _문단_줄시작들(번호):
            """본문 문단 화면줄마다 시작 위치 목록."""
            원위치 = hwp.GetPos()
            시작들 = []
            try:
                hwp.SetPos(0, 번호, 0)
                hwp_run('MoveParaEnd')
                끝 = hwp.GetPos()
                hwp.SetPos(0, 번호, 0)
                while len(시작들) < 200:
                    시작들.append(tuple(hwp.GetPos()))
                    hwp_run('MoveLineEnd')
                    줄끝 = hwp.GetPos()
                    if 줄끝[1] != 번호 or 줄끝[2] >= 끝[2]:
                        break
                    hwp_run('MoveNextChar')
                    if tuple(hwp.GetPos()) == tuple(줄끝):
                        break
                return 시작들
            finally:
                try:
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
        return bind_function(_문단_줄시작들, _docfit_namespace)
    if _docfit_symbol == '문단_줄수_원본맞춤':
        def 문단_줄수_원본맞춤(번호, 원줄):
            """원본보다 줄이 늘어난 문단에서 마지막 줄 어절을 자간을 줄여 앞 줄로 당겨 원본 줄 수에 맞춘다.

            기존 '다음 단어 당김'(다음단어_당김_시도)을 쓰되, 자간 상한(기본 10%)과 당길 어절 길이(기본 5자) 제한을
            본문 자간 최대치·20자까지 넓힌다(사용자 결정, 2026-10-09: 결과의 쪽 구성은 원본과 같아야 한다). 맞추면 True.
            """
            global 다음단어_당김_자간_최대_퍼센트, 문장부호_2줄_기준글자수
            if 작업_모드 == 'spacing' and not any(stage_enabled(선택_세부작업, key, 작업_모드)
                                              for key in ('body_spacing', 'word_check')):
                return False
            기존 = (다음단어_당김_자간_최대_퍼센트, 문장부호_2줄_기준글자수)
            다음단어_당김_자간_최대_퍼센트 = max(기존[0], int(자간_최대시도_본문 or 0), 40)   # 실측: 15%로는 두 어절째를 못 당김
            문장부호_2줄_기준글자수 = max(기존[1], 20)
            try:
                for _ in range(12):
                    if 중단_요청됨():
                        return False
                    시작들 = _문단_줄시작들(번호)
                    if len(시작들) <= 원줄:
                        return True
                    if len(시작들) < 2 or not 다음단어_당김_시도(시작들[-2], 다음단어_당김_자간_최대_퍼센트):
                        return False
                return len(_문단_줄시작들(번호)) <= 원줄
            finally:
                다음단어_당김_자간_최대_퍼센트, 문장부호_2줄_기준글자수 = 기존
        return bind_function(문단_줄수_원본맞춤, _docfit_namespace)
    if _docfit_symbol == '보고서_새쪽_시작인가':
        def 보고서_새쪽_시작인가(시작문단):
            """보고서 첫 문단(제목 표)이 새 쪽에서 시작하는지: 바로 앞 문단 끝보다 뒤 쪽에 있으면 True.

            쪽첫줄_시작인가(MovePageBegin 비교)는 제목 표가 문단 중간 위치에 놓이면 쪽 첫머리에 있어도 False라
            보고서 경계 쪽 나누기가 한 번도 들어가지 않았다(2026-10-09 실측).
            """
            if 시작문단 <= 0:
                return True
            원위치 = hwp.GetPos()
            try:
                hwp.SetPos(0, 시작문단, 0)
                쪽 = 현재_페이지번호()
                hwp.SetPos(0, 시작문단 - 1, 0)
                hwp_run('MoveParaEnd')
                앞쪽 = 현재_페이지번호()
                return bool(쪽 and 앞쪽 and 쪽 > 앞쪽)
            except Exception:
                return False
            finally:
                try:
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
        return bind_function(보고서_새쪽_시작인가, _docfit_namespace)
    if _docfit_symbol == '_대표_줄간격':
        def _대표_줄간격(목록):
            """원본 줄간격 목록에서 가장 많이 쓰인 비율 줄간격(없으면 None)."""
            try:
                percent = hwp.LineSpacingMethod('Percent')
            except Exception:
                percent = 0
            값들 = [value for kind, value in (목록 or []) if kind == percent and value > 0]
            return max(set(값들), key=값들.count) if 값들 else None
        return bind_function(_대표_줄간격, _docfit_namespace)
    if _docfit_symbol == '쪽맞춤_원본_보고서_기록':
        def 쪽맞춤_원본_보고서_기록():
            """처리 전 문서의 보고서별 쪽 수를 기록한다(결과에서도 보고서마다 이 쪽 수 안에 담는다)."""
            global 쪽맞춤_원본_보고서
            쪽맞춤_원본_보고서 = None
            # 쪽 구성 동일 원칙은 서식 통일에서만 쓴다(사용자 지정, 2026-10-09). 한 번에 적용·서식 적용은 문서 유형별
            # 쪽 맞춤(1쪽 보고서는 1쪽)만 한다.
            if not (작업_모드 == 'unify' and 쪽맞춤_유형판정_사용 and 페이지맞춤_문단간격_사용 and hwp is not None
                    and stage_enabled(선택_세부작업, 'page_layout_keep', 작업_모드)):
                return
            try:
                보고서, 제목문단 = 쪽맞춤_보고서_목록()
                if not 보고서:
                    return
                def 줄간격목록(r):
                    try:
                        보관 = 보고서_줄간격_보관((0, r['문단범위'].start, 0), (0, r['문단범위'].stop - 1, 0)) or []
                    except Exception:
                        return None
                    return [(kind, value) for _, kind, value in 보관]
                def 줄과자간(r):
                    return [(문단_화면줄수(번호), None) for 번호 in r['문단범위']]
                쪽맞춤_원본_보고서 = [(r['end'] - r['start'] + 1, 보고서_새쪽_시작인가(r['문단범위'].start), 줄간격목록(r),
                                  줄과자간(r)) for r in 보고서]
                로그(f"[문서 유형] 원본 보고서 {len(보고서)}개(제목 표 {len(제목문단)}개), 보고서별 쪽 수 "
                     f"{[x[0] for x in 쪽맞춤_원본_보고서]}, 대표 줄간격 {[_대표_줄간격(x[2]) for x in 쪽맞춤_원본_보고서]}% — "
                     "결과에서도 이 쪽 수 안에 담음")
            except Exception as e:
                로그(f"원본 보고서 쪽 수 기록 실패(무시): {e}")
            finally:
                _표칸영역.clear()
        return bind_function(쪽맞춤_원본_보고서_기록, _docfit_namespace)
    if _docfit_symbol == '_보고서_내부_쪽나눔_해제':
        def _보고서_내부_쪽나눔_해제(보고서):
            """보고서 첫 문단(제목 표)을 뺀 문단의 '문단 앞 쪽 나눔'을 푼다. 푼 개수."""
            해제 = 0
            원위치 = hwp.GetPos()
            try:
                for 번호 in list(보고서['문단범위'])[1:]:
                    hwp.SetPos(0, 번호, 0)
                    if tuple(hwp.GetPos()[:2]) != (0, 번호):
                        continue
                    act = hwp.CreateAction('ParagraphShape')
                    pset = act.CreateSet()
                    act.GetDefault(pset)
                    if int(pset.Item('PagebreakBefore') or 0):
                        쪽나눔_설정((0, 번호, 0), False)
                        해제 += 1
            finally:
                hwp.SetPos(*원위치)
            return 해제
        return bind_function(_보고서_내부_쪽나눔_해제, _docfit_namespace)
    if _docfit_symbol == '_문서유형별_쪽맞춤':
        def _문서유형별_쪽맞춤():
            """문서 유형을 판정해 보고서마다 정해진 쪽 수 안에 담는다.

            원본 보고서 쪽 수를 기록해 두었으면(보고서 수가 같을 때) 보고서마다 그 쪽 수가 목표다(사용자 지적, 2026-10-09:
            원본에서 1쪽이던 보고서가 결과에서 2쪽으로 퍼짐). 없으면 1쪽 보고서(넘친 줄 4줄 이하)만 1쪽에 맞춘다.
            처리했으면 True. 심화보고서이거나 판정하지 못하면 False(기존 '마지막 쪽 당기기'를 쓴다).
            """
            global _쪽맞춤_표캐시
            쪽맞춤_바꾼문단.clear()
            _쪽맞춤_표캐시 = {}
            try:
                return _문서유형별_쪽맞춤_본체()
            finally:
                _쪽맞춤_표캐시 = None
                _쪽맞춤_바꾼문단_단어분리_재검사()
        return bind_function(_문서유형별_쪽맞춤, _docfit_namespace)
    if _docfit_symbol == '_쪽맞춤_바꾼문단_단어분리_재검사':
        def _쪽맞춤_바꾼문단_단어분리_재검사():
            """보고서 쪽 맞춤이 고친 문단만 본문 자간·단어 분리 조정을 다시 한다(다음 단어 당김 제외)."""
            global 재검사_대상문단, 다음단어_당김_사용
            대상 = set(쪽맞춤_바꾼문단)
            쪽맞춤_바꾼문단.clear()
            if not 대상 or 중단_요청됨() or not (stage_enabled(선택_세부작업, 'body_spacing')
                                               or stage_enabled(선택_세부작업, 'word_check')):
                return
            로그(f"[쪽 수 맞춤] 간격·줄간격을 바꾼 {len(대상)}개 문단의 단어 분리 재검사")
            재검사_대상문단, 다음단어_당김_사용 = 대상, False
            try:
                순회_시작()
                본문_기존자간조정()
            except Exception as e:
                로그(f"쪽 수 맞춤 뒤 단어 분리 재검사 실패(무시): {e}")
            finally:
                재검사_대상문단, 다음단어_당김_사용 = None, True
        return bind_function(_쪽맞춤_바꾼문단_단어분리_재검사, _docfit_namespace)
    if _docfit_symbol == '_문서유형별_쪽맞춤_본체':
        def _문서유형별_쪽맞춤_본체():
            global 쪽맞춤_보고서조정됨
            쪽맞춤_보고서조정됨 = False
            보고서, 제목문단 = 쪽맞춤_보고서_목록()
            if not 보고서:
                로그("[문서 유형] 보고서 쪽 범위를 확인하지 못해 기존 방식으로 쪽 수를 맞춥니다.")
                return False
            원본 = 쪽맞춤_원본_보고서 if 쪽맞춤_원본_보고서 and len(쪽맞춤_원본_보고서) == len(보고서) else None
            유형, 대상 = 쪽맞춤_문서유형_판정(보고서, 페이지맞춤_최대남은줄수)
            if 원본 is not None:
                유형 = ('취합보고서' if len(보고서) > 1 else '1쪽 보고서' if 원본[0][0] == 1 else '심화보고서')
                목표 = {i: x[0] for i, x in enumerate(원본)}
                새쪽 = {i for i, x in enumerate(원본) if i and x[1]}
            else:
                목표 = {i: 1 for i in 대상}
                # 1쪽 분량 보고서(두 쪽 이하)가 쪽 중간에서 시작하면 새 쪽에서 시작한다(사용자 결정, 2026-10-09).
                새쪽 = {i for i, r in enumerate(보고서) if i and 유형 == '취합보고서' and r['end'] - r['start'] <= 1}
            요약 = ", ".join(f"{i + 1}:{r['start']}~{r['end']}쪽" for i, r in enumerate(보고서[:12]))
            로그(f"[문서 유형] {유형} — 제목 표 {len(제목문단)}개, 보고서 {len(보고서)}개({요약}"
                 f"{' …' if len(보고서) > 12 else ''})"
                 f"{', 원본 쪽 수 ' + str([x[0] for x in 원본]) if 원본 else ''}")
            if 유형 == '심화보고서' and 원본 is None:
                return False
            for 번호 in range(len(보고서)):
                if 중단_요청됨():
                    return True
                if 번호 not in 목표 and 번호 not in 새쪽:
                    continue
                # 앞 보고서를 바꾸면 뒤 보고서의 쪽이 바뀌므로 매번 다시 잰다(이 보고서만).
                현재목록, _ = 쪽맞춤_보고서_목록(제목문단, 대상=번호)
                if not 현재목록 or 번호 >= len(현재목록) or 현재목록[번호] is None:
                    break
                항목 = 현재목록[번호]
                위치 = (0, 항목['문단범위'].start, 0)
                # 원본에서 새 쪽에 시작한 보고서는 지금 쪽 첫머리에 있어도 쪽 나누기를 넣는다. 넣지 않으면 앞 보고서가
                # 나중에(쪽 배치 등) 늘어날 때 함께 밀렸다(2026-10-09 실측: 보고서 5~8이 한 쪽씩 밀림).
                if 번호 in 새쪽 and not 쪽나눔_켜짐(위치):
                    쪽나눔_설정(위치, True)
                    쪽맞춤_보고서조정됨 = True
                    로그(f"[문서 유형] 보고서 {번호 + 1}을 새 쪽에서 시작")
                    항목 = 쪽맞춤_보고서_목록(제목문단, 대상=번호)[0][번호]
                if 번호 not in 목표 or 항목['end'] - 항목['start'] + 1 <= 목표[번호]:
                    continue
                # 쪽 배치가 넣은 보고서 안의 쪽 나눔은 걷어내고 다시 잰다(원본에는 없던 빈 쪽을 만든다).
                if _보고서_내부_쪽나눔_해제(항목):
                    쪽맞춤_보고서조정됨 = True
                    항목 = 쪽맞춤_보고서_목록(제목문단, 대상=번호)[0][번호]
                    if 항목['end'] - 항목['start'] + 1 <= 목표[번호]:
                        로그(f"보고서 {번호 + 1}: 보고서 안 쪽 나눔을 풀어 {목표[번호]}쪽 안에 들어감")
                        continue
                if 보고서_1쪽_맞춤(항목, 번호 + 1, 목표[번호], 원본[번호][2] if 원본 is not None else None,
                               원본[번호][3] if 원본 is not None else None):
                    쪽맞춤_보고서조정됨 = True
                else:
                    hwp.SetPos(*위치)
                    검수_문제_기록(현재_처리파일, f"[보고서 쪽 수 초과] 보고서 {번호 + 1}이 원래 {목표[번호]}쪽 안에 담기지 않음")
            return True
        return bind_function(_문서유형별_쪽맞춤_본체, _docfit_namespace)
    if _docfit_symbol == '보고서_페이지수_맞춤_전체_적용':
        def 보고서_페이지수_맞춤_전체_적용():
            """마지막 쪽에 몇 줄 안 되는 내용만 걸쳐 있으면(다음 쪽으로 밀려난
            상황), 문단 아래 간격을 줄여 앞쪽 쪽으로 당겨오도록 시도한다.

            목표 쪽수를 사용자가 지정하지 않아도 되도록, "마지막 쪽 줄 수가
            적다"는 것 자체를 트리거로 쓴다 — 이 값이 크면(내용이 많이 남은
            경우) 간격 조정만으로는 해결이 안 되는 상황이라 아예 시도하지
            않는다. 실패해도 문서 자체는 항상 그대로 저장 가능한 상태로
            남는다(마지막 시도 이후 값이 남아있을 뿐, 구조를 깨지 않음).
            """
            global 쪽맞춤_묶음_확인됨, 쪽맞춤_묶음이동_결정
            # 여러 문서를 이어 처리할 때 앞 문서의 판단이 남지 않도록 매번 지운다.
            쪽맞춤_묶음_확인됨 = False
            쪽맞춤_묶음이동_결정 = False
            if not 페이지맞춤_문단간격_사용:
                return True
            if 중단_요청됨():
                return False
            if 쪽맞춤_유형판정_사용:
                try:
                    처리됨 = _문서유형별_쪽맞춤()
                except Exception as e:
                    로그(f"문서 유형 판정 실패(무시하고 기존 방식): {e}")
                    처리됨 = False
                if 처리됨:
                    hwp_run('MoveDocBegin')
                    return True
            마지막쪽, 줄수 = 마지막쪽_화면줄수()
            if 마지막쪽 is None or 줄수 is None:
                로그("페이지 수 맞춤 건너뜀: 마지막 쪽 정보 확인 실패")
                return True
            if 마지막쪽 <= 1 or 줄수 > 페이지맞춤_최대남은줄수:
                로그(f"페이지 수 맞춤 불필요: 마지막 쪽({마지막쪽}쪽)에 {줄수}줄 "
                     f"(당겨올 기준 {페이지맞춤_최대남은줄수}줄 이하가 아님)")
                return True
            로그(f"마지막 쪽({마지막쪽}쪽)에 {줄수}줄만 남아 페이지 수 맞춤을 시도합니다.")
            보고서_페이지수_맞춤_시도(마지막쪽 - 1)
            hwp_run('MoveDocBegin')
            return True
        return bind_function(보고서_페이지수_맞춤_전체_적용, _docfit_namespace)
    if _docfit_symbol == '전체_찾아바꾸기':
        def 전체_찾아바꾸기(찾을문자열, 바꿀문자열):
            """한글 AllReplace를 사용해 문서 전체(본문/표/글상자 등)를 치환한다.

            위치 오프셋을 직접 계산해서 Delete하는 방식보다 문자모양(run)이 갈라진
            HWP/HWPX에서도 안정적이다. HWP의 AllReplace가 캐럿 위치의 영향을 받는
            경우를 줄이기 위해 매 실행 전 문서 처음으로 이동한다.
            """
            if hwp is None or 찾을문자열 == 바꿀문자열:
                return False
            try:
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
                hwp_run("MoveDocBegin")

                pset = hwp.HParameterSet.HFindReplace
                hwp.HAction.GetDefault("AllReplace", pset.HSet)
                pset.MatchCase = 0
                pset.AllWordForms = 0
                pset.SeveralWords = 0
                pset.UseWildCards = 0
                pset.WholeWordOnly = 0
                pset.Direction = hwp.FindDir("AllDoc")
                pset.FindString = 찾을문자열
                pset.ReplaceString = 바꿀문자열
                pset.ReplaceMode = 1
                pset.IgnoreMessage = 1
                pset.FindRegExp = 0
                pset.FindType = 1
                return bool(hwp.HAction.Execute("AllReplace", pset.HSet))
            except Exception as e:
                로그(f"문서 전체 찾아바꾸기 실패(무시): {찾을문자열!r} → {바꿀문자열!r} / {e}")
                return False
        return bind_function(전체_찾아바꾸기, _docfit_namespace)
    if _docfit_symbol == '괄호_안쪽_공백_정리_AllReplace':
        def 괄호_안쪽_공백_정리_AllReplace():
            """괄호 바로 안쪽 공백을 문서 전체에서 제거한다.

            '(   내용)'처럼 여러 칸인 경우도 없어질 때까지 반복한다.
            ASCII space 외에 NBSP/전각 공백도 처리한다.
            탭은 AllReplace 환경별 차이가 있어 문단 보정 함수에서도 한 번 더 처리한다.
            """
            총실행 = 0
            # HWP AllReplace는 일부 버전에서 실제 치환이 있었어도 반환값이 False가
            # 될 수 있으므로 반환값만 보고 반복을 중단하지 않는다.
            # ASCII 공백은 16칸부터 1칸까지 "정확한 문자열"을 긴 것부터 제거하여
            # 한 번에 여러 칸도 처리하고, NBSP/전각공백/탭도 별도로 정리한다.
            for 길이 in range(16, 0, -1):
                공백묶음 = " " * 길이
                if 전체_찾아바꾸기("(" + 공백묶음, "("):
                    총실행 += 1
                if 전체_찾아바꾸기(공백묶음 + ")", ")"):
                    총실행 += 1

            for 공백문자 in ("\u00A0", "\u3000", "\t"):
                # 동일 종류 공백이 여러 개 연속된 경우도 제거되도록 몇 차례 반복한다.
                for _ in range(4):
                    if 전체_찾아바꾸기("(" + 공백문자, "("):
                        총실행 += 1
                    if 전체_찾아바꾸기(공백문자 + ")", ")"):
                        총실행 += 1
            return 총실행
        return bind_function(괄호_안쪽_공백_정리_AllReplace, _docfit_namespace)
    if _docfit_symbol == '괄호_안쪽_공백_정리_문단_처리':
        def 괄호_안쪽_공백_정리_문단_처리():
            """현재 문단에서 괄호 바로 안쪽 공백을 후방 보정한다.

            AllReplace가 특정 컨트롤/환경에서 놓친 경우를 위한 2차 안전장치다.
            """
            if 현재_한칸표인가():
                return 0
            text = 현재문단_텍스트()
            if not text or "(" not in text or ")" not in text:
                return 0

            삭제구간 = [(m.start(), m.end()) for m in 괄호_안쪽_공백_패턴.finditer(text)]
            if not 삭제구간:
                return 0

            병합 = []
            for 시작, 끝 in sorted(삭제구간):
                if 병합 and 시작 <= 병합[-1][1]:
                    병합[-1] = (병합[-1][0], max(병합[-1][1], 끝))
                else:
                    병합.append((시작, 끝))

            문단_시작위치 = hwp.GetPos()
            삭제수 = 0
            try:
                for 시작, 끝 in reversed(병합):
                    try:
                        if 문단_범위_선택(문단_시작위치, 시작, 끝) is False:
                            raise RuntimeError("구간 선택 실패")
                        hwp_run("Delete")
                        삭제수 += (끝 - 시작)
                    except Exception as e:
                        로그(f"괄호 안쪽 공백 후방 보정 실패(무시): {e}")
                        try:
                            hwp_run("Cancel")
                        except Exception:
                            pass
            finally:
                try:
                    hwp.SetPos(*문단_시작위치)
                except Exception:
                    pass
            return 삭제수
        return bind_function(괄호_안쪽_공백_정리_문단_처리, _docfit_namespace)
    if _docfit_symbol == '쉼표_공백_보정_대상':
        def 쉼표_공백_보정_대상(text):
            """단어와 단어 사이 쉼표 주변 공백을 표준화할 구간을 반환한다.

            규칙:
              - 쉼표 앞 공백: 0칸
              - 쉼표 뒤 공백: 정확히 ASCII 공백 1칸

            숫자 천단위(1,000)는 건드리지 않는다.

            반환값: [(시작, 끝), ...]
              시작~끝 구간을 `", "`로 교체한다.

              - "도토리,만두"     -> "도토리, 만두"
              - "도토리 ,만두"    -> "도토리, 만두"
              - "도토리,  만두"   -> "도토리, 만두"
              - "도토리  ,  만두" -> "도토리, 만두"
            """
            결과 = []
            if not text or "," not in text:
                return 결과

            공백문자 = " \t\u00A0\u3000"
            for 쉼표위치, ch in enumerate(text):
                if ch != ",":
                    continue

                # 쉼표 왼쪽 공백을 건너뛰어 실제 앞 문자를 찾는다.
                왼쪽 = 쉼표위치 - 1
                while 왼쪽 >= 0 and text[왼쪽] in 공백문자:
                    왼쪽 -= 1
                앞문자위치 = 왼쪽
                if 앞문자위치 < 0:
                    continue

                # 쉼표 오른쪽 공백을 건너뛰어 실제 다음 문자를 찾는다.
                오른쪽 = 쉼표위치 + 1
                while 오른쪽 < len(text) and text[오른쪽] in 공백문자:
                    오른쪽 += 1
                if 오른쪽 >= len(text):
                    continue

                # 문자 단어 사이의 쉼표만 대상으로 한다.
                # 따라서 1,000 같은 숫자 천단위 표기는 제외된다.
                if not (text[앞문자위치].isalpha() and text[오른쪽].isalpha()):
                    continue

                시작 = 앞문자위치 + 1
                끝 = 오른쪽
                if text[시작:끝] == ", ":
                    continue
                결과.append((시작, 끝))

            return 결과
        return bind_function(쉼표_공백_보정_대상, _docfit_namespace)
    if _docfit_symbol == '쉼표_공백_정리_문단_처리':
        def 쉼표_공백_정리_문단_처리():
            """현재 문단의 단어 사이 쉼표를 `단어, 단어` 형식으로 정규화한다."""
            if 현재_한칸표인가():
                return 0
            text = 현재문단_텍스트()
            수정구간 = 쉼표_공백_보정_대상(text)
            if not 수정구간:
                return 0

            문단_시작위치 = hwp.GetPos()
            수정수 = 0
            try:
                # 오른쪽부터 처리하여 앞쪽 문자 위치가 변하지 않게 한다.
                for 시작, 끝 in reversed(수정구간):
                    try:
                        기존길이 = 끝 - 시작
                        if 기존길이 > 0:
                            if 문단_범위_선택(문단_시작위치, 시작, 끝) is False:
                                raise RuntimeError("구간 선택 실패")
                            hwp_run("Delete")
                        else:
                            hwp.SetPos(
                                문단_시작위치[0],
                                문단_시작위치[1],
                                문단_시작위치[2] + 문단_위치(문단_시작위치, 시작),
                            )
                        텍스트_삽입(", ")
                        수정수 += 1
                    except Exception as e:
                        로그(f"쉼표 공백 보정 실패(무시): {e}")
                        try:
                            hwp_run("Cancel")
                        except Exception:
                            pass
            finally:
                try:
                    hwp.SetPos(*문단_시작위치)
                except Exception:
                    pass
            return 수정수
        return bind_function(쉼표_공백_정리_문단_처리, _docfit_namespace)
    if _docfit_symbol == '_콜론_한글인가':
        def _콜론_한글인가(ch):
            return "\uAC00" <= ch <= "\uD7A3"
        return bind_function(_콜론_한글인가, _docfit_namespace)
    if _docfit_symbol == '콜론_공백_보정_대상':
        def 콜론_공백_보정_대상(text):
            """콜론 주변 공백을 `글자: 글자` 형식으로 맞출 구간을 반환한다.

            규칙(2026-10-10 사용자 지시):
              - 콜론 앞: 글자(숫자·닫는 괄호 포함)와 콜론 사이 공백 0칸
              - 콜론 뒤: 다음 글자와 사이에 ASCII 공백 정확히 1칸

            건드리지 않는 경우: 숫자:숫자(시각·비율), `::`, 콜론 뒤 `/`·`\\`·닫는 괄호,
            영문·숫자끼리 붙은 `mailto:abc`·`C:` 꼴(주소·경로일 수 있음, 붙은 곳에 공백을 넣지 않음),
            문단 맨 앞 콜론. 콜론 문자 자체(반각/전각)는 바꾸지 않는다.

            반환값: [(시작, 끝, 교체문자열), ...] 왼쪽에서 오른쪽, 서로 겹치지 않음.
            """
            결과 = []
            if not text or not any(c in text for c in _콜론_문자):
                return 결과
            n = len(text)
            for 위치, ch in enumerate(text):
                if ch not in _콜론_문자:
                    continue
                왼쪽 = 위치 - 1
                while 왼쪽 >= 0 and text[왼쪽] in _콜론_공백류:
                    왼쪽 -= 1
                if 왼쪽 < 0:
                    continue
                앞 = text[왼쪽]
                if not (앞.isalnum() or 앞 in _콜론_앞_닫는문자):
                    continue
                오른쪽 = 위치 + 1
                while 오른쪽 < n and text[오른쪽] in _콜론_공백류:
                    오른쪽 += 1
                뒤 = text[오른쪽] if 오른쪽 < n else ""
                if 뒤 in _콜론_문자:
                    continue
                if 앞.isdigit() and 뒤.isdigit():
                    continue
                왼쪽공백 = (왼쪽 + 1, 위치)
                if 왼쪽공백[0] < 왼쪽공백[1]:
                    결과.append((왼쪽공백[0], 왼쪽공백[1], ""))
                if not 뒤:
                    continue
                if 뒤 in "/\\" or 뒤 in _콜론_뒤_제외:
                    continue
                오른공백 = (위치 + 1, 오른쪽)
                if 오른공백[0] == 오른공백[1]:
                    # 붙어 있는 경우: 한글이 한쪽에 있을 때만 공백을 넣는다(URL·경로 보호).
                    if not (_콜론_한글인가(앞) or _콜론_한글인가(뒤)):
                        continue
                    결과.append((오른공백[0], 오른공백[1], " "))
                elif text[오른공백[0]:오른공백[1]] != " ":
                    결과.append((오른공백[0], 오른공백[1], " "))
            return 결과
        return bind_function(콜론_공백_보정_대상, _docfit_namespace)
    if _docfit_symbol == '콜론_공백_정리_문단_처리':
        def 콜론_공백_정리_문단_처리():
            """현재 문단의 콜론 주변 공백을 `글자: 글자` 형식으로 정규화한다."""
            if 현재_한칸표인가():
                return 0
            text = 현재문단_텍스트()
            수정구간 = 콜론_공백_보정_대상(text)
            if not 수정구간:
                return 0

            문단_시작위치 = hwp.GetPos()
            수정수 = 0
            try:
                # 오른쪽부터 처리하여 앞쪽 문자 위치가 변하지 않게 한다.
                for 시작, 끝, 교체 in reversed(수정구간):
                    try:
                        if 끝 > 시작:
                            if 문단_범위_선택(문단_시작위치, 시작, 끝) is False:
                                raise RuntimeError("구간 선택 실패")
                            hwp_run("Delete")
                        else:
                            hwp.SetPos(
                                문단_시작위치[0],
                                문단_시작위치[1],
                                문단_시작위치[2] + 문단_위치(문단_시작위치, 시작),
                            )
                        if 교체:
                            텍스트_삽입(교체)
                        수정수 += 1
                    except Exception as e:
                        로그(f"콜론 공백 보정 실패(무시): {e}")
                        try:
                            hwp_run("Cancel")
                        except Exception:
                            pass
            finally:
                try:
                    hwp.SetPos(*문단_시작위치)
                except Exception:
                    pass
            return 수정수
        return bind_function(콜론_공백_정리_문단_처리, _docfit_namespace)
    if _docfit_symbol == '쉼표_앞_공백_보정_대상':
        def 쉼표_앞_공백_보정_대상(text):
            return 쉼표_공백_보정_대상(text)
        return bind_function(쉼표_앞_공백_보정_대상, _docfit_namespace)
    if _docfit_symbol == '쉼표_앞_공백_정리_문단_처리':
        def 쉼표_앞_공백_정리_문단_처리():
            return 쉼표_공백_정리_문단_처리()
        return bind_function(쉼표_앞_공백_정리_문단_처리, _docfit_namespace)
    if _docfit_symbol == '_균등라벨_범위':
        def _균등라벨_범위(text, 시작=0):
            """text[시작:]이 (항목기호 +) 한 글자씩 띄운 콜론 라벨로 시작하면 라벨의 (처음, 끝), 아니면 None."""
            m = _균등라벨_패턴.match(text, 시작)
            return m.span(1) if m else None
        return bind_function(_균등라벨_범위, _docfit_namespace)
    if _docfit_symbol == '단어사이_연속공백_정리_대상':
        def 단어사이_연속공백_정리_대상(text):
            """문단 안에서 단어 사이의 공백류(2칸 이상, 또는 탭·전각공백 1칸)를
            표준 반각 공백 1칸으로 줄일 구간을 찾는다.

            문단 맨 앞의 들여쓰기 공백(□/ㅇ/- 등 항목 위치나 세트문장 후속 판정에
            쓰이는 선행 공백)은 이 정리의 대상이 아니므로 건드리지 않고, 실제
            내용이 시작된 뒤에 나오는 공백류만 대상으로 한다. 탭·전각공백은
            자동 탭 간격이 규격과 안 맞아 수기로 스페이스를 끼워 넣은 흔적인
            경우가 많아, 연속이 아니어도(1칸이라도) 표준 공백이 아니면 대상으로
            삼는다. '일    시:'처럼 한 글자씩 띄워 폭을 맞춘 문두 콜론 라벨 안의
            공백은 정렬용이므로 그대로 둔다.
            """
            결과 = []
            if not text:
                return 결과
            벗긴텍스트 = text.lstrip("".join(_단어사이_공백류))
            선행공백_길이 = len(text) - len(벗긴텍스트)
            라벨 = _균등라벨_범위(text, 선행공백_길이)
            # '바랍니다.  끝.'·'붙임  계획서 1부.'의 2타는 공식 규정(2025 행정업무운영 편람)이라 줄이지 않는다.
            공식2타 = official_double_space_spans(text)
            i = 선행공백_길이
            n = len(text)
            while i < n:
                if text[i] in _단어사이_공백류:
                    시작 = i
                    while i < n and text[i] in _단어사이_공백류:
                        i += 1
                    if 라벨 and 라벨[0] < 시작 and i < 라벨[1]:
                        continue
                    if any(처음 < i and 시작 < 끝 for 처음, 끝 in 공식2타):
                        continue
                    if (알파_연결부호_탭정렬_사용 and text[시작:i] == "	" and text.count("	") == 1
                            and 시작 > 선행공백_길이 and i < n):
                        continue            # 연결 부호를 바꾼 탭·목차 탭(글 사이 탭 하나)은 정렬용이라 남긴다
                    if i - 시작 > 1 or text[시작] != " ":
                        결과.append((시작, i))
                else:
                    i += 1
            return 결과
        return bind_function(단어사이_연속공백_정리_대상, _docfit_namespace)
    if _docfit_symbol == '단어사이_연속공백_정리_문단_처리':
        def 단어사이_연속공백_정리_문단_처리():
            """현재 문단에서 단어 사이의 연속 공백(2칸 이상)을 1칸으로 줄인다."""
            if 현재_한칸표인가():
                return 0
            text = 현재문단_텍스트()
            수정구간 = 단어사이_연속공백_정리_대상(text)
            if not 수정구간:
                return 0

            문단_시작위치 = hwp.GetPos()
            수정수 = 0
            try:
                # 오른쪽부터 처리하여 앞쪽 문자 위치가 변하지 않게 한다.
                for 시작, 끝 in reversed(수정구간):
                    try:
                        if 문단_범위_선택(문단_시작위치, 시작, 끝) is False:
                            raise RuntimeError("구간 선택 실패")
                        hwp_run("Delete")
                        텍스트_삽입(" ")
                        수정수 += 1
                    except Exception as e:
                        로그(f"연속 공백 정리 실패(무시): {e}")
                        try:
                            hwp_run("Cancel")
                        except Exception:
                            pass
            finally:
                try:
                    hwp.SetPos(*문단_시작위치)
                except Exception:
                    pass
            return 수정수
        return bind_function(단어사이_연속공백_정리_문단_처리, _docfit_namespace)
    if _docfit_symbol == '문두_미음_기호_위치':
        def 문두_미음_기호_위치(text):
            """문단 첫 비공백 문자가 항목기호 ㅁ일 때만 위치를 반환한다."""
            stripped = (text or "").lstrip()
            if not stripped.startswith("ㅁ"):
                return None
            return len(text) - len(stripped)
        return bind_function(문두_미음_기호_위치, _docfit_namespace)
    if _docfit_symbol == '문두_미음_기호_정리':
        def 문두_미음_기호_정리():
            # 기존 한 칸 표 보호 정책을 유지한다.
            if 현재_한칸표인가():
                return 0
            text = 현재문단_텍스트()
            offset = 문두_미음_기호_위치(text)
            if offset is None:
                return 0
            start = hwp.GetPos()
            try:
                if 문단_범위_선택(start, offset, offset + 1) is False:
                    raise RuntimeError("문두 ㅁ 선택 실패")
                텍스트_삽입("□")
                return 1
            finally:
                hwp_run("Cancel")
                hwp.SetPos(*start)
        return bind_function(문두_미음_기호_정리, _docfit_namespace)
    if _docfit_symbol == '연도_따옴표_정리_문단_처리':
        def 연도_따옴표_정리_문단_처리():
            """현재 문단에서 연도 앞의 작은따옴표만 ’로 바꾼다."""
            text = 현재문단_텍스트()
            matches = list(YEAR_QUOTE_PATTERN.finditer(text or ""))
            if not matches:
                return 0
            start = hwp.GetPos()
            changed = 0
            try:
                for match in reversed(matches):
                    if 문단_범위_선택(start, match.start(), match.end()) is False:
                        raise RuntimeError("연도 앞 따옴표 선택 실패")
                    텍스트_삽입("’")
                    changed += 1
            finally:
                hwp_run("Cancel")
                hwp.SetPos(*start)
            return changed
        return bind_function(연도_따옴표_정리_문단_처리, _docfit_namespace)
    if _docfit_symbol == '곧은따옴표_통일_문단_처리':
        def 곧은따옴표_통일_문단_처리():
            """현재 문단에서 곧은 큰따옴표(")를 한글 표준 둥근따옴표(" ")로 바꾼다.

            작은따옴표는 여기서 다루지 않는다 — 발·분 표기(6' 2")나 영어 축약형과
            진짜 인용부호를 구분할 방법이 없어, 연도 앞 표기처럼 문맥이 분명한
            좁은 규칙(연도_따옴표_정리_문단_처리)만 따로 둔다.
            """
            text = 현재문단_텍스트()
            replacements = straight_double_quote_replacements(text or "")
            if not replacements:
                return 0
            start = hwp.GetPos()
            changed = 0
            try:
                for index, replacement in reversed(replacements):
                    if 문단_범위_선택(start, index, index + 1) is False:
                        raise RuntimeError("곧은따옴표 선택 실패")
                    텍스트_삽입(replacement)
                    changed += 1
            finally:
                hwp_run("Cancel")
                hwp.SetPos(*start)
            return changed
        return bind_function(곧은따옴표_통일_문단_처리, _docfit_namespace)
    if _docfit_symbol == '작은따옴표_통일_문단_처리':
        def 작은따옴표_통일_문단_처리():
            """현재 문단에서 곧은 작은따옴표(')를 한글 표준 둥근따옴표(' ')로 바꾼다.

            연도 앞 표기('26년)는 이미 앞서 실행되는 연도_따옴표_정리_문단_처리가
            처리하므로, 여기 도달하는 '는 일반 인용부호로 보고 문맥(앞 글자)으로
            여는/닫는 방향을 판정한다. 숫자 뒤에 오는 '(6', 37° 33')는 발·분 표기로
            보아 건드리지 않는다 — curly_single_quote_replacements 참고.
            """
            text = 현재문단_텍스트()
            replacements = curly_single_quote_replacements(text or "")
            if not replacements:
                return 0
            start = hwp.GetPos()
            changed = 0
            try:
                for index, replacement in reversed(replacements):
                    if 문단_범위_선택(start, index, index + 1) is False:
                        raise RuntimeError("작은따옴표 선택 실패")
                    텍스트_삽입(replacement)
                    changed += 1
            finally:
                hwp_run("Cancel")
                hwp.SetPos(*start)
            return changed
        return bind_function(작은따옴표_통일_문단_처리, _docfit_namespace)
    if _docfit_symbol == '날짜_구분자_정리_문단_처리':
        def 날짜_구분자_정리_문단_처리():
            """현재 문단에서 날짜·기간·시간 표기의 대시류(-,–,—)를 물결표(~)로,
            날짜 뒤 빠진 온점과 요일 괄호 앞뒤 온점 위치를 표준에 맞춘다.

            normalize_date_range_marks가 만든 결과 문자열과 원문을 비교해 바뀐
            구간만 역순으로 적용한다(text_edit_spans) — 전화번호·법령 조항·사업
            코드처럼 점(.) 없는 하이픈은 애초에 패턴에 안 걸려 손대지 않는다.
            """
            text = 현재문단_텍스트()
            if not text:
                return 0
            변환후 = normalize_date_range_marks(text)
            spans = text_edit_spans(text, 변환후)
            if not spans:
                return 0
            문단_시작위치 = hwp.GetPos()
            수정수 = 0
            try:
                for 시작, 끝, 대체 in sorted(spans, key=lambda s: s[0], reverse=True):
                    try:
                        if 끝 > 시작:
                            if 문단_범위_선택(문단_시작위치, 시작, 끝) is False:
                                raise RuntimeError("날짜 구분자 구간 선택 실패")
                            if hwp_run("Delete") is False:
                                raise RuntimeError("날짜 구분자 구간 삭제 실패")
                            hwp.SetPos(*문단_시작위치)
                        if 대체:
                            hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2] + 문단_위치(문단_시작위치, 시작))
                            텍스트_삽입(대체)
                        수정수 += 1
                    except Exception as e:
                        로그(f"날짜 구분자 정리 실패(무시): {e}")
                        try:
                            hwp_run("Cancel")
                        except Exception:
                            pass
            finally:
                try:
                    hwp.SetPos(*문단_시작위치)
                except Exception:
                    pass
            return 수정수
        return bind_function(날짜_구분자_정리_문단_처리, _docfit_namespace)
    if _docfit_symbol == '공문_띄어쓰기_정리_문단_처리':
        def 공문_띄어쓰기_정리_문단_처리():
            """현재 문단에 「2025 행정업무운영 편람」 띄어쓰기 규정을 적용한다(normalize_official_spacing).

            '끝.' 앞·'붙임' 뒤 2타, 날짜 '2021. 12. 12.'(마침표 뒤 1타, 0 생략). 바뀐 구간만 뒤에서부터 고친다.
            """
            text = 현재문단_텍스트()
            if not text:
                return 0
            normalized = normalize_official_spacing(text)
            if normalize_attachment_list_header(text) != text:
                normalized = normalize_attachment_list_header(normalized)
            spans = text_edit_spans(text, normalized)
            if not spans:
                return 0
            문단_시작위치 = hwp.GetPos()
            수정수 = 0
            try:
                for 시작, 끝, 대체 in sorted(spans, key=lambda s: s[0], reverse=True):
                    try:
                        if 끝 > 시작:
                            if 문단_범위_선택(문단_시작위치, 시작, 끝) is False:
                                raise RuntimeError("공문 띄어쓰기 구간 선택 실패")
                            if hwp_run("Delete") is False:
                                raise RuntimeError("공문 띄어쓰기 구간 삭제 실패")
                            hwp.SetPos(*문단_시작위치)
                        if 대체:
                            hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2] + 문단_위치(문단_시작위치, 시작))
                            텍스트_삽입(대체)
                        수정수 += 1
                    except Exception as e:
                        로그(f"공문 띄어쓰기 정리 실패(무시): {e}")
                        try:
                            hwp_run("Cancel")
                        except Exception:
                            pass
            finally:
                try:
                    hwp.SetPos(*문단_시작위치)
                except Exception:
                    pass
            return 수정수
        return bind_function(공문_띄어쓰기_정리_문단_처리, _docfit_namespace)
    if _docfit_symbol == '공문_띄어쓰기_전체_적용':
        def 공문_띄어쓰기_전체_적용():
            """자간 정리 작업에서 문서 전체에 공문 띄어쓰기 규정을 적용한다(서식 작업은 공백 정규화에서 한다)."""
            if hwp is None:
                return True
            if 중단_요청됨():
                return False
            순회_시작()
            수정수 = 0
            정체횟수 = 0
            while True:
                if 중단_요청됨():
                    return False
                시작위치 = hwp.GetPos()
                수정수 += 공문_띄어쓰기_정리_문단_처리()
                if not 범위_다음_문단으로_진행():
                    break
                if hwp.GetPos() == 시작위치:
                    정체횟수 += 1
                    if 정체횟수 >= 2:
                        break
                else:
                    정체횟수 = 0
            로그(f"공문 띄어쓰기 규정(끝 표시·붙임 2타, 날짜 표기) 적용: {수정수}건")
            return True
        return bind_function(공문_띄어쓰기_전체_적용, _docfit_namespace)
    if _docfit_symbol == '문장내_공백_정규화_전체_적용':
        def 문장내_공백_정규화_전체_적용():
            """괄호 안쪽 공백 + 단어 사이 쉼표 공백 + 단어 사이 연속 공백을 문서 전체에 적용한다."""
            if 중단_요청됨():
                return False

            로그("문장 내 공백 정규화 시작")

            # 1) 괄호 공백은 HWP 자체 AllReplace로 먼저 처리한다.
            #    문자 런/서식 경계를 넘는 경우에도 직접 좌표 삭제보다 안정적이다.
            # AllReplace는 문서 전체를 바꾸므로 쪽 범위를 지정한 작업에서는 쓰지 않고 문단 단위 보정만 한다.
            allreplace_실행수 = 0 if (한칸표_보호영역 or 디자인표_보호영역 or 쪽범위_사용중()) else 괄호_안쪽_공백_정리_AllReplace()

            # 2) 문단 단위 안전 보정 + 쉼표 공백 보정(앞 0칸 / 뒤 1칸) + 연속 공백 정리(2칸 이상 -> 1칸).
            #    기존 v1.7의 `list id == 0` 제한을 제거하여 접근 가능한 모든 문단에 적용한다.
            global _문단글_캐시
            _문단글_캐시 = {} if 알파_문단글_캐시_사용 else None
            try:
                return _문장내_공백_정규화_순회(allreplace_실행수)
            finally:
                _문단글_캐시 = None
        return bind_function(문장내_공백_정규화_전체_적용, _docfit_namespace)
    if _docfit_symbol == '_문장내_공백_정규화_순회':
        def _문장내_공백_정규화_순회(allreplace_실행수):
            순회_시작()
            괄호삭제수 = 0
            쉼표수정수 = 0
            콜론수정수 = 0
            연속공백수정수 = 0
            기호수정수 = 0
            연도따옴표수정수 = 0
            따옴표수정수 = 0
            작은따옴표수정수 = 0
            날짜구분자수정수 = 0
            공문수정수 = 0
            방문문단수 = 0
            정체횟수 = 0

            while True:
                if 중단_요청됨():
                    return False

                시작위치 = hwp.GetPos()
                방문문단수 += 1

                결과 = []
                for 규칙 in (문두_미음_기호_정리, 연도_따옴표_정리_문단_처리, 곧은따옴표_통일_문단_처리,
                           작은따옴표_통일_문단_처리, 날짜_구분자_정리_문단_처리, 괄호_안쪽_공백_정리_문단_처리,
                           쉼표_공백_정리_문단_처리, 콜론_공백_정리_문단_처리, 단어사이_연속공백_정리_문단_처리,
                           # 연속 공백을 줄인 뒤 공식 규정의 2타·날짜 띄어쓰기를 맞춘다(2025 행정업무운영 편람).
                           공문_띄어쓰기_정리_문단_처리):
                    try:
                        값 = 규칙() or 0
                    except Exception as e:
                        # 한 규칙이 실패해도(예: 숨은 글자로 위치를 맞출 수 없는 문단) 문서 처리를 멈추지 않는다.
                        로그(f"문장 내 공백 정리 규칙 건너뜀({getattr(규칙, '__name__', 규칙)}): {e}")
                        try:
                            hwp_run("Cancel")
                        except Exception:
                            pass
                        값 = 0
                    if 값:
                        _문단글_캐시_비우기()     # 글을 고쳤으면 다음 규칙은 새로 읽는다
                    결과.append(값)
                (기호, 연도, 따옴표, 작은, 날짜, 괄호, 쉼표, 콜론, 연속, 공문) = 결과
                기호수정수 += 기호
                연도따옴표수정수 += 연도
                따옴표수정수 += 따옴표
                작은따옴표수정수 += 작은
                날짜구분자수정수 += 날짜
                괄호삭제수 += 괄호
                쉼표수정수 += 쉼표
                콜론수정수 += 콜론
                연속공백수정수 += 연속
                공문수정수 += 공문

                if not 범위_다음_문단으로_진행():
                    break

                if hwp.GetPos() == 시작위치:
                    정체횟수 += 1
                    if 정체횟수 >= 2:
                        break
                else:
                    정체횟수 = 0

            로그(
                "문장 내 공백 정규화 완료 "
                f"(방문 문단 {방문문단수}개 / 괄호 AllReplace {allreplace_실행수}회 / "
                f"문두 ㅁ→□ {기호수정수}건 / 연도 따옴표 {연도따옴표수정수}건 / 곧은따옴표 {따옴표수정수}건 / "
                f"작은따옴표 {작은따옴표수정수}건 / 날짜 구분자 {날짜구분자수정수}건 / "
                f"괄호 후방삭제 {괄호삭제수}자 / 쉼표 공백 {쉼표수정수}건 / 콜론 공백 {콜론수정수}건 / 연속 공백 {연속공백수정수}건 / "
                f"공문 띄어쓰기 규정 {공문수정수}건)"
            )
            return True
        return bind_function(_문장내_공백_정규화_순회, _docfit_namespace)
    if _docfit_symbol == '괄호_안쪽_공백_정리_전체_적용':
        def 괄호_안쪽_공백_정리_전체_적용():
            return 문장내_공백_정규화_전체_적용()
        return bind_function(괄호_안쪽_공백_정리_전체_적용, _docfit_namespace)
    if _docfit_symbol == '문장부호_뒤_공백_보정_문단_처리':
        def 문장부호_뒤_공백_보정_문단_처리():
            if 현재_한칸표인가():
                return 0
            text = 현재문단_텍스트()
            if not text:
                return False
            마커_끝 = 문장부호_마커_끝위치(text)
            조치 = marker_space_fix(text, 마커_끝)
            if 조치 is None:
                return False

            문단_시작위치 = hwp.GetPos()
            try:
                if 조치 == "replace":
                    # 탭·전각공백 등 다른 공백류가 이미 있으면 지우고 표준 반각
                    # 공백 한 칸으로 다시 넣는다(그냥 앞에 삽입만 하면 두 공백이
                    # 함께 남는다).
                    if 문단_범위_선택(문단_시작위치, 마커_끝, 마커_끝 + 1) is False:
                        raise RuntimeError("공백류 문자 선택 실패")
                    if hwp_run("Delete") is False:
                        raise RuntimeError("공백류 문자 삭제 실패")
                    hwp.SetPos(*문단_시작위치)
                hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2] + 문단_위치(문단_시작위치, 마커_끝))
                텍스트_삽입(" ")
                return True
            except Exception as e:
                로그(f"문장부호 뒤 공백 보정 실패(무시): {e}")
                return False
            finally:
                try:
                    hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2])
                except Exception:
                    pass
        return bind_function(문장부호_뒤_공백_보정_문단_처리, _docfit_namespace)
    if _docfit_symbol == '문장부호_뒤_공백_보정_전체_적용':
        def 문장부호_뒤_공백_보정_전체_적용():
            if 중단_요청됨():
                return False
            로그("문장부호 뒤 공백 보정 시작")
            순회_시작()
            총_적용_횟수 = 0

            while True:
                if 중단_요청됨():
                    return False
                if 문장부호_뒤_공백_보정_문단_처리():
                    총_적용_횟수 += 1
                if not 범위_다음_문단으로_진행():
                    break

            로그(f"문장부호 뒤 공백 보정 완료 (총 {총_적용_횟수}건)")
            return True
        return bind_function(문장부호_뒤_공백_보정_전체_적용, _docfit_namespace)
    if _docfit_symbol == '문단글_캐시_구간':
        def 문단글_캐시_구간(함수):
            """함수가 도는 동안만 문단 글 캐시를 켠다(이미 켜져 있으면 그대로 쓴다)."""
            def 감싼(*args, **kwargs):
                global _문단글_캐시
                if not 알파_문단글_캐시_확대_사용 or _문단글_캐시 is not None:
                    return 함수(*args, **kwargs)
                _문단글_캐시 = {}
                try:
                    return 함수(*args, **kwargs)
                finally:
                    _문단글_캐시 = None
            감싼.__name__ = getattr(함수, '__name__', '문단글_캐시_구간')
            return 감싼
        return bind_function(문단글_캐시_구간, _docfit_namespace)
    if _docfit_symbol == '_문단글_캐시_비우기':
        def _문단글_캐시_비우기():
            if _문단글_캐시 is not None:
                _문단글_캐시.clear()
        return bind_function(_문단글_캐시_비우기, _docfit_namespace)
    if _docfit_symbol == '현재문단_텍스트':
        def 현재문단_텍스트():
            글 = _현재문단_텍스트_본체()
            global _최근_문단글
            try:
                _최근_문단글 = (tuple(hwp.GetPos()[:2]), 글)
            except Exception:
                _최근_문단글 = None
            return 글
        return bind_function(현재문단_텍스트, _docfit_namespace)
    if _docfit_symbol == '_문단_위치표_계산':
        def _문단_위치표_계산(문단_시작위치, 글):
            """[읽은 글 i번째 글자의 한/글 위치(시작 기준)…, 문단 끝 위치]. 숨은 글자가 없으면 None, 맞출 수 없으면 '불일치'."""
            본문 = (글 or '').rstrip('\r\n')
            hwp.SetPos(*문단_시작위치)
            hwp_run('MoveParaEnd')
            끝 = hwp.GetPos()
            if 끝[0] != 문단_시작위치[0] or 끝[1] != 문단_시작위치[1]:
                return '불일치'
            길이 = 끝[2] - 문단_시작위치[2]
            if 길이 == len(본문):
                return None
            if 길이 < len(본문) or 길이 > len(본문) + 200:
                return '불일치'
            보이는 = []
            try:
                for off in range(길이):
                    hwp.SelectText(문단_시작위치[1], 문단_시작위치[2] + off, 문단_시작위치[1], 문단_시작위치[2] + off + 1)
                    ch = 현재선택영역_텍스트()
                    hwp_run('Cancel')
                    if ch:
                        보이는.append((off, ch[0]))
            finally:
                hwp.SetPos(*문단_시작위치)
            표, j = [], 0
            for c in 본문:
                while j < len(보이는) and 보이는[j][1] != c:
                    j += 1
                if j >= len(보이는):
                    return '불일치'
                표.append(보이는[j][0])
                j += 1
            표.append(길이)
            return 표
        return bind_function(_문단_위치표_계산, _docfit_namespace)
    if _docfit_symbol == '문단_위치':
        def 문단_위치(문단_시작위치, offset, 끝쪽=False):
            """읽은 문단 글 위치 → 한/글 위치(문단 시작 기준). 끝쪽이면 범위 끝(앞 글자 바로 뒤)으로 바꾼다.

            위치표를 만들 수 없는 문단이면 RuntimeError(고치지 않음)."""
            if _최근_문단글 is None or _최근_문단글[0] != tuple(문단_시작위치[:2]) or 문단_시작위치[2] != 0:
                return offset
            키 = tuple(문단_시작위치)
            글 = _최근_문단글[1]
            저장 = _문단_위치표_저장.get(키)
            if 저장 is None or 저장[0] != 글:
                표 = _문단_위치표_계산(문단_시작위치, 글)
                _문단_위치표_저장.clear()
                _문단_위치표_저장[키] = (글, 표)
            else:
                표 = 저장[1]
            if 표 is None:
                return offset
            if 표 == '불일치':
                raise RuntimeError('문단 글과 한/글 위치가 맞지 않아 이 문단은 고치지 않습니다(숨은 글자)')
            if 끝쪽 and offset > 0:
                # 범위 끝은 마지막 글자 바로 뒤(그 뒤 숨은 글자는 범위에 넣지 않는다).
                return 표[offset - 1] + 1 if offset - 1 < len(표) - 1 else 표[-1]
            return 표[min(offset, len(표) - 1)]
        return bind_function(문단_위치, _docfit_namespace)
    if _docfit_symbol == '_현재문단_텍스트_본체':
        def _현재문단_텍스트_본체():
            if _문단글_캐시 is not None:
                try:
                    hwp.Run("MoveParaBegin")      # 원래 함수처럼 커서를 문단 시작에 둔다
                    키 = tuple(hwp.GetPos()[:2])
                    저장 = _문단글_캐시.get(키)
                    if 저장 is not None and 저장[0] == _문서_편집_세대:
                        return 저장[1]
                    세대 = _문서_편집_세대
                    글, 성공 = _현재문단_텍스트_읽기_상태()
                    if not 성공:
                        # 일시적 읽기 실패는 빈 문단으로 기억하지 않고 한 번 더 읽는다(Beta 12 리뷰 R4).
                        글, 성공 = _현재문단_텍스트_읽기_상태()
                    if 성공:
                        _문단글_캐시[키] = (세대, 글)
                    return 글
                except Exception:
                    return _현재문단_텍스트_읽기()
            return _현재문단_텍스트_읽기()
        return bind_function(_현재문단_텍스트_본체, _docfit_namespace)
    if _docfit_symbol == '_현재문단_텍스트_읽기':
        def _현재문단_텍스트_읽기():
            return _현재문단_텍스트_읽기_상태()[0]
        return bind_function(_현재문단_텍스트_읽기, _docfit_namespace)
    if _docfit_symbol == '_현재문단_텍스트_읽기_상태':
        def _현재문단_텍스트_읽기_상태():
            """(문단 글, 읽기 성공 여부). 실패하면 ("", False) — 실제 빈 문단과 구별한다."""
            try:
                hwp.Run("MoveParaBegin")
                문단시작위치 = hwp.GetPos()
                hwp.Run("MoveSelParaEnd")
                hwp.InitScan(option=None, Range=0xff, spara=None, spos=None, epara=None, epos=None)
                try:
                    _, text = hwp.GetText()
                finally:
                    hwp.ReleaseScan()
                hwp.Run("Cancel")
                hwp.SetPos(문단시작위치[0], 문단시작위치[1], 문단시작위치[2])
                return text or "", True
            except Exception:
                try:
                    hwp.Run("Cancel")
                except Exception:
                    pass
                return "", False
        return bind_function(_현재문단_텍스트_읽기_상태, _docfit_namespace)
    if _docfit_symbol == '실제_엔터_포함':
        def 실제_엔터_포함(text):
            return ("\n" in text or "\r" in text) if text else False
        return bind_function(실제_엔터_포함, _docfit_namespace)
    if _docfit_symbol == '두_위치_사이_줄바꿈_문자인가':
        def 두_위치_사이_줄바꿈_문자인가(시작pos, 끝pos):
            try:
                hwp.SetPos(시작pos[0], 시작pos[1], 시작pos[2])
                hwp_run("MoveSelRight")
                hwp.InitScan(option=None, Range=0xff, spara=None, spos=None, epara=None, epos=None)
                try:
                    _, text = hwp.GetText()
                finally:
                    hwp.ReleaseScan()
                hwp_run("Cancel")
                hwp.SetPos(시작pos[0], 시작pos[1], 시작pos[2])
                return 실제_엔터_포함(text)
            except Exception:
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
                return False
        return bind_function(두_위치_사이_줄바꿈_문자인가, _docfit_namespace)
    if _docfit_symbol == '문장부호_대상문장인가':
        def 문장부호_대상문장인가():
            text = 현재문단_텍스트()
            return bool(text and 문장부호_시작인가(text))
        return bind_function(문장부호_대상문장인가, _docfit_namespace)
    if _docfit_symbol == '현재_화면줄_텍스트':
        def 현재_화면줄_텍스트():
            try:
                hwp_run("MoveLineBegin")
                줄시작위치 = hwp.GetPos()
                hwp_run("MoveSelLineEnd")
                hwp.InitScan(option=None, Range=0xff, spara=None, spos=None, epara=None, epos=None)
                try:
                    _, text = hwp.GetText()
                finally:
                    hwp.ReleaseScan()
                hwp_run("Cancel")
                hwp.SetPos(줄시작위치[0], 줄시작위치[1], 줄시작위치[2])
                return text or ""
            except Exception:
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
                return ""
        return bind_function(현재_화면줄_텍스트, _docfit_namespace)
    if _docfit_symbol == '다음_줄_판정':
        def 다음_줄_판정(현재줄끝위치):
            hwp_run("MoveNextChar")
            다음위치 = hwp.GetPos()
            if 다음위치 == 현재줄끝위치:
                return "없음", 다음위치
            if 다음위치[0] != 현재줄끝위치[0] or 다음위치[1] != 현재줄끝위치[1]:
                return "끝남", 다음위치
            if 두_위치_사이_줄바꿈_문자인가(현재줄끝위치, 다음위치):
                return "끝남", 다음위치
            return "계속", 다음위치
        return bind_function(다음_줄_판정, _docfit_namespace)
    if _docfit_symbol == '줄_목록_수집':
        def 줄_목록_수집(시작위치, 최대줄수=None):
            if 최대줄수 is None:
                최대줄수 = 문장부호_최대_처리_줄수
            줄목록 = []
            hwp.SetPos(시작위치[0], 시작위치[1], 시작위치[2])
            hwp_run("MoveLineBegin")
            앵커 = hwp.GetPos()

            while len(줄목록) < 최대줄수:
                if 중단_요청됨():
                    return 줄목록, True
                hwp.SetPos(앵커[0], 앵커[1], 앵커[2])
                줄텍스트 = 현재_화면줄_텍스트()
                if not 줄텍스트:
                    return 줄목록, True
                줄목록.append((앵커, 줄텍스트))

                hwp.SetPos(앵커[0], 앵커[1], 앵커[2])
                hwp_run("MoveLineEnd")
                줄끝 = hwp.GetPos()
                분류, 다음위치 = 다음_줄_판정(줄끝)
                if 분류 in ("없음", "끝남"):
                    return 줄목록, True
                앵커 = 다음위치

            return 줄목록, False
        return bind_function(줄_목록_수집, _docfit_namespace)
    if _docfit_symbol == '문장부호_줄병합_시도':
        def 문장부호_줄병합_시도():
            """짧은 마지막 줄을 앞줄로 당긴다. 조정할 본문이 없는 줄(문두 보호)은 건너뛴다."""
            return _문두보호_줄건너뜀(_문장부호_줄병합_시도_본체)
        return bind_function(문장부호_줄병합_시도, _docfit_namespace)
    if _docfit_symbol == '_문장부호_줄병합_시도_본체':
        def _문장부호_줄병합_시도_본체():
            if 현재_한칸표인가():
                return True
            if 중단_요청됨():
                return False
            원래위치 = hwp.GetPos()
            try:
                if not 문장부호_대상문장인가():
                    return True

                hwp_run("MoveLineBegin")
                줄목록, 끝까지_확인됨 = 줄_목록_수집(hwp.GetPos())
                if len(줄목록) < 2 or not 끝까지_확인됨:
                    return True

                마지막줄_시작, 마지막줄_텍스트 = 줄목록[-1]
                if len(마지막줄_텍스트) > 문장부호_2줄_기준글자수:
                    return True

                문장부호_통계["대상"] += 1
                압축대상_시작, _ = 줄목록[-2]
                조정횟수 = 0
                최대조정 = 40
                해결됨 = False
                새_줄목록 = 줄목록

                while 조정횟수 < 최대조정:
                    if 중단_요청됨():
                        return False
                    hwp.SetPos(압축대상_시작[0], 압축대상_시작[1], 압축대상_시작[2])
                    hwp_run("MoveLineEnd")
                    hwp_run("MoveSelLineBegin")
                    hwp_run("CharShapeSpacingDecrease")
                    색상_적용_현재선택()
                    hwp_run("Cancel")
                    조정횟수 += 1

                    새_줄목록, 새_끝까지_확인됨 = 줄_목록_수집(원래위치)
                    if not 새_끝까지_확인됨:
                        break
                    if len(새_줄목록) < len(줄목록):
                        해결됨 = True
                        break

                if 해결됨:
                    문장부호_통계["성공"] += 1
                    if len(새_줄목록) >= 2:
                        hwp.SetPos(원래위치[0], 원래위치[1], 원래위치[2])
                        문장부호_줄병합_시도()
                else:
                    문장부호_통계["실패"] += 1
                    검수_문제_기록(현재_처리파일, 줄목록[0][1].strip() + " / " + 마지막줄_텍스트.strip())
                return True
            finally:
                try:
                    hwp.SetPos(원래위치[0], 원래위치[1], 원래위치[2])
                    hwp.Run("MoveParaEnd")
                except Exception:
                    pass
        return bind_function(_문장부호_줄병합_시도_본체, _docfit_namespace)
    if _docfit_symbol == '본문_문장부호_처리':
        def 본문_문장부호_처리():
            hwp_run("MoveDocBegin")
            끝위치 = 끝위치추출()
            순회_시작()
            직전위치 = None
            정체횟수 = 0
            검사문단 = None

            while hwp.GetPos() != 끝위치:
                if 중단_요청됨():
                    return False
                현재위치 = hwp.GetPos()
                if 쪽범위_끝지남(현재위치):
                    return True
                if (_알파_일괄서식_문서 and 현재위치[0] == 0
                        and tuple(현재위치[:2]) != 검사문단):
                    검사문단 = tuple(현재위치[:2])
                    if _알파_한줄문단인가(현재위치):
                        hwp_run('MoveParaEnd')
                        문단끝 = hwp.GetPos()
                        hwp_run('MoveNextChar')
                        if hwp.GetPos() == 문단끝:
                            return True
                        continue
                if ((not 쪽범위_안인가(현재위치)) or (not 재검사_대상인가(현재위치))
                        or 표셀_자간_제외인가()):
                    # 작업 쪽 범위 밖, 2차 이후 재검사 대상이 아닌 문단, '표 안 문장 제외'인
                    # 표 셀이면 줄 병합을 하지 않고 넘어간다.
                    try:
                        hwp_run("MoveParaEnd")
                        hwp_run("MoveNextChar")
                    except Exception:
                        pass
                    if hwp.GetPos() == 현재위치:
                        return True
                    직전위치 = None
                    정체횟수 = 0
                    continue
                if 현재위치 == 직전위치:
                    정체횟수 += 1
                    if 정체횟수 == 1:
                        try:
                            hwp_run("MoveParaEnd")
                            hwp_run("MoveNextChar")
                        except Exception:
                            pass
                        직전위치 = 현재위치
                        continue
                    return True
                else:
                    정체횟수 = 0
                직전위치 = 현재위치
                문장부호_줄병합_시도()
                hwp_run("MoveLineEnd")
                hwp_run("MoveNextChar")
            return True
        return bind_function(본문_문장부호_처리, _docfit_namespace)
    if _docfit_symbol == '현재_셀_주소_행번호':
        def 현재_셀_주소_행번호():
            """KeyIndicator의 '(A1)' 또는 'A1' 셀주소를 파싱한다."""
            try:
                정보 = hwp.KeyIndicator()
                if not 정보:
                    return None, None
                원문 = str(정보[-1]).strip()
                일치 = re.search(r"\(?([A-Za-z]+)(\d+)\)?", 원문)
                if not 일치:
                    return None, None
                주소 = f"{일치.group(1).upper()}{일치.group(2)}"
                return 주소, int(일치.group(2))
            except Exception:
                return None, None
        return bind_function(현재_셀_주소_행번호, _docfit_namespace)
    if _docfit_symbol == '현재_셀_행번호':
        def 현재_셀_행번호():
            _, 행번호 = 현재_셀_주소_행번호()
            return 행번호
        return bind_function(현재_셀_행번호, _docfit_namespace)
    if _docfit_symbol == '현재_한칸표인가':
        def 현재_한칸표인가():
            return hwp is not None and hwp.GetPos()[0] in 한칸표_보호영역
        return bind_function(현재_한칸표인가, _docfit_namespace)
    if _docfit_symbol == '현재_표_키':
        def 현재_표_키():
            """캐럿이 있는 칸을 담은 표 컨트롤의 고유 키(앵커 위치). 표가 아니면 None.

            예외가 나면 False(판정 불가)를 돌려 호출자가 예전 방식으로 대신하게 한다.
            """
            try:
                ctrl = hwp.ParentCtrl
                if ctrl is None or ctrl.CtrlID != 'tbl':
                    return None
                anchor = ctrl.GetAnchorPos(0)
                return (anchor.Item('List'), anchor.Item('Para'), anchor.Item('Pos'))
            except Exception:
                return False
        return bind_function(현재_표_키, _docfit_namespace)
    if _docfit_symbol == '표칸_묶음_수집':
        def 표칸_묶음_수집():
            """표마다 [(area, 셀주소, 행번호), ...] 목록(문서 순서). 판정 불가면 None."""
            묶음 = 표칸_묶음_키별()
            return None if 묶음 is None else list(묶음.values())
        return bind_function(표칸_묶음_수집, _docfit_namespace)
    if _docfit_symbol == '표칸_묶음_키별':
        def 표칸_묶음_키별():
            """{표 키(앵커 리스트, 문단, 위치): [(area, 셀주소, 행번호), ...]}. 판정 불가면 None.

            예전에는 'A1 칸이 나오면 새 표'로 묶었는데, 실측(2026-09-25, 표 서식 문서)에서
            가운데 열이 세로 병합된 표가 세 조각으로 나뉘어 셀 너비 맞춤이 엉뚱한 열에
            너비를 넣었다. 칸을 담은 표 컨트롤(ParentCtrl)의 앵커 위치로 묶는다.
            """
            묶음 = {}
            area = 1
            while True:
                if 중단_요청됨():
                    break
                area += 1
                try:
                    hwp.SetPos(area, 0, 0)
                except Exception:
                    break
                if hwp.GetPos()[0] != area:
                    break
                키 = 현재_표_키()
                if 키 is False:
                    return None
                if 키 is None:
                    continue
                주소, 행번호 = 현재_셀_주소_행번호()
                if 주소 is None:
                    continue
                묶음.setdefault(키, []).append((area, 주소, 행번호))
            return 묶음
        return bind_function(표칸_묶음_키별, _docfit_namespace)
    if _docfit_symbol == '한칸표_영역_목록':
        def 한칸표_영역_목록():
            """문서의 컨트롤 리스트를 훑어 한 셀로만 된 표의 영역 번호를 찾는다.

            칸을 담은 표 컨트롤 기준으로 묶어(표칸_묶음_수집) 칸이 A1 하나뿐인 표를
            한 칸 표로 판정한다. 표 컨트롤을 읽지 못하는 환경이면 예전 규칙(다음 A1
            또는 비표 영역이 나오기 전까지를 한 표로 봄)으로 대신한다.
            """
            묶음 = 표칸_묶음_수집()
            if 묶음 is not None:
                return {칸들[0][0] for 칸들 in 묶음 if len(칸들) == 1 and 칸들[0][1] == "A1"}
            한칸영역 = set()
            현재표 = []

            def 표_확정():
                nonlocal 현재표
                if len(현재표) == 1 and 현재표[0][1] == "A1":
                    한칸영역.add(현재표[0][0])
                현재표 = []

            area = 1
            while True:
                area += 1
                try:
                    hwp.SetPos(area, 0, 0)
                except Exception:
                    break
                if hwp.GetPos()[0] != area:
                    break
                주소, _ = 현재_셀_주소_행번호()
                if 주소 is None:
                    표_확정()
                    continue
                if 주소 == "A1" and 현재표:
                    표_확정()
                현재표.append((area, 주소))
            표_확정()
            return 한칸영역
        return bind_function(한칸표_영역_목록, _docfit_namespace)
    if _docfit_symbol == '디자인표_영역_목록':
        def 디자인표_영역_목록():
            """사용자가 꾸민 표(빈 점선 칸이 있고 글 칸이 모두 첫 행인 장식 표, '(단위: 개소)' 같은 캡션이 달린 표)의
            칸 영역 번호. 이런 표는 문서 디자인이라 서식·자간 초기화·자간 조정·찾아 바꾸기를 하지 않는다
            (사용자 규칙, 2026-10-15). 현재 문서를 HWPX로 한 번 저장해 구조로 판별한다(서식표_보호영역_조사와 같은 방식).
            표가 없는 문서는 저장하지 않는다(스냅샷 저장은 문서마다 몇 초가 들고 편집 문서를 임시 파일로 바꾼다).
            """
            global 디자인표_확인
            디자인표_확인 = []
            if not _문서에_표_있음():
                return set()
            return 서식표_보호영역_조사(장식만=True)
        return bind_function(디자인표_영역_목록, _docfit_namespace)
    if _docfit_symbol == '디자인표_보호영역_갱신':
        def 디자인표_보호영역_갱신():
            """디자인표_보호영역(한/글 목록 번호)이 아직 같은 표를 가리키는지 확인하고, 어긋났으면 다시 조사한다.

            목록 번호는 문서 순서의 subList 순번이라 처리 중 표·글상자가 생기거나 없어지면 밀린다. 그대로 쓰면
            일반 표가 서식을 잃고 꾸민 표는 보호가 풀린다. 표마다 기억한 칸 글이 그 자리에 있는지만 보므로 빠르다.
            """
            global 디자인표_보호영역
            if not 디자인표_보호영역:
                return 디자인표_보호영역
            try:
                위치 = hwp.GetPos()
            except Exception:
                위치 = None
            if not all(_서식표_칸_확인(*확인) for _, 확인 in 디자인표_확인):
                로그("사용자가 꾸민 표의 칸 위치가 바뀌어 보호 영역을 다시 조사합니다.")
                디자인표_보호영역 = 디자인표_영역_목록()
            else:
                hwp_run("Cancel")
                if 위치 is not None:
                    try:
                        hwp.SetPos(*위치)
                    except Exception:
                        pass
            return 디자인표_보호영역
        return bind_function(디자인표_보호영역_갱신, _docfit_namespace)
    if _docfit_symbol == '_문서에_표_있음':
        def _문서에_표_있음():
            """문서에 표 컨트롤이 하나라도 있는가(컨트롤 목록만 훑어 빠르다). 읽지 못하면 있다고 본다."""
            try:
                ctrl = hwp.HeadCtrl
                남은수 = 100000   # 컨트롤 목록이 끝나지 않는 비정상 상황 방지
                while ctrl and 남은수 > 0:
                    남은수 -= 1
                    if ctrl.CtrlID == 'tbl':
                        return True
                    ctrl = ctrl.Next
                return False
            except Exception:
                return True
        return bind_function(_문서에_표_있음, _docfit_namespace)
    if _docfit_symbol == '표_헤더서식_현재셀_처리':
        def 표_헤더서식_현재셀_처리():
            """현재 셀의 전체 텍스트에 헤더/본문 폰트·크기·굵기를 적용한다."""
            if 현재_한칸표인가():
                return False
            _, 행번호 = 현재_셀_주소_행번호()
            if 행번호 is None:
                return False

            try:
                hwp_run("MoveListBegin")
                hwp_run("MoveSelListEnd")
                if 행번호 == 1:
                    문자모양_적용_현재선택(
                        폰트=표_헤더서식_헤더_폰트,
                        크기_pt=표_헤더서식_헤더_크기,
                        굵게=표_헤더서식_헤더_굵게,
                    )
                else:
                    문자모양_적용_현재선택(
                        폰트=표_헤더서식_본문_폰트,
                        크기_pt=표_헤더서식_본문_크기,
                        # 본문 셀의 기존 굵은 강조는 해제하지 않는다.
                        굵게=True if 표_헤더서식_본문_굵게 else None,
                    )
                hwp_run("Cancel")
                hwp_run("MoveListBegin")
                return True
            except Exception as e:
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
                로그(f"표 셀 문자서식적용 실패(무시): {e}")
                return False
        return bind_function(표_헤더서식_현재셀_처리, _docfit_namespace)
    if _docfit_symbol == '표_헤더서식_현재줄_처리':
        def 표_헤더서식_현재줄_처리():
            return 표_헤더서식_현재셀_처리()
        return bind_function(표_헤더서식_현재줄_처리, _docfit_namespace)
    if _docfit_symbol == '표_헤더서식_표단위_처리':
        def 표_헤더서식_표단위_처리(칸들):
            """표 하나(표칸_묶음_수집의 칸 목록)에 본문·머리글 서식을 한 번에 적용한다.

            실측(2026-09-26): 통계표가 많은 수출입동향(표 칸 5,052개)은 칸마다 글자를
            선택해 적용하느라 표 서식에만 14분이 걸렸다. 표 전체를 칸 블록으로 골라
            (F5 세 번 = TableCellBlock + TableCellBlockExtend×2) 본문 서식을 한 번에 주고,
            머리글 서식은 칸 주소가 1행인 칸에만 칸마다 다시 준다(칸마다 적용하던 예전 방식과
            결과가 같다). 첫 행 선택(TableCellBlockRow)은 A1이 두 행에 걸쳐 병합된 표에서
            둘째 행까지 골라 결과가 달라졌으므로 쓰지 않는다(실측, 표 서식 문서 2개 표).
            성공하면 칸 수, A1 칸이 없거나 실패하면 None(호출자가 칸마다 적용으로 대신한다).
            """
            첫칸 = next((area for area, 주소, _ in 칸들 if 주소 == "A1"), None)
            if 첫칸 is None:
                return None
            try:
                hwp.SetPos(첫칸, 0, 0)
                hwp_run("Cancel")
                for 명령 in ("TableCellBlock", "TableCellBlockExtend", "TableCellBlockExtend"):
                    hwp_run(명령)
                문자모양_적용_현재선택(
                    폰트=표_헤더서식_본문_폰트,
                    크기_pt=표_헤더서식_본문_크기,
                    # 본문 칸의 기존 굵은 강조는 해제하지 않는다.
                    굵게=True if 표_헤더서식_본문_굵게 else None,
                )
                hwp_run("Cancel")
                for area, _, 행 in 칸들:
                    if 행 != 1:
                        continue
                    hwp.SetPos(area, 0, 0)
                    hwp_run("MoveListBegin")
                    hwp_run("MoveSelListEnd")
                    문자모양_적용_현재선택(
                        폰트=표_헤더서식_헤더_폰트,
                        크기_pt=표_헤더서식_헤더_크기,
                        굵게=표_헤더서식_헤더_굵게,
                    )
                    hwp_run("Cancel")
                return len(칸들)
            except Exception as e:
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
                로그(f"표 단위 서식적용 실패(칸마다 적용으로 대신): {e}")
                return None
        return bind_function(표_헤더서식_표단위_처리, _docfit_namespace)
    if _docfit_symbol == '서식표_영역_목록':
        def 서식표_영역_목록(hwpx경로, 장식만=False):
            """HWPX의 제목·중제목·붙임 서식 표마다 (칸 목록 번호 목록, 확인할 (목록 번호, 문단 순번, 글))을 돌려준다.

            한/글의 목록 번호는 문서 순서의 subList 순번 + 2다(_서식통일_표모형 참고). 준말 변환이 만든
            제목 표는 날짜·담당자 칸이 비어 있으므로 빈 정보 칸도 제목 표로 본다. 확인할 글은 표에서
            가장 긴 글 문단이다(중제목 번호처럼 짧은 글로 확인하면 다른 표와 헷갈릴 수 있다).
            """
            from docfit_core.style_inventory import _sections
            from docfit_core.table_style import is_protected_table
            with open_hwpx_safely(hwpx경로) as z:
                구역들 = [safe_xml_fromstring(z.read(name)) for name in _sections(z)]
            목록번호 = {}
            for root in 구역들:
                for item in root.iter():
                    if 제목_xml이름(item) == 'subList':
                        목록번호[id(item)] = len(목록번호) + 2
            결과 = []
            for root in 구역들:
                for table in (t for t in root.iter() if 제목_xml이름(t) == 'tbl'):
                    장식 = is_protected_table(table)
                    if 장식만 and not 장식:
                        continue
                    if not (장식 or 제목_유형판별(table, 빈칸허용=True) or 중제목_글칸들(table) or 붙임_유형판별(table)):
                        continue
                    영역들, 확인 = [], None
                    # Protect descendant cells and caption lists together with
                    # the enclosing design, including nested ordinary tables.
                    sublists = ([x for x in table.iter() if 제목_xml이름(x) == 'subList'] if 장식
                                else [제목_자식(cell, 'subList') for cell in 제목_셀들(table)])
                    for sub in sublists:
                        if sub is None or id(sub) not in 목록번호:
                            continue
                        영역들.append(목록번호[id(sub)])
                        for 순번, p in enumerate(x for x in sub if 제목_xml이름(x) == 'p'):
                            글 = ''.join(_서식통일_run_text(run)[0] for run in p if 제목_xml이름(run) == 'run')
                            if len(글.strip()) > len(확인[2].strip() if 확인 else ''):
                                확인 = (목록번호[id(sub)], 순번, 글)
                    if 영역들 and 확인:
                        결과.append((영역들, 확인))
            return 결과
        return bind_function(서식표_영역_목록, _docfit_namespace)
    if _docfit_symbol == '서식표_보호영역_조사':
        def 서식표_보호영역_조사(묶음=None, 장식만=False):
            """표 머리글·본문 서식에서 뺄 제목·중제목·붙임 서식 표 칸의 목록 번호 집합.

            실측(2026-09-30): 2×2·2행1열 제목 표와 1행 붙임 표는 한 칸 표가 아니라서 1행이 머리글
            서식(한컴돋움 13pt)으로 덮여 제목 27pt·붙임 17pt가 사라졌다. 현재 문서를 HWPX로 스냅샷
            저장해 구조로 판별하고, 한/글에서 칸 글이 같은지 확인된 표만 돌려준다. 묶음(표칸_묶음_키별)이
            있고 서식 표 모양(칸 2~3개)의 표가 없으면 저장하지 않는다. 판별 실패·위치 불일치는
            보호 대상이 없다는 뜻이 아니므로 예외로 작업을 중단한다.
            스냅샷은 지금 편집 문서가 되어 한/글이 잡고 있으므로 다음 실행 때 정리한다.
            """
            # 장식 표·캡션 달린 표는 디자인표_영역_목록(장식만=True)이 따로 보호한다. 여기서는 예전처럼
            # 서식 표 모양(칸 2~3개)의 표가 없으면 스냅샷을 만들지 않는다.
            모양 = ({'A1', 'A2', 'B2'}, {'A1', 'A2'}, {'A1', 'B1'}, {'A1', 'B1', 'C1'})
            if not 장식만 and 묶음 is not None and not any({주소 for _, 주소, _ in 칸들} in 모양 for 칸들 in 묶음.values()):
                return set()
            folder = Path(tempfile.mkdtemp(prefix='hwp_table_guard_'))
            try:
                경로 = _제목_임시hwpx_저장(folder / 'tables.hwpx')
                표들 = 서식표_영역_목록(경로, 장식만=True) if 장식만 else 서식표_영역_목록(경로)
            except Exception as e:
                shutil.rmtree(folder, ignore_errors=True)
                raise RuntimeError("표의 보호 영역을 확인하지 못해 문서 수정을 중단합니다.") from e
            보호, 확인됨 = set(), []
            for 영역들, 확인 in 표들:
                # 목록 번호가 어긋나면 다른 표를 빼게 되므로, 칸 문단 글자가 HWPX와 같은지 확인한다.
                if _서식표_칸_확인(*확인):
                    보호.update(영역들)
                    확인됨.append((영역들, 확인))
                else:
                    hwp_run("Cancel")
                    raise RuntimeError("표의 칸 위치가 일치하지 않아 문서 수정을 중단합니다.")
            hwp_run("Cancel")
            if 장식만:
                global 디자인표_확인
                디자인표_확인 = 확인됨   # 디자인표_보호영역_갱신이 번호가 밀렸는지 볼 때 쓴다
            return 보호
        return bind_function(서식표_보호영역_조사, _docfit_namespace)
    if _docfit_symbol == '_서식표_칸_확인':
        def _서식표_칸_확인(area, 순번, 글):
            """한/글 목록 area의 순번째 문단 글이 HWPX에서 읽은 글과 같은가(목록 번호가 같은 칸을 가리키는지)."""
            try:
                hwp.SetPos(area, 순번, 0)
                return (tuple(hwp.GetPos()[:2]) == (area, 순번)
                        and _서식통일_공백제거(현재문단_텍스트()) == _서식통일_공백제거(글))
            except Exception:
                return False
        return bind_function(_서식표_칸_확인, _docfit_namespace)
    if _docfit_symbol == '표_헤더서식_전체_적용':
        def 표_헤더서식_전체_적용():
            """표 안의 각 셀에 표준 문자서식을 적용한다.

            v1.11: 기존에는 HeadCtrl/Next로 표 컨트롤을 찾은 뒤
            ``hwp.SelectCtrl(ctrl.GetCtrlInstID(), 1)``로 첫 셀에 진입하려 했으나,
            이 메서드는 이 스크립트가 사용하는 win32com 원시 COM 객체에는 없어
            모든 표에서 예외가 발생하며 표 서식적용이 통째로 실패했다
            ("표 N 첫 셀 진입 실패(무시): HwpFrame.HwpObject.SelectCtrl").
            표/글상자 등 각 컨트롤 내부는 문서 안에서 고유한 리스트 번호를
            가지므로, ``컨트롤_내부_자간조정()``과 동일하게 리스트 번호를
            1씩 늘려가며 SetPos로 직접 진입하는, 이미 검증된 방식으로 대체한다.
            표가 아닌 영역(글상자 등)은 ``표_헤더서식_현재셀_처리()``가 셀
            주소를 못 찾으면 그대로 건너뛰므로 안전하다. 제목·중제목·붙임 서식 표는
            데이터 표가 아니므로 건너뛴다(서식표_보호영역_조사).
            """
            if 중단_요청됨():
                return False

            로그("표 헤더/본문 서식적용 시작")
            셀수 = 0
            실패수 = 0
            방문영역수 = 0
            한칸표영역 = 한칸표_영역_목록()
            제외수 = 0
            서식표_제외수 = 0

            # 표 단위 일괄 적용(쪽 범위를 지정하면 범위 밖 칸을 건드리지 않도록 칸마다 적용).
            묶음 = 표칸_묶음_키별() if 표_서식_표단위_사용 and not 쪽범위_사용중() else None
            서식표영역 = 서식표_보호영역_조사(묶음) | 디자인표_보호영역_갱신()   # 사용자가 꾸민 장식 표는 건드리지 않는다
            if 묶음 is not None:
                처리된 = set()
                # 칸 안에 다른 표(한 칸 제목 상자 등)가 든 표는 표 단위 선택이 안쪽 표 글자까지
                # 바꿔 결과가 달라지므로(실측: 수출입동향) 칸마다 적용하는 예전 방식으로 둔다.
                안쪽표_리스트 = {키[0] for 키 in 묶음}
                for 칸들 in 묶음.values():
                    if 중단_요청됨():
                        return False
                    if len(칸들) == 1 and 칸들[0][0] in 한칸표영역:
                        continue
                    if any(area in 서식표영역 for area, _, _ in 칸들):
                        continue
                    if any(area in 안쪽표_리스트 for area, _, _ in 칸들):
                        continue
                    적용 = 표_헤더서식_표단위_처리(칸들)
                    if 적용 is not None:
                        셀수 += 적용
                        처리된.update(area for area, _, _ in 칸들)
            else:
                처리된 = set()

            area = 1
            while True:
                if 중단_요청됨():
                    return False
                area += 1
                try:
                    hwp.SetPos(area, 0, 0)
                except Exception:
                    break
                if hwp.GetPos()[0] == 0:
                    break
                방문영역수 += 1

                if area in 한칸표영역:
                    제외수 += 1
                    진단로그(f"[한 칸 표 제외] 영역 {area}: 문자서식 보존")
                    continue

                if area in 서식표영역:
                    서식표_제외수 += 1
                    진단로그(f"[서식 표 제외] 영역 {area}: 제목·중제목·붙임 서식 보존")
                    continue

                if 쪽범위_사용중() and area not in 쪽범위_컨트롤영역:
                    continue

                if area in 처리된:
                    continue

                if 표_헤더서식_현재셀_처리():
                    셀수 += 1
                else:
                    실패수 += 1

            로그(f"표 헤더/본문 서식적용 완료 (검사한 컨트롤 영역 {방문영역수}개 / 적용된 표 셀 {셀수}개 / 한 칸 표 제외 {제외수}개 / 서식 표 칸 제외 {서식표_제외수}개 / 대상 아님·실패 {실패수}건)")
            return True
        return bind_function(표_헤더서식_전체_적용, _docfit_namespace)
    if _docfit_symbol == '표_목록_수집':
        def 표_목록_수집():
            """문서를 훑어 표마다 [(area, 칼럼문자, 행번호), ...] 목록을 모아
            반환한다(한 칸 표는 제외). 셀 주소가 'A1'로 돌아오는 지점을 새 표의
            시작으로 본다 — 한칸표_영역_목록과 같은 규칙.
            """
            if hwp is None:
                return []
            묶음 = 표칸_묶음_수집()
            if 묶음 is not None:
                표들 = []
                for 칸들 in 묶음:
                    if len(칸들) == 1 and 칸들[0][1] == "A1":
                        continue      # 한 칸 표
                    표 = []
                    for area, 주소, 행번호 in 칸들:
                        일치 = re.match(r"[A-Za-z]+", 주소)
                        표.append((area, 일치.group(0) if 일치 else "A", 행번호))
                    표들.append(표)
                return 표들
            한칸표영역 = 한칸표_영역_목록()
            표들 = []
            현재표 = []
            area = 1
            while True:
                if 중단_요청됨():
                    break
                area += 1
                try:
                    hwp.SetPos(area, 0, 0)
                except Exception:
                    break
                if hwp.GetPos()[0] == 0:
                    break
                if area in 한칸표영역:
                    if 현재표:
                        표들.append(현재표)
                        현재표 = []
                    continue
                주소, 행번호 = 현재_셀_주소_행번호()
                if 주소 is None:
                    if 현재표:
                        표들.append(현재표)
                        현재표 = []
                    continue
                if 주소 == "A1" and 현재표:
                    표들.append(현재표)
                    현재표 = []
                일치 = re.match(r"[A-Za-z]+", 주소)
                컬럼 = 일치.group(0) if 일치 else "A"
                현재표.append((area, 컬럼, 행번호))
            if 현재표:
                표들.append(현재표)
            return 표들
        return bind_function(표_목록_수집, _docfit_namespace)
    if _docfit_symbol == '셀_화면줄수':
        def 셀_화면줄수():
            """캐럿이 있는 셀(리스트) 안에 실제로 배치된 화면줄 수를 센다."""
            if hwp is None:
                return None
            원위치 = hwp.GetPos()
            try:
                hwp_run('MoveListBegin')
                hwp_run('MoveSelListEnd')
                리스트끝 = hwp.GetPos()
                hwp.SetPos(원위치[0], 0, 0)
                hwp_run('MoveListBegin')
                줄수 = 0
                이전줄끝 = None
                while True:
                    if 중단_요청됨():
                        return None
                    hwp_run('MoveLineEnd')
                    줄끝 = hwp.GetPos()
                    if 줄끝 == 이전줄끝:
                        break
                    줄수 += 1
                    if (줄끝[1], 줄끝[2]) >= (리스트끝[1], 리스트끝[2]):
                        break
                    이전줄끝 = 줄끝
                    hwp_run('MoveNextChar')
                    if hwp.GetPos() == 줄끝:
                        break
                return 줄수
            except Exception as e:
                로그(f"셀 화면줄 수 확인 실패(무시): {e}")
                return None
            finally:
                try:
                    hwp.SetPos(*원위치)
                except Exception:
                    pass
        return bind_function(셀_화면줄수, _docfit_namespace)
    if _docfit_symbol == '셀_안쪽여백_읽기':
        def 셀_안쪽여백_읽기():
            """캐럿이 있는 셀의 (셀 여백 사용 여부, 왼쪽, 오른쪽) 원래 값. 실패 시 None."""
            if hwp is None:
                return None
            try:
                pset = hwp.HParameterSet.HShapeObject
                hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
                cell = pset.ShapeTableCell
                return int(cell.HasMargin), int(cell.MarginLeft), int(cell.MarginRight)
            except Exception as e:
                로그(f"셀 안쪽 여백 읽기 실패(무시): {e}")
                return None
        return bind_function(셀_안쪽여백_읽기, _docfit_namespace)
    if _docfit_symbol == '셀_안쪽여백_현재선택':
        def 셀_안쪽여백_현재선택(mm=None, 원래값=None):
            """캐럿이 있는 셀의 좌우 안쪽 여백을 mm로 설정한다(원래값을 주면 그 값으로 복원)."""
            if hwp is None:
                return False
            try:
                pset = hwp.HParameterSet.HShapeObject
                hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
                pset.HSet.SetItem("ShapeType", 3)
                pset.HSet.SetItem("ShapeCellSize", 0)
                if 원래값 is not None:
                    pset.ShapeTableCell.HasMargin, pset.ShapeTableCell.MarginLeft, pset.ShapeTableCell.MarginRight = 원래값
                else:
                    pset.ShapeTableCell.HasMargin = 1
                    pset.ShapeTableCell.MarginLeft = hwp.MiliToHwpUnit(mm)
                    pset.ShapeTableCell.MarginRight = hwp.MiliToHwpUnit(mm)
                return hwp.HAction.Execute("TablePropertyDialog", pset.HSet) is not False
            except Exception as e:
                로그(f"셀 안쪽 여백 적용 실패(무시): {e}")
                return False
        return bind_function(셀_안쪽여백_현재선택, _docfit_namespace)
    if _docfit_symbol == '셀_안쪽여백_축소_시도':
        def 셀_안쪽여백_축소_시도():
            """캐럿이 있는 셀의 텍스트가 2줄 이상이면 좌우 안쪽 여백을 조금씩
            줄여(표_셀여백_기본_mm → 표_셀여백_최소_mm) 1줄로 줄어드는지 시도한다.
            """
            if 셀_화면줄수() is None:
                return False
            줄수 = 셀_화면줄수()
            if 줄수 is None or 줄수 <= 1:
                return False
            # 실측(2026-09-25): 1줄로 만들지 못한 셀도 여백이 0으로 남아(표 서식 문서 46칸)
            # 표 모양만 바뀌었다. 실패하면 원래 여백으로 되돌린다.
            원래값 = 셀_안쪽여백_읽기()
            if 원래값 is None:
                return False
            try:
                if _셀_안쪽여백_단계축소():
                    return True
            except Exception:
                pass
            셀_안쪽여백_현재선택(원래값=원래값)
            return False
        return bind_function(셀_안쪽여백_축소_시도, _docfit_namespace)
    raise KeyError(_docfit_symbol)
