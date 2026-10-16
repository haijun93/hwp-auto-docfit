# tldraw 다이어그램 편집 구조

```text
Flutter Windows Workspace
  └─ 개발자 메뉴 (developer_mode && diagram_editor_enabled)
       └─ DiagramEditorScreen
            ├─ WebView2 (webview_flutter_windows)
            │    └─ tldraw Vite static bundle (offline, local loopback origin)
            ├─ JSON WebMessage bridge (request/response events)
            ├─ file_selector (PNG 저장 대화상자)
            └─ NativeClient → authenticated loopback IPC
                 └─ ApplicationService → DiagramService
                      └─ %APPDATA%/HwpAutoDocFit/diagrams/*.json
```

## 계층의 책임

- `tldraw_editor/`: React 편집기, 기본 도형 편집/실행 취소·다시 실행/선택/줌은 SDK UI를 사용한다. 사용자 템플릿과 편집 명령을 처리하고 `getSnapshot`으로 문서/session을 보낸다. PNG 렌더링은 `Editor.toImage`를 쓴다.
- `flutter_ui/lib/features/diagrams/`: Flutter 라우트, WebView2 생명주기, loopback asset 서버, unsaved-change 경고, PNG 파일 대화상자, Python API 호출을 담당한다. 웹 빌드는 stub 화면을 선택한다.
- `docfit_app/diagram_service.py`: 별도 UI/COM 의존성이 없는 저장소다. 플래그·ID·이름·파일 크기 검증, JSON 파싱, 임시파일+원자 교체, 심볼릭 링크 방지, 목록/열기/삭제를 맡는다.
- `docfit_app/application_service.py`: 네이티브 IPC 허용 명령만 서비스 메서드에 연결한다. 일반 서식 엔진이나 HWP COM에 직접 결합하지 않는다.
- `docfit_core/`: 이번 첫 구현에서 문서 변환 코드는 수정하지 않았다.

## WebView 자산과 메시지

Vite `base: './'` 산출물 전부를 `flutter_ui/assets/diagram_editor/`에 포함한다. Flutter는 Vite manifest의 허용된 파일만 `rootBundle`에서 읽어 loopback HTTP로 전달한다. 요청 경로는 `..`, 역슬래시, NUL을 거절한다. 정적 응답은 MIME·nosniff·CSP 헤더를 적용한다. JS→Dart는 WebView2 `window.chrome.webview.postMessage`를 사용하며, Dart→JS는 `WebviewController.postWebMessage`를 사용한다.

메시지 유형: `ready`, `dirty`, `request_new`, `request_template`, `request_list`, `request_save`, `save_document`, `export_png`, `editor_error`. Dart가 사용자 확인·파일 저장·Python 명령을 수행하고 결과를 `mark_saved`, `load`, `new`, `apply_template`으로 반환한다. 문서 데이터는 WebMessage payload의 IPC 제한(1 MiB)을 넘지 않도록 Python 저장소에서 700 KiB로 제한한다.

## 안전 경계

UI 숨김만으로 보안 경계를 삼지 않는다. Python 저장 명령은 매번 `developer_mode is True`와 `diagram_editor_enabled is True`를 검사한다. ID는 32자리 소문자 hex만 허용하고 filename은 ID로만 만든다. 사용자 이름은 경로에 사용하지 않는다. 데이터는 로컬 AppData에 저장하며 외부 동기화 기능은 없다.

PNG는 현재 사용자가 선택한 경로에 Flutter가 저장한다. 신뢰되지 않은 HWP 삽입 서비스에 자동 전달하지 않는다. 향후 Python 삽입 단계는 sandbox 경로·파일 크기·PNG 시그니처·해시·문서 원본 해시를 다시 검증해야 한다.
