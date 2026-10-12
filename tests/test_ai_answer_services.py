"""제미나이·챗GPT·클로드 답변 유형별 변환 시험과 무작위 입력 안전성 시험(알파, 2026-10-12)."""
from pathlib import Path
import random
import unittest

from docfit_core.ai_answer import ai_answer_to_labeled_text, ai_answer_to_outline_text, looks_like_ai_answer, parse_ai_answer
from docfit_core.labeled_text import looks_labeled, parse_labeled_text

FIX = Path(__file__).resolve().parent / 'fixtures'
ARTIFACTS = ('[cite', 'cite_start', 'oaicite', 'contentReference', '【', '†source', '**', '```', '| ---', '|---')


def load(name):
    return (FIX / f'ai_answer_{name}.txt').read_text(encoding='utf-8')


def lines(name):
    return ai_answer_to_labeled_text(load(name)).splitlines()


class ServiceStyleTest(unittest.TestCase):
    def test_all_services_are_detected_and_clean(self):
        for name in ('gemini', 'chatgpt', 'claude', 'mapo_pots'):
            raw = load(name)
            self.assertTrue(looks_like_ai_answer(raw), name)
            out = ai_answer_to_labeled_text(raw)
            self.assertTrue(looks_labeled(out), name)
            for artifact in ARTIFACTS:
                self.assertNotIn(artifact, out, f'{name}: {artifact}')
            self.assertEqual(len(parse_labeled_text(out)), len(parse_ai_answer(raw)), name)

    def test_gemini(self):
        out = lines('gemini')
        self.assertEqual(out[0], '개요: 공공기관 문서 자동화를 위한 도입 방안을 정리해 드립니다.')
        self.assertIn('네모: 추진 배경', out)
        self.assertIn('원: 현황: 수작업 서식 편집으로 업무 부담이 큽니다.', out)
        self.assertIn('원: 문제점', out)                      # 끝 콜론 뗌
        self.assertIn('바: 담당자 교체 시 노하우가 단절됩니다.', out)
        self.assertEqual(out.count('표: 구분 | 현행 | 개선'), 1)
        self.assertIn('원: 단계별 추진', out)
        self.assertIn('바: 1단계: 시범 적용', out)
        self.assertFalse(any('말씀해' in line for line in out))   # 대화체 맺음 제거

    def test_chatgpt(self):
        out = lines('chatgpt')
        self.assertEqual(out[0], '제목: 문서 서식 자동화 추진 계획')
        self.assertNotIn('📌', '\n'.join(out))
        self.assertIn('원: 준비 단계', out)                    # 번호 굵은 항목은 내용 목록(표제 아님)
        self.assertIn('바: 현황 조사', out)
        self.assertIn('당구: 원본 문서는 반드시 사본으로 시험하세요.', out)
        self.assertFalse(any('드릴까요' in line for line in out))

    def test_claude(self):
        out = lines('claude')
        self.assertEqual(out[0], '제목: 문서 서식 자동화 도입 검토')
        self.assertEqual(out[1].split(':')[0], '개요')
        self.assertIn('네모: 현황 분석', out)
        self.assertIn('바: 서식 불일치', out)
        self.assertIn('점: 글꼴이 문서마다 다름', out)
        self.assertIn('원: 세부 사항', out)                    # 2.1 번호 뗌
        self.assertIn('당구: 시범 운영 후 확대합니다.', out)
        self.assertIn('원: 도입을 권장합니다.', out)            # 결론 문장은 남기고 후속 제안 문장만 뗌
        self.assertFalse(any('알려주세요' in line for line in out))

    def test_outline_text_has_markers(self):
        text = ai_answer_to_outline_text(load('chatgpt'))
        self.assertIn('□ 추진 목적', text)
        self.assertIn('ㅇ 표준화: 기관 서식을 하나로 통일합니다.', text)

    def test_html_entities_and_breaks(self):
        out = ai_answer_to_labeled_text('## 제목\n- 가&amp;나<br>다음 줄\n- &lt;참고&gt; 사항\n')
        self.assertIn('원: 가&나', out)
        self.assertIn('<참고> 사항', out)

    def test_content_not_lost(self):
        # 인용 표식·기호를 뺀 모든 본문 단어가 결과에 남는다(맺음 문장 제외)
        for name in ('gemini', 'chatgpt', 'claude'):
            out = ai_answer_to_labeled_text(load(name))
            for word in ('검수', '시범', '표준', '한글 후처리', '2명', '3분'):
                if word in load(name):
                    self.assertIn(word, out, f'{name}: {word}')


class ScreenCopyTest(unittest.TestCase):
    """마크다운 기호 없이 화면에서 복사한 답변(기호만 한 줄, • ◦ 글머리, 번호 표제)."""

    def test_lone_bullet_lines_join_next_line(self):
        raw = '문서 자동화 도입 방안입니다.\n\n1. 추진 배경\n\n•\n현황: 수작업이 많습니다.\n•\n문제점: 검수 시간이 증가합니다.\n\n2. 기대 효과\n\n•\n시간 단축\n•\n오류 감소\n'
        self.assertTrue(looks_like_ai_answer(raw))
        out = ai_answer_to_labeled_text(raw).splitlines()
        self.assertEqual(out[0], '개요: 문서 자동화 도입 방안입니다.')
        self.assertIn('원: 현황: 수작업이 많습니다.', out)
        self.assertIn('원: 오류 감소', out)
        self.assertFalse(any('•' in line for line in out))

    def test_dot_bullets_with_nested_circle(self):
        raw = '추진 배경\n\n• 수작업 부담 증가\n• 서식 불일치\n   ◦ 글꼴 상이\n   ◦ 여백 상이\n\n기대 효과\n\n• 시간 단축\n'
        self.assertTrue(looks_like_ai_answer(raw))
        out = ai_answer_to_labeled_text(raw).splitlines()
        self.assertEqual(out[0], '네모: 추진 배경')
        self.assertIn('바: 글꼴 상이', out)


class RobustnessTest(unittest.TestCase):
    PIECES = ['# 제목', '## 소제목', '### 세부', '1. 항목', '  - 중첩', '\t* 탭', '- 글머리', '**굵게**', '**1. 굵은 번호**', '> 인용',
              '| a | b |', '|---|---|', '```', '---', '일반 문장입니다.', '', '[cite: 1]', '【1†source】', '*', '-', '#', '**', '|',
              '1.', '※ 참고', '​', '😀 이모지', '<br>', '&amp;', '더 필요하면 말씀해 주세요.']

    def test_random_input_never_raises_and_is_stable(self):
        rng = random.Random(20261012)
        for _ in range(400):
            raw = '\n'.join(rng.choice(self.PIECES) for _ in range(rng.randint(1, 25)))
            blocks = parse_ai_answer(raw)
            out = ai_answer_to_labeled_text(raw)
            ai_answer_to_outline_text(raw)
            looks_like_ai_answer(raw)
            for artifact in ('[cite', '†source'):
                self.assertNotIn(artifact, out)
            if out.strip():
                self.assertTrue(looks_labeled(out) or len(blocks) >= 1)
            self.assertEqual(ai_answer_to_labeled_text(raw), out)   # 결정적

    def test_edge_inputs(self):
        for raw in ('', '   \n\n', '#', '**', '- ', '|', '```\n```', '\x00﻿', '# ' + 'ㄱ' * 5000, '|' * 500,
                    '\n'.join('  ' * i + '- 깊이' for i in range(40)), '1. ' * 300):
            ai_answer_to_labeled_text(raw)
            ai_answer_to_outline_text(raw)

    def test_deep_nesting_is_capped_to_last_marker(self):
        out = ai_answer_to_outline_text('\n'.join('  ' * i + '- 깊이%d' % i for i in range(8)))
        self.assertTrue(out.splitlines()[-1].startswith('•'))


if __name__ == '__main__':
    unittest.main()
