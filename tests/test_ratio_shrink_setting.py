"""장평 줄이기는 기본으로 끈다(2026-10-10 사용자 규칙): 설정에서 켜기 전에는 자간 줄이기·늘리기만 쓴다."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from docfit_core.colon_labels import plan
from docfit_core.connector_tabs import char_em


class RatioShrinkSettingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_default_is_off(self):
        self.assertFalse(self.ns['기본_설정']['ratio_shrink'])
        self.assertFalse(self.ns['장평_줄이기_사용'])

    def test_word_ratio_shrink_does_nothing_when_off(self):
        fn = self.ns['단어_장평_추가축소_시도']
        보관 = Mock(side_effect=AssertionError('장평을 읽거나 바꾸면 안 됨'))
        with patch.dict(fn.__globals__, {'장평_줄이기_사용': False, '단어모드_서식보관': 보관,
                                         '단어모드_장평적용': 보관, '단어모드_자간적용': 보관}):
            self.assertFalse(fn(0, 10, 0, 10, 5))
        보관.assert_not_called()

    def test_colon_labels_use_spacing_and_spaces_only_when_ratio_off(self):
        for label, target in (('장소', 4.0), ('공사명', 4.0), ('행사명', 6.0), ('일시', 5.0), ('기간', 3.0)):
            spaces, spacing, ratio = plan(label, target, allow_ratio=False)
            self.assertEqual(ratio, 100, label)
            self.assertLessEqual(spacing, 50, label)
            width = sum(char_em(c) for c in label) + spaces * (len(label) - 1) * 0.5 \
                + spacing / 100 * sum(char_em(c) for c in label[:-1])
            self.assertAlmostEqual(width, target, delta=0.05, msg=label)


if __name__ == '__main__':
    unittest.main()
