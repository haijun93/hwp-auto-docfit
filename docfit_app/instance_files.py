"""같은 사용자 앱에 '열기' 파일을 전달하는 원자적 요청 큐."""
import json
import os
import sys
import uuid
from pathlib import Path


def _folder():
    return Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'HWP_AutoDocFit' / 'open_requests'


def forward(files):
    files = [str(Path(f).resolve()) for f in files if Path(f).is_file()]
    if not files:
        return
    folder = _folder()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (uuid.uuid4().hex + '.tmp')
    path.write_text(json.dumps(files, ensure_ascii=False), encoding='utf-8')
    path.replace(path.with_suffix('.json'))


def start(gui):
    for value in sys.argv[1:]:
        if Path(value).is_file():
            gui.파일추가(value)

    def poll():
        folder = _folder()
        if folder.exists() and not gui.running:
            for path in sorted(folder.glob('*.json')):
                try:
                    values = json.loads(path.read_text(encoding='utf-8'))
                    if isinstance(values, list):
                        for value in values:
                            if isinstance(value, str):
                                gui.파일추가(value)
                    path.unlink()
                except (OSError, ValueError):
                    pass
        gui.root.after(500, poll)
    gui.root.after(500, poll)
