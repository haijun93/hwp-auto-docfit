# Alpha 8 — 일반 흐름도와 개발자 tldraw 분리

## 사용자 지시와 구현 범위

- 일반 모드: tldraw를 실행하지 않는 업무 흐름도 제공.
- 개발자 모드: 기존 tldraw를 별도 사용 옵션으로 선택. 기존 개발자 전용 API 조건 유지.
- 기존 `tldraw_editor/`와 `diagrams/`를 보존. 일반 편집기 `diagram_editor/`와 `flows/`를 추가. 저장 형식은 `docfit-flow`, version 1이며 두 편집기 데이터를 서로 덮어쓰지 않음.

## 오픈소스 비교·선정

| 후보 | 확인한 라이선스 | 참고·선정 판단 |
|---|---|---|
| draw.io | Apache-2.0 | 도형 팔레트·속성 편집·연결선·정렬 패턴 참고. 이 프로젝트에 소스나 런타임을 복사하지 않음 |
| Excalidraw | MIT | 화이트보드 중심 UX 비교. 이번 일반 업무 흐름도 구현의 의존성으로 채택하지 않음 |
| React Flow / xyflow | MIT | 연결점·노드 이동/크기·선택·확대/축소·미니맵을 제공하는 기반으로 선정, 12.12.0 고정 |

원본 확인: [draw.io](https://github.com/jgraph/drawio/blob/dev/LICENSE),
[Excalidraw](https://github.com/excalidraw/excalidraw/blob/master/LICENSE),
[xyflow](https://github.com/xyflow/xyflow/blob/main/LICENSE).
일반 편집기는 React Flow를 실제 사용하며 애플리케이션의 문서 모델·예시 서식·저장·PNG 렌더러는 별도 구현.
번들에 기여한 패키지의 라이선스 파일을 모아 `THIRD_PARTY_NOTICES.txt`를 빌드 시 생성.
이 결정은 기존 tldraw SDK의 배포 사용권 문제를 해소하거나 승인한 것이 아님.

## 일반 편집기 기능

- 일반 모드에서도 상단 ‘업무 흐름도’ 버튼 제공. 기존 개발자 도구 메뉴의 tldraw 항목은 별도 유지.
- 처리 사각형·판단 마름모·시작/종료 타원·텍스트, 내용/배경 편집, 연결점 기반 화살표·분기 설명 편집.
- 이동·크기 변경·다중 선택·격자 맞춤·왼쪽 정렬·삭제·확대/축소·미니맵·실행 취소/다시 실행.
- 행정·계약·수의계약·예산·보조금·공사·인허가·결재·사고/민원·민원 처리 예시 10종. 민원 서식에 예/아니오 분기와 재검토 연결 포함.
- 새 문서·이름 지정 저장·목록 열기·명시적 삭제·PNG 내보내기. WebView2에서는 브라우저 다운로드 설정에 의존하지 않고 Python 브리지의 저장 대화상자를 사용. 미저장 변경의 폐기 확인.
- Flutter 웹은 동일 출처 iframe + 검증된 postMessage, Windows는 기존 로컬 WebView2 호스트 재사용.
- Python `flow_editor(action,payload)`를 WebView 브리지·네이티브 서비스 양쪽에 연결. ID·크기·심볼릭 링크 등 기존 안전 저장 정책 재사용.
- 기존 tldraw PNG 요청 중계 누락과 저장 문서 열기 시 변경 폐기 확인도 보완.

## 보안·배포

- 런타임 CDN·외부 API·분석 서비스를 사용하지 않음. CSP 외부 연결 차단, 동일 출처/iframe source 검사, SVG 텍스트 이스케이프, 그래프 수·크기와 PNG 크기 제한. PNG 브리지에서 헤더·치수를 확인하고 HWP/HWPX 등 비PNG 경로로의 저장을 거부.
- 일반 편집기 브라우저 시험에서 외부 네트워크 요청 0건 확인. PNG 생성에 사용되는 동일 출처 blob URL은 외부 통신이 아님.
- Node 22.12+ 빌드. `scripts/build_flow_editor.ps1`을 웹/네이티브 빌드에서 호출. 일반 편집기의 JS/CSS/고지를 Flutter 자산에 포함.
- npm production audit: 보고된 취약점 0건(검사 시점 기준). 취약점 부재를 보증하는 침투시험 결과는 아님.

## 검증

- 모델 시험 5개 통과: 10종 서식 왕복, 잘못된 좌표·ID·연결 거부, SVG 이스케이프·이미지 제한, 지원되는 레거시 데이터 변환의 원본 보존, 임의 HTML 필드 제거.
- Python 전체 1,075개 실행: 1,072개 통과, 기존 조건부 skip 3개, 실패·오류 0개. 실제 Tk/Xvfb 및 Windows COM 대역 환경.
- Flutter 전체 40개 통과: 일반 버튼 표시와 개발자 tldraw 메뉴 분리 시험 포함. analyze 문제 없음.
- Chromium iframe 통합 시험 통과: 조건 분기 6노드/6연결, 내용 편집, 저장 데이터 복원, 실행 취소/다시 실행·크기 변경 후 복원, 배경색 저장, PNG 1500×1215 생성, 페이지 오류 0건.
- Flutter 웹 Release 빌드 통과. 로컬 CanvasKit·글꼴·라이선스와 일반 편집기 자산 포함·바이트 일치 검사 통과.
- 최종 Flutter 화면→iframe→실제 Python 저장소 통합 시험 통과: 일반 모드 열기·내용 수정·저장·PNG 저장·다시 열기·확인 후 삭제, tldraw 저장 영역 미생성, 페이지 오류 0건.

## 한계

- 앱에서 제공하던 업무 흐름도 핵심 기능을 일반 편집기에 구현한 것이며 tldraw SDK의 모든 도구와 저장 형식의 완전한 1:1 호환을 뜻하지 않음. 자유 필기·복잡한 그룹·회전 도형·임의 이미지 등은 일반 편집기의 현재 범위에 포함하지 않음.
- 모델에는 일부 단순 tldraw 문서의 변환기가 있으나 사용자 문서의 자동 이관은 수행하지 않음. 복잡하거나 모호한 변환은 거부하며 기존 문서는 개발자 tldraw에서 계속 열 수 있음.
- 한/글 COM 그림 삽입·재편집은 두 편집기 모두 이번 범위에 포함하지 않음. 기존 미구현 과제를 완료했다고 판단하지 않음.
- Windows WebView2 실기기 입력·파일 선택·PNG 저장과 EXE 패키징은 Linux 브라우저 시험과 구분해 추가 검증 필요.

재현: 저장소 Python으로 `scripts/verify_flow_editor.py`와 `scripts/verify_flutter_flow.py` 실행(Playwright·시스템 Chromium 필요). 두 번째 검사는 빌드된 웹 번들과 임시 설정 폴더를 사용하며 실제 사용자 데이터에 접근하지 않음.
