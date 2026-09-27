"""※ 대표값 미확정 시 앞뒤 표준 문장 사이의 ※ 값을 대표값으로 보는 규칙."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


def shape(font, size):
    return (font, size, [], {'marker_bold': False, 'label_bold': None, 'hanging_indent': False})


class NoteNeighborRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def run_rule(self, body_sizes, note_sizes):
        fn = self.ns['_서식통일_참고표_이웃대표_보완']
        body, note = ('ㅇ', 'body', 1), ('※', 'note', 1)
        groups = {body: [], note: []}
        pos = 0
        for body_size, note_size in zip(body_sizes, note_sizes + [None]):
            groups[body].append((shape('한컴돋움', body_size), (0, pos, 0), None, 'ㅇ 본문'))
            pos += 1
            if note_size is not None:
                groups[note].append((shape('한컴돋움', note_size), (0, pos, 0), None, '※ 참고'))
                pos += 1
        profile = {key: self.ns['서식통일_대표']([item[0] for item in items])
                   for key, items in groups.items()}
        with patch.dict(fn.__globals__, {'로그': Mock()}):
            fn(groups, profile)
        return profile[note]

    def test_note_between_standard_sentences_becomes_representative(self):
        profile = self.run_rule([1500, 1500, 1500], [1300, 1200])
        # 두 ※ 모두 앞뒤가 표준이라 후보가 동률이면 문서 순서상 첫 값을 쓴다.
        self.assertEqual(profile['size'][0], 1300)

    def test_note_next_to_nonstandard_sentence_is_not_used(self):
        profile = self.run_rule([1500, 1700, 1500, 1500], [1300, 1200, None][:2])
        self.assertIsNone(profile['size'][0])


class TrailingParenthesisTests(unittest.TestCase):
    def test_sentence_final_parenthesis_is_treated_as_aside(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from docfit_core.style_unify import parenthetical_spans
        text = '□ 활용대상 : 전기버스 4대(※차량원복시 카운티일렉트릭 23인승)'
        self.assertEqual(parenthetical_spans(text, (), include_trailing=True), ((16, 37),))
        # 문두 라벨은 부연 괄호가 아니다.
        label = 'ㅇ (개요) 본문 (참고)'
        self.assertEqual(parenthetical_spans(label, ((2, 6),), include_trailing=True), ((10, 14),))


if __name__ == '__main__':
    unittest.main()
