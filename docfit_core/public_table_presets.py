"""공공기관·비즈니스 6대 표준 표 템플릿 프리셋 엔진 (2.0.0-alpha.1).
행정업무운영편람 및 기획재정부 보고서 표준 지침에 맞춘 조판 메트릭스, 셀 메타, HWPX 생성 자립 모듈.
"""

from __future__ import annotations

import copy
import re
from typing import Any

CATEGORY_NAME = "공공 표준"

# 6대 공공 표준 프리셋 정의
PUBLIC_TABLE_PRESETS: dict[str, dict[str, Any]] = {
    "pub_summary_headline": {
        "id": "pub_summary_headline",
        "category": CATEGORY_NAME,
        "name": "① 요약/헤드라인 1칸 표",
        "badge": "행안부 권장",
        "description": "상하 0.4mm 굵은선, 좌우 개방형, 연청색 음영의 핵심 요약 콜아웃 상자",
        "default_rows": 1,
        "default_cols": 1,
        "col_ratios": [1.0],
        "margins_hwpunit": {"left": 1134, "right": 1134, "top": 708, "bottom": 708},
        "guideline": {
            "margins": "좌우 4.0mm / 상하 2.5mm",
            "borders": "상하 실선 0.4mm (#1A365D), 좌우 선없음",
            "font": "한컴돋움 10.5pt / 줄간격 140% / 자간 -5%",
            "fill": "소프트블루 (#EBF3FA, 12%)"
        },
        "units": {
            "row": {"count": 1, "min": 1, "max": 10, "core": 1, "sep": 0},
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
        "badge": "공공 개요 기본",
        "description": "좌측 항목 22% 연회색 음영, 우측 세부내용 78% 정렬의 표준 개요 양식",
        "default_rows": 4,
        "default_cols": 2,
        "col_ratios": [0.22, 0.78],
        "margins_hwpunit": {"left": 708, "right": 708, "top": 340, "bottom": 340},
        "guideline": {
            "margins": "좌우 2.5mm / 상하 1.2mm",
            "borders": "상하 0.4mm, 좌우 개방, 내부 0.12mm (#E2E8F0)",
            "font": "항목 한컴돋움 9.5pt Bold / 본문 휴먼명조 9.5pt",
            "fill": "항목열 연회색 (#F2F4F7) / 내용열 흰색"
        },
        "units": {
            "row": {"count": 4, "min": 1, "max": 30, "core": 1, "sep": 0},
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
        "badge": "기재부·행안부 표준",
        "description": "머리글 다크네이비/연청, 본문 지브라 교차 음영, 최하단 합계 행",
        "default_rows": 5,
        "default_cols": 4,
        "col_ratios": [0.18, 0.37, 0.30, 0.15],
        "margins_hwpunit": {"left": 708, "right": 708, "top": 340, "bottom": 340},
        "guideline": {
            "margins": "좌우 2.5mm / 상하 1.2mm",
            "borders": "상단 0.4mm, 머리글하단 이중선 0.5mm, 하단 0.4mm",
            "font": "머리글 돋움 9.5pt Bold / 본문 명조 9.0pt / 줄간격 130%",
            "fill": "머리글 (#DFE6F7) / 지브라 (#F8FAFC) / 합계 (#ECEEF2)"
        },
        "units": {
            "row": {"count": 5, "min": 2, "max": 30, "core": 1, "sep": 0},
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
        "badge": "로드맵 전용",
        "description": "월별/분기별 타임라인 바 셀 채우기 색상 규격이 적용된 로드맵 표",
        "default_rows": 5,
        "default_cols": 6,
        "col_ratios": [0.24, 0.20, 0.14, 0.14, 0.14, 0.14],
        "margins_hwpunit": {"left": 283, "right": 283, "top": 283, "bottom": 283},
        "guideline": {
            "margins": "좌우 1.0mm / 상하 1.0mm (타임라인 밀착)",
            "borders": "상단 0.4mm, 머리글 이중선 0.5mm, 타임라인 내부 점선(DOT)",
            "font": "돋움 9.0~9.5pt / 가운데 정렬",
            "fill": "머리글 (#E7EEF8) / 추진바 (#1A365D, 폰트 흰색)"
        },
        "units": {
            "row": {"count": 5, "min": 2, "max": 30, "core": 1, "sep": 0},
            "col": {"count": 4, "min": 2, "max": 12, "core": 1, "sep": 0}
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
        "col_ratios": [0.18, 0.32, 0.16, 0.14, 0.20],
        "margins_hwpunit": {"left": 708, "right": 708, "top": 340, "bottom": 340},
        "guideline": {
            "margins": "좌우 2.5mm / 상하 1.2mm",
            "borders": "상단 0.4mm, 머리글 이중선 0.5mm, 하단 합계 이중선 0.5mm",
            "font": "비목 명조 9.0pt / 수치 맑은고딕 9.0pt 우측정렬 / 합계 돋움 Bold",
            "fill": "머리글 (#F2F4F7) / 합계행 (#E2E8F0)"
        },
        "units": {
            "row": {"count": 5, "min": 2, "max": 30, "core": 1, "sep": 0},
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
        "badge": "감사·점검 표준",
        "description": "문항 No, 점검 기준, 적합/부적합 판정 뱃지가 구비된 감사/진단용 표",
        "default_rows": 4,
        "default_cols": 4,
        "col_ratios": [0.12, 0.48, 0.22, 0.18],
        "margins_hwpunit": {"left": 708, "right": 708, "top": 340, "bottom": 340},
        "guideline": {
            "margins": "좌우 2.5mm / 상하 1.2mm",
            "borders": "상단 0.4mm, 머리글 이중선 0.5mm, 하단 0.4mm, 좌우 개방",
            "font": "돋움 9.0~9.5pt / 판정 뱃지 폰트 색상 매칭",
            "fill": "머리글 (#F0F4F8) / 적합 (#E6F4EA, 녹색) / 주의 (#FCE8E6, 적색)"
        },
        "units": {
            "row": {"count": 4, "min": 2, "max": 30, "core": 1, "sep": 0},
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
    """TableUnitsScreen 및 describe_units()가 인식하는 템플릿 정보 목록을 반환한다."""
    descriptors = []
    for pid, p in PUBLIC_TABLE_PRESETS.items():
        descriptors.append({
            "id": pid,
            "category": p["category"],
            "name": p["name"],
            "badge": p.get("badge", ""),
            "description": p.get("description", ""),
            "guideline": p.get("guideline", {}),
            "rows": p["default_rows"],
            "cols": p["default_cols"],
            "units": p["units"],
        })
    return descriptors


def is_public_preset(template_id: str) -> bool:
    return template_id in PUBLIC_TABLE_PRESETS


def get_public_preset(template_id: str) -> dict[str, Any] | None:
    return PUBLIC_TABLE_PRESETS.get(template_id)


def build_public_preset_preview(
    preset_id: str,
    target_rows: int | None = None,
    target_cols: int | None = None,
    cell_texts: dict[str, str] | None = None
) -> dict[str, Any]:
    """Flutter TableGridPreview가 요구하는 행렬(cell_meta)을 생성한다."""
    preset = PUBLIC_TABLE_PRESETS.get(preset_id)
    if not preset:
        raise ValueError(f"Unknown preset ID: {preset_id}")

    rows = target_rows if target_rows is not None and target_rows > 0 else preset["default_rows"]
    cols = target_cols if target_cols is not None and target_cols > 0 else preset["default_cols"]

    col_ratios = preset.get("col_ratios", [1.0 / cols] * cols)
    if len(col_ratios) < cols:
        col_ratios = col_ratios + [1.0 / cols] * (cols - len(col_ratios))
    elif len(col_ratios) > cols:
        col_ratios = col_ratios[:cols]

    total_ratio = sum(col_ratios)
    total_table_width = 48000.0  # HWPX 표준 A4 170mm 폭
    col_widths = [max(1000.0, (r / total_ratio) * total_table_width) for r in col_ratios]

    sample_rows = preset.get("sample_rows", [])
    borders = preset.get("borders", {})
    cell_texts = cell_texts or {}

    cell_meta = []
    for r in range(rows):
        row_cells = []
        for c in range(cols):
            # 셀 텍스트 결정
            key = f"{r},{c}"
            if key in cell_texts:
                text = cell_texts[key]
            elif r < len(sample_rows) and c < len(sample_rows[r]):
                text = sample_rows[r][c]
            else:
                text = f"내용 {r+1}-{c+1}"

            # 스타일 및 서식 결정
            style, align = _resolve_cell_style(preset_id, r, c, rows, cols, text)

            # 테두리 결정
            cell_borders = _resolve_cell_borders(borders, r, c, rows, cols)

            row_cells.append({
                "row": r,
                "col": c,
                "rowSpan": 1,
                "colSpan": 1,
                "width": round(col_widths[c], 1),
                "height": 1800.0 if r > 0 else 2200.0,
                "text": text,
                "align": align,
                "style": style,
                "borders": cell_borders,
                "shapes": []
            })
        cell_meta.append(row_cells)

    return {
        "rows": rows,
        "cols": cols,
        "cell_meta": cell_meta,
        "guideline": preset.get("guideline", {})
    }


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
            if "적 합" in text or "☑" in text or "Pass" in text:
                return {
                    "font": "한컴돋움",
                    "size": 9.0,
                    "bold": True,
                    "color": "#188038",
                    "fill": "#E6F4EA"
                }, "CENTER"
            else:
                return {
                    "font": "한컴돋움",
                    "size": 9.0,
                    "bold": True,
                    "color": "#D93025",
                    "fill": "#FCE8E6"
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


def _resolve_cell_borders(borders: dict[str, Any], r: int, c: int, rows: int, cols: int) -> dict[str, Any]:
    """공공 표준 테두리(상단 굵은선, 머리글 이중선, 좌우 개방 등)를 셀별로 계산한다."""
    top_def = borders.get("top", {"type": "SOLID", "width": 0.4, "color": "#000000"})
    bottom_def = borders.get("bottom", {"type": "SOLID", "width": 0.4, "color": "#000000"})
    left_def = borders.get("left", {"type": "NONE", "width": 0.1, "color": "#000000"})
    right_def = borders.get("right", {"type": "NONE", "width": 0.1, "color": "#000000"})
    header_split = borders.get("header_split", {"type": "DOUBLE_SLIM", "width": 0.5, "color": "#000000"})
    inner_h = borders.get("inner_h", {"type": "SOLID", "width": 0.12, "color": "#E2E8F0"})
    inner_v = borders.get("inner_v", {"type": "SOLID", "width": 0.12, "color": "#CBD5E1"})

    # 위쪽 테두리
    if r == 0:
        b_top = dict(top_def)
    elif r == 1 and header_split:
        b_top = dict(header_split)
    else:
        b_top = dict(inner_h)

    # 아래쪽 테두리
    if r == rows - 1:
        b_bottom = dict(bottom_def)
    elif r == 0 and header_split:
        b_bottom = dict(header_split)
    else:
        b_bottom = dict(inner_h)

    # 왼쪽 테두리
    if c == 0:
        b_left = dict(left_def)
    else:
        b_left = dict(inner_v)

    # 오른쪽 테두리
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
