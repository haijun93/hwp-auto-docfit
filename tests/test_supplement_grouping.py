from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from docfit_core.continuation import is_continuation


class SupplementGroupingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_common_xml_com_rule(self):
        fn = self.ns['세트문장_후속문단인가']
        for text, expected in [('     ※ 설명', True), ('     ※「근거」', True),
                               ('     * 주석', True), ('     ** 주석', True),
                               ('       (나머지 3대) 설명', True), ('     - 새 항목', False),
                               ('     ② 새 항목', False), ('     1) 번호', False),
                               (' ※ 같은 깊이', False), ('※ 얕은 깊이', False), ('', False)]:
            with self.subTest(text=text):
                self.assertEqual(fn(1, text), expected)
                self.assertEqual(fn(1, text), is_continuation(1, text))

    def document(self, lines):
        class Doc:
            pos = (0, 0, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = pos
            def run(self, action):
                area, i, offset = self.pos
                if action == 'MoveParaBegin':
                    offset = 0
                elif action == 'MoveParaEnd':
                    offset = len(lines[i])
                elif action == 'MoveNextParaBegin':
                    i, offset = min(i + 1, len(lines) - 1), 0
                self.pos = area, i, offset
        return Doc()

    def test_notes_and_deeper_explanations_join_parent_until_next_item(self):
        lines = [' ㅇ 계약방법: 가상 계약', '     ※ 근거 하나', '     ※ 근거 둘',
                 '     * 주석', '     ** 보충', '       (범위 설명) 본문', ' ㅇ 다음 항목']
        doc = self.document(lines)
        fn = self.ns['보고서_본문묶음_수집']
        with patch.dict(fn.__globals__, {'hwp': doc, 'hwp_run': doc.run,
                '현재문단_텍스트': lambda: lines[doc.pos[1]], '중단_요청됨': lambda: False}):
            group = fn((0, 0, 0))
        self.assertEqual(len(group), 6)
        self.assertEqual(doc.pos, (0, 0, 0))

    def test_same_depth_note_starts_independent_group(self):
        lines = ['   - 부모 문장', '   ※ 같은 깊이', ' ㅇ 다음']
        doc = self.document(lines)
        fn = self.ns['보고서_본문묶음_수집']
        with patch.dict(fn.__globals__, {'hwp': doc, 'hwp_run': doc.run,
                '현재문단_텍스트': lambda: lines[doc.pos[1]], '중단_요청됨': lambda: False}):
            self.assertEqual(len(fn((0, 0, 0))), 1)

    def test_page_boundary_move_includes_notes_and_is_idempotent(self):
        lines = [' ㅇ 부모 문장', '     ※ 부연 하나', '     ※ 부연 둘', ' ㅇ 다음']
        doc = self.document(lines)
        pages = [1, 2, 2, 3]
        fn = self.ns['세트문장_같은쪽_시도']
        def counts(group):
            result = {}
            for start, _, _ in group:
                page = pages[start[1]]
                result[page] = result.get(page, 0) + 1
            return result
        def move(start, group, counts, expand, summary):
            for pos, _, _ in group:
                pages[pos[1]] = 2
            return '성공'
        mover = Mock(side_effect=move)
        with patch.dict(fn.__globals__, {'hwp': doc, 'hwp_run': doc.run,
                '현재문단_텍스트': lambda: lines[doc.pos[1]], '중단_요청됨': lambda: False,
                '쪽범위_사용중': lambda: False, '보고서_묶음_쪽별줄수': counts,
                '쪽보다_긴_묶음인가': lambda *args: False, '보고서_압축조건': lambda counts: True,
                '_묶음_같은쪽_이동': mover, '진단로그': Mock(),
                '세트문장_통계': {'대상': 0, '성공': 0, '실패': 0}}):
            self.assertTrue(fn((0, 0, 0), lines[0]))
            self.assertEqual(pages, [2, 2, 2, 3])
            self.assertEqual(len(mover.call_args.args[1]), 3)
            self.assertTrue(fn((0, 0, 0), lines[0]))
            mover.assert_called_once()
