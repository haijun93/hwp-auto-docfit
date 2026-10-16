"""Start our frozen EXE, verify its visible version title, then stop only that process tree."""
import argparse
import ast
import ctypes
import json
import hashlib
import os
import tempfile
from pathlib import Path
import subprocess
import time


def version_from_source(path):
    for node in ast.parse(Path(path).read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "APP_VERSION" for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("APP_VERSION missing")


def main():
    import win32gui
    import win32process
    from ctypes import wintypes
    parser=argparse.ArgumentParser()
    parser.add_argument("--exe",required=True)
    parser.add_argument("--source",default="hwp-auto-docfit.py")
    parser.add_argument("--report",required=True)
    parser.add_argument("--embedded-runtime",action="store_true")
    args=parser.parse_args()
    exe=Path(args.exe).resolve();version=version_from_source(args.source)
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    found=[]
    def inspect(hwnd,_):
        if not win32gui.IsWindowVisible(hwnd):return
        title=win32gui.GetWindowText(hwnd)
        if f"v{version}" not in title:return
        _,pid=win32process.GetWindowThreadProcessId(hwnd)
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:return
        try:
            name=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(name))
            if kernel.QueryFullProcessImageNameW(handle,0,name,ctypes.byref(size)) and Path(name.value).resolve()==exe:
                found.append({"title":title,"pid":pid})
        finally:kernel.CloseHandle(handle)
    launch_env = dict(os.environ)
    launch_env["DOCFIT_OFFLINE"] = "1"
    if args.embedded_runtime and (exe.parent / "HWP_AutoDocFit_kordoc_runtime.zip").exists():
        raise RuntimeError("Embedded runtime smoke must run without a sidecar ZIP")
    process=subprocess.Popen([str(exe)],env=launch_env)
    try:
        deadline=time.monotonic()+120
        while time.monotonic()<deadline and not found:
            win32gui.EnumWindows(inspect,None)
            if process.poll() is not None and not found:break
            time.sleep(.5)
        result={"ok":bool(found),"version":version,"windows":found}
        if found and args.embedded_runtime:
            home=Path(r"C:\HWP_AUTODOCFIT")
            pack=home/"HWP_AutoDocFit_kordoc_runtime.zip"
            expected=Path("resources/HWP_AutoDocFit_kordoc_runtime.zip.sha256").read_text().split()[0]
            with pack.open("rb") as stream:
                assert hashlib.file_digest(stream,"sha256").hexdigest()==expected
            engine_version=json.loads(Path("kordoc_pack/package.json").read_text())["dependencies"]["kordoc"]
            runtime=home/"kordoc-runtime"/engine_version
            node=runtime/"node/node.exe";cli=runtime/"app/node_modules/kordoc/dist/cli.js"
            observed=subprocess.run([str(node),str(cli),"--version"],check=True,capture_output=True,text=True,timeout=30).stdout.strip()
            assert engine_version in observed
            with tempfile.TemporaryDirectory() as folder:
                markdown=Path(folder)/"offline.md";output=Path(folder)/"offline.hwpx"
                markdown.write_text("# 내장 변환 시험\n\n한글 본문",encoding="utf-8")
                subprocess.run([str(node),str(cli),"generate",str(markdown),"-o",str(output),"--preset","report","--silent"],check=True,timeout=60,env=launch_env)
                assert output.is_file() and output.stat().st_size>0
                # Real bundled Korean OCR, with model downloads explicitly disabled.
                from PIL import Image, ImageDraw, ImageFont
                from docfit_core.network_policy import offline_environment
                ocr_env=offline_environment(launch_env)
                ocr_env["KORDOC_MODEL_CACHE"]=str(runtime/"models")
                image=Image.new("RGB",(1200,300),"white")
                draw=ImageDraw.Draw(image)
                font=ImageFont.truetype(str(Path("flutter_ui/assets/NotoSansKR.ttf").resolve()),48)
                draw.text((40,40),"공원 안내판 철거 계획",fill="black",font=font)
                scan=Path(folder)/"scan.png";parsed=Path(folder)/"scan.md"
                image.save(scan)
                subprocess.run([str(node),str(cli),str(scan),"--ocr","--format","markdown","-o",str(parsed),"--silent"],check=True,timeout=180,env=ocr_env)
                recognized=parsed.read_text(encoding="utf-8")
                assert "공원" in recognized and "계획" in recognized,recognized
                ocr_output=Path(folder)/"ocr.hwpx"
                subprocess.run([str(node),str(cli),"generate",str(parsed),"-o",str(ocr_output),"--preset","report","--silent"],check=True,timeout=60,env=ocr_env)
                from docfit_core.hwpx import inspect_hwpx
                assert "공원" in "\n".join(block.text for block in inspect_hwpx(ocr_output).blocks)
                result["offline_ocr"]={"ok":True,"recognized":recognized.strip(),"model":"PP-OCRv5 Korean"}
                scanned_pdf=Path(folder)/"scan.pdf";parsed_pdf=Path(folder)/"scan-pdf.md"
                image.save(scanned_pdf,"PDF",resolution=150)
                subprocess.run([str(node),str(cli),str(scanned_pdf),"--ocr","--format","markdown","-o",str(parsed_pdf),"--silent"],check=True,timeout=180,env=ocr_env)
                pdf_text=parsed_pdf.read_text(encoding="utf-8")
                assert "공원" in pdf_text and "계획" in pdf_text,pdf_text
                result["offline_ocr"]["scanned_pdf"]=True
                image.close()
            result["embedded_runtime"]={"ok":True,"path":str(runtime),"version":observed,"sidecar_required":False}

        Path(args.report).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        if not found:raise RuntimeError("Frozen EXE did not show the expected version window")
        print(json.dumps(result,ensure_ascii=False))
    except Exception as error:
        result=locals().get("result",{"version":version,"windows":found})
        result.update({"ok":False,"error":f"{type(error).__name__}: {error}"})
        Path(args.report).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        raise
    finally:
        subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],capture_output=True,timeout=15)
    return 0


if __name__=="__main__":raise SystemExit(main())
