"""계획 실행과 되돌리기. 덮어쓰기는 절대 하지 않고(os.replace 금지) 이름만 바꾼다."""
from __future__ import annotations

import os
import uuid

from .check import _key


class PlanStaleError(RuntimeError):
    """미리보기 뒤 파일이 바뀌었거나 사라짐."""


def _rename_no_overwrite(src, dst):
    # Windows의 os.rename은 대상이 있으면 실패하지만, 다른 OS는 덮어쓰므로 먼저 확인한다.
    if os.path.lexists(dst) and _key(src) != _key(dst):
        raise FileExistsError(dst)
    os.rename(src, dst)


def _temp_name(path):
    return os.path.join(os.path.dirname(path), f".rename-tmp-{uuid.uuid4().hex[:12]}")


def _run_moves(moves, history, run_id, *, stop_on_error=True, rename=_rename_no_overwrite):
    """moves: [(item_id, src, dst)]. 연쇄(A→B, B→C)는 순서대로, 순환(A↔B)·대소문자만 바꿈은 임시 이름을 거친다."""
    pending = {item_id: [src, dst] for item_id, src, dst in moves}
    done, failed = [], []

    def step(item_id, src, dst, final):
        history.write(dict(op="intent", run=run_id, item=item_id, src=src, dst=dst, final=final))
        rename(src, dst)
        history.write(dict(op="done", run=run_id, item=item_id, src=src, dst=dst))

    while pending:
        sources = {_key(src): item_id for item_id, (src, _) in pending.items()}
        ready = [item_id for item_id, (_, dst) in pending.items() if _key(dst) not in sources]
        if not ready:
            # 순환 또는 대소문자만 바뀜: 하나를 임시 이름으로 비켜 둔다.
            item_id = next(iter(pending))
            src, dst = pending[item_id]
            temp = _temp_name(src)
            try:
                step(item_id, src, temp, False)
            except OSError as error:
                history.write(dict(op="fail", run=run_id, item=item_id, reason=_reason(error)))
                failed.append(dict(id=item_id, reason=_reason(error)))
                del pending[item_id]
                if stop_on_error:
                    break
                continue
            pending[item_id][0] = temp
            continue
        stop = False
        for item_id in ready:
            src, dst = pending.pop(item_id)
            try:
                step(item_id, src, dst, True)
                done.append(dict(id=item_id, path=dst))
            except OSError as error:
                history.write(dict(op="fail", run=run_id, item=item_id, reason=_reason(error)))
                failed.append(dict(id=item_id, reason=_reason(error)))
                if stop_on_error:
                    stop = True
                    break
        if stop:
            break
    # 멈췄을 때 임시 이름에 남은 항목은 원래 이름으로 돌려놓는다.
    for item_id, (src, _) in list(pending.items()):
        original = next(s for i, s, _ in moves if i == item_id)
        if src != original:
            try:
                step(item_id, src, original, False)
            except OSError:
                pass
    skipped = [item_id for item_id in pending]
    return done, failed, skipped


def _reason(error):
    if isinstance(error, FileExistsError):
        return "같은 이름의 파일이 이미 있습니다."
    if isinstance(error, PermissionError):
        return "파일이 열려 있거나 권한이 없습니다."
    if isinstance(error, FileNotFoundError):
        return "파일을 찾을 수 없습니다."
    return str(error) or error.__class__.__name__


def execute_plan(plan, history, *, stop_on_error=True, stat=os.stat, rename=_rename_no_overwrite):
    """계획의 ok 항목만 실행한다. 미리보기 뒤 파일이 바뀌었으면 하나도 바꾸지 않고 PlanStaleError."""
    items = [item for item in plan["items"] if item["status"] == "ok"]
    for item in items:
        try:
            st = stat(item["old_path"])
        except OSError:
            raise PlanStaleError(f"파일을 찾을 수 없습니다: {item['old_name']}") from None
        if [st.st_size, int(st.st_mtime * 1000)] != list(item["fingerprint"]):
            raise PlanStaleError(f"미리보기 뒤 파일이 바뀌었습니다: {item['old_name']}")
    run_id = history.new_run("apply", plan_id=plan["plan_id"], count=len(items))
    # 폴더와 그 안 항목을 함께 바꿀 때: 깊은 경로부터(안쪽 이름을 먼저, 폴더는 나중) 바꿔 경로가 꼬이지 않게 한다.
    # 새 이름은 모두 '옛 폴더 안' 기준으로 계산돼 있으므로 이 순서면 그대로 맞다.
    done, failed, skipped = [], [], []
    for group in _depth_groups(items, deepest_first=True):
        if failed and stop_on_error:
            skipped.extend(i["id"] for i in group)
            continue
        d, f, s = _run_moves([(i["id"], i["old_path"], i["new_path"]) for i in group], history, run_id,
                             stop_on_error=stop_on_error, rename=rename)
        done += d
        failed += f
        skipped += s
    history.write(dict(op="end", run=run_id))
    return dict(run_id=run_id, done=done, failed=failed, skipped=skipped)


def _depth(path):
    return os.path.normpath(path).count(os.sep)


def _depth_groups(items, *, deepest_first, key=lambda i: i["old_path"]):
    """경로 깊이가 같은 항목끼리 묶는다(같은 깊이 안의 순환·연쇄는 _run_moves가 처리)."""
    groups = {}
    for item in items:
        groups.setdefault(_depth(key(item)), []).append(item)
    return [groups[d] for d in sorted(groups, reverse=deepest_first)]


def undo(history, run_id, *, rename=_rename_no_overwrite):
    """실행 하나를 되돌린다. 원래 자리가 이미 다른 파일로 차 있으면 그 항목만 건너뛴다."""
    run = history.get(run_id)
    if run is None:
        raise KeyError(run_id)
    undo_id = history.new_run("undo", undo_of=run_id, count=len(run["items"]))
    done, failed, skipped = [], [], []
    # 되돌리기는 얕은 경로부터: 바깥 폴더 이름을 먼저 되돌려야 안쪽 항목의 기록된 경로가 다시 맞는다.
    entries = [dict(item, id=item_id) for item_id, item in run["items"].items()]
    for group in _depth_groups(entries, deepest_first=False, key=lambda i: i["original"]):
        d, f, s = _undo_group(group, history, undo_id, rename)
        done += d
        failed += f
        skipped += s
    history.write(dict(op="end", run=undo_id))
    return dict(run_id=undo_id, done=done, failed=failed, skipped=skipped)


def _undo_group(group, history, undo_id, rename):
    moves = []
    blocked = []
    for item in group:
        item_id = item["id"]
        current = item["current"]
        if item["pending"]:  # 중단된 rename: 실제로 어디 있는지 디스크로 확인한다.
            src, dst = item["pending"]
            current = dst if os.path.lexists(dst) and not os.path.lexists(src) else src
        if current == item["original"]:
            continue
        if not os.path.lexists(current):
            blocked.append(dict(id=item_id, reason="파일을 찾을 수 없습니다."))
            continue
        moves.append((item_id, current, item["original"]))
    sources = {_key(src) for _, src, _ in moves}
    ready = []
    for move in moves:
        if _key(move[2]) not in sources and os.path.lexists(move[2]) and _key(move[1]) != _key(move[2]):
            blocked.append(dict(id=move[0], reason="원래 이름 자리에 다른 파일이 있습니다."))
        else:
            ready.append(move)
    done, failed, skipped = _run_moves(ready, history, undo_id, stop_on_error=False, rename=rename)
    return done, failed + blocked, skipped
