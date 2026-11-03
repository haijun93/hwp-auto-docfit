"""3.0-α1 LiveLink 서비스·브리지(가짜 한/글로 시험)."""
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from docfit_live import link
from docfit_live.service import LiveLinkService, is_undo_gate_passed, _validate_expected_context, _context_matches
from tests.test_live_link import FakeApp


def session(path, visible=True, in_table=False, document_id="doc-default"):
    app = FakeApp(path, in_table=in_table, document_id=document_id)
    app.XHwpWindows = SimpleNamespace(Active_XHwpWindow=SimpleNamespace(Visible=visible))
    return link.Session("m:" + path, app, path, path.rsplit("\\", 1)[-1])


class LiveServiceTest(unittest.TestCase):
    def service(self, sessions, titles=(), gate_checker=None):
        return LiveLinkService(
            sessions=lambda: sessions,
            titles=lambda: list(titles),
            com_init=False,
            gate_checker=gate_checker or (lambda: True),
        )

    def test_hidden_helper_hangul_is_never_chosen(self):
        user, hidden = session(r"C:\a\보고서.hwpx"), session("", visible=False)
        status = self.service([hidden, user]).status()
        self.assertTrue(status["connected"])
        self.assertEqual(status["title"], "보고서.hwpx")

    def test_front_window_decides_between_many(self):
        a, b = session(r"C:\a\가.hwpx"), session(r"C:\a\나.hwpx")
        svc = self.service([a, b], titles=["나.hwpx [C:\\a\\] - 한글", "가.hwpx - 한글"])
        self.assertEqual(svc.status()["title"], "나.hwpx")
        self.assertEqual(svc.paste()["undo_steps"], 1)
        self.assertEqual((a.app.runs, b.app.runs), ([], ["Paste"]))
        self.assertEqual(self.service([a, b]).status()["code"], "AMBIGUOUS")
        self.assertEqual(self.service([]).status()["code"], "NO_HANGUL")

    def test_commands_run_on_one_thread(self):
        svc, seen = self.service([]), set()
        for _ in range(3):
            svc.call(lambda: seen.add(threading.current_thread().name))
        self.assertEqual(seen, {"docfit-livelink"})
        with self.assertRaises(ValueError):
            svc.call(lambda: (_ for _ in ()).throw(ValueError("x")))
        svc.close()

    def test_undo_gate_requires_explicit_pass_evidence(self):
        repo_root = Path(__file__).resolve().parent.parent
        reports_dir = repo_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        test_gate_path = reports_dir / "_test_live_replace_gate.json"

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)

            # 1. 파일 없음 -> False
            no_file = reports_dir / "does_not_exist_gate.json"
            self.assertFalse(is_undo_gate_passed(no_file))

            # 2. 저장소 외부 경로의 증거 JSON 주입 차단 -> False
            outside_json = tmp_root / "valid_format_outside.json"
            outside_json.write_text(json.dumps({
                "schema_version": 1,
                "gate": "live_replace",
                "status": "PASS",
                "undo_steps": 1,
                "evidence_files": ["tests/test_live_service.py"],
            }), encoding="utf-8")
            self.assertFalse(is_undo_gate_passed(outside_json))

            # 3. 스크립트만 있음 -> False
            script_path = repo_root / "scripts" / "live_replace_gate.py"
            # 실측 스크립트 존재만으로는 게이트 통과 아님
            self.assertFalse(is_undo_gate_passed(script_path))

            # 저장소 내부 게이트 파일 기반 시험
            try:
                # 4. 잘못된 JSON -> False
                test_gate_path.write_text("{bad json...", encoding="utf-8")
                self.assertFalse(is_undo_gate_passed(test_gate_path))

                # 5. status != PASS -> False
                test_gate_path.write_text(json.dumps({
                    "schema_version": 1,
                    "gate": "live_replace",
                    "status": "FAIL",
                    "undo_steps": 1,
                    "evidence_files": ["tests/test_live_service.py"],
                }), encoding="utf-8")
                self.assertFalse(is_undo_gate_passed(test_gate_path))

                # 6. undo_steps != 1 -> False
                test_gate_path.write_text(json.dumps({
                    "schema_version": 1,
                    "gate": "live_replace",
                    "status": "PASS",
                    "undo_steps": 2,
                    "evidence_files": ["tests/test_live_service.py"],
                }), encoding="utf-8")
                self.assertFalse(is_undo_gate_passed(test_gate_path))

                # 7. evidence_files 빈 배열 또는 파일 미존재 -> False
                test_gate_path.write_text(json.dumps({
                    "schema_version": 1,
                    "gate": "live_replace",
                    "status": "PASS",
                    "undo_steps": 1,
                    "evidence_files": [],
                }), encoding="utf-8")
                self.assertFalse(is_undo_gate_passed(test_gate_path))

                test_gate_path.write_text(json.dumps({
                    "schema_version": 1,
                    "gate": "live_replace",
                    "status": "PASS",
                    "undo_steps": 1,
                    "evidence_files": ["does_not_exist_file.txt"],
                }), encoding="utf-8")
                self.assertFalse(is_undo_gate_passed(test_gate_path))

                # 8. evidence_files 상대경로 이탈 (.. 로 저장소 밖 탈출) -> False
                test_gate_path.write_text(json.dumps({
                    "schema_version": 1,
                    "gate": "live_replace",
                    "status": "PASS",
                    "undo_steps": 1,
                    "evidence_files": ["../../outside.txt"],
                }), encoding="utf-8")
                self.assertFalse(is_undo_gate_passed(test_gate_path))

                # 9. evidence_files 외부 절대경로 탈출 -> False
                ext_file = tmp_root / "ext.txt"
                ext_file.write_text("outside evidence", encoding="utf-8")
                test_gate_path.write_text(json.dumps({
                    "schema_version": 1,
                    "gate": "live_replace",
                    "status": "PASS",
                    "undo_steps": 1,
                    "evidence_files": [str(ext_file)],
                }), encoding="utf-8")
                self.assertFalse(is_undo_gate_passed(test_gate_path))

                # 10. 정상 저장소 내부 증거 파일 및 필드 -> True
                ev_file = "tests/test_live_service.py"
                test_gate_path.write_text(json.dumps({
                    "schema_version": 1,
                    "gate": "live_replace",
                    "status": "PASS",
                    "undo_steps": 1,
                    "evidence_files": [ev_file],
                }), encoding="utf-8")
                self.assertTrue(is_undo_gate_passed(test_gate_path))

                # 상대 경로 문자열로 호출해도 저장소 내부 기준 해석 정상 작동
                rel_gate = f"reports/{test_gate_path.name}"
                self.assertTrue(is_undo_gate_passed(rel_gate))

            finally:
                if test_gate_path.exists():
                    test_gate_path.unlink()


class LiveBridgeTest(unittest.TestCase):
    def setUp(self):
        from desktop_web_ui import DesktopWebBridge, _BrowserApi
        self.gui = Mock(files=[], running=False)
        self.bridge = DesktopWebBridge(self.gui)
<<<<<<< HEAD
        self.user = session(r"C:\a\보고서.hwpx")
        self.user.app.XHwpWindows.Active_XHwpWindow.Hwnd = 9
        self.bridge._live = LiveLinkService(sessions=lambda: [self.user], titles=lambda: [], com_init=False)
=======
        self.user = session(r"C:\a\보고서.hwpx", in_table=True, document_id="doc-1")
        self.bridge._live = LiveLinkService(
            sessions=lambda: [self.user], titles=lambda: [], com_init=False, gate_checker=lambda: True
        )
>>>>>>> origin/feature/3.0-wip
        self.assertTrue(callable(getattr(_BrowserApi(self.bridge), "live_link")))

    def test_insert_copies_then_pastes_once_and_restores_clipboard(self):
        order = []
        self.bridge.table_units = Mock(side_effect=lambda a, d: order.append(("copy", a, d)) or {"ok": True})
        with patch("docfit_live.service.save_clipboard", return_value={13: "사용자 글"}), \
                patch("docfit_live.service.restore_clipboard", side_effect=lambda s: order.append(("restore", s)) or True):
            result = self.bridge.live_link("insert", {"source": "table_units", "data": {"id": "g1:1"}})
        self.assertTrue(result["ok"], result)
        self.assertEqual((result["title"], result["undo_steps"]), ("보고서.hwpx", 1))
        self.assertEqual(order, [("copy", "copy", {"id": "g1:1"}), ("restore", {13: "사용자 글"})])
        self.assertEqual(self.user.app.runs, ["Paste"])

    def test_failed_copy_does_not_paste(self):
        self.bridge.table_sketch = Mock(return_value={"ok": False, "message": "표를 만들지 못했습니다."})
        with patch("docfit_live.service.save_clipboard", return_value={}):
            result = self.bridge.live_link("insert", {"source": "table_sketch", "data": {"lines": []}})
        self.assertFalse(result["ok"])
        self.assertEqual(self.user.app.runs, [])

    def test_clipboard_save_failure_preserves_clipboard_and_document(self):
        self.bridge.table_sketch = Mock(return_value={"ok": True})
        with patch("docfit_live.service.save_clipboard", side_effect=link.LiveLinkError("CLIPBOARD_SAVE_FAILED", "보관 실패")) as save, \
                patch("docfit_live.service.restore_clipboard") as restore:
            result = self.bridge.live_link("insert", {"source": "table_sketch", "data": {}})
        self.assertFalse(result["ok"])
        save.assert_called_once()
        self.bridge.table_sketch.assert_not_called()
        restore.assert_not_called()
        self.assertEqual(self.user.app.runs, [])

    def test_restore_failure_is_reported_after_single_insert(self):
        self.bridge.table_sketch = Mock(return_value={"ok": True})
        with patch("docfit_live.service.save_clipboard", return_value={13: "사용자 글"}), \
                patch("docfit_live.service.restore_clipboard", return_value=False):
            result = self.bridge.live_link("insert", {"source": "table_sketch", "data": {}})
        self.assertTrue(result["ok"])
        self.assertFalse(result["clipboard_restored"])
        self.assertIn("복원하지 못", result["clipboard_warning"])
        self.assertEqual(self.user.app.runs, ["Paste"])

    def test_empty_clipboard_is_cleared_after_insert_and_restored(self):
        self.bridge.table_sketch = Mock(return_value={"ok": True})
        saved = {"_empty": True, "_restorable": False}
        with patch("docfit_live.service.save_clipboard", return_value=saved), \
                patch("docfit_live.service.restore_clipboard", return_value=True) as restore:
            result = self.bridge.live_link("insert", {"source": "table_sketch", "data": {}})
        self.assertTrue(result["ok"])
        self.assertTrue(result["clipboard_restored"])
        restore.assert_called_once_with(saved)
        self.assertEqual(self.user.app.runs, ["Paste"])

    def test_unrestorable_clipboard_format_allows_insert_with_warning(self):
        self.bridge.table_sketch = Mock(return_value={"ok": True})
        saved = {"_empty": False, "_restorable": False}
        with patch("docfit_live.service.save_clipboard", return_value=saved), \
                patch("docfit_live.service.restore_clipboard", return_value=False) as restore:
            result = self.bridge.live_link("insert", {"source": "table_sketch", "data": {}})
        self.assertTrue(result["ok"])
        self.assertFalse(result["clipboard_restored"])
        self.assertIn("복원하지 못", result["clipboard_warning"])
        restore.assert_called_once_with(saved)
        self.assertEqual(self.user.app.runs, ["Paste"])

    def test_rejects_bad_input_and_busy_app(self):
        self.assertFalse(self.bridge.live_link("insert", {"source": "exe", "data": {}})["ok"])
        self.assertFalse(self.bridge.live_link("unknown")["ok"])
        self.gui.running = True
        self.assertIn("문서 작업", self.bridge.live_link("insert", {"source": "image", "data": {}})["message"])
        self.assertEqual(self.bridge.live_link("status")["title"], "보고서.hwpx")

    def test_alpha3_disabled_by_default_has_no_com_side_effects(self):
        from desktop_web_ui import DesktopWebBridge
        fresh_gui = Mock(files=[], running=False, settings={"live_alpha3_enabled": False})
        fresh_bridge = DesktopWebBridge(fresh_gui)

        with patch("docfit_live.service.save_clipboard") as mock_save_clip:
            res_tu = fresh_bridge.live_link("table_unit", {"delta": 1, "expected": {"pos": [0, 0, 0]}})
            res_ss = fresh_bridge.live_link("selection_spacing", {"expected": {"pos": [0, 0, 0]}})

        self.assertFalse(res_tu["ok"])
        self.assertEqual(res_tu["code"], "FEATURE_DISABLED")
        self.assertFalse(res_ss["ok"])
        self.assertEqual(res_ss["code"], "FEATURE_DISABLED")
        self.assertIsNone(getattr(fresh_bridge, "_live", None))
        mock_save_clip.assert_not_called()

    def test_alpha3_service_enabled_flag_gate(self):
        user = session(r"C:\a\보고서.hwpx", in_table=True, document_id="doc-1")
        svc = LiveLinkService(sessions=lambda: [user], titles=lambda: [], com_init=False, gate_checker=lambda: True)
        ctx = link.context(user.app)

        # enabled=False(기본값)일 때 FEATURE_DISABLED 즉시 반환 및 COM 접근 없음
        res_disabled_tu = svc.resize_cursor_table(1, expected=ctx)
        self.assertFalse(res_disabled_tu["ok"])
        self.assertEqual(res_disabled_tu["code"], "FEATURE_DISABLED")

        res_disabled_ss = svc.normalize_selection_spacing(expected=ctx)
        self.assertFalse(res_disabled_ss["ok"])
        self.assertEqual(res_disabled_ss["code"], "FEATURE_DISABLED")
        self.assertEqual(user.app.runs, [])

        # enabled=True일 때 내부 진입
        user.app.ParentCtrl = None
        user.app.SelectionMode = 0
        ctx_out = link.context(user.app)
        # 표 밖 -> expected 검증에서 in_table=False면 INVALID_ARGUMENT
        res_invalid_tu = svc.resize_cursor_table(1, expected=ctx_out, enabled=True)
        self.assertFalse(res_invalid_tu["ok"])
        self.assertEqual(res_invalid_tu["code"], "INVALID_ARGUMENT")

        res_invalid_ss = svc.normalize_selection_spacing(expected=ctx_out, enabled=True)
        self.assertFalse(res_invalid_ss["ok"])
        self.assertEqual(res_invalid_ss["code"], "INVALID_ARGUMENT")

    def test_table_expected_contract_rejects_missing_fields(self):
        user = session(r"C:\a\보고서.hwpx", in_table=True, document_id="doc-1")
        mock_pick = Mock(return_value=user)
        svc = LiveLinkService(sessions=lambda: [user], titles=lambda: [], com_init=False, gate_checker=lambda: True)
        svc._pick = mock_pick

        valid = {
            "path": r"C:\a\보고서.hwpx",
            "document_id": "doc-1",
            "pos": [0, 1, 2],
            "selected": False,
            "in_table": True,
        }

        with patch("docfit_live.link.export_table_block") as mock_export, \
             patch("docfit_live.link.replace_table_block") as mock_replace:
            # None, 빈 dict
            self.assertEqual(svc.resize_cursor_table(1, expected=None, enabled=True)["code"], "INVALID_ARGUMENT")
            self.assertEqual(svc.resize_cursor_table(1, expected={}, enabled=True)["code"], "INVALID_ARGUMENT")

            # 필수 키 누락
            for key in ("path", "document_id", "pos", "selected", "in_table"):
                bad = dict(valid)
                del bad[key]
                res = svc.resize_cursor_table(1, expected=bad, enabled=True)
                self.assertEqual(res["code"], "INVALID_ARGUMENT")

            # 잘못된 타입
            self.assertEqual(svc.resize_cursor_table(1, expected={**valid, "path": ""}, enabled=True)["code"], "INVALID_ARGUMENT")
            self.assertEqual(svc.resize_cursor_table(1, expected={**valid, "document_id": " "}, enabled=True)["code"], "INVALID_ARGUMENT")
            self.assertEqual(svc.resize_cursor_table(1, expected={**valid, "pos": [0, 1]}, enabled=True)["code"], "INVALID_ARGUMENT")
            self.assertEqual(svc.resize_cursor_table(1, expected={**valid, "selected": True}, enabled=True)["code"], "INVALID_ARGUMENT")
            self.assertEqual(svc.resize_cursor_table(1, expected={**valid, "in_table": False}, enabled=True)["code"], "INVALID_ARGUMENT")

            # pick, export, replace 모두 0회 호출
            mock_pick.assert_not_called()
            mock_export.assert_not_called()
            mock_replace.assert_not_called()

    def test_selection_expected_contract_rejects_missing_fields(self):
        user = session(r"C:\a\보고서.hwpx", in_table=False, document_id="doc-1")
        user.app.SelectionMode = 1
        mock_pick = Mock(return_value=user)
        svc = LiveLinkService(sessions=lambda: [user], titles=lambda: [], com_init=False, gate_checker=lambda: True)
        svc._pick = mock_pick

        valid = {
            "path": r"C:\a\보고서.hwpx",
            "document_id": "doc-1",
            "pos": [0, 1, 2],
            "selected": True,
            "in_table": False,
            "selection_range": [[0, 1, 2], [0, 1, 10]],
        }

        with patch("docfit_live.link.export_selection_block") as mock_export, \
             patch("docfit_live.link.replace_selection_block") as mock_replace:
            self.assertEqual(svc.normalize_selection_spacing(expected=None, enabled=True)["code"], "INVALID_ARGUMENT")
            self.assertEqual(svc.normalize_selection_spacing(expected={}, enabled=True)["code"], "INVALID_ARGUMENT")

            for key in ("path", "document_id", "pos", "selected", "in_table", "selection_range"):
                bad = dict(valid)
                del bad[key]
                self.assertEqual(svc.normalize_selection_spacing(expected=bad, enabled=True)["code"], "INVALID_ARGUMENT")

            # selected=False는 거부
            self.assertEqual(svc.normalize_selection_spacing(expected={**valid, "selected": False}, enabled=True)["code"], "INVALID_ARGUMENT")
            # 잘못된 selection_range 거부
            self.assertEqual(svc.normalize_selection_spacing(expected={**valid, "selection_range": [1, 2]}, enabled=True)["code"], "INVALID_ARGUMENT")

            mock_pick.assert_not_called()
            mock_export.assert_not_called()
            mock_replace.assert_not_called()

    def test_closed_undo_gate_prevents_export_and_replace(self):
        user = session(r"C:\a\보고서.hwpx", in_table=True, document_id="doc-1")
        # 게이트가 닫힌 서비스
        svc = LiveLinkService(sessions=lambda: [user], titles=lambda: [], com_init=False, gate_checker=lambda: False)
        valid = {
            "path": r"C:\a\보고서.hwpx",
            "document_id": "doc-1",
            "pos": [0, 1, 2],
            "selected": False,
            "in_table": True,
        }

        with patch("docfit_live.link.export_table_block") as mock_export, \
             patch("docfit_live.link.replace_table_block") as mock_replace:
            res = svc.resize_cursor_table(1, expected=valid, enabled=True)
            self.assertFalse(res["ok"])
            self.assertEqual(res["code"], "UNDO_GATE_CLOSED")
            mock_export.assert_not_called()
            mock_replace.assert_not_called()

    def test_gate_pass_does_not_claim_unsupported_wire_format(self):
        user = session(r"C:\a\보고서.hwpx", in_table=True, document_id="doc-1")
        svc = LiveLinkService(sessions=lambda: [user], titles=lambda: [], com_init=False, gate_checker=lambda: True)
        ctx = link.context(user.app)

        with patch("docfit_live.link.replace_table_block") as mock_replace:
            res = svc.resize_cursor_table(1, expected=ctx, enabled=True)
            self.assertFalse(res["ok"])
            self.assertEqual(res["code"], "UNSUPPORTED_FORMAT")
            mock_replace.assert_not_called()

    def test_table_context_rechecked_before_replace_for_path_document_and_position(self):
        user = session(r"C:\a\보고서.hwpx", in_table=True, document_id="doc-1")
        svc = LiveLinkService(sessions=lambda: [user], titles=lambda: [], com_init=False, gate_checker=lambda: True)
        ctx = link.context(user.app)

        # 시작 문맥 일치 후 교체 직전 시점(link.context 2번째 호출)에서 각 필드 하나씩 변경 시 STALE_CONTEXT
        fields_to_change = [
            ("path", r"C:\b\다른문서.hwpx"),
            ("document_id", "doc-different"),
            ("pos", [99, 99, 99]),
            ("selected", True),
            ("in_table", False),
        ]

        for field_name, new_val in fields_to_change:
            ctx_start = dict(ctx)
            ctx_stale = {**ctx, field_name: new_val}

            with patch("docfit_live.link.context", side_effect=[ctx_start, ctx_stale]), \
                 patch("docfit_live.link.export_table_block", return_value=b"<tbl/>"), \
                 patch.object(LiveLinkService, "_transform_table_block", return_value=b"<new_tbl/>"), \
                 patch("docfit_live.link.replace_table_block") as mock_replace:
                res = svc.resize_cursor_table(1, expected=ctx, enabled=True)
                self.assertFalse(res["ok"], f"Failed for field {field_name}")
                self.assertEqual(res["code"], "STALE_CONTEXT", f"Failed code for field {field_name}")
                mock_replace.assert_not_called()

    def test_selection_context_rechecked_before_replace_for_path_document_and_selection(self):
        user = session(r"C:\a\보고서.hwpx", in_table=False, document_id="doc-1")
        user.app.SelectionMode = 1
        user.app.selection_range = [[0, 1, 2], [0, 1, 10]]
        svc = LiveLinkService(sessions=lambda: [user], titles=lambda: [], com_init=False, gate_checker=lambda: True)
        ctx = link.context(user.app)

        fields_to_change = [
            ("path", r"C:\b\다른문서.hwpx"),
            ("document_id", "doc-different"),
            ("pos", [99, 99, 99]),
            ("selected", False),
            ("selection_range", [[0, 1, 2], [0, 1, 99]]),  # 시작 위치 pos는 같으나 끝점만 변경 (지적 2 Fake 회귀 시험)
        ]

        for field_name, new_val in fields_to_change:
            ctx_start = dict(ctx)
            ctx_stale = {**ctx, field_name: new_val}

            with patch("docfit_live.link.context", side_effect=[ctx_start, ctx_stale]), \
                 patch("docfit_live.link.export_selection_block", return_value=b"<sel/>"), \
                 patch.object(LiveLinkService, "_transform_selection_block", return_value=b"<new_sel/>"), \
                 patch("docfit_live.link.replace_selection_block") as mock_replace:
                res = svc.normalize_selection_spacing(expected=ctx, enabled=True)
                self.assertFalse(res["ok"], f"Failed for field {field_name}")
                self.assertEqual(res["code"], "STALE_CONTEXT", f"Failed code for field {field_name}")
                mock_replace.assert_not_called()

    def test_alpha3_settings_lookup_failure_safely_defaults_off(self):
        from desktop_web_ui import DesktopWebBridge
        faulty_store = Mock()
        faulty_store.read.side_effect = RuntimeError("디스크 I/O 오류 또는 잠금")
        faulty_gui = Mock(files=[], running=False, settings=faulty_store)
        bridge = DesktopWebBridge(faulty_gui)

        with self.assertLogs("desktop_web_ui", level="WARNING") as logs:
            res = bridge.live_link("table_unit", {"delta": 1, "expected": {}})

        self.assertFalse(res["ok"])
        self.assertEqual(res["code"], "FEATURE_DISABLED")
        self.assertIsNone(getattr(bridge, "_live", None))
        self.assertTrue(any("live_alpha3_enabled 설정 조회 실패" in log for log in logs.output))


if __name__ == "__main__":
    unittest.main()
