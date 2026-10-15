import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from docfit_core import mcp_service


class McpDocumentServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name) / "out"
        self.env = patch.dict(os.environ, {"DOCFIT_MCP_OUTPUT_DIR": str(self.output)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.temp.cleanup)

    def test_lists_only_builtin_presets(self):
        presets = mcp_service.list_presets()
        self.assertTrue(presets)
        self.assertTrue(all(set(item) == {"id", "label"} for item in presets))

    def test_creates_new_file_in_fixed_output_and_returns_summary(self):
        def generate(markdown, preset, target):
            self.assertEqual(Path(markdown).read_text(encoding="utf-8"), "# 제목\n본문")
            self.assertEqual(preset, "보고서")
            Path(target).write_bytes(b"generated")

        inspection = SimpleNamespace(
            paragraph_count=2, table_count=0, image_count=0,
            text_sha256="abc123", warnings=[],
        )
        with patch.object(mcp_service, "generate_hwpx", side_effect=generate), \
                patch.object(mcp_service, "inspect_hwpx", return_value=inspection):
            result = mcp_service.create_hwpx_from_ai_answer("# 제목\n본문", "보고서", "결과 문서")

        self.assertTrue(result["ok"])
        self.assertEqual(Path(result["path"]), self.output / "결과 문서.hwpx")
        self.assertTrue(Path(result["path"]).is_file())
        self.assertEqual(result["paragraph_count"], 2)
        self.assertIn("아직 연결되지 않았습니다", result["next_step"])

    def test_rejects_invalid_input_preset_filename_and_overwrite(self):
        for args in (
            (" ", "보고서", "ok"),
            ("내용", "unknown", "ok"),
            ("내용", "보고서", "../escape"),
            ("내용", "보고서", "NUL"),
            ("내용", "보고서", "CON.report"),
            ("내용", "보고서", "COM1"),
            ("x" * (mcp_service.MAX_INPUT_CHARS + 1), "보고서", "ok"),
        ):
            with self.subTest(args=args[:2]), self.assertRaises(ValueError):
                mcp_service.create_hwpx_from_ai_answer(*args)

        self.output.mkdir()
        existing = self.output / "existing.hwpx"
        existing.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            mcp_service.create_hwpx_from_ai_answer("내용", "보고서", "existing")
        self.assertEqual(existing.read_bytes(), b"keep")

    def test_racing_output_creation_is_never_overwritten_or_deleted(self):
        self.output.mkdir()
        target=self.output/'race.hwpx'
        def generate(_markdown,_preset,staged):
            # Another writer creates the final file after the early exists check.
            target.write_bytes(b'other writer document')
            Path(staged).write_bytes(b'generated')
        inspection=SimpleNamespace(paragraph_count=1,table_count=0,image_count=0,
                                   text_sha256='abc',warnings=[])
        with patch.object(mcp_service,'generate_hwpx',side_effect=generate), \
             patch.object(mcp_service,'inspect_hwpx',return_value=inspection):
            with self.assertRaises(FileExistsError):
                mcp_service.create_hwpx_from_ai_answer('내용','보고서','race')
        self.assertEqual(target.read_bytes(),b'other writer document')

    def test_failed_generation_removes_partial_output(self):
        def fail(_markdown, _preset, target):
            Path(target).write_bytes(b"partial")
            raise RuntimeError("generation failed")

        with patch.object(mcp_service, "generate_hwpx", side_effect=fail):
            with self.assertRaises(RuntimeError):
                mcp_service.create_hwpx_from_ai_answer("내용", "보고서", "partial")
        self.assertFalse((self.output / "partial.hwpx").exists())


if __name__ == "__main__":
    unittest.main()
