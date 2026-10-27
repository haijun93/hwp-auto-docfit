# HWP AutoDocFit 2.0.1 표 템플릿 공공 표준 프리셋 결합 명세서 (P7)

- **문서 버전**: v2.0.1
- **기준 브랜치**: `feature/2.0.1-public-presets` (main v2.0.0 기준)
- **적용 대상**: `docfit_core/public_table_presets.py`, `docfit_app/table_units_service.py`, `flutter_ui/lib/core/api/table_units_api.dart`, `flutter_ui/lib/features/table_units/table_units_screen.dart`
- **설계 기준 문서**: `reports/P7-design.md` (Codex 수석 아키텍트)

---

## 1. 개요 및 설계 목적

본 문서는 행정업무운영편람 및 공공 보고서 작성 관례에 맞춘 **공공 업무 예시 6대 표준 표 프리셋**을 AutoDocFit 표 템플릿 시스템에 정식 결합하기 위한 명세서입니다.

기관의 법적 공인이나 외부 규정 인증이 아닌 실무 보고서 작성을 돕는 **공공 업무 예시 프리셋**으로 제공되며, 기존 템플릿 목록 뒤에 순서대로 결합되어 분류·검색·즐겨찾기·최근 사용·썸네일·정보단위 조절·칸 글 수정·복사 흐름을 동일하게 사용합니다.

### 핵심 원칙
1. **공통 파이프라인 유지**: 별도 프리셋 전용 복사창, HTML 클립보드, 새로운 COM 수명주기를 만들지 않고 기존 API 계약(`TableUnitsService`)과 화면 흐름을 그대로 공유합니다.
2. **독립 HWPX 생성 자립 엔진**: 표 HWPX 생성 및 구조 미리보기는 앱 내장 기본 서식(`resources/서식예시/기본 서식.hwpx`)과 `table_builder`/`table_units` 엔진을 기반으로 순수 파이썬 환경에서 자립 수행합니다.
3. **한/글 COM 복사 및 썸네일 연동**: 한/글 클립보드 복사는 검증된 `Hwp Native` 클립보드 포맷과 백그라운드 한/글 인스턴스를 사용하며, 실측 PNG 썸네일은 기존 PDF 변환/래스터화 캐시 파이프라인을 그대로 재사용합니다.

---

## 2. 6대 공공 표준 프리셋 정의 및 정보단위 계획

공공 프리셋 6종은 `pub_` 접두사를 가지며, 고정 머리글 및 합계(끝) 행을 보존하면서 본문 반복 정보단위를 조절합니다.

| 프리셋 ID | 명칭 | 용도 배지 | 기본 격자 | 반복 축 단위 (start / count / min / max) | 머리/끝행 |
|---|---|---|---|---|---|
| `pub_summary_headline` | ① 요약/헤드라인 1칸 표 | 핵심 요약 | 1행 × 1열 | 고정 (조절 축 없음) | 0 / 0 |
| `pub_two_col_definition` | ② 2열 정의/대비 표 | 개요 양식 | 4행 × 2열 | 행 (start: 0, count: 4, min: 1, max: 30) | 0 / 0 |
| `pub_multi_col_comparison` | ③ 3~4열 다단 비교/평가 표 | 비교·평가 | 5행 × 4열 | 행 (start: 1, count: 3, min: 1, max: 30) | 1 / 1 |
| `pub_gantt_timeline` | ④ 추진 일정/간트차트형 표 | 추진 일정 | 5행 × 6열 | 행 (start: 1, count: 4, min: 1, max: 30)<br>열 (start: 2, count: 4, min: 2, max: 12) | 1 / 0 |
| `pub_budget_breakdown` | ⑤ 예산/소요비용 산출 내역 표 | 재정·회계 서식 | 5행 × 5열 | 행 (start: 1, count: 3, min: 1, max: 30) | 1 / 1 |
| `pub_qa_checklist` | ⑥ 질의응답(Q&A) / 체크리스트 표 | 감사·점검 | 4행 × 4열 | 행 (start: 1, count: 3, min: 1, max: 30) | 1 / 0 |

- 모든 활성 축의 core=1, sep=0.
- 실제 행수 = 머리행 + 요청 `row_count` + 끝행 (고정표 제외).
- 간트 실제 열수 = 2(고정 설명열) + 요청 `col_count`.
- 고정 축에 값을 전달하거나 범위를 벗어난 값(0, 음수, bool, 문자열)은 `ValueError`로 거부됩니다.

---

## 3. 프리셋 세부 조판 메트릭스 명세

### ① 요약/헤드라인 1칸 표 (`pub_summary_headline`)
- **용도**: 보고서 서두 핵심 요약 콜아웃 상자
- **구조**: 1행 1열 (100% 폭, 조절 불가)
- **테두리**: 상하 실선 0.4mm (`#1A365D`), 좌우 선 없음(`NONE`)
- **배경음영**: 소프트 블루 `#EBF3FA`
- **안쪽 여백**: 좌우 4.0mm (1134 HWP단위) / 상하 2.5mm (708 HWP단위)
- **글꼴 및 문단**: 한컴돋움 10.5pt, 줄간격 140%, 자간 -5%, 좌측 정렬

### ② 2열 정의/대비 표 (`pub_two_col_definition`)
- **용도**: 사업 개요(명칭, 목적, 기간, 예산), 용어 정의, 1:1 대비 서식
- **구조**: 기본 4행 2열 (열 너비 22% : 78%)
- **테두리**: 상하 실선 0.4mm, 좌우 선 없음, 중간 가로선 0.12mm (`#E2E8F0`), 열 구분선 0.12mm
- **배경음영**: 1열 항목 연회색 `#F2F4F7`, 2열 내용 흰색 `#FFFFFF`
- **안쪽 여백**: 좌우 2.5mm (708 HWP단위) / 상하 1.2mm (340 HWP단위)
- **글꼴 및 문단**: 항목열 한컴돋움 9.5pt Bold (가운데 정렬) / 내용열 휴먼명조 9.5pt (좌측 정렬), 줄간격 130%

### ③ 3~4열 다단 비교/평가 표 (`pub_multi_col_comparison`)
- **용도**: 대안 비교 평가, 지표별 달성도, 추진 방안 대비
- **구조**: 기본 5행 4열 (18% : 37% : 30% : 15%), 머리글 1행, 합계 1행
- **테두리**: 최상단 0.4mm, 머리글 하단 이중선 0.5mm (`DOUBLE_SLIM`), 최하단 0.4mm, 좌우 개방
- **배경음영**: 머리글 연청색 `#DFE6F7`, 본문 지브라(홀수행 `#FFFFFF`, 짝수행 `#F8FAFC`), 합계행 `#ECEEF2`
- **글꼴 및 문단**: 머리글 한컴돋움 9.5pt Bold / 본문 휴먼명조 9.0pt / 합계 한컴돋움 9.5pt Bold, 줄간격 130%

### ④ 추진 일정/간트차트형 표 (`pub_gantt_timeline`)
- **용도**: 월별/분기별 추진 일정 및 타임라인 로드맵
- **구조**: 기본 5행 6열 (과제 24%, 세부내역 20%, 기간열 균등 56%)
- **테두리**: 상단 0.4mm, 머리글 하단 이중선 0.5mm, 하단 0.4mm, 좌우 개방. 고정열 사이 및 경계는 0.12mm 실선, 기간 영역 내부는 점선(`DOT`)
- **배경음영**: 머리글 `#E7EEF8`, 추진 바 다크네이비 `#1A365D` (흰색 굵은 글자), 완료 바 `#94BBE9`
- **안쪽 여백**: 좌우 1.0mm (283 HWP단위) / 상하 1.0mm (283 HWP단위)

### ⑤ 예산/소요비용 산출 내역 표 (`pub_budget_breakdown`)
- **용도**: 비목별 예산 산출 내역 및 소요 경비 계산
- **구조**: 기본 5행 5열 (비목 18%, 산출내역 32%, 단가 16%, 수량 14%, 금액 20%), 머리글 1행, 합계 1행
- **테두리**: 상단 0.4mm, 머리글 하단 이중선 0.5mm, 최하단 합계 이중선 0.5mm (`DOUBLE_SLIM`) 마감
- **배경음영**: 머리글 `#F2F4F7`, 합계행 `#E2E8F0`
- **글꼴 및 정렬**: 수치 및 금액 열 우측 정렬(RIGHT), 비목/산출내역 휴먼명조 9.0pt, 합계 돋움 Bold

### ⑥ 질의응답(Q&A) / 체크리스트 표 (`pub_qa_checklist`)
- **용도**: 업무 점검표, 자가 진단, 대관 질의응답
- **구조**: 기본 4행 4열 (연번 12%, 점검항목 48%, 점검기준 22%, 판정결과 18%), 머리글 1행
- **테두리**: 상단 0.4mm, 머리글 하단 이중선 0.5mm, 하단 0.4mm, 좌우 개방
- **판정 뱃지 서식**: 명확한 적합 텍스트('적 합 (☑)', '적합', '☑', 'Pass')는 소프트 그린 `#E6F4EA` / 텍스트 `#188038`, 주의/부적합('보완 요망', '부적합', '부적 합')은 소프트 핑크 `#FCE8E6` / 텍스트 `#D93025`

---

## 4. 모듈 구조 및 함수 인터페이스

### `docfit_core/public_table_presets.py`
순수 파이썬/XML 기반 자립 프리셋 조판 엔진:

```python
# 프리셋 정보 조회
def get_public_preset_descriptors() -> list[dict[str, Any]]: ...
def is_public_preset(template_id: str) -> bool: ...
def get_public_preset(template_id: str) -> dict[str, Any] | None: ...
def public_preset_plan(preset_id: str) -> dict[str, Any]: ...

# 조판 및 내보내기
def preview_public_preset(
    preset_id: str,
    row_count: int | None = None,
    col_count: int | None = None,
    *,
    fill: str = "increment",
    cell_texts: dict[str, str] | None = None
) -> dict[str, Any]: ...

def export_public_preset(
    preset_id: str,
    output_path: str | Path,
    row_count: int | None = None,
    col_count: int | None = None,
    *,
    fill: str = "increment",
    cell_texts: dict[str, str] | None = None
) -> Path: ...

# 결정론적 스냅샷 키
def public_preset_snapshot_key(preset_id: str) -> str: ...

# 호환용 wrapper (물리적 행열 격자 변환)
def build_public_preset_preview(
    preset_id: str,
    target_rows: int | None = None,
    target_cols: int | None = None,
    cell_texts: dict[str, str] | None = None
) -> dict[str, Any]: ...
```

---

## 5. 백엔드 및 서비스 캐시 정책 (`TableUnitsService`)

1. **디스크립터 병합 (`_units`)**:
   - 기존 서식 모음 파일(`표 서식모음.hwpx`)의 `describe_units()` 목록 뒤에 공공 6대 프리셋 디스크립터를 결합합니다.
   - 기존 서식 손상 시 `CATALOG_UNAVAILABLE` 오류를 정상 반환합니다.
2. **독립 스냅샷 캐시 (`_snapshot_path`, `_snapshot_url`)**:
   - 공공 프리셋 스냅샷은 `<snapshot_root>/public/<key>.png` 경로에 분리 저장합니다.
   - 스냅샷 키는 `PUBLIC_PRESET_REVISION = 'p7-v1'`, 프리셋 ID, 바탕 양식 해시, 최종 표/헤더/페이지 XML 튜플 해시(SHA256 20자리)로 계산되어 결정론적으로 유지됩니다.
   - 16자리 레거시 해시 폴더 청소 로직에 6자리 'public' 폴더가 영향을 받지 않습니다.
3. **루팅 분기 (`preview`, `_export`)**:
   - `is_public_preset(id)` 판정으로 공공 프리셋만 전용 엔진으로 라우팅하며, 미등록 ID는 기존 `INVALID_INPUT` 예외로 처리됩니다.

---

## 6. 프론트엔드 연동 명세 (`Flutter UI`)

1. **`TableTemplateInfo` 모델 확장**:
   - 선택적 메타 필드 `badge: String`, `description: String`, `guideline: Map<String, String>` 지원.
   - 이전 버전 응답 및 필드 누락 시 안전한 기본값(빈 문자열 및 빈 맵) 폴백.
2. **분류 리본 및 카테고리 칩**:
   - `공공 표준` 카테고리 칩 왼쪽에 `Icons.account_balance` (16px) 아이콘 표시.
   - 별도 모드 분기 없이 기존 칩 필터링 및 검색(`searchTextField`) 파이프라인과 100% 호환.
3. **표준 조판 가이드라인 카드 (`_buildPresetGuideline`)**:
   - 우측 상세 화면 상단에 용도 배지, 설명 및 4대 가이드라인(여백, 테두리, 글꼴, 배경) 카드 표시 (`Key('publicPresetGuideline')`).
   - 비공공 템플릿 선택 시 자동으로 사라지며, 420px 모바일 폭 반응형에서도 오버플로 없이 줄바꿈 배치.
