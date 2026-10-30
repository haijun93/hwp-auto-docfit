"""UI 독립 업데이트 서비스. HTTP·시간·프로세스 실행은 시험에서 대체한다."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse, urljoin, quote
import webbrowser

from docfit_core.network_policy import offline_mode, settings_folder
from docfit_core.updater import verify_download

RAW = "https://gitlab.aigov.go.kr/haijun93/hwp_autodocfit/-/raw/downloads/"
INTERNAL_HOST = "gitlab.aigov.go.kr"
DOWNLOAD_PAGE = "https://gitlab.aigov.go.kr/haijun93/hwp_autodocfit/-/tree/downloads"
GITHUB_API = "https://api.github.com/repos/haijun93/hwp-auto-docfit/releases/latest"
BUSY = {"checking", "downloading", "installing"}


def _error_line(error):
    return (str(error).strip() or "알 수 없는 오류").splitlines()[0]


def portable_target(executable, environ):
    """캐시에서 실행 중이면 배포용 런처를 교체하고, 일반 단일 EXE는 자신을 교체한다."""
    launcher = environ.get("DOCFIT_LAUNCHER_PATH")
    if launcher:
        path = Path(launcher).resolve()
        if path.suffix.lower() == ".exe" and path.is_file():
            return path
    return Path(executable).resolve()


def version_key(value):
    match = re.fullmatch(r"v?(\d+(?:\.\d+){1,3})(?:[- ]?(alpha|beta|rc)[. ]?(\d+)?)?", str(value).strip(), re.I)
    if not match:
        raise ValueError("버전 형식이 올바르지 않습니다.")
    numbers = [int(n) for n in match[1].split(".")]
    return (*((numbers + [0] * 4)[:4]), {"alpha": 0, "beta": 1, "rc": 2, None: 3}[match[2].lower() if match[2] else None], int(match[3] or 0))


def extract_notes(body):
    # 2.0.x 릴리스 노트는 '## 바뀐 점' 아래 '### 1. 제목' 소제목을 쓴다(예전은 '## 새로 된 점' 아래 '- ' 목록).
    lines, titles, active = [], [], False
    for line in str(body).splitlines():
        if line.strip() in ("## 새로 된 점", "## 바뀐 점"):
            active = True
        elif active and line.startswith("## "):
            break
        elif active and line.startswith("### "):
            titles.append(re.sub(r"^\d+\.\s*", "", line[4:]).replace("**", "").strip())
        elif active and line.startswith("- "):
            lines.append(line[2:].replace("**", "").strip())
    return (titles or lines)[:6]


def parse_sha256sums(body):
    result = {}
    for line in str(body).splitlines():
        match = re.fullmatch(r"([a-fA-F0-9]{64})\s+\*?(.+)", line.strip())
        if match:
            # 실제 SHA256SUMS는 'release-assets/HWP_AutoDocFit_v1.80.4_Portable.exe'처럼 경로가 붙어 있다(2026-10-23 실측).
            result[re.split(r"[\/]", match[2].strip())[-1]] = match[1].lower()
    return result


def validate_url(url):
    parsed = urlparse(str(url))
    host = (parsed.hostname or "").lower()
    if (parsed.scheme != "https" or parsed.username or parsed.password or
            parsed.port not in (None, 443) or not (host in ("gitlab.aigov.go.kr", "api.github.com", "github.com") or host.endswith(".githubusercontent.com"))):
        raise ValueError("허용되지 않은 업데이트 URL입니다.")
    return str(url)


def http_get(url, headers, timeout, redirects=5, _deadline=None):
    if timeout <= 8 and _deadline is None:
        _deadline = time.monotonic() + timeout
    if _deadline is not None:
        timeout = min(timeout, _deadline - time.monotonic())
        if timeout <= 0:
            raise TimeoutError("업데이트 조회 시간이 초과됐어요.")
    parsed = urlparse(validate_url(url))
    connection = http.client.HTTPSConnection(  # nosemgrep
        parsed.hostname, 443, timeout=timeout, context=ssl.create_default_context())
    try:
        connection.request("GET", parsed.path + ("?" + parsed.query if parsed.query else ""), headers=headers)
        response = connection.getresponse()
        if response.status in (301, 302, 303, 307, 308):
            target = response.getheader("Location")
            response.close()
            connection.close()
            if not target or redirects <= 0:
                raise RuntimeError("업데이트 주소의 리디렉션을 확인하지 못했습니다.")
            return http_get(urljoin(url, target), headers, timeout, redirects - 1, _deadline)
        if response.status != 200:
            raise RuntimeError(f"업데이트 서버 응답: {response.status}")
        response._docfit_connection = connection
        return response
    except BaseException:
        connection.close()
        raise


def setup_script():
    return '''param([string]$Installer, [string]$Sha256, [string]$WaitPidList,
                   [int]$AppPid, [string]$AppExecutable)
$ErrorActionPreference = 'Stop'
function Get-Sha256Hex([string]$Path) {
    # Get-FileHash는 모듈 경로가 달라진 PowerShell에서 없을 수 있다(2026-10-23 CI 실측) — .NET으로 직접 계산한다.
    $stream = [System.IO.File]::OpenRead($Path)
    try { $sha = [System.Security.Cryptography.SHA256]::Create()
          try { return (($sha.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '') } finally { $sha.Dispose() } }
    finally { $stream.Dispose() }
}
foreach ($processId in ($WaitPidList -split ' ')) {
    if ($processId) {
        $appProcess = Get-Process -Id ([int]$processId) -ErrorAction SilentlyContinue
        # onedir can be started directly by Explorer; only app/bootloader parents are waited on.
        if ($appProcess -and ($appProcess.Id -eq $AppPid -or $appProcess.Path -eq $AppExecutable -or
                             $appProcess.ProcessName -eq 'HWP_AutoDocFit')) {
            Wait-Process -Id $appProcess.Id -ErrorAction SilentlyContinue
        }
    }
}
if ((Get-Sha256Hex $Installer) -ne $Sha256.ToLower()) { throw 'SHA-256 불일치' }
Start-Process -FilePath $Installer -ArgumentList '/SILENT /NORESTART /SUPPRESSMSGBOXES /SP-' -Wait
'''


class UpdateService:
    def __init__(self, current, *, http_get=http_get, clock=time.monotonic,
                 launch=subprocess.Popen, offline=offline_mode, folder=None,
                 executable=None, frozen=None, portable_install=None, exit_app=None,
                 open_page=webbrowser.open, running=lambda: False):
        self.http_get, self.clock, self.launch, self.offline = http_get, clock, launch, offline
        self.folder = Path(folder) if folder else settings_folder()
        self.executable = Path(executable or sys.executable)
        self.frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
        self.portable_install, self.exit_app = portable_install, exit_app
        self.open_page, self.running = open_page, running
        self._lock, self._operation = threading.RLock(), threading.Lock()
        self._release, self._announced = None, set()
        self._periodic_started = False
        self._metadata_deadline = None
        self._state = dict(step="idle", current=current, latest=None, percent=0,
                           message="", notes=[], installed=(self.executable.parent / "unins000.exe").is_file(), source="")

    def _set(self, **changes):
        with self._lock:
            self._state.update(changes)

    def _internal_only(self):
        # 폐쇄망 모드여도 업데이트는 끄지 않는다(2.0.4, 사용자 지시). 공공기관망에서 열리는 내부 GitLab에서만 받고 GitHub에는 접속하지 않는다.
        return bool(self.offline())

    def state(self):
        with self._lock:
            return deepcopy(self._state)

    @contextmanager
    def _response(self, url, timeout):
        if self._internal_only() and urlparse(url).hostname != INTERNAL_HOST:
            raise RuntimeError("폐쇄망 모드에서는 내부 GitLab에서만 업데이트를 받습니다.")
        response = self.http_get(validate_url(url), {"User-Agent": f"HWP-AutoDocFit/{self._state['current']}"}, timeout)
        try:
            yield response
        finally:
            response.close()
            connection = getattr(response, "_docfit_connection", None)
            if connection:
                connection.close()

    def _read(self, url):
        remaining = self._metadata_deadline - self.clock()
        if remaining <= 0:
            raise TimeoutError("업데이트 조회 시간이 초과됐어요.")
        with self._response(url, min(8, remaining)) as response:
            chunks, size = [], 0
            reader = getattr(response, "read1", response.read)
            while True:
                remaining = self._metadata_deadline - self.clock()
                if remaining <= 0:
                    raise TimeoutError("업데이트 조회 시간이 초과됐어요.")
                # HTTPResponse retains the socket after HTTPSConnection relinquishes it.
                sock = getattr(getattr(getattr(response, "fp", None), "raw", None), "_sock", None)
                if sock is not None:
                    sock.settimeout(remaining)
                chunk = reader(64 * 1024)
                if self.clock() > self._metadata_deadline:
                    raise TimeoutError("업데이트 조회 시간이 초과됐어요.")
                if not chunk:
                    return b"".join(chunks).decode("utf-8-sig")
                size += len(chunk)
                if size > 4 * 1024 * 1024:
                    raise ValueError("업데이트 정보가 너무 큽니다.")
                chunks.append(chunk)

    def _file(self, version, kind, item):
        name = str(item.get("name", ""))
        expected = f"HWP_AutoDocFit_v{version}_{'Setup' if kind == 'setup' else 'Portable'}.exe"
        digest = str(item.get("sha256", "")).lower()
        size = int(item.get("size", 0))
        if name != expected or size <= 0 or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("업데이트 파일 이름·크기·SHA-256 정보가 올바르지 않습니다.")
        return dict(name=name, size=size, sha256=digest, url=validate_url(item.get("url") or RAW + quote(name) + "?inline=false"))

    def _gitlab(self):
        data = json.loads(self._read(RAW + "latest.json?inline=false"))
        version = str(data["version"]).removeprefix("v")
        version_key(version)
        files = {kind: self._file(version, kind, data["files"][kind]) for kind in ("portable", "setup")}
        notes = data.get("notes", [])
        if not isinstance(notes, list):
            raise ValueError("바뀐 점 형식이 올바르지 않습니다.")
        return dict(version=version, files=files, notes=[str(n).replace("**", "").strip().splitlines()[0] for n in notes[:6] if str(n).strip()], source="GitLab")

    def _github(self):
        data = json.loads(self._read(GITHUB_API))
        version = str(data["tag_name"]).removeprefix("v")
        version_key(version)
        assets = {a["name"]: a for a in data["assets"]}
        sums = parse_sha256sums(self._read(assets["SHA256SUMS"]["browser_download_url"]))
        files = {}
        for kind, suffix in (("portable", "Portable"), ("setup", "Setup")):
            name = f"HWP_AutoDocFit_v{version}_{suffix}.exe"
            item = assets[name]
            digest = sums.get(name) or str(item.get("digest") or "").removeprefix("sha256:")   # GitHub 자산 digest를 예비로
            files[kind] = self._file(version, kind, {**item, "sha256": digest, "url": item["browser_download_url"]})
        return dict(version=version, files=files, notes=extract_notes(data.get("body", "")), source="GitHub")

    def _refresh(self):
        self._set(step="checking", percent=0, message="새 버전을 확인하고 있어요…")
        results = []
        for read in (self._gitlab,) if self._internal_only() else (self._gitlab, self._github):
            try:
                self._metadata_deadline = self.clock() + 8
                results.append(read())
            except Exception:
                pass
        if not results:
            self._set(step="failed", message="업데이트 정보를 확인하지 못했어요. 잠시 뒤 다시 눌러 주세요.")
            return False
        release = max(results, key=lambda r: version_key(r["version"]))
        self._release = release
        newer = version_key(release["version"]) > version_key(self._state["current"])
        self._set(step="available" if newer else "latest", latest=release["version"], notes=release["notes"], source=release["source"],
                  message=f"새 버전 v{release['version']}이 나왔어요." if newer else "최신 버전이에요.")
        return True

    def check(self):
        if not self._begin():
            return False
        try:
            return self._refresh()
        except Exception as exc:
            self._set(step="failed", message=f"업데이트 확인 실패: {_error_line(exc)}")
            return False
        finally:
            self._operation.release()

    def _begin(self):
        if not self._operation.acquire(False):
            return False
        with self._lock:
            if self._state["step"] in BUSY:
                self._operation.release()
                return False
        return True

    def _verified(self, path, item):
        if not path.is_file():
            return False
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            head = stream.read(2)
            digest.update(head)
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return verify_download(path.stat().st_size, head, digest.hexdigest(), item["size"], item["sha256"]) is None

    def _download(self, item):
        folder = self.folder / "updates"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / item["name"]
        if self._verified(path, item):
            self._set(percent=100)
            return path
        part = path.with_name(path.name + ".part")
        try:
            total = 0
            with self._response(item["url"], 30) as response, part.open("wb") as stream:
                # read1 returns after receiving bytes, rather than waiting to fill a whole block.
                reader = getattr(response, "read1", response.read)
                while True:
                    before = self.clock()
                    chunk = reader(64 * 1024)
                    if self.clock() - before >= 30:
                        raise TimeoutError("30초 동안 다운로드 응답이 없어요.")
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > item["size"]:
                        raise ValueError("업데이트 파일 크기가 예상보다 큽니다.")
                    stream.write(chunk)
                    self._set(percent=min(100, int(total * 100 / item["size"])), message=f"내려받는 중… {min(100, int(total * 100 / item['size']))}%")
            if not self._verified(part, item):
                raise ValueError("업데이트 파일 크기·EXE 머리·SHA-256 검증에 실패했어요.")
            os.replace(part, path)
            return path
        finally:
            part.unlink(missing_ok=True)

    def start_update(self):
        if self.running() or not self._begin():
            return False
        try:
            if not self.frozen:
                return self.open_download_page()
            if not self._refresh() or self._state["step"] != "available":
                return False
            kind = "setup" if self._state["installed"] else "portable"
            item = self._release["files"][kind]
            self._set(step="downloading", percent=0, message="업데이트 파일을 내려받고 있어요…")
            path = self._download(item)
            if self.running():
                self._set(step="available", message="문서 작업이 끝난 뒤 업데이트해 주세요.")
                return False
            self._set(step="installing", message="설치를 시작했어요. 잠시 뒤 앱이 다시 열려요.")
            if kind == "setup":
                script = path.with_suffix(".ps1")
                script.write_text(setup_script(), encoding="utf-8-sig")
                from docfit_core.updater import launch_environment
                self.launch(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
                             "-Installer", str(path), "-Sha256", item["sha256"], "-WaitPidList", f"{os.getpid()} {os.getppid()}",
                             "-AppPid", str(os.getpid()), "-AppExecutable", str(self.executable)],
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), env=launch_environment(os.environ))
                if self.exit_app:
                    self.exit_app()
            elif self.portable_install:
                if self.portable_install(path, item["sha256"]) is False:
                    raise RuntimeError("포터블 파일을 교체하지 못했어요.")
            else:
                raise RuntimeError("포터블 업데이트 설치 연결이 없습니다.")
            return True
        except Exception as exc:
            cancelled = getattr(exc, "winerror", None) == 1223
            self._set(step="cancelled" if cancelled else "failed", message="업데이트를 취소했어요." if cancelled else f"업데이트 실패: {_error_line(exc)}")
            return False
        finally:
            self._operation.release()

    def open_download_page(self):
        self.open_page(DOWNLOAD_PAGE)
        return True

    def version_notice(self, storage):
        previous = None
        def update(settings):
            nonlocal previous
            previous = settings.get("last_run_version")
            settings["last_run_version"] = self._state["current"]
        storage.update(update)
        if previous and previous != self._state["current"]:
            return f"v{previous} → v{self._state['current']}으로 바뀌었어요"
        return None

    def start_periodic_checks(self, schedule, enabled, announce, alive=lambda: True):
        if self._periodic_started:
            return
        self._periodic_started = True
        def tick():
            if not alive():
                return
            if enabled():
                def work():
                    if self.check():
                        state = self.state()
                        if state["step"] == "available" and state["latest"] not in self._announced:
                            self._announced.add(state["latest"])
                            schedule(0, lambda: announce(state))
                threading.Thread(target=work, daemon=True, name="periodic-update-check").start()
            schedule(6 * 60 * 60 * 1000, tick)
        schedule(20000, tick)
