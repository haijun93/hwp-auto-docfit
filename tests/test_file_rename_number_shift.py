"""V2211-NUM: 파일명 번호 일괄 증감 시 자릿수(폭) 유지 회귀 시험."""
import unittest

from docfit_core.file_rename import Entry, RuleError, apply_rules


def _shift(name, delta, which="first", keep_width=True):
    entry = Entry("1", "/dummy/" + name, 1, 0.0, 0.0)
    rule = {"kind": "number_shift", "delta": delta, "which": which, "keep_width": keep_width}
    results = apply_rules([entry], [rule])
    new_name, err, _ = results[0]
    if err:
        raise RuleError(err)
    return new_name


class NumberShiftTests(unittest.TestCase):
    def test_default_keep_width(self):
        """1. 기본 폭 유지: doc_10 -> doc_09 및 data_1000 -> data_0999 단언."""
        self.assertEqual(_shift("doc_10.txt", -1), "doc_09.txt")
        self.assertEqual(_shift("data_1000.dat", -1), "data_0999.dat")

    def test_zero_padded_number_shift(self):
        """2. 0 채움 숫자 증감: img_008 -> img_010 및 test_00 -> test_01 단언."""
        self.assertEqual(_shift("img_008.png", +2), "img_010.png")
        self.assertEqual(_shift("test_00.log", +1), "test_01.log")

    def test_natural_digit_expansion(self):
        """3. 자릿수 자연 확장: item_9 -> item_10 및 item_99 -> item_100 단언."""
        self.assertEqual(_shift("item_9.csv", +1), "item_10.csv")
        self.assertEqual(_shift("item_99.csv", +1), "item_100.csv")

    def test_keep_width_false_compatibility(self):
        """4. keep_width=False 호환성: doc_10 -> doc_9 단언 (0으로 시작하지 않으면 1자리)."""
        self.assertEqual(_shift("doc_10.txt", -1, keep_width=False), "doc_9.txt")

    def test_negative_number_safety_exception(self):
        """5. 음수 안전 예외: file_0에 delta=-1 적용 시 RuleError 발생 단언."""
        with self.assertRaises(RuleError) as cm:
            _shift("file_0.txt", -1)
        self.assertIn("0보다 작아집니다", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
