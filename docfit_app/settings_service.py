"""Read/modify/write existing settings without resetting unrelated values."""

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from threading import RLock

from .api_contract import ServiceError


class SettingsService:
    def __init__(self, path):
        self._path = path
        self._lock = RLock()

    def read(self):
        with self._lock:
            path = Path(self._path() if callable(self._path) else self._path)
            try:
                with path.open(encoding="utf-8") as stream:
                    settings = json.load(stream)
                if not isinstance(settings, dict):
                    raise ValueError("settings must be an object")
                return settings
            except FileNotFoundError:
                return {}
            except (OSError, ValueError) as exc:
                raise ServiceError("SETTINGS_READ_FAILED", "설정 파일을 읽지 못했습니다. 기존 파일을 확인해 주세요.") from exc

    def update(self, change):
        with self._lock:
            settings = self.read()
            updated = deepcopy(settings)
            change(updated)
            if updated == settings:
                return settings
            path = Path(self._path() if callable(self._path) else self._path)
            temporary = None
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                                 prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
                    temporary = Path(stream.name)
                    json.dump(updated, stream, ensure_ascii=False, indent=2)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, path)
            except (OSError, ValueError, TypeError) as exc:
                raise ServiceError("SETTINGS_WRITE_FAILED", "설정을 저장하지 못했습니다. 다시 시도해 주세요.") from exc
            finally:
                if temporary is not None:
                    try:
                        temporary.unlink(missing_ok=True)
                    except OSError:
                        pass  # Preserve the original read/write error for the caller.
            return updated
