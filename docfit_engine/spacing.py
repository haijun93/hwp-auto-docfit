"""Extracted docfit_engine.spacing definitions; installed into the compatibility session.

Original algorithms and comments are preserved. Runtime bindings are session-local;
see docfit_engine.runtime. This module does not import the application bootstrap.
"""
from docfit_engine.runtime import bind_function, bind_class

def _install(*, _docfit_namespace, _docfit_symbol):
    global 문단_자간보호_선행부_오프셋, 컨트롤_내부_자간조정, 한칸표_자간조정, 표셀_자간_제외인가, 컨트롤_줄병합_대상인가, 문서_전체_자간_초기화, 자간초기화_hwpx_처리, 현재_페이지번호, 처리중_기록_대체, 검수_문제_기록, 줄경계_어절연속_문자쌍인가, 현재줄_끝_어절분리인가, 현재줄_끝_붙임괄호_분리인가, 현재줄_끝_괄호내부_공백분리인가, 단어문자인가, 단어모드_범위선택, 단어모드_한글자, 단어모드_줄범위, 의미단위_범위, 일반_의미단위_범위, 등_어절인가, 숫자쉼표_어절인가, 숫자끝_어절인가, _숫자쉼표_앞단어인가, 어절_의미단위_범위, 앞어절_묶음_후속인가, _왼쪽_어절_추가, _단어모드_공백전까지, _띄운날짜_어절_확장, _직함이름_어절_확장, 단어모드_분리정보, 칸폭보다_긴_단어인가, 붙임의미단위_줄분리인가, 자간보호_글자수, 자간조정_본문범위, 자간조정_현재줄_본문선택, _단어모드_다음위치, 단어모드_서식보관, 단어모드_자간보관, 단어모드_자간적용, 단어모드_장평보관, 단어모드_장평적용, 최소_성공단계_탐색, 단어_장평_추가축소_시도, 다음단어_당김_시도, 어절분리_앞줄당김인가, 단어모드_마지막줄_짧은잔여인가, 연결부호_구간, 연결부호_단위들, 연결부호_전체_맞춤, _연결단위_맞춤, 단어중간_줄바꿈방지, 자간자동조정, _자간자동조정_본체, 본문_기존자간조정, 문단세트_가능, 문단세트1_글서식_적용, _문단세트_줄순회, 문단세트2_배치_적용, _괄호따옴표_시작문자인가, 문장부호_시작인가, 문장부호_마커_끝위치, 세트문장_시작인가
    if _docfit_symbol == '자간초기화_hwpx_처리':
        def 자간초기화_hwpx_처리(source, target=None, selections=None):
            """문서 전체(표·글상자 안 포함) 본문 자간을 0%로 되돌린다. 항목기호·라벨 등 보호 구간은 그대로 둔다."""
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
            전 = {n: 제목_문자열(roots[n]) for n in names}
            통계 = 자간초기화모듈.reset_spacing(header, [roots[n] for n in names], lambda text: 자간보호_글자수(text) or 0)
            if any(제목_문자열(roots[n]) != 전[n] for n in names):
                raise RuntimeError('자간 초기화 중 글 보존 검사에 실패했습니다.')
            if not 통계["runs"]:
                shutil.copyfile(source, target)
                로그("자간 초기화(XML): 자간이 남은 본문 없음")
                return 0
            for n in names:
                contents[n] = ET.tostring(roots[n], encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"자간 초기화(XML): 문단 {통계['paragraphs']}개 · 글 묶음 {통계['runs']}개를 0%로"
                + (f"(보호 구간에서 나눔 {통계['split']}개)" if 통계['split'] else "")
                + (f" · 컨트롤이 걸쳐 건너뜀 {통계['skipped']}개" if 통계['skipped'] else ""))
            return 통계["paragraphs"]
        return bind_function(자간초기화_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '현재_페이지번호':
        def 현재_페이지번호():
            """캐럿이 있는 쪽의 실제 순서(1부터). 인쇄 쪽 번호가 아니다.

            KeyIndicator()[3]은 인쇄되는 쪽 번호라 '새 번호로 시작'이 있는 문서에서는
            서로 다른 쪽이 같은 번호를 갖는다(실측: 공고문 18쪽부터 1쪽으로 다시 시작해
            마지막 쪽이 8쪽으로 보였고, 검수 표시는 13~17쪽). 쪽 수 맞춤·묶음 판정이
            엉뚱한 쪽을 섞지 않도록 문서 안 실제 쪽 순서를 쓰고, 읽지 못할 때만
            인쇄 쪽 번호로 대신한다.
            """
            try:
                return int(hwp.XHwpDocuments.Active_XHwpDocument.XHwpDocumentInfo.CurrentPage) + 1
            except Exception:
                pass
            try:
                정보 = hwp.KeyIndicator()
                if 정보 and len(정보) >= 4:
                    return int(정보[3])
            except Exception:
                pass
            return None
        return bind_function(현재_페이지번호, _docfit_namespace)
    if _docfit_symbol == '처리중_기록_대체':
        def 처리중_기록_대체(파일, 완료된_검사, 경계):
            """검수_문제목록[:경계](저장 전 처리 중 기록) 가운데, 저장 후 검사를 마친
            규칙의 기록을 지운다. 경계 뒤의 저장 후 검사 기록은 그대로 둔다.

            단어 분리 기록은 본문·표 구분이 없으므로, 표·컨트롤 단어 검사가 필요한
            작업이면 두 검사를 모두 마쳤을 때만 지운다.
            """
            global 검수_문제목록
            접두어 = []
            if 'page_group' in 완료된_검사:
                접두어 += _처리중_기록_접두어['page_group']
            컨트롤_필요 = (stage_enabled(선택_세부작업, 'control_spacing')
                        or stage_enabled(선택_세부작업, 'control_word_check'))
            if 'word_check' in 완료된_검사 and (not 컨트롤_필요 or 'control_word_check' in 완료된_검사):
                접두어 += _처리중_기록_접두어['word']
            if not 접두어:
                return 0
            접두어 = tuple(접두어)
            남김 = [item for index, item in enumerate(검수_문제목록)
                  if index >= 경계 or str(item.get('file')) != str(파일)
                  or not str(item.get('text', '')).startswith(접두어)]
            지운수 = len(검수_문제목록) - len(남김)
            검수_문제목록[:] = 남김
            return 지운수
        return bind_function(처리중_기록_대체, _docfit_namespace)
    if _docfit_symbol == '검수_문제_기록':
        def 검수_문제_기록(파일, text):
            global 검수_문제목록
            if not 검수_사용:
                return
            문제 = {
                "file": str(파일),
                "text": text,
                "page": 현재_페이지번호(),
            }
            # 반복 처리나 최종 검수에서 같은 미해결 줄이 반복 검출될 수 있다.
            # 파일·페이지·문제 텍스트가 같으면 한 번만 기록한다.
            문제키 = (문제["file"], 문제["page"], 문제["text"])
            기존키 = {(항목["file"], 항목["page"], 항목["text"]) for 항목 in 검수_문제목록}
            if 문제키 not in 기존키:
                검수_문제목록.append(문제)
        return bind_function(검수_문제_기록, _docfit_namespace)
    if _docfit_symbol == '줄경계_어절연속_문자쌍인가':
        def 줄경계_어절연속_문자쌍인가(앞문자, 다음문자):
            """화면줄 경계의 두 문자가 공백 없는 같은 어절의 연속인지 판정한다.

            한글/영문/숫자처럼 ``isalnum()``인 문자끼리 실제 Enter나 공백 없이
            화면줄만 바뀐 경우를 대상으로 한다. 예: ``제공하 | 며,``.

            v1.11: "경기도·경상북도"처럼 가운뎃점(·)으로 단어를 이어붙인 경우도
            하나의 어절로 취급한다. 줄 끝이 "·"로 끝나거나 다음 줄이 "·"로
            시작하면(즉 "·"가 경계에 걸리면) 글자가 alnum인지와 무관하게
            같은 어절의 연속으로 본다.
            """
            if not 앞문자 or not 다음문자:
                return False
            if 앞문자[-1] in "·ㆍ" or 다음문자[0] in "·ㆍ":
                return True
            return 앞문자[-1].isalnum() and 다음문자[0].isalnum()
        return bind_function(줄경계_어절연속_문자쌍인가, _docfit_namespace)
    if _docfit_symbol == '현재줄_끝_어절분리인가':
        def 현재줄_끝_어절분리인가():
            """'제공하' | '며,'처럼 같은 어절이 화면줄 경계에서 갈라졌는지 확인.

            HWP의 MoveSelWordBegin/End만으로는 조사·어미+구두점 경계에서
            단어 선택이 다음 화면줄까지 안정적으로 확장되지 않는 경우가 있다.
            따라서 화면줄 끝과 다음 화면줄 첫 문자를 직접 확인한다.
            실제 Enter, 다른 컨트롤/문단, 공백 경계는 제외한다.
            """
            if hwp is None:
                return False

            원래위치 = hwp.GetPos()
            try:
                hwp_run("MoveLineEnd")
                줄끝위치 = hwp.GetPos()

                # 현재 화면줄의 마지막 실제 문자를 확인한다.
                hwp_run("MoveSelLineBegin")
                줄텍스트 = 현재선택영역_텍스트()
                hwp_run("Cancel")
                hwp.SetPos(*줄끝위치)
                줄텍스트 = (줄텍스트 or "").rstrip("\r\n")
                if not 줄텍스트:
                    return False
                앞문자 = 줄텍스트[-1]
                if 앞문자.isspace():
                    return False

                # 다음 화면줄 첫 문자 위치로 이동한다.
                hwp_run("MoveNextChar")
                다음위치 = hwp.GetPos()
                if 다음위치 == 줄끝위치:
                    return False
                if 다음위치[0] != 줄끝위치[0] or 다음위치[1] != 줄끝위치[1]:
                    return False
                if 두_위치_사이_줄바꿈_문자인가(줄끝위치, 다음위치):
                    return False

                # 줄끝에서 오른쪽 한 글자를 직접 읽어 공백 없는 연속 어절인지 확인한다.
                hwp.SetPos(*줄끝위치)
                hwp_run("MoveSelRight")
                다음텍스트 = 현재선택영역_텍스트()
                hwp_run("Cancel")
                hwp.SetPos(*줄끝위치)
                if not 다음텍스트:
                    return False

                다음문자 = ""
                for ch in 다음텍스트:
                    if ch not in "\r\n":
                        다음문자 = ch
                        break
                if not 다음문자 or 다음문자.isspace():
                    return False

                return 줄경계_어절연속_문자쌍인가(앞문자, 다음문자)
            except Exception:
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
                return False
            finally:
                try:
                    hwp.SetPos(*원래위치)
                except Exception:
                    pass
        return bind_function(현재줄_끝_어절분리인가, _docfit_namespace)
    if _docfit_symbol == '현재줄_끝_붙임괄호_분리인가':
        def 현재줄_끝_붙임괄호_분리인가():
            """'경상북도' | '(1)'처럼 붙임 괄호가 화면 줄 경계에서 갈라졌는지 확인.

            v1.11:
            - 기존에는 줄 끝 바로 다음 글자가 곧바로 여는 괄호인 경우만 감지했다.
              그래서 '…사기진' | '작(노조,동호회),…'처럼, 같은 단어의 꼬리 글자
              ('작')가 괄호 앞에 공백 없이 붙어 다음 줄로 넘어간 경우는 놓쳤다.
            - 이제는 다음 줄 맨 앞의 짧은 구간(최대 _붙임괄호_다음구간_미리보기_글자수자)
              안에서, 공백 없이 이어지는 한글/영문/숫자 0~2자 뒤에 여는 괄호가
              나오면 같은 '붙임 괄호 분리'로 인식한다. 아래아한글에서 Shift+Tab으로
              맞춘 들여쓰기가 이런 단어 조각 때문에 어긋나 보이는 것을 막기 위함이다.
            """
            if hwp is None:
                return False

            원래위치 = hwp.GetPos()
            try:
                hwp_run("MoveLineEnd")
                줄끝위치 = hwp.GetPos()

                hwp_run("MoveSelLineBegin")
                줄텍스트 = 현재선택영역_텍스트()
                hwp_run("Cancel")
                hwp.SetPos(*줄끝위치)

                줄텍스트 = (줄텍스트 or "").rstrip()
                if not (줄텍스트 and re.search(r"[0-9A-Za-z가-힣]$", 줄텍스트)):
                    return False

                hwp.SetPos(*줄끝위치)
                for _ in range(_붙임괄호_다음구간_미리보기_글자수):
                    hwp_run("MoveSelRight")
                다음구간 = 현재선택영역_텍스트()
                hwp_run("Cancel")
                hwp.SetPos(*줄끝위치)

                다음구간 = (다음구간 or "").replace("\r", "").replace("\n", "")
                if not 다음구간:
                    return False

                # 다음 줄 첫머리가: (a) 곧바로 여는 괄호이거나,
                # (b) 공백 없이 붙은 한글/영문/숫자 0~2자 뒤에 여는 괄호가 오면 대상.
                일치 = re.match(r"^[0-9A-Za-z가-힣]{0,2}[(（\[［{｛]", 다음구간)
                return bool(일치)
            except Exception:
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
                return False
            finally:
                try:
                    hwp.SetPos(*원래위치)
                except Exception:
                    pass
        return bind_function(현재줄_끝_붙임괄호_분리인가, _docfit_namespace)
    if _docfit_symbol == '현재줄_끝_괄호내부_공백분리인가':
        def 현재줄_끝_괄호내부_공백분리인가():
            """'계약방법(공개모집' | '원칙, 수의계약)이'처럼, 괄호 안 부연 설명의
            공백에서 화면줄이 갈라졌는지 확인한다.

            '(공개모집 원칙, 수의계약)'처럼 여는 괄호와 닫는 괄호 사이가 공백·쉼표로
            이어진 짧은 설명은 여는 괄호부터 닫는 괄호까지를 하나의 어절로 보고,
            그 안의 공백에서 줄이 갈라지면 다른 어절 분리와 똑같이 자간을 좁혀
            같은 화면줄에 붙인다. 닫는 괄호가 미리보기 범위 안에 없으면(설명이
            너무 길면) 대상으로 보지 않는다.
            """
            if hwp is None:
                return False

            원래위치 = hwp.GetPos()
            try:
                hwp_run("MoveLineEnd")
                줄끝위치 = hwp.GetPos()

                # 줄 끝 바로 다음 문자가 실제 공백이어야 이 규칙의 대상이다
                # (실제 Enter는 제외).
                hwp_run("MoveSelRight")
                다음위치 = hwp.GetPos()
                다음문자 = 현재선택영역_텍스트()
                hwp_run("Cancel")
                hwp.SetPos(*줄끝위치)
                if not 다음문자 or 실제_엔터_포함(다음문자) or not 다음문자[0].isspace():
                    return False
                if 다음위치[0] != 줄끝위치[0] or 다음위치[1] != 줄끝위치[1]:
                    return False

                # 문단 시작부터 줄 끝까지 열린 괄호가 아직 닫히지 않았는지 확인한다.
                hwp.SetPos(줄끝위치[0], 줄끝위치[1], 0)
                if hwp.SelectText(줄끝위치[1], 0, 줄끝위치[1], 줄끝위치[2]) is False:
                    hwp.SetPos(*줄끝위치)
                    return False
                앞부분 = (현재선택영역_텍스트() or "").replace("\r", "").replace("\n", "")
                hwp_run("Cancel")
                hwp.SetPos(*줄끝위치)
                여는괄호수 = sum(앞부분.count(ch) for ch in "(（")
                닫는괄호수 = sum(앞부분.count(ch) for ch in ")）")
                if 여는괄호수 <= 닫는괄호수:
                    return False

                # 닫는 괄호가 미리보기 범위 안에서 나오는지 확인한다.
                for _ in range(_괄호내부_다음구간_미리보기_글자수):
                    hwp_run("MoveSelRight")
                다음구간 = (현재선택영역_텍스트() or "").replace("\r", "").replace("\n", "")
                hwp_run("Cancel")
                hwp.SetPos(*줄끝위치)
                return any(ch in ")）" for ch in 다음구간)
            except Exception:
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
                return False
            finally:
                try:
                    hwp.SetPos(*원래위치)
                except Exception:
                    pass
        return bind_function(현재줄_끝_괄호내부_공백분리인가, _docfit_namespace)
    if _docfit_symbol == '단어문자인가':
        def 단어문자인가(ch):
            return bool(ch) and all(c.isalnum() or unicodedata.category(c).startswith('M')
                                    or c in '·ㆍ' for c in ch)
        return bind_function(단어문자인가, _docfit_namespace)
    if _docfit_symbol == '단어모드_범위선택':
        def 단어모드_범위선택(start, end):
            if start[:2] != end[:2] or start[2] >= end[2]:
                raise ValueError('같은 문단의 비어 있지 않은 범위만 선택할 수 있습니다.')
            hwp.SetPos(*start)
            if hwp.SelectText(start[1], start[2], end[1], end[2]) is False:
                raise RuntimeError('단어 모드 범위 선택 실패')
        return bind_function(단어모드_범위선택, _docfit_namespace)
    if _docfit_symbol == '단어모드_한글자':
        def 단어모드_한글자(pos, 뒤로=False):
            """문자열 인덱스 대신 한글의 실제 위치를 사용(컨트롤/UTF-16 안전)."""
            hwp.SetPos(*pos)
            hwp_run('MovePrevChar' if 뒤로 else 'MoveNextChar')
            other = hwp.GetPos()
            if other[:2] != pos[:2] or other == pos:
                return None
            start, end = (other, pos) if 뒤로 else (pos, other)
            단어모드_범위선택(start, end)
            text = 현재선택영역_텍스트()
            hwp_run('Cancel')
            return start, end, text
        return bind_function(단어모드_한글자, _docfit_namespace)
    if _docfit_symbol == '단어모드_줄범위':
        def 단어모드_줄범위(pos):
            """화면줄의 [시작, 끝) 실제 위치. MoveLineEnd의 커서 위치를 단정하지 않는다."""
            hwp.SetPos(*pos)
            hwp_run('MoveLineBegin')
            start = hwp.GetPos()
            hwp_run('MoveLineEnd')
            raw_end = hwp.GetPos()
            hwp_run('MoveNextChar')
            probe = hwp.GetPos()
            if probe[:2] == start[:2] and probe != raw_end:
                hwp_run('MoveLineBegin')
                next_start = hwp.GetPos()
                if next_start[:2] == start[:2] and next_start[2] > start[2]:
                    # 소프트 줄바꿈에서는 MoveLineEnd가 정확한 경계이고, 다음 줄의
                    # MoveLineBegin은 첫 글자 뒤 위치를 돌려주는 한글 COM 사례가 있다.
                    # 이를 next_start로 쓰면 '맞춤|형'의 '형'을 건너뛰어 분리를 놓친다.
                    # 실제 줄바꿈 문자가 있을 때만 그 문자를 포함한 next_start를 쓴다.
                    if 두_위치_사이_줄바꿈_문자인가(raw_end, next_start):
                        return start, next_start
                    return start, raw_end
            hwp.SetPos(*start)
            hwp_run('MoveParaEnd')
            return start, hwp.GetPos()
        return bind_function(단어모드_줄범위, _docfit_namespace)
    if _docfit_symbol == '의미단위_범위':
        def 의미단위_범위(text):
            """날짜·기간·직함:이름을 독립된 의미 단위로 보존한다."""
            result = []
            offset = 0
            protected = sorted([match.span() for match in _기간_단위.finditer(text)]
                               + staff_role_name_ranges(text))
            for start, end in protected:
                if start < offset:
                    continue
                result.extend((a + offset, b + offset)
                              for a, b in 일반_의미단위_범위(text[offset:start]))
                result.append((start, end))
                offset = end
            result.extend((a + offset, b + offset)
                          for a, b in 일반_의미단위_범위(text[offset:]))
            return result
        return bind_function(의미단위_범위, _docfit_namespace)
    if _docfit_symbol == '일반_의미단위_범위':
        def 일반_의미단위_범위(text):
            """공백을 넘지 않고 붙임표시와 짧은 괄호를 포함한 단어 범위를 반환."""
            result = []
            i = 0
            while i < len(text):
                start = i
                has_core = False
                while i < len(text):
                    ch = text[i]
                    if ch in "·ㆍ":
                        break
                    if 단어문자인가(ch):
                        has_core = has_core or ch.isalnum()
                        i += 1
                    elif ch in _단어_붙임표시:
                        i += 1
                    elif ch in '(（' and has_core:
                        closing = ')' if ch == '(' else '）'
                        end = text.find(closing, i + 1)
                        inside = text[i + 1:end] if end >= 0 else ''
                        if not (1 <= len(inside) <= 3 and all(c.isalnum() for c in inside)):
                            break
                        i = end + 1
                    else:
                        break
                if has_core:
                    result.append((start, i))
                if i == start:
                    i += 1
            return result
        return bind_function(일반_의미단위_범위, _docfit_namespace)
    if _docfit_symbol == '등_어절인가':
        def 등_어절인가(text):
            return bool(text) and bool(_등_어절.fullmatch(text))
        return bind_function(등_어절인가, _docfit_namespace)
    if _docfit_symbol == '숫자쉼표_어절인가':
        def 숫자쉼표_어절인가(text):
            return bool(text) and bool(_숫자쉼표_어절.fullmatch(text))
        return bind_function(숫자쉼표_어절인가, _docfit_namespace)
    if _docfit_symbol == '숫자끝_어절인가':
        def 숫자끝_어절인가(text):
            return (bool(text) and bool(_숫자끝_어절.fullmatch(text))
                    and not 숫자쉼표_어절인가(text))
        return bind_function(숫자끝_어절인가, _docfit_namespace)
    if _docfit_symbol == '_숫자쉼표_앞단어인가':
        def _숫자쉼표_앞단어인가(text):
            """'수원 2,'의 '수원'처럼 숫자 앞에 오는 단어. 숫자·쉼표로 끝나는 앞 항목
            ('2,' 등)은 단어가 아니므로 '2, 3,'처럼 숫자끼리는 묶지 않는다."""
            return bool(text) and not text[-1] in ',，' and any(ch.isalpha() for ch in text)
        return bind_function(_숫자쉼표_앞단어인가, _docfit_namespace)
    if _docfit_symbol == '어절_의미단위_범위':
        def 어절_의미단위_범위(text):
            """의미단위_범위에 '앞 어절 + 공백 + 등', '단어 + 공백 + 숫자,' 묶음을 더한 범위."""
            result = []
            for a, b in 의미단위_범위(text):
                joined = result and a >= 1 and text[a - 1] == ' ' and result[-1][1] == a - 1
                if joined and 등_어절인가(text[a:b]):
                    result[-1] = (result[-1][0], b)
                elif (joined and 숫자쉼표_어절인가(text[a:b])
                        and _숫자쉼표_앞단어인가(text[result[-1][0]:result[-1][1]])):
                    result[-1] = (result[-1][0], b)
                elif (joined and 숫자끝_어절인가(text[a:b]) and len(result) >= 2
                        and _숫자쉼표_앞단어인가(text[result[-1][0]:result[-1][1]])
                        and result[-2][1] + 1 == result[-1][0] and text[result[-2][1]] == ' '
                        and _숫자쉼표_끝.search(text[result[-2][0]:result[-2][1]])):
                    result[-1] = (result[-1][0], b)
                else:
                    result.append((a, b))
            return result
        return bind_function(어절_의미단위_범위, _docfit_namespace)
    if _docfit_symbol == '앞어절_묶음_후속인가':
        def 앞어절_묶음_후속인가(text):
            """앞 어절과 빈칸을 사이에 두고 한 어절로 묶일 수 있는 뒤 어절
            ('등으로', '2,', 열거 마지막 항목의 '1등으로'). 실제로 묶이는지는
            어절_의미단위_범위가 앞 문맥까지 보고 가린다."""
            return 등_어절인가(text) or 숫자쉼표_어절인가(text) or 숫자끝_어절인가(text)
        return bind_function(앞어절_묶음_후속인가, _docfit_namespace)
    if _docfit_symbol == '_왼쪽_어절_추가':
        def _왼쪽_어절_추가(before):
            """before(경계에서 왼쪽으로 읽은 글자, 역순)에 빈칸 너머 앞 어절 하나를 더한다.
            열거 마지막 항목('용인 1등으로')은 그 앞 항목('4,')을 보고 묶기 때문이다."""
            if not before:
                return before
            gap, space = _단어모드_공백전까지(before[-1][0], True)
            if gap is None or gap or space is None:
                return before
            previous, _ = _단어모드_공백전까지(space[0], True)
            if previous:
                return before + [space] + previous
            return before
        return bind_function(_왼쪽_어절_추가, _docfit_namespace)
    if _docfit_symbol == '_단어모드_공백전까지':
        def _단어모드_공백전까지(pos, 뒤로=False):
            """pos에서 한 방향으로 공백·개행·컨트롤 전까지의 글자 목록과,
            멈춘 글자가 보통 공백(' ')이면 그 글자를 돌려준다. 중단 시 (None, None)."""
            parts = []
            while True:
                if 중단_요청됨():
                    return None, None
                part = 단어모드_한글자(pos, 뒤로)
                if not part or not part[2]:
                    return parts, None
                if any(c.isspace() or unicodedata.category(c) == 'Cc' for c in part[2]):
                    return parts, (part if part[2] == ' ' else None)
                parts.append(part)
                pos = part[0] if 뒤로 else part[1]
        return bind_function(_단어모드_공백전까지, _docfit_namespace)
    if _docfit_symbol == '_띄운날짜_어절_확장':
        def _띄운날짜_어절_확장(before, after, stop_left, stop_right, 최대=3):
            """경계 양쪽으로 빈칸 너머의 날짜 조각('10.', '19.~11.', '18.')을 최대 몇 개 더 붙인다.
            실제로 한 기간인지는 어절_의미단위_범위(_기간_단위)가 가린다."""
            for 뒤로, parts, stop in ((True, before, stop_left), (False, after, stop_right)):
                for _ in range(최대):
                    if stop is None:
                        break
                    word, next_stop = _단어모드_공백전까지(stop[0] if 뒤로 else stop[1], 뒤로)
                    if word is None:
                        return None, None
                    text = ''.join(p[2] for p in (reversed(word) if 뒤로 else word))
                    if not word or not _띄운날짜어절.fullmatch(text):
                        break
                    parts = parts + [stop] + word
                    stop = next_stop
                if 뒤로:
                    before = parts
                else:
                    after = parts
            return before, after
        return bind_function(_띄운날짜_어절_확장, _docfit_namespace)
    if _docfit_symbol == '_직함이름_어절_확장':
        def _직함이름_어절_확장(before, after, stop_left, stop_right):
            original = before, after
            word = ''.join(p[2] for p in reversed(before)) + ''.join(p[2] for p in after)
            if stop_left is not None and not STAFF_PREFIX.fullmatch(word):
                last = 단어모드_한글자(stop_left[0], True)
                if word in (':', '：') or (last and last[2] in (':', '：')):
                    previous, gap = _단어모드_공백전까지(stop_left[0], True)
                    if previous:
                        before = before + [stop_left] + previous
                        if ''.join(p[2] for p in reversed(previous)) in (':', '：') and gap is not None:
                            title, _ = _단어모드_공백전까지(gap[0], True)
                            if title:
                                before = before + [gap] + title
            combined = ''.join(p[2] for p in reversed(before)) + ''.join(p[2] for p in after)
            if STAFF_PREFIX.fullmatch(combined.strip()) or combined.strip() in (':', '：'):
                for _ in range(2):
                    if stop_right is None:
                        break
                    following, gap = _단어모드_공백전까지(stop_right[1])
                    if not following:
                        break
                    after = after + [stop_right] + following
                    stop_right = gap
                    candidate = ''.join(p[2] for p in reversed(before)) + ''.join(p[2] for p in after)
                    if staff_role_name_ranges(candidate):
                        break
            text = ''.join(p[2] for p in reversed(before)) + ''.join(p[2] for p in after)
            cut = sum(len(p[2]) for p in before)
            return (before, after) if any(a < cut < b for a, b in staff_role_name_ranges(text)) else original
        return bind_function(_직함이름_어절_확장, _docfit_namespace)
    if _docfit_symbol == '단어모드_분리정보':
        def 단어모드_분리정보(anchor):
            start, boundary = 단어모드_줄범위(anchor)
            right = 단어모드_한글자(boundary)
            if not right or not right[2]:
                return None
            before, stop_left = _단어모드_공백전까지(boundary, True)
            after, stop_right = _단어모드_공백전까지(boundary)
            if before is None or after is None:
                return None
            staff_before, staff_after = _직함이름_어절_확장(before, after, stop_left, stop_right)
            if 중단_요청됨():
                return None
            staff_parts = list(reversed(staff_before)) + staff_after
            staff_text = ''.join(part[2] for part in staff_parts)
            staff_cut = sum(len(part[2]) for part in staff_before)
            for a, b in staff_role_name_ranges(staff_text):
                if a < staff_cut < b:
                    positions = [0]
                    for part in staff_parts:
                        positions.append(positions[-1] + len(part[2]))
                    if a not in positions or b not in positions:
                        continue
                    selected = staff_parts[positions.index(a):positions.index(b)]
                    _, next_end = 단어모드_줄범위(right[1])
                    if next_end[2] <= boundary[2]:
                        return None
                    return (start, boundary, selected[0][0], selected[-1][1],
                            sum(len(t) for p, q, t in selected if p[2] >= start[2] and q[2] <= boundary[2]),
                            sum(len(t) for p, q, t in selected if p[2] >= boundary[2] and q[2] <= next_end[2]))
            if any(c.isspace() for c in right[2]):
                # 공백에서 줄이 바뀐 경우는 다음 어절이 '등' 또는 '숫자,'일 때만
                # 분리 후보다(실제로 묶이는지는 어절_의미단위_범위가 가린다).
                if right[2] != ' ':
                    return None
                peek = 단어모드_한글자(right[1])
                if not peek or not (peek[2] == '등' or peek[2].isdigit()):
                    return None
            _, next_end = 단어모드_줄범위(right[1])
            if next_end[2] <= boundary[2]:
                return None
            # 공백/실제 개행/컨트롤 경계를 넘지 않는 구간의 실제 HWP 위치를 보관.
            if not before and not after:
                return None
            # 경계가 걸친 어절이 '등'·'숫자,' 어절이면 공백 앞 어절까지 묶는다.
            현재어절 = ''.join(p[2] for p in reversed(before)) + ''.join(p[2] for p in after)
            # 띄어 쓴 날짜 기간('10. 19.~11. 18.')은 빈칸을 넘어 한 어절로 묶는다.
            날짜기간 = bool(_띄운날짜어절.fullmatch(현재어절))
            if 날짜기간:
                before, after = _띄운날짜_어절_확장(before, after, stop_left, stop_right)
                if before is None:
                    return None
            elif stop_left is not None and 앞어절_묶음_후속인가(현재어절):
                previous, _ = _단어모드_공백전까지(stop_left[0], True)
                if previous is None:
                    return None
                if previous:
                    before = before + [stop_left] + previous
            # 경계가 걸친 어절 뒤에 '등'·'숫자,' 어절이 이어지면 그 어절까지 묶는다.
            뒤어절 = ''
            if not 날짜기간 and (stop_left is None or not 앞어절_묶음_후속인가(현재어절)):
                if stop_right is not None:
                    peek = 단어모드_한글자(stop_right[1])
                    if peek and (peek[2] == '등' or peek[2].isdigit()):
                        following, _ = _단어모드_공백전까지(stop_right[1])
                        if following is None:
                            return None
                        뒤어절 = ''.join(p[2] for p in following)
                        if 앞어절_묶음_후속인가(뒤어절):
                            after = after + [stop_right] + following
            # 열거 마지막 항목은 앞 항목('4,')까지 봐야 묶을지 정할 수 있다.
            if not 날짜기간 and (숫자끝_어절인가(현재어절) or 숫자끝_어절인가(뒤어절)):
                before = _왼쪽_어절_추가(before)
            parts = list(reversed(before)) + after
            text = ''.join(part[2] for part in parts)
            offsets = [0]
            for part in parts:
                offsets.append(offsets[-1] + len(part[2]))
            cut = sum(len(part[2]) for part in before)
            for a, b in 어절_의미단위_범위(text):
                if not a < cut < b or a not in offsets or b not in offsets:
                    continue
                selected = parts[offsets.index(a):offsets.index(b)]
                left_count = sum(len(t) for p, q, t in selected if p[2] >= start[2] and q[2] <= boundary[2])
                right_count = sum(len(t) for p, q, t in selected if p[2] >= boundary[2] and q[2] <= next_end[2])
                return start, boundary, selected[0][0], selected[-1][1], left_count, right_count
            return None
        return bind_function(단어모드_분리정보, _docfit_namespace)
    if _docfit_symbol == '칸폭보다_긴_단어인가':
        def 칸폭보다_긴_단어인가(info):
            """단어모드_분리정보 결과가 '줄 첫머리에서 시작했는데도 넘치는 단어'인지.

            실측: 공고문 표 칸 단어 분리 미해결 20건 중 13건이 줄 전체가 그 단어
            하나였다(예: 5자 칸의 '질그랭이거|점센터'). 밀 곳도 당길 곳도 없어 어떤
            조정으로도 풀 수 없으므로, 시도하지 않고 검수에서도 적용 제외로 적는다.
            """
            start, _, word_start, _, left, right = info
            return word_start[2] <= start[2] and right > left * 칸폭초과_허용비율
        return bind_function(칸폭보다_긴_단어인가, _docfit_namespace)
    if _docfit_symbol == '붙임의미단위_줄분리인가':
        def 붙임의미단위_줄분리인가():
            original = hwp.GetPos()
            try:
                hwp_run("MoveLineBegin")
                info = 단어모드_분리정보(hwp.GetPos())
                if info is None:
                    return False
                단어모드_범위선택(info[2], info[3])
                text = 현재선택영역_텍스트()
                return (bool(_기간_단위.search(text))
                        or bool(staff_role_name_ranges(text))
                        or any(ch in _단어_붙임표시 or ch in '(（' for ch in text)
                        or any(앞어절_묶음_후속인가(word) for word in text.split(' ')[1:]))
            finally:
                hwp_run('Cancel')
                hwp.SetPos(*original)
        return bind_function(붙임의미단위_줄분리인가, _docfit_namespace)
    if _docfit_symbol == '자간보호_글자수':
        def 자간보호_글자수(text):
            """자간·장평 조정이 바꾸지 않는 문단 앞 글자 수(항목기호·라벨 등). 보호할 것이 없으면 None(순수 함수).

            '(운영방식)'처럼 본문 없이 라벨만 있는 문단과 기호만 있는 문단은 문단 끝까지 보호한다.
            한/글 경로(자간조정_본문범위)와 XML 자간 초기화(자간초기화_hwpx_처리)가 같은 규칙을 쓴다."""
            offset = 문단_자간보호_선행부_오프셋(text)
            marker_end = 문장부호_마커_끝위치(text)
            if marker_end is not None and re.fullmatch(r'\s*[（(][^\r\n]+[)）]\s*[:：]?\s*', text[marker_end:]):
                offset = len(text.rstrip('\r\n'))
            if marker_end is not None and not text[marker_end:].strip():
                offset = len(text.rstrip('\r\n'))
            return offset
        return bind_function(자간보호_글자수, _docfit_namespace)
    if _docfit_symbol == '자간조정_본문범위':
        def 자간조정_본문범위(start, end):
            """내어쓰기와 같은 기준으로 항목기호·라벨·후행 공백을 제외한다."""
            if start[:2] != end[:2]:
                raise ValueError('자간 조정 범위는 한 문단이어야 합니다')
            original = hwp.GetPos()
            try:
                hwp.SetPos(start[0], start[1], 0)
                text = 현재문단_텍스트()
                offset = 자간보호_글자수(text)
                if offset is None:
                    return start, end
                body = len(text[:offset].encode('utf-16-le')) // 2
                return (start[0], start[1], min(end[2], max(start[2], body))), end
            finally:
                hwp.SetPos(*original)
        return bind_function(자간조정_본문범위, _docfit_namespace)
    if _docfit_symbol == '자간조정_현재줄_본문선택':
        def 자간조정_현재줄_본문선택():
            """화면줄 기반 단축키 조정에서도 선행부를 제외한다."""
            anchor = hwp.GetPos()
            hwp.Run('Cancel')
            hwp.SetPos(*anchor)
            hwp.Run('MoveLineEnd')
            end = hwp.GetPos()
            hwp.Run('MoveLineBegin')
            start = hwp.GetPos()
            start, end = 자간조정_본문범위(start, end)
            if start[2] >= end[2]:
                return False
            단어모드_범위선택(start, end)
            return True
        return bind_function(자간조정_현재줄_본문선택, _docfit_namespace)
    if _docfit_symbol == '_단어모드_다음위치':
        def _단어모드_다음위치(pos):
            """pos 다음 글자 위치(같은 문단 안). 글자 내용은 읽지 않는다."""
            hwp.SetPos(*pos)
            hwp_run('MoveNextChar')
            other = hwp.GetPos()
            if other[:2] != pos[:2] or other == pos:
                return None
            return other
        return bind_function(_단어모드_다음위치, _docfit_namespace)
    if _docfit_symbol == '단어모드_서식보관':
        def 단어모드_서식보관(start, end):
            """자간과 장평을 한 번에 글자별로 읽어 (자간 runs, 장평 runs)로 보관한다.

            실패 시 Undo 이력 대신 정확히 복원하기 위한 원래 값이다. 한글은 여러
            글자를 선택했을 때 서식이 섞여 있으면 값을 믿을 수 없게 돌려주므로(실측)
            글자마다 읽되, 보관에는 글자 내용이 필요 없어 위치만 옮긴다(한글 호출
            약 40% 감소). 자간과 장평을 따로 읽던 두 번의 순회도 한 번으로 줄인다.
            """
            start, end = 자간조정_본문범위(start, end)
            spacing_runs, ratio_runs = [], []
            pos = start

            def 병합(runs, pos, nxt, values):
                if runs and runs[-1][2] == values:
                    runs[-1] = (runs[-1][0], nxt, values)
                else:
                    runs.append((pos, nxt, values))

            while pos[2] < end[2]:
                if 중단_요청됨():
                    return None
                nxt = _단어모드_다음위치(pos)
                if not nxt or nxt[2] > end[2]:
                    # 예전에는 예외로 문서 처리 전체가 멈췄다(2026-10-11 실측: 표 칸 '다음 단어 당김' 중). 부르는 곳은 모두
                    # None을 '이번 조정은 하지 않음'으로 처리하므로, 이 줄의 조정만 건너뛴다.
                    hwp_run('Cancel')
                    진단로그(f"[서식 보관] 문자 위치 확인 실패로 이 구간 조정을 건너뜀: {start}~{end}")
                    return None
                단어모드_범위선택(pos, nxt)
                pset = hwp.HParameterSet.HCharShape
                hwp.HAction.GetDefault('CharShape', pset.HSet)
                spacing = tuple(int(getattr(pset, key)) for key in _단어모드_자간필드)
                if any(v < -50 or v > 50 for v in spacing):
                    raise RuntimeError('허용 범위 밖의 원래 자간')
                ratio = tuple(int(getattr(pset, key)) for key in _단어모드_장평필드)
                병합(spacing_runs, pos, nxt, spacing)
                병합(ratio_runs, pos, nxt, ratio)
                pos = nxt
            hwp_run('Cancel')
            return spacing_runs, ratio_runs
        return bind_function(단어모드_서식보관, _docfit_namespace)
    if _docfit_symbol == '단어모드_자간보관':
        def 단어모드_자간보관(start, end):
            """혼합 자간을 연속 구간별 보관. 실패 시 Undo 이력 대신 정확히 복원."""
            보관 = 단어모드_서식보관(start, end)
            return None if 보관 is None else 보관[0]
        return bind_function(단어모드_자간보관, _docfit_namespace)
    if _docfit_symbol == '단어모드_자간적용':
        def 단어모드_자간적용(runs, delta):
            for start, end, values in runs:
                단어모드_범위선택(start, end)
                act = hwp.CreateAction('CharShape')
                pset = act.CreateSet()
                for key, value in zip(_단어모드_자간필드, values):
                    pset.SetItem(key, value + delta)
                if act.Execute(pset) is False:
                    raise RuntimeError('단어 모드 자간 적용 실패')
            hwp_run('Cancel')
        return bind_function(단어모드_자간적용, _docfit_namespace)
    if _docfit_symbol == '단어모드_장평보관':
        def 단어모드_장평보관(start, end):
            """혼합 장평(글자 가로비율)을 연속 구간별 보관."""
            보관 = 단어모드_서식보관(start, end)
            return None if 보관 is None else 보관[1]
        return bind_function(단어모드_장평보관, _docfit_namespace)
    if _docfit_symbol == '단어모드_장평적용':
        def 단어모드_장평적용(runs, delta):
            for start, end, values in runs:
                단어모드_범위선택(start, end)
                act = hwp.CreateAction('CharShape')
                pset = act.CreateSet()
                for key, value in zip(_단어모드_장평필드, values):
                    pset.SetItem(key, max(85, min(150, value + delta)))
                if act.Execute(pset) is False:
                    raise RuntimeError('단어 모드 장평 적용 실패')
            hwp_run('Cancel')
        return bind_function(단어모드_장평적용, _docfit_namespace)
    if _docfit_symbol == '최소_성공단계_탐색':
        def 최소_성공단계_탐색(최대, 적용후_확인, 상한먼저=False, 선형구간=8):
            """1..최대 단계 중 성공하는 가장 작은 단계를 찾는다.

            적용후_확인(step)은 step 단계를 문서에 적용하고 성공 여부를 돌려준다
            (중단이면 None). 측정(줄 배치 다시 재기)이 비싸므로 상황별로 줄인다.

            - 기본(성공이 흔하고 대개 작은 단계에서 성공하는 어절 분리): 선형구간
              (8단계)까지는 한 단계씩 올려 예전과 똑같이 찾고, 그래도 안 되면 상한을
              바로 확인한 뒤 그 사이를 이분 탐색한다. 실패 시 30번 대신 약 10번만 잰다.
            - 상한먼저(실패가 흔한 다음 단어 당김·장평 축소): 상한에서도 안 되면 한
              번만 재고 포기하고, 되면 한 단계씩 올려 가장 작은 단계를 찾는다.

            반환: 성공 단계(그 단계가 적용된 상태) 또는 None(마지막으로 시도한
            단계가 적용된 상태이므로 호출자가 원래 값으로 복원한다).
            중단 시 _단계탐색_중단을 일으킨다.
            """
            if 최대 < 1:
                return None
            단계탐색_통계["탐색"] += 1
            마지막 = [None]

            def 확인(step):
                if 중단_요청됨():
                    raise _단계탐색_중단
                결과 = 적용후_확인(step)
                if 결과 is None:
                    raise _단계탐색_중단
                단계탐색_통계["측정"] += 1
                마지막[0] = step
                return bool(결과)

            def 확정(step):
                # 마지막으로 잰 단계가 아니면 다시 적용해 확인한다. 드문 비단조 배치로
                # 실패하면 그 위 단계를 차례로 확인한다.
                if 마지막[0] == step:
                    return step
                while not 확인(step):
                    if step >= 최대:
                        return None
                    step += 1
                return step

            if 상한먼저:
                if not 확인(최대):
                    return None
                for step in range(1, 최대):
                    if 확인(step):
                        return step
                return 확정(최대)

            for step in range(1, min(선형구간, 최대) + 1):
                if 확인(step):
                    return step
            if 최대 <= 선형구간 or not 확인(최대):
                return None
            성공 = 최대
            lo, hi = 선형구간 + 1, 최대 - 1
            while lo <= hi:
                mid = (lo + hi) // 2
                if 확인(mid):
                    성공, hi = mid, mid - 1
                else:
                    lo = mid + 1
            return 확정(성공)
        return bind_function(최소_성공단계_탐색, _docfit_namespace)
    if _docfit_symbol == '단어_장평_추가축소_시도':
        def 단어_장평_추가축소_시도(start, end, anchor, word_end, 최대시도, 보관=None):
            """자간만으로 안 줄어드는 긴 어절에 장평(글자 가로비율)을 추가로 줄여본다.

            자간을 허용 범위 끝까지 밀어붙이면 글자가 다닥다닥 붙어 보기 흉해
            지므로, 사람이 수동으로 하듯 자간은 적당히만(최대 4%p) 남기고 장평을
            1%씩 최대 단어_장평_추가축소_최대_단계(기본 10단계, 90%까지) 줄이며
            다시 확인한다 — '자간 -4%, 장평 93%' 조합처럼, 자간을 극한까지
            밀어붙이는 대신 장평과 나눠 분담한다.
            """
            if not 장평_줄이기_사용:
                return False            # 장평 줄이기 끔(기본): 자간만으로 조정한다
            # 보관: 호출자가 같은 구간을 이미 읽고 원래 값으로 되돌려 둔 (자간, 장평)
            # runs. 넘겨받으면 같은 줄을 다시 글자별로 읽지 않는다.
            if 보관 is None:
                보관 = 단어모드_서식보관(start, end)
            if 보관 is None:
                return False
            spacing_runs, ratio_runs = 보관
            # 이 구간이 이전 단계·이전 회차에서 이미 일부 압축돼 있을 수 있다
            # (자간/장평은 회차 사이에 초기화되지 않는다). "이번에 -4%p까지"가
            # 아니라 "최종적으로 -4%p까지"가 되도록, 이미 줄어든 만큼을 빼고
            # 남은 여유만 쓴다 — 그래야 여러 단계·회차에 걸쳐 조금씩 계속
            # 줄어드는 일이 없다.
            현재_최소자간 = min((v for _, _, vs in spacing_runs for v in vs), default=0)
            자간_한도 = min(4, max(1, 최대시도))
            자간값 = -max(0, 자간_한도 + 현재_최소자간)
            if 자간값 and any(not -50 <= v + 자간값 <= 50 for _, _, vs in spacing_runs for v in vs):
                자간값 = 0
            자간적용됨 = False
            성공 = False
            try:
                if 자간값:
                    단어모드_자간적용(spacing_runs, 자간값)
                    자간적용됨 = True
                현재_최소장평 = min((v for _, _, vs in ratio_runs for v in vs), default=100)
                장평_바닥 = 100 - 단어_장평_추가축소_최대_단계
                여유_단계 = max(0, min(단어_장평_추가축소_최대_단계, 현재_최소장평 - 장평_바닥))

                def 장평_확인(step):
                    단어모드_장평적용(ratio_runs, -step)
                    return 단어모드_줄범위(anchor)[1][2] >= word_end[2]

                try:
                    단계 = 최소_성공단계_탐색(여유_단계, 장평_확인, 상한먼저=True)
                except _단계탐색_중단:
                    return False
                성공 = 단계 is not None
                if 성공:
                    진단로그(f"[단어 분리 보정] 자간 {자간값}%p + 장평 {현재_최소장평 - 단계}%로 해결")
                elif 여유_단계:
                    단어모드_장평적용(ratio_runs, 0)
            finally:
                if not 성공 and 자간적용됨:
                    단어모드_자간적용(spacing_runs, 0)
            return 성공
        return bind_function(단어_장평_추가축소_시도, _docfit_namespace)
    if _docfit_symbol == '다음단어_당김_시도':
        def 다음단어_당김_시도(anchor, 최대시도):
            """긴 단어 전체가 통째로 다음 줄로 밀려, 이번 줄 양쪽정렬이 단어
            사이 간격을 비정상적으로 벌린 경우를 찾아 끌어올린다.

            단어 중간에서 갈라진 경우(단어모드_분리정보가 처리)는 이미 아래
            본 루프가 다루므로 여기서는 제외한다 — 줄 끝이 이미 깨끗한 단어
            경계(공백)이고 바로 다음이 새 단어로 시작하는 경우만 다룬다.

            양쪽정렬 문서에서는 거의 모든 줄이 "단어 경계에서 깔끔하게 끝난"
            상태이므로, 끌어올릴 다음 단어가 문장부호_2줄_기준글자수(기본 5자)
            보다 길면 시도하지 않는다 — 짧은 마지막 줄 병합(문장부호_줄병합_시도)
            과 같은 "끌어올릴 가치가 있을 때만" 기준을 그대로 재사용한다. 자간은
            다음단어_당김_자간_최대_퍼센트(기본 10%p)까지만 쓰고, 그래도 안 되면
            장평도 추가로 줄인다(단어_장평_추가축소_시도, 기본 90%까지).
            """
            start, boundary = 단어모드_줄범위(anchor)
            다음글자 = 단어모드_한글자(boundary)
            if not 다음글자 or not 다음글자[2] or 다음글자[2].isspace():
                return False
            if 단어모드_분리정보(anchor) is not None:
                return False

            pos = boundary
            다음단어_끝 = boundary
            당김단어 = ''
            while True:
                if 중단_요청됨():
                    return False
                part = 단어모드_한글자(pos)
                if not part or not part[2] or part[2].isspace():
                    break
                다음단어_끝 = part[1]
                당김단어 += part[2]
                pos = part[1]
            if 다음단어_끝[2] == boundary[2]:
                return False
            if 다음단어_끝[2] - boundary[2] > 문장부호_2줄_기준글자수:
                return False

            보관 = 단어모드_서식보관(start, boundary)
            if 보관 is None:
                return False
            runs = 보관[0]
            # 정상적인 단어 경계에서의 선택적 당김은 단어 분리 오류가 아니다.
            다음단어_통계['대상'] += 1
            success = False
            changed = False
            # 단어_장평_추가축소_시도와 같은 이유로, 이 구간이 이미 어느 정도
            # 압축돼 있으면(다른 단계·회차에서) 남은 여유만큼만 쓴다 — "이번에
            # 최대 10%p"가 아니라 "최종적으로 최대 10%p"가 되도록.
            현재_최소자간 = min((v for _, _, vs in runs for v in vs), default=0)
            자간_상한 = max(0, min(최대시도, 다음단어_당김_자간_최대_퍼센트 + 현재_최소자간))
            # 자간은 -50%보다 작게 할 수 없다.
            탐색_상한 = min(자간_상한, 50 + 현재_최소자간)

            def 당김_확인(step):
                nonlocal changed
                changed = True
                단어모드_자간적용(runs, -step)
                return 단어모드_줄범위(anchor)[1][2] >= 다음단어_끝[2]

            try:
                success = 최소_성공단계_탐색(탐색_상한, 당김_확인, 상한먼저=True) is not None
            except _단계탐색_중단:
                return False
            finally:
                if changed and not success:
                    단어모드_자간적용(runs, 0)
            if not success and 단어_장평_추가축소_시도(start, boundary, anchor, 다음단어_끝, 자간_상한, 보관=보관):
                success = True
            if success:
                다음단어_통계['적용'] += 1
                단어모드_범위선택(start, boundary)
                색상_적용_현재선택()
                hwp_run('Cancel')
                진단로그(f"[다음 단어 당김 적용] {당김단어!r} / 위치={anchor}")
            else:
                다음단어_통계['미적용'] += 1
                진단로그(f"[다음 단어 당김 미적용] {당김단어!r} / 위치={anchor} / "
                         f"허용 자간 {자간_상한}단계·장평 범위 내 당김 불가, 원래 서식 복원 (오류 아님)")
            return success
        return bind_function(다음단어_당김_시도, _docfit_namespace)
    if _docfit_symbol == '어절분리_앞줄당김인가':
        def 어절분리_앞줄당김인가(left, right, 마지막줄_짧음=False):
            """화면줄 경계에서 갈라진 어절을 앞줄로 당길지(True) 다음 줄로 밀지(False).

            1) 문단 마지막 줄에 남는 글자가 빈칸 포함 5자 미만이면 무조건 당긴다.
            2) 그 외에는 글자 수가 많은 쪽으로 붙인다. 같으면 앞줄로 당긴다.
               예: '전기|버스'(2:2) → 당김, '실|질적인'(1:3) → '실'을 다음 줄로 밈.
            """
            return bool(마지막줄_짧음) or left >= right
        return bind_function(어절분리_앞줄당김인가, _docfit_namespace)
    if _docfit_symbol == '단어모드_마지막줄_짧은잔여인가':
        def 단어모드_마지막줄_짧은잔여인가(boundary):
            """경계 다음 화면줄이 문단의 마지막 줄이고, 그 줄의 글자 수가
            빈칸 포함 문장부호_2줄_기준글자수(기본 5자) 미만인지 확인한다."""
            original = hwp.GetPos()
            try:
                right = 단어모드_한글자(boundary)
                if not right:
                    return False
                _, next_end = 단어모드_줄범위(right[1])
                hwp.SetPos(*boundary)
                hwp_run('MoveParaEnd')
                para_end = hwp.GetPos()
                if para_end[:2] != boundary[:2] or para_end[2] <= boundary[2]:
                    return False
                if next_end[:2] != para_end[:2] or next_end[2] < para_end[2]:
                    return False
                단어모드_범위선택(boundary, para_end)
                text = (현재선택영역_텍스트() or '').replace('\r', '').replace('\n', '')
                return len(text) < 문장부호_2줄_기준글자수
            except Exception:
                return False
            finally:
                hwp_run('Cancel')
                hwp.SetPos(*original)
        return bind_function(단어모드_마지막줄_짧은잔여인가, _docfit_namespace)
    if _docfit_symbol == '연결부호_구간':
        def 연결부호_구간(글):
            """글 안의 가장 긴 연결 부호 구간 (시작, 끝). 없으면 None(순수 함수)."""
            찾음 = max(_연결부호.finditer(글 or ""), key=lambda m: m.end() - m.start(), default=None)
            return (찾음.start(), 찾음.end()) if 찾음 else None
        return bind_function(연결부호_구간, _docfit_namespace)
    if _docfit_symbol == '연결부호_단위들':
        def 연결부호_단위들(글):
            """[(단위 시작, 부호 시작, 부호 끝, 단위 끝)]: 연결 부호와 양옆 어절(빈칸 하나는 건너 붙인다)(순수 함수)."""
            결과 = []
            글 = 글 or ""
            for m in _연결부호.finditer(글):
                if not m.group(0).strip() and not 연결부호탭.space_connector_ok(글[:m.start()], 글[m.end():]):
                    continue            # 라벨 안 빈칸·부서 표시·줄 채움 빈칸은 연결 부호가 아니다
                왼 = m.start()
                if 왼 > 0 and 글[왼 - 1] == " " and not m.group(0).startswith(" "):
                    왼 -= 1
                while 왼 > 0 and not 글[왼 - 1].isspace():
                    왼 -= 1
                오 = m.end()
                if 오 < len(글) and 글[오] == " " and not m.group(0).endswith(" "):
                    오 += 1
                while 오 < len(글) and not 글[오].isspace():
                    오 += 1
                결과.append((왼, m.start(), m.end(), 오))
            return 결과
        return bind_function(연결부호_단위들, _docfit_namespace)
    if _docfit_symbol == '연결부호_전체_맞춤':
        def 연결부호_전체_맞춤():
            """본문 문단의 연결 단위가 줄 경계에 걸쳤으면 부호를 줄여 한 줄에 맞춘다."""
            if not 알파_연결부호_맞춤_사용:
                return True
            통계 = {"대상": 0, "자간": 0, "개수": 0, "미해결": 0}
            순회_시작()
            while True:
                if 중단_요청됨():
                    return False
                위치 = hwp.GetPos()
                if 위치[0] == 0:
                    글 = 현재문단_텍스트()
                    단위들 = 연결부호_단위들(글.rstrip("\r\n")) if 글 else []
                    if 단위들:
                        문단시작 = tuple(hwp.GetPos())
                        for 단위 in reversed(단위들):
                            결과 = _연결단위_맞춤(문단시작, 단위)
                            if 결과 is None:
                                return False
                            if 결과:
                                통계["대상"] += 1
                                통계[결과] += 1
                        hwp.SetPos(*문단시작)
                if not 범위_다음_문단으로_진행():
                    break
            if 통계["대상"]:
                로그(f"[연결 부호] 줄에 걸친 연결 단위 {통계['대상']}개: 부호 자간 축소 {통계['자간']} / 개수 줄임 {통계['개수']} / "
                     f"미해결 {통계['미해결']}")
            return True
        return bind_function(연결부호_전체_맞춤, _docfit_namespace)
    if _docfit_symbol == '_연결단위_맞춤':
        def _연결단위_맞춤(문단시작, 단위):
            """한 연결 단위를 맞춘다. '자간'·'개수'·'미해결'(걸쳤던 단위), ''(걸치지 않음·대상 아님), None(중단)."""
            단위시작, 부호시작, 부호끝, 단위끝 = 단위
            try:
                위치 = [문단_위치(문단시작, 단위시작), 문단_위치(문단시작, 부호시작),
                      문단_위치(문단시작, 부호끝, 끝쪽=True), 문단_위치(문단시작, 단위끝, 끝쪽=True)]
            except RuntimeError:
                return ""
            a, cs, ce, b = ((문단시작[0], 문단시작[1], 문단시작[2] + x) for x in 위치)

            def 한줄인가(끝):
                return 단어모드_줄범위(a)[1][2] >= 끝[2]

            if 한줄인가(b):
                return ""
            # 단위가 줄 하나보다 길면(줄 첫머리에서 시작해도 넘침) 맞출 수 없다.
            if 단어모드_줄범위(a)[0][2] == a[2]:
                return "미해결"
            # ① 부호 글자만 자간을 한도 넘어 줄인다.
            runs = 단어모드_자간보관(cs, ce)
            if runs is not None:
                상한 = 50 + min((v for _, _, vs in runs for v in vs), default=0)
                바뀜 = 성공 = False

                def 확인(step):
                    nonlocal 바뀜
                    바뀜 = True
                    단어모드_자간적용(runs, -step)
                    return 한줄인가(b)

                try:
                    step = 최소_성공단계_탐색(max(0, 상한), 확인)
                    성공 = step is not None
                    if 성공:
                        진단로그(f"[연결 부호] 부호 자간 -{step}%(한도 초과 허용)로 한 줄에 맞춤")
                        return "자간"
                except _단계탐색_중단:
                    return None
                finally:
                    if 바뀜 and not 성공:
                        단어모드_자간적용(runs, 0)
            # ② 부호 개수를 끝에서부터 하나씩 줄인다(2개는 남김).
            지운 = []
            끝 = b
            부호수 = ce[2] - cs[2]
            while 부호수 - len(지운) > 연결부호_최소개수:
                if 중단_요청됨():
                    return None
                자리 = (ce[0], ce[1], ce[2] - len(지운) - 1)
                단어모드_범위선택(자리, (자리[0], 자리[1], 자리[2] + 1))
                글자 = 현재선택영역_텍스트()
                if not 글자 or hwp_run("Delete") is False:
                    hwp_run("Cancel")
                    break
                지운.append(글자)
                끝 = (끝[0], 끝[1], 끝[2] - 1)
                if 한줄인가(끝):
                    진단로그(f"[연결 부호] 부호 {len(지운)}개 줄여 한 줄에 맞춤")
                    return "개수"
            # 맞추지 못하면 지운 부호를 되돌린다.
            if 지운:
                hwp.SetPos(*(ce[0], ce[1], ce[2] - len(지운)))
                텍스트_삽입("".join(reversed(지운)))
            return "미해결"
        return bind_function(_연결단위_맞춤, _docfit_namespace)
    if _docfit_symbol == '단어중간_줄바꿈방지':
        def 단어중간_줄바꿈방지(최대시도):
            """현재 화면줄을 처리하고 다음 경계는 호출자의 줄 순회에서 처리한다."""
            # '단어모드_분리정보'는 경계에서 양옆으로 공백을 만나면 즉시 멈추므로
            # '계약방법(공개모집' | '원칙, 수의계약)이'처럼 괄호 안 공백에서 갈라진
            # 경우는 감지하지 못한다. 아래 루프에서 먼저 자간을 좁혀 처리한다.
            for _ in range(max(1, 최대시도)):
                if 중단_요청됨():
                    return False
                if not 현재줄_끝_괄호내부_공백분리인가():
                    break
                hwp_run("MoveLineEnd")
                hwp_run("MoveSelLineBegin")
                hwp_run("CharShapeSpacingDecrease")
                색상_적용_현재선택()
                hwp_run("Cancel")
            else:
                문제줄 = 현재_화면줄_텍스트()
                검수_문제_기록(현재_처리파일, f"[괄호 안 공백 분리] {문제줄.strip()}")

            # 긴 단어 전체가 통째로 다음 줄로 밀려 양쪽정렬 간격이 벌어진 경우도
            # 같은 방식(자간 우선, 부족하면 장평 추가)으로 먼저 당겨 본다.
            #
            # 한 줄에서 딱 한 번만 시도한다 — 예전에는 성공할 때마다 같은 줄에서
            # 반복 호출했는데, 그러면 짧은 단어가 연달아 이어질 때(예: '대체
            # 가능'처럼 공백으로 나뉜 두 단어) 매번 새로 5%이내 자간/장평을
            # 재는 게 아니라 '이미 한 번 줄어든 값'을 기준으로 또 줄이는 식으로
            # 누적돼, 결국 문장 전체가 한 줄로 욱여넣어질 때까지 압축이 쌓였다.
            # 한 단어만 당기고 멈추면 각 시도의 상한(다음단어_당김_자간_최대_퍼센트)이
            # 실제 최종 압축폭의 상한으로도 그대로 유지된다.
            if 중단_요청됨():
                return False
            anchor0, _ = 단어모드_줄범위(hwp.GetPos())
            if 다음단어_당김_사용:
                다음단어_당김_시도(anchor0, 최대시도)

            # 다음 단어 당김의 탐색 함수가 경계 주변 문자를 읽으며 커서를 옮긴다.
            # 원래 화면줄로 복귀하지 않으면 바로 뒤의 분리 어절 검사가 다른 줄에서
            # 시작해 '맞춤|형' 같은 실제 문제를 놓친다.
            hwp.SetPos(*anchor0)
            anchor, _ = 단어모드_줄범위(hwp.GetPos())
            seen = set()
            failure_reason = "반복 한도 도달"
            unit_text = ""
            try:
                # 한 단어를 당긴 뒤 다른 단어가 걸칠 수도 있으므로 같은 줄 재검사.
                for _ in range(max(1, 최대시도)):
                    if 중단_요청됨():
                        return False
                    info = 단어모드_분리정보(anchor)
                    if info is None:
                        return not 중단_요청됨()
                    start, boundary, word_start, word_end, left, right = info
                    단어모드_범위선택(word_start, word_end)
                    unit_text = 현재선택영역_텍스트()
                    hwp_run('Cancel')
                    진단로그(f"[단어 판정] {unit_text!r} / {left}:{right}자 / 경계={boundary} / 범위={word_start}~{word_end}")
                    key = (boundary, word_start, word_end)
                    if key in seen:
                        failure_reason = "같은 경계 반복"
                        break
                    seen.add(key)
                    if 칸폭보다_긴_단어인가(info):
                        진단로그(f"[단어 분리] {unit_text!r} {left}:{right}자: 줄 첫머리부터 넘치는 "
                                 f"칸 폭보다 긴 단어라 조정 제외")
                        return not 중단_요청됨()
                    # 마지막 줄에 빈칸 포함 5자 미만이 남으면 무조건 앞줄로 당긴다.
                    # 그 외에는 글자 수가 많은 쪽으로 붙인다(같으면 앞줄로 당김).
                    # 예: '실|질적인'은 '실'이 있는 앞줄 자간을 넓혀 '실'을 다음 줄로
                    # 밀어낸다. 밀기는 어절 앞까지만 넓혀 어절 전체를 옮기므로
                    # '맞|춤형'이 '맞춤|형'으로 일부만 이동한 상태는 성공으로 보지 않는다.
                    마지막줄_짧음 = 단어모드_마지막줄_짧은잔여인가(boundary)
                    shrink = 어절분리_앞줄당김인가(left, right, 마지막줄_짧음)
                    # 이전 줄에서 이미 시작한 긴 단어는 어느 방향으로도 옮길 수 없다.
                    if word_start[2] < start[2] or word_end[2] <= start[2]:
                        failure_reason = "이전 줄부터 이어진 단어"
                        break
                    단어분리_통계["대상"] += 1
                    failure_reason = f"{최대시도}단계 이내 이동 실패"
                    방법 = ""

                    def 앞줄로_당기기():
                        보관 = 단어모드_서식보관(start, word_end)
                        if 보관 is None:
                            return None
                        runs = 보관[0]
                        success = False
                        changed = False
                        # 자간은 -50%보다 작게 할 수 없다.
                        상한 = min(최대시도, 50 + min((v for _, _, vs in runs for v in vs), default=0))

                        def 당김_확인(step):
                            nonlocal changed
                            changed = True
                            단어모드_자간적용(runs, -step)
                            return 단어모드_줄범위(anchor)[1][2] >= word_end[2]

                        try:
                            step = 최소_성공단계_탐색(상한, 당김_확인)
                            success = step is not None
                            if success:
                                return f"앞줄 자간 -{step}%로 당김"
                        except _단계탐색_중단:
                            return None
                        finally:
                            if changed and not success:
                                단어모드_자간적용(runs, 0)
                        # 자간만으로 안 되면 장평을 추가로 줄여 본다 — 사람이 수동으로
                        # 하듯 자간은 적당히만 남기고 장평과 나눠 분담한다.
                        if 단어_장평_추가축소_시도(start, word_end, anchor, word_end, 최대시도, 보관=보관):
                            return "앞줄 자간+장평 축소로 당김"
                        return ""

                    def 다음줄로_밀기():
                        # 어절 앞까지만 넓혀 어절 전체를 다음 줄로 보낸다. 어절 일부나
                        # 다음 줄 전체를 넓히지 않으므로 혼합 자간 상태를 남기지 않는다.
                        if word_start[2] <= start[2]:
                            return ""
                        push_runs = 단어모드_자간보관(start, word_start)
                        if push_runs is None:
                            return None
                        success = False
                        changed = False
                        # 자간은 +50%보다 크게 할 수 없다.
                        상한 = min(최대시도, 50 - max((v for _, _, vs in push_runs for v in vs), default=0))

                        def 밀기_확인(push_step):
                            nonlocal changed
                            changed = True
                            단어모드_자간적용(push_runs, push_step)
                            _, previous_end = 단어모드_줄범위(anchor)
                            next_start, next_end = 단어모드_줄범위(word_start)
                            return (previous_end[2] <= word_start[2]
                                    and next_start[2] <= word_start[2]
                                    and next_end[2] >= word_end[2])

                        try:
                            push_step = 최소_성공단계_탐색(상한, 밀기_확인)
                            success = push_step is not None
                            if success:
                                return f"앞 구간 자간 +{push_step}%로 어절 전체를 다음 줄로 밈"
                        except _단계탐색_중단:
                            return None
                        finally:
                            if changed and not success:
                                단어모드_자간적용(push_runs, 0)
                        return ""

                    # 정한 방향을 먼저 시도하고, 한도 안에서 안 되면 반대 방향으로
                    # 보완해 어절이 갈라진 채 남지 않게 한다.
                    시도순서 = (앞줄로_당기기, 다음줄로_밀기) if shrink else (다음줄로_밀기, 앞줄로_당기기)
                    for 시도 in 시도순서:
                        try:
                            결과 = 시도()
                        except RuntimeError as e:
                            # 서식 보관(읽기 전용) 단계에서 글자 위치를 확인하지 못하면
                            # 이 방향만 실패로 보고 반대 방향·다음 줄로 넘어간다. 예외를
                            # 올려 보내면 문서 전체 처리가 중단되고 결과도 저장되지
                            # 않았다(실측: 보도자료 '건강을' 위치에서 중단).
                            진단로그(f"[단어 중간 줄바꿈 방지] {unit_text!r} 서식 확인 실패로 이 방향 건너뜀: {e}")
                            결과 = ""
                        if 결과 is None:
                            return False
                        if 결과:
                            방법 = 결과
                            break
                    if not 방법:
                        단어분리_통계["실패"] += 1
                        break
                    failure_reason = ""
                    단어분리_통계["성공"] += 1
                    end = word_end if 방법.startswith("앞줄") else word_start
                    단어모드_범위선택(start, end)
                    색상_적용_현재선택()
                    hwp_run('Cancel')
                    기준 = "마지막 줄 5자 미만" if 마지막줄_짧음 else ("글자 수 같음" if left == right else "글자 수 많은 쪽")
                    진단로그(f"[단어 중간 줄바꿈 방지] {unit_text!r} {left}/{right}자 ({기준}): {방법}")
                if 단어모드_분리정보(anchor) is not None:
                    hwp.SetPos(*anchor)
                    로그(f"[단어 중간 줄바꿈 미해결] {unit_text!r}: {failure_reason}")
                    검수_문제_기록(현재_처리파일, '[단어 중간 줄바꿈 미해결] ' + 현재_화면줄_텍스트().strip())
                return True
            finally:
                hwp_run('Cancel')
                hwp.SetPos(*anchor)
        return bind_function(단어중간_줄바꿈방지, _docfit_namespace)
    if _docfit_symbol == '자간자동조정':
        def 자간자동조정(최대시도=None):
            """현재 화면줄의 단어 분리를 자간으로 푼다. 조정할 본문이 없는 줄(문두 보호)은 건너뛴다."""
            return _문두보호_줄건너뜀(_자간자동조정_본체, 최대시도)
        return bind_function(자간자동조정, _docfit_namespace)
    if _docfit_symbol == '_자간자동조정_본체':
        def _자간자동조정_본체(최대시도=None):
            if 최대시도 is None:
                최대시도 = 자간_최대시도_본문
            # 세부 작업에서 '단어 분리 최종 검사'를 선택했다면 일반 자간 옵션과
            # 무관하게 실제 화면줄의 공백 없는 어절 분리를 검사해야 한다.
            if (단어중간_줄바꿈방지_사용
                    or stage_enabled(선택_세부작업, 'word_check')):
                return 단어중간_줄바꿈방지(최대시도)

            count = 0
            이전_단어_시작 = None
            총_시도 = 0
            총_시도_상한 = max(최대시도 * 8, 40)
            붙임괄호_축소횟수 = 0
            괄호내부공백_축소횟수 = 0
            어절분리_축소횟수 = 0
            단어_장평축소횟수 = 0

            while True:
                if 중단_요청됨():
                    return False

                hwp_run("MoveLineEnd")

                # 새 모드를 꺼도 붙임표시/짧은 괄호의 의미 단위는 동일하게 보호한다.
                if 붙임의미단위_줄분리인가():
                    return 단어중간_줄바꿈방지(최대시도)

                # 붙임 괄호가 다음 화면줄로 밀린 경우에는 자간 증가를 금지하고
                # 현재 줄을 우선 축소해 괄호를 앞줄로 당긴다.
                if 현재줄_끝_붙임괄호_분리인가():
                    if 붙임괄호_축소횟수 >= 최대시도:
                        # v1.11: 포기할 때 그동안 줄인 자간을 그대로 남겨두면 문제가
                        # 해결되지도 않은 채 글자 사이만 억지로 눌려 보기 흉해진다.
                        # 일반 단어 선택 루프(아래)와 동일하게 되돌려서, 실패하더라도
                        # 최소한 원래의 자연스러운 줄바꿈 상태로 남긴다.
                        for _ in range(붙임괄호_축소횟수):
                            hwp_run("Undo")
                        문제줄 = 현재_화면줄_텍스트()
                        검수_문제_기록(현재_처리파일, f"[붙임 괄호 분리] {문제줄.strip()}")
                        return True

                    hwp_run("MoveLineEnd")
                    hwp_run("MoveSelLineBegin")
                    hwp_run("CharShapeSpacingDecrease")
                    색상_적용_현재선택()
                    hwp_run("Cancel")
                    붙임괄호_축소횟수 += 1
                    총_시도 += 1
                    if 총_시도 > 총_시도_상한:
                        return True
                    continue

                붙임괄호_축소횟수 = 0

                # '계약방법(공개모집' | '원칙, 수의계약)이'처럼 괄호 안 부연 설명의
                # 공백에서 갈라진 경우도 하나의 어절로 보고 우선 처리한다.
                if 현재줄_끝_괄호내부_공백분리인가():
                    if 괄호내부공백_축소횟수 >= 최대시도:
                        for _ in range(괄호내부공백_축소횟수):
                            hwp_run("Undo")
                        문제줄 = 현재_화면줄_텍스트()
                        검수_문제_기록(현재_처리파일, f"[괄호 안 공백 분리] {문제줄.strip()}")
                        return True

                    hwp_run("MoveLineEnd")
                    hwp_run("MoveSelLineBegin")
                    hwp_run("CharShapeSpacingDecrease")
                    색상_적용_현재선택()
                    hwp_run("Cancel")
                    괄호내부공백_축소횟수 += 1
                    총_시도 += 1
                    if 총_시도 > 총_시도_상한:
                        return True
                    continue

                괄호내부공백_축소횟수 = 0

                # '제공하' | '며,'처럼 공백 없는 한 어절이 화면줄 경계에서
                # 갈라진 경우에는 HWP의 단어 선택 로직보다 먼저 처리한다.
                # 반드시 현재(앞) 줄을 축소해야 다음 줄의 짧은 꼬리 조각이 올라온다.
                if 현재줄_끝_어절분리인가():
                    if 어절분리_축소횟수 >= 최대시도:
                        # 위 붙임 괄호 케이스와 동일한 이유로, 실패 시 되돌린다.
                        for _ in range(어절분리_축소횟수):
                            hwp_run("Undo")
                        문제줄 = 현재_화면줄_텍스트()
                        검수_문제_기록(현재_처리파일, f"[어절 줄분리] {문제줄.strip()}")
                        return True

                    hwp_run("MoveLineEnd")
                    hwp_run("MoveSelLineBegin")
                    hwp_run("CharShapeSpacingDecrease")
                    색상_적용_현재선택()
                    hwp_run("Cancel")
                    어절분리_축소횟수 += 1
                    총_시도 += 1
                    if 총_시도 > 총_시도_상한:
                        return True
                    continue

                어절분리_축소횟수 = 0

                hwp_run("MoveSelWordBegin")
                단어_시작 = hwp.GetPos()

                if 단어_시작 != 이전_단어_시작:
                    count = 0
                    단어_장평축소횟수 = 0
                    이전_단어_시작 = 단어_시작

                총_시도 += 1
                if 총_시도 > 총_시도_상한:
                    hwp_run("Cancel")
                    return True

                if count >= 최대시도:
                    # 자간만으로 해결되지 않는 긴 어절은 현재 줄의 장평을 1%씩
                    # 최대 15단계 보조 축소한다. 자간을 과도하게 30단계 이상
                    # 누르는 것보다 글자 폭을 소폭 줄이는 편이 가독성이 안정적이다.
                    if 장평_줄이기_사용 and 단어_장평축소횟수 < 15:
                        hwp_run("Cancel")
                        hwp_run("MoveLineEnd")
                        hwp_run("MoveSelLineBegin")
                        hwp_run("CharShapeRatioDecrease")
                        hwp_run("Cancel")
                        단어_장평축소횟수 += 1
                        진단로그(f"[단어 분리 보정] 장평 {단어_장평축소횟수}단계 추가 축소")
                        # 다음 반복에서 해결 여부를 다시 판정하되 기존 자간은 유지한다.
                        count = 최대시도 - 1
                        continue

                    문제줄 = 현재_화면줄_텍스트()
                    for _ in range(count + 단어_장평축소횟수):
                        hwp_run("Undo")
                    검수_문제_기록(현재_처리파일, f"[단어 분리] {문제줄.strip()}")
                    try:
                        hwp.SetPos(단어_시작[0], 단어_시작[1], 단어_시작[2])
                    except Exception:
                        pass
                    hwp_run("MoveWordEnd")
                    이전_단어_시작 = None
                    count = 0
                    단어_장평축소횟수 = 0
                    continue

                앞부분길이 = 현재선택영역_글자수()
                if 앞부분길이 == 0:
                    return True

                hwp_run("MoveSelWordEnd")
                뒷부분길이 = 현재선택영역_글자수()
                if not (앞부분길이 and 뒷부분길이):
                    hwp_run("Cancel")
                    hwp_run("Cancel")
                    return True

                hwp_run("MoveWordBegin")
                try:
                    hwp.SetPos(단어_시작[0], 단어_시작[1], 단어_시작[2])
                except Exception:
                    pass

                hwp_run("MoveSelWordEnd")
                전체_단어_텍스트 = 현재선택영역_텍스트()
                hwp_run("Cancel")

                try:
                    hwp.SetPos(단어_시작[0], 단어_시작[1], 단어_시작[2])
                except Exception:
                    pass

                목표_앞부분길이 = None
                for 괄호문자 in "(（「[{":
                    위치 = 전체_단어_텍스트.find(괄호문자)
                    if 위치 > 0 and (목표_앞부분길이 is None or 위치 < 목표_앞부분길이):
                        목표_앞부분길이 = 위치

                hwp_run("MoveLineEnd")
                hwp_run("MoveSelLineBegin")

                if 목표_앞부분길이 is not None and 목표_앞부분길이 == 앞부분길이:
                    hwp_run("Cancel")
                    return True
                elif 목표_앞부분길이 is not None:
                    # 괄호가 붙은 단어는 자간을 늘리지 않는다.
                    hwp_run("CharShapeSpacingDecrease")
                elif 앞부분길이 >= 뒷부분길이:
                    hwp_run("CharShapeSpacingDecrease")
                else:
                    hwp_run("CharShapeSpacingIncrease")

                색상_적용_현재선택()
                count += 1
                hwp_run("Cancel")
        return bind_function(_자간자동조정_본체, _docfit_namespace)
    if _docfit_symbol == '본문_기존자간조정':
        def 본문_기존자간조정():
            # 호출 전 단계가 남긴 커서 위치에 의존하면 두 번째 '최종 검사'가 문서
            # 끝에서 시작해 아무것도 검사하지 않는 경우가 생긴다. 모든 호출은
            # 본문 시작부터 독립적으로 전수 검사한다.
            순회_시작()
            직전위치 = None
            정체횟수 = 0
            검사문단 = None
            while True:
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
                    # 표 셀이면 조정하지 않고 다음 문단으로 넘어간다.
                    hwp_run("MoveParaEnd")
                    hwp_run("MoveNextChar")
                    if hwp.GetPos() == 현재위치:
                        return True
                    직전위치 = None
                    정체횟수 = 0
                    continue
                if 현재위치 == 직전위치:
                    정체횟수 += 1
                    if 정체횟수 >= 2:
                        # v1.44: 해결 불가능한 단어(예: 15단계로도 못 당기는 긴 인용부호
                        # 단어) 하나에서 순회 전체를 return True로 끝내버리면, 그 뒤에
                        # 있는 나머지 문서 전체가 단어분리 검사에서 통째로 빠진다.
                        # 이 문단(줄)만 포기하고 다음 문단으로 강제 이동해 나머지
                        # 문서는 계속 검사되도록 한다.
                        로그("본문 자간조정 순회가 같은 위치에서 반복되어 이 문단을 건너뜁니다.")
                        hwp_run("MoveParaEnd")
                        hwp_run("MoveNextChar")
                        건너뛴위치 = hwp.GetPos()
                        정체횟수 = 0
                        직전위치 = None
                        if 건너뛴위치 == 현재위치:
                            return True  # 문서 끝: 더 이상 이동할 곳이 없음
                        continue
                else:
                    정체횟수 = 0
                직전위치 = 현재위치

                result = 자간자동조정()
                if result is False:
                    return False
                hwp_run("MoveLineEnd")
                줄끝 = hwp.GetPos()
                hwp_run("MoveNextChar")
                if hwp.GetPos() == 줄끝:
                    return True
        return bind_function(본문_기존자간조정, _docfit_namespace)
    if _docfit_symbol == '문단세트_가능':
        def 문단세트_가능(회차=1):
            """세트 방식을 쓸 수 있는 조건(아니면 기존 단계별 방식)."""
            return bool(알파_문단세트_사용 and 회차 == 1 and 작업_모드 == 'all' and 표준서식_사용
                        and 쪽범위_요청 is None and not stage_enabled(선택_세부작업, 'style_unify'))
        return bind_function(문단세트_가능, _docfit_namespace)
    if _docfit_symbol == '문단세트1_글서식_적용':
        def 문단세트1_글서식_적용():
            """세트 1: 문단마다 공백 정규화 → 문장부호 뒤 공백 → 라벨/괄호를 차례로 적용한다."""
            global _문단글_캐시
            if 중단_요청됨():
                return False
            공백 = stage_enabled(선택_세부작업, 'normalize_space')
            문장부호 = stage_enabled(선택_세부작업, 'punctuation_space')
            괄호 = stage_enabled(선택_세부작업, 'parenthesis') and (괄호_축소_사용 or 괄호_라벨_볼드_사용)
            로그(f"[문단 세트 1] 시작(공백 정규화 {'O' if 공백 else 'X'}, 문장부호 뒤 공백 {'O' if 문장부호 else 'X'}, "
                 f"라벨/괄호 {'O' if 괄호 else 'X'})")
            allreplace = 0
            if 공백 and not (한칸표_보호영역 or 디자인표_보호영역 or 쪽범위_사용중()):
                allreplace = 괄호_안쪽_공백_정리_AllReplace()
            규칙들 = (문두_미음_기호_정리, 연도_따옴표_정리_문단_처리, 곧은따옴표_통일_문단_처리, 작은따옴표_통일_문단_처리,
                    날짜_구분자_정리_문단_처리, 괄호_안쪽_공백_정리_문단_처리, 쉼표_공백_정리_문단_처리,
                    단어사이_연속공백_정리_문단_처리, 공문_띄어쓰기_정리_문단_처리)
            수정 = [0] * len(규칙들)
            문장부호수 = 괄호수 = 방문 = 정체 = 0
            활성_세트_들여쓰기 = None
            _일관성_굵게_적용기호.clear()
            일관성_후보 = []
            _문단글_캐시 = {} if 알파_문단글_캐시_사용 else None
            try:
                순회_시작()
                while True:
                    if 중단_요청됨():
                        return False
                    시작위치 = hwp.GetPos()
                    방문 += 1
                    if 공백:
                        for i, 규칙 in enumerate(규칙들):
                            값 = 규칙() or 0
                            if 값:
                                _문단글_캐시_비우기()
                            수정[i] += 값
                    if 문장부호 and 문장부호_뒤_공백_보정_문단_처리():
                        문장부호수 += 1
                        _문단글_캐시_비우기()
                    if 괄호:
                        text = 현재문단_텍스트()
                        세트후속문단 = False
                        if (괄호_라벨_볼드_사용 and 항목기호_굵게_일관성_사용
                                and not 문두_라벨_굵게_제외_문단인가(text)):
                            범위 = 일관성_굵게_머리말_범위(text)
                            if 범위:
                                일관성_후보.append((hwp.GetPos(), text, 범위))
                        if 활성_세트_들여쓰기 is not None and 세트문장_후속문단인가(활성_세트_들여쓰기, text):
                            세트후속문단 = True
                        else:
                            활성_세트_들여쓰기 = None
                            if 세트문장_시작인가(text):
                                활성_세트_들여쓰기 = 세트문장_선행들여쓰기_폭(text)
                        결과 = 괄호_및_라벨_텍스트_문단_처리(세트후속문단=세트후속문단)
                        if 결과:
                            괄호수 += 결과
                    if not 범위_다음_문단으로_진행():
                        break
                    if hwp.GetPos() == 시작위치:
                        정체 += 1
                        if 정체 >= 2:
                            break
                    else:
                        정체 = 0
            finally:
                _문단글_캐시 = None
            일관성 = 0
            for 위치, text, (시작, 끝) in 일관성_후보:
                if 중단_요청됨():
                    return False
                if 항목기호_키(text) not in _일관성_굵게_적용기호:
                    continue
                try:
                    문단_범위_선택(위치, 시작, 끝)
                    문자모양_적용_현재선택(굵게=True)
                    hwp_run("Cancel")
                    일관성 += 1
                except Exception as e:
                    로그(f"항목기호 굵게 일관성 적용 중 오류(무시): {e}")
            로그(f"[문단 세트 1] 완료(방문 문단 {방문}개 / 괄호 AllReplace {allreplace}회 / 공백 규칙 수정 {sum(수정)}건 "
                 f"{수정} / 문장부호 뒤 공백 {문장부호수}건 / 라벨·괄호 {괄호수}건 / 굵게 일관성 {일관성}건)")
            return True
        return bind_function(문단세트1_글서식_적용, _docfit_namespace)
    if _docfit_symbol == '_문단세트_줄순회':
        def _문단세트_줄순회(시작, 처리):
            """본문 문단 하나의 화면줄마다 처리()를 부른다(기존 본문_기존자간조정·본문_문장부호_처리의 문단 안 부분)."""
            hwp.SetPos(*시작)
            직전 = None
            정체 = 0
            while not 중단_요청됨():
                현재 = hwp.GetPos()
                if 현재[0] != 시작[0] or 현재[1] != 시작[1]:
                    return True
                if 현재 == 직전:
                    정체 += 1
                    if 정체 >= 2:
                        return True
                else:
                    정체 = 0
                직전 = 현재
                if 처리() is False:
                    return False
                hwp_run("MoveLineEnd")
                줄끝 = hwp.GetPos()
                hwp_run("MoveNextChar")
                if hwp.GetPos() == 줄끝:
                    return True
            return False
        return bind_function(_문단세트_줄순회, _docfit_namespace)
    if _docfit_symbol == '문단세트2_배치_적용':
        def 문단세트2_배치_적용(문장부호기능=True, 부연설명_단계_사용=False):
            """세트 2: 문단마다 내어쓰기 → 부연설명 → 별표 → 자간·단어 분리 → 짧은 줄 병합(자간이 바뀌면 그 문단만 반복)."""
            global 다음단어_당김_사용
            내어쓰기 = (표준서식_내어쓰기_사용 and stage_enabled(선택_세부작업, 'hanging_indent'))
            별표 = (not 부연설명_단계_사용) and stage_enabled(선택_세부작업, 'star_align')
            자간 = stage_enabled(선택_세부작업, 'body_spacing') or stage_enabled(선택_세부작업, 'word_check')
            줄병합 = stage_enabled(선택_세부작업, 'short_line') and 문장부호기능
            로그(f"[문단 세트 2] 시작(내어쓰기 {'O' if 내어쓰기 else 'X'}, 부연설명 {'O' if 부연설명_단계_사용 else 'X'}, "
                 f"별표 {'O' if 별표 else 'X'}, 자간 {'O' if 자간 else 'X'}, 줄 병합 {'O' if 줄병합 else 'X'})")
            붙임번호_대상 = _붙임목록_내어쓰기_대상수집() if 내어쓰기 else {}
            붙임번호_기준점들 = {}
            부연상태, 별표상태 = {'부모': None}, {'별표': None}
            방문 = 반복문단 = 부연수 = 별표수 = 정체 = 0
            내어쓰기_변경문단.clear()
            순회_시작()
            try:
                while True:
                    if 중단_요청됨():
                        return False
                    hwp_run("MoveParaBegin")
                    시작 = hwp.GetPos()
                    방문 += 1
                    text = 현재문단_텍스트()
                    한칸표 = 현재_한칸표인가()
                    if 내어쓰기 and not 한칸표:
                        hwp.SetPos(*시작)
                        _내어쓰기_한문단(text, 붙임번호_대상, 붙임번호_기준점들)
                    if 부연설명_단계_사용:
                        hwp.SetPos(*시작)
                        if _부연설명_한문단(시작, text, 부연상태):
                            부연수 += 1
                    if 별표:
                        hwp.SetPos(*시작)
                        if _별표_한문단(시작, text, 별표상태):
                            별표수 += 1
                    if 시작[0] == 0 and (자간 or 줄병합):
                        hwp.SetPos(*시작)
                        if not (쪽범위_안인가(시작) and 재검사_대상인가(시작)) or (
                                _알파_일괄서식_문서 and _알파_한줄문단인가(시작)):
                            pass
                        else:
                            for 차수 in range(1, 자간_내어쓰기_최대반복 + 1):
                                if 차수 > 1:
                                    다음단어_당김_사용 = False
                                    반복문단 += 1
                                변경_전 = 자간_변경_횟수
                                if 자간 and _문단세트_줄순회(시작, 자간자동조정) is False:
                                    return False
                                if 줄병합 and _문단세트_줄순회(시작, 문장부호_줄병합_시도) is False:
                                    return False
                                if 자간_변경_횟수 == 변경_전 or not 내어쓰기:
                                    break
                                # 자간이 첫 줄 폭을 바꾸면 내어쓰기 기준점이 어긋날 수 있어 이 문단만 다시 맞춘다.
                                hwp.SetPos(*시작)
                                _내어쓰기_한문단(현재문단_텍스트(), 붙임번호_대상, 붙임번호_기준점들)
                            다음단어_당김_사용 = True
                    hwp.SetPos(*시작)
                    if not 범위_다음_문단으로_진행():
                        break
                    if tuple(hwp.GetPos()) == tuple(시작):
                        정체 += 1
                        if 정체 >= 2:
                            break
                    else:
                        정체 = 0
            finally:
                다음단어_당김_사용 = True
            로그(f"[문단 세트 2] 완료(방문 문단 {방문}개 / 부연설명 {부연수}건 / 별표 {별표수}건 / "
                 f"자간 변경으로 다시 맞춘 문단 {반복문단}회)")
            return True
        return bind_function(문단세트2_배치_적용, _docfit_namespace)
    if _docfit_symbol == '_괄호따옴표_시작문자인가':
        def _괄호따옴표_시작문자인가(ch):
            """여는/닫는 괄호·따옴표류인지 판정한다.

            ``( 6~16번) : ...`` 처럼 괄호로 시작하는 라벨 문단은 실제로는
            "괄호 라벨"이지 ※·ㅇ·□ 같은 공문서 항목 기호(문장부호)가 아니다.
            Unicode P(구두점)/S(기호) 카테고리 전체를 마커로 인식하는 광범위한
            폴백이 여는/닫는 괄호(Ps/Pe)와 따옴표(Pi/Pf)까지 마커로 오인해서,
            "(6~16번)" 같은 라벨을 "※ 내용"과 같은 방식(기호 뒤에 공백 1칸 강제
            삽입)으로 잘못 처리하는 문제가 있었다. 괄호/따옴표류만 폴백에서
            제외한다.
            """
            if not ch:
                return False
            return unicodedata.category(ch) in ("Ps", "Pe", "Pi", "Pf")
        return bind_function(_괄호따옴표_시작문자인가, _docfit_namespace)
    if _docfit_symbol == '문장부호_시작인가':
        def 문장부호_시작인가(text):
            if not text:
                return False
            text = text.lstrip()
            if not text:
                return False
            for pattern in 항목_패턴:
                if pattern.match(text):
                    return True
            first = text[0]
            if first in 공문서_기호:
                return True
            if _괄호따옴표_시작문자인가(first):
                return False
            category = unicodedata.category(first)
            return category.startswith("P") or category.startswith("S")
        return bind_function(문장부호_시작인가, _docfit_namespace)
    if _docfit_symbol == '문장부호_마커_끝위치':
        def 문장부호_마커_끝위치(text):
            if not text:
                return None
            벗긴텍스트 = text.lstrip()
            if not 벗긴텍스트:
                return None
            선행공백_길이 = len(text) - len(벗긴텍스트)
            별표 = re.match(r"[*＊]+", 벗긴텍스트)
            if 별표:
                return 선행공백_길이 + 별표.end()
            for pattern in 항목_패턴:
                m = pattern.match(벗긴텍스트)
                if m:
                    return 선행공백_길이 + m.end()
            first = 벗긴텍스트[0]
            if first in 공문서_기호:
                return 선행공백_길이 + 1
            if _괄호따옴표_시작문자인가(first):
                return None
            category = unicodedata.category(first)
            if category.startswith("P") or category.startswith("S"):
                return 선행공백_길이 + 1
            return None
        return bind_function(문장부호_마커_끝위치, _docfit_namespace)
    if _docfit_symbol == '세트문장_시작인가':
        def 세트문장_시작인가(text):
            """세트문장의 최상위 시작 문단인지 판정한다.

            일반 따옴표/괄호 등 모든 유니코드 문장부호를 대상으로 하지 않고,
            공문서에서 실제 항목 표지로 쓰는 기호와 번호 패턴만 대상으로 한다.
            """
            if not text:
                return False
            벗긴텍스트 = text.lstrip(" \t")
            if not 벗긴텍스트:
                return False
            for pattern in 항목_패턴:
                if pattern.match(벗긴텍스트):
                    return True
            return 벗긴텍스트[0] in 공문서_기호
        return bind_function(세트문장_시작인가, _docfit_namespace)
    if _docfit_symbol == '문단_자간보호_선행부_오프셋':
        def 문단_자간보호_선행부_오프셋(text):
            """자간·장평 조정이 바꾸지 않는 선행부(항목기호·빈칸·괄호/콜론 라벨)가 끝나는 문자 위치.

            내어쓰기 기준에서 괄호 라벨 뒤 첫 글자 규칙을 폐지했지만(2026-10-10), 라벨 글자의 자간이 문단마다
            달라지지 않도록 괄호 라벨까지는 이전처럼 보호한다. 서식 복사 규칙이 '고정 값'·'없음'이면 None.
            """
            규칙 = 복사_내어쓰기_규칙(text)
            if 규칙 in ("fixed", "none"):
                return None
            if 규칙 == "after_marker":
                return _여는낫표_건너뛰기(text, _문단_기호뒤_오프셋(text))
            return _여는낫표_건너뛰기(text, _문단_본문시작_오프셋(text, 괄호라벨_뒤=True))
        return bind_function(문단_자간보호_선행부_오프셋, _docfit_namespace)
    if _docfit_symbol == '컨트롤_내부_자간조정':
        def 컨트롤_내부_자간조정():
            """표/글상자 등 모든 컨트롤 영역의 단어 분리를 보정한다.

            한 칸 표(제목·요지·개요 박스)는 표 셀이 아니라 본문과 다름없는 긴 문장이므로
            단어 분리 재시도 예산도 표용(자간_최대시도_표, 짧음)이 아니라 본문용
            (자간_최대시도_본문)을 써야 한다. 이 함수는 이미 한칸표영역을 계산해 공백
            정리 호출 여부를 가르는 데는 쓰고 있었지만, 정작 재시도 예산 선택에는
            반영하지 않아 한 칸 표 안의 단어 분리가 5단계 만에 포기되고 있었다.
            """
            한칸표영역 = 한칸표_영역_목록()
            # 제목·중제목·붙임 서식 표와 사용자가 꾸민 표의 칸 글(예: 담당자 칸 '담당관:◎◎◎')은 공백 규칙으로
            # 바꾸지 않는다. 예전에는 콜론 공백 규칙이 담당자 칸에 빈칸을 넣어 서식 예시를 그대로 재연하지 못했다
            # (서식 재연 시험, 2026-10-16). 보호 영역을 확인하지 못하면 여러 칸 표의 공백 규칙을 건너뛴다.
            서식표영역 = None
            if 작업_모드 != "spacing":
                try:
                    서식표영역 = 서식표_보호영역_조사() | set(디자인표_보호영역 or ())
                except Exception as e:
                    진단로그(f"서식 표 보호 영역 확인 실패로 표 칸 공백 규칙을 건너뜀: {e}")
            area = 1
            while True:
                if 중단_요청됨():
                    return False
                area += 1
                hwp.SetPos(area, 0, 0)
                if hwp.GetPos()[0] != area:
                    break
                if 쪽범위_사용중() and area not in 쪽범위_컨트롤영역:
                    continue
                if not 재검사_영역인가(area):
                    continue
                if 표셀_자간_제외인가():
                    진단로그(f"[표 안 문장 제외] 영역 {area}: 자간 조정 안 함")
                    continue
                if 숫자_표칸인가():
                    continue
                while True:
                    if 중단_요청됨():
                        return False
                    시작위치 = hwp.GetPos()
                    현재영역_한칸표 = hwp.GetPos()[0] in 한칸표영역
                    # 표/글상자/각주/미주 내부 텍스트도 본문과 동일한 공백 규칙을 적용한다.
                    if (작업_모드 != "spacing" and not 현재영역_한칸표
                            and 서식표영역 is not None and area not in 서식표영역):
                        괄호_안쪽_공백_정리_문단_처리()
                        쉼표_공백_정리_문단_처리()
                        콜론_공백_정리_문단_처리()
                    최대시도 = (자간_최대시도_본문 if 현재영역_한칸표 or 넓은_표칸_줄인가()
                            else 자간_최대시도_표)
                    result = 자간자동조정(최대시도=최대시도)
                    if result is False:
                        return False
                    hwp_run("MoveLineEnd")
                    줄끝 = hwp.GetPos()
                    hwp_run("MoveNextChar")
                    if hwp.GetPos()[0] != area:
                        break
                    # 셀의 마지막 줄에서는 MoveNextChar가 줄 끝에 머문다. 시작 위치와만
                    # 비교하면 같은 줄을 한 번 더 처리했다(실측: 표 셀마다 다음 단어
                    # 당김을 두 번 시도해 한 번에 약 5초씩 낭비).
                    if hwp.GetPos() in (시작위치, 줄끝):
                        break
            return True
        return bind_function(컨트롤_내부_자간조정, _docfit_namespace)
    if _docfit_symbol == '한칸표_자간조정':
        def 한칸표_자간조정():
            """서식 정리에서도 개요 등 한 칸 표의 단어 분리를 보정한다.

            한칸표_보호영역(=한칸표_영역_목록)에 들어가는 표는 정의상 셀이 A1 하나뿐인
            표뿐이다. 실제 데이터 표의 짧은 셀이 아니라 제목·요지·개요 박스처럼 표
            형태를 빌린 본문형 긴 문장이므로, 표 셀용으로 정해둔 짧은 재시도 예산
            (자간_최대시도_표)이 아니라 본문과 동일한 예산(자간_최대시도_본문)을 써야
            한다. 표 전용 예산을 쓰면 본문에서는 무리 없이 풀리는 정도의 단어 분리도
            이 박스 안에서는 예산 부족만으로 실패로 남는다.
            """
            original = hwp.GetPos()
            try:
                for area in sorted(한칸표_보호영역):
                    hwp.SetPos(area, 0, 0)
                    if hwp.GetPos()[0] != area:
                        continue
                    if 쪽범위_사용중() and area not in 쪽범위_컨트롤영역:
                        continue
                    if 표셀_자간_제외인가():
                        진단로그(f"[표 안 문장 제외] 영역 {area}: 자간 조정 안 함")
                        continue
                    while True:
                        if 중단_요청됨():
                            return False
                        start = hwp.GetPos()
                        if 자간자동조정(최대시도=자간_최대시도_본문) is False:
                            return False
                        hwp_run('MoveLineEnd')
                        end = hwp.GetPos()
                        hwp_run('MoveNextChar')
                        nxt = hwp.GetPos()
                        if nxt[0] != area or nxt in (start, end):
                            break
                return True
            finally:
                hwp_run('Cancel')
                hwp.SetPos(*original)
        return bind_function(한칸표_자간조정, _docfit_namespace)
    if _docfit_symbol == '표셀_자간_제외인가':
        def 표셀_자간_제외인가():
            """'표 서식 내 문장도 자간조정하기'가 꺼져 있고 커서가 표 셀 안이면 True."""
            if hwp is not None and 디자인표_보호영역 and hwp.GetPos()[0] in 디자인표_보호영역:
                return True   # 사용자가 꾸민 장식 표 칸은 자간·줄 작업을 하지 않는다
            return (not 표_자간조정_사용) and 현재_표셀인가()
        return bind_function(표셀_자간_제외인가, _docfit_namespace)
    if _docfit_symbol == '컨트롤_줄병합_대상인가':
        def 컨트롤_줄병합_대상인가():
            """표·글상자 안 줄 병합 대상 여부(쪽 범위·표 제외 설정 반영)."""
            if not 쪽범위_안인가():
                return False
            return not 표셀_자간_제외인가()
        return bind_function(컨트롤_줄병합_대상인가, _docfit_namespace)
    if _docfit_symbol == '문서_전체_자간_초기화':
        def 문서_전체_자간_초기화():
            """항목기호·라벨을 제외한 본문·컨트롤의 자간을 0%로 되돌린다.

            이 프로그램을 이미 한 번 이상 돌렸거나 사용자가 손으로 자간을 만져둔
            문서를 다시 처리하면, 잔여 자간값 위에 압축이 계속 누적되어 HWP의
            자간 조정 가능 범위(최솟값)에 금방 닿아버린다. 그러면 겉보기엔
            "본문 자간 자동조정"이 여러 번 시도해도 실제로는 더 줄어들 여지가
            없어 단어 분리가 그대로 남는다. 2회차 처리를 시작하기 전, 문서
            조정 가능한 본문만 한 번 0%로 되돌려 압축 여유를 확보한 채로
            자간조정을 시작하도록 한다. 회차마다 반복하면 1회차의 압축 결과가
            지워지므로 문서당 정확히 한 번만 호출해야 한다.
            """
            if hwp is None:
                return False
            try:
                hwp_run("Cancel")
                hwp_run("MoveDocBegin")
                def 영역_초기화(area):
                    while True:
                        if 중단_요청됨():
                            return False
                        hwp_run('MoveParaBegin')
                        start = hwp.GetPos()
                        if start[0] != area or (area == 0 and 쪽범위_끝지남(start)):
                            break
                        hwp_run('MoveParaEnd')
                        end = hwp.GetPos()
                        body, end = 자간조정_본문범위(start, end)
                        if body[2] < end[2]:
                            단어모드_범위선택(body, end)
                            문자모양_적용_현재선택(자간=0)
                            hwp_run('Cancel')
                        hwp.SetPos(*end)
                        hwp_run('MoveNextParaBegin')
                        nxt = hwp.GetPos()
                        if nxt[0] != area or nxt[1] <= start[1]:
                            break
                    return True

                순회_시작()
                if 영역_초기화(0) is False:
                    return False

                area = 1
                while True:
                    if 중단_요청됨():
                        return False
                    area += 1
                    hwp.SetPos(area, 0, 0)
                    if hwp.GetPos()[0] != area:
                        break
                    if 쪽범위_사용중() and area not in 쪽범위_컨트롤영역:
                        continue
                    if 표셀_자간_제외인가() or 숫자_표칸인가():
                        continue
                    if 영역_초기화(area) is False:
                        return False

                hwp_run("MoveDocBegin")
                return True
            except Exception as e:
                로그(f"문서 전체 자간 초기화 실패(무시): {e}")
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
                return False
        return bind_function(문서_전체_자간_초기화, _docfit_namespace)
    raise KeyError(_docfit_symbol)
