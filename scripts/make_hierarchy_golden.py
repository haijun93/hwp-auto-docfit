"""기존 타임머신 문단 위계 분류를 고정 Rust 골든 입력으로 내보낸다."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docfit_core.timemachine.content_search import ParagraphRecord, classify_paragraph_levels


def samples():
    rows = [
        ("2026. 11. 04. 시행계획 안내", "body", False),
        ("2026.11.04. 날짜 형식", "body", False),
        ("문서번호 제2026-123호", "body", False),
        ("제목: 골든 표본", "document_title", False),
        ("제1장 총칙", "chapter", False),
        ("제2장 적용 범위", "chapter", False),
        ("Ⅰ. 추진 배경", "section", False),
        ("Ⅱ. 추진 목적", "section", False),
        ("I. 영문 로마자", "section", False),
        ("□ 기본 원칙", "square", False),
        ("ㅁ 추가 원칙", "square", False),
        ("■ 검토 항목", "square", False),
        ("ㅇ 첫 항목", "circle", False),
        ("○ 둘째 항목", "circle", False),
        ("◦ 셋째 항목", "circle", False),
        ("- 세부 내용", "dash", False),
        ("– 긴 대시", "dash", False),
        ("— 전각 대시", "dash", False),
        ("* 참고 사항", "asterisk", False),
        ("** 중요 참고", "asterisk", False),
        ("※ 유의사항", "asterisk", False),
        ("• 추가 설명", "asterisk", False),
        ("· 가운데점 표식", "asterisk", False),
        ("1. 첫째", "body", False),
        ("2. 둘째", "body", False),
        ("가. 가나다 항목", "body", False),
        ("나. 이어지는 항목", "body", False),
        ("(1) 괄호 번호", "body", False),
        ("1) 괄호 없는 번호", "body", False),
        ("① 원문자 항목", "body", False),
        ("② 다음 원문자", "body", False),
        ("㉮ 한글 원문자", "body", False),
        ("붙임 1. 제출 서식", "body", False),
        ("붙임 2. 참고 자료", "body", False),
        ("참고자료: 본문 설명", "body", False),
        ("일반 본문 문장입니다.", "body", False),
        ("", "body", False),
        ("   ", "body", False),
        ("표 안의 □ 표식", "table_cell", True),
        ("표 셀의 제목 텍스트", "table_cell", True),
        ("날짜 2026. 11. 04. 본문 중간", "body", False),
        ("문서번호 1234-5678", "body", False),
        ("제3부 부록", "chapter", False),
        ("Chapter 4 Appendix", "chapter", False),
        ("Ⅲ. 세 번째 절", "section", False),
        ("□ 마무리 소제목", "square", False),
        ("ㅇ 마무리 본문 항목", "circle", False),
    ]
    return rows


def main():
    rows = samples()
    inputs = [ParagraphRecord(i, text, "", 0, table) for i, (text, _, table) in enumerate(rows)]
    classified = classify_paragraph_levels("golden-synthetic.hwpx", inputs)
    cases = []
    for (text, _, is_table_cell), record in zip(rows, classified):
        role = {"장": "chapter", "중제목": "section", "소제목": "topic", "본문": "body", "내용": "body", "부연설명": "asterisk"}.get(record.level, record.level)
        cases.append({"text": text, "is_table_cell": is_table_cell, "style_hint": None, "outline_level": -1, "expected": role})
    target = ROOT / "hierarchy" / "tests" / "golden.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"source": "docfit_core.timemachine.content_search.classify_paragraph_levels", "cases": cases}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(cases)} cases to {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
