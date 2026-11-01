"""같은 사용자 앱에 '열기' 파일을 전달하는 원자적 요청 큐."""
import json
import os
import sys
import uuid
from pathlib import Path


def _folder():
    return Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'HWP_AutoDocFit' / 'open_requests'


def forward(files):
    rename, paths = split_rename_arguments(files)
    files = [str(Path(f).resolve()) for f in paths if Path(f).is_file()]
    if not files:
        return
    folder = _folder()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (uuid.uuid4().hex + '.tmp')
    path.write_text(json.dumps({'rename': rename, 'paths': files}, ensure_ascii=False), encoding='utf-8')
    path.replace(path.with_suffix('.json'))


def split_rename_arguments(arguments):
    """Separate `--rename <paths>` from ordinary document-open arguments."""
    values = list(arguments or [])
    if '--rename' not in values:
        return False, values
    index = values.index('--rename')
    paths = values[index + 1:]
    return True, [value for value in paths if isinstance(value, str) and not value.startswith('--')]


def _deliver(gui, paths, rename=False):
    if rename:
        # 화면 쪽 다음 상태 조회가 가져간다(desktop_web_ui._drain_rename_paths).
        queue = getattr(gui, '_rename_startup_paths', None)
        if isinstance(queue, list):
            queue.extend(paths)
        else:
            gui._rename_startup_paths = list(paths)
    else:
        for value in paths:
            if isinstance(value, str):
                gui.파일추가(value)


def start(gui):
    rename, paths = split_rename_arguments(sys.argv[1:])
    _deliver(gui, paths if rename else [value for value in paths if Path(value).is_file()], rename)

    def poll():
        folder = _folder()
        if folder.exists() and not gui.running:
            for path in sorted(folder.glob('*.json')):
                try:
                    values = json.loads(path.read_text(encoding='utf-8'))
                    if isinstance(values, dict) and isinstance(values.get('paths'), list):
                        _deliver(gui, values['paths'], values.get('rename') is True)
                    elif isinstance(values, list):
                        _deliver(gui, values)
                    path.unlink()
                except (ValueError, UnicodeError):
                    # 깨진 요청을 격리하고 다음 정상 요청을 계속 처리한다.
                    try:
                        path.replace(path.with_suffix('.bad'))
                    except OSError:
                        pass
                except OSError:
                    pass
        gui.root.after(500, poll)
    gui.root.after(500, poll)
