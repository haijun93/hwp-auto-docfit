# P5 설계서 — 2.0.1 파일변환 전용 화면

작성일: 2026-10-28. 설계 담당: Codex. 이 문서는 구현 지시이며 소스 변경 또는 구현 검수 완료 보고가 아니다.
산출물: C:\HWP_AUTODOCFIT\v1803\reports\P5-design.md
저장소 보관본: C:\HWP_AUTODOCFIT\v1803\fconv\docs\P5-design.md
저장소: C:\HWP_AUTODOCFIT\v1803\fconv, 지정 브랜치 feature/2.0.1-file-conversion.
행 번호 기준: HEAD a04137f(WIP), 1-based, 끝행 포함. main 기준 ea84ccf(v2.0.0). 큰 파일은 아래 TARGET 범위만 충분히 읽고 함수 앵커를 찾아 부분 편집한다.

## 1. 현재 상태와 구현 범위

현재 HEAD에는 이전 설계(0377ab0)에 따른 P5 구현이 WIP로 들어 있다. 따라서 새 화면을 중복 생성하지 말고 기존 FileConversionWorkspace를 완성한다. P5-impl.md의 '구현 완료'는 시험 통과의 근거가 아니다. 루트 P5-design.md의 ea84ccf 기준 행 번호 대신 이 문서의 a04137f 기준 위치를 따른다. O5.md는 지정 경로에 존재하지 않아 검토하지 못했다.

확인한 실행 사슬은 start_job('file_format', params) → DesktopWebBridge._start_legacy → gui.파일포맷_변경_시작(target_format) → conversion_runner.start_conversion_job → run_conversion이다. 새 엔진·CLI·COM worker·변환 subprocess를 만들지 않는다. 현재 번들 kordoc 4.21.30, Pandoc 및 한/글 직접 변환의 기존 경로와 준비 상태 판단을 그대로 사용한다.

화면은 여섯 번째 탭에 FileConversionWorkspace, 텍스트 입력은 문서편집의 '텍스트 입력' → openTools('convert') → DocumentToolsWorkspace로 유지한다. 통합 탭은 이미 연결되어 있다(main.dart:115-163). 재구현하지 않는다.

지원 계약: 입력은 file_conversion.CONVERSION_INPUTS, 출력은 CONVERSION_OUTPUTS(hwpx/pdf/pdfz/pdfm/docx/epub/html/jpg/png/txt/md)다. HWP와 PPTX는 현재 입력이며 출력이 아니다. '상호 변환'을 모든 형식의 전 조합 지원으로 해석하지 않는다. UI 선택지는 _conversion_targets의 enabled/reason을 따른다. HWP/PPTX 출력 추가·번들 교체는 범위 밖이다.

## 2. 편집 TARGET — 파일마다 한 줄

아래는 실제 수정 대상이다. 범위 밖 전체 재작성 금지. 기존 파일은 UTF-8과 CRLF를 유지한다. 특히 24,000자 초과 파일(main.dart, file_conversion_workspace.dart, desktop_web_ui.py)은 지정된 구간과 앵커를 사용한다.

TARGET: flutter_ui/lib/main.dart:115-165,185-230,1850-1875
TARGET: flutter_ui/lib/features/conversion/file_conversion_workspace.dart:1-340,341-600,601-880
TARGET: desktop_web_ui.py:489-499,658-736
TARGET: flutter_ui/test/file_conversion_workspace_test.dart:1-505
TARGET: flutter_ui/test/file_conversion_integration_test.dart:1-197
TARGET: tests/test_p5_file_conversion_bridge.py:1-177
TARGET: tests/test_desktop_file_drop.py:89-146

재사용·보존 확인 위치(수정 대상 아님): main.dart:19-21,71-113,400-424,508-623,1310-1335,2084-2095; workspace_adapters.dart의 FileConversionAdapter/IntegratedWorkspace; tab_navigation_shell.dart:1-87; floating_format_picker.dart:1-409; merge_order_dialog.dart:1-276; document_tools_workspace.dart:1-253; desktop_web_ui.py:501-634,636-656,738-756,937-1031,1685-1697,1786-1848,2018-2036; native_file_dialog_service.py:14-25,72-112,121-151; legacy.py:4285-4315,4600 이후 파일포맷_변경_시작; jobs.py:1-280; conversion_runner.py:1-214; file_conversion.py:295-305; kordoc_bridge.py:29-38. 이미 있는 변환 purpose·파일 등록 옵션·공개 API는 유지하며 새로 또 추가하지 않는다.

## 3. 조사에서 확인한 보완점

1. main.dart:133-140은 API 호출 후 세대 번호를 비교한다. 이미 서버에서 적용된 이전 set_drop_target의 부작용을 되돌리지는 못한다. P5-impl.md에 적힌 '직렬 큐'는 실제 코드에 없다.
2. file_conversion_workspace.dart:117-152에서 raw 오류를 표시해도 호출자가 drainEvents를 계속하며, applySnapshot의 expectedRevision 인자를 내부에서 검사하지 않는다. startConversion의 최신 조회 오류가 이전 snapshot으로 실행을 이어갈 수 있다. remove_file/clear_files/show_result 응답은 get_state여서 mode!=file_format이면 conversion_targets가 빈 배열이다.
3. addFiles:240-294는 탭 비활성화 시 선택 응답을 버린다. 시작/선택/병합 대화상자 전체를 포괄하는 작업 잠금도 없다. pickerOpen은 형식창 종료 직후 풀려 병합창이 열린 동안 재진입할 수 있다.
4. cancelConversion:493-509는 실패 응답을 해석하지 않고 cancelPending을 유지한다. 취소 성공과 실제 worker 종료를 구분해야 한다.
5. build:803-808은 failed 상태도 '변환 완료'로 표시한다. :862는 jobItems 인덱스를 results 인덱스로 간주하여 중간 실패가 있으면 다른 파일 폴더를 열 수 있다.
6. applySnapshot은 jobId가 한번 정해지면 외부에서 새로 시작한 변환 작업을 채택하지 않는다. terminal 상태도 뒤늦은 started 사건으로 running으로 돌아갈 수 있다. gap 복구 시 결과 상세는 snapshot에서 다시 구성하지 않는다.
7. desktop_web_ui.py:678-685의 토큰 등록이 디렉터리를 먼저 거부하므로 :711-713의 '파일을 끌어 놓아 주세요' 안내는 그 경로에 도달하지 않는다.
8. Python P5 시험의 start 위임은 실제와 다른 target/file_order 키워드·반환값을 가정한다. 취소 시험의 manager 대역도 실제 dict 계약과 다르다. show_result 시험은 Windows explorer Popen을 막지 않는다. Flutter stale refresh 시험은 최초 목록 응답도 오기 전에 삭제 버튼을 찾고, 텍스트 입력 시험은 버튼이 없으면 통째로 생략한다. timer만 돌린 시험은 실제 드롭 검증이 아니다.

## 4. 유지할 API와 자료 구조

기존 공개 계약(이름·인자 변경 금지):
- FileConversionWorkspace({Key? key, required ApiCall api, bool isActive = true}).
- get_file_conversion_state() -> dict: files, mode, running, conversion_target, conversion_targets, can_start, job, results, failures. mode를 변경하지 않는다. snapshot의 파일은 문서편집과 공유한다.
- select_files({'request_id': String, 'purpose':'add_conversion_files', 'mode':'open', 'multiple':true}) -> {pending, cancelled, selection_id, ...}; selection_status(requestId)로 완료 확인; add_conversion_files(selectionId)로만 등록한다.
- remove_file(index), clear_files(), show_result(index)의 응답은 일반 snapshot이다. 이후 get_file_conversion_state로 재조회하여 변환 상태를 확정한다.
- start_job('file_format', {'target':String, 'file_order':List<String> 선택}) -> String jobId. file_order는 pdfm만 전달한다. 값 검증은 서버에도 이미 있다.
- cancel_job(jobId) -> job dict; 취소 요청을 수락해도 running일 수 있다. get_events(after_seq,200) -> {events,next_seq,latest_seq,oldest_seq,gap}; 사건은 {seq,job_id,type,data}. seq는 작업별이 아닌 전역 증가 값이다.
- 결과 snapshot 항목은 {name,path,source,pages,...}, 성공 사건은 {source,output}, 실패 사건은 {source,message}. 서로 키가 다르므로 명시적으로 변환한다.

새 Dart 내부 자료 구조(같은 화면 파일에 두고 외부 API를 바꾸지 않음):
- enum _ConversionOperation { idle, selectingFiles, choosingFormat, orderingMerge, starting }.
- class _ConversionResultRow { const _ConversionResultRow({required String source, String? output, String? message, required String state}); final String source; final String? output; final String? message; final String state; }. state는 done/failed, 화면에서 resultIndex를 캐시하지 않는다.
- int revision: 목록/시작 등 변경 시 증가; int jobGeneration: 추적 ID 변경 시 증가; int nextSeq: 전역 사건 커서; Set<int> seenEventSeqs: 현재 추적 작업 중복 사건 방지; bool eventPolling: 사건 조회 단일 실행; _ConversionOperation operation; bool cancelPending.
- Map<String,dynamic>? trackedJob; List<_ConversionResultRow> jobItems; String? terminalMessage. snapshot/job 데이터는 기존 Map 계약을 유지하고 불필요한 모델 계층을 만들지 않는다.
- 파일 목록 비교는 순서 포함 path List로 한다. 결과 경로 비교는 Windows 구분자 정규화와 대소문자 무시를 적용하되 브라우저에 임의 파일 열기 API를 추가하지 않는다.

새/보완할 내부 함수 시그니처:
- bool applySnapshot(Map raw, int expectedRevision): mounted·revision·응답 오류를 모두 검사하고 유효할 때만 적용. 성공 여부 반환.
- bool get isJobRunning: queued/running을 진행 중으로 처리하고 terminal이면 false. snapshot.running은 다른 작업의 전역 잠금으로 별도 사용.
- bool get canMutate: isActive && operation==idle && !running && !isJobRunning && !cancelPending.
- void adoptJob(Map<String,dynamic> job): 새 ID 채택·jobGeneration 증가·상세/중복 집합 초기화. 전역 nextSeq를 0으로 되돌리지 않는다.
- Future<void> refresh(); Future<void> drainEvents(); Future<void> addFiles(); Future<void> removeFile(int index); Future<void> clearFiles(); Future<void> chooseFormat(); Future<void> startConversion(String target,{List<String>? fileOrder}); Future<void> cancelConversion(); Future<void> openResultFolder([String? outputPath]).
- int? resultIndexForOutput(String outputPath): 최신 snapshot.results에서 path가 일치하는 실제 인덱스만 반환.
- void rebuildResultRowsFromSnapshot(): 해당 변환 작업의 성공 results와 실패 failures에서 행 복구. events와 snapshot이 같은 항목을 중복 표시하지 않게 (source,output,state) 기준으로 합친다. source만으로 합치면 여러 출력 구분이 사라지므로 금지.
- main.dart의 Future<void> _routeDropTarget(int index) 유지, Future<void> _dropTargetQueue=Future<void>.value() 추가. API는 큐의 앞 요청이 끝난 뒤 실행한다.
- Python def add_paths(self, paths, *, from_drop=False, file_conversion=False)와 def add_conversion_files(self, selection_id=None) 유지. 신규 공개 Python API는 필요 없다.

## 5. 단계별 구현 순서

### 단계 1 — 탭·드롭 상태 소유권

main.dart:115-165에서 기존 selectedIndex와 주입 구조를 유지한다. _routeDropTarget은 호출 시 최신 세대를 증가시키고 큐에 작업을 연결한다. 큐 작업이 실제 실행되기 직전 mounted와 세대를 검사하고, 유효할 때 set_drop_target을 await한다. 진행 중인 요청이 끝나면 가장 최신 요청이 반드시 뒤에서 적용되어야 한다. 실패는 큐를 끊지 않도록 처리하되 현재 요청 실패를 무조건 성공으로 보이지 않게 후속 전환/재활성화에서 재시도할 수 있게 한다. 큐에 숨은 Workspace의 set_drop_target이 끼어들지 않도록 기존 isActive 가드를 유지한다.

Workspace.reportProfileBounds/didUpdateWidget의 활성 검사와 비활성 시 좌표 무효화 유지. apply의 숨은 탭 팝업 차단 유지. 문서편집 폴링 전체를 중단하지 않는다(전역 종료/백엔드 대화상자 처리 소유권 유지). 탭 순서·IndexedStack key·useIntegratedShell=false의 기본 true 동작은 그대로다.

### 단계 2 — 파일 목록·선택 생명주기

파일 추가는 operation=selectingFiles를 setState로 먼저 반영하고 revision을 증가시킨다. native 선택창 pending은 기존 200ms 조회·120초 제한을 사용한다. 시작 당시 isActive일 때만 선택을 열되, 한번 열린 선택은 탭 전환 뒤 완료되어도 동일 requestId를 추적하고 selection_id를 한번만 소비하여 공유 목록에 등록한다. 숨겨진 탭에서 새 모달이나 변환은 열지 않는다. dispose 뒤 새 API·setState 금지. 오류/취소/타임아웃 모두 finally에서 idle 복원하고 활성 상태 또는 추적 job이 있으면 재조회한다. error 응답을 성공 토큰처럼 다루지 않는다.

removeFile/clearFiles는 canMutate 검사 → operation 잠금에 준하는 busy 잠금 및 revision 증가 → 기존 API await → 오류 검사 → 변환 전용 refresh 순서다. 일반 snapshot 응답을 변환 snapshot 전체로 덮어쓰지 않는다. 오래된 refresh는 expectedRevision 불일치로 버린다. refresh가 이미 진행 중이면 후속 refresh 요청을 pending으로 남겨 변경 이후 반드시 한번 수행한다. operation/busy 중 주기 조회는 덮어쓰기를 미룬다.

desktop_web_ui.py:672-736의 add_paths에서 file_conversion=True이며 선택 검증이 ServiceError로 거부될 때만 디렉터리 여부를 확인하여 Tk를 통해 '파일을 끌어 놓아 주세요'를 알린다. 디렉터리를 목록에 넣거나 검증을 우회하지 않는다. 혼합 드롭(파일+폴더)은 현재 전체 검증 거부 정책을 유지한다. 링크·junction·UNC·ADS·상대 경로/TTL·purpose·일회 소비·1000개 제한은 그대로다. 문서편집의 file_conversion=False 분기와 기본 DOCUMENTS 허용 목록도 변경하지 않는다. add_conversion_files는 add_paths가 반환한 변환 snapshot을 그대로 돌려 불필요한 중복 준비 상태 조회를 줄인다.

### 단계 3 — 형식 선택·병합·시작

chooseFormat 전체를 하나의 operation으로 잠근다. 형식창을 여는 시점에 파일 경로 순서와 revision을 캡처한다. FloatingFormatPicker와 기존 Esc/취소/바깥 클릭 동작을 그대로 사용한다. 선택하지 않고 닫으면 target/files/job 모두 변경하지 않는다.

pdfm이면 2개 이상에서 기존 MergeOrderDialog를 열고 operation=orderingMerge를 유지한다. 정렬 결과가 취소되면 시작하지 않는다. 확인 뒤 최신 변환 snapshot을 받아 캡처 목록과 순서까지 비교한다. 파일 수만 비교하지 않는다. 형식창·병합창이 열린 동안 목록이 바뀌면 '파일 목록이 바뀌었습니다. 다시 선택해 주세요.' 표시 후 종료한다.

시작 직전에도 유효한 최신 조회, 활성 탭, running=false, 대상 enabled=true, 파일 존재를 확인한다. 조회 실패이면 이전 snapshot으로 시작하지 않는다. 형식 선택 연속 클릭·병합창 연속 클릭은 start_job을 중복 호출하지 않게 operation을 starting으로 원자적으로 전이한다. start_job에는 기존 두 인자만 사용하고 반환 String ID를 채택한다. 별도로 set_mode('file_format')를 호출하거나 별도 변환 실행기를 만들지 않는다. 파일 등록/드롭/단순 refresh로 자동 시작하지 않는다. 버튼에는 '형식 선택 후 변환'처럼 선택이 실행으로 이어짐을 알리는 문구를 사용한다.

### 단계 4 — jobs·지연 응답·취소

drainEvents 진입 시 eventPolling을 설정하고 작업 ID·jobGeneration·revision을 캡처한다. 각 await 뒤 dispose/추적 세대 변경을 검사한다. 목록 revision만 바뀌어도 오래된 사건의 화면 적용을 막고 재조회를 예약한다. nextSeq는 모든 작업의 사건에서 서버 next_seq로 전진하되 현재 ID 사건만 화면에 적용한다. 중복 seq는 무시하고 terminal 뒤의 started/progress로 상태를 되돌리지 않는다. 서버 snapshot에서 이미 terminal이면 과거 시작 사건을 재생하지 않는다.

snapshot.job이 file_format이고 추적 ID가 없거나 기존 추적이 terminal이면 새 ID를 채택한다. 다른 종류 job은 trackedJob으로 채택하지 않고 전역 running 잠금/안내만 반영한다. 현재 추적이 running인데 최신 job이 다른 ID라는 이유만으로 취소 대상을 갈아끼우지 않는다. 현재 ID의 terminal 사건을 먼저 처리한 다음 최신 snapshot을 적용한다.

gap이면 최신 get_file_conversion_state를 다시 요청하여 progress/terminal/results/failures를 복구한다. cursor는 응답 latest_seq가 유효한 정수일 때 그 위치로 이동하고 snapshot과 겹친 후속 사건은 중복 방지한다. 복구 조회 실패 시 cursor를 앞당겨 사건을 잃지 말고 오류를 표시한다. 재진입·dispose·다른 작업 사건에도 안전해야 한다.

취소는 진행 중인 현재 ID만 한번 요청한다. 응답 job의 cancel_requested/state를 반영하되 수락을 terminal로 가정하지 않는다. 성공 후에는 해당 ID terminal 또는 snapshot 종료 확인까지 cancelPending과 폴링을 유지한다. 예외·{ok:false}/{error:...} 실패이면 오류를 표시하고 cancelPending=false로 돌려 재시도 가능하게 한다. terminal 수신 시 해제한다. 탭 전환해도 추적 중인 작업은 폴링하며 재실행하지 않는다.

### 단계 5 — 결과·반응형 표시

상태 제목 우선순위: failed='변환 실패', cancelled='변환 취소됨', done+실패항목='변환 완료 (일부 실패 포함)', done+실패없음='변환 완료'. 실패 사건 data.message를 보존한다. 서버가 done으로 끝내면서 개별 실패를 보고하는 기존 계약은 바꾸지 않는다. 같은 형식 건너뜀 메시지도 지우지 않는다.

결과 폴더 버튼은 성공 output 경로를 받아 최신 results.path에서 실제 인덱스를 찾은 경우만 show_result(index)를 호출한다. snapshot이 아직 결과를 모르면 refresh 후 한번 다시 찾고, 없으면 안내한다. 0으로 임의 fallback 금지. 상단 버튼은 최신 성공 결과의 경로를 사용한다. 자동 폴더 열기·open_result/open_results 호출 금지. 이전 문서편집 결과를 변환 완료로 표시하지 않도록 trackedJob.kind와 현재 작업의 결과만 사용한다. 전역 snapshot이 다른 작업으로 바뀌면 보관된 변환 결과는 표시할 수 있으나 현재 results에 없는 항목의 버튼은 비활성화한다.

420px/1280px, 긴 한글 이름·경로·진행 제목·형식 label에서 overflow가 없게 :709-725,753-779,800-818의 Row를 Wrap 또는 Expanded+적절한 줄바꿈으로 바꾼다. 파일명과 경로는 ellipsis/Tooltip, 전체 내용은 스크롤로 접근 가능하게 한다. 기존 위젯 key 유지; 행 열기 key는 렌더링 순서여도 실제 API 인덱스는 path로 찾는다.

## 6. 작성·수정할 무인 시험

시험은 코더가 파일로 작성하고 별도 실행 담당자가 실행한다. 모든 대화상자 입력은 Flutter tester 또는 native dialog 대역으로 완료한다. 실제 한/글·사용자 문서·explorer를 띄우지 않는다. 조건부로 핵심 assertion을 건너뛰거나 구현 함수 전체를 통과 반환으로 바꾸지 않는다.

### flutter_ui/test/file_conversion_workspace_test.dart

기존 FakeApi의 기본 get_events는 빈 사건, 정수 커서다. events 대역에는 seq를 넣는다. 반복 반환하는 이벤트가 있을 때 중복 처리를 확인한다. 각 시험은 pumpWidget(SizedBox)로 dispose, 필요시 bounded pump로 Future 완료를 제어한다.
- 기존 'stale refresh cannot restore removed files': 첫 snapshot을 먼저 완료해 삭제 버튼을 표시한다. 두 번째 refresh만 Completer로 지연 → 삭제 → 옛 응답 완료. 삭제 파일 미복원 및 후속 조회 확인.
- 기존 'file addition and drop refresh never start conversion': timer만 돌리는 방식 교체. 선택 토큰 등록 후 파일 표시, 통합 시험의 실제 드롭 사건 경로와 함께 시작/모달 0회 확인.
- 'selection completes after tab switch': pending 선택 중 isActive=false 전환 후 완료; token 1회 소비, 파일 등록, 모달/시작 0회.
- 'invalid refresh blocks start': 최신 조회 {ok:false,error:...} 또는 throw; 이전 파일 snapshot이 있어도 start_job 0회.
- 'merge flow blocks duplicate start': 병합창 중 추가·비우기·형식 재진입 금지, 확인 1회만 실행, 순서 반전 후 정확한 file_order 확인.
- 'changed files block regular conversion': 일반 형식 선택 중 서버 목록 바뀜; 시작 0회. 기존 merge changed 시험과 별개.
- 'cancel request failure can retry': cancel_job 오류 뒤 버튼 재활성, 같은 ID 재시도, cancel_requested=true 응답만으로 완료되지 않음, terminal 뒤 잠금 해제.
- 'terminal state cannot regress': snapshot done 뒤 늦은 started/progress가 와도 완료 유지. 다른 ID 사건은 진행률·결과·취소에 영향 없음.
- 'adopts next conversion after terminal': 완료 job A 뒤 snapshot job B를 채택하고 B만 취소. 탭 전환/복귀 후 ID 보존.
- 기존 'event gap restores snapshot and partial failures': 여러 페이지 사건 유실(gap=true,latest_seq) 뒤 snapshot만으로 성공/실패 상세·진행률 복구, 중복 없음.
- 'mixed failure reveals matching result': item_failed(A), item_done(B), item_done(C); results=[B,C]. C 버튼은 show_result(1), 존재하지 않는 경로는 호출 0회.
- 'failed job displays failure': failed+message, 결과 0건에서 변환 실패 표시; 변환 완료 없음. done+일부실패/전체건너뜀도 각각 검사.
- 'editor result is not conversion completion': snapshot.job.kind=spacing와 기존 results가 있어도 변환 완료/결과 버튼 없음.
- 기존 취소·비활성·dispose 시험 확대: in-flight refresh/events 후 dispose해도 setState 오류·후속 API 없음.
- 기존 narrow/wide 시험에 긴 label/긴 경로/실패 메시지/결과/진행중을 각각 넣고 tester.takeException()==null 확인.

### flutter_ui/test/file_conversion_integration_test.dart

- 기존 'sixth tab mounts FileConversionWorkspace': NavigationDestination으로 탭을 찾는다. '파일변환' 문자열은 화면 제목과 탐색 탭에 중복될 수 있으므로 findsOneWidget 가정 제거.
- 기존 'text input keeps original entrypoint': if(find...isNotEmpty) 제거. 버튼 존재를 먼저 expect, ensureVisible 후 tap, DocumentToolsWorkspace와 convert 초기 모드 확인, pageBack 후 원 화면 복귀 검증. 실패를 조건문으로 숨기지 않는다.
- 'drop target requests are serialized': 첫 set_drop_target Future를 지연한 상태에서 5→0→5 연속 전환, 서버 적용 순서와 최종 file_conversion 확인. 세대 비교만으로 통과할 수 없는 대역 작성.
- 기존 'hidden editor cannot open picker on conversion update' 유지 및 mode=file_format에서 탭 복귀·드롭 revision 갱신 검증. 단독 Workspace 기존 동작 시험도 유지.
- 'conversion drop refresh never auto starts': Flutter web 시험에서 브라우저 docfit-documents-dropped 사건을 실제 dispatch하고 get_file_conversion_state 재조회/표시만 확인. dart:js_interop/package:web 의존 코드는 별도 web 전용 시험 파일이 필요하면 이 파일을 web 실행 대상으로 제한하는 대신 기존 VM 회귀를 없애지 말고 조건부 import helper를 추가할 것. 새 파일이 필요해지는 경우 먼저 해당 파일의 TARGET와 범위를 설계서에 추가한다. VM 기본 시험에서는 api snapshot의 document_drop_revision 변화와 주기 refresh를 검증하며 실제 DOM 드롭 검증과 구분해 보고한다.

### tests/test_p5_file_conversion_bridge.py

_make_bridge에 gui._job_id=None, 실제 list/dict 상태, 동기 _tk 대역을 사용한다. Mock을 job 객체 대신 내보내며 truthiness에 의존하지 않는다.
- test_file_format_start_delegates_existing_worker: worker side_effect가 gui._job_id='job-1234'를 설정. target=pdf에는 file_order를 전달하지 않고 worker가 positional 'pdf'로 1회 호출됨을 검사한다. start_job은 worker 반환값이 아닌 _job_id를 반환한다. 별도 pdfm 시험에서는 실파일 경로의 역순을 params에 넣고 worker 호출 순간 gui.files가 그 순서이며 호출 뒤 원래 순서 복원됨을 검사. 잘못된 file_order는 worker 0회. 실제 COM/Popen 금지 대역 사용.
- test_job_cancellation_uses_exact_id: gui._job_id='job-target'; manager.cancel 반환 dict를 사용하고 올바른 ID에서만 gui.작업중단 호출. 다른 ID는 중단 호출 0회. 존재하지 않는 ID의 ServiceError는 그대로 전파됨을 확인.
- test_show_result_reveals_folder_without_opening_document: Windows에서는 desktop_web_ui.subprocess.Popen을 patch하여 ['explorer','/select,',정규화경로]를 검사; Windows 외에서는 _경로_열기 호출 검사. os.startfile/open_result/open_results/알림 호출 0회. 실제 프로세스 실행 금지.
- test_conversion_snapshot_keeps_editor_mode_and_uses_targets 확대: selected_mode.set 미호출, 반환 state can_start도 확인. test_conversion_snapshot_does_not_duplicate_ready_probe 유지.
- test_add_conversion_files_reuses_returned_snapshot: 유효 토큰·add_paths 대역으로 반환 snapshot 동일성 및 변환 조회 중복 0회 확인.
- 기존 registration_preserves_source_bytes 유지: TemporaryDirectory 합성 파일만 사용, 등록 전후 hash 동일.

### tests/test_desktop_file_drop.py

기존 test_conversion_drop_precedes_profile_badge, test_existing_drop_targets_keep_routing 유지. test_conversion_drop_rejects_folders_and_missing_native_paths는 get_state/get_file_conversion_state를 모두 dict 대역으로 두어 무관한 GUI snapshot 때문에 실패하지 않게 한다. 폴더·혼합 목록은 등록 0회·안내 문구 확인, 경로 없는 native drop은 이름으로 경로를 추정하지 않음 확인. 모든 native 파일 선택/윈도우는 대역.

기존 tests/test_v2_file_dialog_service.py:108-173과 tests/test_p5_legacy_file_registration.py:1-114는 재작성하지 않고 회귀 실행한다. purpose 단일 소비·TTL·문서편집 입력 불변·변환 HTML/PPTX 등록·목록 UI 갱신이 통과해야 한다.

## 7. 실행 담당자의 검증 및 완료 기준

코더는 명령 실행·빌드·시험·푸시 없이 위 파일 편집과 변경 요약만 남긴다. 실행 담당자는 저장소 규칙에 따라 검증/커밋/푸시한다. 이 설계 작성에서는 소스 시험과 COM 시험을 실행하지 않았다.

1. Python 지정 묶음: .venv\Scripts\python.exe -m unittest tests.test_p5_file_conversion_bridge tests.test_p5_legacy_file_registration tests.test_v2_file_dialog_service tests.test_desktop_file_drop
2. 전체 Python: .venv\Scripts\python.exe -m unittest discover -s tests. 실제 모달·한/글 실행 경로가 남아 있으면 먼저 patch하고 무인 종료시킨다.
3. flutter_ui에서 flutter analyze, flutter test test/file_conversion_workspace_test.dart test/file_conversion_integration_test.dart, 이어 기존 conversion_source_name_test/merge_order_dialog_test/document_tools_workspace_test/workspace_test/workspace_adapters_test 및 전체 flutter test. web 전용 실제 DOM 시험을 작성했다면 flutter test --platform chrome 대상으로 따로 실행하고 VM 시험과 결과를 나눠 기록한다.
4. build_flutter.ps1의 기존 빌드/자산 검사 통과. 생성 desktop_web/flutter 자산은 손으로 수정하거나 Git에 추가하지 않는다. 설계/소스 시험만으로 EXE 검증 완료라고 하지 않는다.
5. 변경 파일 git diff --check, CRLF/단독 LF 확인. hwp-auto-docfit.py 및 변환 엔진 파일은 변경 없어야 한다.
6. 선택적인 Windows+한/글 실기기 검증은 사용자 원본 사본만 사용하며 시작 전에 C:\HWP_AUTODOCFIT\.com-test.lock를 원자적으로 획득하고 소유자/시간/목적을 기록, 종료 후 자기 잠금만 해제한다. 자동 단위 시험은 COM을 patch하므로 잠금 없이 실제 COM을 실행하지 않는다.

완료 기준: 여섯 번째 탭은 파일 목록·형식 선택·진행/취소·실패/성공 상세·명시적 결과 폴더 열기를 제공한다. 텍스트 입력 원래 진입점과 다른 다섯 탭/단독 화면의 동작이 유지된다. PPTX/HTML 등 변환 입력은 전용 purpose로만 확장된다. 추가/드롭은 자동 실행하지 않는다. 탭 전환·선택/병합 취소·취소 요청 실패·늦은 응답·사건 유실·일부 실패·다른 작업 진행에서 잘못된 실행/취소/폴더 열기가 없다. 위 무인 시험과 빌드 검증이 모두 통과하고 실제 실행 여부를 구분해 보고한다. 편법 return/pass/상수 조건/주석 처리로 기존 처리나 시험을 무력화하지 않는다. XML 변경이 필요해져도 파서는 defusedxml만 사용한다. 버전/릴리스 태그/배포는 이 과제에 포함하지 않는다.
