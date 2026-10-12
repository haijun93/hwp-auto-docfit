# AI 답변 → HWPX MCP 설계 및 1차 구현

## 목표

Claude 또는 ChatGPT에서 작성·선택한 답변을 MCP 도구에 전달해 사용자가 지정한 문서 서식으로 새 HWPX를 만든다. 원본 문서는 덮어쓰지 않는다. 완성 흐름은 `AI 답변 → 구조화/서식 적용 → HWPX 생성 → (선택) 로컬 한/글 COM 내어쓰기·조판 → 재검사 → 파일 경로와 검수 요약 반환`이다.

## 연결 환경 차이

- Claude Desktop의 로컬 MCP는 Windows PC에서 stdio 서버를 실행할 수 있다. 따라서 로컬 파일 접근과 한/글 COM은 해당 PC에 설치된 서버에 한정한다.
- ChatGPT MCP 연결은 원격 MCP 서버 방식이다. ChatGPT에서 이 Windows 로컬 프로세스를 직접 stdio로 실행할 수 없으므로, ChatGPT까지 지원하려면 인증·접근통제가 있는 보안 터널/조직 승인된 원격 연결을 별도 구축해야 한다. 인터넷에 임의로 포트를 공개하거나 COM 호출 API를 무인 원격 노출하지 않는다. 적용 가능한 ChatGPT 요금제·조직 정책은 실제 연결 단계에서 다시 확인한다.

## 1차 PoC (현재 구현)

- 기본은 비활성화한다. MCP 호스트가 서버를 자동 실행하더라도 도구가 노출되지 않도록 `DOCFIT_MCP_ENABLED=1`을 명시한 경우에만 `python scripts/mcp_server.py`가 stdio 서버로 시작한다.
- 도구 `list_format_presets`: 현재 제공하는 내장 생성 프리셋 목록만 반환.
- 도구 `create_document_from_ai_answer`: Markdown 답변, 내장 프리셋, 출력 파일명을 받아 새 HWPX를 만든다. 입력은 1,000,000자 이하이며 출력 폴더는 기본 `Documents/HwpAutoDocFit/MCP-Output` 또는 `DOCFIT_MCP_OUTPUT_DIR`로 고정한다. 도구 인자로 임의의 입력/출력 경로는 받지 않는다. 동일 파일명 덮어쓰기는 거부한다.
- 생성은 기존 `kordoc_bridge.generate_hwpx`를 사용하며, 결과를 `inspect_hwpx`로 다시 열어 검증한다. 생성 실패/검증 실패면 불완전한 출력물을 지운다. AI 답변 원문은 임시 Markdown 파일로만 전달하고 임시 폴더는 종료 시 삭제한다.
- `mcp` SDK는 데스크톱 앱의 기본 의존성에 넣지 않고 별도 `requirements-mcp.txt`로 격리한다. kordoc/Node는 사전 설치를 요구하며, MCP 실행 중 npx 자동 다운로드를 허용하지 않는다.

## 현재 범위 밖 / 릴리스 후 다음 단계

1. 사용자가 앱에 저장한 사용자 서식 프로필 목록·세부요소를 안전한 데이터 서비스로 추출하고 MCP에서 선택 적용. 현재 도구는 내장 kordoc 프리셋만 제공하며 저장 프로필 적용은 아직 아니다.
2. 한/글 2020 COM 후처리를 독립된 Windows 로컬 작업 프로세스로 구현한다. 한/글 설치/실행 상태, 사용자 승인, 단일 인스턴스 잠금, 취소/시간초과, 저장 후 재열기·검수를 포함한다. 서버가 원격일 경우 COM 도구를 제공하지 않는다.
3. 장시간 작업을 `job_id`/상태/취소 인터페이스로 바꾸고, 중복 요청 키, 격리 임시 디렉터리, 실패 복구와 보존 기간을 추가한다.
4. ChatGPT 사용은 인증 가능한 전용 터널을 통해 제한된 도구만 노출한다. 토큰·세션 비밀을 앱 바이너리에 포함하지 않고, 일반 네트워크 바인딩·익명 쓰기 도구는 금지한다.
5. 실제 Claude Desktop 및 승인된 ChatGPT 연결로 권한 확인, 경로 탈출·프롬프트 인젝션·대용량 입력·악성 HWPX·재전송·COM 충돌을 시험한다. 베타 앱과 동일 입력으로 콘텐츠·서식·오류율 및 성능 비저하를 비교한다.

## 보안 경계

- 현재 MCP는 새 파일 생성만 가능하고 문서 읽기/편집, 임의 경로 열기, 앱 설정 변경, COM 실행 도구는 제공하지 않는다.
- 출력 루트는 고정 설정이며 파일명만 받는다. 답변 본문·자격증명은 로그/도구 결과에 넣지 않는다.
- 생성된 문서는 AI가 만든 비신뢰 입력으로 간주한다. 한/글 COM 실행 전 사용자 확인 단계는 다음 구현에서도 유지한다.
- MCP stdout은 프로토콜 전용이다. 진단 메시지는 stderr로만 쓴다.

## 설치/연결 예시

별도 Python 환경에 `requirements.txt`와 `requirements-mcp.txt`를 설치하고, Node.js 20 이상과 kordoc을 보안 검토 후 사전 설치한다. Claude Desktop에는 `command`로 해당 Python 실행 파일, `args`로 저장소의 `scripts/mcp_server.py`를 지정한다. 개발 중에는 `%APPDATA%/HwpAutoDocFit/MCP-Output` 대신 `DOCFIT_MCP_OUTPUT_DIR`로 시험 폴더를 지정할 수 있다.

ChatGPT는 로컬 stdio 설정만으로 연결되지 않는다. 승인된 원격 MCP 터널을 별도 구성하기 전에는 이 PoC를 Claude Desktop의 로컬 연결에서만 사용한다.
