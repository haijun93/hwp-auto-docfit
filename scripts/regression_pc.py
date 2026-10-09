"""PC 회귀 시험: 문서 사본을 처리하고 원본과 쪽 구성이 같은지 판정한다(알파 W0, 2026-10-09).

사용: .venv\\Scripts\\python.exe scripts\\regression_pc.py 문서.hwp [문서2.hwpx ...] [--exclude-tables] [--out 결과.json]

- 원본은 고치지 않는다. 문서마다 임시 폴더에 사본을 만들어 저장된 앱 설정 그대로 '한 번에 적용'으로 처리한다.
- 판정(쪽 구성 동일 원칙): 보고서(제목 표 1개 + 계층체계)별 쪽 범위와 전체 쪽 수가 원본과 같고, 쪽 나누기는
  보고서 경계에만 있다. 결과 JSON에는 문서 내용을 싣지 않고 쪽 번호·점수·시간만 남긴다.
"""
import argparse
import json
import runpy
import shutil
import sys
import tempfile
import time
from pathlib import Path

import pythoncom
import win32com.client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docfit_core.stage_selection import default_choice, stages_for_mode, without_tables


def 앱_불러오기():
    ns = runpy.run_path(str(ROOT / 'hwp-auto-docfit.py'))
    return ns['작업_실행'].__globals__


def 처리(g, 원본, 작업폴더, 표제외, 로그파일):
    """저장된 설정으로 '한 번에 적용'을 실행하고 결과 경로와 점수 줄을 돌려준다."""
    사본 = Path(작업폴더) / ('src' + Path(원본).suffix.lower())
    shutil.copyfile(원본, 사본)
    점수 = []

    def 로그(*a):
        s = ' '.join(str(x) for x in a)
        로그파일.write(s + '\n')
        if '작업 수행 점수' in s:
            점수.append(s.strip())

    g.update(로그=로그, 진단로그=로그, 상태=lambda *_: None, 단계표시=g.get('단계표시', lambda *_: None),
             _서식통일_최종결과_사용자확인=lambda *_: None)
    s = g['설정_불러오기']()
    std_keys = ["std_margin", "std_ratio", "std_linespacing", "std_title", "std_title_bold", "std_title_auto",
                "std_attachment_auto", "std_midtitle_auto", "std_midtitle_bold", "std_dateinfo", "std_dateinfo_bold",
                "std_symbols", "std_symbol_box_bold", "std_symbol_o_bold", "std_symbol_dash_bold",
                "std_symbol_note_bold", "std_marker_bold_consistency", "std_remove_blank_lines", "std_hanging_indent",
                "std_supplement_indent", "std_parspace", "std_table_header"]
    세부 = {k: bool(s[k]) for k in std_keys}
    세부["std_title_subtitle_pt"] = s["std_title_subtitle_pt"]
    세부["table_fonts"] = s.get("table_fonts", {})
    간격 = {k: int(s[k]) for k in ("std_parspace_chapter", "std_parspace_midtitle", "std_parspace_box",
                                  "std_parspace_circle", "std_parspace_dash", "std_parspace_note",
                                  "std_parspace_return_percent")}
    mode = "all" if s.get("include_spacing", True) else "format"
    stages = {k: default_choice(k, mode) for k, _ in stages_for_mode(mode)}
    if 표제외:
        stages = without_tables(stages)
    시작 = time.time()
    g['작업_실행']([str(사본)], s["punctuation"], None, False, None, None, True, s["stdformat"], s["verify"],
               int(s["punctuation_threshold"]), int(s.get("retry_body", 30)), int(s.get("retry_table", 5)),
               s["paren_shrink"], 세부, 간격, s["paren_label_bold"], s["keep_punctuation_set_together"],
               s["prevent_word_split"], mode, s["label_symbols"], int(s["linespacing_min"]),
               int(s["linespacing_max"]), bool(s.get("table_spacing", True)) and not 표제외, None, False, stages,
               1, 1, None, False, False)
    결과 = next(Path(작업폴더).glob('src(*).hwpx'), None)
    return 사본, 결과, round(time.time() - 시작, 1), (점수[-1] if 점수 else None)


def 쪽구성(g, app, 경로):
    """(보고서별 (첫 쪽, 끝 쪽) 목록, 전체 쪽 수, 쪽 나누기 수)."""
    app.Open(str(경로), 'HWPX' if str(경로).lower().endswith('x') else 'HWP', 'forceopen:true')
    g.update(hwp=app)
    보고서, _ = g['쪽맞춤_보고서_목록']()
    app.Run('MoveDocEnd')
    끝쪽 = g['현재_페이지번호']()
    쪽나눔 = 0
    번호 = 0
    while True:
        try:
            app.SetPos(0, 번호, 0)
        except Exception:
            break
        if tuple(app.GetPos()[:2]) != (0, 번호):
            break
        act = app.CreateAction('ParagraphShape')
        ps = act.CreateSet()
        act.GetDefault(ps)
        쪽나눔 += int(ps.Item('PagebreakBefore') or 0)
        번호 += 1
    app.Clear(1)
    return [[r['start'], r['end']] for r in 보고서 or []], 끝쪽, 쪽나눔


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('documents', nargs='+')
    parser.add_argument('--exclude-tables', action='store_true', help="'표 제외'를 켠 것과 같게 처리")
    parser.add_argument('--out', help='결과 JSON 경로(기본: 표준 출력)')
    args = parser.parse_args()

    g = 앱_불러오기()
    보고 = []
    for 문서 in args.documents:
        with tempfile.TemporaryDirectory(prefix='docfit_regression_') as 폴더, \
                open(Path(폴더) / 'log.txt', 'w', encoding='utf-8') as 로그파일:
            사본, 결과, 초, 점수 = 처리(g, 문서, 폴더, args.exclude_tables, 로그파일)
            항목 = {'document': Path(문서).name, 'seconds': 초, 'score': 점수, 'output_created': bool(결과)}
            if 결과:
                pythoncom.CoInitialize()
                app = win32com.client.DispatchEx('HwpFrame.HwpObject')
                try:
                    app.RegisterModule(g['REGISTER_MODULE_NAME'], g['REGISTER_MODULE_VALUE'])
                    g.update(로그=lambda *a: None, 진단로그=lambda *a: None)
                    원, 원쪽, 원나눔 = 쪽구성(g, app, 사본)
                    결, 결쪽, 결나눔 = 쪽구성(g, app, 결과)
                finally:
                    app.Quit()
                    pythoncom.CoUninitialize()
                다른 = [i + 1 for i in range(max(len(원), len(결)))
                       if (원[i] if i < len(원) else None) != (결[i] if i < len(결) else None)]
                항목.update({'pages': {'original': 원쪽, 'result': 결쪽},
                           'reports': {'original': 원, 'result': 결, 'different': 다른},
                           'page_breaks': {'original': 원나눔, 'result': 결나눔},
                           'layout_same': not 다른 and 원쪽 == 결쪽 and 결나눔 <= max(0, len(결) - 1)})
            보고.append(항목)
    text = json.dumps(보고, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    print(text)
    return 0 if all(x.get('layout_same') for x in 보고) else 1


if __name__ == '__main__':
    sys.exit(main())
