"""Shared table-template management, stored in the existing 표 abbreviation."""
from copy import deepcopy
from pathlib import Path
from zipfile import BadZipFile
from defusedxml import ElementTree as ET
from docfit_core import abbreviations as registry
from docfit_core.table_style import (default_style, describe_style, learn_table_style,
                                     valid_style)
from .api_contract import ServiceError


class TableTemplateService:
    def __init__(self, abbreviations):
        self.abbreviations = abbreviations

    def snapshot(self):
        user = self.abbreviations.user_entries()
        effective = registry.merge_with_defaults(user, self.abbreviations.defaults_enabled())
        style = registry.table_style_of(effective)
        if style is not None and not valid_style(style):
            raise ServiceError("INVALID_TABLE_STYLE", "저장된 표 서식을 확인해 주세요.")
        return {"enabled": style is not None, "builtin": registry.TABLE_KEY not in user,
                "description": describe_style(style) if style else "기본 표 서식 사용 안 함",
                "preview": deepcopy(style) if style else None}

    def command(self, action, payload, *, running=False):
        if not isinstance(payload, dict):
            raise ServiceError("INVALID_INPUT", "표 서식 입력을 확인해 주세요.")
        if action == "get":
            return self.snapshot()
        self.abbreviations._editable(running)
        if action == "learn":
            raw = payload.get("path")
            if not isinstance(raw, str) or not raw or "\x00" in raw:
                raise ServiceError("INVALID_PATH", "예시 HWPX 문서를 선택해 주세요.")
            path = Path(raw)
            if path.suffix.lower() != ".hwpx" or not path.is_file():
                raise ServiceError("INVALID_PATH", "존재하는 HWPX 문서를 선택해 주세요.")
            try:
                style = learn_table_style(path)
            except (ValueError, OSError, BadZipFile, ET.ParseError) as exc:
                raise ServiceError("TABLE_LEARN_FAILED", "예시 표를 읽지 못했습니다. 문서를 확인해 주세요.") from exc
        elif action == "reset":
            style = default_style()
        else:
            raise ServiceError("INVALID_ACTION", "지원하지 않는 표 서식 명령입니다.")

        def update(settings):
            entries = self.abbreviations._entries(settings)
            entries[registry.TABLE_KEY] = {"type": "format", "value": "table", **({"style": style} if action == "learn" else {})}
            settings["abbreviations"] = entries
        self.abbreviations.settings.update(update)
        return self.snapshot()
