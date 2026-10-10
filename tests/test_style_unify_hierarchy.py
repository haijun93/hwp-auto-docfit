"""서식통일 고도화: 문서 체계(계층) 판별, 표지 제외, 글자색·음영, 번호 계열 묶기."""
from contextlib import contextmanager
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from docfit_core.style_unify import (
    attachment_heading, dominant, hierarchy_levels, looks_like_cover, marker_class,
    style_change_points, unify_marker, vocabulary_fallback,
)

PUA_1, PUA_5 = "\U000F02B1", "\U000F02B5"


class MarkerAndHierarchyTests(unittest.TestCase):
    def test_numbered_series_share_one_group(self):
        self.assertEqual(unify_marker("1. 제목")[0], "1.")
        self.assertEqual(unify_marker("12. 제목")[0], "1.")
        self.assertEqual(unify_marker("Ⅱ. 중점 추진과제")[:2], ("Ⅰ", "중제목"))
        self.assertEqual(unify_marker("② 원문자")[0], "①")
        self.assertEqual(marker_class("가"), "가.")

    def test_heading_markers_that_leading_marker_misses(self):
        # 번호 뒤 공백 없이 낫표가 붙은 제목, 한/글 PUA 원문자, 가타카나 가운데점.
        self.assertEqual(unify_marker("1.「마포 교육의 달」 참여자 모집")[:2], ("1.", "소제목"))
        self.assertEqual(unify_marker(f"{PUA_5} 교육 분야 글로벌 이니셔티브")[:2], (PUA_1, "중제목"))
        self.assertEqual(unify_marker("・ 기관별 현장 방문")[:2], ("•", "부연설명"))

    def test_decimals_and_dates_are_not_markers(self):
        for text in ("1.5배 증가", "2026. 10. 12.(월)", "3.1운동 기념"):
            self.assertEqual(unify_marker(text), ("", "", ""), text)

    def test_hierarchy_order_follows_nesting(self):
        sequence = ["Ⅰ", PUA_1, "□", "ㅇ", "*", "ㅇ", "-", PUA_1, "□", "ㅇ",
                    "Ⅰ", PUA_1, "1.", "□", "ㅇ", "※"]
        levels = hierarchy_levels(sequence)
        # □가 절 제목 바로 아래에도 나오지만 '1.' 아래에 놓인 적이 있으므로 '1.'이 상위다.
        self.assertEqual(levels[:5], ["Ⅰ", PUA_1, "1.", "□", "ㅇ"])
        self.assertLess(levels.index("ㅇ"), levels.index("-"))

    def test_cover_needs_large_centered_title_and_little_body_text(self):
        cover = [("교육부 업무보고", 3200, True, False), ("2025. 12. 12.", 2400, True, False)]
        self.assertTrue(looks_like_cover(cover, 1500))
        # 제목은 크지만 첫 쪽 대부분이 본문 문장이면 표지가 아니다.
        report = [("2026년 업무계획", 2000, True, False)] + [
            ("ㅇ 본문 문장이 이어지는 일반 보고서 첫 쪽입니다", 1500, False, True)] * 3
        self.assertFalse(looks_like_cover(report, 1500))
        # 가운데 정렬이 아니거나 본문보다 조금만 크면 표지가 아니다.
        self.assertFalse(looks_like_cover([("제목", 3200, False, False)], 1500))
        self.assertFalse(looks_like_cover([("제목", 1700, True, False)], 1500))

    def test_vocabulary_fallback_only_for_values_used_elsewhere(self):
        values = ["한컴돋움"] * 6 + ["한양중고딕"] * 4 + ["HY중고딕"] * 2
        self.assertEqual(vocabulary_fallback(values, {"한컴돋움", "휴먼명조"}), "한컴돋움")
        self.assertIsNone(vocabulary_fallback(values, {"휴먼명조"}))
        self.assertIsNone(vocabulary_fallback(["가", "가", "나", "나"], {"가", "나"}))

    def test_attachment_headings(self):
        for text, name in (("[붙임] 점검내역(상세)", "붙임"), ("붙임 2", "붙임 2"),
                           ("별첨 1. 세부 계획", "별첨 1"), ("<참고 1> 추진 경과", "참고 1")):
            self.assertEqual(attachment_heading(text), name, text)
        for text in ("※ 참고: 예산 포함", "참고로 추진함", "붙임성 좋은 사업", "ㅇ 붙임 참조"):
            self.assertEqual(attachment_heading(text), "", text)

    def test_style_change_point_needs_several_levels_switching_together(self):
        body = [(i, ("휴먼명조", 1500)) for i in range(0, 40, 2)]
        annex = [(i, ("한컴돋움", 1300)) for i in range(40, 70, 2)]
        dash_body = [(i, ("휴먼명조", 1400)) for i in range(1, 40, 2)]
        dash_annex = [(i, ("한컴돋움", 1200)) for i in range(41, 70, 2)]
        points = style_change_points({"ㅇ": body + annex, "-": dash_body + dash_annex})
        self.assertEqual(points, [40])
        # 한 계층만 바뀌면 체계가 아니라 예외(또는 계층 고유 변화)로 본다.
        self.assertEqual(style_change_points({"ㅇ": body + annex, "-": dash_body}), [])
        # 몇 문장만 다른 서식이면(붙여넣은 구간) 경계가 아니다.
        pasted = body[:10] + [(21, ("한컴돋움", 1000)), (23, ("한컴돋움", 1000))] + body[10:]
        self.assertEqual(style_change_points({"ㅇ": pasted, "-": dash_body}), [])
        # 취합 문서의 한 부서 구간(전체의 20% 미만)은 체계가 아니라 통일할 예외다.
        long_body = [(i, ("휴먼명조", 1500)) for i in range(0, 200, 2)]
        dept = [(i, ("한컴돋움", 1300)) for i in range(200, 212, 2)]
        long_dash = [(i, ("휴먼명조", 1400)) for i in range(1, 200, 2)]
        dept_dash = [(i, ("한컴돋움", 1200)) for i in range(201, 213, 2)]
        self.assertEqual(style_change_points({"ㅇ": long_body + dept, "-": long_dash + dept_dash}), [])

    def test_dominant_requires_clear_majority(self):
        self.assertEqual(dominant([("#000000", 30), ("#0000FF", 5)]), "#000000")
        self.assertIsNone(dominant([("#000000", 10), ("#0000FF", 10)]))


class UnifyEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    @contextmanager
    def document(self, paragraphs, *, pages=None, cover=False, position_text=None, boundaries=None):
        """paragraphs: (문단 텍스트, 글꼴, 크기, 글자색) 목록."""
        fn = self.ns['서식통일_전체_적용']
        index = [0]
        texts = [item[0] for item in paragraphs]

        def shape(pos, text):
            i = pos[1]
            _, font, size, color = paragraphs[i][:4]
            end = (0, i, len(text))
            return ((font, size, [(pos, end, (font, size), len(text), False)], {
                'marker_bold': False, 'label_bold': None, 'hanging_indent': False,
                'marker_bold_runs': [], 'label_bold_runs': [], 'parenthetical_size_runs': [],
                'red_marked': False, 'color': color, 'shade': '없음',
                'color_runs': [(pos, end, color, len(text))],
                'shade_runs': [(pos, end, '없음', len(text))],
                **(paragraphs[i][4] if len(paragraphs[i]) > 4 else {}),
            }), pos, end)

        def advance():
            index[0] += 1
            return index[0] < len(paragraphs)

        com = Mock()
        com.GetPos.side_effect = lambda: (0, index[0], 0)

        def command(name):
            if name == 'MoveDocBegin':
                index[0] = 0

        writes, marks, colors, selection = Mock(), Mock(), Mock(), Mock()
        with patch.dict(fn.__globals__, {
            'hwp': com, 'hwp_run': command, '중단_요청됨': lambda: False,
            '쪽범위_실제': None, '쪽범위_안인가': lambda pos: True,
            '현재문단_텍스트': lambda: texts[index[0]], '다음_문단으로_진행': advance,
            '서식통일_표본': shape, '_서식통일_문서대표프로필': {},
            '_서식통일_대표값_검토콜백': None,
            '_서식통일_위치텍스트': position_text or (lambda pos, text: text),
            '_서식통일_제목표_표본': lambda 제외=(): [],
            '_서식통일_체계경계': lambda 표본, 위치: list(boundaries or []),
            '현재_페이지번호': (lambda: pages[index[0]]) if pages else (lambda: None),
            '_서식통일_표지인가': lambda 문단, 크기: cover,
            '_서식통일_내어쓰기_상태': lambda pos, text: False,
            '문자모양_적용_현재선택': writes, '_서식통일_미확정_빨간표시': marks,
            '_서식통일_색_적용': colors,
            '_서식통일_문단자간_조정': Mock(return_value=True),
            '서식통일_보류자간_재조정': Mock(return_value=True),
            '단어모드_범위선택': selection, '문단_내어쓰기_적용': Mock(),
            '로그': Mock(), '진단로그': Mock(),
        }):
            yield fn, writes, marks, colors, selection

    def test_numbered_headings_form_one_group_instead_of_red_marks(self):
        paragraphs = [('1. 첫째 제목', 'HY견고딕', 1700, '#000000'),
                      ('ㅇ 본문', '한컴돋움', 1500, '#000000'),
                      ('2. 둘째 제목', 'HY견고딕', 1700, '#000000'),
                      ('ㅇ 본문', '한컴돋움', 1500, '#000000'),
                      ('3. 셋째 제목', 'HY견고딕', 1700, '#000000'),
                      ('ㅇ 본문', '한컴돋움', 1500, '#000000')]
        with self.document(paragraphs) as (fn, writes, marks, colors, _):
            self.assertTrue(fn())
            writes.assert_not_called()
            marks.assert_not_called()
            colors.assert_not_called()

    def test_sentence_color_outlier_is_recolored_to_representative(self):
        paragraphs = [(f'ㅇ 본문 {i}', '한컴돋움', 1500, '#000000') for i in range(4)]
        paragraphs.append(('ㅇ 보라색 문장', '한컴돋움', 1500, '#800080'))
        with self.document(paragraphs) as (fn, writes, marks, colors, selection):
            self.assertTrue(fn())
            colors.assert_called_once_with('TextColor', '#000000')
            self.assertEqual(selection.call_args.args, ((0, 4, 0), (0, 4, 8)))
            writes.assert_not_called()
            marks.assert_not_called()

    def test_markers_hidden_by_fixed_width_spaces_are_sampled(self):
        # 한/글 GetText가 고정폭 빈칸을 빼서 'ㅇ본문'으로 돌려줘도 원문으로 문두기호를 찾는다.
        paragraphs = [(f'ㅇ본문{i}', '함초롬바탕', 1500, '#000000') for i in range(3)]
        paragraphs.append(('ㅇ붙여넣은문장', '한컴돋움', 1000, '#000000'))
        with self.document(paragraphs,
                           position_text=lambda pos, text: text.replace('ㅇ', 'ㅇ  ', 1)) as (
                fn, writes, marks, _, _):
            self.assertTrue(fn())
            self.assertEqual({call.kwargs.get('폰트') or call.kwargs.get('크기_pt')
                              for call in writes.call_args_list}, {15.0, '함초롬바탕'})
            marks.assert_not_called()

    def test_cover_page_sentences_are_excluded(self):
        paragraphs = [('ㅇ 표지 안내', '휴먼명조', 2400, '#000000')]
        paragraphs += [(f'ㅇ 본문 {i}', '한컴돋움', 1500, '#000000') for i in range(3)]
        with self.document(paragraphs, pages=[1, 2, 2, 2], cover=True) as (fn, writes, marks, _, _):
            self.assertTrue(fn())
            writes.assert_not_called()
            marks.assert_not_called()
        with self.document(paragraphs, pages=[1, 2, 2, 2], cover=False) as (fn, writes, _, _, _):
            self.assertTrue(fn())
            self.assertTrue(writes.called)

    def test_mixed_hanging_on_one_line_items_is_not_marked_red(self):
        # 실측(정책회의 자료): 한 줄 '-' 항목의 내어쓰기가 57:39로 갈려 103문장이 빨갛게 표시됐다.
        paragraphs = [(f'- 항목 {i}', '휴먼명조', 1400, '#000000',
                       {'hanging_indent': i % 2 == 0, 'line_count': 1}) for i in range(8)]
        with self.document(paragraphs) as (fn, writes, marks, _, _):
            self.assertTrue(fn())
            writes.assert_not_called()
            marks.assert_not_called()

    def test_each_format_system_keeps_its_own_representative(self):
        # 본문(휴먼명조 15pt)과 붙임(한컴돋움 13pt)은 서로 다른 체계다. 붙임 안의 예외만 고친다.
        paragraphs = [(f'ㅇ 본문 {i}', '휴먼명조', 1500, '#000000') for i in range(5)]
        paragraphs += [(f'ㅇ 붙임 {i}', '한컴돋움', 1300, '#000000') for i in range(4)]
        paragraphs.append(('ㅇ 붙임 예외', '굴림', 1300, '#000000'))
        with self.document(paragraphs, boundaries=[(5, '붙임')]) as (fn, writes, marks, _, selection):
            self.assertTrue(fn())
            self.assertEqual([call.kwargs.get('폰트') for call in writes.call_args_list], ['한컴돋움'])
            self.assertEqual(selection.call_args.args[0], (0, 9, 0))
            marks.assert_not_called()
        # 경계를 모르면 5:4로 갈려 대표 글꼴을 정할 수 없으므로 고치지 않고 빨간 표시한다.
        with self.document(paragraphs) as (fn, writes, marks, _, _):
            self.assertTrue(fn())
            self.assertNotIn('휴먼명조', [call.kwargs.get('폰트') for call in writes.call_args_list])
            self.assertTrue(marks.called)

    def test_small_region_borrows_document_representative(self):
        # 붙임 영역에 ㅇ 문장이 하나뿐이면 문서 전체 ㅇ 대표값과 비교한다.
        paragraphs = [(f'ㅇ 본문 {i}', '휴먼명조', 1500, '#000000') for i in range(5)]
        paragraphs.append(('ㅇ 붙임 하나', '굴림', 1500, '#000000'))
        with self.document(paragraphs, boundaries=[(5, '붙임')]) as (fn, writes, marks, _, _):
            self.assertTrue(fn())
            self.assertEqual([call.kwargs.get('폰트') for call in writes.call_args_list], ['휴먼명조'])
            marks.assert_not_called()

    def test_split_font_group_borrows_font_used_as_representative_elsewhere(self):
        paragraphs = [(f'ㅇ 본문 {i}', '한컴돋움', 1500, '#000000') for i in range(3)]
        # ※ 글꼴이 3:2:1로 갈려 엄격한 다수(60%)에 못 미친다.
        fonts = ['한컴돋움', '한양중고딕', '한컴돋움', 'HY중고딕', '한양중고딕', '한컴돋움']
        paragraphs += [(f'※ 참고 {i}', font, 1300, '#000000') for i, font in enumerate(fonts)]
        with self.document(paragraphs) as (fn, writes, marks, _, _):
            self.assertTrue(fn())
            written = [call.kwargs.get('폰트') for call in writes.call_args_list]
            self.assertEqual(written, ['한컴돋움'] * 3)
            marks.assert_not_called()


if __name__ == '__main__':
    unittest.main()
