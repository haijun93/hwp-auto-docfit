"""로컬 브라우저의 반응형 웹 UX 검사. 모의 브리지이며 실제 문서는 처리하지 않는다."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desktop_web_ui import _FILE_DROP_SCRIPT
from scripts.browser_qa import launch_browser


def main():
    from playwright.sync_api import sync_playwright
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(ROOT/'desktop_web')))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = launch_browser(p)
            page = browser.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.add_init_script('''
              window.qaCalls=[];
              window.qaState={files:[{name:'초안.md',path:'C:/fixture.md'}],count:1,mode:'spacing',running:false,can_start:true,
                options:{},profiles:[],range:{enabled:false,start:'1',end:'1'},results:[],stages:[],
                card_options:{spacing_enabled:true,spacing_page_fit:false},
                doc_hints:{show_table_option:false,show_page_range:false,reason:'양식 유지'},zero_click:{pending:false}};
              window.pywebview={api:new Proxy({}, {get:(_,name)=>async(...args)=>{
                window.qaCalls.push([name,...args]);
                if(name==='cancel_zero_click') window.qaState.zero_click={pending:false};
                if(name==='start_zero_click') { window.qaState.running=true; window.qaState.zero_click={pending:false}; }
                return structuredClone(window.qaState);
              }})};
            ''')
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
            page.evaluate("dispatchEvent(new Event('pywebviewready'))")
            page.evaluate(_FILE_DROP_SCRIPT)
            for width in (420, 1280):
                page.set_viewport_size({'width': width, 'height': 1000})
                page.evaluate('navigate(2); render(window.qaState)')
                assert page.locator('#quickOptionsPanel').is_hidden()
                page.locator('#optionsSummary').click()
                assert page.locator('#quickOptionsPanel').is_visible()
                assert page.locator('#tableSpacingOption').is_hidden()
                assert page.locator('#rangeBox').is_hidden()
                page.locator('#optionsSummary').click()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'overflow at {width}'
            # 서식 배지 DOM 위치와 네이티브 경로 수신용 좌표를 공유한다.
            page.evaluate('''() => {
              const r=window.docfitProfileDropRect, data=new DataTransfer();
              data.items.add(new File(['fixture'],'sample.hwpx'));
              document.dispatchEvent(new DragEvent('dragover',{dataTransfer:data,clientX:r[0]+5,clientY:r[1]+5,bubbles:true}));
            }''')
            assert '새 서식' in page.locator('#docfit-file-drop').inner_text()
            page.evaluate("dispatchEvent(new Event('blur'))")
            for cancel in (True, False):
                page.evaluate('''(cancel) => {
                  qaState.running=false; qaState.zero_click={pending:true,token:cancel?'pause':'run',file_name:'초안.md',mode:'spacing',remaining_ms:2500}; render(qaState);
                }''', cancel)
                assert page.locator('#zeroClickBar').is_visible()
                if cancel:
                    page.locator('#pauseAutoRun').click()
                page.wait_for_timeout(2800)
                started = page.evaluate("qaCalls.filter(c=>c[0]==='start_zero_click').length")
                assert started == (0 if cancel else 1), started
            assert not errors, errors
            browser.close()
            print(json.dumps({'ok': True, 'viewports': [420,1280], 'context_options': True,
                              'native_drop_highlight': True, 'cancel': True, 'auto_start_once': True}, ensure_ascii=False))
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
