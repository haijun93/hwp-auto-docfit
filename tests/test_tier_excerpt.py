"""약식 시험 발췌 구간: 항목 문장이 가장 많은 연속 5쪽을 고른다(2026-10-11)."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import test_tier_pc as tier  # noqa: E402


class TierExcerptTest(unittest.TestCase):
    def test_picks_densest_window(self):
        쪽별 = {1: 0, 2: 0, 3: 5, 4: 9, 5: 9, 6: 9, 7: 9, 8: 1, 9: 0}
        self.assertEqual(tier.발췌_구간(쪽별, 5), (3, 7))

    def test_short_document_kept_whole(self):
        self.assertEqual(tier.발췌_구간({1: 2, 2: 3}, 5), (1, 2))

    def test_tie_prefers_front(self):
        self.assertEqual(tier.발췌_구간({p: 1 for p in range(1, 11)}, 5), (1, 5))

    def test_item_sentence_pattern(self):
        for 글 in (" □ 제목", "ㅇ 본문", "  - 내용", "* 부연", "※ 참고", "1. 소제목"):
            self.assertTrue(tier.항목문장.match(글), 글)
        self.assertFalse(tier.항목문장.match("일반 문장"))

    def test_quick_tier_runs_all_mode_on_first_document_only(self):
        작업 = {이름: 첫문서만 for 이름, _, 첫문서만 in tier.TIERS["quick"]}
        self.assertEqual(작업, {"unify": False, "all": True})


if __name__ == "__main__":
    unittest.main()
