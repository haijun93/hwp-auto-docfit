"""문두기호 문장 사이의 빈 줄만 지우고, 컨트롤 문단·머리 문단 주변 빈 줄은 둔다."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class BlankLineRemovalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def classify(self, text, units=None):
        units = len(text) if units is None else units
        return self.ns['빈문단_분류'](text, (0, 1, 0), (0, 1, units))

    def test_classification(self):
        self.assertEqual(self.classify(''), 'blank')
        self.assertEqual(self.classify('   '), 'blank')
        self.assertEqual(self.classify('', units=8), 'other')   # 표·그림 컨트롤 문단
        self.assertEqual(self.classify('  ㅇ (개요) 본문'), 'marker')
        self.assertEqual(self.classify('2026. 9. 24.(목)'), 'other')
        self.assertEqual(self.classify('일반 문장'), 'other')

    def test_only_blanks_between_marker_sentences(self):
        find = self.ns['문두기호문장_사이_빈문단_찾기']
        kinds = ['other', 'blank', 'marker', 'blank', 'blank', 'marker', 'blank',
                 'other', 'blank', 'marker', 'blank']
        self.assertEqual(find(kinds), [3, 4])

    def test_deletes_from_the_end_joining_into_previous_paragraph(self):
        fn = self.ns['문두기호문장_사이_빈줄_삭제']
        texts = ['□ 제목', '', 'ㅇ 본문', '', '', '- 내용']
        state = {'i': 0}
        selections = []

        class Doc:
            def GetPos(self):
                return (0, state['i'], 0)
            def SetPos(self, *pos):
                pass
            def SelectText(self, *args):
                selections.append(args)
                return True

        def run(cmd):
            if cmd == 'MoveNextParaBegin' and state['i'] < len(texts) - 1:
                state['i'] += 1
            elif cmd == 'MoveDocBegin':
                state['i'] = 0

        doc = Doc()
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': run, '현재문단_텍스트': lambda: texts[state['i']],
            '중단_요청됨': lambda: False, '쪽범위_안인가': lambda pos=None: True,
            '로그': Mock(), '문두기호문장_빈줄_삭제_사용': True,
        }):
            self.assertTrue(fn())
        # 뒤에서부터(4, 3, 1번 빈 문단) 바로 앞 문단 끝에서 선택해 지운다.
        self.assertEqual([args[0] for args in selections], [3, 2, 0])
        self.assertEqual([args[2] for args in selections], [4, 3, 1])

    def test_setting_defaults_on(self):
        self.assertIs(self.ns['기본_설정']['std_remove_blank_lines'], True)


if __name__ == '__main__':
    unittest.main()
