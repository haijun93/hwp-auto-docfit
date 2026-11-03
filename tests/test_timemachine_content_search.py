import tempfile
import unittest
import time
import sqlite3
from pathlib import Path
from zipfile import ZipFile

from docfit_core.timemachine.content_search import ContentSearchIndex, extract_text


class ContentSearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.index = ContentSearchIndex(self.root / "content.sqlite")

    def tearDown(self):
        self.index.close()
        self.tmp.cleanup()

    def test_txt_search_snippet_and_incremental_update(self):
        path = self.root / "보고서.txt"
        path.write_text("분기별 업무 실적 검색 대상 문장", encoding="utf-8")
        self.assertTrue(self.index.index_file(path)["indexed"])
        self.assertFalse(self.index.index_file(path)["indexed"])
        found = self.index.search("업무 실적", roots=[str(self.root)])
        self.assertEqual(found[0]["name"], path.name)
        self.assertIn("업무 실적", found[0]["snippet"])
        path.write_text("새로운 내용", encoding="utf-8")
        self.assertTrue(self.index.index_file(path)["indexed"])
        self.assertEqual(self.index.search("업무 실적"), [])

    def test_hwpx_uses_defused_xml_extractor(self):
        path = self.root / "문서.hwpx"
        with ZipFile(path, "w") as archive:
            archive.writestr("Contents/header.xml", "<head/>")
            archive.writestr("Contents/section0.xml", '<root><p>타임머신 본문 검색</p></root>')
        self.assertIn("타임머신 본문", extract_text(path))
        self.index.index_file(path)
        self.assertEqual(len(self.index.search("타임머신")), 1)

    def test_failures_are_retained_and_trash_is_filtered(self):
        broken = self.root / "bad.docx"
        broken.write_text("not a zip", encoding="utf-8")
        self.assertIsNotNone(self.index.index_file(broken)["error"])
        self.assertEqual(len(self.index.errors([str(self.root)])), 1)
        trash = self.root / "$Recycle.Bin"
        trash.mkdir()
        hidden = trash / "hidden.txt"
        hidden.write_text("secretword", encoding="utf-8")
        self.index.index_file(hidden)
        self.assertEqual(self.index.search("secretword"), [])

    def test_query_operators_and_korean_substrings(self):
        p1 = self.root / "a-report.txt"
        p2 = self.root / "b-other.txt"
        p1.write_text("대한민국의 행정문서 검색 대상 문구 그리고 빠른 갈색 여우", encoding="utf-8")
        p2.write_text("대한민국 행정문서 검색 대상", encoding="utf-8")
        self.index.index_file(p1); self.index.index_file(p2)
        self.assertEqual(len(self.index.search("대한민국의")), 1)  # 조사 붙은 단어의 부분 일치
        self.assertEqual(len(self.index.search("행정")), 2)  # 2글자 LIKE 보완
        self.assertEqual([x["name"] for x in self.index.search('"검색 대상" -빠른')], [p2.name])
        self.assertEqual([x["name"] for x in self.index.search("ext:txt 대한민국")], [p1.name, p2.name])
        self.assertEqual([x["name"] for x in self.index.search("path:a-report 대한민국")], [p1.name])
        self.assertEqual([x["name"] for x in self.index.search("대한민국 빠른 ~5")], [p1.name])

    def test_rank_snippet_highlight_and_filename_cache(self):
        common = self.root / "common.txt"
        strong = self.root / "strong.txt"
        common.write_text("업무 검색 결과", encoding="utf-8")
        strong.write_text("업무 검색 업무 검색 업무 검색", encoding="utf-8")
        self.index.index_file(common); self.index.index_file(strong)
        found = self.index.search("업무 검색")
        self.assertEqual(found[0]["name"], strong.name)
        self.assertTrue(found[0]["highlights"])
        self.assertEqual(found[0]["snippet"][slice(*found[0]["highlights"][0])], "업무")
        names = self.index.search_files("strong txt")
        self.assertEqual(names[0]["name"], strong.name)

    def test_match_counts_phrases_exclusions_casefold_and_mentions_sort(self):
        low = self.root / "low.txt"
        high = self.root / "high.txt"
        low.write_text('예산이 집행되고 Annual Plan annual plan', encoding="utf-8")
        high.write_text('예산 예산을 집행 집행했다 annual plan Annual Plan', encoding="utf-8")
        self.index.index_file(low); self.index.index_file(high)
        found = self.index.search('예산 집행 "Annual Plan" -없는말', sort="mentions")
        self.assertEqual(found[0]["name"], high.name)
        item = next(row for row in found if row["name"] == low.name)
        self.assertEqual(item["match_counts"], {"예산": 1, "집행": 1, "Annual Plan": 2})
        self.assertEqual(item["total_matches"], 4)

    def test_legacy_schema_migrates_without_losing_documents(self):
        path = self.root / "legacy.sqlite"
        db = sqlite3.connect(path)
        db.executescript("CREATE TABLE content_meta(path TEXT PRIMARY KEY,size INTEGER,mtime REAL); CREATE VIRTUAL TABLE content_fts USING fts5(path UNINDEXED,name UNINDEXED,body,tokenize='unicode61');")
        db.execute("INSERT INTO content_meta VALUES('C:/old.txt',1,1)")
        db.execute("INSERT INTO content_fts VALUES('C:/old.txt','old.txt','한글 검색 이전')")
        db.commit(); db.close()
        migrated = ContentSearchIndex(path)
        self.assertEqual(migrated.search("검색")[0]["name"], "old.txt")
        migrated.close()

    def test_3000_document_search_under_one_second(self):
        with self.index.db:
            self.index.db.executemany("INSERT INTO content_fts(path,name,body) VALUES(?,?,?)",
                [(f"{self.root}/d{i}.txt", f"d{i}.txt", f"문서 {i} 공통어 행정문서 대한민국 검색") for i in range(3000)])
            self.index.db.executemany("INSERT INTO content_meta(path,size,mtime) VALUES(?,?,?)",
                [(f"{self.root}/d{i}.txt", 1, 1) for i in range(3000)])
        start = time.perf_counter()
        result = self.index.search("행정문서 대한민국", limit=100)
        elapsed = time.perf_counter() - start
        self.assertEqual(len(result), 100)
        self.assertLess(elapsed, 1.0, f"3000건 검색: {elapsed:.3f}s")


if __name__ == "__main__":
    unittest.main()
