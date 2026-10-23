# C21 — formatter 기능별 분할 지도

기준: `3aaa6c3da23c0dfa6b0f27f46e51526f9de527b6` (10,316줄, 358개 함수).
함수 이름·인자·본문 및 그 안의 중첩 함수/주석을 바꾸지 않고 `_install` 분기 단위로 이동했다.
아래 표는 이동 함수 전수 목록이며 기계 판독 원본은 `scripts/formatter_split_manifest.json`이다.

## 전역·호출 그래프와 호환 경계

함수들은 `_install`의 형제 함수 이름과 부트스트랩 상태를 LOAD_GLOBAL/STORE_GLOBAL로 공유한다.
358개 모두 자유 변수(closure)가 없고 기본 인자는 상수/빈 튜플이다. 기능 경계의 호출은 새 모듈끼리
import하지 않고 기존 namespace 이름으로 유지한다. 특히 분석→제목 분류→표, 표준 적용→내어쓰기,
서식통일→글자/문단 적용, 텍스트→제목 표 생성이 서로 연결되므로 각 모듈에 상태를 나누지 않는다.

새 모듈은 원본 함수를 만드는 factory만 소유한다. formatter는 `_plain_bind`로 **원래 formatter 전역**에
raw 함수를 재바인딩한 뒤 재수출한다. `patch('docfit_engine.formatter.X')`는 raw 함수의 의존성 조회에
그대로 적용된다. `__getattr__`는 설치 전 직접 import/patch도 제공한다. `_install`은 기존과 같이 매번 새
정의를 만들고 `runtime.bind_function`에 넘긴다. 세션 template도 formatter 전역을 갖고, 실행 때는 기존
`RunContext.function`이 별도 state에 다시 바인딩한다. runtime/bootstrap의 resolve 경로는 바꾸지 않았다.
새 모듈을 그냥 재수출하면 patch가 무효화되므로 위 단계가 필요하다. 새 모듈 간 순환 import는 없다.

## 모듈별 지도

| 새 모듈 | 함수 수 | 줄 수 | 분할 이유 |
|---|---:|---:|---|
| `formatter_utils.py` | 60 | 863 | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `formatter_analysis.py` | 15 | 683 | 서식 프로필·예시 분석과 내보내기 |
| `formatter_titles.py` | 74 | 1850 | 제목·개요·중제목·붙임의 공통 구조 및 적용 |

| 함수 | 새 모듈 | 이유 |
|---|---|---|
| `_hwp_설치폴더_후보_레지스트리` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `_hwp_설치폴더_후보_공통경로` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `한글_폰트_폴더_자동감지` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `_ttf_패밀리이름` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `한글_폰트_목록` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `한컴_번들_폰트_폴더_목록` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `한글_폰트_목록_전체` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `서식_기본값_전역_복원` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `프로그램_폴더` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `번들_리소스_폴더` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `기본_서식프로파일` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `서식프로파일_목록` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `_제목뒤간격_다시재기` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `hwpx_서식_분석` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `보고서머리_프로필_반영` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `보고서머리_hwpx_처리` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `예시문서_기본이름` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `_분석본_보관` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `한글파일_서식_분석` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `교정용_hwpx_준비` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `분석용_hwpx_준비` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `스타일분석_파일생성` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `스타일분석_요약` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `서식프로파일_표시이름` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `문서_markdown_내보내기` | `formatter_analysis` | 서식 프로필·예시 분석과 내보내기 |
| `개요붙임_원본자료` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `붙임_유형판별` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `붙임_대상찾기` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `중제목_글칸들` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `중제목_유형판별` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `중제목_대상찾기` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `중제목_원본자료` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_구역_본문폭` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_예정_좌우여백` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_최종_본문폭` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_빈_문단인가` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_문단사이_빈줄_삭제` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_문단_본문글` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_서식표_뒤_빈줄_삭제` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_서식표_가로맞춤` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_중제목_번호굵게_적용` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `중제목_표서식_복사` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_중제목_글자치수` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_중제목_문단폭` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_중제목_칸폭_맞춤` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `개요_표인가` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_xml이름` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_자식` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_셀들` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_문단들` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_문자열` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_한칸_제목글인가` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_기타_제목표인가` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_한칸_제목표인가` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_유형판별` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_대상찾기` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `서식표_종류판별` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_서식표_예시` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목2행1열_원본자료` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_원본자료` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_참조병합` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `날짜칸인가` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_날짜칸_한줄` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_표서식_복사` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_문단_가운데정렬` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_괄호부연_축소` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_hwpx_처리` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_제목_임시hwpx_저장` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `이전_작업_임시폴더_정리` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_제목_임시폴더_정리` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `서식구조_조사` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목4종_현재문서_조사` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목4종_현재문서_적용` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `붙임_hwpx_처리` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `중제목_hwpx_처리` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_부제_크기_해석` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_부제_크기_반영` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_담당자_글_반영` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_설정_담당자_글인가` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_서식표_기준` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목_부제_크기` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_칸_글_지우기` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_칸_날짜_현행화` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_빈칸_서식_참조_변환` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_칸_글_넣기` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `서식표_생성` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_제목개요_빈줄_정리` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_서식표_글` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_서식표_글_확인` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `라벨_서식표_적용` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_문서_표번호` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_서식표_번호_부여` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `_hwpx_안전_저장` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `제목개요폭_hwpx_처리` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `상자서식_hwpx_처리` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `쪽번호_hwpx_처리` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `붙임2종_현재문서_조사` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `제목붙임_선행적용` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `정밀표_선행적용` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `붙임2종_현재문서_적용` | `formatter_titles` | 제목·개요·중제목·붙임의 공통 구조 및 적용 |
| `설정_폴더` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `서식프로파일_폴더` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `서식예시_정보_폴더` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `서식예시_폴더` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `첫쪽_그림_만들기` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `번들_서식예시_찾기` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `_json_파일_읽기` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `서식예시_서명` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `설정_파일_경로` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `설정_불러오기` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `설정_저장` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `진행률` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `단계시간_시작` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `_단계시간_닫기` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `단계시간_구간` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `단계시간_끝` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `단계시간_분류` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `단계시간_요약줄` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `단계초기화` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `중단_요청됨` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `_문서_편집_시도` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `hwp_run` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `_문두보호_줄건너뜀` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `번들_상용구_파일_찾기` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `글자상용구_폴더` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `본문상용구_폴더` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `번들_본문상용구_폴더` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `상용구_폴더_준비` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `상용구_전용폴더_찾기` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `텍스트_삽입` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `끝위치추출` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `다음_문단으로_진행` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `쪽표시` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `절약시간_표시` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `절약시간_분초_표시` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `번들_고양이_그림_찾기` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `번들_앱아이콘_찾기` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `_앱아이콘_적용` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `처리_쪽수_구하기` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `쪽범위_사용중` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `쪽범위_안인가` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `쪽범위_끝지남` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `순회_시작` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `범위_다음_문단으로_진행` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `현재_표셀인가` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `숫자_표칸인가` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `저장파일명` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `바이너리_HWP_파일인가` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |
| `텍스트파일_읽기` | `formatter_utils` | 글꼴 탐색·설정·진행·범위 공통 포트 |

## 검증 방법

- `python scripts/verify_split_identity.py --out docs/V2_SPLIT_FORMATTER_IDENTITY.json`: 고정 Git 기준과
  이동/잔류 함수 전체 AST(중첩 함수·문자열 포함)를 비교하며 누락·중복·추가도 실패한다.
- `scripts/verify_formatter_bindings.py`: 직접 import, formatter patch의 실제 호출, 모든 함수 전역,
  runtime resolve 및 컨텍스트별 상태 분리를 검증한다. 전체 unittest 개수는 기존과 동일하게 유지한다.
- 전체 시험·COM 결과 및 빌드 수집 확인은 검증 완료 후 아래에 기록한다.

## 남은 계획

358개 함수의 물리적 이동 뒤에는 공유 namespace 의존성을 명시적 포트로 바꾸는 별도 설계가 필요하다.
이는 알고리즘/함수 본문 수정이므로 C21의 순수 이동 범위에 포함하지 않는다. 제목/표의 공통 XML
primitive와 서식통일의 조사/적용을 더 작게 나누는 작업은 다음 단계에서 같은 AST 검증으로 진행한다.
