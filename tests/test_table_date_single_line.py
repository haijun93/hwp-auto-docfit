"""표 칸 안 날짜는 한 줄 표기가 원칙이다(사용자 규칙, 2026-10-10): 날짜 칸을 '한 줄로 입력'으로 둔다."""
import copy
from pathlib import Path
import runpy
import unittest


class TableDateSingleLineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.name = staticmethod(cls.ns['제목_xml이름'])

    def test_date_cell_detection(self):
        날짜칸인가 = self.ns['날짜칸인가']
        for text in ("’26. 10. 10.(토)", "2026. 10. 10.", "2026년 10월 10일(토) 14:00", "26.10.10.", "10. 6.(화) 10:00 ~"):
            self.assertTrue(날짜칸인가(text), text)
        for text in ("관광정책과장: 조희옥 ☎3153-8660", "구분", "",
                     "2026. 10. 10.부터 민원 안내 서비스를 시범 운영하여 대기 시간을 줄임"):
            self.assertFalse(날짜칸인가(text), text)

    def test_title_and_general_tables_get_single_line_date_cells(self):
        header, section = self.ns['제목_원본자료']()
        table = copy.deepcopy(next(x for x in section.iter() if self.name(x) == 'tbl'))
        cells = self.ns['제목_셀들'](table)
        # A2(날짜 칸)에 날짜를 넣는다.
        date_cell = cells[1]
        t = next(x for x in date_cell.iter() if self.name(x) == 't')
        t.text = "’26. 10. 10.(토)"
        for x in list(t):
            t.remove(x)
        self.assertGreaterEqual(self.ns['표_날짜칸_한줄'](table), 1)
        sub = self.ns['제목_자식'](date_cell, 'subList')
        self.assertEqual(sub.get('lineWrap'), 'SQUEEZE')
        # 제목 칸은 그대로
        self.assertNotEqual(self.ns['제목_자식'](cells[0], 'subList').get('lineWrap'), 'SQUEEZE')
        self.assertEqual(self.ns['제목_날짜칸_한줄'](table), 0)    # 이미 한 줄이면 다시 바꾸지 않는다


if __name__ == '__main__':
    unittest.main()
