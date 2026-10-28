# P6 설계서 — 2.0.1 편집기 화면 축소·확대 대응

작성: Codex, 2026-10-28. 설계 전용이며 이 문서 작성 과정에서는 제품 코드·시험 코드를 변경하지 않았다.

작업 루트: `C:\HWP_AUTODOCFIT\v1803\resp`, 브랜치 `feature/2.0.1-responsive`, 조사 HEAD `ea84ccfebbe35ead55b24b844cb737e6654a7b22`(v2.0.0 main 기준). 아래 행 번호는 이 HEAD의 실제 파일 기준이다. 앞선 수정으로 행이 이동하면 함께 적은 함수명·코드 앵커로 찾는다. 출력 정본은 `C:\HWP_AUTODOCFIT\v1803\reports\P6-design.md`, 저장소 보관본은 `docs/P6-design.md`다. 사용자 메시지에서 제어문자로 깨진 경로 및 빈 `-design.md`는 명확하게 제시된 P6 경로로 해석한다.

## 1. 구현 범위와 조사 결과

목표는 창 축소·확대 시 툴바와 패널의 모든 기존 동작에 접근할 수 있게 하는 것이다. 넘치는 도구는 가로 스크롤로 제공한다. 폭 700 이하에서는 툴바 버튼의 텍스트를 아이콘으로 바꾸고, 측면 패널은 기본 접힘으로 제공한다. 패널 내부 폼의 이름·설명·입력값까지 감추지는 않는다. 키·콜백·명령·파일 형식·편집 기능은 바꾸지 않는다. 이번 과제에서 허용된 반응형 표시 변경 외 기능 변경은 하지 않는다.

확인한 구조:

| 대상 | 실제 구현과 문제 지점 |
|---|---|
| 표그림판 | `table_sketch_screen.dart` 794~1381. 상단 도구줄은 이미 가로 스크롤이지만 AppBar는 600 미만만 아이콘 처리한다. 선 굵기·종류는 항상 글자 칩이다. 본문은 750 미만에서 아래 패널을 높이 260으로 붙이고, 넓으면 우측 320 고정 패널이다. |
| 표 템플릿 | `table_units_screen.dart` 1793~5553. 760 이상은 갤러리+10폭 분할선+상세 패널, 미만은 전체 갤러리와 상세를 세로로 이어 붙인다. 상세 제목줄의 긴 복사·초기화 버튼, 높이 36인 검색/카테고리 줄, 48인 복사 버튼이 확대에 취약하다. 이 파일은 불필요한 빈 줄도 많으므로 전체 포맷을 하지 않는다. |
| 다이어그램 native | `diagram_editor_screen_native.dart` 482~529는 AppBar와 Webview 호스트다. 실제 도구는 `diagram_editor/src/main.jsx`와 `style.css`에 있다. |
| 흐름도 native | `flow_editor_screen_native.dart` 1~13은 위 DiagramEditorScreen을 호출하는 래퍼다. 중복 툴바를 만들지 않는다. |
| 흐름도 web | `flow_editor_screen_web.dart` 392~432는 AppBar와 HtmlElementView iframe이다. 같은 웹 편집기를 띄운다. |
| 웹 편집기 | `main.jsx` 479~535의 header/nav/aside, `style.css` 1~2의 전역 overflow:hidden, 헤더 wrap 및 고정 aside 폭이 원인 후보다. 현재 좁은 미디어쿼리는 650 이하에서 aside를 155로 줄일 뿐 접지 않는다. 다이어그램·마인드맵이 현재 활성 모드이고 표 템플릿은 Flutter 화면으로 이동한다. |

이 진단은 정적 조사 결과이며 실제 화면 재현 완료를 의미하지 않는다. `diagram_editor_screen.dart`, 각 stub 및 native flow 래퍼의 조건부 export/생성자/initialMode 전달 정책은 변경하지 않는다. 특히 native의 initialMode 미사용은 별도 문제이며 P6에 섞지 않는다. 비활성화된 흐름표·기본 표·catalog·org·bar를 다시 활성화하지 않는다.

중요: Flutter 위젯 시험은 iframe/WebView 내부 CSS overflow를 볼 수 없다. 따라서 Flutter 실제 화면 위젯 시험과 내장 웹 편집기 브라우저 시험을 모두 완료 기준으로 둔다. Webview를 빈 박스로 대체한 위젯 시험만으로 전체 합격이라고 보고해서는 안 된다.

검수 참고 확인: 2026-10-28 재확인 시 `C:\HWP_AUTODOCFIT\v1803\reports\O5.md`는 존재하지 않았다. 따라서 DeepSeek 지적을 읽거나 수용했다고 간주하지 않는다. 추후 파일이 제공되면 구현 담당자는 지적별 코드 근거·수용/보류 이유를 추가하되 P6 범위를 넘는 기능 변경은 분리한다. 기존 설계 커밋 `56baa77` 이후 대상 제품 소스 변경이 없음을 확인했으므로 위 기준 HEAD의 행 번호를 유지한다.
## 2. 변경 파일 TARGET 목록

24,000자가 넘는 기존 파일은 수정에 필요한 넓은 범위를 명시했다. 한 파일당 TARGET 한 줄이며 여러 구간은 세미콜론으로 구분한다. 새 파일의 1-1은 현재 파일이 없다는 뜻으로, 지정 내용 전체를 새로 작성한다.

TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\lib\core\widgets\editor_responsive.dart:1-1 (신규 전체)
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\lib\features\table_sketch\table_sketch_screen.dart:1-90;794-1112;1210-1381
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\lib\features\table_units\table_units_screen.dart:1-240;1793-2381;2389-3320;3330-3908;4097-4433;4961-5109;5373-5553
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\lib\features\diagrams\diagram_editor_screen_native.dart:1-24;482-529
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\lib\features\flows\flow_editor_screen_web.dart:1-25;392-432
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\diagram_editor\src\main.jsx:1-23;235-246;479-535;583-656
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\diagram_editor\src\style.css:1-35;54-65;91-105
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\test\editor_responsive_test.dart:1-1 (신규 전체)
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\test\table_sketch_responsive_test.dart:1-1 (신규 전체)
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\test\table_units_responsive_test.dart:1-1 (신규 전체)
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\test\editor_host_responsive_test.dart:1-1 (신규 전체, VM/native)
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\test\editor_host_web_responsive_test.dart:1-1 (신규 전체, browser 전용)
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\test\support\responsive_test_support.dart:1-1 (신규 전체)
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\flutter_ui\test\table_sketch_test.dart:610-651
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\scripts\verify_editor_responsive.py:1-1 (신규 전체)
TARGET:C:\HWP_AUTODOCFIT\v1803\resp\scripts\verify_flow_editor.py:119-142

생성 자산은 손으로 고칠 TARGET이 아니다. `scripts/build_flow_editor.ps1` / Vite가 `flutter_ui/assets/flow_editor/`를 재생성하며 이 저장소에서는 이 자산들이 추적된다. 실행 담당자는 기존 해시 JS/CSS 제거와 새 manifest/index/notices/JS/CSS 추가를 한 묶음으로 검토·커밋한다. 생성물을 고치거나 이름만 바꾸어 빌드를 대체하지 않는다. `desktop_web/flutter/`는 생성·미추적 상태를 유지한다. 패키지 의존성·lockfile 변경은 필요 없다.

## 3. 공통 표시 계약과 새 자료 구조

### 3.1 폭과 배율

레이아웃 기준 폭은 부모가 준 유한 `LayoutBuilder.constraints.maxWidth`(Flutter logical px)다. 플랫폼 전체 화면 크기를 사용하지 않는다. AppBar의 압축 여부도 Scaffold를 감싼 최상위 LayoutBuilder에서 계산하여 전달한다. 웹은 iframe 내부 `window.matchMedia('(max-width: 700px)')`와 CSS가 같은 경계를 쓴다.

`compact = width <= 700.0`. 700은 아이콘/접힘, 701은 보통 표시다. 테스트는 699·700·701도 별도 확인한다. 넓은 창이어도 패널 내부처럼 실제 남은 폭이 부족한 툴바는 언제나 스크롤한다. 700보다 넓다는 이유로 스크롤을 끄지 않는다.

시험에서 '배율'을 두 종류로 명확히 기록한다.

1. 글자 확대: logical width를 420/700/1024/1440으로 유지하고 `TextScaler.linear(1.0/1.5)`를 적용한 필수 8조합.
2. 창/디스플레이 확대: 물리적 가용 폭 W, 높이 900에 대해 DPR=배율, logical width=W/배율 및 logical height=900/배율로 검사하는 추가 8조합. DPR만 바꾸고 physicalSize도 같은 배수로 키워 logical 폭을 유지하는 시험을 창 축소 시험이라고 부르지 않는다.

브라우저도 필수 CSS viewport 폭 4종 및 콘텐츠 글자 확대 1.0/1.5를 검사하고, 화면 확대 보충 조합은 viewport를 W/배율, 900/배율로 줄인다. `device_scale_factor=1.5`만으로 CSS zoom을 시험했다고 보고하지 않는다. 브라우저 글자 확대는 시험에서 iframe의 button/select/input/textarea 및 일반 UI 텍스트 계산 글꼴에 배수를 적용하되 그래프 문서 좌표·노드 텍스트 크기는 바꾸지 않는다. 실제 WebView2/OS 확대 실측은 별도 결과로 구분한다.

### 3.2 editor_responsive.dart 신규 API

아래 선언을 구현한다. 순수 표시 컴포넌트이며 저장·API·문서 상태를 갖지 않는다.

```dart
const double editorCompactWidth = 700.0;
bool isEditorCompact(double width);

class EditorToolbar extends StatefulWidget {
  const EditorToolbar({super.key, required this.children,
    this.padding = const EdgeInsets.symmetric(horizontal: 8, vertical: 4)});
  final List<Widget> children;
  final EdgeInsetsGeometry padding;
  @override State<EditorToolbar> createState();
}

class EditorAction extends StatelessWidget {
  const EditorAction({super.key, required this.compact, required this.icon,
    required this.label, required this.onPressed, this.selected = false});
  final bool compact;
  final IconData icon;
  final String label;
  final VoidCallback? onPressed;
  final bool selected;
  @override Widget build(BuildContext context);
}
```

EditorToolbar는 자기 ScrollController 하나를 생성·dispose한다. Scrollbar(controller 동일, thumbVisibility:true) → SingleChildScrollView(horizontal, controller 동일) → Row(mainAxisSize:min, children) 구조다. ScrollConfiguration으로 mouse/touch/stylus/trackpad drag를 허용한다. 기존 수직 휠 이벤트를 강제로 가로로 바꾸지는 않는다. 키보드 focus 이동 시 `Scrollable.ensureVisible`로 현재 도구를 노출한다. 높이를 고정하지 않고 버튼 intrinsic height를 따른다. 가로 스크롤 자식에 Expanded/Spacer를 넣지 않는다. 같은 컨트롤러를 두 스크롤뷰에 연결하지 않는다.

EditorAction은 compact일 때 Tooltip과 IconButton, 보통일 때 TextButton.icon으로 같은 onPressed를 연결한다. selected는 아이콘 색/배경 및 Semantics.selected로 보인다. onPressed가 null인 경우 두 표현 모두 비활성이다. label은 기존 한국어 동작명/tooltip을 쓰며 compact에서도 Semantics.label이 남아야 한다. 동일 동작을 두 개 동시에 렌더링하지 않는다. 기존 Key는 EditorAction의 super.key로 옮기고 내부 IconButton에 중복 부여하지 않는다. 기존 배경 강조 등 특별한 버튼은 이 컴포넌트에 억지로 넣지 말고 같은 compact 계약으로 기존 버튼을 분기한다.

새 UI 상태는 각 화면 State에만 둔다. `_dockPanelVisible: bool = true`는 넓은 화면 패널 표시 상태이며 파일·설정·snapshot에 저장하지 않는다. 좁은 화면 Drawer는 항상 닫힌 상태로 진입한다. 좁은 화면의 Drawer 열기와 넓은 패널 접기는 기존 문서 dirty/generation/history를 변경하지 않는다. compact로 바뀔 때 열려 있던 wide 패널을 강제로 Drawer로 열지 않는다. 넓어지면 `_dockPanelVisible` 값에 따라 원래 docking 상태를 복구한다.

## 4. 표그림판 구현 지시

1. import와 State 위쪽에 공통 위젯 import와 `_dockPanelVisible`을 추가한다. 기존 `tableSketchScreen` Key는 Scaffold에서 유지한다. Scaffold 아래 Builder의 Scaffold.of(context)로 endDrawer를 여는 방식으로 구현하고 Scaffold key는 교체하지 않는다.
2. build 794~913의 CallbackShortcuts/Focus는 그대로 두고 그 안에 LayoutBuilder를 넣어 Scaffold/AppBar/body에 같은 compact를 전달한다. `_buildTopToolbar({required bool isNarrow})`의 이름·인자는 유지하여 호출부 변경을 줄인다. isNarrow에 <=700 결과를 전달한다. 600/750 별도 분기 제거.
3. AppBar 제목은 현재 Flexible+ellipsis를 유지한다. actions는 고정 전체 Row 대신 폭 상한 `constraints.maxWidth * 0.62`를 가진 EditorToolbar 하나에 기존 조직도·undo·redo·clearAll과 패널 토글을 넣는다. actions의 전체 폭이 제목·leading을 잠식하지 않게 titleSpacing을 조정하며 버튼은 축소하지 않는다. `sketchOrgExample`은 <=700에서 아이콘만, 넓으면 기존 OutlinedButton.icon 유지. undo/redo/clear 활성 조건·tooltip·키 그대로.
4. 새 토글 Key `sketchPanelToggle`, tooltip `미리보기·저장 패널`. compact에서는 Scaffold endDrawer 열기, wide에서는 `_dockPanelVisible` 토글이다. endDrawer는 SafeArea+닫기 버튼(Key `sketchPanelClose`)+Expanded(panel)로 구성한 Drawer이며 폭은 min(360, maxWidth-24), 높이는 Scaffold가 제한한다. modal barrier/Escape/닫기를 통해 닫을 수 있어야 한다.
5. 본문은 항상 Row → Expanded → Column(toolbar, Expanded(canvas)) 경로를 유지하고, 우측 320 패널만 `!compact && _dockPanelVisible`일 때 붙인다. 기존 compact 하단 패널은 없애고 Drawer로 접근한다. 캔버스의 타입·Key·부모 경로를 폭에 따라 교체하지 않아 pointer/scroll 상태가 보존되게 한다. 패널은 한 시점에 dock 또는 drawer 한 곳에서만 만든다. 넓은 화면에는 endDrawer 콘텐츠를 중복 생성하지 않는다.
6. toolbar 916~1026의 기존 가로 스크롤을 EditorToolbar로 교체한다. 여섯 도구 키와 동작은 그대로다. 굵기/종류 제목은 compact에서 숨기고, `_widthChip(String width, String label, Key key, {bool compact = false})`, `_styleChip(String style, String label, Key key, {bool compact = false})`로 확장한다. 기존 ChoiceChip.selected/onSelected를 유지하면서 compact의 label만 선 굵기/실선·파선·점선 CustomPaint 또는 구별 가능한 Icon으로 바꾸고 Tooltip(label)을 추가한다. 굵기 키 thin/thick/double 및 종류 solid/dash/dot는 문자열까지 유지한다. 확대율 수치는 상태값으로 계속 표시한다. zoom 동작 범위·식은 변경하지 않는다.
7. panel 1210~1381의 maxHeight:260 제약을 제거한다. 부모에서 높이를 제한하고 panel 내부 SingleChildScrollView가 수직 스크롤을 담당한다. 기존 isNarrow 인자는 유지한다. 미리보기 제목은 Expanded(Text)+로딩 아이콘으로, 저장 이름+저장 버튼 Row는 로컬 폭이 부족하면 Column으로 배치한다. 복사·불러오기 버튼은 compact에서 아이콘+tooltip, 넓으면 기존 label. 입력 폼의 '서식 이름'과 경고·크기는 계속 표시한다.
8. `_doc`, `_tool`, `_lineWidth`, `_lineStyle`, `_zoom`, 두 스크롤 컨트롤러, undo/redo 스택, debounce, API 메서드는 변경하지 않는다. 패널 토글/resize 자체가 preview·save·copy 요청을 추가 발생시키면 실패다.

## 5. 표 템플릿 구현 지시

1. 공통 import와 `_dockPanelVisible`을 State에 추가한다. top LayoutBuilder에서 <=700 compact를 계산한다. `btnGenerateThumbnails`는 compact에서 같은 key의 IconButton(tooltip `스냅샷 새로 만들기`), wide에서 기존 TextButton.icon이다. 로딩 중 스피너와 비활성 조건을 보존한다. 제목은 한 줄 ellipsis다.
2. `_buildBody()` 1921~2381은 loading/error 반환을 보존한 뒤 LayoutBuilder에서 compact 여부를 판단한다. 기존 wide Row의 gallery 폭/분할선/상세 스크롤을 보존한다. compact에서는 상세를 Expanded 전체 영역에 유지하고 갤러리는 Drawer로 연다. endDrawer든 drawer든 한 방향으로 고정하며 여기서는 **좌측 drawer**를 쓴다. 새 AppBar Key `tableUnitsGalleryToggle`, tooltip `템플릿 목록`을 추가한다. wide에서는 같은 버튼으로 왼쪽 갤러리를 접고 펼친다. compact 초기에는 상세의 기존 자동 선택 결과가 표시되고 목록은 닫혀 있어야 한다.
3. Drawer는 폭 min(420, width-24), SafeArea, 목록 제목+닫기(Key `tableUnitsGalleryClose`), Expanded(_buildGallery())로 구성한다. 항목 선택 콜백은 기존 `_selectTemplate` 호출을 그대로 사용하고 그 후 compact Drawer만 닫는다. 함수를 다시 작성하여 cellTexts 초기화 정책 등을 바꾸지 않는다. 선택 도중 loading 상태가 돌아도 사용자 조작에 모달을 띄우지 않는다.
4. wide 폭 계산 2045~2053은 오른쪽 상세 최소폭에 확대와 padding을 반영한다. `detailMin = max(280.0, 280.0 * MediaQuery.textScalerOf(context).scale(14) / 14)`; `maxLeft = max(220.0, width - detailMin - 10.0)`; `defaultLeft = min(460.0, width*0.42).clamp(220.0,maxLeft)`; `leftWidth = (_leftPaneWidth ?? defaultLeft).clamp(220.0,maxLeft)`. wide 진입 최소 701에서는 이 식의 합이 width 이하인지 확인하고 detailMin+230이 width를 초과하면 패널을 자동 비도킹시킨다(토글은 Drawer 열기로 작동). `_leftPaneWidth` 원값을 clamp 결과로 덮어쓰지 말아 넓어졌을 때 사용자가 선택한 폭을 복구한다. 분할선 drag/doubleTap 복구 동작 유지.
5. 갤러리 2389~3320: 검색 입력의 height:36을 최소높이로 바꾸고 입력 글자/힌트가 1.5배에서 잘리지 않게 한다. 카테고리 리본은 기존 좌우 버튼 `btnCategoryRibbonLeft/Right`, scroll controller, `categoryChip_$cat`을 유지한다. 높이 28/36은 텍스트 배율을 반영한 최소높이로 바꾸며 수평 스크롤을 유지한다. 가로 화살표를 글자와 겹치게 absolute 배치하지 않는다. 필터·개수 Row는 Expanded 텍스트 또는 Wrap으로 폭을 보장한다.
6. 갤러리 그리드 3330~3425: 고정 2열·비율 0.82는 작은 Drawer+큰 글자에 부적절하다. `SliverLayoutBuilder`로 grid 폭을 받고, `crossAxisCount = width < 360 || textScale > 1.2 ? 1 : 2`, mainAxisExtent는 `220 + (textScale-1)*100` 이상으로 정한다. textScale은 위 scale(14)/14로 계산한다. 카드 내 이름은 기존 줄 수·ellipsis를 유지하고 전체 이름 Tooltip을 제공한다. 카드 정보/즐겨찾기/선택 콜백·Key는 변경하지 않는다. 전체 파일의 빈 줄을 지우거나 formatter로 5700행 전체를 재작성하지 않는다.
7. `_buildDetail()` 4165~4429의 제목+복사+글 지우기 한 Row를 제목 영역과 EditorToolbar 동작 영역으로 분리한다. 제목은 줄바꿈 허용, 복사/초기화는 <=700에서 아이콘만. wide라도 실제 detail 폭이 작으면 toolbar만 가로 스크롤한다. 기존 `btnTopCopyTable`, `btnClearCellTexts`, 활성 조건을 그대로 전달한다. clear는 실제 입력이 있는 경우에만 생긴다.
8. bottom `btnCopyTable` 높이 48은 minHeight:48로 바꾸고 동일 compact 표시를 적용한다. `_buildStepper()`는 label Expanded와 +/- 영역이 겹치면 Wrap/Column으로 분기한다. 이름·count는 보이고 plus/minus min/max/loading 조건을 유지한다. `_buildFillSelector()`의 Wrap과 입력 양식 라벨은 유지한다. detail 수직 Scrollbar와 controller를 한 곳에만 attach한다.
9. 검색·분류·즐겨찾기·최근 사용·선택·편집한 칸 글·행열 count·fill·preview/cache·copy error는 기존 State 소유다. resize/toggle로 `_loadList`/`_selectTemplate`를 재실행하지 않는다. gallery/detail scroll 위치는 PageStorageKey를 각각 부여해 보존한다. Drawer 밖에서 다시 생성할 때 SearchController를 새로 만들지 않는다.

### 5.1 코더의 함수 변경 범위와 키 대조표

신규 표시 헬퍼가 필요한 경우 아래 시그니처로 고정한다. `compact`는 최상위 유한 폭에서 계산한 값이고, 상세 패널 자체의 좁은 폭을 화면 compact로 오인하지 않는다.

```dart
// table_sketch_screen.dart, State에 추가. 기존 데이터 메서드는 그대로 사용.
Widget _buildPanelDrawer({required double availableWidth});
// table_units_screen.dart, 기존 인자 없는 두 함수를 아래로 변경하고 호출부 전체 갱신.
Widget _buildBody({required bool compact});
Widget _buildDetail({required bool compact});
Widget _buildGalleryDrawer({required double availableWidth});
Widget _buildGallery({bool shrinkWrap = false, VoidCallback? onTemplateSelected});
```

Drawer 열기 콜백은 Scaffold 아래 Builder의 context를 받는다. 갤러리 카드의 기존 `_selectTemplate(template)` 다음에 `if (compact && Scaffold.of(context).isDrawerOpen) Scaffold.of(context).closeDrawer()`를 실행할 때, 이 compact는 최상위 화면 판정값을 사용한다. State의 읽기 전용 getter로 숨겨 계산하지 말고 build에서 결정한 값을 갤러리 카드 콜백까지 전달하는 지역 함수/클로저로 연결한다. 선택 로직 자체인 821행 `_selectTemplate`는 변경하지 않는다. `_buildGallery`에서 이 값이 직접 필요하면 선택 후 닫기를 담당하는 콜백을 optional named 인자로 추가하고, 모든 호출부에서 동일 콜백을 전달한다: `Widget _buildGallery({bool shrinkWrap = false, VoidCallback? onTemplateSelected})`. 카드 탭에서 기존 선택 처리를 마친 직후에만 `onTemplateSelected?.call()`을 호출한다. wide에서는 null을 전달한다. 신규 `_buildGalleryDrawer`의 내용에서 닫기 콜백을 제공한다.

| 실제 위치 | 보존할 Key / 점검 |
|---|---|
| 표그림판 815~866 | `tableSketchScreen`, `sketchOrgExample`, `undoButton`, `redoButton`, `clearAllButton` |
| 표그림판 929~990 | `toolLine`, `toolRect`, `toolEraser`, `toolPreciseEraser`, `toolText`, `toolSelect`, `lineWidthThin`, `lineWidthThick`, `lineWidthDouble`, `lineStyleSolid`, `lineStyleDash`, `lineStyleDot` |
| 표그림판 1186, 1302~1369 | `sketchCanvas`, `sketchCopyButton`, `sketchNameField`, `sketchSaveButton`, `sketchListButton` |
| 표 템플릿 1865, 2445~3085 | `btnGenerateThumbnails`, `searchTextField`, `btnCategoryRibbonLeft`, `categoryChip_$cat`, `btnCategoryRibbonRight` |
| 표 템플릿 3441~3881 | `templateCard_${template.id}`, `btnFavorite_${template.id}`; 카드 이름 Tooltip/탭 후 Drawer 닫기 및 갤러리 scroll 연결을 포함하는 수정 범위 |
| 표 템플릿 4277~5305 | `btnTopCopyTable`, `btnClearCellTexts`, `tableGridPreview`, `fixedTableNotice`, `btnRowMinus`, `btnRowPlus`, `btnColMinus`, `btnColPlus`, `colWidthNotice`, `btnCopyTable`, `copyErrorMessage`, `fillOption_increment`, `fillOption_blank`, `fillOption_copy` |

표그림판 `_saveNameController`(58행), `_vScroll`/`_hScroll`(71~72행), 표 템플릿 `_searchController`(141행), gallery/detail/category 컨트롤러(197~205행)는 기존 State에서 계속 소유·dispose한다. 도킹/Drawer 전환 중 동일 ScrollController가 두 활성 ScrollPosition에 동시에 붙지 않게 한 곳만 구성한다. 일반 PageStorageKey는 서로 다른 subtree 간 이동을 자동으로 해결하지 않으므로 gallery/detail 각각 동일한 PageStorageBucket을 State에 `final PageStorageBucket _galleryBucket = PageStorageBucket();` 및 `final PageStorageBucket _detailBucket = PageStorageBucket();`로 보관하여 dock/Drawer 어느 위치에서도 같은 bucket+key를 사용하거나 기존 컨트롤러 offset을 유한 범위로 복원한다. 새 GlobalKey로 본문 전체를 갈아 끼워 문제를 숨기지 않는다.
## 6. 웹 편집기와 Dart 호스트 구현 지시

### 6.1 main.jsx

최상위 유틸 영역(21행 다음)에 다음 컴포넌트/훅을 추가한다. 외부 라이브러리 추가 없음.

```jsx
function useEditorCompact() // boolean, matchMedia max-width:700px 구독/해제
function ToolbarAction({label, icon, onClick, disabled=false, className=''})
function ToolbarSelect({label, icon, value, onChange, children})
```

ToolbarAction은 `<button title={label} aria-label={label} ...>` 안에 aria-hidden 아이콘과 `.tool-label` span을 둔다. ToolbarSelect는 label을 숨겨도 native select를 화면 밖으로 보내지 않는다. compact에서 아이콘 위에 투명한 select를 동일 크기로 겹쳐 두어 click/Tab/화살표가 실제 select에 도달하게 한다. aria-label `예시 서식`, option value, onChange를 유지한다. select의 width/height를 0으로 만들거나 display:none 하지 않는다. wide에는 기존 select 문구가 보인다.

아이콘은 기존 Unicode 기호 또는 작은 inline SVG로 만든다. icon 매핑은 새 문서=문서+, 열기·삭제=폴더, 저장=디스크, 그림 복사=겹친 사각형, PNG=아래화살표, 예시 서식=레이아웃 격자, 다이어그램=연결 상자, 마인드맵=가지, 표 템플릿=격자다. 아이콘 그림과 aria-label이 일치해야 한다.

App 235~246에 compact 훅, `dockPanelVisible=true`, `compactPanelOpen=false`, 토글 버튼 ref를 추가한다. `panelVisible = compact ? compactPanelOpen : dockPanelVisible`. compact 변경 effect는 compactPanelOpen만 false로 닫고, graph/선택/dirty/history는 만지지 않는다. document keydown listener를 새로 만들 경우 Escape가 패널을 닫을 때에만 처리하고 기존 키 이벤트에 영향을 주지 않는다.

header 483~494를 제목/문서명 한 줄, 두 번째 mode-tabs scroll 영역, 세 번째 nav scroll 영역으로 분리한다. 높이는 intrinsic이며 flex-shrink:0이다. 각 scroll 영역은 하나의 nowrap Row로, 자식은 flex:0 0 auto다. tab role/aria-selected/React key 및 onClick을 유지하고 tab 안에 icon+tool-label을 넣는다. ToolbarAction으로 동작 표현만 교체하며 send/handle/current 콜백은 옮겨도 내용은 바꾸지 않는다. `busy ? 'PNG 변환 중…' : 'PNG 내보내기'` 상태 문구는 title/accessible name에도 보존한다.

nav의 끝이 아니라 항상 노출되는 고정 슬롯에 패널 버튼을 둔다: `data-testid="editor-panel-toggle"`, aria-label `도구·속성 패널`, aria-controls `editor-tools-panel`, aria-expanded. compact에서 toggle은 compactPanelOpen, wide에서 dockPanelVisible만 바꾼다.

workspace 495~535에서 활성 diagram/mindmap aside를 단일 `<div id="editor-tools-panel">`로 감싼다. diagram/mindmap 조건부 aside 내부는 그대로 둔다. 숨김 상태는 패널 wrapper의 hidden 속성/display:none으로 구현하여 React 문서 상태를 버리지 않는다. compact 열린 상태는 workspace 안에서 position:absolute인 덮개 패널(폭 min(340px,calc(100% - 24px)), 높이 100%, overflow-y:auto, z-index는 그래프보다 높게)이며 반대편 배경막 클릭·닫기 버튼·Escape로 닫힌다. role=region, 접근성 이름 `도구·속성`을 부여하며 진짜 modal로 선언하지 않는다. 닫을 때 focus를 토글로 복귀시킨다. 패널 속 필드에 포커스가 있을 때 자동 접힘 resize가 발생해도 사라진 필드에 focus를 남기지 않는다. main/ReactFlow는 항상 같은 DOM/React 인스턴스로 유지한다. panel만 열고 닫아 fitView를 호출하지 않는다.

선택 도형·선·다중 정렬·마인드맵 가지의 원래 controls를 이 패널에 그대로 둔다. 비활성 TABLE_KINDS/catalog 코드를 재작성하거나 활성화하지 않는다.

### 6.2 style.css

기존 2행의 압축 CSS에서 header/nav/aside/workspace/main 규칙만 분리해 읽기 쉽게 옮긴다. 문서 노드의 실제 svg/폰트/크기/테두리 CSS는 변경하지 않는다. 650px 미디어쿼리는 새 700px 계약으로 대체하고 중복 충돌을 남기지 않는다.

- `.editor-shell,.workspace,main`에 min-width:0/min-height:0를 적절히 둔다. workspace position:relative. main은 flex:1, panel wide는 기존 폭210에 flex-shrink:0. panel 내부 aside는 width:100%, min-width:0.
- mode-tabs/nav는 overflow-x:auto, overflow-y:hidden, white-space:nowrap, flex-wrap:nowrap이며 스크롤바를 숨기지 않는다. 마지막 버튼도 scrollIntoView로 완전히 노출 가능해야 한다. header 전체를 잘라서 '해결'하지 않는다.
- <=700에서 `.tool-label`을 시각적으로 숨기고(버튼의 aria-label은 유지), compact ToolbarAction/탭은 최소 40x40이다. 제목은 ellipsis. 편집 중 문서명은 계속 접근성 이름/tooltip으로 확인 가능하다.
- aside의 .tool-row는 기존 wrap을 유지하고 버튼 label이 길면 줄바꿈한다. 폼 입력/select/textarea max-width:100%, min-width:0. fieldset min-inline-size:0. TextStyleControls/색 견본은 패널 안에서 수직/줄바꿈 스크롤로 접근한다.
- footer는 flex-shrink:0, 긴 상태 문구는 한 줄 ellipsis+title 또는 높이 제한 없는 줄바꿈 중 하나로 정하며 여기서는 한 줄 ellipsis+title로 한다. main의 유효 높이가 0이 되지 않아야 한다.
- root의 기존 overflow:hidden만 검사하여 합격시키지 않는다. 내부 header/workspace의 자식 경계와 스크롤 가능성을 직접 검사한다.

### 6.3 Dart 호스트

native build 482~529와 web build 392~432의 AppBar `Text(name)`에 `maxLines:1, overflow:TextOverflow.ellipsis`를 추가한다. 제목을 늘리기 위해 action을 제거하지 않는다. `사본으로 저장`은 원래부터 아이콘이므로 유지한다. 실패 문구/로딩 레이어가 작은 높이에 잘리면 Center 안에 bounded SingleChildScrollView+Padding을 둔다. Webview/HtmlElementView의 타입·등록·URL·크기를 교체하지 않는다. isModal/PopScope/CloseLease/close guard, 저장 세대·revision, postMessage 보안 검사는 그대로다. Flutter Drawer를 iframe 위에 덧대는 방식으로 웹 패널을 구현하지 않는다.

## 7. 시험 명세 — 코더가 작성할 파일과 검사

### 7.1 공통 지원과 위젯 검사 방식

`test/support/responsive_test_support.dart`에 다음을 작성한다.

```dart
typedef ResponsiveCase = ({double width, double scale});
const responsiveCases = <ResponsiveCase>[
  (width:420,scale:1), (width:420,scale:1.5),
  (width:700,scale:1), (width:700,scale:1.5),
  (width:1024,scale:1), (width:1024,scale:1.5),
  (width:1440,scale:1), (width:1440,scale:1.5),
];
Future<void> setResponsiveViewport(WidgetTester tester,
  ResponsiveCase value, {bool displayScale = false});
Future<void> revealToolbarAction(WidgetTester tester,
  Finder toolbar, Finder action);
void expectNoLayoutErrors(WidgetTester tester);
```

setResponsiveViewport는 displayScale=false면 physicalSize=(width,900), DPR=1, MaterialApp.builder의 MediaQuery textScaler를 scale로 덮는다. true면 physicalSize=(width,900), DPR=scale, textScaler=1이다. 둘을 같은 시험에서 혼합하지 않는다. MediaQuery wrapper는 각 시험 pump 함수에서 실제 적용한다. view reset을 addTearDown에 등록한다. 같은 State resize 시험에서는 MaterialApp/home의 Key를 바꾸거나 새 화면을 생성하지 않는다.

revealToolbarAction은 먼저 ensureVisible을 사용하고 불가능할 때 지정 toolbar의 Scrollable에 한정하여 최대 20회 유한 drag한다. `findsOneWidget`만으로 접근 성공 판정하지 않는다. 최종 `hitTestable()` 1개 및 viewport와 버튼 rect의 포함 관계(1px 허용)를 검사한 뒤 tap한다. 수직 detail scroll도 해당 컨트롤러의 scrollable에 한정한다. 모든 조작 뒤 takeException을 비울 때까지 확인하여 RenderFlex/부모 제약 오류를 놓치지 않는다. FlutterError.onError를 삼키거나 overflow 로그를 제외하지 않는다.

API fake는 실제 앱이 쓰는 ApiCall 형식을 따른다. table_units는 기존 `table_units_screen_test.dart` 8~130의 envelope/samplePreview/sampleListData 구조를 새 시험의 작은 fixture로 복사한다(그 파일을 import하여 main/시험을 중복 실행하지 않는다). 가변행 템플릿, 가변열 템플릿, 고정표, 즐겨찾기와 80자 긴 이름을 넣는다. table_sketch는 `table_sketch_api.dart` 계약대로 preview/copy/save/list/load 응답을 제공하고 모든 call을 기록한다. 알 수 없는 요청은 명시적 실패로 처리한다. 무조건 성공을 돌려주는 fake로 기능 접근 검증을 대체하지 않는다.

비동기 loading 상태는 Completer로 제어하고 완료시킨다. spinner가 살아 있는 상태에서 pumpAndSettle하지 않는다. debounce는 600ms pump 한 번 등 지정 시간으로 전진시킨다. showDialog는 tester가 버튼 선택/취소를 하고 끝낸다. 네이티브 파일창/클립보드·한/글은 호출하지 않는다.

### 7.2 editor_responsive_test.dart

- `compact_boundary_is_inclusive_700`: 699/700/701 결과 true/true/false.
- `toolbar_reveals_last_action_with_mouse_and_keyboard`: 30개 도구, 마지막 도구가 drag/Tab으로 hitTestable, callback 1회, 가로 extent>0, overflow 없음.
- `action_keeps_semantics_disabled_and_selected`: compact/wide 두 표현에서 label·selected·disabled 보존, disabled tap이 호출되지 않음. 새 공통 컴포넌트 자체 시험이다.

### 7.3 table_sketch_responsive_test.dart

아래 시험명 뒤에 `_w${width}_s${scale}`를 붙여 필수 8조합 모두 생성한다. displayScale 조합은 `_display` 접미사로 추가한다.

- `sketch_all_toolbar_actions_accessible`: 조직도 예시 적용, 여섯 tool key 선택, 굵기3/종류3 선택, zoom out/in/reset 접근; 캔버스 선 추가→undo→redo→clear(확인 대화상자는 tester가 선택)까지 실제 결과 검사. compact에서는 label Text가 없고 tooltip/Semantics가 있으며 wide에서는 기존 표시가 보인다.
- `sketch_panel_copy_save_load_accessible`: compact 기본 닫힘→토글→copy/save/list/load 접근, wide 패널 및 접기/복원 접근. 이름 입력 후 save payload의 name/sketch를 확인하고 list에서 저장 이름을 선택하여 load payload/캔버스 모델 복원을 확인한다. 각 key는 활성 트리에 하나뿐이다.
- `sketch_resize_preserves_document_and_pending_preview`: 1440→700→420→1024, 텍스트배율 1→1.5; 미리 그린 선·선택 속성·undo/redo·zoom·이름이 보존되고 resize/toggle만으로 저장/복사/불필요 preview가 늘지 않는다. canvas 스크롤 후 위치 보존도 확인한다.

기존 `table_sketch_test.dart` 610~651의 narrow 시험은 처음부터 copy 버튼이 본문에 있다는 기대만 바꾼다. 먼저 `sketchPanelToggle`을 눌러 Drawer를 연 뒤 원래 copy key/overflow 검사를 수행한다. 나머지 기존 420 시험을 삭제하거나 skip 처리하지 않는다.

### 7.4 table_units_responsive_test.dart

- `units_gallery_and_detail_actions_accessible_wW_sS`: 8조합. compact 초기 목록 접힘, 목록 열기→검색·분류 좌우 리본·즐겨찾기·카드 선택→상세 복귀. `btnGenerateThumbnails`, `btnTopCopyTable`, 입력 후 `btnClearCellTexts`, 행열 +/-, fill3종, `btnCopyTable`까지 모두 스크롤 후 hitTestable/tap. API action/payload 및 preview count/count 범위 검사. 고정표에서는 stepper가 없고 복사는 접근 가능해야 한다.
- `units_resize_preserves_selection_cell_edits_and_filters`: 선택/검색/분류/칸 글/행열/fill/오류를 만든 뒤 1440→700→420→1024, 값·payload 보존 및 resize로 list/preview 재호출 없음. wide 분할선 drag 후 작은 폭으로 줄였다 넓힐 때 width 복원; panel 접기와 다시 열기 포함.
- `units_loading_and_long_names_do_not_clip_wW_sS`: 80자 이름·오류·loading→성공, 텍스트 1.5. 검색 caret/카드 즐겨찾기/분류 줄/하단 복사 버튼의 rect 확인, disabled 중 중복 copy 호출 없음.

### 7.5 native/editor host 위젯 시험

`editor_host_responsive_test.dart` 첫 줄 library에 `@TestOn('vm')`를 붙인다. 실제 `DiagramEditorScreen`과 native `FlowEditorScreen` 래퍼를 각각 mount한다. 제품 코드에 시험용 화면/빈 body 플래그를 추가하지 않는다.

무인 WebView mock 지침(조사한 설치 패키지 webview_flutter_windows 1.2.0 기준):

- TestDefaultBinaryMessengerBinding에서 MethodChannel `io.jns.webview.win`의 initialize에 `{'textureId':1}` 응답. per-instance `io.jns.webview.win/1`의 setPopupWindowPolicy/setBackgroundColor/loadUrl/postWebMessage/setSize 등 void 메서드는 null 응답하고 호출을 기록한다. dispose도 기록한다.
- EventChannel `io.jns.webview.win/1/events`의 listen/cancel에 성공 응답을 제공하고 구독 종료를 검사한다. 이벤트를 보낼 때 StandardMethodCodec의 성공 envelope를 사용한다. rootBundle asset-manifest는 저장소의 실제 fixture를 사용한다. 로컬 HttpServer.bind/close는 tester.runAsync 구간에서 완료를 기다리며 네이티브 WebView2 프로세스는 실행하지 않는다. 로컬 서버를 외부 네트워크로 접속하지 않는다.
- 모든 채널 handler는 teardown에서 해제한다. MissingPluginException을 잡아 성공 처리하지 않는다. setUp/tearDown의 실제 오류는 실패다.

시험명:

- `native_diagram_host_fits_and_copy_action_reachable_wW_sS`, `native_flow_host_fits_and_copy_action_reachable_wW_sS`: 실제 화면 초기화 완료→사본 저장 버튼 탭→기존 저장 대화상자에 긴 이름 입력→tester가 확인→postWebMessage에 기존 save payload 확인. 네이티브 호스트 및 래퍼 각각 8조합.
- `native_host_resize_does_not_reinitialize_webview`: 한 mount에서 폭 순환, initialize/loadUrl 1회, postMessage 형식 유지, dispose 1회.

`editor_host_web_responsive_test.dart`는 `@TestOn('browser')`와 `dart:js_interop`/package:web을 쓴다. 실제 `flow_editor_screen_web.dart`를 import한다. 등록된 iframe을 DOM에서 찾아 그 contentWindow를 source로, window.location.origin을 origin으로 하는 ready MessageEvent를 보낸다. foreign source/origin 이벤트로 버튼이 활성화되지 않는지도 검사한다. 이후 실제 버튼→저장 대화상자→save message를 검사한다. iframe src를 외부 URL로 바꾸지 않는다.

- `web_flow_host_fits_and_copy_action_reachable_wW_sS`: 8조합, ready 전 disabled/후 enabled, 타이틀 ellipsis, 버튼과 모달 접근.
- `web_host_resize_keeps_same_iframe`: frame identity/src 고정, resize로 registry 재등록/ready 초기화 없음. 부모 통신 보안 조건 유지.

이 위젯 시험은 host layer 합격만 의미한다. 내부 웹 툴바는 아래 브라우저 시험으로 별도 합격시킨다.

### 7.6 verify_editor_responsive.py — 실제 내장 웹 도구 시험

새 스크립트는 기존 `verify_flow_editor.py`의 Handler/ROOT 및 `browser_qa.launch_browser`를 재사용한다. unittest 기반 `EditorResponsiveBrowserTests(unittest.TestCase)`로 만들고 실행부에서 unittest.main(). 테스트는 setUpClass의 loopback ThreadingHTTPServer/start, tearDownClass의 shutdown/server_close/thread.join을 보장한다. Playwright와 browser/context/page도 finally/cleanup으로 닫는다. JSON 결과는 `C:\HWP_AUTODOCFIT\v1803\reports\P6-artifacts\web-responsive.json`에 쓰고 실패 시 nonzero 종료한다.

`test_toolbar_panel_reachability_matrix`는 diagram/mindmap 각각 필수 8조합과 display 보충 조합을 subTest로 순환한다. iframe 실제 DOM에서 다음을 검사한다.

1. title/header/workspace/footer rect가 viewport 내부(오차1px); main 폭/높이>0; root 및 shell의 scrollWidth/Height가 client보다 커서 잘리지 않음. overflow:hidden 때문에 값만 같아지는 경우를 잡으려고 스크롤 영역 외 자식 rect도 검사한다.
2. nav/mode-tabs는 각 항목을 순서대로 scrollIntoView하고 실제 click/focus 확인. scrollbar/Tab으로 마지막 도구 도달. compact에서 label 시각적 숨김 및 aria-label 존재, 700/701 경계 포함.
3. 새 문서·열기·저장·PNG 요청은 host messages로 횟수와 payload 검사. PNG/그림복사는 실제 로컬 렌더 후 PNG signature/비어 있지 않음을 검사한다. 예시 select는 실제 option 선택으로 request_template 메시지 검사. 외부 프로그램/파일창 대신 host message harness가 요청을 기록·응답한다.
4. compact 초기 패널 hidden→토글→도형 추가/선택→내용·모양·선·글자 서식 접근, 다중 선택 정렬·zOrder·복제·undo/redo까지 적어도 한 번 실행하여 snapshot 변화 확인. mindmap은 가지 선택/하위·형제/순서/부모선/글꼴/도형 controls를 패널 스크롤로 접근하고 실제 snapshot 변화 확인. 선택이 필요한 도구는 먼저 해당 선택 fixture를 만든다. 조건부 도구가 안 보이는 상태를 '접근 가능'으로 세지 않는다.
5. wide panel 접기→펼치기, compact 바깥 클릭/닫기/Escape/focus 복귀; 반복 resize에 ReactFlow DOM과 graph snapshot/선택/undo가 유지. 패널 접기로 dirty 메시지가 늘지 않음.
6. pageerror·console error·외부 요청 없음. 기다림은 wait_for_function/locator 상태와 10초 기본·PNG30초 상한 사용. 사람 입력·고정 장시간 sleep 없음.

`test_resize_preserves_editor_state`는 한 page에서 1440→700→420→1024 및 글자 확대를 적용하고 저장 snapshot을 전후 비교한다. `test_compact_boundary_700_701`은 두 경계에서 label/panel 기본값을 검사한다.

기존 `verify_flow_editor.py` 125~128은 현재 JSX와 다른 옛 탭 목록을 기대한다. tabs 검사만 `get_attribute('aria-label')`(새 탭에 기존 label을 추가)로 바꿔 `['다이어그램','마인드맵','표 템플릿']`을 기대하고, 제거 목록에 `흐름표`,`기본 표`를 추가한다. 그 외 저장·복원·PNG·외부 요청 검사를 약화시키지 않는다. 새 compact CSS로 inner_text가 비는 경우에도 accessible name을 기준으로 판정한다.

## 8. 단계별 구현 순서와 실행 담당자 인계

코더(Gemini/Gemma)는 파일 수정만 수행한다. 아래 1~7은 명령 없이 가능하다. 코더에게 명령 성공/빌드 생성물 제작을 요구하지 않는다.

1. TARGET 파일을 위 범위로 열고 기존 인코딩/CRLF를 보존한다. root HANDOVER/공동작업 문서는 읽되 P6 범위에서 과거 W1~W3 엔진을 다시 수정하지 않는다.
2. 공통 responsive 위젯과 공통 시험 support를 먼저 작성한다. 폭 기준·아이콘 Semantics·스크롤을 한 계약으로 고정한다.
3. 표그림판 레이아웃/패널/속성 칩과 신규 시험 작성. 기존 narrow 시험 1개의 패널 접근 순서를 갱신한다.
4. 표 템플릿 갤러리 Drawer/분할선 폭/툴바/그리드와 신규 시험 작성. 데이터/API 로직을 복사하여 재작성하지 않는다.
5. 웹 main.jsx/style.css와 두 Dart host 제목 표시를 수정한다. 실제 문서 처리/보안/저장 콜백은 보존한다.
6. host 위젯 시험(native+browser), 브라우저 행렬 시험, 기존 웹 탭 기대값 갱신을 작성한다.
7. 변경 파일/미실행 시험/남은 사항을 제출한다. 명령을 못 돌렸으면 반드시 '실행 담당 검증 대기'로 쓰며 PASS로 쓰지 않는다.

다음은 명령 실행 가능한 통합 담당자가 수행할 순서다. 디렉터리 이동 후 각각 실행하며 한 줄에 셸 명령을 연결하지 않는다.

| 위치 | 실행/확인 |
|---|---|
| 저장소 루트 | `powershell -File scripts/build_flow_editor.ps1` — Node>=22.12, npm ci/test/build. 기존 package-lock을 그대로 사용. |
| flutter_ui | `flutter analyze` |
| flutter_ui | `flutter test` — @TestOn에 따라 browser 전용 시험 제외, 기존 전체 포함. |
| flutter_ui | `flutter test --platform chrome test/editor_host_web_responsive_test.dart` — browser 전용 실제 host 시험 별도 실행. |
| 저장소 루트 | `.venv\Scripts\python.exe scripts\verify_editor_responsive.py` |
| 저장소 루트 | `.venv\Scripts\python.exe scripts\verify_flow_editor.py` 및 `scripts\verify_mindmap_editor.py` 각각 실행 |
| 저장소 루트 | `.venv\Scripts\python.exe -m unittest discover -s tests` — 기존 저장소 회귀. 외부 프로그램/COM 경로가 있는 시험은 기존 patch/격리 규칙 확인 후 실행. |
| 저장소 루트 | `git diff --check`, 변경 전후 키/콜백/CRLF 확인, 생성 자산 manifest 참조 파일 존재 확인. |

SDK는 HANDOVER의 `%LOCALAPPDATA%\DocFitTools\flutter`/FLUTTER_SDK를 사용한다. .venv가 이 worktree에 없으면 기존 공용 가상환경의 실제 경로를 기록해서 사용하고 시스템 Python으로 몰래 바꾸지 않는다. Playwright/Chrome/Edge/SDK가 없으면 환경 미충족으로 기록하며 해당 게이트를 PASS 처리하지 않는다. 이 P6 자체는 COM이 필요 없고 원본 문서를 열지 않는다. 전체 회귀 중 실제 COM 경로를 실행해야 하는 경우에만 `C:\HWP_AUTODOCFIT\.com-test.lock`을 획득·반납하고 사용자 원본은 사본으로만 시험한다.

## 9. 반드시 보존할 동작과 완료 기준

보존 계약:

- 모든 기존 Key 문자열, DOM role/aria-label/option value/React key, API action/payload/result 형식. 새 wrapper에 키를 옮길 때 활성 위젯 트리에 한 개만 존재한다.
- 표그림판 그리기·사각형·지우개·정밀 지우개·글·선택/속성·키보드 단축키, 1 drag=1 undo, 좌표·zoom·캔버스 wheel/scroll·debounce·copy/save/load.
- 표 템플릿 자동 첫 선택·필터·즐겨찾기·최근 사용·스냅샷 생성·행열 최소/최대·fill 정책·편집 칸 글·고정표 정책·preview 캐시/오류·copy 비활성/중복 방지·분할선 조작.
- diagram/mindmap generation/revision/dirty, 저장 중 정책, 사본 저장, 폐기 확인, CloseGuards, iframe origin/source 검증, CSP, 로컬 자산/네트워크 제한, PNG 검증, 미지원 모드 비활성. resize/panel 토글은 문서 편집 이벤트가 아니다.
- 편법 return/pass/상수 조건/주석 처리/시험 skip으로 결함을 숨기지 않는다. XML 변경은 없으며 추가하게 되더라도 defusedxml만. 사용자 원본 수정 금지. 기존 CRLF 파일을 LF로 일괄 변환하지 않는다.

완료 체크:

1. 표그림판·표 템플릿·native Diagram·native Flow 래퍼·web Flow host 각각 420/700/1024/1440 × 1.0/1.5 위젯 시험 성공. 창 확대 보충 행렬·699/700/701도 성공.
2. 실제 웹 편집기의 diagram/mindmap 같은 행렬 성공. 모든 툴바/조건부 속성 기능이 scroll 또는 panel toggle 뒤 hitTest/click/키보드로 접근 가능하고 의미 있는 결과가 검증됨.
3. RenderFlex overflow/constraint 오류·브라우저 clipping/pageerror 없음. 700 이하 아이콘+툴팁/접근성 이름, 패널 기본 접힘과 열기/닫기 모두 성공. 그래프/캔버스 작업 영역 유효 크기>0.
4. 연속 resize/패널 접기로 문서·선택·undo/redo·입력·필터·API 상태가 초기화되지 않고 불필요 save/copy/preview가 발생하지 않음.
5. 기존 회귀와 analyze, 웹 빌드, 기존 브라우저 두 gate 성공. 환경 문제/기존 실패가 있으면 정확한 시험명과 로그를 남기고 전체 완료와 구분함.
6. 실행 담당자가 `reports/P6-artifacts/`에 조합별 결과·실행 명령·종료 코드·실패 상세를 보관하고 생성 자산과 소스 일치를 확인. 이번 설계 문서 작성만으로 위 구현 게이트가 통과한 것으로 간주하지 않음.

## 10. 설계 작성 결과

HANDOVER.md 및 공동작업 지시를 읽고 과거 W1~W3 완료/판정 기록은 유지했다. 현 P6 요청은 설계 전용이므로 엔진·Flutter·JS·시험·생성 자산·사용자 문서를 수정하거나 실행하지 않았다. 저장소 조사와 문서 경로/행 번호 검사를 수행했다. 이 설계의 제품 구현·위젯 시험·브라우저 시험·COM 시험은 미실행이다.
