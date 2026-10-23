"""글자 상용구 HWPX ↔ HWP.IDO 왕복: 같은 준말 여러 개와 항목 속성을 잃지 않는다(2026-10-23 사용자 요청)."""
import tempfile
import unittest
from pathlib import Path

from docfit_core import hwp_idioms
from docfit_core.hwpx_idioms import HwpxIdiomError, compile_native_idiom_file, parse_hwpx, write_paragraph_document

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "resources" / "서식예시" / "기본 서식.hwpx"
IDO = ROOT / "resources" / "HWP.IDO"


class HwpxIdiomRoundTripTest(unittest.TestCase):
    def _write(self, folder, idioms):
        lines = ["안내 문단"]
        for item in idioms:
            lines += ["#+" + item.key + (f" [속성 {item.attr:04x}]" if item.attr else ""), *item.value.split("\n")]
        return write_paragraph_document(BASE, Path(folder) / "글자상용구.hwpx", lines,
                                        lambda p: parse_hwpx(p, allow_duplicate_keys=True))

    def test_bundled_ido_round_trips_with_duplicates_and_attributes(self):
        original = hwp_idioms.parse(IDO.read_bytes())
        self.assertTrue(any(i.attr for i in original.text))
        with tempfile.TemporaryDirectory() as folder:
            path = self._write(folder, original.text)
            back = compile_native_idiom_file(path, Path(folder) / "없음.hwpx").text
        self.assertEqual([(i.key, i.value, i.attr) for i in original.text], [(i.key, i.value, i.attr) for i in back])

    def test_duplicate_keys_are_rejected_unless_allowed(self):
        items = [hwp_idioms.Idiom("화", "→", 0), hwp_idioms.Idiom("화", "⇒", 0x1348)]
        with tempfile.TemporaryDirectory() as folder:
            path = self._write(folder, items)
            with self.assertRaises(HwpxIdiomError):
                parse_hwpx(path)                       # 본문 상용구처럼 겹치면 안 되는 곳
            self.assertEqual([{"key": "화", "value": "→"}, {"key": "화", "value": "⇒", "attr": 0x1348}],
                             parse_hwpx(path, allow_duplicate_keys=True))


if __name__ == "__main__":
    unittest.main()
