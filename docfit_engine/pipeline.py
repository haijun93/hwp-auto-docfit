"""Extracted docfit_engine.pipeline definitions; installed into the compatibility session.

Original algorithms and comments are preserved. Runtime bindings are session-local;
see docfit_engine.runtime. This module does not import the application bootstrap.
"""
from docfit_engine.runtime import bind_function, bind_class

from dataclasses import dataclass
from typing import Callable

def _noop(*args):
    pass

@dataclass(frozen=True)
class PipelineCallbacks:
    log: Callable[[str], None] = _noop
    status: Callable[[str], None] = _noop
    progress: Callable[[str], None] = _noop
    on_stage_enter: Callable[[str], None] = _noop
    on_stage_exit: Callable[[str, bool], None] = _noop
    on_stage_error: Callable[[str, BaseException], None] = _noop
    event: object = None

def _install(*, _docfit_namespace, _docfit_symbol):
    global 쪽범위_계산, 문서_처리_1회, _문서_처리_1회, 로그, 진단로그, 상태, 단계표시, 문서_처리, _문서_처리_본체, 절전_방지, 작업_실행
    if _docfit_symbol == '로그':
        def 로그(message):
            from docfit_engine.context import current_context
            current_context().callbacks.log(str(message))
        return bind_function(로그, _docfit_namespace)
    if _docfit_symbol == '진단로그':
        def 진단로그(message):
            if 검수_사용:
                로그(message)
        return bind_function(진단로그, _docfit_namespace)
    if _docfit_symbol == '상태':
        def 상태(message):
            from docfit_engine.context import current_context
            current_context().callbacks.status(str(message))
        return bind_function(상태, _docfit_namespace)
    if _docfit_symbol == '단계표시':
        def 단계표시(단계명):
            """세부 단계명(또는 상위 절차명)을 받아 해당 상위 절차 칸을 켜도록 큐에 넣는다."""
            단계시간_구간(단계명)
            상위 = _세부단계_단계매핑.get(단계명, 단계명)
            if 상위 in 진행단계_순서:
                from docfit_engine.context import current_context
                current_context().callbacks.progress(상위)
            # 진행 화면의 친절한 단계 안내 문장도 함께 바꾼다.
            gui_queue.put(("guide", 단계명))
        return bind_function(단계표시, _docfit_namespace)
    if _docfit_symbol == '문서_처리':
        def 문서_처리(파일, index, total, 문장부호기능=True):
            """문서 처리 본체를 부르며 단계별 소요 시간을 작업 로그에 남긴다(동작은 같다)."""
            단계시간_시작()
            try:
                return _문서_처리_본체(파일, index, total, 문장부호기능)
            finally:
                표 = 단계시간_끝()
                if 표:
                    for 줄 in 단계시간_요약줄(표, Path(파일).name):
                        로그(줄)
        return bind_function(문서_처리, _docfit_namespace)
    if _docfit_symbol == '_문서_처리_본체':
        def _문서_처리_본체(파일, index, total, 문장부호기능=True):
            global hwp, 현재_처리파일, 한칸표_보호영역, 최종검수_문서목록
            global 쪽범위_본문_문단, 쪽범위_컨트롤영역, 쪽범위_실제, 기본표서식_적용됨
            global _표준서식_XML텍스트, _알파_일괄서식_문서, _표준서식_XML간격
            _표준서식_XML텍스트 = set()
            _표준서식_XML간격 = {}
            _알파_일괄서식_문서 = False
            쪽배치_쪽나눔문단.clear()
            한칸표_보호영역 = set()
            기본표서식_적용됨 = False
            쪽범위_본문_문단 = None
            쪽범위_컨트롤영역 = set()
            쪽범위_실제 = None
            if 중단_요청됨():
                return False

            현재_처리파일 = 파일
            파일명 = Path(파일).name
            상태(f"{index}/{total} : {파일명}")
            로그("")
            로그(f"[{index}/{total}] {파일명}")

            확장자 = Path(파일).suffix.lower()
            원본_확장자명 = "hwpx" if 확장자 == ".hwpx" else "hwp"

            파일경로 = Path(파일)
            if not 파일경로.is_file():
                raise FileNotFoundError(f"문서를 찾을 수 없습니다: {파일}")
            if 확장자 not in 지원_확장자:
                raise ValueError(f"지원하지 않는 파일 형식입니다: {확장자 or '(확장자 없음)'}")
            if 확장자 == ".hwpx" and 바이너리_HWP_파일인가(파일경로):
                # 실측: 이름만 .hwpx이고 내용은 HWP 5.0 바이너리인 배포 문서가 있다.
                로그("확장자는 .hwpx지만 실제 내용은 HWP(바이너리) 문서라 HWP로 엽니다.")
                확장자 = ".hwp"
                원본_확장자명 = "hwp"

            # 한글에 넘기기 전에 경로 조작, ZIP bomb, CRC와 필수 구조를 검사한다.
            원본_구조 = None
            작업_임시폴더 = None
            작업파일경로 = 파일경로

            if 확장자 in (".hwp", ".hwpx"):
                if 확장자 == ".hwpx":
                    if 검수_사용:
                        검사정보, 원본_구조 = validate_and_inspect_hwpx(파일경로)
                    else:
                        검사정보 = validate_hwpx(파일경로)
                    로그(
                        f"HWPX 안전 검사 통과: 압축 항목 {검사정보['entry_count']}개 / "
                        f"해제 예상 {검사정보['total_uncompressed_size']:,}바이트"
                    )

                로그(f"문서 열기: {파일}")
                단계초기화()
                단계표시("열기")
                # HWP NEO에서 최신 HWPX의 호환성 경고가 뜨는 경우에도 자동화가
                # 중단되지 않도록 강제 열기 옵션을 사용한다.
                열린결과 = 한글_문서_열기(hwp, 파일경로, 원본_확장자명.upper(), "forceopen:true")
                if 열린결과 is False:
                    raise RuntimeError(f"한글에서 문서를 열지 못했습니다: {파일}")

                # 바이너리 HWP는 원본을 건드리지 않고 임시 HWPX로 변환한다. 이후의
                # 분석·서식 적용·무결성 검사·저장은 모두 HWPX 문서를 기준으로 수행한다.
                if 확장자 == ".hwp":
                    작업_임시폴더 = tempfile.TemporaryDirectory(prefix="docfit_hwp_to_hwpx_")
                    작업파일경로 = Path(작업_임시폴더.name) / f"{파일경로.stem}.hwpx"
                    if hwp.SaveAs(str(작업파일경로), "HWPX", "") is False:
                        raise RuntimeError("HWP 문서를 작업용 HWPX로 변환하지 못했습니다.")
                    if 검수_사용:
                        검사정보, 원본_구조 = validate_and_inspect_hwpx(작업파일경로)
                    else:
                        검사정보 = validate_hwpx(작업파일경로)
                    로그(
                        f"HWP → HWPX 변환 완료: {작업파일경로.name} / "
                        f"압축 항목 {검사정보['entry_count']}개"
                    )
                    if 한글_문서_열기(hwp, 작업파일경로, "HWPX", "forceopen:true") is False:
                        raise RuntimeError("변환한 작업용 HWPX 문서를 다시 열지 못했습니다.")

                원본_뷰어_문서표시(파일, 원본_확장자명)
            else:
                # .txt/.md/.doc/.docx/.pdf: 한글이 직접 열 수 없으므로 먼저 작업용
                # HWPX로 변환한 뒤, 이후 단계는 HWP/HWPX와 동일하게 진행한다.
                로그(f"문서 변환 중: {파일} → HWPX")
                단계초기화()
                단계표시("변환")
                상태(f"{파일명} : {확장자[1:].upper()} → HWPX 변환 중")
                작업_임시폴더 = tempfile.TemporaryDirectory(prefix="docfit_외부문서_")
                작업파일경로 = Path(작업_임시폴더.name) / f"{파일경로.stem}.hwpx"
                외부문서_hwpx로_변환(파일경로, 확장자, 작업파일경로)
                if 검수_사용:
                    검사정보, 원본_구조 = validate_and_inspect_hwpx(작업파일경로)
                else:
                    검사정보 = validate_hwpx(작업파일경로)
                로그(f"변환 완료: {작업파일경로.name} / 압축 항목 {검사정보['entry_count']}개")
                단계표시("열기")
                if 한글_문서_열기(hwp, 작업파일경로, "HWPX", "forceopen:true") is False:
                    raise RuntimeError(f"변환한 문서를 열지 못했습니다: {파일}")
                # 원본이 HWP/HWPX가 아니므로 좌우 비교 보기 대상에서는 제외한다.
            비교보기_임베드_재확인()

            # 보고서별 원본 쪽 수는 아무것도 고치기 전에 잰다(서식을 입힌 뒤 재면 이미 늘어난 쪽 수가 기준이 된다).
            단계시간_구간('원본 쪽 구성 기록')
            # TXT·MD·DOC·PDF는 원본에 쪽 구성이 없다(변환본은 서식 없는 글이라 기준이 될 수 없다). 쪽 구성 동일 원칙은
            # HWP·HWPX 원본에만 적용한다(2026-10-09 실측: TXT 변환본 2쪽을 기준으로 잡아 '쪽 수 초과' 오판정).
            if 확장자 in ('.hwp', '.hwpx'):
                쪽맞춤_원본_보고서_기록()
            else:
                globals()['쪽맞춤_원본_보고서'] = None

            # 원본 배치의 쪽 범위를 수정 전에 고정한다. 페이지 보호 해제나 서식 변경
            # 이후에 계산하면 쪽이 밀려 사용자가 지정한 문단과 다른 문단을 처리하게 된다.
            if 쪽범위_요청 is not None:
                상태(f"{파일명} : 작업 쪽 범위 확인")
                범위결과 = 쪽범위_계산(*쪽범위_요청)
                if 범위결과 is None:
                    return False
                if 범위결과 is False:
                    raise RuntimeError("지정한 쪽 범위에 처리할 내용이 없습니다. 쪽 범위를 확인해 주세요.")

            # 서식 적용·한 번에 적용은 ① 준말 → 본말 변환 ② 보고서 표준서식(항목기호별 서식 등)을 다른 모든 단계보다
            # 먼저 한다. 서식 통일은 두 단계를 하지 않는다(기본 표 서식 → 서식통일 → 표 서식통일).
            # ① 준말 변환: 줄 첫 어절의 준말을 서식 표·문구로 바꿔 문서 구조가 바뀌므로 뒤의 모든 단계가 바뀐 문서를
            # 기준으로 하게 한다. 아직 문서를 고치지 않았으므로 원본 HWPX를 직접 읽고, 바꿀 줄이 있을 때만 결과를 다시
            # 연다. 쪽 범위 작업에서는 건너뛴다. 서식 표 기준 글자 모양의 자간은 0%라 뒤의 자간 초기화가 만든 표의
            # 서식을 바꾸지 않는다.
            문서_변경됨 = False
            globals()["_문서_제목표_있음"] = False
            맨앞목록 = []
            if (작업_모드 in ('format', 'all') and 준말_등록표
                    and stage_enabled(선택_세부작업, 'abbreviation', 작업_모드)):
                if 쪽범위_요청 is not None:
                    로그("쪽 범위 지정: 준말 변환(문서 전체 구조 변환)은 이번 작업에서 건너뜁니다.")
                else:
                    맨앞목록.append((True, '준말 변환', 준말_hwpx_처리, 'abbrev.hwpx', '준말 변환'))
            # 제목·개요 표 가로 크기(쪽 좌우 여백 사이 최대 폭)는 준말 변환 바로 뒤, 다른 모든 단계보다 먼저 맞춘다
            # (2026-10-03 사용자 요청). 표준서식이 바꿀 편집 여백으로 재므로 여백이 바뀐 뒤에도 그대로 맞는다.
            if (표준서식_사용 and 작업_모드 in ('format', 'all') and 쪽범위_요청 is None and 제목4종_사용
                    and stage_enabled(선택_세부작업, 'pre_format', 작업_모드)):
                맨앞목록.append((True, '제목·개요 가로 크기', 제목개요폭_hwpx_처리, 'title_width.hwpx', '제목·개요 가로 크기'))
            if 알파_일괄서식_가능():
                맨앞목록.append((True, '본문 서식 일괄 적용', 표준서식_hwpx_처리,
                                'body_format.hwpx', '보고서 표준서식'))
            if 맨앞목록:
                상태(f"{파일명} : " + " · ".join(항목[1] for 항목 in 맨앞목록))
                알림 = {}
                if 제목붙임_선행적용(작업파일경로, 현재문서_기준=False, 처리목록=tuple(맨앞목록), 변경알림=알림) is False:
                    return False
                문서_변경됨 = bool(알림.get('changed'))

            # ② 보고서 표준서식. 쪽 범위는 위에서 이미 문단 번호로 고정했다.
            결과 = 표준서식_선행_적용(파일명)
            if 결과 is False:
                return False
            문서_변경됨 = 문서_변경됨 or bool(결과)

            박스그림_실행 = False
            # 박스 그림 표(AI 채팅 답변을 붙여넣을 때 흔한 '┌─┬─┐ / │ … │ / └─┴─┘' 형태)는
            # 문단 구조 자체를 바꾸므로, 자간 초기화를 포함한 다른 모든 서식·자간 단계보다
            # 먼저 변환한다. 쪽 범위 지정 작업은 pre_format·precise_table과 마찬가지로
            # 건너뛴다(문서 전체 구조를 바꾸는 작업이라 쪽 단위로 나눌 수 없음).
            if (표준서식_사용 and 작업_모드 in ('format', 'all') and 쪽범위_요청 is None
                    and stage_enabled(선택_세부작업, 'text_table_convert')):
                단계표시("텍스트 표(박스 그림) 변환")
                상태(f"{파일명} : 텍스트 표(박스 그림) 변환")
                if 박스그림_전체_적용() is False:
                    return False
                박스그림_실행 = True

            # 자간 초기화는 제목·개요·붙임 선행 서식과 일반 표 정밀 복제보다 먼저 한다.
            # 두 단계는 예시 서식의 글자 모양(자간 포함)을 복사하므로, 뒤에서 초기화하면
            # 복사한 자간이 0%로 지워진다. 쪽 범위 작업은 두 단계를 건너뛰므로 범위를
            # 고정한 뒤(아래) 초기화한다.
            자간초기화_완료 = False
            # 알파 1-a: '한 번에 적용'은 아래 XML 선행 단계 맨 앞에서 자간을 초기화한다(한/글 방식 생략).
            자간초기화_XML_예정 = bool(알파_자간초기화_XML_사용 and 작업_모드 == 'all' and 표준서식_사용
                                   and 쪽범위_요청 is None and stage_enabled(선택_세부작업, 'reset_spacing', 작업_모드))
            if (작업_모드 in ('spacing', 'all') and 쪽범위_요청 is None and not 자간초기화_XML_예정
                    and stage_enabled(선택_세부작업, 'reset_spacing', 작업_모드)):
                상태(f"{파일명} : 자간 초기화")
                단계시간_구간('자간 초기화')
                if 문서_전체_자간_초기화() is False:
                    return False
                자간초기화_완료 = True

            # 앞 단계(준말 변환·박스 그림 표 변환·자간 초기화)가 열린 문서를 바꿨으면 뒤 단계는 그 문서를, 아니면 원본
            # 파일을 기준으로 한다. 별표 위첨자는 바꿀 것이 있을 때만 결과를 다시 열고, 다시 열었으면 뒤 단계도 그 문서를
            # 기준으로 한다.
            문서_변경됨 = 문서_변경됨 or 자간초기화_완료 or 박스그림_실행

            # 별표 위첨자·붙임 글꼴 → 제목·개요·붙임 선행 서식 → 기본 표 서식은 모두 HWPX를 직접 고치는 단계다.
            # 예전에는 단계마다 현재 문서를 스냅숏으로 저장하고 결과를 다시 열었다(최대 3회씩). 순서는 그대로 두고
            # 한 HWPX에 이어서 처리한 뒤 결과를 한 번만 연다. 쪽 범위 작업에서는 모두 건너뛴다.
            서식단계_사용 = 표준서식_사용 and 작업_모드 in ('format', 'all')
            선행목록 = []
            if 자간초기화_XML_예정:
                # 제목·개요 선행 서식과 일반 표 정밀 복제는 예시의 자간을 복사하므로 그보다 먼저 초기화한다.
                선행목록.append((True, '자간 초기화', 자간초기화_hwpx_처리, 'spacing_reset.hwpx', '자간 초기화'))
            if 서식단계_사용 and 쪽범위_요청 is None:
                # 글자 서식 정리: 별표(*, **) 위첨자와 붙임~끝. 묶음의 글꼴·크기 통일(글자 모양만 바꿈).
                선행목록 += [
                    (stage_enabled(선택_세부작업, 'asterisk_superscript', 작업_모드), '별표 위첨자',
                     별표위첨자_hwpx_처리, 'asterisk.hwpx', '별표 위첨자'),
                    (stage_enabled(선택_세부작업, 'attachment_font', 작업_모드), '붙임 글꼴',
                     붙임글꼴_hwpx_처리, 'attach_font.hwpx', '별표 위첨자'),
                ]
            if 서식단계_사용:
                if 쪽범위_요청 is not None:
                    # 제목·개요·붙임 표 서식은 문서 전체 구조를 한 번에 바꾸는 방식이라 쪽별로 나눌 수 없다.
                    로그("쪽 범위 지정: 제목·개요·중제목·붙임 자동 서식(문서 전체 구조 변환)은 이번 작업에서 건너뜁니다.")
                elif stage_enabled(선택_세부작업, 'pre_format', 작업_모드):
                    선행목록 += [
                        (bool(알파_머리서식복사_사용 and 활성_머리서식_프로필), '보고서 머리 서식 복사', 보고서머리_hwpx_처리,
                         'report_header.hwpx', '제목·개요·붙임 선행 서식'),
                        (제목4종_사용, '제목·개요', 제목_hwpx_처리, 'title.hwpx', '제목·개요·붙임 선행 서식'),
                        (중제목_사용, '중제목', 중제목_hwpx_처리, 'midtitle.hwpx', '제목·개요·붙임 선행 서식'),
                        (붙임2종_사용, '붙임', 붙임_hwpx_처리, 'attachment.hwpx', '제목·개요·붙임 선행 서식'),
                        # 서식 프로필에 한 칸 상자 예시가 있을 때만(서식 복사 전면 복제)
                        (bool((활성_서식표_프로필 or {}).get('box')), '한 칸 상자', 상자서식_hwpx_처리, 'box.hwpx',
                         '제목·개요·붙임 선행 서식'),
                    ]
            # 쪽 번호 모양: 서식 프로필이 예시 보고서에서 복사한 경우(문서에 쪽 번호가 있을 때만 바꿈)
            if (서식단계_사용 and 쪽범위_요청 is None and 표준서식_설정.get("쪽번호")
                    and stage_enabled(선택_세부작업, 'standard_format', 작업_모드)):
                선행목록.append((True, '쪽 번호 모양', 쪽번호_hwpx_처리, 'page_number.hwpx', '제목·개요·붙임 선행 서식'))
            # 기본 표 서식(준말 '표'의 본말)은 제목·중제목·붙임 서식 표를 정한 뒤, 일반 표 정밀 복제보다 먼저
            # 입힌다(정밀 복제에 맞는 표는 예시 서식으로 다시 덮인다). 서식통일 작업에서도 적용한다.
            기본표_포함 = False
            if ((서식단계_사용 or 작업_모드 == 'unify')
                    and stage_enabled(선택_세부작업, 'table_style', 작업_모드) and 기본표서식() is not None):
                if 쪽범위_요청 is not None:
                    로그("쪽 범위 지정: 기본 표 서식(문서 전체 표 서식 변환)은 이번 작업에서 건너뜁니다.")
                else:
                    로그(("기본 표 서식(서식의 예시 표): " if 활성_표서식_프로필 and 기본표서식() is 활성_표서식_프로필
                         else "기본 표 서식(준말 '표'): ") + 표서식_설명(기본표서식()))
                    선행목록.append((True, '기본 표 서식', 기본표서식_hwpx_처리, 'table_style.hwpx', '기본 표 서식'))
                    기본표_포함 = True
            # 표 칸 너비(글자 수 비례·쪽 좌우 여백 폭)는 기본 표 서식 다음, 일반 표 정밀 복제 앞에서 한다
            # (정밀 복제에 맞는 표는 예시 표의 칸 크기로 다시 덮인다).
            if 서식단계_사용 and stage_enabled(선택_세부작업, 'table_width', 작업_모드):
                if 쪽범위_요청 is not None:
                    로그("쪽 범위 지정: 표 칸 너비 맞춤(문서 전체 표 구조 변경)은 이번 작업에서 건너뜁니다.")
                else:
                    선행목록.append((True, '표 칸 너비', 표너비_hwpx_처리, 'table_width.hwpx', '표 칸 너비'))
            # 연속된 연결 부호 문장(목차·일정표)은 한/글 목차 점선(왼쪽 정렬 탭)으로 맞춘다(알파, 2026-10-10).
            if 서식단계_사용 and 쪽범위_요청 is None and 알파_연결부호_탭정렬_사용:
                선행목록.append((True, '연결 부호 탭 정렬', 연결부호탭_hwpx_처리, 'connector_tab.hwpx', '표 칸 너비'))
            if 서식단계_사용 and 쪽범위_요청 is None and 알파_콜론라벨_정렬_사용:
                선행목록.append((True, '콜론 라벨 정렬', 콜론라벨_hwpx_처리, 'colon_label.hwpx', '표 칸 너비'))
            # 표 칸 안 날짜는 한 줄 표기가 원칙이다(사용자 규칙, 2026-10-10). 표 서식 단계들 뒤 맨 끝에서 지정한다.
            if (서식단계_사용 or 작업_모드 == 'unify') and 쪽범위_요청 is None:
                선행목록.append((True, '표 날짜 칸 한 줄', 표날짜칸_hwpx_처리, 'table_date.hwpx', '표 칸 너비'))
            if any(항목[0] for 항목 in 선행목록):
                상태(f"{파일명} : 글자·제목·표 선행 서식")
                알림 = {}
                if 제목붙임_선행적용(작업파일경로, 현재문서_기준=문서_변경됨,
                                    처리목록=tuple(선행목록), 변경알림=알림) is False:
                    return False
                if 자간초기화_XML_예정:
                    자간초기화_완료 = True
                문서_변경됨 = 문서_변경됨 or bool(알림.get('changed'))
                기본표서식_적용됨 = 기본표_포함
            if 표준서식_사용 and 작업_모드 in ('format', 'all'):
                if 쪽범위_요청 is None and 활성_정밀표_프로필 and stage_enabled(선택_세부작업, 'precise_table'):
                    단계표시("표 정밀 서식")
                    상태(f"{파일명} : 일반 표 정밀 서식 복제")
                    if 정밀표_선행적용() is False:
                        return False
            단계시간_구간('한 칸 표 영역 조사')
            한칸표_보호영역 = 한칸표_영역_목록()

            # 기존 결과를 다시 입력했거나 원문 자체에 설정돼 있던 페이지 보호가
            # 페이지 판정을 왜곡하지 않도록 처리 시작 전에도 먼저 해제한다.
            단계시간_구간('쪽 보호 해제')
            if 작업_모드 != 'unify' and 보고서_페이지보호_전체해제() is False:
                return False

            # 잔여 자간(이전 실행/수동 편집으로 남은 값)이 있으면 압축 여유가
            # 줄어드니, 처리 회차를 시작하기 전 문서 전체를 한 번만 0%로 초기화한다.
            if (작업_모드 in ('spacing', 'all')
                    and stage_enabled(선택_세부작업, 'reset_spacing', 작업_모드)
                    and not 자간초기화_완료):
                상태(f"{파일명} : 자간 초기화")
                단계시간_구간('자간 초기화')
                if 문서_전체_자간_초기화() is False:
                    return False

            # 기본은 1회 처리한다. 사용자가 2회 반복을 선택한 경우에만 1회차의
            # 서식 변경으로 새로 생긴 줄바꿈/페이지 배치를 전체 파이프라인으로 재처리한다.
            총회차 = 작업_반복횟수
            for 회차 in range(1, 총회차 + 1):
                if 중단_요청됨():
                    return False
                if 문서_처리_1회(파일명, 문장부호기능, 회차, 총회차) is False:
                    return False

            # 각 검사는 최종 문단 모양이 확정된 뒤 실행되고 페이지 배치는 맨 마지막에
            # 실행된다. 검수라는 이름으로 같은 수정 함수를 다시 호출하지 않는다.
            단계시간_구간('검수 집계')
            if 검수_사용:
                상태(f"{파일명} : 최종 검수 결과 집계")
                미해결수 = len([x for x in 검수_문제목록 if str(x.get('file')) == str(파일)])
                로그(f"최종 결과 규칙 검수 집계 완료: 미해결 {미해결수}건")

            # 선택한 처리 회차가 끝난 뒤 최종 결과만 한 번 저장한다.
            if 중단_요청됨():
                return False

            # 중간 처리나 입력 문서에 있던 페이지 보호가 최종 HWPX에 남으면 이후
            # 편집 시 큰 문단 묶음이 다시 통째로 이동한다. 저장 직전에 항상 해제한다.
            단계시간_구간('저장 준비(쪽 보호·쪽 나누기 해제)')
            if 작업_모드 != 'unify' and 보고서_페이지보호_전체해제() is False:
                return False
            if not 쪽나누기_사용:
                # 보고서 경계(제목 표)의 쪽 나누기는 보고서가 원본처럼 새 쪽에서 시작하게 하므로 남긴다(사용자 결정, 2026-10-09).
                보존 = set()
                if 쪽맞춤_원본_보고서 or 쪽맞춤_보고서조정됨:
                    try:
                        _표칸영역.clear()
                        보존 = {번호 for 번호, 키 in 본문_표_문단번호().items() if 제목표인가_현재(키)}
                    except Exception as e:
                        로그(f"보고서 경계 확인 실패(무시): {e}")
                묶음보존 = set(쪽배치_쪽나눔문단) - 보존
                푼수 = 문서_쪽나누기_전체해제(보존 | 묶음보존)
                if 푼수 or 묶음보존:
                    로그(f"저장 전 쪽 나누기 {푼수}개 해제(보고서 경계 {len(보존)}곳·쪽 배치 묶음 {len(묶음보존)}곳은 유지)")
            저장파일 = 저장파일명(파일)
            단계표시("저장")
            상태(f"{파일명} : {총회차}회 처리 완료 / 최종 저장 중")
            처리쪽수 = 처리_쪽수_구하기()
            저장결과 = hwp.SaveAs(Path=저장파일, Format="HWPX", arg="")
            if 저장결과 is False:
                raise RuntimeError(f"문서 저장에 실패했습니다: {저장파일}")
            로그(f"전체 처리 {총회차}회 완료")
            로그(f"저장 완료: {저장파일}")
            단계시간_구간('저장 후 규칙 검수')
            최종규칙검사 = 저장결과_규칙검수(파일, 저장파일, 결과창=_결과창_띄우는가(total))
            if 최종규칙검사 is False:
                return False
            단계시간_구간('무결성·숫자 대조')
            무결성 = None
            if 검수_사용 and 원본_구조 is not None:
                결과_구조 = inspect_hwpx(저장파일)
                무결성 = compare_documents(원본_구조, 결과_구조)
                보고서경로 = None
                if 무결성보고서파일_사용:
                    보고서경로 = Path(저장파일).with_name(Path(저장파일).stem + "(무결성검사).json")
                    보고서경로.write_text(json.dumps(무결성, ensure_ascii=False, indent=2), encoding="utf-8")
                로그(
                    f"문서 무결성 검사: {'통과' if 무결성['ok'] else '확인 필요'} / "
                    f"본문 일치도 {무결성['text_similarity']:.1%} / "
                    f"보고서 {보고서경로.name if 보고서경로 else '파일 저장 안 함'}"
                )
                for 문제 in 무결성["issues"]:
                    로그(f"  - [{문제['severity']}] {문제['message']}")
            if 검수_사용:
                # 숫자 데이터 일치 검사(TODO 4순위): 표 가까이의 본문 수치가 그 표에 같은 단위로
                # 있는지 본다. 읽기 전용이며 실패가 아닌 '확인 필요'로만 알린다.
                try:
                    대조 = 숫자_대조(결과_구조 if 원본_구조 is not None else inspect_hwpx(저장파일))
                    최종규칙검사['number_check'] = 대조
                    if 대조['status'] == 'skipped':
                        진단로그(f"숫자 대조: {대조['reason']}")
                    else:
                        로그(f"숫자 대조: 표 가까이 본문 수치 {대조['checked']}개 중 표에서 찾지 못한 "
                             f"{len(대조['review'])}개(확인 필요)")
                        for 항목 in 대조['review']:
                            로그(f"  - [숫자 대조 확인 필요] {항목['text']}: {항목['context']}")
                except Exception as exc:
                    진단로그(f"숫자 대조 실패(무시): {exc}")
            최종검수_문서목록.append({
                "source": str(파일),
                "output": str(저장파일),
                "success": True,
                "rule_checks": 최종규칙검사,
                "processed_pages": 처리쪽수,
                "integrity_ok": 무결성["ok"] if 무결성 is not None else None,
                "text_similarity": 무결성.get("text_similarity") if 무결성 is not None else None,
            })
            if 작업_임시폴더 is not None:
                작업_임시폴더.cleanup()
            # 실행창이 '작업 결과' 표시와 '결과파일 열기'에 쓰도록 알린다.
            gui_queue.put(("saved", str(파일), str(저장파일), 처리쪽수))
            return True
        return bind_function(_문서_처리_본체, _docfit_namespace)
    if _docfit_symbol == '절전_방지':
        def 절전_방지(켜기):
            """처리 중에는 PC가 절전(대기)에 들어가지 않게 한다(화면은 꺼져도 됨).

            실전 테스트에서 긴 문서 처리 중 PC가 절전에 들어가 한글 연결이 끊기고
            (RPC 서버를 사용할 수 없음) 하루 가까이 멈춰 있었다. 이 설정은 호출한
            스레드에만 적용되고, 끄거나 스레드가 끝나면 원래대로 돌아간다. 사용자가
            직접 절전·덮개 닫기를 하면 막지 못한다.
            """
            ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
            try:
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(
                    ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if 켜기 else 0))
            except Exception:
                pass
        return bind_function(절전_방지, _docfit_namespace)
    if _docfit_symbol == '작업_실행':
        def 작업_실행(
            파일목록,
            문장부호기능=True,
            색상=None,
            비교보기=False,
            좌측_프레임_hwnd=None,
            우측_프레임_hwnd=None,
            자동닫기=True,
            표준서식=False,
            검수=False,
            둘째줄기준글자수=5,
            본문재시도횟수=15,
            표재시도횟수=5,
            괄호축소=True,
            표준서식_세부=None,
            표준서식_문단위간격_pt=None,
            괄호라벨굵게=True,
            세트문장같은쪽=True,
            단어분리방지=False,
            실행모드='all',
            라벨기호설정=None,
            줄간격최소=160,
            줄간격최대=200,
            표자간조정=True,
            쪽범위=None,
            로그파일=False,
            세부작업_선택=None,
            반복횟수=1,
            시작_인덱스=1,
            준말_등록=None,  # 화면이 위치 인자로 호출하므로 새 매개변수는 항상 맨 끝에만 추가한다.
            무결성보고서파일=False,
            최종검수파일=False,
        ):
            global 작업_모드, 문두라벨_기호설정
            global 표_자간조정_사용, 쪽범위_요청, 로그파일_사용
            global 단어중간_줄바꿈방지_사용
            global 제목4종_사용, 붙임2종_사용, 중제목_사용, 중제목_번호굵게, 준말_등록표
            global hwp, 색상_설정, 비교보기_사용, 비교보기_좌측_프레임_hwnd, 비교보기_우측_프레임_hwnd, 로그_파일_경로
            global 작업_hwp_hwnd, 자동닫기_설정, 표준서식_사용, 검수_사용, 검수_문제목록, 최종검수_문서목록
            global 무결성보고서파일_사용, 최종검수보고서파일_사용
            global 서식통일_빨간표시_사용, 표준서식_선행_사용
            global 문장부호_2줄_기준글자수, 문장부호_통계, 자간_최대시도_본문, 자간_최대시도_표
            global 세트문장_같은쪽_사용, 세트문장_통계, 단어분리_통계, 다음단어_통계
            global 세트문장_최소줄간격_퍼센트, 세트문장_최대줄간격_퍼센트
            global 괄호_축소_사용, 괄호_라벨_볼드_사용
            global 표준서식_여백_사용, 표준서식_장평_사용, 표준서식_줄간격_사용, 표준서식_제목_사용
            global 표준서식_일자담당자_사용, 표준서식_기호_사용, 표준서식_제목_굵게, 표준서식_일자담당자_굵게
            global 표준서식_내어쓰기_사용
            global 부연설명_들여쓰기_사용, 항목기호_굵게_일관성_사용, 항목기호문장_빈줄_삭제_사용
            global 표준서식_기호_굵게, 표준서식_문단위간격_사용, 표준서식_문단위간격_box_pt
            global 선택_세부작업, 작업_반복횟수
            global 표준서식_문단위간격_circle_pt, 표준서식_문단위간격_note_pt, 표준서식_문단위간격_복귀배율, 표_헤더서식_사용
            global 표준서식_문단위간격_dash_pt
            global 표준서식_문단위간격_chapter_pt, 표준서식_문단위간격_midtitle_pt

            if 표준서식_세부 is None:
                표준서식_세부 = {}
            준말_등록표 = 준말_사용표_만들기(설정_불러오기() if 준말_등록 is None else {'abbreviations': 준말_등록})
            if 표준서식_문단위간격_pt is None:
                표준서식_문단위간격_pt = {}

            절전_방지(True)
            try:
                if 실행모드 not in ("spacing", "unify", "format", "all"):
                    raise ValueError("잘못된 실행 모드")
                작업_모드 = 실행모드
                작업_반복횟수 = 2 if int(반복횟수) >= 2 else 1
                선택_세부작업 = dict(세부작업_선택 or {})
                표_자간조정_사용 = bool(표자간조정)
                쪽범위_요청 = tuple(쪽범위) if 쪽범위 else None
                문두라벨_기호설정 = dict(기본_설정["label_symbols"])
                문두라벨_기호설정.update(라벨기호설정 or {})
                total = len(파일목록)
                검수_사용 = bool(검수)
                무결성보고서파일_사용 = bool(무결성보고서파일)
                최종검수보고서파일_사용 = bool(최종검수파일)
                로그파일_사용 = bool(로그파일)
                if 파일목록 and 로그파일_사용:
                    로그_파일_경로 = str(Path(파일목록[0]).with_name(
                        Path(파일목록[0]).stem + f"(작업로그-{_datetime.datetime.now():%Y%m%d-%H%M%S}).log"
                    ))
                else:
                    로그_파일_경로 = None
                로그(f"프로그램 버전: {APP_VERSION} / 전체 처리 {작업_반복횟수}회 / 단어 분리 방지: {bool(단어분리방지)} / 본문 {본문재시도횟수}단계 / 표 {표재시도횟수}단계 / 줄간격 조정범위 {줄간격최소}~{줄간격최대}%")
                try:
                    globals()["장평_줄이기_사용"] = bool(설정_불러오기().get("ratio_shrink", 기본_설정["ratio_shrink"]))
                except Exception:
                    globals()["장평_줄이기_사용"] = 기본_설정["ratio_shrink"]
                로그(f"장평 줄이기: {'사용' if 장평_줄이기_사용 else '안 함(자간 줄이기·늘리기만 사용)'}")
                로그(f"작업 로그 파일: {로그_파일_경로 or '(만들지 않음)'}")
                정리수 = 이전_작업_임시폴더_정리()
                if 정리수:
                    로그(f"이전 실행의 임시 폴더 {정리수}개 정리")
                if 쪽범위_요청 is None:
                    로그("작업 범위: 문서 전체")
                else:
                    로그(f"작업 범위: {쪽표시(쪽범위_요청[0])} ~ {쪽표시(쪽범위_요청[1])}"
                       " (각 문서에 같은 쪽 번호를 적용, 문서보다 큰 끝 쪽은 마지막쪽까지)")
                로그(f"표 안 문장 자간조정: {'포함' if 표_자간조정_사용 else '제외'}")
                중단_event.clear()
                단어중간_줄바꿈방지_사용 = bool(단어분리방지)
                색상_설정 = 색상
                비교보기_사용 = 비교보기
                비교보기_좌측_프레임_hwnd = 좌측_프레임_hwnd
                비교보기_우측_프레임_hwnd = 우측_프레임_hwnd
                자동닫기_설정 = 자동닫기
                # 서식통일은 문서 자체의 대표 서식이 기준이므로 설정의 표준 서식을 쓰지 않는다.
                표준서식_사용 = bool(표준서식) and 작업_모드 in ("format", "all")
                서식통일_빨간표시_사용 = not 표준서식_사용
                # 보고서 표준서식은 준말 변환 다음 가장 먼저 입힌다(서식 적용·한 번에 적용).
                표준서식_선행_사용 = 표준서식_사용
                검수_사용 = 검수
                검수_문제목록 = []
                최종검수_문서목록 = []
                문장부호_2줄_기준글자수 = 둘째줄기준글자수
                자간_최대시도_본문 = 본문재시도횟수
                자간_최대시도_표 = 표재시도횟수
                # 줄간격 조정은 사용자가 설정창에서 지정한 최소~최대 범위를 벗어나지 않는다.
                세트문장_최소줄간격_퍼센트 = max(10, min(int(줄간격최소), int(줄간격최대)))
                세트문장_최대줄간격_퍼센트 = max(세트문장_최소줄간격_퍼센트, int(줄간격최대))
                괄호_축소_사용 = 표준서식_사용 and bool(괄호축소)
                괄호_라벨_볼드_사용 = 표준서식_사용 and bool(괄호라벨굵게)
                세트문장_같은쪽_사용 = bool(세트문장같은쪽)

                표준서식_여백_사용 = 표준서식_세부.get("std_margin", 표준서식_여백_사용)
                표준서식_장평_사용 = 표준서식_세부.get("std_ratio", 표준서식_장평_사용)
                표준서식_줄간격_사용 = 표준서식_세부.get("std_linespacing", 표준서식_줄간격_사용)
                제목4종_사용 = bool(표준서식_세부.get("std_title_auto", True))
                붙임2종_사용 = bool(표준서식_세부.get("std_attachment_auto", True))
                중제목_사용 = bool(표준서식_세부.get("std_midtitle_auto", True))
                중제목_번호굵게 = bool(표준서식_세부.get("std_midtitle_bold", True))
                표준서식_제목_사용 = 표준서식_세부.get("std_title", 표준서식_제목_사용)
                표준서식_일자담당자_사용 = 표준서식_세부.get("std_dateinfo", 표준서식_일자담당자_사용)
                표준서식_기호_사용 = 표준서식_세부.get("std_symbols", 표준서식_기호_사용)
                표준서식_내어쓰기_사용 = 표준서식_세부.get("std_hanging_indent", 표준서식_내어쓰기_사용)
                부연설명_들여쓰기_사용 = 표준서식_세부.get("std_supplement_indent", 부연설명_들여쓰기_사용)
                항목기호_굵게_일관성_사용 = bool(표준서식_세부.get("std_marker_bold_consistency", True))
                항목기호문장_빈줄_삭제_사용 = bool(표준서식_세부.get("std_remove_blank_lines", True))
                표준서식_제목_굵게 = 표준서식_세부.get("std_title_bold", 표준서식_제목_굵게)
                표준서식_일자담당자_굵게 = 표준서식_세부.get("std_dateinfo_bold", 표준서식_일자담당자_굵게)

                표준서식_기호_굵게 = {
                    "□": 표준서식_세부.get("std_symbol_box_bold", 표준서식_기호_굵게["□"]),
                    "ㅇ": 표준서식_세부.get("std_symbol_o_bold", 표준서식_기호_굵게["ㅇ"]),
                    "-": 표준서식_세부.get("std_symbol_dash_bold", 표준서식_기호_굵게["-"]),
                    "※": 표준서식_세부.get("std_symbol_note_bold", 표준서식_기호_굵게["※"]),
                }

                표준서식_문단위간격_사용 = 표준서식_세부.get("std_parspace", 표준서식_문단위간격_사용)
                표준서식_문단위간격_chapter_pt = 표준서식_문단위간격_pt.get("std_parspace_chapter", 표준서식_문단위간격_chapter_pt)
                표준서식_문단위간격_midtitle_pt = 표준서식_문단위간격_pt.get("std_parspace_midtitle", 표준서식_문단위간격_midtitle_pt)
                표준서식_문단위간격_box_pt = 표준서식_문단위간격_pt.get("std_parspace_box", 표준서식_문단위간격_box_pt)
                표준서식_문단위간격_circle_pt = 표준서식_문단위간격_pt.get("std_parspace_circle", 표준서식_문단위간격_circle_pt)
                표준서식_문단위간격_dash_pt = 표준서식_문단위간격_pt.get("std_parspace_dash", 표준서식_문단위간격_dash_pt)
                표준서식_문단위간격_note_pt = 표준서식_문단위간격_pt.get("std_parspace_note", 표준서식_문단위간격_note_pt)
                표준서식_문단위간격_복귀배율 = 표준서식_문단위간격_pt.get(
                    "std_parspace_return_percent", 표준서식_문단위간격_복귀배율)
                표_헤더서식_사용 = 표준서식_세부.get("std_table_header", 표_헤더서식_사용)
                # 설정창의 표 글꼴·크기는 서식 프로파일 값보다 우선한다.
                표글꼴_적용(표준서식_세부.get("table_fonts"))
                제목_부제_크기_반영(표준서식_세부.get("std_title_subtitle_pt", 제목_부제_크기_pt))
                제목_담당자_글_반영(표준서식_세부.get("title_owner_text", 제목_담당자_글))
                서식통일_결과창_반영(표준서식_세부.get("unify_result_window", 서식통일_결과창_사용))
                # 서식 프로필(예시 보고서) 글꼴의 형식(TTF·HFT)을 등록해 HFT 글꼴도 실제로 입혀지게 한다.
                글꼴형식_등록((표준서식_설정 or {}).get("글꼴형식"))
                # 서식 통일 작업은 세부 작업 '서식통일 문장 자간 정리'(카드의 '자간 정리 제외'와 연동)도 따른다.
                서식통일_자간조정_반영(not 표준서식_세부.get("unify_exclude_spacing", False)
                                 and (작업_모드 != "unify" or stage_enabled(선택_세부작업, "unify_spacing", 작업_모드)))

                문장부호_통계 = {"대상": 0, "성공": 0, "실패": 0}
                세트문장_통계 = {"대상": 0, "성공": 0, "실패": 0, "축소횟수": 0, "확대횟수": 0}
                단어분리_통계 = {"대상": 0, "성공": 0, "실패": 0}
                단계탐색_통계.update(탐색=0, 측정=0)
                다음단어_통계 = {"대상": 0, "적용": 0, "미적용": 0}

                원본_뷰어_분리()
                작업창_분리()

                상태("AutomationModule 확인 중...")
                보안모듈_초기화()

                if 중단_요청됨():
                    gui_queue.put(("stopped", None))
                    return

                상태("한컴오피스 한글 연결 중...")
                한글_시작()

                if 비교보기_사용:
                    상태("비교 보기 창 준비 중...")
                    try:
                        원본_뷰어_시작()
                    except Exception as e:
                        로그(f"비교 보기 준비 오류: {e}")
                        비교보기_사용 = False

                성공 = 0
                실패 = 0

                if 시작_인덱스 > 1:
                    로그(f"이전에 중단된 작업을 이어서 진행합니다: {시작_인덱스}/{total}번째 문서부터")
                    for 완료파일 in 파일목록[:시작_인덱스 - 1]:
                        기존결과 = 저장파일명(완료파일)
                        최종검수_문서목록.append({
                            "source": str(완료파일), "output": str(기존결과),
                            "success": Path(기존결과).is_file(), "integrity_ok": None,
                            "resumed_result": True,
                        })

                for index, 파일 in enumerate(파일목록, 1):
                    if index < 시작_인덱스:
                        continue
                    if 중단_요청됨():
                        break
                    try:
                        result = 문서_처리(파일, index, total, 문장부호기능)
                        if result is False:
                            break
                        성공 += 1
                        진행률(index / total * 100)
                    except Exception as e:
                        실패 += 1
                        최종검수_문서목록.append({
                            "source": str(파일), "output": None, "success": False,
                            "integrity_ok": None, "error": str(e),
                        })
                        traceback.print_exc()
                        로그(f"문서 처리 오류: {파일} — {e}")
                        gui_queue.put(("document_error", str(파일), str(e)))

                로그("=" * 45)
                로그(f"문장부호 줄병합 자간조정 통계({작업_반복횟수}회 누적): 대상 {문장부호_통계['대상']}건 (성공 {문장부호_통계['성공']}/실패 {문장부호_통계['실패']})")
                로그(f"단어 분리 방지 통계({작업_반복횟수}회 누적): 대상 {단어분리_통계['대상']}건 (성공 {단어분리_통계['성공']}/실패 {단어분리_통계['실패']})")
                if 단계탐색_통계["탐색"]:
                    로그(f"자간·장평 단계 탐색: {단계탐색_통계['탐색']}회 / 줄 배치 측정 {단계탐색_통계['측정']}회")
                로그(f"선택적 다음 단어 당김: 대상 {다음단어_통계['대상']}건 "
                     f"(적용 {다음단어_통계['적용']}/미적용 {다음단어_통계['미적용']}, 오류 통계 제외)")
                if 세트문장_같은쪽_사용:
                    로그(
                        f"세트문장 페이지 맞춤 통계({작업_반복횟수}회 누적): 대상 {세트문장_통계['대상']}건 "
                        f"(성공 {세트문장_통계['성공']}/미해결 {세트문장_통계['실패']}, "
                        f"줄간격 축소 {세트문장_통계['축소횟수']}회, 확대 {세트문장_통계.get('확대횟수', 0)}회)"
                    )
                총작업_대상 = 문장부호_통계['대상'] + 단어분리_통계['대상'] + 세트문장_통계['대상']
                총작업_성공 = 문장부호_통계['성공'] + 단어분리_통계['성공'] + 세트문장_통계['성공']
                총작업_실패 = 문장부호_통계['실패'] + 단어분리_통계['실패'] + 세트문장_통계['실패']
                로그(f"작업 항목 총계: 시도 {총작업_대상}건 (성공 {총작업_성공}/실패 {총작업_실패})")

                if 검수_사용:
                    if 검수_문제목록:
                        로그("=" * 45)
                        로그(f"검수 결과: 자간조정 미해결 문단 {len(검수_문제목록)}건")
                        for 항목 in 검수_문제목록:
                            p = 항목["page"] if 항목["page"] is not None else "?"
                            로그(f"  - [{Path(항목['file']).name} / {p}페이지] {항목['text']}")
                    else:
                        로그("검수 결과: 자간조정 미해결 문단 없음")

                if 중단_요청됨():
                    상태("작업 중단")
                    gui_queue.put(("stopped", None))
                else:
                    작업목표 = build_work_goal(작업_모드, total, 선택_세부작업)
                    최종검수 = evaluate_work(
                        작업목표,
                        최종검수_문서목록,
                        {"attempted": 총작업_대상, "succeeded": 총작업_성공},
                        검수_문제목록,
                        verification_enabled=검수_사용,
                    )
                    최종검수['optional_optimizations'] = {'next_word_pull': dict(다음단어_통계)}
                    검수보고서 = None
                    if 최종검수보고서파일_사용:
                        검수보고서 = Path(파일목록[0]).with_name(
                            Path(파일목록[0]).stem + "(최종검수).json"
                        )
                        write_evaluation_report(최종검수, 검수보고서)
                    로그("=" * 45)
                    로그(
                        f"작업 수행 점수: {최종검수['score']:.1f}/100 / "
                        f"판정 {최종검수['verdict']} / "
                        f"보고서 {검수보고서.name if 검수보고서 else '파일 저장 안 함'}"
                    )
                    for 기준 in 최종검수["criteria"]:
                        점수 = f"{기준['score']:.1f}%" if 기준["applicable"] else "해당 없음"
                        로그(f"  - {기준['label']}: {점수}")
                    for 사유 in 최종검수["blockers"]:
                        로그(f"  - 확인: {사유}")
                    for 참고 in 최종검수.get("notes", []):
                        로그(f"  - 참고: {참고}")
                    상태("모든 작업 완료")
                    gui_queue.put(("finished", 성공, 실패, 총작업_대상, 총작업_성공, 총작업_실패,
                                   최종검수, str(검수보고서) if 검수보고서 else None))

            except Exception as e:
                traceback.print_exc()
                gui_queue.put(("fatal_error", str(e)))
            finally:
                절전_방지(False)
                # COM 객체는 생성한 작업 스레드에서 반드시 정리한다.
                # 창을 보존하는 옵션이어도 COM 프록시 자체를 다음 작업 스레드로 넘기면
                # RPC_E_WRONG_THREAD 류 오류가 날 수 있으므로 창만 분리하고 참조를 해제한다.
                if 자동닫기_설정:
                    원본_뷰어_닫기()
                    작업창_닫기()
                else:
                    원본_뷰어_분리()
                    작업창_분리()
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
        return bind_function(작업_실행, _docfit_namespace)
    if _docfit_symbol == '쪽범위_계산':
        def 쪽범위_계산(시작쪽, 끝쪽):
            """지정한 쪽 범위를 본문 문단 번호와 표·글상자 영역 번호로 한 번만 고정한다.

            쪽 번호는 처리 중 줄 수가 바뀌면 밀리므로, 아무것도 고치기 전에 이 함수를
            호출해 두고 이후 모든 단계는 고정된 문단·영역 번호만 본다.
            문단은 '첫 줄이 놓인 쪽' 기준으로 판정한다. 표·글상자는 셀(영역)이 놓인 쪽 기준이다.

            반환: True(범위 확정) / False(범위 안에 처리할 내용 없음) / None(중단됨)
            """
            global 쪽범위_본문_문단, 쪽범위_컨트롤영역, 쪽범위_실제
            쪽범위_본문_문단 = None
            쪽범위_컨트롤영역 = set()
            쪽범위_실제 = None

            hwp_run("Cancel")
            hwp_run("MoveDocBegin")
            문단쪽 = {}
            while True:
                if 중단_요청됨():
                    return None
                pos = hwp.GetPos()
                if pos[0] == 0:
                    hwp_run("MoveParaBegin")
                    시작 = hwp.GetPos()
                    쪽 = 현재_페이지번호()
                    if 쪽 is None:
                        raise RuntimeError("문단이 놓인 쪽 번호를 확인하지 못했습니다.")
                    문단쪽.setdefault(시작[1], 쪽)
                if not 다음_문단으로_진행():
                    break
            if not 문단쪽:
                raise RuntimeError("본문 문단을 찾지 못했습니다.")

            총쪽 = max(문단쪽.values())
            # 0은 '마지막쪽'이다(시작·끝 모두). 끝 쪽이 문서보다 크면 마지막쪽까지로 본다.
            시작 = 총쪽 if not 시작쪽 else max(1, int(시작쪽))
            끝 = 총쪽 if not 끝쪽 else min(int(끝쪽), 총쪽)
            대상 = sorted(p for p, 쪽 in 문단쪽.items() if 시작 <= 쪽 <= 끝)
            if 시작 > 끝 or not 대상:
                로그(f"지정한 쪽 범위({쪽표시(시작쪽)} ~ {쪽표시(끝쪽)})에 해당하는 문단이 없습니다. 이 문서는 총 {총쪽}쪽입니다.")
                hwp_run("MoveDocBegin")
                return False

            영역 = set()
            검사수 = 0
            area = 1
            while True:
                if 중단_요청됨():
                    return None
                area += 1
                try:
                    hwp.SetPos(area, 0, 0)
                except Exception:
                    break
                if hwp.GetPos()[0] != area:
                    break
                검사수 += 1
                쪽 = 현재_페이지번호()
                if 쪽 is not None and 시작 <= 쪽 <= 끝:
                    영역.add(area)
            hwp_run("Cancel")
            hwp_run("MoveDocBegin")

            쪽범위_본문_문단 = (대상[0], 대상[-1])
            쪽범위_컨트롤영역 = 영역
            쪽범위_실제 = (시작, 끝)
            로그(
                f"작업 쪽 범위 확정: {시작}~{끝}쪽 (문서 총 {총쪽}쪽) / "
                f"본문 문단 {len(대상)}개 / 표·글상자 영역 {len(영역)}개 (전체 {검사수}개 중)"
            )
            return True
        return bind_function(쪽범위_계산, _docfit_namespace)
    if _docfit_symbol == '문서_처리_1회':
        def 문서_처리_1회(파일명, 문장부호기능=True, 회차=1, 총회차=1):
            """실행 버튼의 작업 범위에 맞춰 서식과 자간 단계를 분리한다."""
            global 최종_내어쓰기_예정
            최종_내어쓰기_예정 = bool(
                작업_모드 in ('format', 'all') and 표준서식_사용 and 표준서식_내어쓰기_사용
                and stage_enabled(선택_세부작업, 'hanging_indent'))
            try:
                return _문서_처리_1회(파일명, 문장부호기능, 회차, 총회차)
            finally:
                최종_내어쓰기_예정 = False
        return bind_function(문서_처리_1회, _docfit_namespace)
    if _docfit_symbol == '_문서_처리_1회':
        def _문서_처리_1회(파일명, 문장부호기능=True, 회차=1, 총회차=1):
            global _서식통일_문서대표프로필, 서식통일_줄병합_사용
            if 중단_요청됨():
                return False
            if 회차 == 1:
                _서식통일_문서대표프로필 = {}
                _서식통일_자간보류문단.clear()
                _서식통일_위치텍스트_보관.clear()
                _서식통일_보류위치.clear()
            def stage(name, action):
                from docfit_engine.context import current_context
                callbacks = current_context().callbacks
                callbacks.on_stage_enter(name)
                try:
                    단계표시(name)
                    상태(f"{파일명} [{회차}/{총회차}] : {name}")
                    hwp_run('Cancel')
                    순회_시작()
                    result = action() is not False
                except BaseException as error:
                    callbacks.on_stage_error(name, error)
                    raise
                callbacks.on_stage_exit(name, result)
                return result
            def 최종_서식통일_검증():
                # 서식통일이 기준인 경우(표준서식 없음)에만, 서식통일 뒤의 자간·내어쓰기 반복이 바꾼 문장을
                # 처음 대표값으로 다시 맞춘다. 표준서식이 기준이면 괄호 -2pt·최종 내어쓰기·부연설명 단계가
                # 설정값을 입히므로, 서식통일 직후 대표값으로 재적용하면 그 결과를 되돌린다(실측 2026-10-01:
                # 괄호 축소와 내어쓰기가 모두 해제됨). 서식 적용(표준서식 없음)은 서식통일 뒤 바뀌는 단계가 없다.
                if (작업_모드 == 'all' and not 표준서식_사용
                        and stage_enabled(선택_세부작업, 'style_unify', 작업_모드)
                        and _서식통일_문서대표프로필):
                    return stage('후속 작업 후 서식통일 재검증',
                                 lambda: 서식통일_전체_적용(고정_프로필_재적용=True))
                return True
            로그(f"{작업_모드} 처리 {회차}/{총회차}회차 시작")
            # 서식통일은 옵트인(기본 꺼짐). 서식 정리 단계 묶음이 돌지 않는 경우(자간 정리 모드,
            # 표준서식 꺼짐)에도 따로 실행한다.
            if 작업_모드 == 'unify':
                if 회차 > 1:
                    return True
                서식통일_줄병합_사용 = bool(문장부호기능)
                # 문서를 한 번 읽어 항목기호·계층별 대표 서식을 구하고, 다른 문장만 그 값으로 맞춘 뒤
                # 그 문장에만 내어쓰기 → 자간 → 외톨이 글자 당기기를 한 묶음으로 적용한다.
                if not stage('서식통일', 서식통일_전체_적용):
                    return False
                # 표는 본문과 따로, 같은 종류의 표끼리 맞춘다(세부 작업에서 끌 수 있다).
                if stage_enabled(선택_세부작업, 'table_unify', 작업_모드):
                    if not stage('표 서식통일', 서식통일_표_전체_적용):
                        return False
                # 쪽 맞춤은 사용자가 세부 작업에서 켠 경우, 또는 '원본 쪽 구성 유지'를 켠 경우 서식통일 뒤에 실행한다.
                if (stage_enabled(선택_세부작업, 'page_fit', 작업_모드)
                        or stage_enabled(선택_세부작업, 'page_layout_keep', 작업_모드)):
                    return stage('문단 아래 간격 페이지 맞춤', 보고서_페이지수_맞춤_전체_적용)
                return True
            if (회차 == 1 and stage_enabled(선택_세부작업, 'style_unify')
                    and not (작업_모드 in ('format', 'all') and 표준서식_사용)):
                if not stage('서식통일', 서식통일_전체_적용):
                    return False
            # 알파: 문단 세트 방식(문단마다 여러 절차를 차례로 적용하고 문서는 한 번만 순회). 조건이 맞지 않으면 기존 방식.
            세트모드 = 문단세트_가능(회차)
            if 세트모드:
                로그("[문단 세트] 공백·괄호(세트 1)와 내어쓰기·자간(세트 2)을 문단 단위로 한 번에 처리합니다.")
            if 작업_모드 in ('format', 'all') and 표준서식_사용 and 회차 == 1 and 세트모드:
                if not stage('문단 세트 1(공백·문장부호·라벨/괄호)', 문단세트1_글서식_적용):
                    return False
            if 작업_모드 in ('format', 'all') and 표준서식_사용 and 회차 == 1 and not 세트모드:
                # 알파 1-c: 공백 정규화·문장부호 뒤 공백(·서식통일이 꺼져 있으면 라벨/괄호)을 XML 한 번으로.
                라벨_사용 = stage_enabled(선택_세부작업, 'parenthesis') and (괄호_축소_사용 or 괄호_라벨_볼드_사용)
                XML묶음 = {}
                if 알파_글규칙_XML_사용 and 쪽범위_요청 is None:
                    XML묶음 = {"space": stage_enabled(선택_세부작업, 'normalize_space'),
                             "punct": stage_enabled(선택_세부작업, 'punctuation_space'),
                             "label": 라벨_사용 and not stage_enabled(선택_세부작업, 'style_unify')}
                    if any(XML묶음.values()):
                        _글규칙_XML_구성.update(XML묶음)
                        if not stage('공백·문장부호·라벨(XML)',
                                     lambda: 현재문서_XML단계_적용('공백·문장부호·라벨', 글규칙_hwpx_처리, 'text_rules.hwpx')):
                            return False
                for key, name, action, 묶음키 in (
                    ('normalize_space', '공백 정규화', 문장내_공백_정규화_전체_적용, 'space'),
                    ('punctuation_space', '문장부호 뒤 공백 보정', 문장부호_뒤_공백_보정_전체_적용, 'punct'),
                    ('style_unify', '서식통일', 서식통일_전체_적용, None),
                    # 보고서 표준서식은 준말 변환 다음 다른 모든 단계보다 먼저 이미 입혔다(표준서식_선행_적용).
                ):
                    if XML묶음.get(묶음키):
                        continue
                    if stage_enabled(선택_세부작업, key) and not stage(name, action):
                        return False
                if 라벨_사용 and not XML묶음.get("label"):
                    if not stage('문두 라벨/괄호 서식', 괄호_텍스트_크기_축소_전체_적용):
                        return False
            if 작업_모드 in ('format', 'all') and 표준서식_사용 and 회차 == 1:
                # 정밀 프로필·기본 표 서식(준말 '표')은 칸별 서식을 이미 입혔으므로 대표 머리글/본문 값으로 덮지 않는다.
                if (stage_enabled(선택_세부작업, 'table_format') and 표_헤더서식_사용 and not 활성_정밀표_프로필
                        and not 기본표서식_적용됨 and not stage('표 서식', 표_헤더서식_전체_적용)):
                    return False
                # 표 구조 정밀 조정(셀 여백/너비/테두리)은 기본 꺼짐(각 *_사용 변수
                # 참고) — 실험적 기능이라 각 함수가 꺼져 있으면 즉시 True를 반환한다.
                if not stage('셀 안쪽 여백 강제 축소', 표_셀_안쪽여백_전체_적용):
                    return False
                if not stage('셀 너비 본문 맞춤', 표_열너비_본문맞춤_전체_적용):
                    return False
                if not stage('표 테두리 선 굵기 통일', 표_테두리_전체_적용):
                    return False
            if 작업_모드 == 'format' and 표준서식_사용 and stage_enabled(선택_세부작업, 'single_cell_spacing'):
                if not stage('개요·한 칸 표 자간 조정', 한칸표_자간조정):
                    return False
            # 내어쓰기는 화면줄의 가로 폭과 줄바꿈을 바꿀 수 있으므로 자간·단어
            # 분리 검사를 수행하기 전에 최종 문단 모양을 먼저 확정한다.
            if (not 세트모드 and 작업_모드 in ('format', 'all') and 표준서식_사용 and 표준서식_내어쓰기_사용
                    and stage_enabled(선택_세부작업, 'hanging_indent')):
                if not stage('최종 서식 기준 내어쓰기', 문단_내어쓰기_전체_갱신):
                    return False
            # 부연설명은 위 문단의 '실측' 본문 시작 위치에 맞추므로 최종 내어쓰기 뒤에
            # 한다. 자간·단어 분리 검사보다는 앞이어야 옮긴 부연설명의 줄바꿈도 검사된다.
            부연설명_단계_사용 = (작업_모드 in ('format', 'all') and 표준서식_사용
                              and stage_enabled(선택_세부작업, 'supplement_indent')
                              and 부연설명_들여쓰기_사용)
            if 부연설명_단계_사용 and not 세트모드:
                if not stage('부연설명 들여쓰기', 부연설명_들여쓰기_전체_적용):
                    return False
            # 별표(**) 정렬: 앞선 내어쓰기·부연설명 여백 조정이 끝난 뒤 최종 보정한다.
            # 바로 앞줄 *의 별표 위치에 **의 둘째 별표를 맞추며, 필요하면 앞 빈칸을 지운다.
            if (not 세트모드 and 작업_모드 in ('format', 'all') and not 부연설명_단계_사용
                    and stage_enabled(선택_세부작업, 'star_align')):
                if not stage('별표(**) 정렬', 별표_정렬_전체_적용):
                    return False
            if 세트모드:
                if not stage('문단 세트 2(내어쓰기·부연설명·별표·자간·줄 병합)',
                             lambda: 문단세트2_배치_적용(문장부호기능, 부연설명_단계_사용)):
                    return False
                if (stage_enabled(선택_세부작업, 'control_spacing')
                        or stage_enabled(선택_세부작업, 'control_word_check')):
                    if not stage('표/컨트롤 자간·단어 분리 조정', 컨트롤_내부_자간조정):
                        return False
                if (stage_enabled(선택_세부작업, 'control_short_line') and 문장부호기능
                        and not stage('표/컨트롤 줄 병합', 컨트롤_내부_문장부호_처리)):
                    return False
            if 작업_모드 in ('spacing', 'all') and not 세트모드:
                # 자간을 줄이거나 넓히면 항목기호 문장의 첫 줄 폭이 바뀌어
                # 내어쓰기 기준점이 어긋날 수 있다. 자간 변경이 있으면 내어쓰기를
                # 1회 다시 적용하고, 그 결과로 새로 생긴 단어 분리를 다시 검사한다.
                # 무한 반복을 막기 위해 자간 조정 → 내어쓰기는 최대 3회만 수행한다.
                # 2차 이후는 직전 내어쓰기에서 값이 바뀐 문단만 단어 분리를 다시
                # 검사하고, 선택적 '다음 단어 당김'은 하지 않는다.
                내어쓰기_재적용 = 표준서식_내어쓰기_사용 and stage_enabled(선택_세부작업, 'hanging_indent')
                global 재검사_대상문단, 다음단어_당김_사용
                # 자간 정리만 할 때도 공문 띄어쓰기 규정('.  끝.', '붙임  …', 날짜)을 자간 조정 전에 맞춘다.
                # 서식·한 번에 적용은 공백 정규화 단계에서 이미 했다.
                if (작업_모드 == 'spacing' and 회차 == 1 and stage_enabled(선택_세부작업, 'body_spacing')
                        and not stage('공문 띄어쓰기 규정', 공문_띄어쓰기_전체_적용)):
                    return False
                try:
                    for 차수 in range(1, 자간_내어쓰기_최대반복 + 1):
                        접미 = ""
                        if 차수 > 1:
                            접미 = f" ({차수}/{자간_내어쓰기_최대반복}차)"
                            재검사_대상문단 = set(내어쓰기_변경문단)
                            다음단어_당김_사용 = False
                            if not 재검사_대상문단:
                                로그(f"[자간·내어쓰기 반복] {차수}차 재검사 생략: 내어쓰기 값이 바뀐 문단 없음")
                                break
                            로그(f"[자간·내어쓰기 반복] {차수}차 재검사: 내어쓰기가 바뀐 "
                                 f"{len(재검사_대상문단)}개 문단만 단어 분리 검사(다음 단어 당김 제외)")
                        변경_전 = 자간_변경_횟수
                        자간_변경문단.clear()
                        # 두 선택 항목은 같은 전수 순회 함수를 사용하므로 한 번만 실행한다.
                        if (stage_enabled(선택_세부작업, 'body_spacing')
                                or stage_enabled(선택_세부작업, 'word_check')):
                            if not stage('본문 자간·단어 분리 조정' + 접미, 본문_기존자간조정):
                                return False
                            if 알파_연결부호_맞춤_사용 and not stage('연결 부호 맞춤' + 접미, 연결부호_전체_맞춤):
                                return False
                        if stage_enabled(선택_세부작업, 'short_line') and 문장부호기능 and not stage('짧은 마지막 줄 병합' + 접미, 본문_문장부호_처리):
                            return False
                        if (stage_enabled(선택_세부작업, 'control_spacing')
                                or stage_enabled(선택_세부작업, 'control_word_check')):
                            if not stage('표/컨트롤 자간·단어 분리 조정' + 접미, 컨트롤_내부_자간조정):
                                return False
                        if stage_enabled(선택_세부작업, 'control_short_line') and 문장부호기능 and not stage('표/컨트롤 줄 병합' + 접미, 컨트롤_내부_문장부호_처리):
                            return False
                        변경 = 자간_변경_횟수 - 변경_전
                        if not 변경:
                            if 차수 > 1:
                                로그(f"[자간·내어쓰기 반복] {차수}차 재검사: 추가 자간 조정 없음, 반복 종료")
                            break
                        if not 내어쓰기_재적용:
                            break
                        대상 = set(자간_변경문단)
                        로그(f"[자간·내어쓰기 반복] {차수}차 자간 조정 {변경}건 → "
                             f"자간이 바뀐 {len(대상)}개 문단 내어쓰기 재적용")
                        if not stage('자간 조정 후 내어쓰기' + 접미,
                                     lambda: 문단_내어쓰기_전체_갱신(대상문단=대상)):
                            return False
                        # 내어쓰기가 바뀐 위 문단에 딸린 부연설명도 새 위치에 다시 맞춘다
                        # (옮긴 부연설명은 다음 차수 단어 분리 재검사 대상에 들어간다).
                        if 부연설명_단계_사용 and 내어쓰기_변경문단:
                            부모들 = set(내어쓰기_변경문단)
                            if not stage('자간 조정 후 부연설명 들여쓰기' + 접미,
                                         lambda: 부연설명_들여쓰기_전체_적용(부모대상=부모들)):
                                return False
                        if stage_enabled(선택_세부작업, 'star_align') and 내어쓰기_변경문단:
                            if not stage('자간 조정 후 별표(**) 정렬' + 접미, 별표_정렬_전체_적용):
                                return False
                    else:
                        로그(f"[자간·내어쓰기 반복] 최대 {자간_내어쓰기_최대반복}회 도달, 반복 종료")
                finally:
                    재검사_대상문단 = None
                    다음단어_당김_사용 = True
            # 고정 프로필 재적용도 글꼴·크기·문단 간격을 바꿀 수 있는 수정 작업이다.
            # 쪽 배치 이후에 실행하면 확정한 배치를 다시 깨므로 세로 배치 전에 끝낸다.
            if not 최종_서식통일_검증():
                return False
            # 문단 아래 간격 조정은 세로 배치를 다시 바꾼다. 개별 문단이 쪽 사이에
            # 갈라졌는지는 이 단계가 끝난 뒤 마지막으로 처리해야 결과가 재오염되지 않는다.
            쪽수맞춤_사용 = (작업_모드 in ('format', 'all') and 표준서식_사용
                           and stage_enabled(선택_세부작업, 'page_fit'))
            if 쪽수맞춤_사용:
                if not stage('문단 아래 간격 페이지 맞춤', 보고서_페이지수_맞춤_전체_적용):
                    return False
            if 작업_모드 in ('format', 'all') and 표준서식_사용 and 세트문장_같은쪽_사용 and stage_enabled(선택_세부작업, 'page_group'):
                조정_전 = 세트문장_통계.get('확대횟수', 0) + 세트문장_통계.get('축소횟수', 0)
                if not stage('개별 문단 페이지 배치', 문단글_캐시_구간(세트문장_같은쪽_전체_적용)):
                    return False
                조정_후 = 세트문장_통계.get('확대횟수', 0) + 세트문장_통계.get('축소횟수', 0)
                # 문단 페이지 배치가 줄간격을 바꾸면 마지막 쪽이 넘치거나 줄어 쪽 수가
                # 달라질 수 있다. 쪽 수 맞춤을 한 번 더 확인하고, 그 결과 쪽 수가 바뀌면
                # 문단 페이지 배치도 한 번만 더 한다(무한 반복 방지).
                # 사용자 결정(2026-09-24): 쪽 수 맞춤으로 간격을 줄인 뒤 묶음이 쪽 경계에
                # 걸려 쪽 배치가 묶음 전체를 다음 쪽으로 옮기면, 쪽 수가 다시 늘더라도
                # 그 결과와 줄인 간격을 그대로 둔다. 마지막 쪽에 본문 1줄만 남기는 것보다
                # 묶음 전체를 옮기는 편을 택한다.
                if 쪽수맞춤_사용 and 조정_후 > 조정_전 and 쪽맞춤_묶음이동_결정:
                    # 쪽 수 맞춤이 이미 '걸린 묶음은 다음 쪽으로'로 정했다. 쪽 배치가 묶음을
                    # 옮겨 마지막 쪽이 짧아진 것은 의도한 결과이므로 다시 줄이지 않는다
                    # (실측: 9쪽을 8쪽으로 줄이려다 실패하고 되돌리는 데 약 2.5분).
                    로그("[쪽 수 재확인] 쪽 수 맞춤이 걸린 묶음을 다음 쪽으로 옮기기로 한 결과라 다시 줄이지 않습니다.")
                elif 쪽수맞춤_사용 and 조정_후 > 조정_전:
                    # 마지막 쪽을 한 번만 재서, 쪽 수 맞춤이 할 일이 없으면(마지막 쪽에
                    # 내용이 충분하면) 쪽 수 맞춤 단계 자체를 건너뛴다.
                    전_쪽, 남은줄 = 마지막쪽_화면줄수()
                    # 보고서별 1쪽 맞춤을 한 문서(취합보고서 등)는 마지막 쪽과 관계없이 보고서마다 다시 확인한다.
                    if not 쪽맞춤_보고서조정됨 and not (페이지맞춤_문단간격_사용 and 전_쪽 and 전_쪽 > 1
                            and 남은줄 is not None and 남은줄 <= 페이지맞춤_최대남은줄수):
                        진단로그(f"[쪽 수 재확인] 마지막 쪽({전_쪽}쪽) {남은줄}줄: 페이지 수 맞춤 불필요")
                        hwp_run('MoveDocBegin')
                        return True
                    로그("[쪽 수 재확인] 문단 페이지 배치가 줄간격을 바꿔 페이지 수 맞춤을 다시 확인합니다.")
                    if not stage('문단 아래 간격 페이지 맞춤 (재확인)', 보고서_페이지수_맞춤_전체_적용):
                        return False
                    후_쪽, _ = 마지막쪽_화면줄수()
                    if 쪽맞춤_묶음_확인됨:
                        로그("[쪽 수 재확인] 쪽 경계에 걸린 묶음이 없어 문단 페이지 배치를 다시 하지 않습니다.")
                    elif 전_쪽 != 후_쪽 or 쪽맞춤_보고서조정됨:
                        # 보고서별 1쪽 맞춤은 전체 쪽 수가 같아도 보고서 안의 배치를 바꾼다(실측: 표 묶음 쪽 분리 4건이 남음).
                        로그(f"[쪽 수 재확인] 쪽 수 {전_쪽} → {후_쪽}"
                             f"{', 보고서별 1쪽 맞춤으로 배치 변경' if 쪽맞춤_보고서조정됨 else ''}: 문단 페이지 배치를 한 번 더 확인합니다.")
                        if not stage('개별 문단 페이지 배치 (재확인)', 문단글_캐시_구간(세트문장_같은쪽_전체_적용)):
                            return False
                        # 쪽 배치가 묶음을 옮기며 맞춘 보고서를 다시 늘릴 수 있으므로, 원본 쪽 구성 맞춤을 마지막에 한 번 더
                        # 한다(사용자 원칙, 2026-10-09: 결과의 쪽 구성은 원본과 같아야 한다).
                        if 쪽맞춤_원본_보고서 and 쪽맞춤_유형판정_사용:
                            if not stage('보고서 쪽 구성 최종 확인', _문서유형별_쪽맞춤):
                                return False
            hwp_run('MoveDocBegin')
            return True
        return bind_function(_문서_처리_1회, _docfit_namespace)
    raise KeyError(_docfit_symbol)
