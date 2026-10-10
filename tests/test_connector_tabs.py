"""연속된 연결 부호 문장 → 목차 점선(왼쪽 정렬 탭) 정렬(사용자 규칙, 2026-10-10)."""
import unittest

from defusedxml import ElementTree as ET

from docfit_core import connector_tabs as CT

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HH = "http://www.hancom.co.kr/hwpml/2011/head"


def section(*texts):
    ps = "".join(f'<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>{t}</hp:t></hp:run></hp:p>' for t in texts)
    return ET.fromstring(f'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="{HP}">{ps}</hs:sec>')


HEADER = (f'<hh:head xmlns:hh="{HH}" xmlns:hp="{HP}"><hh:refList>'
          '<hh:charProperties itemCnt="1"><hh:charPr id="0" height="1500"/></hh:charProperties>'
          '<hh:tabProperties itemCnt="1"><hh:tabPr id="0" autoTabLeft="0" autoTabRight="0"/></hh:tabProperties>'
          '<hh:paraProperties itemCnt="1"><hh:paraPr id="0" tabPrIDRef="0"/></hh:paraProperties>'
          '</hh:refList></hh:head>')


class ConnectorTabsTest(unittest.TestCase):
    def test_split_three_kinds(self):
        self.assertEqual(CT.split_connector("Ⅰ. 추진 배경 ........ 1"), ("Ⅰ. 추진 배경", "........", "1"))
        self.assertEqual(CT.split_connector("1단계 ------ 기본계획"), ("1단계", "------", "기본계획"))
        self.assertEqual(CT.split_connector("일    시      2026. 10. 7."), ("일    시", "      ", "2026. 10. 7."))
        self.assertIsNone(CT.split_connector("두 칸  공백"))
        self.assertIsNone(CT.split_connector("앞 ..... 가운데 ----- 뒤"))      # 부호가 둘이면 바꾸지 않는다

    def test_groups_split_by_kind_and_need_two_lines(self):
        root = section("가 ..... 1", "나 ....... 2", "다 ----- 3", "라 ----- 4", "외톨이 ...... 5", "보통 문장")
        groups = CT.groups_in(root)
        self.assertEqual([[g[2] for g in grp] for grp in groups], [["가", "나"], ["다", "라"]])

    def test_align_inserts_tab_and_left_tab_definition(self):
        header = ET.fromstring(HEADER)
        root = section("Ⅰ. 추진 배경 ........ 1", "Ⅱ. 추진 계획 .................. 3")
        stats = CT.align_connectors(header, [root], lambda c: 42520)
        self.assertEqual((stats["groups"], stats["paragraphs"]), (1, 2))
        tabs = [x for x in root.iter() if CT._tag(x) == "tab"]
        self.assertEqual(len(tabs), 2)
        self.assertEqual([t.tail for t in tabs], ["1", "3"])
        items = [x for x in header.iter() if CT._tag(x) == "tabItem"]
        self.assertTrue(all(i.get("type") == "LEFT" for i in items))          # 오른쪽 글 시작점 세로 정렬
        self.assertEqual(items[0].get("leader"), CT.LEADER["dot"][0])
        ps = [p for p in root if CT._tag(p) == "p"]
        self.assertEqual(len({p.get("paraPrIDRef") for p in ps}), 1)
        self.assertNotEqual(ps[0].get("paraPrIDRef"), "0")


if __name__ == '__main__':
    unittest.main()
