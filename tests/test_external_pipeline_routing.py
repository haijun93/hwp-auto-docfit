"""파일 추가에서 허용한 오피스 입력은 실제 후처리 변환기로 연결되어야 한다."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


class ExternalPipelineRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = runpy.run_path(str(Path(__file__).parents[1] / 'hwp-auto-docfit.py'))

    def test_office_inputs_use_existing_safe_kordoc_conversion(self):
        for suffix in ('.xlsx', '.xls', '.pptx', '.hml'):
            with self.subTest(suffix=suffix):
                source, target = Path('source' + suffix), Path('generated.hwpx')
                with patch('docfit_core.kordoc_bridge.convert_to_hwpx', return_value=target) as convert:
                    self.namespace['외부문서_hwpx로_변환'](source, suffix, target)
                convert.assert_called_once_with(source, target)

    def test_unknown_extension_is_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError, '지원하지 않는 변환'):
            self.namespace['외부문서_hwpx로_변환'](Path('source.zip'), '.zip', Path('unused.hwpx'))
