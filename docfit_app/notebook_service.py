"""노트북(출처·근거 찾기·노트) 서비스: 문서 문단 추출 + klib nb_* 파이프 명령 중계.

- 원본 파일은 읽기만 한다(쓰기·이동·삭제 없음).
- 크기·수정 시각이 같으면 다시 추출하지 않고, 실패 사유는 보관한다.
- AI·네트워크 호출 없음. 추출은 타임머신 content_search 추출기를 재사용한다.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from docfit_app.library_bridge import LibraryBridgeError

NOTEBOOK_COMMANDS = frozenset({
    "nb_create", "nb_list", "nb_update", "nb_delete",
    "nb_source_add", "nb_source_list", "nb_source_remove", "nb_source_paragraphs",
    "nb_index", "nb_search", "nb_transform",
    "nb_note_save", "nb_note_list", "nb_note_delete", "nb_export_md",
})
SOURCE_EXTENSIONS = frozenset({"hwpx", "hwp", "docx", "pdf", "xlsx", "pptx", "txt", "md"})
INDEX_BATCH_BYTES = 40 * 1024  # 파이프 요청 한도(64 KiB)보다 작게 나눠 보낸다.
MAX_PARAGRAPH_CHARS = 4000


def extract_source_paragraphs(path):
    """문서에서 [{seq, page, text, level}] 목록을 만든다. 원본은 읽기만 한다."""
    from docfit_core.timemachine import content_search as cs

    path = os.path.abspath(os.fspath(path))
    ext = Path(path).suffix.lower().lstrip(".")
    if ext not in SOURCE_EXTENSIONS:
        raise ValueError("지원하지 않는 형식")
    records = cs.extract_paragraphs(path)
    with cs._EXTRACTED_LOCATIONS_LOCK:
        locations = dict(cs._EXTRACTED_LOCATIONS.get(path, {}))
    result = []
    for record in records:
        text = (record.text or "").strip()
        if not text:
            continue
        label = locations.get(record.paragraph_index, (None, None))[0]
        level = record.level if record.level and record.level != "body" else None
        result.append({
            "seq": len(result) + 1,
            "page": str(label) if label else None,
            "text": text[:MAX_PARAGRAPH_CHARS],
            "level": level,
        })
    if not result:
        raise ValueError("본문 텍스트가 없음")
    return result


def _batches(paragraphs, limit=INDEX_BATCH_BYTES):
    import json
    batch, size = [], 0
    for item in paragraphs:
        item_size = len(json.dumps(item, ensure_ascii=False).encode("utf-8")) + 1
        if batch and size + item_size > limit:
            yield batch
            batch, size = [], 0
        batch.append(item)
        size += item_size
    if batch:
        yield batch


class NotebookService:
    def __init__(self, bridge, *, extractor=extract_source_paragraphs):
        self.bridge = bridge
        self.extractor = extractor
        self._lock = threading.Lock()
        self._signatures = {}  # (notebook_id, abspath) -> (size, mtime_ns, source_id)
        self._failures = {}    # (notebook_id, abspath) -> 사유

    def _send(self, cmd, **payload):
        return self.bridge.request(dict(payload, cmd=cmd))

    def failure_reason(self, notebook_id, path):
        return self._failures.get((notebook_id, os.path.abspath(os.fspath(path))))

    def add_source(self, notebook_id, path, *, display_name=None):
        """출처를 추가한다. 같은 크기·수정 시각이면 재추출하지 않는다."""
        path = os.path.abspath(os.fspath(path))
        key = (notebook_id, path)
        try:
            stat = os.stat(path)
        except OSError as exc:
            return self._fail(key, f"파일을 열 수 없음: {exc.strerror or exc}")
        signature = (stat.st_size, stat.st_mtime_ns)
        with self._lock:
            cached = self._signatures.get(key)
            if cached and cached[:2] == signature:
                return {"ok": True, "skipped": True, "source_id": cached[2]}
        ext = Path(path).suffix.lower().lstrip(".")
        added = self._send(
            "nb_source_add", notebook_id=notebook_id, kind=ext, path=path,
            name=display_name or Path(path).name,
            size=stat.st_size, mtime_ns=stat.st_mtime_ns)
        if not added.get("ok", True):
            return added
        source_id = added.get("source_id", added.get("id"))
        try:
            paragraphs = self.extractor(path)
        except Exception as exc:  # 추출 실패는 사유로 보관
            return self._fail(key, str(exc) or exc.__class__.__name__, source_id=source_id)
        for batch in _batches(paragraphs):
            result = self._send("nb_index", notebook_id=notebook_id, source_id=source_id,
                                paragraphs=batch, replace=batch[0]["seq"] == paragraphs[0]["seq"])
            if not result.get("ok", True):
                return self._fail(key, result.get("message", "색인 실패"), source_id=source_id)
        with self._lock:
            self._signatures[key] = (*signature, source_id)
            self._failures.pop(key, None)
        return {"ok": True, "source_id": source_id, "paragraphs": len(paragraphs)}

    def _fail(self, key, reason, *, source_id=None):
        with self._lock:
            self._failures[key] = reason
            self._signatures.pop(key, None)
        return {"ok": False, "message": reason, "source_id": source_id}

    def handle(self, request):
        """notebook(request) 진입점: add_source 또는 nb_* 명령."""
        if not isinstance(request, dict):
            raise LibraryBridgeError("노트북 요청은 JSON 객체여야 합니다.")
        cmd = request.get("cmd")
        if cmd == "nb_source_add" and request.get("path"):
            return self.add_source(request.get("notebook_id"), request["path"],
                                   display_name=request.get("name"))
        if cmd not in NOTEBOOK_COMMANDS:
            raise LibraryBridgeError("허용되지 않은 노트북 명령입니다.")
        return self.bridge.request(request)
