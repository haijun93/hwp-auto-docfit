"""쪽 범위 보존, 최종 배치 순서, 저장 결과 검수의 회귀 검사."""
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch


class PipelineReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_page_protection_only_changes_selected_paragraphs(self):
        fn = self.ns['보고서_페이지보호_전체해제']
        doc = Mock()
        position = [0, 0, 0]
        doc.GetPos.side_effect = lambda: tuple(position)
        doc.SetPos.side_effect = lambda *pos: position.__setitem__(slice(None), pos)
        doc.HParameterSet.HParaShape.KeepWithNext = 1
        changed = []
        doc.CreateAction.return_value.Execute.side_effect = lambda _: changed.append(position[1]) or True

        def run(action):
            if action == 'MoveDocBegin':
                position[:] = [0, 0, 0]
            elif action == 'MoveNextParaBegin':
                position[1] = min(position[1] + 1, 4)

        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': run, '쪽범위_본문_문단': (1, 2),
            '중단_요청됨': lambda: False, '로그': Mock(),
        }):
            self.assertTrue(fn())
        self.assertEqual(changed, [1, 2])
        self.assertEqual(position, [0, 0, 0])

    def _process_document(self, source, extra=None):
        fn = self.ns['문서_처리']
        calls = []
        doc = Mock()
        settings = {
            'hwp': doc, '작업_모드': 'format', '표준서식_사용': False,
            '준말_등록표': {}, '쪽범위_요청': (2, 2), '검수_사용': False,
            '선택_세부작업': {'style_unify': False}, '작업_반복횟수': 1,
            '중단_요청됨': lambda: False, '로그': Mock(), '상태': Mock(),
            '단계초기화': Mock(), '단계표시': Mock(),
            'validate_hwpx': Mock(return_value={'entry_count': 1, 'total_uncompressed_size': 1}),
            '한글_문서_열기': lambda *a: calls.append('open') or True,
            '원본_뷰어_문서표시': Mock(), '비교보기_임베드_재확인': Mock(),
            '쪽범위_계산': lambda *a: calls.append('range') or True,
            '표준서식_선행_적용': lambda *a: calls.append('format') or None,
            '한칸표_영역_목록': lambda: set(),
            '보고서_페이지보호_전체해제': lambda: calls.append('clear') or True,
            '문서_처리_1회': lambda *a: calls.append('pass') or True,
            '처리_쪽수_구하기': lambda: 1,
            '최종검수_문서목록': [], '검수_문제목록': [], 'gui_queue': Mock(),
        }
        settings.update(extra or {})
        with patch.dict(fn.__globals__, settings):
            result = fn(source, 1, 1)
        return result, calls, doc

    def test_range_is_fixed_before_any_format_or_protection_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.hwpx'
            source.touch()
            result, calls, _ = self._process_document(source)
        self.assertTrue(result)
        self.assertEqual(calls, ['open', 'range', 'format', 'clear', 'pass', 'clear'])

    def test_empty_page_range_does_not_modify_document(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.hwpx'
            source.touch()
            mutate = Mock(side_effect=AssertionError('빈 쪽 범위에서 수정함'))
            with self.assertRaisesRegex(RuntimeError, '쪽 범위'):
                self._process_document(source, {
                    '쪽범위_계산': lambda *a: False,
                    '보고서_페이지보호_전체해제': mutate,
                    '표준서식_선행_적용': mutate,
                })
            mutate.assert_not_called()

    def _pass_calls(self, mode, standard):
        fn = self.ns['_문서_처리_1회']
        calls = []
        def unify(**kwargs):
            calls.append('reapply' if kwargs else 'unify')
            fn.__globals__['_서식통일_문서대표프로필'] = {'profile': True}
            return True
        with patch.dict(fn.__globals__, {
            '작업_모드': mode, '표준서식_사용': standard,
            '세트문장_같은쪽_사용': True, '세트문장_통계': {},
            'stage_enabled': lambda _, key, *a: key in ('style_unify', 'page_fit', 'page_group'),
            '중단_요청됨': lambda: False, '단계표시': Mock(), '상태': Mock(), '로그': Mock(),
            'hwp_run': Mock(), '순회_시작': Mock(), '서식통일_전체_적용': unify,
            '표_셀_안쪽여백_전체_적용': lambda: True,
            '표_열너비_본문맞춤_전체_적용': lambda: True,
            '표_테두리_전체_적용': lambda: True,
            '보고서_페이지수_맞춤_전체_적용': lambda: calls.append('fit') or True,
            '세트문장_같은쪽_전체_적용': lambda: calls.append('group') or True,
            '본문_기존자간조정': lambda: True, '컨트롤_내부_자간조정': lambda: True,
        }):
            self.assertTrue(fn('source.hwpx'))
        return calls

    def test_standard_format_stages_are_not_reverted_by_unify_profile(self):
        # 표준서식이 기준이면 괄호·내어쓰기 단계가 서식통일 뒤에 설정값을 입힌다. 서식통일 직후
        # 대표값으로 다시 맞추면 그 결과가 되돌려지므로(실측) 재적용 없이 쪽 배치로 넘어간다.
        self.assertEqual(self._pass_calls('format', True), ['unify', 'fit', 'group'])
        self.assertEqual(self._pass_calls('all', True), ['unify', 'fit', 'group'])

    def test_unify_led_all_mode_rechecks_after_spacing_only(self):
        # 표준서식 없는 한 번에 적용은 서식통일이 기준이라 자간 반복 뒤 처음 대표값으로 재검증한다.
        self.assertEqual(self._pass_calls('all', False), ['unify', 'reapply'])
        # 서식 적용(표준서식 없음)은 서식통일 뒤 바뀌는 단계가 없어 재검증하지 않는다.
        self.assertEqual(self._pass_calls('format', False), ['unify'])

    def _audit(self, 결과창=True, **overrides):
        fn = self.ns['저장결과_규칙검수']
        passed = {'status': 'passed', 'checked': 1, 'issues': []}
        open_document = Mock(return_value=True)
        style = Mock(return_value=passed.copy())
        table = Mock(return_value=passed.copy())
        word = Mock(return_value=passed.copy())
        record = Mock()
        settings = {
            '작업_모드': 'all', '선택_세부작업': {'style_unify': True},
            '검수_사용': True, 'hwp': object(), '_서식통일_문서대표프로필': {'profile': True},
            '서식통일_빨간표시_사용': True,
            '한글_문서_열기': open_document, '서식통일_전체_적용': style,
            '서식통일_표_전체_적용': table, '보고서_단어분리_최종검사': word,
            '보고서_페이지배치_최종검사': Mock(return_value=passed.copy()),
            '중단_요청됨': lambda: False, '로그': Mock(), '검수_문제_기록': record,
            '처리중_기록_대체': Mock(return_value=0), '검수_문제목록': [],
            '_서식통일_최종결과_사용자확인': Mock(),
        }
        settings.update(overrides)
        with patch.dict(fn.__globals__, settings):
            result = fn('source.hwpx', 'result.hwpx', 결과창=결과창)
        return result, open_document, style, table, word, record

    def test_result_window_only_for_single_document_runs(self):
        dialog = Mock()
        self._audit(_서식통일_최종결과_사용자확인=dialog)
        dialog.assert_called_once()
        self.assertEqual(dialog.call_args.args[0]['file'], 'source.hwpx')
        dialog.reset_mock()
        result, *_ = self._audit(결과창=False, _서식통일_최종결과_사용자확인=dialog)
        dialog.assert_not_called()
        self.assertEqual(result['style_unify']['status'], 'passed')

    def test_result_window_does_not_block_the_worker(self):
        import queue
        fn = self.ns['_서식통일_최종결과_사용자확인']
        blocking = Mock(side_effect=AssertionError('작업 스레드가 결과 확인을 기다림'))
        events = queue.Queue()
        with patch.dict(fn.__globals__, {'_서식통일_대표값_검토콜백': blocking, 'gui_queue': events}):
            fn({'status': 'passed'})
        blocking.assert_not_called()
        event, request = events.get_nowait()
        self.assertEqual(event, 'style_unify_result_review')
        self.assertEqual(request['payload'], {'status': 'passed'})

    def test_all_saved_checks_share_one_reopen(self):
        result, reopened, style, _, word, _ = self._audit()
        reopened.assert_called_once()
        style.assert_called_once()
        self.assertEqual(word.call_count, 2)
        self.assertEqual(set(result), {'style_unify', 'page_group', 'word_check', 'control_word_check'})

    def test_table_audit_runs_without_body_profile(self):
        result, reopened, style, table, _, _ = self._audit(
            작업_모드='unify', _서식통일_문서대표프로필={})
        self.assertEqual(result['style_unify']['status'], 'incomplete')
        self.assertEqual(result['table_unify']['status'], 'passed')
        style.assert_not_called()
        table.assert_called_once_with(검증만=True)
        reopened.assert_called_once()

    def test_table_audit_survives_body_audit_error(self):
        result, _, _, table, _, _ = self._audit(
            작업_모드='unify', 서식통일_전체_적용=Mock(side_effect=RuntimeError('본문 검사 오류')))
        self.assertEqual(result['style_unify']['status'], 'error')
        self.assertEqual(result['table_unify']['status'], 'passed')
        table.assert_called_once()

    def test_no_enabled_checks_do_not_reopen(self):
        result, reopened, *_ = self._audit(검수_사용=False, 선택_세부작업={'style_unify': False})
        self.assertEqual(result, {})
        reopened.assert_not_called()

    def test_saved_check_cancellation_is_not_reported_as_error(self):
        result, _, _, _, word, record = self._audit(서식통일_전체_적용=Mock(return_value=False))
        self.assertIs(result, False)
        word.assert_not_called()
        record.assert_not_called()

    def test_reopen_failure_marks_all_requested_checks(self):
        result, _, style, _, word, _ = self._audit(한글_문서_열기=Mock(return_value=False))
        self.assertEqual(len(result), 4)
        self.assertTrue(all(value['status'] == 'error' for value in result.values()))
        style.assert_not_called()
        word.assert_not_called()

    def test_table_unify_respects_page_range_for_edits_and_audit(self):
        from tests.test_table_unify import cell, grid
        fn = self.ns['서식통일_표_전체_적용']
        cells = [cell(i, f'기준{i}') for i in range(10, 18)]
        cells += [cell(20, '범위 안', font='굴림'), cell(21, '범위 밖', font='굴림')]
        doc = Mock()
        state = {}
        doc.SetPos.side_effect = lambda *pos: state.update(pos=pos)
        doc.GetPos.side_effect = lambda: state['pos']
        apply = Mock()
        select = Mock()
        with patch.dict(fn.__globals__, {
            'hwp': doc, '_서식통일_표모형': lambda: [grid(0, cells)],
            '쪽범위_본문_문단': (1, 2), '쪽범위_컨트롤영역': {20},
            '중단_요청됨': lambda: False, '단계표시': Mock(), '로그': Mock(), '진단로그': Mock(),
            '문자모양_적용_현재선택': apply, '단어모드_범위선택': select,
            '현재문단_텍스트': lambda: '범위 안', 'hwp_run': Mock(),
        }):
            self.assertTrue(fn())
            result = fn(검증만=True)
        select.assert_called_once()
        self.assertEqual(select.call_args.args[0][0], 20)
        apply.assert_called_once()
        self.assertEqual(result['checked'], 1)
        self.assertEqual([issue['text'] for issue in result['issues']], ['범위 안'])

    def test_document_uses_combined_input_check_and_single_saved_audit(self):
        from tests.test_hwpx_core import make_hwpx
        from docfit_core import inspect_hwpx, validate_and_inspect_hwpx
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.hwpx'
            make_hwpx(source)
            combined = Mock(wraps=validate_and_inspect_hwpx)
            audit = Mock(return_value={})
            result, _, _ = self._process_document(source, {
                '검수_사용': True, 'validate_and_inspect_hwpx': combined,
                'validate_hwpx': Mock(side_effect=AssertionError('중복 안전 검사')),
                'inspect_hwpx': Mock(return_value=inspect_hwpx(source)),
                '저장결과_규칙검수': audit, '숫자_대조': lambda _: {'status': 'skipped', 'reason': '표본 없음'},
                '진단로그': Mock(),
            })
        self.assertTrue(result)
        combined.assert_called_once_with(source)
        audit.assert_called_once()

    def test_blank_line_removal_keeps_page_range_on_original_paragraphs(self):
        fn = self.ns['문두기호문장_사이_빈줄_삭제']
        paras = ['ㅇ 하나', '', 'ㅇ 둘', '', 'ㅇ 셋', 'ㅇ 넷(범위 밖)']
        state = {'pos': (0, 0, 0), 'sel': None}
        doc = Mock()
        doc.GetPos.side_effect = lambda: state['pos']
        doc.SetPos.side_effect = lambda *pos: state.update(pos=tuple(pos))
        doc.SelectText.side_effect = lambda p1, o1, p2, o2: state.update(sel=p2) or True

        def run(action):
            area, index, _ = state['pos']
            if action == 'MoveDocBegin':
                state['pos'] = (0, 0, 0)
            elif action == 'MoveParaBegin':
                state['pos'] = (0, index, 0)
            elif action == 'MoveParaEnd':
                state['pos'] = (0, index, len(paras[index]))
            elif action == 'MoveNextParaBegin':
                state['pos'] = (0, min(index + 1, len(paras) - 1), 0)
            elif action == 'Delete':
                del paras[state['sel']]   # 앞 문단 끝~빈 문단 끝 선택 삭제 = 빈 문단이 사라짐
            return True

        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': run, '문두기호문장_빈줄_삭제_사용': True,
            '본문_컨트롤_문단번호': lambda: set(), '중단_요청됨': lambda: False,
            '현재문단_텍스트': lambda: paras[state['pos'][1]],
            '빈문단_분류': lambda text, begin, end: 'marker' if text.strip() else 'blank',
            '쪽범위_본문_문단': (0, 4), '쪽범위_컨트롤영역': set(), '로그': Mock(),
        }):
            self.assertTrue(fn())
            fixed = fn.__globals__['쪽범위_본문_문단']
        self.assertEqual(paras, ['ㅇ 하나', 'ㅇ 둘', 'ㅇ 셋', 'ㅇ 넷(범위 밖)'])
        # 빈 문단 2개를 지웠으므로 범위 끝도 2 당겨져 '넷'(범위 밖)이 들어오지 않는다.
        self.assertEqual(fixed, (0, 2))

    def test_xml_pre_stages_share_one_snapshot_and_reopen(self):
        calls = []

        def pre_format(path, 현재문서_기준=False, 처리목록=None, 변경알림=None):
            calls.append([name for enabled, name, *_ in 처리목록 if enabled])
            변경알림['changed'] = True
            return True

        seen = {}

        def one_pass(*args):
            seen['table_style_applied'] = fn_globals['기본표서식_적용됨']
            return True

        fn_globals = self.ns['문서_처리'].__globals__
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.hwpx'
            source.touch()
            result, _, _ = self._process_document(source, {
                '표준서식_사용': True, '쪽범위_요청': None, '선택_세부작업': {},
                '제목붙임_선행적용': pre_format, '박스그림_전체_적용': lambda: True,
                '기본표서식': lambda: {}, '표서식_설명': lambda style: '기본',
                '제목4종_사용': True, '중제목_사용': True, '붙임2종_사용': True,
                '활성_정밀표_프로필': None, '문서_처리_1회': one_pass,
            })
        self.assertTrue(result)
        # 글자 서식·제목/붙임·기본 표 서식을 순서대로 한 번에 처리한다(스냅숏·다시 열기 1회).
        self.assertEqual(calls, [['별표 위첨자', '붙임 글꼴', '제목·개요', '중제목', '붙임', '기본 표 서식']])
        self.assertTrue(seen['table_style_applied'])

    def _unify_plan(self, 검증만, extra, samples):
        """서식통일_전체_적용을 가짜 문서로 실행해 결과와 문단별 적용 계획을 돌려준다."""
        fn = self.ns['서식통일_전체_적용']
        texts = [text for text, _ in samples]
        state = {'i': 0}
        applied = []

        class Doc:
            def GetPos(self):
                return (0, state['i'], 0)
            def SetPos(self, *pos):
                state['i'] = pos[1]

        def advance():
            if state['i'] >= len(texts) - 1:
                return False
            state['i'] += 1
            return True

        def sample(pos, text):
            idx = pos[1]
            extra_shape = dict(samples[idx][1])
            run = ((0, idx, 0), (0, idx, len(text)), ('한컴돋움', 1500), len(text), False)
            return ('한컴돋움', 1500, (run,), extra_shape), pos, (0, idx, len(text))

        settings = {
            '서식통일_보류자간_재조정': lambda: True, 'hwp': Doc(), 'hwp_run': lambda *args: True,
            '중단_요청됨': lambda: False, '순회_시작': lambda: state.__setitem__('i', 0),
            '쪽범위_안인가': lambda pos=None: True, '현재문단_텍스트': lambda: texts[state['i']],
            '서식통일_표본': sample, '다음_문단으로_진행': advance,
            '_서식통일_그룹키': lambda marker, text, pos: ('ㅇ', '본문', '문서 공통'),
            '문단_내어쓰기_기준_오프셋': lambda text: 2, '_서식통일_현재_HWPX': lambda: None,
            '_서식통일_문서대표프로필': {}, '_서식통일_자간보류문단': {}, '_서식통일_위치텍스트_보관': {},
            '_서식통일_문단서식_적용': applied.append, '_서식통일_문단내어쓰기_적용': applied.append,
            '서식통일_빨간표시_사용': False, '서식통일_괄호크기차이': None,
            '로그': Mock(), '진단로그': Mock(), '단계표시': Mock(),
        }
        settings.update(extra)
        with patch.dict(fn.__globals__, settings):
            result = fn(검증만=검증만)
        return result, applied

    def test_standard_format_paren_rule_follows_the_parenthesis_stage(self):
        paren = {'parenthetical_size_runs': (((0, 0, 3), (0, 0, 6), 1500, 3),)}
        samples = [(f'ㅇ 사업{i}(세부)', paren) for i in range(3)]
        standard = {'작업_모드': 'format', '표준서식_사용': True, '괄호_축소_사용': True,
                    '괄호_축소_pt': 2, '선택_세부작업': {'parenthesis': True}}
        result, _ = self._unify_plan(True, standard, samples)
        # 표준서식 직후 관행(0pt)이 아니라 괄호 서식 단계의 -2pt가 기준이다.
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['issues'][0]['expected_actual']['parenthetical_size']['expected'], 1300)
        # 서식 통일 작업은 문서 관행이 기준이다(본문과 같은 크기 괄호는 그대로).
        result, _ = self._unify_plan(True, dict(standard, 작업_모드='unify', 표준서식_사용=False), samples)
        self.assertEqual(result['status'], 'passed')

    def test_unify_leaves_hanging_indent_to_the_final_indent_stage(self):
        flat = {'hanging_indent': False, 'line_count': 2, 'marker_bold': True}
        samples = [('ㅇ 하나', flat), ('ㅇ 둘', flat), ('ㅇ 셋', flat),
                   ('ㅇ 넷', dict(flat, hanging_indent=True))]
        base = {'작업_모드': 'format', '표준서식_사용': True, '괄호_축소_사용': False}
        _, applied = self._unify_plan(False, dict(base, 최종_내어쓰기_예정=True), samples)
        self.assertEqual(applied, [])
        _, applied = self._unify_plan(False, dict(base, 최종_내어쓰기_예정=False), samples)
        self.assertTrue(any(item['hanging_mismatch'] for item in applied if isinstance(item, dict)))


if __name__ == '__main__':
    unittest.main()
