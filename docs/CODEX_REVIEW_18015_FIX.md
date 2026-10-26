# v1.80.15 버그 수정 수석 검수

- 검수일: 2026-10-26
- 검수자: Codex / 수석 아키텍트·개발자
- 기준: main, HEAD `81b34ef` 위 유지보수 변경
- 판정: **요청된 단계 누락 수정 승인. v1.80.15 릴리스 패키징 진행 승인.** 공개 배포 및 실제 문서 조판 합격 판정은 별도 릴리스 검증 대상이다.

## 코드 검토

1. `docfit_core/stage_selection.py`: all 단계 목록에 `single_cell_spacing` 추가 확인. 표 서식 다음, 내어쓰기 이전 순서를 유지한다. 기본 선택은 켜짐이며 과거 저장 설정에 키가 없어도 기본값이 적용된다.
2. `docfit_engine/pipeline.py`: format 전용 조건을 format/all로 확장한 것이 단계 목록 변경과 일치한다. 표준서식 사용 및 사용자 세부 선택 조건을 유지하며, `stage_enabled`에 모드를 전달한다. 기존 단계 실행 래퍼의 실패·취소 처리도 유지한다.
3. `tests/test_stage_selection.py`: all 목록 포함 검증 확인. 추가로 `tests/test_pipeline_review.py`에서 실제 `_문서_처리_1회`를 Mock으로 실행하여 all/format/spacing × 표준서식 켬·끔 × 단계 선택 켬·끔의 12개 조합을 검증했다. all/format에서 두 조건이 켜진 경우에만 정확히 1회 호출된다.

이 범위에서 차단할 코드 결함은 발견하지 않았다. 기존 format의 개요·한 칸 표 처리 정책을 all에도 적용하는 수정이며 자간 알고리즘 자체의 변경은 없다.

## 검증 결과

```powershell
.\.venv\Scripts\python.exe -m unittest tests/test_stage_selection.py tests/test_stage_timing.py tests/test_hwpx_core.py tests/test_pipeline_review.py
```

- 제출 변경 기준: 52개 PASS, 실패·오류 0 (2.537초).
- 호출 조건 회귀 시험 추가 후: 53개 PASS, 실패·오류 0 (2.993초).
- 전체 unittest discover, EXE 빌드·설치·공개 배포는 이번 검수에서 실행하지 않았다.
- 한/글 COM 시험 및 사용자 원본 수정 없음. 본체 `hwp-auto-docfit.py` 변경 없음.

## 증거의 범위와 후속 릴리스 검증

제공된 분석의 4줄→3줄, 칸 높이 8082→5982 및 +4%/-3% 값은 사용자 제공 증거이며 이번 검수에서 XML·픽셀 비교를 독립 재실행한 결과가 아니다. 코드상 단계 미실행 원인은 확인되지만, 단계를 실행하는 것만으로 사용자 수동 조판과 동일해진다고 보장할 수 없다.

실제 문서 검증에서는 `C:\HWP_AUTODOCFIT\.com-test.lock`을 확보하고 지정 TXT 사본을 all로 실행하여 단계 실행 로그, 개요 상자 줄 수·높이, 본문 보존, 후속 자간 단계 이후 최종 저장 결과를 확인해야 한다. 패키징 승인은 이 실문서 검증이나 최종 공개 배포 승인을 대체하지 않는다.
