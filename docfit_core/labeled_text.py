"""라벨 입력 모드: ``제목: / 네모: / 원: / 바:`` 같은 줄머리 라벨로 계층을 지정한 텍스트.

생성형 AI에게 "이 라벨 형식으로 답해 달라"고 시키면(``ai_prompts``), 답변의 계층을
추론하지 않고 라벨 그대로 공문서 개조식으로 바꿀 수 있다. 라벨이 없는 ``기간: …``
같은 줄은 상위 항목의 세부 내용으로 보고 ``ㅇ (기간) …`` 괄호 라벨 문장으로 만든다.

블록 종류:
    title  문서 제목(1×1 제목 표)          box   제목 아래 개요 상자(1×1 표)
    ref    참고 상자(1×1 표)               para  문두기호 문단(marker + text)
    table  표(rows)                        blank 빈 줄(항목 묶음 구분)
"""

from __future__ import annotations

import re

# 라벨 → (블록 종류, 문두기호). 같은 뜻의 여러 이름을 받는다.
LABELS: dict[str, tuple[str, str]] = {}
for names, spec in (
    (("제목", "문서제목", "타이틀"), ("title", "")),
    (("상자", "상단박스", "개요상자", "요약", "서론"), ("box", "")),
    (("참고", "참고상자", "참고박스"), ("ref", "")),
    (("네모", "사각형", "소제목", "항목"), ("para", "□")),
    (("원", "동그라미", "세부", "내용"), ("para", "ㅇ")),
    (("바", "대시", "하위"), ("para", "-")),
    (("점", "가운데점"), ("para", "•")),
    (("당구", "당구장", "참고사항"), ("para", "※")),
    (("주석", "주석1", "별"), ("para", "*")),
    (("주석2", "쌍별"), ("para", "**")),
    (("숫자소제목", "소제목숫자"), ("para", "#1")),
    (("로마소제목", "소제목로마"), ("para", "#Ⅰ")),
    (("표",), ("table", "")),
    (("엔터", "빈줄"), ("blank", "")),
):
    for name in names:
        LABELS[name] = spec

_LABEL_LINE = re.compile(r"^\s*(?:[-*•]\s*)?\**\s*([가-힣0-9]{1,6})\s*\**\s*[:：]\s?(.*)$")
_KEY_VALUE = re.compile(r"^\s*([^:：\s][^:：]{0,11}?)\s*[:：]\s*(\S.*)$")
ROMAN = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ"
# 세부 내용(라벨 없는 "키: 값")의 문두기호: 가장 가까운 상위 항목보다 한 단계 아래
_CHILD = {"□": "ㅇ", "#1": "ㅇ", "#Ⅰ": "□", "ㅇ": "-", "-": "•", "•": "•", "※": "-", "*": "-", "**": "-"}


def _label_of(line: str):
    match = _LABEL_LINE.match(line)
    if not match:
        return None
    name = match.group(1)
    return (name, LABELS[name], match.group(2).strip()) if name in LABELS else None


def looks_labeled(text: str) -> bool:
    """줄머리 라벨이 두 줄 이상이고, 그중 계층 라벨(제목·네모·원 등)이 있으면 라벨 형식."""
    hits = [_label_of(line) for line in (text or "").splitlines()]
    hits = [h for h in hits if h]
    return len(hits) >= 2 and any(h[1][0] in ("title", "para", "box") for h in hits)


def _table_cells(value: str) -> list[str]:
    if "|" in value:
        parts = value.strip().strip("|").split("|")
    elif "\t" in value:
        parts = value.split("\t")
    else:
        parts = re.split(r"\s+[:：]\s+|[:：](?=\s)", value, maxsplit=1)
    return [p.strip() for p in parts]


def parse_labeled_text(text: str) -> list[dict]:
    blocks: list[dict] = []
    parent = "□"
    numbers = {"#1": 0, "#Ⅰ": 0}
    for raw in (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if not line:
            if blocks and blocks[-1]["kind"] != "blank":
                blocks.append({"kind": "blank"})
            continue
        label = _label_of(line)
        if label:
            _, (kind, marker), value = label
            if kind == "blank":
                if blocks and blocks[-1]["kind"] != "blank":
                    blocks.append({"kind": "blank"})
                continue
            if kind == "table":
                cells = _table_cells(value)
                if blocks and blocks[-1]["kind"] == "table":
                    blocks[-1]["rows"].append(cells)
                else:
                    blocks.append({"kind": "table", "rows": [cells]})
                continue
            if not value:
                continue
            if kind in ("title", "box", "ref"):
                blocks.append({"kind": kind, "text": value})
                continue
            if marker in numbers:
                numbers[marker] += 1
                if marker == "#1":
                    shown = f"{numbers[marker]}."
                else:
                    n = numbers[marker]
                    shown = (ROMAN[n - 1] if n <= len(ROMAN) else str(n)) + "."
                blocks.append({"kind": "para", "marker": shown, "text": value, "level": marker})
                parent = marker
                continue
            blocks.append({"kind": "para", "marker": marker, "text": value, "level": marker})
            if marker in ("□", "ㅇ", "-"):
                parent = marker
            continue
        kv = _KEY_VALUE.match(line)
        if kv and not re.match(r"^\d{1,2}$", kv.group(1)):  # 시각(14:00)은 키가 아니다
            child = _CHILD.get(parent, "ㅇ")
            blocks.append({"kind": "para", "marker": child, "text": f"({kv.group(1).strip()}) {kv.group(2).strip()}",
                           "level": child})
            continue
        if blocks and blocks[-1]["kind"] in ("para", "box", "ref", "title"):
            blocks[-1]["text"] += " " + line  # 줄바꿈으로 끊긴 같은 항목
        else:
            blocks.append({"kind": "para", "marker": "", "text": line, "level": ""})
    while blocks and blocks[-1]["kind"] == "blank":
        blocks.pop()
    return blocks


def render_blocks(blocks: list[dict]) -> str:
    """블록을 개조식 텍스트로 만든다(상자는 대괄호 머리말로 표시)."""
    lines = []
    for index, block in enumerate(blocks):
        kind = block["kind"]
        if kind == "blank":
            lines.append("")
        elif kind == "title":
            lines.append(block["text"])
        elif kind == "box":
            lines.append(f"[개요] {block['text']}")
        elif kind == "ref":
            lines.append(f"[참고] {block['text']}")
        elif kind == "table":
            lines.extend(" | ".join(row) for row in block["rows"])
        else:
            marker = block["marker"]
            # 새 □/숫자 항목 앞은 한 줄 띄워 묶음을 구분한다(앞이 이미 빈 줄이면 생략).
            if block.get("level") in ("□", "#1", "#Ⅰ") and lines and lines[-1] != "" and index > 0 \
                    and blocks[index - 1]["kind"] != "title":
                lines.append("")
            lines.append(f"{marker} {block['text']}".strip())
    return "\n".join(lines).strip()


def label_outline_text(text: str) -> str:
    return render_blocks(parse_labeled_text(text))
