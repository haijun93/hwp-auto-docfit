from __future__ import annotations

from contextlib import ExitStack
import os
import unittest
from unittest.mock import Mock, patch

from docfit_core.file_rename import Entry, build_plan, invalid_name_reason

LENGTH_REASON = "이름이 UTF-16 기준 255단위를 넘습니다(일부 이모지는 2단위로 계산됩니다)."


def _entry(entry_id: str, name: str) -> Entry:
    return Entry(entry_id, os.path.join("virtual", name), size=1, mtime=0.0, ctime=0.0)


class FileRenameNameLimitTests(unittest.TestCase):
    def test_bmp_name_length_boundary(self) -> None:
        chars = [("ascii", "a"), ("hangul", "한")]
        exts = [("no_ext", ""), ("txt", ".txt")]
        unit_cases = [(255, None), (256, LENGTH_REASON)]
        for char_label, ch in chars:
            for ext_label, ext in exts:
                for units, expected_reason in unit_cases:
                    sub_label = f"{char_label}_{ext_label}_{units}"
                    with self.subTest(label=sub_label):
                        name = ch * (units - len(ext)) + ext
                        self.assertEqual(len(name.encode("utf-16-le")) // 2, units)
                        reason = invalid_name_reason(name)
                        if expected_reason is None:
                            self.assertIsNone(reason)
                        else:
                            self.assertEqual(reason, expected_reason)

    def test_emoji_name_length_boundary(self) -> None:
        cases = [
            ("emoji_255", "😀" * 125 + "a.txt", 255, None),
            ("emoji_256", "😀" * 126 + ".txt", 256, LENGTH_REASON),
            ("emoji_258", "😀" * 127 + ".txt", 258, LENGTH_REASON),
        ]
        for label, name, expected_units, expected_reason in cases:
            with self.subTest(label=label):
                self.assertEqual(len(name.encode("utf-16-le")) // 2, expected_units)
                reason = invalid_name_reason(name)
                if expected_reason is None:
                    self.assertIsNone(reason)
                else:
                    self.assertEqual(reason, expected_reason)

    def test_mixed_name_length_boundary_and_short_names(self) -> None:
        cases = [
            ("mixed_255", "한A😀" * 62 + "한ab.txt", 255, None),
            ("mixed_256", "한A😀" * 62 + "한abc.txt", 256, LENGTH_REASON),
            ("short_10", "보고서A😀.txt", 10, None),
            ("short_4", "한A😀", 4, None),
            ("ext_emoji_254", "a." + "😀" * 126, 254, None),
            ("ext_emoji_256", "a." + "😀" * 127, 256, LENGTH_REASON),
        ]
        for label, name, expected_units, expected_reason in cases:
            with self.subTest(label=label):
                self.assertEqual(len(name.encode("utf-16-le")) // 2, expected_units)
                reason = invalid_name_reason(name)
                if expected_reason is None:
                    self.assertIsNone(reason)
                else:
                    self.assertEqual(reason, expected_reason)

    def test_override_rejects_overlong_emoji_name(self) -> None:
        overlong_names = [
            ("emoji_256", "😀" * 126 + ".txt"),
            ("emoji_258", "😀" * 127 + ".txt"),
        ]
        for label, name in overlong_names:
            with self.subTest(label=label):
                entry = _entry("one", "a.txt")
                mock_exists = Mock(return_value=False)
                plan = build_plan([entry], rules=[], overrides={entry.id: name}, exists=mock_exists)
                self.assertEqual(len(plan["items"]), 1)
                item = plan["items"][0]
                self.assertEqual(item["status"], "invalid")
                self.assertEqual(item["reason"], LENGTH_REASON)
                self.assertEqual(item["new_name"], name)
                self.assertIsNone(item["new_path"])
                self.assertTrue(item["overridden"])
                self.assertEqual(item["old_name"], "a.txt")
                self.assertEqual(item["old_path"], entry.path)
                self.assertEqual(entry.name, "a.txt")
                self.assertEqual(
                    plan["summary"],
                    {"ok": 0, "unchanged": 0, "conflict": 0, "invalid": 1, "skipped": 0, "executables": 0},
                )
                mock_exists.assert_not_called()

    def test_rule_generated_overlong_name_is_invalid_without_writes(self) -> None:
        entry = _entry("one", "a.txt")
        rules = [{"kind": "replace", "find": "a", "to": "😀" * 126}]
        expected_new_name = "😀" * 126 + ".txt"
        mock_exists = Mock(return_value=False)

        targets = [
            "os.rename", "os.replace", "builtins.open", "io.open", "os.open",
            "os.mkdir", "os.makedirs", "os.unlink", "os.remove", "os.rmdir",
            "pathlib.Path.rename", "pathlib.Path.replace",
            "pathlib.Path.write_text", "pathlib.Path.write_bytes", "pathlib.Path.touch",
        ]
        patched_mocks = []
        with ExitStack() as stack:
            for target in targets:
                m = stack.enter_context(patch(target, side_effect=AssertionError("미리보기 중 파일 변경 호출")))
                patched_mocks.append(m)
            plan = build_plan([entry], rules=rules, exists=mock_exists)

        for m in patched_mocks:
            m.assert_not_called()

        self.assertEqual(len(plan["items"]), 1)
        item = plan["items"][0]
        self.assertEqual(item["status"], "invalid")
        self.assertEqual(item["reason"], LENGTH_REASON)
        self.assertEqual(item["new_name"], expected_new_name)
        self.assertIsNone(item["new_path"])
        self.assertFalse(item["overridden"])
        self.assertEqual(item["old_name"], "a.txt")
        self.assertEqual(item["old_path"], entry.path)
        self.assertEqual(entry.name, "a.txt")
        self.assertEqual(
            plan["summary"],
            {"ok": 0, "unchanged": 0, "conflict": 0, "invalid": 1, "skipped": 0, "executables": 0},
        )
        mock_exists.assert_not_called()

    def test_auto_number_candidates_respect_utf16_limit_without_truncation(self) -> None:
        table = [
            (1, 251, 255, True),
            (2, 252, 256, False),
            (5, 255, 259, False),
        ]
        collision_modes = ["internal", "external"]

        for n, expected_base_units, expected_cand_units, allowed in table:
            stem = "😀" * 123 + "a" * n
            base = stem + ".txt"
            candidate = stem + " (2).txt"

            self.assertIsNone(invalid_name_reason(base))
            self.assertEqual(len(base.encode("utf-16-le")) // 2, expected_base_units)
            self.assertEqual(len(candidate.encode("utf-16-le")) // 2, expected_cand_units)

            for mode in collision_modes:
                sub_label = f"n{n}_{mode}"
                with self.subTest(label=sub_label):
                    if mode == "internal":
                        entry1 = _entry("a", "a.txt")
                        entry2 = _entry("b", "b.txt")
                        entries = [entry1, entry2]
                        overrides = {entry1.id: base, entry2.id: base}
                        mock_exists = Mock(return_value=False)
                        plan = build_plan(
                            entries, rules=[], overrides=overrides, on_conflict="number", exists=mock_exists
                        )

                        self.assertEqual(plan["summary"]["unchanged"], 0)
                        self.assertEqual(plan["summary"]["skipped"], 0)
                        self.assertEqual(plan["summary"]["executables"], 0)

                        item1, item2 = plan["items"]
                        self.assertEqual(item1["old_name"], "a.txt")
                        self.assertEqual(item1["old_path"], entry1.path)
                        self.assertEqual(entry1.name, "a.txt")
                        self.assertEqual(item2["old_name"], "b.txt")
                        self.assertEqual(item2["old_path"], entry2.path)
                        self.assertEqual(entry2.name, "b.txt")

                        if allowed:
                            self.assertEqual([item1["status"], item2["status"]], ["ok", "ok"])
                            self.assertEqual([item1["new_name"], item2["new_name"]], [base, candidate])
                            self.assertEqual(plan["summary"]["ok"], 2)
                            self.assertEqual(plan["summary"]["conflict"], 0)
                            self.assertEqual(plan["summary"]["invalid"], 0)
                            self.assertNotIn("auto_numbered", item1["warnings"])
                            self.assertIn("auto_numbered", item2["warnings"])
                        else:
                            self.assertEqual([item1["status"], item2["status"]], ["ok", "conflict"])
                            self.assertEqual([item1["new_name"], item2["new_name"]], [base, base])
                            self.assertEqual(plan["summary"]["ok"], 1)
                            self.assertEqual(plan["summary"]["conflict"], 1)
                            self.assertEqual(plan["summary"]["invalid"], 0)
                            self.assertNotIn("auto_numbered", item1["warnings"])
                            self.assertNotIn("auto_numbered", item2["warnings"])
                            self.assertEqual(item2["reason"], "목록 안에서 새 이름이 겹칩니다.")

                        for item, ent in zip(plan["items"], entries):
                            self.assertEqual(item["new_path"], os.path.join(ent.folder, item["new_name"]))
                            self.assertTrue(item["new_name"].endswith(".txt"))
                            if item["status"] == "ok":
                                self.assertLessEqual(len(item["new_name"].encode("utf-16-le")) // 2, 255)

                    else:
                        entry1 = _entry("a", "a.txt")
                        entries = [entry1]
                        overrides = {entry1.id: base}
                        mock_exists = Mock(side_effect=lambda path: os.path.basename(path) == base)
                        plan = build_plan(
                            entries, rules=[], overrides=overrides, on_conflict="number", exists=mock_exists
                        )

                        self.assertEqual(plan["summary"]["unchanged"], 0)
                        self.assertEqual(plan["summary"]["skipped"], 0)
                        self.assertEqual(plan["summary"]["executables"], 0)

                        item1 = plan["items"][0]
                        self.assertEqual(item1["old_name"], "a.txt")
                        self.assertEqual(item1["old_path"], entry1.path)
                        self.assertEqual(entry1.name, "a.txt")

                        if allowed:
                            self.assertEqual(item1["status"], "ok")
                            self.assertEqual(item1["new_name"], candidate)
                            self.assertIn("auto_numbered", item1["warnings"])
                            self.assertEqual(plan["summary"]["ok"], 1)
                            self.assertEqual(plan["summary"]["conflict"], 0)
                            self.assertEqual(plan["summary"]["invalid"], 0)
                        else:
                            self.assertEqual(item1["status"], "conflict")
                            self.assertEqual(item1["new_name"], base)
                            self.assertNotIn("auto_numbered", item1["warnings"])
                            self.assertEqual(plan["summary"]["ok"], 0)
                            self.assertEqual(plan["summary"]["conflict"], 1)
                            self.assertEqual(plan["summary"]["invalid"], 0)
                            self.assertEqual(item1["reason"], "같은 이름의 파일이 이미 있습니다.")

                        self.assertEqual(item1["new_path"], os.path.join(entry1.folder, item1["new_name"]))
                        self.assertTrue(item1["new_name"].endswith(".txt"))
                        if item1["status"] == "ok":
                            self.assertLessEqual(len(item1["new_name"].encode("utf-16-le")) // 2, 255)


if __name__ == "__main__":
    unittest.main()
