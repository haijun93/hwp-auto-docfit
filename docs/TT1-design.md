# TT1 설계서 — 라벨 서식 후순위·조직도 정보단위 복구

작성일: 2026-10-28. 조사 기준: `feature/alpha-tt1`, HEAD `1fc691d4d00c858587c11320f43b9ece725fee0d`.
납품 경로: `C:\HWP_AUTODOCFIT\v1803\reports\TT1-design.md`. 이 파일은 같은 내용의 Git 보관 사본이다.
상태: **설계 완료, 구현·전체 시험 미수행**. 본 작업에서 소스·시험·TODO 완료 상태는 바꾸지 않는다.

## 1. 범위와 조사 결과

TODO.md 1~12행(첫 절), 25~38행(세 번째 절)이 대상이다. 두 번째 절인 추진절차(가로세로) 재설계는 제외한다. 기본 동작으로 적용하며 기능 플래그를 추가하지 않는다. 기존 동작 변경 금지의 예외는 사용자가 이번 과제로 직접 지정한 정렬·조직도 오류 복구 범위뿐이다.

### 반드시 알아야 하는 실제 자료 차이

`git show v1.80.9:docfit_core/table_units.py`를 확인했고, 현재 파일과의 `git diff v1.80.9 -- docfit_core/table_units.py`는 비어 있다. 따라서 “1.80.9 소스의 모양 1 전용 행·열 판정”은 존재하지 않는다. 당시 코드도 모양 2(N=5)를 대표 조직도로 노출하고 생성기로 N을 바꾸는 방식이다. 행 축은 None이고 팀 수 열 축만 조절한다. 근거 없이 행 반복 기능을 새로 만들지 않는다.

읽기 전용 `_scan`·`_load`·`shape_signature` 조사 결과:

| 자료 | 이름 | 행×열 | 실제 서명 | 하단 단위 수 | 현재 문제 |
|---|---|---|---|---|---|
| 저장소 내장본 | 조직도 · 모양 1 | 5×18 | f97c6d9d4a4f2dc6 | 6 | col=None, 기존 생성기의 6행 검사도 실패 |
| PC 사용자본 | 조직도 · 모양 1 | 6×12 | 824aaef78af34c47 | 4 | col=None, 생성기에 직접 넣어도 팀 3·4 글이 유실됨 |
| PC 사용자본 | 조직도 · 모양 2 | 6×14 | b9b82a52e1e1e44e | 5 | 현재 지원, 회귀 보호 대상 |
| PC 사용자본 | 조직도 · 모양 3 | 5×18 | f97c6d9d4a4f2dc6 | 6 | 내장 모양 1과 같은 구조, 현재 지원 없음 |
| PC 사용자본 | 조직도 · 모양 4 | 6×13 | e8d5cc6f44a0fbb5 | 3 | 팀 칸 폭·병합이 불규칙, 현재 지원 없음 |

내장본: `resources/서식예시/표 서식모음.hwpx`. PC 사용자본: `C:\HWP_AUTODOCFIT\표서식모음\표 서식모음.hwpx`.
**f97c…와 12열 N=4를 같은 구조로 취급하면 안 된다.** 기존 f97c… 상수는 보존하고 824a…를 별도 구조로 등록한다. 이름만 보고 count=4를 넣으면 내장본이 깨진다. 사용자본의 모양 4도 “카탈로그의 모든 조직도 col 판정” 구조 시험에 포함되므로 누락시키지 않는다.

현재 `generate_org_chart`는 756~1055행에서 모양 2의 고정 좌표를 사용한다. 예: 팀 열 `[0,3,6,9,12]`, 상단 `(1,4)`, 팀행 4·인원행 5. 짝수 N에서는 가운데 간격이 2열이라 N=4의 팀 시작 열은 `[0,3,7,10]`이다. 고정 열 배열로 모양 1을 읽으면 뒤 두 팀을 읽지 못한다. 생성 결과를 다음 호출 원본으로 다시 쓰면 같은 문제로 연속 조절 때 내용이 손실된다. plan 등록만으로 끝낼 수 없다.

`describe_units`는 1228~1250행에서 조직도 여러 모양을 대표 1개로 합친다. 기존 시험 588~591행도 이 정책을 고정한다. 이번 복구는 **대표 1개 노출·표시 이름 “조직도” 정책을 유지**한다. 단일 모양 1만 든 사용자 카탈로그도 조절 가능하게 만들고, 원시 카탈로그의 모든 조직도에 대해 직접 plan/preview/export가 작동하게 한다. 여러 모양을 별도 카드로 늘리는 UI 변경은 이번 범위에 넣지 않는다.

즐겨찾기도 주의: 백엔드는 설정에 ID 배열을 저장하지만 응답에는 bool만 보내고, Flutter는 전체 templates에서 favorite만 거른다. 전체 목록만 정렬해도 즐겨찾기 순서가 바뀐다. 따라서 저장된 ID 순서를 별도 전달해야 한다. 최근 사용은 이미 ID 배열을 따라가므로 유지하면 된다. 검색은 현재 관련도 점수 없이 contains 필터이므로 입력 목록의 상대 순서를 그대로 보존한다.

## 2. 수정 위치 — 코더에게 넘길 TARGET

아래는 조사 HEAD의 LF 구분 줄 번호다. 파일이 바뀌었으면 함수명·주변 문장으로 해당 구간을 찾아 적용한다. 특히 screen 파일은 현재 `CRCRLF`와 빈 줄이 중복되어 PowerShell Get-Content/일부 splitlines 도구에서 줄 번호가 두 배로 보인다. 아래 screen 범위는 **바이트를 `\n`으로 나눈 실제 줄 번호**이며 전체 개행 정리를 하지 않는다. 24,000자를 넘는 파일도 변경 주변을 포함한 범위를 명시했다.

TARGET: docfit_app/table_units_service.py:20-35,157-175 — TEMPLATE_LAST_CATEGORIES·정렬 helper, list()의 templates와 favorites 응답.
TARGET: docfit_core/table_units.py:24-64,68-154,272-320,756-1055,1103-1150,1152-1200,1208-1250 — 구조 프로필·판정·생성·연속 조절 상태·preview/export/대표 선택 연결.
TARGET: tests/test_table_units_service.py:1-15,58-86,145-203 — 안정 정렬·설정 ID 순서·원본 불변 시험.
TARGET: tests/test_table_units.py:1-70,262-290,453-628,630-650,830-841 — 공통 helper, 최소값 시험 정리, 조직도 신규·회귀·구조 시험.
TARGET: flutter_ui/lib/core/api/table_units_api.dart:119-146 — TableUnitsListData.favorites의 호환 가능한 추가.
TARGET: flutter_ui/lib/features/table_units/table_units_screen.dart:273-397,797-887 — 즐겨찾기 낙관적 갱신/롤백·필터, 분류 삽입 순서 보존 확인.
TARGET: flutter_ui/test/table_units_screen_test.dart:71-151,205-279,610-649,825-855 — 목록 fixture, 순서·토글/롤백·조직도 조절 위젯 시험.
TARGET: tests/tt1_org_fixture.py:신규 전체 — 사용자형 조직도 1~4의 합성 HWPX를 임시 폴더에 만드는 시험 helper. 사용자 원본·바이너리 fixture를 커밋하지 않는다.
TARGET: TODO.md:1-12,25-38 — 구현과 전체 검증 통과 뒤 두 제목만 [완료·alpha]로 변경하고 각 절에 결과 한 줄 추가.

위 파일 외 hwp-auto-docfit.py, XML 범용 엔진, 배포 버전, 플래그, 생성 웹 자산은 수정하지 않는다. 이 문서와 공동 작업 보고 문서는 설계 전달 기록이다.

## 3. A 구현 계약

### 3.1 백엔드 한 곳에서 정렬

`TEMPLATE_LAST_CATEGORIES: tuple[str, ...] = ("라벨 서식",)`를 서비스 모듈 상수에 둔다.
새 helper: `_template_is_last(item: dict) -> bool`.
비교 키는 `"".join(str(item.get("category", "")).split())`로 모든 공백을 제거한다. 상수 쪽도 같은 규칙을 쓴다. 표시 category/name/id는 변경하지 않는다. 띄어쓰기 다른 분류를 합치는 기능은 추가하지 않는다.

list()가 기존대로 thumbnail/favorite 필드를 붙인 후 `templates = sorted(templates, key=_template_is_last)`를 딱 한 번 적용한다. Python의 안정 정렬을 사용하므로 False 항목 순서와 True 항목 순서가 각각 유지된다. 모양 번호로 재정렬하거나 category/name으로 2차 정렬하지 않는다. describe_units·catalog 스캔 순서·snapshot 지문·ID는 그대로 둔다.

응답에 `favorites: list[str]`를 추가한다. 값은 `_id_list(preferences.get("table_template_favorites"))`에서 현존 ids만 순서대로 거른 배열이다. recent의 기존 순서·최대 8개는 유지한다. `favorite()`의 추가=배열 끝 append 정책을 유지한다. templates의 bool 필드도 기존 클라이언트용으로 유지한다.

### 3.2 Flutter 순서 계약

`TableUnitsListData`에 `final List<String> favorites;`, 생성자 `this.favorites = const []`를 추가한다. fromJson은 favorites 키가 List이면 ID 순서를 그대로 읽는다. 키가 없는 이전 응답은 **입력 templates 원래 순서의 favorite=true ID**를 계산하여 사용한다. 빈 배열과 키 없음은 구별한다. recent와 같은 불필요한 정렬을 하지 않는다.

_getCategories()의 Set 삽입 순서와 선두 `즐겨찾기, 최근 사용, 전체`는 현재대로 유지한다. 정렬 로직을 넣지 않는다. 전체·분류 검색은 현재처럼 templates의 where 결과를 그대로 사용한다.

즐겨찾기 분기는 recent 분기와 같은 ID→template map을 만들고 `favorites` 순서대로 현존하고 favorite=true인 템플릿을 모은다. 라벨 서식이 첫 즐겨찾기이면 계속 첫 카드다.

_toggleFavorite에서 원래 listData(특히 favorites 배열)를 지역 변수로 보관한다. 낙관적 켬은 중복 제거 후 끝에 ID 추가, 끔은 해당 ID 제거한다. TableUnitsListData 재생성 297·371행에 favorites를 빠짐없이 전달한다. 성공은 서버 응답으로 교체하고 실패는 저장해 둔 순서를 그대로 복원한다. templates의 순서를 다시 정렬하지 않는다.

## 4. B 자료 구조와 판정 계약

### 4.1 프로필

새 불변 프로필 테이블 `ORG_CHART_PROFILES: dict[str, dict]`를 모듈 상수로 둔다. 키는 `six_even_4`, `six_odd_5`, `five_even_6`, `six_irregular_3`이다. 값에 `rows`, `cols`, `count`, `signature`, `top_row`, `connector_row`, `stem_row`, `team_row`, `count_row`, `cap_row`(없으면 None), `team_starts`, `role_sources`를 둔다. 가변 dict를 PLANS 항목끼리 공유하지 말고 매번 deepcopy한다.

| 프로필 | rows/cols/count | top/connector/stem/team/count/cap | 팀 시작 열 |
|---|---|---|---|
| six_even_4 | 6/12/4 | 1/2/3/4/5/0 | 0,3,7,10 |
| six_odd_5 | 6/14/5 | 1/2/3/4/5/0 | 0,3,6,9,12 |
| five_even_6 | 5/18/6 | 0/1/2/3/4/없음 | 0,3,6,10,13,16 |
| six_irregular_3 | 6/13/3 | 1/2/3/4/5/0 | 0,5,11 |

새 함수:

```python
def _org_chart_profile(template: dict) -> dict | None: ...
def _org_chart_plan(profile: dict) -> dict: ...
def _org_chart_source(table, profile: dict) -> dict: ...
def _generate_org_chart_from_source(source: dict, team_count: int, *,
                                    fill="increment", cell_texts=None, id_roots=()): ...
```

이름 판정만으로 프로필을 확정하지 않는다. 먼저 `rows/cols`와 계산 서명, 하단 팀행 칸의 col/colSpan 배치를 검사한다. 기본 네 프로필은 이름을 바꿔도 인식한다. 같은 이름의 다른 구조는 강제 매칭하지 않는다. 조직도 category가 아니면 일반 표와의 서명 충돌에 주의한다. f97c…는 이미 조직도 전용 서명이므로 이름 변경도 지원하되, 이름·category가 조직도인 경우 구조 검사 결과를 우선한다.

`_plans()`에 모양 1·2·3을 명시 등록한다. 모양 1의 기본은 **실제 내장본 five_even_6(count=6, f97c…)**이고 사용자 모양 1(824a…, count=4)은 `_org_chart_profile`에서 고른다. 모양 2는 b9b8…를 채운다. 모양 3은 five_even_6, 모양 4는 six_irregular_3로 등록한다. 각 org col dict는 `kind='org_chart', count=<실제 N>, min=2, max=UNIT_MAX, core=2, sep=1, profile=<키>`를 가진다. irregular_3의 core/sep는 UI 요약·호환 필드이며 일반 _resize_axis의 계산에는 사용하지 않는다. 실제 원본 팀 span은 profile/source가 보관한다. row=None을 유지한다.

`plan_for()`에서는 조직도 구조 판정을 기존 이름 폴백보다 앞에 적용한다. 성공하면 해당 프로필로 독립 plan을 만든다. 기존 `cols == 14` 단독 폴백을 삭제한다. 조직도가 아닌 표에는 기존 서명→이름→detect_plan 순서를 유지한다. `_capped`가 모든 org에 기존 공통 상한 9를 적용하게 유지한다. 사용자 모양 1을 4로 강제하는 이름 override를 넣지 않는다.

profile 내부 필드는 describe_units의 공개 units에 노출하지 않는다. 기존 공개 필드 count/min/max/core/sep/kind를 유지한다. shape_signature 함수의 알고리즘·기존 서명 상수 f97c…를 바꾸지 않는다.

### 4.2 역할 기반 원본 추출

`_org_chart_source`는 입력 XML에서 다음을 deepcopy하여 보관한다: 원본 표 전체, base_count, 원본 행 높이·폭, 위 상자 셀, 팀 셀 배열, 팀별 인원 셀 배열, 각 연결선·빈칸 역할의 prototype. 반환 자료는 메모리 내부 전용이며 API JSON이나 설정에 저장하지 않는다.

팀 셀은 프로필의 team_starts 주소를 사용하며 텍스트 존재만으로 셀을 찾지 않는다(빈 팀명도 유효). 인원 셀은 count_row에서 팀의 중심 열을 덮는 셀을 찾고, 같은 셀이 여러 팀 중심을 덮는 irregular_3은 각 팀에 동일 내용·서식을 대응시키되 원본 snapshot에는 병합을 그대로 남긴다. 마지막으로 잘못된 프로필/그리드 구멍·중복을 검사하고 명확한 ValueError를 낸다.

역할별 borderFillIDRef는 **입력 XML의 참조를 복제**한다. 번호 260, 265 등을 코드 상수로 쓰지 않는다. 프로필의 역할 좌표를 통해 참조를 가져온다. 아래는 source 셀을 찾는 주소 기준이며 source에 실제로 존재하는 셀만 선택한다.

* six_odd_5는 기존 proto 좌표를 그대로 role_sources에 옮긴다(현재 920~1032행의 proto 호출 전체가 목록이다). 이 경로의 기존 출력 구조·테두리·폭 배분을 유지한다.
* six_even_4: 상단 빈칸 (0,0), 덮개 (0,4)/(0,5)/(0,7), 위 상자 (1,4), 좌우 외곽 (1,3)/(1,8), 가로선 외곽 (2,0)/(2,11), 일반 가로선 (2,1), 상자 아래 (2,4)/(2,7), 가운데 가지 (2,5)/(2,6), 첫 줄기 (3,0)/(3,1), 내부 줄기 (3,3)/(3,4), 마지막 줄기 (3,10)/(3,11), 줄기 간격 (3,2), 팀/간격 (4,0)/(4,2), 인원/간격 (5,0)/(5,2).
* five_even_6: 위 상자 (0,6), 좌우 외곽 (0,5)/(0,12), 상단 빈칸 (0,0), 가로선 외곽 (1,0)/(1,17), 일반 가로선 (1,2), 가운데 가지 (1,6)/(1,9), 첫 줄기 (2,0)/(2,1), 내부 줄기 (2,3)/(2,4), 마지막 줄기 (2,16)/(2,17), 간격 (2,2), 팀/간격 (3,0)/(3,2), 인원/간격 (4,0)/(4,2). 덮개 행은 추가하지 않는다.
* six_irregular_3: 위 상자 (1,4), 외곽 (1,3)/(1,9), 덮개 (0,4)/(0,6)/(0,8), 빈칸 (0,0), 가로선 외곽 (2,0)/(2,12), 일반 (2,1), 상자 아래 (2,4)/(2,8), 가운데 가지 (2,6)/(2,7), 첫 줄기 (3,0)/(3,1), 내부 줄기 (3,6)/(3,7), 마지막 줄기 (3,11)/(3,12), 줄기 간격 (3,3), 팀/간격 (4,0)/(4,3), 인원/간격 (5,0)/(5,3).

각 역할은 기하학적 의미를 가진 이름(예: stem_first_left)으로 관리하고 행·열 숫자는 profile 정의에만 둔다. 같은 테두리 역할로 셀을 재사용할 때 width/span/addr는 결과 그리드 값으로 새로 정한다. 위 상자·팀명·인원 셀은 대응 원본 셀 자체를 복제하여 글자·문단 서식을 보존한다. 새 역할에서 없는 source 주소를 첫 셀로 대신하는 현재 proto fallback은 새 경로에서 금지한다.

### 4.3 생성과 왕복

기존 공개 시그니처 `generate_org_chart(template_table_element, team_count, *, fill="increment", cell_texts=None, id_roots=())`는 유지한다. 이 함수는 입력 XML에서 프로필·source를 추출해 새 private 생성기로 보낸다. 기존 six_odd_5의 알고리즘을 역할 이름으로 옮기되 원래 출력에 대한 회귀 시험을 먼저 고정한다.

새 생성기는 다음 규칙을 따른다.

1. 입력 target은 int( bool 제외 ) 2~10. resize_table 공개 경로는 plan 상한 9를 추가 적용한다. 기존 직접 생성기 2~10 계약과 resize 2~9 계약을 구별한다.
2. 기존 열 배분을 재사용한다: 각 팀 폭 가중치 8345+8345, 사이 간격 4304, 짝수 N 가운데만 2152+2152. 결과 열 수는 홀수 3N−1, 짝수 3N. 누적 정수 배분으로 원본 전체 폭 유지.
3. 결과 top/connector/stem/team/count 행은 profile의 행 수(5 또는 6)를 유지한다. 5행 입력에 가짜 덮개 행을 추가하지 않는다. 원본 행 높이를 유지한다. 상단 상자의 좌우 열 수 동일, 폭은 기존 알고리즘처럼 기준 폭의 95% 이상이 되도록 확장한다.
4. 가로선은 첫 팀 중심부터 마지막 팀 중심까지, 각 팀 중심에 세로 줄기를 놓는다. 짝수 가운데 간격 2열, 홀수 가운데 팀의 특수 연결을 기존 규칙대로 만든다. role_sources에서 해당 선의 좌/우 prototype을 선택한다. 5행 프로필은 기존 6행의 row0 cap만 생략하고 top/connector/stem 역할을 0/1/2로 대응시킨다. 결과 그리드에 각 좌표 소유자가 정확히 1개인지 검증한다.
5. i번째 기존 팀은 source의 i번째 팀 셀·인원 셀을 사용한다. 추가 팀은 마지막 원본 팀 기준으로 fill=increment/copy/blank를 적용한다. 기존 팀의 글과 혼합 run은 `_fill_clone` 등 기존 보존 helper를 사용한다. 숫자 증가를 기존 모든 팀에 재적용하지 않는다. cell_texts는 최종 그리드 좌표에 기존 검증 규칙으로 적용한다.
6. N이 base_count이면 원본 snapshot을 deepcopy하여 복원한다. 이때도 fill/cell_texts 입력 검증·cell_texts 적용은 수행한다. 이것은 원래 병합·폭·텍스트·테두리를 복원하는 정상 경로다. 무조건 return으로 시험을 피하는 분기가 아니다. base_count 외 실제 생성·증감 시험을 반드시 둔다.
7. 새 개체 ID·instId·zOrder는 기존 `_ObjectIds` 정책대로 재할당하고 문서의 기존 예약 ID와 충돌하지 않게 한다. 직접 메모리 왕복 시험의 snapshot 복원은 원본 ID를 포함해 비교한다. export에서는 원본 보존 의미 비교와 최종 문서 ID 유일성을 각각 검사한다.

resize_table의 updated org col plan 안에 private `_source`를 첫 호출에만 만들고 이후 호출에서 재사용한다. `_source`에는 원본 XML과 base_count가 있고, public count는 현재 값이다. **매 호출 현재 working을 새 기준으로 삼지 않는다.** 이를 통해 4→5→3→4 때 사라진 팀명·불규칙 원본 병합도 복원한다. plan 자체가 deepcopy되므로 실패 시 원래 table·plan 둘 다 불변이다. `_source`는 describe_units의 whitelist 밖이라 응답에 포함되지 않는다.

cell_texts를 적용한 현재 문서는 현재 결과에 반영하되 `_source` 원본을 변경하지 않는다. 기준 N으로 되돌리면 원본으로 복원하고 그 호출의 cell_texts를 적용하는 계약으로 고정한다. preview/export는 매 요청 원본을 다시 읽는 기존 계약을 유지한다.

_select_org_chart_record·describe_units는 기존 다중 모양 대표 정책을 유지하되, 대표 후보의 구조 판정이 실제 성공하는지 확인한다. 단일 모양 1도 지원한다. 내장본의 “조직도 · 모양 1” 표시 이름을 임의로 바꾸지 않는다.

## 5. 시험 자료와 시험 목록

코더는 명령을 실행할 수 없으므로 아래 순서로 **파일만 작성**한다. 실행·결과 판정·커밋·푸시는 실행 권한이 있는 검수자가 담당한다. 테스트가 사용자 PC 파일 존재 여부에 의존하거나 skip으로 통과하면 안 된다.

### 5.1 재현 fixture

`tests/tt1_org_fixture.py`에 `make_org_catalog(destination: Path, *, profiles: tuple[str, ...] = ("six_even_4", "six_odd_5", "five_even_6", "six_irregular_3")) -> Path`를 작성한다. 테스트 실행 시 TemporaryDirectory 안에 ZIP을 만든다. 코더가 바이너리를 만들거나 셸 명령을 실행할 필요가 없다. defusedxml·zipfile로 기존 내장 SOURCE의 ZIP 뼈대와 header 정의를 읽고, section0에는 `#조직도` 문단 뒤 선택한 프로필 표를 순서대로 넣는다(_scan은 # 제목 이후 표 등장 순서로 모양 번호를 만든다). 원본 section의 secPr이 있는 첫 문단은 사본에 보존하고, 다른 기존 표는 사본 section에서 제거한다. 원본 ZIP에는 쓰지 않는다.

시험용 표 모델은 **제품의 ORG_CHART_PROFILES나 제품 생성기를 호출하지 않고** 행별 `(col, colSpan, rowSpan, text, border 역할)` 데이터로 독립 정의한다. 위 구조·팀 시작 열·역할 좌표를 재현한다. header의 borderFill은 내장 정의에서 필요한 4면 조합을 복제하거나 시험 helper에서 생성하여 새 ID를 할당한다. itemCnt를 갱신하고 모든 셀 참조가 그 header에서 풀리도록 한다. 문단·글자 모양은 기존 header의 유효한 첫 정의를 사용한다. 합성 팀명은 팀1/팀2/팀3/팀4처럼 서로 구분되게 넣고 인원은 (11명)/(22명)처럼 구분한다. 서명은 내용과 무관하지만 채움 유무와 span 배치는 동일해야 하므로 생성한 각 표의 서명을 표에 적힌 값으로 검사한다. 테스트 기대 모델을 제품 생성기로 만들어 자기 자신과 비교하는 시험은 금지한다.

내장본 5×18은 기존 SOURCE로 시험한다. 사용자 구조 fixture는 6×12·6×14·5×18·6×13, 위 표의 팀 시작과 원본 병합을 재현한다. 테스트는 TemporaryDirectory에서 fixture 사본만 쓴다. 셀 정보 비교에는 header를 푼 실제 borders/style를 포함한다. XML 파서는 defusedxml만 사용한다.

### 5.2 Python 서비스 시험 — tests/test_table_units_service.py

TableUnitsServiceTests에 추가한다. `_units`를 patch하여 [A1, 라벨1, B1, 라벨2, A2] dict를 반환시키고 `_snapshot_url`도 고정 문자열로 patch한다. 콜백 COM을 실행하지 않는다.

| 시험명 | 검사 내용 |
|---|---|
| test_list_moves_label_category_last_stably | IDs가 A1,B1,A2,라벨1,라벨2. 입력 배열·각 dict도 원래와 동일 |
| test_list_normalizes_category_whitespace | 라벨서식/라벨 서식/탭·여러 공백 변형 모두 마지막, 원래 표시 문자열 유지 |
| test_list_preserves_label_shape_order | 모양1~6 사이 다른 분류를 끼워도 출력 라벨 부분 1~6 유지 |
| test_list_without_or_only_label_categories | 빈 목록·라벨 없음·라벨만 있음 모두 입력 상대 순서, ready 값의 기존 의미 유지 |
| test_list_preserves_favorites_and_recent_order | 설정 favorites=[label2,A1,label1], recent=[label1,B1,label2] 그대로. 사라진 ID 제거·recent 8개 상한, category 정렬 영향 없음 |
| test_list_orders_custom_catalog_without_mutation | 합성 사용자 카탈로그 사본으로 서비스 list, 일반·라벨 순서 및 사본 SHA-256 불변 |

### 5.3 엔진 시험 — tests/test_table_units.py

기존 `load()`가 내장본만 쓰므로 `load_from(source, name)` helper를 추가해 table/plan/header 정보를 시험에서 함께 확보한다. 내장본 setUpClass/tearDownClass 원본 bytes 비교는 유지한다. source별 테스트를 subTest로 구분한다.

| 시험명 | 검사 내용 |
|---|---|
| test_org_shape_profiles_match_actual_catalogs | 내장 모양1=5×18/count6/f97c…, fixture 모양1=6×12/count4/824a…, 모양2=count5, 모양3=count6, 모양4=count3; col.kind, row=None, min2,max9 |
| test_org_profiles_survive_rename_and_reject_unrelated_grid | 각 org 이름 변경 후 같은 plan, cols14 일반 표를 org로 오인하지 않음, 같은 이름 구조 변조 시 강제 plan 금지 |
| test_catalog_org_records_all_have_column_plan | describe_units가 아니라 `_scan`의 category==조직도 **전체**를 순회해 col non-None. 내장+fixture 1~4 모두 포함, 모양2 하나로 축약된 목록만 검사하는 편법 금지 |
| test_org_shape1_grow_shrink_and_connectors | 6×12에서 target 2,3,5,6,9; 그리드·폭·높이·N개 팀/인원·첫~끝 가로선·모든 줄기·중앙 정렬. 고유한 뒤 두 팀명도 보존 |
| test_org_shape1_roundtrip_restores_original_xml | 같은 table·plan으로 4→5→3→4, 원본 ET.tostring과 일치, plan count4; private source 유지. 5행 내장본도 6→7→2→6 왕복 |
| test_org_resize_is_atomic_at_limits | min=2,max=9는 성공, min−1/max+1/True/1.5/row_count 요청은 ValueError. table bytes와 plan(원본 XML 포함) 둘 다 불변 |
| test_org_shape2_legacy_generation_regression | 기존 test_org_chart_generation의 6행 N3/4/5/6/8 결과·테두리·중앙정렬 유지, 직접 generator N2~10 계약 유지 |
| test_org_shape3_five_rows_and_shape4_irregular_roundtrip | 5행 모양3은 증감 후에도 5행, 모양4 N3→4→2→3 원래 불규칙 병합/팀·인원 글 복원. 새 생성 결과에는 중복/누락 셀 없음 |
| test_org_fill_and_cell_texts_preserve_existing_teams | copy/blank/increment가 추가 팀에만 작용, 혼합 run 보존, cell_texts 좌표·길이 오류는 원자 거부 |
| test_org_preview_export_single_shape1_catalog | 모양1만 든 임시 HWPX로 list/preview/export. units col 있음, N5 결과 정상, 원본 hash 불변, validate_and_inspect_hwpx·ID 유일성 |
| test_org_describe_keeps_single_representative | 다중 조직도는 기존처럼 1개·이름 조직도·대표 모양2 우선. 단일 모양1도 units 있음 |

기존 283~285행 `col_count=2 ValueError`는 지우지 말고 **“2는 유효한 최솟값”** 성공 검사로 바꾼다: col 존재·min2 확인 후 resize(col_count=2), count2 및 grid 검사. 이어서 before와 plan snapshot을 저장하고 col_count=1은 ValueError·table/plan 불변을 검사한다. 시험명 `test_invalid_requests_are_atomic`은 유지할 수 있으나 주석으로 정상 경계와 거부 경계를 구별한다.

기존 test_all_adjustable_templates_min_max_and_grid의 target=(1,...)은 min2인 org에서 실패하므로 `p['min']`으로 바꾼다. 일반 축 min1 시험 의미는 유지된다. describe_units_matches_all_builtin_plans는 실제 내장 모양1 count6과 공개 필드 whitelist를 비교하도록 갱신한다. profile·_source를 API에 노출해 기대값을 맞추지 않는다.

기존 사용자 파일을 선택하거나 없으면 skip하는 조직도 시험은 fixture를 기본으로 바꾸고 기존 검사 자체는 유지한다. PC 사용자 원본 추가 대조는 별도 선택 검수이며 필수 시험을 대체하지 않는다.

### 5.4 Flutter — flutter_ui/test/table_units_screen_test.dart

sampleListData에 favorites 인자를 추가한다. 별도 정렬 완료 fixture는 템플릿 [A1,B1,label1,label2], favorites=[label2,A1], recent=[label1,B1]로 구성한다. 모의 API는 list/favorite/preview만 응답하고 thumbnails_ready=true를 써 COM·모달 자동 경로를 피한다.

* `분류 칩은 백엔드 순서이며 라벨 서식이 마지막`: categoryChip_ 키의 위젯 트리 순서가 즐겨찾기,최근 사용,전체,A,B,라벨 서식. 가로 스크롤이 필요한 경우 해당 칩을 ensureVisible한 뒤 확인. 화면상의 x좌표만으로 숨겨진 칩 순서를 판단하지 않는다.
* `전체 목록과 검색은 라벨 서식이 마지막`: 전체 카드 ID 순서와 검색으로 남은 부분집합 순서. 카드 finder는 실제 카드 하위 Text로 한정하고 상세창 중복 텍스트를 세지 않는다.
* `즐겨찾기와 최근 사용은 ID 배열 순서 유지`: favorites=[label2,A1]이면 라벨이 먼저, recent도 전달 순서. 전체 목록 정렬을 이 분기에서 반복하지 않음.
* `즐겨찾기 토글 성공과 실패는 사용자 순서를 보존`: 낙관적 append/remove, 서버 응답, 실패 롤백 순서 모두 검사. 기존 토글 시험도 유지.
* `이전 목록 응답은 favorites 없이 기존 순서로 표시`: 키 없음 호환 및 명시적 빈 배열 구별.
* `조직도 모양 1은 팀 수 조절을 표시하고 preview에 전달`: col={count:4,min:2,max:9,core:2,sep:1,kind:org_chart} 응답으로 고정 안내가 없고 ±/입력 표시, + 후 col_count5로 preview, 최소/최대 경계 버튼 상태. 행 조절은 표시하지 않음.

## 6. 파일 편집만 가능한 코더의 구현 순서

1. 위 TARGET 범위를 읽고 기존 파일 인코딩·개행을 보존한다. 새 파일은 UTF-8/CRLF. 기존 screen CRCRLF를 일괄 정리하거나 파일 전체 format을 하지 않는다.
2. 서비스 상수/helper·list 안정 정렬·favorites 응답을 작성한다. 서비스 시험을 추가한다.
3. Dart 목록 모델의 favorites 파싱을 추가하고 screen의 ID 순서 필터·낙관적 갱신·롤백을 연결한다. _getCategories에는 재정렬을 넣지 않는다. 위젯 시험을 추가한다.
4. 합성 조직도 fixture helper를 작성한다. PC 원본 절대 경로·사용자 설치 여부·한/글 실행 없이 시험이 끝나게 한다.
5. 프로필 테이블·_org_chart_profile·_org_chart_plan을 작성한다. 모양1의 두 구조를 분리하고 14열 단독 폴백을 없앤다. raw 카탈로그 구조 시험을 추가한다.
6. 기존 모양2 생성 결과를 회귀 시험으로 고정한 다음 역할/source 추출과 생성기를 작성한다. 5행·6행·불규칙3팀을 처리한다. 일반 _resize_axis는 바꾸지 않는다.
7. resize_table에서 private 원본 source를 보관하고 원자 갱신을 유지한다. preview/export/단일 모양 카탈로그를 연결한다. 왕복·오류 불변·기존 시험 경계를 정리한다.
8. 코더는 변경 파일 목록·시험명·실행 미수행을 검수자에게 보고한다. 테스트 결과를 추정하여 PASS로 쓰거나 TODO를 완료로 바꾸지 않는다.
9. 검수자가 아래 검증을 실행해 실패를 코더에게 전달한다. 코더가 파일로 수정하고 같은 검증을 다시 수행한다.
10. 모든 검증이 통과하면 TODO 첫 절·세 번째 절 제목만 [완료·alpha]로 바꾸고 실제 시험 수·결과 한 줄을 추가한다. 두 번째 절은 미착수 유지한다. 지정 브랜치 feature/alpha-tt1에 커밋하고 github→origin 순서로 푸시한다. main 배포·병합·버전 변경은 하지 않는다.

## 7. 검수자가 실행할 검증과 완료 기준

실행 위치는 이 작업 폴더. 지정 Python은 `.venv\Scripts\python.exe`이나 **현재 tt1 worktree에는 해당 파일이 없다**. 검수자가 기존 Windows 가상환경의 실제 경로를 확인해 같은 의존성을 사용한다. 전역 Python으로 실행한 설계 조사 결과를 지정 가상환경 전체 PASS라고 보고하면 안 된다.

권한 있는 검수자가 수행할 명령:

```powershell
$env:PYTHONIOENCODING='utf-8'
# 지정 가상환경이 준비된 뒤
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_table_units*.py
.\.venv\Scripts\python.exe -m unittest discover -s tests
Set-Location flutter_ui
flutter test test/table_units_screen_test.dart
flutter test
flutter analyze
```

전체 unittest에 COM 실험이 포함되어 있는지는 실행 전에 검사한다. 이번 신규 시험은 catalog/HWPX XML·FakeHwp/mock만 사용하고 사람 입력·모달·한/글 실행이 없다. 별도 실제 COM 시험을 수행한다면 `C:\HWP_AUTODOCFIT\.com-test.lock`을 획득하고 사본만 사용하며 finally에서 해제한다. 이번 과제 완료에 실제 COM 조판 시험을 요구하지 않는다.

완료 조건:

1. A 일반 목록에서 라벨 두 표기 모두 맨 뒤, 비라벨 및 라벨 모양 내부 상대 순서 유지. 분류 칩 끝=라벨, favorites/recent는 사용자 ID 순서 유지.
2. B 내장 5×18 및 사용자형 6×12 모양1 모두 조절 가능. raw 카탈로그 조직도 전체 col 있음. 모양2 기존 결과 유지, 모양3 5행 보존, fixture 모양4도 구조 시험 누락 없음.
3. 증감·원래 N 왕복·min/max·오류 불변·fill·preview/export·원본 hash·개체 ID 시험 통과. 오류를 return/pass/if True/if False/주석 처리나 skip으로 우회하지 않음.
4. Python 전체 unittest, Flutter 전체 test 및 analyze 전부 통과. 기존 실패가 발견되면 별도 원인·로그를 보고하고 전체 통과로 표시하지 않는다.
5. XML 파싱 defusedxml만, CRLF/기존 개행 보존, 사용자 문서 불변, 무관 소스 변경 없음. git diff --check와 파일별 개행 검사를 통과한다.
6. 실제 결과를 TODO 두 절에 반영하고 검증 로그·브랜치·커밋·원격 반영 결과를 보고한다.

설계 조사에서는 한/글 COM·사용자 원본 변경·전체 테스트를 수행하지 않았다. HANDOVER와 공동 작업 문서의 ★ 지시를 확인했으며, 오래된 W1~W3 구현을 이번 TT1 설계 전용 작업에 섞지 않는다.
