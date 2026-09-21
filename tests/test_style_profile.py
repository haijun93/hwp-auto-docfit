from pathlib import Path
import runpy
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile


HEADER = '''<?xml version="1.0" encoding="UTF-8"?>
<hh:head xmlns:hh="urn:head">
  <hh:fontfaces><hh:fontface lang="HANGUL"><hh:font id="0" face="테스트명조" /></hh:fontface></hh:fontfaces>
  <hh:refList>
    <hh:charProperties>
      <hh:charPr id="0" height="1200"><hh:fontRef hangul="0"/><hh:ratio hangul="95"/><hh:spacing hangul="-2"/></hh:charPr>
      <hh:charPr id="1" height="1600"><hh:fontRef hangul="0"/><hh:ratio hangul="100"/><hh:bold/></hh:charPr>
    </hh:charProperties>
    <hh:borderFills itemCnt="1"><hh:borderFill id="0" threeD="0" shadow="0"/></hh:borderFills>
    <hh:tabProperties itemCnt="1"><hh:tabPr id="0" autoTabLeft="0" autoTabRight="0"/></hh:tabProperties>
    <hh:paraProperties>
      <hh:paraPr id="0"><hh:margin><hh:left value="0" unit="HWPUNIT"/></hh:margin><hh:lineSpacing type="PERCENT" value="170"/></hh:paraPr>
    </hh:paraProperties>
  </hh:refList>
</hh:head>'''.encode("utf-8")

SECTION = '''<?xml version="1.0" encoding="UTF-8"?>
<hs:sec xmlns:hs="urn:section" xmlns:hp="urn:para">
  <hp:secPr><hp:pagePr><hp:margin left="5102" right="5102" top="3600" bottom="3600" header="1800" footer="1800"/></hp:pagePr></hp:secPr>
  <hp:p paraPrIDRef="0"><hp:run charPrIDRef="1"><hp:t>문서 제목</hp:t></hp:run></hp:p>
  <hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>기호 없이 작성된 일반 본문입니다.</hp:t></hp:run></hp:p>
  <hp:p><hp:run><hp:tbl rowCnt="2" colCnt="1" borderFillIDRef="0"><hp:sz width="10000" height="4000"/><hp:tr><hp:tc borderFillIDRef="0" hasMargin="1"><hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/><hp:cellSz width="10000" height="2000"/><hp:cellMargin left="100" right="100" top="50" bottom="50"/><hp:subList vertAlign="CENTER"><hp:p paraPrIDRef="0"><hp:run charPrIDRef="1"><hp:t>구분</hp:t></hp:run></hp:p></hp:subList></hp:tc></hp:tr><hp:tr><hp:tc borderFillIDRef="0"><hp:cellAddr colAddr="0" rowAddr="1"/><hp:cellSpan colSpan="1" rowSpan="1"/><hp:cellSz width="10000" height="2000"/><hp:cellMargin left="100" right="100" top="50" bottom="50"/><hp:subList vertAlign="CENTER"><hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>내용</hp:t></hp:run></hp:p></hp:subList></hp:tc></hp:tr></hp:tbl></hp:run></hp:p>
</hs:sec>'''.encode("utf-8")

TABLE_ONLY_SECTION = SECTION.replace(
    b'<hp:p paraPrIDRef="0"><hp:run charPrIDRef="1"><hp:t>\xeb\xac\xb8\xec\x84\x9c \xec\xa0\x9c\xeb\xaa\xa9</hp:t></hp:run></hp:p>\n  '
    b'<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>\xea\xb8\xb0\xed\x98\xb8 \xec\x97\x86\xec\x9d\xb4 \xec\x9e\x91\xec\x84\xb1\xeb\x90\x9c \xec\x9d\xbc\xeb\xb0\x98 \xeb\xb3\xb8\xeb\xac\xb8\xec\x9e\x85\xeb\x8b\x88\xeb\x8b\xa4.</hp:t></hp:run></hp:p>\n  ',
    b'',
)


class StyleProfileTest(unittest.TestCase):
    def test_table_only_document_uses_table_body_as_body_style(self):
        namespace = runpy.run_path(
            str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
            run_name="table_only_style_profile_test",
        )
        analyze = namespace["hwpx_서식_분석"]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "table-only.hwpx"
            with ZipFile(source, "w", ZIP_DEFLATED) as archive:
                archive.writestr("Contents/header.xml", HEADER)
                archive.writestr("Contents/section0.xml", TABLE_ONLY_SECTION)
            profile = analyze(source)

        self.assertEqual(profile["source"]["paragraphs_analyzed"], 0)
        self.assertEqual(profile["source"]["body_style_fallback"], "표 본문 셀")
        self.assertEqual(profile["format"]["본문_문단"]["size_pt"], 12)
        self.assertEqual(len(profile["precise_tables"]["tables"]), 1)

    def test_plain_document_without_symbols_can_be_profile(self):
        namespace = runpy.run_path(
            str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
            run_name="style_profile_test",
        )
        analyze = namespace["hwpx_서식_분석"]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sample.hwpx"
            with ZipFile(source, "w", ZIP_DEFLATED) as archive:
                archive.writestr("Contents/header.xml", HEADER)
                archive.writestr("Contents/section0.xml", SECTION)
            profile = analyze(source)

        self.assertEqual(profile["profile_version"], 4)
        self.assertEqual(profile["format"]["기본_장평"], 95)
        self.assertEqual(profile["format"]["기본_줄간격_퍼센트"], 170)
        self.assertEqual(profile["format"]["제목_문단"]["font"], "테스트명조")
        self.assertEqual(profile["table_format"]["header_size"], 16)
        self.assertEqual(profile["table_format"]["body_size"], 12)
        self.assertEqual(len(profile["precise_tables"]["tables"]), 1)
        self.assertEqual(profile["precise_tables"]["tables"][0]["rows"], 2)

    def test_copied_profile_contains_logical_marker_rules(self):
        namespace = runpy.run_path(
            str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
            run_name="logical_style_test",
        )
        section = SECTION.replace("문서 제목".encode(), "□ 사업".encode()).replace(
            "기호 없이 작성된 일반 본문입니다.".encode(), "ㅇ 추진 내용".encode())
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "logical.hwpx"
            with ZipFile(source, "w", ZIP_DEFLATED) as archive:
                archive.writestr("Contents/header.xml", HEADER)
                archive.writestr("Contents/section0.xml", section)
            profile = namespace["hwpx_서식_분석"](source)
        hierarchy = profile["style_hierarchy"]
        self.assertEqual(hierarchy["role_sequence"], ["소제목", "본문"])
        self.assertEqual(profile["format"]["논리역할_규칙"]["소제목"][0], "□")
        self.assertTrue(profile["format"]["복제_들여쓰기_유지"])

    def test_precise_table_style_preserves_text_and_copies_geometry(self):
        namespace = runpy.run_path(
            str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
            run_name="precise_table_test",
        )
        analyze = namespace["hwpx_서식_분석"]
        apply_style = namespace["정밀표_서식_적용"]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sample.hwpx"
            input_target = Path(folder) / "input.hwpx"
            target = Path(folder) / "result.hwpx"
            with ZipFile(source, "w", ZIP_DEFLATED) as archive:
                archive.writestr("Contents/header.xml", HEADER)
                archive.writestr("Contents/section0.xml", SECTION)
            with ZipFile(input_target, "w", ZIP_DEFLATED) as archive:
                archive.writestr("Contents/header.xml", HEADER)
                archive.writestr("Contents/section0.xml", SECTION.replace(b'width="10000"', b'width="5000"'))
            profile = analyze(source)
            result = apply_style(input_target, target, profile["precise_tables"])
            with ZipFile(target) as archive:
                section = archive.read("Contents/section0.xml").decode("utf-8")

        self.assertEqual(result["applied"], 1)
        self.assertTrue(result["matches"][0]["geometry"])
        self.assertIn("구분", section)
        self.assertIn("내용", section)
        self.assertIn('width="10000"', section)


if __name__ == "__main__":
    unittest.main()
