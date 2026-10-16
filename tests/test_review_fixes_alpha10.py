"""알파 10 코드 리뷰 지적 사항: 실행 컨텍스트와 UI·호환 전역 사이의 값 전달."""
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest

from docfit_engine.pipeline import PipelineCallbacks
from docfit_engine.runtime import session_for


class ReviewFixesAlpha10(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).parents[1] / "hwp-auto-docfit.py"))
        cls.namespace = cls.ns["_문서_처리_1회"].__globals__
        cls.session = session_for(cls.namespace)
        cls.gui = cls.namespace["HwpAutoDocFitGUI"]

    def test_legacy_call_keeps_globals_changed_by_ui_during_the_call(self):
        # 백그라운드 레거시 호출 중 UI가 서식 프로필 전역을 바꿔도 호출 종료 시 되돌리지 않는다.
        namespace = self.namespace
        before, marker = namespace["표준서식_설정"], {"marker": True}

        def ui_changes_profile(_message):
            namespace["표준서식_설정"] = marker

        try:
            self.ns["원본_DLL_찾기"](callbacks=PipelineCallbacks(log=ui_changes_profile))
            self.assertIs(namespace["표준서식_설정"], marker)
        finally:
            namespace["표준서식_설정"] = before

    def test_legacy_call_still_publishes_values_it_rebinds(self):
        namespace = self.namespace
        before = namespace["서식통일_결과창_사용"]
        try:
            self.ns["서식통일_결과창_반영"](not before)
            self.assertIs(namespace["서식통일_결과창_사용"], not before)
        finally:
            namespace["서식통일_결과창_사용"] = before

    def _review_request(self, context):
        events = []
        namespace = self.namespace
        queue = namespace["gui_queue"]

        class ImmediateQueue:
            def put(self, event):
                events.append(event)
                event[1]["done"].set()

        namespace["gui_queue"] = ImmediateQueue()
        try:
            fake = SimpleNamespace(closing=False)
            if context is None:
                return self.gui._서식통일_대표값_검토_요청(fake, "profile", {}), events
            with context.activate():
                return self.gui._서식통일_대표값_검토_요청(fake, "profile", {}), events
        finally:
            namespace["gui_queue"] = queue

    def test_review_request_carries_the_running_context_profile(self):
        context = self.session.new_context()
        profile = {("□", "본문", 1): {"font": ("옛 글꼴", 3)}}
        context.state["_서식통일_문서대표프로필"] = profile
        요청, events = self._review_request(context)
        self.assertIs(요청["profile"], profile)
        self.assertEqual(events[0][0], "style_unify_profile_review")
        요청, _ = self._review_request(None)
        self.assertIsNone(요청["profile"])

    def test_profile_review_edits_the_run_profile_not_the_bootstrap_global(self):
        bootstrap = self.namespace["_서식통일_문서대표프로필"]
        bootstrap_copy = dict(bootstrap)
        profile = {("□", "본문", 1): {"font": ("옛 글꼴", 3)}}
        요청 = {"payload": {}, "done": __import__("threading").Event(), "approved": False,
              "profile": profile}
        calls = []

        def notify(*args, **kwargs):
            # 대표값을 찾지 못하면 오류 알림 뒤 다시 묻는다. 무한 반복 대신 실패로 끝낸다.
            calls.append(args)
            if len(calls) > 3:
                raise AssertionError("검토창이 대표 프로필을 찾지 못해 반복했습니다.")
            return True

        fake = SimpleNamespace(root=SimpleNamespace(_docfit_hidden_backend=True),
                               _flutter_values={"0:font": "새 글꼴"}, _알림=notify)
        self.gui._서식통일_대표서식_검토창(fake, 요청)
        self.assertTrue(요청["approved"])
        self.assertTrue(요청["done"].is_set())
        self.assertEqual(profile[("□", "본문", 1)]["font"], ("새 글꼴", 3))
        self.assertIs(self.namespace["_서식통일_문서대표프로필"], bootstrap)
        self.assertEqual(bootstrap, bootstrap_copy)

    def test_compare_view_resize_uses_the_running_context_window(self):
        context = self.session.new_context(state={"작업_hwp_hwnd": 77, "원본_hwp_hwnd": 55})
        fake = SimpleNamespace(_run_context=context, running=True)
        self.assertEqual(self.gui._실행_창핸들(fake, "작업_hwp_hwnd"), 77)
        self.assertEqual(self.gui._실행_창핸들(fake, "원본_hwp_hwnd"), 55)
        fake.running = False
        self.assertEqual(self.gui._실행_창핸들(fake, "작업_hwp_hwnd"),
                         self.namespace["작업_hwp_hwnd"])


if __name__ == "__main__":
    unittest.main()
