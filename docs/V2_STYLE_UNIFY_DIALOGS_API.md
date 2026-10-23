# 서식통일 마법사 검토 대화상자 API (T20·T21·T22)

다중 문서 서식 통일 마법사 진행 중 모달로 사용자의 검토 및 승인을 기다리는
검토 창 3개(T20 대표 서식 검토, T21 편집 영역 검토, T22 결과 확인)의 통신 규약이다.
기존 `get_pending_dialog` / `resolve_dialog` 브리지 파이프라인을 확장하여
Flutter 화면(`flutter_ui/lib/features/style_unify/`)에서 완전하게 모달로 처리한다.
`ui_tk_fallback=true` 설정 시 기존 Tkinter Toplevel 창이 열린다.

---

## 1. 대표 서식 검토 (T20 · Step 2)

문서에서 조사한 항목기호 및 계층별 대표 서식(글꼴, 크기, 굵기, 내어쓰기 등)을 확인하고
필요 시 사용자가 대표값을 수정하거나 판정 보류할 수 있는 대화상자다. 그룹을 선택하면 해당 그룹 필드를 편집하며, 승인 시 모든 그룹의 수정값을 함께 보낸다.

### get_pending_dialog 반환 JSON
```json
{
  "id": "dialog-uuid-001",
  "kind": "style_unify_profile",
  "title": "서식통일 2/5 · 대표 서식 확인",
  "message": "문서에서 조사한 대표 서식입니다. 대표값을 확인하면 불일치 부분을 추가 승인 없이 자동 교정합니다.",
  "confirm": true,
  "ok_label": "확인한 대표값으로 진행",
  "cancel_label": "취소",
  "styles": [
    {
      "index": 0,
      "marker": "1.",
      "role": "개조식",
      "level": 1,
      "samples_count": 5,
      "font": "맑은 고딕",
      "size": 15.0,
      "marker_bold": true,
      "label_bold": false,
      "hanging_indent": true
    },
    {
      "index": 1,
      "marker": "가.",
      "role": "본문",
      "level": 2,
      "samples_count": 8,
      "font": "맑은 고딕",
      "size": 13.0,
      "marker_bold": false,
      "label_bold": false,
      "hanging_indent": true
    }
  ],
  "choices": [
    {"id": 0, "label": "1. · 개조식 · 표본 5개"},
    {"id": 1, "label": "가. · 본문 · 표본 8개"}
  ],
  "fields": [
    {"id": "0:font", "label": "1. 글꼴", "type": "text", "value": "맑은 고딕"},
    {"id": "0:size", "label": "1. 크기 (pt)", "type": "text", "value": "15.0"},
    {"id": "0:marker_bold", "label": "1. 기호 굵게", "type": "bool", "value": "True"},
    {"id": "0:label_bold", "label": "1. 라벨 굵게", "type": "bool", "value": "False"},
    {"id": "0:hanging_indent", "label": "1. 내어쓰기", "type": "bool", "value": "True"}
  ]
}
```

### resolve_dialog 호출 (승인 및 값 수정)
```json
[
  "dialog-uuid-001",
  true,
  [0, 1],
  {
    "0:font": "나눔고딕",
    "0:size": "16.0",
    "0:marker_bold": "True",
    "0:label_bold": "False",
    "0:hanging_indent": "True"
  }
]
```

### resolve_dialog 호출 (취소)
```json
[
  "dialog-uuid-001",
  false,
  [],
  {}
]
```
- 승인 시 수정된 필드값이 마법사 대표프로필에 반영된다(크기는 pt * 100 정수로 저장).
- 취소 시 마법사는 문서 수정을 중단하고 안전하게 복귀한다.

---

## 2. 적용 영역 검토 (T21 · Step 3)

대표 서식과 불일치하여 교정 예정인 문장들을 나열하고, 사용자가 체크한 영역만
실제 교정 대상에 포함하도록 선별하는 대화상자다.

### get_pending_dialog 반환 JSON
```json
{
  "id": "dialog-uuid-002",
  "kind": "style_unify_regions",
  "title": "서식통일 3/5 · 편집 영역 확인",
  "message": "대표 서식 미적용 영역입니다. 체크된 문장만 적용합니다.",
  "confirm": true,
  "ok_label": "선택 영역만 적용",
  "cancel_label": "취소",
  "areas": [
    {
      "id": 0,
      "doc": "doc1",
      "area": "area0",
      "marker": "1.",
      "role": "개조식",
      "level": 1,
      "text": "1. 추진 배경 및 필요성 설명 문장",
      "changes": "글꼴 1영역 → 맑은 고딕, 크기 1영역 → 15pt",
      "checked": true
    },
    {
      "id": 1,
      "doc": "doc1",
      "area": "area1",
      "marker": "가.",
      "role": "본문",
      "level": 2,
      "text": "가. 세부 실행 계획 및 일정 안내",
      "changes": "내어쓰기 → 적용",
      "checked": true
    }
  ],
  "choices": [
    {"id": 0, "label": "1. / 개조식 — 추진 배경 및 필요성..."},
    {"id": 1, "label": "가. / 본문 — 세부 실행 계획 및 일정..."}
  ],
  "fields": []
}
```

### resolve_dialog 호출 (선택 영역 승인)
```json
[
  "dialog-uuid-002",
  true,
  [0],
  {}
]
```

### resolve_dialog 호출 (취소)
```json
[
  "dialog-uuid-002",
  false,
  [],
  {}
]
```
- `selection`에 포함된 인덱스 문장만 4단계 서식 수정 및 자간/내어쓰기 단계가 수행된다.
- 취소 시 선택 목록은 빈 배열이 되며 마법사가 종료된다.

---

## 3. 작업 결과 확인 (T22 · Step 5)

서식통일 교정 및 저장이 완료된 후 읽기 전용 검수 결과를 사용자에게 보고하는 대화상자다.
불일치·판정 보류·미확정 문단 및 오류 내역을 모두 스크롤로 표시한다. 결과 폴더 열기는 작업 완료 후 기존 결과 화면에서 제공한다.

### get_pending_dialog 반환 JSON
```json
{
  "id": "dialog-uuid-003",
  "kind": "style_unify_result",
  "title": "서식통일 5/5 · 작업 결과 확인",
  "message": "저장 결과 확인 · 검수 통과",
  "confirm": false,
  "ok_label": "결과 확인",
  "cancel_label": "닫기",
  "result": {
    "file": "보고서.hwp",
    "status": "passed",
    "status_text": "검수 통과",
    "checked": 45,
    "issues": [],
    "not_checkable": [],
    "unresolved": [],
    "error": null
  }
}
```

### resolve_dialog 호출 (확인 완료)
```json
[
  "dialog-uuid-003",
  true,
  [],
  {}
]
```

---

## 4. UI 및 Key 규약

| 화면 | 위젯 클래스 | 식별 키 |
| :--- | :--- | :--- |
| T20 대표 서식 | `UnifyPickStyleDialog` | `Key('unifyPickStyle_<i>')`<br>`Key('unifyConfirm')`<br>`Key('unifyCancel')` |
| T21 적용 영역 | `UnifyAreaDialog` | `Key('unifyArea_<doc>_<area>')`<br>`Key('unifyConfirm')`<br>`Key('unifyCancel')` |
| T22 결과 확인 | `UnifyResultDialog` | `Key('unifyOpenFolder')`<br>`Key('unifyConfirm')`<br>`Key('unifyCancel')` |

모든 대화상자는 폭 420px 환경(작은 창)에서도 오버플로 없이 스크롤할 수 있도록 반응형으로 구현된다.

## C19 검증
Tk 전용 검토창 본문은 a737632와 동일하며, ui_tk_fallback 또는 일반 Tk 실행에서 기존 창으로 분기한다. 단위 시험은 Toplevel·messagebox를 차단하고 숨은 백엔드 대기/응답을 가짜 변수로 완료하여 사람 입력 없이 종료한다.
