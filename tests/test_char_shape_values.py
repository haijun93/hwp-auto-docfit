"""장평·자간 실수값이 COM에 0으로 들어가 글자가 눌리는 문제 회귀 검사."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class CharShapeValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def apply(self, **kwargs):
        fn = self.ns['문자모양_적용_현재선택']
        pset = Mock()
        com = Mock()
        com.CreateAction.return_value.CreateSet.return_value = pset
        com.CreateAction.return_value.Execute.return_value = True
        with patch.dict(fn.__globals__, {'hwp': com, '로그': Mock()}):
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


if __name__ == '__main__':
    unittest.main()
