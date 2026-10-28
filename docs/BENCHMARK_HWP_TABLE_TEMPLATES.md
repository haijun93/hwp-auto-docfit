# HWP AutoDocFit 2.0.0 표준 표 템플릿 벤치마킹 및 규격서

- **작성자**: Gemini 3 (한글 표 템플릿 벤치마킹 전문 리서치 워커)
- **검수**: 프로젝트 총괄 매니저 제미나이 1 (Main PC) & 수석 아키텍트 코덱스 (Codex)
- **일자**: 2026-10-28
- **적용 대상**: `flutter_ui/lib/features/table_sketch`, `docfit_core/hwpx/table_builder.py`, `docfit_core/table_style.py`

---

## 1. 개요 및 벤치마킹 목적

공공기관(행정안전부, 기획재정부, 국무조정실 등) 및 대기업 비즈니스 보고서에서 표(Table)는 **"정보의 위계와 결론을 즉시 전달하는 시각적 아키텍처"**입니다. 행정업무운영편람(구 정부보고서 작성 매뉴얼)과 기재부 예산/기획 보고서 가이드라인에 부합하지 않는 표 서식은 가독성을 떨어뜨리고 문서의 신뢰도를 저해합니다.

본 문서는 **HWP AutoDocFit 2.0.0**의 차세대 기능인 **표그림판(`flutter_ui/lib/features/table_sketch`)** 및 **표 단위 서식 엔진(`docfit_core/hwpx`, `table_builder`, `table_style`)**에 기본 탑재할 **공공·비즈니스 6대 표준 표 템플릿**의 물리적 규격, XML 파라미터, 시각적 조판 규칙을 체계화한 규격서입니다.

---

## 2. 공공기관 행정업무운영편람 및 보고서 표준 표 6대 유형 분석

| 번호 | 표 템플릿 유형 | 주 용도 및 배치 맥락 | 핵심 시각 디자인 특징 | 표준 배치 비율 및 행/열 구조 |
| :--- | :--- | :--- | :--- | :--- |
| **①** | **요약/헤드라인 1칸 표** | 보고서 서두의 핵심 결론, 추진 배경 요약, 장관/실국장 보고용 콜아웃 상자 | 상하 0.4mm 굵은 실선, 좌우 선 없음(개방형), 10~15% 연청/연회색 음영 채우기 | 1행 1열 (100% 폭), 상하 여백 넉넉히 부여 |
| **②** | **2열 정의/대비 표** | 사업 개요(명칭, 기간, 주관, 내용), 용어 정의, 기존 vs 개선안 1:1 대비 | 좌측 항목열(20~25%) 음영+볼드, 우측 상세열(75~80%) 흰색바탕+좌측정렬 | N행 2열 (20~25% : 75~80%), 내부 가로 0.12mm |
| **③** | **3~4열 다단 비교/평가 표** | 부처간/방안별 비교 평가, 지표별 달성도, 다각적 대안 검토 | 머리글 음영+볼드, 본문 줄무늬(Zebra striping) 교차 음영, 최하단 합계/평균 행 | N행 3~4열 (구분/대안A/대안B/비고), 머리글 하단 이중선 |
| **④** | **추진 일정/간트차트형 표** | 연간/분기별/월별/주차별 세부 추진 로드맵 및 마일스톤 관리 | 타임라인 열 균등 분할, 추진 구간 셀 채우기(포인트 네이비/블루) 및 심볼(■/▶) 결합 | N행 M열 (과제명 25~30% + 타임라인 균등 분할) |
| **⑤** | **예산/소요비용 산출 내역 표** | 비목별 예산 편성, 사업비 산출 근거, 단가×수량 내역 산출 | 우측 상단 '(단위: 천원)' 명시, 금액 우측정렬+3자리 콤마, 최하단 '합 계' 이중선 마감 | N행 5열 (비목/내역/단가/수량/금액), 최하단 굵은 마감 |
| **⑥** | **질의응답(Q&A) / 체크리스트 표** | 현장 점검표, 적격성 사전 자가진단, 대국민 Q&A 질의응답집 | 아이콘/No 열, 질문(Q) vs 답변(A) 교차 구조, 판정 열(적격/부적격/보완) 뱃지 음영 | N행 4~5열 (No/문항/판정/확인), 체크박스(□, ☑) 지원 |

---

## 3. HWP/HWPX 세부 파라미터 정밀 벤치마킹 및 환산 규격

한글(HWP/HWPX) 조판 단위는 **HWPUnit**을 기준으로 작동합니다.
* **길이 환산**: $1\text{ mm} \approx 283.4646\text{ hwpunit}$, $1\text{ pt} = 100\text{ hwpunit}$
* **A4 기본 여백(행안부 F7 표준)**: 좌 20mm, 우 20mm 기준 **본문 출력 폭 = 170mm (48,189 hwpunit)**

### (1) 셀 내부 여백 (Cell Internal Margins)
* **공공 표준 권장값**: 좌/우 `2.0mm ~ 3.0mm` (567 ~ 850 hwpunit), 상/하 `1.0mm ~ 1.5mm` (283 ~ 425 hwpunit)
* **표 유형별 세부 적용**:
  * **헤드라인 1칸 표**: 좌우 4.0mm (1,134 hwpunit), 상하 2.5mm (708 hwpunit) — 박스 안 텍스트 답답함 방지
  * **일반 데이터 표(2~4열, 예산)**: 좌우 2.5mm (708 hwpunit), 상하 1.2mm (340 hwpunit) — 컴팩트하고 정돈된 밀도
  * **간트차트형 타임라인**: 좌우 1.0mm (283 hwpunit), 상하 1.0mm (283 hwpunit) — 좁은 열 간격 최적화

### (2) 테두리 선 규격 (Border Specifications)
* **HWPX 테두리 타입**: `SOLID`(실선), `DOUBLE_SLIM`(이중 실선), `NONE`(선 없음), `DASH`(파선), `DOT`(점선)
* **테두리 배치 규칙**:
  * **최상단(Top)**: `SOLID` 0.4mm (#000000 또는 부처 메인 컬러)
  * **머리글 하단(Header Split)**: `DOUBLE_SLIM` 0.5mm (#000000) — 행안부 전통 양식의 품격
  * **외곽 좌우(Left / Right)**: `NONE` (개방형 모던 스타일) 또는 `SOLID` 0.12mm (박스형 격자)
  * **내부 가로/세로선(Inner Grid)**: `SOLID` 0.12mm (#000000 또는 연한 그리드 #D1D5DB)
  * **최하단(Bottom)**: `SOLID` 0.4mm 또는 `DOUBLE_SLIM` 0.5mm (합계 마감)

### (3) 셀 채우기 색상 팔레트 (Fill Color Codes)
* **공공 기본 연회색 (Public Gray)**: `#F2F4F7` (머리글 1순위, 10~12% 틴트) / 본문 교차 음영: `#F8FAFC`
* **포인트 네이비 / 블루 (Public Executive Blue)**:
  * 머리글/강조: `#1A365D` (기재부/금융위 보고서 다크 네이비, 폰트 흰색 #FFFFFF 매칭)
  * 연청색 헤더/강조: `#DFE6F7` 또는 `#EBF3FA` (행안부 소프트 블루, 폰트 검정 #000000 매칭)
  * 타임라인 추진 활성 바: `#3182CE` (비비드 블루) 또는 `#7FA8D6` (소프트 블루)
* **경고 / 적격 판정 틴트**:
  * 적격 / 정상(Pass): `#E6F4EA` (소프트 그린)
  * 부적격 / 주의(Alert): `#FCE8E6` (소프트 핑크)

### (4) 글자체 및 크기 / 자간 / 줄간격 (Typography Rules)
* **표준 글꼴**: 한컴돋움, 맑은 고딕 (가독성 높은 고딕계열 표 기본), 휴먼명조 (전통 기안문용)
* **글자 크기**:
  * 머리글(Header): `9.5pt ~ 10.0pt` (950~1000 hwpunit), 볼드(Bold)
  * 본문(Body): `9.0pt ~ 9.5pt` (900~950 hwpunit), 보통(Regular)
  * 요약 상자: `10.5pt ~ 11.0pt`, 볼드/보통 혼합
* **자간(Spacing)**: `-5% ~ -7%` (국문 조판 시 단어 쪼개짐 및 불필요한 줄바꿈 방지 필수)
* **장평(Ratio)**: `95% ~ 100%`
* **줄간격(Line Spacing)**: `130% ~ 140%` (본문 160% 대비 표 내부는 130~140%로 밀도감 부여)

---

## 4. HWP AutoDocFit 2.0 즉시 탑재용 JSON 스키마 프리셋 6종

이 JSON 스키마는 `flutter_ui/lib/features/table_sketch`의 원클릭 프리셋 버튼 및 `docfit_core/hwpx/table_builder.py`의 `normalize()` 및 빌더 입력으로 즉각 호환됩니다.

```json
{
  "$schema": "https://hwpx.autodocfit.io/v2/table_sketch_schema.json",
  "version": "2.0.0",
  "presets": [
    {
      "id": "preset_summary_headline_box",
      "name": "요약/헤드라인 1칸 표",
      "category": "headline",
      "description": "상하 0.4mm 굵은선, 좌우 개방형, 연청색 음영의 핵심 요약 콜아웃 상자",
      "rows": 1,
      "cols": 1,
      "header_rows": 0,
      "col_widths_ratio": [1.0],
      "margins_mm": { "left": 4.0, "right": 4.0, "top": 2.5, "bottom": 2.5 },
      "margins_hwpunit": { "left": 1134, "right": 1134, "top": 708, "bottom": 708 },
      "borders": {
        "outer": {
          "top": { "type": "SOLID", "width": "0.4 mm", "color": "#1A365D" },
          "bottom": { "type": "SOLID", "width": "0.4 mm", "color": "#1A365D" },
          "left": { "type": "NONE", "width": "0.1 mm", "color": "#000000" },
          "right": { "type": "NONE", "width": "0.1 mm", "color": "#000000" }
        },
        "inner": {
          "horizontal": { "type": "NONE", "width": "0.1 mm", "color": "#000000" },
          "vertical": { "type": "NONE", "width": "0.1 mm", "color": "#000000" }
        }
      },
      "styles": {
        "headline": {
          "font": "한컴돋움",
          "size": 10.5,
          "bold": false,
          "color": "#1A202C",
          "fill": "#EBF3FA",
          "align": "LEFT",
          "letter_spacing": -5,
          "line_spacing": 140
        }
      },
      "sample_content": [
        ["◈ [핵심 요약] 본 사업은 차세대 공공 서식 자동화 표준을 확립하고, 부처 간 문서 정합성을 99.8% 수준으로 제고하기 위해 추진됨."]
      ]
    },
    {
      "id": "preset_two_column_definition",
      "name": "2열 정의/대비 표",
      "category": "definition",
      "description": "좌측 항목 22% 연회색 음영, 우측 세부내용 78% 정렬의 표준 개요 양식",
      "rows": 4,
      "cols": 2,
      "header_rows": 0,
      "col_widths_ratio": [0.22, 0.78],
      "margins_mm": { "left": 2.5, "right": 2.5, "top": 1.2, "bottom": 1.2 },
      "margins_hwpunit": { "left": 708, "right": 708, "top": 340, "bottom": 340 },
      "borders": {
        "outer": {
          "top": { "type": "SOLID", "width": "0.4 mm", "color": "#000000" },
          "bottom": { "type": "SOLID", "width": "0.4 mm", "color": "#000000" },
          "left": { "type": "NONE", "width": "0.1 mm", "color": "#000000" },
          "right": { "type": "NONE", "width": "0.1 mm", "color": "#000000" }
        },
        "inner": {
          "horizontal": { "type": "SOLID", "width": "0.12 mm", "color": "#E2E8F0" },
          "vertical": { "type": "SOLID", "width": "0.12 mm", "color": "#CBD5E1" }
        }
      },
      "styles": {
        "label_col": {
          "font": "한컴돋움",
          "size": 9.5,
          "bold": true,
          "color": "#000000",
          "fill": "#F2F4F7",
          "align": "CENTER",
          "letter_spacing": -5,
          "line_spacing": 130
        },
        "content_col": {
          "font": "휴먼명조",
          "size": 9.5,
          "bold": false,
          "color": "#000000",
          "fill": "#FFFFFF",
          "align": "LEFT",
          "letter_spacing": -5,
          "line_spacing": 135
        }
      },
      "sample_content": [
        ["사 업 명", "2026년 공공 행정 문서 표준화 및 자동 조판 엔진 고도화"],
        ["추진 목적", "HWPX 개방형 서식 확산 및 공공기관 실무 보고서 작성 효율성 50% 향상"],
        ["수행 기간", "2026. 01. 01. ~ 2026. 12. 31. (12개월)"],
        ["총 소요예산", "금 850,000,000원 (팔억오천만 원, 부가세 포함)"]
      ]
    },
    {
      "id": "preset_multi_col_evaluation",
      "name": "3~4열 다단 비교/평가 표",
      "category": "comparison",
      "description": "머리글 다크네이비/연청, 본문 지브라 교차 음영, 최하단 합계 행",
      "rows": 5,
      "cols": 4,
      "header_rows": 1,
      "col_widths_ratio": [0.18, 0.37, 0.30, 0.15],
      "margins_mm": { "left": 2.5, "right": 2.5, "top": 1.2, "bottom": 1.2 },
      "margins_hwpunit": { "left": 708, "right": 708, "top": 340, "bottom": 340 },
      "borders": {
        "outer": {
          "top": { "type": "SOLID", "width": "0.4 mm", "color": "#000000" },
          "bottom": { "type": "SOLID", "width": "0.4 mm", "color": "#000000" },
          "left": { "type": "NONE", "width": "0.1 mm", "color": "#000000" },
          "right": { "type": "NONE", "width": "0.1 mm", "color": "#000000" }
        },
        "header_split": { "type": "DOUBLE_SLIM", "width": "0.5 mm", "color": "#000000" },
        "footer_split": { "type": "SOLID", "width": "0.4 mm", "color": "#000000" },
        "inner": {
          "horizontal": { "type": "SOLID", "width": "0.12 mm", "color": "#E2E8F0" },
          "vertical": { "type": "SOLID", "width": "0.12 mm", "color": "#E2E8F0" }
        }
      },
      "styles": {
        "header": {
          "font": "한컴돋움",
          "size": 9.5,
          "bold": true,
          "color": "#000000",
          "fill": "#DFE6F7",
          "align": "CENTER",
          "letter_spacing": -5,
          "line_spacing": 130
        },
        "body_odd": {
          "font": "휴먼명조",
          "size": 9.0,
          "bold": false,
          "color": "#000000",
          "fill": "#FFFFFF",
          "align": "LEFT",
          "letter_spacing": -5,
          "line_spacing": 135
        },
        "body_even": {
          "font": "휴먼명조",
          "size": 9.0,
          "bold": false,
          "color": "#000000",
          "fill": "#F8FAFC",
          "align": "LEFT",
          "letter_spacing": -5,
          "line_spacing": 135
        },
        "footer_summary": {
          "font": "한컴돋움",
          "size": 9.5,
          "bold": true,
          "color": "#000000",
          "fill": "#ECEEF2",
          "align": "CENTER",
          "letter_spacing": -5,
          "line_spacing": 130
        }
      },
      "sample_content": [
        ["구 분", "기존 방식 (수작업)", "개선 방안 (AutoDocFit)", "개선 효과"],
        ["서식 정렬", "실무자가 수작업 셀 여백 및 너비 조정", "룰 기반 원클릭 자동 피팅 및 정렬", "시간 85% 단축"],
        ["규격 검증", "인쇄 후 눈대중 및 수기 육안 검토", "공공 편람 룰셋 기반 자동 오류 진단", "오류율 0.1% 미만"],
        ["출력 품질", "작성자마다 제각각인 폰트/선 굵기", "표준 프로파일 기반 통일된 품질 보장", "문서 신뢰도 극대화"],
        ["합 계", "3개 영역 수기 검토", "전 영역 지능형 원패스 자동화", "업무 생산성 4.8배"]
      ]
    },
    {
      "id": "preset_gantt_timeline",
      "name": "추진 일정/간트차트형 표",
      "category": "schedule",
      "description": "월별/분기별 타임라인 바 셀 채우기 색상 규격이 적용된 로드맵 표",
      "rows": 5,
      "cols": 6,
      "header_rows": 1,
      "col_widths_ratio": [0.24, 0.20, 0.14, 0.14, 0.14, 0.14],
      "margins_mm": { "left": 1.0, "right": 1.0, "top": 1.0, "bottom": 1.0 },
      "margins_hwpunit": { "left": 283, "right": 283, "top": 283, "bottom": 283 },
      "borders": {
        "outer": {
          "top": { "type": "SOLID", "width": "0.4 mm", "color": "#000000" },
          "bottom": { "type": "SOLID", "width": "0.4 mm", "color": "#000000" },
          "left": { "type": "NONE", "width": "0.1 mm", "color": "#000000" },
          "right": { "type": "NONE", "width": "0.1 mm", "color": "#000000" }
        },
        "header_split": { "type": "DOUBLE_SLIM", "width": "0.5 mm", "color": "#000000" },
        "inner": {
          "horizontal": { "type": "SOLID", "width": "0.12 mm", "color": "#E2E8F0" },
          "vertical": { "type": "DOT", "width": "0.12 mm", "color": "#CBD5E1" }
        }
      },
      "styles": {
        "header": {
          "font": "한컴돋움",
          "size": 9.5,
          "bold": true,
          "color": "#000000",
          "fill": "#E7EEF8",
          "align": "CENTER",
          "letter_spacing": -6,
          "line_spacing": 130
        },
        "task_name": {
          "font": "한컴돋움",
          "size": 9.0,
          "bold": false,
          "color": "#000000",
          "fill": "#FFFFFF",
          "align": "LEFT",
          "letter_spacing": -5,
          "line_spacing": 130
        },
        "timeline_active": {
          "font": "한컴돋움",
          "size": 9.0,
          "bold": true,
          "color": "#FFFFFF",
          "fill": "#1A365D",
          "align": "CENTER",
          "letter_spacing": -5,
          "line_spacing": 130
        },
        "timeline_sub": {
          "font": "한컴돋움",
          "size": 9.0,
          "bold": false,
          "color": "#1A202C",
          "fill": "#94BBE9",
          "align": "CENTER",
          "letter_spacing": -5,
          "line_spacing": 130
        }
      },
      "sample_content": [
        ["주요 과제", "세부 내역", "1분기", "2분기", "3분기", "4분기"],
        ["기획 및 분석", "요구사항 도출 및 표준 수립", "■", "", "", ""],
        ["엔진 개발", "HWPX 파서 및 빌더 최적화", "", "■", "■", ""],
        ["UI/UX 구현", "Flutter 표그림판 고도화", "", "", "■", ""],
        ["시범 운영", "중앙부처 시범 적용 및 검증", "", "", "", "▶ 완료"]
      ]
    },
    {
      "id": "preset_budget_breakdown",
      "name": "예산/소요비용 산출 내역 표",
      "category": "budget",
      "description": "금액 우측정렬, 3자리 콤마, 하단 합계 이중선 마감의 표준 예산 표",
      "rows": 5,
      "cols": 5,
      "header_rows": 1,
      "caption": "(단위: 원, 부가세 포함)",
      "col_widths_ratio": [0.18, 0.32, 0.16, 0.14, 0.20],
      "margins_mm": { "left": 2.5, "right": 2.5, "top": 1.2, "bottom": 1.2 },
      "margins_hwpunit": { "left": 708, "right": 708, "top": 340, "bottom": 340 },
      "borders": {
        "outer": {
          "top": { "type": "SOLID", "width": "0.4 mm", "color": "#000000" },
          "bottom": { "type": "DOUBLE_SLIM", "width": "0.5 mm", "color": "#000000" },
          "left": { "type": "NONE", "width": "0.1 mm", "color": "#000000" },
          "right": { "type": "NONE", "width": "0.1 mm", "color": "#000000" }
        },
        "header_split": { "type": "DOUBLE_SLIM", "width": "0.5 mm", "color": "#000000" },
        "total_split": { "type": "SOLID", "width": "0.4 mm", "color": "#000000" },
        "inner": {
          "horizontal": { "type": "SOLID", "width": "0.12 mm", "color": "#E2E8F0" },
          "vertical": { "type": "SOLID", "width": "0.12 mm", "color": "#E2E8F0" }
        }
      },
      "styles": {
        "header": {
          "font": "한컴돋움",
          "size": 9.5,
          "bold": true,
          "color": "#000000",
          "fill": "#F2F4F7",
          "align": "CENTER",
          "letter_spacing": -5,
          "line_spacing": 130
        },
        "category_col": {
          "font": "휴먼명조",
          "size": 9.0,
          "bold": false,
          "color": "#000000",
          "fill": "#FFFFFF",
          "align": "CENTER",
          "letter_spacing": -5,
          "line_spacing": 130
        },
        "detail_col": {
          "font": "휴먼명조",
          "size": 9.0,
          "bold": false,
          "color": "#000000",
          "fill": "#FFFFFF",
          "align": "LEFT",
          "letter_spacing": -5,
          "line_spacing": 130
        },
        "numeric_col": {
          "font": "맑은 고딕",
          "size": 9.0,
          "bold": false,
          "color": "#000000",
          "fill": "#FFFFFF",
          "align": "RIGHT",
          "letter_spacing": -3,
          "line_spacing": 130
        },
        "total_row": {
          "font": "한컴돋움",
          "size": 9.5,
          "bold": true,
          "color": "#000000",
          "fill": "#E2E8F0",
          "align": "RIGHT",
          "letter_spacing": -5,
          "line_spacing": 130
        }
      },
      "sample_content": [
        ["비 목", "산출 내역", "단 가", "수량", "금 액"],
        ["연구개발비", "전문 연구원 인건비 (3명 × 6개월)", "4,500,000", "18", "81,000,000"],
        ["서버인프라", "클라우드 분산 연산 인스턴스", "1,200,000", "12", "14,400,000"],
        ["자문회의비", "서식 표준화 전문가 위원 자문", "200,000", "25", "5,000,000"],
        ["합 계", "총 3개 비목 소요 예산 총액", "-", "-", "100,400,000"]
      ]
    },
    {
      "id": "preset_qa_checklist",
      "name": "질의응답(Q&A) / 체크리스트 표",
      "category": "audit",
      "description": "문항 No, 점검 기준, 적합/부적합 판정 뱃지가 구비된 감사/진단용 표",
      "rows": 4,
      "cols": 4,
      "header_rows": 1,
      "col_widths_ratio": [0.12, 0.48, 0.22, 0.18],
      "margins_mm": { "left": 2.5, "right": 2.5, "top": 1.2, "bottom": 1.2 },
      "margins_hwpunit": { "left": 708, "right": 708, "top": 340, "bottom": 340 },
      "borders": {
        "outer": {
          "top": { "type": "SOLID", "width": "0.4 mm", "color": "#000000" },
          "bottom": { "type": "SOLID", "width": "0.4 mm", "color": "#000000" },
          "left": { "type": "NONE", "width": "0.1 mm", "color": "#000000" },
          "right": { "type": "NONE", "width": "0.1 mm", "color": "#000000" }
        },
        "header_split": { "type": "DOUBLE_SLIM", "width": "0.5 mm", "color": "#000000" },
        "inner": {
          "horizontal": { "type": "SOLID", "width": "0.12 mm", "color": "#E2E8F0" },
          "vertical": { "type": "SOLID", "width": "0.12 mm", "color": "#E2E8F0" }
        }
      },
      "styles": {
        "header": {
          "font": "한컴돋움",
          "size": 9.5,
          "bold": true,
          "color": "#000000",
          "fill": "#F0F4F8",
          "align": "CENTER",
          "letter_spacing": -5,
          "line_spacing": 130
        },
        "icon_col": {
          "font": "한컴돋움",
          "size": 9.5,
          "bold": true,
          "color": "#1A365D",
          "fill": "#FFFFFF",
          "align": "CENTER",
          "letter_spacing": -5,
          "line_spacing": 130
        },
        "text_col": {
          "font": "휴먼명조",
          "size": 9.0,
          "bold": false,
          "color": "#000000",
          "fill": "#FFFFFF",
          "align": "LEFT",
          "letter_spacing": -5,
          "line_spacing": 135
        },
        "status_pass": {
          "font": "한컴돋움",
          "size": 9.0,
          "bold": true,
          "color": "#188038",
          "fill": "#E6F4EA",
          "align": "CENTER",
          "letter_spacing": -5,
          "line_spacing": 130
        },
        "status_fail": {
          "font": "한컴돋움",
          "size": 9.0,
          "bold": true,
          "color": "#D93025",
          "fill": "#FCE8E6",
          "align": "CENTER",
          "letter_spacing": -5,
          "line_spacing": 130
        }
      },
      "sample_content": [
        ["연번", "점검 및 진단 항목", "점검 기준", "판정 결과"],
        ["01", "행안부 F7 편집용지 여백 기준 준수 여부", "상30/하15/좌20/우20mm 일치", "적 합 (☑)"],
        ["02", "표 내부 머리글 하단 이중실선 규격 적용", "이중선 0.5mm 정상 조판 여부", "적 합 (☑)"],
        ["03", "금액 항목 천 단위 구분 콤마 및 우측정렬", "수치 데이터 우측 밀착 정렬", "보완 요망"]
      ]
    }
  ]
}
```

---

## 5. UI/엔진 연계 아키텍처

1. **`flutter_ui/lib/features/table_sketch`**:
   - 도구 모음(Toolbar)에 **[표 프리셋 (6종)]** 드롭다운 버튼을 배치하여 사용자가 원클릭 시 캔버스 그리드로 즉시 시각 렌더링.
2. **`docfit_core/hwpx/table_builder.py`**:
   - `_cellMargin` 태그에 표준 `margins_hwpunit`(`left=708, right=708, top=340, bottom=340`)을 동적 적용하여 HWPX 출력 시 완벽한 공공 표준 여백 보장.
3. **`docfit_core/table_style.py`**:
   - `profile > user_learned > standard_presets(6종)` 순의 폴백 계층으로 사용자 커스텀 서식과 충돌 방지.
