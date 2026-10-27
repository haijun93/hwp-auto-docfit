"""공공기관·비즈니스 6대 표준 표 템플릿 프리셋 엔진 (2.0.1).
행정업무운영편람 및 기획재정부 보고서 표준 지침에 맞춘 조판 메트릭스, 셀 메타, HWPX 생성 자립 모듈.
"""

from __future__ import annotations

import copy
import hashlib
import io
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as ET

from docfit_core import table_builder
from docfit_core import table_catalog as catalog
from docfit_core import table_units
from docfit_core.archive_safety import open_hwpx_safely

CATEGORY_NAME = "공공 표준"
PUBLIC_PRESET_REVISION = "p7-v1"

# 6대 공공 표준 프리셋 정의 (공공 업무 예시 프리셋)
PUBLIC_TABLE_PRESETS: dict[str, dict[str, Any]] = {
    "pub_summary_headline": {
        "id": "pub_summary_headline",
        "category": CATEGORY_NAME,
        "name": "① 요약/헤드라인 1칸 표",
        "badge": "핵심 요약",
        "description": "상하 0.4mm 굵은선, 좌우 개방형, 연청색 음영의 핵심 요약 콜아웃 상자",
        "default_rows": 1,
        "default_cols": 1,
        "header_rows": 0,
        "footer_rows": 0,
        "line_spacing": 140,
        "char_spacing": -5,
        "col_ratios": [1.0],
        "margins_hwpunit": {"left": 1134, "right": 1134, "top": 708, "bottom": 708},
        "guideline": {
            "margins": "좌우 4.0mm / 상하 2.5mm",
            "borders": "상하 실선 0.4mm (#1A365D), 좌우 선없음",
            "font": "한컴돋움 10.5pt / 줄간격 140% / 자간 -5%",
            "fill": "소프트블루 (#EBF3FA, 12%)"
        },
        "units": {
            "row": None,
            "col": None
        },
        "_plan": {
            "row": None,
            "col": None
        },
        "sample_rows": [
            ["◈ [핵심 요약] 본 사업은 차세대 공공 서식 자동화 표준을 확립하고, 부처 간 문서 정합성을 99.8% 수준으로 제고하기 위해 추진됨."]
        ],
        "default_style": {
            "font": "한컴돋움",
            "size": 10.5,
            "bold": False,
            "color": "#1A202C",
            "fill": "#EBF3FA",
            "align": "LEFT"
        },
        "borders": {
            "top": {"type": "SOLID", "width": 0.4, "color": "#1A365D"},
            "bottom": {"type": "SOLID", "width": 0.4, "color": "#1A365D"},
            "left": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "right": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "inner_h": {"type": "SOLID", "width": 0.12, "color": "#CBD5E1"},
            "inner_v": {"type": "NONE", "width": 0.1, "color": "#000000"}
        }
    },

    "pub_two_col_definition": {
        "id": "pub_two_col_definition",
        "category": CATEGORY_NAME,
        "name": "② 2열 정의/대비 표",
        "badge": "개요 양식",
        "description": "좌측 항목 22% 연회색 음영, 우측 세부내용 78% 정렬의 표준 개요 양식",
        "default_rows": 4,
        "default_cols": 2,
        "header_rows": 0,
        "footer_rows": 0,
        "line_spacing": 130,
        "char_spacing": 0,
        "col_ratios": [0.22, 0.78],
        "margins_hwpunit": {"left": 708, "right": 708, "top": 340, "bottom": 340},
        "guideline": {
            "margins": "좌우 2.5mm / 상하 1.2mm",
            "borders": "상하 0.4mm, 좌우 개방, 내부 0.12mm (#E2E8F0)",
            "font": "항목 한컴돋움 9.5pt Bold / 본문 휴먼명조 9.5pt / 줄간격 130%",
            "fill": "항목열 연회색 (#F2F4F7) / 내용열 흰색"
        },
        "units": {
            "row": {"count": 4, "min": 1, "max": 30, "core": 1, "sep": 0},
            "col": None
        },
        "_plan": {
            "row": {"start": 0, "count": 4, "min": 1, "max": 30, "core": 1, "sep": 0},
            "col": None
        },
        "sample_rows": [
            ["사 업 명", "2026년 공공 행정 문서 표준화 및 자동 조판 엔진 고도화"],
            ["추진 목적", "HWPX 개방형 서식 확산 및 공공기관 실무 보고서 작성 효율성 50% 향상"],
            ["수행 기간", "2026. 01. 01. ~ 2026. 12. 31. (12개월)"],
            ["총 소요예산", "금 850,000,000원 (팔억오천만 원, 부가세 포함)"]
        ],
        "borders": {
            "top": {"type": "SOLID", "width": 0.4, "color": "#000000"},
            "bottom": {"type": "SOLID", "width": 0.4, "color": "#000000"},
            "left": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "right": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "inner_h": {"type": "SOLID", "width": 0.12, "color": "#E2E8F0"},
            "inner_v": {"type": "SOLID", "width": 0.12, "color": "#CBD5E1"}
        }
    },

    "pub_multi_col_comparison": {
        "id": "pub_multi_col_comparison",
        "category": CATEGORY_NAME,
        "name": "③ 3~4열 다단 비교/평가 표",
        "badge": "비교·평가",
        "description": "머리글 다크네이비/연청, 본문 지브라 교차 음영, 최하단 합계 행",
        "default_rows": 5,
        "default_cols": 4,
        "header_rows": 1,
        "footer_rows": 1,
        "line_spacing": 130,
        "char_spacing": 0,
        "col_ratios": [0.18, 0.37, 0.30, 0.15],
        "margins_hwpunit": {"left": 708, "right": 708, "top": 340, "bottom": 340},
        "guideline": {
            "margins": "좌우 2.5mm / 상하 1.2mm",
            "borders": "상단 0.4mm, 머리글하단 이중선 0.5mm, 하단 0.4mm",
            "font": "머리글 한컴돋움 9.5pt Bold / 본문 휴먼명조 9.0pt / 줄간격 130%",
            "fill": "머리글 (#DFE6F7) / 지브라 (#F8FAFC) / 합계 (#ECEEF2)"
        },
        "units": {
            "row": {"count": 3, "min": 1, "max": 30, "core": 1, "sep": 0},
            "col": None
        },
        "_plan": {
            "row": {"start": 1, "count": 3, "min": 1, "max": 30, "core": 1, "sep": 0},
            "col": None
        },
        "sample_rows": [
            ["구 분", "기존 방식 (수작업)", "개선 방안 (AutoDocFit)", "개선 효과"],
            ["서식 정렬", "실무자가 수작업 셀 여백 및 너비 조정", "룰 기반 원클릭 자동 피팅 및 정렬", "시간 85% 단축"],
            ["규격 검증", "인쇄 후 눈대중 및 수기 육안 검토", "공공 편람 룰셋 기반 자동 오류 진단", "오류율 0.1% 미만"],
            ["출력 품질", "작성자마다 제각각인 폰트/선 굵기", "표준 프로파일 기반 통일된 품질 보장", "문서 신뢰도 극대화"],
            ["합 계", "3개 영역 수기 검토", "전 영역 지능형 원패스 자동화", "업무 생산성 4.8배"]
        ],
        "borders": {
            "top": {"type": "SOLID", "width": 0.4, "color": "#000000"},
            "bottom": {"type": "SOLID", "width": 0.4, "color": "#000000"},
            "left": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "right": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "header_split": {"type": "DOUBLE_SLIM", "width": 0.5, "color": "#000000"},
            "inner_h": {"type": "SOLID", "width": 0.12, "color": "#E2E8F0"},
            "inner_v": {"type": "SOLID", "width": 0.12, "color": "#E2E8F0"}
        }
    },

    "pub_gantt_timeline": {
        "id": "pub_gantt_timeline",
        "category": CATEGORY_NAME,
        "name": "④ 추진 일정/간트차트형 표",
        "badge": "추진 일정",
        "description": "월별/분기별 타임라인 바 셀 채우기 색상 규격이 적용된 로드맵 표",
        "default_rows": 5,
        "default_cols": 6,
        "header_rows": 1,
        "footer_rows": 0,
        "line_spacing": 130,
        "char_spacing": 0,
        "col_ratios": [0.24, 0.20, 0.14, 0.14, 0.14, 0.14],
        "margins_hwpunit": {"left": 283, "right": 283, "top": 283, "bottom": 283},
        "guideline": {
            "margins": "좌우 1.0mm / 상하 1.0mm (타임라인 밀착)",
            "borders": "상단 0.4mm, 머리글 이중선 0.5mm, 타임라인 내부 점선(DOT)",
            "font": "한컴돋움 9.0~9.5pt / 줄간격 130% / 가운데 정렬",
            "fill": "머리글 (#E7EEF8) / 추진바 (#1A365D, 폰트 흰색)"
        },
        "units": {
            "row": {"count": 4, "min": 1, "max": 30, "core": 1, "sep": 0},
            "col": {"count": 4, "min": 2, "max": 12, "core": 1, "sep": 0}
        },
        "_plan": {
            "row": {"start": 1, "count": 4, "min": 1, "max": 30, "core": 1, "sep": 0},
            "col": {"start": 2, "count": 4, "min": 2, "max": 12, "core": 1, "sep": 0}
        },
        "sample_rows": [
            ["주요 과제", "세부 내역", "1분기", "2분기", "3분기", "4분기"],
            ["기획 및 분석", "요구사항 도출 및 표준 수립", "■", "", "", ""],
            ["엔진 개발", "HWPX 파서 및 빌더 최적화", "", "■", "■", ""],
            ["UI/UX 구현", "Flutter 표그림판 고도화", "", "", "■", ""],
            ["시범 운영", "중앙부처 시범 적용 및 검증", "", "", "", "▶ 완료"]
        ],
        "borders": {
            "top": {"type": "SOLID", "width": 0.4, "color": "#000000"},
            "bottom": {"type": "SOLID", "width": 0.4, "color": "#000000"},
            "left": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "right": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "header_split": {"type": "DOUBLE_SLIM", "width": 0.5, "color": "#000000"},
            "inner_h": {"type": "SOLID", "width": 0.12, "color": "#E2E8F0"},
            "inner_v": {"type": "DOT", "width": 0.12, "color": "#CBD5E1"}
        }
    },

    "pub_budget_breakdown": {
        "id": "pub_budget_breakdown",
        "category": CATEGORY_NAME,
        "name": "⑤ 예산/소요비용 산출 내역 표",
        "badge": "재정·회계 서식",
        "description": "금액 우측정렬, 3자리 콤마, 하단 합계 이중선 마감의 표준 예산 표",
        "default_rows": 5,
        "default_cols": 5,
        "header_rows": 1,
        "footer_rows": 1,
        "line_spacing": 130,
        "char_spacing": 0,
        "col_ratios": [0.18, 0.32, 0.16, 0.14, 0.20],
        "margins_hwpunit": {"left": 708, "right": 708, "top": 340, "bottom": 340},
        "guideline": {
            "margins": "좌우 2.5mm / 상하 1.2mm",
            "borders": "상단 0.4mm, 머리글 이중선 0.5mm, 하단 합계 이중선 0.5mm",
            "font": "비목 휴먼명조 9.0pt / 수치 맑은 고딕 9.0pt 우측정렬 / 합계 한컴돋움 Bold / 줄간격 130%",
            "fill": "머리글 (#F2F4F7) / 합계행 (#E2E8F0)"
        },
        "units": {
            "row": {"count": 3, "min": 1, "max": 30, "core": 1, "sep": 0},
            "col": None
        },
        "_plan": {
            "row": {"start": 1, "count": 3, "min": 1, "max": 30, "core": 1, "sep": 0},
            "col": None
        },
        "sample_rows": [
            ["비 목", "산출 내역", "단 가", "수량", "금 액"],
            ["연구개발비", "전문 연구원 인건비 (3명 × 6개월)", "4,500,000", "18", "81,000,000"],
            ["서버인프라", "클라우드 분산 연산 인스턴스", "1,200,000", "12", "14,400,000"],
            ["자문회의비", "서식 표준화 전문가 위원 자문", "200,000", "25", "5,000,000"],
            ["합 계", "총 3개 비목 소요 예산 총액", "-", "-", "100,400,000"]
        ],
        "borders": {
            "top": {"type": "SOLID", "width": 0.4, "color": "#000000"},
            "bottom": {"type": "DOUBLE_SLIM", "width": 0.5, "color": "#000000"},
            "left": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "right": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "header_split": {"type": "DOUBLE_SLIM", "width": 0.5, "color": "#000000"},
            "inner_h": {"type": "SOLID", "width": 0.12, "color": "#E2E8F0"},
            "inner_v": {"type": "SOLID", "width": 0.12, "color": "#E2E8F0"}
        }
    },

    "pub_qa_checklist": {
        "id": "pub_qa_checklist",
        "category": CATEGORY_NAME,
        "name": "⑥ 질의응답(Q&A) / 체크리스트 표",
        "badge": "감사·점검",
        "description": "문항 No, 점검 기준, 적합/부적합 판정 뱃지가 구비된 감사/진단용 표",
        "default_rows": 4,
        "default_cols": 4,
        "header_rows": 1,
        "footer_rows": 0,
        "line_spacing": 130,
        "char_spacing": 0,
        "col_ratios": [0.12, 0.48, 0.22, 0.18],
        "margins_hwpunit": {"left": 708, "right": 708, "top": 340, "bottom": 340},
        "guideline": {
            "margins": "좌우 2.5mm / 상하 1.2mm",
            "borders": "상단 0.4mm, 머리글 이중선 0.5mm, 하단 0.4mm, 좌우 개방",
            "font": "한컴돋움 9.0~9.5pt / 줄간격 130% / 판정 뱃지 폰트 색상 매칭",
            "fill": "머리글 (#F0F4F8) / 적합 (#E6F4EA, 녹색) / 주의 (#FCE8E6, 적색)"
        },
        "units": {
            "row": {"count": 3, "min": 1, "max": 30, "core": 1, "sep": 0},
            "col": None
        },
        "_plan": {
            "row": {"start": 1, "count": 3, "min": 1, "max": 30, "core": 1, "sep": 0},
            "col": None
        },
        "sample_rows": [
            ["연번", "점검 및 진단 항목", "점검 기준", "판정 결과"],
            ["01", "행안부 F7 편집용지 여백 기준 준수 여부", "상30/하15/좌20/우20mm 일치", "적 합 (☑)"],
            ["02", "표 내부 머리글 하단 이중실선 규격 적용", "이중선 0.5mm 정상 조판 여부", "적 합 (☑)"],
            ["03", "금액 항목 천 단위 구분 콤마 및 우측정렬", "수치 데이터 우측 밀착 정렬", "보완 요망"]
        ],
        "borders": {
            "top": {"type": "SOLID", "width": 0.4, "color": "#000000"},
            "bottom": {"type": "SOLID", "width": 0.4, "color": "#000000"},
            "left": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "right": {"type": "NONE", "width": 0.1, "color": "#000000"},
            "header_split": {"type": "DOUBLE_SLIM", "width": 0.5, "color": "#000000"},
            "inner_h": {"type": "SOLID", "width": 0.12, "color": "#E2E8F0"},
            "inner_v": {"type": "SOLID", "width": 0.12, "color": "#E2E8F0"}
        }
    }
}


def get_public_preset_descriptors() -> list[dict[str, Any]]:
    """TableUnitsScreen 및 describe_units()가 인식하는 템플릿 정보 목록을 깊은 복사로 반환한다."""
    descriptors = []
    for pid, p in PUBLIC_TABLE_PRESETS.items():
        units_desc = {}
        for axis, u in p["units"].items():
            if u:
                units_desc[axis] = {
                    k: u[k]
                    for k in ("count", "min", "max", "core", "sep")
                    if k in u
                }
            else:
                units_desc[axis] = None
        descriptors.append({
            "id": pid,
            "category": p["category"],
            "name": p["name"],
            "badge": p.get("badge", ""),
            "description": p.get("description", ""),
            "guideline": copy.deepcopy(p.get("guideline", {})),
            "rows": p["default_rows"],
            "cols": p["default_cols"],
            "units": units_desc,
        })
    return copy.deepcopy(descriptors)


def is_public_preset(template_id: str) -> bool:
    """정확히 등록된 공공 프리셋 ID인지 여부를 반환한다."""
    return template_id in PUBLIC_TABLE_PRESETS


def get_public_preset(template_id: str) -> dict[str, Any] | None:
    """공공 프리셋 원본 사본을 반환한다."""
    preset = PUBLIC_TABLE_PRESETS.get(template_id)
    return copy.deepcopy(preset) if preset is not None else None


def public_preset_plan(preset_id: str) -> dict[str, Any]:
    """공공 프리셋의 내부 반복 조절 계획(start 포함)을 반환한다."""
    preset = PUBLIC_TABLE_PRESETS.get(preset_id)
    if not preset:
        raise ValueError(f"Unknown preset ID: {preset_id}")
    return copy.deepcopy(preset["_plan"])


def _default_base_path() -> Path:
    return Path(__file__).resolve().parents[1] / "resources" / "서식예시" / "기본 서식.hwpx"


def _validate_preset_counts(preset: dict[str, Any], row_count: int | None, col_count: int | None) -> tuple[int | None, int | None]:
    plan = preset["_plan"]
    for axis, val in (("row", row_count), ("col", col_count)):
        axis_plan = plan.get(axis)
        if axis_plan is None:
            if val is not None:
                raise ValueError(f"고정 축({axis})에 정보단위 개수를 지정할 수 없습니다.")
        else:
            if val is not None:
                if type(val) is not int:
                    raise ValueError(f"정보단위 개수는 정수여야 합니다: {val}")
                if not axis_plan["min"] <= val <= axis_plan["max"]:
                    raise ValueError(f"정보단위 개수({val})가 허용 범위({axis_plan['min']}~{axis_plan['max']})를 벗어났습니다.")
    return row_count, col_count


def _public_para(pool: table_builder._Header, align: str, line_spacing: int, cache: dict[tuple[str, int], str]) -> str:
    key = (align, line_spacing)
    if key in cache:
        return cache[key]
    source = next(x for x in pool.groups["paraProperties"] if x.get("id") == "0")
    clone = copy.deepcopy(source)
    align_el = table_builder._child(clone, "align")
    if align_el is not None:
        align_el.set("horizontal", align)
    for line in (x for x in clone.iter() if table_builder._tag(x) == "lineSpacing"):
        if line.get("type") == "PERCENT":
            line.set("value", str(line_spacing))
    pid = pool._append("paraProperties", clone)
    cache[key] = pid
    return pid


def _resolve_cell_style(preset_id: str, r: int, c: int, rows: int, cols: int, text: str) -> tuple[dict[str, Any], str]:
    """공공 표준 규칙에 따라 셀 글꼴, 크기, 굵기, 색상, 채우기, 정렬을 결정한다."""
    if preset_id == "pub_summary_headline":
        return {
            "font": "한컴돋움",
            "size": 10.5,
            "bold": False,
            "color": "#1A202C",
            "fill": "#EBF3FA"
        }, "LEFT"

    elif preset_id == "pub_two_col_definition":
        if c == 0:
            return {
                "font": "한컴돋움",
                "size": 9.5,
                "bold": True,
                "color": "#000000",
                "fill": "#F2F4F7"
            }, "CENTER"
        else:
            return {
                "font": "휴먼명조",
                "size": 9.5,
                "bold": False,
                "color": "#000000",
                "fill": "#FFFFFF"
            }, "LEFT"

    elif preset_id == "pub_multi_col_comparison":
        if r == 0:
            return {
                "font": "한컴돋움",
                "size": 9.5,
                "bold": True,
                "color": "#000000",
                "fill": "#DFE6F7"
            }, "CENTER"
        elif r == rows - 1 and rows > 2:
            return {
                "font": "한컴돋움",
                "size": 9.5,
                "bold": True,
                "color": "#000000",
                "fill": "#ECEEF2"
            }, "CENTER"
        else:
            fill = "#FFFFFF" if r % 2 == 1 else "#F8FAFC"
            return {
                "font": "휴먼명조",
                "size": 9.0,
                "bold": False,
                "color": "#000000",
                "fill": fill
            }, "CENTER" if c == 0 or c == cols - 1 else "LEFT"

    elif preset_id == "pub_gantt_timeline":
        if r == 0:
            return {
                "font": "한컴돋움",
                "size": 9.5,
                "bold": True,
                "color": "#000000",
                "fill": "#E7EEF8"
            }, "CENTER"
        elif c >= 2:
            if "■" in text:
                return {
                    "font": "한컴돋움",
                    "size": 9.0,
                    "bold": True,
                    "color": "#FFFFFF",
                    "fill": "#1A365D"
                }, "CENTER"
            elif "▶" in text:
                return {
                    "font": "한컴돋움",
                    "size": 9.0,
                    "bold": True,
                    "color": "#1A365D",
                    "fill": "#94BBE9"
                }, "CENTER"
            else:
                return {
                    "font": "한컴돋움",
                    "size": 9.0,
                    "bold": False,
                    "color": "#000000",
                    "fill": "#FFFFFF"
                }, "CENTER"
        else:
            return {
                "font": "한컴돋움",
                "size": 9.0,
                "bold": False,
                "color": "#000000",
                "fill": "#FFFFFF"
            }, "LEFT"

    elif preset_id == "pub_budget_breakdown":
        if r == 0:
            return {
                "font": "한컴돋움",
                "size": 9.5,
                "bold": True,
                "color": "#000000",
                "fill": "#F2F4F7"
            }, "CENTER"
        elif r == rows - 1 and rows > 2:
            return {
                "font": "한컴돋움",
                "size": 9.5,
                "bold": True,
                "color": "#000000",
                "fill": "#E2E8F0"
            }, "RIGHT" if c >= 2 else "CENTER"
        else:
            if c >= 2:
                return {
                    "font": "맑은 고딕",
                    "size": 9.0,
                    "bold": False,
                    "color": "#000000",
                    "fill": "#FFFFFF"
                }, "RIGHT"
            else:
                return {
                    "font": "휴먼명조",
                    "size": 9.0,
                    "bold": False,
                    "color": "#000000",
                    "fill": "#FFFFFF"
                }, "CENTER" if c == 0 else "LEFT"

    elif preset_id == "pub_qa_checklist":
        if r == 0:
            return {
                "font": "한컴돋움",
                "size": 9.5,
                "bold": True,
                "color": "#000000",
                "fill": "#F0F4F8"
            }, "CENTER"
        elif c == cols - 1:
            stripped = text.strip()
            if stripped in ("적 합 (☑)", "적합", "☑", "Pass"):
                return {
                    "font": "한컴돋움",
                    "size": 9.0,
                    "bold": True,
                    "color": "#188038",
                    "fill": "#E6F4EA"
                }, "CENTER"
            elif stripped in ("보완 요망", "부적합", "부적 합"):
                return {
                    "font": "한컴돋움",
                    "size": 9.0,
                    "bold": True,
                    "color": "#D93025",
                    "fill": "#FCE8E6"
                }, "CENTER"
            else:
                return {
                    "font": "한컴돋움",
                    "size": 9.0,
                    "bold": False,
                    "color": "#000000",
                    "fill": "#FFFFFF"
                }, "CENTER"
        elif c == 0:
            return {
                "font": "한컴돋움",
                "size": 9.5,
                "bold": True,
                "color": "#1A365D",
                "fill": "#FFFFFF"
            }, "CENTER"
        else:
            return {
                "font": "휴먼명조",
                "size": 9.0,
                "bold": False,
                "color": "#000000",
                "fill": "#FFFFFF"
            }, "LEFT"

    return {
        "font": "한컴돋움",
        "size": 9.5,
        "bold": False,
        "color": "#000000",
        "fill": "#FFFFFF"
    }, "CENTER"


def _resolve_cell_borders(preset: dict[str, Any], r: int, c: int, rows: int, cols: int) -> dict[str, Any]:
    borders = preset["borders"]
    header_rows = preset.get("header_rows", 0)
    top_def = borders.get("top", {"type": "SOLID", "width": 0.4, "color": "#000000"})
    bottom_def = borders.get("bottom", {"type": "SOLID", "width": 0.4, "color": "#000000"})
    left_def = borders.get("left", {"type": "NONE", "width": 0.1, "color": "#000000"})
    right_def = borders.get("right", {"type": "NONE", "width": 0.1, "color": "#000000"})
    header_split = borders.get("header_split")
    inner_h = borders.get("inner_h", {"type": "SOLID", "width": 0.12, "color": "#E2E8F0"})
    inner_v = borders.get("inner_v", {"type": "SOLID", "width": 0.12, "color": "#CBD5E1"})

    # 위쪽 테두리
    if r == 0:
        b_top = dict(top_def)
    elif r == header_rows and header_split:
        b_top = dict(header_split)
    else:
        b_top = dict(inner_h)

    # 아래쪽 테두리
    if r == rows - 1:
        b_bottom = dict(bottom_def)
    elif r == header_rows - 1 and header_split:
        b_bottom = dict(header_split)
    else:
        b_bottom = dict(inner_h)

    # 왼쪽/오른쪽 테두리
    is_gantt = (preset["id"] == "pub_gantt_timeline")
    if is_gantt:
        solid_line = {"type": "SOLID", "width": 0.12, "color": "#CBD5E1"}
        dot_line = {"type": "DOT", "width": 0.12, "color": "#CBD5E1"}
        # 왼쪽
        if c == 0:
            b_left = dict(left_def)
        elif c <= 2:
            b_left = dict(solid_line)
        else:
            b_left = dict(dot_line)
        # 오른쪽
        if c == cols - 1:
            b_right = dict(right_def)
        elif c < 2:
            b_right = dict(solid_line)
        else:
            b_right = dict(dot_line)
    else:
        if c == 0:
            b_left = dict(left_def)
        else:
            b_left = dict(inner_v)

        if c == cols - 1:
            b_right = dict(right_def)
        else:
            b_right = dict(inner_v)

    return {
        "top": b_top,
        "bottom": b_bottom,
        "left": b_left,
        "right": b_right,
    }


def _apply_public_style(table: ET.Element, header: ET.Element, preset: dict[str, Any], body_width: int) -> None:
    pool = table_builder._Header(header)
    preset_id = preset["id"]
    rows = int(table.get("rowCnt"))
    cols = int(table.get("colCnt"))
    margins_hwpunit = preset["margins_hwpunit"]
    header_rows = preset.get("header_rows", 0)
    line_spacing = preset.get("line_spacing", 130)
    char_spacing = preset.get("char_spacing", 0)

    # 열 너비 정수 분배 (합계 = body_width 정확히 일치)
    if preset_id == "pub_gantt_timeline":
        period_cols = max(1, cols - 2)
        ratios = [0.24, 0.20] + [0.56 / period_cols] * period_cols
    else:
        ratios = preset.get("col_ratios", [1.0 / cols] * cols)
        if len(ratios) < cols:
            ratios = ratios + [1.0 / cols] * (cols - len(ratios))
        elif len(ratios) > cols:
            ratios = ratios[:cols]

    total_ratio = sum(ratios)
    col_widths = []
    prev_cum = 0
    for i in range(cols):
        if i == cols - 1:
            col_widths.append(body_width - sum(col_widths))
        else:
            cum = int(round(body_width * sum(ratios[:i + 1]) / total_ratio))
            col_widths.append(cum - prev_cum)
            prev_cum = cum

    sz = table.find(table_units.HP + "sz")
    if sz is not None:
        sz.set("width", str(body_width))

    inMargin = table.find(table_units.HP + "inMargin")
    if inMargin is not None:
        inMargin.attrib.update({
            "left": str(margins_hwpunit["left"]),
            "right": str(margins_hwpunit["right"]),
            "top": str(margins_hwpunit["top"]),
            "bottom": str(margins_hwpunit["bottom"])
        })

    para_cache: dict[tuple[str, int], str] = {}

    for r_idx, tr in enumerate(table.findall(table_units.HP + "tr")):
        for tc in tr.findall(table_units.HP + "tc"):
            addr = tc.find(table_units.HP + "cellAddr")
            c_idx = int(addr.get("colAddr")) if addr is not None else 0
            span = tc.find(table_units.HP + "cellSpan")
            col_span = int(span.get("colSpan")) if span is not None else 1

            # 셀 폭 설정
            cell_sz = tc.find(table_units.HP + "cellSz")
            if cell_sz is not None:
                w = sum(col_widths[c_idx:c_idx + col_span])
                cell_sz.set("width", str(w))

            # 셀 여백 설정
            tc.set("hasMargin", "1")
            cell_margin = tc.find(table_units.HP + "cellMargin")
            if cell_margin is None:
                cell_margin = table_builder._element(tc, "cellMargin")
            cell_margin.attrib.update({
                "left": str(margins_hwpunit["left"]),
                "right": str(margins_hwpunit["right"]),
                "top": str(margins_hwpunit["top"]),
                "bottom": str(margins_hwpunit["bottom"])
            })

            # 머리글 여부
            tc.set("header", "1" if r_idx < header_rows else "0")

            # 텍스트 추출
            text_nodes = catalog._cell_text_nodes(tc)
            text = " ".join("".join(n.text or "" for n in text_nodes).split())

            # 스타일 및 정렬
            style, align = _resolve_cell_style(preset_id, r_idx, c_idx, rows, cols, text)

            # 테두리
            cell_borders = _resolve_cell_borders(preset, r_idx, c_idx, rows, cols)
            border_sides = {
                side: (cell_borders[side]["type"], f"{cell_borders[side]['width']} mm", cell_borders[side]["color"])
                for side in ("top", "bottom", "left", "right")
            }
            border_id = pool.border(border_sides, fill=style.get("fill", ""))
            tc.set("borderFillIDRef", str(border_id))

            # 문단 모양 및 글자 모양 적용
            para_id = _public_para(pool, align, line_spacing, para_cache)
            char_id = pool.char(style, spacing=char_spacing)

            for p in tc.iter(table_units.HP + "p"):
                p.set("paraPrIDRef", str(para_id))
                for run in p.findall(table_units.HP + "run"):
                    run.set("charPrIDRef", str(char_id))
                for cache in p.findall(table_units.HP + "linesegarray"):
                    p.remove(cache)


def _build_public_document(
    preset_id: str,
    row_count: int | None,
    col_count: int | None,
    *,
    fill: str,
    cell_texts: dict[str, str] | None
) -> tuple[dict[str, bytes], ET.Element, ET.Element]:
    """공통 HWPX 문서 빌드 엔진.

    반환: (contents bytes dict, section0 table Element, header Element)
    """
    preset = PUBLIC_TABLE_PRESETS.get(preset_id)
    if not preset:
        raise ValueError(f"Unknown preset ID: {preset_id}")

    table_units.validate_input(fill, cell_texts)
    _validate_preset_counts(preset, row_count, col_count)

    base_path = _default_base_path()
    if not base_path.is_file():
        raise OSError(f"내장 기본 서식 파일을 찾을 수 없습니다: {base_path}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_hwpx = Path(temp_dir) / "base_grid.hwpx"
        spec = {
            "kind": "grid",
            "rows": copy.deepcopy(preset["sample_rows"]),
            "header_rows": preset["header_rows"],
            "use_basic_style": False,
            "styles": {},
            "borders": {}
        }
        table_builder.build_table_hwpx(spec, base_path, temp_hwpx, basic_style=None)

        with open_hwpx_safely(temp_hwpx) as z:
            contents = {info.filename: z.read(info.filename) for info in z.infolist()}

    sections = sorted(n for n in contents if re.fullmatch(r"Contents/section\d+\.xml", n))
    if len(sections) != 1 or "Contents/header.xml" not in contents:
        raise ValueError("내장 바탕 문서의 섹션 구조가 단일 section이 아닙니다.")

    header_bytes = contents["Contents/header.xml"]
    section_bytes = contents[sections[0]]
    header = ET.fromstring(header_bytes)
    section0 = ET.fromstring(section_bytes)

    tables = section0.findall(f".//{table_units.HP}tbl")
    if not tables:
        raise ValueError("표 요소를 찾을 수 없습니다.")
    table = tables[0]

    plan = public_preset_plan(preset_id)
    table_units.resize_table(
        table,
        plan,
        row_count=row_count,
        col_count=col_count,
        id_roots=(header, section0),
        fill=fill,
        cell_texts=cell_texts
    )

    page_pr = next(x for x in section0.iter() if table_builder._tag(x) == "pagePr")
    margin_el = table_builder._child(page_pr, "margin")
    body_width = int(page_pr.get("width")) - int(margin_el.get("left")) - int(margin_el.get("right"))

    _apply_public_style(table, header, preset, body_width)

    # PrvImage 제거 (기존 문서 썸네일 방지)
    if "Preview/PrvImage.png" in contents:
        contents.pop("Preview/PrvImage.png")

    # PrvText 재생성
    all_texts = []
    for tc in table.findall(f".//{table_units.HP}tc"):
        txt = " ".join("".join(n.text or "" for n in catalog._cell_text_nodes(tc)).split())
        if txt:
            all_texts.append(txt)
    contents["Preview/PrvText.txt"] = "\n".join(all_texts).encode("utf-8")

    contents["Contents/header.xml"] = table_builder._serialize(header, header_bytes)
    contents[sections[0]] = table_builder._serialize(section0, section_bytes)

    return contents, table, header


def _write_public_package(contents: dict[str, bytes], target: Path) -> Path:
    target = Path(target)
    base_path = _default_base_path()
    try:
        if target.resolve() == base_path.resolve() or (target.exists() and os.path.samefile(target, base_path)):
            raise ValueError("내장 바탕 원본 문서를 출력 대상으로 덮어쓸 수 없습니다.")
    except (FileNotFoundError, OSError):
        pass

    target.parent.mkdir(parents=True, exist_ok=True)
    temp_file = target.with_name(target.name + f".tmp_{os.getpid()}")

    try:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as out:
            if "mimetype" in contents:
                out.writestr("mimetype", contents["mimetype"], compress_type=zipfile.ZIP_STORED)
            for name, data in contents.items():
                if name != "mimetype":
                    out.writestr(name, data)
        temp_file.write_bytes(buffer.getvalue())

        # 임시 파일 무결성 및 구조 재검증
        with open_hwpx_safely(temp_file) as check_z:
            c_sec = check_z.read("Contents/section0.xml")
            c_hdr = check_z.read("Contents/header.xml")
            s_elem = ET.fromstring(c_sec)
            h_elem = ET.fromstring(c_hdr)
            tb_list = s_elem.findall(f".//{table_units.HP}tbl")
            if len(tb_list) != 1:
                raise ValueError("최상위 표가 정확히 1개가 아닙니다.")
            # 스타일 참조 유효성 검사
            bf_ids = {x.get("id") for x in h_elem.iter() if table_builder._tag(x) == "borderFill"}
            for tc in tb_list[0].findall(f".//{table_units.HP}tc"):
                bf_ref = tc.get("borderFillIDRef")
                if bf_ref is not None and bf_ref not in bf_ids:
                    raise ValueError(f"유효하지 않은 borderFillIDRef 참조: {bf_ref}")

        temp_file.replace(target)
        return target
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass


def preview_public_preset(
    preset_id: str,
    row_count: int | None = None,
    col_count: int | None = None,
    *,
    fill: str = "increment",
    cell_texts: dict[str, str] | None = None
) -> dict[str, Any]:
    """공공 프리셋의 조판 완료 미리보기 데이터를 반환한다."""
    preset = PUBLIC_TABLE_PRESETS.get(preset_id)
    if not preset:
        raise ValueError(f"Unknown preset ID: {preset_id}")

    _, table, header = _build_public_document(
        preset_id,
        row_count=row_count,
        col_count=col_count,
        fill=fill,
        cell_texts=cell_texts
    )

    rows = int(table.get("rowCnt"))
    cols = int(table.get("colCnt"))
    header_info = catalog._header_lookup(header)

    result = {
        "id": preset_id,
        "name": preset["name"],
        "rows": rows,
        "cols": cols,
        "cells": [],
        "cell_meta": [],
        "guideline": copy.deepcopy(preset["guideline"]),
    }

    for i, row in enumerate(table.findall(table_units.HP + "tr")):
        row_texts, row_meta = [], []
        for j, cell in enumerate(row.findall(table_units.HP + "tc")):
            text = " ".join("".join(n.text or "" for n in catalog._cell_text_nodes(cell)).split())[:80]
            row_texts.append(text)
            item = catalog._cell_meta(cell, i, j, text, header_info)
            row_meta.append(item)
        result["cells"].append(row_texts)
        result["cell_meta"].append(row_meta)

    return result


def export_public_preset(
    preset_id: str,
    output_path: str | Path,
    row_count: int | None = None,
    col_count: int | None = None,
    *,
    fill: str = "increment",
    cell_texts: dict[str, str] | None = None
) -> Path:
    """공공 프리셋을 HWPX 파일로 내보낸다."""
    contents, _, _ = _build_public_document(
        preset_id,
        row_count=row_count,
        col_count=col_count,
        fill=fill,
        cell_texts=cell_texts
    )
    return _write_public_package(contents, Path(output_path))


def public_preset_snapshot_key(preset_id: str) -> str:
    """공공 프리셋 기본 표의 결정론적 스냅샷 키(20자리 hex)를 계산한다."""
    if not is_public_preset(preset_id):
        raise ValueError(f"Unknown preset ID: {preset_id}")

    base_path = _default_base_path()
    if not base_path.is_file():
        raise OSError(f"내장 기본 서식을 읽을 수 없습니다: {base_path}")

    contents, table, header = _build_public_document(
        preset_id,
        row_count=None,
        col_count=None,
        fill="increment",
        cell_texts=None
    )

    section0 = ET.fromstring(contents[sorted(n for n in contents if re.fullmatch(r"Contents/section\d+\.xml", n))[0]])
    page_pr = next(x for x in section0.iter() if table_builder._tag(x) == "pagePr")

    digest = hashlib.sha256(PUBLIC_PRESET_REVISION.encode("utf-8"))
    digest.update(preset_id.encode("utf-8"))

    # pagePr 반영
    digest.update(repr((page_pr.tag, sorted(page_pr.attrib.items()))).encode("utf-8"))

    # header 요소 순회
    for elem in header.iter():
        digest.update(repr((elem.tag, sorted(elem.attrib.items()), elem.text or "", elem.tail or "")).encode("utf-8"))

    # table 요소 순회
    for elem in table.iter():
        digest.update(repr((elem.tag, sorted(elem.attrib.items()), elem.text or "", elem.tail or "")).encode("utf-8"))

    return digest.hexdigest()[:20]


def build_public_preset_preview(
    preset_id: str,
    target_rows: int | None = None,
    target_cols: int | None = None,
    cell_texts: dict[str, str] | None = None
) -> dict[str, Any]:
    """초안 호환용 래퍼: 실제 물리적 격자 크기(target_rows, target_cols)를 단위 count로 변환하여 위임한다."""
    preset = PUBLIC_TABLE_PRESETS.get(preset_id)
    if not preset:
        raise ValueError(f"Unknown preset ID: {preset_id}")

    if target_rows is not None and (type(target_rows) is not int or target_rows <= 0):
        raise ValueError(f"target_rows는 양의 정수여야 합니다: {target_rows}")
    if target_cols is not None and (type(target_cols) is not int or target_cols <= 0):
        raise ValueError(f"target_cols는 양의 정수여야 합니다: {target_cols}")

    plan = preset["_plan"]

    # 행 단위 count 계산
    row_count = None
    if plan["row"] is None:
        if target_rows is not None and target_rows != preset["default_rows"]:
            raise ValueError(f"고정 행 표는 기본 크기({preset['default_rows']}) 외의 크기로 변경할 수 없습니다.")
    else:
        if target_rows is not None:
            fixed_rows = preset.get("header_rows", 0) + preset.get("footer_rows", 0)
            row_count = target_rows - fixed_rows
            if row_count < 1:
                raise ValueError(f"target_rows({target_rows})가 고정 행 수({fixed_rows})보다 커야 합니다.")

    # 열 단위 count 계산
    col_count = None
    if plan["col"] is None:
        if target_cols is not None and target_cols != preset["default_cols"]:
            raise ValueError(f"고정 열 표는 기본 크기({preset['default_cols']}) 외의 크기로 변경할 수 없습니다.")
    else:
        if target_cols is not None:
            fixed_cols = plan["col"]["start"]
            col_count = target_cols - fixed_cols
            if col_count < 1:
                raise ValueError(f"target_cols({target_cols})가 고정 열 수({fixed_cols})보다 커야 합니다.")

    return preview_public_preset(
        preset_id,
        row_count=row_count,
        col_count=col_count,
        fill="increment",
        cell_texts=cell_texts
    )
