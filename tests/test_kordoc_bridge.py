import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from docfit_core import kordoc_bridge


class KordocBridgeTest(unittest.TestCase):
    def test_generate_uses_requested_government_preset(self):
        with tempfile.TemporaryDirectory() as folder:
            markdown = Path(folder) / "report.md"
            markdown.write_text("# 제목", encoding="utf-8")
            with patch.object(kordoc_bridge, "run_kordoc") as run:
                target = kordoc_bridge.generate_hwpx(markdown, "보고서")
        arguments = run.call_args.args[0]
        self.assertIn("generate", arguments)
        self.assertEqual(arguments[arguments.index("--preset") + 1], "보고서")
        self.assertEqual(target.suffix, ".hwpx")

    def test_compare_documents_reports_block_changes(self):
        documents = [
            {"blocks": [{"type": "paragraph", "text": "이전 내용"}]},
            {"blocks": [{"type": "paragraph", "text": "새로운 내용"}]},
        ]
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source_a, source_b = folder / "a.hwpx", folder / "b.hwpx"
            source_a.write_bytes(b"a")
            source_b.write_bytes(b"b")
            calls = iter(documents)
            def fake_parse(_source, target, **_kwargs):
                Path(target).write_text(json.dumps(next(calls), ensure_ascii=False), encoding="utf-8")
                return Path(target)
            with patch.object(kordoc_bridge, "parse_document", side_effect=fake_parse):
                report_path = kordoc_bridge.compare_documents(source_a, source_b)
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["blocks_before"], 1)
        self.assertEqual(report["blocks_after"], 1)
        self.assertEqual(report["changes"][0]["operation"], "replace")

    def test_invalid_preset_is_rejected(self):
        with self.assertRaises(ValueError):
            kordoc_bridge.generate_hwpx("input.md", "알 수 없음")


if __name__ == "__main__":
    unittest.main()
