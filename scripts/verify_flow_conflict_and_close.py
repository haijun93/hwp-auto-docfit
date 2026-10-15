"""Compiled Flutter QA: stale-save recovery and simulated OS close handshake.

The HTTP adapter replaces only the native host event; actual flow storage and
Flutter routes/messages are used. Windows WebView2 X/Alt+F4 still needs QA.
"""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from docfit_app.application_service import ApplicationService
from playwright.sync_api import sync_playwright
from browser_qa import launch_browser

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory() as folder:
        app = ApplicationService(Path(folder) / 'settings.json')
        host = {'pending': None, 'answers': []}

        class Handler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                if self.path != '/qa-api':
                    self.send_error(404)
                    return
                try:
                    request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                    method, args = request['method'], request['args']
                    if method == 'enable_close_guard':
                        value = {'ok': True}
                    elif method == 'resolve_dialog':
                        assert args[0] == host['pending']['id']
                        host['answers'].append(args[1])
                        host['pending'] = None
                        value = {'accepted': args[1]}
                    elif method == 'get_pending_dialog':
                        value = host['pending']
                    else:
                        value = app.dispatch(method, args)
                        if method == 'get_state':
                            value['pending_dialog'] = host['pending']
                    result = {'ok': True, 'data': value}
                except Exception as exc:
                    result = {'ok': False, 'message': str(exc)}
                data = json.dumps(result, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(
            Handler, directory=str(ROOT / 'desktop_web/flutter')))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as playwright:
                browser = launch_browser(playwright)
                page = browser.new_page(viewport={'width': 1280, 'height': 900})
                failures = []
                page.on('pageerror', lambda exc: failures.append(str(exc)))
                page.add_init_script("""
                window.addEventListener('flutter-first-frame',()=>window.qaReady=true);
                window.pywebview={api:new Proxy({},{get:(_,method)=>async(...args)=>{
                  const r=await(await fetch('/qa-api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({method,args})})).json();
                  if(!r.ok)throw new Error(r.message);return r.data;
                }})};
                """)
                page.goto(f'http://127.0.0.1:{server.server_port}/')
                page.wait_for_function('window.qaReady===true', timeout=60000)
                page.locator('flt-semantics-placeholder').evaluate('element=>element.click()')
                page.get_by_role('button', name='표/다이어그램', exact=True).click()
                frame = page.frame_locator('iframe[title="표/다이어그램 편집기"]')
                frame.get_by_role('button', name='처리 추가', exact=True).click()
                frame.get_by_label('도형 내용').fill('첫 저장')

                def save(name):
                    frame.get_by_role('button', name='저장', exact=True).click()
                    page.get_by_role('textbox', name='문서 이름').fill(name)
                    page.get_by_role('button', name='저장', exact=True).click()

                save('원본 흐름도')
                page.locator('span').filter(has_text='흐름도를 이 PC에 저장했어요.').wait_for()
                original = app.flows.load(app.flows.list()[0]['id'])
                app.flows.save(original['id'], '다른 편집자의 최신본', original['snapshot'], original['revision'])
                frame.get_by_label('도형 내용').fill('충돌 시 복구할 편집')
                save('오래된 편집')
                page.locator('span').filter(has_text='다른 편집자가 문서를 변경했습니다.').wait_for()
                assert app.flows.load(original['id'])['name'] == '다른 편집자의 최신본'
                page.get_by_role('button', name='사본으로 저장', exact=True).click()
                page.get_by_role('textbox', name='문서 이름').fill('복구 사본')
                page.get_by_role('button', name='저장', exact=True).click()
                # Wait for the ACK before attempting to edit/close again.
                page.get_by_text('복구 사본', exact=True).wait_for()
                copies = [item for item in app.flows.list() if item['id'] != original['id']]
                assert len(copies) == 1
                assert app.flows.load(copies[0]['id'])['snapshot']['nodes'][0]['data']['label'] == '충돌 시 복구할 편집'
                frame.get_by_label('도형 내용').fill('종료 확인용 미저장 입력')
                host['pending'] = {'id': 'close-cancel', 'kind': 'app_close'}
                page.get_by_role('button', name='계속 편집', exact=True).wait_for()
                page.get_by_role('button', name='계속 편집', exact=True).click()
                page.locator('span').filter(has_text='종료를 취소했습니다.').wait_for()
                assert host['answers'] == [False]
                assert frame.get_by_label('도형 내용').input_value() == '종료 확인용 미저장 입력'
                host['pending'] = {'id': 'close-discard', 'kind': 'app_close'}
                page.get_by_role('button', name='변경사항 버리기', exact=True).click()
                page.locator('iframe[title="표/다이어그램 편집기"]').wait_for(state='detached')
                page.wait_for_timeout(500)
                assert host['answers'] == [False, True], host
                assert app.flows.load(original['id'])['name'] == '다른 편집자의 최신본'
                assert not failures, failures
                print(json.dumps({'stale_save_rejected': True, 'copy_recovered': True,
                                  'host_close_cancel_preserves_input': True,
                                  'explicit_discard_disposes_editor_before_host_ack': True,
                                  'page_errors': failures}))
                browser.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
