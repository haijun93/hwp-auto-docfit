"""Render Flutter UI with a fake bridge; never invokes document processing.

Optional QA dependency: pip install playwright (uses installed Microsoft Edge).
Screenshots are saved in reports/flutter-ui.
"""

import functools
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright


def main():
    root = Path(__file__).resolve().parents[1]
    web = root / 'desktop_web' / 'flutter'
    output = root / 'reports' / 'flutter-ui'
    output.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(web))
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    errors = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            for width, height in [(1040, 800), (420, 820)]:
                page = browser.new_page(viewport={'width': width, 'height': height})
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.route('**/*', lambda route: route.continue_()
                           if route.request.url.startswith('http://127.0.0.1:')
                           else route.abort())
                page.add_init_script('''
                    window.addEventListener('flutter-first-frame', () => window.uiReady = true);
                    const state = {files: [], mode: 'unify', running: false,
                      range: {enabled: false, start: '1', end: '1'},
                      progress: {steps: ['열기','서식','자간','페이지 배치','저장'], visited: []},
                      results: [], version: 'UI PREVIEW', status: '문서를 선택하세요.'};
                    window.pywebview = {api: new Proxy({}, {get: (_, method) => async (...args) => {
                      if (method === 'add_files') state.files = [{name: '검토할 문서.hwpx', path: 'preview.hwpx'}];
                      if (method === 'set_mode') state.mode = args[0];
                      if (method === 'set_range') state.range = {enabled: args[0], start: args[1], end: args[2]};
                      if (method === 'next_job') state.files = [];
                      return JSON.parse(JSON.stringify(state));
                    }})};
                ''')
                page.goto(f'http://127.0.0.1:{server.server_port}/')
                page.wait_for_function('window.uiReady === true', timeout=90000)
                page.wait_for_timeout(1200)
                page.screenshot(path=str(output / f'documents-{width}.png'))
                # CanvasKit paints to canvas; widget tests separately verify
                # semantic button names and command routing.
                page.mouse.click(90, 231) if width >= 1000 else page.mouse.click(width * .375, 100)
                page.wait_for_timeout(400)
                page.screenshot(path=str(output / f'options-{width}.png'))
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print(json.dumps({'screenshots': str(output), 'errors': errors}, ensure_ascii=True))
    if errors:
        raise RuntimeError('Flutter browser errors detected')


if __name__ == '__main__':
    main()
