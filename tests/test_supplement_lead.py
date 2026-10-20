"""부연설명(*, **, ※) 앞 빈칸: 위 문단 유형별 규칙과 서식 복사 프로필의 학습값(2026-10-20).

회귀 배경: XML 일괄 서식이 부연설명에 기호 규칙 고정값(* 3, ** 2)을 넣고 뒤 단계가 XML 처리 문단을 건너뛰어
'-' 아래 * 6·** 5가 3·2로 남았다. 서식 복사(복제) 프로필은 앞 빈칸 맞춤을 아예 건너뛰어 txt 입력의 ㅇ·-가 0칸이었다.
"""
import ast
import re
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZIP_DEFLATED, ZipFile

from tests.test_batch_format import app_functions
from tests.test_style_profile import HEADER

ROOT = Path(__file__).resolve().parents[1]


def _section(lines):
    paras = "".join(f'<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>{line}</hp:t></hp:run></hp:p>'
                    for line in lines)
    return ('<?xml version="1.0" encoding="UTF-8"?><hs:sec xmlns:hs="urn:section" xmlns:hp="urn:para">'
            '<hp:secPr><hp:pagePr><hp:margin left="5102" right="5102" top="3600" bottom="3600"/></hp:pagePr></hp:secPr>'
            f'{paras}</hs:sec>').encode("utf-8")


def _app_defaults(ns, names):
    tree = ast.parse((ROOT / "hwp-auto-docfit.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
            exec(compile(ast.Module(body=[node], type_ignores=[]), "<app defaults>", "exec"), ns)


class SupplementLeadLookupTests(unittest.TestCase):
    def setUp(self):
        self.ns = app_functions("부연설명_앞빈칸_수")
        _app_defaults(self.ns, {"부연설명_앞빈칸"})

    def test_default_table_by_parent(self):
        self.ns["표준서식_설정"] = {}
        lookup = self.ns["부연설명_앞빈칸_수"]
        self.assertEqual((lookup("내용", "*"), lookup("내용", "**")), (6, 5))
        self.assertEqual(lookup("본문", "※"), 5)
        self.assertEqual((lookup("제목", "*"), lookup("제목", "**")), (5, 4))
        self.assertEqual((lookup(None, "*"), lookup(None, "**")), (4, 3))

    def test_learned_table_wins_and_missing_pairs_fall_back(self):
        self.ns["표준서식_설정"] = {"부연설명_앞빈칸": {"본문": {"※": 3}, "": {"*": 2}}}
        lookup = self.ns["부연설명_앞빈칸_수"]
        self.assertEqual(lookup("본문", "※"), 3)        # 예시에서 배운 값
        self.assertEqual(lookup(None, "*"), 2)          # 위 문단 없음은 "" 키
        self.assertEqual(lookup("내용", "*"), 6)        # 예시에 없는 조합은 기본표


class SupplementLeadLearningTests(unittest.TestCase):
    def test_analysis_learns_supplement_leads_per_parent(self):
        ns = runpy.run_path(str(ROOT / "hwp-auto-docfit.py"), run_name="supplement_learn_test")
        lines = ["□ 추진 배경", " ㅇ (현황) 문장", "   - 내용 문장", "      * 항세기: 설명",
                 "     ** 난세기: 설명", " ㅇ (위험) 문장", "   ※ 참고 설명"]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sample.hwpx"
            with ZipFile(source, "w", ZIP_DEFLATED) as archive:
                archive.writestr("Contents/header.xml", HEADER)
                archive.writestr("Contents/section0.xml", _section(lines))
            profile = ns["hwpx_서식_분석"](source)
        self.assertEqual(profile["format"]["부연설명_앞빈칸"], {"내용": {"*": 6, "**": 5}, "본문": {"※": 3}})


class XmlPlanSupplementLeadTests(unittest.TestCase):
    """표준서식_hwpx_처리의 XML 계획이 위 문단별 칸 수를 내어쓰기 계산 전에 확정하는지 본다."""

    def _run(self, text, settings_extra=None, supplement_on=True):
        from docfit_core.batch_format import BatchUnsupported, ParagraphStyle, apply_batch
        from docfit_core.document_rules import ParagraphSpacingTracker
        from docfit_core.fidelity.package import UnsupportedPackage
        from docfit_core.stage_selection import enabled as stage_enabled
        from docfit_core.style_hierarchy import DOT_MARKERS, leading_marker, normalize_leading_dot
        from docfit_core.xml_hanging_indent import build_hwpx_from_text_file

        ns = app_functions(
            "알파_일괄서식_가능", "_알파_라벨_굵게범위", "표준서식_hwpx_처리",
            "표준서식_기호규칙_찾기", "문장부호_마커_끝위치",
            "문두_라벨_굵게_제외_문단인가", "괄호_문두_라벨인가", "_문단_본문글", "_알파_글꼴형식",
            "_부모문단_유형", "_부연설명_문단인가", "부연설명_앞빈칸_수",
        )
        ns["DOT_MARKERS"] = DOT_MARKERS
        _app_defaults(ns, {"표준서식_설정", "표준서식_기호_별칭", "문두라벨_기호설정", "표준서식_기호_굵게",
                           "_제목_기호", "_본문_기호", "_내용_기호", "부연설명_앞빈칸"})
        ns["표준서식_설정"].update(settings_extra or {})
        tag = lambda e: e.tag.rsplit("}", 1)[-1]
        ns.update(
            apply_batch=apply_batch, ParagraphStyle=ParagraphStyle, BatchUnsupported=BatchUnsupported,
            UnsupportedPackage=UnsupportedPackage, ParagraphSpacingTracker=ParagraphSpacingTracker,
            stage_enabled=stage_enabled, normalize_leading_dot=normalize_leading_dot,
            leading_marker=leading_marker, DOT_MARKERS=DOT_MARKERS, 부연설명_들여쓰기_사용=supplement_on,
            알파_HWPX_일괄서식_사용=True, 작업_모드="all", 표준서식_선행_사용=True,
            표준서식_내어쓰기_사용=False, 쪽범위_요청=None, 선택_세부작업={}, 괄호_라벨_볼드_사용=True,
            표준서식_기호_사용=True, 표준서식_문단위간격_사용=False,
            표준서식_장평_사용=True, 표준서식_줄간격_사용=True,
            표준서식_문단위간격_복귀배율=150, _글꼴형식={}, 항목_패턴=[], 공문서_기호={"□", "ㅇ", "-", "*", "※"},
            _문두_무시문자_정규식=re.compile(r"[\s​⁠﻿]+"),
            괄호_정규식=re.compile(r"\(([^()]+)\)|\[([^\[\]]+)\]"), 제목_xml이름=tag,
            _표준서식_문단위간격_표=lambda: {}, _GDI_글꼴인가=lambda name: True, 로그=Mock(),
            shutil=__import__("shutil"), 서식예시_폴더=lambda: ROOT / "resources" / "서식예시",
        )
        with tempfile.TemporaryDirectory() as folder:
            txt, source, target = (Path(folder) / n for n in ("in.txt", "in.hwpx", "out.hwpx"))
            txt.write_text(text, encoding="utf-8")
            build_hwpx_from_text_file(txt, source)
            ns["표준서식_hwpx_처리"](source, target, ns["표준서식_hwpx_처리"](source))
            with ZipFile(target) as z:
                xml = z.read("Contents/section0.xml").decode("utf-8")
        return re.findall(r"<hp:t>([^<]*)</hp:t>", xml)

    def test_default_profile_parent_specific_leads(self):
        texts = self._run("□ 배경\nㅇ 상황 설명 문장\n- 내용 문장\n* 항세기: 설명\n** 난세기: 설명\n"
                          "ㅇ 다른 문장\n※ 참고 설명\n□ 둘째\n* 제목 아래 설명\n** 제목 아래 둘째")
        joined = "\n".join(texts)
        for expected in (" ㅇ 상황 설명 문장", "   - 내용 문장", "      * 항세기: 설명", "     ** 난세기: 설명",
                         "     ※ 참고 설명", "     * 제목 아래 설명", "    ** 제목 아래 둘째"):
            self.assertIn(expected, texts, joined)

    def test_copied_profile_uses_learned_leads_even_when_keeping_indent(self):
        texts = self._run("□ 배경\nㅇ 상황 설명 문장\n- 내용 문장\n* 항세기: 설명\n** 난세기: 설명\nㅇ 다른 문장\n※ 참고 설명",
                          settings_extra={"복제_들여쓰기_유지": True,
                                          "부연설명_앞빈칸": {"내용": {"*": 6, "**": 5}, "본문": {"※": 3}}},
                          supplement_on=False)
        for expected in (" ㅇ 상황 설명 문장", "   - 내용 문장", "      * 항세기: 설명", "     ** 난세기: 설명",
                         "   ※ 참고 설명"):
            self.assertIn(expected, texts, "\n".join(texts))


if __name__ == "__main__":
    unittest.main()
