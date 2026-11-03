import tempfile
import unittest
import time
import sqlite3
import os
from pathlib import Path
from zipfile import ZipFile
from unittest.mock import patch

from docfit_core.timemachine.content_search import (
    ContentSearchIndex,
    extract_text,
    extract_paragraphs,
    classify_paragraph_levels,
    LEVEL_ORDER,
    LEVEL_LABELS,
    CURRENT_HIERARCHY_SCHEMA_VERSION,
    ParagraphRecord,
)


def write_hwpx_paragraphs(path: Path, paragraphs: list[dict]) -> None:
    """HWPX fixture 제작 helper. 외부 템플릿 없이 최소 XML Zip을 구성한다."""
    header_styles = []
    style_id_map = {}
    sid_counter = 0
    for p in paragraphs:
        sname = p.get("style_name")
        if sname and sname not in style_id_map:
            style_id_map[sname] = str(sid_counter)
            header_styles.append(f'<hh:style id="{sid_counter}" type="para" name="{sname}" />')
            sid_counter += 1

    header_xml = f"""<?xml version="1.0" encoding="utf-8"?>
    <hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head">
      <hh:styles>
        {''.join(header_styles)}
      </hh:styles>
    </hh:head>"""

    body_elements = []
    for p in paragraphs:
        text = p.get("text", "")
        sname = p.get("style_name")
        sid_attr = f' styleIDRef="{style_id_map[sname]}"' if (sname and sname in style_id_map) else ""
        olvl = p.get("outline_level")
        olvl_attr = f' outlineLevel="{olvl}"' if olvl is not None else ""
        is_tbl = p.get("is_table_cell", False)

        p_inner = f'<hp:run><hp:t>{text}</hp:t></hp:run>'
        if is_tbl:
            body_elements.append(
                f'<hp:p><hp:run><hp:tbl><hp:tr><hp:tc><hp:p{sid_attr}{olvl_attr}>{p_inner}</hp:p></hp:tc></hp:tr></hp:tbl></hp:run></hp:p>'
            )
        else:
            body_elements.append(f'<hp:p{sid_attr}{olvl_attr}>{p_inner}</hp:p>')

    section_xml = f"""<?xml version="1.0" encoding="utf-8"?>
    <hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
      {''.join(body_elements)}
    </hp:sec>"""

    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w") as archive:
        archive.writestr("Contents/header.xml", header_xml)
        archive.writestr("Contents/section0.xml", section_xml)


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
        self.assertEqual(len(self.index.search("대한민국의")), 1)
        self.assertEqual(len(self.index.search("행정")), 2)
        self.assertEqual([x["name"] for x in self.index.search('"검색 대상" -빠른')], [p2.name])
        self.assertEqual(set(x["name"] for x in self.index.search("ext:txt 대한민국")), {p1.name, p2.name})
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
        db.executescript("""
            CREATE TABLE content_meta(path TEXT PRIMARY KEY,size INTEGER,mtime REAL);
            CREATE VIRTUAL TABLE content_fts USING fts5(path UNINDEXED,name UNINDEXED,body,tokenize='unicode61');
        """)
        old_file = self.root / "old.txt"
        old_file.write_text("한글 검색 이전", encoding="utf-8")
        db.execute("INSERT INTO content_meta VALUES(?,1,1)", (str(old_file),))
        db.execute("INSERT INTO content_fts VALUES(?,'old.txt','한글 검색 이전')", (str(old_file),))
        db.commit()
        db.close()
        migrated = ContentSearchIndex(path)
        # 구형 색인 상태이므로 재색인 필요 카운트 1, 검색 결과에는 미노출
        self.assertEqual(migrated.needs_reindex_count(), 1)
        self.assertEqual(migrated.search("검색"), [])
        # 재색인 수행 후 정상 검색
        self.assertTrue(migrated.index_file(old_file)["indexed"])
        self.assertEqual(migrated.needs_reindex_count(), 0)
        self.assertEqual(migrated.search("검색")[0]["name"], "old.txt")
        migrated.close()

    def test_hierarchy_order_title_once_beats_square_five_and_body_ten(self):
        # 문서A.hwpx: 제목 표식 문단에 query 1회
        doc_a = self.root / "A_title.hwpx"
        write_hwpx_paragraphs(doc_a, [
            {"text": "핵심과제 추진계획", "style_name": "제목", "outline_level": 0},
            {"text": "일반 설명 문장입니다.", "style_name": "바탕글"},
        ])
        # 문서B.hwpx: ㅁ 문단에 query 5회
        doc_b = self.root / "B_square.hwpx"
        write_hwpx_paragraphs(doc_b, [
            {"text": "ㅁ 핵심과제 핵심과제 핵심과제 핵심과제 핵심과제 추진", "style_name": "바탕글"},
        ])
        # 문서C.txt: 일반 본문에 query 10회
        doc_c = self.root / "C_body.txt"
        doc_c.write_text(" ".join(["핵심과제"] * 10), encoding="utf-8")

        self.index.index_file(doc_a)
        self.index.index_file(doc_b)
        self.index.index_file(doc_c)

        found = self.index.search("핵심과제")
        self.assertEqual(len(found), 3)
        self.assertEqual(found[0]["name"], doc_a.name)
        self.assertEqual(found[0]["best_level"], "문서 제목")
        self.assertEqual(found[0]["total_matches"], 1)

        self.assertEqual(found[1]["name"], doc_b.name)
        self.assertEqual(found[1]["best_level"], "ㅁ")
        self.assertEqual(found[1]["total_matches"], 5)

        self.assertEqual(found[2]["name"], doc_c.name)
        self.assertEqual(found[2]["best_level"], "본문")
        self.assertEqual(found[2]["total_matches"], 10)

    def test_hierarchy_order_same_level_more_mentions_first(self):
        doc1 = self.root / "m1.txt"
        doc2 = self.root / "m2.txt"
        doc1.write_text("동일위계 검색어 단독 출현", encoding="utf-8")
        doc2.write_text("동일위계 검색어 검색어 2회 출현", encoding="utf-8")
        self.index.index_file(doc1)
        self.index.index_file(doc2)
        found = self.index.search("검색어")
        self.assertEqual(found[0]["name"], doc2.name)
        self.assertEqual(found[1]["name"], doc1.name)

    def test_hierarchy_order_same_level_same_mentions_newer_document_first(self):
        p_old = self.root / "z_older.txt"
        p_new = self.root / "a_newer.txt"
        p_old.write_text("날짜 동률 검사 키워드", encoding="utf-8")
        p_new.write_text("날짜 동률 검사 키워드", encoding="utf-8")
        self.index.index_file(p_old)
        self.index.index_file(p_new)

        # DB fixture로 안정된 timestamp 설정
        # p_old: ctime=10.0, mtime=20.0 -> max=20.0
        # p_new: ctime=30.0, mtime=15.0 -> max=30.0 (생성일이 미래인 경우도 검증)
        with self.index._lock, self.index.db:
            self.index.db.execute("UPDATE content_meta SET ctime=10.0, mtime=20.0 WHERE path=?", (str(p_old.resolve()),))
            self.index.db.execute("UPDATE content_meta SET ctime=30.0, mtime=15.0 WHERE path=?", (str(p_new.resolve()),))

        found = self.index.search("키워드")
        self.assertEqual(len(found), 2)
        self.assertEqual(found[0]["name"], p_new.name)
        self.assertEqual(found[1]["name"], p_old.name)

    def test_hierarchy_order_bm25_is_fourth_tiebreaker(self):
        # 위계, 횟수, 날짜가 완전히 동률인 두 문서
        # 한 문서는 검색어가 집중된 짧은 문맥, 다른 문서는 다량의 잡음 단어 포함 문맥
        p_dense = self.root / "z_dense.txt"
        p_sparse = self.root / "a_sparse.txt"
        p_dense.write_text("알고리즘분석", encoding="utf-8")
        p_sparse.write_text("알고리즘분석 " + " ".join([f"잡음단어{i}" for i in range(50)]), encoding="utf-8")
        self.index.index_file(p_dense)
        self.index.index_file(p_sparse)

        with self.index._lock, self.index.db:
            self.index.db.execute("UPDATE content_meta SET ctime=100.0, mtime=100.0 WHERE path=?", (str(p_dense.resolve()),))
            self.index.db.execute("UPDATE content_meta SET ctime=100.0, mtime=100.0 WHERE path=?", (str(p_sparse.resolve()),))

        found = self.index.search("알고리즘분석")
        self.assertEqual(len(found), 2)
        # z_dense가 파일명 알파벳 순서상 뒤이지만 BM25 밀도가 높아 우선해야 함
        self.assertEqual(found[0]["name"], p_dense.name)

    def test_best_level_total_matches_and_relevance_rank_are_returned(self):
        path = self.root / "doc.hwpx"
        write_hwpx_paragraphs(path, [
            {"text": "제1장 총칙", "style_name": "개요 1", "outline_level": 1},
            {"text": "총칙 세부 내용 총칙", "style_name": "바탕글"},
        ])
        self.index.index_file(path)
        found = self.index.search("총칙")
        self.assertEqual(len(found), 1)
        item = found[0]
        self.assertEqual(item["best_level"], "장")
        self.assertEqual(item["total_matches"], 3)
        self.assertEqual(item["relevance_rank"], 1)

    def test_heading_markers_reuse_existing_classifier(self):
        path = self.root / "headings.hwpx"
        paras = [
            {"text": "Ⅰ. 장", "outline_level": 1},
            {"text": "1. 절", "outline_level": 2},
            {"text": "가. 주제", "outline_level": 3},
            {"text": "ㅁ 항목", "style_name": "바탕글"},
            {"text": "ㅇ 항목", "style_name": "바탕글"},
            {"text": "- 항목", "style_name": "바탕글"},
            {"text": "* 참고", "style_name": "바탕글"},
            {"text": "일반 본문 문장입니다.", "style_name": "바탕글"},
            {"text": "표 내부 텍스트", "is_table_cell": True},
        ]
        write_hwpx_paragraphs(path, paras)
        records = extract_paragraphs(path)
        levels = [r.level for r in records]
        expected = ["chapter", "section", "topic", "square", "circle", "dash", "asterisk", "body", "table_cell"]
        self.assertEqual(levels, expected)

    def test_default_hierarchy_sort_and_explicit_mentions_sort(self):
        doc_sq = self.root / "square.hwpx"
        write_hwpx_paragraphs(doc_sq, [{"text": "ㅁ 연관도키워드"}])
        doc_body = self.root / "body.txt"
        doc_body.write_text("연관도키워드 연관도키워드 연관도키워드", encoding="utf-8")
        self.index.index_file(doc_sq)
        self.index.index_file(doc_body)

        default_res = self.index.search("연관도키워드")
        self.assertEqual(default_res[0]["name"], doc_sq.name)

        mentions_res = self.index.search("연관도키워드", sort="mentions")
        self.assertEqual(mentions_res[0]["name"], doc_body.name)

    def test_hwpx_outline_level_wins_over_plain_text_role(self):
        path = self.root / "outline_win.hwpx"
        write_hwpx_paragraphs(path, [
            {"text": "기호 없는 문서 대제목", "style_name": "제목", "outline_level": 0},
            {"text": "일반 본문", "style_name": "바탕글"},
        ])
        records = extract_paragraphs(path)
        self.assertEqual(records[0].level, "document_title")

    def test_hwpx_chapter_and_section_markers_map_to_distinct_levels(self):
        path = self.root / "chap_sec.hwpx"
        write_hwpx_paragraphs(path, [
            {"text": "제1장 운영 지침"},
            {"text": "1. 절 세부 사항", "outline_level": 2},
        ])
        records = extract_paragraphs(path)
        self.assertEqual(records[0].level, "chapter")
        self.assertEqual(records[1].level, "section")

    def test_square_marker_aliases_share_square_level(self):
        path = self.root / "squares.txt"
        path.write_text("ㅁ 첫째 항목\n□ 둘째 항목", encoding="utf-8")
        records = extract_paragraphs(path)
        self.assertEqual(records[0].level, "square")
        self.assertEqual(records[1].level, "square")

    def test_circle_marker_aliases_share_circle_level(self):
        path = self.root / "circles.txt"
        path.write_text("ㅇ 첫째 원\n○ 둘째 원", encoding="utf-8")
        records = extract_paragraphs(path)
        self.assertEqual(records[0].level, "circle")
        self.assertEqual(records[1].level, "circle")

    def test_dash_and_asterisk_are_below_circle(self):
        c_rank = LEVEL_ORDER.index("circle")
        d_rank = LEVEL_ORDER.index("dash")
        a_rank = LEVEL_ORDER.index("asterisk")
        self.assertLess(c_rank, d_rank)
        self.assertLess(d_rank, a_rank)

    def test_unknown_or_unmarked_paragraph_is_body(self):
        path = self.root / "plain.txt"
        path.write_text("2026. 10. 20. 날짜로 시작하는 일반 문장\n1. 문맥 없는 단독 번호 문장", encoding="utf-8")
        records = extract_paragraphs(path)
        self.assertEqual(records[0].level, "body")
        self.assertEqual(records[1].level, "body")

    def test_table_cell_records_keep_table_level_and_order(self):
        path = self.root / "table.hwpx"
        write_hwpx_paragraphs(path, [
            {"text": "본문 첫 문단"},
            {"text": "1. 표 첫째 칸 번호 문단", "is_table_cell": True},
            {"text": "표 내부 제목 스타일 문단", "is_table_cell": True, "style_name": "제목", "outline_level": 0},
            {"text": "본문 둘째 문단"},
        ])
        records = extract_paragraphs(path)
        self.assertEqual(records[0].level, "body")
        self.assertFalse(records[0].is_table_cell)
        self.assertEqual(records[1].level, "table_cell")
        self.assertTrue(records[1].is_table_cell)
        self.assertEqual(records[2].level, "table_cell")
        self.assertTrue(records[2].is_table_cell)
        self.assertEqual(records[3].level, "body")

    def test_new_index_stores_paragraph_level_and_schema_version(self):
        path = self.root / "store_test.txt"
        path.write_text("본문 내용", encoding="utf-8")
        self.index.index_file(path)
        row = self.index.db.execute("SELECT hierarchy_schema_version, ctime FROM content_meta WHERE path=?", (str(path.resolve()),)).fetchone()
        self.assertEqual(row["hierarchy_schema_version"], CURRENT_HIERARCHY_SCHEMA_VERSION)
        self.assertIsNotNone(row["ctime"])

        p_row = self.index.db.execute("SELECT level, level_rank FROM content_paragraph_fts WHERE path=?", (str(path.resolve()),)).fetchone()
        self.assertEqual(p_row["level"], "body")
        self.assertEqual(int(p_row["level_rank"]), LEVEL_ORDER.index("body"))

    def test_index_unchanged_current_schema_is_noop(self):
        path = self.root / "noop.txt"
        path.write_text("고정 내용", encoding="utf-8")
        self.assertTrue(self.index.index_file(path)["indexed"])
        self.assertFalse(self.index.index_file(path)["indexed"])

        with self.index._lock, self.index.db:
            self.index.db.execute("UPDATE content_meta SET hierarchy_schema_version=0 WHERE path=?", (str(path.resolve()),))

        self.assertTrue(self.index.index_file(path)["indexed"])

    def test_reindex_replaces_all_rows_atomically(self):
        path = self.root / "atomic.txt"
        path.write_text("줄 1\n줄 2\n줄 3", encoding="utf-8")
        self.index.index_file(path)
        count1 = self.index.db.execute("SELECT COUNT(*) FROM content_paragraph_fts WHERE path=?", (str(path.resolve()),)).fetchone()[0]
        self.assertEqual(count1, 3)

        path.write_text("단일 줄", encoding="utf-8")
        self.index.index_file(path)
        count2 = self.index.db.execute("SELECT COUNT(*) FROM content_paragraph_fts WHERE path=?", (str(path.resolve()),)).fetchone()[0]
        self.assertEqual(count2, 1)

    def test_remove_file_clears_paragraph_and_legacy_rows(self):
        path = self.root / "remove_me.txt"
        path.write_text("지울 내용", encoding="utf-8")
        self.index.index_file(path)
        self.index.remove_file(path)
        c_p = self.index.db.execute("SELECT COUNT(*) FROM content_paragraph_fts WHERE path=?", (str(path.resolve()),)).fetchone()[0]
        c_f = self.index.db.execute("SELECT COUNT(*) FROM content_fts WHERE path=?", (str(path.resolve()),)).fetchone()[0]
        c_m = self.index.db.execute("SELECT COUNT(*) FROM content_meta WHERE path=?", (str(path.resolve()),)).fetchone()[0]
        self.assertEqual(c_p, 0)
        self.assertEqual(c_f, 0)
        self.assertEqual(c_m, 0)

    def test_full_body_counts_not_limited_to_snippet(self):
        path = self.root / "long.txt"
        # 1번째 줄에 1회, 100번째 줄에 2회 -> 총 3회
        lines = ["키워드 첫 문맥"] + ["일반 줄"] * 98 + ["키워드 반복 키워드 끝 문맥"]
        path.write_text("\n".join(lines), encoding="utf-8")
        self.index.index_file(path)
        found = self.index.search("키워드")
        self.assertEqual(found[0]["total_matches"], 3)
        self.assertIn("첫 문맥", found[0]["snippet"])

    def test_multiple_terms_count_by_term_and_total(self):
        path = self.root / "multi.txt"
        # 예산 2회, 집행 3회
        lines = [
            "예산 예산 관련 문장",
            "집행 집행 집행 관련 문장",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        self.index.index_file(path)
        found = self.index.search("예산 집행")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["match_counts"], {"예산": 2, "집행": 3})
        self.assertEqual(found[0]["total_matches"], 5)

    def test_excluded_terms_do_not_contribute_to_count_or_best_level(self):
        path = self.root / "exclude.hwpx"
        write_hwpx_paragraphs(path, [
            {"text": "제1장 제외키워드 포함", "style_name": "개요 1", "outline_level": 1},
            {"text": "본문에만 양성키워드 존재", "style_name": "바탕글"},
        ])
        self.index.index_file(path)
        found = self.index.search("양성키워드 -다른제외어")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["best_level"], "본문")
        self.assertEqual(found[0]["total_matches"], 1)

    def test_highest_level_is_used_when_one_document_matches_multiple_levels(self):
        path = self.root / "mixed.hwpx"
        write_hwpx_paragraphs(path, [
            {"text": "복합문서 제목검색어", "style_name": "제목", "outline_level": 0},
            {"text": " ".join(["제목검색어"] * 8), "style_name": "바탕글"},
        ])
        self.index.index_file(path)
        found = self.index.search("제목검색어")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["best_level"], "문서 제목")
        self.assertEqual(found[0]["total_matches"], 9)

    def test_phrase_counts_and_highlights_preserve_existing_contract(self):
        path = self.root / "phrase.txt"
        path.write_text('First Line "Exact Match Target" And More "Exact Match Target"', encoding="utf-8")
        self.index.index_file(path)
        found = self.index.search('"Exact Match Target"')
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["match_counts"], {'Exact Match Target': 2})
        self.assertEqual(found[0]["total_matches"], 2)
        self.assertTrue(found[0]["highlights"])

    def test_operator_filters_do_not_change_hierarchy_ordering(self):
        p_hwpx = self.root / "target.hwpx"
        p_txt = self.root / "target.txt"
        write_hwpx_paragraphs(p_hwpx, [{"text": "제1장 필터검색어", "outline_level": 1}])
        p_txt.write_text("필터검색어 필터검색어 필터검색어", encoding="utf-8")
        self.index.index_file(p_hwpx)
        self.index.index_file(p_txt)

        found = self.index.search("ext:hwpx 필터검색어")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["best_level"], "장")

    def test_sort_alias_compatibility(self):
        p1 = self.root / "p1.txt"
        p2 = self.root / "p2.txt"
        p1.write_text("별칭검색 1회", encoding="utf-8")
        p2.write_text("별칭검색 별칭검색 2회", encoding="utf-8")
        self.index.index_file(p1)
        self.index.index_file(p2)
        found = self.index.search("별칭검색", sort="relevance")
        self.assertEqual(found[0]["name"], p2.name)

    def test_3000_document_search_under_one_second(self):
        with self.index._lock, self.index.db:
            self.index.db.executemany(
                "INSERT INTO content_paragraph_fts(path,name,paragraph_index,level,level_rank,body) VALUES(?,?,?,?,?,?)",
                [(f"{self.root}/d{i}.txt", f"d{i}.txt", 0, "body", 8, f"문서 {i} 공통어 행정문서 대한민국 검색") for i in range(3000)]
            )
            self.index.db.executemany(
                "INSERT INTO content_fts(path,name,body) VALUES(?,?,?)",
                [(f"{self.root}/d{i}.txt", f"d{i}.txt", f"문서 {i} 공통어 행정문서 대한민국 검색") for i in range(3000)]
            )
            self.index.db.executemany(
                "INSERT INTO content_meta(path,size,mtime,ctime,hierarchy_schema_version) VALUES(?,?,?,?,?)",
                [(f"{self.root}/d{i}.txt", 1, 1.0, 1.0, CURRENT_HIERARCHY_SCHEMA_VERSION) for i in range(3000)]
            )
        start = time.perf_counter()
        result = self.index.search("행정문서 대한민국", limit=100)
        elapsed = time.perf_counter() - start
        print(f"\n[성능 측정] 3000건 본문검색: {elapsed:.4f}초", flush=True)
        self.assertEqual(len(result), 100)
        self.assertLess(elapsed, 1.0, f"3000건 검색: {elapsed:.3f}s")


if __name__ == "__main__":
    unittest.main()
