"""서식 선택·서식예시 폴더 자동 감지(2026-10-23 사용자 실측 결함).

- 설정 창을 열지 않은 채(웹 화면) 서식을 바꾸면, 그 서식의 옵션(내어쓰기·부연설명 들여쓰기 등)도 작업 설정에 들어가야 한다.
  v1.80.0부터 설정 창이 없으면 옵션을 넣지 않아, 앞 서식의 '내어쓰기 꺼짐'이 남아 항목기호·붙임 내어쓰기가 빠졌다.
- 서식예시 폴더에 사용자가 직접 넣은 예시는 서식으로 자동 등록하고, 그 파일을 그대로 예시로 기록한다.
"""
import json
from pathlib import Path
import runpy
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


class _Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class ProfileSelectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.gui = cls.ns['HwpAutoDocFitGUI']

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.globals = self.gui._서식예시_경로.__globals__
        self.saved = {k: self.globals[k] for k in ('서식예시_폴더', '서식예시_정보_폴더', '서식프로파일_폴더')}
        self.globals['서식예시_폴더'] = lambda: self.dir / 'samples'
        self.globals['서식예시_정보_폴더'] = lambda: self.dir / 'info'
        self.globals['서식프로파일_폴더'] = lambda: self.dir / 'formats'
        (self.dir / 'samples').mkdir()

    def tearDown(self):
        self.globals.update(self.saved)
        self.tmp.cleanup()

    def _bind(self, app, *names):
        for name in names:
            setattr(app, name, types.MethodType(getattr(self.gui, name), app))
        return app

    def test_selecting_without_settings_window_applies_profile_options(self):
        기본 = self.ns['기본_설정']
        profiles = {
            '': {'name': '기본 보고서 서식', 'options': {'std_hanging_indent': True, 'std_supplement_indent': True}},
            'p1': {'name': '확대간부회의', 'options': {'std_hanging_indent': False, 'std_supplement_indent': False}},
        }
        combo = Mock()
        app = types.SimpleNamespace(
            running=False, settings_toplevel=None, _프로파일들=profiles, _프로파일_ids=['', 'p1'],
            _활성_서식_프로파일='p1', main_profile_combo=combo, _프로파일_전역반영=Mock(),
            std_bool_vars={'std_hanging_indent': _Var(False), 'std_supplement_indent': _Var(False)},
            std_parspace_vars={}, paren_shrink_var=_Var(True), paren_label_bold_var=_Var(True),
            symbol_font_vars={}, table_font_vars={p: {'font': _Var(''), 'size': _Var('')} for p in ('header', 'body')},
            label_symbol_vars={}, _설정_변경됨=Mock(), _프로파일_목록갱신=Mock(), _표준서식_하위옵션_상태_갱신=Mock())
        self._bind(app, '_프로파일_선택')
        self.assertIn('std_hanging_indent', 기본)
        combo.current.return_value = 0
        app._프로파일_선택()
        self.assertEqual(app._활성_서식_프로파일, '')
        self.assertTrue(app.std_bool_vars['std_hanging_indent'].get())       # 앞 서식의 '꺼짐'이 남지 않는다
        self.assertTrue(app.std_bool_vars['std_supplement_indent'].get())
        app._설정_변경됨.assert_called()                                      # 바뀐 옵션을 저장한다
        combo.current.return_value = 1
        app._프로파일_선택()
        self.assertFalse(app.std_bool_vars['std_hanging_indent'].get())

    def _detect_app(self, profiles):
        app = types.SimpleNamespace(running=False, _서식분석중=False, _프로파일들=profiles, 로그표시=Mock(),
                                    _서식_분석_시작=Mock())
        app._서식_분석_시작.side_effect = lambda *a, **k: setattr(app, '_서식분석중', True)   # 실제처럼 분석 중 표시
        return self._bind(app, '_서식예시_경로', '_서식예시_자동감지')

    def test_auto_detect_registers_only_unregistered_examples_once(self):
        samples = self.dir / 'samples'
        for name in ('기본 서식.hwpx', '보고서.hwpx', '1장 보고서.hwpx', '~$임시.hwpx', '메모.txt'):
            (samples / name).write_bytes(b'x')
        app = self._detect_app({'': {'name': '기본 보고서 서식'}, 'p1': {'name': '보고서'}})
        app._서식예시_자동감지()
        app._서식_분석_시작.assert_called_once_with(str(samples / '1장 보고서.hwpx'), 이름묻기=False)
        self.assertEqual(app._자동감지_예시, samples / '1장 보고서.hwpx')
        app._서식_분석_시작.reset_mock()
        app._서식분석중 = False                       # 분석이 끝난 뒤(실패 포함) 다시 훑어도
        app._서식예시_자동감지()                       # 같은 실행 중에는 같은 파일을 다시 시도하지 않는다
        app._서식_분석_시작.assert_not_called()

    def test_auto_detect_waits_while_job_or_analysis_runs(self):
        (self.dir / 'samples' / '새 예시.hwpx').write_bytes(b'x')
        app = self._detect_app({'': {'name': '기본 보고서 서식'}})
        app.running = True
        app._서식예시_자동감지()
        app.running, app._서식분석중 = False, True
        app._서식예시_자동감지()
        app._서식_분석_시작.assert_not_called()

    def test_auto_detected_example_is_recorded_in_place_and_keeps_selection(self):
        sample = self.dir / 'samples' / '1장 보고서.hwpx'
        sample.write_bytes(b'user example')
        app = types.SimpleNamespace(
            running=False, _서식분석중=True, _서식분석_파일='1장 보고서.hwpx', _프로파일들={'': {'name': '기본 보고서 서식'}},
            _활성_서식_프로파일='', _자동감지_예시=sample, _quick_registration=False, status_var=Mock(), 로그표시=Mock(),
            root=Mock(), _서식창_부모=Mock(), _웹화면_모드=lambda: True, _프로파일_목록갱신=Mock(), _프로파일_선택=Mock(),
            _썸네일_만들기_시작=Mock(), _서식예시_원본_보관=Mock(), _서식예시_자동감지=Mock())
        self._bind(app, '_서식_복사완료', '_서식_복사완료_처리', '_서식예시_경로', '_서식예시_기록', '_서식예시_원본사본')
        still_cut = patch.object(self.globals['서식예시모듈'], 'still_cut', return_value=b'png')
        still_cut.start()
        self.addCleanup(still_cut.stop)
        표본 = self.dir / 'tmp' / 'sample.hwpx'
        표본.parent.mkdir()
        표본.write_bytes(b'analysed copy')
        app._서식_복사완료({'name': '1장 보고서', 'summary': '', '_서식예시_원본': str(표본)})
        identifier = next(k for k in app._프로파일들 if k)
        self.assertEqual(app._활성_서식_프로파일, '')               # 지금 고른 서식은 그대로
        app._프로파일_선택.assert_not_called()
        app._서식예시_원본_보관.assert_not_called()                  # 복사본(… (2).hwpx)을 만들지 않는다
        self.assertEqual(sample.read_bytes(), b'user example')      # 사용자 파일은 그대로
        self.assertEqual(sorted(p.name for p in sample.parent.iterdir()), ['1장 보고서.hwpx'])
        info = json.loads(app._서식예시_경로(identifier)[1].read_text(encoding='utf-8'))
        self.assertEqual(info['file'], '1장 보고서.hwpx')
        self.assertEqual(app._서식예시_경로(identifier)[0], sample)
        self.assertIsNone(app._자동감지_예시)
        app.root.after.assert_called_with(500, app._서식예시_자동감지)  # 다음 예시를 이어서 찾는다


if __name__ == '__main__':
    unittest.main()
