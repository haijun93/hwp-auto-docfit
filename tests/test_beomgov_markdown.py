"""범정부오피스 내장 설명서에서 관찰한 문법을 독립 구현한 호환 시험."""
import unittest
from docfit_core.labeled_text import parse_labeled_text, looks_labeled, BEOMGOV_DIRECTIVE


class BeomgovMarkdownTests(unittest.TestCase):
    def test_all_colon_cells_empty_values_times_and_urls_are_preserved(self):
        blocks=parse_labeled_text('표 : 순번 : 이름 : 주소 : 비고\n표 : 1 : : 서울 : 14:00\n표 : 2 : 이름 : https://example.com/a : 추가 : 손실금지')
        self.assertEqual(blocks[0]['rows'],[['순번','이름','주소','비고'],['1','','서울','14:00'],
                                          ['2','이름','https://example.com/a','추가','손실금지']])
        self.assertEqual(parse_labeled_text(r'표: 내용\: 예시 : 다음')[0]['rows'],[['내용: 예시','다음']])

    def test_numbered_heading_tables_have_independent_counters(self):
        blocks=parse_labeled_text(BEOMGOV_DIRECTIVE+'\n소제목: 개요\n숫자소제목: 세부\n소제목로마: 총괄\n로마소제목: 다음\n표: 항목 : 값')
        self.assertEqual([b['rows'] for b in blocks[:4]],[[['1','개요']],[['2','세부']],[['Ⅰ','총괄']],[['Ⅱ','다음']]])
        self.assertEqual(blocks[4]['rows'],[['항목','값']])
        self.assertTrue(all(b.get('role')=='heading' for b in blocks[:4]))

    def test_opt_in_keeps_existing_subheading_behavior(self):
        self.assertEqual(parse_labeled_text('소제목: 개요')[0]['marker'],'□')
        self.assertEqual(parse_labeled_text('소제목: 개요',dialect='beomgov')[0]['kind'],'table')
        with self.assertRaises(ValueError):parse_labeled_text('',dialect='unknown')

    def test_explicit_single_table_is_routed_and_fences_remain_literal(self):
        self.assertTrue(looks_labeled('\ufeff\n'+BEOMGOV_DIRECTIVE+'\n표: A : B'))
        blocks=parse_labeled_text(BEOMGOV_DIRECTIVE+'\n```text\n소제목: 코드 예시\n```\n소제목: 실제 제목')
        self.assertEqual(blocks[0]['text'],'소제목: 코드 예시')
        self.assertEqual(blocks[1]['rows'],[['1','실제 제목']])

    def test_aliases_and_notes_remain_compatible(self):
        text='네모: 큰 내용\n사각형: 같은 계층\n원: 중간\n동그라미: 중간2\n바: 작은\n당구장: 유의\n주석1: 주석\n주석2: 둘\n상단박스: 요지\n참고: 자료'
        blocks=parse_labeled_text(text,dialect='beomgov')
        self.assertEqual([b.get('marker') for b in blocks[:8]],['□','□','ㅇ','ㅇ','-','※','*','**'])
        self.assertEqual([b['kind'] for b in blocks[8:]],['box','ref'])


if __name__=='__main__':unittest.main()
