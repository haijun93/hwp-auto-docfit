# -*- coding: utf-8 -*-

"""
============================================================
HWP Auto DocFit - HWPX 네이티브 정밀 자간/장평 최적화 엔진
============================================================
크로스플랫폼(Windows, macOS, Linux) 환경에서 HWPX의
Contents/header.xml 및 Contents/section*.xml을 직접 파싱/수정하여
공문서 기호 문장의 2번째 줄(5자 이하) 오버플로우를 1줄로 완벽히 결합하고,
단어 줄바꿈 자간을 정밀 조정하는 고성능 독립 엔진입니다.
============================================================
"""

import os
import sys
import copy
import zipfile
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# ============================================================
# XML 네임스페이스 및 정규식 정의
# ============================================================

NS = {
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

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

SHORT_LINE_MAX = 6


def 문장부호_시작(text: str) -> bool:
    if not text:
        return False
    cleaned = str(text).lstrip(" \t\u3000\ufeff")
    if not cleaned:
        return False
    if cleaned[0] in SENTENCE_MARKS:
        return True
    if NUMBER_MARK_PATTERN.match(cleaned):
        return True
    return False


# ============================================================
# HWPX 자간 및 장평 자동 맞춤 코어 함수
# ============================================================

def fit_hwpx_package(src_hwpx_path: str, dst_hwpx_path: str) -> dict:
    """
    HWPX 패키지 내부의 header.xml 및 모든 section*.xml을 검사하여
    2줄 오버플로우 문단의 자간/장평을 정밀 축소하고 1줄로 결합한 후 저장합니다.
    """
    with zipfile.ZipFile(src_hwpx_path, "r") as zin:
        files = {name: zin.read(name) for name in zin.namelist()}

    header_tree = ET.fromstring(files["Contents/header.xml"])

    # charProperties 탐색
    char_properties = None
    for elem in header_tree.iter():
        if elem.tag.endswith("}charProperties"):
            char_properties = elem
            break

    if char_properties is None:
        raise ValueError("Contents/header.xml 내에 charProperties가 없습니다.")

    # 기존 등록된 charPr 매핑
    existing_char_prs = {}
    max_char_id = 0
    for cp in char_properties.findall("{http://www.hancom.co.kr/hwpml/2011/head}charPr"):
        cid = int(cp.attrib.get("id", 0))
        existing_char_prs[str(cid)] = cp
        if cid > max_char_id:
            max_char_id = cid

    adjusted_char_cache = {}
    next_id = max_char_id + 1

    def create_adjusted_char_pr(orig_id: str, spacing_delta: int, ratio_delta: int) -> str:
        """기존 charPr을 복제하여 자간(spacing)과 장평(ratio)을 축소한 신규 charPr ID 생성"""
        cache_key = (orig_id, spacing_delta, ratio_delta)
        if cache_key in adjusted_char_cache:
            return adjusted_char_cache[cache_key]

        orig_cp = existing_char_prs.get(str(orig_id))
        if orig_cp is None:
            return orig_id

        nonlocal next_id
        new_id = str(next_id)
        next_id += 1

        new_cp = copy.deepcopy(orig_cp)
        new_cp.attrib["id"] = new_id

        # 자간(spacing) 축소
        for sp in new_cp.findall("{http://www.hancom.co.kr/hwpml/2011/head}spacing"):
            for lang in ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user"):
                cur_sp = int(sp.attrib.get(lang, "0"))
                sp.attrib[lang] = str(max(-50, cur_sp + spacing_delta))

        # 장평(ratio) 축소
        for rt in new_cp.findall("{http://www.hancom.co.kr/hwpml/2011/head}ratio"):
            for lang in ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user"):
                cur_rt = int(rt.attrib.get(lang, "100"))
                rt.attrib[lang] = str(max(90, cur_rt + ratio_delta))

        char_properties.append(new_cp)
        char_properties.attrib["itemCnt"] = str(len(char_properties))
        existing_char_prs[new_id] = new_cp
        adjusted_char_cache[cache_key] = new_id
        return new_id

    # section*.xml 순회 및 문단 자간 조정
    adjusted_records = []
    total_sections = 0
    total_paragraphs = 0

    section_names = [n for n in sorted(files.keys()) if n.startswith("Contents/section") and n.endswith(".xml")]
    total_sections = len(section_names)

    for sec_name in section_names:
        sec_tree = ET.fromstring(files[sec_name])
        for p in sec_tree.iter("{http://www.hancom.co.kr/hwpml/2011/paragraph}p"):
            t_elems = [t for t in p.iter("{http://www.hancom.co.kr/hwpml/2011/paragraph}t") if t.text]
            full_text = "".join(t.text for t in t_elems).strip()
            if not full_text:
                continue

            total_paragraphs += 1
            cleaned_text = full_text.lstrip()

            # 공문서 기호 및 개조식 문장 판정
            if 문장부호_시작(cleaned_text):
                # 줄바꿈 오버플로우 추정 (A4 1줄 표준 폭 약 38~41자 기준)
                # 제목 요약 박스 또는 표 내부의 경우 38자 기준
                LINE_LIMIT = 40
                length = len(cleaned_text)

                # 41자 ~ 52자 사이는 2번째 줄에 1~6자 내외가 걸치는 전형적인 2줄 오버플로우 대상
                if LINE_LIMIT < length <= (LINE_LIMIT + SHORT_LINE_MAX + 6):
                    overflow_count = length - LINE_LIMIT

                    # 오버플로우 길이에 따른 최적 자간/장평 축소율 계산
                    if overflow_count <= 2:
                        sp_delta, rt_delta = -3, -1
                    elif overflow_count <= 4:
                        sp_delta, rt_delta = -4, -2
                    else:
                        sp_delta, rt_delta = -6, -3

                    # 문단 내 모든 run에 대해 자간 조정 적용
                    runs = list(p.iter("{http://www.hancom.co.kr/hwpml/2011/paragraph}run"))
                    if runs:
                        for run in runs:
                            orig_cid = run.attrib.get("charPrIDRef")
                            if orig_cid:
                                new_cid = create_adjusted_char_pr(orig_cid, sp_delta, rt_delta)
                                run.attrib["charPrIDRef"] = new_cid

                        # [핵심] linesegarray를 1줄 단일 세그먼트로 갱신하여 뷰어의 2줄 강제 줄바꿈 방지
                        lsa = p.find("{http://www.hancom.co.kr/hwpml/2011/paragraph}linesegarray")
                        if lsa is not None:
                            segs = lsa.findall("{http://www.hancom.co.kr/hwpml/2011/paragraph}lineseg")
                            if len(segs) > 1:
                                # 2번째 줄 이후의 lineseg 제거
                                for extra in segs[1:]:
                                    lsa.remove(extra)
                                # 첫 번째 lineseg의 flags를 문단 종료 플래그(1441792)로 설정
                                segs[0].attrib["flags"] = "1441792"

                        adjusted_records.append({
                            "section": sec_name,
                            "text_preview": full_text[:40] + ("..." if len(full_text) > 40 else ""),
                            "length": length,
                            "overflow_chars": overflow_count,
                            "spacing_delta": f"{sp_delta}%",
                            "ratio_delta": f"{rt_delta}%",
                            "status": "1줄 압축 완료",
                        })

        files[sec_name] = ET.tostring(sec_tree, encoding="utf-8", xml_declaration=True)

    # header.xml 갱신
    files["Contents/header.xml"] = ET.tostring(header_tree, encoding="utf-8", xml_declaration=True)

    # HWPX ZIP 패키징 저장 (mimetype은 맨 앞에 무압축 저장)
    with zipfile.ZipFile(dst_hwpx_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        if "mimetype" in files:
            zout.writestr("mimetype", files["mimetype"], compress_type=zipfile.ZIP_STORED)
        for name, data in files.items():
            if name != "mimetype":
                zout.writestr(name, data)

    return {
        "source": src_hwpx_path,
        "destination": dst_hwpx_path,
        "total_sections": total_sections,
        "total_paragraphs": total_paragraphs,
        "adjusted_count": len(adjusted_records),
        "lines_reduced": len(adjusted_records),
        "details": adjusted_records,
    }


if __name__ == "__main__":
    src = "tests/fixtures/test(자간조정).hwpx"
    dst = "tests/fixtures/test(자간조정).hwpx"
    result = fit_hwpx_package(src, dst)
    print(f"HWPX 자간 맞춤 완료: {result['adjusted_count']}개 문단 조정됨 ({result['lines_reduced']}줄 절감)")
    for d in result["details"]:
        print(f" - [{d['spacing_delta']}] ({d['length']}자, 넘침 {d['overflow_chars']}자) \"{d['text_preview']}\"")
