"""원본 보존 경로: 무손실 보관·최소 변경 쓰기·원문 위치 맵·내용 패치·다층 검증·해석 범위."""
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from docfit_core.fidelity import (PackageSnapshot, PatchError, apply_patch, build_source_map, copy_exact,
                                  coverage, inventory, list_objects, verify_patch, write_package)
from docfit_core.fidelity.package import CFB_SIG, build_package

HP = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'
SEG = '<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="1000" horzpos="0" horzsize="42520"/></hp:linesegarray>'
SECTION = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><hs:sec {HP}>'
    f'<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>첫째 문단 9월 계획</hp:t></hp:run>'
    f'<hp:run charPrIDRef="1"><hp:t>(참고)</hp:t></hp:run>{SEG}</hp:p>'
    f'<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:tbl rowCnt="1" colCnt="1">'
    f'<hp:tr><hp:tc borderFillIDRef="1"><hp:subList vertAlign="CENTER">'
    f'<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>칸 글</hp:t></hp:run>{SEG}</hp:p>'
    f'</hp:subList><hp:cellAddr colAddr="0" rowAddr="0"/></hp:tc></hp:tr></hp:tbl></hp:run>{SEG}</hp:p>'
    f'<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>A &amp; B 사업</hp:t></hp:run>{SEG}</hp:p>'
    f'<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>빈칸<hp:fwSpace/>섞인 글</hp:t></hp:run>{SEG}</hp:p>'
    f'<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run>'
    f'<hp:run charPrIDRef="0"><hp:t>둘째 run 글</hp:t></hp:run>{SEG}</hp:p>'
    '</hs:sec>')
HEADER = '<?xml version="1.0" encoding="UTF-8" ?><hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"><hh:refList/></hh:head>'


def make_hwpx(path, section=SECTION, comment=b"docfit test"):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(zipfile.ZipInfo("mimetype", (1980, 1, 1, 0, 0, 0)), "application/hwp+zip",
                         compress_type=zipfile.ZIP_STORED)
        for name, data in (("Contents/header.xml", HEADER), ("Contents/section0.xml", section),
                           ("Preview/PrvText.txt", "미리보기")):
            info = zipfile.ZipInfo(name, (2026, 10, 3, 12, 0, 0))
            info.external_attr = 0o644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr(zipfile.ZipInfo("BinData/image1.png", (1980, 1, 1, 0, 0, 0)), b"\x89PNG" + bytes(200),
                         compress_type=zipfile.ZIP_STORED)
        archive.comment = comment


class FidelityTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix="docfit-fidelity-"))
        self.source = self.folder / "source.hwpx"
        make_hwpx(self.source)
        self.snapshot = PackageSnapshot.load(self.source)

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def plan(self, *operations):
        return {"source_sha256": self.snapshot.sha256, "operations": list(operations)}

    def section(self, path):
        return build_source_map("Contents/section0.xml", PackageSnapshot.load(path).read("Contents/section0.xml"))

    # ---- 보관·쓰기 ---------------------------------------------------------
    def test_unchanged_write_is_byte_identical(self):
        self.assertEqual(build_package(self.snapshot, {}), self.source.read_bytes())
        self.assertEqual(self.snapshot.format, "hwpx")
        self.assertEqual(self.snapshot.read("mimetype"), b"application/hwp+zip")

    def test_rewrite_keeps_other_entries_raw_and_metadata(self):
        target = self.folder / "out.hwpx"
        new = SECTION.replace("9월", "10월").encode("utf-8")
        write_package(self.snapshot, {"Contents/section0.xml": new}, target)
        result = PackageSnapshot.load(target)
        for name, entry in self.snapshot.entries.items():
            if name != "Contents/section0.xml":
                self.assertEqual(result.entries[name].local, entry.local, name)
        with zipfile.ZipFile(target) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.read("Contents/section0.xml"), new)
            self.assertEqual(archive.comment, b"docfit test")
            info = archive.getinfo("Contents/section0.xml")
            self.assertEqual((info.date_time, info.external_attr >> 16), ((2026, 10, 3, 12, 0, 0), 0o644))
        with self.assertRaises(ValueError):
            write_package(self.snapshot, {}, self.source)

    def test_copy_exact_and_binary_hwp(self):
        report = copy_exact(self.source, self.folder / "copy.hwpx")
        self.assertEqual(report["verdict"], "검증된 완전 일치")
        hwp = self.folder / "old.hwp"
        hwp.write_bytes(CFB_SIG + bytes(600))
        self.assertEqual(PackageSnapshot.load(hwp).format, "hwp")
        self.assertTrue(copy_exact(hwp, self.folder / "old2.hwp")["identical"])
        self.assertEqual(coverage(inventory(hwp))["verdict"], "원본 보관·동일 복제만 지원(내용 해석 지원 불가)")

    # ---- 원문 위치 맵 ------------------------------------------------------
    def test_source_map_paths_and_text(self):
        source_map = build_source_map("Contents/section0.xml", self.snapshot.read("Contents/section0.xml"))
        cell = "/p[1]/run[0]/tbl[0]/tr[0]/tc[0]/subList[0]/p[0]"
        self.assertEqual(source_map.paragraph_text(source_map.by_path[cell]), "칸 글")
        self.assertEqual(source_map.paragraph_text(source_map.by_path["/p[2]"]), "A & B 사업")
        self.assertEqual(source_map.paragraph_text(source_map.by_path["/p[3]"]), "빈칸 섞인 글")
        objects = {item["object"]: item for item in list_objects(self.snapshot)}
        self.assertTrue(objects[cell]["in_table"])
        self.assertFalse(objects["/p[3]"]["whole_text_editable"])

    # ---- 내용 패치 ---------------------------------------------------------
    def test_replace_text_changes_only_that_text_and_layout_cache(self):
        target = self.folder / "patched.hwpx"
        report = apply_patch(self.snapshot, self.plan(
            {"op": "replace_text", "part": "Contents/section0.xml", "object": "/p[0]", "old": "9월", "new": "10월"}),
            target)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["verdict"], "허용한 변화만 확인")
        self.assertEqual(report["applied"][0]["after"], "첫째 문단 10월 계획(참고)")
        self.assertEqual(report["changed_parts"], ["Contents/section0.xml"])
        before = self.snapshot.read("Contents/section0.xml")
        after = PackageSnapshot.load(target).read("Contents/section0.xml")
        expected = before.replace("9월".encode(), "10월".encode(), 1).replace(SEG.encode(), b"", 1)
        self.assertEqual(after, expected)
        result = self.section(target)
        self.assertFalse(result.by_path["/p[0]"].child("linesegarray"))
        self.assertTrue(result.by_path["/p[2]"].child("linesegarray"))
        self.assertTrue(any("미리보기" in w for w in report["warnings"]))

    def test_entity_and_cell_and_empty_text_element(self):
        target = self.folder / "patched2.hwpx"
        cell = "/p[1]/run[0]/tbl[0]/tr[0]/tc[0]/subList[0]/p[0]"
        report = apply_patch(self.snapshot, self.plan(
            {"op": "replace_text", "part": "Contents/section0.xml", "object": "/p[2]", "old": "B", "new": "C<D>"},
            {"op": "set_paragraph_text", "part": "Contents/section0.xml", "object": cell,
             "expect": "칸 글", "new": "새 칸 글"},
            {"op": "set_paragraph_text", "part": "Contents/section0.xml", "object": "/p[4]",
             "expect": "둘째 run 글", "new": "첫 run으로 옮긴 글"}), target)
        self.assertEqual(report["verdict"], "허용한 변화만 확인", report)
        result = self.section(target)
        self.assertEqual(result.paragraph_text(result.by_path["/p[2]"]), "A & C<D> 사업")
        self.assertEqual(result.paragraph_text(result.by_path[cell]), "새 칸 글")
        last = result.by_path["/p[4]"]
        self.assertEqual([result.paragraph_text(last)], ["첫 run으로 옮긴 글"])
        first_t = result.paragraph_runs(last)[0]
        self.assertEqual(result.text(first_t.open_end, first_t.close_start), "첫 run으로 옮긴 글")
        # 바깥 문단(표가 든 문단)의 줄 배치 캐시는 그대로다.
        self.assertTrue(result.by_path["/p[1]"].child("linesegarray"))

    def test_strict_mode_does_not_write_partial_results(self):
        target = self.folder / "strict.hwpx"
        good = {"op": "replace_text", "part": "Contents/section0.xml", "object": "/p[0]", "old": "9월", "new": "10월"}
        stale = {"op": "set_paragraph_text", "part": "Contents/section0.xml", "object": "/p[2]",
                 "expect": "예전 글", "new": "새 글"}
        report = apply_patch(self.snapshot, self.plan(good, stale), target)
        self.assertEqual((report["status"], report["verdict"]), ("failed", "실패"))
        self.assertIn("expect", report["skipped"][0]["reason"])
        self.assertFalse(target.exists())
        report = apply_patch(self.snapshot, self.plan(good, stale), target, allow_partial=True)
        self.assertEqual((report["status"], report["verdict"]), ("partial", "부분 적용"))
        self.assertTrue(target.exists())

    def test_unsafe_requests_are_refused(self):
        cases = [
            ({"op": "replace_text", "part": "Contents/section0.xml", "object": "/p[0]", "old": "계획(참고",
              "new": "x"}, "걸쳐"),
            ({"op": "replace_text", "part": "Contents/section0.xml", "object": "/p[0]", "old": "9월",
              "new": "줄\n바꿈"}, "제어 문자"),
            ({"op": "set_paragraph_text", "part": "Contents/section0.xml", "object": "/p[3]",
              "expect": "빈칸 섞인 글", "new": "x"}, "빈칸·탭"),
            ({"op": "replace_text", "part": "Contents/section0.xml", "object": "/p[9]", "old": "a", "new": "b"},
             "찾지 못"),
            ({"op": "replace_text", "part": "Contents/header.xml", "object": "/p[0]", "old": "a", "new": "b"},
             "본문 파트"),
        ]
        for op, words in cases:
            with self.subTest(op=op):
                report = apply_patch(self.snapshot, self.plan(op))
                self.assertIn(words, report["skipped"][0]["reason"])
        with self.assertRaises(PatchError):
            apply_patch(self.snapshot, {"source_sha256": "0" * 64, "operations": []})
        with self.assertRaises(PatchError):
            apply_patch(self.snapshot, {"operations": []})

    # ---- 검증 --------------------------------------------------------------
    def test_verify_detects_unexpected_changes(self):
        target = self.folder / "patched3.hwpx"
        report = apply_patch(self.snapshot, self.plan(
            {"op": "replace_text", "part": "Contents/section0.xml", "object": "/p[0]", "old": "9월", "new": "10월"}),
            target)
        self.assertEqual(report["verdict"], "허용한 변화만 확인")
        # 고치지 않기로 한 항목이 바뀐 경우
        tampered = self.folder / "tampered.hwpx"
        result = PackageSnapshot.load(target)
        write_package(result, {"Preview/PrvText.txt": "다른 미리보기".encode("utf-8")}, tampered)
        verdict = verify_patch(self.snapshot, tampered, report)
        self.assertEqual(verdict["verdict"], "실패")
        self.assertEqual(verdict["layers"][1]["status"], "failed")
        # 바꾼 파트 안에서 허용하지 않은 속성이 바뀐 경우
        section = result.read("Contents/section0.xml").replace(b'rowCnt="1"', b'rowCnt="2"')
        write_package(result, {"Contents/section0.xml": section}, tampered)
        verdict = verify_patch(self.snapshot, tampered, report)
        self.assertEqual(verdict["layers"][2]["status"], "failed")
        self.assertTrue(any("tbl[0]" in d for d in verdict["layers"][2]["details"]))
        # 한/글 열기 검사 결과를 받는다.
        verdict = verify_patch(self.snapshot, target, report, native=lambda path: {"opened": True})
        self.assertEqual(verdict["layers"][-1]["status"], "passed")
        self.assertEqual(verdict["notes"], [])

    # ---- 해석 범위 ---------------------------------------------------------
    def test_coverage_reports_unknown_elements_honestly(self):
        section = SECTION.replace("</hs:sec>", '<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0">'
                                  '<hp:newThing magic="1"/></hp:run></hp:p></hs:sec>')
        path = self.folder / "unknown.hwpx"
        make_hwpx(path, section)
        report = coverage(inventory(path))
        part = next(p for p in report["parts"] if p["name"] == "Contents/section0.xml")
        self.assertEqual(part["status"], "일부 해석")
        self.assertIn("newThing", part["unknown_elements"])
        self.assertIn("newThing@magic", part["unknown_attributes"])
        self.assertEqual(next(p for p in report["parts"] if p["name"] == "BinData/image1.png")["status"], "원문 보존만")
        self.assertEqual(report["verdict"], "원본 보존 완료·의미 해석 미완료")
        self.assertLess(report["elements_ratio"], 1)


if __name__ == "__main__":
    unittest.main()
