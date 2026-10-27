# P7 설계서 — 2.0.1 공공 표 프리셋 정식 결합

작성일: 2026-10-28. 조사 기준: `feature/2.0.1-public-presets`, HEAD `b756ee8` (Gemini 1 초안), 부모 `ea84ccf` (main v2.0.0). 저장소 루트: `C:\HWP_AUTODOCFIT\v1803\presets`.
산출물: `C:\HWP_AUTODOCFIT\v1803\reports\P7-design.md`. Git 보관 사본: `docs/P7-design.md`.
본 작업은 설계만 수행한다. 아래 변경은 후속 코더의 구현 지시이며 현재 구현 완료를 뜻하지 않는다. 사용자 프롬프트의 제어문자가 섞인 중복 경로는 명확히 지정된 P7-design.md로 해석했다.

## 1. 범위와 판단

공공 프리셋 6개를 기존 표 템플릿 목록에 추가한다. 분류·검색·즐겨찾기·최근 사용·썸네일·정보단위 조절·글 처리·칸 글 수정·복사는 동일한 API와 화면 흐름을 사용한다. 별도 프리셋 복사 UI, HTML 클립보드, 새로운 COM 생명주기를 만들지 않는다.

새 동작은 정확한 공공 프리셋 ID 6개에 한정한다. 기존 ID의 목록 상대 순서·초기 선택·미리보기·단위 판정표·복사·스냅샷 알고리즘은 유지한다. 기존 목록 뒤에 공공 프리셋을 추가한다. 공공 카테고리만 새 분류로 보이며 기존 분류의 상대 순서도 유지한다. 기능 플래그 없이 기존 템플릿을 다른 엔진으로 옮기지 않는다.

지침 읽음: AGENTS.md, HANDOVER.md, docs/CODEX_CLAUDE_SPACING_COORDINATION.md의 ★ Claude 작업 지시. W1~W3는 과거 별도 과제이며 이번 P7 설계로 다시 구현하거나 완료 판정을 바꾸지 않는다. 코더는 파일 편집만 수행하고 명령 실행·검증·커밋/푸시는 실행 담당자가 한다.

## 2. Gemini 1 초안 검토

1. `docfit_core/public_table_presets.py:245-339`: descriptor와 직접 계산한 cell_meta만 있다. 문서에서 약속한 HWPX 생성 함수가 없다. `table_units_service.py:157-188`은 catalog 엔진만 호출하므로 현재 공공 프리셋은 사용 경로에 진입하지 못한다.
2. `public_table_presets.py:271-339`: target_rows/target_cols는 실제 격자 수인데 서비스 row_count/col_count는 반복 정보단위 수다. 간트 col.count=4는 고정 2열을 제외한 4기간, 실제 cols=6이어야 한다. 이를 그대로 넘기면 4열 표가 된다. 행도 머리글·합계행을 반복 영역으로 잡으면 늘릴 때 합계가 본문으로 복제된다.
3. `public_table_presets.py:285-300`: 0·음수를 기본값으로 덮고 bool을 허용하며 max·고정 축을 검사하지 않는다. 폭은 48000 상수에 min 1000을 적용해 합계 폭 보장이 없고 바탕 문서 본문 폭과 다를 수 있다.
4. `public_table_presets.py:304-339`: fill 처리가 없고, 늘어난 칸은 '내용 행-열'로 채운다. cell_texts 형식·범위 검사와 원본 보호 경계가 없다. id/name/cells도 기존 preview 계약에서 빠져 있다.
5. `public_table_presets.py:245-269`: units/guideline과 get_public_preset 결과가 전역 사전을 그대로 참조한다. 호출자가 수정하면 다음 요청까지 오염된다.
6. `public_table_presets.py:527-570`: header_split이 없는 표에도 기본 이중선을 넣는다. 정의형 표 첫 두 행 사이가 잘못 표시된다. 간트 inner_v 점선은 고정 설명열 사이에도 적용된다.
7. `public_table_presets.py:341-524`: 글꼴·정렬·음영만 계산한다. cellMargin, 줄간격, 자간은 HWPX에 기록되지 않는다. QA 판정은 '적 합' 포함 여부만 보면 '부적 합'도 잘못 녹색 처리할 수 있다. 값 편집 후 임의 텍스트를 자동 적합 판정하지 말아야 한다.
8. `docs/TABLE_TEMPLATE_V2_ALPHA_DESIGN.md:1-127`: COM 없이 한/글 클립보드 복사 100% 자립이라는 설명은 현행 Hwp Native 경로와 모순이다. 일반 표 생성은 COM 없이 가능하지만 복사·실제 PNG 생성은 기존 한/글 COM을 쓴다. '행안부 권장', '기재부·행안부 표준'과 특정 수치의 공식 규정 근거가 이 초안에 제시되지 않았다. P7에서는 기관 공인 표시를 제거하고 '공공 업무 예시 프리셋'으로 설명한다. 외부 규정 준수 인증으로 표현하지 않는다.
9. `tests/test_public_table_presets.py:1-93`: 6개 시험은 통과(2026-10-28, Python 3.14 가상환경, 0.003초). 셀 필드 존재와 단순 행수만 확인하며 내보내기·재파싱·서비스·캐시·복사·UI 회귀는 검사하지 않는다. 합격 범위를 확장해야 한다.

## 3. 편집 대상과 정확한 기준 위치

아래 행 번호는 HEAD b756ee8 기준이며 편집 이후에는 함수명 앵커로 찾는다. 24,000자 초과 파일은 넉넉한 문맥 범위를 적었다. TARGET은 저장소 상대 경로다. 새 파일은 생성 위치 1행이다.

TARGET: docfit_core/public_table_presets.py:1-570
TARGET: docfit_app/table_units_service.py:17-188,251-291
TARGET: flutter_ui/lib/core/api/table_units_api.dart:65-127
TARGET: flutter_ui/lib/features/table_units/table_units_screen.dart:1593-1781,2697-2905,4097-4350
TARGET: tests/test_public_table_presets.py:1-93
TARGET: tests/test_table_units_service.py:1-203
TARGET: flutter_ui/test/table_units_screen_test.dart:1-855
TARGET: docs/TABLE_TEMPLATE_V2_ALPHA_DESIGN.md:1-127

추가 코드 파일은 만들지 않는다. `table_units.py`(54,185자), `table_catalog.py`(50,002자), `table_builder.py`는 참조 전용이다. 특히 PLANS, detect_plan, resize_table, fingerprint, 공유 builder의 제한을 P7을 위해 변경하지 않는다. 화면 파일은 56,213자/5764행이며 빈 줄을 대량 정리하지 않는다.

참조 전용 핵심 위치:
- `docfit_core/table_units.py:562-604`: validate_input, _apply_texts (200칸/1000자, 실제 좌표).
- `docfit_core/table_units.py:605-755,1103-1200`: 반복 단위 복제, resize_table, export/preview 계약.
- `docfit_core/table_catalog.py:140-215,324-407`: header 해석, cell_meta 추출.
- `docfit_core/table_builder.py:144-202,211-379,589-654`: 기본 grid HWPX 생성, 헤더 풀, 셀 생성, ZIP 저장.
- `docfit_app/table_units_service.py:203-249`: copy job 및 표 컨트롤 복사, 수정하지 않는다.
- 화면 `table_units_screen.dart:277-539,821-1065,1309-1437,3389-3905,4901-5109`: 자동 썸네일 생성·선택·미리보기·복사·사진 폴백·스테퍼 연결을 유지한다.

## 4. 자료 구조 및 단위 계약

프리셋 정의의 id/name/category/default_rows/default_cols/col_ratios/margins_hwpunit/guideline/sample_rows/borders는 유지한다. units는 반드시 내부 plan에 start까지 포함한 깊은 복사로 보관한다. descriptor에서는 기존과 같이 count/min/max/core/sep만 노출한다. 추가 필드: header_rows:int, footer_rows:int, line_spacing:int, char_spacing:int. style의 공통 기본값은 한곳에서 결정하고 실제 HWPX에 기록한다.

공공 6개에만 적용할 반복 계획:

| ID 끝부분 | 기본 실제 rows×cols | row start/count/min/max | col start/count/min/max | 고정 머리/끝행 |
| --- | --- | --- | --- | --- |
| summary_headline | 1×1 | null | null | 0/0 |
| two_col_definition | 4×2 | 0/4/1/30 | null | 0/0 |
| multi_col_comparison | 5×4 | 1/3/1/30 | null | 1/1 |
| gantt_timeline | 5×6 | 1/4/1/30 | 2/4/2/12 | 1/0 |
| budget_breakdown | 5×5 | 1/3/1/30 | null | 1/1 |
| qa_checklist | 4×4 | 1/3/1/30 | null | 1/0 |

모든 ID에는 `pub_` 접두사가 붙는다. 모든 활성 축은 core=1, sep=0. 실제 행수=머리행+요청 row_count+끝행(고정표 제외), 간트 실제 열수=2+col_count. null 입력은 기본 반복 수다. 고정 축에 값을 주면 기본과 같아도 ValueError. bool/float/문자/0/음수/범위 초과도 ValueError. summary는 명칭대로 1×1 고정으로 확정한다. 기존 초안의 summary row 확장은 삭제한다(아직 제품 연결 전 초안만 변경).

descriptor: 기존 필드에 `badge: str`, `description: str`, `guideline: dict[str,str]`를 추가한다. category는 '공공 표준'. badge는 기관 인증 표현 없는 용도명으로 바꾼다. 원본 사전·중첩 사전·리스트는 반환하지 않고 deepcopy한다. 미등록 ID는 is_public_preset=False, get_public_preset=None, 생성 함수는 ValueError. 접두사 검사로 라우팅하지 않는다.

preview: `{id,name,rows,cols,cells:list[list[str]],cell_meta:list[list[dict]],guideline}`. cell_meta는 catalog._cell_meta와 같은 row/col/rowSpan/colSpan/width/height/text/align/style/borders/shapes 계약이다. 미리보기 표시 글은 기존 preview처럼 공백 정규화 후 80자로 제한하되 내보낸 원문은 1000자까지 보존한다. guideline은 문자열 4개(margins/borders/font/fill)만 UI에 전달한다.

## 5. public_table_presets.py 구현 명세

### 5.1 함수 시그니처

기존 get_public_preset_descriptors(), is_public_preset(template_id: str)->bool, get_public_preset(template_id: str)->dict[str,Any]|None은 유지하되 깊은 복사를 보장한다.

새 공개 함수:

```python
def public_preset_plan(preset_id: str) -> dict[str, Any]: ...
def preview_public_preset(preset_id: str, row_count: int | None = None,
    col_count: int | None = None, *, fill: str = "increment",
    cell_texts: dict[str, str] | None = None) -> dict[str, Any]: ...
def export_public_preset(preset_id: str, output_path: str | Path,
    row_count: int | None = None, col_count: int | None = None, *,
    fill: str = "increment", cell_texts: dict[str, str] | None = None) -> Path: ...
def public_preset_snapshot_key(preset_id: str) -> str: ...
```

기존 `build_public_preset_preview(preset_id, target_rows=None, target_cols=None, cell_texts=None)`는 호환용으로 유지한다. 이 함수의 target_*는 실제 격자 크기다. 머리/끝행, 간트 고정열을 빼서 반복 count로 변환해 preview_public_preset으로 위임한다. 음수·0은 거부하며 고정축의 기본 실제 크기는 None으로 변환하고 다른 크기는 거부한다. 서비스는 반드시 새 preview_public_preset을 호출한다.

내부 함수:

```python
def _build_public_document(preset_id: str, row_count: int | None,
    col_count: int | None, *, fill: str, cell_texts: dict[str,str] | None
    ) -> tuple[dict[str, bytes], Any, Any]: ...
def _apply_public_style(table: Any, header: Any, preset: dict[str,Any],
    body_width: int) -> None: ...
def _public_para(pool: Any, align: str, line_spacing: int,
    cache: dict[tuple[str,int],str]) -> str: ...
def _write_public_package(contents: dict[str,bytes], table: Any,
    header: Any, target: Path) -> Path: ...
```

_build_public_document의 반환값은 ZIP 멤버 bytes 사전, section0 안의 table 요소, header 요소다. contents의 section0은 resize/style 완료 뒤 직렬화해 갱신한다. preview와 export가 동일 빌드 함수의 결과를 사용해 별도 셀 계산을 없앤다. Any는 ElementTree 요소를 뜻하며 구현 시 적절한 타입 별칭을 붙여도 된다.

### 5.2 생성 순서 (공통 builder를 고치지 않는 구현)

1. preset 존재 및 table_units.validate_input(fill,cell_texts)를 먼저 검증한다. plan 깊은 복사로 count/고정축을 검사한다. 잘못된 요청으로 출력 파일이나 COM을 만들지 않는다.
2. 바탕은 `Path(__file__).resolve().parents[1]/"resources"/"서식예시"/"기본 서식.hwpx"` 내장 파일로 고정한다. 사용자 표 모음이나 기본 서식 경로를 받지 않는다. 내장 파일은 읽기만 한다. 누락 시 OSError를 그대로 서비스가 변환하게 한다.
3. TemporaryDirectory 안에서 table_builder.build_table_hwpx에 기본 크기의 sample_rows만 전달한다. spec은 kind='grid', use_basic_style=False, header_rows는 정의값(0 또는1). basic_style=None. MAX_COLS=12는 기본 6열 생성에만 걸리므로 간트 14열 최종 결과를 막지 않는다. 1000자 사용자 편집은 builder를 통과시키지 않고 이후 resize_table에서 적용한다. 샘플은 200자 이하로 유지한다.
4. 생성 HWPX를 open_hwpx_safely로 읽고 dict[filename,bytes]로 보관한다. defusedxml.ElementTree로 Contents/header.xml 및 Contents/section0.xml을 파싱하고 최상위 표 1개를 얻는다. 내장 바탕은 단일 section임을 검사한다. 사용자가 준 다중 section 문서를 임의로 줄이는 경로는 만들지 않는다.
5. table_units.resize_table(table, deepcopied_plan, row_count,col_count,id_roots=(header,section),fill=fill,cell_texts=cell_texts)를 호출한다. 이로써 고정 머리/합계행을 보존하고 마지막 본문 단위를 기존 규칙대로 복제한다. blank/copy/increment는 추가된 단위에만 적용하고 원래 샘플은 유지한다. 별도 '내용 n-m' 생성은 제거한다. cell_texts는 조절 후 적용되며 범위를 벗어나면 실패한다.
6. _apply_public_style로 최종 좌표에 스타일을 재적용한다. 줄어든 끝행 테두리·늘어난 본문 음영을 이 단계에서 바로잡는다. 텍스트는 다시 쓰지 않는다. 기본 열 비율을 본문 폭에 맞춰 정수 분배한다. 마지막 열은 body_width - 앞 열 합계로 두어 폭 합을 정확히 보장한다. 간트는 고정열 24%/20%를 유지하고 나머지 56%를 기간 개수로 균등 분배한다. 일반 프리셋은 고정 비율을 쓴다. tc cellSz와 tbl sz.width를 함께 갱신한다.
7. table_builder._Header(header)의 char/border/_append를 재사용한다(읽기 전용 의존). char는 size pt×100, char_spacing(요약 -5, 나머지 0)을 전달한다. border에는 float를 직접 넣지 말고 (type, '0.12 mm', '#색') 튜플로 변환한다. _public_para는 id=0 문단 모양을 deepcopy해 align.horizontal 및 lineSpacing type=PERCENT/value를 설정하고 _append('paraProperties',clone)로 참조를 추가한다. 캐시는 요청 내부에만 둔다. 요약 line_spacing=140, 나머지=130으로 명시하고 guideline도 이 값과 맞춘다. 기본 builder.center_para()를 바꾸지 않는다.
8. tc hasMargin=1, cellMargin left/right/top/bottom에 정의값을 기록한다. tbl inMargin도 같은 값으로 맞춘다. 모든 셀의 run charPrIDRef·문단 paraPrIDRef를 갱신하고 linesegarray를 제거한다. 머리행이 있는 표만 첫 행 header=1, 나머지=0. 합계행은 마지막 1행에만 합계 스타일, 정의형 첫 행은 본문과 같은 역할이다. 불필요한 기본 builder 서식 정의는 남아도 되지만 참조는 모두 유효해야 한다.
9. _resolve_cell_borders는 header_split 없는 경우 inner_h를 쓰도록 수정한다. 간트 점선은 기간 영역 내부 경계에만 적용한다. 고정 설명열 내부·설명열/기간 경계는 0.12mm 실선으로 둔다. 이웃 두 셀의 공유 변은 같은 규격이다. 상하 외곽·머리글 이중선·예산 최하단 이중선은 초안의 수치를 유지한다.
10. QA 결과는 strip한 명확한 적합 샘플 '적 합 (☑)'/'적합'/'☑'/'Pass'만 녹색, '보완 요망'/'부적합'/'부적 합'은 적색, 그 밖의 사용자 글과 빈칸은 검정/흰색으로 둔다. 원문은 바꾸지 않는다. 금액은 예시 문자열의 콤마와 RIGHT 정렬을 유지하며 합계 계산/사용자 숫자 재포맷 기능은 넣지 않는다.
11. _serialize로 header/section을 bytes로 갱신한다. Preview/PrvText.txt는 완성 표의 전체 셀 글에서 재생성하고, 바탕의 Preview/PrvImage.png가 있으면 제거해 이전 문서 사진이 남지 않게 한다. manifest에 그 이미지가 등록돼 있으면 해당 preview 항목도 제거한다. 기본 문서의 섹션/스타일 참조·mimetype·container/content.hpf를 보존한다.
12. preview_public_preset은 완성 table/header를 catalog._header_lookup/_cell_meta로 해석한다. public snapshot 키와 preview는 ZIP 시간에 의존하지 않는다. export는 같은 contents를 ZIP으로 쓴다. mimetype은 첫 항목 ZIP_STORED. target과 내장 base가 resolve 또는 samefile로 같으면 거부하고, 형제 임시 파일을 만든 뒤 안전 재파싱/최상위 표1개/스타일 참조 검사 성공 후 replace한다. 실패 시 기존 target 및 base는 그대로, 임시 파일은 삭제한다. 경로·ZIP/XML 검사는 기존 safe helper를 사용한다.

### 5.3 스냅샷 키

PUBLIC_PRESET_REVISION='p7-v1' 상수를 둔다. public_preset_snapshot_key는 `_build_public_document`의 기본 요청 결과에서 최종 table과 header의 tag/sorted attributes/text/tail을 튜플 순회해 SHA256(UTF-8)로 계산한다. 접두사 직렬화·ZIP 타임스탬프에 의존하지 않는다. revision도 입력에 넣고 20자리 hex를 반환한다. 기본 preset 표·폰트·문단·선·여백 또는 내장 바탕의 페이지 정보 변화가 키에 반영되도록 section의 pagePr도 포함한다. 파일 읽기만 하는 list에서 같은 키를 매번 재생성하지 않도록 서비스 인스턴스에 `(preset_id, revision, 내장 바탕 bytes SHA256)`→key 캐시를 둔다. 내용 변경 시 revision도 올리는 유지 규칙을 문서에 명시한다.

## 6. 서비스 연결

기존 함수 시그니처와 command action/payload, api_version=1은 변경하지 않는다.

- import에 public_table_presets 모듈을 추가한다.
- `_units:157-161`: 기존 describe_units(self.source)의 오류 처리를 그대로 두고 성공 결과 뒤에 get_public_preset_descriptors()를 더한다. 기존 catalog 손상 시 공공 목록만 조용히 반환하는 폴백은 만들지 않는다. 기존 오류 CATALOG_UNAVAILABLE을 보존한다. 즐겨찾기 검증은 이 합친 목록을 그대로 이용한다.
- `list:163-173`: 같은 루프로 신규 descriptor를 처리한다. 기존 첫 항목·최근8개·favorite·source 계약은 유지한다. 공공 6개는 고정 순서 ①~⑥으로 뒤에 붙는다.
- `preview:175-180`: try 안에서 is_public_preset(str(template_id))이면 preview_public_preset으로 분기, 아니면 원래 table_units.preview 호출문을 유지한다. `_export:182-188`도 export_public_preset으로 같은 분기한다. 정확히 등록된 ID만 공공 엔진을 타야 한다. unknown pub_*도 기존 INVALID_INPUT으로 끝난다. 신규 내장 base OSError는 공공 경로에서만 ServiceError('PRESET_UNAVAILABLE', 읽을 수 없는 내장 양식 안내)로 변환한다. legacy 예외 의미를 넓혀 바꾸지 않는다.
- `_snapshot_path:134-139`: 공공일 때 `<snapshot_root 또는 USER_CATALOG.parent/.스냅샷>/public/<key>.png` 반환 후 기존 코드는 유지한다. 새 내부 helper `_public_snapshot_key(self,template_id: str)->str`로 위 캐시를 사용한다.
- `_bundled_snapshot:141-144`: 공공은 None. 이번 소스 편집 작업에서 가짜 PNG/base64 그림이나 바이너리 동봉을 만들지 않는다. 실제 그림은 기존 thumbnails 경로로 생성한다.
- `_snapshot_url:146-155`: 공공은 공공 path만 읽고 없으면 None 반환한다. 기존 catalog의 legacy 폴더로 폴백하지 않는다. 기존 ID의 캐시/내장그림 우선순위는 그대로 둔다.
- `thumbnails:251-291`: 공공 PNG 저장은 picture.save/replace를 try/finally로 감싸 해당 public .tmp가 실패 후 남지 않게 한다(완성 PNG를 실패 결과로 지우지는 않는다). 기존 missing 항목 계산→_export→한/글 PDF→crop→PNG 임시파일 replace를 그대로 재사용한다. 공공 폴더명 'public'(6자)은 기존 오래된 해시폴더 청소(16자)에 걸리지 않는다. 기존 SNAPSHOT_REVISION/_digest/_table_fingerprint/_content_keys는 수정하지 않는다. public 캐시 누락 시 새 6건만 생성하고 기존 내장 그림을 재생성하지 않아야 한다.
- `copy:217-249`, start_copy_job, command의 입력 검증은 변경하지 않는다. 내보내기만 라우팅하고 숨긴 한/글 Open→표 컨트롤 찾기→SetPosBySet→FindCtrl→Copy→Clear/Quit→Hwp Native 확인→최근 목록 갱신→활성화 순서를 공통 사용한다. SelectAll로 바꾸지 않는다. 실패 시 최근 목록은 유지된다.

새 공공 PNG 캐시가 없는 첫 실행은 thumbnails_ready=False이며 기존 화면의 자동 1회 생성이 작동한다. 이는 기존 ready의 '모든 목록 항목에 사진 있음' 정의를 그대로 적용한 결과다. 한/글 부재 시 기존 오류 표시와 구조 미리보기 폴백을 사용한다. 기존 내장 항목의 사진이 없어졌다고 처리하지 않는다. 공공 6개까지 첫 실행부터 COM 없이 실제 PNG가 필요하다는 추가 요구가 생기면 실측 PNG 동봉을 별도 작업으로 다룬다.

## 7. Flutter 변경 (공통 흐름 유지)

`core/api/table_units_api.dart:65-127` TableTemplateInfo 생성자에 선택 필드를 추가한다:
`this.badge='', this.description='', this.guideline=const <String,String>{}`.
각 final String/String/Map<String,String> 필드, copyWith의 선택 인자, fromJson 변환을 함께 추가한다. guideline이 Map이면 문자열 key/value만 복사하고 아니면 빈 맵. 오래된 응답/테스트의 필드 누락은 빈 기본값이다. 기존 UnitAxis/TableUnits/TablePreview/요청 payload를 변경하지 않는다.

`table_units_screen.dart:1593-1781`: _getCategories/_getFilteredTemplates의 일반 목록 경로를 그대로 사용한다. 별도 '공공 프리셋 모드'를 만들지 않는다. badge/description 검색으로 기존 검색 범위를 넓히지 않는다. 공공 category가 descriptor로 들어오므로 칩은 자동 생성된다.

`2697-2905` 기존 categoryChip_$cat 만드는 분기에서 공공 표준에만 Icons.account_balance(16px)를 텍스트 왼쪽에 표시한다. 문자열/칩 key는 '공공 표준'을 유지한다. emoji를 카테고리 값에 넣지 않는다. 다른 칩 UI는 유지한다.

`4097-4350` _buildDetail 이름/크기 안내 다음, 기존 미리보기/스테퍼보다 앞에 메타 안내를 넣는다. 새 함수 `Widget _buildPresetGuideline(TableTemplateInfo template)`를 _buildDetail 직전에 추가한다. badge/description/guideline이 모두 비면 SizedBox.shrink. 설명과 4개 guideline 항목을 있는 것만 Text로 출력하며 줄바꿈 가능 Column/Wrap을 사용한다. Key('publicPresetGuideline')은 공공 템플릿 가이드의 최상위에 둔다. 비공공 데이터의 선택 필드가 없는 경우 기존 화면과 같다.

화면의 _selectTemplate/_requestPreview/_copyTable/스테퍼/셀 편집/fill 선택/즐겨찾기·최근 사용/자동 스냅샷 생성/응답 순번 무시 로직은 그대로 쓴다. fixed summary는 기존 isFixed 분기로 -/+가 나타나지 않는다. 간트의 +1 요청은 col_count=5이며 응답 cols=7이어야 한다. UI에서 +2 보정하거나 별도 실제 열수를 상태에 저장하지 않는다.

## 8. 구현 순서 (코더는 명령 없이 파일 편집만)

1. public_table_presets.py 정의·plan·딥카피·검증 계약과 기존 호환 wrapper부터 수정한다. 기관 공인 배지는 용도 배지로 바꾸고 수치 안내와 실제 속성 값을 일치시킨다.
2. 동일 모듈에 공통 HWPX 생성·스타일·preview/export·snapshot key 함수를 구현한다. 외부 명령, COM, OS 글꼴 검색을 새 순수 코어 경로에 넣지 않는다. 기존 builder에는 모든 기본 style font를 FONTS 안의 값으로 명시한다.
3. test_public_table_presets.py에 아래 순수 XML/ZIP 시험을 추가한다. 초안의 target_rows=6 호환 시험은 유지한다.
4. 서비스 라우팅과 public snapshot 분기만 추가하고 기존 경로 본문은 유지한다. test_table_units_service.py의 legacy 전용 검증과 public 통합 검증을 분리한다.
5. Dart 모델의 선택 필드를 먼저 추가하고 화면의 아이콘·가이드만 연결한다. 기존 generic 흐름에 새 ID를 흘리는 UI 시험을 추가한다.
6. TABLE_TEMPLATE_V2_ALPHA_DESIGN.md를 2.0.1 계약으로 갱신한다. 본 설계의 단위 표·COM 의존성·캐시 정책·인증 아닌 예시 문구를 반영한다. 설계상의 가상 클래스 계층과 실제 존재하지 않는 toHwpxXml 선언을 제거하고 실제 함수명을 기록한다.
7. 코더는 변경 파일 목록과 미실행 검증 항목을 실행 담당자에게 전달한다. 실행 담당자가 검사하고 실패를 정확한 시험명/출력과 함께 코더에게 돌려준다. 편법 return/pass/상수 조건/주석 처리/skip 추가로 합격시키지 않는다.

## 9. 작성할 자동 시험

모든 Python 시험은 unittest, TemporaryDirectory와 defusedxml를 사용한다. 새 시험은 사람 입력, 실제 한/글, 실제 클립보드, 화면 포커스 전환을 일절 필요로 하지 않는다. 기존 FakeHwp 및 주입 factory/clipboard_formats/activator를 재사용한다. 실제 COM 검증은 이 단위 시험과 별도다.

### tests/test_public_table_presets.py (PublicTablePresetsTest에 추가)

- `test_descriptors_and_getter_are_deep_copies`: units/guideline/샘플을 바꾼 반환값이 다음 요청에 영향을 주지 않는다. 정확한 ID6개·순서·카테고리·새 count를 검사한다.
- `test_unit_counts_exclude_header_footer_and_fixed_columns`: 위 표 전체 기본값, 비교/예산 row_count=4→실제6행·합계1개, 간트 col_count=5→7열, QA row_count=4→5행, summary 고정1×1.
- `test_invalid_counts_and_fixed_axes_fail_without_output`: bool/float/문자/0/음수/min-1/max+1/고정축/unknown pub ID를 preview와 export에 같은 subTest로 적용한다. output이 생성되지 않고 기존 target bytes도 불변이다.
- `test_legacy_preview_wrapper_uses_physical_dimensions`: 정의형 target_rows=6→6행, 간트 target_cols=7→7열, row_count형 새 함수와 동등, 0/잘못된 고정열 거부.
- `test_fill_modes_and_text_overrides_match_export`: 세 fill 모드에서 늘어난 본문만 copy/blank/increment 처리, 예산 합계1개·머리행 보존, QA 연번 확장, 간트 기간 머리글 숫자 확장, cell_texts를 마지막에 적용한다. 원래 샘플은 변하지 않는다.
- `test_text_validation_and_multiline_roundtrip`: 1000자·한글·&<>·줄바꿈·탭 보존, 1001자/제어문자/201칸/잘못된 좌표/조절 후 범위 밖 좌표 거부. 문서 텍스트는 전체, preview만80자라는 차이를 검사한다.
- `test_all_six_exports_reparse_as_single_table`: 실제 ZIP 생성→safe open→catalog/table_units.preview('0:0' 같은 ID를 하드코딩하지 말고 _scan 결과의 첫 ID 사용)로 재파싱. 최상위 표1개·행열·셀 좌표·전체폭·폰트/문단/선 참조·itemCnt·mimetype 저장방식 검사. 원본 base SHA256 불변.
- `test_preview_and_export_have_identical_cell_metadata`: 각 preset 기본/최소/최대·간트 두 축 동시 변경에 대해 public preview와 내보내기 재파싱의 cell_meta를 비교한다(id/name/guideline 제외). 색/테두리 float와 문자열 폭은 mm 값으로 정규화해 비교하고 실제 텍스트 잘림 규칙은 동일하게 맞춘다.
- `test_public_metrics_are_written_to_xml`: 1134/708/340/283 여백, summary 자간 -5/줄간격140, 나머지130, LEFT/CENTER/RIGHT, pt×100, NONE·DOUBLE_SLIM·DOT와 색상, 반복 머리글 속성을 원시 XML에서 검사한다.
- `test_definition_has_no_implicit_header_double_border`: 정의형 첫 두 행 공유변은 inner_h 실선, summary는 좌우 NONE. 간트 고정열 사이는 SOLID, 기간 내부는 DOT.
- `test_footer_styles_and_qa_status_after_resize`: 비교·예산 footer 스타일은 마지막에만, 본문 지브라 최종좌표 재계산, 부적합/임의글/빈글이 적합 녹색이 아님.
- `test_gantt_max_columns_keep_total_width`: col_count=12→실제14열, row_count=30→31행, 열 너비 모두 양수·정수, 합계=tbl width=본문폭. 기존 builder MAX_COLS를 수정하지 않고 성공해야 한다.
- `test_snapshot_key_is_deterministic_and_tracks_styles`: 같은 정의/바탕에서 키 동일, ET 접두사 등록·ZIP 시간 차이 무관, 내용·header 스타일·여백·pagePr·revision 변화는 키 변경. 미등록 ID 거부.
- `test_export_failure_preserves_target_and_base`: _serialize/ZIP 검증/replace 실패 patch, 대상 기존 bytes 불변·임시파일 없음·원본 동일; base와 같은 경로/하드링크 출력 거부.

### tests/test_table_units_service.py

기존 FakeHwp를 유지한다. public 추가로 전체 template 개수가 늘어난 것을 반영하되 기존 시험을 지우지 않는다. BundledSnapshotTests 두 시험은 `_units`를 legacy describe_units 결과로 patch해 '내장 그림은 COM 없이 준비됨'의 기존 단언을 보존한다. 별도 혼합 목록 시험에서 새 public의 캐시 없는 상태를 검사한다. 템플릿 개수 하드코딩 대신 legacy개수+6을 검사한다.

- `test_public_presets_append_without_changing_legacy_descriptors`: describe_units baseline과 서비스 앞부분의 id/name/category/units/thumbnail 비교, 기존 첫 항목 그대로, 뒤 공공6개, category 정확성.
- `test_public_preview_and_export_route_by_exact_id`: 6개 신규 엔진 호출/legacy 원함수 호출, 알 수 없는 pub_는 INVALID_INPUT. _export 실제 결과 재파싱으로 stub 반환만 검사하지 않는다.
- `test_public_copy_uses_existing_hwp_native_sequence`: 6개 모두 FakeHwp.Open 시점에 파일 ZIP 읽어 표 존재 확인; 기존 표 선택→Copy→Clear/Quit·Native 검사·임시 폴더 삭제. SelectAll 없음. clipboard 누락/HeadCtrl 없음/Open=False 시 오류와 최근목록 불변.
- `test_public_favorite_recent_persist_with_legacy_ids`: 혼합9개 복사·중복 제거·최근8개·설정 재생성·즐겨찾기 해제 확인.
- `test_public_snapshots_use_separate_content_cache`: public/path·키·legacy fingerprint 경로 구분, catalog 파일 변경으로 public 키가 바뀌지 않음, preset 스타일 변경은 public 키만 바뀜, legacy 키·내장 그림이 그대로.
- `test_public_thumbnails_generate_once_and_preserve_bundled_legacy`: 실제 기존 내장 그림을 사용하고 빈 snapshot_root, 처음 ready=False/public6개만 없음→가짜 PDF 저장6회→ready=True→재호출0회. pypdfium2 사용 또는 PDF/render/crop을 정해진 fake로 patch해 무인 종료. 기존 그림 bytes 불변. public 캐시가 legacy old-folder 청소 뒤에도 남는다.
- `test_failed_public_thumbnail_does_not_leave_png_or_lose_legacy_cache`: PDF 변환·render·save 실패 각각 patch, .tmp/완성 PNG를 성공처럼 남기지 않음, app 종료·임시문서 정리, legacy 캐시 보존.
- `test_public_errors_are_api_errors_before_hwp_launch`: 잘못된 단위/fill/좌표/unknown ID는 factory 호출0, base 누락은 PRESET_UNAVAILABLE, legacy catalog 오류는 기존 CATALOG_UNAVAILABLE.

### flutter_ui/test/table_units_screen_test.dart

기존 sampleListData 기본3개는 유지하고, 선택적 `includePublic=false` 인자를 추가해 공공 fixture6개를 뒤에 추가한다. API callback은 기존 envelope를 사용한다. 실 API·COM을 호출하지 않는다. key는 기존 categoryChip_공공 표준/templateCard_<id>/tableGridPreview와 새 publicPresetGuideline을 쓴다.

- `공공 분류는 기존 분류와 함께 나타나고 여섯 프리셋을 필터링한다`: 칩/아이콘·ID6개·검색 '공공'·전체 복귀, 최초 선택은 기존 첫 항목.
- `공공 모델의 선택 메타 필드는 이전 응답과 호환된다`: TableTemplateInfo.fromJson/copyWith에 badge/description/guideline 보존, 필드 없는 기존 응답 기본값, 비맵/비문자 guideline 무시.
- `공공 가이드 표시 후 기존 표 선택 시 사라진다`: 색/폰트/여백 안내4개, 420px와1280px 오버플로 없음, 기존 상세 스테퍼/미리보기 유지.
- `공공 간트 열 더하기는 정보단위 수를 전송한다`: 초기 count4/실제6열 fixture, +1→payload col_count5/응답7열, copy에도 같은 count와 fill/cell_texts 전달. 고정 설명열 보정은 서버만 담당.
- `공공 요약은 기존 고정표 조작을 사용한다`: row/col null, -/+ 없음, 정상 preview/copy.
- `공공 표도 즐겨찾기 최근사용과 복사 오류를 공유한다`: favorite 요청 ID·최근분류·copy 실패 안내, 성공 메시지는 기존 문구.
- `공공 썸네일 누락은 기존 자동 생성 한 번과 구조 폴백을 사용한다`: ready=False→thumbnails1회→PNG 표시, 실패 시 spinner 종료·구조 preview 유지·자동 무한 재시도 없음. 기존 템플릿 사진 계속 보임.
- `공공 미리보기의 늦은 응답은 다음 선택을 덮지 않는다`: Completer로 공공→기존 순서 역전 응답을 만들고 기존 seq 보호 유지 확인.

## 10. 검증 실행 담당자 절차와 완료 기준

설계 단계에서 실행한 것은 초안 test_public_table_presets.py 6건뿐이다. 아직 구현·Flutter·전체회귀·실제 COM 합격 주장은 하지 않는다. 이 worktree에는 .venv가 없고 조사 시 확인한 공용 가상환경은 `C:\HWP_AUTODOCFIT\v1803\v2\.venv\Scripts\python.exe`다. 실행 담당자는 의존성 있는 이 환경 또는 저장소의 정상 .venv를 사용하며 코더에게 환경 수정을 시키지 않는다.

구현 후 실행 담당자 순서:
1. 변경 파일 allowlist·diff/CRLF 확인. `hwp-auto-docfit.py`, PLANS, 사용자 원본, 생성된 Flutter 웹 번들에 diff가 없어야 한다.
2. 저장소 루트에서 지정 가상환경으로 `-m unittest discover -s tests -p test_public_table_presets.py`, 이어 `-p test_table_units_service.py`, `-p test_table_units.py`, `-p test_table_catalog.py`, `-p test_table_builder.py` 실행.
3. Flutter 루트에서 `flutter test test/table_units_screen_test.dart`, 전체 `flutter test`, `flutter analyze` 실행. 새 시험은 모달이나 사용자 입력으로 멈추지 않아야 한다.
4. 저장소 루트에서 `python -m unittest discover -s tests` 전체 실행(실제 사용한 인터프리터 절대경로와 결과 기록). 관련 없는 기존 실패가 있으면 baseline과 분리해 기록하고 신규 실패를 숨기지 않는다.
5. 실제 한/글 검증을 하는 실행 담당자는 `C:\HWP_AUTODOCFIT\.com-test.lock`을 기존 lock helper로 배타 획득한 뒤 수행한다. 남의 lock을 지우지 않는다. 임시 사본만 사용하고 소유 COM 인스턴스만 닫는다. 공공6개 기본값 및 간트14열/예산 행추가 결과를 숨긴 한/글로 열어 PDF 저장, 별도 새 임시 문서에 복사/붙여넣기/저장 후 행열·문자·정렬·선·여백을 재확인한다. 기존 내장 템플릿 대표3개도 같은 방식으로 비교한다. 원본·내장 base SHA256 전후 동일. PDF/PNG/재파싱 JSON과 실패 목록을 reports/P7-validation에 보관한다. 실제 렌더링과 단위 시험의 판정을 구분한다.
6. 최종 검사 후 feature/2.0.1-public-presets에 커밋, github 먼저 origin 다음 순서로 같은 브랜치에 푸시한다. main 병합·태그·공개 배포는 P7 범위 밖이다.

완료 기준: (a) 기존 목록 뒤 정확히6개 추가, 공공 분류·동일 검색/썸네일/복사 UX (b) preview/export 동일 구조·서식, 정확한 단위 계산, 합계/머리/고정열 보존 (c) 기존 내장 단위·정보단위 -/+·원본 경로·snapshot fingerprint/내장그림 회귀 없음 (d) public/legacy 캐시 독립 및 2회차 불필요 COM0 (e) 새/관련 자동시험 실패0, Flutter 분석0, 전체시험 결과와 기존 실패 분리 기록 (f) 원본 SHA/CRLF 유지, XML defusedxml만, 사람 입력 없는 시험 (g) 실제 COM 붙여넣기·PNG 조판 검증 결과 명시. 실제 COM 미실행이면 구현검증 완료와 제품 실측 완료를 구분하며 P7 최종 인수 완료로 표시하지 않는다.

## 11. 금지 및 보존 사항

편법 return/pass/상수 조건/시험 주석 처리 금지. 기존 예외 정리용 pass나 정상 early return을 무관하게 리팩터링하지 말고, 새 기능을 건너뛰어 통과시키는 분기를 추가하지 않는다. 기존 사용자 서식·원본 문서·표 모음·스냅샷 자산은 수정하지 않는다. CRLF 기존 파일은 CRLF 유지(초안 혼합 개행은 기능 수정 시 그 파일 안에서 CRLF로 통일 가능, 무관 파일은 금지). 파싱은 defusedxml만 사용하며 stdlib XML 파서는 새로 도입하지 않는다. 공공 프리셋을 이유로 COM 복사를 HTML로 대체하거나 실제 PNG를 구조 그림으로 바꾸지 않는다. 자동시험에 실제 COM/파일창/메시지박스/포커스 조작을 넣지 않는다.