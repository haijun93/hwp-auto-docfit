"""Shared abbreviation operations for Flutter and the fallback Tk dialog."""

import os
from copy import deepcopy
from pathlib import Path

from docfit_core import abbreviation_doc as doc
from docfit_core import abbreviations as registry

from .api_contract import ServiceError


class AbbreviationService:
    def __init__(self, settings, document_root=None, base_hwpx=None, opener=None):
        self.settings = settings
        # 준말 관리 HWPX 문서가 있는 앱 폴더(기본 C:\HWP_AUTODOCFIT). 시험에서는 임시 폴더를 넘긴다.
        if document_root is None:
            from docfit_core.format_samples import APP_HOME
            document_root = APP_HOME
        self.document_root = Path(document_root)
        self.base_hwpx = base_hwpx
        self._opener = opener

    @staticmethod
    def _editable(running):
        if running:
            raise ServiceError("JOB_RUNNING", "작업 중에는 준말을 바꿀 수 없습니다.")

    @staticmethod
    def _entries(settings):
        entries = settings.get("abbreviations", {})
        if not isinstance(entries, dict):
            raise ServiceError("INVALID_REGISTRY", "저장된 준말 등록표를 확인해 주세요.")
        return deepcopy(entries)

    def user_entries(self):
        return registry.normalize(self._entries(self.settings.read()))

    def defaults_enabled(self):
        return bool(self.settings.read().get("abbreviation_defaults", True))

    @staticmethod
    def _label(spec):
        try:
            return registry.describe(spec)[1]
        except (KeyError, TypeError, ValueError):
            return "저장된 서식 (전체 설정에서 확인해 주세요.)"

    def snapshot(self, *, running=False):
        settings = self.settings.read()
        user = registry.normalize(self._entries(settings))
        use_defaults = bool(settings.get("abbreviation_defaults", True))
        # 설정 파일에 키가 없으면 앱 기본값("document")을 따른다(엔진의 설정_불러오기와 같은 규칙).
        source = doc.source_of({"abbreviation_source": "document", **settings})
        path = doc.document_path(self.document_root)
        document = {"path": str(path), "exists": path.is_file(), "errors": []}
        effective = registry.merge_with_defaults(user, use_defaults)
        if source == "document" and path.is_file():
            # 화면도 작업과 같이 매번 문서를 새로 읽는다(문서가 아직 없으면 첫 작업 때 설정 값으로 만들어진다).
            own, document["errors"], readable = doc.read_document(path)
            if readable:
                user = own
                effective = registry.normalize(registry.DEFAULT_ENTRIES) if use_defaults else {}
                effective.update(user)
        return {
            "use_defaults": use_defaults,
            "running": bool(running),
            "source": source,
            "document": document,
            "entries": [{"key": key, **deepcopy(spec), "builtin": key not in user,
                         "label": self._label(spec)}
                        for key, spec in sorted(effective.items())],
            "format_kinds": dict(registry.FORMAT_KINDS),
        }

    def document_command(self, action, *, running=False):
        """준말 관리 HWPX 문서: create(없으면 만들기)·open(한/글에서 열기)·reload(다시 읽기)·use_document·use_settings."""
        if action not in ("create", "open", "reload", "use_document", "use_settings"):
            raise ServiceError("INVALID_INPUT", "준말 문서 작업을 확인해 주세요.")
        if action in ("use_document", "use_settings"):
            self._editable(running)
            source = "document" if action == "use_document" else "settings"
            self.settings.update(lambda settings: settings.update(abbreviation_source=source))
        if action in ("create", "open", "use_document"):
            path = doc.ensure_document(self.settings.read(), self.document_root, self.base_hwpx)
            if path is None:
                raise ServiceError("DOCUMENT_UNAVAILABLE", "준말 문서를 만들지 못했어요. 앱 폴더 권한을 확인해 주세요.")
            if action == "open":
                (self._opener or os.startfile)(str(path))
        return self.snapshot(running=running)

    def save(self, key, kind, value, original_key="", *, running=False):
        self._editable(running)
        if not all(isinstance(item, str) for item in (key, kind, value, original_key)):
            raise ServiceError("INVALID_INPUT", "준말과 본말을 문자열로 입력해 주세요.")

        def change(settings):
            entries = self._entries(settings)
            clean = registry.clean_key(key)
            if original_key and original_key not in registry.normalize(entries):
                raise ServiceError("NOT_FOUND", "수정할 준말이 없어졌습니다. 목록을 다시 불러와 주세요.")
            if clean in entries and clean != original_key:
                raise ServiceError("DUPLICATE_KEY", "이미 등록된 준말입니다. 해당 항목을 수정해 주세요.")
            if original_key and clean != original_key:
                entries[clean] = entries.pop(original_key)
            updated, error = registry.upsert(entries, key, kind, value)
            if error:
                raise ServiceError("INVALID_INPUT", error)
            settings["abbreviations"] = updated

        self.settings.update(change)
        return self.snapshot(running=running)

    def delete(self, key, *, running=False):
        self._editable(running)
        if not isinstance(key, str):
            raise ServiceError("INVALID_INPUT", "삭제할 준말을 선택해 주세요.")

        def change(settings):
            entries = self._entries(settings)
            if key not in entries:
                raise ServiceError("NOT_FOUND", "사용자 등록 준말만 삭제할 수 있습니다.")
            del entries[key]
            settings["abbreviations"] = entries

        self.settings.update(change)
        return self.snapshot(running=running)

    def set_defaults(self, enabled, *, running=False):
        self._editable(running)
        if not isinstance(enabled, bool):
            raise ServiceError("INVALID_INPUT", "기본 준말 사용 여부를 선택해 주세요.")
        self.settings.update(lambda settings: settings.update(abbreviation_defaults=enabled))
        return self.snapshot(running=running)

    def replace_entries(self, entries, *, running=False):
        """Compatibility adapter for the existing Tk dialog's full registry save."""
        self._editable(running)
        if not isinstance(entries, dict):
            raise ServiceError("INVALID_INPUT", "준말 등록표를 확인해 주세요.")
        normalized = registry.normalize(entries)
        self.settings.update(lambda settings: settings.update(abbreviations=normalized))
