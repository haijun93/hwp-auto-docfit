"""Start our frozen EXE, verify its visible version title, then stop only that process tree."""
import argparse
import ast
import ctypes
import json
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
    process=subprocess.Popen([str(exe)])
    try:
        deadline=time.monotonic()+60
        while time.monotonic()<deadline and not found:
            win32gui.EnumWindows(inspect,None)
            if process.poll() is not None and not found:break
            time.sleep(.5)
        result={"ok":bool(found),"version":version,"windows":found}
        Path(args.report).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        if not found:raise RuntimeError("Frozen EXE did not show the expected version window")
        print(json.dumps(result,ensure_ascii=False))
    finally:
        subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],capture_output=True,timeout=15)
    return 0


if __name__=="__main__":raise SystemExit(main())
