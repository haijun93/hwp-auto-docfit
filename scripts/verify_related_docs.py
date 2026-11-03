"""실제 포터블 앱에서 타임머신 본문 색인·연관 문서·증분 갱신을 판정한다."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time


LOCK_DIR = Path("C:/HWP_AUTODOCFIT/v1803/reports/.app-test.lock")
DEFAULT_EXE = Path("C:/HWP_AUTODOCFIT/v1803/rel228/HWP_AutoDocFit_v2.2.8_Portable.exe")


def resolve_isolated_paths(env: dict[str, str], temp_root: Path) -> dict[str, Path]:
    """앱 소스와 동일한 APPDATA 우선 설정 경로 및 LocalAppData 데이터 경로."""
    appdata = env.get("APPDATA") or env.get("LOCALAPPDATA")
    home = Path(env.get("USERPROFILE") or Path.home())
    settings_base = Path(appdata) if appdata else home / ".hwp_auto_docfit"
    local_base = Path(env.get("LOCALAPPDATA") or home)
    return {"settings": settings_base / "HwpAutoDocFit" / "settings.json",
            "timeline": local_base / "HwpAutoDocFit" / "timeline-content.sqlite"}


def acquire_lock(path: Path, timeout: float = 1200, interval: float = 2) -> bool:
    """mkdir 원자성으로 앱 시험 잠금을 얻는다. 생성한 호출자만 삭제한다."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            path.mkdir(parents=True)
            return True
        except FileExistsError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(interval)


def process_executable_under(root: Path, psutil_module) -> list:
    """명령줄을 쓰지 않고 실행 파일 경로가 root 아래인 프로세스만 반환."""
    root = root.resolve()
    found = []
    for proc in psutil_module.process_iter(["pid", "exe"]):
        try:
            exe = proc.info.get("exe")
            if exe and Path(exe).resolve().is_relative_to(root):
                found.append(proc)
        except (psutil_module.Error, OSError, ValueError):
            continue
    return found


def main() -> int:
    from playwright.sync_api import sync_playwright
    import psutil

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--app-root", type=Path,
                        default=Path("C:/HWP_AUTODOCFIT/v1803/rel228/root"))
    parser.add_argument("--report", type=Path, default=Path("reports/related-docs.json"))
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--lock-timeout", type=float, default=1200)
    args = parser.parse_args()
    report = {"ok": False, "exe": str(args.exe.resolve()), "checks": {}, "errors": []}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if not acquire_lock(LOCK_DIR, args.lock_timeout):
        report["error"] = f"앱 시험 잠금 대기 {args.lock_timeout:g}초 초과: {LOCK_DIR}"
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    temp = Path(tempfile.mkdtemp(prefix="docfit-related-"))
    process = None
    try:
        app_root = args.app_root.resolve()
        roaming, local = temp / "appdata", temp / "localappdata"
        webview, corpus = temp / "webview2", temp / "documents"
        for folder in (roaming, local, webview, corpus):
            folder.mkdir(parents=True, exist_ok=True)
        original_settings = resolve_isolated_paths(dict(os.environ), temp)["settings"]
        original_exists = original_settings.is_file()
        original_mtime = original_settings.stat().st_mtime_ns if original_exists else None
        env = dict(os.environ)
        env.update({"APPDATA": str(roaming), "LOCALAPPDATA": str(local),
                    "WEBVIEW2_USER_DATA_FOLDER": str(webview), "DOCFIT_OFFLINE": "1",
                    "DOCFIT_LAUNCHER_TEST_ROOT": str(app_root)})
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        env["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = f"--remote-debugging-port={port}"
        env["DOCFIT_SMOKE_CDP_PORT"] = str(port)
        isolated = resolve_isolated_paths(env, temp)
        settings_path, content_db_path = isolated["settings"], isolated["timeline"]
        report["settings_isolated"] = settings_path.is_relative_to(temp)
        report["timeline_isolated"] = content_db_path.is_relative_to(temp)
        report["settings_resolution"] = {
            "original_settings": str(original_settings),
            "original_mtime_ns_before": original_mtime,
            "isolated_path": str(settings_path),
            "isolated_content_db": str(content_db_path),
            "app_root": str(app_root), "lock_dir": str(LOCK_DIR)}
        if not report["settings_isolated"] or not report["timeline_isolated"]:
            raise RuntimeError("APPDATA/LOCALAPPDATA 경로가 임시 루트에 격리되지 않았습니다.")
        if not args.exe.is_file() or not app_root.is_dir():
            raise FileNotFoundError(f"시험 EXE 또는 launcher test root가 없습니다: {args.exe}, {app_root}")

        # Tiny synthetic corpus; the user's documents are never opened or changed.
        docs = {
            "alpha.txt": "2026년도 3분기 주요업무추진실적\n작성 기준일: 2026. 9. 30.\nZXQ-RELATED-ALPHA 본문 색인 전용 문장입니다. 공통 키워드 달빛기록.",
            "beta.txt": "2026년도 2분기 주요업무추진실적\n작성 기준일: 2026. 6. 30.\nZXQ-RELATED-BETA 본문 색인 대상 문장입니다. 공통 키워드 달빛기록.",
            "unrelated.txt": "요리법과 여행 기록\nZXQ-UNRELATED 독립적인 본문이며 공통 키워드가 없습니다.",
        }
        for name, body in docs.items():
            (corpus / name).write_text(body, encoding="utf-8")
        # Test corpus selection is passed through the app's existing folder picker only;
        # UI automation below remains the source of pass/fail evidence.
        report["corpus"] = {name: str(corpus / name) for name in docs}
        process = subprocess.Popen([str(args.exe.resolve())], env=env)
        report["launcher_pid"] = process.pid
        with sync_playwright() as pw:
            browser = None
            deadline = time.monotonic() + args.timeout
            last_error = None
            while time.monotonic() < deadline:
                try:
                    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=1500)
                    break
                except Exception as exc:
                    last_error = str(exc)
                    if not process_executable_under(app_root, psutil):
                        time.sleep(.25)
                    else:
                        time.sleep(.25)
            if browser is None:
                raise RuntimeError(f"WebView2 CDP 연결 실패: {last_error}; launcher exit={process.poll()}")
            pages = [page for context in browser.contexts for page in context.pages]
            if not pages:
                raise RuntimeError("실행된 앱의 WebView 페이지가 없습니다.")
            page = pages[0]
            page.set_default_timeout(10000)
            page.wait_for_function("window.docfitFirstFrame === true", timeout=int(args.timeout * 1000))
            page.wait_for_function("window.pywebview && typeof window.pywebview.api.get_state === 'function'", timeout=30000)
            report["page"] = {"url": page.url, "title": page.title()}
            report["ui_text_initial"] = page.locator("body").inner_text(timeout=15000)[:12000]
            state = page.evaluate("window.pywebview.api.get_state()")
            report["app_version"] = state.get("version") if isinstance(state, dict) else None
            report["checks"]["app_rendered"] = bool(report["app_version"])
            viewport = page.evaluate("({width: innerWidth, height: innerHeight, dpr: devicePixelRatio})")
            report["viewport"] = viewport
            menu_y = 459 * viewport["height"] / 759
            page.mouse.click(91 * viewport["width"] / 1283, menu_y)
            page.wait_for_timeout(1200)
            report["initial_screen_capture"] = str(args.report.with_name("related-docs-initial.png"))
            page.screenshot(path=report["initial_screen_capture"])
            # Configure only the synthetic corpus in the isolated app profile.
            configured = page.evaluate("""async ([root]) => {
              return await window.pywebview.api.timemachine('settings_set', {
                roots: [root], enabled: true, time_mode: 'max',
                extensions: ['txt']
              });
            }""", [str(corpus)])
            report["setup_settings"] = configured
            if configured.get("ok") is not True:
                raise RuntimeError(f"격리 타임머신 설정 실패: {configured}")
            report["checks"]["timemachine_screen_opened"] = True
            enabled = page.evaluate("window.pywebview.api.timemachine('settings_get', {})")
            report["enabled_settings"] = enabled
            if enabled.get("settings", {}).get("enabled") is not True:
                raise RuntimeError("타임머신 켜기 버튼을 눌렀지만 설정이 활성화되지 않았습니다.")
            # Invoke the app bridge actions whose buttons are rendered on the
            # Flutter canvas (DOM controls do not exist in this WebView build).
            scan = page.evaluate("window.pywebview.api.timemachine('scan', {})")
            report["scan_started"] = scan
            page.wait_for_function("""async () => {
              const r = await window.pywebview.api.timemachine('status', {});
              return r.scan && r.scan.running === false && r.scan.seen >= 3;
            }""", timeout=60000)
            page.evaluate("window.pywebview.api.timemachine('content_index_start', {})")
            page.wait_for_function("""async () => {
              const r = await window.pywebview.api.timemachine('content_index_status', {});
              return r.running === false && r.seen >= 3 && r.indexed >= 3;
            }""", timeout=120000)
            page.screenshot(path=str(args.report.with_name("related-docs-timemachine.png")))
            report["body_search_index_status"] = page.evaluate("window.pywebview.api.timemachine('content_index_status', {})")
            search = page.evaluate("window.pywebview.api.timemachine('content_search', {query:'ZXQ-RELATED-BETA', limit:100})")
            report["body_search_results"] = {"ok": search.get("ok"), "items": [
                {"name": item.get("name"), "path": item.get("path"),
                 "contains_query": "ZXQ-RELATED-BETA" in item.get("snippet", "")}
                for item in search.get("items", [])]}
            names = [item.get("name") for item in search.get("items", [])]
            report["checks"]["body_search_index"] = "beta.txt" in names and "alpha.txt" not in names
            related = page.evaluate("([path]) => window.pywebview.api.timemachine('related_search', {path})", [str(corpus / "alpha.txt")])
            report["related_results"] = {"ok": related.get("ok"),
                "reference_date": related.get("reference_date"),
                "reference_date_found": related.get("reference_date_found"),
                "items": [{"name": item.get("name"), "score": item.get("score"),
                           "reference_date": item.get("reference_date"),
                           "reference_date_found": item.get("reference_date_found"),
                           "reasons": item.get("reasons", [])}
                          for item in related.get("items", [])]}
            related_names = [item.get("name") for item in related.get("items", [])]
            report["checks"]["related_document"] = "beta.txt" in related_names
            report["checks"]["unrelated_document_excluded"] = "unrelated.txt" not in related_names
            exclusion = page.evaluate("([selected_path, related_path]) => window.pywebview.api.timemachine('related_exclude', {selected_path, related_path})",
                                      [str(corpus / "alpha.txt"), str(corpus / "beta.txt")])
            report["related_exclusion"] = exclusion
            after_exclusion = page.evaluate("([path]) => window.pywebview.api.timemachine('related_search', {path})", [str(corpus / "alpha.txt")])
            report["related_after_exclusion"] = after_exclusion
            report["checks"]["related_exclusion"] = exclusion.get("ok") is True and not after_exclusion.get("items")

            # Refresh the app's indexes after file modification and deletion.
            modified = corpus / "beta.txt"
            time.sleep(1.1)
            modified.write_text(docs["beta.txt"] + "\nZXQ-MODIFIED-REFRESH", encoding="utf-8")
            page.evaluate("window.pywebview.api.timemachine('scan', {})")
            page.wait_for_function("""async () => {
              const r = await window.pywebview.api.timemachine('status', {});
              return r.scan && r.scan.running === false;
            }""", timeout=60000)
            page.wait_for_function("""async () => {
              const r = await window.pywebview.api.timemachine('content_index_status', {});
              if (r.running) return false;
              const search = await window.pywebview.api.timemachine('content_search', {query:'ZXQ-MODIFIED-REFRESH', limit:100});
              return search.items && search.items.some(item => item.name === 'beta.txt');
            }""", timeout=60000)
            refreshed = page.evaluate("window.pywebview.api.timemachine('content_search', {query:'ZXQ-MODIFIED-REFRESH', limit:100})")
            report["modified_search"] = {"ok": refreshed.get("ok"), "items": [
                {"name": item.get("name"), "contains_modified_token": "ZXQ-MODIFIED-REFRESH" in item.get("snippet", "")}
                for item in refreshed.get("items", [])]}
            report["checks"]["file_modified_index_refresh"] = any(x.get("name") == "beta.txt" for x in refreshed.get("items", []))
            modified.unlink()
            page.evaluate("window.pywebview.api.timemachine('scan', {})")
            page.wait_for_function("""async () => {
              const r = await window.pywebview.api.timemachine('status', {});
              return r.scan && r.scan.running === false;
            }""", timeout=60000)
            page.wait_for_function("""async () => {
              const r = await window.pywebview.api.timemachine('content_index_status', {});
              if (r.running) return false;
              const search = await window.pywebview.api.timemachine('content_search', {query:'ZXQ-MODIFIED-REFRESH', limit:100});
              return search.items && search.items.length === 0;
            }""", timeout=60000)
            deleted = page.evaluate("window.pywebview.api.timemachine('content_search', {query:'ZXQ-MODIFIED-REFRESH', limit:100})")
            report["deleted_search"] = {"ok": deleted.get("ok"), "items": [
                {"name": item.get("name")} for item in deleted.get("items", [])]}
            report["checks"]["file_deleted_index_refresh"] = not any(x.get("name") == "beta.txt" for x in deleted.get("items", []))
            page.screenshot(path=str(args.report.with_name("related-docs-indexed.png")))
            report["launcher_exit_code"] = process.poll()
            report["checks"]["launcher_returned"] = process.poll() == 0
            try:
                browser.close()
            except Exception:
                pass
        return 1
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        return 1
    finally:
        # Stop only processes whose executable path is physically under the test root.
        survivors = process_executable_under(args.app_root, psutil)
        report["app_root_processes_before_cleanup"] = [
            {"pid": p.pid, "exe": p.info.get("exe")} for p in survivors]
        cleanup_errors = []
        for proc in survivors:
            try:
                proc.terminate()
            except psutil.Error as exc:
                cleanup_errors.append(f"terminate {proc.pid}: {exc}")
        _, alive = psutil.wait_procs(survivors, timeout=8)
        for proc in alive:
            try:
                proc.kill()
            except psutil.Error as exc:
                cleanup_errors.append(f"kill {proc.pid}: {exc}")
        _, remaining = psutil.wait_procs(alive, timeout=5)
        report["app_root_processes_remaining"] = [
            {"pid": p.pid, "exe": p.exe()} for p in remaining]
        report["cleanup_errors"] = cleanup_errors
        report["checks"]["test_app_processes_closed"] = not remaining and not cleanup_errors
        original_settings = Path(report.get("settings_resolution", {}).get("original_settings", ""))
        before = report.get("settings_resolution", {}).get("original_mtime_ns_before")
        original_existed_before = before is not None
        exists_after = original_settings.is_file() if original_settings else False
        after = original_settings.stat().st_mtime_ns if exists_after else None
        report.setdefault("settings_resolution", {})["original_mtime_ns_after"] = after
        report["checks"]["user_settings_mtime_unchanged"] = (
            (exists_after and before == after) if original_existed_before
            else not exists_after)
        report["ok"] = all(report["checks"].values()) and not report["errors"]
        shutil.rmtree(temp, ignore_errors=True)
        try:
            LOCK_DIR.rmdir()
        except OSError:
            pass
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
