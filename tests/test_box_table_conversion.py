"""'텍스트 표(박스 그림) 변환' 단계의 한/글 COM 연동 로직을 검증한다.

실제 한/글 COM 동작(SelectText/Delete가 여러 문단에 걸쳐 정확히 어떻게
합쳐지는지 등)까지는 가짜 객체로 재현할 수 없으므로, 이 테스트는 다음만
확인한다:
    - 문서를 훑어 박스 그림 표 블록을 찾고, 뒤에 있는 표부터 순서대로
      바꾸는 제어 흐름(``박스그림_전체_적용``).
    - 문단 범위 선택·삭제·재배치 호출 인자가 올바른지(``_박스그림표_교체``).
    - 실제 표 생성 HAction 호출값과 셀 채우는 순서(``_박스그림표_한글표_삽입``).

셀 텍스트 파싱 자체(테두리/내용 줄 판별, 행렬 변환)는
tests/test_text_table.py에서 순수 함수로 이미 검증한다.
"""

from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"


class FakeHwpWalk:
    """본문(list id 0) 문단 목록만 흉내 내는 가짜 hwp. 표·글상자는 다루지 않는다."""

    def __init__(self, paragraphs):
        self.paragraphs = list(paragraphs)
        self.pos = (0, 0, 0)

    def GetPos(self):
        return self.pos

    def SetPos(self, *pos):
        self.pos = tuple(pos)


def _walk_run(fake):
    def run(action):
        _, para, _ = fake.pos
        if action == "MoveDocBegin":
            fake.pos = (0, 0, 0)
        elif action == "MoveNextParaBegin":
            if para + 1 < len(fake.paragraphs):
                fake.pos = (0, para + 1, 0)
        return True

    return run


class BoxGridApplyAllTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(SOURCE), run_name="box_table_apply_all_test")

    def _run(self, paragraphs, replace_calls):
        fn = self.ns["박스그림_전체_적용"]
        fake = FakeHwpWalk(paragraphs)
        with patch.dict(fn.__globals__, {
            "hwp": fake,
            "hwp_run": _walk_run(fake),
            "현재문단_텍스트": lambda: fake.paragraphs[fake.pos[1]],
            "중단_요청됨": lambda: False,
            "로그": lambda *a, **k: None,
            "_박스그림표_교체": lambda 시작, 끝, 행들: replace_calls.append((시작, 끝, 행들)),
        }):
            return fn()

    def test_finds_single_table_and_replaces_it(self):
        paragraphs = ["ㅁ 추진 개요", "┌───┬───┐", "│ a │ b │", "└───┴───┘", "ㅇ 이하 생략"]
        replace_calls = []
        self.assertTrue(self._run(paragraphs, replace_calls))
        self.assertEqual(replace_calls, [(1, 3, [["a", "b"]])])

    def test_converts_from_last_match_to_first(self):
        table_a = ["┌───┬───┐", "│ a │ b │", "└───┴───┘"]
        table_b = ["┌───┐", "│ c │", "└───┘"]
        paragraphs = table_a + ["본문"] + table_b
        replace_calls = []
        self.assertTrue(self._run(paragraphs, replace_calls))
        self.assertEqual([(시작, 끝) for 시작, 끝, _ in replace_calls], [(4, 6), (0, 2)])

    def test_no_table_found_does_not_call_replace(self):
        paragraphs = ["ㅁ 제목", "ㅇ 본문 내용"]
        replace_calls = []
        self.assertTrue(self._run(paragraphs, replace_calls))
        self.assertEqual(replace_calls, [])

    def test_stop_requested_aborts_immediately(self):
        fn = self.ns["박스그림_전체_적용"]
        fake = FakeHwpWalk(["ㅁ 제목"])
        with patch.dict(fn.__globals__, {
            "hwp": fake,
            "hwp_run": _walk_run(fake),
            "현재문단_텍스트": lambda: fake.paragraphs[fake.pos[1]],
            "중단_요청됨": lambda: True,
            "로그": lambda *a, **k: None,
        }):
            self.assertFalse(fn())


class BoxGridReplaceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(SOURCE), run_name="box_table_replace_test")

    def test_selects_from_block_start_to_end_of_last_line_then_inserts_table(self):
        fn = self.ns["_박스그림표_교체"]

        class FakeHwp:
            def __init__(self):
                self.pos = (0, 0, 0)
                self.selection = None
                self.deleted = False

            def GetPos(self):
                return self.pos

            def SetPos(self, *pos):
                self.pos = tuple(pos)

            def SelectText(self, spara, spos, epara, epos):
                self.selection = (spara, spos, epara, epos)
                return True

        fake = FakeHwp()

        def run(action):
            if action == "MoveParaEnd":
                # 끝 문단(7번)의 텍스트 길이가 12자라고 가정한다.
                fake.pos = (fake.pos[0], fake.pos[1], 12)
            elif action == "Delete":
                fake.deleted = True
            return True

        insert_calls = []
        with patch.dict(fn.__globals__, {
            "hwp": fake,
            "hwp_run": run,
            "_박스그림표_한글표_삽입": lambda 행들: insert_calls.append(행들),
        }):
            fn(5, 7, [["구분", "내용"]])

        self.assertEqual(fake.selection, (5, 0, 7, 12))
        self.assertTrue(fake.deleted)
        self.assertEqual(fake.GetPos(), (0, 5, 0))
        self.assertEqual(insert_calls, [[["구분", "내용"]]])

    def test_raises_when_selection_fails(self):
        fn = self.ns["_박스그림표_교체"]

        class FailingHwp:
            def __init__(self):
                self.pos = (0, 0, 0)

            def GetPos(self):
                return self.pos

            def SetPos(self, *pos):
                self.pos = tuple(pos)

            def SelectText(self, *args):
                return False

        fake = FailingHwp()
        with patch.dict(fn.__globals__, {
            "hwp": fake,
            "hwp_run": lambda action: True,
        }):
            with self.assertRaises(RuntimeError):
                fn(0, 2, [["a"]])


class BoxGridTableInsertTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(SOURCE), run_name="box_table_insert_test")

    def _fake_hwp(self):
        class TableProperties:
            TreatAsChar = None

        class ParamSet:
            def __init__(self):
                self.Rows = None
                self.Cols = None
                self.WidthType = None
                self.HeightType = None
                self.TableProperties = TableProperties()
                self.HSet = object()

        class FakeAction:
            def __init__(self, pset):
                self._pset = pset
                self.calls = []

            def GetDefault(self, name, hset):
                self.calls.append(("default", name))

            def Execute(self, name, hset):
                p = self._pset
                self.calls.append(("execute", name, p.Rows, p.Cols, p.WidthType,
                                    p.HeightType, p.TableProperties.TreatAsChar))
                return True

        class FakeHwp:
            def __init__(self):
                self._pset = ParamSet()
                self.HAction = FakeAction(self._pset)

            @property
            def HParameterSet(self):
                pset = self._pset

                class NS:
                    HTableCreation = pset

                return NS()

        return FakeHwp()

    def test_creates_table_with_expected_size_and_fills_cells_in_reading_order(self):
        fn = self.ns["_박스그림표_한글표_삽입"]
        fake = self._fake_hwp()
        inserted = []
        run_calls = []
        with patch.dict(fn.__globals__, {
            "hwp": fake,
            "텍스트_삽입": lambda text: inserted.append(text),
            "hwp_run": lambda cmd: run_calls.append(cmd) or True,
        }):
            fn([["구분", "내용"], ["추진", "완료"]])

        self.assertEqual(fake.HAction.calls, [
            ("default", "TableCreate"),
            ("execute", "TableCreate", 2, 2, 0, 0, 1),
        ])
        self.assertEqual(inserted, ["구분", "내용", "추진", "완료"])
        # 마지막 칸 뒤에는 TableRightCell을 호출하지 않고 표 밖으로 나간다(Cancel).
        self.assertEqual(run_calls, ["TableRightCell", "TableRightCell", "TableRightCell", "Cancel"])

    def test_empty_cell_is_skipped_but_navigation_still_advances(self):
        fn = self.ns["_박스그림표_한글표_삽입"]
        fake = self._fake_hwp()
        inserted = []
        run_calls = []
        with patch.dict(fn.__globals__, {
            "hwp": fake,
            "텍스트_삽입": lambda text: inserted.append(text),
            "hwp_run": lambda cmd: run_calls.append(cmd) or True,
        }):
            fn([["", "b"]])

        # 빈 칸은 텍스트를 넣지 않지만, 다음 칸으로 넘어가는 TableRightCell은 그대로 실행된다.
        self.assertEqual(inserted, ["b"])
        self.assertEqual(run_calls, ["TableRightCell", "Cancel"])

    def test_ragged_rows_are_padded_to_widest_row(self):
        fn = self.ns["_박스그림표_한글표_삽입"]
        fake = self._fake_hwp()
        with patch.dict(fn.__globals__, {
            "hwp": fake,
            "텍스트_삽입": lambda text: None,
            "hwp_run": lambda cmd: True,
        }):
            fn([["a", "b", "c"], ["d"]])

        self.assertEqual(fake.HAction.calls[-1][2:4], (2, 3))  # Rows=2, Cols=3


if __name__ == "__main__":
    unittest.main()
