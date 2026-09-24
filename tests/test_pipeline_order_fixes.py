"""작업 순서·중복·임시파일 개선(A1·A2·B1·B3·C1)을 확인한다."""
import os
from pathlib import Path
import runpy
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from docfit_core.stage_selection import FORMAT_STAGES, SPACING_STAGES


class PipelineOrderFixesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    # A1: 자간 초기화를 먼저 한 문서를 선행 서식이 기준으로 삼는다.
    def test_pre_format_uses_current_document_snapshot_after_reset(self):
        fn = self.ns['제목붙임_선행적용']
        seen = []

        def processor(source, target=None, selections=None):
            seen.append(Path(source).name)
            return {}

        snapshot = Mock(side_effect=lambda path: Path(path))
        with patch.dict(fn.__globals__, {
            '제목4종_사용': True, '붙임2종_사용': False, '제목_hwpx_처리': processor,
            '_제목_임시hwpx_저장': snapshot, '로그': Mock(), '중단_요청됨': lambda: False,
        }):
            self.assertTrue(fn('C:/원본/문서.hwpx', 현재문서_기준=True))
            self.assertEqual(seen, ['source.hwpx'])
            seen.clear()
            self.assertTrue(fn('C:/원본/문서.hwpx'))
            self.assertEqual(seen, ['문서.hwpx'])

    # B3: 저장 후 검사를 마친 규칙의 처리 중 기록만 지운다.
    def test_in_process_records_replaced_by_saved_result_check(self):
        fn = self.ns['처리중_기록_대체']
        records = [
            {'file': 'a.hwpx', 'text': '[문장 묶음 페이지 분리] ㅇ (기대효과)'},
            {'file': 'a.hwpx', 'text': '[단어 중간 줄바꿈 미해결] 전기버스'},
            {'file': 'b.hwpx', 'text': '[문장 묶음 페이지 분리] 다른 파일'},
            {'file': 'a.hwpx', 'text': '[소제목 묶음 쪽 분리] □ 제목'},   # 저장 후 검사 기록
        ]
        with patch.dict(fn.__globals__, {'검수_문제목록': list(records),
                                         '선택_세부작업': {'control_spacing': False,
                                                         'control_word_check': False}}):
            removed = fn('a.hwpx', {'page_group'}, 3)
            left = [r['text'] for r in fn.__globals__['검수_문제목록']]
        self.assertEqual(removed, 1)
        self.assertEqual(left, ['[단어 중간 줄바꿈 미해결] 전기버스',
                                '[문장 묶음 페이지 분리] 다른 파일',
                                '[소제목 묶음 쪽 분리] □ 제목'])

    def test_word_records_kept_until_control_word_check_also_done(self):
        fn = self.ns['처리중_기록_대체']
        records = [{'file': 'a.hwpx', 'text': '[어절 줄분리] 표 안 문장'}]
        with patch.dict(fn.__globals__, {'검수_문제목록': list(records), '선택_세부작업': {}}):
            self.assertEqual(fn('a.hwpx', {'word_check'}, 1), 0)
            self.assertEqual(fn('a.hwpx', {'word_check', 'control_word_check'}, 1), 1)

    # C1: 오래된 작업용 임시 폴더만 정리한다.
    def test_old_work_temp_folders_are_cleaned(self):
        fn = self.ns['이전_작업_임시폴더_정리']
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            old = root / 'hwp_format_first_old'
            new = root / 'hwp_format_first_new'
            other = root / 'someone_else_old'
            for folder in (old, new, other):
                folder.mkdir()
                (folder / 'title.hwpx').write_text('x')
            past = time.time() - 3600
            os.utime(old, (past, past))
            os.utime(other, (past, past))
            with patch.object(fn.__globals__['tempfile'], 'gettempdir', return_value=str(root)):
                self.assertEqual(fn(), 1)
            self.assertFalse(old.exists())
            self.assertTrue(new.exists())
            self.assertTrue(other.exists())

    # B1: 기호별 내어쓰기 선택을 존중하고, 최종 단계가 예정되면 표준서식에서 생략한다.
    def test_per_marker_indent_choice_respected(self):
        fn = self.ns['내어쓰기_기호선택_허용']
        with patch.dict(fn.__globals__, {
            '표준서식_기호규칙_찾기': lambda text: ('-',) if text.strip().startswith('-') else None,
            '표준서식_설정': {'스타일_속성선택': {'-': {'indent': False}}},
        }):
            self.assertFalse(fn('  - 추진부서 : 사업부서'))
            self.assertTrue(fn('  ㅇ (개요) 본문'))

    def test_final_indent_flag_set_only_while_processing(self):
        fn = self.ns['문서_처리_1회']
        g = fn.__globals__
        seen = []
        with patch.dict(g, {
            '작업_모드': 'all', '표준서식_사용': True, '표준서식_내어쓰기_사용': True,
            '선택_세부작업': {}, '_문서_처리_1회': lambda *a: seen.append(g['최종_내어쓰기_예정']) or True,
        }):
            self.assertTrue(fn('a.hwpx'))
            self.assertFalse(g['최종_내어쓰기_예정'])
            g['선택_세부작업'] = {'hanging_indent': False}
            fn('a.hwpx')
        self.assertEqual(seen, [True, False])

    # A2: 문단 페이지 배치가 줄간격을 바꾸면 쪽 수 맞춤을 한 번 더 확인한다.
    def _page_stages(self, page_counts, group_changes, last_lines=3):
        fn = self.ns['_문서_처리_1회']
        g = fn.__globals__
        calls = []
        stats = {'대상': 0, '성공': 0, '실패': 0, '축소횟수': 0, '확대횟수': 0}
        changes = iter(group_changes)
        pages = iter(page_counts)

        def page_group():
            calls.append('group')
            stats['확대횟수'] += next(changes, 0)
            return True

        selection = {key: False for key, _ in FORMAT_STAGES + SPACING_STAGES}
        selection.update(page_fit=True, page_group=True)
        with patch.dict(g, {
            '작업_모드': 'format', '표준서식_사용': True, '세트문장_같은쪽_사용': True,
            '선택_세부작업': selection, '세트문장_통계': stats,
            '중단_요청됨': lambda: False, '단계표시': Mock(), '상태': Mock(), '로그': Mock(),
            'hwp_run': lambda cmd: True, '순회_시작': lambda: None,
            '보고서_페이지수_맞춤_전체_적용': lambda: calls.append('fit') or True,
            '세트문장_같은쪽_전체_적용': page_group,
            '마지막쪽_화면줄수': lambda: (next(pages), last_lines),
            '페이지맞춤_문단간격_사용': True, '페이지맞춤_최대남은줄수': 4, '진단로그': Mock(),
        }):
            self.assertTrue(fn('a.hwpx', True, 2, 2))
        return calls

    def test_page_fit_rechecked_after_group_changes_spacing(self):
        self.assertEqual(self._page_stages([5, 4], [2, 0]), ['fit', 'group', 'fit', 'group'])
        self.assertEqual(self._page_stages([4, 4], [1]), ['fit', 'group', 'fit'])
        self.assertEqual(self._page_stages([], [0]), ['fit', 'group'])
        # 마지막 쪽에 내용이 충분하면 한 번만 재고 쪽 수 맞춤을 건너뛴다.
        self.assertEqual(self._page_stages([4], [1], last_lines=20), ['fit', 'group'])


if __name__ == '__main__':
    unittest.main()
