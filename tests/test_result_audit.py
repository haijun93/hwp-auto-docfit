"""Outcome checks must be read-only; optional layout attempts are not errors."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class ResultAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_optional_pull_not_applied_is_not_a_word_failure(self):
        fn = self.ns['다음단어_당김_시도']
        errors = {'대상': 0, '성공': 0, '실패': 0}
        optional = {'대상': 0, '적용': 0, '미적용': 0}
        log = Mock()
        with patch.dict(fn.__globals__, {
            '단어분리_통계': errors, '다음단어_통계': optional,
            '단어모드_줄범위': lambda p: ((0, 0, 0), (0, 0, 2)),
            '단어모드_한글자': lambda p: (p, (0, 0, 3), '끝') if p[2] == 2 else None,
            '단어모드_분리정보': lambda p: None,
            '단어모드_자간보관': lambda *args: [((0, 0, 0), (0, 0, 2), [0])],
            '단어모드_서식보관': lambda *args: ([((0, 0, 0), (0, 0, 2), [0])], []),
            '단어_장평_추가축소_시도': lambda *args, **kw: False,
            '중단_요청됨': lambda: False, '진단로그': log,
        }):
            self.assertFalse(fn((0, 0, 0), 0))
        self.assertEqual(errors, {'대상': 0, '성공': 0, '실패': 0})
        self.assertEqual(optional, {'대상': 1, '적용': 0, '미적용': 1})
        self.assertIn('미적용', log.call_args.args[0])
        self.assertIn('끝', log.call_args.args[0])

    def test_word_audit_records_remaining_split_without_editing(self):
        fn = self.ns['보고서_단어분리_최종검사']
        class Document:
            pos = (0, 0, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos)
            def run(self, action):
                if action == 'MoveLineEnd':
                    self.pos = (0, 0, 2 if self.pos[2] < 3 else 5)
                elif action == 'MoveParaEnd':
                    self.pos = (0, 0, 5)
                elif action == 'MoveNextChar':
                    self.pos = (0, 0, min(5, self.pos[2] + 1))
                elif action != 'Cancel':
                    raise AssertionError('Unexpected mutation/action: ' + action)
        doc = Document()
        record = Mock()
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': doc.run, '순회_시작': lambda: doc.SetPos(0, 0, 0),
            '중단_요청됨': lambda: False, '쪽범위_끝지남': lambda p: False,
            '현재_페이지번호': lambda: 2, '현재_처리파일': 'sample.hwpx',
            '단어모드_분리정보': lambda p: (p, (0, 0, 2), p, (0, 0, 4), 2, 2),
            '단어모드_범위선택': lambda *args: None,
            '현재선택영역_텍스트': lambda: '전기버스', '검수_문제_기록': record,
        }):
            result = fn()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['checked'], 1)
        self.assertEqual(result['issues'][0]['page'], 2)
        self.assertIn('전기버스', result['issues'][0]['text'])
        self.assertEqual(doc.pos, (0, 0, 0))
        record.assert_called_once()


if __name__ == '__main__':
    unittest.main()
