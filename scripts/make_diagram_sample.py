"""Create a diagram HWPX for manual opening in Hancom Office.

Usage: python scripts/make_diagram_sample.py <target.hwpx> <result.hwpx>
"""
import sys
from pathlib import Path

from docfit_core.hwpx.canvas_package_adapter import merge_canvas_block_into_hwpx


def main(argv):
    if len(argv) != 3:
        raise SystemExit('사용법: python scripts/make_diagram_sample.py <대상.hwpx> <결과.hwpx>')
    source, target = map(Path, argv[1:])
    payload = {
        'nodes': [
            {'id': 'start', 'type': 'ellipse', 'position': {'x': 30, 'y': 30}, 'width': 120, 'height': 60,
             'data': {'label': '시작'}},
            {'id': 'process', 'type': 'rect', 'position': {'x': 210, 'y': 30}, 'width': 150, 'height': 60,
             'data': {'label': '처리\n확인'}, 'style': {'backgroundColor': '#EAF2FF', 'borderColor': '#345678'}},
            {'id': 'decision', 'type': 'diamond', 'position': {'x': 430, 'y': 20}, 'width': 100, 'height': 80,
             'data': {'label': '완료?'}},
        ],
        'edges': [
            {'id': 'e1', 'source': 'start', 'target': 'process', 'label': ''},
            {'id': 'e2', 'source': 'process', 'target': 'decision', 'label': ''},
        ],
    }
    merge_canvas_block_into_hwpx(source, {'kind': 'diagram', 'source': payload}, target)
    print(f'생성 완료: {target}')


if __name__ == '__main__':
    main(sys.argv)
