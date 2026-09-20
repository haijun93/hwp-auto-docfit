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
  <hp:p><hp:run><hp:tbl><hp:tr><hp:tc><hp:p paraPrIDRef="0"><hp:run charPrIDRef="1"><hp:t>구분</hp:t></hp:run></hp:p></hp:tc></hp:tr><hp:tr><hp:tc><hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>내용</hp:t></hp:run></hp:p></hp:tc></hp:tr></hp:tbl></hp:run></hp:p>
</hs:sec>'''.encode("utf-8")


class StyleProfileTest(unittest.TestCase):
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

        self.assertEqual(profile["profile_version"], 2)
        self.assertEqual(profile["format"]["기본_장평"], 95)
        self.assertEqual(profile["format"]["기본_줄간격_퍼센트"], 170)
        self.assertEqual(profile["format"]["제목_문단"]["font"], "테스트명조")
        self.assertEqual(profile["table_format"]["header_size"], 16)
        self.assertEqual(profile["table_format"]["body_size"], 12)


if __name__ == "__main__":
    unittest.main()
