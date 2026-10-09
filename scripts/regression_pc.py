"""PC 회귀 시험: 문서 사본을 앱과 같은 설정으로 처리하고 결과를 판정한다(알파 W0, 2026-10-09; R3 정비 2026-10-10).

사용: .venv\\Scripts\\python.exe scripts\\regression_pc.py 문서 [문서2 ...] [--mode all|format|unify|spacing]
      [--exclude-tables] [--require-same-layout] [--min-score 100] [--flag 이름=0|1] [--log-dir 폴더] [--out 결과.json]

- 원본은 고치지 않는다. 문서마다 임시 폴더에 사본을 만들어 처리한다.
- 설정은 화면이 작업을 시작할 때와 같은 규칙으로 만든다: 저장된 설정(all_include_spacing·카드 옵션), 저장된 세부 작업
  선택(stage_choices), 카드 옵션(표 제외·페이지 맞춤 제외·자간 정리 제외). 실제로 쓴 설정을 결과에 남긴다.
- 판정은 검사마다 pass / fail / not_run / not_applicable 이다. 요구한 검사가 not_run이면 실패로 본다.
  · output: 결과 파일 생성  · score: 최종 점수 >= --min-score  · layout: 원본과 쪽 구성 동일(--require-same-layout일 때)
- 결과 JSON에는 문서 내용을 싣지 않고 버전·커밋·해시·설정·쪽 번호·점수·시간만 남긴다.
"""
import argparse
import hashlib
import json
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pythoncom
import win32com.client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docfit_core.stage_selection import default_choice, stages_for_mode, without_page_fit, without_tables

STD_KEYS = ["std_margin", "std_ratio", "std_linespacing", "std_title", "std_title_bold", "std_title_auto",
            "std_attachment_auto", "std_midtitle_auto", "std_midtitle_bold", "std_dateinfo", "std_dateinfo_bold",
            "std_symbols", "std_symbol_box_bold", "std_symbol_o_bold", "std_symbol_dash_bold",
            "std_symbol_note_bold", "std_marker_bold_consistency", "std_remove_blank_lines", "std_hanging_indent",
            "std_supplement_indent", "std_parspace", "std_table_header"]
PARSPACE_KEYS = ("std_parspace_chapter", "std_parspace_midtitle", "std_parspace_box", "std_parspace_circle",
                 "std_parspace_dash", "std_parspace_note", "std_parspace_return_percent")


def 앱_불러오기(베타모드=False):
    ns = runpy.run_path(str(ROOT / 'hwp-auto-docfit.py'))
    g = ns['작업_실행'].__globals__
    if 베타모드:
        # 알파 새 기능 플래그('알파_…_사용')를 모두 끈다. 배포 베타와 같은지는 버전·커밋으로 따로 확인한다.
        for 이름 in [k for k in g if k.startswith('알파_') and k.endswith('_사용')]:
            g[이름] = False
    return g


def 코드_정보():
    def git(*a):
        try:
            return subprocess.run(['git', '-C', str(ROOT), *a], capture_output=True, text=True, timeout=20).stdout.strip()
        except Exception:
            return ''
    return {'commit': git('rev-parse', '--short', 'HEAD'), 'dirty': bool(git('status', '--porcelain', '--', '*.py'))}


def 작업_설정(s, 모드, 표제외_요청):
    """화면이 작업을 시작할 때와 같은 규칙으로 (모드, 세부 작업, 표준서식 세부, 표 제외 여부)를 만든다."""
    if 모드 is None:
        모드 = 'all' if s.get('all_include_spacing', True) else 'format'
    세부작업 = {k: default_choice(k, 모드) for k, _ in stages_for_mode(모드)}
    저장 = (s.get('stage_choices') or {}).get(모드)
    if isinstance(저장, dict):
        세부작업.update({k: v for k, v in 저장.items() if k in 세부작업 and isinstance(v, bool)})
    if 모드 == 'unify':
        표제외 = 표제외_요청 or bool(s.get('unify_exclude_tables', False))
        쪽맞춤제외 = bool(s.get('unify_exclude_pagefit', True))
    elif 모드 in ('all', 'format'):
        표제외 = 표제외_요청 or bool(s.get('all_exclude_tables', False))
        쪽맞춤제외 = bool(s.get('all_exclude_pagefit', False))
    else:
        표제외 = 쪽맞춤제외 = False
    if 표제외:
        세부작업 = without_tables(세부작업)
    if 쪽맞춤제외:
        세부작업 = without_page_fit(세부작업)
    if 모드 == 'unify' and 'page_layout_keep' in 세부작업:
        세부작업['page_layout_keep'] = bool(s.get('unify_keep_layout', 세부작업['page_layout_keep']))
    세부 = {k: bool(s[k]) for k in STD_KEYS if k in s}
    세부['std_title_subtitle_pt'] = s.get('std_title_subtitle_pt')
    세부['table_fonts'] = s.get('table_fonts', {})
    세부['unify_exclude_spacing'] = 모드 == 'unify' and (bool(s.get('unify_exclude_spacing', False))
                                                     or not 세부작업.get('unify_spacing', True))
    return 모드, 세부작업, 세부, 표제외


def 처리(g, 원본, 작업폴더, 모드, 표제외_요청, 로그파일):
    """앱과 같은 설정으로 처리하고 (사본, 결과, 초, 점수, 설정 요약)을 돌려준다."""
    사본 = Path(작업폴더) / ('src' + Path(원본).suffix.lower())
    shutil.copyfile(원본, 사본)
    점수줄 = []

    def 로그(*a):
        s = ' '.join(str(x) for x in a)
        로그파일.write(s + '\n')
        if '작업 수행 점수' in s:
            점수줄.append(s.strip())

    g.update(로그=로그, 진단로그=로그, 상태=lambda *_: None, 단계표시=g.get('단계표시', lambda *_: None),
             _서식통일_최종결과_사용자확인=lambda *_: None)
    s = g['설정_불러오기']()
    모드, 세부작업, 세부, 표제외 = 작업_설정(s, 모드, 표제외_요청)
    간격 = {k: int(s[k]) for k in PARSPACE_KEYS}
    시작 = time.time()
    g['작업_실행']([str(사본)], s["punctuation"], None, False, None, None, True, s["stdformat"], s["verify"],
               int(s["punctuation_threshold"]), int(s.get("retry_body", 30)), int(s.get("retry_table", 5)),
               s["paren_shrink"], 세부, 간격, s["paren_label_bold"], s["keep_punctuation_set_together"],
               s["prevent_word_split"], 모드, s["label_symbols"], int(s["linespacing_min"]),
               int(s["linespacing_max"]), bool(s.get("table_spacing", True)) and not 표제외, None, False, 세부작업,
               2 if s.get("two_pass_processing") else 1, 1, None, False, False)
    결과 = next(Path(작업폴더).glob('src(*).hwpx'), None)
    점수 = None
    if 점수줄:
        m = re.search(r'([\d.]+)\s*/\s*100', 점수줄[-1])
        점수 = float(m.group(1)) if m else None
    설정 = {'mode': 모드, 'exclude_tables': 표제외,
            'stages_on': sorted(k for k, v in 세부작업.items() if v),
            'settings_sha256': hashlib.sha256(json.dumps(s, ensure_ascii=False, sort_keys=True, default=str)
                                              .encode('utf-8')).hexdigest()[:16]}
    return 사본, 결과, round(time.time() - 시작, 1), 점수, 설정


def 쪽구성(g, app, 경로):
    """(보고서별 [첫 쪽, 끝 쪽] 목록, 전체 쪽 수, {보고서 경계 쪽 나누기, 그 밖의 쪽 나누기})."""
    app.Open(str(경로), 'HWPX' if str(경로).lower().endswith('x') else 'HWP', 'forceopen:true')
    g.update(hwp=app)
    보고서, 제목문단 = g['쪽맞춤_보고서_목록']()
    경계 = set(제목문단 or [])
    app.Run('MoveDocEnd')
    끝쪽 = g['현재_페이지번호']()
    나눔 = {'report_boundary': 0, 'other': 0}
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
        if int(ps.Item('PagebreakBefore') or 0):
            나눔['report_boundary' if 번호 in 경계 else 'other'] += 1
        번호 += 1
    app.Clear(1)
    return [[r['start'], r['end']] for r in 보고서 or []], 끝쪽, 나눔


def 판정(항목, 요구):
    """검사별 상태와 전체 합격. 요구한 검사가 not_run이면 실패."""
    검사 = {'output': 'pass' if 항목['output_created'] else 'fail'}
    점수 = 항목.get('score')
    검사['score'] = 'not_run' if 점수 is None else ('pass' if 점수 >= 요구['min_score'] else 'fail')
    if not 요구['same_layout']:
        검사['layout'] = 'not_applicable'
    elif 항목.get('layout_same') is None:
        검사['layout'] = 'not_run'
    else:
        검사['layout'] = 'pass' if 항목['layout_same'] else 'fail'
    필수 = ['output', 'score'] + (['layout'] if 요구['same_layout'] else [])
    return 검사, all(검사[k] == 'pass' for k in 필수)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('documents', nargs='+')
    parser.add_argument('--mode', choices=('all', 'format', 'unify', 'spacing'),
                        help='작업 유형(기본: 저장된 설정의 한 번에 적용 구성, all_include_spacing)')
    parser.add_argument('--exclude-tables', action='store_true', help="'표 제외'를 켠 것과 같게 처리")
    parser.add_argument('--require-same-layout', action='store_true',
                        help='쪽 구성(원본과 같음)을 합격 조건으로 쓴다(서식 통일의 원본 쪽 구성 유지 시험용)')
    parser.add_argument('--min-score', type=float, default=100.0, help='합격 최소 점수(기본 100)')
    parser.add_argument('--out', help='결과 JSON 경로(기본: 표준 출력)')
    parser.add_argument('--log-dir', help='문서별 작업 로그를 남길 폴더(처리 시간 계측 확인용)')
    parser.add_argument('--flag', action='append', default=[], metavar='이름=0|1',
                        help='앱 전역 플래그를 켜고 끔(예: --flag 알파_문단세트_사용=0). 여러 번 줄 수 있음')
    parser.add_argument('--beta-mode', action='store_true', help="알파 새 기능 플래그('알파_…_사용')를 모두 끔")
    args = parser.parse_args()

    g = 앱_불러오기(args.beta_mode)
    바꾼_플래그 = {}
    for 항목 in args.flag:
        이름, _, 값 = 항목.partition('=')
        if 이름 not in g:
            parser.error(f'앱에 없는 플래그입니다: {이름}')
        g[이름] = 값.strip() not in ('0', 'false', 'False', '')
        바꾼_플래그[이름] = g[이름]
    알파_플래그 = {k: bool(v) for k, v in g.items() if k.startswith('알파_') and k.endswith('_사용')}
    공통 = {'app_version': g.get('APP_VERSION'), **코드_정보(), 'alpha_flags': 알파_플래그,
            'flags_overridden': 바꾼_플래그, 'beta_mode': args.beta_mode}
    요구 = {'min_score': args.min_score, 'same_layout': args.require_same_layout}
    보고 = []
    for 문서 in args.documents:
        with tempfile.TemporaryDirectory(prefix='docfit_regression_') as 폴더, \
                open(Path(폴더) / 'log.txt', 'w', encoding='utf-8') as 로그파일:
            사본, 결과, 초, 점수, 설정 = 처리(g, 문서, 폴더, args.mode, args.exclude_tables, 로그파일)
            항목 = {'document': Path(문서).name,
                  'document_sha256': hashlib.sha256(Path(문서).read_bytes()).hexdigest()[:16],
                  **공통, 'settings': 설정, 'seconds': 초, 'score': 점수, 'output_created': bool(결과)}
            if 결과:
                pythoncom.CoInitialize()
                app = win32com.client.DispatchEx('HwpFrame.HwpObject')
                try:
                    app.RegisterModule(g['REGISTER_MODULE_NAME'], g['REGISTER_MODULE_VALUE'])
                    g.update(로그=lambda *a: None, 진단로그=lambda *a: None)
                    # TXT·MD 등은 원본에 쪽 구성이 없어 결과만 잰다(쪽 구성 비교 없음).
                    if 사본.suffix in ('.hwp', '.hwpx'):
                        원, 원쪽, 원나눔 = 쪽구성(g, app, 사본)
                    else:
                        원, 원쪽, 원나눔 = [], None, None
                    결, 결쪽, 결나눔 = 쪽구성(g, app, 결과)
                finally:
                    app.Quit()
                    pythoncom.CoUninitialize()
                다른 = [i + 1 for i in range(max(len(원), len(결)))
                       if (원[i] if i < len(원) else None) != (결[i] if i < len(결) else None)]
                항목.update({'pages': {'original': 원쪽, 'result': 결쪽},
                           'reports': {'original': 원, 'result': 결, 'different': 다른},
                           'page_breaks': {'original': 원나눔, 'result': 결나눔},
                           'layout_same': None if 원쪽 is None else (not 다른 and 원쪽 == 결쪽)})
            항목['checks'], 항목['passed'] = 판정(항목, 요구)
            if args.log_dir:
                로그파일.flush()
                Path(args.log_dir).mkdir(parents=True, exist_ok=True)
                shutil.copyfile(Path(폴더) / 'log.txt', Path(args.log_dir) / f"{Path(문서).stem}.log")
            보고.append(항목)
    text = json.dumps(보고, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    print(text)
    return 0 if all(x['passed'] for x in 보고) else 1


if __name__ == '__main__':
    sys.exit(main())
