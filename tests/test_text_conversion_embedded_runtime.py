import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from docfit_core import file_conversion as fc, kordoc_runtime as kr
from tests.test_offline_runtime import make_pack, VERSION


class TextConversionTests(unittest.TestCase):
    def test_text_encoding_and_markdown_are_generated_without_parser(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            fixture=Path(__file__).resolve().parents[1]/"resources/서식예시/기본 서식.hwpx"
            for ext,encoding in [(".md","utf-8"),(".txt","cp949"),(".txt","utf-16")]:
                source=root/("원본"+ext);source.write_text("# 제목\n한글 본문",encoding=encoding)
                target=root/("결과"+encoding+ext+".hwpx");original=source.read_bytes()
                def generate(markdown,preset,output):
                    text=Path(markdown).read_text(encoding="utf-8")
                    self.assertIn("한글 본문",text)
                    self.assertIn("# 제목" if ext==".md" else "\\# 제목",text)
                    shutil.copyfile(fixture,output)
                with patch("docfit_core.kordoc_bridge.generate_hwpx",side_effect=generate),patch("docfit_core.kordoc_bridge.parse_document",side_effect=AssertionError("must not parse text")):
                    self.assertTrue(fc.convert_input_to_hwpx(source,target).samefile(target))
                self.assertEqual(source.read_bytes(),original)
                with self.assertRaises(ValueError):fc.convert_input_to_hwpx(source,target)

    def test_hwpx_export_and_no_overwrite(self):
        source=Path(__file__).resolve().parents[1]/"resources/서식예시/기본 서식.hwpx"
        with tempfile.TemporaryDirectory() as folder:
            for ext in ("txt","md"):
                target=Path(folder)/("결과."+ext)
                fc.convert_hwpx_to_text(source,target)
                self.assertTrue(target.is_file())
                before=target.read_bytes()
                with self.assertRaises(ValueError):fc.convert_hwpx_to_text(source,target)
                self.assertEqual(target.read_bytes(),before)

    def test_readiness_has_text_results_without_external_tools(self):
        from desktop_web_ui import DesktopWebBridge
        bridge=DesktopWebBridge.__new__(DesktopWebBridge)
        bridge._conversion_prerequisites=lambda:{"kordoc":{"available":False},"pandoc":False,"hwp_com":False,"ocr":False}
        values={v["format"]:v for v in bridge._conversion_targets(["report.hwpx"])}
        self.assertTrue(values["txt"]["enabled"]);self.assertTrue(values["md"]["enabled"])
        self.assertFalse(values["pdf"]["enabled"])
        self.assertFalse(next(v for v in bridge._conversion_targets(["draft.md"]) if v["format"]=="txt")["enabled"])


class EmbeddedRuntimeTests(unittest.TestCase):
    def test_embedded_pack_is_saved_installed_and_reused_offline(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);bundle=root/"bundle";(bundle/"resources").mkdir(parents=True)
            pack=make_pack(bundle/"resources"/kr.RUNTIME_PACK_NAME)
            pack.with_name(pack.name+".sha256").write_text(hashlib.sha256(pack.read_bytes()).hexdigest()+"  "+pack.name)
            home=root/"C_HWP_AUTODOCFIT";fallback=root/"user"/"kordoc-runtime"
            with patch.object(kr.sys,"frozen",True,create=True),patch.object(kr.sys,"_MEIPASS",str(bundle),create=True),patch.object(kr,"deployment_home",return_value=home),patch.object(kr,"user_installed_root",return_value=fallback):
                node,cli=kr.deploy_embedded_runtime(VERSION)
                self.assertTrue(Path(node).is_relative_to(home))
                self.assertEqual((home/kr.RUNTIME_PACK_NAME).read_bytes(),pack.read_bytes())
                self.assertEqual(kr.deploy_embedded_runtime(VERSION),(node,cli))
                pack.write_bytes(b"corrupted")
                with self.assertRaises(kr.RuntimePackError):kr.deploy_embedded_runtime(VERSION)

    def test_permission_failure_falls_back_to_user_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);pack=make_pack(root/kr.RUNTIME_PACK_NAME)
            pack.with_name(pack.name+".sha256").write_text(hashlib.sha256(pack.read_bytes()).hexdigest())
            forbidden=root/"not-a-folder";forbidden.write_text("keep")
            user=root/"user"/"kordoc-runtime"
            with patch.object(kr,"embedded_pack",return_value=pack),patch.object(kr,"deployment_home",return_value=forbidden),patch.object(kr,"user_installed_root",return_value=user):
                node,_=kr.deploy_embedded_runtime(VERSION)
                self.assertTrue(Path(node).is_relative_to(user))
                self.assertEqual(forbidden.read_text(),"keep")


class TextRenderingTests(unittest.TestCase):
    def test_txt_md_pdf_png_jpg_use_generated_hwpx_and_preserve_source(self):
        from tests.test_file_conversion import FileConversionTests
        fixture=Path(__file__).resolve().parents[1]/"resources/서식예시/기본 서식.hwpx"
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for ext in ("txt","md"):
                source=root/("원본."+ext);source.write_text("# 제목\n한글 본문",encoding="utf-8")
                original=source.read_bytes()
                for output in ("pdf","png","jpg"):
                    target=root/(ext+"-결과."+output)
                    with patch("docfit_core.kordoc_bridge.generate_hwpx",side_effect=lambda md,preset,path:shutil.copyfile(fixture,path)):
                        action=fc.convert_to_pdf if output=="pdf" else fc.convert_to_images
                        result=action(FileConversionTests._pdf_app(1),source,target)
                    self.assertTrue(Path(result).is_file())
                    self.assertEqual(source.read_bytes(),original)
                    magic=target.read_bytes()
                    self.assertTrue(magic.startswith({"pdf":b"%PDF-","png":b"\x89PNG","jpg":b"\xff\xd8"}[output]))


class TextMarkupPreservationTests(unittest.TestCase):
    def test_markdown_table_keeps_cell_pipes_and_line_breaks(self):
        from docfit_core.hwpx import _markdown_table
        rendered = _markdown_table([["항목", "본문"], ["A|B", "첫 줄\n둘째 줄"]])
        self.assertIn("A\\|B", rendered)
        self.assertIn("첫 줄<br>둘째 줄", rendered)

    def test_plain_text_punctuation_is_not_converted_to_markdown_lists(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"source.txt";source.write_text("1. 접수\n- 참고\n+ 추가",encoding="utf-8")
            fixture=Path(__file__).resolve().parents[1]/"resources/서식예시/기본 서식.hwpx"
            def generate(markdown,preset,output):
                text=Path(markdown).read_text(encoding="utf-8")
                self.assertIn(r"1\. 접수",text)
                self.assertIn(r"\- 참고",text)
                self.assertIn(r"\+ 추가",text)
                shutil.copyfile(fixture,output)
            with patch("docfit_core.kordoc_bridge.generate_hwpx",side_effect=generate):
                fc.convert_input_to_hwpx(source,source.with_suffix(".hwpx"))
