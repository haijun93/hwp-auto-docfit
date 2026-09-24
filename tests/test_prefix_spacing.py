"""Spacing and ratio adjustment must never alter the hanging-indent prefix."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


class PrefixSpacingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def clipped(self, text, start=0, end=None):
        fn = self.ns['자간조정_본문범위']
        class Doc:
            pos = (0, 7, 30)
            def GetPos(self): return self.pos
            def SetPos(self, *pos): self.pos = tuple(pos)
        doc = Doc()
        if end is None:
            end = len(text.encode('utf-16-le')) // 2
        with patch.dict(fn.__globals__, {'hwp': doc, '현재문단_텍스트': lambda: text}):
            result = fn((0, 7, start), (0, 7, end))
        self.assertEqual(doc.pos, (0, 7, 30))
        return result

    def test_parenthesis_and_colon_labels_protected(self):
        for prefix in [' ㅇ (개요) ', '  - 무상대부 절차 : ', '  - 무상대부 절차 ： ', ' ※ (참고) ']:
            with self.subTest(prefix=prefix):
                self.assertEqual(self.clipped(prefix + '본문')[0][2], len(prefix))

    def test_plain_body_and_later_lines_not_clipped(self):
        self.assertEqual(self.clipped('일반 문장 본문')[0][2], 0)
        self.assertEqual(self.clipped(' ㅇ (개요) 길게 이어진 본문입니다', 15)[0][2], 15)

    def test_label_only_and_prefix_only_selection_are_empty(self):
        start, end = self.clipped(' ㅇ (운영방식)')
        self.assertEqual(start, end)
        start, end = self.clipped(' ㅇ (개요) 본문', end=3)
        self.assertEqual(start, end)
        start, end = self.clipped(' ㅇ ')
        self.assertEqual(start, end)

    def test_utf16_body_position(self):
        prefix = ' - 🚍 활용 : '
        self.assertEqual(self.clipped(prefix + '본문')[0][2], len(prefix.encode('utf-16-le')) // 2)

    def test_spacing_and_ratio_snapshots_do_not_read_protected_chars(self):
        for name in ['단어모드_자간보관', '단어모드_장평보관']:
            fn = self.ns[name]
            def forbidden(*args):
                raise AssertionError('Protected characters must not be selected')
            with patch.dict(fn.__globals__, {
                '자간조정_본문범위': lambda a, b: (b, b),
                '단어모드_한글자': forbidden, 'hwp_run': lambda cmd: True,
            }):
                self.assertEqual(fn((0, 0, 0), (0, 0, 5)), [])


if __name__ == '__main__':
    unittest.main()
