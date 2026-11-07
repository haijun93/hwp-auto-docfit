# 메모 편집기 Rust 코어(editor_core) 설계 — 1단계

작성: 2026-11-07, 브랜치 `feature/edcore`. 근거: TODO.md '노트북(개발자 모드) 개선 3건 (3) +메모 추가'의 구현 방침
(외부 서식 편집 패키지 없이 Rust 편집 코어 + Flutter UI, Windows 메모장 벤치마킹, 독립 모듈).
이번 단계는 **Rust 코어만**이다. Flutter UI·klib 연결은 하지 않았다.

## 1. 구성

`editor_core/` 크레이트(Cargo 의존성 0개, std만 — GitLab 보안 검사 때문). 시험: `cd editor_core && cargo test`.

| 모듈 | 역할 |
|---|---|
| `buffer.rs` `TextBuffer` | 갭 버퍼(바이트) + 줄 시작 색인 + 글자 수. 위치는 UTF-8 **바이트 오프셋**, 글자 경계만 허용. 내부 줄바꿈은 항상 `\n` |
| `doc.rs` `Document` | 버퍼 + 실행취소/다시실행(입력 묶음) + 줄·열 + 찾기·바꾸기 + 저장/자동 저장 + 변경 여부(dirty) |
| `search.rs` | 찾기(대소문자 옵션·온전한 낱말 옵션), 모두 바꾸기 문자열 생성 |
| `markdown.rs` | 블록·인라인 해석, 서식 적용/해제 연산 |
| `fileio.rs` | 인코딩(UTF-8/UTF-8 BOM/UTF-16 LE·BE) 감지·변환, 줄바꿈(CRLF/LF/CR) 감지·변환, 임시 파일 후 교체 저장 |
| `json.rs` | 직접 구현한 JSON 값·파서·직렬화(대리 쌍·깊이 64 제한) |
| `api.rs` `Engine` | JSON 한 줄 명령 → JSON 한 줄 응답. 여러 문서를 번호로 관리 |

### 선택한 구조와 이유
- **갭 버퍼**(rope 대신): 메모 편집은 커서 근처에 편집이 몰려 갭 버퍼가 단순하고 빠르다. 7 MB 글에서 같은 위치 이어 입력 글자당 12 µs.
  병목은 갭이 아니라 줄 색인 갱신(뒤 줄 오프셋 이동, 줄 수에 비례)이다. 수십만 줄 이상이 필요해지면 줄 색인을 청크/Fenwick 트리로 바꾼다(공개 API 불변).
- **내부는 LF 통일**: 열 때 줄바꿈 형식을 감지해 기억하고, 저장할 때 원래 형식으로 되돌린다. 붙여넣은 `\r\n`·`\r`도 LF가 된다. 새 문서는 메모장처럼 CRLF.
- **바이트 오프셋을 API 기준으로**: Flutter(`TextEditingValue`)는 UTF-16 코드 유닛이므로 `edit_to_utf16`/`edit_from_utf16` 변환 명령을 둔다
  (이모지 같은 대리 쌍 한가운데는 오류). 글자 경계가 아닌 위치는 항상 오류로 거절해 문자열이 깨지지 않는다.

## 2. 실행취소 규칙(입력 묶음)
- 이어 쓰기는 한 묶음: 직전에 넣은 글의 안쪽·끝에서 일어나는 교체는 합친다. **한글 조합(ㅎ→하→한→…)이 한 번의 실행취소**가 되는 이유.
- 공백·줄바꿈이 새 낱말을 시작하면 묶음을 나눈다(낱말 단위 실행취소). 줄바꿈부터는 새 묶음.
- Backspace/Delete 연속은 한 묶음(`abcdef`에서 뒤 3자를 지우고 실행취소 1번이면 복원).
- `begin_group`/`end_group`(중첩 가능)으로 여러 편집을 명시적으로 한 묶음으로. 서식 연산·모두 바꾸기는 내부에서 이를 쓴다.
- `commit`: 커서 이동·붙여넣기·포커스 이동 같은 경계에서 호출해 묶음을 마감.
- 단계는 최대 5000묶음(넘으면 가장 오래된 것 폐기). 새 편집은 다시실행 기록을 지운다.
- `dirty`: 저장 시점의 실행취소 위치와 비교하므로 입력 후 전부 취소하면 다시 "저장됨"으로 돌아간다.

## 3. Markdown 해석
지원: 제목(`#`~`######`), 굵게(`**`,`__`), 기울임(`*`,`_`), 인라인 코드(`` ` ``), 코드 블록(``` ``` ```), 링크(`[글](주소)`),
글머리(`- * +`, 들여쓰기 2칸=1단계)·번호(`1.`) 목록, 인용(`>`), 구분선(`---`,`***`,`___`).
의도적 단순화: 표·이미지·HTML·setext 제목·참조 링크·중첩 인용 미지원. 닫히지 않은 표지는 글자 그대로 둔다. 단어 안쪽 `_`(snake_case)는 기울임이 아니다.

`edit_md_parse`는 `[from_line,to_line)`만 해석한다(코드 블록 안/밖 상태는 문서 처음부터 울타리 줄만 훑어 계산). Flutter는 **화면에 보이는 줄만** 요청한다.

서식 연산(모두 한 번의 실행취소, 새 선택 범위를 돌려줌):
`edit_md_inline`(굵게·기울임·코드 토글: 표지 포함 선택·바깥을 감싼 경우 모두 해제, `***`에서 한쪽만 해제 가능),
`edit_md_block`(보통·제목1~6·글머리·번호·인용; 모든 줄이 이미 그 형식이면 보통으로 토글, 코드 블록 안은 건드리지 않음),
`edit_md_link`, `edit_md_rule`, `edit_md_code_block`(토글), `edit_md_clear`(서식 지우기: 줄 머리 표지·인라인 표지·코드 울타리 제거, 코드 블록 안 내용은 보존).

## 4. 공개 API (JSON)
요청 `{"cmd":"edit_xxx","doc":N,...}` → 응답 `{"ok":true,...}` / `{"ok":false,"message":"..."}`.
`cmd`·`ok`·`message` 규약은 klib 파이프와 동일. 위치 인자는 모두 바이트 오프셋.

| 명령 | 인자 | 응답 핵심 |
|---|---|---|
| `edit_ping` | – | `message`,`version` |
| `edit_open` | `text` 또는 `path`, 선택 `line_ending` | `doc`, 줄/글자/바이트/낱말 수, `line_ending`,`mixed_line_endings`,`encoding`,`dirty` |
| `edit_close` / `edit_info` | `doc` | 정보 |
| `edit_text` / `edit_lines` | `start,end` / `from,to` | `text` / `lines[{line,start,text}]` |
| `edit_insert` / `edit_delete` / `edit_replace` | `pos,text` / `start,end` / `start,end,text` | `cursor`,`len`,`chars`,`lines`,`dirty`,`can_undo`,`can_redo` |
| `edit_begin_group` / `edit_end_group` / `edit_commit` | – | 묶음 제어 |
| `edit_undo` / `edit_redo` | – | 위와 같음 + `changed` |
| `edit_line_col` / `edit_offset` | `pos` / `line,col` | `line,col`(1부터, 글자 단위) / `pos` |
| `edit_to_utf16` / `edit_from_utf16` | `pos` / `unit` | 변환값 |
| `edit_find` / `edit_find_all` | `query`,`case_sensitive`,`whole_word`,`from`,`wrap`/`limit` | `found,start,end` / `count,matches[]` |
| `edit_replace_next` / `edit_replace_all` | `query,with`+옵션 | `replaced,start` / `count` |
| `edit_md_parse` | `from_line,to_line` | `blocks[{kind,line,start,end,content_start,spans[]}]` |
| `edit_md_inline` | `start,end,kind=bold\|italic\|code` | `sel_start,sel_end` |
| `edit_md_block` | `start,end,kind=paragraph\|heading\|bullet\|number\|quote`,`level` | `sel_start,sel_end` |
| `edit_md_link` / `edit_md_rule` / `edit_md_code_block` / `edit_md_clear` | `start,end[,url]` / `pos` | 선택 범위 / `cursor` |
| `edit_set_line_ending` / `edit_set_encoding` | `line_ending` / `encoding` | 정보 |
| `edit_save` / `edit_autosave` | `path`(저장은 생략 가능) | 정보 / `saved,dirty` |

Rust에서는 `editor_core::api::Engine::new().handle(&str) -> String` 한 함수가 전부다. 직접 쓸 때는 `Document`·`markdown::*`를 바로 호출할 수 있다.

### 저장·자동 저장
`save`: 같은 폴더에 `.이름.PID.tmp`를 쓰고 `sync_all` 후 `rename`으로 교체(Windows에서도 기존 파일 덮어쓰기). 실패하면 임시 파일을 지우고 원본은 그대로.
`autosave`: 같은 방식으로 **복구 사본**을 따로 쓰며 원본·dirty 상태는 건드리지 않는다. 호출 시점(입력 후 N초 유휴, 포커스 상실)은 UI가 정한다.
복구 사본 위치·수명 정책(예: `%LOCALAPPDATA%\HWP_AUTODOCFIT\memo-recovery\<메모id>.autosave`, 저장 성공 시 삭제)은 UI 단계에서 확정.
인코딩은 UTF-8/BOM/UTF-16만. BOM 없는 CP949(옛 한글 txt)는 **열기 오류**로 알린다(변환기는 후속, 표 없이 std만으로는 불가).

## 5. klib 통합 방안 비교

| | A. klib에 포함 (`klib/Cargo.toml`에 `editor_core = { path = "../editor_core" }`) | B. 새 exe (`editor_core` 단독 서버) |
|---|---|---|
| 호출 경로 | 기존 파이프·Dart 브리지 그대로. `pipe.rs`의 `match cmd`에 `cmd.starts_with("edit_")` 한 줄을 `Engine`에 위임 | 새 파이프 이름·기동/종료/유휴 종료·사용자 SID 보안 등을 다시 구현 |
| 배포·서명 | 파일 수 불변, 서명 대상 불변. klib.exe 크기 증가는 작음(코어 의존성 0, 순수 로직) | exe 1개 추가: 서명·설치기·백신 예외·업데이트 항목 추가 |
| 수명 | klib 프로세스와 같음(유휴 종료 시 열린 편집 문서 상태가 사라짐 → **문서 상태를 UI가 항상 복구 가능하게** 보관 필요) | 편집 전용 수명 가능 |
| 결함 격리 | `panic = "abort"`(klib release 설정)라 코어 버그가 klib(자료함·검색 색인)까지 죽임 | 편집기 문제가 자료함에 번지지 않음 |
| 잠금 | 편집은 문서별 상태라 `Mutex<Engine>` 하나로 충분(명령이 µs 단위) | 해당 없음 |

**권고: A(klib 포함).** 근거: 명령이 모두 µs~수십 ms 순수 계산이고 의존성이 없어 크기·보안 부담이 거의 없으며, 파이프·서명·기동 로직 재사용이 크다.
단, 위험 두 가지를 같이 처리한다: ① `panic = "abort"` 때문에 코어는 `unwrap`/인덱싱 패닉이 없어야 한다 → 이번 시험에 3000회 무작위 모델 시험을 넣었고, UI 연결 전 퍼징(무작위 명령열) 확대를 권한다.
② klib가 유휴로 종료돼도 메모가 사라지지 않게, Flutter가 편집 중 내용을 자동 저장(`edit_autosave`)하고 재연결 시 `edit_open`으로 복원한다.
이후 크기·안정성 문제가 확인되면 같은 `Engine`을 `src/bin/editor_server.rs`로 빼서 B로 바꿀 수 있다(코어 변경 없음).
이 결정은 사용자 확인 사항이다(klib.exe는 서명 대상 배포물이므로).

연결 시 `pipe.rs` 변경 예(다음 카드):
```rust
static EDITOR: std::sync::OnceLock<Mutex<editor_core::api::Engine>> = std::sync::OnceLock::new();
// handle_request 맨 앞(Value로 바꾸기 전)에서:
if val.str("cmd").is_some_and(|c| c.starts_with("edit_")) {
    return EDITOR.get_or_init(|| Mutex::new(editor_core::api::Engine::new())).lock().unwrap().handle(req_str);
}
```
(`handle`은 이미 완성된 JSON 문자열을 돌려주므로 `Value`로 다시 만들지 말고 그대로 응답에 쓴다.)

## 6. IME 경계 (Flutter가 맡는 것 / Rust가 맡는 것)
- **IME 조합(한글 입력)은 Flutter `EditableText`/`TextField`가 그대로 처리**한다. 조합 중 글자("ㅎ→하→한")는 Flutter 쪽 `TextEditingValue.composing`에 있다.
- Rust는 **확정된 변경의 기록·버퍼·이력·저장·서식**만 맡는다. 조합 중에는 Rust에 보내지 않거나, 보내더라도 `replace_range`로 조합 구간을 교체하면 같은 실행취소 묶음에 합쳐진다(시험 `hangul_composition_steps_become_one_undo`).
- 권장 흐름: 조합 확정(또는 조합 종료/공백) 때 변경분 `(start,end,text)`를 UTF-16→바이트로 변환해 `edit_replace`; 서식 단추·실행취소·찾기·저장만 Rust 호출. Ctrl+Z는 UI가 가로채 `edit_undo` 결과 텍스트를 반영(조합 중이면 먼저 확정).
- 큰 글에서 모든 글자를 파이프로 왕복하지 않도록, UI는 `TextEditingController`를 소스로 두고 Rust는 "이력/저장/검색/서식 계산"의 미러로 쓰는 안을 기본으로 한다. 두 쪽 내용이 어긋날 위험(드리프트)은 `edit_info`의 `len`/`chars`로 주기 검증하고 어긋나면 `edit_open`으로 다시 맞춘다.
- 직접 그리는 편집기(자체 커서·선택·IME)는 IME·접근성 위험 때문에 후속 검토 — TODO.md 방침과 동일.
- **한글 조합 실기 확인은 Windows에서만 가능**(이 카드는 macOS에서 코어만 시험).

## 7. 시험·성능 기록 (macOS arm64, `cargo test` 21개 + 성능 1개)
입력: 100,000줄, 6.99 MB, 4,468,890 글자(한글·영문·제목·목록·인라인 코드 혼합). `cargo test --release --test perf -- --nocapture`.

| 항목 | 시간 |
|---|---|
| 불러오기(LF 통일+줄 색인) | 11.5 ms |
| 무작위 위치 입력 4000회 | 244.6 ms (회당 61 µs) |
| 같은 위치 이어 입력 20000자 | 241.2 ms (회당 12 µs) |
| 줄·열 계산 1회 | 0.024 ms |
| 통계(줄·글자·낱말) | 12.3 ms |
| 찾기 모두 – 대소문자 구분 (80000건) | 11.3 ms |
| 찾기 모두 – 대소문자 무시 (80000건) | 31.8 ms |
| 모두 바꾸기 (80000건, 한 번의 실행취소) / 실행취소 | 33.3 ms / 7.5 ms |
| Markdown 전체 해석(100001블록) / 화면 60줄 | 38.1 ms / 0.3 ms |
| 저장(임시 파일 후 교체) / 파일 열기 | 21.1 ms / 14.1 ms |
| 4001묶음 전체 실행취소 | 236.6 ms |
| JSON 명령 1000회(삽입) | 1.2 ms (회당 1.2 µs, 파이프 제외) |

디버그 빌드(`cargo test`)에서도 성능 시험이 통과(약 7초). 파이프 왕복 지연은 포함하지 않았다(Windows 실기 측정 필요).

## 8. 남은 일 / 후속
1. klib 연결(`pipe.rs`에 `edit_*` 위임) + Dart 브리지 클라이언트 — 위 5절 결정 후.
2. `flutter_ui/lib/features/editor/` UI(도구줄, 상태 표시줄 줄·열·글자 수·줄바꿈, 자동 저장 표시, 찾기·바꾸기 막대) — UTF-16↔바이트 변환 포함.
3. 줄 색인 청크화(수십만 줄 이상 필요 시), 줄 바꿈(word wrap) 계산은 UI 쪽.
4. CP949 등 레거시 인코딩 열기(표 필요 → 별도 결정), 확대·축소는 UI 단.
5. 무작위 명령열 퍼징 확대(패닉 0 보장; klib `panic = "abort"`).

## 9. klib 연결과 메모 화면 2단계 (EDLINK, 2026-11-07, 브랜치 `feature/edlink`)

5절 A안으로 연결했다(새 exe 없음).
- **klib**: `Cargo.toml`에 `editor_core = { path = "../editor_core" }`(경로 의존성만). `pipe.rs`의 `handle_request`가 `cmd`가 `edit_`로 시작하면
  `OnceLock<Mutex<Engine>>`에 위임하고 코어의 응답 문자열을 그대로 돌려준다(자료함 DB 잠금과 무관). 시험 `test_edit_commands_delegate_to_editor_core`.
- **Python**: `library_bridge.ALLOWED_COMMANDS`에 4절의 `edit_*` 33개, `EDITOR_COMMANDS` 추가. 화면 통로는 새 브리지 메서드 대신
  `desktop_web_ui.notebook()`이 `edit_*`를 klib에 그대로 넘긴다(개발자 모드 전용). **`path` 인자는 거절**: 메모는 노트북 출처로 저장하므로
  화면에서 임의 파일을 열거나 덮어쓰는 통로를 만들지 않는다(`edit_save`·`edit_autosave`는 허용 목록에는 있으나 지금 화면 경로로는 쓸 수 없음).
- **Flutter**: `EditorCore` 경계를 넓혀(명령은 `Future`, 찾기·바꾸기·개수·줄바꿈·인코딩·엔진 이름·`changes`·`dispose`)
  `KlibEditorCore`(`klib_editor_core.dart`)를 추가. 6절 권장대로 `TextEditingController`가 원본이고 Rust는 거울이다:
  입력은 바뀐 구간만 UTF-16→UTF-8 바이트로 바꿔 `edit_replace`(요청 줄 세우기로 순서 보장), 실행취소·서식·찾기·바꾸기는 Rust에 묻고 글을 다시 받는다
  (`edit_text`가 응답 64 KiB를 넘으면 `edit_lines`로 400줄씩). 30초마다 `edit_info`로 klib를 깨워 두고 글자 수로 드리프트를 검사한다.
  klib가 문서를 잃으면(유휴 종료 후 재기동) 지금 글로 다시 열고(이전 실행취소 기록은 사라짐, 세대 번호로 중복 반영 방지),
  다시 열 수도 없으면 `DartEditorCore`로 바꿔 끼운다(klib 없음·요청 64 KiB 초과 포함). 노트북 '+메모 추가'는 `NotebookApi.memoEditorBackend`가 있으면 Rust 코어를 쓴다.
- **메모 화면 ②**: 찾기·바꾸기 막대(Ctrl+F/Ctrl+H, F3/Shift+F3, 대/소문자·온전한 낱말, 바꾸기=메모장처럼 첫 번째는 선택만, 모두 바꾸기, 일치 수,
  포커스가 없어도 찾은 구간 칠하기), 확대·축소(Ctrl+휠, Ctrl+=/−/0, 50~500%, Ctrl 누른 동안 본문 휠 스크롤 막음),
  상태 표시줄(줄·열, 글자 수, 확대 비율, 줄바꿈 `Windows (CRLF)`/`Unix (LF)`/`Macintosh (CR)`, 인코딩, 엔진 표시 도움말).
  명령이 파이프를 오가는 동안 들어온 입력은 버린다(Rust와 글이 어긋나지 않게).

### editor_core에 있으면 좋을 공개 API (이번 카드에서는 코어를 고치지 않음)
1. 거꾸로 찾기(`edit_find`에 `backward`) — 지금은 `edit_find_all`(최대 10000개)에서 고른다.
2. 개수만 세기(`edit_count`) — 지금은 일치 구간 목록 전체를 받는다. `edit_find_all`에 상한 초과 여부(`truncated`)도 필요.
3. 실행취소·다시실행·서식·모두 바꾸기 응답에 **바뀐 구간**(`start,end,text`) — 지금은 명령마다 글 전체를 다시 받는다(큰 메모에서 느림).
4. 이력 없이 글을 이어 넣는 열기(`edit_open` 나눠 보내기 또는 `edit_reset_history`) — 요청 64 KiB(Python 브리지 한도)를 넘는 메모는 지금 Dart 폴백.
5. 열린 문서 수 조회(`Engine::doc_count`) — klib 유휴 종료 감시가 편집 중 문서가 있으면 종료하지 않게(지금은 30초 깨우기로 대신).
6. 패닉 격리: klib release는 `panic = "abort"`라 코어 패닉이 자료함까지 끝낸다 — 무작위 명령열 퍼징 확대 필요(8절 5).

## 10. 자료함 '+메모'·글 자료 고치기 (LIBMEMO, 2026-11-07, 브랜치 `feature/libmemo`)

결정 단계 ④(다른 화면에서도 재사용). 노트북 동작은 그대로다.
- **Flutter**: 노트북의 메모 화면(`_MemoPage`)을 `editor/memo_editor_page.dart`의 `MemoEditorPage<T>`로 옮겨 두 화면이 같이 쓴다
  (저장 단추 이름·안내 문구·저장 동작만 다르고 키 `memo-save`·`memo-hint`는 같음).
  자료함 도구줄 `+메모`(`libraryAddMemo`): 편집기를 열고 '자료함에 저장'하면 핵심자료에 `text` 자료로 넣는다. 저장하지 않고 닫으면 초안이 남고(`+메모(초안)`), 휴지통은 초안을 버린다.
  글 자료(`text`·`note`) 더블클릭·메뉴 '열기'·검색 결과 선택은 같은 편집기로 열고 '저장'하면 그 자료의 내용과 이름을 고친다(닫기만 하면 바뀌지 않음, 휴지통 없음).
  파일·폴더·링크·서식 글(`richText`)은 이전처럼 연결 프로그램·보기 창. 새 인터페이스 `LibraryMemoApi`(`readItemText`·`updateItemText`·`memoEditorBackend`)를
  `BridgeLibraryApi`·`InMemoryLibraryApi`가 구현하고, 구현하지 않는 API면 글 자료도 이전 보기 창으로 연다.
- **klib**: `item_text_get {id}` → `content`·`display_name`·`kind`, `item_text_set {id, content, display_name?}`(이름이 비면 그대로). 경로 인자는 없고,
  `text`·`note` 종류이면서 사본이 자료함 데이터 폴더 `boxes/<box_id>/items` 바로 아래 `.txt`일 때만 읽고 쓴다(사용자 원본 보호). 쓰기는 임시 파일 후 바꿔치기,
  저장 뒤 본문 검색 색인을 다시 만든다(실패는 `index_warning`). 시험 `test_item_text_get_set_for_memo_editor`.
- **Python**: `ALLOWED_COMMANDS`에 `item_text_get`·`item_text_set`. `desktop_web_ui.library()`도 `edit_*`를 노트북과 같은 `_memo_editor_request`로 보내
  `path` 인자와 모르는 편집 명령을 거절한다(이전에는 자료함 통로로 `edit_save {path}`가 그대로 klib에 갈 수 있었음).
- **한계**: 요청 64 KiB(Python 브리지 한도)를 넘는 메모는 `item_add`·`item_text_set`이 실패한다(편집기는 Dart 폴백으로 열리지만 저장 불가 — 오류 표시).
  고치기 화면은 자동 저장 초안이 없어 저장하지 않고 닫으면 고친 내용이 사라진다.
