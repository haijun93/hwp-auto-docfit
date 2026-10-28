# P7 설계서 — 2.0.1 공공 표 프리셋 정식 결합

작성: 2026-10-28. 저장소: C:\HWP_AUTODOCFIT\v1803\presets. 지정 브랜치: feature/2.0.1-public-presets. 원본 초안 b756ee8, 이전 설계 789bedd, 이번 조사 HEAD b8b28aa(WIP, 검수 전). main=v2.0.0 계열이다.
산출물: C:\HWP_AUTODOCFIT\v1803\reports\P7-design.md. 동일 내용의 Git 보관본: docs/P7-design.md.
이번에는 설계 문서만 작성한다. 아래 지시는 후속 코더용이며 구현 완료 보고가 아니다. Gemini/Gemma는 파일만 편집한다. 명령 실행, 시험 판정, 커밋·푸시는 실행 담당자가 한다. 사용자 요청의 제어문자와 중복된 출력 경로는 명확한 P7-design.md 경로로 해석한다.

## 1. 조사 결과와 초안의 문제

HANDOVER.md, AGENTS.md, 공동 작업 문서의 ‘★ Claude 작업 지시’를 읽었다. W1~W3는 기존 별도 과제이며 P7에서 재구현하지 않는다. 지정된 C:/HWP_AUTODOCFIT/v1803/reports/O5.md는 이번 조사 시 존재하지 않았다. 따라서 DeepSeek 지적을 확인했다고 주장하지 않는다.

최초 Gemini 1 초안(b756ee8)의 문제:
- public_table_presets.py:245-339는 descriptor와 수작업 cell_meta만 만들고 HWPX 내보내기를 구현하지 않았다. 서비스와 Flutter 연결도 없다.
- 실제 격자 rows/cols를 반복 정보단위 count와 혼용한다. 머리행·합계행을 본문으로 복제하거나 간트의 고정 2열을 기간 count에 포함할 위험이 있다.
- 0·음수를 기본값으로 덮고 bool·상한·고정축을 검사하지 않는다. units/guideline/getter 반환값이 전역 정의를 공유한다.
- fill·cell_texts 검증과 원본 보호·원자 저장·캐시 계약이 없다. 폭 48000 상수와 최소폭 보정으로 본문 폭을 초과할 수 있다.
- header_split이 없는 정의형에도 머리글 이중선을 넣고 간트 설명열에도 점선을 넣는다. QA의 부분 문자열 ‘적 합’ 판정은 부적합도 녹색으로 표시할 수 있다.
- 여백·줄간격·자간 안내가 HWPX에 기록되지 않는다. COM 없이 한/글 복사가 완결된다는 문구는 기존 Hwp Native 복사 경로와 다르다. 공식 규정의 출처 없이 기관 권장·인증으로 표시해서는 안 된다.
- 초안 시험 6개는 XML 내보내기·서비스·복사·캐시·UI를 보장하지 않는다. 과거 설계의 6개 PASS 기록을 현재 WIP 검증 결과로 사용하지 않는다.

현재 WIP(b8b28aa)의 반영 사항과 남은 문제:
1. descriptor 깊은 복사, 반복 plan, 공통 생성/preview/export, 서비스 정확한 ID 분기, public 캐시, Dart 선택 메타·카테고리 아이콘·가이드, 관련 시험 골격은 이미 있다. 이를 삭제하고 최초 초안으로 되돌리지 않는다.
2. 차단 오류: public_table_presets.py:23 및 tests/test_public_table_presets.py:17이 존재하지 않는 docfit_core.archive_safety를 import한다. 실제 helper는 docfit_core/hwpx/__init__.py:132의 open_hwpx_safely다. 이번에 순수 코어 시험을 실행했으나 ModuleNotFoundError로 로드 실패했다(1 loader error, 개별 시험 미실행). 이 오류가 서비스 import까지 전파될 수 있다.
3. public_preset_snapshot_key:974-989는 pagePr 자체 속성만 해시하고 하위 margin을 누락한다. 좌우 여백은 표 폭에 간접 반영되지만 상하 여백 변경은 키에 반영되지 않는다.
4. _build_public_document:792-804의 단일 section 검사는 builder가 나머지 section을 삭제한 뒤라 원래 바탕의 다중 section을 검출하지 못한다. 첫 표만 선택하며 정확히 하나인지 검사하지 않는다. :823-825는 PrvImage 파일만 지워 content.hpf manifest 참조를 남길 수 있다.
5. _public_para:383-385는 이미 PERCENT인 lineSpacing만 수정한다. 다른 type의 바탕에서는 안내한 130/140%가 보장되지 않는다.
6. _write_public_package:841-886은 PID만 붙인 임시 이름을 공유하고 borderFill만 검사한다. charPr/paraPr/style/font 참조, itemCnt, 필수 manifest 참조 검증이 빠져 있다. samefile 실패를 넓은 OSError/pass로 삼키고 새 정리 오류도 Exception/pass로 숨긴다.
7. 서비스 :183-193의 list는 public 키 생성 오류 때문에 기존 템플릿 목록까지 실패할 수 있다. 새 프리셋 내장 바탕의 누락이 기존 목록·내장 사진을 막지 않게 공공 경로에 한정해 처리한다.
8. 시험 이름과 실제 검사가 다르다. snapshot 시험은 동일 키/ID 차이만 확인한다. footer 시험은 QA만 확인한다. metadata 비교는 일부 필드만 본다. ‘기존 내장 그림 보존’ 시험은 setUp에서 내장 그림을 차단하며, 가짜 PDF 변환을 쓰고도 SaveAs 횟수를 세어 재생성 0회 단언이 무효다. 실패 썸네일 시험도 public에 도달하기 전에 legacy 저장에서 실패할 수 있다.
9. 화면 파일은 CRCRLF가 섞여 있다(LF 3000개, CR 5764개, CRCRLF 2882개). 개행을 일괄 변환해 거대한 diff를 만들지 않는다. 아래 위치는 읽기 도구의 universal-newline 기준과 LF 기준을 함께 제공한다.

## 2. 편집 대상과 정확한 위치

HEAD b8b28aa 기준. TARGET은 저장소 상대 경로이며 각 파일당 한 줄이다. 24,000자 초과 파일은 충분한 문맥을 포함한다. 구현 후 행이 움직이면 함께 기재한 함수명으로 찾는다. screen.dart의 TARGET은 Get-Content/Python universal-newline 기준이다. LF만 세는 편집기에서는 뒤의 대응 범위를 사용한다.

TARGET: docfit_core/public_table_presets.py:1-43,305-391,651-1042
TARGET: docfit_app/table_units_service.py:65-224,287-334
TARGET: flutter_ui/lib/core/api/table_units_api.dart:65-158
TARGET: flutter_ui/lib/features/table_units/table_units_screen.dart:1593-1781,2770-2925,4097-4235,4515-4570
TARGET: tests/test_public_table_presets.py:1-149,149-384,385-521
TARGET: tests/test_table_units_service.py:1-115,211-407
TARGET: flutter_ui/test/table_units_screen_test.dart:1-265,824-1168
TARGET: docs/TABLE_TEMPLATE_V2_ALPHA_DESIGN.md:1-160

screen.dart의 LF 기준 대응: 분류/검색 797-891, 카테고리 칩 1386-1464, 가이드와 상세 시작 2054-2176, 가이드 삽입 2316-2344. 앵커는 _getCategories(1593), _getFilteredTemplates(1653), categoryChip_$cat(2791), _buildPresetGuideline(4108), _buildDetail(4213), _buildPresetGuideline(template)(4549)다. 화면의 기존 일반 흐름은 보존하며 해당 범위 밖 정리는 하지 않는다.

참조만 할 파일: table_units.py:562-604(validate_input/_apply_texts), :605-755(_resize_axis/resize_table), :1103-1200(export/preview), table_catalog.py:66-88(_top_tables/글 추출), :140-215(_header_lookup), :324-407(_cell_meta), table_builder.py:144-202(normalize), :211-337(_Header), :589-654(build_table_hwpx), docfit_core/hwpx/__init__.py:78-137(안전 ZIP 검사). 이 파일들 및 PLANS, detect_plan, resize_table, 공유 builder 제한값은 고치지 않는다. archive_safety.py를 새로 만들지 않는다.

## 3. 최종 데이터 계약

프리셋 ID는 정확히 다음 6개다. category='공공 표준', 공인 의미 없는 용도 배지를 쓴다. 기존 목록 뒤 이 순서로 추가한다. 미등록 pub_*는 공공 엔진으로 보내지 않는다.

| ID(pub_ 이후) | 기본 실제 격자 | row start/count/min/max | col start/count/min/max | 머리/끝행 |
|---|---|---|---|---|
| summary_headline | 1×1 | null | null | 0/0 |
| two_col_definition | 4×2 | 0/4/1/30 | null | 0/0 |
| multi_col_comparison | 5×4 | 1/3/1/30 | null | 1/1 |
| gantt_timeline | 5×6 | 1/4/1/30 | 2/4/2/12 | 1/0 |
| budget_breakdown | 5×5 | 1/3/1/30 | null | 1/1 |
| qa_checklist | 4×4 | 1/3/1/30 | null | 1/0 |

모든 활성 축 core=1/sep=0. 실제 행수=머리행+row_count+끝행, 간트 실제 열수=2+col_count. None은 기본 단위 수. 고정축은 반드시 None이며 기본 실제 크기와 같은 값을 지정해도 거부한다. bool/float/문자/0/음수/범위 초과는 ValueError다. 호환 wrapper의 target_rows/target_cols만 실제 격자 수다.

내부 preset은 기존 id/name/category/default_rows/default_cols/col_ratios/margins_hwpunit/guideline/sample_rows/borders 및 _plan/header_rows/footer_rows/line_spacing/char_spacing을 유지한다. units는 외부용 count/min/max/core/sep만, _plan은 start까지 포함한다. 두 표현의 값이 어긋나지 않게 descriptor는 _plan에서 만들고 전역 units와 중복 관리하지 않는 방향으로 정리한다. get_public_preset의 기존 units 키는 호환을 위해 유지하고 _plan에서 복사한 동일 값을 제공한다. 모든 공개 반환은 deepcopy로 격리한다.

descriptor={id,name,category,rows,cols,units,badge,description,guideline}. guideline은 margins/borders/font/fill 문자열 4개. preview={id,name,rows,cols,cells,cell_meta,guideline}. cell_meta는 catalog의 row/col/rowSpan/colSpan/width/height/text/align/style/borders/shapes와 동일하다. preview의 글은 기존처럼 공백 정규화 후 80자, 내보내기는 칸당 최대1000자와 줄바꿈/탭을 보존한다. cell_texts 키는 '행,열'(실제 좌표)이고 최대200칸. fill=increment|blank|copy는 추가된 단위에만 적용한다. 원래 샘플·머리·합계는 그대로 둔다.

## 4. 함수 시그니처와 자료 구조

다음 공개 함수는 WIP에 이미 있으므로 이름·인자·기본값을 유지한다(최초 초안 대비 새 API). 내부 함수는 아래 형태로 정리한다. 기존 _write_public_package(contents,target) 인자도 유지한다.

```python
def get_public_preset_descriptors() -> list[dict[str, Any]]: ...
def is_public_preset(template_id: str) -> bool: ...
def get_public_preset(template_id: str) -> dict[str, Any] | None: ...
def public_preset_plan(preset_id: str) -> dict[str, Any]: ...
def preview_public_preset(preset_id: str, row_count: int | None = None,
    col_count: int | None = None, *, fill: str = 'increment',
    cell_texts: dict[str, str] | None = None) -> dict[str, Any]: ...
def export_public_preset(preset_id: str, output_path: str | Path,
    row_count: int | None = None, col_count: int | None = None, *,
    fill: str = 'increment', cell_texts: dict[str, str] | None = None) -> Path: ...
def public_preset_snapshot_key(preset_id: str) -> str: ...
def build_public_preset_preview(preset_id: str, target_rows: int | None = None,
    target_cols: int | None = None, cell_texts: dict[str, str] | None = None
    ) -> dict[str, Any]: ...

# 새 내부 helper (Element는 defusedxml로 파싱한 요소를 뜻한다)
def _validate_public_contents(contents: dict[str, bytes]) -> tuple[Any, Any, Any]: ...
def _remove_public_preview_image(contents: dict[str, bytes]) -> None: ...
def _hash_public_tree(digest: Any, root: Any) -> None: ...
# 기존 내부 계약 유지
def _build_public_document(preset_id: str, row_count: int | None,
    col_count: int | None, *, fill: str, cell_texts: dict[str,str] | None
    ) -> tuple[dict[str, bytes], Any, Any]: ...
def _apply_public_style(table: Any, header: Any,
    preset: dict[str, Any], body_width: int) -> None: ...
def _public_para(pool: Any, align: str, line_spacing: int,
    cache: dict[tuple[str,int],str]) -> str: ...
def _write_public_package(contents: dict[str, bytes], target: Path) -> Path: ...
```

_build_public_document 반환은 ZIP 멤버 bytes 사전·최종 table·header다. _validate_public_contents 반환은 section0·최상위 table·header다. 호출부에서 table/header 순서를 혼용하지 않는다. 새 클래스 계층이나 독립 복사 엔진은 필요 없다.

서비스는 기존 모든 공개 시그니처와 command action/payload/api_version=1을 유지한다. 기존 _public_snapshot_key(self,template_id:str)->str도 유지한다. 캐시는 dict[tuple[str,str,str],str]이며 키는 (preset ID, revision, 내장 base 전체 bytes의 SHA256), 값은 최종 public 키다. 최초 생성 후 같은 요청은 재사용한다. 정의·스타일 변경 시 PUBLIC_PRESET_REVISION을 반드시 올리고, 이번 보완은 'p7-v2'로 올려 잘못된 WIP 그림 캐시를 재사용하지 않는다.

Dart의 TableTemplateInfo 선택 필드 badge:String='', description:String='', guideline:Map<String,String>=const {}와 copyWith/fromJson을 유지한다. guideline은 문자열 key/value만 복사한다. 새 화면 helper는 이미 있는 Widget _buildPresetGuideline(TableTemplateInfo template)다. 요청용 rowCount/colCount 및 TablePreview 모델은 변경하지 않는다.

## 5. 코더의 단계별 구현 지시

### 5.1 모듈 로드와 정의 정리

1. core와 core 시험의 archive_safety import를 모두 `from docfit_core.hwpx import open_hwpx_safely`로 교체한다. 모듈 stub/try import/skip로 가리지 않는다.
2. 모듈 docstring을 ‘공공 업무 예시 프리셋’으로 고쳐 공식 지침 준수 인증 오해를 없앤다. public revision=p7-v2. deepcopy와 정확한 ID 판정은 유지한다. _plan/descriptor 단위 값은 3절 표대로 고정한다.
3. _validate_preset_counts와 validate_input은 I/O 전에 호출한다. wrapper는 고정 실제 크기를 None으로 바꾸고, 가변 행은 머리+끝행을 빼고, 간트 열은 2를 빼서 새 API에 위임한다. 실제7열 요청→col_count5. 0·음수·잘못된 type을 기본값으로 대체하지 않는다.

### 5.2 공통 HWPX 생성과 검증

1. _default_base_path의 앱 내장 기본 서식만 읽는다. builder 호출 전에 open_hwpx_safely로 원래 base를 열어 header/section0 및 단일 section을 확인한다. builder가 다중 section을 제거한 뒤 검사하는 것으로 대체하지 않는다. 누락은 OSError, 잘못된 구조는 ValueError로 명확히 끝낸다.
2. TemporaryDirectory의 기본 grid 생성은 현재 spec kind='grid', sample_rows, header_rows, use_basic_style=False, basic_style=None을 유지한다. 기본6열까지만 builder를 통과시키고 14열 결과는 resize_table로 만든다. 사용자1000자 입력은 builder(MAX_TEXT200) 뒤 resize_table에서 적용한다. builder의 MAX_COLS12/MAX_TEXT200을 늘리지 않는다.
3. 안전 ZIP을 읽고 defusedxml로 파싱한다. 최상위 표는 section의 각 직접 p에 catalog._top_tables(p)를 적용해 모은다. 첫 번째 표를 무조건 선택하거나 .//tbl 개수를 최상위 표 수라고 부르지 않는다. 공공 생성문서는 최상위1개·중첩0개로 검증한다.
4. deepcopy plan을 resize_table(...,id_roots=(header,section0),fill=fill,cell_texts=cell_texts)에 전달한다. 늘리기/줄이기·숫자 증가·고정 머리/합계 보존은 공유 엔진에 맡긴다. 스타일은 최종 크기에서 재적용하고 텍스트를 덮어쓰지 않는다.
5. 본문폭=pagePr.width-margin.left-margin.right(양수 검사). 열폭은 정수 분배 후 마지막 열에 나머지를 준다. 간트는 고정24%/20%, 나머지56% 균등 분배. 모든 cellSz.width와 tbl sz.width를 함께 갱신한다. 각 행의 열폭 합=본문폭이어야 한다.
6. _public_para는 paraPr id0을 복제하되 align.horizontal과 모든 switch 분기의 lineSpacing type='PERCENT'/value=130 또는140을 명시한다. 요소가 없거나 원래 type이 FIXED인 바탕도 처리한다. 누락 요소는 동일 namespace와 주변 schema 순서를 따르게 생성한다. 캐시는 요청 내부 전용이다. 기본 builder.center_para는 고치지 않는다.
7. 기존 _Header.char(style,spacing=...)는 size를 pt×100으로 변환하므로 style.size는9.0/9.5/10.5 그대로 전달한다(호출 전에100을 곱하지 않는다). cellMargin과 tbl inMargin에 프리셋 여백을 기록한다. summary 좌우1134/상하708·자간-5/줄간격140, 일반708/340, 간트283/283, 나머지 자간0/줄간격130이다. 각 셀의 run/paragraph 참조를 갱신하고 linesegarray를 제거한다. 머리행만 header=1이다.
8. 현재 테두리/QA 보완을 보존한다. header_split 없으면 inner_h, 간트 설명열 사이와 기간 시작 경계는 실선·기간 내부는 점선, 좌우 외곽 NONE. 양옆 셀 공유변 type/width/color가 같아야 한다. footer는 최종 마지막 행에만 적용한다. QA는 명시한 적합/부적합 텍스트의 완전 일치만 색칠하고 임의 글·빈글은 검정/흰색이다. 사용자 숫자·합계를 다시 계산하지 않는다.
9. _remove_public_preview_image는 Preview/PrvImage.png를 제거하고 Contents/content.hpf가 이를 참조하면 해당 manifest item도 제거한다. itemref가 해당 item id를 가리키면 함께 제거한다. 다른 image/section/font/binary 관계는 보존한다. XML은 원본 serialize helper를 쓴다. PrvText는 완성된 표의 글로 다시 만든다.
10. _validate_public_contents는 필수 mimetype/header/section0, 정확한 단일 section과 최상위표1개, rowCnt/colCnt·실제 행열·양수폭·좌표, 사용 중 borderFillIDRef/charPrIDRef/paraPrIDRef/styleIDRef 및 fontRef 언어별 ID 존재를 검사한다. header group별 ID 중복·itemCnt와 실제 자식 수 불일치를 거부한다. 필수 manifest의 로컬 href가 존재하는지도 확인한다. optional preview의 관계를 정상 정리한 결과는 통과시킨다. 검증하려고 참조를 지우거나 유효하지 않은 값을0으로 바꾸지 않는다. ValueError 메시지에 실패 항목을 포함한다.
11. preview/export 모두 같은 _build_public_document 결과를 쓴다. preview는 catalog._header_lookup/_cell_meta로 재해석한다. 별도의 가짜 width·style 메타를 만들지 않는다.

### 5.3 원자 저장과 스냅샷

1. _write_public_package는 resolve 및 존재하는 경로의 samefile로 base 덮어쓰기/하드링크를 거부한다. Path.exists로 ‘출력 없음’을 구분하고 실제 samefile/권한 오류는 전파한다. OSError를 삼키고 보호 검사를 통과시키지 않는다.
2. target.parent에 tempfile.NamedTemporaryFile(delete=False, prefix=target.name+'.tmp_', suffix='.hwpx',dir=...)로 고유 임시 경로를 만들고 핸들을 닫는다. ZIP은 mimetype 첫 항목 ZIP_STORED, 나머지 기존 멤버 보존. open_hwpx_safely와 _validate_public_contents를 통과한 뒤에만 replace(target)한다. 실패하면 원래 target/base bytes 불변, 자기 임시 파일만 삭제한다. 정리는 missing_ok=True를 이용하고 넓은 Exception/pass를 새로 넣지 않는다.
3. _hash_public_tree는 순회하는 각 요소의 expanded tag/sorted attributes/text/tail을 UTF-8로 해시한다. snapshot 키는 revision·preset ID·최종 table·header·pagePr 하위 전체(margin 포함)를 입력으로20자리 hex다. ZIP timestamp·namespace 접두사 등록에 의존하지 않는다. _build_public_document의 최종 section0에서 pagePr를 읽는다.
4. 서비스 _public_key_cache는 바탕 SHA256+revision을 포함한다. definition/style를 고치면 revision을 올리는 규칙을 문서와 시험에 명시한다. catalog 내용 변화는 public 키를 바꾸지 않는다. 기존 SNAPSHOT_REVISION/_digest/_table_fingerprint/_content_keys는 수정하지 않는다.

### 5.4 서비스 정식 결합

1. _units는 legacy describe_units 성공 결과 뒤에 공공6개를 붙이는 현 WIP를 유지한다. 기존 catalog 손상이면 기존 CATALOG_UNAVAILABLE. legacy 첫 선택·상대 순서·source·favorite·recent8개 제한은 그대로다.
2. preview/_export는 is_public_preset의 정확한6개 ID만 신규 엔진으로 분기한다. unknown pub_*는 기존 INVALID_INPUT. 공공 base OSError는 PRESET_UNAVAILABLE, 사용자 count/fill/좌표 오류는 INVALID_INPUT. legacy 예외 의미를 바꾸지 않는다.
3. _snapshot_path/public/<key>.png, _bundled_snapshot(public)=None, _snapshot_url(public)은 public 경로만 읽는 현 구조를 유지한다. public 바탕 누락/잘못된 구조에 따른 OSError/ValueError는 public _snapshot_url 안에서만 None으로 처리하여 legacy 목록·사진을 보존한다. 실제 생성 preview/copy/thumbnails에서는 오류를 정상 보고한다. 일반 예외 전체를 잡아 숨기지 않는다.
4. thumbnails는 기존 missing→_export→숨긴 한/글 PDF→crop→PNG를 사용한다. public PNG가 없으면 처음 ready=False, 기존 자동1회 생성과 구조 폴백을 쓴다. public 저장 실패의 자기 .tmp만 정리한다. 기존 ready 정의·legacy 캐시/내장그림 우선순위·old16자리폴더 청소는 바꾸지 않는다. public 폴더는6자리여서 청소 대상이 아니다.
5. copy/start_copy_job/command의 공통 흐름은 고치지 않는다. Open→표 컨트롤 anchor→SetPosBySet→FindCtrl→Copy→Clear/Quit→Hwp Native 확인→최근목록 갱신→활성화 순서 유지. SelectAll/HTML 복사/추가 COM 인스턴스로 대체하지 않는다. 실패 시 최근목록 갱신 금지.

### 5.5 Flutter와 문서

1. TableTemplateInfo의 현 선택 메타와 JSON 필터를 유지하고 copyWith 보존을 시험한다. 기존 응답에 필드가 없어도 동일하게 작동해야 한다. 불필요한 모델 개편은 하지 않는다.
2. _getCategories/_getFilteredTemplates의 기존 이름·분류 검색과 categoryChip 키를 그대로 사용한다. 공공 칩에만 account_balance 아이콘16px, category 문자열은 ‘공공 표준’ 그대로다. badge/description 검색을 전역으로 추가하지 않는다.
3. _buildPresetGuideline은 여백·테두리·글꼴·배경4개 안내를 Column/Wrap으로 표시한다. badge/description/guideline 모두 없으면 공간을 차지하지 않는다. publicPresetGuideline key를 유지하고 420px/1280px에서 글이 잘리거나 overflow가 나면 해당 helper 안에서만 제약/줄바꿈을 수정한다. 현재 구현이 시험을 통과하면 화면/모델을 억지로 수정하지 않는다.
4. _selectTemplate/_requestPreview/_copyTable/fill/셀 편집/스테퍼/자동 썸네일/응답 순번 보호는 공유한다. 간트 +1은 count5를 전송하고7열을 받는다. UI에서 +2를 더하지 않는다. summary는 기존 isFixed 경로라 -/+가 없다.
5. TABLE_TEMPLATE_V2_ALPHA_DESIGN.md는 실제 helper 경로·p7-v2·공공/기존 캐시 분리·여백 포함 키·COM 의존성·시험 상태를 반영한다. ‘구현됨’과 ‘실측 합격’을 구분하고 존재하지 않는 API를 기록하지 않는다.

## 6. 작성·보강할 자동 시험

기존 시험을 지우거나 skip/상수 조건으로 우회하지 않는다. 같은 이름의 기존 시험은 아래 단언을 보강한다. unittest/TemporaryDirectory/defusedxml, Flutter 가짜 API를 쓴다. 가짜 hwp_factory/clipboard_formats/activator를 주입하고 실제 한/글·클립보드·Tk messagebox·파일창·포커스를 호출하지 않는다. 필수 경로가 이를 호출하면 patch로 즉시 실패하게 한다.

### tests/test_public_table_presets.py

- test_import_uses_existing_hwpx_helper(추가): 정상 import로 공개 함수들을 사용한다. 잘못된 모듈 stub 없이 새 프로세스 import smoke도 실행 담당자가 확인한다.
- test_descriptors_and_getter_are_deep_copies: 정확한6ID/순서/category/단위 표, getter·plan·descriptor의 중첩 dict/list를 바꿔도 다음 요청 불변.
- test_unit_counts_exclude_header_footer_and_fixed_columns: 기본/최소/최대6종, 비교·예산 count4→6행/합계1개, QA count4→5행, 간트 count5→7열, summary1×1.
- test_invalid_counts_and_fixed_axes_fail_without_output: bool/float/str/0/음수/min-1/max+1/고정축/unknown을 preview/export 양쪽 검사. 새 파일 없음·기존 출력 bytes 불변.
- test_legacy_preview_wrapper_uses_physical_dimensions: 정의형 target_rows6→6행, 간트 target_cols7→7열, 고정 기본 실제 크기는 허용·다른 크기는 거부.
- test_fill_modes_and_text_overrides_match_export: 세 fill 모드에서 늘어난 본문만 변함, QA 연번04·간트 기간 제목 증가, 머리·합계 유지, cell_texts 최종 적용 및 XML 재파싱 일치.
- test_text_validation_and_multiline_roundtrip: 1000자·한글·&<>·탭·여러줄 export 보존/preview80자,1001자/201칸/제어문자/범위밖·잘못된좌표 거부.
- test_all_six_exports_reparse_as_single_table: safe ZIP→catalog._scan 결과 ID로 재조회, 최상위1/중첩0·행열·참조·itemCnt·mimetype 첫항목/무압축, base SHA256 전후 동일.
- test_preview_and_export_have_identical_cell_metadata: 기본/최소/최대 및 간트 양축 동시 변경의 전체 cell_meta 비교. 텍스트·span·폭·높이·정렬·font/size/bold/color/fill·4변선·shapes 모두 검사한다. 숫자/단위 표현만 정규화하고 실제 차이는 제외하지 않는다.
- test_public_metrics_are_written_to_xml: 6종 여백·줄간격·자간·폰트·pt×100·정렬·머리글·line cache 제거를 실제 참조가 가리키는 XML에서 확인.
- test_definition_has_no_implicit_header_double_border: 정의형 첫 공유변 실선, summary 좌우NONE, 간트 설명/기간 경계SOLID·기간 내부DOT, 모든 공유변 양쪽 규격 일치.
- test_footer_styles_and_qa_status_after_resize: 비교/예산 축소·확대 후 마지막 footer만 별도 음영, 본문 지브라, QA 적합/부적합/임의글/빈글 색상.
- test_gantt_max_columns_keep_total_width: row_count30/col_count12→31×14, 모든 열폭 양의 정수, 각 행 합=tbl width=본문폭, 설명열 비율 유지.
- test_snapshot_key_is_deterministic_and_tracks_styles: 동일 키20hex·namespace/ZIP timestamp 무관. 샘플글·스타일·cellMargin·pagePr.margin.top/bottom·revision 각각 변경 시 키 변경을 patch/임시 base로 검사한다.
- test_export_failure_preserves_target_and_base: serialize/검증/replace 실패 각각 patch, 원래 대상/base 불변·자기 tmp만 정리. 같은 경로·base 하드링크 거부. 하드링크는 임시 base 사본으로 만들고 원본에 연결을 만들지 않는다.
- test_base_sections_checked_before_builder(추가): 임시2section base를 주고 builder 호출0·ValueError·출력없음.
- test_removed_preview_image_has_no_manifest_reference(추가): preview image manifest item/idref 포함 fixture에서 파일·참조 제거, 다른 manifest item 보존.
- test_non_percent_line_spacing_is_replaced(추가): paraPr id0의 FIXED 및 lineSpacing 누락 fixture를 PERCENT140/130으로 만들고 미리보기/export가 같은 결과.
- test_package_rejects_dangling_style_references(추가): border/char/para/style/fontRef·중복ID·잘못된 itemCnt·manifest href 각각 손상한 contents가 replace 전에 실패.
- test_unique_temporary_outputs_do_not_collide(추가): 실제 스레드/COM 없이 임시 생성 helper 두 호출의 서로 다른 경로와 각 실패 정리를 검사. 다른 임시 파일은 보존.

### tests/test_table_units_service.py

- test_public_presets_append_without_changing_legacy_descriptors: legacy describe_units 앞부분 전체 계약·최초 선택·내장사진 bytes 동일, 뒤6개.
- test_public_preview_and_export_route_by_exact_id:6종/legacy/unknown 분기 호출 인자와 실제 export 재파싱. 접두사만 같은 unknown은 INVALID_INPUT.
- test_public_copy_uses_existing_hwp_native_sequence:6종 FakeHwp.Open 시 실제 ZIP 표 확인, 표 선택/Copy/Clear/Quit·Native·삭제 순서, SelectAll 없음. Open=False/HeadCtrl없음/Native없음은 최근목록 불변.
- test_public_favorite_recent_persist_with_legacy_ids: 혼합9개·중복제거·최근8개·설정 재로딩·즐겨찾기 해제.
- test_public_snapshots_use_separate_content_cache: legacy/public 경로 독립·catalog 변경 public 불변·base/revision 변경 public만 변경. patch한 key builder call_count로 캐시 재사용 확인.
- test_public_thumbnails_generate_once_and_preserve_bundled_legacy: setUp의 no-bundled patch를 이 시험 안에서 실제 BUNDLED_SNAPSHOTS로 복원. 기본 내장사진의 bytes를 기록하고, 빈 public 캐시에서 fake_convert 호출 수가 정확히6, 두 번째는 추가0인지 Mock.call_count로 검사한다. 가짜 PDF를 쓰며 SaveAs 수를 세지 않는다. 결과 ready=True·public PNG6개·legacy bytes 불변·청소 후 public 보존.
- test_failed_public_thumbnail_does_not_leave_png_or_lose_legacy_cache: legacy는 내장사진으로 준비하고 public 단1개만 missing으로 만들어 실패 지점이 public임을 확인한다. convert/render/save 각각 patch; save는 일부 .tmp bytes를 쓴 뒤 실패시켜 실제 정리를 검사. .png/.tmp 없음·COM종료·legacy유지.
- test_public_errors_are_api_errors_before_hwp_launch: 잘못된 사용자 입력/unknown은 preview/copy에서 factory0·INVALID_INPUT, base누락 preview/copy는 PRESET_UNAVAILABLE, legacy catalog손상은 CATALOG_UNAVAILABLE.
- test_missing_public_base_keeps_legacy_list_and_pictures(추가): public base 누락 시 list 성공·legacy사진그대로·public thumbnail=None·ready=False, 직접 public 요청은 오류. 사용자 원본 접근0.
- 기존 BundledSnapshotTests의 legacy 전용 _units patch 두 건은 유지하되, 혼합 목록 시험을 대신하지 않는다고 명시한다. 이미 있는 stdlib namespace 등록용 코드를 새 파서로 확대하지 않는다. 새 XML 파싱은 defusedxml만 사용한다.

### flutter_ui/test/table_units_screen_test.dart

sampleListData의 기존3개 기본값을 유지하고 includePublic=true일 때만6개를 뒤에 붙인다. 공공 fixture의 units는3절 표와 일치해야 한다. preview fixture는 간트 count4→6열/count5→7열을 정확히 반영한다.
- ‘공공 분류는 기존 분류와 함께 나타나고 여섯 프리셋을 필터링한다’: categoryChip_공공 표준/account_balance·6ID·검색/전체 복귀·최초 legacy 선택.
- ‘공공 모델의 선택 메타 필드는 이전 응답과 호환된다’: fromJson/copyWith 필드 보존·누락 기본값·비맵/비문자 guideline 무시.
- ‘공공 가이드 표시 후 기존 표 선택 시 사라진다’: publicPresetGuideline/4개안내·420/1280폭·tester.takeException()==null·legacy 재선택 후 가이드없음.
- ‘공공 간트 열 더하기는 정보단위 수를 전송한다’: preview와copy payload count5, 결과7열, fill/cell_texts 동시 보존. min/max 스테퍼 차단.
- ‘공공 요약은 기존 고정표 조작을 사용한다’: -/+없음·preview/copy row/col null.
- ‘공공 표도 즐겨찾기 최근사용과 복사 오류를 공유한다’: favorite ID와 최근순서·copy 성공 기존메시지·실패 메시지.
- ‘공공 썸네일 누락은 기존 자동 생성 한 번과 구조 폴백을 사용한다’: 성공PNG, 실패spinner종료·구조표유지·무한재요청없음·legacy사진유지까지 별도 subcase.
- ‘공공 미리보기의 늦은 응답은 다음 선택을 덮지 않는다’: Completer 역순응답, 최종legacy선택/행열보존. 미완료 Future를 기다리는 pumpAndSettle로 교착시키지 말고 pump와명시적 complete를 사용한다.

## 7. 실행 담당자의 검증과 인계 순서

코더 작업 순서: import/단위계약 → 공통 생성·XML/원자저장·키 보완 → 순수코어 시험 보강 → 서비스 예외/캐시·통합시험 → Dart/화면 필요 보완·widget시험 → 설명 문서. 단계마다 변경 파일과 미실행 시험명을 인계한다. 코더에게 명령 실행이나 바이너리 PNG 생성·Flutter 빌드를 요구하지 않는다.

실행 담당자:
1. 변경 allowlist/개행/diff 확인. hwp-auto-docfit.py, table_units.py, table_catalog.py, table_builder.py, 사용자 표모음/원본·생성 웹번들 변경0. 이번 설계 작성에서는 앱 코드 변경0을 확인한다.
2. worktree에는 .venv가 없으며 조사한 공용 인터프리터는 C:\HWP_AUTODOCFIT\v1803\v2\.venv\Scripts\python.exe다. 저장소 루트에서 이 실행파일로 `-m unittest discover -s tests -p test_public_table_presets.py`, 이어 test_table_units_service.py/table_units.py/table_catalog.py/table_builder.py에 대응하는 test_*.py 패턴을 실행한다. 최초 smoke는 `-c "import docfit_core.public_table_presets; import docfit_app.table_units_service"`다. 라이브러리 미설치를 앱 stub으로 해결하지 않는다.
3. Flutter 루트에서 `flutter test test/table_units_screen_test.dart`, `flutter test`, `flutter analyze`. Python 전체는 지정 가상환경의 `-m unittest discover -s tests`. 새시험은 모두 무인 종료한다. 기존실패는 baseline과 대조해 별도 보고하며 신규 실패를 기존문제로 덮지 않는다.
4. 실제 한/글 검증은 자동 단위시험과 별도다. 기존 lock helper로 C:\HWP_AUTODOCFIT\.com-test.lock을 배타 획득하고 남의 lock을 지우지 않는다. 공공6종 기본·간트31×14·예산행추가와 기존대표3종을 임시 사본에서 PDF/PNG 및 새 임시문서 붙여넣기로 검증한다. 소유 COM만 닫는다. 행열/문자/머리/합계/정렬/여백/선/잘림을 확인하고 사용자원본·내장base SHA256 전후 동일을 기록한다. 결과는 reports/P7-validation에 둔다.
5. 구현 인수 합격 뒤 지정 feature/2.0.1-public-presets에 커밋, github→origin 순서 푸시. main 병합·태그·공개 배포는 하지 않는다. 이 설계 문서는 코드 구현 판정을 기다리는 W1~W3 과제와 독립된 문서 전용 산출물이다.

이번 조사에서 실행한 시험: `C:\HWP_AUTODOCFIT\v1803\v2\.venv\Scripts\python.exe -m unittest discover -s tests -p test_public_table_presets.py` → ModuleNotFoundError(docfit_core.archive_safety), loader error1. 코드 무수정 조건에 따라 수정/우회 재시험하지 않았다. 서비스/Flutter/전체/COM 시험은 미실행이다.

## 8. 완료 기준과 보존 규칙

- 기존 목록의 상대 순서·첫선택·분류·즐겨찾기·최근8개·legacy사진/캐시 동작이 그대로이고 뒤에 공공6개가 동일 UI 흐름으로 추가된다.
- preview/export가 같은 실제 HWPX 구조/서식이며 정확한 반복단위, 고정머리/합계/간트설명열·원문을 보존한다. 간트 최대31×14와 폭 합이 맞는다.
- public/legacy 캐시가 독립이고 바탕 페이지 여백·서식·revision 변화가 키에 반영된다. 2회차 썸네일 생성COM0, 실패 캐시/임시파일 잔재0.
- 참조/manifest/itemCnt 검증을 통과하며 실패 시 기존 출력·원본 불변이다. 사람 입력 없는 신규/관련 자동시험 실패0, Flutter analyze0, 전체시험 결과/기존실패 구분이 기록된다.
- 실제 COM 붙여넣기와 조판 결과를 별도 명시한다. 미실행이면 자동검증 완료와 제품 실측 완료를 구분하며 P7 최종 인수 완료라고 쓰지 않는다.
- 편법 return/pass/if True/if False/주석처리/skip로 기능·시험을 우회하지 않는다. 정상 early return과 기존 무관 예외정리 코드는 억지로 리팩터링하지 않는다. 새 cleanup은 넓은 pass로 숨기지 않는다.
- 기존 동작을 플래그 없이 바꾸지 않는다. 신규 동작은 정확한 공공ID 또는 공공 메타 표시 범위에 한정한다. CRLF 및 기존 혼합 개행의 무관 구간을 보존하고 hwp-auto-docfit.py는 건드리지 않는다. XML 파싱은 defusedxml만, 사용자 문서 원본 수정 금지, 모든 시험 모달/한글실행은 patch 또는 가짜 주입, 실제 COM은 지정 잠금 필수다.
