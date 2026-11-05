# NB-MERGE 결과 보고

브랜치 `feature/v4-nb-core`에 `feature/v4-nb-transform`을 병합하고, 노트북 변환·근거 찾기를 `nb_transform` 규칙 모듈로 하나로 모았다.

## 한 일

1. **병합**: `klib/src/main.rs`의 mod 선언 충돌을 `mod notebook;` + `mod nb_transform;` 둘 다 두는 것으로 정리. 통합 시험 `klib/tests/test_klib.rs`의 `#[path]` mod 목록에 `nb_transform` 추가.
2. **중복 제거**: `notebook::transform`의 자체 규칙(정규식 숫자 찾기, 단어 빈도 등)을 지우고 `nb_transform::{outline, tables, numbers, keywords}`를 호출하도록 바꿈. `notebook.rs`는 문단 형식 변환(`Paragraph` → `nb_transform::Para`)과 결과 형식(`TransformItem`)만 맡는다.
   - 개요: 위계 수준 `level > 0`인 문단(0은 위계 없음).
   - 표: 표 묶음마다 원문 문단을 차례로 내보내고, `score`에 1부터 세는 **표 묶음 번호**를 넣는다. 추출기가 `kind = "table"`로 표시한 문단은 표지·칸 구분이 없어도 표 행으로 본다(`Para.table` 필드 추가).
   - 숫자 문장: 설계(“숫자·날짜 문장 모음”)대로 문단을 문장으로 나눈 뒤 `nb_transform::numbers`로 거른다. 마침표 앞이 숫자면 끊지 않아 `2026. 11. 5.`, `3.5%`가 한 문장에 남는다(이전 구현은 날짜를 조각냈다).
   - 핵심어: `nb_transform::keywords`(조사·불용어 제거, 빈도순, 동률은 가나다순). 근거 위치는 핵심어가 처음 나오는 문단.
3. **근거 찾기**: `nb_search`가 질문에서 `nb_transform::query_terms`로 핵심어를 뽑아(질문어·조사 제거) 검색한다. 핵심어가 하나도 없으면 원래 질문으로 검색한다. 응답에 `terms`(뽑은 핵심어 배열)를 추가해 화면에서 일치 강조에 쓸 수 있게 했다.

## 실패 시험 4건 처리와 이유

| 시험 | 처리 | 이유 |
|---|---|---|
| `nb_transform::tests::keywords_breaks_ties_and_limits_top_n` | **시험 수정** | 입력 “예산 편성 지침 / 성과 관리 지침 / 추진 계획”에서 “지침”이 2회로 가장 많다. 시험은 1위를 “관리”로 가정했는데 빈도순 설계와 맞지 않는다. 1위 `지침(2)`, 2위는 1회 동률 중 가나다순 첫째인 `계획(1)`으로 고쳤다. |
| `nb_transform::tests::tables_accepts_explicit_table_markers_without_levels` | **코드 수정** | 표지만 있고 칸 구분이 없는 행(표 제목)은 원문 그대로 한 칸으로 둬야 한다는 시험 의도가 타당하다(표 제목임을 잃지 않음). 칸 구분이 있으면 표지를 떼고 칸으로 나눈다. |
| `nb_transform::tests::tables_keeps_marked_rows_together_and_excludes_following_prose` | **코드 수정** | 표지 행 뒤에 이어지는 구분 행은 같은 표다. 기존 코드는 ‘표지 여부가 같은 행끼리만’ 묶어서 표지 행과 다음 행이 갈렸고(4묶음), 칸 구분이 있는 표지 행에서 표지를 떼지 않았다. 묶음 조건에서 표지 여부 비교를 빼고, 표지 행은 항상 표지를 뗀 뒤 칸을 나누도록 고쳤다. |
| `notebook::tests::transforms_four_kinds` | **시험 수정** | 시험은 “정책” 빈도를 2로 가정했지만 입력에 “정책”이 3번 나온다(첫 문단 1 + 셋째 문단 2). `nb_transform`의 핵심어 빈도는 출현 횟수(문단 하나 안의 반복도 셈)이고 이는 `keywords_removes_each_requested_particle...` 시험이 정한 의미다. 기대값을 3.0으로 고쳤다. |

## 추가한 시험

- `nb_transform::tests::tables_accepts_extractor_table_flag_without_delimiters`: `table` 표시 문단이 칸 구분 없이도 표 행이 되고, 이어지는 구분 행과 한 표로 묶임.
- `notebook::tests::transforms_keep_dates_in_one_sentence_and_group_table_rows`: 공문 날짜·소수점이 문장 나누기에서 깨지지 않음, 표 묶음 번호, 알 수 없는 변환 종류는 오류.

## 시험 결과

`cargo test --manifest-path klib/Cargo.toml` (PATH 앞에 DocFitTools mingw64/bin)

- 단위 시험(src/main.rs): 33 통과, 0 실패
- 통합 시험(tests/test_klib.rs): 48 통과, 0 실패
- 경고는 기존 미사용 코드(`NotebookIndex` 등) 관련만 있음

## 남은 문제

- `notebook.rs`의 옛 `NotebookIndex`(자체 Tantivy 색인)는 `search.rs`의 `search_notebook`으로 대체되어 쓰이지 않는다(미사용 경고). 지우는 것은 이번 범위 밖이라 그대로 뒀다.
- `nb_transform`의 개요는 추출기가 넣어 주는 위계 수준에 의존한다. 현재 `nb_source_add`는 모든 문단을 `level 0`, `kind "text"`로 저장하므로 실제 문서에서 개요·표(`kind=table`)가 나오려면 NB2에서 위계 엔진·표 추출 결과를 문단에 실어야 한다.
- 표 결과의 묶음 번호를 `score`에 담았다. 화면(NB2)에서 이 의미로 묶어 보여 줘야 한다.
