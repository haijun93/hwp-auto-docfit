"""노트북(출처·근거 찾기·노트) 요청 중계: 기본은 klib가 직접 추출하고, klib가 못 읽는 형식만 Python이 추출한다.

- klib nb_source_add가 txt·md·hwpx·docx·pptx·xlsx를 직접 읽는다(hwpx·docx는 개요 수준·표 행 포함).
- 구형 hwp·pdf는 타임머신 content_search 추출기로 문단을 만든 뒤 nb_source_add(첫 묶음)·nb_index(나머지 묶음)로 넣는다.
- 원본 파일은 읽기만 한다(쓰기·이동·삭제 없음). AI·네트워크 호출 없음.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from docfit_app.library_bridge import LibraryBridgeError

NOTEBOOK_COMMANDS = frozenset({
    "nb_create", "nb_list", "nb_update", "nb_delete",
    "nb_source_add", "nb_source_from_item", "nb_source_item",
    "nb_source_list", "nb_source_remove", "nb_source_paragraphs",
    "nb_index", "nb_search", "nb_transform",
    "nb_note_save", "nb_note_list", "nb_note_delete", "nb_export_md", "nb_compare",
})
# klib(Rust)가 직접 읽지 못해 Python이 추출하는 형식.
PYTHON_EXTRACT_EXTENSIONS = frozenset({"hwp", "pdf"})
SOURCE_EXTENSIONS = frozenset({"hwpx", "hwp", "docx", "pdf", "xlsx", "pptx", "txt", "md"})
INDEX_BATCH_BYTES = 40 * 1024  # 파이프 요청 한도(64 KiB)보다 작게 나눠 보낸다.
MAX_PARAGRAPH_CHARS = 4000
# content_search 위계 이름 → klib 문단 수준(klib 기호 수준과 맞춤: Ⅰ.=1, 1.=2, □=3, ○=4, -=5, *=6).
LEVEL_NUMBERS = {
    "document_title": 1, "chapter": 1, "section": 2, "topic": 2,
    "square": 3, "circle": 4, "dash": 5, "asterisk": 6,
}


def extract_source_paragraphs(path):
    """문서에서 [{text, level, table, location}] 목록을 만든다. 원본은 읽기만 한다."""
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
        result.append({
            "text": text[:MAX_PARAGRAPH_CHARS],
            "level": LEVEL_NUMBERS.get(record.level, 0),
            "table": bool(record.is_table_cell or record.level == "table_cell"),
            "location": str(label) if label else "",
        })
    if not result:
        raise ValueError("본문 텍스트가 없음")
    return result


def _batches(paragraphs, limit=INDEX_BATCH_BYTES):
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


def _source_label(source):
    """출처 표시 이름: 표시 이름, 원본 파일명이 다르면 괄호로 덧붙인다(전체 경로는 넣지 않음)."""
    if not isinstance(source, dict):
        return "삭제된 출처"
    name = str(source.get("display_name") or "").strip()
    origin = str(source.get("origin") or "").strip()
    file_name = os.path.basename(origin.replace("\\", "/")) if origin else ""
    if not name:
        return file_name or "출처"
    return f"{name} ({file_name})" if file_name and file_name != name else name


def needs_python_extraction(path):
    return Path(os.fspath(path)).suffix.lower().lstrip(".") in PYTHON_EXTRACT_EXTENSIONS


class NotebookService:
    def __init__(self, bridge, *, extractor=extract_source_paragraphs):
        self.bridge = bridge
        self.extractor = extractor

    def add_source(self, notebook_id, path, *, display_name=None):
        """Python으로 추출한 문단을 klib에 넣는다. 첫 묶음은 출처 등록과 함께, 나머지는 nb_index로 덧붙인다."""
        path = os.path.abspath(os.fspath(path))
        if not os.path.isfile(path):
            return {"ok": False, "message": "출처 파일을 찾을 수 없습니다."}
        try:
            paragraphs = self.extractor(path)
        except Exception as exc:
            return {"ok": False, "message": f"본문을 읽지 못했습니다: {exc or exc.__class__.__name__}"}
        batches = list(_batches(paragraphs))
        request = {"cmd": "nb_source_add", "notebook_id": notebook_id, "source_path": path,
                   "paragraphs": batches[0]}
        if display_name:
            request["display_name"] = display_name
        added = self.bridge.request(request)
        if not added.get("ok"):
            return added
        source_id = added.get("id")
        for batch in batches[1:]:
            result = self.bridge.request({"cmd": "nb_index", "notebook_id": notebook_id,
                                          "source_id": source_id, "paragraphs": batch})
            if not result.get("ok"):
                return dict(result, id=source_id)
        return {"ok": True, "id": source_id, "paragraph_count": len(paragraphs)}

    def _require(self, request):
        result = self.bridge.request(request)
        if not isinstance(result, dict) or not result.get("ok"):
            message = result.get("message") if isinstance(result, dict) else None
            raise LibraryBridgeError(message or "노트북 정보를 읽지 못했습니다.")
        return result

    def export_document(self, notebook_id, note_id, *, compare_query=None, compare_source_ids=None, per_source=3):
        """klib의 노트·출처·출처 비교 응답을 HWPX 내보내기 자료(docfit_core.notebook_hwpx 형식)로 모은다."""
        notes = self._require({"cmd": "nb_note_list", "notebook_id": notebook_id}).get("notes") or []
        note = next((n for n in notes if isinstance(n, dict) and n.get("id") == note_id), None)
        if note is None:
            raise LibraryBridgeError("노트를 찾을 수 없습니다.")
        sources = {s.get("id"): s for s in
                   self._require({"cmd": "nb_source_list", "notebook_id": notebook_id}).get("sources") or []
                   if isinstance(s, dict)}
        notebook_name = ""
        try:
            listed = self.bridge.request({"cmd": "nb_list"})
            notebook_name = next((str(n.get("name") or "") for n in listed.get("notebooks") or []
                                  if isinstance(n, dict) and n.get("id") == notebook_id), "")
        except Exception:
            notebook_name = ""

        locations = {}
        citations = []
        for item in note.get("citations") or []:
            if not isinstance(item, dict):
                continue
            source_id, ordinal = item.get("source_id"), item.get("paragraph_ordinal")
            if source_id in sources and source_id not in locations:
                try:  # 인용 위치(쪽·표 등)는 있으면 쓰고, 못 읽어도 내보내기는 계속한다.
                    rows = self.bridge.request({"cmd": "nb_source_paragraphs", "notebook_id": notebook_id,
                                                "source_id": source_id}).get("paragraphs") or []
                    locations[source_id] = {r.get("ordinal"): r.get("location") or "" for r in rows if isinstance(r, dict)}
                except Exception:
                    locations[source_id] = {}
            citations.append({
                "quote": item.get("quote") or "",
                "source_name": _source_label(sources.get(source_id)),
                "paragraph": ordinal + 1 if isinstance(ordinal, int) else None,
                "location": locations.get(source_id, {}).get(ordinal, ""),
            })

        compare = None
        query = (compare_query or "").strip() if isinstance(compare_query, str) else ""
        if query:
            request = {"cmd": "nb_compare", "notebook_id": notebook_id, "query": query, "per_source": per_source}
            if compare_source_ids is not None:
                request["source_ids"] = compare_source_ids
            groups = []
            for group in self._require(request).get("groups") or []:
                if not isinstance(group, dict):
                    continue
                hits = [{"paragraph": h.get("ordinal") + 1 if isinstance(h.get("ordinal"), int) else None,
                         "location": h.get("location") or "", "body": h.get("body") or ""}
                        for h in group.get("hits") or [] if isinstance(h, dict)]
                groups.append({"source_name": _source_label(group), "hits": hits})
            compare = {"query": query, "groups": groups}
        return {"title": note.get("title") or "", "notebook": notebook_name, "tags": note.get("tags") or [],
                "body": note.get("body") or "", "citations": citations, "compare": compare}

    def export_hwpx(self, request, target, *, base_hwpx=None):
        """노트를 한/글 HWPX로 target에 저장한다(COM 없음). target은 호출자가 저장 대화상자로 확인한 경로다."""
        from docfit_core.abbreviation_doc import default_base_hwpx
        from docfit_core.notebook_hwpx import NotebookHwpxError, build_notebook_hwpx

        notebook_id, note_id = request.get("notebook_id"), request.get("note_id")
        if not isinstance(notebook_id, int) or not isinstance(note_id, int):
            return {"ok": False, "message": "notebook_id와 note_id가 필요합니다."}
        if Path(os.fspath(target)).suffix.lower() != ".hwpx":
            return {"ok": False, "message": "HWPX 파일로 저장해 주세요."}
        base = base_hwpx or default_base_hwpx()
        if base is None:
            return {"ok": False, "message": "앱 내장 기본 서식 문서를 찾지 못했습니다."}
        per_source = request.get("per_source", 3)
        try:
            doc = self.export_document(
                notebook_id, note_id, compare_query=request.get("compare_query"),
                compare_source_ids=request.get("compare_source_ids"),
                per_source=per_source if isinstance(per_source, int) else 3)
            path = build_notebook_hwpx(doc, base, target)
        except (LibraryBridgeError, NotebookHwpxError) as exc:
            return {"ok": False, "message": str(exc)}
        return {"ok": True, "path": str(path)}

    def handle(self, request):
        """notebook(request) 진입점: hwp·pdf 출처 추가는 Python 추출, 나머지 nb_* 명령은 klib로 그대로 보낸다."""
        if not isinstance(request, dict):
            raise LibraryBridgeError("노트북 요청은 JSON 객체여야 합니다.")
        cmd = request.get("cmd")
        if cmd not in NOTEBOOK_COMMANDS:
            raise LibraryBridgeError("허용되지 않은 노트북 명령입니다.")
        path = request.get("source_path")
        if (cmd == "nb_source_add" and isinstance(path, str) and "paragraphs" not in request
                and needs_python_extraction(path)):
            return self.add_source(request.get("notebook_id"), path, display_name=request.get("display_name"))
        if cmd == "nb_source_from_item" and "paragraphs" not in request:
            return self.add_source_from_item(request)
        return self.bridge.request(request)

    def add_source_from_item(self, request):
        """자료함 항목을 출처로 추가. 구형 hwp·pdf 항목은 Python으로 추출해 넘기고, 이미 출처면 klib가 재사용해 알려 준다."""
        item = self.bridge.request({"cmd": "item_get", "id": request.get("item_id")})
        path = item.get("source_path") if isinstance(item, dict) else None
        if not (item.get("ok") and isinstance(path, str) and path and needs_python_extraction(path)):
            return self.bridge.request(request)
        path = os.path.abspath(os.fspath(path))
        if not os.path.isfile(path):
            return {"ok": False, "message": "출처 파일을 찾을 수 없습니다."}
        try:
            paragraphs = self.extractor(path)
        except Exception as exc:
            return {"ok": False, "message": f"본문을 읽지 못했습니다: {exc or exc.__class__.__name__}"}
        batches = list(_batches(paragraphs))
        if not batches:
            return {"ok": False, "message": "출처에서 본문 문단을 찾지 못했습니다."}
        added = self.bridge.request(dict(request, paragraphs=batches[0]))
        if not added.get("ok") or added.get("reused"):
            return added
        source_id = added.get("id")
        for batch in batches[1:]:
            result = self.bridge.request({"cmd": "nb_index", "notebook_id": request.get("notebook_id"),
                                          "source_id": source_id, "paragraphs": batch})
            if not result.get("ok"):
                return dict(result, id=source_id)
        return {"ok": True, "id": source_id, "paragraph_count": len(paragraphs), "reused": False}
