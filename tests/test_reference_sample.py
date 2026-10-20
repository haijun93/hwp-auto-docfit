"""서식별 활성 예시 파일 경로(활성_서식예시_파일) 및 내어쓰기 기준 복원 단위 시험(카드 R1)."""

from __future__ import annotations

import ast
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch

from tests.test_batch_format import app_functions
from docfit_core.xml_hanging_indent import build_hwpx_from_text_file

ROOT = Path(__file__).resolve().parents[1]


def _app_defaults(ns, names):
    tree = ast.parse((ROOT / "hwp-auto-docfit.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in names for t in node.targets
        ):
            exec(compile(ast.Module(body=[node], type_ignores=[]), "<app defaults>", "exec"), ns)


class ReferenceSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(ROOT / "hwp-auto-docfit.py"))

    def test_default_global_exists_in_entry(self):
        defaults = {}
        _app_defaults(defaults, {"활성_서식예시_파일"})
        self.assertIn("활성_서식예시_파일", defaults)
        self.assertIsNone(defaults["활성_서식예시_파일"])

    def test_pipeline_uses_active_sample_file_when_present(self):
        fn = self.ns["문서_처리"]
        doc = Mock()
        logs = []
        restored_calls = []

        def fake_restore(saved_path, ref_path, out_path):
            restored_calls.append(Path(ref_path))
            return {"checked": 5, "repaired": 0}

        with tempfile.TemporaryDirectory() as folder:
            folder_path = Path(folder)
            source = folder_path / "source.hwpx"
            source.touch()
            custom_sample = folder_path / "내맞춤서식.hwpx"
            custom_sample.write_bytes(b"custom-sample")

            settings = {
                "hwp": doc,
                "작업_모드": "format",
                "표준서식_사용": True,
                "표준서식_내어쓰기_사용": True,
                "알파_일괄서식_가능": lambda: True,
                "활성_서식예시_파일": custom_sample,
                "_사용자서식인가": lambda: True,
                "서식예시_폴더": lambda: folder_path,
                "준말_등록표": {},
                "쪽범위_요청": (2, 2),
                "검수_사용": False,
                "선택_세부작업": {"style_unify": False},
                "작업_반복횟수": 1,
                "중단_요청됨": lambda: False,
                "로그": lambda *a: logs.append(" ".join(str(x) for x in a)),
                "상태": Mock(),
                "단계초기화": Mock(),
                "단계표시": Mock(),
                "validate_hwpx": Mock(return_value={"entry_count": 1, "total_uncompressed_size": 1}),
                "한글_문서_열기": lambda *a: True,
                "원본_뷰어_문서표시": Mock(),
                "비교보기_임베드_재확인": Mock(),
                "쪽범위_계산": lambda *a: True,
                "표준서식_선행_적용": lambda *a: None,
                "제목붙임_선행적용": lambda *a, **kw: True,
                "박스그림_전체_적용": lambda *a, **kw: True,
                "한칸표_영역_목록": lambda: set(),
                "디자인표_영역_목록": lambda: set(),
                "보고서_페이지보호_전체해제": lambda: True,
                "문서_처리_1회": lambda *a: True,
                "처리_쪽수_구하기": lambda: 1,
                "저장결과_규칙검수": lambda *a, **kw: True,
                "최종검수_문서목록": [],
                "검수_문제목록": [],
                "gui_queue": Mock(),
            }
            with patch("docfit_core.xml_hanging_indent.restore_reference_indent_geometry", side_effect=fake_restore):
                with patch.dict(fn.__globals__, settings):
                    self.assertTrue(fn(source, 1, 1))

        self.assertEqual(restored_calls, [custom_sample])

    def test_pipeline_skips_restore_for_user_format_when_sample_missing(self):
        fn = self.ns["문서_처리"]
        doc = Mock()
        logs = []
        restored_calls = []

        def fake_restore(saved_path, ref_path, out_path):
            restored_calls.append(Path(ref_path))
            return {"checked": 5, "repaired": 0}

        with tempfile.TemporaryDirectory() as folder:
            folder_path = Path(folder)
            source = folder_path / "source.hwpx"
            source.touch()
            # 기본 서식.hwpx가 폴더에 있어도 사용자 서식이고 활성 예시가 없으면 건너뛰어야 함
            (folder_path / "기본 서식.hwpx").write_bytes(b"default-sample")
            missing_sample = folder_path / "없는서식.hwpx"

            settings = {
                "hwp": doc,
                "작업_모드": "format",
                "표준서식_사용": True,
                "표준서식_내어쓰기_사용": True,
                "알파_일괄서식_가능": lambda: True,
                "활성_서식예시_파일": missing_sample,
                "_사용자서식인가": lambda: True,
                "서식예시_폴더": lambda: folder_path,
                "준말_등록표": {},
                "쪽범위_요청": (2, 2),
                "검수_사용": False,
                "선택_세부작업": {"style_unify": False},
                "작업_반복횟수": 1,
                "중단_요청됨": lambda: False,
                "로그": lambda *a: logs.append(" ".join(str(x) for x in a)),
                "상태": Mock(),
                "단계초기화": Mock(),
                "단계표시": Mock(),
                "validate_hwpx": Mock(return_value={"entry_count": 1, "total_uncompressed_size": 1}),
                "한글_문서_열기": lambda *a: True,
                "원본_뷰어_문서표시": Mock(),
                "비교보기_임베드_재확인": Mock(),
                "쪽범위_계산": lambda *a: True,
                "표준서식_선행_적용": lambda *a: None,
                "제목붙임_선행적용": lambda *a, **kw: True,
                "박스그림_전체_적용": lambda *a, **kw: True,
                "한칸표_영역_목록": lambda: set(),
                "디자인표_영역_목록": lambda: set(),
                "보고서_페이지보호_전체해제": lambda: True,
                "문서_처리_1회": lambda *a: True,
                "처리_쪽수_구하기": lambda: 1,
                "저장결과_규칙검수": lambda *a, **kw: True,
                "최종검수_문서목록": [],
                "검수_문제목록": [],
                "gui_queue": Mock(),
            }
            with patch("docfit_core.xml_hanging_indent.restore_reference_indent_geometry", side_effect=fake_restore):
                with patch.dict(fn.__globals__, settings):
                    self.assertTrue(fn(source, 1, 1))

        self.assertEqual(restored_calls, [])
        self.assertTrue(any("사용자 서식 예시 파일이 없어 기준 복원을 건너뜁니다" in line for line in logs), logs)

    def test_pipeline_default_format_falls_back_to_default_sample(self):
        fn = self.ns["문서_처리"]
        doc = Mock()
        restored_calls = []

        def fake_restore(saved_path, ref_path, out_path):
            restored_calls.append(Path(ref_path))
            return {"checked": 5, "repaired": 0}

        with tempfile.TemporaryDirectory() as folder:
            folder_path = Path(folder)
            source = folder_path / "source.hwpx"
            source.touch()
            default_sample = folder_path / "기본 서식.hwpx"
            default_sample.write_bytes(b"default-sample")

            settings = {
                "hwp": doc,
                "작업_모드": "format",
                "표준서식_사용": True,
                "표준서식_내어쓰기_사용": True,
                "알파_일괄서식_가능": lambda: True,
                "활성_서식예시_파일": None,
                "_사용자서식인가": lambda: False,
                "서식예시_폴더": lambda: folder_path,
                "준말_등록표": {},
                "쪽범위_요청": (2, 2),
                "검수_사용": False,
                "선택_세부작업": {"style_unify": False},
                "작업_반복횟수": 1,
                "중단_요청됨": lambda: False,
                "로그": Mock(),
                "상태": Mock(),
                "단계초기화": Mock(),
                "단계표시": Mock(),
                "validate_hwpx": Mock(return_value={"entry_count": 1, "total_uncompressed_size": 1}),
                "한글_문서_열기": lambda *a: True,
                "원본_뷰어_문서표시": Mock(),
                "비교보기_임베드_재확인": Mock(),
                "쪽범위_계산": lambda *a: True,
                "표준서식_선행_적용": lambda *a: None,
                "제목붙임_선행적용": lambda *a, **kw: True,
                "박스그림_전체_적용": lambda *a, **kw: True,
                "한칸표_영역_목록": lambda: set(),
                "디자인표_영역_목록": lambda: set(),
                "보고서_페이지보호_전체해제": lambda: True,
                "문서_처리_1회": lambda *a: True,
                "처리_쪽수_구하기": lambda: 1,
                "저장결과_규칙검수": lambda *a, **kw: True,
                "최종검수_문서목록": [],
                "검수_문제목록": [],
                "gui_queue": Mock(),
            }
            with patch("docfit_core.xml_hanging_indent.restore_reference_indent_geometry", side_effect=fake_restore):
                with patch.dict(fn.__globals__, settings):
                    self.assertTrue(fn(source, 1, 1))

        self.assertEqual(restored_calls, [default_sample])

    def test_formatter_uses_active_sample_as_first_candidate(self):
        from docfit_core.batch_format import BatchUnsupported, ParagraphStyle, apply_batch
        from docfit_core.document_rules import ParagraphSpacingTracker
        from docfit_core.fidelity.package import UnsupportedPackage
        from docfit_core.stage_selection import enabled as stage_enabled
        from docfit_core.style_hierarchy import DOT_MARKERS, leading_marker, normalize_leading_dot

        ns = app_functions(
            "알파_일괄서식_가능", "_알파_라벨_굵게범위", "표준서식_hwpx_처리",
            "표준서식_기호규칙_찾기", "문장부호_마커_끝위치",
            "문두_라벨_굵게_제외_문단인가", "괄호_문두_라벨인가", "_문단_본문글", "_알파_글꼴형식",
            "_부모문단_유형", "_부연설명_문단인가", "부연설명_앞빈칸_수", "_사용자서식인가",
        )
        ns["DOT_MARKERS"] = DOT_MARKERS
        _app_defaults(ns, {"표준서식_설정", "표준서식_기호_별칭", "문두라벨_기호설정", "표준서식_기호_굵게",
                           "_제목_기호", "_본문_기호", "_내용_기호", "부연설명_앞빈칸"})
        logs = []
        with tempfile.TemporaryDirectory() as folder:
            folder_path = Path(folder)
            txt = folder_path / "in.txt"
            source = folder_path / "in.hwpx"
            custom_ref = folder_path / "복제서식.hwpx"
            txt.write_text("□ 추진 배경\nㅇ 세부 내용\n", encoding="utf-8")
            build_hwpx_from_text_file(txt, source)
            build_hwpx_from_text_file(txt, custom_ref)

            ns.update(
                apply_batch=apply_batch, ParagraphStyle=ParagraphStyle, BatchUnsupported=BatchUnsupported,
                UnsupportedPackage=UnsupportedPackage, ParagraphSpacingTracker=ParagraphSpacingTracker,
                stage_enabled=stage_enabled, normalize_leading_dot=normalize_leading_dot,
                leading_marker=leading_marker, DOT_MARKERS=DOT_MARKERS, 부연설명_들여쓰기_사용=True,
                알파_HWPX_일괄서식_사용=True, 작업_모드="all", 표준서식_선행_사용=True,
                표준서식_내어쓰기_사용=True, 쪽범위_요청=None, 선택_세부작업={}, 괄호_라벨_볼드_사용=True,
                표준서식_기호_사용=True, 표준서식_문단위간격_사용=False,
                표준서식_장평_사용=True, 표준서식_줄간격_사용=True,
                표준서식_문단위간격_복귀배율=150, _글꼴형식={}, 항목_패턴=[], 공문서_기호={"□", "ㅇ", "-", "*", "※"},
                _문두_무시문자_정규식=re.compile(r"[\s​⁠﻿]+"),
                괄호_정규식=re.compile(r"\(([^()]+)\)|\[([^\[\]]+)\]"),
                제목_xml이름=lambda e: e.tag.rsplit("}", 1)[-1],
                _표준서식_문단위간격_표=lambda: {}, _GDI_글꼴인가=lambda name: True,
                로그=lambda *a: logs.append(" ".join(str(x) for x in a)),
                서식예시_폴더=lambda: ROOT / "resources" / "서식예시",
                활성_서식예시_파일=custom_ref,
            )
            with patch("docfit_core.xml_hanging_indent.reference_marker_indent_pairs", return_value={}) as mock_pairs:
                ns["표준서식_hwpx_처리"](source)
                mock_pairs.assert_called_once_with(custom_ref)


if __name__ == "__main__":
    unittest.main()
