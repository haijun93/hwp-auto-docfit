# 메모 편집기 코어 경계 (EditorCore) — 2026-11-07

노트북 '+메모 추가' 1단계에서 만든 메모 편집기의 Flutter ↔ 편집 코어 경계를 적는다.
Rust 편집 코어(EDCORE, 맥에서 작업 중)는 이 경계에 맞춰 나중에 연결한다.

## 사용자 결정
- 외부 서식 편집 패키지(flutter_quill 등) 사용 금지.
- 입력은 Flutter `TextField`/`EditableText`가 그대로 받는다(한글 IME 조합·접근성 보존).
- 편집 로직은 `flutter_ui/lib/features/editor/` 독립 모듈. 다른 화면(자료함 메모 등)에서 재사용.
- Windows 메모장 벤치마킹(실행취소 여러 단계, 자동 저장 등). 찾기·바꾸기·확대·상태 표시줄은 2단계.

## 모듈 구성
| 파일 | 역할 | Flutter 위젯 의존 |
|---|---|---|
| `markdown_format.dart` | 서식 명령(순수 함수: 굵게·기울임·코드·코드 블록·목록·인용·구분선·링크·제목·서식 지우기), Markdown → 평문 문단 | 없음(`TextEditingValue`만) |
| `editor_core.dart` | `EditorCore` 추상(경계) + `DartEditorCore`(임시 구현: 스냅숏 실행취소) | 없음 |
| `memo_editor.dart` | `MemoEditor` 위젯(제목·도구줄·본문·'Saved' 표시·삭제), `MemoEditorController` | 있음 |

노트북 연결은 `notebook_screen.dart`의 `_MemoPage`(출처로 저장)와 `NotebookApi.addMemoSource`.

## EditorCore 계약
- **값**: `value`(본문 Markdown 원문 + 선택). 본문은 서식 기호가 들어간 원문 그대로 입력 칸에 보인다.
- **입력**: 화면이 `updateFromInput(TextEditingValue)`로 알린다. 코어는 이력 묶음을 정한다.
  - IME 조합 중(`composing` 유효)인 값은 조합이 끝날 때까지 한 묶음.
  - 줄바꿈, 커서 이동, 서식 명령, `breakUndoGroup()`(화면이 0.7초 멈춤마다 부름)에서 묶음을 끊는다.
- **명령**: `apply(EditorCommand)`, `setBlockStyle(0~3)`, `insertLink(url)` — 하나가 실행취소 한 단계.
- **이력**: `undo/redo/canUndo/canRedo`. Ctrl+Z/Y/Shift+Z는 `TextField` 자체 이력이 아니라 코어 이력을 쓴다.
- **출력**: `markdown`(저장 원문), `plainParagraphs()`(검색 색인 평문 + 제목 수준).

## Rust 코어로 바꿀 때
1. `EditorCore`를 구현한 브리지 클래스(예: `RustEditorCore`)를 만들고 `MemoEditor(createCore: ...)`로 넘긴다. 화면 코드는 바꾸지 않는다.
2. 동기 계약이다(`value`를 바로 돌려줌). FFI 동기 호출이면 그대로, 프로세스 브리지(비동기)면 Dart 쪽에 값 사본을 두고 이력·서식만 코어에 맡기는 어댑터가 필요하다.
3. 서식 규칙의 기준은 `test/memo_editor_test.dart`와 `tests/test_notebook_service.py`(평문 변환)이다. Rust 구현은 같은 입력에 같은 결과를 내야 한다.
4. 평문 변환 규칙은 Dart `markdownToPlainParagraphs`와 Python `memo_markdown_to_paragraphs` 두 곳에 있다(바꾸면 함께). Rust 코어가 들어오면 한 곳으로 모으는 것을 검토.

## 저장 형식(1단계)
- 화면 → 호스트 `notebook({"cmd": "nb_memo_add", notebook_id, title, markdown})`.
- 호스트(`docfit_app/notebook_service.py`)가 Markdown 원문을 `%LOCALAPPDATA%\HWP_AutoDocFit\notebook_memos\<제목>-<시각>-<난수>.txt`에 새로 쓰고(덮어쓰기 없음),
  평문 문단을 붙여 klib `nb_source_add`(kind=`txt`)로 넣는다. 그래서 다른 출처처럼 체크·본문검색·인용 대상이 된다.
- 자동 저장('Saved')은 1단계에서 노트북 화면의 초안(메모리)에만 한다. 닫았다 다시 열면 이어 쓰고, '출처로 저장'이나 삭제하면 비운다.

## 남은 일(2단계 이후)
- 저장한 메모 출처 다시 열어 수정·이름 바꾸기(klib에 출처 문단 교체 API 필요: 현재 `nb_index`는 덧붙이기만 함).
- 앱 재시작 후 초안 복구(파일 자동 저장), 찾기·바꾸기, 확대·축소, 상태 표시줄, 서식 미리보기(Markdown 원문 보기 전환).
- 한글 조합 입력 실기 확인(Windows).
