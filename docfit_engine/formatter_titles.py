"""제목·개요·중제목·붙임의 공통 구조 및 적용 — formatter의 호환 전역으로 바인딩할 원본 정의."""

SYMBOLS = ('개요붙임_원본자료', '붙임_유형판별', '붙임_대상찾기', '중제목_글칸들', '중제목_유형판별', '중제목_대상찾기', '중제목_원본자료', '_구역_본문폭', '_예정_좌우여백', '_최종_본문폭', '_빈_문단인가', '_문단사이_빈줄_삭제', '_문단_본문글', '_서식표_뒤_빈줄_삭제', '_서식표_가로맞춤', '_중제목_번호굵게_적용', '중제목_표서식_복사', '_중제목_글자치수', '_중제목_문단폭', '_중제목_칸폭_맞춤', '개요_표인가', '제목_xml이름', '제목_자식', '제목_셀들', '제목_문단들', '제목_문자열', '_한칸_제목글인가', '_기타_제목표인가', '_한칸_제목표인가', '제목_유형판별', '제목_대상찾기', '서식표_종류판별', '_서식표_예시', '제목2행1열_원본자료', '제목_원본자료', '제목_참조병합', '날짜칸인가', '제목_날짜칸_한줄', '제목_표서식_복사', '제목_문단_가운데정렬', '제목_괄호부연_축소', '제목_hwpx_처리', '_제목_임시hwpx_저장', '이전_작업_임시폴더_정리', '_제목_임시폴더_정리', '서식구조_조사', '제목4종_현재문서_조사', '제목4종_현재문서_적용', '붙임_hwpx_처리', '중제목_hwpx_처리', '제목_부제_크기_해석', '제목_부제_크기_반영', '제목_담당자_글_반영', '_설정_담당자_글인가', '_서식표_기준', '제목_부제_크기', '_칸_글_지우기', '_칸_날짜_현행화', '_빈칸_서식_참조_변환', '_칸_글_넣기', '서식표_생성', '_제목개요_빈줄_정리', '_서식표_글', '_서식표_글_확인', '라벨_서식표_적용', '_문서_표번호', '_서식표_번호_부여', '제목개요폭_hwpx_처리', '상자서식_hwpx_처리', '쪽번호_hwpx_처리', '붙임2종_현재문서_조사', '제목붙임_선행적용', '정밀표_선행적용', '붙임2종_현재문서_적용')

def _install(*, _docfit_namespace, _docfit_symbol, bind_function):
    global 개요붙임_원본자료, 붙임_유형판별, 붙임_대상찾기, 중제목_글칸들, 중제목_유형판별, 중제목_대상찾기, 중제목_원본자료, _구역_본문폭, _예정_좌우여백, _최종_본문폭, _빈_문단인가, _문단사이_빈줄_삭제, _문단_본문글, _서식표_뒤_빈줄_삭제, _서식표_가로맞춤, _중제목_번호굵게_적용, 중제목_표서식_복사, _중제목_글자치수, _중제목_문단폭, _중제목_칸폭_맞춤, 개요_표인가, 제목_xml이름, 제목_자식, 제목_셀들, 제목_문단들, 제목_문자열, _한칸_제목글인가, _기타_제목표인가, _한칸_제목표인가, 제목_유형판별, 제목_대상찾기, 서식표_종류판별, _서식표_예시, 제목2행1열_원본자료, 제목_원본자료, 제목_참조병합, 날짜칸인가, 제목_날짜칸_한줄, 제목_표서식_복사, 제목_문단_가운데정렬, 제목_괄호부연_축소, 제목_hwpx_처리, _제목_임시hwpx_저장, 이전_작업_임시폴더_정리, _제목_임시폴더_정리, 서식구조_조사, 제목4종_현재문서_조사, 제목4종_현재문서_적용, 붙임_hwpx_처리, 중제목_hwpx_처리, 제목_부제_크기_해석, 제목_부제_크기_반영, 제목_담당자_글_반영, _설정_담당자_글인가, _서식표_기준, 제목_부제_크기, _칸_글_지우기, _칸_날짜_현행화, _빈칸_서식_참조_변환, _칸_글_넣기, 서식표_생성, _제목개요_빈줄_정리, _서식표_글, _서식표_글_확인, 라벨_서식표_적용, _문서_표번호, _서식표_번호_부여, 제목개요폭_hwpx_처리, 상자서식_hwpx_처리, 쪽번호_hwpx_처리, 붙임2종_현재문서_조사, 제목붙임_선행적용, 정밀표_선행적용, 붙임2종_현재문서_적용
    if _docfit_symbol == '개요붙임_원본자료':
        def 개요붙임_원본자료():
            payload = json.loads(zlib.decompress(base64.b64decode(_개요붙임3종_XML)).decode('utf-8'))
            return safe_xml_fromstring(payload['header']), safe_xml_fromstring(payload['section'])
        return bind_function(개요붙임_원본자료, _docfit_namespace)
    if _docfit_symbol == '붙임_유형판별':
        def 붙임_유형판별(table):
            """붙임 표: 유형1=1행3열(가운데 빈칸), 유형2=1행2열."""
            cells = 제목_셀들(table)
            rows, cols = int(table.get('rowCnt', '0')), int(table.get('colCnt', '0'))
            if rows != 1 or cols not in (2, 3) or len(cells) != cols:
                return None
            first = 제목_문자열(cells[0]).strip()
            last = 제목_문자열(cells[-1]).strip()
            if not re.match(r'^붙임(?:\s*\d+)?(?:\s|$)', first):
                return None
            if not last:
                return None
            if cols == 3 and 제목_문자열(cells[1]).strip():
                return None
            return 1 if cols == 3 else 2
        return bind_function(붙임_유형판별, _docfit_namespace)
    if _docfit_symbol == '붙임_대상찾기':
        def 붙임_대상찾기(section):
            """문서의 각 쪽 첫부분에 놓이는 '붙임' 표를 구조/문구로 판별한다.
            HWPX는 페이지 번호를 직접 제공하지 않는 경우가 있으므로, '붙임' 라벨과
            1x3/1x2 구조를 동시에 만족할 때만 대상으로 삼아 일반 표 오인을 막는다.
            """
            result = []
            ordinal = 0
            for p in section:
                for run in p:
                    for table in run:
                        if 제목_xml이름(table) != 'tbl':
                            continue
                        kind = 붙임_유형판별(table)
                        if kind:
                            result.append((ordinal, kind))
                        ordinal += 1
            return result
        return bind_function(붙임_대상찾기, _docfit_namespace)
    if _docfit_symbol == '중제목_글칸들':
        def 중제목_글칸들(table, 숫자번호=True):
            """중제목 모양 표의 글 칸 번호 목록(아니면 빈 목록).

            1행 2열 이상이고, 첫 칸에는 로마자 번호(숫자번호면 아라비아 숫자 번호도)만 있고, 2열 또는 3열에 글이 있는 표다. 칸 병합이나
            표·그림이 든 칸, 붙임·기호 문장으로 시작하는 글이 있으면 중제목으로 보지 않는다.
            """
            cells = 제목_셀들(table)
            rows, cols = int(table.get('rowCnt', '0')), int(table.get('colCnt', '0'))
            if rows != 1 or cols < 2 or len(cells) != cols:
                return []
            for c in cells:
                if any(제목_xml이름(x) in ('tbl', 'pic', 'ole', 'rect', 'fieldBegin') for x in c.iter()):
                    return []
                span = 제목_자식(c, 'cellSpan')
                if span is not None and (span.get('colSpan', '1') != '1' or span.get('rowSpan', '1') != '1'):
                    return []
            texts = [제목_문자열(c).strip() for c in cells]
            if not (_중제목_번호_숫자포함 if 숫자번호 else _중제목_번호).match(texts[0]):
                return []
            글칸 = [i for i, text in enumerate(texts) if i and text]
            if not set(글칸) & {1, 2}:
                return []
            if any(len(texts[i]) > 80 or re.match(r'^[□ㅁㅇ○※*\-]', texts[i]) or texts[i].startswith('붙임') for i in 글칸):
                return []
            return 글칸
        return bind_function(중제목_글칸들, _docfit_namespace)
    if _docfit_symbol == '중제목_유형판별':
        def 중제목_유형판별(table):
            """중제목 서식 표: 1행, 첫 칸은 번호, 다음 칸(유형2) 또는 다음다음 칸(유형1)에 글.

            유형1 = 1행3열(번호·빈칸·글), 유형2 = 1행2열(번호·글). 번호는 로마자만 본다. 그 밖의 중제목 모양 표(숫자 번호,
            번호·글·빈칸 등)는 서식은 그대로 두고 글 칸 폭만 맞춘다(중제목_대상찾기의 'fit').
            """
            cols = int(table.get('colCnt', '0'))
            if cols not in (2, 3) or 중제목_글칸들(table, 숫자번호=False) != [cols - 1]:
                return None
            return 1 if cols == 3 else 2
        return bind_function(중제목_유형판별, _docfit_namespace)
    if _docfit_symbol == '중제목_대상찾기':
        def 중제목_대상찾기(section):
            """각 구역의 최상위 표 중 중제목 구조인 표의 (순번, 유형) 목록. 유형 'fit'은 글 칸 폭만 맞출 표다."""
            result = []
            ordinal = 0
            for p in section:
                for run in p:
                    for table in run:
                        if 제목_xml이름(table) != 'tbl':
                            continue
                        kind = 중제목_유형판별(table) or ('fit' if 중제목_글칸들(table) else None)
                        if kind:
                            result.append((ordinal, kind))
                        ordinal += 1
            return result
        return bind_function(중제목_대상찾기, _docfit_namespace)
    if _docfit_symbol == '중제목_원본자료':
        def 중제목_원본자료():
            payload = json.loads(zlib.decompress(base64.b64decode(_중제목_XML)).decode('utf-8'))
            return safe_xml_fromstring(payload['header']), safe_xml_fromstring(payload['section'])
        return bind_function(중제목_원본자료, _docfit_namespace)
    if _docfit_symbol == '_구역_본문폭':
        def _구역_본문폭(section, 기본값=42520):
            """구역의 쪽 폭에서 좌우 여백을 뺀 본문 폭(HWPUNIT). 찾지 못하면 기본값(A4 기본 42520).

            가로 방향 용지(landscape="NARROWLY")도 width·height는 세로 기준 용지 치수 그대로라 높이가 쪽 폭이다
            (실측 2026-10-03: 가로 구역 줄 폭 72848 = 높이 84188 − 좌우 여백 11338).
            """
            for x in section.iter():
                if 제목_xml이름(x) == 'pagePr':
                    margin = next((m for m in x if 제목_xml이름(m) == 'margin'), None)
                    try:
                        폭 = int(x.get('height') if x.get('landscape') == 'NARROWLY' else x.get('width'))
                        return 폭 - int(margin.get('left')) - int(margin.get('right'))
                    except (TypeError, ValueError, AttributeError):
                        break
            return 기본값
        return bind_function(_구역_본문폭, _docfit_namespace)
    if _docfit_symbol == '_예정_좌우여백':
        def _예정_좌우여백():
            """이번 작업에서 보고서 표준서식이 편집 여백을 바꿀 예정이면 (왼쪽, 오른쪽) 여백(HWPUNIT), 아니면 None.

            표준서식_전체_적용이 페이지_여백_설정(표준서식_설정['여백_mm'])을 부르는 조건과 같다.
            """
            if not (작업_모드 in ('format', 'all') and 표준서식_선행_사용 and 표준서식_여백_사용 and 쪽범위_요청 is None
                    and stage_enabled(선택_세부작업, 'standard_format', 작업_모드)):
                return None
            mm = (표준서식_설정 or {}).get('여백_mm') or {}
            try:
                표준 = tuple(int(round(float(mm[k]) * 7200 / 25.4)) for k in ('left', 'right'))
            except (KeyError, TypeError, ValueError):
                return None
            # 원본 여백이 더 좁으면 원본을 두므로(페이지_여백_설정과 같은 규칙) 그 값으로 본문 폭을 잰다.
            원본 = _현재_쪽여백()
            return (_표준_또는_원본여백("LeftMargin", 표준[0], 원본), _표준_또는_원본여백("RightMargin", 표준[1], 원본))
        return bind_function(_예정_좌우여백, _docfit_namespace)
    if _docfit_symbol == '_최종_본문폭':
        def _최종_본문폭(section):
            """표준서식이 바꿀 편집 여백까지 반영한 본문 폭(HWPUNIT). 여백을 바꿀 예정이 없으면 지금 여백으로 재고,
            쪽 정보가 없으면 None. 가로 방향 용지는 높이가 쪽 폭이다(_구역_본문폭과 같음)."""
            여백 = _예정_좌우여백()
            if 여백 is None:
                return _구역_본문폭(section, None)
            for x in section.iter():
                if 제목_xml이름(x) == 'pagePr':
                    try:
                        return int(x.get('height') if x.get('landscape') == 'NARROWLY' else x.get('width')) - 여백[0] - 여백[1]
                    except (TypeError, ValueError):
                        return None
            return None
        return bind_function(_최종_본문폭, _docfit_namespace)
    if _docfit_symbol == '_빈_문단인가':
        def _빈_문단인가(p):
            """글자·표·개체 없이 빈 run과 줄 배치 정보만 있는 본문 문단(빈 줄)인지."""
            if 제목_xml이름(p) != 'p':
                return False
            for child in p:
                이름 = 제목_xml이름(child)
                if 이름 == 'linesegarray':
                    continue
                if 이름 != 'run':
                    return False
                for x in child:
                    if 제목_xml이름(x) != 't' or len(x) or (x.text or '').strip():
                        return False
            return True
        return bind_function(_빈_문단인가, _docfit_namespace)
    if _docfit_symbol == '_문단사이_빈줄_삭제':
        def _문단사이_빈줄_삭제(root, 앞문단, 뒷문단):
            """두 본문 문단 사이가 빈 줄로만 채워져 있으면 그 빈 줄을 지우고 지운 수를 돌려준다.

            사이에 글·표 등 다른 내용이 있으면 한 쌍이 아니므로 그대로 둔다.
            """
            문단들 = list(root)
            if 앞문단 is 뒷문단 or 앞문단 not in 문단들 or 뒷문단 not in 문단들:
                return 0
            처음, 끝 = 문단들.index(앞문단), 문단들.index(뒷문단)
            사이 = 문단들[처음 + 1:끝]
            if 끝 <= 처음 or not 사이 or not all(_빈_문단인가(p) for p in 사이):
                return 0
            for p in 사이:
                root.remove(p)
            return len(사이)
        return bind_function(_문단사이_빈줄_삭제, _docfit_namespace)
    if _docfit_symbol == '_문단_본문글':
        def _문단_본문글(p):
            """본문 문단에 바로 든 글(표·개체 안 글은 빼고, 빈칸 요소 뒤 글은 넣는다)."""
            return ''.join((t.text or '') + ''.join(s.tail or '' for s in t)
                           for r in p if 제목_xml이름(r) == 'run' for t in r if 제목_xml이름(t) == 't')
        return bind_function(_문단_본문글, _docfit_namespace)
    if _docfit_symbol == '_서식표_뒤_빈줄_삭제':
        def _서식표_뒤_빈줄_삭제(root, 표문단):
            """제목·개요 서식 표 문단 바로 뒤의 빈 줄을 첫 항목기호 문장 앞까지 지우고 지운 수를 돌려준다.

            제목·개요 표와 첫 항목기호 문장 사이는 그 문장의 문단 위 여백으로만 띄운다(2026-10-03 사용자 요청:
            빈 줄이 없어야 함). 빈 줄 다음이 항목기호 문장이 아니면(일반 글·표 등) 그대로 둔다.
            """
            문단들 = list(root)
            if 표문단 not in 문단들:
                return 0
            처음 = 끝 = 문단들.index(표문단) + 1
            while 끝 < len(문단들) and _빈_문단인가(문단들[끝]):
                끝 += 1
            if 끝 == 처음 or 끝 >= len(문단들) or not 보고서_문단역할(_문단_본문글(문단들[끝]).strip()):
                return 0
            for p in 문단들[처음:끝]:
                root.remove(p)
            return 끝 - 처음
        return bind_function(_서식표_뒤_빈줄_삭제, _docfit_namespace)
    if _docfit_symbol == '_서식표_가로맞춤':
        def _서식표_가로맞춤(table, 본문폭, 비례=False):
            """제목·개요 서식 표를 쪽 좌우 여백 사이 최대 폭(본문 폭 − 표 바깥 여백)으로 맞춘다.

            행마다 칸 너비 합이 표 폭과 같게, 그 행에서 가장 넓은 칸이 차이를 받는다(날짜 칸처럼 좁은 칸은 그대로).
            행 병합 칸이 있거나 가장 넓은 칸이 너무 좁아지면 모든 칸을 같은 비율로 줄인다. 비례이면(서식 프로필의 예시
            표를 쓴 경우) 행마다 예시 표의 열 비율을 그대로 두고 폭만 맞춘다(2026-10-04 결정 1).
            """
            size, out = 제목_자식(table, 'sz'), 제목_자식(table, 'outMargin')
            if size is None or not 본문폭:
                return
            try:
                바깥 = (int(out.get('left', '0')) + int(out.get('right', '0'))) if out is not None else 0
                이전 = int(size.get('width', '0'))
            except ValueError:
                return
            목표 = int(본문폭) - 바깥
            if 목표 <= 0 or 이전 <= 0 or 목표 == 이전:
                return
            행들 = [[c for c in row if 제목_xml이름(c) == 'tc'] for row in table if 제목_xml이름(row) == 'tr']
            병합 = any((제목_자식(c, 'cellSpan') is not None and 제목_자식(c, 'cellSpan').get('rowSpan', '1') != '1')
                       for 행 in 행들 for c in 행)
            for 행 in 행들:
                크기들 = [제목_자식(c, 'cellSz') for c in 행]
                if not 크기들 or any(s is None for s in 크기들):
                    continue
                너비 = [int(s.get('width', '0')) for s in 크기들]
                if 비례 and not 병합 and sum(너비) > 0:
                    새너비들 = [max(1, round(w * 목표 / sum(너비))) for w in 너비]
                    새너비들[-1] += 목표 - sum(새너비들)
                    for s, w in zip(크기들, 새너비들):
                        s.set('width', str(w))
                    continue
                넓은 = 너비.index(max(너비))
                새너비 = 너비[넓은] + 목표 - sum(너비)
                if 병합 or 새너비 < 1000:
                    for s, w in zip(크기들, 너비):
                        s.set('width', str(max(1, round(w * 목표 / 이전))))
                else:
                    크기들[넓은].set('width', str(새너비))
            size.set('width', str(목표))
        return bind_function(_서식표_가로맞춤, _docfit_namespace)
    if _docfit_symbol == '_중제목_번호굵게_적용':
        def _중제목_번호굵게_적용(header, maps):
            """번호 굵게를 끈 경우 병합된 번호 글자모양(기준 8번)에서 굵게를 뺀다(중제목 전용 사본이라 안전)."""
            if 중제목_번호굵게:
                return
            merged = maps['charProperties'].get('8')
            for cp in header.iter():
                if 제목_xml이름(cp) == 'charPr' and cp.get('id') == merged:
                    for b in [x for x in cp if 제목_xml이름(x) == 'bold']:
                        cp.remove(b)
        return bind_function(_중제목_번호굵게_적용, _docfit_namespace)
    if _docfit_symbol == '중제목_표서식_복사':
        def 중제목_표서식_복사(table, sample, maps, kind, 최대폭=None, header=None):
            """중제목 글은 그대로 두고 표·칸·문단·글자 서식만 기준 표에서 복사한다.

            기준 표는 [번호 | 빈칸 | 글] 순서이며 유형2(2열)는 빈칸 서식을 건너뛴다.
            번호 칸·빈칸 크기는 문서의 것을 유지하고, 글 칸 폭은 글자 수에 비례해 맞춘다(_중제목_칸폭_맞춤).
            """
            for attr in ('borderFillIDRef', 'cellSpacing', 'textWrap', 'textFlow', 'pageBreak', 'repeatHeader'):
                if attr in sample.attrib:
                    value = sample.get(attr)
                    table.set(attr, maps['borderFills'][value] if attr == 'borderFillIDRef' else value)
            for name in ('inMargin', 'outMargin'):
                src, dst = 제목_자식(sample, name), 제목_자식(table, name)
                if src is not None and dst is not None:
                    dst.attrib.update(src.attrib)
            scells = 제목_셀들(sample)
            # 2열 유형은 기준 표의 번호 칸과 마지막(글) 칸을 쓴다(서식 프로필의 2열 예시 표도 같다).
            roles = [scells[0], scells[1], scells[2]] if kind == 1 else [scells[0], scells[-1]]
            for cell, scell in zip(제목_셀들(table), roles):
                cell.set('borderFillIDRef', maps['borderFills'][scell.get('borderFillIDRef')])
                cell.set('hasMargin', scell.get('hasMargin', '0'))
                src, dst = 제목_자식(scell, 'cellMargin'), 제목_자식(cell, 'cellMargin')
                if src is not None and dst is not None:
                    dst.attrib.update(src.attrib)
                sub, ssub = 제목_자식(cell, 'subList'), 제목_자식(scell, 'subList')
                sub.set('vertAlign', ssub.get('vertAlign', 'CENTER'))
                sp = 제목_문단들(scell)[0]
                para_id = maps['paraProperties'].get(sp.get('paraPrIDRef'))
                char_id = maps['charProperties'].get(next(r for r in sp if 제목_xml이름(r) == 'run').get('charPrIDRef'))
                if para_id is None or char_id is None:
                    raise RuntimeError(f'중제목 기준서식 매핑 누락: {sp.get("paraPrIDRef")}')
                # 빈칸 문단도 함께 맞춰 글자 크기(줄 높이)가 서식 그대로 유지되게 한다.
                for p in 제목_문단들(cell):
                    p.set('paraPrIDRef', para_id)
                    p.set('styleIDRef', '0')
                    for r in list(p):
                        if 제목_xml이름(r) == 'linesegarray':
                            p.remove(r)
                        elif 제목_xml이름(r) == 'run':
                            r.set('charPrIDRef', char_id)
            _중제목_칸폭_맞춤(table, 최대폭, header)
        return bind_function(중제목_표서식_복사, _docfit_namespace)
    if _docfit_symbol == '_중제목_글자치수':
        def _중제목_글자치수(header):
            """header의 글자 모양 ID → (크기 HWPUNIT, 한글 장평 %, 한글 자간 %). 중제목 글 칸 폭 어림에 쓴다."""
            치수 = {}
            for cp in (x for x in header.iter() if 제목_xml이름(x) == 'charPr'):
                ratio, spacing = 제목_자식(cp, 'ratio'), 제목_자식(cp, 'spacing')
                try:
                    치수[cp.get('id')] = (int(cp.get('height', '0')) or _중제목_글자폭_pt * 100,
                                       int(ratio.get('hangul', '100')) if ratio is not None else 100,
                                       int(spacing.get('hangul', '0')) if spacing is not None else 0)
                except (TypeError, ValueError):
                    continue
            return 치수
        return bind_function(_중제목_글자치수, _docfit_namespace)
    if _docfit_symbol == '_중제목_문단폭':
        def _중제목_문단폭(p, 치수):
            """문단 글 한 줄의 폭(HWPUNIT)과 가장 큰 글자 크기. 한글·한자는 글자 크기, 영문·숫자는 0.55배, 빈칸은 0.5배에
            장평을 곱하고 글자마다 자간(글자 크기의 %)을 더한다. 글자 모양을 모르면 20pt로 어림한다."""
            폭, 최대크기 = 0.0, 0
            for run in (r for r in p if 제목_xml이름(r) == 'run'):
                크기, 장평, 자간 = 치수.get(run.get('charPrIDRef'), (_중제목_글자폭_pt * 100, 100, 0))
                글 = 제목_문자열(run)
                if 글:
                    최대크기 = max(최대크기, 크기)
                for ch in 글:
                    배율 = 0.5 if ch == ' ' else (0.55 if ch.isascii() else 1.0)
                    폭 += 크기 * 배율 * 장평 / 100 + 크기 * 자간 / 100
            return int(폭), 최대크기
        return bind_function(_중제목_문단폭, _docfit_namespace)
    if _docfit_symbol == '_중제목_칸폭_맞춤':
        def _중제목_칸폭_맞춤(table, 최대폭=None, header=None):
            """중제목 표의 글 칸 폭을 글자 수에 비례해 자동으로 맞춘다(2026-10-04 사용자 요청).

            글이 든 칸(2열·3열 …)은 가장 긴 줄의 글 폭 + 칸 안 좌우 여백 + 여유(글자 반 개)로 넓히거나 줄이고,
            번호 칸과 빈칸은 그대로 둔다. 표 폭은 칸 폭의 합이며, 최대폭(쪽 본문 폭)을 넘으면 글 칸을 줄인다(넘친
            글은 줄바꿈된다). 글 폭은 칸 글자 모양(크기·장평·자간)으로 어림하고, header가 없으면 20pt로 어림한다.
            예전에는 20pt 글이 들어가지 않을 때 넓히기만 해, 짧은 중제목 칸이 길게 비어 있었다.
            """
            cells = 제목_셀들(table)
            글칸 = 중제목_글칸들(table)
            tsize = 제목_자식(table, 'sz')
            sizes = [제목_자식(c, 'cellSz') for c in cells]
            if not 글칸 or tsize is None or any(s is None for s in sizes):
                return
            치수 = _중제목_글자치수(header) if header is not None else {}
            안여백 = 제목_자식(table, 'inMargin')
            widths = [int(s.get('width', '0')) for s in sizes]
            최소 = {}
            for i in 글칸:
                cell = cells[i]
                margin = 제목_자식(cell, 'cellMargin') if cell.get('hasMargin') == '1' else 안여백
                좌우 = sum(int(margin.get(k, '0')) for k in ('left', 'right')) if margin is not None else 0
                줄들 = [_중제목_문단폭(p, 치수) for p in 제목_문단들(cell)]
                글폭 = max([폭 for 폭, _ in 줄들] + [0])
                크기 = max([k for _, k in 줄들] + [_중제목_글자폭_pt * 100])
                widths[i] = 글폭 + 좌우 + max(600, 크기 // 2)
                최소[i] = 2 * 크기 + 좌우          # 글자 두 개는 들어가게
                widths[i] = max(widths[i], 최소[i])
                # 줄 배치를 한/글이 다시 계산하게 한다.
                for p in 제목_문단들(cell):
                    for r in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                        p.remove(r)
            if 최대폭 and sum(widths) > 최대폭:
                넘침 = sum(widths) - 최대폭
                글칸폭 = sum(widths[i] for i in 글칸)
                for i in 글칸:
                    widths[i] = max(최소[i], widths[i] - int(넘침 * widths[i] / 글칸폭) - 1)
            for size, width in zip(sizes, widths):
                size.set('width', str(width))
            tsize.set('width', str(sum(widths)))
        return bind_function(_중제목_칸폭_맞춤, _docfit_namespace)
    if _docfit_symbol == '개요_표인가':
        def 개요_표인가(table):
            cells = 제목_셀들(table)
            if len(cells) != 1 or (int(table.get('rowCnt','0')), int(table.get('colCnt','0'))) != (1,1):
                return False
            text = 제목_문자열(cells[0]).strip()
            return bool(text) and len(text) >= 15 and not re.match(r'^[□ㅁㅇ○※*\-]', text) and not text.startswith('붙임')
        return bind_function(개요_표인가, _docfit_namespace)
    if _docfit_symbol == '제목_xml이름':
        def 제목_xml이름(e):
            return e.tag.rsplit('}', 1)[-1]
        return bind_function(제목_xml이름, _docfit_namespace)
    if _docfit_symbol == '제목_자식':
        def 제목_자식(e, name):
            return next((x for x in e if 제목_xml이름(x) == name), None)
        return bind_function(제목_자식, _docfit_namespace)
    if _docfit_symbol == '제목_셀들':
        def 제목_셀들(table):
            return [c for row in table if 제목_xml이름(row) == 'tr'
                    for c in row if 제목_xml이름(c) == 'tc']
        return bind_function(제목_셀들, _docfit_namespace)
    if _docfit_symbol == '제목_문단들':
        def 제목_문단들(cell):
            sub = 제목_자식(cell, 'subList')
            return [] if sub is None else [p for p in sub if 제목_xml이름(p) == 'p']
        return bind_function(제목_문단들, _docfit_namespace)
    if _docfit_symbol == '제목_문자열':
        def 제목_문자열(e):
            return ''.join(x.text or '' for x in e.iter() if 제목_xml이름(x) == 't')
        return bind_function(제목_문자열, _docfit_namespace)
    if _docfit_symbol == '_한칸_제목글인가':
        def _한칸_제목글인가(문단글들):
            """1×1 표 칸 글이 제목다운지: 1~2문단, 4~160자, 계층 기호·붙임·참고·목차로 시작하지 않고 날짜·담당자 줄이 아니다."""
            ps = [t.strip() for t in 문단글들 if t and t.strip()]
            글 = ' '.join(ps)
            if not 1 <= len(ps) <= 2 or not 6 <= len(re.sub(r'\s+', '', 글)) or len(글) > 160:
                return False
            # 문서 안 표시 상자('서면보고' 등)는 제목이 아니다(실측: 마포구청 회의 자료, 2026-10-10).
            if re.fullmatch(r'[<〈【\[(]?\s*(서면|구두|대면)?\s*보\s*고\s*(사항|안건|자료)?\s*[>〉】\])]?|'
                            r'[<〈【\[(]?\s*(참\s*고|별\s*첨|붙\s*임|요\s*약|개\s*요|목\s*차|안\s*건)\s*\d*\s*[>〉】\])]?', 글):
                return False
            if re.match(r'^\s*[□ㅁㅇ○※*\-•▪<〈]|^\s*(붙임|참고|목\s*차)', 글):
                return False
            return 보고서머리._looks_title(글)
        return bind_function(_한칸_제목글인가, _docfit_namespace)
    if _docfit_symbol == '_기타_제목표인가':
        def _기타_제목표인가(table, header):
            """여러 칸 장식 제목 상자(kordoc 개조식 3×3 등): 4행·4열 이하, 글이 있는 칸 중 제목다운 칸이 하나이고 글자가
            한칸_제목_최소크기_pt 이상, 나머지 글 칸은 보고 주체(날짜·부서·담당자) 글뿐이다(유형 5, 2026-10-10)."""
            try:
                rows, cols = int(table.get('rowCnt', '0')), int(table.get('colCnt', '0'))
            except ValueError:
                return False
            if rows * cols < 2 or rows > 4 or cols > 4:
                return False
            cells = 제목_셀들(table)
            if any(제목_xml이름(x) in ('tbl', 'ole', 'fieldBegin') for c in cells for x in c.iter()):
                return False
            글칸 = [(c, [제목_문자열(p) for p in 제목_문단들(c)]) for c in cells]
            글칸 = [(c, t) for c, t in 글칸 if any(x.strip() for x in t)]
            제목칸 = [c for c, t in 글칸 if _한칸_제목글인가(t)]
            if len(제목칸) != 1:
                return False
            나머지 = [' '.join(t).strip() for c, t in 글칸 if c is not 제목칸[0]]
            if any(not 보고서머리.parse_info(x) for x in 나머지):
                return False
            return 보고서머리._Header(header).char_of(제목칸[0]).get('size_pt', 0) >= 한칸_제목_최소크기_pt
        return bind_function(_기타_제목표인가, _docfit_namespace)
    if _docfit_symbol == '_한칸_제목표인가':
        def _한칸_제목표인가(table, header=None):
            """제목다운 1×1 표. header를 주면 칸 글자 크기가 한칸_제목_최소크기_pt 이상인지도 본다(크기 기준을 만족했는지 돌려준다)."""
            if (table.get('rowCnt'), table.get('colCnt')) != ('1', '1'):
                return False
            cells = 제목_셀들(table)
            if len(cells) != 1 or any(제목_xml이름(x) in ('tbl', 'ole', 'rect', 'fieldBegin') for x in cells[0].iter()):
                return False
            if not _한칸_제목글인가([제목_문자열(p) for p in 제목_문단들(cells[0])]):
                return False
            if header is None:
                return True
            크기 = 보고서머리._Header(header).char_of(cells[0]).get('size_pt', 0)
            return 크기 >= 한칸_제목_최소크기_pt
        return bind_function(_한칸_제목표인가, _docfit_namespace)
    if _docfit_symbol == '제목_유형판별':
        def 제목_유형판별(table, 빈칸허용=False):
            """제목 표 유형. 1·2 = 2×2(제목+날짜·담당자, 부제 없음/있음), 3 = 2행1열(제목+담당자).

            한 제목 칸(1~2문단)과 담당자 칸(2×2는 날짜·담당자 2칸)만 허용한다. 1×1 제목 표는
            제목 서식 대상이 아니다. 빈칸허용이면 날짜·담당자 칸이 모두 빈 표(준말 변환이 만든
            제목 표)도 같은 유형으로 본다.
            """
            cells = 제목_셀들(table)
            if len(cells) not in (2, 3): return None
            rows, cols = int(table.get('rowCnt', '0')), int(table.get('colCnt', '0'))
            # 3행1열(제목 + 담당자 칸 2개, 실측: '마포문화재단 10월 주요 프로그램')도 유형3으로 본다(사용자 요청, 2026-10-09).
            세줄 = len(cells) == 3 and (rows, cols) == (3, 1)
            if (len(cells) == 2 and (rows, cols) != (2, 1)) or (len(cells) == 3 and (rows, cols) != (2, 2) and not 세줄):
                return None
            for i, c in enumerate(cells):
                # 제목 칸의 글 사이 그림(축제 이름 로고 등, 실측: 마포구청 회의 자료)은 제목의 일부로 본다(2026-10-10).
                막는개체 = ('tbl', 'ole', 'rect', 'fieldBegin') if i == 0 else ('tbl', 'pic', 'ole', 'rect', 'fieldBegin')
                if any(제목_xml이름(x) in 막는개체 for x in c.iter()):
                    return None
            ps = [p for p in 제목_문단들(cells[0]) if 제목_문자열(p).strip()]
            if len(ps) not in (1, 2): return None
            if any(re.match(r'^\s*[□ㅁㅇ○※*\-]', 제목_문자열(p)) for p in ps): return None
            정보칸_빔 = 빈칸허용 and not any(제목_문자열(c).strip() for c in cells[1:])
            if len(cells) == 2 or 세줄:
                # 유형3: 윗칸(부제+제목) / 아랫칸(담당자) 2행1열(또는 담당자 칸 2개인 3행1열). 날짜 칸이 없다.
                for 칸 in cells[1:]:
                    if (not 정보칸_빔 and not _제목표_담당자.search(제목_문자열(칸))
                            and not _설정_담당자_글인가(제목_문자열(칸))): return None
                return 3
            span = 제목_자식(cells[0], 'cellSpan')
            if span is None or span.get('colSpan') != '2': return None
            date, owner = map(제목_문자열, cells[1:])
            if not 정보칸_빔 and not re.search(r'[0-9]{2,4}\s*[.년/\-]\s*[0-9]{1,2}', date): return None
            if not 정보칸_빔 and not re.search(r'담당|과장|팀장|☎|전화|부서|작성', owner) and not _설정_담당자_글인가(owner):
                return None
            return 2 if len(ps) == 2 else 1
        return bind_function(제목_유형판별, _docfit_namespace)
    if _docfit_symbol == '제목_대상찾기':
        def 제목_대상찾기(section, header):
            """쪽 첫부분의 제목 표(유형 1·2·3, 1×1 제목 상자는 유형 4)를 판별한다.

            날짜·담당자 칸이 있는 2×2 표, 또는 담당자 칸이 있는 2행1열 표는 구조만으로
            제목으로 확정한다(글자크기·정렬 같은 시각 서식은 필요 없다). 1×1 표는 제목으로 보지 않는다.
            """
            result = []
            ordinal = 0
            # 1×1 제목 상자(유형 4)는 쪽(구역) 첫머리에서만 본다: 앞에 글 문단이 없고(쪽 나누기 뒤 포함) 이 쪽에서 아직
            # 제목을 찾지 않았을 때. 제목 바로 뒤의 1×1 개요 상자를 제목으로 오인하지 않는다(사용자 요청, 2026-10-10).
            쪽첫머리 = True
            직전제목 = False
            for p in section:
                if p.get('pageBreak') == '1':
                    쪽첫머리 = True
                표있음 = False
                for run in p:
                    for table in run:
                        if 제목_xml이름(table) != 'tbl':
                            continue
                        표있음 = True
                        kind = 제목_유형판별(table)
                        # 1×1 제목 상자: 쪽 첫머리이거나, 글자가 제목 크기(16pt 이상)이고 바로 앞 표가 제목이 아닐 때
                        # (제목 바로 뒤 개요 상자 제외). 쪽 나누기 속성 없이 보고서를 이어 붙인 문서도 보고서마다 찾는다.
                        if not kind and _한칸_제목표인가(table) and (
                                쪽첫머리 or (not 직전제목 and _한칸_제목표인가(table, header))):
                            kind = 4
                        if not kind and (쪽첫머리 or not 직전제목) and _기타_제목표인가(table, header):
                            kind = 5
                        찾음 = False
                        if kind:
                            cells = 제목_셀들(table)
                            # 장식 제목 상자(유형 5)는 제목이 첫 칸이 아닐 수 있어 표 전체 글로 본다.
                            title = (제목_문자열(table) if kind == 5 else 제목_문자열(cells[0])).strip()
                            if title and len(title) <= 160 and not title.startswith('붙임'):
                                result.append((ordinal, kind))
                                쪽첫머리 = False
                                찾음 = True
                        직전제목 = 찾음
                        ordinal += 1
                if not 표있음 and 제목_문자열(p).strip():
                    쪽첫머리 = False
                    # 제목 아래 보고 주체 줄(날짜·부서)은 제목과 개요 상자 사이에 올 수 있다.
                    if not 보고서머리.parse_info(제목_문자열(p).strip()):
                        직전제목 = False
            return result
        return bind_function(제목_대상찾기, _docfit_namespace)
    if _docfit_symbol == '서식표_종류판별':
        def 서식표_종류판별(table):
            """서식 요소 분석용 표 종류: 제목(title1~3)·중제목(midtitle1·2)·붙임(attach1·2)·한 칸 상자(box).

            서식 적용과 같은 판별 함수를 쓴다. 제목 표 바로 뒤의 한 칸 상자는 분석 모듈이 개요 표로 본다.
            그 밖의 표는 None(일반 표)이다.
            """
            kind = 제목_유형판별(table)
            if kind:
                title = 제목_문자열(제목_셀들(table)[0]).strip()
                if title and len(title) <= 160 and not title.startswith('붙임'):
                    return f'title{kind}'
            kind = 중제목_유형판별(table)
            if kind:
                return f'midtitle{kind}'
            kind = 붙임_유형판별(table)
            if kind:
                return f'attach{kind}'
            return 'box' if 개요_표인가(table) else None
        return bind_function(서식표_종류판별, _docfit_namespace)
    if _docfit_symbol == '_서식표_예시':
        def _서식표_예시(종류):
            """선택한 서식 프로필이 예시 문서에서 보관한 서식 표 (header, 표). 없으면 None.

            보관한 표도 서식 적용과 같은 판별 함수로 다시 확인해, 칸 구성이 다른 표를 기준으로 쓰지 않는다.
            """
            item = (활성_서식표_프로필 or {}).get(종류)
            if not item:
                return None
            try:
                header = safe_xml_fromstring(item["header_xml"].encode("utf-8"))
                table = safe_xml_fromstring(item["table_xml"].encode("utf-8"))
                판별 = 서식표_종류판별(table)
            except Exception as exc:
                로그(f"서식 프로필의 {서식요소.FORM_LABELS.get(종류, 종류)} 예시를 읽지 못해 기본 서식 표를 씁니다: {exc}")
                return None
            if 판별 != ('box' if 종류 == 'overview' else 종류):
                로그(f"서식 프로필의 {서식요소.FORM_LABELS.get(종류, 종류)} 예시가 칸 구성과 맞지 않아 기본 서식 표를 씁니다.")
                return None
            return header, table
        return bind_function(_서식표_예시, _docfit_namespace)
    if _docfit_symbol == '제목2행1열_원본자료':
        def 제목2행1열_원본자료():
            payload = json.loads(zlib.decompress(base64.b64decode(_제목2행1열_XML)).decode('utf-8'))
            return safe_xml_fromstring(payload['header']), safe_xml_fromstring(payload['section'])
        return bind_function(제목2행1열_원본자료, _docfit_namespace)
    if _docfit_symbol == '제목_원본자료':
        def 제목_원본자료():
            payload = json.loads(zlib.decompress(base64.b64decode(_제목2종_XML)).decode('utf-8'))
            return safe_xml_fromstring(payload['header']), safe_xml_fromstring(payload['section'])
        return bind_function(제목_원본자료, _docfit_namespace)
    if _docfit_symbol == '제목_참조병합':
        def 제목_참조병합(header, source):
            """글꼴·테두리·탭·문자·문단 속성을 새 ID로 추가하여 기존 서식을 보존한다."""
            maps = {}
            def find(root, name): return next(x for x in root.iter() if 제목_xml이름(x) == name)
            for sf in find(source, 'fontfaces'):
                lang = sf.get('lang')
                target = next((x for x in find(header, 'fontfaces') if x.get('lang') == lang), None)
                if target is None:
                    target = XML_자식_추가(find(header, 'fontfaces'), sf, tag=sf.tag, attrib={'lang': lang, 'fontCnt': '0'})
                mapping = {}
                for f in sf:
                    same = next((x for x in target if x.get('face') == f.get('face') and x.get('type') == f.get('type')), None)
                    if same is None:
                        same = copy.deepcopy(f)
                        same.set('id', str(max([int(x.get('id')) for x in target] + [-1]) + 1))
                        target.append(same)
                    mapping[f.get('id')] = same.get('id')
                target.set('fontCnt', str(len(target)))
                maps[lang.lower()] = mapping
            attrs = {'borderFillIDRef': 'borderFills', 'tabPrIDRef': 'tabProperties'}
            for group in ('borderFills', 'tabProperties', 'charProperties', 'paraProperties'):
                src, dst = find(source, group), find(header, group)
                maps[group] = {}
                for item in src:
                    # 제목뿐 아니라 제목과 한 쌍인 개요표도 이 병합 함수를 사용한다.
                    # 개요 기준서식은 paraPrIDRef=27을 사용하므로 20~23만 복사하면
                    # 제목 유형 3 판별 후 개요 적용 단계에서 KeyError('27')가 발생한다.
                    # 기준 XML이 참조하는 모든 문단속성을 새 ID로 병합해 제목/개요/붙임
                    # 어느 서식에서도 paraPrIDRef 매핑이 누락되지 않게 한다.
                    clone = copy.deepcopy(item)
                    new_id = str(max([int(x.get('id')) for x in dst] + [-1]) + 1)
                    maps[group][item.get('id')] = new_id
                    clone.set('id', new_id)
                    for x in clone.iter():
                        for attr, category in attrs.items():
                            if attr in x.attrib and category in maps:
                                x.set(attr, maps[category].get(x.get(attr), x.get(attr)))
                        if 제목_xml이름(x) == 'fontRef':
                            for lang, old in list(x.attrib.items()): x.set(lang, maps[lang][old])
                    dst.append(clone)
                dst.set('itemCnt', str(len(dst)))
            return maps
        return bind_function(제목_참조병합, _docfit_namespace)
    if _docfit_symbol == '날짜칸인가':
        def 날짜칸인가(글):
            """칸 글이 주로 날짜인지: 날짜가 있고, 날짜·요일·시간을 빼면 남는 글이 짧다(12자 이하)."""
            글 = (글 or '').strip()
            if not 글 or len(글) > 40:
                return False
            m = _제목_날짜.search(글)
            if not m:
                return False
            나머지 = 글[:m.start()] + 글[m.end():]
            나머지 = re.sub(r'\(\s*[월화수목금토일]\s*\)|[월화수목금토일]요일|\d{1,2}\s*:\s*\d{2}|[.\s~\-]', '', 나머지)
            return len(나머지) <= 12
        return bind_function(날짜칸인가, _docfit_namespace)
    if _docfit_symbol == '제목_날짜칸_한줄':
        def 제목_날짜칸_한줄(table):
            """제목 표에서 날짜가 든 짧은 칸(첫 칸 제외)을 '한 줄로 입력'(lineWrap=SQUEEZE)으로 둔다. 바꾼 칸 수.

            날짜 칸 폭이 좁으면 "’26. 10. 10.(토)"가 두 줄로 나뉘었다(2026-10-10 실측). 한 줄로 입력은 칸 폭에 맞춰
            글자 폭을 줄여 한 줄을 지킨다.
            """
            count = 0
            for cell in 제목_셀들(table)[1:]:
                글 = 제목_문자열(cell).strip()
                if not 글 or len(글) > 40 or not _제목_날짜.search(글):
                    continue
                sub = 제목_자식(cell, 'subList')
                if sub is not None and sub.get('lineWrap') != 'SQUEEZE':
                    sub.set('lineWrap', 'SQUEEZE')
                    count += 1
            return count
        return bind_function(제목_날짜칸_한줄, _docfit_namespace)
    if _docfit_symbol == '제목_표서식_복사':
        def 제목_표서식_복사(table, sample, maps, 상자=False):
            """제목 내용은 그대로 두고 원본 표·셀·문단·문자 서식만 복사한다.

            문단은 끝에서부터 맞춘다(제목 표: 부제가 없는 문서도 제목 문단 서식을 받게). 상자=True(한 칸 상자)는 문단 수가
            같으면 하나씩, 다르면 예시의 본문 문단(글이 가장 많은 문단) 서식을 모든 문단에 입힌다. 끝에서 맞추면 한 문단
            상자가 예시 상자 끝의 안내 문단(파란 11pt 등) 서식을 받았다(2026-10-04 범정부오피스 서식 시험).
            """
            for attr in ('borderFillIDRef', 'cellSpacing', 'textWrap', 'textFlow', 'pageBreak', 'repeatHeader'):
                if attr in sample.attrib:
                    value = sample.get(attr)
                    table.set(attr, maps['borderFills'][value] if attr == 'borderFillIDRef' else value)
            for name in ('sz', 'inMargin', 'outMargin'):
                src, dst = 제목_자식(sample, name), 제목_자식(table, name)
                if src is not None and dst is not None: dst.attrib.update(src.attrib)
            표본칸 = 제목_셀들(sample)
            대상칸 = 제목_셀들(table)
            # 예시보다 칸이 많은 제목 표(3행1열: 담당자 칸 2개)는 남는 칸에 예시의 마지막(담당자) 칸 서식을 입힌다.
            if 표본칸 and len(대상칸) > len(표본칸) and not 상자:
                표본칸 = 표본칸 + [표본칸[-1]] * (len(대상칸) - len(표본칸))
            for cell, scell in zip(대상칸, 표본칸):
                cell.set('borderFillIDRef', maps['borderFills'][scell.get('borderFillIDRef')])
                cell.set('hasMargin', scell.get('hasMargin', '0'))
                for name in ('cellSz', 'cellMargin'):
                    src, dst = 제목_자식(scell, name), 제목_자식(cell, name)
                    if src is not None and dst is not None:
                        원래높이 = dst.get('height') if name == 'cellSz' else None
                        dst.attrib.update(src.attrib)
                        # 칸 높이는 원본과 예시 중 낮은 값을 둔다(최소 높이라 글이 더 필요하면 한/글이 늘린다). 예시의 높은 칸을
                        # 그대로 받으면 제목 표가 3mm 커져 큰 표가 다음 쪽으로 밀리고 원본 쪽 구성이 깨졌다(2026-10-09 실측).
                        try:
                            if 원래높이 is not None and 0 < int(원래높이) < int(dst.get('height', '0')):
                                dst.set('height', 원래높이)
                        except ValueError:
                            pass
                sub, ssub = 제목_자식(cell, 'subList'), 제목_자식(scell, 'subList')
                sub.set('vertAlign', ssub.get('vertAlign', 'CENTER'))
                ps = [p for p in 제목_문단들(cell) if 제목_문자열(p).strip()]
                sps = [p for p in 제목_문단들(scell) if 제목_문자열(p).strip()]
                본문 = max(sps, key=lambda q: len(제목_문자열(q).strip())) if 상자 and sps and len(sps) != len(ps) else None
                for i, p in enumerate(ps):
                    sp = 본문 if 본문 is not None else sps[min(i + max(0, len(sps) - len(ps)), len(sps)-1)]
                    source_para_id = sp.get('paraPrIDRef')
                    mapped_para_id = maps['paraProperties'].get(source_para_id)
                    if mapped_para_id is None:
                        raise RuntimeError(f'기준서식 문단속성 매핑 누락: paraPrIDRef={source_para_id}')
                    p.set('paraPrIDRef', mapped_para_id)
                    p.set('styleIDRef', '0')
                    sruns = [r for r in sp if 제목_xml이름(r) == 'run']
                    main = max(sruns, key=lambda r: len(제목_문자열(r))).get('charPrIDRef')
                    quote = next((r.get('charPrIDRef') for r in sruns if 제목_문자열(r).strip() in ('‘', '’', "'")), main)
                    for r in list(p):
                        if 제목_xml이름(r) == 'linesegarray': p.remove(r)
                        elif 제목_xml이름(r) == 'run':
                            r.set('charPrIDRef', maps['charProperties'][main])
                            # 따옴표 글꼴(돋움)을 동일 런에 섞인 텍스트에도 보존한다.
                            if all(제목_xml이름(t) == 't' and not len(t) for t in r):
                                text = 제목_문자열(r)
                                index = list(p).index(r); p.remove(r)
                                for piece in re.split(r"([‘’'])", text):
                                    if not piece: continue
                                    nr = XML_요소_생성(r, tag=r.tag, attrib=dict(r.attrib))
                                    nr.set('charPrIDRef', maps['charProperties'][quote if piece in ('‘', '’', "'") else main])
                                    XML_자식_추가(nr, r, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}t').text = piece
                                    p.insert(index, nr); index += 1
        return bind_function(제목_표서식_복사, _docfit_namespace)
    if _docfit_symbol == '제목_문단_가운데정렬':
        def 제목_문단_가운데정렬(header, table):
            """제목 셀의 모든 실제 제목 문단을 가운데 정렬로 강제한다.

            제목 기준서식의 다른 속성은 그대로 유지하고 paraPr의 align.horizontal만
            CENTER로 바꾼다. 제목 전용으로 새로 병합된 paraPr를 사용하므로 본문/개요에는
            영향을 주지 않는다.
            """
            para_group = next((x for x in header.iter() if 제목_xml이름(x) == 'paraProperties'), None)
            if para_group is None:
                return 0
            by_id = {x.get('id'): x for x in para_group if 제목_xml이름(x) == 'paraPr'}
            cells = 제목_셀들(table)
            if not cells:
                return 0
            count = 0
            for p in 제목_문단들(cells[0]):
                if not 제목_문자열(p).strip():
                    continue
                pp = by_id.get(p.get('paraPrIDRef'))
                if pp is None:
                    continue
                align = next((x for x in pp if 제목_xml이름(x) == 'align'), None)
                if align is not None:
                    align.set('horizontal', 'CENTER')
                    count += 1
            return count
        return bind_function(제목_문단_가운데정렬, _docfit_namespace)
    if _docfit_symbol == '제목_괄호부연_축소':
        def 제목_괄호부연_축소(header, table):
            """제목 셀 안의 '(...)' 부연설명만 설정값만큼 글자 크기를 줄인다.

            일반 본문의 '괄호 안 부연설명 글자 크기 축소'와 동일하게 해당 기능이
            OFF이면 제목에서도 적용하지 않는다. 텍스트 자체는 변경하지 않는다.
            """
            if not globals().get('괄호_축소_사용', True):
                return 0
            reduce_pt = float(globals().get('괄호_축소_pt', 2) or 2)
            char_group = next((x for x in header.iter() if 제목_xml이름(x) == 'charProperties'), None)
            if char_group is None:
                return 0
            by_id = {x.get('id'): x for x in char_group if 제목_xml이름(x) == 'charPr'}
            cache = {}

            def reduced_char_id(old_id):
                key = (old_id, reduce_pt)
                if key in cache:
                    return cache[key]
                src = by_id.get(old_id)
                if src is None:
                    return old_id
                clone = copy.deepcopy(src)
                try:
                    old_h = int(clone.get('height', '1000'))
                    new_h = max(100, old_h - int(round(reduce_pt * 100)))
                    clone.set('height', str(new_h))
                except Exception:
                    return old_id
                new_id = str(max([int(x.get('id')) for x in char_group if (x.get('id') or '').isdigit()] + [-1]) + 1)
                clone.set('id', new_id)
                char_group.append(clone)
                char_group.set('itemCnt', str(len(char_group)))
                by_id[new_id] = clone
                cache[key] = new_id
                return new_id

            cells = 제목_셀들(table)
            if not cells:
                return 0
            applied = 0
            # 제목은 기준서식 적용 후 단순 텍스트 run으로 정규화되어 있으므로 run 단위에서
            # 괄호 구간을 안전하게 분리한다. 중첩괄호는 가장 안쪽부터 일반 괄호로 처리한다.
            pattern = re.compile(r'(\([^()]+\))')
            for p in 제목_문단들(cells[0]):
                for run in list(p):
                    if 제목_xml이름(run) != 'run':
                        continue
                    # 컨트롤이 섞인 run은 건드리지 않는다.
                    ts = [x for x in run if 제목_xml이름(x) == 't']
                    if len(ts) != 1 or len(run) != 1:
                        continue
                    text = ts[0].text or ''
                    if '(' not in text or ')' not in text:
                        continue
                    pieces = pattern.split(text)
                    if len(pieces) == 1:
                        continue
                    idx = list(p).index(run)
                    p.remove(run)
                    for piece in pieces:
                        if not piece:
                            continue
                        nr = XML_요소_생성(run, tag=run.tag, attrib=dict(run.attrib))
                        if pattern.fullmatch(piece):
                            nr.set('charPrIDRef', reduced_char_id(run.get('charPrIDRef')))
                            applied += 1
                        nt = XML_자식_추가(nr, ts[0], tag=ts[0].tag, attrib=dict(ts[0].attrib))
                        nt.text = piece
                        p.insert(idx, nr)
                        idx += 1
            return applied
        return bind_function(제목_괄호부연_축소, _docfit_namespace)
    if _docfit_symbol == '제목_hwpx_처리':
        def 제목_hwpx_처리(source, target=None, selections=None):
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            # 기존 네임스페이스 접두사를 유지한다.
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items()
                        if re.fullmatch(r'Contents/section\d+\.xml', n)}
            if selections is None:
                return {n: 제목_대상찾기(root, header) for n, root in sections.items()}
            if not any(kind in (1, 2, 3, 4, 5) for items in selections.values() for _, kind in items):
                if target is not None: shutil.copyfile(source, target)
                return 0
            기준 = {}

            def 기준표(종류):
                """(기준 표, ID 매핑, 서식 프로필 예시 여부). 필요한 기준만 한 번씩 header에 병합한다.

                선택한 서식 프로필에 그 종류의 예시 표가 있으면 그 표를, 없으면 내장 기준 표를 쓴다.
                유형3(2행1열)과 개요는 내장 기준 자료가 따로 있다.
                """
                if 종류 not in 기준:
                    예시 = _서식표_예시(종류)
                    if 예시 is not None:
                        기준[종류] = (예시[1], 제목_참조병합(header, 예시[0]), True)
                    elif 종류 in ('title1', 'title2'):
                        if '내장제목' not in 기준:
                            sh, ss = 제목_원본자료()
                            기준['내장제목'] = ([x for x in ss.iter() if 제목_xml이름(x) == 'tbl'], 제목_참조병합(header, sh))
                        samples, maps = 기준['내장제목']
                        기준[종류] = (samples[int(종류[-1]) - 1], maps, False)
                    elif 종류 == 'title3':
                        h5, s5 = 제목2행1열_원본자료()
                        기준[종류] = (next(x for x in s5.iter() if 제목_xml이름(x) == 'tbl'), 제목_참조병합(header, h5), False)
                    else:
                        # 제목은 개요와 한 쌍이므로, 제목 바로 다음의 1칸 개요표에도 기준 개요 서식을 적용한다.
                        eh, es = 개요붙임_원본자료()
                        기준[종류] = ([x for x in es.iter() if 제목_xml이름(x) == 'tbl'][0], 제목_참조병합(header, eh), False)
                return 기준[종류]

            count = 0
            지운빈줄 = 뒤빈줄 = 0
            for name, items in selections.items():
                root = sections[name]
                tables = [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']
                표문단 = {id(t): p for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl'}
                본문폭 = _구역_본문폭(root, None)   # 쪽 정보가 없으면 폭을 바꾸지 않는다
                for index, kind in items:
                    table = tables[index]
                    현재종류 = (제목_유형판별(table) if kind not in (4, 5) else
                             4 if kind == 4 and _한칸_제목표인가(table) else 5 if kind == 5 and _기타_제목표인가(table, header) else None)
                    if 현재종류 != kind:
                        raise RuntimeError('처리 중 제목 구조가 변경되어 제목 서식적용을 중단했습니다.')
                    before = 제목_문자열(table)
                    if kind in (4, 5):
                        # 1×1·장식 제목 상자: 서식은 보고서 머리 서식 복사(예시 프로필)가 맡고, 여기서는 가로 크기만 맞춘다.
                        _서식표_가로맞춤(table, 본문폭, 비례=True)
                        if 제목_문자열(table) != before: raise RuntimeError('제목 텍스트 보존 검사 실패')
                        count += 1
                        continue
                    sample, maps, 예시사용 = 기준표(f'title{kind}')
                    제목_표서식_복사(table, sample, maps)
                    # 제목 표 날짜 칸(A2, "’26. 10. 10.(토)" 등)은 칸 너비와 관계없이 한 줄로 둔다(사용자 요청, 2026-10-10).
                    제목_날짜칸_한줄(table)
                    # 제목 표 가로 크기는 쪽 좌우 여백 사이 최대 폭으로 한다(기준 표 폭과 문서 여백이 달라도 맞춤).
                    # 서식 프로필의 예시 표를 쓰면 열 비율은 예시대로 둔다.
                    _서식표_가로맞춤(table, 본문폭, 비례=예시사용)
                    # 제목 텍스트는 유형과 관계없이 가운데 정렬을 기본값으로 한다.
                    # 서식 프로필의 예시 표를 쓰면 그 표의 정렬을 따른다.
                    if not 예시사용:
                        제목_문단_가운데정렬(header, table)
                    # 일반 보고서 서식의 괄호 부연설명 축소 설정을 제목에도 동일 적용한다.
                    제목_괄호부연_축소(header, table)
                    # 부제(첫 문단)는 15pt로 둔다(내장 기준 표일 때). 서식 프로필 예시 표는 그 표의 크기를 따른다.
                    if not 예시사용:
                        제목_부제_크기(header, table)
                    if 제목_문자열(table) != before: raise RuntimeError('제목 텍스트 보존 검사 실패')
                    끝문단 = 표문단[id(table)]
                    # 제목 다음 표가 개요 구조이면 내용은 보존하고 개요 기준서식 적용
                    if index + 1 < len(tables) and 개요_표인가(tables[index + 1]):
                        obefore = 제목_문자열(tables[index + 1])
                        overview_sample, emaps, 개요예시 = 기준표('overview')
                        제목_표서식_복사(tables[index + 1], overview_sample, emaps)
                        # 제목_표서식_복사는 문단의 모든 run을 대표 charPrIDRef 하나로
                        # 정규화한다. 개요(요지) 표 문단이 본문 처리 단계에서 이미
                        # 괄호 부연설명 2pt 축소를 받았더라도 이 정규화로 지워지므로,
                        # 제목 표와 동일하게 여기서 다시 적용해 유지시킨다.
                        제목_괄호부연_축소(header, tables[index + 1])
                        _서식표_가로맞춤(tables[index + 1], 본문폭, 비례=개요예시)
                        if 제목_문자열(tables[index + 1]) != obefore: raise RuntimeError('개요 텍스트 보존 검사 실패')
                        # 제목 표와 개요 표 사이에는 빈 줄을 두지 않는다.
                        지운빈줄 += _문단사이_빈줄_삭제(root, 표문단[id(table)], 표문단[id(tables[index + 1])])
                        끝문단 = 표문단[id(tables[index + 1])]
                    # 제목·개요 표와 첫 항목기호 문장 사이도 빈 줄 없이 문단 위 여백으로만 띄운다.
                    뒤빈줄 += _서식표_뒤_빈줄_삭제(root, 끝문단)
                    count += 1
                contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            if 지운빈줄:
                로그(f"제목 표와 개요 표 사이 빈 줄 {지운빈줄}개 삭제")
            if 뒤빈줄:
                로그(f"제목·개요 표와 첫 항목기호 문장 사이 빈 줄 {뒤빈줄}개 삭제")
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
                for name, data in contents.items():
                    z.writestr(name, data, compress_type=zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED)
            return count
        return bind_function(제목_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '_제목_임시hwpx_저장':
        def _제목_임시hwpx_저장(경로):
            """
            현재 문서를 HWPX 스냅샷으로 저장한다.

            HwpObject.SaveAs()는 저장된 파일을 현재 편집 문서로 전환해 파일 핸들을
            계속 잡을 수 있다. TemporaryDirectory 안에 직접 SaveAs 하면 블록 종료 시
            Windows에서 WinError 32가 발생하므로, 임시 파일을 명시적으로 관리한다.
            """
            경로 = Path(경로)
            경로.parent.mkdir(parents=True, exist_ok=True)
            if hwp.SaveAs(str(경로), 'HWPX', '') is False:
                raise RuntimeError('제목 분석/적용용 HWPX 저장 실패')
            # SaveAs 직후 파일 쓰기가 완전히 끝날 때까지 짧게 확인한다.
            for _ in range(20):
                try:
                    with open_hwpx_safely(경로) as z:
                        if 'Contents/header.xml' in z.namelist():
                            return 경로
                except (PermissionError, OSError, zipfile.BadZipFile):
                    pass
                time.sleep(0.05)
            raise RuntimeError('제목 분석/적용용 HWPX 저장 완료를 확인하지 못했습니다.')
        return bind_function(_제목_임시hwpx_저장, _docfit_namespace)
    if _docfit_symbol == '이전_작업_임시폴더_정리':
        def 이전_작업_임시폴더_정리(최소_경과초=600):
            """이전 실행에서 한글이 파일을 잡고 있어 지우지 못한 작업용 임시 폴더를
            정리한다. 지금 실행 중인 다른 작업의 폴더를 건드리지 않도록 일정 시간
            지난 폴더만 지우며, 아직 사용 중인 폴더는 조용히 건너뛴다."""
            기준 = time.time() - 최소_경과초
            정리수 = 0
            try:
                후보들 = list(Path(tempfile.gettempdir()).iterdir())
            except OSError:
                return 0
            for 폴더 in 후보들:
                if not 폴더.name.startswith(_작업_임시폴더_접두어):
                    continue
                try:
                    if not 폴더.is_dir() or 폴더.stat().st_mtime > 기준:
                        continue
                    shutil.rmtree(폴더)
                    정리수 += 1
                except OSError:
                    continue
            return 정리수
        return bind_function(이전_작업_임시폴더_정리, _docfit_namespace)
    if _docfit_symbol == '_제목_임시폴더_정리':
        def _제목_임시폴더_정리(폴더):
            """한글이 잠시 파일 핸들을 유지해도 본 작업을 실패시키지 않도록 지연 정리한다."""
            폴더 = Path(폴더)
            for 시도 in range(20):
                try:
                    shutil.rmtree(폴더)
                    return
                except FileNotFoundError:
                    return
                except (PermissionError, OSError) as e:
                    if 시도 == 19:
                        # 임시파일 정리 실패는 문서 편집 실패가 아니다. 다음 실행/Windows가 정리한다.
                        진단로그(f'제목 임시파일 정리 보류: {폴더} ({e})')
                        return
                    time.sleep(0.1)
        return bind_function(_제목_임시폴더_정리, _docfit_namespace)
    if _docfit_symbol == '서식구조_조사':
        def 서식구조_조사(원본문서경로, 처리함수, 이름):
            """HWPX는 직접 읽고, HWP만 현재 한글에서 변환한다. 추가 COM 실행 금지."""
            if 원본문서경로 is not None and Path(원본문서경로).suffix.lower() == '.hwpx':
                로그(f'{이름} 구조 직접 분석 시작')
                result = 처리함수(Path(원본문서경로))
                로그(f'{이름} 구조 직접 분석 완료')
                return result
            folder = Path(tempfile.mkdtemp(prefix='hwp_structure_scan_'))
            try:
                로그(f'{이름} 분석: 현재 한글에서 HWPX 변환 시작')
                source = _제목_임시hwpx_저장(folder / 'scan.hwpx')
                result = 처리함수(source)
                로그(f'{이름} 구조 분석 완료')
                return result
            finally:
                _제목_임시폴더_정리(folder)
        return bind_function(서식구조_조사, _docfit_namespace)
    if _docfit_symbol == '제목4종_현재문서_조사':
        def 제목4종_현재문서_조사(원본문서경로=None):
            return 서식구조_조사(원본문서경로, 제목_hwpx_처리, '제목')
        return bind_function(제목4종_현재문서_조사, _docfit_namespace)
    if _docfit_symbol == '제목4종_현재문서_적용':
        def 제목4종_현재문서_적용(selections):
            if not any(items for items in selections.values()):
                로그('제목 서식 대상 없음: 제목표가 검출되지 않아 제목서식을 적용하지 않습니다.')
                return
            folder = Path(tempfile.mkdtemp(prefix='hwp_title_apply_'))
            try:
                source, target = folder / 'before.hwpx', folder / 'after.hwpx'
                _제목_임시hwpx_저장(source)
                count = 제목_hwpx_처리(source, target, selections)
                if 한글_문서_열기(hwp, target, 'HWPX', 'forceopen:true') is False:
                    raise RuntimeError('제목 적용 결과를 열지 못했습니다.')
                로그(f'제목 서식 자동 적용: {count}개 / 유형 ' + ', '.join(str(k) for v in selections.values() for _, k in v))
            finally:
                # after.hwpx가 현재 문서로 열려 있을 수 있으므로 삭제 실패를 작업 실패로 전파하지 않는다.
                _제목_임시폴더_정리(folder)
        return bind_function(제목4종_현재문서_적용, _docfit_namespace)
    if _docfit_symbol == '붙임_hwpx_처리':
        def 붙임_hwpx_처리(source, target=None, selections=None):
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
            if selections is None:
                return {n: 붙임_대상찾기(root) for n, root in sections.items()}
            if not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            기준 = {}

            def 기준표(kind):
                """붙임 유형의 (기준 표, ID 매핑). 서식 프로필의 예시 표가 있으면 그 표를 쓴다."""
                if kind not in 기준:
                    예시 = _서식표_예시(f'attach{kind}')
                    if 예시 is not None:
                        기준[kind] = (예시[1], 제목_참조병합(header, 예시[0]))
                    else:
                        if '내장' not in 기준:
                            sh, ss = 개요붙임_원본자료()
                            기준['내장'] = ([x for x in ss.iter() if 제목_xml이름(x) == 'tbl'][1:3], 제목_참조병합(header, sh))
                        samples, maps = 기준['내장']
                        기준[kind] = (samples[kind - 1], maps)
                return 기준[kind]

            count = 0
            for name, items in selections.items():
                root = sections[name]
                tables = [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']
                for index, kind in items:
                    table = tables[index]
                    if 붙임_유형판별(table) != kind:
                        raise RuntimeError('처리 중 붙임 구조가 변경되어 붙임 서식적용을 중단했습니다.')
                    before = 제목_문자열(table)
                    제목_표서식_복사(table, *기준표(kind))
                    if 제목_문자열(table) != before: raise RuntimeError('붙임 텍스트 보존 검사 실패')
                    count += 1
                contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
                for name, data in contents.items():
                    z.writestr(name, data, compress_type=zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED)
            return count
        return bind_function(붙임_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '중제목_hwpx_처리':
        def 중제목_hwpx_처리(source, target=None, selections=None):
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
            if selections is None:
                found = {n: 중제목_대상찾기(root) for n, root in sections.items()}
                scheme = globals().get('활성_항목기호_체계')
                for name, root in sections.items():
                    for index, p in enumerate(root):
                        if 제목_xml이름(p) != 'p':
                            continue
                        texts = _문단_일반글(p)
                        글 = ''.join(t.text or '' for t in texts) if texts else ''
                        heading = roman_heading_match(글) if texts else None
                        # 항목기호 체계가 Ⅰ.를 □ 단계로 정한 문서(공식 □ 없음)는 중제목 표로 바꾸지 않는다.
                        if heading and scheme and scheme.canonical(글):
                            continue
                        if heading:
                            found[name].append((index, ('text', *heading)))
                return found
            if not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            기준 = {}

            def 기준표(kind):
                """중제목 유형의 (기준 표, ID 매핑).

                서식 프로필의 같은 유형 예시를 먼저 쓴다. 2열 유형은 3열 예시(번호·빈칸·글)의 번호·글 칸도
                쓸 수 있지만, 3열 유형은 빈칸 서식이 필요해 2열 예시로 대신하지 않는다.
                """
                if kind not in 기준:
                    예시 = _서식표_예시(f'midtitle{kind}') or (_서식표_예시('midtitle1') if kind == 2 else None)
                    if 예시 is not None:
                        기준[kind] = (예시[1], 제목_참조병합(header, 예시[0]))
                    else:
                        if '내장' not in 기준:
                            sh, ss = 중제목_원본자료()
                            maps = 제목_참조병합(header, sh)
                            # 번호 굵게 끄기는 내장 기준 표의 번호 글자 모양(8번)에만 적용한다.
                            _중제목_번호굵게_적용(header, maps)
                            기준['내장'] = (next(x for x in ss.iter() if 제목_xml이름(x) == 'tbl'), maps)
                        기준[kind] = 기준['내장']
                return 기준[kind]

            count = 0
            new_cache, ids = {}, _문서_표번호(sections)
            for name, items in selections.items():
                root = sections[name]
                tables = [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']
                for index, kind in items:
                    if isinstance(kind, tuple) and kind[:1] == ('text',):
                        p = root[index]
                        texts = _문단_일반글(p)
                        current = roman_heading_match(''.join(t.text or '' for t in texts)) if texts else None
                        if current is None or ('text', *current) != kind:
                            raise RuntimeError('처리 중 로마자 중제목이 변경되어 서식적용을 중단했습니다.')
                        numeral, title = current
                        table = 서식표_생성(header, 'midtitle', title, new_cache, numeral, _구역_본문폭(root))
                        _서식표_글_확인('midtitle', table, title, numeral)
                        _서식표_번호_부여(table, ids)
                        base_char = next((r.get('charPrIDRef', '0') for r in p if 제목_xml이름(r) == 'run'), '0')
                        for run in [r for r in p if 제목_xml이름(r) == 'run']:
                            for t in [t for t in run if 제목_xml이름(t) == 't']:
                                run.remove(t)
                            if not len(run):
                                p.remove(run)
                        for seg in [c for c in p if 제목_xml이름(c) == 'linesegarray']:
                            p.remove(seg)
                        holder = XML_자식_추가(p, p, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}run',
                                            attrib={'charPrIDRef': base_char})
                        holder.append(table)
                        XML_자식_추가(holder, p, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}t')
                        p.set('paraPrIDRef', '0')
                        p.set('styleIDRef', '0')
                        count += 1
                        continue
                    table = tables[index]
                    현재 = 중제목_유형판별(table) or ('fit' if 중제목_글칸들(table) else None)
                    if 현재 != kind:
                        raise RuntimeError('처리 중 중제목 구조가 변경되어 중제목 서식적용을 중단했습니다.')
                    before = 제목_문자열(table)
                    if kind == 'fit':
                        # 번호·글·빈칸 등 서식 기준 표가 없는 모양은 서식은 두고 글 칸 폭만 글자 수에 맞춘다.
                        _중제목_칸폭_맞춤(table, _구역_본문폭(root), header)
                    else:
                        sample, maps = 기준표(kind)
                        중제목_표서식_복사(table, sample, maps, kind, _구역_본문폭(root), header)
                    if 제목_문자열(table) != before: raise RuntimeError('중제목 텍스트 보존 검사 실패')
                    count += 1
                contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
                for name, data in contents.items():
                    z.writestr(name, data, compress_type=zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED)
            return count
        return bind_function(중제목_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '제목_부제_크기_해석':
        def 제목_부제_크기_해석(value, 기본값=15):
            """설정의 제목 부제 크기(pt) 글을 숫자로 바꾼다. 숫자가 아니면 기본값, 5~40pt 밖이면 범위 끝 값."""
            try:
                크기 = float(str(value).strip().replace(',', '.'))
            except (TypeError, ValueError):
                return 기본값
            if 크기 != 크기:   # NaN
                return 기본값
            크기 = min(40.0, max(5.0, 크기))
            return int(크기) if 크기.is_integer() else 크기
        return bind_function(제목_부제_크기_해석, _docfit_namespace)
    if _docfit_symbol == '제목_부제_크기_반영':
        def 제목_부제_크기_반영(value):
            """설정값을 제목 부제 크기 전역값에 반영하고 반영한 값을 돌려준다."""
            global 제목_부제_크기_pt
            제목_부제_크기_pt = 제목_부제_크기_해석(value)
            return 제목_부제_크기_pt
        return bind_function(제목_부제_크기_반영, _docfit_namespace)
    if _docfit_symbol == '제목_담당자_글_반영':
        def 제목_담당자_글_반영(value):
            """설정값(한 줄, 앞뒤 빈칸 제거, 200자까지)을 제목 담당자 칸 글 전역값에 반영하고 반영한 값을 돌려준다."""
            global 제목_담당자_글
            제목_담당자_글 = ' '.join(str(value or '').split('\n')).replace('\r', ' ').strip()[:200]
            return 제목_담당자_글
        return bind_function(제목_담당자_글_반영, _docfit_namespace)
    if _docfit_symbol == '_설정_담당자_글인가':
        def _설정_담당자_글인가(text):
            """칸 글이 설정한 제목 담당자 칸 글과 같은지(담당·과장 같은 낱말이 없는 글도 담당자 칸으로 본다)."""
            return bool(제목_담당자_글) and (text or '').strip() == 제목_담당자_글
        return bind_function(_설정_담당자_글인가, _docfit_namespace)
    if _docfit_symbol == '_서식표_기준':
        def _서식표_기준(header, kind, cache):
            """서식 표 종류의 (기준 표, ID 매핑)을 문서 header에 한 번만 병합해 돌려준다.

            선택한 서식 프로필에 같은 종류의 예시 표가 있으면 그 표를 쓴다(cache['예시사용']에 종류를 남긴다).
            2행1열 제목과 부제 있는 제목 서식1은 부제·제목 두 문단이 있는 예시만 쓴다(부제를 넣을 문단이 있어야 한다).
            """
            예시키 = '예시:' + kind
            if 예시키 not in cache:
                예시 = _서식표_예시(_서식표_예시종류[kind])
                if 예시 is not None and kind in ('title2', 'title1부제') and len(
                        [p for p in 제목_문단들(제목_셀들(예시[1])[0]) if 제목_문자열(p).strip()]) != 2:
                    예시 = None
                cache[예시키] = (예시[1], 제목_참조병합(header, 예시[0])) if 예시 is not None else None
            if cache[예시키] is not None:
                cache.setdefault('예시사용', set()).add(kind)
                return cache[예시키]
            group = _서식표_묶음[kind]
            if group not in cache:
                source_header, source = {'제목': 제목_원본자료, '제목2행1열': 제목2행1열_원본자료,
                                         '개요붙임': 개요붙임_원본자료, '중제목': 중제목_원본자료}[group]()
                maps = 제목_참조병합(header, source_header)
                if group == '중제목':
                    _중제목_번호굵게_적용(header, maps)
                cache[group] = ([x for x in source.iter() if 제목_xml이름(x) == 'tbl'], maps)
            tables, maps = cache[group]
            # 제목 원본자료: 0 = 부제 없는 2×2 제목, 1 = 부제·제목 두 문단의 2×2 제목
            index = {'overview': 0, 'attach1': 1, 'attach2': 2, 'title1부제': 1}.get(kind, 0)
            return tables[index], maps
        return bind_function(_서식표_기준, _docfit_namespace)
    if _docfit_symbol == '제목_부제_크기':
        def 제목_부제_크기(header, table, 크기_pt=None):
            """제목 표 A1 칸에 글 문단이 둘 이상이면 첫 문단(부제)의 글자 크기를 정한 크기로 맞춘다. 바꾼 글 묶음 수.

            제목 글의 첫 쉼표 앞 글이 부제다(2026-10-03 사용자 규칙: 쉼표 앞 글자는 기본 15pt). 부제 안 괄호 부연설명도
            같은 크기로 둔다. 글자 모양은 복제해서 바꾸므로 다른 곳의 글자 모양은 그대로다.
            """
            cells = 제목_셀들(table)
            ps = [p for p in 제목_문단들(cells[0]) if 제목_문자열(p).strip()] if cells else []
            char_group = next((x for x in header.iter() if 제목_xml이름(x) == 'charProperties'), None)
            if len(ps) < 2 or char_group is None:
                return 0
            높이 = str(int(round(float(크기_pt or 제목_부제_크기_pt) * 100)))
            by_id = {x.get('id'): x for x in char_group if 제목_xml이름(x) == 'charPr'}
            복제 = {}
            count = 0
            for run in (r for r in ps[0] if 제목_xml이름(r) == 'run'):
                old = run.get('charPrIDRef')
                src = by_id.get(old)
                if src is None or src.get('height') == 높이:
                    continue
                if old not in 복제:
                    clone = copy.deepcopy(src)
                    clone.set('height', 높이)
                    new_id = str(max([int(x.get('id')) for x in char_group if (x.get('id') or '').isdigit()] + [-1]) + 1)
                    clone.set('id', new_id)
                    char_group.append(clone)
                    char_group.set('itemCnt', str(len(char_group)))
                    by_id[new_id] = clone
                    복제[old] = new_id
                run.set('charPrIDRef', 복제[old])
                count += 1
            return count
        return bind_function(제목_부제_크기, _docfit_namespace)
    if _docfit_symbol == '_칸_글_지우기':
        def _칸_글_지우기(cell):
            for p in 제목_문단들(cell):
                for r in [x for x in p if 제목_xml이름(x) == 'run']:
                    for t in [x for x in r if 제목_xml이름(x) == 't']:
                        r.remove(t)
        return bind_function(_칸_글_지우기, _docfit_namespace)
    if _docfit_symbol == '_칸_날짜_현행화':
        def _칸_날짜_현행화(cell, 오늘):
            """칸 글 가운데 요일이 붙은 날짜를 오늘 날짜로 바꾼다(다른 글과 글자 모양은 그대로). 바꾼 수.

            연도는 ’26처럼 따옴표 붙은 두 자리 약어로 쓴다(2026-10-03 사용자 요청: '2026.'이 아니라 '’26.').
            날짜가 한 글 조각(hp:t) 안에 있으면 그 조각만 고친다(따옴표가 앞 조각에 있으면 그대로 둔다).
            숫자가 여러 조각에 걸쳐 있으면 그 문단 글을 첫 조각에 모아 바꾼다.
            """
            바꾼수 = 0
            for p in 제목_문단들(cell):
                조각들 = [t for r in p if 제목_xml이름(r) == 'run' for t in r if 제목_xml이름(t) == 't' and not len(t)]
                조각수, 앞글 = 0, ''
                for t in 조각들:
                    새글, 수 = 날짜_현행화(t.text or '', 오늘, short_year=True, before=앞글)
                    if 수:
                        t.text = 새글
                        조각수 += 수
                    앞글 += t.text or ''
                if not 조각수 and 조각들:
                    새글, 수 = 날짜_현행화(''.join(t.text or '' for t in 조각들), 오늘, short_year=True)
                    if 수:
                        조각들[0].text = 새글
                        for t in 조각들[1:]:
                            t.text = ''
                        조각수 = 수
                바꾼수 += 조각수
            return 바꾼수
        return bind_function(_칸_날짜_현행화, _docfit_namespace)
    if _docfit_symbol == '_빈칸_서식_참조_변환':
        def _빈칸_서식_참조_변환(cell, maps):
            """글 없는 칸의 문단·글자 모양 참조를 새로 병합된 ID로 바꾼다(글 있는 문단은 표서식 복사가 처리)."""
            for p in 제목_문단들(cell):
                p.set('paraPrIDRef', maps['paraProperties'].get(p.get('paraPrIDRef'), p.get('paraPrIDRef')))
                for r in p:
                    if 제목_xml이름(r) == 'run' and r.get('charPrIDRef') is not None:
                        r.set('charPrIDRef', maps['charProperties'].get(r.get('charPrIDRef'), r.get('charPrIDRef')))
        return bind_function(_빈칸_서식_참조_변환, _docfit_namespace)
    if _docfit_symbol == '_칸_글_넣기':
        def _칸_글_넣기(cell, sample, value):
            """칸의 첫 문단을 글 하나만 있는 한 문단으로 만들어 value를 넣는다(서식 참조는 이후 복사 단계가 맞춘다)."""
            top = 제목_자식(cell, 'subList')
            paras = [p for p in top if 제목_xml이름(p) == 'p']
            for extra in paras[1:]:
                top.remove(extra)
            runs = [r for r in paras[0] if 제목_xml이름(r) == 'run']
            for extra in runs[1:]:
                paras[0].remove(extra)
            for child in list(runs[0]):
                runs[0].remove(child)
            XML_자식_추가(runs[0], sample, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}t').text = value
        return bind_function(_칸_글_넣기, _docfit_namespace)
    if _docfit_symbol == '서식표_생성':
        def 서식표_생성(header, kind, text, cache, 번호=None, 최대폭=None, 본문폭=None):
            """기준 서식 표를 복사해 글을 넣은 새 표를 만든다.

            title1 = 제목 서식1(2×2, 글은 A1), title2 = 제목 서식2(2행1열). 제목 글에 쉼표가 있으면 첫 쉼표 앞은
            부제 15pt·뒤는 제목 27pt 두 줄이다(제목1은 부제 있는 2×2 기준 표를 쓴다). 쉼표가 없으면 제목 한 줄.
            overview = 개요(요지) 표(글은 A1).
            제목 서식의 글은 모두 가운데 정렬이다. midtitle = 중제목 표(번호 칸에 로마자 번호, 글은 글 칸),
            attach1·attach2 = 붙임 서식1(1행3열)·2(1행2열)(글은 마지막 글 칸, '붙임' 글자는 그대로).
            """
            sub = ''
            if kind in ('title1', 'title2'):
                # 첫 쉼표 앞은 부제(2026-10-03 사용자 규칙: 제목1도 쉼표 앞 글자는 부제 크기)
                sub, text = split_title2(text)
            기준종류 = 'title1부제' if kind == 'title1' and sub else kind
            sample, maps = _서식표_기준(header, 기준종류, cache)
            result = copy.deepcopy(sample)
            cells = 제목_셀들(result)
            if kind in ('midtitle', 'attach1', 'attach2'):
                # 마지막 칸이 글 칸이다. 번호·붙임 글자 칸과 빈 칸은 기준 표의 글을 그대로 두거나 비운다.
                blank = not text.strip()
                _칸_글_넣기(cells[-1], sample, text if not blank else 'X')
                if kind == 'midtitle':
                    _칸_글_넣기(cells[0], sample, 번호 or 'Ⅰ')
                if len(cells) == 3:  # 가운데 빈칸은 글이 없으므로 기준 표의 글 없는 문단을 비워 둔다.
                    _칸_글_지우기(cells[1])
                if kind == 'midtitle':
                    중제목_표서식_복사(result, sample, maps, 1, 최대폭, header)
                else:
                    제목_표서식_복사(result, sample, maps)
                    if len(cells) == 3:
                        _빈칸_서식_참조_변환(cells[1], maps)
                if blank:
                    _칸_글_지우기(cells[-1])
                return result
            top = 제목_자식(cells[0], 'subList')
            paras = [p for p in top if 제목_xml이름(p) == 'p']
            # A1 칸: 글 문단 수만큼만 남긴다(부제가 없으면 제목 문단 하나).
            wanted = [t for t in ((sub, text) if sub else (text,))]
            keep = paras[len(paras) - len(wanted):] if (sub or kind == 'title2') else paras[:1]
            for p in paras:
                if p not in keep:
                    top.remove(p)
            blank = not any(w.strip() for w in wanted)
            for p, value in zip(keep, wanted):
                runs = [r for r in p if 제목_xml이름(r) == 'run']
                for extra in runs[1:]:
                    p.remove(extra)
                for child in list(runs[0]):
                    runs[0].remove(child)
                # 글이 비면 서식만 복사되도록 표시용 글자를 잠시 넣었다가 지운다.
                XML_자식_추가(runs[0], sample, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}t').text = value or 'X'
            제목_표서식_복사(result, sample, maps)
            # 서식 프로필의 예시 표는 그 표의 정렬을 따른다.
            if kind != 'overview' and 기준종류 not in cache.get('예시사용', ()):
                제목_문단_가운데정렬(header, result)
            제목_괄호부연_축소(header, result)
            if sub and 기준종류 not in cache.get('예시사용', ()):
                제목_부제_크기(header, result)
            if blank:
                _칸_글_지우기(cells[0])
            # 사용자 글은 A1에만 넣는다. 나머지 칸(날짜·담당자 등)은 기준 표의 글을 그대로 두되, 요일이 붙은
            # 날짜는 오늘 날짜로 바꾼다(2026-10-03 사용자 요청: 예전에는 나머지 칸을 비웠다).
            오늘 = _datetime.date.today()
            for cell in cells[1:]:
                _칸_날짜_현행화(cell, 오늘)
            # 담당자 칸(2×2 표 B2, 2행1열 표 A2 = 마지막 칸)은 설정한 글이 있으면 그 글로 바꾼다(글자 모양은 기준 표 것).
            if kind in ('title1', 'title2') and 제목_담당자_글 and len(cells) >= 2:
                _칸_글_넣기(cells[-1], sample, 제목_담당자_글)
                for p in 제목_문단들(cells[-1]):
                    for cache in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                        p.remove(cache)
            # 제목·개요 표 가로 크기는 쪽 좌우 여백 사이 최대 폭으로 한다(본문폭 = 쪽 정보로 잰 폭, 없으면 그대로).
            if 본문폭:
                _서식표_가로맞춤(result, 본문폭, 비례=기준종류 in cache.get('예시사용', ()))
            return result
        return bind_function(서식표_생성, _docfit_namespace)
    if _docfit_symbol == '_제목개요_빈줄_정리':
        def _제목개요_빈줄_정리(root, 변환목록):
            """변환으로 생긴 서식 표 문단 목록[(문단, 종류)]에서 제목 표 바로 다음이 개요 표면 사이 빈 줄을 지우고,
            제목·개요 표와 그 뒤 첫 항목기호 문장 사이의 빈 줄도 지운다."""
            지운수 = 0
            for (앞, 앞종류), (뒤, 뒤종류) in zip(변환목록, 변환목록[1:]):
                if 앞종류 in ('title1', 'title2') and 뒤종류 == 'overview':
                    지운수 += _문단사이_빈줄_삭제(root, 앞, 뒤)
            if 지운수:
                로그(f"제목 표와 개요 표 사이 빈 줄 {지운수}개 삭제")
            # 개요 표가 붙은 제목 표는 바로 뒤가 개요 표라 그대로이고, 개요 표(없으면 제목 표) 뒤 빈 줄만 지운다.
            뒤빈줄 = sum(_서식표_뒤_빈줄_삭제(root, 문단) for 문단, 종류 in 변환목록
                        if 종류 in ('title1', 'title2', 'title3', 'overview'))
            if 뒤빈줄:
                로그(f"제목·개요 표와 첫 항목기호 문장 사이 빈 줄 {뒤빈줄}개 삭제")
            return 지운수 + 뒤빈줄
        return bind_function(_제목개요_빈줄_정리, _docfit_namespace)
    if _docfit_symbol == '_서식표_글':
        def _서식표_글(table):
            return 제목_문자열(제목_셀들(table)[0])
        return bind_function(_서식표_글, _docfit_namespace)
    if _docfit_symbol == '_서식표_글_확인':
        def _서식표_글_확인(kind, table, text, 번호=None):
            """넣은 글이 요청한 글과 같은지 확인한다(제목1·2는 부제를 나눈 쉼표만 빠짐, 중제목은 번호 칸도 확인)."""
            cells = 제목_셀들(table)
            if kind in ('midtitle', 'attach1', 'attach2'):
                ok = 제목_문자열(cells[-1]).strip() == text.strip()
                if kind == 'midtitle':
                    ok = ok and 제목_문자열(cells[0]).strip() == (번호 or 'Ⅰ')
                if not ok:
                    raise RuntimeError('서식 표 글 삽입 검사 실패')
                return
            if kind in ('title1', 'title2'):
                sub, title = split_title2(text)
                expected = sub + title
            else:
                expected = text.strip()
            if _서식표_글(table).strip() != expected:
                raise RuntimeError('서식 표 글 삽입 검사 실패')
        return bind_function(_서식표_글_확인, _docfit_namespace)
    if _docfit_symbol == '라벨_서식표_적용':
        def 라벨_서식표_적용(source, target=None):
            """표식이 붙은 표를 제목1·제목2·개요 서식 표로 바꾼다. 바꾼 표 수를 돌려준다.

            표식 없는 문서는 파일을 건드리지 않는다. target이 없으면 source를 덮어쓴다.
            """
            target = source if target is None else target
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            if not any(m.encode('utf-8') in data for n, data in contents.items()
                       if re.fullmatch(r'Contents/section\d+\.xml', n) for m in _라벨_표식.values()):
                return 0
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
            cache = {}
            ids = _문서_표번호(sections)
            count = 0
            for name, root in sections.items():
                변환목록 = []
                for p, run in [(p, r) for p in root for r in p]:
                    for table in [t for t in run if 제목_xml이름(t) == 'tbl']:
                        cells = 제목_셀들(table)
                        head_text = 제목_문자열(cells[0]) if cells else ''
                        kind = next((k for k, m in _라벨_표식.items() if head_text.startswith(m)), None)
                        if kind is None:
                            continue
                        text = head_text[len(_라벨_표식[kind]):]
                        result = 서식표_생성(header, kind, text, cache, 최대폭=_구역_본문폭(root),
                                            본문폭=_최종_본문폭(root))
                        _서식표_글_확인(kind, result, text)
                        _서식표_번호_부여(result, ids)
                        run[list(run).index(table)] = result
                        변환목록.append((p, kind))
                        count += 1
                _제목개요_빈줄_정리(root, 변환목록)
                contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            return count
        return bind_function(라벨_서식표_적용, _docfit_namespace)
    if _docfit_symbol == '_문서_표번호':
        def _문서_표번호(sections):
            """문서의 표 id·zOrder 최댓값(새 표에 겹치지 않는 번호를 주기 위한 카운터)."""
            tables = [t for root in sections.values() for t in root.iter() if 제목_xml이름(t) == 'tbl']
            def biggest(attr):
                return max([int(t.get(attr)) for t in tables if (t.get(attr) or '').isdigit()] + [0])
            return {'id': biggest('id'), 'z': biggest('zOrder')}
        return bind_function(_문서_표번호, _docfit_namespace)
    if _docfit_symbol == '_서식표_번호_부여':
        def _서식표_번호_부여(table, ids):
            ids['id'] += 1
            ids['z'] += 1
            table.set('id', str(ids['id']))
            table.set('zOrder', str(ids['z']))
        return bind_function(_서식표_번호_부여, _docfit_namespace)
    if _docfit_symbol == '제목개요폭_hwpx_처리':
        def 제목개요폭_hwpx_처리(source, target=None, selections=None):
            """문서의 제목 표와 바로 뒤 개요 표의 가로 크기를 쪽 좌우 여백 사이 최대 폭으로 맞춘다.

            작업 맨 앞(준말 변환 바로 뒤)에서 표·칸 너비만 바꾼다(2026-10-03 사용자 요청: 가로폭 맞춤을 최대한 앞당김).
            표준서식이 편집 여백을 바꿀 예정이면 바뀐 뒤의 여백으로 잰다(_최종_본문폭). 제목·개요 서식 단계도 같은 폭으로
            다시 맞추므로 이미 맞으면 그 단계에서는 바뀌지 않는다. 이미 최대 폭인 표는 대상에서 뺀다.
            """
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items()
                        if re.fullmatch(r'Contents/section\d+\.xml', n)}

            def 표들(root):
                return [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']

            def 목표폭(table, 본문폭):
                out = 제목_자식(table, 'outMargin')
                try:
                    return int(본문폭) - ((int(out.get('left', '0')) + int(out.get('right', '0'))) if out is not None else 0)
                except ValueError:
                    return None

            if selections is None:
                # 서식 복사 간격 규칙(제목·개요 뒤 첫 문장 간격)은 제목 표가 있는 문서에만 쓴다.
                globals()["_문서_제목표_있음"] = any(제목_대상찾기(root, header) for root in sections.values())

            def 대상(root):
                본문폭 = _최종_본문폭(root)
                if not 본문폭:
                    return []
                tables = 표들(root)
                found = []
                for index, _ in 제목_대상찾기(root, header):
                    found.append(index)
                    if index + 1 < len(tables) and 개요_표인가(tables[index + 1]):
                        found.append(index + 1)
                result = []
                for index in dict.fromkeys(found):
                    size = 제목_자식(tables[index], 'sz')
                    폭 = 목표폭(tables[index], 본문폭)
                    if size is not None and 폭 and size.get('width') != str(폭):
                        result.append(index)
                return result

            if selections is None:
                return {n: 대상(root) for n, root in sections.items()}
            if not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            count = 0
            for name, items in selections.items():
                root = sections[name]
                tables, 본문폭 = 표들(root), _최종_본문폭(root)
                for index in items:
                    table = tables[index]
                    before = 제목_문자열(table)
                    _서식표_가로맞춤(table, 본문폭)
                    # 칸 문단의 줄 배치 캐시는 한/글이 새 폭으로 다시 계산한다.
                    for p in (x for x in table.iter() if 제목_xml이름(x) == 'p'):
                        for cache in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                            p.remove(cache)
                    if 제목_문자열(table) != before:
                        raise RuntimeError('제목·개요 표 가로 크기 맞춤 중 글 보존 검사에 실패했습니다.')
                    count += 1
                contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"제목·개요 표 가로 크기 맞춤: {count}개 (쪽 좌우 여백 사이 최대 폭"
                 + (", 표준서식 편집 여백 반영)" if _예정_좌우여백() else ")"))
            return count
        return bind_function(제목개요폭_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '상자서식_hwpx_처리':
        def 상자서식_hwpx_처리(source, target=None, selections=None):
            """서식 프로필의 한 칸 상자 예시로 문서의 짧은 한 칸 상자(‘< 핵심 추진과제 >’ 등) 서식을 맞춘다.

            제목 표 바로 뒤의 개요 표는 제목·개요 단계가 맡으므로 뺀다. 내용이 많은 상자(글 문단 4개 이상)는 문단마다
            모양이 달라 한 가지 예시로 덮지 않는다. 표·칸·문단·글자 서식만 바꾸고 글은 그대로 둔다.
            """
            예시 = _서식표_예시('box')
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items()
                        if re.fullmatch(r'Contents/section\d+\.xml', n)}

            def 표들(root):
                return [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']

            def 대상(root):
                if 예시 is None:
                    return []
                tables, result = 표들(root), []
                for index, table in enumerate(tables):
                    if 서식표_종류판별(table) != 'box':
                        continue
                    if index > 0 and 제목_유형판별(tables[index - 1], 빈칸허용=True):
                        continue
                    if len([p for p in 제목_문단들(제목_셀들(table)[0]) if 제목_문자열(p).strip()]) > 3:
                        continue
                    result.append(index)
                return result

            if selections is None:
                return {n: 대상(root) for n, root in sections.items()}
            if 예시 is None or not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            sample, maps = 예시[1], 제목_참조병합(header, 예시[0])
            count = 0
            for name, items in selections.items():
                root = sections[name]
                tables = 표들(root)
                for index in items:
                    table = tables[index]
                    before = 제목_문자열(table)
                    제목_표서식_복사(table, sample, maps, 상자=True)
                    if 제목_문자열(table) != before:
                        raise RuntimeError('한 칸 상자 서식 적용 중 글 보존 검사에 실패했습니다.')
                    count += 1
                contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"한 칸 상자 서식: {count}개를 예시 보고서의 상자 모양으로 맞춤")
            return count
        return bind_function(상자서식_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '쪽번호_hwpx_처리':
        def 쪽번호_hwpx_처리(source, target=None, selections=None):
            """서식 프로필의 예시 보고서와 같은 쪽 번호 모양(위치·번호 모양·줄표)으로 문서의 쪽 번호를 맞춘다.

            쪽 번호가 없는 문서에는 넣지 않는다(2026-10-04 결정 4: 모양만 복사).
            """
            모양 = dict(표준서식_설정.get("쪽번호") or {})
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items()
                        if re.fullmatch(r'Contents/section\d+\.xml', n)}

            def 쪽번호들(root):
                return [x for x in root.iter() if 제목_xml이름(x) == 'pageNum']

            if selections is None:
                return {n: [i for i, x in enumerate(쪽번호들(root)) if any(x.get(k) != v for k, v in 모양.items())]
                        if 모양 else [] for n, root in sections.items()}
            if not 모양 or not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            count = 0
            for name, items in selections.items():
                found = 쪽번호들(sections[name])
                for index in items:
                    found[index].attrib.update(모양)
                    count += 1
                contents[name] = ET.tostring(sections[name], encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"쪽 번호 모양: {count}개를 예시 보고서와 같게(" + ", ".join(f"{k}={v}" for k, v in 모양.items()) + ")")
            return count
        return bind_function(쪽번호_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '붙임2종_현재문서_조사':
        def 붙임2종_현재문서_조사(원본문서경로):
            return 서식구조_조사(원본문서경로, 붙임_hwpx_처리, '붙임')
        return bind_function(붙임2종_현재문서_조사, _docfit_namespace)
    if _docfit_symbol == '제목붙임_선행적용':
        def 제목붙임_선행적용(원본문서경로, 현재문서_기준=False, 처리목록=None, 변경알림=None):
            """제목·개요·붙임을 먼저 처리하고 결과 문서를 한 번만 연다.

            원본 HWPX는 읽기만 한다. HWP는 이미 열린 작업용 한글에서 한 번
            변환한다. 별도 한글 생성/등록/원본 재열기를 수행하지 않는다.
            현재문서_기준이면 원본 파일 대신 지금 열린 문서(예: 자간 초기화를 마친
            문서)를 스냅샷으로 저장해 그 위에 서식을 입힌다.
            처리목록 항목은 (사용, 이름, 처리함수, 파일명[, 진행 단계명])이며 앞 항목의 결과 HWPX를
            다음 항목이 이어 받는다. 진행 단계명이 있으면 화면의 진행 단계를 그 이름으로 표시한다.
            """
            if 처리목록 is None:
                처리목록 = (
                    (제목4종_사용, '제목·개요', 제목_hwpx_처리, 'title.hwpx'),
                    (중제목_사용, '중제목', 중제목_hwpx_처리, 'midtitle.hwpx'),
                    (붙임2종_사용, '붙임', 붙임_hwpx_처리, 'attachment.hwpx'),
                )
            if not any(enabled for enabled, *_ in 처리목록):
                return True
            folder = Path(tempfile.mkdtemp(prefix='hwp_format_first_'))
            스냅샷_저장시도 = False
            try:
                source = Path(원본문서경로)
                if 현재문서_기준:
                    스냅샷_저장시도 = True
                    source = _제목_임시hwpx_저장(folder / 'source.hwpx')
                elif source.suffix.lower() != '.hwpx':
                    로그('선행 서식: 현재 한글에서 HWPX 변환 시작')
                    스냅샷_저장시도 = True
                    source = _제목_임시hwpx_저장(folder / 'source.hwpx')
                    로그('선행 서식: HWPX 변환 완료')
                changed = False
                for enabled, name, processor, filename, *진행단계 in 처리목록:
                    if 중단_요청됨():
                        return False
                    if not enabled:
                        continue
                    if 진행단계:
                        단계표시(진행단계[0])
                    로그(f'{name} 구조 직접 분석 시작')
                    selections = processor(source)
                    count = sum(len(items) for items in selections.values())
                    로그(f'{name} 구조 직접 분석 완료: {count}개')
                    if not count:
                        continue
                    target = folder / filename
                    processor(source, target, selections)
                    if name == '본문 서식 일괄 적용':
                        from docfit_core.marker_prefix import audit_hwpx_prefixes
                        prefix_audit = audit_hwpx_prefixes(
                            target, 표준서식_설정.get('기호_규칙', ()))
                        mismatch_count = len(prefix_audit['mismatches'])
                        로그(f'[항목기호 앞 공백 검수] 검사 {sum(prefix_audit["measured"].values())}문단 / '
                             f'불일치 {mismatch_count}문단')
                        for mismatch in prefix_audit['mismatches'][:20]:
                            로그(f'[항목기호 공백 불일치] {mismatch["marker"]}: '
                                 f'{mismatch["actual"]}칸 → {mismatch["expected"]}칸 / '
                                 f'{mismatch["text"][:80]}')
                        from docfit_core.indent_stage_trace import capture_saved_stage, trace_enabled
                        if trace_enabled():
                            capture_saved_stage('XML 산출물·한글 재열기 전', target)
                    source = target
                    changed = True
                    로그(f'{name} 선행 서식 파일 생성 완료')
                if 변경알림 is not None:
                    변경알림['changed'] = changed
                if changed:
                    if 중단_요청됨():
                        return False
                    로그('선행 서식 결과 열기 시작')
                    if 한글_문서_열기(hwp, source, 'HWPX', 'forceopen:true') is False:
                        raise RuntimeError('선행 서식 결과를 열지 못했습니다.')
                    로그('선행 서식 결과 열기 완료')
                return True
            except Exception:
                # 현재 문서 기준 스냅샷 SaveAs 후 분석이 실패하면 한글은 임시
                # source.hwpx를 계속 열고 있을 수 있다. 원본으로 되돌려 임시파일
                # 핸들이 남는 문제와 다음 작업의 잘못된 문서 대상을 함께 막는다.
                if 스냅샷_저장시도:
                    원본 = Path(원본문서경로)
                    형식 = 'HWPX' if 원본.suffix.lower() == '.hwpx' else 'HWP'
                    try:
                        if 한글_문서_열기(hwp, 원본, 형식, 'forceopen:true') is False:
                            raise RuntimeError('원본 문서 재열기 결과가 False입니다.')
                        로그('선행 서식 실패 후 원본 문서 복구 완료')
                    except Exception as 복구오류:
                        로그(f'선행 서식 오류 후 원본 문서 복구 실패: {복구오류}')
                raise
            finally:
                _제목_임시폴더_정리(folder)
        return bind_function(제목붙임_선행적용, _docfit_namespace)
    if _docfit_symbol == '정밀표_선행적용':
        def 정밀표_선행적용():
            """현재 문서를 HWPX로 스냅샷 저장한 뒤 선택 프로필의 표 서식을 적용한다."""
            if not 활성_정밀표_프로필 or not 활성_정밀표_프로필.get("tables"):
                return True
            folder = Path(tempfile.mkdtemp(prefix="hwp_precise_table_"))
            try:
                source = _제목_임시hwpx_저장(folder / "before.hwpx")
                target = folder / "after.hwpx"
                result = 정밀표_서식_적용(source, target, 활성_정밀표_프로필)
                if result["applied"]:
                    # 예시 표 서식을 덮어쓴 뒤에도 표 칸 날짜는 한 줄로 둔다.
                    날짜칸 = 표날짜칸_hwpx_처리(target)
                    if any(날짜칸.values()):
                        표날짜칸_hwpx_처리(target, target, 날짜칸)
                    if 한글_문서_열기(hwp, target, "HWPX", "forceopen:true") is False:
                        raise RuntimeError("정밀 표 서식 결과를 열지 못했습니다.")
                로그(
                    f"일반 표 정밀 복제: 적용 {result['applied']}개 / 건너뜀 {result['skipped']}개"
                )
                for match in result["matches"]:
                    진단로그(
                        f"[표 매칭] 대상 {match['target'] + 1}번 ← 프로필 {match['source'] + 1}번 / "
                        f"점수 {match['score']:.1f} / 병합·크기 {'복제' if match['geometry'] else '보존'}"
                    )
                return True
            finally:
                _제목_임시폴더_정리(folder)
        return bind_function(정밀표_선행적용, _docfit_namespace)
    if _docfit_symbol == '붙임2종_현재문서_적용':
        def 붙임2종_현재문서_적용(selections):
            if not any(items for items in selections.values()):
                로그('붙임 서식 대상 없음: 붙임서식을 적용하지 않습니다.')
                return
            folder = Path(tempfile.mkdtemp(prefix='hwp_attach_apply_'))
            try:
                source, target = folder/'before.hwpx', folder/'after.hwpx'
                _제목_임시hwpx_저장(source)
                count = 붙임_hwpx_처리(source, target, selections)
                if 한글_문서_열기(hwp, target, 'HWPX', 'forceopen:true') is False: raise RuntimeError('붙임 적용 결과를 열지 못했습니다.')
                로그(f'붙임 서식 자동 적용: {count}개 / 유형 ' + ', '.join(str(k) for v in selections.values() for _, k in v))
            finally:
                _제목_임시폴더_정리(folder)
        return bind_function(붙임2종_현재문서_적용, _docfit_namespace)
    raise KeyError(_docfit_symbol)
