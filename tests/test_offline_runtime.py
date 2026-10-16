"""폐쇄망 운영: 기본 폐쇄망 모드, 앱 꾸러미 kordoc 설치·사용, 외부 접속 차단."""
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock
import zipfile

from docfit_core import kordoc_bridge as kb
from docfit_core import kordoc_runtime as kr
from docfit_core import network_policy as np_

VERSION = kb.KORDOC_VERSION


def make_pack(path, version=VERSION, extra=(), node=True):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("runtime.json", json.dumps({"kordoc": version, "node": "22.23.3"}))
        if node:
            archive.writestr("node/node.exe", b"MZ fake node")
        archive.writestr("app/node_modules/kordoc/dist/cli.js", "console.log('4.21.30')")
        for name, data in extra:
            archive.writestr(name, data)
    return path


class OfflineRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        env = {"APPDATA": str(self.root / "roaming"), "LOCALAPPDATA": str(self.root / "local")}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        for key in ("DOCFIT_OFFLINE", "DOCFIT_KORDOC_BIN", "DOCFIT_ALLOW_NPX_DOWNLOAD"):
            os.environ.pop(key, None)
        self.app = self.root / "app"
        self.app.mkdir()
        app_patch = mock.patch.object(kr, "app_directory", return_value=self.app)
        app_patch.start()
        self.addCleanup(app_patch.stop)

    def test_offline_mode_is_default_and_follows_settings_and_override(self):
        self.assertTrue(np_.offline_mode())
        settings = np_.settings_folder() / "settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text(json.dumps({"offline_mode": False}), encoding="utf-8")
        self.assertFalse(np_.offline_mode())
        with mock.patch.dict(os.environ, {"DOCFIT_OFFLINE": "1"}):
            self.assertTrue(np_.offline_mode())
        settings.write_text("{broken", encoding="utf-8")
        self.assertTrue(np_.offline_mode())

    def test_pack_next_to_app_installs_once_and_is_found(self):
        make_pack(self.app / kr.RUNTIME_PACK_NAME)
        self.assertIsNone(kr.find_runtime(VERSION))
        self.assertEqual(kb.engine_status()["available"], True)
        node, cli = kr.ensure_runtime(VERSION)
        self.assertTrue(Path(node).is_file() and Path(cli).is_file())
        self.assertTrue(Path(node).is_relative_to(kr.installed_root() / VERSION))
        self.assertEqual(kr.find_runtime(VERSION), (node, cli))
        self.assertIn("앱에 포함된", kb.engine_status()["reason"])
        self.assertEqual(kb._kordoc_command(), [node, cli])
        self.assertFalse(kb.ocr_available())

    def test_runtime_folder_next_to_app_is_used_without_installing(self):
        folder = self.app / kr.RUNTIME_FOLDER_NAME
        with zipfile.ZipFile(make_pack(self.root / "p.zip")) as archive:
            archive.extractall(folder)
        node, _ = kr.find_runtime(VERSION)
        self.assertTrue(Path(node).is_relative_to(folder))
        self.assertFalse(kr.installed_root().exists())

    def test_unsafe_or_mismatched_packs_are_rejected(self):
        cases = {
            "traversal": make_pack(self.root / "a.zip", extra=[("../escape.txt", "x")]),
            "absolute": make_pack(self.root / "b.zip", extra=[("/abs.txt", "x")]),
            "drive": make_pack(self.root / "c.zip", extra=[("C:/win.txt", "x")]),
            "version": make_pack(self.root / "d.zip", version="0.0.1"),
            "no-node": make_pack(self.root / "e.zip", node=False),
        }
        for name, pack in cases.items():
            with self.subTest(name), self.assertRaises(kr.RuntimePackError):
                kr.install_pack(pack, VERSION, self.root / "install")
        self.assertFalse((self.root / "escape.txt").exists())
        self.assertFalse((self.root / "install" / VERSION).exists())
        self.assertEqual([p.name for p in (self.root / "install").iterdir() if p.suffix != ".lock"], [])  # 반쯤 푼 폴더도 남기지 않는다

    def test_offline_mode_never_downloads_with_npx(self):
        with mock.patch.dict(os.environ, {"DOCFIT_ALLOW_NPX_DOWNLOAD": "1"}), \
                mock.patch.object(kb, "_node_major", return_value=22), \
                mock.patch.object(kb, "_local_kordoc", return_value=None), \
                mock.patch.object(kb, "_npx_command", side_effect=AssertionError("npx used")):
            with self.assertRaisesRegex(kb.KordocUnavailableError, kr.RUNTIME_PACK_NAME):
                kb._kordoc_command()
            self.assertFalse(kb.engine_status()["available"])

    def test_kordoc_runs_with_offline_environment_and_local_model_cache(self):
        completed = mock.Mock(returncode=0, stdout="4.21.30", stderr="")
        with mock.patch.object(kb, "_kordoc_command", return_value=["node", "cli.js"]), \
                mock.patch.object(kb.subprocess, "run", return_value=completed) as run:
            kb.run_kordoc(["--version"])
        env = run.call_args.kwargs["env"]
        self.assertEqual(env["KORDOC_OFFLINE"], "1")
        self.assertEqual(env["ORT_DISABLE_TELEMETRY"], "1")
        self.assertEqual(env["KORDOC_MODEL_CACHE"], str(kr.model_cache_dir()))

    def test_image_input_without_ocr_gives_a_clear_message(self):
        make_pack(self.app / kr.RUNTIME_PACK_NAME)
        image = self.root / "scan.jpg"
        image.write_bytes(b"\xff\xd8\xff")
        with mock.patch.object(kb, "run_kordoc", side_effect=AssertionError("kordoc started")):
            with self.assertRaisesRegex(kb.KordocUnavailableError, "글자 인식"):
                kb.convert_to_hwpx(image, self.root / "scan.hwpx")


class OfflineSettingsTests(unittest.TestCase):
    def test_offline_setting_is_listed_and_defaults_on(self):
        from docfit_app.configuration_service import fields
        field = next(item for item in fields() if item["key"] == "offline_mode")
        self.assertEqual((field["type"], field["default"], field["group"]), ("boolean", True, "네트워크"))

    def test_update_check_does_not_touch_network_in_offline_mode(self):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"), run_name="offline_update")
        gui = ns["HwpAutoDocFitGUI"]
        notices = []
        status = mock.Mock()
        fake = mock.Mock(settings_toplevel=None, status_var=status,
                         _알림=lambda *args, **kwargs: notices.append(args))
        with mock.patch.dict(os.environ, {"DOCFIT_OFFLINE": "1"}), \
                mock.patch.object(ns["threading"], "Thread", side_effect=AssertionError("network thread")):
            gui._자동업데이트_확인_시작(fake)
            self.assertEqual(notices, [])
            gui._자동업데이트_확인_시작(fake, 수동=True)
        self.assertIn("폐쇄망", notices[0][2])


if __name__ == "__main__":
    unittest.main()
