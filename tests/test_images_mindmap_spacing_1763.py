"""Image OCR preparation, runtime upgrades and actual unify-spacing dispatch."""
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from PIL import Image
from docfit_core import file_conversion as fc, kordoc_runtime as kr, kordoc_bridge as kb

ROOT = Path(__file__).resolve().parents[1]


class ImageConversionTests(unittest.TestCase):
    def test_image_formats_are_normalized_ocr_is_requested_and_originals_preserved(self):
        fixture = ROOT / "resources/서식예시/기본 서식.hwpx"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for suffix in ("png", "jpg", "webp", "bmp", "tiff", "gif"):
                with self.subTest(suffix=suffix):
                    source = root / ("원본." + suffix)
                    with Image.new("RGB", (180, 80), "white") as image:
                        image.save(source)
                    before = hashlib.sha256(source.read_bytes()).digest()
                    target = root / (suffix + ".hwpx")
                    def parse(source, target, **options):
                        self.assertTrue(options["ocr"])
                        with Image.open(source) as image:
                            self.assertEqual(image.format, "PNG")
                            self.assertEqual(image.mode, "RGB")
                        Path(target).write_text("인식된 한글", encoding="utf-8")
                    def generate(source, preset, target, **options):
                        self.assertEqual(Path(source).read_text(encoding="utf-8"), "인식된 한글")
                        shutil.copyfile(fixture, target)
                    with patch.object(kb, "ocr_available", return_value=True), patch.object(kb, "parse_document", side_effect=parse), patch.object(kb, "generate_hwpx", side_effect=generate):
                        self.assertEqual(fc.convert_input_to_hwpx(source, target), target)
                        with self.assertRaises(ValueError):
                            fc.convert_input_to_hwpx(source, target)
                    self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), before)

    def test_multiframe_order_blank_ocr_and_unavailable_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);source = root / "scan.tiff";target = root / "out.hwpx"
            a=Image.new("RGB",(100,50),"white");b=Image.new("RGB",(100,50),"black")
            a.save(source,save_all=True,append_images=[b]);a.close();b.close()
            calls=[]
            def parse(source, target, **kw):
                calls.append(Path(source).name)
                Path(target).write_text(str(len(calls)),encoding="utf-8")
            def generate(source, preset, target, **kw):
                self.assertEqual(Path(source).read_text(encoding="utf-8"),"1\n\n---\n\n2")
                shutil.copyfile(ROOT/"resources/서식예시/기본 서식.hwpx",target)
            with patch.object(kb,"ocr_available",return_value=True), patch.object(kb,"parse_document",side_effect=parse), patch.object(kb,"generate_hwpx",side_effect=generate):
                fc.convert_input_to_hwpx(source,target)
            self.assertEqual(calls,["frame-001.png","frame-002.png"])
            with patch.object(kb,"ocr_available",return_value=True), patch.object(kb,"parse_document",side_effect=lambda s,t,**k:Path(t).write_text("",encoding="utf-8")):
                with self.assertRaisesRegex(RuntimeError,"인식하지 못"):
                    fc.convert_input_to_hwpx(source,root/"empty.hwpx")
            self.assertFalse((root/"empty.hwpx").exists())
            with patch.object(kb,"ocr_available",return_value=False):
                with self.assertRaises(kb.KordocUnavailableError):
                    fc.convert_input_to_hwpx(source,root/"unavailable.hwpx")

    def test_image_readiness_requires_ocr_and_exposes_extra_formats(self):
        from desktop_web_ui import DesktopWebBridge
        bridge=DesktopWebBridge.__new__(DesktopWebBridge)
        for ready in (False,True):
            bridge._conversion_prerequisites=lambda:{"kordoc":{"available":True},"pandoc":False,"hwp_com":True,"ocr":ready}
            for suffix in fc.IMAGE_INPUT_EXTENSIONS:
                targets={v["format"]:v for v in bridge._conversion_targets(["scan"+suffix])}
                self.assertEqual(targets["hwpx"]["enabled"],ready,suffix)
                self.assertEqual(targets["png"]["enabled"],ready,suffix)


class RuntimeUpgradeTests(unittest.TestCase):
    def test_same_kordoc_version_old_pack_upgrades_to_ocr_revision(self):
        from tests.test_offline_runtime import make_pack, VERSION
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);install=root/"runtime";old=make_pack(root/"old.zip")
            destination=kr.install_pack(old,VERSION,install)
            new=root/"new.zip"
            with zipfile.ZipFile(old) as src,zipfile.ZipFile(new,"w") as dst:
                for name in src.namelist():
                    if name!="runtime.json":dst.writestr(name,src.read(name))
                dst.writestr("runtime.json",json.dumps({"kordoc":VERSION,"bundle_revision":"ocr-1","ocr":"ppocr-korean-v5"}))
                for name in kr.OCR_MODEL_FILES:dst.writestr("models/ppocr/"+name,b"new-model")
            self.assertEqual(kr.install_pack(new,VERSION,install),destination)
            self.assertEqual((destination/"models/ppocr/det.onnx").read_bytes(),b"new-model")
            with patch.object(kr,"app_directory",return_value=root/"app"),patch.object(kr,"installed_root",return_value=install):
                self.assertEqual(kr.model_cache_dir(),destination/"models")


class UnifySpacingDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns=runpy.run_path(str(ROOT/"hwp-auto-docfit.py"),run_name="import_check")

    def test_off_exclusion_runs_whole_body_even_if_unify_changes_nothing(self):
        fn=self.ns["_문서_처리_1회"]
        names=["서식통일_전체_적용","서식통일_표_전체_적용","본문_기존자간조정","본문_문장부호_처리",
               "컨트롤_내부_자간조정","컨트롤_내부_문장부호_처리","보고서_페이지수_맞춤_전체_적용"]
        for spacing in (False,True):
            for tables in (False,True):
                calls=[]
                replacements={name:(lambda *a,_name=name,**kw:calls.append(_name) or True) for name in names}
                with patch.dict(fn.__globals__,{**replacements,"작업_모드":"unify",
                    "선택_세부작업":{"unify_spacing":spacing,"table_unify":False,"page_layout_keep":False,"page_fit":False},
                    "서식통일_자간조정_사용":spacing,"표_자간조정_사용":tables,
                    "중단_요청됨":lambda:False,"단계표시":Mock(),"상태":Mock(),"로그":Mock(),
                    "hwp_run":Mock(),"순회_시작":Mock()}):
                    self.assertTrue(fn("원본.hwpx"))
                self.assertEqual("본문_기존자간조정" in calls,spacing)
                self.assertEqual("본문_문장부호_처리" in calls,spacing)
                self.assertEqual("컨트롤_내부_자간조정" in calls,spacing and tables)
                self.assertEqual(calls[0],"서식통일_전체_적용")
