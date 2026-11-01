import os
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path

from docfit_core.timemachine import Rules, Store, cloud_only, default_roots, scan_root, scan_roots


def touch(path, when=None, text="x"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if when is not None:
        os.utime(path, (when, when))
    return path


class RulesTests(unittest.TestCase):
    def test_extensions_and_exclusions(self):
        rules = Rules()
        for name in ("보고서.hwpx", "a.HWP", "표.xlsx", "b.pdf", "사진.JPG", "메모.txt"):
            self.assertFalse(rules.skip_file(name), name)
        for name in ("~$보고서.docx", "~WRL0001.tmp", "a.tmp", "x.crdownload", "Thumbs.db", "desktop.ini",
                     "a.asv", "a.bak", "setup.exe", "a.zip", "a(무결성검사).json", "b.heic"):
            self.assertTrue(rules.skip_file(name), name)
        self.assertTrue(rules.skip_file("a.pdf", 2))  # 숨김
        self.assertFalse(Rules(include_hidden=True).skip_file("a.pdf", 2))
        for name in ("AppData", "appdata", "node_modules", ".git", "$Recycle.Bin", "Cache", ".hidden"):
            self.assertTrue(rules.skip_dir(name), name)
        self.assertFalse(rules.skip_dir("2026 업무"))
        self.assertEqual(Rules(extra_extensions=["dwg"]).kind("도면.DWG"), "other")
        self.assertTrue(Rules(extra_dirs=["백업"]).skip_dir("백업"))

    def test_work_time(self):
        rules = Rules()
        self.assertEqual(rules.work_time(100.0, 500.0), (500.0, []))
        self.assertEqual(rules.work_time(900.0, 500.0), (900.0, ["copied"]))  # 복사: 생성이 늦음
        self.assertEqual(rules.work_time(500.5, 500.0), (500.5, ["new"]))
        self.assertEqual(Rules(time_mode="mtime").work_time(900.0, 500.0), (500.0, ["copied"]))
        with self.assertRaises(ValueError):
            Rules(time_mode="x")

    def test_cloud_only(self):
        self.assertTrue(cloud_only(0x00400000))
        self.assertFalse(cloud_only(0x20))


class ScanStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "문서"
        self.store = Store(Path(self.tmp.name) / "index" / "timeline.db")
        self.day = datetime(2026, 10, 31, 9, 0).timestamp()

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_initial_scan_excludes_and_queries(self):
        touch(self.root / "보고서.hwpx", self.day)
        touch(self.root / "하위" / "표.xlsx", self.day + 3600)
        touch(self.root / "사진.jpg", self.day - 86400)
        touch(self.root / "~$보고서.hwpx", self.day)
        touch(self.root / "node_modules" / "x.pdf", self.day)
        touch(self.root / "AppData" / "y.pdf", self.day)
        touch(self.root / "프로그램.exe", self.day)
        result = scan_root(self.store, self.root)
        self.assertEqual((result.seen, result.written, result.removed), (3, 3, 0))
        self.assertEqual(result.skipped_dirs, 2)
        # 오늘(10/31)만: 최신이 위
        start = datetime(2026, 10, 31).timestamp()
        # 시험 파일은 지금 만들어져 생성 시각이 수정 시각보다 늦다(max 방식이면 '오늘' 작업) — 수정 시각 규칙으로 본다.
        self.assertTrue(all("copied" in r["flags"] for r in self.store.range(0, 2e10)))
        mrows = Store(":memory:")
        scan_root(mrows, self.root, Rules(time_mode="mtime"))
        names = [r["name"] for r in mrows.range(start, start + 86400)]
        self.assertEqual(names, ["표.xlsx", "보고서.hwpx"])
        self.assertEqual([r["name"] for r in mrows.range(start, start + 86400, newest_first=False)],
                         ["보고서.hwpx", "표.xlsx"])
        self.assertEqual([r["name"] for r in mrows.range(0, 2e10, kinds=["image"])], ["사진.jpg"])
        self.assertEqual([r["name"] for r in mrows.range(0, 2e10, query="보고")], ["보고서.hwpx"])
        self.assertEqual(mrows.range(0, 2e10, query="%"), [])
        counts = mrows.day_counts(2026, 10)
        self.assertEqual(counts[31]["total"], 2)
        self.assertEqual(counts[30], {"total": 1, "image": 1})
        self.assertEqual(mrows.hour_density(start, start + 86400), {9: 1, 10: 1})
        self.assertEqual(mrows.count(0, 2e10, kinds=["hwp", "sheet"]), 2)
        self.assertIn("copied", mrows.range(0, 2e10, kinds=["image"])[0]["flags"])
        mrows.close()

    def test_incremental_no_change_means_no_writes(self):
        for i in range(30):
            touch(self.root / f"d{i % 3}" / f"문서{i}.hwpx", self.day + i)
        first = scan_root(self.store, self.root)
        self.assertEqual(first.written, 30)
        again = scan_root(self.store, self.root)
        self.assertEqual((again.seen, again.written, again.removed), (30, 0, 0))

    def test_incremental_modify_add_delete_rename(self):
        a = touch(self.root / "a.hwpx", self.day)
        b = touch(self.root / "b.pdf", self.day)
        scan_root(self.store, self.root)
        touch(a, self.day + 100, text="바뀐 내용")
        os.rename(b, self.root / "b2.pdf")
        touch(self.root / "c.docx", self.day)
        result = scan_root(self.store, self.root)
        self.assertEqual((result.written, result.removed), (3, 1))  # a 수정 · b2·c 추가 / b 삭제
        names = sorted(r["name"] for r in self.store.range(0, 2e10))
        self.assertEqual(names, ["a.hwpx", "b2.pdf", "c.docx"])

    def test_cancel_keeps_rows_and_skips_delete(self):
        touch(self.root / "a.hwpx", self.day)
        scan_root(self.store, self.root)
        os.unlink(self.root / "a.hwpx")
        result = scan_root(self.store, self.root, cancel=lambda: True)
        self.assertTrue(result.cancelled)
        self.assertEqual(result.removed, 0)
        self.assertEqual(self.store.stats()["files"], 1)

    def test_hide_drop_root_and_multiple_roots(self):
        other = Path(self.tmp.name) / "바탕 화면"
        touch(self.root / "a.hwpx", self.day)
        touch(other / "b.hwpx", self.day)
        total = scan_roots(self.store, [self.root, other])
        self.assertEqual(total.written, 2)
        row = self.store.range(0, 2e10, roots=[str(other)])[0]
        self.assertEqual(row["name"], "b.hwpx")
        self.assertTrue(self.store.hide(row["id"]))
        self.assertEqual(self.store.stats()["files"], 1)
        self.assertEqual(self.store.drop_root(self.root), 1)
        self.assertEqual(self.store.range(0, 2e10), [])

    def test_query_speed_month_range(self):
        rows = [dict(path=f"C:/문서/f{i}.hwpx", root="C:/문서", name=f"f{i}.hwpx", kind="hwp", size=1,
                     mtime=self.day - i * 30, ctime=self.day - i * 30, work_time=self.day - i * 30, flags=[])
                for i in range(100000)]
        memory = Store(":memory:")
        memory.upsert_many(rows)
        start = time.perf_counter()
        page = memory.range(self.day - 30 * 86400, self.day + 1, limit=200)
        counts = memory.day_counts(2026, 10)
        elapsed = time.perf_counter() - start
        memory.close()
        self.assertEqual(len(page), 200)
        self.assertGreater(sum(c["total"] for c in counts.values()), 0)
        self.assertLess(elapsed, 0.5)  # 목표 20ms(PC 측정), 시험 환경 여유

    def test_default_roots(self):
        home = Path(self.tmp.name) / "home"
        (home / "Desktop").mkdir(parents=True)
        (home / "Documents").mkdir()
        (home / "Downloads").mkdir()
        roots = default_roots(str(home), environ={})
        self.assertEqual([Path(r).name for r in roots], ["Desktop", "Documents"])


if __name__ == "__main__":
    unittest.main()
