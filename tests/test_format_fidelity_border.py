from pathlib import Path
import runpy
import unittest

from defusedxml import ElementTree as ET


MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "format_fidelity_pc.py"))


class BorderFidelityTest(unittest.TestCase):
    def test_serialization_differences_are_ignored(self):
        original = ET.fromstring('<a:borderFill xmlns:a="urn:head" id="1" shadow="0">\n <a:topBorder type="SOLID" color="#000000" />\n</a:borderFill>')
        result = ET.fromstring('<b:borderFill xmlns:b="urn:head" shadow="0" id="9"><b:topBorder color="#000000" type="SOLID"/></b:borderFill>')
        self.assertEqual(MODULE["_border_fill"](original), MODULE["_border_fill"](result))

    def test_visible_border_changes_are_detected(self):
        original = ET.fromstring('<borderFill><topBorder type="SOLID" width="0.1 mm" color="#000000"/></borderFill>')
        for key, value in (("type", "NONE"), ("width", "0.4 mm"), ("color", "#FFFFFF")):
            with self.subTest(key=key):
                result = ET.fromstring(ET.tostring(original))
                result[0].set(key, value)
                self.assertNotEqual(MODULE["_border_fill"](original), MODULE["_border_fill"](result))

    def test_requested_paragraph_and_character_exclusions(self):
        original = ("P", "text", (("prev", "100"), ("next", "200")), [((("ratio", "97"),), "text")], 2)
        result = ("P", "text", (("prev", "0"), ("next", "0")), [((("ratio", "100"),), "text")], 2)
        self.assertEqual(MODULE["_normalized"](original, 2), MODULE["_normalized"](result, 2))

    def test_normalized_text_is_also_used_in_character_runs(self):
        for text, changed in (("ㅇ text", " ㅇ text"), ("ㆍ text", "• text"),
                              ("구분", "구 분"), ("끝.", "  끝."),
                              ("2026.10.25.", "2026. 10. 25.")):
            with self.subTest(text=text):
                original = ("P", text, (), [((), text)], 2)
                result = ("P", changed, (), [((), changed)], 2)
                self.assertEqual(MODULE["_normalized"](original, 2), MODULE["_normalized"](result, 2))
