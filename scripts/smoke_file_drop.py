"""Exercise native WebView2 file-drop paths over the built Flutter canvas.

Uses browser drag events via CDP; no user documents are opened or processed.
"""
import json
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import webview
from desktop_web_ui import _bind_file_drop, _resource_path


def main():
    received = []
    finished = threading.Event()
    report = {'passed': False}
    class Bridge:
        def add_paths(self, paths):
            received.extend(paths)
            finished.set()
    class PreviewApi:
        def get_state(self):
            return {'files': [{'name': Path(path).name, 'path': path} for path in received],
                    'mode': 'unify', 'running': False, 'results': [], 'version': 'DROP TEST',
                    'range': {'enabled': False, 'start': '1', 'end': '1'},
                    'progress': {'steps': [], 'visited': []}}
    window = webview.create_window('DocFit file-drop test', str(_resource_path()),
                                   js_api=PreviewApi(), width=1040, height=800, hidden=True)
    def run():
        try:
            from System import Func, Object
            deadline = time.monotonic() + 45
            while not window.evaluate_js("document.querySelector('flutter-view') !== null"):
                if time.monotonic() >= deadline:
                    raise TimeoutError('Flutter did not load')
                time.sleep(.2)
            _bind_file_drop(window, Bridge())
            # Injecting twice must not duplicate overlay/capture listeners.
            from desktop_web_ui import _FILE_DROP_SCRIPT
            window.run_js(_FILE_DROP_SCRIPT)
            assert window.evaluate_js("document.querySelectorAll('#docfit-file-drop').length") == 1
            files = [str((ROOT / 'HANDOVER.md').resolve()),
                     str((ROOT / 'README.md').resolve())]
            assert all(Path(path).is_file() for path in files)
            def dispatch(kind):
                payload = json.dumps({'type': kind, 'x': 600, 'y': 500,
                                      'data': {'items': [], 'files': files, 'dragOperationsMask': 1}})
                def send():
                    return window.native.webview.CoreWebView2.CallDevToolsProtocolMethodAsync(
                        'Input.dispatchDragEvent', payload)
                task = window.native.Invoke(Func[Object](send))
                if not task.Wait(10000):
                    raise TimeoutError('CDP drag event timed out')
                return task.Result
            dispatch('dragEnter')
            dispatch('dragOver')
            assert window.evaluate_js("document.getElementById('docfit-file-drop').style.display") == 'flex'
            dispatch('drop')
            assert finished.wait(10), 'Native drop callback did not arrive'
            assert received == files, (received, files)
            assert window.evaluate_js("document.getElementById('docfit-file-drop').style.display") == 'none'
            report.update(passed=True, received_files=len(received), native_paths_match=True)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            report['error'] = repr(exc)
        finally:
            window.destroy()
    window.events.loaded += run
    webview.start(gui='edgechromium', http_server=True)
    print(json.dumps(report))
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
