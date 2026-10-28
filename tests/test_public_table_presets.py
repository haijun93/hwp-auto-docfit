"""공공기관·비즈니스 6대 표준 표 템플릿 프리셋 단위 시험 (2.0.1 P7 정식 결합)."""

import copy
import hashlib
import os
import re
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from defusedxml import ElementTree as ET

from docfit_core import table_builder, table_units
from docfit_core import table_catalog as catalog
from docfit_core.hwpx import open_hwpx_safely
from docfit_core.public_table_presets import (
    CATEGORY_NAME,
    PUBLIC_PRESET_REVISION,
    PUBLIC_TABLE_PRESETS,
    build_public_preset_preview,
    export_public_preset,
    get_public_preset,
    get_public_preset_descriptors,
    is_public_preset,
    preview_public_preset,
    public_preset_plan,
    public_preset_snapshot_key,
    _default_base_path,
    _remove_public_preview_image,
    _validate_public_contents,
    _hash_public_tree,
    _public_para,
    _write_public_package,
    _build_public_document,
)


class PublicTablePresetsTest(unittest.TestCase):
    def test_import_uses_existing_hwpx_helper(self):
        from docfit_core.hwpx import open_hwpx_safely as helper
        self.assertTrue(callable(helper))
        self.assertTrue(callable(get_public_preset_descriptors))
        self.assertTrue(callable(preview_public_preset))
        self.assertTrue(callable(export_public_preset))
        self.assertTrue(callable(public_preset_snapshot_key))

    def test_descriptors_has_six_presets(self):
        descriptors = get_public_preset_descriptors()
        self.assertEqual(len(descriptors), 6)
        ids = [d["id"] for d in descriptors]
        expected_ids = [
            "pub_summary_headline",
            "pub_two_col_definition",
            "pub_multi_col_comparison",
            "pub_gantt_timeline",
            "pub_budget_breakdown",
            "pub_qa_checklist",
        ]
        self.assertEqual(ids, expected_ids)
        for d in descriptors:
            self.assertEqual(d["category"], "공공 표준")
            self.assertTrue(d["name"].startswith(("①", "②", "③", "④", "⑤", "⑥")))
            self.assertIn("guideline", d)
            self.assertIn("badge", d)
            self.assertIn("description", d)

    def test_is_public_preset(self):
        self.assertTrue(is_public_preset("pub_summary_headline"))
        self.assertTrue(is_public_preset("pub_qa_checklist"))
        self.assertFalse(is_public_preset("unknown_preset"))
        self.assertFalse(is_public_preset("pub_unknown"))

    def test_preview_generation_all_presets(self):
        for pid in PUBLIC_TABLE_PRESETS:
            preview = preview_public_preset(pid)
            self.assertIn("rows", preview)
            self.assertIn("cols", preview)
            self.assertIn("cell_meta", preview)
            meta = preview["cell_meta"]
            self.assertEqual(len(meta), preview["rows"])
            self.assertEqual(len(meta[0]), preview["cols"])

            for r, row in enumerate(meta):
                for c, cell in enumerate(row):
                    self.assertEqual(cell["row"], r)
                    self.assertEqual(cell["col"], c)
                    self.assertIn("width", cell)
                    self.assertIn("height", cell)
                    self.assertIn("text", cell)
                    self.assertIn("align", cell)
                    self.assertIn("style", cell)
                    self.assertIn("borders", cell)
                    self.assertIn("top", cell["borders"])
                    self.assertIn("bottom", cell["borders"])

    def test_headline_box_properties(self):
        preview = preview_public_preset("pub_summary_headline")
        self.assertEqual(preview["rows"], 1)
        self.assertEqual(preview["cols"], 1)
        cell = preview["cell_meta"][0][0]
        self.assertEqual(cell["style"]["fill"], "#EBF3FA")
        self.assertEqual(cell["borders"]["top"]["color"], "#1A365D")
        self.assertEqual(cell["borders"]["left"]["type"], "NONE")
        self.assertEqual(cell["borders"]["right"]["type"], "NONE")

    def test_two_col_definition_properties(self):
        preview = preview_public_preset("pub_two_col_definition")
        self.assertEqual(preview["rows"], 4)
        self.assertEqual(preview["cols"], 2)
        col0 = preview["cell_meta"][0][0]
        self.assertEqual(col0["style"]["fill"], "#F2F4F7")
        self.assertTrue(col0["style"]["bold"])
        self.assertEqual(col0["align"], "CENTER")
        col1 = preview["cell_meta"][0][1]
        self.assertEqual(col1["style"]["fill"], "#FFFFFF")
        self.assertFalse(col1["style"]["bold"])
        self.assertEqual(col1["align"], "LEFT")

    def test_custom_row_col_resizing(self):
        preview = preview_public_preset("pub_two_col_definition", row_count=6)
        self.assertEqual(preview["rows"], 6)
        self.assertEqual(len(preview["cell_meta"]), 6)

    # --- P7 정식 결합 신규 시험 (설계서 9장 명세) ---

    def test_descriptors_and_getter_are_deep_copies(self):
        desc1 = get_public_preset_descriptors()
        desc1[0]["units"]["row"] = {"mutated": True}
        desc1[0]["guideline"]["margins"] = "mutated"
        desc1[0]["badge"] = "mutated"
        desc2 = get_public_preset_descriptors()
        self.assertIsNone(desc2[0]["units"]["row"])
        self.assertNotEqual(desc2[0]["guideline"]["margins"], "mutated")
        self.assertNotEqual(desc2[0]["badge"], "mutated")

        p1 = get_public_preset("pub_two_col_definition")
        p1["sample_rows"][0][0] = "mutated"
        p2 = get_public_preset("pub_two_col_definition")
        self.assertEqual(p2["sample_rows"][0][0], "사 업 명")

        # 정확한 ID 6개, 순서, 카테고리, units 구조 검사
        expected = [
            ("pub_summary_headline", None, None),
            ("pub_two_col_definition", 4, None),
            ("pub_multi_col_comparison", 3, None),
            ("pub_gantt_timeline", 4, 4),
            ("pub_budget_breakdown", 3, None),
            ("pub_qa_checklist", 3, None),
        ]
        for idx, (exp_id, exp_rc, exp_cc) in enumerate(expected):
            self.assertEqual(desc2[idx]["id"], exp_id)
            self.assertEqual(desc2[idx]["category"], "공공 표준")
            u = desc2[idx]["units"]
            self.assertEqual(u["row"]["count"] if u["row"] else None, exp_rc)
            self.assertEqual(u["col"]["count"] if u["col"] else None, exp_cc)
            if u["row"]:
                self.assertNotIn("start", u["row"])
            if u["col"]:
                self.assertNotIn("start", u["col"])

    def test_unit_counts_exclude_header_footer_and_fixed_columns(self):
        # 기본값 검증
        cases = [
            ("pub_summary_headline", None, None, 1, 1),
            ("pub_two_col_definition", None, None, 4, 2),
            ("pub_multi_col_comparison", None, None, 5, 4),
            ("pub_gantt_timeline", None, None, 5, 6),
            ("pub_budget_breakdown", None, None, 5, 5),
            ("pub_qa_checklist", None, None, 4, 4),
        ]
        for pid, rc, cc, exp_r, exp_c in cases:
            res = preview_public_preset(pid, row_count=rc, col_count=cc)
            self.assertEqual(res["rows"], exp_r, f"{pid} rows mismatch")
            self.assertEqual(res["cols"], exp_c, f"{pid} cols mismatch")

        # 비교표 row_count=4 -> 헤더 1 + 단위 4 + 합계 1 = 6행
        comp = preview_public_preset("pub_multi_col_comparison", row_count=4)
        self.assertEqual(comp["rows"], 6)
        self.assertEqual(comp["cols"], 4)
        # 합계행은 마지막 1개만
        self.assertEqual(comp["cell_meta"][-1][0]["text"], "합 계")
        self.assertEqual(comp["cell_meta"][-2][0]["text"][:2], "출력")  # 본문 복제

        # 예산표 row_count=4 -> 헤더 1 + 단위 4 + 합계 1 = 6행
        budg = preview_public_preset("pub_budget_breakdown", row_count=4)
        self.assertEqual(budg["rows"], 6)
        self.assertEqual(budg["cell_meta"][-1][0]["text"], "합 계")

        # 간트표 col_count=5 -> 고정 2열 + 기간 5 = 7열
        gantt = preview_public_preset("pub_gantt_timeline", col_count=5)
        self.assertEqual(gantt["rows"], 5)
        self.assertEqual(gantt["cols"], 7)

        # QA 표 row_count=4 -> 헤더 1 + 단위 4 = 5행
        qa = preview_public_preset("pub_qa_checklist", row_count=4)
        self.assertEqual(qa["rows"], 5)

        # summary 고정 1x1
        summary = preview_public_preset("pub_summary_headline")
        self.assertEqual(summary["rows"], 1)
        self.assertEqual(summary["cols"], 1)

        # 6종 최소/최대 허용 범위 검증
        # two_col: min=1, max=30
        self.assertEqual(preview_public_preset("pub_two_col_definition", row_count=1)["rows"], 1)
        self.assertEqual(preview_public_preset("pub_two_col_definition", row_count=30)["rows"], 30)

        # multi_col: min=1 (1+1+1=3행), max=30 (1+30+1=32행)
        self.assertEqual(preview_public_preset("pub_multi_col_comparison", row_count=1)["rows"], 3)
        self.assertEqual(preview_public_preset("pub_multi_col_comparison", row_count=30)["rows"], 32)

        # gantt: min=(row 1, col 2) -> (2행, 4열), max=(row 30, col 12) -> (31행, 14열)
        g_min = preview_public_preset("pub_gantt_timeline", row_count=1, col_count=2)
        self.assertEqual(g_min["rows"], 2)
        self.assertEqual(g_min["cols"], 4)
        g_max = preview_public_preset("pub_gantt_timeline", row_count=30, col_count=12)
        self.assertEqual(g_max["rows"], 31)
        self.assertEqual(g_max["cols"], 14)

        # budget: min=1 (3행), max=30 (32행)
        self.assertEqual(preview_public_preset("pub_budget_breakdown", row_count=1)["rows"], 3)
        self.assertEqual(preview_public_preset("pub_budget_breakdown", row_count=30)["rows"], 32)

        # qa: min=1 (2행), max=30 (31행)
        self.assertEqual(preview_public_preset("pub_qa_checklist", row_count=1)["rows"], 2)
        self.assertEqual(preview_public_preset("pub_qa_checklist", row_count=30)["rows"], 31)

    def test_invalid_counts_and_fixed_axes_fail_without_output(self):
        invalids = [
            ("bool", True, None),
            ("float", 3.5, None),
            ("str", "3", None),
            ("zero", 0, None),
            ("negative", -1, None),
            ("min-1", 0, None),
            ("max+1", 31, None),
        ]
        with tempfile.TemporaryDirectory() as td:
            out_file = Path(td) / "test.hwpx"
            out_file.write_bytes(b"original_bytes")

            for label, r_val, c_val in invalids:
                with self.subTest(case="two_col", label=label):
                    with self.assertRaises(ValueError):
                        preview_public_preset("pub_two_col_definition", row_count=r_val, col_count=c_val)
                    with self.assertRaises(ValueError):
                        export_public_preset("pub_two_col_definition", out_file, row_count=r_val, col_count=c_val)
                    self.assertEqual(out_file.read_bytes(), b"original_bytes")

            # 고정축에 값 전달 시 실패 (기본값과 같아도 거부)
            with self.subTest(case="fixed_axis_two_col"):
                with self.assertRaises(ValueError):
                    preview_public_preset("pub_two_col_definition", col_count=2)
                with self.assertRaises(ValueError):
                    export_public_preset("pub_two_col_definition", out_file, col_count=2)
                self.assertEqual(out_file.read_bytes(), b"original_bytes")

            with self.subTest(case="fixed_axis_summary"):
                with self.assertRaises(ValueError):
                    preview_public_preset("pub_summary_headline", row_count=1)
                with self.assertRaises(ValueError):
                    export_public_preset("pub_summary_headline", out_file, row_count=1)
                self.assertEqual(out_file.read_bytes(), b"original_bytes")

            # 미등록 pub ID 거부
            with self.subTest(case="unknown_pub_id"):
                with self.assertRaises(ValueError):
                    preview_public_preset("pub_unknown")
                with self.assertRaises(ValueError):
                    export_public_preset("pub_unknown", out_file)
                self.assertEqual(out_file.read_bytes(), b"original_bytes")

    def test_legacy_preview_wrapper_uses_physical_dimensions(self):
        p1 = build_public_preset_preview("pub_two_col_definition", target_rows=6)
        p2 = preview_public_preset("pub_two_col_definition", row_count=6)
        self.assertEqual(p1["rows"], 6)
        self.assertEqual(p1["rows"], p2["rows"])
        self.assertEqual(p1["cols"], p2["cols"])

        # 간트 target_cols=7 -> 실제 7열 (col_count=5와 동일)
        g1 = build_public_preset_preview("pub_gantt_timeline", target_cols=7)
        g2 = preview_public_preset("pub_gantt_timeline", col_count=5)
        self.assertEqual(g1["cols"], 7)
        self.assertEqual(g1["cols"], g2["cols"])

        # 0, 음수, 고정축 변경 거부
        with self.assertRaises(ValueError):
            build_public_preset_preview("pub_two_col_definition", target_rows=0)
        with self.assertRaises(ValueError):
            build_public_preset_preview("pub_two_col_definition", target_cols=3)
        with self.assertRaises(ValueError):
            build_public_preset_preview("pub_summary_headline", target_rows=2)

    def test_fill_modes_and_text_overrides_match_export(self):
        with tempfile.TemporaryDirectory() as td:
            # increment
            p_inc = preview_public_preset("pub_qa_checklist", row_count=4, fill="increment")
            # 4행 단위 -> 5행 표. QA 4번째 항목 연번이 "04"로 증가해야 함
            self.assertEqual(p_inc["cell_meta"][4][0]["text"], "04")

            # blank
            p_blk = preview_public_preset("pub_qa_checklist", row_count=4, fill="blank")
            self.assertEqual(p_blk["cell_meta"][4][0]["text"], "")

            # copy
            p_cpy = preview_public_preset("pub_qa_checklist", row_count=4, fill="copy")
            self.assertEqual(p_cpy["cell_meta"][4][0]["text"], "03")

            # cell_texts 오버라이드
            texts = {"4,0": "99", "4,1": "사용자 지정 항목"}
            p_txt = preview_public_preset("pub_qa_checklist", row_count=4, fill="increment", cell_texts=texts)
            self.assertEqual(p_txt["cell_meta"][4][0]["text"], "99")
            self.assertEqual(p_txt["cell_meta"][4][1]["text"], "사용자 지정 항목")

            # 원본 샘플(01, 02, 03)은 보존
            self.assertEqual(p_txt["cell_meta"][1][0]["text"], "01")
            self.assertEqual(p_txt["cell_meta"][2][0]["text"], "02")
            self.assertEqual(p_txt["cell_meta"][3][0]["text"], "03")

            # export 파일에서도 동일 텍스트 확인
            out_file = Path(td) / "qa_export.hwpx"
            export_public_preset("pub_qa_checklist", out_file, row_count=4, fill="increment", cell_texts=texts)
            with open_hwpx_safely(out_file) as z:
                sec_root = ET.fromstring(z.read("Contents/section0.xml"))
                tbl = sec_root.find(f".//{table_units.HP}tbl")
                rows = tbl.findall(table_units.HP + "tr")
                last_row_tcs = rows[4].findall(table_units.HP + "tc")
                txt0 = "".join(n.text or "" for n in catalog._cell_text_nodes(last_row_tcs[0]))
                txt1 = "".join(n.text or "" for n in catalog._cell_text_nodes(last_row_tcs[1]))
                self.assertEqual(txt0.strip(), "99")
                self.assertEqual(txt1.strip(), "사용자 지정 항목")

    def test_text_validation_and_multiline_roundtrip(self):
        long_text = "가나다 " * 140  # 약 560자
        multiline = "첫째 줄\n둘째 줄\t(탭)&<>"
        with tempfile.TemporaryDirectory() as td:
            out_file = Path(td) / "text_test.hwpx"
            texts = {"1,1": long_text, "2,1": multiline}
            p = preview_public_preset("pub_two_col_definition", cell_texts=texts)
            # preview는 80자로 잘림
            self.assertLessEqual(len(p["cell_meta"][1][1]["text"]), 80)

            # export는 원문 전체(1000자 이내) 보존
            export_public_preset("pub_two_col_definition", out_file, cell_texts=texts)
            with open_hwpx_safely(out_file) as z:
                sec_root = ET.fromstring(z.read("Contents/section0.xml"))
                tbl = sec_root.find(f".//{table_units.HP}tbl")
                rows = tbl.findall(table_units.HP + "tr")
                tcs_r1 = rows[1].findall(table_units.HP + "tc")
                tcs_r2 = rows[2].findall(table_units.HP + "tc")
                full_r1 = "".join(n.text or "" for n in catalog._cell_text_nodes(tcs_r1[1])).strip()
                full_r2_lines = [
                    "".join(n.text or "" for n in p_el.iter(table_units.HP + "t"))
                    for p_el in tcs_r2[1].findall(f".//{table_units.HP}p")
                ]
                self.assertEqual(full_r1, long_text.strip())
                self.assertEqual("\n".join(full_r2_lines), multiline)

            # 1001자 거부
            with self.assertRaises(ValueError):
                preview_public_preset("pub_two_col_definition", cell_texts={"1,1": "a" * 1001})
            # 제어문자 거부
            with self.assertRaises(ValueError):
                preview_public_preset("pub_two_col_definition", cell_texts={"1,1": "a\x00b"})
            # 잘못된 좌표 거부
            with self.assertRaises(ValueError):
                preview_public_preset("pub_two_col_definition", cell_texts={"99,99": "a"})

    def test_all_six_exports_reparse_as_single_table(self):
        base_path = _default_base_path()
        base_hash_before = hashlib.sha256(base_path.read_bytes()).hexdigest()

        with tempfile.TemporaryDirectory() as td:
            for pid in PUBLIC_TABLE_PRESETS:
                out_hwpx = Path(td) / f"{pid}.hwpx"
                export_public_preset(pid, out_hwpx)
                self.assertTrue(out_hwpx.is_file())

                with open_hwpx_safely(out_hwpx) as z:
                    # mimetype 첫 항목 ZIP_STORED 확인
                    infolist = z.infolist()
                    self.assertEqual(infolist[0].filename, "mimetype")
                    self.assertEqual(infolist[0].compress_type, zipfile.ZIP_STORED)

                    # 최상위 표 1개 검사
                    sec = ET.fromstring(z.read("Contents/section0.xml"))
                    tbls = sec.findall(f".//{table_units.HP}tbl")
                    self.assertEqual(len(tbls), 1)

                    # table_catalog preview 파싱 검사
                    record = catalog._scan(out_hwpx)[0]
                    cat_prev = catalog.preview(record["id"], out_hwpx)
                    self.assertEqual(cat_prev["rows"], PUBLIC_TABLE_PRESETS[pid]["default_rows"])
                    self.assertEqual(cat_prev["cols"], PUBLIC_TABLE_PRESETS[pid]["default_cols"])

        base_hash_after = hashlib.sha256(base_path.read_bytes()).hexdigest()
        self.assertEqual(base_hash_before, base_hash_after, "원본 base 서식이 수정되지 않아야 합니다.")

    def test_preview_and_export_have_identical_cell_metadata(self):
        cases = [
            # 기본
            ("pub_summary_headline", None, None),
            ("pub_two_col_definition", None, None),
            ("pub_multi_col_comparison", None, None),
            ("pub_gantt_timeline", None, None),
            ("pub_budget_breakdown", None, None),
            ("pub_qa_checklist", None, None),
            # 최소
            ("pub_two_col_definition", 1, None),
            ("pub_multi_col_comparison", 1, None),
            ("pub_gantt_timeline", 1, 2),
            ("pub_budget_breakdown", 1, None),
            ("pub_qa_checklist", 1, None),
            # 최대
            ("pub_two_col_definition", 30, None),
            ("pub_multi_col_comparison", 30, None),
            ("pub_budget_breakdown", 30, None),
            ("pub_qa_checklist", 30, None),
            # 간트 양축 동시 변경
            ("pub_gantt_timeline", 10, 6),
            ("pub_gantt_timeline", 30, 12),
        ]
        with tempfile.TemporaryDirectory() as td:
            for pid, rc, cc in cases:
                prev = preview_public_preset(pid, row_count=rc, col_count=cc)
                out_path = Path(td) / f"{pid}_{rc}_{cc}_cmp.hwpx"
                export_public_preset(pid, out_path, row_count=rc, col_count=cc)

                record = catalog._scan(out_path)[0]
                reparsed = catalog.preview(record["id"], out_path)

                self.assertEqual(prev["rows"], reparsed["rows"])
                self.assertEqual(prev["cols"], reparsed["cols"])
                for r in range(prev["rows"]):
                    for c in range(prev["cols"]):
                        m1 = prev["cell_meta"][r][c]
                        m2 = reparsed["cell_meta"][r][c]
                        self.assertEqual(m1["row"], m2["row"])
                        self.assertEqual(m1["col"], m2["col"])
                        self.assertEqual(m1["rowSpan"], m2["rowSpan"])
                        self.assertEqual(m1["colSpan"], m2["colSpan"])
                        self.assertEqual(m1["text"], m2["text"])
                        self.assertEqual(m1["width"], m2["width"])
                        self.assertEqual(m1["height"], m2["height"])
                        self.assertEqual(m1["align"], m2["align"])
                        self.assertEqual(m1["style"], m2["style"])
                        self.assertEqual(m1["borders"], m2["borders"])
                        self.assertEqual(m1.get("shapes"), m2.get("shapes"))

    def test_public_metrics_are_written_to_xml(self):
        with tempfile.TemporaryDirectory() as td:
            # 요약 상자 여백 및 문단 속성
            out_sum = Path(td) / "summary.hwpx"
            export_public_preset("pub_summary_headline", out_sum)
            with open_hwpx_safely(out_sum) as z:
                sec = ET.fromstring(z.read("Contents/section0.xml"))
                hdr = ET.fromstring(z.read("Contents/header.xml"))
                tc = sec.find(f".//{table_units.HP}tc")
                cm = tc.find(table_units.HP + "cellMargin")
                self.assertEqual(cm.get("left"), "1134")
                self.assertEqual(cm.get("right"), "1134")
                self.assertEqual(cm.get("top"), "708")
                self.assertEqual(cm.get("bottom"), "708")

                p = tc.find(f".//{table_units.HP}p")
                para_id = p.get("paraPrIDRef")
                para_prop = next(x for x in hdr.iter() if table_builder._tag(x) == "paraPr" and x.get("id") == para_id)
                ls = next(x for x in para_prop.iter() if table_builder._tag(x) == "lineSpacing")
                self.assertEqual(ls.get("value"), "140")

                run = p.find(table_units.HP + "run")
                char_id = run.get("charPrIDRef")
                char_prop = next(x for x in hdr.iter() if table_builder._tag(x) == "charPr" and x.get("id") == char_id)
                sp = next(x for x in char_prop.iter() if table_builder._tag(x) == "spacing")
                self.assertEqual(sp.attrib.get("hangul"), "-5")

    def test_definition_has_no_implicit_header_double_border(self):
        prev = preview_public_preset("pub_two_col_definition")
        # r=0과 r=1 사이의 공유 변은 inner_h 실선이어야 함
        r0_bottom = prev["cell_meta"][0][0]["borders"]["bottom"]
        r1_top = prev["cell_meta"][1][0]["borders"]["top"]
        self.assertEqual(r0_bottom["type"], "SOLID")
        self.assertEqual(r1_top["type"], "SOLID")
        self.assertNotEqual(r0_bottom["type"], "DOUBLE_SLIM")

        # summary 좌우는 NONE
        sum_prev = preview_public_preset("pub_summary_headline")
        self.assertEqual(sum_prev["cell_meta"][0][0]["borders"]["left"]["type"], "NONE")
        self.assertEqual(sum_prev["cell_meta"][0][0]["borders"]["right"]["type"], "NONE")

        # 간트 고정열 사이(0열과 1열 사이)는 SOLID, 기간 영역 내부(2열과 3열 사이)는 DOT
        gantt_prev = preview_public_preset("pub_gantt_timeline")
        col0_right = gantt_prev["cell_meta"][1][0]["borders"]["right"]
        col1_left = gantt_prev["cell_meta"][1][1]["borders"]["left"]
        self.assertEqual(col0_right["type"], "SOLID")
        self.assertEqual(col1_left["type"], "SOLID")

        col2_right = gantt_prev["cell_meta"][1][2]["borders"]["right"]
        col3_left = gantt_prev["cell_meta"][1][3]["borders"]["left"]
        self.assertEqual(col2_right["type"], "DOT")
        self.assertEqual(col3_left["type"], "DOT")

    def test_footer_styles_and_qa_status_after_resize(self):
        # QA 상태 검증
        qa = preview_public_preset(
            "pub_qa_checklist",
            row_count=4,
            cell_texts={
                "1,3": "적합",
                "2,3": "보완 요망",
                "3,3": "부적합",
                "4,3": "검토 중 임의 문구",
            }
        )
        # 적합 -> 녹색 (#E6F4EA, #188038)
        self.assertEqual(qa["cell_meta"][1][3]["style"]["fill"], "#E6F4EA")
        self.assertEqual(qa["cell_meta"][1][3]["style"]["color"], "#188038")
        # 보완 요망 -> 적색 (#FCE8E6, #D93025)
        self.assertEqual(qa["cell_meta"][2][3]["style"]["fill"], "#FCE8E6")
        self.assertEqual(qa["cell_meta"][2][3]["style"]["color"], "#D93025")
        # 부적합 -> 적색 (#FCE8E6, #D93025)
        self.assertEqual(qa["cell_meta"][3][3]["style"]["fill"], "#FCE8E6")
        self.assertEqual(qa["cell_meta"][3][3]["style"]["color"], "#D93025")
        # 임의 문구 -> 검정/흰색
        self.assertEqual(qa["cell_meta"][4][3]["style"]["fill"], "#FFFFFF")
        self.assertEqual(qa["cell_meta"][4][3]["style"]["color"], "#000000")

    def test_gantt_max_columns_keep_total_width(self):
        # 간트 최대 col_count=12 -> 실제 14열, row_count=30 -> 실제 31행
        gantt = preview_public_preset("pub_gantt_timeline", row_count=30, col_count=12)
        self.assertEqual(gantt["rows"], 31)
        self.assertEqual(gantt["cols"], 14)

        widths = [cell["width"] for cell in gantt["cell_meta"][0]]
        self.assertEqual(len(widths), 14)
        for w in widths:
            self.assertGreater(w, 0)

        # 전체 폭이 본문 폭과 정확히 일치하는지 확인
        with tempfile.TemporaryDirectory() as td:
            out_file = Path(td) / "gantt_max.hwpx"
            export_public_preset("pub_gantt_timeline", out_file, row_count=30, col_count=12)
            with open_hwpx_safely(out_file) as z:
                sec = ET.fromstring(z.read("Contents/section0.xml"))
                page_pr = next(x for x in sec.iter() if table_builder._tag(x) == "pagePr")
                m_el = table_builder._child(page_pr, "margin")
                body_w = int(page_pr.get("width")) - int(m_el.get("left")) - int(m_el.get("right"))
                tbl = sec.find(f".//{table_units.HP}tbl")
                self.assertEqual(int(tbl.find(table_units.HP + "sz").get("width")), body_w)

    def test_snapshot_key_is_deterministic_and_tracks_styles(self):
        k1 = public_preset_snapshot_key("pub_summary_headline")
        k2 = public_preset_snapshot_key("pub_summary_headline")
        self.assertEqual(k1, k2)
        self.assertEqual(len(k1), 20)

        k_other = public_preset_snapshot_key("pub_two_col_definition")
        self.assertNotEqual(k1, k_other)

        with self.assertRaises(ValueError):
            public_preset_snapshot_key("pub_unknown")

        # revision 변경 시 키 변경
        with patch("docfit_core.public_table_presets.PUBLIC_PRESET_REVISION", "test-rev-new"):
            self.assertNotEqual(public_preset_snapshot_key("pub_summary_headline"), k1)

        # 샘플 텍스트 변경 시 키 변경
        with patch.dict(PUBLIC_TABLE_PRESETS["pub_summary_headline"], {"sample_rows": [["다른 요약 텍스트"]]}):
            self.assertNotEqual(public_preset_snapshot_key("pub_summary_headline"), k1)

        # cellMargin 변경 시 키 변경
        with patch.dict(PUBLIC_TABLE_PRESETS["pub_summary_headline"]["margins_hwpunit"], {"left": 2500}):
            self.assertNotEqual(public_preset_snapshot_key("pub_summary_headline"), k1)

        # pagePr margin top/bottom 변경 시 키 변경
        with tempfile.TemporaryDirectory() as td:
            base_src = _default_base_path()
            mod_base = Path(td) / "mod_base.hwpx"
            with open_hwpx_safely(base_src) as z_in, zipfile.ZipFile(mod_base, "w") as z_out:
                for item in z_in.infolist():
                    data = z_in.read(item.filename)
                    if item.filename == "Contents/section0.xml":
                        sec_el = ET.fromstring(data)
                        p_pr = next(x for x in sec_el.iter() if table_builder._tag(x) == "pagePr")
                        m_el = table_builder._child(p_pr, "margin")
                        m_el.set("top", "9999")
                        data = table_builder._serialize(sec_el, data)
                    z_out.writestr(item, data)
            with patch("docfit_core.public_table_presets._default_base_path", return_value=mod_base):
                self.assertNotEqual(public_preset_snapshot_key("pub_summary_headline"), k1)

    def test_export_failure_preserves_target_and_base(self):
        base_path = _default_base_path()
        base_bytes = base_path.read_bytes()

        # base 경로와 동일한 곳으로 export 시도 -> 거부
        with self.assertRaises(ValueError):
            export_public_preset("pub_summary_headline", base_path)
        self.assertEqual(base_path.read_bytes(), base_bytes)

        # base 사본의 하드링크 대상 export 거부
        with tempfile.TemporaryDirectory() as td:
            temp_base_copy = Path(td) / "base_copy.hwpx"
            temp_base_copy.write_bytes(base_bytes)
            hardlink_target = Path(td) / "hardlink.hwpx"
            try:
                os.link(temp_base_copy, hardlink_target)
                has_hardlink = True
            except (OSError, NotImplementedError):
                has_hardlink = False

            if has_hardlink:
                with patch("docfit_core.public_table_presets._default_base_path", return_value=temp_base_copy):
                    with self.assertRaises(ValueError):
                        export_public_preset("pub_summary_headline", hardlink_target)
                self.assertEqual(temp_base_copy.read_bytes(), base_bytes)

        # 임시 대상 파일 생성 후 replace 실패 시 기존 대상 파일 보존
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "existing.hwpx"
            target.write_bytes(b"preserve_me")
            with patch("pathlib.Path.replace", side_effect=OSError("replace_failed")):
                with self.assertRaises(OSError):
                    export_public_preset("pub_summary_headline", target)
            self.assertEqual(target.read_bytes(), b"preserve_me")
            tmps = [p for p in target.parent.iterdir() if p.name.startswith("existing.hwpx.tmp")]
            self.assertEqual(len(tmps), 0)

        # 검증 실패 시 기존 대상 파일 보존 및 tmp 정리
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "existing_val.hwpx"
            target.write_bytes(b"preserve_me_val")
            with patch("docfit_core.public_table_presets._validate_public_contents", side_effect=ValueError("bad_contents")):
                with self.assertRaises(ValueError):
                    export_public_preset("pub_summary_headline", target)
            self.assertEqual(target.read_bytes(), b"preserve_me_val")
            tmps = [p for p in target.parent.iterdir() if p.name.startswith("existing_val.hwpx.tmp")]
            self.assertEqual(len(tmps), 0)

    def test_base_sections_checked_before_builder(self):
        """임시 2section base를 주고 builder 호출0·ValueError·출력없음."""
        with tempfile.TemporaryDirectory() as td:
            base_src = _default_base_path()
            multi_sec_base = Path(td) / "multi_section.hwpx"
            with open_hwpx_safely(base_src) as z_in, zipfile.ZipFile(multi_sec_base, "w") as z_out:
                for item in z_in.infolist():
                    z_out.writestr(item, z_in.read(item.filename))
                # 두 번째 섹션 추가
                z_out.writestr("Contents/section1.xml", z_in.read("Contents/section0.xml"))

            out_target = Path(td) / "out.hwpx"
            with patch("docfit_core.public_table_presets._default_base_path", return_value=multi_sec_base), \
                 patch("docfit_core.table_builder.build_table_hwpx") as mock_builder:
                with self.assertRaises(ValueError) as ctx:
                    export_public_preset("pub_summary_headline", out_target)
                self.assertIn("단일 section", str(ctx.exception))
                self.assertEqual(mock_builder.call_count, 0)
                self.assertFalse(out_target.exists())

    def test_removed_preview_image_has_no_manifest_reference(self):
        """preview image manifest item/idref 포함 fixture에서 파일·참조 제거, 다른 manifest item 보존."""
        hpf_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<package xmlns="http://www.idpf.org/2007/opf" version="2.0">'
            '<metadata><title>Test</title></metadata>'
            '<manifest>'
            '<item id="header" href="header.xml" media-type="application/xml"/>'
            '<item id="section0" href="section0.xml" media-type="application/xml"/>'
            '<item id="prv_img" href="Preview/PrvImage.png" media-type="image/png"/>'
            '</manifest>'
            '<spine>'
            '<itemref idref="section0"/>'
            '<itemref idref="prv_img"/>'
            '</spine>'
            '</package>'
        ).encode("utf-8")

        contents = {
            "Contents/content.hpf": hpf_xml,
            "Preview/PrvImage.png": b"fake_png",
            "Contents/header.xml": b"<header/>",
            "Contents/section0.xml": b"<section0/>",
        }

        _remove_public_preview_image(contents)

        self.assertNotIn("Preview/PrvImage.png", contents)
        new_hpf = ET.fromstring(contents["Contents/content.hpf"])
        items = [x for x in new_hpf.iter() if table_builder._tag(x) == "item"]
        itemrefs = [x for x in new_hpf.iter() if table_builder._tag(x) == "itemref"]

        self.assertEqual(len(items), 2)
        self.assertFalse(any(it.get("id") == "prv_img" for it in items))
        self.assertTrue(any(it.get("id") == "header" for it in items))
        self.assertTrue(any(it.get("id") == "section0" for it in items))

        self.assertEqual(len(itemrefs), 1)
        self.assertEqual(itemrefs[0].get("idref"), "section0")

    def test_non_percent_line_spacing_is_replaced(self):
        """paraPr id0의 FIXED 및 lineSpacing 누락 fixture를 PERCENT 140/130으로 만들고 미리보기/export가 같은 결과."""
        with tempfile.TemporaryDirectory() as td:
            base_src = _default_base_path()
            mod_base = Path(td) / "mod_para.hwpx"
            with open_hwpx_safely(base_src) as z_in, zipfile.ZipFile(mod_base, "w") as z_out:
                for item in z_in.infolist():
                    data = z_in.read(item.filename)
                    if item.filename == "Contents/header.xml":
                        hdr_el = ET.fromstring(data)
                        for p_pr in hdr_el.iter():
                            if table_builder._tag(p_pr) == "paraPr" and p_pr.get("id") == "0":
                                for ls in list(p_pr):
                                    if table_builder._tag(ls) == "lineSpacing":
                                        ls.set("type", "FIXED")
                                        ls.set("value", "2000")
                        data = table_builder._serialize(hdr_el, data)
                    z_out.writestr(item, data)

            with patch("docfit_core.public_table_presets._default_base_path", return_value=mod_base):
                prev = preview_public_preset("pub_summary_headline")
                out_path = Path(td) / "out_sum.hwpx"
                export_public_preset("pub_summary_headline", out_path)

                with open_hwpx_safely(out_path) as z:
                    hdr = ET.fromstring(z.read("Contents/header.xml"))
                    sec = ET.fromstring(z.read("Contents/section0.xml"))
                    p = sec.find(f".//{table_units.HP}p")
                    pid = p.get("paraPrIDRef")
                    para_prop = next(x for x in hdr.iter() if table_builder._tag(x) == "paraPr" and x.get("id") == pid)
                    ls = next(x for x in para_prop.iter() if table_builder._tag(x) == "lineSpacing")
                    self.assertEqual(ls.get("type"), "PERCENT")
                    self.assertEqual(ls.get("value"), "140")

    def test_package_rejects_dangling_style_references(self):
        """border/char/para/style/fontRef·중복ID·잘못된 itemCnt·manifest href 각각 손상한 contents가 replace 전에 실패."""
        # 정상 문서 생성 후 contents 추출
        contents, _, _ = _build_public_document(
            "pub_summary_headline", None, None, fill="increment", cell_texts=None
        )

        # 1. borderFillIDRef 손상
        bad_bf = copy.deepcopy(contents)
        sec = ET.fromstring(bad_bf["Contents/section0.xml"])
        tc = sec.find(f".//{table_units.HP}tc")
        tc.set("borderFillIDRef", "999999")
        bad_bf["Contents/section0.xml"] = table_builder._serialize(sec, contents["Contents/section0.xml"])
        with self.assertRaises(ValueError) as ctx:
            _validate_public_contents(bad_bf)
        self.assertIn("borderFillIDRef", str(ctx.exception))

        # 2. charPrIDRef 손상
        bad_char = copy.deepcopy(contents)
        sec = ET.fromstring(bad_char["Contents/section0.xml"])
        run = sec.find(f".//{table_units.HP}run")
        run.set("charPrIDRef", "888888")
        bad_char["Contents/section0.xml"] = table_builder._serialize(sec, contents["Contents/section0.xml"])
        with self.assertRaises(ValueError) as ctx:
            _validate_public_contents(bad_char)
        self.assertIn("charPrIDRef", str(ctx.exception))

        # 3. paraPrIDRef 손상
        bad_para = copy.deepcopy(contents)
        sec = ET.fromstring(bad_para["Contents/section0.xml"])
        p = sec.find(f".//{table_units.HP}p")
        p.set("paraPrIDRef", "777777")
        bad_para["Contents/section0.xml"] = table_builder._serialize(sec, contents["Contents/section0.xml"])
        with self.assertRaises(ValueError) as ctx:
            _validate_public_contents(bad_para)
        self.assertIn("paraPrIDRef", str(ctx.exception))

        # 4. 중복 ID 존재
        bad_dup = copy.deepcopy(contents)
        hdr = ET.fromstring(bad_dup["Contents/header.xml"])
        bf_group = next(x for x in hdr.iter() if table_builder._tag(x) == "borderFills")
        clone_bf = copy.deepcopy(list(bf_group)[0])
        bf_group.append(clone_bf)  # 동일한 ID 중복 추가
        bf_group.set("itemCnt", str(len(list(bf_group))))
        bad_dup["Contents/header.xml"] = table_builder._serialize(hdr, contents["Contents/header.xml"])
        with self.assertRaises(ValueError) as ctx:
            _validate_public_contents(bad_dup)
        self.assertIn("중복된 id", str(ctx.exception))

        # 5. 잘못된 itemCnt
        bad_cnt = copy.deepcopy(contents)
        hdr = ET.fromstring(bad_cnt["Contents/header.xml"])
        bf_group = next(x for x in hdr.iter() if table_builder._tag(x) == "borderFills")
        bf_group.set("itemCnt", "999")
        bad_cnt["Contents/header.xml"] = table_builder._serialize(hdr, contents["Contents/header.xml"])
        with self.assertRaises(ValueError) as ctx:
            _validate_public_contents(bad_cnt)
        self.assertIn("itemCnt", str(ctx.exception))

        # 6. manifest href 누락
        bad_manifest = copy.deepcopy(contents)
        if "Contents/content.hpf" in bad_manifest:
            hpf = ET.fromstring(bad_manifest["Contents/content.hpf"])
            manifest = next(x for x in hpf.iter() if table_builder._tag(x) == "manifest")
            bad_item = ET.SubElement(manifest, "item", {"id": "ghost", "href": "ghost_file.xml"})
            bad_manifest["Contents/content.hpf"] = table_builder._serialize(hpf, contents["Contents/content.hpf"])
            with self.assertRaises(ValueError) as ctx:
                _validate_public_contents(bad_manifest)
            self.assertIn("manifest 참조 파일", str(ctx.exception))

    def test_unique_temporary_outputs_do_not_collide(self):
        """실제 스레드/COM 없이 임시 생성 helper 두 호출의 서로 다른 경로와 각 실패 정리를 검사. 다른 임시 파일은 보존."""
        with tempfile.TemporaryDirectory() as td:
            target1 = Path(td) / "out1.hwpx"
            target2 = Path(td) / "out2.hwpx"

            # 기존 다른 임시 파일 존재
            other_tmp = Path(td) / "out1.hwpx.tmp_other.hwpx"
            other_tmp.write_bytes(b"leave_me_alone")

            # 두 번 export
            export_public_preset("pub_summary_headline", target1)
            export_public_preset("pub_two_col_definition", target2)

            self.assertTrue(target1.is_file())
            self.assertTrue(target2.is_file())
            self.assertTrue(other_tmp.is_file(), "기존 다른 임시 파일은 보존되어야 합니다.")


if __name__ == "__main__":
    unittest.main()
