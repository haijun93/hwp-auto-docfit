"""Regression: delayed save ACK must not clear later edits in compiled Flutter.

Requires Playwright, system Chromium, and an already-built Flutter web bundle.
Uses a temporary settings folder, never user data or document processing.
"""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docfit_app.application_service import ApplicationService
from playwright.sync_api import sync_playwright
from browser_qa import launch_browser

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory() as folder:
        saved_started, release_ack = threading.Event(), threading.Event()
        app = ApplicationService(Path(folder) / "settings.json")

        class Handler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                if self.path != "/qa-api":
                    self.send_error(404)
                    return
                try:
                    request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                    result = {"ok": True, "data": app.dispatch(request["method"], request["args"])}
                    if request["method"] == "flow_editor" and request["args"][0] == "save":
                        saved_started.set()
                        if not release_ack.wait(10):
                            raise TimeoutError("test did not release save ACK")
                except Exception as exc:
                    result = {"ok": False, "message": str(exc)}
                payload = json.dumps(result, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(ROOT / "desktop_web/flutter")))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as playwright:
                browser = launch_browser(playwright)
                page = browser.new_page(viewport={"width": 1280, "height": 900}, accept_downloads=True)
                failures = []
                page.on("pageerror", lambda exc: failures.append(str(exc)))
                page.add_init_script("""
                window.addEventListener('flutter-first-frame',()=>window.qaReady=true);
                window.pywebview={api:new Proxy({},{get:(_,method)=>async(...args)=>{
                  const result=await(await fetch('/qa-api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({method,args})})).json();
                  if(!result.ok)throw new Error(result.message);return result.data;
                }})};
                """)
                page.goto(f"http://127.0.0.1:{server.server_port}/")
                page.wait_for_function("window.qaReady===true", timeout=60000)
                page.locator("flt-semantics-placeholder").evaluate("element=>element.click()")
                page.get_by_role("button", name="표/다이어그램", exact=True).click()
                frame = page.frame_locator('iframe[title="표/다이어그램 편집기"]')
                frame.get_by_role("button", name="처리 추가", exact=True).click()
                frame.get_by_label("도형 내용").fill("일반 모드 실제 저장")
                frame.get_by_role("button", name="저장", exact=True).click()
                page.get_by_role("textbox", name="문서 이름").fill("일반 모드 QA")
                page.get_by_role("button", name="저장", exact=True).click()
                assert saved_started.wait(5)
                frame.get_by_label("도형 내용").fill("저장 응답 중 추가한 미저장 문장")
                release_ack.set()
                frame.get_by_role("status").filter(has_text="추가 변경사항을 저장해 주세요.").wait_for()
                saved = app.flows.list()
                document = app.flows.load(saved[0]["id"])
                persisted = document["snapshot"]["nodes"][0]["data"]["label"]
                current = frame.get_by_label("도형 내용").input_value()
                assert persisted != current
                page.mouse.click(28, 28)
                page.get_by_role("button", name="계속 편집", exact=True).wait_for()
                assert page.locator('iframe[title="표/다이어그램 편집기"]').count() == 1
                page.get_by_role("button", name="계속 편집", exact=True).click()
                assert frame.get_by_label("도형 내용").input_value() == current
                assert not failures, failures
                print(json.dumps({"delayed_ack": True, "later_input_preserved": True,
                                  "unsaved_confirmation": True, "page_errors": failures}))
                browser.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
