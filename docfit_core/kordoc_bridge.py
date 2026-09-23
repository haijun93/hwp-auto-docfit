"""Optional bridge to the MIT-licensed kordoc v4 document engine.

The desktop editor remains fully functional without Node.js.  Advanced
conversion/generation features are enabled when Node 18+ and npx are present.
"""

from __future__ import annotations

import difflib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

KORDOC_PACKAGE = "kordoc@^4"


class KordocUnavailableError(RuntimeError):
    pass


def _npx_command() -> str:
    command = shutil.which("npx.cmd") or shutil.which("npx")
    if not command:
        raise KordocUnavailableError(
            "고급 문서 엔진을 사용하려면 Node.js 18 이상이 필요합니다. "
            "https://nodejs.org 에서 LTS 버전을 설치해 주세요."
        )
    return command


def _startupinfo():
    if os.name != "nt":
        return None
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = 0
    return info


def run_kordoc(arguments: list[str], timeout: int = 600,
                acceptable_codes: tuple[int, ...] = (0, 2)) -> subprocess.CompletedProcess[str]:
    command = [_npx_command(), "-y", KORDOC_PACKAGE, *map(str, arguments)]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        startupinfo=_startupinfo(),
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    # patch는 일부 미적용 항목이 있으면 2를 반환하지만 결과 파일은 정상 생성한다.
    if completed.returncode not in acceptable_codes:
        message = (completed.stderr or completed.stdout or "kordoc 실행 실패").strip()
        raise RuntimeError(message)
    return completed


def engine_version() -> str:
    return run_kordoc(["--version"], timeout=120).stdout.strip()


def parse_document(source: str | Path, target: str | Path, *, output_format: str = "markdown",
                   pages: str | None = None, ocr: bool = False) -> Path:
    args = [str(source), "--format", output_format, "-o", str(target), "--silent"]
    if pages:
        args.extend(["--pages", pages])
    if ocr:
        # 텍스트층이 없는 페이지만 내장 OCR로 인식한다(스캔 PDF 대응). 텍스트층이
        # 있으면 건드리지 않으므로 일반 PDF에도 안전하게 항상 켤 수 있다.
        args.append("--ocr")
    run_kordoc(args)
    return Path(target)


def export_advanced_markdown(source: str | Path, pages: str | None = None) -> Path:
    source = Path(source)
    suffix = ".pages.md" if pages else ".advanced.md"
    return parse_document(source, source.with_name(source.stem + suffix), pages=pages)


def export_common_ir(source: str | Path) -> Path:
    source = Path(source)
    return parse_document(source, source.with_name(source.stem + ".document.json"), output_format="json")


def export_rag_chunks(source: str | Path) -> Path:
    source = Path(source)
    return parse_document(source, source.with_name(source.stem + ".chunks.json"), output_format="chunks")


def analyze_tables(source: str | Path) -> Path:
    source = Path(source)
    target = source.with_name(source.stem + ".tables.json")
    run_kordoc(["tables", str(source), "--cells", "--visual", "none", "-o", str(target), "--silent"])
    return target


def analyze_form(source: str | Path) -> Path:
    source = Path(source)
    target = source.with_name(source.stem + ".form-fields.txt")
    completed = run_kordoc(["fill", str(source), "--dry-run", "--silent"])
    target.write_text((completed.stdout or completed.stderr).strip(), encoding="utf-8")
    return target


def render_preview(source: str | Path) -> Path:
    source = Path(source)
    output_dir = source.with_name(source.stem + "_preview")
    output_dir.mkdir(parents=True, exist_ok=True)
    run_kordoc(["render", str(source), "--format", "png", "-d", str(output_dir), "--silent"])
    return output_dir


def _flatten_blocks(value: Any, prefix: str = "") -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    if isinstance(value, dict):
        kind = str(value.get("type", ""))
        text = value.get("text") or value.get("markdown") or value.get("content")
        if kind and isinstance(text, str):
            blocks.append({"path": prefix, "type": kind, "text": text})
        for key, child in value.items():
            if key not in {"text", "markdown", "content", "images"}:
                blocks.extend(_flatten_blocks(child, f"{prefix}/{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            blocks.extend(_flatten_blocks(child, f"{prefix}/{index}"))
    return blocks


def compare_documents(source_a: str | Path, source_b: str | Path, target: str | Path | None = None) -> Path:
    """Create a block/cell-aware JSON diff from kordoc's common document IR."""
    source_a, source_b = Path(source_a), Path(source_b)
    target = Path(target) if target else source_b.with_name(source_b.stem + ".comparison.json")
    with tempfile.TemporaryDirectory(prefix="docfit_kordoc_diff_") as folder:
        a_path, b_path = Path(folder) / "a.json", Path(folder) / "b.json"
        parse_document(source_a, a_path, output_format="json")
        parse_document(source_b, b_path, output_format="json")
        a_blocks = _flatten_blocks(json.loads(a_path.read_text(encoding="utf-8")))
        b_blocks = _flatten_blocks(json.loads(b_path.read_text(encoding="utf-8")))
    a_text = [f"{b['type']}\t{b['text']}" for b in a_blocks]
    b_text = [f"{b['type']}\t{b['text']}" for b in b_blocks]
    matcher = difflib.SequenceMatcher(None, a_text, b_text, autojunk=False)
    changes = []
    for operation, a1, a2, b1, b2 in matcher.get_opcodes():
        if operation != "equal":
            changes.append({"operation": operation, "before": a_blocks[a1:a2], "after": b_blocks[b1:b2]})
    report = {
        "version": 1,
        "before": str(source_a),
        "after": str(source_b),
        "blocks_before": len(a_blocks),
        "blocks_after": len(b_blocks),
        "similarity": matcher.ratio(),
        "changes": changes,
    }
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def fill_form(source: str | Path, fields: str, target: str | Path | None = None) -> Path:
    source = Path(source)
    target = Path(target) if target else source.with_name(source.stem + "(양식채움).hwpx")
    run_kordoc(["fill", str(source), "--fields", fields, "--require-unique", "-o", str(target), "--silent"])
    return target


def patch_document(source: str | Path, edited_markdown: str | Path,
                   target: str | Path | None = None) -> Path:
    source = Path(source)
    target = Path(target) if target else source.with_name(source.stem + "(텍스트패치)" + source.suffix)
    run_kordoc(["patch", str(source), str(edited_markdown), "-o", str(target), "--silent"])
    return target


def lint_document(source: str | Path) -> Path:
    source = Path(source)
    report = source.with_name(source.stem + ".lint.json")
    with tempfile.TemporaryDirectory(prefix="docfit_kordoc_lint_") as folder:
        markdown = Path(folder) / "document.md"
        parse_document(source, markdown)
        completed = run_kordoc(["lint", str(markdown), "--json", "--munche"], acceptable_codes=(0, 1))
        report.write_text(completed.stdout or "[]", encoding="utf-8")
    return report


PRESET_NAMES = {"보고서": "보고서", "계획서": "계획서", "기안문": "기안문"}


def generate_hwpx(markdown: str | Path, preset: str, target: str | Path | None = None,
                   *, image_dir: str | Path | None = None) -> Path:
    markdown = Path(markdown)
    if preset not in PRESET_NAMES:
        raise ValueError(f"지원하지 않는 프리셋입니다: {preset}")
    target = Path(target) if target else markdown.with_name(markdown.stem + f"({preset}).hwpx")
    args = ["generate", str(markdown), "-o", str(target), "--preset", PRESET_NAMES[preset], "--silent"]
    if image_dir:
        # kordoc generate는 --image-dir을 줘야만 마크다운의 이미지 참조를 실제
        # 바이트로 읽어 HWPX에 임베드한다(없으면 자리표시만 남고 이미지가 사라짐).
        args.extend(["--image-dir", str(image_dir)])
    run_kordoc(args)
    return target
