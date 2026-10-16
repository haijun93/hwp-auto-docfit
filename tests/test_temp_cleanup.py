"""오류·중단으로 남는 문서 사본 임시 폴더를 남기지 않는다."""
import os
from pathlib import Path
import queue
import runpy
import tempfile
import time
import unittest
from unittest.mock import patch

from tests.gui_support import gui_root

SOURCE = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"


class TempCleanupTest(unittest.TestCase):
    def test_startup_sweep_removes_old_hwp_conversion_and_sample_copies(self):
        ns = runpy.run_path(str(SOURCE), run_name="temp_cleanup_sweep")
        sweep = ns["이전_작업_임시폴더_정리"]
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            old_hwp = root / "docfit_hwp_to_hwpx_old"
            old_sample = root / "docfit_sample_old"
            fresh_hwp = root / "docfit_hwp_to_hwpx_fresh"
            for folder in (old_hwp, old_sample, fresh_hwp):
                folder.mkdir()
                (folder / "문서.hwpx").write_bytes(b"copy of a user document")
            past = time.time() - 3600
            for folder in (old_hwp, old_sample):
                os.utime(folder, (past, past))
            with patch.object(sweep.__globals__["tempfile"], "gettempdir", return_value=str(root)):
                self.assertEqual(sweep(), 2)
            self.assertFalse(old_hwp.exists())
            self.assertFalse(old_sample.exists())
            self.assertTrue(fresh_hwp.exists())   # 지금 실행 중일 수 있는 폴더는 건드리지 않는다

    def test_failed_format_analysis_leaves_no_sample_folder(self):
        with tempfile.TemporaryDirectory(prefix="hwp-docfit-temp-") as folder, \
                patch.dict(os.environ, {"APPDATA": folder}):
            ns = runpy.run_path(str(SOURCE), run_name="temp_cleanup_analysis")
            root = gui_root(ns["TkinterDnD"].Tk, ns)
            root.withdraw()
            try:
                app = ns["HwpAutoDocFitGUI"](root)
                scratch = Path(folder) / "tmp"
                scratch.mkdir()
                globals_ = app._서식_분석_시작.__globals__

                def no_sample(path, keep=None):
                    return {"format": {}}   # 표본 파일을 만들지 못한 분석

                def failed(path, keep=None):
                    raise RuntimeError("분석 실패")

                for analysis, expected in ((no_sample, "format_copied"), (failed, "format_copy_error")):
                    with patch.dict(globals_, {"한글파일_서식_분석": analysis, "알파_서식예시폴더_사용": True}), \
                            patch.object(tempfile, "tempdir", str(scratch)):
                        app._서식_분석_시작(str(Path(folder) / "예시.hwpx"), 이름묻기=False)
                        event = ns["gui_queue"].get(timeout=10)
                        while event[0] not in ("format_copied", "format_copy_error"):
                            event = ns["gui_queue"].get(timeout=10)
                    self.assertEqual(event[0], expected)
                    for _ in range(50):   # 작업 스레드의 finally 정리가 끝날 때까지 잠시 기다린다
                        if not list(scratch.glob("docfit_sample_*")):
                            break
                        time.sleep(0.05)
                    self.assertEqual(list(scratch.glob("docfit_sample_*")), [], analysis.__name__)
                    app._서식분석중 = False
            finally:
                root.destroy()


if __name__ == "__main__":
    unittest.main()
