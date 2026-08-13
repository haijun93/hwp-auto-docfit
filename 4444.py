# -*- coding: utf-8 -*-

"""
============================================================
HWP Auto DocFit
============================================================

한글 2020 HWP / HWPX 자동 자간 조정 프로그램

주요 기능
------------------------------------------------------------
1. 한글 2020 HwpObject COM 자동화
2. AutomationModule 보안모듈 등록
3. FilePathCheckerModuleExample.dll 최초 1회 설치
4. Registry AutomationModule 최초 1회 등록
5. HWP / HWPX 다중 선택
6. 파일 Drag & Drop
7. 폴더 Drag & Drop
8. 중복 파일 자동 제거
9. 기존 자간 자동 조정 알고리즘
10. 공문서 문장부호/번호 문장 자동 인식
    (같은 문단 내 자동 줄바꿈으로 2줄이 된 경우만 대상,
     실제 Enter로 문단이 나뉜 경우는 제외)
11. 2번째 줄 5자 이하인 경우 자간 축소
12. 한 줄이 될 때까지 반복
13. 표 / 글상자 / 각주 / 미주 등 컨트롤 내부 처리
14. 결과를 "(자간조정)"으로 저장
15. 실행 / 중단 / 종료 버튼
16. 작업 진행률
17. 작업 로그
18. GUI와 HWP 작업을 별도 스레드로 처리
19. GUI 창 크기 자유 조절
20. 최소 GUI 크기 450 x 350
21. 실행 전 확인창 생략
22. 공문서 문장부호 자동 자간 축소 GUI 옵션(ON/OFF)

필요 패키지
------------------------------------------------------------
C:\\Python314\\python.exe -m pip install pywin32 tkinterdnd2

프로그램 폴더
------------------------------------------------------------
4444.py
FilePathCheckerModuleExample.dll

최초 실행 시 DLL을 다음 위치로 복사합니다.

C:\\HwpAutomation\\FilePathCheckerModuleExample.dll

Registry:

HKEY_CURRENT_USER
└─ Software
   └─ HNC
      └─ HwpAutomation
         └─ Modules
            └─ AutomationModule
                 = C:\\HwpAutomation\\FilePathCheckerModuleExample.dll

주의
------------------------------------------------------------
이 프로그램은 한글 2020의 HwpObject COM 자동화를 사용합니다.

실행 환경:
- Windows
- 한글 2020
- Python 3.14 64bit
- pywin32
- tkinterdnd2
- FilePathCheckerModuleExample.dll
============================================================
"""


# ============================================================
# 표준 라이브러리
# ============================================================

import os
import sys
import shutil
import winreg
import threading
import queue
import traceback
import re
import time

from pathlib import Path


# ============================================================
# Tkinter
# ============================================================

import tkinter as tk

from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilenames


# ============================================================
# Drag & Drop
# ============================================================

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:

    print()
    print("=" * 60)
    print("tkinterdnd2가 설치되어 있지 않습니다.")
    print()
    print(
        r"C:\Python314\python.exe -m pip install tkinterdnd2"
    )
    print("=" * 60)
    print()

    raise


# ============================================================
# Windows COM
# ============================================================

import pythoncom
import win32com.client as win32


# ============================================================
# 프로그램 정보
# ============================================================

APP_NAME = "HWP Auto DocFit"
APP_VERSION = "4.1"


# ============================================================
# AutomationModule
# ============================================================

DLL_NAME = "FilePathCheckerModuleExample.dll"

HWP_AUTOMATION_DIR = Path(
    r"C:\HwpAutomation"
)

TARGET_DLL = (
    HWP_AUTOMATION_DIR
    / DLL_NAME
)

REGISTRY_PATH = (
    r"Software\HNC\HwpAutomation\Modules"
)

REGISTRY_VALUE_NAME = (
    "AutomationModule"
)

REGISTER_MODULE_NAME = (
    "FilePathCheckDLL"
)

REGISTER_MODULE_VALUE = (
    "FilePathCheckerModule"
)


# ============================================================
# 자간 설정
# ============================================================

# 일반 기존 알고리즘의 최대 조정 횟수
MAX_GENERAL_SPACING = 15

# 문장부호 2줄 문장의 두 번째 줄 최대 문자 수
SHORT_LINE_MAX = 5

# 자간 축소 명령
SPACING_DECREASE_COMMAND = (
    "CharShapeSpacingDecrease"
)

# 자간 증가 명령
SPACING_INCREASE_COMMAND = (
    "CharShapeSpacingIncrease"
)


# ============================================================
# 공문서 문장 시작 기호
# ============================================================

"""
공문서에서 자주 사용되는 문장/항목 시작 형태.

단순히 기호 하나만 검사하지 않고,
다음과 같은 형태를 함께 지원합니다.

- 문장부호
ㆍ 문장부호
· 문장부호
• 문장부호
○ 문장부호
● 문장부호
□ 문장부호
■ 문장부호
◇ 문장부호
◆ 문장부호
△ 문장부호
▲ 문장부호
▽ 문장부호
▼ 문장부호
※ 문장부호
▶ 문장부호
▷ 문장부호
→ 문장부호
⇒ 문장부호

1.
1)
(1)
①
가.
가)
(가)
㉠

등.
"""

SENTENCE_MARKS = (
    "-",
    "－",
    "–",
    "—",
    "ㆍ",
    "·",
    "•",
    "∙",
    "‧",
    "○",
    "●",
    "◦",
    "◉",
    "◎",
    "□",
    "■",
    "▣",
    "▢",
    "◇",
    "◆",
    "△",
    "▲",
    "▽",
    "▼",
    "※",
    "▶",
    "▷",
    "◀",
    "◁",
    "→",
    "⇒",
    "↔",
    "☞",
    "☑",
    "✓",
    "✔",
    "★",
    "☆",
    "▪",
    "▫",
    "‣",
    "⁃",
    "⁌",
    "⁍",
)


# ============================================================
# 번호형 문장 시작 패턴
# ============================================================

NUMBER_MARK_PATTERN = re.compile(
    r"""
    ^
    (?:
        [0-9]{1,3}[.)]
        |
        \([0-9]{1,3}\)
        |
        [가-힣][.)]
        |
        \([가-힣]\)
        |
        [A-Za-z][.)]
        |
        \([A-Za-z]\)
        |
        [①②③④⑤⑥⑦⑧⑨⑩
         ⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]
        |
        [㉠㉡㉢㉣㉤㉥㉦㉧㉨㉩
         ㉪㉫㉬㉭㉮㉯㉰㉱㉲]
        |
        [ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.)]
    )
    (?=\s|$)
    """,
    re.VERBOSE,
)


# ============================================================
# 전역 상태
# ============================================================

hwp = None

gui_queue = queue.Queue()

중단_event = threading.Event()

# 공문서 문장부호 자동 자간 축소 기능 ON/OFF (GUI 체크박스로 제어)
문장부호_옵션_사용 = True


# ============================================================
# 프로그램 폴더
# ============================================================

def 프로그램_폴더():
    """
    .py 실행:
        현재 Python 파일이 있는 폴더

    EXE 실행:
        EXE 파일이 있는 폴더
    """

    if getattr(
        sys,
        "frozen",
        False
    ):
        return Path(
            sys.executable
        ).resolve().parent

    return Path(
        __file__
    ).resolve().parent


# ============================================================
# GUI 메시지
# ============================================================

def 로그(message):

    print(message)

    gui_queue.put(
        (
            "log",
            str(message)
        )
    )


def 상태(message):

    gui_queue.put(
        (
            "status",
            str(message)
        )
    )


def 진행률(value):

    gui_queue.put(
        (
            "progress",
            int(value)
        )
    )


def 중단_요청됨():

    return 중단_event.is_set()


# ============================================================
# DLL 찾기
# ============================================================

def 원본_DLL_찾기():

    dll_path = (
        프로그램_폴더()
        /
        DLL_NAME
    )

    로그(
        f"DLL 확인: {dll_path}"
    )

    if dll_path.is_file():

        return dll_path

    return None


# ============================================================
# Registry 확인
# ============================================================

def 등록된_DLL_경로():

    try:

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ
        ) as key:

            value, value_type = (
                winreg.QueryValueEx(
                    key,
                    REGISTRY_VALUE_NAME
                )
            )

            if value_type == winreg.REG_SZ:

                return str(value)

    except (
        FileNotFoundError,
        OSError
    ):

        pass

    return None


# ============================================================
# Registry 등록
# ============================================================

def 레지스트리_등록():

    HWP_AUTOMATION_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER,
        REGISTRY_PATH
    ) as key:

        winreg.SetValueEx(
            key,
            REGISTRY_VALUE_NAME,
            0,
            winreg.REG_SZ,
            str(TARGET_DLL)
        )

    로그(
        "AutomationModule Registry 등록 완료"
    )


# ============================================================
# 보안모듈 초기화
# ============================================================

def 보안모듈_초기화():

    """
    최초 실행:

    1. 프로그램 폴더 DLL 확인
    2. C:\\HwpAutomation 생성
    3. DLL 복사
    4. Registry 확인
    5. Registry 필요 시 등록

    이후:

    기존 DLL 및 Registry 재사용
    """

    로그(
        "AutomationModule 확인 시작"
    )

    source_dll = 원본_DLL_찾기()

    if source_dll is None:

        raise FileNotFoundError(
            "\n\n"
            "FilePathCheckerModuleExample.dll을 "
            "프로그램 폴더에서 찾을 수 없습니다.\n\n"
            f"프로그램 폴더:\n"
            f"{프로그램_폴더()}\n\n"
            "다음 파일이 필요합니다.\n"
            f"{프로그램_폴더() / DLL_NAME}\n\n"
            "DLL 파일을 프로그램과 같은 폴더에 넣어주세요."
        )

    HWP_AUTOMATION_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not TARGET_DLL.is_file():

        로그(
            "AutomationModule DLL 최초 설치"
        )

        shutil.copy2(
            source_dll,
            TARGET_DLL
        )

        로그(
            f"DLL 복사 완료: {TARGET_DLL}"
        )

    else:

        로그(
            "C:\\HwpAutomation DLL 확인 완료"
        )

    registered_path = (
        등록된_DLL_경로()
    )

    target_path = (
        TARGET_DLL.resolve()
    )

    registered_normalized = None

    if registered_path:

        try:

            registered_normalized = (
                Path(
                    registered_path
                ).resolve()
            )

        except Exception:

            registered_normalized = Path(
                registered_path
            )

    if (
        registered_normalized
        !=
        target_path
    ):

        로그(
            "AutomationModule Registry 등록 필요"
        )

        레지스트리_등록()

    else:

        로그(
            "AutomationModule Registry 확인 완료"
        )

    로그(
        "AutomationModule 초기화 완료"
    )


# ============================================================
# 한글 시작
# ============================================================

def 한글_시작():

    global hwp

    로그(
        "한글 2020 시작 중..."
    )

    pythoncom.CoInitialize()

    hwp = win32.Dispatch(
        "HwpFrame.HwpObject"
    )

    hwp.XHwpWindows.Item(
        0
    ).Visible = True

    로그(
        "한글 창 표시 성공"
    )

    result = hwp.RegisterModule(
        REGISTER_MODULE_NAME,
        REGISTER_MODULE_VALUE
    )

    로그(
        f"RegisterModule 결과: {result}"
    )

    if not result:

        raise RuntimeError(
            "RegisterModule 등록에 실패했습니다."
        )

    로그(
        "한글 2020 시작 완료"
    )

    return hwp


# ============================================================
# 선택 영역 글자 수
# ============================================================

def 현재선택영역_글자수():

    hwp.InitScan(
        option=None,
        Range=0xff,
        spara=None,
        spos=None,
        epara=None,
        epos=None
    )

    try:

        _, text = hwp.GetText()

        if text is None:

            return 0

        return len(
            text
        )

    finally:

        hwp.ReleaseScan()


# ============================================================
# 선택 영역 텍스트
# ============================================================

def 현재선택영역_텍스트():

    hwp.InitScan(
        option=None,
        Range=0xff,
        spara=None,
        spos=None,
        epara=None,
        epos=None
    )

    try:

        _, text = hwp.GetText()

        if text is None:

            return ""

        return str(text)

    finally:

        hwp.ReleaseScan()


# ============================================================
# 텍스트 정규화
# ============================================================

def 줄_텍스트_정리(text):

    if text is None:

        return ""

    text = str(text)

    # HWP가 반환하는 제어문자 제거
    text = text.replace(
        "\r",
        ""
    )

    text = text.replace(
        "\n",
        ""
    )

    # 탭은 공백 하나로 취급
    text = text.replace(
        "\t",
        " "
    )

    return text


# ============================================================
# 짧은 줄 글자 수
# ============================================================

def 줄_글자수(text):

    """
    사용자가 요구한 조건:

    "빈칸을 포함하여 5개"

    따라서 공백을 제거하지 않고 그대로 len() 계산.
    """

    text = 줄_텍스트_정리(
        text
    )

    return len(
        text
    )


# ============================================================
# 문장부호 시작 여부
# ============================================================

def 문장부호_시작(text):

    """
    문장 앞쪽의 불필요한 공백을 제거한 뒤 판단.

    예:

        "- 문장"
        " - 문장"
        "  - 문장"

    모두 인식.

    또한 번호형 항목도 인식.
    """

    if not text:

        return False

    text = str(
        text
    ).lstrip(
        " \t"
    )

    if not text:

        return False

    # --------------------------------------------------------
    # 일반 기호
    # --------------------------------------------------------

    if text[0] in SENTENCE_MARKS:

        return True

    # --------------------------------------------------------
    # 번호형
    # --------------------------------------------------------

    if NUMBER_MARK_PATTERN.match(
        text
    ):

        return True

    return False


# ============================================================
# 현재 줄 텍스트 가져오기
# ============================================================

def 현재줄_텍스트():

    """
    현재 커서가 위치한 줄 전체를 선택하여
    텍스트를 읽는다.

    읽은 후 선택을 취소하고
    원래 줄의 시작 위치로 복귀한다.
    """

    original_pos = (
        hwp.GetPos()
    )

    try:

        hwp.Run(
            "MoveLineBegin"
        )

        hwp.Run(
            "MoveSelLineEnd"
        )

        text = (
            현재선택영역_텍스트()
        )

    except Exception:

        text = ""

    finally:

        try:

            hwp.Run(
                "Cancel"
            )

        except Exception:

            pass

        try:

            hwp.SetPos(
                original_pos[0],
                original_pos[1],
                original_pos[2]
            )

        except Exception:

            pass

    return 줄_텍스트_정리(
        text
    )


# ============================================================
# 현재 줄 선택
# ============================================================

def 현재줄_선택():

    hwp.Run(
        "MoveLineBegin"
    )

    hwp.Run(
        "MoveSelLineEnd"
    )


# ============================================================
# 다음 줄로 이동
# ============================================================

def 다음줄_이동():

    hwp.Run(
        "MoveLineEnd"
    )

    hwp.Run(
        "MoveNextChar"
    )


# ============================================================
# 같은 문단인지 확인
# ============================================================

def 같은_문단(pos_a, pos_b):

    """
    hwp.GetPos()는 (List, Para, Pos)를 반환한다.

    List/Para가 같다면 두 위치는 같은 문단(문단 내
    자동 줄바꿈) 안에 있는 것이고, 다르다면 그 사이에
    실제 Enter(문단 나눔)가 있었다는 뜻이다.

    텍스트에서 "\\n"을 찾는 방식보다 HWP가 실제로
    관리하는 문단 경계를 직접 확인하므로 더 정확하다.
    """

    return (
        pos_a[0] == pos_b[0]
        and
        pos_a[1] == pos_b[1]
    )


# ============================================================
# 문장부호 2줄 처리
# ============================================================

def 문장부호_2줄_자간조정():

    """
    핵심 신규 기능.

    예:

    - 다채로운 시민참여 행사 개최해 머물고 싶고 다시 방문하고 싶은
      골목으로 조성

    위와 같은 구조에서:

    1. 첫 번째 줄이 문장부호/번호로 시작
    2. 다음 줄이 "같은 문단" 안에서 자동 줄바꿈으로 존재
       (실제 Enter로 나뉜 다음 문단이면 대상에서 제외)
    3. 다음 줄의 글자수가 공백 포함 5자 이하

    라면 첫 번째 줄의 자간을 -1% 한다.

    한 줄로 합쳐질 때까지 반복한다.

    GUI에서 이 기능을 끈 경우(문장부호_옵션_사용 == False)에는
    아무 작업도 하지 않고 즉시 반환한다.

    반환:
        True  = 처리
        False = 중단
    """

    if not 문장부호_옵션_사용:

        return True

    if 중단_요청됨():

        return False

    # --------------------------------------------------------
    # 현재 위치 저장
    # --------------------------------------------------------

    original_pos = (
        hwp.GetPos()
    )

    try:

        # ----------------------------------------------------
        # 현재 문단의 시작으로 이동
        # ----------------------------------------------------

        hwp.Run(
            "MoveParaBegin"
        )

        # ----------------------------------------------------
        # 첫 번째 줄 확인
        # ----------------------------------------------------

        first_line_text = (
            현재줄_텍스트()
        )

        if not first_line_text:

            return True

        # ----------------------------------------------------
        # 문장부호/번호 시작 여부
        # ----------------------------------------------------

        if not 문장부호_시작(
            first_line_text
        ):

            return True

        # ----------------------------------------------------
        # 반복
        # ----------------------------------------------------

        adjustment_count = 0

        while True:

            if 중단_요청됨():

                return False

            if adjustment_count >= MAX_GENERAL_SPACING:

                로그(
                    "문장부호 문장: 자간조정 최대 횟수 도달"
                )

                break

            # ------------------------------------------------
            # 현재 줄의 시작 위치
            # ------------------------------------------------

            current_pos = (
                hwp.GetPos()
            )

            # ------------------------------------------------
            # 현재 줄 끝으로
            # ------------------------------------------------

            hwp.Run(
                "MoveLineEnd"
            )

            before_next = (
                hwp.GetPos()
            )

            # ------------------------------------------------
            # 다음 문자
            # ------------------------------------------------

            hwp.Run(
                "MoveNextChar"
            )

            after_next = (
                hwp.GetPos()
            )

            # ------------------------------------------------
            # 이동하지 못했다면 현재 줄이 마지막
            # ------------------------------------------------

            if (
                before_next
                ==
                after_next
            ):

                break

            # ------------------------------------------------
            # 문단 경계(실제 Enter) 확인
            #
            # 다음 문자가 다른 문단으로 넘어갔다면,
            # 지금 첫 번째 줄은 그 자체로 완결된 문단이고
            # 그 뒤에 실제 Enter가 있다는 뜻이다.
            # 이 경우는 자동 줄바꿈이 아니므로 대상에서 제외한다.
            # ------------------------------------------------

            if not 같은_문단(
                current_pos,
                after_next
            ):

                break

            # ------------------------------------------------
            # 다음 줄 텍스트 확인
            # ------------------------------------------------

            second_line_text = (
                현재줄_텍스트()
            )

            second_line_length = (
                줄_글자수(
                    second_line_text
                )
            )

            # ------------------------------------------------
            # 다음 줄이 5자 초과
            # ------------------------------------------------

            if second_line_length > SHORT_LINE_MAX:

                break

            # ------------------------------------------------
            # 다음 줄이 비어 있는 경우
            # ------------------------------------------------

            if second_line_length == 0:

                break

            # ------------------------------------------------
            # 첫 번째 줄로 복귀
            # ------------------------------------------------

            try:

                hwp.SetPos(
                    current_pos[0],
                    current_pos[1],
                    current_pos[2]
                )

            except Exception:

                break

            # ------------------------------------------------
            # 첫 번째 줄 전체 선택
            # ------------------------------------------------

            현재줄_선택()

            # ------------------------------------------------
            # 자간 -1%
            # ------------------------------------------------

            hwp.Run(
                SPACING_DECREASE_COMMAND
            )

            adjustment_count += 1

            로그(
                "문장부호 2줄 문장: "
                f"두 번째 줄 {second_line_length}자 → "
                f"자간 -1% "
                f"({adjustment_count}회)"
            )

            # ------------------------------------------------
            # 선택 취소
            # ------------------------------------------------

            hwp.Run(
                "Cancel"
            )

            # ------------------------------------------------
            # 문장이 한 줄이 되었는지 확인
            # ------------------------------------------------

            hwp.SetPos(
                current_pos[0],
                current_pos[1],
                current_pos[2]
            )

            first_line_after = (
                현재줄_텍스트()
            )

            hwp.Run(
                "MoveLineEnd"
            )

            hwp.Run(
                "MoveNextChar"
            )

            second_line_after = (
                현재줄_텍스트()
            )

            # ------------------------------------------------
            # 두 번째 줄이 없어졌으면 완료
            # ------------------------------------------------

            if not second_line_after:

                break

            # ------------------------------------------------
            # 다음 줄이 더 이상 짧지 않으면 종료
            # ------------------------------------------------

            if 줄_글자수(
                second_line_after
            ) > SHORT_LINE_MAX:

                break

            # ------------------------------------------------
            # 다시 문장 첫 줄로
            # ------------------------------------------------

            try:

                hwp.SetPos(
                    current_pos[0],
                    current_pos[1],
                    current_pos[2]
                )

            except Exception:

                break

        return True

    except Exception as e:

        로그(
            f"문장부호 문장 처리 오류: {e}"
        )

        return True

    finally:

        try:

            hwp.Run(
                "Cancel"
            )

        except Exception:

            pass

        try:

            hwp.SetPos(
                original_pos[0],
                original_pos[1],
                original_pos[2]
            )

        except Exception:

            pass


# ============================================================
# 기존 자간 자동 조정
# ============================================================

def 자간자동조정():

    """
    기존 프로그램의 핵심 알고리즘.

    라인 끝에서 단어가 걸려 있는 경우:

        앞부분 >= 뒷부분
            → 자간 -1%

        앞부분 < 뒷부분
            → 자간 +1%

    15회 이상이면 Undo.
    """

    count = 0

    while True:

        if 중단_요청됨():

            return False

        hwp.Run(
            "MoveLineEnd"
        )

        hwp.Run(
            "MoveSelWordBegin"
        )

        if count >= MAX_GENERAL_SPACING:

            로그(
                "15회 이상 자간조정으로 원상복구"
            )

            for _ in range(count):

                if 중단_요청됨():

                    return False

                hwp.Run(
                    "Undo"
                )

            try:

                hwp.Run(
                    "Cancel"
                )

            except Exception:

                pass

            return True

        앞부분길이 = (
            현재선택영역_글자수()
        )

        if 앞부분길이 == 0:

            try:

                hwp.Run(
                    "Cancel"
                )

            except Exception:

                pass

            return True

        hwp.Run(
            "MoveSelWordEnd"
        )

        뒷부분길이 = (
            현재선택영역_글자수()
        )

        if not (
            앞부분길이
            and
            뒷부분길이
        ):

            try:

                hwp.Run(
                    "Cancel"
                )

                hwp.Run(
                    "Cancel"
                )

            except Exception:

                pass

            return True

        hwp.Run(
            "MoveWordBegin"
        )

        hwp.Run(
            "MoveLineEnd"
        )

        hwp.Run(
            "MoveSelLineBegin"
        )

        if 앞부분길이 >= 뒷부분길이:

            hwp.Run(
                SPACING_DECREASE_COMMAND
            )

        else:

            hwp.Run(
                SPACING_INCREASE_COMMAND
            )

        count += 1

        hwp.Run(
            "Cancel"
        )


# ============================================================
# 컨트롤 내부 자간 조정
# ============================================================

def 컨트롤_내부_자간조정():

    area = 1

    while True:

        if 중단_요청됨():

            return False

        area += 1

        hwp.SetPos(
            area,
            0,
            0
        )

        if hwp.GetPos()[0] == 0:

            break

        while True:

            if 중단_요청됨():

                return False

            시작위치 = (
                hwp.GetPos()
            )

            # 일반 자간
            result = (
                자간자동조정()
            )

            if result is False:

                return False

            # 문장부호형 2줄
            result = (
                문장부호_2줄_자간조정()
            )

            if result is False:

                return False

            hwp.Run(
                "MoveLineEnd"
            )

            hwp.Run(
                "MoveNextChar"
            )

            current_area = (
                hwp.GetPos()[0]
            )

            if (
                current_area != 0
                and
                current_area >= area
            ):

                area = current_area

            if (
                hwp.GetPos()
                ==
                시작위치
            ):

                break

    return True


# ============================================================
# 본문 전체 처리
# ============================================================

def 본문_자간조정():

    """
    본문을 처음부터 끝까지 처리.

    기존 알고리즘 +
    문장부호 기반 알고리즘.
    """

    끝위치 = (
        끝위치추출()
    )

    while True:

        if 중단_요청됨():

            return False

        현재위치 = (
            hwp.GetPos()
        )

        if 현재위치 == 끝위치:

            break

        # ----------------------------------------------------
        # 기존 자간 조정
        # ----------------------------------------------------

        result = (
            자간자동조정()
        )

        if result is False:

            return False

        # ----------------------------------------------------
        # 문장부호 2줄 조정
        # ----------------------------------------------------

        result = (
            문장부호_2줄_자간조정()
        )

        if result is False:

            return False

        # ----------------------------------------------------
        # 다음 문자
        # ----------------------------------------------------

        hwp.Run(
            "MoveLineEnd"
        )

        hwp.Run(
            "MoveNextChar"
        )

        # ----------------------------------------------------
        # 무한 루프 방지
        # ----------------------------------------------------

        new_pos = (
            hwp.GetPos()
        )

        if new_pos == 현재위치:

            break

    return True


# ============================================================
# 문서 끝 위치
# ============================================================

def 끝위치추출():

    hwp.Run(
        "MoveDocEnd"
    )

    end_pos = (
        hwp.GetPos()
    )

    hwp.Run(
        "MoveDocBegin"
    )

    return end_pos


# ============================================================
# 저장 파일명
# ============================================================

def 저장파일명(
    파일
):

    path = Path(
        파일
    )

    return str(
        path.with_name(
            path.stem
            +
            "(자간조정)"
            +
            path.suffix
        )
    )


# ============================================================
# 문서 닫기
# ============================================================

def 문서_닫기():

    global hwp

    try:

        hwp.Run(
            "FileClose"
        )

    except Exception:

        try:

            hwp.XHwpDocuments.Item(
                0
            ).Close(
                False
            )

        except Exception:

            pass


# ============================================================
# 문서 하나 처리
# ============================================================

def 문서_처리(
    파일,
    index,
    total
):

    global hwp

    if 중단_요청됨():

        return False

    파일명 = (
        Path(파일).name
    )

    상태(
        f"{index}/{total} : {파일명}"
    )

    로그("")

    로그(
        f"[{index}/{total}] {파일명}"
    )

    확장자 = (
        Path(파일)
        .suffix
        .lower()
    )

    if 확장자 == ".hwpx":

        확장자명 = "hwpx"

    elif 확장자 == ".hwp":

        확장자명 = "hwp"

    else:

        raise ValueError(
            f"지원하지 않는 파일: {파일}"
        )

    # --------------------------------------------------------
    # 기존 문서 닫기
    # --------------------------------------------------------

    try:

        문서_닫기()

    except Exception:

        pass

    # --------------------------------------------------------
    # 문서 열기
    # --------------------------------------------------------

    로그(
        f"문서 열기: {파일}"
    )

    opened = hwp.Open(
        파일,
        Format=확장자명.upper(),
        arg=""
    )

    if not opened:

        raise RuntimeError(
            f"문서를 열지 못했습니다: {파일}"
        )

    # --------------------------------------------------------
    # 처음 위치
    # --------------------------------------------------------

    hwp.Run(
        "MoveDocBegin"
    )

    # --------------------------------------------------------
    # 본문
    # --------------------------------------------------------

    상태(
        f"{파일명} : 본문 자간 조정"
    )

    result = (
        본문_자간조정()
    )

    if result is False:

        return False

    # --------------------------------------------------------
    # 컨트롤
    # --------------------------------------------------------

    상태(
        f"{파일명} : 표/글상자 자간 조정"
    )

    result = (
        컨트롤_내부_자간조정()
    )

    if result is False:

        return False

    # --------------------------------------------------------
    # 저장
    # --------------------------------------------------------

    if 중단_요청됨():

        return False

    저장파일 = (
        저장파일명(파일)
    )

    상태(
        f"{파일명} : 저장 중"
    )

    로그(
        f"저장 시작: {저장파일}"
    )

    document_format = (
        hwp.XHwpDocuments
        .Item(0)
        .Format
    )

    hwp.SaveAs(
        Path=저장파일,
        Format=document_format,
        arg=""
    )

    # --------------------------------------------------------
    # 저장 확인
    # --------------------------------------------------------

    if not Path(
        저장파일
    ).is_file():

        raise RuntimeError(
            "결과 파일 저장 확인 실패"
        )

    로그(
        f"저장 완료: {저장파일}"
    )

    return True


# ============================================================
# 전체 작업
# ============================================================

def 작업_실행(
    파일목록
):

    global hwp

    com_initialized = False

    try:

        total = len(
            파일목록
        )

        if total == 0:

            raise ValueError(
                "처리할 문서가 없습니다."
            )

        중단_event.clear()

        # ----------------------------------------------------
        # AutomationModule
        # ----------------------------------------------------

        상태(
            "AutomationModule 확인 중..."
        )

        보안모듈_초기화()

        if 중단_요청됨():

            gui_queue.put(
                (
                    "stopped",
                    None
                )
            )

            return

        # ----------------------------------------------------
        # 한글 시작
        # ----------------------------------------------------

        상태(
            "한글 2020 시작 중..."
        )

        한글_시작()

        com_initialized = True

        # ----------------------------------------------------
        # 문서 처리
        # ----------------------------------------------------

        success_count = 0

        for index, 파일 in enumerate(
            파일목록,
            1
        ):

            if 중단_요청됨():

                break

            try:

                result = (
                    문서_처리(
                        파일,
                        index,
                        total
                    )
                )

                if result is False:

                    break

                success_count += 1

                진행률(
                    index
                    /
                    total
                    *
                    100
                )

            except Exception as e:

                traceback.print_exc()

                로그(
                    f"문서 처리 오류: {파일}"
                )

                로그(
                    f"{type(e).__name__}: {e}"
                )

                gui_queue.put(
                    (
                        "document_error",
                        str(파일),
                        str(e)
                    )
                )

        # ----------------------------------------------------
        # 결과
        # ----------------------------------------------------

        if 중단_요청됨():

            상태(
                "작업 중단"
            )

            gui_queue.put(
                (
                    "stopped",
                    None
                )
            )

        else:

            상태(
                f"모든 작업 완료 ({success_count}/{total})"
            )

            gui_queue.put(
                (
                    "finished",
                    success_count,
                    total
                )
            )

    except Exception as e:

        traceback.print_exc()

        gui_queue.put(
            (
                "fatal_error",
                str(e)
            )
        )

    finally:

        # ----------------------------------------------------
        # 한글 종료
        # ----------------------------------------------------

        if hwp is not None:

            try:

                로그(
                    "한글 종료 중..."
                )

                hwp.Quit()

                로그(
                    "한글 종료 완료"
                )

            except Exception as e:

                로그(
                    f"한글 종료 오류: {e}"
                )

            finally:

                hwp = None

        # ----------------------------------------------------
        # COM 종료
        # ----------------------------------------------------

        if com_initialized:

            try:

                pythoncom.CoUninitialize()

            except Exception:

                pass


# ============================================================
# GUI
# ============================================================

class HwpAutoDocFitGUI:

    def __init__(
        self,
        root
    ):

        self.root = root

        self.files = []

        self.worker = None

        self.running = False

        self.closing = False

        # ====================================================
        # Window
        # ====================================================

        root.title(
            f"{APP_NAME} v{APP_VERSION}"
        )

        root.geometry(
            "520x450"
        )

        # 기존 요청:
        # 현재 창 크기의 약 1/3 수준까지 축소 가능
        root.minsize(
            450,
            350
        )

        root.resizable(
            True,
            True
        )

        # ====================================================
        # Style
        # ====================================================

        style = ttk.Style()

        try:

            style.theme_use(
                "vista"
            )

        except Exception:

            pass

        # ====================================================
        # Root Grid
        # ====================================================

        root.grid_rowconfigure(
            0,
            weight=0
        )

        root.grid_rowconfigure(
            1,
            weight=1
        )

        root.grid_rowconfigure(
            2,
            weight=0
        )

        root.grid_columnconfigure(
            0,
            weight=1
        )

        # ====================================================
        # Header
        # ====================================================

        header = ttk.Frame(
            root,
            padding=(
                12,
                8,
                12,
                4
            )
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        header.grid_columnconfigure(
            0,
            weight=1
        )

        ttk.Label(
            header,
            text=APP_NAME,
            font=(
                "맑은 고딕",
                14,
                "bold"
            )
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ttk.Label(
            header,
            text="한글 2020 HWP / HWPX 자동 자간 조정"
        ).grid(
            row=1,
            column=0,
            sticky="w"
        )

        # ====================================================
        # Main
        # ====================================================

        main_frame = ttk.Frame(
            root,
            padding=(
                12,
                0,
                12,
                0
            )
        )

        main_frame.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        main_frame.grid_rowconfigure(
            0,
            weight=3
        )

        main_frame.grid_rowconfigure(
            1,
            weight=0
        )

        main_frame.grid_rowconfigure(
            2,
            weight=0
        )

        main_frame.grid_rowconfigure(
            3,
            weight=2
        )

        main_frame.grid_columnconfigure(
            0,
            weight=1
        )

        # ====================================================
        # File Frame
        # ====================================================

        file_frame = ttk.LabelFrame(
            main_frame,
            text="문서 선택",
            padding=6
        )

        file_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            pady=(0, 4)
        )

        file_frame.grid_rowconfigure(
            1,
            weight=1
        )

        file_frame.grid_columnconfigure(
            0,
            weight=1
        )

        # ====================================================
        # Drop Label
        # ====================================================

        self.drop_label = ttk.Label(
            file_frame,
            text=(
                "HWP / HWPX 파일 또는 폴더를\n"
                "여기로 끌어다 놓으세요"
            ),
            anchor="center",
            justify="center"
        )

        self.drop_label.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 4)
        )

        self.drop_label.drop_target_register(
            DND_FILES
        )

        self.drop_label.dnd_bind(
            "<<Drop>>",
            self.파일_드롭
        )

        # ====================================================
        # List
        # ====================================================

        list_frame = ttk.Frame(
            file_frame
        )

        list_frame.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        list_frame.grid_rowconfigure(
            0,
            weight=1
        )

        list_frame.grid_columnconfigure(
            0,
            weight=1
        )

        list_scroll = ttk.Scrollbar(
            list_frame,
            orient="vertical"
        )

        list_scroll.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.file_list = tk.Listbox(
            list_frame,
            font=(
                "맑은 고딕",
                9
            ),
            yscrollcommand=(
                list_scroll.set
            ),
            selectmode=tk.SINGLE,
            borderwidth=1
        )

        self.file_list.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        list_scroll.config(
            command=self.file_list.yview
        )

        self.file_list.drop_target_register(
            DND_FILES
        )

        self.file_list.dnd_bind(
            "<<Drop>>",
            self.파일_드롭
        )

        file_frame.drop_target_register(
            DND_FILES
        )

        file_frame.dnd_bind(
            "<<Drop>>",
            self.파일_드롭
        )

        # ====================================================
        # Options
        # ====================================================

        options_frame = ttk.Frame(
            main_frame
        )

        options_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 4)
        )

        options_frame.grid_columnconfigure(
            0,
            weight=1
        )

        self.문장부호_var = tk.BooleanVar(
            value=True
        )

        self.문장부호_checkbox = ttk.Checkbutton(
            options_frame,
            text=(
                "공문서 문장부호(항목기호) "
                "자동 자간 축소"
            ),
            variable=self.문장부호_var
        )

        self.문장부호_checkbox.grid(
            row=0,
            column=0,
            sticky="w"
        )

        # ====================================================
        # Status
        # ====================================================

        status_frame = ttk.Frame(
            main_frame
        )

        status_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 4)
        )

        status_frame.grid_columnconfigure(
            0,
            weight=1
        )

        self.status_var = tk.StringVar(
            value=(
                "HWP/HWPX 파일 또는 폴더를 선택하세요."
            )
        )

        ttk.Label(
            status_frame,
            textvariable=self.status_var
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.progress = ttk.Progressbar(
            status_frame,
            orient="horizontal",
            mode="determinate",
            maximum=100
        )

        self.progress.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(3, 0)
        )

        # ====================================================
        # Log
        # ====================================================

        log_frame = ttk.LabelFrame(
            main_frame,
            text="작업 로그",
            padding=4
        )

        log_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            pady=(0, 4)
        )

        log_frame.grid_rowconfigure(
            0,
            weight=1
        )

        log_frame.grid_columnconfigure(
            0,
            weight=1
        )

        log_scroll = ttk.Scrollbar(
            log_frame,
            orient="vertical"
        )

        log_scroll.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.log_text = tk.Listbox(
            log_frame,
            font=(
                "맑은 고딕",
                8
            ),
            yscrollcommand=(
                log_scroll.set
            ),
            borderwidth=1
        )

        self.log_text.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        log_scroll.config(
            command=self.log_text.yview
        )

        # ====================================================
        # Buttons
        # ====================================================

        self.button_frame = ttk.Frame(
            root,
            padding=(
                12,
                4,
                12,
                8
            )
        )

        self.button_frame.grid(
            row=2,
            column=0,
            sticky="ew"
        )

        self.button_frame.grid_columnconfigure(
            0,
            weight=1
        )

        # ----------------------------------------------------
        # 왼쪽
        # ----------------------------------------------------

        left_buttons = ttk.Frame(
            self.button_frame
        )

        left_buttons.grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.select_button = ttk.Button(
            left_buttons,
            text="파일선택",
            command=self.파일선택,
            width=9
        )

        self.select_button.pack(
            side="left"
        )

        self.clear_button = ttk.Button(
            left_buttons,
            text="목록 지우기",
            command=self.목록지우기,
            width=11
        )

        self.clear_button.pack(
            side="left",
            padx=(4, 0)
        )

        # ----------------------------------------------------
        # 오른쪽
        # ----------------------------------------------------

        action_buttons = ttk.Frame(
            self.button_frame
        )

        action_buttons.grid(
            row=0,
            column=1,
            sticky="e"
        )

        self.start_button = ttk.Button(
            action_buttons,
            text="▶ 실행",
            command=self.작업시작,
            width=9
        )

        self.start_button.pack(
            side="left",
            padx=2
        )

        self.stop_button = ttk.Button(
            action_buttons,
            text="■ 중단",
            command=self.작업중단,
            width=9,
            state="disabled"
        )

        self.stop_button.pack(
            side="left",
            padx=2
        )

        self.exit_button = ttk.Button(
            action_buttons,
            text="✕ 종료",
            command=self.종료,
            width=9
        )

        self.exit_button.pack(
            side="left",
            padx=2
        )

        # ====================================================
        # Queue
        # ====================================================

        root.after(
            100,
            self.queue_처리
        )

        # ====================================================
        # Close
        # ====================================================

        root.protocol(
            "WM_DELETE_WINDOW",
            self.종료
        )

    # ========================================================
    # 로그 표시
    # ========================================================

    def 로그표시(
        self,
        message
    ):

        self.log_text.insert(
            tk.END,
            str(message)
        )

        self.log_text.see(
            tk.END
        )

    # ========================================================
    # 파일 추가
    # ========================================================

    def 파일추가(
        self,
        file_path
    ):

        try:

            file_path = str(
                Path(
                    file_path
                ).resolve()
            )

        except Exception:

            return False

        if not os.path.isfile(
            file_path
        ):

            return False

        suffix = (
            Path(file_path)
            .suffix
            .lower()
        )

        if suffix not in (
            ".hwp",
            ".hwpx"
        ):

            return False

        if file_path in self.files:

            return False

        self.files.append(
            file_path
        )

        self.file_list.insert(
            tk.END,
            file_path
        )

        return True

    # ========================================================
    # 폴더 추가
    # ========================================================

    def 폴더추가(
        self,
        folder_path
    ):

        folder = Path(
            folder_path
        )

        if not folder.is_dir():

            return 0

        count = 0

        try:

            items = sorted(
                folder.iterdir(),
                key=lambda p:
                p.name.lower()
            )

        except Exception:

            return 0

        for path in items:

            if not path.is_file():

                continue

            if path.suffix.lower() not in (
                ".hwp",
                ".hwpx"
            ):

                continue

            if self.파일추가(
                path
            ):

                count += 1

        return count

    # ========================================================
    # Drag & Drop
    # ========================================================

    def 파일_드롭(
        self,
        event
    ):

        if self.running:

            return

        try:

            items = (
                self.root.tk.splitlist(
                    event.data
                )
            )

        except Exception:

            items = [
                event.data
            ]

        added = 0

        for item in items:

            item = str(
                item
            ).strip()

            if os.path.isdir(
                item
            ):

                added += (
                    self.폴더추가(
                        item
                    )
                )

            elif os.path.isfile(
                item
            ):

                if self.파일추가(
                    item
                ):

                    added += 1

        if added:

            self.status_var.set(
                f"{len(self.files)}개 문서 선택"
            )

            self.로그표시(
                f"{added}개 문서 추가"
            )

    # ========================================================
    # 파일 선택
    # ========================================================

    def 파일선택(
        self
    ):

        if self.running:

            return

        files = askopenfilenames(
            parent=self.root,
            title=(
                "자간을 조정할 "
                "HWP/HWPX 문서를 선택하세요."
            ),
            initialdir=os.getcwd(),
            filetypes=[
                (
                    "한/글 파일",
                    "*.hwp *.hwpx"
                ),
                (
                    "HWP 파일",
                    "*.hwp"
                ),
                (
                    "HWPX 파일",
                    "*.hwpx"
                )
            ]
        )

        if not files:

            return

        added = 0

        for file in files:

            if self.파일추가(
                file
            ):

                added += 1

        self.status_var.set(
            f"{len(self.files)}개 문서 선택"
        )

        if added:

            self.로그표시(
                f"{added}개 문서 추가"
            )

    # ========================================================
    # 목록 삭제
    # ========================================================

    def 목록지우기(
        self
    ):

        if self.running:

            return

        self.files.clear()

        self.file_list.delete(
            0,
            tk.END
        )

        self.progress["value"] = 0

        self.status_var.set(
            "HWP/HWPX 파일 또는 폴더를 선택하세요."
        )

    # ========================================================
    # 작업 시작
    # ========================================================

    def 작업시작(
        self
    ):

        if self.running:

            return

        if not self.files:

            messagebox.showwarning(
                APP_NAME,
                (
                    "먼저 HWP/HWPX 문서를 "
                    "선택하거나 끌어다 놓으세요."
                ),
                parent=self.root
            )

            return

        # ====================================================
        # 중요
        #
        # 기존의:
        #
        # "1개 문서의 자간을 자동 조정합니다."
        #
        # 확인창은 제거함.
        # ====================================================

        self.running = True

        self.closing = False

        중단_event.clear()

        # ----------------------------------------------------
        # 공문서 문장부호 자동 자간 축소 옵션 적용
        # ----------------------------------------------------

        global 문장부호_옵션_사용

        문장부호_옵션_사용 = (
            self.문장부호_var.get()
        )

        self.progress["value"] = 0

        # ----------------------------------------------------
        # 버튼 상태
        # ----------------------------------------------------

        self.start_button.config(
            state="disabled"
        )

        self.stop_button.config(
            state="normal"
        )

        self.select_button.config(
            state="disabled"
        )

        self.clear_button.config(
            state="disabled"
        )

        self.문장부호_checkbox.config(
            state="disabled"
        )

        # ----------------------------------------------------
        # 로그
        # ----------------------------------------------------

        self.로그표시("")

        self.로그표시(
            "=" * 50
        )

        self.로그표시(
            f"{APP_NAME} 작업 시작"
        )

        self.로그표시(
            f"처리 문서: {len(self.files)}개"
        )

        self.로그표시(
            "=" * 50
        )

        # ----------------------------------------------------
        # Worker
        # ----------------------------------------------------

        self.worker = threading.Thread(
            target=작업_실행,
            args=(
                list(self.files),
            ),
            daemon=True
        )

        self.worker.start()

    # ========================================================
    # 작업 중단
    # ========================================================

    def 작업중단(
        self
    ):

        if not self.running:

            return

        answer = messagebox.askyesno(
            APP_NAME,
            (
                "현재 자간 조정 작업이 진행 중입니다.\n\n"
                "작업을 중단하시겠습니까?"
            ),
            parent=self.root
        )

        if not answer:

            return

        중단_event.set()

        self.stop_button.config(
            state="disabled"
        )

        self.status_var.set(
            "작업 중단 처리 중..."
        )

        self.로그표시(
            "사용자가 작업 중단을 요청했습니다."
        )

    # ========================================================
    # 버튼 상태 복원
    # ========================================================

    def 버튼_복원():

        pass

    # ========================================================
    # Queue 처리
    # ========================================================

    def queue_처리(
        self
    ):

        try:

            while True:

                item = (
                    gui_queue.get_nowait()
                )

                event = item[0]

                # ------------------------------------------------
                # 로그
                # ------------------------------------------------

                if event == "log":

                    self.로그표시(
                        item[1]
                    )

                # ------------------------------------------------
                # 상태
                # ------------------------------------------------

                elif event == "status":

                    self.status_var.set(
                        item[1]
                    )

                # ------------------------------------------------
                # 진행률
                # ------------------------------------------------

                elif event == "progress":

                    self.progress[
                        "value"
                    ] = item[1]

                # ------------------------------------------------
                # 문서 오류
                # ------------------------------------------------

                elif event == "document_error":

                    self.로그표시(
                        f"문서 처리 실패: {item[1]}"
                    )

                    self.로그표시(
                        item[2]
                    )

                # ------------------------------------------------
                # 중단
                # ------------------------------------------------

                elif event == "stopped":

                    self.running = False

                    self.start_button.config(
                        state="normal"
                    )

                    self.stop_button.config(
                        state="disabled"
                    )

                    self.select_button.config(
                        state="normal"
                    )

                    self.clear_button.config(
                        state="normal"
                    )

                    self.문장부호_checkbox.config(
                        state="normal"
                    )

                    self.status_var.set(
                        "작업 중단"
                    )

                    self.로그표시(
                        "=" * 50
                    )

                    self.로그표시(
                        "작업이 중단되었습니다."
                    )

                    self.로그표시(
                        "=" * 50
                    )

                    if not self.closing:

                        messagebox.showinfo(
                            APP_NAME,
                            (
                                "자간 조정 작업이 "
                                "중단되었습니다."
                            ),
                            parent=self.root
                        )

                # ------------------------------------------------
                # 완료
                # ------------------------------------------------

                elif event == "finished":

                    self.running = False

                    self.progress[
                        "value"
                    ] = 100

                    self.start_button.config(
                        state="normal"
                    )

                    self.stop_button.config(
                        state="disabled"
                    )

                    self.select_button.config(
                        state="normal"
                    )

                    self.clear_button.config(
                        state="normal"
                    )

                    self.문장부호_checkbox.config(
                        state="normal"
                    )

                    success_count = item[1]

                    total = item[2]

                    self.status_var.set(
                        f"작업 완료 ({success_count}/{total})"
                    )

                    self.로그표시(
                        "=" * 50
                    )

                    self.로그표시(
                        f"모든 작업 완료: "
                        f"{success_count}/{total}"
                    )

                    self.로그표시(
                        "=" * 50
                    )

                    if not self.closing:

                        messagebox.showinfo(
                            APP_NAME,
                            (
                                "자간 조정이 완료되었습니다.\n\n"
                                f"정상 처리: "
                                f"{success_count}/{total}\n\n"
                                "원본 파일은 유지되며\n"
                                "'(자간조정)' 결과 파일이 "
                                "생성되었습니다."
                            ),
                            parent=self.root
                        )

                # ------------------------------------------------
                # 치명적 오류
                # ------------------------------------------------

                elif event == "fatal_error":

                    self.running = False

                    self.start_button.config(
                        state="normal"
                    )

                    self.stop_button.config(
                        state="disabled"
                    )

                    self.select_button.config(
                        state="normal"
                    )

                    self.clear_button.config(
                        state="normal"
                    )

                    self.문장부호_checkbox.config(
                        state="normal"
                    )

                    self.status_var.set(
                        "오류 발생"
                    )

                    self.로그표시(
                        "치명적 오류:"
                    )

                    self.로그표시(
                        item[1]
                    )

                    if not self.closing:

                        messagebox.showerror(
                            APP_NAME,
                            (
                                "작업 중 오류가 "
                                "발생했습니다.\n\n"
                                f"{item[1]}"
                            ),
                            parent=self.root
                        )

        except queue.Empty:

            pass

        try:

            self.root.after(
                100,
                self.queue_처리
            )

        except tk.TclError:

            pass

    # ========================================================
    # 종료
    # ========================================================

    def 종료(
        self
    ):

        if self.closing:

            return

        if self.running:

            answer = messagebox.askyesno(
                APP_NAME,
                (
                    "현재 자간 조정 작업이 진행 중입니다.\n\n"
                    "종료하면 작업을 중단하고 "
                    "한글을 종료합니다.\n\n"
                    "종료하시겠습니까?"
                ),
                parent=self.root
            )

            if not answer:

                return

            self.closing = True

            중단_event.set()

            self.status_var.set(
                "프로그램 종료 처리 중..."
            )

            self.start_button.config(
                state="disabled"
            )

            self.stop_button.config(
                state="disabled"
            )

            self.select_button.config(
                state="disabled"
            )

            self.clear_button.config(
                state="disabled"
            )

            self.문장부호_checkbox.config(
                state="disabled"
            )

            self.worker_종료확인()

            return

        self.root.destroy()

    # ========================================================
    # Worker 종료 확인
    # ========================================================

    def worker_종료확인(
        self
    ):

        if (
            self.worker is not None
            and
            self.worker.is_alive()
        ):

            self.root.after(
                200,
                self.worker_종료확인
            )

            return

        self.root.destroy()


# ============================================================
# Main
# ============================================================

def main():

    root = TkinterDnD.Tk()

    HwpAutoDocFitGUI(
        root
    )

    root.mainloop()


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":

    main()
