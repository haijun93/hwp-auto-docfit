"""서식예시 폴더(C:\\HWP_AUTODOCFIT\\서식예시): 예시 HWPX를 사용자가 고치면 '한 번에 적용' 때 바뀐 서식 값만 설정에 옮긴다."""
import copy
import json
from pathlib import Path
import runpy
import tempfile
import types
import unittest
import zipfile
from unittest.mock import Mock

from docfit_core import format_samples as fs
from tests import test_format_elements as fx


class MergeChangesTest(unittest.TestCase):
    def test_only_values_changed_in_file_move_and_user_edits_stay(self):
        base = {"format": {"size": 15, "font": "휴먼명조", "rules": [["□", 16], ["ㅇ", 15]]}, "options": {"bold": True}}
        new = copy.deepcopy(base)
        new["format"]["size"] = 17                    # 사용자가 예시 파일에서 바꾼 값
        new["format"]["rules"][1][1] = 14
        profile = copy.deepcopy(base)
        profile["format"]["font"] = "맑은 고딕"          # 사용자가 앱 화면에서 바꾼 값(파일에서는 그대로)
        changed = fs.merge_changes(profile, base, new)
        self.assertEqual(profile["format"]["size"], 17)
        self.assertEqual(profile["format"]["rules"], [["□", 16], ["ㅇ", 14]])
        self.assertEqual(profile["format"]["font"], "맑은 고딕")
        self.assertEqual(sorted(changed), ["format/rules/1/1", "format/size"])

    def test_no_difference_changes_nothing(self):
        base = {"format": {"a": 1}}
        profile = {"format": {"a": 5}}
        self.assertEqual(fs.merge_changes(profile, base, copy.deepcopy(base)), [])
        self.assertEqual(profile, {"format": {"a": 5}})

    def test_names_and_description(self):
        self.assertEqual(fs.file_name_for("", standard=True), "기본 서식.hwpx")
        self.assertEqual(fs.file_name_for('A/B:C*'), "A_B_C.hwpx")
        self.assertEqual(fs.file_name_for("기본 서식"), "기본 서식 (사용자).hwpx")
        self.assertEqual(fs.sample_folder(Path(r"C:\HWP_AUTODOCFIT")), Path(r"C:\HWP_AUTODOCFIT\서식예시"))
        self.assertIn("외 1개", fs.describe(["format/a", "format/b"], limit=1))


class SampleFolderAppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.gui = cls.ns['HwpAutoDocFitGUI']

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.globals = self.gui._서식예시_경로.__globals__
        keys = ('서식예시_폴더', '서식예시_정보_폴더', '서식프로파일_폴더', '번들_서식예시_찾기', '알파_서식예시폴더_사용')
        self.saved = {k: self.globals[k] for k in keys}
        self.globals['서식예시_폴더'] = lambda: self.dir / 'HWP_AUTODOCFIT' / '서식예시'
        self.globals['서식예시_정보_폴더'] = lambda: self.dir / 'appdata' / 'format_examples'
        self.globals['서식프로파일_폴더'] = lambda: self.dir / 'appdata' / 'formats'
        self.bundled = self.make('bundled.hwpx', fx.HEADER)
        self.globals['번들_서식예시_찾기'] = lambda: self.bundled
        self.globals['알파_서식예시폴더_사용'] = True

    def tearDown(self):
        self.globals.update(self.saved)
        self.tmp.cleanup()

    def make(self, name, header):
        path = self.dir / name
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', header)
            z.writestr('Contents/section0.xml', fx.SECTION)
        return path

    def fake(self, profiles=None, active=''):
        app = types.SimpleNamespace(
            running=False, _프로파일들=profiles or {'': self.ns['기본_서식프로파일']()}, _활성_서식_프로파일=active,
            status_var=Mock(), 로그표시=Mock(), _프로파일_전역반영=Mock())
        for name in ('_서식예시_경로', '_서식예시_원본사본', '_서식예시_기록', '_서식예시_폴더_준비', '_서식예시_동기화',
                     '_서식예시_원본_보관', '_서식_파일_저장'):
            setattr(app, name, types.MethodType(getattr(self.gui, name), app))
        return app

    def test_startup_puts_standard_sample_and_unchanged_file_does_nothing(self):
        app = self.fake()
        app._서식예시_폴더_준비()
        sample = self.dir / 'HWP_AUTODOCFIT' / '서식예시' / '기본 서식.hwpx'
        self.assertTrue(sample.is_file())
        self.assertEqual(app._서식예시_동기화(), ([], None))       # 고치지 않았으면 설정을 건드리지 않는다
        app._프로파일_전역반영.assert_not_called()

    def test_edited_standard_sample_updates_settings_then_deleting_it_resets(self):
        app = self.fake()
        app._서식예시_폴더_준비()
        sample = self.dir / 'HWP_AUTODOCFIT' / '서식예시' / '기본 서식.hwpx'
        before = copy.deepcopy(app._프로파일들[''])
        before['format']['사용자_화면값'] = '그대로'           # 앱 화면에서 고친 값(예시 파일과 무관)
        app._프로파일들[''] = before
        edited = self.make('edited.hwpx', fx.HEADER.replace('height="1500"', 'height="1700"'))
        sample.write_bytes(edited.read_bytes())               # 사용자가 한/글에서 글자 크기를 고쳐 저장
        changed, message = app._서식예시_동기화()
        self.assertTrue(changed)
        self.assertIn('반영', message)
        after = app._프로파일들['']
        self.assertNotEqual(after['format'], before['format'])
        self.assertEqual(after['format']['사용자_화면값'], '그대로')
        app._프로파일_전역반영.assert_called_once()
        override = self.dir / 'appdata' / 'formats' / '_standard.json'
        self.assertTrue(override.is_file())                   # 바뀐 기본 서식은 따로 저장한다
        self.assertEqual(app._서식예시_동기화(), ([], None))   # 다시 시작해도 같은 변경을 두 번 옮기지 않는다
        # 서식 목록은 바뀐 기본 서식을 기본 서식 자리에 쓴다.
        listed = self.ns['서식프로파일_목록'].__globals__
        saved = listed['서식프로파일_폴더']
        listed['서식프로파일_폴더'] = lambda: self.dir / 'appdata' / 'formats'
        try:
            profiles = self.ns['서식프로파일_목록']()
        finally:
            listed['서식프로파일_폴더'] = saved
        self.assertEqual(profiles['']['format'], json.loads(json.dumps(after['format'], ensure_ascii=False)))
        self.assertNotIn('_standard', profiles)
        # 예시 파일을 지우면 처음 기본 서식으로 되돌리고 기본 예시를 다시 넣는다.
        sample.unlink()
        app._서식예시_폴더_준비()
        self.assertFalse(override.exists())
        self.assertTrue(sample.is_file())
        self.assertEqual(app._프로파일들['']['format'], self.ns['기본_서식프로파일']()['format'])

    def test_added_format_keeps_source_in_folder_and_text_only_edit_changes_nothing(self):
        profile = dict(self.ns['기본_서식프로파일'](), name='우리 기관')
        app = self.fake({'': self.ns['기본_서식프로파일'](), 'p1': profile}, active='p1')
        source = self.make('source.hwpx', fx.HEADER)
        app._서식예시_원본_보관('p1', source)
        sample = self.dir / 'HWP_AUTODOCFIT' / '서식예시' / '우리 기관.hwpx'
        self.assertEqual(sample.read_bytes(), source.read_bytes())
        info = json.loads(app._서식예시_경로('p1')[1].read_text(encoding='utf-8'))
        self.assertEqual((info['kind'], info['file']), ('source', '우리 기관.hwpx'))
        # 글만 바꾸고(서식 그대로) 저장한 경우: 압축 파일은 달라도 서식 값은 그대로다.
        with zipfile.ZipFile(sample, 'a') as z:
            z.writestr('Preview/PrvText.txt', '글만 바뀜')
        changed, message = app._서식예시_동기화()
        self.assertEqual(changed, [])
        self.assertIn('그대로', message)
        app._프로파일_전역반영.assert_not_called()

    def test_unreadable_sample_keeps_settings(self):
        app = self.fake()
        app._서식예시_폴더_준비()
        sample = self.dir / 'HWP_AUTODOCFIT' / '서식예시' / '기본 서식.hwpx'
        sample.write_bytes(b'not a zip')
        before = copy.deepcopy(app._프로파일들[''])
        changed, message = app._서식예시_동기화()
        self.assertEqual(changed, [])
        self.assertIn('읽지 못해', message)
        self.assertEqual(app._프로파일들[''], before)

    def test_old_examples_in_settings_folder_move_to_sample_folder(self):
        old = self.dir / 'appdata' / 'format_examples'
        old.mkdir(parents=True)
        (old / '서식예시_p1.hwpx').write_bytes(self.bundled.read_bytes())
        (old / '서식예시_p1.json').write_text(json.dumps({'서명': 'abc'}), encoding='utf-8')
        app = self.fake({'': self.ns['기본_서식프로파일'](), 'p1': {'name': '보고서'}})
        app._서식예시_폴더_준비()
        moved = self.dir / 'HWP_AUTODOCFIT' / '서식예시' / '보고서.hwpx'
        self.assertTrue(moved.is_file())
        self.assertFalse((old / '서식예시_p1.hwpx').exists())
        info = json.loads((old / '서식예시_p1.json').read_text(encoding='utf-8'))
        self.assertEqual((info['서명'], info['file'], info['kind']), ('abc', '보고서.hwpx', 'generated'))

    def test_flag_off_keeps_old_locations(self):
        self.globals['알파_서식예시폴더_사용'] = False
        self.globals['서식예시_폴더'] = self.saved['서식예시_폴더']
        self.globals['서식예시_정보_폴더'] = lambda: self.dir / 'appdata' / 'format_examples'
        app = self.fake()
        example, info = app._서식예시_경로('')
        self.assertEqual(example.name, '서식예시__기본.hwpx')
        self.assertEqual(app._서식예시_동기화(), ([], None))


class KioskTest(unittest.TestCase):
    """키오스크식 서식 고르기: 예시 HWPX의 첫 쪽 미리보기 그림을 스틸컷으로 쓰고, 카드를 누르면 그 서식을 고른다."""

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.gui = cls.ns['HwpAutoDocFitGUI']

    def test_still_cut_reads_preview_image_without_hangul(self):
        import io
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sample.hwpx'
            png = io.BytesIO()
            Image.new('RGB', (724, 1024), 'white').save(png, format='PNG')
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('mimetype', 'application/hwp+zip')
                z.writestr('Preview/PrvImage.png', png.getvalue())
            cut = fs.still_cut(path, 300)
            self.assertEqual(Image.open(io.BytesIO(cut)).size, (300, 424))
            self.assertIsNone(fs.still_cut(Path(tmp) / 'none.hwpx'))
            empty = Path(tmp) / 'empty.hwpx'
            with zipfile.ZipFile(empty, 'w') as z:
                z.writestr('mimetype', 'application/hwp+zip')
            self.assertIsNone(fs.still_cut(empty))       # 미리보기가 없는 파일은 글 카드로 보인다

    def test_card_click_selects_format_like_combo(self):
        combo = Mock()
        app = types.SimpleNamespace(running=False, _프로파일_ids=['', 'p1'], main_profile_combo=combo,
                                    _프로파일들={'': {}, 'p1': {'name': '우리 기관'}}, _프로파일_선택=Mock(),
                                    status_var=Mock())
        pick = types.MethodType(self.gui._서식_키오스크_고르기, app)
        self.assertTrue(pick('p1'))
        combo.current.assert_called_once_with(1)
        self.assertIs(app._프로파일_선택.call_args[0][0].widget, combo)
        self.assertFalse(pick('없는 서식'))
        app.running = True
        self.assertFalse(pick(''))                       # 작업 중에는 바꾸지 않는다


class AppFolderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_dll_lives_in_dll_subfolder_with_new_registry_name(self):
        ns = self.ns
        self.assertEqual(ns['HWP_AUTOMATION_DIR'], Path(r"C:\HWP_AUTODOCFIT"))
        self.assertEqual(ns['TARGET_DLL'], Path(r"C:\HWP_AUTODOCFIT\dll\HwpAutoDocFitSecurity.dll"))
        self.assertEqual(ns['REGISTRY_VALUE_NAME'], "HwpAutoDocFitSecurity")
        self.assertEqual(ns['REGISTER_MODULE_VALUE'], ns['REGISTRY_VALUE_NAME'])   # 한/글은 두 이름이 같아야 한다
        self.assertEqual(ns['DLL_NAME'], "MapoHwpAutoDocFitSecurity.dll")        # 앱에 포함된 원본 파일 이름

    def test_old_dll_folder_and_registry_value_are_cleaned(self):
        clean = self.ns['이전_보안모듈_정리']
        g = clean.__globals__
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / 'HwpAutomation'
            legacy.mkdir()
            (legacy / fs.LEGACY_DLL_FILE).write_bytes(b'dll')
            module = types.SimpleNamespace(LEGACY_APP_HOME=legacy, LEGACY_DLL_FILE=fs.LEGACY_DLL_FILE,
                                           LEGACY_REGISTRY_VALUE=fs.LEGACY_REGISTRY_VALUE)
            reg = Mock()
            reg.OpenKey.return_value.__enter__ = Mock(return_value='key')
            reg.OpenKey.return_value.__exit__ = Mock(return_value=False)
            saved = {k: g[k] for k in ('서식예시모듈', '로그', 'winreg')}
            g.update(서식예시모듈=module, 로그=Mock(), winreg=reg)
            try:
                clean()
            finally:
                g.update(saved)
            self.assertFalse(legacy.exists())
            reg.DeleteValue.assert_called_once_with('key', 'MapoHwpAutoDocFitSecurity')

    def test_idiom_folders_get_bundled_files_without_overwriting_user_files(self):
        fn = self.ns['상용구_폴더_준비']
        g = fn.__globals__
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            bundled_ido = tmp / 'res' / 'HWP.IDO'
            bundled_body = tmp / 'res' / 'IDIOM'
            bundled_body.mkdir(parents=True)
            bundled_ido.write_bytes(b'[HWPIDIOM]')
            (bundled_body / 'a0000000.HWP').write_bytes(b'body')
            home = tmp / 'HWP_AUTODOCFIT'
            (home / '본문상용구').mkdir(parents=True)
            (home / '본문상용구' / 'a0000000.HWP').write_bytes(b'user')     # 사용자가 바꾼 본문 상용구
            saved = {k: g[k] for k in ('HWP_AUTOMATION_DIR', '번들_상용구_파일_찾기', '번들_본문상용구_폴더')}
            g.update(HWP_AUTOMATION_DIR=home, 번들_상용구_파일_찾기=lambda: bundled_ido,
                     번들_본문상용구_폴더=lambda: bundled_body)
            try:
                fn()
            finally:
                g.update(saved)
            self.assertEqual((home / '글자상용구' / 'HWP.IDO').read_bytes(), b'[HWPIDIOM]')
            self.assertEqual((home / '본문상용구' / 'a0000000.HWP').read_bytes(), b'user')


if __name__ == '__main__':
    unittest.main()
