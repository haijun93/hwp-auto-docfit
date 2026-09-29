"""장평·자간 실수값이 COM에 0으로 들어가 글자가 눌리는 문제 회귀 검사."""
from pathlib import Path
import runpy
import tempfile
import unittest
from zipfile import ZipFile
from unittest.mock import Mock, patch


class CharShapeValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def apply(self, 글꼴형식=None, **kwargs):
        fn = self.ns['문자모양_적용_현재선택']
        pset = Mock()
        com = Mock()
        com.CreateAction.return_value.CreateSet.return_value = pset
        com.CreateAction.return_value.Execute.return_value = True
        com.FontType.side_effect = {'TTF': 1, 'HFT': 2}.get
        with patch.dict(fn.__globals__, {'hwp': com, '로그': Mock(), '_글꼴형식': 글꼴형식 or {}}):
            fn(**kwargs)
        return {call.args[0]: call.args[1] for call in pset.SetItem.call_args_list}

    def test_float_ratio_and_spacing_become_integers(self):
        items = self.apply(장평=100.0, 자간=-3.0)
        self.assertEqual(items['RatioHangul'], 100)
        self.assertIsInstance(items['RatioHangul'], int)
        self.assertEqual(items['SpacingHangul'], -3)
        self.assertIsInstance(items['SpacingHangul'], int)

    def test_out_of_range_values_are_clamped(self):
        items = self.apply(장평=0, 자간=-80)
        self.assertEqual(items['RatioHangul'], 50)
        self.assertEqual(items['SpacingHangul'], -50)


    def test_font_type_follows_document_header(self):
        # 한/글 내장 HFT 글꼴을 TTF로 지정하면 한/글이 오류 없이 무시한다(실측: 정책회의 ※ 글꼴).
        형식 = {'한양중고딕': 'HFT', '한컴돋움': 'TTF'}
        self.assertEqual(self.apply(글꼴형식=형식, 폰트='한양중고딕')['FontTypeHangul'], 2)
        self.assertEqual(self.apply(글꼴형식=형식, 폰트='한컴돋움')['FontTypeHangul'], 1)
        self.assertEqual(self.apply(폰트='모르는 글꼴')['FontTypeHangul'], 1)

    def test_hwpx_analysis_records_font_types(self):
        header = ('<hh:head xmlns:hh="urn:head"><hh:fontfaces>'
                  '<hh:fontface lang="HANGUL"><hh:font id="0" face="한양중고딕" type="HFT"/>'
                  '<hh:font id="1" face="휴먼명조" type="TTF"/></hh:fontface>'
                  '<hh:fontface lang="LATIN"><hh:font id="0" face="휴먼명조" type="HFT"/></hh:fontface>'
                  '</hh:fontfaces></hh:head>')
        fn = self.ns['_서식통일_HWPX_분석']
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'fonts.hwpx'
            with ZipFile(path, 'w') as archive:
                archive.writestr('Contents/header.xml', header)
                archive.writestr('Contents/section0.xml', '<hs:sec xmlns:hs="urn:section"/>')
            형식 = {}
            with patch.dict(fn.__globals__, {'_글꼴형식': 형식, '_서식통일_HWPX_캐시': {}}):
                fn(path)
        # 같은 이름이 두 형식이면 TTF를 쓴다.
        self.assertEqual(형식, {'한양중고딕': 'HFT', '휴먼명조': 'TTF'})

if __name__ == '__main__':
    unittest.main()
