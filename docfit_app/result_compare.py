"""원본·결과 비교(2.0.6): 두 문서의 글을 꺼내 줄 단위로 나란히 비교한 HTML을 만든다.

예전에는 '독립 한/글 비교 뷰어'를 붙일 때까지 비교 단추가 '준비 중' 오류만 보였다(사용자 보고). 한/글 없이 글만 꺼낼 수
있는 형식(HWPX·PDF·MD·TXT)을 비교하고, 바뀐 줄을 색으로 표시한다. 서식(글꼴·간격) 차이는 보이지 않는다.
"""
from __future__ import annotations

import difflib
import html
from pathlib import Path

TEXT_SUFFIXES = {".md", ".txt", ".csv", ".html", ".htm", ".json", ".xml"}
SUPPORTED = TEXT_SUFFIXES | {".hwpx", ".pdf"}
MAX_LINES = 20000


def document_lines(path) -> list[str]:
    """문서의 글을 줄 목록으로. 꺼낼 수 없는 형식이면 ValueError."""
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"{suffix or '이 형식'} 문서는 비교할 수 없어요. HWPX·PDF·MD·TXT만 비교할 수 있어요.")
    if suffix in TEXT_SUFFIXES:
        text = source.read_text(encoding="utf-8-sig", errors="replace")
    elif suffix == ".hwpx":
        from docfit_core.hwpx import inspect_hwpx, to_markdown
        text = to_markdown(inspect_hwpx(source))
        # 첫 줄은 내보내기 표시(파일 이름) 주석이라 비교에서 뺀다.
        text = "\n".join(line for line in text.splitlines() if not line.startswith("<!-- HWP AutoDocFit"))
    else:
        from pypdf import PdfReader
        reader = PdfReader(str(source))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:
                raise ValueError("암호가 걸린 PDF는 비교할 수 없어요.") from exc
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return lines[:MAX_LINES]


def build_report(original, result, target) -> Path:
    """원본·결과 비교 HTML을 target에 쓰고 경로를 돌려준다."""
    original, result, target = Path(original), Path(result), Path(target)
    before, after = document_lines(original), document_lines(result)
    table = difflib.HtmlDiff(wrapcolumn=70).make_table(
        before, after, html.escape(original.name), html.escape(result.name), context=False)
    # difflib은 공백을 &nbsp;로, 칸을 nowrap으로 만들어 긴 문장이 화면 밖으로 나간다 — 줄바꿈되게 바꾼다.
    table = table.replace("&nbsp;", " ").replace(' nowrap="nowrap"', "")
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    changed = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal")
    page = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>원본·결과 비교 — {html.escape(result.name)}</title>
<style>
body {{ font-family: "Malgun Gothic", sans-serif; margin: 24px; color: #0f172a; }}
h1 {{ font-size: 20px; margin: 0 0 4px; }}
p.meta {{ color: #475569; margin: 0 0 16px; font-size: 13px; }}
table.diff {{ border-collapse: collapse; width: 100%; font-size: 13px; table-layout: fixed; }}
table.diff td {{ padding: 2px 6px; vertical-align: top; white-space: pre-wrap; word-break: break-all; }}
table.diff th {{ background: #e2e8f0; padding: 6px; text-align: left; }}
td.diff_header {{ color: #94a3b8; width: 3em; text-align: right; }}
td.diff_next {{ display: none; }}
.diff_add {{ background: #dcfce7; }} .diff_chg {{ background: #fef9c3; }} .diff_sub {{ background: #fee2e2; }}
</style></head><body>
<h1>원본·결과 비교</h1>
<p class="meta">왼쪽 원본: {html.escape(str(original))}<br>오른쪽 결과: {html.escape(str(result))}<br>
바뀐 줄 약 {changed}줄 · 노랑=고침, 초록=더함, 빨강=뺌 · 글만 비교하며 글꼴·간격 같은 서식은 보이지 않아요.</p>
{table}
</body></html>"""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    return target
