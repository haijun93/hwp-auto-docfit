# 노트북 기능 설계 (개발자 모드, 2026-11-05)

벤치마킹 대상: [lfnovo/open-notebook](https://github.com/lfnovo/open-notebook)(MIT). 코드는 가져오지 않고 기능 흐름만 참고한다. 코드를 직접 옮기게 되면 MIT 저작권 문구와 라이선스 전문을 오픈소스 고지에 넣는다. 'NotebookLM'은 구글 상표이므로 기능 이름·안내에 쓰지 않는다.

## 1. 목표와 원칙

- 여러 문서(출처)를 한 '노트북'에 모아 읽고, 근거를 찾고, 근거에 연결된 메모(노트)를 쓰는 연구·보고서 준비 공간.
- 폐쇄망 원칙(docs/V4_OFFLINE_DESIGN.md)을 따른다. **AI(LLM)·외부 전송 없음.** open-notebook의 AI 대화·요약·팟캐스트는 규칙 기반 기능으로 바꾸거나 제외한다.
- 처리 속도가 필요한 부분(문서 추출 결과 색인, 검색, 개요·표 추출)은 Rust(klib), 화면은 Flutter, 앱 연결은 기존 Python 브리지를 쓴다.
- 개발자 모드에서만 사이드메뉴에 '노트북' 버튼을 보인다.

## 2. open-notebook 기능 대응표

| open-notebook | 이 앱의 노트북 | 비고 |
|---|---|---|
| 여러 노트북 | 노트북 만들기·이름 바꾸기·삭제 | 같음 |
| 출처(PDF·Office·웹·영상·음성) | 출처: hwpx·hwp·docx·pdf·xlsx·pptx·txt·md, 저장한 웹 페이지(html), 자료함 자료 | 영상·음성 제외 |
| 전문·벡터 검색 | 노트북 한정 전문 검색(Tantivy: 2글자 조각·초성·오타, ko-dic 선택) | 벡터 검색 제외 |
| AI 대화(근거 인용) | **근거 찾기**: 질문 문장의 핵심어로 출처 문단을 찾아 점수순으로 모아 보여 줌(출처·쪽·문단 인용) | LLM 대신 검색 |
| AI 노트 생성 | 근거 문단을 골라 노트에 **인용 붙이기**(출처 링크 유지) | 사람이 작성 |
| 변환(요약·추출) | **규칙 기반 변환**: 개요(위계 엔진), 표 모음, 숫자·날짜 문장 모음, 핵심어 빈도 | Rust |
| 인용(Citations) | 노트의 인용을 누르면 출처 미리보기에서 해당 문단 강조 | 같음 |
| 팟캐스트 | 제외 | |
| REST API·MCP | 제외(앱 내부 파이프만) | |

## 3. 화면(Flutter, `flutter_ui/lib/features/notebook/`)

세 칸 구성(open-notebook과 같은 흐름):

1. **왼쪽 — 출처**: 출처 목록(종류 아이콘·이름·추출 상태), 추가(파일 고르기·끌어 놓기·자료함에서 가져오기), 체크로 근거 찾기 범위 선택.
2. **가운데 — 근거 찾기·미리보기**: 질문/검색어 입력 → 근거 문단 카드(출처·쪽·점수·일치 강조). 카드를 누르면 출처 미리보기, '노트에 인용' 버튼. 상단 탭으로 '변환'(개요·표·숫자 문장·핵심어) 결과 보기.
3. **오른쪽 — 노트**: 노트 목록과 편집기(일반 글 + 인용 블록). 인용 블록을 누르면 가운데에 원문 문단을 띄운다. 노트는 Markdown으로 내보내기, 한/글로 보내기는 다음 단계.

좁은 폭(1000 미만)에서는 세 칸을 탭으로 바꾼다.

## 4. 데이터(klib, SQLite + Tantivy)

- `notebook`: id, 이름, 설명, 만든·고친 시각
- `nb_source`: id, notebook_id, 종류, 원본 경로 또는 자료함 item_id, 표시 이름, 추출 상태(대기·완료·실패·사유), 문단 수, 원본 크기·수정 시각(바뀌면 다시 추출)
- `nb_paragraph`: source_id, 순번, 쪽/시트/슬라이드, 위계 수준(위계 엔진), 본문 — Tantivy 색인 대상(notebook_id로 한정)
- `nb_note`: id, notebook_id, 제목, 본문(Markdown), 고친 시각
- `nb_citation`: note_id, source_id, 문단 순번, 인용 원문 사본(원본이 바뀌어도 인용 보존)

원본 파일은 읽기만 한다. 추출은 기존 Python 추출기(타임머신 content_search의 추출 함수)를 재사용하고 문단 목록을 klib에 넘긴다.

## 5. klib 명령(파이프)

`nb_create/nb_list/nb_update/nb_delete`, `nb_source_add/nb_source_list/nb_source_remove/nb_source_paragraphs`, `nb_index`(문단 묶음 받아 색인), `nb_search`(질문 → 근거 문단, 출처 범위 필터), `nb_transform`(종류: outline·tables·numbers·keywords), `nb_note_save/nb_note_list/nb_note_delete`, `nb_export_md`.

## 6. 단계와 완료 기준

| 단계 | 내용 | 완료 기준 |
|---|---|---|
| NB1 | klib 노트북 모듈(테이블·명령·Tantivy 근거 찾기·규칙 변환) | cargo test: 근거 찾기 순위(질문 핵심어 포함 문단 우선), 출처 범위 필터, 변환 4종, 인용 보존 |
| NB2 | Python 브리지·추출 연결, Flutter 3칸 화면, 사이드메뉴 버튼(개발자 모드) | Python 브리지 시험(임시 폴더, 원본 불변), 위젯 시험(추가→근거 찾기→인용→노트 저장→내보내기), 폭 1000·1400·좁은 폭 넘침 없음 |
| NB3 | 자료함 연계(자료함 자료를 출처로·출처에서 자료함 항목 보기), 한/글 보내기 | 자료함 연계 화면 완료(2026-11-07, 아래 절) |
| NB4 | 노트 태그·태그로 거르기, 여러 출처 비교, Markdown 내보내기에 태그·출처 비교 | cargo test(태그 정리·거르기·옛 DB에 태그 표 추가·출처 비교 순서), 위젯 시험(폭 700·1000·1400) |

### NB4 노트 태그·출처 비교 (2026-11-07)

- **태그**: `nb_note_tag(note_id, tag, PRIMARY KEY(note_id,tag))` 별도 표(`CREATE TABLE IF NOT EXISTS`라 옛 DB도 열 때 표만 더해짐, 기존 노트 그대로). 노트를 지우면 태그도 함께 지워진다. 태그 정리 규칙(klib `normalize_tags`, Flutter `parseNbTags` 같음): 앞 '#' 제거, 30자, 대소문자 무시 중복 제거, 노트당 20개.
  - `nb_note_save`에 `tags`(문자열 배열)를 보내면 태그를 그 목록으로 바꾸고, 빼면 기존 태그를 둔다.
  - `nb_note_list`에 `tag`를 보내면 그 태그 노트만 낸다. 응답에 노트별 `tags`와 노트북 전체 `tags`([{tag,count}])가 있다.
- **출처 비교** `nb_compare`(notebook_id, query, source_ids?, per_source=3): 출처마다 따로 근거를 찾아(점수가 낮은 출처도 빠지지 않게) `groups`[{source_id, display_name, origin, kind, hits}]로 낸다. 근거가 있는 출처(최고 점수순) → 근거 없는 출처(빈 칸) 순. 화면은 가운데 칸 '출처 비교'에서 출처마다 한 칸씩 가로로 놓고, 근거를 누르면 미리보기에서 원문 문단을 강조한다.
- **내보내기**: 제목 아래 `태그: #가 #나` 줄. `nb_export_md`에 `compare_query`(·`compare_source_ids`·`per_source`)를 주면 `## 출처 비교: 검색어` 절을 붙인다. 화면은 마지막으로 비교한 검색어·범위를 자동으로 넣는다.

### NB3 자료함↔노트북 화면 연결 (2026-11-07)

- **자료함 → 노트북**: 자료함 항목 카드의 메뉴(오른쪽 클릭·길게 누르기·카드의 ⋮ 단추)에 '노트북에 출처로 추가'. 노트북 고르기 창(노트북이 없으면 이름을 넣어 새로 만들기) → `nb_source_from_item`(notebook_id, item_id 정수). klib가 `reused:true`를 돌려주면 "이미 '노트북' 출처에 있습니다"로 알린다. 파일 경로가 없는 글·메모 항목은 고르기 창을 열기 전에 막는다. 메뉴 항목은 `LibraryScreen(notebookApi:)`를 줄 때만 보인다.
- **노트북 → 자료함**: `nb_source_list`의 `item_id`가 있는 출처에만 '자료함에서 보기' 단추. `nb_source_item`으로 box_id·item_id를 얻어 자료함 화면(`LibraryScreen(initialBoxId, initialItemId)`)을 새 페이지로 열고 그 자료함을 골라 항목 카드를 강조한다. `found:false`면 klib 사유(예: "자료함 항목이 삭제되었습니다.")만 보이고 열지 않는다. 자료함이나 항목이 사라졌으면 자료함 화면 상태 줄에 알린다.
- 시험: `flutter_ui/test/library_notebook_link_test.dart`(가짜 API), `tests/test_notebook_service.py`의 `test_item_link_requests_from_flutter_reach_klib`, `klib/tests/test_klib.rs`.

## 7. 성능 목표

- 출처 100개·문단 5만 개에서 근거 찾기 0.2초 안(Tantivy).
- 출처 추가 시 추출은 백그라운드, 화면은 상태만 갱신.
