"""표 서식통일 판정(한/글 호출 없음).

공문서에는 제목 상자(1칸 표), 자료 표, 항목·내용 표처럼 여러 종류의 표가 섞인다. 표의
종류를 억지로 하나로 맞추지 않고, **모양(테두리·배경)이 같은 칸은 같은 역할**이라는 원칙으로
비교 대상을 정한다.

- 제목 상자: 같은 문두기호 계열(Ⅰ, 󰊱 …) 또는 같은 상자 모양끼리 글꼴·크기·굵기·글자색을 맞춘다.
- 여러 칸 표 안: 같은 역할(머리글 행 여부 + 칸 모양) 칸의 80% 이상이 쓰는 글꼴·크기·굵기와
  다른 칸만 고친다. 글자 크기는 더 큰 칸만 줄인다(작은 칸은 칸에 맞추려 줄였을 수 있다).
  표 안 글자색은 증감 표시 등 의미가 있어 건드리지 않는다.
- 여러 표 사이: 같은 모양 칸의 글꼴만 문서 대표값(표 60% 이상)으로 맞춘다. 크기는 표마다
  칸 폭에 맞춰 다를 수 있으므로 표 사이에서는 맞추지 않는다.

입력 표 모델:
    {"index": 문서 순번, "box": 1칸 표 여부, "marker": 첫 글자 문두기호 그룹,
     "cells": [{"area": 한/글 목록 번호, "header": 머리글 행 여부, "fill": 칸 모양 번호,
                "paras": [{"index": 문단 번호, "text": 글자,
                           "runs": [(시작, 끝, 글꼴, 크기, 글자색, 굵게), ...]}]}]}
"""

from __future__ import annotations

from collections import Counter, defaultdict

from docfit_core.style_unify import dominant, representative

FIELDS = ("font", "size", "color", "bold")
_RUN_INDEX = {"font": 2, "size": 3, "color": 4, "bold": 5}


def cell_value(cell, field):
    """칸 글자 대부분(60% 이상)이 쓰는 값. 비어 있거나 갈리면 None."""
    index = _RUN_INDEX[field]
    return dominant(((run[index], run[1] - run[0])
                     for para in cell["paras"] for run in para["runs"]), ratio=0.6)


def _fix_runs(cell, field, wrong, right, reason, fixes):
    for para in cell["paras"]:
        for run in para["runs"]:
            if run[_RUN_INDEX[field]] == wrong and run[1] > run[0]:
                fixes.append({"area": cell["area"], "para": para["index"], "text": para["text"],
                              "start": run[0], "end": run[1], "field": field,
                              "value": right, "was": wrong, "reason": reason})


def _text_cells(table):
    return [cell for cell in table["cells"]
            if any(run[1] > run[0] for para in cell["paras"] for run in para["runs"])]


def plan_table_fixes(tables, *, consensus=0.8, minimum_cells=4, minimum_tables=3,
                     table_ratio=0.6):
    """고칠 글자 구간 목록과 요약을 돌려준다: (fixes, summary)."""
    fixes = []
    summary = Counter()

    # 1) 제목 상자: 같은 기호 계열 또는 같은 상자 모양끼리. 한 문단짜리 상자만 비교한다.
    boxes = defaultdict(list)
    for table in tables:
        cells = _text_cells(table)
        if not table.get("box") or len(cells) != 1:
            continue
        cell = cells[0]
        if sum(1 for para in cell["paras"] if para["runs"]) != 1:
            continue
        key = ("기호", table["marker"]) if table.get("marker") else ("모양", cell["fill"])
        boxes[key].append(cell)
    for key, cells in boxes.items():
        if len(cells) < 2:
            continue
        for field in FIELDS:
            values = [cell_value(cell, field) for cell in cells]
            value, _, _ = representative(values, minimum=max(2, min(3, len(cells))), ratio=0.6)
            if value is None:
                continue
            for cell, current in zip(cells, values):
                if current is not None and current != value:
                    _fix_runs(cell, field, current, value, f"제목 상자({key[1] or '같은 모양'})", fixes)
                    summary["제목 상자"] += 1

    # 2) 여러 칸 표 안: 같은 역할(머리글 행 여부 + 칸 모양) 칸끼리.
    grids = [table for table in tables if not table.get("box")]
    for table in grids:
        roles = defaultdict(list)
        for cell in _text_cells(table):
            roles[(cell["header"], cell["fill"])].append(cell)
        for (header, _), cells in roles.items():
            if len(cells) < minimum_cells:
                continue
            for field in ("font", "size", "bold"):
                values = [cell_value(cell, field) for cell in cells]
                value, _, _ = representative(values, minimum=minimum_cells, ratio=consensus)
                if value is None:
                    continue
                for cell, current in zip(cells, values):
                    if current is None or current == value:
                        continue
                    if field == "size" and current < value:
                        continue   # 칸에 맞추려 줄인 글자일 수 있다.
                    _fix_runs(cell, field, current, value,
                              f"표 {table['index'] + 1} {'머리글' if header else '본문'} 칸", fixes)
                    summary["표 안"] += 1

    # 3) 여러 표 사이: 같은 모양 칸의 글꼴만 문서 대표값으로.
    by_role = defaultdict(list)
    for table in grids:
        roles = defaultdict(list)
        for cell in _text_cells(table):
            roles[(cell["header"], cell["fill"])].append(cell)
        for role, cells in roles.items():
            font = dominant(((cell_value(cell, "font"), 1) for cell in cells), ratio=0.6)
            if font is not None:
                by_role[role].append((table, cells, font))
    for role, entries in by_role.items():
        if len(entries) < minimum_tables:
            continue
        value, _, _ = representative([font for _, _, font in entries],
                                     minimum=minimum_tables, ratio=table_ratio)
        if value is None:
            continue
        for table, cells, font in entries:
            if font == value:
                continue
            for cell in cells:
                if cell_value(cell, "font") == font:
                    _fix_runs(cell, "font", font, value,
                              f"표 {table['index'] + 1}의 글꼴을 같은 모양 표들과 맞춤", fixes)
            summary["표 사이"] += 1

    # 같은 구간에 같은 항목을 두 번 적용하지 않는다.
    unique = {}
    for fix in fixes:
        unique.setdefault((fix["area"], fix["para"], fix["start"], fix["end"], fix["field"]), fix)
    return list(unique.values()), dict(summary)
