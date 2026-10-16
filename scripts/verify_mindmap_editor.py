"""Browser gate: drag, nested editing, save/reload and PNG export of mind maps."""
import functools
from http.server import ThreadingHTTPServer
import threading
from playwright.sync_api import sync_playwright
from browser_qa import launch_browser
from verify_flow_editor import Handler, ROOT


def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Handler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser=launch_browser(playwright)
            page=browser.new_page(viewport={"width":1500,"height":1000})
            errors=[]
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{server.server_port}/host.html")
            page.wait_for_function("messages.some(m=>m.type==='ready')")
            frame=page.frame_locator("#editor")
            frame.get_by_role("tab",name="마인드맵",exact=True).click()
            node=frame.locator(".react-flow__node").first
            node.click()
            box=node.bounding_box()
            page.mouse.move(box["x"]+box["width"]/2,box["y"]+box["height"]/2)
            page.mouse.down()
            page.mouse.move(box["x"]+box["width"]/2+100,box["y"]+box["height"]/2+100,steps=15)
            page.mouse.up()
            frame.get_by_label("가지 내용",exact=True).fill("자유 이동 중심")
            frame.get_by_role("button",name="＋ 하위 가지 (Tab)",exact=True).click()
            frame.get_by_label("가지 내용",exact=True).fill("하위 1")
            frame.get_by_role("button",name="＋ 하위 가지 (Tab)",exact=True).click()
            frame.get_by_label("가지 내용",exact=True).fill("하위 2")
            frame.get_by_label("가지 연결선 설명",exact=True).fill("확장 관계")
            page.evaluate("send({type:'save',name:'마인드맵 회귀'})")
            page.wait_for_function("messages.some(m=>m.type==='save_document')")
            saved=page.evaluate("messages.findLast(m=>m.type==='save_document')")
            root=saved["snapshot"]["mindmap"]["root"]
            assert root["text"]=="자유 이동 중심"
            assert "position" in root
            child=next(c for c in root["children"] if c["text"]=="하위 1")
            assert child["children"][0]["text"]=="하위 2"
            assert child["children"][0]["edge"]["label"]=="확장 관계"
            frame.get_by_role("button",name="부모 연결선 삭제 (가지 유지)",exact=True).click()
            page.evaluate("send({type:'load',name:'복원',snapshot:"+__import__("json").dumps(saved["snapshot"])+"})")
            page.wait_for_function("messages.some(m=>m.type==='document_loaded')")
            page.evaluate("send({type:'export_png'})")
            page.wait_for_function("messages.some(m=>m.type==='export_png')",timeout=20000)
            assert not errors,errors
            print("PASS: mindmap drag, nested children, edge editing, save/reload, PNG export")
            browser.close()
    finally:
        server.shutdown();server.server_close()


if __name__=="__main__":
    main()
