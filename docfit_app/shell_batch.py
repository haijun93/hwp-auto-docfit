"""우클릭 메뉴 여러 파일 일괄 처리를 위한 요청 수집 및 대표 프로세스 실행기."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from docfit_core.file_conversion import CONVERSION_INPUTS


def natural_sort_key(s: str | Path) -> list[int | str]:
    """자연 정렬 키: 문자열 내 숫자를 int로 변환하여 1, 2, 10 순으로 정렬한다."""
    name = Path(s).name.casefold()
    return [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', name)]


def get_batch_dir(batch_name: str, base_dir: Path | str | None = None) -> Path:
    """모음 폴더 경로 반환 및 생성."""
    if base_dir is not None:
        folder = Path(base_dir) / batch_name
    else:
        local_app_data = os.environ.get('LOCALAPPDATA')
        if local_app_data:
            base = Path(local_app_data) / 'HWP_AutoDocFit' / 'shell_batch'
        else:
            base = Path.home() / '.local' / 'share' / 'HWP_AutoDocFit' / 'shell_batch'
        folder = base / batch_name
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def write_request(folder: Path, file_path: str | Path, *, time_func: Callable[[], float] | None = None) -> Path:
    """원자적으로 요청 파일을 작성한다 (.tmp -> .req)."""
    now = (time_func or time.time)()
    pid = os.getpid()
    unique_id = uuid.uuid4().hex[:8]
    req_name = f"req_{now:.6f}_{pid}_{unique_id}.req"
    tmp_name = f".tmp_{now:.6f}_{pid}_{unique_id}.tmp"
    req_path = folder / req_name
    tmp_path = folder / tmp_name

    data = {
        "path": str(Path(file_path).resolve()),
        "pid": pid,
        "time": now,
    }
    tmp_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(req_path)
    return req_path


class BatchLock:
    """O_CREAT | O_EXCL 기반 파일 잠금. 첫 프로세스가 대표(Leader)가 된다."""

    def __init__(self, lock_file: Path):
        self.lock_file = lock_file
        self.fd: int | None = None
        self.acquired: bool = False

    def acquire(self) -> bool:
        try:
            self.fd = os.open(str(self.lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            try:
                os.write(self.fd, f"{os.getpid()}\n{time.time():.6f}".encode("utf-8"))
            except OSError:
                pass
            self.acquired = True
            return True
        except (FileExistsError, OSError):
            self.acquired = False
            return False

    def release(self) -> None:
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None
        if self.acquired:
            try:
                self.lock_file.unlink(missing_ok=True)
            except OSError:
                pass
            self.acquired = False

    def __enter__(self) -> bool:
        return self.acquire()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()


def validate_request_file(
    req_file: Path,
    *,
    user_profile: Path | None = None,
    supported_extensions: set[str] | frozenset[str] | None = None,
) -> Path | None:
    """요청 파일을 검증하여 유효한 대상 파일 경로를 반환한다.

    - 깨진 요청(JSON 오류, 필드 누락 등): .bad 로 확장자 변경 후 None 반환.
    - 사용자 프로필 외부 경로: .bad 로 이동 후 None 반환.
    - 실제 존재하지 않거나 일반 파일이 아닌 경우: None 반환 (제외).
    - 지원 확장자가 아닌 경우: None 반환 (제외).
    """
    if supported_extensions is None:
        supported_extensions = CONVERSION_INPUTS

    try:
        content = req_file.read_text(encoding="utf-8")
        data = json.loads(content)
        if not isinstance(data, dict) or "path" not in data or not isinstance(data["path"], str):
            raise ValueError("유효하지 않은 요청 데이터")
        target_path = Path(data["path"])
    except Exception:
        bad_path = req_file.with_suffix(".bad")
        try:
            req_file.replace(bad_path)
        except OSError:
            pass
        return None

    # 사용자 프로필 경로 확인 (대소문자 무시 비교)
    profile = (user_profile or Path(os.environ.get("USERPROFILE") or Path.home())).resolve()
    resolved_target = target_path.resolve()
    profile_str = str(profile).casefold()
    target_str = str(resolved_target).casefold()
    if not (target_str == profile_str or target_str.startswith(profile_str + os.sep) or target_str.startswith(profile_str + "/")):
        bad_path = req_file.with_suffix(".bad")
        try:
            req_file.replace(bad_path)
        except OSError:
            pass
        return None

    # 실제 존재하는 일반 파일인지 검사
    if not resolved_target.exists() or not resolved_target.is_file() or resolved_target.is_symlink():
        return None

    # 지원 확장자 검사
    if resolved_target.suffix.lower() not in supported_extensions:
        return None

    return resolved_target


def collect_requests(
    folder: Path,
    *,
    quiet_seconds: float = 1.5,
    max_wait_seconds: float = 30.0,
    max_files: int = 200,
    time_func: Callable[[], float] | None = None,
    sleep_func: Callable[[float], None] | None = None,
) -> list[Path]:
    """새 요청이 quiet_seconds 동안 오지 않거나 max_wait_seconds/max_files에 도달할 때까지 수집한다."""
    now_func = time_func or time.monotonic
    nap_func = sleep_func or time.sleep

    start_time = now_func()
    last_arrival_time = start_time
    seen_files: set[Path] = set()

    while True:
        try:
            current_reqs = {p for p in folder.glob("*.req") if p.is_file()}
        except OSError:
            current_reqs = set()

        new_reqs = current_reqs - seen_files
        if new_reqs:
            last_arrival_time = now_func()
            seen_files.update(new_reqs)

        if len(seen_files) >= max_files:
            break

        now = now_func()
        if now - start_time >= max_wait_seconds:
            break

        if seen_files and (now - last_arrival_time >= quiet_seconds):
            break

        nap_func(0.05)

    return sorted(seen_files, key=lambda p: p.name)[:max_files]


def handle_collect(
    batch_name: str,
    files: list[str],
    target: str,
    *,
    output_dir: str | None = None,
    timeout: float = 180.0,
    runner: Any = None,
    argv: list[str] | None = None,
    console: bool = False,
    stdout: Any = None,
    stderr: Any = None,
    base_dir: Path | str | None = None,
    lock_factory: Callable[[Path], Any] | None = None,
    quiet_seconds: float = 1.5,
    max_wait_seconds: float = 30.0,
    max_files: int = 200,
    time_func: Callable[[], float] | None = None,
    sleep_func: Callable[[float], None] | None = None,
    user_profile: Path | None = None,
) -> int:
    """여러 프로세스 요청을 모음 폴더에 모으고, 대표 프로세스가 일괄 처리한다."""
    folder = get_batch_dir(batch_name, base_dir=base_dir)

    for file_path in files:
        write_request(folder, file_path, time_func=time_func)

    lock_file = folder / ".lock"
    lock = (lock_factory or BatchLock)(lock_file)
    if not lock.acquire():
        # 추종자 프로세스는 요청만 남기고 바로 정상 종료
        return 0

    all_results: list[dict[str, Any]] = []
    final_error: str | None = None
    exit_code = 0

    try:
        while True:
            req_files = collect_requests(
                folder,
                quiet_seconds=quiet_seconds,
                max_wait_seconds=max_wait_seconds,
                max_files=max_files,
                time_func=time_func,
                sleep_func=sleep_func,
            )
            if not req_files:
                break

            valid_paths: list[Path] = []
            for req in req_files:
                p = validate_request_file(req, user_profile=user_profile)
                if p is not None:
                    valid_paths.append(p)

            # 중복 제거 및 파일 이름 자연 정렬 (1, 2, 10 순)
            unique_targets: list[str] = []
            seen_keys: set[str] = set()
            for p in valid_paths:
                key = str(p.resolve()).casefold()
                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_targets.append(str(p.resolve()))

            unique_targets.sort(key=natural_sort_key)

            if target == "pdfm" and len(unique_targets) < 2:
                batch_results = [
                    dict(source=p, output=None, status="failed", error="PDF 합치기는 파일이 2개 이상 필요합니다.")
                    for p in unique_targets
                ] or [dict(source=None, output=None, status="failed", error="PDF 합치기는 파일이 2개 이상 필요합니다.")]
                final_error = "PDF 합치기는 파일이 2개 이상 필요합니다."
                exit_code = 2
                all_results.extend(batch_results)
            elif unique_targets:
                if runner is None:
                    from docfit_app.conversion_runner import run_conversion
                    runner = run_conversion
                from docfit_app.cli import _run_with_timeout
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    batch_results = _run_with_timeout(runner, unique_targets, target, output_dir, timeout)
                all_results.extend(batch_results)

            # 이번 회차에서 처리한 요청 파일 삭제
            for req in req_files:
                try:
                    req.unlink(missing_ok=True)
                except OSError:
                    pass

            # 늦게 들어온 요청이 남아있는지 확인
            try:
                remaining = [p for p in folder.glob("*.req") if p.is_file()]
            except OSError:
                remaining = []
            if not remaining:
                break

        # 전체 결과 판정
        statuses = {r["status"] for r in all_results}
        if "cancelled" in statuses:
            exit_code, final_error = 130, "중단됨"
        elif "failed" in statuses:
            exit_code = 1 if exit_code == 0 else exit_code
        elif "success" not in statuses and not all_results:
            exit_code = 3
        elif "skipped" in statuses:
            exit_code = 1 if exit_code == 0 else exit_code

    finally:
        lock.release()

    argv = argv or []
    stdout = stdout or sys.stdout or io.StringIO()
    stderr = stderr or sys.stderr or io.StringIO()

    if "--json" in argv:
        print(json.dumps(dict(exit_code=exit_code, results=all_results, error=final_error), ensure_ascii=False), file=stdout)
    elif "--quiet" not in argv:
        if final_error:
            print(final_error, file=stderr)
        for result in all_results:
            print(f"{result['status']}: {result['source'] or ''} → {result['output'] or result['error']}", file=stdout)

    if "--notify" in argv and not console:
        from docfit_app.cli import notify
        if target == "pdfm":
            successes = [r for r in all_results if r["status"] == "success"]
            if successes and successes[0].get("output"):
                out_name = Path(successes[0]["output"]).name
                notify(f"PDF 하나로 합치기 완료: {out_name}")
            else:
                fail_msgs = [r["error"] for r in all_results if r.get("error")]
                notify(final_error or ("PDF 하나로 합치기 실패\n" + "\n".join(fail_msgs)))
        else:
            success_cnt = sum(r["status"] == "success" for r in all_results)
            failures = [r["error"] for r in all_results if r["status"] != "success" and r.get("error")]
            notify(final_error or f"변환 완료: {success_cnt}개\n" + "\n".join(failures))

    return exit_code
