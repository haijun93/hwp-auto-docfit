"""타임머신 확장자 설정 검증 및 이미지 필터링 단위 시험."""
import tempfile
import unittest
from pathlib import Path

from docfit_app.timemachine_service import TimemachineService
from docfit_core.timemachine import rules
from docfit_core.timemachine.rules import DEFAULT_EXTENSIONS, IMAGE_EXTENSIONS, Rules, SUPPORTED_EXTENSIONS


class FakeAgent:
    def __init__(self):
        self.is_running = False
        self.settings = {"timeline_roots": [], "timeline_mtime_only": False}
        self.calls = []

    def running(self):
        return self.is_running

    def request(self, command, **payload):
        self.calls.append((command, payload))
        if command == "settings_set":
            self.settings = dict(payload.get("settings", {}))
        return {"ok": True, "settings": dict(self.settings)}


class TimemachineExtensionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "문서"
        self.root.mkdir()
        self.settings_dir = Path(self.temp.name) / "설정"
        self.service = TimemachineService(
            self.settings_dir,
            db_path=Path(self.temp.name) / "timeline.db",
            agent=FakeAgent(),
            scanner=lambda *a, **k: type("Stub", (), {"seen": 0, "written": 0, "removed": 0, "errors": []})(),
            thumb_dir=Path(self.temp.name) / "thumbs",
        )

    def tearDown(self):
        self.service.close()
        self.temp.cleanup()

    def test_supported_extensions_constants(self):
        """1. rules.SUPPORTED_EXTENSIONS 상수 검증: 기본 문서 및 이미지 확장자 포함 여부 및 중복 없음 단언."""
        # 중복이 없어야 함
        self.assertEqual(len(SUPPORTED_EXTENSIONS), len(set(SUPPORTED_EXTENSIONS)))
        self.assertEqual(len(IMAGE_EXTENSIONS), len(set(IMAGE_EXTENSIONS)))

        # 기본 문서 확장자와 이미지 확장자가 모두 SUPPORTED_EXTENSIONS에 포함되어야 함
        supported_set = set(SUPPORTED_EXTENSIONS)
        for ext in DEFAULT_EXTENSIONS:
            self.assertIn(ext, supported_set, f"기본 확장자 {ext}가 SUPPORTED_EXTENSIONS에 없음")
        for ext in IMAGE_EXTENSIONS:
            self.assertIn(ext, supported_set, f"이미지 확장자 {ext}가 SUPPORTED_EXTENSIONS에 없음")

        # 모든 확장자는 소문자이고 선행 점(.)이 없어야 함
        for ext in SUPPORTED_EXTENSIONS:
            self.assertFalse(ext.startswith("."), f"확장자에 선행 점이 포함됨: {ext}")
            self.assertEqual(ext, ext.lower(), f"확장자가 소문자가 아님: {ext}")

    def test_validate_extensions_valid_and_image(self):
        """2. _validate_extensions 유효값 검증: 이미지 확장자 포함, 선행 점 제거, 소문자화, 중복 제거 단언."""
        raw_inputs = [".PNG", "hwpx", "BMP", "png", "pdf", ".Jpeg"]
        expected = ["png", "hwpx", "bmp", "pdf", "jpeg"]
        validated = TimemachineService._validate_extensions(raw_inputs)
        self.assertEqual(validated, expected)

    def test_validate_extensions_invalid_or_empty(self):
        """3. _validate_extensions 무효값 검증: 빈 리스트, 비문자열, 미지원 확장자 예외 발생 단언."""
        # 빈 리스트
        with self.assertRaises(ValueError):
            TimemachineService._validate_extensions([])

        # 비문자열 원소
        with self.assertRaises(ValueError):
            TimemachineService._validate_extensions(["png", 123])
        with self.assertRaises(ValueError):
            TimemachineService._validate_extensions(None)

        # 미지원 확장자 (.exe, .sh)
        with self.assertRaises(ValueError):
            TimemachineService._validate_extensions(["exe"])
        with self.assertRaises(ValueError):
            TimemachineService._validate_extensions(["png", "sh"])

    def test_rules_filtering_with_custom_extensions(self):
        """4. Rules 필터링 검증: 지정된 확장자(png, hwp)만 허용되고 제외 확장자(docx)는 skip_file 대상임 단언."""
        custom_rules = Rules(extensions=["png", "hwp"])
        
        # 지정된 확장자는 허용
        self.assertFalse(custom_rules.skip_file("사진.png"))
        self.assertEqual(custom_rules.kind("사진.png"), "image")
        self.assertFalse(custom_rules.skip_file("문서.HWP"))
        self.assertEqual(custom_rules.kind("문서.HWP"), "hwp")

        # 지정되지 않은 확장자는 건너뜀 (skip_file True, kind None)
        self.assertTrue(custom_rules.skip_file("보고서.docx"))
        self.assertIsNone(custom_rules.kind("보고서.docx"))
        self.assertTrue(custom_rules.skip_file("자료.pdf"))
        self.assertIsNone(custom_rules.kind("자료.pdf"))

    def test_service_settings_with_image_extensions(self):
        """5. 서비스 설정 검증: command("settings", ...) 호출로 이미지 확장자가 저장되고 조회됨 단언."""
        payload = {
            "roots": [str(self.root)],
            "time_mode": "max",
            "enabled": True,
            "extensions": ["hwpx", "png", "pdf"],
        }
        # command("settings", ...) 저장 호출
        result = self.service.command("settings", payload)
        self.assertTrue(result.get("ok"), result.get("message"))
        self.assertEqual(result["settings"]["extensions"], ["hwpx", "png", "pdf"])

        # command("settings_get") 조회 호출로 재확인
        get_result = self.service.command("settings_get")
        self.assertTrue(get_result.get("ok"))
        self.assertEqual(get_result["settings"]["extensions"], ["hwpx", "png", "pdf"])

        # command("settings") 인자 없는 조회 호출로도 확인
        query_result = self.service.command("settings")
        self.assertTrue(query_result.get("ok"))
        self.assertEqual(query_result["settings"]["extensions"], ["hwpx", "png", "pdf"])


if __name__ == "__main__":
    unittest.main()
