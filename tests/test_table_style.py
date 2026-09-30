"""기본 표 서식(준말 '표'의 본말): 예시 표 위치별 서식 학습·적용."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from docfit_core.table_style import (HeaderPool, apply_table_style, default_style, describe_style,
                                     is_grid_table, learn_table_style, valid_style)

HP_URI = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HP = f'xmlns:hp="{HP_URI}"'
HH = 'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"'
LANGS = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")


def _char(char_id, color="#000000", bold=False):
    zero = " ".join(f'{lang}="0"' for lang in LANGS)
    hundred = " ".join(f'{lang}="100"' for lang in LANGS)
    return (f'<hh:charPr id="{char_id}" height="1000" textColor="{color}" shadeColor="none" useFontSpace="0" '
            f'useKerning="0" symMark="NONE" borderFillIDRef="1"><hh:fontRef {zero}/><hh:ratio {hundred}/>'
            f'<hh:spacing {zero}/><hh:relSz {hundred}/><hh:offset {zero}/>' + ("<hh:bold/>" if bold else "")
            + '<hh:underline type="NONE" shape="SOLID" color="#000000"/><hh:strikeout shape="NONE" color="#000000"/>'
            '<hh:outline type="NONE"/><hh:shadow type="NONE" color="#B2B2B2" offsetX="10" offsetY="10"/></hh:charPr>')


def _header():
    sides = "".join(f'<hh:{side} type="SOLID" width="0.12 mm" color="#000000"/>'
                    for side in ("leftBorder", "rightBorder", "topBorder", "bottomBorder"))
    return ET.fromstring(
        f'<hh:head {HH}><hh:refList><hh:fontfaces itemCnt="7">'
        + "".join(f'<hh:fontface lang="{lang.upper()}" fontCnt="1"><hh:font id="0" face="바탕" type="TTF" '
                  f'isEmbedded="0"/></hh:fontface>' for lang in LANGS)
        + '</hh:fontfaces><hh:borderFills itemCnt="1"><hh:borderFill id="1" threeD="0" shadow="0" centerLine="NONE" '
        f'breakCellSeparateLine="0"><hh:slash type="NONE" Crooked="0" isCounter="0"/>'
        f'<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>{sides}'
        '<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/></hh:borderFill></hh:borderFills>'
        f'<hh:charProperties itemCnt="2">{_char(0)}{_char(1, "#FF0000", True)}</hh:charProperties>'
        '<hh:paraProperties itemCnt="1"><hh:paraPr id="0"><hh:align horizontal="LEFT" vertical="BASELINE"/>'
        '</hh:paraPr></hh:paraProperties></hh:refList></hh:head>')


def _cell(row, col, text="", rows=1, cols=1, char=0, width=10000):
    return (f'<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1">'
            f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="TOP">'
            f'<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="{char}"><hp:t>{text}</hp:t></hp:run>'
            f'<hp:linesegarray><hp:lineseg textpos="0"/></hp:linesegarray></hp:p></hp:subList>'
            f'<hp:cellAddr colAddr="{col}" rowAddr="{row}"/><hp:cellSpan colSpan="{cols}" rowSpan="{rows}"/>'
            f'<hp:cellSz width="{width * cols}" height="1000"/>'
            f'<hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>')


def _table_xml(rows, cols, cells):
    by_row = {}
    for row, xml in cells:
        by_row.setdefault(row, []).append(xml)
    body = "".join(f"<hp:tr>{''.join(by_row[r])}</hp:tr>" for r in sorted(by_row))
    return (f'<hp:tbl {HP} id="7" rowCnt="{rows}" colCnt="{cols}" borderFillIDRef="1">'
            f'<hp:sz width="{10000 * cols}" height="{1000 * rows}"/>'
            f'<hp:inMargin left="510" right="510" top="141" bottom="141"/>{body}</hp:tbl>')


def _grid(rows, cols, text=lambda r, c: f"{r}-{c}", char=lambda r, c: 0):
    return ET.fromstring(_table_xml(rows, cols, [(r, _cell(r, c, text(r, c), char=char(r, c)))
                                                   for r in range(rows) for c in range(cols)]))


def _tag(e):
    return e.tag.rsplit("}", 1)[-1]


class Reader:
    """적용 결과를 칸 위치로 읽는다."""

    def __init__(self, header, table):
        self.fills = {x.get("id"): x for x in header.iter() if _tag(x) == "borderFill"}
        self.chars = {x.get("id"): x for x in header.iter() if _tag(x) == "charPr"}
        self.paras = {x.get("id"): x for x in header.iter() if _tag(x) == "paraPr"}
        self.faces = {f.get("id"): f.get("face") for ff in header.iter()
                      if _tag(ff) == "fontface" and ff.get("lang") == "HANGUL" for f in ff}
        self.cells = {}
        for tc in (x for x in table.iter() if _tag(x) == "tc"):
            addr = next(x for x in tc if _tag(x) == "cellAddr")
            self.cells[(int(addr.get("rowAddr")), int(addr.get("colAddr")))] = tc

    def side(self, pos, side):
        fill = self.fills[self.cells[pos].get("borderFillIDRef")]
        return next(x for x in fill if _tag(x) == side).get("type")

    def face_color(self, pos):
        fill = self.fills[self.cells[pos].get("borderFillIDRef")]
        brush = next((x for x in fill.iter() if _tag(x) == "winBrush"), None)
        return brush.get("faceColor") if brush is not None else None

    def run_char(self, pos):
        run = next(x for x in self.cells[pos].iter() if _tag(x) == "run")
        return self.chars[run.get("charPrIDRef")]

    def font(self, pos):
        char = self.run_char(pos)
        ref = next(x for x in char if _tag(x) == "fontRef")
        return (self.faces[ref.get("hangul")], int(char.get("height")),
                any(_tag(x) == "bold" for x in char), char.get("textColor"))

    def align(self, pos):
        p = next(x for x in self.cells[pos].iter() if _tag(x) == "p")
        return next(x for x in self.paras[p.get("paraPrIDRef")].iter() if _tag(x) == "align").get("horizontal")

    def valign(self, pos):
        return next(x for x in self.cells[pos] if _tag(x) == "subList").get("vertAlign")


def _apply(table, style=None):
    header = _header()
    before = "".join(t.text or "" for t in table.iter() if _tag(t) == "t")
    apply_table_style(HeaderPool(header, style or default_style()), table)
    assert "".join(t.text or "" for t in table.iter() if _tag(t) == "t") == before   # 글은 그대로
    return header, Reader(header, table)


class DefaultStyleTest(unittest.TestCase):
    def test_default_style_is_the_learned_sample(self):
        style = default_style()
        self.assertTrue(valid_style(style))
        self.assertEqual((style["rows"], style["cols"], style["header_rows"]), (5, 3, 1))
        text = describe_style(style)
        self.assertIn("한컴돋움 13pt 굵게", text)
        self.assertIn("휴먼명조 12pt", text)

    def test_invalid_styles_are_rejected(self):
        style = default_style()
        for broken in ({}, {**style, "version": 99}, {**style, "grid": [[0]]}, {**style, "borders": {}}):
            self.assertFalse(valid_style(broken))


class ApplyTest(unittest.TestCase):
    def test_bigger_table_gets_style_by_position(self):
        table = _grid(5, 4)
        _, read = _apply(table)
        # 머리글 행: 바탕색, 아래 이중선, 바깥 왼쪽·오른쪽 선 없음, 한컴돋움 13pt 굵게, 가운데 정렬
        for col in range(4):
            self.assertEqual(read.face_color((0, col)), "#DFE6F7")
            self.assertEqual(read.side((0, col), "bottomBorder"), "DOUBLE_SLIM")
            self.assertEqual(read.font((0, col))[:3], ("한컴돋움", 1300, True))
            self.assertEqual(read.align((0, col)), "CENTER")
        self.assertEqual(read.side((0, 0), "leftBorder"), "NONE")
        self.assertEqual(read.side((0, 3), "rightBorder"), "NONE")
        self.assertEqual(read.side((0, 1), "leftBorder"), "SOLID")
        self.assertEqual(read.side((0, 2), "rightBorder"), "SOLID")
        # 첫 본문 행은 위 이중선, 본문은 바탕색 없음·휴먼명조 12pt, 첫 열은 배분 정렬
        self.assertEqual(read.side((1, 2), "topBorder"), "DOUBLE_SLIM")
        self.assertEqual(read.side((2, 2), "topBorder"), "SOLID")
        self.assertIsNone(read.face_color((3, 1)))
        self.assertEqual(read.font((3, 1))[:3], ("휴먼명조", 1200, False))
        self.assertEqual(read.align((3, 0)), "DISTRIBUTE")
        self.assertEqual(read.align((3, 2)), "CENTER")
        self.assertEqual(read.side((4, 0), "leftBorder"), "NONE")
        self.assertEqual(read.side((4, 3), "rightBorder"), "NONE")
        self.assertEqual(read.valign((2, 2)), "CENTER")
        self.assertFalse(any(_tag(x) == "linesegarray" for x in table.iter()))

    def test_long_body_text_keeps_its_alignment_but_header_is_aligned(self):
        long_text = "가" * 40
        table = _grid(3, 3, text=lambda r, c: long_text if (r, c) in ((0, 1), (2, 1)) else "짧은 글")
        _, read = _apply(table)
        self.assertEqual(read.align((2, 1)), "LEFT")     # 여러 줄 긴 글은 원래 정렬
        self.assertEqual(read.align((0, 1)), "CENTER")   # 머리글은 길어도 예시 정렬
        self.assertEqual(read.align((2, 2)), "CENTER")

    def test_body_emphasis_color_and_bold_are_kept(self):
        table = _grid(3, 3, char=lambda r, c: 1 if (r, c) == (2, 1) else 0)
        _, read = _apply(table)
        self.assertEqual(read.font((2, 1)), ("휴먼명조", 1200, True, "#FF0000"))

    def test_two_row_header_is_detected_from_row_spans(self):
        cells = [(0, _cell(0, 0, "구분", rows=2)), (0, _cell(0, 1, "2026", cols=2)),
                 (1, _cell(1, 1, "상반기")), (1, _cell(1, 2, "하반기"))]
        cells += [(r, _cell(r, c, f"{r}{c}")) for r in (2, 3) for c in range(3)]
        table = ET.fromstring(_table_xml(4, 3, cells))
        _, read = _apply(table)
        self.assertEqual(read.face_color((1, 2)), "#DFE6F7")
        self.assertEqual(read.side((1, 1), "bottomBorder"), "DOUBLE_SLIM")
        self.assertEqual(read.side((0, 0), "bottomBorder"), "DOUBLE_SLIM")   # 두 행에 걸친 머리글 칸
        self.assertEqual(read.side((2, 0), "topBorder"), "DOUBLE_SLIM")
        self.assertIsNone(read.face_color((2, 0)))

    def test_full_height_separator_column_is_not_a_header(self):
        cells = [(0, _cell(0, 0, "2025년")), (0, _cell(0, 1, "", rows=3)), (0, _cell(0, 2, "2026년"))]
        cells += [(r, _cell(r, c, "항목")) for r in (1, 2) for c in (0, 2)]
        table = ET.fromstring(_table_xml(3, 3, cells))
        _, read = _apply(table)
        self.assertEqual(read.face_color((0, 0)), "#DFE6F7")
        self.assertIsNone(read.face_color((0, 1)))
        self.assertEqual(read.side((1, 0), "topBorder"), "DOUBLE_SLIM")

    def test_repeated_tables_share_new_styles(self):
        header = _header()
        pool = HeaderPool(header, default_style())
        for _ in range(3):
            apply_table_style(pool, _grid(4, 3))
        fills = [x for x in header.iter() if _tag(x) == "borderFill"]
        self.assertLessEqual(len(fills), 1 + 10)   # 칸 위치 9종 + 표 테두리 1종만 더한다


class TargetTest(unittest.TestCase):
    def test_only_real_grid_tables_are_targets(self):
        self.assertTrue(is_grid_table(_grid(2, 2)))
        self.assertFalse(is_grid_table(_grid(1, 3)))
        self.assertFalse(is_grid_table(_grid(3, 1)))
        arrow = _grid(2, 3, text=lambda r, c: "⇨" if c == 1 else "단계")
        self.assertFalse(is_grid_table(arrow))            # 추진절차 흐름도
        nested = ET.fromstring(_table_xml(2, 2, [(r, _cell(r, c, "칸")) for r in range(2) for c in range(2)]))
        sub = next(x for x in nested.iter() if _tag(x) == "run")
        sub.append(_grid(2, 2))
        self.assertFalse(is_grid_table(nested))

    def test_titled_boxes_with_one_body_cell_are_not_targets(self):
        # '개선 필요사항' 탭 상자(2×2)와 '< 핵심 추진과제 >' 제목 상자(3×3): 본문 행이 전체 너비 한 칸이다.
        tab = ET.fromstring(_table_xml(2, 2, [(0, _cell(0, 0, "개선 필요사항")), (0, _cell(0, 1, "")),
                                              (1, _cell(1, 0, "☞ 설명", cols=2))]))
        titled = ET.fromstring(_table_xml(3, 3, [(0, _cell(0, 0, "")), (0, _cell(0, 1, "&lt; 핵심 추진과제 &gt;", rows=2)),
                                                 (0, _cell(0, 2, "")), (1, _cell(1, 0, "")), (1, _cell(1, 2, "")),
                                                 (2, _cell(2, 0, "▪ 내용", cols=3))]))
        self.assertFalse(is_grid_table(tab))
        self.assertFalse(is_grid_table(titled))
        # 머리글 아래 칸이 둘 이상인 본문 행이 하나라도 있으면 데이터 표다.
        mixed = ET.fromstring(_table_xml(3, 2, [(0, _cell(0, 0, "구분")), (0, _cell(0, 1, "내용")),
                                                (1, _cell(1, 0, "합계", cols=2)),
                                                (2, _cell(2, 0, "가")), (2, _cell(2, 1, "나"))]))
        self.assertTrue(is_grid_table(mixed))


class LearnTest(unittest.TestCase):
    def test_learning_a_styled_table_gives_the_same_style(self):
        table = _grid(5, 4)
        header, _ = _apply(table)
        folder = Path(tempfile.mkdtemp(prefix="docfit-table-style-"))
        path = folder / "예시.hwpx"
        section = ET.fromstring(f'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" {HP}>'
                                f'<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"/></hp:p></hs:sec>')
        next(x for x in section.iter() if _tag(x) == "run").append(table)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("mimetype", "application/hwp+zip")
            archive.writestr("Contents/header.xml", ET.tostring(header, encoding="utf-8"))
            archive.writestr("Contents/section0.xml", ET.tostring(section, encoding="utf-8"))
        learned = learn_table_style(path)
        self.assertTrue(valid_style(learned))
        self.assertEqual((learned["rows"], learned["cols"], learned["source"]), (5, 4, "예시.hwpx"))
        self.assertEqual(describe_style(learned).split(" 표, ")[1], describe_style(default_style()).split(" 표, ")[1])
        # 다시 배운 서식을 다른 표에 입혀도 같은 위치별 서식이 나온다.
        _, read = _apply(_grid(3, 3), learned)
        self.assertEqual(read.face_color((0, 1)), "#DFE6F7")
        self.assertEqual(read.side((0, 0), "leftBorder"), "NONE")
        self.assertEqual(read.align((2, 0)), "DISTRIBUTE")

    def test_document_without_grid_table_is_rejected(self):
        folder = Path(tempfile.mkdtemp(prefix="docfit-table-style-"))
        path = folder / "빈문서.hwpx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("Contents/header.xml", ET.tostring(_header(), encoding="utf-8"))
            archive.writestr("Contents/section0.xml",
                             f'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" {HP}/>')
        with self.assertRaises(ValueError):
            learn_table_style(path)


if __name__ == "__main__":
    unittest.main()
