import tempfile
import unittest
from pathlib import Path
from unittest import mock
from zipfile import ZIP_DEFLATED, ZipFile

from docfit_core.file_conversion import (
    CONVERSION_INPUTS, convert_hwpx_to_pdf, convert_input_to_hwpx, convert_to_images,
    convert_to_pandoc_format, convert_to_pdf, output_path_for,
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

    def test_html_input_and_output_format_are_available(self):
        from docfit_core.file_conversion import CONVERSION_OUTPUTS
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.html"
            source.write_text("<h1>Example</h1>", encoding="utf-8")
            self.assertIn(".html", CONVERSION_INPUTS)
            self.assertIn(".htm", CONVERSION_INPUTS)
            self.assertIn("html", CONVERSION_OUTPUTS)
            self.assertEqual(output_path_for(source, "html").suffix, ".html")

    def test_html_to_html_uses_pandoc_without_kordoc_parser(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.html"
            source.write_text("<h1>Safe input</h1>", encoding="utf-8")
            target = Path(folder) / "result.html"

            def run(args, **kwargs):
                self.assertIn("--from=html", args)
                self.assertIn("--to=html5", args)
                self.assertIn("--standalone", args)
                self.assertIn("--embed-resources", args)
                Path(args[args.index("--output") + 1]).write_text("<!DOCTYPE html><h1>Safe input</h1>", encoding="utf-8")
                return mock.Mock(returncode=0, stdout="", stderr="")

            with (mock.patch("docfit_core.kordoc_bridge.parse_document", side_effect=AssertionError("HTML should be parsed directly")),
                  mock.patch("docfit_core.file_conversion.subprocess.run", side_effect=run)):
                self.assertEqual(convert_to_pandoc_format(source, target, "bundled-pandoc"), target)
            self.assertIn("Safe input", target.read_text(encoding="utf-8"))

    def test_html_input_converts_to_document_and_text_targets(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.html"
            source.write_text("<h1>Round trip</h1>", encoding="utf-8")
            for extension, expected in (("docx", "docx"), ("epub", "epub3"),
                                        ("md", "markdown"), ("txt", "plain")):
                target = Path(folder) / f"result.{extension}"

                def run(args, **kwargs):
                    self.assertIn("--from=html", args)
                    self.assertIn(f"--to={expected}", args)
                    Path(args[args.index("--output") + 1]).write_text("converted", encoding="utf-8")
                    return mock.Mock(returncode=0, stdout="", stderr="")

                with mock.patch("docfit_core.file_conversion.subprocess.run", side_effect=run):
                    self.assertEqual(convert_to_pandoc_format(source, target, "bundled-pandoc"), target)
                self.assertEqual(target.read_text(encoding="utf-8"), "converted")

    def test_html_to_hwpx_uses_pandoc_markdown_then_generator(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.html"
            source.write_text("<h1>Report</h1>", encoding="utf-8")
            target = Path(folder) / "result.hwpx"

            def run(args, **kwargs):
                self.assertIn("--from=html", args)
                self.assertIn("--to=markdown", args)
                Path(args[args.index("--output") + 1]).write_text("# Report", encoding="utf-8")
                return mock.Mock(returncode=0, stdout="", stderr="")

            def generate(markdown, _preset, output, **_kwargs):
                self.assertEqual(Path(markdown).read_text(encoding="utf-8"), "# Report")
                with ZipFile(output, "w", ZIP_DEFLATED) as archive:
                    archive.writestr("Contents/header.xml", "<hh:head xmlns:hh='urn:head'/>")
                    archive.writestr("Contents/section0.xml", "<hs:sec xmlns:hs='urn:section'/>")

            with (mock.patch("docfit_core.file_conversion._pandoc_executable", return_value="bundled-pandoc"),
                  mock.patch("docfit_core.file_conversion.subprocess.run", side_effect=run),
                  mock.patch("docfit_core.kordoc_bridge.generate_hwpx", side_effect=generate)):
                self.assertEqual(convert_input_to_hwpx(source, target), target)
            self.assertTrue(target.is_file())

    def test_html_can_convert_to_pdf_through_hwpx_and_hwp_com(self):
        class App:
            def Open(self, path, fmt, _options):
                self.opened = Path(path)
                self.format = fmt
                return True

            def SaveAs(self, path, fmt, _options):
                Path(path).write_bytes(b"%PDF-1.7\\n")
                self.output_format = fmt
                return True

            def Clear(self, _flag):
                pass

        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.html"
            source.write_text("<h1>Report</h1>", encoding="utf-8")
            target = Path(folder) / "result.pdf"

            def to_hwpx(_source, intermediate):
                Path(intermediate).write_bytes(b"HWPX")
                return Path(intermediate)

            with mock.patch("docfit_core.file_conversion.convert_input_to_hwpx", side_effect=to_hwpx) as converter:
                self.assertTrue(convert_to_pdf(App(), source, target).samefile(target))
            self.assertEqual(converter.call_args.args[0], source)
            self.assertTrue(target.read_bytes().startswith(b"%PDF-"))

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
            self.assertTrue(convert_hwpx_to_pdf(app, source, target).samefile(target))
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
                self.assertTrue(convert_to_pdf(app, source, target).samefile(target))
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

    def test_pandoc_route_uses_bundled_executable_without_system_install(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "report.pdf"
            source.write_bytes(b"original")
            target = Path(folder) / "report.docx"

            def parse(_source, markdown, **_kwargs):
                Path(markdown).write_text("# Report", encoding="utf-8")

            def run(args, **kwargs):
                Path(args[args.index("--output") + 1]).write_bytes(b"DOCX")
                return mock.Mock(returncode=0, stdout="", stderr="")

            with (mock.patch("docfit_core.kordoc_bridge.parse_document", side_effect=parse),
                  mock.patch("docfit_core.kordoc_runtime.ensure_pandoc", return_value="runtime/pandoc/pandoc.exe"),
                  mock.patch("docfit_core.file_conversion.shutil.which", return_value=None),
                  mock.patch("docfit_core.file_conversion.subprocess.run", side_effect=run) as run_mock):
                self.assertEqual(convert_to_pandoc_format(source, target), target)

            self.assertEqual(run_mock.call_args.args[0][0], "runtime/pandoc/pandoc.exe")
            self.assertTrue(target.is_file())

    def test_hwp_pdf_direct_route_opens_hwp_without_external_parser(self):
        class App:
            def Open(self, path, fmt, options):
                self.format = fmt
                return True

            def SaveAs(self, path, fmt, options):
                Path(path).write_bytes(b"%PDF-1.7\n")
                return True

            def Clear(self, flag):
                pass

        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "report.hwp"
            source.write_bytes(b"original")
            app = App()
            with mock.patch("docfit_core.kordoc_bridge.convert_to_hwpx",
                            side_effect=AssertionError("external parser called")):
                convert_to_pdf(app, source, Path(folder) / "report.pdf")
            self.assertEqual(app.format, "HWP")
            self.assertEqual(source.read_bytes(), b"original")

    @staticmethod
    def _pdf_app(pages):
        from PIL import Image

        class App:
            def Open(self, *_args):
                return True

            def SaveAs(self, path, *_args):
                images = [Image.new("RGB", (200, 280), color) for color in ("white", "gray", "black")[:pages]]
                images[0].save(path, "PDF", save_all=True, append_images=images[1:])
                return True

            def Clear(self, flag):
                pass

        return App()

    def test_image_conversion_saves_each_page_in_a_new_folder(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "report.hwpx"
            source.write_bytes(b"original")
            target = output_path_for(source, "jpg")
            self.assertEqual(target.name, "report(JPG변경).jpg")
            result = convert_to_images(self._pdf_app(3), source, target)
            self.assertEqual(result, Path(folder) / "report(JPG변경)")
            pages = sorted(result.iterdir())
            self.assertEqual([page.name for page in pages],
                             [f"report(JPG변경)-00{index}.jpg" for index in (1, 2, 3)])
            with Image.open(pages[1]) as image:
                self.assertEqual(image.format, "JPEG")
            self.assertEqual(source.read_bytes(), b"original")
            # 같은 이름의 결과 폴더가 있으면 다음 번호 이름을 고른다.
            self.assertEqual(output_path_for(source, "jpg").name, "report(JPG변경) (2).jpg")

    def test_single_page_image_is_one_png_file_and_never_overwrites(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "memo.hwpx"
            source.write_bytes(b"original")
            target = output_path_for(source, "png")
            self.assertEqual(convert_to_images(self._pdf_app(1), source, target), target)
            with Image.open(target) as image:
                self.assertEqual(image.format, "PNG")
            with self.assertRaises(ValueError):
                convert_to_images(self._pdf_app(1), source, target)


if __name__ == "__main__":
    unittest.main()
