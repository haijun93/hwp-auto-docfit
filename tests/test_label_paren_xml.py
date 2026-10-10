"""알파 1-b: 문두 라벨 굵게·부연설명 괄호 축소를 XML에서 한다(한/글 경로와 같은 판정)."""
from pathlib import Path
import runpy
import tempfile
import unittest
import zipfile
from unittest.mock import Mock, patch
from xml.etree import ElementTree as StdET

from defusedxml import ElementTree as ET

from docfit_core import char_ranges as cr
from docfit_core.spacing_reset import run_text

HH = 'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"'
HP = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
HS = 'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'
HEADER = (f'<hh:head {HH}><hh:refList><hh:charProperties itemCnt="1">'
          '<hh:charPr id="0" height="1500"><hh:spacing hangul="0"/><hh:underline type="NONE"/></hh:charPr>'
          '</hh:charProperties></hh:refList></hh:head>')


def tag(e):
    return e.tag.rsplit('}', 1)[-1]


def section(*texts):
    body = ''.join(f'<hp:p><hp:run charPrIDRef="0"><hp:t>{t}</hp:t></hp:run></hp:p>' for t in texts)
    return f'<hs:sec {HS} {HP}>{body}</hs:sec>'


class PlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.plan = staticmethod(cls.ns['라벨괄호_계획'])
        cls.g = cls.ns['라벨괄호_계획'].__globals__

    def run_plan(self, text, size=None):
        with patch.dict(self.g, {'괄호_라벨_볼드_사용': True, '괄호_축소_사용': True, '괄호_축소_pt': 2,
                                 '표준서식_설정': {}}):
            return self.plan(text, False, size)

    def test_colon_label_bold(self):
        text = '- 추진부서 : 행정지원과'
        ranges, labeled = self.run_plan(text)
        self.assertIn((text.index('추진부서'), text.index('추진부서') + 4, {'bold': True}), ranges)
        self.assertTrue(labeled)

    def test_leading_paren_label_bold_and_inner_paren_shrinks(self):
        text = 'ㅇ (목적) 주민 편의 증진(이동 시간 단축)'
        ranges, labeled = self.run_plan(text)
        self.assertIn((2, 6, {'bold': True}), ranges)
        start = text.index('(이동')
        self.assertIn((start, len(text), {'shrink_pt': 2.0}), ranges)
        self.assertTrue(labeled)

    def test_already_small_paren_is_skipped(self):
        text = '- 주민 편의 증진(이동 시간 단축) 추진'
        start = text.index('(')
        size = lambda a, b: 13.0 if start <= a < text.index(')') + 1 else 15.0
        ranges, _ = self.run_plan(text, size)
        self.assertFalse(any('shrink_pt' in c for _, _, c in ranges))

    def test_weekday_after_date_is_not_shrunk(self):
        ranges, _ = self.run_plan("’26. 10. 11.(일) 보고(안건)")
        shrunk = [(a, b) for a, b, c in ranges if 'shrink_pt' in c]
        self.assertEqual(shrunk, [(len("’26. 10. 11.(일) 보고"), len("’26. 10. 11.(일) 보고(안건)"))])

    def test_box_paragraph_label_not_bold(self):
        with patch.dict(self.g, {'문두라벨_기호설정': {'□': False, '기타': True}}):
            ranges, labeled = self.run_plan('□ (배경) 설명 글')
        self.assertFalse(labeled)
        self.assertFalse(any(c.get('bold') for _, _, c in ranges))


class XmlApplyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_ranges_split_runs_and_make_bold_and_small_styles(self):
        header = ET.fromstring(HEADER)
        sec = ET.fromstring(section('ㅇ (목적) 본문(설명)'))
        para = next(x for x in sec.iter() if tag(x) == 'p')
        styles = cr.CharStyles(header)
        n = cr.apply_ranges(para, [(2, 6, {'bold': True}), (9, 13, {'shrink_pt': 2.0})], styles)
        self.assertEqual(n, 2)
        runs = [r for r in para if tag(r) == 'run']
        self.assertEqual([run_text(r) for r in runs], ['ㅇ ', '(목적)', ' 본문', '(설명)'])
        self.assertTrue(styles.is_bold(runs[1].get('charPrIDRef')))
        self.assertEqual(styles.height_pt(runs[3].get('charPrIDRef')), 13.0)
        self.assertFalse(styles.is_bold(runs[0].get('charPrIDRef')))
        bold = styles.chars[runs[1].get('charPrIDRef')]
        self.assertLess([tag(x) for x in bold].index('bold'), [tag(x) for x in bold].index('underline'))

    def test_processor_keeps_text_and_applies_consistency(self):
        fn = self.ns['라벨괄호_hwpx_처리']
        texts = ('- 추진부서 : 행정지원과', '- 조례제정 (무료 셔틀버스 운행 근거)')
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / 'in.hwpx', Path(tmp) / 'out.hwpx'
            with zipfile.ZipFile(src, 'w') as z:
                z.writestr('mimetype', 'application/hwp+zip')
                z.writestr('Contents/header.xml', HEADER)
                z.writestr('Contents/section0.xml', section(*texts))
            with patch.dict(fn.__globals__, {'로그': Mock(), '괄호_라벨_볼드_사용': True, '괄호_축소_사용': True,
                                             '괄호_축소_pt': 2, '항목기호_굵게_일관성_사용': True,
                                             '표준서식_설정': {}}):
                self.assertGreater(fn(src, dst, fn(src)), 0)
            with zipfile.ZipFile(dst) as z:
                sec = StdET.fromstring(z.read('Contents/section0.xml'))
                header = StdET.fromstring(z.read('Contents/header.xml'))
        bold_ids = {c.get('id') for c in header.iter() if tag(c) == 'charPr' and any(tag(x) == 'bold' for x in c)}
        paras = [p for p in sec.iter() if tag(p) == 'p']
        self.assertEqual([''.join(run_text(r) for r in p if tag(r) == 'run') for p in paras], list(texts))
        bolded = [[run_text(r) for r in p if tag(r) == 'run' and r.get('charPrIDRef') in bold_ids] for p in paras]
        self.assertEqual(bolded[0], ['추진부서'])
        self.assertEqual(bolded[1], ['조례제정'])         # 같은 기호 '-'의 라벨이 굵어 머리말도 굵게 맞춤


if __name__ == '__main__':
    unittest.main()
