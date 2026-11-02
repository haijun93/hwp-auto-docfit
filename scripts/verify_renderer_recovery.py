"""Build/run the desktop app and verify WebView2 renderer recovery through CDP.

Only the WebView2 renderer child of the launched app process is terminated.
No HWP COM calls or user documents are involved.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import uuid


def _owned_renderer_pids(root_pid: int, psutil) -> list[int]:
    """Return renderer PIDs strictly within this launched app's descendant tree."""
    try:
        root = psutil.Process(root_pid)
        descendants = root.children(recursive=True)
    except psutil.Error:
        return []
    result = []
    for proc in descendants:
        try:
            name = (proc.name() or "").lower()
            cmdline = " ".join(proc.cmdline() or []).lower()
            if name.startswith("msedgewebview2") and "--type=renderer" in cmdline:
                result.append(proc.pid)
        except psutil.Error:
            continue
    return sorted(set(result))


def _wait_for_renderer(root_pid: int, psutil, timeout: float = 20) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pids = _owned_renderer_pids(root_pid, psutil)
        if pids:
            return pids[0]
        time.sleep(.2)
    raise TimeoutError("No renderer process found under the launched app PID")


def _terminate_owned_renderer(root_pid: int, pid: int, psutil) -> None:
    """Revalidate ancestry and process type immediately before terminating."""
    owned = _owned_renderer_pids(root_pid, psutil)
    if pid not in owned:
        raise RuntimeError(f"Refusing to terminate renderer PID {pid}: ownership changed")
    proc = psutil.Process(pid)
    proc.terminate()
    try:
        proc.wait(timeout=8)
    except psutil.TimeoutExpired:
        # The PID and parent tree were revalidated above; never escalate via a
        # process-tree kill because that could include the browser or app.
        proc.kill()
        proc.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("reports/renderer-recovery.json"))
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--flutter-exe", type=Path, help="existing app executable (skips web build)")
    parser.add_argument("--no-build", action="store_true", help="use the existing Flutter web bundle")
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright
    import psutil

    root = Path(__file__).resolve().parents[1]
    flutter = Path(os.environ["LOCALAPPDATA"]) / "DocFitTools/flutter/bin/flutter.bat"
    python = Path("C:/Users/haiju/OneDrive/바탕 화면/HWP_AutoDocFit/mapo-agent-1/.venv/Scripts/python.exe")
    app_script = root / "hwp-auto-docfit.py"
    report = {"ok": False, "build": None, "pid": None, "initial_frame": False,
              "renderer_pid": None, "renderer_exit_observed": False,
              "recovered_frame": False, "screenshot": None, "ink_fraction": None,
              "error": None}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="docfit-renderer-recovery-"))
    app_home = temp_root / "launcher"
    local_appdata = temp_root / "localappdata"
    webview_data = temp_root / "webview2"
    for directory in (app_home, local_appdata, webview_data):
        directory.mkdir(parents=True)

    def save():
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    proc = None
    try:
        if args.flutter_exe:
            executable = args.flutter_exe.resolve()
            report["build"] = {"skipped": True, "reason": "provided executable"}
        else:
            if not args.no_build:
                build = subprocess.run([str(flutter), "build", "web", "--release"],
                                       cwd=root / "flutter_ui", text=True, capture_output=True,
                                       timeout=600)
                report["build"] = {"returncode": build.returncode,
                                   "stdout_tail": build.stdout[-3000:],
                                   "stderr_tail": build.stderr[-3000:]}
                if build.returncode:
                    raise RuntimeError("Flutter web build failed")
            report["build"] = report["build"] or {"skipped": True}
            executable = python
        if not args.flutter_exe:
            launch_command = [str(executable), str(app_script)]
        else:
            launch_command = [str(executable)]

        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        env = dict(os.environ)
        env.update({
            "DOCFIT_LAUNCHER_TEST_ROOT": str(app_home),
            "LOCALAPPDATA": str(local_appdata),
            "WEBVIEW2_USER_DATA_FOLDER": str(webview_data),
            "DOCFIT_SMOKE_CDP_PORT": str(port),
            "DOCFIT_LAUNCHER_MUTEX_NAME": "Local\\DocFitRendererRecovery_" + uuid.uuid4().hex,
            "DOCFIT_OFFLINE": "1",
            "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS": f"--remote-debugging-port={port}",
        })
        proc = subprocess.Popen(launch_command, cwd=root, env=env)
        report["pid"] = proc.pid
        with sync_playwright() as playwright:
            deadline = time.monotonic() + args.timeout
            browser = None
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise RuntimeError(f"App exited early with code {proc.returncode}")
                try:
                    browser = playwright.chromium.connect_over_cdp(
                        f"http://127.0.0.1:{port}", timeout=1000)
                    break
                except Exception:
                    time.sleep(.2)
            if browser is None:
                raise TimeoutError("Could not connect to app WebView2 CDP endpoint")
            page = browser.contexts[0].pages[0]
            page.wait_for_function("window.docfitFirstFrame === true", timeout=60000)
            report["initial_frame"] = True
            renderer_pid = _wait_for_renderer(proc.pid, psutil)
            report["renderer_pid"] = renderer_pid
            _terminate_owned_renderer(proc.pid, renderer_pid, psutil)
            report["renderer_exit_observed"] = True
            # Reload creates a fresh renderer. Require both the Flutter frame
            # marker and a screenshot with visible ink to reject a blank canvas.
            page.wait_for_function("window.docfitFirstFrame === true", timeout=60000)
            report["recovered_frame"] = True
            page.wait_for_timeout(1000)
            screenshot_path = args.report.with_suffix(".png")
            screenshot_path.write_bytes(page.screenshot())
            report["screenshot"] = str(screenshot_path.resolve())
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(screenshot_path.read_bytes())).convert("RGB")
            pixels = list(image.resize((160, 120)).getdata())
            report["ink_fraction"] = sum(max(pixel) < 180 for pixel in pixels) / len(pixels)
            report["ok"] = report["ink_fraction"] >= .005
            if not report["ok"]:
                raise RuntimeError("Recovered frame screenshot appears blank")
            browser.close()
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if proc is not None and proc.poll() is None:
            try:
                app = psutil.Process(proc.pid)
                children = app.children(recursive=True)
                # Graceful app shutdown first; terminate only tracked descendants.
                proc.terminate()
                try:
                    proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    for child in children:
                        try:
                            child.terminate()
                        except psutil.Error:
                            pass
                    proc.kill()
            except psutil.Error:
                pass
        save()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
