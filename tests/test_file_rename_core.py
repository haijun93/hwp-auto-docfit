import hashlib
import os
import tempfile
import unittest
import zipfile
from datetime import datetime
from pathlib import Path
from defusedxml import ElementTree as ET
from docfit_core.file_rename.doc_title import read_document_title, sanitize_title

from docfit_core.file_rename import (Entry, History, PlanStaleError, RuleError, apply_rules, build_plan,
                                     execute_plan, invalid_name_reason, natural_key, split_name, undo,
                                     validate_rules)


def names(entries, rules, **kw):
    return [r[0] for r in apply_rules(entries, rules, **kw)]


def fake(path, mtime=0.0):
    return Entry(path, path, 10, mtime, mtime)


class RuleTests(unittest.TestCase):
    def test_doc_title_and_template(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def hwpx(name, body):
                path = root / name
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr("Contents/section0.xml", body)
                return Entry.from_path(path)
            table = hwpx("table.hwpx", '<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p><hp:run><hp:tbl><hp:tr><hp:tc><hp:p><hp:run><hp:t>보고서: 계획/안</hp:t></hp:run></hp:p></hp:tc></hp:tr></hp:tbl></hp:run></hp:p></hp:sec>')
            ordinary = hwpx("plain.hwpx", '<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p><hp:run><hp:t>첫 제목</hp:t></hp:run></hp:p></hp:sec>')
            empty = hwpx("empty.hwpx", '<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p/></hp:sec>')
            broken_path = root / "broken.hwpx"
            broken_path.write_bytes(b"not a zip")
            broken = Entry.from_path(broken_path)
            pdf = Entry("pdf", str(root / "file.pdf"), 1, 0, 0)
            rules = [{"kind": "doc_title", "max_length": 60}]
            results = apply_rules([table, ordinary, empty, broken, pdf], rules)
            self.assertEqual(results[0][0], "보고서_ 계획_안.hwpx")
            self.assertEqual(results[1][0], "첫 제목.hwpx")
            self.assertIsNotNone(results[2][1])
            self.assertIsNotNone(results[3][1])
            self.assertEqual(results[4][0], "file.pdf")
            self.assertIn("title_unsupported", results[4][2])
            template = apply_rules([table, pdf], [{"kind": "template", "dept": "기획", "digits": 2}],
                                   today=datetime(2026, 10, 31))
            self.assertEqual(template[0][0], "20261031_기획_보고서_ 계획_안.hwpx")
            self.assertTrue(template[1][0].endswith("_기획_file.pdf"))
            with self.assertRaises(RuleError):
                validate_rules([{"kind": "template", "template": "{wat}"}])

    def test_split_name(self):
        self.assertEqual(split_name("a.b.hwpx"), ("a.b", ".hwpx"))
        self.assertEqual(split_name(".bashrc"), (".bashrc", ""))
        self.assertEqual(split_name("noext"), ("noext", ""))

    def test_replace_plain_regex_case(self):
        e = [fake("/d/IMG_img_01.JPG")]
        self.assertEqual(names(e, [{"kind": "replace", "find": "img_", "to": "", "case": False}]), ["01.JPG"])
        self.assertEqual(names(e, [{"kind": "replace", "find": "img_", "to": ""}]), ["IMG_01.JPG"])
        self.assertEqual(names(e, [{"kind": "replace", "find": r"\d+", "to": r"[\g<0>]", "regex": True}]),
                         ["IMG_img_[01].JPG"])
        self.assertEqual(names(e, [{"kind": "replace", "find": "_", "to": "\\", "count": "first"}]), ["IMG\\img_01.JPG"])

    def test_add_variables_and_clear(self):
        e = [fake("/d/현장/a.jpg")]
        self.assertEqual(names(e, [{"kind": "add", "text": "{folder}", "sep": "_"}]), ["현장_a.jpg"])
        self.assertEqual(names(e, [{"kind": "clear"}, {"kind": "add", "text": "x", "position": "suffix"}]), ["x.jpg"])

    def test_del_pos(self):
        e = [fake("/d/abcdef.txt")]
        self.assertEqual(names(e, [{"kind": "del_pos", "start": 2, "end": 3}]), ["adef.txt"])
        self.assertEqual(names(e, [{"kind": "del_pos", "start": 1, "end": 2, "origin": "end"}]), ["abcd.txt"])
        self.assertEqual(names(e, [{"kind": "del_pos", "start": 3, "end": 99}]), ["ab.txt"])
        with self.assertRaises(RuleError):
            validate_rules([{"kind": "del_pos", "start": 3, "end": 2}])

    def test_del_between_nested(self):
        e = [fake("/d/보고서(초안(2))(자간조정) 최종.hwpx")]
        self.assertEqual(names(e, [{"kind": "del_between"}]), ["보고서 최종.hwpx"])
        self.assertEqual(names(e, [{"kind": "del_between", "nest": "inner"}]), ["보고서(초안) 최종.hwpx"])
        self.assertEqual(names([fake("/d/a[1]b.txt")], [{"kind": "del_between", "open": "[", "close": "]"}]), ["ab.txt"])

    def test_digits(self):
        e = [fake("/d/사진7-2.jpg")]
        self.assertEqual(names(e, [{"kind": "digits_keep"}]), ["72.jpg"])
        self.assertEqual(names(e, [{"kind": "digits_delete"}]), ["사진-.jpg"])
        self.assertEqual(names(e, [{"kind": "digits_pad", "digits": 3}]), ["사진7-002.jpg"])
        self.assertEqual(names(e, [{"kind": "digits_pad", "digits": 3, "which": "first"}]), ["사진007-2.jpg"])

    def test_number_per_folder_not_broken_by_interleaving(self):
        e = [fake("/a/x.jpg"), fake("/a/sub/y.jpg"), fake("/a/z.jpg"), fake("/a/sub/w.jpg")]
        rule = {"kind": "number", "digits": 2, "position": "replace", "per_folder": True}
        self.assertEqual(names(e, [rule]), ["01.jpg", "01.jpg", "02.jpg", "02.jpg"])
        rule = {"kind": "number", "start": 1, "step": 3, "digits": 1, "position": "suffix", "sep": "-"}
        self.assertEqual(names(e[:3], [rule]), ["x-1.jpg", "y-4.jpg", "z-7.jpg"])

    def test_number_shift(self):
        e = [fake("/d/1589(3-1).hwp"), fake("/d/doc009.txt")]
        self.assertEqual(names(e, [{"kind": "number_shift", "delta": -1}]), ["1588(3-1).hwp", "doc008.txt"])
        self.assertEqual(names([fake("/d/099.txt")], [{"kind": "number_shift", "delta": 1}]), ["100.txt"])
        result = apply_rules([fake("/d/a0.txt")], [{"kind": "number_shift", "delta": -1}])
        self.assertIsNone(result[0][0])
        self.assertIn("0보다", result[0][1])

    def test_ext_rules(self):
        e = [fake("/d/a.JPG")]
        self.assertEqual(names(e, [{"kind": "ext_case"}]), ["a.jpg"])
        self.assertEqual(names(e, [{"kind": "ext_replace", "ext": "png"}]), ["a.png"])
        self.assertEqual(names(e, [{"kind": "ext_del"}]), ["a"])
        self.assertEqual(names(e, [{"kind": "ext_add", "ext": ".bak"}]), ["a.JPG.bak"])
        with self.assertRaises(RuleError):
            validate_rules([{"kind": "ext_replace", "ext": "a/b"}])

    def test_date_sources_and_exif_fallback(self):
        mtime = datetime(2026, 10, 31, 9, 5, 7).timestamp()
        e = [Entry("1", "/d/6C1D56A5.JPG", 1, mtime, mtime), Entry("2", "/d/b.txt", 1, mtime, mtime)]
        shot = datetime(2025, 1, 2, 3, 4, 5)
        rules = [{"kind": "date", "source": "exif", "format": "YYYYMMDD", "position": "replace"},
                 {"kind": "number", "digits": 3, "sep": "_"}]
        result = apply_rules(e, rules, exif_reader=lambda path: shot)
        self.assertEqual([r[0] for r in result], ["20250102_001.JPG", "20261031_002.txt"])
        self.assertEqual(result[1][2], {"exif_missing"})
        today = datetime(2026, 1, 9, 13, 0, 0)
        self.assertEqual(names(e[:1], [{"kind": "date", "source": "today", "format": "YY.MM.DD.", "position": "suffix",
                                        "sep": " "}], today=today), ["6C1D56A5 26.01.09..JPG"])
        self.assertEqual(names(e[:1], [{"kind": "date", "source": "mtime", "format": "hhmmss"}]), ["090507_6C1D56A5.JPG"])

    def test_cleanup_nfc_and_suffix(self):
        nfd = "한"  # '한'의 NFD
        e = [fake(f"/d/ {nfd}__글  문서 (자간조정).hwpx")]
        self.assertEqual(names(e, [{"kind": "strip_result_suffix"}, {"kind": "cleanup"}]), ["한_글 문서.hwpx"])
        self.assertEqual(names(e, [{"kind": "cleanup", "underscore": "to_space"}]), ["한 글 문서 (자간조정).hwpx"])

    def test_validation(self):
        for bad in ({"kind": "nope"}, {"kind": "replace"}, {"kind": "replace", "find": "(", "regex": True},
                    {"kind": "number", "digits": 0}, {"kind": "number_shift", "delta": 0},
                    {"kind": "date", "format": "abc"}, {"kind": "number", "per_folder": "yes"}):
            with self.assertRaises(RuleError, msg=bad):
                validate_rules([bad])
        self.assertEqual(validate_rules([{"kind": "clear", "enabled": False}]), [])

    def test_natural_key(self):
        self.assertEqual(sorted(["file10", "File2", "file1"], key=natural_key), ["file1", "File2", "file10"])


class CheckTests(unittest.TestCase):
    def test_invalid_names(self):
        for name in ("", " ", "a:b", "a?.txt", "CON", "con.txt", "NUL .txt", "a.", "a ", "x" * 256, "a\x01"):
            self.assertIsNotNone(invalid_name_reason(name), name)
        for name in ("CONSOLE.txt", "보고서.hwpx", ".hidden"):
            self.assertIsNone(invalid_name_reason(name), name)

    def test_plan_statuses(self):
        e = [fake("/d/a.txt"), fake("/d/b.txt"), fake("/d/c.exe"), fake("/d/d.txt")]
        plan = build_plan(e, [{"kind": "replace", "find": "a", "to": "b"}],
                          overrides={"/d/c.exe": "c.txt", "/d/d.txt": "e:.txt"},
                          exists=lambda p: os.path.basename(p) in {"a.txt", "b.txt", "c.exe", "d.txt"})
        status = {i["old_name"]: i["status"] for i in plan["items"]}
        # a→b: b는 목록에서 움직이지 않으므로(unchanged) 충돌
        self.assertEqual(status, {"a.txt": "conflict", "b.txt": "unchanged", "c.exe": "ok", "d.txt": "invalid"})
        c = next(i for i in plan["items"] if i["old_name"] == "c.exe")
        self.assertEqual(c["warnings"], ["ext_changed", "executable"])
        self.assertEqual(plan["summary"]["executables"], 1)

    def test_duplicates_and_swap_allowed(self):
        e = [fake("/d/a.txt"), fake("/d/b.txt")]
        dup = build_plan(e, [{"kind": "clear"}, {"kind": "add", "text": "x"}], exists=lambda p: False)
        self.assertEqual([i["status"] for i in dup["items"]], ["conflict", "conflict"])
        swap = build_plan(e, [], overrides={"/d/a.txt": "b.txt", "/d/b.txt": "a.txt"}, exists=lambda p: True)
        self.assertEqual([i["status"] for i in swap["items"]], ["ok", "ok"])
        case_only = build_plan([fake("/d/a.txt")], [{"kind": "case", "mode": "upper"}], exists=lambda p: True)
        self.assertEqual(case_only["items"][0]["status"], "ok")

    def test_plan_id_changes_with_file(self):
        a = build_plan([Entry("1", "/d/a.txt", 1, 1.0, 1.0)], [{"kind": "clear"}, {"kind": "add", "text": "b"}],
                       exists=lambda p: False)
        b = build_plan([Entry("1", "/d/a.txt", 2, 1.0, 1.0)], [{"kind": "clear"}, {"kind": "add", "text": "b"}],
                       exists=lambda p: False)
        self.assertNotEqual(a["plan_id"], b["plan_id"])


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.history = History(self.root / "cfg" / "history.jsonl")

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, *names):
        entries = []
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("내용-" + name, encoding="utf-8")
            entries.append(Entry.from_path(path))
        return entries

    def listing(self):
        return sorted(p.name for p in self.root.iterdir() if p.is_file())

    def digest(self):
        return sorted(hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir() if p.is_file())

    def test_apply_and_undo_keep_contents_and_mtime(self):
        e = self.make("6C1D56A5.JPG", "8AA3A713.JPG")
        before, mtimes = self.digest(), sorted(x.mtime for x in e)
        plan = build_plan(e, [{"kind": "clear"}, {"kind": "add", "text": "현장사진"},
                              {"kind": "number", "digits": 2}, {"kind": "ext_case"}])
        result = execute_plan(plan, self.history)
        self.assertEqual(len(result["done"]), 2)
        self.assertEqual(self.listing(), ["현장사진_01.jpg", "현장사진_02.jpg"])
        self.assertEqual(self.digest(), before)
        self.assertEqual(sorted(p.stat().st_mtime for p in self.root.iterdir() if p.is_file()), mtimes)
        back = undo(self.history, result["run_id"])
        self.assertEqual(len(back["done"]), 2)
        self.assertEqual(self.listing(), ["6C1D56A5.JPG", "8AA3A713.JPG"])
        self.assertTrue(self.history.get(result["run_id"])["undone"])

    def test_folder_and_child_file_apply_undo_preserve_hash(self):
        folder = self.root / "기존 폴더"
        folder.mkdir()
        child = folder / "a.txt"
        child.write_text("원본 내용", encoding="utf-8")
        before = hashlib.sha256(child.read_bytes()).hexdigest()
        entries = [Entry.from_path(folder), Entry.from_path(child)]
        # 폴더와 안쪽 파일 이름을 함께 바꾼다(안쪽 새 이름은 옛 폴더 기준으로 계산됨).
        plan = build_plan(entries, [], overrides={entries[0].id: "새 폴더", entries[1].id: "b.txt"})
        self.assertEqual([item["status"] for item in plan["items"]], ["ok", "ok"])
        result = execute_plan(plan, self.history)
        self.assertEqual(result["failed"], [])
        self.assertTrue((self.root / "새 폴더" / "b.txt").is_file())
        self.assertFalse(folder.exists())
        self.assertEqual(hashlib.sha256((self.root / "새 폴더" / "b.txt").read_bytes()).hexdigest(), before)
        back = undo(self.history, result["run_id"])
        self.assertEqual(len(back["done"]), 2)
        self.assertEqual(back["failed"], [])
        self.assertTrue(child.is_file())
        self.assertEqual(hashlib.sha256(child.read_bytes()).hexdigest(), before)

    def test_swap_chain_and_case_only(self):
        e = self.make("a.txt", "b.txt", "c.txt")
        before = {p.name: p.read_text(encoding="utf-8") for p in self.root.iterdir()}
        plan = build_plan(e, [], overrides={e[0].id: "b.txt", e[1].id: "a.txt", e[2].id: "C.txt"})
        self.assertEqual([i["status"] for i in plan["items"]], ["ok", "ok", "ok"])
        result = execute_plan(plan, self.history)
        self.assertEqual(result["failed"], [])
        self.assertEqual((self.root / "b.txt").read_text(encoding="utf-8"), before["a.txt"])
        self.assertEqual((self.root / "a.txt").read_text(encoding="utf-8"), before["b.txt"])
        self.assertIn("C.txt", self.listing())
        self.assertFalse([n for n in os.listdir(self.root) if n.startswith(".rename-tmp")])
        undo(self.history, result["run_id"])
        self.assertEqual({p.name: p.read_text(encoding="utf-8") for p in self.root.iterdir() if p.is_file()}, before)

    def test_chain_order(self):
        e = self.make("1.txt", "2.txt")
        plan = build_plan(e, [], overrides={e[0].id: "2.txt", e[1].id: "3.txt"})
        execute_plan(plan, self.history)
        self.assertEqual(self.listing(), ["2.txt", "3.txt"])
        self.assertEqual((self.root / "2.txt").read_text(encoding="utf-8"), "내용-1.txt")

    def test_stale_plan_changes_nothing(self):
        e = self.make("a.txt", "b.txt")
        plan = build_plan(e, [{"kind": "add", "text": "x"}])
        (self.root / "b.txt").write_text("바뀜!!", encoding="utf-8")
        with self.assertRaises(PlanStaleError):
            execute_plan(plan, self.history)
        self.assertEqual(self.listing(), ["a.txt", "b.txt"])

    def test_never_overwrites_file_appearing_after_preview(self):
        e = self.make("a.txt", "b.txt")
        plan = build_plan(e, [{"kind": "add", "text": "x"}])
        (self.root / "xb.txt").write_text("남의 파일", encoding="utf-8")
        result = execute_plan(plan, self.history)  # 기본: 실패하면 멈춤
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual((self.root / "xb.txt").read_text(encoding="utf-8"), "남의 파일")
        self.assertIn("b.txt", self.listing())

    def test_stop_on_error_restores_temp_names(self):
        e = self.make("a.txt", "b.txt")
        plan = build_plan(e, [], overrides={e[0].id: "b.txt", e[1].id: "a.txt"})
        calls = []

        def flaky(src, dst):
            calls.append((src, dst))
            if len(calls) == 2:
                raise PermissionError("잠김")
            os.rename(src, dst)

        result = execute_plan(plan, self.history, rename=flaky)
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(self.listing(), ["a.txt", "b.txt"])
        self.assertEqual((self.root / "a.txt").read_text(encoding="utf-8"), "내용-a.txt")

    def test_undo_skips_reoccupied_original(self):
        e = self.make("a.txt")
        result = execute_plan(build_plan(e, [{"kind": "add", "text": "x"}]), self.history)
        (self.root / "a.txt").write_text("새 파일", encoding="utf-8")
        back = undo(self.history, result["run_id"])
        self.assertEqual(back["done"], [])
        self.assertEqual(len(back["failed"]), 1)
        self.assertEqual(sorted(self.listing()), ["a.txt", "xa.txt"])

    def test_undo_after_crash_between_intent_and_done(self):
        e = self.make("a.txt")
        run = self.history.new_run("apply")
        src, dst = str(self.root / "a.txt"), str(self.root / "z.txt")
        self.history.write(dict(op="intent", run=run, item=e[0].id, src=src, dst=dst, final=True))
        os.rename(src, dst)  # rename은 됐지만 done 기록 전에 꺼짐
        with open(self.history.path, "a", encoding="utf-8") as stream:
            stream.write('{"op": "done", "run": "' + run[:5])  # 잘린 줄
        undo(self.history, run)
        self.assertEqual(self.listing(), ["a.txt"])

    def test_history_prune_and_runs(self):
        e = self.make("a.txt")
        execute_plan(build_plan(e, [{"kind": "add", "text": "x"}]), self.history)
        runs = self.history.runs()
        self.assertEqual(len(runs), 1)
        self.assertTrue(runs[0]["finished"])
        self.assertEqual(self.history.prune(now=runs[0]["when"] + 31 * 86400), 0)
        self.assertEqual(self.history.runs(), [])


if __name__ == "__main__":
    unittest.main()
