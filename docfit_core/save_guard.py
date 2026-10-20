"""HWPX 저장 결과 빈 문서·본문 급감 방지(fail-closed) 및 한/글 COM 시험 잠금 유틸리티."""

from __future__ import annotations

import contextlib
from datetime import datetime
import os
from pathlib import Path
import re
import time
from zipfile import BadZipFile, ZipFile

from defusedxml import ElementTree as ET


DEFAULT_COM_LOCK_PATH = Path(r"C:\HWP_AUTODOCFIT\.com-test.lock")
_SECTION_NAME_RE = re.compile(r"^Contents/section\d+\.xml$")


def _local_name(tag_name: str) -> str:
    return tag_name.rsplit("}", 1)[-1] if "}" in tag_name else tag_name


def count_hwpx_nonspace_chars(hwpx_path: str | Path) -> int:
    """HWPX 패키지의 모든 구역(Contents/section*.xml) 내 공백 제외 본문·표 글자 수를 반환한다."""
    path = Path(hwpx_path)
    if not path.is_file():
        raise RuntimeError(f"저장된 HWPX 파일이 존재하지 않습니다: {path}")
    try:
        with ZipFile(path, "r") as archive:
            section_names = sorted(
                name for name in archive.namelist() if _SECTION_NAME_RE.match(name)
            )
            if not section_names:
                return 0
            total = 0
            for name in section_names:
                root = ET.fromstring(archive.read(name))
                for elem in root.iter():
                    if _local_name(elem.tag) == "t":
                        if elem.text:
                            total += len(re.sub(r"\s+", "", elem.text))
                        for child in elem:
                            if child.tail:
                                total += len(re.sub(r"\s+", "", child.tail))
            return total
    except (BadZipFile, OSError, ET.ParseError) as exc:
        raise RuntimeError(f"저장된 HWPX 파일을 읽을 수 없습니다: {path}") from exc


def verify_saved_hwpx_not_empty(
    saved_path: str | Path,
    reference_path: str | Path | None = None,
    *,
    reference_chars: int | None = None,
    min_ratio: float = 0.5,
) -> dict[str, int]:
    """저장 직후 결과 HWPX의 본문 글자 수가 0이거나 기준 대비 min_ratio 미만이면 RuntimeError를 발생시킨다."""
    saved_chars = count_hwpx_nonspace_chars(saved_path)
    if reference_chars is not None:
        expected_chars = int(reference_chars)
    elif reference_path is not None and Path(reference_path).is_file():
        expected_chars = count_hwpx_nonspace_chars(reference_path)
    else:
        expected_chars = 0

    if saved_chars <= 0:
        raise RuntimeError(
            f"저장된 HWPX 본문 글자 수가 0입니다(빈 문서 저장 감지, 기준 {expected_chars}자): {saved_path}"
        )
    if expected_chars > 0 and saved_chars < expected_chars * min_ratio:
        raise RuntimeError(
            f"저장된 HWPX 본문 글자 수가 비정상적으로 급감했습니다"
            f"(저장 전 {expected_chars}자 → 저장 후 {saved_chars}자): {saved_path}"
        )
    return {"saved_chars": saved_chars, "reference_chars": expected_chars}


@contextlib.contextmanager
def com_test_lock(
    owner: str,
    purpose: str,
    *,
    lock_path: str | Path = DEFAULT_COM_LOCK_PATH,
    timeout_sec: float = 1800.0,
    poll_sec: float = 1.0,
):
    """한/글 COM 동시 실행 충돌을 막는 파일 잠금 컨텍스트 매니저."""
    target = Path(lock_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    env_key = "DOCFIT_COM_LOCK_PATH"
    resolved_str = str(target.resolve())
    if os.environ.get(env_key) == resolved_str and target.is_file():
        yield target
        return

    deadline = time.monotonic() + max(0.0, float(timeout_sec))
    acquired = False

    while True:
        try:
            fd = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                started = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                payload = f"{owner} {started} {purpose}\n".encode("utf-8")
                os.write(fd, payload)
            finally:
                os.close(fd)
            acquired = True
            os.environ[env_key] = resolved_str
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                holder = ""
                try:
                    holder = target.read_text(encoding="utf-8", errors="replace").strip()
                except OSError:
                    pass
                raise TimeoutError(
                    f"COM 잠금 파일 대기 시간({timeout_sec}초)을 초과했습니다: {target} ({holder})"
                )
            time.sleep(max(0.01, float(poll_sec)))

    try:
        yield target
    finally:
        if acquired:
            os.environ.pop(env_key, None)
            try:
                target.unlink()
            except FileNotFoundError:
                pass
