"""알파 1-a: 자간 초기화를 XML에서 한다. 보호 구간(항목기호·라벨)은 그대로, 본문만 0%."""
from pathlib import Path
import runpy
import tempfile
import unittest
import zipfile
from unittest.mock import Mock, patch
from xml.etree import ElementTree as StdET

from defusedxml import ElementTree as ET

from docfit_core import spacing_reset as sr

HH = 'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"'
HP = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
HS = 'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'


def _char(cid, spacing):
    sp = ' '.join(f'{k}="{spacing}"' for k in ('hangul', 'latin', 'hanja', 'japanese', 'other', 'symbol', 'user'))
    return f'<hh:charPr id="{cid}" height="1500"><hh:spacing {sp}/></hh:charPr>'


HEADER = (f'<hh:head {HH}><hh:refList><hh:charProperties itemCnt="2">{_char(0, -5)}{_char(1, 0)}'
          '</hh:charProperties></hh:refList></hh:head>')


def _p(*runs):
    body = ''.join(f'<hp:run charPrIDRef="{c}"><hp:t>{t}</hp:t></hp:run>' for c, t in runs)
    return f'<hp:p paraPrIDRef="0"><hp:linesegarray><hp:lineseg textpos="0"/></hp:linesegarray>{body}</hp:p>'


def tag(e):
    return e.tag.rsplit('}', 1)[-1]


class SpacingResetModuleTest(unittest.TestCase):
    def setUp(self):
        self.header = ET.fromstring(HEADER)

    def spacing_of(self, cid):
        c = next(x for x in self.header.iter() if tag(x) == 'charPr' and x.get('id') == cid)
        return int(next(x for x in c if tag(x) == 'spacing').get('hangul'))

    def test_body_reset_and_marker_kept_by_splitting(self):
        sec = ET.fromstring(f'<hs:sec {HS} {HP}>{_p((0, "ㅇ 추진 배경 설명"))}</hs:sec>')
        stats = sr.reset_spacing(self.header, [sec], lambda text: 2)        # 'ㅇ ' 보호
        runs = [r for r in sec.iter() if tag(r) == 'run']
        self.assertEqual([sr.run_text(r) for r in runs], ['ㅇ ', '추진 배경 설명'])
        self.assertEqual(self.spacing_of(runs[0].get('charPrIDRef')), -5)   # 보호 구간 그대로
        self.assertEqual(self.spacing_of(runs[1].get('charPrIDRef')), 0)
        self.assertEqual(stats['split'], 1)
        self.assertFalse(any(tag(x) == 'linesegarray' for x in sec.iter()))  # 낡은 줄 배치 제거

    def test_zero_spacing_paragraph_untouched_and_ids_reused(self):
        sec = ET.fromstring(f'<hs:sec {HS} {HP}>{_p((1, "그대로"))}{_p((0, "가"))}{_p((0, "나"))}</hs:sec>')
        before = len([x for x in self.header.iter() if tag(x) == 'charPr'])
        stats = sr.reset_spacing(self.header, [sec], lambda text: 0)
        self.assertEqual(stats['paragraphs'], 2)
        self.assertEqual(len([x for x in self.header.iter() if tag(x) == 'charPr']), before + 1)   # 새 글자 모양 하나만
        first = next(x for x in sec if tag(x) == 'p')
        self.assertTrue(any(tag(x) == 'linesegarray' for x in first))    # 바꾸지 않은 문단은 그대로

    def test_run_with_hidden_char_straddling_protection_is_skipped(self):
        sec = ET.fromstring(f'<hs:sec {HS} {HP}><hp:p><hp:run charPrIDRef="0"><hp:t>ㅇ<hp:fwSpace/>본문</hp:t>'
                            '</hp:run></hp:p></hs:sec>')
        stats = sr.reset_spacing(self.header, [sec], lambda text: 1)
        self.assertEqual(stats['skipped'], 1)
        self.assertEqual(stats['runs'], 0)

    def test_paragraphs_inside_tables_are_reset(self):
        cell = f'<hp:tbl><hp:tr><hp:tc><hp:subList>{_p((0, "칸 안 글"))}</hp:subList></hp:tc></hp:tr></hp:tbl>'
        sec = ET.fromstring(f'<hs:sec {HS} {HP}><hp:p><hp:run charPrIDRef="1">{cell}</hp:run></hp:p></hs:sec>')
        stats = sr.reset_spacing(self.header, [sec], lambda text: 0)
        self.assertEqual(stats['paragraphs'], 1)


class SpacingResetAppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_protection_matches_hangul_path_rules(self):
        fn = self.ns['자간보호_글자수']
        self.assertGreater(fn('ㅇ (목적) 본문 내용'), 0)
        self.assertEqual(fn('ㅇ (운영방식)'), len('ㅇ (운영방식)'))     # 라벨만 있는 문단은 끝까지 보호
        self.assertEqual(fn('ㅇ '), len('ㅇ '))

    def test_processor_keeps_text_and_resets_body(self):
        fn = self.ns['자간초기화_hwpx_처리']
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / 'in.hwpx', Path(tmp) / 'out.hwpx'
            with zipfile.ZipFile(src, 'w') as z:
                z.writestr('mimetype', 'application/hwp+zip')
                z.writestr('Contents/header.xml', HEADER)
                z.writestr('Contents/section0.xml', f'<hs:sec {HS} {HP}>{_p((0, "□ 추진 배경 본문"))}</hs:sec>')
            with patch.dict(fn.__globals__, {'로그': Mock()}):
                found = fn(src)
                self.assertEqual(found, {'Contents/section0.xml': [0]})
                self.assertEqual(fn(src, dst, found), 1)
            with zipfile.ZipFile(dst) as z:
                section = StdET.fromstring(z.read('Contents/section0.xml'))
                header = StdET.fromstring(z.read('Contents/header.xml'))
            runs = [r for r in section.iter() if tag(r) == 'run']
            self.assertEqual(''.join(sr.run_text(r) for r in runs), '□ 추진 배경 본문')
            spacing = {c.get('id'): int(next(x for x in c if tag(x) == 'spacing').get('hangul'))
                       for c in header.iter() if tag(c) == 'charPr'}
            self.assertEqual(spacing[runs[0].get('charPrIDRef')], -5)
            self.assertEqual(spacing[runs[-1].get('charPrIDRef')], 0)


if __name__ == '__main__':
    unittest.main()
