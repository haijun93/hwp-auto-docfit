import tempfile
import unittest
from pathlib import Path
from unittest import mock
from zipfile import ZIP_DEFLATED, ZipFile

from docfit_core.file_conversion import (
    convert_hwpx_to_pdf, convert_to_pandoc_format, convert_to_pdf, output_path_for,
)
from docfit_core.kordoc_bridge import SUPPORTED_INPUT_EXTENSIONS, convert_to_hwpx


class FileConversionTests(unittest.TestCase):
    def test_output_path_uses_unique_names_and_supported_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "report.xlsx"
            source.write_bytes(b"source")
            first = output_path_for(source, "hwpx")
            self.assertEqual(first.name, "report(HWPX변경).hwpx")
            first.touch()
            self.assertEqual(output_path_for(source, "hwpx").name, "report(HWPX변경) (2).hwpx")

    def test_pdf_output_path_supports_any_kordoc_input(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "report.pdf"
            source.write_bytes(b"pdf")
            self.assertEqual(output_path_for(source, "pdf").name, "report(PDF변경).pdf")
            unsupported = Path(folder) / "archive.zip"
            unsupported.write_bytes(b"zip")
            with self.assertRaises(ValueError):
                output_path_for(unsupported, "pdf")

    def test_kordoc_extension_allowlist_matches_expected_formats(self):
        self.assertEqual(SUPPORTED_INPUT_EXTENSIONS, {
            ".hwp", ".hwpx", ".hml", ".pdf", ".xls", ".xlsx", ".docx", ".pptx",
            ".png", ".jpg", ".jpeg", ".webp",
        })

    def test_convert_to_hwpx_parses_then_generates_without_touching_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sheet.xlsx"
            source.write_bytes(b"original")
            target = Path(folder) / "sheet(HWPX변경).hwpx"

            def parse(src, markdown, **kwargs):
                Path(markdown).write_text("# parsed", encoding="utf-8")
                return Path(markdown)

            def generate(markdown, preset, output, *, image_dir=None):
                with ZipFile(output, "w", ZIP_DEFLATED) as archive:
                    archive.writestr("Contents/header.xml", "<hh:head xmlns:hh='urn:head'/>")
                    archive.writestr("Contents/section0.xml", "<hs:sec xmlns:hs='urn:section'/>")
                return Path(output)

            with mock.patch("docfit_core.kordoc_bridge.parse_document", side_effect=parse) as parse_mock, \
                    mock.patch("docfit_core.kordoc_bridge.generate_hwpx", side_effect=generate) as generate_mock:
                result = convert_to_hwpx(source, target)

            self.assertEqual(result, target)
            self.assertEqual(source.read_bytes(), b"original")
            self.assertTrue(target.is_file())
            from docfit_core.hwpx import validate_hwpx
            self.assertEqual(validate_hwpx(target)["entry_count"], 2)
            self.assertEqual(parse_mock.call_args.kwargs["output_format"], "markdown")
            self.assertEqual(parse_mock.call_args.kwargs["ocr"], False)
            self.assertEqual(generate_mock.call_args.args[1], "보고서")

    def test_convert_to_hwpx_rejects_malformed_generated_package(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sheet.xlsx"
            source.write_bytes(b"original")
            target = Path(folder) / "sheet.hwpx"

            def parse(_source, markdown, **_kwargs):
                Path(markdown).write_text("# parsed", encoding="utf-8")

            def generate(_markdown, _preset, output, **_kwargs):
                Path(output).write_bytes(b"not a zip")

            with mock.patch("docfit_core.kordoc_bridge.parse_document", side_effect=parse), \
                    mock.patch("docfit_core.kordoc_bridge.generate_hwpx", side_effect=generate):
                with self.assertRaisesRegex(RuntimeError, "올바른 HWPX 문서"):
                    convert_to_hwpx(source, target)
            self.assertFalse(target.exists())

    def test_pdf_conversion_checks_signature_and_preserves_source(self):
        class App:
            def Open(self, *_args):
                return True

            def SaveAs(self, path, *_args):
                self.assert_target_absent = not Path(path).exists()
                Path(path).write_bytes(b"%PDF-1.7\n")
                return True

        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "report.hwpx"
            source.write_bytes(b"original")
            target = Path(folder) / "report.pdf"
            app = App()
            self.assertEqual(convert_hwpx_to_pdf(app, source, target), target)
            self.assertTrue(app.assert_target_absent)
            self.assertTrue(target.read_bytes().startswith(b"%PDF-"))
            self.assertEqual(source.read_bytes(), b"original")
            with self.assertRaises(ValueError):
                convert_hwpx_to_pdf(App(), source, target)

    def test_non_hwpx_pdf_route_closes_intermediate_before_temp_cleanup(self):
        class App:
            opened = None

            def Open(self, path, *_args):
                self.opened = Path(path)
                self.assert_exists_during_open = self.opened.is_file()
                return True

            def SaveAs(self, path, *_args):
                Path(path).write_bytes(b"%PDF-1.7\n")
                return True

            def Run(self, command):
                if command == "FileClose":
                    self.opened = None

        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "scan.pdf"
            source.write_bytes(b"pdf source")
            target = Path(folder) / "scan(PDF변경).pdf"

            def fake_hwpx(_source, destination):
                Path(destination).write_bytes(b"intermediate")
                return Path(destination)

            app = App()
            with mock.patch("docfit_core.kordoc_bridge.convert_to_hwpx", side_effect=fake_hwpx):
                self.assertEqual(convert_to_pdf(app, source, target), target)
            self.assertTrue(app.assert_exists_during_open)
            self.assertIsNone(app.opened)
            self.assertTrue(target.read_bytes().startswith(b"%PDF-"))
            self.assertEqual(source.read_bytes(), b"pdf source")

    def test_hwpx_pdf_direct_route_never_calls_external_parser_and_clears_session(self):
        class App:
            cleared = False

            def Open(self, path, fmt, options):
                self.opened = path
                self.format = fmt
                return True

            def SaveAs(self, path, fmt, options):
                Path(path).write_bytes(b"%PDF-1.7\n")
                return True

            def Clear(self, flag):
                self.cleared = flag == 1

        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.hwpx"
            source.write_bytes(b"original")
            target = Path(folder) / "new-folder" / "result.pdf"
            app = App()
            with mock.patch("docfit_core.kordoc_bridge.convert_to_hwpx", side_effect=AssertionError("external parser called")):
                self.assertEqual(convert_to_pdf(app, source, target), target.resolve())
            self.assertTrue(target.is_file())
            self.assertTrue(app.cleared)
            self.assertEqual(app.format, "HWPX")
            self.assertEqual(source.read_bytes(), b"original")

    def test_pandoc_route_uses_kordoc_markdown_and_safe_argument_list(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "report.pdf"
            source.write_bytes(b"original")
            target = Path(folder) / "report(EPUB변경).epub"

            def parse(_source, markdown, **_kwargs):
                Path(markdown).write_text("# Report", encoding="utf-8")

            def run(args, **kwargs):
                output = Path(args[args.index("--output") + 1])
                output.write_bytes(b"EPUB")
                return mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch("docfit_core.kordoc_bridge.parse_document", side_effect=parse), \
                    mock.patch("docfit_core.file_conversion.shutil.which", return_value="pandoc.exe"), \
                    mock.patch("docfit_core.file_conversion.subprocess.run", side_effect=run) as run_mock:
                self.assertEqual(convert_to_pandoc_format(source, target), target)

            self.assertEqual(target.read_bytes(), b"EPUB")
            args = run_mock.call_args.args[0]
            self.assertIn("--to=epub3", args)
            self.assertFalse(run_mock.call_args.kwargs["shell"])
            self.assertEqual(source.read_bytes(), b"original")


if __name__ == "__main__":
    unittest.main()
