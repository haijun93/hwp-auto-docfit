"""tests/fixtures/timport_*.hwpx 합성 표 시료를 만든다(한/글 없이). 한 번 실행해 결과 파일을 커밋한다."""
import sys
import zipfile
from pathlib import Path

U = 283.465
NS = ('xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
      'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"')


def side(name, kind="SOLID", width="0.12 mm", color="#000000"):
    return f'<hh:{name}Border type="{kind}" width="{width}" color="{color}"/>'


def border_fill(ident, left=None, right=None, top=None, bottom=None, fill=None, extra="", diag=False):
    none = dict(kind="NONE")
    parts = "".join(side(n, **(v or none)) for n, v in (("left", left), ("right", right), ("top", top), ("bottom", bottom)))
    brush = f'<hc:fillBrush><hc:winBrush faceColor="{fill}" hatchColor="#000000" alpha="0"/></hc:fillBrush>' if fill else ""
    slash = f'<hh:slash type="{"CENTER" if diag else "NONE"}"/>'
    return f'<hh:borderFill id="{ident}">{slash}{parts}{brush}{extra}</hh:borderFill>'


THIN = dict(kind="SOLID")
THICK = dict(width="0.5 mm")
DOUBLE = dict(kind="DOUBLE_SLIM", width="0.5 mm")
DASH = dict(kind="DASH")
DOT = dict(kind="DOT")
ALL = dict(left=THIN, right=THIN, top=THIN, bottom=THIN)


def cell(r, c, w, h, bf, text="", rs=1, cs=1, bold=False, para=1):
    run = f'<hp:run charPrIDRef="{2 if bold else 1}"><hp:t>{text}</hp:t></hp:run>' if text else '<hp:run charPrIDRef="1"/>'
    return (f'<hp:tc borderFillIDRef="{bf}"><hp:subList><hp:p paraPrIDRef="{para}">{run}</hp:p></hp:subList>'
            f'<hp:cellAddr colAddr="{c}" rowAddr="{r}"/><hp:cellSpan colSpan="{cs}" rowSpan="{rs}"/>'
            f'<hp:cellSz width="{round(w*U)}" height="{round(h*U)}"/></hp:tc>')


def rows(cells):
    by = {}
    for r, xml in cells:
        by.setdefault(r, []).append(xml)
    return "".join(f"<hp:tr>{''.join(by[r])}</hp:tr>" for r in sorted(by))


def table(cells):
    return f'<hp:p><hp:run><hp:tbl>{rows(cells)}</hp:tbl></hp:run></hp:p>'


HEADER_FILLS = [
    border_fill(1, **ALL),
    border_fill(2, left=THICK, right=THICK, top=THICK, bottom=THICK),
    border_fill(3, left=DOUBLE, right=DOUBLE, top=DOUBLE, bottom=DOUBLE),
    border_fill(4, left=DASH, right=DOT, top=DASH, bottom=DOT),
    border_fill(5, fill="#FCE4D6", **ALL),
    border_fill(6),
    border_fill(7, **ALL, diag=True),
    border_fill(8, fill="#FFFFFF", **ALL),
    border_fill(9, extra='<hc:fillBrush><hc:imgBrush mode="TOTAL"/></hc:fillBrush>', **ALL),
    border_fill(10, left=dict(width="0.7 mm"), right=THIN, top=THIN, bottom=THIN),
]


def write(path, body_tables):
    header = (f'<?xml version="1.0" encoding="UTF-8"?><hh:head {NS}><hh:refList><hh:borderFills>{"".join(HEADER_FILLS)}</hh:borderFills>'
              '<hh:charProperties><hh:charPr id="1"/><hh:charPr id="2"><hh:bold/></hh:charPr></hh:charProperties>'
              '<hh:paraProperties><hh:paraPr id="1"><hh:align horizontal="CENTER"/></hh:paraPr>'
              '<hh:paraPr id="2"><hh:align horizontal="LEFT"/></hh:paraPr><hh:paraPr id="3"><hh:align horizontal="RIGHT"/></hh:paraPr>'
              '</hh:paraProperties></hh:refList></hh:head>')
    section = f'<?xml version="1.0" encoding="UTF-8"?><hs:sec {NS} xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section">{body_tables}</hs:sec>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/hwp+zip")
        z.writestr("Contents/header.xml", header)
        z.writestr("Contents/section0.xml", section)


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    W = 20  # 20mm = 격자 4칸
    # 1 기본 2x2
    write(out / "timport_basic.hwpx", table([(0, cell(0, 0, W, 10, 1, "가")), (0, cell(0, 1, W, 10, 1, "나", bold=True)),
                                            (1, cell(1, 0, W, 10, 1, "다", para=2)), (1, cell(1, 1, W, 10, 1, "라", para=3))]))
    # 2 가운데 병합(가로 2·세로 2)
    write(out / "timport_merge_center.hwpx", table([
        (0, cell(0, 0, W, 10, 1, "a")), (0, cell(0, 1, W, 10, 1, "b", rs=2, cs=2)), (0, cell(0, 3, W, 10, 1, "c")),
        (1, cell(1, 0, W, 10, 1, "d")), (1, cell(1, 3, W, 10, 1, "e")),
        (2, cell(2, 0, W, 10, 1, "f")), (2, cell(2, 1, W, 10, 1, "g")), (2, cell(2, 2, W, 10, 1, "h")), (2, cell(2, 3, W, 10, 1, "i"))]))
    # 3 비균일 칸(열 10·30·20mm, 행 10·20mm)
    write(out / "timport_uneven.hwpx", table([
        (0, cell(0, 0, 10, 10, 1, "x")), (0, cell(0, 1, 30, 10, 1, "y")), (0, cell(0, 2, 20, 10, 1, "z")),
        (1, cell(1, 0, 10, 20, 1)), (1, cell(1, 1, 30, 20, 1)), (1, cell(1, 2, 20, 20, 1))]))
    # 4 굵은·이중·점선·파선 테두리
    write(out / "timport_borders.hwpx", table([(0, cell(0, 0, W, 10, 2, "굵")), (0, cell(0, 1, W, 10, 3, "이중")),
                                              (1, cell(1, 0, W, 10, 4, "점")), (1, cell(1, 1, W, 10, 10, "칠"))]))
    # 5 배경색(흰색은 제외)
    write(out / "timport_fill.hwpx", table([(0, cell(0, 0, W, 10, 5, "색")), (0, cell(0, 1, W, 10, 8, "흰"))]))
    # 6 빈 칸·선 없는 칸
    write(out / "timport_empty.hwpx", table([(0, cell(0, 0, W, 10, 1)), (0, cell(0, 1, W, 10, 6)),
                                            (1, cell(1, 0, W, 10, 6)), (1, cell(1, 1, W, 10, 1, "끝"))]))
    # 7 표 두 개(번호 선택) — 둘째 표는 1x1
    write(out / "timport_two_tables.hwpx", table([(0, cell(0, 0, W, 10, 1, "첫째"))]) + table([(0, cell(0, 0, 40, 10, 2, "둘째"))]))
    # 8 표현 못 하는 속성(대각선·칸 그림 배경)
    write(out / "timport_unsupported.hwpx", table([(0, cell(0, 0, W, 10, 7, "대")), (0, cell(0, 1, W, 10, 9, "그"))]))
    # 9 표가 없는 문서
    write(out / "timport_no_table.hwpx", '<hp:p><hp:run><hp:t>글만</hp:t></hp:run></hp:p>')
    # 10 칸 수 상한 초과(201열)
    write(out / "timport_too_wide.hwpx", table([(0, cell(0, c, 5, 5, 1)) for c in range(201)]))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "tests/fixtures")
