import json
from pathlib import Path
import shutil
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from docfit_app.api_contract import ServiceError
from docfit_app.jobs import JobManager
from docfit_app.public_language_service import PublicLanguageService
from docfit_core.korean_proofread import scan_hwpx, load_exclusions, save_exclusions
from docfit_engine.formatter import _install
from desktop_web_ui import DesktopWebBridge, _BrowserApi
from test_korean_proofread import SECTION


class FakeHwp:
    def __init__(self, fixture):
        self.fixture = fixture
        self.opened = []
        self.quit = False

    def RegisterModule(self, *args):
        return True

    def SaveAs(self, target, *args):
        shutil.copy2(self.fixture, target)
        return True

    def Quit(self):
        self.quit = True


class PublicLanguageServiceTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'source.hwpx'
        with ZipFile(self.source, 'w') as archive:
            archive.writestr('Contents/header.xml', '<head/>')
            archive.writestr('Contents/section0.xml', SECTION)
        self.original = self.source.read_bytes()
        self.hwp = FakeHwp(self.source)
        ns = dict(Path=Path, uuid=__import__('uuid'), shutil=shutil,
                  pythoncom=SimpleNamespace(CoInitialize=lambda: None, CoUninitialize=lambda: None),
                  보안모듈_초기화=lambda: None, 한글_COM_인스턴스_생성=lambda **kw: self.hwp,
                  REGISTER_MODULE_NAME='fake', REGISTER_MODULE_VALUE='fake',
                  한글_문서_열기=lambda app, path, fmt: app.opened.append(Path(path)) or True)
        self.prepare = _install(_docfit_namespace=ns, _docfit_symbol='교정용_hwpx_준비')
        self.manager = JobManager()
        self.service = PublicLanguageService(self.folder, self.manager, self.prepare)
        self.addCleanup(lambda: self.manager.shutdown(timeout=1))
        self.addCleanup(self.cleanup_reviews)

    def cleanup_reviews(self):
        for temporary, _, _ in self.service._reviews.values():
            temporary.cleanup()

    def finish(self, identifier, state='done'):
        self.manager.thread(identifier).join(5)
        self.assertEqual(self.manager.status(identifier)['state'], state)
        return next(e['data'] for e in self.manager.events()['events']
                    if e['job_id'] == identifier and e['type'] == state)

    def scan(self, source=None):
        return self.finish(self.service.start([str(source or self.source)]))['result']

    def test_fake_hwp_matches_tk_engine_with_locations(self):
        source = self.folder / 'original.hwp'
        source.write_bytes(b'fake HWP original')
        result = self.scan(source)
        expected = scan_hwpx(self.source)  # Tk worker가 직접 사용하는 같은 함수
        actual = [{k: item[k] for k in expected[0]} for item in result['issues']]
        self.assertEqual(actual, expected)
        self.assertTrue(self.hwp.quit)
        self.assertNotEqual(self.hwp.opened[0], source)
        self.assertEqual(source.read_bytes(), b'fake HWP original')
        self.assertEqual(len({i['id'] for i in result['issues']}), len(expected))
        for item in result['issues']:
            self.assertEqual(len(item['locations']), item['count'])
            self.assertIsNone(item['locations'][0]['page'])
        nested = next(i for i in result['issues'] if i['source'] == '명일')
        self.assertEqual(nested['locations'][0]['paragraph'], 4)
        events = self.manager.events()['events']
        self.assertEqual(events[0]['type'], 'started')
        self.assertIn('progress', [e['type'] for e in events])
        self.assertEqual(events[-1]['type'], 'done')

    def test_selected_ids_apply_snapshot_only_and_preserve_original(self):
        review = self.scan()
        selected = next(i for i in review['issues'] if i['source'] == '금번')
        # 원본이 검사 후 달라져도 결과는 화면에서 검토한 스냅숏에서만 생성한다.
        self.source.write_bytes(b'changed source')
        data = self.finish(self.service.apply(review['review_id'], [selected['id']]))['result']
        output = Path(data['results'][0]['path'])
        self.assertEqual(data['results'][0]['changes'], 2)
        self.assertNotIn('금번', {i['source'] for i in scan_hwpx(output)})
        self.assertIn('몇일', {i['source'] for i in scan_hwpx(output)})
        self.assertEqual(self.source.read_bytes(), b'changed source')
        second = self.finish(self.service.apply(review['review_id'], [selected['id']]))['result']
        self.assertNotEqual(second['results'][0]['path'], str(output))
        with self.assertRaises(ServiceError):
            self.service.apply(review['review_id'], ['unknown'])

    def test_exclusions_share_exact_tk_path_and_format(self):
        path = self.folder / 'proofreading_exclusions.json'
        save_exclusions(path, {'금번'})
        self.assertEqual(self.service.exclusions()['expressions'], ['금번'])
        self.service.exclusions('add', {'expressions': ['몇일', '몇일']})
        self.assertEqual(load_exclusions(path), {'금번', '몇일'})
        self.assertIsInstance(json.loads(path.read_text(encoding='utf-8')), list)
        self.assertNotIn('금번', {i['source'] for i in self.scan()['issues']})
        self.service.exclusions('delete', {'expressions': ['금번']})
        self.assertEqual(load_exclusions(path), {'몇일'})
        save_exclusions(path, set())
        self.assertEqual(self.service.exclusions()['expressions'], [])
        for payload in ({'expressions': 'word'}, {'expressions': ['']}, []):
            with self.assertRaises(ServiceError):
                self.service.exclusions('add', payload)
        path.write_text('{}', encoding='utf-8')
        with self.assertRaises(ServiceError) as error:
            self.service.exclusions()
        self.assertEqual(error.exception.code, 'EXCLUSIONS_FAILED')

    def test_cancel_during_conversion_and_slot_contention(self):
        entered, release = threading.Event(), threading.Event()
        def blocked(source, folder):
            entered.set()
            release.wait(5)
            return source
        self.service.prepare_snapshot = blocked
        identifier = self.service.start([str(self.source)])
        self.assertTrue(entered.wait(2))
        try:
            with self.assertRaises(ServiceError) as error:
                self.service.start([str(self.source)])
            self.assertEqual(error.exception.code, 'JOB_RUNNING')
            self.manager.cancel(identifier)
        finally:
            release.set()
        self.finish(identifier, 'cancelled')
        self.assertFalse(self.service._reviews)
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_cancel_scan_inside_paragraphs(self):
        calls = []
        def cancelled():
            calls.append(1)
            return len(calls) >= 3
        self.assertEqual(scan_hwpx(self.source, locations=True, cancelled=cancelled), [])

    def test_cancel_apply_before_publish_leaves_no_output(self):
        from docfit_core import korean_proofread as core
        review = self.scan()
        selected = review['issues'][0]
        original = core.apply_approved_hwpx
        def cancel_on_apply(*args, **kwargs):
            self.manager.cancel(self.manager.latest()['id'])
            return original(*args, **kwargs)
        with patch('docfit_app.public_language_service.apply_approved_hwpx', cancel_on_apply):
            self.finish(self.service.apply(review['review_id'], [selected['id']]), 'cancelled')
        self.assertFalse(list(self.folder.glob('*_공공언어교정*')))
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_failure_and_invalid_input(self):
        bad = self.folder / 'bad.hwpx'
        bad.write_bytes(b'invalid')
        self.finish(self.service.start([str(bad)]), 'failed')
        for sources in (None, [], ['missing.hwp'], [True]):
            with self.assertRaises(ServiceError):
                self.service.start(sources)

    def test_multiple_documents_ids_and_partial_failure(self):
        second = self.folder / 'second.hwpx'
        shutil.copy2(self.source, second)
        bad = self.folder / 'bad.hwpx'
        bad.write_bytes(b'bad')
        result = self.finish(self.service.start([str(self.source), str(second), str(bad)]))['result']
        self.assertEqual(len(result['errors']), 1)
        selected = next(i for i in result['issues']
                        if i['source_path'] == str(second) and i['source'] == '금번')
        applied = self.finish(self.service.apply(result['review_id'], [selected['id']]))['result']
        self.assertEqual([r['source'] for r in applied['results']], [str(second)])
        self.assertFalse((self.folder / 'source_공공언어교정.hwpx').exists())
        self.assertEqual(second.read_bytes(), self.original)

    def test_bridge_job_envelope_browser_exposure_and_fallback(self):
        def tk_review():
            pass
        with patch.dict(tk_review.__globals__, {'설정_폴더': lambda: self.folder,
                                               '교정용_hwpx_준비': self.prepare}):
            gui = SimpleNamespace(files=[str(self.source)], _job_manager=self.manager,
                                  _공공언어_검토=tk_review, ui_tk_fallback=False)
            bridge = DesktopWebBridge(gui)
            bridge._tk = lambda callback, **kw: callback()
            # 실제 생성 경로도 검증한다.
            self.assertEqual(bridge._public_language_service().exclusion_path,
                             self.service.exclusion_path)
            gui._public_language_backend = self.service
            api = _BrowserApi(bridge)
            self.assertTrue(callable(api.public_language))
            response = api.public_language('start')
            self.assertTrue(response['ok'])
            review = self.finish(response['data']['job_id'])['result']
            applied = api.public_language('apply', {'review_id': review['review_id'],
                                                  'ids': [review['issues'][0]['id']]})
            self.assertTrue(applied['ok'])
            self.finish(applied['data']['job_id'])
            self.assertTrue(api.proofreading_exclusions('add', {'expressions': ['금번']})['ok'])
            self.assertFalse(api.public_language('bad')['ok'])
            self.assertFalse(api.public_language('start', [])['ok'])
            self.finish(bridge.run_tool('proofread')['data']['job_id'])
            gui.ui_tk_fallback = True
            for name in ('_문서검토_열기', '_텍스트로_문서추가_열기', '_붙여넣기_정리_열기',
                         '_아웃라이너_열기', '_작성도우미_열기', 'Markdown_내보내기', '고급문서도구_열기'):
                setattr(gui, name, lambda: None)
            with patch.object(gui, '_공공언어_검토') as tk_fallback:
                self.assertTrue(bridge.run_tool('proofread'))
                tk_fallback.assert_called_once()


if __name__ == '__main__':
    unittest.main()
