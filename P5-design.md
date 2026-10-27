# P5 설계서 — 2.0.1 파일변환 전용 화면

작성: 2026-10-28 / 설계만 작성, 소스 변경·엔진 실행 없음.
저장소: C:\HWP_AUTODOCFIT\v1803\fconv
기준: feature/2.0.1-file-conversion, HEAD ea84ccfebbe35ead55b24b844cb737e6654a7b22 (사용자가 지정한 main=v2.0.0 기준 작업선).
산출물: C:\HWP_AUTODOCFIT\v1803\reports\P5-design.md. 같은 내용의 저장소 보관본은 docs/P5-design.md.
아래 행 번호는 위 HEAD의 1-based 번호이다. 새 파일은 1행부터 작성한다. 코더는 명령을 실행하지 않고 파일만 편집한다. 검증 명령은 별도 실행 담당자가 수행한다.

## 1. 조사 결론과 범위

1. main.dart:108-118에서 IntegratedWorkspace.fileConversionWidget에 DocumentToolsWorkspace(initial:'convert', isModal:false)를 넣는다. 이것이 현상의 직접 원인이다. workspace_adapters.dart:100-137와 tab_navigation_shell.dart:1-87은 주입된 자식을 그대로 보존하며 6개 탭을 IndexedStack에 올린다.
2. 텍스트 도구의 정상 진입점은 main.dart:1239-1261 부근 addButtons의 ‘텍스트 입력’ → openTools('convert'), main.dart:2013-2024 → DocumentToolsWorkspace이다. 이 경로와 document_tools_workspace.dart의 document_tool 호출은 보존한다.
3. 기존 변환 실행 사슬은 DesktopWebBridge.start_job('file_format', params) → _start_legacy → gui.파일포맷_변경_시작 → conversion_runner.start_conversion_job → run_conversion이다. 새 변환기, CLI, subprocess, COM worker를 만들지 않는다.
4. 화면만 교체하면 PPTX 추가가 실패한다. native_file_dialog_service.py:16-24의 DOCUMENTS/add_files 정책이 PPTX·XLSX·이미지 등을 거부하며 DesktopWebBridge.add_paths도 같은 purpose로 재검증한다. 기존 문서편집 정책을 넓히지 않고 변환 전용 purpose를 추가한다.
5. get_state:480-487은 선택 모드가 file_format일 때만 conversion_targets를 채운다. 탭을 여는 것만으로 문서편집 모드를 변경하지 않도록 변환 전용 읽기 API를 추가한다.
6. 숨긴 Workspace도 Timer와 드롭 감시가 살아 있고 apply:347-352가 포맷 선택창을 연다. IndexedStack의 TickerMode는 Timer를 멈추지 않는다. 활성 탭 정보를 주어 숨은 화면의 자동 팝업·배지 영역 보고를 차단한다.
7. 현재 번들 계약은 kordoc_bridge.py:29-38의 kordoc 4.21.30이다. 이번 작업에서 버전·다운로드·엔진 선택 순서를 변경하지 않는다.

형식 계약: 입력 HWP/HWPX/HML/PDF/XLS/XLSX/DOCX/PPTX/PNG/JPG/JPEG/WebP 및 file_conversion.CONVERSION_INPUTS의 TXT/MD/HTML/HTM·기타 그림. 출력은 현재 CONVERSION_OUTPUTS의 hwpx/pdf/pdfz/pdfm/docx/epub/html/jpg/png/txt/md이다. **HWP·PPTX는 입력 형식이며 현재 출력 형식이 아니다.** ‘상호 변환’이라는 문구로 모든 조합/HWP·PPTX 출력을 약속하지 않는다. 출력 선택은 _conversion_targets의 enabled/reason을 그대로 따른다. 엔진 기능 확장은 P5에 포함하지 않는다. DOC는 기존 문서편집 입력만 유지하며 변환 전용 정책에서는 CONVERSION_INPUTS를 따른다.

## 2. 편집 대상과 정확한 위치

각 TARGET는 코더가 읽고 고칠 범위다. 큰 파일은 해당 범위를 충분히 읽고 앵커를 찾아 부분 편집한다. 구간 밖 전체 재작성 금지. 모든 기존 대상은 현재 CRLF, 단독 LF=0이다.

TARGET: flutter_ui/lib/main.dart:1-35,71-162,278-355,438-551,2013-2024
- 새 화면 import와 통합 호스트 추가, Workspace 활성 여부 입력, 숨은 화면 부작용 제한. 438-551 기존 선택 플로우는 그대로 두고 진입 가드만 보강한다. 2013-2024는 보존 확인 범위.
TARGET: flutter_ui/lib/features/conversion/file_conversion_workspace.dart:1-1 (신규 전체)
- FileConversionWorkspace와 상태·파일 선택·폴링·형식 대화상자·jobs 표시 구현.
TARGET: desktop_web_ui.py:140-155,390-507,624-723,1753-1811,1982-2001
- 변환 전용 snapshot·파일 등록 API, add_paths의 선택적 변환 정책, 드롭 대상 추가, BrowserApi 공개 목록 추가. 기존 작업 실행 900-1029 및 폴더 표시 show_result 1652-1664는 재사용하며 고치지 않는다.
TARGET: docfit_app/native_file_dialog_service.py:14-25,70-77,119-134
- CONVERSION_INPUTS import, add_conversion_files purpose, 복수 선택·등록 허용 목록에 그 purpose만 추가.
TARGET: docfit_ui/legacy.py:4285-4308
- 파일추가에 명시적인 변환 입력 옵션을 추가해 HTML/HTM 등 기존 변환 입력도 실제 등록되게 한다. 기본 지원_확장자는 그대로 둔다.
TARGET: flutter_ui/test/file_conversion_workspace_test.dart:1-1 (신규 전체)
- 새 화면 단독 위젯 시험과 API 대역.
TARGET: flutter_ui/test/file_conversion_integration_test.dart:1-1 (신규 전체)
- 실제 DocFitApp 통합 탭·숨은 화면·텍스트 입력 회귀 시험.
TARGET: tests/test_p5_file_conversion_bridge.py:1-1 (신규 전체)
- snapshot·새 purpose 등록·드롭·기존 실행 위임·원본 보존의 무인 시험.
TARGET: tests/test_v2_file_dialog_service.py:1-109
- FileDialogTests에 변환 purpose 및 기존 정책 불변 시험 추가.
TARGET: tests/test_desktop_file_drop.py:1-88
- FileDropTests에 file_conversion 드롭의 배지 우선순위·기존 분기 보존 시험 추가.
TARGET: tests/test_p5_legacy_file_registration.py:1-1 (신규 전체)
- 실제 파일추가 메서드의 기본/변환 정책과 목록·UI 갱신 시험.

재사용 전용(수정하지 않음): floating_format_picker.dart:1-409, merge_order_dialog.dart:1-276, workspace_adapters.dart:100-137, tab_navigation_shell.dart:1-87, document_tools_workspace.dart:1-253, conversion_runner.py:1-214, jobs.py:1-280, file_conversion.py:1-350, hwp-auto-docfit.py:3103-3104. 기존 workspace_test.dart와 workspace_adapters_test.dart는 수정하지 않고 회귀 실행한다.

## 3. 백엔드의 추가 계약 — 기존 변환 실행 로직은 그대로

### 3.1 파일 선택 서비스

PURPOSES['add_conversion_files'] = ('open', CONVERSION_INPUTS). CONVERSION_INPUTS는 docfit_core.file_conversion에서 가져온 기존 불변 집합을 재사용한다. DOCUMENTS는 수정하지 않는다.
_policy의 multiple 허용 조건은 mode=='open' AND purpose in {'add_files','add_conversion_files'}로 한다. register_selection의 다중 경로 허용 집합 {'add_files','add_format_file'}에 add_conversion_files를 추가한다. 목적 바인딩, 300초 TTL, 단일 소비, 재검증, 경로/파일 ID·ADS·UNC·reparse 거부, 1000개 상한은 전혀 바꾸지 않는다.

### 3.2 DesktopWebBridge 새 공개 메서드

- def get_file_conversion_state(self): -> dict
  state=self.get_state()를 읽고, state['files']의 path를 _conversion_targets(files)에 전달한다. 반환 사본에 conversion_targets와 conversion_target, can_start=self._can_start('file_format',files,state['running'],targets)를 채운다. 기존 mode는 그대로 남긴다. gui.selected_mode.set/set_mode 호출, 파일/설정 변경 금지. 외부 엔진 준비 상태 조회는 기존 get_state처럼 Tk snapshot 밖에서 실행한다. mode가 이미 file_format이면 get_state가 만든 targets를 재사용해 중복 조회하지 않는다.
- def add_conversion_files(self, selection_id): -> dict
  resolve_selection(selection_id,'add_conversion_files')로 일회용 선택을 해석하고 add_paths(paths, file_conversion=True)로 전달한 뒤 get_file_conversion_state()를 반환한다. 파일 선택 취소에는 이 메서드를 호출하지 않는다.
- def add_paths(self, paths, *, from_drop=False, file_conversion=False): -> dict (기존 시그니처 확장)
  file_conversion=False일 때 기존 코드·반환 get_state·기존 gui.파일추가(path) 호출 형태를 유지한다. True일 때만 register/resolve purpose='add_conversion_files', 허용 확장자=CONVERSION_INPUTS, gui.파일추가(path, file_conversion=True)를 사용한다. 기존 from_drop revision, 중복 제거, status/log, hints, 실행 중 등록 금지 유지. 변환 전용 드롭은 파일만 허용하며 폴더는 목록에 넣지 않고 상태 문구로 ‘파일을 끌어 놓아 주세요’를 알린다. 폴더 재귀 추가 기능은 만들지 않는다.
- set_drop_target의 기존 허용 값에 'file_conversion' 추가.
- receive_drop의 첫 분기에 drop_target=='file_conversion'이면 add_paths(paths,from_drop=True,file_conversion=True)로 연결한다. 이 분기는 format/quick_format 및 _profile_drop_bounds 판정보다 앞에 둔다. 기존 네 분기는 그대로 유지한다. _FILE_DROP_SCRIPT 및 _bind_file_drop의 경로 전달·보안 검증은 재사용한다.
- _BrowserApi 공개 목록에 get_file_conversion_state/add_conversion_files 두 이름과 기존 서비스 메서드 select_files/selection_status를 공개 목록에 추가한다. 두 선택 메서드는 브리지에 구현되어 있지만 현재 _BrowserApi에는 빠져 있다. register_selection은 raw 경로를 받으므로 새로 공개하지 않는다.

### 3.3 레거시 파일 등록의 최소 확장

def 파일추가(self, file_path, *, file_conversion=False):
- 기본 False: 기존 지원_확장자 검사 및 모든 부수 동작 보존.
- True: 함수 내부에서 CONVERSION_INPUTS를 import해 그 집합으로만 확장자 검사. 이것은 사용자가 요구한 변환 화면의 명시적 경로 구분이며 전역 기능 플래그/설정 키를 만들지 않는다.
- resolve, isfile, 중복 거부, self.files.append, file_count/file_list, 원본폴더 버튼, 범위·결과 초기화 등 4295-4308의 나머지 동작은 공통으로 그대로 수행한다. 별도 append 우회 경로를 만들지 않는다.
- 폴더추가/파일_드롭/지원_확장자 전역은 변경하지 않는다.

## 4. Flutter 자료 구조와 함수 계약

### 4.1 통합 호스트와 활성 상태

main.dart에서 기존 Stateless DocFitApp의 theme 및 useIntegratedShell=False 경로는 유지한다. home의 integrated 분기만 private StatefulWidget인 _IntegratedAppWorkspace(api:api)로 교체한다.

_IntegratedAppWorkspace({required ApiCall api}); State의 int selectedIndex=0.
그 build는 기존 IntegratedWorkspace를 사용하며 documentEditorWidget=Workspace(api:api,isActive:selectedIndex==0), fileConversionWidget=FileConversionWorkspace(api:api,isActive:selectedIndex==5), onTabChanged는 selectedIndex를 setState로 갱신한다. 기존 adapter/shell/key/탭 순서는 바꾸지 않는다.

Workspace({super.key,required this.api,this.isActive=true}); final bool isActive.
- 별도 화면으로 쓰는 기존 호출은 기본 true라 동작 불변.
- reportProfileBounds: 비활성이면 보고하지 않는다.
- apply의 post-frame 자동 quick_notice/문서 변경에 따른 탭 전환·포맷 창 호출은 widget.isActive인 경우만 수행한다. 상태 적용·진행/완료 기록·기존 pending backend dialog 처리는 유지한다. 숨겨진 탭은 앱 전역 종료/대화상자 처리를 계속 담당할 수 있으므로 polling 전체를 중단하지 않는다.
- openConversionPicker 첫 가드에 !widget.isActive 추가.
- didUpdateWidget에서 true→false일 때 lastProfileBounds=null로 지우고 기존 set_profile_drop_bounds([0,0,0,0]) 호출을 직렬화한다. false→true일 때 다음 프레임 reportProfileBounds로 재보고한다. 타이밍상 비활성화 뒤 도착한 좌표 보고가 남아도 file_conversion 드롭 분기가 좌표보다 우선하므로 잘못된 서식 등록을 막는다.
- 활성화 복귀 시 drop_target을 기존 documents로 돌린다. FileConversionWorkspace 활성화는 file_conversion으로 지정한다. 양쪽 전환 호출은 호스트의 한 async 직렬 큐에서 처리한다: Future<void> _routeDropTarget(int index). 탭 변경마다 세대 번호를 증가시키며 최신 index를 순차 처리한다. index==5→file_conversion, 나머지→documents. 초기 호스트에서 한 번 적용한다. Workspace의 설정/텍스트/서식 모달 내부 drop_target 동작은 그대로 유지한다. 비활성화된 Workspace의 모달 복귀 코드가 드롭 대상을 덮지 않도록 setDropTarget에 !isActive 가드를 추가하되 단독 Workspace 기본 true는 유지한다.

### 4.2 새 화면

class FileConversionWorkspace extends StatefulWidget {
  const FileConversionWorkspace({super.key, required this.api, this.isActive=true});
  final ApiCall api;
  final bool isActive;
}

새 파일은 main.dart를 import하지 않는다. ApiCall, FloatingFormatPicker, MergeOrderDialog, watchDocumentDrops, Material/services/dart:async만 필요한 만큼 import한다. 외부 패키지 추가 없음.

상태 자료:
- Map<String,dynamic> snapshot = {}; 서버 snapshot의 files/results/failures/completion/conversion_targets/job를 읽는다. 변환 목록은 기존 gui.files를 공유하며 탭 전환 시 복사/지우지 않는다. 화면에 ‘문서편집과 파일 목록을 함께 사용합니다’를 짧게 표시한다.
- bool busy=false, polling=false, pickerOpen=false, cancelPending=false; String? error, jobId; int revision=0, nextSeq=0; Timer? pollTimer; void Function()? stopWatchingDrops.
- List<Map<String,dynamic>> jobItems=[]; 각 항목 {source:String, output:String?, message:String?, state:'done'|'failed'}; 이벤트에서 만든 현재 job 결과 캐시. 다른 작업의 결과를 섞지 않는다.
- Map<String,dynamic>? trackedJob; id/kind/state/progress/cancel_requested만 신뢰한다. 서버 progress는 {file:num,total:num,stage:String,percent:num}; percent를 0..100으로 제한해 LinearProgressIndicator에는 /100.
- 선택 요청 식별자는 int 카운터+현재 microseconds를 결합한 화면 인스턴스 고유 문자열. 선택 요청 중 busy=true이고, 재클릭을 막는다.

함수 시그니처:
Future<void> refresh();
Future<void> addFiles();
Future<void> removeFile(int index);
Future<void> clearFiles();
Future<void> chooseFormat();
Future<void> startConversion(String target, {List<String>? fileOrder});
Future<void> cancelConversion();
Future<void> openResultFolder();
Future<void> drainEvents();
void applySnapshot(Map raw, int expectedRevision);

API 호출은 기존 비정형 응답을 존중한다. get_file_conversion_state/remove_file/clear_files는 bare snapshot, select_files/selection_status는 {ok,pending,cancelled,selection_id,error}, start_job은 문자열 job ID, cancel_job은 bare job status, get_events는 bare batch, show_result는 bare snapshot이다. 모든 응답을 {ok,data}로 가정하지 않는다. ok:false 또는 error가 있는 응답·예외는 error에 표시하며 snapshot으로 덮어쓰지 않는다.

## 5. 화면과 동작의 구현 순서

1. 3장의 Python 경계부터 구현한다. 순수 읽기 API와 변환 전용 등록 경로만 추가하며 _start_legacy/conversion_runner/jobs는 수정하지 않는다.
2. 새 화면 build: 상단 ‘파일변환’, 파일 추가/전체 비우기, 스크롤 파일 목록(이름·확장자·전체 경로 툴팁·행 삭제), 선택 결과 형식/선택 버튼, enabled/reason 안내, 진행 막대/처리 파일 수/취소 버튼, 완료·실패/취소 요약, 결과 폴더 열기. 좁은 폭 420에서도 Wrap/Expanded/스크롤로 넘침을 막는다. 뒤로가기 화살표/텍스트 입력 필드/작성 도구 드롭다운은 넣지 않는다.
3. initState: 드롭 감시 등록, 최초 refresh와 1초 주기 폴링. 비활성·자기 변환 job 없음이면 새 화면 폴링을 쉬고, 활성 또는 자기 job 진행 중일 때만 실행한다. didUpdateWidget 활성화 시 refresh한다. 드롭 이벤트는 활성인 경우 refresh만 예약한다. dispose는 Timer/리스너를 해제하고 revision을 증가시킨다.
4. refresh: 중첩 호출을 막고 revision을 캡처, get_file_conversion_state를 await한 뒤 mounted·revision 일치 때만 반영. 명령은 시작 시 revision을 증가시켜 명령 전 조회가 뒤늦게 파일 목록을 되돌리지 못하게 한다. busy 중 조회는 보류하고 finally에 1회 재조회한다. 실패하면 연결 오류와 재시도 버튼, 다음 폴링으로 회복. 오류를 빈 성공 화면으로 처리하지 않는다.
5. addFiles: select_files([{request_id,purpose:'add_conversion_files',mode:'open',multiple:true}]) → pending이면 selection_status([request_id])를 150~250ms 간격으로 확인(동시에 1회) → cancelled이면 등록 호출 없이 종료 → selection_id 확인 → add_conversion_files([selection_id]) → refresh. 상태 확인은 유한 수명(예: 120초)을 두고 기한 후 화면 오류로 종료하며 선택 토큰을 추측하거나 파일 이름으로 경로를 만들지 않는다. 선택 완료가 dispose 뒤면 추가 호출을 하지 않는다. 탭 이탈 뒤 완료는 토큰을 소비하지 않고 등록 취소로 처리한다.
6. 등록·드롭은 파일 목록만 갱신한다. 자동 변환/결과 자동 열기/형식창 자동 표시 없음. canMutate는 !busy && !snapshot.running이며 job cancel 요청 중에도 비활성. start 조건은 여기에 snapshot.can_start와 선택 target.enabled를 함께 적용한다. engine_ready 같은 네이티브 시제품 전용 필드는 새로 요구하지 않는다.
7. chooseFormat: 기존 FloatingFormatPicker를 showGeneralDialog 안에서 그대로 사용한다. 기존 main.dart:443-525의 크기 제한·Esc·중앙/바깥 취소 패턴을 따른다. targets는 서버 목록이며 busy/running이면 모두 비활성. 원본 파일 이름과 개수는 snapshot.files에서 공급한다. 기존 컴포넌트의 ‘포맷을 누르면 바로 변환’ 의미를 유지한다. 사용자가 명시적으로 포맷을 선택하면 startConversion으로 바로 진행한다. Esc/중앙/바깥 취소면 target·작업·목록 불변.
8. pdfm 선택은 snapshot.files 사본을 MergeOrderDialog에 넘긴다. null은 아무 작업도 하지 않는다. 확인 결과는 경로 순서를 그대로 file_order에 전달한다. 다이얼로그를 기다리는 동안 파일 목록/작업 상태가 변했으면 재조회 후 비교하여 ‘파일 목록이 바뀌었습니다. 다시 선택해 주세요’ 표시, 시작하지 않는다. 서버 _start_legacy의 최종 순서 재검증도 유지한다. 원래 gui.files 정렬을 변경하지 않는다.
9. startConversion: 시작 직전에 최신 snapshot을 받아 target.enabled, running, 파일 목록 동일성을 재검사. start_job(['file_format', {'target':target, 필요 시 'file_order':order}])를 단 한 번 호출한다. 범위·stage·문서편집 모드/set_mode는 보내지 않는다. 반환 nonempty 문자열 ID를 jobId로 저장하고 jobItems/nextSeq를 초기화한다. set_conversion_target 별도 호출은 불필요(start_job이 이미 수행). ID 수신 전후 중복 클릭은 busy로 막는다. 기존 Workspace.start/startJob는 변경하지 않는다.
10. jobs: get_events([nextSeq,200])를 순차 소비하고 next_seq를 저장한다. 모든 이벤트의 seq는 전진시키되 job_id==jobId만 표시한다. started/progress/item_done/item_failed/done/failed/cancelled를 반영한다. 200개가 차면 다음 배치를 이어 읽되 UI에 제어를 돌려준다. gap이면 get_file_conversion_state.job로 상태를 재동기화하고 results/failures로 표시를 보완한다. snapshot.job.kind=='file_format'이면 화면 재진입 시 기존 job에 다시 연결할 수 있다. 다른 kind는 ‘다른 문서 작업이 진행 중입니다’로 표시하며 그 job 취소 버튼은 제공하지 않는다.
11. 취소는 cancel_job([jobId]) 1회만 호출한다. 즉시 ‘취소 요청 중’으로 바꾸되 terminal로 꾸미지 않는다. terminal 사건 또는 같은 ID의 terminal snapshot을 받을 때까지 잠근다. 백엔드의 10초 정리·worker 종료·소유 HWP PID 보호를 그대로 사용한다. 실패/부분 성공 수치는 done과 별개로 표시한다(done이라도 item_failed/failures가 있으면 실패 수를 숨기지 않는다). 작업 도중 탭을 옮겨도 jobId/진행 상태는 유지한다.
12. 결과 폴더는 기존 show_result([index])를 사용해 탐색기에서 결과 파일이 든 폴더를 연다. open_results는 실제로 결과 문서를 열고 여러 파일이면 확인 모달도 띄우므로 사용하지 않는다. snapshot/results 또는 현재 jobItems에 성공 결과가 있고 running=false인 경우만 제공한다. 다른 job의 과거 결과를 현재 변환 결과로 보이지 않게 한다. 성공 결과 각 행에 해당 snapshot.results 인덱스의 폴더 열기 버튼을 둔다. 대표 버튼은 첫 성공 결과 인덱스를 사용한다. 경로로 results에서 정확한 인덱스를 매핑하고 결과가 바뀌어 인덱스를 찾을 수 없으면 다시 조회해 안내한다. 여러 폴더/다중 쪽 그림도 기존 show_result의 동작을 따른다. 앱 밖 경로를 Flutter에서 직접 열지 않는다. 클릭에 의해서만 실행한다. show_result의 반환 snapshot은 다시 get_file_conversion_state로 보완한다.
13. 4.1의 호스트 연결 및 숨은 Workspace 가드를 적용한다. 초기 탭 0 유지, 5를 선택했을 때만 새 화면 활성화. 통합 전용 신규 동작은 useIntegratedShell=True 안에 제한한다. ‘텍스트 입력’의 기존 라우트·모달 닫기 가드·입력 보존은 그대로다.

주요 위젯 Key: fileConversionWorkspace, conversionAddFiles, conversionClearFiles, conversionFileList, conversionRemove_<index>, conversionChooseFormat, conversionProgress, conversionCancelJob, conversionOpenResults, conversionError. 기존 picker/merge Key는 원래 것을 사용한다.

## 6. 기존 동작과 금지 사항

- 6개 탭의 이름·순서·stable Key·IndexedStack 수명 보존. 기존 문서편집 단계/옵션/프로필/범위·결과 화면 보존.
- 원본·기존 결과 덮어쓰기 금지, 파일 추가가 자동 실행을 의미하지 않음. 기존 명시적 포맷 선택 즉시 실행 의미는 보존.
- HWP/HWPX→PDF 한/글 내장 경로, PDF→이미지 직접 경로, PDF 합치기/압축, TXT/MD 처리, 같은 형식 입력 제외, 준비 상태 사유 및 엔진 캐시 모두 재사용.
- return/pass/상수 조건/주석 처리로 기존 검증·시험을 회피하지 않는다. 추가 가드는 실제 활성 상태/경합/지원 정책을 검사한다. 전역 DOCUMENTS 확장으로 해결하지 않는다.
- 수정 파일의 UTF-8·CRLF 유지. hwp-auto-docfit.py는 수정하지 않는다. XML 처리를 추가할 필요 없으며 필요해지더라도 defusedxml만 허용.
- 원본 사용 문서는 시험에 쓰지 않는다. TemporaryDirectory의 합성 파일·사본만 사용한다. 자동 시험은 네이티브 선택창·messagebox·한/글·탐색기를 실제 실행하지 않는다.
- 별도 네이티브 Flutter 시제품의 IPC/브리지 기능 확대는 이번 범위 밖이다. 현재 운영 Flutter Web+WebView2+DesktopWebBridge가 수용 대상이며 useIntegratedShell=False도 회귀로 지킨다.

## 7. 작성할 시험 — 파일·시험명·검사 내용

### flutter_ui/test/file_conversion_workspace_test.dart (신규)

공통: ApiCall 대역이 호출 method/args를 기록하고 bare snapshot·문자열 job ID·event batch를 실제 계약대로 반환. pending 요청에는 Completer 사용. Timer 시험은 pump(Duration)로 전진시키며 마지막에 pumpWidget(SizedBox())로 해제. 진행 막대·주기 Timer가 있으므로 무제한 pumpAndSettle 금지.

- file conversion shows files without text tools: 파일명·개수·형식·비활성 reason, 텍스트 입력/개조식 컨트롤 없음.
- adds selected pptx through scoped selection token: pending→완료→add_conversion_files 정확한 ID, start_job 0회.
- cancelled selection leaves file list unchanged: add_conversion_files/start_job 0회.
- file addition and drop refresh never start conversion: 활성 드롭 통지/목록 변경 뒤 picker와 시작 모두 없음.
- format choice starts existing file_format job once: 유효 picker 선택 → start_job kind/target 정확, 더블 클릭에도 1회.
- unavailable target cannot start: enabled=false와 reason 확인, 호출 없음.
- picker cancellation preserves target and files: Esc/중앙/바깥 각각 검사.
- merge confirmation preserves chosen order: 두 파일 순서 변경 뒤 file_order 정확, 서버 목록 원본 순서는 그대로.
- merge cancellation and changed files do not start: 취소 및 pending 중 목록 변경 각각 0회 시작.
- progress and cancellation follow tracked job: 자기 job percent 표시, 다른 ID 이벤트 무시, 취소 1회, terminal 전 재실행 불가.
- event gap restores snapshot and partial failures: gap 재조회, done+실패 1건/성공 1건 동시 표시.
- stale refresh cannot restore removed files: 조회 Completer를 삭제 응답 후 완료해도 파일 재등장 없음.
- opens result folder only on explicit click: 성공 완료만으로 show_result 0회, 클릭 후 올바른 인덱스로 1회, open_results/open_result 0회.
- inactive widget and disposal stop side effects: 비활성의 드롭 반응 없음, dispose 뒤 late 응답·Timer 오류·추가 API 호출 없음.
- layout supports narrow and wide windows: 420x800/1280x900에서 tester.takeException()==null, 파일/결과 스크롤 접근 가능.

### flutter_ui/test/file_conversion_integration_test.dart (신규)

- sixth tab mounts FileConversionWorkspace: DocFitApp 실제 integrated 경로에서 6번째 탭 선택, 새 위젯 표시/DocumentToolsWorkspace 미표시, 탭 이름 순서 고정.
- hidden editor cannot open picker on conversion update: 변환 탭에서 공유 snapshot의 mode=file_format/files/revision 변경을 흘려도 기존 Workspace의 floating picker가 열리지 않음.
- switching tabs preserves conversion job and routes drops: 0→5→0→5, 같은 jobId/취소 상태 보존, drop_target의 최종값 정확, 폴링 응답 순서 역전에도 최신 탭을 따른다.
- text input keeps original entrypoint: 문서편집의 ‘텍스트 입력’으로 DocumentToolsWorkspace 라우트 진입, document_tool('convert'/'add_text') 계약과 뒤로가기 유지.
- standalone Workspace retains existing behavior: useIntegratedShell=False에서 기존 문서편집/포맷 선택 동작 유지.

### tests/test_v2_file_dialog_service.py (기존 FileDialogTests 확장)

- test_conversion_selection_accepts_supported_formats: CONVERSION_INPUTS 각 확장자 합성 파일을 subTest로 생성, 복수 선택 token resolve 성공(PPTX 포함).
- test_conversion_purpose_does_not_expand_document_policy: PPTX가 add_conversion_files에서 성공하고 기존 add_files에서 UNSUPPORTED_FORMAT ServiceError로 거부됨.
- test_conversion_token_is_bound_single_use_and_expires: 다른 purpose 오용·만료·재사용 거부, files 메타데이터에 경로 없음.
- test_conversion_selection_cancel_and_request_dedup: 주입 dialog 대역만 실행, 취소와 동일 request 1회 실행 유지.

### tests/test_p5_file_conversion_bridge.py (신규, unittest.TestCase)

- test_conversion_snapshot_keeps_editor_mode_and_uses_targets: _tk 동기 대역, get_state/_conversion_targets/_can_start 대역으로 mode 불변·대상/실행 가능 값 검증. 추가 시험에서는 기존 test_desktop_browser_api의 Fake GUI 패턴으로 실제 get_state 경유도 확인한다.
- test_conversion_snapshot_does_not_duplicate_ready_probe: mode=file_format 상태에서 _conversion_targets 중복 조회 없음.
- test_selected_pptx_uses_conversion_policy: 실제 선택 서비스+임시 PPTX → 등록 token 소비 → gui.파일추가(path,file_conversion=True) 및 1회 등록.
- test_running_job_rejects_conversion_list_mutation: 등록·삭제·비우기 중 running 보호 검증. 기존 clear_files가 GUI에 위임하므로 GUI 대역도 실제 실행 중 목록 변경 금지 계약을 구현한다.
- test_file_format_start_delegates_existing_worker: start_job/_start_legacy 실제 경유, 가짜 gui.파일포맷_변경_시작이 job ID를 생성, target·file_order 전달/원래 files 복원 및 JOB_RUNNING/지원 불가 거부 확인. subprocess·COM 생성은 호출되면 시험 실패로 patch.
- test_job_cancellation_uses_exact_id: cancel_job이 manager.cancel과 matching gui 작업중단만 호출, 다른 job 취소 오염 없음.
- test_show_result_reveals_folder_without_opening_document: show_result 실제 호출에서 explorer /select 경로 또는 _경로_열기(부모 폴더)를 확인, subprocess.Popen/os.name을 patch하고 문서 열기·모달 호출은 0회.
- test_browser_api_exposes_only_required_conversion_methods: 신규 두 메서드+select_files/selection_status 노출, register_selection·gui/COM 객체 직접 노출 없음.
- test_registration_preserves_source_bytes: 임시 PPTX/MD의 등록 전후 SHA-256 일치(변환 정확도를 뜻하지 않음).

### tests/test_desktop_file_drop.py (기존 FileDropTests 확장)

- test_conversion_drop_precedes_profile_badge: file_conversion+배지 안 좌표에서도 add_paths(...,from_drop=True,file_conversion=True)만 호출, 서식 복제 0회.
- test_existing_drop_targets_keep_routing: documents/manual_documents/format/quick_format 기존 분기·revision 계약 그대로.
- test_conversion_drop_rejects_folders_and_missing_native_paths: 폴더·이름만 있는 drop 거부, 파일 경로 추정 없음.

### tests/test_p5_legacy_file_registration.py (신규)

- test_default_file_registration_keeps_extensions: 기본 등록은 기존 지원_확장자만 허용, HTML은 기존대로 거부.
- test_conversion_file_registration_accepts_html_and_pptx: explicit 옵션에서 두 형식 등록·카운터·리스트·범위/결과 초기화 갱신.
- test_conversion_file_registration_rejects_invalid_and_duplicate: exe/없는 파일/중복 거부, 목록/카운터 불변.

기존 시험 파일의 if __name__ == '__main__' 블록 앞에 메서드를 추가한다.

실제 legacy 파일추가 메서드를 시험한다. 거대한 GUI를 띄우지 않도록 기존 legacy 시험의 클래스 추출/바인딩 패턴을 사용하고, 필요한 경우 def 파일추가 노드만 ast로 추출·compile하여 Path/os/지원_확장자/tk.END를 주입한다. Fake self의 file_count/file_list/원본폴더·범위·결과 함수는 Mock. 원본 함수를 모사한 복제 테스트는 금지한다.

## 8. 실행 담당자 검증과 완료 기준

코더는 위 파일을 편집하고 편집 목록만 제출한다. 아래는 실행 권한이 있는 검수 담당자의 절차이며 코더가 실행해야 완료되는 요구가 아니다.

1. 지정 가상환경을 먼저 확인한다. 이 worktree에는 .venv가 없을 수 있으므로 시스템 Python으로 대체해 통과라고 쓰지 않는다. 저장소 환경 연결 후 루트에서 .\.venv\Scripts\python.exe -m unittest discover -s tests. 집중 시험은 tests/test_p5_file_conversion_bridge.py, test_p5_legacy_file_registration.py, test_v2_file_dialog_service.py, test_desktop_file_drop.py 및 기존 test_desktop_browser_api/test_jobs/test_file_conversion/test_text_conversion_embedded_runtime이다.
2. flutter_ui에서 flutter analyze, flutter test(새 시험+기존 전체). SDK 위치는 flutter_ui/README.md를 따른다. 정적 검사/전체 시험 성공 뒤 운영 Web 자산을 build_flutter.ps1의 기존 절차로 재생성·검증한다. 생성 desktop_web/flutter는 커밋하지 않는다. 이번 설계 작성 시에는 이 검증을 실행하지 않았다.
3. 자동 시험의 네이티브 파일 선택은 NativeFileDialogService에 dialog 대역을 주입한다. 한/글 실행/COM·messagebox·os.startfile/subprocess/탐색기 경로는 patch로 차단한다. 시험은 사람이 누를 창 없이 유한 시간 안에 종료한다.
4. 실제 앱 검수는 합성 MD 및 문서 사본만 사용한다. 파일 추가/PPTX 드롭→목록 유지→형식 선택→진행→취소 또는 완료→결과 폴더 클릭, PDF 2개 합치기 순서, 비활성 사유, 탭 왕복·텍스트 입력을 확인한다. 실제 한/글 COM 변환을 수행할 때만 C:\HWP_AUTODOCFIT\.com-test.lock을 소유자/시각/P5로 원자적 취득하고 finally에서 해제한다. 다른 소유자의 잠금은 지우지 않는다.
5. 완료 판정: 6번째 탭이 FileConversionWorkspace, 정상 텍스트 입력 경로 그대로, PPTX/HWP/HWPX/PDF/DOCX/TXT/MD 추가 가능, 출력은 기존 enabled 목록만, 새 엔진 없음, 원본 불변, jobs 취소의 실제 terminal 대기, 결과 폴더 명시적 열기, 숨은 팝업 없음, 신규·기존 회귀 통과 및 CRLF/차이 검사 완료. 시험 불가 항목은 미검증으로 남기며 합격으로 치환하지 않는다.
6. 배포·버전 변경·main 병합은 이번 요청 범위 밖. 구현 후 허가된 작업 브랜치 feature/2.0.1-file-conversion에 해당 작업만 커밋하고 github→origin 순으로 푸시한다. 설계 산출물도 같은 브랜치의 문서로 보관한다. 다른 작업의 변경은 포함하지 않는다.

## 9. 설계 단계 결과 보고

HANDOVER.md와 공동 조사 문서의 ★ Claude 작업 지시를 확인했다. 이번 최신 직접 지시는 P5 설계 전용이므로 과거 W1~W3 엔진 수정을 재개하지 않았다. 소스·사용자 원본·COM·빌드·시험을 변경/실행하지 않았다. 변경할 지점과 API 계약, 입력 정책 누락, 숨은 탭 경합을 소스 조사로 확인했으며 실제 구현/실행 합격은 후속 검수에 남긴다.
