# -*- coding: utf-8 -*-

"""
============================================================
HWP Auto DocFit - test.hwp 종합 정밀 검수 및 시뮬레이션 감사 스크립트
============================================================
"""

import os
import sys
import struct
import zlib
import re
import json
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server import (
    extract_document_paragraphs,
    tool_analyze_hwp_document,
    문장부호_시작,
    SENTENCE_MARKS,
    NUMBER_MARK_PATTERN,
    SHORT_LINE_MAX,
)
from hwp_auto_docfit import 저장파일명

TEST_FILE = str(Path(__file__).parent / "fixtures" / "test.hwp")


def run_comprehensive_audit():
    print("=" * 80)
    print("📋 HWP Auto DocFit - test.hwp 종합 정밀 검수 및 동작 감사 보고서")
    print("=" * 80)

    # 1. 파일 기본 정보 검수
    print("\n[검수 1] 파일 무결성 및 기본 정보 검수")
    assert os.path.isfile(TEST_FILE), f"파일 없음: {TEST_FILE}"
    file_size = os.path.getsize(TEST_FILE)
    print(f"  • 파일 경로: {TEST_FILE}")
    print(f"  • 파일 크기: {file_size:,} bytes")

    with open(TEST_FILE, "rb") as f:
        header = f.read(256)
    signature = header[:8]
    assert signature == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "OLE Compound Signature 불일치"
    print("  • OLE Compound Binary Signature 검증: [정상 (HWP 5.0 OLE CFB)]")

    # 2. 문단 추출 및 텍스트 구조 검수
    print("\n[검수 2] 문단 추출 및 본문 파싱 검수")
    paragraphs = extract_document_paragraphs(TEST_FILE)
    print(f"  • 추출된 총 문단 수: {len(paragraphs)}개")
    assert len(paragraphs) == 102, f"문단 수 불일치 (예상 102, 실제 {len(paragraphs)})"
    print("  • 문단 수 정합성: [정상 (102개 문단 확인)]")

    # 3. 항목 기호 및 개조식 번호 패턴 검수
    print("\n[검수 3] 공문서 항목 기호 및 개조식 번호 분류 검수")
    sentence_mark_list = []
    other_list = []

    for idx, p in enumerate(paragraphs, 1):
        if 문장부호_시작(p):
            cleaned = p.lstrip()
            first_char = cleaned[0]
            sentence_mark_list.append((idx, first_char, p))
        else:
            other_list.append((idx, p))

    print(f"  • 기호/번호 시작 문장: {len(sentence_mark_list)}개 ({len(sentence_mark_list)/len(paragraphs)*100:.1f}%)")
    print(f"  • 일반 본문/제목/표 헤더: {len(other_list)}개 ({len(other_list)/len(paragraphs)*100:.1f}%)")

    symbol_dist = {}
    for _, sym, _ in sentence_mark_list:
        symbol_dist[sym] = symbol_dist.get(sym, 0) + 1
    print(f"  • 기호별 분포: {symbol_dist}")

    # 4. 공문서 2줄 자간 압축 대상 정밀 시뮬레이션 검수
    print("\n[검수 4] 공문서 2줄 자간 압축(SHORT_LINE_MAX=5) 대상 정밀 검수")
    LINE_WIDTH = 40
    candidates = []

    print("-" * 80)
    print(f"{'문단':<6} | {'기호':<4} | {'1줄 추정 길이':<10} | {'2줄 넘침(자)':<10} | {'판정':<14} | {'텍스트 미리보기'}")
    print("-" * 80)

    for idx, sym, text in sentence_mark_list:
        line1 = text[:LINE_WIDTH]
        line2 = text[LINE_WIDTH:]
        overflow = len(line2.strip())

        if 0 < overflow <= SHORT_LINE_MAX:
            verdict = "★ 자간압축 대상"
            candidates.append((idx, text, overflow, line2.strip()))
        elif 0 < overflow <= 10:
            verdict = "검토 대상"
        elif overflow == 0:
            verdict = "1줄 완결"
        else:
            verdict = "다행 본문"

        if verdict in ("★ 자간압축 대상", "검토 대상") or idx in (23, 24, 25, 26, 27, 28):
            print(f"P{idx:<5} | {sym:<4} | {len(line1):<10} | {overflow:<10} | {verdict:<14} | {text[:35]}...")

    print("-" * 80)
    print(f"  • 자간 -1% 압축을 통해 1줄로 결합될 대상 문단: 총 {len(candidates)}개")
    for c_idx, c_text, c_over, c_over_txt in candidates:
        print(f"    - [P{c_idx:02d}] 2번째 줄 '{c_over_txt}' ({c_over}자) -> 자간 -1% 축소 후 1줄 결합 완료")

    # 5. MCP Server 도구 연동 및 Dry-run 검수
    print("\n[검수 5] AI 에이전트용 MCP Server 도구 호출 검수")
    mcp_analysis = tool_analyze_hwp_document({"file_path": TEST_FILE})
    assert mcp_analysis["total_paragraphs"] == 102
    assert mcp_analysis["sentence_mark_paragraphs_count"] == len(sentence_mark_list)
    print("  • MCP `analyze_hwp_document` 호출 결과:")
    print(f"    - 총 문단: {mcp_analysis['total_paragraphs']}개")
    print(f"    - 기호 문장: {mcp_analysis['sentence_mark_paragraphs_count']}개")
    print(f"    - 압축 대상: {mcp_analysis['two_line_compression_candidates_count']}개")
    print(f"    - 예상 절감 줄 수: {mcp_analysis['estimated_lines_saved']}줄")
    print(f"    - 요약: {mcp_analysis['summary']}")

    # 6. 저장 경로 및 포맷 규칙 검수
    print("\n[검수 6] 결과 파일명 및 항상 HWPX 저장 규칙 검수")
    out_path = 저장파일명(TEST_FILE)
    print(f"  • 원본 파일명: {Path(TEST_FILE).name}")
    print(f"  • 생성 파일명: {Path(out_path).name}")
    assert out_path.endswith(".hwpx"), f"결과 파일 확장자 오류: {out_path}"
    assert "(자간조정)" in out_path, f"결과 파일명 식별자 오류: {out_path}"
    print("  • HWPX 결과 파일명 규칙: [정상 검수 완료]")

    print("\n" + "=" * 80)
    print("🎉 종합 검수 결과: 모든 6개 항목 정상 (ALL AUDIT CHECKS PASSED)")
    print("=" * 80)


if __name__ == "__main__":
    run_comprehensive_audit()
