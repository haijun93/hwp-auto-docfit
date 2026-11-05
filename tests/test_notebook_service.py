import hashlib
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from docfit_app.library_bridge import ALLOWED_COMMANDS, LibraryBridgeError
from docfit_app.notebook_service import NOTEBOOK_COMMANDS, NotebookService, extract_source_paragraphs


class FakeBridge:
    def __init__(self):
        self.calls = []

    def request(self, request):
        self.calls.append(request)
        if request["cmd"] == "nb_source_add":
            return {"ok": True, "source_id": 7}
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


class NotebookServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_commands_are_allowed_by_bridge(self):
        self.assertTrue(NOTEBOOK_COMMANDS <= ALLOWED_COMMANDS)

    def test_txt_extraction_and_command_order(self):
        txt = self.dir / "a.txt"
        txt.write_text("첫째 문단\n\n둘째 문단\n", encoding="utf-8")
        before = digest(txt)
        bridge = FakeBridge()
        result = NotebookService(bridge).add_source(1, txt)
        self.assertTrue(result["ok"])
        self.assertEqual([c["cmd"] for c in bridge.calls], ["nb_source_add", "nb_index"])
        add, index = bridge.calls
        self.assertEqual((add["notebook_id"], add["kind"], add["name"]), (1, "txt", "a.txt"))
        self.assertEqual(index["source_id"], 7)
        texts = [p["text"] for p in index["paragraphs"]]
        self.assertIn("첫째 문단", texts)
        self.assertIn("둘째 문단", texts)
        for p in index["paragraphs"]:
            self.assertEqual(set(p), {"seq", "page", "text", "level"})
        self.assertEqual([p["seq"] for p in index["paragraphs"]], list(range(1, len(texts) + 1)))
        self.assertEqual(digest(txt), before)

    def test_docx_extraction_original_unchanged(self):
        docx = self.dir / "b.docx"
        make_docx(docx, ["보고서 제목", "본문 내용입니다"])
        before = digest(docx)
        paragraphs = extract_source_paragraphs(docx)
        self.assertEqual([p["text"] for p in paragraphs], ["보고서 제목", "본문 내용입니다"])
        self.assertEqual(digest(docx), before)

    def test_unchanged_file_not_extracted_again(self):
        txt = self.dir / "a.txt"
        txt.write_text("내용", encoding="utf-8")
        extractor = mock.Mock(return_value=[{"seq": 1, "page": None, "text": "내용", "level": None}])
        bridge = FakeBridge()
        service = NotebookService(bridge, extractor=extractor)
        service.add_source(1, txt)
        again = service.add_source(1, txt)
        self.assertTrue(again["skipped"])
        self.assertEqual(extractor.call_count, 1)
        self.assertEqual(len(bridge.calls), 2)
        txt.write_text("내용이 바뀜", encoding="utf-8")
        service.add_source(1, txt)
        self.assertEqual(extractor.call_count, 2)

    def test_failure_reason_is_kept(self):
        bad = self.dir / "c.docx"
        bad.write_bytes(b"not a zip")
        service = NotebookService(FakeBridge())
        result = service.add_source(1, bad)
        self.assertFalse(result["ok"])
        self.assertTrue(service.failure_reason(1, bad))
        self.assertEqual(service.failure_reason(1, bad), result["message"])
        missing = service.add_source(1, self.dir / "none.txt")
        self.assertFalse(missing["ok"])

    def test_large_index_is_split_into_small_requests(self):
        txt = self.dir / "big.txt"
        txt.write_text("\n".join(f"문단 {i} " + "가" * 500 for i in range(400)), encoding="utf-8")
        bridge = FakeBridge()
        NotebookService(bridge).add_source(1, txt)
        indexes = [c for c in bridge.calls if c["cmd"] == "nb_index"]
        self.assertGreater(len(indexes), 1)
        self.assertEqual(sum(len(c["paragraphs"]) for c in indexes), 400)

    def test_handle_passthrough_and_rejects_unknown(self):
        bridge = FakeBridge()
        service = NotebookService(bridge)
        service.handle({"cmd": "nb_search", "notebook_id": 1, "query": "예산"})
        self.assertEqual(bridge.calls[-1]["cmd"], "nb_search")
        with self.assertRaises(LibraryBridgeError):
            service.handle({"cmd": "box_list"})

    def test_developer_mode_off_is_rejected(self):
        import desktop_web_ui
        bridge = desktop_web_ui.DesktopWebBridge.__new__(desktop_web_ui.DesktopWebBridge)
        bridge._developer_mode_enabled = lambda: False
        with mock.patch("docfit_app.library_bridge.LibraryBridge", side_effect=AssertionError):
            result = bridge.notebook({"cmd": "nb_list"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "DEVELOPER_MODE_REQUIRED")
        self.assertFalse(hasattr(bridge, "_notebook_service"))

    def test_developer_mode_on_creates_service_lazily(self):
        import desktop_web_ui
        bridge = desktop_web_ui.DesktopWebBridge.__new__(desktop_web_ui.DesktopWebBridge)
        bridge._developer_mode_enabled = lambda: True
        fake = FakeBridge()
        with mock.patch("docfit_app.library_bridge.LibraryBridge", return_value=fake):
            result = bridge.notebook({"cmd": "nb_list"})
        self.assertTrue(result["ok"])
        self.assertEqual(fake.calls[0]["cmd"], "nb_list")


if __name__ == "__main__":
    unittest.main()
