# IPC v1

Named Pipe는 Windows ACL·비동기 클라이언트 및 실기기 검증이 필요한 별도 후보로 남겼다. 시제품은 Dart/Python 표준 라이브러리로 양쪽 실제 프로세스 시험이 가능한 127.0.0.1 임시 포트 TCP를 선택했다. 외부 주소에는 바인딩하지 않는다.

Flutter는 암호학적 난수 32바이트 토큰을 생성해 자식 stdin 초기 JSON으로 전달한다. 토큰을 argv나 로그에 넣지 않는다. 백엔드 stdout 첫 줄은 ready, protocol_version, backend_version, port를 반환한다. 버전 불일치 시 시작을 거절한다.

UTF-8 JSON 한 줄당 최대 1MiB. 요청: protocol_version=1, request_id 문자열(1~128자), token, method, params.args 배열. 응답: protocol_version, request_id, success 및 result 또는 error(code/message/recoverable). 설정 서비스의 result는 기존 API 계약인 ok/data/error 구조를 유지한다.

명령은 ApplicationService allowlist만 허용한다. 동일 연결에서 최근 4096개 request_id 재사용은 거절한다. 이를 영속적인 중복 실행 방지로 간주하지 않는다. 쓰기는 자동 재시도하지 않으며 연결 장애 후 재시작은 명시적으로 요청한다. 연결 최대 8개, 요청 대기 8개, 서버 읽기 제한 30초. 현재 작업 이벤트·job_id·COM 실행·취소 프로토콜은 미구현이다.

shutdown 응답 뒤 서버를 종료한다. 부모 stdin EOF도 종료한다. Flutter는 정상 종료 후 최대 5초 기다리고 필요하면 자식 프로세스를 종료한다. 입력·문서 내용·인증 토큰은 오류 로그로 출력하지 않는다.
