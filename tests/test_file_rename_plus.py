"""파일명 일괄변경 보강(PowerRename·DarkNamer 벤치마킹): 변수·이름 목록·대소문자·전각/반각·폴더 규칙·충돌 자동 번호."""
import os
import re
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from docfit_core.file_rename import Entry, apply_rules, build_plan, execute_plan, History, undo
from docfit_core.file_rename.rules import RuleError, expand_vars


def names(entries, rules, **kw):
    return [r[0] for r in apply_rules(entries, rules, **kw)]


def fake(path, mtime=0.0, is_folder=False):
    return Entry(path, path, 10, mtime, mtime, is_folder)


class VariableTests(unittest.TestCase):
    def setUp(self):
        self.mtime = datetime(2026, 10, 31, 9, 5, 7, 123000).timestamp()
        self.e = [fake(f"/d/IMG_{i}.jpg", self.mtime) for i in range(3)]

    def test_powerrename_counter(self):
        rule = {"kind": "replace", "find": r"IMG_\d", "to": "사진_${start=10,increment=5,padding=3}", "regex": True}
        self.assertEqual(names(self.e, [rule]), ["사진_010.jpg", "사진_015.jpg", "사진_020.jpg"])
        self.assertEqual(names(self.e[:2], [{"kind": "add", "text": "${}", "position": "suffix", "sep": "-"}]),
                         ["IMG_0-0.jpg", "IMG_1-1.jpg"])

    def test_dates_and_dollar_escape(self):
        rule = {"kind": "add", "text": "$YYYY$MM$DD_$hh$mm$ss_$fff $$", "position": "prefix", "sep": "_"}
        self.assertEqual(names(self.e[:1], [rule]), ["20261031_090507_123 $_IMG_0.jpg"])

    def test_random_and_uuid_lengths(self):
        rule = {"kind": "replace", "find": "IMG", "to": "${rstringalnum=8}-${rstringdigit=4}-${ruuidv4}"}
        result = names(self.e[:2], [rule])
        for name in result:
            self.assertRegex(name, r"^[A-Za-z0-9]{8}-\d{4}-[0-9a-f-]{36}_\d\.jpg$")
        self.assertNotEqual(result[0][:8], result[1][:8])

    def test_regex_dollar_groups(self):
        rule = {"kind": "replace", "find": r"(IMG)_(\d)", "to": "$2-$1", "regex": True}
        self.assertEqual(names(self.e[:1], [rule]), ["0-IMG.jpg"])

    def test_regex_dollar_escape_is_not_a_group(self):
        rule = {"kind": "replace", "find": r"(IMG)", "to": "$$1-$1", "regex": True}
        self.assertEqual(names(self.e[:1], [rule]), ["$1-IMG_0.jpg"])

    def test_dollar_escape_alone_in_replace(self):
        self.assertEqual(names(self.e[:1], [{"kind": "replace", "find": "IMG", "to": "$$"}]), ["$_0.jpg"])

    def test_missing_regex_group_is_rule_error(self):
        for to in ("$3", r"\3", r"\q"):
            with self.subTest(to=to), self.assertRaises(RuleError):
                apply_rules(self.e[:1], [{"kind": "replace", "find": "(IMG)", "to": to, "regex": True}])

    def test_plain_replace_keeps_literal_backslash(self):
        self.assertEqual(names([fake("/d/a_b.txt")], [{"kind": "replace", "find": "_", "to": "\\"}]), ["a\\b.txt"])

    def test_expand_vars_app_vars(self):
        ctx = dict(entry=fake("/d/현장/a.jpg", self.mtime), position=0)
        self.assertEqual(expand_vars("{folder}-{orig}-{date}", ctx), "현장-a-20261031")


class RuleTests(unittest.TestCase):
    def test_names_list(self):
        e = [fake(f"/d/{n}.hwpx") for n in ("a", "b", "c")]
        rule = {"kind": "names_list", "names": "보고서\r\n붙임1\n\n"}
        result = apply_rules(e, [rule])
        self.assertEqual([r[0] for r in result], ["보고서.hwpx", "붙임1.hwpx", "c.hwpx"])
        self.assertIn("names_short", result[2][2])
        full = names(e[:1], [{"kind": "names_list", "names": "새.pdf", "keep_ext": False}])
        self.assertEqual(full, ["새.pdf"])

    def test_case_modes(self):
        e = [fake("/d/hello WORLD file.txt")]
        self.assertEqual(names(e, [{"kind": "case", "mode": "capitalize"}]), ["Hello WORLD file.txt"])
        self.assertEqual(names(e, [{"kind": "case", "mode": "sentence"}]), ["Hello world file.txt"])
        self.assertEqual(names(e, [{"kind": "case", "mode": "title"}]), ["Hello World File.txt"])

    def test_fullwidth_halfwidth(self):
        e = [fake("/d/보고서（２０２６）　Ａ.txt")]
        self.assertEqual(names(e, [{"kind": "cleanup", "width": "half"}]), ["보고서(2026) A.txt"])
        self.assertEqual(names([fake("/d/AB 1.txt")], [{"kind": "cleanup", "width": "full", "strip": False}]),
                         ["ＡＢ　１.txt"])

    def test_rules_apply_to_folders_without_ext_rules(self):
        folder = fake("/d/2025.자료", is_folder=True)
        self.assertEqual(names([folder], [{"kind": "replace", "find": "2025", "to": "2026"},
                                         {"kind": "ext_replace", "ext": "txt"}]), ["2026.자료"])


class ConflictNumberTests(unittest.TestCase):
    def test_auto_number_existing_and_duplicates(self):
        e = [fake("/d/a.txt"), fake("/d/b.txt"), fake("/d/c.txt")]
        rules = [{"kind": "clear"}, {"kind": "add", "text": "x"}]
        blocked = build_plan(e, rules, exists=lambda p: False)
        self.assertEqual(blocked["summary"]["conflict"], 3)
        plan = build_plan(e, rules, exists=lambda p: os.path.basename(p) == "x.txt", on_conflict="number")
        self.assertEqual([i["new_name"] for i in plan["items"]], ["x (2).txt", "x (3).txt", "x (4).txt"])
        self.assertTrue(all("auto_numbered" in i["warnings"] for i in plan["items"]))
        plan = build_plan(e, rules, exists=lambda p: False, on_conflict="number")
        self.assertEqual([i["new_name"] for i in plan["items"]], ["x.txt", "x (2).txt", "x (3).txt"])
        self.assertEqual(plan["summary"]["conflict"], 0)

    def test_auto_number_real_files_apply_undo(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for n in ("a.txt", "b.txt", "x.txt"):
                (root / n).write_text(n, encoding="utf-8")
            entries = [Entry.from_path(root / "a.txt"), Entry.from_path(root / "b.txt")]
            plan = build_plan(entries, [{"kind": "clear"}, {"kind": "add", "text": "x"}], on_conflict="number")
            history = History(root / "h" / "history.jsonl")
            result = execute_plan(plan, history)
            self.assertEqual(result["failed"], [])
            self.assertEqual(sorted(p.name for p in root.iterdir() if p.is_file()), ["x (2).txt", "x (3).txt", "x.txt"])
            self.assertEqual((root / "x.txt").read_text(encoding="utf-8"), "x.txt")  # 남의 파일은 그대로
            undo(history, result["run_id"])
            self.assertEqual(sorted(p.name for p in root.iterdir() if p.is_file()), ["a.txt", "b.txt", "x.txt"])


if __name__ == "__main__":
    unittest.main()
