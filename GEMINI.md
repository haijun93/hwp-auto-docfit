# GEMINI.md (Gemini CLI 등 AI 코딩 에이전트용)

이 저장소에서 작업하기 전에 **`HANDOVER.md`를 먼저 읽으세요.** 개발 환경, 코드 구조, 작업 규칙, 배포 절차, 알려진 함정이 모두 정리되어 있습니다.

꼭 지킬 것:
- Windows + 한/글 2020 COM 환경의 Python(`.venv\Scripts\python.exe`) 앱입니다. 테스트: `python -m unittest discover -s tests`
- 새 기능은 `alpha` 브랜치, 배포는 `main`. 푸시는 `github` 먼저, 그다음 `origin`(GitLab 백업)
- XML 파싱은 `defusedxml`만(GitLab 보안 검사). `hwp-auto-docfit.py`의 CRLF 줄바꿈 보존
- 사용자 문서 원본은 수정하지 말고 사본으로 시험. 커밋·푸시는 사용자가 요청할 때만
- 사용자와는 한국어로 소통
