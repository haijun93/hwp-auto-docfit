"""파일 변환 모드: 세부 작업이 없는 모드에서 KeyError 없이 동작하고 준비 안 된 형식은 시작하지 않는다."""
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from desktop_web_ui import DesktopWebBridge
from tests.gui_support import gui_root


class FileFormatModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {'APPDATA': self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        ns = runpy.run_path(str(Path(__file__).parents[1] / 'hwp-auto-docfit.py'), run_name='file_format_mode_test')
        self.root = gui_root(ns['TkinterDnD'].Tk, ns)
        self.addCleanup(self.root.destroy)
        self.root.withdraw()
        self.root.report_callback_exception = lambda *exc: self.errors.append(exc)
        self.errors = []
        self.app = ns['HwpAutoDocFitGUI'](self.root)
        self.bridge = DesktopWebBridge(self.app)
        self.bridge._tk = lambda callback, **kwargs: callback()
        self.bridge._conversion_prerequisites = lambda: {
            'kordoc': {'available': False, 'reason': 'kordoc 없음'}, 'pandoc': False, 'hwp_com': True}
        documents = []
        for name in ('보고서.hwpx', '취합.hwp'):
            path = Path(self.temp.name) / name
            path.write_bytes(b'not a real document')
            documents.append(str(path))
        self.app.files = documents

    def test_selecting_file_format_mode_has_no_stage_lookup_errors(self):
        self.bridge.set_mode('file_format')
        self.root.update()
        self.assertEqual(self.app.selected_mode.get(), 'file_format')
        self.assertIn('파일 형식', self.app.options_summary.cget('text'))
        # 세부 작업 명령은 이 모드에서 아무것도 하지 않는다.
        self.bridge.stage_config('all', {'enabled': False})
        self.bridge.reset_stages()
        self.bridge.set_stage_default(True)
        self.app._세부작업_열기('file_format')
        state = self.bridge.get_state()
        self.assertEqual(state['stages'], [])
        self.assertEqual(self.errors, [])

    def test_hwp_and_hwpx_offer_pdf_and_images_without_kordoc(self):
        self.bridge.set_mode('file_format')
        targets = {item['format']: item for item in self.bridge.get_state()['conversion_targets']}
        self.assertEqual(set(targets), {'hwpx', 'pdf', 'pdfz', 'pdfm', 'docx', 'epub', 'html', 'jpg', 'png', 'txt', 'md'})
        self.assertFalse(targets['pdfz']['enabled'])
        self.assertTrue(targets['pdf']['enabled'])
        self.assertTrue(targets['jpg']['enabled'] and targets['png']['enabled'])
        self.assertFalse(targets['hwpx']['enabled'])

    def _use(self, *names):
        documents = []
        for name in names:
            path = Path(self.temp.name) / name
            path.write_bytes(b'not a real document')
            documents.append(str(path))
        self.app.files = documents
        self.bridge.set_mode('file_format')
        return {item['format']: item for item in self.bridge.get_state()['conversion_targets']}

    def test_same_format_target_is_disabled(self):
        targets = self._use('가.pdf', '나.pdf')
        self.assertFalse(targets['pdf']['enabled'])
        self.assertIn('같은 형식', targets['pdf']['reason'])
        self.assertTrue(targets['pdfz']['enabled'])          # PDF 압축은 PDF→PDF가 목적
        targets = self._use('보고서.hwpx')
        self.assertFalse(targets['hwpx']['enabled'])
        self.assertIn('같은 형식', targets['hwpx']['reason'])
        targets = self._use('사진.jpeg')
        self.assertFalse(targets['jpg']['enabled'])
        targets = self._use('가.pdf', '보고서.hwpx')             # 섞여 있으면 PDF를 고를 수 있다
        self.assertTrue(targets['pdf']['enabled'])

    def test_merge_target_needs_two_files(self):
        targets = self._use('가.pdf')
        self.assertFalse(targets['pdfm']['enabled'])
        targets = self._use('가.pdf', '사진.png')                # PDF·그림만이면 한/글 없이 합친다
        self.assertTrue(targets['pdfm']['enabled'])
        targets = self._use('가.pdf', '보고서.hwpx', '사진.jpg')
        self.assertTrue(targets['pdfm']['enabled'])

    def test_disabled_target_is_refused_before_conversion_starts(self):
        self.bridge.set_mode('file_format')
        self.bridge.set_conversion_target('hwpx')
        with patch.object(self.app, '파일포맷_변경_시작') as start:
            with self.assertRaisesRegex(ValueError, 'kordoc 없음'):
                self.bridge.start('file_format')
        start.assert_not_called()
        self.assertFalse(self.app.running)

    def _run_worker(self, target):
        self.app.파일포맷_변경_시작(target)
        self.app.worker.join(30)
        self.assertFalse(self.app.worker.is_alive())
        events = []
        queue = self.ns_queue()
        while not queue.empty():
            events.append(queue.get_nowait())
        return events

    def ns_queue(self):
        return self.app.파일포맷_변경_시작.__globals__['gui_queue']

    def test_merge_pdf_and_image_into_one_pdf_without_hwp(self):
        from PIL import Image
        from pypdf import PdfReader, PdfWriter
        folder = Path(self.temp.name)
        writer = PdfWriter()
        writer.add_blank_page(200, 200)
        writer.add_blank_page(200, 200)
        with open(folder / '가.pdf', 'wb') as stream:
            writer.write(stream)
        Image.new('RGBA', (60, 40), (255, 0, 0, 128)).save(folder / '나.png')
        self.app.files = [str(folder / '가.pdf'), str(folder / '나.png')]
        events = self._run_worker('pdfm')
        saved = [event for event in events if event[0] == 'saved']
        self.assertEqual(len(saved), 1)
        merged = Path(saved[0][2])
        self.assertEqual(merged.name, '가 외 1개(합친 PDF).pdf')
        self.assertEqual(len(PdfReader(str(merged)).pages), 3)
        self.assertIn(('file_conversion_finished', 1, 0), events)

    def test_pdf_to_png_renders_pages_without_hwp(self):
        from pypdf import PdfWriter
        folder = Path(self.temp.name)
        writer = PdfWriter()
        writer.add_blank_page(100, 100)
        with open(folder / '쪽.pdf', 'wb') as stream:
            writer.write(stream)
        self.app.files = [str(folder / '쪽.pdf')]
        self.bridge.set_mode('file_format')
        targets = {item['format']: item for item in self.bridge.get_state()['conversion_targets']}
        self.assertTrue(targets['png']['enabled'])
        with patch.dict(self.app.파일포맷_변경_시작.__globals__, {'한글_COM_인스턴스_생성': None}):
            events = self._run_worker('png')   # 한/글을 만들려 하면 None 호출로 실패한다
        saved = [event for event in events if event[0] == 'saved']
        self.assertEqual(len(saved), 1)
        self.assertTrue(Path(saved[0][2]).is_file())

    def test_same_format_files_are_skipped(self):
        folder = Path(self.temp.name)
        (folder / '메모.txt').write_text('글', encoding='utf-8')
        self.app.files = [str(folder / '메모.txt')]
        events = self._run_worker('txt')
        self.assertTrue(any(event[0] == 'document_error' and '건너뛰' in event[2] for event in events))
        self.assertIn(('file_conversion_finished', 0, 1), events)   # 건너뛴 파일은 처리 못 한 수로 센다
        self.assertEqual(sorted(p.name for p in folder.iterdir() if p.name.startswith('메모')), ['메모.txt'])


if __name__ == '__main__':
    unittest.main()
