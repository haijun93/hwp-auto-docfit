"""표 칸 줄 간격·자간 하한(TCELL231): 설정값이 엔진 하한으로 쓰이고 본문 한도와 섞이지 않는다."""
from pathlib import Path
import ctypes
import runpy
import sys
import unittest
from unittest.mock import MagicMock, patch

from docfit_core.table_limits import TableLimits, line_floor, spacing_floor

ROOT = Path(__file__).resolve().parents[1]


class TableLimitsTest(unittest.TestCase):
    def test_defaults_when_setting_missing_or_invalid(self):
        for settings in (None, {}, {'table_linespacing_min': '', 'table_spacing_min': 'abc'}):
            limits = TableLimits.from_settings(settings)
            self.assertEqual((limits.line_min, limits.spacing_min), (100, -25))

    def test_user_values_and_clamping(self):
        limits = TableLimits.from_settings({'table_linespacing_min': '120', 'table_spacing_min': '-10'})
        self.assertEqual((limits.line_min, limits.spacing_min), (120, -10))
        limits = TableLimits.from_settings({'table_linespacing_min': '30', 'table_spacing_min': '-90'})
        self.assertEqual((limits.line_min, limits.spacing_min), (100, -50))
        limits = TableLimits.from_settings({'table_spacing_min': '7'})
        self.assertEqual(limits.spacing_min, 0)

    def test_body_settings_do_not_leak(self):
        limits = TableLimits.from_settings({'linespacing_min': '140', 'retry_table': '5'})
        self.assertEqual((limits.line_min, limits.spacing_min), (100, -25))

    def test_floor_depends_on_location(self):
        ns = {'표칸_자간_하한': -10, '표칸_줄간격_하한': 120}
        self.assertEqual(spacing_floor(ns, in_table_cell=True), -10)
        self.assertEqual(spacing_floor(ns, in_table_cell=False), -50)
        self.assertEqual(line_floor(ns, 140, in_table_cell=True), 120)
        self.assertEqual(line_floor(ns, 140, in_table_cell=False), 140)
        self.assertEqual(spacing_floor({}, in_table_cell=True), -25)      # 설정 없음 → 기본값
        self.assertEqual(line_floor({}, 140, in_table_cell=True), 100)

    def test_single_cell_box_keeps_body_floor(self):
        class Doc:
            def GetPos(self):
                return (3, 0, 0)
        ns = {'hwp': Doc(), '한칸표_보호영역': {3}, '현재_표셀인가': lambda: True}
        self.assertEqual(spacing_floor(ns), -50)
        ns['한칸표_보호영역'] = set()
        self.assertEqual(spacing_floor(ns), -25)


class EngineWiringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Windows 전용 모듈이 없는 환경(맥·리눅스)에서도 메인 스크립트가 읽히도록 가짜로 채운다.
        # 이미 진짜 모듈이 있으면(Windows) 건드리지 않는다.
        cls._added = []
        for name in ('winreg', 'pythoncom', 'win32com', 'win32com.client', 'win32gui', 'win32con',
                     'win32api', 'win32process', 'pywintypes', 'win32clipboard'):
            if name not in sys.modules:
                try:
                    __import__(name)
                except ImportError:
                    sys.modules[name] = MagicMock()
                    cls._added.append(name)
        if not hasattr(ctypes, 'windll'):
            ctypes.windll = MagicMock()
            cls._added.append('ctypes.windll')
        cls.ns = runpy.run_path(str(ROOT / 'hwp-auto-docfit.py'))

    @classmethod
    def tearDownClass(cls):
        for name in cls._added:
            if name == 'ctypes.windll':
                del ctypes.windll
            else:
                sys.modules.pop(name, None)

    def test_main_script_defaults_and_crlf(self):
        self.assertEqual((self.ns['표칸_줄간격_하한'], self.ns['표칸_자간_하한']), (100, -25))
        data = (ROOT / 'hwp-auto-docfit.py').read_bytes()
        self.assertEqual(data.count(b'\n'), data.count(b'\r\n'))

    def test_pipeline_reads_settings(self):
        src = (ROOT / 'docfit_engine/pipeline.py').read_text(encoding='utf-8')
        self.assertIn('TableLimits.from_settings(설정_불러오기())', src)
        self.assertIn('globals()["표칸_자간_하한"]', src)
        self.assertIn('globals()["표칸_줄간격_하한"]', src)

    # ---- 줄 간격: 문단_줄간격_적용_현재선택 ----
    def _line_spacing_applied(self, target, *, in_cell, extra=None, drop=()):
        applied = []

        class PSet:
            LineSpacing = 0
            LineSpacingType = 0
            HSet = object()

        class Action:
            def GetDefault(self, *a): pass
            def Execute(self, name, hset): applied.append(PSet.LineSpacing)

        class Doc:
            HAction = Action()
            class HParameterSet:
                HParaShape = PSet
            def LineSpacingMethod(self, name): return 0
            def GetPos(self): return (2, 0, 0) if in_cell else (0, 0, 0)

        fn = self.ns['문단_줄간격_적용_현재선택']
        values = {'hwp': Doc(), '현재_한칸표인가': lambda: False, '현재_표셀인가': lambda: in_cell,
                  '한칸표_보호영역': set(), '세트문장_최소줄간격_퍼센트': 140,
                  '세트문장_최대줄간격_퍼센트': 200, '로그': lambda *_: None}
        values.update(extra or {})
        with patch.dict(fn.__globals__, values):
            for key in drop:
                fn.__globals__.pop(key, None)
            fn(target)
        return applied[-1]

    def test_line_spacing_default_user_and_body(self):
        # 기본값: 표 칸은 100%까지 내려가고, 본문은 140에서 멈춘다.
        self.assertEqual(self._line_spacing_applied(110, in_cell=True, extra={'표칸_줄간격_하한': 100}), 110)
        self.assertEqual(self._line_spacing_applied(110, in_cell=False, extra={'표칸_줄간격_하한': 100}), 140)
        # 사용자 값: 하한을 130으로 올리면 같은 목표도 130에서 멈춘다.
        self.assertEqual(self._line_spacing_applied(110, in_cell=True, extra={'표칸_줄간격_하한': 130}), 130)
        # 본문 한도(140)를 바꿔도 표 칸 결과는 그대로.
        self.assertEqual(self._line_spacing_applied(
            110, in_cell=True, extra={'표칸_줄간격_하한': 100, '세트문장_최소줄간격_퍼센트': 180}), 110)

    def test_line_spacing_without_setting_uses_default_100(self):
        self.assertEqual(self._line_spacing_applied(90, in_cell=True, drop=('표칸_줄간격_하한',)), 100)
        self.assertEqual(self._line_spacing_applied(110, in_cell=True, drop=('표칸_줄간격_하한',)), 110)
        self.assertEqual(self._line_spacing_applied(110, in_cell=False, drop=('표칸_줄간격_하한',)), 140)

    # ---- 자간: 다음단어_당김_시도가 최소_성공단계_탐색에 넘기는 상한 ----
    def _spacing_search_limit(self, *, in_cell, extra=None, drop=(), current_min=0):
        seen = []

        class Doc:
            def GetPos(self): return (2, 0, 0) if in_cell else (0, 0, 0)

        text = {5: 'a', 6: 'b'}

        def one_char(pos):
            ch = text.get(pos[2])
            return None if ch is None else (pos, (pos[0], pos[1], pos[2] + 1), ch)

        def search(최대, 확인, 상한먼저=False, 선형구간=8):
            seen.append(최대)
            return None

        fn = self.ns['다음단어_당김_시도']
        values = {
            'hwp': Doc(), '현재_표셀인가': lambda: in_cell, '한칸표_보호영역': set(),
            '중단_요청됨': lambda: False, '단어모드_줄범위': lambda a: ((0, 0, 0), (0, 0, 5)),
            '단어모드_한글자': one_char, '단어모드_분리정보': lambda a: None,
            '단어모드_서식보관': lambda s, e: ([((0, 0, 0), (0, 0, 5), (current_min,))], []),
            '단어모드_자간적용': lambda runs, v: None, '최소_성공단계_탐색': search,
            '단어_장평_추가축소_시도': lambda *a, **k: False, '진단로그': lambda *_: None,
            '문장부호_2줄_기준글자수': 5, '다음단어_당김_자간_최대_퍼센트': 100,
            '다음단어_통계': {'대상': 0, '적용': 0, '미적용': 0},
        }
        values.update(extra or {})
        with patch.dict(fn.__globals__, values):
            for key in drop:
                fn.__globals__.pop(key, None)
            fn((0, 0, 3), 40)
        return seen[-1]

    def test_spacing_floor_default_user_and_body(self):
        # 이미 -20까지 줄어든 칸: 기본 -25면 5단계 남고, 사용자가 -22로 바꾸면 2단계, 본문은 -50까지 30단계.
        self.assertEqual(self._spacing_search_limit(in_cell=True, current_min=-20, extra={'표칸_자간_하한': -25}), 5)
        self.assertEqual(self._spacing_search_limit(in_cell=True, current_min=-20, extra={'표칸_자간_하한': -22}), 2)
        self.assertEqual(self._spacing_search_limit(in_cell=False, current_min=-20, extra={'표칸_자간_하한': -22}), 30)

    def test_spacing_without_setting_uses_default_minus_25(self):
        self.assertEqual(self._spacing_search_limit(in_cell=True, current_min=-20, drop=('표칸_자간_하한',)), 5)
        self.assertEqual(self._spacing_search_limit(in_cell=False, current_min=-20, drop=('표칸_자간_하한',)), 30)


if __name__ == '__main__':
    unittest.main()
