"""순수 XML 내어쓰기(docfit_core.xml_hanging_indent) 단위 및 통합 테스트."""

from pathlib import Path
import tempfile
import unittest

from defusedxml import ElementTree as ET

from docfit_core.batch_format import plain_text, tag
from docfit_core.release_format_audit import inspect_hanging_indent
from docfit_core.xml_hanging_indent import (
    apply_xml_hanging_indent,
    attachment_numbered_pair,
    build_hwpx_from_text_file,
    char_width_factor,
    hanging_indent_offset,
    hanging_indent_pair,
    prefix_width_hwpunit,
    reference_hanging_indent_pair,
    reference_marker_indent_pairs,
    restore_reference_indent_geometry,
    safe_reference_hanging_indent_pair,
)
from tests.test_batch_format import app_functions, fixture, paragraph, roots, shapes


SAMPLE_LINES = [
    "제목 : 삼체 문명 존속을 위한, 지구 이주·점령 계획(안) 보고",
    "",
    "개요 : 삼체 행성의 항성계 불안정성 심화에 따른 문명 파괴 위기를 극복하고자, 신규 거점(지구) 확보를 위한 「선(先) 기초과학 봉쇄 - 후(後) 함대 일괄 점령」 3단계 침공·이주 전략을 수립하여 보고드림.",
    "",
    "ㅁ 추진 배경",
    "  ㅇ (삼체 행성 상황) 3개 항성의 불규칙 운동으로 혹독한 환경 반복",
    "    - 항세기*와 난세기**가 예측 불가능하게 교차, 문명 파괴 주기적 발생",
    "    * 항세기: 기후가 안정된 시기, ",
    "   ** 난세기: 극단적 기후가 발생하는 시기",
    "    - 탈수(脫水)* 대응에도 불구하고 문명 재건 비용 누적",
    "    * 탈수: 난세기 생존을 위해 몸의 수분을 빼 휴면 상태로 전환하는 방식",
    "  ㅇ (지구 확인 경과) 인류가 발신한 전파 수신으로 존재 확인",
    "    - 항성계 안정, 액체 상태 물 존재, 문명 발달 수준 파악",
    "  ㅇ (판단) 삼체 세계 존속의 유일한 대안으로 지구 이주 필요",
    "",
    "붙임 : 1. 지구 침공 세부 시행계획 1부.",
    "   2. 스케줄표 1부.  끝.",
]


class XmlHangingIndentUnitTests(unittest.TestCase):
    def test_wrapped_reference_markers_get_compensating_continuation_margin(self):
        reference = Path(__file__).resolve().parents[1] / "resources" / "서식예시" / "기본 서식.hwpx"
        pairs = reference_marker_indent_pairs(reference)
        cases = {
            "□ 총 소요: 미네랄 52만 단위, 베스핀 가스 18만 단위(’26~’30년)": None,
            " ㅇ 난세기 예보 시 전 주민을 탈수하여 건조 보관고에 보관하고, 항세기가 오면 일괄 침수 복원": None,
        }
        cases = {
            text: (-reference_hanging_indent_pair(text, pairs)[1], reference_hanging_indent_pair(text, pairs)[1])
            for text in cases
        }
        for text, expected in cases.items():
            self.assertEqual(safe_reference_hanging_indent_pair(text, pairs), expected)

        with tempfile.TemporaryDirectory() as folder:
            restored = Path(folder) / "restored.hwpx"
            result = restore_reference_indent_geometry(reference, reference, restored)
            self.assertGreater(result["repaired"], 0)
            audit = inspect_hanging_indent(restored, reference)
            findings = {item["text"]: item for item in audit["findings"]}
            header, section = roots(restored)
            para_map = shapes(header, "paraPr")
            for text, expected in cases.items():
                self.assertEqual((findings[text]["left"], findings[text]["indent"]), expected)
                self.assertEqual(findings[text]["status"], "pass")
                paragraph = next(p for p in section.iter() if tag(p) == "p" and plain_text(p) == text)
                self.assertFalse(any(tag(child) == "linesegarray" for child in paragraph))
                self.assertIn(paragraph.get("paraPrIDRef"), para_map)

    def test_final_guard_aligns_trailing_attachment_numbers(self):
        from docfit_core.batch_format import ParagraphStyle, StylePool, _serialize
        from docfit_core.fidelity.package import PackageSnapshot, build_package

        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source_text = folder / "attachments.txt"
            source = folder / "source.hwpx"
            damaged = folder / "damaged.hwpx"
            restored = folder / "restored.hwpx"
            source_text.write_text(
                "붙임 : 1. 계획서 1부.\n   2. 일정표 1부. 끝.\n", encoding="utf-8")
            build_hwpx_from_text_file(source_text, source)
            apply_xml_hanging_indent(source, damaged)
            snapshot = PackageSnapshot.load(damaged)
            header = ET.fromstring(snapshot.read("Contents/header.xml"))
            section = ET.fromstring(snapshot.read("Contents/section0.xml"))
            pool = StylePool(header)
            from docfit_core.xml_hanging_indent import _paragraph_visible_text
            for item in section.iter():
                if tag(item) == "p" and _paragraph_visible_text(item).startswith("붙임"):
                    item.set("paraPrIDRef", pool.para(item.get("paraPrIDRef"), ParagraphStyle(
                        text=_paragraph_visible_text(item), para_extra=(("left", 7500), ("intent", -4300)))))
                if tag(item) == "p" and (plain_text(item) or "").lstrip().startswith("2."):
                    item.set("paraPrIDRef", pool.para(item.get("paraPrIDRef"), ParagraphStyle(
                        text=plain_text(item), para_extra=(("left", 7500), ("intent", -4300)))))
            damaged.write_bytes(build_package(snapshot, {
                "Contents/header.xml": _serialize(header, snapshot.read("Contents/header.xml")),
                "Contents/section0.xml": _serialize(section, snapshot.read("Contents/section0.xml")),
            }))
            before = inspect_hanging_indent(damaged)
            self.assertTrue(any("attachment numbers" in item["reason"] for item in before["findings"]))
            self.assertTrue(any("must start with 붙임" in item["reason"] for item in before["findings"]), before["findings"])
            from docfit_core.attachment_block import find_trailing_numbered_blocks
            from docfit_core.xml_hanging_indent import _paragraph_visible_text
            section = ET.fromstring(PackageSnapshot.load(damaged).read("Contents/section0.xml"))
            texts = [_paragraph_visible_text(item) for item in section.iter() if tag(item) == "p"]
            self.assertTrue(find_trailing_numbered_blocks(texts), texts)
            result = restore_reference_indent_geometry(damaged, damaged, restored)
            self.assertGreater(result["repaired"], 0)
            after = inspect_hanging_indent(restored)
            self.assertEqual(after["failed_count"], 0)
            from docfit_core.xml_hanging_indent import _char_size_pt, _paragraph_left_intent
            saved_header, saved_section = roots(restored)
            saved_shapes = shapes(saved_header, "paraPr")
            numbered = []
            for para in saved_section.iter():
                if tag(para) != "p":
                    continue
                value = _paragraph_visible_text(para)
                if value.startswith("붙임") or value.lstrip().startswith("2."):
                    left, indent = _paragraph_left_intent(saved_shapes[para.get("paraPrIDRef")])
                    numbered.append({"text": value, "left": left, "indent": indent,
                                     "size": _char_size_pt(saved_header, para)})
            self.assertEqual(len(numbered), 2)
            self.assertTrue(numbered[0]["text"].startswith("붙임"))
            self.assertEqual(numbered[0]["left"] + numbered[0]["indent"], 0)
            for item in numbered:
                self.assertGreater(item["left"], 0)
                self.assertLess(item["indent"], 0)
                self.assertGreaterEqual(item["left"] + item["indent"], 0)
            from docfit_core.attachment_block import numbered_item_offset
            self.assertEqual(
                numbered[0]["left"] + numbered[0]["indent"]
                + prefix_width_hwpunit(numbered[0]["text"], numbered_item_offset(numbered[0]["text"]), size_pt=numbered[0]["size"]),
                numbered[1]["left"] + numbered[1]["indent"]
                + prefix_width_hwpunit(numbered[1]["text"], numbered_item_offset(numbered[1]["text"]), size_pt=numbered[1]["size"]),
            )

    def test_reference_restore_keeps_explicit_exception_for_same_marker(self):
        from docfit_core.batch_format import ParagraphStyle, StylePool, _serialize
        from docfit_core.fidelity.package import PackageSnapshot, build_package

        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source_text = folder / "sample.txt"
            reference = folder / "reference.hwpx"
            damaged = folder / "damaged.hwpx"
            restored = folder / "restored.hwpx"
            source_text.write_text("ㅇ default\nㅇ another\nㅇ exceptional\n", encoding="utf-8")
            build_hwpx_from_text_file(source_text, reference)
            snapshot = PackageSnapshot.load(reference)
            header = ET.fromstring(snapshot.read("Contents/header.xml"))
            section = ET.fromstring(snapshot.read("Contents/section0.xml"))
            pool = StylePool(header)
            for item in section.iter():
                if tag(item) != "p" or not (plain_text(item) or "").startswith("ㅇ"):
                    continue
                pair = (0, -3240) if plain_text(item) == "ㅇ exceptional" else (0, -2996)
                item.set("paraPrIDRef", pool.para(item.get("paraPrIDRef"), ParagraphStyle(
                    text=plain_text(item), para_extra=(("left", pair[0]), ("intent", pair[1])))))
            replacements = {
                "Contents/header.xml": _serialize(header, snapshot.read("Contents/header.xml")),
                "Contents/section0.xml": _serialize(section, snapshot.read("Contents/section0.xml")),
            }
            reference.write_bytes(build_package(snapshot, replacements))
            pairs = reference_marker_indent_pairs(reference)
            self.assertEqual(reference_hanging_indent_pair("ㅇ exceptional", pairs), (0, -3240))
            self.assertEqual(reference_hanging_indent_pair("ㅇ new text", pairs), (0, -2996))

            # Simulate a later pass flattening the exceptional paragraph to the mode.
            snapshot = PackageSnapshot.load(reference)
            header = ET.fromstring(snapshot.read("Contents/header.xml"))
            section = ET.fromstring(snapshot.read("Contents/section0.xml"))
            pool = StylePool(header)
            for item in section.iter():
                if tag(item) == "p" and plain_text(item) == "ㅇ exceptional":
                    item.set("paraPrIDRef", pool.para(item.get("paraPrIDRef"), ParagraphStyle(
                        text=plain_text(item), para_extra=(("left", 0), ("intent", -2996)))))
            damaged.write_bytes(build_package(snapshot, {
                "Contents/header.xml": _serialize(header, snapshot.read("Contents/header.xml")),
                "Contents/section0.xml": _serialize(section, snapshot.read("Contents/section0.xml")),
            }))
            result = restore_reference_indent_geometry(damaged, reference, restored)
            self.assertGreaterEqual(result["repaired"], 1)
            self.assertEqual(inspect_hanging_indent(restored, reference)["failed_count"], 0)

    def test_reference_document_pairs_are_preserved_per_marker_and_label(self):
        reference = Path(__file__).resolve().parents[1] / "resources" / "서식예시" / "기본 서식.hwpx"
        pairs = reference_marker_indent_pairs(reference)
        self.assertEqual(pairs["-"], (0, -2800))
        self.assertEqual(pairs["□"], (0, -2548))
        self.assertEqual(pairs["ㅇ"], (0, -2996))
        self.assertEqual(reference_hanging_indent_pair("ㅁ heading", pairs), (0, -2548))
        self.assertEqual(reference_hanging_indent_pair("○ heading", pairs), (0, -2996))
        self.assertEqual(pairs["*:label"], (0, -8336))
        self.assertEqual(pairs["**:label"], (0, -9092))
        self.assertEqual(reference_hanging_indent_pair("   * 항목: 본문", pairs), (0, -8336))
        self.assertEqual(reference_hanging_indent_pair("   ** 주석: 본문", pairs), (0, -9092))

    def test_saved_artifact_geometry_guard_restores_only_reference_pair(self):
        reference = Path(__file__).resolve().parents[1] / "resources" / "서식예시" / "기본 서식.hwpx"
        with tempfile.TemporaryDirectory() as folder:
            txt_path = Path(folder) / "sample.txt"
            raw_hwpx = Path(folder) / "raw.hwpx"
            formatted = Path(folder) / "formatted.hwpx"
            restored = Path(folder) / "restored.hwpx"
            txt_path.write_text("□ 추진 배경\nㅇ (현황) 내용", encoding="utf-8")
            build_hwpx_from_text_file(txt_path, raw_hwpx)
            apply_xml_hanging_indent(raw_hwpx, formatted)

            # Simulate a later COM/page-fit pass overwriting the chapter marker geometry.
            from docfit_core.batch_format import ParagraphStyle, StylePool, _serialize
            from docfit_core.fidelity.package import PackageSnapshot, build_package
            from defusedxml import ElementTree as SafeET
            snapshot = PackageSnapshot.load(formatted)
            header = SafeET.fromstring(snapshot.read("Contents/header.xml"))
            section_name = "Contents/section0.xml"
            section = SafeET.fromstring(snapshot.read(section_name))
            pool = StylePool(header)
            for paragraph in section.iter():
                if tag(paragraph) == "p" and plain_text(paragraph).lstrip().startswith("□"):
                    para_id = pool.para(paragraph.get("paraPrIDRef"), ParagraphStyle(
                        text=plain_text(paragraph), para_extra=(("left", 0), ("intent", 0))))
                    paragraph.set("paraPrIDRef", para_id)
            payload = build_package(snapshot, {
                "Contents/header.xml": _serialize(header, snapshot.read("Contents/header.xml")),
                section_name: _serialize(section, snapshot.read(section_name)),
            })
            formatted.write_bytes(payload)

            result = restore_reference_indent_geometry(formatted, reference, restored)
            self.assertEqual(result["checked"], 2)
            self.assertEqual(result["repaired"], 2)
            audit = inspect_hanging_indent(restored, reference)
            self.assertEqual(audit["status"], "pass")
            self.assertEqual(audit["failed_count"], 0)

    def test_char_width_factor_and_prefix_width(self):
        self.assertEqual(char_width_factor("가"), 1.0)
        self.assertEqual(char_width_factor("ㅇ"), 1.0)
        self.assertEqual(char_width_factor(" "), 0.5)
        self.assertEqual(char_width_factor("-"), 0.5)
        self.assertEqual(char_width_factor("("), 0.42)
        self.assertEqual(prefix_width_hwpunit(" ㅇ 본문", 3, size_pt=15.0), 3000)
        self.assertEqual(prefix_width_hwpunit("   - 본문", 5, size_pt=14.0), 3500)
        self.assertEqual(prefix_width_hwpunit("   * 항세기: 기후", 10, size_pt=13.0), 8450)
        self.assertEqual(prefix_width_hwpunit("  ** 난세기: 극단", 10, size_pt=13.0), 8450)
        self.assertEqual(prefix_width_hwpunit("   * 탈수: 난세기", 9, size_pt=13.0), 7150)

    def test_hanging_indent_offset_and_pair_rules(self):
        self.assertEqual(hanging_indent_offset("ㅁ 추진 배경"), 0)
        self.assertEqual(hanging_indent_pair("ㅁ 추진 배경", size_pt=17.0), (0, 0))
        self.assertEqual(hanging_indent_offset(" ㅇ (삼체 행성 상황) 3개 항성"), 3)
        self.assertEqual(hanging_indent_pair(" ㅇ (삼체 행성 상황) 3개 항성", size_pt=15.0), (3000, -3000))
        self.assertEqual(hanging_indent_offset("   * 항세기: 기후가 안정된 시기"), 10)
        self.assertEqual(hanging_indent_pair("   * 항세기: 기후가 안정된 시기", size_pt=13.0), (8450, -8450))
        self.assertEqual(hanging_indent_offset(" ㅇ 「선(先) 기초과학」"), 4)
        self.assertIsNone(hanging_indent_offset("일반 문단입니다."))

    def test_attachment_numbered_pair_aligns_numbers_and_body(self):
        first = "붙임 : 1. 지구 침공 세부 시행계획 1부."
        second = "   2. 스케줄표 1부.  끝."
        anchor = prefix_width_hwpunit(first, 5, size_pt=15.0)
        self.assertEqual(anchor, 5250)
        self.assertEqual(attachment_numbered_pair(first, anchor, size_pt=15.0), (7500, -7500))
        self.assertEqual(attachment_numbered_pair(second, anchor, size_pt=15.0), (7500, -4500))

    def test_end_to_end_sample_text_passes_release_format_audit(self):
        with tempfile.TemporaryDirectory() as folder:
            txt_path = Path(folder) / "sample.txt"
            raw_hwpx = Path(folder) / "raw.hwpx"
            out_hwpx = Path(folder) / "out.hwpx"
            txt_path.write_text("\n".join(SAMPLE_LINES), encoding="utf-8")

            build_hwpx_from_text_file(txt_path, raw_hwpx)
            res = apply_xml_hanging_indent(raw_hwpx, out_hwpx)
            self.assertEqual(res.applied, 12)

            audit = inspect_hanging_indent(out_hwpx)
            self.assertEqual(audit["status"], "pass")
            self.assertEqual(audit["failed_count"], 0)
            self.assertEqual(audit["checked_count"], 11)

            header, section = roots(out_hwpx)
            para_map = shapes(header, "paraPr")
            for p in section:
                if tag(p) != "p":
                    continue
                self.assertFalse(any(tag(c) == "linesegarray" for c in p))
                shape = para_map[p.get("paraPrIDRef")]
                case_node = next(x for x in shape.iter() if tag(x) == "case")
                def_node = next(x for x in shape.iter() if tag(x) == "default")
                c_left = int(next(x for x in case_node.iter() if tag(x) == "left").get("value"))
                c_intent = int(next(x for x in case_node.iter() if tag(x) == "intent").get("value"))
                d_left = int(next(x for x in def_node.iter() if tag(x) == "left").get("value"))
                d_intent = int(next(x for x in def_node.iter() if tag(x) == "intent").get("value"))
                self.assertEqual(d_left, c_left * 2)
                self.assertEqual(d_intent, c_intent * 2)

    def test_formatter_hwpx_batch_integrates_xml_hanging_indent_when_enabled(self):
        from docfit_core.batch_format import BatchUnsupported, ParagraphStyle, apply_batch
        from docfit_core.document_rules import ParagraphSpacingTracker
        from docfit_core.fidelity.package import UnsupportedPackage
        from docfit_core.stage_selection import enabled as stage_enabled
        from docfit_core.style_hierarchy import DOT_MARKERS, leading_marker, normalize_leading_dot
        import ast
        import re
        from unittest.mock import Mock

        ns = app_functions(
            "알파_일괄서식_가능", "_알파_라벨_굵게범위", "표준서식_hwpx_처리",
            "표준서식_기호규칙_찾기", "문장부호_마커_끝위치",
            "문두_라벨_굵게_제외_문단인가", "괄호_문두_라벨인가", "_문단_본문글", "_알파_글꼴형식",
        )
        ns["DOT_MARKERS"] = DOT_MARKERS
        tree = ast.parse((Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py").read_text(encoding="utf-8"))
        wanted = {"표준서식_설정", "표준서식_기호_별칭", "문두라벨_기호설정", "표준서식_기호_굵게"}
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in wanted for t in node.targets):
                exec(compile(ast.Module(body=[node], type_ignores=[]), "<app defaults>", "exec"), ns)
        ns.update(
            apply_batch=apply_batch, ParagraphStyle=ParagraphStyle, BatchUnsupported=BatchUnsupported,
            UnsupportedPackage=UnsupportedPackage, ParagraphSpacingTracker=ParagraphSpacingTracker,
            stage_enabled=stage_enabled, normalize_leading_dot=normalize_leading_dot,
            leading_marker=leading_marker, DOT_MARKERS=DOT_MARKERS,
            알파_HWPX_일괄서식_사용=True, 작업_모드="all", 표준서식_선행_사용=True,
            표준서식_내어쓰기_사용=True, 쪽범위_요청=None, 선택_세부작업={}, 괄호_라벨_볼드_사용=True,
            표준서식_기호_사용=True, 표준서식_문단위간격_사용=True,
            표준서식_장평_사용=True, 표준서식_줄간격_사용=True,
            표준서식_문단위간격_복귀배율=150, _글꼴형식={}, 항목_패턴=[], 공문서_기호={"□", "ㅇ", "-", "*", "※"},
            _문두_무시문자_정규식=re.compile(r"[\s\u200b\u2060\ufeff]+"),
            괄호_정규식=re.compile(r"\(([^()]+)\)|\[([^\[\]]+)\]"), 제목_xml이름=tag,
            _표준서식_문단위간격_표=lambda: dict(chapter=15, midtitle=15, box=15, circle=8, dash=4, note=0),
            _GDI_글꼴인가=lambda name: True, 로그=Mock(),
        )
        reference = Path(__file__).resolve().parents[1] / "resources" / "서식예시"
        ns["서식예시_폴더"] = lambda: reference
        with tempfile.TemporaryDirectory() as folder:
            txt_file = Path(folder) / "in.txt"
            source, target = Path(folder) / "in.hwpx", Path(folder) / "out.hwpx"
            txt_file.write_text(
                "ㅁ 추진 배경\n"
                "  ㅇ (삼체 행성 상황) 3개 항성의 불규칙 운동\n"
                "    * 항세기: 기후가 안정된 시기",
                encoding="utf-8",
            )
            build_hwpx_from_text_file(txt_file, source)
            selections = ns["표준서식_hwpx_처리"](source)
            self.assertEqual(ns["표준서식_hwpx_처리"](source, target, selections), 3)
            audit = inspect_hanging_indent(target, reference / "기본 서식.hwpx")
            self.assertEqual(audit["status"], "pass")
            findings = {item["text"]: item for item in audit["findings"]}
            expected_pairs = reference_marker_indent_pairs(reference / "기본 서식.hwpx")
            self.assertEqual(
                (findings["ㅁ 추진 배경"]["left"], findings["ㅁ 추진 배경"]["indent"]),
                safe_reference_hanging_indent_pair("ㅁ 추진 배경", expected_pairs),
            )
            self.assertEqual(
                (findings[" ㅇ (삼체 행성 상황) 3개 항성의 불규칙 운동"]["left"],
                 findings[" ㅇ (삼체 행성 상황) 3개 항성의 불규칙 운동"]["indent"]),
                safe_reference_hanging_indent_pair(" ㅇ (삼체 행성 상황) 3개 항성의 불규칙 운동", expected_pairs),
            )
            self.assertEqual(
                (findings["   * 항세기: 기후가 안정된 시기"]["left"],
                 findings["   * 항세기: 기후가 안정된 시기"]["indent"]),
                safe_reference_hanging_indent_pair("   * 항세기: 기후가 안정된 시기", expected_pairs),
            )


if __name__ == "__main__":
    unittest.main()
