"""몽땅클립보드 화면 서비스: 켜기(동의)·끄기·상태·목록·고정·지우기·되돌려 붙이기·설정.

기록과 빠른 붙여넣기는 독립 상주 프로그램 kagent.exe가 한다(기본 꺼짐). 이 서비스는
사용자가 켤 때만 에이전트를 설치·실행하고, 이후에는 파이프로 명령만 보낸다.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import webbrowser
from pathlib import Path

from . import kagent_client as kc

CONSENT = ("몽땅클립보드는 이 PC에서 복사(Ctrl+C)한 글·그림·파일 경로를 기록해 다시 붙여넣을 수 있게 합니다. "
           "기록은 이 PC의 사용자 폴더에만 암호화해 저장하고 밖으로 보내지 않습니다. "
           "암호 관리자가 보내는 '기록 제외' 신호는 따릅니다. 언제든 일시정지·끄기·모두 지우기를 할 수 있습니다.")


def bundled_exe():
    """앱에 들어 있는 kagent.exe(배포판: resources, 개발: kagent/target/release)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    for candidate in (base / "resources" / "kagent.exe", base / "kagent" / "target" / "release" / "kagent.exe"):
        if candidate.is_file():
            return candidate
    return None


def _verify(exe):
    """배포판에는 SHA-256 파일이 함께 있다 — 있으면 맞는지 확인한다."""
    digest_file = exe.with_name(exe.name + ".sha256")
    if not digest_file.is_file():
        return True
    expected = digest_file.read_text(encoding="ascii").strip().lower()
    return hashlib.sha256(exe.read_bytes()).hexdigest() == expected


class KClipService:
    def __init__(self, client=None, *, installer=kc.install, starter=kc.start, autostart=kc.set_autostart,
                 autostart_status=kc.autostart_enabled,
                 bundled=bundled_exe):
        self.client = client or kc.KAgentClient()
        self._install = installer
        self._start = starter
        self._autostart = autostart
        self._autostart_status = autostart_status
        self._bundled = bundled
        self._pause_file = Path(tempfile.gettempdir()) / f"docfit-kclip-pause-{os.getpid()}.json"

    def _pause_until(self, until=None):
        try:
            data = json.loads(self._pause_file.read_text(encoding="utf-8"))
            expiry = float(data.get("until", 0))
        except (OSError, ValueError, TypeError):
            expiry = 0
        if until is not None:
            expiry = until
            self._pause_file.write_text(json.dumps({"until": expiry}), encoding="utf-8")
        if expiry and expiry <= time.time():
            self._pause_file.unlink(missing_ok=True)
            if self.client.running():
                try:
                    self.client.request("resume")
                except kc.KAgentError:
                    pass
            return 0
        return expiry

    def status(self):
        expiry = self._pause_until()
        status = self.client.status_file() if self.client.running() else None
        if status is not None and expiry:
            status["paused"] = True
            status["pause_until"] = expiry
        try:
            autostart = bool(self._autostart_status())
        except (OSError, ImportError):
            autostart = False
        return dict(ok=True, running=bool(status), available=self._bundled() is not None,
                    autostart=autostart, consent=CONSENT, status=status or {})

    def enable(self, payload):
        if payload.get("consent") is not True:
            return dict(ok=False, code="KCLIP_CONSENT", message="안내를 읽고 동의해 주세요.")
        exe = self._bundled()
        if exe is None:
            return dict(ok=False, code="KCLIP_MISSING", message="이 버전에는 몽땅클립보드 프로그램이 들어 있지 않습니다.")
        if not _verify(exe):
            return dict(ok=False, code="KCLIP_INTEGRITY", message="몽땅클립보드 프로그램 파일이 손상됐습니다. 다시 설치해 주세요.")
        if not self.client.running():
            installed = self._install(exe)
            self._start(installed)
            for _ in range(100):
                if self.client.running():
                    break
                time.sleep(0.02)
        try:
            self._autostart(payload.get("autostart", True) is True)
        except OSError:
            pass
        return self.status()

    def disable(self, payload):
        if self.client.running():
            try:
                self.client.request("quit")
            except kc.KAgentError:
                pass
            for _ in range(50):
                if not self.client.running():
                    break
                time.sleep(0.02)
        try:
            self._autostart(False)
        except OSError:
            pass
        return self.status()

    def _forward(self, cmd, payload, keys):
        try:
            response = self.client.request(cmd, **{k: payload[k] for k in keys if k in payload})
        except kc.KAgentError as error:
            return dict(ok=False, code="KCLIP_OFFLINE", message=str(error))
        return response

    def command(self, action, payload=None):
        payload = payload if isinstance(payload, dict) else {}
        if action == "status":
            return self.status()
        if action == "enable":
            return self.enable(payload)
        if action == "disable":
            return self.disable(payload)
        if action == "autostart":
            enabled = payload.get("enabled") is True
            try:
                self._autostart(enabled)
            except OSError as error:
                return dict(ok=False, code="KCLIP_AUTOSTART", message=f"자동 시작 설정을 바꾸지 못했습니다: {error}")
            return self.status()
        forwards = {
            "add_text": ("add_text", ("text",)),
            "add_files": ("add_files", ("paths",)),
            "list": ("list", ("limit", "query")),
            "get": ("get", ("id",)),
            "restore": ("restore", ("id",)),
            "delete": ("delete", ("id",)),
            "pin": ("pin", ("id", "pinned")),
            "clear": ("clear", ("keep_pinned",)),
            "pause": ("pause", ("minutes",)),
            "resume": ("resume", ()),
            "settings_get": ("settings_get", ()),
            "settings_set": ("settings_set", ("settings",)),
        }
        if action == "open_web":
            try:
                item_id = int(payload.get("id"))
            except (TypeError, ValueError):
                return dict(ok=False, code="KCLIP_WEB", message="웹 링크 항목을 확인해 주세요.")
            try:
                result = self.client.request("get", id=item_id)
            except kc.KAgentError as error:
                return dict(ok=False, code="KCLIP_OFFLINE", message=str(error))
            from urllib.parse import urlsplit
            url = str(result.get("data") or "").strip()
            parsed = urlsplit(url)
            if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
                return dict(ok=False, code="KCLIP_WEB", message="HTTP 또는 HTTPS 웹 주소가 아닙니다.")
            return dict(ok=bool(webbrowser.open(url)), message="기본 브라우저에서 웹 링크를 열었습니다.")
        if action not in forwards:
            return dict(ok=False, code="NOT_AVAILABLE", message="지원하지 않는 명령입니다.")
        if action == "pause":
            minutes = payload.get("minutes")
            if minutes is not None:
                try:
                    minutes = max(1, min(1440, int(minutes)))
                except (TypeError, ValueError):
                    return dict(ok=False, code="KCLIP_PAUSE", message="일시정지 시간을 확인해 주세요.")
                self._pause_until(time.time() + minutes * 60)
        elif action == "resume":
            self._pause_file.unlink(missing_ok=True)
        cmd, keys = forwards[action]
        if action in ("get", "restore", "delete", "pin"):
            try:
                item_id = int(payload.get("id"))
                if isinstance(payload.get("id"), bool) or item_id <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                return dict(ok=False, code="KCLIP_ITEM", message="항목을 확인해 주세요.")
            payload = dict(payload, id=item_id)
        if action == "pin":
            payload = dict(payload, pinned=payload.get("pinned") is not False)
        if action == "clear":
            # 고정 항목은 기본으로 보존한다. 고정까지 지우려면 keep_pinned=False를 명시해야 한다.
            keep_pinned = payload.get("keep_pinned") is not False
            result = self._forward(cmd, dict(payload, keep_pinned=keep_pinned), keys)
            if isinstance(result, dict) and result.get("ok") is not False:
                result = dict(result, keep_pinned=keep_pinned)
                result.setdefault("message", "고정한 항목은 남기고 지웠습니다." if keep_pinned
                                  else "고정한 항목까지 모두 지웠습니다.")
            return result
        return self._forward(cmd, payload, keys)
