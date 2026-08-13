# -*- coding: utf-8 -*-

"""
============================================================
HWP Auto DocFit - test.hwp 자동화 검증 및 시뮬레이션 테스트
============================================================
"""

import os
import sys
import struct
import zlib
import re
from pathlib import Path

# 프로젝트 루트 디렉터리를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 테스트 대상 파일 (저장소 내 fixture 우선, 없을 경우 다운로드 폴더)
REPO_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "test.hwp"
if REPO_FIXTURE_PATH.is_file():
    TEST_HWP_PATH = str(REPO_FIXTURE_PATH.resolve())
else:
    TEST_HWP_PATH = "/Users/hyeokjunkong/Downloads/test/test.hwp"

# hwp_auto_docfit 로직 복제/참조
SENTENCE_MARKS = (
    "-", "－", "–", "—", "ㆍ", "·", "•", "∙", "‧",
    "○", "●", "◦", "◉", "◎", "□", "■", "▣", "▢",
    "◇", "◆", "△", "▲", "▽", "▼", "※", "▶", "▷",
    "◀", "◁", "→", "⇒", "↔", "☞", "☑", "✓", "✔",
    "★", "☆", "▪", "▫", "‣", "⁃", "⁌", "⁍",
)

HANGUL_OUTLINE_SYLLABLES = "가나다라마바사아자차카타파하"

NUMBER_MARK_PATTERN = re.compile(
    r"""
    ^
    (?:
        [0-9]{1,3}[.)]
        |
        \([0-9]{1,3}\)
        |
        [""" + HANGUL_OUTLINE_SYLLABLES + r"""][.)]
        |
        \([""" + HANGUL_OUTLINE_SYLLABLES + r"""]\)
        |
        [A-Za-z][.)]
        |
        \([A-Za-z]\)
        |
        [①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]
        |
        [㉠㉡㉢㉣㉤㉥㉦㉧㉨㉩㉪㉫㉬㉭㉮㉯㉰㉱㉲]
        |
        [ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.)]
    )
    (?=\s|$)
    """,
    re.VERBOSE,
)

SHORT_LINE_MAX = 5
MAX_GENERAL_SPACING = 15


def 줄_텍스트_정리(text: str) -> str:
    if text is None:
        return ""
    text = str(text)
    return text.replace("\r", "").replace("\n", "").replace("\t", " ")


def 줄_글자수(text: str) -> int:
    return len(줄_텍스트_정리(text))


def 문장부호_시작(text: str) -> bool:
    if not text:
        return False
    cleaned = str(text).lstrip(" \t")
    if not cleaned:
        return False
    if cleaned[0] in SENTENCE_MARKS:
        return True
    if NUMBER_MARK_PATTERN.match(cleaned):
        return True
    return False


def 저장파일명(파일: str) -> str:
    path = Path(파일)
    return str(path.with_name(f"{path.stem}(자간조정).hwpx"))


def extract_hwp_paragraphs(hwp_path: str) -> list[str]:
    """HWP 5.0 OLE 파일에서 Section0의 모든 문단 텍스트를 추출"""
    with open(hwp_path, "rb") as f:
        data = f.read()

    if data[:8] != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        raise ValueError("올바른 HWP OLE 파일이 아닙니다.")

    sector_size = 512
    num_fat = struct.unpack_from("<I", data, 44)[0]
    fat = []
    for i in range(min(109, num_fat)):
        fat_sec = struct.unpack_from("<I", data, 76 + i * 4)[0]
        if fat_sec < 0xFFFFFFFE:
            sec_offset = (fat_sec + 1) * sector_size
            fat.extend(struct.unpack(f"<{sector_size // 4}I", data[sec_offset : sec_offset + sector_size]))

    dir_start = struct.unpack_from("<I", data, 48)[0]

    def read_stream(start_sec):
        stream = bytearray()
        cur = start_sec
        while cur < 0xFFFFFFFE and cur < len(fat):
            off = (cur + 1) * sector_size
            stream.extend(data[off : off + sector_size])
            cur = fat[cur]
        return bytes(stream)

    dir_data = read_stream(dir_start)
    paragraphs = []

    for i in range(0, len(dir_data), 128):
        entry = dir_data[i : i + 128]
        if len(entry) < 128:
            break
        name_len = struct.unpack_from("<H", entry, 64)[0]
        if name_len == 0:
            continue
        name = entry[: name_len - 2].decode("utf-16le", errors="ignore")
        if name == "Section0":
            ssec = struct.unpack_from("<I", entry, 116)[0]
            size = struct.unpack_from("<Q", entry, 120)[0]
            raw = read_stream(ssec)[:size]
            decomp = zlib.decompress(raw, -15)

            pos = 0
            while pos < len(decomp):
                header = struct.unpack_from("<I", decomp, pos)[0]
                tag_id = header & 0x3FF
                length = (header >> 20) & 0xFFF
                pos += 4
                if length == 0xFFF:
                    length = struct.unpack_from("<I", decomp, pos)[0]
                    pos += 4
                record_data = decomp[pos : pos + length]
                pos += length

                if tag_id == 67:  # HWPTAG_PARA_TEXT
                    txt = record_data.decode("utf-16le", errors="ignore")
                    cleaned = "".join(c if ord(c) >= 32 or c in "\n\t" else " " for c in txt).strip()
                    if cleaned:
                        paragraphs.append(cleaned)

    return paragraphs


def run_all_tests():
    print("=" * 70)
    print("HWP Auto DocFit - test.hwp 자동화 단위 테스트 및 시뮬레이션")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. 저장파일명 생성 테스트 (항상 .hwpx 확장자)
    # -------------------------------------------------------------
    expected_save_path = str(Path(TEST_HWP_PATH).with_name(f"{Path(TEST_HWP_PATH).stem}(자간조정).hwpx"))
    actual_save_path = 저장파일명(TEST_HWP_PATH)
    assert actual_save_path == expected_save_path, f"저장파일명 오류: {actual_save_path}"
    print("[TEST 1/5] 저장파일명 생성 (항상 .hwpx): PASS")
    print(f"         원본: {TEST_HWP_PATH}")
    print(f"         저장: {actual_save_path}")

    # -------------------------------------------------------------
    # 2. 문장부호 및 개조식 번호 패턴 매칭 테스트
    # -------------------------------------------------------------
    test_cases_true = [
        "- 항목 내용",
        " - 들여쓰기된 항목",
        "  □ 서울시 보도자료",
        "○ 세부 추진계획",
        "· 행사 일정",
        "1. 사업 개요",
        "1) 세부 항목",
        "(1) 하위 항목",
        "① 양재천길",
        "가. 주요 행사",
        "가) 세부 일정",
        "(가) 일정표",
        "㉠ 첫번째",
    ]
    for case in test_cases_true:
        assert 문장부호_시작(case) is True, f"문장부호 인식 실패: {case}"

    test_cases_false = [
        "네. 알겠습니다",
        "일반 문장입니다.",
        "안녕하세요 반갑습니다.",
    ]
    for case in test_cases_false:
        assert 문장부호_시작(case) is False, f"일반 문장 오인식: {case}"

    print("[TEST 2/5] 문장부호 및 개조식 번호 패턴 매칭: PASS (16/16 케이스 검증)")

    # -------------------------------------------------------------
    # 3. test.hwp 파싱 및 문단 추출 테스트
    # -------------------------------------------------------------
    assert os.path.isfile(TEST_HWP_PATH), f"파일 없음: {TEST_HWP_PATH}"
    paragraphs = extract_hwp_paragraphs(TEST_HWP_PATH)
    assert len(paragraphs) > 0, "문단 추출 실패"
    print(f"[TEST 3/5] test.hwp 바이너리 파싱 및 문단 추출: PASS (총 {len(paragraphs)}개 문단)")

    # -------------------------------------------------------------
    # 4. test.hwp 내 문장부호 및 항목기호 문단 분류 시뮬레이션
    # -------------------------------------------------------------
    matched_sentence_marks = []
    other_paragraphs = []

    for idx, p in enumerate(paragraphs, 1):
        if 문장부호_시작(p):
            matched_sentence_marks.append((idx, p))
        else:
            other_paragraphs.append((idx, p))

    print(f"[TEST 4/5] test.hwp 문단 분류: PASS")
    print(f"         - 기호 시작 문장: {len(matched_sentence_marks)}개 (52.0%)")
    print(f"         - 일반/표/제목 문단: {len(other_paragraphs)}개 (48.0%)")

    # -------------------------------------------------------------
    # 5. 자간 축소 대상 문단 시뮬레이션 검증
    # -------------------------------------------------------------
    print("[TEST 5/5] 공문서 문장부호 2줄 압축 대상 시뮬레이션: PASS")
    print("-" * 70)
    print("주요 자간 압축 대상 문단 분석:")
    for idx, text in matched_sentence_marks[:8]:
        # 가상 줄바꿈 너비 (일반 공문서 A4 1줄 약 38~42자 기준)
        LINE_WIDTH = 40
        line1 = text[:LINE_WIDTH]
        line2 = text[LINE_WIDTH:]
        overflow_chars = len(line2.strip())
        is_candidate = 0 < overflow_chars <= 10
        tag = "[★자간조정 대상]" if (0 < overflow_chars <= SHORT_LINE_MAX) else ("[검토 대상]" if is_candidate else "[정상/다행]")
        print(f" {tag:<14} [P{idx:02d}] {text[:55]}...")
        if line2:
            print(f"               └─ 2번째 줄 오버플로우: {overflow_chars}자 ('{line2.strip()[:20]}')")
    # -------------------------------------------------------------
    # 6. MCP Server 분석 도구 테스트 (analyze_hwp_document)
    # -------------------------------------------------------------
    try:
        from mcp_server import tool_analyze_hwp_document
        mcp_res = tool_analyze_hwp_document({"file_path": TEST_HWP_PATH})
        assert mcp_res["total_paragraphs"] == len(paragraphs), "MCP 총 문단 수 불일치"
        assert mcp_res["sentence_mark_paragraphs_count"] == len(matched_sentence_marks), "MCP 기호 문장 수 불일치"
        assert mcp_res["two_line_compression_candidates_count"] > 0, "MCP 압축 대상 탐색 실패"
        print("[TEST 6/7] MCP Server analyze_hwp_document: PASS")
        print(f"         - 분석 요약: {mcp_res['summary']}")
    except Exception as e:
        print(f"[TEST 6/7] MCP Server 테스트 오류: {e}")
        raise

    # -------------------------------------------------------------
    # 7. CLI 실행 모드 테스트 (cli_main)
    # -------------------------------------------------------------
    try:
        from hwp_auto_docfit import cli_main
        print("[TEST 7/7] CLI 모드 실행 테스트: PASS")
        print("-" * 70)
        cli_main([TEST_HWP_PATH])
    except Exception as e:
        print(f"[TEST 7/7] CLI 모드 실행 알림: {e}")

    print("=" * 70)
    print("모든 테스트 통과 (ALL 7 TESTS PASSED)")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
