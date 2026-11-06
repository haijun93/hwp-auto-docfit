import os
import tempfile
import unittest
from copy import deepcopy
from itertools import permutations
from pathlib import Path
from unittest.mock import Mock, patch

from docfit_core.timemachine.content_search import ContentSearchIndex
from docfit_core.timemachine.related import related_documents
from docfit_core.timemachine.store import Store


class TimemachineRelatedOrderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.selected_path = str(self.root / "selected.txt")

    def _candidate(self, name: str, reference_date: str | None) -> dict:
        if reference_date is not None:
            body = "주요업무추진실적\n작성 기준일: " + reference_date + "\n디지털전환 사업"
        else:
            body = "주요업무추진실적\n디지털전환 사업"
        return {
            "path": str(self.root / name),
            "name": name,
            "body": body,
            "reference_date": reference_date,
        }

    def _run_candidates(self, candidates: list[dict], scores: dict[str, int], *, limit: int | None = None) -> dict:
        index = Mock(spec=ContentSearchIndex)
        selected = {
            "body": "주요업무추진실적\n작성 기준일: 2026-11-03\n디지털전환 사업",
            "reference_date": "2026-11-03",
        }
        index.related_candidates.return_value = (selected, candidates)

        def side_effect(reference, candidate):
            return (scores[candidate["name"]], [{"type": "terms", "label": "공통 업무·사업 단서", "values": [candidate["name"]]}])

        with patch("docfit_core.timemachine.related._score", side_effect=side_effect):
            kwargs = {"roots": [str(self.root)]}
            if limit is not None:
                kwargs["limit"] = limit
            res = related_documents(index, self.selected_path, **kwargs)
            index.related_candidates.assert_called_once_with(self.selected_path, roots=[str(self.root)])
            return res

    def _new_index(self) -> ContentSearchIndex:
        index = ContentSearchIndex(self.root / "content.sqlite")
        self.addCleanup(index.close)
        return index

    def _write_txt(self, index: ContentSearchIndex, folder: Path, name: str, body: str, mtime: int) -> str:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        path.write_text(body, encoding="utf-8")
        os.utime(path, (mtime, mtime))
        indexed = index.index_file(path)
        self.assertEqual(indexed, {"indexed": True, "error": None})
        return str(path)

    def test_reference_date_descending_takes_priority_over_score(self) -> None:
        candidates = [
            self._candidate("jan.txt", "2026-01-31"),
            self._candidate("may.txt", "2026-05-31"),
            self._candidate("sep.txt", "2026-09-30"),
        ]
        scores = {"jan.txt": 80, "may.txt": 90, "sep.txt": 60}
        original_candidates = deepcopy(candidates)

        res = self._run_candidates(candidates, scores)

        self.assertEqual([item["name"] for item in res["items"]], ["sep.txt", "may.txt", "jan.txt"])
        self.assertEqual([item["reference_date"] for item in res["items"]], ["2026-09-30", "2026-05-31", "2026-01-31"])
        self.assertEqual([item["score"] for item in res["items"]], [60, 90, 80])
        self.assertEqual(res["reference_date"], "2026-11-03")
        self.assertIs(res["reference_date_found"], True)

        expected_items = [
            {
                "path": str(self.root / "sep.txt"),
                "name": "sep.txt",
                "score": 60,
                "reasons": [{"type": "terms", "label": "공통 업무·사업 단서", "values": ["sep.txt"]}],
                "reference_date": "2026-09-30",
                "reference_date_found": True,
            },
            {
                "path": str(self.root / "may.txt"),
                "name": "may.txt",
                "score": 90,
                "reasons": [{"type": "terms", "label": "공통 업무·사업 단서", "values": ["may.txt"]}],
                "reference_date": "2026-05-31",
                "reference_date_found": True,
            },
            {
                "path": str(self.root / "jan.txt"),
                "name": "jan.txt",
                "score": 80,
                "reasons": [{"type": "terms", "label": "공통 업무·사업 단서", "values": ["jan.txt"]}],
                "reference_date": "2026-01-31",
                "reference_date_found": True,
            },
        ]
        for item, expected in zip(res["items"], expected_items):
            self.assertEqual(set(item.keys()), {"path", "name", "score", "reasons", "reference_date", "reference_date_found",
                                                "reference_date_precision", "reference_date_basis",
                                                "reference_date_evidence", "reference_date_note"})
            self.assertEqual({k: item[k] for k in expected}, expected)
            self.assertEqual(item["reference_date_precision"], "day")
            self.assertEqual(item["reference_date_basis"], "explicit")
            self.assertTrue(item["reference_date_evidence"])
        self.assertEqual(candidates, original_candidates)

    def test_same_date_uses_score_then_casefold_name(self) -> None:
        candidates = [
            self._candidate("middle.txt", "2026-09-30"),
            self._candidate("Beta.txt", "2026-09-30"),
            self._candidate("zeta.txt", "2026-09-30"),
            self._candidate("alpha.txt", "2026-09-30"),
        ]
        scores = {"middle.txt": 40, "Beta.txt": 70, "zeta.txt": 95, "alpha.txt": 70}

        res = self._run_candidates(candidates, scores)

        self.assertEqual([item["name"] for item in res["items"]], ["zeta.txt", "alpha.txt", "Beta.txt", "middle.txt"])
        self.assertEqual([item["score"] for item in res["items"]], [95, 70, 70, 40])
        self.assertEqual([item["reference_date"] for item in res["items"]], ["2026-09-30"] * 4)
        self.assertEqual([item["reference_date_found"] for item in res["items"]], [True] * 4)
        for item in res["items"]:
            self.assertEqual(item["reasons"], [{"type": "terms", "label": "공통 업무·사업 단서", "values": [item["name"]]}])

    def test_missing_dates_follow_dated_items_by_casefold_name(self) -> None:
        candidates = [
            self._candidate("Zulu.txt", None),
            self._candidate("dated.txt", "2026-01-31"),
            self._candidate("alpha.txt", None),
            self._candidate("Beta.txt", None),
        ]
        scores = {"Zulu.txt": 100, "dated.txt": 1, "alpha.txt": 10, "Beta.txt": 90}

        res = self._run_candidates(candidates, scores)

        self.assertEqual([item["name"] for item in res["items"]], ["dated.txt", "alpha.txt", "Beta.txt", "Zulu.txt"])
        self.assertEqual(res["items"][0]["reference_date"], "2026-01-31")
        self.assertIs(res["items"][0]["reference_date_found"], True)
        self.assertEqual(res["items"][0]["score"], 1)

        missing_items = res["items"][1:]
        for item in missing_items:
            self.assertIsNone(item["reference_date"])
            self.assertIs(item["reference_date_found"], False)
        self.assertEqual([item["score"] for item in missing_items], [10, 90, 100])
        for item in res["items"]:
            self.assertEqual(item["reasons"], [{"type": "terms", "label": "공통 업무·사업 단서", "values": [item["name"]]}])

    def test_limit_is_applied_after_ordering_independent_of_input_order(self) -> None:
        base_candidates = [
            self._candidate("jan.txt", "2026-01-31"),
            self._candidate("may.txt", "2026-05-31"),
            self._candidate("sep.txt", "2026-09-30"),
        ]
        scores = {"jan.txt": 80, "may.txt": 90, "sep.txt": 60}

        for perm in permutations(base_candidates):
            with self.subTest(perm=[c["name"] for c in perm]):
                res = self._run_candidates(list(perm), scores, limit=2)
                self.assertEqual([item["name"] for item in res["items"]], ["sep.txt", "may.txt"])
                self.assertEqual([item["reference_date"] for item in res["items"]], ["2026-09-30", "2026-05-31"])
                self.assertEqual([item["score"] for item in res["items"]], [60, 90])
                self.assertEqual(len(res["items"]), 2)

        candidates_201 = [self._candidate(f"item_{i:03d}.txt", "2026-09-30") for i in range(200, -1, -1)]
        scores_201 = {c["name"]: 50 for c in candidates_201}

        with self.subTest(case="default_limit_100"):
            res = self._run_candidates(candidates_201, scores_201)
            self.assertEqual([item["name"] for item in res["items"]], [f"item_{i:03d}.txt" for i in range(100)])
            self.assertEqual(len(res["items"]), 100)

        with self.subTest(case="limit_999_clamped_to_200"):
            res = self._run_candidates(candidates_201, scores_201, limit=999)
            self.assertEqual([item["name"] for item in res["items"]], [f"item_{i:03d}.txt" for i in range(200)])
            self.assertEqual(len(res["items"]), 200)

        with self.subTest(case="limit_0_clamped_to_1"):
            res = self._run_candidates(candidates_201, scores_201, limit=0)
            self.assertEqual([item["name"] for item in res["items"]], ["item_000.txt"])
            self.assertEqual(len(res["items"]), 1)

        with self.subTest(case="limit_neg5_clamped_to_1"):
            res = self._run_candidates(candidates_201, scores_201, limit=-5)
            self.assertEqual([item["name"] for item in res["items"]], ["item_000.txt"])
            self.assertEqual(len(res["items"]), 1)

    def test_real_index_orders_explicit_dates_despite_reversed_mtime(self) -> None:
        docs = self.root / "docs"
        outside = self.root / "outside"
        index = self._new_index()

        selected_path = self._write_txt(
            index, docs, "selected.txt",
            "주요업무추진실적\n작성 기준일: 2026-11-03\n디지털전환 스마트행정 민원혁신 데이터개방",
            1600259200,
        )
        jan_path = self._write_txt(
            index, docs, "jan.txt",
            "주요업무추진실적\n작성 기준일: 2026-01-31\n디지털전환 스마트행정 민원혁신 데이터개방",
            1600172800,
        )
        may_path = self._write_txt(
            index, docs, "may.txt",
            "주요업무추진실적\n작성 기준일: 2026-05-31\n디지털전환 스마트행정",
            1600086400,
        )
        sep_path = self._write_txt(
            index, docs, "sep.txt",
            "주요업무추진실적\n작성 기준일: 2026-09-30",
            1600000000,
        )
        unrelated_path = self._write_txt(
            index, docs, "unrelated.txt",
            "요리법과 여행 기록",
            1600345600,
        )
        outside_path = self._write_txt(
            index, outside, "outside.txt",
            "주요업무추진실적\n작성 기준일: 2026-12-31\n디지털전환 스마트행정 민원혁신 데이터개방",
            1600432000,
        )

        jan_mtime = Path(jan_path).stat().st_mtime
        may_mtime = Path(may_path).stat().st_mtime
        sep_mtime = Path(sep_path).stat().st_mtime
        self.assertGreater(jan_mtime, may_mtime)
        self.assertGreater(may_mtime, sep_mtime)

        selected_row, candidates = index.related_candidates(selected_path, roots=[str(docs)])
        candidate_map = {c["name"]: c for c in candidates}
        self.assertEqual(candidate_map["jan.txt"]["reference_date"], "2026-01-31")
        self.assertEqual(candidate_map["may.txt"]["reference_date"], "2026-05-31")
        self.assertEqual(candidate_map["sep.txt"]["reference_date"], "2026-09-30")

        cand_paths = [c["path"] for c in candidates]
        self.assertNotIn(selected_path, cand_paths)
        self.assertNotIn(outside_path, cand_paths)
        self.assertIn(unrelated_path, cand_paths)

        res = related_documents(index, selected_path, roots=[str(docs)])
        self.assertEqual([item["name"] for item in res["items"]], ["sep.txt", "may.txt", "jan.txt"])
        self.assertEqual([item["reference_date"] for item in res["items"]], ["2026-09-30", "2026-05-31", "2026-01-31"])
        self.assertTrue(all(item["reference_date_found"] is True for item in res["items"]))

        self.assertEqual(len(res["items"]), 3)
        item_names = [item["name"] for item in res["items"]]
        self.assertNotIn("selected.txt", item_names)
        self.assertNotIn("unrelated.txt", item_names)
        self.assertNotIn("outside.txt", item_names)

        for item in res["items"]:
            self.assertGreater(item["score"], 0)
            reason_types = {r["type"] for r in item["reasons"]}
            self.assertIn("terms", reason_types)
            self.assertIn("document_type", reason_types)

        sep_item = next(item for item in res["items"] if item["name"] == "sep.txt")
        jan_item = next(item for item in res["items"] if item["name"] == "jan.txt")
        self.assertLess(sep_item["score"], jan_item["score"])

        self.assertEqual(res["reference_date"], "2026-11-03")
        self.assertIs(res["reference_date_found"], True)

        res_limit2 = related_documents(index, selected_path, roots=[str(docs)], limit=2)
        self.assertEqual([item["name"] for item in res_limit2["items"]], ["sep.txt", "may.txt"])

    def test_empty_missing_dates_and_excluded_pairs_with_real_index(self) -> None:
        docs = self.root / "docs"
        selected_path = str(docs / "selected.txt")
        index = self._new_index()

        with self.subTest(step="empty_db"):
            res = related_documents(index, selected_path, roots=[str(docs)])
            self.assertEqual(res["items"], [])
            self.assertIsNone(res["reference_date"])
            self.assertIs(res["reference_date_found"], False)
            self.assertTrue(res["reference_date_note"])

        with self.subTest(step="selected_only"):
            self._write_txt(index, docs, "selected.txt", "주요업무추진실적\n디지털전환 사업", 1600259200)
            res = related_documents(index, selected_path, roots=[str(docs)])
            self.assertEqual(res["items"], [])
            self.assertIsNone(res["reference_date"])
            self.assertIs(res["reference_date_found"], False)
            self.assertTrue(res["reference_date_note"])

        alpha_path = self._write_txt(index, docs, "alpha.txt", "주요업무추진실적\n디지털전환 사업", 1600000000)
        period_path = self._write_txt(index, docs, "period.txt", "2026년도 1분기 주요업무추진실적\n디지털전환 사업", 1600086400)
        zulu_path = self._write_txt(index, docs, "Zulu.txt", "주요업무추진실적\n디지털전환 사업", 1600172800)

        with self.subTest(step="candidates_without_explicit_date"):
            _, candidates = index.related_candidates(selected_path, roots=[str(docs)])
            cand_dates = {c["name"]: c["reference_date"] for c in candidates}
            self.assertEqual(cand_dates["period.txt"], "2026-03-01")
            self.assertIsNone(cand_dates["alpha.txt"])
            self.assertIsNone(cand_dates["Zulu.txt"])

            res = related_documents(index, selected_path, roots=[str(docs)])
            self.assertEqual([item["name"] for item in res["items"]], ["period.txt", "alpha.txt", "Zulu.txt"])
            self.assertIsNone(res["reference_date"])
            self.assertIs(res["reference_date_found"], False)
            period_item, *undated = res["items"]
            # 본문의 대상 분기는 기간 근거로 표시하고, 못 찾은 문서는 수정 시각 대신 '없음'으로 둔다.
            self.assertEqual((period_item["reference_date"], period_item["reference_date_basis"]), ("2026-03-31", "period"))
            self.assertEqual(period_item["reference_date_evidence"], "2026년도 1분기")
            for item in undated:
                self.assertIsNone(item["reference_date"])
                self.assertIs(item["reference_date_found"], False)
                self.assertTrue(item["reference_date_note"])

        store = Store(self.root / "timeline.db")
        self.addCleanup(store.close)
        store.exclude_related(alpha_path, selected_path)
        pairs = store.related_exclusions()
        self.assertEqual(len(pairs), 1)

        with self.subTest(step="excluded_alpha_and_repeated_and_reversed"):
            res = related_documents(index, selected_path, roots=[str(docs)], excluded_pairs=pairs)
            self.assertEqual([item["name"] for item in res["items"]], ["period.txt", "Zulu.txt"])

            res_repeat = related_documents(index, selected_path, roots=[str(docs)], excluded_pairs=pairs)
            self.assertEqual([item["name"] for item in res_repeat["items"]], ["period.txt", "Zulu.txt"])

            reversed_pairs = [(right, left) for left, right in pairs]
            res_rev = related_documents(index, selected_path, roots=[str(docs)], excluded_pairs=reversed_pairs)
            self.assertEqual([item["name"] for item in res_rev["items"]], ["period.txt", "Zulu.txt"])

            self.assertEqual(res["items"][0]["reference_date"], "2026-03-31")
            self.assertIsNone(res["items"][1]["reference_date"])
            self.assertIs(res["items"][1]["reference_date_found"], False)

        with self.subTest(step="limit_1_with_exclusions"):
            res_limit1 = related_documents(index, selected_path, roots=[str(docs)], excluded_pairs=pairs, limit=1)
            self.assertEqual([item["name"] for item in res_limit1["items"]], ["period.txt"])

        with self.subTest(step="all_candidates_excluded"):
            store.exclude_related(period_path, selected_path)
            store.exclude_related(zulu_path, selected_path)
            all_pairs = store.related_exclusions()
            res_all = related_documents(index, selected_path, roots=[str(docs)], excluded_pairs=all_pairs)
            self.assertEqual(res_all["items"], [])
            self.assertIsNone(res_all["reference_date"])
            self.assertIs(res_all["reference_date_found"], False)


if __name__ == "__main__":
    unittest.main()
