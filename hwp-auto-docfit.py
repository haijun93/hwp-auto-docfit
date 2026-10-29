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
3. MapoHwpAutoDocFitSecurity.dll 최초 1회 설치
4. Registry AutomationModule 최초 1회 등록
5. HWP / HWPX 다중 선택
6. Drag & Drop
7. 폴더 Drag & Drop
8. 중복 파일 자동 제거
9. 기존 자간 자동조정 알고리즘(줄 끝 단어분리 방지)
10. 문장부호/공문서 항목 자동 인식(계층형 번호 2-7. 포함)
11. 문장부호 시작 문장 줄병합 자간조정
    (2줄 이상, 마지막 줄이 지정 글자수 이하일 때)
12. 실제 Enter 문장은 문장부호 기능에서 제외
13. 표/글상자/각주/미주 등 컨트롤 처리
14. 보고서 표준서식적용(여백/장평/줄간격/기호별 폰트)
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
27. 붙임 괄호 줄분리 우선 자간조정
28. 표 컨트롤/셀 직접 순회 서식적용
29. 괄호 안쪽 불필요 공백 자동 제거 (( 내용 ) → (내용))
30. 전체 편집 파이프라인 기본 1회, 사용자 선택 시 2회 반복 처리
31. 화면줄 경계 어절 분리 우선 자간조정 (예: 제공하 | 며,)
32. 선택형 다줄 단어 분리 방지: 앞/뒤 글자 수 비교에 따른 축소·확대
33. 본문·내용·부연설명 묶음의 쪽별 줄 수에 따른 줄간격 축소·확대
34. 쉼표·따옴표 및 공백 없이 붙은 3글자 이하 괄호를 단어와 함께 처리
35. 생성형 AI 채팅창에서 복사한 텍스트 정리(마크다운 기호 제거, 문단·목록 줄바꿈 복원)
36. 괄호 안 공백을 포함한 부연 설명 전체를 한 어절로 보고 줄 끝 분리 방지
    (예: "계약방법(공개모집 원칙, 수의계약)이")
37. 작업 중단 후 실행 버튼으로 완료된 문서는 건너뛰고 이어서 진행
38. 세부 설정 '자간 정리' 탭을 실행창 '세부 작업'과 같은 7단계로 재구성,
    짧은 마지막 줄 병합 글자 수를 세부 작업 창에서 바로 설정
39. 세부 설정 '서식·내어쓰기' 탭을 '서식 정리'·'내어쓰기'로 분리하고
    실행창 '세부 작업'과 같은 10단계로 재구성. 문서 스타일(계층구조) 편집,
    항목기호별 글꼴·크기·굵게, 문단위 여백을 각 단계 아래로 모음
40. 실행창 '세부 작업' 창에도 세부 설정과 동일한 상세 항목(문서 스타일,
    항목기호별 글꼴·크기·굵게, 문단위 여백 등)을 표시해 두 창이 항상
    같은 내용을 보이도록 통일(같은 변수를 공유해 어느 쪽에서 바꿔도 반영)
41. HWP/HWPX 외 TXT·MD·DOC(X)·PDF 파일도 추가해 처리 가능. 자간·서식
    작업 전에 작업용 HWPX로 자동 변환하며, 결과물은 항상 HWPX로 저장.
    MD/DOC(X)/PDF는 선택형 kordoc 엔진(Node.js)이 있어야 서식을 살려
    변환하며, MD는 엔진이 없으면 서식 없이 텍스트로만 변환
42. 실행창 '세부 작업'과 세부 설정의 '01. 문서 전체 자간 초기화' 등
    번호가 붙은 항목 제목을 굵은 글씨로 표시해 켜고 끄는 단계가
    잘 구분되도록 개선
43. 서식 정리의 항목기호별 글꼴 선택 목록에 한컴오피스 전용 번들
    (HFT) 글꼴도 자동으로 찾아 포함. 설치 경로에서 .hft 파일이 있는
    폴더를 이름에 상관없이 직접 찾아 지정한 글꼴 폴더의 목록과 합침
44. PDF·DOC(X)를 HWPX로 변환할 때 내용 손실을 줄임: 텍스트층이 없는
    스캔 PDF 페이지는 내장 OCR로 인식하고, 문서 안 이미지는 kordoc이
    추출한 그대로 결과 HWPX에 실제로 임베드(이전에는 자리표시만 남고
    이미지가 사라졌음)
45. 자간 정리 '01. 문서 전체 자간 초기화'에서 같은 뜻으로 중복되던
    "기존 자간을 0%로 초기화 후 정리하기" 체크박스를 없애고, 번호
    체크박스 하나로 통일(한 번에 정리에서도 같은 체크박스로 켜고 끔)
46. 붙여넣은 텍스트 정리가 제미나이 등에서 자주 나오는, 백슬래시로
    이스케이프된 굵게 표시를 먼저 풀어낸 뒤 정리해, 이전엔 뒤따르는
    글자에 따라 삐뚤빼뚤 깨지던 문제를 없앰. 문장 끝에 붙는 [1],
    [2][4] 같은 숫자 전용 각주 표시도 함께 제거(글자가 섞인
    [별표 21의2] 같은 대괄호는 그대로 유지)
47. 붙여넣은 텍스트 정리에 '개조식으로 변환' 버튼 추가. 제미나이 등의
    답변에 있는 제목(#)·글머리 기호의 계층 구조를 읽어 1단계는 원문
    번호를 그대로 쓰거나 없으면 ㅁ을, 그 아래는 들여쓰기 깊이에 따라
    ㅇ→-→•(3단계 이후는 모두 •) 순으로 항목기호를 붙여 공문서
    개조식 서식으로 바꿈
48. 실행창 '01 정리할 문서'에 '텍스트 붙여넣기' 버튼 추가. 파일이
    없어도 텍스트를 붙여넣어 .txt로 저장하면 바로 문서 목록에
    추가되어 다른 파일과 함께 자간·서식 정리를 적용할 수 있음
49. '01 정리할 문서'에 '아웃라이너로 작성' 버튼 추가. 워크플로위처럼
    Tab/Shift+Tab으로 계층을 넣고 빼며 새 글을 쓰고, 저장 형식 자체가
    계층 구조를 담은 마크다운(0단계 "# ", 그 아래는 "- "를 들여쓰기
    깊이만큼 겹침)이라 '개조식 텍스트로 추가'를 누르면 ㅁ/ㅇ/-/•
    공문서 항목기호로 바꿔 바로 문서 목록에 추가됨(또는 '마크다운으로
    추가'로 원본 그대로 추가해 고급 문서 엔진이 서식을 살려 변환)
50. 붙여넣은 텍스트 정리의 '개조식으로 변환'이 워크플로위 등을
    브라우저에서 통째로 복사해 줄바꿈이 모두 공백으로 뭉개진 경우도
    알아서 인식. 이때는 계층 깊이까지는 복원할 수 없어 항목만 한 줄씩
    펼쳐 ㅇ로 표시하고, 워크플로위 해시태그(#표시)도 함께 정리
51. '텍스트 붙여넣기'에 자동 저장 폴더 지정 기능 추가. 폴더를 지정해
    두면 '문서로 추가'를 누를 때 바로 그 폴더에 HWPX로 변환해(배치
    작업과 독립된 한/글 세션 사용) 문서 목록에 추가하며, 비워두면
    기존처럼 저장 위치를 직접 골라 .txt로 추가함
52. 곧은 큰따옴표(")를 한글 표준 둥근따옴표(" ")로 자동 통일(공백
    정규화 단계에 포함). 여는/닫는 판정은 줄 시작·공백·여는 괄호 뒤인지로
    가리며, 작은따옴표는 발·분 표기나 영어 축약형과 구분할 방법이 없어
    다루지 않음(연도 앞 표기는 기존 규칙 그대로 유지)
53. 항목기호 뒤 공백 보정이 탭·전각공백도 인식해 표준 반각 공백 1칸으로
    바꿈(이전엔 스페이스만 인식해 탭·전각공백 뒤에 공백을 하나 더
    끼워 넣었음). 단어 사이 공백 정리도 탭·전각공백 1칸까지 대상에 포함
54. 자간만으로 줄바꿈이 해결되지 않는 긴 어절에 장평(글자 가로비율)을
    추가로 줄이는 기능 활성화. 자간은 적당히만(최대 4%p) 남기고 장평을
    1%씩 최대 15단계(85%까지) 줄이며 재확인 — 자간을 허용 범위 끝까지
    밀어붙여 글자가 다닥다닥 붙어 보이는 대신 장평과 나눠 분담함
55. 긴 단어 전체가 통째로 다음 줄로 밀려 양쪽정렬 단어 간격이 비정상
    적으로 벌어지는 경우를 새로 감지해 자간(부족하면 장평도 추가)으로
    끌어올림. 기존에는 단어가 중간에서 갈라지는 경우만 감지했고, 이처럼
    깨끗한 단어 경계에서 통째로 밀려난 경우는 대상이 아니었음
56. 보고서 표준서식의 기호 앞 들여쓰기 기본값을 행정안전부 개조식
    보고서 작성 표준(□0칸→ㅇ1칸→―2칸→·/*3칸)에 맞춤. 기존 기본값
    (-3칸, ※·•5칸)이 실제 표준과 달라 항목 기호 뒤에 스페이스바를
    수동으로 끼워 맞추던 원인이었음
57. 곧은 작은따옴표(')도 한글 표준 둥근따옴표(' ')로 통일. 숫자 뒤
    발·분 표기(6', 37° 33')는 단위 기호로 보아 건드리지 않고, 연도 앞
    표기('26년)는 기존 규칙이 먼저 처리하므로 겹치지 않음
58. 날짜·기간·시간 표기의 하이픈(-)·엔대시(–)·엠대시(—)를 물결표(~)로
    통일하고 날짜 뒤 빠진 온점, 요일 괄호(예: (금)) 앞뒤 온점 위치를
    표준에 맞춤. 점(.)으로 연·월·일을 구분한 날짜/시:분 형태 사이에 낀
    경우만 다뤄 전화번호·법령 조항·사업 코드의 하이픈은 손대지 않음.
    단, 기간 앞뒤 날짜가 같은 연도를 반복 표기한 경우를 "2026. 6. 30"
    같은 축약형으로 압축하는 것은 의미 판단이 필요해 자동화하지 않음
59. 마지막 쪽에 2~3줄만 걸쳐 있으면, 본문 줄간격은 그대로 두고 항목기호
    문단의 '문단 아래 간격'만 1pt씩 줄여(최대 10pt) 앞쪽 쪽으로 당겨
    페이지 수를 맞춤. 실제 페이지 수를 매 단계 다시 측정해 판단하며,
    최대치까지 줄여도 안 되면 더 손대지 않고 멈춤(본문 내용을 강제로
    줄이거나 지우지 않음). '관련 문단 페이지 배치' 다음 마지막 단계로
    실행되는 세부 작업(page_fit)으로 켜고 끌 수 있음
60. 표 구조 정밀 조정 3종(기본 꺼짐 — 표_셀여백_축소_사용/표_열너비_맞춤_사용
    /표_테두리_통일_사용을 True로 바꿔야 실행됨. 실험적 기능으로,
    문자 서식보다 잘못됐을 때 위험이 커 실제 한/글 검증 전까지는
    기본값을 꺼둠):
    - 셀 안쪽 여백 강제 축소: 셀 텍스트가 2줄로 넘어가면 좌우 안쪽
      여백을 1.8mm→0mm까지 0.3mm씩 줄여 1줄로 줄어드는지 시도
    - 셀 너비 본문 맞춤: 표 첫 행(칼럼별 셀)의 현재 너비 비율을 유지한
      채 표 전체 너비를 본문 가용 너비(용지 폭 - 좌우 여백)에 비례
      조정. 첫 행이 병합돼 칼럼을 구분 못 하면 건드리지 않음
    - 표 테두리 선 굵기 통일(삼선표): 위/아래 외곽선 0.5mm 실선, 헤더
      아래 이중선 0.5mm, 나머지 안쪽 구분선 0.12mm 실선, 좌우
      외곽선은 선 없음으로 통일
61. '다음 단어 당김'(통째로 밀린 단어를 앞줄로 끌어올리는 기능, 항목
    54/55)이 과도하게 넓은 범위에서 자간·장평을 축소하던 문제를 수정.
    양쪽정렬 문서에서는 거의 모든 줄이 "단어 경계에서 깔끔하게 끝난"
    상태라 조건이 쉽게 성립하는데, 정작 이 기능에는 짧은 마지막 줄
    병합(문장부호_줄병합_시도)과 달리 "끌어올릴 가치가 있을 때만"
    시도하는 길이 제한이 전혀 없었음. 이제 끌어올릴 다음 단어가
    문장부호_2줄_기준글자수(기본 5자)보다 길면 아예 시도하지 않고,
    시도하더라도 자간은 최대 10%p(기존 최대 30%p), 장평은 최대
    90%까지(기존 85%까지)만 쓰도록 좁힘
62. 실사용 로그에서 발견된 버그 수정: hwp.HwpUnitToPoint()/
    hwp.HwpUnitToMili()가 실제 한/글 자동화 API에는 없는 메서드였음
    (win32com 원시 객체 기준 "HwpFrame.HwpObject.HwpUnitToPoint" 오류로
    확인 — pyhwpx가 자기 래퍼 클래스에서 순수 파이썬 나눗셈으로
    흉내만 낸 편의 메서드를 실제 COM 메서드로 착각해 그대로 가져다
    쓴 것이 원인). 항목 59(문단 아래 간격 페이지 맞춤)와 항목 60의
    셀 너비 본문 맞춤이 영향을 받아, 값을 하나도 읽지 못한 채 매번
    조용히 실패(무시)하고 있었음. HwpUnit_pt()/HwpUnit_mm() 함수를
    새로 만들어 같은 비율(100 HwpUnit=1pt, 7200 HwpUnit=1인치)로
    직접 계산하도록 고침
63. '다음 단어 당김'(항목 55/61)이 같은 줄에서 성공할 때마다 반복
    호출되던 것을 한 줄당 한 번만 시도하도록 수정. 반복 호출 구조에서는
    '대체 가능'처럼 공백으로 나뉜 짧은 단어가 연달아 있으면, 두 번째
    시도가 첫 번째 시도로 이미 줄어든 자간/장평 값을 새 기준으로 삼아
    또 줄이는 식으로 압축이 누적됐음(각 시도의 상한은 지켜도 최종
    누적값은 상한을 훌쩍 넘김). 그 결과 항목 61에서 좁혀둔 상한과
    무관하게 긴 문장 전체가 한 줄로 욱여넣어지는 경우가 있었음
64. 처리 속도 검토(실사용 로그 기준 82문단 표준서식 처리에 약 18분
    소요, 그중 자간 조정 단계가 5~6분으로 최대): 문단_아래간격_일괄조정
    (항목 59, 페이지 수 맞춤)이 매 회 문서 전체를 훑던 것을, 쪽 번호를
    먼저 저렴하게 확인해(현재_페이지번호, COM 호출 1회) 목표 쪽수보다
    앞선 쪽의 문단은 비용이 큰 현재문단_텍스트() 읽기(COM 호출 약
    8회) 자체를 건너뛰도록 수정(페이지맞춤_뒤쪽범위_쪽수, 기본 2쪽).
    문서가 길수록 효과가 커짐. 자간 조정 엔진(단어모드_한글자 등)의
    글자당 COM 왕복 비용은 이번 세션에서 구조를 바꾸지 않음 — 자간
    조정 로직의 핵심이라 잘못 건드리면 정확성 문제로 이어질 위험이
    커서, 별도로 신중히 검토가 필요한 부분으로 남겨둠
65. 다음단어_당김_시도/단어_장평_추가축소_시도(항목 55/61/63)의 자간
    ±10%p·장평 90% 가이드라인이 "이번 시도에서 얼마나 더 줄이는가"가
    아니라 "최종적으로 얼마나 압축됐는가"를 기준으로 작동하도록 수정.
    자간/장평은 회차 사이나 단계 사이에 초기화되지 않으므로(문서_전체_
    자간_초기화는 이번 실행 시작 전 1회만 호출됨), 이전에 이미 압축된
    구간에 그대로 "추가로 10%p까지" 허용하면 누적되어 가이드라인이
    사실상 무의미해질 수 있었음. 이제 시도 전 해당 구간의 현재
    자간/장평 값을 먼저 확인해 "가이드라인 한도 - 이미 쓴 만큼"만큼만
    추가로 쓰고, 이미 한도를 넘겼으면 더 줄이지 않고 바로 실패로
    처리함(장평은 단계별로 넘어가고, 필요하면 결과 미해결로 검수
    목록에 남음)
66. 작업 완료 팝업에 문서(파일) 단위 성공/실패 개수뿐 아니라, 세부
    작업 항목(단어 중간 줄바꿈 방지·다음 단어 당김·짧은 마지막 줄
    병합·세트문장 페이지 맞춤) 기준 총 시도/성공/실패 건수도 함께
    표시. 새 단어분리_통계 카운터를 단어중간_줄바꿈방지()/
    다음단어_당김_시도()에 추가해, 기존 문장부호_통계·세트문장_통계와
    합산한 값을 "finished" 이벤트에 실어 팝업에 띄움(로그 파일에도
    "작업 항목 총계" 줄로 남음)

필요 패키지
------------------------------------------------------------
python -m pip install pywin32 tkinterdnd2
============================================================
"""

# Frozen smoke test runs before GUI/COM bootstrap and reports missing packages.
import sys as _selftest_sys
if __name__ == "__main__" and "--self-test" in _selftest_sys.argv:
    from docfit_app.self_test import check as _packaging_check, finish as _packaging_finish
    _packaging_result = _packaging_check()
    if not _packaging_result["ok"]:
        raise SystemExit(_packaging_finish(_packaging_result))

# Read-only CLI commands do not need Windows COM or GUI imports.
if __name__ == "__main__" and len(_selftest_sys.argv) > 1:
    from docfit_app.cli import is_cli_command as _early_cli, main as _early_cli_main
    if _selftest_sys.argv[1] in {"formats", "help", "--help", "-h", "/?"} and _early_cli(_selftest_sys.argv[1:]):
        raise SystemExit(_early_cli_main())

from docfit_engine.runtime import resolve as _engine_resolve
from docfit_engine.pipeline import PipelineCallbacks

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
import math
import zipfile
import base64
import zlib
import io
import struct
import tempfile
import uuid
import subprocess
import importlib
import hashlib
import difflib
import urllib.error
import urllib.parse
import http.client
import ssl
import webbrowser
from defusedxml import ElementTree as ET
from collections import Counter, defaultdict, deque
from tkinter import simpledialog
import datetime as _datetime
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilenames, askopenfilename, askdirectory, asksaveasfilename

from tkinterdnd2 import TkinterDnD, DND_FILES

import pythoncom
import win32com.client as win32
import win32gui
import win32con
from defusedxml.ElementTree import fromstring as safe_xml_fromstring
from docfit_core.batch_format import apply_batch, ParagraphStyle, BatchUnsupported
from docfit_core.updater import (expected_sha256 as 업데이트_예상해시, install_script as 업데이트_교체스크립트, launch_environment as 업데이트_실행환경,
                                 leftover_files as 업데이트_잔여파일, verify_download as 업데이트_파일검증)
from docfit_core.fidelity.package import UnsupportedPackage
from docfit_core.style_hierarchy import DOT_MARKERS, DOCUMENT_TYPES, analyze_hierarchy, display_role, document_type as 문서유형_판정, hierarchy_summary, leading_marker, normalize_leading_dot, stored_role
from docfit_core.style_unify import complement_ranges as 서식통일_범위분리, merge_adjacent as 서식통일_범위병합, parenthetical_spans as 서식통일_부연괄호, representative as 서식통일_최빈값
from docfit_core.style_unify import dominant as 서식통일_우세값, hierarchy_levels as 서식통일_계층순서, looks_like_cover as 서식통일_표지판정, unify_marker as 서식통일_항목기호, vocabulary_fallback as 서식통일_문서어휘_대표
from docfit_core.style_unify import attachment_heading as 서식통일_붙임제목, style_change_points as 서식통일_체계전환점
from docfit_core.number_check import 숫자_대조
from docfit_core import outline_ops
from docfit_core import format_samples as 서식예시모듈
from docfit_core.progress_guide import guide_key as 진행안내_키, guide_state as 진행안내_상태
from docfit_core.stage_selection import STAGE_EXAMPLES, default_choice as stage_default, enabled as stage_enabled, stages_for_mode
from docfit_core.stage_selection import TABLE_STAGE_KEYS as 표작업_키목록, without_tables as 표작업_제외
from docfit_core.stage_selection import without_page_fit as 페이지맞춤_제외
from docfit_core.page_fit_search import level_amounts as 쪽맞춤_레벨_줄임량, search_level as 쪽맞춤_레벨_탐색
from docfit_core.page_fit_search import classify_reports as 쪽맞춤_문서유형_판정
from docfit_core.stage_selection import CARD_OPTION_STAGES as 카드옵션_세부작업, card_option_from_stages as 카드옵션_판정
from docfit_core.stage_selection import card_option_off_keys as 카드옵션_끈작업, card_option_stage_values as 카드옵션_세부작업값
from docfit_core.stage_selection import card_option_turns_off as 카드옵션_끄는값
from docfit_core.document_rules import (
    ParagraphSpacingTracker, YEAR_QUOTE_PATTERN, marker_space_fix,
    curly_single_quote_replacements, normalize_date_range_marks, normalize_official_spacing,
    normalize_attachment_list_header,
    official_double_space_spans,
    paragraph_level, straight_double_quote_replacements, text_edit_spans,
)
from docfit_core.document_review import DOCUMENT_KINDS, PURPOSES, review_document
from docfit_core.final_evaluation import build_work_goal, evaluate_work, write_evaluation_report
from docfit_core.style_profile_edit import FIELDS as STYLE_FIELDS, ROLES as STYLE_ROLES, apply_reviewed_styles
from docfit_core.korean_proofread import (
    apply_approved_hwpx, load_exclusions, save_exclusions, scan_hwpx,
)
from docfit_core.pasted_text import clean_pasted_text, outline_pasted_text
from docfit_core.labeled_text import label_outline_text, looks_labeled, parse_labeled_text
from docfit_core.roman_heading import match_heading as roman_heading_match
from docfit_core.ai_answer import ai_answer_to_labeled_text, ai_answer_to_outline_text, looks_like_ai_answer
from docfit_core.asterisk_superscript import mark_spans as 별표_위치
from docfit_core.attachment_block import find_blocks as 붙임묶음_찾기
from docfit_core.attachment_block import blank_line_plan as 붙임_앞빈줄_계획
from docfit_core.attachment_block import (
    find_trailing_numbered_blocks as 끝붙임번호묶음_찾기,
    numbered_item_offset as 붙임번호_오프셋,
)
from docfit_core.abbreviations import merge_with_defaults as 준말_기본_병합, match_line as 준말_줄_판별, normalize as 준말_등록표_정리, roman_of_key as 준말_로마자, split_title2
from docfit_core.abbreviations import line_registry as 준말_줄변환표, table_style_of as 준말_표서식
from docfit_core.abbreviations import excluded_reason as 준말_제외사유
from docfit_core.table_style import HeaderPool as 표서식_저장소, apply_table_style as 표서식_적용, describe_style as 표서식_설명, is_design_table as 디자인표인가, is_grid_table as 표서식_모양인가
from docfit_core.table_style import learn_from_table as 표서식_한표학습, valid_style as 표서식_유효
from docfit_core.table_style import has_unit_caption as 단위캡션표인가, is_user_designed_table as 사용자표인가, protected_tables as 보호표_목록
from docfit_core.text_table import find_box_tables
from docfit_core import writing_aids, ai_prompts
from docfit_core.writing_aids import refresh_dates as 날짜_현행화


XML_네임스페이스_등록 = _engine_resolve('docfit_engine.com_driver', 'XML_네임스페이스_등록', globals())


XML_요소_생성 = _engine_resolve('docfit_engine.com_driver', 'XML_요소_생성', globals())


XML_자식_추가 = _engine_resolve('docfit_engine.com_driver', 'XML_자식_추가', globals())
from docfit_core.style_inventory import analyze_style_inventory, build_style_sample, inventory_markdown
from docfit_core import report_header as 보고서머리
from docfit_core import connector_tabs as 연결부호탭
from docfit_core import colon_labels as 콜론라벨
from docfit_core import spacing_reset as 자간초기화모듈
from docfit_core import char_ranges as 글자구간모듈
from docfit_core import text_edit as 글고치기모듈
from docfit_core import format_elements as 서식요소
from docfit_core.table_width import fit_table as 표너비_맞춤, host_reserve as 표너비_앞자리, is_target as 표너비_대상인가
from docfit_core import (
    KordocUnavailableError,
    analyze_form,
    analyze_tables,
    compare_documents,
    compare_documents_advanced,
    export_advanced_markdown,
    export_common_ir,
    export_markdown,
    export_rag_chunks,
    fill_form,
    generate_hwpx,
    inspect_hwpx,
    validate_and_inspect_hwpx,
    kordoc_engine_version,
    lint_document,
    parse_document,
    patch_document,
    render_preview,
    validate_hwpx,
    open_hwpx_safely,
)

# ============================================================
# 프로그램 정보
# ============================================================

APP_NAME = "한글편집 후처리"
APP_VERSION = "2.0.3"
PROJECT_URL = "https://gitlab.aigov.go.kr/haijun93/hwp_autodocfit"
UPDATE_API_URL = "https://gitlab.aigov.go.kr/api/v4/projects/haijun93%2Fhwp_autodocfit/releases/permalink/latest"
GITHUB_UPDATE_API_URL = "https://api.github.com/repos/haijun93/hwp-auto-docfit/releases/latest"
UPDATE_ASSET_NAME = "HWP_AutoDocFit.exe"
_업데이트_허용_호스트 = "gitlab.aigov.go.kr"
# GitHub 릴리스 파일은 github.com에서 githubusercontent.com 계열 주소로 넘어간다(리디렉션).
_업데이트_허용_호스트들 = (_업데이트_허용_호스트, "api.github.com", "github.com")
_업데이트_허용_호스트_접미사 = (".githubusercontent.com",)


_업데이트_URL_검증 = _engine_resolve('docfit_engine.com_driver', '_업데이트_URL_검증', globals())


_업데이트_HTTP_GET = _engine_resolve('docfit_engine.com_driver', '_업데이트_HTTP_GET', globals())


_업데이트_기록 = _engine_resolve('docfit_engine.com_driver', '_업데이트_기록', globals())


UPDATE_STARTED_FLAG = "app_started.flag"   # 새 버전이 켜졌다는 신호(교체 스크립트가 확인 뒤 백업을 지운다)
UPDATE_BUSY_FLAG = "update_busy.flag"      # 교체 스크립트가 도는 중(이때는 시작 정리가 백업을 지우지 않는다)


업데이트_시작신호 = _engine_resolve('docfit_engine.com_driver', '업데이트_시작신호', globals())


업데이트_잔여정리 = _engine_resolve('docfit_engine.com_driver', '업데이트_잔여정리', globals())


_버전_튜플 = _engine_resolve('docfit_engine.com_driver', '_버전_튜플', globals())


_최신_릴리스_조회 = _engine_resolve('docfit_engine.com_driver', '_최신_릴리스_조회', globals())


_최신_릴리스_통합_조회 = _engine_resolve('docfit_engine.com_driver', '_최신_릴리스_통합_조회', globals())


_업데이트_자산_선택 = _engine_resolve('docfit_engine.com_driver', '_업데이트_자산_선택', globals())

# ============================================================
# AutomationModule
# ============================================================

DLL_NAME = "MapoHwpAutoDocFitSecurity.dll"
# 알파(2026-10-10 사용자 요청): 최상위 앱 폴더를 C:\HwpAutomation에서 C:\HWP_AUTODOCFIT로 바꾸고, 그 아래
# '서식예시' 폴더에 서식마다 예시 HWPX를 둔다. 사용자가 예시 파일을 고치면 '한 번에 적용'을 시작할 때 바뀐 서식 값을
# 설정에 옮긴다(서식예시모듈). 끄면 예전 폴더(C:\HwpAutomation)와 설정 폴더의 예시 보관 방식으로 돌아간다.
알파_서식예시폴더_사용 = True
HWP_AUTOMATION_DIR = 서식예시모듈.APP_HOME if 알파_서식예시폴더_사용 else 서식예시모듈.LEGACY_APP_HOME
# 알파(2026-10-10 사용자 요청): 보안 모듈 DLL은 앱 폴더의 dll 하위 폴더에 HwpAutoDocFitSecurity.dll로 두고, 레지스트리 값
# 이름도 HwpAutoDocFitSecurity로 바꾼다. 앱에 포함된 원본 DLL 파일 이름(DLL_NAME)은 그대로다.
DLL_DIR = 서식예시모듈.app_subfolder(서식예시모듈.DLL_FOLDER_NAME, HWP_AUTOMATION_DIR) if 알파_서식예시폴더_사용 else HWP_AUTOMATION_DIR
TARGET_DLL = DLL_DIR / (서식예시모듈.DLL_FILE if 알파_서식예시폴더_사용 else DLL_NAME)
REGISTRY_PATH = r"Software\HNC\HwpAutomation\Modules"
# 한/글은 RegisterModule의 두 번째 인자와
# ...\HwpAutomation\Modules 아래 레지스트리 값 이름이 같아야 한다.
# 공용 예제 이름 대신 이 프로젝트 전용 이름을 사용한다.
REGISTRY_VALUE_NAME = 서식예시모듈.REGISTRY_VALUE if 알파_서식예시폴더_사용 else 서식예시모듈.LEGACY_REGISTRY_VALUE
REGISTER_MODULE_NAME = "FilePathCheckDLL"
REGISTER_MODULE_VALUE = REGISTRY_VALUE_NAME


한글_COM_인스턴스_생성 = _engine_resolve('docfit_engine.com_driver', '한글_COM_인스턴스_생성', globals())


한글_문서_열기 = _engine_resolve('docfit_engine.com_driver', '한글_문서_열기', globals())

# ============================================================
# 전역 상태
# ============================================================

hwp = None
gui_queue = queue.Queue()
로그_파일_경로 = None
로그파일_사용 = False    # 작업 로그(.log) 파일을 만들지 여부(기본 꺼짐)
로그_파일_잠금 = threading.Lock()
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

작업_모드 = "all"
# 문두 라벨 굵게에서 뺄 기호(False). 별표(*, **)도 기본으로 뺀다(2026-10-03 사용자 요청).
문두라벨_기호설정 = {"□": False, "ㅁ": False, "※": False, "*": False, "**": False}
표준서식_사용 = False

# 자간 정리에서 표(셀) 안 문장을 대상에 넣을지 여부. False면 표 안 문장은 제외한다.
표_자간조정_사용 = True
# 쪽 범위 작업: 요청값(시작쪽, 끝쪽|None)과, 문서를 연 뒤 처음 한 번 고정한 값.
# 처리 중 줄이 줄어 쪽 경계가 밀려도 범위가 흔들리지 않도록 문단·영역 번호로 고정한다.
쪽범위_요청 = None
쪽범위_실제 = None
쪽범위_본문_문단 = None
쪽범위_컨트롤영역 = set()

표준서식_여백_사용 = True
# 쪽 맞춤: 서식의 위·아래 쪽 여백이 기본값 그대로(따로 정하지 않음)이면 이 값(mm)까지 줄여 목표 쪽에 담아 본다(2026-10-23 사용자 요청).
쪽맞춤_위아래여백_최소_mm = 5.0
표준서식_장평_사용 = True
표준서식_줄간격_사용 = True
표준서식_제목_사용 = True
표준서식_일자담당자_사용 = True
표준서식_기호_사용 = True
표준서식_내어쓰기_사용 = True

표준서식_제목_굵게 = True
표준서식_일자담당자_굵게 = True

표준서식_기호_굵게 = {
    "□": True,
    "ㅇ": True,
    "-": False,
    "※": False,
}

표준서식_문단위간격_사용 = True
# 계층별 문단 위 여백 기본값(2026-10-05 사용자 정의): 2~4단계(장·중제목·□) 15pt, 5단계(ㅇ) 8pt,
# 6단계(-) 4pt, 그 밖의 항목기호(*·※·• 등) 0pt.
표준서식_문단위간격_chapter_pt = 15
표준서식_문단위간격_midtitle_pt = 15
표준서식_문단위간격_box_pt = 15
표준서식_문단위간격_circle_pt = 8
표준서식_문단위간격_dash_pt = 4
표준서식_문단위간격_note_pt = 0
표준서식_문단위간격_복귀배율 = 150
_표준서식_문단위간격_상태 = ParagraphSpacingTracker()

표_헤더서식_사용 = True
표_헤더서식_헤더_폰트 = "한컴돋움"
표_헤더서식_헤더_크기 = 13
표_헤더서식_헤더_굵게 = True
표_헤더서식_본문_폰트 = "휴먼명조"
표_헤더서식_본문_크기 = 12
표_헤더서식_본문_굵게 = False
활성_정밀표_프로필 = None
# 선택한 서식 프로필이 예시 문서에서 보관한 서식 표(제목·개요·중제목·붙임) 예시.
# {종류: {"header_xml", "table_xml"}}. 없는 종류는 내장 기준 표를 쓴다.
활성_서식표_프로필 = None
# 알파(2026-10-10): 선택한 서식 프로필이 예시 문서에서 배운 보고서 머리(제목·보고 주체·개요) 구성과 표기 틀.
# 정부기관 보고서마다 제목(1×1 상자·2×2·2행1열·문단)과 보고 주체 표기("2026. 10. 7.  기관  부서",
# "'26. 10. 7.(수)  /  과", "(날짜, 과장 홍길동, ☎…)")가 달라, 서식 복사 때 이 구성을 대상 문서에 그대로 옮긴다.
알파_머리서식복사_사용 = True
활성_머리서식_프로필 = None
# 선택한 서식 프로필이 예시 보고서의 일반 표에서 배운 기본 표 서식(table_style). 있으면 준말 '표' 서식보다
# 먼저 쓴다(2026-10-04 결정 5).
활성_표서식_프로필 = None
활성_서식예시_파일 = None
활성_항목기호_체계 = None

표준서식_설정 = {
    "여백_mm": {
        "left": 20,
        "right": 20,
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
    # 행정안전부 개조식 보고서 작성 표준(□0칸→ㅇ1칸→―2칸→·/*3칸)에 맞춘
    # 기호 앞 들여쓰기 칸수(각 튜플의 두 번째 값)다. "-"/"※"는 각각
    # 3단계(―)와 4단계(·/*)와 같은 자리에 선다.
    # 2단계 장(제1장·2장·Chapter 3 …). 문두가 문서마다 달라 기호 대신 역할로 찾는다(표준서식_기호규칙_찾기).
    # 규칙의 기호 자리는 '(장)'이며, 문단 모양 복사·속성 선택도 이 이름을 쓴다(2026-10-04).
    "장_규칙": ("(장)", 0, "HY헤드라인M", 20, True, False),
    "기호_규칙": [
        ("□", 0, "HY견고딕", 17, False, True),
        ("ㅇ", 1, "한컴돋움", 15, True, False),
        # - 앞 3칸: 기준 문서 '1) 보고서(계획서) 서식.hwpx'(사용자 지정 2026-10-08).
        ("-", 3, "휴먼명조", 14, False, False),
        ("※", 3, "한컴돋움", 13, False, False),
        # *(주석1)의 대표 항목기호는 *이며(**는 여기로 합침), 기본값은 ※와 같다.
        ("*", 3, "한컴돋움", 13, False, False),
        ("•", 3, "한컴돋움", 13, False, False),
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
    "chapter": 표준서식_문단위간격_chapter_pt,
    "midtitle": 표준서식_문단위간격_midtitle_pt,
    "box": 표준서식_문단위간격_box_pt,
    "circle": 표준서식_문단위간격_circle_pt,
    "dash": 표준서식_문단위간격_dash_pt,
    "note": 표준서식_문단위간격_note_pt,
}

_표준서식_문단위간격_표 = _engine_resolve('docfit_engine.formatter', '_표준서식_문단위간격_표', globals())


기본_계층_스타일 = _engine_resolve('docfit_engine.formatter', '기본_계층_스타일', globals())


표준서식_문단위간격_찾기 = _engine_resolve('docfit_engine.formatter', '표준서식_문단위간격_찾기', globals())

문장기호_목록 = ["□", "ㅇ", "-", "※", "*", "•"]


기호글꼴_적용 = _engine_resolve('docfit_engine.formatter', '기호글꼴_적용', globals())


표글꼴_적용 = _engine_resolve('docfit_engine.formatter', '표글꼴_적용', globals())


_hwp_설치폴더_후보_레지스트리 = _engine_resolve('docfit_engine.formatter', '_hwp_설치폴더_후보_레지스트리', globals())


_hwp_설치폴더_후보_공통경로 = _engine_resolve('docfit_engine.formatter', '_hwp_설치폴더_후보_공통경로', globals())


한글_폰트_폴더_자동감지 = _engine_resolve('docfit_engine.formatter', '한글_폰트_폴더_자동감지', globals())


_ttf_패밀리이름 = _engine_resolve('docfit_engine.formatter', '_ttf_패밀리이름', globals())


한글_폰트_목록 = _engine_resolve('docfit_engine.formatter', '한글_폰트_목록', globals())


한컴_번들_폰트_폴더_목록 = _engine_resolve('docfit_engine.formatter', '한컴_번들_폰트_폴더_목록', globals())


한글_폰트_목록_전체 = _engine_resolve('docfit_engine.formatter', '한글_폰트_목록_전체', globals())


서식_기본값_전역_복원 = _engine_resolve('docfit_engine.formatter', '서식_기본값_전역_복원', globals())

검수_사용 = False
검수_문제목록 = []
최종검수_문서목록 = []
무결성보고서파일_사용 = False
최종검수보고서파일_사용 = True
현재_처리파일 = None
단어중간_줄바꿈방지_사용 = False
문장부호_2줄_기준글자수 = 5
자간_최대시도_본문 = 30
자간_최대시도_표 = 5

# '다음 단어 당김'(통째로 밀린 단어를 앞줄로 끌어올리는 기능) 전용 상한.
# 이 기능은 문서의 거의 모든 줄(양쪽정렬에서 단어 경계로 깔끔하게 끝나는
# 줄)에서 조건이 성립하므로, 짧은 마지막 줄 병합처럼 "끌어올릴 가치가
# 있을 때만"(다음 단어가 문장부호_2줄_기준글자수 이하일 때만) 시도한다.
# 축소 폭도 원래 설계 예시(자간 -1%~-10%, 장평 90~99%)를 넘지 않도록
# 자간_최대시도_본문/표(최대 -30%p)와는 별도로 더 좁게 둔다.
다음단어_당김_자간_최대_퍼센트 = 10
# 자간 조정 → 내어쓰기 재적용 → 자간 재검사 반복의 최대 횟수(무한 반복 방지).
자간_내어쓰기_최대반복 = 3
# 2차 이후 재검사는 내어쓰기 값이 실제로 바뀐 문단만 대상으로 한다.
# None이면 전체 문단, 집합이면 (리스트, 문단) 번호가 들어 있는 문단만 검사한다.
재검사_대상문단 = None
# 가장 최근 내어쓰기 전체 갱신에서 값이 바뀐 문단의 (리스트, 문단) 번호.
내어쓰기_변경문단 = set()
# 선택적 '다음 단어 당김'은 1차에서만 시도한다. 2차 이후에 켜 두면 1차에서
# 방향 규칙에 따라 다음 줄로 밀어 둔 어절을 다시 끌어올려 규칙을 뒤집고,
# 이미 실패한 당김을 매 차수 반복해 시간만 쓴다.
다음단어_당김_사용 = True
단어_장평_추가축소_최대_단계 = 10  # 장평 100% -> 90%까지만(기존 15단계=85%에서 축소)
# 장평 줄이기 사용(설정 'ratio_shrink', 기본 끔, 2026-10-10 사용자 규칙): 끄면 자간 조정 중 장평 축소(단어 분리 보정의
# 장평 추가 축소·자간 한도 뒤 장평 단계 축소)와 콜론 라벨 정렬의 장평 늘리기를 쓰지 않고 자간·빈칸만 쓴다.
장평_줄이기_사용 = False

# 한 문단의 앞쪽 줄 수가 더 많거나 같으면 앞쪽 전체부터 해당 문단까지 축소.
# 더 적으면 해당 문단 앞의 문단만 확대해 뒤쪽으로 이동. 단계당 10%p, 최대 6단계.
세트문장_같은쪽_사용 = True
세트문장_페이지줄간격_최대시도 = 6
# 줄간격 조정은 160~200% 범위 밖으로 나가지 않는다. 이 범위를 벗어나는
# 축소/확대는 금지한다.
세트문장_최소줄간격_퍼센트 = 160
세트문장_최대줄간격_퍼센트 = 200

# 마지막 쪽에 몇 줄 안 되는 내용만 넘어가 있으면(예: 2~3줄), 본문 줄간격은
# 그대로 두고 항목기호 문단의 '문단 아래 간격'만 1pt씩 줄여 앞쪽 쪽으로
# 당겨오는 걸 시도한다. 마지막 쪽 줄 수가 이 값을 넘으면(내용이 많이 남은
# 경우) 간격을 조금 줄이는 정도로는 해결이 안 되므로 시도하지 않는다.
페이지맞춤_문단간격_사용 = True
페이지맞춤_최대남은줄수 = 4
페이지맞춤_최대_pt = 10.0
페이지맞춤_스텝_pt = 1.0
# 조정 대상 문단을 "목표 쪽수보다 이 값만큼 앞선 쪽부터"로만 제한한다.
# 문단마다 텍스트를 읽는 데 COM 왕복이 여러 번 드는데, 페이지 수를
# 맞추는 데 필요한 문단은 어차피 마지막 몇 쪽에 몰려 있으므로 문서
# 전체를 훑을 필요가 없다 — 긴 문서일수록 이 제한의 효과가 커진다.
페이지맞춤_뒤쪽범위_쪽수 = 2
# 문서 세로 조정(페이지 수 맞춤) 시 표 셀의 상하 안쪽 여백도 함께 비례 축소한다.
페이지맞춤_표셀세로여백_사용 = True
페이지맞춤_표셀세로여백_최소_pt = 0.0
# 쪽 수 맞춤을 대상 위치를 한 번만 조사한 뒤 줄임 정도(레벨)를 이분 탐색으로 찾는다. 끄면 기존처럼
# 1단계씩 줄이며 매번 문서 전체를 다시 훑는다(실측: 단계당 15~34초, 문서당 6~15분). 결과가 어긋나면 기존 방식으로 되돌아간다.
페이지맞춤_고속_사용 = True
# 쪽 수 맞춤 전에 문서 유형(1쪽 보고서·심화보고서·취합보고서)을 판정해 1쪽 보고서는 보고서마다 1쪽에 담는다.
쪽맞춤_유형판정_사용 = True
# 마지막 문서 유형별 쪽 맞춤이 쪽 나눔을 넣거나 보고서를 1쪽에 맞춰 배치를 바꿨는지(재확인 뒤 쪽 배치 재검사용).
쪽맞춤_보고서조정됨 = False
# 문서를 연 직후(처리 전) 잰 보고서별 [(쪽 수, 쪽 첫 줄에서 시작했는지)]. 결과에서도 보고서마다 이 쪽 수 안에 담는다.
쪽맞춤_원본_보고서 = None
# 마지막으로 찾은 보고서 제목 표의 본문 문단 번호(쪽 배치가 앞 보고서 문장과 다음 제목 표를 한 묶음으로 보지 않게).
쪽맞춤_제목문단 = set()
# 보고서 쪽 맞춤이 문단 모양을 고친 본문 문단 (리스트, 문단). 고친 문단은 한/글이 줄 배치를 다시 계산해 숨어 있던
# 단어 분리가 드러나므로(2026-10-09 실측: '판매장터'), 맞춤이 끝나면 이 문단만 단어 분리를 다시 검사한다.
쪽맞춤_바꾼문단 = set()

문장부호_통계 = {"대상": 0, "성공": 0, "실패": 0}
세트문장_통계 = {"대상": 0, "성공": 0, "실패": 0, "축소횟수": 0, "확대횟수": 0}
단어분리_통계 = {"대상": 0, "성공": 0, "실패": 0}
다음단어_통계 = {"대상": 0, "적용": 0, "미적용": 0}

프로그램_폴더 = _engine_resolve('docfit_engine.formatter', '프로그램_폴더', globals())

번들_리소스_폴더 = _engine_resolve('docfit_engine.formatter', '번들_리소스_폴더', globals())

# ============================================================
# 사용자 설정 저장/불러오기
# ============================================================

설정_파일명 = "settings.json"

from docfit_app.settings_schema import DEFAULTS as _설정_기본값
기본_설정 = copy.deepcopy(_설정_기본값)


# 첨부 버전의 서식값을 기본 서식으로 고정한다.
# 사용자 PC의 settings.json은 별도로 유지하며 초기화할 때 이 값을 사용한다.
기본_서식프로파일 = _engine_resolve('docfit_engine.formatter', '기본_서식프로파일', globals())


서식프로파일_목록 = _engine_resolve('docfit_engine.formatter', '서식프로파일_목록', globals())
_제목뒤간격_다시재기 = _engine_resolve('docfit_engine.formatter', '_제목뒤간격_다시재기', globals())


_표_텍스트 = _engine_resolve('docfit_engine.formatter', '_표_텍스트', globals())


_표_서명 = _engine_resolve('docfit_engine.formatter', '_표_서명', globals())


_정밀표_프로필_추출 = _engine_resolve('docfit_engine.formatter', '_정밀표_프로필_추출', globals())


hwpx_서식_분석 = _engine_resolve('docfit_engine.formatter', 'hwpx_서식_분석', globals())


보고서머리_프로필_반영 = _engine_resolve('docfit_engine.formatter', '보고서머리_프로필_반영', globals())


_정렬이름 = {"LEFT": "왼쪽", "RIGHT": "오른쪽", "CENTER": "가운데", "JUSTIFY": "양쪽", "DISTRIBUTE": "배분"}


보고서머리_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '보고서머리_hwpx_처리', globals())


예시문서_기본이름 = _engine_resolve('docfit_engine.formatter', '예시문서_기본이름', globals())


_분석본_보관 = _engine_resolve('docfit_engine.formatter', '_분석본_보관', globals())


한글파일_서식_분석 = _engine_resolve('docfit_engine.formatter', '한글파일_서식_분석', globals())


교정용_hwpx_준비 = _engine_resolve('docfit_engine.formatter', '교정용_hwpx_준비', globals())


분석용_hwpx_준비 = _engine_resolve('docfit_engine.formatter', '분석용_hwpx_준비', globals())


스타일분석_파일생성 = _engine_resolve('docfit_engine.formatter', '스타일분석_파일생성', globals())


스타일분석_요약 = _engine_resolve('docfit_engine.formatter', '스타일분석_요약', globals())


서식프로파일_표시이름 = _engine_resolve('docfit_engine.formatter', '서식프로파일_표시이름', globals())


문서_markdown_내보내기 = _engine_resolve('docfit_engine.formatter', '문서_markdown_내보내기', globals())


# 문단 여백·간격 COM 항목. 복사_문단모양은 HWPX case 값(실제 HWPUNIT)을 담고, COM ParaShape는 그
# 두 배 값을 쓴다(실측 2026-10-03: COM 왼쪽 여백 2000 → HWPX case 1000, 줄 시작 위치 1000).
_문단여백_COM항목 = ("LeftMargin", "RightMargin", "Indentation", "PrevSpacing", "NextSpacing")


복사_문단모양_적용 = _engine_resolve('docfit_engine.formatter', '복사_문단모양_적용', globals())


# 계층별 추가 서식 값 → 한/글 COM 값(실측 2026-10-04: 정렬 0 양쪽·1 왼쪽·2 오른쪽·3 가운데·4 배분·5 나눔,
# 밑줄 1 아래·2 가운데·3 위, 한글 줄 나눔 BreakNonLatinWord 1 어절·0 글자)
_정렬_COM = {"JUSTIFY": 0, "LEFT": 1, "RIGHT": 2, "CENTER": 3, "DISTRIBUTE": 4, "DISTRIBUTE_SPACE": 5}
_밑줄_COM = {"BOTTOM": 1, "CENTER": 2, "TOP": 3}
_언어별_장평 = ("RatioHangul", "RatioLatin", "RatioHanja", "RatioJapanese", "RatioOther", "RatioSymbol", "RatioUser")
_언어별_자간 = ("SpacingHangul", "SpacingLatin", "SpacingHanja", "SpacingJapanese", "SpacingOther",
              "SpacingSymbol", "SpacingUser")


계층_추가서식_값 = _engine_resolve('docfit_engine.formatter', '계층_추가서식_값', globals())


# 서식 복사 간격 규칙 상태(표준서식_전체_적용이 문서마다 초기화). 정리할 문서에 제목 표가 있는지는 XML 단계가 알린다.
_문서_제목표_있음 = False
_간격규칙_상태 = {"첫문장": False, "직전깊이": None}


복사_간격_규칙_적용 = _engine_resolve('docfit_engine.formatter', '복사_간격_규칙_적용', globals())


계층_추가서식_적용 = _engine_resolve('docfit_engine.formatter', '계층_추가서식_적용', globals())


_제목2종_XML = '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'

# 첨부한 제목 표의 원본 XML을 내장한다(외부 서식파일 불필요). 제목 유형은 2×2 제목+날짜·담당자 2종(1·2)과
# 2행1열 제목+담당자(3, 별도 기준표)이며 1×1 제목 표는 제목 서식 대상이 아니다.
# (변수명 제목4종_사용은 설정 호환을 위해 옛 이름을 유지한다.)
제목4종_사용 = True
붙임2종_사용 = True
중제목_사용 = True
중제목_번호굵게 = True

_개요붙임3종_XML = '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'

# 첨부한 '중제목' 표(로마자 번호 + 글)의 기준 서식. 번호·글 모두 HY견고딕 20pt로 정규화해 내장한다.
# 기준 모양은 Ⅰ·Ⅱ 표(검은 0.5mm 테두리)이며, Ⅲ 표의 남색(#1D1E42) 변형은 쓰지 않는다.
_중제목_XML = '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'

# 제목 서식2: 2행1열 표(윗칸 부제+제목, 아랫칸 담당자). 날짜 칸이 없는 제목 표의 기준 서식.
_제목2행1열_XML = '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'

개요붙임_원본자료 = _engine_resolve('docfit_engine.formatter', '개요붙임_원본자료', globals())

붙임_유형판별 = _engine_resolve('docfit_engine.formatter', '붙임_유형판별', globals())

붙임_대상찾기 = _engine_resolve('docfit_engine.formatter', '붙임_대상찾기', globals())

# 중제목 번호 칸: 서식(HY견고딕 20pt 등)을 입히는 표는 로마자 번호(Ⅰ·Ⅱ, I·V)만, 글 칸 폭을 맞추는 표는 아라비아 숫자
# 번호(1·01·1.)도 본다(2026-10-04). 숫자 번호 표는 로마자 중제목 아래 소제목인 경우가 많아 서식은 그대로 둔다.
_중제목_번호 = re.compile(r'^(?:[Ⅰ-ⅿ]+|[IVX]{1,4})\s*[.．]?$')
_중제목_번호_숫자포함 = re.compile(r'^(?:[Ⅰ-ⅿ]+|[IVX]{1,4}|\d{1,2})\s*[.．]?$')
_중제목_글자폭_pt = 20


중제목_글칸들 = _engine_resolve('docfit_engine.formatter', '중제목_글칸들', globals())


중제목_유형판별 = _engine_resolve('docfit_engine.formatter', '중제목_유형판별', globals())


중제목_대상찾기 = _engine_resolve('docfit_engine.formatter', '중제목_대상찾기', globals())


중제목_원본자료 = _engine_resolve('docfit_engine.formatter', '중제목_원본자료', globals())


_구역_본문폭 = _engine_resolve('docfit_engine.formatter', '_구역_본문폭', globals())


_예정_좌우여백 = _engine_resolve('docfit_engine.formatter', '_예정_좌우여백', globals())


_최종_본문폭 = _engine_resolve('docfit_engine.formatter', '_최종_본문폭', globals())


_빈_문단인가 = _engine_resolve('docfit_engine.formatter', '_빈_문단인가', globals())


_문단사이_빈줄_삭제 = _engine_resolve('docfit_engine.formatter', '_문단사이_빈줄_삭제', globals())


_문단_본문글 = _engine_resolve('docfit_engine.formatter', '_문단_본문글', globals())


_서식표_뒤_빈줄_삭제 = _engine_resolve('docfit_engine.formatter', '_서식표_뒤_빈줄_삭제', globals())


_서식표_가로맞춤 = _engine_resolve('docfit_engine.formatter', '_서식표_가로맞춤', globals())


_중제목_번호굵게_적용 = _engine_resolve('docfit_engine.formatter', '_중제목_번호굵게_적용', globals())


중제목_표서식_복사 = _engine_resolve('docfit_engine.formatter', '중제목_표서식_복사', globals())


_중제목_글자치수 = _engine_resolve('docfit_engine.formatter', '_중제목_글자치수', globals())


_중제목_문단폭 = _engine_resolve('docfit_engine.formatter', '_중제목_문단폭', globals())


_중제목_칸폭_맞춤 = _engine_resolve('docfit_engine.formatter', '_중제목_칸폭_맞춤', globals())


개요_표인가 = _engine_resolve('docfit_engine.formatter', '개요_표인가', globals())

제목_xml이름 = _engine_resolve('docfit_engine.formatter', '제목_xml이름', globals())

제목_자식 = _engine_resolve('docfit_engine.formatter', '제목_자식', globals())

제목_셀들 = _engine_resolve('docfit_engine.formatter', '제목_셀들', globals())

제목_문단들 = _engine_resolve('docfit_engine.formatter', '제목_문단들', globals())

제목_문자열 = _engine_resolve('docfit_engine.formatter', '제목_문자열', globals())

# 1×1 제목 상자의 글자 크기 하한(pt). 개요·요약 상자(보통 13~15pt)와 가른다(korean-report-hwpx 제목 20pt,
# 마포구청 제목 표 27pt 실측).
한칸_제목_최소크기_pt = 16


_한칸_제목글인가 = _engine_resolve('docfit_engine.formatter', '_한칸_제목글인가', globals())


_기타_제목표인가 = _engine_resolve('docfit_engine.formatter', '_기타_제목표인가', globals())


_한칸_제목표인가 = _engine_resolve('docfit_engine.formatter', '_한칸_제목표인가', globals())


제목_유형판별 = _engine_resolve('docfit_engine.formatter', '제목_유형판별', globals())


제목_대상찾기 = _engine_resolve('docfit_engine.formatter', '제목_대상찾기', globals())


서식표_종류판별 = _engine_resolve('docfit_engine.formatter', '서식표_종류판별', globals())


_서식표_예시 = _engine_resolve('docfit_engine.formatter', '_서식표_예시', globals())


제목2행1열_원본자료 = _engine_resolve('docfit_engine.formatter', '제목2행1열_원본자료', globals())


제목_원본자료 = _engine_resolve('docfit_engine.formatter', '제목_원본자료', globals())


제목_참조병합 = _engine_resolve('docfit_engine.formatter', '제목_참조병합', globals())


# 날짜: 연·월·일(’26. 10. 10. / 2026년 10월 10일 / 2026-10-10) 또는 요일이 붙은 월·일(10. 6.(화)).
_제목_날짜 = re.compile(r"[’'‘`]?\d{2,4}\s*[.년/\-]\s*\d{1,2}\s*[.월/\-]\s*\d{1,2}"
                    r"|\d{1,2}\s*[.월]\s*\d{1,2}\s*[.일]?\s*\(\s*[월화수목금토일]\s*\)")


날짜칸인가 = _engine_resolve('docfit_engine.formatter', '날짜칸인가', globals())


표_날짜칸_한줄 = _engine_resolve('docfit_engine.formatter', '표_날짜칸_한줄', globals())


표날짜칸_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '표날짜칸_hwpx_처리', globals())
두글자칸_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '두글자칸_hwpx_처리', globals())
빈줄서식_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '빈줄서식_hwpx_처리', globals())
강조낱말_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '강조낱말_hwpx_처리', globals())
개요첫칸_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '개요첫칸_hwpx_처리', globals())


제목_날짜칸_한줄 = _engine_resolve('docfit_engine.formatter', '제목_날짜칸_한줄', globals())


제목_표서식_복사 = _engine_resolve('docfit_engine.formatter', '제목_표서식_복사', globals())


_정밀표_매칭점수 = _engine_resolve('docfit_engine.formatter', '_정밀표_매칭점수', globals())


_정밀표_셀서식_복사 = _engine_resolve('docfit_engine.formatter', '_정밀표_셀서식_복사', globals())
_정밀표_글자위치_복사 = _engine_resolve('docfit_engine.formatter', '_정밀표_글자위치_복사', globals())
_표_글_그대로 = _engine_resolve('docfit_engine.formatter', '_표_글_그대로', globals())


_정밀표_같은표만 = _engine_resolve('docfit_engine.formatter', '_정밀표_같은표만', globals())


_정밀표_글같음 = _engine_resolve('docfit_engine.formatter', '_정밀표_글같음', globals())


정밀표_서식_적용 = _engine_resolve('docfit_engine.formatter', '정밀표_서식_적용', globals())



제목_문단_가운데정렬 = _engine_resolve('docfit_engine.formatter', '제목_문단_가운데정렬', globals())


제목_괄호부연_축소 = _engine_resolve('docfit_engine.formatter', '제목_괄호부연_축소', globals())

제목_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '제목_hwpx_처리', globals())


_제목_임시hwpx_저장 = _engine_resolve('docfit_engine.formatter', '_제목_임시hwpx_저장', globals())


_작업_임시폴더_접두어 = ("hwp_format_first_", "hwp_precise_table_", "docfit_외부문서_", "hwp_table_guard_",
                   "docfit_hwp_to_hwpx_", "docfit_sample_")  # 오류·중단으로 남은 문서 사본도 다음 실행 때 정리


이전_작업_임시폴더_정리 = _engine_resolve('docfit_engine.formatter', '이전_작업_임시폴더_정리', globals())


_제목_임시폴더_정리 = _engine_resolve('docfit_engine.formatter', '_제목_임시폴더_정리', globals())


서식구조_조사 = _engine_resolve('docfit_engine.formatter', '서식구조_조사', globals())


제목4종_현재문서_조사 = _engine_resolve('docfit_engine.formatter', '제목4종_현재문서_조사', globals())


제목4종_현재문서_적용 = _engine_resolve('docfit_engine.formatter', '제목4종_현재문서_적용', globals())


붙임_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '붙임_hwpx_처리', globals())

중제목_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '중제목_hwpx_처리', globals())


# 라벨 입력 모드(제목1:/제목2:/개요:)가 한/글에 넣은 1×1 표의 첫 칸에 붙이는 표식. 저장한 HWPX에서
# 이 표식이 붙은 표를 찾아 해당 서식 표로 바꾸고 표식은 지운다. (키는 서식 표 종류)
_라벨_표식 = {'title1': '@@DOCFIT:제목1@@', 'title2': '@@DOCFIT:제목2@@', 'overview': '@@DOCFIT:개요@@'}
_라벨_블록_종류 = {'title1': 'title1', 'title2': 'title2', 'box': 'overview'}  # 블록 종류 → 서식 표 종류


# 서식 표 종류 → 기준 자료 묶음(한 묶음의 기준 표는 header에 한 번만 병합한다)
_서식표_묶음 = {'title1': '제목', 'title1부제': '제목', 'title2': '제목2행1열', 'overview': '개요붙임',
               'attach1': '개요붙임', 'attach2': '개요붙임', 'midtitle': '중제목'}


# 서식 표 종류 → 서식 프로필 예시 표 종류(라벨의 'title2'는 2행1열 제목 = 제목 유형3)
_서식표_예시종류 = {'title1': 'title1', 'title1부제': 'title2', 'title2': 'title3', 'overview': 'overview',
                 'attach1': 'attach1', 'attach2': 'attach2', 'midtitle': 'midtitle1'}

# 제목 서식의 부제(제목 글의 첫 쉼표 앞 글) 글자 크기(pt). 내장 기준 표에 쓴다(서식 프로필 예시 표는 그 표의 크기).
# 기본값 15pt(2026-10-03 사용자 요청, 잠시 17pt였음). 설정창 '제목 부제 크기'(std_title_subtitle_pt)로 바꾼다.
제목_부제_크기_pt = 15


제목_부제_크기_해석 = _engine_resolve('docfit_engine.formatter', '제목_부제_크기_해석', globals())


제목_부제_크기_반영 = _engine_resolve('docfit_engine.formatter', '제목_부제_크기_반영', globals())


# 새로 만드는 제목 서식 표 담당자 칸(B2) 글. 빈 글이면 기준 표의 글(○○과장/담당관 …)을 그대로 둔다.
# 설정창 '제목 표 담당자 칸(B2) 글'(title_owner_text)로 바꾼다(2026-10-03 사용자 요청).
제목_담당자_글 = ''


제목_담당자_글_반영 = _engine_resolve('docfit_engine.formatter', '제목_담당자_글_반영', globals())


_설정_담당자_글인가 = _engine_resolve('docfit_engine.formatter', '_설정_담당자_글인가', globals())


_서식표_기준 = _engine_resolve('docfit_engine.formatter', '_서식표_기준', globals())


제목_부제_크기 = _engine_resolve('docfit_engine.formatter', '제목_부제_크기', globals())


_칸_글_지우기 = _engine_resolve('docfit_engine.formatter', '_칸_글_지우기', globals())


_칸_날짜_현행화 = _engine_resolve('docfit_engine.formatter', '_칸_날짜_현행화', globals())


_빈칸_서식_참조_변환 = _engine_resolve('docfit_engine.formatter', '_빈칸_서식_참조_변환', globals())


_칸_글_넣기 = _engine_resolve('docfit_engine.formatter', '_칸_글_넣기', globals())


서식표_생성 = _engine_resolve('docfit_engine.formatter', '서식표_생성', globals())


_제목개요_빈줄_정리 = _engine_resolve('docfit_engine.formatter', '_제목개요_빈줄_정리', globals())


_서식표_글 = _engine_resolve('docfit_engine.formatter', '_서식표_글', globals())


_서식표_글_확인 = _engine_resolve('docfit_engine.formatter', '_서식표_글_확인', globals())


라벨_서식표_적용 = _engine_resolve('docfit_engine.formatter', '라벨_서식표_적용', globals())


_문서_표번호 = _engine_resolve('docfit_engine.formatter', '_문서_표번호', globals())


_서식표_번호_부여 = _engine_resolve('docfit_engine.formatter', '_서식표_번호_부여', globals())


_hwpx_안전_저장 = _engine_resolve('docfit_engine.formatter', '_hwpx_안전_저장', globals())


# 준말(약어) 등록표. 작업_실행이 설정에서 채우며, 한 번에 적용 때 줄 첫 어절의 준말을 본말로 바꾼다.
준말_등록표 = {}


# 글 위치를 차지하지 않는 구역·쪽 설정 컨트롤(단 설정·쪽 번호·감추기·머리말 등). 문서 첫 문단에 흔히 함께 있다.
_문단_설정컨트롤 = frozenset({'colPr', 'secPr', 'pageNum', 'pageNumCtrl', 'pageHiding', 'newNum', 'header', 'footer'})


_문단_일반글 = _engine_resolve('docfit_engine.formatter', '_문단_일반글', globals())


_문단_준말_판별 = _engine_resolve('docfit_engine.formatter', '_문단_준말_판별', globals())


# 준말 줄을 건너뛴 이유로 알려 줄 요소 이름(없는 이름은 XML 이름 그대로 보여 준다).
_준말_제외요소_이름 = {'tbl': '표', 'pic': '그림', 'ole': 'OLE 개체', 'rect': '글상자', 'equation': '수식',
                     'fieldBegin': '필드(누름틀·하이퍼링크 등)', 'fieldEnd': '필드 끝', 'bookmark': '책갈피',
                     'footNote': '각주', 'endNote': '미주', 'autoNum': '자동 번호', 'tab': '탭',
                     'fwSpace': '고정폭 빈칸', 'nbSpace': '묶음 빈칸', 'lineBreak': '강제 줄바꿈'}


_문단_준말_제외사유 = _engine_resolve('docfit_engine.formatter', '_문단_준말_제외사유', globals())


_문단_글_바꾸기 = _engine_resolve('docfit_engine.formatter', '_문단_글_바꾸기', globals())


준말_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '준말_hwpx_처리', globals())


제목개요폭_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '제목개요폭_hwpx_처리', globals())


알파_연결부호_탭정렬_사용 = True


연결부호탭_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '연결부호탭_hwpx_처리', globals())


알파_콜론라벨_정렬_사용 = True


# 알파 1-a(2026-10-11): '한 번에 적용'의 자간 초기화를 XML 선행 단계에서 한다(한/글 방식 15.8초 → 1초 미만 목표).
# 끄면 한/글로 문단마다 선택해 0%로 바꾸는 예전 방식이다. 자간 정리 모드·쪽 범위 작업은 언제나 예전 방식.
알파_자간초기화_XML_사용 = True


자간초기화_hwpx_처리 = _engine_resolve('docfit_engine.spacing', '자간초기화_hwpx_처리', globals())


콜론라벨_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '콜론라벨_hwpx_처리', globals())


상자서식_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '상자서식_hwpx_처리', globals())


쪽번호_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '쪽번호_hwpx_처리', globals())


준말_사용표_만들기 = _engine_resolve('docfit_engine.formatter', '준말_사용표_만들기', globals())


준말_선행적용 = _engine_resolve('docfit_engine.formatter', '준말_선행적용', globals())


# 기본 표 서식을 입혔으면(준말 '표') COM 표 머리글·본문 서식 단계가 그 서식을 덮지 않게 건너뛴다.
기본표서식_적용됨 = False


기본표서식 = _engine_resolve('docfit_engine.formatter', '기본표서식', globals())


_기본표서식_대상인가 = _engine_resolve('docfit_engine.formatter', '_기본표서식_대상인가', globals())


기본표서식_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '기본표서식_hwpx_처리', globals())


표너비_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '표너비_hwpx_처리', globals())


기본표서식_선행적용 = _engine_resolve('docfit_engine.formatter', '기본표서식_선행적용', globals())


_위첨자_글자모양 = _engine_resolve('docfit_engine.formatter', '_위첨자_글자모양', globals())


_문단_별표_대상 = _engine_resolve('docfit_engine.formatter', '_문단_별표_대상', globals())


별표위첨자_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '별표위첨자_hwpx_처리', globals())


별표위첨자_선행적용 = _engine_resolve('docfit_engine.formatter', '별표위첨자_선행적용', globals())


_한글_글꼴표 = _engine_resolve('docfit_engine.formatter', '_한글_글꼴표', globals())


_글꼴_확보 = _engine_resolve('docfit_engine.formatter', '_글꼴_확보', globals())


_글자모양_글꼴크기 = _engine_resolve('docfit_engine.formatter', '_글자모양_글꼴크기', globals())


_본문기호_글꼴 = _engine_resolve('docfit_engine.formatter', '_본문기호_글꼴', globals())


붙임글꼴_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '붙임글꼴_hwpx_처리', globals())


글자서식_선행적용 = _engine_resolve('docfit_engine.formatter', '글자서식_선행적용', globals())


붙임2종_현재문서_조사 = _engine_resolve('docfit_engine.formatter', '붙임2종_현재문서_조사', globals())


제목붙임_선행적용 = _engine_resolve('docfit_engine.formatter', '제목붙임_선행적용', globals())


정밀표_선행적용 = _engine_resolve('docfit_engine.formatter', '정밀표_선행적용', globals())


붙임2종_현재문서_적용 = _engine_resolve('docfit_engine.formatter', '붙임2종_현재문서_적용', globals())

설정_폴더 = _engine_resolve('docfit_engine.formatter', '설정_폴더', globals())

서식프로파일_폴더 = _engine_resolve('docfit_engine.formatter', '서식프로파일_폴더', globals())

서식예시_정보_폴더 = _engine_resolve('docfit_engine.formatter', '서식예시_정보_폴더', globals())

서식예시_폴더 = _engine_resolve('docfit_engine.formatter', '서식예시_폴더', globals())

첫쪽_그림_만들기 = _engine_resolve('docfit_engine.formatter', '첫쪽_그림_만들기', globals())


번들_서식예시_찾기 = _engine_resolve('docfit_engine.formatter', '번들_서식예시_찾기', globals())

_json_파일_읽기 = _engine_resolve('docfit_engine.formatter', '_json_파일_읽기', globals())

기본서식_덮어쓰기_식별자 = "_standard"   # 기본 서식 예시를 사용자가 고쳐 바뀐 기본 서식(formats/_standard.json)

# 서식 예시는 '한 번에 적용'(서식 + 자간 정리)으로 만든다(2026-10-04 사용자 요청: 예시 파일 자간 정리 미흡).
서식예시_작업모드 = "all"

서식예시_서명 = _engine_resolve('docfit_engine.formatter', '서식예시_서명', globals())

설정_파일_경로 = _engine_resolve('docfit_engine.formatter', '설정_파일_경로', globals())

창_맨앞으로 = _engine_resolve('docfit_ui.legacy', '창_맨앞으로', globals())


설정_불러오기 = _engine_resolve('docfit_engine.formatter', '설정_불러오기', globals())

설정_저장 = _engine_resolve('docfit_engine.formatter', '설정_저장', globals())

# ============================================================
# GUI 메시지
# ============================================================

로그 = _engine_resolve('docfit_engine.pipeline', '로그', globals())

진단로그 = _engine_resolve('docfit_engine.pipeline', '진단로그', globals())

상태 = _engine_resolve('docfit_engine.pipeline', '상태', globals())

진행률 = _engine_resolve('docfit_engine.formatter', '진행률', globals())

# 진행 단계 다이어그램: 파이프라인의 세부 단계명을 6개 상위 절차로 묶어
# 화면 상단 다이어그램의 어느 칸을 켤지 결정한다.
진행단계_순서 = ["열기", "서식", "자간", "줄 병합", "페이지 배치", "저장"]
_세부단계_단계매핑 = {
    "공백 정규화": "서식",
    "문장부호 뒤 공백 보정": "서식",
    "보고서 표준서식": "서식",
    "최종 서식 기준 내어쓰기": "서식",
    "문두 라벨/괄호 서식": "서식",
    "부연설명 들여쓰기": "서식",
    "별표(**) 정렬": "서식",
    "자간 조정 후 별표(**) 정렬": "자간",
    "표 서식": "서식",
    "개요·한 칸 표 자간 조정": "자간",
    "제목·개요·붙임 선행 서식": "서식",
    "기본 표 서식": "서식",
    "표 칸 너비": "서식",
    "자간 조정": "자간",
    "표/컨트롤 자간 조정": "자간",
    "단어 분리 최종 검사": "자간",
    "표/컨트롤 단어 검사": "자간",
    "짧은 마지막 줄 병합": "줄 병합",
    "표/컨트롤 줄 병합": "줄 병합",
    "관련 문단 페이지 배치": "페이지 배치",
}

# 문서 처리 단계별 소요 시간 계측(알파 계획 W7-0, 2026-10-09). 동작은 바꾸지 않는다.
# 단계가 바뀔 때마다(단계표시) 직전 구간의 시간을 이름별로 모아, 문서 하나가 끝나면 로그에 요약한다.
# 실측: 전체 317.5초 중 쪽 수 맞춤은 약 67초뿐이고 나머지 약 250초가 어느 단계인지 몰랐다.
_단계시간표 = None


단계시간_시작 = _engine_resolve('docfit_engine.formatter', '단계시간_시작', globals())


_단계시간_닫기 = _engine_resolve('docfit_engine.formatter', '_단계시간_닫기', globals())


단계시간_구간 = _engine_resolve('docfit_engine.formatter', '단계시간_구간', globals())


단계시간_끝 = _engine_resolve('docfit_engine.formatter', '단계시간_끝', globals())


단계시간_분류 = _engine_resolve('docfit_engine.formatter', '단계시간_분류', globals())


단계시간_요약줄 = _engine_resolve('docfit_engine.formatter', '단계시간_요약줄', globals())


단계표시 = _engine_resolve('docfit_engine.pipeline', '단계표시', globals())

단계초기화 = _engine_resolve('docfit_engine.formatter', '단계초기화', globals())

중단_요청됨 = _engine_resolve('docfit_engine.formatter', '중단_요청됨', globals())


class 문두보호_조정불가(RuntimeError):
    """화면줄에 항목기호·라벨만 있어 자간·장평을 줄일 본문이 없다. 그 줄만 건너뛴다.

    예전에는 일반 RuntimeError라 줄 단위 자간 함수가 잡지 않아 문서 전체가 실패했다
    (2026-10-04 범정부오피스 인천 업무보고 서식에서 한 번에 적용이 10분 뒤 실패).
    """


# 문서 편집 세대: 글을 바꿀 수 있는 명령을 시도할 때마다(성공 여부와 관계없이) 올린다. 문단 글 캐시는 읽은 뒤
# 세대가 바뀌었으면 쓰지 않는다(Beta 12 리뷰 R2: 지운 뒤 넣기만 실패하면 글은 바뀌었는데 수정 건수가 0이라
# 캐시가 옛 글을 다음 규칙에 넘겼다).
_문서_편집_세대 = 0


_문서_편집_시도 = _engine_resolve('docfit_engine.formatter', '_문서_편집_시도', globals())


hwp_run = _engine_resolve('docfit_engine.formatter', 'hwp_run', globals())


_문두보호_줄건너뜀 = _engine_resolve('docfit_engine.formatter', '_문두보호_줄건너뜀', globals())

# ============================================================
# 보안 모듈
# ============================================================

원본_DLL_찾기 = _engine_resolve('docfit_engine.security', '원본_DLL_찾기', globals())

등록된_DLL_경로 = _engine_resolve('docfit_engine.security', '등록된_DLL_경로', globals())

레지스트리_등록 = _engine_resolve('docfit_engine.security', '레지스트리_등록', globals())

보안모듈_초기화 = _engine_resolve('docfit_engine.security', '보안모듈_초기화', globals())


이전_보안모듈_정리 = _engine_resolve('docfit_engine.security', '이전_보안모듈_정리', globals())

# ============================================================
# 상용구 파일저장 (HWP.IDO)
# ============================================================

# 상용구(자주 쓰는 텍스트·서식)는 한/글이 기본 데이터 폴더의
# \User\Hwp\버전폴더 아래에 HWP.IDO 파일로 저장한다(예: 한/글 2020 = 60).
상용구_파일명 = "HWP.IDO"


번들_상용구_파일_찾기 = _engine_resolve('docfit_engine.formatter', '번들_상용구_파일_찾기', globals())


글자상용구_폴더 = _engine_resolve('docfit_engine.formatter', '글자상용구_폴더', globals())


본문상용구_폴더 = _engine_resolve('docfit_engine.formatter', '본문상용구_폴더', globals())


번들_본문상용구_폴더 = _engine_resolve('docfit_engine.formatter', '번들_본문상용구_폴더', globals())


상용구_폴더_준비 = _engine_resolve('docfit_engine.formatter', '상용구_폴더_준비', globals())


상용구_전용폴더_찾기 = _engine_resolve('docfit_engine.formatter', '상용구_전용폴더_찾기', globals())


# ============================================================
# 한글 시작
# ============================================================

한글_시작 = _engine_resolve('docfit_engine.com_driver', '한글_시작', globals())

현재선택영역_글자수 = _engine_resolve('docfit_engine.com_driver', '현재선택영역_글자수', globals())

현재선택영역_텍스트 = _engine_resolve('docfit_engine.com_driver', '현재선택영역_텍스트', globals())

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

색상_미리보기_hex = _engine_resolve('docfit_engine.com_driver', '색상_미리보기_hex', globals())

# 자간을 줄이거나 넓힌 구간은 모두 색상_적용_현재선택으로 표시한다.
# 이 호출 횟수로 한 차례 자간 조정에서 실제 변경이 있었는지 판단해,
# 변경이 있으면 내어쓰기를 다시 적용하고 자간을 재검사한다.
자간_변경_횟수 = 0
# 자간을 바꾼 문단의 (리스트, 문단) 번호. 자간 조정 뒤에는 이 문단들만
# 내어쓰기를 다시 계산한다(내어쓰기 값은 그 문단 첫 줄에만 달려 있다).
자간_변경문단 = set()


색상_적용_현재선택 = _engine_resolve('docfit_engine.com_driver', '색상_적용_현재선택', globals())

# ============================================================
# 비교 보기 (창 임베드)
# ============================================================

_표시중인_최상위창_목록 = _engine_resolve('docfit_engine.com_driver', '_표시중인_최상위창_목록', globals())

새_한글창_찾기 = _engine_resolve('docfit_engine.com_driver', '새_한글창_찾기', globals())

창_임베드 = _engine_resolve('docfit_engine.com_driver', '창_임베드', globals())

창_임베드_크기조정 = _engine_resolve('docfit_engine.com_driver', '창_임베드_크기조정', globals())

창_임베드_해제 = _engine_resolve('docfit_engine.com_driver', '창_임베드_해제', globals())

원본_뷰어_시작 = _engine_resolve('docfit_engine.com_driver', '원본_뷰어_시작', globals())

작업창_임베드 = _engine_resolve('docfit_engine.com_driver', '작업창_임베드', globals())

비교보기_임베드_재확인 = _engine_resolve('docfit_engine.com_driver', '비교보기_임베드_재확인', globals())

원본_뷰어_문서표시 = _engine_resolve('docfit_engine.com_driver', '원본_뷰어_문서표시', globals())

원본_뷰어_분리 = _engine_resolve('docfit_engine.com_driver', '원본_뷰어_분리', globals())

작업창_분리 = _engine_resolve('docfit_engine.com_driver', '작업창_분리', globals())

원본_뷰어_닫기 = _engine_resolve('docfit_engine.com_driver', '원본_뷰어_닫기', globals())

작업창_닫기 = _engine_resolve('docfit_engine.com_driver', '작업창_닫기', globals())

# ============================================================
# 서식 조작 함수들
# ============================================================

텍스트_삽입 = _engine_resolve('docfit_engine.formatter', '텍스트_삽입', globals())

문자모양_적용_현재선택 = _engine_resolve('docfit_engine.formatter', '문자모양_적용_현재선택', globals())


_언어별_글꼴형식 = ("FontTypeHangul", "FontTypeLatin", "FontTypeHanja", "FontTypeJapanese", "FontTypeOther",
                "FontTypeSymbol", "FontTypeUser")


_다른_글꼴형식으로_재실행 = _engine_resolve('docfit_engine.formatter', '_다른_글꼴형식으로_재실행', globals())

문단_줄간격_적용_현재선택 = _engine_resolve('docfit_engine.formatter', '문단_줄간격_적용_현재선택', globals())

HwpUnit_pt = _engine_resolve('docfit_engine.formatter', 'HwpUnit_pt', globals())


HwpUnit_mm = _engine_resolve('docfit_engine.formatter', 'HwpUnit_mm', globals())


문단_위간격_적용_현재선택 = _engine_resolve('docfit_engine.formatter', '문단_위간격_적용_현재선택', globals())

문단_아래간격_pt_현재문단 = _engine_resolve('docfit_engine.formatter', '문단_아래간격_pt_현재문단', globals())

문단_아래간격_적용_현재선택 = _engine_resolve('docfit_engine.formatter', '문단_아래간격_적용_현재선택', globals())

텍스트_너비_em = _engine_resolve('docfit_engine.formatter', '텍스트_너비_em', globals())

_문단_공백_건너뛰기 = _engine_resolve('docfit_engine.formatter', '_문단_공백_건너뛰기', globals())


# 본문이 낫표(「」, 『』)로 시작하면 여는 낫표가 아니라 그 바로 다음
# 글자를 내어쓰기 기준으로 삼는다.
# 예: 'ㅇ (개요)「공유재산법 시행령」…' → 기준은 '「'이 아니라 '공'.
_내어쓰기_건너뛸_여는낫표 = "「『"


복사_내어쓰기_규칙 = _engine_resolve('docfit_engine.formatter', '복사_내어쓰기_규칙', globals())


문단_내어쓰기_기준_오프셋 = _engine_resolve('docfit_engine.formatter', '문단_내어쓰기_기준_오프셋', globals())


_여는낫표_건너뛰기 = _engine_resolve('docfit_engine.formatter', '_여는낫표_건너뛰기', globals())


_문단_기호뒤_오프셋 = _engine_resolve('docfit_engine.formatter', '_문단_기호뒤_오프셋', globals())


_문단_본문시작_오프셋 = _engine_resolve('docfit_engine.formatter', '_문단_본문시작_오프셋', globals())


문단_자간보호_선행부_오프셋 = _engine_resolve('docfit_engine.spacing', '문단_자간보호_선행부_오프셋', globals())


문단_내어쓰기_적용_현재선택 = _engine_resolve('docfit_engine.formatter', '문단_내어쓰기_적용_현재선택', globals())


# ASCII 괄호·대괄호 등 '좁은 문장부호'는 함초롬/한컴 계열 글꼴에서 약 0.42em
# 폭으로 렌더된다(반각 0.5em보다 좁음). 선행부 폭 추정 오차의 주원인이므로
# 별도 보정한다. 필요 시 이 값만 미세조정하면 된다.
_좁은문장부호_폭배수 = 0.42
_좁은문장부호 = set("()[]{}<>")

# 폭 추정 도우미는 부연설명 배치 기능에서만 사용한다.
# 문단 내어쓰기는 정렬을 변경하지 않고 실제 Shift+Tab으로 처리한다.

_반각전각_폭배수 = _engine_resolve('docfit_engine.formatter', '_반각전각_폭배수', globals())

문단_선행부_폭_HWPUNIT = _engine_resolve('docfit_engine.formatter', '문단_선행부_폭_HWPUNIT', globals())

_내어쓰기_값_설정 = _engine_resolve('docfit_engine.formatter', '_내어쓰기_값_설정', globals())
_내어쓰기_여백쌍_설정 = _engine_resolve('docfit_engine.formatter', '_내어쓰기_여백쌍_설정', globals())



# 문서 처리 중 '최종 서식 기준 내어쓰기' 단계가 뒤에 예정돼 있으면
# 표준서식 단계에서는 내어쓰기를 계산하지 않는다(어차피 다시 계산된다).
최종_내어쓰기_예정 = False


내어쓰기_기호선택_허용 = _engine_resolve('docfit_engine.formatter', '내어쓰기_기호선택_허용', globals())


재검사_대상인가 = _engine_resolve('docfit_engine.formatter', '재검사_대상인가', globals())


재검사_영역인가 = _engine_resolve('docfit_engine.formatter', '재검사_영역인가', globals())


문단_내어쓰기_전체_갱신 = _engine_resolve('docfit_engine.formatter', '문단_내어쓰기_전체_갱신', globals())


_내어쓰기_한문단 = _engine_resolve('docfit_engine.formatter', '_내어쓰기_한문단', globals())


_붙임목록_내어쓰기_대상수집 = _engine_resolve('docfit_engine.formatter', '_붙임목록_내어쓰기_대상수집', globals())


_붙임번호_기준위치_실측 = _engine_resolve('docfit_engine.formatter', '_붙임번호_기준위치_실측', globals())


_붙임목록_번호_내어쓰기_적용 = _engine_resolve('docfit_engine.formatter', '_붙임목록_번호_내어쓰기_적용', globals())



문단_내어쓰기_적용 = _engine_resolve('docfit_engine.formatter', '문단_내어쓰기_적용', globals())

# ============================================================
# 부연설명(*, **, ※) 들여쓰기
# ============================================================
#
# 규칙(사용자 정의):
#  - □/ㅁ = 제목, ㅇ/○ = 본문, - = 내용.
#  - *, **, ※ 로 시작하는 문단 = '부연설명'으로, 바로 위의 제목/본문/내용에
#    연결된다.
#  - 부연설명의 들여쓰기 기준값 = 바로 위 제목/본문/내용의 '본문 첫 글자'
#    가로 위치. 즉 위 문단에 문두 라벨(괄호/콜론)이 있으면 그 라벨 뒤 첫
#    글자 위치, 없으면 첫 공백 뒤 첫 글자 위치.
#
# 구현(1.68 Alpha 6, TODO.md 1순위): 폭을 글자 크기로 '계산'하지 않고 한/글에
# '실측'시킨다. 본문 내어쓰기와 같은 원리로, 캐럿을 본문 첫 글자에 두고 실제
# Shift+Tab(ParagraphShapeIndentAtCaret)을 실행해 한/글이 정한 값을 읽는다.
# 실측(2026-09-25, 통합테스트 문서): 예전 계산 폭은 한/글 실측값의 절반
# 수준이었다(예: '  - ' 계산 2800 / 실측 5600). 양쪽정렬로 늘어난 공백까지
# 한/글이 반영하므로 정렬과 무관하게 맞는다.
#  - 위 문단 본문 첫 글자 위치 = 위 문단 왼쪽여백 + 실측 폭
#  - 부연설명 왼쪽여백 = 그 위치 − 부연설명 자신의 선행 공백 실측 폭
#    → 선행 공백 뒤 마커(*, ※)가 위 문단 본문 첫 글자와 같은 칸에서 시작한다.
#  - 부연설명 자신의 첫 줄 값(내어쓰기)은 건드리지 않는다(자기 본문에 맞춘
#    내어쓰기를 그대로 두고 문단 전체만 옮긴다).
부연설명_들여쓰기_사용 = True

_제목_기호 = set("□ㅁ■")
_본문_기호 = set("ㅇ○●◦")
_내용_기호 = set("-–—‒−―")

_부모문단_유형 = _engine_resolve('docfit_engine.formatter', '_부모문단_유형', globals())

_부연설명_문단인가 = _engine_resolve('docfit_engine.formatter', '_부연설명_문단인가', globals())

_선행공백_길이 = _engine_resolve('docfit_engine.formatter', '_선행공백_길이', globals())


_캐럿위치_폭_실측 = _engine_resolve('docfit_engine.formatter', '_캐럿위치_폭_실측', globals())


# 부연설명 앞 빈칸 수(문단 왼쪽 끝에서 센 칸 수, 사용자 지정 2026-10-07).
# 기준 문서 '1) 보고서(계획서) 서식.hwpx': □ 아래 ※ 4·* 5·** 4칸, ㅇ·- 아래 ※ 5·* 6·** 5칸,
# 번호 항목 아래 등 위에 제목/본문/내용이 없으면 ※ 3·* 4·** 3칸.
# ※와 **는 같은 칸에서 시작하고 *는 한 칸 더 띄워 **의 둘째 별표가 *와 세로로 맞는다.
부연설명_앞빈칸 = {
    "제목": {"※": 4, "*": 5, "**": 4},
    "본문": {"※": 5, "*": 6, "**": 5},
    "내용": {"※": 5, "*": 6, "**": 5},
    None: {"※": 3, "*": 4, "**": 3},
}


부연설명_앞빈칸_수 = _engine_resolve('docfit_engine.formatter', '부연설명_앞빈칸_수', globals())


_부연설명_앞빈칸_적용 = _engine_resolve('docfit_engine.formatter', '_부연설명_앞빈칸_적용', globals())


_부연설명_한문단 = _engine_resolve('docfit_engine.formatter', '_부연설명_한문단', globals())


부연설명_들여쓰기_전체_적용 = _engine_resolve('docfit_engine.formatter', '부연설명_들여쓰기_전체_적용', globals())


_별표_위치_실측 = _engine_resolve('docfit_engine.formatter', '_별표_위치_실측', globals())


_별표_정렬_적용 = _engine_resolve('docfit_engine.formatter', '_별표_정렬_적용', globals())


_별표_한문단 = _engine_resolve('docfit_engine.formatter', '_별표_한문단', globals())


별표_정렬_전체_적용 = _engine_resolve('docfit_engine.formatter', '별표_정렬_전체_적용', globals())

_mm_hwpunit = _engine_resolve('docfit_engine.formatter', '_mm_hwpunit', globals())


_현재_쪽여백 = _engine_resolve('docfit_engine.formatter', '_현재_쪽여백', globals())


_표준_또는_원본여백 = _engine_resolve('docfit_engine.formatter', '_표준_또는_원본여백', globals())


페이지_여백_설정 = _engine_resolve('docfit_engine.formatter', '페이지_여백_설정', globals())

용지_다르면_알림 = _engine_resolve('docfit_engine.formatter', '용지_다르면_알림', globals())


들여쓰기_공백_맞추기 = _engine_resolve('docfit_engine.formatter', '들여쓰기_공백_맞추기', globals())

표준서식_기호_별칭 = {
    # ☞로 시작하는 문장은 ㅇ와 동일한 폰트·크기·굵기·문단위간격 규칙을 적용한다.
    "☞": "ㅇ",
    # 공식 규정상 'ㅇ'은 한글 자소 '이응'(U+3147)을 써야 하지만, 문자표에서
    # 비슷하게 생긴 원문자 '○'(WHITE CIRCLE)를 잘못 입력하는 사례가 실제로
    # 있었다(공문서_기호·문단위간격_찾기에서도 이미 같은 기호로 취급 중).
    # 오타로 들어간 경우에도 서식이 깨지지 않도록 별칭으로 남겨 둔다.
    "○": "ㅇ",
    # 네모(ㅁ)는 □와 같은 항목기호로 취급한다.
    "ㅁ": "□",
    # **(주석2)는 *(주석1)와 같은 대표 기호로 묶는다(별표 하나짜리 규칙을 그대로 씀).
    "**": "*",
    **{marker: "•" for marker in DOT_MARKERS if marker != "•"},
}
# 주의: '-'는 규정상 키보드 마이너스(U+002D, HYPHEN-MINUS)만 사용하도록
# 되어 있다. en dash/em dash 등 다른 대시 문자는 별칭으로 묶지 않는다 —
# 그런 문자가 문단 맨 앞에 오는 경우는 대부분 '-' 항목 기호가 아니라
# 다른 용도(날짜 범위, 인용 출처 표기 등)이므로 자동으로 같이 묶으면
# 오탐(과잉 서식적용) 위험이 더 크다.

표준서식_기호규칙_찾기 = _engine_resolve('docfit_engine.formatter', '표준서식_기호규칙_찾기', globals())


_정렬_이름 = {값: 이름 for 이름, 값 in _정렬_COM.items()}


본문형_일반문장인가 = _engine_resolve('docfit_engine.formatter', '본문형_일반문장인가', globals())


# 알파는 기본 보고서 서식을 XML에서 먼저 입힌다. 내어쓰기·쪽 배치는 실측한다.
# 사용자 서식의 복사 속성은 아직 기존 경로로 처리해 미지원 속성을 잃지 않는다.
알파_HWPX_일괄서식_사용 = True
_표준서식_XML텍스트 = set()
_표준서식_XML간격 = {}
_알파_일괄서식_문서 = False


# 알파 1-d(2026-10-11): 사용자 서식(예시 보고서 복사)도 항목기호 문단은 XML에서 입힌다(복사한 문단 모양·계층 추가 서식).
# 항목기호 없는 문단(제목·날짜·본문·세트 후속)과 내어쓰기·간격 규칙은 한/글 경로. 끄면 사용자 서식은 전부 한/글 경로.
알파_사용자서식_XML_사용 = True
_사용자서식_키 = ('복사_문단모양', '계층_추가서식', '복제_본문서식', '복제_들여쓰기_유지', '복귀_간격', '제목뒤_간격')


_사용자서식인가 = _engine_resolve('docfit_engine.formatter', '_사용자서식인가', globals())


알파_일괄서식_가능 = _engine_resolve('docfit_engine.formatter', '알파_일괄서식_가능', globals())


_줄간격_종류_HWPX = {0: "PERCENT", 1: "FIXED", 2: "BETWEEN_LINES", 3: "AT_LEAST"}
_문단여백_HWPX = {"LeftMargin": "left", "RightMargin": "right", "Indentation": "intent",
                 "PrevSpacing": "prev", "NextSpacing": "next"}


사용자서식_XML추가값 = _engine_resolve('docfit_engine.formatter', '사용자서식_XML추가값', globals())


_GDI_글꼴 = None


_GDI_글꼴인가 = _engine_resolve('docfit_engine.formatter', '_GDI_글꼴인가', globals())


_알파_글꼴형식 = _engine_resolve('docfit_engine.formatter', '_알파_글꼴형식', globals())


_알파_라벨_굵게범위 = _engine_resolve('docfit_engine.formatter', '_알파_라벨_굵게범위', globals())


표준서식_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '표준서식_hwpx_처리', globals())


_알파_한줄문단인가 = _engine_resolve('docfit_engine.formatter', '_알파_한줄문단인가', globals())


표준서식_문단_처리 = _engine_resolve('docfit_engine.formatter', '표준서식_문단_처리', globals())

# 문서 작성자가 문단 위 여백 대신 빈 줄로 띄운 간격은 표준서식의 문단 위
# 여백과 겹치므로 지운다. 앞뒤가 모두 항목기호 문장인 빈 문단만 대상이다.
# 설정 > 서식 정리 > 보고서 표준서식에서 켜고 끈다.
항목기호문장_빈줄_삭제_사용 = True


빈문단_분류 = _engine_resolve('docfit_engine.formatter', '빈문단_분류', globals())


항목기호문장_사이_빈문단_찾기 = _engine_resolve('docfit_engine.formatter', '항목기호문장_사이_빈문단_찾기', globals())


본문_컨트롤_문단번호 = _engine_resolve('docfit_engine.formatter', '본문_컨트롤_문단번호', globals())


항목기호문장_사이_빈줄_삭제 = _engine_resolve('docfit_engine.formatter', '항목기호문장_사이_빈줄_삭제', globals())


# ============================================================
# 여러 사람이 쓴 문서를 합쳐 만든 문서 안에서, 항목기호(□·ㅇ·-·*·※ 등)별로
# 문단 전체의 글꼴·크기·문단 앞 여백을 모아 대표값을 정하고, 대표와 다른 구간만
# 맞춘 뒤 해당 문단에 내어쓰기를 적용한다. 고정된 기준 서식을 적용하는 '서식 정리'와
# 달리 기준은 '이 문서 자신'이며, 자간은 초기화하거나 대표값으로 통일하지 않는다.
#  - 제목·날짜처럼 일부러 다르게 쓰는 일반 문단과 표·글상자는 대상이 아니다.
#  - 문단별 기본 글꼴/크기는 항목기호와 라벨을 포함한 문단 전체 글자 사용량의
#    최빈 문자모양으로 판정한다. 첫 글자와 가운데 글자만 비교하면 중간 혼합서식을
#    놓치거나 한컴 charPr ID 하나가 여러 속성의 문자를 함께 포함한 표본을 잘못 버릴 수 있다.
#  - 보고서 항목기호 문단을 항목기호별로 묶고, 다수 대표가 뚜렷한 경우만 교정한다.
#  - 문장 안의 굵게/색상/기울임 등 강조서식은 보존하고 글꼴/크기만 불일치 구간에 적용한다.
서식통일_최소문단수 = 3
서식통일_최소비율 = 0.6
_서식통일_문서대표프로필 = {}
# 표준 서식이 서식통일 뒤에 기준을 정하는 작업이면 미확정 문단을 빨간색으로 표시하지 않는다.
서식통일_빨간표시_사용 = True
# 괄호(문두 라벨 제외)가 본문보다 얼마나 작은지(1/100pt)의 문서 관행. None이면 설정값(-2pt).
서식통일_괄호크기차이 = None
# 표준 서식이 뒤따르면 서식통일이 고친 문장의 자간을 표준 서식 뒤에 다시 조정한다.
# 문단 위치는 빈 줄 삭제 등으로 바뀔 수 있어 문단 텍스트로 다시 찾는다.
_서식통일_자간보류문단 = {}
_서식통일_최종감사 = None
_서식통일_대표값_검토콜백 = None
# 원본 HWPX 분석 결과(경로·수정 시각·크기가 같을 때 재사용)와 마무리 단계용 위치 기준 텍스트.
_서식통일_HWPX_캐시 = {}
_서식통일_위치텍스트_보관 = {}
# 마무리 단계용 고친 문장의 계획 위치(문단 글 → 시작 위치). 서식 적용은 문단 수를 바꾸지 않으므로
# 마무리에서 이 위치로 바로 가 글을 대조하고, 맞지 않는 문장만 예전처럼 문서를 순회해 찾는다.
_서식통일_보류위치 = {}
# 문서 헤더에서 읽은 글꼴 이름별 형식(TTF/HFT). 한/글 내장 HFT 글꼴(한양중고딕 등)을
# TTF로 지정하면 한/글이 오류 없이 무시한다(실측: 정책회의 ※ 문장 8개 글꼴 미반영).
_글꼴형식 = {}


글꼴형식_모으기 = _engine_resolve('docfit_engine.formatter', '글꼴형식_모으기', globals())


글꼴형식_등록 = _engine_resolve('docfit_engine.formatter', '글꼴형식_등록', globals())


_서식통일_문두요소_범위 = _engine_resolve('docfit_engine.formatter', '_서식통일_문두요소_범위', globals())


_서식통일_글자모양 = _engine_resolve('docfit_engine.formatter', '_서식통일_글자모양', globals())


_서식통일_공백제거 = _engine_resolve('docfit_engine.formatter', '_서식통일_공백제거', globals())


_서식통일_HWPX_분석 = _engine_resolve('docfit_engine.formatter', '_서식통일_HWPX_분석', globals())


# 한/글 글자 위치에서 한 칸을 차지하는 문장 안 요소. 강제 줄바꿈도 한 칸이다
# (실측: 줄바꿈 뒤 괄호 구간이 한 글자씩 밀려 적용됨). 줄바꿈은 공백으로 취급되는
# U+2028로 두어 문장 끝 개행 제거·공백 비교에 영향을 주지 않는다.
_서식통일_글자요소 = {"fwSpace": " ", "nbSpace": " ", "tab": " ", "lineBreak": " "}


_서식통일_run_text = _engine_resolve('docfit_engine.formatter', '_서식통일_run_text', globals())


_서식통일_XML문단 = _engine_resolve('docfit_engine.formatter', '_서식통일_XML문단', globals())


_서식통일_위치텍스트 = _engine_resolve('docfit_engine.formatter', '_서식통일_위치텍스트', globals())


_서식통일_음영값 = _engine_resolve('docfit_engine.formatter', '_서식통일_음영값', globals())


서식통일_표본 = _engine_resolve('docfit_engine.formatter', '서식통일_표본', globals())


_서식통일_그룹키 = _engine_resolve('docfit_engine.formatter', '_서식통일_그룹키', globals())


_서식통일_현재_HWPX = _engine_resolve('docfit_engine.formatter', '_서식통일_현재_HWPX', globals())


_서식통일_불일치_구간 = _engine_resolve('docfit_engine.formatter', '_서식통일_불일치_구간', globals())


_서식통일_부연괄호_불일치_구간 = _engine_resolve('docfit_engine.formatter', '_서식통일_부연괄호_불일치_구간', globals())


_서식통일_굵기_불일치_구간 = _engine_resolve('docfit_engine.formatter', '_서식통일_굵기_불일치_구간', globals())


서식통일_대표 = _engine_resolve('docfit_engine.formatter', '서식통일_대표', globals())


_서식통일_표지인가 = _engine_resolve('docfit_engine.formatter', '_서식통일_표지인가', globals())


_서식통일_제목표_표본 = _engine_resolve('docfit_engine.formatter', '_서식통일_제목표_표본', globals())


_서식통일_체계경계 = _engine_resolve('docfit_engine.formatter', '_서식통일_체계경계', globals())


_서식통일_참고표_이웃대표_보완 = _engine_resolve('docfit_engine.formatter', '_서식통일_참고표_이웃대표_보완', globals())


_서식통일_대표값_사용자검토 = _engine_resolve('docfit_engine.formatter', '_서식통일_대표값_사용자검토', globals())


_서식통일_적용영역_사용자검토 = _engine_resolve('docfit_engine.formatter', '_서식통일_적용영역_사용자검토', globals())


# 서식통일 뒤 '작업 결과 확인' 창을 띄울지(설정 unify_result_window, 기본 꺼짐). 꺼져 있으면 결과는 처리 기록과
# 최종 검수 보고서에만 남긴다.
서식통일_결과창_사용 = False


서식통일_결과창_반영 = _engine_resolve('docfit_engine.formatter', '서식통일_결과창_반영', globals())


_결과창_띄우는가 = _engine_resolve('docfit_engine.formatter', '_결과창_띄우는가', globals())


_서식통일_최종결과_사용자확인 = _engine_resolve('docfit_engine.formatter', '_서식통일_최종결과_사용자확인', globals())


_서식통일_미확정_항목 = _engine_resolve('docfit_engine.formatter', '_서식통일_미확정_항목', globals())


_서식통일_미확정_빨간표시 = _engine_resolve('docfit_engine.formatter', '_서식통일_미확정_빨간표시', globals())


_서식통일_문단앞간격_적용 = _engine_resolve('docfit_engine.formatter', '_서식통일_문단앞간격_적용', globals())


_서식통일_내어쓰기_필요 = _engine_resolve('docfit_engine.formatter', '_서식통일_내어쓰기_필요', globals())


_서식통일_내어쓰기_상태 = _engine_resolve('docfit_engine.formatter', '_서식통일_내어쓰기_상태', globals())


_서식통일_문단서식_적용 = _engine_resolve('docfit_engine.formatter', '_서식통일_문단서식_적용', globals())


# 서식통일 글자 요소 → 한/글 CharShape 항목(실측 2026-10-03: Italic=1 → italic,
# UnderlineType=1 → underline BOTTOM, StrikeOutType=1 → strikeout SOLID).
_서식통일_글자요소_항목 = {
    "italic": ("Italic",),
    "underline": ("UnderlineType", "UnderlineShape", "UnderlineColor"),
    "strike": ("StrikeOutType", "StrikeOutShape", "StrikeOutColor"),
}


_서식통일_글자요소_적용 = _engine_resolve('docfit_engine.formatter', '_서식통일_글자요소_적용', globals())


_서식통일_색값 = _engine_resolve('docfit_engine.formatter', '_서식통일_색값', globals())


_서식통일_색_적용 = _engine_resolve('docfit_engine.formatter', '_서식통일_색_적용', globals())


_서식통일_문단내어쓰기_적용 = _engine_resolve('docfit_engine.formatter', '_서식통일_문단내어쓰기_적용', globals())


_서식통일_문단자간_조정 = _engine_resolve('docfit_engine.formatter', '_서식통일_문단자간_조정', globals())


알파_서식통일_XML조사_사용 = True   # 서식통일 표본 조사를 한/글 문단 순회 대신 HWPX 스냅숏에서 한다(꺼짐=예전 순회)
_서식통일_글꼴크기_필드 = ("font", "size")


_서식통일_글꼴크기만 = _engine_resolve('docfit_engine.formatter', '_서식통일_글꼴크기만', globals())


_서식통일_글꼴크기_대표 = _engine_resolve('docfit_engine.formatter', '_서식통일_글꼴크기_대표', globals())


_서식통일_XML_조사 = _engine_resolve('docfit_engine.formatter', '_서식통일_XML_조사', globals())


_서식통일_COM_조사 = _engine_resolve('docfit_engine.formatter', '_서식통일_COM_조사', globals())


서식통일_전체_적용 = _engine_resolve('docfit_engine.formatter', '서식통일_전체_적용', globals())


서식통일_줄병합_사용 = True   # 짧은 마지막 줄(외톨이 글자) 당기기 사용 여부(작업별로 설정)
# 서식통일이 고친 문장의 자간 조정·외톨이 글자 당기기 사용 여부. 서식 통일 카드의 '자간 정리 제외'를 켜면
# 끈다(내어쓰기는 그대로 맞춘다).
서식통일_자간조정_사용 = True


서식통일_자간조정_반영 = _engine_resolve('docfit_engine.formatter', '서식통일_자간조정_반영', globals())


서식통일_문장_마무리 = _engine_resolve('docfit_engine.formatter', '서식통일_문장_마무리', globals())


알파_서식통일_위치마무리_사용 = True   # 마무리 단계에서 고친 문장을 계획 위치로 바로 찾는다(꺼짐=문서 전체 순회)


_서식통일_마무리_위치로 = _engine_resolve('docfit_engine.formatter', '_서식통일_마무리_위치로', globals())


서식통일_보류자간_재조정 = _engine_resolve('docfit_engine.formatter', '서식통일_보류자간_재조정', globals())


_서식통일_표모형 = _engine_resolve('docfit_engine.formatter', '_서식통일_표모형', globals())


서식통일_표_전체_적용 = _engine_resolve('docfit_engine.formatter', '서식통일_표_전체_적용', globals())


표준서식_전체_적용 = _engine_resolve('docfit_engine.formatter', '표준서식_전체_적용', globals())

# ============================================================
# 괄호 및 문두 라벨 처리 (콜론 라벨 굵게 + 괄호 라벨 굵게 + 부연설명 축소)
# ============================================================

괄호_축소_사용 = True
괄호_축소_pt = 2
괄호_라벨_볼드_사용 = True

# 문장 중간의 대괄호('[세부일정 붙임1]')도 소괄호와 같은 부연설명으로 보고 축소한다.
괄호_정규식 = re.compile(r"\(([^()]+)\)|\[([^\[\]]+)\]")


괄호_안쪽 = _engine_resolve('docfit_engine.formatter', '괄호_안쪽', globals())


대괄호인가 = _engine_resolve('docfit_engine.formatter', '대괄호인가', globals())
괄호_범위라벨_정규식 = re.compile(r"^\s*\d+\s*[~～\-–—]\s*\d+\s*번?\s*$")

# HWP 문단 앞에 섞일 수 있는 폭 없는 제어문자까지 문두 공백으로 취급한다.
_문두_무시문자_정규식 = re.compile(r"[\s\u200b\u2060\ufeff]+")

괄호_문두_라벨인가 = _engine_resolve('docfit_engine.formatter', '괄호_문두_라벨인가', globals())

괄호_뒤_콜론인가 = _engine_resolve('docfit_engine.formatter', '괄호_뒤_콜론인가', globals())


세트후속_범위괄호_라벨인가 = _engine_resolve('docfit_engine.formatter', '세트후속_범위괄호_라벨인가', globals())

문단_범위_선택 = _engine_resolve('docfit_engine.formatter', '문단_범위_선택', globals())

선택범위_현재크기_pt = _engine_resolve('docfit_engine.formatter', '선택범위_현재크기_pt', globals())

괄호_축소량_pt = _engine_resolve('docfit_engine.formatter', '괄호_축소량_pt', globals())
대괄호_축소_제외 = _engine_resolve('docfit_engine.formatter', '대괄호_축소_제외', globals())


괄호_텍스트_크기_축소_현재선택 = _engine_resolve('docfit_engine.formatter', '괄호_텍스트_크기_축소_현재선택', globals())

문두_라벨_굵게_제외_문단인가 = _engine_resolve('docfit_engine.formatter', '문두_라벨_굵게_제외_문단인가', globals())


# 항목기호별 굵게 일관성 규칙:
# 같은 항목기호를 쓰는 문단 중 하나라도 문두 라벨('- 추진부서 : …'의
# '추진부서', '- (운영방식) …'의 '(운영방식)')이 굵게 처리되면, 그 기호를
# 쓰는 다른 문단의 머리말('- 조례제정 (무료 셔틀버스 …)'의 '조례제정')도
# 굵게 맞춘다. 부연·보조 설명 괄호는 굵게 하지 않는다. 머리말 없이 일반
# 문장으로 이어지는 문단은 문장 전체가 굵어지므로 대상에서 뺀다.
_일관성_머리말_최대글자수 = 15
항목기호_굵게_일관성_사용 = True  # 설정 > 서식 정리 > 항목 이름 강조에서 켜고 끔
_일관성_굵게_적용기호 = set()


항목기호_키 = _engine_resolve('docfit_engine.formatter', '항목기호_키', globals())


일관성_굵게_머리말_범위 = _engine_resolve('docfit_engine.formatter', '일관성_굵게_머리말_범위', globals())

문두_라벨_굵게_선반영 = _engine_resolve('docfit_engine.formatter', '문두_라벨_굵게_선반영', globals())

괄호_및_라벨_텍스트_문단_처리 = _engine_resolve('docfit_engine.formatter', '괄호_및_라벨_텍스트_문단_처리', globals())

라벨괄호_계획 = _engine_resolve('docfit_engine.formatter', '라벨괄호_계획', globals())


# 알파 1-b(2026-10-11): 문두 라벨 굵게·부연설명 괄호 축소를 지금 열린 문서의 HWPX에서 한다(한/글 문단별 선택 대신).
알파_라벨괄호_XML_사용 = False   # 실측(2026-10-11, test4): 216.4초 → 213.9초(−1.2%, 오차 수준). 다시 열기 비용과 비슷해 1-c 묶음 뒤 재판단


라벨괄호_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '라벨괄호_hwpx_처리', globals())


표안_문단_구분 = _engine_resolve('docfit_engine.formatter', '표안_문단_구분', globals())


공백규칙_글변환 = _engine_resolve('docfit_engine.formatter', '공백규칙_글변환', globals())


문장부호뒤공백_글변환 = _engine_resolve('docfit_engine.formatter', '문장부호뒤공백_글변환', globals())


# 알파 1-c(2026-10-11): 공백 정규화·문장부호 뒤 공백(·서식통일이 꺼져 있으면 문두 라벨/괄호까지)을 지금 열린 문서의 HWPX에서
# 한 번에 처리하고 다시 연다(한/글 문단별 수정 세 단계 대신). 끄면 예전 한/글 경로. 한 칸 표 보호·쪽 범위 작업은 예전 경로.
알파_글규칙_XML_사용 = True
_글규칙_XML_구성 = {"space": False, "punct": False, "label": False}


글규칙_hwpx_처리 = _engine_resolve('docfit_engine.formatter', '글규칙_hwpx_처리', globals())


현재문서_XML단계_적용 = _engine_resolve('docfit_engine.formatter', '현재문서_XML단계_적용', globals())


괄호_텍스트_크기_축소_전체_적용 = _engine_resolve('docfit_engine.formatter', '괄호_텍스트_크기_축소_전체_적용', globals())

# ============================================================
# 자간조정 및 단어 분리 방지 알고리즘
# ============================================================

현재_페이지번호 = _engine_resolve('docfit_engine.spacing', '현재_페이지번호', globals())

# 저장 후 결과 검사가 끝난 규칙은 처리 중 기록을 대신한다. 처리 중 기록은
# 뒤 단계에서 해결됐을 수도 있고, 같은 문제를 다른 이름으로 한 번 더 세게 된다.
_처리중_기록_접두어 = {
    'page_group': ('[문장 묶음 페이지 분리]', '[소제목 묶음 쪽 분리]'),
    'word': ('[단어 중간 줄바꿈 미해결]', '[어절 줄분리]', '[단어 분리]',
             '[붙임 괄호 분리]', '[괄호 안 공백 분리]'),
}


처리중_기록_대체 = _engine_resolve('docfit_engine.spacing', '처리중_기록_대체', globals())


검수_문제_기록 = _engine_resolve('docfit_engine.spacing', '검수_문제_기록', globals())


줄경계_어절연속_문자쌍인가 = _engine_resolve('docfit_engine.spacing', '줄경계_어절연속_문자쌍인가', globals())


현재줄_끝_어절분리인가 = _engine_resolve('docfit_engine.spacing', '현재줄_끝_어절분리인가', globals())


_붙임괄호_다음구간_미리보기_글자수 = 3

현재줄_끝_붙임괄호_분리인가 = _engine_resolve('docfit_engine.spacing', '현재줄_끝_붙임괄호_분리인가', globals())


_괄호내부_다음구간_미리보기_글자수 = 40


현재줄_끝_괄호내부_공백분리인가 = _engine_resolve('docfit_engine.spacing', '현재줄_끝_괄호내부_공백분리인가', globals())


# 단어는 한글/영문/숫자와 결합문자, 단어 사이 가운뎃점으로 판정한다.
단어문자인가 = _engine_resolve('docfit_engine.spacing', '단어문자인가', globals())


단어모드_범위선택 = _engine_resolve('docfit_engine.spacing', '단어모드_범위선택', globals())


단어모드_한글자 = _engine_resolve('docfit_engine.spacing', '단어모드_한글자', globals())


단어모드_줄범위 = _engine_resolve('docfit_engine.spacing', '단어모드_줄범위', globals())


_단어_붙임표시 = frozenset(",，'\"‘’“”")


# 날짜 내부의 마침표는 단어 경계로 취급하지 않는다.
# 비정형 원문(예: 26.5.6.30.)도 숫자 묶음을 그대로 보존한다.
_날짜_패턴 = r"[‘’'ʼ]?(?:[0-9]{4}|[0-9]{2})(?:\.[0-9]{1,2}){1,3}\."
# 띄어 쓴 월·일 날짜와 기간('10. 19.~11. 18.', '2026. 10. 19.')도 하나의 어절로 본다.
_띄운날짜_패턴 = r"(?:[0-9]{4}\. )?[0-9]{1,2}\. [0-9]{1,2}\."
_띄운기간_패턴 = (r"(?<![0-9.])" + _띄운날짜_패턴
               + r"(?: ?[~∼～] ?(?:" + _띄운날짜_패턴 + r"|[0-9]{1,2}\.))?")
_띄운날짜어절 = re.compile(r"[0-9]+\.(?:[0-9]+\.)*(?:[~∼～][0-9]+\.)?|[~∼～]")
_기간_단위 = re.compile(
    _띄운기간_패턴 + r"|"
    r"(?<![0-9])(?:\(" + _날짜_패턴 + r"(?:[~∼～](?:" + _날짜_패턴 + r")?)?\)"
    r"|（" + _날짜_패턴 + r"(?:[~∼～](?:" + _날짜_패턴 + r")?)?）"
    r"|" + _날짜_패턴 + r")|[~∼～]"
)

from docfit_core.semantic_units import STAFF_PREFIX, staff_role_name_ranges


의미단위_범위 = _engine_resolve('docfit_engine.spacing', '의미단위_범위', globals())


일반_의미단위_범위 = _engine_resolve('docfit_engine.spacing', '일반_의미단위_범위', globals())


# 열거 뒤에 쓰는 의존명사 '등'은 바로 앞 어절과 한 어절로 묶는다.
# 예: '사과, 바나나 등으로' → '바나나 등으로'가 한 어절이므로 '바나나 | 등으로'로
# 갈라지면 단어 분리로 보고 자간을 조정한다. '등록', '등급'처럼 '등'으로
# 시작하는 다른 낱말은 뒤에 조사만 오는 경우가 아니므로 묶지 않는다.
_등_어절 = re.compile(
    r"등(?:으로서|으로써|으로|에서|에게|까지|부터|이며|이고|이다|이나|이라|"
    r"과|와|을|를|은|는|이|가|의|에|도|만)?[,，.)）」』’”]*")


등_어절인가 = _engine_resolve('docfit_engine.spacing', '등_어절인가', globals())


# 열거의 '단어 + 빈칸 + 숫자 + 쉼표'도 한 어절로 묶는다.
# 예: '수원 2, 서울 4, 용인 1등으로 구성' → '수원 2,'와 '서울 4,'가 각각 한
# 어절이므로 '수원 | 2,'로 갈라지면 단어 분리로 보고 자간을 조정한다.
_숫자쉼표_어절 = re.compile(r"[0-9]+(?:\.[0-9]+)?[,，]")


숫자쉼표_어절인가 = _engine_resolve('docfit_engine.spacing', '숫자쉼표_어절인가', globals())


# 열거의 마지막 항목은 쉼표 없이 끝난다: '…, 서울 4, 용인 1등으로 구성'의
# '용인 1등으로'. 숫자로 시작하고 쉼표로 끝나지 않는 어절이며, 바로 앞 항목이
# '서울 4,'처럼 '숫자 + 쉼표'로 끝날 때만 묶는다('대회에서 1등으로'는 묶지 않음).
_숫자끝_어절 = re.compile(r"[0-9]+(?:\.[0-9]+)?[^\s,，]*")
_숫자쉼표_끝 = re.compile(r"[0-9]+(?:\.[0-9]+)?[,，]$")


숫자끝_어절인가 = _engine_resolve('docfit_engine.spacing', '숫자끝_어절인가', globals())


_숫자쉼표_앞단어인가 = _engine_resolve('docfit_engine.spacing', '_숫자쉼표_앞단어인가', globals())


어절_의미단위_범위 = _engine_resolve('docfit_engine.spacing', '어절_의미단위_범위', globals())


앞어절_묶음_후속인가 = _engine_resolve('docfit_engine.spacing', '앞어절_묶음_후속인가', globals())


_왼쪽_어절_추가 = _engine_resolve('docfit_engine.spacing', '_왼쪽_어절_추가', globals())


_단어모드_공백전까지 = _engine_resolve('docfit_engine.spacing', '_단어모드_공백전까지', globals())


_띄운날짜_어절_확장 = _engine_resolve('docfit_engine.spacing', '_띄운날짜_어절_확장', globals())


_직함이름_어절_확장 = _engine_resolve('docfit_engine.spacing', '_직함이름_어절_확장', globals())


단어모드_분리정보 = _engine_resolve('docfit_engine.spacing', '단어모드_분리정보', globals())


# 줄 첫머리에서 시작한 단어가 넘친 부분이 그 줄 글자 수의 이 비율을 넘으면
# 자간·장평을 허용 범위까지 줄여도 한 줄에 넣을 수 없다(좁은 표 칸의 긴 합성어).
칸폭초과_허용비율 = 0.2


칸폭보다_긴_단어인가 = _engine_resolve('docfit_engine.spacing', '칸폭보다_긴_단어인가', globals())


붙임의미단위_줄분리인가 = _engine_resolve('docfit_engine.spacing', '붙임의미단위_줄분리인가', globals())


_단어모드_자간필드 = tuple('Spacing' + name for name in
    ('Hangul', 'Latin', 'Hanja', 'Japanese', 'Other', 'Symbol', 'User'))
_단어모드_장평필드 = tuple('Ratio' + name for name in
    ('Hangul', 'Latin', 'Hanja', 'Japanese', 'Other', 'Symbol', 'User'))


자간보호_글자수 = _engine_resolve('docfit_engine.spacing', '자간보호_글자수', globals())


자간조정_본문범위 = _engine_resolve('docfit_engine.spacing', '자간조정_본문범위', globals())


자간조정_현재줄_본문선택 = _engine_resolve('docfit_engine.spacing', '자간조정_현재줄_본문선택', globals())


_단어모드_다음위치 = _engine_resolve('docfit_engine.spacing', '_단어모드_다음위치', globals())


단어모드_서식보관 = _engine_resolve('docfit_engine.spacing', '단어모드_서식보관', globals())


단어모드_자간보관 = _engine_resolve('docfit_engine.spacing', '단어모드_자간보관', globals())


단어모드_자간적용 = _engine_resolve('docfit_engine.spacing', '단어모드_자간적용', globals())


단어모드_장평보관 = _engine_resolve('docfit_engine.spacing', '단어모드_장평보관', globals())


단어모드_장평적용 = _engine_resolve('docfit_engine.spacing', '단어모드_장평적용', globals())


class _단계탐색_중단(Exception):
    """단계 탐색 중 사용자가 작업을 중단했다."""


# 자간·장평 단계 탐색에서 실제로 줄 배치를 다시 잰 횟수(작업 로그 통계용).
단계탐색_통계 = {"탐색": 0, "측정": 0}


최소_성공단계_탐색 = _engine_resolve('docfit_engine.spacing', '최소_성공단계_탐색', globals())


단어_장평_추가축소_시도 = _engine_resolve('docfit_engine.spacing', '단어_장평_추가축소_시도', globals())


다음단어_당김_시도 = _engine_resolve('docfit_engine.spacing', '다음단어_당김_시도', globals())


어절분리_앞줄당김인가 = _engine_resolve('docfit_engine.spacing', '어절분리_앞줄당김인가', globals())


단어모드_마지막줄_짧은잔여인가 = _engine_resolve('docfit_engine.spacing', '단어모드_마지막줄_짧은잔여인가', globals())


# 연결 부호(사용자 규칙, 2026-10-10): 왼쪽·오른쪽 어절을 뜻으로 잇는 부호는 세 가지다 — 점('......', '……'),
# 선('------'), 여러 칸 빈칸('세부내용      3쪽'). 부호의 개수에는 뜻이 없다. '왼쪽 어절 + 연결 부호 + 오른쪽 어절'을
# 한 어절(연결 단위)로 보고, 줄 경계에 걸치면 ① 부호 글자만 자간을 한도를 넘어 한/글 최대(-50%)까지 줄이고,
# ② 그래도 안 되면 부호 개수를 끝에서부터 최소한으로 줄인다(2개는 남김). 둘 다 안 되면 원래대로 되돌린다.
알파_연결부호_맞춤_사용 = True
연결부호_최소개수 = 2
_연결부호 = re.compile(r"[-‐‑–—―]{3,}|[.·∙•‥…]{3,}|(?<=\S) {3,}(?=\S)|(?<=\S)\u3000{2,}(?=\S)")


연결부호_구간 = _engine_resolve('docfit_engine.spacing', '연결부호_구간', globals())


연결부호_단위들 = _engine_resolve('docfit_engine.spacing', '연결부호_단위들', globals())


연결부호_전체_맞춤 = _engine_resolve('docfit_engine.spacing', '연결부호_전체_맞춤', globals())


_연결단위_맞춤 = _engine_resolve('docfit_engine.spacing', '_연결단위_맞춤', globals())


단어중간_줄바꿈방지 = _engine_resolve('docfit_engine.spacing', '단어중간_줄바꿈방지', globals())


자간자동조정 = _engine_resolve('docfit_engine.spacing', '자간자동조정', globals())


_자간자동조정_본체 = _engine_resolve('docfit_engine.spacing', '_자간자동조정_본체', globals())

본문_기존자간조정 = _engine_resolve('docfit_engine.spacing', '본문_기존자간조정', globals())

# ============================================================
# 알파: 문단 세트 방식(2026-10-09, 사용자 요청)
# 지금 방식은 공백 정규화·라벨/괄호·내어쓰기·부연설명·별표·자간·줄 병합을 단계마다 문서 전체로 한 번씩 돈다.
# 세트 방식은 이 절차들을 두 세트로 묶어 문단 하나에 세트 전체를 차례로 적용한 뒤 다음 문단으로 간다.
#   세트 1(글·서식): 공백 정규화 9규칙 → 문장부호 뒤 공백 → 라벨/괄호. 끝나면 항목기호 굵게 일관성(문서 전체를 본 뒤
#                    정해지므로 자간보다 먼저) 한 번.
#   세트 2(배치): 내어쓰기 → 부연설명 → 별표 정렬 → 자간·단어 분리 → 짧은 줄 병합. 자간이 바뀌면 그 문단만 내어쓰기를
#                 다시 하고 자간을 재검사(최대 자간_내어쓰기_최대반복회, 2회차부터 다음 단어 당김 제외 — 기존 반복과 같은 규칙).
# 표 서식·표 칸 자간·쪽 맞춤·배치처럼 문서 단위로 봐야 하는 단계는 기존대로 따로 돈다. 끄면(False) 베타와 같다.
# ============================================================
알파_문단세트_사용 = False   # 실측 효과 없음(2026-10-10): 시간 대부분이 줄마다 한/글에 재 보는 작업이라 순회를 묶어도 줄지 않음


문단세트_가능 = _engine_resolve('docfit_engine.spacing', '문단세트_가능', globals())


문단세트1_글서식_적용 = _engine_resolve('docfit_engine.spacing', '문단세트1_글서식_적용', globals())


_문단세트_줄순회 = _engine_resolve('docfit_engine.spacing', '_문단세트_줄순회', globals())


문단세트2_배치_적용 = _engine_resolve('docfit_engine.spacing', '문단세트2_배치_적용', globals())


# ============================================================
# 문장부호 판정 및 공백 보정
# ============================================================

공문서_기호 = {
    "※", "ㅁ", "□", "■", "○", "●", "◎", "◇", "◆", "△", "▲", "▽", "▼",
    "▷", "▶", "◁", "◀", "▪", "▫", "ㆍ", "·", "‧", "•", "∙", "⋅", "‣", "⁃", "ㅇ",
    "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
    # DINGBAT NEGATIVE CIRCLED DIGIT/SANS-SERIF DIGIT (❶❷❸.../➊➋➌...).
    # 유니코드 카테고리가 "No"(숫자류)라서 문장부호_시작인가()의 P/S 카테고리
    # 폴백에 걸리지 않아, 이 기호로 시작하는 문단이 표준서식(내어쓰기)과
    # 문장부호_줄병합_시도(짧은 마지막 줄 합치기) 대상에서 통째로 빠지던 문제가 있었다.
    "❶", "❷", "❸", "❹", "❺", "❻", "❼", "❽", "❾", "❿",
    "➊", "➋", "➌", "➍", "➎", "➏", "➐", "➑", "➒", "➓",
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

_괄호따옴표_시작문자인가 = _engine_resolve('docfit_engine.spacing', '_괄호따옴표_시작문자인가', globals())

문장부호_시작인가 = _engine_resolve('docfit_engine.spacing', '문장부호_시작인가', globals())

문장부호_마커_끝위치 = _engine_resolve('docfit_engine.spacing', '문장부호_마커_끝위치', globals())

세트문장_시작인가 = _engine_resolve('docfit_engine.spacing', '세트문장_시작인가', globals())


세트문장_선행들여쓰기_폭 = _engine_resolve('docfit_engine.page_fit', '세트문장_선행들여쓰기_폭', globals())


세트문장_후속문단인가 = _engine_resolve('docfit_engine.page_fit', '세트문장_후속문단인가', globals())


세트문장_끝위치_찾기 = _engine_resolve('docfit_engine.page_fit', '세트문장_끝위치_찾기', globals())


위치_페이지번호 = _engine_resolve('docfit_engine.page_fit', '위치_페이지번호', globals())


현재문단_줄간격_퍼센트 = _engine_resolve('docfit_engine.page_fit', '현재문단_줄간격_퍼센트', globals())


항목기호_역할표 = _engine_resolve('docfit_engine.page_fit', '항목기호_역할표', globals())


보고서_문단역할 = _engine_resolve('docfit_engine.page_fit', '보고서_문단역할', globals())


보고서_본문묶음_수집 = _engine_resolve('docfit_engine.page_fit', '보고서_본문묶음_수집', globals())


보고서_단어분리_최종검사 = _engine_resolve('docfit_engine.page_fit', '보고서_단어분리_최종검사', globals())


보고서_페이지배치_최종검사 = _engine_resolve('docfit_engine.page_fit', '보고서_페이지배치_최종검사', globals())


보고서_묶음_쪽별줄수 = _engine_resolve('docfit_engine.page_fit', '보고서_묶음_쪽별줄수', globals())


# 줄간격으로 옮기지 못한 묶음을 '문단 앞에서 쪽 나눔'으로 다음 쪽에 보낼 때,
# 앞쪽에 남는 빈 공간이 한 쪽 줄 수의 이 비율 이하일 때만 쪽을 나눈다.
쪽나눔_최대_앞쪽비율 = 0.5


쪽_본문줄수 = _engine_resolve('docfit_engine.page_fit', '쪽_본문줄수', globals())


쪽첫줄_시작인가 = _engine_resolve('docfit_engine.page_fit', '쪽첫줄_시작인가', globals())


쪽보다_긴_묶음인가 = _engine_resolve('docfit_engine.page_fit', '쪽보다_긴_묶음인가', globals())


# 결과 문서의 '쪽 나누기'(문단 앞 쪽 나눔)는 모든 작업이 끝난 뒤 저장 직전에 푼다(사용자 지시, 2026-10-09). 남기는 것은
# 두 가지뿐이다: 보고서 경계(제목 표 앞)와, 쪽 배치가 줄간격으로 옮기지 못한 묶음을 다음 쪽에 보내려고 넣은 쪽 나눔
# (사용자 결정, 2026-10-09: 표 제목 문장이 앞쪽에 홀로 남는 것을 막는다). 원문에 있던 쪽 나누기 등은 지운다.
쪽나누기_사용 = True
# 쪽 배치가 묶음을 옮기려고 넣은 쪽 나눔의 본문 문단 번호(저장 직전 해제에서 남긴다).
쪽배치_쪽나눔문단 = set()


문서_쪽나누기_전체해제 = _engine_resolve('docfit_engine.page_fit', '문서_쪽나누기_전체해제', globals())


쪽나눔_설정 = _engine_resolve('docfit_engine.page_fit', '쪽나눔_설정', globals())


_묶음_쪽나눔_이동 = _engine_resolve('docfit_engine.page_fit', '_묶음_쪽나눔_이동', globals())


보고서_압축조건 = _engine_resolve('docfit_engine.page_fit', '보고서_압축조건', globals())


보고서_줄간격_보관 = _engine_resolve('docfit_engine.page_fit', '보고서_줄간격_보관', globals())


보고서_줄간격_적용 = _engine_resolve('docfit_engine.page_fit', '보고서_줄간격_적용', globals())


보고서_페이지보호_전체해제 = _engine_resolve('docfit_engine.page_fit', '보고서_페이지보호_전체해제', globals())


# 쪽 맞춤 논리묶음: □(소제목)를 기준으로 이어지는 ㅇ/-/* 문단 전체.
# 논리단위: □ 또는 ㅇ에서 시작하고, 뒤따르는 -(내용)·*(부연설명)은 바로 앞
# 단위에 붙는다(ㅇ- = ㅇ, ㅇ* = ㅇ, ㅇ-* = ㅇ, □* = □). 논리단위가
# 쪽맞춤_묶음_최대단위(5개) 이하인 묶음은 묶음 전체를 한 쪽에 모은다.
# 앞쪽에서 시작한 단위 수가 뒤쪽 이상이면 앞쪽으로 당기고, 적으면 뒤쪽으로 민다.
# 예: □/ㅇ → □ㅇ/, □ㅇ/ㅇㅇ → □ㅇㅇㅇ/, □ㅇ/ㅇㅇㅇ → /□ㅇㅇㅇㅇ,
#     □ㅇ-/-- → □ㅇ---/(쪽을 넘어간 -는 앞쪽에서 시작한 ㅇ 단위),
#     □ㅇ--/-ㅇㅇ → □ㅇ/ㅇㅇ와 같으므로 □ㅇ---ㅇㅇ/.
# 6개 이상이면 묶음은 그대로 두고 ㅇ 단위(ㅇ와 -·*)만 한 쪽에 모은다.
쪽맞춤_묶음_최대단위 = 5


쪽맞춤_논리단위 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_논리단위', globals())


쪽맞춤_뒤로밀기인가 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_뒤로밀기인가', globals())


보고서_소제목묶음_수집 = _engine_resolve('docfit_engine.page_fit', '보고서_소제목묶음_수집', globals())


문단_첫줄_쪽 = _engine_resolve('docfit_engine.page_fit', '문단_첫줄_쪽', globals())


소제목묶음_뒤_표인가 = _engine_resolve('docfit_engine.page_fit', '소제목묶음_뒤_표인가', globals())


소제목묶음_쪽맞춤_대상 = _engine_resolve('docfit_engine.page_fit', '소제목묶음_쪽맞춤_대상', globals())


# 줄간격이 이미 최소라 묶음을 앞쪽으로 당기지 못하면, 그 쪽 문단들의 '문단 위 간격'을 원래 값의 10%씩
# 최대 이 비율까지 줄여 당긴다(2026-10-04 실측: 서식 예시 'Ⅱ 추진 계획' 묶음이 '- 입자가속기 …' 한 줄 때문에
# 2쪽으로 밀림). 당기지 못하면 원래 간격으로 되돌린다.
쪽맞춤_위간격_최대축소비율 = 0.5


_묶음_위간격_축소_당김 = _engine_resolve('docfit_engine.page_fit', '_묶음_위간격_축소_당김', globals())


_묶음뒤_같은쪽_줄간격_맞춤 = _engine_resolve('docfit_engine.page_fit', '_묶음뒤_같은쪽_줄간격_맞춤', globals())
쪽배치_축소쪽_줄간격_통일 = _engine_resolve('docfit_engine.page_fit', '쪽배치_축소쪽_줄간격_통일', globals())
_묶음_같은쪽_이동 = _engine_resolve('docfit_engine.page_fit', '_묶음_같은쪽_이동', globals())


소제목묶음_단위경계_앞쪽우선 = _engine_resolve('docfit_engine.page_fit', '소제목묶음_단위경계_앞쪽우선', globals())


소제목묶음_같은쪽_시도 = _engine_resolve('docfit_engine.page_fit', '소제목묶음_같은쪽_시도', globals())


# ---- 표 묶음 쪽 배치 ------------------------------------------------------
# 'ㅇ (세부 추진일정)' + 표 + 표 주석(*, **, ※)은 하나의 묶음이다(실측: 지구 침공계획 보고,
# 제목 문장만 3쪽 끝에 남고 표·주석은 4쪽으로 넘어감). 표가 든 문단은 글자가 없어 역할이
# 없으므로 예전 묶음 수집은 표 앞에서 끊겼고, 표 높이는 본문 줄 수로 잴 수 없다.
# 표의 쪽은 첫 칸과 마지막 칸의 쪽으로 판정한다.
_표칸영역 = {}
# 쪽 나눔(Ctrl+Enter)으로 새 쪽을 시작하는 본문 문단 번호. 표 묶음 판정 전에 본문_쪽나눔_기억()으로 채운다.
_쪽나눔문단 = set()


본문_표_문단번호 = _engine_resolve('docfit_engine.page_fit', '본문_표_문단번호', globals())


본문_쪽나눔_기억 = _engine_resolve('docfit_engine.page_fit', '본문_쪽나눔_기억', globals())


표_칸영역_범위 = _engine_resolve('docfit_engine.page_fit', '표_칸영역_범위', globals())


표_쪽범위 = _engine_resolve('docfit_engine.page_fit', '표_쪽범위', globals())


보고서_표묶음_수집 = _engine_resolve('docfit_engine.page_fit', '보고서_표묶음_수집', globals())


표묶음_같은쪽_시도 = _engine_resolve('docfit_engine.page_fit', '표묶음_같은쪽_시도', globals())


세트문장_같은쪽_시도 = _engine_resolve('docfit_engine.page_fit', '세트문장_같은쪽_시도', globals())


# ---- 로마자 중제목 쪽 배치 ---------------------------------------------------
# 'Ⅰ | 추진 배경' 같은 로마자 중제목 표는 뒤따르는 □ 소제목의 머리다. 중제목 + □ + 첫 ㅇ(딸린 -·*까지)은
# 쪼갤 수 없는 하나의 논리 묶음이므로 한 쪽에 둔다(2026-10-04 사용자 요청, 실측: 서식 예시 1쪽 마지막 줄에
# 'Ⅱ 추진 계획'만 남음). 뒤 □ 묶음과 첫 ㅇ 단위의 쪽 배치가 끝난 뒤 이 묶음이 두 쪽에 걸쳤으면, 소제목처럼
# 줄간격으로 당기거나 밀고, 안 되면 중제목 앞에서 쪽을 나눈 뒤 □ 묶음을 다시 배치한다.
_로마자_중제목_번호 = re.compile(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ]+\.?$|^[IVX]{1,5}\.?$")


로마자_중제목_표인가 = _engine_resolve('docfit_engine.page_fit', '로마자_중제목_표인가', globals())


중제목_다음글문단 = _engine_resolve('docfit_engine.page_fit', '중제목_다음글문단', globals())


쪽나눔_켜짐 = _engine_resolve('docfit_engine.page_fit', '쪽나눔_켜짐', globals())


중제목_묶음_문단 = _engine_resolve('docfit_engine.page_fit', '중제목_묶음_문단', globals())


중제목_묶음_쪽 = _engine_resolve('docfit_engine.page_fit', '중제목_묶음_쪽', globals())


중제목_외톨이_정리 = _engine_resolve('docfit_engine.page_fit', '중제목_외톨이_정리', globals())


세트문장_같은쪽_전체_적용 = _engine_resolve('docfit_engine.page_fit', '세트문장_같은쪽_전체_적용', globals())


마지막쪽_화면줄수 = _engine_resolve('docfit_engine.page_fit', '마지막쪽_화면줄수', globals())


# 페이지 수 맞춤 소요 시간 계측(2026-10-08). 동작은 바꾸지 않고, 쪽 수 맞춤이 도는 동안만
# 구간별 (누적 초, 건수)를 모아 단계마다 한 줄, 끝에 합계 한 줄을 작업 로그에 남긴다.
# 실측: 15쪽 문서의 쪽 수 맞춤이 실패까지 5분 21초(전체의 85%) 걸렸는데 구간별 시간을 몰랐다.
쪽맞춤_계측값 = None


쪽맞춤_계측_시작 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_계측_시작', globals())


쪽맞춤_계측_끝 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_계측_끝', globals())


쪽맞춤_계측_더하기 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_계측_더하기', globals())


쪽맞춤_계측_복사 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_계측_복사', globals())


쪽맞춤_계측_차이 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_계측_차이', globals())


쪽맞춤_계측_단계문구 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_계측_단계문구', globals())


쪽맞춤_계측_합계문구 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_계측_합계문구', globals())


문단_위간격_pt_현재문단 = _engine_resolve('docfit_engine.page_fit', '문단_위간격_pt_현재문단', globals())


구조문단_간격_일괄조정 = _engine_resolve('docfit_engine.page_fit', '구조문단_간격_일괄조정', globals())


구조문단_아래간격_일괄조정 = _engine_resolve('docfit_engine.page_fit', '구조문단_아래간격_일괄조정', globals())


구조문단_간격_복원 = _engine_resolve('docfit_engine.page_fit', '구조문단_간격_복원', globals())


셀_세로여백_읽기 = _engine_resolve('docfit_engine.page_fit', '셀_세로여백_읽기', globals())


셀_세로여백_현재선택 = _engine_resolve('docfit_engine.page_fit', '셀_세로여백_현재선택', globals())


표_셀_세로여백_일괄조정 = _engine_resolve('docfit_engine.page_fit', '표_셀_세로여백_일괄조정', globals())


# 문서 유형별 쪽 맞춤 한 번 동안 쓰는 표 칸 묶음 캐시(None이면 쓰지 않음). 간격·여백·쪽 나눔만 바꾸므로 표 칸
# 목록 번호(area)는 그동안 바뀌지 않는다. 예전에는 보고서마다 문서의 표 칸 전체를 다시 훑었다(2026-10-09).
_쪽맞춤_표캐시 = None


_표_셀_대상_순회 = _engine_resolve('docfit_engine.page_fit', '_표_셀_대상_순회', globals())


표_셀_세로여백_복원 = _engine_resolve('docfit_engine.page_fit', '표_셀_세로여백_복원', globals())


# 목표 쪽 수에 닿은 뒤 묶음이 쪽 경계에 걸려 있으면 몇 단계까지 더 줄여 볼지.
페이지맞춤_묶음확인_추가단계 = 4
# 마지막 페이지 수 맞춤이 묶음 규칙까지 지키며 끝났는지(쪽 배치 재실행 생략용).
쪽맞춤_묶음_확인됨 = False
# 마지막 페이지 수 맞춤이 '걸린 묶음은 다음 쪽으로 옮긴다'로 끝났는지. 이때는
# 쪽 배치가 묶음을 옮겨 마지막 쪽이 짧아져도 다시 줄이지 않는다(사용자 결정).
쪽맞춤_묶음이동_결정 = False


쪽맞춤_묶음분리_있음 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_묶음분리_있음', globals())


쪽맞춤_대상_조사 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_대상_조사', globals())


쪽맞춤_레벨_적용 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_레벨_적용', globals())


_보고서_페이지수_맞춤_고속 = _engine_resolve('docfit_engine.page_fit', '_보고서_페이지수_맞춤_고속', globals())


보고서_페이지수_맞춤_시도 = _engine_resolve('docfit_engine.page_fit', '보고서_페이지수_맞춤_시도', globals())


_보고서_페이지수_맞춤_시도_본체 = _engine_resolve('docfit_engine.page_fit', '_보고서_페이지수_맞춤_시도_본체', globals())


# 문서 유형별 쪽 수 맞춤(사용자 규칙, 2026-10-09). 보고서 1개 = 제목 표 1개 + 계층체계 1개이고, 제목 표마다
# 새 보고서다(붙임은 앞 보고서에 속한다). 1쪽 보고서는 모든 문장이 1쪽에 담겨야 하고, 1쪽 보고서를 묶은
# 취합보고서는 각 보고서가 자기 1쪽 안에 들어가야 한다. 심화보고서(제목 1개, 1쪽 초과)는 기존처럼 마지막 쪽만 본다.
# 담당자 칸: 부서명·직함·담당자 이름·내선/전화번호(3행1열 제목 표는 소속이 다른 두 담당자 칸, 사용자 설명 2026-10-09).
_제목표_담당자 = re.compile(r'담당|과장|팀장|본부장|부장|☎|전화|내선|부서|작성|\d{2,4}-\d{4}')
_제목표_날짜 = re.compile(r'[0-9]{2,4}\s*[.년/\-]\s*[0-9]{1,2}')


_칸_문단글들 = _engine_resolve('docfit_engine.page_fit', '_칸_문단글들', globals())


제목표인가_현재 = _engine_resolve('docfit_engine.page_fit', '제목표인가_현재', globals())


_한칸_제목표인가_현재 = _engine_resolve('docfit_engine.page_fit', '_한칸_제목표인가_현재', globals())


_기타_제목표인가_현재 = _engine_resolve('docfit_engine.page_fit', '_기타_제목표인가_현재', globals())


_보고서_끝내용 = _engine_resolve('docfit_engine.page_fit', '_보고서_끝내용', globals())


쪽맞춤_보고서_끝쪽 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_보고서_끝쪽', globals())


쪽맞춤_보고서_목록 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_보고서_목록', globals())


_쪽맞춤_줄간격_되돌리기 = _engine_resolve('docfit_engine.page_fit', '_쪽맞춤_줄간격_되돌리기', globals())


보고서_1쪽_맞춤 = _engine_resolve('docfit_engine.page_fit', '보고서_1쪽_맞춤', globals())


_자간_항목 = ("SpacingHangul", "SpacingLatin", "SpacingHanja", "SpacingJapanese", "SpacingOther", "SpacingSymbol",
            "SpacingUser")


문단_화면줄수 = _engine_resolve('docfit_engine.page_fit', '문단_화면줄수', globals())


문단_자간_읽기 = _engine_resolve('docfit_engine.page_fit', '문단_자간_읽기', globals())


문단_자간_적용 = _engine_resolve('docfit_engine.page_fit', '문단_자간_적용', globals())


_문단_줄시작들 = _engine_resolve('docfit_engine.page_fit', '_문단_줄시작들', globals())


문단_줄수_원본맞춤 = _engine_resolve('docfit_engine.page_fit', '문단_줄수_원본맞춤', globals())


보고서_새쪽_시작인가 = _engine_resolve('docfit_engine.page_fit', '보고서_새쪽_시작인가', globals())


_대표_줄간격 = _engine_resolve('docfit_engine.page_fit', '_대표_줄간격', globals())


쪽맞춤_원본_보고서_기록 = _engine_resolve('docfit_engine.page_fit', '쪽맞춤_원본_보고서_기록', globals())


_보고서_내부_쪽나눔_해제 = _engine_resolve('docfit_engine.page_fit', '_보고서_내부_쪽나눔_해제', globals())


_문서유형별_쪽맞춤 = _engine_resolve('docfit_engine.page_fit', '_문서유형별_쪽맞춤', globals())


_쪽맞춤_바꾼문단_단어분리_재검사 = _engine_resolve('docfit_engine.page_fit', '_쪽맞춤_바꾼문단_단어분리_재검사', globals())


_문서유형별_쪽맞춤_본체 = _engine_resolve('docfit_engine.page_fit', '_문서유형별_쪽맞춤_본체', globals())


보고서_페이지수_맞춤_전체_적용 = _engine_resolve('docfit_engine.page_fit', '보고서_페이지수_맞춤_전체_적용', globals())


# ============================================================
# 문장 내 공백 정규화
#   1) 괄호 바로 안쪽 공백 제거: "( 내용 )" -> "(내용)"
#   2) 단어-쉼표-단어 구조에서 쉼표 앞 0칸 + 뒤 1칸: "도토리,만두" -> "도토리, 만두"
# ============================================================

괄호_안쪽_공백_패턴 = re.compile(r"(?<=\()[ \t\u00A0\u3000]+|[ \t\u00A0\u3000]+(?=\))")


전체_찾아바꾸기 = _engine_resolve('docfit_engine.page_fit', '전체_찾아바꾸기', globals())


괄호_안쪽_공백_정리_AllReplace = _engine_resolve('docfit_engine.page_fit', '괄호_안쪽_공백_정리_AllReplace', globals())


괄호_안쪽_공백_정리_문단_처리 = _engine_resolve('docfit_engine.page_fit', '괄호_안쪽_공백_정리_문단_처리', globals())


쉼표_공백_보정_대상 = _engine_resolve('docfit_engine.page_fit', '쉼표_공백_보정_대상', globals())


쉼표_공백_정리_문단_처리 = _engine_resolve('docfit_engine.page_fit', '쉼표_공백_정리_문단_처리', globals())


_콜론_공백류 = " \t\u00A0\u3000"
_콜론_문자 = (":", "：")
_콜론_앞_닫는문자 = ")]}>」』”’'\""
_콜론_뒤_제외 = ")]}>」』”’"


_콜론_한글인가 = _engine_resolve('docfit_engine.page_fit', '_콜론_한글인가', globals())


콜론_공백_보정_대상 = _engine_resolve('docfit_engine.page_fit', '콜론_공백_보정_대상', globals())


콜론_공백_정리_문단_처리 = _engine_resolve('docfit_engine.page_fit', '콜론_공백_정리_문단_처리', globals())
항목기호_낫표_빈칸_구간 = _engine_resolve('docfit_engine.page_fit', '항목기호_낫표_빈칸_구간', globals())
항목기호_낫표_빈칸_정리_문단_처리 = _engine_resolve('docfit_engine.page_fit', '항목기호_낫표_빈칸_정리_문단_처리', globals())


# v1.10 함수명을 호출하는 기존 경로와의 호환성 유지
쉼표_앞_공백_보정_대상 = _engine_resolve('docfit_engine.page_fit', '쉼표_앞_공백_보정_대상', globals())


쉼표_앞_공백_정리_문단_처리 = _engine_resolve('docfit_engine.page_fit', '쉼표_앞_공백_정리_문단_처리', globals())


_단어사이_공백류 = (" ", "\t", "　")
# '일    시:', '총  무  과:'처럼 글자 사이를 띄워 긴 라벨('참석인원:')과 폭을 맞춘 문두 콜론 라벨.
# 이 공백은 정렬용이라 줄이면 같은 묶음의 콜론·둘째 줄 위치가 어긋난다(실측: 10월 확대간부회의 자료 24곳).
_균등라벨_패턴 = re.compile(r"(?:\S{1,2}[ \t　]+)?(\S(?:[ \t　]+\S){1,5})[ \t　]*[:：]")


_균등라벨_범위 = _engine_resolve('docfit_engine.page_fit', '_균등라벨_범위', globals())


단어사이_연속공백_정리_대상 = _engine_resolve('docfit_engine.page_fit', '단어사이_연속공백_정리_대상', globals())


단어사이_연속공백_정리_문단_처리 = _engine_resolve('docfit_engine.page_fit', '단어사이_연속공백_정리_문단_처리', globals())


문두_미음_기호_위치 = _engine_resolve('docfit_engine.page_fit', '문두_미음_기호_위치', globals())


문두_미음_기호_정리 = _engine_resolve('docfit_engine.page_fit', '문두_미음_기호_정리', globals())


연도_따옴표_정리_문단_처리 = _engine_resolve('docfit_engine.page_fit', '연도_따옴표_정리_문단_처리', globals())


곧은따옴표_통일_문단_처리 = _engine_resolve('docfit_engine.page_fit', '곧은따옴표_통일_문단_처리', globals())


작은따옴표_통일_문단_처리 = _engine_resolve('docfit_engine.page_fit', '작은따옴표_통일_문단_처리', globals())


날짜_구분자_정리_문단_처리 = _engine_resolve('docfit_engine.page_fit', '날짜_구분자_정리_문단_처리', globals())


공문_띄어쓰기_정리_문단_처리 = _engine_resolve('docfit_engine.page_fit', '공문_띄어쓰기_정리_문단_처리', globals())


공문_띄어쓰기_전체_적용 = _engine_resolve('docfit_engine.page_fit', '공문_띄어쓰기_전체_적용', globals())


문장내_공백_정규화_전체_적용 = _engine_resolve('docfit_engine.page_fit', '문장내_공백_정규화_전체_적용', globals())


_문장내_공백_정규화_순회 = _engine_resolve('docfit_engine.page_fit', '_문장내_공백_정규화_순회', globals())


# 이전 함수명을 호출하는 외부/기존 코드와의 호환성 유지
괄호_안쪽_공백_정리_전체_적용 = _engine_resolve('docfit_engine.page_fit', '괄호_안쪽_공백_정리_전체_적용', globals())


문장부호_뒤_공백_보정_문단_처리 = _engine_resolve('docfit_engine.page_fit', '문장부호_뒤_공백_보정_문단_처리', globals())

문장부호_뒤_공백_보정_전체_적용 = _engine_resolve('docfit_engine.page_fit', '문장부호_뒤_공백_보정_전체_적용', globals())

# 알파: 문단 글 읽기 캐시(2026-10-09). 공백 정규화는 문단마다 규칙 9개가 각자 문단 글을 다시 읽었다(읽기 1번에
# COM 호출 약 7번). 순회하는 동안 한 번 읽은 글을 같은 문단의 다음 규칙이 다시 쓰고, 규칙이 글을 고치면 비운다.
# 끄면(False) 베타와 같다.
알파_문단글_캐시_사용 = True
_문단글_캐시 = None      # None이면 캐시를 쓰지 않음, dict이면 {(리스트, 문단): (편집 세대, 글)}


# 알파 C2(2026-10-10): 문단 글 캐시를 쪽 배치 단계와 저장 결과 검사에도 켠다. 프로파일 실측(기준 파일):
# 저장 후 검수 13.3초 중 쪽 배치 최종 검사 10.1초, 그 대부분이 같은 문단 글을 묶음마다 다시 읽는 시간
# (현재문단_텍스트 1회 약 22ms). 편집하면 편집 세대가 바뀌어 다시 읽으므로 결과는 같다. 끄면(False) 베타와 같다.
알파_문단글_캐시_확대_사용 = True


문단글_캐시_구간 = _engine_resolve('docfit_engine.page_fit', '문단글_캐시_구간', globals())


_문단글_캐시_비우기 = _engine_resolve('docfit_engine.page_fit', '_문단글_캐시_비우기', globals())


# 읽은 문단 글의 글자 위치 → 한/글 커서 위치(2026-10-10, test6 시험 P1).
# 한/글 GetText는 고정폭 빈칸(fwSpace) 같은 일부 글자를 돌려주지 않는다. 읽은 글의 위치를 그대로 커서 위치로 쓰면 그런
# 글자 뒤에서 한 칸씩 밀려 엉뚱한 글자를 지웠다(실측: '구비2,241,275천원,' → '천, ,', '주민과의 대화' → '’화', '15:00' → '15.:00').
# 문단 글을 읽을 때 (문단, 글)을 기억하고, 범위 선택·커서 이동은 이 문단의 위치표로 바꿔 쓴다. 숨은 글자가 없으면
# (읽은 글 길이 = 문단 끝 위치) 그대로 쓰고, 위치표를 만들 수 없으면 고치지 않는다.
_최근_문단글 = None          # ((리스트, 문단), 글)
_문단_위치표_저장 = {}       # (리스트, 문단, 시작) → (글, 위치표 | None | '불일치')


현재문단_텍스트 = _engine_resolve('docfit_engine.page_fit', '현재문단_텍스트', globals())


_문단_위치표_계산 = _engine_resolve('docfit_engine.page_fit', '_문단_위치표_계산', globals())


문단_위치 = _engine_resolve('docfit_engine.page_fit', '문단_위치', globals())


_현재문단_텍스트_본체 = _engine_resolve('docfit_engine.page_fit', '_현재문단_텍스트_본체', globals())


_현재문단_텍스트_읽기 = _engine_resolve('docfit_engine.page_fit', '_현재문단_텍스트_읽기', globals())


_현재문단_텍스트_읽기_상태 = _engine_resolve('docfit_engine.page_fit', '_현재문단_텍스트_읽기_상태', globals())

실제_엔터_포함 = _engine_resolve('docfit_engine.page_fit', '실제_엔터_포함', globals())

두_위치_사이_줄바꿈_문자인가 = _engine_resolve('docfit_engine.page_fit', '두_위치_사이_줄바꿈_문자인가', globals())

문장부호_대상문장인가 = _engine_resolve('docfit_engine.page_fit', '문장부호_대상문장인가', globals())

현재_화면줄_텍스트 = _engine_resolve('docfit_engine.page_fit', '현재_화면줄_텍스트', globals())

문장부호_최대_처리_줄수 = 6

다음_줄_판정 = _engine_resolve('docfit_engine.page_fit', '다음_줄_판정', globals())

줄_목록_수집 = _engine_resolve('docfit_engine.page_fit', '줄_목록_수집', globals())

문장부호_줄병합_시도 = _engine_resolve('docfit_engine.page_fit', '문장부호_줄병합_시도', globals())


_문장부호_줄병합_시도_본체 = _engine_resolve('docfit_engine.page_fit', '_문장부호_줄병합_시도_본체', globals())

본문_문장부호_처리 = _engine_resolve('docfit_engine.page_fit', '본문_문장부호_처리', globals())

# ============================================================
# 표 및 컨트롤 서식
# ============================================================

현재_셀_주소_행번호 = _engine_resolve('docfit_engine.page_fit', '현재_셀_주소_행번호', globals())


현재_셀_행번호 = _engine_resolve('docfit_engine.page_fit', '현재_셀_행번호', globals())


한칸표_보호영역 = set()
디자인표_보호영역 = set()
디자인표_확인 = []   # 디자인표_보호영역 표마다 (목록 번호들, 확인할 칸 글): 번호가 밀렸는지 볼 때 쓴다

현재_한칸표인가 = _engine_resolve('docfit_engine.page_fit', '현재_한칸표인가', globals())

현재_표_키 = _engine_resolve('docfit_engine.page_fit', '현재_표_키', globals())


표칸_묶음_수집 = _engine_resolve('docfit_engine.page_fit', '표칸_묶음_수집', globals())


표칸_묶음_키별 = _engine_resolve('docfit_engine.page_fit', '표칸_묶음_키별', globals())


한칸표_영역_목록 = _engine_resolve('docfit_engine.page_fit', '한칸표_영역_목록', globals())
디자인표_영역_목록 = _engine_resolve('docfit_engine.page_fit', '디자인표_영역_목록', globals())
디자인표_보호영역_갱신 = _engine_resolve('docfit_engine.page_fit', '디자인표_보호영역_갱신', globals())
_문서에_표_있음 = _engine_resolve('docfit_engine.page_fit', '_문서에_표_있음', globals())

표_헤더서식_현재셀_처리 = _engine_resolve('docfit_engine.page_fit', '표_헤더서식_현재셀_처리', globals())


표_헤더서식_현재줄_처리 = _engine_resolve('docfit_engine.page_fit', '표_헤더서식_현재줄_처리', globals())


# 표 서식을 표 단위로 한 번에 적용할지(칸마다 적용하는 예전 방식과 결과가 같다).
표_서식_표단위_사용 = True


표_헤더서식_표단위_처리 = _engine_resolve('docfit_engine.page_fit', '표_헤더서식_표단위_처리', globals())

서식표_영역_목록 = _engine_resolve('docfit_engine.page_fit', '서식표_영역_목록', globals())


서식표_보호영역_조사 = _engine_resolve('docfit_engine.page_fit', '서식표_보호영역_조사', globals())
_서식표_칸_확인 = _engine_resolve('docfit_engine.page_fit', '_서식표_칸_확인', globals())


표_헤더서식_전체_적용 = _engine_resolve('docfit_engine.page_fit', '표_헤더서식_전체_적용', globals())


# ============================================================
# 표 구조 정밀 조정 (셀 안쪽 여백 / 열 너비 / 테두리 굵기) — 실험적 기능
#
# 이 세 기능은 표의 구조(셀 너비, 테두리)를 직접 바꾸므로, 문자 서식
# 조정보다 잘못됐을 때의 위험이 크다. 이 환경에는 한/글이 없어 실제로
# 검증할 수 없었고, PyPI의 pyhwpx·hwpapi 패키지 소스(포럼 문서 사이트는
# 이 환경에서 접근 차단됨)를 읽어 확인한 API를 근거로 구현했다. 기본값을
# 꺼둔 채(아래 *_사용 변수 참고) 제공하니, 실제 한/글에서 사본으로 먼저
# 확인한 뒤 켜서 쓰는 것을 권한다.
# ============================================================

표_셀여백_축소_사용 = False
표_셀여백_기본_mm = 1.8
표_셀여백_최소_mm = 0.0
표_셀여백_스텝_mm = 0.3

표_열너비_맞춤_사용 = False
표_열너비_허용오차_mm = 1.0

표_테두리_통일_사용 = False


표_목록_수집 = _engine_resolve('docfit_engine.page_fit', '표_목록_수집', globals())


# ---- C1. 셀 안쪽 여백 강제 축소 ------------------------------------------

셀_화면줄수 = _engine_resolve('docfit_engine.page_fit', '셀_화면줄수', globals())


셀_안쪽여백_읽기 = _engine_resolve('docfit_engine.page_fit', '셀_안쪽여백_읽기', globals())


셀_안쪽여백_현재선택 = _engine_resolve('docfit_engine.page_fit', '셀_안쪽여백_현재선택', globals())


셀_안쪽여백_축소_시도 = _engine_resolve('docfit_engine.page_fit', '셀_안쪽여백_축소_시도', globals())


_셀_안쪽여백_단계축소 = _engine_resolve('docfit_engine.formatter', '_셀_안쪽여백_단계축소', globals())


표_셀_안쪽여백_전체_적용 = _engine_resolve('docfit_engine.formatter', '표_셀_안쪽여백_전체_적용', globals())


# ---- C2. 셀 너비를 본문 여백에 맞춤 ---------------------------------------

본문_가용너비_mm = _engine_resolve('docfit_engine.formatter', '본문_가용너비_mm', globals())


표_전체너비_mm = _engine_resolve('docfit_engine.formatter', '표_전체너비_mm', globals())


현재셀_너비_mm = _engine_resolve('docfit_engine.formatter', '현재셀_너비_mm', globals())


표_열너비_순서대로_설정 = _engine_resolve('docfit_engine.formatter', '표_열너비_순서대로_설정', globals())


표_열너비_본문맞춤_시도 = _engine_resolve('docfit_engine.formatter', '표_열너비_본문맞춤_시도', globals())


표_열너비_본문맞춤_전체_적용 = _engine_resolve('docfit_engine.formatter', '표_열너비_본문맞춤_전체_적용', globals())


# ---- C3. 표 테두리 선 굵기 통일 (삼선표: 외곽 0.5mm / 헤더 이중선 /
#          내부 0.12mm / 좌우 외곽선 없음) ---------------------------------

표_셀_테두리_적용 = _engine_resolve('docfit_engine.formatter', '표_셀_테두리_적용', globals())


표_테두리_삼선표_적용 = _engine_resolve('docfit_engine.formatter', '표_테두리_삼선표_적용', globals())


표_테두리_전체_적용 = _engine_resolve('docfit_engine.formatter', '표_테두리_전체_적용', globals())


# 한 줄이 이 글자 수 이상인 표 칸은 본문과 같은 자간 한도를 쓴다(사용자 결정
# 2026-09-25). 좁은 칸은 자간을 많이 바꾸면 글자가 뭉개져 표 한도로 묶어 둔다.
넓은_표칸_기준글자수 = 20


넓은_표칸_줄인가 = _engine_resolve('docfit_engine.formatter', '넓은_표칸_줄인가', globals())


컨트롤_내부_자간조정 = _engine_resolve('docfit_engine.spacing', '컨트롤_내부_자간조정', globals())

한칸표_자간조정 = _engine_resolve('docfit_engine.spacing', '한칸표_자간조정', globals())


컨트롤_내부_문장부호_처리 = _engine_resolve('docfit_engine.formatter', '컨트롤_내부_문장부호_처리', globals())

끝위치추출 = _engine_resolve('docfit_engine.formatter', '끝위치추출', globals())

다음_문단으로_진행 = _engine_resolve('docfit_engine.formatter', '다음_문단으로_진행', globals())

# ------------------------------------------------------------
# 쪽 범위 / 표 안 문장 제외 도우미
# ------------------------------------------------------------

쪽표시 = _engine_resolve('docfit_engine.formatter', '쪽표시', globals())

# 절약 시간 추정(수작업 기준). 작업 종류별로 한 쪽을 손으로 정리할 때 걸리는 분(分)이다.
# 처리한 쪽 수 × 이 값 − 실제 걸린 시간 = 화면에 보여 주는 '절약된 시간'이다. 추정치를 바꾸려면 이 값을 고친다.
절약시간_쪽당_분 = {"spacing": 4.0, "unify": 2.0, "format": 5.0, "all": 8.0}

절약시간_표시 = _engine_resolve('docfit_engine.formatter', '절약시간_표시', globals())

절약시간_분초_표시 = _engine_resolve('docfit_engine.formatter', '절약시간_분초_표시', globals())


번들_고양이_그림_찾기 = _engine_resolve('docfit_engine.formatter', '번들_고양이_그림_찾기', globals())


번들_앱아이콘_찾기 = _engine_resolve('docfit_engine.formatter', '번들_앱아이콘_찾기', globals())


_앱아이콘_적용 = _engine_resolve('docfit_engine.formatter', '_앱아이콘_적용', globals())


처리_쪽수_구하기 = _engine_resolve('docfit_engine.formatter', '처리_쪽수_구하기', globals())

쪽범위_사용중 = _engine_resolve('docfit_engine.formatter', '쪽범위_사용중', globals())

쪽범위_안인가 = _engine_resolve('docfit_engine.formatter', '쪽범위_안인가', globals())

쪽범위_끝지남 = _engine_resolve('docfit_engine.formatter', '쪽범위_끝지남', globals())

순회_시작 = _engine_resolve('docfit_engine.formatter', '순회_시작', globals())

범위_다음_문단으로_진행 = _engine_resolve('docfit_engine.formatter', '범위_다음_문단으로_진행', globals())

현재_표셀인가 = _engine_resolve('docfit_engine.formatter', '현재_표셀인가', globals())

# 숫자·기호만으로 된 표 칸(통계표의 수치 칸 등)은 어절이 없어 자간·단어 분리
# 조정할 것이 없다. 실측: 수출입동향(통계표 위주) 문서에서 자간 초기화만
# 32분이 걸렸다(사용자 요청 2026-09-25: 숫자만으로 된 표는 건너뜀).
_숫자칸_패턴 = re.compile(r"[\s0-9０-９,，.．%％+\-－−–△▲▼▽↑↓()（）~∼'‘’/:×·]*")


숫자_표칸인가 = _engine_resolve('docfit_engine.formatter', '숫자_표칸인가', globals())


표셀_자간_제외인가 = _engine_resolve('docfit_engine.spacing', '표셀_자간_제외인가', globals())

컨트롤_줄병합_대상인가 = _engine_resolve('docfit_engine.spacing', '컨트롤_줄병합_대상인가', globals())

쪽범위_계산 = _engine_resolve('docfit_engine.pipeline', '쪽범위_계산', globals())

저장파일명 = _engine_resolve('docfit_engine.formatter', '저장파일명', globals())

# ============================================================
# 문서 처리 파이프라인
# ============================================================

선택_세부작업 = {}
작업_반복횟수 = 1


# 보고서 표준서식(항목기호별 서식 등)을 준말 변환 바로 다음, 다른 모든 단계보다 먼저 입힐지.
# 작업_실행이 서식 적용·한 번에 적용에서 서식 옵션을 켰을 때 채운다(서식 통일은 표준서식을 쓰지 않는다).
표준서식_선행_사용 = False


표준서식_선행_적용 = _engine_resolve('docfit_engine.formatter', '표준서식_선행_적용', globals())


문서_처리_1회 = _engine_resolve('docfit_engine.pipeline', '문서_처리_1회', globals())


_문서_처리_1회 = _engine_resolve('docfit_engine.pipeline', '_문서_처리_1회', globals())


문서_전체_자간_초기화 = _engine_resolve('docfit_engine.spacing', '문서_전체_자간_초기화', globals())


지원_확장자 = (".hwp", ".hwpx", ".txt", ".md", ".doc", ".docx", ".pdf",
              ".hml", ".xls", ".xlsx", ".pptx", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif")


바이너리_HWP_파일인가 = _engine_resolve('docfit_engine.formatter', '바이너리_HWP_파일인가', globals())


_텍스트_인코딩_후보 = ("utf-8-sig", "utf-8", "cp949")


텍스트파일_읽기 = _engine_resolve('docfit_engine.formatter', '텍스트파일_읽기', globals())


텍스트_hwpx로_변환 = _engine_resolve('docfit_engine.formatter', '텍스트_hwpx로_변환', globals())


라벨블록_한글삽입 = _engine_resolve('docfit_engine.formatter', '라벨블록_한글삽입', globals())


# '서식 예시 확인'(2026-10-04 사용자 요청)에 쓰는 예시 보고서 글. 준말 줄(제목1:·개요:·로1:·붙임:)은 서식 적용의
# 준말 단계가 서식 표로, 박스 그림 표는 텍스트 표 변환 단계가 실제 표로 바꾸므로 서식의 모든 부분이 한 문서에 드러난다.
# 서식 예시 확인용 가상 보고서(사용자가 준 삼채인.txt 내용을 참고해 지음, 2026-10-04).
서식예시_글 = "\n".join([
    # 쉼표 앞 '삼체 문명 존속을 위한'은 부제(제목 서식의 부제 크기로 줄여 윗줄에 놓는다).
    "제목1: 삼체 문명 존속을 위한, 지구 이주 계획(안) 보고",
    "개요: 삼체 행성의 항성계 불안정으로 문명 파괴가 반복됨에 따라, 새로운 거점(지구) 확보를 위한 「기초과학 봉쇄 → 함대 항행 → 이주」 3단계 전략을 마련하여 보고드림",
    "로1: 추진 배경",
    "□ 항성계 불안정에 따른 문명 존속 위기 심화",
    " ㅇ (현황) 3개 항성의 불규칙 운동으로 혹독한 환경이 되풀이됨",
    "  - 문명이 주기적으로 파괴되어 재건 비용이 계속 누적됨",
    # *·** 주석은 위첨자 *·**가 붙은 바로 앞 문장의 낱말(항세기·난세기)을 풀이한다.
    "  - 항세기*와 난세기**가 예측 없이 교차하여 문명 파괴가 반복됨",
    "   * 항세기: 기후가 안정된 시기",
    "   ** 난세기: 극단적 기후가 발생하는 시기",
    " ㅇ (지구 확인) 인류가 보낸 전파를 수신해 안정된 항성계와 액체 상태 물의 존재를 확인",
    "□ 지구 현황 분석",
    " ㅇ (환경) 단일 항성 중심으로 안정된 기후가 지속되어 이주에 적합함",
    " ㅇ (위험요인) 인류의 기술 도약 가능성과 내부 저항 세력이 존재함",
    "  ※ 인류는 사고가 밖으로 드러나지 않아 전략적 기만이 가능하므로 별도 대응 체계 필요",
    "로2: 추진 계획",
    "□ 단계별 추진 일정",
    " ㅇ (1단계) 지자 투입으로 지구를 감시하고 기초과학 발전을 봉쇄",
    "  - 입자가속기 실험을 교란하여 물리학 진보를 차단",
    " ㅇ (2단계) 함대 발진 및 항행(지구 도착까지 약 450년 소요 예상)",
    " ㅇ (3단계) 지구 도착 후 저항 세력을 무력화하고 이주를 실행",
    "┌──────┬──────────────┬──────┐",
    "│ 구분 │ 추진 내용 │ 시기 │",
    "├──────┼──────────────┼──────┤",
    "│ 1단계 │ 지자 투입 및 기초과학 봉쇄 │ 즉시 │",
    "│ 2단계 │ 함대 발진 및 항행 │ 1년 이내 │",
    "│ 3단계 │ 지구 도착 및 이주 │ 약 450년 뒤 │",
    "└──────┴──────────────┴──────┘",
    "□ 향후 계획",
    " ㅇ 지자 제조 공정에 즉시 착수하고 제1함대 편제를 확정",
    "로3: 소요예산",
    "□ 총 소요: 미네랄 52만 단위, 베스핀 가스 18만 단위(’26~’30년)",
    " ㅇ (지자 제조) 양성자 전개·회로 각인 설비 구축에 미네랄 7만, 가스 3만 단위",
    " ㅇ (함대 건설) 함선 1,000척 건조에 미네랄 40만, 가스 13만 단위",
    "  - 함선 1척당 미네랄 400, 가스 130 단위 소요(시험 건조 실적 기준)",
    " ㅇ (지구 협력 지원) 지구삼체조직 활동 지원에 미네랄 5만, 가스 2만 단위",
    "  ※ 가스 채취량이 계획에 못 미치면 함대 건조 일정을 조정",
    "┌──────┬──────┬──────┐",
    "│ 구분 │ 미네랄 │ 베스핀 가스 │",
    "├──────┼──────┼──────┤",
    "│ 지자 제조 │ 7만 │ 3만 │",
    "│ 함대 건설 │ 40만 │ 13만 │",
    "│ 지구 협력 지원 │ 5만 │ 2만 │",
    "│ 합계 │ 52만 │ 18만 │",
    "└──────┴──────┴──────┘",
    "로4: 행정사항",
    "□ 난세기 대비 탈수 준비",
    " ㅇ 난세기 예보 시 전 주민을 탈수하여 건조 보관고에 보관하고, 항세기가 오면 일괄 침수 복원",
    "  - 보관고를 정기 점검하고 탈수체 훼손 방지 대책을 마련",
    "□ 함대 건설을 위한 광물 채취",
    " ㅇ 항세기 동안 광산 가동을 최대로 늘려 미네랄·가스를 비축",
    " ㅇ 채취 실적은 매월 원수에게 보고하고 부족분은 다음 항세기에 보충",
    "□ 지구 내 삼체 추종 조직 지원",
    " ㅇ 지자를 통해 지구삼체조직(ETO)에 행동 지침을 내리고 활동 자원을 지원",
    "  - 강림파*·구원파** 등 분파 간 이견은 지침으로 조정",
    "   * 강림파: 인류 문명의 파멸을 바라는 분파",
    "   ** 구원파: 삼체 세계를 구원하려는 분파",
    "붙임: 지구 이주 세부 시행계획 1부.  끝.",
])


# 알파(2026-10-12): 챗GPT·클로드·제미나이 답변을 복사한 그대로(마크다운 기호·번호 표제·글머리·표) 붙여넣거나 .txt로 저장해도
# 항목기호(□ ㅇ - •) 개조식 문서로 바꿔 서식 적용이 되게 한다. 끄면 글을 그대로 넣는다. docfit_core/ai_answer.py
알파_AI답변변환_사용 = True


AI답변_개조식_변환 = _engine_resolve('docfit_engine.formatter', 'AI답변_개조식_변환', globals())


텍스트_hwpx_단독변환 = _engine_resolve('docfit_engine.formatter', '텍스트_hwpx_단독변환', globals())


외부문서_hwpx로_변환 = _engine_resolve('docfit_engine.formatter', '외부문서_hwpx로_변환', globals())


# 알파(2026-10-10): kordoc은 PDF를 마크다운으로 바꿔 프리셋 서식으로 HWPX를 만들어 원본 서식이 사라진다.
# PDF 글자마다 글꼴·크기·굵게·글자색·장평·배경색을 읽어 변환 HWPX에 다시 적용한다(docfit_core.pdf_style_transfer).
# 실측(재경부 업무보고 PDF 17쪽): 짝지은 글자 기준 글꼴 0.3→99.9%, 크기 41→100%, 색 글자 0→100%, 배경색 1.1→100%.
알파_PDF서식이식_사용 = True


PDF_서식_이식 = _engine_resolve('docfit_engine.formatter', 'PDF_서식_이식', globals())


_박스그림표_한글표_삽입 = _engine_resolve('docfit_engine.formatter', '_박스그림표_한글표_삽입', globals())


# 선 문자 표의 줄은 테두리·칸 구분 문자로 시작한다. 정상 글을 지우지 않도록 '선 문자로 시작하는 줄'만 잔여물로 본다.
_박스그림_줄시작 = re.compile(r'^\s*[┌├└│┃┏┣┗]')


_박스그림_줄인가 = _engine_resolve('docfit_engine.formatter', '_박스그림_줄인가', globals())


_박스그림_남은_문단 = _engine_resolve('docfit_engine.formatter', '_박스그림_남은_문단', globals())


_박스그림표_교체 = _engine_resolve('docfit_engine.formatter', '_박스그림표_교체', globals())


박스그림_전체_적용 = _engine_resolve('docfit_engine.formatter', '박스그림_전체_적용', globals())


저장결과_규칙검수 = _engine_resolve('docfit_engine.formatter', '저장결과_규칙검수', globals())


문서_처리 = _engine_resolve('docfit_engine.pipeline', '문서_처리', globals())


_문서_처리_본체 = _engine_resolve('docfit_engine.pipeline', '_문서_처리_본체', globals())

# ============================================================
# 백그라운드 작업 실행 스레드
# ============================================================

절전_방지 = _engine_resolve('docfit_engine.pipeline', '절전_방지', globals())


작업_실행 = _engine_resolve('docfit_engine.pipeline', '작업_실행', globals())

# Tk fallback palette. Keep the keys aligned with the WebView2 UI's neutral
# surfaces and single blue primary action so startup also works without WebView2.
UI_COLORS = {
    "bg": "#F5F6F8",
    "surface": "#FFFFFF",
    "ink": "#191F28",
    "muted": "#6B7684",
    "separator": "#E5E8EB",
    "teal": "#3182F6",
    "teal_dark": "#1B64DA",
    "teal_tint": "#E8F3FF",
    "rose": "#F2F4F6",
    "lavender": "#DCEBFF",
    "success": "#16875D",
}


색_rgb = _engine_resolve('docfit_ui.legacy', '색_rgb', globals())


LiveStageBoard = _engine_resolve('docfit_ui.legacy', 'LiveStageBoard', globals())


HwpAutoDocFitGUI = _engine_resolve('docfit_ui.legacy', 'HwpAutoDocFitGUI', globals())

# ============================================================
# Main 실행부
# ============================================================

_새창_맨앞으로 = _engine_resolve('docfit_ui.legacy', '_새창_맨앞으로', globals())


웹모드_기본창_숨김 = _engine_resolve('docfit_ui.legacy', '웹모드_기본창_숨김', globals())


웹모드_기본창_복원 = _engine_resolve('docfit_ui.legacy', '웹모드_기본창_복원', globals())


_APP_MUTEX_HANDLE = None


def _닫기_스플래시():
    try:
        import pyi_splash
        if pyi_splash.is_alive():
            pyi_splash.close()
    except Exception:
        pass


def _단일_인스턴스_확인():
    """앱이 이미 실행 중인지 Windows Named Mutex로 확인하고 기존 창을 활성화한다."""
    global _APP_MUTEX_HANDLE
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        ERROR_ALREADY_EXISTS = 183

        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.GetLastError.restype = wintypes.DWORD
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowTextW.restype = ctypes.c_int
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
        user32.EnumWindows.restype = wintypes.BOOL

        launcher_mutex_name = os.environ.get("DOCFIT_LAUNCHER_MUTEX_NAME", "")
        mutex_name = launcher_mutex_name or "Global\\HWP_AutoDocFit_SingleInstance_Mutex"
        handle = kernel32.CreateMutexW(None, True, mutex_name)
        if not handle:
            # Global 네임스페이스 접근 제한 시 Local 네임스페이스로 폴백
            mutex_name = launcher_mutex_name or "Local\\HWP_AutoDocFit_SingleInstance_Mutex"
            handle = kernel32.CreateMutexW(None, True, mutex_name)

        last_error = kernel32.GetLastError()
        handoff_event = os.environ.pop("DOCFIT_LAUNCHER_HANDOFF_EVENT", "")
        if handle and last_error == ERROR_ALREADY_EXISTS and handoff_event:
            kernel32.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
            kernel32.OpenEventW.restype = wintypes.HANDLE
            kernel32.SetEvent.argtypes = [wintypes.HANDLE]
            kernel32.SetEvent.restype = wintypes.BOOL
            kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel32.WaitForSingleObject.restype = wintypes.DWORD
            event_handle = kernel32.OpenEventW(0x0002, False, handoff_event)  # EVENT_MODIFY_STATE
            if not event_handle or not kernel32.SetEvent(event_handle):
                if event_handle:
                    kernel32.CloseHandle(event_handle)
                kernel32.CloseHandle(handle)
                return False
            kernel32.CloseHandle(event_handle)
            wait_result = kernel32.WaitForSingleObject(handle, 45000)
            if wait_result in (0x00000000, 0x00000080):  # WAIT_OBJECT_0 / WAIT_ABANDONED
                _APP_MUTEX_HANDLE = handle
                return True
            kernel32.CloseHandle(handle)
            return False
        if handle and last_error == ERROR_ALREADY_EXISTS:
            from docfit_app.instance_files import forward
            try:
                forward(sys.argv[1:])
            except OSError:
                pass
            _닫기_스플래시()
            # 이미 실행 중인 창을 찾아 앞으로 가져오기
            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

            def enum_cb(hwnd, _lparam):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        text = buff.value
                        if APP_NAME in text or "한글편집" in text:
                            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                            user32.SetForegroundWindow(hwnd)
                            return False
                return True

            try:
                user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
            except Exception:
                pass
            if handle:
                kernel32.CloseHandle(handle)
            return False

        _APP_MUTEX_HANDLE = handle
        return True
    except Exception:
        _닫기_스플래시()
        return True


def main():
    from docfit_app.cli import is_cli_command, main as cli_main
    if is_cli_command(sys.argv[1:]):
        raise SystemExit(cli_main())
    import importlib.util

    if not _단일_인스턴스_확인():
        return

    try:
        from docfit_app.shell_menu import refresh_registered
        refresh_registered()
    except OSError:
        pass

    if getattr(_selftest_sys, "frozen", False):
        def _배경_런타임_배포():
            try:
                from docfit_core.kordoc_runtime import deploy_embedded_runtime
                from docfit_core.kordoc_bridge import KORDOC_VERSION
                deploy_embedded_runtime(KORDOC_VERSION)
            except Exception:
                pass

        threading.Thread(target=_배경_런타임_배포, name="kordoc-deploy", daemon=True).start()

    # WebView2가 있으면 반응형 웹 화면을 주 UI로 사용하고, 문서 처리·설정 창은
    # 기존 Tk 백엔드에 연결한다. WebView 초기화 문제 진단·복구 시 환경변수로
    # 기존 화면을 선택할 수 있고, 연결 패키지가 없을 때도 Tk 화면으로 돌아간다.
    tk_only = os.environ.get("HWP_AUTODOCFIT_UI", "").strip().lower() == "tk"
    if tk_only or importlib.util.find_spec("webview") is None:
        _닫기_스플래시()
        root = TkinterDnD.Tk()
        _앱아이콘_적용(root)
        gui = HwpAutoDocFitGUI(root)
        from docfit_app.instance_files import start
        start(gui)
        _새창_맨앞으로(root)
        root.mainloop()
        return

    준비됨 = threading.Event()
    보관 = {}

    def tk_실행():
        try:
            root = TkinterDnD.Tk()
            _앱아이콘_적용(root)
            gui = HwpAutoDocFitGUI(root)
            from docfit_app.instance_files import start
            start(gui)
            웹모드_기본창_숨김(root)
            보관.update(root=root, gui=gui)
            준비됨.set()
            root.mainloop()
        except BaseException as 오류:
            보관["오류"] = 오류
            준비됨.set()

    tk_thread = threading.Thread(target=tk_실행, name="hwp-tk-event-loop", daemon=True)
    tk_thread.start()
    if not 준비됨.wait(30):
        _닫기_스플래시()
        raise RuntimeError("앱 인터페이스를 시작하지 못했습니다.")
    if "오류" in 보관:
        _닫기_스플래시()
        raise RuntimeError("앱 인터페이스를 시작하지 못했습니다.") from 보관["오류"]

    try:
        import desktop_web_ui

        desktop_web_ui.APP_NAME = APP_NAME
        desktop_web_ui.APP_VERSION = APP_VERSION
        desktop_web_ui.STAGE_ORDER = 진행단계_순서
        desktop_web_ui.APP_ICON = str(번들_앱아이콘_찾기() or "")
        if not desktop_web_ui.run_webview(보관["gui"]):
            _닫기_스플래시()
            보관["root"].after(0, lambda: 웹모드_기본창_복원(보관["root"]))
            tk_thread.join()
    except Exception as 오류:
        _닫기_스플래시()
        def 기존화면_안내(시작오류):
            messagebox.showwarning(
                APP_NAME,
                "웹 화면을 시작하지 못해 기존 화면으로 전환합니다.\n\n"
                f"{시작오류}",
                parent=보관["root"],
            )
            웹모드_기본창_복원(보관["root"])

        try:
            보관["root"].after(0, lambda 시작오류=오류: 기존화면_안내(시작오류))
            tk_thread.join()
        except Exception:
            raise

if __name__ == "__main__":
    if "--self-test" in _selftest_sys.argv:
        raise SystemExit(_packaging_finish(_packaging_result, globals()))
    main()
