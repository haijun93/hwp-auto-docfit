"""현재 사용자 탐색기 메뉴. registry 인자로 가짜 winreg를 주입할 수 있다."""
import os
import sys
from pathlib import Path

ROOT = r'Software\Classes\SystemFileAssociations'
MENU = 'HwpAutoDocFit'
EXTENSIONS = ('.hwp', '.hwpx', '.pdf', '.png', '.jpg', '.jpeg')


def launch_command():
    launcher = os.environ.get('DOCFIT_LAUNCHER_PATH')
    if launcher:
        return [launcher]
    if getattr(sys, 'frozen', False):
        return [sys.executable]
    return [sys.executable, str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py')]


def _registry(registry):
    if registry is None:
        import winreg
        return winreg
    return registry


def _command(exe_path):
    parts = [os.fspath(exe_path)] if isinstance(exe_path, (str, os.PathLike)) else list(exe_path)
    if not parts or any('"' in part or '\x00' in part for part in parts):
        raise ValueError('실행 파일 경로를 확인해 주세요.')
    # 공백 없는 실행 파일도 항상 따옴표로 감싼다.
    return ' '.join('"' + part + '"' for part in parts)


def menu_entries(exe_path):
    command = _command(exe_path)
    result = {}
    for ext in EXTENSIONS:
        base = ROOT + '\\' + ext + '\\shell\\' + MENU
        result[base] = {
            'MUIVerb': '한글편집 후처리',
            'SubCommands': '',
            'DocFitCommand': command,
            'MultiSelectModel': 'Player',
        }
        if ext == '.hwp':
            actions = [
                ('pdf', 'PDF로 변환(여러 개)', 'pdf'),
                ('hwpx', 'HWPX로 변환(여러 개)', 'hwpx'),
                ('pdfm', 'PDF 하나로 합치기', 'pdfm'),
                ('png', '그림(PNG)으로 변환', None),
                ('open', '한글편집 후처리로 열기', None),
            ]
        elif ext == '.hwpx':
            actions = [
                ('pdf', 'PDF로 변환', 'pdf'),
                ('pdfm', 'PDF 하나로 합치기', 'pdfm'),
                ('png', '그림(PNG)으로 변환', None),
                ('open', '한글편집 후처리로 열기', None),
            ]
        elif ext == '.pdf':
            actions = [
                ('pdfm', 'PDF 하나로 합치기', 'pdfm'),
                ('pdfz', 'PDF 압축', None),
                ('png', '그림(PNG)으로 변환', None),
            ]
        else:
            actions = [
                ('pdf', 'PDF로 변환', None),
                ('pdfm', 'PDF 하나로 합치기', 'pdfm'),
            ]
        for index, (target, label, collect) in enumerate(actions):
            key = base + f'\\shell\\{index:02d}_{target}'
            result[key] = {'MUIVerb': label, 'MultiSelectModel': 'Player'}
            if target == 'open':
                value = f'{command} "%1"'
            elif collect:
                value = f'{command} convert "%1" --to {target} --collect {collect} --notify'
            else:
                value = f'{command} convert "%1" --to {target} --notify'
            result[key + r'\command'] = {'': value}
    return result


def register(exe_path, *, registry=None):
    reg = _registry(registry)
    for path, values in menu_entries(exe_path).items():
        with reg.CreateKey(reg.HKEY_CURRENT_USER, path) as key:
            for name, value in values.items():
                reg.SetValueEx(key, name, 0, reg.REG_SZ, value)


def unregister(*, registry=None):
    reg = _registry(registry)

    def delete(path):
        try:
            with reg.OpenKey(reg.HKEY_CURRENT_USER, path, 0, reg.KEY_READ | reg.KEY_WRITE) as key:
                children = []
                index = 0
                while True:
                    try:
                        children.append(reg.EnumKey(key, index))
                        index += 1
                    except OSError:
                        break
            for child in children:
                delete(path + '\\' + child)
            reg.DeleteKey(reg.HKEY_CURRENT_USER, path)
        except FileNotFoundError:
            pass
    for ext in EXTENSIONS:
        delete(ROOT + '\\' + ext + '\\shell\\' + MENU)


def status(*, registry=None):
    reg = _registry(registry)
    installed, command = False, None
    for ext in EXTENSIONS:
        try:
            with reg.OpenKey(reg.HKEY_CURRENT_USER, ROOT + '\\' + ext + '\\shell\\' + MENU) as key:
                installed = True
                command = reg.QueryValueEx(key, 'DocFitCommand')[0]
        except FileNotFoundError:
            pass
    return {'registered': installed, 'command': command}


def refresh_registered(*, registry=None):
    state = status(registry=registry)
    command = launch_command()
    if state['registered'] and state['command'] != _command(command):
        register(command, registry=registry)
