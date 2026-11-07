# 업데이트 무결성(S1) — 서명된 latest.json (Ed25519)

## 문제
SHA-256이 exe와 같은 릴리스·저장소에서 오므로, 계정이 탈취되면 exe와 해시가 함께 바뀐다.

## 설계 (1단계, 구현됨 · 기본 꺼짐)
- `latest.json`에 최상위 `signature`(Ed25519 서명 64바이트의 base64)를 둔다.
- 서명 대상 = `signature`를 뺀 JSON을 정규화한 바이트 (`sort_keys`, 구분자 `,` `:`, `ensure_ascii`, UTF-8). 구현: `docfit_core/update_signature.py`.
- 앱에 공개키(`UPDATE_PUBLIC_KEY_B64`, base64 32바이트) 내장. `docfit_app/update_service.py`의 GitLab `latest.json` 경로가 켜져 있으면 서명을 검증한다.
- 실패(서명 없음·변조·다른 키·공개키 미설정) 시 업데이트 거부 + 오류 문구 표시. 기존 동작으로 폴백하지 않는다.
- 검증이 켜져 있으면 서명이 없는 GitHub 릴리스 정보(SHA256SUMS)도 쓰지 않는다(우회 방지).
- 기능 플래그: 환경변수 `DOCFIT_VERIFY_UPDATE_SIGNATURE=1` 또는 `VERIFY_UPDATE_SIGNATURE=True`. 기본 꺼짐.
- exe의 SHA-256은 서명된 latest.json 안에 있으므로 서명이 exe 무결성까지 보증한다.

## 도구 (`scripts/update_signing.py`)
- `python scripts/update_signing.py keygen --key-file <저장소 밖 경로>` → 비밀키 파일(권한 0600) 생성, 공개키 base64 출력.
- `python scripts/update_signing.py sign latest.json [--key-file <경로>]` (또는 환경변수 `DOCFIT_UPDATE_SIGNING_KEY`).
- 저장소 안 경로는 거부한다. 비밀키는 저장소·CI 로그에 두지 않는다.

## 릴리스 절차 초안 (변경안) — **사용자 결정 필요**
1. [사용자 결정 필요] 서명 키 생성 위치·보관 방식(오프라인 PC / 하드웨어 토큰 / CI 비밀 변수)과 백업·교체 정책.
2. [사용자 결정 필요] 공개키 값을 `docfit_core/update_signature.py`의 `UPDATE_PUBLIC_KEY_B64`에 커밋(공개키 교체 = 앱 새 버전 필요).
3. 릴리스 시 `scripts/publish_gitlab_downloads.py`가 `latest.json`을 올리기 직전에 `update_signing.py sign`을 실행하도록 연결 (서명은 CI가 아니라 별도 신뢰 환경에서 하는 것이 탈취 방어에 유리).
4. [사용자 결정 필요] 전환 순서: ①공개키 내장 버전 배포(플래그 꺼짐) → ②대부분 업데이트 후 서명된 latest.json 게시 → ③플래그 기본값 켬. 이전 버전 앱은 서명 필드를 무시하므로 호환된다.
5. [사용자 결정 필요] GitHub 폴백 경로 정책(서명 파일 `latest.json`을 GitHub 릴리스에도 올려 검증하거나, 켠 뒤에는 GitHub 경로 폐지).
6. 키 유출 시 대응(폐기·새 키 앱 배포)과 되돌림(롤백) 방지를 위한 `version` 단조 증가 검사는 2단계 과제.

## 한계 (1단계)
- 롤백/동결 공격(서명된 옛 latest.json 재전송) 방어 없음 → 서명에 만료일 추가 검토.
- 공개키는 앱과 함께 배포되므로 최초 설치본의 신뢰는 별도(코드 서명 인증서 등).
