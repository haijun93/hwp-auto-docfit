import copy
from pathlib import Path
import runpy
import unittest


class ThreeRowTitleTableTest(unittest.TestCase):
    """3행1열 제목 표(제목 + 담당자 칸 2개, 실측: '마포문화재단 10월 주요 프로그램')."""

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def three_row(self, owner_texts):
        ns = self.ns
        header, section = ns['제목2행1열_원본자료']()
        table = copy.deepcopy(next(x for x in section.iter() if ns['제목_xml이름'](x) == 'tbl'))
        rows = [r for r in table if ns['제목_xml이름'](r) == 'tr']
        new_row = copy.deepcopy(rows[-1])
        table.insert(list(table).index(rows[-1]) + 1, new_row)
        table.set('rowCnt', '3')
        for row, text in zip(rows[-1:] + [new_row], owner_texts):
            texts = [t for t in row.iter() if ns['제목_xml이름'](t) == 't']
            texts[0].text = text
            for t in texts[1:]:
                t.text = ''
        return header, section, table

    def test_three_row_title_is_type3(self):
        _, _, table = self.three_row(['마포문화재단 경영본부장:오세인☎3274-8603', '마포문화재단 예술본부장:이선아☎3274-8511'])
        self.assertEqual(self.ns['제목_유형판별'](table), 3)
        self.assertEqual(self.ns['서식표_종류판별'](table), 'title3')

    def test_three_row_without_owner_is_not_title(self):
        _, _, table = self.three_row(['마포문화재단 경영본부장:오세인☎3274-8603', '일반 내용 칸'])
        self.assertIsNone(self.ns['제목_유형판별'](table))

    def test_extra_owner_cell_gets_owner_format(self):
        ns = self.ns
        header, section, table = self.three_row(['경영본부장 ☎1', '예술본부장 ☎2'])
        sample = next(x for x in section.iter() if ns['제목_xml이름'](x) == 'tbl')
        maps = ns['제목_참조병합'](header, copy.deepcopy(header))
        for cell in ns['제목_셀들'](table):
            cell.set('borderFillIDRef', '1')
        ns['제목_표서식_복사'](table, sample, maps)
        cells = ns['제목_셀들'](table)
        owner = ns['제목_셀들'](sample)[-1]
        self.assertEqual(cells[2].get('borderFillIDRef'), maps['borderFills'][owner.get('borderFillIDRef')])


if __name__ == '__main__':
    unittest.main()
