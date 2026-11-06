"""엑셀 클립보드 HTML Format(CF_HTML)에서 셀 배경 음영만 지운다.

지우는 것: td/th/tr/col/colgroup/table 태그의 bgcolor·background 속성, 같은 태그 인라인 style의
background*·mso-pattern·mso-background-source, <style> 규칙(.xl63 같은 클래스 포함)의 같은 선언.
그대로 두는 것: 글자색·글꼴·테두리·colspan/rowspan·표 구조·글자 내용·<span> 등 셀 안쪽 태그의 style.
변환이 구조나 글자를 바꾸었거나 예외가 나면 원본을 그대로 돌려준다(안전한 폴백).
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

_CELL_TAGS = ("table", "colgroup", "col", "tbody", "thead", "tfoot", "tr", "td", "th")
_START_TAG = re.compile(r"<(%s)(?=[\s/>])((?:\"[^\"]*\"|'[^']*'|[^>\"'])*)>" % "|".join(_CELL_TAGS), re.I)
_ATTR = re.compile(r"""([^\s=/>"']+)(?:\s*=\s*("[^"]*"|'[^']*'|[^\s>]+))?""")
_STYLE_BLOCK = re.compile(r"(<style\b[^>]*>)(.*?)(</style\s*>)", re.I | re.S)
_RULE_BODY = re.compile(r"\{([^{}]*)\}")
_SHADING_PROP = re.compile(r"(?:background(?:-[\w-]+)?|mso-pattern|mso-background-source|mso-shading)\Z", re.I)
_HEADER_KEYS = ("StartHTML", "EndHTML", "StartFragment", "EndFragment")
_STRUCT_TAGS = ("table", "tr", "td", "th", "col", "colgroup")


def _split_declarations(body):
    """따옴표·역슬래시 안의 ';'(mso-number-format 등)는 구분자로 보지 않고 선언을 나눈다."""
    parts, buf, quote, i = [], [], "", 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            buf.append(body[i:i + 2])
            i += 2
            continue
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch == ";":
            parts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    parts.append("".join(buf))
    return parts


def _strip_declarations(body):
    """선언 목록에서 음영 속성만 뺀다. (새 본문, 뺀 개수)"""
    kept, removed = [], 0
    for part in _split_declarations(body):
        name = part.split(":", 1)[0].strip().lower() if ":" in part else ""
        if name and _SHADING_PROP.match(name):
            removed += 1
        else:
            kept.append(part)
    return ";".join(kept), removed


def _strip_style_blocks(html):
    total = 0

    def block(match):
        nonlocal total

        def rule(m):
            nonlocal total
            body, n = _strip_declarations(m.group(1))
            total += n
            return "{" + body + "}"
        return match.group(1) + _RULE_BODY.sub(rule, match.group(2)) + match.group(3)
    return _STYLE_BLOCK.sub(block, html), total


def _strip_tags(html):
    total = 0

    def tag(match):
        nonlocal total
        attrs, cuts = match.group(2), []
        for m in _ATTR.finditer(attrs):
            name = m.group(1).lower()
            if name in ("bgcolor", "background"):
                cuts.append((m.start(), m.end()))
            elif name == "style" and m.group(2):
                raw = m.group(2)
                quote = raw[0] if raw[0] in "\"'" else ""
                body, n = _strip_declarations(raw[1:-1] if quote else raw)
                if n:
                    cuts.append((m.start(), m.end(), "" if not body.strip() else f"style={quote or chr(34)}{body}{quote or chr(34)}"))
        if not cuts:
            return match.group(0)
        out, pos = [], 0
        for cut in cuts:
            out.append(attrs[pos:cut[0]])
            out.append(cut[2] if len(cut) > 2 else "")
            pos = cut[1]
            total += 1
        out.append(attrs[pos:])
        return f"<{match.group(1)}{''.join(out)}>"
    return _START_TAG.sub(tag, html), total


class _Fingerprint(HTMLParser):
    """배경 말고는 바뀌면 안 되는 것들(구조 태그·병합·글자색·글자)을 모은다."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags, self.text, self.in_style = [], [], False

    def handle_starttag(self, tag, attrs):
        if tag == "style":
            self.in_style = True
        if tag in _STRUCT_TAGS:
            a = dict(attrs)
            self.tags.append((tag, a.get("colspan"), a.get("rowspan"), a.get("class"), a.get("width"), a.get("align")))
        for name, value in attrs:
            if name == "style" and value:
                colors = re.findall(r"(?:^|;)\s*(color|border[\w-]*)\s*:\s*([^;]+)", value, re.I)
                if colors:
                    self.tags.append((tag, tuple((k.lower(), v.strip().lower()) for k, v in colors)))

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if not self.in_style:
            self.text.append(data)


def _fingerprint(html):
    parser = _Fingerprint()
    parser.feed(html)
    parser.close()
    return parser.tags, "".join(parser.text)


def _safe_style_fingerprint(html):
    # color·border 선언은 같아야 한다(음영 속성만 사라짐).
    return sorted(re.sub(r"\s+", "", v).lower()
                  for body in _RULE_BODY.findall("".join(m.group(2) for m in _STYLE_BLOCK.finditer(html)))
                  for part in _split_declarations(body)
                  for v in [part] if re.match(r"\s*(color|border[\w-]*)\s*:", v, re.I))


def _rebuild_header(header, html_bytes):
    """CF_HTML 머리의 바이트 위치 4개를 새 본문에 맞춰 다시 쓴다."""
    start_html = len(header)
    new = header
    for key in _HEADER_KEYS:
        new = re.sub(rb"(%s:)(\d+)" % key.encode(), lambda m: m.group(1) + b"%0*d" % (len(m.group(2)), 0), new)
    start_frag = html_bytes.find(b"<!--StartFragment-->")
    end_frag = html_bytes.find(b"<!--EndFragment-->")
    values = {
        "StartHTML": start_html,
        "EndHTML": start_html + len(html_bytes),
        "StartFragment": start_html + (start_frag + len(b"<!--StartFragment-->") if start_frag >= 0 else 0),
        "EndFragment": start_html + (end_frag if end_frag >= 0 else len(html_bytes)),
    }
    for key, value in values.items():
        new = re.sub(rb"(%s:)(\d+)" % key.encode(), lambda m, v=value: m.group(1) + b"%0*d" % (len(m.group(2)), v), new)
    return new


def _transform(data):
    is_text = isinstance(data, str)
    raw = data.encode("utf-8") if is_text else bytes(data)
    match = re.search(rb"StartHTML:\s*(\d+)", raw)
    start = int(match.group(1)) if match else 0
    header, body = (raw[:start], raw[start:]) if match and 0 < start < len(raw) else (b"", raw)
    html = body.decode("utf-8")  # 복호화 실패는 호출 쪽에서 폴백
    if not re.search(r"<t[dh]\b", html, re.I):
        return data, dict(changed=False, removed=0, reason="표 셀이 없는 HTML")
    new, n_style = _strip_style_blocks(html)
    new, n_tag = _strip_tags(new)
    removed = n_style + n_tag
    if not removed:
        return data, dict(changed=False, removed=0, reason="지울 음영 없음")
    if _fingerprint(html) != _fingerprint(new) or _safe_style_fingerprint(html) != _safe_style_fingerprint(new):
        return data, dict(changed=False, removed=0, reason="구조 검증 실패")
    out = new.encode("utf-8")
    if header:
        out = _rebuild_header(header, out) + out
    return (out.decode("utf-8") if is_text else out), dict(changed=True, removed=removed, reason="")


def strip_cell_shading_report(data):
    """(결과, 보고) — 보고에는 changed·removed·reason이 있다. 실패하면 원본과 함께 reason을 돌려준다."""
    if not data or not isinstance(data, (str, bytes, bytearray)):
        return data, dict(changed=False, removed=0, reason="비어 있거나 지원하지 않는 형식")
    try:
        return _transform(data)
    except Exception as exc:  # 어떤 오류든 원본 보존이 우선이다.
        return data, dict(changed=False, removed=0, reason=f"변환 실패: {type(exc).__name__}")


def strip_cell_shading(data):
    """CF_HTML(bytes·str)에서 셀 배경만 지운 같은 형식의 값을 돌려준다. 실패·비정상이면 원본 그대로."""
    return strip_cell_shading_report(data)[0]
