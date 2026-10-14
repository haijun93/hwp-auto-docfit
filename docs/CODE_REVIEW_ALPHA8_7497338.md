# Alpha 8 — 커밋 포함 전체 구조·주요 경로 코드 리뷰

검토일: 2026-10-14. 기준 커밋: 74973381d4fdd22446c01b5219497b89996f80fd.

범위: fe00c0d·d43dc9b·41e5428·c388516·1bb12b7·7497338 및 연결된 기존 코드.
엔진/호환 바인딩, 상태·설정, ZIP/XML/fidelity·표 복제, 브리지·IPC·MCP·외부 변환,
Flutter 도구·흐름도·저장, 빌드 경로를 정적 검색·주요 경로 수동 검토·재현 시험으로 확인했다.
모든 코드 줄의 정확성이나 취약점 부재를 증명하는 감사는 아니다.

**판정: P1 3건, P2 2건. 배포 전 수정 필요. 이번 리뷰에서 기능 코드는 수정하지 않았다.**

## R1 / P1 — CI EXE의 동적 엔진·UI 모듈 수집 누락

- 위치: .github/workflows/build-windows-exe.yml:47, hwp-auto-docfit.py:314, docfit_engine/runtime.py:45.
- c388516에서 본체는 문자열 모듈명을 import_module로 해석하도록 바뀌었다.
  build.bat은 collect-submodules를 추가했지만 CI는 해당 파일을 호출하지 않고 독립 PyInstaller 명령을 사용한다.
  그 명령에는 engine/ui 수집 옵션이 없다.
- 처음 동적으로 호출하는 docfit_engine.com_driver, 이후 formatter/spacing/page_fit와 docfit_ui.legacy는
  관련 실행 경로에서 정적 import되지 않는다. PyInstaller가 임의의 문자열 모듈명을 추적하지 못하므로
  소스 시험이 통과해도 CI 실행 파일에서 ModuleNotFoundError·시작 실패가 발생할 수 있다.
- 근거 수준: 빌드 명령·import 경로의 소스상 누락 확인. Windows EXE 실행 재현은 미수행.
  GitHub Actions 로그 조회는 HTTP 403으로 확인하지 못해 실제 최근 실행 결과로 단정하지 않는다.
- 조치: 로컬/CI 빌드 명령 단일화, engine/ui/core/app 동일 수집, 동결된 EXE 모듈 로드 smoke test.

## R2 / P1 — 흐름도 저장 중 추가 편집의 미저장 상태 해제

- 위치: flutter_ui/lib/features/flows/flow_editor_screen_web.dart:145,
  flutter_ui/lib/features/diagrams/diagram_editor_screen_native.dart:218.
- snapshot 전송 뒤에도 편집이 가능하다. 추가 편집의 dirty 이벤트 뒤에 이전 저장 응답이 도착하면
  무조건 dirty=false와 mark_saved를 보내 최신 편집까지 저장 완료로 간주한다.
- 실제 Flutter 웹→iframe→Python 저장소 재현: 저장 응답을 2초 지연하고 그 사이 문장을 수정한 뒤 뒤로 이동.
  저장 파일은 '일반 모드 실제 저장', 화면은 '저장 응답 중 추가한 미저장 문장'인데
  closed_without_unsaved_confirmation=true 확인.
- Windows/tldraw 호스트에도 같은 무조건 초기화가 있으나 해당 OS 실행은 미검증.
- 조치: 변경 세대·저장 요청 ID·snapshot 버전으로 ACK를 구분. 이후 편집은 dirty 유지.
  pending 저장/추가 변경이 있으면 닫기 전 최신 내용 저장 또는 명시적 폐기.
- 필수 회귀: 저장→추가 입력/이동→이전 ACK→닫기에서 최신 편집 보존.

## R3 / P1 — 아웃라이너의 오래된 응답이 최신 입력 덮어쓰기

- 위치: flutter_ui/lib/features/tools/document_tools_workspace.dart:174.
- edit는 이전 입력을 전송하고 await한 뒤 input.text에 응답 전체를 대입한다.
  busy 설정과 입력 버전 비교가 없어 대기 중 타이핑·연속 단축키의 결과가 소실될 수 있다.
- 실제 Flutter 위젯 재현: outline.toggle 응답을 Completer로 보류→새 문장 추가→이전 응답 반환.
  최종 입력은 '# [x] 원래 문장'만 남고 '응답 대기 중 추가한 문장'은 소실했다.
- 조치: 작업 직렬화, 요청 시 문서 세대·선택 위치 기록, 오래된 응답 폐기 또는 병합.
- 필수 회귀: 지연 toggle/move/note·연속 작업·타이핑 교차.

## R4 / P2 — 초안 저장 응답이 다른 편집자의 revision 반환

- 위치: docfit_app/document_tools_service.py:50.
- 파일 교체는 ProcessLock 안이지만 응답용 load는 잠금 해제 뒤 수행한다.
  A 저장→B가 새 revision으로 저장→A의 응답용 load 순서에서 A는 B의 text/revision을 받는다.
- Flutter는 saved=자기 snapshot, revision=응답 revision으로 설정하므로 다음 A 저장이 B 편집을
  충돌 없이 덮을 수 있다.
- 제어된 호출 교차 재현: A 최초 저장의 반환 text='B의 동시 편집',
  그 revision으로 A 후속 저장이 성공해 최종 파일이 'A의 후속 편집'으로 바뀌었다.
- 조치: 잠금 안에서 실제 쓴 바이트의 text/hash를 확정해 반환.
  Windows 줄바꿈을 포함해 실제 저장 바이트를 revision 기준으로 사용.
- 필수 회귀: 두 서비스 인스턴스의 저장 완료·응답 교차에서 CAS 보존.

## R5 / P2 — 긴 흐름도 라벨의 PNG 잘림

- 위치: diagram_editor/src/model.js:103 및 :106.
- viewBox는 도형 경계+40px만 계산하지만 라벨은 너비/높이와 무관하게 20문자·22px 간격으로 배치한다.
- 재현: 220×90 도형에 한글 400자. viewBox Y=[-40,130], 텍스트 기준선 Y=[-164,254].
  일부 행은 PNG 밖에 있으며 긴 라벨이 이웃 도형 위로 넘어갈 수도 있다.
- 조치: 화면/출력의 글자 측정·줄바꿈·클리핑을 통일하거나 텍스트 경계를 포함해 크기를 계산.
- 필수 회귀: 긴 한글·명시적 여러 줄·좁은 도형·긴 분기 설명.

## 재검증·근거

- Python 전체 재실행: 1,075개 실행, 1,072개 통과, 조건부 skip 3개, 실패/오류 0개.
- Flutter 전체 재실행: 40개 통과. 일반 편집기 모델 시험 5개 통과.
- core/app/engine/ui/infra 81개 Python 파일 AST/compile, 본체·브리지 py_compile 통과.
- R2 실제 Flutter/브라우저 저장 경쟁, R3 Flutter 지연 응답, R4 제어된 저장 교차, R5 SVG 경계 확인.
  기존 시험 통과는 이 결함들의 부재를 의미하지 않는다.
- 임시 증거: /tmp/docfit-review-flow-save-race.log,
  /tmp/docfit-review-outline-stale.log,
  /tmp/docfit-review-7497338-python.log,
  /tmp/docfit-review-7497338-flutter.log.
  로그의 장기 보존을 전제로 하지 않고 재현 순서·결과를 위에 기록했다.
- 실제 Windows 한/글 COM·WebView2·EXE 실행, 선택형 kordoc 종단 검증과 침투시험은 미수행.

## 보안·구조·최적화

- 인증 IPC, ZIP 크기/비율 제한, defusedxml, 원본 사본 처리, PNG 제한·SVG 이스케이프의 구현과
  기존 시험을 확인했다. 이는 전체 보안의 보증이 아니며 확정한 결함은 배포 경로와 데이터 보존 문제다.
- tldraw 메뉴/API는 개발자 전용이지만 자산은 일반 Flutter 빌드에도 포함된다.
  기능 플래그는 패키지 제외 장치가 아니므로 기존 사용권·배포 정책 과제는 별도 유지한다.
- 모듈 분리는 책임별 소스 위치를 개선했으나 runtime 바인더로 본체 전역을 공유한다.
  PipelineCallbacks는 정의/re-export만 있고 실제 파이프라인 의존성 주입에는 사용되지 않는다.
  독립 엔진·완전한 UI 분리로 판단하지 않는다.
- 다음 개선은 명시적 엔진 컨텍스트/콜백, 공통 빌드 명령, 저장 revision·비동기 계약 공통화,
  지연·동시성·동결 EXE 시험을 우선한다.
- Windows 실문서 처리 시간·시작 시간·메모리 비교 측정이 없어 성능 개선률은 주장하지 않는다.
