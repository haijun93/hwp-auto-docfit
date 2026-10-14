"""Actual engine entrypoints, callbacks and simultaneous run-state isolation."""
from concurrent.futures import ThreadPoolExecutor
import runpy
from pathlib import Path
import threading
import unittest
from docfit_core.app_state import RunOptions
from docfit_engine.context import RunContext, current_context
from docfit_engine.pipeline import PipelineCallbacks
from docfit_engine.runtime import session_for


class RunContextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).parents[1] / "hwp-auto-docfit.py"))
        cls.session = session_for(cls.ns["_문서_처리_1회"].__globals__)

    def context(self, action, callbacks):
        return self.session.new_context(
            options=RunOptions(mode="unify", verify_result=False),
            profile={"font": "시험 글꼴"},
            callbacks=callbacks,
            state={"중단_요청됨": lambda: False, "hwp_run": lambda _: True,
                   "순회_시작": lambda: None,
                   "단계시간_구간": lambda _: None,
                   "stage_enabled": lambda *args: False,
                   "서식통일_전체_적용": action})

    def test_actual_document_stage_reports_enter_exit_and_status(self):
        events = []
        callbacks = PipelineCallbacks(log=lambda value: events.append(("log", value)),
            status=lambda value: events.append(("status", value)),
            progress=lambda value: events.append(("progress", value)),
            on_stage_enter=lambda value: events.append(("enter", value)),
            on_stage_exit=lambda value, result: events.append(("exit", value, result)))
        context = self.context(lambda: True, callbacks)
        self.assertTrue(self.ns["문서_처리_1회"]("test.hwpx", context=context, callbacks=callbacks))
        self.assertIn(("enter", "서식통일"), events)
        self.assertIn(("exit", "서식통일", True), events)
        self.assertTrue(any(event[0] == "log" for event in events))
        self.assertTrue(any(event[0] == "status" for event in events))
        self.assertIsNone(current_context())

    def test_stage_errors_are_reported_and_propagated(self):
        errors = []
        def fail():
            raise RuntimeError("action failed")
        callbacks = PipelineCallbacks(on_stage_error=lambda name, error: errors.append((name, str(error))))
        context = self.context(fail, callbacks)
        with self.assertRaisesRegex(RuntimeError, "action failed"):
            self.ns["_문서_처리_1회"]("test.hwpx", context=context)
        self.assertEqual(errors, [("서식통일", "action failed")])
        self.assertIsNone(current_context())

    def test_parallel_runs_do_not_share_caches_profiles_or_bootstrap_globals(self):
        barrier = threading.Barrier(2)
        bootstrap = self.session.namespace
        original = bootstrap["_서식통일_문서대표프로필"]
        def run(label):
            def action():
                context = current_context()
                context.state["_서식통일_문서대표프로필"]["owner"] = label
                barrier.wait(3)
                self.assertEqual(context.state["_서식통일_문서대표프로필"], {"owner": label})
                self.assertIsNot(context.function("_문서_처리_1회").__globals__, bootstrap)
                return True
            context = self.context(action, PipelineCallbacks())
            self.assertTrue(self.ns["문서_처리_1회"]("test.hwpx", context=context))
            return context
        with ThreadPoolExecutor(2) as workers:
            first, second = list(workers.map(run, ("A", "B")))
        self.assertIs(bootstrap["_서식통일_문서대표프로필"], original)
        self.assertEqual(first.state["_서식통일_문서대표프로필"], {"owner": "A"})
        self.assertEqual(second.state["_서식통일_문서대표프로필"], {"owner": "B"})
        self.assertIsNot(first.cancellation, second.cancellation)
        first.cancellation.set()
        self.assertFalse(second.cancellation.is_set())
        from defusedxml.ElementTree import fromstring
        from docfit_engine.context import RunContext
        original = {"preserved"}
        cloned = RunContext({"members": original}).state["members"]
        self.assertEqual(cloned, original)
        cloned.add("isolated")
        self.assertEqual(original, {"preserved"})
        xml = fromstring("<cache><item/></cache>")
        a = self.session.new_context(state={"xml_cache": xml})
        b = self.session.new_context(state={"xml_cache": xml})
        a.state["xml_cache"][0].set("owner", "A")
        self.assertIsNone(b.state["xml_cache"][0].get("owner"))
        self.assertIsNone(xml[0].get("owner"))
        first.profile["font"] = "수정"
        self.assertEqual(second.profile["font"], "시험 글꼴")


    def test_real_job_entry_reports_through_callbacks_and_honors_options(self):
        from types import SimpleNamespace
        events = []
        callbacks = PipelineCallbacks(
            status=lambda text: events.append(("status", text)),
            event=lambda event: events.append(event))
        context = self.session.new_context(
            options=RunOptions(mode="spacing", exclude_tables=True, verify_result=False),
            callbacks=callbacks,
            state={"중단_요청됨": lambda: True, "보안모듈_초기화": lambda: None,
                   "원본_뷰어_분리": lambda: None, "작업창_분리": lambda: None,
                   "설정_불러오기": lambda: {},
                   "pythoncom": SimpleNamespace(CoInitialize=lambda: None, CoUninitialize=lambda: None)})
        self.ns["작업_실행"]([], context=context, callbacks=callbacks, 준말_등록={})
        self.assertEqual(context.state["작업_모드"], "spacing")
        self.assertFalse(context.state["표_자간조정_사용"])
        self.assertIn(("stopped", None), events)
        self.assertTrue(any(event[0] == "status" for event in events))
        self.assertFalse(any(event[0] == "fatal_error" for event in events), events)


    def test_bare_context_is_seeded_only_at_the_compatibility_boundary(self):
        context = RunContext(options=RunOptions(mode="unify", verify_result=False),
            state={"중단_요청됨": lambda: False, "hwp_run": lambda _: True,
                   "순회_시작": lambda: None, "단계시간_구간": lambda _: None,
                   "stage_enabled": lambda *args: False,
                   "서식통일_전체_적용": lambda: True},
            callbacks=PipelineCallbacks())
        self.assertTrue(self.ns["문서_처리_1회"]("test.hwpx", context=context))
        self.assertIsNot(context.function("문서_처리_1회").__globals__, self.session.namespace)

    def test_context_options_resolve_stages_when_no_selection_is_supplied(self):
        from types import SimpleNamespace
        context = self.session.new_context(
            options=RunOptions(mode="all", reset_spacing=False, exclude_tables=True),
            state={"중단_요청됨": lambda: True, "보안모듈_초기화": lambda: None,
                   "원본_뷰어_분리": lambda: None, "작업창_분리": lambda: None,
                   "설정_불러오기": lambda: {},
                   "pythoncom": SimpleNamespace(CoInitialize=lambda: None, CoUninitialize=lambda: None)})
        self.ns["작업_실행"]([], context=context, 준말_등록={})
        stages = context.state["선택_세부작업"]
        self.assertFalse(stages["reset_spacing"])
        self.assertFalse(stages["table_style"])
        self.assertFalse(stages["control_spacing"])
