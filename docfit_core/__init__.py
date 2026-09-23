"""Safe document inspection helpers used by HWP AutoDocFit."""

from .hwpx import (
    HwpxLimits,
    HwpxSecurityError,
    compare_documents,
    export_markdown,
    inspect_hwpx,
    validate_hwpx,
)
from .kordoc_bridge import (
    KordocUnavailableError,
    analyze_form,
    analyze_tables,
    compare_documents as compare_documents_advanced,
    engine_version as kordoc_engine_version,
    export_advanced_markdown,
    export_common_ir,
    export_rag_chunks,
    fill_form,
    generate_hwpx,
    lint_document,
    parse_document,
    patch_document,
    render_preview,
)

__all__ = [
    "HwpxLimits",
    "HwpxSecurityError",
    "compare_documents",
    "export_markdown",
    "inspect_hwpx",
    "validate_hwpx",
    "KordocUnavailableError",
    "analyze_form",
    "analyze_tables",
    "compare_documents_advanced",
    "kordoc_engine_version",
    "export_advanced_markdown",
    "export_common_ir",
    "export_rag_chunks",
    "fill_form",
    "generate_hwpx",
    "lint_document",
    "parse_document",
    "patch_document",
    "render_preview",
]
