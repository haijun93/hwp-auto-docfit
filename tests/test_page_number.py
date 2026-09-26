"""쪽 판단은 인쇄 쪽 번호가 아니라 문서 안 실제 쪽 순서를 쓴다."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


class PageNumberTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_uses_physical_page_not_printed_number(self):
        fn = self.ns['현재_페이지번호']
        info = type('Info', (), {'CurrentPage': 17})()      # 0부터: 실제 18번째 쪽
        doc = type('Doc', (), {'XHwpDocument': None})()
        doc.Active_XHwpDocument = type('D', (), {'XHwpDocumentInfo': info})()

        class Hwp:
            XHwpDocuments = doc
            def KeyIndicator(self):
                return (True, 1, 1, 1, 1)                     # 인쇄 쪽 번호는 1로 다시 시작
        with patch.dict(fn.__globals__, {'hwp': Hwp()}):
            self.assertEqual(fn(), 18)

    def test_falls_back_to_printed_number(self):
        fn = self.ns['현재_페이지번호']

        class Hwp:
            def KeyIndicator(self):
                return (True, 1, 1, 5, 1)
        with patch.dict(fn.__globals__, {'hwp': Hwp()}):
            self.assertEqual(fn(), 5)


if __name__ == '__main__':
    unittest.main()
