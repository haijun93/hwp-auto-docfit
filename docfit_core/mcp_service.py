"""Restricted local MCP document-generation service.

The service accepts AI-authored Markdown, creates a new HWPX using the
bundled kordoc presets, and never edits an input document. User-specific
format profiles and Hancom COM finalization are deliberately separate phases.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path, PureWindowsPath

from docfit_core.hwpx import inspect_hwpx
from docfit_core.kordoc_bridge import PRESET_NAMES, generate_hwpx

MAX_INPUT_CHARS = 1_000_000
_SAFE_NAME = re.compile(r"^[\w가-힣][\w가-힣 .()_-]{0,79}$", re.UNICODE)


def output_directory() -> Path:
    """Return the dedicated output directory; callers cannot choose a path."""
    configured = os.environ.get("DOCFIT_MCP_OUTPUT_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / "Documents" / "HwpAutoDocFit" / "MCP-Output").resolve()


def list_presets() -> list[dict[str, str]]:
    """Expose only generator presets, not arbitrary paths or app internals."""
    return [
        {"id": preset, "label": preset}
        for preset in PRESET_NAMES
    ]


def create_hwpx_from_ai_answer(
    text: str,
    preset: str = "보고서",
    filename: str = "AI 답변",
) -> dict:
    """Create a new HWPX in the fixed MCP output folder and return a summary."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("AI 답변 텍스트를 입력해 주세요.")
    if "\x00" in text:
        raise ValueError("입력에 지원하지 않는 제어 문자가 포함되어 있습니다.")
    if len(text) > MAX_INPUT_CHARS:
        raise ValueError(f"입력은 {MAX_INPUT_CHARS:,}자 이하여야 합니다.")
    if preset not in PRESET_NAMES:
        raise ValueError("지원하지 않는 서식 프리셋입니다. list_format_presets 결과를 사용해 주세요.")
    if not isinstance(filename, str):
        raise ValueError("파일 이름은 문자열이어야 합니다.")
    filename = filename.strip()
    if (not _SAFE_NAME.fullmatch(filename) or filename in {".", ".."}
            or PureWindowsPath(filename + ".hwpx").is_reserved()):
        raise ValueError("파일 이름에는 경로가 아닌 1~80자의 안전한 이름을 입력해 주세요.")

    output_dir = output_directory()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = (output_dir / f"{filename}.hwpx").resolve()
    if target.parent != output_dir or target.exists():
        raise FileExistsError("출력 파일이 이미 있거나 허용된 출력 위치가 아닙니다. 다른 파일 이름을 사용해 주세요.")

    # Generate from an ephemeral Markdown input; do not retain or log the AI text.
    with tempfile.TemporaryDirectory(prefix="docfit-mcp-") as temporary:
        markdown = Path(temporary) / "answer.md"
        markdown.write_text(text, encoding="utf-8", newline="\n")
        staged = Path(temporary) / "validated.hwpx"
        generate_hwpx(markdown, preset, staged)
        inspection = inspect_hwpx(staged)
        # The earlier exists check improves the message, but cannot authorize
        # replacing a path: another writer may create it during generation.
        created = False
        try:
            with staged.open("rb") as source, target.open("xb") as output:
                created = True
                shutil.copyfileobj(source, output)
                output.flush()
                os.fsync(output.fileno())
        except Exception:
            if created:
                target.unlink(missing_ok=True)
            raise

    return {
        "ok": True,
        "path": str(target),
        "preset": preset,
        "paragraph_count": inspection.paragraph_count,
        "table_count": inspection.table_count,
        "image_count": inspection.image_count,
        "text_sha256": inspection.text_sha256,
        "warnings": inspection.warnings,
        "next_step": "이 MVP는 kordoc 기본 프리셋을 적용했습니다. 사용자 저장 서식프로필과 한/글 COM 내어쓰기 후처리는 아직 연결되지 않았습니다.",
    }
