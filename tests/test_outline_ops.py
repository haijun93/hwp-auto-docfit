"""아웃라이너 편집 규칙(TODO 5순위): 이동·접기 범위·완료·메모·검색·내보내기."""
import unittest

from docfit_core import outline_ops as ops
from docfit_core.pasted_text import outline_pasted_text

LINES = [
    "# 추진 계획",
    "- 개요",
    "  > 사업 배경 메모",
    "  - 세부 1",
    "  - 세부 2",
    "- 예산",
    "  - 국비",
    "# 기대 효과",
]


class OutlineOpsTest(unittest.TestCase):
    def test_parse_and_depth(self):
        self.assertEqual(ops.parse("# 추진 계획"), ("item", 0, "추진 계획"))
        self.assertEqual(ops.parse("  - 세부 1"), ("item", 2, "세부 1"))
        self.assertEqual(ops.parse("  > 사업 배경 메모")[0], "note")
        self.assertEqual(ops.depth(LINES, 2), 1)      # 메모는 위 항목 깊이

    def test_subtree_includes_notes_and_children(self):
        self.assertEqual(ops.subtree_end(LINES, 1), 5)   # 개요 + 메모 + 세부 2개
        self.assertEqual(ops.subtree_end(LINES, 0), 7)

    def test_move_block_swaps_with_sibling_subtree(self):
        moved, index = ops.move_block(LINES, 5, up=True)   # '예산'을 '개요' 위로
        self.assertEqual(moved[1:3], ["- 예산", "  - 국비"])
        self.assertEqual(moved[3], "- 개요")
        self.assertEqual(index, 1)
        moved, index = ops.move_block(LINES, 1, up=False)  # '개요'를 '예산' 아래로
        self.assertEqual(moved[1], "- 예산")
        self.assertEqual(moved[index], "- 개요")
        self.assertIsNone(ops.move_block(LINES, 3, up=True))    # 첫 하위 항목은 위로 못 감
        self.assertIsNone(ops.move_block(LINES, 7, up=False))   # 마지막 항목은 아래로 못 감

    def test_done_and_note(self):
        done = ops.toggle_done("  - 세부 1")
        self.assertEqual(done, "  - [x] 세부 1")
        self.assertTrue(ops.is_done(done))
        self.assertEqual(ops.toggle_done(done), "  - 세부 1")
        self.assertEqual(ops.note_prefix("  - 세부 1"), "    > ")
        self.assertEqual(ops.note_prefix("# 제목"), "  > ")

    def test_search_keeps_ancestors(self):
        visible = ops.filter_visible(LINES, "국비")
        self.assertEqual(visible, {0, 5, 6})
        self.assertEqual(ops.filter_visible(LINES, "배경"), {0, 1, 2})
        self.assertEqual(ops.filter_visible(LINES, ""), set(range(len(LINES))))

    def test_export_turns_notes_into_reference_marks(self):
        lines = LINES[:3] + ["  - [x] 완료된 세부"]
        text = outline_pasted_text(ops.export_markdown(lines))
        self.assertEqual(text.splitlines(), ["ㅁ 추진 계획", "ㅇ 개요", "※ 사업 배경 메모", "- 완료된 세부"])


if __name__ == "__main__":
    unittest.main()
