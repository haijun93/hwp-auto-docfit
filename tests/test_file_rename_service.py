import os
import tempfile
import unittest
from pathlib import Path

from docfit_app.file_rename_service import FileRenameService


class FakeDialogs:
    def __init__(self, paths):
        self.paths = paths
        self.calls = []

    def select_files(self, request_id, purpose, mode, multiple):
        self.calls.append((purpose, mode, multiple))
        return {"ok": True, "cancelled": not self.paths, "selection_id": "tok"}

    def resolve_selection(self, selection_id, purpose):
        return list(self.paths)


class FileRenameServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "work"
        self.root.mkdir()
        self.settings = Path(self.tmp.name) / "settings"
        for name in ("6C1D56A5.JPG", "8AA3A713.JPG", "보고서(자간조정).hwpx"):
            (self.root / name).write_text(name, encoding="utf-8")
        (self.root / "sub").mkdir()
        (self.root / "sub" / "c.txt").write_text("c", encoding="utf-8")
        self.service = FileRenameService(self.settings, dialogs=FakeDialogs([str(self.root)]))

    def tearDown(self):
        self.tmp.cleanup()

    def names(self, result):
        return [e["name"] for e in result["entries"]]

    def test_pick_folder_recursive_preview_apply_undo(self):
        listed = self.service.command("pick_folder", {"recursive": True})
        self.assertTrue(listed["ok"], listed)
        self.assertEqual(self.names(listed), ["6C1D56A5.JPG", "8AA3A713.JPG", "보고서(자간조정).hwpx", "c.txt"])
        self.assertNotIn("path", listed["entries"][0])
        ids = [e["id"] for e in listed["entries"]]
        rules = [{"kind": "strip_result_suffix"}, {"kind": "number", "digits": 2, "per_folder": True},
                 {"kind": "ext_case"}]
        preview = self.service.command("preview", {"rules": rules, "excluded": [ids[3]]})
        self.assertEqual([i["new_name"] for i in preview["items"][:3]],
                         ["6C1D56A5_01.jpg", "8AA3A713_02.jpg", "보고서_03.hwpx"])
        self.assertEqual(preview["summary"]["ok"], 3)
        self.assertEqual(preview["summary"]["skipped"], 1)
        applied = self.service.command("apply", {"plan_id": preview["plan_id"]})
        self.assertTrue(applied["ok"], applied)
        self.assertEqual(applied["done"], 3)
        self.assertEqual(self.names(applied)[:3], ["6C1D56A5_01.jpg", "8AA3A713_02.jpg", "보고서_03.hwpx"])
        self.assertTrue((self.root / "보고서_03.hwpx").is_file())
        history = self.service.command("history", {})
        self.assertEqual(history["runs"][0]["count"], 3)
        back = self.service.command("undo", {})
        self.assertEqual(back["done"], 3)
        self.assertTrue((self.root / "보고서(자간조정).hwpx").is_file())
        self.assertEqual(self.names(back)[2], "보고서(자간조정).hwpx")

    def test_stale_plan_and_missing_preview(self):
        self.service.command("pick_folder", {})
        self.assertEqual(self.service.command("apply", {"plan_id": "x"})["code"], "RENAME_PLAN_STALE")
        preview = self.service.command("preview", {"rules": [{"kind": "add", "text": "a"}]})
        self.service.command("sort", {"key": "name", "reverse": True})  # 목록 바뀜 → 다시 미리보기 필요 없음(같은 계획)
        os.utime(self.root / "8AA3A713.JPG", (1, 1))
        result = self.service.command("apply", {"plan_id": preview["plan_id"]})
        self.assertEqual(result["code"], "RENAME_PLAN_STALE")
        self.assertTrue((self.root / "6C1D56A5.JPG").is_file())

    def test_invalid_rule_and_unknown_action(self):
        self.service.command("pick_folder", {})
        self.assertEqual(self.service.command("preview", {"rules": [{"kind": "zzz"}]})["code"], "RENAME_INVALID_RULE")
        self.assertEqual(self.service.command("nope")["code"], "NOT_AVAILABLE")

    def test_executable_needs_confirmation(self):
        (self.root / "tool.bat").write_text("@echo", encoding="utf-8")
        self.service.add_paths([str(self.root / "tool.bat")])
        preview = self.service.command("preview", {"rules": [{"kind": "add", "text": "x"}]})
        self.assertEqual(self.service.command("apply", {"plan_id": preview["plan_id"]})["code"], "RENAME_CONFIRM")
        ok = self.service.command("apply", {"plan_id": preview["plan_id"], "confirm_executables": True})
        self.assertTrue(ok["ok"], ok)

    def test_move_remove_sort_duplicates(self):
        listed = self.service.command("pick_folder", {})
        self.assertEqual(self.service.add_paths([str(self.root / "8AA3A713.JPG")])["added"], 0)
        ids = [e["id"] for e in listed["entries"]]
        moved = self.service.command("move", {"ids": [ids[2]], "delta": -1})
        self.assertEqual([e["id"] for e in moved["entries"]], [ids[0], ids[2], ids[1]])
        moved = self.service.command("move", {"ids": [ids[0]], "delta": 1})
        self.assertEqual([e["id"] for e in moved["entries"]], [ids[2], ids[0], ids[1]])
        self.assertEqual(len(self.service.command("remove", {"ids": [ids[0]]})["entries"]), 2)
        self.assertEqual(self.service.command("remove", {"ids": ["없음"]})["code"], "INVALID_INPUT")
        self.assertEqual(self.service.command("clear")["entries"], [])

    def test_relative_and_missing_paths_rejected(self):
        result = self.service.add_paths(["relative.txt", str(self.root / "없는파일.txt")])
        self.assertEqual(result["added"], 0)
        self.assertEqual(result["skipped_count"], 2)

    def test_rulesets(self):
        listed = self.service.command("ruleset_list")
        self.assertIn("사진 촬영일+번호", [r["name"] for r in listed["rulesets"]])
        saved = self.service.command("ruleset_save", {"name": "내 규칙", "rules": [{"kind": "clear"}]})
        self.assertIn("내 규칙", [r["name"] for r in saved["rulesets"]])
        self.assertEqual(self.service.command("ruleset_save", {"name": "a/b", "rules": []})["code"], "INVALID_INPUT")
        self.assertEqual(self.service.command("ruleset_save", {"name": "x", "rules": [{"kind": "q"}]})["code"],
                         "RENAME_INVALID_RULE")
        deleted = self.service.command("ruleset_delete", {"name": "내 규칙"})
        self.assertNotIn("내 규칙", [r["name"] for r in deleted["rulesets"]])
        reloaded = FileRenameService(self.settings).command("ruleset_list")
        self.assertNotIn("내 규칙", [r["name"] for r in reloaded["rulesets"]])


if __name__ == "__main__":
    unittest.main()
