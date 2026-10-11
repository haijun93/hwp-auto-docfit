"""약식·정식 시험(2026-10-11 사용자 지시): 약식은 핵심 기능만 5쪽 이내 발췌본으로, 정식은 전체 문서로 1회씩 돌린다.

사용: .venv\\Scripts\\python.exe scripts\\test_tier_pc.py --tier quick|full [--corpus 목록.json] [--flag 이름=0|1]
      [--beta-mode] [--out-dir 폴더] [문서 ...]

- 약식(quick): 문서마다 항목 문장(□·ㅇ·-·*·※ 등)이 가장 많은 연속 5쪽만 남긴 발췌본(원본 해시로 캐시)을 만들어
  핵심 작업만 1회씩 처리한다. 서식 통일(기본=글꼴·크기)은 모든 문서, 한 번에 적용은 시간이 커서 첫 문서에서만 돈다.
  앞 5쪽을 자르면 표지·조직 현황만 남아 서식 통일 표본이 모자라 판정 보류로 불합격이 났다(2026-10-11 실측).
  발췌본은 한 번 만들면 다시 쓴다.
- 정식(full): 원본 전체 문서로 4가지 작업 유형(한 번에 적용·서식 적용·서식 통일·자간 정리)을 1회씩 처리한다.
  단위 시험(python -m unittest discover -s tests)은 따로 돌린다.
- 반복 회차는 두지 않는다(1회차만, 사용자 지시). 처리는 scripts/regression_pc.py를 문서·작업마다 새 프로세스로 부른다.
- 문서 목록은 저장소에 넣지 않는다(업무 문서 이름 비공개). 기본 목록: %APPDATA%\\HwpAutoDocFit\\test_corpus.json
  형식: {"documents": ["C:/.../문서.hwpx", ...]}. 명령줄에 문서를 주면 그 문서만 쓴다.
- 결과: 폴더에 작업별 r.json·로그·결과 문서와 summary.json·summary.md(시간·단계 시간·점수·쪽 구성·판정).
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
약식_쪽수 = 5
TIERS = {
    # (이름, regression_pc 인자, 첫 문서에서만 돌릴지). 약식의 한 번에 적용은 5쪽에도 3~11분이라 첫 문서만(실측 2026-10-11).
    'quick': [('unify', ['--mode', 'unify', '--unify-full-format', '0', '--require-same-layout'], False),
              ('all', ['--mode', 'all'], True)],
    'full': [('all', ['--mode', 'all'], False),
             ('format', ['--mode', 'format'], False),
             ('unify', ['--mode', 'unify', '--unify-full-format', '0', '--require-same-layout'], False),
             ('spacing', ['--mode', 'spacing'], False)],
}
단계들 = ('서식통일 조사', '서식통일 적용', '서식통일 마무리', '서식통일 검수', '문단 아래 간격 페이지 맞춤', '저장')


def 기본_목록():
    return Path(os.environ.get('APPDATA', str(Path.home()))) / 'HwpAutoDocFit' / 'test_corpus.json'


def 발췌본_폴더():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'HwpAutoDocFit' / 'test_excerpts'


항목문장 = re.compile(r'^\s*(?:[□■◇◆○●ㅇ\-*※·•▶]|\d+\.|[①-⑳]|[가-하]\.)')


def 발췌_구간(쪽별_항목수, 쪽수):
    """항목 문장이 가장 많은 연속 '쪽수' 쪽의 (첫 쪽, 끝 쪽). 같으면 앞 구간(순수 함수)."""
    전체 = max(쪽별_항목수) if 쪽별_항목수 else 1
    if 전체 <= 쪽수:
        return 1, 전체
    best = max(range(1, 전체 - 쪽수 + 2),
               key=lambda a: (sum(쪽별_항목수.get(p, 0) for p in range(a, a + 쪽수)), -a))
    return best, best + 쪽수 - 1


def 발췌본_만들기(원본, 쪽수=약식_쪽수):
    """항목 문장이 가장 많은 연속 '쪽수' 쪽만 남긴 HWPX 사본의 경로(원본 해시로 캐시, 원본은 열기만 한다).

    첫 문단(구역·쪽 설정이 든 문단)은 남기고, 그 뒤부터 구간 앞까지와 구간 뒤를 지운다.
    """
    원본 = Path(원본)
    해시 = hashlib.sha256(원본.read_bytes()).hexdigest()[:16]
    대상 = 발췌본_폴더() / f"{원본.stem}.w{쪽수}b.{해시}.hwpx"
    if 대상.exists():
        return 대상
    대상.parent.mkdir(parents=True, exist_ok=True)
    import pythoncom
    import win32com.client
    sys.path.insert(0, str(ROOT / 'scripts'))
    from regression_pc import 앱_불러오기
    g = 앱_불러오기()
    pythoncom.CoInitialize()
    app = win32com.client.DispatchEx('HwpFrame.HwpObject')
    try:
        app.RegisterModule(g['REGISTER_MODULE_NAME'], g['REGISTER_MODULE_VALUE'])
        g.update(hwp=app)

        def 열기():
            app.Open(str(원본), 'HWPX' if 원본.suffix.lower() == '.hwpx' else 'HWP', 'forceopen:true')
            app.Run('MoveDocEnd')
            return app.GetPos()[1], g['현재_페이지번호']()

        끝문단, 전체쪽 = 열기()
        if 전체쪽 > 쪽수:
            쪽별, 문단쪽 = {}, []
            for 번호 in range(끝문단 + 1):
                app.SetPos(0, 번호, 0)
                문단쪽.append(g['현재_페이지번호']())
                if 항목문장.match(g['현재문단_텍스트']() or ''):
                    쪽별[문단쪽[-1]] = 쪽별.get(문단쪽[-1], 0) + 1
            쪽별.setdefault(전체쪽, 0)
            첫쪽, 끝쪽 = 발췌_구간(쪽별, 쪽수)
            print(f'[발췌] {원본.name}: {전체쪽}쪽 중 {첫쪽}~{끝쪽}쪽(항목 문장 '
                  f'{sum(쪽별.get(p, 0) for p in range(첫쪽, 끝쪽 + 1))}개)', flush=True)
            뒤 = next((i for i, p in enumerate(문단쪽) if p > 끝쪽), None)
            앞 = next((i for i, p in enumerate(문단쪽) if p >= 첫쪽), 1)
            # 뒤를 먼저 지워야 앞 문단 번호가 그대로다. 표가 다음 쪽까지 이어지면 한 문단씩 앞에서 다시 자른다.
            while 뒤 is not None and 뒤 > max(1, 앞):
                app.SetPos(0, 뒤, 0)
                app.Run('MoveParaBegin')
                app.Run('MoveSelDocEnd')
                app.Run('Delete')
                app.Run('MoveDocEnd')
                if g['현재_페이지번호']() <= 끝쪽:
                    break
                app.Clear(1)
                열기()
                뒤 -= 1
            if 앞 > 1:
                app.SelectText(1, 0, 앞, 0)
                app.Run('Delete')
            # 남긴 첫 문단이 한 쪽을 따로 차지하면(구간 첫 문단의 쪽 나누기) 끝 문단을 하나씩 지워 '쪽수' 쪽 이내로 맞춘다.
            for _ in range(500):
                app.Run('MoveDocEnd')
                끝 = app.GetPos()[1]
                if g['현재_페이지번호']() <= 쪽수 or 끝 <= 1:
                    break
                app.SetPos(0, 끝 - 1, 0)
                app.Run('MoveParaEnd')
                app.Run('MoveSelDocEnd')
                app.Run('Delete')
        app.SaveAs(str(대상), 'HWPX', '')
        app.Clear(1)
    finally:
        app.Quit()
        pythoncom.CoUninitialize()
    return 대상


def 로그_단계시간(로그):
    if not 로그 or not 로그.exists():
        return {}
    s = 로그.read_text(encoding='utf-8', errors='replace')
    out = {}
    m = re.search(r'오래 걸린 단계\(상위 \d+\): (.*)', s)
    for 이름 in 단계들:
        mm = re.search(re.escape(이름) + r' ([\d.]+)초', m.group(1)) if m else None
        if mm:
            out[이름] = float(mm.group(1))
    if m:
        # 작업마다 단계 이름이 달라 오래 걸린 단계 3개를 그대로 남긴다.
        out['상위 단계'] = ' / '.join(re.sub(r'\(\d+%, \d+회\)', '', x).strip() for x in m.group(1).split(' / ')[:3])
    m = re.search(r'서식통일 완료 \(교정 (\d+)개', s)
    if m:
        out['교정 문단'] = int(m.group(1))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('documents', nargs='*')
    p.add_argument('--tier', choices=tuple(TIERS), default='quick')
    p.add_argument('--corpus', help='문서 목록 JSON(기본 %%APPDATA%%\\HwpAutoDocFit\\test_corpus.json)')
    p.add_argument('--flag', action='append', default=[], metavar='이름=0|1')
    p.add_argument('--beta-mode', action='store_true')
    p.add_argument('--out-dir', help='결과 폴더(기본: 임시 폴더 아래 docfit_tier_시각)')
    a = p.parse_args()

    문서들 = a.documents
    if not 문서들:
        목록 = Path(a.corpus) if a.corpus else 기본_목록()
        if not 목록.exists():
            p.error(f'문서 목록이 없습니다: {목록}')
        문서들 = json.loads(목록.read_text(encoding='utf-8'))['documents']
    출력 = Path(a.out_dir or Path(os.environ.get('TEMP', '.')) / f"docfit_tier_{time.strftime('%Y%m%d_%H%M%S')}")
    출력.mkdir(parents=True, exist_ok=True)
    공통 = [x for f in a.flag for x in ('--flag', f)] + (['--beta-mode'] if a.beta_mode else [])

    시작 = time.time()
    행 = []
    for i, 문서 in enumerate(문서들, 1):
        원본 = Path(문서)
        if a.tier == 'quick':
            t = time.time()
            대상 = 발췌본_만들기(원본)
            print(f'[발췌] {i}. {원본.name} → {대상.name} ({time.time() - t:.0f}초)', flush=True)
        else:
            대상 = 원본
        for 이름, 인자, 첫문서만 in TIERS[a.tier]:
            if 첫문서만 and i > 1:
                continue
            폴더 = 출력 / f'd{i}' / 이름
            폴더.mkdir(parents=True, exist_ok=True)
            t = time.time()
            with open(폴더 / 'stdout.txt', 'w', encoding='utf-8') as so:
                subprocess.run([sys.executable, str(ROOT / 'scripts' / 'regression_pc.py'), *인자, *공통,
                                '--log-dir', str(폴더), '--keep-dir', str(폴더), '--out', str(폴더 / 'r.json'),
                                str(대상)], cwd=str(ROOT), stdout=so, stderr=subprocess.STDOUT)
            r = {}
            if (폴더 / 'r.json').exists():
                r = json.loads((폴더 / 'r.json').read_text(encoding='utf-8'))[0]
            항목 = {'doc': f'd{i}', 'task': 이름, 'wall': round(time.time() - t, 1), 'seconds': r.get('seconds'),
                  'score': r.get('score'), 'pages': r.get('pages'), 'layout_same': r.get('layout_same'),
                  'passed': r.get('passed', False), 'commit': r.get('commit'),
                  'stages': 로그_단계시간(next(폴더.glob('*.log'), None))}
            행.append(항목)
            print(f"[{a.tier}] d{i} {이름}: {'합격' if 항목['passed'] else '불합격'} 처리 {항목['seconds']}초 "
                  f"점수 {항목['score']} 쪽 {항목['pages']} 단계 {항목['stages']}", flush=True)

    요약 = {'tier': a.tier, 'documents': len(문서들), 'flags': a.flag, 'beta_mode': a.beta_mode,
          'total_seconds': round(time.time() - 시작, 1), 'passed': all(x['passed'] for x in 행), 'rows': 행}
    (출력 / 'summary.json').write_text(json.dumps(요약, ensure_ascii=False, indent=2), encoding='utf-8')
    줄 = [f"# {'약식' if a.tier == 'quick' else '정식'} 시험 결과 — 전체 {요약['total_seconds']}초, "
         f"{'합격' if 요약['passed'] else '불합격 있음'}", '',
         '| 문서 | 작업 | 판정 | 처리(초) | 점수 | 쪽(원본→결과) | ' + ' | '.join(단계들) + ' | 교정 | 오래 걸린 단계 |',
         '|' + '---|' * (8 + len(단계들))]
    for x in 행:
        쪽 = x['pages'] or {}
        줄.append(f"| {x['doc']} | {x['task']} | {'합격' if x['passed'] else '불합격'} | {x['seconds']} | {x['score']} | "
                 f"{쪽.get('original')}→{쪽.get('result')} | "
                 + ' | '.join(str(x['stages'].get(s, '')) for s in 단계들) + f" | {x['stages'].get('교정 문단', '')} | {x['stages'].get('상위 단계', '')} |")
    (출력 / 'summary.md').write_text('\n'.join(줄) + '\n', encoding='utf-8')
    print('\n'.join(줄))
    print(f'결과 폴더: {출력}')
    return 0 if 요약['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
