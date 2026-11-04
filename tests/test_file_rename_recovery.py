"""이름 변경 실패 뒤 임시 이름에 남은 파일 복구 회귀 시험."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path
import tempfile
import unittest

from docfit_core.file_rename.check import _key, build_plan
from docfit_core.file_rename.executor import _rename_no_overwrite, execute_plan, undo
from docfit_core.file_rename.history import History
from docfit_core.file_rename.model import Entry


class RecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.history_path = self.root / "cfg" / "history.jsonl"
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.history = History(self.history_path)

    def _make_entries(self, *names: str, root: Path | None = None) -> list[Entry]:
        target_root = root if root is not None else self.root
        entries = []
        for i, name in enumerate(names):
            p = target_root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"content-{name}-{i}", encoding="utf-8")
            entries.append(Entry.from_path(str(p), entry_id=name))
        return entries

    def _file_names(self, root: Path | None = None) -> list[str]:
        target_root = root if root is not None else self.root
        return sorted([p.name for p in target_root.iterdir() if p.is_file()])

    def _content_hashes(self, root: Path | None = None) -> list[str]:
        target_root = root if root is not None else self.root
        return sorted([
            hashlib.sha256(p.read_bytes()).hexdigest()
            for p in target_root.iterdir()
            if p.is_file()
        ])

    def _assert_case_final_failure(self, *, stop_on_error: bool) -> None:
        entries = self._make_entries("a.txt")
        before_hashes = self._content_hashes()
        plan = build_plan(entries, [], overrides={entries[0].id: "A.txt"})
        self.assertTrue(all(item["status"] == "ok" for item in plan["items"]))

        calls = []
        def wrapper(src, dst):
            calls.append((src, dst))
            if len(calls) == 2:
                raise PermissionError("injected second rename failure")
            return _rename_no_overwrite(src, dst)

        result = execute_plan(plan, self.history, stop_on_error=stop_on_error, rename=wrapper)

        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[1][0], calls[0][1])
        self.assertEqual(calls[2][0], calls[0][1])
        self.assertEqual(calls[2][1], calls[0][0])

        self.assertEqual(self._file_names(), ["a.txt"])
        self.assertEqual(sum(1 for n in self._file_names() if n.startswith(".rename-tmp-")), 0)
        self.assertEqual(result["done"], [])
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(result["failed"][0]["id"], entries[0].id)
        self.assertEqual(result["skipped"], [])
        self.assertEqual(self._content_hashes(), before_hashes)

        reloaded = History(self.history_path)
        run_info = reloaded.get(result["run_id"])
        self.assertIsNotNone(run_info)
        item_info = run_info["items"][entries[0].id]
        self.assertEqual(item_info["original"], str(self.root / "a.txt"))
        self.assertEqual(item_info["current"], str(self.root / "a.txt"))
        self.assertIsNone(item_info["pending"])
        self.assertEqual(item_info["final"], str(self.root / "A.txt"))
        self.assertIsNotNone(item_info["failed"])

        records = [r for r in reloaded.records() if r.get("run") == result["run_id"]]
        intents = [r for r in records if r.get("op") == "intent"]
        dones = [r for r in records if r.get("op") == "done"]
        self.assertFalse(intents[-1].get("final"))
        self.assertEqual(intents[-1].get("dst"), str(self.root / "a.txt"))
        self.assertEqual(dones[-1].get("dst"), str(self.root / "a.txt"))

    def test_first_rename_failure_keeps_original(self):
        entries = self._make_entries("a.txt")
        before_hashes = self._content_hashes()
        plan = build_plan(entries, [], overrides={entries[0].id: "A.txt"})
        self.assertTrue(all(item["status"] == "ok" for item in plan["items"]))

        calls = []
        def wrapper(src, dst):
            calls.append((src, dst))
            if len(calls) == 1:
                raise PermissionError("injected first rename failure")
            return _rename_no_overwrite(src, dst)

        result = execute_plan(plan, self.history, rename=wrapper)

        self.assertEqual(len(calls), 1)
        self.assertEqual(self._file_names(), ["a.txt"])
        self.assertEqual(sum(1 for n in self._file_names() if n.startswith(".rename-tmp-")), 0)
        self.assertEqual(result["done"], [])
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(result["failed"][0]["id"], entries[0].id)
        self.assertEqual(result["skipped"], [])
        self.assertEqual(self._content_hashes(), before_hashes)

        reloaded = History(self.history_path)
        run_info = reloaded.get(result["run_id"])
        self.assertIsNotNone(run_info)
        item_info = run_info["items"][entries[0].id]
        self.assertEqual(item_info["original"], str(self.root / "a.txt"))
        self.assertEqual(item_info["current"], str(self.root / "a.txt"))
        self.assertIsNone(item_info["pending"])
        self.assertIsNotNone(item_info["failed"])
        self.assertEqual(hashlib.sha256(Path(item_info["current"]).read_bytes()).hexdigest(), before_hashes[0])

        records = [r for r in reloaded.records() if r.get("run") == result["run_id"]]
        self.assertFalse(any(rec.get("op") == "done" for rec in records))

    def test_case_final_failure_restores_original_stop_on_error(self):
        self._assert_case_final_failure(stop_on_error=True)

    def test_case_final_failure_restores_original_continue_on_error(self):
        self._assert_case_final_failure(stop_on_error=False)

    def test_unrecovered_temp_preserves_paths_hashes_and_undo(self):
        for stop_val in (True, False):
            with self.subTest(scenario="occupied_original", stop_on_error=stop_val):
                sub_tmp = tempfile.TemporaryDirectory()
                self.addCleanup(sub_tmp.cleanup)
                sub_root = Path(sub_tmp.name)
                sub_hist_path = sub_root / "cfg" / "history.jsonl"
                sub_hist_path.parent.mkdir(parents=True, exist_ok=True)
                sub_history = History(sub_hist_path)

                entries = self._make_entries("a.txt", "b.txt", root=sub_root)
                hash_a = hashlib.sha256((sub_root / "a.txt").read_bytes()).hexdigest()
                hash_b = hashlib.sha256((sub_root / "b.txt").read_bytes()).hexdigest()
                before_hashes = sorted([hash_a, hash_b])

                plan = build_plan(entries, [], overrides={entries[0].id: "b.txt", entries[1].id: "a.txt"})
                self.assertTrue(all(item["status"] == "ok" for item in plan["items"]))

                calls = []
                def wrapper(src, dst):
                    calls.append((src, dst))
                    if os.path.lexists(dst) and _key(src) != _key(dst):
                        self.fail(f"Destination already exists: src={src}, dst={dst}")
                    if len(calls) == 3:
                        raise PermissionError("injected third rename failure")
                    return _rename_no_overwrite(src, dst)

                result = execute_plan(plan, sub_history, stop_on_error=stop_val, rename=wrapper)

                self.assertEqual(len(calls), 3)
                occupied_dest_calls = [c for c in calls[3:] if c[1] == str(sub_root / "a.txt")]
                self.assertEqual(len(occupied_dest_calls), 0)

                self.assertEqual(result["done"], [dict(id=entries[1].id, path=str(sub_root / "a.txt"))])
                self.assertEqual(len(result["failed"]), 1)
                self.assertEqual(result["failed"][0]["id"], entries[0].id)
                self.assertEqual(result["skipped"], [])

                files = [p.name for p in sub_root.iterdir() if p.is_file()]
                self.assertIn("a.txt", files)
                self.assertNotIn("b.txt", files)
                temp_files = [n for n in files if n.startswith(".rename-tmp-")]
                self.assertEqual(len(temp_files), 1)
                temp_path = sub_root / temp_files[0]

                self.assertEqual(hashlib.sha256((sub_root / "a.txt").read_bytes()).hexdigest(), hash_b)
                self.assertEqual(hashlib.sha256(temp_path.read_bytes()).hexdigest(), hash_a)
                self.assertEqual(self._content_hashes(root=sub_root), before_hashes)

                failed_reason = result["failed"][0]["reason"]
                self.assertIn("파일이 열려 있거나 권한이 없습니다.", failed_reason)
                self.assertIn("원래 이름 복구 실패:", failed_reason)
                self.assertIn("같은 이름의 파일이 이미 있습니다.", failed_reason)
                self.assertIn(str(temp_path), failed_reason)

                reloaded = History(sub_hist_path)
                run_info = reloaded.get(result["run_id"])
                self.assertIsNotNone(run_info)
                item_a = run_info["items"][entries[0].id]
                item_b = run_info["items"][entries[1].id]
                self.assertEqual(item_a["current"], str(temp_path))
                self.assertEqual(item_b["current"], str(sub_root / "a.txt"))
                self.assertTrue(os.path.exists(item_a["current"]))
                self.assertTrue(os.path.exists(item_b["current"]))
                self.assertEqual(hashlib.sha256(Path(item_a["current"]).read_bytes()).hexdigest(), hash_a)
                self.assertEqual(hashlib.sha256(Path(item_b["current"]).read_bytes()).hexdigest(), hash_b)
                self.assertIsNone(item_a["pending"])
                self.assertIn(str(temp_path), item_a["failed"])

                undo_res = undo(reloaded, result["run_id"])
                self.assertEqual(len(undo_res["done"]), 2)
                self.assertEqual(len(undo_res["failed"]), 0)
                self.assertEqual(len(undo_res["skipped"]), 0)
                self.assertEqual(self._file_names(root=sub_root), ["a.txt", "b.txt"])
                self.assertEqual(hashlib.sha256((sub_root / "a.txt").read_bytes()).hexdigest(), hash_a)
                self.assertEqual(hashlib.sha256((sub_root / "b.txt").read_bytes()).hexdigest(), hash_b)
                apply_run = reloaded.get(result["run_id"])
                self.assertIsNotNone(apply_run)
                self.assertTrue(apply_run.get("undone"))

        for stop_val in (True, False):
            with self.subTest(scenario="recovery_denied", stop_on_error=stop_val):
                sub_tmp = tempfile.TemporaryDirectory()
                self.addCleanup(sub_tmp.cleanup)
                sub_root = Path(sub_tmp.name)
                sub_hist_path = sub_root / "cfg" / "history.jsonl"
                sub_hist_path.parent.mkdir(parents=True, exist_ok=True)
                sub_history = History(sub_hist_path)

                entries = self._make_entries("a.txt", root=sub_root)
                hash_a = hashlib.sha256((sub_root / "a.txt").read_bytes()).hexdigest()
                before_hashes = [hash_a]

                plan = build_plan(entries, [], overrides={entries[0].id: "A.txt"})
                self.assertTrue(all(item["status"] == "ok" for item in plan["items"]))

                calls = []
                def wrapper(src, dst):
                    calls.append((src, dst))
                    if len(calls) in (2, 3):
                        raise PermissionError(f"injected failure at call {len(calls)}")
                    return _rename_no_overwrite(src, dst)

                result = execute_plan(plan, sub_history, stop_on_error=stop_val, rename=wrapper)
                self.assertEqual(len(calls), 3)
                self.assertEqual(result["done"], [])
                self.assertEqual(len(result["failed"]), 1)
                self.assertEqual(result["failed"][0]["id"], entries[0].id)
                self.assertEqual(result["skipped"], [])

                files = [p.name for p in sub_root.iterdir() if p.is_file()]
                temp_files = [n for n in files if n.startswith(".rename-tmp-")]
                self.assertEqual(len(temp_files), 1)
                temp_path = sub_root / temp_files[0]
                self.assertEqual(self._content_hashes(root=sub_root), before_hashes)

                failed_reason = result["failed"][0]["reason"]
                self.assertIn(str(temp_path), failed_reason)
                self.assertIn("원래 이름 복구 실패:", failed_reason)

                reloaded = History(sub_hist_path)
                run_info = reloaded.get(result["run_id"])
                self.assertIsNotNone(run_info)
                item_a = run_info["items"][entries[0].id]
                self.assertEqual(item_a["current"], str(temp_path))
                self.assertIsNone(item_a["pending"])

                records = [r for r in reloaded.records() if r.get("run") == result["run_id"]]
                intents = [r for r in records if r.get("op") == "intent"]
                fails = [r for r in records if r.get("op") == "fail"]
                self.assertEqual(len(intents), 3)
                self.assertEqual(len(fails), 2)

                undo_res = undo(reloaded, result["run_id"])
                self.assertEqual(len(undo_res["done"]), 1)
                self.assertEqual(self._file_names(root=sub_root), ["a.txt"])
                self.assertEqual(hashlib.sha256((sub_root / "a.txt").read_bytes()).hexdigest(), hash_a)

        with self.subTest(scenario="pending_recovery_denied", stop_on_error=True):
            sub_tmp = tempfile.TemporaryDirectory()
            self.addCleanup(sub_tmp.cleanup)
            sub_root = Path(sub_tmp.name)
            sub_hist_path = sub_root / "cfg" / "history.jsonl"
            sub_hist_path.parent.mkdir(parents=True, exist_ok=True)
            sub_history = History(sub_hist_path)

            entries = self._make_entries("a.txt", "b.txt", root=sub_root)
            hash_a = hashlib.sha256((sub_root / "a.txt").read_bytes()).hexdigest()
            hash_b = hashlib.sha256((sub_root / "b.txt").read_bytes()).hexdigest()
            before_hashes = sorted([hash_a, hash_b])

            plan = build_plan(entries, [], overrides={entries[0].id: "b.txt", entries[1].id: "a.txt"})
            self.assertTrue(all(item["status"] == "ok" for item in plan["items"]))

            calls = []
            def wrapper(src, dst):
                calls.append((src, dst))
                if len(calls) in (2, 3):
                    raise PermissionError(f"injected failure at call {len(calls)}")
                return _rename_no_overwrite(src, dst)

            result = execute_plan(plan, sub_history, stop_on_error=True, rename=wrapper)
            self.assertEqual(len(calls), 3)
            self.assertEqual(result["done"], [])
            self.assertEqual(len(result["failed"]), 2)
            self.assertEqual(set(f["id"] for f in result["failed"]), {entries[0].id, entries[1].id})
            self.assertEqual(result["skipped"], [])

            files = [p.name for p in sub_root.iterdir() if p.is_file()]
            self.assertIn("b.txt", files)
            self.assertNotIn("a.txt", files)
            temp_files = [n for n in files if n.startswith(".rename-tmp-")]
            self.assertEqual(len(temp_files), 1)
            temp_path = sub_root / temp_files[0]

            self.assertEqual(hashlib.sha256((sub_root / "b.txt").read_bytes()).hexdigest(), hash_b)
            self.assertEqual(hashlib.sha256(temp_path.read_bytes()).hexdigest(), hash_a)
            self.assertEqual(self._content_hashes(root=sub_root), before_hashes)

            a_fail = next(f for f in result["failed"] if f["id"] == entries[0].id)
            self.assertIn(str(temp_path), a_fail["reason"])

            reloaded = History(sub_hist_path)
            run_info = reloaded.get(result["run_id"])
            self.assertIsNotNone(run_info)
            item_a = run_info["items"][entries[0].id]
            self.assertEqual(item_a["current"], str(temp_path))
            self.assertTrue(os.path.exists(item_a["current"]))

            undo_res = undo(reloaded, result["run_id"])
            self.assertEqual(len(undo_res["done"]), 1)
            self.assertEqual(self._file_names(root=sub_root), ["a.txt", "b.txt"])
            self.assertEqual(hashlib.sha256((sub_root / "a.txt").read_bytes()).hexdigest(), hash_a)
            self.assertEqual(hashlib.sha256((sub_root / "b.txt").read_bytes()).hexdigest(), hash_b)

    @unittest.skipUnless(os.name == 'nt', 'Windows 공유 잠금 시험')
    def test_windows_share_lock_releases_before_recovery(self):
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create_file = kernel32.CreateFileW
        create_file.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
            ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
            wintypes.HANDLE
        ]
        create_file.restype = wintypes.HANDLE
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = [wintypes.HANDLE]
        close_handle.restype = wintypes.BOOL
        invalid_handle = ctypes.c_void_p(-1).value

        entries = self._make_entries("a.txt")
        before_hashes = self._content_hashes()
        plan = build_plan(entries, [], overrides={entries[0].id: "A.txt"})
        self.assertTrue(all(item["status"] == "ok" for item in plan["items"]))

        calls = []
        lock_errors = []
        close_results = []

        def wrapper(src, dst):
            calls.append((src, dst))
            if len(calls) == 2:
                self.assertEqual(src, calls[0][1])
                handle = create_file(
                    src,
                    0x80000000,
                    0x00000001 | 0x00000002,
                    None,
                    3,
                    0x80,
                    None,
                )
                if handle == invalid_handle:
                    raise ctypes.WinError(ctypes.get_last_error())
                try:
                    _rename_no_overwrite(src, dst)
                except PermissionError as error:
                    lock_errors.append(error)
                    raise
                finally:
                    ok = close_handle(handle)
                    if not ok:
                        raise ctypes.WinError(ctypes.get_last_error())
                    close_results.append(ok)
            return _rename_no_overwrite(src, dst)

        result = execute_plan(plan, self.history, rename=wrapper)

        self.assertEqual(len(lock_errors), 1)
        self.assertEqual(lock_errors[0].winerror, 32)
        self.assertEqual(len(close_results), 1)
        self.assertEqual(len(calls), 3)
        self.assertEqual(self._file_names(), ["a.txt"])
        self.assertEqual(sum(1 for n in self._file_names() if n.startswith(".rename-tmp-")), 0)
        self.assertEqual(result["done"], [])
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(result["failed"][0]["id"], entries[0].id)
        self.assertEqual(result["skipped"], [])
        self.assertEqual(self._content_hashes(), before_hashes)

        reloaded = History(self.history_path)
        run_info = reloaded.get(result["run_id"])
        self.assertIsNotNone(run_info)
        item_info = run_info["items"][entries[0].id]
        self.assertEqual(item_info["current"], str(self.root / "a.txt"))
        self.assertIsNone(item_info["pending"])
        self.assertIsNotNone(item_info["failed"])


if __name__ == '__main__':
    unittest.main()
