"""본문 수치와 표 수치의 존재 여부 대조(최종검수, 읽기 전용).

TODO.md 4순위. 본문이 표를 설명하는 곳에서 쓴 수치가 그 표에 똑같은 숫자로 있는지
본다(정확한 대응 관계 검증이 아니라 '표와 어긋난 숫자는 아닌지'의 1차 점검).

실측(2026-09-25, 실전 테스트 결과 22개 문서): 문서 전체의 모든 본문 수치를 표와
대조하면 보도자료·업무계획에서 본문의 서술용 수치가 대부분 걸렸다(예: 45개 중 34개).
그래서 대조 범위를 좁힌다.
  - 표 가까이(앞뒤 문단 표_주변_문단수 이내)의 본문만 — 표를 소개·요약하는 문장.
  - 그 표의 글자(머리글·단위 표기 포함)에 같은 단위가 나오는 수치만 — 예: 표에
    '억원'이 없으면 본문의 '218억원'은 그 표와 대조하지 않는다.
  - 수치가 있는 표(숫자 최소_표숫자개 이상)만, 날짜·연도·차수 등은 제외.
결과는 실패가 아니라 '확인 필요' 목록으로만 돌려준다(문서는 고치지 않음).
"""
from __future__ import annotations

import re

# 표 수치와 대조할 단위. 연·월·일·시·분·차·회·쪽 등은 날짜·순서라 제외한다.
_단위 = (r"억\s?원|조\s?원|백만\s?원|천만\s?원|천\s?원|만\s?원|원|%p|％p|%|％|"
        r"명|건|개소|곳|대|가구|세대|톤|㎡|㎢|km|㎞")
_숫자 = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
_본문_수치 = re.compile(rf"(?<![\d.,])({_숫자})\s?({_단위})")
_표_숫자 = re.compile(rf"(?<![\d.])({_숫자})")
최소_표숫자 = 5
표_주변_문단수 = 3


def 숫자_정규화(value: str) -> str:
    """'1,234.50' → '1234.5'(쉼표·끝자리 0 제거)."""
    value = value.replace(",", "")
    if "." in value:
        value = value.rstrip("0").rstrip(".")
    return value


def _단위_정규화(unit: str) -> str:
    return re.sub(r"\s", "", unit).replace("％", "%")


def 본문_수치(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), _단위_정규화(m.group(2))) for m in _본문_수치.finditer(text or "")]


def 표_숫자(rows) -> set[str]:
    result = set()
    for row in rows or []:
        for cell in row:
            for m in _표_숫자.finditer(cell or ""):
                result.add(숫자_정규화(m.group(1)))
    return result


_단위_붙은_수치 = re.compile(rf"(?<![\d.,])({_숫자})\s?({_단위})")
_단위_표기 = re.compile(rf"[(（]\s*(?:단위\s*[:：]\s*)?({_단위})\s*[)）]|단위\s*[:：]\s*({_단위})")


def 표_단위별_숫자(rows) -> dict[str, set[str]]:
    """단위마다 그 단위와 짝지을 수 있는 표 숫자 집합.

    - 칸 안에서 숫자 바로 뒤에 단위가 붙어 있으면('4대', '218억원') 그 숫자만 넣는다.
    - '(억원)', '(단위: 억원)'처럼 괄호 안 단위 표기가 있으면 표 전체에 걸린 단위로
      보고 그 표의 모든 숫자를 넣는다(칸에는 숫자만 있는 통계표).
    실측: 표의 모든 숫자와 대조하면 '4대'를 '11대'로 바꿔도 표 어딘가의 11(행 번호·
    날짜) 때문에 통과했고, 단어 안의 글자('대부분'의 '대')를 단위로 잘못 잡았다.
    """
    rows = rows or []
    result: dict[str, set[str]] = {}
    모든숫자 = 표_숫자(rows)
    for row in rows:
        for cell in row:
            cell = cell or ""
            for m in _단위_붙은_수치.finditer(cell):
                result.setdefault(_단위_정규화(m.group(2)), set()).add(숫자_정규화(m.group(1)))
            for m in _단위_표기.finditer(cell):
                unit = _단위_정규화(m.group(1) or m.group(2))
                result.setdefault(unit, set()).update(모든숫자)
    return result


def 숫자_대조(document) -> dict:
    """inspect_hwpx 결과로, 표 가까이의 본문 수치가 그 표에 있는지 대조한다."""
    blocks = list(document.blocks)
    표들 = [(i, 표_숫자(b.rows), 표_단위별_숫자(b.rows)) for i, b in enumerate(blocks)
           if b.type == "table"]
    표들 = [t for t in 표들 if len(t[1]) >= 최소_표숫자]
    if not 표들:
        return {"status": "skipped", "checked": 0, "issues": [], "review": [],
                "reason": "수치가 있는 표가 없어 대조하지 않음"}
    검사 = 0
    확인필요 = []
    for i, block in enumerate(blocks):
        if block.type != "paragraph":
            continue
        가까운표 = [t for t in 표들 if abs(t[0] - i) <= 표_주변_문단수]
        if not 가까운표:
            continue
        for value, unit in 본문_수치(block.text):
            대상 = [t for t in 가까운표 if unit in t[2]]
            if not 대상:
                continue
            검사 += 1
            if not any(숫자_정규화(value) in t[2][unit] for t in 대상):
                확인필요.append({"text": f"'{value}{unit}'", "context": block.text.strip()[:80]})
    return {"status": "passed", "checked": 검사, "issues": [], "review": 확인필요}
