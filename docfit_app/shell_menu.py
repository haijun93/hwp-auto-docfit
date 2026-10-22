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
        result[base] = {'MUIVerb': '한글편집 후처리', 'SubCommands': '', 'DocFitCommand': command}
        actions = [('pdf', 'PDF로 변환'), ('png', '그림(PNG)으로 변환')]
        if ext in ('.hwp', '.hwpx'):
            if ext == '.hwp':
                actions.insert(1, ('hwpx', 'HWPX로 변환'))
            actions.append(('open', '한글편집 후처리로 열기'))
        elif ext == '.pdf':
            actions = [('pdfz', 'PDF 압축'), ('png', '그림(PNG)으로 변환')]
        else:
            actions = [('pdf', 'PDF로 변환')]
        for index, (target, label) in enumerate(actions):
            key = base + f'\\shell\\{index:02d}_{target}'
            result[key] = {'MUIVerb': label}
            value = f'{command} "%1"' if target == 'open' else f'{command} convert "%1" --to {target} --notify'
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
