"""C28: 사본과 소유 PID만 사용하는 Windows 한/글 LiveLink 실측.

실행: 지정 venv Python scripts/livelink_poc.py --out <새 결과 폴더>
원본 입력/임의 PID 인자는 의도적으로 제공하지 않는다. 결과 JSON은 단계마다 기록한다.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = Path(r"C:\HWP_AUTODOCFIT")
LOCK = BASE / ".com-test.lock"
SOURCE = BASE / "테스트예시" / "기본 서식.hwpx"


class UnsafeTargetError(RuntimeError):
    """일반적인 API 미지원과 달리 전체 시험을 즉시 중단해야 하는 대상 변경."""


def hwp_ids():
    # tasklist는 이 PC에서 3초 제한을 간헐적으로 초과한다. 프로세스 정보만 조회한다.
    import psutil
    return {p.info['pid'] for p in psutil.process_iter(['pid', 'name'])
            if (p.info['name'] or '').casefold() == 'hwp.exe'}


def cleanup_owned():
    from docfit_core import hwp_process
    def runner(args):
        return subprocess.run(args, capture_output=True, text=True, timeout=15,
                              creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    return hwp_process.kill_owned(runner=runner)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_copy(obj, sample, pid, live_pids):
    if pid not in live_pids:
        raise UnsafeTargetError('소유 PID 종료: 문서 접근 중단')
    path = Path(str(obj.XHwpDocuments.Active_XHwpDocument.FullName)).resolve()
    if path != sample.resolve():
        raise UnsafeTargetError('사본 경로 불일치: 즉시 중단')
    return {'pid': pid, 'copy_path_verified': True}


def write_json(path, value):
    tmp = path.with_name(f'{path.name}.{os.getpid()}.{threading.get_ident()}.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    for attempt in range(30):
        try:
            os.replace(tmp, path)
            break
        except PermissionError:
            if attempt == 29:
                raise
            time.sleep(.03)


@contextmanager
def test_lock(wait_seconds):
    """기존 잠금은 나이와 무관하게 삭제하지 않는다."""
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f'COM 잠금 대기 만료: {LOCK}')
            time.sleep(1)
    token = f'Codex {time.strftime("%Y-%m-%dT%H:%M:%S")} C28 pid={os.getpid()}'
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        stream.write(token)
    try:
        yield token
    finally:
        if LOCK.exists() and LOCK.read_text(encoding='utf-8') == token:
            LOCK.unlink()


def worker(folder):
    import pythoncom
    import win32com.client as client
    import win32process
    import win32gui
    from docfit_core import hwp_process

    report = {'started': time.strftime('%Y-%m-%dT%H:%M:%S'), 'probes': []}
    result_path = folder / 'result.json'
    target_guard = None
    def probe(name, api, action):
        report['active'] = name
        report['heartbeat'] = time.time()
        write_json(result_path, report)
        start = time.perf_counter()
        try:
            if target_guard is not None:
                target_guard()
            value = action()
            row = dict(name=name, api=api, status='PASS', value=value)
        except Exception as exc:
            row = dict(name=name, api=api, status='FAIL', error=repr(exc))
            if isinstance(exc, UnsafeTargetError):
                report['probes'].append(row)
                write_json(result_path, report)
                raise
        row['seconds'] = round(time.perf_counter() - start, 4)
        report['probes'].append(row)
        write_json(result_path, report)
        return row

    pythoncom.CoInitialize()
    app = None
    owned = set()
    try:
        before = hwp_ids()
        report['preexisting_pids'] = sorted(before)
        if before:
            raise RuntimeError('기존 한/글 PID 존재: 이 NEO PoC는 독점 시험 환경에서만 실행')
        report['active'] = 'DispatchEx'
        report['heartbeat'] = time.time()
        write_json(result_path, report)
        app = client.DispatchEx('HwpFrame.HwpObject')
        new_pids = hwp_ids() - before
        if len(new_pids) != 1:
            app = None
            raise RuntimeError('독립 신규 Hwp.exe PID 확인 실패: 문서 접근 중단')
        pid = new_pids.pop()
        owned.add(pid)
        hwp_process.register_owned(owned)
        write_json(folder / 'owned.json', {'pids': sorted(owned)})
        windows = []
        win32gui.EnumWindows(lambda handle, _: windows.append(handle)
            if win32process.GetWindowThreadProcessId(handle)[1] == pid else None, None)
        hwnd = windows[0] if windows else 0
        write_json(folder / 'owned.json', {'pids': sorted(owned), 'hwnd': hwnd})
        report.update(pid=pid, hwnd=hwnd)
        app.XHwpWindows.Item(0).Visible = True
        probe('version', 'Version', lambda: app.Version)
        report['typeinfo_methods'] = sorted(set(app._prop_map_get_) |
            {name for name in dir(type(app)) if not name.startswith('_')})

        def register():
            from docfit_core.format_samples import REGISTRY_VALUE
            if not app.RegisterModule('FilePathCheckDLL', REGISTRY_VALUE):
                raise RuntimeError('RegisterModule False; Open 금지')
            return True
        if probe('security', 'RegisterModule', register)['status'] != 'PASS':
            return
        scratch = folder / 'scratch'
        scratch.mkdir()
        sample = scratch / 'sample.hwpx'
        shutil.copy2(SOURCE, sample)
        original_hash = digest(SOURCE)
        report['source_sha256'] = original_hash
        if not app.Open(str(sample), 'HWPX', ''):
            raise RuntimeError('사본 Open 실패')

        def verify(obj):
            # ROT 접근 전 소유 창의 경로를 먼저 확인한다. 후보는 다시 PID와 경로를 검사한다.
            return verify_copy(obj, sample, pid, hwp_ids())
        verify(app)
        target_guard = lambda: verify(app)

        def rot_attach():
            verify(app)
            rot = pythoncom.GetRunningObjectTable()
            context = pythoncom.CreateBindCtx(0)
            found = []
            for moniker in rot.EnumRunning():
                name = moniker.GetDisplayName(context, None)
                # HWP ROT 이름 끝 PID를 검증한 후보만 GetObject. 다른 문서에는 붙지 않는다.
                if 'HwpObject' not in name:
                    continue
                if str(pid) not in name.split('!')[-1].split(':') and hwp_ids() != owned:
                    found.append({'moniker': name, 'status': 'SKIP_UNVERIFIED_PID'})
                    continue
                candidate = client.Dispatch(rot.GetObject(moniker).QueryInterface(pythoncom.IID_IDispatch))
                report['owned_moniker'] = name
                found.append({'moniker': name, **verify(candidate),
                              'RegisterModule': bool(candidate.RegisterModule('FilePathCheckDLL', 'HwpAutoDocFitSecurity'))})
            return found
        probe('attach_rot', 'ROT.EnumRunning/GetObject (PID whitelist)', rot_attach)
        def bind_attach():
            verify(app)
            if hwp_ids() != owned or not report.get('owned_moniker'):
                return {'status': 'SKIP', 'reason': '단독 소유 인스턴스 조건 미충족'}
            candidate = client.GetObject(report['owned_moniker'])
            return verify(candidate)
        probe('attach_moniker', 'GetObject(display name)/BindToMoniker', bind_attach)
        def active_attach():
            verify(app)
            if hwp_ids() != owned:
                return {'status': 'SKIP', 'reason': '사용자 PID 존재: GetActiveObject 대상 보장 불가'}
            candidate = client.GetActiveObject('HwpFrame.HwpObject')
            return verify(candidate)
        probe('attach_active', 'GetActiveObject (only owned HWP exists)', active_attach)
        probe('cursor', 'GetPos/GetSelectedPosBySet', lambda: {'pos': app.GetPos(), 'selection': selected_pos(app)})
        def paragraph():
            saved = app.GetPos()
            try:
                app.HAction.Run('MoveParaBegin')
                app.HAction.Run('MoveSelParaEnd')
                return {'selection': selected_pos(app), 'text': app.GetTextFile('TEXT', 'saveblock:true')}
            finally:
                app.HAction.Run('Cancel')
                app.SetPos(*saved)
        probe('paragraph', 'MoveParaBegin/MoveSelParaEnd/GetTextFile', paragraph)
        def page():
            saved = app.GetPos()
            try:
                number = app.KeyIndicator()
                app.HAction.Run('MovePageBegin')
                begin = app.GetPos()
                app.HAction.Run('MovePageEnd')
                return {'indicator': number, 'begin': begin, 'end': app.GetPos()}
            finally:
                app.SetPos(*saved)
        probe('page', 'KeyIndicator/MovePageBegin/MovePageEnd', page)
        def table_context():
            ctrl = app.HeadCtrl
            while ctrl:
                if ctrl.CtrlID == 'tbl':
                    anchor = ctrl.GetAnchorPos(0)
                    pos = tuple(anchor.Item(key) for key in ('List', 'Para', 'Pos'))
                    app.SetPos(*pos)
                    app.HAction.Run('MoveRight')
                    return {'anchor': pos, 'inside_pos': app.GetPos(),
                            'parent': app.ParentCtrl.CtrlID}
                ctrl = ctrl.Next
            raise RuntimeError('표 없음')
        probe('table_context', 'HeadCtrl/GetAnchorPos/ParentCtrl/GetPos', table_context)

        # 이후는 사본 편집. 원본/사본 저장 없이 메모리에서만 시험한다.
        app.HAction.Run('Cancel')
        app.HAction.Run('MoveDocEnd')
        def insert(text):
            action = app.CreateAction('InsertText')
            params = action.CreateSet()
            params.SetItem('Text', text)
            if not action.Execute(params):
                raise RuntimeError('InsertText False')
        def undo_group():
            before_text = app.GetTextFile('TEXT', '')
            app.BeginTransaction()
            try:
                insert('C28_ALPHA')
                insert('C28_BETA')
            finally:
                app.EndTransaction()
            changed = app.GetTextFile('TEXT', '')
            app.HAction.Run('Undo')
            restored = app.GetTextFile('TEXT', '')
            if changed == before_text or restored != before_text:
                raise AssertionError('복수 편집 후 Undo 1회 원복 실패')
            return {'changed': True, 'one_undo_restored_text': True}
        probe('undo_group', 'BeginTransaction/EndTransaction/HAction.Undo', undo_group)
        def undo_plain():
            before_text = app.GetTextFile('TEXT', '')
            insert('C28_FIRST')
            app.HAction.Run('CharShapeBold')
            insert('C28_SECOND')
            app.HAction.Run('Undo')
            after = app.GetTextFile('TEXT', '')
            return {'one_undo_restored_text': after == before_text,
                    'first_remaining': 'C28_FIRST' in after, 'second_remaining': 'C28_SECOND' in after}
        probe('undo_plain', 'InsertText/Bold/InsertText/Undo', undo_plain)

        def insert_template():
            # 같은 사본의 첫 표를 블록 HML로 얻어 클립보드 없이 문서 끝에 삽입.
            ctrl = app.HeadCtrl
            while ctrl and ctrl.CtrlID != 'tbl':
                ctrl = ctrl.Next
            if not ctrl:
                raise RuntimeError('표 없음')
            anchor = ctrl.GetAnchorPos(0)
            app.SetPos(*(anchor.Item(k) for k in ('List', 'Para', 'Pos')))
            app.FindCtrl()
            hml = app.GetTextFile('HWPML2X', 'saveblock:true')
            if '<TABLE' not in hml.upper():
                raise AssertionError('선택 HML에 표 없음')
            (scratch / 'table.hml').write_text(hml, encoding='utf-8')
            app.HAction.Run('Cancel')
            app.HAction.Run('MoveDocEnd')
            count = table_count(app)
            before_hml = app.GetTextFile('HWPML2X', '')
            result = app.SetTextFile(hml, 'HWPML2X', 'insertfile')
            after = table_count(app)
            if not result or after != count + 1:
                raise AssertionError(f'표 수 {count}->{after}, result={result}')
            app.HAction.Run('Undo')
            restored_hml = app.GetTextFile('HWPML2X', '')
            undo_count = table_count(app)
            return {'tables_before': count, 'tables_after': after, 'clipboard': False,
                    'one_undo_table_count_restored': undo_count == count,
                    'one_undo_hml_identical': before_hml == restored_hml}
        probe('insert_template', 'FindCtrl/GetTextFile(HWPML2X)/SetTextFile(insertfile)', insert_template)
        probe('replace_table', 'table_units.export_resized/auxiliary HML/DeleteCtrl/SetTextFile',
              lambda: replace_table(app, scratch))

        def selection_spacing():
            import runpy
            ns = runpy.run_path(str(ROOT / 'hwp-auto-docfit.py'), run_name='livelink_poc_import')
            ns['단어모드_자간적용'].__globals__['hwp'] = app
            app.HAction.Run('Cancel')
            app.HAction.Run('MoveDocEnd')
            insert('\r\nC28 SELECTED OUTSIDE')
            app.HAction.Run('MoveParaBegin')
            start = app.GetPos()
            end = (*start[:2], start[2] + 3)
            outside = (*start[:2], start[2] + 6)
            fields = ['Spacing' + suffix for suffix in ('Hangul', 'Latin', 'Hanja', 'Japanese', 'Other', 'Symbol', 'User')]
            def values(pos):
                app.SetPos(*pos)
                shape = app.CharShape
                return [shape.Item(key) for key in fields]
            before_selected, before_outside = values(start), values(outside)
            ns['단어모드_자간적용']([(start, end, before_selected)], -1)
            after_selected, after_outside = values(start), values(outside)
            if after_selected != [v - 1 for v in before_selected] or after_outside != before_outside:
                raise AssertionError('선택 경계 침범/자간 적용 불일치')
            return dict(before=before_selected, after=after_selected, outside_unchanged=True,
                        limitation='기존 엔진 저수준 적용만 검증; 전체 탐색 결과 동일성 미검증')
        probe('selection_spacing', 'existing 단어모드_자간적용/SelectText/CharShape', selection_spacing)
        probe('dialog', 'HAction.Run(CharShape) + marshaled GetPos + PID dialog close',
              lambda: dialog_probe(app, pid, folder))
        report['source_unchanged'] = digest(SOURCE) == original_hash
    except Exception as exc:
        report['fatal'] = repr(exc)
    finally:
        report['active'] = 'cleanup'
        report['heartbeat'] = time.time()
        write_json(result_path, report)
        if app is not None and owned:
            try:
                app.Clear(1)
                app.Quit()
            except Exception as exc:
                report['cleanup_error'] = repr(exc)
        report['killed_owned'] = cleanup_owned()
        report['remaining_owned'] = sorted(owned & hwp_ids())
        report['active'] = 'done'
        write_json(result_path, report)
        pythoncom.CoUninitialize()


def table_count(app):
    ctrl, count = app.HeadCtrl, 0
    while ctrl:
        count += ctrl.CtrlID == 'tbl'
        ctrl = ctrl.Next
    return count


def selected_pos(app):
    begin, end = app.CreateSet('ListParaPos'), app.CreateSet('ListParaPos')
    if not app.GetSelectedPosBySet(begin, end):
        pos = tuple(app.GetPos())
        return [pos, pos]
    return [tuple(item.Item(k) for k in ('List', 'Para', 'Pos')) for item in (begin, end)]


def replace_table(app, scratch):
    from docfit_core import table_catalog, table_units
    trace = []
    def mark(step):
        trace.append(step)
        write_json(scratch.parent / 'replace-trace.json', trace)
    mark('export_resized')
    source = scratch / 'catalog.hwpx'
    shutil.copy2(table_catalog.default_catalog_path(), source)
    record = next(row for row in table_catalog._scan(source) if table_units.plan_for(row).get('row'))
    plan = table_units.plan_for(record)
    original, resized, shrunk = scratch / 'template.hwpx', scratch / 'resized.hwpx', scratch / 'shrunk.hwpx'
    table_catalog.export_template(record['id'], original, source)
    table_units.export_resized(record['id'], resized, source, row_count=plan['row']['count'] + 1)
    table_units.export_resized(record['id'], shrunk, source, row_count=plan['row']['count'] - 1)
    target_doc = app.XHwpDocuments.Active_XHwpDocument
    target_id = target_doc.DocumentID
    def hml_for(path):
        mark(f'auxiliary Add {path.name}')
        auxiliary = app.XHwpDocuments.Add(True)
        try:
            auxiliary.SetActive_XHwpDocument()
            mark(f'auxiliary Open {path.name}')
            if not auxiliary.Open(str(path), 'HWPX', ''):
                raise RuntimeError('보조 문서 Open False')
            if Path(str(auxiliary.FullName)).resolve() != path.resolve():
                raise RuntimeError('보조 문서 경로 불일치')
            value = app.GetTextFile('HWPML2X', '')
            mark(f'auxiliary HML read {path.name}')
            return value
        finally:
            # NEO에서 보조 탭 Clear/Close가 예외·대기를 일으켜 세션 끝까지 유지한다.
            # 입력을 열고 읽기만 했으므로 저장할 변경이 없으며 대상은 다시 열지 않는다.
            target_doc.SetActive_XHwpDocument()
            if app.XHwpDocuments.Active_XHwpDocument.DocumentID != target_id:
                raise RuntimeError('대상 문서 ID 복귀 실패')
    original_hml, resized_hml, shrunk_hml = hml_for(original), hml_for(resized), hml_for(shrunk)
    app.HAction.Run('Cancel')
    app.HAction.Run('MoveDocEnd')
    count = table_count(app)
    mark('insert original HML')
    if not app.SetTextFile(original_hml, 'HWPML2X', 'insertfile'):
        raise RuntimeError('SetTextFile(template HML) False')
    if table_count(app) != count + 1:
        raise AssertionError('템플릿 직접 삽입 후 표 수 불일치')
    ctrl, target = app.HeadCtrl, None
    while ctrl:
        if ctrl.CtrlID == 'tbl':
            target = ctrl
        ctrl = ctrl.Next
    anchor = target.GetAnchorPos(0)
    pos = tuple(anchor.Item(k) for k in ('List', 'Para', 'Pos'))
    app.SetPos(*pos)
    app.HAction.Run('MoveRight')
    if app.ParentCtrl.CtrlID != 'tbl':
        raise AssertionError('커서가 대상 표 내부가 아님')
    app.SetPos(*pos)
    mark('delete original table')
    if not app.DeleteCtrl(target):
        raise RuntimeError('DeleteCtrl False')
    mark('insert increased HML')
    if not app.SetTextFile(resized_hml, 'HWPML2X', 'insertfile'):
        raise RuntimeError('SetTextFile(resized HML) False')
    if table_count(app) != count + 1:
        raise AssertionError('교체 후 표 수 불일치')
    from defusedxml import ElementTree as ET
    root = ET.fromstring(app.GetTextFile('HWPML2X', ''))
    tables = list(root.iter('TABLE'))
    expected = record['rows'] + plan['row']['core'] + plan['row']['sep']
    if int(tables[-1].get('RowCount')) != expected:
        raise AssertionError('정보단위 증가 결과의 행 수 불일치')
    ctrl, target = app.HeadCtrl, None
    while ctrl:
        if ctrl.CtrlID == 'tbl':
            target = ctrl
        ctrl = ctrl.Next
    anchor = target.GetAnchorPos(0)
    mark('delete increased table and insert decreased HML')
    app.SetPos(*(anchor.Item(k) for k in ('List', 'Para', 'Pos')))
    if not app.DeleteCtrl(target) or not app.SetTextFile(shrunk_hml, 'HWPML2X', 'insertfile'):
        raise RuntimeError('정보단위 감소 교체 실패')
    tables = list(ET.fromstring(app.GetTextFile('HWPML2X', '')).iter('TABLE'))
    expected_shrink = record['rows'] - plan['row']['core'] - plan['row']['sep']
    if int(tables[-1].get('RowCount')) != expected_shrink or table_count(app) != count + 1:
        raise AssertionError('정보단위 감소 결과 불일치')
    mark('verified')
    return {'template': record['name'], 'anchor': pos, 'rows_before': record['rows'],
            'rows_after_increase': expected, 'rows_after_decrease': expected_shrink,
            'table_count': count + 1, 'clipboard': False, 'target_doc_id_unchanged': True,
            'limitation': '임의 기존 표의 의미단위 역판정/내용 이관은 별도 구현 필요'}


def dialog_probe(app, pid, folder):
    import threading
    import pythoncom
    import win32com.client as client
    import win32con
    import win32gui
    import win32process
    stream = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, app._oleobj_)
    result = {}
    def caller():
        pythoncom.CoInitialize()
        try:
            remote = client.Dispatch(pythoncom.CoGetInterfaceAndReleaseStream(stream, pythoncom.IID_IDispatch))
            time.sleep(1)
            visible = []
            win32gui.EnumWindows(lambda hwnd, _: visible.append(hwnd)
                if win32process.GetWindowThreadProcessId(hwnd)[1] == pid
                and win32gui.GetWindowText(hwnd) == '글자 모양'
                and win32gui.IsWindowVisible(hwnd) else None, None)
            result['dialog_visible_at_call'] = bool(visible)
            start = time.perf_counter()
            result['call_started'] = time.time()
            write_json(folder / 'dialog.json', result)
            result['getpos'] = remote.GetPos()
            result['call_seconds'] = round(time.perf_counter() - start, 4)
            start = time.perf_counter()
            result['edit_return'] = remote.HAction.Run('CharShapeBold')
            result['edit_seconds'] = round(time.perf_counter() - start, 4)
        except Exception as exc:
            result['error'] = repr(exc)
        finally:
            write_json(folder / 'dialog.json', result)
            pythoncom.CoUninitialize()
    def closer():
        time.sleep(4)
        def visit(hwnd, _):
            if win32process.GetWindowThreadProcessId(hwnd)[1] == pid:
                result.setdefault('windows', []).append({'hwnd': hwnd, 'class': win32gui.GetClassName(hwnd),
                    'title': win32gui.GetWindowText(hwnd), 'visible': bool(win32gui.IsWindowVisible(hwnd))})
            if (win32process.GetWindowThreadProcessId(hwnd)[1] == pid
                    and (win32gui.GetClassName(hwnd) == '#32770' or win32gui.GetWindowText(hwnd) == '글자 모양')):
                result['dialog_seen'] = True
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        win32gui.EnumWindows(visit, None)
        write_json(folder / 'dialog.json', result)
    thread = threading.Thread(target=caller, daemon=True)
    thread.start()
    threading.Thread(target=closer, daemon=True).start()
    app.HAction.Run('CharShape')
    deadline = time.monotonic() + 5
    while thread.is_alive() and time.monotonic() < deadline:
        pythoncom.PumpWaitingMessages()
        thread.join(.02)
    if not result.get('dialog_seen'):
        raise RuntimeError(f'실제 대화상자 확인 실패: {result}')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--lock-wait', type=float, default=600)
    parser.add_argument('--phase-timeout', type=float, default=30)
    parser.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if (not os.environ.get('LIVELINK_POC_LOCK_TOKEN') or not LOCK.is_file()
                or os.environ['LIVELINK_POC_LOCK_TOKEN'] != LOCK.read_text(encoding='utf-8')):
            raise RuntimeError('잠금을 소유한 감시 프로세스에서만 worker 실행 가능')
        worker(args.worker.resolve())
        return
    from docfit_core import hwp_process
    folder = (args.out or Path(tempfile.gettempdir()) / ('livelink-c28-' + time.strftime('%Y%m%d-%H%M%S'))).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    with test_lock(args.lock_wait) as token:
        initial = hwp_ids()
        original_hash = digest(SOURCE)
        env = {**os.environ, 'LIVELINK_POC_LOCK_TOKEN': token}
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker', str(folder)], cwd=ROOT, env=env)
        start = time.time()
        try:
            while process.poll() is None:
                time.sleep(.2)
                path = folder / 'result.json'
                report = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
                if time.time() - report.get('heartbeat', start) > args.phase_timeout:
                    terminate_worker(process)
                    report['watchdog_timeout'] = report.get('active', 'startup')
                    write_json(path, report)
                    break
        finally:
            if process.poll() is None:
                terminate_worker(process)
            owned_path = folder / 'owned.json'
            if owned_path.exists():
                pids = set(json.loads(owned_path.read_text())['pids']) - initial
                hwp_process.register_owned(pids)
                cleanup_owned()
            write_json(folder / 'supervisor.json', {'worker_exit': process.returncode,
                       'preexisting_pids': sorted(initial), 'remaining_hwp_pids': sorted(hwp_ids()),
                       'source_sha256': original_hash, 'source_unchanged': digest(SOURCE) == original_hash,
                       'copy_unchanged_on_disk': (digest(folder / 'scratch' / 'sample.hwpx') == original_hash)
                           if (folder / 'scratch' / 'sample.hwpx').exists() else None})
    print(folder)


def terminate_worker(process):
    """venv의 Windows launcher 아래 실제 Python까지 소유 트리만 종료한다."""
    import psutil
    if process.poll() is not None:
        return
    try:
        root = psutil.Process(process.pid)
        members = root.children(recursive=True) + [root]
        for member in members:
            try:
                member.kill()
            except psutil.NoSuchProcess:
                pass
        psutil.wait_procs(members, timeout=5)
    except psutil.NoSuchProcess:
        pass
    process.wait(timeout=5)


if __name__ == '__main__':
    main()
