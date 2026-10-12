"""AI 답변(마크다운)을 복사한 그대로 개조식 항목기호 문서로 바꾼다(알파, 2026-10-12)."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

from docfit_core.ai_answer import (ai_answer_to_labeled_text, ai_answer_to_outline_text, looks_like_ai_answer,
                                   parse_ai_answer)
from docfit_core.labeled_text import looks_labeled

FIXTURE = Path(__file__).resolve().parent / 'fixtures' / 'ai_answer_mapo_pots.txt'


class DetectionTest(unittest.TestCase):
    def test_ai_markdown_is_detected_but_report_or_label_text_is_not(self):
        self.assertTrue(looks_like_ai_answer(FIXTURE.read_text(encoding='utf-8')))
        self.assertTrue(looks_like_ai_answer('## 제목\n* 항목 하나\n* 항목 둘\n'))
        self.assertFalse(looks_like_ai_answer('□ 추진 배경\n ㅇ 내용\n - 세부\n - 세부2'))
        self.assertFalse(looks_like_ai_answer('제목: 가\n네모: 나\n원: 다'))
        self.assertFalse(looks_like_ai_answer('그냥 한 문장입니다.'))
        self.assertFalse(looks_like_ai_answer(''))


class ConversionTest(unittest.TestCase):
    def test_numbered_sections_become_boxes_and_nested_bullets_follow_depth(self):
        out = ai_answer_to_outline_text(FIXTURE.read_text(encoding='utf-8')).split('\n')
        self.assertIn('□ 조경식재 및 시설물 철거 전문 업체 (마포구 등록업체)', out)
        self.assertIn('ㅇ 오월', out)
        self.assertIn('- 대표업종: 조경식재·시설물공사업', out)
        self.assertIn('□ 과업 추진 시 제안', out)                 # 번호 없는 짧은 제목 줄도 표제
        self.assertEqual(sum(line.startswith('□ ') for line in out), 4)
        self.assertFalse(any('*' in line or '](' in line for line in out))   # 마크다운 기호·링크 주소 없음
        # 표제 바로 아래 설명 문장은 ㅇ 항목, 표제와 한 줄로 이어 붙지 않는다.
        self.assertIn('ㅇ 화분 내 식재된 수목 분리, 화분 구조물 해체 및 현장 복구에 가장 적합한 전문건설업 면허 등록업체입니다.', out)

    def test_intro_paragraph_is_the_overview_box_in_label_form(self):
        labeled = ai_answer_to_labeled_text(FIXTURE.read_text(encoding='utf-8')).split('\n')
        self.assertTrue(labeled[0].startswith('개요: 마포구청 나라장터'))
        self.assertIn('원: 오피스가든', labeled)                          # 번호 표제 아래 업체명은 원(ㅇ)
        self.assertIn('바: 연락처: 1688-2052', labeled)
        self.assertTrue(looks_labeled('\n'.join(labeled)))

    def test_indent_width_does_not_matter_two_three_four_spaces_or_tab(self):
        template = '## 1. 업체\n* 오월\n{a}* 대표업종: 조경\n{b}* 세부: 상담\n* 윤스\n'
        expected = ['Ⅰ. 업체', '□ 오월', 'ㅇ 대표업종: 조경', '- 세부: 상담', '□ 윤스']   # 4단계 → Ⅰ. □ ㅇ -
        for a, b in (('  ', '    '), ('   ', '      '), ('    ', '        '), ('\t', '\t\t')):
            out = ai_answer_to_outline_text(template.format(a=a, b=b)).replace('\n\n', '\n').split('\n')
            self.assertEqual(out, expected, repr(a))

    def test_markdown_title_table_note_and_emoji(self):
        text = ('# 2026년 화분 철거 계획\n\n요약 문단입니다.\n\n## 1. 업체 현황\n| 업체 | 연락처 |\n|---|---|\n'
                '| 오월 | 02-6351-2002 |\n\n> 참고: 견적은 별도 확인 [1]\n\n- 수의계약 가능 🌿\n')
        blocks = parse_ai_answer(text)
        self.assertEqual([b['kind'] for b in blocks], ['title1', 'box', 'para', 'table', 'para', 'para'])
        self.assertEqual(blocks[0]['text'], '2026년 화분 철거 계획')
        self.assertEqual(blocks[3]['rows'], [['업체', '연락처'], ['오월', '02-6351-2002']])
        self.assertEqual((blocks[4]['marker'], blocks[4]['text']), ('※', '견적은 별도 확인'))
        self.assertEqual((blocks[5]['marker'], blocks[5]['text']), ('ㅇ', '수의계약 가능'))

    def test_numbered_steps_are_list_items_not_section_headings(self):
        out = ai_answer_to_outline_text('신청 절차는 다음과 같습니다.\n\n1. 서류를 준비합니다.\n2. 구청에 접수합니다.\n').split('\n')
        self.assertEqual(out, ['신청 절차는 다음과 같습니다.', 'ㅇ 서류를 준비합니다.', 'ㅇ 구청에 접수합니다.'])

    def test_bold_only_lines_are_headings(self):
        out = ai_answer_to_outline_text('**1. 업체 선정 기준**\n- 면허 보유\n- 관내 소재\n\n**2. 유의사항**\n- 폐기물 적법 처리\n')
        self.assertEqual(out.replace('\n\n', '\n').split('\n'),
                         ['□ 업체 선정 기준', 'ㅇ 면허 보유', 'ㅇ 관내 소재', '□ 유의사항', 'ㅇ 폐기물 적법 처리'])


class AppWiringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.g = cls.ns['AI답변_개조식_변환'].__globals__

    def test_flag_controls_conversion(self):
        fn = self.ns['AI답변_개조식_변환']
        raw = FIXTURE.read_text(encoding='utf-8')
        with patch.dict(self.g, {'알파_AI답변변환_사용': True}):
            text, changed = fn(raw)
            self.assertTrue(changed)
            self.assertIn('□ 조경식재', text)
            label, changed = fn(raw, 라벨형식=True)
            self.assertTrue(changed and looks_labeled(label))
        with patch.dict(self.g, {'알파_AI답변변환_사용': False}):
            self.assertEqual(fn(raw), (raw, False))
        self.assertEqual(fn('□ 이미 개조식\n ㅇ 내용\n'), ('□ 이미 개조식\n ㅇ 내용\n', False))

    def test_txt_file_is_converted_before_it_is_put_into_hwp(self):
        convert = self.ns['외부문서_hwpx로_변환']
        captured = []
        with patch.dict(convert.__globals__, {'텍스트파일_읽기': lambda path: FIXTURE.read_text(encoding='utf-8'),
                                              '텍스트_hwpx로_변환': lambda text, target: captured.append(text),
                                              '로그': lambda *a: None, '알파_AI답변변환_사용': True}):
            convert('answer.txt', '.txt', 'out.hwpx')
        self.assertEqual(len(captured), 1)
        self.assertIn('네모: 조경식재 및 시설물 철거 전문 업체', captured[0])
        self.assertTrue(looks_labeled(captured[0]))  # 저장된 제목·개요·문두기호 서식 적용 경로로 연결
        self.assertNotIn('**', captured[0])


    def test_md_file_without_images_uses_outline_conversion_even_with_engine(self):
        convert = self.ns['외부문서_hwpx로_변환']
        captured, engine = [], []
        with patch.dict(convert.__globals__, {'텍스트파일_읽기': lambda path: FIXTURE.read_text(encoding='utf-8'),
                                              '텍스트_hwpx로_변환': lambda text, target: captured.append(text),
                                              'generate_hwpx': lambda *a, **k: engine.append(a),
                                              '로그': lambda *a: None, '알파_AI답변변환_사용': True}):
            convert('answer.md', '.md', 'out.hwpx')
        self.assertEqual((len(captured), engine), (1, []))
        self.assertIn('네모: 조경식재 및 시설물 철거 전문 업체', captured[0])
        self.assertTrue(looks_labeled(captured[0]))  # 일반 목록이 아닌 프로필 기반 서식 블록으로 전달

    def test_md_file_with_image_still_goes_to_engine(self):
        convert = self.ns['외부문서_hwpx로_변환']
        captured, engine = [], []
        with patch.dict(convert.__globals__, {'텍스트파일_읽기': lambda path: '# 제목\n- 가\n- 나\n![그림](a.png)\n',
                                              '텍스트_hwpx로_변환': lambda text, target: captured.append(text),
                                              'generate_hwpx': lambda *a, **k: engine.append(a),
                                              '로그': lambda *a: None, '알파_AI답변변환_사용': True}):
            convert('a.md', '.md', 'out.hwpx')
        self.assertEqual((captured, len(engine)), ([], 1))


if __name__ == '__main__':
    unittest.main()
