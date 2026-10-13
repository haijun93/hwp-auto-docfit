# Flutter Windows native 기술 검증 현황

2026-10-13, 1.74 Alpha 3. **Windows native 시제품·COM·성능 비교는 미실시**다. 이번 머신은 Linux이며 한/글 2020/WebView2가 없다. Flutter Web의 검사/위젯 테스트/웹 빌드와 Python 순수 서비스 검증만 수행한다. Windows native가 더 빠르거나 메모리를 덜 쓴다는 결론을 내리지 않는다.

선행 조건은 주요 Web UI의 서비스 독립화와 Windows 기능 동등성이다. WebView2와 Tk 비상 복구 경로를 유지한다. native 전환은 별도 Windows 개발 PC에서 아래 순서로 검증한다.

1. Flutter Windows EXE와 Python engine 패키지를 만들고, COM 초기화/해제·단일 worker 소유권을 확인한다.
2. Named Pipe(Windows ACL)와 loopback socket(인증/외부 bind 금지)을 비교한다. 단일 설치 사용자 범위의 접근 제어·명령 validation·요청 취소·종료/재연결 프로토콜을 확정한다. 현재 어느 후보도 채택하지 않았다.
3. 파일/폴더 선택·드롭·설정/프로필/준말·예시 분석·처리/검수 결과 동등성을 사본 문서로 검증한다.
4. 오프라인 자산 로드, update/rollback, 프로세스 종료, 업무용 PC 보안 정책/설치 권한을 검증한다.
5. 같은 PC·문서·설정·교차 반복에서 아래 측정을 수집한다.

| 항목 | Flutter Web | Flutter Windows |
|---|---|---|
| 초기 실행 시간·유휴 메모리·UI 반응성 | 미측정 | 미측정 |
| 문서 처리 시간·결과 품질·원본 SHA-256 | 미측정 | 미측정 |
| EXE 크기·오류/종료 안정성 | 미측정 | 미측정 |
| 배포·업데이트·롤백·오프라인 | 미검증 | 미검증 |

실측 이점과 배포 안정성이 확인된 경우에만 기본 실행 방식 변경을 제안한다. Linux Web 빌드 시간이나 mock 위젯 성능을 Windows 비교값으로 사용하지 않는다.
