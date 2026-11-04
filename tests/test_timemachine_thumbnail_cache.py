"""타임머신 썸네일 캐시 용량 통계 및 LRU 정리 회귀 시험."""
import os
import tempfile
import time
import unittest
from pathlib import Path

from docfit_app.timemachine_service import TimemachineService
from docfit_core.timemachine import thumbs


class FakeAgent:
    def __init__(self):
        self.settings = {"timeline_roots": [], "timeline_mtime_only": False}
    def running(self): return False
    def status_file(self): return None
    def request(self, command, **payload):
        return {"ok": True, "settings": dict(self.settings)}


def stub_scanner(store, roots, rules, progress=None):
    class Stub:
        seen = written = removed = 0
        errors = []
    return Stub()


class ThumbnailCacheStatsAndPruneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "thumbs"
        self.cache = thumbs.ThumbnailCache(self.folder, max_bytes=1000)

    def test_stats_empty_cache(self):
        # 1. 캐시 폴더가 아직 생성되지 않은 상태
        res = self.cache.stats()
        self.assertEqual(res["bytes"], 0)
        self.assertEqual(res["count"], 0)
        self.assertIsNone(res["oldest_mtime"])
        self.assertIsNone(res["newest_mtime"])
        self.assertEqual(res["max_bytes"], 1000)

        # 2. 빈 디렉터리 생성 후
        self.folder.mkdir(parents=True, exist_ok=True)
        res2 = self.cache.stats()
        self.assertEqual(res2["bytes"], 0)
        self.assertEqual(res2["count"], 0)
        self.assertIsNone(res2["oldest_mtime"])
        self.assertIsNone(res2["newest_mtime"])

    def test_stats_with_cached_files(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        f1 = self.folder / "abc1.jpg"
        f2 = self.folder / "abc2.jpg"
        tmp = self.folder / "thumb-1.tmp"

        f1.write_bytes(b"A" * 120)
        f2.write_bytes(b"B" * 230)
        tmp.write_bytes(b"C" * 999)  # .tmp는 통계에 포함되지 않아야 함

        t1 = 1700000000.0
        t2 = 1700001000.0
        os.utime(f1, (t1, t1))
        os.utime(f2, (t2, t2))

        stats = self.cache.stats()
        self.assertEqual(stats["count"], 2)
        self.assertEqual(stats["bytes"], 350)
        self.assertAlmostEqual(stats["oldest_mtime"], t1, places=1)
        self.assertAlmostEqual(stats["newest_mtime"], t2, places=1)
        self.assertEqual(stats["max_bytes"], 1000)

    def test_prune_lru_order(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        f1 = self.folder / "f1.jpg"
        f2 = self.folder / "f2.jpg"
        f3 = self.folder / "f3.jpg"

        f1.write_bytes(b"1" * 100)
        f2.write_bytes(b"2" * 150)
        f3.write_bytes(b"3" * 200)

        # f1이 가장 오래됨, f2 중간, f3 최신
        t = time.time()
        os.utime(f1, (t - 300, t - 300))
        os.utime(f2, (t - 200, t - 200))
        os.utime(f3, (t - 100, t - 100))

        # 목표: 250 바이트 이하로 prune
        # f1(100)과 f2(150)를 삭제하면 200바이트 남아 <= 250 만족
        res = self.cache.prune(target_bytes=250)
        self.assertEqual(res["removed_count"], 2)
        self.assertEqual(res["removed_bytes"], 250)
        self.assertEqual(res["remaining_bytes"], 200)

        self.assertFalse(f1.exists())
        self.assertFalse(f2.exists())
        self.assertTrue(f3.exists())


class TimemachineServiceThumbnailCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings = Path(self.temp.name) / "설정"
        self.thumb_dir = Path(self.temp.name) / "thumbs"
        self.agent = FakeAgent()
        self.service = TimemachineService(
            self.settings,
            db_path=Path(self.temp.name) / "timeline.db",
            agent=self.agent,
            opener=lambda p: None,
            revealer=lambda p: None,
            scanner=stub_scanner,
            thumb_dir=self.thumb_dir, developer_mode=lambda: True,
        )
        self.addCleanup(self.service.close)

    def test_service_thumbnail_cache_stats(self):
        self.thumb_dir.mkdir(parents=True, exist_ok=True)
        (self.thumb_dir / "cache1.jpg").write_bytes(b"X" * 300)

        res = self.service.command("thumbnail_cache_stats")
        self.assertTrue(res["ok"])
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["bytes"], 300)
        self.assertIsNotNone(res["oldest_mtime"])
        self.assertIsNotNone(res["newest_mtime"])
        self.assertEqual(res["max_bytes"], self.service.thumbnails.max_bytes)

    def test_service_thumbnail_cache_clear_with_target(self):
        self.thumb_dir.mkdir(parents=True, exist_ok=True)
        f1 = self.thumb_dir / "t1.jpg"
        f2 = self.thumb_dir / "t2.jpg"
        f3 = self.thumb_dir / "t3.jpg"

        f1.write_bytes(b"A" * 100)
        f2.write_bytes(b"B" * 100)
        f3.write_bytes(b"C" * 100)

        t = time.time()
        os.utime(f1, (t - 30, t - 30))
        os.utime(f2, (t - 20, t - 20))
        os.utime(f3, (t - 10, t - 10))

        # 1. target_bytes 지정 호출 (부분 정리: f1, f2 삭제)
        res = self.service.command("thumbnail_cache_clear", {"target_bytes": 100})
        self.assertTrue(res["ok"])
        self.assertEqual(res["removed"], 2)
        self.assertEqual(res["freed_bytes"], 200)
        self.assertFalse(f1.exists())
        self.assertFalse(f2.exists())
        self.assertTrue(f3.exists())

        # 2. target_bytes 미지정 호출 (전체 정리: f3 삭제)
        res_full = self.service.command("thumbnail_cache_clear")
        self.assertTrue(res_full["ok"])
        self.assertEqual(res_full["removed"], 1)
        self.assertFalse(f3.exists())


if __name__ == "__main__":
    unittest.main()
