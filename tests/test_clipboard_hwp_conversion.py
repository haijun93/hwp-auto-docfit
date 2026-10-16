import base64
import io
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from PIL import Image
from docfit_core.table_clipboard import cf_html, table_html
from docfit_core.file_conversion import convert_hwp_to_hwpx
from docfit_app.clipboard_service import copy_result


class ClipboardTests(unittest.TestCase):
    def test_cf_html_offsets_are_utf8_bytes(self):
        fragment = "<table><tr><td>한글 &amp; 본문</td></tr></table>"
        data = cf_html(fragment)
        values = dict((k.decode(), int(v)) for k,v in re.findall(rb"(StartHTML|EndHTML|StartFragment|EndFragment):(\d+)", data))
        self.assertEqual(data[values["StartFragment"]:values["EndFragment"]].decode(), fragment)
        self.assertEqual(values["EndHTML"], len(data))
        self.assertTrue(data[values["StartHTML"]:].startswith(b"<html>"))

    def test_table_is_editable_and_escapes_text(self):
        html, text=table_html({"kind":"grid","rows":[["제목","내용"],["<script>alert(1)</script>","본문"]]})
        self.assertEqual(html.count("<tr>"),2)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("제목\t내용",text)

    def test_all_table_kinds(self):
        for spec in [
            {"kind":"flow","steps":[{"title":"접수"},{"title":"선정"}]},
            {"kind":"flow","direction":"vertical","steps":[{"title":"접수"},{"title":"선정"}]},
            {"kind":"org","root":"부서","units":[{"title":"팀","detail":"담당"}]},
            {"kind":"bar","title":"사업","note":"2026"},
        ]:
            with self.subTest(kind=spec["kind"]):
                self.assertIn("<table",table_html(spec)[0])

    def test_windows_formats_survive_return_and_clipboard_always_closes(self):
        cb=MagicMock();cb.RegisterClipboardFormat.return_value=50000
        with patch("docfit_app.clipboard_service.sys.platform","win32"),patch.dict("sys.modules",{"win32clipboard":cb}):
            self.assertTrue(copy_result({"kind":"table","spec":{"kind":"grid","rows":[["한글"]]}})["copied"])
            self.assertEqual(cb.SetClipboardData.call_args_list[-1].args,(13,"한글"))
            cb.CloseClipboard.assert_called_once()
            cb.reset_mock();cb.SetClipboardData.side_effect=RuntimeError("write failed")
            with self.assertRaises(RuntimeError):copy_result({"kind":"table","spec":{"kind":"grid","rows":[["내용"]]}})
            cb.CloseClipboard.assert_called_once()

    def test_picture_has_dib_and_png_formats(self):
        stream=io.BytesIO();Image.new("RGBA",(2,2),(255,0,0,80)).save(stream,format="PNG")
        cb=MagicMock();cb.RegisterClipboardFormat.return_value=50001
        with patch("docfit_app.clipboard_service.sys.platform","win32"),patch.dict("sys.modules",{"win32clipboard":cb}):
            result=copy_result({"kind":"png","base64":base64.b64encode(stream.getvalue()).decode()})
        self.assertEqual(result["format"],"image")
        self.assertEqual(cb.SetClipboardData.call_args_list[0].args[0],8)
        self.assertEqual(cb.SetClipboardData.call_args_list[1].args[1],stream.getvalue())


class HwpConversionTests(unittest.TestCase):
    def test_native_save_preserves_original_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"원본.hwp";source.write_bytes(b"original")
            target=source.with_suffix(".hwpx")
            app=MagicMock()
            app.SaveAs.side_effect=lambda path,*_: shutil.copyfile(Path(__file__).resolve().parents[1]/"resources/서식예시/기본 서식.hwpx",path)
            self.assertTrue(convert_hwp_to_hwpx(app,source,target).samefile(target))
            self.assertEqual(source.read_bytes(),b"original")
            app.Run.assert_called_with("FileClose")
            before=target.read_bytes()
            with self.assertRaises(ValueError):convert_hwp_to_hwpx(app,source,target)
            self.assertEqual(target.read_bytes(),before)

    def test_invalid_output_is_not_published_and_session_closes(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"원본.hwp";source.write_bytes(b"original")
            target=source.with_suffix(".hwpx");app=MagicMock()
            app.SaveAs.side_effect=lambda path,*_: Path(path).write_bytes(b"not hwpx")
            with self.assertRaises(Exception):convert_hwp_to_hwpx(app,source,target)
            self.assertFalse(target.exists());app.Run.assert_called_with("FileClose")
            self.assertEqual(list(Path(folder).iterdir()),[source])


class ConversionReadinessTests(unittest.TestCase):
    def test_hwp_hwpx_requires_hancom_not_external_engine(self):
        from desktop_web_ui import DesktopWebBridge
        bridge = DesktopWebBridge.__new__(DesktopWebBridge)
        bridge._conversion_prerequisites = lambda: {"kordoc":{"available":False}, "pandoc":False, "hwp_com":True, "ocr":False}
        target = next(x for x in bridge._conversion_targets(["source.hwp"]) if x["format"] == "hwpx")
        self.assertTrue(target["enabled"])
        self.assertIn("HWP→HWPX", target["reason"])
        mixed = next(x for x in bridge._conversion_targets(["source.hwp", "source.docx"]) if x["format"] == "hwpx")
        self.assertFalse(mixed["enabled"])
        bridge._conversion_prerequisites = lambda: {"kordoc":{"available":True}, "pandoc":False, "hwp_com":False, "ocr":False}
        target = next(x for x in bridge._conversion_targets(["source.hwp"]) if x["format"] == "hwpx")
        self.assertFalse(target["enabled"])

    def test_bridge_dispatches_clipboard_on_owner_thread(self):
        from desktop_web_ui import DesktopWebBridge
        from types import SimpleNamespace
        bridge = DesktopWebBridge.__new__(DesktopWebBridge)
        store = SimpleNamespace(_path=Path(tempfile.gettempdir())/"docfit-test-settings.json")
        bridge.gui = SimpleNamespace(_준말_서비스=lambda: SimpleNamespace(settings=store))
        calls=[]
        bridge._tk=lambda callback: (calls.append(True), callback())[1]
        with patch("docfit_app.clipboard_service.copy_result", return_value={"copied":True}) as copy:
            result=bridge.flow_editor("copy_result", {"kind":"table","spec":{"kind":"grid","rows":[["한글"]]}})
        self.assertTrue(result["copied"]);copy.assert_called_once();self.assertEqual(len(calls),2)
