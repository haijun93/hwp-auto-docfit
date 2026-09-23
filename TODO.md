# 작업 예정 목록

지금 당장 진행하지 않고 미뤄둔 기능 요청을 적어둔다. "나중에 작업해"라고
명시적으로 요구받으면 그때 해당 항목을 꺼내 구현한다.

## 표 구조 정밀 조정 (C1/C2/C3)

한/글 COM 자동화(win32com)로 표 셀/열/테두리를 직접 조작하는 작업. 이
샌드박스에는 한/글이 없어 실제 검증이 불가능하고, 문자 서식 조정보다
표 구조를 잘못 건드렸을 때 문서 손상 위험이 커서 신중하게 별도로
진행하기로 함. 아래 API는 PyPI의 `pyhwpx` 패키지 소스(`pip download
pyhwpx --no-deps`로 받은 공식 문서 대안 — forum.developer.hancom.com 등은
이 환경에서 접근 차단됨)를 읽어 이미 확인해둔 실제 동작하는 호출이다.

### C1. 셀 안쪽 여백 강제 축소

표 안 텍스트가 1~2자 차이로 다음 줄로 넘어갈 때, 셀 좌우 안쪽 여백을
기본 1.8mm에서 0~1mm까지 단계적으로 줄여본다.

- 캐럿이 셀 안에 있어야 함(`is_cell()` 확인 필요).
- `pset = hwp.HParameterSet.HShapeObject`
- `hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)`
- `pset.HSet.SetItem("ShapeType", 3)`
- `pset.HSet.SetItem("ShapeCellSize", 0)`  ← 0 = 여백 모드
- `pset.ShapeTableCell.HasMargin = 1`
- `pset.ShapeTableCell.MarginLeft/Right/Top/Bottom = hwp.MiliToHwpUnit(mm)`
- `hwp.HAction.Execute("TablePropertyDialog", pset.HSet)`

해야 할 일: 셀 텍스트가 실제로 2줄로 넘어갔는지 감지하는 함수(셀 높이나
화면줄 수 비교), 1.8mm→0mm까지 0.2~0.3mm 단위로 줄이며 매 단계
재측정하는 루프, try/except 방어, 관련 테스트(순수 로직 부분만), 문서화.

### C2. 셀 너비를 본문 여백에 맞춤

표 전체 너비가 본문 좌우 여백과 어긋나 있을 때(통상 목표 150~170mm),
열 너비를 1pt 단위로 밀고 당겨 맞춘다.

- **안전한 방식(채택 예정)**: 열 단위 선택 후 `ShapeCellSize=1`(너비
  모드)로 개별 열의 `pset.ShapeTableCell.Width`를 설정. 열 선택은
  `TableColPageUp()` + `TableCellBlock()` + `TableCellBlockExtend()` +
  `TableColPageDown()` 같은 Run 액션 조합(pyhwpx `set_col_width` 참고).
  목표 전체 너비에 맞춰 열별 목표 너비를 비례 계산해 하나씩 적용.
- **피해야 할 방식**: pyhwpx의 `set_table_width()`가 쓰는 전체 표
  XML 왕복(`GetTextFile("HWPML2X","saveblock")` → XML 수정 →
  선택 영역 삭제 → `SetTextFile(..., option="insertfile")`) 방식은
  삭제 후 재삽입이라 내용/서식 손실 위험이 있어 이 코드베이스의
  "안전하고 덧붙이기만 하는" COM 사용 방식과 맞지 않음. 쓰지 않는다.

해야 할 일: 본문 좌우 여백 조회(`HSecDef`/`"PageSetup"`), 현재 표 전체
너비 측정, 열별 목표 너비 비례 계산, 열 순회하며 안전한 방식으로 적용,
재측정 후 오차 보정 루프.

### C3. 표 테두리 선 굵기 통일

외곽선 0.4~0.5mm 실선, 헤더 하단 이중선 0.5mm, 내부 구분선 0.12mm 실선,
좌우 외곽선은 투명/없음으로 통일.

- 셀 배경(채우기)은 `HParameterSet.HCellBorderFill` + 액션
  `"CellFill"`로 이미 확인함(`pset.FillAttr.type`,
  `WinBrushFaceColor` 등 — pyhwpx `cell_fill()` 참고).
- **테두리 선(굵기/종류) 자체의 정확한 속성명은 아직 확인 못함.**
  pyhwpx 소스에서 `HCellBorderFill`을 grep하면 두 번째 사용처가
  더 있었는데(그라데이션 함수였음, 배경 채우기 관련) 실제 선 굵기용
  속성(`BorderTypeLeft/Right/Top/Bottom`,
  `BorderWidthLeft/Right/Top/Bottom`, "이중선"/"실선"/"없음"에 해당하는
  정수값, 특정 방향만 선택하는 방법, "ApplyTo" 관련)은 다음에 이어서
  pyhwpx 소스나 다른 경로로 마저 확인해야 함.

해야 할 일: 테두리 선 속성명 확정 → 표마다 외곽선/헤더 하단선/내부
구분선을 구분해 적용하는 함수 작성 → 방어적 코드 → 문서화.

### 공통 사항

- 세 항목 모두 Windows + 실제 한/글에서 검증 전이라 신뢰 수준이 낮음.
  구현 직후에도 사용자에게 실기 검증을 권해야 함.
- 표 구조를 잘못 건드리면 문자 서식 실수보다 되돌리기 어려우므로,
  구현 시 모든 COM 호출을 try/except로 감싸고 실패 시 원본을
  손상시키지 않는 방향으로 조심스럽게 진행할 것.
