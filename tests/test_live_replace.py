"""3.0-α3 표 정보단위 교체 및 선택 자간 변환 계약 시험 (Fake COM 환경)."""
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from docfit_live import link
from docfit_live.service import LiveLinkService, is_undo_gate_passed
from tests.test_live_link import FakeApp


def session(path, visible=True, in_table=False, selected=False):
    app = FakeApp(path, in_table=in_table)
    app.SelectionMode = 1 if selected else 0
    app.XHwpWindows = SimpleNamespace(Active_XHwpWindow=SimpleNamespace(Visible=visible))
    return link.Session("m:" + path, app, path, path.rsplit("\\", 1)[-1])


class LiveReplaceContractTest(unittest.TestCase):
    def test_replace_contract_reports_required_measurements(self):
        user = session(r"C:\a\보고서.hwpx", in_table=True)
        # 게이트가 통과된 가짜 환경이어도 wire format 미실측 시 UNSUPPORTED_FORMAT 보고
        svc = LiveLinkService(
            sessions=lambda: [user],
            titles=lambda: [],
            com_init=False,
            gate_checker=lambda: True,
        )
        ctx = link.context(user.app)

        # 미측정 HWPML export/import 매개변수, 인코딩, 경계, 단일 Undo 확인 항목이 오류/보고 데이터에 빠짐없이 포함됨
        res = svc.resize_cursor_table(1, expected=ctx, enabled=True)
        self.assertFalse(res["ok"])
        self.assertEqual(res["code"], "UNSUPPORTED_FORMAT")
        self.assertEqual(user.app.runs, [])

        measurements = res.get("required_measurements", [])
        self.assertTrue(isinstance(measurements, list))
        joined = " ".join(measurements)
        self.assertIn("HWPML", joined)
        self.assertIn("GetTextFile", joined)
        self.assertIn("SetTextFile", joined)
        self.assertIn("인코딩", joined)
        self.assertIn("경계", joined)
        self.assertIn("Ctrl+Z", joined)

    def test_spacing_contract_is_not_a_successful_noop(self):
        user = session(r"C:\a\보고서.hwpx", selected=True)
        # 게이트가 통과된 가짜 환경이어도 wire format 미실측 시 UNSUPPORTED_FORMAT 보고
        svc = LiveLinkService(
            sessions=lambda: [user],
            titles=lambda: [],
            com_init=False,
            gate_checker=lambda: True,
        )
        ctx = link.context(user.app)

        # 선택 자간 미연결을 성공 no-op으로 표현하지 않고 명시적 미지원(UNSUPPORTED_FORMAT)으로 보고, 쓰기 0회
        res = svc.normalize_selection_spacing(expected=ctx, enabled=True)
        self.assertFalse(res["ok"])
        self.assertNotEqual(res.get("code"), "OK")
        self.assertEqual(res["code"], "UNSUPPORTED_FORMAT")
        self.assertIn("실측", res["message"])
        self.assertTrue(len(res["required_measurements"]) > 0)
        self.assertEqual(user.app.runs, [])

    def test_closed_gate_has_zero_fake_replace_calls(self):
        user_table = session(r"C:\a\보고서.hwpx", in_table=True)
        user_sel = session(r"C:\a\보고서.hwpx", selected=True)

        # 기본 게이트(증거 없음) 상태에서 서비스 호출
        svc_table = LiveLinkService(
            sessions=lambda: [user_table],
            titles=lambda: [],
            com_init=False,
            gate_checker=lambda: False,
        )
        svc_sel = LiveLinkService(
            sessions=lambda: [user_sel],
            titles=lambda: [],
            com_init=False,
            gate_checker=lambda: False,
        )

        ctx_table = link.context(user_table.app)
        ctx_sel = link.context(user_sel.app)

        res_table = svc_table.resize_cursor_table(1, expected=ctx_table, enabled=True)
        self.assertFalse(res_table["ok"])
        self.assertEqual(res_table["code"], "UNDO_GATE_CLOSED")
        self.assertEqual(user_table.app.runs, [])

        res_sel = svc_sel.normalize_selection_spacing(expected=ctx_sel, enabled=True)
        self.assertFalse(res_sel["ok"])
        self.assertEqual(res_sel["code"], "UNDO_GATE_CLOSED")
        self.assertEqual(user_sel.app.runs, [])

    def test_gate_evidence_is_required_for_fake_replace_path(self):
        # 허위/불완전 증거 파일이 있을 때 게이트가 닫히고 교체 호출이 0회임을 확인
        with tempfile.TemporaryDirectory() as td:
            bad_gate_file = os.path.join(td, "bad-gate.json")
            with open(bad_gate_file, "w", encoding="utf-8") as f:
                json.dump({
                    "schema_version": 1,
                    "gate": "live_replace",
                    "status": "FAIL",
                    "undo_steps": 1,
                    "evidence_files": ["fake.txt"]
                }, f)

            self.assertFalse(is_undo_gate_passed(bad_gate_file))

            user = session(r"C:\a\보고서.hwpx", in_table=True)
            svc = LiveLinkService(
                sessions=lambda: [user],
                titles=lambda: [],
                com_init=False,
                gate_checker=lambda: is_undo_gate_passed(bad_gate_file),
            )
            ctx = link.context(user.app)

            res = svc.resize_cursor_table(1, expected=ctx, enabled=True)
            self.assertFalse(res["ok"])
            self.assertEqual(res["code"], "UNDO_GATE_CLOSED")
            self.assertEqual(user.app.runs, [])

            # 가짜 승인 주입 시에도 와이어 포맷 미실측으로 쓰기 호출 0회
            svc_pass = LiveLinkService(
                sessions=lambda: [user],
                titles=lambda: [],
                com_init=False,
                gate_checker=lambda: True,
            )
            res_pass = svc_pass.resize_cursor_table(1, expected=ctx, enabled=True)
            self.assertFalse(res_pass["ok"])
            self.assertEqual(res_pass["code"], "UNSUPPORTED_FORMAT")
            self.assertEqual(user.app.runs, [])


if __name__ == "__main__":
    unittest.main()
