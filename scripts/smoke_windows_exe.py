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
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


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
    parser.add_argument("--smart-launcher",action="store_true",help="accept the cached app_main.exe child of this launcher")
    parser.add_argument("--require-launcher-splash",action="store_true",help="fail unless the first-run splash is visible")
    args=parser.parse_args()
    exe=Path(args.exe).resolve();version=version_from_source(args.source)
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    found=[]
    splash_state={"ready_ms":None}
    def inspect(hwnd,_):
        if not win32gui.IsWindowVisible(hwnd):return
        title=win32gui.GetWindowText(hwnd)
        if f"v{version}" not in title:return
        _,pid=win32process.GetWindowThreadProcessId(hwnd)
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:return
        try:
            name=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(name))
            if kernel.QueryFullProcessImageNameW(handle,0,name,ctypes.byref(size)):
                image=Path(name.value).resolve()
                matches=image==exe
                if args.smart_launcher:
                    cache_root=(Path(os.environ["LOCALAPPDATA"])/"HWP_AutoDocFit").resolve()
                    matches=matches or (image.name.lower()=="app_main.exe" and image.parent.parent==cache_root and image.parent.name.startswith("app_v"))
                if matches:found.append({"title":title,"pid":pid,"image":str(image)})
        finally:kernel.CloseHandle(handle)
    def inspect_splash(hwnd,_):
        if splash_state["ready_ms"] is not None or not win32gui.IsWindowVisible(hwnd):return
        title=win32gui.GetWindowText(hwnd)
        if "실행 준비" not in title:return
        _,pid=win32process.GetWindowThreadProcessId(hwnd)
        if pid==process.pid:
            splash_state["ready_ms"]=round((time.perf_counter()-process_started)*1000,2)
    launch_env = dict(os.environ)
    launch_env["DOCFIT_OFFLINE"] = "1"
    if args.embedded_runtime and (exe.parent / "HWP_AutoDocFit_kordoc_runtime.zip").exists():
        raise RuntimeError("Embedded runtime smoke must run without a sidecar ZIP")
    process_started=time.perf_counter()
    process=subprocess.Popen([str(exe)],env=launch_env)
    try:
        deadline=time.monotonic()+120
        while time.monotonic()<deadline and not found:
            if args.require_launcher_splash:win32gui.EnumWindows(inspect_splash,None)
            win32gui.EnumWindows(inspect,None)
            if process.poll() is not None and not found and not args.smart_launcher:break
            time.sleep(.05)
        result={"ok":bool(found),"version":version,"windows":found,
                "window_ready_ms":round((time.perf_counter()-process_started)*1000,2) if found else None,
                "smart_launcher":bool(args.smart_launcher),
                "first_run_splash_ms":splash_state["ready_ms"]}
        if found and args.embedded_runtime:
            home=Path(r"C:\HWP_AUTODOCFIT")
            pack=home/"HWP_AutoDocFit_kordoc_runtime.zip"
            expected=Path("resources/HWP_AutoDocFit_kordoc_runtime.zip.sha256").read_text().split()[0]
            with pack.open("rb") as stream:
                assert hashlib.file_digest(stream,"sha256").hexdigest()==expected
            engine_version=json.loads(Path("kordoc_pack/package.json").read_text())["dependencies"]["kordoc"]
            runtime=home/"kordoc-runtime"/engine_version
            node=runtime/"node/node.exe";cli=runtime/"app/node_modules/kordoc/dist/cli.js"
            # Startup deploys the verified embedded runtime on a daemon thread so
            # the UI can appear first. Do not race that extraction in this smoke test.
            runtime_deadline=time.monotonic()+180
            while time.monotonic()<runtime_deadline and not (node.is_file() and cli.is_file()):
                time.sleep(.5)
            if not (node.is_file() and cli.is_file()):
                raise FileNotFoundError(f"Embedded runtime deployment did not finish: {runtime}")
            observed=subprocess.run([str(node),str(cli),"--version"],check=True,capture_output=True,text=True,timeout=30).stdout.strip()
            assert engine_version in observed
            with tempfile.TemporaryDirectory() as folder:
                markdown=Path(folder)/"offline.md";output=Path(folder)/"offline.hwpx"
                markdown.write_text("# 내장 변환 시험\n\n한글 본문",encoding="utf-8")
                subprocess.run([str(node),str(cli),"generate",str(markdown),"-o",str(output),"--preset","report","--silent"],check=True,timeout=60,env=launch_env)
                assert output.is_file() and output.stat().st_size>0
            from scripts.verify_runtime_ocr import verify_ocr
            result["offline_ocr"] = verify_ocr(runtime)
            result["embedded_runtime"]={"ok":True,"path":str(runtime),"version":observed,"sidecar_required":False}

        Path(args.report).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        if not found:raise RuntimeError("Frozen EXE did not show the expected version window")
        if args.require_launcher_splash and splash_state["ready_ms"] is None:
            raise RuntimeError("Smart launcher did not show its first-run splash")
        print(json.dumps(result,ensure_ascii=False))
    except Exception as error:
        result=locals().get("result",{"version":version,"windows":found})
        result.update({"ok":False,"error":f"{type(error).__name__}: {error}"})
        Path(args.report).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        raise
    finally:
        process_ids={process.pid}
        process_ids.update(item["pid"] for item in found)
        for pid in process_ids:
            subprocess.run(["taskkill","/PID",str(pid),"/T","/F"],capture_output=True,timeout=15)
    return 0


if __name__=="__main__":raise SystemExit(main())
