"""Verify rendered Flutter content and native close on the actual Windows EXE.

Uses WebView2's loopback CDP endpoint, never HWP COM or user documents.
The title-only smoke cannot distinguish an empty WebView from a usable app.
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import uuid


def _cdp_diagnostics(process, port):
    """Record why CDP is unreachable: app alive?, WebView2 browser args, listening ports."""
    info = {'app_exit_code': process.poll(), 'port': port, 'browsers': [], 'listening': []}
    try:
        import psutil
        tree = [psutil.Process(process.pid)]
        tree += tree[0].children(recursive=True)
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if (proc.info['name'] or '').lower().startswith('msedgewebview2'):
                line = ' '.join(proc.info['cmdline'] or [])
                if '--type=' not in line:
                    info['browsers'].append(line[:600])
        pids = {p.pid for p in tree}
        info['tree'] = sorted({p.name() for p in tree})
        for conn in psutil.net_connections('tcp'):
            if conn.status == 'LISTEN' and conn.laddr and conn.laddr.ip in ('127.0.0.1', '::1', '0.0.0.0'):
                info['listening'].append([conn.pid, conn.laddr.port, conn.pid in pids])
    except Exception as error:
        info['diagnostic_error'] = repr(error)
    return info


def main():
    from PIL import Image
    from playwright.sync_api import sync_playwright
    import win32gui
    import win32process

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--hard-timeout', type=float, default=240)
    parser.add_argument('--unresponsive', action='store_true', help='remove frontend close polling after first frame')
    parser.add_argument('--legacy-frame', action='store_true', help='diagnose pre-2.0.1 bundles without a first-frame marker')
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    env = dict(os.environ)
    env['DOCFIT_OFFLINE'] = '1'
    env['DOCFIT_LAUNCHER_MUTEX_NAME'] = 'Local\\DocFitSmoke_' + uuid.uuid4().hex
    env['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = f'--remote-debugging-port={port}'
    env['DOCFIT_SMOKE_CDP_PORT'] = str(port)  # honoured by the app via pywebview settings
    # A WebView2 browser already running on the same user data folder (e.g. the
    # previous smoke step's app) would adopt this window and ignore the CDP port.
    import tempfile
    env['WEBVIEW2_USER_DATA_FOLDER'] = tempfile.mkdtemp(prefix='docfit-smoke-webview-')
    process = subprocess.Popen([str(args.exe.resolve())], env=env)
    result = {'ok': False, 'exe': str(args.exe.resolve()), 'pid': process.pid, 'console': [], 'errors': [], 'failed_requests': []}
    app_pid = process.pid
    # Hard limit: Playwright evaluate/cleanup have no timeout of their own. Record
    # the stage that hung instead of blocking CI for hours.
    import threading
    def _hung():
        result['error'] = f"Timeout after {args.hard_timeout}s at stage {result.get('stage')}"
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False), flush=True)
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=15)
        os._exit(1)
    watchdog = threading.Timer(args.hard_timeout, _hung)
    watchdog.daemon = True
    watchdog.start()
    started = time.monotonic()
    try:
        with sync_playwright() as playwright:
            result['stage'] = 'cdp_connect'
            deadline = time.monotonic() + 120
            while True:
                try:
                    browser = playwright.chromium.connect_over_cdp(f'http://127.0.0.1:{port}', timeout=2000)
                    break
                except Exception:
                    if time.monotonic() >= deadline:
                        result['cdp_diagnostics'] = _cdp_diagnostics(process, port)
                        raise RuntimeError('WebView2 CDP did not start')
                    time.sleep(.2)
            result['stage'] = 'attach_page'
            page = browser.contexts[0].pages[0]
            page.on('console', lambda event: result['console'].append({'type': event.type, 'text': event.text}))
            page.on('pageerror', lambda event: result['errors'].append(str(event)))
            page.on('requestfailed', lambda request: result['failed_requests'].append({'url': request.url, 'reason': request.failure}))
            result['stage'] = 'first_frame'
            page.wait_for_function(
                '!!document.querySelector("flutter-view")' if args.legacy_frame
                else 'window.docfitFirstFrame === true', timeout=90000)
            page.wait_for_function('window.pywebview && typeof window.pywebview.api.get_state === "function"', timeout=15000)
            result['stage'] = 'get_state'
            state = page.evaluate('window.pywebview.api.get_state()')
            result['version'] = state.get('version')
            result['url'] = page.url
            result['first_frame_ms'] = round((time.monotonic() - started) * 1000)
            page.wait_for_timeout(1000)
            result['stage'] = 'screenshot'
            screenshot = page.screenshot()
            args.report.with_suffix('.png').write_bytes(screenshot)
            picture = Image.open(io.BytesIO(screenshot)).convert('RGB')
            pixels = list(picture.resize((160, 120)).getdata())
            # Require dark text/icons as well as a first-frame event. A solid
            # loading/error/background canvas must not satisfy this gate.
            ink = sum(max(pixel) < 180 for pixel in pixels) / len(pixels)
            result['ink_fraction'] = ink
            if ink < .005 or result['errors']:
                raise RuntimeError('Flutter did not paint usable content without runtime errors')
            if args.unresponsive:
                page.evaluate('window.pywebview.api.get_state = () => new Promise(() => {})')
            result['stage'] = 'find_window'
            candidates = []
            def inspect(hwnd, _):
                if win32gui.IsWindowVisible(hwnd) and '한글편집 후처리' in win32gui.GetWindowText(hwnd):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    candidates.append((hwnd, pid))
            win32gui.EnumWindows(inspect, None)
            # CDP provides the browser owner PID through the observed native
            # window only when unique; never close another running instance.
            matches = [(hwnd, pid) for hwnd, pid in candidates if pid == process.pid]
            if not matches:
                # Smart launcher starts app_main.exe in its cache. Match its
                # per-launch mutex environment through the process tree.
                import psutil
                descendants = {item.pid for item in psutil.process_iter(['ppid'])
                               if item.info['ppid'] == process.pid}
                matches = [(hwnd, pid) for hwnd, pid in candidates if pid in descendants]
            if len(matches) != 1:
                raise RuntimeError(f'Expected one owned application window, found {len(matches)}')
            hwnd, app_pid = matches[0]
            result['stage'] = 'native_close'
            close_started = time.monotonic()
            win32gui.PostMessage(hwnd, 0x0010, 0, 0)  # WM_CLOSE: same native path as X
            while win32gui.IsWindow(hwnd) and time.monotonic() - close_started < 12:
                time.sleep(.1)
            if win32gui.IsWindow(hwnd):
                raise RuntimeError('Native close did not close the window')
            result['close_ms'] = round((time.monotonic() - close_started) * 1000)
            import psutil
            try:
                psutil.Process(app_pid).wait(timeout=10)
            except psutil.NoSuchProcess:
                pass
            result['stage'] = 'done'
            result['ok'] = True
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    finally:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        if not result['ok']:
            for pid in {process.pid, app_pid}:
                subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], capture_output=True, timeout=15)
    watchdog.cancel()
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
