"""Run the local HWP AutoDocFit MCP server over stdio (Claude Desktop)."""

from __future__ import annotations

import sys
from pathlib import Path

# Claude Desktop launches this file directly, so Python otherwise places only
# the scripts directory on sys.path (not the repository root).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # optional dependency, kept out of the desktop app
    print("MCP 의존성이 없습니다. requirements-mcp.txt를 설치해 주세요.", file=sys.stderr)
    raise SystemExit(2) from exc

from docfit_core.mcp_service import create_hwpx_from_ai_answer, list_presets

mcp = FastMCP("HWP AutoDocFit")


@mcp.tool()
def list_format_presets() -> list[dict[str, str]]:
    """List the currently supported built-in HWPX format presets."""
    return list_presets()


@mcp.tool()
def create_document_from_ai_answer(
    answer_markdown: str,
    preset: str = "보고서",
    filename: str = "AI 답변",
) -> dict:
    """Create a new HWPX from AI Markdown; saves only under the configured MCP output folder."""
    return create_hwpx_from_ai_answer(answer_markdown, preset, filename)


if __name__ == "__main__":
    # MCP protocol is the only stdout content; do not add prints here.
    mcp.run(transport="stdio")
