"""#IEeEE 접두어 파일 회귀 시험(v2.2.15 재발 오류).

스캔·본문색인 제외뿐 아니라 이전 버전이 DB에 남긴 행이 조회 단계(타임라인·집계·검색)에서도
보이지 않고, 정리 후 재색인해도 다시 나타나지 않는지 확인한다. 모든 DB는 임시 폴더에 만든다.
"""
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from docfit_core.timemachine import Store, scan_root
from docfit_core.timemachine.content_search import ContentSearchIndex
from docfit_core.timemachine.rules import excluded_name

EXCLUDED = [
    "#IEeEE'.pptx", "#IEeEE'.docx", "#IEeEE'.hwp", "#IEeEE'.xlsx", "#ieeee.hwpx", "#IEEEE 메모.txt",
    " '#IEeEE legacy'.pdf", "‘#IeEeE quoted’.jpg", "\"#IEeEE\".png", "﻿#IEeEE bom.hwpx", "`#ieeee`.docx",
]
NORMAL = ["보고서.hwpx", "표.xlsx", "발표.pptx", "IEeEE.hwp", "a#IEeEE.docx"]


def touch(path, when, text="x"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.utime(path, (when, when))
    return path


class ExcludedNameTests(unittest.TestCase):
    def test_prefix_rule(self):
        for name in EXCLUDED:
            self.assertTrue(excluded_name(name), name)
            self.assertTrue(excluded_name(os.path.join("상위", "하위", name)), name)
        for name in NORMAL:
            self.assertFalse(excluded_name(name), name)
        self.assertFalse(excluded_name(""))
        self.assertFalse(excluded_name(None))


class StoreLegacyRowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "문서"
        self.db_path = Path(self.tmp.name) / "index" / "timeline.db"
        self.store = Store(self.db_path)
        self.day = datetime(2026, 10, 31, 9, 0).timestamp()

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def _insert_raw(self, names, folder="legacy"):
        """이전 버전이 저장한 행을 흉내 낸다(현재 쓰기 경로의 필터를 우회)."""
        for index, name in enumerate(names):
            path = str(self.root / folder / str(index) / name)
            self.store._db.execute(
                "INSERT INTO files(key, path, root, name, kind, size, mtime, ctime, work_time, flags, cloud) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,0)",
                (path.casefold() + folder, path, os.path.normcase(str(self.root)).casefold(), name,
                 "doc", 1, self.day, self.day, self.day, ""))

    def test_queries_hide_legacy_rows_before_purge(self):
        self._insert_raw(EXCLUDED)
        self._insert_raw(["보고서.hwpx"], folder="ok")
        ids = [row[0] for row in self.store._db.execute("SELECT id FROM files WHERE name != '보고서.hwpx'")]
        start = datetime(2026, 10, 31).timestamp()
        self.assertEqual([r["name"] for r in self.store.range(0, 2e10)], ["보고서.hwpx"])
        self.assertEqual(self.store.range(0, 2e10, query="ieeee"), [])
        self.assertEqual(self.store.range(0, 2e10, extensions=["pptx", "docx", "hwp", "xlsx", "pdf", "jpg", "png", "txt"]), [])
        self.assertEqual(self.store.count(0, 2e10), 1)
        self.assertEqual(self.store.day_counts(2026, 10), {31: {"total": 1, "doc": 1}})
        self.assertEqual(self.store.hour_density(start, start + 86400), {9: 1})
        self.assertEqual(self.store.stats()["files"], 1)
        self.assertTrue(all(self.store.get(i) is None for i in ids))
        removed = self.store.purge_excluded()
        self.assertEqual(sorted(r["name"] for r in removed), sorted(EXCLUDED))
        self.assertEqual(self.store._db.execute("SELECT COUNT(*) FROM files").fetchone()[0], 1)

    def test_upsert_never_stores_excluded(self):
        rows = [dict(path=str(self.root / name), root=str(self.root), name=name, kind="doc", size=1,
                     mtime=self.day, ctime=self.day, work_time=self.day, flags=[]) for name in EXCLUDED + NORMAL]
        self.assertEqual(self.store.upsert_many(rows), len(NORMAL))
        self.assertEqual(sorted(r["name"] for r in self.store.range(0, 2e10)), sorted(NORMAL))

    def test_rescan_with_subfolders_and_reopen_never_reappears(self):
        on_disk = [n for n in EXCLUDED + NORMAL if '"' not in n]  # Windows 파일명에 쓸 수 없는 문자 제외
        for depth, name in enumerate(on_disk):
            folder = self.root.joinpath(*[f"하위{d}" for d in range(depth % 4)])
            touch(folder / name, self.day)
        self._insert_raw(EXCLUDED)  # 이전 버전 잔여 행
        for _ in range(2):
            scan_root(self.store, self.root)
            names = [r["name"] for r in self.store.range(0, 2e10)]
            self.assertFalse(any(excluded_name(n) for n in names), names)
            self.assertEqual(self.store._db.execute("SELECT COUNT(*) FROM files").fetchone()[0], len(NORMAL))
        self.store.close()
        self.store = Store(self.db_path)
        scan_root(self.store, self.root)
        self.assertEqual(sorted(r["name"] for r in self.store.range(0, 2e10)), sorted(NORMAL))


class ContentIndexLegacyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve() / "문서"
        self.db = Path(self.tmp.name) / "content.sqlite"
        self.index = ContentSearchIndex(self.db)

    def tearDown(self):
        self.index.close()
        self.tmp.cleanup()

    def _legacy_index(self, path):
        """제외 규칙이 없던 이전 버전처럼 강제로 색인한다."""
        with patch("docfit_core.timemachine.rules.excluded_name", return_value=False), \
             patch("docfit_core.timemachine.content_search.excluded_name", return_value=False):
            self.assertTrue(self.index.index_file(path)["indexed"])

    def _count(self, table):
        return self.index.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def test_legacy_content_rows_hidden_then_purged(self):
        good = touch(self.root / "정상" / "업무.txt", 0, "needleword 업무 문장")
        bad = [touch(self.root / f"하위{i}" / name, 0, "needleword 숨김 문장")
               for i, name in enumerate(["#IEeEE'.txt", " '#ieeee 메모'.txt", "‘#IEEEE’.txt"])]
        self.index.index_file(good)
        for path in bad:
            self._legacy_index(path)
        roots = [str(self.root)]
        self.assertEqual([r["name"] for r in self.index.keyword_search("needleword", roots=roots)], ["업무.txt"])
        self.assertEqual([r["name"] for r in self.index.search("needleword", roots=roots)], ["업무.txt"])
        self.assertEqual(self.index.search_files("ieeee", roots=roots), [])
        self.assertEqual([r["name"] for r in self.index.search_files("txt", roots=roots)], ["업무.txt"])
        _, candidates = self.index.related_candidates(str(good.resolve()), roots=roots)
        self.assertFalse(any(excluded_name(os.path.basename(c["path"])) for c in candidates))
        # 앱 재시작(재오픈) 시 이전 버전 잔여 행이 모든 본문 표에서 지워진다.
        self.index.close()
        self.index = ContentSearchIndex(self.db)
        self.assertEqual(self._count("content_meta"), 1)
        paths = {row[0] for row in self.index.db.execute("SELECT DISTINCT path FROM content_paragraph_fts")}
        self.assertEqual(paths, {str(good.resolve())})
        # 재색인해도 다시 들어오지 않는다.
        for path in [good, *bad]:
            self.index.index_file(path)
        self.assertEqual(self._count("content_meta"), 1)
        self.assertEqual(self.index.indexed_paths(roots=roots), [os.path.abspath(str(good.resolve()))])


if __name__ == "__main__":
    unittest.main()
