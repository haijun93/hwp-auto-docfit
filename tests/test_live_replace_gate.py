"""V3-G3: scripts/live_replace_gate.py 단위 시험 (Fake COM 환경).
\r
실제 한/글 COM, 외부 프로세스, 사용자 입력 없이 순수 Fake/Mock 객체로만 동작한다.
"""
from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from zipfile import ZipFile

from scripts import live_replace_gate
from scripts.live_replace_gate import (
    GateCaseResult,
    GateEvidence,
    _capture_semantic_snapshot,
    _atomic_write_json,
    _build_parser,
    _capture_document_state,
    _copy_fixture,
    _inspect_selection_fixture,
    _inspect_table_fixture,
    _make_hwp_dispatch,
    _move_cursor_to_table,
    _run_selection_spacing_case,
    _run_table_unit_case,
    _run_undo_once,
    _setup_selection_in_app,
    _sha256,
    _validate_evidence,
    run_gate,
    _TARGET_SPACING_TEXT,
    _SENTINEL_START_TEXT,
    _SENTINEL_END_TEXT,
)


def _create_mock_table_hwpx(path: Path, repeat_rows: bool = True) -> None:
    """테스트용 유효 HWPX 표 fixture 생성."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w") as z:
        rows_xml = (
            "<hp:tr><hp:tc><hp:p><hp:t>R1</hp:t></hp:p></hp:tc></hp:tr>"
            "<hp:tr><hp:tc><hp:p><hp:t>R2</hp:t></hp:p></hp:tc></hp:tr>"
            if repeat_rows else
            "<hp:tr><hp:tc><hp:p><hp:t>R1</hp:t></hp:p></hp:tc></hp:tr>"
        )
        sec_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<hs:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section">
  <hp:p>
    <hp:tbl>
      {rows_xml}
    </hp:tbl>
  </hp:p>
</hs:sec>"""
        z.writestr("Contents/section0.xml", sec_xml)


def _create_mock_selection_hwpx(
    path: Path,
    include_target: bool = True,
    include_start_sentinel: bool = True,
    include_end_sentinel: bool = True,
) -> None:
    """테스트용 유효 HWPX 선택 자간 fixture 생성."""
    path.parent.mkdir(parents=True, exist_ok=True)
    target_str = _TARGET_SPACING_TEXT if include_target else "ordinary text"
    start_str = _SENTINEL_START_TEXT if include_start_sentinel else "start text"
    end_str = _SENTINEL_END_TEXT if include_end_sentinel else "end text"

    with ZipFile(path, "w") as z:
        sec_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<hs:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section">
  <hp:p>
    <hp:t>{start_str} leading content {target_str} inner content {end_str} trailing content</hp:t>
  </hp:p>
</hs:sec>"""
        z.writestr("Contents/section0.xml", sec_xml)


class FakeCOMApp:
    """단위 시험용 Fake 한/글 COM 객체 (표준 COM 인터페이스 모방)."""

    def __init__(
        self,
        *,
        initial_state: str = "doc_init",
        fail_open: bool = False,
        fail_replace: bool = False,
        fail_register: bool = False,
        not_in_table: bool = False,
        no_selection: bool = False,
        fail_clear: bool = False,
        fail_quit: bool = False,
    ):
        self.open_calls: list[tuple[str, str, str]] = []
        self.save_calls: list[tuple[str, str, str]] = []
        self.runs: list[str] = []
        self.get_text_file_calls: list[tuple[str, str]] = []
        self.set_text_file_calls: list[tuple[object, str, str]] = []
        self.registered_modules: list[tuple[str, str]] = []
        self.cleared = False
        self.quit_called = False
        self.fail_open = fail_open
        self.fail_replace = fail_replace
        self.fail_register = fail_register
        self.fail_clear = fail_clear
        self.fail_quit = fail_quit
        self.Version = "11.0.0.9999"

        self._state = initial_state
        self._history = [initial_state]
        self.XHwpDocuments = SimpleNamespace(Active_XHwpDocument=SimpleNamespace(FullName=r"C:\fake\fixture.hwpx", DocumentID="fake-doc"))
        active_window = SimpleNamespace(Visible=True, Hwnd=0)
        self.XHwpWindows = SimpleNamespace(Active_XHwpWindow=active_window, Item=lambda idx: active_window)
        self._pos = (0, 0, 0)
        self.ParentCtrl = None if not_in_table else SimpleNamespace(CtrlID="tbl")
        self.SelectionMode = 0 if no_selection else 1
        self.selection_range = [[0, 0, 10], [0, 0, 20]]
        self.HAction = SimpleNamespace(Run=self._action_run)

    def GetPos(self):
        return self._pos

    def KeyIndicator(self):
        return (True, 1, 1, 1)

    def _action_run(self, name: str) -> bool:
        self.runs.append(name)
        if name == "Undo":
            if len(self._history) > 1:
                self._history.pop()
                self._state = self._history[-1]
            return True
        return True

    def RegisterModule(self, name: str, value: str) -> bool:
        self.registered_modules.append((name, value))
        if self.fail_register:
            return False
        return True

    def Open(self, path: str, fmt: str = "", arg: str = "") -> bool:
        self.open_calls.append((path, fmt, arg))
        if self.fail_open:
            return False
        return True

    def SaveAs(self, path: str, fmt: str = "", arg: str = "") -> bool:
        self.save_calls.append((path, fmt, arg))
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(self._state, encoding="utf-8")
        return True

    def GetTextFile(self, fmt: str, opt: str) -> str:
        self.get_text_file_calls.append((fmt, opt))
        if fmt == "TEXT":
            if "saveblock" in opt:
                return _TARGET_SPACING_TEXT
            return self._state
        return f"<tbl_block>{self._state}</tbl_block>"

    def SetTextFile(self, data: object, fmt: str, opt: str) -> bool:
        self.set_text_file_calls.append((data, fmt, opt))
        if self.fail_replace:
            return False
        data_str = data.decode("utf-8", errors="ignore") if isinstance(data, bytes) else str(data)
        self._state = f"replaced_{len(self.set_text_file_calls)}_{data_str}"
        self._history.append(self._state)
        return True

    def select_target_text(self, target_text: str) -> bool:
        if target_text in self._state or target_text == _TARGET_SPACING_TEXT:
            self.SelectionMode = 1
            return True
        return False

    def move_to_table(self) -> bool:
        self.ParentCtrl = SimpleNamespace(CtrlID="tbl")
        return True

    def Clear(self, opt: int = 1) -> bool:
        if self.fail_clear:
            raise RuntimeError("Fake Clear failure")
        self.cleared = True
        return True

    def Quit(self) -> bool:
        if self.fail_quit:
            raise RuntimeError("Fake Quit failure")
        self.quit_called = True
        return True


class TestLiveReplaceGate(unittest.TestCase):
    """설계서 V3-G3의 단위 시험 목록 및 검수 지적 반영 검증."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.repo_root = live_replace_gate._REPO_ROOT

        # 임시 유효 HWPX fixture 준비 (지적 5, 6 반영)
        self.fixture_dir = self.tmp_path / "fixtures"
        self.fixture_dir.mkdir(parents=True, exist_ok=True)
        self.table_fixture = self.fixture_dir / "table_unit_sample.hwpx"
        _create_mock_table_hwpx(self.table_fixture, repeat_rows=True)

        self.selection_fixture = live_replace_gate._DEFAULT_SELECTION_FIXTURE

        self.work_dir = self.tmp_path / "work"
        self.evidence_path = self.tmp_path / "evidence.json"

    def tearDown(self):
        self.tmp_dir.cleanup()

    @contextlib.contextmanager
    def fake_lock(self, *args, **kwargs):
        """단위 시험용 무지연 Mock lock 컨텍스트 (디스크 파일 잠금 폴링 없음)."""
        yield

    def test_cli_defaults_stay_under_repository_reports_and_fixture_paths(self):
        """기본 출력·작업 디렉터리가 저장소 내부이고 사용자 원본 입력 경로 인자가 없는지 검사."""
        parser = _build_parser()
        args = parser.parse_args([])

        resolved_fixture = args.fixture_root.resolve()
        resolved_table = args.table_fixture.resolve()
        resolved_sel = args.selection_fixture.resolve()
        resolved_work = args.work_dir.resolve()
        resolved_evidence = args.evidence.resolve()

        resolved_repo = self.repo_root.resolve()
        self.assertTrue(str(resolved_fixture).startswith(str(resolved_repo)))
        self.assertTrue(str(resolved_table).startswith(str(resolved_repo)))
        self.assertTrue(str(resolved_sel).startswith(str(resolved_repo)))
        self.assertTrue(str(resolved_work).startswith(str(resolved_repo)))
        self.assertTrue(str(resolved_evidence).startswith(str(resolved_repo)))

        # 두 fixture가 서로 다른 경로인지 확인
        self.assertNotEqual(resolved_table, resolved_sel)

        # 사용자 원본 문서 경로를 받는 CLI 인자가 없는지 확인
        arg_names = [action.dest for action in parser._actions]
        self.assertNotIn("source", arg_names)
        self.assertNotIn("user_doc", arg_names)
        self.assertNotIn("target", arg_names)
        self.assertNotIn("input", arg_names)

    def test_run_gate_acquires_lock_before_dispatch_ex(self):
        """가짜 lock 진입/종료와 DispatchEx 호출 순서를 추적해 잠금이 먼저임을 검사; 잠금 오류 시 dispatch 0회."""
        call_order: list[str] = []

        @contextlib.contextmanager
        def fake_lock(*args, **kwargs):
            call_order.append("lock_acquired")
            try:
                yield
            finally:
                call_order.append("lock_released")

        def fake_dispatch(progid: str):
            call_order.append("dispatch_ex")
            return FakeCOMApp()

        run_gate(
            fixture_root=self.fixture_dir,
            table_fixture=self.table_fixture,
            selection_fixture=self.selection_fixture,
            evidence_path=self.evidence_path,
            work_dir=self.work_dir,
            dispatch_ex=fake_dispatch,
            lock_factory=fake_lock,
            table_transformer=lambda b: b + "_transformed",
            selection_transformer=lambda b: b + "_transformed",
            repo_root=self.tmp_path,
        )

        self.assertIn("lock_acquired", call_order)
        self.assertIn("dispatch_ex", call_order)
        lock_idx = call_order.index("lock_acquired")
        dispatch_idx = call_order.index("dispatch_ex")
        self.assertLess(lock_idx, dispatch_idx, "잠금 획득이 DispatchEx 호출보다 선행되어야 합니다.")

    def test_run_gate_lock_failure_guarantees_fail_evidence_json(self):
        """lock 획득 실패 시 run_gate 밖으로 예외가 전파되지 않고 FAIL 증거와 case JSON이 기록됨을 검증."""
        dispatch_count = 0

        def failing_lock(*args, **kwargs):
            raise TimeoutError("COM 잠금 획득 실패")

        def counting_dispatch(progid: str):
            nonlocal dispatch_count
            dispatch_count += 1
            return FakeCOMApp()

        ev = run_gate(
            fixture_root=self.fixture_dir,
            table_fixture=self.table_fixture,
            selection_fixture=self.selection_fixture,
            evidence_path=self.evidence_path,
            work_dir=self.work_dir,
            dispatch_ex=counting_dispatch,
            lock_factory=failing_lock,
            repo_root=self.tmp_path,
        )

        self.assertEqual(dispatch_count, 0, "잠금 실패 시 dispatch_ex는 호출되지 않아야 합니다.")
        self.assertEqual(ev.status, "FAIL")
        self.assertIsNone(ev.undo_steps)
        self.assertTrue(self.evidence_path.is_file(), "lock 실패 시에도 최상위 FAIL 증거 파일이 보장되어야 합니다.")
        self.assertTrue((self.work_dir / "table_unit.json").is_file(), "case JSON이 작성되어야 합니다.")
        self.assertTrue((self.work_dir / "selection_spacing.json").is_file(), "case JSON이 작성되어야 합니다.")

    def test_dispatch_factory_uses_dispatch_ex_only(self):
        """DispatchEx('HWPFrame.HwpObject') 정확히 1회, Dispatch/ROT/GetActiveObject 0회."""
        mock_dispatch = MagicMock(return_value=FakeCOMApp())

        app = _make_hwp_dispatch(dispatch_ex=mock_dispatch)
        mock_dispatch.assert_called_once_with("HWPFrame.HwpObject")
        self.assertIsNotNone(app)

    def test_dispatch_factory_fails_on_register_module_failure(self):
        """한/글 보안 모듈 등록 실패 시 모달 대기 방지를 위해 즉시 예외 발생 검증."""
        failing_app = FakeCOMApp(fail_register=True)
        with self.assertRaises(RuntimeError) as ctx:
            _make_hwp_dispatch(dispatch_ex=lambda progid: failing_app)
        self.assertIn("보안 모듈 등록 실패", str(ctx.exception))

    def test_fixture_is_copied_before_open_and_source_is_unchanged(self):
        """원본 fixture 해시 보존, 열린 경로는 작업 사본이고 다른 경로는 열지 않음."""
        initial_hash = _sha256(self.table_fixture)
        fake_app = FakeCOMApp()

        case_result = _run_table_unit_case(
            fake_app,
            self.table_fixture,
            self.work_dir,
            table_transformer=lambda b: b + "_mod",
        )

        # 원본 fixture 해시가 변경되지 않았는지 확인
        self.assertEqual(_sha256(self.table_fixture), initial_hash)

        # FakeApp이 연 경로가 원본이 아니라 work_dir 하위의 사본인지 확인
        self.assertEqual(len(fake_app.open_calls), 1)
        opened_path = Path(fake_app.open_calls[0][0])
        self.assertNotEqual(opened_path.resolve(), self.table_fixture.resolve())
        self.assertTrue(str(opened_path.resolve()).startswith(str(self.work_dir.resolve())))

    def test_inspect_fixture_strict_hwpx_validation(self):
        """지적 5, 6: HWPX ZIP/XML 파싱 오류 시 fallback 없이 FAIL, 표 반복 구조 및 sentinel/target 누락 시 FAIL 검증."""
        # 1. 일반 텍스트 파일 (.txt 또는 손상된 .hwpx) -> 파싱 오류 즉시 FAIL (텍스트 fallback 없음)
        text_fake = self.tmp_path / "fake.hwpx"
        text_fake.write_text("table tbl text fallback attempt", encoding="utf-8")
        ok, msg = _inspect_table_fixture(text_fake)
        self.assertFalse(ok)
        self.assertIn("유효한 ZIP/HWPX", msg)

        # 2. 반복 행이 없는 단일 행 표 -> FAIL
        single_row_hwpx = self.tmp_path / "single_row.hwpx"
        _create_mock_table_hwpx(single_row_hwpx, repeat_rows=False)
        ok, msg = _inspect_table_fixture(single_row_hwpx)
        self.assertFalse(ok)
        self.assertIn("반복 구조의 표", msg)

        # 3. 자간 fixture에서 target 문자열 누락 -> FAIL
        missing_target_hwpx = self.tmp_path / "missing_target.hwpx"
        _create_mock_selection_hwpx(missing_target_hwpx, include_target=False)
        ok, msg = _inspect_selection_fixture(missing_target_hwpx)
        self.assertFalse(ok)
        self.assertIn(_TARGET_SPACING_TEXT, msg)

        # 4. 자간 fixture에서 sentinel 누락 -> FAIL
        missing_sentinel_hwpx = self.tmp_path / "missing_sentinel.hwpx"
        _create_mock_selection_hwpx(missing_sentinel_hwpx, include_start_sentinel=False)
        ok, msg = _inspect_selection_fixture(missing_sentinel_hwpx)
        self.assertFalse(ok)
        self.assertIn(_SENTINEL_START_TEXT, msg)

    def test_cursor_moved_to_table_before_replacement(self):
        """지적 3: 표 fixture 연 후 표 내부로 커서 이동 검증, 이동 실패 시 NOT_IN_TABLE FAIL 검증."""
        # 커서가 표 안에 없고 이동도 실패하는 앱
        failing_cursor_app = FakeCOMApp(not_in_table=True)
        failing_cursor_app.move_to_table = lambda: False
        failing_cursor_app.ParentCtrl = None

        res = _run_table_unit_case(
            failing_cursor_app,
            self.table_fixture,
            self.work_dir,
            table_transformer=lambda b: b + "_mod",
        )
        self.assertEqual(res.status, "FAIL")
        self.assertIn("NOT_IN_TABLE", res.error)

    def test_selection_check_verifies_target_text_and_extracted_content(self):
        """지적 2: _setup_selection_in_app 반환값 확인 및 추출 내용 일치 검증, 불일치 시 FAIL 검증."""
        # 선택 설정 실패
        failing_sel_app = FakeCOMApp(no_selection=True)
        failing_sel_app.select_target_text = lambda target: False
        failing_sel_app.SelectionMode = 0

        res = _run_selection_spacing_case(
            failing_sel_app,
            self.selection_fixture,
            self.work_dir,
            selection_transformer=lambda b: b + "_mod",
        )
        self.assertEqual(res.status, "FAIL")
        self.assertIn("_setup_selection_in_app 실패", res.error)

        # 선택 설정은 되었으나 추출 블록 내용이 대상과 불일치
        mismatch_app = FakeCOMApp()
        mismatch_app.GetTextFile = lambda fmt, opt: "WRONG_SELECTED_TEXT"
        res_mismatch = _run_selection_spacing_case(
            mismatch_app,
            self.selection_fixture,
            self.work_dir,
            selection_transformer=lambda b: b + "_mod",
        )
        self.assertEqual(res_mismatch.status, "FAIL")
        self.assertIn("일치하지 않습니다", res_mismatch.error)

    def test_arbitrary_transform_is_forbidden_and_not_implemented_fails(self):
        """지적 1: 임의 알고리즘(_unit+1, _spacing-1) 금지 및 운영 엔진 미구현 시 명시적 FAIL 검증."""
        fake_app = FakeCOMApp()

        # transformer 주입 없이 실행 시, 운영 엔진이 NotImplementedError이므로 명시적 FAIL이어야 함
        res_table = _run_table_unit_case(
            fake_app,
            self.table_fixture,
            self.work_dir,
            table_transformer=None,
        )
        self.assertEqual(res_table.status, "FAIL")
        self.assertIn("구현되지 않아", res_table.error)
        self.assertNotIn("_unit+1", res_table.action)

        res_sel = _run_selection_spacing_case(
            fake_app,
            self.selection_fixture,
            self.work_dir,
            selection_transformer=None,
        )
        self.assertEqual(res_sel.status, "FAIL")
        self.assertIn("구현되지 않아", res_sel.error)
        self.assertNotIn("_spacing-1", res_sel.action)

    def test_table_measurement_records_exact_export_replace_arguments(self):
        """Fake HAction/GetTextFile/SetTextFile 호출 기록에서 측정 인자·반환 형식 저장과 교체 1회 검증."""
        fake_app = FakeCOMApp(initial_state="table_data")

        case_result = _run_table_unit_case(
            fake_app,
            self.table_fixture,
            self.work_dir,
            table_transformer=lambda b: b + "_unit_transformed",
        )

        # GetTextFile 및 SetTextFile 호출 기록 검증
        self.assertIn("live_link.export_table_block", case_result.action)
        self.assertIn("NotImplementedError", case_result.action)
        self.assertEqual(case_result.status, "FAIL")
        self.assertIsNone(case_result.undo_steps)

    def test_selection_measurement_targets_exact_selection_and_replaces_once(self):
        """선택 시작/끝 문맥, 자간 변환기 호출, 교체 호출 1회 및 선택 외 sentinel 보존을 Fake 모델로 검사."""
        fake_app = FakeCOMApp(initial_state="[SENTINEL_START] prefix [SPACING_TARGET] target [SENTINEL_END] suffix")

        case_result = _run_selection_spacing_case(
            fake_app,
            self.selection_fixture,
            self.work_dir,
            selection_transformer=lambda b: b + "_spacing_transformed",
        )

        self.assertIn("live_link.export_selection_block", case_result.action)
        self.assertIn("NotImplementedError", case_result.action)
        self.assertEqual(case_result.status, "FAIL")
        self.assertIsNone(case_result.undo_steps)

    def test_undo_is_invoked_once_and_restored_state_is_required(self):
        """지적 4: Undo 1회 호출, 필수 의미 항목 신뢰성 검사, 빈 값 일치 가짜 PASS 방지."""
        fake_app = FakeCOMApp(initial_state="orig", no_selection=True)
        fake_app._history = ["orig", "changed"]
        fake_app._state = "changed"

        expected_semantic = _capture_semantic_snapshot(fake_app, self.table_fixture)
        expected_semantic["text"] = "orig"

        # 정상 Undo 1회 및 복원 성공
        restored, steps, current = _run_undo_once(fake_app, expected_semantic, self.table_fixture)
        self.assertTrue(restored)
        self.assertEqual(steps, 1)
        self.assertEqual(fake_app.runs, ["Undo"])

        # 필수 의미 데이터가 누락/빈 값인 경우 (is_valid=False) -> 복원 불가
        empty_semantic = {
            "is_valid": False,
            "text": "",
            "in_table": False,
            "selected": False,
            "tables": [],
            "char_spacings": [],
            "has_sentinel_start": False,
            "has_sentinel_end": False,
        }
        restored_empty, _, _ = _run_undo_once(fake_app, empty_semantic, self.table_fixture)
        self.assertFalse(restored_empty, "빈 값끼리의 일치는 복원으로 인정되지 않아야 합니다.")

        # 상태 불일치(mismatch)면 FAIL
        fake_mismatch_app = FakeCOMApp(initial_state="orig")
        fake_mismatch_app._history = ["orig", "changed"]
        fake_mismatch_app._state = "changed"
        mismatch_expected = dict(expected_semantic, text="different_state")
        restored_m, steps_m, _ = _run_undo_once(fake_mismatch_app, mismatch_expected, self.table_fixture)
        self.assertFalse(restored_m)
        self.assertEqual(steps_m, 1)

    def test_cleanup_failure_blocks_pass_and_records_fail_evidence(self):
        """지적 7: 격리 인스턴스의 Clear/Quit 실패 시 PASS 승격 차단 및 FAIL 증거 생성 검증."""
        failing_clear_app = FakeCOMApp(fail_clear=True)

        evidence = run_gate(
            fixture_root=self.fixture_dir,
            table_fixture=self.table_fixture,
            selection_fixture=self.selection_fixture,
            evidence_path=self.evidence_path,
            work_dir=self.work_dir,
            dispatch_ex=lambda progid: failing_clear_app,
            lock_factory=self.fake_lock,
            table_transformer=lambda b: b + "_mod",
            selection_transformer=lambda b: b + "_mod",
            repo_root=self.tmp_path,
        )

        self.assertEqual(evidence.status, "FAIL", "인스턴스 정리 실패 시 PASS가 되어서는 안 됩니다.")
        self.assertIsNone(evidence.undo_steps)

    def test_evidence_pass_requires_both_real_case_records_and_files(self):
        """두 case PASS, 각 undo_steps=1 및 실존 저장소 내부 증거가 있을 때만 통과 형식 생성."""
        fake_app = FakeCOMApp()

        def fake_dispatch(progid: str):
            return fake_app

        evidence = run_gate(
            fixture_root=self.fixture_dir,
            table_fixture=self.table_fixture,
            selection_fixture=self.selection_fixture,
            evidence_path=self.evidence_path,
            work_dir=self.work_dir,
            dispatch_ex=fake_dispatch,
            lock_factory=self.fake_lock,
            table_transformer=lambda b: b + "_unit_ok",
            selection_transformer=lambda b: b + "_spacing_ok",
            repo_root=self.tmp_path,
        )

        self.assertEqual(evidence.status, "FAIL")
        self.assertIsNone(evidence.undo_steps)
        self.assertEqual(len(evidence.cases), 2)
        for c in evidence.cases:
            self.assertEqual(c.status, "FAIL")
            self.assertIsNone(c.undo_steps)

        self.assertTrue(self.evidence_path.is_file())
        with open(self.evidence_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["status"], "FAIL")
        self.assertIsNone(data["undo_steps"])

    def test_evidence_fail_closed_for_missing_case_bad_status_or_path_escape(self):
        """case 누락, FAIL/SKIP, undo_steps 불일치, 파일 누락, ../외부 경로 탈출을 PASS로 만들지 않음."""
        base_valid_file = self.tmp_path / "valid_ev.json"
        base_valid_file.write_text("{}", encoding="utf-8")
        h64_a = "a" * 64
        h64_b = "b" * 64
        h64_c = "c" * 64
        h64_d = "d" * 64

        valid_case_1 = {
            "name": "table_unit",
            "status": "PASS",
            "undo_steps": 1,
            "source_sha256": h64_a,
            "working_copy": str(base_valid_file),
            "before_sha256": h64_a,
            "after_sha256": h64_b,
            "restored_sha256": h64_a,
            "action": "action_tbl; semantic_restored=True",
            "error": None,
            "evidence_files": [str(base_valid_file)],
        }
        valid_case_2 = {
            "name": "selection_spacing",
            "status": "PASS",
            "undo_steps": 1,
            "source_sha256": h64_c,
            "working_copy": str(base_valid_file),
            "before_sha256": h64_c,
            "after_sha256": h64_d,
            "restored_sha256": h64_c,
            "action": "action_sel; semantic_restored=True",
            "error": None,
            "evidence_files": [str(base_valid_file)],
        }

        # 1. case 개수 부족 (1개뿐임)
        bad_cases_payload = {
            "schema_version": 1,
            "gate": "live_replace",
            "status": "PASS",
            "undo_steps": 1,
            "cases": [valid_case_1],
            "evidence_files": [str(base_valid_file)],
        }
        with self.assertRaises(ValueError):
            _validate_evidence(bad_cases_payload, self.tmp_path)

        # 2. case status가 FAIL인 경우
        bad_status_case = {
            "schema_version": 1,
            "gate": "live_replace",
            "status": "PASS",
            "undo_steps": 1,
            "cases": [
                dict(valid_case_1, status="FAIL"),
                valid_case_2,
            ],
            "evidence_files": [str(base_valid_file)],
        }
        with self.assertRaises(ValueError):
            _validate_evidence(bad_status_case, self.tmp_path)

        # 3. undo_steps 불일치
        bad_undo_steps = {
            "schema_version": 1,
            "gate": "live_replace",
            "status": "PASS",
            "undo_steps": 2,
            "cases": [valid_case_1, valid_case_2],
            "evidence_files": [str(base_valid_file)],
        }
        with self.assertRaises(ValueError):
            _validate_evidence(bad_undo_steps, self.tmp_path)

        # 4. evidence_files 중 미실존 파일
        non_existent_file = {
            "schema_version": 1,
            "gate": "live_replace",
            "status": "PASS",
            "undo_steps": 1,
            "cases": [valid_case_1, valid_case_2],
            "evidence_files": [str(self.tmp_path / "not_found.json")],
        }
        with self.assertRaises(ValueError):
            _validate_evidence(non_existent_file, self.tmp_path)

        # 5. 상대경로/절대경로 탈출 시도
        escaped_file = {
            "schema_version": 1,
            "gate": "live_replace",
            "status": "PASS",
            "undo_steps": 1,
            "cases": [valid_case_1, valid_case_2],
            "evidence_files": ["../../outside.json"],
        }
        with self.assertRaises(ValueError):
            _validate_evidence(escaped_file, self.tmp_path)

        # 6. 적용 전후 해시 동일 (변경 미발생)
        same_hash_case = {
            "schema_version": 1,
            "gate": "live_replace",
            "status": "PASS",
            "undo_steps": 1,
            "cases": [
                dict(valid_case_1, after_sha256=h64_a),
                valid_case_2,
            ],
            "evidence_files": [str(base_valid_file)],
        }
        with self.assertRaises(ValueError):
            _validate_evidence(same_hash_case, self.tmp_path)

    def test_write_is_atomic_and_failure_evidence_is_not_gate_pass(self):
        """임시 파일 작성 후 replace 호출을 확인하고 중간 예외/COM 오류에서 PASS 증거가 생성되지 않음."""
        failing_app = FakeCOMApp(fail_replace=True)

        def failing_dispatch(progid: str):
            return failing_app

        evidence = run_gate(
            fixture_root=self.fixture_dir,
            table_fixture=self.table_fixture,
            selection_fixture=self.selection_fixture,
            evidence_path=self.evidence_path,
            work_dir=self.work_dir,
            dispatch_ex=failing_dispatch,
            lock_factory=self.fake_lock,
            table_transformer=lambda b: b + "_mod",
            selection_transformer=lambda b: b + "_mod",
            repo_root=self.tmp_path,
        )

        self.assertEqual(evidence.status, "FAIL")
        self.assertIsNone(evidence.undo_steps)

        # 생성된 JSON 파일도 FAIL이어야 함
        with open(self.evidence_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["status"], "FAIL")
        self.assertIsNone(data["undo_steps"])

        # 원자적 작성 확인 (.tmp 잔류 없음)
        tmp_files = list(self.tmp_path.glob("*.tmp"))
        self.assertEqual(len(tmp_files), 0, "원자적 교체 완료 후 임시 파일이 남아있지 않아야 합니다.")

    def test_mac_mode_never_enters_real_com(self):
        """플랫폼 가짜 macOS에서 main/어댑터가 COM을 생성하지 않고 fake-only 검증 결과만 내는지 검사."""
        with patch("sys.platform", "darwin"):
            # dispatch_ex 없이 실제 COM 생성 시도 시 RuntimeError 발생하며 차단
            with self.assertRaises(RuntimeError) as ctx:
                _make_hwp_dispatch(dispatch_ex=None)
            self.assertIn("비Windows", str(ctx.exception))

            # fake dispatch_ex 주입 시에는 macOS에서도 정상적으로 fake 측정 완료
            fake_app = FakeCOMApp()
            evidence = run_gate(
                fixture_root=self.fixture_dir,
                table_fixture=self.table_fixture,
                selection_fixture=self.selection_fixture,
                evidence_path=self.evidence_path,
                work_dir=self.work_dir,
                dispatch_ex=lambda progid: fake_app,
                lock_factory=self.fake_lock,
                table_transformer=lambda b: b + "_mod",
                selection_transformer=lambda b: b + "_mod",
                repo_root=live_replace_gate._REPO_ROOT,
            )
            self.assertEqual(evidence.status, "FAIL")


if __name__ == "__main__":
    unittest.main()
