"""README 자간 정리 약속: 원문 보존, 표 제외, 실패한 압축 복원."""
from pathlib import Path
import runpy
import tempfile
import unittest
from zipfile import ZipFile
from unittest.mock import Mock, patch


class SpacingContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_spacing_never_deletes_connector_characters_on_failed_fit(self):
        fn = self.ns['_연결단위_맞춤']
        actions = []
        with patch.dict(fn.__globals__, {
            '작업_모드': 'spacing', '문단_위치': lambda p, i, **kw: i,
            '단어모드_줄범위': lambda p: ((0, 0, 0), (0, 0, 5)),
            '단어모드_자간보관': lambda *a: None,
            'hwp_run': lambda action: actions.append(action),
        }):
            self.assertEqual(fn((0, 0, 0), (2, 4, 12, 14)), '미해결')
        self.assertNotIn('Delete', actions)

    def test_pc_text_comparison_preserves_space_tails_and_separates_table_cells(self):
        from scripts.verify_spacing_contract_pc import paragraph_texts
        section = '''<sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
          <hp:p><hp:run><hp:t>원문<hp:fwSpace/>공백<hp:nbSpace/>꼬리</hp:t></hp:run></hp:p>
          <hp:p><hp:run><hp:tbl><hp:tr><hp:tc><hp:subList>
            <hp:p><hp:run><hp:t>표 안 본문</hp:t></hp:run></hp:p>
          </hp:subList></hp:tc></hp:tr></hp:tbl></hp:run></hp:p>
        </sec>'''
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'sample.hwpx'
            with ZipFile(path, 'w') as archive:
                archive.writestr('Contents/section0.xml', section)
            self.assertEqual(paragraph_texts(path), ['원문 공백 꼬리', '', '표 안 본문'])

    def _parenthetical_fit(self, threshold, limit=3):
        fn = self.ns['단어중간_줄바꿈방지']
        state = {'delta': 0, 'pos': (0, 0, 0)}
        doc = Mock()
        doc.GetPos.side_effect = lambda: state['pos']
        doc.SetPos.side_effect = lambda *pos: state.update(pos=tuple(pos))
        record = Mock()
        def split():
            return threshold is None or -state['delta'] < threshold
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': lambda cmd: True, '중단_요청됨': lambda: False,
            '현재줄_끝_괄호내부_공백분리인가': split,
            '단어모드_줄범위': lambda p: ((0, 0, 0), (0, 0, 20)),
            '단어모드_자간보관': lambda *a: [((0, 0, 0), (0, 0, 20), (0,) * 7)],
            '단어모드_자간적용': lambda runs, delta: state.update(delta=delta),
            '단어모드_분리정보': lambda p: None,
            '현재_화면줄_텍스트': lambda: '계약방법(공개모집 원칙, 수의계약)',
            '현재_처리파일': 'sample.hwpx', '검수_문제_기록': record,
            '다음단어_당김_사용': False, '단계탐색_통계': {'탐색': 0, '측정': 0},
        }):
            self.assertTrue(fn(limit))
        return state, record

    def test_unsolved_parenthetical_fit_restores_original_spacing(self):
        state, record = self._parenthetical_fit(None)
        self.assertEqual(state['delta'], 0)
        record.assert_called_once()

    def test_success_at_last_allowed_step_is_not_reported_as_failure(self):
        state, record = self._parenthetical_fit(3)
        self.assertEqual(state['delta'], -3)
        record.assert_not_called()

    def test_spacing_keeps_preexisting_official_spacing_policy(self):
        fn = self.ns['문서_처리_1회']
        normalize = Mock()
        noop = lambda *a, **kw: True
        with patch.dict(fn.__globals__, {
            '작업_모드': 'spacing', '표준서식_사용': False, '선택_세부작업': {},
            '표준서식_내어쓰기_사용': False, '세트문장_같은쪽_사용': False,
            '중단_요청됨': lambda: False, '단계표시': Mock(), '상태': Mock(),
            '로그': Mock(), 'hwp_run': noop, '순회_시작': noop,
            '공문_띄어쓰기_전체_적용': normalize,
            '본문_기존자간조정': noop, '연결부호_전체_맞춤': noop,
            '본문_문장부호_처리': noop, '컨트롤_내부_자간조정': noop,
            '컨트롤_내부_문장부호_처리': noop, '보고서_페이지수_맞춤_전체_적용': noop,
        }):
            self.assertTrue(fn('sample.hwpx'))
        normalize.assert_called_once_with()

    def test_saved_audit_rejects_parenthetical_split_at_whitespace(self):
        fn = self.ns['보고서_단어분리_최종검사']
        class Doc:
            pos = (0, 0, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos)
            def run(self, action):
                if action == 'MoveLineEnd':
                    self.pos = (0, 0, 10 if self.pos[2] < 11 else 20)
                elif action == 'MoveParaEnd':
                    self.pos = (0, 0, 20)
                elif action == 'MoveNextChar':
                    self.pos = (0, 0, min(20, self.pos[2] + 1))
                elif action != 'Cancel':
                    raise AssertionError('검수 중 수정 명령: ' + action)
        doc = Doc()
        record = Mock()
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': doc.run, '순회_시작': lambda: doc.SetPos(0, 0, 0),
            '중단_요청됨': lambda: False, '쪽범위_끝지남': lambda p: False,
            '현재_페이지번호': lambda: 1, '현재_처리파일': 'sample.hwpx',
            '한칸표_영역_목록': lambda: set(), '단어모드_분리정보': lambda p: None,
            '현재줄_끝_괄호내부_공백분리인가': lambda: True,
            '현재_화면줄_텍스트': lambda: '계약방법(공개모집', '검수_문제_기록': record,
        }):
            result = fn()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['checked'], 1)
        self.assertIn('괄호 안 공백 분리', result['issues'][0]['text'])
        self.assertEqual(doc.pos, (0, 0, 0))
        record.assert_called_once()


if __name__ == '__main__':
    unittest.main()
