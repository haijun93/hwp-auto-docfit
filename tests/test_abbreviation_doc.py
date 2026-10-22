"""준말 관리 HWPX 문서(1.80.3) 시험. 한/글 없이 순수 파이썬으로 만들고 읽는다."""
import json
import tempfile
import unittest
from pathlib import Path

from docfit_app.abbreviation_service import AbbreviationService
from docfit_app.api_contract import ServiceError
from docfit_app.settings_service import SettingsService
from docfit_core import abbreviation_doc as doc

BASE = doc.default_base_hwpx()


@unittest.skipIf(BASE is None, "기본 서식 HWPX가 없음")
class AbbreviationDocumentTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = doc.document_path(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def write_lines(self, lines):
        self.path.unlink(missing_ok=True)
        from docfit_core.hwpx_idioms import write_paragraph_document
        return write_paragraph_document(BASE, self.path, lines, lambda _temp: None)

    def test_round_trip_keeps_every_kind(self):
        entries = {"ㅁㅍ": {"type": "text", "value": "마포구청 행정지원과"},
                   **{key: {"type": "format", "value": kind} for key, kind in
                      (("제목1", "title1"), ("제목2", "title2"), ("개요", "overview"), ("로3", "midtitle"),
                       ("붙임", "attach1"), ("붙임2", "attach2"), ("표", "table"))}}
        doc.create_document(BASE, self.path, entries)
        parsed, errors = doc.parse_document(self.path)
        self.assertEqual(errors, [])
        self.assertEqual(parsed, entries)

    def test_existing_document_is_never_overwritten(self):
        doc.create_document(BASE, self.path, {"가": {"type": "text", "value": "첫 값"}})
        doc.create_document(BASE, self.path, {"가": {"type": "text", "value": "다른 값"}})
        self.assertEqual(doc.parse_document(self.path)[0]["가"]["value"], "첫 값")

    def test_multi_paragraph_body_comments_and_idiom_markers(self):
        self.write_lines(["설명 문단은 읽지 않음", "#요약", "첫 문단", "", "※ 주석은 무시", "둘째 문단",
                          "#+ㅁ", "상용구 본말은 요약에 이어짐", "# 개요 ", "[서식: 개요]"])
        parsed, errors = doc.parse_document(self.path)
        self.assertEqual(errors, [])
        self.assertEqual(parsed["요약"]["value"], "첫 문단 둘째 문단 #+ㅁ 상용구 본말은 요약에 이어짐")
        self.assertEqual(parsed["개요"], {"type": "format", "value": "overview"})

    def test_bad_items_are_reported_and_good_items_survive(self):
        self.write_lines(["#", "빈 준말", "#가", "", "#너무긴준말이에요열세자넘음", "x", "#가나 다", "x",
                          "#중", "[서식:중제목]", "#알수", "[서식:없는서식]", "#좋음", "좋은 본말",
                          "#좋음", "중복"])
        parsed, errors = doc.parse_document(self.path)
        self.assertEqual(parsed, {"좋음": {"type": "text", "value": "좋은 본말"}})
        self.assertEqual(len(errors), 7)
        self.assertTrue(any("본말이 비어" in error for error in errors))
        self.assertTrue(any("12자" in error for error in errors))
        self.assertTrue(any("없는서식" in error for error in errors))
        self.assertTrue(any("두 번" in error for error in errors))

    def test_missing_and_broken_document(self):
        self.assertEqual(doc.parse_document(self.path)[0], {})
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(b"not a zip")
        parsed, errors = doc.parse_document(self.path)
        self.assertEqual(parsed, {})
        self.assertEqual(len(errors), 1)

    def test_effective_registry_rereads_after_edit(self):
        settings = {"abbreviation_source": "document", "abbreviation_defaults": False,
                    "abbreviations": {"ㅁㅍ": {"type": "text", "value": "마포구청"}}}
        registry, errors, source = doc.effective_registry(settings, self.root, BASE)
        self.assertEqual((source, errors), ("document", []))
        self.assertEqual(registry["ㅁㅍ"]["value"], "마포구청")   # 설정 준말이 처음 문서로 옮겨짐
        self.assertTrue(self.path.is_file())
        self.write_lines(["#ㅁㅍ", "마포구청 행정지원과"])
        registry, _, _ = doc.effective_registry(settings, self.root, BASE)
        self.assertEqual(registry["ㅁㅍ"]["value"], "마포구청 행정지원과")
        self.assertIn("ㅁㅍ", settings["abbreviations"])          # 설정 값은 백업으로 남음

    def test_settings_source_keeps_previous_behaviour(self):
        settings = {"abbreviation_source": "settings", "abbreviations": {"요약": {"type": "text", "value": "x"}}}
        registry, errors, source = doc.effective_registry(settings, self.root, BASE)
        self.assertEqual(source, "settings")
        self.assertIn("요약", registry)
        self.assertIn("제목1", registry)
        self.assertFalse(self.path.exists())
        self.assertEqual(doc.source_of({}), "settings")

    def test_defaults_follow_setting(self):
        self.write_lines(["#표", "[서식:표]"])
        registry, _, _ = doc.effective_registry({"abbreviation_source": "document"}, self.root, BASE)
        self.assertIn("제목1", registry)   # 기본 준말 사용
        self.assertEqual(registry["표"]["value"], "table")
        registry, _, _ = doc.effective_registry(
            {"abbreviation_source": "document", "abbreviation_defaults": False}, self.root, BASE)
        self.assertEqual(set(registry), {"표"})

    def test_service_document_commands(self):
        settings_path = self.root / "settings.json"
        settings_path.write_text(json.dumps({"abbreviations": {"ㅇ": {"type": "text", "value": "본말"}}}),
                                 encoding="utf-8")
        opened = []
        service = AbbreviationService(SettingsService(settings_path), self.root, BASE, opened.append)
        snapshot = service.snapshot()
        self.assertEqual(snapshot["source"], "document")
        self.assertFalse(snapshot["document"]["exists"])
        snapshot = service.document_command("open")
        self.assertEqual(opened, [str(self.path)])
        self.assertTrue(snapshot["document"]["exists"])
        self.assertIn("ㅇ", {item["key"] for item in snapshot["entries"] if not item["builtin"]})
        snapshot = service.document_command("use_settings")
        self.assertEqual(snapshot["source"], "settings")
        with self.assertRaises(ServiceError):
            service.document_command("use_document", running=True)
        with self.assertRaises(ServiceError):
            service.document_command("delete")


if __name__ == "__main__":
    unittest.main()
