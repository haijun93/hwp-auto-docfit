"""예시 서식 문서의 제목·개요 표 분석 → 서식 프로필 → 제목 서식 적용에 예시 표 사용."""
import copy
from pathlib import Path
import runpy
import tempfile
import unittest
import zipfile

from docfit_core import format_elements as fe


class FormTableProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
                                run_name="form_table_profile_test")
        cls.name = staticmethod(cls.ns["제목_xml이름"])
        # run_path는 전역 사본을 돌려준다. 함수가 보는 전역은 __globals__로 바꾼다.
        cls.g = cls.ns["_서식표_예시"].__globals__
        cls.folder = tempfile.TemporaryDirectory(prefix="docfit-form-profile-")

    @classmethod
    def tearDownClass(cls):
        cls.g["활성_서식표_프로필"] = None
        cls.folder.cleanup()

    def setUp(self):
        self.g["활성_서식표_프로필"] = None

    def _hwpx(self, filename, tables, header=None):
        """내장 제목 기준 자료의 header에 표들을 본문 문단 하나로 넣은 HWPX."""
        ns = self.ns
        base_header, section = ns["제목_원본자료"]()
        header = header if header is not None else base_header
        for p in list(section):
            section.remove(p)
        pt = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
        p = ns["XML_자식_추가"](section, section, tag=pt + "p",
                              attrib={"id": "0", "paraPrIDRef": "20", "styleIDRef": "0"})
        for table in tables:
            run = ns["XML_자식_추가"](p, section, tag=pt + "run", attrib={"charPrIDRef": "8"})
            run.append(copy.deepcopy(table))
        path = Path(self.folder.name) / filename
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("mimetype", "application/hwp+zip")
            archive.writestr("Contents/header.xml", ns["ET"].tostring(header, encoding="utf-8", xml_declaration=True))
            archive.writestr("Contents/section0.xml", ns["ET"].tostring(section, encoding="utf-8", xml_declaration=True))
        return path

    def _builtin_tables(self):
        _, section = self.ns["제목_원본자료"]()
        title1 = next(x for x in section.iter() if self.name(x) == "tbl")
        _, extra = self.ns["개요붙임_원본자료"]()
        overview = next(x for x in extra.iter() if self.name(x) == "tbl")
        return title1, overview

    def _a1_look(self, path):
        with zipfile.ZipFile(path) as archive:
            header = self.ns["safe_xml_fromstring"](archive.read("Contents/header.xml"))
            section = self.ns["safe_xml_fromstring"](archive.read("Contents/section0.xml"))
        chars = {c.get("id"): c for c in header.iter() if self.name(c) == "charPr"}
        table = next(t for t in section.iter() if self.name(t) == "tbl")
        paragraph = [p for p in self.ns["제목_문단들"](self.ns["제목_셀들"](table)[0])
                     if self.ns["제목_문자열"](p).strip()][0]
        heights = {chars[r.get("charPrIDRef")].get("height") for r in paragraph if self.name(r) == "run"
                   and self.ns["제목_문자열"](r).strip() not in ("‘", "’", "’ ")}
        return heights

    def test_example_document_profile_keeps_form_tables(self):
        title1, overview = self._builtin_tables()
        source = self._hwpx("example.hwpx", [title1, overview])
        profile = self.ns["hwpx_서식_분석"](source)
        self.assertEqual(sorted(profile["form_tables"]), ["overview", "title1"])
        forms = profile["element_analysis"]["forms"]
        self.assertEqual(list(forms["title1"]["cells"]), ["A1", "A2", "B2"])
        self.assertEqual(forms["title1"]["cells"]["A1"]["paras"][0]["size"]["value"], 2700)
        self.assertIn("서식 표 예시", profile["summary"])
        # 저장 형식(JSON)으로 바꿀 수 있어야 한다.
        import json
        json.dumps(profile, ensure_ascii=False)

    def test_title_formatting_uses_edited_profile_sample(self):
        title1, overview = self._builtin_tables()
        profile = self.ns["hwpx_서식_분석"](self._hwpx("example2.hwpx", [title1, overview]))
        fe.set_value(profile["element_analysis"], ("form", "title1", "para", "A1", 0), "size", 2400)
        fe.apply_to_profile(profile)
        target = self._hwpx("target.hwpx", [title1])
        found = self.ns["제목_hwpx_처리"](target)
        self.assertEqual(found, {"Contents/section0.xml": [(0, 1)]})
        # 서식 프로필이 없으면 내장 기준 표(27pt)를 쓴다.
        plain = target.with_name("plain.hwpx")
        self.ns["제목_hwpx_처리"](target, plain, found)
        self.assertEqual(self._a1_look(plain), {"2700"})
        self.g["활성_서식표_프로필"] = profile["form_tables"]
        styled = target.with_name("styled.hwpx")
        self.assertEqual(self.ns["제목_hwpx_처리"](target, styled, found), 1)
        self.assertEqual(self._a1_look(styled), {"2400"})

    def test_mismatched_sample_falls_back_to_builtin(self):
        title1, overview = self._builtin_tables()
        profile = self.ns["hwpx_서식_분석"](self._hwpx("example3.hwpx", [title1, overview]))
        # 2×2 제목 예시를 2행1열 제목 자리에 두면 칸 구성이 달라 쓰지 않는다.
        self.g["활성_서식표_프로필"] = {"title3": profile["form_tables"]["title1"]}
        self.assertIsNone(self.ns["_서식표_예시"]("title3"))
        self.g["활성_서식표_프로필"] = profile["form_tables"]
        header, table = self.ns["_서식표_예시"]("title1")
        self.assertEqual(self.ns["제목_유형판별"](table), 1)

    def test_label_tables_use_profile_sample_without_forcing_center(self):
        title1, overview = self._builtin_tables()
        profile = self.ns["hwpx_서식_분석"](self._hwpx("example4.hwpx", [title1, overview]))
        fe.set_value(profile["element_analysis"], ("form", "title1", "para", "A1", 0), "align", "LEFT")
        fe.apply_to_profile(profile)
        self.g["활성_서식표_프로필"] = profile["form_tables"]
        header, _ = self.ns["제목_원본자료"]()
        cache = {}
        table = self.ns["서식표_생성"](header, "title1", "새 보고서 제목", cache)
        self.assertIn("title1", cache["예시사용"])
        paras = {p.get("id"): p for p in header.iter() if self.name(p) == "paraPr"}
        paragraph = self.ns["제목_문단들"](self.ns["제목_셀들"](table)[0])[0]
        align = next(x for x in paras[paragraph.get("paraPrIDRef")].iter() if self.name(x) == "align")
        self.assertEqual(align.get("horizontal"), "LEFT")
        self.assertEqual(self.ns["제목_문자열"](self.ns["제목_셀들"](table)[0]).strip(), "새 보고서 제목")


if __name__ == "__main__":
    unittest.main()
