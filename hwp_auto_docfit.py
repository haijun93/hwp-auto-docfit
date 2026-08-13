# -*- coding: utf-8 -*-

"""
============================================================
HWP Auto DocFit (with pyhwpx)
============================================================

한글 2020 이상 HWP / HWPX 자동 자간 맞춤 도구 (v4.1)

주요 기능
------------------------------------------------------------
1. pyhwpx 기반의 안정적이고 빠른 한글 OLE Automation
2. AutomationModule 보안모듈 자동 확인 및 설치
3. HWP / HWPX 다중 파일 및 폴더 Drag & Drop 지원
4. 중복 파일 자동 제거
5. 자동 줄바꿈 자간 조정 알고리즘 (LineFit)
6. 공문서 문장부호/번호 개조식 문장 자동 인식 및 2줄 압축
   (같은 문단 내 자동 줄바꿈으로 2번째 줄이 5자 이하인 경우)
7. 표 / 글상자(컨트롤) 내부 자동 탐색 및 자간 조정
8. 결과 파일 "(자간조정)" 접미사로 안전하게 자동 저장
9. 작업 진행률 표시바 및 실시간 상세 로그 제공
10. GUI 반응성을 위한 백그라운드 워커 스레드 처리
11. 실행 / 중단 / 종료 버튼 및 작업 취소 지원

필요 패키지
------------------------------------------------------------
pip install pyhwpx pywin32 tkinterdnd2
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
# GUI & Drag and Drop
# ============================================================

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilenames

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:
    print()
    print("=" * 60)
    print("tkinterdnd2가 설치되어 있지 않습니다.")
    print(f'설치 명령: "{sys.executable}" -m pip install tkinterdnd2')
    print("=" * 60)
    print()
    raise

# ============================================================
# 한글 Automation (pyhwpx / win32com)
# ============================================================

import pythoncom

try:
    from pyhwpx import Hwp
except ImportError:
    print()
    print("=" * 60)
    print("pyhwpx가 설치되어 있지 않습니다.")
    print(f'설치 명령: "{sys.executable}" -m pip install pyhwpx')
    print("=" * 60)
    print()
    # 런타임에 Hwp를 사용할 수 있도록 모듈 수준에서는 raise 처리
    raise

# ============================================================
# 프로그램 메타데이터
# ============================================================

APP_NAME = "HWP Auto DocFit"
APP_VERSION = "4.1"

# ============================================================
# AutomationModule 보안모듈 설정
# ============================================================

DLL_NAME = "FilePathCheckerModuleExample.dll"

HWP_AUTOMATION_DIR = Path(r"C:\HwpAutomation")
TARGET_DLL = HWP_AUTOMATION_DIR / DLL_NAME

REGISTRY_PATH = r"Software\HNC\HwpAutomation\Modules"
REGISTRY_VALUE_NAME = "AutomationModule"
REGISTER_MODULE_NAME = "FilePathCheckDLL"
REGISTER_MODULE_VALUE = "AutomationModule"

# ============================================================
# 자간 조정 기본 상수
# ============================================================

MAX_GENERAL_SPACING = 15      # 기존 알고리즘 최대 조정 횟수 (초과 시 롤백)
SHORT_LINE_MAX = 5           # 문장부호 2줄 문장의 2번째 줄 최대 글자 수 (공백 포함)
SPACING_DECREASE_COMMAND = "CharShapeSpacingDecrease"
SPACING_INCREASE_COMMAND = "CharShapeSpacingIncrease"

# ============================================================
# 공문서 문장 시작 기호 및 번호 패턴
# ============================================================

SENTENCE_MARKS = (
    "-", "－", "–", "—", "ㆍ", "·", "•", "∙", "‧",
    "○", "●", "◦", "◉", "◎", "□", "■", "▣", "▢",
    "◇", "◆", "△", "▲", "▽", "▼", "※", "▶", "▷",
    "◀", "◁", "→", "⇒", "↔", "☞", "☑", "✓", "✔",
    "★", "☆", "▪", "▫", "‣", "⁃", "⁌", "⁍",
)

HANGUL_OUTLINE_SYLLABLES = "가나다라마바사아자차카타파하"

NUMBER_MARK_PATTERN = re.compile(
    r"""
    ^
    (?:
        [0-9]{1,3}[.)]
        |
        \([0-9]{1,3}\)
        |
        [""" + HANGUL_OUTLINE_SYLLABLES + r"""][.)]
        |
        \([""" + HANGUL_OUTLINE_SYLLABLES + r"""]\)
        |
        [A-Za-z][.)]
        |
        \([A-Za-z]\)
        |
        [①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]
        |
        [㉠㉡㉢㉣㉤㉥㉦㉧㉨㉩㉪㉫㉬㉭㉮㉯㉰㉱㉲]
        |
        [ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.)]
    )
    (?=\s|$)
    """,
    re.VERBOSE,
)

# ============================================================
# 전역 상태 변수
# ============================================================

hwp = None
gui_queue = queue.Queue()
중단_event = threading.Event()
문장부호_옵션_사용 = True


# ============================================================
# 유틸리티 함수
# ============================================================

def 프로그램_폴더() -> Path:
    """실행 파일 또는 스크립트가 위치한 폴더 반환"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def 로그(message: str):
    """콘솔 및 GUI 큐로 로그 메시지 전송"""
    print(message)
    gui_queue.put(("log", str(message)))


def 상태(message: str):
    """GUI 상태 표시줄 텍스트 갱신"""
    gui_queue.put(("status", str(message)))


def 진행률(value: float):
    """GUI 진행률 바 갱신 (0~100)"""
    gui_queue.put(("progress", int(value)))


def 중단_요청됨() -> bool:
    """사용자의 작업 중단 요청 여부 확인"""
    return 중단_event.is_set()


# ============================================================
# 보안 모듈 설치 및 레지스트리 설정
# ============================================================

def 원본_DLL_찾기() -> Path | None:
    dll_path = 프로그램_폴더() / DLL_NAME
    if dll_path.is_file():
        return dll_path
    return None


def 등록된_DLL_경로() -> str | None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ,
        ) as key:
            value, value_type = winreg.QueryValueEx(key, REGISTRY_VALUE_NAME)
            if value_type == winreg.REG_SZ:
                return str(value)
    except (FileNotFoundError, OSError):
        pass
    return None


def 레지스트리_등록():
    HWP_AUTOMATION_DIR.mkdir(parents=True, exist_ok=True)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH) as key:
        winreg.SetValueEx(
            key,
            REGISTRY_VALUE_NAME,
            0,
            winreg.REG_SZ,
            str(TARGET_DLL),
        )
    로그("AutomationModule Registry 등록 완료")


def 보안모듈_초기화():
    """보안모듈 DLL 및 레지스트리 등록 상태를 확인하고 필요한 경우 자동 설정"""
    로그("AutomationModule 보안모듈 확인 시작")

    source_dll = 원본_DLL_찾기()
    if source_dll is None and not TARGET_DLL.is_file():
        raise FileNotFoundError(
            f"{DLL_NAME}을 찾을 수 없습니다.\n"
            f"위치: {프로그램_폴더() / DLL_NAME}\n"
            "DLL 파일을 프로그램 폴더에 배치해 주세요."
        )

    HWP_AUTOMATION_DIR.mkdir(parents=True, exist_ok=True)

    # DLL 복사 필요 여부 확인
    if source_dll and (not TARGET_DLL.is_file() or source_dll.stat().st_size != TARGET_DLL.stat().st_size):
        shutil.copy2(source_dll, TARGET_DLL)
        로그(f"DLL 복사 완료: {TARGET_DLL}")

    # 레지스트리 등록 여부 확인
    registered = 등록된_DLL_경로()
    if not registered or Path(registered).resolve() != TARGET_DLL.resolve():
        레지스트리_등록()
    else:
        로그("AutomationModule Registry 확인 완료")

    로그("AutomationModule 보안모듈 준비 완료")


# ============================================================
# 한글 인스턴스 시작 및 종료
# ============================================================

def 한글_시작():
    """pyhwpx Hwp 인스턴스를 생성하고 보안모듈을 등록하여 반환"""
    global hwp

    로그("한글 인스턴스 시작 중 (pyhwpx)...")
    pythoncom.CoInitialize()

    # pyhwpx Hwp 객체 생성
    hwp = Hwp(visible=True)

    # 보안 모듈 등록 (pyhwpx 내부 및 명시적 RegisterModule 지원)
    try:
        result = hwp.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE)
        로그(f"RegisterModule 등록 결과: {result}")
    except Exception as e:
        로그(f"RegisterModule 호출 알림: {e}")

    로그("한글 인스턴스 준비 완료")
    return hwp


# ============================================================
# 텍스트 검사 및 추출 유틸리티 (pyhwpx 기반)
# ============================================================

def 줄_텍스트_정리(text) -> str:
    """HWP 텍스트에서 줄바꿈 및 제어문자를 공백/정리된 형태로 변환"""
    if text is None:
        return ""
    text = str(text)
    text = text.replace("\r", "").replace("\n", "").replace("\t", " ")
    return text


def 줄_글자수(text) -> int:
    """공백을 포함한 문자 수 계산"""
    return len(줄_텍스트_정리(text))


def 문장부호_시작(text: str) -> bool:
    """텍스트가 공문서 항목 기호 또는 가나다/숫자 개조식 번호로 시작하는지 검사"""
    if not text:
        return False
    cleaned = str(text).lstrip(" \t")
    if not cleaned:
        return False

    if cleaned[0] in SENTENCE_MARKS:
        return True

    if NUMBER_MARK_PATTERN.match(cleaned):
        return True

    return False


def 현재선택영역_텍스트() -> str:
    """현재 블록 선택 영역의 텍스트 추출 (pyhwpx get_selected_text 활용)"""
    try:
        text = hwp.get_selected_text()
        return 줄_텍스트_정리(text) if text else ""
    except Exception:
        return ""


def 현재선택영역_글자수() -> int:
    """현재 블록 선택 영역의 글자수 반환"""
    return len(현재선택영역_텍스트())


def 현재줄_텍스트() -> str:
    """현재 커서가 위치한 줄 전체 텍스트 추출 후 커서 복귀"""
    original_pos = hwp.GetPos()
    try:
        hwp.Run("MoveLineBegin")
        hwp.Run("MoveSelLineEnd")
        text = 현재선택영역_텍스트()
        hwp.Run("Cancel")
        return text
    except Exception:
        return ""
    finally:
        try:
            hwp.SetPos(original_pos[0], original_pos[1], original_pos[2])
        except Exception:
            pass


def 같은_문단(pos_a, pos_b) -> bool:
    """두 위치가 같은 문단(문단 내 자동 줄바꿈)인지 판별"""
    return pos_a[0] == pos_b[0] and pos_a[1] == pos_b[1]


# ============================================================
# 자간 조정 핵심 알고리즘
# ============================================================

def 문장부호_2줄_자간조정() -> bool:
    """
    공문서 항목 기호 또는 번호로 시작하는 문장이 같은 문단 내 자동 줄바꿈으로
    2번째 줄에 5자 이하로 걸쳐있는 경우, 1줄이 될 때까지 자간을 축소 (-1%)
    """
    if not 문장부호_옵션_사용:
        return True

    if 중단_요청됨():
        return False

    original_pos = hwp.GetPos()

    try:
        # 문단 시작 줄 확인
        hwp.Run("MoveParaBegin")
        first_line_text = 현재줄_텍스트()

        if not first_line_text or not 문장부호_시작(first_line_text):
            return True

        adjustment_count = 0

        while True:
            if 중단_요청됨():
                return False

            if adjustment_count >= MAX_GENERAL_SPACING:
                로그("문장부호 문장: 자간조정 최대 횟수 도달")
                break

            current_pos = hwp.GetPos()

            # 첫 번째 줄 끝으로 이동 후 다음 글자로 넘어가 두 번째 줄 확인
            hwp.Run("MoveLineEnd")
            before_next = hwp.GetPos()
            hwp.Run("MoveNextChar")
            after_next = hwp.GetPos()

            if before_next == after_next:
                break  # 문서 끝

            if not 같은_문단(current_pos, after_next):
                break  # 실제 엔터로 구분된 다른 문단인 경우 제외

            second_line_text = 현재줄_텍스트()
            second_line_len = 줄_글자수(second_line_text)

            if second_line_len > SHORT_LINE_MAX or second_line_len == 0:
                break

            # 첫 줄 전체 선택 후 자간 -1%
            hwp.SetPos(current_pos[0], current_pos[1], current_pos[2])
            hwp.Run("MoveLineBegin")
            hwp.Run("MoveSelLineEnd")
            hwp.Run(SPACING_DECREASE_COMMAND)
            hwp.Run("Cancel")

            adjustment_count += 1
            로그(f"문장부호 2줄 문장: 두 번째 줄 {second_line_len}자 → 자간 -1% ({adjustment_count}회)")

            # 한 줄로 합쳐졌는지 확인
            hwp.SetPos(current_pos[0], current_pos[1], current_pos[2])
            hwp.Run("MoveLineEnd")
            hwp.Run("MoveNextChar")
            second_line_after = 현재줄_텍스트()

            if not second_line_after or 줄_글자수(second_line_after) > SHORT_LINE_MAX:
                break

            hwp.SetPos(current_pos[0], current_pos[1], current_pos[2])

        return True

    except Exception as e:
        로그(f"문장부호 문장 처리 중 알림: {e}")
        return True
    finally:
        try:
            hwp.Run("Cancel")
            hwp.SetPos(original_pos[0], original_pos[1], original_pos[2])
        except Exception:
            pass


def 자간자동조정() -> bool:
    """
    줄 끝에서 단어가 걸쳐 잘리는 경우:
    - 앞부분 글자수 >= 뒷부분 글자수 → 자간 -1%
    - 앞부분 글자수 < 뒷부분 글자수 → 자간 +1%
    15회 초과 시 원상복구(Undo)
    """
    count = 0

    while True:
        if 중단_요청됨():
            return False

        hwp.Run("MoveLineEnd")
        hwp.Run("MoveSelWordBegin")

        if count >= MAX_GENERAL_SPACING:
            로그("15회 이상 자간조정으로 원상복구")
            for _ in range(count):
                if 중단_요청됨():
                    return False
                hwp.Run("Undo")
            try:
                hwp.Run("Cancel")
            except Exception:
                pass
            return True

        앞부분길이 = 현재선택영역_글자수()
        if 앞부분길이 == 0:
            try:
                hwp.Run("Cancel")
            except Exception:
                pass
            return True

        hwp.Run("MoveSelWordEnd")
        뒷부분길이 = 현재선택영역_글자수()

        if not (앞부분길이 and 뒷부분길이):
            try:
                hwp.Run("Cancel")
                hwp.Run("Cancel")
            except Exception:
                pass
            return True

        hwp.Run("MoveWordBegin")
        hwp.Run("MoveLineEnd")
        hwp.Run("MoveSelLineBegin")

        if 앞부분길이 >= 뒷부분길이:
            hwp.Run(SPACING_DECREASE_COMMAND)
        else:
            hwp.Run(SPACING_INCREASE_COMMAND)

        count += 1
        hwp.Run("Cancel")


def 본문_자간조정() -> bool:
    """본문 처음부터 끝까지 순회하며 자간 조정 수행"""
    hwp.Run("MoveDocEnd")
    끝위치 = hwp.GetPos()
    hwp.Run("MoveDocBegin")

    while True:
        if 중단_요청됨():
            return False

        현재위치 = hwp.GetPos()
        if 현재위치 == 끝위치:
            break

        # 일반 자간 맞춤
        if 자간자동조정() is False:
            return False

        # 문장부호 2줄 맞춤
        if 문장부호_2줄_자간조정() is False:
            return False

        # 다음 줄 이동
        hwp.Run("MoveLineEnd")
        hwp.Run("MoveNextChar")

        새위치 = hwp.GetPos()
        if 새위치 == 현재위치:
            break

    return True


def 컨트롤_내부_자간조정() -> bool:
    """
    pyhwpx의 ctrl_list를 활용하여 표(tbl) 및 글상자(gso)를 누락 없이 순회하며
    컨트롤 내부 텍스트의 자간을 조정
    """
    try:
        # pyhwpx의 컨트롤 목록에서 표와 글상자 탐색
        controls = [
            c for c in hwp.ctrl_list
            if getattr(c, "UserDesc", "") in ("표", "글상자")
            or getattr(c, "CtrlID", "") in ("tbl", "gso")
        ]

        if controls:
            로그(f"표 및 글상자 컨트롤 {len(controls)}개 탐색 완료, 내부 처리 시작")

            for index, ctrl in enumerate(controls, 1):
                if 중단_요청됨():
                    return False
                try:
                    hwp.move_to_ctrl(ctrl)
                    # 표 내부 진입 후 자간 조정
                    hwp.Run("MoveDocBegin")
                except Exception as e:
                    로그(f"컨트롤 [{index}/{len(controls)}] 탐색 알림: {e}")

    except Exception as e:
        로그(f"pyhwpx ctrl_list 순회 알림: {e}")

    # 추가 안전망: sublist area 번호 순회 병행
    area = 1
    consecutive_empty = 0

    while area < 200:
        if 중단_요청됨():
            return False

        area += 1
        hwp.SetPos(area, 0, 0)
        pos = hwp.GetPos()

        if pos[0] == 0:
            consecutive_empty += 1
            if consecutive_empty > 5:
                break
            continue
        else:
            consecutive_empty = 0

        while True:
            if 중단_요청됨():
                return False

            시작위치 = hwp.GetPos()
            if 자간자동조정() is False:
                return False
            if 문장부호_2줄_자간조정() is False:
                return False

            hwp.Run("MoveLineEnd")
            hwp.Run("MoveNextChar")

            if hwp.GetPos() == 시작위치:
                break

    return True


# ============================================================
# 문서 입출력 및 전체 처리
# ============================================================

def 저장파일명(파일_경로: str) -> str:
    """결과 파일명을 항상 .hwpx 확장자로 생성"""
    path = Path(파일_경로)
    return str(path.with_name(f"{path.stem}(자간조정).hwpx"))


def 문서_닫기():
    """열린 문서를 대화상자 없이 안전하게 닫기"""
    global hwp
    if hwp is None:
        return
    try:
        hwp.clear(1)
    except Exception:
        try:
            hwp.Clear(1)
        except Exception:
            try:
                hwp.Run("FileClose")
            except Exception:
                pass


def 문서_처리(파일: str, index: int, total: int) -> bool:
    """단일 HWP/HWPX 문서 처리 및 HWPX 결과 저장"""
    global hwp

    if 중단_요청됨():
        return False

    파일명 = Path(파일).name
    상태(f"[{index}/{total}] {파일명} 처리 중...")
    로그("")
    로그(f"[{index}/{total}] {파일명}")

    확장자 = Path(파일).suffix.lower()
    if 확장자 not in (".hwp", ".hwpx"):
        raise ValueError(f"지원하지 않는 파일 형식: {파일}")

    # 기존 문서 닫기
    문서_닫기()

    # 문서 열기
    로그(f"문서 열기: {파일}")
    hwp.open(파일)

    # 본문 자간 조정
    상태(f"{파일명} : 본문 자간 조정 중")
    if 본문_자간조정() is False:
        return False

    # 표/글상자 내부 자간 조정
    상태(f"{파일명} : 표/글상자 자간 조정 중")
    if 컨트롤_내부_자간조정() is False:
        return False

    if 중단_요청됨():
        return False

    # 저장 (항상 HWPX 포맷으로 저장)
    저장파일 = 저장파일명(파일)
    상태(f"{파일명} : HWPX로 저장 중...")
    로그(f"HWPX 저장 시작: {저장파일}")
    hwp.save_as(저장파일, Format="HWPX")

    if not Path(저장파일).is_file():
        raise RuntimeError("결과 파일 생성 확인 실패")

    로그(f"저장 완료: {저장파일}")
    문서_닫기()
    return True


def 작업_실행(파일목록: list):
    """백그라운드 스레드에서 전체 문서 일괄 처리"""
    global hwp
    com_initialized = False

    try:
        total = len(파일목록)
        if total == 0:
            raise ValueError("처리할 문서가 없습니다.")

        중단_event.clear()

        # 보안모듈 준비
        상태("보안모듈 확인 중...")
        보안모듈_초기화()

        if 중단_요청됨():
            gui_queue.put(("stopped", None))
            return

        # 한글 시작
        상태("한글 2020 시작 중 (pyhwpx)...")
        한글_시작()
        com_initialized = True

        success_count = 0

        for index, 파일 in enumerate(파일목록, 1):
            if 중단_요청됨():
                break

            try:
                result = 문서_처리(파일, index, total)
                if result is False:
                    break
                success_count += 1
                진행률(index / total * 100)

            except Exception as e:
                traceback.print_exc()
                로그(f"문서 처리 실패: {파일} ({e})")
                gui_queue.put(("document_error", str(파일), str(e)))

        if 중단_요청됨():
            상태("작업 중단")
            gui_queue.put(("stopped", None))
        else:
            상태(f"모든 작업 완료 ({success_count}/{total})")
            gui_queue.put(("finished", success_count, total))

    except Exception as e:
        traceback.print_exc()
        gui_queue.put(("fatal_error", str(e)))

    finally:
        if hwp is not None:
            try:
                로그("한글 인스턴스 종료 중...")
                hwp.quit()
                로그("한글 인스턴스 종료 완료")
            except Exception as e:
                로그(f"한글 종료 알림: {e}")
            finally:
                hwp = None

        if com_initialized:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass


# ============================================================
# GUI 구현 (TkinterDnD 기반)
# ============================================================

class HwpAutoDocFitGUI:

    def __init__(self, root):
        self.root = root
        self.files = []
        self.worker = None
        self.running = False
        self.closing = False

        root.title(f"{APP_NAME} v{APP_VERSION} (pyhwpx)")
        root.geometry("540x480")
        root.minsize(450, 360)
        root.resizable(True, True)

        style = ttk.Style()
        try:
            style.theme_use("vista")
        except Exception:
            pass

        root.grid_rowconfigure(0, weight=0)
        root.grid_rowconfigure(1, weight=1)
        root.grid_rowconfigure(2, weight=0)
        root.grid_columnconfigure(0, weight=1)

        # Header
        header = ttk.Frame(root, padding=(12, 8, 12, 4))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text=f"{APP_NAME} v{APP_VERSION}",
            font=("맑은 고딕", 13, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            header,
            text="한글 2020+ HWP / HWPX 자동 자간 맞춤 도구 (pyhwpx 기반)",
            font=("맑은 고딕", 9),
        ).grid(row=1, column=0, sticky="w")

        # Main
        main_frame = ttk.Frame(root, padding=(12, 0, 12, 0))
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=3)
        main_frame.grid_rowconfigure(1, weight=0)
        main_frame.grid_rowconfigure(2, weight=0)
        main_frame.grid_rowconfigure(3, weight=2)
        main_frame.grid_columnconfigure(0, weight=1)

        # File Drop Frame
        file_frame = ttk.LabelFrame(main_frame, text="문서 선택 (Drag & Drop)", padding=6)
        file_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        file_frame.grid_rowconfigure(1, weight=1)
        file_frame.grid_columnconfigure(0, weight=1)

        self.drop_label = ttk.Label(
            file_frame,
            text="HWP / HWPX 파일 또는 폴더를 여기로 끌어다 놓으세요",
            anchor="center",
            justify="center",
        )
        self.drop_label.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.파일_드롭)

        # File List
        list_frame = ttk.Frame(file_frame)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        list_scroll = ttk.Scrollbar(list_frame, orient="vertical")
        list_scroll.grid(row=0, column=1, sticky="ns")

        self.file_list = tk.Listbox(
            list_frame,
            font=("맑은 고딕", 9),
            yscrollcommand=list_scroll.set,
            selectmode=tk.EXTENDED,
            borderwidth=1,
        )
        self.file_list.grid(row=0, column=0, sticky="nsew")
        list_scroll.config(command=self.file_list.yview)

        self.file_list.drop_target_register(DND_FILES)
        self.file_list.dnd_bind("<<Drop>>", self.파일_드롭)
        file_frame.drop_target_register(DND_FILES)
        file_frame.dnd_bind("<<Drop>>", self.파일_드롭)

        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        options_frame.grid_columnconfigure(0, weight=1)

        self.문장부호_var = tk.BooleanVar(value=True)
        self.문장부호_checkbox = ttk.Checkbutton(
            options_frame,
            text="공문서 문장부호/번호 2번째 줄(5자 이하) 자동 자간 축소",
            variable=self.문장부호_var,
        )
        self.문장부호_checkbox.grid(row=0, column=0, sticky="w")

        # Status & Progress
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="HWP/HWPX 파일 또는 폴더를 선택하세요.")
        ttk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

        self.progress = ttk.Progressbar(
            status_frame,
            orient="horizontal",
            mode="determinate",
            maximum=100,
        )
        self.progress.grid(row=1, column=0, sticky="ew", pady=(3, 0))

        # Log
        log_frame = ttk.LabelFrame(main_frame, text="작업 로그", padding=4)
        log_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 4))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        log_scroll = ttk.Scrollbar(log_frame, orient="vertical")
        log_scroll.grid(row=0, column=1, sticky="ns")

        self.log_text = tk.Listbox(
            log_frame,
            font=("맑은 고딕", 8),
            yscrollcommand=log_scroll.set,
            borderwidth=1,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll.config(command=self.log_text.yview)

        # Buttons
        self.button_frame = ttk.Frame(root, padding=(12, 4, 12, 8))
        self.button_frame.grid(row=2, column=0, sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)

        left_buttons = ttk.Frame(self.button_frame)
        left_buttons.grid(row=0, column=0, sticky="w")

        self.select_button = ttk.Button(
            left_buttons,
            text="파일 선택",
            command=self.파일선택,
            width=9,
        )
        self.select_button.pack(side="left")

        self.clear_button = ttk.Button(
            left_buttons,
            text="목록 지우기",
            command=self.목록지우기,
            width=11,
        )
        self.clear_button.pack(side="left", padx=(4, 0))

        action_buttons = ttk.Frame(self.button_frame)
        action_buttons.grid(row=0, column=1, sticky="e")

        self.start_button = ttk.Button(
            action_buttons,
            text="▶ 실행",
            command=self.작업시작,
            width=9,
        )
        self.start_button.pack(side="left", padx=2)

        self.stop_button = ttk.Button(
            action_buttons,
            text="■ 중단",
            command=self.작업중단,
            width=9,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=2)

        self.exit_button = ttk.Button(
            action_buttons,
            text="✕ 종료",
            command=self.종료,
            width=9,
        )
        self.exit_button.pack(side="left", padx=2)

        # Queue Polling & WM_DELETE
        root.after(100, self.queue_처리)
        root.protocol("WM_DELETE_WINDOW", self.종료)

    def 로그표시(self, message):
        self.log_text.insert(tk.END, str(message))
        self.log_text.see(tk.END)

    def 파일추가(self, file_path) -> bool:
        try:
            file_path = str(Path(file_path).resolve())
        except Exception:
            return False

        if not os.path.isfile(file_path):
            return False

        if Path(file_path).suffix.lower() not in (".hwp", ".hwpx"):
            return False

        if file_path in self.files:
            return False

        self.files.append(file_path)
        self.file_list.insert(tk.END, file_path)
        return True

    def 폴더추가(self, folder_path) -> int:
        folder = Path(folder_path)
        if not folder.is_dir():
            return 0

        count = 0
        try:
            items = sorted(folder.iterdir(), key=lambda p: p.name.lower())
            for path in items:
                if path.is_file() and path.suffix.lower() in (".hwp", ".hwpx"):
                    if self.파일추가(path):
                        count += 1
        except Exception:
            pass
        return count

    def 파일_드롭(self, event):
        if self.running:
            return

        try:
            items = self.root.tk.splitlist(event.data)
        except Exception:
            items = [event.data]

        added = 0
        for item in items:
            item_str = str(item).strip("{}").strip()
            if os.path.isdir(item_str):
                added += self.폴더추가(item_str)
            elif os.path.isfile(item_str):
                if self.파일추가(item_str):
                    added += 1

        if added:
            self.status_var.set(f"{len(self.files)}개 문서 선택됨")
            self.로그표시(f"{added}개 문서 추가됨")

    def 파일선택(self):
        if self.running:
            return

        files = askopenfilenames(
            parent=self.root,
            title="자간을 조정할 HWP/HWPX 문서를 선택하세요.",
            initialdir=os.getcwd(),
            filetypes=[
                ("한/글 파일", "*.hwp *.hwpx"),
                ("HWP 파일", "*.hwp"),
                ("HWPX 파일", "*.hwpx"),
            ],
        )

        if not files:
            return

        added = 0
        for file in files:
            if self.파일추가(file):
                added += 1

        self.status_var.set(f"{len(self.files)}개 문서 선택됨")
        if added:
            self.로그표시(f"{added}개 문서 추가됨")

    def 목록지우기(self):
        if self.running:
            return
        self.files.clear()
        self.file_list.delete(0, tk.END)
        self.progress["value"] = 0
        self.status_var.set("HWP/HWPX 파일 또는 폴더를 선택하세요.")

    def 작업시작(self):
        if self.running:
            return

        if not self.files:
            messagebox.showwarning(
                APP_NAME,
                "먼저 HWP/HWPX 문서를 선택하거나 끌어다 놓으세요.",
                parent=self.root,
            )
            return

        global 문장부호_옵션_사용
        문장부호_옵션_사용 = self.문장부호_var.get()

        self.running = True
        self.closing = False
        중단_event.clear()

        self.progress["value"] = 0
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.select_button.config(state="disabled")
        self.clear_button.config(state="disabled")
        self.문장부호_checkbox.config(state="disabled")

        self.로그표시("")
        self.로그표시("=" * 50)
        self.로그표시(f"{APP_NAME} 작업 시작 (처리 문서: {len(self.files)}개)")
        self.로그표시("=" * 50)

        self.worker = threading.Thread(
            target=작업_실행,
            args=(list(self.files),),
            daemon=True,
        )
        self.worker.start()

    def 작업중단(self):
        if not self.running:
            return

        answer = messagebox.askyesno(
            APP_NAME,
            "현재 자간 조정 작업이 진행 중입니다.\n\n작업을 중단하시겠습니까?",
            parent=self.root,
        )
        if not answer:
            return

        중단_event.set()
        self.stop_button.config(state="disabled")
        self.status_var.set("작업 중단 처리 중...")
        self.로그표시("사용자가 작업 중단을 요청했습니다.")

    def queue_처리(self):
        try:
            while True:
                item = gui_queue.get_nowait()
                event = item[0]

                if event == "log":
                    self.로그표시(item[1])
                elif event == "status":
                    self.status_var.set(item[1])
                elif event == "progress":
                    self.progress["value"] = item[1]
                elif event == "document_error":
                    self.로그표시(f"문서 처리 실패: {item[1]}")
                    self.로그표시(item[2])
                elif event == "stopped":
                    self.running = False
                    self.start_button.config(state="normal")
                    self.stop_button.config(state="disabled")
                    self.select_button.config(state="normal")
                    self.clear_button.config(state="normal")
                    self.문장부호_checkbox.config(state="normal")
                    self.status_var.set("작업 중단됨")
                    if not self.closing:
                        messagebox.showinfo(
                            APP_NAME,
                            "자간 조정 작업이 중단되었습니다.",
                            parent=self.root,
                        )
                elif event == "finished":
                    self.running = False
                    self.progress["value"] = 100
                    self.start_button.config(state="normal")
                    self.stop_button.config(state="disabled")
                    self.select_button.config(state="normal")
                    self.clear_button.config(state="normal")
                    self.문장부호_checkbox.config(state="normal")
                    success_count, total = item[1], item[2]
                    self.status_var.set(f"작업 완료 ({success_count}/{total})")
                    if not self.closing:
                        messagebox.showinfo(
                            APP_NAME,
                            f"자간 조정이 완료되었습니다.\n\n"
                            f"정상 처리: {success_count}/{total}\n\n"
                            f"'(자간조정)' 결과 파일이 생성되었습니다.",
                            parent=self.root,
                        )
                elif event == "fatal_error":
                    self.running = False
                    self.start_button.config(state="normal")
                    self.stop_button.config(state="disabled")
                    self.select_button.config(state="normal")
                    self.clear_button.config(state="normal")
                    self.문장부호_checkbox.config(state="normal")
                    self.status_var.set("오류 발생")
                    if not self.closing:
                        messagebox.showerror(
                            APP_NAME,
                            f"작업 중 오류가 발생했습니다.\n\n{item[1]}",
                            parent=self.root,
                        )
        except queue.Empty:
            pass

        try:
            self.root.after(100, self.queue_처리)
        except tk.TclError:
            pass

    def 종료(self):
        if self.closing:
            return

        if self.running:
            answer = messagebox.askyesno(
                APP_NAME,
                "현재 자간 조정 작업이 진행 중입니다.\n\n종료하시겠습니까?",
                parent=self.root,
            )
            if not answer:
                return

            self.closing = True
            중단_event.set()
            self.status_var.set("프로그램 종료 처리 중...")
            self.worker_종료확인()
            return

        self.root.destroy()

    def worker_종료확인(self):
        if self.worker is not None and self.worker.is_alive():
            self.root.after(200, self.worker_종료확인)
            return
        self.root.destroy()


# ============================================================
# CLI 및 메인 엔트리포인트
# ============================================================

def cli_main(files: list[str]):
    """CLI 환경에서 일괄 문서 처리 및 분석 통계 리포트 출력"""
    print("=" * 70)
    print(f"{APP_NAME} v{APP_VERSION} (CLI 모드)")
    print("=" * 70)

    try:
        from mcp_server import tool_analyze_hwp_document
    except ImportError:
        tool_analyze_hwp_document = None

    valid_files = [f for f in files if os.path.isfile(f)]
    if not valid_files:
        print("처리할 파일이 없습니다.")
        return

    for idx, f in enumerate(valid_files, 1):
        print(f"\n[{idx}/{len(valid_files)}] 문서 분석 및 자간 맞춤: {f}")
        if tool_analyze_hwp_document:
            analysis = tool_analyze_hwp_document({"file_path": f})
            print(f"  • 총 문단 수: {analysis.get('total_paragraphs', 0)}개")
            print(f"  • 공문서 기호/번호 문장: {analysis.get('sentence_mark_paragraphs_count', 0)}개")
            print(f"  • 2줄 압축 대상 문단: {analysis.get('two_line_compression_candidates_count', 0)}개 (예상 {analysis.get('estimated_lines_saved', 0)}줄 절감)")

        out_path = 저장파일명(f)
        print(f"  • HWPX 결과 저장 예정: {out_path}")

    # 실제 한글 환경일 경우 일괄 실행
    try:
        작업_실행(valid_files)
    except Exception as e:
        print(f"실행 알림: {e}")


def main():
    args = sys.argv[1:]

    # 1. MCP 서버 모드
    if "--mcp" in args:
        try:
            import mcp_server
            mcp_server.main()
        except Exception as e:
            print(f"MCP 서버 실행 오류: {e}", file=sys.stderr)
        return

    # 2. CLI 파일 인자 전달 모드
    if args and not args[0].startswith("-"):
        cli_main(args)
        return

    # 3. 기본 GUI 모드
    root = TkinterDnD.Tk()
    HwpAutoDocFitGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
