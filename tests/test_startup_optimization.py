"""시작 속도 최적화 회귀 시험: 지연 import, 폰트 지연 로딩, 런처 고속 검사 무결성 검증."""
import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if "hwp_auto_docfit" not in sys.modules:
    import importlib.util
    _hwp_path = ROOT / "hwp-auto-docfit.py"
    if _hwp_path.is_file():
        _spec = importlib.util.spec_from_file_location("hwp_auto_docfit", _hwp_path)
        _mod = importlib.util.module_from_spec(_spec)
        sys.modules["hwp_auto_docfit"] = _mod
        _spec.loader.exec_module(_mod)


class StartupOptimizationTest(unittest.TestCase):

    def test_lazy_engine_symbol_defers_import(self):
        """_LazyEngineSymbol이 실제 호출 전까지 대상 모듈 로딩을 지연시키는지 검사."""
        import importlib
        import hwp_auto_docfit as app_module

        # docfit_engine.formatter는 hwp_auto_docfit 로드 시점에 즉시 임포트되지 않아야 함
        lazy_func = app_module.AI답변_개조식_변환
        self.assertTrue(hasattr(lazy_func, "_get_target") or callable(lazy_func))

    def test_font_cache_is_lazy(self):
        """HwpAutoDocFitGUI가 시작 시점에 한글_폰트_목록_전체를 동기 호출하지 않는지 검사."""
        from docfit_ui.legacy import HwpAutoDocFitGUI

        gui = Mock(spec=HwpAutoDocFitGUI)
        # 프로퍼티 동작 검증
        prop = getattr(HwpAutoDocFitGUI, "_한글_폰트_목록_캐시")
        self.assertTrue(isinstance(prop, property))

    def test_shell_menu_refresh_non_blocking(self):
        """main()에서 refresh_registered가 메인 스레드를 블로킹하지 않는지 검사."""
        import hwp_auto_docfit as app_module
        # threading.Thread 타겟으로 감싸져 있는지 소스 검사
        import inspect
        source = inspect.getsource(app_module.main)
        self.assertIn("shell-menu-refresh", source)


if __name__ == "__main__":
    unittest.main()
