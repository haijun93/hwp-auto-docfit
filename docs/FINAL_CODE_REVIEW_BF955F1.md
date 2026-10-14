# 전체 코드 최종 검토 — bf955f1

검토일: 2026-10-14. 기준 커밋: bf955f1d5a1ebb27d8f439d891ad8519820c03a6.
범위: 전체 저장소 구조·정적 검색·생산 Python 87개 AST/컴파일 및 전체 시험,
엔진/GUI 호환 경계, 문서·표 조판, 저장 서비스, ZIP/XML/fidelity, IPC·브라우저 브리지,
Flutter 편집 상태, Node 배포 및 CI의 주요 경로 수동 검토.
모든 줄과 가능한 입력을 증명한 감사는 아니며 아래 근거 수준을 구분한다.

**결론: 이전 Alpha 10 리뷰 R1~R5 수정은 유지된다. 전체 범위를 확장해 잔여 P1 2건·P2 3건을 확인했다.**
기존 시험 통과와 별개로 원본 보존과 종료 경로의 P1을 우선 수정해야 한다.
이번 검토에서 기능 코드는 변경하지 않았다.

## F1 / P1 — fidelity writer의 고정 임시 이름이 원본 보존을 우회

- 위치: docfit_core/fidelity/package.py:224, 특히 :230.
- 대상 경로와 원본의 resolve 결과만 비교한 뒤 target.name + ".tmp"를 write_bytes로 연다.
  이미 존재하는 임시 파일을 독점 생성하지 않아 심볼릭 링크/하드링크를 따라 기존 파일을 자를 수 있다.
- 실제 재현: source.hwpx 생성 → output.hwpx.tmp를 source.hwpx의 하드링크로 생성 →
  PackageSnapshot.load(source) → write_package(snapshot, {"Preview/PrvText.txt": b"changed"}, output).
  원본 source.hwpx의 바이트가 변경됐다. 대상은 원본과 다른 경로여서 기존 경로 검사를 통과했다.
- 범위: 명령줄 scripts/fidelity.py 및 fidelity 패키지 쓰기 경로다.
  메인 한 번에 적용 파이프라인에서 같은 현상을 재현했다는 뜻은 아니다.
  공격 전제는 출력 폴더에 미리 존재하는 파일 별칭이며 원격 침입을 입증한 것은 아니다.
- 추가 확인: 대상 기존 파일은 temp.replace로 덮어쓴다. copy_exact도 기존 대상 쓰기를 허용한다.
- 수정: 예측할 수 없는 이름을 독점 생성하고 직접 소유한 임시 파일만 사용한다.
  대상 기존 파일·원본 별칭을 거부하고 원자적인 비덮어쓰기 확정 및 오류 시 임시 정리를 적용한다.
  고정 .tmp의 하드링크/심볼릭 링크, 기존 대상 파일, 두 writer 교차 시험에서 원본·기존 파일 해시가 불변이어야 한다.

## F2 / P1 — 앱 창 닫기가 Flutter 편집기의 미저장 상태를 확인하지 않음

- 위치: desktop_web_ui.py:1183, docfit_ui/legacy.py:6858.
- WebView 창의 closing은 request_close로 연결된다.
  종료 확인을 유예하는 조건은 숨김 Tk + gui.running(문서 처리 중)이며,
  흐름도 편집·저장 대기는 이 작업 상태를 켜지 않는다.
  running=False이면 실제 GUI 종료 메서드가 root.destroy를 호출한다.
- Flutter의 dirty/저장 세대 및 PopScope는 편집기 내부에 있고 호스트 종료 경로로 전달되지 않는다.
  경로 뒤로 이동 보호가 OS 창 닫기 보호를 대신하지 않는다.
- 실제 함수 재현: 실제 request_close + 실제 HwpAutoDocFitGUI.종료, 소유 스레드 직접 디스패치와 가짜 루트.
  숨김 백엔드·running=False에서 close_accepted=True, root_destroyed=True,
  프런트엔드 evaluate_js 조회 0건이었다.
  실제 Windows WebView2의 X/Alt+F4는 미실행이며, 미저장 상태를 검사하지 않는 호스트 경로를 확인했다.
- 영향: 미저장 흐름도/tldraw 변경 또는 저장 응답 대기 중 입력은 앱 창 종료 시 보존 보장이 없다.
- 수정: Flutter의 편집기·초안별 dirty/저장 대기 상태를 호스트에 집계한다.
  native closing 콜백은 즉시 거부하고 비동기 저장/폐기/취소 확인을 진행한다.
  저장 완료한 정확한 세대에만 일회성 종료를 허용하며 JS 응답을 closing 콜백에서 동기 대기하지 않는다.
  Windows X/Alt+F4, 저장 중 추가 편집, 저장 실패·브리지 지연을 포함한 종료 회귀 검증이 필요하다.

## F3 / P2 — 표 보호 판별 실패가 보호 해제로 처리됨

- 위치: docfit_engine/page_fit.py:4305, :4324; docfit_engine/pipeline.py:336.
- 스냅샷 저장/읽기 실패는 예외를 삼키고 빈 집합을 반환한다.
  보호 표가 없음과 판별 불가를 구분하지 않는다.
  위치·글 확인이 실패한 표도 보호 목록에서 제외하고 서식을 적용한다고 기록한다.
- 실제 엔진 함수 재현: 스냅샷 포트에서 OSError("snapshot unavailable") 발생 →
  디자인표_영역_목록은 예외 없이 [] 반환 →
  해당 결과를 실행 상태에 반영하면 표셀_자간_제외인가는 False.
  로그는 "서식 표 판별 실패(표 서식을 모든 표에 적용)"였다.
- 영향: 캡션/중첩 표의 정상 판별은 고쳤지만, 판별 오류 때 사용자 디자인을 보호한다는 계약이 깨진다.
- 수정: 조사 결과를 성공/판별 불가로 구분하고 판별 불가 때 문서 작업을 중단하거나 표 작업을 보수적으로 제외한다.
  잘못된 위치를 임의로 보호하기보다 수정 자체를 막는다.
  저장 실패, XML 오류, SetPos 불일치에서 보호 대상에 서식·자간 쓰기가 발생하지 않는 시험을 추가한다.

## F4 / P2 — 여러 편집자의 흐름도 저장에 충돌 감지가 없음

- 위치: docfit_app/diagram_service.py:94, :111; FlowService가 같은 저장 구현을 상속한다.
- 임시 파일을 통한 교체는 원자적이지만 읽은 revision과 저장할 revision을 비교하지 않는다.
  문서별 프로세스 잠금도 없다. UI의 편집 세대는 자기 요청의 ACK만 구분하며 다른 편집자의 저장을 감지하지 못한다.
- 실제 서비스 재현: 같은 설정 폴더를 사용하는 FlowService 두 개.
  둘 다 v1을 읽음 → B가 새 편집 저장 → A가 v1 기반 오래된 초안 저장.
  A 저장은 성공하고 최종 문서는 A 초안으로 바뀌어 B 편집이 사라졌다.
- 범위: 동일 문서를 여러 앱 인스턴스/편집자가 다루는 경우. 단일 편집기 안의 지연 ACK 수정은 유지된다.
- 수정: 문서별 ProcessLock 아래 expected_revision 대조·쓰기·반환 revision 확정을 수행한다.
  Flutter/브리지에도 revision을 전달하고 충돌 시 새 ID로 저장/다시 열기 등을 명시적으로 선택하게 한다.
  두 서비스·프로세스가 교차 저장하는 회귀 시험이 필요하다.

## F5 / P2 — 동시 첫 설치가 다른 호출자에게 반환한 런타임을 삭제

- 위치: docfit_core/kordoc_runtime.py:139.
- 설치 시작 시 destination을 확인하지만 프로세스 간 잠금이 없다.
  두 호출자가 준비를 마치면 뒤 호출자는 먼저 완성된 destination을 rmtree한 뒤 자기 staging으로 교체한다.
- 실제 두 스레드 재현: 양쪽 staging 검증에 barrier →
  A 설치 반환 → B가 destination 삭제 후 교체 직전 일시 정지.
  A가 받은 경로의 node/node.exe가 존재하지 않았다.
  B 교체 후 최종 런타임은 유효했고 양쪽 설치 함수 자체의 예외는 없었다.
- 영향: 먼저 성공을 받은 변환이 실행 파일/JS를 찾지 못할 수 있다.
  Windows의 실행 파일 잠금 때문에 제거가 부분 실패하는 경우는 별도 실측이 필요하다.
- 수정: 설치 루트/버전의 ProcessLock 안에서 이미 설치됐는지 다시 확인한다.
  먼저 설치된 유효 런타임은 재사용하고 활성 디렉터리를 삭제하지 않는다.
  중단된 staging만 정리하며 두 프로세스 첫 실행과 중간 실패를 검사한다.

## 이전 수정과 전체 시험

- 이전 R1~R5의 미리보기 의존성, 병합 칸 너비, 프로필 요소 왕복 값, 캡션 날짜 칸 및 중첩 보호의 정상 경로 시험은 유지된다.
- 생산 Python 87개 AST/compile 및 runpy import_check 통과. 본체 CRLF 3,323줄 유지.
- Python 전체 1,132개: 통과 1,129개, 조건부 제외 3개, 실패/오류 0개.
  실제 Tk/Xvfb를 사용하고 Windows 전용 모듈만 대체했다.
  제외는 선택형 MCP SDK와 실제 Windows PowerShell·절전 API 시험이다.
- dart analyze --fatal-infos 지적 0개. Flutter 전체 49개, 흐름도 모델 6개 통과.
- 현재 빌드된 Flutter 웹/iframe + 실제 Python 저장소의 저장·재열기·삭제·PNG 통과.
  지연 저장 ACK 중 추가 입력 유지 및 뒤로 이동 시 미저장 확인 통과. 두 브라우저 시험의 페이지 오류 0건.
- 소스 --self-test: 패키지/모듈 82개와 실제 부트스트랩 심볼 6개 통과.
  동결 Windows EXE를 실행한 시험은 아니다.
- 추가 재현은 기존 전체 시험에 포함되지 않은 경계 조건이다. 실패하는 시험을 기존 스위트에 추가하지 않고 증거와 재현 순서를 기록했다.

## 보안·배포 검토

- IPC는 loopback 바인딩, token 비교, 메시지/동시 연결 제한을 유지한다.
  브라우저 편집기의 origin/source 확인, JSON 명령 위주의 공개 API 및 개발자 전용 tldraw 조건을 확인했다.
- XML의 defusedxml, ZIP 이름·크기 제한, 사본 작업, 변환 결과 비덮어쓰기 경로가 존재한다.
  원본 보존은 F1의 파일 별칭 사례까지 해결해야 보장을 강화할 수 있다.
- npm audit --package-lock-only --omit=dev: diagram_editor, tldraw_editor, kordoc_pack 모두
  알려진 운영 의존성 취약점 0건. 검사 시점의 registry 결과이며 개발 의존성·Python/Windows 전체 감사는 아니다.
- 빌드 스크립트의 Node 22.23.3 Windows ZIP 기대 SHA-256이 공식 SHASUMS256.txt와 일치함을 확인했다.
  꾸러미 설치 시 해시 자동 검증/신뢰 원천과 manifest 개별 크기 제한은 추가 보강 대상이다.
- 로컬·CI가 공통 PyInstaller spec과 소스/동결 EXE 자가진단 계약을 사용한다.
  GitHub Actions 실행 조회는 접속 오류로 확인하지 못했으며 실제 CI 성공으로 단정하지 않는다.
- github/origin은 같은 GitHub URL이다. 별도 GitLab 백업의 반영을 의미하지 않는다.
- Python requirements.txt는 버전이 고정되지 않았다. Windows에서 검증한 의존성 잠금/해시·SBOM을 두어 재현성을 보강할 필요가 있다.
- 신규 원격 코드 실행을 입증한 결과는 없다. F1은 로컬 파일 보존 문제이며 침투시험·전체 의존성 감사 완료를 의미하지 않는다.
- tldraw 기능 제한은 자산의 배포 제외가 아니다. 기존 사용권·정식 배포 정책 과제는 남아 있다.

## 구조·최적화 판단

- 모듈 분리와 RunContext는 정상 GUI 작업의 옵션·프로필·캐시 상태를 격리한다.
  PipelineCallbacks는 실제 단계의 진입·종료·오류 경로에 연결돼 있으며 과거의 '미연결' 상태와 구분한다.
- 구형 루트 함수의 전역 동기화 어댑터는 호환 목적으로 남아 있다. 엔진 전체가 순수한 명시적 인자 함수로 재작성된 것은 아니다.
- 운영 경로는 Flutter 웹/WebView2 + 숨김 Tk/COM이다. 별도 네이티브 엔진 시제품은 engine_ready=false이며 완전 네이티브 이관 완료로 판단하지 않는다.
- 정상 경로와 오류 경로의 정책을 공유하는 것이 우선이다. 저장은 원자성뿐 아니라 충돌 검사·종료와의 연결이 필요하다.
- 대용량 표·XML 순회, 컨텍스트 초기화, 실제 COM 조판 시간은 Windows 실문서로 측정해야 한다.
  현재 시험만으로 처리 속도·메모리 개선률을 주장하지 않는다.

## 근거 보관과 한계

재현은 임시 폴더와 최소 HWPX/포트 대체 객체만 사용했으며 사용자 원본 문서는 사용하지 않았다.
주요 로그:
- /tmp/docfit-final-review-bf955f1-python.log
- /tmp/docfit-final-review-bf955f1-flutter.log
- /tmp/docfit-final-review-bf955f1-analyze.log
- /tmp/docfit-final-review-storage-repros.log
- /tmp/docfit-final-review-host-guard-repros.log
- /tmp/docfit-final-review-runtime-race.log
- /tmp/docfit-final-review-browser-race.log
- /tmp/docfit-final-review-browser-flow.log

임시 로그의 장기 보존을 전제로 하지 않으며 재현 전제·결과·위치를 본문에 기록했다.
Windows 한/글 COM 조판 결과, 실제 WebView2 X/Alt+F4, 동결 EXE, 실제 폐쇄망 PC의 종단 검증은 남아 있다.
