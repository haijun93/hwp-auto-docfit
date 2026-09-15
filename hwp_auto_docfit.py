# -*- coding: utf-8 -*-

"""
============================================================
hwp 자동 편집기
============================================================

한글 2020 HWP / HWPX 자동 자간 조정 프로그램

주요 기능
------------------------------------------------------------
1. HWPFrame.HwpObject COM 자동화
2. AutomationModule 보안모듈 등록
3. FilePathCheckerModuleExample.dll 최초 1회 설치
4. Registry AutomationModule 최초 1회 등록
5. HWP / HWPX 다중 선택
6. Drag & Drop
7. 폴더 Drag & Drop
8. 중복 파일 자동 제거
9. 기존 자간 자동조정 알고리즘(줄 끝 단어분리 방지)
10. 문장부호/공문서 항목 자동 인식(계층형 번호 2-7. 포함)
11. 문장부호 시작 문장 줄병합 자간축소
    (2줄 이상, 마지막 줄이 지정 글자수 이하일 때)
12. 실제 Enter 문장은 문장부호 기능에서 제외
13. 표/글상자/각주/미주 등 컨트롤 처리
14. 보고서 표준서식 적용(여백/장평/줄간격/기호별 폰트)
15. 자간조정 부분 글자색 표시(빨강/파랑)
16. 원본·결과 좌우 비교 보기(창 임베드)
17. 자간조정 결과 검수(미해결 문단 자동 점검)
18. "(자간조정)"으로 저장
19. 설정 창 + 설정값 영구 저장(%APPDATA%)
20. 실행 / 중단 / 종료, 작업 진행률, 작업 로그(복사 가능)
21. GUI / HWP 작업 스레드 분리
22. 문두 라벨(괄호 및 콜론 라벨) 굵게 처리 및 서식 토글 연동
23. 문장부호 세트문장 동일 페이지 유지(시작 페이지 줄간격 자동 축소)
24. 표준서식 기호 우선 판정(첫 문단 제목 오인 방지)
25. 세트 후속 범위 괄호 라벨 축소 제외
26. 세트 후속문단 상위 기호 서식 상속
27. 붙임 괄호 줄분리 우선 자간축소
28. 표 컨트롤/셀 직접 순회 서식 적용
29. 괄호 안쪽 불필요 공백 자동 제거 (( 내용 ) → (내용))
30. 전체 편집 파이프라인 2회 반복 처리
31. 화면줄 경계 어절 분리 우선 자간축소 (예: 제공하 | 며,)

필요 패키지
------------------------------------------------------------
python -m pip install pywin32 tkinterdnd2
============================================================
"""

import os
import sys
import shutil
import winreg
import threading
import queue
import traceback
import re
import time
import unicodedata
import json
import copy
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilenames, askopenfilename

from tkinterdnd2 import TkinterDnD, DND_FILES

import pythoncom
import win32com.client as win32
import win32gui
import win32con

# ============================================================
# 프로그램 정보
# ============================================================

APP_NAME = "hwp 자동 편집기"
APP_VERSION = "1.11"

# ============================================================
# AutomationModule
# ============================================================

DLL_NAME = "FilePathCheckerModuleExample.dll"
HWP_AUTOMATION_DIR = Path(r"C:\HwpAutomation")
TARGET_DLL = HWP_AUTOMATION_DIR / DLL_NAME
REGISTRY_PATH = r"Software\HNC\HwpAutomation\Modules"
REGISTRY_VALUE_NAME = "AutomationModule"
REGISTER_MODULE_NAME = "FilePathCheckDLL"
REGISTER_MODULE_VALUE = "FilePathCheckerModule"

# ============================================================
# 전역 상태
# ============================================================

hwp = None
gui_queue = queue.Queue()
_콘솔_출력_가능 = (sys.stdout is not None)
로그_최대_줄수 = 3000

중단_event = threading.Event()
색상_설정 = None
비교보기_사용 = False
원본_hwp = None
비교보기_좌측_프레임_hwnd = None
비교보기_우측_프레임_hwnd = None
원본_hwp_hwnd = None
작업_hwp_hwnd = None
자동닫기_설정 = True

# ============================================================
# 보고서 표준서식 기본값
# ============================================================

표준서식_사용 = False

표준서식_여백_사용 = True
표준서식_장평_사용 = True
표준서식_줄간격_사용 = True
표준서식_제목_사용 = True
표준서식_일자담당자_사용 = True
표준서식_기호_사용 = True

표준서식_제목_굵게 = True
표준서식_일자담당자_굵게 = True

표준서식_기호_굵게 = {
    "□": True,
    "ㅇ": True,
    "-": False,
    "※": False,
}

표준서식_문단위간격_사용 = True
표준서식_문단위간격_box_pt = 15
표준서식_문단위간격_circle_pt = 10
표준서식_문단위간격_note_pt = 3

표_헤더서식_사용 = True
표_헤더서식_헤더_폰트 = "한컴돋움"
표_헤더서식_헤더_크기 = 13
표_헤더서식_헤더_굵게 = True
표_헤더서식_본문_폰트 = "휴먼명조"
표_헤더서식_본문_크기 = 12
표_헤더서식_본문_굵게 = False

표준서식_설정 = {
    "여백_mm": {
        "left": 18,
        "right": 18,
        "top": 12.7,
        "bottom": 12.7,
        "header": 12.7,
        "footer": 12.7,
    },
    "기본_장평": 100,
    "기본_자간": 0,
    "기본_줄간격_퍼센트": 160,
    "제목_문단": {
        "font": "HY헤드라인M",
        "size_pt": 27,
        "bold": True,
    },
    "일자담당자_문단": {
        "font": "한컴돋움",
        "size_pt": 15,
        "bold": True,
    },
    "기호_규칙": [
        ("□", 0, "HY견고딕", 17, False, True),
        ("ㅇ", 1, "한컴돋움", 15, True, False),
        ("-", 3, "휴먼명조", 14, False, False),
        ("※", 5, "한컴돋움", 13, False, False),
    ],
}

_표준서식_설정_기본값 = copy.deepcopy(표준서식_설정)
_표_헤더서식_기본값 = {
    "헤더_폰트": 표_헤더서식_헤더_폰트,
    "헤더_크기": 표_헤더서식_헤더_크기,
    "헤더_굵게": 표_헤더서식_헤더_굵게,
    "본문_폰트": 표_헤더서식_본문_폰트,
    "본문_크기": 표_헤더서식_본문_크기,
    "본문_굵게": 표_헤더서식_본문_굵게,
}
_표준서식_문단위간격_기본값 = {
    "box": 표준서식_문단위간격_box_pt,
    "circle": 표준서식_문단위간격_circle_pt,
    "note": 표준서식_문단위간격_note_pt,
}

def 표준서식_문단위간격_찾기(text):
    if not text:
        return None
    벗긴텍스트 = text.lstrip()
    if not 벗긴텍스트:
        return None
    첫글자 = 벗긴텍스트[0]
    if 첫글자 == "□":
        return 표준서식_문단위간격_box_pt
    if 첫글자 in ("ㅇ", "○", "☞"):
        return 표준서식_문단위간격_circle_pt
    if 첫글자 in ("*", "※", "→"):
        return 표준서식_문단위간격_note_pt
    return None

def 서식_기본값_전역_복원():
    global 표준서식_설정
    global 표_헤더서식_헤더_폰트, 표_헤더서식_헤더_크기, 표_헤더서식_헤더_굵게
    global 표_헤더서식_본문_폰트, 표_헤더서식_본문_크기, 표_헤더서식_본문_굵게
    global 표준서식_문단위간격_box_pt, 표준서식_문단위간격_circle_pt, 표준서식_문단위간격_note_pt

    표준서식_설정 = copy.deepcopy(_표준서식_설정_기본값)
    표_헤더서식_헤더_폰트 = _표_헤더서식_기본값["헤더_폰트"]
    표_헤더서식_헤더_크기 = _표_헤더서식_기본값["헤더_크기"]
    표_헤더서식_헤더_굵게 = _표_헤더서식_기본값["헤더_굵게"]
    표_헤더서식_본문_폰트 = _표_헤더서식_기본값["본문_폰트"]
    표_헤더서식_본문_크기 = _표_헤더서식_기본값["본문_크기"]
    표_헤더서식_본문_굵게 = _표_헤더서식_기본값["본문_굵게"]
    표준서식_문단위간격_box_pt = _표준서식_문단위간격_기본값["box"]
    표준서식_문단위간격_circle_pt = _표준서식_문단위간격_기본값["circle"]
    표준서식_문단위간격_note_pt = _표준서식_문단위간격_기본값["note"]

검수_사용 = False
검수_문제목록 = []
현재_처리파일 = None
문장부호_2줄_기준글자수 = 5
자간_최대시도_본문 = 30
자간_최대시도_표 = 5

# 문장부호로 시작하는 "세트문장"이 페이지 경계에서 갈라질 때
# 해당 세트의 시작 페이지 전체 줄간격을 10%씩 축소하여 한 페이지 안에 모은다.
세트문장_같은쪽_사용 = True
세트문장_페이지줄간격_최대시도 = 6
세트문장_최소줄간격_퍼센트 = 100

문장부호_통계 = {"대상": 0, "성공": 0, "실패": 0}
세트문장_통계 = {"대상": 0, "성공": 0, "실패": 0, "축소횟수": 0}

def 프로그램_폴더():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

def 번들_리소스_폴더():
    meipass = getattr(sys, "_MEIPASS", None)
    return Path(meipass) if meipass else None

# ============================================================
# 사용자 설정 저장/불러오기
# ============================================================

설정_파일명 = "settings.json"

기본_설정 = {
    "punctuation": True,
    "punctuation_threshold": "5",
    "keep_punctuation_set_together": True,
    "color_mark_on": False,
    "color": "red",
    "autoclose": False,
    "stdformat": False,
    "verify": False,
    "retry_body": "30",
    "retry_table": "5",
    "paren_shrink": True,
    "paren_label_bold": True,
    "std_margin": True,
    "std_ratio": True,
    "std_linespacing": True,
    "std_title": True,
    "std_title_bold": True,
    "std_dateinfo": True,
    "std_dateinfo_bold": True,
    "std_symbols": True,
    "std_symbol_box_bold": True,
    "std_symbol_o_bold": True,
    "std_symbol_dash_bold": False,
    "std_symbol_note_bold": False,
    "std_parspace": True,
    "std_parspace_box": "15",
    "std_parspace_circle": "10",
    "std_parspace_note": "3",
    "std_table_header": True,
    "active_format_profile": "",
}

def 설정_폴더():
    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    if appdata:
        return Path(appdata) / "HwpAutoDocFit"
    return Path.home() / ".hwp_auto_docfit"

def 서식프로파일_폴더():
    return 설정_폴더() / "formats"

def 설정_파일_경로():
    return 설정_폴더() / 설정_파일명

def 설정_불러오기():
    설정 = dict(기본_설정)
    try:
        경로 = 설정_파일_경로()
        if not 경로.is_file():
            return 설정
        with open(경로, "r", encoding="utf-8") as f:
            저장된값 = json.load(f)
        if isinstance(저장된값, dict):
            for 키 in 기본_설정:
                if 키 in 저장된값:
                    설정[키] = 저장된값[키]
    except Exception as e:
        print(f"설정 불러오기 실패(기본값 사용): {e}")
    return 설정

def 설정_저장(설정):
    try:
        폴더 = 설정_폴더()
        폴더.mkdir(parents=True, exist_ok=True)
        with open(설정_파일_경로(), "w", encoding="utf-8") as f:
            json.dump(설정, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"설정 저장 실패(무시): {e}")
        return False

# ============================================================
# GUI 메시지
# ============================================================

def 로그(message):
    if _콘솔_출력_가능:
        try:
            print(message)
        except Exception:
            pass
    gui_queue.put(("log", str(message)))

def 진단로그(message):
    if 검수_사용:
        로그(message)

def 상태(message):
    gui_queue.put(("status", str(message)))

def 진행률(value):
    gui_queue.put(("progress", int(max(0, min(100, value)))))

def 중단_요청됨():
    return 중단_event.is_set()

def hwp_run(command):
    if hwp is None:
        raise RuntimeError("HWP 객체가 없습니다.")
    try:
        return hwp.Run(command)
    except Exception as e:
        로그(f"HWP 명령 실패: {command} / {e}")
        raise

# ============================================================
# 보안 모듈
# ============================================================

def 원본_DLL_찾기():
    후보_목록 = [프로그램_폴더() / DLL_NAME]
    번들_폴더 = 번들_리소스_폴더()
    if 번들_폴더 is not None:
        후보_목록.append(번들_폴더 / DLL_NAME)
    for dll_path in 후보_목록:
        로그(f"DLL 확인: {dll_path}")
        if dll_path.is_file():
            return dll_path
    return None

def 등록된_DLL_경로():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_READ) as key:
            value, value_type = winreg.QueryValueEx(key, REGISTRY_VALUE_NAME)
            if value_type == winreg.REG_SZ:
                return str(value)
    except (FileNotFoundError, OSError):
        pass
    return None

def 레지스트리_등록():
    HWP_AUTOMATION_DIR.mkdir(parents=True, exist_ok=True)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH) as key:
        winreg.SetValueEx(key, REGISTRY_VALUE_NAME, 0, winreg.REG_SZ, str(TARGET_DLL))
    로그("AutomationModule Registry 등록 완료")

def 보안모듈_초기화():
    로그("AutomationModule 확인 시작")
    source_dll = 원본_DLL_찾기()
    if source_dll is None:
        raise FileNotFoundError(
            f"\n\nFilePathCheckerModuleExample.dll을 프로그램 폴더에서 찾을 수 없습니다.\n"
            f"위치: {프로그램_폴더() / DLL_NAME}"
        )
    HWP_AUTOMATION_DIR.mkdir(parents=True, exist_ok=True)
    if not TARGET_DLL.is_file():
        로그("AutomationModule DLL 최초 설치")
        shutil.copy2(source_dll, TARGET_DLL)
        로그(f"DLL 복사 완료: {TARGET_DLL}")
    else:
        로그("C:\\HwpAutomation DLL 확인 완료")

    registered_path = 등록된_DLL_경로()
    target_path = TARGET_DLL.resolve()
    registered_normalized = None
    if registered_path:
        try:
            registered_normalized = Path(registered_path).resolve()
        except Exception:
            registered_normalized = Path(registered_path)

    if registered_normalized != target_path:
        로그("AutomationModule Registry 등록 필요")
        레지스트리_등록()
    else:
        로그("AutomationModule Registry 확인 완료")
    로그("AutomationModule 초기화 완료")

# ============================================================
# 한글 시작
# ============================================================

def 한글_시작():
    global hwp
    로그("한글 2020 시작 중...")
    pythoncom.CoInitialize()

    이전_창목록 = _표시중인_최상위창_목록() if 비교보기_사용 else None

    hwp = win32.Dispatch("HwpFrame.HwpObject")
    hwp.XHwpWindows.Item(0).Visible = True
    로그("한글 창 표시 성공")

    result = hwp.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE)
    로그(f"RegisterModule 결과: {result}")
    if not result:
        raise RuntimeError("RegisterModule 등록에 실패했습니다.")

    if 비교보기_사용 and 이전_창목록 is not None:
        작업창_임베드(이전_창목록)

    로그("한글 2020 시작 완료")
    return hwp

def 현재선택영역_글자수():
    hwp.InitScan(option=None, Range=0xff, spara=None, spos=None, epara=None, epos=None)
    try:
        _, text = hwp.GetText()
        return len(text)
    finally:
        hwp.ReleaseScan()

def 현재선택영역_텍스트():
    try:
        hwp.InitScan(option=None, Range=0xff, spara=None, spos=None, epara=None, epos=None)
        try:
            _, text = hwp.GetText()
            return text or ""
        finally:
            hwp.ReleaseScan()
    except Exception:
        return ""

COLOR_OPTIONS = [
    ("red",     "빨강",     (255, 0, 0)),
    ("orange",  "주황",     (255, 128, 0)),
    ("green",   "초록",     (0, 153, 0)),
    ("blue",    "파랑",     (0, 0, 255)),
    ("skyblue", "하늘",     (0, 153, 255)),
    ("purple",  "보라",     (128, 0, 192)),
    ("magenta", "자홍",     (224, 0, 160)),
    ("brown",   "갈색",     (140, 70, 20)),
    ("gray",    "회색",     (128, 128, 128)),
]

COLOR_MAP = {키: rgb for 키, _, rgb in COLOR_OPTIONS}

def 색상_미리보기_hex(rgb):
    if not rgb:
        return "#808080"
    return "#{:02X}{:02X}{:02X}".format(*rgb)

def 색상_적용_현재선택():
    if 색상_설정 is None or hwp is None:
        return
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HCharShape
        act.GetDefault("CharShape", pset.HSet)
        pset.TextColor = hwp.RGBColor(*색상_설정)
        act.Execute("CharShape", pset.HSet)
    except Exception as e:
        로그(f"자간조정 글자색 적용 실패: {e}")

# ============================================================
# 비교 보기 (창 임베드)
# ============================================================

def _표시중인_최상위창_목록():
    결과 = []
    def 콜백(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            if win32gui.GetParent(hwnd) != 0:
                return True
            결과.append(hwnd)
        except Exception:
            pass
        return True
    try:
        win32gui.EnumWindows(콜백, None)
    except Exception:
        pass
    return set(결과)

def 새_한글창_찾기(이전_창목록, 제한시간=10.0):
    시작시각 = time.time()
    while time.time() - 시작시각 < 제한시간:
        현재_창목록 = _표시중인_최상위창_목록()
        신규 = 현재_창목록 - 이전_창목록
        if 신규:
            후보 = list(신규)
            for h in 후보:
                try:
                    클래스명 = win32gui.GetClassName(h)
                except Exception:
                    클래스명 = ""
                if "hwp" in 클래스명.lower():
                    return h
            return 후보[0]
        time.sleep(0.15)
    return None

def 창_임베드(hwnd, 부모_hwnd):
    if not hwnd or not 부모_hwnd:
        return False
    try:
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        style &= ~(win32con.WS_POPUP | win32con.WS_CAPTION | win32con.WS_THICKFRAME |
                   win32con.WS_SYSMENU | win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX)
        style |= win32con.WS_CHILD
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
        win32gui.SetParent(hwnd, 부모_hwnd)
        win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                              win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
        창_임베드_크기조정(hwnd, 부모_hwnd)
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        return True
    except Exception as e:
        로그(f"창 임베드 실패: {e}")
        return False

def 창_임베드_크기조정(hwnd, 부모_hwnd):
    if not hwnd or not 부모_hwnd:
        return
    try:
        left, top, right, bottom = win32gui.GetClientRect(부모_hwnd)
        win32gui.MoveWindow(hwnd, 0, 0, max(right - left, 1), max(bottom - top, 1), True)
    except Exception:
        pass

def 창_임베드_해제(hwnd):
    if not hwnd:
        return
    try:
        win32gui.SetParent(hwnd, 0)
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        style &= ~win32con.WS_CHILD
        style |= (win32con.WS_POPUP | win32con.WS_CAPTION | win32con.WS_THICKFRAME |
                  win32con.WS_SYSMENU | win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX)
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
        win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                              win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
    except Exception as e:
        로그(f"창 임베드 해제 실패(무시): {e}")

def 원본_뷰어_시작():
    global 원본_hwp, 원본_hwp_hwnd, 비교보기_사용
    if not 비교보기_사용 or not 비교보기_좌측_프레임_hwnd or 원본_hwp is not None:
        return

    로그("비교 보기용 원본 창 시작 중...")
    이전_창목록 = _표시중인_최상위창_목록()

    for 시도 in range(1, 4):
        try:
            원본_hwp = win32.Dispatch("HwpFrame.HwpObject")
            원본_hwp.XHwpWindows.Item(0).Visible = True
            break
        except Exception as e:
            원본_hwp = None
            로그(f"비교 보기용 원본 창 시작 실패 ({시도}/3): {e}")
            if 시도 < 3:
                time.sleep(1.5)

    if 원본_hwp is None:
        로그("비교 보기용 원본 창을 띄우지 못해 비교 보기 없이 진행합니다.")
        비교보기_사용 = False
        return

    try:
        원본_hwp.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE)
    except Exception as e:
        로그(f"원본 창 RegisterModule 실패(무시): {e}")

    try:
        원본_hwp_hwnd = 새_한글창_찾기(이전_창목록)
        if 원본_hwp_hwnd:
            창_임베드(원본_hwp_hwnd, 비교보기_좌측_프레임_hwnd)
    except Exception as e:
        로그(f"원본 창 임베드 실패(무시): {e}")

    로그("비교 보기용 원본 창 시작 완료")

def 작업창_임베드(이전_창목록):
    global 작업_hwp_hwnd
    if not 비교보기_사용 or not 비교보기_우측_프레임_hwnd:
        return
    작업_hwp_hwnd = 새_한글창_찾기(이전_창목록)
    if 작업_hwp_hwnd:
        창_임베드(작업_hwp_hwnd, 비교보기_우측_프레임_hwnd)

def 비교보기_임베드_재확인():
    if not 비교보기_사용:
        return
    if 원본_hwp_hwnd and 비교보기_좌측_프레임_hwnd:
        창_임베드(원본_hwp_hwnd, 비교보기_좌측_프레임_hwnd)
    if 작업_hwp_hwnd and 비교보기_우측_프레임_hwnd:
        창_임베드(작업_hwp_hwnd, 비교보기_우측_프레임_hwnd)

def 원본_뷰어_문서표시(파일, 확장자명):
    if not 비교보기_사용 or 원본_hwp is None:
        return
    try:
        원본_hwp.Open(파일, Format=확장자명.upper(), arg="lock:true;forceopen:true")
    except Exception as e:
        로그(f"원본 보기 창에서 파일 열기 실패(무시): {e}")
        return
    비교보기_임베드_재확인()

def 원본_뷰어_분리():
    global 원본_hwp, 원본_hwp_hwnd
    if 원본_hwp is None:
        return
    창_임베드_해제(원본_hwp_hwnd)
    원본_hwp = None
    원본_hwp_hwnd = None

def 작업창_분리():
    global hwp, 작업_hwp_hwnd
    if 작업_hwp_hwnd:
        창_임베드_해제(작업_hwp_hwnd)
    hwp = None
    작업_hwp_hwnd = None

def 원본_뷰어_닫기():
    global 원본_hwp, 원본_hwp_hwnd
    if 원본_hwp is None:
        return
    창_임베드_해제(원본_hwp_hwnd)
    try:
        원본_hwp.Quit()
    except Exception:
        pass
    finally:
        원본_hwp = None
        원본_hwp_hwnd = None

def 작업창_닫기():
    global hwp, 작업_hwp_hwnd
    if hwp is None:
        return
    창_임베드_해제(작업_hwp_hwnd)
    try:
        hwp.Quit()
    except Exception:
        pass
    finally:
        hwp = None
        작업_hwp_hwnd = None

# ============================================================
# 서식 조작 함수들
# ============================================================

def 텍스트_삽입(text):
    if not text or hwp is None:
        return
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HInsertText
        act.GetDefault("InsertText", pset.HSet)
        pset.Text = text
        act.Execute("InsertText", pset.HSet)
    except Exception as e:
        로그(f"텍스트 삽입 실패(무시): {e}")

def 문자모양_적용_현재선택(폰트=None, 크기_pt=None, 굵게=None, 장평=None, 자간=None):
    if hwp is None:
        return
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HCharShape
        act.GetDefault("CharShape", pset.HSet)
        if 폰트:
            for 필드 in ("FaceNameHangul", "FaceNameLatin", "FaceNameHanja",
                         "FaceNameJapanese", "FaceNameOther", "FaceNameSymbol", "FaceNameUser"):
                try:
                    setattr(pset, 필드, 폰트)
                except Exception:
                    pass
        if 크기_pt:
            try:
                pset.Height = hwp.PointToHwpUnit(크기_pt)
            except Exception:
                pass
        if 굵게 is not None:
            try:
                pset.Bold = 1 if 굵게 else 0
            except Exception:
                pass
        if 장평 is not None:
            for 필드 in ("RatioHangul", "RatioLatin", "RatioHanja", "RatioJapanese",
                         "RatioOther", "RatioSymbol", "RatioUser"):
                try:
                    setattr(pset, 필드, 장평)
                except Exception:
                    pass
        if 자간 is not None:
            for 필드 in ("SpacingHangul", "SpacingLatin", "SpacingHanja", "SpacingJapanese",
                         "SpacingOther", "SpacingSymbol", "SpacingUser"):
                try:
                    setattr(pset, 필드, 자간)
                except Exception:
                    pass
        act.Execute("CharShape", pset.HSet)
    except Exception as e:
        로그(f"문자모양 적용 실패(무시): {e}")

def 문단_줄간격_적용_현재선택(퍼센트):
    if hwp is None:
        return
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HParaShape
        act.GetDefault("ParagraphShape", pset.HSet)
        try:
            pset.LineSpacingType = hwp.LineSpacingMethod("Percent")
        except Exception:
            pass
        pset.LineSpacing = 퍼센트
        act.Execute("ParagraphShape", pset.HSet)
    except Exception as e:
        로그(f"줄간격 적용 실패(무시): {e}")

def 문단_위간격_적용_현재선택(pt):
    if hwp is None:
        return
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HParaShape
        act.GetDefault("ParagraphShape", pset.HSet)
        pset.PrevSpacing = hwp.PointToHwpUnit(pt)
        act.Execute("ParagraphShape", pset.HSet)
    except Exception as e:
        로그(f"문단 위 간격 적용 실패(무시): {e}")

def 텍스트_너비_em(text):
    총 = 0.0
    for ch in text:
        폭 = unicodedata.east_asian_width(ch)
        총 += 1.0 if 폭 in ("W", "F") else 0.5
    return 총

def _문단_공백_건너뛰기(text, idx):
    """문단 내 실제 문자 오프셋을 유지하면서 공백류만 건너뛴다."""
    while idx < len(text) and text[idx] in (" ", "\t", "\u00a0", "\u3000"):
        idx += 1
    return idx


def 문단_내어쓰기_기준_오프셋(text):
    """Shift+Tab을 실행할 '본문 첫 글자'의 문자 오프셋을 반환한다.

    v1.10:
    - 문자 폭을 추정하지 않고 실제 Shift+Tab(ParagraphShapeIndentAtCaret)을 쓸 수 있도록
      커서를 본문 첫 글자 위치까지 정확히 이동시키기 위한 오프셋만 계산한다.
    - 일반 기호 문단: '- 본문' -> '본문', '※ 본문' -> '본문'
    - 괄호 라벨 문단: 'ㅇ (개요) 본문' -> '본문'
    - 콜론 라벨 문단: '- 추진부서 : 본문' -> '본문'
    - 세트 후속문단: '(6~16번) : 최근 ...' -> '최근'
    """
    if not text:
        return None

    # 1) □/ㅇ/-/※/번호 항목 등 실제 구조 마커가 있는 문단
    마커_끝 = 문장부호_마커_끝위치(text)
    if 마커_끝 is not None:
        idx = _문단_공백_건너뛰기(text, 마커_끝)

        # 마커 바로 뒤 괄호 라벨: 'ㅇ (개요) 본문', '- (이동도서관) 본문',
        # '※ (1~5번) : 본문' 등. 괄호/콜론 라벨 전체 뒤의 첫 본문에 맞춘다.
        if idx < len(text) and text[idx] in "(（":
            닫는괄호 = ")" if text[idx] == "(" else "）"
            close_idx = text.find(닫는괄호, idx + 1)
            if close_idx > idx:
                after = _문단_공백_건너뛰기(text, close_idx + 1)
                if after < len(text) and text[after] in ":：":
                    after = _문단_공백_건너뛰기(text, after + 1)
                if after > close_idx + 1 and after < len(text):
                    return after

        # 일반 콜론 라벨: '- 추진부서 : 총무과' -> '총무과'
        라벨_탐색_구간 = text[idx:idx + 40]
        콜론_일치 = re.match(r"^([^\n\r:：]{1,30}?)[ \t]*[:：][ \t]+", 라벨_탐색_구간)
        if 콜론_일치:
            return idx + 콜론_일치.end()

        # 별도 라벨이 없으면 마커 뒤 첫 본문 글자에 맞춘다.
        return idx if idx < len(text) else None

    # 2) 상위 문장부호를 상속하는 세트 후속문단.
    #    예: '         (6~16번) : 최근 ...'
    idx = _문단_공백_건너뛰기(text, 0)
    if idx < len(text) and text[idx] in "(（":
        닫는괄호 = ")" if text[idx] == "(" else "）"
        close_idx = text.find(닫는괄호, idx + 1)
        if close_idx > idx:
            after = _문단_공백_건너뛰기(text, close_idx + 1)
            if after < len(text) and text[after] in ":：":
                after = _문단_공백_건너뛰기(text, after + 1)
                if after < len(text):
                    return after

    return None


def 문단_내어쓰기_적용_현재선택(들여쓰기_pt):
    """구형 수치 기반 보정용 함수.

    v1.10부터 표준서식의 주 내어쓰기 경로에서는 사용하지 않는다.
    Shift+Tab 실행이 불가능한 특수 상황의 호환성을 위해 함수 자체만 유지한다.
    """
    if hwp is None:
        return
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HParaShape
        act.GetDefault("ParagraphShape", pset.HSet)
        여백 = hwp.PointToHwpUnit(들여쓰기_pt)
        pset.LeftMargin = 여백
        pset.Indentation = -여백
        act.Execute("ParagraphShape", pset.HSet)
    except Exception as e:
        로그(f"내어쓰기 적용 실패(무시): {e}")


def 문단_내어쓰기_적용(문단_시작위치, text, 폰트크기_pt=None, 폰트=None, 굵게=None):
    """아래아한글 Shift+Tab과 동일한 방식으로 내어쓰기를 적용한다.

    핵심은 본문 첫 글자 위치까지 *실제 커서*를 이동한 뒤
    HAction.Run('ParagraphShapeIndentAtCaret')을 실행하는 것이다.
    문자폭(em) 추정값으로 LeftMargin/Indentation을 계산하지 않는다.

    v1.11: ParagraphShapeIndentAtCaret 실행 후 문단의 글자 서식(폰트/크기/
    굵게)이 풀리는 사례가 있어, 호출 직전에 문단 전체에 적용해 둔 값을
    알고 있다면(폰트/폰트크기_pt/굵게 중 하나라도 전달됨) 내어쓰기 실행
    직후 문단 전체에 동일한 값을 한 번 더 적용해 되돌린다.
    """
    오프셋 = 문단_내어쓰기_기준_오프셋(text)
    if 오프셋 is None or 오프셋 <= 0:
        return False

    원래위치 = None
    try:
        원래위치 = hwp.GetPos()
    except Exception:
        pass

    try:
        # SetPos의 문자 인덱스를 직접 더하는 방식보다, 문단 시작에서 실제 문자를
        # 한 글자씩 이동하는 방식이 HWP/HWPX 및 서로 다른 런(run)에서도 안전하다.
        hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2])
        hwp_run("MoveParaBegin")
        for _ in range(오프셋):
            이전 = hwp.GetPos()
            hwp_run("MoveRight")
            if hwp.GetPos() == 이전:
                raise RuntimeError("Shift+Tab 기준 위치까지 커서를 이동하지 못했습니다.")

        # 아래아한글 Shift+Tab의 실제 액션. 현재 커서의 X좌표가 둘째 줄 이후의
        # 시작 위치가 되므로 비례폰트/공백/라벨 폭과 무관하게 정확히 정렬된다.
        try:
            결과 = hwp.HAction.Run("ParagraphShapeIndentAtCaret")
        except Exception:
            결과 = hwp.Run("ParagraphShapeIndentAtCaret")

        if 결과 is False:
            raise RuntimeError("ParagraphShapeIndentAtCaret 실행 결과가 False입니다.")

        # 내어쓰기(문단 여백 설정) 실행 직후 글자 서식이 풀리는 경우를 대비해,
        # 호출부가 문단에 적용해 둔 폰트/크기/굵게 값을 알고 있다면 다시 한 번
        # 문단 전체에 적용해 서식을 보존한다.
        if 폰트 is not None or 폰트크기_pt is not None or 굵게 is not None:
            try:
                hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2])
                hwp_run("MoveParaBegin")
                hwp_run("MoveSelParaEnd")
                문자모양_적용_현재선택(폰트=폰트, 크기_pt=폰트크기_pt, 굵게=굵게)
                hwp_run("Cancel")
            except Exception as e:
                로그(f"내어쓰기 후 글자서식 복원 실패(무시): {e}")

        진단로그(f"[Shift+Tab 내어쓰기] 기준 오프셋 {오프셋}: {text.strip()[:60]}")
        return True
    except Exception as e:
        # 수치 추정 방식으로 조용히 대체하면 실제 Shift+Tab과 위치가 달라질 수 있으므로
        # v1.10에서는 실패 사실을 명확히 남기고 임의 보정을 하지 않는다.
        로그(f"Shift+Tab 내어쓰기 적용 실패(무시): {e}")
        return False
    finally:
        if 원래위치 is not None:
            try:
                hwp.SetPos(*원래위치)
            except Exception:
                pass

def 페이지_여백_설정(여백_mm):
    if hwp is None:
        return
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HSecDef
        act.GetDefault("PageSetup", pset.HSet)
        pset.PageDef.LeftMargin = hwp.MiliToHwpUnit(여백_mm["left"])
        pset.PageDef.RightMargin = hwp.MiliToHwpUnit(여백_mm["right"])
        pset.PageDef.TopMargin = hwp.MiliToHwpUnit(여백_mm["top"])
        pset.PageDef.BottomMargin = hwp.MiliToHwpUnit(여백_mm["bottom"])
        pset.PageDef.HeaderLen = hwp.MiliToHwpUnit(여백_mm["header"])
        pset.PageDef.FooterLen = hwp.MiliToHwpUnit(여백_mm["footer"])
        act.Execute("PageSetup", pset.HSet)
    except Exception as e:
        로그(f"표준서식 여백 설정 실패(무시): {e}")

def 들여쓰기_공백_맞추기(목표_공백수):
    try:
        hwp_run("MoveParaBegin")
        문단_시작위치 = hwp.GetPos()
        text = 현재문단_텍스트()
        벗긴텍스트 = text.lstrip(" ")
        기존_공백수 = len(text) - len(벗긴텍스트)
        hwp.SetPos(*문단_시작위치)
        if 기존_공백수 == 목표_공백수:
            return
        if 기존_공백수 > 0:
            문단_범위_선택(문단_시작위치, 0, 기존_공백수)
            hwp_run("Delete")
            hwp.SetPos(*문단_시작위치)
        if 목표_공백수 > 0:
            텍스트_삽입(" " * 목표_공백수)
    except Exception as e:
        로그(f"들여쓰기 보정 실패(무시): {e}")

표준서식_기호_별칭 = {
    # ☞로 시작하는 문장은 ㅇ와 동일한 폰트·크기·굵기·문단위간격 규칙을 적용한다.
    "☞": "ㅇ",
}

def 표준서식_기호규칙_찾기(text):
    if not text:
        return None
    벗긴텍스트 = text.lstrip(" ")
    if not 벗긴텍스트:
        return None
    for 규칙 in 표준서식_설정["기호_규칙"]:
        if 벗긴텍스트.startswith(규칙[0]):
            return 규칙
    for 별칭_기호, 원본_기호 in 표준서식_기호_별칭.items():
        if 벗긴텍스트.startswith(별칭_기호):
            for 규칙 in 표준서식_설정["기호_규칙"]:
                if 규칙[0] == 원본_기호:
                    return 규칙
    return None

def 표준서식_문단_처리(문단_순번, 헤더_역할=None, 상속_기호_매칭=None):
    """현재 문단에 보고서 표준서식을 적용한다.

    v1.5:
    - □/ㅇ/-/※ 구조 기호가 제목/일자 판정보다 우선한다.
    - 세트 후속문단은 상위 문장부호의 폰트/크기 규칙을 상속한다.
      예: '※ (1~5번)...' 다음 '(6~16번)...'도 ※ 규칙(한컴돋움 13pt)을 적용한다.
    - 상속 문단은 원래의 더 깊은 들여쓰기를 유지한다.
    """
    text = 현재문단_텍스트()
    if not text or not text.strip():
        if 표준서식_장평_사용:
            hwp_run("MoveParaBegin")
            hwp_run("MoveSelParaEnd")
            문자모양_적용_현재선택(장평=표준서식_설정["기본_장평"])
            hwp_run("Cancel")
        if 표준서식_줄간격_사용:
            hwp_run("MoveParaBegin")
            hwp_run("MoveSelParaEnd")
            문단_줄간격_적용_현재선택(표준서식_설정["기본_줄간격_퍼센트"])
            hwp_run("Cancel")
        return

    자체_기호_매칭 = 표준서식_기호규칙_찾기(text) if 표준서식_기호_사용 else None
    기호_매칭 = 자체_기호_매칭 or 상속_기호_매칭

    제목_문단인가 = bool(
        not 기호_매칭 and 표준서식_제목_사용 and 헤더_역할 == "title"
    )
    일자담당자_문단인가 = bool(
        not 기호_매칭 and 표준서식_일자담당자_사용 and 헤더_역할 == "dateinfo"
    )

    # 자체 문장부호가 있는 경우에만 표준 선행공백으로 보정한다.
    if 자체_기호_매칭:
        들여쓰기_공백_맞추기(자체_기호_매칭[1])

    if 표준서식_장평_사용:
        hwp_run("MoveParaBegin")
        hwp_run("MoveSelParaEnd")
        문자모양_적용_현재선택(장평=표준서식_설정["기본_장평"])
        hwp_run("Cancel")

    if 표준서식_줄간격_사용:
        hwp_run("MoveParaBegin")
        hwp_run("MoveSelParaEnd")
        문단_줄간격_적용_현재선택(표준서식_설정["기본_줄간격_퍼센트"])
        hwp_run("Cancel")

    if 표준서식_문단위간격_사용:
        간격_pt = 표준서식_문단위간격_찾기(text)
        if 간격_pt is not None:
            hwp_run("MoveParaBegin")
            hwp_run("MoveSelParaEnd")
            문단_위간격_적용_현재선택(간격_pt)
            hwp_run("Cancel")

    if 제목_문단인가:
        규칙 = 표준서식_설정["제목_문단"]
        hwp_run("MoveParaBegin")
        hwp_run("MoveSelParaEnd")
        문자모양_적용_현재선택(
            폰트=규칙["font"], 크기_pt=규칙["size_pt"], 굵게=표준서식_제목_굵게
        )
        hwp_run("Cancel")
    elif 일자담당자_문단인가:
        규칙 = 표준서식_설정["일자담당자_문단"]
        hwp_run("MoveParaBegin")
        hwp_run("MoveSelParaEnd")
        문자모양_적용_현재선택(
            폰트=규칙["font"], 크기_pt=규칙["size_pt"], 굵게=표준서식_일자담당자_굵게
        )
        hwp_run("Cancel")
    elif 기호_매칭:
        기호, 공백수, 폰트, 크기, 문단굵게_기본값, 기호만굵게_기본값 = 기호_매칭
        굵게_허용 = 표준서식_기호_굵게.get(기호, True)
        문단굵게 = 문단굵게_기본값 and 굵게_허용
        기호만굵게 = 기호만굵게_기본값 and 굵게_허용

        hwp_run("MoveParaBegin")
        hwp_run("MoveSelParaEnd")
        # 전체 문단의 bold 상태도 규칙값으로 정규화한다.
        문자모양_적용_현재선택(
            폰트=폰트,
            크기_pt=크기,
            굵게=문단굵게,
        )
        hwp_run("Cancel")

        # v1.10: 실제 Shift+Tab 내어쓰기는 자체 기호 문단뿐 아니라
        # '(6~16번) : 최근 ...' 같은 상위 기호 상속 문단에도 적용한다.
        # 오프셋을 찾을 수 없는 단순 연속 설명문은 건드리지 않는다.
        현재_text = 현재문단_텍스트()
        if 문단_내어쓰기_기준_오프셋(현재_text) is not None:
            문단_내어쓰기_적용(hwp.GetPos(), 현재_text, 폰트크기_pt=크기, 폰트=폰트, 굵게=문단굵게)

        # 기호 자체 bold는 실제 기호가 존재하는 문단에만 적용한다.
        if 자체_기호_매칭 and 기호만굵게 and not 문단굵게:
            hwp_run("MoveParaBegin")
            문단_시작 = hwp.GetPos()
            문단_범위_선택(문단_시작, 공백수, 공백수 + 1)
            문자모양_적용_현재선택(굵게=True)
            hwp_run("Cancel")

def 표준서식_전체_적용():
    if 중단_요청됨():
        return False
    로그("표준서식 적용 시작")
    if 표준서식_여백_사용:
        페이지_여백_설정(표준서식_설정["여백_mm"])

    hwp_run("MoveDocBegin")
    문단_순번 = 0
    구조_시작됨 = False
    상단_비기호_문단수 = 0
    활성_세트_들여쓰기 = None
    활성_세트_기호규칙 = None

    while True:
        if 중단_요청됨():
            return False

        문단_순번 += 1
        text = 현재문단_텍스트()
        헤더_역할 = None
        상속_기호_매칭 = None

        if text and text.strip():
            자체_기호_매칭 = 표준서식_기호규칙_찾기(text) if 표준서식_기호_사용 else None

            if (
                not 자체_기호_매칭
                and 활성_세트_들여쓰기 is not None
                and 활성_세트_기호규칙 is not None
                and 세트문장_후속문단인가(활성_세트_들여쓰기, text)
            ):
                상속_기호_매칭 = 활성_세트_기호규칙
            else:
                활성_세트_들여쓰기 = None
                활성_세트_기호규칙 = None

                if 자체_기호_매칭:
                    구조_시작됨 = True
                    활성_세트_들여쓰기 = 자체_기호_매칭[1]
                    활성_세트_기호규칙 = 자체_기호_매칭
                elif not 구조_시작됨:
                    상단_비기호_문단수 += 1
                    if 상단_비기호_문단수 == 1:
                        헤더_역할 = "title"
                    elif 상단_비기호_문단수 == 2:
                        헤더_역할 = "dateinfo"

        표준서식_문단_처리(
            문단_순번,
            헤더_역할=헤더_역할,
            상속_기호_매칭=상속_기호_매칭,
        )
        if not 다음_문단으로_진행():
            break

    로그("표준서식 적용 완료")
    return True

# ============================================================
# 괄호 및 문두 라벨 처리 (콜론 라벨 굵게 + 괄호 라벨 굵게 + 부연설명 축소)
# ============================================================

괄호_축소_사용 = True
괄호_축소_pt = 2
괄호_라벨_볼드_사용 = True

괄호_정규식 = re.compile(r"\(([^()]+)\)")
괄호_범위라벨_정규식 = re.compile(r"^\s*\d+\s*[~～\-–—]\s*\d+\s*번?\s*$")

# HWP 문단 앞에 섞일 수 있는 폭 없는 제어문자까지 문두 공백으로 취급한다.
_문두_무시문자_정규식 = re.compile(r"[\s\u200b\u2060\ufeff]+")

def 괄호_문두_라벨인가(text, match):
    """실제 문두/문장부호 직후의 첫 괄호만 라벨로 판정한다.

    '- (이동도서관) ...' -> 라벨
    '- 예산 편성(차량 운영비...)' -> 부연설명(라벨 아님)
    """
    if not text or match is None:
        return False

    앞부분 = text[:match.start()]
    if not _문두_무시문자_정규식.sub("", 앞부분):
        return True

    마커_끝 = 문장부호_마커_끝위치(text)
    if 마커_끝 is None or 마커_끝 > match.start():
        return False

    사이 = text[마커_끝:match.start()]
    return not _문두_무시문자_정규식.sub("", 사이)

def 괄호_뒤_콜론인가(text, 끝_offset):
    idx = 끝_offset
    while idx < len(text) and (text[idx].isspace() or text[idx] in "\u200b\u2060\ufeff"):
        idx += 1
    return idx < len(text) and text[idx] in (":", "：")


def 세트후속_범위괄호_라벨인가(text, match, 세트후속문단=False):
    """※ 세트의 후속 '(6~16번) :' 같은 범위 괄호를 라벨로 판정한다.

    이 라벨은 상위 문장부호 바로 뒤의 첫 괄호가 아니더라도 같은 세트의
    계층 라벨이므로 부연설명 괄호처럼 2pt 축소하면 안 된다.
    """
    if not 세트후속문단:
        return False

    앞부분 = text[:match.start()]
    if _문두_무시문자_정규식.sub("", 앞부분):
        return False
    if not 괄호_뒤_콜론인가(text, match.end()):
        return False
    return bool(괄호_범위라벨_정규식.fullmatch(match.group(1)))

def 문단_범위_선택(문단_시작위치, 시작offset, 끝offset):
    """문단 안의 [시작offset, 끝offset) 구간을 한 번의 SelectText 호출로 선택한다.

    v1.11 효율성 개선: 예전에는 이 구간을 MoveSelRight로 한 글자씩 반복
    이동하며 선택했다. 글자 수만큼 COM 호출이 발생해 라벨/괄호가 길수록
    느려졌는데, SelectText는 시작·끝 좌표만 지정하면 한 번에 선택되므로
    결과는 같고 호출 횟수만 크게 줄어든다.
    """
    hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2])
    return hwp.SelectText(
        문단_시작위치[1], 문단_시작위치[2] + 시작offset,
        문단_시작위치[1], 문단_시작위치[2] + 끝offset,
    )

def 선택범위_현재크기_pt(문단_시작위치, 시작offset, 끝offset):
    if 끝offset <= 시작offset:
        return None
    try:
        문단_범위_선택(문단_시작위치, 시작offset, 끝offset)
        act = hwp.HAction
        pset = hwp.HParameterSet.HCharShape
        act.GetDefault("CharShape", pset.HSet)
        hwp_run("Cancel")
        return pset.Height / 100.0
    except Exception:
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        return None

def 괄호_텍스트_크기_축소_현재선택():
    if hwp is None:
        return
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HCharShape
        act.GetDefault("CharShape", pset.HSet)
        기존_pt = getattr(pset, "Height", 0) / 100.0
        if 기존_pt:
            새_pt = max(1, 기존_pt - 괄호_축소_pt)
            pset.Height = hwp.PointToHwpUnit(새_pt)
        act.Execute("CharShape", pset.HSet)
    except Exception as e:
        로그(f"괄호 텍스트 크기 축소 실패(무시): {e}")

def 괄호_및_라벨_텍스트_문단_처리(세트후속문단=False):
    """
    현재 문단에 대해:
    1) 문두 라벨(콜론 앞 텍스트 or 괄호 라벨) 굵게 처리
    2) 문장 중간·끝의 부연설명 괄호 크기 2pt 축소
    """
    text = 현재문단_텍스트()
    if not text:
        return 0

    if not 괄호_라벨_볼드_사용 and (not 괄호_축소_사용 or "(" not in text):
        return 0

    문단_시작위치 = hwp.GetPos()
    적용_횟수 = 0

    # --------------------------------------------------------
    # 1. 문두 콜론 라벨 굵게 ("- 추진부서 : 내용", "ㅇ (추진부서) : 내용")
    # --------------------------------------------------------
    if 괄호_라벨_볼드_사용 and 문장부호_시작인가(text):
        마커_끝 = 문장부호_마커_끝위치(text)
        if 마커_끝 is not None:
            idx = 마커_끝
            while idx < len(text) and text[idx] in (" ", "\t"):
                idx += 1
            if idx < len(text):
                나머지 = text[idx:]
                콜론_매치 = re.match(r"^([^\n\r:：]{1,25}?)[ \t]*([:：])[ \t]+(\S.*)$", 나머지)
                if 콜론_매치:
                    라벨_텍스트 = 콜론_매치.group(1).strip()
                    if 라벨_텍스트:
                        라벨_시작 = idx + 나머지.find(라벨_텍스트)
                        라벨_끝 = 라벨_시작 + len(라벨_텍스트)
                        try:
                            문단_범위_선택(문단_시작위치, 라벨_시작, 라벨_끝)
                            문자모양_적용_현재선택(굵게=True)
                            hwp_run("Cancel")
                            적용_횟수 += 1
                            진단로그(f"[문두라벨굵게] '{라벨_텍스트}' 굵게 적용")
                        except Exception as e:
                            로그(f"문두 라벨 굵게 적용 중 오류(무시): {e}")

    # --------------------------------------------------------
    # 2. 괄호 처리 (문두 라벨 괄호 굵게 / 본문 부연설명 괄호 축소)
    # --------------------------------------------------------
    if "(" in text:
        for match in 괄호_정규식.finditer(text):
            앞부분 = text[:match.start()]
            시작_offset = match.start()
            끝_offset = match.end()

            범위_세트라벨 = 세트후속_범위괄호_라벨인가(
                text, match, 세트후속문단=세트후속문단
            )
            if 괄호_문두_라벨인가(text, match) or 범위_세트라벨:
                if 범위_세트라벨:
                    진단로그(f"[세트후속라벨] '{match.group(0)}' 괄호 2pt 축소 제외")
                if not 괄호_라벨_볼드_사용:
                    continue
                try:
                    문단_범위_선택(문단_시작위치, 시작_offset, 끝_offset)
                    문자모양_적용_현재선택(굵게=True)
                    hwp_run("Cancel")
                    적용_횟수 += 1
                    진단로그(f"[괄호굵게] '{match.group(0)}' 굵게 적용")
                except Exception as e:
                    로그(f"괄호 라벨 굵게 적용 중 오류(무시): {e}")
                continue

            if not 괄호_축소_사용:
                continue

            if 시작_offset > 0:
                주변_pt = 선택범위_현재크기_pt(문단_시작위치, 시작_offset - 1, 시작_offset)
            elif 끝_offset < len(text):
                주변_pt = 선택범위_현재크기_pt(문단_시작위치, 끝_offset, 끝_offset + 1)
            else:
                주변_pt = None

            괄호_pt = 선택범위_현재크기_pt(문단_시작위치, 시작_offset, 끝_offset)

            if 괄호_pt is not None and 주변_pt is not None and 괄호_pt < 주변_pt - 0.4:
                continue

            try:
                문단_범위_선택(문단_시작위치, 시작_offset, 끝_offset)
                괄호_텍스트_크기_축소_현재선택()
                hwp_run("Cancel")
                적용_횟수 += 1
                진단로그(f"[괄호축소] '{match.group(0)}' 글자 크기 {괄호_축소_pt}pt 축소")
            except Exception as e:
                로그(f"괄호 텍스트 축소 중 오류(무시): {e}")

    try:
        hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2])
    except Exception:
        pass

    return 적용_횟수

def 괄호_텍스트_크기_축소_전체_적용():
    if 중단_요청됨():
        return False
    로그("문두 라벨(콜론/괄호) 굵게 및 부연설명 괄호 크기 축소 처리 시작")
    hwp_run("MoveDocBegin")
    총_적용_횟수 = 0
    활성_세트_들여쓰기 = None

    while True:
        if 중단_요청됨():
            return False

        text = 현재문단_텍스트()
        세트후속문단 = False

        # 순차 문단 문맥을 유지해 '※ ...' 다음의 더 깊게 들여쓴
        # '(6~16번) : ...' 등을 같은 세트의 후속 문단으로 인식한다.
        if 활성_세트_들여쓰기 is not None and 세트문장_후속문단인가(활성_세트_들여쓰기, text):
            세트후속문단 = True
        else:
            활성_세트_들여쓰기 = None
            if 세트문장_시작인가(text):
                활성_세트_들여쓰기 = 세트문장_선행들여쓰기_폭(text)

        결과 = 괄호_및_라벨_텍스트_문단_처리(세트후속문단=세트후속문단)
        if 결과:
            총_적용_횟수 += 결과
        if not 다음_문단으로_진행():
            break

    로그(f"문두 라벨 / 괄호 처리 완료 (총 {총_적용_횟수}건)")
    return True

# ============================================================
# 자간조정 및 단어 분리 방지 알고리즘
# ============================================================

def 현재_페이지번호():
    try:
        정보 = hwp.KeyIndicator()
        if 정보 and len(정보) >= 4:
            return int(정보[3])
    except Exception:
        pass
    return None

def 검수_문제_기록(파일, text):
    global 검수_문제목록
    if not 검수_사용:
        return
    검수_문제목록.append({
        "file": str(파일),
        "text": text,
        "page": 현재_페이지번호(),
    })


def 줄경계_어절연속_문자쌍인가(앞문자, 다음문자):
    """화면줄 경계의 두 문자가 공백 없는 같은 어절의 연속인지 판정한다.

    한글/영문/숫자처럼 ``isalnum()``인 문자끼리 실제 Enter나 공백 없이
    화면줄만 바뀐 경우를 대상으로 한다. 예: ``제공하 | 며,``.

    v1.11: "경기도·경상북도"처럼 가운뎃점(·)으로 단어를 이어붙인 경우도
    하나의 어절로 취급한다. 줄 끝이 "·"로 끝나거나 다음 줄이 "·"로
    시작하면(즉 "·"가 경계에 걸리면) 글자가 alnum인지와 무관하게
    같은 어절의 연속으로 본다.
    """
    if not 앞문자 or not 다음문자:
        return False
    if 앞문자[-1] in "·ㆍ" or 다음문자[0] in "·ㆍ":
        return True
    return 앞문자[-1].isalnum() and 다음문자[0].isalnum()


def 현재줄_끝_어절분리인가():
    """'제공하' | '며,'처럼 같은 어절이 화면줄 경계에서 갈라졌는지 확인.

    HWP의 MoveSelWordBegin/End만으로는 조사·어미+구두점 경계에서
    단어 선택이 다음 화면줄까지 안정적으로 확장되지 않는 경우가 있다.
    따라서 화면줄 끝과 다음 화면줄 첫 문자를 직접 확인한다.
    실제 Enter, 다른 컨트롤/문단, 공백 경계는 제외한다.
    """
    if hwp is None:
        return False

    원래위치 = hwp.GetPos()
    try:
        hwp_run("MoveLineEnd")
        줄끝위치 = hwp.GetPos()

        # 현재 화면줄의 마지막 실제 문자를 확인한다.
        hwp_run("MoveSelLineBegin")
        줄텍스트 = 현재선택영역_텍스트()
        hwp_run("Cancel")
        hwp.SetPos(*줄끝위치)
        줄텍스트 = (줄텍스트 or "").rstrip("\r\n")
        if not 줄텍스트:
            return False
        앞문자 = 줄텍스트[-1]
        if 앞문자.isspace():
            return False

        # 다음 화면줄 첫 문자 위치로 이동한다.
        hwp_run("MoveNextChar")
        다음위치 = hwp.GetPos()
        if 다음위치 == 줄끝위치:
            return False
        if 다음위치[0] != 줄끝위치[0] or 다음위치[1] != 줄끝위치[1]:
            return False
        if 두_위치_사이_줄바꿈_문자인가(줄끝위치, 다음위치):
            return False

        # 줄끝에서 오른쪽 한 글자를 직접 읽어 공백 없는 연속 어절인지 확인한다.
        hwp.SetPos(*줄끝위치)
        hwp_run("MoveSelRight")
        다음텍스트 = 현재선택영역_텍스트()
        hwp_run("Cancel")
        hwp.SetPos(*줄끝위치)
        if not 다음텍스트:
            return False

        다음문자 = ""
        for ch in 다음텍스트:
            if ch not in "\r\n":
                다음문자 = ch
                break
        if not 다음문자 or 다음문자.isspace():
            return False

        return 줄경계_어절연속_문자쌍인가(앞문자, 다음문자)
    except Exception:
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        return False
    finally:
        try:
            hwp.SetPos(*원래위치)
        except Exception:
            pass


_붙임괄호_다음구간_미리보기_글자수 = 3

def 현재줄_끝_붙임괄호_분리인가():
    """'경상북도' | '(1)'처럼 붙임 괄호가 화면 줄 경계에서 갈라졌는지 확인.

    v1.11:
    - 기존에는 줄 끝 바로 다음 글자가 곧바로 여는 괄호인 경우만 감지했다.
      그래서 '…사기진' | '작(노조,동호회),…'처럼, 같은 단어의 꼬리 글자
      ('작')가 괄호 앞에 공백 없이 붙어 다음 줄로 넘어간 경우는 놓쳤다.
    - 이제는 다음 줄 맨 앞의 짧은 구간(최대 _붙임괄호_다음구간_미리보기_글자수자)
      안에서, 공백 없이 이어지는 한글/영문/숫자 0~2자 뒤에 여는 괄호가
      나오면 같은 '붙임 괄호 분리'로 인식한다. 아래아한글에서 Shift+Tab으로
      맞춘 들여쓰기가 이런 단어 조각 때문에 어긋나 보이는 것을 막기 위함이다.
    """
    if hwp is None:
        return False

    원래위치 = hwp.GetPos()
    try:
        hwp_run("MoveLineEnd")
        줄끝위치 = hwp.GetPos()

        hwp_run("MoveSelLineBegin")
        줄텍스트 = 현재선택영역_텍스트()
        hwp_run("Cancel")
        hwp.SetPos(*줄끝위치)

        줄텍스트 = (줄텍스트 or "").rstrip()
        if not (줄텍스트 and re.search(r"[0-9A-Za-z가-힣]$", 줄텍스트)):
            return False

        hwp.SetPos(*줄끝위치)
        for _ in range(_붙임괄호_다음구간_미리보기_글자수):
            hwp_run("MoveSelRight")
        다음구간 = 현재선택영역_텍스트()
        hwp_run("Cancel")
        hwp.SetPos(*줄끝위치)

        다음구간 = (다음구간 or "").replace("\r", "").replace("\n", "")
        if not 다음구간:
            return False

        # 다음 줄 첫머리가: (a) 곧바로 여는 괄호이거나,
        # (b) 공백 없이 붙은 한글/영문/숫자 0~2자 뒤에 여는 괄호가 오면 대상.
        일치 = re.match(r"^[0-9A-Za-z가-힣]{0,2}[(（\[［{｛]", 다음구간)
        return bool(일치)
    except Exception:
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        return False
    finally:
        try:
            hwp.SetPos(*원래위치)
        except Exception:
            pass


def 자간자동조정(최대시도=None):
    if 최대시도 is None:
        최대시도 = 자간_최대시도_본문

    count = 0
    이전_단어_시작 = None
    총_시도 = 0
    총_시도_상한 = max(최대시도 * 8, 40)
    붙임괄호_축소횟수 = 0
    어절분리_축소횟수 = 0

    while True:
        if 중단_요청됨():
            return False

        hwp_run("MoveLineEnd")

        # 붙임 괄호가 다음 화면줄로 밀린 경우에는 자간 증가를 금지하고
        # 현재 줄을 우선 축소해 괄호를 앞줄로 당긴다.
        if 현재줄_끝_붙임괄호_분리인가():
            if 붙임괄호_축소횟수 >= 최대시도:
                # v1.11: 포기할 때 그동안 줄인 자간을 그대로 남겨두면 문제가
                # 해결되지도 않은 채 글자 사이만 억지로 눌려 보기 흉해진다.
                # 일반 단어 선택 루프(아래)와 동일하게 되돌려서, 실패하더라도
                # 최소한 원래의 자연스러운 줄바꿈 상태로 남긴다.
                for _ in range(붙임괄호_축소횟수):
                    hwp_run("Undo")
                문제줄 = 현재_화면줄_텍스트()
                검수_문제_기록(현재_처리파일, f"[붙임 괄호 분리] {문제줄.strip()}")
                return True

            hwp_run("MoveLineEnd")
            hwp_run("MoveSelLineBegin")
            hwp_run("CharShapeSpacingDecrease")
            색상_적용_현재선택()
            hwp_run("Cancel")
            붙임괄호_축소횟수 += 1
            총_시도 += 1
            if 총_시도 > 총_시도_상한:
                return True
            continue

        붙임괄호_축소횟수 = 0

        # '제공하' | '며,'처럼 공백 없는 한 어절이 화면줄 경계에서
        # 갈라진 경우에는 HWP의 단어 선택 로직보다 먼저 처리한다.
        # 반드시 현재(앞) 줄을 축소해야 다음 줄의 짧은 꼬리 조각이 올라온다.
        if 현재줄_끝_어절분리인가():
            if 어절분리_축소횟수 >= 최대시도:
                # 위 붙임 괄호 케이스와 동일한 이유로, 실패 시 되돌린다.
                for _ in range(어절분리_축소횟수):
                    hwp_run("Undo")
                문제줄 = 현재_화면줄_텍스트()
                검수_문제_기록(현재_처리파일, f"[어절 줄분리] {문제줄.strip()}")
                return True

            hwp_run("MoveLineEnd")
            hwp_run("MoveSelLineBegin")
            hwp_run("CharShapeSpacingDecrease")
            색상_적용_현재선택()
            hwp_run("Cancel")
            어절분리_축소횟수 += 1
            총_시도 += 1
            if 총_시도 > 총_시도_상한:
                return True
            continue

        어절분리_축소횟수 = 0

        hwp_run("MoveSelWordBegin")
        단어_시작 = hwp.GetPos()

        if 단어_시작 != 이전_단어_시작:
            count = 0
            이전_단어_시작 = 단어_시작

        총_시도 += 1
        if 총_시도 > 총_시도_상한:
            hwp_run("Cancel")
            return True

        if count >= 최대시도:
            문제줄 = 현재_화면줄_텍스트()
            for _ in range(count):
                hwp_run("Undo")
            검수_문제_기록(현재_처리파일, f"[단어 분리] {문제줄.strip()}")
            try:
                hwp.SetPos(단어_시작[0], 단어_시작[1], 단어_시작[2])
            except Exception:
                pass
            hwp_run("MoveWordEnd")
            이전_단어_시작 = None
            count = 0
            continue

        앞부분길이 = 현재선택영역_글자수()
        if 앞부분길이 == 0:
            return True

        hwp_run("MoveSelWordEnd")
        뒷부분길이 = 현재선택영역_글자수()
        if not (앞부분길이 and 뒷부분길이):
            hwp_run("Cancel")
            hwp_run("Cancel")
            return True

        hwp_run("MoveWordBegin")
        try:
            hwp.SetPos(단어_시작[0], 단어_시작[1], 단어_시작[2])
        except Exception:
            pass

        hwp_run("MoveSelWordEnd")
        전체_단어_텍스트 = 현재선택영역_텍스트()
        hwp_run("Cancel")

        try:
            hwp.SetPos(단어_시작[0], 단어_시작[1], 단어_시작[2])
        except Exception:
            pass

        목표_앞부분길이 = None
        for 괄호문자 in "(（「[{":
            위치 = 전체_단어_텍스트.find(괄호문자)
            if 위치 > 0 and (목표_앞부분길이 is None or 위치 < 목표_앞부분길이):
                목표_앞부분길이 = 위치

        hwp_run("MoveLineEnd")
        hwp_run("MoveSelLineBegin")

        if 목표_앞부분길이 is not None and 목표_앞부분길이 == 앞부분길이:
            hwp_run("Cancel")
            return True
        elif 목표_앞부분길이 is not None:
            # 괄호가 붙은 단어는 자간을 늘리지 않는다.
            hwp_run("CharShapeSpacingDecrease")
        elif 앞부분길이 >= 뒷부분길이:
            hwp_run("CharShapeSpacingDecrease")
        else:
            hwp_run("CharShapeSpacingIncrease")

        색상_적용_현재선택()
        count += 1
        hwp_run("Cancel")

def 본문_기존자간조정():
    직전위치 = None
    정체횟수 = 0
    while True:
        if 중단_요청됨():
            return False
        현재위치 = hwp.GetPos()
        if 현재위치 == 직전위치:
            정체횟수 += 1
            if 정체횟수 >= 2:
                로그("본문 자간조정 순회가 같은 위치에서 반복되어 안전 종료합니다.")
                return True
        else:
            정체횟수 = 0
        직전위치 = 현재위치

        result = 자간자동조정()
        if result is False:
            return False
        hwp_run("MoveLineEnd")
        줄끝 = hwp.GetPos()
        hwp_run("MoveNextChar")
        if hwp.GetPos() == 줄끝:
            return True

# ============================================================
# 문장부호 판정 및 공백 보정
# ============================================================

공문서_기호 = {
    "※", "□", "■", "○", "●", "◎", "◇", "◆", "△", "▲", "▽", "▼",
    "▷", "▶", "◁", "◀", "▪", "▫", "ㆍ", "·", "‣", "⁃", "ㅇ",
    "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
    "㉠", "㉡", "㉢", "㉣", "㉤", "㉥", "㉦", "㉧", "㉨", "㉩", "㉪",
    "→", "←", "↑", "↓", "⇒", "⇐", "―", "–", "—", "-", "‒", "−",
}

항목_패턴 = [
    re.compile(r"^\s*\d+(?:-\d+)+\s*[.)]"),
    re.compile(r"^\s*\d+\."),
    re.compile(r"^\s*\d+\)"),
    re.compile(r"^\s*[가-힣]\."),
    re.compile(r"^\s*[가-힣]\)"),
    re.compile(r"^\s*\([가-힣]\)"),
    re.compile(r"^\s*\(\d+\)"),
    re.compile(r"^\s*\[[가-힣]\]"),
]

def _괄호따옴표_시작문자인가(ch):
    """여는/닫는 괄호·따옴표류인지 판정한다.

    ``( 6~16번) : ...`` 처럼 괄호로 시작하는 라벨 문단은 실제로는
    "괄호 라벨"이지 ※·ㅇ·□ 같은 공문서 항목 기호(문장부호)가 아니다.
    Unicode P(구두점)/S(기호) 카테고리 전체를 마커로 인식하는 광범위한
    폴백이 여는/닫는 괄호(Ps/Pe)와 따옴표(Pi/Pf)까지 마커로 오인해서,
    "(6~16번)" 같은 라벨을 "※ 내용"과 같은 방식(기호 뒤에 공백 1칸 강제
    삽입)으로 잘못 처리하는 문제가 있었다. 괄호/따옴표류만 폴백에서
    제외한다.
    """
    if not ch:
        return False
    return unicodedata.category(ch) in ("Ps", "Pe", "Pi", "Pf")

def 문장부호_시작인가(text):
    if not text:
        return False
    text = text.lstrip()
    if not text:
        return False
    for pattern in 항목_패턴:
        if pattern.match(text):
            return True
    first = text[0]
    if first in 공문서_기호:
        return True
    if _괄호따옴표_시작문자인가(first):
        return False
    category = unicodedata.category(first)
    return category.startswith("P") or category.startswith("S")

def 문장부호_마커_끝위치(text):
    if not text:
        return None
    벗긴텍스트 = text.lstrip()
    if not 벗긴텍스트:
        return None
    선행공백_길이 = len(text) - len(벗긴텍스트)
    for pattern in 항목_패턴:
        m = pattern.match(벗긴텍스트)
        if m:
            return 선행공백_길이 + m.end()
    first = 벗긴텍스트[0]
    if first in 공문서_기호:
        return 선행공백_길이 + 1
    if _괄호따옴표_시작문자인가(first):
        return None
    category = unicodedata.category(first)
    if category.startswith("P") or category.startswith("S"):
        return 선행공백_길이 + 1
    return None

def 세트문장_시작인가(text):
    """세트문장의 최상위 시작 문단인지 판정한다.

    일반 따옴표/괄호 등 모든 유니코드 문장부호를 대상으로 하지 않고,
    공문서에서 실제 항목 표지로 쓰는 기호와 번호 패턴만 대상으로 한다.
    """
    if not text:
        return False
    벗긴텍스트 = text.lstrip(" \t")
    if not 벗긴텍스트:
        return False
    for pattern in 항목_패턴:
        if pattern.match(벗긴텍스트):
            return True
    return 벗긴텍스트[0] in 공문서_기호


def 세트문장_선행들여쓰기_폭(text):
    """문단 앞 공백의 상대 폭을 계산한다. 탭은 공백 4칸으로 본다."""
    if not text:
        return 0
    폭 = 0
    for ch in text:
        if ch == " ":
            폭 += 1
        elif ch == "\t":
            폭 += 4
        else:
            break
    return 폭


def 세트문장_후속문단인가(상위_들여쓰기, text):
    """상위 문장부호 문단에 종속된 연속 설명 문단인지 판정한다.

    예) '     ※ ...' 다음의 '         (6~16번) ...'은 포함하지만,
        ' ㅇ ...', '   - ...', '□ ...'처럼 독립 구조 항목은 새 세트로 본다.
    """
    if not text or not text.strip():
        return False

    현재_들여쓰기 = 세트문장_선행들여쓰기_폭(text)
    if 현재_들여쓰기 <= 상위_들여쓰기:
        return False

    벗긴텍스트 = text.lstrip(" \t")
    if not 벗긴텍스트:
        return False

    # 공문서 구조 기호(□/ㅇ/-/※ 등)는 들여쓰기가 더 깊어도 별도 항목이다.
    if 벗긴텍스트[0] in 공문서_기호:
        return False

    # '1.', '(1)', '가.' 등 명시적 항목 번호 역시 별도 항목으로 본다.
    # '(6~16번)'처럼 범위 설명 라벨은 항목_패턴과 일치하지 않으므로 후속문단으로 유지된다.
    for pattern in 항목_패턴:
        if pattern.match(벗긴텍스트):
            return False

    return True


def 세트문장_끝위치_찾기(시작위치, 시작텍스트):
    """세트문장의 마지막 문단 끝 위치와 포함 문단 수를 반환한다."""
    원래위치 = hwp.GetPos()
    상위_들여쓰기 = 세트문장_선행들여쓰기_폭(시작텍스트)
    마지막끝 = 시작위치
    문단수 = 1

    try:
        hwp.SetPos(*시작위치)
        hwp_run("MoveParaEnd")
        마지막끝 = hwp.GetPos()

        hwp.SetPos(*시작위치)
        while True:
            현재시작 = hwp.GetPos()
            hwp_run("MoveNextParaBegin")
            다음시작 = hwp.GetPos()
            if 다음시작 == 현재시작 or 다음시작[0] != 시작위치[0]:
                break

            다음텍스트 = 현재문단_텍스트()
            if not 세트문장_후속문단인가(상위_들여쓰기, 다음텍스트):
                break

            문단수 += 1
            hwp_run("MoveParaEnd")
            마지막끝 = hwp.GetPos()
            hwp.SetPos(*다음시작)

        return 마지막끝, 문단수
    finally:
        try:
            hwp.SetPos(*원래위치)
        except Exception:
            pass


def 위치_페이지번호(pos):
    """지정 위치의 현재 인쇄 페이지 번호를 반환한다."""
    원래위치 = hwp.GetPos()
    try:
        hwp.SetPos(*pos)
        return 현재_페이지번호()
    finally:
        try:
            hwp.SetPos(*원래위치)
        except Exception:
            pass


def 현재문단_줄간격_퍼센트():
    """현재 문단의 줄간격 값을 읽는다. 읽지 못하면 None을 반환한다."""
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HParaShape
        act.GetDefault("ParagraphShape", pset.HSet)
        값 = int(getattr(pset, "LineSpacing", 0) or 0)
        return 값 if 값 > 0 else None
    except Exception:
        return None


def 시작페이지_전체_줄간격_한단계_축소(기준위치):
    """기준위치가 놓인 페이지 전체를 선택해 줄간격을 10% 한 단계 축소한다.

    한글의 ParagraphShapeDecreaseLineSpacing 액션은 선택된 각 문단의 기존 줄간격을
    상대적으로 10%씩 줄이므로, 페이지 안에 서로 다른 줄간격이 있어도 일괄 고정값으로
    덮어쓰지 않는다.
    """
    원래위치 = hwp.GetPos()
    try:
        hwp.SetPos(*기준위치)
        페이지번호 = 현재_페이지번호()
        hwp_run("MovePageBegin")
        페이지시작 = hwp.GetPos()

        # 지나친 축소 방지: 페이지 첫 문단이 이미 100% 이하이면 더 줄이지 않는다.
        현재줄간격 = 현재문단_줄간격_퍼센트()
        if 현재줄간격 is not None and 현재줄간격 <= 세트문장_최소줄간격_퍼센트:
            진단로그(f"[세트문장] {페이지번호}페이지 줄간격이 이미 {현재줄간격}%여서 추가 축소 중단")
            return False

        hwp.SetPos(*기준위치)
        hwp_run("MovePageEnd")
        페이지끝 = hwp.GetPos()

        if 페이지시작[0] != 페이지끝[0]:
            로그(f"세트문장 페이지 선택 실패: 페이지 시작/끝 리스트가 다릅니다. ({페이지시작[0]} != {페이지끝[0]})")
            return False

        hwp.SetPos(*페이지시작)
        선택결과 = hwp.SelectText(페이지시작[1], 페이지시작[2], 페이지끝[1], 페이지끝[2])
        if 선택결과 is False:
            로그("세트문장 페이지 선택에 실패했습니다.")
            return False

        hwp_run("ParagraphShapeDecreaseLineSpacing")
        hwp_run("Cancel")
        return True
    except Exception as e:
        로그(f"세트문장 시작 페이지 줄간격 축소 실패(무시): {e}")
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        return False
    finally:
        try:
            hwp.SetPos(*원래위치)
        except Exception:
            pass


def 세트문장_같은쪽_시도(시작위치, text):
    """하나의 문장부호 세트가 페이지를 넘으면 시작 페이지를 압축한다."""
    if 중단_요청됨():
        return False
    if not 세트문장_시작인가(text):
        return True

    끝위치, 문단수 = 세트문장_끝위치_찾기(시작위치, text)
    시작페이지 = 위치_페이지번호(시작위치)
    끝페이지 = 위치_페이지번호(끝위치)
    if 시작페이지 is None or 끝페이지 is None or 끝페이지 <= 시작페이지:
        return True

    세트문장_통계["대상"] += 1
    요약 = text.strip().replace("\r", " ").replace("\n", " ")[:50]
    진단로그(f"[세트문장] {시작페이지}→{끝페이지}페이지 분리 감지 / {문단수}문단 / {요약}")

    for 시도 in range(1, 세트문장_페이지줄간격_최대시도 + 1):
        if 중단_요청됨():
            return False

        if not 시작페이지_전체_줄간격_한단계_축소(시작위치):
            break
        세트문장_통계["축소횟수"] += 1

        새_시작페이지 = 위치_페이지번호(시작위치)
        새_끝페이지 = 위치_페이지번호(끝위치)
        진단로그(f"[세트문장] 줄간격 축소 {시도}회 후 {새_시작페이지}→{새_끝페이지}페이지")

        if 새_시작페이지 is not None and 새_끝페이지 is not None and 새_끝페이지 <= 새_시작페이지:
            세트문장_통계["성공"] += 1
            로그(f"세트문장 동일 페이지 배치 완료: {요약} (줄간격 {시도}단계 축소)")
            return True

        시작페이지, 끝페이지 = 새_시작페이지, 새_끝페이지

    세트문장_통계["실패"] += 1
    검수_문제_기록(현재_처리파일, f"[세트문장 페이지 분리] {요약}")
    로그(f"세트문장 동일 페이지 배치 미해결: {요약}")
    return True


def 세트문장_같은쪽_전체_적용():
    if not 세트문장_같은쪽_사용:
        return True
    if 중단_요청됨():
        return False

    로그("문장부호 세트문장 동일 페이지 유지 처리 시작")
    hwp_run("MoveDocBegin")

    while True:
        if 중단_요청됨():
            return False

        시작위치 = hwp.GetPos()
        # 본문(리스트 0) 문단만 대상으로 한다. 표/글상자 등은 기존 컨트롤 처리와 충돌하지 않게 제외한다.
        if 시작위치[0] == 0:
            text = 현재문단_텍스트()
            if 세트문장_시작인가(text):
                if 세트문장_같은쪽_시도(시작위치, text) is False:
                    return False
                try:
                    hwp.SetPos(*시작위치)
                except Exception:
                    pass

        if not 다음_문단으로_진행():
            break

    로그(
        "문장부호 세트문장 동일 페이지 유지 완료 "
        f"(대상 {세트문장_통계['대상']} / 성공 {세트문장_통계['성공']} / "
        f"미해결 {세트문장_통계['실패']} / 줄간격 축소 {세트문장_통계['축소횟수']}회)"
    )
    return True


# ============================================================
# 문장 내 공백 정규화
#   1) 괄호 바로 안쪽 공백 제거: "( 내용 )" -> "(내용)"
#   2) 단어-쉼표-단어 구조에서 쉼표 앞 0칸 + 뒤 1칸: "도토리,만두" -> "도토리, 만두"
# ============================================================

괄호_안쪽_공백_패턴 = re.compile(r"(?<=\()[ \t\u00A0\u3000]+|[ \t\u00A0\u3000]+(?=\))")


def 전체_찾아바꾸기(찾을문자열, 바꿀문자열):
    """한글 AllReplace를 사용해 문서 전체(본문/표/글상자 등)를 치환한다.

    위치 오프셋을 직접 계산해서 Delete하는 방식보다 문자모양(run)이 갈라진
    HWP/HWPX에서도 안정적이다. HWP의 AllReplace가 캐럿 위치의 영향을 받는
    경우를 줄이기 위해 매 실행 전 문서 처음으로 이동한다.
    """
    if hwp is None or 찾을문자열 == 바꿀문자열:
        return False
    try:
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        hwp_run("MoveDocBegin")

        pset = hwp.HParameterSet.HFindReplace
        hwp.HAction.GetDefault("AllReplace", pset.HSet)
        pset.MatchCase = 0
        pset.AllWordForms = 0
        pset.SeveralWords = 0
        pset.UseWildCards = 0
        pset.WholeWordOnly = 0
        pset.Direction = hwp.FindDir("AllDoc")
        pset.FindString = 찾을문자열
        pset.ReplaceString = 바꿀문자열
        pset.ReplaceMode = 1
        pset.IgnoreMessage = 1
        pset.FindRegExp = 0
        pset.FindType = 1
        return bool(hwp.HAction.Execute("AllReplace", pset.HSet))
    except Exception as e:
        로그(f"문서 전체 찾아바꾸기 실패(무시): {찾을문자열!r} → {바꿀문자열!r} / {e}")
        return False


def 괄호_안쪽_공백_정리_AllReplace():
    """괄호 바로 안쪽 공백을 문서 전체에서 제거한다.

    '(   내용)'처럼 여러 칸인 경우도 없어질 때까지 반복한다.
    ASCII space 외에 NBSP/전각 공백도 처리한다.
    탭은 AllReplace 환경별 차이가 있어 문단 보정 함수에서도 한 번 더 처리한다.
    """
    총실행 = 0
    # HWP AllReplace는 일부 버전에서 실제 치환이 있었어도 반환값이 False가
    # 될 수 있으므로 반환값만 보고 반복을 중단하지 않는다.
    # ASCII 공백은 16칸부터 1칸까지 "정확한 문자열"을 긴 것부터 제거하여
    # 한 번에 여러 칸도 처리하고, NBSP/전각공백/탭도 별도로 정리한다.
    for 길이 in range(16, 0, -1):
        공백묶음 = " " * 길이
        if 전체_찾아바꾸기("(" + 공백묶음, "("):
            총실행 += 1
        if 전체_찾아바꾸기(공백묶음 + ")", ")"):
            총실행 += 1

    for 공백문자 in ("\u00A0", "\u3000", "\t"):
        # 동일 종류 공백이 여러 개 연속된 경우도 제거되도록 몇 차례 반복한다.
        for _ in range(4):
            if 전체_찾아바꾸기("(" + 공백문자, "("):
                총실행 += 1
            if 전체_찾아바꾸기(공백문자 + ")", ")"):
                총실행 += 1
    return 총실행


def 괄호_안쪽_공백_정리_문단_처리():
    """현재 문단에서 괄호 바로 안쪽 공백을 후방 보정한다.

    AllReplace가 특정 컨트롤/환경에서 놓친 경우를 위한 2차 안전장치다.
    """
    text = 현재문단_텍스트()
    if not text or "(" not in text or ")" not in text:
        return 0

    삭제구간 = [(m.start(), m.end()) for m in 괄호_안쪽_공백_패턴.finditer(text)]
    if not 삭제구간:
        return 0

    병합 = []
    for 시작, 끝 in sorted(삭제구간):
        if 병합 and 시작 <= 병합[-1][1]:
            병합[-1] = (병합[-1][0], max(병합[-1][1], 끝))
        else:
            병합.append((시작, 끝))

    문단_시작위치 = hwp.GetPos()
    삭제수 = 0
    try:
        for 시작, 끝 in reversed(병합):
            try:
                문단_범위_선택(문단_시작위치, 시작, 끝)
                hwp_run("Delete")
                삭제수 += (끝 - 시작)
            except Exception as e:
                로그(f"괄호 안쪽 공백 후방 보정 실패(무시): {e}")
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
    finally:
        try:
            hwp.SetPos(*문단_시작위치)
        except Exception:
            pass
    return 삭제수


def 쉼표_공백_보정_대상(text):
    """단어와 단어 사이 쉼표 주변 공백을 표준화할 구간을 반환한다.

    규칙:
      - 쉼표 앞 공백: 0칸
      - 쉼표 뒤 공백: 정확히 ASCII 공백 1칸

    숫자 천단위(1,000)는 건드리지 않는다.

    반환값: [(시작, 끝), ...]
      시작~끝 구간을 `", "`로 교체한다.

      - "도토리,만두"     -> "도토리, 만두"
      - "도토리 ,만두"    -> "도토리, 만두"
      - "도토리,  만두"   -> "도토리, 만두"
      - "도토리  ,  만두" -> "도토리, 만두"
    """
    결과 = []
    if not text or "," not in text:
        return 결과

    공백문자 = " \t\u00A0\u3000"
    for 쉼표위치, ch in enumerate(text):
        if ch != ",":
            continue

        # 쉼표 왼쪽 공백을 건너뛰어 실제 앞 문자를 찾는다.
        왼쪽 = 쉼표위치 - 1
        while 왼쪽 >= 0 and text[왼쪽] in 공백문자:
            왼쪽 -= 1
        앞문자위치 = 왼쪽
        if 앞문자위치 < 0:
            continue

        # 쉼표 오른쪽 공백을 건너뛰어 실제 다음 문자를 찾는다.
        오른쪽 = 쉼표위치 + 1
        while 오른쪽 < len(text) and text[오른쪽] in 공백문자:
            오른쪽 += 1
        if 오른쪽 >= len(text):
            continue

        # 문자 단어 사이의 쉼표만 대상으로 한다.
        # 따라서 1,000 같은 숫자 천단위 표기는 제외된다.
        if not (text[앞문자위치].isalpha() and text[오른쪽].isalpha()):
            continue

        시작 = 앞문자위치 + 1
        끝 = 오른쪽
        if text[시작:끝] == ", ":
            continue
        결과.append((시작, 끝))

    return 결과


def 쉼표_공백_정리_문단_처리():
    """현재 문단의 단어 사이 쉼표를 `단어, 단어` 형식으로 정규화한다."""
    text = 현재문단_텍스트()
    수정구간 = 쉼표_공백_보정_대상(text)
    if not 수정구간:
        return 0

    문단_시작위치 = hwp.GetPos()
    수정수 = 0
    try:
        # 오른쪽부터 처리하여 앞쪽 문자 위치가 변하지 않게 한다.
        for 시작, 끝 in reversed(수정구간):
            try:
                기존길이 = 끝 - 시작
                if 기존길이 > 0:
                    문단_범위_선택(문단_시작위치, 시작, 끝)
                    hwp_run("Delete")
                else:
                    hwp.SetPos(
                        문단_시작위치[0],
                        문단_시작위치[1],
                        문단_시작위치[2] + 시작,
                    )
                텍스트_삽입(", ")
                수정수 += 1
            except Exception as e:
                로그(f"쉼표 공백 보정 실패(무시): {e}")
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
    finally:
        try:
            hwp.SetPos(*문단_시작위치)
        except Exception:
            pass
    return 수정수


# v1.10 함수명을 호출하는 기존 경로와의 호환성 유지
def 쉼표_앞_공백_보정_대상(text):
    return 쉼표_공백_보정_대상(text)


def 쉼표_앞_공백_정리_문단_처리():
    return 쉼표_공백_정리_문단_처리()


def 단어사이_연속공백_정리_대상(text):
    """문단 안에서 단어 사이의 연속 공백(2칸 이상)을 1칸으로 줄일 구간을 찾는다.

    문단 맨 앞의 들여쓰기 공백(□/ㅇ/- 등 항목 위치나 세트문장 후속 판정에
    쓰이는 선행 공백)은 이 정리의 대상이 아니므로 건드리지 않고, 실제
    내용이 시작된 뒤에 나오는 연속 공백만 대상으로 한다.
    """
    결과 = []
    if not text:
        return 결과
    벗긴텍스트 = text.lstrip(" ")
    선행공백_길이 = len(text) - len(벗긴텍스트)
    i = 선행공백_길이
    n = len(text)
    while i < n:
        if text[i] == " ":
            시작 = i
            while i < n and text[i] == " ":
                i += 1
            if i - 시작 > 1:
                결과.append((시작, i))
        else:
            i += 1
    return 결과


def 단어사이_연속공백_정리_문단_처리():
    """현재 문단에서 단어 사이의 연속 공백(2칸 이상)을 1칸으로 줄인다."""
    text = 현재문단_텍스트()
    수정구간 = 단어사이_연속공백_정리_대상(text)
    if not 수정구간:
        return 0

    문단_시작위치 = hwp.GetPos()
    수정수 = 0
    try:
        # 오른쪽부터 처리하여 앞쪽 문자 위치가 변하지 않게 한다.
        for 시작, 끝 in reversed(수정구간):
            try:
                문단_범위_선택(문단_시작위치, 시작, 끝)
                hwp_run("Delete")
                텍스트_삽입(" ")
                수정수 += 1
            except Exception as e:
                로그(f"연속 공백 정리 실패(무시): {e}")
                try:
                    hwp_run("Cancel")
                except Exception:
                    pass
    finally:
        try:
            hwp.SetPos(*문단_시작위치)
        except Exception:
            pass
    return 수정수


def 문장내_공백_정규화_전체_적용():
    """괄호 안쪽 공백 + 단어 사이 쉼표 공백 + 단어 사이 연속 공백을 문서 전체에 적용한다."""
    if 중단_요청됨():
        return False

    로그("문장 내 공백 정규화 시작")

    # 1) 괄호 공백은 HWP 자체 AllReplace로 먼저 처리한다.
    #    문자 런/서식 경계를 넘는 경우에도 직접 좌표 삭제보다 안정적이다.
    allreplace_실행수 = 괄호_안쪽_공백_정리_AllReplace()

    # 2) 문단 단위 안전 보정 + 쉼표 공백 보정(앞 0칸 / 뒤 1칸) + 연속 공백 정리(2칸 이상 -> 1칸).
    #    기존 v1.7의 `list id == 0` 제한을 제거하여 접근 가능한 모든 문단에 적용한다.
    hwp_run("MoveDocBegin")
    괄호삭제수 = 0
    쉼표수정수 = 0
    연속공백수정수 = 0
    방문문단수 = 0
    정체횟수 = 0

    while True:
        if 중단_요청됨():
            return False

        시작위치 = hwp.GetPos()
        방문문단수 += 1

        괄호삭제수 += 괄호_안쪽_공백_정리_문단_처리()
        쉼표수정수 += 쉼표_공백_정리_문단_처리()
        연속공백수정수 += 단어사이_연속공백_정리_문단_처리()

        if not 다음_문단으로_진행():
            break

        if hwp.GetPos() == 시작위치:
            정체횟수 += 1
            if 정체횟수 >= 2:
                break
        else:
            정체횟수 = 0

    로그(
        "문장 내 공백 정규화 완료 "
        f"(방문 문단 {방문문단수}개 / 괄호 AllReplace {allreplace_실행수}회 / "
        f"괄호 후방삭제 {괄호삭제수}자 / 쉼표 공백 {쉼표수정수}건 / 연속 공백 {연속공백수정수}건)"
    )
    return True


# 이전 함수명을 호출하는 외부/기존 코드와의 호환성 유지
def 괄호_안쪽_공백_정리_전체_적용():
    return 문장내_공백_정규화_전체_적용()


def 문장부호_뒤_공백_보정_문단_처리():
    text = 현재문단_텍스트()
    if not text:
        return False
    마커_끝 = 문장부호_마커_끝위치(text)
    if 마커_끝 is None or 마커_끝 >= len(text) or text[마커_끝] == " ":
        return False

    문단_시작위치 = hwp.GetPos()
    try:
        hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2] + 마커_끝)
        텍스트_삽입(" ")
        return True
    except Exception as e:
        로그(f"문장부호 뒤 공백 보정 실패(무시): {e}")
        return False
    finally:
        try:
            hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2])
        except Exception:
            pass

def 문장부호_뒤_공백_보정_전체_적용():
    if 중단_요청됨():
        return False
    로그("문장부호 뒤 공백 보정 시작")
    hwp_run("MoveDocBegin")
    총_적용_횟수 = 0

    while True:
        if 중단_요청됨():
            return False
        if 문장부호_뒤_공백_보정_문단_처리():
            총_적용_횟수 += 1
        if not 다음_문단으로_진행():
            break

    로그(f"문장부호 뒤 공백 보정 완료 (총 {총_적용_횟수}건)")
    return True

def 현재문단_텍스트():
    try:
        hwp.Run("MoveParaBegin")
        문단시작위치 = hwp.GetPos()
        hwp.Run("MoveSelParaEnd")
        hwp.InitScan(option=None, Range=0xff, spara=None, spos=None, epara=None, epos=None)
        try:
            _, text = hwp.GetText()
        finally:
            hwp.ReleaseScan()
        hwp.Run("Cancel")
        hwp.SetPos(문단시작위치[0], 문단시작위치[1], 문단시작위치[2])
        return text or ""
    except Exception:
        try:
            hwp.Run("Cancel")
        except Exception:
            pass
        return ""

def 실제_엔터_포함(text):
    return ("\n" in text or "\r" in text) if text else False

def 두_위치_사이_줄바꿈_문자인가(시작pos, 끝pos):
    try:
        hwp.SetPos(시작pos[0], 시작pos[1], 시작pos[2])
        hwp_run("MoveSelRight")
        hwp.InitScan(option=None, Range=0xff, spara=None, spos=None, epara=None, epos=None)
        try:
            _, text = hwp.GetText()
        finally:
            hwp.ReleaseScan()
        hwp_run("Cancel")
        hwp.SetPos(시작pos[0], 시작pos[1], 시작pos[2])
        return 실제_엔터_포함(text)
    except Exception:
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        return False

def 문장부호_대상문장인가():
    text = 현재문단_텍스트()
    return bool(text and 문장부호_시작인가(text))

def 현재_화면줄_텍스트():
    try:
        hwp_run("MoveLineBegin")
        줄시작위치 = hwp.GetPos()
        hwp_run("MoveSelLineEnd")
        hwp.InitScan(option=None, Range=0xff, spara=None, spos=None, epara=None, epos=None)
        try:
            _, text = hwp.GetText()
        finally:
            hwp.ReleaseScan()
        hwp_run("Cancel")
        hwp.SetPos(줄시작위치[0], 줄시작위치[1], 줄시작위치[2])
        return text or ""
    except Exception:
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        return ""

문장부호_최대_처리_줄수 = 6

def 다음_줄_판정(현재줄끝위치):
    hwp_run("MoveNextChar")
    다음위치 = hwp.GetPos()
    if 다음위치 == 현재줄끝위치:
        return "없음", 다음위치
    if 다음위치[0] != 현재줄끝위치[0] or 다음위치[1] != 현재줄끝위치[1]:
        return "끝남", 다음위치
    if 두_위치_사이_줄바꿈_문자인가(현재줄끝위치, 다음위치):
        return "끝남", 다음위치
    return "계속", 다음위치

def 줄_목록_수집(시작위치, 최대줄수=None):
    if 최대줄수 is None:
        최대줄수 = 문장부호_최대_처리_줄수
    줄목록 = []
    hwp.SetPos(시작위치[0], 시작위치[1], 시작위치[2])
    hwp_run("MoveLineBegin")
    앵커 = hwp.GetPos()

    while len(줄목록) < 최대줄수:
        if 중단_요청됨():
            return 줄목록, True
        hwp.SetPos(앵커[0], 앵커[1], 앵커[2])
        줄텍스트 = 현재_화면줄_텍스트()
        if not 줄텍스트:
            return 줄목록, True
        줄목록.append((앵커, 줄텍스트))

        hwp.SetPos(앵커[0], 앵커[1], 앵커[2])
        hwp_run("MoveLineEnd")
        줄끝 = hwp.GetPos()
        분류, 다음위치 = 다음_줄_판정(줄끝)
        if 분류 in ("없음", "끝남"):
            return 줄목록, True
        앵커 = 다음위치

    return 줄목록, False

def 문장부호_줄병합_시도():
    if 중단_요청됨():
        return False
    원래위치 = hwp.GetPos()
    try:
        if not 문장부호_대상문장인가():
            return True

        hwp_run("MoveLineBegin")
        줄목록, 끝까지_확인됨 = 줄_목록_수집(hwp.GetPos())
        if len(줄목록) < 2 or not 끝까지_확인됨:
            return True

        마지막줄_시작, 마지막줄_텍스트 = 줄목록[-1]
        if len(마지막줄_텍스트) > 문장부호_2줄_기준글자수:
            return True

        문장부호_통계["대상"] += 1
        압축대상_시작, _ = 줄목록[-2]
        조정횟수 = 0
        최대조정 = 40
        해결됨 = False
        새_줄목록 = 줄목록

        while 조정횟수 < 최대조정:
            if 중단_요청됨():
                return False
            hwp.SetPos(압축대상_시작[0], 압축대상_시작[1], 압축대상_시작[2])
            hwp_run("MoveLineEnd")
            hwp_run("MoveSelLineBegin")
            hwp_run("CharShapeSpacingDecrease")
            색상_적용_현재선택()
            hwp_run("Cancel")
            조정횟수 += 1

            새_줄목록, 새_끝까지_확인됨 = 줄_목록_수집(원래위치)
            if not 새_끝까지_확인됨:
                break
            if len(새_줄목록) < len(줄목록):
                해결됨 = True
                break

        if 해결됨:
            문장부호_통계["성공"] += 1
            if len(새_줄목록) >= 2:
                hwp.SetPos(원래위치[0], 원래위치[1], 원래위치[2])
                문장부호_줄병합_시도()
        else:
            문장부호_통계["실패"] += 1
            검수_문제_기록(현재_처리파일, 줄목록[0][1].strip() + " / " + 마지막줄_텍스트.strip())
        return True
    finally:
        try:
            hwp.SetPos(원래위치[0], 원래위치[1], 원래위치[2])
            hwp.Run("MoveParaEnd")
        except Exception:
            pass

def 본문_문장부호_처리():
    hwp_run("MoveDocBegin")
    끝위치 = 끝위치추출()
    직전위치 = None
    정체횟수 = 0

    while hwp.GetPos() != 끝위치:
        if 중단_요청됨():
            return False
        현재위치 = hwp.GetPos()
        if 현재위치 == 직전위치:
            정체횟수 += 1
            if 정체횟수 == 1:
                try:
                    hwp_run("MoveParaEnd")
                    hwp_run("MoveNextChar")
                except Exception:
                    pass
                직전위치 = 현재위치
                continue
            return True
        else:
            정체횟수 = 0
        직전위치 = 현재위치
        문장부호_줄병합_시도()
        hwp_run("MoveLineEnd")
        hwp_run("MoveNextChar")
    return True

# ============================================================
# 표 및 컨트롤 서식
# ============================================================

def 현재_셀_주소_행번호():
    """KeyIndicator의 '(A1)' 또는 'A1' 셀주소를 파싱한다."""
    try:
        정보 = hwp.KeyIndicator()
        if not 정보:
            return None, None
        원문 = str(정보[-1]).strip()
        일치 = re.search(r"\(?([A-Za-z]+)(\d+)\)?", 원문)
        if not 일치:
            return None, None
        주소 = f"{일치.group(1).upper()}{일치.group(2)}"
        return 주소, int(일치.group(2))
    except Exception:
        return None, None


def 현재_셀_행번호():
    _, 행번호 = 현재_셀_주소_행번호()
    return 행번호

def 표_헤더서식_현재셀_처리():
    """현재 셀의 전체 텍스트에 헤더/본문 폰트·크기·굵기를 적용한다."""
    _, 행번호 = 현재_셀_주소_행번호()
    if 행번호 is None:
        return False

    try:
        hwp_run("MoveListBegin")
        hwp_run("MoveSelListEnd")
        if 행번호 == 1:
            문자모양_적용_현재선택(
                폰트=표_헤더서식_헤더_폰트,
                크기_pt=표_헤더서식_헤더_크기,
                굵게=표_헤더서식_헤더_굵게,
            )
        else:
            문자모양_적용_현재선택(
                폰트=표_헤더서식_본문_폰트,
                크기_pt=표_헤더서식_본문_크기,
                굵게=표_헤더서식_본문_굵게,
            )
        hwp_run("Cancel")
        hwp_run("MoveListBegin")
        return True
    except Exception as e:
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        로그(f"표 셀 문자서식 적용 실패(무시): {e}")
        return False


def 표_헤더서식_현재줄_처리():
    return 표_헤더서식_현재셀_처리()

def 표_헤더서식_전체_적용():
    """표 안의 각 셀에 표준 문자서식을 적용한다.

    v1.11: 기존에는 HeadCtrl/Next로 표 컨트롤을 찾은 뒤
    ``hwp.SelectCtrl(ctrl.GetCtrlInstID(), 1)``로 첫 셀에 진입하려 했으나,
    이 메서드는 이 스크립트가 사용하는 win32com 원시 COM 객체에는 없어
    모든 표에서 예외가 발생하며 표 서식 적용이 통째로 실패했다
    ("표 N 첫 셀 진입 실패(무시): HwpFrame.HwpObject.SelectCtrl").
    표/글상자 등 각 컨트롤 내부는 문서 안에서 고유한 리스트 번호를
    가지므로, ``컨트롤_내부_자간조정()``과 동일하게 리스트 번호를
    1씩 늘려가며 SetPos로 직접 진입하는, 이미 검증된 방식으로 대체한다.
    표가 아닌 영역(글상자 등)은 ``표_헤더서식_현재셀_처리()``가 셀
    주소를 못 찾으면 그대로 건너뛰므로 안전하다.
    """
    if 중단_요청됨():
        return False

    로그("표 헤더/본문 서식 적용 시작")
    셀수 = 0
    실패수 = 0
    방문영역수 = 0

    area = 1
    while True:
        if 중단_요청됨():
            return False
        area += 1
        try:
            hwp.SetPos(area, 0, 0)
        except Exception:
            break
        if hwp.GetPos()[0] == 0:
            break
        방문영역수 += 1

        if 표_헤더서식_현재셀_처리():
            셀수 += 1
        else:
            실패수 += 1

    로그(f"표 헤더/본문 서식 적용 완료 (검사한 컨트롤 영역 {방문영역수}개 / 적용된 표 셀 {셀수}개 / 대상 아님·실패 {실패수}건)")
    return True

def 컨트롤_내부_자간조정():
    area = 1
    while True:
        if 중단_요청됨():
            return False
        area += 1
        hwp.SetPos(area, 0, 0)
        if hwp.GetPos()[0] == 0:
            break
        while True:
            if 중단_요청됨():
                return False
            시작위치 = hwp.GetPos()
            # 표/글상자/각주/미주 내부 텍스트도 본문과 동일한 공백 규칙을 적용한다.
            괄호_안쪽_공백_정리_문단_처리()
            쉼표_공백_정리_문단_처리()
            result = 자간자동조정(최대시도=자간_최대시도_표)
            if result is False:
                return False
            hwp_run("MoveLineEnd")
            hwp_run("MoveNextChar")
            if hwp.GetPos()[0] != 0 and hwp.GetPos()[0] >= area:
                area = hwp.GetPos()[0]
            if hwp.GetPos() == 시작위치:
                break
    return True

def 컨트롤_내부_문장부호_처리():
    area = 1
    while True:
        if 중단_요청됨():
            return False
        area += 1
        hwp.SetPos(area, 0, 0)
        if hwp.GetPos()[0] == 0:
            break
        while True:
            if 중단_요청됨():
                return False
            시작위치 = hwp.GetPos()
            문장부호_줄병합_시도()
            hwp_run("MoveLineEnd")
            hwp_run("MoveNextChar")
            if hwp.GetPos()[0] != 0 and hwp.GetPos()[0] >= area:
                area = hwp.GetPos()[0]
            if hwp.GetPos() == 시작위치:
                break
    return True

def 끝위치추출():
    hwp_run("MoveDocEnd")
    end_pos = hwp.GetPos()
    hwp_run("MoveDocBegin")
    return end_pos

def 다음_문단으로_진행():
    """현재 문단을 벗어나 다음 위치로 이동한다.

    문서 내용이 처리 중 삽입/삭제되어도 미리 저장한 문서 끝 좌표에 의존하지 않는다.
    더 이상 이동할 수 없으면 False를 반환한다.
    """
    hwp_run("MoveParaEnd")
    문단끝 = hwp.GetPos()
    hwp_run("MoveNextChar")
    다음위치 = hwp.GetPos()
    return 다음위치 != 문단끝

def 저장파일명(파일):
    path = Path(파일)
    return str(path.with_name(path.stem + "(자간조정)" + path.suffix))

# ============================================================
# 문서 처리 파이프라인
# ============================================================

def 문서_처리_1회(파일명, 문장부호기능=True, 회차=1, 총회차=2):
    """현재 열려 있는 문서에 전체 처리 파이프라인을 1회 적용한다.

    1회차에서 발생한 줄바꿈/페이지 재배치/자간 변경을 2회차에서 다시
    처음부터 검사할 수 있도록 각 회차 시작 시 문서 처음으로 이동한다.
    저장은 이 함수에서 하지 않고 모든 회차가 끝난 뒤 한 번만 수행한다.

    v1.11:
    - 1회차: 공백 정규화 → 표준서식 → 문두라벨/괄호 처리까지 포함해
      전체 파이프라인을 수행한다.
    - 2회차: 공백 정규화 → 표준서식 → 문두라벨/괄호 처리는 건너뛰고,
      본문 자간 자동조정 → 문장부호 줄병합 자간축소 → 표/컨트롤 내부
      처리(표 헤더/본문 서식 포함) → 세트문장 페이지 맞춤만 수행한다.
      앞의 세 단계는 텍스트 내용만으로 결과가 정해지는 서식이라
      1회차에서 이미 확정되며 다시 실행해도 같은 값이 나오므로, 2회차
      에서 또 적용하는 것은 결과에 영향 없이 시간만 잡아먹는 중복이었다.
      2회차는 1회차 처리로 새로 생긴 줄바꿈/페이지 배치를 자간·문장부호·
      표·세트문장 단계로 다시 잡아준다.
    - 각 단계 내부에서 글자 하나하나를 옮기며 선택하던 부분은
      SelectText 한 번 호출로 바꿔 불필요한 COM 호출만 줄였다(결과에는
      영향 없는 순수 효율화).
    """
    if 중단_요청됨():
        return False

    로그("")
    로그("-" * 45)
    로그(f"전체 처리 {회차}/{총회차}회차 시작")
    로그("-" * 45)
    상태(f"{파일명} : 전체 처리 {회차}/{총회차}회차 시작")

    # 회차 시작 위치를 항상 문서 처음으로 통일한다.
    try:
        hwp_run("Cancel")
    except Exception:
        pass
    hwp_run("MoveDocBegin")

    if 회차 == 1:
        # 0. 문장 내 공백을 먼저 정규화한다.
        #    - 괄호 바로 안쪽 공백 제거: "( 6~16번)" -> "(6~16번)"
        #    - 단어 사이 쉼표 앞 0칸/뒤 1칸: "도토리,만두" -> "도토리, 만두"
        #    뒤의 라벨/자간/서식 판정은 정규화된 텍스트를 기준으로 수행한다.
        상태(f"{파일명} [{회차}/{총회차}] : 문장 내 공백 정규화")
        if 문장내_공백_정규화_전체_적용() is False:
            return False

        # 1. 표준서식 적용
        if 표준서식_사용:
            상태(f"{파일명} [{회차}/{총회차}] : 문장부호 뒤 공백 보정")
            if 문장부호_뒤_공백_보정_전체_적용() is False:
                return False
            상태(f"{파일명} [{회차}/{총회차}] : 표준서식 적용")
            if 표준서식_전체_적용() is False:
                return False

        # 2. 문두 라벨(콜론/괄호) 굵게 및 부연설명 괄호 축소
        if 괄호_축소_사용 or 괄호_라벨_볼드_사용:
            상태(f"{파일명} [{회차}/{총회차}] : 문두 라벨/괄호 처리")
            if 괄호_텍스트_크기_축소_전체_적용() is False:
                return False
    else:
        로그(f"{회차}회차: 공백정규화/표준서식/문두라벨·괄호 단계는 생략 - 자간조정·문장부호·표/컨트롤·세트문장 단계만 수행")

    # 3. 본문 자간 자동조정 — 회차와 무관하게 항상 실행하는 핵심 기능
    상태(f"{파일명} [{회차}/{총회차}] : 기존 자간 자동조정")
    hwp_run("MoveDocBegin")
    if 본문_기존자간조정() is False:
        return False

    # 4. 문장부호 줄병합 자간 축소 — 회차와 무관하게 항상 실행
    if 표준서식_사용 and 문장부호기능:
        상태(f"{파일명} [{회차}/{총회차}] : 문장부호 2줄 검사")
        if 본문_문장부호_처리() is False:
            return False

    # 5. 표/컨트롤 내부 처리 — 회차와 무관하게 항상 실행
    if 표준서식_사용 and 표_헤더서식_사용:
        상태(f"{파일명} [{회차}/{총회차}] : 표 헤더/본문 서식 적용")
        if 표_헤더서식_전체_적용() is False:
            return False

    상태(f"{파일명} [{회차}/{총회차}] : 표/글상자 등 처리")
    if 컨트롤_내부_자간조정() is False:
        return False

    if 표준서식_사용 and 문장부호기능:
        if 컨트롤_내부_문장부호_처리() is False:
            return False

    # 6. 문장부호 세트문장 동일 페이지 유지 — 회차와 무관하게 항상 실행
    # 모든 자간/서식/컨트롤 처리가 끝난 최종 레이아웃을 기준으로 판단한다.
    if 세트문장_같은쪽_사용:
        상태(f"{파일명} [{회차}/{총회차}] : 문장부호 세트문장 페이지 맞춤")
        if 세트문장_같은쪽_전체_적용() is False:
            return False

    # 다음 회차가 항상 문서 처음부터 시작할 수 있도록 위치를 복원한다.
    try:
        hwp_run("Cancel")
    except Exception:
        pass
    hwp_run("MoveDocBegin")

    로그(f"전체 처리 {회차}/{총회차}회차 완료")
    return True


def 문서_전체_자간_초기화():
    """문서 전체(본문 + 표/글상자 등 컨트롤 내부)의 자간을 0%로 되돌린다.

    이 프로그램을 이미 한 번 이상 돌렸거나 사용자가 손으로 자간을 만져둔
    문서를 다시 처리하면, 잔여 자간값 위에 압축이 계속 누적되어 HWP의
    자간 조정 가능 범위(최솟값)에 금방 닿아버린다. 그러면 겉보기엔
    "본문 자간 자동조정"이 여러 번 시도해도 실제로는 더 줄어들 여지가
    없어 단어 분리가 그대로 남는다. 2회차 처리를 시작하기 전, 문서
    전체를 한 번만 0%로 되돌려 항상 최대한의 압축 여유를 확보한 채로
    자간조정을 시작하도록 한다. 회차마다 반복하면 1회차의 압축 결과가
    지워지므로 문서당 정확히 한 번만 호출해야 한다.
    """
    if hwp is None:
        return False
    try:
        hwp_run("Cancel")
        hwp_run("MoveDocBegin")
        hwp_run("MoveSelDocEnd")
        문자모양_적용_현재선택(자간=0)
        hwp_run("Cancel")

        area = 1
        while True:
            if 중단_요청됨():
                return False
            area += 1
            hwp.SetPos(area, 0, 0)
            if hwp.GetPos()[0] == 0:
                break
            hwp_run("MoveListBegin")
            hwp_run("MoveSelListEnd")
            문자모양_적용_현재선택(자간=0)
            hwp_run("Cancel")

        hwp_run("MoveDocBegin")
        return True
    except Exception as e:
        로그(f"문서 전체 자간 초기화 실패(무시): {e}")
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        return False


def 문서_처리(파일, index, total, 문장부호기능=True):
    global hwp, 현재_처리파일
    if 중단_요청됨():
        return False

    현재_처리파일 = 파일
    파일명 = Path(파일).name
    상태(f"{index}/{total} : {파일명}")
    로그("")
    로그(f"[{index}/{total}] {파일명}")

    확장자 = Path(파일).suffix.lower()
    확장자명 = "hwpx" if 확장자 == ".hwpx" else "hwp"

    파일경로 = Path(파일)
    if not 파일경로.is_file():
        raise FileNotFoundError(f"문서를 찾을 수 없습니다: {파일}")
    if 확장자 not in (".hwp", ".hwpx"):
        raise ValueError(f"지원하지 않는 파일 형식입니다: {확장자 or '(확장자 없음)'}")

    로그(f"문서 열기: {파일}")
    열린결과 = hwp.Open(str(파일경로), Format=확장자명.upper(), arg="")
    if 열린결과 is False:
        raise RuntimeError(f"한글에서 문서를 열지 못했습니다: {파일}")

    원본_뷰어_문서표시(파일, 확장자명)
    비교보기_임베드_재확인()

    # 잔여 자간(이전 실행/수동 편집으로 남은 값)이 있으면 압축 여유가
    # 줄어드니, 두 회차를 시작하기 전 문서 전체를 한 번만 0%로 초기화한다.
    상태(f"{파일명} : 자간 초기화")
    if 문서_전체_자간_초기화() is False:
        return False

    # 전체 파이프라인을 총 2회 수행한다.
    # 1회차 결과에서 새로 생긴 줄바꿈/페이지 배치를 2회차가 다시 검사한다.
    총회차 = 2
    for 회차 in range(1, 총회차 + 1):
        if 중단_요청됨():
            return False
        if 문서_처리_1회(파일명, 문장부호기능, 회차, 총회차) is False:
            return False

    # 모든 2회 처리가 끝난 뒤 최종 결과만 한 번 저장한다.
    if 중단_요청됨():
        return False

    저장파일 = 저장파일명(파일)
    상태(f"{파일명} : 2회 처리 완료 / 최종 저장 중")
    문서_format = 확장자명.upper()
    저장결과 = hwp.SaveAs(Path=저장파일, Format=문서_format, arg="")
    if 저장결과 is False:
        raise RuntimeError(f"문서 저장에 실패했습니다: {저장파일}")
    로그(f"전체 처리 2회 완료")
    로그(f"저장 완료: {저장파일}")
    return True

# ============================================================
# 백그라운드 작업 실행 스레드
# ============================================================

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
    세트문장같은쪽=True
):
    global hwp, 색상_설정, 비교보기_사용, 비교보기_좌측_프레임_hwnd, 비교보기_우측_프레임_hwnd
    global 작업_hwp_hwnd, 자동닫기_설정, 표준서식_사용, 검수_사용, 검수_문제목록
    global 문장부호_2줄_기준글자수, 문장부호_통계, 자간_최대시도_본문, 자간_최대시도_표
    global 세트문장_같은쪽_사용, 세트문장_통계
    global 괄호_축소_사용, 괄호_라벨_볼드_사용
    global 표준서식_여백_사용, 표준서식_장평_사용, 표준서식_줄간격_사용, 표준서식_제목_사용
    global 표준서식_일자담당자_사용, 표준서식_기호_사용, 표준서식_제목_굵게, 표준서식_일자담당자_굵게
    global 표준서식_기호_굵게, 표준서식_문단위간격_사용, 표준서식_문단위간격_box_pt
    global 표준서식_문단위간격_circle_pt, 표준서식_문단위간격_note_pt, 표_헤더서식_사용

    if 표준서식_세부 is None:
        표준서식_세부 = {}
    if 표준서식_문단위간격_pt is None:
        표준서식_문단위간격_pt = {}

    try:
        total = len(파일목록)
        중단_event.clear()
        색상_설정 = 색상
        비교보기_사용 = 비교보기
        비교보기_좌측_프레임_hwnd = 좌측_프레임_hwnd
        비교보기_우측_프레임_hwnd = 우측_프레임_hwnd
        자동닫기_설정 = 자동닫기
        표준서식_사용 = 표준서식
        검수_사용 = 검수
        검수_문제목록 = []
        문장부호_2줄_기준글자수 = 둘째줄기준글자수
        자간_최대시도_본문 = 본문재시도횟수
        자간_최대시도_표 = 표재시도횟수
        괄호_축소_사용 = 괄호축소
        괄호_라벨_볼드_사용 = 괄호라벨굵게
        세트문장_같은쪽_사용 = bool(세트문장같은쪽)

        표준서식_여백_사용 = 표준서식_세부.get("std_margin", 표준서식_여백_사용)
        표준서식_장평_사용 = 표준서식_세부.get("std_ratio", 표준서식_장평_사용)
        표준서식_줄간격_사용 = 표준서식_세부.get("std_linespacing", 표준서식_줄간격_사용)
        표준서식_제목_사용 = 표준서식_세부.get("std_title", 표준서식_제목_사용)
        표준서식_일자담당자_사용 = 표준서식_세부.get("std_dateinfo", 표준서식_일자담당자_사용)
        표준서식_기호_사용 = 표준서식_세부.get("std_symbols", 표준서식_기호_사용)
        표준서식_제목_굵게 = 표준서식_세부.get("std_title_bold", 표준서식_제목_굵게)
        표준서식_일자담당자_굵게 = 표준서식_세부.get("std_dateinfo_bold", 표준서식_일자담당자_굵게)

        표준서식_기호_굵게 = {
            "□": 표준서식_세부.get("std_symbol_box_bold", 표준서식_기호_굵게["□"]),
            "ㅇ": 표준서식_세부.get("std_symbol_o_bold", 표준서식_기호_굵게["ㅇ"]),
            "-": 표준서식_세부.get("std_symbol_dash_bold", 표준서식_기호_굵게["-"]),
            "※": 표준서식_세부.get("std_symbol_note_bold", 표준서식_기호_굵게["※"]),
        }

        표준서식_문단위간격_사용 = 표준서식_세부.get("std_parspace", 표준서식_문단위간격_사용)
        표준서식_문단위간격_box_pt = 표준서식_문단위간격_pt.get("std_parspace_box", 표준서식_문단위간격_box_pt)
        표준서식_문단위간격_circle_pt = 표준서식_문단위간격_pt.get("std_parspace_circle", 표준서식_문단위간격_circle_pt)
        표준서식_문단위간격_note_pt = 표준서식_문단위간격_pt.get("std_parspace_note", 표준서식_문단위간격_note_pt)
        표_헤더서식_사용 = 표준서식_세부.get("std_table_header", 표_헤더서식_사용)

        문장부호_통계 = {"대상": 0, "성공": 0, "실패": 0}
        세트문장_통계 = {"대상": 0, "성공": 0, "실패": 0, "축소횟수": 0}

        원본_뷰어_분리()
        작업창_분리()

        상태("AutomationModule 확인 중...")
        보안모듈_초기화()

        if 중단_요청됨():
            gui_queue.put(("stopped", None))
            return

        상태("한글 2020 시작 중...")
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

        for index, 파일 in enumerate(파일목록, 1):
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
                traceback.print_exc()
                로그(f"문서 처리 오류: {파일}")
                gui_queue.put(("document_error", str(파일), str(e)))

        로그("=" * 45)
        로그(f"문장부호 줄병합 자간축소 통계(2회 누적): 대상 {문장부호_통계['대상']}건 (성공 {문장부호_통계['성공']}/실패 {문장부호_통계['실패']})")
        if 세트문장_같은쪽_사용:
            로그(
                f"세트문장 페이지 맞춤 통계(2회 누적): 대상 {세트문장_통계['대상']}건 "
                f"(성공 {세트문장_통계['성공']}/미해결 {세트문장_통계['실패']}, "
                f"줄간격 축소 {세트문장_통계['축소횟수']}회)"
            )

        if 검수_사용:
            if 검수_문제목록:
                로그("=" * 45)
                로그(f"검수 결과: 자간축소 미해결 문단 {len(검수_문제목록)}건")
                for 항목 in 검수_문제목록:
                    p = 항목["page"] if 항목["page"] is not None else "?"
                    로그(f"  - [{Path(항목['file']).name} / {p}페이지] {항목['text']}")
            else:
                로그("검수 결과: 자간축소 미해결 문단 없음")

        if 중단_요청됨():
            상태("작업 중단")
            gui_queue.put(("stopped", None))
        else:
            상태("모든 작업 완료")
            gui_queue.put(("finished", 성공, 실패))

    except Exception as e:
        traceback.print_exc()
        gui_queue.put(("fatal_error", str(e)))
    finally:
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

# ============================================================
# GUI 클래스
# ============================================================

class HwpAutoDocFitGUI:

    def __init__(self, root):
        self.root = root
        self.files = []
        self.worker = None
        self.running = False
        self.closing = False

        self.compare_toplevel = None
        self.compare_left_frame = None
        self.compare_right_frame = None

        root.title(f"{APP_NAME} v{APP_VERSION}")
        root.geometry("552x637")
        root.minsize(420, 480)
        root.resizable(True, True)

        style = ttk.Style()
        try:
            style.theme_use("vista")
        except Exception:
            pass

        try:
            style.configure("Start.TButton", foreground="#0000FF")
            style.map("Start.TButton", foreground=[("disabled", "#A0A0A0"), ("active", "#0000CC")])
        except Exception:
            pass

        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Header
        header = ttk.Frame(root, padding=(10, 6, 10, 2))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text=APP_NAME, font=("맑은 고딕", 13, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="한글 2020 HWP / HWPX 자동 자간 조정").grid(row=1, column=0, sticky="w")

        # Main
        main = ttk.Frame(root, padding=(10, 0, 10, 0))
        main.grid(row=1, column=0, sticky="nsew")
        main.grid_rowconfigure(0, weight=3)
        main.grid_rowconfigure(2, weight=2)
        main.grid_columnconfigure(0, weight=1)

        file_frame = ttk.LabelFrame(main, text="문서", padding=5)
        file_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 3))
        file_frame.grid_rowconfigure(1, weight=1)
        file_frame.grid_columnconfigure(0, weight=1)

        self.drop_label = ttk.Label(file_frame, text="HWP / HWPX 파일 또는 폴더를 여기로 끌어다 놓으세요", anchor="center")
        self.drop_label.grid(row=0, column=0, sticky="ew", pady=(0, 3))
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.파일_드롭)

        list_frame = ttk.Frame(file_frame)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_list = tk.Listbox(list_frame, font=("맑은 고딕", 8), yscrollcommand=scrollbar.set)
        self.file_list.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.file_list.yview)
        self.file_list.drop_target_register(DND_FILES)
        self.file_list.dnd_bind("<<Drop>>", self.파일_드롭)

        # 설정 변수
        저장된_설정 = 설정_불러오기()
        self._활성_서식_프로파일 = str(저장된_설정.get("active_format_profile", ""))
        self.punctuation_var = tk.BooleanVar(value=bool(저장된_설정["punctuation"]))
        self.punctuation_threshold_var = tk.StringVar(value=str(저장된_설정["punctuation_threshold"]))
        self.keep_punctuation_set_var = tk.BooleanVar(value=bool(저장된_설정["keep_punctuation_set_together"]))
        self.color_mark_on_var = tk.BooleanVar(value=bool(저장된_설정["color_mark_on"]))
        self.color_var = tk.StringVar(value=str(저장된_설정["color"]))
        self.autoclose_var = tk.BooleanVar(value=bool(저장된_설정["autoclose"]))
        self.stdformat_var = tk.BooleanVar(value=bool(저장된_설정["stdformat"]))
        self.verify_var = tk.BooleanVar(value=bool(저장된_설정["verify"]))
        self.retry_body_var = tk.StringVar(value=str(저장된_설정["retry_body"]))
        self.retry_table_var = tk.StringVar(value=str(저장된_설정["retry_table"]))
        self.paren_shrink_var = tk.BooleanVar(value=bool(저장된_설정["paren_shrink"]))
        self.paren_label_bold_var = tk.BooleanVar(value=bool(저장된_설정["paren_label_bold"]))

        self.std_bool_keys = [
            "std_margin", "std_ratio", "std_linespacing", "std_title", "std_title_bold",
            "std_dateinfo", "std_dateinfo_bold", "std_symbols", "std_symbol_box_bold",
            "std_symbol_o_bold", "std_symbol_dash_bold", "std_symbol_note_bold",
            "std_parspace", "std_table_header",
        ]
        self.std_bool_vars = {키: tk.BooleanVar(value=bool(저장된_설정[키])) for 키 in self.std_bool_keys}

        self.std_parspace_str_keys = ["std_parspace_box", "std_parspace_circle", "std_parspace_note"]
        self.std_parspace_vars = {키: tk.StringVar(value=str(저장된_설정[키])) for 키 in self.std_parspace_str_keys}

        for 변수 in ([self.punctuation_var, self.punctuation_threshold_var, self.keep_punctuation_set_var,
                     self.color_mark_on_var, self.color_var,
                     self.autoclose_var, self.stdformat_var, self.verify_var,
                     self.retry_body_var, self.retry_table_var, self.paren_shrink_var,
                     self.paren_label_bold_var] + list(self.std_bool_vars.values()) + list(self.std_parspace_vars.values())):
            변수.trace_add("write", self._설정_변경됨)

        self.color_radios = []
        self.std_detail_checks = []
        self.std_parspace_spins = []
        self.settings_toplevel = None

        # 상태 및 프로그레스바
        status_frame = ttk.Frame(main)
        status_frame.grid(row=1, column=0, sticky="e")
        self.status_var = tk.StringVar(value="대기 중")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left")
        self.progress = ttk.Progressbar(status_frame, orient="horizontal", mode="determinate", maximum=100, length=100)
        self.progress.pack(side="left", padx=(5, 0))

        # 로그 프레임
        log_frame = ttk.LabelFrame(main, text="작업 로그", padding=3)
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        self.log_copy_button = ttk.Button(log_button_frame, text="로그 전체 복사", command=self.로그전체복사)
        self.log_copy_button.pack(side="right")

        log_scroll = ttk.Scrollbar(log_frame, orient="vertical")
        log_scroll.grid(row=1, column=1, sticky="ns")
        self.log_text = tk.Text(log_frame, font=("맑은 고딕", 8), wrap="none", yscrollcommand=log_scroll.set)
        self.log_text.grid(row=1, column=0, sticky="nsew")
        log_scroll.config(command=self.log_text.yview)
        self.log_text.bind("<Key>", self._로그_키입력_차단)

        # 하단 버튼
        button_frame = ttk.Frame(root, padding=(10, 3, 10, 6))
        button_frame.grid(row=2, column=0, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)

        left = ttk.Frame(button_frame)
        left.grid(row=0, column=0, sticky="w")
        self.select_button = ttk.Button(left, text="파일선택", command=self.파일선택)
        self.select_button.pack(side="left")
        self.clear_button = ttk.Button(left, text="목록 지우기", command=self.목록지우기)
        self.clear_button.pack(side="left", padx=(3, 0))
        self.settings_button = ttk.Button(left, text="⚙ 설정", command=self.설정창_열기)
        self.settings_button.pack(side="left", padx=(3, 0))

        right = ttk.Frame(button_frame)
        right.grid(row=0, column=1, sticky="e")
        self.start_button = ttk.Button(right, text="▶ 실행", style="Start.TButton", command=self.작업시작)
        self.start_button.pack(side="left", padx=1)
        self.stop_button = ttk.Button(right, text="■ 중단", command=self.작업중단, state="disabled")
        self.stop_button.pack(side="left", padx=1)
        self.exit_button = ttk.Button(right, text="✕ 종료", command=self.종료)
        self.exit_button.pack(side="left", padx=1)

        file_frame.drop_target_register(DND_FILES)
        file_frame.dnd_bind("<<Drop>>", self.파일_드롭)

        self._설정창_생성()

        root.after(100, self.queue_처리)
        root.protocol("WM_DELETE_WINDOW", self.종료)

    def _색상표시_상태_갱신(self, *args):
        """'자간조정 부분 글자색 표시' On/Off에 따라 색상 선택 라디오를 활성화/비활성화한다."""
        if getattr(self, "running", False):
            return
        활성 = bool(self.color_mark_on_var.get())
        상태 = "normal" if 활성 else "disabled"
        for 위젯 in getattr(self, "color_radios", []):
            try:
                위젯.config(state=상태)
            except Exception:
                pass

    def _표준서식_하위옵션_상태_갱신(self, *args):
        """
        '보고서 표준서식 적용' On/Off에 따라
        편집 여백 ~ 표 헤더/본문 서식 하위 옵션을 활성화/비활성화한다.
        """
        if getattr(self, "running", False):
            return

        활성 = bool(self.stdformat_var.get())
        상태 = "normal" if 활성 else "disabled"

        for 위젯 in getattr(self, "std_detail_checks", []):
            try:
                위젯.config(state=상태)
            except Exception:
                pass

        for 스핀 in getattr(self, "std_parspace_spins", []):
            try:
                스핀.config(state=상태)
            except Exception:
                pass

    def _설정창_생성(self):
        self.settings_toplevel = tk.Toplevel(self.root)
        self.settings_toplevel.title("설정")
        self.settings_toplevel.geometry("520x620")
        self.settings_toplevel.minsize(460, 420)
        self.settings_toplevel.transient(self.root)
        self.settings_toplevel.protocol("WM_DELETE_WINDOW", self.settings_toplevel.withdraw)

        canvas_frame = ttk.Frame(self.settings_toplevel)
        canvas_frame.pack(fill="both", expand=True)

        settings_canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        settings_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=settings_canvas.yview)
        settings_canvas.configure(yscrollcommand=settings_scroll.set)
        settings_scroll.pack(side="right", fill="y")
        settings_canvas.pack(side="left", fill="both", expand=True)

        container = ttk.Frame(settings_canvas, padding=10)
        container_창 = settings_canvas.create_window((0, 0), window=container, anchor="nw")

        def _내용_크기_변경(event):
            settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))

        container.bind("<Configure>", _내용_크기_변경)

        def _캔버스_크기_변경(event):
            settings_canvas.itemconfig(container_창, width=event.width)

        settings_canvas.bind("<Configure>", _캔버스_크기_변경)
        settings_canvas.bind("<MouseWheel>", lambda e: settings_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # 그룹 1: 자간축소 옵션
        group1 = ttk.LabelFrame(container, text="자간축소 옵션", padding=8)
        group1.pack(fill="x", pady=(0, 8))

        punctuation_frame = ttk.Frame(group1)
        punctuation_frame.pack(anchor="w", fill="x")
        self.punctuation_check = ttk.Checkbutton(
            punctuation_frame,
            text="문장부호/공문서 항목 시작 문장의 2줄 이상 자동 자간 축소 (마지막 줄",
            variable=self.punctuation_var
        )
        self.punctuation_check.pack(side="left")
        self.punctuation_threshold_spin = ttk.Spinbox(
            punctuation_frame, from_=1, to=20, width=3, textvariable=self.punctuation_threshold_var, justify="center"
        )
        self.punctuation_threshold_spin.pack(side="left", padx=(4, 4))
        ttk.Label(punctuation_frame, text="자 이하일 때)").pack(side="left")

        self.keep_punctuation_set_check = ttk.Checkbutton(
            group1,
            text=(
                "문장부호 세트문장을 같은 쪽에 유지 (기본 ON)\n"
                "(세트가 다음 쪽으로 넘어가면 문장부호가 있는 시작 쪽 전체 줄간격을 10%씩 축소, 최소 100%)"
            ),
            variable=self.keep_punctuation_set_var,
            justify="left"
        )
        self.keep_punctuation_set_check.pack(anchor="w", pady=(6, 0))

        color_frame = ttk.Frame(group1)
        color_frame.pack(anchor="w", fill="x", pady=(6, 0))
        self.color_mark_check = ttk.Checkbutton(
            color_frame, text="자간조정 부분 글자색 표시", variable=self.color_mark_on_var
        )
        self.color_mark_check.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 2))

        self.color_radios = []
        for 순번, (키, 이름, rgb) in enumerate(COLOR_OPTIONS):
            행 = (순번 // 5) + 1
            열 = 순번 % 5
            항목 = ttk.Frame(color_frame)
            항목.grid(row=행, column=열, sticky="w", padx=(0, 8))
            라디오 = ttk.Radiobutton(항목, text=이름, value=키, variable=self.color_var)
            라디오.pack(side="left")
            self.color_radios.append(라디오)
            if rgb:
                tk.Label(항목, text="●", fg=색상_미리보기_hex(rgb)).pack(side="left")

        self.color_mark_on_var.trace_add("write", self._색상표시_상태_갱신)
        self._색상표시_상태_갱신()

        retry_frame = ttk.Frame(group1)
        retry_frame.pack(anchor="w", fill="x", pady=(6, 0))
        ttk.Label(retry_frame, text="단어분리 자간조정 재시도 횟수 — 본문:").pack(side="left")
        self.retry_body_spin = ttk.Spinbox(
            retry_frame, from_=1, to=99, width=3, textvariable=self.retry_body_var, justify="center"
        )
        self.retry_body_spin.pack(side="left", padx=(4, 12))
        ttk.Label(retry_frame, text="표/글상자 안:").pack(side="left")
        self.retry_table_spin = ttk.Spinbox(
            retry_frame, from_=1, to=99, width=3, textvariable=self.retry_table_var, justify="center"
        )
        self.retry_table_spin.pack(side="left", padx=(4, 0))

        # 그룹 2: 보고서 서식
        group2 = ttk.LabelFrame(container, text="보고서 서식", padding=8)
        group2.pack(fill="x", pady=(0, 8))

        self.stdformat_check = ttk.Checkbutton(
            group2,
            text="보고서 표준서식 적용\n(여백·장평·줄간격 및 문장부호별 폰트·들여쓰기 적용)",
            variable=self.stdformat_var,
            justify="left"
        )
        self.stdformat_check.pack(anchor="w")

        self.std_detail_checks = []
        std_detail = ttk.Frame(group2)
        std_detail.pack(anchor="w", fill="x", padx=(18, 0), pady=(4, 0))

        # 2-1. 여백/장평/줄간격
        기본항목_행 = ttk.Frame(std_detail)
        기본항목_행.pack(anchor="w", fill="x")
        for 문구, 설정_키, 여백 in [("편집 여백", "std_margin", 0), ("기본 장평", "std_ratio", 10), ("기본 줄간격", "std_linespacing", 10)]:
            체크 = ttk.Checkbutton(기본항목_행, text=문구, variable=self.std_bool_vars[설정_키])
            체크.pack(side="left", padx=(여백, 0))
            self.std_detail_checks.append(체크)

        # 2-2. 제목 문단
        제목_행 = ttk.Frame(std_detail)
        제목_행.pack(anchor="w", fill="x", pady=(4, 0))
        for 문구, 설정_키, 여백 in [("제목 문단(1번째 문단) 서식", "std_title", 0), ("굵게", "std_title_bold", 10)]:
            체크 = ttk.Checkbutton(제목_행, text=문구, variable=self.std_bool_vars[설정_키])
            체크.pack(side="left", padx=(여백, 0))
            self.std_detail_checks.append(체크)

        # 2-3. 일자·담당자
        일자담당자_행 = ttk.Frame(std_detail)
        일자담당자_행.pack(anchor="w", fill="x", pady=(4, 0))
        for 문구, 설정_키, 여백 in [("일자·담당자 문단(2번째 문단) 서식", "std_dateinfo", 0), ("굵게", "std_dateinfo_bold", 10)]:
            체크 = ttk.Checkbutton(일자담당자_행, text=문구, variable=self.std_bool_vars[설정_키])
            체크.pack(side="left", padx=(여백, 0))
            self.std_detail_checks.append(체크)

        # 2-4. 기호별 서식
        기호_행 = ttk.Frame(std_detail)
        기호_행.pack(anchor="w", fill="x", pady=(4, 0))
        기호_체크 = ttk.Checkbutton(기호_행, text="문장부호별 폰트·크기·들여쓰기 (□/ㅇ/-/※)", variable=self.std_bool_vars["std_symbols"])
        기호_체크.pack(side="left")
        self.std_detail_checks.append(기호_체크)

        기호_굵게_행 = ttk.Frame(std_detail)
        기호_굵게_행.pack(anchor="w", fill="x", pady=(2, 0))
        ttk.Label(기호_굵게_행, text="굵게:").pack(side="left")
        for 기호_텍스트, 설정_키 in [("□", "std_symbol_box_bold"), ("ㅇ", "std_symbol_o_bold"), ("-", "std_symbol_dash_bold"), ("※", "std_symbol_note_bold")]:
            체크 = ttk.Checkbutton(기호_굵게_행, text=기호_텍스트, variable=self.std_bool_vars[설정_키])
            체크.pack(side="left", padx=(6, 0))
            self.std_detail_checks.append(체크)

        # 2-5. 문단 위 간격
        self.std_parspace_spins = []
        문단위간격_체크 = ttk.Checkbutton(std_detail, text="문장부호별 문단 위 간격 적용", variable=self.std_bool_vars["std_parspace"])
        문단위간격_체크.pack(anchor="w", pady=(8, 0))
        self.std_detail_checks.append(문단위간격_체크)

        문단위간격_행 = ttk.Frame(std_detail)
        문단위간격_행.pack(anchor="w", fill="x", padx=(18, 0), pady=(2, 0))
        for 라벨, 설정_키 in [("□", "std_parspace_box"), ("ㅇ·○·☞", "std_parspace_circle"), ("*·※·→", "std_parspace_note")]:
            ttk.Label(문단위간격_행, text=f"{라벨}:").pack(side="left", padx=(0 if 라벨 == "□" else 10, 0))
            스핀 = ttk.Spinbox(문단위간격_행, from_=0, to=99, width=3, textvariable=self.std_parspace_vars[설정_키], justify="center")
            스핀.pack(side="left", padx=(4, 0))
            ttk.Label(문단위간격_행, text="pt").pack(side="left", padx=(2, 0))
            self.std_parspace_spins.append(스핀)

        # 2-6. 표 헤더 서식
        표_헤더서식_체크 = ttk.Checkbutton(
            std_detail,
            text="표 헤더/본문 서식 적용\n(1행: 한컴돋움 13pt 굵게 / 나머지 행: 휴먼명조 12pt)",
            variable=self.std_bool_vars["std_table_header"],
            justify="left"
        )
        표_헤더서식_체크.pack(anchor="w", pady=(8, 0))
        self.std_detail_checks.append(표_헤더서식_체크)

        # 표준서식 토글 이벤트 연결 및 초기값 반영
        self.stdformat_var.trace_add("write", self._표준서식_하위옵션_상태_갱신)
        self._표준서식_하위옵션_상태_갱신()

        # 2-7. 문두 라벨 굵게 & 괄호 축소 (표준서식 적용 여부와 독립적으로 운용 가능)
        self.paren_label_bold_check = ttk.Checkbutton(
            group2,
            text="문두 라벨(괄호 및 콜론 라벨) 굵게\n(\"ㅇ (운영방식)\"의 괄호 또는 \"- 추진부서 :\"처럼 문장부호 뒤 콜론 앞 텍스트 굵게)",
            variable=self.paren_label_bold_var,
            justify="left"
        )
        self.paren_label_bold_check.pack(anchor="w", pady=(10, 0))

        self.paren_shrink_check = ttk.Checkbutton(
            group2,
            text="괄호 안 부연설명 글자 크기 축소\n(문장 중간·끝에 오는 괄호 안 글자를 2pt 작게 표시)",
            variable=self.paren_shrink_var,
            justify="left"
        )
        self.paren_shrink_check.pack(anchor="w", pady=(6, 0))

        # 그룹 3: 완료 후 처리
        group3 = ttk.LabelFrame(container, text="완료 후 처리", padding=8)
        group3.pack(fill="x", pady=(0, 8))
        self.autoclose_check = ttk.Checkbutton(group3, text="자간조정 후 파일 닫기", variable=self.autoclose_var)
        self.autoclose_check.pack(anchor="w")
        self.verify_check = ttk.Checkbutton(
            group3, text="작업 상황 로그 기록 (자간축소 미해결 문단 등 작업 상황을 로그에 기록)", variable=self.verify_var
        )
        self.verify_check.pack(anchor="w", pady=(6, 0))

        # 하단
        footer = ttk.Frame(container)
        footer.pack(fill="x", pady=(8, 0))
        ttk.Label(footer, text="제작 : 마포구청 도토리만두", foreground="#666666").pack(side="left")
        ttk.Button(footer, text="닫기", command=self.settings_toplevel.withdraw).pack(side="right")
        ttk.Button(footer, text="설정 초기화", command=self._설정_초기화_클릭).pack(side="right", padx=(0, 6))

        self.settings_toplevel.withdraw()

    def 설정창_열기(self):
        if self.settings_toplevel is None or not self.settings_toplevel.winfo_exists():
            self._설정창_생성()
        self.settings_toplevel.deiconify()
        self.settings_toplevel.lift()

    def _설정_변경됨(self, *args):
        try:
            설정값 = {
                "punctuation": bool(self.punctuation_var.get()),
                "punctuation_threshold": str(self.punctuation_threshold_var.get()),
                "keep_punctuation_set_together": bool(self.keep_punctuation_set_var.get()),
                "color_mark_on": bool(self.color_mark_on_var.get()),
                "color": str(self.color_var.get()),
                "autoclose": bool(self.autoclose_var.get()),
                "stdformat": bool(self.stdformat_var.get()),
                "verify": bool(self.verify_var.get()),
                "retry_body": str(self.retry_body_var.get()),
                "retry_table": str(self.retry_table_var.get()),
                "paren_shrink": bool(self.paren_shrink_var.get()),
                "paren_label_bold": bool(self.paren_label_bold_var.get()),
            }
            for 키, 변수 in self.std_bool_vars.items():
                설정값[키] = bool(변수.get())
            for 키, 변수 in self.std_parspace_vars.items():
                설정값[키] = str(변수.get())
            설정값["active_format_profile"] = getattr(self, "_활성_서식_프로파일", "")
            설정_저장(설정값)
        except Exception:
            pass

    def _설정_초기화_클릭(self):
        if not messagebox.askyesno(APP_NAME, "모든 설정을 기본값으로 초기화하시겠습니까?"):
            return
        try:
            설정_저장(dict(기본_설정))
        except Exception as e:
            messagebox.showerror(APP_NAME, f"설정 초기화 오류: {e}")
            return

        self.punctuation_var.set(기본_설정["punctuation"])
        self.punctuation_threshold_var.set(기본_설정["punctuation_threshold"])
        self.keep_punctuation_set_var.set(기본_설정["keep_punctuation_set_together"])
        self.color_mark_on_var.set(기본_설정["color_mark_on"])
        self.color_var.set(기본_설정["color"])
        self.autoclose_var.set(기본_설정["autoclose"])
        self.stdformat_var.set(기본_설정["stdformat"])
        self.verify_var.set(기본_설정["verify"])
        self.retry_body_var.set(기본_설정["retry_body"])
        self.retry_table_var.set(기본_설정["retry_table"])
        self.paren_shrink_var.set(기본_설정["paren_shrink"])
        self.paren_label_bold_var.set(기본_설정["paren_label_bold"])

        for 키 in self.std_bool_keys:
            self.std_bool_vars[키].set(기본_설정[키])
        for 키 in self.std_parspace_str_keys:
            self.std_parspace_vars[키].set(기본_설정[키])

        서식_기본값_전역_복원()
        self._활성_서식_프로파일 = ""
        self._설정_변경됨()
        self._색상표시_상태_갱신()
        self._표준서식_하위옵션_상태_갱신()
        messagebox.showinfo(APP_NAME, "모든 설정을 기본값으로 초기화했습니다.")

    def 로그표시(self, message):
        self.로그_여러줄_표시([str(message)])

    def 로그_여러줄_표시(self, 줄들):
        if not 줄들:
            return
        try:
            self.log_text.insert(tk.END, "\n".join(줄들) + "\n")
            총줄수 = int(self.log_text.index("end-1c").split(".")[0])
            if 총줄수 > 로그_최대_줄수:
                self.log_text.delete("1.0", f"{총줄수 - 로그_최대_줄수}.0")
            self.log_text.see(tk.END)
        except tk.TclError:
            pass

    def _로그_키입력_차단(self, event):
        허용_키셋 = ("Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next")
        if event.state & 0x4 or event.keysym in 허용_키셋:
            return None
        return "break"

    def 로그전체복사(self):
        try:
            내용 = self.log_text.get("1.0", "end-1c")
            self.root.clipboard_clear()
            self.root.clipboard_append(내용)
            self.status_var.set("로그를 클립보드에 복사했습니다")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"로그 복사 중 오류가 발생했습니다.\n\n{e}", parent=self.root)

    def 파일추가(self, file_path):
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

    def 폴더추가(self, folder_path):
        folder = Path(folder_path)
        if not folder.is_dir():
            return 0
        count = 0
        try:
            items = sorted(folder.iterdir(), key=lambda p: p.name.lower())
        except Exception:
            return 0

        for path in items:
            if path.is_file() and path.suffix.lower() in (".hwp", ".hwpx"):
                if self.파일추가(path):
                    count += 1
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
            item = str(item).strip()
            if os.path.isdir(item):
                added += self.폴더추가(item)
            elif os.path.isfile(item):
                if self.파일추가(item):
                    added += 1

        if added:
            self.status_var.set(f"{len(self.files)}개 문서 선택")
            self.로그표시(f"{added}개 문서 추가")

    def 파일선택(self):
        if self.running:
            return
        files = askopenfilenames(
            parent=self.root,
            title="자간을 조정할 HWP/HWPX 문서를 선택하세요.",
            initialdir=os.getcwd(),
            filetypes=[("한/글 파일", "*.hwp *.hwpx"), ("HWP 파일", "*.hwp"), ("HWPX 파일", "*.hwpx")]
        )
        if not files:
            return
        added = 0
        for file in files:
            if self.파일추가(file):
                added += 1
        self.status_var.set(f"{len(self.files)}개 문서 선택")
        if added:
            self.로그표시(f"{added}개 문서 추가")

    def 목록지우기(self):
        if self.running:
            return
        self.files.clear()
        self.file_list.delete(0, tk.END)
        self.progress["value"] = 0
        self.status_var.set("대기 중")

    def 버튼_작업중(self):
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.select_button.config(state="disabled")
        self.clear_button.config(state="disabled")
        self.punctuation_check.config(state="disabled")
        self.punctuation_threshold_spin.config(state="disabled")
        self.retry_body_spin.config(state="disabled")
        self.retry_table_spin.config(state="disabled")
        self.color_mark_check.config(state="disabled")
        for 라디오 in self.color_radios:
            라디오.config(state="disabled")
        for 체크 in self.std_detail_checks:
            체크.config(state="disabled")
        for 스핀 in self.std_parspace_spins:
            스핀.config(state="disabled")
        self.autoclose_check.config(state="disabled")
        self.stdformat_check.config(state="disabled")
        self.paren_shrink_check.config(state="disabled")
        self.paren_label_bold_check.config(state="disabled")
        self.verify_check.config(state="disabled")

    def 버튼_대기중(self):
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.select_button.config(state="normal")
        self.clear_button.config(state="normal")
        self.punctuation_check.config(state="normal")
        self.punctuation_threshold_spin.config(state="normal")
        self.retry_body_spin.config(state="normal")
        self.retry_table_spin.config(state="normal")
        self.color_mark_check.config(state="normal")

        self.autoclose_check.config(state="normal")
        self.stdformat_check.config(state="normal")
        self.paren_shrink_check.config(state="normal")
        self.paren_label_bold_check.config(state="normal")
        self.verify_check.config(state="normal")
        self._색상표시_상태_갱신()
        self._표준서식_하위옵션_상태_갱신()

    def 비교창_준비(self):
        if self.compare_toplevel is not None and self.compare_toplevel.winfo_exists():
            self.compare_toplevel.deiconify()
            self.compare_toplevel.lift()
            self.compare_toplevel.update_idletasks()
            return (self.compare_left_frame.winfo_id(), self.compare_right_frame.winfo_id())

        self.compare_toplevel = tk.Toplevel(self.root)
        self.compare_toplevel.title("원본·결과 비교 보기 (왼쪽: 원본 / 오른쪽: 자간조정 중)")
        화면너비 = self.root.winfo_screenwidth()
        화면높이 = self.root.winfo_screenheight()
        self.compare_toplevel.geometry(f"{화면너비}x{화면높이}+0+0")
        self.compare_toplevel.minsize(640, 360)

        self.compare_toplevel.grid_rowconfigure(1, weight=1)
        self.compare_toplevel.grid_columnconfigure(0, weight=1)
        self.compare_toplevel.grid_columnconfigure(1, weight=1)

        ttk.Label(self.compare_toplevel, text="원본", anchor="center").grid(row=0, column=0, sticky="ew")
        ttk.Label(self.compare_toplevel, text="자간조정 중", anchor="center").grid(row=0, column=1, sticky="ew")

        self.compare_left_frame = tk.Frame(self.compare_toplevel, bg="#202020")
        self.compare_left_frame.grid(row=1, column=0, sticky="nsew")
        self.compare_right_frame = tk.Frame(self.compare_toplevel, bg="#202020")
        self.compare_right_frame.grid(row=1, column=1, sticky="nsew")

        self.compare_left_frame.bind("<Configure>", self._비교_왼쪽_리사이즈)
        self.compare_right_frame.bind("<Configure>", self._비교_오른쪽_리사이즈)
        self.compare_toplevel.protocol("WM_DELETE_WINDOW", self._비교창_닫기시도)
        self.compare_toplevel.update_idletasks()

        return (self.compare_left_frame.winfo_id(), self.compare_right_frame.winfo_id())

    def _비교_왼쪽_리사이즈(self, event):
        if 원본_hwp_hwnd:
            창_임베드_크기조정(원본_hwp_hwnd, self.compare_left_frame.winfo_id())

    def _비교_오른쪽_리사이즈(self, event):
        if 작업_hwp_hwnd:
            창_임베드_크기조정(작업_hwp_hwnd, self.compare_right_frame.winfo_id())

    def _비교창_닫기시도(self):
        if self.running:
            messagebox.showinfo(APP_NAME, "작업이 진행 중일 때는 비교 보기 창을 닫을 수 없습니다.", parent=self.compare_toplevel)
            return
        if self.compare_toplevel is not None:
            self.compare_toplevel.withdraw()

    def 작업시작(self):
        if self.running:
            return
        if not self.files:
            messagebox.showwarning(APP_NAME, "먼저 HWP/HWPX 문서를 선택하거나 끌어다 놓으세요.", parent=self.root)
            return

        self.running = True
        self.closing = False
        중단_event.clear()
        self.progress["value"] = 0
        self.버튼_작업중()

        self.로그표시("")
        self.로그표시("=" * 45)
        self.로그표시(f"{APP_NAME} 작업 시작")
        self.로그표시(f"문서: {len(self.files)}개")

        try:
            둘째줄기준값 = max(1, int(self.punctuation_threshold_var.get()))
        except Exception:
            둘째줄기준값 = 5
            self.punctuation_threshold_var.set("5")

        try:
            본문재시도값 = max(1, int(self.retry_body_var.get()))
        except Exception:
            본문재시도값 = 30
            self.retry_body_var.set("30")

        try:
            표재시도값 = max(1, int(self.retry_table_var.get()))
        except Exception:
            표재시도값 = 5
            self.retry_table_var.set("5")

        문단위간격_기본값 = {"std_parspace_box": 15, "std_parspace_circle": 10, "std_parspace_note": 3}
        문단위간격_값 = {}
        for 키, 기본값 in 문단위간격_기본값.items():
            try:
                문단위간격_값[키] = max(0, int(self.std_parspace_vars[키].get()))
            except Exception:
                문단위간격_값[키] = 기본값
                self.std_parspace_vars[키].set(str(기본값))

        선택_색상 = COLOR_MAP.get(self.color_var.get()) if self.color_mark_on_var.get() else None
        표준서식_세부_전달 = {키: var.get() for 키, var in self.std_bool_vars.items()}

        self.worker = threading.Thread(
            target=작업_실행,
            args=(
                list(self.files),
                self.punctuation_var.get(),
                선택_색상,
                False,
                None,
                None,
                self.autoclose_var.get(),
                self.stdformat_var.get(),
                self.verify_var.get(),
                둘째줄기준값,
                본문재시도값,
                표재시도값,
                self.paren_shrink_var.get(),
                표준서식_세부_전달,
                문단위간격_값,
                self.paren_label_bold_var.get(),
                self.keep_punctuation_set_var.get()
            ),
            daemon=True
        )
        self.worker.start()

    def 작업중단(self):
        if not self.running:
            return
        중단_event.set()
        self.stop_button.config(state="disabled")
        self.status_var.set("작업 중단 처리 중...")
        self.로그표시("사용자가 작업 중단을 요청했습니다.")

    def queue_처리(self):
        모인_로그 = []
        try:
            while True:
                item = gui_queue.get_nowait()
                event = item[0]
                if event == "log":
                    모인_로그.append(str(item[1]))
                    continue
                if 모인_로그:
                    self.로그_여러줄_표시(모인_로그)
                    모인_로그 = []

                if event == "status":
                    self.status_var.set(item[1])
                elif event == "progress":
                    self.progress["value"] = item[1]
                elif event == "document_error":
                    self.로그표시(f"문서 처리 실패: {item[1]}\n{item[2]}")
                elif event == "stopped":
                    self.running = False
                    self.버튼_대기중()
                    self.status_var.set("작업 중단")
                    self.로그표시("=" * 45 + "\n작업이 중단되었습니다.\n" + "=" * 45)
                    if not self.closing:
                        messagebox.showinfo(APP_NAME, "자간 조정 작업이 중단되었습니다.", parent=self.root)
                elif event == "finished":
                    self.running = False
                    self.progress["value"] = 100
                    self.버튼_대기중()
                    self.status_var.set("모든 작업 완료")
                    self.로그표시("=" * 45 + f"\n작업 완료 - 성공 {item[1]}개 / 실패 {item[2]}개\n" + "=" * 45)
                    if not self.closing:
                        messagebox.showinfo(APP_NAME, f"자간 조정이 완료되었습니다.\n\n성공: {item[1]}개\n실패: {item[2]}개", parent=self.root)
                elif event == "fatal_error":
                    self.running = False
                    self.버튼_대기중()
                    self.status_var.set("오류 발생")
                    self.로그표시(f"치명적 오류:\n{item[1]}")
                    if not self.closing:
                        messagebox.showerror(APP_NAME, f"작업 중 오류가 발생했습니다.\n\n{item[1]}", parent=self.root)
        except queue.Empty:
            pass

        if 모인_로그:
            self.로그_여러줄_표시(모인_로그)

        try:
            self.root.after(100, self.queue_처리)
        except tk.TclError:
            pass

    def 종료(self):
        if self.closing:
            return
        if self.running:
            if not messagebox.askyesno(APP_NAME, "현재 자간 조정 작업이 진행 중입니다.\n\n작업을 중단하고 종료하시겠습니까?", parent=self.root):
                return
            self.closing = True
            중단_event.set()
            self.status_var.set("프로그램 종료 처리 중...")
            self.버튼_작업중()
            self.worker_종료확인()
            return
        self._비교창_분리_후_보존()
        self.root.destroy()

    def _비교창_분리_후_보존(self):
        원본_뷰어_분리()
        작업창_분리()

    def worker_종료확인(self):
        if self.worker is not None and self.worker.is_alive():
            self.root.after(200, self.worker_종료확인)
            return
        self._비교창_분리_후_보존()
        self.root.destroy()

# ============================================================
# Main 실행부
# ============================================================

def main():
    root = TkinterDnD.Tk()
    HwpAutoDocFitGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()