"""HWP native conversion readiness across 32/64-bit Hancom registrations."""
from contextlib import nullcontext
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PIL import Image
from desktop_web_ui import DesktopWebBridge
from docfit_core import file_conversion as fc


class HwpFourFormatsTests(unittest.TestCase):
    def test_registration_in_either_registry_view_enables_all_four_native_formats(self):
        for registered in (0, 0x200, 0x100, None):
            calls = []
            def open_key(root, key, reserved, access):
                self.assertEqual(key, "HwpFrame.HwpObject")
                view = access & 0x300
                calls.append(view)
                if view != registered:
                    raise FileNotFoundError(key)
                return nullcontext()
            registry = SimpleNamespace(HKEY_CLASSES_ROOT=1, KEY_READ=0x20019,
                                       KEY_WOW64_32KEY=0x200, KEY_WOW64_64KEY=0x100,
                                       OpenKey=open_key)
            with patch("desktop_web_ui.os.name", "nt"), patch.dict(sys.modules, {"winreg": registry}):
                ready = DesktopWebBridge._hwp_com_available()
            self.assertEqual(ready, registered is not None)
            bridge = DesktopWebBridge.__new__(DesktopWebBridge)
            bridge._conversion_prerequisites = lambda: {
                "hwp_com": ready, "kordoc": {"available": False},
                "pandoc": False, "ocr": False}
            targets = {t["format"]: t for t in bridge._conversion_targets(["원본.HWP"])}
            for output in ("hwpx", "png", "jpg", "pdf"):
                self.assertEqual(targets[output]["enabled"], ready, (registered, output))
            if registered is None:
                self.assertEqual(calls, [0, 0x200, 0x100])

    def test_hwp_four_outputs_preserve_source_without_kordoc_or_pandoc(self):
        from tests.test_file_conversion import FileConversionTests
        fixture = Path(__file__).resolve().parents[1] / "resources/서식예시/기본 서식.hwpx"
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "원본.HWP"
            source.write_bytes(b"original hwp stand-in")
            original = source.read_bytes()
            for output in ("hwpx", "pdf", "png", "jpg"):
                with self.subTest(output=output):
                    app = FileConversionTests._pdf_app(2)
                    app.Open = Mock(wraps=app.Open)
                    if output == "hwpx":
                        app.SaveAs = lambda path, *_: shutil.copyfile(fixture, path)
                    action = fc.convert_hwp_to_hwpx if output == "hwpx" else (
                        fc.convert_to_pdf if output == "pdf" else fc.convert_to_images)
                    with patch("docfit_core.kordoc_bridge.run_kordoc",
                               side_effect=AssertionError("Native HWP conversion must not use kordoc")):
                        result = action(app, source, fc.output_path_for(source, output))
                    self.assertEqual(app.Open.call_args.args[1], "HWP")
                    if output in ("png", "jpg"):
                        images = sorted(result.iterdir())
                        self.assertEqual(len(images), 2)
                        for path in images:
                            with Image.open(path) as image:
                                self.assertEqual(image.format, "PNG" if output == "png" else "JPEG")
                    else:
                        self.assertTrue(result.is_file())
                    self.assertEqual(source.read_bytes(), original)
