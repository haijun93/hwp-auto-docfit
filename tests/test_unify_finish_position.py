"""서식 통일 마무리: 고친 문장을 계획 위치로 바로 찾고, 위치의 글이 다르면 예전처럼 순회해 찾는다(알파, 2026-10-11)."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]


class FakeDoc:
    """문단 글 목록만 가진 한/글 흉내. 위치는 (0, 문단 번호, 0)."""

    def __init__(self, texts):
        self.texts = texts
        self.index = 0
        self.reads = 0

    def SetPos(self, list_id, para, pos):
        if not 0 <= para < len(self.texts):
            return False
        self.index = para
        return True

    def GetPos(self):
        return (0, self.index, 0)

    def run(self, command):
        if command == "MoveDocBegin":
            self.index = 0
        return True

    def text(self):
        self.reads += 1
        return self.texts[self.index]

    def next_para(self):
        if self.index + 1 >= len(self.texts):
            return False
        self.index += 1
        return True


class UnifyFinishPositionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(ROOT / "hwp-auto-docfit.py"))

    def run_finish(self, texts, targets, positions, flag=True):
        fn = self.ns["서식통일_보류자간_재조정"]
        g = fn.__globals__
        doc = FakeDoc(texts)
        finished = []
        saved = {k: g.get(k) for k in ("hwp", "hwp_run", "현재문단_텍스트", "서식통일_문장_마무리", "다음_문단으로_진행",
                                       "중단_요청됨", "진단로그", "로그", "단계표시", "검수_문제_기록",
                                       "알파_서식통일_위치마무리_사용")}
        g.update({
            "hwp": doc, "hwp_run": doc.run, "현재문단_텍스트": doc.text, "다음_문단으로_진행": doc.next_para,
            "서식통일_문장_마무리": lambda 시작, text, 내어쓰기: finished.append((시작[1], text.strip(), 내어쓰기)) or True,
            "중단_요청됨": lambda: False, "진단로그": Mock(), "로그": Mock(), "단계표시": Mock(),
            "검수_문제_기록": Mock(), "알파_서식통일_위치마무리_사용": flag,
        })
        g["_서식통일_자간보류문단"].clear()
        g["_서식통일_위치텍스트_보관"].clear()
        g["_서식통일_보류위치"].clear()
        g["_서식통일_자간보류문단"].update(targets)
        g["_서식통일_보류위치"].update(positions)
        try:
            self.assertTrue(fn())
        finally:
            g.update(saved)
            for name in ("_서식통일_자간보류문단", "_서식통일_위치텍스트_보관", "_서식통일_보류위치"):
                g[name].clear()
        return finished, doc

    def test_finishes_at_planned_positions_without_traversal(self):
        texts = [f"ㅇ 문장 {i}" for i in range(50)]
        targets = {"ㅇ 문장 40": True, "ㅇ 문장 3": False}
        positions = {"ㅇ 문장 40": (0, 40, 0), "ㅇ 문장 3": (0, 3, 0)}
        finished, doc = self.run_finish(texts, targets, positions)
        self.assertEqual(finished, [(3, "ㅇ 문장 3", False), (40, "ㅇ 문장 40", True)])
        self.assertEqual(doc.reads, 2)   # 대상 문장만 읽고 문서 전체를 순회하지 않는다

    def test_falls_back_to_traversal_when_text_moved(self):
        texts = ["ㅇ 첫 문장", "", "ㅇ 옮겨진 문장", "ㅇ 끝 문장"]
        targets = {"ㅇ 옮겨진 문장": True, "ㅇ 끝 문장": False}
        positions = {"ㅇ 옮겨진 문장": (0, 1, 0), "ㅇ 끝 문장": (0, 3, 0)}   # 첫째는 위치가 한 칸 어긋남
        finished, _ = self.run_finish(texts, targets, positions)
        self.assertCountEqual(finished, [(3, "ㅇ 끝 문장", False), (2, "ㅇ 옮겨진 문장", True)])

    def test_flag_off_keeps_traversal(self):
        texts = [f"ㅇ 문장 {i}" for i in range(10)]
        targets = {"ㅇ 문장 7": True}
        finished, doc = self.run_finish(texts, targets, {"ㅇ 문장 7": (0, 7, 0)}, flag=False)
        self.assertEqual(finished, [(7, "ㅇ 문장 7", True)])
        self.assertEqual(doc.reads, 8)   # 예전 방식: 처음부터 그 문장까지 읽는다


if __name__ == "__main__":
    unittest.main()
