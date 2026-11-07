"""노트북 노트 → 한/글 HWPX 내보내기: 생성 파일을 defusedxml로 다시 읽어 구조를 확인한다(COM 없음)."""
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from defusedxml import ElementTree as ET

from docfit_core.abbreviation_doc import default_base_hwpx
from docfit_core.notebook_hwpx import (
    NotebookHwpxError, build_notebook_hwpx, clean_text, normalize, read_notebook_hwpx,
)
from docfit_app.notebook_service import NOTEBOOK_COMMANDS, NotebookService

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"

DOC = {
    "title": "복지 예산 검토 노트",
    "notebook": "2027 예산",
    "tags": ["예산", "복지"],
    "body": "첫째 줄 <요약> & 정리\n둘째 줄\x01",
    "citations": [
        {"quote": "노인 일자리 예산은 12% 늘었다.", "source_name": "예산서.hwpx", "paragraph": 3, "location": "2쪽"},
        {"quote": "돌봄 사업 신설", "source_name": "계획.pdf", "paragraph": 7, "location": ""},
    ],
    "compare": {"query": "복지 예산", "groups": [
        {"source_name": "예산서.hwpx", "hits": [{"paragraph": 1, "location": "표", "body": "복지 예산 1,250억원"},
                                              {"paragraph": 4, "location": "", "body": "복지 예산 증가"}]},
        {"source_name": "계획.pdf", "hits": []},
    ]},
}


class NotebookHwpxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.base = default_base_hwpx()
        self.assertIsNotNone(self.base, "내장 기본 서식.hwpx가 필요합니다")

    def build(self, doc=DOC, name="노트.hwpx"):
        return build_notebook_hwpx(doc, self.base, self.dir / name)

    def test_structure_read_back_with_defusedxml(self):
        before = hashlib.sha256(Path(self.base).read_bytes()).hexdigest()
        path = self.build()
        parsed = read_notebook_hwpx(path)
        paragraphs = parsed["paragraphs"]
        self.assertEqual(paragraphs[0], "복지 예산 검토 노트")
        self.assertIn("노트북: 2027 예산", paragraphs)
        self.assertIn("태그: #예산 #복지", paragraphs)
        self.assertIn("첫째 줄 <요약> & 정리", paragraphs)
        self.assertIn("둘째 줄", paragraphs)          # 제어 문자는 빠진다
        self.assertIn("인용 (2건)", paragraphs)
        quote = paragraphs.index("노인 일자리 예산은 12% 늘었다.")
        self.assertEqual(paragraphs[quote + 1], "— 예산서.hwpx · 문단 3 · 2쪽")
        self.assertIn("— 계획.pdf · 문단 7", paragraphs)
        self.assertIn("출처 비교: 복지 예산", paragraphs)
        self.assertEqual(parsed["tables"], [[
            ["출처", "위치", "근거 문단"],
            ["예산서.hwpx", "문단 1 · 표", "복지 예산 1,250억원"],
            ["문단 4", "복지 예산 증가"],                # 출처 칸은 세로로 합쳐 첫 행에만 있다
            ["계획.pdf", "", "근거 문단 없음"],
        ]])
        # 바탕 문서는 그대로, 임시 파일은 남지 않는다.
        self.assertEqual(hashlib.sha256(Path(self.base).read_bytes()).hexdigest(), before)
        self.assertEqual([p.name for p in self.dir.iterdir()], ["노트.hwpx"])

    def test_package_and_table_xml(self):
        path = self.build()
        with zipfile.ZipFile(path) as z:
            first = z.infolist()[0]
            self.assertEqual((first.filename, first.compress_type), ("mimetype", zipfile.ZIP_STORED))
            self.assertEqual(z.read("mimetype"), b"application/hwp+zip")
            section = ET.fromstring(z.read("Contents/section0.xml"))
            ET.fromstring(z.read("Contents/header.xml"))
            names = z.namelist()
            if "Preview/PrvText.txt" in names:
                self.assertIn("복지 예산 검토 노트", z.read("Preview/PrvText.txt").decode("utf-8"))
        self.assertEqual(sum(1 for _ in section.iter(f"{HP}secPr")), 1)
        table = next(section.iter(f"{HP}tbl"))
        self.assertEqual((table.get("rowCnt"), table.get("colCnt")), ("4", "3"))
        width = int(table.find(f"{HP}sz").get("width"))
        merged = [tc for tc in table.iter(f"{HP}tc") if tc.find(f"{HP}cellSpan").get("rowSpan") == "2"]
        self.assertEqual(len(merged), 1)
        first_row = next(table.iter(f"{HP}tr"))
        self.assertEqual(sum(int(tc.find(f"{HP}cellSz").get("width")) for tc in first_row), width)
        self.assertTrue(all(tc.get("header") == "1" for tc in first_row))

    def test_without_citations_or_compare_has_no_table(self):
        path = self.build({"title": "", "body": "본문만", "tags": []}, "빈.hwpx")
        parsed = read_notebook_hwpx(path)
        self.assertEqual(parsed["paragraphs"][0], "제목 없는 노트")
        self.assertEqual(parsed["tables"], [])
        self.assertNotIn("인용 (0건)", parsed["paragraphs"])

    def test_overwrites_existing_target_atomically(self):
        target = self.dir / "노트.hwpx"
        target.write_bytes(b"old")
        self.build()
        self.assertEqual(read_notebook_hwpx(target)["paragraphs"][0], "복지 예산 검토 노트")

    def test_failed_verification_keeps_existing_file(self):
        target = self.dir / "노트.hwpx"
        target.write_bytes(b"old")
        with mock.patch("docfit_core.notebook_hwpx._verify", side_effect=NotebookHwpxError("검증 실패")):
            with self.assertRaises(NotebookHwpxError):
                self.build()
        self.assertEqual(target.read_bytes(), b"old")
        self.assertEqual([p.name for p in self.dir.iterdir()], ["노트.hwpx"])

    def test_read_rejects_broken_references(self):
        path = self.build()
        broken = self.dir / "깨짐.hwpx"
        with zipfile.ZipFile(path) as src, zipfile.ZipFile(broken, "w") as out:
            for info in src.infolist():
                data = src.read(info.filename)
                if info.filename == "Contents/section0.xml":
                    data = data.replace(b'charPrIDRef="', b'charPrIDRef="9999', 1)
                out.writestr(info, data)
        with self.assertRaises(NotebookHwpxError):
            read_notebook_hwpx(broken)

    def test_clean_text_and_compare_row_limit(self):
        self.assertEqual(clean_text("a\r\nb\tc\x00\x0b"), "a\nb c")
        many = {"title": "t", "compare": {"query": "q", "groups": [
            {"source_name": f"s{i}", "hits": [{"paragraph": j, "body": "x"} for j in range(5)]} for i in range(100)]}}
        self.assertEqual(len(normalize(many)["compare"]["groups"]), 100)
        parsed = read_notebook_hwpx(self.build(many, "많음.hwpx"))
        rows = parsed["tables"][0]
        self.assertEqual(len(rows), 401)              # 머리글 + 400행 상한


class FakeNotebookBridge:
    def __init__(self):
        self.calls = []

    def request(self, request):
        self.calls.append(request)
        cmd = request["cmd"]
        if cmd == "nb_list":
            return {"ok": True, "notebooks": [{"id": 1, "name": "2027 예산"}]}
        if cmd == "nb_note_list":
            return {"ok": True, "notes": [{"id": 4, "title": "검토", "body": "본문", "tags": ["복지"], "citations": [
                {"id": 1, "source_id": 2, "paragraph_ordinal": 0, "quote": "인용 하나"},
                {"id": 2, "source_id": 9, "paragraph_ordinal": 5, "quote": "지운 출처 인용"},
            ]}]}
        if cmd == "nb_source_list":
            return {"ok": True, "sources": [{"id": 2, "display_name": "예산서", "origin": "C:\\자료\\예산서.hwpx"},
                                            {"id": 3, "display_name": "계획.pdf", "origin": "D:/계획.pdf"}]}
        if cmd == "nb_source_paragraphs":
            return {"ok": True, "paragraphs": [{"ordinal": 0, "location": "1쪽"}]}
        if cmd == "nb_compare":
            return {"ok": True, "groups": [
                {"source_id": 3, "display_name": "계획.pdf", "origin": "D:/계획.pdf",
                 "hits": [{"ordinal": 2, "location": "", "body": "근거"}]},
                {"source_id": 2, "display_name": "예산서", "origin": "C:\\자료\\예산서.hwpx", "hits": []}]}
        return {"ok": False, "message": "unexpected"}


class NotebookServiceHwpxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_service_collects_note_and_compare(self):
        bridge = FakeNotebookBridge()
        service = NotebookService(bridge, extractor=mock.Mock())
        result = service.export_hwpx({"notebook_id": 1, "note_id": 4, "compare_query": " 복지 ",
                                      "compare_source_ids": [2, 3], "per_source": 2}, self.dir / "out.hwpx")
        self.assertTrue(result["ok"], result)
        parsed = read_notebook_hwpx(result["path"])
        self.assertEqual(parsed["paragraphs"][0], "검토")
        self.assertIn("— 예산서 (예산서.hwpx) · 문단 1 · 1쪽", parsed["paragraphs"])
        self.assertIn("— 삭제된 출처 · 문단 6", parsed["paragraphs"])
        self.assertEqual(parsed["tables"][0][1:], [["계획.pdf", "문단 3", "근거"],
                                                  ["예산서 (예산서.hwpx)", "", "근거 문단 없음"]])
        compare = next(c for c in bridge.calls if c["cmd"] == "nb_compare")
        self.assertEqual(compare, {"cmd": "nb_compare", "notebook_id": 1, "query": "복지", "per_source": 2,
                                   "source_ids": [2, 3]})
        # 지운 출처의 문단은 klib에 묻지 않는다.
        asked = [c["source_id"] for c in bridge.calls if c["cmd"] == "nb_source_paragraphs"]
        self.assertEqual(asked, [2])

    def test_service_errors(self):
        service = NotebookService(FakeNotebookBridge(), extractor=mock.Mock())
        self.assertFalse(service.export_hwpx({"notebook_id": 1, "note_id": 99}, self.dir / "a.hwpx")["ok"])
        self.assertFalse(service.export_hwpx({"notebook_id": 1, "note_id": 4}, self.dir / "a.txt")["ok"])
        self.assertFalse(service.export_hwpx({"notebook_id": "1", "note_id": 4}, self.dir / "a.hwpx")["ok"])
        self.assertEqual(list(self.dir.iterdir()), [])

    def test_export_command_is_not_passed_to_klib(self):
        self.assertNotIn("nb_export_hwpx", NOTEBOOK_COMMANDS)
        self.assertNotIn("nb_select_output", NOTEBOOK_COMMANDS)

    def test_desktop_bridge_uses_save_selection(self):
        import desktop_web_ui
        bridge = desktop_web_ui.DesktopWebBridge.__new__(desktop_web_ui.DesktopWebBridge)
        bridge._developer_mode_enabled = lambda: True
        bridge.window = None
        dialogs = mock.Mock()
        dialogs.select_files.return_value = {"ok": True, "cancelled": False, "selection_id": "tok"}
        dialogs.resolve_selection.return_value = [str(self.dir / "out.hwpx")]
        bridge._file_dialogs = dialogs
        service = mock.Mock()
        service.export_hwpx.return_value = {"ok": True, "path": "p"}
        bridge._notebook_service = service
        self.assertEqual(bridge.notebook({"cmd": "nb_select_output"})["selection_id"], "tok")
        self.assertEqual(dialogs.select_files.call_args.args[1:], ("notebook_hwpx", "save"))
        request = {"cmd": "nb_export_hwpx", "notebook_id": 1, "note_id": 4, "output_selection_id": "tok"}
        self.assertEqual(bridge.notebook(request), {"ok": True, "path": "p"})
        dialogs.resolve_selection.assert_called_once_with("tok", "notebook_hwpx")
        service.export_hwpx.assert_called_once_with(request, str(self.dir / "out.hwpx"))
        # 저장 위치 선택 없이 경로를 직접 넘길 수 없다.
        result = bridge.notebook({"cmd": "nb_export_hwpx", "notebook_id": 1, "note_id": 4, "target_path": "C:/x.hwpx"})
        self.assertFalse(result["ok"])

    def test_dialog_purpose_registered(self):
        from docfit_app.native_file_dialog_service import PURPOSES
        self.assertEqual(PURPOSES["notebook_hwpx"], ("save", frozenset({".hwpx"})))


if __name__ == "__main__":
    unittest.main()
