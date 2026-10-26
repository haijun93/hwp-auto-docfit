# HWP AutoDocFit 2.0.0 — OpenOffice 벤치마킹 및 6-탭 아키텍처 분석

작성일: 2026-10-26 · 성격: 소스·공식 문서 기반 설계 보고서 · 구현/성능 검증 보고서가 아님

## 1. 결론과 분석 범위

2.0의 우선 과제는 오피스 엔진 전체를 이식하는 것이 아니라 **6개 탭이 공유하는 문서 세션, 스타일 해석기, 변경 트랜잭션, 변환 작업 큐**를 만드는 것이다. 기존 HWPX 최소 변경 경로와 한/글 COM 조판을 유지하면서, 편집 화면과 파일 엔진 사이에 명시적인 계약을 둔다.

지정 저장소인 **`pblsketch/openoffice`는 Apache OpenOffice/StarOffice 계열 소스가 아니다.** GenOffice를 바탕으로 한 이음오피스(IeumOffice)이며 Electron·TypeScript 모노레포다. UNO·`sw`·`SdrObject`를 이 저장소의 구성 요소로 기술하면 잘못된 분석이 된다. 따라서 두 대상을 구분한다.

| 분석 대상 | 실제 확인 범위 | 벤치마킹 목적 |
|---|---|---|
| 이음오피스 | 셸/편집기/공용 패키지 분리, ODT 브리지, DOCX 패치·스타일 코드, 마인드맵 의존성 | 통합 UI, 파일별 어댑터, 원본 보존 방식 |
| Apache OpenOffice(AOO) | UNO 공식 문서, Writer 표 레이아웃·AutoFormat·페인팅, Draw 스냅 코드, PDF 내보내기 코드 | 성숙한 문서 모델과 편집 동작의 설계 원리 |
| HWP AutoDocFit | 현재 작업 트리 `2c164c82c27a3fddfdd431ed7a51b0e8ac45c9e0`, 인수인계, 표/스타일/서비스/편집기 소스 | 재사용 지점과 실제 공백 식별 |

이음오피스 조사 기준 SHA는 `1877ecc23bf3b4f8b36746262ca61feeb6d42374`, AOO `trunk` 조회 기준 SHA는 `7d712b94e3ff1803b979fa5f284e7acd2daba990`이다. 아래 외부 소스 링크는 해당 버전으로 고정한다. 기준 SHA는 조사 시점의 원격 상태이며 로컬 앱 날짜와 외부 릴리스 날짜가 일치한다는 의미는 아니다. 외부 앱 설치·실행, 렌더링 비교, 처리량 벤치마크는 수행하지 않았다. [이음오피스 구조](https://github.com/pblsketch/openoffice/blob/1877ecc23bf3b4f8b36746262ca61feeb6d42374/docs/architecture.md), [패키지 구성](https://github.com/pblsketch/openoffice/blob/1877ecc23bf3b4f8b36746262ca61feeb6d42374/package.json)

## 2. 이음오피스의 실제 아키텍처

### 2.1 셸·편집기·엔진 분리

`apps/shell`이 창·탭·파일 열기 등을 관리하고, `apps/docs`, `sheets`, `slides`, `pdf`, `mindmap`, `hwp` 등 편집기가 공용 `packages/*`를 사용한다. 화면은 WebContentsView로 분리되지만 편집기 메인 코드는 셸의 단일 메인 프로세스에 묶인다. 따라서 화면 분리가 변환 작업의 프로세스 격리를 뜻하지 않으며 IPC 채널 충돌도 관리해야 한다.

AutoDocFit에는 Electron 전환보다 이 **의존 방향**이 유용하다. Flutter/웹/Tk는 명령과 상태만 교환하고, `docfit_app`은 유스케이스와 작업 수명, `docfit_core`는 순수 문서 규칙, COM 어댑터는 한/글 실행을 맡게 한다. 현재 `desktop_web_ui.py`와 서비스 계층을 이 경계로 점진 정리한다. [구조와 IPC 설명](https://github.com/pblsketch/openoffice/blob/1877ecc23bf3b4f8b36746262ca61feeb6d42374/docs/architecture.md)

### 2.2 파일별 모델과 최소 변경 저장

DOCX 엔진은 ZIP·관계·문서 요소를 다루는 패치 모듈과 스타일 파서를 분리한다. ODT는 자체 전용 화면 대신 DOCX 브리지와 원본 요소 대응 지도를 사용하며, 저장 시 변경 부분을 원본 ODT에 반영한다. 이런 구조는 편집 모델과 저장 형식을 분리하는 참고 사례다. 단, 대응되지 않는 기능의 변환 손실까지 없애 주는 방식은 아니다. [DOCX 패치](https://github.com/pblsketch/openoffice/blob/1877ecc23bf3b4f8b36746262ca61feeb6d42374/packages/docx-engine/src/patch.ts), [ODT 경로](https://github.com/pblsketch/openoffice/blob/1877ecc23bf3b4f8b36746262ca61feeb6d42374/docs/architecture.md)

AutoDocFit도 모든 HWPX를 단순 JSON으로 재생성하지 말고, 원본 패키지와 편집 대상 위치를 보관하는 방식이 적합하다. 다만 `docfit_core/fidelity/`의 원본 보존 경로와 공문서 후처리 경로는 현재 별개이므로 전체 처리에 무손실 보장이 적용된다고 표현해서는 안 된다.

### 2.3 마인드맵과 변환의 실체

이음오피스의 마인드맵 UI 의존성은 `mind-elixir` 5.15.1이고 파일 엔진은 `packages/xmind-engine`이다. AOO Draw의 트리 엔진을 사용한다는 근거는 없다. 또한 `packages/pipelines/src/index.ts`는 조사 버전에서 slides 진입점을 내보내므로, 디렉터리 이름만으로 범용 멀티스레드 변환 프레임워크라고 판단할 수 없다. [마인드맵 의존성](https://github.com/pblsketch/openoffice/blob/1877ecc23bf3b4f8b36746262ca61feeb6d42374/apps/mindmap/package.json), [pipelines 진입점](https://github.com/pblsketch/openoffice/blob/1877ecc23bf3b4f8b36746262ca61feeb6d42374/packages/pipelines/src/index.ts)

## 3. Apache OpenOffice의 핵심 설계

### 3.1 UNO와 문서 객체 모델

UNO는 서비스·인터페이스·속성·컴포넌트 컨텍스트·언어 바인딩·프로세스 간 브리지를 제공하는 컴포넌트 체계다. Writer의 텍스트·표, Draw의 페이지·도형 등을 API로 다루게 한다. **UNO 문서 모델은 XML DOM과 동일하지 않다.** 저장 XML, 문서의 의미 모델, 배치 프레임, 화면 컨트롤러를 구분해야 한다. [UNO 공식 가이드](https://wiki.openoffice.org/wiki/Documentation/DevGuide/ProUNO/UNO_Concepts)

AutoDocFit 적용안은 UNO 바이너리 의존성을 추가하는 대신 다음 인터페이스를 Python 서비스 계약으로 정의하는 것이다.

| 제안 계약 | 책임 | 기존 연결 지점 |
|---|---|---|
| `DocumentSession` | document_id, revision, 원본 해시, 작업 사본, 변경 상태 | `docfit_core/app_state.py`, `docfit_app/application_service.py` |
| `StyleResolver` | 스타일 상속·직접 서식·보호 규칙 해석 | `format_elements.py`, `style_profile_edit.py` |
| `CommandBus` / `HistoryService` | 명령 실행·묶음·되돌리기·충돌 감지 | 기존 서비스/브리지 앞단 |
| `DocumentAdapter` | 기능 지원 조회·읽기·패치·저장·검증 | `fidelity/`, `hwpx.py`, `kordoc_bridge.py`, COM 드라이버 |

위 이름은 모두 신규 설계 제안이다. 현재 코드에 구현됐다는 뜻이 아니다.

### 3.2 Writer 표: 의미 구조 → 배치 → 페인팅

Writer는 표 내용 구조와 화면/페이지 배치 프레임을 분리한다. `tabfrm.cxx`의 `SwTabFrm`은 표 프레임의 분할·후속 프레임 병합 등을 다룬다. `paintfrm.cxx`는 배경과 테두리 페인팅을 다룬다. 따라서 표 폭 변경은 셀 수치 하나를 바꾸는 작업에서 끝나지 않고 줄바꿈·행 높이·쪽 경계 재계산과 연결된다. [표 레이아웃](https://github.com/apache/openoffice/blob/7d712b94e3ff1803b979fa5f284e7acd2daba990/main/sw/source/core/layout/tabfrm.cxx), [페인팅](https://github.com/apache/openoffice/blob/7d712b94e3ff1803b979fa5f284e7acd2daba990/main/sw/source/core/layout/paintfrm.cxx)

현재 `table_width.py`는 본문 행의 글자 수 비율과 최장 낱말의 추정 폭을 사용한다. 병합·여백을 고려하지만 폰트별 실제 글리프 폭을 측정하는 완전한 조판 엔진은 아니다. 그림·도형 등이 있는 표를 제외하는 보호 조건도 있다. 2.0에서는 다음 단계로 확장한다.

1. 셀별 최소 폭, 선호 폭, 병합 제약, 좌우 여백, 고정 폭 여부를 별도 측정 결과로 만든다.
2. 병합 셀은 `걸친 열 폭 합 ≥ 셀 최소 폭` 제약으로 처리한다. 본문 폭보다 최소 폭 합이 크면 조용히 축소하지 말고 넘침 원인을 반환한다.
3. 폭 배분 후 한/글 재조판 결과에서 행 높이·쪽 분리·글자 유실을 검사한다. 미리보기와 저장 결과에 같은 해석 결과를 사용한다.
4. 인접 셀의 공통 테두리는 한 경계로 판정한다. 선 두께·우선순위·배경·대각선은 별도 속성으로 유지하고 병합 전후 경계 불변을 검사한다.

이는 Writer의 C++ 알고리즘을 그대로 번역한 설명이 아니라 구조 분리 원칙에서 도출한 AutoDocFit 개선안이다.

### 3.3 AutoFormat과 스타일 상속

Writer의 `SwTableAutoFmt`는 위치별 `SwBoxAutoFmt`와 속성 집합을 연결한다. 표 모양을 반복 적용 가능한 데이터로 다루는 것이 핵심이다. 이를 임의의 병합·중첩 표까지 해결하는 CSS 엔진으로 해석해서는 안 된다. [AutoFormat 구현](https://github.com/apache/openoffice/blob/7d712b94e3ff1803b979fa5f284e7acd2daba990/main/sw/source/core/doc/tblafmt.cxx)

UNO의 `XStyle`은 부모 스타일을 지정하는 인터페이스를 제공한다. 이음오피스의 DOCX 스타일 파서는 `basedOn` 연결과 표의 첫 행·첫 열·마지막 행·교대 배경 등 조건부 표시 속성을 다룬다. 두 사례에서 **속성 미지정과 명시적 해제의 구분**을 배운다. 예를 들어 자식의 `bold=false`는 부모의 `true`를 취소해야 하며 미지정과 달라야 한다. [XStyle API](https://www.openoffice.org/api/docs/common/ref/com/sun/star/style/XStyle.html), [DOCX 스타일 파서](https://github.com/pblsketch/openoffice/blob/1877ecc23bf3b4f8b36746262ca61feeb6d42374/packages/docx-engine/src/parse-styles.ts)

### 3.4 Draw/Impress: 객체·스냅·연결점

Draw의 `SdrObject` 계열은 도형 객체를 공통 모델로 다루며, 스냅은 객체 자체만의 책임이 아니다. `SdrSnapView::SnapPos`·`CheckSnap` 같은 뷰 동작과 연결선 객체 구현이 함께 필요하다. **정렬 스냅**은 좌표를 맞추고, **연결점 결합**은 도형이 이동해도 선 끝이 따라오는 관계를 유지한다. [스냅 구현](https://github.com/apache/openoffice/blob/7d712b94e3ff1803b979fa5f284e7acd2daba990/main/svx/source/svdraw/svdsnpv.cxx), [연결선 소스](https://github.com/apache/openoffice/blob/7d712b94e3ff1803b979fa5f284e7acd2daba990/main/svx/source/svdraw/svdoedge.cxx)

AutoDocFit에는 `Shape(id, bounds, transform, styleRef, ports)`와 `Connector(sourceId, sourcePort, targetId, targetPort, route)`를 제안한다. 좌표만 저장하면 크기 변경·회전 뒤 연결 관계가 깨진다. 스냅 후보는 격자·가이드·모서리·중심·포트로 구분하고 확대율에 독립적인 화면 픽셀 임계값을 사용한다. 드래그 중 가이드는 임시 상태이며 놓을 때만 이력 한 건을 남긴다.

### 3.5 아웃라인과 마인드맵 자동 배치

Draw의 도형·연결선이 있다는 사실만으로 범용 마인드맵 자동 배치가 제공된다고 단정할 수 없다. 본 조사에서는 AOO의 완성된 전용 마인드맵 배치 엔진을 확인하지 않았다. 따라서 2.0 알고리즘은 독자 설계로 명시한다.

현재 앱 `diagram_editor/src/mindmap.js`에는 이미 `both/right/down` 배치, `mindmapGraph`, 부모 변경, 수동 좌표, 자동 배치 초기화가 있다. 목표는 신규 도입보다 긴 한글 라벨·접힘·수동 고정·부분 재배치의 안정화다.

제안 절차는 텍스트 실측 → 후위 순회로 서브트리 점유 높이 계산 → 전위 순회로 좌표 배정 → 좌우 가지의 점유량 균형 → 포트 기반 연결선 생성이다. 좌우 분배는 단순 번갈아 배치보다 서브트리 크기를 반영한다. 전체 배치는 트리 순회 기준 O(n)을 목표로 하되 충돌 검사와 라우팅 비용은 별도로 측정한다. 순환·다중 부모는 트리 검증에서 거부하고 일반 다이어그램 그래프와 분리한다.

### 3.6 Filter: 입력과 출력 지원을 분리

공통 파이프라인은 형식 감지 → 입력 필터 → 문서 모델 → 필요한 조판 → 출력 필터로 이해할 수 있다. PDF 출력은 원본 XML 이름 변경이 아니라 렌더링 경로다. AOO `PDFExport`는 `XRenderable`과 PDFWriter를 사용하는 페이지 출력 코드를 갖는다. [PDF 구현](https://github.com/apache/openoffice/blob/7d712b94e3ff1803b979fa5f284e7acd2daba990/main/filter/source/pdf/pdfexport.cxx)

| 형식 | AOO에서 참고할 점 | AutoDocFit의 판단 |
|---|---|---|
| ODF | 기본 문서 형식과 필터 분리 | ODT/ODS/ODP를 한 능력으로 묶지 말고 문서 유형별 지원표 관리 |
| OOXML | 읽기 지원과 쓰기 지원이 다름 | AOO를 DOCX/XLSX/PPTX 범용 출력 엔진으로 선정하지 않음 |
| RTF | 텍스트·서식 입력/출력 필터 | 표·필드·그림의 왕복 손실을 별도 시험한 뒤 채택 |
| PDF | 페이지 조판을 거치는 출력 | HWP 계열은 우선 한/글 네이티브 출력, 텍스트/OCR 재구성과 구분 |

AOO의 OOXML 저장 미지원은 공식 FAQ에서도 구분한다. LibreOffice의 지원 범위를 AOO에 옮겨 적지 않는다. 이음오피스의 DOCX/PPTX 엔진도 AOO 필터와 별개다. [AOO 형식 호환 FAQ](https://wiki.openoffice.org/wiki/Documentation/FAQ/General/Is_OpenOffice.org_compatible_with_MS_Office_and_StarOffice_file_formats%3F)

## 4. AutoDocFit의 강점과 보완점

| 항목 | 현재 근거와 평가 | 2.0에 주는 의미 |
|---|---|---|
| HWPX 원본 보존 | `fidelity/`에 패키지 보관·최소 변경·검증 경로가 있음. 모든 변환/후처리의 무손실 보장은 아님 | 미지원 요소는 보존하고 변경 범위를 명시 |
| 한국 공공 보고서 | `format_elements.py`, `style_hierarchy.py`, `marker_scheme.py`, `document_rules.py`에 역할·규칙·예시 분석 축적 | 일반 오피스보다 도메인 특화가 명확함 |
| kordoc 4.x | `kordoc_bridge.py`는 Node 변환 엔진 연결. 규범 서식 학습의 주체 전체가 kordoc인 것은 아님 | 변환과 기관별 예시 학습의 책임 분리 |
| 캐싱 런처 | 캐시 재사용 구조는 구현됨. 확인한 10-18 문서의 실제 창 표시는 약 8.5~8.7초로 1.5초 목표 미달 | '1초대 실행 달성'으로 홍보하지 않고 최신 후보 재측정 |
| 표 템플릿·리본 | `table_units.py` 정보단위 복제와 네이티브 복사, 최신 Flutter 리본이 존재 | 구조 템플릿과 시각 스타일 프리셋을 조합 |
| Undo/Redo | 편집기별 동작과 별개로 Python/Flutter/JS/COM을 잇는 전역 트랜잭션 계약을 확인하지 못함 | 공유 HistoryService 우선 설계 |
| 탭 간 스타일 | 프로필·글자·표·도형 스타일의 적용 경로가 나뉨 | 공통 스타일 ID·해석 규칙·revision 필요 |
| 표 수식·조건부 스타일 | 작성 보조 계산은 있으나 일반 의존 그래프·재계산·병합 참조 계약은 확인되지 않음 | 제한된 수식부터 단계 도입 |

근거: [코드 구조/운영 규칙](../HANDOVER.md), [캐시 런처 실측](SMART_CACHING_LAUNCHER.md), [표 너비](../docfit_core/table_width.py), [네이티브 표 복사 서비스](../docfit_app/table_units_service.py), [PPT 스타일 리본](../flutter_ui/lib/features/table_units/table_units_screen.dart), [마인드맵 모델](../diagram_editor/src/mindmap.js).

## 5. 6-탭 통합 설계

### 5.1 공통 기반과 데이터 흐름

```text
문서편집 | 표템플릿 | 표그림판 | 다이어그램 | 마인드맵 | 파일변환
                         ↓ 명령 / ↑ 상태 이벤트
DocumentSession + CommandBus + HistoryService + StyleResolver
                         ↓ 검증된 변경 계획
HWPX 최소 패치 | 표 구조 엔진 | 도형/트리 모델 | 변환 JobScheduler
                         ↓ 형식별 어댑터
HWPX ZIP/XML | 전용 COM 작업자 | kordoc/기타 변환 프로세스
                         ↓
작업 사본 → 무결성·조판 검사 → 새 결과 파일
```

각 기능 탭과 문서 ID를 분리한다. 같은 문서를 여러 탭에서 다루면 하나의 revision을 공유하고, 서로 다른 문서는 독립 이력을 가진다. 이벤트에는 `document_id`, `revision`, `command_id`, `job_id`를 넣어 늦게 도착한 미리보기가 최신 상태를 덮지 않게 한다.

### 5.2 스타일 상속 계약

스타일은 `id`, `family`, `parent_id`, `properties`, `revision`, `provenance`로 표현한다. 문단/글자/표/도형은 같은 저장 계약을 쓰되 허용 속성은 family별로 제한한다. 기관 프로필의 예시 경로·해시·표본 수를 provenance에 둔다.

제안 우선순위는 **앱 기본값 < 기관 프로필 < 문서 테마 < 이름 있는 스타일의 부모→자식 < 표 역할 조건 < 직접 서식**이다. 이것은 2.0 제품 정책이며 AOO/OOXML의 모든 해석 순서와 동일하다는 뜻이 아니다. 공문서 불변 규칙·보호 영역은 별도의 검증/적용 정책으로 두고 숨은 스타일 덮어쓰기로 처리하지 않는다.

상속은 순환을 거부하고 미지정/값/명시적 해제를 구분한다. 부모 변경 시 영향받는 자식과 미리보기 캐시만 무효화한다. HWPX가 같은 상속을 직접 표현하지 못하면 해석된 값으로 새 모양 참조를 만들고 원래 ID 대응을 보관한다. 새 ID는 기존 도형·모양 참조와 충돌하지 않아야 한다.

### 5.3 Undo/Redo 트랜잭션

명령은 `expected_revision`, 변경 대상, 이전 값/역패치, 새 값, 설명을 갖는다. 실행은 계획 생성 → 사본에 적용 → 검증 → 원자적 세션 승격 → 이력 추가 순서다. 실패·취소된 명령은 이력에 넣지 않는다. 드래그·표 프리셋 적용·다중 요소 스타일 변경은 각각 하나의 복합 명령으로 묶는다.

COM 재조판이나 여러 파일을 건드리는 작업은 역패치만으로 충분하지 않으므로 작업 전 사본 체크포인트를 사용한다. COM의 자체 Undo와 앱 이력을 이중 실행하지 않도록 어댑터가 담당 범위를 정한다. 외부 한/글에서 파일이 바뀌면 해시/revision 충돌로 재열기 또는 새 분기를 요구한다. 클립보드 붙여넣기와 이미 전달된 결과물은 앱 내부 Undo로 회수할 수 없으며 이 경계를 UI에 표시한다.

### 5.4 탭별 실행안

| 탭 | 재사용 기반 | 구체적 개선 | 완료 기준 |
|---|---|---|---|
| 1. 문서편집 | 역할 분석·예시 프로필·HWPX 패치 | 문단/글자 스타일 갤러리, 상속 출처 표시, 선택 영역 직접 서식 해제 | 부모 수정이 자식에 반영되고 명시적 해제·강조 구간 보존, Undo 왕복 일치 |
| 2. 표템플릿 | 정보단위 PLANS·표 카탈로그·PPT 리본 | 구조 선택과 AutoFormat 프리셋 분리, 머리글/본문/합계/교대행 옵션 | 단위 수 변경 후 병합·그림·ID 유지, 스타일 적용 전후 셀 텍스트 동일 |
| 3. 표그림판 | 선→격자·직사각형 병합·HWPX 출력 | 격자/기존 선/끝점 스냅, 임시 가이드, 경계 충돌 검사 | 확대율별 동일 시각 임계값, 직사각형 병합 검증, 드래그 한 번에 Undo 한 건 |
| 4. 다이어그램 | JS 도형·연결선·핸들 모델 | 중심/모서리 정렬, 포트 결합, 직교 경로, 장애물 회피 | 이동·회전·크기 변경 후 연결점 유지, 삭제/복구 시 선 참조 정상 |
| 5. 마인드맵 | 기존 트리·both/right/down 배치 | 라벨 실측·서브트리 균형·접힘·수동 고정·국소 배치 | 긴 한글 라벨 겹침 없음, 형제 순서 보존, 순환 거부, 개요 왕복 의미 동일 |
| 6. 파일변환 | kordoc·한/글 네이티브 출력·PDF 처리 | 기능 기반 경로 선택, 배경 큐, 취소/재시도/개별 실패 복구 | 원본 해시 불변, COM 동시 실행 1, 작업별 실패 격리, 손실 경고와 결과 경로 제공 |

탭 2 리본은 현재 구조를 유지하면서 ‘구조/스타일/테두리/채우기/정렬/내보내기’ 명령을 공통 CommandBus에 연결한다. 프리셋은 최소형·공공보고형·교대행형·합계강조형부터 시작한다. 구조를 바꾸지 않는 프리셋은 병합·열 폭·그림 위치를 수정하지 않는다. 구조와 스타일의 복합 적용은 별도 명령으로 명시한다.

탭 3과 4는 스냅 후보 검색을 공유하되 저장 모델을 강제로 합치지 않는다. 표그림판은 정수 격자와 병합 제약이 중요하고 다이어그램은 자유 좌표와 그래프 연결이 중요하다. 탭 5는 트리를 의미 모델로 유지하고 도형 그래프를 렌더링 결과로 생성한다.

### 5.5 표 수식과 캐스케이딩

첫 단계 수식은 숫자 상수·사칙연산·SUM으로 제한하고 셀 ID 기반 의존 그래프를 둔다. 병합 셀은 좌상단 기준 셀로 참조를 정규화하고, 정보단위 복제 시 상대/절대 참조 정책을 적용한다. 순환·0 나누기·숫자 해석 실패를 별도 오류로 표시하며 Python `eval`은 사용하지 않는다. HWPX 수식 직렬화 호환성이 검증되기 전에는 기존 수식을 보존하고 신규 수식의 네이티브 재계산 지원을 약속하지 않는다.

스타일 조건은 머리글·합계·교대행·직접 지정 순으로 명문화하고, 칸별 최종 속성과 출처를 조회할 수 있게 한다. 예컨대 합계 행의 직접 지정 굵게를 교대행 프리셋이 지우지 않도록 한다. 이 정책은 수식 계산과 독립적으로 시험한다.

### 5.6 배경 필터와 동시성

작업 상태는 `queued → running → validating → succeeded/failed/cancelled`로 정의한다. 입력·출력 형식 외에 `preserve_package`, `requires_layout`, `requires_com`, `supports_cancel`, 손실 가능 기능을 capability로 관리한다. HWP/HWPX→PDF는 한/글 네이티브 경로를 우선하고, DOCX/ODF 출력 등은 검증된 어댑터가 있을 때만 지원 목록에 노출한다.

**멀티스레드 배치는 COM 병렬 호출을 뜻하지 않는다.** 파일 탐색·해시·I/O는 제한된 스레드 풀, CPU 작업은 필요 시 프로세스, kordoc은 동시 수를 제한한 자식 프로세스, 한/글은 COM 초기화·사용·종료를 같은 스레드에서 수행하는 전용 작업자 하나로 분리한다. COM 객체를 스레드 간 전달하지 않는다. 여러 문서가 겹쳐 들어와도 COM 큐는 직렬이다.

COM 시험은 `C:\HWP_AUTODOCFIT\.com-test.lock`을 반드시 사용한다. 제품 실행 간 중복 처리는 별도 프로세스 잠금/뮤텍스로 설계하며 시험 잠금을 제품 동기화 구현의 대체물로 취급하지 않는다. 취소·시간 초과 시 자신이 만든 작업자/PID만 정리한다. 출력은 작업별 임시 디렉터리에서 검증한 뒤 새 파일명으로 원자 저장하고 원본은 덮어쓰지 않는다.

캐시 키는 원본 해시+엔진 버전+필터 옵션+스타일 revision+렌더링 환경 식별자를 포함한다. 작업마다 재시도 가능 여부와 실패 단계를 기록한다. 지원되지 않는 기능은 조용히 버리지 말고 그림 대체·생략·서식 단순화 등을 결과 경고로 반환한다. 재구성 변환을 무손실 패치로 표시하지 않는다.

## 6. 도입 로드맵과 검증 게이트

기간은 인력·실문서 코퍼스·COM 안정성 확인 전의 순서 제안이며 일정 확약이 아니다.

| 단계 | 우선순위 | 산출물과 의존성 | 통과 조건 |
|---|---|---|---|
| A. 계약 정리 | P0 | DocumentSession, capability 표, 공통 이벤트, 원본/작업 사본 정책 | 동일 문서 동시 명령 충돌 검출, 원본 해시 불변 |
| B. 이력·스타일 | P0 | CommandBus/HistoryService, StyleResolver, 기존 프로필 마이그레이션 | 트랜잭션 실패 복원, 상속 순환 거부, 구버전 프로필 결과 유지 |
| C. 문서·표 | P1 | 탭 1 스타일 갤러리, 탭 2 리본 프리셋, 폭 제약 측정 | 기존 서식 재연 기준 유지, 병합·중첩 표·그림 보존 |
| D. 그래픽 공통화 | P1 | 탭 3/4 스냅·포트·이력, 탭 5 부분 배치 | 확대/이동/회전/삭제·Undo 후 연결 일관성 |
| E. 변환 작업화 | P1 | COM 직렬 큐, 제한된 비COM 병렬 처리, 취소·재시도 | UI 응답 유지, 작업 실패 격리, 원본 보존, 고아 프로세스 없음 |
| F. 고급 계산·필터 | P2 | 제한 수식, 참조 복제, 선택적 외부 필터 | 계산 오류 명시, 형식별 손실표·실문서 왕복 근거 |

성능 목표는 새로 측정할 제품 기준으로 정한다. 시작 시간은 cold 추출·warm 캐시·실제 주 화면 표시를 분리하고, 변환 시간은 대기/파싱/조판/저장을 나눠 p50·p95와 실패율을 기록한다. 1.5초 실행과 마인드맵 대규모 배치는 목표값이지 이번 분석에서 입증된 성능이 아니다.

필수 검증은 다음과 같다.

- 순수 모델: 상속/명시적 해제, 병합 제약, 수식 순환, 트리 검증, revision 충돌, Undo/Redo 상태 왕복.
- 파일: 미수정 패키지 항목·미지원 요소 보존, 변경 참조 ID 유효성, 텍스트/필드/그림 보존, 실패 시 결과 승격 금지.
- UI: 6탭 상태 공유, 늦은 미리보기 폐기, 스냅 가이드, 키보드 조작, 작업 취소·개별 실패 표시.
- 실기기: 잠금 하에 사본으로 한/글 재열기·저장·PDF/붙여넣기 확인. XML 비교와 실제 조판 검사를 함께 사용.
- 회귀/배포: `.venv\Scripts\python.exe -m unittest discover -s tests`, 해당 Flutter/JS 검사, `scripts/format_fidelity_pc.py`와 저장소 릴리스 검수 절차. 문서만 작성한 이번 작업에서는 앱 시험과 COM을 실행하지 않았다.

## 7. 채택과 보류 결정

**채택:** 이음오피스의 셸/엔진 경계와 원본 대응 지도, AOO의 스타일 부모 관계·표 모델/배치/페인팅 분리·스냅/연결점 구분·필터 계약. 먼저 공통 이력·스타일을 만들고 기존 리본과 편집기를 연결한다.

**보류:** AOO 전체 내장, UNO 런타임 필수화, HWPX를 중간 일반 모델로 전면 재생성, COM 다중 스레드 호출, 검증되지 않은 OOXML 출력 지원, Draw에 전용 마인드맵 알고리즘이 있다는 가정.

저장소 운영 규칙에 따라 외부 코드는 옮기지 않고 설계 아이디어를 독자 구현한다. 실제 의존성 도입을 검토하는 경우에만 별도로 LICENSE/NOTICE와 전이 의존성을 확인한다. 이번 산출물은 분석 문서이며 엔진 추가·UI 수정·버전 승격·공개 배포를 포함하지 않는다.

## 8. 근거 및 재현 범위

외부 근거는 본문에 연결한 이음오피스 고정 SHA의 구조/패키지/패치/스타일 파일, AOO 고정 SHA의 Writer/Draw/PDF 소스와 공식 UNO/API/호환성 문서다. 연결선 파일의 존재와 공통 모델은 검토했으나 전 라우팅 알고리즘의 정확성·성능을 검증한 것은 아니다. 외부 문서의 기능 설명과 소스 관찰, 본 보고서의 신규 설계 제안을 구분했다.

내부 근거는 `HANDOVER.md`, 공동 작업 지침, 캐싱 런처 실측 및 본문에 명시한 소스다. 다른 2.0 worktree의 미통합 구현은 현재 기준 기능으로 산입하지 않았다. 기존 W1~W3 공동 작업은 현황판에서 완료/판정 대기로 기록되어 있어 이번 문서 작업에서 재수정하지 않았다. 사용자 문서 원본과 `hwp-auto-docfit.py`는 변경하지 않았다.
