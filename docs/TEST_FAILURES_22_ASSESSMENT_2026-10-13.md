# 실패·오류 22건의 해결 가능성 검토

## 판단

**해결 불가능한 문제가 아니다.** 이전 “기존 기준선과 동일”이라는 표현은 새 실패가 추가되지 않았다는 의미이며, 22건을 해결할 수 없거나 무시해도 된다는 의미가 아니다.

986시험 결과의 7실패·15오류를 traceback, 시험 코드, Linux stub 실행기와 대조했다. 3건은 pywebview 가짜 모듈, 16건은 Tk 가짜 객체, 3건은 운영체제별 경로 의미 차이에서 발생했다. 현재 기록만으로 제품 결함 22개 또는 Windows 정상 동작을 단정할 수 없다.

## 항목별 원인과 해결

| 분류/건수 | 대상 | 확인된 실패 지점 | 해결 방법 |
| --- | --- | --- | --- |
| pywebview 모듈 3오류 | `test_desktop_file_drop`: native_paths_delivered, missing_native_path, non_file_drop | stub가 `webview`를 일반 MagicMock으로 등록하여 `webview.dom` import 실패 | 실제 pywebview/DOMEventHandler를 사용. 이 시험은 가짜 window로 이벤트 계약을 검사하므로 실제 WebView 창은 불필요 |
| Tk 화면 크기 9오류 | example_profile.rename / format_manager.rename_delete / idiom_file_save 2개 / outliner.shortcuts / startup 2개 / writing_aids.windows_open / saved_time.dialog | 화면 너비/좌표가 정수가 아닌 MagicMock이 되어 `max` 비교 실패 | 실제 Tk+디스플레이에서 실행. 화면 없는 Linux에서는 Tk 생성 실패를 명시적으로 skip하고 Windows GUI 검증을 필수로 유지 |
| Tk Treeview 선택 2오류 | format_detail_dialog.cancel / edit_cell_value | Treeview.selection의 결과가 실제 항목 ID가 아닌 MagicMock, 사전 조회 KeyError | 실제 Tk에서 확인/취소/편집 callbacks 실행. 필요한 순수 편집 규칙은 서비스로 추출해 별도 시험 |
| Tk Listbox 선택 1오류 | style_review_dialog.confirm | 가짜 목록 선택값으로 rows 범위를 벗어남 | 실제 Listbox와 예약 callback으로 시험. 실제 GUI에서 재현될 경우 선택값 유효성 검사를 별도 수정 |
| Tk 변수/목록 4실패 | abbreviation_dialog 3개 / korean_proofread_dialog.scan_list | StringVar/BooleanVar/Treeview의 값과 목록이 저장되지 않아 기대값과 다름 | 실제 Tk에서 값·등록·삭제·저장 검증. 고정 반환값으로 시험만 통과시키지 않음 |
| 경로 의미 3실패 | desktop_browser_api.state_lists / format_samples.names / format_samples.dll_path | Linux Path는 `C:\\a\\문서.hwp`의 백슬래시를 구분자로 인식하지 않음; 혼합 구분자 결과와 Windows 문자열 비교 | 범용 시험은 임시 폴더/플랫폼 Path 조합 사용. Windows 경로 규칙은 PureWindowsPath로 별도 계약 검사하거나 Windows 전용 시험으로 실행 |

합계: Tk 12오류+4실패, pywebview 3오류, 경로 3실패 = **15오류+7실패**.

## 시험 실행기 문제

`scripts/linux_stub_test_runner.py`는 Tk와 pywebview가 설치되어 있어도 import 전 `sys.modules`에 MagicMock을 넣는다. GUI 시험은 “Tk를 생성할 수 없으면 skip”하도록 설계되어 있지만, 가짜 `Tk()`는 생성에 성공한 것처럼 보이므로 skip되지 않고 가짜 객체에 실제 GUI 의미를 요구하게 된다.

해결 방향은 Windows COM 모듈만 필요한 범위에서 대체하고 Tk/pywebview는 실제 모듈을 쓰는 것이다. GUI 기능을 수행하지 않는 순수·계약 시험과 실제 GUI 시험을 분리하고, GUI 시험에는 사용 가능한 디스플레이가 필요하다. Linux Xvfb+Tk로 화면 시험을 추가할 수 있지만 Windows 파일 대화상자·WebView2·COM 검증을 대신하지는 못한다.

## 이번 재검사와 제한

제품 코드와 영구 시험 실행기를 수정하지 않고 별도 프로세스에서 실제 `tkinter`, `tkinter.ttk`, 대화상자 모듈, `webview`, `webview.dom`을 먼저 import한 뒤 기존 stub 실행기를 사용했다. 설치된 실제 Tk 9.0과 pywebview DOM 클래스의 import는 성공했다. 이 환경은 `$DISPLAY`가 없어 실제 Tk 창 생성은 TclError로 실패한다.

따라서 화면 시험의 올바른 처리 결과는 **건너뜀**이며, 통과로 계산하지 않는다. pywebview 이벤트 계약 시험은 화면 없이 실행 가능하다. 경로 비교 3건은 같은 Linux 환경에서 남는 것이 예상된다. 재검사 결과는 아래 최종 기록에 적는다.

## 권장 조치와 완료 기준

1. Linux 실행기에서 설치된 Tk/pywebview를 불필요하게 대체하지 않도록 개선한다. 순수·이벤트 계약 시험은 계속 실행하고 GUI 미검증 개수는 별도로 보고한다.
2. 경로 시험 3건의 플랫폼 가정을 수정한다. 실제 Windows 앱 경로를 Linux 시험 통과만을 위해 바꾸지 않는다.
3. Windows GUI CI/개발 PC에서 해당 16개 GUI 시험을 실제 Tk로 실행하고 신규 오류를 추적한다. 실제 창·변수·목록·확인/취소 동작이 통과해야 해결 완료다.
4. 드래그앤드롭 계약 3건 통과와 별개로 실제 WebView2에서 한글/공백/여러 파일 드롭을 확인한다.
5. Windows 전체 시험과 한/글 COM 실문서 시험은 별도 완료 조건으로 둔다. Linux에서 skip 증가만으로 “전체 문제 해결”이라고 보고하지 않는다.

이번 요청은 해결 가능성 검토·보고이므로 시험 기대값을 낮추거나 제품 코드를 수정해 숫자만 없애지 않았다. 원인은 시험 기반에서 정리 가능하지만 실제 Windows 동작의 검증 책임은 남아 있다.

### 최종 재검사 기록

관련 시험 모듈 14개에서 **78시험: 59통과 / 3실패 / 8오류 / 8건너뜀**(52.283초).

- 실제 `webview.dom` 사용으로 드래그앤드롭 import 오류 3건이 없어지고 해당 계약 시험이 통과했다.
- 실제 Tk를 사용하는 화면 시험 8건은 디스플레이 없음으로 정상적으로 skip됐다. 이것은 기능 통과가 아니다.
- GUI 초기화 오류 8건은 `tkinterdnd2`가 여전히 stub이어서 남았다. 해당 시험은 앱의 `TkinterDnD.Tk()`로 root를 생성하므로 tkinter만 실제 모듈로 바꿔서는 충분하지 않다. 실행기에서 tkinterdnd2도 실제 모듈을 쓰고, 이 시험들의 화면 가용성 검사를 보완해야 한다. 실제 디스플레이가 있는 환경에서는 skip 없이 실행해야 한다.
- 경로 가정 실패 3건은 그대로 남았다.

원문 로그: `/tmp/docfit-22-recheck.log`. 이번 재검사는 분류 근거를 강화했으며 22건을 모두 수정 완료한 결과는 아니다.
