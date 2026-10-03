"""공백 정규화: 단어 사이 연속 공백은 1칸으로, 폭 맞춤 콜론 라벨('일    시:')의 공백은 그대로."""
from pathlib import Path
import runpy
import unittest


class LabelSpacingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def fixed(self, text):
        """정리 대상 구간을 공백 1칸으로 바꾼 결과."""
        for start, end in reversed(self.ns['단어사이_연속공백_정리_대상'](text)):
            text = text[:start] + ' ' + text[end:]
        return text

    def test_spaced_out_colon_labels_keep_their_alignment(self):
        # 실측(10월 확대간부회의 자료): '기    간'이 '기 간'으로 줄어 '참석인원:'과 콜론 위치가 어긋났다.
        for text in [' ㅇ 기    간: 2026. 10. 16.(금)', ' ㅇ 총  무  과: 장소 사용 협조',
                     ' ㅇ 사 업 비: 19,390천원', '   - 일    시 : 10:00', '일    시: 10:00']:
            with self.subTest(text=text):
                self.assertEqual(self.fixed(text), text)

    def test_body_after_label_is_still_normalized(self):
        self.assertEqual(self.fixed(' ㅇ 일    시: 2026.  10.  30.'), ' ㅇ 일    시: 2026. 10. 30.')
        self.assertEqual(self.fixed(' ㅇ  일    시: 10:00'), ' ㅇ 일    시: 10:00')

    def test_word_labels_and_sentences_are_normalized(self):
        self.assertEqual(self.fixed(' ㅇ 관련  부서: 홍보'), ' ㅇ 관련 부서: 홍보')
        self.assertEqual(self.fixed(' ㅇ 동  주민센터: 홍보'), ' ㅇ 동 주민센터: 홍보')
        self.assertEqual(self.fixed(' ㅇ 2026. 9.  ~ 10. : 모집'), ' ㅇ 2026. 9. ~ 10. : 모집')
        self.assertEqual(self.fixed(' ㅇ 가    나 다라마바사 추진'), ' ㅇ 가 나 다라마바사 추진')


if __name__ == '__main__':
    unittest.main()
