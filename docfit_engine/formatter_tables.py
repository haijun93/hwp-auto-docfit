"""표 서명·정밀 복제·일반 표 서식·너비·테두리 — formatter의 호환 전역으로 바인딩할 원본 정의."""

SYMBOLS = ('_표_텍스트', '_표_서명', '_정밀표_프로필_추출', '표_날짜칸_한줄', '표날짜칸_hwpx_처리', '두글자칸_hwpx_처리', '_정밀표_매칭점수', '_정밀표_셀서식_복사', '_표_글_그대로', '_정밀표_글자위치_복사', '_정밀표_같은표만', '_정밀표_글같음', '정밀표_서식_적용', '기본표서식', '_기본표서식_대상인가', '기본표서식_hwpx_처리', '표너비_hwpx_처리', '기본표서식_선행적용', '_셀_안쪽여백_단계축소', '표_셀_안쪽여백_전체_적용', '본문_가용너비_mm', '표_전체너비_mm', '현재셀_너비_mm', '표_열너비_순서대로_설정', '표_열너비_본문맞춤_시도', '표_열너비_본문맞춤_전체_적용', '표_셀_테두리_적용', '표_테두리_삼선표_적용', '표_테두리_전체_적용', '넓은_표칸_줄인가', '컨트롤_내부_문장부호_처리')

def _install(*, _docfit_namespace, _docfit_symbol, bind_function):
    global _표_텍스트, _표_서명, _정밀표_프로필_추출, 표_날짜칸_한줄, 표날짜칸_hwpx_처리, 두글자칸_hwpx_처리, _정밀표_매칭점수, _정밀표_셀서식_복사, _표_글_그대로, _정밀표_글자위치_복사, _정밀표_같은표만, _정밀표_글같음, 정밀표_서식_적용, 기본표서식, _기본표서식_대상인가, 기본표서식_hwpx_처리, 표너비_hwpx_처리, 기본표서식_선행적용, _셀_안쪽여백_단계축소, 표_셀_안쪽여백_전체_적용, 본문_가용너비_mm, 표_전체너비_mm, 현재셀_너비_mm, 표_열너비_순서대로_설정, 표_열너비_본문맞춤_시도, 표_열너비_본문맞춤_전체_적용, 표_셀_테두리_적용, 표_테두리_삼선표_적용, 표_테두리_전체_적용, 넓은_표칸_줄인가, 컨트롤_내부_문장부호_처리
    if _docfit_symbol == '_표_텍스트':
        def _표_텍스트(element):
            return " ".join("".join(t.itertext()).strip() for t in element.iter()
                            if 제목_xml이름(t) == "t" and "".join(t.itertext()).strip())
        return bind_function(_표_텍스트, _docfit_namespace)
    if _docfit_symbol == '_표_서명':
        def _표_서명(table, ordinal=0):
            rows = [row for row in table.iter() if 제목_xml이름(row) == "tr"]
            cells = 제목_셀들(table)
            first_row_cells = [cell for cell in rows[0] if 제목_xml이름(cell) == "tc"] if rows else []
            return {
                "ordinal": ordinal,
                "rows": int(table.get("rowCnt", len(rows)) or len(rows)),
                "cols": int(table.get("colCnt", 0) or 0),
                "cell_count": len(cells),
                "first_cell": _표_텍스트(cells[0])[:120] if cells else "",
                "first_row": " | ".join(_표_텍스트(cell) for cell in first_row_cells)[:500],
                # 표 글 전체(빈칸 뺌)의 지문: 칸 구성이 같은 두 표(교육부 '< 지역교육 혁신모델 >' 상자 둘)를 가린다.
                "text_key": hashlib.sha256(re.sub(r"\s", "", _표_글_그대로(table)).encode("utf-8")).hexdigest()[:16],
            }
        return bind_function(_표_서명, _docfit_namespace)
    if _docfit_symbol == '_정밀표_프로필_추출':
        def _정밀표_프로필_추출(header, sections):
            """표별 구조와 셀 서식을 원본 HWPX XML 그대로 JSON 호환 형태로 보존한다."""
            tables = []
            ordinal = 0
            for section_name in sections:
                root = safe_xml_fromstring(sections[section_name])
                for table in (e for e in root.iter() if 제목_xml이름(e) == "tbl"):
                    signature = _표_서명(table, ordinal)
                    signature["section"] = section_name
                    signature["table_xml"] = ET.tostring(table, encoding="unicode")
                    tables.append(signature)
                    ordinal += 1
            return {
                "version": 1,
                "header_xml": ET.tostring(header, encoding="unicode"),
                "tables": tables,
            }
        return bind_function(_정밀표_프로필_추출, _docfit_namespace)
    if _docfit_symbol == '표_날짜칸_한줄':
        def 표_날짜칸_한줄(table):
            """표의 날짜 칸(주로 날짜인 칸)을 '한 줄로 입력'(lineWrap=SQUEEZE)으로 둔다. 바꾼 칸 수.

            표 칸 안 날짜는 한 줄로 표기하는 것이 원칙이다(사용자 규칙, 2026-10-10). 칸 폭이 좁아도 한/글이 글자 폭을
            줄여 한 줄을 지킨다. 안쪽 표는 그 표대로 따로 본다.
            """
            count = 0
            from docfit_core.table_style import iter_unprotected_cells
            for cell in iter_unprotected_cells(table):
                sub = 제목_자식(cell, 'subList')
                if sub is None or sub.get('lineWrap') == 'SQUEEZE':
                    continue
                if any(제목_xml이름(x) == 'tbl' for x in sub.iter()):
                    continue
                if 날짜칸인가(''.join(제목_문자열(q) for q in sub if 제목_xml이름(q) == 'p')):
                    sub.set('lineWrap', 'SQUEEZE')
                    count += 1
            return count
        return bind_function(표_날짜칸_한줄, _docfit_namespace)
    if _docfit_symbol == '표날짜칸_hwpx_처리':
        def 표날짜칸_hwpx_처리(source, target=None, selections=None):
            """문서의 모든 표에서 날짜 칸을 한 줄로 입력으로 둔다(선행 서식 단계, 칸 글은 바꾸지 않음)."""
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}

            def 대상(root):
                보호 = 보호표_목록(root)
                return [i for i, t in enumerate(x for x in root.iter() if 제목_xml이름(x) == 'tbl')
                        if id(t) not in 보호 and 표_날짜칸_한줄(copy.deepcopy(t))]

            if selections is None:
                return {n: 대상(root) for n, root in sections.items()}
            if not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            count = 0
            for name, items in selections.items():
                root = sections[name]
                tables = [x for x in root.iter() if 제목_xml이름(x) == 'tbl']
                보호 = 보호표_목록(root)
                for index in items:
                    if id(tables[index]) in 보호:
                        continue
                    before = _표_텍스트(tables[index])
                    count += 표_날짜칸_한줄(tables[index])
                    if _표_텍스트(tables[index]) != before:
                        raise RuntimeError('표 날짜 칸 한 줄 처리 중 표 내용 보존 검사에 실패했습니다.')
                contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"표 날짜 칸 한 줄: {count}칸을 한 줄로 입력으로 지정")
            return count
        return bind_function(표날짜칸_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '두글자칸_hwpx_처리':
        def 두글자칸_hwpx_처리(source, target=None, selections=None):
            """표 칸 글이 한글 두 글자뿐이고 사이에 빈칸이 없으면 빈칸 1칸을 넣는다('구분' → '구 분', 사용자 규칙 2026-10-17).

            숫자·영문이 섞인 칸('10'·'1부')과 제목·중제목·붙임 서식 표, 사용자가 꾸민 표는 건드리지 않는다.
            """
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items()
                        if re.fullmatch(r'Contents/section\d+\.xml', n)}

            def 대상(root):
                """(글 요소, 첫 글자 뒤 위치) 목록. 두 글자가 한 글 요소에 함께 있을 때만."""
                보호 = 보호표_목록(root)
                결과 = []
                for table in (x for x in root.iter() if 제목_xml이름(x) == 'tbl'):
                    if id(table) in 보호 or 서식표_종류판별(table):
                        continue
                    for cell in 제목_셀들(table):
                        if not re.fullmatch(r'\s*[가-힣]{2}\s*', 제목_문자열(cell)):
                            continue
                        ts = [t for t in cell.iter() if 제목_xml이름(t) == 't' and (t.text or '').strip()]
                        if len(ts) == 1 and not len(ts[0]) and re.search(r'[가-힣]{2}', ts[0].text):
                            결과.append((ts[0], re.search(r'[가-힣]{2}', ts[0].text).start() + 1))
                return 결과

            if selections is None:
                return {n: list(range(len(대상(root)))) for n, root in sections.items()}
            if not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            count = 0
            for name, root in sections.items():
                for t, at in 대상(root):
                    t.text = t.text[:at] + ' ' + t.text[at:]
                    count += 1
                contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"표 두 글자 칸: {count}칸의 두 글자 사이에 빈칸 1칸")
            return count
        return bind_function(두글자칸_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '_정밀표_매칭점수':
        def _정밀표_매칭점수(target_signature, source_signature):
            score = 0.0
            if (target_signature["rows"], target_signature["cols"]) == (source_signature["rows"], source_signature["cols"]):
                score += 80
            else:
                score -= 20 * (abs(target_signature["rows"] - source_signature["rows"])
                               + abs(target_signature["cols"] - source_signature["cols"]))
            if target_signature["cell_count"] == source_signature["cell_count"]:
                score += 45
            if target_signature["first_cell"] and target_signature["first_cell"] == source_signature["first_cell"]:
                score += 35
            score += 25 * difflib.SequenceMatcher(
                None, target_signature["first_row"], source_signature["first_row"]
            ).ratio()
            score += max(0, 10 - abs(target_signature["ordinal"] - source_signature["ordinal"]) * 2)
            if target_signature.get("text_key") and target_signature.get("text_key") == source_signature.get("text_key"):
                score += 60   # 글이 똑같은 표(같은 표): 칸 구성이 같은 다른 표와 모호하지 않게(2026-10-17 재연 시험)
            return round(score, 2)
        return bind_function(_정밀표_매칭점수, _docfit_namespace)
    if _docfit_symbol == '_정밀표_셀서식_복사':
        def _정밀표_셀서식_복사(target, sample, maps, copy_geometry):
            """셀 내용은 유지하고 HWPX 표·셀·문단·문자 서식 참조만 복사한다."""
            reference_attrs = {
                "borderFillIDRef": "borderFills",
                "paraPrIDRef": "paraProperties",
                "charPrIDRef": "charProperties",
            }
            for attr in ("borderFillIDRef", "cellSpacing", "textWrap", "textFlow", "pageBreak", "repeatHeader"):
                if attr in sample.attrib:
                    value = sample.get(attr)
                    target.set(attr, maps.get(reference_attrs.get(attr, ""), {}).get(value, value))
            for name in ("sz", "inMargin", "outMargin"):
                source_child, target_child = 제목_자식(sample, name), 제목_자식(target, name)
                if source_child is not None and target_child is not None:
                    target_child.attrib.update(source_child.attrib)

            target_cells, source_cells = 제목_셀들(target), 제목_셀들(sample)
            for target_cell, source_cell in zip(target_cells, source_cells):
                border = source_cell.get("borderFillIDRef")
                if border is not None:
                    target_cell.set("borderFillIDRef", maps["borderFills"].get(border, border))
                if "hasMargin" in source_cell.attrib:
                    target_cell.set("hasMargin", source_cell.get("hasMargin"))
                geometry_names = ("cellAddr", "cellSpan", "cellSz") if copy_geometry else ()
                for name in (*geometry_names, "cellMargin"):
                    source_child, target_child = 제목_자식(source_cell, name), 제목_자식(target_cell, name)
                    if source_child is not None and target_child is not None:
                        target_child.attrib.update(source_child.attrib)
                source_sub, target_sub = 제목_자식(source_cell, "subList"), 제목_자식(target_cell, "subList")
                if source_sub is not None and target_sub is not None:
                    for attr in ("vertAlign", "textDirection", "lineWrap"):
                        if attr in source_sub.attrib:
                            target_sub.set(attr, source_sub.get(attr))

                source_paragraphs = 제목_문단들(source_cell)
                target_paragraphs = 제목_문단들(target_cell)
                for paragraph_index, target_para in enumerate(target_paragraphs):
                    if not source_paragraphs:
                        break
                    source_para = source_paragraphs[min(paragraph_index, len(source_paragraphs) - 1)]
                    para_ref = source_para.get("paraPrIDRef")
                    if para_ref is not None:
                        target_para.set("paraPrIDRef", maps["paraProperties"].get(para_ref, para_ref))
                    source_runs = [run for run in source_para if 제목_xml이름(run) == "run"]
                    target_runs = [run for run in target_para if 제목_xml이름(run) == "run"]
                    if _정밀표_글자위치_복사(target_para, source_runs, target_runs, maps):
                        continue
                    for run_index, target_run in enumerate(target_runs):
                        if not source_runs:
                            break
                        source_run = source_runs[min(run_index, len(source_runs) - 1)]
                        char_ref = source_run.get("charPrIDRef")
                        if char_ref is not None:
                            target_run.set("charPrIDRef", maps["charProperties"].get(char_ref, char_ref))
        return bind_function(_정밀표_셀서식_복사, _docfit_namespace)
    if _docfit_symbol == '_표_글_그대로':
        def _표_글_그대로(table):
            """표의 글을 빈칸까지 그대로 이어 붙인 문자열(보존 검사용). run이 글자 위치로 나뉘어도 같다."""
            return "".join("".join(t.itertext()) for t in table.iter() if 제목_xml이름(t) == "t")
        return bind_function(_표_글_그대로, _docfit_namespace)
    if _docfit_symbol == '_정밀표_글자위치_복사':
        def _정밀표_글자위치_복사(target_para, source_runs, target_runs, maps):
            """칸 문단 글이 예시와 같으면 예시 run 경계대로 나눠 글자 모양을 글자 위치에 맞춰 옮긴다. 옮겼으면 True.

            run 순서로 짝지으면 run 수가 다를 때 모양이 엇갈렸다: 예시 개요 '…새로운|거점|(지구)|…'(5개)를
            '…거점|(지구)|…'(3개)에 입히면 '(지구)' 뒤 글 전체가 13pt가 됐다(서식 재연 시험, 2026-10-17).
            글 요소 하나에 글만 든 run(빈칸 묶음·컨트롤 없음)일 때만 다룬다.
            """
            def 단순글(run):
                ts = [x for x in run if 제목_xml이름(x) == "t"]
                if len(ts) != len(run) or len(ts) > 1 or (ts and len(ts[0])):
                    return None
                return (ts[0].text or "") if ts else ""
            source_texts = [단순글(r) for r in source_runs]
            target_texts = [단순글(r) for r in target_runs]
            if not target_runs or None in source_texts or None in target_texts:
                return False
            if "".join(source_texts) != "".join(target_texts) or not "".join(target_texts):
                return False
            template = target_runs[0]
            index = list(target_para).index(template)
            for run in target_runs:
                target_para.remove(run)
            made = 0
            for source_run, text in zip(source_runs, source_texts):
                if not text:
                    continue
                run = copy.deepcopy(template)
                for child in list(run):
                    run.remove(child)
                t = type(template)(template.tag.rsplit("}", 1)[0] + "}t", {})
                t.text = text
                run.append(t)
                char_ref = source_run.get("charPrIDRef")
                if char_ref is not None:
                    run.set("charPrIDRef", maps["charProperties"].get(char_ref, char_ref))
                target_para.insert(index + made, run)
                made += 1
            for cache in [x for x in target_para if 제목_xml이름(x) == "linesegarray"]:
                target_para.remove(cache)
            return True
        return bind_function(_정밀표_글자위치_복사, _docfit_namespace)
    if _docfit_symbol == '_정밀표_같은표만':
        def _정밀표_같은표만(table, signature):
            """정밀 복제를 같은 표(첫 칸 글이 같은 예시 표)에만 할 표인가: 한 칸 표와 서식 표(제목·중제목·붙임·한 칸 상자).

            이 표들은 서식 표 단계가 예시 모양을 문단별로 입힌다. 예전에는 칸 수만 같으면 다른 한 칸 표를 짝지어 상자 둘째
            문단(파란 11pt 안내 글 등)까지 첫 문단 서식으로 덮었다(2026-10-04 범정부오피스 인천 서식 왕복 시험). 같은 표가
            예시에 있으면(예시 문서 자체를 정리할 때 등) 그 표 모양을 그대로 되살린다.
            """
            return signature["cell_count"] == 1 or bool(서식표_종류판별(table))
        return bind_function(_정밀표_같은표만, _docfit_namespace)
    if _docfit_symbol == '_정밀표_글같음':
        def _정밀표_글같음(first, second):
            """두 표 첫 칸 글이 같은가(빈칸 무시, 빈 글은 같지 않음)."""
            first, second = re.sub(r"\s", "", first or ""), re.sub(r"\s", "", second or "")
            return bool(first) and first == second
        return bind_function(_정밀표_글같음, _docfit_namespace)
    if _docfit_symbol == '정밀표_서식_적용':
        def 정밀표_서식_적용(source_path, target_path, precise_profile):
            """프로필 표를 구조·앵커로 매칭해 대상 HWPX에 셀별 서식을 적용한다."""
            if Path(source_path).resolve() == Path(target_path).resolve():
                raise ValueError("원본 문서에는 정밀 표 서식을 덮어쓸 수 없습니다.")
            if not precise_profile or not precise_profile.get("tables"):
                return {"applied": 0, "skipped": 0, "matches": []}
            with open_hwpx_safely(source_path) as archive:
                contents = {name: archive.read(name) for name in archive.namelist()}
            target_header = safe_xml_fromstring(contents["Contents/header.xml"])
            source_header = safe_xml_fromstring(precise_profile["header_xml"].encode("utf-8"))
            maps = 제목_참조병합(target_header, source_header)
            source_tables = []
            for item in precise_profile["tables"]:
                parsed = safe_xml_fromstring(item["table_xml"].encode("utf-8"))
                source_tables.append((item, parsed))

            before_text = []
            matches = []
            fallbacks = []
            ordinal = 0
            for name in sorted(n for n in contents if re.fullmatch(r"Contents/section\d+\.xml", n)):
                root = safe_xml_fromstring(contents[name])
                changed = False
                보호 = 보호표_목록(root)
                for table in (element for element in root.iter() if 제목_xml이름(element) == "tbl"):
                    before_text.append(_표_글_그대로(table))
                    if id(table) in 보호:
                        ordinal += 1   # 사용자가 꾸민 표(안에 든 표 포함)는 정밀 복제하지 않는다
                        continue
                    target_signature = _표_서명(table, ordinal)
                    scored = [(_정밀표_매칭점수(target_signature, signature), signature, sample)
                              for signature, sample in source_tables]
                    from docfit_core.format_elements import ambiguous_table_match
                    if ambiguous_table_match(scored):
                        from docfit_core.table_style import HeaderPool, apply_table_style, default_style, is_grid_table, valid_style
                        fallback = globals().get("활성_표서식_프로필")
                        fallback = fallback if valid_style(fallback) else default_style()
                        applied_fallback = _기본표서식_대상인가(table)
                        if applied_fallback:
                            apply_table_style(HeaderPool(target_header, fallback), table)
                            changed = True
                        fallbacks.append({"target": ordinal, "reason": "ambiguous_match",
                                          "applied": applied_fallback})
                        로그(f"정밀 표 {ordinal + 1}: 후보 점수가 모호하여 정밀 복제 생략"
                           + (" · 기본 표 서식 적용" if applied_fallback else " · 특수 표 원형 유지"))
                        ordinal += 1
                        continue
                    score, signature, sample = max(scored, key=lambda item: item[0])
                    # 행·열 또는 셀 수가 같은 표만 적용해 무관한 레이아웃 훼손을 방지한다.
                    compatible = ((target_signature["rows"], target_signature["cols"])
                                  == (signature["rows"], signature["cols"])
                                  or target_signature["cell_count"] == signature["cell_count"])
                    # 서식 표(제목·중제목·붙임·한 칸 상자)와 한 칸 표는 같은 표(첫 칸 글이 같음)일 때만, 일반 표는 대응하는 표
                    # (첫 칸 글이 같거나 첫 행 글이 60% 이상 같음)일 때만 정밀 복제한다. 예전에는 행·열 수만 같으면 다른 문서의
                    # 무관한 표 모양을 입혀 서식 프로필의 대표 표 서식(기본 표 서식)을 덮었다(2026-10-04 범정부오피스 서식 시험).
                    if compatible and _정밀표_같은표만(table, target_signature):
                        compatible = _정밀표_글같음(target_signature["first_cell"], signature["first_cell"])
                    elif compatible:
                        compatible = (_정밀표_글같음(target_signature["first_cell"], signature["first_cell"])
                                      or difflib.SequenceMatcher(None, target_signature["first_row"],
                                                                 signature["first_row"]).ratio() >= 0.6)
                    if compatible and score >= 45:
                        exact = (target_signature["rows"] == signature["rows"]
                                 and target_signature["cols"] == signature["cols"]
                                 and target_signature["cell_count"] == signature["cell_count"])
                        _정밀표_셀서식_복사(table, sample, maps, exact)
                        changed = True
                        matches.append({"target": ordinal, "source": signature["ordinal"],
                                        "score": score, "geometry": exact})
                    ordinal += 1
                if changed:
                    contents[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            contents["Contents/header.xml"] = ET.tostring(target_header, encoding="utf-8", xml_declaration=True)

            after_text = []
            for name in sorted(n for n in contents if re.fullmatch(r"Contents/section\d+\.xml", n)):
                root = safe_xml_fromstring(contents[name])
                after_text.extend(_표_글_그대로(table) for table in root.iter() if 제목_xml이름(table) == "tbl")
            if before_text != after_text:
                raise RuntimeError("정밀 표 서식 적용 중 표 내용 보존 검사에 실패했습니다.")
            with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for name, data in contents.items():
                    archive.writestr(name, data, compress_type=zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED)
            return {"applied": len(matches), "skipped": ordinal - len(matches), "matches": matches, "fallbacks": fallbacks}
        return bind_function(정밀표_서식_적용, _docfit_namespace)
    if _docfit_symbol == '기본표서식':
        def 기본표서식():
            """기본 표 서식. 선택한 서식 프로필이 예시 보고서의 일반 표에서 배운 서식이 있으면 그것(결정 5), 없으면 준말
            '표'의 본말(배운 서식이 없으면 내장 기본값). 준말 '표'가 없거나 다른 본말이면 None."""
            if 활성_표서식_프로필 and 표서식_유효(활성_표서식_프로필):
                return 활성_표서식_프로필
            return 준말_표서식(준말_등록표)
        return bind_function(기본표서식, _docfit_namespace)
    if _docfit_symbol == '_기본표서식_대상인가':
        def _기본표서식_대상인가(table):
            """2행 2열 이상 일반 표만 대상이다. 제목(준말로 만든 빈 정보 칸 제목 표 포함)·중제목·붙임 서식 표는 뺀다."""
            # '(단위: 개소)' 같은 단위 캡션이 달린 표는 작성자가 꾸민 표라 서식을 입히지 않는다(사용자 규칙, 2026-10-15).
            # '<표 1> 추진 현황' 같은 일반 캡션 표는 베타처럼 데이터 표로 서식을 입힌다.
            return bool(표서식_모양인가(table) and not 단위캡션표인가(table) and not (
                제목_유형판별(table, 빈칸허용=True) or 중제목_글칸들(table) or 붙임_유형판별(table)))
        return bind_function(_기본표서식_대상인가, _docfit_namespace)
    if _docfit_symbol == '기본표서식_hwpx_처리':
        def 기본표서식_hwpx_처리(source, target=None, selections=None):
            """문서의 일반 표에 기본 표 서식(준말 '표'의 본말)을 입힌다. 칸 글은 바꾸지 않는다.

            예시 표의 같은 위치 칸에서 테두리·바탕색·글꼴(종류·크기·굵게·장평·자간)·세로 정렬을 가져오고,
            머리글과 한 줄에 들어가는 짧은 문단만 예시 정렬로 바꾼다. 내장 기본값은 본문 칸 가운데 첫 열이 아닌
            칸(B2·B3 …)의 문장을 길이와 관계없이 왼쪽 정렬한다(숫자·날짜 칸은 예시 정렬, docfit_core.table_style).
            """
            style = 기본표서식()
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}

            def 표들(root):
                return [t for t in root.iter() if 제목_xml이름(t) == 'tbl']

            if selections is None:
                if style is None:
                    return {n: [] for n in sections}
                # 문서 머리의 결재란·보고자 표와 제목처럼 큰 글자가 든 표는 데이터 표가 아니라 일반 표 서식을 입히지 않는다
                # (서식 요소 분석의 데이터 표와 같은 기준, 2026-10-04).
                순서 = sorted(sections, key=lambda n: int(re.search(r'(\d+)\.xml$', n).group(1)))
                머리표 = {id(t) for t in 서식요소.head_block_tables([sections[n] for n in 순서], header)}
                # 사용자가 꾸민 표 안에 든 표도 그대로 둔다.
                제외 = 머리표.union(*(보호표_목록(root) for root in sections.values()))
                return {n: [i for i, t in enumerate(표들(root)) if _기본표서식_대상인가(t) and id(t) not in 제외]
                        for n, root in sections.items()}
            if style is None or not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            저장소 = 표서식_저장소(header, style)
            count = 0
            for name, items in selections.items():
                root = sections[name]
                found = 표들(root)
                for index in items:
                    table = found[index]
                    if not _기본표서식_대상인가(table):
                        raise RuntimeError('처리 중 표 구조가 바뀌어 기본 표 서식 적용을 중단했습니다.')
                    before = _표_텍스트(table)
                    표서식_적용(저장소, table)
                    if _표_텍스트(table) != before:
                        raise RuntimeError('기본 표 서식 적용 중 표 내용 보존 검사에 실패했습니다.')
                    count += 1
                contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            return count
        return bind_function(기본표서식_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '표너비_hwpx_처리':
        def 표너비_hwpx_처리(source, target=None, selections=None):
            """가로로 칸이 둘 이상인 본문 표의 열 너비를 칸 글자 수(글자 사이 빈칸 포함)에 비례해 나누고,
            표 폭은 쪽 좌우 여백 사이 최대 폭으로 맞춘다(docfit_core.table_width). 칸 글은 바꾸지 않는다.

            제목·중제목·붙임 서식 표와 한 칸 상자는 서식 표 자체의 배치를 쓰므로 건드리지 않는다. 쪽 정보(pagePr)가
            없는 구역의 표도 폭을 알 수 없어 그대로 둔다.
            """
            with open_hwpx_safely(source) as z:
                contents = {n: z.read(n) for n in z.namelist()}
            for name, data in contents.items():
                if name.startswith('Contents/') and name.endswith('.xml'):
                    for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                        if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
            header = safe_xml_fromstring(contents['Contents/header.xml'])
            sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}

            def 표들(root):
                # 본문에 놓인 표만(칸 안의 표는 바깥 칸 폭에 묶여 있어 다루지 않는다).
                return [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']

            def 대상인가(table):
                return 서식표_종류판별(table) is None and 표너비_대상인가(table)

            if selections is None:
                return {n: ([i for i, t in enumerate(표들(root)) if 대상인가(t)] if _구역_본문폭(root, None) else [])
                        for n, root in sections.items()}
            if not any(items for items in selections.values()):
                if target is not None: shutil.copyfile(source, target)
                return 0
            index = 서식요소.HeaderIndex(header)
            count = 0
            for name, items in selections.items():
                root = sections[name]
                found = 표들(root)
                놓인문단 = {id(t): p for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl'}
                본문폭 = _구역_본문폭(root, None)
                for number in items:
                    table = found[number]
                    if not 대상인가(table):
                        raise RuntimeError('처리 중 표 구조가 바뀌어 표 칸 너비 맞춤을 중단했습니다.')
                    before = _표_텍스트(table)
                    # 표 앞 글(빈칸)·문단 여백만큼 빼야 넓힌 표가 줄을 넘쳐 용지 밖으로 밀리지 않는다.
                    if 표너비_맞춤(table, 본문폭, index, reserve=표너비_앞자리(놓인문단.get(id(table)), table, index)):
                        count += 1
                    if _표_텍스트(table) != before:
                        raise RuntimeError('표 칸 너비 맞춤 중 표 내용 보존 검사에 실패했습니다.')
                contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            _hwpx_안전_저장(contents, target)
            로그(f"표 칸 너비 맞춤: 표 {count}개(글자 수 비례, 쪽 좌우 여백 폭)")
            return count
        return bind_function(표너비_hwpx_처리, _docfit_namespace)
    if _docfit_symbol == '기본표서식_선행적용':
        def 기본표서식_선행적용(원본문서경로, 현재문서_기준=False, 변경알림=None):
            """문서의 일반 표에 기본 표 서식을 입힌 결과를 한 번만 다시 연다(대상 표가 없으면 다시 열지 않음)."""
            return 제목붙임_선행적용(원본문서경로, 현재문서_기준=현재문서_기준,
                                    처리목록=((True, '기본 표 서식', 기본표서식_hwpx_처리, 'table_style.hwpx'),), 변경알림=변경알림)
        return bind_function(기본표서식_선행적용, _docfit_namespace)
    if _docfit_symbol == '_셀_안쪽여백_단계축소':
        def _셀_안쪽여백_단계축소():
            현재_mm = 표_셀여백_기본_mm
            최대반복 = max(1, int(round((표_셀여백_기본_mm - 표_셀여백_최소_mm) / 표_셀여백_스텝_mm)))
            for _ in range(최대반복):
                if 중단_요청됨():
                    return False
                현재_mm = max(표_셀여백_최소_mm, round(현재_mm - 표_셀여백_스텝_mm, 2))
                if not 셀_안쪽여백_현재선택(현재_mm):
                    return False
                새_줄수 = 셀_화면줄수()
                if 새_줄수 is None:
                    return False
                if 새_줄수 <= 1:
                    return True
                if 현재_mm <= 표_셀여백_최소_mm:
                    break
            return False
        return bind_function(_셀_안쪽여백_단계축소, _docfit_namespace)
    if _docfit_symbol == '표_셀_안쪽여백_전체_적용':
        def 표_셀_안쪽여백_전체_적용():
            if not 표_셀여백_축소_사용:
                return True
            if 중단_요청됨():
                return False
            로그("셀 안쪽 여백 강제 축소 시작")
            원위치 = hwp.GetPos()
            한칸표영역 = 한칸표_영역_목록()
            검사수 = 0
            적용수 = 0
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
                if area in 한칸표영역:
                    continue
                주소, _ = 현재_셀_주소_행번호()
                if 주소 is None:
                    continue
                검사수 += 1
                if 셀_안쪽여백_축소_시도():
                    적용수 += 1
            try:
                hwp.SetPos(*원위치)
            except Exception:
                pass
            로그(f"셀 안쪽 여백 강제 축소 완료 (검사 {검사수}개 / 축소 적용 {적용수}개)")
            return True
        return bind_function(표_셀_안쪽여백_전체_적용, _docfit_namespace)
    if _docfit_symbol == '본문_가용너비_mm':
        def 본문_가용너비_mm():
            """현재 섹션 용지 폭에서 좌우 여백을 뺀 본문 가용 너비(mm)."""
            if hwp is None:
                return None
            try:
                act = hwp.HAction
                pset = hwp.HParameterSet.HSecDef
                act.GetDefault("PageSetup", pset.HSet)
                return HwpUnit_mm(
                    pset.PageDef.PaperWidth - pset.PageDef.LeftMargin - pset.PageDef.RightMargin
                )
            except Exception as e:
                로그(f"본문 가용 너비 확인 실패(무시): {e}")
                return None
        return bind_function(본문_가용너비_mm, _docfit_namespace)
    if _docfit_symbol == '표_전체너비_mm':
        def 표_전체너비_mm():
            """캐럿이 표 안 어딘가에 있을 때, 그 표 전체의 현재 너비(mm)."""
            if hwp is None:
                return None
            try:
                return HwpUnit_mm(hwp.CellShape.Item("Width"))
            except Exception as e:
                로그(f"표 전체 너비 확인 실패(무시): {e}")
                return None
        return bind_function(표_전체너비_mm, _docfit_namespace)
    if _docfit_symbol == '현재셀_너비_mm':
        def 현재셀_너비_mm():
            """캐럿이 있는 셀(표 안)의 현재 너비(mm)."""
            if hwp is None:
                return None
            try:
                pset = hwp.HParameterSet.HShapeObject
                hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
                return HwpUnit_mm(pset.ShapeTableCell.Width)
            except Exception as e:
                로그(f"셀 너비 확인 실패(무시): {e}")
                return None
        return bind_function(현재셀_너비_mm, _docfit_namespace)
    if _docfit_symbol == '표_열너비_순서대로_설정':
        def 표_열너비_순서대로_설정(목표_mm_목록):
            """캐럿이 표의 첫 행 첫 칸에 있다고 가정하고, 왼쪽 열부터 순서대로
            목표_mm_목록의 값으로 각 열 너비를 설정한다. 실제로 적용된 열 수를
            반환한다.

            열을 고르는 방식(TableColPageUp → TableCellBlock →
            TableCellBlockExtend → TableColPageDown으로 한 열 전체 선택 후
            ShapeCellSize=1로 너비 지정)은 사람이 Alt+방향키 대신 '표/셀 속성'
            대화상자를 여는 것과 같은 효과의 실제 한/글 액션 조합이다.
            """
            if hwp is None:
                return 0
            hwp_run('TableColBegin')
            적용수 = 0
            for 목표_mm in 목표_mm_목록:
                if 중단_요청됨():
                    break
                try:
                    hwp_run('TableColPageUp')
                    hwp_run('TableCellBlock')
                    hwp_run('TableCellBlockExtend')
                    hwp_run('TableColPageDown')
                    pset = hwp.HParameterSet.HShapeObject
                    hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
                    pset.HSet.SetItem("ShapeType", 3)
                    pset.HSet.SetItem("ShapeCellSize", 1)
                    pset.ShapeTableCell.Width = hwp.MiliToHwpUnit(목표_mm)
                    if hwp.HAction.Execute("TablePropertyDialog", pset.HSet) is not False:
                        적용수 += 1
                    hwp_run('Cancel')
                    hwp_run('TableRightCell')
                except Exception as e:
                    로그(f"열 너비 설정 실패(무시): {e}")
                    try:
                        hwp_run('Cancel')
                    except Exception:
                        pass
                    break
            return 적용수
        return bind_function(표_열너비_순서대로_설정, _docfit_namespace)
    if _docfit_symbol == '표_열너비_본문맞춤_시도':
        def 표_열너비_본문맞춤_시도(표_셀목록, 목표_전체너비_mm):
            """표 첫 행(칼럼별 대표 셀)의 현재 너비 비율을 유지한 채, 표 전체
            너비를 목표_전체너비_mm에 맞춰 각 열 너비를 비례 조정한다.

            첫 행이 병합돼 칼럼별 셀을 구분할 수 없거나(첫 행 셀이 1개뿐),
            이미 허용오차 안이면 건드리지 않는다.
            """
            if not 표_셀목록 or 목표_전체너비_mm is None or 목표_전체너비_mm <= 0:
                return False
            첫행_area = [area for area, _, 행 in 표_셀목록 if 행 == 1]
            if len(첫행_area) < 2:
                return False
            # 실측(2026-09-25): 첫 행이 병합된 표(연도 아래 분기 칸 등)는 첫 행 칸과 실제
            # 열이 맞지 않아 너비가 엉뚱한 열에 들어가 표가 용지 밖으로 넘쳤다(4쪽→7쪽).
            # 모든 행의 열 구성이 첫 행과 같은 격자형 표만 조정한다.
            행별_열 = {}
            for _, 컬럼, 행 in 표_셀목록:
                행별_열.setdefault(행, []).append(컬럼)
            첫행_열 = 행별_열.get(1, [])
            if any(열 != 첫행_열 for 열 in 행별_열.values()):
                진단로그("[셀 너비 본문 맞춤] 병합된 칸이 있는 표는 건너뜀")
                return False
            try:
                hwp.SetPos(첫행_area[0], 0, 0)
            except Exception:
                return False
            현재_전체너비 = 표_전체너비_mm()
            if 현재_전체너비 is None or 현재_전체너비 <= 0:
                return False
            if abs(현재_전체너비 - 목표_전체너비_mm) <= 표_열너비_허용오차_mm:
                return False
            현재_너비들 = []
            for area in 첫행_area:
                try:
                    hwp.SetPos(area, 0, 0)
                except Exception:
                    return False
                w = 현재셀_너비_mm()
                if w is None or w <= 0:
                    return False
                현재_너비들.append(w)
            비율합 = sum(현재_너비들)
            if 비율합 <= 0:
                return False
            목표_너비들 = [w / 비율합 * 목표_전체너비_mm for w in 현재_너비들]
            try:
                hwp.SetPos(첫행_area[0], 0, 0)
            except Exception:
                return False
            적용수 = 표_열너비_순서대로_설정(목표_너비들)
            return 적용수 == len(목표_너비들)
        return bind_function(표_열너비_본문맞춤_시도, _docfit_namespace)
    if _docfit_symbol == '표_열너비_본문맞춤_전체_적용':
        def 표_열너비_본문맞춤_전체_적용():
            if not 표_열너비_맞춤_사용:
                return True
            if 중단_요청됨():
                return False
            목표_mm = 본문_가용너비_mm()
            if 목표_mm is None or 목표_mm <= 0:
                로그("셀 너비 본문 맞춤 건너뜀: 본문 가용 너비 확인 실패")
                return True
            로그(f"셀 너비를 본문 여백({목표_mm:.1f}mm)에 맞추는 작업 시작")
            원위치 = hwp.GetPos()
            표들 = 표_목록_수집()
            적용표수 = 0
            for 표 in 표들:
                if 중단_요청됨():
                    return False
                if 표_열너비_본문맞춤_시도(표, 목표_mm):
                    적용표수 += 1
            try:
                hwp.SetPos(*원위치)
            except Exception:
                pass
            로그(f"셀 너비 본문 맞춤 완료 (표 {len(표들)}개 중 {적용표수}개 조정)")
            return True
        return bind_function(표_열너비_본문맞춤_전체_적용, _docfit_namespace)
    if _docfit_symbol == '표_셀_테두리_적용':
        def 표_셀_테두리_적용(위=None, 아래=None, 왼쪽=None, 오른쪽=None):
            """캐럿이 있는 셀에 지정된 방향의 테두리 선 종류/굵기를 적용한다.
            각 인자는 (HwpLineType 이름, HwpLineWidth 이름) 튜플이거나
            None(해당 방향은 건드리지 않음).
            """
            # 실측(2026-09-25): pset.SelCellsBorderFill 아래 항목에 값을 넣는 예전 방식은
            # 실행 결과가 True여도 테두리가 바뀌지 않았다. 셀을 블록으로 선택한 뒤
            # HCellBorderFill의 BorderType*/BorderWidth* 항목을 직접 넣어야 적용된다.
            # 'CellBorderFill' 액션은 셀 배경색까지 다시 적용해 머리글 배경이 지워졌으므로
            # 테두리만 바꾸는 'CellBorder' 액션을 쓴다.
            if hwp is None:
                return False
            try:
                hwp_run("TableCellBlock")
                pset = hwp.HParameterSet.HCellBorderFill
                hwp.HAction.GetDefault("CellBorder", pset.HSet)
                for 방향, 값 in (("Top", 위), ("Bottom", 아래), ("Left", 왼쪽), ("Right", 오른쪽)):
                    if 값 is None:
                        continue
                    종류, 굵기 = 값
                    setattr(pset, "BorderType" + 방향, hwp.HwpLineType(종류))
                    setattr(pset, "BorderWidth" + 방향, hwp.HwpLineWidth(굵기))
                return hwp.HAction.Execute("CellBorder", pset.HSet) is not False
            except Exception as e:
                로그(f"표 셀 테두리 적용 실패(무시): {e}")
                return False
            finally:
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
        return bind_function(표_셀_테두리_적용, _docfit_namespace)
    if _docfit_symbol == '표_테두리_삼선표_적용':
        def 표_테두리_삼선표_적용(표_셀목록):
            """표 하나(표_목록_수집이 모은 (area, 칼럼, 행번호) 목록)에 삼선표
            규칙을 적용한다: 위/아래 외곽선 0.5mm 실선, 헤더 아래 이중선 0.5mm,
            나머지 안쪽 구분선(가로/세로) 0.12mm 실선, 좌우 외곽선은 선 없음.
            """
            if not 표_셀목록:
                return 0
            마지막행 = max(행 for _, _, 행 in 표_셀목록)
            행별_첫area = {}
            행별_끝area = {}
            for area, _, 행 in 표_셀목록:
                if 행 not in 행별_첫area:
                    행별_첫area[행] = area
                행별_끝area[행] = area
            적용수 = 0
            for area, _, 행 in 표_셀목록:
                if 중단_요청됨():
                    break
                if 행 == 마지막행:
                    아래 = ("Solid", "0.5mm")
                elif 행 == 1:
                    아래 = ("DoubleSlim", "0.5mm")
                else:
                    아래 = ("Solid", "0.12mm")
                if 행 == 1:
                    위 = ("Solid", "0.5mm")
                elif 행 == 2:
                    위 = ("DoubleSlim", "0.5mm")
                else:
                    위 = ("Solid", "0.12mm")
                왼쪽 = ("None", "0.1mm") if area == 행별_첫area[행] else ("Solid", "0.12mm")
                오른쪽 = ("None", "0.1mm") if area == 행별_끝area[행] else ("Solid", "0.12mm")
                try:
                    hwp.SetPos(area, 0, 0)
                except Exception:
                    continue
                if 표_셀_테두리_적용(위=위, 아래=아래, 왼쪽=왼쪽, 오른쪽=오른쪽):
                    적용수 += 1
            return 적용수
        return bind_function(표_테두리_삼선표_적용, _docfit_namespace)
    if _docfit_symbol == '표_테두리_전체_적용':
        def 표_테두리_전체_적용():
            if not 표_테두리_통일_사용:
                return True
            if 중단_요청됨():
                return False
            로그("표 테두리 선 굵기 통일 시작")
            원위치 = hwp.GetPos()
            표들 = 표_목록_수집()
            총적용 = 0
            for 표 in 표들:
                if 중단_요청됨():
                    return False
                총적용 += 표_테두리_삼선표_적용(표)
            try:
                hwp.SetPos(*원위치)
            except Exception:
                pass
            로그(f"표 테두리 선 굵기 통일 완료 (표 {len(표들)}개 / 적용 셀 {총적용}개)")
            return True
        return bind_function(표_테두리_전체_적용, _docfit_namespace)
    if _docfit_symbol == '넓은_표칸_줄인가':
        def 넓은_표칸_줄인가():
            """현재 화면줄이 넓은 표 칸의 줄인지(글자 위치 기준 길이).

            실측: 한 줄 33자인 공고문 표 칸의 '신|뢰를' 등 3건이 표 한도(5단계)
            때문에 풀리지 않았다.
            """
            original = hwp.GetPos()
            try:
                start, end = 단어모드_줄범위(original)
                return end[2] - start[2] >= 넓은_표칸_기준글자수
            except Exception:
                return False
            finally:
                hwp.SetPos(*original)
        return bind_function(넓은_표칸_줄인가, _docfit_namespace)
    if _docfit_symbol == '컨트롤_내부_문장부호_처리':
        def 컨트롤_내부_문장부호_처리():
            한칸표영역 = 한칸표_영역_목록()
            area = 1
            while True:
                if 중단_요청됨():
                    return False
                area += 1
                hwp.SetPos(area, 0, 0)
                if hwp.GetPos()[0] == 0:
                    break
                if not 재검사_영역인가(area):
                    continue
                if area in 한칸표영역:
                    진단로그(f"[한 칸 표 제외] 영역 {area}: 문장부호 서식 보존")
                    continue
                if 숫자_표칸인가():
                    continue
                while True:
                    if 중단_요청됨():
                        return False
                    시작위치 = hwp.GetPos()
                    # 이 순회는 다음 영역까지 이어질 수 있어 줄마다 쪽 범위·표 제외 설정을 확인한다.
                    if 컨트롤_줄병합_대상인가():
                        문장부호_줄병합_시도()
                    hwp_run("MoveLineEnd")
                    줄끝 = hwp.GetPos()
                    hwp_run("MoveNextChar")
                    if hwp.GetPos()[0] != 0 and hwp.GetPos()[0] >= area:
                        area = hwp.GetPos()[0]
                    # 마지막 줄에서 MoveNextChar가 줄 끝에 머물면 같은 줄을 다시 처리하지 않는다.
                    if hwp.GetPos() in (시작위치, 줄끝):
                        break
            return True
        return bind_function(컨트롤_내부_문장부호_처리, _docfit_namespace)
    raise KeyError(_docfit_symbol)
