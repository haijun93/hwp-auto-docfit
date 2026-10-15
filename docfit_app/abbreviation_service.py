"""Shared abbreviation operations for Flutter and the fallback Tk dialog."""

from copy import deepcopy

from docfit_core import abbreviations as registry

from .api_contract import ServiceError


class AbbreviationService:
    def __init__(self, settings):
        self.settings = settings

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
        effective = registry.merge_with_defaults(user, use_defaults)
        return {
            "use_defaults": use_defaults,
            "running": bool(running),
            "entries": [{"key": key, **deepcopy(spec), "builtin": key not in user,
                         "label": self._label(spec)}
                        for key, spec in sorted(effective.items())],
            "format_kinds": dict(registry.FORMAT_KINDS),
        }

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
