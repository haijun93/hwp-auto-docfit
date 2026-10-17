"""설정의 '글자 상용구'·'본문 상용구' 관리(알파, 2026-10-15). 한/글이 실제로 읽는 사용자 폴더 파일을 고친다.

앱 폴더(C:\\HWP_AUTODOCFIT\\글자상용구) 사본을 덮어쓰면 사용자가 한/글에서 직접 넣은 상용구가 사라지므로,
편집 대상은 %APPDATA%\\HNC\\User\\Hwp\\<버전>\\HWP.IDO다. 그 파일이 없을 때만 앱 사본에서 시작한다.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from docfit_core import hwp_idioms, hwpx_idioms
from docfit_core.hwp_idioms import IdiomError, IdiomStore
from .api_contract import ServiceError


class IdiomService:
    def __init__(self, folder=None, app_copy=None, config_root=None):
        self.folder = Path(folder) if folder else hwp_idioms.hangul_folder()
        self.app_copy = Path(app_copy) if app_copy else None
        # HWPX 설정 파일이 존재하면 이 파일이 읽기 전용 원본이다. 편집은
        # 한/글에서 문서를 직접 고치는 흐름으로 유도하고, 별도 폼 저장은 막는다.
        self.config_root = Path(config_root) if config_root else None
        self.text_config = self.config_root / "글자상용구" / "글자상용구.hwpx" if self.config_root else None
        self.body_config = self.config_root / "본문상용구" / "본문상용구.hwpx" if self.config_root else None

    def _has_hwpx_configs(self):
        return bool(self.config_root and (
            (self.text_config and self.text_config.is_file()) or
            (self.body_config and self.body_config.is_file())
        ))

    def _hwpx_snapshot(self):
        if not self._has_hwpx_configs():
            return None
        try:
            text = hwpx_idioms.parse_hwpx(self.text_config) if self.text_config and self.text_config.is_file() else []
            body = hwpx_idioms.parse_hwpx(self.body_config) if self.body_config and self.body_config.is_file() else []
        except hwpx_idioms.HwpxIdiomError as exc:
            raise ServiceError("INVALID_IDIOM_FILE", str(exc)) from exc
        return {
            "available": True,
            "folder": str(self.config_root),
            "source": "hwpx",
            "config_files": {"text": str(self.text_config), "body": str(self.body_config)},
            "text": [{"key": item["key"], "value": item["value"], "attr": 0} for item in text],
            "body": [{"key": item["key"], "title": item["key"], "value": item["value"],
                      "attr": 1, "has_file": True} for item in body],
        }

    def _store(self):
        if self.folder is None:
            raise ServiceError("HANGUL_FOLDER_MISSING", "한/글 사용자 폴더를 찾지 못했어요. 한/글을 한 번 실행한 뒤 다시 열어 주세요.")
        return IdiomStore(self.folder, self.app_copy)

    def snapshot(self):
        configured = self._hwpx_snapshot()
        if configured is not None:
            return configured
        if self.folder is None:
            return {"available": False, "reason": "한/글 사용자 폴더를 찾지 못했어요. 한/글을 한 번 실행한 뒤 다시 열어 주세요.",
                    "text": [], "body": []}
        store = self._store()
        try:
            data = store.load()
        except IdiomError as exc:
            raise ServiceError("INVALID_IDIOM_FILE", str(exc)) from exc
        return {
            "available": True,
            "folder": str(store.folder),
            "source": "hangul" if store.path.is_file() else "app",
            "text": [{"key": i.key, "value": i.value, "attr": i.attr} for i in data.text],
            "body": [{"key": i.key, "title": i.value, "attr": i.attr, "has_file": store.body_path(i.key).is_file()}
                     for i in data.body],
        }

    def command(self, action, payload):
        if not isinstance(payload, dict):
            raise ServiceError("INVALID_INPUT", "상용구 입력을 확인해 주세요.")
        if action == "get":
            return self.snapshot()
        if self._has_hwpx_configs():
            raise ServiceError(
                "EDIT_HWPX_DIRECTLY",
                "상용구는 설정 HWPX 문서를 한/글에서 직접 수정해 주세요. "
                f"글자상용구: {self.text_config} / 본문상용구: {self.body_config}",
            )
        store = self._store()
        try:
            data = store.load()
            if action == "save_text":
                data.text = hwp_idioms.validate_entries(payload.get("entries"))
            elif action == "save_body":
                entries = payload.get("entries")
                new = hwp_idioms.validate_entries(entries, body=True)
                renames = {e.get("old_key"): e.get("key") for e in entries
                           if isinstance(e, dict) and isinstance(e.get("old_key"), str) and e.get("old_key") != e.get("key")}
                kept = {e.get("old_key") or e.get("key") for e in entries if isinstance(e, dict)}
                for old in data.body:
                    if old.key not in kept:
                        store.remove_body_file(old.key)
                for old, key in renames.items():
                    store.rename_body_file(old, key.strip())
                data.body = new
            elif action == "add_body":
                path = Path(str(payload.get("path") or ""))
                if path.suffix.lower() != ".hwp" or not path.is_file():
                    raise IdiomError("본문 상용구로 쓸 HWP 문서를 골라 주세요.")
                item = hwp_idioms.validate_entries([{"key": payload.get("key"), "title": payload.get("title")}], body=True)[0]
                if any(old.key == item.key for old in data.body):
                    raise IdiomError(f"같은 준말의 본문 상용구가 이미 있습니다: {item.key}")
                store.put_body_file(item.key, path)
                data.body.append(item)
                data.has_body_section = True
            elif action == "import_app":
                if self.app_copy is None or not self.app_copy.is_file():
                    raise IdiomError("앱에 포함된 상용구 파일을 찾지 못했어요.")
                base = hwp_idioms.parse(self.app_copy.read_bytes())
                have = {(i.key, i.value) for i in data.text}   # 같은 준말이 여러 개일 수 있어 (준말, 본말) 쌍으로 본다
                added = [i for i in base.text if (i.key, i.value) not in have]
                data.text += added
                store.save(data)
                return {**self.snapshot(), "added": len(added)}
            else:
                raise ServiceError("INVALID_ACTION", "지원하지 않는 상용구 작업입니다.")
            store.save(data)
        except IdiomError as exc:
            raise ServiceError("INVALID_IDIOM", str(exc)) from exc
        return self.snapshot()

    def apply_hwpx(self, body_converter):
        """HWPX 원본을 한/글 사용자 상용구 파일로 반영한다.

        body_converter(value, output_path)는 본문 텍스트를 한/글 HWP 문서로 저장해야 한다.
        먼저 임시 폴더에서 모든 문서를 생성·검증한 다음 한/글 사용자 폴더에 백업하며 반영한다.
        """
        if self.folder is None:
            raise ServiceError("HANGUL_FOLDER_MISSING", "한/글 사용자 폴더를 찾지 못했어요.")
        if not self._has_hwpx_configs():
            raise ServiceError("CONFIG_MISSING", "상용구 HWPX 설정 파일이 없습니다.")
        try:
            text = hwpx_idioms.parse_hwpx(self.text_config) if self.text_config and self.text_config.is_file() else []
            body = hwpx_idioms.parse_hwpx(self.body_config) if self.body_config and self.body_config.is_file() else []
        except hwpx_idioms.HwpxIdiomError as exc:
            raise ServiceError("INVALID_IDIOM_FILE", str(exc)) from exc

        from docfit_core.hwp_idioms import Idiom, IdiomFile, IdiomStore

        store = IdiomStore(self.folder, self.app_copy)
        with tempfile.TemporaryDirectory(prefix="docfit_idiom_export_") as work:
            staged: list[tuple[str, Path]] = []
            for index, item in enumerate(body):
                output = Path(work) / f"body-{index}.hwp"
                try:
                    body_converter(item["value"], output)
                except Exception as exc:
                    raise ServiceError("BODY_CONVERSION_FAILED", f"'{item['key']}' 본문 문서 생성 실패: {exc}") from exc
                if not output.is_file() or output.stat().st_size == 0:
                    raise ServiceError("BODY_CONVERSION_FAILED", f"'{item['key']}' 본문 HWP 결과가 비어 있습니다.")
                staged.append((item["key"], output))

            previous = store.load()
            data = IdiomFile(
                text=[Idiom(item["key"], item["value"], 0) for item in text],
                body=[Idiom(item["key"], item["key"], 1) for item in body],
                versions=previous.versions,
                has_body_section=True,
            )
            try:
                store.save(data)
                keep = {key for key, _ in staged}
                for old in previous.body:
                    if old.key not in keep:
                        store.remove_body_file(old.key)
                for key, path in staged:
                    store.put_body_file(key, path)
            except Exception as exc:
                raise ServiceError("IDIOM_EXPORT_FAILED", f"한/글 상용구 파일 반영 실패: {exc}") from exc
        return self.snapshot()
