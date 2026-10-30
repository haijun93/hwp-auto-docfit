"""표 템플릿 추가 서식(2.0.5): 공공기관 보고서에 자주 쓰는 표를 디자인 유형별로 만든다.

사용자가 고쳐 쓰는 '표 서식모음.hwpx'와 따로, 앱에 내장한 '표 서식모음 추가.hwpx'에 넣는다. 템플릿 id 앞에
GALLERY_PREFIX를 붙여 기존 서식(사용자 파일 포함)과 섞이지 않게 한다.

종류(정부·지자체 보고서·계획서·검토서 조사)와 디자인 유형(한컴 표 마당·MS 표 스타일·미리캔버스 등 상용 서비스 조사)을
조합한다. 디자인은 공문서에 어울리는 차분한 색만 쓴다.
- 청색 머리글: 머리글 칸에 연한 청색 바탕, 바깥선 굵게(가장 흔한 공문서 표)
- 선 강조(미니멀): 위·아래 굵은 선과 머리글 아래 선만, 세로선 없음(학술·통계표)
- 진한 머리글 줄무늬: 진한 회청색 머리글에 흰 글자, 본문 줄무늬(가독성 높은 현황표)
- 첫 열 강조: 머리글과 첫 열에 연한 녹색 바탕(항목·내용형)
- 합계 강조: 연한 주황 머리글, 마지막 합계 행을 굵게·노란 바탕(실적·예산표)
행(정보 단위)은 본문 한 줄, 열 단위가 있는 표는 같은 성격의 열(연도·월·대안)이다. 합계 행·열은 단위에 넣지 않는다.
"""
from __future__ import annotations

import copy
import io
import re
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from .batch_format import _serialize
from .hwpx import open_hwpx_safely
from .table_builder import _Header, _cell, _child, _element, _table, _tag

GALLERY_PREFIX = "g"
GALLERY_NAME = "표 서식모음 추가.hwpx"
ROW_HEIGHT = 1984  # 7mm

_THIN = ("SOLID", "0.12 mm", "#000000")
_NONE = ("NONE", "0.1 mm", "#000000")

THEMES = {
    "blue": {"label": "청색 머리글", "head_fill": "#DCE6F2", "head_color": "#000000", "outer": ("SOLID", "0.4 mm", "#000000"),
             "inner": _THIN, "head_line": ("DOUBLE_SLIM", "0.5 mm", "#000000"), "vertical": True},
    "minimal": {"label": "선 강조", "head_fill": "", "head_color": "#000000", "outer": ("SOLID", "0.5 mm", "#1F2937"),
                "inner": ("SOLID", "0.12 mm", "#9CA3AF"), "head_line": ("SOLID", "0.3 mm", "#1F2937"), "vertical": False},
    "stripe": {"label": "진한 머리글 줄무늬", "head_fill": "#44546A", "head_color": "#FFFFFF", "outer": ("SOLID", "0.25 mm", "#44546A"),
               "inner": ("SOLID", "0.12 mm", "#BFC6D1"), "head_line": ("SOLID", "0.25 mm", "#44546A"), "vertical": True,
               "zebra": "#F2F4F7"},
    "green": {"label": "첫 열 강조", "head_fill": "#E2EFDA", "head_color": "#000000", "outer": ("SOLID", "0.4 mm", "#375623"),
              "inner": ("SOLID", "0.12 mm", "#7F7F7F"), "head_line": ("SOLID", "0.4 mm", "#375623"), "vertical": True,
              "first_fill": "#F2F8EE"},
    "total": {"label": "합계 강조", "head_fill": "#FCE4D6", "head_color": "#000000", "outer": ("SOLID", "0.4 mm", "#000000"),
              "inner": _THIN, "head_line": ("SOLID", "0.4 mm", "#000000"), "vertical": True, "total_fill": "#FFF2CC"},
}

# (종류, 열[(머리글, 폭 비율, 정렬)], 본문 행, 끝 행(합계 등, 단위 밖), 열 단위(시작 열, 개수) 또는 None, 디자인들)
_L, _C = "left", "center"
DEFINITIONS = [
    ("사업개요표", [("구 분", 22, _C), ("내 용", 78, _L)],
     [["사 업 명", "○○○ 사업"], ["사업기간", "2026. 1. ~ 2026. 12."], ["사 업 비", "000백만원(국비 00, 시비 00, 구비 00)"],
      ["사업내용", "○○○ 설치 및 운영"], ["추진부서", "○○과 ○○팀"]], [], None, ("green", "blue", "minimal")),
    ("추진실적표", [("구 분", 22, _C), ("목 표", 18, _C), ("실 적", 18, _C), ("달성률(%)", 18, _C), ("비 고", 24, _C)],
     [["○○ 사업", "100", "95", "95.0", ""], ["△△ 사업", "50", "52", "104.0", ""], ["□□ 사업", "30", "24", "80.0", ""]],
     [["합 계", "180", "171", "95.0", ""]], None, ("total", "blue", "stripe")),
    ("예산집행표", [("구 분", 24, _C), ("예산액", 19, _C), ("집행액", 19, _C), ("잔 액", 19, _C), ("집행률(%)", 19, _C)],
     [["인 건 비", "000", "000", "000", "00.0"], ["운 영 비", "000", "000", "000", "00.0"], ["사 업 비", "000", "000", "000", "00.0"]],
     [["계", "000", "000", "000", "00.0"]], None, ("total", "minimal", "blue")),
    ("연도별 추진계획표", [("사 업 명", 28, _C), ("2026년", 18, _C), ("2027년", 18, _C), ("2028년", 18, _C), ("비 고", 18, _C)],
     [["○○ 사업", "기본계획 수립", "시범 운영", "전면 확대", ""], ["△△ 사업", "실태 조사", "설계", "준공", ""]],
     [], (1, 3), ("blue", "stripe", "minimal")),
    ("월별 실적표", [("구 분", 16, _C), ("1월", 12, _C), ("2월", 12, _C), ("3월", 12, _C), ("4월", 12, _C), ("5월", 12, _C),
                ("6월", 12, _C), ("계", 12, _C)],
     [["○○ 건수", "0", "0", "0", "0", "0", "0", "0"], ["△△ 건수", "0", "0", "0", "0", "0", "0", "0"]],
     [["합 계", "0", "0", "0", "0", "0", "0", "0"]], (1, 6), ("total", "stripe")),
    ("문제점·개선방안표", [("구 분", 16, _C), ("현황 및 문제점", 42, _L), ("개선 방안", 42, _L)],
     [["제 도", "○ 관련 규정 미비로 …", "○ 조례 개정으로 …"], ["운 영", "○ 전담 인력 부족으로 …", "○ 전담팀 신설 …"],
      ["시 설", "○ 노후 시설 증가 …", "○ 단계별 정비 …"]], [], None, ("green", "blue", "minimal")),
    ("대안비교표", [("구 분", 16, _C), ("1안", 28, _L), ("2안", 28, _L), ("3안", 28, _L)],
     [["내 용", "○ …", "○ …", "○ …"], ["장 점", "○ …", "○ …", "○ …"], ["단 점", "○ …", "○ …", "○ …"],
      ["소요예산", "00백만원", "00백만원", "00백만원"]], [], (1, 3), ("green", "blue", "stripe")),
    ("업무분장표", [("담 당", 16, _C), ("성 명", 14, _C), ("직 급", 14, _C), ("담당 업무", 40, _L), ("연락처", 16, _C)],
     [["팀 장", "홍길동", "행정6급", "○ 업무 총괄", "0000"], ["주무관", "김○○", "행정7급", "○ ○○ 사업 추진", "0000"],
      ["주무관", "이○○", "행정8급", "○ 예산·회계", "0000"]], [], None, ("blue", "stripe", "minimal")),
    ("성과지표표", [("성과지표", 28, _C), ("측정 방법", 34, _L), ("목표치", 19, _C), ("가중치(%)", 19, _C)],
     [["○○ 참여율", "참여 인원 ÷ 대상 인원 × 100", "80%", "40"], ["만족도", "참여자 설문(5점 척도)", "4.0점", "30"],
      ["△△ 건수", "연간 처리 건수", "100건", "30"]], [], None, ("blue", "green")),
    ("점검표(체크리스트)", [("번호", 10, _C), ("점검 항목", 50, _L), ("적합", 10, _C), ("부적합", 10, _C), ("비 고", 20, _C)],
     [["1", "○○ 설치 상태는 양호한가?", "□", "□", ""], ["2", "안전 수칙을 게시하였는가?", "□", "□", ""],
      ["3", "비상 연락망을 갖추었는가?", "□", "□", ""]], [], None, ("minimal", "blue", "green")),
    ("참석자 명단", [("연번", 10, _C), ("소 속", 30, _C), ("직 위", 18, _C), ("성 명", 20, _C), ("서 명", 22, _C)],
     [["1", "○○과", "과장", "", ""], ["2", "○○과", "팀장", "", ""], ["3", "○○과", "주무관", "", ""]], [], None,
     ("blue", "minimal")),
    ("민원처리 현황표", [("구 분", 22, _C), ("접 수", 15, _C), ("처리 완료", 15, _C), ("처리 중", 15, _C), ("처리율(%)", 15, _C),
                   ("비 고", 18, _C)],
     [["○○ 민원", "0", "0", "0", "0.0", ""], ["△△ 민원", "0", "0", "0", "0.0", ""]],
     [["계", "0", "0", "0", "0.0", ""]], None, ("total", "stripe")),
    ("비상연락망", [("구 분", 18, _C), ("성 명", 16, _C), ("직 위", 16, _C), ("사무실", 25, _C), ("휴대전화", 25, _C)],
     [["총 괄", "", "과장", "02-000-0000", "010-0000-0000"], ["실 무", "", "팀장", "02-000-0000", "010-0000-0000"],
      ["지 원", "", "주무관", "02-000-0000", "010-0000-0000"]], [], None, ("stripe", "blue")),
    ("위원 명단", [("연번", 10, _C), ("구 분", 16, _C), ("성 명", 16, _C), ("소속 및 직위", 40, _C), ("비 고", 18, _C)],
     [["1", "위원장", "", "○○대학교 교수", ""], ["2", "위 원", "", "○○연구원 연구위원", ""], ["3", "위 원", "", "○○구 ○○국장", "당연직"]],
     [], None, ("blue", "minimal")),
    ("추진경과표", [("일 자", 20, _C), ("주요 내용", 62, _L), ("비 고", 18, _C)],
     [["2026. 1. 00.", "○○ 기본계획 수립", ""], ["2026. 3. 00.", "관계기관 협의", ""], ["2026. 5. 00.", "사업 착수", ""]],
     [], None, ("minimal", "green", "blue")),
    ("SWOT 분석표", [("구 분", 16, _C), ("내 용", 84, _L)],
     [["강점(S)", "○ …"], ["약점(W)", "○ …"], ["기회(O)", "○ …"], ["위협(T)", "○ …"]], [], None, ("green", "stripe")),
    # 새 종류는 끝에 더한다(앞 종류의 id·그림 지문이 바뀌지 않게).
    ("평가표(심사표)", [("평가 항목", 22, _C), ("배 점", 12, _C), ("평가 기준", 50, _L), ("점 수", 16, _C)],
     [["사업 계획", "30", "○ 목표의 명확성·실현 가능성", ""], ["추진 역량", "40", "○ 인력·경험·조직 역량", ""],
      ["기대 효과", "30", "○ 파급 효과 및 지속 가능성", ""]], [["총 점", "100", "", ""]], None, ("total", "blue")),
    ("인력 현황표", [("구 분", 24, _C), ("정 원", 16, _C), ("현 원", 16, _C), ("과부족", 16, _C), ("비 고", 28, _C)],
     [["○○과", "00", "00", "0", ""], ["△△과", "00", "00", "0", ""], ["□□과", "00", "00", "0", ""]],
     [["계", "00", "00", "0", ""]], None, ("stripe", "total")),
]


def gallery_templates():
    """[(종류 이름, 모양 번호, 정의, 디자인 이름)] — 카탈로그 읽기와 같은 이름 규칙('종류 · 모양 N')."""
    result = []
    for category, columns, body, tail, col_unit, themes in DEFINITIONS:
        for number, theme in enumerate(themes, 1):
            result.append((category, number, (columns, body, tail, col_unit), theme))
    return result


_TRAILING = {"비고", "계", "합계"}
MIN_UNIT_MM = 15   # 열을 늘려도 단위 열 하나가 이 폭(본문 170mm 기준)보다 좁아지지 않게 상한을 정한다


def column_unit(columns, col_unit=None):
    """열 정보단위 (시작 열, 개수). 정한 것이 없으면 첫 열(구분·번호)과 끝의 비고·계 열을 뺀 가운데 열 모두."""
    if col_unit:
        return col_unit
    end = len(columns) - 1 if len(columns) > 2 and columns[-1][0].replace(" ", "") in _TRAILING else len(columns)
    return (1, max(1, end - 1))


def gallery_plans():
    """이름별 정보단위 판정표 재료: {이름: (행 단위(start, core, count), 열 단위(start, core, count))}.

    2.0.6부터 모든 추가 서식이 열 단위도 늘리고 줄인다(사용자 요청)."""
    plans = {}
    for category, number, (columns, body, tail, col_unit), _ in gallery_templates():
        start, count = column_unit(columns, col_unit)
        plans[f"{category} · 모양 {number}"] = ((1, 1, len(body)), (start, 1, count))
    return plans


def gallery_col_caps():
    """열 단위 상한: 단위 열 폭 합(본문 170mm 비율)을 MIN_UNIT_MM로 나눈 값(지금 개수보다 작지 않게, 최대 15)."""
    caps = {}
    for category, number, (columns, body, tail, col_unit), _ in gallery_templates():
        start, count = column_unit(columns, col_unit)
        share = sum(c[1] for c in columns[start:start + count]) / sum(c[1] for c in columns)
        caps[(f"{category} · 모양 {number}", "col")] = max(count, min(15, int(170 * share // MIN_UNIT_MM)))
    return caps


def _para(pool, horizontal):
    key = "_para_" + horizontal
    if not hasattr(pool, key):
        source = next(x for x in pool.groups["paraProperties"] if x.get("id") == "0")
        clone = copy.deepcopy(source)
        align = _child(clone, "align")
        if align is not None:
            align.set("horizontal", "CENTER" if horizontal == _C else "LEFT")
        for line in (x for x in clone.iter() if _tag(x) == "lineSpacing"):
            if line.get("type") == "PERCENT":
                line.set("value", "130")
        setattr(pool, key, pool._append("paraProperties", clone))
    return getattr(pool, key)


def _build_table(run, pool, body_width, columns, body, tail, theme):
    t = THEMES[theme]
    rows = [[c[0] for c in columns]] + body + tail
    n_rows, n_cols = len(rows), len(columns)
    total_ratio = sum(c[1] for c in columns)
    widths = [body_width * c[1] // total_ratio for c in columns]
    widths[-1] += body_width - sum(widths)
    head_char = pool.char({"font": "한컴돋움", "size": 12, "bold": True, "color": t["head_color"]})
    first_char = pool.char({"font": "한컴돋움", "size": 12, "bold": True, "color": "#000000"})
    body_char = pool.char({"font": "휴먼명조", "size": 12, "bold": False, "color": "#000000"})
    tail_char = pool.char({"font": "한컴돋움", "size": 12, "bold": True, "color": "#000000"})
    table = _table(run, n_rows, n_cols, body_width, ROW_HEIGHT * n_rows, pool.border({}))
    last_body = len(body)  # 본문 마지막 행 번호(머리글이 0행)
    for r, values in enumerate(rows):
        tr = _element(table, "tr")
        is_head, is_tail = r == 0, r > last_body
        for c, value in enumerate(values):
            inner_v = t["inner"] if t["vertical"] else _NONE
            sides = {
                "top": t["outer"] if r == 0 else (t["head_line"] if r == 1 else
                                                   (t["head_line"] if is_tail and r == last_body + 1 else t["inner"])),
                "bottom": t["outer"] if r == n_rows - 1 else (t["head_line"] if r == 0 else t["inner"]),
                "left": (t["outer"] if t["vertical"] else _NONE) if c == 0 else inner_v,
                "right": (t["outer"] if t["vertical"] else _NONE) if c == n_cols - 1 else inner_v,
            }
            fill = ""
            if is_head:
                fill = t["head_fill"]
            elif is_tail and t.get("total_fill"):
                fill = t["total_fill"]
            elif c == 0 and t.get("first_fill"):
                fill = t["first_fill"]
            elif t.get("zebra") and not is_tail and r % 2 == 0:
                fill = t["zebra"]
            char = head_char if is_head else tail_char if is_tail else first_char if c == 0 else body_char
            align = _C if is_head or is_tail else columns[c][2]
            _cell(tr, col=c, row=r, width=widths[c], height=ROW_HEIGHT, border=pool.border(sides, fill),
                  para=_para(pool, align), char=char, text=value, header=is_head)
    return table


def build_gallery(base_path, target_path):
    """base_path(앱 내장 표 서식모음, 쪽 설정·글꼴 목록)를 바탕으로 추가 서식 HWPX를 만든다."""
    with open_hwpx_safely(base_path) as z:
        contents = {info.filename: z.read(info.filename) for info in z.infolist()}
    sections = sorted(n for n in contents if re.fullmatch(r"Contents/section\d+\.xml", n))
    header_bytes, section_bytes = contents["Contents/header.xml"], contents[sections[0]]
    header, section = ET.fromstring(header_bytes), ET.fromstring(section_bytes)
    pool = _Header(header)
    page = next(x for x in section.iter() if _tag(x) == "pagePr")
    margin = _child(page, "margin")
    body_width = int(page.get("width")) - int(margin.get("left")) - int(margin.get("right"))
    paragraphs = [p for p in section if _tag(p) == "p"]
    first = paragraphs[0]
    for p in paragraphs[1:]:
        section.remove(p)
    for child in list(first):
        if _tag(child) == "run":
            for item in list(child):
                if _tag(item) not in ("secPr", "ctrl"):
                    child.remove(item)
            if not len(child):
                first.remove(child)
        elif _tag(child) == "linesegarray":
            first.remove(child)
    label_char = pool.char({"font": "한컴돋움", "size": 11, "bold": True, "color": "#000000"})
    current = None
    for category, number, (columns, body, tail, _), theme in gallery_templates():
        if category != current:
            current = category
            title = _element(section, "p", id=0, paraPrIDRef=0, styleIDRef=0, pageBreak=0, columnBreak=0, merged=0)
            _element(_element(title, "run", charPrIDRef=label_char), "t").text = "#" + category
        note = _element(section, "p", id=0, paraPrIDRef=0, styleIDRef=0, pageBreak=0, columnBreak=0, merged=0)
        _element(_element(note, "run", charPrIDRef=0), "t").text = f"모양 {number}: {THEMES[theme]['label']}"
        holder = _element(section, "p", id=0, paraPrIDRef=_para(pool, _C), styleIDRef=0, pageBreak=0,
                          columnBreak=0, merged=0)
        run = _element(holder, "run", charPrIDRef=0)
        _build_table(run, pool, body_width, columns, body, tail, theme)
        _element(run, "t")
    contents["Contents/header.xml"] = _serialize(header, header_bytes)
    contents[sections[0]] = _serialize(section, section_bytes)
    for extra in sections[1:]:
        contents.pop(extra)
    if "Preview/PrvText.txt" in contents:
        contents["Preview/PrvText.txt"] = "표 서식모음 추가".encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as out:
        if "mimetype" in contents:
            out.writestr("mimetype", contents.pop("mimetype"), compress_type=zipfile.ZIP_STORED)
        for name, data in contents.items():
            out.writestr(name, data)
    Path(target_path).write_bytes(buffer.getvalue())
    return Path(target_path)
