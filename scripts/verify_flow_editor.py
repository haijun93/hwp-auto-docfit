"""Browser integration gate for the local general-mode flow editor.

Run with repository Python and Playwright installed; Chromium must be available.
No external service, tldraw runtime or application settings are required.
"""
import base64
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import struct
import threading
import tempfile

from playwright.sync_api import sync_playwright
from browser_qa import launch_browser

ROOT = Path(__file__).resolve().parents[1] / "flutter_ui" / "assets"
HOST = b"""<!doctype html><html><body style="margin:0"><iframe id="editor"
src="/flow_editor/index.html" style="width:100vw;height:100vh;border:0"
sandbox="allow-scripts allow-same-origin"></iframe><script>
window.messages=[];
window.addEventListener('message',e=>{
 if(e.origin===location.origin&&e.source===editor.contentWindow)messages.push(e.data);
});
window.send=message=>editor.contentWindow.postMessage(message,location.origin);
</script></body></html>"""


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/host.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HOST)
        else:
            super().do_GET()

    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = launch_browser(playwright)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            failures = []
            requests = []
            page.on("pageerror", lambda error: failures.append(str(error)))
            page.on("request", lambda request: requests.append(request.url))
            page.goto(f"http://127.0.0.1:{server.server_port}/host.html")
            page.wait_for_function("messages.some(m=>m.type==='ready')")
            frame = page.frame_locator("#editor")
            page.evaluate("send({type:'apply_template',template:'complaint'})")
            frame.locator(".react-flow__node").first.wait_for()
            assert frame.locator(".react-flow__node").count() == 6
            assert frame.locator(".react-flow__edge").count() == 6
            frame.locator(".react-flow__node").first.click()
            frame.get_by_label("도형 내용").fill("민원 접수 <검증>")
            frame.get_by_label("도형 배경").select_option("green")
            page.evaluate("send({type:'save',name:'브라우저 회귀'})")
            page.wait_for_function("messages.some(m=>m.type==='save_document')")
            saved = page.evaluate("messages.findLast(m=>m.type==='save_document')")
            assert any(n["data"]["label"] == "민원 접수 <검증>" for n in saved["snapshot"]["nodes"])
            assert any(n["data"]["color"] == "green" and n["data"]["label"] == "민원 접수 <검증>" for n in saved["snapshot"]["nodes"])
            assert saved["snapshot"]["format"] == "docfit-flow"
            page.evaluate("send({type:'new'})")
            page.wait_for_timeout(100)
            assert frame.locator(".react-flow__node").count() == 0
            page.evaluate("snapshot=>send({type:'load',name:'복원',snapshot})", saved["snapshot"])
            page.wait_for_function("messages.some(m=>m.type==='document_loaded')")
            assert frame.locator(".react-flow__node").count() == 6
            frame.get_by_role("button", name="처리 추가", exact=True).click()
            assert frame.locator(".react-flow__node").count() == 7
            frame.get_by_role("button", name="실행 취소 (Ctrl+Z)", exact=True).click()
            assert frame.locator(".react-flow__node").count() == 6
            frame.get_by_role("button", name="다시 실행 (Ctrl+Y)", exact=True).click()
            assert frame.locator(".react-flow__node").count() == 7
            frame.locator(".react-flow__node").first.click()
            handle = frame.locator(".react-flow__node").first.locator(".react-flow__resize-control.handle.bottom.right")
            bounds = handle.bounding_box()
            assert bounds
            page.mouse.move(bounds["x"] + bounds["width"] / 2, bounds["y"] + bounds["height"] / 2)
            page.mouse.down()
            page.mouse.move(bounds["x"] + 70, bounds["y"] + 50, steps=8)
            page.mouse.up()
            page.evaluate("send({type:'save',name:'크기 검증'})")
            page.wait_for_function("messages.filter(m=>m.type==='save_document').length===2")
            resized = page.evaluate("messages.findLast(m=>m.type==='save_document').snapshot.nodes[0].width")
            assert resized > 220, resized
            frame.get_by_role("button", name="실행 취소 (Ctrl+Z)", exact=True).click()
            page.evaluate("send({type:'save',name:'크기 복원'})")
            page.wait_for_function("messages.filter(m=>m.type==='save_document').length===3")
            assert page.evaluate("messages.findLast(m=>m.type==='save_document').snapshot.nodes[0].width") == 220
            page.evaluate("send({type:'new'})")
            frame.locator(".react-flow__node").wait_for(state="detached")
            frame.get_by_role("button", name="처리 추가", exact=True).click()
            frame.get_by_label("도형 내용").fill("한글" * 200)
            frame.locator(".react-flow__controls-fitview").click()
            page.evaluate("send({type:'save',name:'긴 문장'})")
            page.wait_for_function("messages.filter(m=>m.type==='save_document').length===4")
            snapshot = page.evaluate("messages.findLast(m=>m.type==='save_document').snapshot")
            rect = frame.locator(".react-flow__node").first.bounding_box()
            scale = rect["width"] / snapshot["nodes"][0]["width"]
            spans = frame.locator(".node-lines > span")
            assert spans.count() > 1
            for index in range(spans.count()):
                box = spans.nth(index).bounding_box()
                assert box["x"] >= rect["x"] + 14 * scale
                assert box["x"] + box["width"] <= rect["x"] + rect["width"] - 14 * scale
                assert box["y"] >= rect["y"] + 10 * scale
                assert box["y"] + box["height"] <= rect["y"] + rect["height"] - 10 * scale
            page.evaluate("send({type:'export_png'})")
            page.wait_for_function("messages.some(m=>m.type==='export_png')", timeout=30000)
            png = base64.b64decode(page.evaluate("messages.findLast(m=>m.type==='export_png').base64"))
            assert png[:8] == b"\x89PNG\r\n\x1a\n"
            width, height = struct.unpack(">II", png[16:24])
            assert width > 500 and height > 500
            assert not failures, failures
            assert all(url.startswith((f"http://127.0.0.1:{server.server_port}/", f"blob:http://127.0.0.1:{server.server_port}/")) for url in requests), requests
            page.screenshot(path=str(Path(tempfile.gettempdir()) / "docfit-flow-editor.png"))
            print(json.dumps({"templates": 10, "decision_nodes": 6, "decision_edges": 6,
                              "round_trip": True, "undo_redo": True, "long_korean_safe": True, "png_size": [width, height],
                              "external_requests": 0, "page_errors": failures}, ensure_ascii=False))
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
