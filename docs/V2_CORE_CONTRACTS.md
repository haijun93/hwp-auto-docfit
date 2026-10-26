# 2.0.0 세션 계약과 6탭 통합 경계

## 공통 모델 계약

`docfit_core.session`은 COM·Tk·Flutter에 의존하지 않는다. 문서마다 하나의
`DocumentSession`과 하나의 `CommandBus`를 두고 모든 탭의 편집 어댑터가 공유한다.
선택 영역·확대율·스크롤·진행 중 도형은 각 탭이 소유하며 문서 모델과 구분한다.

- `DocumentSession.open(original, working, state)`는 원본을 읽어 SHA-256을 고정하고
  새 작업 사본을 배타 생성한다. 기존 출력과 원본 경로는 덮어쓰지 않는다.
- `state`는 딕셔너리 기반 순수 값 모델이다. 어댑터는 deepcopy와 값 비교가 가능한
  값만 넣는다. COM 객체·파일 핸들·UI 컨트롤을 넣지 않는다. 읽기는 방어 복사다.
- 명령은 `apply(draft)`만 구현한다. `execute(command, expected_revision=n)` 또는
  `execute_batch(commands, expected_revision=n)`는 사본에서 전체 실행 후 한 번 반영한다.
  예외 시 모델·revision·dirty·이력은 그대로다. 중첩 실행은 거부한다.
- 성공한 실행·Undo·Redo는 revision을 각각 1 증가시킨다. Undo도 revision을 되돌리지
  않는다. 같은 revision의 동시 명령은 하나만 성공하며 나머지는 `RevisionConflict`다.
  충돌한 어댑터는 최신 상태를 다시 읽고 사용자 의도를 재평가한다.
- Undo/Redo는 모델 스냅샷을 복원한다. 새 편집은 Redo를 비운다. 이력은 세션에 종속되고
  다른 CommandBus에서 편집하면 이전 버스는 충돌한다. 이력 용량 제한·영속화는 후속 범위다.
- dirty는 현재 모델과 마지막 저장 모델의 값 비교다. 저장 지점으로 Undo/Redo하면 꺼진다.
  저장 어댑터는 `snapshot()`으로 revision과 state를 함께 확보하고 새 출력에 원자 저장한 뒤
  `mark_saved(expected_revision=n)`을 호출한다. 중간에 편집되면 저장 완료 표시를 거부한다.

이 트랜잭션은 **메모리 모델 경계**다. 명령 내부 파일 쓰기·COM 호출·네트워크 호출은
금지한다. 임의의 외부 부작용을 되돌리는 계약이 아니다. HWPX 직렬화 어댑터는
원본 패키지의 미지원 요소를 보존하고 임시 출력 검증 후 승격해야 한다. COM 큐·직렬화·
프로세스 간 충돌·영속 저장 트랜잭션은 이후 어댑터에서 구현한다.

## 스타일 계약

`StyleResolver.resolve()`의 우선순위는 다음 순서이며 뒤 값이 앞 값을 덮는다.

1. App Defaults
2. Agency Profile
3. Document Theme
4. Parent Style (조상 → 자식)
5. Table Role Conditions (호출자가 전달한 순서)
6. Direct Formatting

속성은 `border.top.color`와 같은 평평한 키 단위로 합친다. 중첩 객체는 하나의 값이다.
누락 키만 상속하고 `None`·`False`·0은 명시적 해제/지정이다. 직접 서식을 지우고 다시
상속하려면 해당 키를 직접 서식 맵에서 제거한다. 반환값의 `properties`와 `sources`에서
최종 값과 출처를 조회한다. 없는 스타일은 KeyError, 부모 순환은 ValueError다.
조건 판정은 호출자가 수행한다. 교대행 → 머리글 → 합계 순으로 조건을 전달하고 직접
서식은 항상 마지막에 둔다. 기존 프로필 변환은 어댑터 책임이며 자동 이관은 아직 없다.

## Flutter 통합 계약과 후속 담당

`TabNavigationShell`은 6개 필수 Widget을 받아 고정 순서로 표시한다:
문서편집 / 표템플릿 / 표그림판 / 다이어그램 / 마인드맵 / 파일변환.
IndexedStack이 모든 자식을 마운트한 채 유지하므로 탭 전환으로 State를 폐기하지 않는다.
비활성 탭의 Flutter ticker는 정지한다. 웹뷰·배경 타이머의 정지는 별도 어댑터 책임이다.
셸의 수명과 각 화면의 타입·키를 안정적으로 유지해야 하며 앱 재시작 복구는 별도다.

이번 산출물은 주입 가능한 루트 셸이다. 기존 main.dart의 운영 경로 교체는 하지 않는다.
기존 문서 도구가 폐기된 상태이므로 가짜 편집 화면을 제품 진입점으로 노출하지 않는다.

- 제미나이 2: main.dart 진입점에 셸을 연결하고 탭 1·2·6 화면 어댑터를 주입한다.
  브리지 요청에는 document_id와 expected_revision을 전달하고 충돌 처리를 연결한다.
- 제미나이 3: 탭 3·4·5 모델 편집을 순수 Command로 감싸고 스타일 조건을 정규화한다.
  캔버스 선택·뷰포트는 화면 상태로 유지한다. 외부 효과는 Command 밖에서 수행한다.
- 제미나이 1: 위 어댑터 통합 뒤 잠금 하에서 사본을 사용해 한/글 저장·재열기·붙여넣기와
  원본 해시·지원 외 요소 보존을 실측하고 결과를 전달한다.
- 코덱스: 어댑터 코드와 실측 실패 로그를 검수하고 재현 시험 및 개선 지시를 정리한다.

순수 계약 시험은 `tests/test_v2_session.py`, 여섯 캔버스의 탭 왕복 상태 보존 시험은
`flutter_ui/test/tab_navigation_shell_test.dart`에 둔다.
