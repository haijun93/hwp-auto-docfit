"""생성 문서로 쪽 범위 보존과 통합 검수를 검증한다. 사용자 문서는 열지 않는다."""
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile

import pythoncom
import win32com.client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docfit_core.stage_selection import stages_for_mode


def protection_snapshot(app, g):
    result = []
    app.Run('MoveDocBegin')
    while True:
        pos = app.GetPos()
        action = app.CreateAction('ParagraphShape')
        params = action.CreateSet()
        action.GetDefault(params)
        # 한/글의 문단 보호 항목은 KeepLinesTogether다(KeepLines는 없는 항목).
        result.append((pos[1], g['현재문단_텍스트'](),
                       int(params.Item('KeepLinesTogether') or 0),
                       int(params.Item('KeepWithNext') or 0)))
        app.Run('MoveNextParaBegin')
        next_pos = app.GetPos()
        if next_pos[0] != 0 or next_pos[1] <= pos[1]:
            return result


def main():
    folder = ROOT / 'reports' / 'pipeline-review'
    folder.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='generated-', dir=folder))
    source = work / 'range.hwpx'
    ns = runpy.run_path(str(ROOT / 'hwp-auto-docfit.py'))
    process = ns['문서_처리']
    g = process.__globals__
    pythoncom.CoInitialize()
    app = None
    try:
        app = win32com.client.DispatchEx('HwpFrame.HwpObject')
        app.RegisterModule(g['REGISTER_MODULE_NAME'], g['REGISTER_MODULE_VALUE'])
        g.update(hwp=app, 로그=lambda *_: None, 진단로그=lambda *_: None,
                 상태=lambda *_: None, 단계표시=lambda *_: None)
        app.Run('FileNew')
        for page in range(1, 4):
            if page > 1:
                app.Run('BreakPage')
            g['텍스트_삽입'](f'ㅇ {page}쪽 범위 검증용 본문입니다.')
            action = app.CreateAction('ParagraphShape')
            params = action.CreateSet()
            action.GetDefault(params)
            params.SetItem('KeepLinesTogether', 1)
            params.SetItem('KeepWithNext', 1)
            assert action.Execute(params) is not False
        assert app.SaveAs(str(source), 'HWPX', '') is not False
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        before = protection_snapshot(app, g)
        assert len(before) == 3, before
        assert all(item[2:] == (1, 1) for item in before), before
        g.update(작업_모드='format', 표준서식_사용=False, 표준서식_선행_사용=False,
                 준말_등록표={}, 쪽범위_요청=(2, 2), 검수_사용=True,
                 선택_세부작업={key: False for key, _ in stages_for_mode('format')},
                 작업_반복횟수=1, 최종검수_문서목록=[], 검수_문제목록=[])
        assert process(str(source), 1, 1) is True
        record = g['최종검수_문서목록'][-1]
        output = Path(record['output'])
        assert output.is_file()
        assert record['integrity_ok'] is True, record
        assert app.Open(str(output), 'HWPX', 'forceopen:true') is not False
        after = protection_snapshot(app, g)
        assert before[0] == after[0] and before[2] == after[2], (before, after)
        # 범위 안 문단만 '다음 문단과 함께'를 풀고, 원문의 문단 보호는 그대로 둔다.
        assert after[1][2:] == (1, 0), after
        assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash

        # 표본이 없는 본문·표 검사와 단어 검사가 같은 저장 결과를 한 번만 연다.
        opens = []
        original_open = g['한글_문서_열기']
        def tracked_open(*args):
            opens.append(str(args[1]))
            return original_open(*args)
        g.update(작업_모드='all', 선택_세부작업={'style_unify': True},
                 한글_문서_열기=tracked_open, _서식통일_문서대표프로필={},
                 _서식통일_최종결과_사용자확인=lambda *_: None)
        audit = g['저장결과_규칙검수'](str(source), str(output))
        assert len(opens) == 1, opens
        assert audit['style_unify']['status'] == 'incomplete', audit
        assert all(item['status'] in ('passed', 'incomplete') for item in audit.values()), audit
        assert after == protection_snapshot(app, g), '읽기 전용 검수가 서식을 바꿈'
        report = {'passed': True, 'source': str(source), 'output': str(output),
                  'source_unchanged': True, 'outside_range_unchanged': True,
                  'selected_page_protection_cleared': True, 'audit_reopens': len(opens),
                  'rule_checks': audit}
        (work / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=True))
    finally:
        if app is not None:
            try:
                app.Clear(1)
            finally:
                app.Quit()
        pythoncom.CoUninitialize()


if __name__ == '__main__':
    main()
