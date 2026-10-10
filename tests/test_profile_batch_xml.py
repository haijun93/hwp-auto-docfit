"""알파 1-d: 사용자 서식의 계층 추가 서식·복사한 문단 모양을 XML 일괄 서식으로 입힌다."""
from pathlib import Path
import tempfile
import unittest

from docfit_core.batch_format import apply_batch, ParagraphStyle, tag
from tests.test_batch_format import ATTRS, LANGS, RATIOS, fixture, paragraph, roots, shapes

HEADER = (f'''<hh:head xmlns:hh="urn:head" xmlns:hc="urn:core" xmlns:hp="urn:para">
 <hh:fontfaces>{''.join(f'<hh:fontface lang="{lang.upper()}" fontCnt="1"><hh:font id="0" face="원본" type="TTF" isEmbedded="0"/></hh:fontface>' for lang in LANGS)}</hh:fontfaces>
 <hh:refList><hh:charProperties itemCnt="1">
 <hh:charPr id="0" height="1200" textColor="#000000" shadeColor="none"><hh:fontRef {ATTRS}/><hh:ratio {RATIOS}/><hh:spacing {ATTRS}/><hh:offset {ATTRS}/><hh:strikeout shape="NONE"/></hh:charPr>
 </hh:charProperties><hh:paraProperties itemCnt="1"><hh:paraPr id="0">
 <hh:align horizontal="LEFT" vertical="BASELINE"/><hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="BREAK_WORD"/>
 <hp:switch><hp:case required-namespace="urn:core"><hh:margin><hc:intent value="0" unit="HWPUNIT"/><hc:left value="0" unit="HWPUNIT"/><hc:right value="0" unit="HWPUNIT"/><hc:prev value="0" unit="HWPUNIT"/><hc:next value="0" unit="HWPUNIT"/></hh:margin><hh:lineSpacing type="PERCENT" value="150" unit="HWPUNIT"/></hp:case>
 <hp:default><hh:margin><hc:intent value="0" unit="HWPUNIT"/><hc:left value="0" unit="HWPUNIT"/><hc:right value="0" unit="HWPUNIT"/><hc:prev value="0" unit="HWPUNIT"/><hc:next value="0" unit="HWPUNIT"/></hh:margin><hh:lineSpacing type="PERCENT" value="150" unit="HWPUNIT"/></hp:default></hp:switch>
 </hh:paraPr></hh:paraProperties></hh:refList></hh:head>''').encode()


class ProfileExtrasTest(unittest.TestCase):
    def run_plan(self, spec_extra):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'in.hwpx', Path(folder) / 'out.hwpx'
            fixture(source, paragraph('□ 추진 배경'), header=HEADER)
            plan = lambda text, p: ParagraphStyle(text=text, **spec_extra) if text else None
            result = apply_batch(source, target, plan)
            self.assertEqual(result.applied, 1)
            return roots(target)

    def test_char_extras(self):
        header, root = self.run_plan(dict(char_extra=(
            ('color', '#0000FF'), ('italic', True), ('latin_font', 'HY견고딕'), ('latin_type', 'TTF'),
            ('ratio', 95), ('shade', '#FFFF00'), ('spacing', -3), ('underline', 'BOTTOM'))))
        run = next(x for x in root.iter() if tag(x) == 'run')
        shape = shapes(header, 'charPr')[run.get('charPrIDRef')]
        self.assertEqual((shape.get('textColor'), shape.get('shadeColor')), ('#0000FF', '#FFFF00'))
        kids = [tag(x) for x in shape]
        self.assertIn('italic', kids)
        self.assertLess(kids.index('italic'), kids.index('underline'))
        self.assertLess(kids.index('underline'), kids.index('strikeout'))
        ratio = next(x for x in shape if tag(x) == 'ratio')
        spacing = next(x for x in shape if tag(x) == 'spacing')
        self.assertEqual({ratio.get(l) for l in LANGS}, {'95'})
        self.assertEqual({spacing.get(l) for l in LANGS}, {'-3'})
        ref = next(x for x in shape if tag(x) == 'fontRef')
        latin_face = next(f for ff in header.iter() if tag(ff) == 'fontface' and ff.get('lang') == 'LATIN'
                          for f in ff if f.get('id') == ref.get('latin'))
        self.assertEqual(latin_face.get('face'), 'HY견고딕')
        self.assertEqual(ref.get('hangul'), '0')                     # 한글 글꼴은 그대로

    def test_para_extras_case_and_default_values(self):
        header, root = self.run_plan(dict(para_extra=(
            ('align', 'JUSTIFY'), ('break_non_latin', 'KEEP_WORD'), ('intent', -1500), ('left', 2000),
            ('line_type', 'PERCENT'), ('line_value', 160), ('next', 0), ('prev', 1200), ('right', 0))))
        p = next(x for x in root if tag(x) == 'p')
        shape = shapes(header, 'paraPr')[p.get('paraPrIDRef')]
        self.assertEqual(next(x for x in shape if tag(x) == 'align').get('horizontal'), 'JUSTIFY')
        self.assertEqual(next(x for x in shape if tag(x) == 'breakSetting').get('breakNonLatinWord'), 'KEEP_WORD')
        case = next(x for x in shape.iter() if tag(x) == 'case')
        default = next(x for x in shape.iter() if tag(x) == 'default')
        get = lambda part, name: next(x for x in part.iter() if tag(x) == name).get('value')
        self.assertEqual([get(case, n) for n in ('left', 'intent', 'prev')], ['2000', '-1500', '1200'])
        self.assertEqual([get(default, n) for n in ('left', 'intent', 'prev')], ['4000', '-3000', '2400'])
        self.assertEqual((get(case, 'lineSpacing'), get(default, 'lineSpacing')), ('160', '160'))   # 퍼센트는 두 배 아님

    def test_fixed_line_spacing_doubles_in_default(self):
        header, root = self.run_plan(dict(para_extra=(('line_type', 'FIXED'), ('line_value', 1800))))
        p = next(x for x in root if tag(x) == 'p')
        shape = shapes(header, 'paraPr')[p.get('paraPrIDRef')]
        values = [(x.get('type'), x.get('value')) for x in shape.iter() if tag(x) == 'lineSpacing']
        self.assertEqual(values, [('FIXED', '1800'), ('FIXED', '3600')])


if __name__ == '__main__':
    unittest.main()
