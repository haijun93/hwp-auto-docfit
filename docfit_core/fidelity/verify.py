"""패치 결과 다층 검증: 패키지 → 원문 보존 → 구조·내용 → (선택) 한/글 실제 열기.

같은 분석기로 입력과 출력을 읽기만 하면 두 쪽에서 똑같이 빠뜨리는 항목을 놓친다. 그래서 원문 보존은
압축 항목의 원본 바이트로, 구조는 원문 시작 태그 바이트(요소 이름·모든 속성 포함)로 비교한다. 한/글 열기
검사는 COM을 쓰므로 호출자가 native(결과 경로) 함수를 넘긴다.

판정: 검증된 완전 일치 / 허용한 변화만 확인 / 부분 적용 / 검증 불가 / 실패.
"""

from __future__ import annotations

from ..hwpx import validate_hwpx
from .package import PackageSnapshot
from .source_map import build_source_map

# 중앙 디렉터리 레코드에서 내용에 따라 달라지는 필드(플래그·CRC·크기·위치)를 뺀 나머지는 같아야 한다.
_CENTRAL_VARIABLE = [(8, 10), (16, 28), (42, 46)]


def _central_fixed(raw: bytes) -> bytes:
    data = bytearray(raw)
    for start, end in _CENTRAL_VARIABLE:
        data[start:end] = b"\0" * (end - start)
    return bytes(data)


def _layer(name, ok, details=None, status=None):
    return {"layer": name, "status": status or ("passed" if ok else "failed"), "details": details or []}


def verify_patch(source, result, patch_report=None, native=None) -> dict:
    source = source if isinstance(source, PackageSnapshot) else PackageSnapshot.load(source)
    layers = []
    # 1. 패키지
    problems = []
    try:
        validate_hwpx(result)
        output = PackageSnapshot.load(result)
    except Exception as exc:
        layers.append(_layer("패키지", False, [f"결과를 읽지 못함: {exc}"]))
        return {"layers": layers, "verdict": "실패"}
    if list(output.entries) != list(source.entries) or output.central_order != source.central_order:
        problems.append("압축 항목 이름이나 순서가 원본과 다릅니다.")
    if output.prefix != source.prefix or output.eocd[22:] != source.eocd[22:]:
        problems.append("압축 파일 앞부분이나 끝 주석이 원본과 다릅니다.")
    layers.append(_layer("패키지", not problems, problems))
    if problems:
        return {"layers": layers, "verdict": "실패"}
    # 2. 원문 보존
    allowed = set((patch_report or {}).get("changed_parts", []))
    changed = {name for name in source.entries if source.entries[name].local != output.entries[name].local}
    problems = [f"고치지 않기로 한 항목이 바뀜: {name}" for name in sorted(changed - allowed)]
    for name in sorted(changed & allowed):
        if _central_fixed(source.entries[name].central) != _central_fixed(output.entries[name].central):
            problems.append(f"바뀐 항목의 이름·날짜·속성이 원본과 다름: {name}")
    kept = len(source.entries) - len(changed)
    layers.append(_layer("원문 보존", not problems,
                         problems or [f"고치지 않은 항목 {kept}개는 원본 압축 바이트 그대로"]))
    # 3. 구조·내용
    problems = []
    targets = {(item["part"], item["object"]): item for item in (patch_report or {}).get("applied", [])}
    for name in sorted(changed & allowed):
        before = build_source_map(name, source.read(name))
        after = build_source_map(name, output.read(name))
        target_paths = {path for part, path in targets if part == name}
        caches = tuple(node.path for path in target_paths
                       for node in (before.by_path[path].child("linesegarray") if path in before.by_path else ()))

        def under_target(path):
            return any(path == t or path.startswith(t + "/") for t in target_paths)

        for path, node in before.by_path.items():
            other = after.by_path.get(path)
            if any(path == c or path.startswith(c + "/") for c in caches):
                continue        # 고친 문단의 줄 배치 캐시(와 그 안의 줄 정보)는 지운다(허용한 변화)
            if other is None:
                problems.append(f"{name}{path}: 요소가 사라짐")
                continue
            if (before.data[node.start:node.open_end] != after.data[other.start:other.open_end]
                    and not (node.local == "t" and under_target(path))):
                problems.append(f"{name}{path}: 요소 이름·속성이 바뀜")
            if node.local == "t" and not under_target(path):
                if [before.text(*s) for s in before.segments(node)] != [after.text(*s) for s in after.segments(other)]:
                    problems.append(f"{name}{path}: 고치지 않기로 한 글이 바뀜")
        for path in after.by_path:
            if path not in before.by_path:
                problems.append(f"{name}{path}: 원본에 없던 요소가 생김")
        for path in target_paths:
            item = targets[(name, path)]
            text = after.paragraph_text(after.by_path[path]) if path in after.by_path else None
            if item.get("after") is not None and text != item["after"]:
                problems.append(f"{name}{path}: 바꾼 글이 요청과 다름")
    layers.append(_layer("구조·내용", not problems,
                         problems or [f"바꾼 문단 {len(targets)}개 외 구조·글자 변화 없음"]))
    # 4. 한/글 실제 열기(선택)
    if native is None:
        layers.append(_layer("한/글 열기", True, ["실행하지 않음"], status="not_run"))
    else:
        try:
            outcome = native(str(result)) or {}
            layers.append(_layer("한/글 열기", bool(outcome.get("opened")), [outcome]))
        except Exception as exc:
            layers.append(_layer("한/글 열기", False, [f"한/글 열기 확인 실패: {exc}"]))
    failed = any(layer["status"] == "failed" for layer in layers)
    if failed:
        verdict = "실패"
    elif (patch_report or {}).get("status") == "partial":
        verdict = "부분 적용"
    elif not changed:
        verdict = "검증된 완전 일치"
    else:
        verdict = "허용한 변화만 확인"
    notes = []
    if layers[-1]["status"] == "not_run":
        notes.append("한/글에서 열어 보는 검사는 하지 않았습니다.")
    return {"layers": layers, "verdict": verdict, "notes": notes,
            "changed_parts": sorted(changed), "result_sha256": output.sha256}
