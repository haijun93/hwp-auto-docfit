"""'서식 예시 확인': 서식마다 예시 파일을 만들어 보관하고, 서식이 그대로면 다시 열고, 바뀌면 새로 만들고, 서식과 함께 지운다."""
import json
from pathlib import Path
import runpy
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock, patch


class FormatExampleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.gui = cls.ns['HwpAutoDocFitGUI']

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        # run_path가 돌려준 ns는 사본이므로, 메서드가 실제로 보는 전역을 바꿔 사용자 설정 폴더를 건드리지 않는다.
        self.globals = self.gui._서식예시_경로.__globals__
        self.saved = {k: self.globals[k] for k in ('서식예시_폴더', '서식프로파일_폴더')}
        self.globals['서식예시_폴더'] = lambda: self.dir / 'format_examples'
        self.globals['서식프로파일_폴더'] = lambda: self.dir / 'formats'

    def tearDown(self):
        self.globals.update(self.saved)
        self.tmp.cleanup()

    def fake(self, **extra):
        app = types.SimpleNamespace(
            running=False, _프로파일들={'p1': {'name': '보고서', 'title_size': 20}}, _활성_서식_프로파일='p1',
            status_var=Mock(), 로그표시=Mock(), _경로_열기=Mock(), root=Mock(), **extra)
        for name in ('_서식예시_경로', '_서식예시_확인', '_서식예시_완료', '_서식_삭제'):
            setattr(app, name, types.MethodType(getattr(self.gui, name), app))
        return app

    def store(self, app, signature):
        example, info = app._서식예시_경로('p1')
        self.assertTrue(str(example).startswith(str(self.dir)))
        example.parent.mkdir(parents=True, exist_ok=True)
        example.write_bytes(b'hwpx')
        info.write_text(json.dumps({'서명': signature}), encoding='utf-8')
        return example

    def test_stored_example_of_same_format_opens_directly(self):
        app = self.fake()
        example = self.store(app, self.ns['서식예시_서명'](app._프로파일들['p1']))
        with patch.object(threading, 'Thread') as thread:
            app._서식예시_확인()
        app._경로_열기.assert_called_once_with(str(example))
        thread.assert_not_called()                          # 한/글 작업 없이 보관한 예시를 연다

    def test_changed_format_makes_new_example(self):
        app = self.fake()
        self.store(app, self.ns['서식예시_서명']({'name': '보고서', 'title_size': 18}))   # 서식 값이 바뀌기 전 예시
        with patch.object(threading, 'Thread') as thread:
            app._서식예시_확인()
        thread.assert_called_once()
        app._경로_열기.assert_not_called()
        self.assertTrue(app._서식예시_준비중)
        app.root.after.assert_called()                      # 화면 스레드가 예시 글 변환이 끝났는지 살핀다

    def test_finished_example_is_stored_with_signature_and_opened(self):
        result = self.dir / 'result.hwpx'
        result.write_bytes(b'formatted')
        app = self.fake(_안내_설정=Mock(), 버튼_대기중=Mock(), stage_board=Mock(), open_result_button=Mock(),
                        autoclose_var=Mock(get=Mock(return_value=True)), _결과목록=[{'결과': str(result)}])
        example, info = app._서식예시_경로('p1')
        signature = self.ns['서식예시_서명'](app._프로파일들['p1'])
        app._서식예시_작업 = {'이름': '보고서', '식별자': 'p1', '서명': signature, '예시경로': example,
                          '정보경로': info, '결과목록': [{'결과': 'earlier.hwpx'}]}
        app._서식예시_완료({})
        self.assertEqual(example.read_bytes(), b'formatted')
        self.assertEqual(json.loads(info.read_text(encoding='utf-8'))['서명'], signature)
        app._경로_열기.assert_called_once_with(str(example))
        self.assertEqual(app._결과목록, [{'결과': 'earlier.hwpx'}])   # 이전 결과 목록을 되돌린다
        self.assertFalse(app.running)

    def test_deleting_format_deletes_its_example(self):
        app = self.fake(_프로파일_목록갱신=Mock(), _프로파일_선택=Mock())
        example = self.store(app, 'x')
        info = app._서식예시_경로('p1')[1]
        self.assertIsNone(app._서식_삭제('p1'))
        self.assertFalse(example.exists())
        self.assertFalse(info.exists())

    def test_default_format_has_own_example_name(self):
        app = self.fake()
        self.assertEqual(app._서식예시_경로('')[0].name, '서식예시__기본.hwpx')
        self.assertNotEqual(self.ns['서식예시_서명']({}), self.ns['서식예시_서명']({'name': '보고서'}))


    def test_asterisk_notes_follow_sentence_with_superscript_marks(self):
        # *·** 주석은 위첨자 *·**를 붙인 낱말을 풀이하므로, 바로 앞 문장에 그 표시가 있어야 한다.
        import re
        lines = self.ns['서식예시_글'].split('\n')
        notes = 0
        for i, line in enumerate(lines):
            mark = re.match(r'\s*(\*+)\s', line)
            if not mark:
                continue
            notes += 1
            j = i - 1
            while re.match(r'\s*\*+\s', lines[j]):
                j -= 1
            self.assertRegex(lines[j], r'[^\s*]' + re.escape(mark.group(1)) + r'(?!\*)', line)
        self.assertGreaterEqual(notes, 2)

if __name__ == '__main__':
    unittest.main()
