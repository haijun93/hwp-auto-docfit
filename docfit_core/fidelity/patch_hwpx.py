"""같은 서식에서 내용만 바꾸는 최소 변경 패치.

계획(plan)은 원본 해시와 연산 목록이다. 연산마다 대상 문단(파트 + 객체 경로)과 바꾸기 전 글을 함께 적어,
원본이 계획을 만든 뒤 바뀌었거나 글이 다르면 적용하지 않는다. 바뀐 글자 구간만 원문 바이트에서 바꾸고,
그 문단의 줄 배치 캐시(linesegarray)만 지워 한/글이 다시 배치하게 한다. 다른 항목·구간은 원본 그대로다.

연산
- replace_text: 문단의 한 글자 구간 안에 있는 old를 new로 바꾼다(같은 run 서식 유지). 서식이 다른 구간에
  걸친 글은 바꾸지 않는다.
- set_paragraph_text: 문단 글 전체를 new로 바꾼다. 서식 배분 규칙: 새 글은 첫 글자 구간(첫 run)의 서식을
  받고 나머지 구간은 비운다. 빈칸·탭·줄바꿈 요소가 섞인 문단은 바꾸지 않는다.

미적용 연산이 있으면 기본(정확 모드)은 결과 파일을 만들지 않는다(allow_partial=True면 '부분 적용'으로 만든다).
결과 파일은 verify_patch로 다층 검증하고, 실패하면 지운다.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re

from ..hwpx import validate_hwpx
from .package import PackageSnapshot, UnsupportedPackage, write_package
from .source_map import SourceMapError, build_source_map, escape

_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_DERIVED = {"Preview/PrvText.txt": "미리보기 글(Preview/PrvText.txt)은 바뀐 내용을 반영하지 않습니다. "
                                   "한/글에서 다시 저장하면 새로 만들어집니다."}


class PatchError(ValueError):
    """계획 자체를 받을 수 없을 때(형식 오류·원본 불일치 등)."""


def list_objects(source) -> list:
    """고칠 수 있는 문단 목록(계획 작성용): 파트, 객체 경로, 글, 문단 전체 바꾸기 가능 여부."""
    snapshot = source if isinstance(source, PackageSnapshot) else PackageSnapshot.load(source)
    if snapshot.format != "hwpx":
        raise UnsupportedPackage("HWPX 문서만 객체 목록을 만들 수 있습니다.")
    result = []
    for name in snapshot.names():
        if not re.fullmatch(r"Contents/section\d+\.xml", name):
            continue
        source_map = build_source_map(name, snapshot.read(name))
        for p in source_map.paragraphs():
            texts = source_map.paragraph_runs(p)
            text = source_map.paragraph_text(p)
            if not text.strip():
                continue
            result.append({"part": name, "object": p.path, "text": text,
                           "in_table": "/tc[" in p.path,
                           "whole_text_editable": bool(texts) and not any(t.children for t in texts)})
    return result


def _replace_text(source_map, p, op):
    old, new = op.get("old"), op.get("new")
    if not old or new is None:
        return None, "old·new 값이 필요합니다."
    occurrence = int(op.get("occurrence", 1))
    found = []
    for t in source_map.paragraph_runs(p):
        for start, end in source_map.segments(t):
            text = source_map.text(start, end)
            index = text.find(old)
            while index >= 0:
                found.append((start, end, text, index))
                index = text.find(old, index + 1)
    if not found:
        whole = source_map.paragraph_text(p)
        if old in whole:
            return None, "바꿀 글이 서식이 다른 글자 구간에 걸쳐 있어 바꾸지 않았습니다."
        return None, "바꿀 글이 문단에 없습니다(원본이 바뀌었을 수 있음)."
    if not 1 <= occurrence <= len(found):
        return None, f"바꿀 글이 {len(found)}번 나옵니다. occurrence를 1~{len(found)}로 지정하세요."
    if len(found) > 1 and "occurrence" not in op:
        return None, f"바꿀 글이 {len(found)}번 나옵니다. 몇 번째인지 occurrence로 지정하세요."
    start, end, text, index = found[occurrence - 1]
    raw = source_map.data[start:end]
    if b"&" not in raw:
        # 엔티티가 없는 구간은 바뀐 글자만 바이트 위치로 바꾼다.
        prefix = len(text[:index].encode("utf-8"))
        edit = (start + prefix, start + prefix + len(old.encode("utf-8")), escape(new))
    else:
        edit = (start, end, escape(text[:index] + new + text[index + len(old):]))
    return [edit], None


def _set_text(source_map, p, op):
    new, expect = op.get("new"), op.get("expect")
    if new is None or expect is None:
        return None, "new와 바꾸기 전 글(expect)이 모두 필요합니다."
    texts = source_map.paragraph_runs(p)
    if not texts:
        return None, "글자 구간이 없는 문단입니다."
    if any(t.children for t in texts):
        return None, "빈칸·탭·줄바꿈 요소가 섞인 문단은 문단 전체 바꾸기를 지원하지 않습니다."
    if source_map.paragraph_text(p) != expect:
        return None, "문단의 지금 글이 expect와 다릅니다(원본이 바뀌었을 수 있음)."
    first = texts[0]
    opening = source_map.data[first.start:first.open_end]
    if opening.endswith(b"/>"):
        # 빈 요소(<hp:t/>)는 여는·닫는 태그로 바꿔 글을 넣는다.
        tag = first.qname.encode("utf-8")
        edits = [(first.start, first.end, opening[:-2].rstrip() + b">" + escape(new) + b"</" + tag + b">")]
    else:
        edits = [(first.open_end, first.close_start, escape(new))]
    edits += [(t.open_end, t.close_start, b"") for t in texts[1:] if t.close_start > t.open_end]
    return edits, None


def apply_patch(source, plan, target=None, *, allow_partial=False, native=None) -> dict:
    """계획을 적용해 target에 쓰고 결과 보고서를 돌려준다. target이 없으면 검사만 한다(dry run)."""
    from .verify import verify_patch

    snapshot = source if isinstance(source, PackageSnapshot) else PackageSnapshot.load(source)
    if snapshot.format != "hwpx":
        raise UnsupportedPackage("내용 패치는 HWPX 문서만 지원합니다.")
    if not isinstance(plan, dict) or not isinstance(plan.get("operations"), list):
        raise PatchError("계획에는 operations 목록이 있어야 합니다.")
    expected = plan.get("source_sha256")
    if not expected:
        raise PatchError("계획에 원본 해시(source_sha256)가 없습니다.")
    if expected.lower() != snapshot.sha256:
        raise PatchError("원본이 계획을 만든 뒤 바뀌었습니다(해시 불일치). 계획을 다시 만드세요.")
    validate_hwpx(snapshot.path)
    report = {"source": snapshot.path, "source_sha256": snapshot.sha256, "applied": [], "skipped": [],
              "changed_parts": [], "layout_invalidated": [], "warnings": [], "format_rule": "first_run"}
    maps, edits, targeted = {}, defaultdict(list), set()
    for number, op in enumerate(plan["operations"]):
        part, path, kind = op.get("part"), op.get("object"), op.get("op")
        if kind not in ("replace_text", "set_paragraph_text"):
            report["skipped"].append({"index": number, "reason": f"지원하지 않는 연산: {kind}"})
            continue
        if part not in snapshot.entries or not re.fullmatch(r"Contents/section\d+\.xml", part or ""):
            report["skipped"].append({"index": number, "reason": f"본문 파트가 아닙니다: {part}"})
            continue
        try:
            if part not in maps:
                maps[part] = build_source_map(part, snapshot.read(part))
        except SourceMapError as exc:
            report["skipped"].append({"index": number, "reason": str(exc)})
            continue
        source_map = maps[part]
        p = source_map.by_path.get(path)
        if p is None or p.local != "p":
            report["skipped"].append({"index": number, "reason": f"문단을 찾지 못했습니다: {path}"})
            continue
        if (part, path) in targeted:
            report["skipped"].append({"index": number, "reason": "같은 문단을 한 계획에서 두 번 고칠 수 없습니다."})
            continue
        new = op.get("new")
        if isinstance(new, str) and _CONTROL.search(new):
            report["skipped"].append({"index": number, "reason": "줄바꿈·탭 같은 제어 문자는 넣을 수 없습니다."})
            continue
        before = source_map.paragraph_text(p)
        found, reason = (_replace_text if kind == "replace_text" else _set_text)(source_map, p, op)
        if reason:
            report["skipped"].append({"index": number, "reason": reason})
            continue
        targeted.add((part, path))
        edits[part].extend(found)
        cache = p.child("linesegarray")
        if cache:
            edits[part].append((cache[0].start, cache[0].end, b""))
            report["layout_invalidated"].append({"part": part, "object": path})
        after = (op["new"] if kind == "set_paragraph_text"
                 else before.replace(op["old"], op["new"]) if before.count(op["old"]) == 1 else None)
        report["applied"].append({"index": number, "op": kind, "part": part, "object": path,
                                  "before": before, "after": after})
    replacements = {}
    for part, changes in edits.items():
        data = maps[part].data
        changes.sort()
        for (a_start, a_end, _), (b_start, _, _) in zip(changes, changes[1:]):
            if b_start < a_end:
                raise PatchError(f"{part}: 고칠 구간이 겹칩니다.")
        out, cursor = bytearray(), 0
        for start, end, replacement in changes:
            out += data[cursor:start] + replacement
            cursor = end
        out += data[cursor:]
        result = bytes(out)
        new_map = build_source_map(part, result)       # 형식이 깨지면 여기서 멈춘다
        for item in report["applied"]:
            if item["part"] == part and item["after"] is None:
                item["after"] = new_map.paragraph_text(new_map.by_path[item["object"]])
        replacements[part] = result
    report["changed_parts"] = sorted(replacements)
    if replacements:
        report["warnings"] += [message for name, message in _DERIVED.items() if name in snapshot.entries]
    if report["skipped"] and not allow_partial:
        report["status"] = "failed"
        report["verdict"] = "실패"
        report["note"] = "미적용 연산이 있어 결과를 확정하지 않았습니다(정확 모드)."
        return report
    report["status"] = ("no_change" if not report["applied"] else "partial" if report["skipped"]
                        else "complete")
    if target is None:
        report["verdict"] = "검사만 함(결과 파일 없음)"
        return report
    target = Path(target)
    report["target"] = str(target)
    report["result_sha256"] = write_package(snapshot, replacements, target)
    verification = verify_patch(snapshot, target, report, native=native)
    report["verification"] = verification
    report["verdict"] = verification["verdict"]
    if verification["verdict"] == "실패":
        target.unlink(missing_ok=True)
        report["status"] = "failed"
        report["note"] = "검증에 실패해 결과 파일을 지웠습니다."
    return report
