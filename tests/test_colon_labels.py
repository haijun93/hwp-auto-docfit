"""연속된 '항목기호 + 짧은 라벨 + 콜론' 문장의 콜론 세로 정렬(사용자 규칙, 2026-10-10)."""
import unittest

from defusedxml import ElementTree as ET

from docfit_core import colon_labels as CL

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HH = "http://www.hancom.co.kr/hwpml/2011/head"
HEADER = (f'<hh:head xmlns:hh="{HH}"><hh:refList><hh:charProperties itemCnt="1"><hh:charPr id="0" height="1500">'
          '<hh:ratio hangul="100" latin="100"/><hh:spacing hangul="0" latin="0"/></hh:charPr></hh:charProperties>'
          '</hh:refList></hh:head>')


def section(*texts):
    ps = "".join(f'<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>{t}</hp:t></hp:run></hp:p>' for t in texts)
    return ET.fromstring(f'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="{HP}">{ps}</hs:sec>')


class ColonLabelTest(unittest.TestCase):
    def test_label_detection(self):
        self.assertEqual(CL.label_of("- 공사명: 현수식 안내판 철거"), (2, 5, 5))
        self.assertEqual(CL.label_of("ㅇ 참석대상: 구민"), (2, 6, 6))
        self.assertIsNone(CL.label_of("긴 문장 안의 콜론: 없음"))                     # 항목기호 없음
        self.assertIsNone(CL.label_of("- 일곱글자라벨임: 값"))                          # 라벨 7자 이상은 제외
        self.assertEqual(CL.label_of("- 행사명이름명: 도토리만두"), (2, 8, 8))              # 6자는 대상

    def test_stretch_formula(self):
        self.assertEqual(CL.plan("공사명", 4.0), (0, 50, 100))      # 3자→4자(홀짝 다름): 자간만
        self.assertEqual(CL.plan("장소", 4.0), (3, 50, 100))        # 2자→4자(짝짝): '장   소' 빈칸 + 미세 자간
        self.assertEqual(CL.plan("행사명", 6.0)[0], 2)              # 3자→6자: 글자 사이 빈칸 + 자간
        self.assertEqual(CL.plan("공사기간", 4.0), (0, 0, 100))     # 기준 라벨은 그대로

    def test_group_alignment_splits_label_runs_and_keeps_text(self):
        header = ET.fromstring(HEADER)
        root = section("- 공사명: 현수식 안내판 철거", "- 공사기간: 2026. 10. 11.", "- 계약방식: 수의계약")
        before = ["".join(p.itertext()) for p in root]
        stats = CL.align_colons(header, [root])
        self.assertEqual(stats, {"groups": 1, "stretched": 1})
        self.assertEqual(["".join(p.itertext()) for p in root], before)
        first = [r for r in root[0] if CL._tag(r) == "run"]
        self.assertEqual(["".join(r.itertext()) for r in first], ["- ", "공사", "명", ": 현수식 안내판 철거"])   # 빈칸 없음
        shapes = {c.get("id"): c for c in header.iter() if CL._tag(c) == "charPr"}
        spaced = shapes[first[1].get("charPrIDRef")]
        self.assertEqual(next(x for x in spaced if CL._tag(x) == "spacing").get("hangul"), "50")
        last = shapes[first[2].get("charPrIDRef")]
        self.assertEqual(next(x for x in last if CL._tag(x) == "spacing").get("hangul"), "0")

    def test_long_label_line_is_skipped_but_group_continues(self):
        header = ET.fromstring(HEADER)
        root = section("- 장소: 구청", "- 아주긴예외라벨이름: 값", "- 참여대상: 구민")
        groups = CL.groups_in(root)
        self.assertEqual([[g[1].text[:6] for g in grp] for grp in groups], [["- 장소: ", "- 참여대상"]])

    def test_single_line_is_not_changed(self):
        header = ET.fromstring(HEADER)
        root = section("- 공사명: 현수식 안내판 철거", "보통 문장")
        self.assertEqual(CL.align_colons(header, [root]), {"groups": 0, "stretched": 0})


if __name__ == '__main__':
    unittest.main()
