"""LABEL228: ❶~❿ 항목은 '-'와 같은 수준·같은 규칙, 라벨 굵게는 본문보다 커지지 않는다."""

from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

from docfit_core.batch_format import ParagraphStyle, apply_batch, plain_text, tag
from docfit_core.continuation import is_continuation
from docfit_core.marker_scheme import BLACK_CIRCLED, classify_marker, detect_scheme
from docfit_core.style_hierarchy import leading_marker
from docfit_core.xml_hanging_indent import hanging_indent_offset
from tests.test_batch_format import ATTRS, HEADER, RATIOS, fixture, roots, shapes

FIXTURE = Path(__file__).parent / 'fixtures/label228_circled_black.hwpx'
SCRIPT = Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'
COM_MODULES = ('winreg', 'pythoncom', 'pywintypes', 'win32com', 'win32com.client', 'win32gui', 'win32con',
               'win32api', 'win32process', 'win32clipboard', 'win32file')


class BlackCircledMarkerTest(unittest.TestCase):
    def test_all_black_circled_digits_are_dash_level(self):
        for marker in BLACK_CIRCLED:
            with self.subTest(marker=marker):
                text = f'   {marker} (라벨) 본문'
                self.assertEqual(classify_marker(text), ('-', 4))
                self.assertEqual(leading_marker(text), ('-', '내용'))
                self.assertEqual(detect_scheme([text]).canonical(text), ('-', 4))
        self.assertIsNone(classify_marker('❶본문'))  # 기호 뒤 빈칸이 없으면 기호가 아니다.

    def test_scheme_levels_of_other_families_are_not_disturbed(self):
        texts = ['□ 가', ' ㅇ 나', '   ❶ 다', '   ❷ 라']
        self.assertEqual(detect_scheme(texts).family_levels, detect_scheme(texts[:2]).family_levels)

    def test_hanging_offset_same_as_dash(self):
        for tail in ('(이동도서관) 서가, 열람공간 운영', '모든 주민 대상: 안내 내용', '노약자 등 대상: 안내 내용'):
            with self.subTest(tail=tail):
                dash, circled = hanging_indent_offset('   - ' + tail), hanging_indent_offset('   ❶ ' + tail)
                self.assertIsNotNone(circled)
                self.assertEqual(circled, dash)
        self.assertEqual(hanging_indent_offset('   ❶ (이동도서관) 서가'), len('   ❶ '))
        self.assertEqual(hanging_indent_offset('   ❶ 모든 주민 대상: 안내'), len('   ❶ 모든 주민 대상: '))

    def test_continuation_still_accepts_every_black_circled_digit(self):
        for marker in BLACK_CIRCLED:
            self.assertTrue(is_continuation(1, f'    {marker} 설명'))


class BlackCircledFormatTest(unittest.TestCase):
    def format_fixture(self):
        stubs = {name: MagicMock() for name in COM_MODULES if name not in sys.modules}
        with patch.dict(sys.modules, stubs):
            namespace = runpy.run_path(str(SCRIPT))
        fn = namespace['표준서식_hwpx_처리']
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        output = Path(folder.name) / 'out.hwpx'
        with patch.dict(fn.__globals__, {
                '알파_일괄서식_가능': lambda: True, '표준서식_내어쓰기_사용': True,
                '_알파_글꼴형식': lambda face: 'TTF', '로그': lambda message: None, '활성_서식예시_파일': None}):
            self.assertGreater(fn(FIXTURE, output), 0)
        return roots(output)

    def runs(self, header, paragraph):
        chars = shapes(header, 'charPr')
        result = []
        for run in paragraph:
            if tag(run) != 'run':
                continue
            shape = chars[run.get('charPrIDRef')]
            font = next(x for x in shape if tag(x) == 'fontRef').get('hangul')
            result.append((run[0].text, shape.get('height'), font, any(tag(x) == 'bold' for x in shape)))
        return result

    def test_circled_items_get_dash_font_size_and_label_only_bold(self):
        header, root = self.format_fixture()
        by_text = {plain_text(p).strip(): p for p in root}
        dash = self.runs(header, by_text['- 운영구분'])
        self.assertEqual(len(dash), 1)
        _, size, font, bold = dash[0]
        self.assertFalse(bold)
        for key, label in (('❶ (가상도서관)', '(가상도서관)'), ('❷ (가상버스)', '(가상버스)'),
                           ('❶ 모든 주민 대상', '모든 주민 대상'), ('❷ 노약자 등 대상', '노약자 등 대상'),
                           ('❸ 학생 등교 대상', '학생 등교 대상')):
            paragraph = next(p for text, p in by_text.items() if text.startswith(key))
            with self.subTest(key=key):
                runs = self.runs(header, paragraph)
                self.assertTrue(all(r[1] == size and r[2] == font for r in runs), runs)
                self.assertEqual([r[0] for r in runs if r[3]], [label])

    def test_label_bold_never_exceeds_body_size_even_if_source_label_was_larger(self):
        header = HEADER.decode().replace('<hh:charProperties itemCnt="2">', '<hh:charProperties itemCnt="3">').replace(
            '</hh:charProperties>',
            f'<hh:charPr id="2" height="1600" textColor="#112233"><hh:fontRef {ATTRS}/><hh:ratio {RATIOS}/>'
            f'<hh:spacing {ATTRS}/><hh:offset {ATTRS}/><hh:bold/></hh:charPr></hh:charProperties>').encode()

        def plan(text, element):
            if not text or not text.lstrip().startswith(('-', '❶')):
                return None
            return ParagraphStyle(text=text.lstrip(), font='서식글꼴', size_pt=14, bold_spans=((2, 6),))

        for marker in ('-', '❶'):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as folder:
                source, target = Path(folder) / 's.hwpx', Path(folder) / 't.hwpx'
                body = ('<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>   ' + marker + ' </hp:t></hp:run>'
                        '<hp:run charPrIDRef="2"><hp:t>운행형태</hp:t></hp:run>'
                        '<hp:run charPrIDRef="0"><hp:t>: 비정기(신청시)</hp:t></hp:run></hp:p>')
                fixture(source, body, header=header)
                apply_batch(source, target, plan)
                new_header, root = roots(target)
                runs = self.runs(new_header, root[0])
                self.assertEqual({r[1] for r in runs}, {'1400'})
                self.assertEqual([r[0] for r in runs if r[3]], ['운행형태'])
                self.assertEqual(plain_text(root[0]), marker + ' 운행형태: 비정기(신청시)')


if __name__ == '__main__':
    unittest.main()
