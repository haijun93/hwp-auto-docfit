import csv
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from docfit_core import hwp_bulk

OLE = hwp_bulk.OLE_SIGNATURE + b"\0" * 64


def _hwpx(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/hwp+zip")
        z.writestr("Contents/header.xml", "<head/>")
        z.writestr("Contents/section0.xml", "<sec/>")


class FakeHwp:
    """Open: 암호 문서는 suspendpassword면 실패, 암호(responder.current)가 맞으면 성공."""

    def __init__(self, responder=None, password="pw"):
        self.responder, self.password, self.opened = responder, password, None
        self.calls = []

    def Open(self, path, fmt, arg):
        self.calls.append((Path(path).name, fmt, arg))
        name = Path(path).name
        if name.startswith("암호"):
            if "suspendpassword" in arg:
                return False
            return self.password in (self.responder.current if self.responder else [])
        if Path(path).read_bytes().startswith(b"DRM"):
            return False
        self.opened = path
        return True

    def SaveAs(self, path, fmt, arg):
        _hwpx(path)
        return True

    def Clear(self, option):
        self.calls.append(("Clear", option))

    def Quit(self):
        pass


class FindTests(unittest.TestCase):
    def test_skips_system_folders_existing_results_and_other_files(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            for rel in ("a.hwp", "sub/b.HWP", "sub/AppData/c.hwp", "Windows/d.hwp", "e.hwpx", "f.txt", "g.hwp"):
                (base / rel).parent.mkdir(parents=True, exist_ok=True)
                (base / rel).write_bytes(OLE)
            (base / "g.hwpx").write_bytes(b"x")
            found, skipped = hwp_bulk.find_hwp([base])
            self.assertEqual([p.name for p in found], ["a.hwp", "b.HWP"])
            self.assertEqual(skipped, 1)
            flat, _ = hwp_bulk.find_hwp([base], recursive=False)
            self.assertEqual([p.name for p in flat], ["a.hwp"])
            stop = threading.Event()
            stop.set()
            self.assertEqual(hwp_bulk.find_hwp([base], stop=stop)[0], [])

    def test_classify(self):
        with tempfile.TemporaryDirectory() as root:
            ole, old, drm = (Path(root) / n for n in ("1.hwp", "2.hwp", "3.hwp"))
            ole.write_bytes(OLE)
            old.write_bytes(b"HWP Document File V3.00 \x1a\x01\x02\x03\x04\x05")
            drm.write_bytes(b"SCDSA002" + b"\0" * 40)
            self.assertEqual([hwp_bulk.classify(p) for p in (ole, old, drm)], ["hwp", "hwp3", "protected"])
            self.assertEqual(hwp_bulk.classify(Path(root) / "missing.hwp"), "unreadable")


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _file(self, name, data=OLE):
        path = self.root / name
        path.write_bytes(data)
        return path

    def test_plain_password_and_drm(self):
        responder = hwp_bulk.DialogResponder(pid=None, passwords=["x", "pw"])
        responder.pid = 1  # 창 감시 스레드는 띄우지 않고 암호 순서만 시험한다
        app = FakeHwp(responder)
        plain = hwp_bulk.convert_one(app, self._file("일반.hwp"), responder)
        self.assertEqual(plain.status, "success")
        self.assertTrue(Path(plain.output).is_file())
        self.assertEqual(app.calls[0], ("일반.hwp", "HWP", "forceopen:true;suspendpassword:true"))
        locked = hwp_bulk.convert_one(app, self._file("암호.hwp"), responder)
        self.assertEqual(locked.status, "success")
        self.assertIn("같은 암호", locked.message)
        drm = hwp_bulk.convert_one(app, self._file("보안.hwp", b"DRM" + b"\0" * 40), responder)
        self.assertEqual((drm.status, drm.message), ("failed", hwp_bulk.MSG_DRM))
        again = hwp_bulk.convert_one(app, self.root / "일반.hwp", responder)
        self.assertEqual(again.status, "skipped")
        self.assertFalse(list(self.root.glob(".~docfit_*")))  # 임시 파일 남기지 않음
        self.assertIn(("Clear", 1), app.calls)  # 저장 묻지 않고 닫아 원본을 덮지 않는다

    def test_password_missing_or_wrong(self):
        responder = hwp_bulk.DialogResponder(pid=None, passwords=["nope"])
        responder.pid = 1
        result = hwp_bulk.convert_one(FakeHwp(responder), self._file("암호.hwp"), responder)
        self.assertEqual((result.status, result.message), ("failed", hwp_bulk.MSG_PASSWORD))
        result = hwp_bulk.convert_one(FakeHwp(), self._file("암호2.hwp"), None)
        self.assertEqual(result.message, hwp_bulk.MSG_PASSWORD)

    def test_run_bulk_writes_report(self):
        self._file("일반.hwp")
        self._file("암호.hwp")
        state = hwp_bulk.BulkState()
        with mock.patch.object(hwp_bulk, "hwp_pids", return_value=set()):
            results = hwp_bulk.run_bulk([self.root], app_factory=FakeHwp, state=state, stop=threading.Event(),
                                        report_dir=self.root / "report")
        self.assertEqual((state.phase, state.found, state.succeeded, state.failed), ("done", 2, 1, 1))
        self.assertEqual(len(results), 2)
        with open(state.report, encoding="utf-8-sig") as stream:
            rows = list(csv.reader(stream))
        self.assertEqual(rows[0], ["결과", "원본", "HWPX", "설명"])
        self.assertEqual(sorted(r[0] for r in rows[1:]), ["변환", "실패"])
        self.assertEqual(state.as_dict()["failures"][0]["message"], hwp_bulk.MSG_PASSWORD)


if __name__ == "__main__":
    unittest.main()
