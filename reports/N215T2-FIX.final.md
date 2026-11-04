# N215T2-FIX 작업 결과

- 브랜치: `feature/n215t`
- 기준 백엔드 계약: `2e290ab` (`content_search`), `44b711d` (관련도 점수와 검색 정렬)

## 변경 사항

- 본문검색을 모든 사용자에게 노출하고 `content_search`를 호출하도록 수정했습니다. 기본 정렬은 `relevance`이며 서버가 정렬한 점수 순서를 유지합니다.
- 기존 위계 기반 검색은 개발자 모드 전용 `연관검색`으로 분리하고 `related_search`를 사용합니다. 위계순·언급 횟수 정렬과 색인 조작 UI도 개발자 모드에서만 보입니다.
- 결과 단일 클릭 미리보기와 더블클릭 문서 열기 동작을 유지하고, 검색/선택 세대가 바뀐 오래된 미리보기 응답을 무시합니다.
- 본문 검색 결과 정렬, 접근성, 개발자 모드 노출을 새 기능 의도에 맞춰 테스트를 갱신했습니다.

## 검증

실행 명령: `flutter test --no-pub test/timemachine_screen_test.dart` (`flutter_ui`)

결과: **37개 테스트 통과** (`All tests passed!`).

`git diff --check`도 통과했습니다. `pub get`은 실행하지 않았습니다.