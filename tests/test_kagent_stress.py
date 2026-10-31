"""K에이전트 누수 스트레스 측정 스크립트 단위 시험.

임의 샘플 기반 판정 로직, 기준 표본(quick: 0초 초기 표본 vs 일반: 60초 시점 표본) 선택,
임계값(Private 1MB, Handles/GDI 20), 자원 API 오류 검출, 필수 스트레스 수행 횟수 요건,
환경변수 및 클립보드 복원, 임시 폴더 정리, 클립보드 본문 미포함, 단일 인스턴스 격리 보호, 원 설정 복원을 검증합니다.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.kagent_stress_pc import evaluate_samples, parse_args, run


class TestKAgentStressEvaluation(unittest.TestCase):
    def test_parse_args(self):
        args = parse_args(["kagent.exe"])
        self.assertEqual(str(args.exe), "kagent.exe")
        self.assertEqual(args.minutes, 10)
        self.assertFalse(args.quick)

        args_quick = parse_args(["kagent.exe", "--quick"])
        self.assertTrue(args_quick.quick)

        args_custom = parse_args(["kagent.exe", "--minutes", "5"])
        self.assertEqual(args_custom.minutes, 5)

    def test_quick_baseline_after_warmup_and_end(self):
        # quick 모드(1분): 30초 준비 구간 뒤 표본(baseline)과 60초 종료 표본(end) 비교
        samples = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 8, "valid": True},
            {"elapsed_sec": 30.0, "private": 1050, "handles": 11, "gdi": 5, "user": 8, "valid": True},
            {"elapsed_sec": 60.0, "private": 1100, "handles": 12, "gdi": 6, "user": 9, "valid": True},
        ]
        stress_counts = {
            "clip_success": 60,
            "popup_success": 1,
            "settings_success": 1,
            "timeline_success": 1,
        }
        res = evaluate_samples(samples, quick=True, minutes=1, stress_counts=stress_counts)
        self.assertTrue(res["passed"], f"FAIL reasons: {res.get('failures')}")
        self.assertEqual(res["baseline"]["elapsed_sec"], 30.0)
        self.assertEqual(res["end"]["elapsed_sec"], 60.0)
        self.assertEqual(res.get("quick_baseline"), "after_warmup_30s")
        self.assertEqual(res["diff"]["private"], 50)  # 1100 - 1050
        self.assertEqual(res["diff"]["handles"], 1)   # 12 - 11
        self.assertEqual(res["diff"]["gdi"], 1)       # 6 - 5
        self.assertEqual(res["diff"]["user"], 1)      # 9 - 8
        self.assertIn("sample_intervals", res)

    def test_quick_samples_shortage_fails(self):
        # quick 모드에서 표본이 1개뿐이거나 종료 시점이 45초 미만인 경우 FAIL
        samples = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 8, "valid": True},
        ]
        res = evaluate_samples(samples, quick=True, minutes=1)
        self.assertFalse(res["passed"])
        self.assertTrue(any("quick 모드 최소 표본 부족" in f for f in res["failures"]))

        samples_short_time = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 8, "valid": True},
            {"elapsed_sec": 20.0, "private": 1050, "handles": 11, "gdi": 5, "user": 8, "valid": True},
        ]
        res2 = evaluate_samples(samples_short_time, quick=True, minutes=1)
        self.assertFalse(res2["passed"])
        self.assertTrue(any("측정 지속 시간 미달" in f for f in res2["failures"]))

    def test_standard_baseline_selection_at_60s(self):
        # 일반 모드(기본 10분): 60초 시점 기준 표본(baseline)과 종료 표본(end) 비교
        samples = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 8, "valid": True},
            {"elapsed_sec": 30.0, "private": 1200, "handles": 12, "gdi": 6, "user": 9, "valid": True},
            {"elapsed_sec": 60.0, "private": 1500, "handles": 15, "gdi": 8, "user": 10, "valid": True},
            {"elapsed_sec": 90.0, "private": 1550, "handles": 16, "gdi": 8, "user": 10, "valid": True},
            {"elapsed_sec": 120.0, "private": 1560, "handles": 16, "gdi": 8, "user": 10, "valid": True},
        ]
        stress_counts = {
            "clip_success": 600,
            "popup_success": 12,
            "settings_success": 6,
            "timeline_success": 6,
        }
        res = evaluate_samples(samples, quick=False, minutes=10, stress_counts=stress_counts)
        self.assertTrue(res["passed"])
        self.assertEqual(res["baseline"]["elapsed_sec"], 60.0)
        self.assertEqual(res["end"]["elapsed_sec"], 120.0)
        self.assertEqual(res["diff"]["private"], 60)
        self.assertEqual(res["diff"]["handles"], 1)
        self.assertEqual(res["diff"]["gdi"], 0)
        self.assertEqual(res["diff"]["user"], 0)

    def test_standard_baseline_missing_fails(self):
        # 일반 모드에서 60초 미만 표본만 있는 경우 -> 기준 표본 부재 FAIL
        samples = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 8, "valid": True},
            {"elapsed_sec": 30.0, "private": 1100, "handles": 11, "gdi": 5, "user": 8, "valid": True},
        ]
        res = evaluate_samples(samples, quick=False, minutes=10)
        self.assertFalse(res["passed"])
        self.assertTrue(any("60초 시점 기준 표본 부재" in f for f in res["failures"]))

    def test_standard_samples_after_baseline_missing_fails(self):
        # 일반 모드에서 60초 표본만 있고 그 이후 종료 표본이 없는 경우 -> 종료 표본 부재 FAIL
        samples = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 8, "valid": True},
            {"elapsed_sec": 30.0, "private": 1100, "handles": 11, "gdi": 5, "user": 8, "valid": True},
            {"elapsed_sec": 60.0, "private": 1200, "handles": 12, "gdi": 6, "user": 9, "valid": True},
        ]
        res = evaluate_samples(samples, quick=False, minutes=10)
        self.assertFalse(res["passed"])
        self.assertTrue(any("60초 이후 유효 종료 표본 부재" in f for f in res["failures"]))

    def test_threshold_private_1mb(self):
        valid_stress = {"clip_success": 60, "popup_success": 1, "settings_success": 1, "timeline_success": 1}

        # 1MB - 1 byte -> PASS
        samples_pass = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": True},
            {"elapsed_sec": 30.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": True},
            {"elapsed_sec": 60.0, "private": 1000 + (1024 * 1024 - 1), "handles": 10, "gdi": 5, "user": 5, "valid": True},
        ]
        res_pass = evaluate_samples(samples_pass, quick=True, minutes=1, stress_counts=valid_stress)
        self.assertTrue(res_pass["passed"])

        # 1MB exactly -> FAIL
        samples_fail = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": True},
            {"elapsed_sec": 30.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": True},
            {"elapsed_sec": 60.0, "private": 1000 + (1024 * 1024), "handles": 10, "gdi": 5, "user": 5, "valid": True},
        ]
        res_fail = evaluate_samples(samples_fail, quick=True, minutes=1, stress_counts=valid_stress)
        self.assertFalse(res_fail["passed"])
        self.assertTrue(any("PrivateUsage" in f for f in res_fail["failures"]))

    def test_threshold_handles_and_gdi(self):
        valid_stress = {"clip_success": 60, "popup_success": 1, "settings_success": 1, "timeline_success": 1}

        # handles +19, gdi +19 -> PASS
        samples_pass = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 10, "user": 5, "valid": True},
            {"elapsed_sec": 30.0, "private": 1000, "handles": 10, "gdi": 10, "user": 5, "valid": True},
            {"elapsed_sec": 60.0, "private": 1000, "handles": 29, "gdi": 29, "user": 5, "valid": True},
        ]
        res_pass = evaluate_samples(samples_pass, quick=True, minutes=1, stress_counts=valid_stress)
        self.assertTrue(res_pass["passed"])

        # handles +20 -> FAIL
        samples_fail_h = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 10, "user": 5, "valid": True},
            {"elapsed_sec": 30.0, "private": 1000, "handles": 10, "gdi": 10, "user": 5, "valid": True},
            {"elapsed_sec": 60.0, "private": 1000, "handles": 30, "gdi": 29, "user": 5, "valid": True},
        ]
        res_fail_h = evaluate_samples(samples_fail_h, quick=True, minutes=1, stress_counts=valid_stress)
        self.assertFalse(res_fail_h["passed"])
        self.assertTrue(any("HandleCount" in f for f in res_fail_h["failures"]))

        # gdi +20 -> FAIL
        samples_fail_g = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 10, "user": 5, "valid": True},
            {"elapsed_sec": 30.0, "private": 1000, "handles": 10, "gdi": 10, "user": 5, "valid": True},
            {"elapsed_sec": 60.0, "private": 1000, "handles": 29, "gdi": 30, "user": 5, "valid": True},
        ]
        res_fail_g = evaluate_samples(samples_fail_g, quick=True, minutes=1, stress_counts=valid_stress)
        self.assertFalse(res_fail_g["passed"])
        self.assertTrue(any("GdiObjects" in f for f in res_fail_g["failures"]))

    def test_api_failure_in_snapshot_fails(self):
        # 자원 수집 API 실패가 포함된 표본 -> FAIL
        samples = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": True},
            {"elapsed_sec": 30.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": False, "error": "GetProcessMemoryInfo failed"},
            {"elapsed_sec": 60.0, "private": 1100, "handles": 11, "gdi": 5, "user": 5, "valid": True},
        ]
        res = evaluate_samples(samples, quick=True, minutes=1)
        self.assertFalse(res["passed"])
        self.assertTrue(any("자원 측정 API 호출 실패" in f for f in res["failures"]))

    def test_gui_resources_failure_in_snapshot_fails(self):
        # GetGuiResources 실패 표본 -> FAIL
        samples = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": True},
            {"elapsed_sec": 30.0, "private": 1000, "handles": 10, "gdi": 0, "user": 0, "valid": False, "error": "GetGuiResources(GDI) failed (error=5)"},
            {"elapsed_sec": 60.0, "private": 1100, "handles": 11, "gdi": 5, "user": 5, "valid": True},
        ]
        res = evaluate_samples(samples, quick=True, minutes=1)
        self.assertFalse(res["passed"])
        self.assertTrue(any("GetGuiResources(GDI) failed" in f for f in res["failures"]))

    def test_sample_intervals_deviation_fails(self):
        # 표본 간격 편차가 허용(15~45초)을 크게 벗어난 경우 -> FAIL
        samples = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": True},
            {"elapsed_sec": 50.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": True},  # 50초 간격 (>45s)
            {"elapsed_sec": 60.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": True},
        ]
        res = evaluate_samples(samples, quick=True, minutes=1)
        self.assertFalse(res["passed"])
        self.assertTrue(any("표본 수집 주기 편차 초과" in f for f in res["failures"]))

    def test_stress_count_shortage_fails(self):
        samples = [
            {"elapsed_sec": 0.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": True},
            {"elapsed_sec": 30.0, "private": 1000, "handles": 10, "gdi": 5, "user": 5, "valid": True},
            {"elapsed_sec": 60.0, "private": 1100, "handles": 11, "gdi": 5, "user": 5, "valid": True},
        ]
        short_stress = {"clip_success": 10, "popup_success": 0, "settings_success": 0, "timeline_success": 0}
        res = evaluate_samples(samples, quick=True, minutes=1, stress_counts=short_stress)
        self.assertFalse(res["passed"])
        self.assertTrue(any("클립보드 복사 부하 횟수 미달" in f for f in res["failures"]))


class TestKAgentStressRunLifecycle(unittest.TestCase):
    @patch("scripts.kagent_stress_pc.check_existing_instance", return_value=False)
    @patch("scripts.kagent_stress_pc.subprocess.Popen")
    @patch("scripts.kagent_stress_pc.KAgentClient")
    @patch("scripts.kagent_stress_pc.snapshot")
    @patch("scripts.kagent_stress_pc.get_text")
    @patch("scripts.kagent_stress_pc.set_text")
    @patch("scripts.kagent_stress_pc.time.sleep")
    def test_run_cleanup_and_restore(
        self,
        mock_sleep,
        mock_set_text,
        mock_get_text,
        mock_snap,
        mock_client_cls,
        mock_popen,
        mock_check_instance,
    ):
        mock_get_text.return_value = "ORIGINAL_SECRET_CLIPBOARD_TEXT"
        mock_snap.return_value = {
            "working_set": 1000,
            "private": 1000,
            "handles": 10,
            "gdi": 5,
            "user": 5,
            "valid": True,
            "error": None,
        }

        mock_proc = MagicMock()
        mock_proc.pid = 9999
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        mock_client = MagicMock()
        mock_client.status_file.return_value = {"version": "0.1.0"}
        # settings_get 및 settings_set 형식 준수 모의
        stored_roots: list[str] = ["C:\\original_root"]
        settings_set_called_with = []

        def mock_req(req, **kw):
            if req == "settings_get":
                return {"ok": True, "settings": {"timeline_roots": list(stored_roots)}}
            elif req == "settings_set":
                settings = kw.get("settings", {})
                stored_roots.clear()
                stored_roots.extend(settings.get("timeline_roots", []))
                settings_set_called_with.append(dict(settings))
                return {"ok": True}
            return {}

        mock_client.request.side_effect = mock_req
        mock_client_cls.return_value = mock_client

        orig_env_data = os.environ.get("KAGENT_DATA")
        orig_env_shots = os.environ.get("KAGENT_SCREENSHOTS")

        # 시간 흐름 모의 (루프가 빠르게 60초를 지나도록 설정)
        curr_time = [0.0]

        def fake_perf_counter():
            curr_time[0] += 30.0
            return curr_time[0]

        with patch("scripts.kagent_stress_pc.time.perf_counter", side_effect=fake_perf_counter):
            result = run(Path("fake_kagent.exe"), minutes=1, quick=True)

        # 1. 원래 클립보드 복원 확인
        mock_set_text.assert_called_with("ORIGINAL_SECRET_CLIPBOARD_TEXT")

        # 2. 환경변수 복원 확인
        self.assertEqual(os.environ.get("KAGENT_DATA"), orig_env_data)
        self.assertEqual(os.environ.get("KAGENT_SCREENSHOTS"), orig_env_shots)

        # 3. 종료 전 원 설정(timeline_roots) 복원 호출 확인
        self.assertTrue(len(settings_set_called_with) >= 2)
        final_settings_set = settings_set_called_with[-1]
        self.assertEqual(final_settings_set.get("timeline_roots"), ["C:\\original_root"])

        # 4. 결과 리포트에 클립보드 원본 텍스트 내용이 포함되지 않음을 확인 (보안 검증)
        report_str = str(result)
        self.assertNotIn("ORIGINAL_SECRET_CLIPBOARD_TEXT", report_str)

    @patch("scripts.kagent_stress_pc.check_existing_instance", return_value=True)
    @patch("scripts.kagent_stress_pc.subprocess.Popen")
    @patch("scripts.kagent_stress_pc.KAgentClient")
    def test_run_aborts_when_existing_instance_running(self, mock_client_cls, mock_popen, mock_check_instance):
        # 기존 인스턴스 발견 시 예외를 던지고 프로세스 및 IPC를 시작하지 않아야 함
        with self.assertRaises(RuntimeError) as cm:
            run(Path("fake_kagent.exe"), minutes=1, quick=True)

        self.assertIn("기존 kagent 인스턴스가 실행 중입니다", str(cm.exception))
        mock_popen.assert_not_called()
        mock_client_cls.assert_not_called()

    @patch("scripts.kagent_stress_pc.check_existing_instance", return_value=False)
    @patch("scripts.kagent_stress_pc.subprocess.Popen")
    @patch("scripts.kagent_stress_pc.KAgentClient")
    @patch("scripts.kagent_stress_pc.get_text")
    @patch("scripts.kagent_stress_pc.set_text")
    def test_run_exception_cleanup_and_restore(
        self,
        mock_set_text,
        mock_get_text,
        mock_client_cls,
        mock_popen,
        mock_check_instance,
    ):
        # 실행 도중 시작 실패 예외 발생 시 정리 검증
        mock_get_text.return_value = "ORIGINAL_TEXT_ON_EXCEPTION"
        mock_proc = MagicMock()
        mock_proc.pid = 8888
        mock_popen.return_value = mock_proc

        mock_client = MagicMock()
        mock_client.status_file.return_value = None  # 시작 실패 유발
        mock_client_cls.return_value = mock_client

        orig_env_data = os.environ.get("KAGENT_DATA")
        orig_env_shots = os.environ.get("KAGENT_SCREENSHOTS")

        with self.assertRaises(RuntimeError):
            run(Path("fake_kagent.exe"), minutes=1, quick=True)

        mock_set_text.assert_called_with("ORIGINAL_TEXT_ON_EXCEPTION")
        self.assertEqual(os.environ.get("KAGENT_DATA"), orig_env_data)
        self.assertEqual(os.environ.get("KAGENT_SCREENSHOTS"), orig_env_shots)


if __name__ == "__main__":
    unittest.main()
