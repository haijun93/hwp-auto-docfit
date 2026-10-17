"""QA: compiled Flutter -> local flow iframe -> real Python flow storage.

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
                # The current palette defaults to the basic shapes; flowchart
                # process shapes live in a collapsed group, not the old toolbar.
                frame.get_by_role("button", name="사각형 추가", exact=True).click()
                frame.get_by_label("도형 내용").fill("일반 모드 실제 저장")
                frame.get_by_role("button", name="저장", exact=True).click()
                page.get_by_role("textbox", name="문서 이름").fill("일반 모드 QA")
                page.get_by_role("button", name="저장", exact=True).click()
                page.wait_for_timeout(1000)
                saved = app.flows.list()
                assert len(saved) == 1, saved
                document = app.flows.load(saved[0]["id"])
                assert document["snapshot"]["nodes"][0]["data"]["label"] == "일반 모드 실제 저장"
                assert app.store.read().get("developer_mode", False) is False
                assert not (Path(folder) / "diagrams").exists()
                frame.get_by_role("button", name="PNG 내보내기", exact=True).click()
                page.wait_for_timeout(800)
                exports = list((Path(folder) / "flows" / "exports").glob("*.png"))
                assert len(exports) == 1
                assert exports[0].read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
                frame.get_by_role("button", name="새 문서", exact=True).click()
                frame.locator(".react-flow__node").wait_for(state="detached")
                frame.get_by_role("button", name="열기·삭제", exact=True).click()
                page.wait_for_timeout(400)
                page.get_by_label("일반 모드 QA", exact=True).click()
                frame.locator(".react-flow__node").wait_for()
                assert frame.locator(".react-flow__node").count() == 1
                frame.get_by_role("button", name="열기·삭제", exact=True).click()
                page.get_by_role("button", name="삭제", exact=True).click()
                page.get_by_role("button", name="삭제", exact=True).click()
                page.wait_for_timeout(300)
                assert app.flows.list() == []
                assert not failures, failures
                page.screenshot(path=str(Path(tempfile.gettempdir()) / "docfit-flutter-general-flow.png"))
                print(json.dumps({"general_mode": True, "flutter_iframe": True, "real_python_save": True,
                                  "png_export": True, "reopen_delete": True, "tldraw_storage_created": False, "page_errors": failures}))
                browser.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
