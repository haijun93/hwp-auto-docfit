"""서식 예시 직접 편집 추가(TODO 6순위): 기본 이름 규칙과 서식 이름 바꾸기."""
from pathlib import Path
import json
import os
import runpy
import tempfile
import unittest
from unittest.mock import patch


class ExampleProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_default_name_is_first_eight_chars_of_first_sentence(self):
        fn = self.ns['예시문서_기본이름']
        self.assertEqual(fn(['', '□ 추진 배경 및 필요성. 둘째 문장']), '추진 배경 및')
        self.assertEqual(fn(['주간 업무 보고서입니다.']), '주간 업무 보고')
        self.assertEqual(fn(['ㅇ 짧음.']), '짧음')
        self.assertEqual(fn(['', '   ']), '새 서식')

    def test_rename_updates_saved_profile(self):
        source = Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'
        with tempfile.TemporaryDirectory(prefix='hwp-docfit-profile-') as folder:
            with patch.dict(os.environ, {'APPDATA': folder}):
                ns = runpy.run_path(str(source), run_name='profile_ui_test')
                root = ns['TkinterDnD'].Tk()
                root.withdraw()
                errors = []
                root.report_callback_exception = lambda *args: errors.append(args)
                try:
                    app = ns['HwpAutoDocFitGUI'](root)
                    profiles = ns['서식프로파일_폴더']()
                    profiles.mkdir(parents=True, exist_ok=True)
                    base = next(iter(app._프로파일들.values()))
                    app._프로파일들['abc'] = dict(base, name='주간 업무 보고')
                    (profiles / 'abc.json').write_text(json.dumps(app._프로파일들['abc'], ensure_ascii=False),
                                                       encoding='utf-8')
                    app._활성_서식_프로파일 = 'abc'
                    with patch.object(ns['simpledialog'], 'askstring', return_value='주간 보고(마포)'):
                        app._서식_이름바꾸기()
                    saved = json.loads((profiles / 'abc.json').read_text(encoding='utf-8'))
                    self.assertEqual(saved['name'], '주간 보고(마포)')
                    self.assertEqual(app._프로파일들['abc']['name'], '주간 보고(마포)')
                    self.assertIn('주간 보고(마포)', list(app.main_profile_combo['values']))
                    self.assertEqual(errors, [])
                finally:
                    root.destroy()


if __name__ == '__main__':
    unittest.main()
