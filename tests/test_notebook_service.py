import hashlib
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from docfit_app.library_bridge import ALLOWED_COMMANDS, LibraryBridgeError
from docfit_app.notebook_service import (
    NOTEBOOK_COMMANDS, NotebookService, extract_source_paragraphs, needs_python_extraction,
)


class FakeBridge:
    def __init__(self):
        self.calls = []

    def request(self, request):
        self.calls.append(request)
        if request["cmd"] == "item_get":
            return dict(self.item, ok=True) if getattr(self, "item", None) else {"ok": False}
        if request["cmd"] == "nb_source_from_item":
            return {"ok": True, "id": 9, "paragraph_count": len(request.get("paragraphs") or []), "reused": getattr(self, "reused", False)}
        if request["cmd"] == "nb_source_add":
            return {"ok": True, "id": 7, "paragraph_count": len(request.get("paragraphs") or [])}
        return {"ok": True}


def make_docx(path, paragraphs):
    body = "".join(f"<w:p><w:r><w:t>{t}</w:t></w:r></w:p>" for t in paragraphs)
    xml = ('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/'
           f'wordprocessingml/2006/main"><w:body>{body}</w:body></w:document>')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml", xml)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest(), os.stat(path).st_mtime_ns


def make_desktop_bridge(developer=True):
    import desktop_web_ui
    bridge = desktop_web_ui.DesktopWebBridge.__new__(desktop_web_ui.DesktopWebBridge)
    bridge._developer_mode_enabled = lambda: developer
    bridge.window = None
    return bridge


class NotebookServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_commands_are_allowed_by_bridge(self):
        self.assertTrue(NOTEBOOK_COMMANDS <= ALLOWED_COMMANDS)
        self.assertIn("nb_compare", NOTEBOOK_COMMANDS)

    def test_compare_and_tagged_note_requests_pass_through(self):
        bridge = FakeBridge()
        service = NotebookService(bridge, extractor=mock.Mock())
        requests = [
            {"cmd": "nb_compare", "notebook_id": 1, "query": "복지 예산", "source_ids": [2, 3], "per_source": 3},
            {"cmd": "nb_note_save", "notebook_id": 1, "title": "메모", "body": "", "tags": ["예산"]},
            {"cmd": "nb_note_list", "notebook_id": 1, "tag": "예산"},
            {"cmd": "nb_export_md", "notebook_id": 1, "note_id": 4, "compare_query": "복지"},
        ]
        for request in requests:
            service.handle(request)
        self.assertEqual(bridge.calls, requests)

    def test_only_old_hwp_and_pdf_use_python_extraction(self):
        self.assertTrue(needs_python_extraction("C:/자료/옛보고서.HWP"))
        self.assertTrue(needs_python_extraction("a.pdf"))
        for name in ("a.hwpx", "a.docx", "a.txt", "a.md", "a.pptx", "a.xlsx"):
            self.assertFalse(needs_python_extraction(name), name)

    def test_rust_formats_pass_straight_to_klib(self):
        bridge = FakeBridge()
        extractor = mock.Mock()
        request = {"cmd": "nb_source_add", "notebook_id": 1, "source_path": str(self.dir / "a.hwpx")}
        NotebookService(bridge, extractor=extractor).handle(request)
        self.assertEqual(bridge.calls, [request])
        extractor.assert_not_called()

    def test_item_link_commands_are_allowed(self):
        for cmd in ("nb_source_from_item", "nb_source_item"):
            self.assertIn(cmd, NOTEBOOK_COMMANDS)
            self.assertIn(cmd, ALLOWED_COMMANDS)

    def test_from_item_rust_format_passes_to_klib(self):
        bridge = FakeBridge()
        bridge.item = {"source_path": str(self.dir / "a.hwpx")}
        request = {"cmd": "nb_source_from_item", "notebook_id": 3, "item_id": 5}
        NotebookService(bridge).handle(request)
        self.assertEqual(bridge.calls[-1], request)

    def test_from_item_pdf_is_extracted_and_extra_batches_indexed(self):
        pdf = self.dir / "자료.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        rows = [{"text": "Ⅰ. 개요", "level": 1, "table": False, "location": "1쪽"}]
        bridge = FakeBridge()
        bridge.item = {"source_path": str(pdf)}
        result = NotebookService(bridge, extractor=mock.Mock(return_value=rows)).handle(
            {"cmd": "nb_source_from_item", "notebook_id": 3, "item_id": 5})
        self.assertEqual(result["id"], 9)
        sent = bridge.calls[-1]
        self.assertEqual((sent["cmd"], sent["item_id"], sent["paragraphs"]), ("nb_source_from_item", 5, rows))

    def test_from_item_reused_source_is_not_reindexed(self):
        pdf = self.dir / "자료.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        bridge = FakeBridge()
        bridge.item = {"source_path": str(pdf)}
        bridge.reused = True
        rows = [{"text": "가", "level": 0, "table": False, "location": ""}]
        with mock.patch("docfit_app.notebook_service._batches", return_value=iter([rows, rows])):
            result = NotebookService(bridge, extractor=mock.Mock(return_value=rows)).handle(
                {"cmd": "nb_source_from_item", "notebook_id": 3, "item_id": 5})
        self.assertTrue(result["reused"])
        self.assertNotIn("nb_index", [c["cmd"] for c in bridge.calls])

    def test_pdf_is_extracted_in_python_and_sent_with_paragraphs(self):
        pdf = self.dir / "자료.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        rows = [{"text": "Ⅰ. 개요", "level": 1, "table": False, "location": "1쪽"},
                {"text": "구분\t금액", "level": 0, "table": True, "location": "1쪽"}]
        bridge = FakeBridge()
        result = NotebookService(bridge, extractor=mock.Mock(return_value=rows)).handle(
            {"cmd": "nb_source_add", "notebook_id": 3, "source_path": str(pdf), "display_name": "참고"})
        self.assertEqual(result, {"ok": True, "id": 7, "paragraph_count": 2})
        (add,) = bridge.calls
        self.assertEqual((add["cmd"], add["notebook_id"], add["display_name"]), ("nb_source_add", 3, "참고"))
        self.assertEqual(add["source_path"], os.path.abspath(pdf))
        self.assertEqual(add["paragraphs"], rows)

    def test_large_extraction_is_split_into_index_batches(self):
        hwp = self.dir / "big.hwp"
        hwp.write_bytes(b"x")
        rows = [{"text": f"문단 {i} " + "가" * 500, "level": 0, "table": False, "location": ""} for i in range(400)]
        bridge = FakeBridge()
        result = NotebookService(bridge, extractor=lambda _: rows).add_source(1, hwp)
        self.assertTrue(result["ok"])
        self.assertEqual(bridge.calls[0]["cmd"], "nb_source_add")
        rest = bridge.calls[1:]
        self.assertTrue(rest)
        self.assertTrue(all(c["cmd"] == "nb_index" and c["source_id"] == 7 for c in rest))
        self.assertEqual(sum(len(c["paragraphs"]) for c in bridge.calls), 400)
        import json
        self.assertTrue(all(len(json.dumps(c, ensure_ascii=False).encode()) < 64 * 1024 for c in bridge.calls))

    def test_extraction_failure_is_reported_without_adding(self):
        bad = self.dir / "c.pdf"
        bad.write_bytes(b"not a pdf")
        bridge = FakeBridge()
        result = NotebookService(bridge, extractor=mock.Mock(side_effect=ValueError("암호 문서"))).add_source(1, bad)
        self.assertFalse(result["ok"])
        self.assertIn("암호 문서", result["message"])
        self.assertEqual(bridge.calls, [])
        self.assertFalse(NotebookService(bridge).add_source(1, self.dir / "none.pdf")["ok"])

    def test_txt_and_docx_extraction_shape_and_original_unchanged(self):
        txt = self.dir / "a.txt"
        txt.write_text("첫째 문단\n\n둘째 문단\n", encoding="utf-8")
        docx = self.dir / "b.docx"
        make_docx(docx, ["보고서 제목", "본문 내용입니다"])
        before = digest(txt), digest(docx)
        rows = extract_source_paragraphs(txt)
        self.assertIn("첫째 문단", [r["text"] for r in rows])
        for r in rows:
            self.assertEqual(set(r), {"text", "level", "table", "location"})
            self.assertIsInstance(r["level"], int)
        self.assertEqual([r["text"] for r in extract_source_paragraphs(docx)], ["보고서 제목", "본문 내용입니다"])
        self.assertEqual((digest(txt), digest(docx)), before)

    def test_handle_passthrough_and_rejects_unknown(self):
        bridge = FakeBridge()
        service = NotebookService(bridge)
        service.handle({"cmd": "nb_search", "notebook_id": 1, "query": "예산"})
        self.assertEqual(bridge.calls[-1]["cmd"], "nb_search")
        with self.assertRaises(LibraryBridgeError):
            service.handle({"cmd": "box_list"})


class DesktopNotebookTests(unittest.TestCase):
    def test_single_notebook_method(self):
        import inspect
        import desktop_web_ui
        source = inspect.getsource(desktop_web_ui.DesktopWebBridge)
        self.assertEqual(source.count("def notebook(self"), 1)

    def test_developer_mode_off_is_rejected(self):
        bridge = make_desktop_bridge(developer=False)
        with mock.patch("docfit_app.library_bridge.LibraryBridge", side_effect=AssertionError):
            result = bridge.notebook({"cmd": "nb_list"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "DEVELOPER_MODE_REQUIRED")
        self.assertFalse(hasattr(bridge, "_notebook_service"))

    def test_developer_mode_on_creates_service_lazily(self):
        bridge = make_desktop_bridge()
        fake = FakeBridge()
        with mock.patch("docfit_app.library_bridge.LibraryBridge", return_value=fake):
            result = bridge.notebook({"cmd": "nb_list"})
        self.assertTrue(result["ok"])
        self.assertEqual(fake.calls[0]["cmd"], "nb_list")
        self.assertFalse(bridge.notebook({"cmd": "box_list"})["ok"])

    def test_drop_watch_routes_drops_to_notebook_and_restores(self):
        bridge = make_desktop_bridge()
        bridge.drop_target = "rename_files"
        bridge.get_state = lambda: {"state": True}
        bridge.add_paths = mock.Mock(side_effect=AssertionError("문서 목록으로 가면 안 됨"))
        self.assertEqual(bridge.notebook({"cmd": "nb_drop_watch", "active": True})["drop_target"], "notebook")
        bridge.receive_drop(["C:/자료/가.hwp", "C:/자료/나.docx"])
        bridge.receive_drop(["C:/자료/다.pdf"])
        taken = bridge.notebook({"cmd": "nb_take_drop"})
        self.assertEqual(taken["paths"], ["C:/자료/가.hwp", "C:/자료/나.docx", "C:/자료/다.pdf"])
        self.assertEqual(bridge.notebook({"cmd": "nb_take_drop"})["paths"], [])
        self.assertEqual(bridge.notebook({"cmd": "nb_drop_watch", "active": False})["drop_target"], "rename_files")


    def test_library_drop_watch_routes_drops_to_library_and_restores(self):
        """탐색기에서 자료함 창에 끌어 놓은 파일을 자료함이 가져간다(사용자 보고 2026-11-07)."""
        bridge = make_desktop_bridge()
        bridge.drop_target = "documents"
        bridge.get_state = lambda: {"state": True}
        bridge.add_paths = mock.Mock(side_effect=AssertionError("문서 목록으로 가면 안 됨"))
        self.assertEqual(bridge.library({"cmd": "lib_drop_watch", "active": True})["drop_target"], "library")
        bridge.receive_drop(["C:/자료/가.hwpx"])
        bridge.receive_drop(["C:/자료/나.xlsx"])
        self.assertEqual(bridge.library({"cmd": "lib_take_drop"})["paths"], ["C:/자료/가.hwpx", "C:/자료/나.xlsx"])
        self.assertEqual(bridge.library({"cmd": "lib_take_drop"})["paths"], [])
        self.assertEqual(bridge.library({"cmd": "lib_drop_watch", "active": False})["drop_target"], "documents")

if __name__ == "__main__":
    unittest.main()
