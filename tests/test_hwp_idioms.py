"""설정의 글자 상용구·본문 상용구 관리(docfit_core.hwp_idioms, docfit_app.idiom_service, 2026-10-15)."""
import shutil
import tempfile
import unittest
from pathlib import Path

from docfit_app.api_contract import ServiceError
from docfit_app.idiom_service import IdiomService
from docfit_core import hwp_idioms

BUNDLED = Path(__file__).resolve().parents[1] / "resources" / "HWP.IDO"


class IdiomFileTest(unittest.TestCase):
    def test_bundled_file_round_trips_byte_for_byte(self):
        data = BUNDLED.read_bytes()
        parsed = hwp_idioms.parse(data)
        self.assertEqual((len(parsed.text), len(parsed.body)), (180, 17))
        self.assertEqual(hwp_idioms.dump(parsed), data)
        self.assertEqual((parsed.text[0].key, parsed.text[0].value), ("➓", "⑩"))
        self.assertEqual(parsed.body[14].key, "표")

    def test_body_document_name_follows_hangul(self):
        # 실측: 한/글 2020은 본문 상용구 '표'를 IDIOM\d45c0000.HWP로 저장한다.
        self.assertEqual(hwp_idioms.body_file_name("표"), "d45c0000.HWP")
        self.assertEqual(hwp_idioms.body_file_name("보고"), "bcf4ace00000.HWP")

    def test_entries_are_validated(self):
        for bad in ([{"key": "", "value": "가"}], [{"key": "가\t", "value": "나"}],
                    [{"key": "가" * 21, "value": "나"}], [{"key": "가", "value": ""}], "목록 아님"):
            with self.assertRaises(hwp_idioms.IdiomError):
                hwp_idioms.validate_entries(bad)
        with self.assertRaises(hwp_idioms.IdiomError):   # 본문 상용구는 준말이 파일 이름이라 겹치면 안 된다
            hwp_idioms.validate_entries([{"key": "가", "title": "나"}, {"key": "가", "title": "다"}], body=True)
        self.assertEqual(len(hwp_idioms.validate_entries([{"key": "*", "value": "※"}, {"key": "*", "value": "＊"}])), 2)
        items = hwp_idioms.validate_entries([{"key": "ㅁ", "value": "□\n여러 줄"}])
        self.assertEqual(items[0].value, "□\n여러 줄")


class IdiomServiceTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.hangul = self.folder / "60"
        self.hangul.mkdir()
        shutil.copyfile(BUNDLED, self.hangul / "HWP.IDO")
        self.service = IdiomService(self.hangul, app_copy=BUNDLED)

    def test_text_idioms_add_edit_delete_with_backup(self):
        entries = self.service.snapshot()["text"]
        entries = [e for e in entries if e["key"] != "화"]                     # 삭제
        entries[0] = {**entries[0], "value": "⑩⑩"}                             # 수정(속성 보존)
        entries.append({"key": "ㅁㅂ", "value": "마포구"})                      # 추가
        result = self.service.command("save_text", {"entries": entries})
        keys = {e["key"]: e for e in result["text"]}
        self.assertNotIn("화", keys)
        self.assertEqual(keys["ㅁㅂ"]["value"], "마포구")
        self.assertEqual(keys["➓"]["value"], "⑩⑩")
        backups = list((self.hangul / "docfit-backup").iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), BUNDLED.read_bytes())       # 이전 파일 그대로 보관
        self.assertEqual(len(hwp_idioms.parse((self.hangul / "HWP.IDO").read_bytes()).body), 17)   # 본문 묶음 유지

    def test_body_idioms_add_rename_delete_move_documents(self):
        source = self.folder / "서식.hwp"
        source.write_bytes(b"HWP Document File")
        result = self.service.command("add_body", {"key": "ㅂㄱ", "title": "보고 서식", "path": str(source)})
        added = next(e for e in result["body"] if e["key"] == "ㅂㄱ")
        self.assertTrue(added["has_file"])
        entries = [{**e, "old_key": e["key"]} for e in result["body"]]
        for e in entries:
            if e["key"] == "ㅂㄱ":
                e.update(key="ㅂㄱㅅ", title="보고서 서식")
        result = self.service.command("save_body", {"entries": entries})
        self.assertTrue((self.hangul / "IDIOM" / hwp_idioms.body_file_name("ㅂㄱㅅ")).is_file())
        self.assertFalse((self.hangul / "IDIOM" / hwp_idioms.body_file_name("ㅂㄱ")).exists())
        entries = [{**e, "old_key": e["key"]} for e in result["body"] if e["key"] != "ㅂㄱㅅ"]
        result = self.service.command("save_body", {"entries": entries})
        self.assertNotIn("ㅂㄱㅅ", {e["key"] for e in result["body"]})
        self.assertFalse((self.hangul / "IDIOM" / hwp_idioms.body_file_name("ㅂㄱㅅ")).exists())
        with self.assertRaises(ServiceError):
            self.service.command("add_body", {"key": "표", "title": "중복", "path": str(source)})

    def test_import_app_idioms_adds_only_missing_keys(self):
        entries = [e for e in self.service.snapshot()["text"] if e["key"] not in ("화", "ㅁ")]
        self.service.command("save_text", {"entries": entries})
        result = self.service.command("import_app", {})
        removed = sum(1 for i in hwp_idioms.parse(BUNDLED.read_bytes()).text if i.key in ("화", "ㅁ"))
        self.assertEqual(result["added"], removed)
        self.assertEqual(len(result["text"]), 180)

    def test_missing_hangul_folder_is_reported(self):
        service = IdiomService(None, app_copy=BUNDLED)
        service.folder = None
        self.assertFalse(service.snapshot()["available"])
        with self.assertRaises(ServiceError):
            service.command("save_text", {"entries": []})


if __name__ == "__main__":
    unittest.main()
