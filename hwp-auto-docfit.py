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
from docfit_core.table_style import HeaderPool as 표서식_저장소, apply_table_style as 표서식_적용, describe_style as 표서식_설명, is_grid_table as 표서식_모양인가
from docfit_core.table_style import learn_from_table as 표서식_한표학습, valid_style as 표서식_유효
from docfit_core.text_table import find_box_tables
from docfit_core import writing_aids, ai_prompts
from docfit_core.writing_aids import refresh_dates as 날짜_현행화


def XML_네임스페이스_등록(prefix, uri):
    """defusedxml 파서는 유지하면서 ElementTree 직렬화 접두사만 등록한다.

    defusedxml.ElementTree는 안전 파싱 API로 적합하지만 register_namespace를
    노출하지 않는다. tostring이 사용하는 직렬화 네임스페이스 레지스트리에만
    등록하며, 입력 XML 파싱은 계속 defusedxml 경로를 사용한다.
    """
    register = getattr(ET, "register_namespace", None)
    if callable(register):
        register(prefix, uri)
        return True
    registry = getattr(ET.tostring, "__globals__", {}).get("_namespace_map")
    if not isinstance(registry, dict):
        # 접두사 이름은 XML 의미에 영향을 주지 않는다. 레지스트리를 제공하지
        # 않는 구현에서는 serializer가 ns0/ns1 접두사를 안전하게 생성하게 둔다.
        return False
    for existing_uri, existing_prefix in list(registry.items()):
        if existing_uri == uri or existing_prefix == prefix:
            del registry[existing_uri]
    registry[uri] = prefix
    return True


def XML_요소_생성(prototype, tag=None, attrib=None):
    """defusedxml이 생성자 API를 노출하지 않을 때 파싱 요소 타입으로 새 노드를 만든다."""
    if prototype is None:
        raise ValueError('새 XML 요소를 만들 프로토타입이 없습니다.')
    return type(prototype)(tag if tag is not None else prototype.tag,
                           {} if attrib is None else dict(attrib))


def XML_자식_추가(parent, prototype, tag=None, attrib=None):
    """안전 파싱 결과와 같은 요소 타입으로 자식 노드를 생성해 추가한다."""
    child = XML_요소_생성(prototype, tag=tag, attrib=attrib)
    parent.append(child)
    return child
from docfit_core.style_inventory import analyze_style_inventory, build_style_sample, inventory_markdown
from docfit_core import report_header as 보고서머리
from docfit_core import format_elements as 서식요소
from docfit_core.table_width import fit_table as 표너비_맞춤, is_target as 표너비_대상인가
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
)

# ============================================================
# 프로그램 정보
# ============================================================

APP_NAME = "한글편집 후처리"
APP_VERSION = "1.73 Alpha 1"
PROJECT_URL = "https://gitlab.aigov.go.kr/haijun93/hwp_autodocfit"
UPDATE_API_URL = "https://gitlab.aigov.go.kr/api/v4/projects/haijun93%2Fhwp_autodocfit/releases/permalink/latest"
GITHUB_UPDATE_API_URL = "https://api.github.com/repos/haijun93/hwp-auto-docfit/releases/latest"
UPDATE_ASSET_NAME = "HWP_AutoDocFit.exe"
_업데이트_허용_호스트 = "gitlab.aigov.go.kr"
# GitHub 릴리스 파일은 github.com에서 githubusercontent.com 계열 주소로 넘어간다(리디렉션).
_업데이트_허용_호스트들 = (_업데이트_허용_호스트, "api.github.com", "github.com")
_업데이트_허용_호스트_접미사 = (".githubusercontent.com",)


def _업데이트_URL_검증(url):
    """업데이트 조회·다운로드 URL을 HTTPS GitLab·GitHub 주소로 제한한다."""
    parsed = urllib.parse.urlparse(str(url))
    호스트 = (parsed.hostname or "").lower()
    허용 = 호스트 in _업데이트_허용_호스트들 or any(
        호스트.endswith(접미사) for 접미사 in _업데이트_허용_호스트_접미사
    )
    if parsed.scheme != "https" or not 허용:
        raise ValueError("허용되지 않은 업데이트 URL입니다.")
    return str(url)


def _업데이트_HTTP_GET(url, headers, timeout, _남은_리디렉션=5):
    """검증된 GitLab·GitHub HTTPS URL만 직접 HTTPS 연결로 조회한다(리디렉션도 매번 검증)."""
    parsed = urllib.parse.urlparse(_업데이트_URL_검증(url))
    연결 = http.client.HTTPSConnection(  # nosemgrep
        parsed.hostname, parsed.port or 443, timeout=timeout,
        context=ssl.create_default_context(),
    )
    연결.request("GET", parsed.path + (f"?{parsed.query}" if parsed.query else ""), headers=headers)
    응답 = 연결.getresponse()
    if 응답.status in (301, 302, 303, 307, 308) and 응답.getheader("Location"):
        다음 = urllib.parse.urljoin(str(url), 응답.getheader("Location"))
        응답.read()
        연결.close()
        if _남은_리디렉션 <= 0:
            raise RuntimeError("업데이트 주소의 리디렉션이 너무 많습니다.")
        return _업데이트_HTTP_GET(다음, headers, timeout, _남은_리디렉션 - 1)
    if 응답.status >= 400:
        상태 = 응답.status
        응답.read()
        연결.close()
        raise urllib.error.HTTPError(url, 상태, 응답.reason, 응답.headers, None)
    응답._docfit_connection = 연결
    return 응답


def _업데이트_기록(내용):
    """업데이트 과정을 설정 폴더의 updates\\update.log에 남긴다(실패해도 무시)."""
    try:
        폴더 = 설정_폴더() / "updates"
        폴더.mkdir(parents=True, exist_ok=True)
        with open(폴더 / "update.log", "a", encoding="utf-8") as f:
            f.write(f"{_datetime.datetime.now():%Y-%m-%d %H:%M:%S} [{APP_VERSION}] {내용}\n")
    except Exception:
        pass


UPDATE_STARTED_FLAG = "app_started.flag"   # 새 버전이 켜졌다는 신호(교체 스크립트가 확인 뒤 백업을 지운다)
UPDATE_BUSY_FLAG = "update_busy.flag"      # 교체 스크립트가 도는 중(이때는 시작 정리가 백업을 지우지 않는다)


def 업데이트_시작신호():
    """실행 파일로 켜졌음을 교체 스크립트에 알린다(Beta 12 리뷰 R5)."""
    try:
        폴더 = 설정_폴더() / "updates"
        폴더.mkdir(parents=True, exist_ok=True)
        (폴더 / UPDATE_STARTED_FLAG).write_text(f"{APP_VERSION} {os.getpid()}", encoding="utf-8")
    except Exception:
        pass


def 업데이트_잔여정리():
    """지난 업데이트가 남긴 구버전 백업('*.exe.old')과 내려받기 잔여물을 지운다(실행 중이면 다음에 다시 시도)."""
    try:
        실행폴더 = Path(sys.executable).resolve().parent
        업데이트_폴더 = 설정_폴더() / "updates"
        if (업데이트_폴더 / UPDATE_BUSY_FLAG).exists():
            return      # 교체 스크립트가 시작 확인을 기다리는 중: 구버전 백업을 지우면 되살릴 수 없다
        이름들 = [x.name for x in 실행폴더.iterdir()] if 실행폴더.is_dir() else []
        업데이트_이름들 = [x.name for x in 업데이트_폴더.iterdir()] if 업데이트_폴더.is_dir() else []
        old, stale = 업데이트_잔여파일(이름들, 업데이트_이름들)
        지운 = 0
        for 경로 in [실행폴더 / n for n in old] + [업데이트_폴더 / n for n in stale]:
            try:
                경로.unlink()
                지운 += 1
            except OSError:
                pass
        if 지운:
            _업데이트_기록(f"지난 업데이트 잔여물 {지운}개 정리")
    except Exception:
        pass


def _버전_튜플(value):
    숫자 = [int(item) for item in re.findall(r"\d+", str(value))]
    return tuple((숫자 + [0, 0, 0])[:3])


def _최신_릴리스_조회(timeout=8, api_url=None):
    try:
        응답 = _업데이트_HTTP_GET(api_url or UPDATE_API_URL, {
            "Accept": "application/json",
            "User-Agent": f"HWP-AutoDocFit/{APP_VERSION}",
        }, timeout)
        try:
            릴리스 = json.loads(응답.read().decode("utf-8"))
        finally:
            응답._docfit_connection.close()
    except urllib.error.HTTPError as exc:
        # GitLab은 프로젝트에 Release가 하나도 없으면 latest API에서 404를 반환한다.
        # 이는 통신 오류가 아니라 아직 배포된 업데이트가 없다는 뜻이다.
        if exc.code == 404:
            return None
        raise
    if not isinstance(릴리스, dict):
        raise ValueError(f"릴리스 응답 형식이 올바르지 않습니다({type(릴리스).__name__}): {str(릴리스)[:80]}")
    # GitLab은 assets가 {"links": [...]} 형태의 dict이고, GitHub 형식은 목록이다. 둘 다 받는다.
    자산정보 = 릴리스.get("assets")
    if isinstance(자산정보, dict):
        링크들 = 자산정보.get("links") or []
    elif isinstance(자산정보, list):
        링크들 = 자산정보
    else:
        링크들 = []
    릴리스["assets"] = [
        {
            **링크,
            "browser_download_url": (
                링크.get("direct_asset_url") or 링크.get("browser_download_url") or 링크.get("url")
            ),
        }
        for 링크 in 링크들 if isinstance(링크, dict)
    ]
    return 릴리스


def _최신_릴리스_통합_조회(timeout=8):
    """GitLab과 GitHub를 모두 조회해 가장 높은 버전의 릴리스를 돌려준다.

    한쪽만 실패하면 다른 쪽 결과를 쓰고, 둘 다 실패하면 오류를 낸다.
    버전이 같으면 GitLab(사내 배포선)을 우선한다.
    """
    원본들 = (("GitLab", UPDATE_API_URL), ("GitHub", GITHUB_UPDATE_API_URL))
    결과들, 오류들 = [], []
    for 이름, 주소 in 원본들:
        try:
            릴리스 = _최신_릴리스_조회(timeout, api_url=주소)
        except Exception as exc:
            오류들.append(f"{이름}: {exc}")
            continue
        if 릴리스:
            릴리스["update_source"] = 이름
            결과들.append(릴리스)
    if not 결과들:
        if 오류들 and len(오류들) == len(원본들):
            raise RuntimeError(" / ".join(오류들))
        return None
    최신 = 결과들[0]
    for 후보 in 결과들[1:]:
        if _버전_튜플(후보.get("tag_name") or 후보.get("name")) > _버전_튜플(최신.get("tag_name") or 최신.get("name")):
            최신 = 후보
    return 최신


def _업데이트_자산_선택(릴리스):
    자산들 = [item for item in 릴리스.get("assets", []) if str(item.get("name", "")).lower().endswith(".exe")]
    for 자산 in 자산들:
        if str(자산.get("name", "")).lower() == UPDATE_ASSET_NAME.lower():
            return 자산
    return 자산들[0] if len(자산들) == 1 else None

# ============================================================
# AutomationModule
# ============================================================

DLL_NAME = "MapoHwpAutoDocFitSecurity.dll"
HWP_AUTOMATION_DIR = Path(r"C:\HwpAutomation")
TARGET_DLL = HWP_AUTOMATION_DIR / DLL_NAME
REGISTRY_PATH = r"Software\HNC\HwpAutomation\Modules"
# 한/글은 RegisterModule의 두 번째 인자와
# ...\HwpAutomation\Modules 아래 레지스트리 값 이름이 같아야 한다.
# 공용 예제 이름 대신 이 프로젝트 전용 이름을 사용한다.
REGISTRY_VALUE_NAME = "MapoHwpAutoDocFitSecurity"
REGISTER_MODULE_NAME = "FilePathCheckDLL"
REGISTER_MODULE_VALUE = REGISTRY_VALUE_NAME


def 한글_COM_인스턴스_생성(독립=True):
    """한컴오피스/한글의 공통 COM ProgID로 자동화 객체를 만든다.

    DispatchEx는 작업 문서가 사용자의 기존 편집 세션에 섞이지 않게 우선 사용한다.
    일부 구형 한컴오피스 등록 상태에서 DispatchEx가 실패할 때만 Dispatch로 재시도한다.
    """
    prog_id = "HwpFrame.HwpObject"
    오류들 = []
    생성기들 = (win32.DispatchEx, win32.Dispatch) if 독립 else (win32.Dispatch,)
    for 생성기 in 생성기들:
        try:
            return 생성기(prog_id)
        except Exception as 오류:
            오류들.append(f"{getattr(생성기, '__name__', 'COM 생성기')}: {오류}")
    설명 = " | ".join(오류들)
    raise RuntimeError(
        "한컴오피스 한글 자동화 객체를 만들지 못했습니다. "
        "한글(NEO/2020 이상) 설치와 HwpFrame.HwpObject COM 등록을 확인해 주세요. "
        f"세부 오류: {설명}"
    )


def 한글_문서_열기(app, 경로, 형식, 옵션=""):
    """한글 버전별 pywin32 인자 바인딩 차이를 흡수해 문서를 연다."""
    try:
        # NEO와 2020 모두에서 가장 일관되게 동작하는 positional COM 호출을 우선한다.
        return app.Open(str(경로), str(형식), str(옵션))
    except TypeError as 위치인자오류:
        try:
            # 일부 generated/early-bound wrapper는 이름 있는 인자만 노출한다.
            return app.Open(str(경로), Format=str(형식), arg=str(옵션))
        except Exception as 이름인자오류:
            raise RuntimeError(
                f"한글 문서 열기 호출에 실패했습니다 ({형식}): "
                f"위치 인자 오류={위치인자오류}; 이름 인자 오류={이름인자오류}"
            ) from 이름인자오류

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

def _표준서식_문단위간격_표():
    return {"chapter": 표준서식_문단위간격_chapter_pt,
            "midtitle": 표준서식_문단위간격_midtitle_pt,
            "box": 표준서식_문단위간격_box_pt,
            "circle": 표준서식_문단위간격_circle_pt,
            "dash": 표준서식_문단위간격_dash_pt,
            "note": 표준서식_문단위간격_note_pt}


def 기본_계층_스타일(fmt):
    """분석한 문서가 없는 서식(기본 보고서 서식)의 '계층별 문서 스타일 검토' 행.

    1 제목 · 2 장 · 3 중제목(로마자) · 4~6 □·ㅇ·- · 부연설명 순서다. 문단 위 여백은 서식이 복사한 값이 있으면
    그 값, 없으면 계층별 문단 위 여백 설정값(pt)을 쓴다(2026-10-05: 장·중제목 행과 여백 값이 빠져 있었다).
    """
    복사 = fmt.get("복사_문단모양", {}) or {}
    장 = fmt.get("장_규칙") or _표준서식_설정_기본값["장_규칙"]
    간격 = _표준서식_문단위간격_표()
    행들 = [("제목", "(없음)", fmt["제목_문단"]["font"], fmt["제목_문단"]["size_pt"], None),
           ("장", 장[0], 장[2], 장[3], "chapter"),
           # 중제목 기준 서식은 내장 중제목 표(번호·글 HY견고딕 20pt)다.
           ("중제목", "Ⅰ", "HY견고딕", 20, "midtitle")]
    for rule in fmt["기호_규칙"]:
        marker = str(rule[0])
        role = leading_marker(marker + " 항목")[1] or "미분류"
        행들.append((role, marker, rule[2], rule[3], paragraph_level(marker + " 항목")))
    결과 = []
    for role, marker, font, size, 계층 in 행들:
        모양 = 복사.get(marker, {})
        if "PrevSpacing" in 모양:
            위여백 = 모양["PrevSpacing"]
        else:
            위여백 = int(round(float(간격.get(계층) or 0) * 100)) if 계층 else 0
        결과.append({"role": role, "marker": marker, "count": 1, "kind": "기본값",
                   "font": font, "size_pt": size,
                   "left_hwpunit": 모양.get("LeftMargin", 0),
                   "first_line_hwpunit": 모양.get("Indentation", 0),
                   "prev_spacing_hwpunit": 위여백})
    return 결과


def 표준서식_문단위간격_찾기(text, 계층=None):
    """문단 위 간격(pt). 계층을 주면 글 대신 그 계층으로 정한다(표 첫 칸 로마자 중제목 표)."""
    if 계층:
        return _표준서식_문단위간격_상태.spacing_for_level(
            계층, _표준서식_문단위간격_표(), 표준서식_문단위간격_복귀배율)
    return _표준서식_문단위간격_상태.spacing_for(
        text, _표준서식_문단위간격_표(), 표준서식_문단위간격_복귀배율)

문장기호_목록 = ["□", "ㅇ", "-", "※", "*", "•"]


def 기호글꼴_적용(설정딕셔너리=None):
    """저장된 symbol_fonts 값을 표준서식_설정["기호_규칙"]에 반영한다.

    사용자가 설정창에서 직접 지정한 문장기호별 글꼴·크기는 어떤 문서 서식
    프로파일을 고르든 항상 우선 적용되는 개인 설정으로 취급한다.
    """
    global 표준서식_설정
    # 이전 버전의 점 계열 규칙도 대표 기호 • 하나로 합친다.
    규칙들 = 표준서식_설정.setdefault("기호_규칙", [])
    대표규칙 = next((rule for rule in 규칙들 if rule[0] == "•"), None)
    if 대표규칙 is None:
        대표규칙 = next(rule for rule in _표준서식_설정_기본값["기호_규칙"] if rule[0] == "•")
    규칙들[:] = [rule for rule in 규칙들 if rule[0] not in DOT_MARKERS] + [대표규칙]
    글꼴맵 = (설정딕셔너리 or 기본_설정).get("symbol_fonts") or {}
    글꼴맵 = {**글꼴맵, "•": 글꼴맵.get("•") or next(
        (글꼴맵[key] for key in ("·", "‧", "∙", "⋅", "ㆍ", "●") if key in 글꼴맵), {})}
    if not 글꼴맵:
        return
    새규칙 = []
    for rule in 표준서식_설정.get("기호_규칙", []):
        기호 = rule[0]
        값 = 글꼴맵.get(기호)
        if 값 and (값.get("font") or 값.get("size")):
            폰트 = str(값.get("font") or rule[2]).strip() or rule[2]
            try:
                크기 = int(값.get("size") or rule[3])
            except (TypeError, ValueError):
                크기 = rule[3]
            새규칙.append((기호, rule[1], 폰트, 크기, rule[4], rule[5]))
        else:
            새규칙.append(rule)
    표준서식_설정["기호_규칙"] = 새규칙


def 표글꼴_적용(table_fonts=None):
    """설정창의 표 머리글·본문 글꼴·크기를 표 서식 값에 반영한다.

    비어 있거나 잘못된 값(1~200pt 밖의 크기 등)은 현재 값을 그대로 둔다.
    """
    global 표_헤더서식_헤더_폰트, 표_헤더서식_헤더_크기
    global 표_헤더서식_본문_폰트, 표_헤더서식_본문_크기
    fonts = table_fonts or {}

    def 값(part, current_font, current_size):
        item = fonts.get(part) or {}
        font = str(item.get("font") or "").strip() or current_font
        try:
            size = float(str(item.get("size", "")).strip())
            if not 1 <= size <= 200:
                raise ValueError
            size = int(size) if size.is_integer() else size
        except (TypeError, ValueError):
            size = current_size
        return font, size

    표_헤더서식_헤더_폰트, 표_헤더서식_헤더_크기 = 값(
        "header", 표_헤더서식_헤더_폰트, 표_헤더서식_헤더_크기)
    표_헤더서식_본문_폰트, 표_헤더서식_본문_크기 = 값(
        "body", 표_헤더서식_본문_폰트, 표_헤더서식_본문_크기)


def _hwp_설치폴더_후보_레지스트리():
    """레지스트리에서 한/글(HWP) 설치 경로를 찾아본다. 버전별로 키 이름이 달라
    여러 후보를 시도하고, 실패해도 예외를 삼켜 폰트 자동감지 실패로만 남긴다."""
    후보 = []
    키목록 = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Hnc\HwpFrame"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Hnc\HwpFrame"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Hnc\Hwp"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Hnc\Hwp"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Hnc\HwpFrame"),
    ]
    값이름목록 = ["InstallPath", "Path", "InstallDir", "ProgramDir", ""]
    for 루트, 경로 in 키목록:
        try:
            with winreg.OpenKey(루트, 경로, 0, winreg.KEY_READ) as key:
                for 값이름 in 값이름목록:
                    try:
                        값, _ = winreg.QueryValueEx(key, 값이름)
                        if 값:
                            후보.append(Path(str(값)))
                    except OSError:
                        continue
        except OSError:
            continue
    return 후보


def _hwp_설치폴더_후보_공통경로():
    후보 = []
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"),
                 os.environ.get("ProgramW6432")):
        if not base:
            continue
        for vendor in ("Hnc", "HancomOffice", "Hancom", "한컴오피스"):
            root = Path(base) / vendor
            if root.exists():
                후보.append(root)
    return 후보


def 한글_폰트_폴더_자동감지():
    """글꼴 폴더를 추정한다.

    1) 기본 폴더는 윈도우 글꼴 폴더("C:\\Windows\\Fonts")다.
    2) 없으면 한/글 전용 글꼴 경로("C:\\Program Files (x86)\\Hnc\\Office 2020\\
       HOffice110\\Shared\\Fonts")를 확인한다.
    3) 그래도 없으면 "C:\\Program Files (x86)" 또는 "C:\\Program Files"에서
       "Hnc" 폴더를 찾고, 그 하위 폴더들 중에서 "Fonts" 폴더를 찾는다.
    4) 그래도 못 찾으면 레지스트리 등 다른 후보로 보조 탐색한다.
    못 찾으면 빈 문자열을 반환하고, 사용자가 설정창에서 직접 찾아보기로 지정하면 된다.
    """
    def _폰트파일_있음(폴더):
        try:
            return any(p.suffix.lower() in (".ttf", ".ttc", ".otf", ".hft")
                       for p in 폴더.iterdir() if p.is_file())
        except (OSError, PermissionError):
            return False

    윈도우폰트경로 = Path(r"C:\Windows\Fonts")
    try:
        if 윈도우폰트경로.is_dir() and _폰트파일_있음(윈도우폰트경로):
            return str(윈도우폰트경로)
    except OSError:
        pass

    기본경로 = Path(r"C:\Program Files (x86)\Hnc\Office 2020\HOffice110\Shared\Fonts")
    try:
        if 기본경로.is_dir() and _폰트파일_있음(기본경로):
            return str(기본경로)
    except OSError:
        pass

    for 상위 in (r"C:\Program Files (x86)", r"C:\Program Files"):
        상위경로 = Path(상위)
        try:
            if not 상위경로.is_dir():
                continue
            항목들 = list(상위경로.iterdir())
        except (OSError, PermissionError):
            continue
        for 항목 in 항목들:
            try:
                if not 항목.is_dir() or 항목.name.lower() != "hnc":
                    continue
                for 하위 in 항목.rglob("*"):
                    if 하위.is_dir() and 하위.name.lower() == "fonts" and _폰트파일_있음(하위):
                        return str(하위)
            except (OSError, PermissionError):
                continue

    # 보조 탐색: 레지스트리에 기록된 설치 경로 등 다른 후보도 확인한다.
    시작폴더들 = list(_hwp_설치폴더_후보_레지스트리()) + list(_hwp_설치폴더_후보_공통경로())
    검사한 = set()
    for 시작 in 시작폴더들:
        try:
            if not 시작.exists() or 시작 in 검사한:
                continue
            검사한.add(시작)
        except OSError:
            continue
        try:
            for 하위 in 시작.rglob("*"):
                if 하위.is_dir() and 하위.name.lower() in ("font", "fonts", "hwpfont", "hncfont"):
                    if _폰트파일_있음(하위):
                        return str(하위)
        except (OSError, PermissionError):
            continue
    return ""


def _ttf_패밀리이름(path):
    """TTF/TTC/OTF의 name 테이블에서 패밀리명을 읽는다(외부 라이브러리 없이
    직접 파싱). 한국어(langID 0x0412) 항목을 최우선으로 쓰고, 실패하면 None."""
    try:
        with open(path, "rb") as f:
            data = f.read(1024 * 1024)  # name 테이블은 보통 파일 앞부분에 있음
        if len(data) < 12:
            return None
        if data[:4] == b"ttcf":
            오프셋 = struct.unpack(">I", data[12:16])[0]
        else:
            오프셋 = 0
        표개수 = struct.unpack(">H", data[오프셋 + 4:오프셋 + 6])[0]
        name_오프셋 = None
        for i in range(표개수):
            레코드 = data[오프셋 + 12 + i * 16: 오프셋 + 12 + (i + 1) * 16]
            if len(레코드) < 16:
                break
            if 레코드[0:4] == b"name":
                name_오프셋 = struct.unpack(">I", 레코드[8:12])[0]
                break
        if name_오프셋 is None:
            return None
        _, 레코드수, 문자열오프셋 = struct.unpack(">HHH", data[name_오프셋:name_오프셋 + 6])
        최선 = {}
        for i in range(레코드수):
            위치 = name_오프셋 + 6 + i * 12
            if 위치 + 12 > len(data):
                break
            플랫폼, 인코딩, 언어, 이름ID, 길이, 문자열위치 = struct.unpack(">HHHHHH", data[위치:위치 + 12])
            if 이름ID not in (1, 4, 16):
                continue
            시작 = name_오프셋 + 문자열오프셋 + 문자열위치
            raw = data[시작:시작 + 길이]
            if not raw:
                continue
            try:
                if 플랫폼 == 1:
                    텍스트 = raw.decode("mac_roman", errors="ignore")
                else:
                    텍스트 = raw.decode("utf-16-be", errors="ignore")
            except Exception:
                continue
            텍스트 = 텍스트.strip()
            if not 텍스트:
                continue
            우선순위 = 10 if 이름ID == 16 else 0
            if 플랫폼 == 3 and 언어 == 0x0412:
                우선순위 += 3
            elif 플랫폼 == 3 and 언어 == 0x0409:
                우선순위 += 2
            else:
                우선순위 += 1
            if 이름ID not in 최선 or 최선[이름ID][0] < 우선순위:
                최선[이름ID] = (우선순위, 텍스트)
        for nid in (16, 1, 4):
            if nid in 최선:
                return 최선[nid][1]
        return None
    except Exception:
        return None


def 한글_폰트_목록(폴더):
    """지정한 폴더(보통 한/글 폰트 폴더) 안의 ttf/ttc/otf/hft에서 패밀리명을 모은다.

    hft는 한컴오피스 전용 번들 글꼴 컨테이너 형식으로, 표준 sfnt name 테이블
    파싱이 통하지 않는 경우가 많아 그때는 파일명(확장자 제외)을 글꼴 이름으로
    쓴다. 한/글은 이 이름으로 내부 번들 글꼴을 인식해 적용할 수 있다."""
    결과 = []
    if not 폴더:
        return 결과
    try:
        경로 = Path(폴더)
        if not 경로.is_dir():
            return 결과
        본적있음 = set()
        for p in sorted(경로.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in (".ttf", ".ttc", ".otf", ".hft"):
                continue
            이름 = _ttf_패밀리이름(p) or p.stem
            if 이름 and 이름 not in 본적있음:
                본적있음.add(이름)
                결과.append(이름)
        결과.sort(key=lambda s: (0 if re.match(r'^[A-Za-z]', s) else 1, s))
    except (OSError, PermissionError):
        pass
    return 결과


def 한컴_번들_폰트_폴더_목록():
    """설치 경로 후보들 아래에서 .hft(한컴오피스 전용 번들 글꼴) 파일이 있는
    폴더를 모두 찾는다. 폴더 이름이 'Fonts'가 아니어도 실제 .hft 파일 위치를
    직접 뒤져서 찾으므로, 배포판마다 다른 폴더 이름에 흔들리지 않는다."""
    폴더집합 = set()
    후보들 = list(_hwp_설치폴더_후보_레지스트리()) + list(_hwp_설치폴더_후보_공통경로())
    후보들.append(Path(r"C:\Program Files (x86)\Hnc\Office 2020\HOffice110\Shared\Fonts"))
    검사한 = set()
    for 시작 in 후보들:
        try:
            if not 시작.exists() or 시작 in 검사한:
                continue
            검사한.add(시작)
        except OSError:
            continue
        try:
            for hft파일 in 시작.rglob("*.hft"):
                폴더집합.add(hft파일.parent)
        except (OSError, PermissionError):
            continue
    return sorted(폴더집합, key=str)


def 한글_폰트_목록_전체(폴더):
    """사용자가 지정한 글꼴 폴더 목록에, 자동으로 찾은 한컴오피스 전용
    번들(HFT) 글꼴 폴더의 글꼴을 더해 합친 전체 글꼴 이름 목록을 돌려준다."""
    결과 = list(한글_폰트_목록(폴더))
    본적있음 = set(결과)
    폴더_문자열 = str(Path(폴더)) if 폴더 else ""
    for 번들폴더 in 한컴_번들_폰트_폴더_목록():
        if str(번들폴더) == 폴더_문자열:
            continue
        for 이름 in 한글_폰트_목록(str(번들폴더)):
            if 이름 not in 본적있음:
                본적있음.add(이름)
                결과.append(이름)
    결과.sort(key=lambda s: (0 if re.match(r'^[A-Za-z]', s) else 1, s))
    return 결과


def 서식_기본값_전역_복원():
    global 표준서식_설정
    global 표_헤더서식_헤더_폰트, 표_헤더서식_헤더_크기, 표_헤더서식_헤더_굵게
    global 표_헤더서식_본문_폰트, 표_헤더서식_본문_크기, 표_헤더서식_본문_굵게
    global 표준서식_문단위간격_box_pt, 표준서식_문단위간격_circle_pt, 표준서식_문단위간격_note_pt
    global 표준서식_문단위간격_dash_pt
    global 표준서식_문단위간격_chapter_pt, 표준서식_문단위간격_midtitle_pt
    global 표준서식_문단위간격_복귀배율
    global 활성_정밀표_프로필, 활성_서식표_프로필, 활성_표서식_프로필

    표준서식_설정 = copy.deepcopy(_표준서식_설정_기본값)
    표_헤더서식_헤더_폰트 = _표_헤더서식_기본값["헤더_폰트"]
    표_헤더서식_헤더_크기 = _표_헤더서식_기본값["헤더_크기"]
    표_헤더서식_헤더_굵게 = _표_헤더서식_기본값["헤더_굵게"]
    표_헤더서식_본문_폰트 = _표_헤더서식_기본값["본문_폰트"]
    표_헤더서식_본문_크기 = _표_헤더서식_기본값["본문_크기"]
    표_헤더서식_본문_굵게 = _표_헤더서식_기본값["본문_굵게"]
    표준서식_문단위간격_chapter_pt = _표준서식_문단위간격_기본값["chapter"]
    표준서식_문단위간격_midtitle_pt = _표준서식_문단위간격_기본값["midtitle"]
    표준서식_문단위간격_box_pt = _표준서식_문단위간격_기본값["box"]
    표준서식_문단위간격_circle_pt = _표준서식_문단위간격_기본값["circle"]
    표준서식_문단위간격_dash_pt = _표준서식_문단위간격_기본값["dash"]
    표준서식_문단위간격_note_pt = _표준서식_문단위간격_기본값["note"]
    표준서식_문단위간격_복귀배율 = 150
    _표준서식_문단위간격_상태.reset()
    활성_정밀표_프로필 = None
    활성_서식표_프로필 = None
    활성_표서식_프로필 = None
    globals()["활성_머리서식_프로필"] = None
    globals()["괄호_축소_pt"] = 2

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
    "prevent_word_split": True,
    "punctuation": True,
    "punctuation_threshold": "5",
    "keep_punctuation_set_together": True,
    "color_mark_on": False,
    "color": "blue",
    "autoclose": False,
    "stdformat": True,
    "verify": False,
    # 기록 탭의 보고서 파일 생성 옵션. 상세 진단 자체는 verify가 제어한다.
    "integrity_report_file": False,
    "final_review_file": False,
    # 작업로그·무결성검사 JSON·최종검수 JSON은 사용자가 켜기 전까지 꺼 둔다(판 2부터).
    "report_files_rev": 2,
    "two_pass_processing": False,
    "retry_body": "15",
    "retry_table": "5",
    "linespacing_min": "160",
    "linespacing_max": "200",
    # 문두 라벨 굵게에서 뺄 기호(False). 별표(*, **)는 2026-10-03부터 기본으로 뺀다.
    "label_symbols": {"□": False, "※": False, "*": False, "**": False},
    # 설정 파일 판: 2 = 별표(*, **) 라벨 굵게 기본값 끔을 반영한 설정(예전 파일은 불러올 때 한 번 끈다)
    "label_symbols_rev": 2,
    "paren_shrink": True,
    "paren_label_bold": True,
    "std_margin": True,
    "std_ratio": True,
    "std_linespacing": True,
    "std_title": True,
    "std_title_auto": True,
    "std_attachment_auto": True,
    "std_midtitle_auto": True,
    "std_midtitle_bold": True,
    "abbreviations": {},
    "abbreviation_defaults": True,
    "std_title_bold": True,
    "std_dateinfo": True,
    "std_dateinfo_bold": True,
    "std_symbols": True,
    "std_hanging_indent": True,
    "std_supplement_indent": True,
    "std_symbol_box_bold": False,
    "std_symbol_o_bold": True,
    "std_symbol_dash_bold": False,
    "std_symbol_note_bold": False,
    # 같은 항목기호의 라벨이 굵게 되면 다른 문단의 머리말도 굵게 맞춤
    "std_marker_bold_consistency": True,
    "std_parspace": True,
    # 항목기호 문장 사이에 빈 줄로 띄운 간격 삭제(문단 위 여백으로 대신함)
    "std_remove_blank_lines": True,
    "std_parspace_chapter": "15",
    "std_parspace_midtitle": "15",
    "std_parspace_box": "15",
    "std_parspace_circle": "8",
    "std_parspace_dash": "4",
    "std_parspace_note": "0",
    # 설정 파일 판: 2 = 문단 위 여백 기본값 15/15/15/8/4/0pt(예전 기본값 20/15/15/10/3을 그대로 쓰던 파일은 새 값으로)
    "std_parspace_rev": 2,
    "std_supplement_rev": 2,
    "std_parspace_return_percent": "150",
    # 제목 서식 부제(제목 글의 첫 쉼표 앞 글) 글자 크기 pt
    "std_title_subtitle_pt": "15",
    # 새로 만드는 제목 서식 표의 담당자 칸(2×2 표 B2, 2행1열 표 A2) 글. 비우면 기준 표의 글을 그대로 둔다.
    "title_owner_text": "",
    "std_table_header": True,
    "active_format_profile": "",
    "review_document_kind": "보고서",
    "review_reading_purpose": "상세 설명용",
    "symbol_fonts": {
        "□": {"font": "HY견고딕", "size": "17"},
        "ㅇ": {"font": "한컴돋움", "size": "15"},
        "-": {"font": "휴먼명조", "size": "14"},
        "※": {"font": "한컴돋움", "size": "13"},
        # *(대표 기호, **는 *로 합침)의 기본값은 ※와 동일하다.
        "*": {"font": "한컴돋움", "size": "13"},
        "•": {"font": "한컴돋움", "size": "13"},
    },
    # 표 머리글(첫 행)·본문(나머지 행) 글꼴·크기. 문장기호별 글꼴처럼 서식
    # 프로파일보다 우선하는 개인 설정이다.
    "table_fonts": {
        "header": {"font": "한컴돋움", "size": "13"},
        "body": {"font": "휴먼명조", "size": "12"},
    },
    "hwp_font_folder": "",
    "paste_add_folder": "",
    "always_on_top": True,
    "check_updates_on_start": True,
    "table_spacing": True,
    "log_file": False,
    # 개발자 모드: 켜야 문서 도구(문서 구조 검토·맞춤법·작성 도우미·Markdown·고급 문서 도구 등) 메뉴가 보인다.
    "developer_mode": False,
    # '한 번에 적용' 카드의 '자간 조정 포함'. 끄면 기존 자간을 두고 서식만 입히는 서식 적용(format)으로 실행한다.
    "all_include_spacing": True,
    # 한 번에 적용의 '표 제외': 켜면 표 관련 세부 작업을 모두 빼고 표 칸 안 문장도 자간 작업에서 뺀다.
    "all_exclude_tables": False,
    # 한 번에 적용의 '페이지 맞춤 제외': 켜면 문단 아래 간격 페이지 맞춤·관련 문단 페이지 배치를 뺀다.
    "all_exclude_pagefit": False,
    # 서식 통일 카드의 '표 제외'·'자간 정리 제외'·'페이지 맞춤 제외'. 세부 작업과 연동되며, 서식 통일의 쪽 맞춤은
    # 세부 작업 기본값이 꺼짐이라 '페이지 맞춤 제외'만 기본 켜짐이다.
    "unify_exclude_tables": False,
    "unify_exclude_spacing": False,
    "unify_exclude_pagefit": True,
    # 서식 통일 카드의 '원본 쪽 구성 유지'(세부 작업 page_layout_keep과 연동, 기본 켬).
    "unify_keep_layout": True,
    # 서식통일 뒤 '작업 결과 확인' 창(서식통일 5/5)을 띄울지. 기본 꺼짐(2026-10-04 사용자 요청).
    "unify_result_window": False,
    # '자간 정리' 카드의 '기존 자간 초기화'(세부 작업 01과 같은 값). None이면 저장된 세부 작업 구성을 따른다.
    "spacing_reset_existing": None,
}


# 첨부 버전의 서식값을 기본 서식으로 고정한다.
# 사용자 PC의 settings.json은 별도로 유지하며 초기화할 때 이 값을 사용한다.
def 기본_서식프로파일():
    return {"version": 1, "name": "기본 보고서 서식",
            "format": copy.deepcopy(_표준서식_설정_기본값),
            "options": {k: copy.deepcopy(v) for k, v in 기본_설정.items()
                        if k.startswith("std_") or k in ("paren_shrink", "paren_label_bold", "label_symbols")}}


def 서식프로파일_목록():
    result = {"": 기본_서식프로파일()}
    folder = 서식프로파일_폴더()
    if folder.exists():
        for path in sorted(folder.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("version") != 1 or not isinstance(data.get("name"), str):
                    raise ValueError("지원하지 않는 서식 파일")
                fmt = data["format"]
                if not isinstance(fmt, dict) or not isinstance(data.get("options"), dict):
                    raise ValueError("잘못된 서식 데이터")
                for key in _표준서식_설정_기본값:
                    if key not in fmt:
                        raise ValueError("필수 서식값 누락")
                for rule in fmt["기호_규칙"]:
                    if len(rule) != 6 or not 0 < float(rule[3]) <= 1000:
                        raise ValueError("잘못된 글자 크기")
                # 예전 서식(v4 이하)도 서식 요소 분석이 있으면 지금 복사 범위(계층 추가 서식·규칙)로 적용 값을
                # 다시 만든다. 파일은 바꾸지 않는다(일반 표 서식처럼 예시가 다시 필요한 것은 예시를 다시 넣어야 함).
                if data.get("element_analysis") and int(data.get("profile_version") or 0) < 5:
                    서식요소.apply_to_profile(data)
                result[path.stem] = data
            except Exception as exc:
                if _콘솔_출력_가능:
                    print(f"서식 파일 제외: {path.name}: {exc}")
    return result


def _표_텍스트(element):
    return " ".join("".join(t.itertext()).strip() for t in element.iter()
                    if 제목_xml이름(t) == "t" and "".join(t.itertext()).strip())


def _표_서명(table, ordinal=0):
    rows = [row for row in table.iter() if 제목_xml이름(row) == "tr"]
    cells = 제목_셀들(table)
    first_row_cells = [cell for cell in rows[0] if 제목_xml이름(cell) == "tc"] if rows else []
    return {
        "ordinal": ordinal,
        "rows": int(table.get("rowCnt", len(rows)) or len(rows)),
        "cols": int(table.get("colCnt", 0) or 0),
        "cell_count": len(cells),
        "first_cell": _표_텍스트(cells[0])[:120] if cells else "",
        "first_row": " | ".join(_표_텍스트(cell) for cell in first_row_cells)[:500],
    }


def _정밀표_프로필_추출(header, sections):
    """표별 구조와 셀 서식을 원본 HWPX XML 그대로 JSON 호환 형태로 보존한다."""
    tables = []
    ordinal = 0
    for section_name in sections:
        root = safe_xml_fromstring(sections[section_name])
        for table in (e for e in root.iter() if 제목_xml이름(e) == "tbl"):
            signature = _표_서명(table, ordinal)
            signature["section"] = section_name
            signature["table_xml"] = ET.tostring(table, encoding="unicode")
            tables.append(signature)
            ordinal += 1
    return {
        "version": 1,
        "header_xml": ET.tostring(header, encoding="unicode"),
        "tables": tables,
    }


def hwpx_서식_분석(path):
    """HWPX의 대표 페이지·문단·문자·표 서식을 분석해 재사용 프로필로 만든다."""
    profile = 기본_서식프로파일()
    fmt = profile["format"]
    def tag(e): return e.tag.rsplit("}", 1)[-1]
    def child(e, name):
        return next((x for x in e.iter() if tag(x) == name), None)
    with zipfile.ZipFile(path) as z:
        header = safe_xml_fromstring(z.read("Contents/header.xml"))
        fonts = {}
        for face in header.iter():
            if tag(face) == "fontface" and face.get("lang") == "HANGUL":
                fonts.update({f.get("id"): f.get("face") for f in face if tag(f) == "font"})
        # 예시 글꼴의 형식(TTF·HFT)을 함께 남긴다. 한/글은 HFT 글꼴(HCI Poppy·한양중고딕 등)을 TTF로 지정하면
        # 오류 없이 무시하는데, 예전에는 서식통일 때만 형식을 읽어 서식 적용에서 예시 글꼴이 빠졌다(2026-10-04).
        fmt["글꼴형식"] = 글꼴형식_모으기(header)
        chars = {e.get("id"): e for e in header.iter() if tag(e) == "charPr"}
        paras = {e.get("id"): e for e in header.iter() if tag(e) == "paraPr"}
        groups = {r[0]: Counter() for r in fmt["기호_규칙"]}
        body_styles = Counter()
        first_styles = []
        ratios, spacing, letter_spacings = Counter(), Counter(), Counter()
        paragraphs = {k: Counter() for k in groups}
        marker_shapes = defaultdict(Counter)
        hierarchy_paragraphs = []
        aliases = {"ㅁ": "□", "○": "ㅇ", "☞": "ㅇ", "*": "※", "→": "※"}
        count = 0
        margins = False
        sections = sorted((n for n in z.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)),
                          key=lambda n: int(re.search(r"section(\d+)", n).group(1)))
        for name in sections:
            root = safe_xml_fromstring(z.read(name))
            if not margins:
                page = child(root, "pagePr")
                m = child(page, "margin") if page is not None else None
                if m is not None:
                    for key in fmt["여백_mm"]:
                        if m.get(key) is not None:
                            fmt["여백_mm"][key] = round(float(m.get(key)) * 25.4 / 7200, 3)
                    margins = True
            # section의 직접 자식 p만: 표 셀/각주 등의 중첩 문단을 섞지 않는다.
            for para in root:
                if tag(para) != "p": continue
                runs = []
                for run in para:
                    if tag(run) != "run": continue
                    text = "".join("".join(t.itertext()) for t in run if tag(t) == "t")
                    if text.strip(): runs.append((run, text))
                text = "".join(t for _, t in runs).lstrip()
                if not text: continue
                count += 1
                symbol = aliases.get(text[0], text[0])
                # 가장 긴 텍스트 런을 사용해 짧은 라벨 강조가 본문 서식을 압도하지 않도록 한다.
                run, _ = max(runs, key=lambda item: len(item[1]))
                char = chars.get(run.get("charPrIDRef"))
                if char is None: continue
                fontref = child(char, "fontRef")
                font = fonts.get(fontref.get("hangul")) if fontref is not None else None
                height = float(char.get("height", "0")) / 100
                ratio = child(char, "ratio")
                if ratio is not None: ratios[float(ratio.get("hangul", "100"))] += max(1, len(text))
                letter_spacing = child(char, "spacing")
                if letter_spacing is not None and letter_spacing.get("hangul") is not None:
                    # 예전에는 문단마다 덮어써 마지막 문단의 자간이 기본 자간이 됐다(2026-10-04 수정).
                    try: letter_spacings[float(letter_spacing.get("hangul"))] += max(1, len(text))
                    except (TypeError, ValueError): pass
                pp = paras.get(para.get("paraPrIDRef"))
                ls = child(pp, "lineSpacing") if pp is not None else None
                if ls is not None and ls.get("type") == "PERCENT":
                    spacing[float(ls.get("value"))] += max(1, len(text))
                bold = child(char, "bold") is not None
                pm = child(pp, "margin") if pp is not None else None
                def margin_value(key):
                    item = child(pm, key) if pm is not None else None
                    return int(item.get("value", "0")) if item is not None and item.get("unit", "HWPUNIT") == "HWPUNIT" else 0
                hierarchy_paragraphs.append({"text": text, "font": font,
                                             "size_pt": height, "left": margin_value("left"),
                                             "indent": margin_value("intent"),
                                             "prev_spacing": margin_value("prev")})
                detected_marker, detected_role = leading_marker(text)
                if detected_marker and font and height > 0:
                    marker_shapes[(detected_role, detected_marker)][(font, height, bold)] += 1
                if font and height > 0:
                    body_styles[(font, height, bold)] += max(1, len(text))
                    if len(first_styles) < 2:
                        first_styles.append((font, height, bold))
                if symbol not in groups or not font or height <= 0: continue
                groups[symbol][(font, height, bold)] += 1
                if pp is not None:
                    pm = child(pp, "margin")
                    vals = {}
                    if pm is not None:
                        for xmlkey, key in (("left", "LeftMargin"), ("right", "RightMargin"),
                                            ("intent", "Indentation"), ("prev", "PrevSpacing"), ("next", "NextSpacing")):
                            e = child(pm, xmlkey)
                            if e is not None and e.get("unit", "HWPUNIT") == "HWPUNIT":
                                vals[key] = int(e.get("value", "0"))
                    if ls is not None and ls.get("type") == "PERCENT":
                        vals["LineSpacingType"] = 0
                        vals["LineSpacing"] = int(float(ls.get("value")))
                    paragraphs[symbol][tuple(sorted(vals.items()))] += 1
        # 첫 표의 첫 행과 나머지 행에서 대표 문자 서식을 추출한다. 일반 본문이
        # 없는 표 전용 문서는 표 본문(없으면 머리글)을 대표 본문 대체값으로 쓴다.
        # 글이 있는 첫 표를 쓴다. 빈 테두리 표(1칸 틀 등)가 맨 앞에 있는 서식은 예전에 첫 표만 보다가
        # '복제할 문자 서식이 없다'며 서식 등록이 실패했다(범정부오피스 용인 쪽지 서식, 2026-10-04).
        table_header_styles, table_body_styles = Counter(), Counter()
        for name in sections:
            root = safe_xml_fromstring(z.read(name))
            for table in (e for e in root.iter() if tag(e) == "tbl"):
                rows = [e for e in table.iter() if tag(e) == "tr"]
                for row_index, row in enumerate(rows):
                    counter = table_header_styles if row_index == 0 else table_body_styles
                    for run in (e for e in row.iter() if tag(e) == "run"):
                        text = "".join("".join(t.itertext()) for t in run if tag(t) == "t").strip()
                        char = chars.get(run.get("charPrIDRef"))
                        if not text or char is None:
                            continue
                        fontref = child(char, "fontRef")
                        font = fonts.get(fontref.get("hangul")) if fontref is not None else None
                        height = float(char.get("height", "0")) / 100
                        if font and height > 0:
                            counter[(font, height, child(char, "bold") is not None)] += len(text)
                if table_header_styles or table_body_styles:
                    break
            if table_header_styles or table_body_styles:
                break
        본문_대체출처 = None
        if not body_styles:
            fallback_styles = table_body_styles or table_header_styles
            if not fallback_styles:
                raise ValueError("본문 또는 표 셀에서 복제할 수 있는 문자 서식을 찾지 못했습니다. "
                                 "글이 없는 문서(그림·워터마크만 있는 문서)는 서식 예시로 쓸 수 없습니다. "
                                 "글이 들어 있는 예시 보고서를 넣어 주세요.")
            body_styles.update(fallback_styles)
            본문_대체출처 = "표 본문 셀" if table_body_styles else "표 머리글 셀"
        if ratios: fmt["기본_장평"] = ratios.most_common(1)[0][0]
        if letter_spacings: fmt["기본_자간"] = letter_spacings.most_common(1)[0][0]
        if spacing: fmt["기본_줄간격_퍼센트"] = spacing.most_common(1)[0][0]
        if first_styles:
            font, size, bold = first_styles[0]
            fmt["제목_문단"] = {"font": font, "size_pt": size, "bold": bold}
        if len(first_styles) > 1:
            font, size, bold = first_styles[1]
            fmt["일자담당자_문단"] = {"font": font, "size_pt": size, "bold": bold}
        fmt["복사_문단모양"] = {}
        found, missing = [], []
        for i, rule in enumerate(fmt["기호_규칙"]):
            symbol = rule[0]
            if groups[symbol]:
                font, size, bold = groups[symbol].most_common(1)[0][0]
                fmt["기호_규칙"][i] = (symbol, rule[1], font, size, bold, False)
                key = {"□": "box", "ㅇ": "o", "-": "dash", "※": "note"}.get(symbol)
                if key:
                    profile["options"][f"std_symbol_{key}_bold"] = bold
                if paragraphs[symbol]:
                    fmt["복사_문단모양"][symbol] = dict(paragraphs[symbol].most_common(1)[0][0])
                found.append(f"{symbol}: {font} {size:g}pt, 굵게 {'ON' if bold else 'OFF'}")
            else: missing.append(symbol)
        대표폰트, 대표크기, 대표굵게 = body_styles.most_common(1)[0][0]
        fmt["본문_문단"] = {"font": 대표폰트, "size_pt": 대표크기, "bold": 대표굵게}
        # 기본 프로필은 기존처럼 일반 본문을 보존한다. 분석해서 만든 프로필만
        # 대표 본문 글꼴·크기를 일반 문단에도 적용한다.
        fmt["복제_본문서식"] = True

        section_payloads = {name: z.read(name) for name in sections}
        profile["precise_tables"] = _정밀표_프로필_추출(header, section_payloads)
        # 서식 요소 전수 분석: 항목기호 문장은 계층별로, 제목·개요·중제목·붙임 표는 칸(A1·A2·B2 …)별로
        # 모든 글자·문단·칸 요소의 대표값을 구하고, 서식 표는 예시로 보관해 서식 적용에 쓴다.
        # 사용자는 서식 세부사항 창에서 대표값을 고칠 수 있다.
        요소분석 = 서식요소.analyze_format_elements(path, 서식표_종류판별)
        # 일반 표 서식은 데이터 표(본문이 시작된 뒤의 격자 표, 제목처럼 큰 글자 없음)에서만 배운다. 문서 머리의
        # 결재란·보도자료 머리·보고자 표는 데이터 표가 아니라 그 서식을 정리할 문서의 표에 입히지 않는다. 표 머리글·본문
        # 글자(table_format)도 apply_to_profile이 데이터 표 대표값으로만 채우고, 데이터 표가 없으면 기본 표 서식을
        # 쓴다(2026-10-04 범정부오피스 서식 시험). 예전에는 첫 표(문서 머리 표가 흔함)의 글자를 썼다.
        데이터표 = 요소분석.get("tables", {})
        # 데이터 표 가운데 일반 표 대표값과 가장 많이 같은 표에서 기본 표 서식을 배운다(같으면 칸이 많은 표).
        # 예전처럼 칸이 가장 많은 표에서 배우면 모양이 다른 표 하나의 서식이 모든 일반 표에 퍼졌다.
        표번호 = set(데이터표.get("data_tables", []))
        일반표들 = [t for 번호, t in enumerate(서식요소.top_level_tables(
                      safe_xml_fromstring(section_payloads[name]) for name in sections), 1) if 번호 in 표번호]
        if 일반표들:
            대표_일반표 = 요소분석.get("tables", {})
            기준표 = max(일반표들, key=lambda t: (서식요소.general_table_agreement(t, header, 대표_일반표),
                                             len(제목_셀들(t))))
            try:
                profile["table_style"] = 표서식_한표학습(header, 기준표, Path(path).name)
            except ValueError as exc:
                로그(f"예시 보고서의 일반 표 서식을 배우지 못했습니다(준말 '표' 서식을 씁니다): {exc}")
        profile["style_hierarchy"] = analyze_hierarchy(hierarchy_paragraphs)
        fmt["논리역할_규칙"] = {}
        for item in profile["style_hierarchy"]["styles"]:
            role, marker = item["role"], item["marker"]
            if role not in ("장", "중제목", "소제목", "본문", "내용", "부연설명") or marker == "(없음)":
                continue
            shape = marker_shapes.get((role, marker))
            font, size, bold = shape.most_common(1)[0][0] if shape else (item["font"], item["size_pt"], False)
            if not font or not size:
                continue
            if role == "장":
                # 장 문두(제1장·제2장 …)는 문서마다 달라 기호 규칙에 넣지 않고 역할 규칙 '(장)'으로 둔다.
                fmt["논리역할_규칙"].setdefault("장", ("(장)", 0, font, size, bold, False))
                fmt["복사_문단모양"].setdefault("(장)", {
                    "LeftMargin": item["left_hwpunit"],
                    "Indentation": item["first_line_hwpunit"],
                    "PrevSpacing": item["prev_spacing_typical"] or 0,
                })
                continue
            rule = (marker, 0, font, size, bold, False)
            fmt["논리역할_규칙"].setdefault(role, rule)
            if marker not in {r[0] for r in fmt["기호_규칙"]}:
                fmt["기호_규칙"].append(rule)
            fmt["복사_문단모양"].setdefault(marker, {
                "LeftMargin": item["left_hwpunit"],
                "Indentation": item["first_line_hwpunit"],
                "PrevSpacing": item["prev_spacing_typical"] or 0,
            })
        fmt["복제_들여쓰기_유지"] = True
        profile["profile_version"] = 5
        profile["storage_format"] = "json"
        profile["source"] = {"filename": Path(path).name, "paragraphs_analyzed": count,
                             "body_style_fallback": 본문_대체출처}
        profile["options"]["symbol_fonts"] = {
            rule[0]: {"font": rule[2], "size": str(rule[3])} for rule in fmt["기호_규칙"]
        }
        # 복사한 글자 강조/문단 여백을 다른 후처리로 덮지 않는다.
        profile["options"].update(paren_shrink=False, paren_label_bold=False,
                                   std_hanging_indent=False, std_supplement_indent=False)
        profile["form_tables"] = dict(요소분석.pop("samples"))
        # 중제목을 표 첫 칸의 로마자 숫자로 쓴 문서도 중제목(3단계)이 있는 것으로 보고 문서 유형(A·B·C형)을 정한다.
        profile["style_hierarchy"]["document_type"] = 문서유형_판정(
            profile["style_hierarchy"]["role_sequence"],
            any(k.startswith("midtitle") for k in profile["form_tables"]))
        profile["element_analysis"] = 요소분석
        서식요소.apply_to_profile(profile)
        머리요약 = 보고서머리_프로필_반영(z, profile)
        표글자 = profile.get("table_format") or {}
        profile["summary"] = (
            f"대표 본문: {대표폰트} {대표크기:g}pt, 굵게 {'ON' if 대표굵게 else 'OFF'}\n"
            + (f"대표 본문 대체 분석: {본문_대체출처}\n" if 본문_대체출처 else "")
            + ("\n".join(found) + "\n" if found else "")
            + "미검출 기호(기본값 유지): " + (", ".join(missing) or "없음")
            + (f"\n표 머리글: {표글자.get('header_font')} {float(표글자.get('header_size') or 0):g}pt / "
               f"표 본문: {표글자.get('body_font')} {float(표글자.get('body_size') or 0):g}pt"
               if 표글자.get("header_font") or 표글자.get("body_font")
               else "\n표 머리글·본문: 예시에 데이터 표가 없어 기본 표 서식을 씁니다")
            + f"\n정밀 표 프로필: {len(profile['precise_tables']['tables'])}개"
            + (f"\n일반 표 서식: {표서식_설명(profile['table_style'])}" if profile.get("table_style") else "")
            + (f"\n서식 표 예시: {', '.join(서식요소.FORM_LABELS[k] for k in profile['form_tables'])}"
               if profile["form_tables"] else "")
            + (f"\n{머리요약}" if 머리요약 else "")
            + "\n\n" + hierarchy_summary(profile["style_hierarchy"])
            + "\n페이지 여백·장평·자간·줄간격·문단 모양과 셀별 표 서식을 함께 복제합니다."
        )
        return profile


def 보고서머리_프로필_반영(z, profile):
    """예시 HWPX의 보고서 머리(제목·보고 주체·개요) 구성을 프로필에 저장하고 요약 글을 돌려준다.

    예전에는 '표 밖 첫 두 문단'을 제목·일자담당자로 보아, 제목이 표(1×1 상자) 안에 있는 중앙부처 보고서에서
    작성일 줄을 제목으로, 개요를 일자담당자로 잘못 잡았다(korean-report-hwpx 129종 실측, 2026-10-10).
    """
    try:
        names = sorted((n for n in z.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)),
                       key=lambda n: int(re.search(r"section(\d+)", n).group(1)))
        header_root = safe_xml_fromstring(z.read("Contents/header.xml"))
        spec = 보고서머리.build_spec(header_root, safe_xml_fromstring(z.read(names[0])))
    except Exception as exc:
        로그(f"보고서 머리 분석 실패(무시): {exc}")
        return ""
    if not spec:
        return ""
    profile["report_header"] = spec
    fmt = profile["format"]
    title = spec["title"]
    if title.get("char", {}).get("font"):
        fmt["제목_문단"] = {"font": title["char"]["font"], "size_pt": title["char"]["size_pt"],
                          "bold": bool(title["char"].get("bold"))}
    문단정보 = [i for i in spec["info"] if i["container"] == "paragraph"]
    if 문단정보 and 문단정보[0].get("char", {}).get("font"):
        c = 문단정보[0]["char"]
        fmt["일자담당자_문단"] = {"font": c["font"], "size_pt": c["size_pt"], "bold": bool(c.get("bold"))}
    담는곳 = {"paragraph": "상자 없는 제목 문단"}.get(title["container"]) or (
        title["container"].replace("table", "").replace("x", "×") + " 제목 표")
    줄 = [f"보고서 머리: {담는곳} ({title['char'].get('font')} {title['char'].get('size_pt', 0):g}pt, "
         f"{_정렬이름.get(title.get('align'), title.get('align') or '-')})"]
    for i in spec["info"]:
        위치 = "제목 표 칸" if i["container"] == "cell" else ("제목 위 문단" if i.get("position") == "before_title" else "제목 아래 문단")
        줄.append(f"보고 주체({위치}): {i['text']}  → 틀 {i['template']}")
    if spec.get("overview"):
        줄.append("개요 상자: 있음(예시 상자 서식으로 복사)")
    return "\n".join(줄)


_정렬이름 = {"LEFT": "왼쪽", "RIGHT": "오른쪽", "CENTER": "가운데", "JUSTIFY": "양쪽", "DISTRIBUTE": "배분"}


def 보고서머리_hwpx_처리(source, target=None, selections=None):
    """서식 프로필의 보고서 머리(제목·보고 주체·개요) 구성과 표기 방식을 대상 문서에 옮긴다(알파, 2026-10-10).

    대상의 제목 글·개요 글은 그대로 두고, 날짜·기관·부서·담당자 값은 예시의 표기 틀로 다시 쓴다.
    제목 표 안 날짜 칸은 한 줄로 입력(lineWrap=SQUEEZE)으로 둔다.
    """
    spec = 활성_머리서식_프로필 if 알파_머리서식복사_사용 else None
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    names = sorted((n for n in contents if re.fullmatch(r'Contents/section\d+\.xml', n)),
                   key=lambda n: int(re.search(r'section(\d+)', n).group(1)))
    first = names[0] if names else None
    def 시작들(root):
        # 여러 보고서를 묶은 문서: 보고서마다(제목 표마다) 머리를 맞춘다. 제목 표는 서식 적용과 같은 판정을 쓴다.
        tables = [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']
        제목표 = {id(tables[i]) for i, _ in 제목_대상찾기(root, header) if i < len(tables)}
        return 보고서머리.report_starts(root, lambda t: id(t) in 제목표)

    if selections is None:
        if not spec or first is None:
            return {}
        root = safe_xml_fromstring(contents[first])
        found = [i for i in 시작들(root) if 보고서머리.analyze(header, root, i)["title"]]
        if len(found) > 1 and (spec.get("title") or {}).get("container") == "paragraph":
            # 여러 보고서를 묶은 문서는 제목 표가 보고서 경계다(쪽 맞춤·쪽 나누기). 예시 제목이 상자 없는 문단이면
            # 경계를 잃으므로 머리 서식 복사를 하지 않는다(2026-10-10).
            로그(f"보고서 머리 서식 복사: 건너뜀(보고서 {len(found)}개 문서에 문단 제목 서식을 쓰면 보고서 경계가 사라짐)")
            return {first: []}
        return {first: found}
    if not spec or not any(selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    root = safe_xml_fromstring(contents[first])
    본문폭 = _구역_본문폭(root, None)
    합계 = Counter()
    병합 = {}

    def 한번_병합(h, sample_header):
        # 보고서가 여러 개여도 예시 서식 정의는 문서 header에 한 번만 더한다.
        if 'maps' not in 병합:
            병합['maps'] = 제목_참조병합(h, sample_header)
        return 병합['maps']

    # 뒤 보고서부터 바꿔 앞 보고서의 문단 번호가 흔들리지 않게 한다.
    for start in sorted(시작들(root), reverse=True):
        통계 = 보고서머리.apply_header(header, root, spec, 한번_병합, start=start,
                                   fit_table=(lambda t: _서식표_가로맞춤(t, 본문폭, 비례=True)) if 본문폭 else None)
        합계.update({k: v for k, v in 통계.items() if isinstance(v, int)})
    if not 합계.get("applied"):
        로그("보고서 머리 서식 복사: 바꿀 머리 없음")
        shutil.copyfile(source, target)
        return 0
    contents[first] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
    _hwpx_안전_저장(contents, target)
    로그(f"보고서 머리 서식 복사: 보고서 {합계['applied']}개 · 제목 {합계['title']}·보고 주체 {합계['info']}·개요 "
         f"{합계['overview']}개를 예시 구성으로 맞춤(날짜 칸 한 줄 {합계['squeezed']}개)")
    return 합계['applied']


def 예시문서_기본이름(문단들):
    """직접 편집한 예시 문서의 기본 서식 이름: 첫 문장의 앞 8글자(TODO 6순위).

    첫 번째 비어 있지 않은 문단을 첫 문장으로 보고, 항목기호(□·ㅇ·- 등)와 앞 공백은
    빼며 첫 마침표(. ! ?) 앞까지만 쓴다. 쓸 글자가 없으면 '새 서식'.
    """
    for text in 문단들:
        body = (text or "").strip()
        if not body:
            continue
        marker_end = 문장부호_마커_끝위치(body)
        if marker_end:
            body = body[marker_end:].strip()
        끝 = re.search(r"[.!?。]", body)
        if 끝:
            body = body[:끝.start()]
        body = re.sub(r"\s+", " ", body).strip()
        if body:
            return body[:8].strip()
    return "새 서식"


def 한글파일_서식_분석(path):
    if Path(path).suffix.lower() == ".hwpx":
        return hwpx_서식_분석(path)
    if Path(path).suffix.lower() == ".pdf":
        # PDF 예시: kordoc으로 HWPX를 만든 뒤 PDF 서식을 옮겨 심고 분석한다(원본은 읽기만 함).
        with tempfile.TemporaryDirectory(prefix="pdf_format_") as folder:
            target = Path(folder) / "source.hwpx"
            외부문서_hwpx로_변환(Path(path), ".pdf", target)
            return hwpx_서식_분석(target)
    # 원본을 복사한 뒤 독립 한글 인스턴스에서 임시 HWPX로 변환한다.
    with tempfile.TemporaryDirectory(prefix="hwp_format_") as folder:
        source = Path(folder) / "source.hwp"
        target = Path(folder) / "source.hwpx"
        shutil.copy2(path, source)
        app = None
        pythoncom.CoInitialize()
        try:
            보안모듈_초기화()
            app = 한글_COM_인스턴스_생성(독립=True)
            if not app.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE):
                raise RuntimeError("한글 보안 모듈을 등록하지 못했습니다.")
            if not 한글_문서_열기(app, source, "HWP"):
                raise RuntimeError("한글파일을 열지 못했습니다.")
            if not app.SaveAs(str(target), "HWPX", ""):
                raise RuntimeError("HWPX 변환 실패. 한글에서 HWPX로 저장한 파일을 선택해 주세요.")
            return hwpx_서식_분석(target)
        finally:
            if app is not None:
                try: app.Quit()
                except Exception: pass
            pythoncom.CoUninitialize()


def 교정용_hwpx_준비(path, folder):
    """Return an HWPX snapshot; HWP conversion touches only a temporary copy."""
    source = Path(path)
    if source.suffix.lower() == ".hwpx":
        return source
    copied = Path(folder) / (uuid.uuid4().hex + ".hwp")
    target = copied.with_suffix(".hwpx")
    shutil.copy2(source, copied)
    app = None
    pythoncom.CoInitialize()
    try:
        보안모듈_초기화()
        app = 한글_COM_인스턴스_생성(독립=True)
        if not app.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE):
            raise RuntimeError("한글 보안 모듈을 등록하지 못했습니다.")
        if 한글_문서_열기(app, copied, "HWP") is False:
            raise RuntimeError("HWP 파일을 열지 못했습니다.")
        if app.SaveAs(str(target), "HWPX", "") is False:
            raise RuntimeError("HWPX 임시 변환에 실패했습니다.")
        return target
    finally:
        if app is not None:
            try: app.Quit()
            except Exception: pass
        pythoncom.CoUninitialize()


def 분석용_hwpx_준비(path, folder):
    """분석할 HWPX 스냅숏. 확장자만 .hwpx인 HWP(ZIP이 아님)도 HWP로 보고 임시 변환한다."""
    source = Path(path)
    if source.suffix.lower() == ".hwpx" and not zipfile.is_zipfile(source):
        copied = Path(folder) / (uuid.uuid4().hex + ".hwp")
        shutil.copy2(source, copied)
        source = copied
    return 교정용_hwpx_준비(source, folder)


def 스타일분석_파일생성(경로):
    """문서 스타일 전수 분석 보고서(.md)와 예시 서식 HWPX를 원본 옆에 만든다(A3).

    HWP는 원본을 건드리지 않고 임시 사본을 HWPX로 바꿔 분석한다.
    """
    source = Path(경로)
    with tempfile.TemporaryDirectory(prefix="docfit_inventory_") as folder:
        snapshot = 분석용_hwpx_준비(source, folder)
        inventory = analyze_style_inventory(snapshot)
        inventory["source"] = source.name
        report = source.with_name(f"{source.stem}_스타일분석.md")
        sample = source.with_name(f"{source.stem}_서식예시.hwpx")
        report.write_text(inventory_markdown(inventory), encoding="utf-8")
        stats = build_style_sample(snapshot, sample, inventory)
    return inventory, stats, report, sample


def 스타일분석_요약(inventory, stats, report, sample):
    s = inventory["summary"]
    줄 = [f"문자 모양 {s['chars_used']}/{s['chars_defined']} · 문단 모양 {s['paras_used']}/{s['paras_defined']} "
         f"· 본문 스타일 유형 {s['types']} · 표 {s['table_types']}종 · 글자 음영색 {s['shade_colors']}",
         f"예시 서식: 본문 {stats['paragraphs']}문단, 표 {stats['tables']}개", "",
         f"보고서: {report}", f"예시 서식: {sample}", ""]
    for t in inventory["types"]:
        c = inventory["definitions"]["chars"].get(t["main_char"]) or {}
        효과 = ", ".join(t["effects"]) or "-"
        줄.append(f"{t['marker']:>4}  {c.get('font', {}).get('hangul')} {c.get('size_pt', 0):g}pt"
                 f"{' 굵게' if c.get('bold') else ''} · {t['count']}문단 · 부분 서식: {효과}")
    return "\n".join(줄)


def 서식프로파일_표시이름(profile):
    """서식 목록에 보일 이름. 기관을 지정한 서식은 '[기관] 이름'."""
    기관 = str(profile.get("organization") or "").strip()
    return f"[{기관}] {profile['name']}" if 기관 else profile["name"]


def 문서_markdown_내보내기(path):
    """HWP/HWPX를 같은 이름의 UTF-8 Markdown 파일로 내보낸다."""
    source = Path(path)
    target = source.with_suffix(".md")
    if source.suffix.lower() == ".hwpx":
        validate_hwpx(source)
        return export_markdown(source, target)
    if source.suffix.lower() != ".hwp":
        raise ValueError("HWP 또는 HWPX 문서만 Markdown으로 내보낼 수 있습니다.")

    with tempfile.TemporaryDirectory(prefix="hwp_markdown_") as folder:
        copied = Path(folder) / "source.hwp"
        snapshot = Path(folder) / "source.hwpx"
        shutil.copy2(source, copied)
        app = None
        pythoncom.CoInitialize()
        try:
            보안모듈_초기화()
            app = 한글_COM_인스턴스_생성(독립=True)
            if not app.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE):
                raise RuntimeError("한글 보안 모듈을 등록하지 못했습니다.")
            if not 한글_문서_열기(app, copied, "HWP"):
                raise RuntimeError("한글파일을 열지 못했습니다.")
            if not app.SaveAs(str(snapshot), "HWPX", ""):
                raise RuntimeError("Markdown 변환용 HWPX 스냅샷을 만들지 못했습니다.")
            return export_markdown(snapshot, target)
        finally:
            if app is not None:
                try:
                    app.Quit()
                except Exception:
                    pass
            pythoncom.CoUninitialize()


# 문단 여백·간격 COM 항목. 복사_문단모양은 HWPX case 값(실제 HWPUNIT)을 담고, COM ParaShape는 그
# 두 배 값을 쓴다(실측 2026-10-03: COM 왼쪽 여백 2000 → HWPX case 1000, 줄 시작 위치 1000).
_문단여백_COM항목 = ("LeftMargin", "RightMargin", "Indentation", "PrevSpacing", "NextSpacing")


def 복사_문단모양_적용(symbol):
    values = 표준서식_설정.get("복사_문단모양", {}).get(symbol)
    if not values: return
    selected = 표준서식_설정.get("스타일_속성선택", {}).get(symbol, {})
    action = hwp.CreateAction("ParagraphShape")
    params = action.CreateSet()
    applied = 0
    for key, value in values.items():
        if key in ("LeftMargin", "Indentation") and selected.get("indent") is False: continue
        if key in ("PrevSpacing", "NextSpacing") and selected.get("spacing") is False: continue
        if key in ("LineSpacing", "LineSpacingType") and not 표준서식_줄간격_사용: continue
        if key in ("PrevSpacing", "NextSpacing") and not 표준서식_문단위간격_사용: continue
        # 예전에는 case 값을 그대로 넣어 예시 문서의 여백·간격이 절반으로 들어갔다.
        두배 = key in _문단여백_COM항목 or (key == "LineSpacing" and int(values.get("LineSpacingType", 0) or 0) != 0)
        params.SetItem(key, int(value) * 2 if 두배 else value)
        applied += 1
    if not applied:
        return
    if action.Execute(params) is False:
        raise RuntimeError("복사한 문단 서식적용 실패")


# 계층별 추가 서식 값 → 한/글 COM 값(실측 2026-10-04: 정렬 0 양쪽·1 왼쪽·2 오른쪽·3 가운데·4 배분·5 나눔,
# 밑줄 1 아래·2 가운데·3 위, 한글 줄 나눔 BreakNonLatinWord 1 어절·0 글자)
_정렬_COM = {"JUSTIFY": 0, "LEFT": 1, "RIGHT": 2, "CENTER": 3, "DISTRIBUTE": 4, "DISTRIBUTE_SPACE": 5}
_밑줄_COM = {"BOTTOM": 1, "CENTER": 2, "TOP": 3}
_언어별_장평 = ("RatioHangul", "RatioLatin", "RatioHanja", "RatioJapanese", "RatioOther", "RatioSymbol", "RatioUser")
_언어별_자간 = ("SpacingHangul", "SpacingLatin", "SpacingHanja", "SpacingJapanese", "SpacingOther",
              "SpacingSymbol", "SpacingUser")


def 계층_추가서식_값(values, 장평_사용=True):
    """계층 추가 서식(예시 분석값)을 (글자 모양 COM 항목, 문단 모양 COM 항목)으로 바꾼다.

    영문 글꼴·장평·자간·정렬·줄 나눔 기준은 예시 값으로 맞춘다. 기울임·밑줄·취소선·글자색·음영은 예시가 쓴
    경우에만 넣는다(예시에 없다고 정리할 문서의 강조를 지우지 않는다).
    """
    글자, 문단 = {}, {}
    latin = values.get("font_latin")
    if latin:
        형식 = _글꼴형식.get(latin, "TTF")
        try:
            타입 = hwp.FontType(형식) if hwp is not None else {"TTF": 1, "HFT": 2}.get(형식, 1)
        except Exception:
            타입 = {"TTF": 1, "HFT": 2}.get(형식, 1)
        글자.update(FaceNameLatin=latin, FontTypeLatin=타입)
    if 장평_사용 and values.get("ratio") is not None:
        글자.update({필드: max(50, min(200, int(round(float(values["ratio"]))))) for 필드 in _언어별_장평})
    if 장평_사용 and values.get("spacing") is not None:
        글자.update({필드: max(-50, min(50, int(round(float(values["spacing"]))))) for 필드 in _언어별_자간})
    if values.get("italic"):
        글자["Italic"] = 1
    if values.get("underline") in _밑줄_COM:
        글자["UnderlineType"] = _밑줄_COM[values["underline"]]
    if values.get("strikeout"):
        글자["StrikeOutType"] = 1
    for 키, 필드 in (("color", "TextColor"), ("shade", "ShadeColor")):
        색 = str(values.get(키) or "")
        if re.fullmatch(r"#[0-9A-Fa-f]{6}", 색) and not (키 == "color" and 색.upper() == "#000000"):
            글자[필드] = 색.upper()
    if values.get("align") in _정렬_COM:
        문단["AlignType"] = _정렬_COM[values["align"]]
    if values.get("break_word") in ("KEEP_WORD", "BREAK_WORD"):
        문단["BreakNonLatinWord"] = 1 if values["break_word"] == "KEEP_WORD" else 0
    return 글자, 문단


# 서식 복사 간격 규칙 상태(표준서식_전체_적용이 문서마다 초기화). 정리할 문서에 제목 표가 있는지는 XML 단계가 알린다.
_문서_제목표_있음 = False
_간격규칙_상태 = {"첫문장": False, "직전깊이": None}


def 복사_간격_규칙_적용(symbol, text):
    """서식 복사한 간격 규칙으로 지금 항목기호 문단의 문단 위 간격을 정한다(복사한 문단 모양 다음에 부름).

    - 제목·개요 표 다음 첫 항목기호 문장: 예시에서 잰 표 아래~첫 문장 간격(빈 줄 없이 이 간격만큼 띄움)
    - 깊은 항목 다음 얕은 항목(계층 복귀): 예시에서 그 계층이 복귀할 때 쓴 문단 위 간격
    """
    깊이 = 서식요소.ROLE_DEPTH.get(보고서_문단역할(text) or "")
    직전 = _간격규칙_상태["직전깊이"]
    if 깊이 is not None:
        _간격규칙_상태["직전깊이"] = 깊이
    if hwp is None or not 표준서식_문단위간격_사용:
        return None
    값 = None
    if not _간격규칙_상태["첫문장"]:
        _간격규칙_상태["첫문장"] = True
        if _문서_제목표_있음 and 표준서식_설정.get("제목뒤_간격") is not None:
            값 = 표준서식_설정["제목뒤_간격"]
    elif 깊이 is not None and 직전 is not None and 깊이 < 직전:
        값 = (표준서식_설정.get("복귀_간격") or {}).get(symbol)
    if 값 is None:
        return None
    action = hwp.CreateAction("ParagraphShape")
    params = action.CreateSet()
    params.SetItem("PrevSpacing", int(값) * 2)       # COM은 HWPX case 값의 두 배
    if action.Execute(params) is False:
        로그(f"[서식 복사] 간격 규칙 적용 실패(무시): {text.strip()[:30]}")
        return None
    return int(값)


def 계층_추가서식_적용(symbol):
    """예시 보고서에서 복사한 계층별 추가 서식을 지금 문단에 입힌다(서식 복사 전면 복제 1단계)."""
    values = (표준서식_설정.get("계층_추가서식") or {}).get(symbol)
    if not values or hwp is None:
        return
    글자, 문단 = 계층_추가서식_값(values, 표준서식_장평_사용)
    if 글자:
        hwp_run("MoveParaBegin")
        hwp_run("MoveSelParaEnd")
        try:
            action = hwp.CreateAction("CharShape")

            def 실행(항목):
                params = action.CreateSet()
                for key, value in 항목.items():
                    params.SetItem(key, _서식통일_색값(value) if key in ("TextColor", "ShadeColor") else value)
                return params, action.Execute(params) is not False

            params, 됨 = 실행(글자)
            latin = 글자.get("FaceNameLatin")
            if not 됨 and latin:
                # 영문 글꼴 형식이 이 PC와 맞지 않으면 다른 형식으로, 그래도 안 되면 영문 글꼴 없이 장평·자간·글자색
                # 등 나머지라도 입힌다(예전에는 한 번 실패하면 계층 추가 서식 전체가 빠졌다).
                됨 = _다른_글꼴형식으로_재실행(action, params, latin, ("FontTypeLatin",))
                if not 됨:
                    _, 됨 = 실행({k: v for k, v in 글자.items() if k not in ("FaceNameLatin", "FontTypeLatin")})
                    if 됨:
                        로그(f"[서식 복사] '{symbol}' 계층 영문 글꼴 '{latin}'은 이 PC에서 입힐 수 없어 빼고 적용")
            if not 됨:
                로그(f"[서식 복사] '{symbol}' 계층 글자 서식 적용 실패(무시)")
        finally:
            hwp_run("Cancel")
    if 문단:
        action = hwp.CreateAction("ParagraphShape")
        params = action.CreateSet()
        for key, value in 문단.items():
            params.SetItem(key, value)
        if action.Execute(params) is False:
            로그(f"[서식 복사] '{symbol}' 계층 문단 서식 적용 실패(무시)")


_제목2종_XML = 'eNrtXVtvG8cV/isL5SUBapF74U1oDZAUZdGRSEGkrLgIICzJIbnWcnezOzQtFwWMJC0SuHAQ1EkU1A4coEXSwA9B7Ie0SP9M8mZK/6Fz3Z0lKYuyRIm2xhYgneFc9sw55ztnzs4M/7TQBWYL+AtLysLvu90lTCl3erYTLHWbf3h/oQuht5RIDAaDxa7pNN3eYtNd3PUT3YHXsxNaUlUTTdcH7y/wRt3pGuFxokbedI080zc7vul1UcvbwA8s10EN1UUD0QFoFh2IyfcXrmJOGqBjOZV+T/HMDqDlStt1oeNCTgKnJVCe1WR/wYbNa3zQNyEbBpEJ0rMP2mtWAMnfbdeBbbMJAsWCoEefIMOegH+m2KbTQeWr+cq1rTXyGA6kVdNCVcVqoZIk/hw1Qn8OP7t/8I97+Hn2PEzX6yuIsIJSrwFaLcBqk/a4Rtlpu6hpz7L36rTBSjFf37lWra+Wi6jhAFidLhtU8XzXc33GGh6ziZ7ANwPIyAD67i64YfqWyL/p92pwz+YzZgMIgd92/R4r6Fkt23L4x3dW+Yhs7hKM0xGW1Yjlwy++P3j+yfDbp+fGu3GxvGuTeP/x4eFHX7z5vOsC74+eD7//ZfjDXw6+/fHsGU/NGeNGxPjqzcOv/jn8+6Ph418OHv+8/uYbeyri/eD+EyRx5cVPT188ezJ8KGj86kr9TJhPvhLzyTjzyVHmkzHmkzHmk6PMJwRHMNErrOXr5Yp0CtIpSKcgnYJ0CtIpsKXC9bx0CtIpSKcgnYJ0CtIpYKdwPb+Rr5RqJekXpF+QfkH6BekXmF84/OjRZfYL6KFLmzGnkJoLpzBiI9rEqdLiU6WNTpUWmyotNlWGdArSKVycU5g3hb9Qp3D+vB+Li7Wb64WqfN8qgVECo4yWZbR85lmU9ZtblWvXq69buLxVm8toWToF6RSkU5BOYUa8x2FRpAK6XdL1W8BfsWxb3MrI4+Xo08hiYNcHYJk/fddsuQPOGXDQU67R56pUKzhj3fCBuVsEtl0DeBsnBGshmpMRAtsMunzeWZui76Ip4YBsBUW3jzuOUB8/mdncrb1iWxu0YYFwNtJ4YLUg3siaXFSVXo/IynZx27eS5F+0FRRP9+m6gK53ug4aLoRu73R9tCyz4zqmzdvXqmvl5ek7aC61kWoU/H7QJdTAcghBDKzImjiug/cJd03Y7PKyt3LkH1Z02+uaoj+P9ZmI6eBEldTfUJWcIArtxEp58k7G1PLkXUxSzJP3cjrVnEJxjMuCZVrq9GB2XB9TqI1xJlqTumCtSUkPKD3gWXjAsJtTe8C0BLKTOMDTI9lxXUwHZcYFI1nm8gRO8+EAX0O1idN0xdjsmv4GWtQCtKiNnX9TuR7QGlTLshj4+OpUy5CBILgDx3EQq98oZPYDsIKWqzWPLtiTtOhd4DsWyemRdnu9ddPfFdQ0fODy8iZoj2T6UAlCYqfTt3nKEa27+docfXCLY/Et0zMdEPBxXdgNVQ8N2XDt6IHiKunjhXw0hpoUR6EUH4dSwki0gI9FqXA0SrLxVEHoAZofNCGz5gvYtbvnypfbbgcAzpgt9FGL/dl3kOLgvMoIDCDVjBnTUcYXQN/aBW4fhi1YB0c1QFUnDMc6I3A88lHYUUHD/zGjZI7eY/bHyJucZDZNLXLMOHNzbZyGIG1DkLYRl7YhSNsQpW1E0jakcUrjfM2Mk1QJrVPVpOs8F+u8ogpDEoKPSAhhQELz8QgRDkcoNtoV9U030ktnmepcW6YuyFgXZKzHZawLMtZFGeuRjHVpmdIyXyfL1GOWmZIRrYxoZUQ7N9ZpyGSQtE5pnXNqnSmZDZLWKa1zTq0zLbNBcs0p15xzaJkZmQ2Sliktcw4tM3vpLTMnKlJO1KTciCrlRF3KxZQpJ2hT7qUmqcVsUosZpTZqlVrMLLW4XWqiYWrSMl9zy0yMbRyiu6bMxuStRPy0Df48Optn9qFbNxtroA3jJZvjpwJjXZPO8J61iaMZbDRagZ10IViB++B2zM7utIATChibNN4DFzuVGDimV3ev+eHxuqDveT4IAlyz0u81gB/w7rqguRs7XmTaVsdRuq5v3UV9m1hhrm/V6uWVm/Tuc2g1SWEhXyutlQWh4YvVsTHGpWa1ome3wW1gx5dTeD9fDUCIGxJiDSv2NoIwVO/dUmljZ7u6ucx3/lVc56jPBxbSmKrvIWNgI+wC4G1bsFtBcCsU4Tng3OML2gu44wJou354AhTV2PZNfDV8YbOUfzd8WizqGoMckA8s0ymFMExpNLkCf95SMLBgs0v+bJoBUNBvH3zQt3zQuuKYPRAwZD/2Cvp0YnXgbTkWLCIVZpLqmX7HcsimX8uBwIHKbdPuh44CVcYnzLY3tirlerhZGO9WnKYe2ZE4TUWkWLenqecgMRxbLyGy1V3CkuATztRqo7RZLFVwdd6XahzdG512Mv8t0Db7NpQzN+3MhROWEBWZ78acEGZEkCzAIy0Q0ZGW1F0vRhfI1tMI5BzQ5A0QHiHjXCfMxRGWwuU4cqrzgpx4wsmZ7/kCTgJrEjkvvf3rEjlnMXOvMXJqEjklcs4UOfXk1Ajw0qqXEz3T089eOikR9AIQVJ8XBF0u1+qb5cJWvSQX7hJE5xUG0hJEZzV7JwbR1IWBaGIsOUrLxC88RMblIQxp2GDZbfZ7WPAQdQkgatTxzR6dAmRy7zEzs809tw+LrJllW3AvTAqP9UWPrrrNqofvQOIi2LXwRUuoKj64ynCn7HSBb8EQyukXO8ZL2TDx/qBvNnebXdRF0XXaVkdp22YHI1oqHTXBYHx14XfKQoDmD7WkX48ZLCHyFN9ZyVoG07VkQ5Np9JY8dsuNqqlqLpnMZck8YFmFzpdsc8KXRYk+L8ToUCfsfs8RS3oAiS/yYghi+45Cc/S8I/zihQIyaHIXy16hLSMwbrILq1arm+U/Viv1PL50lWBzkYwWkLMSukF9cg0Snc3S1xCs4AZxikasbGvUotjLihp+tRE+GuGg58YK+fu9G8zfbuNDz6tIppxlM4DA38A64ECB8w5y+8R/Mf9PvbzpC+TAdTod95a14vo9E8a9FTIEyL9xtIaJoIqnpVCtrzJJcKGQrxpNhl81mox/1WjU5W0r4DbTtVpgxfIDuEq+sJW/deKlK8gCxkvXQ0bZJxRu8Juk1er2Tn6NXI+LwCdeErbHLSOnHBaXeh7ciw79K0HXHUTxUYwDOywmElJQKIVnht2XRjWy78DCHqNaCGiQQYQ9szkd7RZPJtJE23RaQZO+6douL5fWbgpH3FO5lBZ785s11Cw28k4f36LGHmGttFLfqVZwS9IzRX+ly2dZp86nzeeX0bSPMDIjQJ1SkzgC9vmNd5Sk6s6aNTg+M5o5CcoOGR8PVEFjMRIHTYh/qm7cBy2XrxGDwO8PcUTDYBHhtHUnooN+O6LfoaFs0PQtL662GDex8BAXTodMHNkB8YoXNtH+uM9sADgAwMH8YBDQsjgubwCbqgsBXbxrxmy4t/klEtmU0BURvOB8iwhdypWt6lYN1XHAgOqmGqmFjUCHOCXyF/qslC+u7hSra1vrFTK0A5AbqUcxLRPAyKwDp3XBMlCNdE7TDWNGkkieuxwqyzvVlZ3lanFrnYZPR8oiPvnEgUVXlrAHYJg6Hj2pDPoLHOg28hskg0UNuuwECMSEqGG0CHWVR84xakgegr38Z3auGmSvF7dzRlI7Z0Ro54wW7LwgXsdyFH+lG6XKm8xfdXn5DWAvwUMiukSFPmUZ2aMYJbEFfWm7xpmhMTFzPtSAyZ02POWAlra1uwJxzfTiJkKHStBg7bigDV59e/js+YtnTw4+fqQcPHk0/OHfysGjJ4f7X6jvkD5gvCvssgPQMX3f3BMLiGA8l8MHTmbEqcC6S9ZD0ZGBaNMVLWugpSS/r9QwUixMpNuosimyT8j170a9Yor1auR0EuHycF1HtJqOpiT+1ERaYuCcvJB4GYV3/KhwLqPqmWwO83i3ypQbEyG2snikni+sldj0sTRKvbqxk0f4iUCvXl1nn63Y5I4mDIQ7NRT6YCS23SZ/yhZaw6HAKGCXx1boVjaRu2KJxHo+8BAMh0ElVjnfHdC4WGO6GRH40qdQYsmJJoxdvOPmW7f6gRhbB3dDz2VkM6ks92SbwK67qDBfQA6OpsmigE3LRUesJ1T0fIQAzbgrRcqjQMQizAfM7ZJ7dNttVHEt/uxtNIU4xcVcEKlno7IqUmY7NLmua7fyThOpYt5p1aqCvvMn2shv5pmyjhThWnmcFKRSZJV4CbN+XKlKEErQ+lgB5QxBBl29cyCj4RTHMUpRGGOBFkcxStJeLCfeCUK4OBiKWDgChWEnkCIebCo4DUdxrhtbl5hBLNMQlxRoWWiNF1723rJ8uHekPhlcgfoNnIWYbvU5IQkpyiJ8r4WzC7hXEQJ4Gc58jq4ot3nwxehY7hgxjVUpaoEKUGQU0iIeaaqRMbJ62piwkFdnBkzZ0CX8em9/EvaPN8mFTQ4+fDr85vODx/vKwf73w88+Pvzo8+m6EEf9WjnxsMhjfffp4ZefovGVFz/dO/zrE+rOZuG7tAm+SxvzXZqWG/Fd6st9V9bIpE/quxKRztOoAmFvvtXyseTxbzYMAmuBSoRVEdQ5uCr+zdAbVWWUGq86Ds0h82mdaGhU+bToQYTWZL/9c0eT9KVDE212YU5SNOzp7FpVwzaatqgYi4qaW3z78OuHswlFtQmhqDYWiibJLt/InPV0MmbO9O2NYNAZOtOztWf1ZfasTmfP2ZQev6QmZ+gzMefzst/MpbNffXb2Kzjmr+6jnxfPfjn45l+J4f3nw/v/efH8HslHDsjBFyTrpTj561cP2M/+A03V9Ss496TQjg7/dg919PLmXz5jP/sPVE03FDrqMW3+x372H6TSmewcQUZGOwYyEEYYxgwwQz1zzDCSmpY5F9DgMUCCLpWpLvIKryxQLUUyCYJMs9lUZlSmrEyQaYa+LnjDMxJHJoO0s/HAqqalVZkQmjYhlM2JCaGkTAjJhJBMCMmEUByYkrMDJj30C4ry270Hh4+fDr97rCU1XRl+uD/85OHBf58cPtg/ePzzb/c+m0m4lZrgG1JjvkHLxH1DOpk884TLRSfnVOPk2Tk1dfr0XGzcafNz4sAzTdBp9BC2zNHJHJ3M0b0CqKRfIUeXkTk6maOTOTqZo5M5Opmjm0mOTjWy5I5umaQ7WZJOPxsXrBkpTZNJuhNPv3E2068bKXLaZN6n/2Uub7ZyEE4PnGhm0fzk5nc7YoIeIbq68Of/A5pHzFc='

# 첨부한 제목 표의 원본 XML을 내장한다(외부 서식파일 불필요). 제목 유형은 2×2 제목+날짜·담당자 2종(1·2)과
# 2행1열 제목+담당자(3, 별도 기준표)이며 1×1 제목 표는 제목 서식 대상이 아니다.
# (변수명 제목4종_사용은 설정 호환을 위해 옛 이름을 유지한다.)
제목4종_사용 = True
붙임2종_사용 = True
중제목_사용 = True
중제목_번호굵게 = True

_개요붙임3종_XML = 'eNrtXf9v20aW/1cI95c94GzxuySjl4Vsy7FT2Qos+bI5FA1oaWSxpkguScV1Dgt0tynQRQ/XLc65ZvecIMHtXbJFgHW/oDD2uv9QJP8PN8NvGoqyRclWRFkvBWrNcL68N/Pe5715wxn+60ITKXVkLSwzC+//8pOWxjxElq0a+j99uMAtsR8uMEivGXVV38cZu9X1xRzOsh1FryuaoSOceYRsnPXLW+83m8ukLQY3otvLTQU/azqOuZzJHB4eLjUV3E5rqWYsHViZ5qHZ0jI8y3EZxTRxdb+OmayOqVjKvqWYTaomxyapKw+qayfr1UY1Bw9Mr14tWb2aYaFepWaySmQkqUoJSWyqtmNYR72KrWT1WortIGvRVPYpSs3GJZXtWhO1FL9XsxHWqlODYrYtbcmw9jP1WgZpqIV0x85wS1wmLG3096HWzYZbhWfZbAY/psoa+G+tqVhOsonule+xdGi2ddUhmcna2Dg0d3GFVVwhbASZ7b3LibbDsjVDb6hEc9qWvmwotmov60oL2ctODfOO9LpRa5NhWaaLL3t6R+uhSJQO1VZ1wjv34YKrbHtoX9W32y2GTJuXzzQMw9ENJ0jiHqiUqdb8X86eFpT4dVtx/G4+XMi4DVuoUcKC5P5uGLrTUGrIZlQHtTwCsj4BwTNGU1x42Chs394tuVTojlc0RxVl1DrOIayRSvhn56svu//1KSHnyCTpanUdJ1S72NpD9TryS7v1SYlNvWHgqi1VO6p6FdZXC9UHt8vVjc1VXPEQqftN0qlMeLUM07B8zkifeGwdC4u5n7QdyzhA/6xYKsU+o1itinOkBQOmIQerRcOwWn5GS61rqh48/mQj6NEbuozPaB/HHMXxq6+7zz5l3v7wonP85PoZl/oZF6KM8wMZZ6OMs/2M8xHG2Qjj4mWM8z3Gz5+cdP/vxzmZcIHm+3X3xy86L9+8M9bFqbIuDmL99Pj8syc3nnWJYv3kx87rnzvfft59efoOtHy6fMs9vjfun3/z585/nHSe/dx9drZ14xU922O9++ULPN/M2+/f9IP7xnr1Wnhnx+J9GLizl4A728d7hrL5Ax2AUqG6uQ32H+w/2H+w/2D/wf6D/Z8r+79R2L5TAPsP9h/sP9h/sP9g/8H+z5X9v1O4W9guVorgAoALAC4AuADgAoALMHcuwPlnJ3PsAmCaizsR+59Nhf0Xk5hBPjpS/OVmkE9uBsH+g/0H+w/2/4bC21Tt/ztnfagNrNzfWinDe3BgBMEIghEEIwiLYIiDj70I3rq/u337TnnGVsG7lVQugsH+g/0H+w/2H+w/2P8rsh41gXTK9g6nGVYdWeuqptEnx7jw7Fr4uGcbnKaF0FpAfVOpG4cBZ0jHVJY8urbL22SDec9CysEq0rQKIkc6HVQKcdntwdYUuxmMu19n1TLwkATWV7VXjTZpOLTwhDCldlAZr6qGGs6Ky1df3UO17pBjn+wSx7Ra7kxpBqn6Huv+C8/dkbG+UguOYV6p/p7hOEbrSk3UVWXf0BUtqF4plzbXktbPRERjoKTwICkgKbh+bbmBZWLFattNN3Wo6m7CxeBVv4Zu6ORAc1Nxas0g7728+49goWa6p9QD2Ys0mUAUhRspigOmgR9VGEduIyaOI7cwSCBHbmTS4CXOB3jx0pXRa0gTCeRFvA5xkaYqLhLYOrB1V7J1QStXtnUyIFdiU3dl6BrSQjLsEqcKXdl58Y3SYOpugLzkQF5mDWAm6RwlM3nvra8U19fEyVm9PDhg4IBdyQFbX782YeRYwMiJxRvi4sRfg0hON9rAcXMiMOLV5UVMQ7hBnLpBXVsvyuvZawqZRtPevhC5e/GuZZjIctTIpYJ8IGJeid5LEs1wC8qDUQd94sQtPZHsfiRu22jd0J2K6e3KsV7WB8jSvetM3XpHrS3FOqA0ICR4c20HNbwdh3CrD+fgodH325ofzdMURw32HvGDjxX/98eKqejIRn7ScJquWItel3tGUB8TZIXvDxBhJZt1vS44l7mgEy8VdOOlqI68jKArLxV25iX97rieVNl4dPBw9LqkO6S76+uM7irSEdVNTwWRVnn0LrkyGg0bOZNlqq1jQSGbpX2ghkUxop8XqLPtWOoBMtpOWMGvf0F5XDLemd+UC+t9ZITNrPDkP8KZOyi/ClwJL3nfT/omxdO+mCJyqVZEgZpdgZpdITq7AjW7Aj27Qm92BVBEUMQUKyJPK2Ie9BD0EPRwGnoopFkPwTEFPZwTPRTBHr5rPVyUqB7dRNChm6D6c9NBd24i7M1N+Z2R36CON0Idpcg6UY7rI1/MiisS6CPYRVDESSqiHFFEDgwjKCIo4jQUMRtRRGk6iihdpIgyNbsyNbtydHZlanZlenbl3uzKoIgzp4j4SX3+VDJHqySfTZlKTkR4QSVBJdOskvlUqyRYSVDJ+dvyj758w4OZfBexVY6OrXJ0bJXri61ydGyVi8RWOSq2ysFK8qYoJJdqhaR3BehNgb49AXpLILIjQG0ISKCQoJAzoJCRl3G4KXmt3EUKmaWmN0tNbzY6vdmL3gLIwlsAoIkzoonCvJvGPC1CeVqG8n1ClKelKB8RozwlR/nLbCIfMYp8xCry/WaRj9hFPmoYedoy8qCQN0UhxTSYxjwEdMA0zrAmhjpyFU0c+krOVJ1U0ETQxHmxiTLYRNBE0MQUaGL0pRwhronetQ1T0kQ65EhHHPsCjnS8MRJupKKNXIoiqTTALNIIs9gHMYs0xixGQGaRQplFGRTypihkLtVvydHhDjrY0RfqoAMdkTAHFeTgwTTC/v9s6GQedBJ0EnRyqjqZiV2Z491HpOwNvERHCD4mQZ73rtBR2o5RVfZKqOFEc3YiHziKVuRiFblkFfkkPfa+JxHhxW1Lb7f2kIX1IvLpCJ+18GGPSttRLIe6pIrcXLWBlHr4wPvSxUMUOMeKpu4TYSwV3W9SYdna1G3nnn+PUsDmJhasoGvvkqVC/eN2+H0NAoVld+78b3XcLe6sFrerkUcEwUhhTPW6YbUUkrG2eXuTlPLmNQA6kc+LeTnL5yX3EaodKHvBd4hufcQtuWMVcDacTX7qbG4Utm/vlh5U7pdKhZVScUSG+VEZFmZyXoV/GJFNccbnVRyVYWkW5/UXH0mj8inP9sT+4iN5VI6zU+d4dXNntVRcezDiDBNT9FF2RG5zqeF27Hl2+c6NyHc+LXJ9p7BVHkmmMwmcCXbq3O2UtwrbDypbhVJppJn0va/QnepL2iHzg29rzFG+Fu1qut5c0L//VTLMeOjgk3UcuVOU/rYmY+uKWTVuWz2Prm2aFrJtUnLbJckOmiNcRD6c5g4/0zQs9RFuWyHTcme3Ut1cv4+LPySU19zMlUKlWNrseetNPKnEjYy662q9R3owy71FB7kdtYIch9RzEyWyrLmHV6242AfF4t0H98o7a8E9qtuGftFzLADGYdky8VLI7+wAIfOe6jS38WxTWWQEAt5NZR+tkIZXUMOwwm9U4hL3LMUkLO4UCx8ExBKhq/jrS1SwVUUvhgtvL41HtseduWwfqk6t6f6sKTZi8F8L/bqtWqi+qCstZPtL+abjmMuZzOHh4RImv2a0lmrG0oGVaR6aLS3Ds5yc2Tg0d3XVWcXS6M9SS7H2Vd29eVTVHawJzENFa4eRAVyYaOq9u7vbBIm9C0vJ1a8Jirn3uyYohyXqYYJiOp6AYcUyNEfNZTIFwVA7/eobNMXJFzbmDbg78nXUUNqaA2M2fMzCocrQwhtcOTv4JQR/tU2tS70Maj3r51QNM5JecW/w7YGajmpBBYw/WB23XN4iXwv2wDGGkxzgJOAk4CTgZEpxkk8JTvKAk4CTk8JJf0MLoHK0YRNYFtAylWgp9KMlF0VLPtVwWd6tek8BMVOLmCwg5hjDxgNiphQxxRuMmBwg5vQRkwfEHGfYREDMlCKmdIMRkwfEnD5iCoCY4wybDIiZUsSUbzBiCoCY00dMERBznGHLAWKmFDGzNxgxRUDM6SOmBIg5bvgXIDOVkJm7wZApAWROHzJlgMyxIBP2ftIKmfkbDJkyQOb0ITMLkDkWZMLmT1ohk4PzPZfipYtmAJjz+xK2BC+uX+uYzS5Swgkf8CxHB8pFTuDmRvGF6wPLRV7mYdxmGjBTc9THP8QPfiX4lTcRKmHMZhom03PGB3AScPJSnfc/wpRA7QUWTo9TA8eLSQdOZiFmOQwxY2d8eHAsATBn2EnKAlqOMWqcCFg5FCslwErAygmdHedYgMuxjpDyLCBmahFTBsQExJzQ2XEeEHO8A1EiIGZ6EXPY6R7YGYed8bFVPw/vXI7lnMNhyNTiZQ7wEvBykje6AWCOd68TAGY6ATMPgAmAOSnAzAFejmVn4H6i1N6xDod6AC9v2BZ5joVTPWOEL2UWDvYMQ0s42ANoCW+qX6j0Irypfq1jNrtAmZoDPWS4izuwNw5ACUd64EhP+oBSAKAEoJzgdeoJ1f6ykvMHlnLicZNZAMx3C5hiWgBzbbNS3dlc2a0WYRUOmAnfoLgRmHmtmzxSWjBTgrAlACasxuHiNtjfuRwoZViNw2ocgHLej4vDa0PDgDILHiV4lBP8Qk9CtZdY2Awf6wvtlxaFLfHrgMzeb8Mk0IRsl1DbOdKQzagOaq3qjr9X3nvi4av7VqY/PoWdAk4RrcSpzunx+WdP3p59SjRb39/2crcNq6VoLmyQ/iKvvmO9jKI0mbYK6YrO1BR9f3PNFQyRjJhm1A7Wcas0JFL0cRfS98NZ581ZhLgVo34UI41PRho3Omn8RaS9PT3p/umY4SLEldsOkUk3N0qhkIxCfnQKhSEU8gMp5GMUiskoFEanUBxCoTCQQiFGoZSMQnF0CqUhFIoDKRRjFMrJKJRGp1AeQqE0kEIpRmE2GYXy6BRmh1AoD6RQjlGYS0ZhdnQKc0MozA6kMBujMJ+MwtzoFOaHUJgbSGEuDtUJScyPgdXsEBrzA2nMx2lMKIrcOAaFGwbb7GDcZuNkJpRHbgzjwlHWZXWjsNMjs/vt35nO91+cP40av7vYj2e8ZU2MUDZGJ3dd5vlCE9N5fdb53zedV3+IULmB10cDCOTiFPIDR3IME8NdYmN+2/3vnyP0rRuGoxsOilMYd3GEgRSOYWK4C21M569n/RQW9frVCBzDwnAXmpjOX447376OELiFWkacurgbJg6kbgzrwl1oXrqnrzsvP2W6L0463/4lQmS1vMpseGv1OK1xh0waSOsYdobLDaGVi5EZdxi5uD8mDyRwDDPD5YcQyMcIjPuLnJSQwDGMDM8OIVCIERh3Fzk5GYH8GJDIX2hgun972f38aYS8VcV0VEOPr1rYhIuCRKYlE64Gvd8WapRU24sF1IyWqTjqnobWjFq7RYIBDl5qIgevJvctpeWtjHmW+5W/eNSUI6PtrPrVVE11jvwu4k25FepGrexyGSzMD1S9YWCGnSZu3A9BbepNZKlOGNDzYDiS6/cSbc6xlNoBHqh9tGroDXWfaWjKPoltSXJYgwTlbi38I7Ng40U1rriwzCy8r9vsMk4zn7Q03V7GqSRBKC7jN4FpDCpyySqS+cXjaTbJMOJay2ZvAd4390R77H7DHMbpwhiB1m7pdE4L4WkLg5ikC6ut99t9Pnjm7GmBQ5TPcjlBlInoPCqTqEagDq43gSGy6klztbBSIuFMB0uhHxyslu8+KGyvPVgpV6vlLf/ZumYckuV4ubrxoLK5Vqz4MunTWbcMs6aYLoduSEFHffytFkslnGUhEymO5zL4PotlHHqxDO+wvUYlkKb5AR+/n3iExjWIRqH+cdt26HGyH5HYqSuOYo7L814s1WnuIK1q4MzCSqVc8l6/agYhZonPZ8P0gIKmheU3jOFk/Dk3bMbBTDoFm4QxfdKVRgOXLEWpb+BBJKHbqhe6dctpOK/8EFmaEgSPmoZWL+i1pmEV9Hql7OeSAHVAkg9BuMSjvixSqkDi3N48+oWCHOqiv7IboQp7tB5FMnzWMCZ4ISpG86JffI4Mt+UPl5dy3KiX93sviHh5Sb8ZVY+2wokc1YqX8lrxfoeteEm/Fcfy/9YC7HWnyhcklw3FpiNqfdOF6qqj7GlBuLGuWs7RhVJFPC9fjtp7BFc9vfKVYU21PMggQFre2fyX8na1UBoYYo/MSLgvSwCTtBrx0v08Eten813N9CU5SEc2RTDbRKB6NXAGXjSE6Qg08ZyYFXOCLMZXke62zKQwKhdi1K3uN6d4CYH/3/3ypPM/PzOdV8+7Tx4znd897Xxx3Hlzdv7HY6bz0+PuyeO3Z6ekQPflaffxd+dPnuI0g7Pxr+43b5ju7950nn/dffaU6T593fnq8flnXzPvZ7w+vL+YjgsJylMEYV/y1e/P//P3pEXS30/H3VdhL397cf7vT7vPztyOfjrpfH/cffaY6T75N7wUevvDC4Zw8Vdc6fQMF3f5+erzzos/E3J/eNF9/gfm/MnrC8gi4mKjfcWylKNIjjvJGFgo3Y+mbPWR/yJFIBIhiPl5e4qNSGuugci65ifEIo6VeF/tvWa9Q88k7TcsygKbcxHLs7xCXuBdBytzEZ2CHCGUl9wupk1rJj7Mbpbp//W122OKmJtCvW4RGSd//fHG9olKZXplMbjrpCz527NlVIouGzdH/WaHKn1VvPTErRb8sIIfe5ov82GhK8gix/MyF51jKScL/XPs51FzLOZzYmSOc31T3D/BeELF0Sc4jQ6ZlKcdMnGWHDLhGh2ybF7OJ3HI+HyOBYfsEodsPFdqBh2y3Bz6Y/IEIUrsuT+dn/7Yff7YTTSI9aohPMP8xFyW7AA3IBtzA0Sx3w3g2ctshJTL8jPkA8gciWXQQOcGACfhAry7NRM7fzrKTlBFpZi7fQWtkwdonRzTOsF937CndXn5UqXDWspOSOm4CSidJEsDnIuZ1jkBVO46VU7uWUWm+6fT7hdP8eq++93nOHHcffL37uMTpvv86+7j7/Cv7pfPkkcbstepy5OxoCKbl8UJaTM/iWU0x7vS8S70eZLL6DwvZ6MTLPBu3D4ywX4eNcF8NivM6SratUrhKlqapVU0f52raJEVYRUNq2hYRcMqGlbRN2QVDR49ePQz4NFz4NFfvDGWE3NSil36jP+e1K2F3/w/vK7F6g=='

# 첨부한 '중제목' 표(로마자 번호 + 글)의 기준 서식. 번호·글 모두 HY견고딕 20pt로 정규화해 내장한다.
# 기준 모양은 Ⅰ·Ⅱ 표(검은 0.5mm 테두리)이며, Ⅲ 표의 남색(#1D1E42) 변형은 쓰지 않는다.
_중제목_XML = 'eNrtXEtvG8kR/iuE9pqIb0oWEgNDirJo06QgjuJ1YMBozjQ5Y81Mz/Y0TUuLAAE2CwTYQy72KXvwXpIg2IOxcXJJ8mdytOT/kOrXPEhapqyHteLYB7F6uqu7uqq+qn7MfL3mYGRjurZVWPuV42xxqvDC94Joy7F+/WTNYSzcKhan0+m6gwKL+OsWWT+kRWca+l6xUiqXixah+MmabuQs14j3kzQKl2sUIorGFIUOtHyOaeSSABqW12tAR9hqBYyTT9buckmGeOwGvYlfCNEYy/LCiBAWEKZJHNgpKnQt9YsNPV3jqwliqhsgi4IzxaOuGzHxe0QCNkIWjgouw74cwYYagX5W8FAwhvJdo3fvoCuGEbD5qgXXhpISfw6N4Of7V9+f/vvtyZ++O/3z7/mojkJeapo7QLhR2x9i28aqjeDCa3SCEQEGvusdmbLBTsswn97rm7udFjScYnfs8K4bXGRKQkKVgLxnC8ZBUcQUGTFKDvFvEHXTs4CoP2BHnp43DzOG6YhQXxX4ru25gX78Ylf3qGawqOSdEbycFvxvp2//ePLDj9cme+3zyl5ZJPubl++/eXX7Za8msu8+fvfTj+/+8frk5avbb++1GblP/v7t6Q9vbr/c9UTu0+9eg9SFBcLv7pifIPzDxwe9e/f7aelLnyR9KSt9aVb6Ukb6Ukb60pnSN+akf//N97Mm/2nSz6v+BghfTMXBhUGxa5idXiYmNs6Kie/++fbkL//Jo2EeDfNoeEujoen6kE738LSwT3wUXIPs1azs9YWy17Ky12dlr2Rkr2Zkr+UR8VxBAVZK943lF0orGRRWaW1YWeFoWF3haFhb0WhYX9G1YSOPhDOR8L6xZ/Tag3YeDPNgmAfDPBjmwTAPhisbDEFl7f1MJKznkTDfK8z3Cq85IMzIXVkodyUrd+Xs/bLKOfbLVmyv8KOwOHj8sNnv5mcoOS7muJifoeQ3CvJE+WCQ58l5PMjjQR4PVjZPTlORvBBMqI3pjut5iy7rJk8TsGAOxXhba85BNplqreIARtmV4+r1e3x/fkgxOmxhzxtgflGZ4W4M5qKHyEORo+ddtWlRAlOi8diNWmTCGSegz0eGrMPBJ7b18Ig1hWQzjaeuzfhV7dJ6ueD7Qlce4W2/KIl/yWVnPt0XY8FIeDEGQ8IY8S/Gw3bRmATI0+0H/W5ne2kGxYyFLDSYSm4wucEkDKytEZhGk04iR1BTNxCEQOSWahKQgL864SBmObrsizviH0dGL3RQOv/L8FzCJKu5SeYmeRkmGbO5sEnWbqlJLlBF5dxGeX4mc2Z5fhaLDPOcXJbQe/1q9d5q90yx5L0Jmq9fguLrF9Z7/TLUXr+Y1hu51s8Vg+adbBP+Lx2EyuulOQY7O+cLQmfzWELnG7dW5+fW15Xo/AZ4epaWq2vLQXSPkhBT5mbehq0qLcoK0kY2eYahF/IV2Q/DL9h8wsGNZzY3mUR4B1b2g1DubZRk0QNMA1fsfop2R/5DRA9TRhaPt7O9j0epF4X5LgGUQMoTjCeeSps9xFy9jQEPniGVuzxDIQpwhBVJmCPMpiq7HBLdHgaky5Ut8D2PpI+ykE73Iindj6RSPckC3Zek4t4kqforp/QewfzAhCR9pntM9zfTW7qvTE+pflI2jr3B8bXKRUajCLMrFgse2ernJADD4VtQMz4MppnxpQ/5X8Soe4jJhMUtFIMPNYCqC7pTzASYzjyKGTUr/D8XVMzRl2LmYvKxJpVLS4+cc847uXPmznmjnXPVPFJU+ewuWc1dMnfJlXXJ4lyOK9NzNFyY9er4JZ4nJ+5owoiJhl1YW2RL9ufP+jOsBTO+Ojozx5YVku4EC+2/6jTSxkGsX+7KfLGVuWoQBSg0yT0aH4NFkzCkOIp4zd7EH2IaaXYOtg4zh4bIc8dBwSHUPQbeiNvL/YOB2dl5LL/Zw1xLFDaNQbvbSemMfxCIe19Waa6djN3Dz7GXTdL4wnGAGeMNBdHldv0IoAvqPWi3954+6u9v6yVmjwQfeg7rIDLt0xB8QfVwiHH4yGVOD2A2VcTnQEvPPyzU5IybeERofK0DajyiiH/SqLnfNh7Eo+WaHiiMwUbkoqAdw6+kYXJT8oVb0dRlliN+WijCBfhL8VcTl2L7lwHycaQQ/aOfTmoUd6fhQeCyFliw0pSP6NgNxEawC4vfgBWeI28SBwiozM/LH+0d9DpmvIHMF8XL1BMr32UqgmE9X6ZeAGr4aL1iWixYwYMm9IQrs9pr7/MNBG6Lile58WFuctrF/Nt4hCYey2du2ZmLJ6yYNmS9b7AgvUgQOYWOsiANjrLEJGGGboo9jgTkAmzpBoBH4JwPhXBZgJVoOQeclRuDnPFe180CTgFrOXLm/p8jZ46cGeQs58iZI+eVIme1tDQCnFn182NA/TOgZ2P52Wv8jGfvZ4SgxbllvSxLf2MWnCsEEBl6eJtYE58rngFLzKDRmCJfTgG43JfKzTx0RCaspZq5nsuO4u2MOV7yZhGx+iG/lKtVcOjym79QlZ8OKtzpBA6mLotxXH5LN1uqusnyYxRZh5YDLFokGLnjwshDY45o9UbShKPx3bVfFNYimD9oKb9IHG0BeYHPBKuW0XItVddiGsOtMNlIkSqKzUW+8Xjk4XSci6E5NgVv4gfpEh+D1pLIBcg6CQpyUyk+99CP2FBfRK6USo1GuVrmnR73uekqdoGIi+An6mq2aTS7bbUzrKKB2d97avS2nzb7ptl/qJ7teOI4Hsp2nw462+0BjyDE0qO0wRQtFEbqUnZPbiKnpWu1u/x1Q4pDjNiu+H60CtuUTOP9Lz4B8fZUweLn+9KtVT/zbsh3iANi2M8m+r68DEnHye2ERlV4vqD3sWcSKDSag373wGynN8mrpXItphdUDCmYrsUyoS8kUYGBiMyIeMzSd/NHI6jYzY59BFPII7UpI7Wo50FZH/IND2l8cIhnG4EFmYkR2IO+KuUpiR7RnrFviIr0eKaI1zJ4YiO1qCrpkm5bvM7EK/UFCMU90uNMgZQM0ECCUMGT+FauCW3p1wgExQSuyd9DjWmSlFzc4BKYMCr/WAWeTUhwcbQJye3oKAOYWU1h24UEM36HynYpO/qgPdW1AU2GHEylPykn2IaMxlKvIez29zu/7fdMo7s4l0rrIs4sOUhyrmkI0GU8gUuXC4/UVy0Uncl/QWhuSkkLKIDMLKbTeFQp1zZqm9VGbXMemEpXBkybGpfu/u/b1yKwqvgKVcUDPm8RHiNK0VG6QAgLrpWy/iwVucc4e6w1e9Q1hGxIv/+yIU89Ym/k8KgMP2HLKc32Tk06rIw41TvVSrmRpArZUfOSUKUN0mZkIgzYZdg25TPH/6peAOxSVDGuClAR8Kr8b4KLKSpVNYG2aqVSXYBgSd2LOp/QmXV93tdYNe+7Oue7ExvCDfWycu1KvKx86V4G3lC7VV62sXIxrnwNyffd03+9PP3rH07evHn3039vUrQrzfhhtTTriaXNyuYVuGLl8l2xvFG+nohXVHlnUa6rUpqM5RfrzLtrv/s/8GP59A=='

# 제목 서식2: 2행1열 표(윗칸 부제+제목, 아랫칸 담당자). 날짜 칸이 없는 제목 표의 기준 서식.
_제목2행1열_XML = 'eNrtXW1v28gR/iuE72sTSdS70QaQbCX2RZYMS24uRYCAolYiY4rkLVdR7KKAcWmLO6RIEDS5uGh8yAEtEhT5cLjkw7VN/8zdt0j+D91XcikpsRy/xLE3MSDOcndmZ3fmmdnlUvr9nAWMNoBz89rcry1rnlDanZ7jBvOW+ZsbcxZC/nwiMRgMLlqGa3q9i6Z3cQMmrIHfcxJ6MpVKmB4EN+ZEI2u2RkRO1MifrZFvQKMLDd/CLW8DGNieixumLmYwHQBzwUWEvDF3iWjSAl3brfV7mm90ASvXOp6HXA8JErhtifJtk1+hliNqfNk3EBeDyQTlDEGnageIXnc8F3UMEwSajUCP9SDPeyDuaY7hdnH5Uql2Zb1Ku+EiVrUgVdXsNi5Jkvu4Eb4cPrg3+vs26c+mT+hm8zIm7KDSa4F2G/DatD2psex2PNy0ZzubTdbg8kKpefNKvbm0vIAbDoDdtYjQHFEWer4HuWpEpol7AI0AcTJA0NsAvzWgLetvwF4DbTpixByAEIAdD/Z4Qc9uO7Yrbt9ZEhL52CW4pmMqpySVnz8c7W5rb189Gz56fPSaZ8c1T8c116dqnoxrnhzXXI9pnoxpnnmv5nqk+d7jp6P/vj4vU56WFX8xev318PuXJ6Z75uPqnpmm+w+P9u4+Pvu6ZyXdn74evngz/NefRt//cAKe/pEVz0WKL13fe/KP4V+fDnffjHZ/Wjn7zp6PdB/de4ZnXHv748txiF+63DwS5ZMfpPx+EJ98D8Qnx5VPSLF/aiJQLTWXayoPUHmAygNUHqDyAJUHqDzgXOYBS6Xa5yWVB6g8QOUBKg9QeYDKA1QecC7zgM9Lq6VapVFRqYBKBVQqoFIBlQqoVOC8pgJ7d5+e51QAd7qyFssD8qciD8jMEg31+FDp74+G+gGiocoDVB6g8gCVB5xljPuoecDJ675vKGxcXynX1XE5FQtVLFSxUMVCtSZW2+OHXROvXF+vXfm8/qktitcbp3JNrPIAlQeoPEDlASoPUHnA0egej4QyFbB32jzYBvCy7Tjy+2ZZ8cZbeDeCSWRBABZF7y2j7Q2EZsDFvayyftXqNfL0uQWBsbEAHKcByLt2CFRDcKYSAscILDHuvM0C9PCQiBhsBwtenzCOAj3pmWFuND6wrQM6qEw1G2s8sNuIvG2YvJjSej06V45H2n6WpP+i9/XIcB+OBfL8wzFoeQh5vcPxaNtG13MNR7Rv1KvLi7MzMOc72DTKsB9YlBrYLiWogy3wJq7nkpc5LQOZlij7rEj/EUN3fMuQU7gYz0TMBqeaZPqMmuSUqdAPbJQHZzJhlgdnMc0wD87lcKY5g+FkzguW6dnDg9l+PGYwm8yRWE32I1tNVkVAFQGPIgKGbA4dAVO6QrITRbL9QGg2KMucJJLFaZb6m5YBV/HqBODVSezbJjLcCliFaAvRClcZWSoHgTto0p6J8Y2bfj8Al/Gyo+GzhVeSFV0F0LXpdhxtt9lbMeCGZKRhf5cX10BHWpaQJQwuwR7ldvsOX2g5eP3k8mt845bBr28ZvuGCAHDSQxY1vBwT2fJEe9whUc6tiSzIIhkpqp2Qwighh1GSJFYgZDEqlMZILi8lzXmAxwcPSCRTlijLG5Mmy4pJkuRIXgKcxtaJ6uV1OgFAx6wWvtXml30XGw5ZH4+hADbNmC+9y/fwmtzeAF4fhS04g3c1wFWniOPMKBiP3QoZlXXynyhKx+gLOnIheV2Q3KWZR044Z0F2Tj1/ypzzeIxYOadyzk/COYun2jlV5FTOeY6dM5WO5bX6KfPOrDTdWWm6s/HpzkrTnZWnOxtNd/Zd3lmUbaooG1VxzKqKslkVY3ZVlAyr+B63vEAXq0Iao4Q4RknyWIEQyKhQIiO5SEacaSc9856ZmFiSsvW40Zq6SBVfykjvRyc2jD7ymkarCjooXrI2eVYkxpoyI5shU6WluTRWgT8Mo1/sSHgIP+aP99rADSeYuDTZXImdVQlcw296V2B46CLo+z4EQUBq1vq9FoCBYGcBcyP2BNJw7K6rWR60tzBvgxjMQqXWpOdZbpOOm7SsXGpUqsvSnJHvxyS+GJ80ux113QG3gROPDGSfqAEQIg0pUSV2fQ0jGK53tVJZvXmtvrYodpRqnivfL69VSldFhYGNLaYOfewMXMQGAP41G1k1DLdSERkDoT35os0y4VwGHQ+GZz5wjWvQ8IWIsLtkqhscckApsA23EsIwo/HgSgr688HARqZFL00jABr+hODLvg1B+4Jr9EDAkX3frxLNJZYG/rprowVswnymegbs2i7dF7RdBFyk3TacfhgocGXyEPra6nptuRnuJ5JtsFnq0b2uWSpiw7o9Sz0XT8O+9RKyWtY8mQkx4NyuVitrxByJMXJeqfS7ubFhp+PfBh2j7yA1crOOXDhgCdmQxT7flDQjgmQJHlmBjI6spOn5MbpMNzUjkHOBKRpgPMLOuUKViyMsg8tJ5EyfFuRcXG4015bL683KqUNP+b4Czw+AgHRyZhB4b9WPDwO5jwCgudlHL/cJj96BQTR7akA0p9JPlX6q9HNf/8+o9PM4Ru4TSj8TE0t7Vib/7AJ2Kh+DR8sBi57Z75FJR5glQLhRFxo9NgTY1b7g7uUYm14fLfBmtmOjzXBLY4IXe6TvmXWfHPIVU7Bhk5PEuCp5oM/xZtm1ALRRiN/s5yXipVxMnB+ChrlhWpjFgud27K7WcYwuQbJsLmpCUPjS3K+0uQCPH27JfqQjmMfkIX45g7cMZmvJRdNh9Of9aO+GTVFoLvQ3OMghaDm+hZAcmoLT77lySQ/gWYsiFkbUvquxjSXBiOwW0luoJc7QpIr5VDpfKJCnNVt1YrqcnUvjIfYTftS7WSpXK3yTmEeBZn31Zqm2eLNcbzbrK/zeZYeewMFlSzcby4uVBokcnil62camaBp+wA9519h+sqzdQqVKXlWGwAcGWqI/qcLDNfQGbFdKZwMQbohpJjnSw9yay5l0Q7L2cr1S+1ZfnEFnoWgrPFqSKeSzBXHUZA04TQ8XlsqNepWtk8L98oJeTIX0lIo+xKZroljI871AQ1hFVApIrBLn3TsdXLEa73sHDyGJ0E0WoWk9B5fVcZ7hGAIfLM9pl1wTZyQlt92o81KSiogerZbWSrQi3BorIrVKJKFhs8griZJqhb4SRyrVKQiFEuFWrIBphtGAgZDmMHzTC2SsoXj0RylEcY1dtwSmMZJxsd04k1QmJTFhFGPCrkMmjGRMEGQfpkayCAYuljAhtiUdxAAzPlOgbePEMnzHqm1DtPlOe8oIA+q3CJgyf+JOsIgzGZO/1rBUX1v+Xb3WLFWn51DyXIQZJQFJwlWGAFFGEje5nHqkOB3F6Vjei5UmphS1wAU4IwtpGY/0VCafKaRzmcIkMOWODZjyApcuadov2/f3dl8On+/qST2tDb/aGX79aPSfZ3v3d0a7P/2y/YDGXR5+MSfajgxrALoGhMamXEDHAnue5BxxKrC3QPxg1/hhrxZOlMQrJ3qePmUKnZUtAIlbRFwJxblmCpk8fe2GB6R0Ma2nclEmEe81KfFnnYrUsU1FIZyKn7d3po31ZJNi2GT01cvhdw9HuzvaaOfF8MEf9+4+nI2FLPVv2oHFPns6fP7N3rffYPna2x+39/78bPjq9dtXz47EVnT2zEsyF+k0w/gJB8lcdL0YN5cCe+x3pOaSiBCILadwJCy125BMPvnkYnDolKhEWBUHHpdUJZ9RlJUoqepkoAyVz6WpkUaVD4vldN5M/glPHNvDROn8gHv6+LLOdOTcT+7hv7ev3oy++2dieO/18N6/377eJvc6A3qYAM/9fJz8+cl9/rdzX0+l0xfIw1qNMdr7yzZm9P7m377ifzv3U3o6ozGp+7T5H//buZ/N5QvHEnH0KRFHn4g4ST0Zg5C8Ho846eQ4iOQLJwAiqeMAkVQxkz5WEEmwlY80kaH+dCV4ae4P/wdOBOfq'

def 개요붙임_원본자료():
    payload = json.loads(zlib.decompress(base64.b64decode(_개요붙임3종_XML)).decode('utf-8'))
    return safe_xml_fromstring(payload['header']), safe_xml_fromstring(payload['section'])

def 붙임_유형판별(table):
    """붙임 표: 유형1=1행3열(가운데 빈칸), 유형2=1행2열."""
    cells = 제목_셀들(table)
    rows, cols = int(table.get('rowCnt', '0')), int(table.get('colCnt', '0'))
    if rows != 1 or cols not in (2, 3) or len(cells) != cols:
        return None
    first = 제목_문자열(cells[0]).strip()
    last = 제목_문자열(cells[-1]).strip()
    if not re.match(r'^붙임(?:\s*\d+)?(?:\s|$)', first):
        return None
    if not last:
        return None
    if cols == 3 and 제목_문자열(cells[1]).strip():
        return None
    return 1 if cols == 3 else 2

def 붙임_대상찾기(section):
    """문서의 각 쪽 첫부분에 놓이는 '붙임' 표를 구조/문구로 판별한다.
    HWPX는 페이지 번호를 직접 제공하지 않는 경우가 있으므로, '붙임' 라벨과
    1x3/1x2 구조를 동시에 만족할 때만 대상으로 삼아 일반 표 오인을 막는다.
    """
    result = []
    ordinal = 0
    for p in section:
        for run in p:
            for table in run:
                if 제목_xml이름(table) != 'tbl':
                    continue
                kind = 붙임_유형판별(table)
                if kind:
                    result.append((ordinal, kind))
                ordinal += 1
    return result

# 중제목 번호 칸: 서식(HY견고딕 20pt 등)을 입히는 표는 로마자 번호(Ⅰ·Ⅱ, I·V)만, 글 칸 폭을 맞추는 표는 아라비아 숫자
# 번호(1·01·1.)도 본다(2026-10-04). 숫자 번호 표는 로마자 중제목 아래 소제목인 경우가 많아 서식은 그대로 둔다.
_중제목_번호 = re.compile(r'^(?:[Ⅰ-ⅿ]+|[IVX]{1,4})\s*[.．]?$')
_중제목_번호_숫자포함 = re.compile(r'^(?:[Ⅰ-ⅿ]+|[IVX]{1,4}|\d{1,2})\s*[.．]?$')
_중제목_글자폭_pt = 20


def 중제목_글칸들(table, 숫자번호=True):
    """중제목 모양 표의 글 칸 번호 목록(아니면 빈 목록).

    1행 2열 이상이고, 첫 칸에는 로마자 번호(숫자번호면 아라비아 숫자 번호도)만 있고, 2열 또는 3열에 글이 있는 표다. 칸 병합이나
    표·그림이 든 칸, 붙임·기호 문장으로 시작하는 글이 있으면 중제목으로 보지 않는다.
    """
    cells = 제목_셀들(table)
    rows, cols = int(table.get('rowCnt', '0')), int(table.get('colCnt', '0'))
    if rows != 1 or cols < 2 or len(cells) != cols:
        return []
    for c in cells:
        if any(제목_xml이름(x) in ('tbl', 'pic', 'ole', 'rect', 'fieldBegin') for x in c.iter()):
            return []
        span = 제목_자식(c, 'cellSpan')
        if span is not None and (span.get('colSpan', '1') != '1' or span.get('rowSpan', '1') != '1'):
            return []
    texts = [제목_문자열(c).strip() for c in cells]
    if not (_중제목_번호_숫자포함 if 숫자번호 else _중제목_번호).match(texts[0]):
        return []
    글칸 = [i for i, text in enumerate(texts) if i and text]
    if not set(글칸) & {1, 2}:
        return []
    if any(len(texts[i]) > 80 or re.match(r'^[□ㅁㅇ○※*\-]', texts[i]) or texts[i].startswith('붙임') for i in 글칸):
        return []
    return 글칸


def 중제목_유형판별(table):
    """중제목 서식 표: 1행, 첫 칸은 번호, 다음 칸(유형2) 또는 다음다음 칸(유형1)에 글.

    유형1 = 1행3열(번호·빈칸·글), 유형2 = 1행2열(번호·글). 번호는 로마자만 본다. 그 밖의 중제목 모양 표(숫자 번호,
    번호·글·빈칸 등)는 서식은 그대로 두고 글 칸 폭만 맞춘다(중제목_대상찾기의 'fit').
    """
    cols = int(table.get('colCnt', '0'))
    if cols not in (2, 3) or 중제목_글칸들(table, 숫자번호=False) != [cols - 1]:
        return None
    return 1 if cols == 3 else 2


def 중제목_대상찾기(section):
    """각 구역의 최상위 표 중 중제목 구조인 표의 (순번, 유형) 목록. 유형 'fit'은 글 칸 폭만 맞출 표다."""
    result = []
    ordinal = 0
    for p in section:
        for run in p:
            for table in run:
                if 제목_xml이름(table) != 'tbl':
                    continue
                kind = 중제목_유형판별(table) or ('fit' if 중제목_글칸들(table) else None)
                if kind:
                    result.append((ordinal, kind))
                ordinal += 1
    return result


def 중제목_원본자료():
    payload = json.loads(zlib.decompress(base64.b64decode(_중제목_XML)).decode('utf-8'))
    return safe_xml_fromstring(payload['header']), safe_xml_fromstring(payload['section'])


def _구역_본문폭(section, 기본값=42520):
    """구역의 쪽 폭에서 좌우 여백을 뺀 본문 폭(HWPUNIT). 찾지 못하면 기본값(A4 기본 42520).

    가로 방향 용지(landscape="NARROWLY")도 width·height는 세로 기준 용지 치수 그대로라 높이가 쪽 폭이다
    (실측 2026-10-03: 가로 구역 줄 폭 72848 = 높이 84188 − 좌우 여백 11338).
    """
    for x in section.iter():
        if 제목_xml이름(x) == 'pagePr':
            margin = next((m for m in x if 제목_xml이름(m) == 'margin'), None)
            try:
                폭 = int(x.get('height') if x.get('landscape') == 'NARROWLY' else x.get('width'))
                return 폭 - int(margin.get('left')) - int(margin.get('right'))
            except (TypeError, ValueError, AttributeError):
                break
    return 기본값


def _예정_좌우여백():
    """이번 작업에서 보고서 표준서식이 편집 여백을 바꿀 예정이면 (왼쪽, 오른쪽) 여백(HWPUNIT), 아니면 None.

    표준서식_전체_적용이 페이지_여백_설정(표준서식_설정['여백_mm'])을 부르는 조건과 같다.
    """
    if not (작업_모드 in ('format', 'all') and 표준서식_선행_사용 and 표준서식_여백_사용 and 쪽범위_요청 is None
            and stage_enabled(선택_세부작업, 'standard_format', 작업_모드)):
        return None
    mm = (표준서식_설정 or {}).get('여백_mm') or {}
    try:
        표준 = tuple(int(round(float(mm[k]) * 7200 / 25.4)) for k in ('left', 'right'))
    except (KeyError, TypeError, ValueError):
        return None
    # 원본 여백이 더 좁으면 원본을 두므로(페이지_여백_설정과 같은 규칙) 그 값으로 본문 폭을 잰다.
    원본 = _현재_쪽여백()
    return (_표준_또는_원본여백("LeftMargin", 표준[0], 원본), _표준_또는_원본여백("RightMargin", 표준[1], 원본))


def _최종_본문폭(section):
    """표준서식이 바꿀 편집 여백까지 반영한 본문 폭(HWPUNIT). 여백을 바꿀 예정이 없으면 지금 여백으로 재고,
    쪽 정보가 없으면 None. 가로 방향 용지는 높이가 쪽 폭이다(_구역_본문폭과 같음)."""
    여백 = _예정_좌우여백()
    if 여백 is None:
        return _구역_본문폭(section, None)
    for x in section.iter():
        if 제목_xml이름(x) == 'pagePr':
            try:
                return int(x.get('height') if x.get('landscape') == 'NARROWLY' else x.get('width')) - 여백[0] - 여백[1]
            except (TypeError, ValueError):
                return None
    return None


def _빈_문단인가(p):
    """글자·표·개체 없이 빈 run과 줄 배치 정보만 있는 본문 문단(빈 줄)인지."""
    if 제목_xml이름(p) != 'p':
        return False
    for child in p:
        이름 = 제목_xml이름(child)
        if 이름 == 'linesegarray':
            continue
        if 이름 != 'run':
            return False
        for x in child:
            if 제목_xml이름(x) != 't' or len(x) or (x.text or '').strip():
                return False
    return True


def _문단사이_빈줄_삭제(root, 앞문단, 뒷문단):
    """두 본문 문단 사이가 빈 줄로만 채워져 있으면 그 빈 줄을 지우고 지운 수를 돌려준다.

    사이에 글·표 등 다른 내용이 있으면 한 쌍이 아니므로 그대로 둔다.
    """
    문단들 = list(root)
    if 앞문단 is 뒷문단 or 앞문단 not in 문단들 or 뒷문단 not in 문단들:
        return 0
    처음, 끝 = 문단들.index(앞문단), 문단들.index(뒷문단)
    사이 = 문단들[처음 + 1:끝]
    if 끝 <= 처음 or not 사이 or not all(_빈_문단인가(p) for p in 사이):
        return 0
    for p in 사이:
        root.remove(p)
    return len(사이)


def _문단_본문글(p):
    """본문 문단에 바로 든 글(표·개체 안 글은 빼고, 빈칸 요소 뒤 글은 넣는다)."""
    return ''.join((t.text or '') + ''.join(s.tail or '' for s in t)
                   for r in p if 제목_xml이름(r) == 'run' for t in r if 제목_xml이름(t) == 't')


def _서식표_뒤_빈줄_삭제(root, 표문단):
    """제목·개요 서식 표 문단 바로 뒤의 빈 줄을 첫 항목기호 문장 앞까지 지우고 지운 수를 돌려준다.

    제목·개요 표와 첫 항목기호 문장 사이는 그 문장의 문단 위 여백으로만 띄운다(2026-10-03 사용자 요청:
    빈 줄이 없어야 함). 빈 줄 다음이 항목기호 문장이 아니면(일반 글·표 등) 그대로 둔다.
    """
    문단들 = list(root)
    if 표문단 not in 문단들:
        return 0
    처음 = 끝 = 문단들.index(표문단) + 1
    while 끝 < len(문단들) and _빈_문단인가(문단들[끝]):
        끝 += 1
    if 끝 == 처음 or 끝 >= len(문단들) or not 보고서_문단역할(_문단_본문글(문단들[끝]).strip()):
        return 0
    for p in 문단들[처음:끝]:
        root.remove(p)
    return 끝 - 처음


def _서식표_가로맞춤(table, 본문폭, 비례=False):
    """제목·개요 서식 표를 쪽 좌우 여백 사이 최대 폭(본문 폭 − 표 바깥 여백)으로 맞춘다.

    행마다 칸 너비 합이 표 폭과 같게, 그 행에서 가장 넓은 칸이 차이를 받는다(날짜 칸처럼 좁은 칸은 그대로).
    행 병합 칸이 있거나 가장 넓은 칸이 너무 좁아지면 모든 칸을 같은 비율로 줄인다. 비례이면(서식 프로필의 예시
    표를 쓴 경우) 행마다 예시 표의 열 비율을 그대로 두고 폭만 맞춘다(2026-10-04 결정 1).
    """
    size, out = 제목_자식(table, 'sz'), 제목_자식(table, 'outMargin')
    if size is None or not 본문폭:
        return
    try:
        바깥 = (int(out.get('left', '0')) + int(out.get('right', '0'))) if out is not None else 0
        이전 = int(size.get('width', '0'))
    except ValueError:
        return
    목표 = int(본문폭) - 바깥
    if 목표 <= 0 or 이전 <= 0 or 목표 == 이전:
        return
    행들 = [[c for c in row if 제목_xml이름(c) == 'tc'] for row in table if 제목_xml이름(row) == 'tr']
    병합 = any((제목_자식(c, 'cellSpan') is not None and 제목_자식(c, 'cellSpan').get('rowSpan', '1') != '1')
               for 행 in 행들 for c in 행)
    for 행 in 행들:
        크기들 = [제목_자식(c, 'cellSz') for c in 행]
        if not 크기들 or any(s is None for s in 크기들):
            continue
        너비 = [int(s.get('width', '0')) for s in 크기들]
        if 비례 and not 병합 and sum(너비) > 0:
            새너비들 = [max(1, round(w * 목표 / sum(너비))) for w in 너비]
            새너비들[-1] += 목표 - sum(새너비들)
            for s, w in zip(크기들, 새너비들):
                s.set('width', str(w))
            continue
        넓은 = 너비.index(max(너비))
        새너비 = 너비[넓은] + 목표 - sum(너비)
        if 병합 or 새너비 < 1000:
            for s, w in zip(크기들, 너비):
                s.set('width', str(max(1, round(w * 목표 / 이전))))
        else:
            크기들[넓은].set('width', str(새너비))
    size.set('width', str(목표))


def _중제목_번호굵게_적용(header, maps):
    """번호 굵게를 끈 경우 병합된 번호 글자모양(기준 8번)에서 굵게를 뺀다(중제목 전용 사본이라 안전)."""
    if 중제목_번호굵게:
        return
    merged = maps['charProperties'].get('8')
    for cp in header.iter():
        if 제목_xml이름(cp) == 'charPr' and cp.get('id') == merged:
            for b in [x for x in cp if 제목_xml이름(x) == 'bold']:
                cp.remove(b)


def 중제목_표서식_복사(table, sample, maps, kind, 최대폭=None, header=None):
    """중제목 글은 그대로 두고 표·칸·문단·글자 서식만 기준 표에서 복사한다.

    기준 표는 [번호 | 빈칸 | 글] 순서이며 유형2(2열)는 빈칸 서식을 건너뛴다.
    번호 칸·빈칸 크기는 문서의 것을 유지하고, 글 칸 폭은 글자 수에 비례해 맞춘다(_중제목_칸폭_맞춤).
    """
    for attr in ('borderFillIDRef', 'cellSpacing', 'textWrap', 'textFlow', 'pageBreak', 'repeatHeader'):
        if attr in sample.attrib:
            value = sample.get(attr)
            table.set(attr, maps['borderFills'][value] if attr == 'borderFillIDRef' else value)
    for name in ('inMargin', 'outMargin'):
        src, dst = 제목_자식(sample, name), 제목_자식(table, name)
        if src is not None and dst is not None:
            dst.attrib.update(src.attrib)
    scells = 제목_셀들(sample)
    # 2열 유형은 기준 표의 번호 칸과 마지막(글) 칸을 쓴다(서식 프로필의 2열 예시 표도 같다).
    roles = [scells[0], scells[1], scells[2]] if kind == 1 else [scells[0], scells[-1]]
    for cell, scell in zip(제목_셀들(table), roles):
        cell.set('borderFillIDRef', maps['borderFills'][scell.get('borderFillIDRef')])
        cell.set('hasMargin', scell.get('hasMargin', '0'))
        src, dst = 제목_자식(scell, 'cellMargin'), 제목_자식(cell, 'cellMargin')
        if src is not None and dst is not None:
            dst.attrib.update(src.attrib)
        sub, ssub = 제목_자식(cell, 'subList'), 제목_자식(scell, 'subList')
        sub.set('vertAlign', ssub.get('vertAlign', 'CENTER'))
        sp = 제목_문단들(scell)[0]
        para_id = maps['paraProperties'].get(sp.get('paraPrIDRef'))
        char_id = maps['charProperties'].get(next(r for r in sp if 제목_xml이름(r) == 'run').get('charPrIDRef'))
        if para_id is None or char_id is None:
            raise RuntimeError(f'중제목 기준서식 매핑 누락: {sp.get("paraPrIDRef")}')
        # 빈칸 문단도 함께 맞춰 글자 크기(줄 높이)가 서식 그대로 유지되게 한다.
        for p in 제목_문단들(cell):
            p.set('paraPrIDRef', para_id)
            p.set('styleIDRef', '0')
            for r in list(p):
                if 제목_xml이름(r) == 'linesegarray':
                    p.remove(r)
                elif 제목_xml이름(r) == 'run':
                    r.set('charPrIDRef', char_id)
    _중제목_칸폭_맞춤(table, 최대폭, header)


def _중제목_글자치수(header):
    """header의 글자 모양 ID → (크기 HWPUNIT, 한글 장평 %, 한글 자간 %). 중제목 글 칸 폭 어림에 쓴다."""
    치수 = {}
    for cp in (x for x in header.iter() if 제목_xml이름(x) == 'charPr'):
        ratio, spacing = 제목_자식(cp, 'ratio'), 제목_자식(cp, 'spacing')
        try:
            치수[cp.get('id')] = (int(cp.get('height', '0')) or _중제목_글자폭_pt * 100,
                               int(ratio.get('hangul', '100')) if ratio is not None else 100,
                               int(spacing.get('hangul', '0')) if spacing is not None else 0)
        except (TypeError, ValueError):
            continue
    return 치수


def _중제목_문단폭(p, 치수):
    """문단 글 한 줄의 폭(HWPUNIT)과 가장 큰 글자 크기. 한글·한자는 글자 크기, 영문·숫자는 0.55배, 빈칸은 0.5배에
    장평을 곱하고 글자마다 자간(글자 크기의 %)을 더한다. 글자 모양을 모르면 20pt로 어림한다."""
    폭, 최대크기 = 0.0, 0
    for run in (r for r in p if 제목_xml이름(r) == 'run'):
        크기, 장평, 자간 = 치수.get(run.get('charPrIDRef'), (_중제목_글자폭_pt * 100, 100, 0))
        글 = 제목_문자열(run)
        if 글:
            최대크기 = max(최대크기, 크기)
        for ch in 글:
            배율 = 0.5 if ch == ' ' else (0.55 if ch.isascii() else 1.0)
            폭 += 크기 * 배율 * 장평 / 100 + 크기 * 자간 / 100
    return int(폭), 최대크기


def _중제목_칸폭_맞춤(table, 최대폭=None, header=None):
    """중제목 표의 글 칸 폭을 글자 수에 비례해 자동으로 맞춘다(2026-10-04 사용자 요청).

    글이 든 칸(2열·3열 …)은 가장 긴 줄의 글 폭 + 칸 안 좌우 여백 + 여유(글자 반 개)로 넓히거나 줄이고,
    번호 칸과 빈칸은 그대로 둔다. 표 폭은 칸 폭의 합이며, 최대폭(쪽 본문 폭)을 넘으면 글 칸을 줄인다(넘친
    글은 줄바꿈된다). 글 폭은 칸 글자 모양(크기·장평·자간)으로 어림하고, header가 없으면 20pt로 어림한다.
    예전에는 20pt 글이 들어가지 않을 때 넓히기만 해, 짧은 중제목 칸이 길게 비어 있었다.
    """
    cells = 제목_셀들(table)
    글칸 = 중제목_글칸들(table)
    tsize = 제목_자식(table, 'sz')
    sizes = [제목_자식(c, 'cellSz') for c in cells]
    if not 글칸 or tsize is None or any(s is None for s in sizes):
        return
    치수 = _중제목_글자치수(header) if header is not None else {}
    안여백 = 제목_자식(table, 'inMargin')
    widths = [int(s.get('width', '0')) for s in sizes]
    최소 = {}
    for i in 글칸:
        cell = cells[i]
        margin = 제목_자식(cell, 'cellMargin') if cell.get('hasMargin') == '1' else 안여백
        좌우 = sum(int(margin.get(k, '0')) for k in ('left', 'right')) if margin is not None else 0
        줄들 = [_중제목_문단폭(p, 치수) for p in 제목_문단들(cell)]
        글폭 = max([폭 for 폭, _ in 줄들] + [0])
        크기 = max([k for _, k in 줄들] + [_중제목_글자폭_pt * 100])
        widths[i] = 글폭 + 좌우 + max(600, 크기 // 2)
        최소[i] = 2 * 크기 + 좌우          # 글자 두 개는 들어가게
        widths[i] = max(widths[i], 최소[i])
        # 줄 배치를 한/글이 다시 계산하게 한다.
        for p in 제목_문단들(cell):
            for r in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                p.remove(r)
    if 최대폭 and sum(widths) > 최대폭:
        넘침 = sum(widths) - 최대폭
        글칸폭 = sum(widths[i] for i in 글칸)
        for i in 글칸:
            widths[i] = max(최소[i], widths[i] - int(넘침 * widths[i] / 글칸폭) - 1)
    for size, width in zip(sizes, widths):
        size.set('width', str(width))
    tsize.set('width', str(sum(widths)))


def 개요_표인가(table):
    cells = 제목_셀들(table)
    if len(cells) != 1 or (int(table.get('rowCnt','0')), int(table.get('colCnt','0'))) != (1,1):
        return False
    text = 제목_문자열(cells[0]).strip()
    return bool(text) and len(text) >= 15 and not re.match(r'^[□ㅁㅇ○※*\-]', text) and not text.startswith('붙임')

def 제목_xml이름(e):
    return e.tag.rsplit('}', 1)[-1]

def 제목_자식(e, name):
    return next((x for x in e if 제목_xml이름(x) == name), None)

def 제목_셀들(table):
    return [c for row in table if 제목_xml이름(row) == 'tr'
            for c in row if 제목_xml이름(c) == 'tc']

def 제목_문단들(cell):
    sub = 제목_자식(cell, 'subList')
    return [] if sub is None else [p for p in sub if 제목_xml이름(p) == 'p']

def 제목_문자열(e):
    return ''.join(x.text or '' for x in e.iter() if 제목_xml이름(x) == 't')

# 1×1 제목 상자의 글자 크기 하한(pt). 개요·요약 상자(보통 13~15pt)와 가른다(korean-report-hwpx 제목 20pt,
# 마포구청 제목 표 27pt 실측).
한칸_제목_최소크기_pt = 16


def _한칸_제목글인가(문단글들):
    """1×1 표 칸 글이 제목다운지: 1~2문단, 4~160자, 계층 기호·붙임·참고·목차로 시작하지 않고 날짜·담당자 줄이 아니다."""
    ps = [t.strip() for t in 문단글들 if t and t.strip()]
    글 = ' '.join(ps)
    if not 1 <= len(ps) <= 2 or not 6 <= len(re.sub(r'\s+', '', 글)) or len(글) > 160:
        return False
    # 문서 안 표시 상자('서면보고' 등)는 제목이 아니다(실측: 마포구청 회의 자료, 2026-10-10).
    if re.fullmatch(r'[<〈【\[(]?\s*(서면|구두|대면)?\s*보\s*고\s*(사항|안건|자료)?\s*[>〉】\])]?|'
                    r'[<〈【\[(]?\s*(참\s*고|별\s*첨|붙\s*임|요\s*약|개\s*요|목\s*차|안\s*건)\s*\d*\s*[>〉】\])]?', 글):
        return False
    if re.match(r'^\s*[□ㅁㅇ○※*\-•▪<〈]|^\s*(붙임|참고|목\s*차)', 글):
        return False
    return 보고서머리._looks_title(글)


def _기타_제목표인가(table, header):
    """여러 칸 장식 제목 상자(kordoc 개조식 3×3 등): 4행·4열 이하, 글이 있는 칸 중 제목다운 칸이 하나이고 글자가
    한칸_제목_최소크기_pt 이상, 나머지 글 칸은 보고 주체(날짜·부서·담당자) 글뿐이다(유형 5, 2026-10-10)."""
    try:
        rows, cols = int(table.get('rowCnt', '0')), int(table.get('colCnt', '0'))
    except ValueError:
        return False
    if rows * cols < 2 or rows > 4 or cols > 4:
        return False
    cells = 제목_셀들(table)
    if any(제목_xml이름(x) in ('tbl', 'ole', 'fieldBegin') for c in cells for x in c.iter()):
        return False
    글칸 = [(c, [제목_문자열(p) for p in 제목_문단들(c)]) for c in cells]
    글칸 = [(c, t) for c, t in 글칸 if any(x.strip() for x in t)]
    제목칸 = [c for c, t in 글칸 if _한칸_제목글인가(t)]
    if len(제목칸) != 1:
        return False
    나머지 = [' '.join(t).strip() for c, t in 글칸 if c is not 제목칸[0]]
    if any(not 보고서머리.parse_info(x) for x in 나머지):
        return False
    return 보고서머리._Header(header).char_of(제목칸[0]).get('size_pt', 0) >= 한칸_제목_최소크기_pt


def _한칸_제목표인가(table, header=None):
    """제목다운 1×1 표. header를 주면 칸 글자 크기가 한칸_제목_최소크기_pt 이상인지도 본다(크기 기준을 만족했는지 돌려준다)."""
    if (table.get('rowCnt'), table.get('colCnt')) != ('1', '1'):
        return False
    cells = 제목_셀들(table)
    if len(cells) != 1 or any(제목_xml이름(x) in ('tbl', 'ole', 'rect', 'fieldBegin') for x in cells[0].iter()):
        return False
    if not _한칸_제목글인가([제목_문자열(p) for p in 제목_문단들(cells[0])]):
        return False
    if header is None:
        return True
    크기 = 보고서머리._Header(header).char_of(cells[0]).get('size_pt', 0)
    return 크기 >= 한칸_제목_최소크기_pt


def 제목_유형판별(table, 빈칸허용=False):
    """제목 표 유형. 1·2 = 2×2(제목+날짜·담당자, 부제 없음/있음), 3 = 2행1열(제목+담당자).

    한 제목 칸(1~2문단)과 담당자 칸(2×2는 날짜·담당자 2칸)만 허용한다. 1×1 제목 표는
    제목 서식 대상이 아니다. 빈칸허용이면 날짜·담당자 칸이 모두 빈 표(준말 변환이 만든
    제목 표)도 같은 유형으로 본다.
    """
    cells = 제목_셀들(table)
    if len(cells) not in (2, 3): return None
    rows, cols = int(table.get('rowCnt', '0')), int(table.get('colCnt', '0'))
    # 3행1열(제목 + 담당자 칸 2개, 실측: '마포문화재단 10월 주요 프로그램')도 유형3으로 본다(사용자 요청, 2026-10-09).
    세줄 = len(cells) == 3 and (rows, cols) == (3, 1)
    if (len(cells) == 2 and (rows, cols) != (2, 1)) or (len(cells) == 3 and (rows, cols) != (2, 2) and not 세줄):
        return None
    for i, c in enumerate(cells):
        # 제목 칸의 글 사이 그림(축제 이름 로고 등, 실측: 마포구청 회의 자료)은 제목의 일부로 본다(2026-10-10).
        막는개체 = ('tbl', 'ole', 'rect', 'fieldBegin') if i == 0 else ('tbl', 'pic', 'ole', 'rect', 'fieldBegin')
        if any(제목_xml이름(x) in 막는개체 for x in c.iter()):
            return None
    ps = [p for p in 제목_문단들(cells[0]) if 제목_문자열(p).strip()]
    if len(ps) not in (1, 2): return None
    if any(re.match(r'^\s*[□ㅁㅇ○※*\-]', 제목_문자열(p)) for p in ps): return None
    정보칸_빔 = 빈칸허용 and not any(제목_문자열(c).strip() for c in cells[1:])
    if len(cells) == 2 or 세줄:
        # 유형3: 윗칸(부제+제목) / 아랫칸(담당자) 2행1열(또는 담당자 칸 2개인 3행1열). 날짜 칸이 없다.
        for 칸 in cells[1:]:
            if (not 정보칸_빔 and not _제목표_담당자.search(제목_문자열(칸))
                    and not _설정_담당자_글인가(제목_문자열(칸))): return None
        return 3
    span = 제목_자식(cells[0], 'cellSpan')
    if span is None or span.get('colSpan') != '2': return None
    date, owner = map(제목_문자열, cells[1:])
    if not 정보칸_빔 and not re.search(r'[0-9]{2,4}\s*[.년/\-]\s*[0-9]{1,2}', date): return None
    if not 정보칸_빔 and not re.search(r'담당|과장|팀장|☎|전화|부서|작성', owner) and not _설정_담당자_글인가(owner):
        return None
    return 2 if len(ps) == 2 else 1


def 제목_대상찾기(section, header):
    """쪽 첫부분의 제목 표(유형 1·2·3, 1×1 제목 상자는 유형 4)를 판별한다.

    날짜·담당자 칸이 있는 2×2 표, 또는 담당자 칸이 있는 2행1열 표는 구조만으로
    제목으로 확정한다(글자크기·정렬 같은 시각 서식은 필요 없다). 1×1 표는 제목으로 보지 않는다.
    """
    result = []
    ordinal = 0
    # 1×1 제목 상자(유형 4)는 쪽(구역) 첫머리에서만 본다: 앞에 글 문단이 없고(쪽 나누기 뒤 포함) 이 쪽에서 아직
    # 제목을 찾지 않았을 때. 제목 바로 뒤의 1×1 개요 상자를 제목으로 오인하지 않는다(사용자 요청, 2026-10-10).
    쪽첫머리 = True
    직전제목 = False
    for p in section:
        if p.get('pageBreak') == '1':
            쪽첫머리 = True
        표있음 = False
        for run in p:
            for table in run:
                if 제목_xml이름(table) != 'tbl':
                    continue
                표있음 = True
                kind = 제목_유형판별(table)
                # 1×1 제목 상자: 쪽 첫머리이거나, 글자가 제목 크기(16pt 이상)이고 바로 앞 표가 제목이 아닐 때
                # (제목 바로 뒤 개요 상자 제외). 쪽 나누기 속성 없이 보고서를 이어 붙인 문서도 보고서마다 찾는다.
                if not kind and _한칸_제목표인가(table) and (
                        쪽첫머리 or (not 직전제목 and _한칸_제목표인가(table, header))):
                    kind = 4
                if not kind and (쪽첫머리 or not 직전제목) and _기타_제목표인가(table, header):
                    kind = 5
                찾음 = False
                if kind:
                    cells = 제목_셀들(table)
                    # 장식 제목 상자(유형 5)는 제목이 첫 칸이 아닐 수 있어 표 전체 글로 본다.
                    title = (제목_문자열(table) if kind == 5 else 제목_문자열(cells[0])).strip()
                    if title and len(title) <= 160 and not title.startswith('붙임'):
                        result.append((ordinal, kind))
                        쪽첫머리 = False
                        찾음 = True
                직전제목 = 찾음
                ordinal += 1
        if not 표있음 and 제목_문자열(p).strip():
            쪽첫머리 = False
            # 제목 아래 보고 주체 줄(날짜·부서)은 제목과 개요 상자 사이에 올 수 있다.
            if not 보고서머리.parse_info(제목_문자열(p).strip()):
                직전제목 = False
    return result


def 서식표_종류판별(table):
    """서식 요소 분석용 표 종류: 제목(title1~3)·중제목(midtitle1·2)·붙임(attach1·2)·한 칸 상자(box).

    서식 적용과 같은 판별 함수를 쓴다. 제목 표 바로 뒤의 한 칸 상자는 분석 모듈이 개요 표로 본다.
    그 밖의 표는 None(일반 표)이다.
    """
    kind = 제목_유형판별(table)
    if kind:
        title = 제목_문자열(제목_셀들(table)[0]).strip()
        if title and len(title) <= 160 and not title.startswith('붙임'):
            return f'title{kind}'
    kind = 중제목_유형판별(table)
    if kind:
        return f'midtitle{kind}'
    kind = 붙임_유형판별(table)
    if kind:
        return f'attach{kind}'
    return 'box' if 개요_표인가(table) else None


def _서식표_예시(종류):
    """선택한 서식 프로필이 예시 문서에서 보관한 서식 표 (header, 표). 없으면 None.

    보관한 표도 서식 적용과 같은 판별 함수로 다시 확인해, 칸 구성이 다른 표를 기준으로 쓰지 않는다.
    """
    item = (활성_서식표_프로필 or {}).get(종류)
    if not item:
        return None
    try:
        header = safe_xml_fromstring(item["header_xml"].encode("utf-8"))
        table = safe_xml_fromstring(item["table_xml"].encode("utf-8"))
        판별 = 서식표_종류판별(table)
    except Exception as exc:
        로그(f"서식 프로필의 {서식요소.FORM_LABELS.get(종류, 종류)} 예시를 읽지 못해 기본 서식 표를 씁니다: {exc}")
        return None
    if 판별 != ('box' if 종류 == 'overview' else 종류):
        로그(f"서식 프로필의 {서식요소.FORM_LABELS.get(종류, 종류)} 예시가 칸 구성과 맞지 않아 기본 서식 표를 씁니다.")
        return None
    return header, table


def 제목2행1열_원본자료():
    payload = json.loads(zlib.decompress(base64.b64decode(_제목2행1열_XML)).decode('utf-8'))
    return safe_xml_fromstring(payload['header']), safe_xml_fromstring(payload['section'])


def 제목_원본자료():
    payload = json.loads(zlib.decompress(base64.b64decode(_제목2종_XML)).decode('utf-8'))
    return safe_xml_fromstring(payload['header']), safe_xml_fromstring(payload['section'])


def 제목_참조병합(header, source):
    """글꼴·테두리·탭·문자·문단 속성을 새 ID로 추가하여 기존 서식을 보존한다."""
    maps = {}
    def find(root, name): return next(x for x in root.iter() if 제목_xml이름(x) == name)
    for sf in find(source, 'fontfaces'):
        lang = sf.get('lang')
        target = next((x for x in find(header, 'fontfaces') if x.get('lang') == lang), None)
        if target is None:
            target = XML_자식_추가(find(header, 'fontfaces'), sf, tag=sf.tag, attrib={'lang': lang, 'fontCnt': '0'})
        mapping = {}
        for f in sf:
            same = next((x for x in target if x.get('face') == f.get('face') and x.get('type') == f.get('type')), None)
            if same is None:
                same = copy.deepcopy(f)
                same.set('id', str(max([int(x.get('id')) for x in target] + [-1]) + 1))
                target.append(same)
            mapping[f.get('id')] = same.get('id')
        target.set('fontCnt', str(len(target)))
        maps[lang.lower()] = mapping
    attrs = {'borderFillIDRef': 'borderFills', 'tabPrIDRef': 'tabProperties'}
    for group in ('borderFills', 'tabProperties', 'charProperties', 'paraProperties'):
        src, dst = find(source, group), find(header, group)
        maps[group] = {}
        for item in src:
            # 제목뿐 아니라 제목과 한 쌍인 개요표도 이 병합 함수를 사용한다.
            # 개요 기준서식은 paraPrIDRef=27을 사용하므로 20~23만 복사하면
            # 제목 유형 3 판별 후 개요 적용 단계에서 KeyError('27')가 발생한다.
            # 기준 XML이 참조하는 모든 문단속성을 새 ID로 병합해 제목/개요/붙임
            # 어느 서식에서도 paraPrIDRef 매핑이 누락되지 않게 한다.
            clone = copy.deepcopy(item)
            new_id = str(max([int(x.get('id')) for x in dst] + [-1]) + 1)
            maps[group][item.get('id')] = new_id
            clone.set('id', new_id)
            for x in clone.iter():
                for attr, category in attrs.items():
                    if attr in x.attrib and category in maps:
                        x.set(attr, maps[category].get(x.get(attr), x.get(attr)))
                if 제목_xml이름(x) == 'fontRef':
                    for lang, old in list(x.attrib.items()): x.set(lang, maps[lang][old])
            dst.append(clone)
        dst.set('itemCnt', str(len(dst)))
    return maps


# 날짜: 연·월·일(’26. 10. 10. / 2026년 10월 10일 / 2026-10-10) 또는 요일이 붙은 월·일(10. 6.(화)).
_제목_날짜 = re.compile(r"[’'‘`]?\d{2,4}\s*[.년/\-]\s*\d{1,2}\s*[.월/\-]\s*\d{1,2}"
                    r"|\d{1,2}\s*[.월]\s*\d{1,2}\s*[.일]?\s*\(\s*[월화수목금토일]\s*\)")


def 날짜칸인가(글):
    """칸 글이 주로 날짜인지: 날짜가 있고, 날짜·요일·시간을 빼면 남는 글이 짧다(12자 이하)."""
    글 = (글 or '').strip()
    if not 글 or len(글) > 40:
        return False
    m = _제목_날짜.search(글)
    if not m:
        return False
    나머지 = 글[:m.start()] + 글[m.end():]
    나머지 = re.sub(r'\(\s*[월화수목금토일]\s*\)|[월화수목금토일]요일|\d{1,2}\s*:\s*\d{2}|[.\s~\-]', '', 나머지)
    return len(나머지) <= 12


def 표_날짜칸_한줄(table):
    """표의 날짜 칸(주로 날짜인 칸)을 '한 줄로 입력'(lineWrap=SQUEEZE)으로 둔다. 바꾼 칸 수.

    표 칸 안 날짜는 한 줄로 표기하는 것이 원칙이다(사용자 규칙, 2026-10-10). 칸 폭이 좁아도 한/글이 글자 폭을
    줄여 한 줄을 지킨다. 안쪽 표는 그 표대로 따로 본다.
    """
    count = 0
    for cell in (x for x in table.iter() if 제목_xml이름(x) == 'tc'):
        sub = 제목_자식(cell, 'subList')
        if sub is None or sub.get('lineWrap') == 'SQUEEZE':
            continue
        if any(제목_xml이름(x) == 'tbl' for x in sub.iter()):
            continue
        if 날짜칸인가(''.join(제목_문자열(q) for q in sub if 제목_xml이름(q) == 'p')):
            sub.set('lineWrap', 'SQUEEZE')
            count += 1
    return count


def 표날짜칸_hwpx_처리(source, target=None, selections=None):
    """문서의 모든 표에서 날짜 칸을 한 줄로 입력으로 둔다(선행 서식 단계, 칸 글은 바꾸지 않음)."""
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}

    def 대상(root):
        return [i for i, t in enumerate(x for x in root.iter() if 제목_xml이름(x) == 'tbl')
                if 표_날짜칸_한줄(copy.deepcopy(t))]

    if selections is None:
        return {n: 대상(root) for n, root in sections.items()}
    if not any(items for items in selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    count = 0
    for name, items in selections.items():
        root = sections[name]
        tables = [x for x in root.iter() if 제목_xml이름(x) == 'tbl']
        for index in items:
            before = _표_텍스트(tables[index])
            count += 표_날짜칸_한줄(tables[index])
            if _표_텍스트(tables[index]) != before:
                raise RuntimeError('표 날짜 칸 한 줄 처리 중 표 내용 보존 검사에 실패했습니다.')
        contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    _hwpx_안전_저장(contents, target)
    로그(f"표 날짜 칸 한 줄: {count}칸을 한 줄로 입력으로 지정")
    return count


def 제목_날짜칸_한줄(table):
    """제목 표에서 날짜가 든 짧은 칸(첫 칸 제외)을 '한 줄로 입력'(lineWrap=SQUEEZE)으로 둔다. 바꾼 칸 수.

    날짜 칸 폭이 좁으면 "’26. 10. 10.(토)"가 두 줄로 나뉘었다(2026-10-10 실측). 한 줄로 입력은 칸 폭에 맞춰
    글자 폭을 줄여 한 줄을 지킨다.
    """
    count = 0
    for cell in 제목_셀들(table)[1:]:
        글 = 제목_문자열(cell).strip()
        if not 글 or len(글) > 40 or not _제목_날짜.search(글):
            continue
        sub = 제목_자식(cell, 'subList')
        if sub is not None and sub.get('lineWrap') != 'SQUEEZE':
            sub.set('lineWrap', 'SQUEEZE')
            count += 1
    return count


def 제목_표서식_복사(table, sample, maps, 상자=False):
    """제목 내용은 그대로 두고 원본 표·셀·문단·문자 서식만 복사한다.

    문단은 끝에서부터 맞춘다(제목 표: 부제가 없는 문서도 제목 문단 서식을 받게). 상자=True(한 칸 상자)는 문단 수가
    같으면 하나씩, 다르면 예시의 본문 문단(글이 가장 많은 문단) 서식을 모든 문단에 입힌다. 끝에서 맞추면 한 문단
    상자가 예시 상자 끝의 안내 문단(파란 11pt 등) 서식을 받았다(2026-10-04 범정부오피스 서식 시험).
    """
    for attr in ('borderFillIDRef', 'cellSpacing', 'textWrap', 'textFlow', 'pageBreak', 'repeatHeader'):
        if attr in sample.attrib:
            value = sample.get(attr)
            table.set(attr, maps['borderFills'][value] if attr == 'borderFillIDRef' else value)
    for name in ('sz', 'inMargin', 'outMargin'):
        src, dst = 제목_자식(sample, name), 제목_자식(table, name)
        if src is not None and dst is not None: dst.attrib.update(src.attrib)
    표본칸 = 제목_셀들(sample)
    대상칸 = 제목_셀들(table)
    # 예시보다 칸이 많은 제목 표(3행1열: 담당자 칸 2개)는 남는 칸에 예시의 마지막(담당자) 칸 서식을 입힌다.
    if 표본칸 and len(대상칸) > len(표본칸) and not 상자:
        표본칸 = 표본칸 + [표본칸[-1]] * (len(대상칸) - len(표본칸))
    for cell, scell in zip(대상칸, 표본칸):
        cell.set('borderFillIDRef', maps['borderFills'][scell.get('borderFillIDRef')])
        cell.set('hasMargin', scell.get('hasMargin', '0'))
        for name in ('cellSz', 'cellMargin'):
            src, dst = 제목_자식(scell, name), 제목_자식(cell, name)
            if src is not None and dst is not None:
                원래높이 = dst.get('height') if name == 'cellSz' else None
                dst.attrib.update(src.attrib)
                # 칸 높이는 원본과 예시 중 낮은 값을 둔다(최소 높이라 글이 더 필요하면 한/글이 늘린다). 예시의 높은 칸을
                # 그대로 받으면 제목 표가 3mm 커져 큰 표가 다음 쪽으로 밀리고 원본 쪽 구성이 깨졌다(2026-10-09 실측).
                try:
                    if 원래높이 is not None and 0 < int(원래높이) < int(dst.get('height', '0')):
                        dst.set('height', 원래높이)
                except ValueError:
                    pass
        sub, ssub = 제목_자식(cell, 'subList'), 제목_자식(scell, 'subList')
        sub.set('vertAlign', ssub.get('vertAlign', 'CENTER'))
        ps = [p for p in 제목_문단들(cell) if 제목_문자열(p).strip()]
        sps = [p for p in 제목_문단들(scell) if 제목_문자열(p).strip()]
        본문 = max(sps, key=lambda q: len(제목_문자열(q).strip())) if 상자 and sps and len(sps) != len(ps) else None
        for i, p in enumerate(ps):
            sp = 본문 if 본문 is not None else sps[min(i + max(0, len(sps) - len(ps)), len(sps)-1)]
            source_para_id = sp.get('paraPrIDRef')
            mapped_para_id = maps['paraProperties'].get(source_para_id)
            if mapped_para_id is None:
                raise RuntimeError(f'기준서식 문단속성 매핑 누락: paraPrIDRef={source_para_id}')
            p.set('paraPrIDRef', mapped_para_id)
            p.set('styleIDRef', '0')
            sruns = [r for r in sp if 제목_xml이름(r) == 'run']
            main = max(sruns, key=lambda r: len(제목_문자열(r))).get('charPrIDRef')
            quote = next((r.get('charPrIDRef') for r in sruns if 제목_문자열(r).strip() in ('‘', '’', "'")), main)
            for r in list(p):
                if 제목_xml이름(r) == 'linesegarray': p.remove(r)
                elif 제목_xml이름(r) == 'run':
                    r.set('charPrIDRef', maps['charProperties'][main])
                    # 따옴표 글꼴(돋움)을 동일 런에 섞인 텍스트에도 보존한다.
                    if all(제목_xml이름(t) == 't' and not len(t) for t in r):
                        text = 제목_문자열(r)
                        index = list(p).index(r); p.remove(r)
                        for piece in re.split(r"([‘’'])", text):
                            if not piece: continue
                            nr = XML_요소_생성(r, tag=r.tag, attrib=dict(r.attrib))
                            nr.set('charPrIDRef', maps['charProperties'][quote if piece in ('‘', '’', "'") else main])
                            XML_자식_추가(nr, r, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}t').text = piece
                            p.insert(index, nr); index += 1


def _정밀표_매칭점수(target_signature, source_signature):
    score = 0.0
    if (target_signature["rows"], target_signature["cols"]) == (source_signature["rows"], source_signature["cols"]):
        score += 80
    else:
        score -= 20 * (abs(target_signature["rows"] - source_signature["rows"])
                       + abs(target_signature["cols"] - source_signature["cols"]))
    if target_signature["cell_count"] == source_signature["cell_count"]:
        score += 45
    if target_signature["first_cell"] and target_signature["first_cell"] == source_signature["first_cell"]:
        score += 35
    score += 25 * difflib.SequenceMatcher(
        None, target_signature["first_row"], source_signature["first_row"]
    ).ratio()
    score += max(0, 10 - abs(target_signature["ordinal"] - source_signature["ordinal"]) * 2)
    return round(score, 2)


def _정밀표_셀서식_복사(target, sample, maps, copy_geometry):
    """셀 내용은 유지하고 HWPX 표·셀·문단·문자 서식 참조만 복사한다."""
    reference_attrs = {
        "borderFillIDRef": "borderFills",
        "paraPrIDRef": "paraProperties",
        "charPrIDRef": "charProperties",
    }
    for attr in ("borderFillIDRef", "cellSpacing", "textWrap", "textFlow", "pageBreak", "repeatHeader"):
        if attr in sample.attrib:
            value = sample.get(attr)
            target.set(attr, maps.get(reference_attrs.get(attr, ""), {}).get(value, value))
    for name in ("sz", "inMargin", "outMargin"):
        source_child, target_child = 제목_자식(sample, name), 제목_자식(target, name)
        if source_child is not None and target_child is not None:
            target_child.attrib.update(source_child.attrib)

    target_cells, source_cells = 제목_셀들(target), 제목_셀들(sample)
    for target_cell, source_cell in zip(target_cells, source_cells):
        border = source_cell.get("borderFillIDRef")
        if border is not None:
            target_cell.set("borderFillIDRef", maps["borderFills"].get(border, border))
        if "hasMargin" in source_cell.attrib:
            target_cell.set("hasMargin", source_cell.get("hasMargin"))
        geometry_names = ("cellAddr", "cellSpan", "cellSz") if copy_geometry else ()
        for name in (*geometry_names, "cellMargin"):
            source_child, target_child = 제목_자식(source_cell, name), 제목_자식(target_cell, name)
            if source_child is not None and target_child is not None:
                target_child.attrib.update(source_child.attrib)
        source_sub, target_sub = 제목_자식(source_cell, "subList"), 제목_자식(target_cell, "subList")
        if source_sub is not None and target_sub is not None:
            for attr in ("vertAlign", "textDirection", "lineWrap"):
                if attr in source_sub.attrib:
                    target_sub.set(attr, source_sub.get(attr))

        source_paragraphs = 제목_문단들(source_cell)
        target_paragraphs = 제목_문단들(target_cell)
        for paragraph_index, target_para in enumerate(target_paragraphs):
            if not source_paragraphs:
                break
            source_para = source_paragraphs[min(paragraph_index, len(source_paragraphs) - 1)]
            para_ref = source_para.get("paraPrIDRef")
            if para_ref is not None:
                target_para.set("paraPrIDRef", maps["paraProperties"].get(para_ref, para_ref))
            source_runs = [run for run in source_para if 제목_xml이름(run) == "run"]
            target_runs = [run for run in target_para if 제목_xml이름(run) == "run"]
            for run_index, target_run in enumerate(target_runs):
                if not source_runs:
                    break
                source_run = source_runs[min(run_index, len(source_runs) - 1)]
                char_ref = source_run.get("charPrIDRef")
                if char_ref is not None:
                    target_run.set("charPrIDRef", maps["charProperties"].get(char_ref, char_ref))


def _정밀표_같은표만(table, signature):
    """정밀 복제를 같은 표(첫 칸 글이 같은 예시 표)에만 할 표인가: 한 칸 표와 서식 표(제목·중제목·붙임·한 칸 상자).

    이 표들은 서식 표 단계가 예시 모양을 문단별로 입힌다. 예전에는 칸 수만 같으면 다른 한 칸 표를 짝지어 상자 둘째
    문단(파란 11pt 안내 글 등)까지 첫 문단 서식으로 덮었다(2026-10-04 범정부오피스 인천 서식 왕복 시험). 같은 표가
    예시에 있으면(예시 문서 자체를 정리할 때 등) 그 표 모양을 그대로 되살린다.
    """
    return signature["cell_count"] == 1 or bool(서식표_종류판별(table))


def _정밀표_글같음(first, second):
    """두 표 첫 칸 글이 같은가(빈칸 무시, 빈 글은 같지 않음)."""
    first, second = re.sub(r"\s", "", first or ""), re.sub(r"\s", "", second or "")
    return bool(first) and first == second


def 정밀표_서식_적용(source_path, target_path, precise_profile):
    """프로필 표를 구조·앵커로 매칭해 대상 HWPX에 셀별 서식을 적용한다."""
    if not precise_profile or not precise_profile.get("tables"):
        return {"applied": 0, "skipped": 0, "matches": []}
    with zipfile.ZipFile(source_path) as archive:
        contents = {name: archive.read(name) for name in archive.namelist()}
    target_header = safe_xml_fromstring(contents["Contents/header.xml"])
    source_header = safe_xml_fromstring(precise_profile["header_xml"].encode("utf-8"))
    maps = 제목_참조병합(target_header, source_header)
    source_tables = []
    for item in precise_profile["tables"]:
        parsed = safe_xml_fromstring(item["table_xml"].encode("utf-8"))
        source_tables.append((item, parsed))

    before_text = []
    matches = []
    ordinal = 0
    for name in sorted(n for n in contents if re.fullmatch(r"Contents/section\d+\.xml", n)):
        root = safe_xml_fromstring(contents[name])
        changed = False
        for table in (element for element in root.iter() if 제목_xml이름(element) == "tbl"):
            before_text.append(_표_텍스트(table))
            target_signature = _표_서명(table, ordinal)
            scored = [(_정밀표_매칭점수(target_signature, signature), signature, sample)
                      for signature, sample in source_tables]
            score, signature, sample = max(scored, key=lambda item: item[0])
            # 행·열 또는 셀 수가 같은 표만 적용해 무관한 레이아웃 훼손을 방지한다.
            compatible = ((target_signature["rows"], target_signature["cols"])
                          == (signature["rows"], signature["cols"])
                          or target_signature["cell_count"] == signature["cell_count"])
            # 서식 표(제목·중제목·붙임·한 칸 상자)와 한 칸 표는 같은 표(첫 칸 글이 같음)일 때만, 일반 표는 대응하는 표
            # (첫 칸 글이 같거나 첫 행 글이 60% 이상 같음)일 때만 정밀 복제한다. 예전에는 행·열 수만 같으면 다른 문서의
            # 무관한 표 모양을 입혀 서식 프로필의 대표 표 서식(기본 표 서식)을 덮었다(2026-10-04 범정부오피스 서식 시험).
            if compatible and _정밀표_같은표만(table, target_signature):
                compatible = _정밀표_글같음(target_signature["first_cell"], signature["first_cell"])
            elif compatible:
                compatible = (_정밀표_글같음(target_signature["first_cell"], signature["first_cell"])
                              or difflib.SequenceMatcher(None, target_signature["first_row"],
                                                         signature["first_row"]).ratio() >= 0.6)
            if compatible and score >= 45:
                exact = (target_signature["rows"] == signature["rows"]
                         and target_signature["cols"] == signature["cols"]
                         and target_signature["cell_count"] == signature["cell_count"])
                _정밀표_셀서식_복사(table, sample, maps, exact)
                changed = True
                matches.append({"target": ordinal, "source": signature["ordinal"],
                                "score": score, "geometry": exact})
            ordinal += 1
        if changed:
            contents[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    contents["Contents/header.xml"] = ET.tostring(target_header, encoding="utf-8", xml_declaration=True)

    after_text = []
    for name in sorted(n for n in contents if re.fullmatch(r"Contents/section\d+\.xml", n)):
        root = safe_xml_fromstring(contents[name])
        after_text.extend(_표_텍스트(table) for table in root.iter() if 제목_xml이름(table) == "tbl")
    if before_text != after_text:
        raise RuntimeError("정밀 표 서식 적용 중 표 내용 보존 검사에 실패했습니다.")
    with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in contents.items():
            archive.writestr(name, data, compress_type=zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED)
    return {"applied": len(matches), "skipped": ordinal - len(matches), "matches": matches}



def 제목_문단_가운데정렬(header, table):
    """제목 셀의 모든 실제 제목 문단을 가운데 정렬로 강제한다.

    제목 기준서식의 다른 속성은 그대로 유지하고 paraPr의 align.horizontal만
    CENTER로 바꾼다. 제목 전용으로 새로 병합된 paraPr를 사용하므로 본문/개요에는
    영향을 주지 않는다.
    """
    para_group = next((x for x in header.iter() if 제목_xml이름(x) == 'paraProperties'), None)
    if para_group is None:
        return 0
    by_id = {x.get('id'): x for x in para_group if 제목_xml이름(x) == 'paraPr'}
    cells = 제목_셀들(table)
    if not cells:
        return 0
    count = 0
    for p in 제목_문단들(cells[0]):
        if not 제목_문자열(p).strip():
            continue
        pp = by_id.get(p.get('paraPrIDRef'))
        if pp is None:
            continue
        align = next((x for x in pp if 제목_xml이름(x) == 'align'), None)
        if align is not None:
            align.set('horizontal', 'CENTER')
            count += 1
    return count


def 제목_괄호부연_축소(header, table):
    """제목 셀 안의 '(...)' 부연설명만 설정값만큼 글자 크기를 줄인다.

    일반 본문의 '괄호 안 부연설명 글자 크기 축소'와 동일하게 해당 기능이
    OFF이면 제목에서도 적용하지 않는다. 텍스트 자체는 변경하지 않는다.
    """
    if not globals().get('괄호_축소_사용', True):
        return 0
    reduce_pt = float(globals().get('괄호_축소_pt', 2) or 2)
    char_group = next((x for x in header.iter() if 제목_xml이름(x) == 'charProperties'), None)
    if char_group is None:
        return 0
    by_id = {x.get('id'): x for x in char_group if 제목_xml이름(x) == 'charPr'}
    cache = {}

    def reduced_char_id(old_id):
        key = (old_id, reduce_pt)
        if key in cache:
            return cache[key]
        src = by_id.get(old_id)
        if src is None:
            return old_id
        clone = copy.deepcopy(src)
        try:
            old_h = int(clone.get('height', '1000'))
            new_h = max(100, old_h - int(round(reduce_pt * 100)))
            clone.set('height', str(new_h))
        except Exception:
            return old_id
        new_id = str(max([int(x.get('id')) for x in char_group if (x.get('id') or '').isdigit()] + [-1]) + 1)
        clone.set('id', new_id)
        char_group.append(clone)
        char_group.set('itemCnt', str(len(char_group)))
        by_id[new_id] = clone
        cache[key] = new_id
        return new_id

    cells = 제목_셀들(table)
    if not cells:
        return 0
    applied = 0
    # 제목은 기준서식 적용 후 단순 텍스트 run으로 정규화되어 있으므로 run 단위에서
    # 괄호 구간을 안전하게 분리한다. 중첩괄호는 가장 안쪽부터 일반 괄호로 처리한다.
    pattern = re.compile(r'(\([^()]+\))')
    for p in 제목_문단들(cells[0]):
        for run in list(p):
            if 제목_xml이름(run) != 'run':
                continue
            # 컨트롤이 섞인 run은 건드리지 않는다.
            ts = [x for x in run if 제목_xml이름(x) == 't']
            if len(ts) != 1 or len(run) != 1:
                continue
            text = ts[0].text or ''
            if '(' not in text or ')' not in text:
                continue
            pieces = pattern.split(text)
            if len(pieces) == 1:
                continue
            idx = list(p).index(run)
            p.remove(run)
            for piece in pieces:
                if not piece:
                    continue
                nr = XML_요소_생성(run, tag=run.tag, attrib=dict(run.attrib))
                if pattern.fullmatch(piece):
                    nr.set('charPrIDRef', reduced_char_id(run.get('charPrIDRef')))
                    applied += 1
                nt = XML_자식_추가(nr, ts[0], tag=ts[0].tag, attrib=dict(ts[0].attrib))
                nt.text = piece
                p.insert(idx, nr)
                idx += 1
    return applied

def 제목_hwpx_처리(source, target=None, selections=None):
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    # 기존 네임스페이스 접두사를 유지한다.
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items()
                if re.fullmatch(r'Contents/section\d+\.xml', n)}
    if selections is None:
        return {n: 제목_대상찾기(root, header) for n, root in sections.items()}
    if not any(kind in (1, 2, 3, 4, 5) for items in selections.values() for _, kind in items):
        if target is not None: shutil.copyfile(source, target)
        return 0
    기준 = {}

    def 기준표(종류):
        """(기준 표, ID 매핑, 서식 프로필 예시 여부). 필요한 기준만 한 번씩 header에 병합한다.

        선택한 서식 프로필에 그 종류의 예시 표가 있으면 그 표를, 없으면 내장 기준 표를 쓴다.
        유형3(2행1열)과 개요는 내장 기준 자료가 따로 있다.
        """
        if 종류 not in 기준:
            예시 = _서식표_예시(종류)
            if 예시 is not None:
                기준[종류] = (예시[1], 제목_참조병합(header, 예시[0]), True)
            elif 종류 in ('title1', 'title2'):
                if '내장제목' not in 기준:
                    sh, ss = 제목_원본자료()
                    기준['내장제목'] = ([x for x in ss.iter() if 제목_xml이름(x) == 'tbl'], 제목_참조병합(header, sh))
                samples, maps = 기준['내장제목']
                기준[종류] = (samples[int(종류[-1]) - 1], maps, False)
            elif 종류 == 'title3':
                h5, s5 = 제목2행1열_원본자료()
                기준[종류] = (next(x for x in s5.iter() if 제목_xml이름(x) == 'tbl'), 제목_참조병합(header, h5), False)
            else:
                # 제목은 개요와 한 쌍이므로, 제목 바로 다음의 1칸 개요표에도 기준 개요 서식을 적용한다.
                eh, es = 개요붙임_원본자료()
                기준[종류] = ([x for x in es.iter() if 제목_xml이름(x) == 'tbl'][0], 제목_참조병합(header, eh), False)
        return 기준[종류]

    count = 0
    지운빈줄 = 뒤빈줄 = 0
    for name, items in selections.items():
        root = sections[name]
        tables = [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']
        표문단 = {id(t): p for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl'}
        본문폭 = _구역_본문폭(root, None)   # 쪽 정보가 없으면 폭을 바꾸지 않는다
        for index, kind in items:
            table = tables[index]
            현재종류 = (제목_유형판별(table) if kind not in (4, 5) else
                     4 if kind == 4 and _한칸_제목표인가(table) else 5 if kind == 5 and _기타_제목표인가(table, header) else None)
            if 현재종류 != kind:
                raise RuntimeError('처리 중 제목 구조가 변경되어 제목 서식적용을 중단했습니다.')
            before = 제목_문자열(table)
            if kind in (4, 5):
                # 1×1·장식 제목 상자: 서식은 보고서 머리 서식 복사(예시 프로필)가 맡고, 여기서는 가로 크기만 맞춘다.
                _서식표_가로맞춤(table, 본문폭, 비례=True)
                if 제목_문자열(table) != before: raise RuntimeError('제목 텍스트 보존 검사 실패')
                count += 1
                continue
            sample, maps, 예시사용 = 기준표(f'title{kind}')
            제목_표서식_복사(table, sample, maps)
            # 제목 표 날짜 칸(A2, "’26. 10. 10.(토)" 등)은 칸 너비와 관계없이 한 줄로 둔다(사용자 요청, 2026-10-10).
            제목_날짜칸_한줄(table)
            # 제목 표 가로 크기는 쪽 좌우 여백 사이 최대 폭으로 한다(기준 표 폭과 문서 여백이 달라도 맞춤).
            # 서식 프로필의 예시 표를 쓰면 열 비율은 예시대로 둔다.
            _서식표_가로맞춤(table, 본문폭, 비례=예시사용)
            # 제목 텍스트는 유형과 관계없이 가운데 정렬을 기본값으로 한다.
            # 서식 프로필의 예시 표를 쓰면 그 표의 정렬을 따른다.
            if not 예시사용:
                제목_문단_가운데정렬(header, table)
            # 일반 보고서 서식의 괄호 부연설명 축소 설정을 제목에도 동일 적용한다.
            제목_괄호부연_축소(header, table)
            # 부제(첫 문단)는 15pt로 둔다(내장 기준 표일 때). 서식 프로필 예시 표는 그 표의 크기를 따른다.
            if not 예시사용:
                제목_부제_크기(header, table)
            if 제목_문자열(table) != before: raise RuntimeError('제목 텍스트 보존 검사 실패')
            끝문단 = 표문단[id(table)]
            # 제목 다음 표가 개요 구조이면 내용은 보존하고 개요 기준서식 적용
            if index + 1 < len(tables) and 개요_표인가(tables[index + 1]):
                obefore = 제목_문자열(tables[index + 1])
                overview_sample, emaps, 개요예시 = 기준표('overview')
                제목_표서식_복사(tables[index + 1], overview_sample, emaps)
                # 제목_표서식_복사는 문단의 모든 run을 대표 charPrIDRef 하나로
                # 정규화한다. 개요(요지) 표 문단이 본문 처리 단계에서 이미
                # 괄호 부연설명 2pt 축소를 받았더라도 이 정규화로 지워지므로,
                # 제목 표와 동일하게 여기서 다시 적용해 유지시킨다.
                제목_괄호부연_축소(header, tables[index + 1])
                _서식표_가로맞춤(tables[index + 1], 본문폭, 비례=개요예시)
                if 제목_문자열(tables[index + 1]) != obefore: raise RuntimeError('개요 텍스트 보존 검사 실패')
                # 제목 표와 개요 표 사이에는 빈 줄을 두지 않는다.
                지운빈줄 += _문단사이_빈줄_삭제(root, 표문단[id(table)], 표문단[id(tables[index + 1])])
                끝문단 = 표문단[id(tables[index + 1])]
            # 제목·개요 표와 첫 항목기호 문장 사이도 빈 줄 없이 문단 위 여백으로만 띄운다.
            뒤빈줄 += _서식표_뒤_빈줄_삭제(root, 끝문단)
            count += 1
        contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    if 지운빈줄:
        로그(f"제목 표와 개요 표 사이 빈 줄 {지운빈줄}개 삭제")
    if 뒤빈줄:
        로그(f"제목·개요 표와 첫 항목기호 문장 사이 빈 줄 {뒤빈줄}개 삭제")
    contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in contents.items():
            z.writestr(name, data, compress_type=zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED)
    return count


def _제목_임시hwpx_저장(경로):
    """
    현재 문서를 HWPX 스냅샷으로 저장한다.

    HwpObject.SaveAs()는 저장된 파일을 현재 편집 문서로 전환해 파일 핸들을
    계속 잡을 수 있다. TemporaryDirectory 안에 직접 SaveAs 하면 블록 종료 시
    Windows에서 WinError 32가 발생하므로, 임시 파일을 명시적으로 관리한다.
    """
    경로 = Path(경로)
    경로.parent.mkdir(parents=True, exist_ok=True)
    if hwp.SaveAs(str(경로), 'HWPX', '') is False:
        raise RuntimeError('제목 분석/적용용 HWPX 저장 실패')
    # SaveAs 직후 파일 쓰기가 완전히 끝날 때까지 짧게 확인한다.
    for _ in range(20):
        try:
            with zipfile.ZipFile(경로, 'r') as z:
                if 'Contents/header.xml' in z.namelist():
                    return 경로
        except (PermissionError, OSError, zipfile.BadZipFile):
            pass
        time.sleep(0.05)
    raise RuntimeError('제목 분석/적용용 HWPX 저장 완료를 확인하지 못했습니다.')


_작업_임시폴더_접두어 = ("hwp_format_first_", "hwp_precise_table_", "docfit_외부문서_", "hwp_table_guard_")


def 이전_작업_임시폴더_정리(최소_경과초=600):
    """이전 실행에서 한글이 파일을 잡고 있어 지우지 못한 작업용 임시 폴더를
    정리한다. 지금 실행 중인 다른 작업의 폴더를 건드리지 않도록 일정 시간
    지난 폴더만 지우며, 아직 사용 중인 폴더는 조용히 건너뛴다."""
    기준 = time.time() - 최소_경과초
    정리수 = 0
    try:
        후보들 = list(Path(tempfile.gettempdir()).iterdir())
    except OSError:
        return 0
    for 폴더 in 후보들:
        if not 폴더.name.startswith(_작업_임시폴더_접두어):
            continue
        try:
            if not 폴더.is_dir() or 폴더.stat().st_mtime > 기준:
                continue
            shutil.rmtree(폴더)
            정리수 += 1
        except OSError:
            continue
    return 정리수


def _제목_임시폴더_정리(폴더):
    """한글이 잠시 파일 핸들을 유지해도 본 작업을 실패시키지 않도록 지연 정리한다."""
    폴더 = Path(폴더)
    for 시도 in range(20):
        try:
            shutil.rmtree(폴더)
            return
        except FileNotFoundError:
            return
        except (PermissionError, OSError) as e:
            if 시도 == 19:
                # 임시파일 정리 실패는 문서 편집 실패가 아니다. 다음 실행/Windows가 정리한다.
                진단로그(f'제목 임시파일 정리 보류: {폴더} ({e})')
                return
            time.sleep(0.1)


def 서식구조_조사(원본문서경로, 처리함수, 이름):
    """HWPX는 직접 읽고, HWP만 현재 한글에서 변환한다. 추가 COM 실행 금지."""
    if 원본문서경로 is not None and Path(원본문서경로).suffix.lower() == '.hwpx':
        로그(f'{이름} 구조 직접 분석 시작')
        result = 처리함수(Path(원본문서경로))
        로그(f'{이름} 구조 직접 분석 완료')
        return result
    folder = Path(tempfile.mkdtemp(prefix='hwp_structure_scan_'))
    try:
        로그(f'{이름} 분석: 현재 한글에서 HWPX 변환 시작')
        source = _제목_임시hwpx_저장(folder / 'scan.hwpx')
        result = 처리함수(source)
        로그(f'{이름} 구조 분석 완료')
        return result
    finally:
        _제목_임시폴더_정리(folder)


def 제목4종_현재문서_조사(원본문서경로=None):
    return 서식구조_조사(원본문서경로, 제목_hwpx_처리, '제목')


def 제목4종_현재문서_적용(selections):
    if not any(items for items in selections.values()):
        로그('제목 서식 대상 없음: 제목표가 검출되지 않아 제목서식을 적용하지 않습니다.')
        return
    folder = Path(tempfile.mkdtemp(prefix='hwp_title_apply_'))
    try:
        source, target = folder / 'before.hwpx', folder / 'after.hwpx'
        _제목_임시hwpx_저장(source)
        count = 제목_hwpx_처리(source, target, selections)
        if 한글_문서_열기(hwp, target, 'HWPX', 'forceopen:true') is False:
            raise RuntimeError('제목 적용 결과를 열지 못했습니다.')
        로그(f'제목 서식 자동 적용: {count}개 / 유형 ' + ', '.join(str(k) for v in selections.values() for _, k in v))
    finally:
        # after.hwpx가 현재 문서로 열려 있을 수 있으므로 삭제 실패를 작업 실패로 전파하지 않는다.
        _제목_임시폴더_정리(folder)


def 붙임_hwpx_처리(source, target=None, selections=None):
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
    if selections is None:
        return {n: 붙임_대상찾기(root) for n, root in sections.items()}
    if not any(items for items in selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    기준 = {}

    def 기준표(kind):
        """붙임 유형의 (기준 표, ID 매핑). 서식 프로필의 예시 표가 있으면 그 표를 쓴다."""
        if kind not in 기준:
            예시 = _서식표_예시(f'attach{kind}')
            if 예시 is not None:
                기준[kind] = (예시[1], 제목_참조병합(header, 예시[0]))
            else:
                if '내장' not in 기준:
                    sh, ss = 개요붙임_원본자료()
                    기준['내장'] = ([x for x in ss.iter() if 제목_xml이름(x) == 'tbl'][1:3], 제목_참조병합(header, sh))
                samples, maps = 기준['내장']
                기준[kind] = (samples[kind - 1], maps)
        return 기준[kind]

    count = 0
    for name, items in selections.items():
        root = sections[name]
        tables = [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']
        for index, kind in items:
            table = tables[index]
            if 붙임_유형판별(table) != kind:
                raise RuntimeError('처리 중 붙임 구조가 변경되어 붙임 서식적용을 중단했습니다.')
            before = 제목_문자열(table)
            제목_표서식_복사(table, *기준표(kind))
            if 제목_문자열(table) != before: raise RuntimeError('붙임 텍스트 보존 검사 실패')
            count += 1
        contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in contents.items():
            z.writestr(name, data, compress_type=zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED)
    return count

def 중제목_hwpx_처리(source, target=None, selections=None):
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
    if selections is None:
        return {n: 중제목_대상찾기(root) for n, root in sections.items()}
    if not any(items for items in selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    기준 = {}

    def 기준표(kind):
        """중제목 유형의 (기준 표, ID 매핑).

        서식 프로필의 같은 유형 예시를 먼저 쓴다. 2열 유형은 3열 예시(번호·빈칸·글)의 번호·글 칸도
        쓸 수 있지만, 3열 유형은 빈칸 서식이 필요해 2열 예시로 대신하지 않는다.
        """
        if kind not in 기준:
            예시 = _서식표_예시(f'midtitle{kind}') or (_서식표_예시('midtitle1') if kind == 2 else None)
            if 예시 is not None:
                기준[kind] = (예시[1], 제목_참조병합(header, 예시[0]))
            else:
                if '내장' not in 기준:
                    sh, ss = 중제목_원본자료()
                    maps = 제목_참조병합(header, sh)
                    # 번호 굵게 끄기는 내장 기준 표의 번호 글자 모양(8번)에만 적용한다.
                    _중제목_번호굵게_적용(header, maps)
                    기준['내장'] = (next(x for x in ss.iter() if 제목_xml이름(x) == 'tbl'), maps)
                기준[kind] = 기준['내장']
        return 기준[kind]

    count = 0
    for name, items in selections.items():
        root = sections[name]
        tables = [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']
        for index, kind in items:
            table = tables[index]
            현재 = 중제목_유형판별(table) or ('fit' if 중제목_글칸들(table) else None)
            if 현재 != kind:
                raise RuntimeError('처리 중 중제목 구조가 변경되어 중제목 서식적용을 중단했습니다.')
            before = 제목_문자열(table)
            if kind == 'fit':
                # 번호·글·빈칸 등 서식 기준 표가 없는 모양은 서식은 두고 글 칸 폭만 글자 수에 맞춘다.
                _중제목_칸폭_맞춤(table, _구역_본문폭(root), header)
            else:
                sample, maps = 기준표(kind)
                중제목_표서식_복사(table, sample, maps, kind, _구역_본문폭(root), header)
            if 제목_문자열(table) != before: raise RuntimeError('중제목 텍스트 보존 검사 실패')
            count += 1
        contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in contents.items():
            z.writestr(name, data, compress_type=zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED)
    return count


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


def 제목_부제_크기_해석(value, 기본값=15):
    """설정의 제목 부제 크기(pt) 글을 숫자로 바꾼다. 숫자가 아니면 기본값, 5~40pt 밖이면 범위 끝 값."""
    try:
        크기 = float(str(value).strip().replace(',', '.'))
    except (TypeError, ValueError):
        return 기본값
    if 크기 != 크기:   # NaN
        return 기본값
    크기 = min(40.0, max(5.0, 크기))
    return int(크기) if 크기.is_integer() else 크기


def 제목_부제_크기_반영(value):
    """설정값을 제목 부제 크기 전역값에 반영하고 반영한 값을 돌려준다."""
    global 제목_부제_크기_pt
    제목_부제_크기_pt = 제목_부제_크기_해석(value)
    return 제목_부제_크기_pt


# 새로 만드는 제목 서식 표 담당자 칸(B2) 글. 빈 글이면 기준 표의 글(○○과장/담당관 …)을 그대로 둔다.
# 설정창 '제목 표 담당자 칸(B2) 글'(title_owner_text)로 바꾼다(2026-10-03 사용자 요청).
제목_담당자_글 = ''


def 제목_담당자_글_반영(value):
    """설정값(한 줄, 앞뒤 빈칸 제거, 200자까지)을 제목 담당자 칸 글 전역값에 반영하고 반영한 값을 돌려준다."""
    global 제목_담당자_글
    제목_담당자_글 = ' '.join(str(value or '').split('\n')).replace('\r', ' ').strip()[:200]
    return 제목_담당자_글


def _설정_담당자_글인가(text):
    """칸 글이 설정한 제목 담당자 칸 글과 같은지(담당·과장 같은 낱말이 없는 글도 담당자 칸으로 본다)."""
    return bool(제목_담당자_글) and (text or '').strip() == 제목_담당자_글


def _서식표_기준(header, kind, cache):
    """서식 표 종류의 (기준 표, ID 매핑)을 문서 header에 한 번만 병합해 돌려준다.

    선택한 서식 프로필에 같은 종류의 예시 표가 있으면 그 표를 쓴다(cache['예시사용']에 종류를 남긴다).
    2행1열 제목과 부제 있는 제목 서식1은 부제·제목 두 문단이 있는 예시만 쓴다(부제를 넣을 문단이 있어야 한다).
    """
    예시키 = '예시:' + kind
    if 예시키 not in cache:
        예시 = _서식표_예시(_서식표_예시종류[kind])
        if 예시 is not None and kind in ('title2', 'title1부제') and len(
                [p for p in 제목_문단들(제목_셀들(예시[1])[0]) if 제목_문자열(p).strip()]) != 2:
            예시 = None
        cache[예시키] = (예시[1], 제목_참조병합(header, 예시[0])) if 예시 is not None else None
    if cache[예시키] is not None:
        cache.setdefault('예시사용', set()).add(kind)
        return cache[예시키]
    group = _서식표_묶음[kind]
    if group not in cache:
        source_header, source = {'제목': 제목_원본자료, '제목2행1열': 제목2행1열_원본자료,
                                 '개요붙임': 개요붙임_원본자료, '중제목': 중제목_원본자료}[group]()
        maps = 제목_참조병합(header, source_header)
        if group == '중제목':
            _중제목_번호굵게_적용(header, maps)
        cache[group] = ([x for x in source.iter() if 제목_xml이름(x) == 'tbl'], maps)
    tables, maps = cache[group]
    # 제목 원본자료: 0 = 부제 없는 2×2 제목, 1 = 부제·제목 두 문단의 2×2 제목
    index = {'overview': 0, 'attach1': 1, 'attach2': 2, 'title1부제': 1}.get(kind, 0)
    return tables[index], maps


def 제목_부제_크기(header, table, 크기_pt=None):
    """제목 표 A1 칸에 글 문단이 둘 이상이면 첫 문단(부제)의 글자 크기를 정한 크기로 맞춘다. 바꾼 글 묶음 수.

    제목 글의 첫 쉼표 앞 글이 부제다(2026-10-03 사용자 규칙: 쉼표 앞 글자는 기본 15pt). 부제 안 괄호 부연설명도
    같은 크기로 둔다. 글자 모양은 복제해서 바꾸므로 다른 곳의 글자 모양은 그대로다.
    """
    cells = 제목_셀들(table)
    ps = [p for p in 제목_문단들(cells[0]) if 제목_문자열(p).strip()] if cells else []
    char_group = next((x for x in header.iter() if 제목_xml이름(x) == 'charProperties'), None)
    if len(ps) < 2 or char_group is None:
        return 0
    높이 = str(int(round(float(크기_pt or 제목_부제_크기_pt) * 100)))
    by_id = {x.get('id'): x for x in char_group if 제목_xml이름(x) == 'charPr'}
    복제 = {}
    count = 0
    for run in (r for r in ps[0] if 제목_xml이름(r) == 'run'):
        old = run.get('charPrIDRef')
        src = by_id.get(old)
        if src is None or src.get('height') == 높이:
            continue
        if old not in 복제:
            clone = copy.deepcopy(src)
            clone.set('height', 높이)
            new_id = str(max([int(x.get('id')) for x in char_group if (x.get('id') or '').isdigit()] + [-1]) + 1)
            clone.set('id', new_id)
            char_group.append(clone)
            char_group.set('itemCnt', str(len(char_group)))
            by_id[new_id] = clone
            복제[old] = new_id
        run.set('charPrIDRef', 복제[old])
        count += 1
    return count


def _칸_글_지우기(cell):
    for p in 제목_문단들(cell):
        for r in [x for x in p if 제목_xml이름(x) == 'run']:
            for t in [x for x in r if 제목_xml이름(x) == 't']:
                r.remove(t)


def _칸_날짜_현행화(cell, 오늘):
    """칸 글 가운데 요일이 붙은 날짜를 오늘 날짜로 바꾼다(다른 글과 글자 모양은 그대로). 바꾼 수.

    연도는 ’26처럼 따옴표 붙은 두 자리 약어로 쓴다(2026-10-03 사용자 요청: '2026.'이 아니라 '’26.').
    날짜가 한 글 조각(hp:t) 안에 있으면 그 조각만 고친다(따옴표가 앞 조각에 있으면 그대로 둔다).
    숫자가 여러 조각에 걸쳐 있으면 그 문단 글을 첫 조각에 모아 바꾼다.
    """
    바꾼수 = 0
    for p in 제목_문단들(cell):
        조각들 = [t for r in p if 제목_xml이름(r) == 'run' for t in r if 제목_xml이름(t) == 't' and not len(t)]
        조각수, 앞글 = 0, ''
        for t in 조각들:
            새글, 수 = 날짜_현행화(t.text or '', 오늘, short_year=True, before=앞글)
            if 수:
                t.text = 새글
                조각수 += 수
            앞글 += t.text or ''
        if not 조각수 and 조각들:
            새글, 수 = 날짜_현행화(''.join(t.text or '' for t in 조각들), 오늘, short_year=True)
            if 수:
                조각들[0].text = 새글
                for t in 조각들[1:]:
                    t.text = ''
                조각수 = 수
        바꾼수 += 조각수
    return 바꾼수


def _빈칸_서식_참조_변환(cell, maps):
    """글 없는 칸의 문단·글자 모양 참조를 새로 병합된 ID로 바꾼다(글 있는 문단은 표서식 복사가 처리)."""
    for p in 제목_문단들(cell):
        p.set('paraPrIDRef', maps['paraProperties'].get(p.get('paraPrIDRef'), p.get('paraPrIDRef')))
        for r in p:
            if 제목_xml이름(r) == 'run' and r.get('charPrIDRef') is not None:
                r.set('charPrIDRef', maps['charProperties'].get(r.get('charPrIDRef'), r.get('charPrIDRef')))


def _칸_글_넣기(cell, sample, value):
    """칸의 첫 문단을 글 하나만 있는 한 문단으로 만들어 value를 넣는다(서식 참조는 이후 복사 단계가 맞춘다)."""
    top = 제목_자식(cell, 'subList')
    paras = [p for p in top if 제목_xml이름(p) == 'p']
    for extra in paras[1:]:
        top.remove(extra)
    runs = [r for r in paras[0] if 제목_xml이름(r) == 'run']
    for extra in runs[1:]:
        paras[0].remove(extra)
    for child in list(runs[0]):
        runs[0].remove(child)
    XML_자식_추가(runs[0], sample, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}t').text = value


def 서식표_생성(header, kind, text, cache, 번호=None, 최대폭=None, 본문폭=None):
    """기준 서식 표를 복사해 글을 넣은 새 표를 만든다.

    title1 = 제목 서식1(2×2, 글은 A1), title2 = 제목 서식2(2행1열). 제목 글에 쉼표가 있으면 첫 쉼표 앞은
    부제 15pt·뒤는 제목 27pt 두 줄이다(제목1은 부제 있는 2×2 기준 표를 쓴다). 쉼표가 없으면 제목 한 줄.
    overview = 개요(요지) 표(글은 A1).
    제목 서식의 글은 모두 가운데 정렬이다. midtitle = 중제목 표(번호 칸에 로마자 번호, 글은 글 칸),
    attach1·attach2 = 붙임 서식1(1행3열)·2(1행2열)(글은 마지막 글 칸, '붙임' 글자는 그대로).
    """
    sub = ''
    if kind in ('title1', 'title2'):
        # 첫 쉼표 앞은 부제(2026-10-03 사용자 규칙: 제목1도 쉼표 앞 글자는 부제 크기)
        sub, text = split_title2(text)
    기준종류 = 'title1부제' if kind == 'title1' and sub else kind
    sample, maps = _서식표_기준(header, 기준종류, cache)
    result = copy.deepcopy(sample)
    cells = 제목_셀들(result)
    if kind in ('midtitle', 'attach1', 'attach2'):
        # 마지막 칸이 글 칸이다. 번호·붙임 글자 칸과 빈 칸은 기준 표의 글을 그대로 두거나 비운다.
        blank = not text.strip()
        _칸_글_넣기(cells[-1], sample, text if not blank else 'X')
        if kind == 'midtitle':
            _칸_글_넣기(cells[0], sample, 번호 or 'Ⅰ')
        if len(cells) == 3:  # 가운데 빈칸은 글이 없으므로 기준 표의 글 없는 문단을 비워 둔다.
            _칸_글_지우기(cells[1])
        if kind == 'midtitle':
            중제목_표서식_복사(result, sample, maps, 1, 최대폭, header)
        else:
            제목_표서식_복사(result, sample, maps)
            if len(cells) == 3:
                _빈칸_서식_참조_변환(cells[1], maps)
        if blank:
            _칸_글_지우기(cells[-1])
        return result
    top = 제목_자식(cells[0], 'subList')
    paras = [p for p in top if 제목_xml이름(p) == 'p']
    # A1 칸: 글 문단 수만큼만 남긴다(부제가 없으면 제목 문단 하나).
    wanted = [t for t in ((sub, text) if sub else (text,))]
    keep = paras[len(paras) - len(wanted):] if (sub or kind == 'title2') else paras[:1]
    for p in paras:
        if p not in keep:
            top.remove(p)
    blank = not any(w.strip() for w in wanted)
    for p, value in zip(keep, wanted):
        runs = [r for r in p if 제목_xml이름(r) == 'run']
        for extra in runs[1:]:
            p.remove(extra)
        for child in list(runs[0]):
            runs[0].remove(child)
        # 글이 비면 서식만 복사되도록 표시용 글자를 잠시 넣었다가 지운다.
        XML_자식_추가(runs[0], sample, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}t').text = value or 'X'
    제목_표서식_복사(result, sample, maps)
    # 서식 프로필의 예시 표는 그 표의 정렬을 따른다.
    if kind != 'overview' and 기준종류 not in cache.get('예시사용', ()):
        제목_문단_가운데정렬(header, result)
    제목_괄호부연_축소(header, result)
    if sub and 기준종류 not in cache.get('예시사용', ()):
        제목_부제_크기(header, result)
    if blank:
        _칸_글_지우기(cells[0])
    # 사용자 글은 A1에만 넣는다. 나머지 칸(날짜·담당자 등)은 기준 표의 글을 그대로 두되, 요일이 붙은
    # 날짜는 오늘 날짜로 바꾼다(2026-10-03 사용자 요청: 예전에는 나머지 칸을 비웠다).
    오늘 = _datetime.date.today()
    for cell in cells[1:]:
        _칸_날짜_현행화(cell, 오늘)
    # 담당자 칸(2×2 표 B2, 2행1열 표 A2 = 마지막 칸)은 설정한 글이 있으면 그 글로 바꾼다(글자 모양은 기준 표 것).
    if kind in ('title1', 'title2') and 제목_담당자_글 and len(cells) >= 2:
        _칸_글_넣기(cells[-1], sample, 제목_담당자_글)
        for p in 제목_문단들(cells[-1]):
            for cache in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                p.remove(cache)
    # 제목·개요 표 가로 크기는 쪽 좌우 여백 사이 최대 폭으로 한다(본문폭 = 쪽 정보로 잰 폭, 없으면 그대로).
    if 본문폭:
        _서식표_가로맞춤(result, 본문폭, 비례=기준종류 in cache.get('예시사용', ()))
    return result


def _제목개요_빈줄_정리(root, 변환목록):
    """변환으로 생긴 서식 표 문단 목록[(문단, 종류)]에서 제목 표 바로 다음이 개요 표면 사이 빈 줄을 지우고,
    제목·개요 표와 그 뒤 첫 항목기호 문장 사이의 빈 줄도 지운다."""
    지운수 = 0
    for (앞, 앞종류), (뒤, 뒤종류) in zip(변환목록, 변환목록[1:]):
        if 앞종류 in ('title1', 'title2') and 뒤종류 == 'overview':
            지운수 += _문단사이_빈줄_삭제(root, 앞, 뒤)
    if 지운수:
        로그(f"제목 표와 개요 표 사이 빈 줄 {지운수}개 삭제")
    # 개요 표가 붙은 제목 표는 바로 뒤가 개요 표라 그대로이고, 개요 표(없으면 제목 표) 뒤 빈 줄만 지운다.
    뒤빈줄 = sum(_서식표_뒤_빈줄_삭제(root, 문단) for 문단, 종류 in 변환목록
                if 종류 in ('title1', 'title2', 'title3', 'overview'))
    if 뒤빈줄:
        로그(f"제목·개요 표와 첫 항목기호 문장 사이 빈 줄 {뒤빈줄}개 삭제")
    return 지운수 + 뒤빈줄


def _서식표_글(table):
    return 제목_문자열(제목_셀들(table)[0])


def _서식표_글_확인(kind, table, text, 번호=None):
    """넣은 글이 요청한 글과 같은지 확인한다(제목1·2는 부제를 나눈 쉼표만 빠짐, 중제목은 번호 칸도 확인)."""
    cells = 제목_셀들(table)
    if kind in ('midtitle', 'attach1', 'attach2'):
        ok = 제목_문자열(cells[-1]).strip() == text.strip()
        if kind == 'midtitle':
            ok = ok and 제목_문자열(cells[0]).strip() == (번호 or 'Ⅰ')
        if not ok:
            raise RuntimeError('서식 표 글 삽입 검사 실패')
        return
    if kind in ('title1', 'title2'):
        sub, title = split_title2(text)
        expected = sub + title
    else:
        expected = text.strip()
    if _서식표_글(table).strip() != expected:
        raise RuntimeError('서식 표 글 삽입 검사 실패')


def 라벨_서식표_적용(source, target=None):
    """표식이 붙은 표를 제목1·제목2·개요 서식 표로 바꾼다. 바꾼 표 수를 돌려준다.

    표식 없는 문서는 파일을 건드리지 않는다. target이 없으면 source를 덮어쓴다.
    """
    target = source if target is None else target
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    if not any(m.encode('utf-8') in data for n, data in contents.items()
               if re.fullmatch(r'Contents/section\d+\.xml', n) for m in _라벨_표식.values()):
        return 0
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
    cache = {}
    ids = _문서_표번호(sections)
    count = 0
    for name, root in sections.items():
        변환목록 = []
        for p, run in [(p, r) for p in root for r in p]:
            for table in [t for t in run if 제목_xml이름(t) == 'tbl']:
                cells = 제목_셀들(table)
                head_text = 제목_문자열(cells[0]) if cells else ''
                kind = next((k for k, m in _라벨_표식.items() if head_text.startswith(m)), None)
                if kind is None:
                    continue
                text = head_text[len(_라벨_표식[kind]):]
                result = 서식표_생성(header, kind, text, cache, 최대폭=_구역_본문폭(root),
                                    본문폭=_최종_본문폭(root))
                _서식표_글_확인(kind, result, text)
                _서식표_번호_부여(result, ids)
                run[list(run).index(table)] = result
                변환목록.append((p, kind))
                count += 1
        _제목개요_빈줄_정리(root, 변환목록)
        contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
    _hwpx_안전_저장(contents, target)
    return count


def _문서_표번호(sections):
    """문서의 표 id·zOrder 최댓값(새 표에 겹치지 않는 번호를 주기 위한 카운터)."""
    tables = [t for root in sections.values() for t in root.iter() if 제목_xml이름(t) == 'tbl']
    def biggest(attr):
        return max([int(t.get(attr)) for t in tables if (t.get(attr) or '').isdigit()] + [0])
    return {'id': biggest('id'), 'z': biggest('zOrder')}


def _서식표_번호_부여(table, ids):
    ids['id'] += 1
    ids['z'] += 1
    table.set('id', str(ids['id']))
    table.set('zOrder', str(ids['z']))


def _hwpx_안전_저장(contents, target):
    """HWPX 항목을 임시 파일에 쓴 뒤 바꿔 넣는다(한/글이 잠시 파일을 잡고 있어도 재시도)."""
    임시 = Path(str(target) + '.tmp')
    with zipfile.ZipFile(임시, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in contents.items():
            z.writestr(name, data, compress_type=zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED)
    for 시도 in range(20):
        try:
            os.replace(임시, target)
            return
        except PermissionError:
            if 시도 == 19: raise
            time.sleep(0.1)


# 준말(약어) 등록표. 작업_실행이 설정에서 채우며, 한 번에 적용 때 줄 첫 어절의 준말을 본말로 바꾼다.
준말_등록표 = {}


# 글 위치를 차지하지 않는 구역·쪽 설정 컨트롤(단 설정·쪽 번호·감추기·머리말 등). 문서 첫 문단에 흔히 함께 있다.
_문단_설정컨트롤 = frozenset({'colPr', 'secPr', 'pageNum', 'pageNumCtrl', 'pageHiding', 'newNum', 'header', 'footer'})


def _문단_일반글(p):
    """표·그림·필드가 없는 일반 글 문단이면 글 요소(t) 목록을, 아니면 None을 돌려준다.

    구역·쪽 설정 컨트롤은 글 위치를 차지하지 않으므로 허용한다(실측: 첫 문단에 쪽 번호
    컨트롤이 있으면 '제목:' 준말을 찾지 못해 제목 표가 만들어지지 않았다).
    """
    texts = []
    for run in p:
        if 제목_xml이름(run) == 'linesegarray':
            continue
        if 제목_xml이름(run) != 'run':
            return None
        for child in run:
            name = 제목_xml이름(child)
            if name == 't':
                if len(child):  # 탭·강제 줄바꿈 등이 섞인 글은 건드리지 않는다.
                    return None
                texts.append(child)
            elif name == 'secPr':
                continue
            elif name == 'ctrl':
                if any(제목_xml이름(x) not in _문단_설정컨트롤 for x in child):
                    return None
            else:
                return None
    return texts


def _문단_준말_판별(p):
    texts = _문단_일반글(p)
    if not texts:
        return None
    found = 준말_줄_판별(''.join(t.text or '' for t in texts), 준말_줄변환표(준말_등록표))
    return (texts, found) if found else None


# 준말 줄을 건너뛴 이유로 알려 줄 요소 이름(없는 이름은 XML 이름 그대로 보여 준다).
_준말_제외요소_이름 = {'tbl': '표', 'pic': '그림', 'ole': 'OLE 개체', 'rect': '글상자', 'equation': '수식',
                     'fieldBegin': '필드(누름틀·하이퍼링크 등)', 'fieldEnd': '필드 끝', 'bookmark': '책갈피',
                     'footNote': '각주', 'endNote': '미주', 'autoNum': '자동 번호', 'tab': '탭',
                     'fwSpace': '고정폭 빈칸', 'nbSpace': '묶음 빈칸', 'lineBreak': '강제 줄바꿈'}


def _문단_준말_제외사유(p):
    """준말 줄처럼 시작하지만 글 사이에 표·필드·탭 같은 요소가 있어 바꾸지 않는 문단이면 알림 문구를, 아니면 None.

    실측(2026-09-30): 첫 문단의 쪽 번호 컨트롤 때문에 '제목:' 줄이 아무 기록 없이 건너뛰어져
    원인을 찾기 어려웠다. 바꾸지 않는 이유를 작업 로그에 남긴다. 공문 붙임 목록('붙임 : 1. … 1부.  끝.')처럼
    규칙상 바꾸지 않는 줄도 이유를 남긴다.
    """
    texts = _문단_일반글(p)
    if texts is not None:
        줄 = ''.join(t.text or '' for t in texts)
        사유 = 준말_제외사유(줄, 준말_줄변환표(준말_등록표)) if texts else ''
        return f"[준말 제외] '{줄.strip()[:40]}': {사유}" if 사유 else None
    글, 요소 = [], []
    for run in p:
        이름 = 제목_xml이름(run)
        if 이름 == 'linesegarray':
            continue
        if 이름 != 'run':
            요소.append(이름)
            continue
        for child in run:
            name = 제목_xml이름(child)
            if name == 't':
                글.append(''.join(child.itertext()))
                요소.extend(제목_xml이름(x) for x in child)
            elif name == 'ctrl':
                요소.extend(제목_xml이름(x) for x in child if 제목_xml이름(x) not in _문단_설정컨트롤)
            elif name != 'secPr':
                요소.append(name)
    줄 = ''.join(글)
    if not 요소 or not 준말_줄_판별(줄, 준말_줄변환표(준말_등록표)):
        return None
    이름들 = ', '.join(dict.fromkeys(_준말_제외요소_이름.get(x, x) for x in 요소))
    return f"[준말 제외] '{줄.strip()[:40]}': 줄 안에 있는 {이름들} 때문에 본말로 바꾸지 않습니다."


def _문단_글_바꾸기(p, texts, remove, insert):
    """문단 앞의 remove 글자를 지우고 그 자리에 insert를 넣는다(나머지 글의 글자 모양은 유지)."""
    left = remove
    for t in texts:
        value = t.text or ''
        cut = min(left, len(value))
        t.text = value[cut:]
        left -= cut
    texts[0].text = insert + (texts[0].text or '')
    for lineseg in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
        p.remove(lineseg)


def 준말_hwpx_처리(source, target=None, selections=None):
    """줄 첫 어절이 등록한 준말이고 콜론이 이어지면 본말로 바꾼다.

    서식 표 본말은 콜론 뒤 글을 표 A1 칸에 넣고 준말 줄의 글을 지운다. 문구 본말은
    준말과 콜론을 본말로 바꾸고 나머지 글은 그대로 둔다. 본문(구역 바로 아래) 문단만 대상이다.
    """
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
    body = {n: [c for c in root if 제목_xml이름(c) == 'p'] for n, root in sections.items()}
    if selections is None:
        result = {}
        for name, paras in body.items():
            result[name] = [(i, found[1][0], found[1][1]) for i, p in enumerate(paras)
                            for found in [_문단_준말_판별(p) or (None, None)] if found[1]]
            for p in paras:
                사유 = _문단_준말_제외사유(p)
                if 사유:
                    로그(사유)
        return result
    if not any(items for items in selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    para_group = next((x for x in header.iter() if 제목_xml이름(x) == 'paraProperties'), None)
    has_default_para = para_group is not None and any(x.get('id') == '0' for x in para_group)
    cache, ids, count = {}, _문서_표번호(sections), 0
    for name, items in selections.items():
        변환목록 = []
        for index, key, _ in items:
            p = body[name][index]
            judged = _문단_준말_판별(p)
            if judged is None or judged[1][0] != key:
                raise RuntimeError('처리 중 준말 줄이 바뀌어 준말 변환을 중단했습니다.')
            texts, (_, rest, prefix_len) = judged
            spec = 준말_등록표[key]
            if spec['type'] == 'text':
                replacement = spec['value'] + (' ' if rest else '')
                expected = replacement + rest
                _문단_글_바꾸기(p, texts, prefix_len, replacement)
                if ''.join(t.text or '' for t in texts) != expected:
                    raise RuntimeError('준말 문구 바꾸기 검사 실패')
            else:
                base_char = next((r.get('charPrIDRef') for r in p if 제목_xml이름(r) == 'run'
                                  and any(제목_xml이름(c) == 't' for c in r)), '0')
                numeral = 준말_로마자(key) if spec['value'] == 'midtitle' else None
                table = 서식표_생성(header, spec['value'], rest, cache, numeral, _구역_본문폭(sections[name]),
                                   _최종_본문폭(sections[name]))
                _서식표_글_확인(spec['value'], table, rest, numeral)
                _서식표_번호_부여(table, ids)
                for run in [r for r in p if 제목_xml이름(r) == 'run']:
                    had_text = any(제목_xml이름(c) == 't' for c in run)
                    for t in [c for c in run if 제목_xml이름(c) == 't']:
                        run.remove(t)
                    if had_text and not len(run):
                        p.remove(run)
                for lineseg in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                    p.remove(lineseg)
                holder = XML_자식_추가(p, p, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}run',
                                       attrib={'charPrIDRef': base_char})
                holder.append(table)
                XML_자식_추가(holder, p, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}t')
                if has_default_para:  # 들여쓰기·내어쓰기가 표 위치를 밀지 않도록 기본 문단 모양을 쓴다.
                    p.set('paraPrIDRef', '0')
                p.set('styleIDRef', '0')
                변환목록.append((p, spec['value']))
            count += 1
        # '제목1:' 줄과 '개요:' 줄 사이의 빈 줄은 두 서식 표 사이 빈 줄이 되므로 지운다.
        _제목개요_빈줄_정리(sections[name], 변환목록)
        contents[name] = ET.tostring(sections[name], encoding='utf-8', xml_declaration=True)
    contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
    _hwpx_안전_저장(contents, target)
    return count


def 제목개요폭_hwpx_처리(source, target=None, selections=None):
    """문서의 제목 표와 바로 뒤 개요 표의 가로 크기를 쪽 좌우 여백 사이 최대 폭으로 맞춘다.

    작업 맨 앞(준말 변환 바로 뒤)에서 표·칸 너비만 바꾼다(2026-10-03 사용자 요청: 가로폭 맞춤을 최대한 앞당김).
    표준서식이 편집 여백을 바꿀 예정이면 바뀐 뒤의 여백으로 잰다(_최종_본문폭). 제목·개요 서식 단계도 같은 폭으로
    다시 맞추므로 이미 맞으면 그 단계에서는 바뀌지 않는다. 이미 최대 폭인 표는 대상에서 뺀다.
    """
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items()
                if re.fullmatch(r'Contents/section\d+\.xml', n)}

    def 표들(root):
        return [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']

    def 목표폭(table, 본문폭):
        out = 제목_자식(table, 'outMargin')
        try:
            return int(본문폭) - ((int(out.get('left', '0')) + int(out.get('right', '0'))) if out is not None else 0)
        except ValueError:
            return None

    if selections is None:
        # 서식 복사 간격 규칙(제목·개요 뒤 첫 문장 간격)은 제목 표가 있는 문서에만 쓴다.
        globals()["_문서_제목표_있음"] = any(제목_대상찾기(root, header) for root in sections.values())

    def 대상(root):
        본문폭 = _최종_본문폭(root)
        if not 본문폭:
            return []
        tables = 표들(root)
        found = []
        for index, _ in 제목_대상찾기(root, header):
            found.append(index)
            if index + 1 < len(tables) and 개요_표인가(tables[index + 1]):
                found.append(index + 1)
        result = []
        for index in dict.fromkeys(found):
            size = 제목_자식(tables[index], 'sz')
            폭 = 목표폭(tables[index], 본문폭)
            if size is not None and 폭 and size.get('width') != str(폭):
                result.append(index)
        return result

    if selections is None:
        return {n: 대상(root) for n, root in sections.items()}
    if not any(items for items in selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    count = 0
    for name, items in selections.items():
        root = sections[name]
        tables, 본문폭 = 표들(root), _최종_본문폭(root)
        for index in items:
            table = tables[index]
            before = 제목_문자열(table)
            _서식표_가로맞춤(table, 본문폭)
            # 칸 문단의 줄 배치 캐시는 한/글이 새 폭으로 다시 계산한다.
            for p in (x for x in table.iter() if 제목_xml이름(x) == 'p'):
                for cache in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                    p.remove(cache)
            if 제목_문자열(table) != before:
                raise RuntimeError('제목·개요 표 가로 크기 맞춤 중 글 보존 검사에 실패했습니다.')
            count += 1
        contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    _hwpx_안전_저장(contents, target)
    로그(f"제목·개요 표 가로 크기 맞춤: {count}개 (쪽 좌우 여백 사이 최대 폭"
         + (", 표준서식 편집 여백 반영)" if _예정_좌우여백() else ")"))
    return count


def 상자서식_hwpx_처리(source, target=None, selections=None):
    """서식 프로필의 한 칸 상자 예시로 문서의 짧은 한 칸 상자(‘< 핵심 추진과제 >’ 등) 서식을 맞춘다.

    제목 표 바로 뒤의 개요 표는 제목·개요 단계가 맡으므로 뺀다. 내용이 많은 상자(글 문단 4개 이상)는 문단마다
    모양이 달라 한 가지 예시로 덮지 않는다. 표·칸·문단·글자 서식만 바꾸고 글은 그대로 둔다.
    """
    예시 = _서식표_예시('box')
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items()
                if re.fullmatch(r'Contents/section\d+\.xml', n)}

    def 표들(root):
        return [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']

    def 대상(root):
        if 예시 is None:
            return []
        tables, result = 표들(root), []
        for index, table in enumerate(tables):
            if 서식표_종류판별(table) != 'box':
                continue
            if index > 0 and 제목_유형판별(tables[index - 1], 빈칸허용=True):
                continue
            if len([p for p in 제목_문단들(제목_셀들(table)[0]) if 제목_문자열(p).strip()]) > 3:
                continue
            result.append(index)
        return result

    if selections is None:
        return {n: 대상(root) for n, root in sections.items()}
    if 예시 is None or not any(items for items in selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    sample, maps = 예시[1], 제목_참조병합(header, 예시[0])
    count = 0
    for name, items in selections.items():
        root = sections[name]
        tables = 표들(root)
        for index in items:
            table = tables[index]
            before = 제목_문자열(table)
            제목_표서식_복사(table, sample, maps, 상자=True)
            if 제목_문자열(table) != before:
                raise RuntimeError('한 칸 상자 서식 적용 중 글 보존 검사에 실패했습니다.')
            count += 1
        contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
    _hwpx_안전_저장(contents, target)
    로그(f"한 칸 상자 서식: {count}개를 예시 보고서의 상자 모양으로 맞춤")
    return count


def 쪽번호_hwpx_처리(source, target=None, selections=None):
    """서식 프로필의 예시 보고서와 같은 쪽 번호 모양(위치·번호 모양·줄표)으로 문서의 쪽 번호를 맞춘다.

    쪽 번호가 없는 문서에는 넣지 않는다(2026-10-04 결정 4: 모양만 복사).
    """
    모양 = dict(표준서식_설정.get("쪽번호") or {})
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items()
                if re.fullmatch(r'Contents/section\d+\.xml', n)}

    def 쪽번호들(root):
        return [x for x in root.iter() if 제목_xml이름(x) == 'pageNum']

    if selections is None:
        return {n: [i for i, x in enumerate(쪽번호들(root)) if any(x.get(k) != v for k, v in 모양.items())]
                if 모양 else [] for n, root in sections.items()}
    if not 모양 or not any(items for items in selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    count = 0
    for name, items in selections.items():
        found = 쪽번호들(sections[name])
        for index in items:
            found[index].attrib.update(모양)
            count += 1
        contents[name] = ET.tostring(sections[name], encoding='utf-8', xml_declaration=True)
    _hwpx_안전_저장(contents, target)
    로그(f"쪽 번호 모양: {count}개를 예시 보고서와 같게(" + ", ".join(f"{k}={v}" for k, v in 모양.items()) + ")")
    return count


def 준말_사용표_만들기(설정):
    """설정의 준말 등록과 기본 준말(제목1·제목2·개요·붙임·로1~로10)을 합친 사용표. 사용자가 같은 준말을 등록하면 그 등록이 우선한다."""
    return 준말_기본_병합(설정.get('abbreviations'), 설정.get('abbreviation_defaults', True))


def 준말_선행적용(원본문서경로, 현재문서_기준=True, 변경알림=None):
    """문서의 준말 줄을 본말로 바꾼 결과를 한 번만 다시 연다(사용표가 비면 아무것도 안 함).

    현재문서_기준이 아니면(앞 단계가 문서를 바꾸지 않았으면) 원본 HWPX를 직접 읽어 확인하므로
    바꿀 줄이 없을 때는 저장·다시 열기도 하지 않는다. 변경알림 dict에 changed를 채워 준다.
    """
    if not 준말_등록표:
        return True
    return 제목붙임_선행적용(원본문서경로, 현재문서_기준=현재문서_기준,
                            처리목록=((True, '준말 변환', 준말_hwpx_처리, 'abbrev.hwpx'),), 변경알림=변경알림)


# 기본 표 서식을 입혔으면(준말 '표') COM 표 머리글·본문 서식 단계가 그 서식을 덮지 않게 건너뛴다.
기본표서식_적용됨 = False


def 기본표서식():
    """기본 표 서식. 선택한 서식 프로필이 예시 보고서의 일반 표에서 배운 서식이 있으면 그것(결정 5), 없으면 준말
    '표'의 본말(배운 서식이 없으면 내장 기본값). 준말 '표'가 없거나 다른 본말이면 None."""
    if 활성_표서식_프로필 and 표서식_유효(활성_표서식_프로필):
        return 활성_표서식_프로필
    return 준말_표서식(준말_등록표)


def _기본표서식_대상인가(table):
    """2행 2열 이상 일반 표만 대상이다. 제목(준말로 만든 빈 정보 칸 제목 표 포함)·중제목·붙임 서식 표는 뺀다."""
    return bool(표서식_모양인가(table) and not (
        제목_유형판별(table, 빈칸허용=True) or 중제목_글칸들(table) or 붙임_유형판별(table)))


def 기본표서식_hwpx_처리(source, target=None, selections=None):
    """문서의 일반 표에 기본 표 서식(준말 '표'의 본말)을 입힌다. 칸 글은 바꾸지 않는다.

    예시 표의 같은 위치 칸에서 테두리·바탕색·글꼴(종류·크기·굵게·장평·자간)·세로 정렬을 가져오고,
    머리글과 한 줄에 들어가는 짧은 문단만 예시 정렬로 바꾼다. 내장 기본값은 본문 칸 가운데 첫 열이 아닌
    칸(B2·B3 …)의 문장을 길이와 관계없이 왼쪽 정렬한다(숫자·날짜 칸은 예시 정렬, docfit_core.table_style).
    """
    style = 기본표서식()
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}

    def 표들(root):
        return [t for t in root.iter() if 제목_xml이름(t) == 'tbl']

    if selections is None:
        if style is None:
            return {n: [] for n in sections}
        # 문서 머리의 결재란·보고자 표와 제목처럼 큰 글자가 든 표는 데이터 표가 아니라 일반 표 서식을 입히지 않는다
        # (서식 요소 분석의 데이터 표와 같은 기준, 2026-10-04).
        순서 = sorted(sections, key=lambda n: int(re.search(r'(\d+)\.xml$', n).group(1)))
        머리표 = {id(t) for t in 서식요소.head_block_tables([sections[n] for n in 순서], header)}
        return {n: [i for i, t in enumerate(표들(root)) if _기본표서식_대상인가(t) and id(t) not in 머리표]
                for n, root in sections.items()}
    if style is None or not any(items for items in selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    저장소 = 표서식_저장소(header, style)
    count = 0
    for name, items in selections.items():
        root = sections[name]
        found = 표들(root)
        for index in items:
            table = found[index]
            if not _기본표서식_대상인가(table):
                raise RuntimeError('처리 중 표 구조가 바뀌어 기본 표 서식 적용을 중단했습니다.')
            before = _표_텍스트(table)
            표서식_적용(저장소, table)
            if _표_텍스트(table) != before:
                raise RuntimeError('기본 표 서식 적용 중 표 내용 보존 검사에 실패했습니다.')
            count += 1
        contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
    _hwpx_안전_저장(contents, target)
    return count


def 표너비_hwpx_처리(source, target=None, selections=None):
    """가로로 칸이 둘 이상인 본문 표의 열 너비를 칸 글자 수(글자 사이 빈칸 포함)에 비례해 나누고,
    표 폭은 쪽 좌우 여백 사이 최대 폭으로 맞춘다(docfit_core.table_width). 칸 글은 바꾸지 않는다.

    제목·중제목·붙임 서식 표와 한 칸 상자는 서식 표 자체의 배치를 쓰므로 건드리지 않는다. 쪽 정보(pagePr)가
    없는 구역의 표도 폭을 알 수 없어 그대로 둔다.
    """
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}

    def 표들(root):
        # 본문에 놓인 표만(칸 안의 표는 바깥 칸 폭에 묶여 있어 다루지 않는다).
        return [t for p in root for r in p for t in r if 제목_xml이름(t) == 'tbl']

    def 대상인가(table):
        return 서식표_종류판별(table) is None and 표너비_대상인가(table)

    if selections is None:
        return {n: ([i for i, t in enumerate(표들(root)) if 대상인가(t)] if _구역_본문폭(root, None) else [])
                for n, root in sections.items()}
    if not any(items for items in selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    index = 서식요소.HeaderIndex(header)
    count = 0
    for name, items in selections.items():
        root = sections[name]
        found = 표들(root)
        본문폭 = _구역_본문폭(root, None)
        for number in items:
            table = found[number]
            if not 대상인가(table):
                raise RuntimeError('처리 중 표 구조가 바뀌어 표 칸 너비 맞춤을 중단했습니다.')
            before = _표_텍스트(table)
            if 표너비_맞춤(table, 본문폭, index):
                count += 1
            if _표_텍스트(table) != before:
                raise RuntimeError('표 칸 너비 맞춤 중 표 내용 보존 검사에 실패했습니다.')
        contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    _hwpx_안전_저장(contents, target)
    로그(f"표 칸 너비 맞춤: 표 {count}개(글자 수 비례, 쪽 좌우 여백 폭)")
    return count


def 기본표서식_선행적용(원본문서경로, 현재문서_기준=False, 변경알림=None):
    """문서의 일반 표에 기본 표 서식을 입힌 결과를 한 번만 다시 연다(대상 표가 없으면 다시 열지 않음)."""
    return 제목붙임_선행적용(원본문서경로, 현재문서_기준=현재문서_기준,
                            처리목록=((True, '기본 표 서식', 기본표서식_hwpx_처리, 'table_style.hwpx'),), 변경알림=변경알림)


def _위첨자_글자모양(header, char_id, cache):
    """글자모양 char_id에 위첨자만 더한 사본의 ID를 돌려준다(이미 위첨자면 그대로, 같은 원본은 사본 하나를 공유)."""
    if char_id in cache:
        return cache[char_id]
    group = next(x for x in header.iter() if 제목_xml이름(x) == 'charProperties')
    source = next((x for x in group if x.get('id') == char_id), None)
    if source is None or any(제목_xml이름(x) == 'supscript' for x in source):
        cache[char_id] = char_id
        return char_id
    clone = copy.deepcopy(source)
    for sub in [x for x in clone if 제목_xml이름(x) == 'subscript']:
        clone.remove(sub)
    XML_자식_추가(clone, source, tag=source.tag.rsplit('}', 1)[0] + '}supscript')
    new_id = str(max([int(x.get('id')) for x in group if (x.get('id') or '').isdigit()] + [-1]) + 1)
    clone.set('id', new_id)
    group.append(clone)
    group.set('itemCnt', str(len(group)))
    cache[char_id] = new_id
    return new_id


def _문단_별표_대상(p, header_super_ids):
    """(글 요소 목록, 새로 위첨자로 만들 별표 글자 위치 집합)을 돌려준다. 대상이 없으면 None."""
    texts = _문단_일반글(p)
    if not texts:
        return None
    full = ''.join(t.text or '' for t in texts)
    spans = 별표_위치(full)
    if not spans:
        return None
    return texts, spans


def 별표위첨자_hwpx_처리(source, target=None, selections=None):
    """항목기호 문장의 단어 뒤 * / **를 위첨자로 바꾼다(글은 그대로, 별표 글자모양에 위첨자만 더함)."""
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
    super_ids = {x.get('id') for x in header.iter() if 제목_xml이름(x) == 'charPr'
                 and any(제목_xml이름(c) == 'supscript' for c in x)}
    body = {n: [c for c in root if 제목_xml이름(c) == 'p'] for n, root in sections.items()}

    def plan(p):
        """별표 위치 중 아직 위첨자가 아닌 것만 글 요소별 (요소, 시작, 끝) 조각으로 나눈다."""
        found = _문단_별표_대상(p, super_ids)
        if found is None:
            return []
        texts, spans = found
        pieces, offset = [], 0
        for t in texts:
            length = len(t.text or '')
            for start, end in spans:
                lo, hi = max(start, offset), min(end, offset + length)
                if lo < hi:
                    pieces.append((t, lo - offset, hi - offset))
            offset += length
        return pieces

    def already(p, piece):
        run = next(r for r in p if piece[0] in list(r))
        return run.get('charPrIDRef') in super_ids

    if selections is None:
        result = {}
        for name, paras in body.items():
            result[name] = [(i, sum(1 for pc in plan(p) if not already(p, pc)))
                            for i, p in enumerate(paras)
                            if any(not already(p, pc) for pc in plan(p))]
        return result
    if not any(items for items in selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    cache, count = {}, 0
    for name, items in selections.items():
        for index, _ in items:
            p = body[name][index]
            by_text = {}
            for piece in plan(p):
                by_text.setdefault(id(piece[0]), []).append(piece)
            before = ''.join(제목_문자열(r) for r in p if 제목_xml이름(r) == 'run')
            for pieces in by_text.values():
                t = pieces[0][0]
                run = next(r for r in p if t in list(r))
                if len(run) != 1 or any(제목_xml이름(x) != 't' for x in run) or len(t):
                    continue  # 다른 요소가 섞인 글 묶음은 건드리지 않는다.
                if run.get('charPrIDRef') in super_ids:
                    continue
                text, cuts, position = t.text or '', [], 0
                for _, lo, hi in sorted(pieces, key=lambda x: x[1]):
                    cuts += [(position, lo, False), (lo, hi, True)]
                    position = hi
                cuts.append((position, len(text), False))
                at = list(p).index(run)
                p.remove(run)
                for lo, hi, mark in [c for c in cuts if c[0] < c[1]]:
                    piece_run = XML_요소_생성(run, tag=run.tag, attrib=dict(run.attrib))
                    if mark:
                        piece_run.set('charPrIDRef', _위첨자_글자모양(header, run.get('charPrIDRef'), cache))
                        count += 1
                    XML_자식_추가(piece_run, t, tag=t.tag, attrib=dict(t.attrib)).text = text[lo:hi]
                    p.insert(at, piece_run)
                    at += 1
            if ''.join(제목_문자열(r) for r in p if 제목_xml이름(r) == 'run') != before:
                raise RuntimeError('별표 위첨자 적용 중 문장 글이 바뀌어 중단했습니다.')
            for lineseg in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                p.remove(lineseg)
        contents[name] = ET.tostring(sections[name], encoding='utf-8', xml_declaration=True)
    contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
    _hwpx_안전_저장(contents, target)
    return count


def 별표위첨자_선행적용(원본문서경로, 현재문서_기준=True, 변경알림=None):
    """문서의 별표(*, **)를 위첨자로 바꾼 결과를 한 번만 다시 연다(바꿀 별표가 없으면 다시 열지 않음)."""
    return 제목붙임_선행적용(원본문서경로, 현재문서_기준=현재문서_기준,
                            처리목록=((True, '별표 위첨자', 별표위첨자_hwpx_처리, 'asterisk.hwpx'),), 변경알림=변경알림)


def _한글_글꼴표(header):
    """언어별 글꼴 ID → 글꼴 이름 표({언어(소문자): {id: 이름}})."""
    return {ff.get('lang', '').lower(): {f.get('id'): f.get('face') for f in ff}
            for ff in header.iter() if 제목_xml이름(ff) == 'fontface'}


def _글꼴_확보(header, face, cache):
    """모든 언어 글꼴 그룹에 face가 있게 하고 {언어(소문자): ID}를 돌려준다(없으면 첫 글꼴을 본떠 추가)."""
    if face in cache:
        return cache[face]
    result = {}
    for ff in [x for x in header.iter() if 제목_xml이름(x) == 'fontface']:
        found = next((f for f in ff if f.get('face') == face), None)
        if found is None:
            found = copy.deepcopy(next(iter(ff)))
            found.set('face', face)
            found.set('id', str(max([int(f.get('id')) for f in ff if (f.get('id') or '').isdigit()] + [-1]) + 1))
            ff.append(found)
            ff.set('fontCnt', str(len(ff)))
        result[ff.get('lang', '').lower()] = found.get('id')
    cache[face] = result
    return result


def _글자모양_글꼴크기(char, faces):
    """글자모양의 (언어별 글꼴 이름 집합, 크기 pt)."""
    ref = next((x for x in char if 제목_xml이름(x) == 'fontRef'), None)
    names = {faces.get(lang, {}).get(fid) for lang, fid in (ref.attrib.items() if ref is not None else [])}
    return names, int(char.get('height', '0')) / 100


def _본문기호_글꼴(header, paras):
    """붙임 묶음에 맞출 (글꼴 이름, 크기 pt). 기호 서식을 쓰면 표준서식의 ㅇ 규칙, 아니면 문서 ㅇ 문장의 대표 글꼴."""
    if 표준서식_기호_사용:
        for rule in 표준서식_설정.get('기호_규칙', []):
            if rule[0] == 'ㅇ':
                return rule[2], float(rule[3])
    faces = _한글_글꼴표(header)
    chars = {x.get('id'): x for x in header.iter() if 제목_xml이름(x) == 'charPr'}
    tally = {}
    for p in paras:
        texts = _문단_일반글(p)
        if not texts or leading_marker(''.join(t.text or '' for t in texts))[0] != 'ㅇ':
            continue
        for run in [r for r in p if 제목_xml이름(r) == 'run']:
            length = sum(len(t.text or '') for t in run if 제목_xml이름(t) == 't')
            char = chars.get(run.get('charPrIDRef'))
            if length and char is not None:
                _, size = _글자모양_글꼴크기(char, faces)
                ref = next(x for x in char if 제목_xml이름(x) == 'fontRef')
                key = (faces.get('hangul', {}).get(ref.get('hangul')), size)
                tally[key] = tally.get(key, 0) + length
    return max(tally, key=tally.get) if tally else None


def 붙임글꼴_hwpx_처리(source, target=None, selections=None):
    """'붙임 …'부터 '끝.'까지 묶음의 모든 문장을 항목기호 ㅇ와 같은 글꼴 종류·크기로 맞춘다(글은 그대로)."""
    with zipfile.ZipFile(source) as z:
        contents = {n: z.read(n) for n in z.namelist()}
    for name, data in contents.items():
        if name.startswith('Contents/') and name.endswith('.xml'):
            for _, pair in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
                if not re.fullmatch(r'ns\d+', pair[0]): XML_네임스페이스_등록(*pair)
    header = safe_xml_fromstring(contents['Contents/header.xml'])
    sections = {n: safe_xml_fromstring(data) for n, data in contents.items() if re.fullmatch(r'Contents/section\d+\.xml', n)}
    body = {n: [c for c in root if 제목_xml이름(c) == 'p'] for n, root in sections.items()}
    goal = _본문기호_글꼴(header, [p for paras in body.values() for p in paras])
    faces = _한글_글꼴표(header)
    chars = {x.get('id'): x for x in header.iter() if 제목_xml이름(x) == 'charPr'}

    def paragraph_text(p):
        texts = _문단_일반글(p)
        return None if texts is None else ''.join(t.text or '' for t in texts)

    def runs_with_text(p):
        return [r for r in p if 제목_xml이름(r) == 'run' and any(제목_xml이름(t) == 't' and (t.text or '') for t in r)]

    def needs_change(p):
        for run in runs_with_text(p):
            char = chars.get(run.get('charPrIDRef'))
            if char is not None:
                names, size = _글자모양_글꼴크기(char, faces)
                if names != {goal[0]} or abs(size - goal[1]) > 0.001:
                    return True
        return False

    if selections is None:
        if goal is None:
            return {n: [] for n in body}
        return {n: [(s, e) for s, e in 붙임묶음_찾기([paragraph_text(p) for p in paras])
                    if any(needs_change(p) for p in paras[s:e + 1])]
                for n, paras in body.items()}
    if goal is None or not any(items for items in selections.values()):
        if target is not None: shutil.copyfile(source, target)
        return 0
    font_cache, char_cache, count = {}, {}, 0
    group = next(x for x in header.iter() if 제목_xml이름(x) == 'charProperties')
    for name, items in selections.items():
        for start, end in items:
            for p in body[name][start:end + 1]:
                before = 제목_문자열(p)
                for run in runs_with_text(p):
                    old = run.get('charPrIDRef')
                    if old not in char_cache:
                        source_char = chars.get(old)
                        names, size = _글자모양_글꼴크기(source_char, faces) if source_char is not None else ({None}, 0)
                        if source_char is None or (names == {goal[0]} and abs(size - goal[1]) < 0.001):
                            char_cache[old] = old
                        else:
                            clone = copy.deepcopy(source_char)
                            clone.set('height', str(int(round(goal[1] * 100))))
                            ids = _글꼴_확보(header, goal[0], font_cache)
                            ref = next(x for x in clone if 제목_xml이름(x) == 'fontRef')
                            for lang in list(ref.attrib):
                                if lang.lower() in ids:
                                    ref.set(lang, ids[lang.lower()])
                            new_id = str(max([int(x.get('id')) for x in group if (x.get('id') or '').isdigit()] + [-1]) + 1)
                            clone.set('id', new_id)
                            group.append(clone)
                            group.set('itemCnt', str(len(group)))
                            chars[new_id] = clone
                            faces = _한글_글꼴표(header)
                            char_cache[old] = new_id
                    run.set('charPrIDRef', char_cache[old])
                if 제목_문자열(p) != before:
                    raise RuntimeError('붙임 글꼴 통일 중 문장 글이 바뀌어 중단했습니다.')
                for lineseg in [x for x in p if 제목_xml이름(x) == 'linesegarray']:
                    p.remove(lineseg)
                count += 1
        contents[name] = ET.tostring(sections[name], encoding='utf-8', xml_declaration=True)
    contents['Contents/header.xml'] = ET.tostring(header, encoding='utf-8', xml_declaration=True)
    _hwpx_안전_저장(contents, target)
    return count


def 글자서식_선행적용(원본문서경로, 별표위첨자=True, 붙임글꼴=True, 현재문서_기준=True, 변경알림=None):
    """별표 위첨자·붙임 글꼴 통일을 한 번에 처리해 결과를 한 번만 다시 연다(둘 다 글자 모양만 바꾸는 단계)."""
    return 제목붙임_선행적용(
        원본문서경로, 현재문서_기준=현재문서_기준, 변경알림=변경알림,
        처리목록=((별표위첨자, '별표 위첨자', 별표위첨자_hwpx_처리, 'asterisk.hwpx'),
                  (붙임글꼴, '붙임 글꼴', 붙임글꼴_hwpx_처리, 'attach_font.hwpx')))


def 붙임2종_현재문서_조사(원본문서경로):
    return 서식구조_조사(원본문서경로, 붙임_hwpx_처리, '붙임')


def 제목붙임_선행적용(원본문서경로, 현재문서_기준=False, 처리목록=None, 변경알림=None):
    """제목·개요·붙임을 먼저 처리하고 결과 문서를 한 번만 연다.

    원본 HWPX는 읽기만 한다. HWP는 이미 열린 작업용 한글에서 한 번
    변환한다. 별도 한글 생성/등록/원본 재열기를 수행하지 않는다.
    현재문서_기준이면 원본 파일 대신 지금 열린 문서(예: 자간 초기화를 마친
    문서)를 스냅샷으로 저장해 그 위에 서식을 입힌다.
    처리목록 항목은 (사용, 이름, 처리함수, 파일명[, 진행 단계명])이며 앞 항목의 결과 HWPX를
    다음 항목이 이어 받는다. 진행 단계명이 있으면 화면의 진행 단계를 그 이름으로 표시한다.
    """
    if 처리목록 is None:
        처리목록 = (
            (제목4종_사용, '제목·개요', 제목_hwpx_처리, 'title.hwpx'),
            (중제목_사용, '중제목', 중제목_hwpx_처리, 'midtitle.hwpx'),
            (붙임2종_사용, '붙임', 붙임_hwpx_처리, 'attachment.hwpx'),
        )
    if not any(enabled for enabled, *_ in 처리목록):
        return True
    folder = Path(tempfile.mkdtemp(prefix='hwp_format_first_'))
    스냅샷_저장시도 = False
    try:
        source = Path(원본문서경로)
        if 현재문서_기준:
            스냅샷_저장시도 = True
            source = _제목_임시hwpx_저장(folder / 'source.hwpx')
        elif source.suffix.lower() != '.hwpx':
            로그('선행 서식: 현재 한글에서 HWPX 변환 시작')
            스냅샷_저장시도 = True
            source = _제목_임시hwpx_저장(folder / 'source.hwpx')
            로그('선행 서식: HWPX 변환 완료')
        changed = False
        for enabled, name, processor, filename, *진행단계 in 처리목록:
            if 중단_요청됨():
                return False
            if not enabled:
                continue
            if 진행단계:
                단계표시(진행단계[0])
            로그(f'{name} 구조 직접 분석 시작')
            selections = processor(source)
            count = sum(len(items) for items in selections.values())
            로그(f'{name} 구조 직접 분석 완료: {count}개')
            if not count:
                continue
            target = folder / filename
            processor(source, target, selections)
            source = target
            changed = True
            로그(f'{name} 선행 서식 파일 생성 완료')
        if 변경알림 is not None:
            변경알림['changed'] = changed
        if changed:
            if 중단_요청됨():
                return False
            로그('선행 서식 결과 열기 시작')
            if 한글_문서_열기(hwp, source, 'HWPX', 'forceopen:true') is False:
                raise RuntimeError('선행 서식 결과를 열지 못했습니다.')
            로그('선행 서식 결과 열기 완료')
        return True
    except Exception:
        # 현재 문서 기준 스냅샷 SaveAs 후 분석이 실패하면 한글은 임시
        # source.hwpx를 계속 열고 있을 수 있다. 원본으로 되돌려 임시파일
        # 핸들이 남는 문제와 다음 작업의 잘못된 문서 대상을 함께 막는다.
        if 스냅샷_저장시도:
            원본 = Path(원본문서경로)
            형식 = 'HWPX' if 원본.suffix.lower() == '.hwpx' else 'HWP'
            try:
                if 한글_문서_열기(hwp, 원본, 형식, 'forceopen:true') is False:
                    raise RuntimeError('원본 문서 재열기 결과가 False입니다.')
                로그('선행 서식 실패 후 원본 문서 복구 완료')
            except Exception as 복구오류:
                로그(f'선행 서식 오류 후 원본 문서 복구 실패: {복구오류}')
        raise
    finally:
        _제목_임시폴더_정리(folder)


def 정밀표_선행적용():
    """현재 문서를 HWPX로 스냅샷 저장한 뒤 선택 프로필의 표 서식을 적용한다."""
    if not 활성_정밀표_프로필 or not 활성_정밀표_프로필.get("tables"):
        return True
    folder = Path(tempfile.mkdtemp(prefix="hwp_precise_table_"))
    try:
        source = _제목_임시hwpx_저장(folder / "before.hwpx")
        target = folder / "after.hwpx"
        result = 정밀표_서식_적용(source, target, 활성_정밀표_프로필)
        if result["applied"]:
            # 예시 표 서식을 덮어쓴 뒤에도 표 칸 날짜는 한 줄로 둔다.
            날짜칸 = 표날짜칸_hwpx_처리(target)
            if any(날짜칸.values()):
                표날짜칸_hwpx_처리(target, target, 날짜칸)
            if 한글_문서_열기(hwp, target, "HWPX", "forceopen:true") is False:
                raise RuntimeError("정밀 표 서식 결과를 열지 못했습니다.")
        로그(
            f"일반 표 정밀 복제: 적용 {result['applied']}개 / 건너뜀 {result['skipped']}개"
        )
        for match in result["matches"]:
            진단로그(
                f"[표 매칭] 대상 {match['target'] + 1}번 ← 프로필 {match['source'] + 1}번 / "
                f"점수 {match['score']:.1f} / 병합·크기 {'복제' if match['geometry'] else '보존'}"
            )
        return True
    finally:
        _제목_임시폴더_정리(folder)


def 붙임2종_현재문서_적용(selections):
    if not any(items for items in selections.values()):
        로그('붙임 서식 대상 없음: 붙임서식을 적용하지 않습니다.')
        return
    folder = Path(tempfile.mkdtemp(prefix='hwp_attach_apply_'))
    try:
        source, target = folder/'before.hwpx', folder/'after.hwpx'
        _제목_임시hwpx_저장(source)
        count = 붙임_hwpx_처리(source, target, selections)
        if 한글_문서_열기(hwp, target, 'HWPX', 'forceopen:true') is False: raise RuntimeError('붙임 적용 결과를 열지 못했습니다.')
        로그(f'붙임 서식 자동 적용: {count}개 / 유형 ' + ', '.join(str(k) for v in selections.values() for _, k in v))
    finally:
        _제목_임시폴더_정리(folder)

def 설정_폴더():
    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    if appdata:
        return Path(appdata) / "HwpAutoDocFit"
    return Path.home() / ".hwp_auto_docfit"

def 서식프로파일_폴더():
    return 설정_폴더() / "formats"

def 서식예시_폴더():
    """서식마다 만든 예시 파일(서식 예시 확인)을 보관하는 폴더."""
    return 설정_폴더() / "format_examples"

# 서식 예시는 '한 번에 적용'(서식 + 자간 정리)으로 만든다(2026-10-04 사용자 요청: 예시 파일 자간 정리 미흡).
서식예시_작업모드 = "all"

def 서식예시_서명(profile):
    """보관한 서식 예시가 지금 서식 값·예시 글·앱 판으로 만든 것인지 가려내는 값(다르면 예시를 새로 만든다)."""
    재료 = json.dumps({"서식": profile or {}, "글": 서식예시_글, "앱판": APP_VERSION, "작업": 서식예시_작업모드},
                    ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(재료.encode("utf-8")).hexdigest()

def 설정_파일_경로():
    return 설정_폴더() / 설정_파일명

def 창_맨앞으로(window):
    """대화상자를 한글·웹 화면 창에 가려지지 않게 맨 앞으로 올린다.

    웹 화면 모드에서는 Tk 기본 창이 숨겨져 있어 그 창에 딸린(transient) 대화상자도 보이지 않으므로
    딸림을 풀고 올린다.
    """
    try:
        if window._root().state() == "withdrawn":
            window.wm_transient("")
        window.deiconify()
        window.lift()
        window.attributes("-topmost", True)
        window.after(300, lambda: window.attributes("-topmost", False))
        window.focus_force()
    except tk.TclError:
        pass


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
            if isinstance(저장된값.get("stage_choices"), dict):
                설정["stage_choices"] = 저장된값["stage_choices"]
            설정["abbreviations"] = 준말_등록표_정리(저장된값.get("abbreviations"))
            설정["abbreviation_defaults"] = bool(저장된값.get("abbreviation_defaults", True))
            # 예전 설정 파일은 별표(*, **) 문두 라벨 굵게가 켜진 채 저장돼 있다. 기본값을 끔으로 바꾼 뒤 한 번만
            # 끄고(판 2로 저장된 뒤에는 사용자가 다시 켠 값을 그대로 둔다).
            try:
                판 = int(저장된값.get("label_symbols_rev", 1) or 1)
            except (TypeError, ValueError):
                판 = 1
            if 판 < 2 and isinstance(설정.get("label_symbols"), dict):
                설정["label_symbols"] = {**설정["label_symbols"], "*": False, "**": False}
            설정["label_symbols_rev"] = 2
            # 예전 설정 파일은 기본값이던 '켜짐'이 그대로 저장돼 있다. 사용자가 켠 값과 구별할 수 없으므로 한 번만
            # 작업로그·무결성검사 JSON·최종검수 JSON을 끄고(판 2로 저장된 뒤에는 사용자가 다시 켠 값을 그대로 둔다).
            try:
                보고판 = int(저장된값.get("report_files_rev", 1) or 1)
            except (TypeError, ValueError):
                보고판 = 1
            if 보고판 < 2:
                설정["log_file"] = False
                설정["integrity_report_file"] = False
                설정["final_review_file"] = False
            설정["report_files_rev"] = 2
            # 문단 위 여백을 예전 기본값 그대로 쓰던(사용자가 바꾸지 않은) 설정은 새 계층별 기본값으로 바꾼다.
            try:
                간격판 = int(저장된값.get("std_parspace_rev", 1) or 1)
            except (TypeError, ValueError):
                간격판 = 1
            if 간격판 < 2:
                예전값 = {"std_parspace_chapter": "20", "std_parspace_midtitle": "15", "std_parspace_box": "15",
                        "std_parspace_circle": "10", "std_parspace_note": "3"}
                if all(str(설정.get(키, 값)).strip() == 값 for 키, 값 in 예전값.items()):
                    for 키 in (*예전값, "std_parspace_dash"):
                        설정[키] = 기본_설정[키]
            설정["std_parspace_rev"] = 2
            # 부연설명 앞 빈칸 규칙(Beta 8)은 '부연설명 들여쓰기' 단계로 적용된다. 예전 설정 파일에 꺼진 채
            # 저장된 값은 한 번만 켠다(판 2로 저장된 뒤에는 사용자가 끈 값을 그대로 둔다).
            try:
                부연판 = int(저장된값.get("std_supplement_rev", 1) or 1)
            except (TypeError, ValueError):
                부연판 = 1
            if 부연판 < 2:
                설정["std_supplement_indent"] = True
            설정["std_supplement_rev"] = 2
            # 예전 기본값의 글꼴 이름 오타('한컴돋음' → '한컴돋움', 항목기호 • 기본 글꼴)를 바로잡는다.
            for 항목 in (설정.get("symbol_fonts") or {}).values():
                if isinstance(항목, dict) and 항목.get("font") == "한컴돋음":
                    항목["font"] = "한컴돋움"
    except Exception as e:
        if _콘솔_출력_가능:
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
        if _콘솔_출력_가능:
            print(f"설정 저장 실패(무시): {e}")
        return False

# ============================================================
# GUI 메시지
# ============================================================

def 로그(message):
    global 로그_파일_경로
    기록 = str(message)
    if _콘솔_출력_가능:
        try:
            print(기록)
        except Exception:
            pass
    if 로그파일_사용 and 로그_파일_경로:
        try:
            with 로그_파일_잠금:
                with open(로그_파일_경로, "a", encoding="utf-8") as 로그파일:
                    로그파일.write(f"{_datetime.datetime.now():%Y-%m-%d %H:%M:%S.%f} {기록}\n")
        except Exception:
            pass
    gui_queue.put(("log", 기록))

def 진단로그(message):
    if 검수_사용:
        로그(message)

def 상태(message):
    gui_queue.put(("status", str(message)))

def 진행률(value):
    gui_queue.put(("progress", int(max(0, min(100, value)))))

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


def 단계시간_시작():
    global _단계시간표
    지금 = time.perf_counter()
    _단계시간표 = {'시작': 지금, '현재': '준비', '현재시작': 지금, '합': {}, '순서': []}


def _단계시간_닫기(표, 지금):
    이름 = 표.get('현재')
    if 이름 is None:
        return
    누적 = 표['합'].get(이름)
    if 누적 is None:
        누적 = 표['합'][이름] = [0.0, 0]
        표['순서'].append(이름)
    누적[0] += 지금 - 표['현재시작']
    누적[1] += 1
    표['현재'] = None


def 단계시간_구간(이름):
    """직전 구간을 닫고 이름 구간을 시작한다. 계측 중이 아니면 아무것도 하지 않는다."""
    표 = _단계시간표
    if 표 is None or not 이름:
        return
    지금 = time.perf_counter()
    _단계시간_닫기(표, 지금)
    표['현재'], 표['현재시작'] = 이름, 지금


def 단계시간_끝():
    global _단계시간표
    표, _단계시간표 = _단계시간표, None
    if 표 is None:
        return None
    지금 = time.perf_counter()
    _단계시간_닫기(표, 지금)
    표['전체'] = 지금 - 표['시작']
    return 표


def 단계시간_분류(이름):
    """단계 이름을 서식 / 내어쓰기 / 자간 / 쪽 맞춤 등 큰 분류로 묶는다(서식통일 안의 자간·쪽 맞춤은 서식통일에 포함)."""
    이름 = str(이름)
    if 이름 in ('준비', '열기', '변환') or '열기' in 이름 or '변환' in 이름:
        return '열기·변환'
    if '페이지' in 이름 or '쪽' in 이름:
        return '쪽 맞춤·배치'
    if '내어쓰기' in 이름 or '들여쓰기' in 이름 or '별표' in 이름:
        return '내어쓰기 계열'
    if '자간' in 이름 or '단어' in 이름 or '줄 병합' in 이름 or '마지막 줄' in 이름:
        return '자간·줄 끝'
    if '저장' in 이름 or '검수' in 이름 or '무결성' in 이름 or '규칙' in 이름:
        return '저장·검수'
    return '서식·기타'


def 단계시간_요약줄(표, 파일명, 상위=10):
    """계측 결과를 로그 줄 목록으로 만든다(순수 함수)."""
    전체 = max(표.get('전체', 0.0), 1e-9)
    분류합 = {}
    for 이름, (초, _건) in 표['합'].items():
        분류합[단계시간_분류(이름)] = 분류합.get(단계시간_분류(이름), 0.0) + 초
    줄 = [f"[처리 시간 계측] {파일명}: 전체 {전체:.1f}초 (단계 {len(표['합'])}종)"]
    줄.append("[처리 시간 계측] 분류별: " + " / ".join(
        f"{이름} {초:.1f}초({초 / 전체:.0%})" for 이름, 초 in sorted(분류합.items(), key=lambda x: -x[1])))
    오래 = sorted(표['합'].items(), key=lambda x: -x[1][0])[:상위]
    줄.append("[처리 시간 계측] 오래 걸린 단계(상위 %d): " % len(오래) + " / ".join(
        f"{이름} {초:.1f}초({초 / 전체:.0%}, {건}회)" for 이름, (초, 건) in 오래))
    return 줄


def 단계표시(단계명):
    """세부 단계명(또는 상위 절차명)을 받아 해당 상위 절차 칸을 켜도록 큐에 넣는다."""
    단계시간_구간(단계명)
    상위 = _세부단계_단계매핑.get(단계명, 단계명)
    if 상위 in 진행단계_순서:
        gui_queue.put(("step", 상위))
    # 진행 화면의 친절한 단계 안내 문장도 함께 바꾼다.
    gui_queue.put(("guide", 단계명))

def 단계초기화():
    gui_queue.put(("step_reset", None))

def 중단_요청됨():
    return 중단_event.is_set()


class 문두보호_조정불가(RuntimeError):
    """화면줄에 항목기호·라벨만 있어 자간·장평을 줄일 본문이 없다. 그 줄만 건너뛴다.

    예전에는 일반 RuntimeError라 줄 단위 자간 함수가 잡지 않아 문서 전체가 실패했다
    (2026-10-04 범정부오피스 인천 업무보고 서식에서 한 번에 적용이 10분 뒤 실패).
    """


# 문서 편집 세대: 글을 바꿀 수 있는 명령을 시도할 때마다(성공 여부와 관계없이) 올린다. 문단 글 캐시는 읽은 뒤
# 세대가 바뀌었으면 쓰지 않는다(Beta 12 리뷰 R2: 지운 뒤 넣기만 실패하면 글은 바뀌었는데 수정 건수가 0이라
# 캐시가 옛 글을 다음 규칙에 넘겼다).
_문서_편집_세대 = 0


def _문서_편집_시도():
    global _문서_편집_세대
    _문서_편집_세대 += 1


def hwp_run(command):
    if hwp is None:
        raise RuntimeError("HWP 객체가 없습니다.")
    if not (str(command).startswith("Move") or command in ("Cancel", "Select", "SelectAll")):
        _문서_편집_시도()
    try:
        if command in ('CharShapeSpacingDecrease', 'CharShapeSpacingIncrease',
                       'CharShapeRatioDecrease', 'CharShapeRatioIncrease'):
            # 이 명령들은 화면줄 선택을 사용하는 기존 자간/줄 병합 경로다.
            # 문두 라벨만 있는 줄에는 조정을 실행하지 않는다.
            if not 자간조정_현재줄_본문선택():
                raise 문두보호_조정불가('문두 보호: 이 화면줄에 조정 가능한 본문이 없습니다')
        return hwp.Run(command)
    except 문두보호_조정불가:
        raise
    except Exception as e:
        로그(f"HWP 명령 실패: {command} / {e}")
        raise


def _문두보호_줄건너뜀(함수, *args, **kwargs):
    """줄 단위 자간·줄 병합 함수를 부르고, 조정할 본문이 없는 줄이면 그 줄만 건너뛴다(True)."""
    try:
        return 함수(*args, **kwargs)
    except 문두보호_조정불가:
        try:
            hwp.Run("Cancel")
            줄 = 현재_화면줄_텍스트().strip()[:40]
        except Exception:
            줄 = ""
        진단로그(f"[문두 보호] 조정할 본문이 없는 줄 건너뜀: {줄}")
        return True

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
            f"\n\n{DLL_NAME}을 프로그램 폴더에서 찾을 수 없습니다.\n"
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
# 상용구 파일저장 (HWP.IDO)
# ============================================================

# 상용구(자주 쓰는 텍스트·서식)는 한/글이 기본 데이터 폴더의
# \User\Hwp\버전폴더 아래에 HWP.IDO 파일로 저장한다(예: 한/글 2020 = 60).
상용구_파일명 = "HWP.IDO"


def 번들_상용구_파일_찾기():
    """앱에 포함해 배포하는 상용구 파일(resources/HWP.IDO)의 실제 경로를 찾는다."""
    후보_목록 = [프로그램_폴더() / "resources" / 상용구_파일명]
    번들_폴더 = 번들_리소스_폴더()
    if 번들_폴더 is not None:
        후보_목록.append(번들_폴더 / "resources" / 상용구_파일명)
    for 경로 in 후보_목록:
        if 경로.is_file():
            return 경로
    return None


def 상용구_전용폴더_찾기():
    """HWP.IDO를 저장해야 할 한/글 버전별 전용 폴더를 찾는다.

    %AppData%\\HNC\\User\\Hwp\\ 아래에 한/글 버전마다 고유 숫자 폴더가
    있다(한/글 2020 = 60). 이미 HWP.IDO가 있는 폴더를 최우선으로 고르고,
    없으면 폴더 이름 숫자가 가장 큰(최신 버전으로 추정되는) 폴더를 고른다.
    AppData 폴더는 숨김 처리돼 있어 탐색기에서 '숨긴 항목'을 켜야 보인다.
    """
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    기준_폴더 = Path(appdata) / "HNC" / "User" / "Hwp"
    if not 기준_폴더.is_dir():
        return None
    후보_폴더들 = [경로 for 경로 in 기준_폴더.iterdir() if 경로.is_dir() and 경로.name.isdigit()]
    if not 후보_폴더들:
        return None
    기존_상용구_폴더들 = [경로 for 경로 in 후보_폴더들 if (경로 / 상용구_파일명).is_file()]
    if 기존_상용구_폴더들:
        return max(기존_상용구_폴더들, key=lambda p: int(p.name))
    return max(후보_폴더들, key=lambda p: int(p.name))


# ============================================================
# 한글 시작
# ============================================================

def 한글_시작():
    global hwp
    로그("한컴오피스 한글 자동화 시작 중... (NEO/2020 공통 COM)")
    pythoncom.CoInitialize()

    이전_창목록 = _표시중인_최상위창_목록() if 비교보기_사용 else None

    hwp = 한글_COM_인스턴스_생성(독립=True)
    hwp.XHwpWindows.Item(0).Visible = True
    로그("한글 창 표시 성공")

    result = hwp.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE)
    로그(f"RegisterModule 결과: {result}")
    if not result:
        raise RuntimeError(
            "한글 보안 모듈 RegisterModule 등록에 실패했습니다. "
            "한컴오피스 자동화 모듈 경로와 관리자/사용자 권한을 확인해 주세요."
        )

    if 비교보기_사용 and 이전_창목록 is not None:
        작업창_임베드(이전_창목록)

    로그("한컴오피스 한글 자동화 연결 완료")
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

# 자간을 줄이거나 넓힌 구간은 모두 색상_적용_현재선택으로 표시한다.
# 이 호출 횟수로 한 차례 자간 조정에서 실제 변경이 있었는지 판단해,
# 변경이 있으면 내어쓰기를 다시 적용하고 자간을 재검사한다.
자간_변경_횟수 = 0
# 자간을 바꾼 문단의 (리스트, 문단) 번호. 자간 조정 뒤에는 이 문단들만
# 내어쓰기를 다시 계산한다(내어쓰기 값은 그 문단 첫 줄에만 달려 있다).
자간_변경문단 = set()


def 색상_적용_현재선택():
    global 자간_변경_횟수
    자간_변경_횟수 += 1
    try:
        if hwp is not None:
            자간_변경문단.add(tuple(hwp.GetPos()[:2]))
    except Exception:
        pass
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
        한글_문서_열기(원본_hwp, 파일, 확장자명.upper(), "lock:true;forceopen:true")
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
    _문서_편집_시도()
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HInsertText
        act.GetDefault("InsertText", pset.HSet)
        pset.Text = text
        act.Execute("InsertText", pset.HSet)
    except Exception as e:
        로그(f"텍스트 삽입 실패(무시): {e}")

def 문자모양_적용_현재선택(폰트=None, 크기_pt=None, 굵게=None, 장평=None, 자간=None,
                        자간_유지=False):
    if hwp is None:
        return
    try:
        # 일부 한컴오피스 버전은 글꼴/크기만 지정한 CharShape 부분 적용에서도
        # 선택 영역의 자간을 기본값으로 돌린다. 서식통일처럼 기존 자간을 보존해야
        # 하는 작업은 선택 영역의 언어별 자간을 먼저 읽어 다시 명시적으로 넣는다.
        보존할_자간 = {}
        if 자간_유지 and 자간 is None and (폰트 or 크기_pt or 굵게 is not None):
            try:
                기존 = hwp.HParameterSet.HCharShape
                hwp.HAction.GetDefault("CharShape", 기존.HSet)
                for 필드 in ("SpacingHangul", "SpacingLatin", "SpacingHanja", "SpacingJapanese",
                             "SpacingOther", "SpacingSymbol", "SpacingUser"):
                    값 = getattr(기존, 필드, None)
                    if 값 is not None:
                        보존할_자간[필드] = int(값)
            except Exception as e:
                로그(f"자간 보존값 읽기 실패: {e}")
        # GetDefault로 HCharShape 전체를 채운 뒤 Execute하면 선택 영역에
        # 서로 다른 서식이 섞여 있을 때 지정하지 않은 속성(특히 Bold)이
        # 기본값으로 덮인다. 빈 파라미터셋에 변경할 항목만 넣어 실행한다.
        act = hwp.CreateAction("CharShape")
        pset = act.CreateSet()
        if 폰트:
            # v1.12 버그수정: FaceName* 만 SetItem하면 한글 오토메이션에서
            # 실제로는 글꼴이 반영되지 않는다(Height/Bold는 정상 반영되는데
            # 글꼴명만 조용히 무시됨 - 실제 출력 hwpx를 열어 charPr을 비교해
            # 확인한 사실). 언어별 FaceName은 반드시 같은 언어의 FontType과
            # 짝을 지어 지정해야 한글이 그 이름을 실제 폰트로 등록/적용한다.
            # (한컴디벨로퍼 포럼·pyhwpx 예제 등에서 공통적으로 FaceName*와
            # FontType*를 항상 함께 SetItem하는 이유와 동일)
            # 형식은 문서 헤더에 적힌 대로(HFT 글꼴을 TTF로 지정하면 조용히 무시됨).
            형식 = _글꼴형식.get(폰트, "TTF")
            try:
                ttf_타입 = hwp.FontType(형식)
            except Exception:
                ttf_타입 = {"TTF": 1, "HFT": 2}.get(형식, 1)  # FontType 호출 실패 시 관례값
            for 필드, 타입필드 in (
                ("FaceNameHangul", "FontTypeHangul"),
                ("FaceNameLatin", "FontTypeLatin"),
                ("FaceNameHanja", "FontTypeHanja"),
                ("FaceNameJapanese", "FontTypeJapanese"),
                ("FaceNameOther", "FontTypeOther"),
                ("FaceNameSymbol", "FontTypeSymbol"),
                ("FaceNameUser", "FontTypeUser"),
            ):
                try:
                    pset.SetItem(필드, 폰트)
                    pset.SetItem(타입필드, ttf_타입)
                except Exception:
                    pass
        if 크기_pt:
            try:
                pset.SetItem("Height", hwp.PointToHwpUnit(크기_pt))
            except Exception:
                pass
        if 굵게 is not None:
            try:
                pset.SetItem("Bold", 1 if 굵게 else 0)
            except Exception:
                pass
        # 분석한 서식 프로필은 장평·자간을 100.0처럼 실수로 담는다. COM에 실수를 넘기면
        # 정수 항목이 0으로 들어가 글자가 완전히 눌리므로 정수로 바꾸고 허용 범위로 제한한다.
        if 장평 is not None:
            장평 = max(50, min(200, int(round(float(장평)))))
        if 자간 is not None:
            자간 = max(-50, min(50, int(round(float(자간)))))
        if 장평 is not None:
            for 필드 in ("RatioHangul", "RatioLatin", "RatioHanja", "RatioJapanese",
                         "RatioOther", "RatioSymbol", "RatioUser"):
                try:
                    pset.SetItem(필드, 장평)
                except Exception:
                    pass
        if 자간 is not None:
            for 필드 in ("SpacingHangul", "SpacingLatin", "SpacingHanja", "SpacingJapanese",
                         "SpacingOther", "SpacingSymbol", "SpacingUser"):
                try:
                    pset.SetItem(필드, 자간)
                except Exception:
                    pass
        elif 보존할_자간:
            for 필드, 값 in 보존할_자간.items():
                try:
                    pset.SetItem(필드, 값)
                except Exception:
                    pass
        if act.Execute(pset) is False:
            # 글꼴 형식(TTF·HFT)이 이 PC의 글꼴과 맞지 않으면 실패한다(같은 이름이 두 형식으로 든 문서 등). 다른 형식으로
            # 한 번 더 해 보고, 되면 그 형식을 기억한다(2026-10-04 범정부오피스 서식: HCI Poppy가 TTF·HFT 둘 다 있음).
            if not (폰트 and _다른_글꼴형식으로_재실행(act, pset, 폰트, _언어별_글꼴형식)):
                raise RuntimeError("CharShape 부분 적용 결과가 False입니다.")
    except Exception as e:
        로그(f"문자모양 적용 실패(무시): {e}")


_언어별_글꼴형식 = ("FontTypeHangul", "FontTypeLatin", "FontTypeHanja", "FontTypeJapanese", "FontTypeOther",
                "FontTypeSymbol", "FontTypeUser")


def _다른_글꼴형식으로_재실행(action, params, 글꼴, 형식필드):
    """글꼴 형식만 반대(TTF↔HFT)로 바꿔 글자 모양을 다시 실행한다. 되면 그 형식을 기억하고 True."""
    다른 = "HFT" if _글꼴형식.get(글꼴, "TTF") == "TTF" else "TTF"
    try:
        코드 = hwp.FontType(다른)
    except Exception:
        코드 = {"TTF": 1, "HFT": 2}[다른]
    try:
        for 필드 in 형식필드:
            params.SetItem(필드, 코드)
        if action.Execute(params) is False:
            return False
    except Exception:
        return False
    _글꼴형식[글꼴] = 다른
    return True

def 문단_줄간격_적용_현재선택(퍼센트):
    if 현재_한칸표인가():
        return
    if hwp is None:
        return
    # 줄간격 조정은 160~200% 범위를 벗어날 수 없다.
    퍼센트 = max(세트문장_최소줄간격_퍼센트, min(세트문장_최대줄간격_퍼센트, 퍼센트))
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

def HwpUnit_pt(hwpunit):
    """HwpUnit(1/7200인치) 값을 포인트로 변환한다.

    hwp.PointToHwpUnit()은 실제 한/글 자동화 API에 있는 메서드지만,
    그 반대 방향인 HwpUnitToPoint()는 그렇지 않다 — pyhwpx가 자기
    래퍼 클래스에서 순수 파이썬 나눗셈(HwpUnit/100)으로 흉내만 낸
    편의 메서드였을 뿐, win32com으로 직접 붙는 이 코드베이스의 raw
    HwpFrame.HwpObject에는 없다. 실사용 로그에서
    "HwpFrame.HwpObject.HwpUnitToPoint" 오류로 확인됨. 같은 비율
    (100 HwpUnit = 1pt)로 직접 계산한다.
    """
    if not hwpunit:
        return 0.0
    return hwpunit / 100


def HwpUnit_mm(hwpunit):
    """HwpUnit(1/7200인치) 값을 밀리미터로 변환한다. HwpUnit_pt와 같은
    이유로 hwp.HwpUnitToMili()도 존재하지 않아 직접 계산한다.
    """
    if not hwpunit:
        return 0.0
    return hwpunit / 7200 * 25.4


def 문단_위간격_적용_현재선택(pt):
    if 현재_한칸표인가():
        return
    if hwp is None:
        return
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HParaShape
        act.GetDefault("ParagraphShape", pset.HSet)
        # COM ParaShape 문단 간격은 실제 HWPUNIT의 두 배다(_문단여백_COM항목 참고). 예전에는 그대로 넣어
        # 기본 문단 위 여백(□ 15pt 등)이 절반(7.5pt)으로 들어갔다(2026-10-04 실측).
        pset.PrevSpacing = hwp.PointToHwpUnit(pt) * 2
        act.Execute("ParagraphShape", pset.HSet)
    except Exception as e:
        로그(f"문단 위 간격 적용 실패(무시): {e}")

def 문단_아래간격_pt_현재문단():
    """현재 캐럿이 있는 문단의 '문단 아래 간격' 값을 pt로 읽는다."""
    if hwp is None:
        return None
    try:
        return HwpUnit_pt(hwp.ParaShape.Item("NextSpacing")) / 2      # COM은 실제 HWPUNIT의 두 배
    except Exception as e:
        로그(f"문단 아래 간격 읽기 실패(무시): {e}")
        return None

def 문단_아래간격_적용_현재선택(pt):
    if 현재_한칸표인가():
        return
    if hwp is None:
        return
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HParaShape
        act.GetDefault("ParagraphShape", pset.HSet)
        pset.NextSpacing = hwp.PointToHwpUnit(max(0.0, pt)) * 2      # COM은 실제 HWPUNIT의 두 배
        act.Execute("ParagraphShape", pset.HSet)
    except Exception as e:
        로그(f"문단 아래 간격 적용 실패(무시): {e}")

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


# 본문이 낫표(「」, 『』)로 시작하면 여는 낫표가 아니라 그 바로 다음
# 글자를 내어쓰기 기준으로 삼는다.
# 예: 'ㅇ (개요)「공유재산법 시행령」…' → 기준은 '「'이 아니라 '공'.
_내어쓰기_건너뛸_여는낫표 = "「『"


def 복사_내어쓰기_규칙(text):
    """서식 복사한 예시 보고서에서 이 문단 계층의 내어쓰기 기준. 서식 복사가 아니거나 규칙이 없으면 None.

    after_marker(기호 뒤 글 시작)·fixed(복사한 고정 값)·none(내어쓰기 없음). 예전 프로필의 after_label(라벨 규칙)은
    폐지돼(2026-10-10) 규칙 없음으로 읽는다: 기본 동작(콜론 라벨은 콜론 뒤 본문, 괄호 라벨은 기호 뒤)이 이전
    after_label과 같은 결과다.
    """
    rules = 표준서식_설정.get("내어쓰기_규칙") or {}
    if not rules:
        return None
    marker, _ = leading_marker(text)
    rule = rules.get(marker) or rules.get(서식요소.unify_marker(text)[0])
    if rule is None and marker == "**":
        # ** 전용 규칙이 없으면 대표 기호 *의 내어쓰기 규칙을 그대로 상속한다.
        rule = rules.get("*")
    return None if rule == "after_label" else rule


def 문단_내어쓰기_기준_오프셋(text):
    """문단 첫 화면줄에서 Shift+Tab을 실행할 본문 시작 문자 위치.

    서식 복사한 계층 규칙이 '기호 뒤'면 라벨을 글에 포함해 기호 뒤 글 시작으로, '고정 값'·'없음'이면 내어쓰기
    규칙이 손대지 않도록 None(복사한 첫 줄 값을 그대로 씀)이다. 규칙이 없을 때는 콜론 라벨이면 콜론 뒤 본문,
    괄호 라벨 '( )'이면 라벨 뒤가 아니라 기호 뒤 첫 글자(2026-10-10 개정)에 맞춘다.
    """
    규칙 = 복사_내어쓰기_규칙(text)
    if 규칙 in ("fixed", "none"):
        return None
    if 규칙 == "after_marker":
        return _여는낫표_건너뛰기(text, _문단_기호뒤_오프셋(text))
    return _여는낫표_건너뛰기(text, _문단_본문시작_오프셋(text))


def _여는낫표_건너뛰기(text, offset):
    """본문이 '「법령」'처럼 여는 낫표로 시작하면 낫표 다음 글자 위치로 옮긴다."""
    if offset is None:
        return None
    body = text.rstrip("\r\n")
    if (offset + 1 < len(body) and body[offset] in _내어쓰기_건너뛸_여는낫표
            and not body[offset + 1].isspace()):
        return offset + 1
    return offset


def _문단_기호뒤_오프셋(text):
    """항목기호(□·ㅇ·-·* 등)와 뒤 빈칸을 건너뛴 글 시작 문자 위치. 괄호·콜론 라벨은 글에 포함한다.

    기호로 시작하지 않는 문단이거나 기호 뒤에 글이 없으면 None.
    """
    if not text:
        return None
    text = text.rstrip("\r\n")
    start = _문단_공백_건너뛰기(text, 0)
    if start >= len(text):
        return None
    tail = text[start:]
    if not (tail[0] in 공문서_기호 or tail[0] in "*＊☞ㅁ" or any(p.match(tail) for p in 항목_패턴)):
        return None
    marker_end = 문장부호_마커_끝위치(text)
    if marker_end is None:
        marker_end = start + 1
    idx = _문단_공백_건너뛰기(text, marker_end)
    if idx >= len(text) or text[idx] in "\r\n":
        return None
    return idx


def _문단_본문시작_오프셋(text, 괄호라벨_뒤=False):
    """내어쓰기 기준이 되는 글 시작 문자 위치.

    - 콜론 라벨('일시:', '- 추진부서 :', '(방식) :')이 있으면 콜론 뒤 본문(현행 유지).
    - 괄호 라벨 '( )'만 있으면 라벨 뒤가 아니라 항목기호 뒤 첫 글자 — 라벨의 '('(2026-10-10 개정:
      괄호라벨 뒤 첫 글자 기준 폐지). 대괄호 '[ ]'는 원래부터 라벨로 보지 않아 같은 기준이다.
    - 괄호라벨_뒤=True는 옛 동작(괄호 라벨 뒤까지)이며 자간·장평 조정이 건드리지 않을 선행부의 끝을
      찾는 데만 쓴다(`문단_자간보호_선행부_오프셋`).
    """
    if not text:
        return None
    # 문단 끝 개행만 제외. 내부 강제 줄바꿈 뒤 문장은 라벨 탐색하지 않는다.
    text = text.rstrip("\r\n")
    start = _문단_공백_건너뛰기(text, 0)
    if start >= len(text):
        return None
    tail = text[start:]
    # 일반 문장의 구두점은 대상으로 삼지 않는다.
    구조마커 = (tail[0] in 공문서_기호 or tail[0] in "*＊☞ㅁ"
                or any(p.match(tail) for p in 항목_패턴))
    if not 구조마커:
        # 기존 세트 후속 라벨: '(6~16번) : 본문'
        m = re.match(r"[（(][^()（）\r\n]+[)）][ \t]*[:：][ \t]*(?=\S)", tail)
        return start + m.end() if m else None
    idx = _문단_기호뒤_오프셋(text)
    if idx is None:
        return None
    # 균형 괄호만 문두 라벨로 인정한다. 붙어 있는 '(연도)지명'은 제외.
    pairs = {"(": ")", "（": "）"}
    if text[idx] in pairs:
        stack = []
        close = None
        for j in range(idx, len(text)):
            ch = text[j]
            if ch in "\r\n":
                break
            if ch in pairs:
                stack.append(pairs[ch])
            elif ch in ")）":
                if not stack or stack.pop() != ch:
                    break
                if not stack:
                    close = j
                    break
        if close is not None:
            label = text[idx + 1:close].strip()
            after = _문단_공백_건너뛰기(text, close + 1)
            separated = after > close + 1
            if after < len(text) and text[after] in ":：":
                after = _문단_공백_건너뛰기(text, after + 1)
                separated = True
            year = re.fullmatch(r"['’‘]?[0-9]{2,4}(?:년|[./-][0-9]{1,2})*\.?", label)
            # '(개요)「법령명」…'처럼 문두 라벨 바로 뒤에 여는 인용부호가
            # 붙는 공문서 표기도 라벨과 본문의 경계다. 공백만 요구하면
            # 기준 오프셋이 괄호 앞에 머물러 둘째 줄이 '(개요)' 아래로 간다.
            quote_boundary = (after < len(text)
                              and text[after] in "「『‘“'\"")
            # 라벨 뒤에 콜론이 오면 콜론 라벨('(방식) :')이라 현행대로 콜론 뒤 본문이 기준이다.
            콜론라벨 = text[_문단_공백_건너뛰기(text, close + 1):][:1] in (":", "：")
            if (label and not year and (separated or quote_boundary)
                    and after < len(text) and text[after] not in "\r\n"
                    and (콜론라벨 or 괄호라벨_뒤)):
                return after
        return idx
    m = re.match(r"([^\n\r:：]{1,30}?)[ \t]*[:：][ \t]+(?=\S)", text[idx:])
    # 콜론 라벨은 '일    시', '교육내용'처럼 짧은 항목명이다. 공백을 뺀 12자를 넘으면
    # 문장 속 콜론('… 지원 규모 : (’25)…')이라 라벨로 보면 둘째 줄이 문장 중간까지 밀린다.
    if (m and len("".join(m.group(1).split())) <= 12
            and not re.search(r"[/\\]|https?$|^\d+$", m.group(1).strip(), re.I)):
        return idx + m.end()
    return idx


def 문단_자간보호_선행부_오프셋(text):
    """자간·장평 조정이 바꾸지 않는 선행부(항목기호·빈칸·괄호/콜론 라벨)가 끝나는 문자 위치.

    내어쓰기 기준에서 괄호 라벨 뒤 첫 글자 규칙을 폐지했지만(2026-10-10), 라벨 글자의 자간이 문단마다
    달라지지 않도록 괄호 라벨까지는 이전처럼 보호한다. 서식 복사 규칙이 '고정 값'·'없음'이면 None.
    """
    규칙 = 복사_내어쓰기_규칙(text)
    if 규칙 in ("fixed", "none"):
        return None
    if 규칙 == "after_marker":
        return _여는낫표_건너뛰기(text, _문단_기호뒤_오프셋(text))
    return _여는낫표_건너뛰기(text, _문단_본문시작_오프셋(text, 괄호라벨_뒤=True))


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


# ASCII 괄호·대괄호 등 '좁은 문장부호'는 함초롬/한컴 계열 글꼴에서 약 0.42em
# 폭으로 렌더된다(반각 0.5em보다 좁음). 선행부 폭 추정 오차의 주원인이므로
# 별도 보정한다. 필요 시 이 값만 미세조정하면 된다.
_좁은문장부호_폭배수 = 0.42
_좁은문장부호 = set("()[]{}<>")

# 폭 추정 도우미는 부연설명 배치 기능에서만 사용한다.
# 문단 내어쓰기는 정렬을 변경하지 않고 실제 Shift+Tab으로 처리한다.

def _반각전각_폭배수(ch):
    """글자 한 개의 가로 폭 배수를 반환한다(전각=1.0, 반각=0.5)."""
    w = unicodedata.east_asian_width(ch)
    if w in ("W", "F"):
        return 1.0
    if w == "A":
        # 가운데점(·) 등 폭이 모호한 문자는 공문서 문맥상 전각으로 본다.
        return 1.0
    if ch in _좁은문장부호:
        return _좁은문장부호_폭배수
    # Na/H(스페이스, 라틴 등)
    return 0.5

def 문단_선행부_폭_HWPUNIT(문단_시작위치, text, 오프셋):
    """문단 시작부터 본문 첫 글자(오프셋) 직전까지 '선행부'의 가로 폭을
    HWPUNIT으로 계산한다.

    선행부 각 글자의 실제 글자모양(크기·장평)을 한글에서 읽어 폭을 합산하므로
    실행 시점·정렬·재시도와 무관하게 항상 같은 값이 나온다(결정적). 이 값이
    둘째 줄 내어쓰기 위치가 된다.
    """
    if 오프셋 <= 0:
        return 0
    총 = 0.0
    for i in range(오프셋):
        ch = text[i]
        높이 = None
        장평 = 100.0
        try:
            문단_범위_선택(문단_시작위치, i, i + 1)
            act = hwp.HAction
            pset = hwp.HParameterSet.HCharShape
            act.GetDefault("CharShape", pset.HSet)
            hwp_run("Cancel")
            높이 = float(pset.Height)
            try:
                장평 = float(pset.RatioHangul)
            except Exception:
                장평 = 100.0
        except Exception:
            try:
                hwp_run("Cancel")
            except Exception:
                pass
        if not 높이 or 높이 <= 0:
            # 글자모양을 못 읽으면 기본 크기(가장 흔한 15pt)로 근사한다.
            높이 = 1500.0
            장평 = 100.0
        총 += 높이 * (장평 / 100.0) * _반각전각_폭배수(ch)
    return int(round(총))

def _내어쓰기_값_설정(value):
    """다른 문단 속성을 덮어쓰지 않고 첫 줄 값만 바꾼다."""
    action = hwp.CreateAction("ParagraphShape")
    params = action.CreateSet()
    params.SetItem("Indentation", value)
    if action.Execute(params) is False:
        raise RuntimeError("첫 줄 내어쓰기 값 설정 실패")



# 문서 처리 중 '최종 서식 기준 내어쓰기' 단계가 뒤에 예정돼 있으면
# 표준서식 단계에서는 내어쓰기를 계산하지 않는다(어차피 다시 계산된다).
최종_내어쓰기_예정 = False


def 내어쓰기_기호선택_허용(text):
    """서식 프로파일의 기호별 '내어쓰기' 선택이 꺼진 기호 문단이면 False."""
    매칭 = 표준서식_기호규칙_찾기(text) if text else None
    if not 매칭:
        return True
    return 표준서식_설정.get("스타일_속성선택", {}).get(매칭[0], {}).get("indent", True)


def 재검사_대상인가(pos):
    """2차 이후 재검사에서 이 위치의 문단을 검사해야 하는지."""
    return 재검사_대상문단 is None or tuple(pos[:2]) in 재검사_대상문단


def 재검사_영역인가(area):
    """2차 이후 재검사에서 이 컨트롤 영역(리스트)을 검사해야 하는지."""
    return 재검사_대상문단 is None or any(key[0] == area for key in 재검사_대상문단)


def 문단_내어쓰기_전체_갱신(대상문단=None):
    """최종 문자 서식/자간으로 본문 내어쓰기만 재계산한다.

    대상문단((리스트, 문단) 번호 집합)을 주면 그 문단만 계산한다.
    값이 실제로 바뀐 문단은 내어쓰기_변경문단에 모아 다음 재검사 범위로 쓴다.
    """
    내어쓰기_변경문단.clear()
    if 대상문단 is not None and not 대상문단:
        return True
    붙임번호_대상 = _붙임목록_내어쓰기_대상수집()
    붙임번호_기준점들 = {}
    순회_시작()
    while True:
        if 중단_요청됨():
            return False
        hwp_run("MoveParaBegin")
        if 대상문단 is not None and tuple(hwp.GetPos()[:2]) not in 대상문단:
            if not 범위_다음_문단으로_진행():
                break
            continue
        text = 현재문단_텍스트()
        if 현재_한칸표인가():
            if not 범위_다음_문단으로_진행():
                break
            continue
        _내어쓰기_한문단(text, 붙임번호_대상, 붙임번호_기준점들)
        if not 범위_다음_문단으로_진행():
            break
    return True


def _내어쓰기_한문단(text, 붙임번호_대상, 붙임번호_기준점들):
    """커서가 있는 문단(문단 시작)의 내어쓰기를 계산해 적용한다(문단_내어쓰기_전체_갱신·문단 세트 공용)."""
    현재키 = tuple(hwp.GetPos()[:2])
    if 현재키 in 붙임번호_대상:
        기준문단, _ = 붙임번호_대상[현재키]
        기준키 = 기준문단[0]
        if 기준키 not in 붙임번호_기준점들:
            붙임번호_기준점들[기준키] = _붙임번호_기준위치_실측(*기준문단)
            if 붙임번호_기준점들[기준키] is None:
                로그(f"[붙임 내어쓰기] 첫 번호 기준점 측정 실패: {기준문단[1].strip()[:60]}")
        기준값 = 붙임번호_기준점들[기준키]
        if 기준값 is None:
            로그(f"[붙임 내어쓰기] 번호 기준을 측정하지 못했습니다: {text.strip()[:60]}")
        # 숫자와 점으로 된 어절은 다음 줄의 번호와 세로로 같은 위치다(계단식으로 밀지 않는다).
        elif not _붙임목록_번호_내어쓰기_적용(hwp.GetPos(), text, 기준값[0]):
            로그(f"[붙임 내어쓰기] 번호 정렬을 건너뜀: {text.strip()[:60]}")
    elif (문단_내어쓰기_기준_오프셋(text) is not None
            and 내어쓰기_기호선택_허용(text)):
        문단_내어쓰기_적용(hwp.GetPos(), text)


def _붙임목록_내어쓰기_대상수집():
    """문서 맨 끝의 번호 붙임 묶음만 훑어 번호 세로 정렬 대상을 수집한다."""
    paragraphs = []
    original = hwp.GetPos()
    try:
        순회_시작()
        while True:
            paragraphs.append((tuple(hwp.GetPos()[:2]), 현재문단_텍스트()))
            if not 범위_다음_문단으로_진행():
                break
    finally:
        try:
            hwp.SetPos(*original)
        except Exception:
            pass
    blocks = 끝붙임번호묶음_찾기([text for _, text in paragraphs])
    targets = {}
    for start, end in blocks:
        anchor = paragraphs[start]
        for 단계, index in enumerate(range(start, end + 1)):
            key = paragraphs[index][0]
            targets[key] = (anchor, 단계)
    return targets


def _붙임번호_기준위치_실측(문단_시작위치, text):
    """첫 번호 위치(와 번호 앞 빈칸 폭)를 글꼴 기준으로 실측한다."""
    offset = 붙임번호_오프셋(text)
    if offset is None:
        return None
    # 수집 단계의 위치는 (리스트, 문단) 두 값뿐이다. SetPos는 (리스트, 문단, 위치) 세 값이 필요하다.
    문단_시작위치 = tuple(문단_시작위치)[:3]
    if len(문단_시작위치) == 2:
        문단_시작위치 += (0,)
    original_pos = hwp.GetPos()
    begin = None
    original_indent = None
    try:
        hwp_run("Cancel")
        hwp.SetPos(*문단_시작위치)
        hwp_run("MoveParaBegin")
        begin = hwp.GetPos()
        original_indent = hwp.ParaShape.Item("Indentation")
        left = int(hwp.ParaShape.Item("LeftMargin"))
        _내어쓰기_값_설정(0)
        hwp.SetPos(*begin)
        hwp_run("MoveLineEnd")
        end = hwp.GetPos()
        units = len(text[:offset].encode("utf-16-le")) // 2
        target = (begin[0], begin[1], begin[2] + units)
        if end[:2] != begin[:2] or target[2] >= end[2]:
            return None
        if hwp.SetPos(*target) is False or tuple(hwp.GetPos()) != target:
            return None
        if hwp_run("ParagraphShapeIndentAtCaret") is False:
            return None
        prefix_width = _캐럿위치_폭_실측(begin, offset)
        prefix_without_gap = len(text[:offset].rstrip(" \t\u00a0\u3000"))
        label_width = _캐럿위치_폭_실측(begin, prefix_without_gap)
        if prefix_width is None or label_width is None or prefix_width <= label_width:
            return None
        return left + prefix_width, prefix_width - label_width
    except Exception as e:
        로그(f"붙임 번호 기준점 실측 실패: {e}")
        return None
    finally:
        if original_indent is not None and begin is not None:
            try:
                hwp.SetPos(*begin)
                _내어쓰기_값_설정(original_indent)
            except Exception:
                pass
        try:
            hwp.SetPos(*original_pos)
        except Exception:
            pass


def _붙임목록_번호_내어쓰기_적용(문단_시작위치, text, 기준위치):
    """번호 위치를 기준 번호와 세로로 같게 맞추고 꺾인 줄은 내용에 맞춘다."""
    offset = 붙임번호_오프셋(text)
    if hwp is None or offset is None:
        return False
    original_pos = None
    original_indent = None
    original_left = None
    begin = None
    changed = False
    try:
        original_pos = hwp.GetPos()
        hwp_run("Cancel")
        if hwp.SetPos(*문단_시작위치) is False:
            raise RuntimeError("붙임 항목 문단 이동 실패")
        hwp_run("MoveParaBegin")
        begin = hwp.GetPos()
        original_indent = hwp.ParaShape.Item("Indentation")
        original_left = hwp.ParaShape.Item("LeftMargin")
        _내어쓰기_값_설정(0)
        changed = True
        prefix_width = _캐럿위치_폭_실측(begin, offset) if offset else 0
        marker_end = text.find(".", offset) + 1
        marker_width = _캐럿위치_폭_실측(begin, marker_end)
        if marker_width is None or marker_width <= 0 or prefix_width is None:
            raise RuntimeError("번호 마커 폭 실측 실패")
        # 한/글 내어쓰기는 첫 줄을 왼쪽여백에 그대로 두고 둘째 줄부터 |값|만큼 더 민다.
        # 첫 줄 번호가 기준 번호 위치에 오도록 왼쪽여백을 잡고, 꺾인 줄은 번호 뒤 내용에 맞춘다.
        target_left = 기준위치 - prefix_width
        target_indent = -marker_width
        action = hwp.CreateAction("ParagraphShape")
        params = action.CreateSet()
        params.SetItem("LeftMargin", target_left)
        params.SetItem("Indentation", target_indent)
        if action.Execute(params) is False:
            raise RuntimeError("붙임 번호 내어쓰기 설정 실패")
        if (int(hwp.ParaShape.Item("LeftMargin")) != target_left
                or int(hwp.ParaShape.Item("Indentation")) != target_indent):
            raise RuntimeError("붙임 번호 내어쓰기 값 검증 실패")
        if (int(original_left) != target_left or int(original_indent) != target_indent):
            내어쓰기_변경문단.add(tuple(begin[:2]))
        진단로그(f"[붙임 내어쓰기] 번호 오프셋 {offset}: {text.strip()[:60]}")
        return True
    except Exception as e:
        if changed and original_indent is not None and begin is not None:
            try:
                hwp.SetPos(*begin)
                action = hwp.CreateAction("ParagraphShape")
                params = action.CreateSet()
                params.SetItem("LeftMargin", original_left)
                params.SetItem("Indentation", original_indent)
                action.Execute(params)
            except Exception as restore_error:
                로그(f"붙임 내어쓰기 원래 값 복원 실패: {restore_error}")
        로그(f"붙임 번호 내어쓰기 실패(건너뜀): {e}")
        return False
    finally:
        if original_pos is not None:
            try:
                hwp.SetPos(*original_pos)
            except Exception:
                pass



def 문단_내어쓰기_적용(문단_시작위치, text, 폰트크기_pt=None, 폰트=None, 굵게=None):
    """실제 Shift+Tab 실행. 정렬/여백 보존, 반복 시 누적 방지, 실패 시 복원.

    글꼴·굵기·장평·자간·탭 폭은 한글이 계산한다. 긴 라벨로 기준점이
    첫 화면줄 밖에 있으면 잘못된 내어쓰기를 적용하지 않고 로그를 남긴다.
    선택된 텍스트나 탭을 삽입하지 않으며 COM 실패를 성공으로 처리하지 않는다.
    """
    if 현재_한칸표인가():
        return False
    offset = 문단_내어쓰기_기준_오프셋(text)
    if hwp is None or offset is None or offset <= 0:
        return False
    original_pos = None
    original_indent = None
    begin = None
    changed = False
    try:
        original_pos = hwp.GetPos()
        hwp_run("Cancel")
        if hwp.SetPos(*문단_시작위치) is False:
            raise RuntimeError("대상 문단 이동 실패")
        hwp_run("MoveParaBegin")
        begin = hwp.GetPos()
        original_indent = hwp.ParaShape.Item("Indentation")
        # 기존 내어쓰기를 지운 동일한 첫 줄 상태에서 매번 계산한다.
        _내어쓰기_값_설정(0)
        changed = True
        hwp.SetPos(*begin)
        hwp_run("MoveLineEnd")
        line_end = hwp.GetPos()
        # 한글 위치값은 UTF-16 코드 단위. 보조평면 문자도 올바르게 이동.
        units = len(text[:offset].encode("utf-16-le")) // 2
        target = (begin[0], begin[1], begin[2] + units)
        if line_end[:2] != begin[:2] or target[2] >= line_end[2]:
            raise RuntimeError("본문 시작점이 첫 화면줄 안에 없습니다")
        if hwp.SetPos(*target) is False or tuple(hwp.GetPos()) != target:
            raise RuntimeError("본문 시작점 이동 실패")
        if hwp_run("ParagraphShapeIndentAtCaret") is False:
            raise RuntimeError("Shift+Tab 명령 실패")
        value = hwp.ParaShape.Item("Indentation")
        if value >= 0:
            raise RuntimeError("Shift+Tab 실행 후 내어쓰기 값이 설정되지 않았습니다")
        if value != original_indent:
            내어쓰기_변경문단.add(tuple(begin[:2]))
        진단로그(f"[내어쓰기] Shift+Tab 오프셋 {offset}, 값 {value}: {text.strip()[:60]}")
        return True
    except Exception as e:
        if changed and original_indent is not None and begin is not None:
            try:
                hwp.SetPos(*begin)
                _내어쓰기_값_설정(original_indent)
            except Exception as restore_error:
                로그(f"내어쓰기 원래 값 복원 실패: {restore_error}")
        로그(f"내어쓰기 적용 실패(건너뜀): {e}")
        return False
    finally:
        if original_pos is not None:
            try:
                hwp.SetPos(*original_pos)
            except Exception:
                pass

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

def _부모문단_유형(text):
    """제목/본문/내용이면 그 유형 문자열, 아니면 None."""
    s = (text or "").lstrip()
    if not s:
        return None
    c = s[0]
    if c in _제목_기호:
        return "제목"
    if c in _본문_기호:
        return "본문"
    if c in _내용_기호:
        return "내용"
    return None

def _부연설명_문단인가(text):
    """*, **, ※ 로 시작하면 부연설명."""
    s = (text or "").lstrip()
    return bool(s) and (s[0] == "*" or s[0] == "※")

def _선행공백_길이(text):
    i = 0
    while i < len(text) and text[i] in (" ", "\t", "\u00a0", "\u3000"):
        i += 1
    return i


def _캐럿위치_폭_실측(문단_시작, 글자수):
    """문단 첫 줄에서 앞 글자수(문자열 길이)만큼의 가로 폭을 한/글에 실측시킨다.

    첫 줄 값을 0으로 두고 그 위치에서 실제 Shift+Tab을 실행해 생긴 내어쓰기
    값을 읽은 뒤, 문단의 원래 첫 줄 값으로 되돌린다. 문단 모양 단위(왼쪽여백과
    같은 단위)로 돌려주며, 위치가 첫 화면줄 밖이거나 실패하면 None.
    """
    original_pos = hwp.GetPos()
    begin = None
    original = None
    try:
        hwp_run("Cancel")
        hwp.SetPos(*문단_시작)
        hwp_run("MoveParaBegin")
        begin = hwp.GetPos()
        original = hwp.ParaShape.Item("Indentation")
        _내어쓰기_값_설정(0)
        hwp.SetPos(*begin)
        hwp_run("MoveLineEnd")
        line_end = hwp.GetPos()
        text = 현재문단_텍스트()
        units = len(text[:글자수].encode("utf-16-le")) // 2
        target = (begin[0], begin[1], begin[2] + units)
        if line_end[:2] != begin[:2] or target[2] >= line_end[2]:
            return None
        if hwp.SetPos(*target) is False or tuple(hwp.GetPos()) != target:
            return None
        if hwp_run("ParagraphShapeIndentAtCaret") is False:
            return None
        value = hwp.ParaShape.Item("Indentation")
        return -int(value) if value < 0 else None
    except Exception as e:
        진단로그(f"[부연설명 들여쓰기] 폭 실측 실패: {e}")
        return None
    finally:
        if begin is not None and original is not None:
            try:
                hwp.SetPos(*begin)
                _내어쓰기_값_설정(original)
            except Exception:
                pass
        try:
            hwp.SetPos(*original_pos)
        except Exception:
            pass


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


def 부연설명_앞빈칸_수(부모_유형, marker):
    """위 문단 유형(제목/본문/내용/None)과 부연설명 기호로 앞 빈칸 수를 정한다. 규칙 밖이면 None."""
    return 부연설명_앞빈칸.get(부모_유형, {}).get(marker)


def _부연설명_앞빈칸_적용(문단_시작, text, 칸수, 왼쪽여백=None):
    """부연설명 문단 앞 빈칸을 칸수만큼으로 바꾸고 왼쪽여백을 맞춘다.

    바뀌었으면 True, 이미 같으면 False, 실패하면 None.
    """
    if 현재_한칸표인가():
        return False
    lead = _선행공백_길이(text)
    try:
        hwp.SetPos(*문단_시작)
        hwp_run("MoveParaBegin")
        기존_여백 = int(hwp.ParaShape.Item("LeftMargin"))
        빈칸_같음 = text[:lead] == " " * 칸수
        여백_같음 = 왼쪽여백 is None or 기존_여백 == int(왼쪽여백)
        if 빈칸_같음 and 여백_같음:
            return False
        if not 빈칸_같음:
            if lead > 0:
                if 문단_범위_선택(문단_시작, 0, lead) is False or hwp_run("Delete") is False:
                    raise RuntimeError("앞 빈칸 삭제 실패")
            hwp.SetPos(*문단_시작)
            텍스트_삽입(" " * 칸수)
        if not 여백_같음:
            hwp.SetPos(*문단_시작)
            act = hwp.CreateAction("ParagraphShape")
            pset = act.CreateSet()
            pset.SetItem("LeftMargin", int(왼쪽여백))
            if act.Execute(pset) is False:
                raise RuntimeError("왼쪽여백 설정 실패")
        hwp.SetPos(*문단_시작)
        cur_text = 현재문단_텍스트()
        진단로그(f"[부연설명 들여쓰기] 앞 빈칸 {lead} → {칸수}칸: {cur_text.strip()[:50]}")
        # 앞 빈칸이 바뀌면 글 시작 위치도 바뀌므로 내어쓰기(Shift+Tab)를 다시 맞춘다.
        if 표준서식_내어쓰기_사용 and stage_enabled(선택_세부작업, 'hanging_indent'):
            hwp.SetPos(*문단_시작)
            문단_내어쓰기_적용(문단_시작, cur_text)
        return True
    except Exception as e:
        로그(f"부연설명 들여쓰기 적용 실패(무시): {e}")
        return None


def _부연설명_한문단(문단_시작, text, 상태, 부모대상=None):
    """부연설명 들여쓰기의 문단 하나 처리(상태['부모']에 위 제목/본문 문단을 이어 받는다). 적용했으면 True."""
    결과 = False
    if text and text.strip():
        유형 = _부모문단_유형(text)
        부모 = 상태.get('부모')
        if 유형 is not None:
            상태['부모'] = (문단_시작, 유형)
        elif _부연설명_문단인가(text):
            marker, _ = leading_marker(text)
            들여쓰기_선택 = 표준서식_설정.get("스타일_속성선택", {}).get(marker, {}).get("indent", True)
            대상 = 부모대상 is None or (부모 is not None and tuple(부모[0][:2]) in 부모대상)
            칸수 = 부연설명_앞빈칸_수(부모[1] if 부모 else None, marker)
            if 대상 and 들여쓰기_선택 and 칸수 is not None:
                왼쪽여백 = None
                if 부모 is not None:
                    hwp.SetPos(*부모[0])
                    왼쪽여백 = int(hwp.ParaShape.Item("LeftMargin"))
                if _부연설명_앞빈칸_적용(문단_시작, text, 칸수, 왼쪽여백):
                    결과 = True
                    내어쓰기_변경문단.add(tuple(문단_시작[:2]))
            hwp.SetPos(*문단_시작)
        else:
            # 제목/본문/내용도 부연설명도 아닌 일반 문단(번호 항목 등)이 끼면 연결이 끊긴다.
            상태['부모'] = None
    return 결과


def 부연설명_들여쓰기_전체_적용(부모대상=None):
    """각 부연설명(*, **, ※)의 앞 빈칸을 위 문단 유형별 칸 수로 맞춘다(부연설명_앞빈칸).

    왼쪽여백은 위 제목/본문/내용 문단과 같게 둔다. 부모대상((리스트, 문단) 집합)을 주면
    그 부모에 딸린 부연설명만 다시 맞춘다. 옮긴 부연설명은 내어쓰기_변경문단에 더한다.
    """
    if not 부연설명_들여쓰기_사용:
        return True
    if 중단_요청됨():
        return False
    if 부모대상 is not None and not 부모대상:
        return True
    if 부모대상 is None:
        로그("부연설명(*, **, ※) 들여쓰기 적용 시작")
    순회_시작()
    부모 = None        # (부모 문단 시작 위치, 유형)
    적용수 = 0
    while True:
        if 중단_요청됨():
            return False
        hwp_run("MoveParaBegin")
        문단_시작 = hwp.GetPos()
        text = 현재문단_텍스트()

        상태 = {'부모': 부모}
        if _부연설명_한문단(문단_시작, text, 상태, 부모대상):
            적용수 += 1
        부모 = 상태['부모']

        if not 범위_다음_문단으로_진행():
            break
    if 부모대상 is None or 적용수:
        로그(f"부연설명 들여쓰기 적용 완료 (적용 {적용수}건)")
    return True


def _별표_위치_실측(문단_시작, text):
    """* 문단에서 별표(*) 기호의 실제 가로 위치를 측정한다(왼쪽여백 + 선행 공백 폭)."""
    if hwp is None or not text:
        return None
    try:
        hwp.SetPos(*문단_시작)
        hwp_run("MoveParaBegin")
        left_margin = int(hwp.ParaShape.Item("LeftMargin"))
        lead = _선행공백_길이(text)
        w_lead = 0
        if lead > 0:
            w_lead = _캐럿위치_폭_실측(문단_시작, lead)
            if w_lead is None:
                return None
        return left_margin + w_lead
    except Exception as e:
        진단로그(f"[별표 위치 실측 실패]: {e}")
        return None


def _별표_정렬_적용(문단_시작, text, 목표_별표_위치):
    """** 문단의 둘째 별표 위치를 바로 앞줄 *의 목표_별표_위치에 맞춘다.

    필요시 앞 빈칸을 삭제하고, 남은 차이는 왼쪽여백으로 보정한다.
    바뀌었으면 True, 이미 같으면 False, 실패하면 None.
    """
    if hwp is None or 현재_한칸표인가():
        return False
    try:
        hwp.SetPos(*문단_시작)
        hwp_run("MoveParaBegin")
        cur_text = 현재문단_텍스트() or text
        lead = _선행공백_길이(cur_text)
        w_lead = _캐럿위치_폭_실측(문단_시작, lead + 1)
        if w_lead is None:
            return None

        필요_여백 = int(목표_별표_위치) - int(w_lead)
        공백_삭제됨 = False

        # 선행 공백이 있고, 필요 여백이 음수이면(두 번째 별표가 오른쪽에 치우침) 앞 빈칸 삭제.
        # 단, 글꼴의 미세 폭 오차(예: 공백 693 vs 별표 774의 수십 HWPUNIT 차이)로
        # 정상 공백이 과도하게 삭제되지 않도록, 공백 1칸의 절반(약 300 HWPUNIT) 이상 음수일 때만 삭제한다.
        while 필요_여백 <= -300 and _선행공백_길이(cur_text) > 0:
            if cur_text and cur_text[0] in (" ", "\u00a0"):
                if 문단_범위_선택(문단_시작, 0, 1) is False:
                    break
                if hwp_run("Delete") is False:
                    break
                공백_삭제됨 = True
                hwp.SetPos(*문단_시작)
                cur_text = 현재문단_텍스트()
                lead = _선행공백_길이(cur_text)
                w_lead = _캐럿위치_폭_실측(문단_시작, lead + 1)
                if w_lead is None:
                    break
                필요_여백 = int(목표_별표_위치) - int(w_lead)
            else:
                break

        margin = max(0, 필요_여백)
        hwp.SetPos(*문단_시작)
        hwp_run("MoveParaBegin")
        기존_여백 = int(hwp.ParaShape.Item("LeftMargin"))
        여백_변경됨 = False
        if 기존_여백 != margin:
            act = hwp.CreateAction("ParagraphShape")
            pset = act.CreateSet()
            pset.SetItem("LeftMargin", margin)
            if act.Execute(pset) is False:
                raise RuntimeError("왼쪽여백 설정 실패")
            여백_변경됨 = True

        if 공백_삭제됨 or 여백_변경됨:
            진단로그(f"[별표(**) 정렬] 목표 {목표_별표_위치}, 폭 {w_lead} → 여백 {margin}"
                     f"{'(앞 공백 삭제)' if 공백_삭제됨 else ''}: {cur_text.strip()[:40]}")
            # 공백이나 여백이 바뀌었으면 내어쓰기(Shift+Tab)도 새 본문 시작점에 맞게 갱신
            if 표준서식_내어쓰기_사용 and stage_enabled(선택_세부작업, 'hanging_indent'):
                hwp.SetPos(*문단_시작)
                문단_내어쓰기_적용(문단_시작, cur_text)
            return True
        return False
    except Exception as e:
        로그(f"별표(**) 정렬 적용 실패(무시): {e}")
        return None


def _별표_한문단(문단_시작, text, 상태):
    """별표(**) 정렬의 문단 하나 처리(상태['별표']에 바로 앞 * 문단의 별표 위치를 이어 받는다). 적용했으면 True."""
    결과 = False
    if text and text.strip():
        marker, _ = leading_marker(text)
        if marker == "*":
            상태['별표'] = _별표_위치_실측(문단_시작, text)
        elif marker == "**":
            if 상태.get('별표') is not None and _별표_정렬_적용(문단_시작, text, 상태['별표']):
                결과 = True
                내어쓰기_변경문단.add(tuple(문단_시작[:2]))
            상태['별표'] = None
        else:
            # 일반 본문이나 다른 구조 기호(※, -, □ 등)가 끼면 별표 연쇄를 끊는다
            상태['별표'] = None
    # 빈 문단(공백 줄)은 줄바꿈 여백이므로 상태['별표']를 유지한다.
    return 결과


def 별표_정렬_전체_적용():
    """문서 내 *(주석1) 바로 뒤에 오는 **(주석2)의 둘째 별표 위치를 *에 맞춘다.

    '부연설명 들여쓰기' 설정(기본 꺼짐)과 분리하여 항상 실행하며,
    필요시 ** 앞의 선행 공백을 지워 정확히 정렬한다.
    문단 사이의 빈 문단(줄바꿈 공백줄)은 단락 간 여백이므로 별표 연쇄를 끊지 않는다.
    """
    if hwp is None:
        return True
    if 중단_요청됨():
        return False
    순회_시작()
    직전_별표_위치 = None
    적용수 = 0

    while True:
        if 중단_요청됨():
            return False
        hwp_run("MoveParaBegin")
        문단_시작 = hwp.GetPos()
        text = 현재문단_텍스트()

        상태 = {'별표': 직전_별표_위치}
        if _별표_한문단(문단_시작, text, 상태):
            적용수 += 1
        직전_별표_위치 = 상태['별표']

        if not 범위_다음_문단으로_진행():
            break

    if 적용수:
        로그(f"별표(**) 정렬 완료 (적용 {적용수}건)")
    return True

def _mm_hwpunit(mm):
    """mm → HWPUNIT(반올림). 한/글 MiliToHwpUnit은 소수를 버려 예시 여백 4252가 4251로 들어갔다(2026-10-04)."""
    return int(round(float(mm) * 7200 / 25.4))


def _현재_쪽여백():
    """지금 문서 첫 구역의 쪽 여백 {항목: HWPUNIT}. 모르면 None."""
    if hwp is None:
        return None
    try:
        pset = hwp.HParameterSet.HSecDef
        hwp.HAction.GetDefault("PageSetup", pset.HSet)
        return {k: int(getattr(pset.PageDef, k)) for k in
                ("LeftMargin", "RightMargin", "TopMargin", "BottomMargin", "HeaderLen", "FooterLen")}
    except Exception:
        return None


def _표준_또는_원본여백(항목, 표준값, 원본=None):
    """표준 여백과 원본 여백 중 좁은 값. 원본 여백이 더 좁으면 원본을 둔다(사용자 결정, 2026-10-09:
    여백을 넓히면 본문 폭이 줄어 원본 쪽 구성이 깨짐. 실측: 좌우 18mm → 20mm로 14쪽 문서가 17쪽)."""
    if 작업_모드 != 'unify':
        return 표준값      # 원본 여백 유지는 쪽 구성 동일 원칙(서식 통일 전용)의 일부다
    원본 = _현재_쪽여백() if 원본 is None else 원본
    if not 원본 or 항목 not in 원본 or 원본[항목] <= 0:
        return 표준값
    return min(표준값, 원본[항목])


def 페이지_여백_설정(여백_mm):
    if hwp is None:
        return
    try:
        원본 = _현재_쪽여백()
        act = hwp.HAction
        pset = hwp.HParameterSet.HSecDef
        act.GetDefault("PageSetup", pset.HSet)
        for 항목, 키 in (("LeftMargin", "left"), ("RightMargin", "right"), ("TopMargin", "top"),
                       ("BottomMargin", "bottom"), ("HeaderLen", "header"), ("FooterLen", "footer")):
            setattr(pset.PageDef, 항목, _표준_또는_원본여백(항목, _mm_hwpunit(여백_mm[키]), 원본))
        if "gutter" in 여백_mm:
            pset.PageDef.GutterLen = _mm_hwpunit(여백_mm["gutter"])
        act.Execute("PageSetup", pset.HSet)
    except Exception as e:
        로그(f"표준서식 여백 설정 실패(무시): {e}")

def 용지_다르면_알림():
    """서식 복사한 예시 보고서와 정리할 문서의 용지 크기·방향이 다르면 작업 로그에 알린다(용지는 바꾸지 않음)."""
    용지 = 표준서식_설정.get("용지_mm")
    if not 용지 or hwp is None:
        return None
    try:
        pset = hwp.HParameterSet.HSecDef
        hwp.HAction.GetDefault("PageSetup", pset.HSet)
        너비 = float(pset.PageDef.PaperWidth) * 25.4 / 7200
        높이 = float(pset.PageDef.PaperHeight) * 25.4 / 7200
        가로 = bool(pset.PageDef.Landscape)
    except Exception:
        return None
    if abs(너비 - 용지["width"]) <= 1 and abs(높이 - 용지["height"]) <= 1 and 가로 == bool(용지.get("landscape")):
        return False

    def 글(w, h, l):
        return f"{w:g}×{h:g}mm{' 가로' if l else ''}"
    로그(f"[서식 복사] 예시 보고서 용지({글(용지['width'], 용지['height'], 용지.get('landscape'))})와 이 문서 용지"
         f"({글(round(너비, 1), round(높이, 1), 가로)})가 다릅니다. 용지 크기·방향은 바꾸지 않았습니다.")
    return True


def 들여쓰기_공백_맞추기(목표_공백수):
    try:
        hwp_run("MoveParaBegin")
        문단_시작위치 = hwp.GetPos()
        text = 현재문단_텍스트()
        # 표준서식_기호규칙_찾기와 동일하게 스페이스뿐 아니라 탭 등
        # 모든 선행 공백류 길이를 기준으로 삼아야 탭 들여쓰기 문단에서도
        # 목표 공백수로 정확히 교체된다.
        벗긴텍스트 = text.lstrip()
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

def 표준서식_기호규칙_찾기(text):
    if not text:
        return None
    # v1.11 버그수정: 기존에는 lstrip(" ")로 '일반 공백'만 제거했다.
    # 그러나 공문서 문단은 탭(Tab)으로 들여쓰기된 뒤 □/ㅇ/-/※ 기호가
    # 오는 경우가 매우 흔한데, 그 경우 벗긴텍스트가 여전히 탭으로
    # 시작해 아래 startswith() 비교가 모든 규칙에서 실패했다. 즉
    # □/ㅇ/-/※ 4종 폰트 규칙이 "전혀 작동하지 않는" 현상의 근본 원인이다.
    # 문장부호_마커_끝위치 등 다른 판정 함수들과 동일하게 모든 공백류
    # (스페이스/탭 등)를 제거하도록 통일한다.
    벗긴텍스트 = text.lstrip()
    if not 벗긴텍스트:
        return None
    detected_marker, detected_role = leading_marker(벗긴텍스트)
    if detected_role == "장":
        return ((표준서식_설정.get("논리역할_규칙") or {}).get("장")
                or 표준서식_설정.get("장_규칙") or _표준서식_설정_기본값.get("장_규칙"))
    if 표준서식_설정.get("논리역할_규칙"):
        for 규칙 in 표준서식_설정["기호_규칙"]:
            if 규칙[0] == detected_marker:
                return 규칙
        if detected_role in 표준서식_설정["논리역할_규칙"]:
            return 표준서식_설정["논리역할_규칙"][detected_role]
    if 벗긴텍스트[0] in DOT_MARKERS:
        return next((규칙 for 규칙 in 표준서식_설정["기호_규칙"] if 규칙[0] == "•"), None)
    for 규칙 in 표준서식_설정["기호_규칙"]:
        if 벗긴텍스트.startswith(규칙[0]):
            return 규칙
    for 별칭_기호, 원본_기호 in 표준서식_기호_별칭.items():
        if 벗긴텍스트.startswith(별칭_기호):
            for 규칙 in 표준서식_설정["기호_규칙"]:
                if 규칙[0] == 원본_기호:
                    return 규칙
    return None


_정렬_이름 = {값: 이름 for 이름, 값 in _정렬_COM.items()}


def 본문형_일반문장인가(text):
    """지금 문단(항목기호 없음)이 본문 문장인가. 서식 요소 분석의 '일반 문장'과 같은 기준(15자 이상, 18pt 미만,
    가운데·오른쪽 정렬 아님)으로, 제목·날짜·서명 줄에는 예시의 본문 서식을 입히지 않는다."""
    try:
        hwp_run("MoveParaBegin")
        정렬 = _정렬_이름.get(int(hwp.ParaShape.Item("AlignType")))
        크기 = int(hwp.CharShape.Item("Height"))
    except Exception:
        return False
    return 서식요소.is_body_sentence(text, 크기, 정렬)


# 알파는 기본 보고서 서식을 XML에서 먼저 입힌다. 내어쓰기·쪽 배치는 실측한다.
# 사용자 서식의 복사 속성은 아직 기존 경로로 처리해 미지원 속성을 잃지 않는다.
알파_HWPX_일괄서식_사용 = True
_표준서식_XML텍스트 = set()
_표준서식_XML간격 = {}
_알파_일괄서식_문서 = False


def 알파_일괄서식_가능():
    return bool(알파_HWPX_일괄서식_사용 and 작업_모드 in ('format', 'all')
                and 표준서식_선행_사용 and 쪽범위_요청 is None
                and stage_enabled(선택_세부작업, 'standard_format', 작업_모드)
                and not any(표준서식_설정.get(key) for key in (
                    '복사_문단모양', '계층_추가서식', '복제_본문서식',
                    '복제_들여쓰기_유지', '복귀_간격', '제목뒤_간격')))


_GDI_글꼴 = None


def _GDI_글꼴인가(글꼴):
    """Windows 글꼴(GDI) 목록에 있는지. 처음 한 번만 읽는다(한글 이름으로 비교된다)."""
    global _GDI_글꼴
    if _GDI_글꼴 is None:
        이름들 = set()
        hdc = win32gui.GetDC(0)
        try:
            win32gui.EnumFontFamilies(hdc, None, lambda lf, tm, ft, data: 이름들.add(lf.lfFaceName) or 1, None)
        finally:
            win32gui.ReleaseDC(0, hdc)
        _GDI_글꼴 = 이름들
    return 글꼴 in _GDI_글꼴


def _알파_글꼴형식(글꼴):
    """XML 일괄 서식에 쓸 글꼴 형식(TTF/HFT). 알 수 없으면 None(그 문단은 기존 COM 경로가 형식을 확인해 처리).

    COM 경로는 TTF로 해 보고 실패하면 HFT로 다시 하지만 XML은 다시 해 볼 수 없다. 예전에는 늘 TTF로 넣어
    한/글 전용 글꼴(휴먼명조·한양신명조 등 HFT, Windows 글꼴 목록에 없음)을 잘못된 형식으로 등록했다(2026-10-09 검토).
    Windows 글꼴 목록에 있으면 TTF, 없으면 HFT로 본다(COM 경로가 다시 시도해 얻는 결과와 같다).
    """
    if not 글꼴:
        return None
    if _글꼴형식.get(글꼴):
        return _글꼴형식[글꼴]
    try:
        return "TTF" if _GDI_글꼴인가(글꼴) else "HFT"
    except Exception:
        return None


def _알파_라벨_굵게범위(text):
    if not 괄호_라벨_볼드_사용 or 문두_라벨_굵게_제외_문단인가(text):
        return ()
    end = 문장부호_마커_끝위치(text)
    if end is None:
        return ()
    while end < len(text) and text[end] in (' ', '\t'):
        end += 1
    rest = text[end:]
    match = re.match(r'^([^\n\r:：]{1,25}?)[ \t]*([:：])[ \t]+(\S.*)$', rest)
    if match and match.group(1).strip():
        label = match.group(1).strip()
        start = end + rest.find(label)
        return ((start, start + len(label)),)
    if '(' in text:
        for match in 괄호_정규식.finditer(text):
            if 괄호_문두_라벨인가(text, match):
                return (match.span(),)
    return ()


def 표준서식_hwpx_처리(source, target=None, selections=None):
    """기본 본문 서식을 XML에서 일괄 적용하고 COM 중복 적용을 막는다."""
    global _알파_일괄서식_문서, _표준서식_XML텍스트, _표준서식_XML간격
    if not 알파_일괄서식_가능():
        return {} if target is None else 0
    tracker = ParagraphSpacingTracker()

    def plan(text, paragraph):
        # 컨트롤 문단도 위계 상태에는 포함한다. 그 문단의 실제 서식은 COM에 맡긴다.
        readable = _문단_본문글(paragraph) if text is None else text
        readable = normalize_leading_dot(readable)
        prev = None
        if 표준서식_문단위간격_사용:
            prev = tracker.spacing_for(readable, _표준서식_문단위간격_표(), 표준서식_문단위간격_복귀배율)
            if not readable.strip():
                tables = [x for x in paragraph.iter() if 제목_xml이름(x) == 'tbl']
                if any(중제목_유형판별(x) for x in tables):
                    tracker.spacing_for_level('midtitle', _표준서식_문단위간격_표(), 표준서식_문단위간격_복귀배율)
        if text is None or not text.strip():
            return None
        rule = 표준서식_기호규칙_찾기(readable) if 표준서식_기호_사용 else None
        if rule is None:
            # 일반 본문·제목은 원래의 글자 모양을 보존한다.
            return ParagraphStyle(text=readable, prev_pt=prev) if prev is not None else None
        symbol, lead, font, size, paragraph_bold, marker_bold = rule
        if readable.lstrip().startswith('**'):
            lead = max(0, lead - 1)
        formatted = ' ' * lead + readable.lstrip()
        selected = 표준서식_설정.get('스타일_속성선택', {}).get(symbol, {})
        글꼴형식 = _알파_글꼴형식(font) if selected.get('font', True) else None
        if selected.get('font', True) and font and 글꼴형식 is None:
            return None      # 글꼴 형식을 모르면 기존 COM 경로(TTF↔HFT 확인)로 처리한다
        enabled = 표준서식_기호_굵게.get(symbol, True)
        bold = bool(paragraph_bold and enabled)
        spans = list(_알파_라벨_굵게범위(formatted))
        if marker_bold and enabled and not bold:
            spans.append((lead, lead + 1))
        return ParagraphStyle(
            text=formatted, font=font if selected.get('font', True) else None,
            font_type=글꼴형식,
            size_pt=size if selected.get('size', True) else None,
            bold=bold if '복사_문단모양' in 표준서식_설정 else (True if bold else None),
            ratio=표준서식_설정['기본_장평'] if 표준서식_장평_사용 else None,
            line_percent=표준서식_설정['기본_줄간격_퍼센트'] if 표준서식_줄간격_사용 else None,
            prev_pt=prev, bold_spans=tuple(spans))

    try:
        result = apply_batch(source, target, plan)
    except Exception as error:
        # 미지원 구조(BatchUnsupported·UnsupportedPackage)뿐 아니라 예상 밖 오류(_rewrite_runs의 글자 보존 검사 등)도
        # 기존 COM 경로로 돌린다. 알파 새 기능의 오류로 베타에서 되던 문서 처리가 실패하면 안 된다(2026-10-09 검토).
        if not isinstance(error, (BatchUnsupported, UnsupportedPackage)):
            로그(f'[알파 일괄 서식] 예상 밖 오류({type(error).__name__}) — 기존 COM 경로로 처리')
        로그(f'[알파 일괄 서식] 기존 COM 경로 사용: {error}')
        if target is not None:
            shutil.copyfile(source, target)
            _표준서식_XML텍스트 = set()
            _표준서식_XML간격 = {}
            _알파_일괄서식_문서 = False
        return {} if target is None else 0
    if target is None:
        return {'본문': list(range(result.applied))}
    _표준서식_XML텍스트 = set(result.formatted_texts)
    _표준서식_XML간격 = dict(result.paragraph_spacing)
    _알파_일괄서식_문서 = bool(result.applied)
    로그(f'[알파 일괄 서식] XML 적용 {result.applied}문단 / 기존 경로 {result.fallback}문단 / '
         f'새 글자 모양 {result.char_styles}개·문단 모양 {result.paragraph_styles}개')
    return result.applied


def _알파_한줄문단인가(pos):
    """현재 실제 조판이 한 줄이면 자간·짧은 마지막 줄 보정이 필요 없다.

    오래된 XML lineseg나 글자 폭 추정값으로 문단을 제외하지 않는다.
    컨트롤, 측정 실패는 기존 전수 검사로 돌린다.
    """
    if not _알파_일괄서식_문서 or pos[0] != 0:
        return False
    try:
        hwp_run('MoveParaBegin')
        begin = hwp.GetPos()
        hwp_run('MoveParaEnd')
        end = hwp.GetPos()
        hwp_run('MoveLineBegin')
        last_line = hwp.GetPos()
        return (tuple(begin) == tuple(last_line) and tuple(begin[:2]) == tuple(pos[:2])
                and tuple(end[:2]) == tuple(pos[:2]) and begin[2] == 0)
    except Exception:
        return False
    finally:
        hwp.SetPos(*pos)


def 표준서식_문단_처리(문단_순번, 헤더_역할=None, 상속_기호_매칭=None):
    """현재 문단에 보고서 표준서식을 적용한다.

    v1.5:
    - □/ㅇ/-/※ 구조 기호가 제목/일자 판정보다 우선한다.
    - 세트 후속문단은 상위 문장부호의 폰트/크기 규칙을 상속한다.
      예: '※ (1~5번)...' 다음 '(6~16번)...'도 ※ 규칙(한컴돋움 13pt)을 적용한다.
    - 상속 문단은 원래의 더 깊은 들여쓰기를 유지한다.
    """
    if 현재_한칸표인가():
        return
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

    통일텍스트 = normalize_leading_dot(text)
    if 통일텍스트 != text:
        시작 = hwp.GetPos()
        hwp_run("MoveParaBegin")
        문단시작 = hwp.GetPos()
        기호위치 = len(text) - len(text.lstrip())
        문단_범위_선택(문단시작, 기호위치, 기호위치 + 1)
        텍스트_삽입("•")
        hwp.SetPos(*시작)
        text = 통일텍스트

    자체_기호_매칭 = 표준서식_기호규칙_찾기(text) if 표준서식_기호_사용 else None
    # 기호 서식 규칙이 없는 *·- 문단도 위계 추적에 포함해야 복귀를 판정할 수 있다.
    if 표준서식_문단위간격_사용 and not 표준서식_설정.get("복제_들여쓰기_유지"):
        간격_pt = 표준서식_문단위간격_찾기(text)
        if 간격_pt is not None and not (
                text.rstrip('\r\n') in _표준서식_XML텍스트
                and _표준서식_XML간격.get(text.rstrip('\r\n')) == 간격_pt and hwp.GetPos()[0] == 0):
            hwp_run("MoveParaBegin")
            hwp_run("MoveSelParaEnd")
            문단_위간격_적용_현재선택(간격_pt)
            hwp_run("Cancel")
    if (text.rstrip('\r\n') in _표준서식_XML텍스트 and hwp.GetPos()[0] == 0):
        # 한/글 실측이 필요한 내어쓰기만 수행한다. 글자/문단 서식은 이미 확정했다.
        if (표준서식_내어쓰기_사용 and not 최종_내어쓰기_예정
                and 내어쓰기_기호선택_허용(text)
                and 문단_내어쓰기_기준_오프셋(text) is not None):
            hwp_run('MoveParaBegin')
            문단_내어쓰기_적용(hwp.GetPos(), text)
        return
    # 보고서 표준서식은 문장부호(□/ㅇ/-/※ 등)로 시작하는 문단만 대상으로
    # 한다. 제목·일자·일반 본문에는 장평/줄간격/폰트/내어쓰기를 적용하지
    # 않아 원문 서식을 보존한다.
    if 자체_기호_매칭 is None:
        본문규칙 = 표준서식_설정.get("본문_문단") if 표준서식_설정.get("복제_본문서식") else None
        # 서식 예시의 본문 서식은 본문 문장에만 입힌다. 예전에는 제목·날짜 줄까지 본문 글꼴·크기로 바꿨다(2026-10-04).
        if 본문규칙 and 본문형_일반문장인가(text):
            hwp_run("MoveParaBegin")
            hwp_run("MoveSelParaEnd")
            문자모양_적용_현재선택(
                폰트=본문규칙.get("font"),
                크기_pt=본문규칙.get("size_pt"),
                굵게=True if 본문규칙.get("bold") else None,
                장평=표준서식_설정["기본_장평"] if 표준서식_장평_사용 else None,
                자간=표준서식_설정.get("기본_자간") if 표준서식_장평_사용 else None,
            )
            hwp_run("Cancel")
            hwp_run("MoveParaBegin")
            if 서식요소.PLAIN_KEY in 표준서식_설정.get("복사_문단모양", {}):
                # 예시 '일반 문장'의 여백·문단 간격·줄 간격과 영문 글꼴·장평·자간·정렬 등을 그대로 입힌다.
                복사_문단모양_적용(서식요소.PLAIN_KEY)
                계층_추가서식_적용(서식요소.PLAIN_KEY)
            elif 표준서식_줄간격_사용:
                hwp_run("MoveSelParaEnd")
                문단_줄간격_적용_현재선택(표준서식_설정["기본_줄간격_퍼센트"])
                hwp_run("Cancel")
        if (표준서식_내어쓰기_사용 and not 최종_내어쓰기_예정
                and 문단_내어쓰기_기준_오프셋(text) is not None):
            hwp_run("MoveParaBegin")
            문단_내어쓰기_적용(hwp.GetPos(), text)
        진단로그(f"[표준서식 제외] 문장부호로 시작하지 않음: {text.strip()[:80]}")
        return
    기호_매칭 = 자체_기호_매칭 or 상속_기호_매칭

    제목_문단인가 = bool(
        not 기호_매칭 and 표준서식_제목_사용 and 헤더_역할 == "title"
    )
    일자담당자_문단인가 = bool(
        not 기호_매칭 and 표준서식_일자담당자_사용 and 헤더_역할 == "dateinfo"
    )

    # 자체 문장부호가 있는 경우에만 표준 선행공백으로 보정한다.
    # **(주석2)는 둘째 별표가 *(주석1)의 별표와 같은 가로 위치에 오도록 선행 공백을 1칸 적게(공백수 - 1) 둔다.
    if 자체_기호_매칭 and not 표준서식_설정.get("복제_들여쓰기_유지"):
        목표_공백수 = 자체_기호_매칭[1]
        if text.lstrip().startswith("**"):
            목표_공백수 = max(0, 목표_공백수 - 1)
        들여쓰기_공백_맞추기(목표_공백수)

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

    if 제목_문단인가:
        규칙 = 표준서식_설정["제목_문단"]
        선택 = 표준서식_설정.get("스타일_속성선택", {}).get("(제목)", {})
        hwp_run("MoveParaBegin")
        hwp_run("MoveSelParaEnd")
        문자모양_적용_현재선택(
            폰트=규칙["font"] if 선택.get("font", True) else None,
            크기_pt=규칙["size_pt"] if 선택.get("size", True) else None,
            굵게=표준서식_제목_굵게
        )
        hwp_run("Cancel")
        복사_문단모양_적용("(제목)")
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
        선택 = 표준서식_설정.get("스타일_속성선택", {}).get(기호, {})
        굵게_허용 = 표준서식_기호_굵게.get(기호, True)
        문단굵게 = 문단굵게_기본값 and 굵게_허용
        기호만굵게 = 기호만굵게_기본값 and 굵게_허용

        hwp_run("MoveParaBegin")
        hwp_run("MoveSelParaEnd")
        # 규칙이 굵게인 경우만 굵게를 추가한다. False를 문단 전체에 강제로
        # 적용하면 원문에서 강조된 일부 텍스트까지 일반체로 풀리므로,
        # 굵게 해제는 하지 않고 기존 강조를 보존한다.
        문자모양_적용_현재선택(
            폰트=폰트 if 선택.get("font", True) else None,
            크기_pt=크기 if 선택.get("size", True) else None,
            굵게=문단굵게 if "복사_문단모양" in 표준서식_설정 else (True if 문단굵게 else None),
        )
        hwp_run("Cancel")

        # 내어쓰기(실제 Shift+Tab) 방식을 적용하기 전에 커서를
        # 반드시 문단 시작으로 옮겨 정확한 문단 기준 위치를 잡는다. 이 위치를
        # 기준으로 오프셋을 더해 선택하므로, 앞 단계(굵게 처리 등)가 커서를
        # 어디에 두었든 영향을 받지 않는다.
        hwp_run("MoveParaBegin")
        문단_기준위치 = hwp.GetPos()
        현재_text = 현재문단_텍스트()

        # 문두 라벨을 미리 굵게 해 첫 줄 폭을 확정한다.
        문두_라벨_굵게_선반영(문단_기준위치, 현재_text)

        # 라벨/본문을 정확히 정렬하는 내어쓰기. on/off 가능(표준서식_내어쓰기_사용).
        # 오프셋을 찾을 수 없는 단순 연속 설명문은 건드리지 않는다.
        if 표준서식_내어쓰기_사용 and 선택.get("indent", True) and not 최종_내어쓰기_예정:
            hwp.SetPos(문단_기준위치[0], 문단_기준위치[1], 문단_기준위치[2])
            if 문단_내어쓰기_기준_오프셋(현재_text) is not None:
                문단_내어쓰기_적용(문단_기준위치, 현재_text, 폰트크기_pt=크기, 폰트=폰트, 굵게=문단굵게)

        실제기호, _ = leading_marker(현재_text)
        복사_문단모양_적용(실제기호 if 실제기호 in 표준서식_설정.get("복사_문단모양", {}) else 기호)
        계층_추가서식_적용(실제기호 if 실제기호 in (표준서식_설정.get("계층_추가서식") or {}) else 기호)
        복사_간격_규칙_적용(실제기호 if 실제기호 in (표준서식_설정.get("복귀_간격") or {}) else 기호, 현재_text)

        # 기호 자체 bold는 실제 기호가 존재하는 문단에만 적용한다.
        if 자체_기호_매칭 and 기호만굵게 and not 문단굵게:
            hwp_run("MoveParaBegin")
            문단_시작 = hwp.GetPos()
            문단_범위_선택(문단_시작, 공백수, 공백수 + 1)
            문자모양_적용_현재선택(굵게=True)
            hwp_run("Cancel")

# 문서 작성자가 문단 위 여백 대신 빈 줄로 띄운 간격은 표준서식의 문단 위
# 여백과 겹치므로 지운다. 앞뒤가 모두 항목기호 문장인 빈 문단만 대상이다.
# 설정 > 서식 정리 > 보고서 표준서식에서 켜고 끈다.
항목기호문장_빈줄_삭제_사용 = True


def 빈문단_분류(text, begin, end):
    """'blank'(공백만 있는 빈 문단), 'marker'(항목기호 문장), 'other'.

    표·그림 같은 컨트롤은 글자 없이 위치만 차지하므로, 위치 길이가 공백
    글자 수와 같을 때만 빈 문단으로 본다. 표 하나만 있는 문단은
    MoveParaBegin이 표 뒤(pos 8)에 멈춰 시작·끝이 같아 보이므로, 시작
    위치가 0이 아니면 빈 문단이 아니다(실측: 공고문 표 5개가 지워짐).
    """
    body = (text or '').rstrip('\r\n')
    if not body.strip():
        if begin[2] != 0:
            return 'other'
        units = len(body.encode('utf-16-le')) // 2
        return 'blank' if end[2] - begin[2] == units else 'other'
    # 날짜 줄('2026. 9. 24.')처럼 번호로 보이는 머리 문단은 항목기호 문장이 아니다.
    if not 보고서_문단역할(body):
        return 'other'
    # 'ㅇ'·'*'처럼 기호만 있고 내용이 빈 문단은 제출서식의 작성란이다. 그
    # 앞뒤 빈 줄은 작성 여백이므로 지우지 않는다(실측: 공고문 '□ (자유작성)'
    # 아래 작성란 여백이 모두 지워짐).
    marker_end = 문장부호_마커_끝위치(body)
    if marker_end is not None and not body[marker_end:].strip():
        return 'template'
    return 'marker'


def 항목기호문장_사이_빈문단_찾기(kinds):
    """분류 목록에서 지울 빈 문단의 인덱스.

    - 앞뒤 가장 가까운 비어 있지 않은 문단이 모두 항목기호 문장인 빈 문단
    - 문서 끝의 빈 문단(뒤에 아무 내용도 없음). 문서 끝 빈 문단 하나가 다음
      쪽으로 넘어가면 내용 없는 빈 쪽이 인쇄된다(실측: 4쪽이 빈 문단 하나).
    """
    result = []
    for index, kind in enumerate(kinds):
        if kind != 'blank':
            continue
        before = next((k for k in reversed(kinds[:index]) if k != 'blank'), None)
        after = next((k for k in kinds[index + 1:] if k != 'blank'), None)
        if before == 'marker' and after == 'marker':
            result.append(index)
        elif before is not None and after is None:
            result.append(index)
    return result


def 본문_컨트롤_문단번호():
    """본문(리스트 0)에서 표·그림·글상자 등 컨트롤이 놓인 문단 번호.

    빈 줄 삭제가 컨트롤 문단을 빈 문단으로 오인해 표를 통째로 지우지
    않도록 막는 이중 안전장치다. 읽지 못하면 빈 집합을 돌려준다.
    """
    result = set()
    try:
        ctrl = hwp.HeadCtrl
        while ctrl:
            try:
                anchor = ctrl.GetAnchorPos(0)
                if anchor.Item("List") == 0:
                    result.add(anchor.Item("Para"))
            except Exception:
                pass
            ctrl = ctrl.Next
    except Exception as e:
        진단로그(f'본문 컨트롤 위치 확인 실패(무시): {e}')
    return result


def 항목기호문장_사이_빈줄_삭제(붙임_빈줄_넣기=False):
    """항목기호 문장 사이·문서 끝 빈 줄과 붙임 앞 여분 빈 줄을 지운다.

    붙임_빈줄_넣기=True이면 지우지 않고, 위에 글이 있는데 빈 줄이 없는 붙임 앞에 빈 줄 1줄만 넣는다.
    문단을 늘리는 작업이라 항목기호 서식(앞 빈칸 맞춤)이 끝난 뒤에 따로 부른다(실측 2026-10-08:
    앞에서 넣으면 뒤따르는 앞 빈칸 맞춤의 삭제가 일부 문단에서 실패해 빈칸이 늘었다).
    """
    global 쪽범위_본문_문단
    if hwp is None:
        return True
    original = hwp.GetPos()
    paragraphs = []
    texts = []
    컨트롤문단 = 본문_컨트롤_문단번호()
    try:
        hwp_run('MoveDocBegin')
        while True:
            if 중단_요청됨():
                return False
            hwp_run('MoveParaBegin')
            begin = hwp.GetPos()
            text = 현재문단_텍스트()
            hwp.SetPos(*begin)
            hwp_run('MoveParaEnd')
            end = hwp.GetPos()
            kind = 'other' if begin[1] in 컨트롤문단 else 빈문단_분류(text, begin, end)
            paragraphs.append((begin, end, kind))
            texts.append(None if begin[1] in 컨트롤문단 else text)
            hwp.SetPos(*begin)
            hwp_run('MoveNextParaBegin')
            after = hwp.GetPos()
            if after == begin or after[0] != 0 or after[1] <= begin[1]:
                break

        kinds = [p[2] for p in paragraphs]
        targets = set()
        붙임_삭제, 붙임_삽입 = 붙임_앞빈줄_계획(texts, kinds)
        if 붙임_빈줄_넣기:
            붙임_삭제 = []
        else:
            붙임_삽입 = []
            if 항목기호문장_빈줄_삭제_사용:
                targets.update(항목기호문장_사이_빈문단_찾기(kinds))
        targets.update(붙임_삭제)
        targets = {index for index in targets if index > 0 and 쪽범위_안인가(paragraphs[index][0])}
        붙임_삽입 = [index for index in 붙임_삽입 if 쪽범위_안인가(paragraphs[index][0])]
        삭제수 = 0
        삽입수 = 0
        # 뒤에서부터 고쳐야 앞 문단의 위치가 바뀌지 않는다. 빈 문단은 바로 앞
        # 문단 끝에 합쳐 지운다 — 뒤 문단에 합치면 항목기호 문장의 문단 모양이
        # 빈 문단의 모양으로 바뀐다. 붙임 앞 빈 줄은 바로 앞 문단 끝에서 문단을 나눠 넣는다.
        for index in sorted(targets | set(붙임_삽입), reverse=True):
            if 중단_요청됨():
                return False
            prev_end = paragraphs[index - 1][1]
            if index not in targets:
                try:
                    hwp.SetPos(*prev_end)
                    if hwp_run('BreakPara') is False:
                        raise RuntimeError('문단 나누기 실패')
                    삽입수 += 1
                except Exception as e:
                    로그(f'붙임 앞 빈 줄 넣기 중 오류(건너뜀): {e}')
                continue
            blank_end = paragraphs[index][1]
            try:
                hwp.SetPos(*prev_end)
                if hwp.SelectText(prev_end[1], prev_end[2], blank_end[1], blank_end[2]) is False:
                    raise RuntimeError('빈 줄 범위 선택 실패')
                hwp_run('Delete')
                삭제수 += 1
            except Exception as e:
                로그(f'항목기호 문장 사이 빈 줄 삭제 중 오류(건너뜀): {e}')
            finally:
                hwp_run('Cancel')
        if (삭제수 or 삽입수) and 쪽범위_본문_문단 is not None:
            # 지우거나 넣은 빈 문단은 모두 범위 안이라 그만큼 뒤 문단 번호가 바뀐다. 고정한 범위 끝을 같이
            # 옮기지 않으면 뒤 단계가 다음 쪽(범위 밖) 문단까지 고친다.
            시작, 끝 = 쪽범위_본문_문단
            쪽범위_본문_문단 = (시작, max(시작, 끝 - 삭제수 + 삽입수))
        if 붙임_빈줄_넣기:
            if 삽입수:
                로그(f'붙임 앞 빈 줄 넣기: {삽입수}개')
        else:
            로그(f'항목기호 문장 사이·문서 끝 빈 줄 삭제: {삭제수}개')
        return True
    finally:
        try:
            hwp_run('MoveDocBegin')
        except Exception:
            try:
                hwp.SetPos(*original)
            except Exception:
                pass


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
# 문서 헤더에서 읽은 글꼴 이름별 형식(TTF/HFT). 한/글 내장 HFT 글꼴(한양중고딕 등)을
# TTF로 지정하면 한/글이 오류 없이 무시한다(실측: 정책회의 ※ 문장 8개 글꼴 미반영).
_글꼴형식 = {}


def 글꼴형식_모으기(header):
    """HWPX 헤더 글꼴 목록의 {글꼴 이름: 형식(TTF·HFT)}. 같은 이름이 두 형식으로 있으면 설치된 TTF를 쓴다."""
    형식들 = {}
    for item in header.iter():
        if item.tag.rsplit("}", 1)[-1] != "font":
            continue
        이름, 형식 = item.get("face"), (item.get("type") or "").upper()
        if 이름 and 형식 and 형식들.get(이름) != "TTF":
            형식들[이름] = 형식
    return 형식들


def 글꼴형식_등록(형식들):
    """서식 프로필(예시 보고서)·문서에서 읽은 글꼴 형식을 글꼴 지정에 쓰는 표에 더한다(TTF가 우선)."""
    for 이름, 형식 in (형식들 or {}).items():
        if 이름 and 형식 and _글꼴형식.get(이름) != "TTF":
            _글꼴형식[이름] = str(형식).upper()


def _서식통일_문두요소_범위(text):
    """항목기호와 바로 뒤 괄호라벨의 (시작, 끝) 문자 오프셋을 돌려준다."""
    if not text:
        return None, None
    시작 = len(text) - len(text.lstrip(" \t\u00a0\u3000"))
    marker_end = 문장부호_마커_끝위치(text)
    if marker_end is None or marker_end <= 시작:
        return None, None
    marker_range = (시작, marker_end)
    label_start = _문단_공백_건너뛰기(text, marker_end)
    if label_start >= len(text) or text[label_start] not in "(（":
        return marker_range, None
    pairs = {"(": ")", "（": "）"}
    stack = []
    for index in range(label_start, len(text)):
        char = text[index]
        if char in "\r\n":
            break
        if char in pairs:
            stack.append(pairs[char])
        elif char in ")）":
            if not stack or stack.pop() != char:
                return marker_range, None
            if not stack:
                return marker_range, (label_start, index + 1)
    return marker_range, None


def _서식통일_글자모양(pos):
    """pos 글자 하나의 (글꼴, 크기 HWPUNIT). 실패 시 None."""
    try:
        nxt = _단어모드_다음위치(pos)
        if not nxt:
            return None
        단어모드_범위선택(pos, nxt)
        pset = hwp.HParameterSet.HCharShape
        hwp.HAction.GetDefault("CharShape", pset.HSet)
        return (str(pset.FaceNameHangul), int(pset.Height))
    except Exception:
        return None
    finally:
        try:
            hwp_run("Cancel")
        except Exception:
            pass


def _서식통일_공백제거(text):
    return "".join(str(text or "").split())


def _서식통일_HWPX_분석(문서경로):
    """HWPX의 글자·문단 모양과 본문 직속 문단 목록을 한 번만 읽어 재사용한다.

    서식통일은 문단마다 원본 HWPX를 참조한다. 문단마다 ZIP을 다시 풀면 큰 문서에서
    조사만 수 분이 걸리므로, 경로·수정 시각·크기가 같으면 분석 결과를 재사용한다.
    """
    from zipfile import ZipFile
    from defusedxml import ElementTree as ET
    from docfit_core.style_inventory import _sections, _parse_fonts, _parse_char, _parse_para, _tag
    path = Path(문서경로)
    stat = path.stat()
    key = (str(path), stat.st_mtime_ns, stat.st_size)
    if _서식통일_HWPX_캐시.get("key") == key:
        return _서식통일_HWPX_캐시["value"]
    with ZipFile(path) as archive:
        header = ET.fromstring(archive.read("Contents/header.xml"))
        fonts = _parse_fonts(header)
        글꼴형식_등록(글꼴형식_모으기(header))
        chars = {item.get("id"): _parse_char(item, fonts)
                 for item in header.iter() if _tag(item) == "charPr"}
        paras = {item.get("id"): _parse_para(item)
                 for item in header.iter() if _tag(item) == "paraPr"}
        문단들 = []
        for name in _sections(archive):
            section = ET.fromstring(archive.read(name))
            # GetPos()[1]는 본문 리스트의 문단 번호다. section.iter()를 쓰면
            # 표 셀·글상자 안의 하위 문단까지 끼어들어 뒤쪽 문단 인덱스가 밀리고,
            # 다른 쪽 문장의 서식을 읽거나 수정하게 된다. 본문 직속 문단만 센다.
            문단들.extend(item for item in section if _tag(item) == "p")
    value = {"chars": chars, "paras": paras, "paragraphs": 문단들}
    _서식통일_HWPX_캐시.clear()
    _서식통일_HWPX_캐시.update(key=key, value=value)
    return value


# 한/글 글자 위치에서 한 칸을 차지하는 문장 안 요소. 강제 줄바꿈도 한 칸이다
# (실측: 줄바꿈 뒤 괄호 구간이 한 글자씩 밀려 적용됨). 줄바꿈은 공백으로 취급되는
# U+2028로 두어 문장 끝 개행 제거·공백 비교에 영향을 주지 않는다.
_서식통일_글자요소 = {"fwSpace": " ", "nbSpace": " ", "tab": " ", "lineBreak": " "}


def _서식통일_run_text(run):
    """(글자, 위치 확실 여부). 표·그림·필드처럼 글자 사이 개체가 있으면 위치를 확신할 수 없다."""
    from docfit_core.style_inventory import _tag
    parts, 확실 = [], True
    for child in run:
        if _tag(child) != "t":
            확실 = False
            continue
        parts.append(child.text or "")
        for sub in child:
            기호 = _서식통일_글자요소.get(_tag(sub))
            if 기호 is None:
                확실 = False
            else:
                parts.append(기호)
            parts.append(sub.tail or "")
    return "".join(parts), 확실


def _서식통일_XML문단(pos):
    """본문 문단 위치의 (HWPX 분석, 문단 요소, HWPX 원문 텍스트, 위치 확실 여부). 없으면 None."""
    문서경로 = _서식통일_현재_HWPX()
    if 문서경로 is None or pos[0] != 0:
        return None
    try:
        from docfit_core.style_inventory import _tag
        분석 = _서식통일_HWPX_분석(문서경로)
        para = 분석["paragraphs"][pos[1]]
        조각 = [_서식통일_run_text(run) for run in para if _tag(run) == "run"]
        return 분석, para, "".join(text for text, _ in 조각), all(확실 for _, 확실 in 조각)
    except Exception:
        return None


def _서식통일_위치텍스트(pos, text):
    """글자 위치와 맞는 문단 텍스트.

    한/글 GetText는 고정폭·묶음 빈칸을 빼고 돌려준다(' ㅇ  본문' → ' ㅇ본문'). 그러면
    항목기호를 찾지 못해 문단이 조사에서 빠지고, 글자 위치도 어긋난다. 공백을 뺀 글자가
    같을 때만 HWPX 원문을 쓰고, 다르면(다른 문단을 읽은 경우) 한/글 텍스트를 쓴다.
    """
    found = _서식통일_XML문단(pos)
    if found and _서식통일_공백제거(found[2]) == _서식통일_공백제거(text):
        return found[2]
    return text


def _서식통일_음영값(value):
    value = str(value or "").strip().upper()
    return "없음" if value in ("", "NONE", "#FFFFFF") else value


def 서식통일_표본(시작, text):
    """항목기호·라벨·본문의 기준 서식과 보호할 괄호 구간을 분리해 표본을 만든다."""
    body = (text or "").rstrip("\r\n")
    found = _서식통일_XML문단(시작)
    if found is None or not body.strip():
        return None
    분석, para, 원문, 위치확실 = found
    # 같은 번호의 HWPX 문단이 이 문단이 아니면(앞 단계에서 문단이 지워지는 등) 다른 문장의
    # 서식을 읽게 되므로 건너뛴다. 글자 위치는 HWPX 원문 기준이다(한/글 텍스트는 고정폭
    # 빈칸이 빠져 위치가 밀린다).
    if _서식통일_공백제거(원문) != _서식통일_공백제거(body):
        진단로그(f"[서식통일] HWPX 원문과 문단 글자가 달라 건너뜀: {body.strip()[:40]}")
        return None
    if not 위치확실:
        진단로그(f"[서식통일] 문장 안에 표·그림 등 개체가 있어 글자 위치를 확신할 수 없어 건너뜀: "
                 f"{body.strip()[:40]}")
        return None
    body = 원문.rstrip("\r\n")

    def utf16길이(value):
        return len(value.encode("utf-16-le")) // 2

    # 항목기호와 바로 뒤 라벨은 문장 표준 크기에 포함한다. 문장 중간의
    # 부연괄호는 본문과 별도 규칙(본문보다 2pt 작게)으로 조사·적용한다.
    본문끝 = utf16길이(body)
    marker_span, label_span = _서식통일_문두요소_범위(body)
    marker_span16 = tuple(utf16길이(body[:i]) for i in marker_span) if marker_span else None
    label_span16 = tuple(utf16길이(body[:i]) for i in label_span) if label_span else None
    보호괄호 = tuple(span for span in (marker_span, label_span) if span)
    부연괄호 = 서식통일_부연괄호(body, 보호괄호, include_trailing=True)
    # 문장 안 ※ 참고(예: 'ㅇ 모집기간: … 마감시  ※ 일부 프로그램 상이')는 문서가 본문보다
    # 작게 쓰는 부연이다(실측: 정책회의의 11~13pt ※ 참고가 15pt로 커짐). 조사·교정 범위를
    # ※ 앞에서 끝내 원래 서식을 둔다. 괄호 안 ※는 괄호 규칙을 따른다.
    앞요소끝 = max((span[1] for span in 보호괄호), default=0)
    참고 = body.find("※", 앞요소끝)
    if (참고 > 0 and body[앞요소끝:참고].strip()
            and not any(left <= 참고 < right for left, right in 부연괄호)):
        본문끝 = utf16길이(body[:참고].rstrip())
        부연괄호 = tuple(span for span in 부연괄호 if span[1] <= 참고)
    부연괄호16 = tuple(tuple(utf16길이(body[:i]) for i in span) for span in 부연괄호)
    try:
        from docfit_core.style_inventory import _tag
        chars, paras = 분석["chars"], 분석["paras"]
        문단모양 = paras.get(para.get("paraPrIDRef"), {})
        cursor = 0
        runs = []
        text_colors = []
        color_runs, shade_runs = [], []
        # 기울임·밑줄·취소선도 글자색처럼 구간별 값을 모아 문장 대부분이 쓰는 값만 비교한다.
        italic_runs, underline_runs, strike_runs = [], [], []
        marker_bold_runs, label_bold_runs, aside_runs = [], [], []
        장평빈도 = Counter()
        for run in (item for item in para if _tag(item) == "run"):
            run_text = _서식통일_run_text(run)[0]
            run_length = len(run_text.encode("utf-16-le")) // 2
            end_offset = cursor + run_length
            start_selected = cursor
            end_selected = min(end_offset, 본문끝)
            char = chars.get(run.get("charPrIDRef"))
            if char and run_text.strip() and end_selected > start_selected:
                text_colors.append(str(char.get("color", "")).upper())
                구간 = ((시작[0], 시작[1], 시작[2] + start_selected),
                        (시작[0], 시작[1], 시작[2] + end_selected))
                글자수 = len(run_text.strip()) or 1
                color_runs.append(구간 + (str(char.get("color", "")).upper(), 글자수))
                shade_runs.append(구간 + (_서식통일_음영값(char.get("shade")), 글자수))
                italic_runs.append(구간 + (bool(char.get("italic")), 글자수))
                underline_runs.append(구간 + (str(char.get("underline") or "NONE").upper(), 글자수))
                # 한/글은 취소선 없는 글자에도 shape="3D"를 저장한다(실측). 선 모양만 취소선으로 본다.
                strike_runs.append(구간 + (str(char.get("strikeout") or "NONE").upper() not in ("NONE", "3D"),
                                           글자수))
                장평빈도[int(char.get("ratio", 100))] += end_selected - start_selected
                shape = (char["font"].get("hangul"), round(char["size_pt"] * 100))
                구간들 = [(left, right, False)
                         for left, right in 서식통일_범위분리(
                             start_selected, end_selected, 부연괄호16)]
                구간들.extend((max(start_selected, left), min(end_selected, right), True)
                              for left, right in 부연괄호16
                              if right > start_selected and left < end_selected)
                # 괄호 안도 대표 글꼴 판정·적용 대상이다. 다만 크기는 별도
                # 규칙(-2pt)이므로 기본 크기 표본/적용에서는 제외한다.
                for left, right, is_aside in sorted(구간들):
                    if right > left:
                        run_start = (시작[0], 시작[1], 시작[2] + left)
                        run_end = (시작[0], 시작[1], 시작[2] + right)
                        runs.append((run_start, run_end, shape, max(1, right - left), is_aside))
                for span, bold_runs in ((marker_span16, marker_bold_runs),
                                        (label_span16, label_bold_runs)):
                    if span:
                        left, right = max(start_selected, span[0]), min(end_selected, span[1])
                        if right > left:
                            bold_runs.append(((시작[0], 시작[1], 시작[2] + left),
                                              (시작[0], 시작[1], 시작[2] + right),
                                              bool(char.get("bold")), right - left))
                for left, right in 부연괄호16:
                    left, right = max(start_selected, left), min(end_selected, right)
                    if right > left:
                        aside_runs.append(((시작[0], 시작[1], 시작[2] + left),
                                           (시작[0], 시작[1], 시작[2] + right),
                                           round(char["size_pt"] * 100), right - left))
            cursor = end_offset
        if cursor < 본문끝:
            return None
    except Exception as exc:
        진단로그(f"[서식통일] HWPX 문자모양 분석 실패 — 안전을 위해 해당 문단 건너뜀: {exc}")
        return None
    if not runs and not aside_runs:
        return None

    def 문단_요소별_표본값(index):
        빈도 = Counter()
        for run in runs:
            shape, 길이 = run[2], run[3]
            is_aside = bool(run[4]) if len(run) > 4 else False
            if index == 1 and is_aside:
                continue
            value = shape[index]
            if value is not None:
                빈도[value] += 길이
        전체 = sum(빈도.values())
        if not 전체:
            return None
        최빈값, 최빈길이 = 빈도.most_common(1)[0]
        if 최빈길이 / 전체 < 서식통일_최소비율:
            return None
        if sum(1 for count in 빈도.values() if count == 최빈길이) > 1:
            return None
        return 최빈값

    def weighted_bold(values):
        total = sum(item[3] for item in values)
        if not total:
            return None
        bold = sum(item[3] for item in values if item[2])
        plain = total - bold
        if max(bold, plain) / total < 서식통일_최소비율:
            return None
        return bold > plain

    표본모양 = (문단_요소별_표본값(0), 문단_요소별_표본값(1), tuple(runs), {
        "indentation": 문단모양.get("indent"),
        "left_margin": 문단모양.get("left"),
        # HWPX의 음수 first-line offset은 내어쓰기 상태를 뜻한다. 정확한
        # 폭은 문두 라벨마다 다르므로 대표값은 '적용/미적용'으로 집계하고,
        # 적용 단계에서는 한/글 Shift+Tab으로 각 문장의 폭을 실측한다.
        "hanging_indent": int(문단모양.get("indent") or 0) < -20,
        # 한/글이 저장한 줄 배치(lineseg) 수. 내어쓰기는 둘째 줄이 있어야 드러난다.
        "line_count": sum(1 for item in para if _tag(item) == "linesegarray"
                          for _ in item) or 1,
        # 문단 전체에 쓰이는 장평·문단 위 간격도 문서 대표값과 비교한다. 줄 간격은 쪽 배치를
        # 위해 구역별로 일부러 조정하는 레이아웃 값이라 서식통일 비교 대상에서 뺀다.
        "ratio": 장평빈도.most_common(1)[0][0] if 장평빈도 else None,
        "prev_spacing": 문단모양.get("prev"),
        "marker_bold": weighted_bold(marker_bold_runs),
        "label_bold": weighted_bold(label_bold_runs),
        "marker_bold_runs": tuple(marker_bold_runs),
        "label_bold_runs": tuple(label_bold_runs),
        "parenthetical_size_runs": tuple(aside_runs),
        "red_marked": bool(text_colors) and all(color == "#FF0000" for color in text_colors),
        # 글자색·음영은 문장 대부분(60% 이상)이 쓰는 값을 문장 값으로 본다. 한두 낱말의
        # 강조색은 문장 값을 바꾸지 못하므로 서식통일이 건드리지 않는다.
        "color": 서식통일_우세값((run[2], run[3]) for run in color_runs),
        "shade": 서식통일_우세값((run[2], run[3]) for run in shade_runs),
        "color_runs": tuple(color_runs),
        "shade_runs": tuple(shade_runs),
        "italic": 서식통일_우세값((run[2], run[3]) for run in italic_runs),
        "underline": 서식통일_우세값((run[2], run[3]) for run in underline_runs),
        "strike": 서식통일_우세값((run[2], run[3]) for run in strike_runs),
        "italic_runs": tuple(italic_runs),
        "underline_runs": tuple(underline_runs),
        "strike_runs": tuple(strike_runs),
        # 문단 정렬·좌우 여백. 왼쪽 여백은 항목기호 앞 빈칸으로 들여 쓴 문서와 섞일 수 있어
        # 기호 앞 빈칸 수가 대표값과 같은 문장끼리만 비교한다.
        "align": 문단모양.get("align"),
        "right_margin": 문단모양.get("right"),
        "lead_spaces": len(body) - len(body.lstrip(" \t 　")),
        "position_text": body,
    })
    return 표본모양, 시작, (시작[0], 시작[1], 시작[2] + 본문끝)


def _서식통일_그룹키(marker, text, pos):
    """같은 계층(번호 계열을 묶은 항목기호·보고서 역할)의 문장끼리 대표 서식을 비교한다."""
    기호, 역할, 원래기호 = 서식통일_항목기호(text)
    role = 항목기호_역할표().get(원래기호) or 역할 or 보고서_문단역할(text) or "미분류"
    return 기호 or marker, role, "문서 공통"


def _서식통일_현재_HWPX():
    """현재 열려 있는 문서의 HWPX 원본 경로를 반환한다."""
    후보 = []
    try:
        후보.append(str(hwp.Path))
    except Exception:
        pass
    try:
        후보.append(str(hwp.XHwpDocuments.Item(0).FullName))
    except Exception:
        pass
    for 경로 in 후보:
        path = Path(경로.strip('"'))
        if path.is_file() and path.suffix.lower() == ".hwpx":
            return path
    return None


def _서식통일_불일치_구간(모양, 시작, 끝, 글꼴, 크기):
    """표준과 다른 연속 run만 모아 강조서식 등 기존 속성을 보존한다."""
    runs = 모양[2] if len(모양) > 2 else ()
    문단기본 = (모양[0], 모양[1])
    변경, 현재 = [], None
    for run in runs:
        run_start, run_end, run_shape = run[:3]
        is_aside = bool(run[4]) if len(run) > 4 else False
        # 표준 서식이 기준을 정하는 작업에서는 괄호 축소 규칙이 줄인 글자(본문 -2pt)를
        # 서식통일의 '중간 괄호' 판정과 관계없이 정상으로 본다.
        if (not 서식통일_빨간표시_사용 and 괄호_축소_사용 and 크기 is not None
                and run_shape[1] == 크기 - int(round(float(괄호_축소_pt) * 100))):
            is_aside = True
        # 대표 글꼴·크기와 다른 run만 교정한다. 글꼴·크기와 무관한 강조 속성은
        # 문자모양 적용 단계에서 기존 값을 보존한다.
        mismatch = ((글꼴 is not None and run_shape[0] != 글꼴)
                    or (크기 is not None and not is_aside and run_shape[1] != 크기))
        if mismatch:
            if 현재 and 현재[1] == run_start:
                현재[1] = run_end
            else:
                if 현재:
                    변경.append(tuple(현재))
                현재 = [run_start, run_end]
        elif 현재:
            변경.append(tuple(현재))
            현재 = None
    if 현재:
        변경.append(tuple(현재))
    return 변경


def _서식통일_부연괄호_불일치_구간(모양, 표준크기):
    """본문 크기보다 2pt 작은 규칙을 벗어난 중간 괄호만 교정한다."""
    if 표준크기 is None or len(모양) < 4 or not isinstance(모양[3], dict):
        return [], None
    차이 = (서식통일_괄호크기차이 if 서식통일_괄호크기차이 is not None
            else int(round(float(괄호_축소_pt) * 100)))
    목표크기 = int(표준크기) - 차이
    if 목표크기 <= 0:
        return [], None
    runs = 모양[3].get("parenthetical_size_runs", ())
    변경 = [(run_start, run_end) for run_start, run_end, size, _ in runs
            if size != 목표크기]
    return list(서식통일_범위병합(변경)), 목표크기


def _서식통일_굵기_불일치_구간(모양, 요소, 표준):
    """항목기호/괄호라벨 안에서 굵기만 다른 연속 run을 반환한다."""
    if 표준 is None or len(모양) < 4 or not isinstance(모양[3], dict):
        return []
    runs = 모양[3].get(f"{요소}_bold_runs", ())
    변경, 현재 = [], None
    for run_start, run_end, bold, _ in runs:
        if bold != 표준:
            if 현재 and 현재[1] == run_start:
                현재[1] = run_end
            else:
                if 현재:
                    변경.append(tuple(현재))
                현재 = [run_start, run_end]
        elif 현재:
            변경.append(tuple(현재))
            현재 = None
    if 현재:
        변경.append(tuple(현재))
    return 변경


def 서식통일_대표(모양들):
    """신뢰도 기준을 통과한 문단 빈도 대표값을 속성별로 독립 산출한다."""
    결과 = {}
    for 항목, 추출 in (
        ("font", lambda 모양: 모양[0]),
        ("size", lambda 모양: 모양[1]),
        ("marker_bold", lambda 모양: 모양[3].get("marker_bold")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
        ("label_bold", lambda 모양: 모양[3].get("label_bold")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
        # 내어쓰기 대표값은 여러 줄 문장으로만 정한다(한 줄 항목의 내어쓰기는 보이지 않는다).
        ("hanging_indent", lambda 모양: 모양[3].get("hanging_indent")
         if len(모양) > 3 and isinstance(모양[3], dict) and 모양[3].get("line_count", 2) > 1
         else None),
        ("ratio", lambda 모양: 모양[3].get("ratio")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
        ("color", lambda 모양: 모양[3].get("color")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
        ("shade", lambda 모양: 모양[3].get("shade")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
        # 서식 요소 분석 고도화(2026-10-03): 기울임·밑줄·취소선·정렬·좌우 여백·기호 앞 빈칸.
        ("italic", lambda 모양: 모양[3].get("italic")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
        ("underline", lambda 모양: 모양[3].get("underline")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
        ("strike", lambda 모양: 모양[3].get("strike")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
        ("align", lambda 모양: 모양[3].get("align")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
        ("left", lambda 모양: 모양[3].get("left_margin")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
        ("right", lambda 모양: 모양[3].get("right_margin")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
        ("lead", lambda 모양: 모양[3].get("lead_spaces")
         if len(모양) > 3 and isinstance(모양[3], dict) else None),
    ):
        값들 = [추출(모양) for 모양 in 모양들 if 모양]
        # 표본이 두 개뿐인 희소 기호(예: ※)도 두 표본이 완전히 일치하면
        # 빈도 100%의 대표값으로 인정한다. 둘이 다르면 동률이라 자동 보정하지 않는다.
        최소표본 = max(2, min(서식통일_최소문단수, len(모양들)))
        대표값, 빈도, _ = 서식통일_최빈값(
            값들, minimum=최소표본, ratio=서식통일_최소비율)
        결과[항목] = (대표값, 빈도 if 대표값 is not None else 0)
    return 결과


def _서식통일_표지인가(첫쪽_문단번호, 본문크기):
    """1쪽이 표지인지 HWPX로 판정한다(표 안 제목 글자까지 포함, 읽기 전용).

    본문 대표 크기보다 확연히 큰 가운데 정렬 글자가 있고 본문형 문장(ㅇ·- 등)이
    거의 없으면 표지로 보고 서식통일에서 뺀다.
    """
    문서경로 = _서식통일_현재_HWPX()
    if 문서경로 is None or not 첫쪽_문단번호 or not 본문크기:
        return False
    try:
        from docfit_core.style_inventory import _tag, _run_text
        분석 = _서식통일_HWPX_분석(문서경로)
        항목들 = []
        for 번호 in 첫쪽_문단번호:
            문단 = 분석["paragraphs"][번호]
            for p in (item for item in 문단.iter() if _tag(item) == "p"):
                글자 = "".join(_run_text(run) for run in p if _tag(run) == "run")
                if not 글자.strip():
                    continue
                크기들 = [round(분석["chars"][run.get("charPrIDRef")]["size_pt"] * 100)
                          for run in p if _tag(run) == "run" and _run_text(run).strip()
                          and run.get("charPrIDRef") in 분석["chars"]]
                크기 = max(크기들, default=0)
                가운데 = 분석["paras"].get(p.get("paraPrIDRef"), {}).get("align") == "CENTER"
                본문형 = (서식통일_항목기호(글자)[1] in ("본문", "내용", "부연설명")
                          and 크기 <= 본문크기 * 1.15)
                항목들.append((글자, 크기, 가운데, 본문형))
        return 서식통일_표지판정(항목들, 본문크기)
    except Exception as exc:
        진단로그(f"[서식통일] 표지 판정 실패 — 1쪽도 일반 쪽으로 처리: {exc}")
        return False


def _서식통일_제목표_표본(제외문단=()):
    """1칸 표(제목 상자) 안 항목기호 문장의 (본문 문단 번호, 그룹키, 표본 모양) 목록.

    장·절 제목은 흔히 1칸 표 안에 있고, 같은 계층 제목이 본문에 표 없이 한두 번
    나오기도 한다. 본문 표본이 부족한 계층의 대표값을 정할 때만 읽기 전용으로 참고한다.
    """
    문서경로 = _서식통일_현재_HWPX()
    if 문서경로 is None:
        return []
    try:
        from docfit_core.style_inventory import _tag, _run_text
        분석 = _서식통일_HWPX_분석(문서경로)
    except Exception:
        return []
    결과 = []
    for 번호, 문단 in enumerate(분석["paragraphs"]):
        if 번호 in 제외문단:
            continue
        for 표 in (item for item in 문단.iter() if _tag(item) == "tbl"):
            if 표.get("rowCnt") != "1" or 표.get("colCnt") != "1":
                continue
            for p in (item for item in 표.iter() if _tag(item) == "p"):
                글자 = "".join(_run_text(run) for run in p if _tag(run) == "run")
                if not 서식통일_항목기호(글자)[0]:
                    continue
                값들 = []
                for run in (item for item in p if _tag(item) == "run"):
                    char = 분석["chars"].get(run.get("charPrIDRef"))
                    길이 = len(_run_text(run).strip())
                    if char and 길이:
                        값들.append((char["font"].get("hangul"), round(char["size_pt"] * 100),
                                    str(char.get("color", "")).upper(),
                                    _서식통일_음영값(char.get("shade")), 길이))
                if not 값들:
                    continue
                모양 = (서식통일_우세값((v[0], v[4]) for v in 값들),
                        서식통일_우세값((v[1], v[4]) for v in 값들), (), {
                            "color": 서식통일_우세값((v[2], v[4]) for v in 값들),
                            "shade": 서식통일_우세값((v[3], v[4]) for v in 값들),
                            "table_heading": True})
                결과.append((번호, _서식통일_그룹키("", 글자, None), 모양))
    return 결과


def _서식통일_체계경계(표본, 위치텍스트):
    """서식 체계가 바뀌는 (본문 문단 번호, 영역 이름) 목록.

    붙임·별첨 제목(본문 문단이나 제목 표 안)은 구조 경계로, 여러 계층이 같은 곳에서 함께
    서식을 바꾸는 큰 전환점은 서식 경계로 본다. 작은 구간의 다른 서식은 경계가 아니다.
    """
    경계 = {}
    문서경로 = _서식통일_현재_HWPX()
    if 문서경로 is not None:
        try:
            from docfit_core.style_inventory import _tag
            분석 = _서식통일_HWPX_분석(문서경로)
            for 번호, 문단 in enumerate(분석["paragraphs"]):
                for p in (item for item in 문단.iter() if _tag(item) == "p"):
                    글자 = "".join(_서식통일_run_text(run)[0] for run in p if _tag(run) == "run")
                    if 글자.strip():
                        이름 = 서식통일_붙임제목(글자)
                        if 이름 and 번호 > 0:
                            경계[번호] = 이름
                        break
        except Exception as exc:
            진단로그(f"[서식통일] 붙임 구역 판별 실패 — 문서 전체를 한 체계로 봄: {exc}")
    순서열 = defaultdict(list)
    for marker, 항목들 in 표본.items():
        for 모양, 시작, _, text in 항목들:
            키 = _서식통일_그룹키(marker, 위치텍스트.get(tuple(시작), text), 시작)[:2]
            값 = (모양[0], 모양[1]) if 모양[0] is not None and 모양[1] is not None else None
            순서열[키].append((시작[1], 값))
    for 위치 in 서식통일_체계전환점(순서열):
        if not any(abs(위치 - 기존) <= 5 for 기존 in 경계):
            경계[위치] = f"서식 전환 {len(경계) + 1}"
    return sorted(경계.items())


def _서식통일_참고표_이웃대표_보완(그룹별_표본, 프로필):
    """※ 대표값이 미확정이면 앞뒤 문장이 모두 표준인 ※의 값을 대표값으로 본다."""
    필드추출 = {
        "font": lambda 모양: 모양[0],
        "size": lambda 모양: 모양[1],
        "marker_bold": lambda 모양: 모양[3].get("marker_bold"),
        "label_bold": lambda 모양: 모양[3].get("label_bold"),
        "hanging_indent": lambda 모양: 모양[3].get("hanging_indent"),
    }

    def 추출(모양, 필드):
        if 필드 not in ("font", "size") and (len(모양) < 4 or not isinstance(모양[3], dict)):
            return None
        return 필드추출[필드](모양)

    def 표준문장인가(그룹키, 모양):
        대표 = 프로필.get(그룹키) or {}
        for 필드 in 필드추출:
            표준 = 대표.get(필드, (None, 0))[0]
            if 필드 in ("font", "size") and 표준 is None:
                return False
            if 표준 is not None and 추출(모양, 필드) not in (None, 표준):
                return False
        return True

    순서 = sorted(((항목[1], 그룹키, 항목[0])
                  for 그룹키, 항목들 in 그룹별_표본.items() for 항목 in 항목들),
                 key=lambda item: item[0])
    후보 = {}
    for i, (_, 그룹키, 모양) in enumerate(순서):
        대표 = 프로필.get(그룹키)
        if 그룹키[0] != "※" or not 대표:
            continue
        if not 0 < i < len(순서) - 1:
            continue
        미확정 = [필드 for 필드 in 필드추출 if 대표.get(필드, (None, 0))[0] is None]
        if not 미확정:
            continue
        앞, 뒤 = 순서[i - 1], 순서[i + 1]
        if not (표준문장인가(앞[1], 앞[2]) and 표준문장인가(뒤[1], 뒤[2])):
            continue
        for 필드 in 미확정:
            값 = 추출(모양, 필드)
            if 값 is not None:
                후보.setdefault((그룹키, 필드), []).append(값)
    보완수 = 0
    for (그룹키, 필드), 값들 in 후보.items():
        값 = max(값들, key=값들.count)
        # 이웃 기준 ※ 가운데 과반이 같은 값일 때만 채택한다(실측: 5개 중 2개뿐인 글꼴을
        # 대표로 삼아 다수 글꼴 ※ 6개를 바꾸려 함).
        if 값들.count(값) * 2 <= len(값들):
            continue
        프로필[그룹키][필드] = (값, 값들.count(값))
        보완수 += 1
        로그(f"[서식통일] ※ 대표값 보완: {그룹키[0]}/{그룹키[1]} {필드}={값} "
             f"(앞뒤 문장이 표준인 ※ {len(값들)}개 기준)")
    return 보완수


def _서식통일_대표값_사용자검토(그룹별_표본):
    """조사된 대표 서식을 사용자 확인 없이 자동 승인한다."""
    로그(f"[서식통일] 대표 서식 {len(그룹별_표본)}개 그룹 자동 승인(사용자 확인 생략)")
    return True


def _서식통일_적용영역_사용자검토(계획):
    """불일치 영역을 적용 전에 사용자에게 보여 주고 선택된 계획만 돌려준다."""
    후보 = [index for index, item in enumerate(계획) if item.get("mismatch")]
    if _서식통일_대표값_검토콜백 is None:
        로그("[서식통일] 사용자 검토 UI가 없어 시험 모드에서 불일치 영역 전체 승인")
        return {"approved": True, "selected": 후보}
    요청 = _서식통일_대표값_검토콜백("regions", 계획)
    return 요청 or {"approved": False, "selected": []}


# 서식통일 뒤 '작업 결과 확인' 창을 띄울지(설정 unify_result_window, 기본 꺼짐). 꺼져 있으면 결과는 처리 기록과
# 최종 검수 보고서에만 남긴다.
서식통일_결과창_사용 = False


def 서식통일_결과창_반영(value):
    """설정값을 '작업 결과 확인' 창 사용 여부 전역값에 반영하고 반영한 값을 돌려준다."""
    global 서식통일_결과창_사용
    서식통일_결과창_사용 = bool(value)
    return 서식통일_결과창_사용


def _결과창_띄우는가(total):
    """저장 결과 검수 뒤 '작업 결과 확인' 창을 띄우는지: 문서 하나를 처리할 때, 설정에서 켰을 때만."""
    return total == 1 and 서식통일_결과창_사용


def _서식통일_최종결과_사용자확인(결과):
    """저장 후 읽기 전용 검수 결과를 GUI에 보여 준다.

    결과는 읽기 전용이라 확인을 기다릴 이유가 없다. 예전에는 작업 스레드가 '결과 확인'을 누를
    때까지 멈춰, 여러 문서를 맡기고 자리를 비우면 첫 문서 뒤에서 일괄 작업이 서 있었다.
    """
    if _서식통일_대표값_검토콜백 is None:
        return
    gui_queue.put(("style_unify_result_review",
                   {"payload": 결과, "done": threading.Event(), "approved": False}))


def _서식통일_미확정_항목(대표, text):
    """실제로 존재하는 요소의 대표값만 요구한다(라벨 없는 문장 등 제외).

    내어쓰기는 문장 서식이 아니라 줄 배치 값이다. 한 줄 항목은 내어쓰기가 보이지 않아
    문서마다 제각각이므로(실측: '-' 한 줄 항목 57:39), 대표값이 없다고 빨간 표시하지 않고
    내어쓰기만 건드리지 않는다.
    """
    marker, label = _서식통일_문두요소_범위(text)
    fields = ["font", "size"]
    if marker:
        fields.append("marker_bold")
    if label:
        fields.append("label_bold")
    return [field for field in fields if 대표.get(field, (None, 0))[0] is None]


def _서식통일_미확정_빨간표시(시작, 끝):
    """대표값 미확정 문단은 글자색만 변경한다. 혼합 자간은 읽거나 쓰지 않는다."""
    try:
        단어모드_범위선택(시작, 끝)
        action = hwp.CreateAction("CharShape")
        params = action.CreateSet()
        params.SetItem("TextColor", hwp.RGBColor(255, 0, 0))
        if action.Execute(params) is False:
            raise RuntimeError("대표값 미확정 문단의 빨간색 표시 실패")
    finally:
        hwp_run("Cancel")


def _서식통일_문단앞간격_적용(pos, hwpunit):
    """현재 문단의 문단 위(앞) 간격만 대표값으로 바꾼다."""
    원래위치 = hwp.GetPos()
    try:
        if hwp.SetPos(*pos) is False:
            raise RuntimeError("대상 문단 이동 실패")
        action = hwp.HAction
        params = hwp.HParameterSet.HParaShape
        action.GetDefault("ParagraphShape", params.HSet)
        # 실측상 HWPX의 prevSpacing 값은 COM HParaShape.PrevSpacing보다
        # 절반으로 직렬화된다(예: COM 1100 → HWPX 550). 표본과 동일한
        # HWPX 대표값을 저장하려면 COM에는 2배 값을 지정해야 한다.
        요청COM값 = int(hwpunit) * 2
        params.PrevSpacing = 요청COM값
        if action.Execute("ParagraphShape", params.HSet) is False:
            raise RuntimeError("문단 앞 간격 적용 결과가 False입니다")
        actual = int(hwp.ParaShape.Item("PrevSpacing"))
        if abs(actual - 요청COM값) > 1:
            raise RuntimeError(f"문단 앞 간격 적용 후 확인 실패: 요청 {요청COM값}, 실제 {actual} COMUNIT")
        return True
    except Exception as exc:
        로그(f"[서식통일] 문단 앞 간격 적용 실패(건너뜀): {exc}")
        return False
    finally:
        try:
            hwp.SetPos(*원래위치)
        except Exception:
            pass


def _서식통일_내어쓰기_필요(pos, text):
    """읽기 전용으로 문단에 내어쓰기가 빠져 있는지 판정한다.

    문두 라벨마다 글자 폭이 달라 음수 내어쓰기의 절대값은 문장별로 다르다.
    따라서 임의 폭 추정값과 비교해 이미 적용된 내어쓰기를 다시 쓰지 않고,
    문단 모양의 Indentation이 사실상 0인 경우에만 누락으로 판정한다.
    """
    offset = 문단_내어쓰기_기준_오프셋(text)
    if hwp is None or offset is None or offset <= 0:
        return False
    original_pos = None
    try:
        original_pos = hwp.GetPos()
        if hwp.SetPos(*pos) is False:
            return None
        hwp_run("MoveParaBegin")
        current = int(hwp.ParaShape.Item("Indentation"))
        # 20 HWPUNIT = 0.2pt. 작은 반올림 잔차도 이미 적용된 상태로 취급한다.
        return current >= -20
    except Exception as exc:
        진단로그(f"[서식통일] 내어쓰기 판정 실패 — 안전을 위해 건너뜀: {exc}")
        return None
    finally:
        try:
            hwp_run("Cancel")
            if original_pos is not None:
                hwp.SetPos(*original_pos)
        except Exception:
            pass


def _서식통일_내어쓰기_상태(pos, text):
    """문단의 내어쓰기 적용 여부를 읽기 전용으로 반환한다 (불명은 None)."""
    offset = 문단_내어쓰기_기준_오프셋(text)
    if hwp is None or offset is None or offset <= 0:
        return None
    original_pos = None
    try:
        original_pos = hwp.GetPos()
        if hwp.SetPos(*pos) is False:
            return None
        hwp_run("MoveParaBegin")
        return int(hwp.ParaShape.Item("Indentation")) < -20
    except Exception as exc:
        진단로그(f"[서식통일] 내어쓰기 상태 조사 실패 — 안전을 위해 건너뜀: {exc}")
        return None
    finally:
        try:
            hwp_run("Cancel")
            if original_pos is not None:
                hwp.SetPos(*original_pos)
        except Exception:
            pass


def _서식통일_문단서식_적용(item):
    """한 문단 안에서 대표값과 다른 문자 속성만 적용한다."""
    operations = (
        (item["font_runs"], {"폰트": item["font"]}),
        (item["size_runs"], {"크기_pt": item["size"] / 100 if item["size"] else None}),
        (item["aside_runs"], {"크기_pt": item["aside_size"] / 100 if item["aside_size"] else None}),
        (item["marker_bold_runs"], {"굵게": item["marker_bold"]}),
        (item["label_bold_runs"], {"굵게": item["label_bold"]}),
    )
    for ranges, options in operations:
        for start, end in ranges:
            try:
                단어모드_범위선택(start, end)
                문자모양_적용_현재선택(**options, 자간_유지=True)
            finally:
                hwp_run("Cancel")
    if item.get("ratio_fix") is not None:
        try:
            단어모드_범위선택(item["start"], item["end"])
            문자모양_적용_현재선택(장평=item["ratio_fix"], 자간_유지=True)
        finally:
            hwp_run("Cancel")
    for ranges, 필드, 값 in ((item.get("color_runs", ()), "TextColor", item.get("color")),
                            (item.get("shade_runs", ()), "ShadeColor", item.get("shade"))):
        for start, end in ranges:
            try:
                단어모드_범위선택(start, end)
                _서식통일_색_적용(필드, 값)
            finally:
                hwp_run("Cancel")
    for 필드, ranges in (item.get("char_runs") or {}).items():
        if ranges:
            _서식통일_글자요소_적용(필드, (item.get("char_values") or {}).get(필드),
                                   (item.get("char_examples") or {}).get(필드), ranges)
    예시 = item.get("para_examples") or {}
    if 예시:
        # 문서 안에서 대표값을 가진 실제 문단의 값을 읽어 그대로 복사한다(단위 변환 없음).
        값들 = {}
        for 종류, 위치 in 예시.items():
            if 위치 is None:
                continue
            hwp.SetPos(*위치)
            모양 = hwp.HParameterSet.HParaShape
            hwp.HAction.GetDefault("ParagraphShape", 모양.HSet)
            if 종류 == "indent":
                값들["Indentation"] = int(모양.Indentation)
                값들["LeftMargin"] = int(모양.LeftMargin)
            elif 종류 == "align":
                값들["AlignType"] = int(모양.AlignType)
            elif 종류 == "left":
                값들["LeftMargin"] = int(모양.LeftMargin)
            elif 종류 == "right":
                값들["RightMargin"] = int(모양.RightMargin)
            else:
                값들["PrevSpacing"] = int(모양.PrevSpacing)
        if 값들:
            hwp.SetPos(*item["start"])
            action = hwp.CreateAction("ParagraphShape")
            params = action.CreateSet()
            for key, value in 값들.items():
                params.SetItem(key, value)
            if action.Execute(params) is False:
                raise RuntimeError("대표 문단모양 복사 실패")


# 서식통일 글자 요소 → 한/글 CharShape 항목(실측 2026-10-03: Italic=1 → italic,
# UnderlineType=1 → underline BOTTOM, StrikeOutType=1 → strikeout SOLID).
_서식통일_글자요소_항목 = {
    "italic": ("Italic",),
    "underline": ("UnderlineType", "UnderlineShape", "UnderlineColor"),
    "strike": ("StrikeOutType", "StrikeOutShape", "StrikeOutColor"),
}


def _서식통일_글자요소_적용(필드, 표준, 예시구간, 구간들):
    """기울임·밑줄·취소선을 대표값으로 맞춘다.

    없애는 경우(기울임 끄기, 밑줄·취소선 없음)는 종류 항목만 0으로 둔다. 넣는 경우에는 대표값을 쓴
    다른 문장 구간(예시구간)의 선 종류·모양·색을 읽어 그대로 복사한다(값 대응을 추정하지 않는다).
    """
    항목들 = _서식통일_글자요소_항목[필드]
    if 필드 == "italic":
        값들 = {"Italic": 1 if 표준 else 0}
    elif 표준 in ("NONE", False):
        값들 = {항목들[0]: 0}
    else:
        if not 예시구간:
            return
        try:
            단어모드_범위선택(*예시구간)
            모양 = hwp.HParameterSet.HCharShape
            hwp.HAction.GetDefault("CharShape", 모양.HSet)
            값들 = {항목: int(getattr(모양, 항목)) for 항목 in 항목들}
        finally:
            hwp_run("Cancel")
    for start, end in 구간들:
        try:
            단어모드_범위선택(start, end)
            action = hwp.CreateAction("CharShape")
            params = action.CreateSet()
            for 항목, 값 in 값들.items():
                params.SetItem(항목, 값)
            if action.Execute(params) is False:
                raise RuntimeError(f"서식통일 {필드} 적용 실패")
        finally:
            hwp_run("Cancel")


def _서식통일_색값(value):
    """'#RRGGBB'는 한/글 색 값으로, '없음'(음영 없음)은 0xFFFFFFFF로 바꾼다."""
    text = str(value or "").strip().lstrip("#")
    if len(text) != 6:
        return 0xFFFFFFFF
    return hwp.RGBColor(int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def _서식통일_색_적용(필드, 값):
    """선택 영역의 글자색(TextColor) 또는 음영색(ShadeColor)만 바꾼다."""
    action = hwp.CreateAction("CharShape")
    params = action.CreateSet()
    params.SetItem(필드, _서식통일_색값(값))
    if action.Execute(params) is False:
        raise RuntimeError(f"서식통일 {필드} 적용 실패")


def _서식통일_문단내어쓰기_적용(item):
    """해당 문단의 자간 처리가 끝난 실제 글자 폭으로 내어쓰기를 확정한다."""
    expected = item["expected_hanging"]
    원문 = item.get("position_text") or item["text"]
    if expected is None or 문단_내어쓰기_기준_오프셋(원문) is None:
        return
    if expected:
        if not 문단_내어쓰기_적용(item["start"], 원문):
            검수_문제_기록(현재_처리파일, "[서식통일 내어쓰기 미적용] " + item["text"].strip())
    elif item["hanging_mismatch"]:
        if hwp.SetPos(*item["start"]) is False:
            raise RuntimeError("대상 문단 이동 실패")
        hwp_run("MoveParaBegin")
        _내어쓰기_값_설정(0)


def _서식통일_문단자간_조정(start, end):
    """예외 문단만 검사. 분리 어절을 ±10% 이내에서 조정하고 실패 시 복원."""
    if start[:2] != end[:2] or start[2] >= end[2]:
        raise ValueError("자간 처리 범위는 같은 문단이어야 합니다")
    anchor = start
    seen = set()
    limit = max(0, min(10, int(자간_최대시도_본문)))
    while anchor[:2] == start[:2] and anchor[2] < end[2]:
        if 중단_요청됨():
            return False
        if anchor in seen:
            break
        seen.add(anchor)
        hwp.SetPos(*anchor)
        info = 단어모드_분리정보(anchor)
        if info:
            line_start, boundary, word_start, word_end, left, right = info
            positions = (line_start, boundary, word_start, word_end)
            if any(pos[:2] != start[:2] or not start[2] <= pos[2] <= end[2] for pos in positions):
                raise RuntimeError("자간 조정 범위가 대상 문단을 벗어났습니다")
            shrink = 어절분리_앞줄당김인가(left, right, 단어모드_마지막줄_짧은잔여인가(boundary))
            success = False
            for direction in ((-1, 1) if shrink else (1, -1)):
                target_end = word_end if direction < 0 else word_start
                if target_end[2] <= line_start[2] or word_start[2] < line_start[2]:
                    continue
                runs = 단어모드_자간보관(line_start, target_end)
                if runs is None:
                    return False
                if not runs:
                    continue
                values = [value for _, _, items in runs for value in items]
                # 이미 압축된 자간을 반복 실행 때 더 누적 축소하지 않는다.
                budget = min(limit, 10 + min(values) if direction < 0 else 10 - max(values))
                changed = False
                try:
                    for step in range(1, max(0, budget) + 1):
                        if 중단_요청됨():
                            return False
                        changed = True
                        단어모드_자간적용(runs, direction * step)
                        _, previous_end = 단어모드_줄범위(anchor)
                        if direction < 0:
                            success = previous_end[:2] == end[:2] and previous_end[2] >= word_end[2]
                        else:
                            next_start, next_end = 단어모드_줄범위(word_start)
                            success = (previous_end[2] <= word_start[2] and
                                       next_start[:2] == end[:2] == next_end[:2] and
                                       next_start[2] <= word_start[2] and next_end[2] >= word_end[2])
                        if success:
                            진단로그(f"[서식통일 자간] 문단 {start[:2]}, {direction * step:+d}%p")
                            break
                finally:
                    if changed and not success:
                        단어모드_자간적용(runs, 0)
                if success:
                    break
            if not success:
                검수_문제_기록(현재_처리파일, f"[서식통일 자간 미해결] 문단 {start[:2]}, 경계 {boundary[2]}: 안전 한도 내 조정 불가")
        hwp.SetPos(*anchor)
        hwp_run("MoveLineEnd")
        line_end = hwp.GetPos()
        if line_end[:2] != end[:2] or line_end[2] >= end[2]:
            break
        hwp_run("MoveNextChar")
        next_pos = hwp.GetPos()
        if next_pos[:2] != end[:2] or next_pos[2] <= anchor[2]:
            break
        anchor = next_pos
    hwp_run("Cancel")
    return True


def 서식통일_전체_적용(고정_프로필_재적용=False, 검증만=False):
    global _서식통일_문서대표프로필, _서식통일_최종감사, 서식통일_괄호크기차이
    if 중단_요청됨():
        return False
    범위표시 = (f"{쪽범위_실제[0]}~{쪽범위_실제[1]}쪽" if 쪽범위_실제 is not None
               else "전체 문서")
    기준설명 = ("최초 문서 표본에서 고정한 대표 프로필로 후속 변경을 재검증"
               if 고정_프로필_재적용 else "항목기호·보고서 계층별 문서 표본에서 대표 서식 산출")
    작업설명 = "저장 결과를 읽기 전용으로 검증" if 검증만 else "표준과 다른 구간만 보정"
    if 검증만:
        단계표시("서식통일 검수")
    elif not 고정_프로필_재적용:
        단계표시("서식통일 조사")
    로그(f"서식통일 시작: 수정 범위 {범위표시}, {기준설명}, {작업설명}, "
         "표준 문장은 무변경, 괄호(문두 라벨 제외)는 본문 크기 기준 -2pt, 자간 초기화 없음")
    if (not 검증만 and (고정_프로필_재적용 or 작업_모드 != "unify")
            and _서식통일_현재_HWPX() is not None):
        # 앞선 단계(공백 정리·표준 서식 등)가 문서를 바꿨으면 디스크의 HWPX와 문단 번호·글자
        # 위치가 다르다. 조사 전에 현재 상태를 스냅숏으로 저장해 원문·서식을 정확히 읽는다.
        try:
            _제목_임시hwpx_저장(Path(tempfile.mkdtemp(prefix="hwp_format_first_")) / "서식통일.hwpx")
        except Exception as exc:
            로그(f"[서식통일] 현재 상태 스냅숏 저장 실패 — 원문이 다른 문단은 건너뜀: {exc}")
    표본 = {}
    # 쪽 범위는 수정 대상을 제한하지만, 대표서식은 같은 문서의 정상 문장까지
    # 포함해 산출해야 한다. 선택 쪽에서만 표본을 모으면 그 쪽의 이상 서식이
    # 대표값으로 채택되어 검출이 0건이 되는 문제가 생긴다.
    문맥 = {}        # 문단 시작 위치 → 바로 앞 문장의 항목기호(문단 위 간격 기준)
    위치텍스트 = {}  # 문단 시작 위치 → 글자 위치와 맞는 원문(고정폭 빈칸 포함)
    첫쪽문단 = []    # 표지 판정용 1쪽 본문 문단 번호
    첫쪽끝 = False
    직전기호 = None
    hwp_run("MoveDocBegin")
    while True:
        if 중단_요청됨():
            return False
        hwp_run("MoveParaBegin")
        pos = hwp.GetPos()
        if pos[0] == 0:
            if not 첫쪽끝:
                if 현재_페이지번호() == 1:
                    첫쪽문단.append(pos[1])
                else:
                    첫쪽끝 = True
            text = 현재문단_텍스트()
            본문 = _서식통일_위치텍스트(pos, text) if text.strip() else text
            # 번호 계열('1.' '2.' …)은 한 그룹으로 묶고, 고정폭 빈칸 뒤 항목기호도 인식한다.
            marker = 서식통일_항목기호(본문)[0] if 본문.strip() else ""
            if marker:
                결과 = 서식통일_표본(pos, text)
                if 결과:
                    표본.setdefault(marker, []).append(결과 + (text,))
                    문맥[tuple(pos)] = 직전기호
                    위치텍스트[tuple(pos)] = 본문
                직전기호 = marker
            elif text.strip():
                직전기호 = None
            hwp.SetPos(*pos)
        if not 다음_문단으로_진행():
            break
    # 1쪽이 표지(본문보다 확연히 큰 가운데 정렬 제목)이면 표본·수정 대상에서 뺀다.
    본문크기 = 서식통일_우세값(((모양[1], 1) for 항목들 in 표본.values()
                             for 모양, *_ in 항목들 if 모양[1]), ratio=0)
    표지문단 = set()
    if 첫쪽끝 and 첫쪽문단 and _서식통일_표지인가(첫쪽문단, 본문크기):
        표지문단 = set(첫쪽문단)
        제외수 = 0
        for marker in list(표본):
            남김 = [항목 for 항목 in 표본[marker] if 항목[1][1] not in 표지문단]
            제외수 += len(표본[marker]) - len(남김)
            if 남김:
                표본[marker] = 남김
            else:
                del 표본[marker]
        로그(f"[서식통일] 1쪽을 표지로 판단해 제외: 본문({본문크기 / 100:g}pt)보다 큰 가운데 정렬 제목, "
             f"항목기호 문장 {제외수}개 제외")
    교정수 = 0
    확인문단수 = 0
    불일치목록 = []
    판정불가그룹 = []
    미확정문단 = []
    그룹별_표본 = {}
    # 한 문서에 서식 체계가 둘 이상일 수 있다(본문과 붙임 등). 붙임·별첨 제목과, 여러 계층이
    # 함께 서식을 바꾸는 큰 전환점에서 영역을 나누고 영역마다 대표 서식을 따로 정한다.
    경계 = _서식통일_체계경계(표본, 위치텍스트)

    def 영역키(번호):
        이름 = "본문" if 경계 else "문서 공통"
        for 위치, 경계이름 in 경계:
            if 번호 >= 위치:
                이름 = 경계이름
        return 이름

    for marker, 항목들 in 표본.items():
        for 항목 in 항목들:
            모양, 시작, 끝, text = 항목
            그룹키 = (_서식통일_그룹키(marker, 위치텍스트.get(tuple(시작), text), 시작)[:2]
                      + (영역키(시작[1]),))
            그룹별_표본.setdefault(그룹키, []).append(항목)
    제목표_표본 = [(번호, 키[:2] + (영역키(번호),), 모양)
                   for 번호, 키, 모양 in _서식통일_제목표_표본(표지문단)]
    if 경계:
        로그(f"[서식통일] 서식 체계 {len(경계) + 1}개로 나눠 영역마다 대표 서식을 정함: 본문 / "
             + " / ".join(f"{이름}(문단 {위치 + 1}부터)" for 위치, 이름 in 경계))
    # 문서 체계: 본문 문장과 제목 표의 항목기호를 문서 순서로 늘어놓아 바깥 → 안쪽 계층을 추정한다.
    순서 = sorted([(시작[1], 그룹키[:2]) for 그룹키, 항목들 in 그룹별_표본.items()
                  for _, 시작, _, _ in 항목들]
                 + [(번호, 그룹키[:2]) for 번호, 그룹키, _ in 제목표_표본])
    체계 = 서식통일_계층순서([그룹키 for _, 그룹키 in 순서])
    로그("[서식통일] 문서 체계(바깥 → 안쪽): "
         + " > ".join(f"{i}단계 {키[0]}({키[1]})" for i, 키 in enumerate(체계, 1)))
    로그(f"[서식통일] 1/5 표본 조사 완료: {sum(map(len, 그룹별_표본.values()))}개 문장, "
         f"{len(그룹별_표본)}개 그룹, 제목 표 {len(제목표_표본)}개 — 문서 변경 0건(읽기 전용)")
    if 검수_사용 and not 검증만 and not 고정_프로필_재적용 and _서식통일_현재_HWPX() is not None:
        # 검수 모드에서는 서식 요소 전수 분석(계층별·서식 표 칸별 대표값)을 작업 로그에 함께 남긴다.
        try:
            요소분석 = 서식요소.analyze_format_elements(_서식통일_현재_HWPX(), 서식표_종류판별)
            for 줄 in 서식요소.summary_lines(요소분석, limit=20):
                진단로그("[서식통일 요소 분석] " + 줄)
        except Exception as exc:
            진단로그(f"[서식통일] 서식 요소 분석 실패(무시): {exc}")
    # 괄호 크기 규칙도 문서 관행을 따른다. 괄호를 본문보다 작게 쓰는 문서만 그 차이를 적용하고,
    # 본문과 같은 크기로 쓰는 문서는 괄호도 본문 크기로 본다. 단, 표준서식이 기준이고 문두 라벨·괄호
    # 단계가 괄호를 줄이면 그 설정값이 기준이다(표준서식 직후 관행은 보통 0pt라 서로 되돌리게 된다).
    괄호설정_기준 = (표준서식_사용 and 작업_모드 in ("format", "all") and 괄호_축소_사용
                   and stage_enabled(선택_세부작업, "parenthesis", 작업_모드))
    if not 고정_프로필_재적용 and 괄호설정_기준:
        서식통일_괄호크기차이 = int(round(float(괄호_축소_pt) * 100))
        로그(f"[서식통일] 괄호 크기 기준: 설정값(본문보다 {괄호_축소_pt:g}pt 작게, 문두 라벨·괄호 서식과 같음)")
    elif not 고정_프로필_재적용:
        차이빈도 = Counter()
        for 항목들 in 그룹별_표본.values():
            for 모양, *_ in 항목들:
                본문크기 = 모양[1]
                if 본문크기 is None or len(모양) < 4 or not isinstance(모양[3], dict):
                    continue
                for _, _, size, 길이 in 모양[3].get("parenthetical_size_runs", ()):
                    차이빈도[int(본문크기) - int(size)] += 1
        서식통일_괄호크기차이 = 차이빈도.most_common(1)[0][0] if 차이빈도 else None
        if 서식통일_괄호크기차이 is not None:
            로그(f"[서식통일] 괄호 크기 관행: 본문보다 {서식통일_괄호크기차이 / 100:g}pt 작게")
    # 프로필은 모든 표본 수집이 끝난 뒤 한 번에 확정한다. 이 구간에는
    # COM 서식 쓰기 호출이 없어 문서의 현재 서식을 조사값으로 보존한다.
    보충표본 = {}
    for 그룹키, 항목들 in 그룹별_표본.items():
        # 본문 표본이 적은 계층만 같은 기호의 제목 표 문장을 함께 본다.
        if len(항목들) < 서식통일_최소문단수:
            보충 = [모양 for _, 키, 모양 in 제목표_표본 if 키 == 그룹키]
            if 보충:
                보충표본[그룹키] = 보충
                로그(f"[서식통일] '{그룹키[0]}' 본문 표본 {len(항목들)}개 — 같은 계층 제목 표 "
                     f"{len(보충)}개를 대표 서식 조사에 참고")
        if 고정_프로필_재적용:
            대표 = _서식통일_문서대표프로필.get(그룹키)
        else:
            대표 = 서식통일_대표([모양 for 모양, *_ in 항목들] + 보충표본.get(그룹키, []))
            _서식통일_문서대표프로필[그룹키] = 대표
    전체수 = Counter()   # 영역을 합친 같은 계층 문장 수(비교 기준이 있는지 판단)
    for 그룹키, 항목들 in 그룹별_표본.items():
        전체수[그룹키[:2]] += len(항목들) + len(보충표본.get(그룹키, []))
    if 경계 and not 고정_프로필_재적용:
        # 영역 안 표본이 부족해 정하지 못한 값은 문서 전체의 같은 계층 대표값을 따른다.
        전체모양 = defaultdict(list)
        for 그룹키, 항목들 in 그룹별_표본.items():
            전체모양[그룹키[:2]].extend([모양 for 모양, *_ in 항목들] + 보충표본.get(그룹키, []))
        전체대표 = {키: 서식통일_대표(모양들) for 키, 모양들 in 전체모양.items()}
        for 그룹키 in 그룹별_표본:
            대표값, 기준 = _서식통일_문서대표프로필.get(그룹키), 전체대표.get(그룹키[:2])
            for 필드, 값 in (기준 or {}).items():
                if 대표값 is not None and 대표값.get(필드, (None, 0))[0] is None and 값[0] is not None:
                    대표값[필드] = 값
    if not 고정_프로필_재적용:
        # 엄격한 다수(60%)에 못 미친 글꼴·크기·색은, 최다값이 문서의 다른 계층도 대표로 쓰는
        # 값이면 채택한다(예: ※ 글꼴이 6:4:2로 갈렸지만 최다 글꼴이 ㅇ 대표 글꼴과 같은 경우).
        # 이웃 기준 ※ 보완보다 먼저 한다: 이웃 표본은 몇 개뿐이라 그룹 안 소수 글꼴이 대표가
        # 될 수 있다(실측: 정책회의 ※ 11개 중 2개만 쓰는 글꼴).
        필드위치 = {"font": lambda 모양: 모양[0], "size": lambda 모양: 모양[1],
                    "color": lambda 모양: 모양[3].get("color") if len(모양) > 3 else None,
                    "shade": lambda 모양: 모양[3].get("shade") if len(모양) > 3 else None}
        어휘 = defaultdict(set)
        for 대표값 in _서식통일_문서대표프로필.values():
            for 필드 in 필드위치:
                값 = (대표값 or {}).get(필드, (None, 0))[0]
                if 값 is not None:
                    어휘[필드].add(값)
        for 그룹키, 항목들 in 그룹별_표본.items():
            대표값 = _서식통일_문서대표프로필.get(그룹키)
            if not 대표값:
                continue
            모양들 = [모양 for 모양, *_ in 항목들] + 보충표본.get(그룹키, [])
            for 필드, 추출 in 필드위치.items():
                if 대표값.get(필드, (None, 0))[0] is not None:
                    continue
                값 = 서식통일_문서어휘_대표([추출(모양) for 모양 in 모양들], 어휘[필드])
                if 값 is not None:
                    대표값[필드] = (값, sum(1 for 모양 in 모양들 if 추출(모양) == 값))
                    로그(f"[서식통일] '{그룹키[0]}' {필드} 대표값 보조 판정: {값} "
                         f"(최다값이 문서의 다른 계층 대표값과 같음)")
        _서식통일_참고표_이웃대표_보완(그룹별_표본, _서식통일_문서대표프로필)
        # 괄호 라벨 굵기는 문서 전체의 관행이다. 그룹 안에 라벨 문장이 적어 기준이 없으면
        # 다른 그룹들의 라벨 굵기 다수값을 따른다(예: ※ 라벨 문장이 하나뿐인 경우).
        라벨관행 = Counter()
        for 대표값 in _서식통일_문서대표프로필.values():
            값, 수 = (대표값 or {}).get("label_bold", (None, 0))
            if 값 is not None:
                라벨관행[값] += 수
        if 라벨관행:
            (관행값, 관행수), *나머지 = 라벨관행.most_common()
            if not 나머지 or 나머지[0][1] < 관행수:
                for 그룹키, 대표값 in _서식통일_문서대표프로필.items():
                    if 대표값 and 대표값.get("label_bold", (None, 0))[0] is None:
                        대표값["label_bold"] = (관행값, 관행수)
                        로그(f"[서식통일] '{그룹키[0]}' 괄호 라벨 굵기는 문서 전체 관행({관행값})을 따름")
    # 문단 위 간격은 앞 문장 기호에 따라 달라지므로(□ 다음 ㅇ, ㅇ 다음 ㅇ 등) 문맥별 대표값을
    # 구하고, 대표값을 가진 실제 문단을 예시로 삼아 그 값을 그대로 복사한다.
    위간격모음 = defaultdict(list)
    for 그룹키, 항목들 in 그룹별_표본.items():
        for 모양, 시작, 끝, text in 항목들:
            위간격모음[(그룹키, 문맥.get(tuple(시작)))].append((모양[3].get("prev_spacing"), 시작))
    위간격대표 = {}
    for key, pairs in 위간격모음.items():
        값, _, _ = 서식통일_최빈값([v for v, _ in pairs if v is not None],
                               minimum=max(2, min(서식통일_최소문단수, len(pairs))),
                               ratio=서식통일_최소비율)
        if 값 is not None:
            위간격대표[key] = (값, next(pos for v, pos in pairs if v == 값))
    로그("[서식통일] 2/5 문서 전체 표본으로 대표값 확정 완료(읽기 전용)")

    # 실제 적용 전에 추정 대표값을 사용자가 확인·수정한다. 특히 ※ 표본이
    # 동률/소수라 대표값이 없을 때는 * 계열과 함께 화면에 제시하고 사용자가
    # 선택하거나 직접 값을 입력해야 보정 계획에 반영된다.
    if not 검증만 and not 고정_프로필_재적용:
        로그("[서식통일] 2/5 조사된 대표 서식 확인")
        if not _서식통일_대표값_사용자검토(그룹별_표본):
            로그("[서식통일] 사용자가 대표 서식 검토를 취소하여 문서 수정 전 작업 중단")
            return False

    계획 = []
    for 그룹키, 항목들 in 그룹별_표본.items():
        marker, role, level = 그룹키
        if 고정_프로필_재적용:
            대표 = _서식통일_문서대표프로필.get(그룹키)
            if 대표 is None:
                로그(f"[서식통일] '{marker}/{role}' 후속 단계에서 새로 생긴 그룹은 "
                     "최초 표본이 없어 안전을 위해 건너뜀")
                continue
        else:
            대표 = _서식통일_문서대표프로필.get(그룹키)
        if 전체수[그룹키[:2]] < 2:
            # 같은 계층 문장이 하나뿐이면 '다른 문장'을 가릴 기준이 없다. 고치거나 표시하지 않는다.
            진단로그(f"[서식통일] '{marker}/{role}' 문장이 하나뿐이라 비교 대상이 없어 건너뜀: "
                     f"{항목들[0][3].strip()[:60]}")
            continue
        글꼴, 글꼴수 = 대표["font"]
        크기, 크기수 = 대표["size"]
        색표준 = 대표.get("color", (None, 0))[0]
        음영표준 = 대표.get("shade", (None, 0))[0]
        문두굵게, 문두굵게수 = 대표["marker_bold"]
        라벨굵게, 라벨굵게수 = 대표["label_bold"]
        내어쓰기표준, 내어쓰기수 = 대표.get("hanging_indent", (None, 0))
        if 최종_내어쓰기_예정 and not 검증만:
            # 뒤의 '최종 서식 기준 내어쓰기' 단계가 항목기호 문장의 내어쓰기를 모두 다시 정한다.
            # 여기서 대표값대로 넣거나 빼면 그 단계가 곧바로 덮으므로 비교하지 않는다.
            내어쓰기표준 = None
        그룹미판정 = set()
        for 모양, 시작, 끝, text in 항목들:
            # 쪽 범위는 대표값 표본에 적용하지 않고 실제 수정 단계에서만 적용한다.
            if not 쪽범위_안인가(시작):
                continue
            # 한/글 텍스트는 문장을 다시 찾는 열쇠로만 쓰고, 기호·위치 판정은 원문으로 한다.
            원문 = 위치텍스트.get(tuple(시작), text)
            미판정필드 = _서식통일_미확정_항목(대표, 원문)
            그룹미판정.update(미판정필드)
            if 미판정필드:
                미확정문단.append({"text": text.strip()[:100], "fields": 미판정필드,
                                   "start": 시작, "marker": marker,
                                   "red_marked": bool(모양[3].get("red_marked", False))})
            글꼴불일치구간 = _서식통일_불일치_구간(모양, 시작, 끝, 글꼴, None)
            크기불일치구간 = _서식통일_불일치_구간(모양, 시작, 끝, None, 크기)
            불일치구간 = 서식통일_범위병합(글꼴불일치구간 + 크기불일치구간)
            문두굵기구간 = _서식통일_굵기_불일치_구간(모양, "marker", 문두굵게)
            라벨굵기구간 = _서식통일_굵기_불일치_구간(모양, "label", 라벨굵게)
            괄호크기구간, 괄호목표크기 = _서식통일_부연괄호_불일치_구간(모양, 크기)
            paragraph_offset = 문단_내어쓰기_기준_오프셋(원문)
            문단시작 = 시작
            부가 = 모양[3] if len(모양) > 3 and isinstance(모양[3], dict) else {}
            # 내어쓰기 상태는 조사한 HWPX 문단 모양에 이미 있다. 문장마다 한/글에 다시 묻지 않는다.
            if paragraph_offset is None or paragraph_offset <= 0:
                현재내어쓰기 = None
            elif "hanging_indent" in 부가:
                현재내어쓰기 = bool(부가["hanging_indent"])
            else:
                현재내어쓰기 = _서식통일_내어쓰기_상태(문단시작, 원문)
            # 기준 미정 문단은 내어쓰기를 일부러 건너뛰고 빨간 표시로 보고하므로 불일치로 세지 않는다.
            # 한 줄 문장은 내어쓰기가 보이지 않으므로 비교하지 않는다(서식을 고친 뒤 줄이 늘면
            # 마무리 단계가 대표값대로 내어쓴다).
            내어쓰기_불일치 = (내어쓰기표준 is not None and 현재내어쓰기 is not None
                               and 부가.get("line_count", 2) > 1
                               and 내어쓰기표준 != 현재내어쓰기 and not 미판정필드)
            장평표준 = 대표.get("ratio", (None, 0))[0]
            장평_불일치 = 장평표준 is not None and 부가.get("ratio") not in (None, 장평표준)
            위간격 = 위간격대표.get((그룹키, 문맥.get(tuple(시작))))
            위간격_불일치 = 위간격 is not None and 부가.get("prev_spacing") != 위간격[0]
            # 글자색·음영: 문장 값이 대표값과 다르면 그 값을 쓴 구간만 대표값으로 바꾼다
            # (다른 색으로 강조한 낱말은 그대로 둔다). 대표값 미확정 문장은 빨간 표시가 우선이다.
            색구간, 음영구간 = [], []
            if not 미판정필드:
                문장색 = 부가.get("color")
                if 색표준 is not None and 문장색 not in (None, 색표준):
                    색구간 = list(서식통일_범위병합(
                        (run[0], run[1]) for run in 부가.get("color_runs", ()) if run[2] == 문장색))
                문장음영 = 부가.get("shade")
                if 음영표준 is not None and 문장음영 not in (None, 음영표준):
                    음영구간 = list(서식통일_범위병합(
                        (run[0], run[1]) for run in 부가.get("shade_runs", ()) if run[2] == 문장음영))
            # 기울임·밑줄·취소선: 글자색과 같이 문장 대부분의 값이 대표값과 다를 때 그 값을 쓴 구간만 고친다.
            # 밑줄·취소선을 새로 넣을 때는 대표값을 쓴 다른 문장의 선 모양·색을 그대로 복사한다.
            글자구간, 글자예시 = {}, {}
            if not 미판정필드:
                for 필드 in ("italic", "underline", "strike"):
                    표준 = 대표.get(필드, (None, 0))[0]
                    문장값 = 부가.get(필드)
                    if 표준 is None or 문장값 in (None, 표준):
                        continue
                    글자구간[필드] = list(서식통일_범위병합(
                        (run[0], run[1]) for run in 부가.get(f"{필드}_runs", ()) if run[2] == 문장값))
                    if 필드 != "italic" and 표준 not in ("NONE", False):
                        글자예시[필드] = next(((run[0], run[1]) for 예시모양, *_ in 항목들
                                               for run in (예시모양[3].get(f"{필드}_runs", ())
                                                           if len(예시모양) > 3 else ())
                                               if run[2] == 표준), None)
                        if 글자예시[필드] is None:
                            글자구간.pop(필드)
            # 정렬·좌우 여백: 대표값을 가진 같은 계층 문장의 값을 그대로 복사한다(단위 변환 없음).
            # 왼쪽 여백은 기호 앞 빈칸 수가 대표값과 같고 내어쓰기를 따로 맞추지 않는 문장만 고친다.
            정렬표준 = 대표.get("align", (None, 0))[0]
            왼쪽표준 = 대표.get("left", (None, 0))[0]
            오른쪽표준 = 대표.get("right", (None, 0))[0]
            빈칸표준 = 대표.get("lead", (None, 0))[0]
            정렬_불일치 = 정렬표준 is not None and 부가.get("align") not in (None, 정렬표준)
            왼쪽_불일치 = (왼쪽표준 is not None and 부가.get("left_margin") not in (None, 왼쪽표준)
                          and 빈칸표준 is not None and 부가.get("lead_spaces") == 빈칸표준
                          and not 내어쓰기_불일치)
            오른쪽_불일치 = 오른쪽표준 is not None and 부가.get("right_margin") not in (None, 오른쪽표준)
            문단모양_예시 = {}
            for 종류, 불일치, 필드, 표준 in (("align", 정렬_불일치, "align", 정렬표준),
                                         ("left", 왼쪽_불일치, "left_margin", 왼쪽표준),
                                         ("right", 오른쪽_불일치, "right_margin", 오른쪽표준)):
                if not 불일치:
                    continue
                예시위치 = next((예시시작 for 예시모양, 예시시작, *_ in 항목들
                                 if len(예시모양) > 3 and 예시모양[3].get(필드) == 표준
                                 and (종류 != "left" or 예시모양[3].get("lead_spaces") == 빈칸표준)), None)
                if 예시위치 is not None:
                    문단모양_예시[종류] = 예시위치
            if 위간격_불일치:
                문단모양_예시["prev"] = 위간격[1]
            if 내어쓰기_불일치 and 내어쓰기표준:
                # 한 줄짜리 문장은 실측 내어쓰기가 되지 않으므로, 같은 그룹에서 라벨(본문 앞부분)이
                # 같고 내어쓰기가 된 문장의 들여쓰기 값을 예시로 복사한다.
                앞부분 = 원문.lstrip()[:max(0, paragraph_offset - (len(원문) - len(원문.lstrip())))]
                for 예시모양, 예시시작, _, 예시text in 항목들:
                    예시text = 위치텍스트.get(tuple(예시시작), 예시text)
                    예시offset = 문단_내어쓰기_기준_오프셋(예시text)
                    if (예시시작 != 시작 and 예시offset is not None
                            and 예시모양[3].get("hanging_indent")
                            and 예시text.lstrip()[:max(0, 예시offset - (len(예시text) - len(예시text.lstrip())))] == 앞부분):
                        문단모양_예시["indent"] = 예시시작
                        break
            현재불일치 = (불일치구간 or 문두굵기구간 or 라벨굵기구간
                        or 괄호크기구간 or 내어쓰기_불일치 or 장평_불일치 or 문단모양_예시
                        or 색구간 or 음영구간 or 글자구간)
            item_plan = {"marker": marker, "role": role, "level": level,
                         "shape": 모양, "start": 문단시작, "end": 끝, "text": text,
                         "position_text": 원문,
                         "color": 색표준, "color_runs": 색구간,
                         "shade": 음영표준, "shade_runs": 음영구간,
                         "unresolved_fields": 미판정필드,
                         "font": 글꼴, "size": 크기,
                         "font_runs": 글꼴불일치구간, "size_runs": 크기불일치구간,
                         "aside_runs": 괄호크기구간, "aside_size": 괄호목표크기,
                         "marker_bold_runs": 문두굵기구간, "marker_bold": 문두굵게,
                         "label_bold_runs": 라벨굵기구간, "label_bold": 라벨굵게,
                         "hanging_mismatch": 내어쓰기_불일치,
                         "ratio_fix": 장평표준 if 장평_불일치 else None,
                         "char_runs": 글자구간, "char_examples": 글자예시,
                         "char_values": {필드: 대표.get(필드, (None, 0))[0] for 필드 in 글자구간},
                         "para_examples": 문단모양_예시,
                         "expected_hanging": 내어쓰기표준,
                         "mismatch": bool(현재불일치)}
            계획.append(item_plan)
            if 검증만:
                확인문단수 += 1
                if 현재불일치:
                    항목 = {"text": text.strip()[:100], "fields": [], "expected_actual": {}}
                    if 글꼴불일치구간:
                        항목["fields"].append("font")
                        항목["expected_actual"]["font"] = {
                            "expected": 글꼴,
                            "actual": sorted({run[2][0] for run in (모양[2] if len(모양) > 2 else ())
                                              if run[2][0] is not None}),
                        }
                    if 크기불일치구간:
                        항목["fields"].append("size")
                        항목["expected_actual"]["size"] = {
                            "expected": 크기,
                            "actual": sorted({run[2][1] for run in (모양[2] if len(모양) > 2 else ())
                                              if run[2][1] is not None}),
                        }
                    if 괄호크기구간:
                        항목["fields"].append("parenthetical_size")
                        항목["expected_actual"]["parenthetical_size"] = {
                            "expected": 괄호목표크기,
                            "actual": sorted({run[2] for run in 모양[3].get("parenthetical_size_runs", ())}),
                        }
                    if 문두굵기구간:
                        항목["fields"].append("marker_bold")
                    if 라벨굵기구간:
                        항목["fields"].append("label_bold")
                    if 장평_불일치:
                        항목["fields"].append("ratio")
                    if 색구간:
                        항목["fields"].append("color")
                        항목["expected_actual"]["color"] = {"expected": 색표준, "actual": 부가.get("color")}
                    if 음영구간:
                        항목["fields"].append("shade")
                        항목["expected_actual"]["shade"] = {"expected": 음영표준, "actual": 부가.get("shade")}
                    if 위간격_불일치:
                        항목["fields"].append("prev_spacing")
                    for 필드 in 글자구간:
                        항목["fields"].append(필드)
                        항목["expected_actual"][필드] = {"expected": 대표.get(필드, (None, 0))[0],
                                                       "actual": 부가.get(필드)}
                    for 종류, 필드, 불일치 in (("align", "align", 정렬_불일치),
                                             ("left_margin", "left_margin", 왼쪽_불일치),
                                             ("right_margin", "right_margin", 오른쪽_불일치)):
                        if 불일치:
                            항목["fields"].append(종류)
                            항목["expected_actual"][종류] = {
                                "expected": {"align": 정렬표준, "left_margin": 왼쪽표준,
                                             "right_margin": 오른쪽표준}[종류],
                                "actual": 부가.get(필드)}
                    if 내어쓰기_불일치:
                        항목["fields"].append("hanging_indent")
                        항목["expected_actual"]["hanging_indent"] = {
                            "expected": 내어쓰기표준, "actual": 현재내어쓰기,
                        }
                    불일치목록.append(항목)
        if 그룹미판정:
            판정불가그룹.append({"marker": marker, "role": role,
                                 "samples": len(항목들), "fields": sorted(그룹미판정)})
        글꼴표시 = f"{글꼴} ({글꼴수})" if 글꼴 is not None else "판정 보류"
        크기표시 = f"{크기 / 100:g}pt ({크기수})" if 크기 is not None else "판정 보류"
        진단로그(f"[서식통일] '{marker}/{role}' 대표값({len(항목들)}문장): 글꼴 {글꼴표시}, "
                 f"크기 {크기표시}, 글자색 {색표준 or '판정 보류'}, 음영 {음영표준 or '판정 보류'}, "
                 f"문두 굵기 {문두굵게}, 괄호라벨 굵기 {라벨굵게}, 내어쓰기 {내어쓰기표준} ({내어쓰기수}), "
                 f"기울임 {대표.get('italic', (None, 0))[0]}, 밑줄 {대표.get('underline', (None, 0))[0]}, "
                 f"취소선 {대표.get('strike', (None, 0))[0]}, 정렬 {대표.get('align', (None, 0))[0]}, "
                 f"왼쪽 여백 {대표.get('left', (None, 0))[0]}(기호 앞 빈칸 {대표.get('lead', (None, 0))[0]}), "
                 f"오른쪽 여백 {대표.get('right', (None, 0))[0]}")
        continue

    후보수 = sum(1 for p in 계획 if p["mismatch"])
    로그(f"[서식통일] 3/5 예외 영역 자동 검출: 수정 후보 {후보수}개 / "
         f"대표값 미확정 {len(미확정문단)}개 — 개별 승인 없이 적용")
    if 검증만:
        for item in (미확정문단 if 서식통일_빨간표시_사용 else ()):
            if not item["red_marked"]:
                불일치목록.append({"text": item["text"], "fields": ["unresolved_red_marking"]})
        if not 확인문단수 and not 판정불가그룹 and not 불일치목록:
            # 검사할 항목기호 문장이 없는 문서(서식·표만 있는 문서)는 '해당 없음'이다. 예전에는 '미완료'로 0점이 되어
            # 서식 통일 판정이 '부분 달성'으로 나왔다(2026-10-04 범정부오피스 서식 9종).
            status = "not_applicable"
        elif not 확인문단수:
            status = "incomplete"
        elif 판정불가그룹 and not 불일치목록 and 서식통일_빨간표시_사용:
            status = "incomplete"
        else:
            status = "failed" if 불일치목록 else "passed"
        _서식통일_최종감사 = {"status": status, "checked": 확인문단수,
                             "issues": 불일치목록, "not_checkable": 판정불가그룹,
                             "unresolved": 미확정문단,
                             "hierarchy": [f"{키[0]}({키[1]})" for 키 in 체계],
                             "systems": ["본문"] + [이름 for _, 이름 in 경계],
                             "cover_excluded": bool(표지문단)}
        로그(f"5/5 저장 결과 서식통일 검수(읽기 전용): {status} / 확인 {확인문단수}개 / "
             f"불일치 {len(불일치목록)}개 / 보류 그룹 {len(판정불가그룹)}개")
        if 불일치목록:
            항목별 = Counter(field for issue in 불일치목록 for field in issue["fields"])
            로그("[서식통일] 불일치 항목별 문장 수: "
                 + ", ".join(f"{field} {count}" for field, count in 항목별.most_common()))
        return _서식통일_최종감사

    # 4단계: 문서 순서로 한 문단의 서식 → 자간 → 내어쓰기를 끝낸다.
    로그("[서식통일] 4/5 문장별 자동 처리: 서식 → 자간 → 내어쓰기")
    if not 고정_프로필_재적용:
        단계표시("서식통일 적용")
    for item in sorted(계획, key=lambda entry: entry["start"]):
        if 중단_요청됨():
            return False
        if not item["mismatch"] and not item["unresolved_fields"]:
            continue
        if item["mismatch"]:
            진단로그(f"[서식통일 문장] 시작 {item['start']}: {item['text'].strip()[:100]}")
            _서식통일_문단서식_적용(item)
            # 기준이 미확정된 문장은 확정된 항목만 고치고 빨간 표시한다.
            # 불완전한 기준으로 자간/내어쓰기를 연쇄 변경하지 않는다.
            if not item["unresolved_fields"]:
                if item["hanging_mismatch"] and not item["expected_hanging"]:
                    _서식통일_문단내어쓰기_적용(item)   # 대표값이 '내어쓰기 없음'이면 여기서 해제
                # 내어쓰기 → 자간 → 외톨이 당기기는 모든 문장의 서식을 맞춘 뒤 한 묶음으로 한다.
                _서식통일_자간보류문단[item["text"].strip()] = item["expected_hanging"]
                _서식통일_위치텍스트_보관[item["text"].strip()] = item["position_text"]
            elif not 서식통일_빨간표시_사용:
                _서식통일_자간보류문단[item["text"].strip()] = item["expected_hanging"]
                _서식통일_위치텍스트_보관[item["text"].strip()] = item["position_text"]
            교정수 += 1
            진단로그(f"[서식통일 문장] 완료 {item['start']}")
        if item["unresolved_fields"] and not 서식통일_빨간표시_사용:
            진단로그(f"[서식통일] 대표값 미확정은 뒤이은 표준 서식이 결정하여 빨간 표시 생략: "
                     f"{item['text'].strip()[:100]}")
        elif item["unresolved_fields"]:
            _서식통일_미확정_빨간표시(item["start"], item["end"])
            진단로그(f"[서식통일] 대표값 미확정 빨간 표시 ({', '.join(item['unresolved_fields'])}): "
                     f"{item['text'].strip()[:100]}")
    로그(f"[서식통일] 4/5 문장별 처리 완료; 미확정 문단 {len(미확정문단)}개 "
         f"{'빨간 표시' if 서식통일_빨간표시_사용 else '표준 서식에 맡김'}, "
         "저장 후 5/5 결과 검수 예정")
    if 서식통일_빨간표시_사용 and not 고정_프로필_재적용:
        # 표준 서식이 뒤따르지 않으면 서식통일이 고친 문장만 지금 자간을 조정한다.
        if 서식통일_보류자간_재조정() is False:
            return False
    로그(f"서식통일 완료 (교정 {교정수}개 문단)")
    return True


서식통일_줄병합_사용 = True   # 짧은 마지막 줄(외톨이 글자) 당기기 사용 여부(작업별로 설정)
# 서식통일이 고친 문장의 자간 조정·외톨이 글자 당기기 사용 여부. 서식 통일 카드의 '자간 정리 제외'를 켜면
# 끈다(내어쓰기는 그대로 맞춘다).
서식통일_자간조정_사용 = True


def 서식통일_자간조정_반영(사용):
    """서식통일이 고친 문장의 자간 조정 사용 여부를 반영하고 반영한 값을 돌려준다."""
    global 서식통일_자간조정_사용
    서식통일_자간조정_사용 = bool(사용)
    return 서식통일_자간조정_사용


def 서식통일_문장_마무리(시작, text, 내어쓰기):
    """한 문장의 마무리 묶음: 내어쓰기 → 자간 → 마지막 줄 외톨이 글자 당기기.

    내어쓰기를 먼저 확정해야 자간 조정 뒤 줄 폭이 다시 바뀌지 않고, 외톨이 글자 당기기는
    자간 조정으로 확정된 줄바꿈을 기준으로 해야 하므로 이 순서로 한 문장씩 끝낸다.
    """
    if 내어쓰기 and 문단_내어쓰기_기준_오프셋(text) is not None:
        문단_내어쓰기_적용(시작, text)
    hwp.SetPos(*시작)
    hwp_run("MoveParaEnd")
    끝 = hwp.GetPos()
    if 서식통일_자간조정_사용 and 끝[:2] == 시작[:2] and 끝[2] > 시작[2]:
        if _서식통일_문단자간_조정(시작, 끝) is False:
            return False
        if 서식통일_줄병합_사용:
            hwp.SetPos(*시작)
            지난 = set()
            while True:
                if 중단_요청됨():
                    return False
                pos = hwp.GetPos()
                if pos[:2] != 시작[:2] or pos in 지난:
                    break
                지난.add(pos)
                문장부호_줄병합_시도()
                hwp_run("MoveLineEnd")
                hwp_run("MoveNextChar")
    hwp.SetPos(*시작)
    return True


def 서식통일_보류자간_재조정():
    """(표준 서식 없음) 서식통일이 고친 문장에 마무리 묶음을 적용한다."""
    if not _서식통일_자간보류문단:
        return True
    대상 = dict(_서식통일_자간보류문단)
    조정수 = 0
    hwp_run("MoveDocBegin")
    while 대상:
        if 중단_요청됨():
            return False
        hwp_run("MoveParaBegin")
        시작 = hwp.GetPos()
        if 시작[0] == 0:
            text = 현재문단_텍스트()
            key = text.strip()
            if key in 대상:
                원문 = _서식통일_위치텍스트_보관.get(key, text)
                if _서식통일_공백제거(원문) != _서식통일_공백제거(text):
                    원문 = text
                if 서식통일_문장_마무리(시작, 원문, bool(대상.pop(key))) is False:
                    return False
                조정수 += 1
        if not 다음_문단으로_진행():
            break
    로그(f"[서식통일] 교정 문장 마무리(내어쓰기→자간→외톨이 당기기): {조정수}개"
         + (f" / 위치를 찾지 못한 문장 {len(대상)}개" if 대상 else ""))
    for text in 대상:
        검수_문제_기록(현재_처리파일, "[서식통일 자간 미조정] 문장 위치를 찾지 못함: " + text[:60])
    return True


def _서식통일_표모형(제외문단=()):
    """HWPX의 표를 표 서식통일 판정용 모형으로 읽는다(읽기 전용).

    한/글의 목록 번호는 문서 순서의 subList(표 칸·머리말·캡션 등) 순번 + 2다(실측: 교육부
    46개, 정책회의 1,179개가 COM 목록 수와 일치). 칸 글자 위치를 확신할 수 없는 문단(칸 안
    표·그림)은 비교에서 뺀다.
    """
    문서경로 = _서식통일_현재_HWPX()
    if 문서경로 is None:
        return []
    from docfit_core.style_inventory import _tag
    분석 = _서식통일_HWPX_분석(문서경로)
    목록번호 = {}
    for 문단 in 분석["paragraphs"]:
        for item in 문단.iter():
            if _tag(item) == "subList":
                목록번호[id(item)] = len(목록번호) + 2
    표들 = []
    for 번호, 문단 in enumerate(분석["paragraphs"]):
        if 번호 in 제외문단:
            continue
        for 표 in (item for item in 문단.iter() if _tag(item) == "tbl"):
            칸들 = []
            for tc in (item for tr in 표 if _tag(tr) == "tr" for item in tr if _tag(item) == "tc"):
                sub = next((item for item in tc if _tag(item) == "subList"), None)
                주소 = next((item for item in tc if _tag(item) == "cellAddr"), None)
                if sub is None or id(sub) not in 목록번호:
                    continue
                문단들 = []
                for 칸문단번호, p in enumerate(item for item in sub if _tag(item) == "p"):
                    조각 = [(run, *_서식통일_run_text(run)) for run in p if _tag(run) == "run"]
                    글자 = "".join(text for _, text, _ in 조각)
                    runs = []
                    if all(확실 for _, _, 확실 in 조각):
                        cursor = 0
                        for run, text, _ in 조각:
                            길이 = len(text.encode("utf-16-le")) // 2
                            char = 분석["chars"].get(run.get("charPrIDRef"))
                            if char and text.strip():
                                runs.append((cursor, cursor + 길이, char["font"].get("hangul"),
                                             round(char["size_pt"] * 100),
                                             str(char.get("color", "")).upper(), bool(char.get("bold"))))
                            cursor += 길이
                    문단들.append({"index": 칸문단번호, "text": 글자, "runs": runs})
                칸들.append({"area": 목록번호[id(sub)],
                             "header": 주소 is not None and 주소.get("rowAddr") == "0",
                             "fill": tc.get("borderFillIDRef"), "paras": 문단들})
            첫글자 = next((para["text"] for 칸 in 칸들 for para in 칸["paras"] if para["text"].strip()), "")
            표들.append({"index": len(표들), "cells": 칸들,
                         "box": 표.get("rowCnt") == "1" and 표.get("colCnt") == "1",
                         "marker": 서식통일_항목기호(첫글자)[0]})
    return 표들


def 서식통일_표_전체_적용(검증만=False):
    """같은 종류(같은 모양 칸·같은 기호 제목 상자)의 표끼리 글자 서식을 맞춘다.

    판정은 docfit_core.table_unify가 HWPX만 보고 하며, 한/글에서는 고칠 칸 문단의 글자가
    HWPX와 같은지 확인한 뒤 그 구간만 바꾼다. 검증만=True면 읽기 전용으로 남은 불일치를 센다.
    """
    from docfit_core.table_unify import plan_table_fixes
    if 중단_요청됨():
        return False
    if not 검증만:
        단계표시("표 서식통일")
    표들 = _서식통일_표모형()
    고칠것, 요약 = plan_table_fixes(표들)
    검사표수 = len(표들)
    if 쪽범위_사용중():
        # 대표값은 문서 전체에서 얻되 수정·검수 대상은 선택한 쪽의 칸으로 제한한다.
        고칠것 = [fix for fix in 고칠것
                 if 쪽범위_안인가((fix['area'], fix['para'], fix['start']))]
        검사표수 = sum(any(쪽범위_안인가((칸['area'], 0, 0)) for 칸 in 표['cells'])
                     for 표 in 표들)
    if 검증만:
        issues = [{"text": fix["text"].strip()[:100], "fields": [f"table_{fix['field']}"],
                   "expected_actual": {fix["field"]: {"expected": fix["value"], "actual": fix["was"]}}}
                  for fix in 고칠것]
        status = "failed" if issues else "passed"
        로그(f"[표 서식통일] 저장 결과 검수(읽기 전용): {status} / 표 {검사표수}개 / 불일치 구간 {len(issues)}개")
        return {"status": status, "checked": 검사표수, "issues": issues}
    로그(f"[표 서식통일] 표 {len(표들)}개 조사 — 고칠 구간 {len(고칠것)}개 "
         + (", ".join(f"{이름} {수}" for 이름, 수 in 요약.items()) or "(없음)"))
    적용, 건너뜀 = 0, 0
    확인됨 = {}
    for fix in sorted(고칠것, key=lambda item: (item["area"], item["para"], item["start"])):
        if 중단_요청됨():
            return False
        문단키 = (fix["area"], fix["para"])
        if 문단키 not in 확인됨:
            # 목록 번호가 어긋나면 다른 칸을 고치게 되므로, 칸 문단 글자가 HWPX와 같은지 확인한다.
            try:
                hwp.SetPos(fix["area"], fix["para"], 0)
                같은칸 = (tuple(hwp.GetPos()[:2]) == 문단키
                          and _서식통일_공백제거(현재문단_텍스트()) == _서식통일_공백제거(fix["text"]))
            except Exception:
                같은칸 = False
            확인됨[문단키] = 같은칸
            if not 같은칸:
                진단로그(f"[표 서식통일] 칸 위치를 확인하지 못해 건너뜀: {fix['text'].strip()[:40]}")
        if not 확인됨[문단키]:
            건너뜀 += 1
            continue
        시작 = (fix["area"], fix["para"], fix["start"])
        끝 = (fix["area"], fix["para"], fix["end"])
        try:
            단어모드_범위선택(시작, 끝)
            # 항목별로 따로 분기한다(사전 리터럴은 값을 모두 계산해 글꼴 이름 / 100에서 멈춤).
            if fix["field"] == "color":
                _서식통일_색_적용("TextColor", fix["value"])
            elif fix["field"] == "font":
                문자모양_적용_현재선택(폰트=fix["value"], 자간_유지=True)
            elif fix["field"] == "size":
                문자모양_적용_현재선택(크기_pt=fix["value"] / 100, 자간_유지=True)
            else:
                문자모양_적용_현재선택(굵게=fix["value"], 자간_유지=True)
            적용 += 1
            진단로그(f"[표 서식통일] {fix['reason']}: {fix['field']} {fix['was']} → {fix['value']} "
                     f"'{fix['text'].strip()[:30]}'")
        finally:
            hwp_run("Cancel")
    hwp_run("MoveDocBegin")
    로그(f"[표 서식통일] 완료: {적용}개 구간 수정"
         + (f", 칸 위치 확인 실패로 {건너뜀}개 건너뜀" if 건너뜀 else ""))
    return True


def 표준서식_전체_적용():
    if 중단_요청됨():
        return False
    _표준서식_문단위간격_상태.reset()
    로그("표준서식적용 시작")
    if 표준서식_여백_사용:
        if 쪽범위_사용중():
            로그("쪽 범위 지정: 편집 여백은 구역 전체에 적용되는 설정이라 이번 작업에서는 건드리지 않습니다.")
        else:
            페이지_여백_설정(표준서식_설정["여백_mm"])
            용지_다르면_알림()

    if not 항목기호문장_사이_빈줄_삭제():
        return False

    # 표 첫 칸에 로마자 숫자가 있는 중제목 표 문단(글 없음)도 3단계 중제목 문단 위 여백을 받는다.
    표문단 = 본문_표_문단번호() if 표준서식_문단위간격_사용 and not 표준서식_설정.get("복제_들여쓰기_유지") else {}
    _표칸영역.clear()
    hwp_run("MoveDocBegin")
    문단_순번 = 0
    구조_시작됨 = False
    _간격규칙_상태.update(첫문장=False, 직전깊이=None)
    상단_비기호_문단수 = 0
    활성_세트_들여쓰기 = None
    활성_세트_기호규칙 = None

    while True:
        if 중단_요청됨():
            return False
        if 쪽범위_끝지남():
            break

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

        위치 = hwp.GetPos()
        if (not (text and text.strip()) and 위치[0] == 0 and 위치[1] in 표문단
                and 로마자_중제목_표인가(표문단[위치[1]])):
            간격_pt = 표준서식_문단위간격_찾기("", 계층="midtitle")
            if 쪽범위_안인가() and 간격_pt is not None:
                hwp.SetPos(0, 위치[1], 0)
                hwp_run("MoveParaBegin")
                hwp_run("MoveSelParaEnd")
                문단_위간격_적용_현재선택(간격_pt)
                hwp_run("Cancel")
                hwp.SetPos(*위치)
        # 제목·일자 판정 등 문맥은 문서 처음부터 읽어 이어 가되, 서식은 쪽 범위 안 문단에만 적용한다.
        if 쪽범위_안인가():
            표준서식_문단_처리(
                문단_순번,
                헤더_역할=헤더_역할,
                상속_기호_매칭=상속_기호_매칭,
            )
        if not 다음_문단으로_진행():
            break

    if not 항목기호문장_사이_빈줄_삭제(붙임_빈줄_넣기=True):
        return False
    로그("표준서식적용 완료")
    return True

# ============================================================
# 괄호 및 문두 라벨 처리 (콜론 라벨 굵게 + 괄호 라벨 굵게 + 부연설명 축소)
# ============================================================

괄호_축소_사용 = True
괄호_축소_pt = 2
괄호_라벨_볼드_사용 = True

# 문장 중간의 대괄호('[세부일정 붙임1]')도 소괄호와 같은 부연설명으로 보고 축소한다.
괄호_정규식 = re.compile(r"\(([^()]+)\)|\[([^\[\]]+)\]")


def 괄호_안쪽(match):
    return match.group(1) if match.group(1) is not None else match.group(2)


def 대괄호인가(match):
    return match.group(0).startswith("[")
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
    return bool(괄호_범위라벨_정규식.fullmatch(괄호_안쪽(match)))

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

def 괄호_축소량_pt(text):
    """이 문단의 괄호 안 글자를 줄일 크기(pt). 서식 예시가 계층마다 정한 값이 있으면 그 값(0이면 줄이지 않음)."""
    기호별 = (표준서식_설정 or {}).get("괄호_축소_기호별") or {}
    if 기호별:
        기호 = 서식통일_항목기호(text)[0]
        if 기호 in 기호별:
            return float(기호별[기호] or 0)
    return float(괄호_축소_pt)


def 괄호_텍스트_크기_축소_현재선택(축소_pt=None):
    if hwp is None:
        return
    try:
        기존_pt = hwp.CharShape.Item("Height") / 100.0
        if 기존_pt:
            새_pt = max(1, 기존_pt - (괄호_축소_pt if 축소_pt is None else 축소_pt))
            문자모양_적용_현재선택(크기_pt=새_pt)
    except Exception as e:
        로그(f"괄호 텍스트 크기 축소 실패(무시): {e}")

def 문두_라벨_굵게_제외_문단인가(text):
    text = (text or '').lstrip()
    symbol = '**' if text.startswith('**') else (text[:1] or '기타')
    if symbol not in 문두라벨_기호설정:
        symbol = '기타'
    return not 문두라벨_기호설정.get(symbol, True)


# 항목기호별 굵게 일관성 규칙:
# 같은 항목기호를 쓰는 문단 중 하나라도 문두 라벨('- 추진부서 : …'의
# '추진부서', '- (운영방식) …'의 '(운영방식)')이 굵게 처리되면, 그 기호를
# 쓰는 다른 문단의 머리말('- 조례제정 (무료 셔틀버스 …)'의 '조례제정')도
# 굵게 맞춘다. 부연·보조 설명 괄호는 굵게 하지 않는다. 머리말 없이 일반
# 문장으로 이어지는 문단은 문장 전체가 굵어지므로 대상에서 뺀다.
_일관성_머리말_최대글자수 = 15
항목기호_굵게_일관성_사용 = True  # 설정 > 서식 정리 > 항목 이름 강조에서 켜고 끔
_일관성_굵게_적용기호 = set()


def 항목기호_키(text):
    """항목기호별 설정·일관성 규칙에서 쓰는 기호 키('**', '-', 'ㅇ' 등)."""
    text = (text or '').lstrip()
    return '**' if text.startswith('**') else (text[:1] or '기타')


def 일관성_굵게_머리말_범위(text):
    """'- 조례제정 (설명)'에서 굵게 맞출 머리말 '조례제정'의 [시작, 끝) 위치.

    항목기호 바로 뒤의 짧은 머리말 다음에 부연설명 괄호가 이어지는 문단만
    대상으로 한다. 콜론 라벨·괄호 라벨 문단(기존 규칙이 처리), 머리말이
    길거나 쉼표·마침표가 있는 일반 문장은 None.
    """
    if not text or not 문장부호_시작인가(text):
        return None
    마커_끝 = 문장부호_마커_끝위치(text)
    if 마커_끝 is None:
        return None
    idx = 마커_끝
    while idx < len(text) and text[idx] in (" ", "\t"):
        idx += 1
    나머지 = text[idx:].rstrip("\r\n")
    if not 나머지 or 나머지[0] in "(（" or re.match(r"^[^\n\r:：]{1,25}?[ \t]*[:：][ \t]+\S", 나머지):
        return None
    m = re.match(r"^([^()（）:：,，.。\r\n]+?)[ \t]*[(（][^()（）]{3,}[)）]", 나머지)
    if not m:
        return None
    머리말 = m.group(1).strip()
    if not 머리말 or len(머리말) > _일관성_머리말_최대글자수 or not any(c.isalpha() for c in 머리말):
        return None
    시작 = idx + 나머지.find(머리말)
    return 시작, 시작 + len(머리말)

def 문두_라벨_굵게_선반영(문단_시작위치, text):
    """Shift+Tab 내어쓰기 계산 직전, 오프셋에 포함되는 문두 라벨(콜론 라벨
    또는 괄호 라벨)을 미리 굵게 처리해 첫 줄의 실제 폭을 확정한다.

    v1.12 버그수정: 기존에는 표준서식적용(Shift+Tab 내어쓰기 포함) 단계가
    끝난 뒤에야 별도 단계(괄호_텍스트_크기_축소_전체_적용)에서 '(개요)',
    '추진부서 :' 같은 문두 라벨을 굵게 처리했다. Shift+Tab
    (ParagraphShapeIndentAtCaret)은 실행 시점의 커서 '화면 X좌표'를 그대로
    둘째 줄 내어쓰기 값으로 굳히는데, 라벨이 굵어지지 않은 상태로 그 좌표를
    캡처한 뒤 나중에 라벨이 굵어져 첫 줄 폭이 늘어나면, 이미 확정된 내어쓰기
    값은 따라서 넓어지지 않아 첫 줄 본문 시작 글자와 둘째 줄 내어쓰기 위치가
    어긋난다(예: 'ㅇ (개요) 특정 사업에...' 문단에서 '특'과 다음 줄
    '통'의 위치가 달라지는 현상). 이 함수가 미리 굵게 처리를 해서 Shift+Tab이
    이미 최종 폭을 기준으로 커서 좌표를 캡처하게 만든다.

    표준서식_문단_처리는 자체 기호(□/ㅇ/-/※)로 시작하는 문단만 대상으로
    하므로(세트 후속 상속 문단은 이 함수에 도달하지 않는다) 세트 후속 여부는
    고려하지 않는다. 이후 전체 문서 패스인 괄호_및_라벨_텍스트_문단_처리가
    동일 라벨을 다시 굵게 처리하지만, 이미 굵은 텍스트에 굵게를 한 번 더
    적용하는 것뿐이라 결과에 영향이 없다(멱등).
    """
    if not 괄호_라벨_볼드_사용 or not text or hwp is None:
        return
    # □ 문단은 문두 라벨 굵게 제외.
    if 문두_라벨_굵게_제외_문단인가(text):
        return
    try:
        if not 문장부호_시작인가(text):
            return
        마커_끝 = 문장부호_마커_끝위치(text)
        if 마커_끝 is None:
            return

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
                    문단_범위_선택(문단_시작위치, 라벨_시작, 라벨_끝)
                    문자모양_적용_현재선택(굵게=True)
                    hwp_run("Cancel")
                    return

        if "(" in text:
            for match in 괄호_정규식.finditer(text):
                if 대괄호인가(match):
                    continue
                if 괄호_문두_라벨인가(text, match):
                    문단_범위_선택(문단_시작위치, match.start(), match.end())
                    문자모양_적용_현재선택(굵게=True)
                    hwp_run("Cancel")
                    return
    except Exception as e:
        로그(f"문두 라벨 선반영 굵게 실패(무시): {e}")

def 괄호_및_라벨_텍스트_문단_처리(세트후속문단=False):
    """
    현재 문단에 대해:
    1) 문두 라벨(콜론 앞 텍스트 or 괄호 라벨) 굵게 처리
    2) 문장 중간·끝의 부연설명 괄호 크기 2pt 축소

    주의: 이 함수는 한 칸 표(제목 박스·요지 박스 등) 안의 문단에도 적용된다.
    한 칸 표 보호(현재_한칸표인가)는 표 헤더/본문 서식적용처럼 "행 역할"에
    의존하는 로직에만 의미가 있고, 괄호 축소·라벨 굵게는 문단 텍스트 패턴만
    보므로 한 칸 표라고 해서 건너뛸 이유가 없다. 이 가드가 있으면 요지 박스처럼
    한 칸 표로 만들어진 본문성 문단의 부연설명 괄호가 전혀 축소되지 않는다.
    """
    text = 현재문단_텍스트()
    if not text:
        return 0

    # 서식 예시가 이 계층의 괄호를 줄이지 않았으면(0pt) 줄이지 않는다.
    축소_pt = 괄호_축소량_pt(text)
    축소_사용 = 괄호_축소_사용 and 축소_pt > 0
    if not 괄호_라벨_볼드_사용 and (not 축소_사용 or ("(" not in text and "[" not in text)):
        return 0

    문단_시작위치 = hwp.GetPos()
    적용_횟수 = 0

    # --------------------------------------------------------
    # 1. 문두 콜론 라벨 굵게 ("- 추진부서 : 내용", "ㅇ (추진부서) : 내용")
    # --------------------------------------------------------
    if 괄호_라벨_볼드_사용 and 문장부호_시작인가(text) and not 문두_라벨_굵게_제외_문단인가(text):
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
                            _일관성_굵게_적용기호.add(항목기호_키(text))
                            진단로그(f"[문두라벨굵게] '{라벨_텍스트}' 굵게 적용")
                        except Exception as e:
                            로그(f"문두 라벨 굵게 적용 중 오류(무시): {e}")

    # --------------------------------------------------------
    # 2. 괄호 처리 (문두 라벨 괄호 굵게 / 본문 부연설명 괄호 축소)
    # --------------------------------------------------------
    if "(" in text or "[" in text:
        for match in 괄호_정규식.finditer(text):
            앞부분 = text[:match.start()]
            시작_offset = match.start()
            끝_offset = match.end()

            if 대괄호인가(match) and 괄호_문두_라벨인가(text, match):
                continue
            범위_세트라벨 = 세트후속_범위괄호_라벨인가(
                text, match, 세트후속문단=세트후속문단
            )
            if 괄호_문두_라벨인가(text, match) or 범위_세트라벨:
                if 범위_세트라벨:
                    진단로그(f"[세트후속라벨] '{match.group(0)}' 괄호 2pt 축소 제외")
                # □ 문단의 문두 라벨 괄호는 굵게 제외 — 라벨이므로 축소도 하지
                # 않고 원형 그대로 둔다.
                if 괄호_문두_라벨인가(text, match) and 문두_라벨_굵게_제외_문단인가(text):
                    진단로그(f"[문두라벨굵게제외] □ 문단 '{match.group(0)}' 굵게 미적용")
                    continue
                if not 괄호_라벨_볼드_사용:
                    continue
                try:
                    문단_범위_선택(문단_시작위치, 시작_offset, 끝_offset)
                    문자모양_적용_현재선택(굵게=True)
                    hwp_run("Cancel")
                    적용_횟수 += 1
                    if 괄호_문두_라벨인가(text, match):
                        _일관성_굵게_적용기호.add(항목기호_키(text))
                    진단로그(f"[괄호굵게] '{match.group(0)}' 굵게 적용")
                except Exception as e:
                    로그(f"괄호 라벨 굵게 적용 중 오류(무시): {e}")
                continue

            if not 축소_사용:
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
                괄호_텍스트_크기_축소_현재선택(축소_pt)
                hwp_run("Cancel")
                적용_횟수 += 1
                진단로그(f"[괄호축소] '{match.group(0)}' 글자 크기 {축소_pt:g}pt 축소")
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
    순회_시작()
    총_적용_횟수 = 0
    활성_세트_들여쓰기 = None
    _일관성_굵게_적용기호.clear()
    일관성_후보 = []

    while True:
        if 중단_요청됨():
            return False

        text = 현재문단_텍스트()
        세트후속문단 = False
        if (괄호_라벨_볼드_사용 and 항목기호_굵게_일관성_사용
                and not 문두_라벨_굵게_제외_문단인가(text)):
            범위 = 일관성_굵게_머리말_범위(text)
            if 범위:
                일관성_후보.append((hwp.GetPos(), text, 범위))

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
        if not 범위_다음_문단으로_진행():
            break

    # 문서 전체를 본 뒤에야 어떤 항목기호에 라벨 굵게가 적용됐는지 알 수 있다.
    일관성_적용 = 0
    for 위치, text, (시작, 끝) in 일관성_후보:
        if 중단_요청됨():
            return False
        if 항목기호_키(text) not in _일관성_굵게_적용기호:
            continue
        try:
            문단_범위_선택(위치, 시작, 끝)
            문자모양_적용_현재선택(굵게=True)
            hwp_run("Cancel")
            일관성_적용 += 1
            진단로그(f"[항목기호 굵게 일관성] '{text[시작:끝]}' 굵게 적용 "
                     f"('{항목기호_키(text)}' 기호 라벨 굵게와 통일, 괄호 설명 제외)")
        except Exception as e:
            로그(f"항목기호 굵게 일관성 적용 중 오류(무시): {e}")
    총_적용_횟수 += 일관성_적용

    로그(f"문두 라벨 / 괄호 처리 완료 (총 {총_적용_횟수}건, 항목기호 굵게 일관성 {일관성_적용}건)")
    return True

# ============================================================
# 자간조정 및 단어 분리 방지 알고리즘
# ============================================================

def 현재_페이지번호():
    """캐럿이 있는 쪽의 실제 순서(1부터). 인쇄 쪽 번호가 아니다.

    KeyIndicator()[3]은 인쇄되는 쪽 번호라 '새 번호로 시작'이 있는 문서에서는
    서로 다른 쪽이 같은 번호를 갖는다(실측: 공고문 18쪽부터 1쪽으로 다시 시작해
    마지막 쪽이 8쪽으로 보였고, 검수 표시는 13~17쪽). 쪽 수 맞춤·묶음 판정이
    엉뚱한 쪽을 섞지 않도록 문서 안 실제 쪽 순서를 쓰고, 읽지 못할 때만
    인쇄 쪽 번호로 대신한다.
    """
    try:
        return int(hwp.XHwpDocuments.Active_XHwpDocument.XHwpDocumentInfo.CurrentPage) + 1
    except Exception:
        pass
    try:
        정보 = hwp.KeyIndicator()
        if 정보 and len(정보) >= 4:
            return int(정보[3])
    except Exception:
        pass
    return None

# 저장 후 결과 검사가 끝난 규칙은 처리 중 기록을 대신한다. 처리 중 기록은
# 뒤 단계에서 해결됐을 수도 있고, 같은 문제를 다른 이름으로 한 번 더 세게 된다.
_처리중_기록_접두어 = {
    'page_group': ('[문장 묶음 페이지 분리]', '[소제목 묶음 쪽 분리]'),
    'word': ('[단어 중간 줄바꿈 미해결]', '[어절 줄분리]', '[단어 분리]',
             '[붙임 괄호 분리]', '[괄호 안 공백 분리]'),
}


def 처리중_기록_대체(파일, 완료된_검사, 경계):
    """검수_문제목록[:경계](저장 전 처리 중 기록) 가운데, 저장 후 검사를 마친
    규칙의 기록을 지운다. 경계 뒤의 저장 후 검사 기록은 그대로 둔다.

    단어 분리 기록은 본문·표 구분이 없으므로, 표·컨트롤 단어 검사가 필요한
    작업이면 두 검사를 모두 마쳤을 때만 지운다.
    """
    global 검수_문제목록
    접두어 = []
    if 'page_group' in 완료된_검사:
        접두어 += _처리중_기록_접두어['page_group']
    컨트롤_필요 = (stage_enabled(선택_세부작업, 'control_spacing')
                or stage_enabled(선택_세부작업, 'control_word_check'))
    if 'word_check' in 완료된_검사 and (not 컨트롤_필요 or 'control_word_check' in 완료된_검사):
        접두어 += _처리중_기록_접두어['word']
    if not 접두어:
        return 0
    접두어 = tuple(접두어)
    남김 = [item for index, item in enumerate(검수_문제목록)
          if index >= 경계 or str(item.get('file')) != str(파일)
          or not str(item.get('text', '')).startswith(접두어)]
    지운수 = len(검수_문제목록) - len(남김)
    검수_문제목록[:] = 남김
    return 지운수


def 검수_문제_기록(파일, text):
    global 검수_문제목록
    if not 검수_사용:
        return
    문제 = {
        "file": str(파일),
        "text": text,
        "page": 현재_페이지번호(),
    }
    # 반복 처리나 최종 검수에서 같은 미해결 줄이 반복 검출될 수 있다.
    # 파일·페이지·문제 텍스트가 같으면 한 번만 기록한다.
    문제키 = (문제["file"], 문제["page"], 문제["text"])
    기존키 = {(항목["file"], 항목["page"], 항목["text"]) for 항목 in 검수_문제목록}
    if 문제키 not in 기존키:
        검수_문제목록.append(문제)


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


_괄호내부_다음구간_미리보기_글자수 = 40


def 현재줄_끝_괄호내부_공백분리인가():
    """'계약방법(공개모집' | '원칙, 수의계약)이'처럼, 괄호 안 부연 설명의
    공백에서 화면줄이 갈라졌는지 확인한다.

    '(공개모집 원칙, 수의계약)'처럼 여는 괄호와 닫는 괄호 사이가 공백·쉼표로
    이어진 짧은 설명은 여는 괄호부터 닫는 괄호까지를 하나의 어절로 보고,
    그 안의 공백에서 줄이 갈라지면 다른 어절 분리와 똑같이 자간을 좁혀
    같은 화면줄에 붙인다. 닫는 괄호가 미리보기 범위 안에 없으면(설명이
    너무 길면) 대상으로 보지 않는다.
    """
    if hwp is None:
        return False

    원래위치 = hwp.GetPos()
    try:
        hwp_run("MoveLineEnd")
        줄끝위치 = hwp.GetPos()

        # 줄 끝 바로 다음 문자가 실제 공백이어야 이 규칙의 대상이다
        # (실제 Enter는 제외).
        hwp_run("MoveSelRight")
        다음위치 = hwp.GetPos()
        다음문자 = 현재선택영역_텍스트()
        hwp_run("Cancel")
        hwp.SetPos(*줄끝위치)
        if not 다음문자 or 실제_엔터_포함(다음문자) or not 다음문자[0].isspace():
            return False
        if 다음위치[0] != 줄끝위치[0] or 다음위치[1] != 줄끝위치[1]:
            return False

        # 문단 시작부터 줄 끝까지 열린 괄호가 아직 닫히지 않았는지 확인한다.
        hwp.SetPos(줄끝위치[0], 줄끝위치[1], 0)
        if hwp.SelectText(줄끝위치[1], 0, 줄끝위치[1], 줄끝위치[2]) is False:
            hwp.SetPos(*줄끝위치)
            return False
        앞부분 = (현재선택영역_텍스트() or "").replace("\r", "").replace("\n", "")
        hwp_run("Cancel")
        hwp.SetPos(*줄끝위치)
        여는괄호수 = sum(앞부분.count(ch) for ch in "(（")
        닫는괄호수 = sum(앞부분.count(ch) for ch in ")）")
        if 여는괄호수 <= 닫는괄호수:
            return False

        # 닫는 괄호가 미리보기 범위 안에서 나오는지 확인한다.
        for _ in range(_괄호내부_다음구간_미리보기_글자수):
            hwp_run("MoveSelRight")
        다음구간 = (현재선택영역_텍스트() or "").replace("\r", "").replace("\n", "")
        hwp_run("Cancel")
        hwp.SetPos(*줄끝위치)
        return any(ch in ")）" for ch in 다음구간)
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


# 단어는 한글/영문/숫자와 결합문자, 단어 사이 가운뎃점으로 판정한다.
def 단어문자인가(ch):
    return bool(ch) and all(c.isalnum() or unicodedata.category(c).startswith('M')
                            or c in '·ㆍ' for c in ch)


def 단어모드_범위선택(start, end):
    if start[:2] != end[:2] or start[2] >= end[2]:
        raise ValueError('같은 문단의 비어 있지 않은 범위만 선택할 수 있습니다.')
    hwp.SetPos(*start)
    if hwp.SelectText(start[1], start[2], end[1], end[2]) is False:
        raise RuntimeError('단어 모드 범위 선택 실패')


def 단어모드_한글자(pos, 뒤로=False):
    """문자열 인덱스 대신 한글의 실제 위치를 사용(컨트롤/UTF-16 안전)."""
    hwp.SetPos(*pos)
    hwp_run('MovePrevChar' if 뒤로 else 'MoveNextChar')
    other = hwp.GetPos()
    if other[:2] != pos[:2] or other == pos:
        return None
    start, end = (other, pos) if 뒤로 else (pos, other)
    단어모드_범위선택(start, end)
    text = 현재선택영역_텍스트()
    hwp_run('Cancel')
    return start, end, text


def 단어모드_줄범위(pos):
    """화면줄의 [시작, 끝) 실제 위치. MoveLineEnd의 커서 위치를 단정하지 않는다."""
    hwp.SetPos(*pos)
    hwp_run('MoveLineBegin')
    start = hwp.GetPos()
    hwp_run('MoveLineEnd')
    raw_end = hwp.GetPos()
    hwp_run('MoveNextChar')
    probe = hwp.GetPos()
    if probe[:2] == start[:2] and probe != raw_end:
        hwp_run('MoveLineBegin')
        next_start = hwp.GetPos()
        if next_start[:2] == start[:2] and next_start[2] > start[2]:
            # 소프트 줄바꿈에서는 MoveLineEnd가 정확한 경계이고, 다음 줄의
            # MoveLineBegin은 첫 글자 뒤 위치를 돌려주는 한글 COM 사례가 있다.
            # 이를 next_start로 쓰면 '맞춤|형'의 '형'을 건너뛰어 분리를 놓친다.
            # 실제 줄바꿈 문자가 있을 때만 그 문자를 포함한 next_start를 쓴다.
            if 두_위치_사이_줄바꿈_문자인가(raw_end, next_start):
                return start, next_start
            return start, raw_end
    hwp.SetPos(*start)
    hwp_run('MoveParaEnd')
    return start, hwp.GetPos()


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

def 의미단위_범위(text):
    """날짜·괄호 기간·물결표를 각각 독립된 의미 단위로 보존한다."""
    result = []
    offset = 0
    for match in _기간_단위.finditer(text):
        result.extend((a + offset, b + offset)
                      for a, b in 일반_의미단위_범위(text[offset:match.start()]))
        result.append(match.span())
        offset = match.end()
    result.extend((a + offset, b + offset)
                  for a, b in 일반_의미단위_범위(text[offset:]))
    return result


def 일반_의미단위_범위(text):
    """공백을 넘지 않고 붙임표시와 짧은 괄호를 포함한 단어 범위를 반환."""
    result = []
    i = 0
    while i < len(text):
        start = i
        has_core = False
        while i < len(text):
            ch = text[i]
            if ch in "·ㆍ":
                break
            if 단어문자인가(ch):
                has_core = has_core or ch.isalnum()
                i += 1
            elif ch in _단어_붙임표시:
                i += 1
            elif ch in '(（' and has_core:
                closing = ')' if ch == '(' else '）'
                end = text.find(closing, i + 1)
                inside = text[i + 1:end] if end >= 0 else ''
                if not (1 <= len(inside) <= 3 and all(c.isalnum() for c in inside)):
                    break
                i = end + 1
            else:
                break
        if has_core:
            result.append((start, i))
        if i == start:
            i += 1
    return result


# 열거 뒤에 쓰는 의존명사 '등'은 바로 앞 어절과 한 어절로 묶는다.
# 예: '사과, 바나나 등으로' → '바나나 등으로'가 한 어절이므로 '바나나 | 등으로'로
# 갈라지면 단어 분리로 보고 자간을 조정한다. '등록', '등급'처럼 '등'으로
# 시작하는 다른 낱말은 뒤에 조사만 오는 경우가 아니므로 묶지 않는다.
_등_어절 = re.compile(
    r"등(?:으로서|으로써|으로|에서|에게|까지|부터|이며|이고|이다|이나|이라|"
    r"과|와|을|를|은|는|이|가|의|에|도|만)?[,，.)）」』’”]*")


def 등_어절인가(text):
    return bool(text) and bool(_등_어절.fullmatch(text))


# 열거의 '단어 + 빈칸 + 숫자 + 쉼표'도 한 어절로 묶는다.
# 예: '수원 2, 서울 4, 용인 1등으로 구성' → '수원 2,'와 '서울 4,'가 각각 한
# 어절이므로 '수원 | 2,'로 갈라지면 단어 분리로 보고 자간을 조정한다.
_숫자쉼표_어절 = re.compile(r"[0-9]+(?:\.[0-9]+)?[,，]")


def 숫자쉼표_어절인가(text):
    return bool(text) and bool(_숫자쉼표_어절.fullmatch(text))


# 열거의 마지막 항목은 쉼표 없이 끝난다: '…, 서울 4, 용인 1등으로 구성'의
# '용인 1등으로'. 숫자로 시작하고 쉼표로 끝나지 않는 어절이며, 바로 앞 항목이
# '서울 4,'처럼 '숫자 + 쉼표'로 끝날 때만 묶는다('대회에서 1등으로'는 묶지 않음).
_숫자끝_어절 = re.compile(r"[0-9]+(?:\.[0-9]+)?[^\s,，]*")
_숫자쉼표_끝 = re.compile(r"[0-9]+(?:\.[0-9]+)?[,，]$")


def 숫자끝_어절인가(text):
    return (bool(text) and bool(_숫자끝_어절.fullmatch(text))
            and not 숫자쉼표_어절인가(text))


def _숫자쉼표_앞단어인가(text):
    """'수원 2,'의 '수원'처럼 숫자 앞에 오는 단어. 숫자·쉼표로 끝나는 앞 항목
    ('2,' 등)은 단어가 아니므로 '2, 3,'처럼 숫자끼리는 묶지 않는다."""
    return bool(text) and not text[-1] in ',，' and any(ch.isalpha() for ch in text)


def 어절_의미단위_범위(text):
    """의미단위_범위에 '앞 어절 + 공백 + 등', '단어 + 공백 + 숫자,' 묶음을 더한 범위."""
    result = []
    for a, b in 의미단위_범위(text):
        joined = result and a >= 1 and text[a - 1] == ' ' and result[-1][1] == a - 1
        if joined and 등_어절인가(text[a:b]):
            result[-1] = (result[-1][0], b)
        elif (joined and 숫자쉼표_어절인가(text[a:b])
                and _숫자쉼표_앞단어인가(text[result[-1][0]:result[-1][1]])):
            result[-1] = (result[-1][0], b)
        elif (joined and 숫자끝_어절인가(text[a:b]) and len(result) >= 2
                and _숫자쉼표_앞단어인가(text[result[-1][0]:result[-1][1]])
                and result[-2][1] + 1 == result[-1][0] and text[result[-2][1]] == ' '
                and _숫자쉼표_끝.search(text[result[-2][0]:result[-2][1]])):
            result[-1] = (result[-1][0], b)
        else:
            result.append((a, b))
    return result


def 앞어절_묶음_후속인가(text):
    """앞 어절과 빈칸을 사이에 두고 한 어절로 묶일 수 있는 뒤 어절
    ('등으로', '2,', 열거 마지막 항목의 '1등으로'). 실제로 묶이는지는
    어절_의미단위_범위가 앞 문맥까지 보고 가린다."""
    return 등_어절인가(text) or 숫자쉼표_어절인가(text) or 숫자끝_어절인가(text)


def _왼쪽_어절_추가(before):
    """before(경계에서 왼쪽으로 읽은 글자, 역순)에 빈칸 너머 앞 어절 하나를 더한다.
    열거 마지막 항목('용인 1등으로')은 그 앞 항목('4,')을 보고 묶기 때문이다."""
    if not before:
        return before
    gap, space = _단어모드_공백전까지(before[-1][0], True)
    if gap is None or gap or space is None:
        return before
    previous, _ = _단어모드_공백전까지(space[0], True)
    if previous:
        return before + [space] + previous
    return before


def _단어모드_공백전까지(pos, 뒤로=False):
    """pos에서 한 방향으로 공백·개행·컨트롤 전까지의 글자 목록과,
    멈춘 글자가 보통 공백(' ')이면 그 글자를 돌려준다. 중단 시 (None, None)."""
    parts = []
    while True:
        if 중단_요청됨():
            return None, None
        part = 단어모드_한글자(pos, 뒤로)
        if not part or not part[2]:
            return parts, None
        if any(c.isspace() or unicodedata.category(c) == 'Cc' for c in part[2]):
            return parts, (part if part[2] == ' ' else None)
        parts.append(part)
        pos = part[0] if 뒤로 else part[1]


def _띄운날짜_어절_확장(before, after, stop_left, stop_right, 최대=3):
    """경계 양쪽으로 빈칸 너머의 날짜 조각('10.', '19.~11.', '18.')을 최대 몇 개 더 붙인다.
    실제로 한 기간인지는 어절_의미단위_범위(_기간_단위)가 가린다."""
    for 뒤로, parts, stop in ((True, before, stop_left), (False, after, stop_right)):
        for _ in range(최대):
            if stop is None:
                break
            word, next_stop = _단어모드_공백전까지(stop[0] if 뒤로 else stop[1], 뒤로)
            if word is None:
                return None, None
            text = ''.join(p[2] for p in (reversed(word) if 뒤로 else word))
            if not word or not _띄운날짜어절.fullmatch(text):
                break
            parts = parts + [stop] + word
            stop = next_stop
        if 뒤로:
            before = parts
        else:
            after = parts
    return before, after


def 단어모드_분리정보(anchor):
    start, boundary = 단어모드_줄범위(anchor)
    right = 단어모드_한글자(boundary)
    if not right or not right[2]:
        return None
    if any(c.isspace() for c in right[2]):
        # 공백에서 줄이 바뀐 경우는 다음 어절이 '등' 또는 '숫자,'일 때만
        # 분리 후보다(실제로 묶이는지는 어절_의미단위_범위가 가린다).
        if right[2] != ' ':
            return None
        peek = 단어모드_한글자(right[1])
        if not peek or not (peek[2] == '등' or peek[2].isdigit()):
            return None
    _, next_end = 단어모드_줄범위(right[1])
    if next_end[2] <= boundary[2]:
        return None
    # 공백/실제 개행/컨트롤 경계를 넘지 않는 구간의 실제 HWP 위치를 보관.
    before, stop_left = _단어모드_공백전까지(boundary, True)
    if before is None:
        return None
    after, stop_right = _단어모드_공백전까지(boundary)
    if after is None:
        return None
    if not before and not after:
        return None
    # 경계가 걸친 어절이 '등'·'숫자,' 어절이면 공백 앞 어절까지 묶는다.
    현재어절 = ''.join(p[2] for p in reversed(before)) + ''.join(p[2] for p in after)
    # 띄어 쓴 날짜 기간('10. 19.~11. 18.')은 빈칸을 넘어 한 어절로 묶는다.
    날짜기간 = bool(_띄운날짜어절.fullmatch(현재어절))
    if 날짜기간:
        before, after = _띄운날짜_어절_확장(before, after, stop_left, stop_right)
        if before is None:
            return None
    elif stop_left is not None and 앞어절_묶음_후속인가(현재어절):
        previous, _ = _단어모드_공백전까지(stop_left[0], True)
        if previous is None:
            return None
        if previous:
            before = before + [stop_left] + previous
    # 경계가 걸친 어절 뒤에 '등'·'숫자,' 어절이 이어지면 그 어절까지 묶는다.
    뒤어절 = ''
    if not 날짜기간 and (stop_left is None or not 앞어절_묶음_후속인가(현재어절)):
        if stop_right is not None:
            peek = 단어모드_한글자(stop_right[1])
            if peek and (peek[2] == '등' or peek[2].isdigit()):
                following, _ = _단어모드_공백전까지(stop_right[1])
                if following is None:
                    return None
                뒤어절 = ''.join(p[2] for p in following)
                if 앞어절_묶음_후속인가(뒤어절):
                    after = after + [stop_right] + following
    # 열거 마지막 항목은 앞 항목('4,')까지 봐야 묶을지 정할 수 있다.
    if not 날짜기간 and (숫자끝_어절인가(현재어절) or 숫자끝_어절인가(뒤어절)):
        before = _왼쪽_어절_추가(before)
    parts = list(reversed(before)) + after
    text = ''.join(part[2] for part in parts)
    offsets = [0]
    for part in parts:
        offsets.append(offsets[-1] + len(part[2]))
    cut = sum(len(part[2]) for part in before)
    for a, b in 어절_의미단위_범위(text):
        if not a < cut < b or a not in offsets or b not in offsets:
            continue
        selected = parts[offsets.index(a):offsets.index(b)]
        left_count = sum(len(t) for p, q, t in selected if p[2] >= start[2] and q[2] <= boundary[2])
        right_count = sum(len(t) for p, q, t in selected if p[2] >= boundary[2] and q[2] <= next_end[2])
        return start, boundary, selected[0][0], selected[-1][1], left_count, right_count
    return None


# 줄 첫머리에서 시작한 단어가 넘친 부분이 그 줄 글자 수의 이 비율을 넘으면
# 자간·장평을 허용 범위까지 줄여도 한 줄에 넣을 수 없다(좁은 표 칸의 긴 합성어).
칸폭초과_허용비율 = 0.2


def 칸폭보다_긴_단어인가(info):
    """단어모드_분리정보 결과가 '줄 첫머리에서 시작했는데도 넘치는 단어'인지.

    실측: 공고문 표 칸 단어 분리 미해결 20건 중 13건이 줄 전체가 그 단어
    하나였다(예: 5자 칸의 '질그랭이거|점센터'). 밀 곳도 당길 곳도 없어 어떤
    조정으로도 풀 수 없으므로, 시도하지 않고 검수에서도 적용 제외로 적는다.
    """
    start, _, word_start, _, left, right = info
    return word_start[2] <= start[2] and right > left * 칸폭초과_허용비율


def 붙임의미단위_줄분리인가():
    original = hwp.GetPos()
    try:
        hwp_run("MoveLineBegin")
        info = 단어모드_분리정보(hwp.GetPos())
        if info is None:
            return False
        단어모드_범위선택(info[2], info[3])
        text = 현재선택영역_텍스트()
        return (bool(_기간_단위.search(text))
                or any(ch in _단어_붙임표시 or ch in '(（' for ch in text)
                or any(앞어절_묶음_후속인가(word) for word in text.split(' ')[1:]))
    finally:
        hwp_run('Cancel')
        hwp.SetPos(*original)


_단어모드_자간필드 = tuple('Spacing' + name for name in
    ('Hangul', 'Latin', 'Hanja', 'Japanese', 'Other', 'Symbol', 'User'))
_단어모드_장평필드 = tuple('Ratio' + name for name in
    ('Hangul', 'Latin', 'Hanja', 'Japanese', 'Other', 'Symbol', 'User'))


def 자간조정_본문범위(start, end):
    """내어쓰기와 같은 기준으로 항목기호·라벨·후행 공백을 제외한다."""
    if start[:2] != end[:2]:
        raise ValueError('자간 조정 범위는 한 문단이어야 합니다')
    original = hwp.GetPos()
    try:
        hwp.SetPos(start[0], start[1], 0)
        text = 현재문단_텍스트()
        offset = 문단_자간보호_선행부_오프셋(text)
        # '(운영방식)'처럼 본문 없이 라벨만 있는 문단은 라벨 끝까지 보호한다.
        marker_end = 문장부호_마커_끝위치(text)
        if marker_end is not None and re.fullmatch(r'\s*[（(][^\r\n]+[)）]\s*[:：]?\s*', text[marker_end:]):
            offset = len(text.rstrip('\r\n'))
        if marker_end is not None and not text[marker_end:].strip():
            offset = len(text.rstrip('\r\n'))
        if offset is None:
            return start, end
        body = len(text[:offset].encode('utf-16-le')) // 2
        return (start[0], start[1], min(end[2], max(start[2], body))), end
    finally:
        hwp.SetPos(*original)


def 자간조정_현재줄_본문선택():
    """화면줄 기반 단축키 조정에서도 선행부를 제외한다."""
    anchor = hwp.GetPos()
    hwp.Run('Cancel')
    hwp.SetPos(*anchor)
    hwp.Run('MoveLineEnd')
    end = hwp.GetPos()
    hwp.Run('MoveLineBegin')
    start = hwp.GetPos()
    start, end = 자간조정_본문범위(start, end)
    if start[2] >= end[2]:
        return False
    단어모드_범위선택(start, end)
    return True


def _단어모드_다음위치(pos):
    """pos 다음 글자 위치(같은 문단 안). 글자 내용은 읽지 않는다."""
    hwp.SetPos(*pos)
    hwp_run('MoveNextChar')
    other = hwp.GetPos()
    if other[:2] != pos[:2] or other == pos:
        return None
    return other


def 단어모드_서식보관(start, end):
    """자간과 장평을 한 번에 글자별로 읽어 (자간 runs, 장평 runs)로 보관한다.

    실패 시 Undo 이력 대신 정확히 복원하기 위한 원래 값이다. 한글은 여러
    글자를 선택했을 때 서식이 섞여 있으면 값을 믿을 수 없게 돌려주므로(실측)
    글자마다 읽되, 보관에는 글자 내용이 필요 없어 위치만 옮긴다(한글 호출
    약 40% 감소). 자간과 장평을 따로 읽던 두 번의 순회도 한 번으로 줄인다.
    """
    start, end = 자간조정_본문범위(start, end)
    spacing_runs, ratio_runs = [], []
    pos = start

    def 병합(runs, pos, nxt, values):
        if runs and runs[-1][2] == values:
            runs[-1] = (runs[-1][0], nxt, values)
        else:
            runs.append((pos, nxt, values))

    while pos[2] < end[2]:
        if 중단_요청됨():
            return None
        nxt = _단어모드_다음위치(pos)
        if not nxt or nxt[2] > end[2]:
            raise RuntimeError('서식 보관 중 문자 위치 확인 실패')
        단어모드_범위선택(pos, nxt)
        pset = hwp.HParameterSet.HCharShape
        hwp.HAction.GetDefault('CharShape', pset.HSet)
        spacing = tuple(int(getattr(pset, key)) for key in _단어모드_자간필드)
        if any(v < -50 or v > 50 for v in spacing):
            raise RuntimeError('허용 범위 밖의 원래 자간')
        ratio = tuple(int(getattr(pset, key)) for key in _단어모드_장평필드)
        병합(spacing_runs, pos, nxt, spacing)
        병합(ratio_runs, pos, nxt, ratio)
        pos = nxt
    hwp_run('Cancel')
    return spacing_runs, ratio_runs


def 단어모드_자간보관(start, end):
    """혼합 자간을 연속 구간별 보관. 실패 시 Undo 이력 대신 정확히 복원."""
    보관 = 단어모드_서식보관(start, end)
    return None if 보관 is None else 보관[0]


def 단어모드_자간적용(runs, delta):
    for start, end, values in runs:
        단어모드_범위선택(start, end)
        act = hwp.CreateAction('CharShape')
        pset = act.CreateSet()
        for key, value in zip(_단어모드_자간필드, values):
            pset.SetItem(key, value + delta)
        if act.Execute(pset) is False:
            raise RuntimeError('단어 모드 자간 적용 실패')
    hwp_run('Cancel')


def 단어모드_장평보관(start, end):
    """혼합 장평(글자 가로비율)을 연속 구간별 보관."""
    보관 = 단어모드_서식보관(start, end)
    return None if 보관 is None else 보관[1]


def 단어모드_장평적용(runs, delta):
    for start, end, values in runs:
        단어모드_범위선택(start, end)
        act = hwp.CreateAction('CharShape')
        pset = act.CreateSet()
        for key, value in zip(_단어모드_장평필드, values):
            pset.SetItem(key, max(85, min(150, value + delta)))
        if act.Execute(pset) is False:
            raise RuntimeError('단어 모드 장평 적용 실패')
    hwp_run('Cancel')


class _단계탐색_중단(Exception):
    """단계 탐색 중 사용자가 작업을 중단했다."""


# 자간·장평 단계 탐색에서 실제로 줄 배치를 다시 잰 횟수(작업 로그 통계용).
단계탐색_통계 = {"탐색": 0, "측정": 0}


def 최소_성공단계_탐색(최대, 적용후_확인, 상한먼저=False, 선형구간=8):
    """1..최대 단계 중 성공하는 가장 작은 단계를 찾는다.

    적용후_확인(step)은 step 단계를 문서에 적용하고 성공 여부를 돌려준다
    (중단이면 None). 측정(줄 배치 다시 재기)이 비싸므로 상황별로 줄인다.

    - 기본(성공이 흔하고 대개 작은 단계에서 성공하는 어절 분리): 선형구간
      (8단계)까지는 한 단계씩 올려 예전과 똑같이 찾고, 그래도 안 되면 상한을
      바로 확인한 뒤 그 사이를 이분 탐색한다. 실패 시 30번 대신 약 10번만 잰다.
    - 상한먼저(실패가 흔한 다음 단어 당김·장평 축소): 상한에서도 안 되면 한
      번만 재고 포기하고, 되면 한 단계씩 올려 가장 작은 단계를 찾는다.

    반환: 성공 단계(그 단계가 적용된 상태) 또는 None(마지막으로 시도한
    단계가 적용된 상태이므로 호출자가 원래 값으로 복원한다).
    중단 시 _단계탐색_중단을 일으킨다.
    """
    if 최대 < 1:
        return None
    단계탐색_통계["탐색"] += 1
    마지막 = [None]

    def 확인(step):
        if 중단_요청됨():
            raise _단계탐색_중단
        결과 = 적용후_확인(step)
        if 결과 is None:
            raise _단계탐색_중단
        단계탐색_통계["측정"] += 1
        마지막[0] = step
        return bool(결과)

    def 확정(step):
        # 마지막으로 잰 단계가 아니면 다시 적용해 확인한다. 드문 비단조 배치로
        # 실패하면 그 위 단계를 차례로 확인한다.
        if 마지막[0] == step:
            return step
        while not 확인(step):
            if step >= 최대:
                return None
            step += 1
        return step

    if 상한먼저:
        if not 확인(최대):
            return None
        for step in range(1, 최대):
            if 확인(step):
                return step
        return 확정(최대)

    for step in range(1, min(선형구간, 최대) + 1):
        if 확인(step):
            return step
    if 최대 <= 선형구간 or not 확인(최대):
        return None
    성공 = 최대
    lo, hi = 선형구간 + 1, 최대 - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if 확인(mid):
            성공, hi = mid, mid - 1
        else:
            lo = mid + 1
    return 확정(성공)


def 단어_장평_추가축소_시도(start, end, anchor, word_end, 최대시도, 보관=None):
    """자간만으로 안 줄어드는 긴 어절에 장평(글자 가로비율)을 추가로 줄여본다.

    자간을 허용 범위 끝까지 밀어붙이면 글자가 다닥다닥 붙어 보기 흉해
    지므로, 사람이 수동으로 하듯 자간은 적당히만(최대 4%p) 남기고 장평을
    1%씩 최대 단어_장평_추가축소_최대_단계(기본 10단계, 90%까지) 줄이며
    다시 확인한다 — '자간 -4%, 장평 93%' 조합처럼, 자간을 극한까지
    밀어붙이는 대신 장평과 나눠 분담한다.
    """
    # 보관: 호출자가 같은 구간을 이미 읽고 원래 값으로 되돌려 둔 (자간, 장평)
    # runs. 넘겨받으면 같은 줄을 다시 글자별로 읽지 않는다.
    if 보관 is None:
        보관 = 단어모드_서식보관(start, end)
    if 보관 is None:
        return False
    spacing_runs, ratio_runs = 보관
    # 이 구간이 이전 단계·이전 회차에서 이미 일부 압축돼 있을 수 있다
    # (자간/장평은 회차 사이에 초기화되지 않는다). "이번에 -4%p까지"가
    # 아니라 "최종적으로 -4%p까지"가 되도록, 이미 줄어든 만큼을 빼고
    # 남은 여유만 쓴다 — 그래야 여러 단계·회차에 걸쳐 조금씩 계속
    # 줄어드는 일이 없다.
    현재_최소자간 = min((v for _, _, vs in spacing_runs for v in vs), default=0)
    자간_한도 = min(4, max(1, 최대시도))
    자간값 = -max(0, 자간_한도 + 현재_최소자간)
    if 자간값 and any(not -50 <= v + 자간값 <= 50 for _, _, vs in spacing_runs for v in vs):
        자간값 = 0
    자간적용됨 = False
    성공 = False
    try:
        if 자간값:
            단어모드_자간적용(spacing_runs, 자간값)
            자간적용됨 = True
        현재_최소장평 = min((v for _, _, vs in ratio_runs for v in vs), default=100)
        장평_바닥 = 100 - 단어_장평_추가축소_최대_단계
        여유_단계 = max(0, min(단어_장평_추가축소_최대_단계, 현재_최소장평 - 장평_바닥))

        def 장평_확인(step):
            단어모드_장평적용(ratio_runs, -step)
            return 단어모드_줄범위(anchor)[1][2] >= word_end[2]

        try:
            단계 = 최소_성공단계_탐색(여유_단계, 장평_확인, 상한먼저=True)
        except _단계탐색_중단:
            return False
        성공 = 단계 is not None
        if 성공:
            진단로그(f"[단어 분리 보정] 자간 {자간값}%p + 장평 {현재_최소장평 - 단계}%로 해결")
        elif 여유_단계:
            단어모드_장평적용(ratio_runs, 0)
    finally:
        if not 성공 and 자간적용됨:
            단어모드_자간적용(spacing_runs, 0)
    return 성공


def 다음단어_당김_시도(anchor, 최대시도):
    """긴 단어 전체가 통째로 다음 줄로 밀려, 이번 줄 양쪽정렬이 단어
    사이 간격을 비정상적으로 벌린 경우를 찾아 끌어올린다.

    단어 중간에서 갈라진 경우(단어모드_분리정보가 처리)는 이미 아래
    본 루프가 다루므로 여기서는 제외한다 — 줄 끝이 이미 깨끗한 단어
    경계(공백)이고 바로 다음이 새 단어로 시작하는 경우만 다룬다.

    양쪽정렬 문서에서는 거의 모든 줄이 "단어 경계에서 깔끔하게 끝난"
    상태이므로, 끌어올릴 다음 단어가 문장부호_2줄_기준글자수(기본 5자)
    보다 길면 시도하지 않는다 — 짧은 마지막 줄 병합(문장부호_줄병합_시도)
    과 같은 "끌어올릴 가치가 있을 때만" 기준을 그대로 재사용한다. 자간은
    다음단어_당김_자간_최대_퍼센트(기본 10%p)까지만 쓰고, 그래도 안 되면
    장평도 추가로 줄인다(단어_장평_추가축소_시도, 기본 90%까지).
    """
    start, boundary = 단어모드_줄범위(anchor)
    다음글자 = 단어모드_한글자(boundary)
    if not 다음글자 or not 다음글자[2] or 다음글자[2].isspace():
        return False
    if 단어모드_분리정보(anchor) is not None:
        return False

    pos = boundary
    다음단어_끝 = boundary
    당김단어 = ''
    while True:
        if 중단_요청됨():
            return False
        part = 단어모드_한글자(pos)
        if not part or not part[2] or part[2].isspace():
            break
        다음단어_끝 = part[1]
        당김단어 += part[2]
        pos = part[1]
    if 다음단어_끝[2] == boundary[2]:
        return False
    if 다음단어_끝[2] - boundary[2] > 문장부호_2줄_기준글자수:
        return False

    보관 = 단어모드_서식보관(start, boundary)
    if 보관 is None:
        return False
    runs = 보관[0]
    # 정상적인 단어 경계에서의 선택적 당김은 단어 분리 오류가 아니다.
    다음단어_통계['대상'] += 1
    success = False
    changed = False
    # 단어_장평_추가축소_시도와 같은 이유로, 이 구간이 이미 어느 정도
    # 압축돼 있으면(다른 단계·회차에서) 남은 여유만큼만 쓴다 — "이번에
    # 최대 10%p"가 아니라 "최종적으로 최대 10%p"가 되도록.
    현재_최소자간 = min((v for _, _, vs in runs for v in vs), default=0)
    자간_상한 = max(0, min(최대시도, 다음단어_당김_자간_최대_퍼센트 + 현재_최소자간))
    # 자간은 -50%보다 작게 할 수 없다.
    탐색_상한 = min(자간_상한, 50 + 현재_최소자간)

    def 당김_확인(step):
        nonlocal changed
        changed = True
        단어모드_자간적용(runs, -step)
        return 단어모드_줄범위(anchor)[1][2] >= 다음단어_끝[2]

    try:
        success = 최소_성공단계_탐색(탐색_상한, 당김_확인, 상한먼저=True) is not None
    except _단계탐색_중단:
        return False
    finally:
        if changed and not success:
            단어모드_자간적용(runs, 0)
    if not success and 단어_장평_추가축소_시도(start, boundary, anchor, 다음단어_끝, 자간_상한, 보관=보관):
        success = True
    if success:
        다음단어_통계['적용'] += 1
        단어모드_범위선택(start, boundary)
        색상_적용_현재선택()
        hwp_run('Cancel')
        진단로그(f"[다음 단어 당김 적용] {당김단어!r} / 위치={anchor}")
    else:
        다음단어_통계['미적용'] += 1
        진단로그(f"[다음 단어 당김 미적용] {당김단어!r} / 위치={anchor} / "
                 f"허용 자간 {자간_상한}단계·장평 범위 내 당김 불가, 원래 서식 복원 (오류 아님)")
    return success


def 어절분리_앞줄당김인가(left, right, 마지막줄_짧음=False):
    """화면줄 경계에서 갈라진 어절을 앞줄로 당길지(True) 다음 줄로 밀지(False).

    1) 문단 마지막 줄에 남는 글자가 빈칸 포함 5자 미만이면 무조건 당긴다.
    2) 그 외에는 글자 수가 많은 쪽으로 붙인다. 같으면 앞줄로 당긴다.
       예: '전기|버스'(2:2) → 당김, '실|질적인'(1:3) → '실'을 다음 줄로 밈.
    """
    return bool(마지막줄_짧음) or left >= right


def 단어모드_마지막줄_짧은잔여인가(boundary):
    """경계 다음 화면줄이 문단의 마지막 줄이고, 그 줄의 글자 수가
    빈칸 포함 문장부호_2줄_기준글자수(기본 5자) 미만인지 확인한다."""
    original = hwp.GetPos()
    try:
        right = 단어모드_한글자(boundary)
        if not right:
            return False
        _, next_end = 단어모드_줄범위(right[1])
        hwp.SetPos(*boundary)
        hwp_run('MoveParaEnd')
        para_end = hwp.GetPos()
        if para_end[:2] != boundary[:2] or para_end[2] <= boundary[2]:
            return False
        if next_end[:2] != para_end[:2] or next_end[2] < para_end[2]:
            return False
        단어모드_범위선택(boundary, para_end)
        text = (현재선택영역_텍스트() or '').replace('\r', '').replace('\n', '')
        return len(text) < 문장부호_2줄_기준글자수
    except Exception:
        return False
    finally:
        hwp_run('Cancel')
        hwp.SetPos(*original)


def 단어중간_줄바꿈방지(최대시도):
    """현재 화면줄을 처리하고 다음 경계는 호출자의 줄 순회에서 처리한다."""
    # '단어모드_분리정보'는 경계에서 양옆으로 공백을 만나면 즉시 멈추므로
    # '계약방법(공개모집' | '원칙, 수의계약)이'처럼 괄호 안 공백에서 갈라진
    # 경우는 감지하지 못한다. 아래 루프에서 먼저 자간을 좁혀 처리한다.
    for _ in range(max(1, 최대시도)):
        if 중단_요청됨():
            return False
        if not 현재줄_끝_괄호내부_공백분리인가():
            break
        hwp_run("MoveLineEnd")
        hwp_run("MoveSelLineBegin")
        hwp_run("CharShapeSpacingDecrease")
        색상_적용_현재선택()
        hwp_run("Cancel")
    else:
        문제줄 = 현재_화면줄_텍스트()
        검수_문제_기록(현재_처리파일, f"[괄호 안 공백 분리] {문제줄.strip()}")

    # 긴 단어 전체가 통째로 다음 줄로 밀려 양쪽정렬 간격이 벌어진 경우도
    # 같은 방식(자간 우선, 부족하면 장평 추가)으로 먼저 당겨 본다.
    #
    # 한 줄에서 딱 한 번만 시도한다 — 예전에는 성공할 때마다 같은 줄에서
    # 반복 호출했는데, 그러면 짧은 단어가 연달아 이어질 때(예: '대체
    # 가능'처럼 공백으로 나뉜 두 단어) 매번 새로 5%이내 자간/장평을
    # 재는 게 아니라 '이미 한 번 줄어든 값'을 기준으로 또 줄이는 식으로
    # 누적돼, 결국 문장 전체가 한 줄로 욱여넣어질 때까지 압축이 쌓였다.
    # 한 단어만 당기고 멈추면 각 시도의 상한(다음단어_당김_자간_최대_퍼센트)이
    # 실제 최종 압축폭의 상한으로도 그대로 유지된다.
    if 중단_요청됨():
        return False
    anchor0, _ = 단어모드_줄범위(hwp.GetPos())
    if 다음단어_당김_사용:
        다음단어_당김_시도(anchor0, 최대시도)

    # 다음 단어 당김의 탐색 함수가 경계 주변 문자를 읽으며 커서를 옮긴다.
    # 원래 화면줄로 복귀하지 않으면 바로 뒤의 분리 어절 검사가 다른 줄에서
    # 시작해 '맞춤|형' 같은 실제 문제를 놓친다.
    hwp.SetPos(*anchor0)
    anchor, _ = 단어모드_줄범위(hwp.GetPos())
    seen = set()
    failure_reason = "반복 한도 도달"
    unit_text = ""
    try:
        # 한 단어를 당긴 뒤 다른 단어가 걸칠 수도 있으므로 같은 줄 재검사.
        for _ in range(max(1, 최대시도)):
            if 중단_요청됨():
                return False
            info = 단어모드_분리정보(anchor)
            if info is None:
                return not 중단_요청됨()
            start, boundary, word_start, word_end, left, right = info
            단어모드_범위선택(word_start, word_end)
            unit_text = 현재선택영역_텍스트()
            hwp_run('Cancel')
            진단로그(f"[단어 판정] {unit_text!r} / {left}:{right}자 / 경계={boundary} / 범위={word_start}~{word_end}")
            key = (boundary, word_start, word_end)
            if key in seen:
                failure_reason = "같은 경계 반복"
                break
            seen.add(key)
            if 칸폭보다_긴_단어인가(info):
                진단로그(f"[단어 분리] {unit_text!r} {left}:{right}자: 줄 첫머리부터 넘치는 "
                         f"칸 폭보다 긴 단어라 조정 제외")
                return not 중단_요청됨()
            # 마지막 줄에 빈칸 포함 5자 미만이 남으면 무조건 앞줄로 당긴다.
            # 그 외에는 글자 수가 많은 쪽으로 붙인다(같으면 앞줄로 당김).
            # 예: '실|질적인'은 '실'이 있는 앞줄 자간을 넓혀 '실'을 다음 줄로
            # 밀어낸다. 밀기는 어절 앞까지만 넓혀 어절 전체를 옮기므로
            # '맞|춤형'이 '맞춤|형'으로 일부만 이동한 상태는 성공으로 보지 않는다.
            마지막줄_짧음 = 단어모드_마지막줄_짧은잔여인가(boundary)
            shrink = 어절분리_앞줄당김인가(left, right, 마지막줄_짧음)
            # 이전 줄에서 이미 시작한 긴 단어는 어느 방향으로도 옮길 수 없다.
            if word_start[2] < start[2] or word_end[2] <= start[2]:
                failure_reason = "이전 줄부터 이어진 단어"
                break
            단어분리_통계["대상"] += 1
            failure_reason = f"{최대시도}단계 이내 이동 실패"
            방법 = ""

            def 앞줄로_당기기():
                보관 = 단어모드_서식보관(start, word_end)
                if 보관 is None:
                    return None
                runs = 보관[0]
                success = False
                changed = False
                # 자간은 -50%보다 작게 할 수 없다.
                상한 = min(최대시도, 50 + min((v for _, _, vs in runs for v in vs), default=0))

                def 당김_확인(step):
                    nonlocal changed
                    changed = True
                    단어모드_자간적용(runs, -step)
                    return 단어모드_줄범위(anchor)[1][2] >= word_end[2]

                try:
                    step = 최소_성공단계_탐색(상한, 당김_확인)
                    success = step is not None
                    if success:
                        return f"앞줄 자간 -{step}%로 당김"
                except _단계탐색_중단:
                    return None
                finally:
                    if changed and not success:
                        단어모드_자간적용(runs, 0)
                # 자간만으로 안 되면 장평을 추가로 줄여 본다 — 사람이 수동으로
                # 하듯 자간은 적당히만 남기고 장평과 나눠 분담한다.
                if 단어_장평_추가축소_시도(start, word_end, anchor, word_end, 최대시도, 보관=보관):
                    return "앞줄 자간+장평 축소로 당김"
                return ""

            def 다음줄로_밀기():
                # 어절 앞까지만 넓혀 어절 전체를 다음 줄로 보낸다. 어절 일부나
                # 다음 줄 전체를 넓히지 않으므로 혼합 자간 상태를 남기지 않는다.
                if word_start[2] <= start[2]:
                    return ""
                push_runs = 단어모드_자간보관(start, word_start)
                if push_runs is None:
                    return None
                success = False
                changed = False
                # 자간은 +50%보다 크게 할 수 없다.
                상한 = min(최대시도, 50 - max((v for _, _, vs in push_runs for v in vs), default=0))

                def 밀기_확인(push_step):
                    nonlocal changed
                    changed = True
                    단어모드_자간적용(push_runs, push_step)
                    _, previous_end = 단어모드_줄범위(anchor)
                    next_start, next_end = 단어모드_줄범위(word_start)
                    return (previous_end[2] <= word_start[2]
                            and next_start[2] <= word_start[2]
                            and next_end[2] >= word_end[2])

                try:
                    push_step = 최소_성공단계_탐색(상한, 밀기_확인)
                    success = push_step is not None
                    if success:
                        return f"앞 구간 자간 +{push_step}%로 어절 전체를 다음 줄로 밈"
                except _단계탐색_중단:
                    return None
                finally:
                    if changed and not success:
                        단어모드_자간적용(push_runs, 0)
                return ""

            # 정한 방향을 먼저 시도하고, 한도 안에서 안 되면 반대 방향으로
            # 보완해 어절이 갈라진 채 남지 않게 한다.
            시도순서 = (앞줄로_당기기, 다음줄로_밀기) if shrink else (다음줄로_밀기, 앞줄로_당기기)
            for 시도 in 시도순서:
                try:
                    결과 = 시도()
                except RuntimeError as e:
                    # 서식 보관(읽기 전용) 단계에서 글자 위치를 확인하지 못하면
                    # 이 방향만 실패로 보고 반대 방향·다음 줄로 넘어간다. 예외를
                    # 올려 보내면 문서 전체 처리가 중단되고 결과도 저장되지
                    # 않았다(실측: 보도자료 '건강을' 위치에서 중단).
                    진단로그(f"[단어 중간 줄바꿈 방지] {unit_text!r} 서식 확인 실패로 이 방향 건너뜀: {e}")
                    결과 = ""
                if 결과 is None:
                    return False
                if 결과:
                    방법 = 결과
                    break
            if not 방법:
                단어분리_통계["실패"] += 1
                break
            failure_reason = ""
            단어분리_통계["성공"] += 1
            end = word_end if 방법.startswith("앞줄") else word_start
            단어모드_범위선택(start, end)
            색상_적용_현재선택()
            hwp_run('Cancel')
            기준 = "마지막 줄 5자 미만" if 마지막줄_짧음 else ("글자 수 같음" if left == right else "글자 수 많은 쪽")
            진단로그(f"[단어 중간 줄바꿈 방지] {unit_text!r} {left}/{right}자 ({기준}): {방법}")
        if 단어모드_분리정보(anchor) is not None:
            hwp.SetPos(*anchor)
            로그(f"[단어 중간 줄바꿈 미해결] {unit_text!r}: {failure_reason}")
            검수_문제_기록(현재_처리파일, '[단어 중간 줄바꿈 미해결] ' + 현재_화면줄_텍스트().strip())
        return True
    finally:
        hwp_run('Cancel')
        hwp.SetPos(*anchor)


def 자간자동조정(최대시도=None):
    """현재 화면줄의 단어 분리를 자간으로 푼다. 조정할 본문이 없는 줄(문두 보호)은 건너뛴다."""
    return _문두보호_줄건너뜀(_자간자동조정_본체, 최대시도)


def _자간자동조정_본체(최대시도=None):
    if 최대시도 is None:
        최대시도 = 자간_최대시도_본문
    # 세부 작업에서 '단어 분리 최종 검사'를 선택했다면 일반 자간 옵션과
    # 무관하게 실제 화면줄의 공백 없는 어절 분리를 검사해야 한다.
    if (단어중간_줄바꿈방지_사용
            or stage_enabled(선택_세부작업, 'word_check')):
        return 단어중간_줄바꿈방지(최대시도)

    count = 0
    이전_단어_시작 = None
    총_시도 = 0
    총_시도_상한 = max(최대시도 * 8, 40)
    붙임괄호_축소횟수 = 0
    괄호내부공백_축소횟수 = 0
    어절분리_축소횟수 = 0
    단어_장평축소횟수 = 0

    while True:
        if 중단_요청됨():
            return False

        hwp_run("MoveLineEnd")

        # 새 모드를 꺼도 붙임표시/짧은 괄호의 의미 단위는 동일하게 보호한다.
        if 붙임의미단위_줄분리인가():
            return 단어중간_줄바꿈방지(최대시도)

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

        # '계약방법(공개모집' | '원칙, 수의계약)이'처럼 괄호 안 부연 설명의
        # 공백에서 갈라진 경우도 하나의 어절로 보고 우선 처리한다.
        if 현재줄_끝_괄호내부_공백분리인가():
            if 괄호내부공백_축소횟수 >= 최대시도:
                for _ in range(괄호내부공백_축소횟수):
                    hwp_run("Undo")
                문제줄 = 현재_화면줄_텍스트()
                검수_문제_기록(현재_처리파일, f"[괄호 안 공백 분리] {문제줄.strip()}")
                return True

            hwp_run("MoveLineEnd")
            hwp_run("MoveSelLineBegin")
            hwp_run("CharShapeSpacingDecrease")
            색상_적용_현재선택()
            hwp_run("Cancel")
            괄호내부공백_축소횟수 += 1
            총_시도 += 1
            if 총_시도 > 총_시도_상한:
                return True
            continue

        괄호내부공백_축소횟수 = 0

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
            단어_장평축소횟수 = 0
            이전_단어_시작 = 단어_시작

        총_시도 += 1
        if 총_시도 > 총_시도_상한:
            hwp_run("Cancel")
            return True

        if count >= 최대시도:
            # 자간만으로 해결되지 않는 긴 어절은 현재 줄의 장평을 1%씩
            # 최대 15단계 보조 축소한다. 자간을 과도하게 30단계 이상
            # 누르는 것보다 글자 폭을 소폭 줄이는 편이 가독성이 안정적이다.
            if 단어_장평축소횟수 < 15:
                hwp_run("Cancel")
                hwp_run("MoveLineEnd")
                hwp_run("MoveSelLineBegin")
                hwp_run("CharShapeRatioDecrease")
                hwp_run("Cancel")
                단어_장평축소횟수 += 1
                진단로그(f"[단어 분리 보정] 장평 {단어_장평축소횟수}단계 추가 축소")
                # 다음 반복에서 해결 여부를 다시 판정하되 기존 자간은 유지한다.
                count = 최대시도 - 1
                continue

            문제줄 = 현재_화면줄_텍스트()
            for _ in range(count + 단어_장평축소횟수):
                hwp_run("Undo")
            검수_문제_기록(현재_처리파일, f"[단어 분리] {문제줄.strip()}")
            try:
                hwp.SetPos(단어_시작[0], 단어_시작[1], 단어_시작[2])
            except Exception:
                pass
            hwp_run("MoveWordEnd")
            이전_단어_시작 = None
            count = 0
            단어_장평축소횟수 = 0
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
    # 호출 전 단계가 남긴 커서 위치에 의존하면 두 번째 '최종 검사'가 문서
    # 끝에서 시작해 아무것도 검사하지 않는 경우가 생긴다. 모든 호출은
    # 본문 시작부터 독립적으로 전수 검사한다.
    순회_시작()
    직전위치 = None
    정체횟수 = 0
    검사문단 = None
    while True:
        if 중단_요청됨():
            return False
        현재위치 = hwp.GetPos()
        if 쪽범위_끝지남(현재위치):
            return True
        if (_알파_일괄서식_문서 and 현재위치[0] == 0
                and tuple(현재위치[:2]) != 검사문단):
            검사문단 = tuple(현재위치[:2])
            if _알파_한줄문단인가(현재위치):
                hwp_run('MoveParaEnd')
                문단끝 = hwp.GetPos()
                hwp_run('MoveNextChar')
                if hwp.GetPos() == 문단끝:
                    return True
                continue
        if ((not 쪽범위_안인가(현재위치)) or (not 재검사_대상인가(현재위치))
                or 표셀_자간_제외인가()):
            # 작업 쪽 범위 밖, 2차 이후 재검사 대상이 아닌 문단, '표 안 문장 제외'인
            # 표 셀이면 조정하지 않고 다음 문단으로 넘어간다.
            hwp_run("MoveParaEnd")
            hwp_run("MoveNextChar")
            if hwp.GetPos() == 현재위치:
                return True
            직전위치 = None
            정체횟수 = 0
            continue
        if 현재위치 == 직전위치:
            정체횟수 += 1
            if 정체횟수 >= 2:
                # v1.44: 해결 불가능한 단어(예: 15단계로도 못 당기는 긴 인용부호
                # 단어) 하나에서 순회 전체를 return True로 끝내버리면, 그 뒤에
                # 있는 나머지 문서 전체가 단어분리 검사에서 통째로 빠진다.
                # 이 문단(줄)만 포기하고 다음 문단으로 강제 이동해 나머지
                # 문서는 계속 검사되도록 한다.
                로그("본문 자간조정 순회가 같은 위치에서 반복되어 이 문단을 건너뜁니다.")
                hwp_run("MoveParaEnd")
                hwp_run("MoveNextChar")
                건너뛴위치 = hwp.GetPos()
                정체횟수 = 0
                직전위치 = None
                if 건너뛴위치 == 현재위치:
                    return True  # 문서 끝: 더 이상 이동할 곳이 없음
                continue
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


def 문단세트_가능(회차=1):
    """세트 방식을 쓸 수 있는 조건(아니면 기존 단계별 방식)."""
    return bool(알파_문단세트_사용 and 회차 == 1 and 작업_모드 == 'all' and 표준서식_사용
                and 쪽범위_요청 is None and not stage_enabled(선택_세부작업, 'style_unify'))


def 문단세트1_글서식_적용():
    """세트 1: 문단마다 공백 정규화 → 문장부호 뒤 공백 → 라벨/괄호를 차례로 적용한다."""
    global _문단글_캐시
    if 중단_요청됨():
        return False
    공백 = stage_enabled(선택_세부작업, 'normalize_space')
    문장부호 = stage_enabled(선택_세부작업, 'punctuation_space')
    괄호 = stage_enabled(선택_세부작업, 'parenthesis') and (괄호_축소_사용 or 괄호_라벨_볼드_사용)
    로그(f"[문단 세트 1] 시작(공백 정규화 {'O' if 공백 else 'X'}, 문장부호 뒤 공백 {'O' if 문장부호 else 'X'}, "
         f"라벨/괄호 {'O' if 괄호 else 'X'})")
    allreplace = 0
    if 공백 and not (한칸표_보호영역 or 쪽범위_사용중()):
        allreplace = 괄호_안쪽_공백_정리_AllReplace()
    규칙들 = (문두_미음_기호_정리, 연도_따옴표_정리_문단_처리, 곧은따옴표_통일_문단_처리, 작은따옴표_통일_문단_처리,
            날짜_구분자_정리_문단_처리, 괄호_안쪽_공백_정리_문단_처리, 쉼표_공백_정리_문단_처리,
            단어사이_연속공백_정리_문단_처리, 공문_띄어쓰기_정리_문단_처리)
    수정 = [0] * len(규칙들)
    문장부호수 = 괄호수 = 방문 = 정체 = 0
    활성_세트_들여쓰기 = None
    _일관성_굵게_적용기호.clear()
    일관성_후보 = []
    _문단글_캐시 = {} if 알파_문단글_캐시_사용 else None
    try:
        순회_시작()
        while True:
            if 중단_요청됨():
                return False
            시작위치 = hwp.GetPos()
            방문 += 1
            if 공백:
                for i, 규칙 in enumerate(규칙들):
                    값 = 규칙() or 0
                    if 값:
                        _문단글_캐시_비우기()
                    수정[i] += 값
            if 문장부호 and 문장부호_뒤_공백_보정_문단_처리():
                문장부호수 += 1
                _문단글_캐시_비우기()
            if 괄호:
                text = 현재문단_텍스트()
                세트후속문단 = False
                if (괄호_라벨_볼드_사용 and 항목기호_굵게_일관성_사용
                        and not 문두_라벨_굵게_제외_문단인가(text)):
                    범위 = 일관성_굵게_머리말_범위(text)
                    if 범위:
                        일관성_후보.append((hwp.GetPos(), text, 범위))
                if 활성_세트_들여쓰기 is not None and 세트문장_후속문단인가(활성_세트_들여쓰기, text):
                    세트후속문단 = True
                else:
                    활성_세트_들여쓰기 = None
                    if 세트문장_시작인가(text):
                        활성_세트_들여쓰기 = 세트문장_선행들여쓰기_폭(text)
                결과 = 괄호_및_라벨_텍스트_문단_처리(세트후속문단=세트후속문단)
                if 결과:
                    괄호수 += 결과
            if not 범위_다음_문단으로_진행():
                break
            if hwp.GetPos() == 시작위치:
                정체 += 1
                if 정체 >= 2:
                    break
            else:
                정체 = 0
    finally:
        _문단글_캐시 = None
    일관성 = 0
    for 위치, text, (시작, 끝) in 일관성_후보:
        if 중단_요청됨():
            return False
        if 항목기호_키(text) not in _일관성_굵게_적용기호:
            continue
        try:
            문단_범위_선택(위치, 시작, 끝)
            문자모양_적용_현재선택(굵게=True)
            hwp_run("Cancel")
            일관성 += 1
        except Exception as e:
            로그(f"항목기호 굵게 일관성 적용 중 오류(무시): {e}")
    로그(f"[문단 세트 1] 완료(방문 문단 {방문}개 / 괄호 AllReplace {allreplace}회 / 공백 규칙 수정 {sum(수정)}건 "
         f"{수정} / 문장부호 뒤 공백 {문장부호수}건 / 라벨·괄호 {괄호수}건 / 굵게 일관성 {일관성}건)")
    return True


def _문단세트_줄순회(시작, 처리):
    """본문 문단 하나의 화면줄마다 처리()를 부른다(기존 본문_기존자간조정·본문_문장부호_처리의 문단 안 부분)."""
    hwp.SetPos(*시작)
    직전 = None
    정체 = 0
    while not 중단_요청됨():
        현재 = hwp.GetPos()
        if 현재[0] != 시작[0] or 현재[1] != 시작[1]:
            return True
        if 현재 == 직전:
            정체 += 1
            if 정체 >= 2:
                return True
        else:
            정체 = 0
        직전 = 현재
        if 처리() is False:
            return False
        hwp_run("MoveLineEnd")
        줄끝 = hwp.GetPos()
        hwp_run("MoveNextChar")
        if hwp.GetPos() == 줄끝:
            return True
    return False


def 문단세트2_배치_적용(문장부호기능=True, 부연설명_단계_사용=False):
    """세트 2: 문단마다 내어쓰기 → 부연설명 → 별표 → 자간·단어 분리 → 짧은 줄 병합(자간이 바뀌면 그 문단만 반복)."""
    global 다음단어_당김_사용
    내어쓰기 = (표준서식_내어쓰기_사용 and stage_enabled(선택_세부작업, 'hanging_indent'))
    별표 = (not 부연설명_단계_사용) and stage_enabled(선택_세부작업, 'star_align')
    자간 = stage_enabled(선택_세부작업, 'body_spacing') or stage_enabled(선택_세부작업, 'word_check')
    줄병합 = stage_enabled(선택_세부작업, 'short_line') and 문장부호기능
    로그(f"[문단 세트 2] 시작(내어쓰기 {'O' if 내어쓰기 else 'X'}, 부연설명 {'O' if 부연설명_단계_사용 else 'X'}, "
         f"별표 {'O' if 별표 else 'X'}, 자간 {'O' if 자간 else 'X'}, 줄 병합 {'O' if 줄병합 else 'X'})")
    붙임번호_대상 = _붙임목록_내어쓰기_대상수집() if 내어쓰기 else {}
    붙임번호_기준점들 = {}
    부연상태, 별표상태 = {'부모': None}, {'별표': None}
    방문 = 반복문단 = 부연수 = 별표수 = 정체 = 0
    내어쓰기_변경문단.clear()
    순회_시작()
    try:
        while True:
            if 중단_요청됨():
                return False
            hwp_run("MoveParaBegin")
            시작 = hwp.GetPos()
            방문 += 1
            text = 현재문단_텍스트()
            한칸표 = 현재_한칸표인가()
            if 내어쓰기 and not 한칸표:
                hwp.SetPos(*시작)
                _내어쓰기_한문단(text, 붙임번호_대상, 붙임번호_기준점들)
            if 부연설명_단계_사용:
                hwp.SetPos(*시작)
                if _부연설명_한문단(시작, text, 부연상태):
                    부연수 += 1
            if 별표:
                hwp.SetPos(*시작)
                if _별표_한문단(시작, text, 별표상태):
                    별표수 += 1
            if 시작[0] == 0 and (자간 or 줄병합):
                hwp.SetPos(*시작)
                if not (쪽범위_안인가(시작) and 재검사_대상인가(시작)) or (
                        _알파_일괄서식_문서 and _알파_한줄문단인가(시작)):
                    pass
                else:
                    for 차수 in range(1, 자간_내어쓰기_최대반복 + 1):
                        if 차수 > 1:
                            다음단어_당김_사용 = False
                            반복문단 += 1
                        변경_전 = 자간_변경_횟수
                        if 자간 and _문단세트_줄순회(시작, 자간자동조정) is False:
                            return False
                        if 줄병합 and _문단세트_줄순회(시작, 문장부호_줄병합_시도) is False:
                            return False
                        if 자간_변경_횟수 == 변경_전 or not 내어쓰기:
                            break
                        # 자간이 첫 줄 폭을 바꾸면 내어쓰기 기준점이 어긋날 수 있어 이 문단만 다시 맞춘다.
                        hwp.SetPos(*시작)
                        _내어쓰기_한문단(현재문단_텍스트(), 붙임번호_대상, 붙임번호_기준점들)
                    다음단어_당김_사용 = True
            hwp.SetPos(*시작)
            if not 범위_다음_문단으로_진행():
                break
            if tuple(hwp.GetPos()) == tuple(시작):
                정체 += 1
                if 정체 >= 2:
                    break
            else:
                정체 = 0
    finally:
        다음단어_당김_사용 = True
    로그(f"[문단 세트 2] 완료(방문 문단 {방문}개 / 부연설명 {부연수}건 / 별표 {별표수}건 / "
         f"자간 변경으로 다시 맞춘 문단 {반복문단}회)")
    return True


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
    별표 = re.match(r"[*＊]+", 벗긴텍스트)
    if 별표:
        return 선행공백_길이 + 별표.end()
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


def 항목기호_역할표():
    """서식 프로필의 항목기호별 역할. 예전 프로필은 '항목기호_역할' 키로 저장했다(용어 변경, 2026-10-10)."""
    return 표준서식_설정.get("항목기호_역할") or 표준서식_설정.get("문두기호_역할") or {}


def 보고서_문단역할(text):
    marker, role = leading_marker(text)
    role = 항목기호_역할표().get(marker, role)
    return role or None


def 보고서_본문묶음_수집(시작위치):
    """본문과 직속 내용·부연설명을 묶고, 소제목은 첫 본문 묶음에 연결한다.

    ㅇ 다음의 - 항목들은 다음 ㅇ/□ 전까지 한 묶음이다. □는 첫 ㅇ 묶음까지만
    연결하므로 여러 ㅇ 묶음을 포함하는 안 전체를 한 쪽으로 강제하지 않는다.
    빈 문단이나 다른 역할·텍스트 영역은 묶음 경계다.
    """
    original = hwp.GetPos()
    try:
        hwp.SetPos(*시작위치)
        hwp_run('MoveParaBegin')
        start = hwp.GetPos()
        role = 보고서_문단역할(현재문단_텍스트())
        if role not in ('소제목', '본문', '내용', '부연설명'):
            return []
        hwp_run('MoveParaEnd')
        result = [(start, hwp.GetPos(), role)]
        body_attached = role == '본문'
        while True:
            if 중단_요청됨():
                return []
            hwp_run('MoveNextParaBegin')
            next_start = hwp.GetPos()
            if next_start[0] != start[0] or next_start[1] <= result[-1][0][1]:
                break
            next_role = 보고서_문단역할(현재문단_텍스트())
            if role == '소제목' and not body_attached and next_role == '본문':
                body_attached = True
            elif next_role == '부연설명':
                pass
            elif body_attached and next_role == '내용':
                pass
            else:
                break
            hwp_run('MoveParaEnd')
            result.append((next_start, hwp.GetPos(), next_role))
        return result
    finally:
        hwp.SetPos(*original)


def 보고서_단어분리_최종검사(컨트롤=False):
    """저장 후 화면줄 경계의 의미 단위 분리를 읽기 전용으로 검사한다."""
    original = hwp.GetPos()
    checked = 0
    issues = []
    # 줄 첫머리부터 넘치는 칸 폭보다 긴 단어는 문제 대신 적용 제외로 적는다.
    exempt = []
    areas = []
    try:
        if 컨트롤:
            area = 2
            while True:
                if 중단_요청됨():
                    return False
                hwp.SetPos(area, 0, 0)
                if hwp.GetPos()[0] != area:
                    break
                if ((not 쪽범위_사용중() or area in 쪽범위_컨트롤영역)
                        and not 표셀_자간_제외인가() and not 숫자_표칸인가()):
                    areas.append(area)
                area += 1
        else:
            areas = [0]
        for area in areas:
            hwp.SetPos(area, 0, 0)
            if area == 0:
                순회_시작()
            seen = set()
            while True:
                if 중단_요청됨():
                    return False
                pos = tuple(hwp.GetPos())
                if pos[0] != area or (area == 0 and 쪽범위_끝지남(pos)):
                    break
                if pos in seen:
                    # 문단 앞 컨트롤 뒤 등에서 MoveLineEnd가 제자리로 돌아오면 같은
                    # 위치를 다시 밟는다. 검사 전체를 실패시키지 말고 다음 문단으로
                    # 넘어간다(실측: 보도자료 (0, 25, 9)에서 검사 중단).
                    진단로그(f'[단어 검수] 같은 위치 반복 {pos}: 다음 문단으로 넘어감')
                    hwp_run('MoveNextParaBegin')
                    moved = tuple(hwp.GetPos())
                    if moved in seen or moved[:2] == pos[:2]:
                        break
                    continue
                seen.add(pos)
                hwp_run('MoveLineEnd')
                boundary = tuple(hwp.GetPos())
                page = 현재_페이지번호()
                hwp_run('MoveParaEnd')
                end = tuple(hwp.GetPos())
                if boundary[:2] != pos[:2] or end[:2] != pos[:2]:
                    raise RuntimeError(f'단어 검수 줄 경계 측정 실패: {pos}')
                if boundary[2] < end[2]:
                    checked += 1
                    info = 단어모드_분리정보(pos)
                    if info and 칸폭보다_긴_단어인가(info):
                        단어모드_범위선택(info[2], info[3])
                        word = 현재선택영역_텍스트()
                        hwp_run('Cancel')
                        exempt.append({'text': f'[칸 폭보다 긴 단어] {word!r}',
                                       'page': page, 'position': pos})
                        hwp.SetPos(*pos)
                    elif info:
                        단어모드_범위선택(info[2], info[3])
                        word = 현재선택영역_텍스트()
                        hwp_run('Cancel')
                        message = f'[저장 결과 단어 분리] {word!r}'
                        issues.append({'text': message, 'page': page, 'position': pos})
                        hwp.SetPos(*pos)
                        검수_문제_기록(현재_처리파일, message)
                hwp.SetPos(*boundary)
                hwp_run('MoveNextChar')
                if tuple(hwp.GetPos()) == boundary:
                    break
        return {'status': 'failed' if issues else 'passed', 'checked': checked,
                'measurement': '화면줄 경계', 'areas': areas, 'issues': issues,
                'exempt': exempt}
    finally:
        hwp_run('Cancel')
        hwp.SetPos(*original)


def 보고서_페이지배치_최종검사():
    """문서를 수정하지 않고 제목 고립과 문단 내부 쪽 분리를 검사한다."""
    original = hwp.GetPos()
    checked = 0
    issues = []
    # 한 쪽에 다 들어갈 수 없는 묶음은 규칙 위반이 아니라 적용 제외로 따로 적는다.
    exempt = []
    표문단 = 본문_표_문단번호()
    본문_쪽나눔_기억(표문단)
    _표칸영역.clear()
    try:
        순회_시작()
        while True:
            if 중단_요청됨():
                return False
            pos = hwp.GetPos()
            # 로마자 중제목 + □ + 첫 ㅇ 단위는 한 쪽에 있어야 한다(중제목_외톨이_정리).
            if pos[0] == 0 and pos[1] in 표문단 and 로마자_중제목_표인가(표문단[pos[1]]):
                다음 = 중제목_다음글문단(pos[1], 표문단)
                묶음 = 중제목_묶음_문단(다음[0]) if 다음 else []
                if 묶음 and all(쪽범위_안인가(p[0]) for p in 묶음):
                    counts, 표쪽 = 중제목_묶음_쪽({'표키': 표문단[pos[1]]}, 묶음)
                    if counts:
                        checked += 1
                        쪽들 = sorted(set(counts) | set(표쪽))
                        if len(쪽들) > 1:
                            message = f'[중제목 묶음 쪽 분리] {다음[1].strip()[:60]}'
                            issues.append({'text': message, 'pages': 쪽들, 'paragraph': pos[1]})
                            검수_문제_기록(현재_처리파일, message)
                hwp.SetPos(*pos)
                if not 범위_다음_문단으로_진행():
                    break
                continue
            text = 현재문단_텍스트()
            # 표 묶음: 제목 문장은 표가 시작하는 쪽에, 주석은 표가 끝나는 쪽에 있어야 한다.
            표묶음 = (보고서_표묶음_수집(pos, 표문단)
                      if 보고서_문단역할(text) in ('소제목', '본문') else None)
            if 표묶음 and all(쪽범위_안인가(p[0]) for p in 표묶음[0]):
                lead, 표항목, notes, 표키 = 표묶음
                lead_counts = 보고서_묶음_쪽별줄수(lead)
                notes_counts = 보고서_묶음_쪽별줄수(notes) if notes else {}
                표쪽 = 표_쪽범위(표키)
                if lead_counts and 표쪽 and notes_counts is not None:
                    checked += 1
                    제목_홀로 = max(lead_counts) < 표쪽[0]
                    주석_홀로 = bool(notes_counts) and min(notes_counts) > 표쪽[1]
                    if 제목_홀로 or 주석_홀로:
                        message = (f'[표 묶음 쪽 분리] {text.strip()[:60]} '
                                   f'({"제목 문장" if 제목_홀로 else "주석"}이 표와 다른 쪽)')
                        issues.append({'text': message, 'pages': sorted(set(lead_counts) | set(표쪽)
                                                                         | set(notes_counts)),
                                       'paragraph': pos[1]})
                        검수_문제_기록(현재_처리파일, message)
                hwp.SetPos(*(notes or [표항목])[-1][0])
                if not 범위_다음_문단으로_진행():
                    break
                continue
            # 논리단위 5개 이하 □ 묶음은 묶음 전체가 한 쪽에 있어야 한다.
            group_target = (소제목묶음_쪽맞춤_대상(pos, 표문단)
                            if 보고서_문단역할(text) == '소제목' else None)
            if group_target and all(쪽범위_안인가(p[0]) for p in group_target[0]):
                counts = 보고서_묶음_쪽별줄수(group_target[0])
                if not counts:
                    raise RuntimeError('최종 페이지 검사의 화면줄 측정 실패')
                checked += 1
                if len(counts) > 1 and 쪽보다_긴_묶음인가(group_target[0], counts):
                    exempt.append({'text': f'[한 쪽보다 긴 묶음] {text.strip()[:80]}',
                                   'pages': sorted(counts), 'paragraph': pos[1]})
                elif len(counts) > 1 and 소제목묶음_단위경계_앞쪽우선(*group_target):
                    exempt.append({'text': f'[ㅇ 단위 경계에서 나눈 소제목 묶음(앞쪽 단위가 많아 밀지 않음)] '
                                           f'{text.strip()[:60]}', 'pages': sorted(counts), 'paragraph': pos[1]})
                elif len(counts) > 1:
                    message = f'[소제목 묶음 쪽 분리] {text.strip()[:80]}'
                    issues.append({'text': message, 'pages': sorted(counts), 'paragraph': pos[1]})
                    검수_문제_기록(현재_처리파일, message)
                hwp.SetPos(*pos)
                if not 범위_다음_문단으로_진행():
                    break
                continue
            paragraphs = 보고서_본문묶음_수집(pos)
            if paragraphs and all(쪽범위_안인가(p[0]) for p in paragraphs):
                counts = 보고서_묶음_쪽별줄수(paragraphs)
                if not counts:
                    raise RuntimeError('최종 페이지 검사의 화면줄 측정 실패')
                checked += 1
                if len(counts) > 1 and 쪽보다_긴_묶음인가(paragraphs, counts):
                    exempt.append({'text': f'[한 쪽보다 긴 묶음] {text.strip()[:80]}',
                                   'pages': sorted(counts), 'paragraph': pos[1]})
                elif counts and len(counts) > 1:
                    kind = ('상위·하위 문단 묶음 분리' if len(paragraphs) > 1
                            else '문단 내부 페이지 분리')
                    message = f'[{kind}] {text.strip()[:80]}'
                    issues.append({'text': message, 'pages': sorted(counts), 'paragraph': pos[1]})
                    검수_문제_기록(현재_처리파일, message)
            hwp.SetPos(*pos)
            if not 범위_다음_문단으로_진행():
                break
        return {'status': 'passed' if not issues else 'failed',
                'checked': checked, 'issues': issues, 'exempt': exempt}
    finally:
        hwp.SetPos(*original)


def 보고서_묶음_쪽별줄수(문단들):
    """문단 개수가 아닌 실제 배치된 화면줄을 페이지별로 센다."""
    original = hwp.GetPos()
    counts = {}
    try:
        for start, end, _ in 문단들:
            hwp.SetPos(*start)
            previous = None
            while True:
                if 중단_요청됨():
                    return None
                hwp_run('MoveLineEnd')
                line_end = hwp.GetPos()
                if line_end[:2] != start[:2] or line_end == previous:
                    raise RuntimeError('묶음의 화면줄 위치 확인 실패')
                page = 현재_페이지번호()
                if page is None:
                    raise RuntimeError('묶음의 페이지 번호 확인 실패')
                counts[page] = counts.get(page, 0) + 1
                if line_end[2] >= end[2]:
                    break
                previous = line_end
                hwp_run('MoveNextChar')
                if hwp.GetPos() == line_end:
                    raise RuntimeError('묶음의 다음 화면줄 이동 실패')
        return counts
    finally:
        hwp.SetPos(*original)


# 줄간격으로 옮기지 못한 묶음을 '문단 앞에서 쪽 나눔'으로 다음 쪽에 보낼 때,
# 앞쪽에 남는 빈 공간이 한 쪽 줄 수의 이 비율 이하일 때만 쪽을 나눈다.
쪽나눔_최대_앞쪽비율 = 0.5


def 쪽_본문줄수(위치):
    """위치가 있는 쪽의 본문 화면줄 수(그 쪽에 들어가는 줄 수의 근사값)."""
    original = hwp.GetPos()
    try:
        hwp.SetPos(*위치)
        page = 현재_페이지번호()
        hwp_run('MovePageBegin')
        count = 0
        while True:
            if 중단_요청됨():
                return None
            hwp_run('MoveLineEnd')
            line_end = hwp.GetPos()
            if line_end[0] != 0 or 현재_페이지번호() != page:
                break
            count += 1
            hwp_run('MoveNextChar')
            if hwp.GetPos() == line_end:
                break
        return count
    finally:
        hwp.SetPos(*original)


def 쪽첫줄_시작인가(시작위치):
    """묶음 첫 문단이 쪽의 첫 줄에서 시작하는지."""
    original = hwp.GetPos()
    try:
        hwp.SetPos(*시작위치)
        hwp_run('MovePageBegin')
        return tuple(hwp.GetPos()) == tuple(시작위치)
    finally:
        hwp.SetPos(*original)


def 쪽보다_긴_묶음인가(문단들, counts):
    """한 쪽에 다 들어갈 수 없는 묶음이면 True. 쪽 배치 규칙을 적용하지 않는다.

    쪽 첫 줄에서 시작하는데도 쪽을 넘거나, 전체 줄 수가 앞쪽(꽉 찬 쪽)의 본문
    줄 수보다 많으면 어떤 배치로도 한 쪽에 모을 수 없다(실측: 34줄 묶음을
    줄간격으로 옮기려다 실패하고 미해결로 남음).
    """
    if not counts or len(counts) < 2:
        return False
    if 쪽첫줄_시작인가(문단들[0][0]):
        return True
    capacity = 쪽_본문줄수(문단들[0][0])
    return bool(capacity) and sum(counts.values()) > capacity


# 결과 문서의 '쪽 나누기'(문단 앞 쪽 나눔)는 모든 작업이 끝난 뒤 저장 직전에 푼다(사용자 지시, 2026-10-09). 남기는 것은
# 두 가지뿐이다: 보고서 경계(제목 표 앞)와, 쪽 배치가 줄간격으로 옮기지 못한 묶음을 다음 쪽에 보내려고 넣은 쪽 나눔
# (사용자 결정, 2026-10-09: 표 제목 문장이 앞쪽에 홀로 남는 것을 막는다). 원문에 있던 쪽 나누기 등은 지운다.
쪽나누기_사용 = True
# 쪽 배치가 묶음을 옮기려고 넣은 쪽 나눔의 본문 문단 번호(저장 직전 해제에서 남긴다).
쪽배치_쪽나눔문단 = set()


def 문서_쪽나누기_전체해제(보존=()):
    """본문 문단의 '문단 앞 쪽 나눔'(쪽 나누기)을 모두 푼다(보존에 든 문단 번호는 둔다). 푼 개수(실패하면 None)."""
    if hwp is None:
        return 0
    원위치 = hwp.GetPos()
    해제 = 0
    try:
        번호 = 0
        while not 중단_요청됨():
            try:
                hwp.SetPos(0, 번호, 0)
            except Exception:
                break
            if tuple(hwp.GetPos()[:2]) != (0, 번호):
                break
            act = hwp.CreateAction('ParagraphShape')
            pset = act.CreateSet()
            act.GetDefault(pset)
            if 번호 not in 보존 and int(pset.Item('PagebreakBefore') or 0):
                쪽나눔_설정((0, 번호, 0), False)
                해제 += 1
            번호 += 1
        return 해제
    except Exception as e:
        로그(f"쪽 나누기 해제 실패(무시): {e}")
        return None
    finally:
        try:
            hwp_run('Cancel')
            hwp.SetPos(*원위치)
        except Exception:
            pass


def 쪽나눔_설정(위치, 켜기):
    hwp.SetPos(*위치)
    act = hwp.CreateAction('ParagraphShape')
    pset = act.CreateSet()
    pset.SetItem('PagebreakBefore', 1 if 켜기 else 0)
    if act.Execute(pset) is False:
        raise RuntimeError('문단 앞 쪽 나눔 설정 실패')


def _묶음_쪽나눔_이동(시작위치, 문단들, counts, summary, 표키=None, 표까지만=False):
    """줄간격으로 옮기지 못한 묶음을 '문단 앞에서 쪽 나눔'으로 다음 쪽에 보낸다.

    앞쪽에 남은 줄이 한 쪽의 쪽나눔_최대_앞쪽비율 이하일 때만 한다(큰 빈 공간
    방지). 옮긴 뒤에도 쪽을 넘으면 되돌린다. 성공 True.
    표키를 주면 표 첫 칸도 같은 쪽이어야 하고, 표까지만=False면 표 끝까지 같은 쪽이어야 한다
    (한 쪽보다 긴 표는 제목 문장이 표 시작과 같은 쪽에 오기만 하면 된다).
    """
    if not 쪽나누기_사용:
        return False
    pages = sorted(counts)
    capacity = 쪽_본문줄수(시작위치)
    if not capacity or counts[pages[0]] > capacity * 쪽나눔_최대_앞쪽비율:
        return False
    original = hwp.GetPos()
    try:
        쪽나눔_설정(시작위치, True)
        new_counts = 보고서_묶음_쪽별줄수(문단들)
        표쪽 = 표_쪽범위(표키) if 표키 is not None else None
        같은쪽 = bool(new_counts) and len(new_counts) == 1
        if 같은쪽 and 표키 is not None:
            쪽 = next(iter(new_counts))
            같은쪽 = bool(표쪽) and 표쪽[0] == 쪽 and (표까지만 or 표쪽[1] == 쪽)
        if 같은쪽:
            if 시작위치[0] == 0:
                쪽배치_쪽나눔문단.add(시작위치[1])
            로그(f'문장 묶음 쪽 나눔으로 다음 쪽 배치: {summary} '
                 f'(앞쪽 {counts[pages[0]]}줄/쪽당 약 {capacity}줄)')
            return True
        쪽나눔_설정(시작위치, False)
        return False
    finally:
        hwp_run('Cancel')
        hwp.SetPos(*original)


def 보고서_압축조건(counts):
    if not counts or len(counts) != 2:
        return False
    pages = sorted(counts)
    return pages[1] == pages[0] + 1 and counts[pages[0]] >= counts[pages[1]]


def 보고서_줄간격_보관(시작, 끝):
    """앞쪽 전체부터 묶음 끝까지 문단별 줄간격 형식/값을 보관한다.

    줄간격은 문단 속성이므로 페이지 경계에 걸친 문단은 문단 전체에
    적용된다. 포인트/고정값 등 비율 이외 줄간격은 변경하지 않는다.
    """
    result = []
    if 시작[0] != 끝[0]:
        raise RuntimeError('페이지와 묶음의 텍스트 영역이 다릅니다.')
    hwp.SetPos(*시작)
    hwp_run('MoveParaBegin')
    while True:
        if 중단_요청됨():
            return None
        pos = hwp.GetPos()
        if pos[0] != 끝[0] or pos[1] > 끝[1]:
            raise RuntimeError('압축 범위 문단 순회 실패')
        pset = hwp.HParameterSet.HParaShape
        hwp.HAction.GetDefault('ParagraphShape', pset.HSet)
        result.append((pos, int(pset.LineSpacingType), int(pset.LineSpacing)))
        if pos[1] == 끝[1]:
            return result
        hwp_run('MoveNextParaBegin')
        if hwp.GetPos()[1] <= pos[1]:
            raise RuntimeError('압축 범위의 다음 문단 이동 실패')


def 보고서_줄간격_적용(보관, 단계, 확대=False):
    percent = hwp.LineSpacingMethod('Percent')
    changed = False
    for pos, kind, value in 보관:
        if kind != percent:
            continue
        if 확대:
            if value >= 세트문장_최대줄간격_퍼센트:
                continue
            target = min(세트문장_최대줄간격_퍼센트, value + 10 * 단계)
        else:
            if value <= 세트문장_최소줄간격_퍼센트:
                continue
            target = max(세트문장_최소줄간격_퍼센트, value - 10 * 단계)
        hwp.SetPos(*pos)
        act = hwp.CreateAction('ParagraphShape')
        pset = act.CreateSet()
        pset.SetItem('LineSpacingType', kind)
        pset.SetItem('LineSpacing', target)
        if act.Execute(pset) is False:
            raise RuntimeError('보고서 묶음 줄간격 적용 실패')
        if target != value:
            changed = True
    return changed


def 보고서_페이지보호_전체해제():
    """작업 범위 안 문단의 '다음 문단과 함께'(KeepWithNext)를 해제한다.

    이어진 문단 묶음이 통째로 다음 쪽으로 밀리면 쪽 배치 판정이 틀어지므로 처리 전과 저장 직전에 푼다.
    한/글의 '문단 보호' 항목 이름은 KeepLinesTogether다(KeepLines는 없는 항목이라 읽으면 None,
    쓰면 무시된다 — 실측 2026-10-01). 문단 보호는 한 문단만 옮기므로 원문 설정을 그대로 둔다.
    """
    original = hwp.GetPos()
    changed = 0
    try:
        순회_시작()
        visited = set()
        while True:
            if 중단_요청됨():
                return False
            hwp_run('MoveParaBegin')
            pos = hwp.GetPos()
            if 쪽범위_끝지남(pos):
                break
            if pos in visited:
                break
            visited.add(pos)
            if pos[0] == 0 and 쪽범위_안인가(pos):
                pset = hwp.HParameterSet.HParaShape
                hwp.HAction.GetDefault('ParagraphShape', pset.HSet)
                if int(getattr(pset, 'KeepWithNext', 0) or 0):
                    act = hwp.CreateAction('ParagraphShape')
                    clear_set = act.CreateSet()
                    clear_set.SetItem('KeepWithNext', 0)
                    if act.Execute(clear_set) is False:
                        raise RuntimeError('최종 문단 페이지 보호 해제 실패')
                    changed += 1
            before = hwp.GetPos()
            hwp_run('MoveNextParaBegin')
            after = hwp.GetPos()
            if after == before or after[0] != 0 or after[1] <= pos[1]:
                break
        로그(f'최종 문단 페이지 보호 해제 완료 ({changed}개 문단)')
        return True
    finally:
        try:
            hwp.SetPos(*original)
        except Exception:
            pass


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


def 쪽맞춤_논리단위(roles):
    """문단 역할 목록을 논리단위(문단 인덱스 목록)로 나눈다."""
    units = []
    for index, role in enumerate(roles):
        if role in ('소제목', '본문') or not units:
            units.append([index])
        else:
            units[-1].append(index)
    return units


def 쪽맞춤_뒤로밀기인가(unit_pages, pages):
    """논리단위 시작 쪽 목록으로 방향을 정한다. 뒤쪽 단위가 더 많을 때만 민다."""
    앞쪽 = sum(1 for page in unit_pages if page == pages[0])
    뒤쪽 = sum(1 for page in unit_pages if page == pages[1])
    return 앞쪽 < 뒤쪽, 앞쪽, 뒤쪽


def 보고서_소제목묶음_수집(시작위치):
    """□ 문단부터 다음 □ 전까지의 ㅇ/-/* 문단을 모은다. □가 아니면 []."""
    original = hwp.GetPos()
    try:
        hwp.SetPos(*시작위치)
        hwp_run('MoveParaBegin')
        start = hwp.GetPos()
        if 보고서_문단역할(현재문단_텍스트()) != '소제목':
            return []
        hwp_run('MoveParaEnd')
        result = [(start, hwp.GetPos(), '소제목')]
        while True:
            if 중단_요청됨():
                return []
            hwp_run('MoveNextParaBegin')
            next_start = hwp.GetPos()
            if next_start[0] != start[0] or next_start[1] <= result[-1][0][1]:
                break
            next_role = 보고서_문단역할(현재문단_텍스트())
            if next_role not in ('본문', '내용', '부연설명'):
                break
            hwp_run('MoveParaEnd')
            result.append((next_start, hwp.GetPos(), next_role))
        return result
    finally:
        hwp.SetPos(*original)


def 문단_첫줄_쪽(start):
    """문단 첫 화면줄이 놓인 쪽 번호."""
    original = hwp.GetPos()
    try:
        hwp.SetPos(*start)
        hwp_run('MoveLineEnd')
        return 현재_페이지번호()
    finally:
        hwp.SetPos(*original)


def 소제목묶음_뒤_표인가(group, 표문단):
    """□ 묶음 바로 뒤(빈 문단 하나 건너뛰어도 됨)에 마지막 ㅇ 단위의 표(로마자 중제목 표 제외)가 오는지."""
    if not 표문단 or not group:
        return False
    번호 = group[-1][0][1] + 1
    if 번호 not in 표문단:
        if 번호 + 1 not in 표문단:
            return False
        original = hwp.GetPos()
        try:
            hwp.SetPos(0, 번호, 0)
            if tuple(hwp.GetPos()[:2]) != (0, 번호) or 현재문단_텍스트().strip():
                return False
        except Exception:
            return False
        finally:
            hwp.SetPos(*original)
        번호 += 1
    return not 로마자_중제목_표인가(표문단[번호])


def 소제목묶음_쪽맞춤_대상(시작위치, 표문단=None):
    """(묶음, 논리단위) 또는 None. 논리단위가 최대 개수를 넘으면 None.

    마지막 ㅇ 단위 뒤에 표가 오면(그 ㅇ는 표의 제목 문장) 표까지 한 쪽에 모아야 하므로 묶음 전체 규칙을 쓰지 않고
    ㅇ 단위·표 묶음 배치에 맡긴다(None). 2026-10-04 실측: 서식 예시 'Ⅱ 추진 계획' 묶음을 1쪽으로 당기자
    'ㅇ (3단계)'만 1쪽, 그 표는 2쪽에 남음 — 사용자 기대는 1쪽에 'ㅇ (2단계)'까지, 2쪽에 'ㅇ (3단계)'와 표.
    """
    group = 보고서_소제목묶음_수집(시작위치)
    if not group:
        return None
    units = 쪽맞춤_논리단위([role for _, _, role in group])
    if len(units) > 쪽맞춤_묶음_최대단위:
        return None
    if 소제목묶음_뒤_표인가(group, 표문단):
        return None
    return group, units


# 줄간격이 이미 최소라 묶음을 앞쪽으로 당기지 못하면, 그 쪽 문단들의 '문단 위 간격'을 원래 값의 10%씩
# 최대 이 비율까지 줄여 당긴다(2026-10-04 실측: 서식 예시 'Ⅱ 추진 계획' 묶음이 '- 입자가속기 …' 한 줄 때문에
# 2쪽으로 밀림). 당기지 못하면 원래 간격으로 되돌린다.
쪽맞춤_위간격_최대축소비율 = 0.5


def _묶음_위간격_축소_당김(보관, paragraphs, target_page, 표키, summary):
    """보관(쪽 시작~묶음 끝 문단) 문단의 문단 위 간격을 줄여 묶음을 target_page로 당긴다.

    성공 True(줄인 간격 유지), 실패 False(원래 간격 복원), 중단·오류 None.
    """
    원래 = []
    for pos, _, _ in 보관:
        hwp.SetPos(*pos)
        값 = 문단_위간격_pt_현재문단()
        if 값 and 값 > 0:
            원래.append((pos, 값))
    if not 원래:
        return False

    def 적용(비율):
        for pos, 값 in 원래:
            hwp.SetPos(*pos)
            hwp_run('MoveParaBegin')
            hwp_run('MoveSelParaEnd')
            문단_위간격_적용_현재선택(round(값 * 비율, 1))
            hwp_run('Cancel')

    단계수 = int(round(쪽맞춤_위간격_최대축소비율 * 10))
    for step in range(1, 단계수 + 1):
        if 중단_요청됨():
            적용(1.0)
            return None
        적용(1 - 0.1 * step)
        세트문장_통계['축소횟수'] = 세트문장_통계.get('축소횟수', 0) + 1
        new_counts = 보고서_묶음_쪽별줄수(paragraphs)
        if new_counts is None:
            적용(1.0)
            return None
        if set(new_counts) == {target_page} and (표키 is None or 표_쪽범위(표키) == (target_page, target_page)):
            로그(f'문장 묶음 {target_page}쪽 배치 완료: {summary} (줄간격 최소라 문단 위 간격 {step * 10}% 축소)')
            return True
    적용(1.0)
    진단로그(f'[문장 묶음] 문단 위 간격 {단계수 * 10}% 축소로도 당기지 못함 / {summary}')
    return False


def _묶음_같은쪽_이동(시작위치, paragraphs, counts, 먼저_확대, summary, 표키=None, 한방향=False):
    """묶음 전체를 두 쪽 중 한 쪽으로 옮긴다.

    먼저_확대로 정한 방향을 먼저 시도하고, 줄간격이 이미 한계값이라
    움직일 수 없거나 실패하면 반대 방향으로 보완한다(한방향=True면 보완하지 않음).
    표키를 주면 그 표의 첫 칸·마지막 칸도 목표 쪽에 있어야 성공이다(표 묶음).
    '성공', '실패'(원래 줄간격 복원), '건너뜀', 중단/오류는 None.
    """
    pages = sorted(counts)
    backup = None
    attempted = False
    success = False
    expand = False
    try:
        hwp.SetPos(*시작위치)
        hwp_run('MovePageBegin')
        page_start = hwp.GetPos()
        if 쪽범위_사용중() and not 쪽범위_안인가(page_start):
            진단로그(f'[문장 묶음] 쪽 시작이 작업 쪽 범위 밖이라 건너뜀 / {summary}')
            return '건너뜀'

        def 방향_시도(expand):
            """성공 True, 실패 False(원래 줄간격 복원), 중단/오류 None."""
            nonlocal backup, attempted, success
            direction = "확대" if expand else "축소"
            target_page = pages[1] if expand else pages[0]
            진단로그(f'[문장 묶음] 쪽별 줄 수 {counts}: {direction}하여 {target_page}쪽으로 이동 / {summary}')
            # 확대는 묶음 앞의 문단만 변경한다. 이동할 묶음 자체는 제외.
            # 페이지 첫 문단에 묶음이 시작하면 확대할 앞부분이 없어 해결 불가.
            backup = 보고서_줄간격_보관(
                page_start, 시작위치 if expand else paragraphs[-1][1])
            if backup is None:
                return None
            if expand:
                backup = [item for item in backup if item[0][1] < 시작위치[1]]
            # 처음 확정한 범위만 변경하며 재배치 후 유입된 문단은 포함하지 않는다.
            for step in range(1, 세트문장_페이지줄간격_최대시도 + 1):
                if 중단_요청됨():
                    return None
                if not 보고서_줄간격_적용(backup, step, 확대=expand):
                    # 이미 최소/최대 줄간격이라 더 바꿀 수 없다.
                    break
                attempted = True
                count_key = '확대횟수' if expand else '축소횟수'
                세트문장_통계[count_key] = 세트문장_통계.get(count_key, 0) + 1
                new_counts = 보고서_묶음_쪽별줄수(paragraphs)
                if new_counts is None:
                    return None
                success = (set(new_counts) == {target_page}
                           and (표키 is None or 표_쪽범위(표키) == (target_page, target_page)))
                if success:
                    로그(f'문장 묶음 {target_page}쪽 배치 완료: {summary} (줄간격 {step}단계 {direction})')
                    return True
            if not expand:
                # 줄간격(최소 한계)으로 못 당기면 줄인 줄간격 위에 문단 위 간격을 더 줄여 본다.
                당김 = _묶음_위간격_축소_당김(backup, paragraphs, target_page, 표키, summary)
                if 당김 is None:
                    return None
                if 당김:
                    success = True
                    return True
            # 페이지 보호 속성은 최종 문서에 남기지 않는다. 줄간격 범위 안에서
            # 해결되지 않으면 원래 값을 복원한다.
            if attempted:
                보고서_줄간격_적용(backup, 0, 확대=expand)
                attempted = False
            진단로그(f'[문장 묶음] {direction} 방향 줄간격 범위 내 이동 불가 / {summary}')
            return False

        for expand in ((먼저_확대,) if 한방향 else (먼저_확대, not 먼저_확대)):
            result = 방향_시도(expand)
            if result is None:
                return None
            if result:
                return '성공'
        return '실패'
    finally:
        try:
            if attempted and not success:
                # 단계 0은 혼합 줄간격을 문단마다 원래 값으로 돌린다.
                보고서_줄간격_적용(backup, 0, 확대=expand)
        finally:
            hwp_run('Cancel')
            hwp.SetPos(*시작위치)


def 소제목묶음_단위경계_앞쪽우선(group, units):
    """두 쪽에 걸친 □ 묶음이 ㅇ 단위 경계에서만 나뉘고 앞쪽 단위가 뒤쪽 이상인지(당기지 못해 단위별로 나눈 결과)."""
    쪽들 = []
    for unit in units:
        counts = 보고서_묶음_쪽별줄수([group[index] for index in unit])
        if not counts or len(counts) != 1:
            return False
        쪽들.append(next(iter(counts)))
    pages = sorted(set(쪽들))
    # 앞쪽에 □와 ㅇ 단위가 하나 이상 함께 있어야 한다(□만 홀로 남은 것은 위반).
    return (len(pages) == 2 and 쪽들.count(pages[0]) >= 2
            and 쪽들.count(pages[0]) >= 쪽들.count(pages[1]))


def 소제목묶음_같은쪽_시도(시작위치, text, 머리=None, 표문단=None):
    """논리단위 5개 이하인 □ 묶음 전체를 한 쪽에 모은다.

    머리(로마자 중제목 {'위치', '표키'})를 주면 중제목 표도 묶음의 맨 앞(첫 단위)으로 보고, 줄간격·쪽 나눔은
    중제목부터 옮긴다(□ 앞에서 쪽을 나누면 중제목만 앞쪽에 남는다. 실측: 서식 예시 'Ⅱ 추진 계획').

    ('처리', 묶음): 이미 한 쪽이거나 옮겼음 — 묶음 안 문단은 다시 보지 않는다.
    ('단위별', 묶음): 대상이 아니거나 옮기지 못함 — ㅇ 단위별 처리로 넘긴다.
    None: 중단/오류.
    """
    summary = text.strip().replace('\r', ' ').replace('\n', ' ')[:50]
    target = 소제목묶음_쪽맞춤_대상(시작위치, 표문단)
    if target is None:
        return '단위별', []
    group, units = target
    if 쪽범위_사용중() and any(not 쪽범위_안인가(item[0]) for item in group):
        return '단위별', group
    counts = 보고서_묶음_쪽별줄수(group)
    if counts is None:
        return None
    이동시작, 표키, 표쪽 = 시작위치, None, None
    if 머리:
        표쪽 = 표_쪽범위(머리['표키'])
        if 표쪽:
            이동시작, 표키 = 머리['위치'], 머리['표키']
            for page in set(표쪽):      # 중제목 표는 한 줄로 센다
                counts[page] = counts.get(page, 0) + 1
    pages = sorted(counts)
    if len(pages) == 1:
        return '처리', group
    if len(pages) != 2 or pages[1] != pages[0] + 1:
        return '단위별', group
    if 쪽보다_긴_묶음인가(group, counts):
        진단로그(f'[쪽 맞춤 묶음] 한 쪽보다 긴 묶음(총 {sum(counts.values())}줄): 묶음 규칙 제외, '
                 f'ㅇ 단위별 배치로 진행 / {summary}')
        return '단위별', group
    unit_pages = []
    for unit in units:
        page = 문단_첫줄_쪽(group[unit[0]][0])
        if page is None:
            return '단위별', group
        unit_pages.append(page)
    # 앞쪽에 □와 함께 남은 ㅇ 단위 수(□만 앞쪽 끝에 홀로 있으면 0)
    앞쪽_ㅇ단위 = sum(1 for page in unit_pages[1:] if page == pages[0])
    if 표쪽 and 표쪽[0] < unit_pages[0]:
        unit_pages.insert(0, 표쪽[0])     # □ 앞쪽에 홀로 남은 중제목도 한 단위로 센다
    먼저_확대, 앞쪽, 뒤쪽 = 쪽맞춤_뒤로밀기인가(unit_pages, pages)
    세트문장_통계['대상'] += 1
    진단로그(f'[쪽 맞춤 묶음] 논리단위 {len(units)}개(앞쪽 {앞쪽}/뒤쪽 {뒤쪽}): '
             f'{"뒤쪽으로 밈" if 먼저_확대 else "앞쪽으로 당김"} / {summary}')
    # 앞쪽 단위가 많아 당기기로 했고 앞쪽에 □와 ㅇ 단위가 함께 있으면 당기기만 한다. 줄간격이 이미 최소라
    # 못 당겨도 묶음 전체를 뒤쪽으로 밀지 않는다 — 앞쪽에 둔 중제목·□·ㅇ가 모두 다음 쪽으로 밀려나 앞쪽이
    # 크게 빈다(2026-10-04 사용자 지적: 서식 예시 'Ⅱ 추진 계획 … ㅇ (2단계)'가 1쪽에 있어야 하는데 2쪽으로
    # 밀림). 이때는 ㅇ 단위 경계에서 나뉘도록 단위별 배치로 넘긴다. □만 앞쪽에 남았으면 예전처럼 민다.
    당김만 = not 먼저_확대 and 앞쪽_ㅇ단위 >= 1
    result = _묶음_같은쪽_이동(이동시작, group, counts, 먼저_확대, summary, 표키=표키, 한방향=당김만)
    if result is None:
        return None
    if result == '성공':
        세트문장_통계['성공'] += 1
        return '처리', group
    if result == '실패' and 당김만:
        세트문장_통계['대상'] -= 1
        로그(f'[쪽 맞춤 묶음] 앞쪽 단위가 많은데 줄간격으로 당기지 못함 — 묶음을 밀지 않고 ㅇ 단위 경계에서 '
             f'나누도록 단위별 배치로 진행: {summary}')
        return '단위별', group
    if result == '실패' and _묶음_쪽나눔_이동(이동시작, group, counts, summary, 표키=표키):
        세트문장_통계['성공'] += 1
        return '처리', group
    if result == '실패':
        세트문장_통계['실패'] += 1
        검수_문제_기록(현재_처리파일, f'[소제목 묶음 쪽 분리] {summary}')
        로그(f'소제목 묶음 배치 미해결(축소·확대 모두 불가) — ㅇ 단위별 배치로 진행: {summary}')
    return '단위별', group


# ---- 표 묶음 쪽 배치 ------------------------------------------------------
# 'ㅇ (세부 추진일정)' + 표 + 표 주석(*, **, ※)은 하나의 묶음이다(실측: 지구 침공계획 보고,
# 제목 문장만 3쪽 끝에 남고 표·주석은 4쪽으로 넘어감). 표가 든 문단은 글자가 없어 역할이
# 없으므로 예전 묶음 수집은 표 앞에서 끊겼고, 표 높이는 본문 줄 수로 잴 수 없다.
# 표의 쪽은 첫 칸과 마지막 칸의 쪽으로 판정한다.
_표칸영역 = {}
# 쪽 나눔(Ctrl+Enter)으로 새 쪽을 시작하는 본문 문단 번호. 표 묶음 판정 전에 본문_쪽나눔_기억()으로 채운다.
_쪽나눔문단 = set()


def 본문_표_문단번호():
    """{본문 문단 번호: 표 키(앵커 위치)}. 본문(리스트 0)에 놓인 표만."""
    result = {}
    try:
        ctrl = hwp.HeadCtrl
        남은수 = 100000   # 컨트롤 목록이 끝나지 않는 비정상 상황 방지
        while ctrl and 남은수 > 0:
            남은수 -= 1
            try:
                if ctrl.CtrlID == 'tbl':
                    anchor = ctrl.GetAnchorPos(0)
                    if anchor.Item('List') == 0:
                        result[anchor.Item('Para')] = (0, anchor.Item('Para'), anchor.Item('Pos'))
            except Exception:
                pass
            ctrl = ctrl.Next
    except Exception as e:
        진단로그(f'본문 표 위치 확인 실패(무시): {e}')
    return result


def 본문_쪽나눔_기억(표문단):
    """지금 문서에서 쪽 나눔으로 새 쪽을 시작하는 본문 문단 번호를 _쪽나눔문단에 기억한다.

    한/글 문단 모양에는 이 쪽 나눔이 보이지 않으므로(PagebreakBefore=0, 실측: 10월 확대간부회의
    자료) 지금 문서의 HWPX 원본에서 본문 직속 문단의 pageBreak를 읽는다. HWPX의 표 문단 번호가
    한/글의 본문 표 문단 번호와 다르면(저장 뒤 문단이 바뀜) 번호가 어긋나므로 쓰지 않는다.
    """
    _쪽나눔문단.clear()
    문서경로 = _서식통일_현재_HWPX()
    if 문서경로 is None or not 표문단:
        return
    try:
        from docfit_core.style_inventory import _sections
        문단들 = []
        with zipfile.ZipFile(문서경로) as archive:
            for name in _sections(archive):
                문단들.extend(p for p in safe_xml_fromstring(archive.read(name)) if 제목_xml이름(p) == 'p')
    except Exception as e:
        진단로그(f'쪽 나눔 위치 확인 실패(무시): {e}')
        return
    표번호 = {i for i, p in enumerate(문단들)
              if any(제목_xml이름(x) == 'tbl' for run in p if 제목_xml이름(run) == 'run' for x in run)}
    if 표번호 != set(표문단):
        진단로그('쪽 나눔 위치 확인 생략: 저장된 HWPX와 지금 문서의 표 위치가 다름')
        return
    _쪽나눔문단.update(i for i, p in enumerate(문단들) if p.get('pageBreak') == '1')


def 표_칸영역_범위(표키):
    """표 칸 목록 번호의 (처음, 끝). 처음 부를 때 문서의 표 칸을 한 번 훑어 기억한다."""
    if not _표칸영역:
        original = hwp.GetPos()
        try:
            area = 2
            while not 중단_요청됨():
                try:
                    hwp.SetPos(area, 0, 0)
                except Exception:
                    break
                if hwp.GetPos()[0] != area:
                    break
                키 = 현재_표_키()
                if 키:
                    처음, 끝 = _표칸영역.get(키, (area, area))
                    _표칸영역[키] = (min(처음, area), max(끝, area))
                area += 1
        finally:
            hwp.SetPos(*original)
    return _표칸영역.get(tuple(표키)) if 표키 is not None else None


def 표_쪽범위(표키):
    """표 첫 칸 시작과 마지막 칸 끝이 놓인 (첫 쪽, 끝 쪽). 모르면 None."""
    범위 = 표_칸영역_범위(표키)
    if not 범위:
        return None
    original = hwp.GetPos()
    try:
        hwp.SetPos(범위[0], 0, 0)
        첫쪽 = 현재_페이지번호()
        hwp.SetPos(범위[1], 0, 0)
        hwp_run('MoveListEnd')
        끝쪽 = 현재_페이지번호()
        return (첫쪽, 끝쪽) if 첫쪽 and 끝쪽 else None
    except Exception:
        return None
    finally:
        hwp.SetPos(*original)


def 보고서_표묶음_수집(시작위치, 표문단):
    """(제목 문장 묶음, 표 문단 위치, 주석 문단들, 표 키) 또는 None.

    제목 문장 묶음(□ 또는 ㅇ와 딸린 -·*) 바로 뒤에 표가 오면 표와, 표 바로 뒤의
    부연설명(*, **, ※)까지 한 묶음이다. 사이의 빈 문단 하나는 묶음에 넣는다.
    """
    if not 표문단:
        return None
    lead = 보고서_본문묶음_수집(시작위치)
    if not lead:
        return None
    original = hwp.GetPos()

    def 문단(번호):
        """(시작, 끝, 글자) 또는 None."""
        try:
            hwp.SetPos(0, 번호, 0)
        except Exception:
            return None
        if tuple(hwp.GetPos()[:2]) != (0, 번호):
            return None
        start = hwp.GetPos()
        text = 현재문단_텍스트()
        hwp.SetPos(*start)
        hwp_run('MoveParaEnd')
        return start, hwp.GetPos(), text

    try:
        번호 = lead[-1][0][1] + 1
        사이빈줄 = []
        if 번호 not in 표문단:
            빈 = 문단(번호)
            if not 빈 or 빈[2].strip() or 번호 + 1 not in 표문단:
                return None
            사이빈줄.append((빈[0], 빈[1], '빈 줄'))
            번호 += 1
        # 쪽 나눔으로 새 쪽에서 시작하는 표(다음 보고서의 제목 표 등)는 앞 문장과 한 쪽에 놓일 수 없다.
        if any(n in _쪽나눔문단 for n in range(lead[-1][0][1] + 1, 번호 + 1)):
            return None
        # 처리 중에 넣은 보고서 경계 쪽 나누기는 저장된 HWPX(_쪽나눔문단)에 없으므로 지금 문서에서도 본다.
        # 보고서 제목 표는 쪽 나눔이 없어도 앞 보고서 문장의 표가 아니다(2026-10-09 실측: 오판정 3건).
        if 번호 in 쪽맞춤_제목문단 or 쪽나눔_켜짐((0, 번호, 0)):
            hwp.SetPos(*original)
            return None
        표 = 문단(번호)
        if not 표 or 표[2].strip():
            return None      # 표 옆에 글자가 있는 문단은 표 묶음으로 보지 않는다.
        if 로마자_중제목_표인가(표문단[번호]):
            return None      # 로마자 중제목 표는 앞 문장의 표가 아니라 다음 □ 묶음의 머리다(중제목_외톨이_정리).
        표항목 = (표[0], 표[1], '표')
        notes = []
        다음 = 번호 + 1
        while not 중단_요청됨():
            item = 문단(다음)
            if not item:
                break
            role = 보고서_문단역할(item[2]) if item[2].strip() else None
            if role == '부연설명':
                notes.append((item[0], item[1], role))
            elif not item[2].strip() and 다음 not in 표문단 and not notes:
                뒤 = 문단(다음 + 1)
                if not 뒤 or 보고서_문단역할(뒤[2]) != '부연설명':
                    break
                notes.append((item[0], item[1], '빈 줄'))
            else:
                break
            다음 += 1
        return lead + 사이빈줄, 표항목, notes, 표문단[번호]
    finally:
        hwp.SetPos(*original)


def 표묶음_같은쪽_시도(시작위치, text, 표문단):
    """제목 문장 + 표 + 주석 묶음을 배치한다. 표 묶음이 아니면 None, 처리했으면 묶음 끝 위치,
    중단·오류면 False.

    - 묶음이 한 쪽에 들어가면 표가 시작하는 쪽에 모은다. 제목 문장만 앞쪽에 남았으면 뒤로 밀고
      (줄간격 확대 → 안 되면 제목 앞 쪽 나눔), 표는 앞쪽에 있고 주석만 넘쳤으면 앞으로 당긴다.
    - 표가 한 쪽보다 길면 표가 쪽을 넘는 것은 두되, 제목 문장이 표 시작과 다른 쪽에 홀로
      남지 않게 한다. 표가 앞쪽에서 시작했으면 앞쪽을 크게 비우는 쪽 나눔은 하지 않는다.
    """
    묶음 = 보고서_표묶음_수집(시작위치, 표문단)
    if 묶음 is None:
        return None
    lead, 표항목, notes, 표키 = 묶음
    끝위치 = (notes or [표항목])[-1][0]
    summary = text.strip().replace('\r', ' ').replace('\n', ' ')[:50]
    전체 = lead + [표항목] + notes
    if 쪽범위_사용중() and any(not 쪽범위_안인가(item[0]) for item in 전체):
        진단로그(f'[표 묶음] 작업 쪽 범위 밖으로 이어져 건너뜀 / {summary}')
        return 끝위치
    글문단 = lead + [item for item in notes if item[2] != '빈 줄']
    lead_counts = 보고서_묶음_쪽별줄수(lead)
    notes_counts = 보고서_묶음_쪽별줄수(notes) if notes else {}
    표쪽 = 표_쪽범위(표키)
    if lead_counts is None or notes_counts is None or not 표쪽:
        진단로그(f'[표 묶음] 쪽 측정 실패로 건너뜀 / {summary}')
        return 끝위치
    tf, tl = 표쪽
    쪽들 = set(lead_counts) | {tf, tl} | set(notes_counts)
    if len(쪽들) == 1:
        return 끝위치
    제목끝쪽 = max(lead_counts)
    세트문장_통계['대상'] += 1
    진단로그(f'[표 묶음] 제목 {sorted(lead_counts)}쪽 · 표 {tf}~{tl}쪽 · 주석 {sorted(notes_counts) or "-"}쪽 '
             f'/ {summary}')
    앞쪽 = min(쪽들)
    결과 = '실패'
    if len(쪽들) == 2 and max(쪽들) == 앞쪽 + 1:
        counts = {앞쪽: 1, 앞쪽 + 1: 1}
        # 표가 앞쪽에서 시작해 끝나고 주석만 넘쳤으면 앞으로 당기고, 그 밖에는 뒤로 민다.
        당김 = tf == tl == 앞쪽 and notes_counts and min(notes_counts) > 앞쪽
        결과 = _묶음_같은쪽_이동(lead[0][0], 글문단, counts, not 당김, summary, 표키=표키,
                             한방향=not 당김 and tf == 앞쪽)
        if 결과 is None:
            return False
        if 결과 == '실패' and tf > 앞쪽:
            # 제목 문장만 앞쪽 끝에 남은 경우: 제목 앞에서 쪽을 나눠 표와 함께 보낸다.
            if _묶음_쪽나눔_이동(lead[0][0], 글문단, lead_counts, summary, 표키=표키):
                결과 = '성공'
    if 결과 != '성공' and 제목끝쪽 < tf:
        # 한 쪽에 다 모으지 못해도 제목 문장이 표와 다른 쪽에 홀로 남지는 않게 한다.
        if _묶음_쪽나눔_이동(lead[0][0], lead, lead_counts, summary, 표키=표키, 표까지만=True):
            로그(f'[표 묶음] 표보다 길어 한 쪽에 모으지 못함 — 제목 문장을 표 시작 쪽으로 옮김: {summary}')
            결과 = '성공'
    if 결과 == '성공':
        세트문장_통계['성공'] += 1
    else:
        세트문장_통계['실패'] += 1
        검수_문제_기록(현재_처리파일, f'[표 묶음 쪽 분리] {summary} (제목 {sorted(lead_counts)}쪽, '
                              f'표 {tf}~{tl}쪽, 주석 {sorted(notes_counts) or "-"}쪽)')
        로그(f'표 묶음 배치 미해결 — 원래 줄간격 유지: {summary}')
    return 끝위치


def 세트문장_같은쪽_시도(시작위치, text):
    """문단 하나의 쪽별 줄 수를 비교해 앞쪽으로 당기거나 뒤쪽으로 민다."""
    if 중단_요청됨():
        return False
    if 보고서_문단역할(text) not in ('소제목', '본문', '내용', '부연설명'):
        return True
    summary = text.strip().replace('\r', ' ').replace('\n', ' ')[:50]
    paragraphs = 보고서_본문묶음_수집(시작위치)
    if not paragraphs:
        return not 중단_요청됨()
    if 쪽범위_사용중() and any(not 쪽범위_안인가(item[0]) for item in paragraphs):
        # 묶음이 작업 쪽 범위 밖까지 이어지면 범위 밖 문단의 줄간격을 건드리게 되므로 건너뛴다.
        진단로그(f'[문장 묶음] 작업 쪽 범위 밖으로 이어져 건너뜀 / {summary}')
        return not 중단_요청됨()
    counts = 보고서_묶음_쪽별줄수(paragraphs)
    pages = sorted(counts) if counts else []
    if len(pages) == 1:
        return not 중단_요청됨()
    if len(pages) != 2 or pages[1] != pages[0] + 1:
        진단로그(f'[문장 묶음] 인접한 두 쪽 조건 미충족: 쪽별 줄 수 {counts} / {summary}')
        if len(pages) > 1:
            검수_문제_기록(현재_처리파일, f'[문장 묶음 페이지 분리] {summary}')
        return not 중단_요청됨()
    if 쪽보다_긴_묶음인가(paragraphs, counts):
        진단로그(f'[문장 묶음] 한 쪽보다 긴 묶음(총 {sum(counts.values())}줄): 쪽 배치 제외 / {summary}')
        return not 중단_요청됨()
    세트문장_통계['대상'] += 1
    # 쪽별 줄 수로 정한 방향을 먼저 시도하고, 안 되면 반대 방향으로 보완한다.
    # 예: 앞쪽 4줄/뒤쪽 1줄이지만 줄간격이 이미 최소(160%)라 당길 수
    # 없으면, 앞 문단들의 줄간격을 넓혀 묶음 전체를 뒤쪽으로 민다.
    result = _묶음_같은쪽_이동(시작위치, paragraphs, counts,
                             not 보고서_압축조건(counts), summary)
    if result is None:
        return False
    if result == '실패' and _묶음_쪽나눔_이동(시작위치, paragraphs, counts, summary):
        result = '성공'
    if result == '성공':
        세트문장_통계['성공'] += 1
    elif result == '실패':
        세트문장_통계['실패'] += 1
        검수_문제_기록(현재_처리파일, f'[문장 묶음 페이지 분리] {summary}')
        로그(f'문장 묶음 배치 미해결(축소·확대 모두 불가) — 원래 줄간격 복원: {summary}')
    return True


# ---- 로마자 중제목 쪽 배치 ---------------------------------------------------
# 'Ⅰ | 추진 배경' 같은 로마자 중제목 표는 뒤따르는 □ 소제목의 머리다. 중제목 + □ + 첫 ㅇ(딸린 -·*까지)은
# 쪼갤 수 없는 하나의 논리 묶음이므로 한 쪽에 둔다(2026-10-04 사용자 요청, 실측: 서식 예시 1쪽 마지막 줄에
# 'Ⅱ 추진 계획'만 남음). 뒤 □ 묶음과 첫 ㅇ 단위의 쪽 배치가 끝난 뒤 이 묶음이 두 쪽에 걸쳤으면, 소제목처럼
# 줄간격으로 당기거나 밀고, 안 되면 중제목 앞에서 쪽을 나눈 뒤 □ 묶음을 다시 배치한다.
_로마자_중제목_번호 = re.compile(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ]+\.?$|^[IVX]{1,5}\.?$")


def 로마자_중제목_표인가(표키):
    """본문 표가 1행 2~3칸이고 첫 칸 글이 로마자 번호(Ⅰ, Ⅱ …)뿐인 중제목 표인지."""
    범위 = 표_칸영역_범위(표키)
    if not 범위 or not 2 <= 범위[1] - 범위[0] + 1 <= 3:
        return False
    original = hwp.GetPos()
    try:
        hwp.SetPos(범위[0], 0, 0)
        if hwp.GetPos()[0] != 범위[0]:
            return False
        return bool(_로마자_중제목_번호.match(현재문단_텍스트().strip()))
    except Exception:
        return False
    finally:
        hwp.SetPos(*original)


def 중제목_다음글문단(표문단번호, 표문단):
    """중제목 표 뒤 첫 글 문단의 (시작 위치, 글). 사이 빈 문단은 건너뛰고, 표·끝이면 None."""
    original = hwp.GetPos()
    try:
        for 번호 in range(표문단번호 + 1, 표문단번호 + 4):
            if 번호 in 표문단:
                return None
            try:
                hwp.SetPos(0, 번호, 0)
            except Exception:
                return None
            if tuple(hwp.GetPos()[:2]) != (0, 번호):
                return None
            start = hwp.GetPos()
            text = 현재문단_텍스트()
            if text.strip():
                return start, text
        return None
    finally:
        hwp.SetPos(*original)


def 쪽나눔_켜짐(위치):
    """위치 문단에 '문단 앞에서 쪽 나눔'이 켜져 있는지."""
    original = hwp.GetPos()
    try:
        hwp.SetPos(*위치)
        pset = hwp.HParameterSet.HParaShape
        hwp.HAction.GetDefault('ParagraphShape', pset.HSet)
        return bool(int(getattr(pset, 'PagebreakBefore', 0) or 0))
    except Exception:
        return False
    finally:
        hwp.SetPos(*original)


def 중제목_묶음_문단(다음위치):
    """중제목과 한 쪽에 있어야 하는 글 문단들: □ + 첫 ㅇ 단위(딸린 -·*). □가 아니면 그 문단의 묶음."""
    group = 보고서_소제목묶음_수집(다음위치)
    if group:
        units = 쪽맞춤_논리단위([role for _, _, role in group])
        return group[:units[min(1, len(units) - 1)][-1] + 1]
    return 보고서_본문묶음_수집(다음위치) or []


def 중제목_묶음_쪽(중제목, 문단들):
    """(묶음 글 문단의 쪽별 줄 수, 중제목 표 쪽 범위). 재지 못하면 (None, None)."""
    counts = 보고서_묶음_쪽별줄수(문단들) if 문단들 else None
    표쪽 = 표_쪽범위(중제목['표키'])
    return (counts, 표쪽) if counts and 표쪽 else (None, None)


def 중제목_외톨이_정리(중제목):
    """중제목 + □ + 첫 ㅇ 단위가 두 쪽에 걸쳤으면 한 쪽에 모은다. 옮겼으면 True, 중단·오류는 None.

    소제목 묶음처럼 앞쪽 줄이 더 많으면 줄간격을 줄여 당기고, 아니면 앞 문단 줄간격을 넓혀 민다.
    안 되면 중제목 앞에서 쪽을 나눈다(뒤 □에 쪽 나눔이 있었으면 중제목으로 옮긴다).
    """
    문단들 = 중제목_묶음_문단(중제목['다음'])
    counts, 표쪽 = 중제목_묶음_쪽(중제목, 문단들)
    if counts is None:
        return False
    쪽들 = set(counts) | set(표쪽)
    if len(쪽들) == 1:
        return False
    if 쪽범위_사용중() and not all(쪽범위_안인가(item[0]) for item in [(중제목['위치'],)] + 문단들):
        return False
    summary = 중제목['요약']
    세트문장_통계['대상'] += 1
    앞쪽 = min(쪽들)
    original = hwp.GetPos()
    # 뒤 □가 이미 '문단 앞 쪽 나눔'으로 다음 쪽에 갔으면 그 쪽 나눔부터 푼다
    # (둘 다 켜면 □가 한 쪽 더 밀린다. 실측: 서식 예시 'Ⅱ 추진 계획').
    글쪽나눔 = 쪽나눔_켜짐(중제목['다음'])
    성공 = False
    try:
        if 글쪽나눔:
            쪽나눔_설정(중제목['다음'], False)
            hwp_run('Cancel')
            counts, 표쪽 = 중제목_묶음_쪽(중제목, 문단들)
            if counts is None:
                return False
            쪽들 = set(counts) | set(표쪽)
            앞쪽 = min(쪽들)
            성공 = len(쪽들) == 1
        if not 성공 and len(쪽들) == 2 and max(쪽들) == 앞쪽 + 1:
            앞줄 = counts.get(앞쪽, 0) + (1 if 표쪽[0] == 앞쪽 else 0)
            뒷줄 = counts.get(앞쪽 + 1, 0) + (1 if 표쪽[1] == 앞쪽 + 1 else 0)
            결과 = _묶음_같은쪽_이동(중제목['위치'], 문단들, {앞쪽: 1, 앞쪽 + 1: 1}, 앞줄 < 뒷줄, summary,
                                 표키=중제목['표키'])
            if 결과 is None:
                return None
            성공 = 결과 == '성공'
            if not 성공:
                성공 = _묶음_쪽나눔_이동(중제목['위치'], 문단들, {앞쪽: 앞줄, 앞쪽 + 1: 뒷줄}, summary,
                                     표키=중제목['표키'])
        if 성공:
            세트문장_통계['성공'] += 1
            로그(f'[중제목 쪽 배치] 중제목·□·첫 ㅇ 묶음을 한 쪽에 모음: {summary}')
            return True
        if 글쪽나눔:
            쪽나눔_설정(중제목['다음'], True)
            hwp_run('Cancel')
        세트문장_통계['실패'] += 1
        검수_문제_기록(현재_처리파일, f'[중제목 묶음 쪽 분리] {summary}')
        return False
    finally:
        hwp.SetPos(*original)


def 세트문장_같은쪽_전체_적용():
    if not 세트문장_같은쪽_사용:
        return True
    if 중단_요청됨():
        return False

    로그("문장부호 세트문장 동일 페이지 유지 처리 시작")
    # 표 묶음(제목 문장 + 표 + 주석) 판정용: 본문에 놓인 표의 문단 번호. 표 칸 범위는 새로 잰다.
    표문단 = 본문_표_문단번호()
    본문_쪽나눔_기억(표문단)
    _표칸영역.clear()
    순회_시작()
    대기_중제목 = None      # 뒤 □ 묶음 배치가 끝나면 외톨이인지 볼 로마자 중제목
    중제목_머리 = {}         # □ 문단 번호 → 그 □의 머리인 로마자 중제목(□ 묶음 배치를 중제목부터 한다)

    while True:
        if 중단_요청됨():
            return False

        시작위치 = hwp.GetPos()
        # 본문(리스트 0) 문단만 대상으로 한다. 표/글상자 등은 기존 컨트롤 처리와 충돌하지 않게 제외한다.
        if 시작위치[0] == 0 and 시작위치[1] in 표문단 and 로마자_중제목_표인가(표문단[시작위치[1]]):
            다음 = 중제목_다음글문단(시작위치[1], 표문단)
            묶음 = 중제목_묶음_문단(다음[0]) if 다음 else []
            if 묶음:
                대기_중제목 = {'위치': (0, 시작위치[1], 0), '표키': 표문단[시작위치[1]], '다음': 다음[0],
                          '끝문단': 묶음[-1][0][1],
                          '요약': 다음[1].strip().replace('\r', ' ').replace('\n', ' ')[:30]}
                중제목_머리[다음[0][1]] = 대기_중제목
        elif 시작위치[0] == 0:
            text = 현재문단_텍스트()
            role = 보고서_문단역할(text)
            처리됨 = False
            if role in ('소제목', '본문'):
                끝위치 = 표묶음_같은쪽_시도(시작위치, text, 표문단)
                if 끝위치 is False:
                    return False
                if 끝위치 is not None:
                    # 표 묶음 안의 문단(표·주석)은 다시 보지 않는다.
                    hwp.SetPos(*끝위치)
                    처리됨 = True
            if not 처리됨 and role == '소제목':
                result = 소제목묶음_같은쪽_시도(시작위치, text, 중제목_머리.get(시작위치[1]), 표문단)
                if result is None:
                    return False
                상태값, group = result
                if 상태값 == '처리' and group:
                    # 묶음 전체가 한 쪽에 있으므로 안의 ㅇ 단위는 다시 보지 않는다.
                    hwp.SetPos(*group[-1][0])
                    처리됨 = True
            if not 처리됨 and role in ('소제목', '본문', '내용', '부연설명'):
                if 세트문장_같은쪽_시도(시작위치, text) is False:
                    return False
                try:
                    hwp.SetPos(*시작위치)
                except Exception:
                    pass
            # □ 묶음과 첫 ㅇ 단위의 배치가 끝나면(묶음 끝 문단까지 왔으면) 중제목 묶음을 본다.
            if 대기_중제목 and max(시작위치[1], hwp.GetPos()[1]) >= 대기_중제목['끝문단']:
                중제목 = 대기_중제목
                대기_중제목 = None
                결과 = 중제목_외톨이_정리(중제목)
                if 결과 is None:
                    return False
                # 중제목을 옮기면 뒤 □ 묶음이 중제목 높이만큼 밀리므로 그 묶음을 한 번 더 배치한다.
                if 결과:
                    hwp.SetPos(*중제목['다음'])
                    continue

        if not 범위_다음_문단으로_진행():
            break

    로그(
        "문장부호 세트문장 동일 페이지 유지 완료 "
        f"(대상 {세트문장_통계['대상']} / 성공 {세트문장_통계['성공']} / "
        f"미해결 {세트문장_통계['실패']} / 줄간격 축소 {세트문장_통계['축소횟수']}회, 확대 {세트문장_통계.get('확대횟수', 0)}회)"
    )
    return True


def 마지막쪽_화면줄수():
    """문서 끝이 있는 쪽 번호와, 그 쪽에 걸린 화면줄 수를 반환한다.

    실패하면 (None, None). 본문(리스트 0)만 대상으로 한다 — 표/글상자
    안 텍스트는 별도 리스트라 MovePageBegin 등 쪽 이동 명령이 기대한
    대로 동작하지 않는다.
    """
    if hwp is None:
        return None, None
    원위치 = hwp.GetPos()
    try:
        hwp_run('MoveDocEnd')
        문서끝 = hwp.GetPos()
        if 문서끝[0] != 0:
            return None, None
        마지막쪽 = 현재_페이지번호()
        if 마지막쪽 is None:
            return None, None
        hwp.SetPos(*문서끝)
        hwp_run('MovePageBegin')
        줄수 = 0
        이전줄끝 = None
        while True:
            if 중단_요청됨():
                return None, None
            hwp_run('MoveLineEnd')
            줄끝 = hwp.GetPos()
            if 줄끝 == 이전줄끝:
                break
            줄수 += 1
            if (줄끝[1], 줄끝[2]) >= (문서끝[1], 문서끝[2]):
                break
            이전줄끝 = 줄끝
            hwp_run('MoveNextChar')
            if hwp.GetPos() == 줄끝:
                break
        return 마지막쪽, 줄수
    except Exception as e:
        로그(f"마지막 쪽 줄 수 확인 실패(무시): {e}")
        return None, None
    finally:
        try:
            hwp.SetPos(*원위치)
        except Exception:
            pass


# 페이지 수 맞춤 소요 시간 계측(2026-10-08). 동작은 바꾸지 않고, 쪽 수 맞춤이 도는 동안만
# 구간별 (누적 초, 건수)를 모아 단계마다 한 줄, 끝에 합계 한 줄을 작업 로그에 남긴다.
# 실측: 15쪽 문서의 쪽 수 맞춤이 실패까지 5분 21초(전체의 85%) 걸렸는데 구간별 시간을 몰랐다.
쪽맞춤_계측값 = None


def 쪽맞춤_계측_시작():
    global 쪽맞춤_계측값
    쪽맞춤_계측값 = {}


def 쪽맞춤_계측_끝():
    global 쪽맞춤_계측값
    값, 쪽맞춤_계측값 = 쪽맞춤_계측값, None
    return 값 or {}


def 쪽맞춤_계측_더하기(키, 초, 건수=0):
    if 쪽맞춤_계측값 is None:
        return
    누적 = 쪽맞춤_계측값.setdefault(키, [0.0, 0])
    누적[0] += 초
    누적[1] += 건수


def 쪽맞춤_계측_복사():
    return {키: list(v) for 키, v in (쪽맞춤_계측값 or {}).items()}


def 쪽맞춤_계측_차이(이전):
    """이전 복사본 이후에 쌓인 (초, 건수)."""
    차이 = {}
    for 키, (초, 건수) in (쪽맞춤_계측값 or {}).items():
        앞초, 앞건수 = (이전 or {}).get(키, (0.0, 0))
        차이[키] = (초 - 앞초, 건수 - 앞건수)
    return 차이


def 쪽맞춤_계측_단계문구(이름, 회, 차이, 단계초, 마지막쪽):
    초 = lambda k: 차이.get(k, (0.0, 0))[0]
    건 = lambda k: 차이.get(k, (0.0, 0))[1]
    표기타 = max(0.0, 초('표합계') - 초('표스캔') - 초('표셀읽기') - 초('표셀쓰기'))
    return (
        f"[쪽 수 맞춤 계측] {이름} {회}단계: "
        f"문단 간격 {초('문단합계'):.1f}초(순회 {초('문단순회'):.1f} + 쓰기 {초('문단쓰기'):.1f}, 훑은 문단 {건('문단순회')}개·바꾼 {건('문단쓰기')}곳) / "
        f"표 여백 {초('표합계'):.1f}초(표 스캔 {초('표스캔'):.1f} + 셀 읽기 {초('표셀읽기'):.1f} + 셀 쓰기 {초('표셀쓰기'):.1f} + 기타 {표기타:.1f}, "
        f"읽은 셀 {건('표셀읽기')}개·바꾼 {건('표셀쓰기')}개) / "
        f"쪽 측정 {초('쪽측정'):.1f}초 → 단계 합계 {단계초:.1f}초, 현재 {마지막쪽}쪽"
    )


def 쪽맞춤_계측_합계문구(값, 전체초, 결과):
    # 고속 방식은 '문단합계'·'표합계'를 따로 재지 않으므로 세부 구간의 합으로 채운다.
    값 = dict(값)
    for 합계, 세부 in (('문단합계', ('문단순회', '문단쓰기')), ('표합계', ('표스캔', '표셀읽기', '표셀쓰기'))):
        세부합 = sum(값.get(k, (0.0, 0))[0] for k in 세부)
        if 값.get(합계, (0.0, 0))[0] < 세부합:
            값[합계] = (세부합, 값.get(합계, (0.0, 0))[1])
    초 = lambda k: 값.get(k, (0.0, 0))[0]
    건 = lambda k: 값.get(k, (0.0, 0))[1]
    알려진 = sum(초(k) for k in ('문단합계', '표합계', '쪽측정', '묶음검사', '원복'))
    return (
        f"[쪽 수 맞춤 계측 합계] 총 {전체초:.1f}초, 결과 {'성공' if 결과 else '실패/원복'}, 쪽 측정 {건('쪽측정')}회 / "
        f"문단 간격 {초('문단합계'):.1f}초(순회 {초('문단순회'):.1f} + 쓰기 {초('문단쓰기'):.1f}) / "
        f"표 여백 {초('표합계'):.1f}초(스캔 {초('표스캔'):.1f} + 셀 읽기 {초('표셀읽기'):.1f} + 셀 쓰기 {초('표셀쓰기'):.1f}) / "
        f"쪽 측정 {초('쪽측정'):.1f}초 / 묶음 검사 {초('묶음검사'):.1f}초({건('묶음검사')}회) / "
        f"원복·재적용 {초('원복'):.1f}초 / 위에 없는 시간 {max(0.0, 전체초 - 알려진):.1f}초"
    )


def 문단_위간격_pt_현재문단():
    """현재 캐럿이 있는 문단의 '문단 위 간격' 값을 pt로 읽는다."""
    if hwp is None:
        return None
    try:
        return HwpUnit_pt(hwp.ParaShape.Item("PrevSpacing")) / 2      # COM은 실제 HWPUNIT의 두 배
    except Exception as e:
        로그(f"문단 위 간격 읽기 실패(무시): {e}")
        return None


def 구조문단_간격_일괄조정(delta_pt, 최소쪽=None, 위간격=False, 원래값=None):
    """문서 전체(본문 리스트만)에서 항목기호(□/ㅇ/-/*/※/• 등)로 시작하는
    문단의 '문단 아래 간격'(위간격이면 '문단 위 간격')을 delta_pt만큼
    조정한다(0pt 아래로는 내려가지 않음). 본문 줄간격은 건드리지 않는다.
    실제로 값이 바뀐 문단 수를 반환한다.

    원래값(dict)을 주면 처음 바꾸는 문단의 원래 pt를 (리스트, 문단) 번호로
    기록해 구조문단_간격_복원으로 되돌릴 수 있게 한다.

    최소쪽을 주면 그 이전 쪽의 문단은 손대지 않는다 — 페이지 수 맞춤은
    항상 마지막 몇 쪽만 조정하면 충분한데, 문단마다 현재문단_텍스트()를
    부르면 COM 왕복이 여러 번(약 8회) 드니, 저렴한 쪽 번호 확인(1회)을
    먼저 해서 대상이 아닌 문단은 비싼 텍스트 읽기 자체를 건너뛴다. 긴
    문서일수록 이 필터의 효과가 커진다.
    """
    if hwp is None or 중단_요청됨():
        return 0
    읽기 = 문단_위간격_pt_현재문단 if 위간격 else 문단_아래간격_pt_현재문단
    쓰기 = 문단_위간격_적용_현재선택 if 위간격 else 문단_아래간격_적용_현재선택
    원위치 = hwp.GetPos()
    순회_시작()
    적용수 = 0
    정체 = 0
    계측_시작 = time.perf_counter()
    계측_쓰기초 = 0.0
    계측_문단수 = 0
    try:
        while True:
            if 중단_요청됨():
                break
            시작위치 = hwp.GetPos()
            계측_문단수 += 1
            if 시작위치[0] == 0 and not 현재_한칸표인가():
                쪽번호 = 현재_페이지번호() if 최소쪽 is not None else None
                if 최소쪽 is None or 쪽번호 is None or 쪽번호 >= 최소쪽:
                    text = 현재문단_텍스트()
                    if paragraph_level(text) is not None:
                        현재값 = 읽기()
                        if 현재값 is not None:
                            새값 = max(0.0, round(현재값 + delta_pt, 1))
                            if abs(새값 - 현재값) >= 0.05:
                                if 원래값 is not None:
                                    원래값.setdefault(tuple(hwp.GetPos()[:2]), 현재값)
                                계측_쓰기_시작 = time.perf_counter()
                                hwp_run('MoveParaBegin')
                                hwp_run('MoveSelParaEnd')
                                쓰기(새값)
                                hwp_run('Cancel')
                                계측_쓰기초 += time.perf_counter() - 계측_쓰기_시작
                                적용수 += 1
            if not 범위_다음_문단으로_진행():
                break
            if hwp.GetPos() == 시작위치:
                정체 += 1
                if 정체 >= 2:
                    break
            else:
                정체 = 0
    finally:
        쪽맞춤_계측_더하기('문단쓰기', 계측_쓰기초, 적용수)
        쪽맞춤_계측_더하기('문단순회', time.perf_counter() - 계측_시작 - 계측_쓰기초, 계측_문단수)
        try:
            hwp.SetPos(*원위치)
        except Exception:
            pass
    return 적용수


def 구조문단_아래간격_일괄조정(delta_pt, 최소쪽=None):
    return 구조문단_간격_일괄조정(delta_pt, 최소쪽=최소쪽)


def 구조문단_간격_복원(원래값, 위간격=False):
    """구조문단_간격_일괄조정이 기록한 원래 간격으로 되돌린다."""
    if hwp is None or not 원래값:
        return 0
    쓰기 = 문단_위간격_적용_현재선택 if 위간격 else 문단_아래간격_적용_현재선택
    원위치 = hwp.GetPos()
    복원수 = 0
    try:
        for (list_id, para_id), 값 in 원래값.items():
            try:
                hwp.SetPos(list_id, para_id, 0)
                hwp_run('MoveParaBegin')
                hwp_run('MoveSelParaEnd')
                쓰기(값)
                hwp_run('Cancel')
                복원수 += 1
            except Exception as e:
                로그(f"문단 간격 복원 실패(무시): {e}")
    finally:
        try:
            hwp.SetPos(*원위치)
        except Exception:
            pass
    return 복원수


def 셀_세로여백_읽기():
    """캐럿이 있는 셀의 (셀 여백 사용 여부, 위, 아래) 원래 값(HWPUNIT). 실패 시 None."""
    if hwp is None:
        return None
    try:
        pset = hwp.HParameterSet.HShapeObject
        hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
        cell = pset.ShapeTableCell
        return int(cell.HasMargin), int(cell.MarginTop), int(cell.MarginBottom)
    except Exception as e:
        로그(f"셀 세로 여백 읽기 실패(무시): {e}")
        return None


def 셀_세로여백_현재선택(top_hwpunit=None, bottom_hwpunit=None, 원래값=None):
    """캐럿이 있는 셀의 상하 안쪽 여백을 HWPUNIT으로 설정한다(원래값을 주면 그 값으로 복원)."""
    if hwp is None:
        return False
    try:
        pset = hwp.HParameterSet.HShapeObject
        hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
        pset.HSet.SetItem("ShapeType", 3)
        pset.HSet.SetItem("ShapeCellSize", 0)
        if 원래값 is not None:
            pset.ShapeTableCell.HasMargin = int(원래값[0])
            pset.ShapeTableCell.MarginTop = int(원래값[1])
            pset.ShapeTableCell.MarginBottom = int(원래값[2])
        else:
            pset.ShapeTableCell.HasMargin = 1
            if top_hwpunit is not None:
                pset.ShapeTableCell.MarginTop = int(top_hwpunit)
            if bottom_hwpunit is not None:
                pset.ShapeTableCell.MarginBottom = int(bottom_hwpunit)
        return hwp.HAction.Execute("TablePropertyDialog", pset.HSet) is not False
    except Exception as e:
        로그(f"셀 세로 여백 적용 실패(무시): {e}")
        return False


def 표_셀_세로여백_일괄조정(스텝, 최소쪽=None, 원래값=None):
    """최소쪽 이후의 표를 대상으로 셀 세로 여백(위·아래)을 원래 여백에 비례하여
    스텝(1단계당 페이지맞춤_스텝_pt / 페이지맞춤_최대_pt 비율)만큼 축소한다.
    실제로 값이 바뀐 셀 수를 반환한다.

    원래값(dict)을 주면 처음 바꾸는 셀의 원래 여백(HasMargin, MarginTop, MarginBottom)을
    셀 area 번호로 기록해 표_셀_세로여백_복원으로 되돌릴 수 있게 한다.
    한 칸 표(제목·개요 상자)는 보호하여 건드리지 않는다.
    """
    if hwp is None or 중단_요청됨() or not 페이지맞춤_표셀세로여백_사용:
        return 0
    if not hasattr(hwp, 'HParameterSet'):
        return 0
    최대_pt = max(0.1, float(페이지맞춤_최대_pt))
    스텝_pt = max(0.1, float(페이지맞춤_스텝_pt))
    축소비율 = min(1.0, max(0.0, float(스텝) * (스텝_pt / 최대_pt)))
    최소_hwpunit = max(0, int(round(페이지맞춤_표셀세로여백_최소_pt * 100)))

    def 읽기_계측():
        시작 = time.perf_counter()
        값 = 셀_세로여백_읽기()
        쪽맞춤_계측_더하기('표셀읽기', time.perf_counter() - 시작, 1)
        return 값

    def 쓰기_계측(**kw):
        시작 = time.perf_counter()
        결과 = 셀_세로여백_현재선택(**kw)
        쪽맞춤_계측_더하기('표셀쓰기', time.perf_counter() - 시작, 1)
        return 결과

    적용수 = 0
    for area in _표_셀_대상_순회(최소쪽):
        현재 = 읽기_계측()
        if 현재 is None:
            continue
        if 원래값 is not None:
            원래값.setdefault(area, 현재)
        원래 = 원래값.get(area, 현재) if 원래값 is not None else 현재
        원래_has, 원래_top, 원래_bottom = 원래
        새_top = max(최소_hwpunit, int(round(원래_top * (1.0 - 축소비율))))
        새_bottom = max(최소_hwpunit, int(round(원래_bottom * (1.0 - 축소비율))))
        if abs(새_top - 현재[1]) >= 5 or abs(새_bottom - 현재[2]) >= 5:
            if 쓰기_계측(top_hwpunit=새_top, bottom_hwpunit=새_bottom):
                적용수 += 1
    return 적용수


# 문서 유형별 쪽 맞춤 한 번 동안 쓰는 표 칸 묶음 캐시(None이면 쓰지 않음). 간격·여백·쪽 나눔만 바꾸므로 표 칸
# 목록 번호(area)는 그동안 바뀌지 않는다. 예전에는 보고서마다 문서의 표 칸 전체를 다시 훑었다(2026-10-09).
_쪽맞춤_표캐시 = None


def _표_셀_대상_순회(최소쪽=None, 문단범위=None):
    """쪽 수 맞춤이 셀 세로 여백을 줄일 표 셀의 area를 차례로 내준다(캐럿은 그 셀에 둔다).

    최소쪽 이전 쪽의 표와 한 칸 표(제목·개요 상자)는 뺀다. 문단범위를 주면 그 본문 문단에 놓인 표만 본다.
    끝나면 캐럿을 원래 자리로 돌린다.
    """
    def 범위안(키):
        return 문단범위 is None or (bool(키) and 키[0] == 0 and 키[1] in 문단범위)

    원위치 = None
    try:
        원위치 = hwp.GetPos()
    except Exception:
        pass

    계측_스캔시작 = time.perf_counter()
    캐시 = _쪽맞춤_표캐시
    if 캐시 is not None and '묶음' in 캐시:
        한칸영역, 묶음 = 캐시['한칸'], 캐시['묶음']
    else:
        한칸영역 = set()
        try:
            목록 = 한칸표_영역_목록()
            if 목록:
                한칸영역 = set(목록)
        except Exception:
            pass
        try:
            묶음 = 표칸_묶음_키별()
        except Exception:
            묶음 = None
        if 캐시 is not None:
            캐시.update(한칸=한칸영역, 묶음=묶음)

    try:
        쪽맞춤_계측_더하기('표스캔', time.perf_counter() - 계측_스캔시작)

        if 묶음 is not None:
            for 키, 칸들 in 묶음.items():
                if 중단_요청됨():
                    break
                if not 칸들:
                    continue
                if len(칸들) == 1 and 칸들[0][1] == "A1":
                    continue
                if 칸들[0][0] in 한칸영역 or not 범위안(키):
                    continue
                첫칸 = 칸들[0][0]
                try:
                    hwp.SetPos(첫칸, 0, 0)
                except Exception:
                    continue
                쪽 = 현재_페이지번호() if 최소쪽 is not None else None
                if 최소쪽 is not None and 쪽 is not None and 쪽 < 최소쪽:
                    continue
                for area, 주소, 행 in 칸들:
                    if 중단_요청됨():
                        break
                    try:
                        hwp.SetPos(area, 0, 0)
                    except Exception:
                        continue
                    yield area
        else:
            area = 1
            while True:
                if 중단_요청됨():
                    break
                area += 1
                try:
                    hwp.SetPos(area, 0, 0)
                except Exception:
                    break
                try:
                    pos = hwp.GetPos()
                    if pos[0] != area:
                        break
                except Exception:
                    break
                if area in 한칸영역 or not 범위안(현재_표_키()):
                    continue
                쪽 = 현재_페이지번호() if 최소쪽 is not None else None
                if 최소쪽 is not None and 쪽 is not None and 쪽 < 최소쪽:
                    continue
                yield area
    finally:
        if 원위치 is not None:
            try:
                hwp.SetPos(*원위치)
            except Exception:
                pass


def 표_셀_세로여백_복원(원래값):
    """표_셀_세로여백_일괄조정이 기록한 원래 여백으로 되돌린다."""
    if hwp is None or not 원래값:
        return 0
    원위치 = None
    try:
        원위치 = hwp.GetPos()
    except Exception:
        pass
    복원수 = 0
    try:
        for area, 값 in 원래값.items():
            try:
                hwp.SetPos(area, 0, 0)
                if 셀_세로여백_현재선택(원래값=값):
                    복원수 += 1
            except Exception as e:
                로그(f"셀 세로 여백 복원 실패(무시): {e}")
    finally:
        if 원위치 is not None:
            try:
                hwp.SetPos(*원위치)
            except Exception:
                pass
    return 복원수


# 목표 쪽 수에 닿은 뒤 묶음이 쪽 경계에 걸려 있으면 몇 단계까지 더 줄여 볼지.
페이지맞춤_묶음확인_추가단계 = 4
# 마지막 페이지 수 맞춤이 묶음 규칙까지 지키며 끝났는지(쪽 배치 재실행 생략용).
쪽맞춤_묶음_확인됨 = False
# 마지막 페이지 수 맞춤이 '걸린 묶음은 다음 쪽으로 옮긴다'로 끝났는지. 이때는
# 쪽 배치가 묶음을 옮겨 마지막 쪽이 짧아져도 다시 줄이지 않는다(사용자 결정).
쪽맞춤_묶음이동_결정 = False


def 쪽맞춤_묶음분리_있음(최소쪽=None, 최대쪽=None):
    """쪽 배치 규칙을 어기고 쪽 경계에 걸린 묶음이 있는지 읽기 전용으로 본다.

    최종 쪽 배치 검사와 같은 기준이다: 논리단위 5개 이하 □ 묶음은 묶음
    전체, 그 밖에는 ㅇ 단위(ㅇ와 -·*)와 □+첫 ㅇ 단위. 처음 발견하면 멈춘다.

    최소쪽을 주면 (최소쪽-1)쪽보다 앞에서 시작하는 묶음은 보지 않는다.
    페이지 수 맞춤은 최소쪽부터만 간격을 바꾸므로 그 앞의 쪽 나눔은 그대로다.
    앞쪽에 원래부터 풀 수 없는 긴 묶음이 걸려 있으면 매 단계 '걸림'으로 판정돼
    헛되이 더 줄였다(실측: 10쪽 회의자료에서 단계마다 약 30초).

    로마자 중제목 + □ + 첫 ㅇ 단위 묶음도 본다(2026-10-04 실측: 서식 예시에서 쪽 수 맞춤이 2쪽부터 문단 위
    간격을 줄여 'Ⅱ 추진 계획 · □ · ㅇ (1단계)'만 1쪽으로 올라오고 '- 입자가속기 …'는 2쪽에 남음).
    ㅇ 단위 경계에서 나뉘고 앞쪽 단위가 많은 □ 묶음은 쪽 배치가 일부러 그렇게 둔 것이라 걸림으로 보지 않는다.
    """
    original = hwp.GetPos()
    표문단 = 본문_표_문단번호()
    try:
        순회_시작()
        while True:
            if 중단_요청됨():
                return False
            pos = hwp.GetPos()
            쪽 = 현재_페이지번호() if ((최소쪽 or 최대쪽) and pos[0] == 0) else None
            if 최대쪽 and 쪽 and 쪽 > 최대쪽:
                return False
            최소쪽 = 최소쪽 or 1
            if (pos[0] == 0 and (쪽 is None or 쪽 >= 최소쪽 - 1) and pos[1] in 표문단
                    and 로마자_중제목_표인가(표문단[pos[1]])):
                다음 = 중제목_다음글문단(pos[1], 표문단)
                묶음 = 중제목_묶음_문단(다음[0]) if 다음 else []
                if 묶음 and all(쪽범위_안인가(p[0]) for p in 묶음):
                    counts, 표쪽 = 중제목_묶음_쪽({'표키': 표문단[pos[1]]}, 묶음)
                    if counts and len(set(counts) | set(표쪽)) > 1:
                        진단로그(f'[쪽 수 맞춤] 쪽 경계에 걸린 중제목 묶음: {다음[1].strip()[:40]}')
                        return True
                hwp.SetPos(*pos)
            elif pos[0] == 0 and (쪽 is None or 쪽 >= 최소쪽 - 1):
                text = 현재문단_텍스트()
                role = 보고서_문단역할(text)
                if role in ('소제목', '본문', '내용', '부연설명'):
                    target = 소제목묶음_쪽맞춤_대상(pos, 표문단) if role == '소제목' else None
                    paragraphs = target[0] if target else 보고서_본문묶음_수집(pos)
                    if paragraphs and all(쪽범위_안인가(p[0]) for p in paragraphs):
                        counts = 보고서_묶음_쪽별줄수(paragraphs)
                        if (counts and len(counts) > 1
                                and not 쪽보다_긴_묶음인가(paragraphs, counts)
                                and not (target and 소제목묶음_단위경계_앞쪽우선(*target))):
                            진단로그(f'[쪽 수 맞춤] 쪽 경계에 걸린 묶음: {text.strip()[:40]}')
                            return True
                hwp.SetPos(*pos)
            if not 범위_다음_문단으로_진행():
                return False
    finally:
        hwp.SetPos(*original)


def 쪽맞춤_대상_조사(최소쪽, 문단범위=None):
    """쪽 수 맞춤이 바꿀 문단·표 셀과 원래 값을 한 번만 모은다(값은 바꾸지 않는다).

    문단: {(list_id, para_id): [원래 아래 pt, 원래 위 pt]}, 셀: {area: (HasMargin, 위, 아래)}.
    """
    문단 = {}
    원위치 = hwp.GetPos()
    # 보고서 범위가 있으면 그 첫 문단부터 보고 범위를 지나면 멈춘다(예전에는 보고서마다 문서 전체를 처음부터 훑었다).
    try:
        if 문단범위 is None:
            raise ValueError
        hwp.SetPos(0, 문단범위.start, 0)
        if tuple(hwp.GetPos()[:2]) != (0, 문단범위.start):
            raise ValueError
    except Exception:
        순회_시작()
    시작 = time.perf_counter()
    훑은수 = 0
    정체 = 0
    try:
        while not 중단_요청됨():
            시작위치 = hwp.GetPos()
            if 문단범위 is not None and 시작위치[0] == 0 and 시작위치[1] >= 문단범위.stop:
                break
            훑은수 += 1
            if (시작위치[0] == 0 and (문단범위 is None or 시작위치[1] in 문단범위)
                    and not 현재_한칸표인가()):
                쪽번호 = 현재_페이지번호()
                if 쪽번호 is None or 쪽번호 >= 최소쪽:
                    if paragraph_level(현재문단_텍스트()) is not None:
                        아래, 위 = 문단_아래간격_pt_현재문단(), 문단_위간격_pt_현재문단()
                        if 아래 is not None and 위 is not None:
                            문단[tuple(hwp.GetPos()[:2])] = [아래, 위]
            if not 범위_다음_문단으로_진행():
                break
            if hwp.GetPos() == 시작위치:
                정체 += 1
                if 정체 >= 2:
                    break
            else:
                정체 = 0
    finally:
        쪽맞춤_계측_더하기('문단순회', time.perf_counter() - 시작, 훑은수)
        try:
            hwp.SetPos(*원위치)
        except Exception:
            pass
    셀 = {}
    if 페이지맞춤_표셀세로여백_사용 and hasattr(hwp, 'HParameterSet'):
        for area in _표_셀_대상_순회(최소쪽, 문단범위):
            시작 = time.perf_counter()
            값 = 셀_세로여백_읽기()
            쪽맞춤_계측_더하기('표셀읽기', time.perf_counter() - 시작, 1)
            if 값 is not None:
                셀.setdefault(area, 값)
    return {'문단': 문단, '셀': 셀, '문단현재': {k: list(v) for k, v in 문단.items()}, '셀현재': dict(셀)}


def 쪽맞춤_레벨_적용(조사, 레벨, 위간격_0=False):
    """조사한 문단·셀을 레벨만큼 줄인 절대값으로 맞춘다(레벨 0은 원래 값). 바뀐 곳만 쓴다.

    위간격_0이면 문단 위 간격을 모두 0pt로 한다(1쪽 보고서 맞춤의 마지막 수단).
    """
    아래줄임, 위줄임, 비율 = 쪽맞춤_레벨_줄임량(
        레벨, half=max(1, int(round(페이지맞춤_최대_pt / 페이지맞춤_스텝_pt))), step_pt=페이지맞춤_스텝_pt)
    원위치 = hwp.GetPos()
    바꾼문단 = 바꾼셀 = 0
    try:
        문단시작 = time.perf_counter()
        for 위치, (원아래, 원위) in 조사['문단'].items():
            현재 = 조사['문단현재'][위치]
            for 칸, 원값, 줄임, 쓰기 in ((0, 원아래, 아래줄임, 문단_아래간격_적용_현재선택),
                                    (1, 원위, 위줄임, 문단_위간격_적용_현재선택)):
                새값 = 원값 if 줄임 <= 0 else max(0.0, round(원값 - 줄임, 1))
                if 위간격_0 and 칸 == 1:
                    새값 = 0.0
                if abs(새값 - 현재[칸]) < 0.05:
                    continue
                hwp.SetPos(위치[0], 위치[1], 0)
                hwp_run('MoveParaBegin')
                hwp_run('MoveSelParaEnd')
                쓰기(새값)
                hwp_run('Cancel')
                현재[칸] = 새값
                바꾼문단 += 1
                쪽맞춤_바꾼문단.add(tuple(위치[:2]))
        쪽맞춤_계측_더하기('문단쓰기', time.perf_counter() - 문단시작, 바꾼문단)
        최소_hwpunit = max(0, int(round(페이지맞춤_표셀세로여백_최소_pt * 100)))
        셀시작 = time.perf_counter()
        for area, 원래 in 조사['셀'].items():
            if 비율 <= 0:
                목표 = 원래
            else:
                목표 = (1, max(최소_hwpunit, int(round(원래[1] * (1.0 - 비율)))),
                       max(최소_hwpunit, int(round(원래[2] * (1.0 - 비율)))))
            현재 = 조사['셀현재'][area]
            if 목표 == 현재 or (비율 > 0 and abs(목표[1] - 현재[1]) < 5 and abs(목표[2] - 현재[2]) < 5):
                continue
            hwp.SetPos(area, 0, 0)
            성공 = (셀_세로여백_현재선택(원래값=원래) if 비율 <= 0
                  else 셀_세로여백_현재선택(top_hwpunit=목표[1], bottom_hwpunit=목표[2]))
            if 성공:
                조사['셀현재'][area] = 목표
                바꾼셀 += 1
        쪽맞춤_계측_더하기('표셀쓰기', time.perf_counter() - 셀시작, 바꾼셀)
    finally:
        try:
            hwp.SetPos(*원위치)
        except Exception:
            pass
    return 바꾼문단, 바꾼셀


def _보고서_페이지수_맞춤_고속(목표_페이지수):
    """대상 조사 1회 + 레벨 이분 탐색으로 쪽 수를 맞춘다. 결과는 기존 방식과 같은 뜻의 True/False.

    탐색이 어긋나면(측정 실패, 다시 잰 쪽 수가 다름) 원래 값으로 되돌리고 None을 돌려줘 기존 방식을 쓰게 한다.
    """
    global 쪽맞춤_묶음_확인됨, 쪽맞춤_묶음이동_결정
    최소쪽 = max(1, 목표_페이지수 - 페이지맞춤_뒤쪽범위_쪽수)
    반레벨 = max(1, int(round(페이지맞춤_최대_pt / 페이지맞춤_스텝_pt)))
    최대레벨 = 2 * 반레벨
    로그(f"페이지 수 맞춤 시도(고속): 목표 {목표_페이지수}쪽 (문단 아래·위 간격 및 표 셀 여백 최대 "
         f"{페이지맞춤_최대_pt:g}pt, {최소쪽}쪽부터, 레벨 1~{최대레벨} 이분 탐색, 묶음 규칙 확인)")
    시작 = time.perf_counter()
    조사 = 쪽맞춤_대상_조사(최소쪽)
    로그(f"[쪽 수 맞춤 고속] 대상 조사: 문단 {len(조사['문단'])}개·표 셀 {len(조사['셀'])}개 "
         f"({time.perf_counter() - 시작:.1f}초)")
    if not 조사['문단'] and not 조사['셀']:
        로그("페이지 수 맞춤: 줄일 문단 간격 및 표 셀 여백이 없음")
        return False

    def 측정(레벨):
        if 중단_요청됨():
            return None
        단계시작 = time.perf_counter()
        바꾼문단, 바꾼셀 = 쪽맞춤_레벨_적용(조사, 레벨)
        구간시작 = time.perf_counter()
        마지막쪽, _ = 마지막쪽_화면줄수()
        쪽맞춤_계측_더하기('쪽측정', time.perf_counter() - 구간시작, 1)
        로그(f"[쪽 수 맞춤 고속] 레벨 {레벨}: {마지막쪽}쪽 (바꾼 간격 {바꾼문단}곳·셀 {바꾼셀}개, "
             f"{time.perf_counter() - 단계시작:.1f}초)")
        return 마지막쪽

    def 묶음걸림(레벨):
        쪽맞춤_레벨_적용(조사, 레벨)
        구간시작 = time.perf_counter()
        try:
            return 쪽맞춤_묶음분리_있음(최소쪽=최소쪽)
        finally:
            쪽맞춤_계측_더하기('묶음검사', time.perf_counter() - 구간시작, 1)

    완료 = False
    try:
        결과 = 쪽맞춤_레벨_탐색(측정, 목표_페이지수, 최대레벨, bundle_split=묶음걸림,
                          extra_levels=페이지맞춤_묶음확인_추가단계)
        if 결과['status'] == 'error':
            if 중단_요청됨():
                return False
            로그("페이지 수 맞춤(고속): 쪽 번호 확인 실패 — 기존 방식으로 다시 시도")
            return None
        if 결과['status'] == 'fail':
            로그(f"페이지 수 맞춤 실패: 문단 아래·위 간격 및 표 셀 여백을 최대 {페이지맞춤_최대_pt:g}pt까지 줄여도 "
                 f"목표({목표_페이지수}쪽) 미달 — 바꾼 간격·여백을 원래 값으로 되돌림")
            return False
        레벨 = 결과['level']
        쪽맞춤_레벨_적용(조사, 레벨)
        마지막쪽, _ = 마지막쪽_화면줄수()
        if 마지막쪽 is None or 마지막쪽 > 목표_페이지수:
            로그(f"페이지 수 맞춤(고속): 레벨 {레벨}을 다시 재니 {마지막쪽}쪽 — 쪽 수가 레벨 순서대로 줄지 않아 "
                 "기존 방식으로 다시 시도")
            return None
        아래, 위, _ = 쪽맞춤_레벨_줄임량(레벨, half=반레벨, step_pt=페이지맞춤_스텝_pt)
        문구 = f"레벨 {레벨}(아래 간격 {아래:g}pt·위 간격 {위:g}pt, 표 셀 여백 연동, 측정 {len(결과['measured'])}회)"
        완료 = True
        if 결과['status'] == 'ok':
            쪽맞춤_묶음_확인됨 = True
            로그(f"페이지 수 맞춤 완료: {문구} 축소로 {목표_페이지수}쪽 달성, 쪽 경계에 걸린 묶음 없음")
        else:
            쪽맞춤_묶음이동_결정 = True
            로그(f"페이지 수 맞춤: 묶음 규칙을 함께 지키는 레벨이 없어 처음 {목표_페이지수}쪽에 닿은 {문구}로 두고, "
                 "걸린 묶음은 쪽 배치에서 다음 쪽으로 옮김")
        return True
    finally:
        if not 완료:
            구간시작 = time.perf_counter()
            try:
                쪽맞춤_레벨_적용(조사, 0)
            finally:
                쪽맞춤_계측_더하기('원복', time.perf_counter() - 구간시작)


def 보고서_페이지수_맞춤_시도(목표_페이지수):
    """페이지 수 맞춤 본체를 부르며 구간별 소요 시간을 작업 로그에 남긴다(동작은 같다)."""
    쪽맞춤_계측_시작()
    시작 = time.perf_counter()
    결과 = False
    try:
        if 페이지맞춤_고속_사용 and hwp is not None and 목표_페이지수 and 목표_페이지수 > 0:
            try:
                결과 = _보고서_페이지수_맞춤_고속(목표_페이지수)
            except Exception as e:
                로그(f"페이지 수 맞춤(고속) 오류: {e} — 기존 방식으로 다시 시도")
                결과 = None
            if 결과 is not None:
                return 결과
        결과 = _보고서_페이지수_맞춤_시도_본체(목표_페이지수)
        return 결과
    finally:
        전체초 = time.perf_counter() - 시작
        값 = 쪽맞춤_계측_끝()
        if 값:
            로그(쪽맞춤_계측_합계문구(값, 전체초, 결과))


def _보고서_페이지수_맞춤_시도_본체(목표_페이지수):
    """본문 줄간격은 그대로 둔 채 항목기호 문단의 간격과 표의 셀 세로 여백을
    단계별로 비례 축소하여 실제 페이지 수를 목표에 맞춘다.

    먼저 '문단 아래 간격'과 표 셀 여백을 연동해 줄이고, 그래도 안 되면
    '문단 위 간격'과 표 셀 여백을 줄인다. 각각 페이지맞춤_최대_pt까지만
    줄이며, 매 단계 실제 페이지 수를 다시 잰다.

    묶음 규칙도 확인한다. 목표 쪽 수에 닿았을 때 쪽 경계에 걸린 묶음이
    없으면 그대로 끝낸다. 걸린 묶음이 있으면 몇 단계 더 줄여 보고, 끝내
    둘 다 만족하지 못하면 처음 목표에 닿았던 단계로 되돌려 둔다 — 그 뒤
    쪽 배치가 걸린 묶음 전체를 다음 쪽으로 옮긴다(사용자 결정: 마지막 쪽에
    본문 1줄만 남기는 것보다 묶음 전체를 옮기는 편을 택함).
    목표 쪽 수에 한 번도 닿지 못하면 바꾼 간격과 여백을 모두 원래 값으로 되돌린다.
    """
    global 쪽맞춤_묶음_확인됨, 쪽맞춤_묶음이동_결정
    쪽맞춤_묶음_확인됨 = False
    쪽맞춤_묶음이동_결정 = False
    if hwp is None or not 목표_페이지수 or 목표_페이지수 <= 0:
        return False
    최대반복 = max(1, int(round(페이지맞춤_최대_pt / 페이지맞춤_스텝_pt)))
    최소쪽 = max(1, 목표_페이지수 - 페이지맞춤_뒤쪽범위_쪽수)
    로그(
        f"페이지 수 맞춤 시도: 목표 {목표_페이지수}쪽 (문단 아래·위 간격 및 표 셀 여백 최대 "
        f"{페이지맞춤_최대_pt:g}pt 비례 축소, {최소쪽}쪽부터만 검사, 묶음 규칙 확인)"
    )
    원래값 = {False: {}, True: {}}
    표셀_원래값 = {}
    적용기록 = []          # 적용한 단계 순서(위간격 여부) — 되돌린 뒤 다시 적용할 때 쓴다
    첫_도달 = None         # 처음 목표 쪽 수에 닿았을 때의 적용기록 길이
    추가단계 = 0

    def 원래대로():
        시작 = time.perf_counter()
        try:
            return (구조문단_간격_복원(원래값[True], 위간격=True)
                    + 구조문단_간격_복원(원래값[False])
                    + 표_셀_세로여백_복원(표셀_원래값))
        finally:
            쪽맞춤_계측_더하기('원복', time.perf_counter() - 시작)

    for 위간격 in (False, True):
        이름 = "문단 위 간격" if 위간격 else "문단 아래 간격"
        for 회 in range(1, 최대반복 + 1):
            if 중단_요청됨():
                return False
            단계시작 = time.perf_counter()
            계측_이전 = 쪽맞춤_계측_복사()
            구간시작 = time.perf_counter()
            조정수 = 구조문단_간격_일괄조정(
                -페이지맞춤_스텝_pt, 최소쪽=최소쪽, 위간격=위간격, 원래값=원래값[위간격])
            쪽맞춤_계측_더하기('문단합계', time.perf_counter() - 구간시작)
            표조정수 = 0
            if 페이지맞춤_표셀세로여백_사용:
                스텝 = len(적용기록) + 1
                구간시작 = time.perf_counter()
                표조정수 = 표_셀_세로여백_일괄조정(
                    스텝, 최소쪽=최소쪽, 원래값=표셀_원래값)
                쪽맞춤_계측_더하기('표합계', time.perf_counter() - 구간시작)
            if 조정수 == 0 and 표조정수 == 0:
                로그(f"페이지 수 맞춤: 더 줄일 {이름} 및 표 셀 여백이 없음")
                break
            적용기록.append(위간격)
            구간시작 = time.perf_counter()
            마지막쪽, _ = 마지막쪽_화면줄수()
            쪽맞춤_계측_더하기('쪽측정', time.perf_counter() - 구간시작, 1)
            로그(쪽맞춤_계측_단계문구(이름, 회, 쪽맞춤_계측_차이(계측_이전),
                                  time.perf_counter() - 단계시작, 마지막쪽))
            if 마지막쪽 is None:
                로그("페이지 수 맞춤 중단: 쪽 번호 확인 실패")
                break
            if 마지막쪽 > 목표_페이지수:
                continue
            구간시작 = time.perf_counter()
            묶음걸림 = 쪽맞춤_묶음분리_있음(최소쪽=최소쪽)
            쪽맞춤_계측_더하기('묶음검사', time.perf_counter() - 구간시작, 1)
            if not 묶음걸림:
                쪽맞춤_묶음_확인됨 = True
                로그(f"페이지 수 맞춤 완료: {이름} {회}단계({회 * 페이지맞춤_스텝_pt:g}pt, 표 셀 여백 연동) 축소로 "
                     f"{목표_페이지수}쪽 달성, 쪽 경계에 걸린 묶음 없음")
                return True
            if 첫_도달 is None:
                첫_도달 = len(적용기록)
                로그(f"페이지 수 맞춤: {목표_페이지수}쪽에 닿았지만 쪽 경계에 걸린 묶음이 있어 "
                     f"최대 {페이지맞춤_묶음확인_추가단계}단계 더 줄여 봄")
            else:
                추가단계 += 1
            if 추가단계 >= 페이지맞춤_묶음확인_추가단계:
                break
        else:
            continue
        if 첫_도달 is not None and 추가단계 >= 페이지맞춤_묶음확인_추가단계:
            break

    if 첫_도달 is None:
        복원수 = 원래대로()
        로그(
            f"페이지 수 맞춤 실패: 문단 아래·위 간격 및 표 셀 여백을 최대 {페이지맞춤_최대_pt:g}pt까지 줄여도 "
            f"목표({목표_페이지수}쪽) 미달 — 바꾼 간격·여백 {복원수}곳을 원래 값으로 되돌림"
        )
        return False

    # 묶음 규칙까지 지키는 단계는 없었다. 처음 목표에 닿았던 단계로 되돌려 두면
    # 쪽 배치가 걸린 묶음 전체를 다음 쪽으로 옮긴다.
    원래대로()
    재적용시작 = time.perf_counter()
    for 위간격 in 적용기록[:첫_도달]:
        구조문단_간격_일괄조정(-페이지맞춤_스텝_pt, 최소쪽=최소쪽, 위간격=위간격)
    if 페이지맞춤_표셀세로여백_사용 and 첫_도달 > 0:
        표_셀_세로여백_일괄조정(첫_도달, 최소쪽=최소쪽, 원래값=표셀_원래값)
    쪽맞춤_계측_더하기('원복', time.perf_counter() - 재적용시작)
    쪽맞춤_묶음이동_결정 = True
    로그(f"페이지 수 맞춤: 묶음 규칙을 함께 지키는 단계가 없어 처음 {목표_페이지수}쪽에 닿은 "
         f"단계({첫_도달}단계)로 두고, 걸린 묶음은 쪽 배치에서 다음 쪽으로 옮김")
    return True


# 문서 유형별 쪽 수 맞춤(사용자 규칙, 2026-10-09). 보고서 1개 = 제목 표 1개 + 계층체계 1개이고, 제목 표마다
# 새 보고서다(붙임은 앞 보고서에 속한다). 1쪽 보고서는 모든 문장이 1쪽에 담겨야 하고, 1쪽 보고서를 묶은
# 취합보고서는 각 보고서가 자기 1쪽 안에 들어가야 한다. 심화보고서(제목 1개, 1쪽 초과)는 기존처럼 마지막 쪽만 본다.
# 담당자 칸: 부서명·직함·담당자 이름·내선/전화번호(3행1열 제목 표는 소속이 다른 두 담당자 칸, 사용자 설명 2026-10-09).
_제목표_담당자 = re.compile(r'담당|과장|팀장|본부장|부장|☎|전화|내선|부서|작성|\d{2,4}-\d{4}')
_제목표_날짜 = re.compile(r'[0-9]{2,4}\s*[.년/\-]\s*[0-9]{1,2}')


def _칸_문단글들(area, 최대=6):
    """표 칸(area)의 문단 글 목록. 칸으로 옮기지 못하면 None."""
    hwp.SetPos(area, 0, 0)
    if hwp.GetPos()[0] != area:
        return None
    글들 = []
    for _ in range(최대):
        이전 = hwp.GetPos()
        글들.append(현재문단_텍스트())
        hwp.SetPos(*이전)
        hwp_run('MoveNextParaBegin')
        지금 = hwp.GetPos()
        # 칸의 마지막 문단에서는 같은 문단에 머문다(실측: 한 문단 칸을 여섯 번 읽음).
        if 지금[0] != area or 지금[1] <= 이전[1]:
            break
    return 글들


def 제목표인가_현재(표키):
    """본문 표가 보고서 제목 표인지 한/글 화면에서 본다(보고서 경계 판정용).

    칸이 2~3개이고 첫 칸이 제목, 나머지 칸 중 하나 이상이 담당자 칸(과장·팀장·☎ 등)이다. 2×2의 날짜 칸,
    3행1열의 두 담당자 칸(실측: 마포문화재단), '- … -' 부제 줄(실측: 고용협력과)도 받는다. 제목 칸은
    □·ㅇ 등 계층 기호로 시작하지 않는 1~3문단이고 '붙임'으로 시작하지 않는다. 날짜·담당자 칸이 모두 빈 표도 제목 표다.
    """
    범위 = 표_칸영역_범위(표키)
    if 범위 and 범위[1] == 범위[0]:
        return _한칸_제목표인가_현재(범위[0])
    if 범위 and 4 <= 범위[1] - 범위[0] + 1 <= 16:
        return _기타_제목표인가_현재(범위)
    if not 범위 or 범위[1] - 범위[0] + 1 not in (2, 3):
        return False
    original = hwp.GetPos()
    try:
        칸글 = [_칸_문단글들(area) for area in range(범위[0], 범위[1] + 1)]
    except Exception:
        return False
    finally:
        hwp.SetPos(*original)
    if any(글 is None for 글 in 칸글):
        return False
    제목 = [t.strip() for t in 칸글[0] if t.strip()]
    if not 1 <= len(제목) <= 3 or any(re.match(r'^[□ㅁㅇ○※*]', t) for t in 제목):
        return False
    합 = ' '.join(제목)
    if len(합) > 160 or 합.startswith('붙임'):
        return False
    정보 = [' '.join(글).strip() for 글 in 칸글[1:]]
    if not any(정보):
        return True
    return any(_제목표_담당자.search(t) or _설정_담당자_글인가(t) for t in 정보)


def _한칸_제목표인가_현재(area):
    """한 칸 표(칸 목록 번호 area)가 1×1 제목 상자인지: 제목다운 글이고 글자가 한칸_제목_최소크기_pt 이상."""
    original = hwp.GetPos()
    try:
        글들 = _칸_문단글들(area)
        if not 글들 or not _한칸_제목글인가(글들):
            return False
        hwp.SetPos(area, 0, 0)
        hwp_run('MoveSelParaEnd')
        크기 = float(hwp.CharShape.Item('Height') or 0) / 100
        hwp_run('Cancel')
        return 크기 >= 한칸_제목_최소크기_pt
    except Exception:
        return False
    finally:
        try:
            hwp.SetPos(*original)
        except Exception:
            pass


def _기타_제목표인가_현재(범위):
    """여러 칸 장식 제목 상자인지(화면 판정, _기타_제목표인가와 같은 기준)."""
    original = hwp.GetPos()
    try:
        칸글 = [(area, _칸_문단글들(area)) for area in range(범위[0], 범위[1] + 1)]
        if any(글 is None for _, 글 in 칸글):
            return False
        글칸 = [(a, 글) for a, 글 in 칸글 if any(t.strip() for t in 글)]
        제목칸 = [a for a, 글 in 글칸 if _한칸_제목글인가(글)]
        if len(제목칸) != 1:
            return False
        if any(not 보고서머리.parse_info(' '.join(글).strip()) for a, 글 in 글칸 if a != 제목칸[0]):
            return False
        hwp.SetPos(제목칸[0], 0, 0)
        hwp_run('MoveSelParaEnd')
        크기 = float(hwp.CharShape.Item('Height') or 0) / 100
        hwp_run('Cancel')
        return 크기 >= 한칸_제목_최소크기_pt
    except Exception:
        return False
    finally:
        try:
            hwp.SetPos(*original)
        except Exception:
            pass


def _보고서_끝내용(시작문단, 끝문단, 표문단):
    """보고서 문단 범위에서 마지막 내용: (끝 위치, None) 또는 표로 끝나면 (None, 표키). 없으면 (None, None)."""
    for 번호 in range(끝문단, 시작문단 - 1, -1):
        if 번호 in 표문단:
            return None, 표문단[번호]
        hwp.SetPos(0, 번호, 0)
        if tuple(hwp.GetPos()[:2]) != (0, 번호):
            continue
        if 현재문단_텍스트().strip():
            hwp_run('MoveParaEnd')
            return tuple(hwp.GetPos()), None
    return None, None


def 쪽맞춤_보고서_끝쪽(끝):
    """보고서 끝 내용의 (쪽, 그 쪽에 걸린 줄 수). 표로 끝나면 줄 수는 None, 모르면 (None, None)."""
    위치, 표키 = 끝
    if 표키 is not None:
        범위 = 표_쪽범위(표키)
        return (범위[1] if 범위 else None), None
    if 위치 is None:
        return None, None
    원위치 = hwp.GetPos()
    try:
        hwp.SetPos(*위치)
        쪽 = 현재_페이지번호()
        hwp_run('MovePageBegin')
        줄수 = 0
        이전줄끝 = None
        while not 중단_요청됨():
            hwp_run('MoveLineEnd')
            줄끝 = hwp.GetPos()
            if 줄끝 == 이전줄끝 or 줄끝[0] != 0:
                break
            줄수 += 1
            if (줄끝[1], 줄끝[2]) >= (위치[1], 위치[2]):
                break
            이전줄끝 = 줄끝
            hwp_run('MoveNextChar')
            if hwp.GetPos() == 줄끝:
                break
        return 쪽, 줄수
    except Exception as e:
        로그(f"보고서 끝 쪽 확인 실패(무시): {e}")
        return None, None
    finally:
        try:
            hwp.SetPos(*원위치)
        except Exception:
            pass


def 쪽맞춤_보고서_목록(제목문단=None, 대상=None):
    """제목 표마다 나눈 보고서 목록과 제목 표 문단 번호.

    보고서: dict(문단범위, 끝, start, end, overflow, 제목). 첫 제목 표 앞 내용(표지 등)은 첫 보고서에 넣는다.
    대상(보고서 번호)을 주면 그 보고서의 쪽만 재고 나머지 자리는 None이다(쪽 측정이 보고서마다 반복되지 않게).
    """
    _표칸영역.clear()
    표문단 = 본문_표_문단번호()
    원위치 = hwp.GetPos()
    try:
        if 제목문단 is None:
            제목문단 = sorted(번호 for 번호, 키 in 표문단.items() if 제목표인가_현재(키))
        쪽맞춤_제목문단.clear()
        쪽맞춤_제목문단.update(제목문단)
        hwp_run('MoveDocEnd')
        끝문단 = hwp.GetPos()[1] if hwp.GetPos()[0] == 0 else max(list(표문단) + [0])
        시작들 = 제목문단 or [0]
        if 시작들[0] != 0:
            시작들 = [0] + 시작들[1:]
        보고서 = []
        for i, 시작 in enumerate(시작들):
            if 대상 is not None and i != 대상:
                보고서.append(None)
                continue
            끝 = (시작들[i + 1] - 1) if i + 1 < len(시작들) else 끝문단
            hwp.SetPos(0, 시작, 0)
            첫쪽 = 현재_페이지번호()
            끝내용 = _보고서_끝내용(시작, 끝, 표문단)
            끝쪽, 줄수 = 쪽맞춤_보고서_끝쪽(끝내용)
            if 첫쪽 is None or 끝쪽 is None:
                return None, 제목문단
            보고서.append({'문단범위': range(시작, 끝 + 1), '끝': 끝내용, 'start': 첫쪽, 'end': 끝쪽,
                         'overflow': 줄수 if 끝쪽 > 첫쪽 else 0})
        return 보고서, 제목문단
    finally:
        try:
            hwp.SetPos(*원위치)
        except Exception:
            pass


def _쪽맞춤_줄간격_되돌리기(보관):
    for pos, kind, value in 보관:
        hwp.SetPos(*pos)
        act = hwp.CreateAction('ParagraphShape')
        pset = act.CreateSet()
        pset.SetItem('LineSpacingType', kind)
        pset.SetItem('LineSpacing', value)
        act.Execute(pset)


def 보고서_1쪽_맞춤(보고서, 번호=1, 목표쪽수=1, 원본줄간격=None, 원본줄자간=None):
    """보고서를 첫 쪽부터 목표쪽수 쪽 안에 담는다. 성공하면 True, 못 하면 바꾼 값을 모두 되돌리고 False.

    1) 문단 아래·위 간격과 표 셀 여백을 레벨 이분 탐색으로 줄인다(보고서 쪽 범위 안 묶음이 쪽 경계에 걸리지 않는
    레벨을 고른다). 2) 최대로 줄여도 넘치면 마지막 수단으로 문단 위 간격을 모두 0pt, 표 셀 여백을 최소로 하고,
    그때 넘친 줄이 4줄 미만이면 줄간격을 160%까지 낮춘다(사용자 규칙, 2026-10-09). 3) 그래도 넘치고 원본의 줄간격이
    더 좁았으면(원본줄간격: 원본 문단별 줄간격 목록) 문단마다 원본 값으로 되돌리고, 문단 수가 다르면 원본 대표 줄간격까지
    낮춘다(사용자 결정, 2026-10-09: 결과의 쪽 구성은 원본과 같아야 한다).
    """
    global 세트문장_최소줄간격_퍼센트
    목표쪽 = 보고서['start'] + max(1, 목표쪽수) - 1
    범위 = 보고서['문단범위']
    시작 = time.perf_counter()
    조사 = 쪽맞춤_대상_조사(1, 문단범위=범위)
    로그(f"[쪽 수 맞춤] 보고서 {번호}({보고서['start']}~{보고서['end']}쪽 → {목표쪽수}쪽): 대상 문단 "
         f"{len(조사['문단'])}개·표 셀 {len(조사['셀'])}개 ({time.perf_counter() - 시작:.1f}초)")
    반레벨 = max(1, int(round(페이지맞춤_최대_pt / 페이지맞춤_스텝_pt)))
    최대레벨 = 2 * 반레벨

    def 끝쪽():
        return 쪽맞춤_보고서_끝쪽(보고서['끝'])

    def 측정(레벨):
        if 중단_요청됨():
            return None
        쪽맞춤_레벨_적용(조사, 레벨)
        return 끝쪽()[0]

    def 묶음걸림(레벨):
        쪽맞춤_레벨_적용(조사, 레벨)
        return 쪽맞춤_묶음분리_있음(최소쪽=보고서['start'], 최대쪽=목표쪽)

    줄간격보관 = []
    자간보관 = []
    완료 = False
    try:
        if 조사['문단'] or 조사['셀']:
            결과 = 쪽맞춤_레벨_탐색(측정, 목표쪽, 최대레벨, bundle_split=묶음걸림,
                              extra_levels=페이지맞춤_묶음확인_추가단계)
            if 결과['status'] in ('ok', 'bundle_moved'):
                쪽맞춤_레벨_적용(조사, 결과['level'])
                if (끝쪽()[0] or 목표쪽 + 1) <= 목표쪽:
                    완료 = True
                    로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 레벨 {결과['level']} 축소(측정 {len(결과['measured'])}회"
                         f"{', 쪽 경계 묶음 있음' if 결과['status'] == 'bundle_moved' else ''})")
                    return True
        if 중단_요청됨():
            return False
        # 마지막 수단: 위 간격 0pt, 표 셀 여백 최소(최대 레벨의 아래 간격 축소는 그대로).
        쪽맞춤_레벨_적용(조사, 최대레벨, 위간격_0=True)
        쪽, 줄수 = 끝쪽()
        if 쪽 is not None and 쪽 <= 목표쪽:
            완료 = True
            로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 마지막 수단(문단 위 간격 0pt·표 셀 여백 최소)")
            return True
        # 자간 초기화 등으로 원본보다 줄이 늘어난 문단은 마지막 줄 어절을 자간을 줄여 앞 줄로 당긴다(사용자 결정,
        # 2026-10-09. 실측: 원본 1줄 '기간' 문단이 자간 0%로 2줄이 되어 큰 표가 다음 쪽으로 밀림).
        if 원본줄자간 and len(원본줄자간) == len(범위) and not 중단_요청됨():
            맞춘수 = 0
            for 문단번호, (원줄, _) in zip(범위, 원본줄자간):
                지금줄 = 문단_화면줄수(문단번호) if 원줄 else None
                if 지금줄 and 지금줄 > 원줄 and 문단_줄수_원본맞춤(문단번호, 원줄):
                    맞춘수 += 1
            if 맞춘수:
                쪽, 줄수 = 끝쪽()
                if 쪽 is not None and 쪽 <= 목표쪽:
                    완료 = True
                    로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 마지막 수단 + 줄이 늘어난 문단 {맞춘수}개를 어절 당김으로 원본 줄 수에 맞춤")
                    return True
        if 쪽 == 목표쪽 + 1 and 줄수 is not None and 줄수 < 4:
            hwp.SetPos(0, 범위.start, 0)
            첫위치 = hwp.GetPos()
            hwp.SetPos(0, 범위.stop - 1, 0)
            줄간격보관 = 보고서_줄간격_보관(첫위치, hwp.GetPos()) or []
            for 단계 in range(1, 11):
                if 중단_요청됨() or not 보고서_줄간격_적용(줄간격보관, 단계):
                    break
                쪽, 줄수 = 끝쪽()
                if 쪽 is not None and 쪽 <= 목표쪽:
                    완료 = True
                    로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 마지막 수단(위 간격 0pt·표 셀 여백 최소) + 줄간격 "
                         f"{단계 * 10}%p 축소(최소 {세트문장_최소줄간격_퍼센트}%)")
                    return True
        if 원본줄간격 and not 중단_요청됨():
            if not 줄간격보관:
                hwp.SetPos(0, 범위.start, 0)
                첫위치 = hwp.GetPos()
                hwp.SetPos(0, 범위.stop - 1, 0)
                줄간격보관 = 보고서_줄간격_보관(첫위치, hwp.GetPos()) or []
            if len(원본줄간격) == len(줄간격보관):
                # 원본보다 넓어진 문단만 원본 줄간격으로 되돌린다(표를 담은 문단은 줄간격이 표 높이에 곱해져
                # 분량을 크게 늘렸다. 실측: 145% → 160%).
                바꾼수 = 0
                for (pos, kind, value), (원형식, 원값) in zip(줄간격보관, 원본줄간격):
                    if 원형식 == kind and 0 < 원값 < value:
                        쪽맞춤_바꾼문단.add(tuple(pos[:2]))
                        hwp.SetPos(*pos)
                        act = hwp.CreateAction('ParagraphShape')
                        pset = act.CreateSet()
                        pset.SetItem('LineSpacingType', kind)
                        pset.SetItem('LineSpacing', 원값)
                        act.Execute(pset)
                        바꾼수 += 1
                쪽, 줄수 = 끝쪽()
                if 쪽 is not None and 쪽 <= 목표쪽:
                    완료 = True
                    로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 마지막 수단 + 넓어진 줄간격 {바꾼수}곳을 원본 값으로 되돌림")
                    return True
            try:
                percent = hwp.LineSpacingMethod('Percent')
            except Exception:
                percent = 0
            값들 = [v for k, v in 원본줄간격 if k == percent and v >= 100]
            원본줄간격 = min(값들) if 값들 else None
        if 원본줄간격 and 원본줄간격 < 세트문장_최소줄간격_퍼센트 and not 중단_요청됨():
            if not 줄간격보관:
                hwp.SetPos(0, 범위.start, 0)
                첫위치 = hwp.GetPos()
                hwp.SetPos(0, 범위.stop - 1, 0)
                줄간격보관 = 보고서_줄간격_보관(첫위치, hwp.GetPos()) or []
            기존하한 = 세트문장_최소줄간격_퍼센트
            세트문장_최소줄간격_퍼센트 = int(원본줄간격)
            try:
                for 단계 in range(1, 16):
                    if 중단_요청됨() or not 보고서_줄간격_적용(줄간격보관, 단계):
                        break
                    쪽, 줄수 = 끝쪽()
                    if 쪽 is not None and 쪽 <= 목표쪽:
                        완료 = True
                        로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 완료: 마지막 수단 + 줄간격을 원본 최소 줄간격 {원본줄간격}%까지 낮춤"
                             f"({단계 * 10}%p)")
                        return True
            finally:
                세트문장_최소줄간격_퍼센트 = 기존하한
        로그(f"보고서 {번호} {목표쪽수}쪽 맞춤 실패: 마지막 수단으로도 {목표쪽}쪽 안에 담지 못함(넘친 줄 {줄수}) — 원래 값으로 되돌림")
        return False
    finally:
        if not 완료:
            if 줄간격보관:
                _쪽맞춤_줄간격_되돌리기(줄간격보관)
            for 문단번호, 이전자간 in reversed(자간보관):
                문단_자간_적용(문단번호, 이전자간)
            쪽맞춤_레벨_적용(조사, 0)


_자간_항목 = ("SpacingHangul", "SpacingLatin", "SpacingHanja", "SpacingJapanese", "SpacingOther", "SpacingSymbol",
            "SpacingUser")


def 문단_화면줄수(번호):
    """본문 문단의 화면줄 수(모르면 None)."""
    원위치 = hwp.GetPos()
    try:
        hwp.SetPos(0, 번호, 0)
        if tuple(hwp.GetPos()[:2]) != (0, 번호):
            return None
        hwp_run('MoveParaEnd')
        끝 = hwp.GetPos()
        hwp.SetPos(0, 번호, 0)
        줄 = 0
        이전 = None
        while 줄 < 200:
            hwp_run('MoveLineEnd')
            줄끝 = hwp.GetPos()
            if 줄끝 == 이전 or 줄끝[1] != 번호:
                break
            줄 += 1
            if 줄끝[2] >= 끝[2]:
                break
            이전 = 줄끝
            hwp_run('MoveNextChar')
        return 줄
    except Exception:
        return None
    finally:
        try:
            hwp.SetPos(*원위치)
        except Exception:
            pass


def 문단_자간_읽기(번호):
    """본문 문단 전체를 선택했을 때의 자간 {항목: 값}(섞여 있으면 한/글이 주는 값). 실패하면 None."""
    원위치 = hwp.GetPos()
    try:
        hwp.SetPos(0, 번호, 0)
        hwp_run('MoveParaBegin')
        hwp_run('MoveSelParaEnd')
        act = hwp.CreateAction('CharShape')
        pset = act.CreateSet()
        act.GetDefault(pset)
        return {k: pset.Item(k) for k in _자간_항목}
    except Exception:
        return None
    finally:
        try:
            hwp_run('Cancel')
            hwp.SetPos(*원위치)
        except Exception:
            pass


def 문단_자간_적용(번호, 자간):
    """본문 문단 전체에 자간 {항목: 값}을 입힌다."""
    원위치 = hwp.GetPos()
    try:
        hwp.SetPos(0, 번호, 0)
        hwp_run('MoveParaBegin')
        hwp_run('MoveSelParaEnd')
        act = hwp.CreateAction('CharShape')
        pset = act.CreateSet()
        act.GetDefault(pset)
        for k, v in 자간.items():
            if v is not None:
                pset.SetItem(k, v)
        return act.Execute(pset) is not False
    except Exception:
        return False
    finally:
        try:
            hwp_run('Cancel')
            hwp.SetPos(*원위치)
        except Exception:
            pass


def _문단_줄시작들(번호):
    """본문 문단 화면줄마다 시작 위치 목록."""
    원위치 = hwp.GetPos()
    시작들 = []
    try:
        hwp.SetPos(0, 번호, 0)
        hwp_run('MoveParaEnd')
        끝 = hwp.GetPos()
        hwp.SetPos(0, 번호, 0)
        while len(시작들) < 200:
            시작들.append(tuple(hwp.GetPos()))
            hwp_run('MoveLineEnd')
            줄끝 = hwp.GetPos()
            if 줄끝[1] != 번호 or 줄끝[2] >= 끝[2]:
                break
            hwp_run('MoveNextChar')
            if tuple(hwp.GetPos()) == tuple(줄끝):
                break
        return 시작들
    finally:
        try:
            hwp.SetPos(*원위치)
        except Exception:
            pass


def 문단_줄수_원본맞춤(번호, 원줄):
    """원본보다 줄이 늘어난 문단에서 마지막 줄 어절을 자간을 줄여 앞 줄로 당겨 원본 줄 수에 맞춘다.

    기존 '다음 단어 당김'(다음단어_당김_시도)을 쓰되, 자간 상한(기본 10%)과 당길 어절 길이(기본 5자) 제한을
    본문 자간 최대치·20자까지 넓힌다(사용자 결정, 2026-10-09: 결과의 쪽 구성은 원본과 같아야 한다). 맞추면 True.
    """
    global 다음단어_당김_자간_최대_퍼센트, 문장부호_2줄_기준글자수
    기존 = (다음단어_당김_자간_최대_퍼센트, 문장부호_2줄_기준글자수)
    다음단어_당김_자간_최대_퍼센트 = max(기존[0], int(자간_최대시도_본문 or 0), 40)   # 실측: 15%로는 두 어절째를 못 당김
    문장부호_2줄_기준글자수 = max(기존[1], 20)
    try:
        for _ in range(12):
            if 중단_요청됨():
                return False
            시작들 = _문단_줄시작들(번호)
            if len(시작들) <= 원줄:
                return True
            if len(시작들) < 2 or not 다음단어_당김_시도(시작들[-2], 다음단어_당김_자간_최대_퍼센트):
                return False
        return len(_문단_줄시작들(번호)) <= 원줄
    finally:
        다음단어_당김_자간_최대_퍼센트, 문장부호_2줄_기준글자수 = 기존


def 보고서_새쪽_시작인가(시작문단):
    """보고서 첫 문단(제목 표)이 새 쪽에서 시작하는지: 바로 앞 문단 끝보다 뒤 쪽에 있으면 True.

    쪽첫줄_시작인가(MovePageBegin 비교)는 제목 표가 문단 중간 위치에 놓이면 쪽 첫머리에 있어도 False라
    보고서 경계 쪽 나누기가 한 번도 들어가지 않았다(2026-10-09 실측).
    """
    if 시작문단 <= 0:
        return True
    원위치 = hwp.GetPos()
    try:
        hwp.SetPos(0, 시작문단, 0)
        쪽 = 현재_페이지번호()
        hwp.SetPos(0, 시작문단 - 1, 0)
        hwp_run('MoveParaEnd')
        앞쪽 = 현재_페이지번호()
        return bool(쪽 and 앞쪽 and 쪽 > 앞쪽)
    except Exception:
        return False
    finally:
        try:
            hwp.SetPos(*원위치)
        except Exception:
            pass


def _대표_줄간격(목록):
    """원본 줄간격 목록에서 가장 많이 쓰인 비율 줄간격(없으면 None)."""
    try:
        percent = hwp.LineSpacingMethod('Percent')
    except Exception:
        percent = 0
    값들 = [value for kind, value in (목록 or []) if kind == percent and value > 0]
    return max(set(값들), key=값들.count) if 값들 else None


def 쪽맞춤_원본_보고서_기록():
    """처리 전 문서의 보고서별 쪽 수를 기록한다(결과에서도 보고서마다 이 쪽 수 안에 담는다)."""
    global 쪽맞춤_원본_보고서
    쪽맞춤_원본_보고서 = None
    # 쪽 구성 동일 원칙은 서식 통일에서만 쓴다(사용자 지정, 2026-10-09). 한 번에 적용·서식 적용은 문서 유형별
    # 쪽 맞춤(1쪽 보고서는 1쪽)만 한다.
    if not (작업_모드 == 'unify' and 쪽맞춤_유형판정_사용 and 페이지맞춤_문단간격_사용 and hwp is not None
            and stage_enabled(선택_세부작업, 'page_layout_keep', 작업_모드)):
        return
    try:
        보고서, 제목문단 = 쪽맞춤_보고서_목록()
        if not 보고서:
            return
        def 줄간격목록(r):
            try:
                보관 = 보고서_줄간격_보관((0, r['문단범위'].start, 0), (0, r['문단범위'].stop - 1, 0)) or []
            except Exception:
                return None
            return [(kind, value) for _, kind, value in 보관]
        def 줄과자간(r):
            return [(문단_화면줄수(번호), None) for 번호 in r['문단범위']]
        쪽맞춤_원본_보고서 = [(r['end'] - r['start'] + 1, 보고서_새쪽_시작인가(r['문단범위'].start), 줄간격목록(r),
                          줄과자간(r)) for r in 보고서]
        로그(f"[문서 유형] 원본 보고서 {len(보고서)}개(제목 표 {len(제목문단)}개), 보고서별 쪽 수 "
             f"{[x[0] for x in 쪽맞춤_원본_보고서]}, 대표 줄간격 {[_대표_줄간격(x[2]) for x in 쪽맞춤_원본_보고서]}% — "
             "결과에서도 이 쪽 수 안에 담음")
    except Exception as e:
        로그(f"원본 보고서 쪽 수 기록 실패(무시): {e}")
    finally:
        _표칸영역.clear()


def _보고서_내부_쪽나눔_해제(보고서):
    """보고서 첫 문단(제목 표)을 뺀 문단의 '문단 앞 쪽 나눔'을 푼다. 푼 개수."""
    해제 = 0
    원위치 = hwp.GetPos()
    try:
        for 번호 in list(보고서['문단범위'])[1:]:
            hwp.SetPos(0, 번호, 0)
            if tuple(hwp.GetPos()[:2]) != (0, 번호):
                continue
            act = hwp.CreateAction('ParagraphShape')
            pset = act.CreateSet()
            act.GetDefault(pset)
            if int(pset.Item('PagebreakBefore') or 0):
                쪽나눔_설정((0, 번호, 0), False)
                해제 += 1
    finally:
        hwp.SetPos(*원위치)
    return 해제


def _문서유형별_쪽맞춤():
    """문서 유형을 판정해 보고서마다 정해진 쪽 수 안에 담는다.

    원본 보고서 쪽 수를 기록해 두었으면(보고서 수가 같을 때) 보고서마다 그 쪽 수가 목표다(사용자 지적, 2026-10-09:
    원본에서 1쪽이던 보고서가 결과에서 2쪽으로 퍼짐). 없으면 1쪽 보고서(넘친 줄 4줄 이하)만 1쪽에 맞춘다.
    처리했으면 True. 심화보고서이거나 판정하지 못하면 False(기존 '마지막 쪽 당기기'를 쓴다).
    """
    global _쪽맞춤_표캐시
    쪽맞춤_바꾼문단.clear()
    _쪽맞춤_표캐시 = {}
    try:
        return _문서유형별_쪽맞춤_본체()
    finally:
        _쪽맞춤_표캐시 = None
        _쪽맞춤_바꾼문단_단어분리_재검사()


def _쪽맞춤_바꾼문단_단어분리_재검사():
    """보고서 쪽 맞춤이 고친 문단만 본문 자간·단어 분리 조정을 다시 한다(다음 단어 당김 제외)."""
    global 재검사_대상문단, 다음단어_당김_사용
    대상 = set(쪽맞춤_바꾼문단)
    쪽맞춤_바꾼문단.clear()
    if not 대상 or 중단_요청됨() or not (stage_enabled(선택_세부작업, 'body_spacing')
                                       or stage_enabled(선택_세부작업, 'word_check')):
        return
    로그(f"[쪽 수 맞춤] 간격·줄간격을 바꾼 {len(대상)}개 문단의 단어 분리 재검사")
    재검사_대상문단, 다음단어_당김_사용 = 대상, False
    try:
        순회_시작()
        본문_기존자간조정()
    except Exception as e:
        로그(f"쪽 수 맞춤 뒤 단어 분리 재검사 실패(무시): {e}")
    finally:
        재검사_대상문단, 다음단어_당김_사용 = None, True


def _문서유형별_쪽맞춤_본체():
    global 쪽맞춤_보고서조정됨
    쪽맞춤_보고서조정됨 = False
    보고서, 제목문단 = 쪽맞춤_보고서_목록()
    if not 보고서:
        로그("[문서 유형] 보고서 쪽 범위를 확인하지 못해 기존 방식으로 쪽 수를 맞춥니다.")
        return False
    원본 = 쪽맞춤_원본_보고서 if 쪽맞춤_원본_보고서 and len(쪽맞춤_원본_보고서) == len(보고서) else None
    유형, 대상 = 쪽맞춤_문서유형_판정(보고서, 페이지맞춤_최대남은줄수)
    if 원본 is not None:
        유형 = ('취합보고서' if len(보고서) > 1 else '1쪽 보고서' if 원본[0][0] == 1 else '심화보고서')
        목표 = {i: x[0] for i, x in enumerate(원본)}
        새쪽 = {i for i, x in enumerate(원본) if i and x[1]}
    else:
        목표 = {i: 1 for i in 대상}
        # 1쪽 분량 보고서(두 쪽 이하)가 쪽 중간에서 시작하면 새 쪽에서 시작한다(사용자 결정, 2026-10-09).
        새쪽 = {i for i, r in enumerate(보고서) if i and 유형 == '취합보고서' and r['end'] - r['start'] <= 1}
    요약 = ", ".join(f"{i + 1}:{r['start']}~{r['end']}쪽" for i, r in enumerate(보고서[:12]))
    로그(f"[문서 유형] {유형} — 제목 표 {len(제목문단)}개, 보고서 {len(보고서)}개({요약}"
         f"{' …' if len(보고서) > 12 else ''})"
         f"{', 원본 쪽 수 ' + str([x[0] for x in 원본]) if 원본 else ''}")
    if 유형 == '심화보고서' and 원본 is None:
        return False
    for 번호 in range(len(보고서)):
        if 중단_요청됨():
            return True
        if 번호 not in 목표 and 번호 not in 새쪽:
            continue
        # 앞 보고서를 바꾸면 뒤 보고서의 쪽이 바뀌므로 매번 다시 잰다(이 보고서만).
        현재목록, _ = 쪽맞춤_보고서_목록(제목문단, 대상=번호)
        if not 현재목록 or 번호 >= len(현재목록) or 현재목록[번호] is None:
            break
        항목 = 현재목록[번호]
        위치 = (0, 항목['문단범위'].start, 0)
        # 원본에서 새 쪽에 시작한 보고서는 지금 쪽 첫머리에 있어도 쪽 나누기를 넣는다. 넣지 않으면 앞 보고서가
        # 나중에(쪽 배치 등) 늘어날 때 함께 밀렸다(2026-10-09 실측: 보고서 5~8이 한 쪽씩 밀림).
        if 번호 in 새쪽 and not 쪽나눔_켜짐(위치):
            쪽나눔_설정(위치, True)
            쪽맞춤_보고서조정됨 = True
            로그(f"[문서 유형] 보고서 {번호 + 1}을 새 쪽에서 시작")
            항목 = 쪽맞춤_보고서_목록(제목문단, 대상=번호)[0][번호]
        if 번호 not in 목표 or 항목['end'] - 항목['start'] + 1 <= 목표[번호]:
            continue
        # 쪽 배치가 넣은 보고서 안의 쪽 나눔은 걷어내고 다시 잰다(원본에는 없던 빈 쪽을 만든다).
        if _보고서_내부_쪽나눔_해제(항목):
            쪽맞춤_보고서조정됨 = True
            항목 = 쪽맞춤_보고서_목록(제목문단, 대상=번호)[0][번호]
            if 항목['end'] - 항목['start'] + 1 <= 목표[번호]:
                로그(f"보고서 {번호 + 1}: 보고서 안 쪽 나눔을 풀어 {목표[번호]}쪽 안에 들어감")
                continue
        if 보고서_1쪽_맞춤(항목, 번호 + 1, 목표[번호], 원본[번호][2] if 원본 is not None else None,
                       원본[번호][3] if 원본 is not None else None):
            쪽맞춤_보고서조정됨 = True
        else:
            hwp.SetPos(*위치)
            검수_문제_기록(현재_처리파일, f"[보고서 쪽 수 초과] 보고서 {번호 + 1}이 원래 {목표[번호]}쪽 안에 담기지 않음")
    return True


def 보고서_페이지수_맞춤_전체_적용():
    """마지막 쪽에 몇 줄 안 되는 내용만 걸쳐 있으면(다음 쪽으로 밀려난
    상황), 문단 아래 간격을 줄여 앞쪽 쪽으로 당겨오도록 시도한다.

    목표 쪽수를 사용자가 지정하지 않아도 되도록, "마지막 쪽 줄 수가
    적다"는 것 자체를 트리거로 쓴다 — 이 값이 크면(내용이 많이 남은
    경우) 간격 조정만으로는 해결이 안 되는 상황이라 아예 시도하지
    않는다. 실패해도 문서 자체는 항상 그대로 저장 가능한 상태로
    남는다(마지막 시도 이후 값이 남아있을 뿐, 구조를 깨지 않음).
    """
    global 쪽맞춤_묶음_확인됨, 쪽맞춤_묶음이동_결정
    # 여러 문서를 이어 처리할 때 앞 문서의 판단이 남지 않도록 매번 지운다.
    쪽맞춤_묶음_확인됨 = False
    쪽맞춤_묶음이동_결정 = False
    if not 페이지맞춤_문단간격_사용:
        return True
    if 중단_요청됨():
        return False
    if 쪽맞춤_유형판정_사용:
        try:
            처리됨 = _문서유형별_쪽맞춤()
        except Exception as e:
            로그(f"문서 유형 판정 실패(무시하고 기존 방식): {e}")
            처리됨 = False
        if 처리됨:
            hwp_run('MoveDocBegin')
            return True
    마지막쪽, 줄수 = 마지막쪽_화면줄수()
    if 마지막쪽 is None or 줄수 is None:
        로그("페이지 수 맞춤 건너뜀: 마지막 쪽 정보 확인 실패")
        return True
    if 마지막쪽 <= 1 or 줄수 > 페이지맞춤_최대남은줄수:
        로그(f"페이지 수 맞춤 불필요: 마지막 쪽({마지막쪽}쪽)에 {줄수}줄 "
             f"(당겨올 기준 {페이지맞춤_최대남은줄수}줄 이하가 아님)")
        return True
    로그(f"마지막 쪽({마지막쪽}쪽)에 {줄수}줄만 남아 페이지 수 맞춤을 시도합니다.")
    보고서_페이지수_맞춤_시도(마지막쪽 - 1)
    hwp_run('MoveDocBegin')
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
    if 현재_한칸표인가():
        return 0
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
    if 현재_한칸표인가():
        return 0
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


_콜론_공백류 = " \t\u00A0\u3000"
_콜론_문자 = (":", "：")
_콜론_앞_닫는문자 = ")]}>」』”’'\""
_콜론_뒤_제외 = ")]}>」』”’"


def _콜론_한글인가(ch):
    return "\uAC00" <= ch <= "\uD7A3"


def 콜론_공백_보정_대상(text):
    """콜론 주변 공백을 `글자: 글자` 형식으로 맞출 구간을 반환한다.

    규칙(2026-10-10 사용자 지시):
      - 콜론 앞: 글자(숫자·닫는 괄호 포함)와 콜론 사이 공백 0칸
      - 콜론 뒤: 다음 글자와 사이에 ASCII 공백 정확히 1칸

    건드리지 않는 경우: 숫자:숫자(시각·비율), `::`, 콜론 뒤 `/`·`\\`·닫는 괄호,
    영문·숫자끼리 붙은 `mailto:abc`·`C:` 꼴(주소·경로일 수 있음, 붙은 곳에 공백을 넣지 않음),
    문단 맨 앞 콜론. 콜론 문자 자체(반각/전각)는 바꾸지 않는다.

    반환값: [(시작, 끝, 교체문자열), ...] 왼쪽에서 오른쪽, 서로 겹치지 않음.
    """
    결과 = []
    if not text or not any(c in text for c in _콜론_문자):
        return 결과
    n = len(text)
    for 위치, ch in enumerate(text):
        if ch not in _콜론_문자:
            continue
        왼쪽 = 위치 - 1
        while 왼쪽 >= 0 and text[왼쪽] in _콜론_공백류:
            왼쪽 -= 1
        if 왼쪽 < 0:
            continue
        앞 = text[왼쪽]
        if not (앞.isalnum() or 앞 in _콜론_앞_닫는문자):
            continue
        오른쪽 = 위치 + 1
        while 오른쪽 < n and text[오른쪽] in _콜론_공백류:
            오른쪽 += 1
        뒤 = text[오른쪽] if 오른쪽 < n else ""
        if 뒤 in _콜론_문자:
            continue
        if 앞.isdigit() and 뒤.isdigit():
            continue
        왼쪽공백 = (왼쪽 + 1, 위치)
        if 왼쪽공백[0] < 왼쪽공백[1]:
            결과.append((왼쪽공백[0], 왼쪽공백[1], ""))
        if not 뒤:
            continue
        if 뒤 in "/\\" or 뒤 in _콜론_뒤_제외:
            continue
        오른공백 = (위치 + 1, 오른쪽)
        if 오른공백[0] == 오른공백[1]:
            # 붙어 있는 경우: 한글이 한쪽에 있을 때만 공백을 넣는다(URL·경로 보호).
            if not (_콜론_한글인가(앞) or _콜론_한글인가(뒤)):
                continue
            결과.append((오른공백[0], 오른공백[1], " "))
        elif text[오른공백[0]:오른공백[1]] != " ":
            결과.append((오른공백[0], 오른공백[1], " "))
    return 결과


def 콜론_공백_정리_문단_처리():
    """현재 문단의 콜론 주변 공백을 `글자: 글자` 형식으로 정규화한다."""
    if 현재_한칸표인가():
        return 0
    text = 현재문단_텍스트()
    수정구간 = 콜론_공백_보정_대상(text)
    if not 수정구간:
        return 0

    문단_시작위치 = hwp.GetPos()
    수정수 = 0
    try:
        # 오른쪽부터 처리하여 앞쪽 문자 위치가 변하지 않게 한다.
        for 시작, 끝, 교체 in reversed(수정구간):
            try:
                if 끝 > 시작:
                    문단_범위_선택(문단_시작위치, 시작, 끝)
                    hwp_run("Delete")
                else:
                    hwp.SetPos(
                        문단_시작위치[0],
                        문단_시작위치[1],
                        문단_시작위치[2] + 시작,
                    )
                if 교체:
                    텍스트_삽입(교체)
                수정수 += 1
            except Exception as e:
                로그(f"콜론 공백 보정 실패(무시): {e}")
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


_단어사이_공백류 = (" ", "\t", "　")
# '일    시:', '총  무  과:'처럼 글자 사이를 띄워 긴 라벨('참석인원:')과 폭을 맞춘 문두 콜론 라벨.
# 이 공백은 정렬용이라 줄이면 같은 묶음의 콜론·둘째 줄 위치가 어긋난다(실측: 10월 확대간부회의 자료 24곳).
_균등라벨_패턴 = re.compile(r"(?:\S{1,2}[ \t　]+)?(\S(?:[ \t　]+\S){1,5})[ \t　]*[:：]")


def _균등라벨_범위(text, 시작=0):
    """text[시작:]이 (항목기호 +) 한 글자씩 띄운 콜론 라벨로 시작하면 라벨의 (처음, 끝), 아니면 None."""
    m = _균등라벨_패턴.match(text, 시작)
    return m.span(1) if m else None


def 단어사이_연속공백_정리_대상(text):
    """문단 안에서 단어 사이의 공백류(2칸 이상, 또는 탭·전각공백 1칸)를
    표준 반각 공백 1칸으로 줄일 구간을 찾는다.

    문단 맨 앞의 들여쓰기 공백(□/ㅇ/- 등 항목 위치나 세트문장 후속 판정에
    쓰이는 선행 공백)은 이 정리의 대상이 아니므로 건드리지 않고, 실제
    내용이 시작된 뒤에 나오는 공백류만 대상으로 한다. 탭·전각공백은
    자동 탭 간격이 규격과 안 맞아 수기로 스페이스를 끼워 넣은 흔적인
    경우가 많아, 연속이 아니어도(1칸이라도) 표준 공백이 아니면 대상으로
    삼는다. '일    시:'처럼 한 글자씩 띄워 폭을 맞춘 문두 콜론 라벨 안의
    공백은 정렬용이므로 그대로 둔다.
    """
    결과 = []
    if not text:
        return 결과
    벗긴텍스트 = text.lstrip("".join(_단어사이_공백류))
    선행공백_길이 = len(text) - len(벗긴텍스트)
    라벨 = _균등라벨_범위(text, 선행공백_길이)
    # '바랍니다.  끝.'·'붙임  계획서 1부.'의 2타는 공식 규정(2025 행정업무운영 편람)이라 줄이지 않는다.
    공식2타 = official_double_space_spans(text)
    i = 선행공백_길이
    n = len(text)
    while i < n:
        if text[i] in _단어사이_공백류:
            시작 = i
            while i < n and text[i] in _단어사이_공백류:
                i += 1
            if 라벨 and 라벨[0] < 시작 and i < 라벨[1]:
                continue
            if any(처음 < i and 시작 < 끝 for 처음, 끝 in 공식2타):
                continue
            if i - 시작 > 1 or text[시작] != " ":
                결과.append((시작, i))
        else:
            i += 1
    return 결과


def 단어사이_연속공백_정리_문단_처리():
    """현재 문단에서 단어 사이의 연속 공백(2칸 이상)을 1칸으로 줄인다."""
    if 현재_한칸표인가():
        return 0
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


def 문두_미음_기호_위치(text):
    """문단 첫 비공백 문자가 항목기호 ㅁ일 때만 위치를 반환한다."""
    stripped = (text or "").lstrip()
    if not stripped.startswith("ㅁ"):
        return None
    return len(text) - len(stripped)


def 문두_미음_기호_정리():
    # 기존 한 칸 표 보호 정책을 유지한다.
    if 현재_한칸표인가():
        return 0
    text = 현재문단_텍스트()
    offset = 문두_미음_기호_위치(text)
    if offset is None:
        return 0
    start = hwp.GetPos()
    try:
        if 문단_범위_선택(start, offset, offset + 1) is False:
            raise RuntimeError("문두 ㅁ 선택 실패")
        텍스트_삽입("□")
        return 1
    finally:
        hwp_run("Cancel")
        hwp.SetPos(*start)


def 연도_따옴표_정리_문단_처리():
    """현재 문단에서 연도 앞의 작은따옴표만 ’로 바꾼다."""
    text = 현재문단_텍스트()
    matches = list(YEAR_QUOTE_PATTERN.finditer(text or ""))
    if not matches:
        return 0
    start = hwp.GetPos()
    changed = 0
    try:
        for match in reversed(matches):
            if 문단_범위_선택(start, match.start(), match.end()) is False:
                raise RuntimeError("연도 앞 따옴표 선택 실패")
            텍스트_삽입("’")
            changed += 1
    finally:
        hwp_run("Cancel")
        hwp.SetPos(*start)
    return changed


def 곧은따옴표_통일_문단_처리():
    """현재 문단에서 곧은 큰따옴표(")를 한글 표준 둥근따옴표(" ")로 바꾼다.

    작은따옴표는 여기서 다루지 않는다 — 발·분 표기(6' 2")나 영어 축약형과
    진짜 인용부호를 구분할 방법이 없어, 연도 앞 표기처럼 문맥이 분명한
    좁은 규칙(연도_따옴표_정리_문단_처리)만 따로 둔다.
    """
    text = 현재문단_텍스트()
    replacements = straight_double_quote_replacements(text or "")
    if not replacements:
        return 0
    start = hwp.GetPos()
    changed = 0
    try:
        for index, replacement in reversed(replacements):
            if 문단_범위_선택(start, index, index + 1) is False:
                raise RuntimeError("곧은따옴표 선택 실패")
            텍스트_삽입(replacement)
            changed += 1
    finally:
        hwp_run("Cancel")
        hwp.SetPos(*start)
    return changed


def 작은따옴표_통일_문단_처리():
    """현재 문단에서 곧은 작은따옴표(')를 한글 표준 둥근따옴표(' ')로 바꾼다.

    연도 앞 표기('26년)는 이미 앞서 실행되는 연도_따옴표_정리_문단_처리가
    처리하므로, 여기 도달하는 '는 일반 인용부호로 보고 문맥(앞 글자)으로
    여는/닫는 방향을 판정한다. 숫자 뒤에 오는 '(6', 37° 33')는 발·분 표기로
    보아 건드리지 않는다 — curly_single_quote_replacements 참고.
    """
    text = 현재문단_텍스트()
    replacements = curly_single_quote_replacements(text or "")
    if not replacements:
        return 0
    start = hwp.GetPos()
    changed = 0
    try:
        for index, replacement in reversed(replacements):
            if 문단_범위_선택(start, index, index + 1) is False:
                raise RuntimeError("작은따옴표 선택 실패")
            텍스트_삽입(replacement)
            changed += 1
    finally:
        hwp_run("Cancel")
        hwp.SetPos(*start)
    return changed


def 날짜_구분자_정리_문단_처리():
    """현재 문단에서 날짜·기간·시간 표기의 대시류(-,–,—)를 물결표(~)로,
    날짜 뒤 빠진 온점과 요일 괄호 앞뒤 온점 위치를 표준에 맞춘다.

    normalize_date_range_marks가 만든 결과 문자열과 원문을 비교해 바뀐
    구간만 역순으로 적용한다(text_edit_spans) — 전화번호·법령 조항·사업
    코드처럼 점(.) 없는 하이픈은 애초에 패턴에 안 걸려 손대지 않는다.
    """
    text = 현재문단_텍스트()
    if not text:
        return 0
    변환후 = normalize_date_range_marks(text)
    spans = text_edit_spans(text, 변환후)
    if not spans:
        return 0
    문단_시작위치 = hwp.GetPos()
    수정수 = 0
    try:
        for 시작, 끝, 대체 in sorted(spans, key=lambda s: s[0], reverse=True):
            try:
                if 끝 > 시작:
                    if 문단_범위_선택(문단_시작위치, 시작, 끝) is False:
                        raise RuntimeError("날짜 구분자 구간 선택 실패")
                    if hwp_run("Delete") is False:
                        raise RuntimeError("날짜 구분자 구간 삭제 실패")
                    hwp.SetPos(*문단_시작위치)
                if 대체:
                    hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2] + 시작)
                    텍스트_삽입(대체)
                수정수 += 1
            except Exception as e:
                로그(f"날짜 구분자 정리 실패(무시): {e}")
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


def 공문_띄어쓰기_정리_문단_처리():
    """현재 문단에 「2025 행정업무운영 편람」 띄어쓰기 규정을 적용한다(normalize_official_spacing).

    '끝.' 앞·'붙임' 뒤 2타, 날짜 '2021. 12. 12.'(마침표 뒤 1타, 0 생략). 바뀐 구간만 뒤에서부터 고친다.
    """
    text = 현재문단_텍스트()
    if not text:
        return 0
    normalized = normalize_official_spacing(text)
    if normalize_attachment_list_header(text) != text:
        normalized = normalize_attachment_list_header(normalized)
    spans = text_edit_spans(text, normalized)
    if not spans:
        return 0
    문단_시작위치 = hwp.GetPos()
    수정수 = 0
    try:
        for 시작, 끝, 대체 in sorted(spans, key=lambda s: s[0], reverse=True):
            try:
                if 끝 > 시작:
                    if 문단_범위_선택(문단_시작위치, 시작, 끝) is False:
                        raise RuntimeError("공문 띄어쓰기 구간 선택 실패")
                    if hwp_run("Delete") is False:
                        raise RuntimeError("공문 띄어쓰기 구간 삭제 실패")
                    hwp.SetPos(*문단_시작위치)
                if 대체:
                    hwp.SetPos(문단_시작위치[0], 문단_시작위치[1], 문단_시작위치[2] + 시작)
                    텍스트_삽입(대체)
                수정수 += 1
            except Exception as e:
                로그(f"공문 띄어쓰기 정리 실패(무시): {e}")
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


def 공문_띄어쓰기_전체_적용():
    """자간 정리 작업에서 문서 전체에 공문 띄어쓰기 규정을 적용한다(서식 작업은 공백 정규화에서 한다)."""
    if hwp is None:
        return True
    if 중단_요청됨():
        return False
    순회_시작()
    수정수 = 0
    정체횟수 = 0
    while True:
        if 중단_요청됨():
            return False
        시작위치 = hwp.GetPos()
        수정수 += 공문_띄어쓰기_정리_문단_처리()
        if not 범위_다음_문단으로_진행():
            break
        if hwp.GetPos() == 시작위치:
            정체횟수 += 1
            if 정체횟수 >= 2:
                break
        else:
            정체횟수 = 0
    로그(f"공문 띄어쓰기 규정(끝 표시·붙임 2타, 날짜 표기) 적용: {수정수}건")
    return True


def 문장내_공백_정규화_전체_적용():
    """괄호 안쪽 공백 + 단어 사이 쉼표 공백 + 단어 사이 연속 공백을 문서 전체에 적용한다."""
    if 중단_요청됨():
        return False

    로그("문장 내 공백 정규화 시작")

    # 1) 괄호 공백은 HWP 자체 AllReplace로 먼저 처리한다.
    #    문자 런/서식 경계를 넘는 경우에도 직접 좌표 삭제보다 안정적이다.
    # AllReplace는 문서 전체를 바꾸므로 쪽 범위를 지정한 작업에서는 쓰지 않고 문단 단위 보정만 한다.
    allreplace_실행수 = 0 if (한칸표_보호영역 or 쪽범위_사용중()) else 괄호_안쪽_공백_정리_AllReplace()

    # 2) 문단 단위 안전 보정 + 쉼표 공백 보정(앞 0칸 / 뒤 1칸) + 연속 공백 정리(2칸 이상 -> 1칸).
    #    기존 v1.7의 `list id == 0` 제한을 제거하여 접근 가능한 모든 문단에 적용한다.
    global _문단글_캐시
    _문단글_캐시 = {} if 알파_문단글_캐시_사용 else None
    try:
        return _문장내_공백_정규화_순회(allreplace_실행수)
    finally:
        _문단글_캐시 = None


def _문장내_공백_정규화_순회(allreplace_실행수):
    순회_시작()
    괄호삭제수 = 0
    쉼표수정수 = 0
    콜론수정수 = 0
    연속공백수정수 = 0
    기호수정수 = 0
    연도따옴표수정수 = 0
    따옴표수정수 = 0
    작은따옴표수정수 = 0
    날짜구분자수정수 = 0
    공문수정수 = 0
    방문문단수 = 0
    정체횟수 = 0

    while True:
        if 중단_요청됨():
            return False

        시작위치 = hwp.GetPos()
        방문문단수 += 1

        결과 = []
        for 규칙 in (문두_미음_기호_정리, 연도_따옴표_정리_문단_처리, 곧은따옴표_통일_문단_처리,
                   작은따옴표_통일_문단_처리, 날짜_구분자_정리_문단_처리, 괄호_안쪽_공백_정리_문단_처리,
                   쉼표_공백_정리_문단_처리, 콜론_공백_정리_문단_처리, 단어사이_연속공백_정리_문단_처리,
                   # 연속 공백을 줄인 뒤 공식 규정의 2타·날짜 띄어쓰기를 맞춘다(2025 행정업무운영 편람).
                   공문_띄어쓰기_정리_문단_처리):
            값 = 규칙() or 0
            if 값:
                _문단글_캐시_비우기()     # 글을 고쳤으면 다음 규칙은 새로 읽는다
            결과.append(값)
        (기호, 연도, 따옴표, 작은, 날짜, 괄호, 쉼표, 콜론, 연속, 공문) = 결과
        기호수정수 += 기호
        연도따옴표수정수 += 연도
        따옴표수정수 += 따옴표
        작은따옴표수정수 += 작은
        날짜구분자수정수 += 날짜
        괄호삭제수 += 괄호
        쉼표수정수 += 쉼표
        콜론수정수 += 콜론
        연속공백수정수 += 연속
        공문수정수 += 공문

        if not 범위_다음_문단으로_진행():
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
        f"문두 ㅁ→□ {기호수정수}건 / 연도 따옴표 {연도따옴표수정수}건 / 곧은따옴표 {따옴표수정수}건 / "
        f"작은따옴표 {작은따옴표수정수}건 / 날짜 구분자 {날짜구분자수정수}건 / "
        f"괄호 후방삭제 {괄호삭제수}자 / 쉼표 공백 {쉼표수정수}건 / 콜론 공백 {콜론수정수}건 / 연속 공백 {연속공백수정수}건 / "
        f"공문 띄어쓰기 규정 {공문수정수}건)"
    )
    return True


# 이전 함수명을 호출하는 외부/기존 코드와의 호환성 유지
def 괄호_안쪽_공백_정리_전체_적용():
    return 문장내_공백_정규화_전체_적용()


def 문장부호_뒤_공백_보정_문단_처리():
    if 현재_한칸표인가():
        return 0
    text = 현재문단_텍스트()
    if not text:
        return False
    마커_끝 = 문장부호_마커_끝위치(text)
    조치 = marker_space_fix(text, 마커_끝)
    if 조치 is None:
        return False

    문단_시작위치 = hwp.GetPos()
    try:
        if 조치 == "replace":
            # 탭·전각공백 등 다른 공백류가 이미 있으면 지우고 표준 반각
            # 공백 한 칸으로 다시 넣는다(그냥 앞에 삽입만 하면 두 공백이
            # 함께 남는다).
            if 문단_범위_선택(문단_시작위치, 마커_끝, 마커_끝 + 1) is False:
                raise RuntimeError("공백류 문자 선택 실패")
            if hwp_run("Delete") is False:
                raise RuntimeError("공백류 문자 삭제 실패")
            hwp.SetPos(*문단_시작위치)
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
    순회_시작()
    총_적용_횟수 = 0

    while True:
        if 중단_요청됨():
            return False
        if 문장부호_뒤_공백_보정_문단_처리():
            총_적용_횟수 += 1
        if not 범위_다음_문단으로_진행():
            break

    로그(f"문장부호 뒤 공백 보정 완료 (총 {총_적용_횟수}건)")
    return True

# 알파: 문단 글 읽기 캐시(2026-10-09). 공백 정규화는 문단마다 규칙 9개가 각자 문단 글을 다시 읽었다(읽기 1번에
# COM 호출 약 7번). 순회하는 동안 한 번 읽은 글을 같은 문단의 다음 규칙이 다시 쓰고, 규칙이 글을 고치면 비운다.
# 끄면(False) 베타와 같다.
알파_문단글_캐시_사용 = True
_문단글_캐시 = None      # None이면 캐시를 쓰지 않음, dict이면 {(리스트, 문단): (편집 세대, 글)}


# 알파 C2(2026-10-10): 문단 글 캐시를 쪽 배치 단계와 저장 결과 검사에도 켠다. 프로파일 실측(기준 파일):
# 저장 후 검수 13.3초 중 쪽 배치 최종 검사 10.1초, 그 대부분이 같은 문단 글을 묶음마다 다시 읽는 시간
# (현재문단_텍스트 1회 약 22ms). 편집하면 편집 세대가 바뀌어 다시 읽으므로 결과는 같다. 끄면(False) 베타와 같다.
알파_문단글_캐시_확대_사용 = True


def 문단글_캐시_구간(함수):
    """함수가 도는 동안만 문단 글 캐시를 켠다(이미 켜져 있으면 그대로 쓴다)."""
    def 감싼(*args, **kwargs):
        global _문단글_캐시
        if not 알파_문단글_캐시_확대_사용 or _문단글_캐시 is not None:
            return 함수(*args, **kwargs)
        _문단글_캐시 = {}
        try:
            return 함수(*args, **kwargs)
        finally:
            _문단글_캐시 = None
    감싼.__name__ = getattr(함수, '__name__', '문단글_캐시_구간')
    return 감싼


def _문단글_캐시_비우기():
    if _문단글_캐시 is not None:
        _문단글_캐시.clear()


def 현재문단_텍스트():
    if _문단글_캐시 is not None:
        try:
            hwp.Run("MoveParaBegin")      # 원래 함수처럼 커서를 문단 시작에 둔다
            키 = tuple(hwp.GetPos()[:2])
            저장 = _문단글_캐시.get(키)
            if 저장 is not None and 저장[0] == _문서_편집_세대:
                return 저장[1]
            세대 = _문서_편집_세대
            글, 성공 = _현재문단_텍스트_읽기_상태()
            if not 성공:
                # 일시적 읽기 실패는 빈 문단으로 기억하지 않고 한 번 더 읽는다(Beta 12 리뷰 R4).
                글, 성공 = _현재문단_텍스트_읽기_상태()
            if 성공:
                _문단글_캐시[키] = (세대, 글)
            return 글
        except Exception:
            return _현재문단_텍스트_읽기()
    return _현재문단_텍스트_읽기()


def _현재문단_텍스트_읽기():
    return _현재문단_텍스트_읽기_상태()[0]


def _현재문단_텍스트_읽기_상태():
    """(문단 글, 읽기 성공 여부). 실패하면 ("", False) — 실제 빈 문단과 구별한다."""
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
        return text or "", True
    except Exception:
        try:
            hwp.Run("Cancel")
        except Exception:
            pass
        return "", False

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
    """짧은 마지막 줄을 앞줄로 당긴다. 조정할 본문이 없는 줄(문두 보호)은 건너뛴다."""
    return _문두보호_줄건너뜀(_문장부호_줄병합_시도_본체)


def _문장부호_줄병합_시도_본체():
    if 현재_한칸표인가():
        return True
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
    순회_시작()
    직전위치 = None
    정체횟수 = 0
    검사문단 = None

    while hwp.GetPos() != 끝위치:
        if 중단_요청됨():
            return False
        현재위치 = hwp.GetPos()
        if 쪽범위_끝지남(현재위치):
            return True
        if (_알파_일괄서식_문서 and 현재위치[0] == 0
                and tuple(현재위치[:2]) != 검사문단):
            검사문단 = tuple(현재위치[:2])
            if _알파_한줄문단인가(현재위치):
                hwp_run('MoveParaEnd')
                문단끝 = hwp.GetPos()
                hwp_run('MoveNextChar')
                if hwp.GetPos() == 문단끝:
                    return True
                continue
        if ((not 쪽범위_안인가(현재위치)) or (not 재검사_대상인가(현재위치))
                or 표셀_자간_제외인가()):
            # 작업 쪽 범위 밖, 2차 이후 재검사 대상이 아닌 문단, '표 안 문장 제외'인
            # 표 셀이면 줄 병합을 하지 않고 넘어간다.
            try:
                hwp_run("MoveParaEnd")
                hwp_run("MoveNextChar")
            except Exception:
                pass
            if hwp.GetPos() == 현재위치:
                return True
            직전위치 = None
            정체횟수 = 0
            continue
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


한칸표_보호영역 = set()

def 현재_한칸표인가():
    return hwp is not None and hwp.GetPos()[0] in 한칸표_보호영역

def 현재_표_키():
    """캐럿이 있는 칸을 담은 표 컨트롤의 고유 키(앵커 위치). 표가 아니면 None.

    예외가 나면 False(판정 불가)를 돌려 호출자가 예전 방식으로 대신하게 한다.
    """
    try:
        ctrl = hwp.ParentCtrl
        if ctrl is None or ctrl.CtrlID != 'tbl':
            return None
        anchor = ctrl.GetAnchorPos(0)
        return (anchor.Item('List'), anchor.Item('Para'), anchor.Item('Pos'))
    except Exception:
        return False


def 표칸_묶음_수집():
    """표마다 [(area, 셀주소, 행번호), ...] 목록(문서 순서). 판정 불가면 None."""
    묶음 = 표칸_묶음_키별()
    return None if 묶음 is None else list(묶음.values())


def 표칸_묶음_키별():
    """{표 키(앵커 리스트, 문단, 위치): [(area, 셀주소, 행번호), ...]}. 판정 불가면 None.

    예전에는 'A1 칸이 나오면 새 표'로 묶었는데, 실측(2026-09-25, 표 서식 문서)에서
    가운데 열이 세로 병합된 표가 세 조각으로 나뉘어 셀 너비 맞춤이 엉뚱한 열에
    너비를 넣었다. 칸을 담은 표 컨트롤(ParentCtrl)의 앵커 위치로 묶는다.
    """
    묶음 = {}
    area = 1
    while True:
        if 중단_요청됨():
            break
        area += 1
        try:
            hwp.SetPos(area, 0, 0)
        except Exception:
            break
        if hwp.GetPos()[0] != area:
            break
        키 = 현재_표_키()
        if 키 is False:
            return None
        if 키 is None:
            continue
        주소, 행번호 = 현재_셀_주소_행번호()
        if 주소 is None:
            continue
        묶음.setdefault(키, []).append((area, 주소, 행번호))
    return 묶음


def 한칸표_영역_목록():
    """문서의 컨트롤 리스트를 훑어 한 셀로만 된 표의 영역 번호를 찾는다.

    칸을 담은 표 컨트롤 기준으로 묶어(표칸_묶음_수집) 칸이 A1 하나뿐인 표를
    한 칸 표로 판정한다. 표 컨트롤을 읽지 못하는 환경이면 예전 규칙(다음 A1
    또는 비표 영역이 나오기 전까지를 한 표로 봄)으로 대신한다.
    """
    묶음 = 표칸_묶음_수집()
    if 묶음 is not None:
        return {칸들[0][0] for 칸들 in 묶음 if len(칸들) == 1 and 칸들[0][1] == "A1"}
    한칸영역 = set()
    현재표 = []

    def 표_확정():
        nonlocal 현재표
        if len(현재표) == 1 and 현재표[0][1] == "A1":
            한칸영역.add(현재표[0][0])
        현재표 = []

    area = 1
    while True:
        area += 1
        try:
            hwp.SetPos(area, 0, 0)
        except Exception:
            break
        if hwp.GetPos()[0] != area:
            break
        주소, _ = 현재_셀_주소_행번호()
        if 주소 is None:
            표_확정()
            continue
        if 주소 == "A1" and 현재표:
            표_확정()
        현재표.append((area, 주소))
    표_확정()
    return 한칸영역

def 표_헤더서식_현재셀_처리():
    """현재 셀의 전체 텍스트에 헤더/본문 폰트·크기·굵기를 적용한다."""
    if 현재_한칸표인가():
        return False
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
                # 본문 셀의 기존 굵은 강조는 해제하지 않는다.
                굵게=True if 표_헤더서식_본문_굵게 else None,
            )
        hwp_run("Cancel")
        hwp_run("MoveListBegin")
        return True
    except Exception as e:
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        로그(f"표 셀 문자서식적용 실패(무시): {e}")
        return False


def 표_헤더서식_현재줄_처리():
    return 표_헤더서식_현재셀_처리()


# 표 서식을 표 단위로 한 번에 적용할지(칸마다 적용하는 예전 방식과 결과가 같다).
표_서식_표단위_사용 = True


def 표_헤더서식_표단위_처리(칸들):
    """표 하나(표칸_묶음_수집의 칸 목록)에 본문·머리글 서식을 한 번에 적용한다.

    실측(2026-09-26): 통계표가 많은 수출입동향(표 칸 5,052개)은 칸마다 글자를
    선택해 적용하느라 표 서식에만 14분이 걸렸다. 표 전체를 칸 블록으로 골라
    (F5 세 번 = TableCellBlock + TableCellBlockExtend×2) 본문 서식을 한 번에 주고,
    머리글 서식은 칸 주소가 1행인 칸에만 칸마다 다시 준다(칸마다 적용하던 예전 방식과
    결과가 같다). 첫 행 선택(TableCellBlockRow)은 A1이 두 행에 걸쳐 병합된 표에서
    둘째 행까지 골라 결과가 달라졌으므로 쓰지 않는다(실측, 표 서식 문서 2개 표).
    성공하면 칸 수, A1 칸이 없거나 실패하면 None(호출자가 칸마다 적용으로 대신한다).
    """
    첫칸 = next((area for area, 주소, _ in 칸들 if 주소 == "A1"), None)
    if 첫칸 is None:
        return None
    try:
        hwp.SetPos(첫칸, 0, 0)
        hwp_run("Cancel")
        for 명령 in ("TableCellBlock", "TableCellBlockExtend", "TableCellBlockExtend"):
            hwp_run(명령)
        문자모양_적용_현재선택(
            폰트=표_헤더서식_본문_폰트,
            크기_pt=표_헤더서식_본문_크기,
            # 본문 칸의 기존 굵은 강조는 해제하지 않는다.
            굵게=True if 표_헤더서식_본문_굵게 else None,
        )
        hwp_run("Cancel")
        for area, _, 행 in 칸들:
            if 행 != 1:
                continue
            hwp.SetPos(area, 0, 0)
            hwp_run("MoveListBegin")
            hwp_run("MoveSelListEnd")
            문자모양_적용_현재선택(
                폰트=표_헤더서식_헤더_폰트,
                크기_pt=표_헤더서식_헤더_크기,
                굵게=표_헤더서식_헤더_굵게,
            )
            hwp_run("Cancel")
        return len(칸들)
    except Exception as e:
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        로그(f"표 단위 서식적용 실패(칸마다 적용으로 대신): {e}")
        return None

def 서식표_영역_목록(hwpx경로):
    """HWPX의 제목·중제목·붙임 서식 표마다 (칸 목록 번호 목록, 확인할 (목록 번호, 문단 순번, 글))을 돌려준다.

    한/글의 목록 번호는 문서 순서의 subList 순번 + 2다(_서식통일_표모형 참고). 준말 변환이 만든
    제목 표는 날짜·담당자 칸이 비어 있으므로 빈 정보 칸도 제목 표로 본다. 확인할 글은 표에서
    가장 긴 글 문단이다(중제목 번호처럼 짧은 글로 확인하면 다른 표와 헷갈릴 수 있다).
    """
    from docfit_core.style_inventory import _sections
    with zipfile.ZipFile(hwpx경로) as z:
        구역들 = [safe_xml_fromstring(z.read(name)) for name in _sections(z)]
    목록번호 = {}
    for root in 구역들:
        for item in root.iter():
            if 제목_xml이름(item) == 'subList':
                목록번호[id(item)] = len(목록번호) + 2
    결과 = []
    for root in 구역들:
        for table in [t for p in root for run in p for t in run if 제목_xml이름(t) == 'tbl']:
            if not (제목_유형판별(table, 빈칸허용=True) or 중제목_글칸들(table) or 붙임_유형판별(table)):
                continue
            영역들, 확인 = [], None
            for cell in 제목_셀들(table):
                sub = 제목_자식(cell, 'subList')
                if sub is None or id(sub) not in 목록번호:
                    continue
                영역들.append(목록번호[id(sub)])
                for 순번, p in enumerate(x for x in sub if 제목_xml이름(x) == 'p'):
                    글 = ''.join(_서식통일_run_text(run)[0] for run in p if 제목_xml이름(run) == 'run')
                    if len(글.strip()) > len(확인[2].strip() if 확인 else ''):
                        확인 = (목록번호[id(sub)], 순번, 글)
            if 영역들 and 확인:
                결과.append((영역들, 확인))
    return 결과


def 서식표_보호영역_조사(묶음=None):
    """표 머리글·본문 서식에서 뺄 제목·중제목·붙임 서식 표 칸의 목록 번호 집합.

    실측(2026-09-30): 2×2·2행1열 제목 표와 1행 붙임 표는 한 칸 표가 아니라서 1행이 머리글
    서식(한컴돋움 13pt)으로 덮여 제목 27pt·붙임 17pt가 사라졌다. 현재 문서를 HWPX로 스냅샷
    저장해 구조로 판별하고, 한/글에서 칸 글이 같은지 확인된 표만 돌려준다. 묶음(표칸_묶음_키별)이
    있고 서식 표 모양(칸 2~3개)의 표가 없으면 저장하지 않는다. 판별에 실패하면 빈 집합이다.
    스냅샷은 지금 편집 문서가 되어 한/글이 잡고 있으므로 다음 실행 때 정리한다.
    """
    모양 = ({'A1', 'A2', 'B2'}, {'A1', 'A2'}, {'A1', 'B1'}, {'A1', 'B1', 'C1'})
    if 묶음 is not None and not any({주소 for _, 주소, _ in 칸들} in 모양 for 칸들 in 묶음.values()):
        return set()
    folder = Path(tempfile.mkdtemp(prefix='hwp_table_guard_'))
    try:
        표들 = 서식표_영역_목록(_제목_임시hwpx_저장(folder / 'tables.hwpx'))
    except Exception as e:
        shutil.rmtree(folder, ignore_errors=True)
        로그(f"서식 표 판별 실패(표 서식을 모든 표에 적용): {e}")
        return set()
    보호 = set()
    for 영역들, (area, 순번, 글) in 표들:
        # 목록 번호가 어긋나면 다른 표를 빼게 되므로, 칸 문단 글자가 HWPX와 같은지 확인한다.
        try:
            hwp.SetPos(area, 순번, 0)
            같은칸 = (tuple(hwp.GetPos()[:2]) == (area, 순번)
                      and _서식통일_공백제거(현재문단_텍스트()) == _서식통일_공백제거(글))
        except Exception:
            같은칸 = False
        if 같은칸:
            보호.update(영역들)
        else:
            진단로그(f"[서식 표 제외] 칸 위치를 확인하지 못해 표 서식을 적용합니다: {글.strip()[:40]}")
    hwp_run("Cancel")
    return 보호


def 표_헤더서식_전체_적용():
    """표 안의 각 셀에 표준 문자서식을 적용한다.

    v1.11: 기존에는 HeadCtrl/Next로 표 컨트롤을 찾은 뒤
    ``hwp.SelectCtrl(ctrl.GetCtrlInstID(), 1)``로 첫 셀에 진입하려 했으나,
    이 메서드는 이 스크립트가 사용하는 win32com 원시 COM 객체에는 없어
    모든 표에서 예외가 발생하며 표 서식적용이 통째로 실패했다
    ("표 N 첫 셀 진입 실패(무시): HwpFrame.HwpObject.SelectCtrl").
    표/글상자 등 각 컨트롤 내부는 문서 안에서 고유한 리스트 번호를
    가지므로, ``컨트롤_내부_자간조정()``과 동일하게 리스트 번호를
    1씩 늘려가며 SetPos로 직접 진입하는, 이미 검증된 방식으로 대체한다.
    표가 아닌 영역(글상자 등)은 ``표_헤더서식_현재셀_처리()``가 셀
    주소를 못 찾으면 그대로 건너뛰므로 안전하다. 제목·중제목·붙임 서식 표는
    데이터 표가 아니므로 건너뛴다(서식표_보호영역_조사).
    """
    if 중단_요청됨():
        return False

    로그("표 헤더/본문 서식적용 시작")
    셀수 = 0
    실패수 = 0
    방문영역수 = 0
    한칸표영역 = 한칸표_영역_목록()
    제외수 = 0
    서식표_제외수 = 0

    # 표 단위 일괄 적용(쪽 범위를 지정하면 범위 밖 칸을 건드리지 않도록 칸마다 적용).
    묶음 = 표칸_묶음_키별() if 표_서식_표단위_사용 and not 쪽범위_사용중() else None
    서식표영역 = 서식표_보호영역_조사(묶음)
    if 묶음 is not None:
        처리된 = set()
        # 칸 안에 다른 표(한 칸 제목 상자 등)가 든 표는 표 단위 선택이 안쪽 표 글자까지
        # 바꿔 결과가 달라지므로(실측: 수출입동향) 칸마다 적용하는 예전 방식으로 둔다.
        안쪽표_리스트 = {키[0] for 키 in 묶음}
        for 칸들 in 묶음.values():
            if 중단_요청됨():
                return False
            if len(칸들) == 1 and 칸들[0][0] in 한칸표영역:
                continue
            if any(area in 서식표영역 for area, _, _ in 칸들):
                continue
            if any(area in 안쪽표_리스트 for area, _, _ in 칸들):
                continue
            적용 = 표_헤더서식_표단위_처리(칸들)
            if 적용 is not None:
                셀수 += 적용
                처리된.update(area for area, _, _ in 칸들)
    else:
        처리된 = set()

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

        if area in 한칸표영역:
            제외수 += 1
            진단로그(f"[한 칸 표 제외] 영역 {area}: 문자서식 보존")
            continue

        if area in 서식표영역:
            서식표_제외수 += 1
            진단로그(f"[서식 표 제외] 영역 {area}: 제목·중제목·붙임 서식 보존")
            continue

        if 쪽범위_사용중() and area not in 쪽범위_컨트롤영역:
            continue

        if area in 처리된:
            continue

        if 표_헤더서식_현재셀_처리():
            셀수 += 1
        else:
            실패수 += 1

    로그(f"표 헤더/본문 서식적용 완료 (검사한 컨트롤 영역 {방문영역수}개 / 적용된 표 셀 {셀수}개 / 한 칸 표 제외 {제외수}개 / 서식 표 칸 제외 {서식표_제외수}개 / 대상 아님·실패 {실패수}건)")
    return True


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


def 표_목록_수집():
    """문서를 훑어 표마다 [(area, 칼럼문자, 행번호), ...] 목록을 모아
    반환한다(한 칸 표는 제외). 셀 주소가 'A1'로 돌아오는 지점을 새 표의
    시작으로 본다 — 한칸표_영역_목록과 같은 규칙.
    """
    if hwp is None:
        return []
    묶음 = 표칸_묶음_수집()
    if 묶음 is not None:
        표들 = []
        for 칸들 in 묶음:
            if len(칸들) == 1 and 칸들[0][1] == "A1":
                continue      # 한 칸 표
            표 = []
            for area, 주소, 행번호 in 칸들:
                일치 = re.match(r"[A-Za-z]+", 주소)
                표.append((area, 일치.group(0) if 일치 else "A", 행번호))
            표들.append(표)
        return 표들
    한칸표영역 = 한칸표_영역_목록()
    표들 = []
    현재표 = []
    area = 1
    while True:
        if 중단_요청됨():
            break
        area += 1
        try:
            hwp.SetPos(area, 0, 0)
        except Exception:
            break
        if hwp.GetPos()[0] == 0:
            break
        if area in 한칸표영역:
            if 현재표:
                표들.append(현재표)
                현재표 = []
            continue
        주소, 행번호 = 현재_셀_주소_행번호()
        if 주소 is None:
            if 현재표:
                표들.append(현재표)
                현재표 = []
            continue
        if 주소 == "A1" and 현재표:
            표들.append(현재표)
            현재표 = []
        일치 = re.match(r"[A-Za-z]+", 주소)
        컬럼 = 일치.group(0) if 일치 else "A"
        현재표.append((area, 컬럼, 행번호))
    if 현재표:
        표들.append(현재표)
    return 표들


# ---- C1. 셀 안쪽 여백 강제 축소 ------------------------------------------

def 셀_화면줄수():
    """캐럿이 있는 셀(리스트) 안에 실제로 배치된 화면줄 수를 센다."""
    if hwp is None:
        return None
    원위치 = hwp.GetPos()
    try:
        hwp_run('MoveListBegin')
        hwp_run('MoveSelListEnd')
        리스트끝 = hwp.GetPos()
        hwp.SetPos(원위치[0], 0, 0)
        hwp_run('MoveListBegin')
        줄수 = 0
        이전줄끝 = None
        while True:
            if 중단_요청됨():
                return None
            hwp_run('MoveLineEnd')
            줄끝 = hwp.GetPos()
            if 줄끝 == 이전줄끝:
                break
            줄수 += 1
            if (줄끝[1], 줄끝[2]) >= (리스트끝[1], 리스트끝[2]):
                break
            이전줄끝 = 줄끝
            hwp_run('MoveNextChar')
            if hwp.GetPos() == 줄끝:
                break
        return 줄수
    except Exception as e:
        로그(f"셀 화면줄 수 확인 실패(무시): {e}")
        return None
    finally:
        try:
            hwp.SetPos(*원위치)
        except Exception:
            pass


def 셀_안쪽여백_읽기():
    """캐럿이 있는 셀의 (셀 여백 사용 여부, 왼쪽, 오른쪽) 원래 값. 실패 시 None."""
    if hwp is None:
        return None
    try:
        pset = hwp.HParameterSet.HShapeObject
        hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
        cell = pset.ShapeTableCell
        return int(cell.HasMargin), int(cell.MarginLeft), int(cell.MarginRight)
    except Exception as e:
        로그(f"셀 안쪽 여백 읽기 실패(무시): {e}")
        return None


def 셀_안쪽여백_현재선택(mm=None, 원래값=None):
    """캐럿이 있는 셀의 좌우 안쪽 여백을 mm로 설정한다(원래값을 주면 그 값으로 복원)."""
    if hwp is None:
        return False
    try:
        pset = hwp.HParameterSet.HShapeObject
        hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
        pset.HSet.SetItem("ShapeType", 3)
        pset.HSet.SetItem("ShapeCellSize", 0)
        if 원래값 is not None:
            pset.ShapeTableCell.HasMargin, pset.ShapeTableCell.MarginLeft, pset.ShapeTableCell.MarginRight = 원래값
        else:
            pset.ShapeTableCell.HasMargin = 1
            pset.ShapeTableCell.MarginLeft = hwp.MiliToHwpUnit(mm)
            pset.ShapeTableCell.MarginRight = hwp.MiliToHwpUnit(mm)
        return hwp.HAction.Execute("TablePropertyDialog", pset.HSet) is not False
    except Exception as e:
        로그(f"셀 안쪽 여백 적용 실패(무시): {e}")
        return False


def 셀_안쪽여백_축소_시도():
    """캐럿이 있는 셀의 텍스트가 2줄 이상이면 좌우 안쪽 여백을 조금씩
    줄여(표_셀여백_기본_mm → 표_셀여백_최소_mm) 1줄로 줄어드는지 시도한다.
    """
    if 셀_화면줄수() is None:
        return False
    줄수 = 셀_화면줄수()
    if 줄수 is None or 줄수 <= 1:
        return False
    # 실측(2026-09-25): 1줄로 만들지 못한 셀도 여백이 0으로 남아(표 서식 문서 46칸)
    # 표 모양만 바뀌었다. 실패하면 원래 여백으로 되돌린다.
    원래값 = 셀_안쪽여백_읽기()
    if 원래값 is None:
        return False
    try:
        if _셀_안쪽여백_단계축소():
            return True
    except Exception:
        pass
    셀_안쪽여백_현재선택(원래값=원래값)
    return False


def _셀_안쪽여백_단계축소():
    현재_mm = 표_셀여백_기본_mm
    최대반복 = max(1, int(round((표_셀여백_기본_mm - 표_셀여백_최소_mm) / 표_셀여백_스텝_mm)))
    for _ in range(최대반복):
        if 중단_요청됨():
            return False
        현재_mm = max(표_셀여백_최소_mm, round(현재_mm - 표_셀여백_스텝_mm, 2))
        if not 셀_안쪽여백_현재선택(현재_mm):
            return False
        새_줄수 = 셀_화면줄수()
        if 새_줄수 is None:
            return False
        if 새_줄수 <= 1:
            return True
        if 현재_mm <= 표_셀여백_최소_mm:
            break
    return False


def 표_셀_안쪽여백_전체_적용():
    if not 표_셀여백_축소_사용:
        return True
    if 중단_요청됨():
        return False
    로그("셀 안쪽 여백 강제 축소 시작")
    원위치 = hwp.GetPos()
    한칸표영역 = 한칸표_영역_목록()
    검사수 = 0
    적용수 = 0
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
        if area in 한칸표영역:
            continue
        주소, _ = 현재_셀_주소_행번호()
        if 주소 is None:
            continue
        검사수 += 1
        if 셀_안쪽여백_축소_시도():
            적용수 += 1
    try:
        hwp.SetPos(*원위치)
    except Exception:
        pass
    로그(f"셀 안쪽 여백 강제 축소 완료 (검사 {검사수}개 / 축소 적용 {적용수}개)")
    return True


# ---- C2. 셀 너비를 본문 여백에 맞춤 ---------------------------------------

def 본문_가용너비_mm():
    """현재 섹션 용지 폭에서 좌우 여백을 뺀 본문 가용 너비(mm)."""
    if hwp is None:
        return None
    try:
        act = hwp.HAction
        pset = hwp.HParameterSet.HSecDef
        act.GetDefault("PageSetup", pset.HSet)
        return HwpUnit_mm(
            pset.PageDef.PaperWidth - pset.PageDef.LeftMargin - pset.PageDef.RightMargin
        )
    except Exception as e:
        로그(f"본문 가용 너비 확인 실패(무시): {e}")
        return None


def 표_전체너비_mm():
    """캐럿이 표 안 어딘가에 있을 때, 그 표 전체의 현재 너비(mm)."""
    if hwp is None:
        return None
    try:
        return HwpUnit_mm(hwp.CellShape.Item("Width"))
    except Exception as e:
        로그(f"표 전체 너비 확인 실패(무시): {e}")
        return None


def 현재셀_너비_mm():
    """캐럿이 있는 셀(표 안)의 현재 너비(mm)."""
    if hwp is None:
        return None
    try:
        pset = hwp.HParameterSet.HShapeObject
        hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
        return HwpUnit_mm(pset.ShapeTableCell.Width)
    except Exception as e:
        로그(f"셀 너비 확인 실패(무시): {e}")
        return None


def 표_열너비_순서대로_설정(목표_mm_목록):
    """캐럿이 표의 첫 행 첫 칸에 있다고 가정하고, 왼쪽 열부터 순서대로
    목표_mm_목록의 값으로 각 열 너비를 설정한다. 실제로 적용된 열 수를
    반환한다.

    열을 고르는 방식(TableColPageUp → TableCellBlock →
    TableCellBlockExtend → TableColPageDown으로 한 열 전체 선택 후
    ShapeCellSize=1로 너비 지정)은 사람이 Alt+방향키 대신 '표/셀 속성'
    대화상자를 여는 것과 같은 효과의 실제 한/글 액션 조합이다.
    """
    if hwp is None:
        return 0
    hwp_run('TableColBegin')
    적용수 = 0
    for 목표_mm in 목표_mm_목록:
        if 중단_요청됨():
            break
        try:
            hwp_run('TableColPageUp')
            hwp_run('TableCellBlock')
            hwp_run('TableCellBlockExtend')
            hwp_run('TableColPageDown')
            pset = hwp.HParameterSet.HShapeObject
            hwp.HAction.GetDefault("TablePropertyDialog", pset.HSet)
            pset.HSet.SetItem("ShapeType", 3)
            pset.HSet.SetItem("ShapeCellSize", 1)
            pset.ShapeTableCell.Width = hwp.MiliToHwpUnit(목표_mm)
            if hwp.HAction.Execute("TablePropertyDialog", pset.HSet) is not False:
                적용수 += 1
            hwp_run('Cancel')
            hwp_run('TableRightCell')
        except Exception as e:
            로그(f"열 너비 설정 실패(무시): {e}")
            try:
                hwp_run('Cancel')
            except Exception:
                pass
            break
    return 적용수


def 표_열너비_본문맞춤_시도(표_셀목록, 목표_전체너비_mm):
    """표 첫 행(칼럼별 대표 셀)의 현재 너비 비율을 유지한 채, 표 전체
    너비를 목표_전체너비_mm에 맞춰 각 열 너비를 비례 조정한다.

    첫 행이 병합돼 칼럼별 셀을 구분할 수 없거나(첫 행 셀이 1개뿐),
    이미 허용오차 안이면 건드리지 않는다.
    """
    if not 표_셀목록 or 목표_전체너비_mm is None or 목표_전체너비_mm <= 0:
        return False
    첫행_area = [area for area, _, 행 in 표_셀목록 if 행 == 1]
    if len(첫행_area) < 2:
        return False
    # 실측(2026-09-25): 첫 행이 병합된 표(연도 아래 분기 칸 등)는 첫 행 칸과 실제
    # 열이 맞지 않아 너비가 엉뚱한 열에 들어가 표가 용지 밖으로 넘쳤다(4쪽→7쪽).
    # 모든 행의 열 구성이 첫 행과 같은 격자형 표만 조정한다.
    행별_열 = {}
    for _, 컬럼, 행 in 표_셀목록:
        행별_열.setdefault(행, []).append(컬럼)
    첫행_열 = 행별_열.get(1, [])
    if any(열 != 첫행_열 for 열 in 행별_열.values()):
        진단로그("[셀 너비 본문 맞춤] 병합된 칸이 있는 표는 건너뜀")
        return False
    try:
        hwp.SetPos(첫행_area[0], 0, 0)
    except Exception:
        return False
    현재_전체너비 = 표_전체너비_mm()
    if 현재_전체너비 is None or 현재_전체너비 <= 0:
        return False
    if abs(현재_전체너비 - 목표_전체너비_mm) <= 표_열너비_허용오차_mm:
        return False
    현재_너비들 = []
    for area in 첫행_area:
        try:
            hwp.SetPos(area, 0, 0)
        except Exception:
            return False
        w = 현재셀_너비_mm()
        if w is None or w <= 0:
            return False
        현재_너비들.append(w)
    비율합 = sum(현재_너비들)
    if 비율합 <= 0:
        return False
    목표_너비들 = [w / 비율합 * 목표_전체너비_mm for w in 현재_너비들]
    try:
        hwp.SetPos(첫행_area[0], 0, 0)
    except Exception:
        return False
    적용수 = 표_열너비_순서대로_설정(목표_너비들)
    return 적용수 == len(목표_너비들)


def 표_열너비_본문맞춤_전체_적용():
    if not 표_열너비_맞춤_사용:
        return True
    if 중단_요청됨():
        return False
    목표_mm = 본문_가용너비_mm()
    if 목표_mm is None or 목표_mm <= 0:
        로그("셀 너비 본문 맞춤 건너뜀: 본문 가용 너비 확인 실패")
        return True
    로그(f"셀 너비를 본문 여백({목표_mm:.1f}mm)에 맞추는 작업 시작")
    원위치 = hwp.GetPos()
    표들 = 표_목록_수집()
    적용표수 = 0
    for 표 in 표들:
        if 중단_요청됨():
            return False
        if 표_열너비_본문맞춤_시도(표, 목표_mm):
            적용표수 += 1
    try:
        hwp.SetPos(*원위치)
    except Exception:
        pass
    로그(f"셀 너비 본문 맞춤 완료 (표 {len(표들)}개 중 {적용표수}개 조정)")
    return True


# ---- C3. 표 테두리 선 굵기 통일 (삼선표: 외곽 0.5mm / 헤더 이중선 /
#          내부 0.12mm / 좌우 외곽선 없음) ---------------------------------

def 표_셀_테두리_적용(위=None, 아래=None, 왼쪽=None, 오른쪽=None):
    """캐럿이 있는 셀에 지정된 방향의 테두리 선 종류/굵기를 적용한다.
    각 인자는 (HwpLineType 이름, HwpLineWidth 이름) 튜플이거나
    None(해당 방향은 건드리지 않음).
    """
    # 실측(2026-09-25): pset.SelCellsBorderFill 아래 항목에 값을 넣는 예전 방식은
    # 실행 결과가 True여도 테두리가 바뀌지 않았다. 셀을 블록으로 선택한 뒤
    # HCellBorderFill의 BorderType*/BorderWidth* 항목을 직접 넣어야 적용된다.
    # 'CellBorderFill' 액션은 셀 배경색까지 다시 적용해 머리글 배경이 지워졌으므로
    # 테두리만 바꾸는 'CellBorder' 액션을 쓴다.
    if hwp is None:
        return False
    try:
        hwp_run("TableCellBlock")
        pset = hwp.HParameterSet.HCellBorderFill
        hwp.HAction.GetDefault("CellBorder", pset.HSet)
        for 방향, 값 in (("Top", 위), ("Bottom", 아래), ("Left", 왼쪽), ("Right", 오른쪽)):
            if 값 is None:
                continue
            종류, 굵기 = 값
            setattr(pset, "BorderType" + 방향, hwp.HwpLineType(종류))
            setattr(pset, "BorderWidth" + 방향, hwp.HwpLineWidth(굵기))
        return hwp.HAction.Execute("CellBorder", pset.HSet) is not False
    except Exception as e:
        로그(f"표 셀 테두리 적용 실패(무시): {e}")
        return False
    finally:
        try:
            hwp_run("Cancel")
        except Exception:
            pass


def 표_테두리_삼선표_적용(표_셀목록):
    """표 하나(표_목록_수집이 모은 (area, 칼럼, 행번호) 목록)에 삼선표
    규칙을 적용한다: 위/아래 외곽선 0.5mm 실선, 헤더 아래 이중선 0.5mm,
    나머지 안쪽 구분선(가로/세로) 0.12mm 실선, 좌우 외곽선은 선 없음.
    """
    if not 표_셀목록:
        return 0
    마지막행 = max(행 for _, _, 행 in 표_셀목록)
    행별_첫area = {}
    행별_끝area = {}
    for area, _, 행 in 표_셀목록:
        if 행 not in 행별_첫area:
            행별_첫area[행] = area
        행별_끝area[행] = area
    적용수 = 0
    for area, _, 행 in 표_셀목록:
        if 중단_요청됨():
            break
        if 행 == 마지막행:
            아래 = ("Solid", "0.5mm")
        elif 행 == 1:
            아래 = ("DoubleSlim", "0.5mm")
        else:
            아래 = ("Solid", "0.12mm")
        if 행 == 1:
            위 = ("Solid", "0.5mm")
        elif 행 == 2:
            위 = ("DoubleSlim", "0.5mm")
        else:
            위 = ("Solid", "0.12mm")
        왼쪽 = ("None", "0.1mm") if area == 행별_첫area[행] else ("Solid", "0.12mm")
        오른쪽 = ("None", "0.1mm") if area == 행별_끝area[행] else ("Solid", "0.12mm")
        try:
            hwp.SetPos(area, 0, 0)
        except Exception:
            continue
        if 표_셀_테두리_적용(위=위, 아래=아래, 왼쪽=왼쪽, 오른쪽=오른쪽):
            적용수 += 1
    return 적용수


def 표_테두리_전체_적용():
    if not 표_테두리_통일_사용:
        return True
    if 중단_요청됨():
        return False
    로그("표 테두리 선 굵기 통일 시작")
    원위치 = hwp.GetPos()
    표들 = 표_목록_수집()
    총적용 = 0
    for 표 in 표들:
        if 중단_요청됨():
            return False
        총적용 += 표_테두리_삼선표_적용(표)
    try:
        hwp.SetPos(*원위치)
    except Exception:
        pass
    로그(f"표 테두리 선 굵기 통일 완료 (표 {len(표들)}개 / 적용 셀 {총적용}개)")
    return True


# 한 줄이 이 글자 수 이상인 표 칸은 본문과 같은 자간 한도를 쓴다(사용자 결정
# 2026-09-25). 좁은 칸은 자간을 많이 바꾸면 글자가 뭉개져 표 한도로 묶어 둔다.
넓은_표칸_기준글자수 = 20


def 넓은_표칸_줄인가():
    """현재 화면줄이 넓은 표 칸의 줄인지(글자 위치 기준 길이).

    실측: 한 줄 33자인 공고문 표 칸의 '신|뢰를' 등 3건이 표 한도(5단계)
    때문에 풀리지 않았다.
    """
    original = hwp.GetPos()
    try:
        start, end = 단어모드_줄범위(original)
        return end[2] - start[2] >= 넓은_표칸_기준글자수
    except Exception:
        return False
    finally:
        hwp.SetPos(*original)


def 컨트롤_내부_자간조정():
    """표/글상자 등 모든 컨트롤 영역의 단어 분리를 보정한다.

    한 칸 표(제목·요지·개요 박스)는 표 셀이 아니라 본문과 다름없는 긴 문장이므로
    단어 분리 재시도 예산도 표용(자간_최대시도_표, 짧음)이 아니라 본문용
    (자간_최대시도_본문)을 써야 한다. 이 함수는 이미 한칸표영역을 계산해 공백
    정리 호출 여부를 가르는 데는 쓰고 있었지만, 정작 재시도 예산 선택에는
    반영하지 않아 한 칸 표 안의 단어 분리가 5단계 만에 포기되고 있었다.
    """
    한칸표영역 = 한칸표_영역_목록()
    area = 1
    while True:
        if 중단_요청됨():
            return False
        area += 1
        hwp.SetPos(area, 0, 0)
        if hwp.GetPos()[0] != area:
            break
        if 쪽범위_사용중() and area not in 쪽범위_컨트롤영역:
            continue
        if not 재검사_영역인가(area):
            continue
        if 표셀_자간_제외인가():
            진단로그(f"[표 안 문장 제외] 영역 {area}: 자간 조정 안 함")
            continue
        if 숫자_표칸인가():
            continue
        while True:
            if 중단_요청됨():
                return False
            시작위치 = hwp.GetPos()
            현재영역_한칸표 = hwp.GetPos()[0] in 한칸표영역
            # 표/글상자/각주/미주 내부 텍스트도 본문과 동일한 공백 규칙을 적용한다.
            if 작업_모드 != "spacing" and not 현재영역_한칸표:
                괄호_안쪽_공백_정리_문단_처리()
                쉼표_공백_정리_문단_처리()
                콜론_공백_정리_문단_처리()
            최대시도 = (자간_최대시도_본문 if 현재영역_한칸표 or 넓은_표칸_줄인가()
                    else 자간_최대시도_표)
            result = 자간자동조정(최대시도=최대시도)
            if result is False:
                return False
            hwp_run("MoveLineEnd")
            줄끝 = hwp.GetPos()
            hwp_run("MoveNextChar")
            if hwp.GetPos()[0] != area:
                break
            # 셀의 마지막 줄에서는 MoveNextChar가 줄 끝에 머문다. 시작 위치와만
            # 비교하면 같은 줄을 한 번 더 처리했다(실측: 표 셀마다 다음 단어
            # 당김을 두 번 시도해 한 번에 약 5초씩 낭비).
            if hwp.GetPos() in (시작위치, 줄끝):
                break
    return True

def 한칸표_자간조정():
    """서식 정리에서도 개요 등 한 칸 표의 단어 분리를 보정한다.

    한칸표_보호영역(=한칸표_영역_목록)에 들어가는 표는 정의상 셀이 A1 하나뿐인
    표뿐이다. 실제 데이터 표의 짧은 셀이 아니라 제목·요지·개요 박스처럼 표
    형태를 빌린 본문형 긴 문장이므로, 표 셀용으로 정해둔 짧은 재시도 예산
    (자간_최대시도_표)이 아니라 본문과 동일한 예산(자간_최대시도_본문)을 써야
    한다. 표 전용 예산을 쓰면 본문에서는 무리 없이 풀리는 정도의 단어 분리도
    이 박스 안에서는 예산 부족만으로 실패로 남는다.
    """
    original = hwp.GetPos()
    try:
        for area in sorted(한칸표_보호영역):
            hwp.SetPos(area, 0, 0)
            if hwp.GetPos()[0] != area:
                continue
            if 쪽범위_사용중() and area not in 쪽범위_컨트롤영역:
                continue
            if 표셀_자간_제외인가():
                진단로그(f"[표 안 문장 제외] 영역 {area}: 자간 조정 안 함")
                continue
            while True:
                if 중단_요청됨():
                    return False
                start = hwp.GetPos()
                if 자간자동조정(최대시도=자간_최대시도_본문) is False:
                    return False
                hwp_run('MoveLineEnd')
                end = hwp.GetPos()
                hwp_run('MoveNextChar')
                nxt = hwp.GetPos()
                if nxt[0] != area or nxt in (start, end):
                    break
        return True
    finally:
        hwp_run('Cancel')
        hwp.SetPos(*original)


def 컨트롤_내부_문장부호_처리():
    한칸표영역 = 한칸표_영역_목록()
    area = 1
    while True:
        if 중단_요청됨():
            return False
        area += 1
        hwp.SetPos(area, 0, 0)
        if hwp.GetPos()[0] == 0:
            break
        if not 재검사_영역인가(area):
            continue
        if area in 한칸표영역:
            진단로그(f"[한 칸 표 제외] 영역 {area}: 문장부호 서식 보존")
            continue
        if 숫자_표칸인가():
            continue
        while True:
            if 중단_요청됨():
                return False
            시작위치 = hwp.GetPos()
            # 이 순회는 다음 영역까지 이어질 수 있어 줄마다 쪽 범위·표 제외 설정을 확인한다.
            if 컨트롤_줄병합_대상인가():
                문장부호_줄병합_시도()
            hwp_run("MoveLineEnd")
            줄끝 = hwp.GetPos()
            hwp_run("MoveNextChar")
            if hwp.GetPos()[0] != 0 and hwp.GetPos()[0] >= area:
                area = hwp.GetPos()[0]
            # 마지막 줄에서 MoveNextChar가 줄 끝에 머물면 같은 줄을 다시 처리하지 않는다.
            if hwp.GetPos() in (시작위치, 줄끝):
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

# ------------------------------------------------------------
# 쪽 범위 / 표 안 문장 제외 도우미
# ------------------------------------------------------------

def 쪽표시(n):
    """쪽 번호 표시. 0(또는 None)은 '마지막쪽'."""
    return "마지막쪽" if not n else f"{n}쪽"

# 절약 시간 추정(수작업 기준). 작업 종류별로 한 쪽을 손으로 정리할 때 걸리는 분(分)이다.
# 처리한 쪽 수 × 이 값 − 실제 걸린 시간 = 화면에 보여 주는 '절약된 시간'이다. 추정치를 바꾸려면 이 값을 고친다.
절약시간_쪽당_분 = {"spacing": 4.0, "unify": 2.0, "format": 5.0, "all": 8.0}

def 절약시간_표시(분):
    """분(分)을 '약 45분', '약 1시간 20분' 꼴로 보여 준다."""
    분 = max(1, int(round(분)))
    if 분 < 60:
        return f"약 {분}분"
    시간, 나머지 = divmod(분, 60)
    return f"약 {시간}시간" + (f" {나머지}분" if 나머지 else "")

def 처리_쪽수_구하기():
    """이번에 처리한 문서의 쪽 수(쪽 범위를 지정했으면 그 범위의 쪽 수). 알 수 없으면 1."""
    try:
        if 쪽범위_실제 is not None:
            return max(1, 쪽범위_실제[1] - 쪽범위_실제[0] + 1)
        hwp_run("Cancel")
        hwp_run("MoveDocEnd")
        쪽 = 현재_페이지번호()
        hwp_run("MoveDocBegin")
        if 쪽:
            return max(1, int(쪽))
    except Exception:
        pass
    return 1

def 쪽범위_사용중():
    return 쪽범위_본문_문단 is not None

def 쪽범위_안인가(pos=None):
    """위치가 작업 쪽 범위 안인지. 쪽 범위를 지정하지 않았으면 항상 True."""
    if 쪽범위_본문_문단 is None:
        return True
    if pos is None:
        pos = hwp.GetPos()
    if pos[0] == 0:
        return 쪽범위_본문_문단[0] <= pos[1] <= 쪽범위_본문_문단[1]
    return pos[0] in 쪽범위_컨트롤영역

def 쪽범위_끝지남(pos=None):
    """본문 순회 중 작업 쪽 범위의 마지막 문단을 지났는지."""
    if 쪽범위_본문_문단 is None:
        return False
    if pos is None:
        pos = hwp.GetPos()
    return pos[0] == 0 and pos[1] > 쪽범위_본문_문단[1]

def 순회_시작():
    """문서 순회를 시작 위치로 옮긴다. 쪽 범위가 있으면 범위의 첫 문단으로 간다."""
    hwp_run("MoveDocBegin")
    if 쪽범위_본문_문단 is not None:
        hwp.SetPos(0, 쪽범위_본문_문단[0], 0)
        현재 = hwp.GetPos()
        if 현재[0] != 0 or 현재[1] != 쪽범위_본문_문단[0]:
            raise RuntimeError("작업 쪽 범위의 첫 문단으로 이동하지 못했습니다.")

def 범위_다음_문단으로_진행():
    """다음_문단으로_진행()과 같지만 쪽 범위 밖 문단은 건너뛰고, 범위를 지나면 False를 돌려준다."""
    if 쪽범위_본문_문단 is None:
        return 다음_문단으로_진행()
    while True:
        if 중단_요청됨():
            return False
        if not 다음_문단으로_진행():
            return False
        pos = hwp.GetPos()
        if 쪽범위_끝지남(pos):
            return False
        if 쪽범위_안인가(pos):
            return True

def 현재_표셀인가():
    """현재 커서가 표 셀 안인지(셀 주소가 있는 영역인지) 판정한다. 본문·글상자는 False."""
    try:
        if hwp is None or hwp.GetPos()[0] == 0:
            return False
        주소, _ = 현재_셀_주소_행번호()
        return 주소 is not None
    except Exception:
        return False

# 숫자·기호만으로 된 표 칸(통계표의 수치 칸 등)은 어절이 없어 자간·단어 분리
# 조정할 것이 없다. 실측: 수출입동향(통계표 위주) 문서에서 자간 초기화만
# 32분이 걸렸다(사용자 요청 2026-09-25: 숫자만으로 된 표는 건너뜀).
_숫자칸_패턴 = re.compile(r"[\s0-9０-９,，.．%％+\-－−–△▲▼▽↑↓()（）~∼'‘’/:×·]*")


def 숫자_표칸인가(area=None):
    """커서가 있는(또는 area) 표 칸의 글자가 숫자·기호뿐이면 True(빈 칸 포함)."""
    original = hwp.GetPos()
    try:
        if area is not None:
            hwp.SetPos(area, 0, 0)
            if hwp.GetPos()[0] != area:
                return False
        if hwp.GetPos()[0] == 0 or not 현재_표셀인가():
            return False
        hwp_run('MoveListBegin')
        hwp_run('MoveSelListEnd')
        text = 현재선택영역_텍스트() or ''
        hwp_run('Cancel')
        return bool(_숫자칸_패턴.fullmatch(text.replace(chr(13), '').replace(chr(10), '')))
    except Exception:
        return False
    finally:
        try:
            hwp.SetPos(*original)
        except Exception:
            pass


def 표셀_자간_제외인가():
    """'표 서식 내 문장도 자간조정하기'가 꺼져 있고 커서가 표 셀 안이면 True."""
    return (not 표_자간조정_사용) and 현재_표셀인가()

def 컨트롤_줄병합_대상인가():
    """표·글상자 안 줄 병합 대상 여부(쪽 범위·표 제외 설정 반영)."""
    if not 쪽범위_안인가():
        return False
    return not 표셀_자간_제외인가()

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

def 저장파일명(파일):
    path = Path(파일)
    suffix = {"spacing": "(자간조정)", "unify": "(서식통일)", "format": "(서식적용)", "all": "(일괄적용)"}[작업_모드]
    if 쪽범위_실제 is not None:
        # 일부 쪽만 처리한 결과가 전체 처리 결과를 덮어쓰지 않도록 범위를 이름에 남긴다.
        suffix += f"({쪽범위_실제[0]}-{쪽범위_실제[1]}쪽)"
    # 입력이 바이너리 HWP여도 결과물은 항상 개방형 HWPX로 저장한다.
    return str(path.with_name(path.stem + suffix + ".hwpx"))

# ============================================================
# 문서 처리 파이프라인
# ============================================================

선택_세부작업 = {}
작업_반복횟수 = 1


# 보고서 표준서식(항목기호별 서식 등)을 준말 변환 바로 다음, 다른 모든 단계보다 먼저 입힐지.
# 작업_실행이 서식 적용·한 번에 적용에서 서식 옵션을 켰을 때 채운다(서식 통일은 표준서식을 쓰지 않는다).
표준서식_선행_사용 = False


def 표준서식_선행_적용(파일명):
    """보고서 표준서식을 입힌다. 입혔으면 True, 꺼져 있으면 None, 실패·중단이면 False.

    뒤에 최종 내어쓰기 단계가 있으면 문단별 내어쓰기를 그 단계로 미룬다(최종_내어쓰기_예정).
    """
    global 최종_내어쓰기_예정
    if not (표준서식_선행_사용 and stage_enabled(선택_세부작업, 'standard_format', 작업_모드)):
        return None
    단계표시("보고서 표준서식")
    상태(f"{파일명} : 보고서 표준서식")
    최종_내어쓰기_예정 = bool(
        작업_모드 in ('format', 'all') and 표준서식_내어쓰기_사용
        and stage_enabled(선택_세부작업, 'hanging_indent'))
    try:
        hwp_run('Cancel')
        순회_시작()
        if 표준서식_전체_적용() is False:
            return False
    finally:
        최종_내어쓰기_예정 = False
    return True


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


def _문서_처리_1회(파일명, 문장부호기능=True, 회차=1, 총회차=1):
    global _서식통일_문서대표프로필, 서식통일_줄병합_사용
    if 중단_요청됨():
        return False
    if 회차 == 1:
        _서식통일_문서대표프로필 = {}
        _서식통일_자간보류문단.clear()
        _서식통일_위치텍스트_보관.clear()
    def stage(name, action):
        단계표시(name)
        상태(f"{파일명} [{회차}/{총회차}] : {name}")
        hwp_run('Cancel')
        순회_시작()
        return action() is not False
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
        for key, name, action in (
            ('normalize_space', '공백 정규화', 문장내_공백_정규화_전체_적용),
            ('punctuation_space', '문장부호 뒤 공백 보정', 문장부호_뒤_공백_보정_전체_적용),
            ('style_unify', '서식통일', 서식통일_전체_적용),
            # 보고서 표준서식은 준말 변환 다음 다른 모든 단계보다 먼저 이미 입혔다(표준서식_선행_적용).
        ):
            if stage_enabled(선택_세부작업, key) and not stage(name, action):
                return False
        if stage_enabled(선택_세부작업, 'parenthesis') and (괄호_축소_사용 or 괄호_라벨_볼드_사용):
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


def 문서_전체_자간_초기화():
    """항목기호·라벨을 제외한 본문·컨트롤의 자간을 0%로 되돌린다.

    이 프로그램을 이미 한 번 이상 돌렸거나 사용자가 손으로 자간을 만져둔
    문서를 다시 처리하면, 잔여 자간값 위에 압축이 계속 누적되어 HWP의
    자간 조정 가능 범위(최솟값)에 금방 닿아버린다. 그러면 겉보기엔
    "본문 자간 자동조정"이 여러 번 시도해도 실제로는 더 줄어들 여지가
    없어 단어 분리가 그대로 남는다. 2회차 처리를 시작하기 전, 문서
    조정 가능한 본문만 한 번 0%로 되돌려 압축 여유를 확보한 채로
    자간조정을 시작하도록 한다. 회차마다 반복하면 1회차의 압축 결과가
    지워지므로 문서당 정확히 한 번만 호출해야 한다.
    """
    if hwp is None:
        return False
    try:
        hwp_run("Cancel")
        hwp_run("MoveDocBegin")
        def 영역_초기화(area):
            while True:
                if 중단_요청됨():
                    return False
                hwp_run('MoveParaBegin')
                start = hwp.GetPos()
                if start[0] != area or (area == 0 and 쪽범위_끝지남(start)):
                    break
                hwp_run('MoveParaEnd')
                end = hwp.GetPos()
                body, end = 자간조정_본문범위(start, end)
                if body[2] < end[2]:
                    단어모드_범위선택(body, end)
                    문자모양_적용_현재선택(자간=0)
                    hwp_run('Cancel')
                hwp.SetPos(*end)
                hwp_run('MoveNextParaBegin')
                nxt = hwp.GetPos()
                if nxt[0] != area or nxt[1] <= start[1]:
                    break
            return True

        순회_시작()
        if 영역_초기화(0) is False:
            return False

        area = 1
        while True:
            if 중단_요청됨():
                return False
            area += 1
            hwp.SetPos(area, 0, 0)
            if hwp.GetPos()[0] != area:
                break
            if 쪽범위_사용중() and area not in 쪽범위_컨트롤영역:
                continue
            if 표셀_자간_제외인가() or 숫자_표칸인가():
                continue
            if 영역_초기화(area) is False:
                return False

        hwp_run("MoveDocBegin")
        return True
    except Exception as e:
        로그(f"문서 전체 자간 초기화 실패(무시): {e}")
        try:
            hwp_run("Cancel")
        except Exception:
            pass
        return False


지원_확장자 = (".hwp", ".hwpx", ".txt", ".md", ".doc", ".docx", ".pdf")


def 바이너리_HWP_파일인가(path):
    """파일 앞부분이 OLE 복합 문서(HWP 5.0 바이너리) 서명인지 본다."""
    try:
        with open(path, "rb") as f:
            return f.read(8) == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    except OSError:
        return False


_텍스트_인코딩_후보 = ("utf-8-sig", "utf-8", "cp949")


def 텍스트파일_읽기(경로):
    for 인코딩 in _텍스트_인코딩_후보:
        try:
            return Path(경로).read_text(encoding=인코딩)
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError(f"텍스트 인코딩을 확인하지 못했습니다(UTF-8/CP949만 지원): {경로}")


def 텍스트_hwpx로_변환(텍스트, 대상경로):
    """현재 hwp에 새 빈 문서를 만들어 텍스트를 문단 단위로 넣고 HWPX로 저장한다."""
    if hwp.Run("FileNew") is False:
        raise RuntimeError("빈 문서를 만들지 못했습니다.")
    줄들 = 텍스트.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for 순번, 줄 in enumerate(줄들):
        if 줄:
            텍스트_삽입(줄)
        if 순번 < len(줄들) - 1:
            hwp_run("BreakPara")
    if hwp.SaveAs(str(대상경로), "HWPX", "") is False:
        raise RuntimeError("텍스트를 HWPX로 저장하지 못했습니다.")


def 라벨블록_한글삽입(한글, 블록들):
    """labeled_text 블록을 한/글 문서 끝에 차례로 넣는다(A4 제목 상자 표 템플릿).

    제목·개요(상자)·참고는 1×1 표로 넣는다. 1×1 제목 표는 제목 서식(제목_hwpx_처리)의
    대상이 아니므로(유형 삭제) 제목 서식이 자동으로 적용되지 않는다. 제목1·제목2·개요 라벨은
    표식을 붙여 넣고 저장 뒤 라벨_서식표_적용이 각각의 서식 표로 바꾼다.
    """
    def 글쓰기(내용):
        act = 한글.HAction
        pset = 한글.HParameterSet.HInsertText
        act.GetDefault("InsertText", pset.HSet)
        pset.Text = 내용
        act.Execute("InsertText", pset.HSet)

    def 표넣기(행들):
        열수 = max(len(행) for 행 in 행들)
        act = 한글.HAction
        pset = 한글.HParameterSet.HTableCreation
        act.GetDefault("TableCreate", pset.HSet)
        pset.Rows = len(행들)
        pset.Cols = 열수
        pset.WidthType = 0   # 단 너비에 맞춤(2는 임의 너비라 글자 폭만큼 좁아진다)
        pset.HeightType = 0  # 자동 높이
        pset.TableProperties.TreatAsChar = 1
        act.Execute("TableCreate", pset.HSet)
        칸들 = [칸 for 행 in 행들 for 칸 in (행 + [""] * (열수 - len(행)))]
        for 순번, 칸 in enumerate(칸들):
            if 칸:
                글쓰기(칸)
            if 순번 < len(칸들) - 1:
                한글.Run("TableRightCell")
        한글.Run("Cancel")
        한글.MovePos(3, 0, 0)  # 문서 끝(표 다음 문단)으로 나온다

    처음 = True
    for 블록 in 블록들:
        if not 처음:
            한글.Run("BreakPara")
        처음 = False
        종류 = 블록["kind"]
        if 종류 == "blank":
            continue
        if 종류 in _라벨_블록_종류:
            # 제목1·제목2·개요는 표식을 붙여 넣고, 저장 뒤 라벨_서식표_적용이 서식 표로 바꾼다.
            표넣기([[_라벨_표식[_라벨_블록_종류[종류]] + 블록["text"]]])
        elif 종류 in ("title", "ref"):
            표넣기([[블록["text"] if 종류 != "ref" else f"참고  {블록['text']}"]])
        elif 종류 == "table":
            표넣기(블록["rows"])
        else:
            글쓰기(f"{블록['marker']} {블록['text']}".strip())


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


def 텍스트_hwpx_단독변환(텍스트, 대상경로, 라벨_해석=True):
    """'텍스트 붙여넣기'에서 저장 즉시 HWPX로 바꿀 때 쓰는, 배치 작업(작업_실행)과
    완전히 독립된 한/글 세션.

    전역 hwp는 작업_실행 전용이라 배치가 실행 중일 때 그 세션을 건드리면
    RPC_E_WRONG_THREAD 류 오류가 난다. 이 함수는 자기 몫의 한/글 인스턴스를
    새로 띄우고 끝나면 바로 종료해, 배치가 동시에 있어도 서로 간섭하지
    않는다. COM은 생성한 스레드에서 정리해야 하므로 반드시 전용 스레드
    (daemon Thread)에서만 호출한다.
    """
    pythoncom.CoInitialize()
    단독_hwp = None
    서식표_후처리 = False
    try:
        단독_hwp = 한글_COM_인스턴스_생성(독립=True)
        try:
            단독_hwp.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE)
        except Exception:
            pass  # 새 문서를 만들어 텍스트만 적으므로 보안 모듈 등록 실패는 무시해도 된다.
        if 단독_hwp.Run("FileNew") is False:
            raise RuntimeError("빈 문서를 만들지 못했습니다.")
        if 라벨_해석 and looks_labeled(텍스트):
            # 라벨 형식(제목:/네모:/원: …)이면 제목·개요·참고를 1×1 상자 표로, 표: 줄을 표로 넣는다.
            블록들 = parse_labeled_text(텍스트)
            라벨블록_한글삽입(단독_hwp, 블록들)
            if 단독_hwp.SaveAs(str(대상경로), "HWPX", "") is False:
                raise RuntimeError("HWPX로 저장하지 못했습니다.")
            서식표_후처리 = any(b["kind"] in _라벨_블록_종류 for b in 블록들)
        else:
            줄들 = 텍스트.replace("\r\n", "\n").replace("\r", "\n").split("\n")
            for 순번, 줄 in enumerate(줄들):
                if 줄:
                    act = 단독_hwp.HAction
                    pset = 단독_hwp.HParameterSet.HInsertText
                    act.GetDefault("InsertText", pset.HSet)
                    pset.Text = 줄
                    act.Execute("InsertText", pset.HSet)
                if 순번 < len(줄들) - 1:
                    단독_hwp.Run("BreakPara")
            if 단독_hwp.SaveAs(str(대상경로), "HWPX", "") is False:
                raise RuntimeError("HWPX로 저장하지 못했습니다.")
    finally:
        if 단독_hwp is not None:
            try:
                # 중간에 실패해 저장 안 된 문서가 남아도 '저장할까요?' 창 없이 닫는다.
                단독_hwp.Clear(1)
            except Exception:
                pass
            try:
                단독_hwp.Quit()
            except Exception:
                pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass
    if 서식표_후처리:
        # 한/글이 저장 파일을 놓은 뒤에 표식 표를 제목1·개요 서식 표로 바꾼다.
        라벨_서식표_적용(대상경로)


def 외부문서_hwpx로_변환(원본경로, 확장자, 대상경로):
    """.txt/.md/.doc/.docx/.pdf를 자간·서식 처리에 쓸 작업용 HWPX로 변환한다.

    .md/.doc/.docx/.pdf는 선택형 kordoc 엔진(Node.js)이 있어야 문단·표·
    글머리 구조를 살려 변환한다. 없으면 .md는 서식 없이 텍스트로라도
    변환하고, .doc/.docx/.pdf는 이 엔진 없이는 읽을 방법이 없어 오류로
    알린다.

    PDF는 텍스트층이 없는 스캔 페이지만 내장 OCR로 인식해(--ocr) 이미지만
    있는 문서도 글자를 뽑아낸다. 추출된 이미지는 kordoc이 마크다운 옆
    images/ 폴더에 저장하는데, generate 단계에 --image-dir로 그 폴더를
    알려줘야 실제 이미지 데이터가 결과 HWPX에 그대로 임베드된다(지정하지
    않으면 자리표시만 남고 이미지가 사라진다).
    """
    if 확장자 == ".txt":
        텍스트_hwpx로_변환(텍스트파일_읽기(원본경로), 대상경로)
        return
    if 확장자 == ".md":
        try:
            generate_hwpx(str(원본경로), "보고서", str(대상경로), image_dir=Path(원본경로).parent)
            return
        except KordocUnavailableError as e:
            로그(f"고급 문서 엔진을 쓸 수 없어 서식 없이 텍스트로만 변환합니다: {e}")
            텍스트_hwpx로_변환(텍스트파일_읽기(원본경로), 대상경로)
            return
    if 확장자 in (".doc", ".docx", ".pdf"):
        with tempfile.TemporaryDirectory(prefix="docfit_변환_") as 임시폴더:
            임시_md = Path(임시폴더) / f"{Path(원본경로).stem}.md"
            parse_document(str(원본경로), str(임시_md), output_format="markdown", ocr=(확장자 == ".pdf"))
            generate_hwpx(str(임시_md), "보고서", str(대상경로), image_dir=임시폴더)
        if 확장자 == ".pdf":
            PDF_서식_이식(원본경로, 대상경로)
        return
    raise ValueError(f"지원하지 않는 변환 형식입니다: {확장자}")


# 알파(2026-10-10): kordoc은 PDF를 마크다운으로 바꿔 프리셋 서식으로 HWPX를 만들어 원본 서식이 사라진다.
# PDF 글자마다 글꼴·크기·굵게·글자색·장평·배경색을 읽어 변환 HWPX에 다시 적용한다(docfit_core.pdf_style_transfer).
# 실측(재경부 업무보고 PDF 17쪽): 짝지은 글자 기준 글꼴 0.3→99.9%, 크기 41→100%, 색 글자 0→100%, 배경색 1.1→100%.
알파_PDF서식이식_사용 = True


def PDF_서식_이식(원본경로, 대상경로):
    if not 알파_PDF서식이식_사용:
        return None
    try:
        from docfit_core.pdf_style_transfer import transfer_pdf_style
        통계 = transfer_pdf_style(원본경로, 대상경로)
        로그(f"[PDF 서식 이식] 글자 {통계['matched']}/{통계['pdf_chars']}개 짝지음, 글자 모양 {통계['new_char_shapes']}개·"
             f"셀 배경 {통계['cells_filled']}칸 적용")
        return 통계
    except Exception as e:
        로그(f"[PDF 서식 이식] 건너뜀(kordoc 변환 결과 그대로 사용): {e}")
        return None


def _박스그림표_한글표_삽입(행들):
    """현재 커서 위치(빈 문단)에 행렬(rows)로 실제 한/글 표를 만든다.

    라벨 입력 모드의 '표:' 삽입(라벨블록_한글삽입/표넣기)과 같은 HTableCreation
    설정을 쓴다 — 단 너비 맞춤(WidthType 0)·자동 높이(HeightType 0)·글자처럼
    취급(TreatAsChar 1). 표 뒤 후속 서식 단계(표 머리글/본문 서식 등)가 그대로
    적용될 수 있도록 첫 행을 머리글로 가정한 별도 서식은 여기서 넣지 않는다.
    """
    열수 = max(len(행) for 행 in 행들)
    act = hwp.HAction
    pset = hwp.HParameterSet.HTableCreation
    act.GetDefault("TableCreate", pset.HSet)
    pset.Rows = len(행들)
    pset.Cols = 열수
    pset.WidthType = 0   # 단 너비에 맞춤(2는 임의 너비라 글자 폭만큼 좁아진다)
    pset.HeightType = 0  # 자동 높이
    pset.TableProperties.TreatAsChar = 1
    act.Execute("TableCreate", pset.HSet)
    칸들 = [칸 for 행 in 행들 for 칸 in (행 + [""] * (열수 - len(행)))]
    for 순번, 칸 in enumerate(칸들):
        if 칸:
            텍스트_삽입(칸)
        if 순번 < len(칸들) - 1:
            hwp_run("TableRightCell")
    hwp_run("Cancel")


def _박스그림표_교체(시작문단, 끝문단, 행들):
    """문단 [시작문단, 끝문단](둘 다 본문, list id 0) 구간의 텍스트를 지우고
    그 자리에 실제 표를 삽입한다."""
    hwp.SetPos(0, 끝문단, 0)
    hwp_run('MoveParaEnd')
    끝위치 = hwp.GetPos()
    hwp.SetPos(0, 시작문단, 0)
    if hwp.SelectText(시작문단, 0, 끝위치[1], 끝위치[2]) is False:
        raise RuntimeError('박스 그림 표 범위 선택 실패')
    if hwp_run('Delete') is False:
        raise RuntimeError('박스 그림 표 텍스트 삭제 실패')
    hwp.SetPos(0, 시작문단, 0)
    _박스그림표_한글표_삽입(행들)


def 박스그림_전체_적용():
    """문서 본문에서 박스 그림(┌─┬─┐ 등)으로 그려진 표를 찾아 실제 한/글
    표로 바꾼다. AI 채팅 답변을 붙여넣을 때 흔히 딸려오는 형태다.

    본문(list id 0) 문단 텍스트를 먼저 전부 모아 docfit_core.text_table로
    블록을 찾은 뒤, 뒤에 있는 표부터 차례로 바꾼다(항목기호문장_사이_빈줄_삭제와
    같은 이유 — 뒤에서부터 바꿔야 앞쪽에서 찾아 둔 문단 번호가 바뀌지 않는다).
    """
    if 중단_요청됨():
        return False
    hwp_run('MoveDocBegin')
    문단텍스트들 = []
    while True:
        if 중단_요청됨():
            return False
        문단텍스트들.append(현재문단_텍스트())
        hwp_run('MoveNextParaBegin')
        새위치 = hwp.GetPos()
        if 새위치[0] != 0 or 새위치[1] != len(문단텍스트들):
            break

    매치들 = find_box_tables(문단텍스트들)
    if not 매치들:
        로그("텍스트 표(박스 그림) 변환: 대상 없음")
        hwp_run('MoveDocBegin')
        return True

    변환수 = 0
    for 시작, 끝, 행들 in reversed(매치들):
        if 중단_요청됨():
            return False
        try:
            _박스그림표_교체(시작, 끝, 행들)
            변환수 += 1
        except Exception as e:
            로그(f"텍스트 표(박스 그림) 변환 중 오류(건너뜀, {시작 + 1}~{끝 + 1}번째 문단): {e}")
            try:
                hwp_run('Cancel')
            except Exception:
                pass
    로그(f"텍스트 표(박스 그림) 변환 완료: {변환수}개")
    hwp_run('MoveDocBegin')
    return True


def 저장결과_규칙검수(파일, 저장파일, 결과창=True):
    """저장 결과를 한 번 열어 선택된 읽기 전용 검사를 각각 독립 실행한다.

    결과창이 거짓이면(여러 문서 일괄 처리) 서식통일 결과 창을 띄우지 않는다. 결과는 로그와
    최종검수 보고서에 남는다.
    """
    결과 = {}
    검사들 = {}
    서식검수 = stage_enabled(선택_세부작업, 'style_unify', 작업_모드)
    if 서식검수:
        if not _서식통일_문서대표프로필:
            결과['style_unify'] = {
                'status': 'not_applicable', 'checked': 0, 'issues': [],
                'reason': '항목기호 문장이 없어 대표 스타일이 없습니다(검사할 문장 없음).',
            }
        else:
            def 서식_검사():
                if not 서식통일_빨간표시_사용:
                    # 표준서식이 뒤이어 기준을 정했으면 최종 대표값을 조사한다.
                    _서식통일_문서대표프로필.clear()
                return 서식통일_전체_적용(
                    고정_프로필_재적용=서식통일_빨간표시_사용, 검증만=True)
            검사들['style_unify'] = 서식_검사
        # 표만 있는 문서도 검수한다. 본문 대표값 유무·검사 실패와 독립이다.
        if 작업_모드 == 'unify' and stage_enabled(선택_세부작업, 'table_unify', 작업_모드):
            검사들['table_unify'] = lambda: 서식통일_표_전체_적용(검증만=True)
    if 검수_사용:
        if 작업_모드 in ('format', 'all') and stage_enabled(선택_세부작업, 'page_group'):
            검사들['page_group'] = 문단글_캐시_구간(보고서_페이지배치_최종검사)
        if 작업_모드 in ('spacing', 'all'):
            if stage_enabled(선택_세부작업, 'word_check'):
                검사들['word_check'] = 문단글_캐시_구간(보고서_단어분리_최종검사)
            if stage_enabled(선택_세부작업, 'control_word_check'):
                검사들['control_word_check'] = 문단글_캐시_구간(lambda: 보고서_단어분리_최종검사(컨트롤=True))
    if 중단_요청됨():
        return False
    if 검사들:
        try:
            if 한글_문서_열기(hwp, 저장파일, 'HWPX', 'forceopen:true') is False:
                raise RuntimeError('저장 결과 재열기 실패')
        except Exception as exc:
            for key in 검사들:
                결과[key] = {'status': 'error', 'checked': 0, 'issues': [], 'error': str(exc)}
            검수_문제_기록(파일, f'[저장 결과 재열기 실패] {exc}')
        else:
            기록_경계 = len(검수_문제목록)
            for key, 검사 in 검사들.items():
                if 중단_요청됨():
                    return False
                try:
                    항목 = 검사()
                    if 항목 is False:
                        return False
                    결과[key] = 항목
                    로그(f"저장 결과 {key} 검수: {항목['status']} / 검사 {항목['checked']}건 / 오류 {len(항목['issues'])}건")
                    if key in ('style_unify', 'table_unify') and 항목['status'] not in ('passed', 'not_applicable'):
                        검수_문제_기록(파일, f"[저장 결과 {key} 검증 {항목['status']}] "
                                             f"불일치 {len(항목['issues'])}개, "
                                             f"판정 보류 그룹 {len(항목.get('not_checkable', []))}개")
                except Exception as exc:
                    결과[key] = {'status': 'error', 'checked': 0, 'issues': [], 'error': str(exc)}
                    검수_문제_기록(파일, f'[최종 {key} 검사 실패] {exc}')
                    로그(f'저장 결과 {key} 검수 실패: {exc}')
            완료된_검사 = {key for key, value in 결과.items()
                        if value.get('status') in ('passed', 'failed')}
            대체수 = 처리중_기록_대체(파일, 완료된_검사, 기록_경계)
            if 대체수:
                로그(f"처리 중 미해결 기록 {대체수}건을 저장 결과 검사로 대체")
    if 서식검수:
        로그("[서식통일] 5/5 저장된 결과 읽기 전용 검수 종료")
        if 결과창:
            _서식통일_최종결과_사용자확인(dict(결과['style_unify'], file=Path(파일).name))
    return 결과


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
    if (작업_모드 in ('spacing', 'all') and 쪽범위_요청 is None
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
    # 표 칸 안 날짜는 한 줄 표기가 원칙이다(사용자 규칙, 2026-10-10). 표 서식 단계들 뒤 맨 끝에서 지정한다.
    if (서식단계_사용 or 작업_모드 == 'unify') and 쪽범위_요청 is None:
        선행목록.append((True, '표 날짜 칸 한 줄', 표날짜칸_hwpx_처리, 'table_date.hwpx', '표 칸 너비'))
    if any(항목[0] for 항목 in 선행목록):
        상태(f"{파일명} : 글자·제목·표 선행 서식")
        알림 = {}
        if 제목붙임_선행적용(작업파일경로, 현재문서_기준=문서_변경됨,
                            처리목록=tuple(선행목록), 변경알림=알림) is False:
            return False
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

# ============================================================
# 백그라운드 작업 실행 스레드
# ============================================================

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
    실행모드="all",
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


def 색_rgb(color):
    """Tk 진행 표시용 #RGB/#RRGGBB 색상을 정수 RGB 튜플로 바꾼다."""
    value = str(color).strip().lstrip("#")
    if len(value) == 3:
        value = "".join(character * 2 for character in value)
    if len(value) != 6:
        raise ValueError(f"잘못된 색상 값: {color}")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


class LiveStageBoard(tk.Canvas):
    """실제 단계 이벤트를 표시. 점멸은 실행 표시이며 완료율 추정이 아니다."""
    def __init__(self, parent):
        super().__init__(parent, height=50, bg=UI_COLORS['bg'], highlightthickness=0)
        self.active = None
        self.visited = set()
        self.started = time.monotonic()
        self.last_signal = self.started
        self.detail = '작업 대기'
        self.outcome = None
        self.ended = None
        self.result_message = None   # 작업이 모두 끝났을 때 보여 줄 메시지(예: 절약된 시간)
        self.job = None
        self._draw_error_reported = False
        self.bind('<Destroy>', self._destroy, add='+')
        self._frame()

    def reset(self):
        self.active = None
        self.visited.clear()
        self.outcome = None
        self.ended = None
        self.result_message = None
        self.detail = '문서 처리 준비'
        self.signal()
        self.draw()

    def signal(self, detail=None):
        self.last_signal = time.monotonic()
        if detail is not None:
            self.detail = str(detail)

    def activate(self, stage):
        if stage not in 진행단계_순서:
            return
        if stage != self.active:
            if self.active:
                self.visited.add(self.active)
            self.active = stage
            self.started = time.monotonic()
        self.outcome = None
        self.ended = None
        self.signal()
        self.draw()

    def set_result_message(self, message):
        self.result_message = message
        self.draw()

    def finish(self, outcome):
        self.outcome = outcome
        self.ended = time.monotonic()
        self.signal()
        self.draw()

    def _destroy(self, event):
        if event.widget is self and self.job is not None:
            self.after_cancel(self.job)
            self.job = None

    def _frame(self):
        self.job = None
        try:
            mapped = self.winfo_ismapped()
            if mapped:
                self.draw()
                self._draw_error_reported = False
        except Exception as exc:
            # 진행 표시 오류가 Tk의 예약 콜백을 끊어 GUI 이벤트 큐까지
            # 멈추게 하지 않도록 진단만 남기고 다음 프레임을 계속 예약한다.
            if not self._draw_error_reported:
                진단로그(f"[진행 표시] 다시 그리기 실패(작업 계속): {exc}")
                self._draw_error_reported = True
            mapped = False
        try:
            self.job = self.after(66 if mapped else 250, self._frame)
        except tk.TclError:
            self.job = None

    def draw(self):
        self.delete('all')
        now = time.monotonic()
        width = max(1, self.winfo_width())
        for i, stage in enumerate(진행단계_순서):
            left, right = i*width/6+2, (i+1)*width/6-2
            current = self.active == stage
            busy = current and self.outcome is None
            # 처리한 단계는 진한 색 바탕 + 흰 글씨로 표시한다(아직 처리 전 단계만 연한 색).
            # 색은 모두 앱 테마 청록(UI_COLORS['teal'])에서 이어 받는다.
            #   처리한 칸 = 테마 청록 / 완료 = 진한 청록 / 진행 중 = 진한 청록↔더 진한 청록 깜빡임
            fill, prefix, text_color = '#f0ece8', '', UI_COLORS['ink']
            if stage in self.visited:
                fill, prefix, text_color = UI_COLORS['teal'], '· ', 'white'
            if current:
                text_color = 'white'
                if self.outcome:
                    fill = '#B85A22' if self.outcome != '완료' else UI_COLORS['teal_dark']
                    prefix = '✓ ' if self.outcome == '완료' else '■ '
                else:
                    mix = .5 + .5*math.sin(now*3)
                    low = 색_rgb(UI_COLORS['teal_dark'])
                    high = tuple(round(v*0.72) for v in low)
                    fill = '#'+''.join(f'{round(a+(b-a)*mix):02x}' for a,b in zip(low, high))
            self.create_rectangle(left,2,right,27,fill=fill,outline='')
            self.create_text((left+right)/2+6,14,text=prefix+stage,fill=text_color,font=('맑은 고딕',8,'bold' if current else 'normal'))
            if busy:
                angle = (now*230)%360
                self.create_arc(left+5,8,left+16,19,start=angle,extent=265,style='arc',outline='white',width=2)
        if self.active:
            elapsed = int((self.ended or now)-self.started)
            silent = int(now-self.last_signal)
            message = f'{self.active} · {self.outcome or "실행 중"} · {elapsed}초'
            if self.outcome is None and silent >= 15:
                message += f'   |   한글 응답 대기 {silent}초 · 중단은 현재 호출 반환 후 적용'
            elif self.outcome is None:
                message += f'   |   마지막 처리 신호 {silent}초 전'
        else:
            message = self.outcome or ''
        font = ('맑은 고딕',8)
        if self.outcome == '완료' and self.result_message:
            message, font = self.result_message, ('맑은 고딕',9,'bold')
        self.create_text(5,39,anchor='w',text=message,fill=UI_COLORS['teal_dark'],font=font)


# ============================================================
# GUI 클래스
# ============================================================
        self.scale('all', 0, 0, .6, .6)
        for item in self.find_all():
            if self.type(item) == 'text':
                self.itemconfigure(item, font=('맑은 고딕', 7), width=66)


class HwpAutoDocFitGUI:

    FOOTER_NOTE_DEFAULT = "정리된 HWPX는 원본 폴더에 저장되며, 같은 이름의 기존 결과를 바꿉니다."

    def __init__(self, root):
        global _서식통일_대표값_검토콜백
        self.root = root
        _서식통일_대표값_검토콜백 = self._서식통일_대표값_검토_요청
        self.files = []
        self.worker = None
        self.running = False
        self.stage_choices = {mode: {key: stage_default(key, mode) for key, _ in stages_for_mode(mode)}
                              for mode in ("spacing", "unify", "format", "all")}
        self._세부작업_기본저장 = {mode: False for mode in self.stage_choices}
        self.closing = False

        self.compare_toplevel = None
        self.compare_left_frame = None
        self.compare_right_frame = None

        root.title(f"{APP_NAME} · v{APP_VERSION}")
        # 화면 해상도와 Windows 배율에 맞춰 초기 크기와 최소 크기를 산정한다.
        self._반응형_예약 = None
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        try:
            scale = float(root.tk.call("tk", "scaling"))
        except (tk.TclError, ValueError, TypeError):
            scale = 1.0
        self._ui_scale = max(0.85, min(1.6, scale / (96 / 72)))
        safe_width = max(440, screen_width - max(32, round(48 * self._ui_scale)))
        safe_height = max(420, screen_height - max(64, round(96 * self._ui_scale)))
        width = min(round(960 * self._ui_scale), safe_width)
        height = min(round(760 * self._ui_scale), safe_height)
        root.geometry(f"{width}x{height}")
        self._minimum_width = min(round(520 * self._ui_scale), safe_width)
        self._minimum_height = min(round(480 * self._ui_scale), safe_height)
        root.minsize(self._minimum_width, self._minimum_height)
        root.resizable(True, True)
        self._테마_적용()
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        pad = max(12, round(24 * self._ui_scale))
        header = ttk.Frame(root, padding=(pad, max(10, round(18 * self._ui_scale)), pad,
                                         max(8, round(14 * self._ui_scale))), style="Header.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ttk.Label(header, text="문서 정리", style="AppTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="파일을 고르고 정리 방식을 선택하세요.",
                  style="HeaderHint.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.header_status = ttk.Label(header, text="새 작업", style="HeaderStatus.TLabel")
        self.header_status.grid(row=0, column=1, rowspan=2, sticky="e", padx=(18, 0))
        main_host = ttk.Frame(root, style="Main.TFrame")
        main_host.grid(row=1, column=0, sticky="nsew")
        main_host.grid_columnconfigure(0, weight=1)
        main_host.grid_rowconfigure(0, weight=1)
        main_canvas = tk.Canvas(main_host, bg=UI_COLORS["bg"], highlightthickness=0)
        main_canvas.grid(row=0, column=0, sticky="nsew")
        main_scrollbar = ttk.Scrollbar(main_host, orient="vertical", command=main_canvas.yview)
        main_scrollbar.grid(row=0, column=1, sticky="ns")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        main = ttk.Frame(main_canvas, padding=(pad, 0, pad, 0), style="Main.TFrame")
        main_window = main_canvas.create_window((0, 0), window=main, anchor="nw")
        main.bind("<Configure>", lambda _e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.bind("<Configure>", lambda e: main_canvas.itemconfigure(main_window, width=e.width))
        self.main_canvas = main_canvas
        self.main_scrollbar = main_scrollbar
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=3, minsize=round(170 * self._ui_scale))
        main.grid_rowconfigure(1, weight=0)
        main.grid_rowconfigure(2, weight=2, minsize=round(105 * self._ui_scale))
        card_padding = max(8, round(14 * self._ui_scale))
        file_frame = ttk.LabelFrame(main, text="문서", padding=card_padding, style="Card.TLabelframe")
        file_frame.grid(row=0, column=0, sticky="nsew")
        self.file_frame = file_frame
        file_frame.grid_columnconfigure(0, weight=1)
        file_frame.grid_rowconfigure(1, weight=1)
        self.drop_label = ttk.Label(file_frame, text="파일 또는 폴더를 끌어 놓거나 ‘파일 추가’를 선택하세요  ·  HWP, HWPX, TXT, MD, DOC(X), PDF", anchor="center", padding=(10, 10), style="Drop.TLabel")
        self.drop_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.파일_드롭)
        self.drop_label.bind("<Button-1>", lambda e: self.파일선택())
        list_frame = ttk.Frame(file_frame)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_list = tk.Listbox(list_frame, font=("맑은 고딕", 10), height=6,
            background=UI_COLORS["surface"], foreground=UI_COLORS["ink"], selectbackground=UI_COLORS["teal"],
            selectforeground="white", relief="flat", highlightthickness=1,
            highlightbackground=UI_COLORS["separator"], selectmode="extended", exportselection=False,
            yscrollcommand=scrollbar.set)
        self.file_list.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.file_list.yview)
        xscroll = ttk.Scrollbar(list_frame, orient="horizontal", command=self.file_list.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        self.file_list.config(xscrollcommand=xscroll.set)
        self.file_list.drop_target_register(DND_FILES)
        self.file_list.dnd_bind("<<Drop>>", self.파일_드롭)
        self.file_list.bind("<Double-Button-1>", self._문서_열기)
        file_actions = ttk.Frame(file_frame)
        self.file_actions = file_actions
        file_actions.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        self.file_buttons = []
        for title, command in (("파일 추가", self.파일선택), ("폴더 추가", self._폴더선택)):
            button = ttk.Button(file_actions, text=title, command=command)
            button.pack(side="left", padx=(0, 6))
            self.file_buttons.append(button)
        self.file_manage_button = ttk.Menubutton(file_actions, text="목록 관리 ▾")
        self.file_manage_menu = tk.Menu(self.file_manage_button, tearoff=False)
        self.file_manage_menu.add_command(label="선택 항목 제거", command=self._선택삭제)
        self.file_manage_menu.add_command(label="목록 비우기", command=self.목록지우기)
        self.file_manage_button["menu"] = self.file_manage_menu
        self.file_manage_button.pack(side="left", padx=(0, 6))
        self.file_buttons.append(self.file_manage_button)
        self.file_count = ttk.Label(file_actions, text="0개 문서", style="Hint.TLabel")
        self.file_count.pack(side="right")

        # 설정 변수
        저장된_설정 = 설정_불러오기()
        저장된_세부작업 = 저장된_설정.get("stage_choices", {})
        if isinstance(저장된_세부작업, dict):
            for mode, stages in self.stage_choices.items():
                저장값 = 저장된_세부작업.get(mode, {})
                if isinstance(저장값, dict):
                    self._세부작업_기본저장[mode] = True
                    for key in stages:
                        if isinstance(저장값.get(key), bool):
                            stages[key] = 저장값[key]
        self.review_document_kind = 저장된_설정.get("review_document_kind", "보고서")
        self.review_reading_purpose = 저장된_설정.get("review_reading_purpose", "상세 설명용")
        self._활성_서식_프로파일 = str(저장된_설정.get("active_format_profile", ""))
        self._프로파일_콤보_이름목록 = ["profile_combo", "main_profile_combo"]
        self.prevent_word_split_var = tk.BooleanVar(value=bool(저장된_설정["prevent_word_split"]))
        self.punctuation_var = tk.BooleanVar(value=bool(저장된_설정["punctuation"]))
        self.punctuation_threshold_var = tk.StringVar(value=str(저장된_설정["punctuation_threshold"]))
        self.keep_punctuation_set_var = tk.BooleanVar(value=bool(저장된_설정["keep_punctuation_set_together"]))
        self.color_mark_on_var = tk.BooleanVar(value=bool(저장된_설정["color_mark_on"]))
        self.color_var = tk.StringVar(value=str(저장된_설정["color"]))
        self.autoclose_var = tk.BooleanVar(value=bool(저장된_설정["autoclose"]))
        self.unify_result_window_var = tk.BooleanVar(value=bool(저장된_설정.get("unify_result_window", False)))
        서식통일_결과창_반영(self.unify_result_window_var.get())
        self.stdformat_var = tk.BooleanVar(value=bool(저장된_설정["stdformat"]))
        self.verify_var = tk.BooleanVar(value=bool(저장된_설정["verify"]))
        self.integrity_report_file_var = tk.BooleanVar(
            value=bool(저장된_설정.get("integrity_report_file", False)))
        self.final_review_file_var = tk.BooleanVar(
            value=bool(저장된_설정.get("final_review_file", False)))
        self.two_pass_var = tk.BooleanVar(value=bool(저장된_설정.get("two_pass_processing", False)))
        self.table_spacing_var = tk.BooleanVar(value=bool(저장된_설정.get("table_spacing", True)))
        self.log_file_var = tk.BooleanVar(value=bool(저장된_설정.get("log_file", False)))
        self.check_updates_on_start_var = tk.BooleanVar(
            value=bool(저장된_설정.get("check_updates_on_start", True))
        )
        self.developer_mode_var = tk.BooleanVar(value=bool(저장된_설정.get("developer_mode", False)))
        # 켜고 끄면 문서 도구 메뉴를 바로 보이거나 숨긴다.
        self.developer_mode_var.trace_add(
            "write", lambda *_: hasattr(self, "tools_button") and self._반응형_배치())
        # 작업 범위는 작업마다 정하는 값이라 저장하지 않고, 실행할 때마다 '문서 전체'로 시작한다.
        # 쪽 표시: 숫자 문자열 또는 '마지막쪽'(내부값 0). 종료쪽 기본값은 시작쪽이다.
        self.range_mode_var = tk.StringVar(value="all")
        self.range_start_var = tk.StringVar(value="1")
        self.range_end_var = tk.StringVar(value="1")
        self._범위_동기중 = False          # 프로그램이 값을 바꾸는 중(사용자 변경과 구분)
        self._범위_끝직접설정 = False      # 사용자가 종료쪽을 직접 바꿨는지
        self.retry_body_var = tk.StringVar(value=str(저장된_설정["retry_body"]))
        self.retry_table_var = tk.StringVar(value=str(저장된_설정["retry_table"]))
        self.linespacing_min_var = tk.StringVar(value=str(저장된_설정["linespacing_min"]))
        self.linespacing_max_var = tk.StringVar(value=str(저장된_설정["linespacing_max"]))
        self.font_folder_var = tk.StringVar(value=str(저장된_설정.get("hwp_font_folder", "")))
        self.paste_add_folder_var = tk.StringVar(value=str(저장된_설정.get("paste_add_folder", "")))
        저장된_기호글꼴 = 저장된_설정.get("symbol_fonts", {})
        self.symbol_font_vars = {}
        for 기호 in 문장기호_목록:
            항목 = {**기본_설정["symbol_fonts"].get(기호, {}), **저장된_기호글꼴.get(기호, {})}
            self.symbol_font_vars[기호] = {
                "font": tk.StringVar(value=str(항목.get("font", ""))),
                "size": tk.StringVar(value=str(항목.get("size", ""))),
            }
        저장된_표글꼴 = 저장된_설정.get("table_fonts") or {}
        self.table_font_vars = {}
        for part in ("header", "body"):
            항목 = {**기본_설정["table_fonts"][part], **(저장된_표글꼴.get(part) or {})}
            self.table_font_vars[part] = {
                "font": tk.StringVar(value=str(항목.get("font", ""))),
                "size": tk.StringVar(value=str(항목.get("size", ""))),
            }
        if not self.font_folder_var.get():
            self.font_folder_var.set(한글_폰트_폴더_자동감지())
        self._한글_폰트_목록_캐시 = 한글_폰트_목록_전체(self.font_folder_var.get())
        기호글꼴_적용(저장된_설정)
        self.paren_shrink_var = tk.BooleanVar(value=bool(저장된_설정["paren_shrink"]))
        self.paren_label_bold_var = tk.BooleanVar(value=bool(저장된_설정["paren_label_bold"]))
        label_keys = ['□', 'ㅁ', 'ㅇ', '○', '-', '※', '*', '**'] + sorted(공문서_기호 - set('□ㅁㅇ○-※')) + ['기타']
        self.label_symbol_vars = {key: tk.BooleanVar(value=bool(저장된_설정['label_symbols'].get(key, True))) for key in label_keys}
        for var in self.label_symbol_vars.values():
            var.trace_add('write', self._설정_변경됨)


        self.std_bool_keys = [
            "std_margin", "std_ratio", "std_linespacing", "std_title", "std_title_bold", "std_title_auto", "std_attachment_auto", "std_midtitle_auto", "std_midtitle_bold",
            "std_dateinfo", "std_dateinfo_bold", "std_symbols", "std_symbol_box_bold",
            "std_symbol_o_bold", "std_symbol_dash_bold", "std_symbol_note_bold",
            "std_marker_bold_consistency",
            "std_remove_blank_lines",
            "std_hanging_indent",
            "std_supplement_indent",
            "std_parspace", "std_table_header",
        ]
        self.std_bool_vars = {키: tk.BooleanVar(value=bool(저장된_설정[키])) for 키 in self.std_bool_keys}

        # 숫자 설정(문단 위 간격·복귀 배율·제목 부제 크기). 저장·기본값 초기화·서식 프로필 반영을 함께 쓴다.
        self.std_parspace_str_keys = ["std_parspace_chapter", "std_parspace_midtitle",
                                      "std_parspace_box", "std_parspace_circle", "std_parspace_dash",
                                      "std_parspace_note", "std_parspace_return_percent", "std_title_subtitle_pt"]
        self.std_parspace_vars = {키: tk.StringVar(value=str(저장된_설정[키])) for 키 in self.std_parspace_str_keys}
        # 부제 크기는 붙여넣은 글 변환(작업 실행 밖)에서도 쓰므로 바뀌는 즉시 전역값에 반영한다.
        제목_부제_크기_반영(저장된_설정["std_title_subtitle_pt"])
        self.std_parspace_vars["std_title_subtitle_pt"].trace_add(
            "write", lambda *_: 제목_부제_크기_반영(self.std_parspace_vars["std_title_subtitle_pt"].get()))
        # 제목 표 담당자 칸(B2) 글: 사용자 고유 글이라 서식 프로필을 골라도 바꾸지 않는다. 바뀌면 바로 반영·저장한다.
        self.title_owner_var = tk.StringVar(value=str(저장된_설정.get("title_owner_text", "") or ""))
        제목_담당자_글_반영(self.title_owner_var.get())
        self.title_owner_var.trace_add("write", lambda *_: 제목_담당자_글_반영(self.title_owner_var.get()))
        self.title_owner_var.trace_add("write", self._설정_변경됨)

        for 변수 in ([self.prevent_word_split_var, self.punctuation_var, self.punctuation_threshold_var, self.keep_punctuation_set_var,
                     self.color_mark_on_var, self.color_var,
                     self.autoclose_var, self.unify_result_window_var,
                     self.stdformat_var, self.verify_var, self.integrity_report_file_var,
                     self.final_review_file_var, self.two_pass_var,
                     self.table_spacing_var, self.log_file_var, self.check_updates_on_start_var,
                     self.developer_mode_var,
                     self.retry_body_var, self.retry_table_var, self.paren_shrink_var,
                     self.linespacing_min_var, self.linespacing_max_var, self.font_folder_var,
                     self.paste_add_folder_var,
                     self.paren_label_bold_var] + list(self.std_bool_vars.values()) + list(self.std_parspace_vars.values())
                    + [v for 항목 in self.symbol_font_vars.values() for v in 항목.values()]
                    + [v for 항목 in self.table_font_vars.values() for v in 항목.values()]):
            변수.trace_add("write", self._설정_변경됨)

        self.color_radios = []
        self.std_detail_checks = []
        self.std_parspace_spins = []
        self.settings_toplevel = None

        self.selected_mode = tk.StringVar(value="spacing")
        self.always_on_top_var = tk.BooleanVar(value=bool(저장된_설정.get("always_on_top", True)))
        # 카드는 세 장이다. '한 번에 적용'에서 자간 조정을 빼면 내부 작업 유형은 서식 적용(format)이다.
        self.include_spacing_var = tk.BooleanVar(value=bool(저장된_설정.get("all_include_spacing", True)))
        self.include_spacing_var.trace_add("write", self._설정_변경됨)
        # '한 번에 적용'의 '표 제외'. 켜면 표 관련 세부 작업을 모두 뺀다(설정 파일에 저장).
        self.exclude_tables_var = tk.BooleanVar(value=bool(저장된_설정.get("all_exclude_tables", False)))
        # '한 번에 적용'의 '페이지 맞춤 제외'와 '서식 통일' 카드의 표 제외·자간 정리 제외·페이지 맞춤 제외. 세부 작업과
        # 연동한다(_카드옵션_연동_시작).
        self.all_exclude_pagefit_var = tk.BooleanVar(value=bool(저장된_설정.get("all_exclude_pagefit", False)))
        self.unify_exclude_tables_var = tk.BooleanVar(value=bool(저장된_설정.get("unify_exclude_tables", False)))
        self.unify_exclude_spacing_var = tk.BooleanVar(value=bool(저장된_설정.get("unify_exclude_spacing", False)))
        self.unify_exclude_pagefit_var = tk.BooleanVar(value=bool(저장된_설정.get("unify_exclude_pagefit", True)))
        self.unify_keep_layout_var = tk.BooleanVar(value=bool(저장된_설정.get("unify_keep_layout", True)))
        for 변수 in (self.exclude_tables_var, self.all_exclude_pagefit_var, self.unify_exclude_tables_var,
                     self.unify_exclude_spacing_var, self.unify_exclude_pagefit_var, self.unify_keep_layout_var):
            변수.trace_add("write", self._설정_변경됨)
            변수.trace_add("write", self._요약갱신)
        # '자간 정리' 카드의 '기존 자간 초기화'. 세부 작업 01(문서 전체 자간 초기화)과 같은 값이며 설정 파일에 저장한다.
        저장된_초기화 = 저장된_설정.get("spacing_reset_existing")
        if isinstance(저장된_초기화, bool):
            self.stage_choices["spacing"]["reset_spacing"] = 저장된_초기화
        self.reset_spacing_var = tk.BooleanVar(value=bool(self.stage_choices["spacing"]["reset_spacing"]))
        self.reset_spacing_var.trace_add("write", self._자간초기화_값변경)
        # '자간 정리' 카드의 '표 제외'는 설정 table_spacing(표 안 문장 자간조정)의 반대 값이다. 바꾸면 카드 요약
        # 문구도 고친다(저장은 설정 변경 감시가 한다).
        self.table_spacing_var.trace_add("write", self._요약갱신)
        self.card_mode_var = tk.StringVar(value="spacing")   # 카드 표시용(format도 '한 번에 적용' 카드)
        choose = ttk.LabelFrame(main, text="처리 방식", padding=card_padding, style="Card.TLabelframe")
        choose.grid(row=1, column=0, sticky="ew", pady=6)
        self.choose_frame = choose
        self.mode_buttons = []
        self.mode_cards = {}
        self.card_option_checks = {}   # 카드별 옵션 체크(선택한 카드 배경색을 같이 바꾼다)
        for i, (title, mode, desc) in enumerate((
            ("자간 정리", "spacing", "줄 끝의 끊긴 단어와 자간을 정리합니다."),
            ("서식 통일", "unify", "문서에서 많이 쓰인 서식으로 맞춥니다."),
            ("한 번에 적용", "all", "공문서 서식을 입히고 자간까지 정리합니다."))):
            choose.grid_columnconfigure(i, weight=1, uniform="modes")
            card = tk.Frame(choose, bg=UI_COLORS["separator"], padx=1, pady=1, cursor="hand2")
            card.grid(row=1, column=i, sticky="nsew", padx=max(2, round(4 * self._ui_scale)))
            inner = tk.Frame(card, bg=UI_COLORS["surface"], padx=max(7, round(12 * self._ui_scale)),
                             pady=max(6, round(10 * self._ui_scale)), cursor="hand2")
            inner.pack(fill="both", expand=True)
            rb = ttk.Radiobutton(inner, text=title, value=mode, variable=self.card_mode_var,
                                 command=lambda m=mode: self._카드_클릭(m), style="Mode.TRadiobutton")
            rb.pack(anchor="w")
            description = tk.Label(inner, text=desc.replace("\n", " "), bg=UI_COLORS["surface"],
                                   fg=UI_COLORS["muted"], justify="left", anchor="w",
                                   wraplength=max(100, round(160 * self._ui_scale)),
                                   font=("맑은 고딕", 9), cursor="hand2")
            description.pack(anchor="w", fill="x", pady=(5, 8))
            self.mode_buttons.append(rb)

            def 카드_체크(text, variable, command, m=mode, inner=inner, **옵션):
                check = tk.Checkbutton(
                    inner, text=text, variable=variable, command=command, bg=UI_COLORS["surface"],
                    activebackground=UI_COLORS["surface"], fg=UI_COLORS["ink"], font=("맑은 고딕", 9),
                    anchor="w", cursor="hand2", **옵션)
                check.pack(anchor="w", pady=(0, 4))
                self.mode_buttons.append(check)
                self.card_option_checks.setdefault(m, []).append(check)
                return check
            if mode == "spacing":
                # 끄면 문서에 이미 있는 자간을 0%로 되돌리지 않고 그 위에서 정리한다.
                self.reset_spacing_check = tk.Checkbutton(
                    inner, text="기존 자간 초기화", variable=self.reset_spacing_var,
                    command=self._자간초기화_변경, bg=UI_COLORS["surface"], activebackground=UI_COLORS["surface"],
                    fg=UI_COLORS["ink"], font=("맑은 고딕", 9), anchor="w", cursor="hand2")
                self.reset_spacing_check.pack(anchor="w", pady=(0, 4))
                self.mode_buttons.append(self.reset_spacing_check)
                self.card_option_checks.setdefault(mode, []).append(self.reset_spacing_check)
                # '표 제외'(기본 꺼짐): 켜면 표 칸 안 문장은 자간 초기화·자간 조정·줄 병합·단어 검사 대상에서 뺀다.
                # 설정 table_spacing(설정창 '표 서식 내 문장도 자간조정하기')의 반대 값이라 켜면 False를 넣는다
                # (2026-10-04 사용자 요청: '표 내 자간 정리'를 '표 제외'로 바꿈).
                self.table_spacing_card_check = 카드_체크(
                    "표 제외", self.table_spacing_var, self._자간초기화_변경, onvalue=False, offvalue=True)
            if mode == "unify":
                # 켜면 기본 표 서식·표 서식통일을 뺀다.
                self.unify_exclude_tables_check = 카드_체크(
                    "표 제외", self.unify_exclude_tables_var, lambda: self._카드옵션_변경("unify"))
                # 켜면 서식통일이 고친 문장의 자간 조정·외톨이 글자 당기기를 뺀다(내어쓰기는 맞춘다).
                self.unify_exclude_spacing_check = 카드_체크(
                    "자간 정리 제외", self.unify_exclude_spacing_var, lambda: self._카드옵션_변경("unify"))
                # 켜면 문단 아래 간격 페이지 맞춤·관련 문단 페이지 배치를 뺀다.
                self.unify_exclude_pagefit_check = 카드_체크(
                    "페이지 맞춤 제외", self.unify_exclude_pagefit_var, lambda: self._카드옵션_변경("unify"))
                # 켜면 결과의 쪽 구성(보고서별 쪽 수·시작 쪽, 전체 쪽 수)을 원본과 같게 맞춘다.
                self.unify_keep_layout_check = 카드_체크(
                    "원본 쪽 구성 유지", self.unify_keep_layout_var, lambda: self._카드옵션_변경("unify"))
            if mode == "all":
                # 끄면 기존 자간을 그대로 두고 서식만 입힌다(결과 파일 이름은 '서식적용').
                self.include_spacing_check = tk.Checkbutton(
                    inner, text="자간 조정 포함", variable=self.include_spacing_var,
                    command=self._자간포함_변경, bg=UI_COLORS["surface"], activebackground=UI_COLORS["surface"],
                    fg=UI_COLORS["ink"], font=("맑은 고딕", 9), anchor="w", cursor="hand2")
                self.include_spacing_check.pack(anchor="w", pady=(0, 4))
                self.mode_buttons.append(self.include_spacing_check)
                self.card_option_checks.setdefault(mode, []).append(self.include_spacing_check)
                # 켜면 표 관련 작업(텍스트 표 변환·기본 표 서식·표 칸 너비·표 정밀 서식·표 머리글 서식·
                # 표 안 자간·줄·단어 작업)을 모두 빼고 실행한다. 제목·개요 서식 표는 그대로 정리한다.
                self.exclude_tables_check = 카드_체크("표 제외", self.exclude_tables_var, self._표제외_변경)
                # 켜면 문단 아래 간격 페이지 맞춤·관련 문단 페이지 배치를 뺀다.
                self.all_exclude_pagefit_check = 카드_체크(
                    "페이지 맞춤 제외", self.all_exclude_pagefit_var, self._표제외_변경)
            self.mode_cards[mode] = (card, inner, description)
            for surface in (card, inner, description):
                surface.bind("<Button-1>", lambda e, m=mode: self._카드_클릭(m))
        quick = ttk.Frame(choose)
        self.quick_actions = quick
        quick.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(max(3, round(5 * self._ui_scale)), 0))
        self.settings_button = ttk.Button(quick, text="설정", command=self.설정창_열기)
        self.settings_button.pack(side="right")
        self.stage_details_button = ttk.Button(
            quick, text="작업 항목", command=lambda: self._세부작업_열기(self.selected_mode.get()))
        self.stage_details_button.pack(side="right", padx=(0, 6))
        self.tools_button = ttk.Menubutton(quick, text="도구 ▾")
        self.tools_menu = tk.Menu(self.tools_button, tearoff=False)
        for label, command in (("문서 구조 검토…", self._문서검토_열기),
                               ("맞춤법 검토…", self._공공언어_검토),
                               ("텍스트 붙여넣기 정리…", self._텍스트로_문서추가_열기),
                               ("붙여넣은 문장 다듬기…", self._붙여넣기_정리_열기),
                               ("아웃라이너로 작성…", self._아웃라이너_열기),
                               ("작성 도우미…", self._작성도우미_열기),
                               ("Markdown 내보내기…", self.Markdown_내보내기),
                               ("고급 문서 도구…", self.고급문서도구_열기)):
            self.tools_menu.add_command(label=label, command=command)
        self.tools_button["menu"] = self.tools_menu
        self.tools_button.pack(side="right", padx=(0, 6))
        self._보조_도구들 = [self.tools_button]
        self.document_review_button = ttk.Button(quick, text="문서 구조 검토", command=self._문서검토_열기)
        self.proofread_button = ttk.Button(quick, text="맞춤법 검토", command=self._공공언어_검토)
        self.options_summary = ttk.Label(quick, style="Hint.TLabel", wraplength=540, justify="left")
        self.options_summary.pack(side="left")

        # 실행창에서 바로 사용할 서식 선택과 예시 문서 드롭 분석.
        format_quick = ttk.Frame(choose)
        self.format_quick = format_quick
        format_quick.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(max(4, round(6 * self._ui_scale)), 0))
        ttk.Label(format_quick, text="적용 서식", font=("맑은 고딕", 9, "bold")).pack(side="left", padx=(0, 6))
        self.main_profile_combo = ttk.Combobox(format_quick, state="readonly", width=20)
        self.main_profile_combo.pack(side="left")
        self.main_profile_combo.bind("<<ComboboxSelected>>", self._프로파일_선택)
        # 고른 서식을 예시 보고서에 입혀 한/글로 미리 보여 준다(2026-10-04 사용자 요청).
        self.format_example_button = ttk.Button(format_quick, text="서식 예시 확인", command=self._서식예시_확인)
        self.format_example_button.pack(side="left", padx=(6, 0))
        self.format_drop_label = ttk.Label(
            format_quick,
            text="예시 HWP/HWPX를 여기에 놓으면 분석 후 바로 선택합니다",
            style="Drop.TLabel",
            padding=(8, 4),
            anchor="center",
        )
        self.format_drop_label.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.format_drop_label.drop_target_register(DND_FILES)
        self.format_drop_label.dnd_bind("<<Drop>>", self.서식파일_드롭)

        # 작업 범위: 기본은 문서 전체. 쪽을 지정하면 그 쪽에 놓인 내용만 처리한다.
        scope = ttk.Frame(choose)
        self.scope_frame = scope
        scope.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(max(4, round(6 * self._ui_scale)), 0))
        self.range_all_radio = ttk.Radiobutton(scope, text="문서 전체", value="all", variable=self.range_mode_var)
        self.range_pages_radio = ttk.Radiobutton(scope, text="쪽 지정", value="pages", variable=self.range_mode_var)
        self.page_range_var = tk.BooleanVar(value=False)
        self.page_range_toggle = ttk.Checkbutton(
            scope, text="특정 쪽만 정리", variable=self.page_range_var, command=self._쪽범위_토글)
        self.page_range_toggle.pack(side="left")
        self.page_range_details = ttk.Frame(scope)
        ttk.Label(self.page_range_details, text="시작").pack(side="left", padx=(12, 4))
        self.range_start_spin = ttk.Spinbox(self.page_range_details, values=self._쪽_목록(), wrap=False, width=8, justify="center",
                                            textvariable=self.range_start_var, state="disabled")
        self.range_start_spin.pack(side="left")
        ttk.Label(self.page_range_details, text="종료").pack(side="left", padx=(10, 4))
        self.range_end_spin = ttk.Spinbox(self.page_range_details, values=self._쪽_목록(1), wrap=False, width=8, justify="center",
                                          textvariable=self.range_end_var, state="disabled")
        self.range_end_spin.pack(side="left")
        self.range_hint = ttk.Label(self.page_range_details, text="1의 아래는 ‘마지막쪽’", style="Hint.TLabel")
        self.range_hint.pack(side="left", padx=(8, 0))
        self.range_mode_var.trace_add("write", self._범위_상태_갱신)
        self.range_start_var.trace_add("write", self._범위_시작_변경)
        self.range_end_var.trace_add("write", self._범위_끝_변경)
        status_frame = ttk.LabelFrame(main, text="진행 상황", padding=card_padding, style="Card.TLabelframe")
        status_frame.grid(row=2, column=0, sticky="ew")
        self.status_var = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.status_var, wraplength=540, style="Status.TLabel").pack(anchor="w")
        self.STEP_IDLE_BG = UI_COLORS["rose"]
        self.STEP_ACTIVE_BG = UI_COLORS["teal"]
        self.STEP_IDLE_FG = UI_COLORS["ink"]
        self.STEP_ACTIVE_FG = "white"
        self.step_boxes = {}  # 이전 설정 코드와의 호환
        self._안내키, self._안내지남 = None, set()   # 진행 화면 단계 안내 상태
        self.stage_board = LiveStageBoard(status_frame)
        self.stage_board.pack(fill="x", pady=(2, 0))
        # '03 진행 상황' 바로 아래 결과 줄: 결과 버튼 두 개(작업 결과가 나오기 전에는 비활성)와,
        # 그 오른쪽 옆에 저장 안내 / '[작업 결과]' 문구를 둔다.
        self._결과목록 = []
        self._재개_대기중 = False    # 중단 버튼으로 멈춘 작업이 있어 실행 버튼으로 이어서 진행할 수 있는 상태
        self._재개_시작_인덱스 = 1
        self._재개_모드 = None
        self._작업시작시각 = None
        self._작업모드 = "all"
        self.result_bar = ttk.Frame(main, height=40)
        self.result_bar.grid(row=3, column=0, sticky="ew", pady=5)
        self.result_bar.pack_propagate(False)
        self.open_folder_button = ttk.Button(self.result_bar, text="원본 폴더 열기", command=self._원본폴더_열기, state="disabled")
        self.open_folder_button.pack(side="left")
        self.open_result_button = ttk.Button(self.result_bar, text="결과파일 열기", command=self._결과파일_열기, state="disabled")
        self.open_result_button.pack(side="left", padx=(8, 0))
        self.footer_note_var = tk.StringVar(value=self.FOOTER_NOTE_DEFAULT)
        self.footer_note = ttk.Label(self.result_bar, textvariable=self.footer_note_var, style="Hint.TLabel",
                                     wraplength=440, justify="left")
        self.footer_note.pack(side="left", padx=(12, 0))
        self.log_window = tk.Toplevel(root)
        self.log_window.title(f"처리 기록 · {APP_NAME}")
        self.log_window.geometry("780x360")
        self.log_window.minsize(500, 240)
        self.log_window.protocol("WM_DELETE_WINDOW", self._기록닫기)
        self.log_frame = ttk.LabelFrame(self.log_window, text="처리 기록 · 문제가 생기면 여기서 확인하세요", padding=10)
        self.log_frame.pack(fill="both", expand=True)
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)
        log_scroll = ttk.Scrollbar(self.log_frame)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text = tk.Text(self.log_frame, height=5, font=("맑은 고딕", 9), wrap="word",
            bg="white", fg=UI_COLORS["ink"], relief="flat", yscrollcommand=log_scroll.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll.config(command=self.log_text.yview)
        self.log_text.bind("<Key>", self._로그_키입력_차단)
        self.log_window.withdraw()
        self._log_visible = False
        footer = ttk.Frame(root, padding=(12, 4, 12, 6))
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        # 창 닫기는 운영체제 제목 표시줄에 맡기고, 하단에는 작업 동작만 둔다.
        right = ttk.Frame(footer)
        right.grid(row=0, column=1, sticky="e")
        for col in range(2):
            right.grid_columnconfigure(col, uniform="footer_btn")
        # 중단은 보조 동작, 문서 정리는 화면의 단일 주요 동작이다.
        def 버튼_칸(열):
            칸 = tk.Frame(right, bg=UI_COLORS["bg"], padx=2, pady=2)
            칸.grid(row=0, column=열, sticky="ew", padx=1)
            return 칸
        self.stop_button = ttk.Button(버튼_칸(0), text="중단", width=10, command=self.작업중단, state="disabled")
        self.stop_button.pack(fill="x")
        self.start_wrap = 버튼_칸(1)
        self.start_button = ttk.Button(self.start_wrap, text="정리 시작", width=14, style="Start.TButton",
            command=lambda: self.작업시작(self.selected_mode.get()), state="disabled")
        self.start_button.pack(fill="x")
        self.run_buttons = [self.start_button]
        self.selected_mode.trace_add("write", self._요약갱신)
        self.selected_mode.trace_add("write", self._모드카드_외관갱신)
        self.always_on_top_var.trace_add("write", self._항상위_변경)
        for var in (self.stdformat_var, *self.std_bool_vars.values()):
            var.trace_add("write", self._요약갱신)
        self._카드옵션_연동_시작()
        self._요약갱신()
        self._모드카드_외관갱신()
        self._안내_설정(1)     # 처음에는 '01 정리할 문서'부터 안내한다.

        file_frame.drop_target_register(DND_FILES)
        file_frame.dnd_bind("<<Drop>>", self.파일_드롭)

        self._프로파일들 = 서식프로파일_목록()
        if self._활성_서식_프로파일 not in self._프로파일들:
            self._활성_서식_프로파일 = ""
        self._프로파일_전역반영(self._프로파일들[self._활성_서식_프로파일])
        self._설정창_생성()
        self._항상위_적용()

        self._queue_after_id = root.after(100, self.queue_처리)
        root.bind("<Destroy>", self._루트_파괴시_예약취소, add="+")
        root.bind("<Control-o>", lambda e: self.파일선택())
        root.bind("<Configure>", self._메인_크기조정, add="+")
        root.protocol("WM_DELETE_WINDOW", self.종료)
        root.after_idle(self._창_최소높이_보정)
        if getattr(sys, "frozen", False):
            업데이트_시작신호()
            # 지난 업데이트가 남긴 구버전 백업과 내려받기 잔여물을 정리한다(교체가 끝난 다음 실행에서).
            threading.Thread(target=업데이트_잔여정리, daemon=True, name="update-cleanup").start()
        if getattr(sys, "frozen", False) and self.check_updates_on_start_var.get():
            root.after(1500, self._자동업데이트_확인_시작)


    def _자동업데이트_확인_시작(self, 수동=False):
        if 수동:
            버튼 = getattr(self, "update_button", None)
            if 버튼 is not None:
                버튼.config(state="disabled")
            self.status_var.set("새 업데이트가 있는지 확인하고 있어요…")

        def 결과_표시(릴리스=None, 오류=None):
            버튼 = getattr(self, "update_button", None)
            if 버튼 is not None and not self.running:
                버튼.config(state="normal")
            if 오류 is not None:
                if 수동:
                    messagebox.showerror(
                        APP_NAME,
                        f"업데이트 정보를 확인하지 못했습니다.\n\n{오류}",
                        parent=self.settings_toplevel or self.root,
                    )
                    self.status_var.set("업데이트 확인에 실패했어요.")
                return
            최신버전 = str((릴리스 or {}).get("tag_name") or (릴리스 or {}).get("name") or APP_VERSION)
            if not 릴리스 or _버전_튜플(최신버전) <= _버전_튜플(APP_VERSION):
                if 수동:
                    messagebox.showinfo(
                        APP_NAME,
                        "현재 최신버전입니다.",
                        parent=self.settings_toplevel or self.root,
                    )
                    self.status_var.set("현재 최신버전입니다.")
                return
            self._자동업데이트_안내(릴리스)

        def 확인():
            try:
                릴리스 = _최신_릴리스_통합_조회()
            except Exception as exc:
                # 네트워크가 없거나 GitLab이 응답하지 않아도 앱 사용은 막지 않는다.
                if 수동:
                    try:
                        self.root.after(0, lambda 오류=str(exc): 결과_표시(오류=오류))
                    except Exception:
                        pass
                return
            try:
                self.root.after(0, lambda: 결과_표시(릴리스=릴리스))
            except Exception:
                pass

        threading.Thread(target=확인, daemon=True, name="release-update-check").start()

    def _자동업데이트_안내(self, 릴리스):
        if self.closing or self.running:
            return
        자산 = _업데이트_자산_선택(릴리스)
        버전 = str(릴리스.get("tag_name") or 릴리스.get("name") or "새 버전")
        if not 자산 or not 자산.get("browser_download_url"):
            messagebox.showinfo(
                APP_NAME,
                f"{버전} 정식 버전이 출시되었지만 Windows EXE 파일이 없습니다.\n"
                f"Release에 {UPDATE_ASSET_NAME}를 첨부해 주세요.",
                parent=self.root,
            )
            return
        if not messagebox.askyesno(
            APP_NAME,
            f"새 정식 버전 {버전}이 출시되었습니다.\n\n"
            "지금 다운로드하고 앱을 자동으로 업데이트할까요?",
            parent=self.root,
        ):
            return
        self.status_var.set(f"{버전} 업데이트를 다운로드하고 있어요…")
        threading.Thread(
            target=self._자동업데이트_다운로드,
            args=(릴리스, 자산),
            daemon=True,
            name="release-update-download",
        ).start()

    def _자동업데이트_다운로드(self, 릴리스, 자산):
        """'.part'로 받고 크기·EXE 머리·SHA-256(자산 digest 또는 릴리스 노트)을 확인한 뒤 확정한다."""
        임시 = None
        try:
            업데이트_폴더 = 설정_폴더() / "updates"
            업데이트_폴더.mkdir(parents=True, exist_ok=True)
            버전 = re.sub(r"[^0-9A-Za-z._-]+", "_", str(릴리스.get("tag_name", "latest")))
            다운로드_경로 = 업데이트_폴더 / f"HWP_AutoDocFit-{버전}.exe"
            임시 = 다운로드_경로.with_name(다운로드_경로.name + ".part")
            다운로드_URL = _업데이트_URL_검증(자산["browser_download_url"])
            예상해시 = 업데이트_예상해시(릴리스, 자산)
            해시 = hashlib.sha256()
            크기 = 0
            머리 = b""
            응답 = _업데이트_HTTP_GET(다운로드_URL,
                                    {"User-Agent": f"HWP-AutoDocFit/{APP_VERSION}"}, 30)
            try:
                with open(임시, "wb") as 출력:
                    while True:
                        조각 = 응답.read(1024 * 1024)
                        if not 조각:
                            break
                        if len(머리) < 2:
                            머리 += 조각[:2]
                        출력.write(조각)
                        해시.update(조각)
                        크기 += len(조각)
            finally:
                응답._docfit_connection.close()
            문제 = 업데이트_파일검증(크기, 머리, 해시.hexdigest(), int(자산.get("size") or 0) or None, 예상해시)
            if 문제:
                raise RuntimeError(문제)
            os.replace(임시, 다운로드_경로)
            임시 = None
            _업데이트_기록(f"내려받기 완료: {다운로드_경로.name} {크기:,}바이트, SHA-256 확인")
            self.root.after(0, lambda: self._자동업데이트_설치(다운로드_경로, 예상해시))
        except Exception as exc:
            _업데이트_기록(f"내려받기 실패: {exc}")
            try:
                self.root.after(0, lambda 오류=str(exc): messagebox.showerror(
                    APP_NAME, f"자동 업데이트를 다운로드하지 못했습니다.\n\n{오류}", parent=self.root
                ))
            except Exception:
                pass
        finally:
            if 임시 is not None:
                try:
                    Path(임시).unlink()
                except OSError:
                    pass

    def _자동업데이트_설치(self, 다운로드_경로, 예상해시=None):
        """구버전을 '.old'로 바꾸고 신버전을 원래 이름으로 넣는 교체 스크립트를 띄운 뒤 앱을 끝낸다.

        PyInstaller 단일 EXE는 부트로더(부모)와 Python(자식) 두 프로세스로 돈다. 예전에는 자식만 기다려 부모가 EXE를
        잡고 있는 동안 복사가 실패했고, 그러면 내려받은 파일을 그 자리에서 실행해 구버전이 남았다(2026-10-09).
        """
        현재_실행파일 = Path(sys.executable).resolve()
        폴더 = 현재_실행파일.parent
        try:
            시험 = 폴더 / f".docfit_update_test_{os.getpid()}"
            시험.write_bytes(b"")
            시험.unlink()
        except OSError:
            _업데이트_기록(f"설치 폴더에 쓸 수 없음: {폴더}")
            messagebox.showwarning(
                APP_NAME,
                f"설치 폴더에 쓸 권한이 없어 자동으로 바꿀 수 없습니다.\n{폴더}\n\n"
                f"내려받은 새 버전으로 직접 바꿔 주세요:\n{다운로드_경로}",
                parent=self.root,
            )
            try:
                os.startfile(str(다운로드_경로.parent))
            except Exception:
                pass
            return
        스크립트 = 다운로드_경로.with_suffix(".ps1")
        스크립트.write_text(업데이트_교체스크립트(), encoding="utf-8-sig")
        기다릴 = [os.getpid()]
        try:
            부모 = os.getppid()
            if 부모 and 부모 != os.getpid():
                기다릴.append(부모)
        except Exception:
            pass
        try:
            subprocess.Popen(
                [
                    "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(스크립트), "-WaitPidList", " ".join(str(x) for x in 기다릴),
                    "-Downloaded", str(다운로드_경로), "-Target", str(현재_실행파일),
                    "-Log", str(다운로드_경로.parent / "update.log"), "-Sha256", str(예상해시 or ""),
                    "-StartedFlag", str(다운로드_경로.parent / UPDATE_STARTED_FLAG),
                    "-BusyFlag", str(다운로드_경로.parent / UPDATE_BUSY_FLAG),
                ],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                env=업데이트_실행환경(os.environ),
            )
        except Exception:
            try:
                스크립트.unlink()
            except OSError:
                pass
            raise
        _업데이트_기록(f"교체 스크립트 시작: {현재_실행파일.name} ← {다운로드_경로.name}")
        self.closing = True
        self.root.destroy()

    def _항상위_적용(self):
        """실행창(및 함께 쓰는 처리 기록·설정 창)을 항상 위에 둘지 반영한다."""
        try:
            켜짐 = bool(self.always_on_top_var.get())
        except Exception:
            켜짐 = True
        for 창 in (self.root, getattr(self, "log_window", None), getattr(self, "settings_toplevel", None)):
            try:
                if 창 is not None and 창.winfo_exists():
                    창.attributes("-topmost", 켜짐)
            except Exception:
                pass

    def _항상위_변경(self, *args):
        self._항상위_적용()
        self._설정_변경됨()

    def _창_최소높이_보정(self):
        """화면 해상도와 Windows 논리 배율을 반영한 최소 창 크기를 적용한다."""
        self.root.update_idletasks()
        screen_width, screen_height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        scale = getattr(self, "_ui_scale", 1.0)
        min_width = min(max(self._minimum_width, round(520 * scale)), screen_width - 24)
        min_height = min(max(self._minimum_height, round(480 * scale)), screen_height - 48)
        if not getattr(self.root, "_docfit_hidden_backend", False):
            self.root.minsize(max(420, min_width), max(400, min_height))
        self._반응형_배치()

    def _테마_적용(self):
        c = UI_COLORS
        self.root.configure(bg=c["bg"])
        self.root.option_add("*Font", ("맑은 고딕", 10))
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=c["bg"], foreground=c["ink"], font=("맑은 고딕", 10))
        style.configure("Header.TFrame", background=c["surface"])
        style.configure("Main.TFrame", background=c["bg"])
        style.configure("AppTitle.TLabel", background=c["surface"], foreground=c["ink"], font=("맑은 고딕", 20, "bold"))
        style.configure("HeaderHint.TLabel", background=c["surface"], foreground=c["muted"], font=("맑은 고딕", 10))
        style.configure("HeaderStatus.TLabel", background=c["teal_tint"], foreground=c["teal_dark"], padding=(11, 5), font=("맑은 고딕", 9, "bold"))
        style.configure("TButton", padding=(10, 5), borderwidth=0, background=c["surface"])
        style.map("TButton", background=[("active", c["teal_tint"]), ("disabled", c["bg"])], foreground=[("disabled", "#8E8E93")])
        style.configure("Start.TButton", background=c["teal"], foreground="white", padding=(14, 6), font=("맑은 고딕", 10, "bold"))
        style.map("Start.TButton", background=[("disabled", c["separator"]), ("active", c["teal_dark"])], foreground=[("disabled", c["muted"])])
        style.configure("TLabelframe", background=c["surface"], bordercolor=c["separator"], relief="solid")
        style.configure("Card.TLabelframe", background=c["surface"], bordercolor=c["separator"], relief="solid")
        # 다음 행동만 파란 테두리로 보인다. 색만으로 오류·우선순위를 전달하지 않는다.
        style.configure("Guide.TLabelframe", background=c["surface"], bordercolor=c["teal"], relief="solid")
        style.configure("TLabelframe.Label", background=c["surface"], foreground=c["ink"], font=("맑은 고딕", 11, "bold"))
        style.configure("Section.TLabel", background=c["surface"], foreground=c["ink"], font=("맑은 고딕", 9, "bold"))
        style.configure("Hint.TLabel", background=c["surface"], foreground=c["muted"], font=("맑은 고딕", 9))
        style.configure("Status.TLabel", background=c["surface"], foreground=c["teal_dark"])
        style.configure("Result.TLabel", background=c["surface"], foreground=c["success"], font=("맑은 고딕", 9, "bold"))
        style.configure("Drop.TLabel", background=c["teal_tint"], foreground=c["ink"])
        style.configure("Mode.TRadiobutton", background=c["surface"], font=("맑은 고딕", 10, "bold"))
        style.configure("Stage.TCheckbutton", font=("맑은 고딕", 10, "bold"))
        style.configure("TNotebook", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(12, 9), background=c["rose"])
        style.map("TNotebook.Tab", background=[("selected", c["lavender"]), ("active", "#E5E1F4")], foreground=[("selected", c["ink"])])
        style.map("TCheckbutton", indicatorbackground=[("selected", c["teal"]), ("disabled", c["rose"])])

    def _자간정리_항목_상세(self, parent, key, *, 주설정탭):
        """'자간 정리' 세부 설정 탭과 세부 작업 창이 함께 쓰는 항목별 상세 위젯.

        같은 변수(self.xxx_var)에 새 위젯을 만들어 값은 항상 공유한다.
        주설정탭=True(세부 설정 탭)일 때만 작업 중 비활성화 등에 쓰이는
        단일 속성(self.prevent_word_split_check 등)에 연결한다.
        """
        if key == "reset_spacing":
            # 이 단계 자체가 곧 "자간 초기화 여부"라서 위 번호 체크박스 하나로
            # 충분하다(설명은 그 체크박스 옆 "예:" 문구로 이미 나옴). 별도 on/off를
            # 더 두면 같은 뜻의 체크박스가 중복된다.
            pass
        elif key == "body_spacing":
            체크 = ttk.Checkbutton(parent, text="줄 끝에서 단어가 끊기지 않게 정리하기", variable=self.prevent_word_split_var)
            체크.pack(anchor="w")
            ttk.Label(parent, text="04. 표·컨트롤 자간 조정에도 함께 적용됩니다.",
                      style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(0, 2))
            if 주설정탭:
                self.prevent_word_split_check = 체크
        elif key == "short_line":
            체크 = ttk.Checkbutton(parent, text="문장부호로 시작하는 문장의 짧은 줄 병합 사용", variable=self.punctuation_var)
            체크.pack(anchor="w")
            행 = ttk.Frame(parent)
            행.pack(anchor="w", fill="x", pady=(2, 0))
            ttk.Label(행, text="마지막 줄").pack(side="left")
            스핀 = ttk.Spinbox(행, from_=1, to=20, width=3, textvariable=self.punctuation_threshold_var, justify="center")
            스핀.pack(side="left", padx=(4, 4))
            ttk.Label(행, text="자 이하일 때 합쳐요 (05. 표·컨트롤 줄 병합에도 함께 적용)").pack(side="left")
            if 주설정탭:
                self.punctuation_check = 체크
                self.punctuation_threshold_spin = 스핀
        elif key == "control_spacing":
            체크 = ttk.Checkbutton(parent, text="표 서식 내 문장도 자간조정하기", variable=self.table_spacing_var)
            체크.pack(anchor="w")
            ttk.Label(parent, text="끄면 표(셀) 안의 문장은 04·05단계에서 제외됩니다. 기본값은 켜짐입니다.",
                      style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(0, 2))
            if 주설정탭:
                self.table_spacing_check = 체크

    def _서식정리_항목_상세(self, parent, key, *, 주설정탭):
        """'서식 정리'·'내어쓰기' 세부 설정 탭과 세부 작업 창이 함께 쓰는
        항목별 상세 위젯. _자간정리_항목_상세와 동일한 방식으로 동작한다.
        """
        def 준말창_열기():
            from docfit_core.abbreviation_dialog import open_abbreviation_dialog

            def 저장(등록표):
                설정 = 설정_불러오기()
                설정["abbreviations"] = 준말_등록표_정리(등록표)
                설정_저장(설정)
            def 기본_저장(사용):
                설정 = 설정_불러오기()
                설정["abbreviation_defaults"] = bool(사용)
                설정_저장(설정)
            open_abbreviation_dialog(parent.winfo_toplevel(), lambda: 설정_불러오기().get("abbreviations", {}), 저장,
                                     lambda: 설정_불러오기().get("abbreviation_defaults", True), 기본_저장)
        if key == "pre_format":
            title_auto = ttk.Checkbutton(parent, text="제목 모양 자동 정리 · 제목표가 있을 때",
                                          variable=self.std_bool_vars["std_title_auto"])
            title_auto.pack(anchor="w")
            ttk.Label(parent, text="문서 앞부분의 제목과 개요를 인식해 알맞은 모양을 적용합니다. 제목표가 없으면 건너뜁니다.",
                      style="Hint.TLabel", wraplength=610).pack(anchor="w")
            부제_행 = ttk.Frame(parent)
            부제_행.pack(anchor="w", padx=(18, 0), pady=(2, 0))
            ttk.Label(부제_행, text="제목 부제 크기 (제목 글의 첫 쉼표 앞 글):").pack(side="left")
            부제_스핀 = ttk.Spinbox(부제_행, from_=5, to=40, increment=1, width=4, justify="center",
                                   textvariable=self.std_parspace_vars["std_title_subtitle_pt"])
            부제_스핀.pack(side="left", padx=(4, 0))
            ttk.Label(부제_행, text="pt (기본 15)").pack(side="left", padx=(2, 0))
            ttk.Label(parent, text="'제목: 부제, 제목'처럼 쉼표가 있으면 쉼표 앞 글을 이 크기의 부제로 윗줄에 넣습니다. "
                                   "서식 프로필의 예시 제목 표를 쓰면 그 표의 크기를 따릅니다.",
                      style="Hint.TLabel", wraplength=610).pack(anchor="w", padx=(18, 0))
            담당자_행 = ttk.Frame(parent)
            담당자_행.pack(anchor="w", fill="x", padx=(18, 0), pady=(6, 0))
            ttk.Label(담당자_행, text="제목 표 담당자 칸(B2) 글:").pack(side="left")
            담당자_입력 = ttk.Entry(담당자_행, textvariable=self.title_owner_var, width=58)
            담당자_입력.pack(side="left", padx=(4, 0), fill="x", expand=True)
            ttk.Label(parent, text="준말(제목:)·라벨로 새로 만드는 제목 표의 담당자 칸(2행1열 표는 A2)에 이 글을 넣습니다. "
                                   "비우면 기본 글(○○과장/담당관 : ◎◎◎☎2133-0000 …)을 넣고, 문서에 이미 있는 제목 표는 바꾸지 않습니다.",
                      style="Hint.TLabel", wraplength=610).pack(anchor="w", padx=(18, 0))
            attachment_auto = ttk.Checkbutton(parent, text="붙임서식적용 (붙임 2종 자동 판별)",
                                               variable=self.std_bool_vars["std_attachment_auto"])
            attachment_auto.pack(anchor="w", pady=(6, 0))
            ttk.Label(parent, text="쪽 첫부분의 '붙임' 표를 1행3열/1행2열 구조로 판별하여 해당 기준서식을 적용.",
                      style="Hint.TLabel", wraplength=610).pack(anchor="w")
            midtitle_auto = ttk.Checkbutton(parent, text="중제목표 서식 적용 (Ⅰ·Ⅱ 번호 표)",
                                             variable=self.std_bool_vars["std_midtitle_auto"])
            midtitle_auto.pack(anchor="w", pady=(6, 0))
            ttk.Label(parent, text="로마자 번호 칸 뒤에 글이 오는 1행 표를 중제목으로 판별해 번호·글을 HY견고딕 20pt 서식으로 정리.",
                      style="Hint.TLabel", wraplength=610).pack(anchor="w")
            midtitle_bold = ttk.Checkbutton(parent, text="중제목 로마자 번호 굵게 (기본)",
                                             variable=self.std_bool_vars["std_midtitle_bold"])
            midtitle_bold.pack(anchor="w", padx=(18, 0))
            if 주설정탭:
                self.std_detail_checks += [title_auto, 부제_스핀, 담당자_입력, attachment_auto, midtitle_auto,
                                           midtitle_bold]
        elif key == "table_style":
            설정 = 설정_불러오기()
            서식 = 준말_표서식(준말_사용표_만들기(설정))
            ttk.Label(parent, text=("현재 기본 표 서식: " + 표서식_설명(서식)) if 서식 else
                      "준말 '표'가 없어 기본 표 서식을 쓰지 않습니다(아래 '표 머리글·본문 서식'을 씁니다).",
                      wraplength=610).pack(anchor="w")
            ttk.Button(parent, text="준말 등록·관리 (표 서식 학습)…", command=준말창_열기).pack(anchor="w", pady=(4, 0))
            ttk.Label(parent, text="준말 '표'의 본말에 담긴 예시 표처럼 문서의 일반 표(2행 2열 이상)에 칸 위치별 테두리·바탕색·"
                                   "글꼴·크기를 입힙니다. 제목·중제목·붙임 서식 표와 한 칸 상자는 두며, 문서의 '표:' 줄은 바꾸지 않습니다. "
                                   "준말 창의 '표 서식 학습…'으로 다른 예시 문서의 표를 배울 수 있습니다.",
                      style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(2, 0))
        elif key == "abbreviation":
            ttk.Button(parent, text="준말 등록·관리…", command=준말창_열기).pack(anchor="w")
            ttk.Label(parent, text="기본 준말(제목1:·제목2:·개요:·붙임:·로1 : …)은 등록하지 않아도 바뀝니다. 콜론 앞에 준말을 적은 줄만 바꾸며, "
                                   "쪽 범위 작업에서는 건너뜁니다. 끄려면 이 단계의 체크를 해제하세요.",
                      style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(2, 0))
        elif key == "precise_table":
            profile_row = ttk.Frame(parent)
            profile_row.pack(anchor="w", fill="x")
            ttk.Label(profile_row, text="문서 스타일(계층구조)").pack(side="left")
            콤보 = ttk.Combobox(profile_row, state="readonly", width=24)
            콤보.pack(side="left", padx=6)
            콤보.bind("<<ComboboxSelected>>", self._프로파일_선택)
            복사버튼 = ttk.Button(profile_row, text="서식 복사하기…", command=self._서식_복사하기)
            복사버튼.pack(side="left")
            ttk.Button(profile_row, text="편집하여 추가…", command=self._서식_예시편집_시작).pack(side="left", padx=(6, 0))
            ttk.Button(profile_row, text="이름 바꾸기…", command=self._서식_이름바꾸기).pack(side="left", padx=(6, 0))
            수정버튼 = ttk.Button(profile_row, text="상세 수정…", command=self._서식_수정하기)
            수정버튼.pack(side="left", padx=(6, 0))
            삭제버튼 = ttk.Button(profile_row, text="삭제", command=self._서식_삭제하기)
            삭제버튼.pack(side="left", padx=(6, 0))
            삭제버튼.config(state="normal" if self._활성_서식_프로파일 else "disabled")
            ttk.Label(parent, text="예시 문서를 복사하면 항목기호 문장의 계층별 서식과 제목·개요·중제목·붙임 표의 칸별(A1·A2·B2 …) "
                                   "글자·문단·테두리·배경 값을 모두 분석해 대표값을 정합니다. 이름과 세부값은 ‘상세 수정…’에서 고칩니다.",
                      style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(2, 0))
            if 주설정탭:
                self.profile_combo = 콤보
                self.copy_format_button = 복사버튼
                self.edit_format_button = 수정버튼
                self.delete_format_button = 삭제버튼
            else:
                self._팝업_profile_combo = 콤보
                if "_팝업_profile_combo" not in self._프로파일_콤보_이름목록:
                    self._프로파일_콤보_이름목록.append("_팝업_profile_combo")
            self._프로파일_목록갱신()
        elif key == "standard_format":
            stdformat_check = ttk.Checkbutton(
                parent, text="서식 옵션 사용 · 아래에서 바꿀 항목을 선택하세요", variable=self.stdformat_var)
            stdformat_check.pack(anchor="w")
            self.stdformat_var.set(True)  # 실행 모드가 서식 적용 여부를 결정하므로 중복된 전체 토글은 숨긴다.

            std_detail = ttk.Frame(parent)
            std_detail.pack(anchor="w", fill="x", pady=(4, 0))
            기본항목_행 = ttk.Frame(std_detail)
            기본항목_행.pack(anchor="w", fill="x")
            기본항목_체크들 = []
            for 문구, 설정_키, 여백 in [("편집 여백", "std_margin", 0), ("글자 가로폭", "std_ratio", 10), ("줄 사이 간격", "std_linespacing", 10)]:
                체크 = ttk.Checkbutton(기본항목_행, text=문구, variable=self.std_bool_vars[설정_키])
                체크.pack(side="left", padx=(여백, 0))
                기본항목_체크들.append(체크)

            문단위간격_체크 = ttk.Checkbutton(std_detail, text="항목 사이 간격 맞추기 · 문단 위 여백", variable=self.std_bool_vars["std_parspace"])
            문단위간격_체크.pack(anchor="w", pady=(8, 0))

            문단위간격_행 = ttk.Frame(std_detail)
            문단위간격_행.pack(anchor="w", fill="x", padx=(18, 0), pady=(2, 0))
            문단위간격_스핀들 = []
            for 라벨, 설정_키 in [("장", "std_parspace_chapter"), ("중제목 Ⅰ", "std_parspace_midtitle"),
                                ("□", "std_parspace_box"), ("ㅇ·○·☞", "std_parspace_circle"), ("-", "std_parspace_dash"),
                                ("*·※·→", "std_parspace_note")]:
                ttk.Label(문단위간격_행, text=f"{라벨}:").pack(side="left", padx=(0 if 라벨 == "장" else 10, 0))
                스핀 = ttk.Spinbox(문단위간격_행, from_=0, to=99, width=3, textvariable=self.std_parspace_vars[설정_키], justify="center")
                스핀.pack(side="left", padx=(4, 0))
                ttk.Label(문단위간격_행, text="pt").pack(side="left", padx=(2, 0))
                문단위간격_스핀들.append(스핀)
            ttk.Label(문단위간격_행, text="깊은 항목에서 복귀할 때:").pack(side="left", padx=(12, 0))
            복귀배율_스핀 = ttk.Spinbox(
                문단위간격_행, from_=100, to=400, increment=10, width=4,
                textvariable=self.std_parspace_vars["std_parspace_return_percent"], justify="center")
            복귀배율_스핀.pack(side="left", padx=(4, 0))
            ttk.Label(문단위간격_행, text="% (100% = 기존 간격)").pack(side="left", padx=(2, 0))
            문단위간격_스핀들.append(복귀배율_스핀)

            빈줄삭제_체크 = ttk.Checkbutton(
                std_detail, text="항목기호 문장 사이·문서 끝 빈 줄 삭제 (빈 줄로 띄운 간격은 문단 위 여백으로 대신하고, 문서 끝 빈 줄로 생기는 빈 쪽을 없앰)",
                variable=self.std_bool_vars["std_remove_blank_lines"])
            빈줄삭제_체크.pack(anchor="w", pady=(6, 0))

            if 주설정탭:
                self.stdformat_check = stdformat_check
                self.std_detail_checks += 기본항목_체크들 + [문단위간격_체크, 빈줄삭제_체크]
                self.std_parspace_spins = 문단위간격_스핀들
        elif key == "parenthesis":
            기호_체크 = ttk.Checkbutton(parent, text="기호별 글꼴·크기·시작 위치 맞추기 (□ / ㅇ / - / ※ / •; 점 계열은 •로 통일)",
                                      variable=self.std_bool_vars["std_symbols"])
            기호_체크.pack(anchor="w")

            기호_굵게_행 = ttk.Frame(parent)
            기호_굵게_행.pack(anchor="w", fill="x", pady=(2, 0))
            ttk.Label(기호_굵게_행, text="굵게:").pack(side="left")
            기호_굵게_체크들 = []
            for 기호_텍스트, 설정_키 in [("□", "std_symbol_box_bold"), ("ㅇ", "std_symbol_o_bold"), ("-", "std_symbol_dash_bold"), ("※", "std_symbol_note_bold")]:
                체크 = ttk.Checkbutton(기호_굵게_행, text=기호_텍스트, variable=self.std_bool_vars[설정_키])
                체크.pack(side="left", padx=(6, 0))
                기호_굵게_체크들.append(체크)

            기호글꼴_틀 = ttk.LabelFrame(parent, text="문장기호별 글꼴 · 크기", padding=8)
            기호글꼴_틀.pack(anchor="w", fill="x", pady=(6, 0))

            폰트폴더_행 = ttk.Frame(기호글꼴_틀)
            폰트폴더_행.pack(anchor="w", fill="x", pady=(0, 6))
            ttk.Label(폰트폴더_행, text="글꼴 폴더").pack(side="left")
            폰트폴더_입력 = ttk.Entry(폰트폴더_행, textvariable=self.font_folder_var, width=40)
            폰트폴더_입력.pack(side="left", padx=(6, 4))
            ttk.Button(폰트폴더_행, text="찾아보기…", command=self._폰트폴더_찾아보기).pack(side="left", padx=(0, 4))
            ttk.Button(폰트폴더_행, text="새로고침", command=self._폰트목록_새로고침).pack(side="left")

            ttk.Label(
                기호글꼴_틀,
                text="기본은 윈도우 글꼴 폴더(C:\\Windows\\Fonts)이며, 이 폴더에서 글꼴 목록을 불러옵니다. "
                     "한컴오피스 전용 번들(HFT) 글꼴은 설치 경로에서 자동으로 찾아 목록에 함께 더합니다. "
                     "목록에 없는 이름도 직접 입력할 수 있습니다.",
                style="Hint.TLabel", wraplength=520
            ).pack(anchor="w", pady=(0, 6))

            글꼴_콤보들, 크기_스핀들 = {}, {}
            for 기호 in 문장기호_목록:
                행 = ttk.Frame(기호글꼴_틀)
                행.pack(anchor="w", fill="x", pady=(2, 0))
                ttk.Label(행, text=기호, width=3).pack(side="left")
                콤보 = ttk.Combobox(
                    행, textvariable=self.symbol_font_vars[기호]["font"],
                    values=self._한글_폰트_목록_캐시, width=22
                )
                콤보.pack(side="left", padx=(4, 8))
                self._휠_콤보박스_바인딩(콤보)
                글꼴_콤보들[기호] = 콤보
                ttk.Label(행, text="크기").pack(side="left")
                크기스핀 = ttk.Spinbox(
                    행, from_=1, to=200, width=4, justify="center",
                    textvariable=self.symbol_font_vars[기호]["size"]
                )
                크기스핀.pack(side="left", padx=(4, 2))
                ttk.Label(행, text="pt").pack(side="left")
                크기_스핀들[기호] = 크기스핀

            표글꼴_틀 = ttk.LabelFrame(parent, text="표 안 글꼴 · 크기", padding=8)
            표글꼴_틀.pack(anchor="w", fill="x", pady=(6, 0))
            ttk.Label(
                표글꼴_틀,
                text="'표 머리글·본문 서식' 작업에서 표의 첫 행(머리글)과 나머지 행(본문)에 적용합니다. "
                     "한 칸짜리 표(제목·개요 상자)는 바꾸지 않습니다.",
                style="Hint.TLabel", wraplength=520
            ).pack(anchor="w", pady=(0, 4))
            for part, 이름 in (("header", "머리글"), ("body", "본문")):
                행 = ttk.Frame(표글꼴_틀)
                행.pack(anchor="w", fill="x", pady=(2, 0))
                ttk.Label(행, text=이름, width=6).pack(side="left")
                콤보 = ttk.Combobox(
                    행, textvariable=self.table_font_vars[part]["font"],
                    values=self._한글_폰트_목록_캐시, width=22
                )
                콤보.pack(side="left", padx=(4, 8))
                self._휠_콤보박스_바인딩(콤보)
                # 글꼴 목록 새로고침이 문장기호 글꼴 상자와 함께 갱신하도록 같이 보관한다.
                글꼴_콤보들[f"표_{part}"] = 콤보
                ttk.Label(행, text="크기").pack(side="left")
                크기스핀 = ttk.Spinbox(
                    행, from_=1, to=200, width=4, justify="center",
                    textvariable=self.table_font_vars[part]["size"]
                )
                크기스핀.pack(side="left", padx=(4, 2))
                ttk.Label(행, text="pt").pack(side="left")
                크기_스핀들[f"표_{part}"] = 크기스핀

            paren_shrink_check = ttk.Checkbutton(
                parent,
                text="괄호 안 부연설명 글자 크기 축소\n(문장 중간·끝에 오는 괄호 안 글자를 2pt 작게 표시)",
                variable=self.paren_shrink_var,
            )
            paren_shrink_check.pack(anchor="w", pady=(10, 0))

            label_bold_frame = ttk.LabelFrame(parent, text="항목 이름 강조", padding=10)
            label_bold_frame.pack(fill="x", pady=(10, 0))
            paren_label_bold_check = ttk.Checkbutton(
                label_bold_frame,
                text="문두 라벨(괄호 및 콜론 라벨) 굵게\n(\"ㅇ (운영방식)\"의 괄호 또는 \"- 추진부서 :\"처럼 문장부호 뒤 콜론 앞 텍스트 굵게)",
                variable=self.paren_label_bold_var,
            )
            paren_label_bold_check.pack(anchor="w")
            symbol_frame = ttk.LabelFrame(label_bold_frame, text='↳ 강조할 기호 선택', padding=6)
            symbol_frame.pack(fill='x', pady=(6, 0))
            label_symbol_checks = []
            for index, (skey, svar) in enumerate(self.label_symbol_vars.items()):
                check = ttk.Checkbutton(symbol_frame, text=skey, variable=svar)
                check.grid(row=index // 8, column=index % 8, sticky='w', padx=4)
                label_symbol_checks.append(check)
            # 문두 라벨 굵게가 켜져 있을 때만 의미가 있으므로 기호 선택과 같이
            # 활성/비활성된다.
            consistency_check = ttk.Checkbutton(
                label_bold_frame,
                text="항목기호별 굵게 일관성 적용\n(같은 기호의 라벨이 굵게 되면 \"- 조례제정 (설명)\"의 \"조례제정\"처럼 "
                     "다른 문단 머리말도 굵게 맞춤, 괄호 설명은 제외)",
                variable=self.std_bool_vars["std_marker_bold_consistency"],
            )
            consistency_check.pack(anchor="w", pady=(6, 0))
            label_symbol_checks.append(consistency_check)

            if 주설정탭:
                self.std_detail_checks += [기호_체크] + 기호_굵게_체크들
                self.symbol_font_combos = 글꼴_콤보들
                self.symbol_size_spins = 크기_스핀들
                self.font_folder_entry = 폰트폴더_입력
                self.paren_shrink_check = paren_shrink_check
                self.paren_label_bold_check = paren_label_bold_check
                self.label_symbol_checks = label_symbol_checks
        elif key == "supplement_indent":
            체크 = ttk.Checkbutton(
                parent,
                text="부연설명 문단 전체를 위 문단에 맞추기\n*, **, ※의 시작 위치를 위 문단의 본문 첫 글자 아래로 옮깁니다.\n‘내어쓰기’는 같은 문단의 둘째 줄 이후만 맞추므로 역할이 다릅니다.",
                variable=self.std_bool_vars["std_supplement_indent"])
            체크.pack(anchor="w")
            if 주설정탭:
                self.std_detail_checks.append(체크)
        elif key == "table_format":
            체크 = ttk.Checkbutton(
                parent,
                text="표 헤더/본문 서식적용\n(1행: 한컴돋움 13pt 굵게 / 나머지 행: 휴먼명조 12pt)",
                variable=self.std_bool_vars["std_table_header"],
            )
            체크.pack(anchor="w")
            if 주설정탭:
                self.std_detail_checks.append(체크)
        elif key == "hanging_indent":
            체크 = ttk.Checkbutton(parent, text="내어쓰기 · 둘째 줄부터 본문 시작 위치에 맞추기",
                                  variable=self.std_bool_vars["std_hanging_indent"])
            체크.pack(anchor="w")
            ttk.Label(parent, text="예: ㅇ (개요) 본문 → 다음 줄은 ‘본문’ 아래부터 시작\n기호별 글꼴 옵션을 켜지 않아도 적용됩니다.",
                      style="Hint.TLabel", wraplength=610).pack(anchor="w", pady=(1, 0))
            if 주설정탭:
                self.std_detail_checks.append(체크)

    def _세부작업_열기(self, mode, save_default=None):
        titles = {"spacing": "자간 정리", "unify": "서식 통일", "format": "한 번에 적용(자간 조정 제외)",
                  "all": "한 번에 적용"}
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{titles[mode]} · 세부 작업")
        dialog.geometry({"spacing": "520x650", "unify": "520x320"}.get(mode, "720x700"))
        dialog.transient(self.root)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="실행 순서대로 표시합니다. 체크를 끄면 해당 단계는 건너뜁니다.\n"
                              "기존 설정에서 꺼진 기능은 여기서 켜도 실행되지 않습니다. 아래 상세 항목은 "
                              "세부 설정 창의 내용과 같은 값을 그대로 공유합니다.",
                  style="Hint.TLabel", wraplength=680).pack(anchor="w", pady=(0, 8))
        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        content = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window, width=event.width))
        choices = {key: tk.BooleanVar(value=self.stage_choices[mode][key])
                   for key, _ in stages_for_mode(mode)}
        for number, (key, label) in enumerate(stages_for_mode(mode), 1):
            item = ttk.Frame(content)
            item.pack(fill="x", pady=(4, 7))
            ttk.Checkbutton(item, text=f"{number:02d}. {label}", style="Stage.TCheckbutton",
                            variable=choices[key]).pack(anchor="w")
            ttk.Label(item, text=STAGE_EXAMPLES[key], style="Hint.TLabel",
                      wraplength=610, justify="left").pack(anchor="w", padx=(25, 0), pady=(1, 0))
            detail = ttk.Frame(item)
            detail.pack(anchor="w", padx=(25, 0), pady=(4, 0), fill="x")
            self._자간정리_항목_상세(detail, key, 주설정탭=False)
            self._서식정리_항목_상세(detail, key, 주설정탭=False)

        기본저장_var = tk.BooleanVar(value=(
            self._세부작업_기본저장.get(mode, True) if save_default is None else bool(save_default)
        ))

        def cleanup():
            if "_팝업_profile_combo" in self._프로파일_콤보_이름목록:
                self._프로파일_콤보_이름목록.remove("_팝업_profile_combo")
            if hasattr(self, "_팝업_profile_combo"):
                del self._팝업_profile_combo

        def close():
            cleanup()
            dialog.destroy()

        def save():
            self.stage_choices[mode] = {key: variable.get() for key, variable in choices.items()}
            self._세부작업_기본저장[mode] = bool(기본저장_var.get())
            if 기본저장_var.get():
                self._세부작업_기본값_저장(mode)
            self._세부작업_옵션_맞춤(mode)   # 관련 작업을 바꿨으면 카드 옵션(표 제외 등)도 맞춘다
            self._요약갱신()
            close()
        buttons = ttk.Frame(dialog, padding=(14, 4, 14, 12))
        buttons.pack(fill="x")
        ttk.Checkbutton(buttons, text="이 구성 다음에도 기본값으로 사용",
                        variable=기본저장_var).pack(side="left")
        ttk.Button(buttons, text="취소", command=close).pack(side="right")
        ttk.Button(buttons, text="적용", command=save).pack(side="right", padx=8)
        dialog.protocol("WM_DELETE_WINDOW", close)

    def _세부작업_기본값_저장(self, mode, 저장=True):
        """작업 유형의 세부 작업 구성을 다음 실행에도 쓰도록 저장한다. 저장=False면 저장값을 지운다."""
        self._세부작업_기본저장[mode] = bool(저장)
        저장값 = 설정_불러오기()
        저장된_세부작업 = 저장값.get("stage_choices", {})
        if not isinstance(저장된_세부작업, dict):
            저장된_세부작업 = {}
        if 저장:
            저장된_세부작업[mode] = dict(self.stage_choices[mode])
        elif mode in 저장된_세부작업:
            del 저장된_세부작업[mode]
        else:
            return
        저장값["stage_choices"] = 저장된_세부작업
        설정_저장(저장값)

    def _요약갱신(self, *args):
        # 세부 작업 창·설정창·웹 화면에서 바꾼 '01 문서 전체 자간 초기화'를 카드의 '기존 자간 초기화'에도 맞춘다.
        초기화 = bool(self.stage_choices["spacing"].get("reset_spacing", True))
        if hasattr(self, "reset_spacing_var") and bool(self.reset_spacing_var.get()) != 초기화:
            self.reset_spacing_var.set(초기화)
        if not hasattr(self, "options_summary"):
            return
        mode = self.selected_mode.get()
        if mode == "spacing":
            summary = ("줄 끝의 끊긴 단어와 자간을 정리합니다." if 초기화
                       else "기존 자간을 초기화하지 않고 그 위에서 줄 끝의 끊긴 단어를 정리합니다.")
            if hasattr(self, "table_spacing_var") and not self.table_spacing_var.get():
                summary += " · 표 제외"
        elif mode == "unify":
            summary = "항목기호별로 문서에서 많이 쓰인 서식을 적용합니다."
            for 이름, 문구 in (("unify_exclude_tables_var", "표 제외"), ("unify_exclude_spacing_var", "자간 정리 제외"),
                             ("unify_exclude_pagefit_var", "페이지 맞춤 제외"),
                             ("unify_keep_layout_var", "원본 쪽 구성 유지")):
                if hasattr(self, 이름) and getattr(self, 이름).get():
                    summary += f" · {문구}"
        elif mode == "format":
            summary = "자간 조정 제외: 기존 자간은 그대로 두고 공문서 서식만 적용합니다."
        else:
            summary = "공문서 서식을 입히고 자간까지 함께 정리합니다."
        if mode in ("all", "format") and hasattr(self, "exclude_tables_var") and self.exclude_tables_var.get():
            summary += " · 표 제외"
        if mode in ("all", "format") and hasattr(self, "all_exclude_pagefit_var") and self.all_exclude_pagefit_var.get():
            summary += " · 페이지 맞춤 제외"
        choices = self.stage_choices[mode]
        # 카드 옵션으로 끈 작업(자간 정리의 자간 초기화, 표 제외·페이지 맞춤 제외 등)은 위 문구로 이미 알린다.
        카드로_끈작업 = 카드옵션_끈작업(self._카드옵션값_목록(), mode)
        disabled = sum(not value for key, value in choices.items()
                       if stage_default(key) and key not in 카드로_끈작업)
        if choices.get("style_unify") and mode != "unify":
            summary += " · 서식 통일 포함"
        if disabled:
            summary += f" · 세부 작업 {disabled}개 제외"
        self.options_summary.configure(text=summary)

    def _범위_상태_갱신(self, *args):
        """'쪽 지정'일 때만 시작·끝 쪽 입력칸을 켠다(작업 중에는 항상 끔)."""
        상태 = "normal" if (self.range_mode_var.get() == "pages" and not self.running) else "disabled"
        for 위젯 in (self.range_start_spin, self.range_end_spin):
            위젯.config(state=상태)

    def _쪽범위_토글(self):
        """기본 화면에는 문서 전체만 표시하고, 요청 시에만 쪽 입력을 펼친다."""
        지정 = bool(self.page_range_var.get())
        self.range_mode_var.set("pages" if 지정 else "all")
        if 지정:
            self.page_range_details.pack(side="left", fill="x", expand=True)
        elif self.page_range_details.winfo_manager() == "pack":
            self.page_range_details.pack_forget()
        self._범위_상태_갱신()

    # ---- 사용 순서 안내(테두리 강조) ----------------------------------
    def _안내_설정(self, 단계):
        """1=문서 추가, 2=작업 선택, 3=실행, 0=안내 없음. 지금 할 차례인 영역의 테두리를 강조한다."""
        self._안내단계 = 단계
        self.file_frame.configure(style="Guide.TLabelframe" if 단계 == 1 else "TLabelframe")
        self.choose_frame.configure(style="Guide.TLabelframe" if 단계 == 2 else "TLabelframe")
        self.start_wrap.configure(bg=UI_COLORS["teal"] if 단계 == 3 else UI_COLORS["bg"])
        labels = {1: "1 / 3  문서 선택", 2: "2 / 3  방식 선택", 3: "3 / 3  실행 준비", 0: "새 작업"}
        self.header_status.configure(text=labels.get(단계, "새 작업"))

    def _모드카드_외관갱신(self, *args):
        """선택한 처리 방식만 분명하게 드러낸다.

        라디오 버튼의 작은 표시만으로 선택 상태를 전달하지 않고 카드 테두리와
        배경을 함께 바꾼다. 키보드로 선택해도 같은 피드백을 받는다.
        """
        selected = self._카드키(self.selected_mode.get())
        if hasattr(self, "card_mode_var") and self.card_mode_var.get() != selected:
            self.card_mode_var.set(selected)
        for mode, (card, inner, description) in getattr(self, "mode_cards", {}).items():
            active = mode == selected
            border = UI_COLORS["teal"] if active else UI_COLORS["separator"]
            surface = UI_COLORS["teal_tint"] if active else UI_COLORS["surface"]
            card.configure(bg=border)
            inner.configure(bg=surface)
            description.configure(bg=surface)
            for check in getattr(self, "card_option_checks", {}).get(mode, ()):
                check.configure(bg=surface, activebackground=surface)

    def _메인_크기조정(self, event=None):
        """창 크기가 바뀔 때 UI 밀도를 폭에 맞춰 조정한다."""
        if event is not None and getattr(event, "widget", self.root) is not self.root:
            return
        예약 = getattr(self, "_반응형_예약", None)
        if 예약 is not None:
            try:
                self.root.after_cancel(예약)
            except tk.TclError:
                pass
        self._반응형_예약 = self.root.after(120, self._반응형_배치)

    def _반응형_배치(self):
        self._반응형_예약 = None
        if not self.root.winfo_exists():
            return
        def 배치해제(widget):
            manager = widget.winfo_manager()
            if manager == "pack":
                widget.pack_forget()
            elif manager == "grid":
                widget.grid_forget()
        width, height = self.root.winfo_width(), self.root.winfo_height()
        scale = getattr(self, "_ui_scale", 1.0)
        cards = list(self.mode_cards.items())
        columns = 2 if width < 1000 * scale else len(cards)
        for index, (_mode, (card, _inner, _desc)) in enumerate(cards):
            card.grid_configure(row=1 + index // columns, column=index % columns,
                                sticky="nsew", padx=3, pady=3)
        rows = (len(cards) + columns - 1) // columns
        for column in range(4):
            self.choose_frame.grid_columnconfigure(column, weight=1 if column < columns else 0,
                                                   uniform="modes" if column < columns else "")
        for row in range(1, 5):
            self.choose_frame.grid_rowconfigure(row, weight=1 if row < 1 + rows else 0)
        self.quick_actions.grid_configure(row=1 + rows, column=0, columnspan=columns)
        self.format_quick.grid_configure(row=2 + rows, column=0, columnspan=columns)
        self.scope_frame.grid_configure(row=3 + rows, column=0, columnspan=columns)
        # 문서 버튼은 작은 창에서 줄바꿈 없이 노출되도록 2×2로 바꾼다.
        file_columns = 2 if width < 760 * scale else 4
        for button in self.file_buttons:
            배치해제(button)
        배치해제(self.file_count)
        for index, button in enumerate(self.file_buttons):
            button.grid(row=index // file_columns, column=index % file_columns,
                        sticky="ew", padx=(0, 6), pady=2)
        for column in range(4):
            self.file_actions.grid_columnconfigure(column, weight=1 if column < file_columns else 0)
        self.file_count.grid(row=(len(self.file_buttons) + file_columns - 1) // file_columns,
                             column=0, columnspan=file_columns, sticky="e")
        compact = width < 760 * scale
        배치해제(self.tools_button)
        # 문서 도구 메뉴는 개발자 모드에서만 보인다.
        quick_widgets = ((self.tools_button,) if self.developer_mode_var.get() else ()) + (
            self.stage_details_button, self.settings_button)
        for widget in quick_widgets:
            배치해제(widget)
        배치해제(self.options_summary)
        if compact:
            for index, widget in enumerate(quick_widgets):
                widget.grid(row=0, column=index, sticky="ew", padx=(0, 4), pady=2)
                self.options_summary.grid(row=1, column=0, columnspan=len(quick_widgets), sticky="w")
        else:
            for widget in quick_widgets:
                widget.pack(side="right", padx=(0, 6))
            self.options_summary.pack(side="left", fill="x", expand=True)
        wrap = max(360, width - round(80 * scale))
        for widget in (getattr(self, "options_summary", None), getattr(self, "footer_note", None)):
            if widget is not None:
                widget.configure(wraplength=wrap)

    def _모드_선택됨(self):
        """작업 종류를 고르면(이미 선택된 것을 다시 눌러도) 다음 차례인 '실행'을 안내한다."""
        self._요약갱신()
        if self._안내단계 == 2 and not self.running:
            self._안내_설정(3)

    @staticmethod
    def _카드키(mode):
        """내부 작업 유형이 놓이는 카드. 서식 적용(format)은 '한 번에 적용'에서 자간 조정을 뺀 것이다."""
        return "all" if mode == "format" else mode

    def _한번에_모드(self):
        """'한 번에 적용' 카드의 내부 작업 유형: 자간 조정 포함이면 all, 아니면 format."""
        return "all" if self.include_spacing_var.get() else "format"

    # 작업 카드 옵션(stage_selection.CARD_OPTION_STAGES 키) → (화면 변수, 변수가 옵션의 반대 값인가).
    # 자간 정리의 '표 제외'는 설정 table_spacing(표 안 문장 자간조정)의 반대 값이다.
    _카드옵션_변수 = {
        "spacing_reset_existing": ("reset_spacing_var", False),
        "spacing_exclude_tables": ("table_spacing_var", True),
        "unify_exclude_tables": ("unify_exclude_tables_var", False),
        "unify_exclude_spacing": ("unify_exclude_spacing_var", False),
        "unify_exclude_pagefit": ("unify_exclude_pagefit_var", False),
        "unify_keep_layout": ("unify_keep_layout_var", False),
        "all_include_spacing": ("include_spacing_var", False),
        "all_exclude_tables": ("exclude_tables_var", False),
        "all_exclude_pagefit": ("all_exclude_pagefit_var", False),
    }

    def _카드옵션값(self, 옵션):
        """카드 옵션 값(화면 변수가 아직 없으면 None)."""
        이름, 반대 = self._카드옵션_변수[옵션]
        변수 = getattr(self, 이름, None)
        return None if 변수 is None else bool(변수.get()) != 반대

    def _카드옵션값_목록(self):
        return {옵션: self._카드옵션값(옵션) for 옵션 in self._카드옵션_변수}

    def _세부작업_값_넣기(self, mode, 값들):
        """세부 작업 값을 바꾸고 바뀐 것이 있었는지 돌려준다."""
        선택 = self.stage_choices[mode]
        바뀜 = any(선택.get(key) != 값 for key, 값 in 값들.items())
        선택.update(값들)
        return 바뀜

    def _세부작업_연동_마무리(self, modes):
        """연동으로 바뀐 세부 작업 구성을 저장하고(기본값 저장을 켠 유형만) 설정창의 단계 체크에도 반영한다."""
        for mode in modes:
            if self._세부작업_기본저장.get(mode):
                self._세부작업_기본값_저장(mode)
        for 이름, mode in (("spacing_stage_vars", "spacing"), ("format_stage_vars", "format"),
                          ("indent_stage_vars", "format")):
            if mode not in modes:
                continue
            for key, var in getattr(self, 이름, {}).items():
                값 = bool(self.stage_choices[mode].get(key, True))
                if bool(var.get()) != 값:
                    var.set(값)

    def _카드옵션_세부작업_반영(self, 옵션):
        """카드 옵션을 바꾸면 그 카드의 세부 작업 가운데 관련 작업을 모두 같이 켜고 끈다(2026-10-04 사용자 요청).

        실행창 카드·웹 화면·설정창 어디서 바꿔도 같은 변수 감시로 반영한다. 세부 작업에 맞춰 옵션을 고치는
        중(_세부작업_옵션_맞춤)에는 사용자가 고른 세부 작업을 덮지 않도록 건너뛴다.
        """
        if getattr(self, "_카드옵션_맞추는중", False):
            return
        옵션값 = self._카드옵션값_목록()
        바뀐_유형 = [mode for mode in 카드옵션_세부작업[옵션][0]
                   if self._세부작업_값_넣기(mode, 카드옵션_세부작업값(옵션, 옵션값[옵션], 옵션값, mode))]
        self._세부작업_연동_마무리(바뀐_유형)

    def _세부작업_옵션_맞춤(self, mode):
        """세부 작업 구성에 맞게 그 카드의 옵션을 맞춘다(세부 작업 창·화면 목록·설정창에서 바꾼 뒤).

        '제외' 옵션은 관련 작업이 모두 꺼지면 켜지고 하나라도 켜면 꺼진다. 옵션이 관련 작업을 끄는 쪽으로 바뀌면
        같은 카드의 다른 구성(한 번에 적용의 자간 조정 포함 all·제외 format)에서도 관련 작업을 끈다. 한 번에 적용에서
        자간 작업을 모두 끄면 '자간 조정 포함'이 꺼지고 서식 적용(format)으로 바뀐다.
        """
        바뀐_옵션 = []
        self._카드옵션_맞추는중 = True
        try:
            for 옵션 in 카드옵션_세부작업:
                값, 현재 = 카드옵션_판정(옵션, self.stage_choices[mode], mode), self._카드옵션값(옵션)
                if 값 is None or 현재 is None or 값 == 현재:
                    continue
                이름, 반대 = self._카드옵션_변수[옵션]
                getattr(self, 이름).set(값 != 반대)
                바뀐_옵션.append(옵션)
        finally:
            self._카드옵션_맞추는중 = False
        옵션값 = self._카드옵션값_목록()
        바뀐_유형 = set()
        for 옵션 in 바뀐_옵션:
            if not 카드옵션_끄는값(옵션, 옵션값[옵션]):
                continue
            for 다른_유형 in 카드옵션_세부작업[옵션][0]:
                if 다른_유형 != mode and self._세부작업_값_넣기(
                        다른_유형, 카드옵션_세부작업값(옵션, 옵션값[옵션], 옵션값, 다른_유형)):
                    바뀐_유형.add(다른_유형)
        self._세부작업_연동_마무리(바뀐_유형)
        if "all_include_spacing" in 바뀐_옵션 and self.selected_mode.get() in ("all", "format"):
            self.selected_mode.set(self._한번에_모드())

    def _카드옵션_연동_시작(self):
        """카드 옵션과 세부 작업을 처음 맞추고 옵션 변수에 연동 감시를 건다(화면 변수를 모두 만든 뒤).

        켜 둔 '제외' 옵션은 저장된 세부 작업 구성보다 우선해 관련 작업을 끄고, 나머지 옵션은 세부 작업 구성을
        따른다(예: 서식 통일의 쪽 맞춤은 기본 꺼짐이라 '페이지 맞춤 제외'가 켜져 보인다). 감시는 기존 감시보다 나중에
        걸어 먼저 실행되므로, 요약 문구·설정 저장은 바뀐 세부 작업을 본다.
        """
        self._카드옵션_맞추는중 = False
        for 옵션, (_, _, 제외) in 카드옵션_세부작업.items():
            if 제외 and self._카드옵션값(옵션):
                self._카드옵션_세부작업_반영(옵션)
        for mode in ("spacing", "unify", self._한번에_모드()):
            self._세부작업_옵션_맞춤(mode)
        for 옵션, (이름, _) in self._카드옵션_변수.items():
            getattr(self, 이름).trace_add("write", lambda *_, 옵션=옵션: self._카드옵션_세부작업_반영(옵션))

    def _설정탭_세부작업_변경(self, mode, key, var):
        """설정창의 단계 체크를 세부 작업 구성에 반영하고, 바뀌었으면 카드 옵션도 맞춘다."""
        값 = bool(var.get())
        if self.stage_choices[mode].get(key) == 값:
            return
        self.stage_choices[mode][key] = 값
        self._세부작업_옵션_맞춤(mode)

    def _카드옵션_변경(self, mode):
        """카드 옵션 체크를 바꾸면 그 카드를 고른다(값 저장·요약은 변경 감시가 한다)."""
        if self.running:
            return
        self.selected_mode.set(self._한번에_모드() if mode in ("all", "format") else mode)
        self._모드_선택됨()

    def _표제외_변경(self):
        """'표 제외'를 바꾸면 '한 번에 적용' 카드를 고른다(값 저장·요약은 변경 감시가 한다)."""
        if self.running:
            return
        self.selected_mode.set(self._한번에_모드())
        self._모드_선택됨()

    def _카드_클릭(self, mode):
        if self.running:
            self._모드카드_외관갱신()
            return
        self.selected_mode.set(self._한번에_모드() if mode in ("all", "format") else mode)
        self._모드_선택됨()

    def _자간포함_변경(self):
        """'자간 조정 포함'을 바꾸면 '한 번에 적용' 카드를 고르고 내부 작업 유형을 맞춘다."""
        if self.running:
            return
        self.selected_mode.set(self._한번에_모드())
        self._모드_선택됨()

    def _자간초기화_값변경(self, *args):
        """'기존 자간 초기화' 값을 자간 정리 세부 작업 01에 반영하고 설정 파일에 저장한다."""
        self.stage_choices["spacing"]["reset_spacing"] = bool(self.reset_spacing_var.get())
        self._설정_변경됨()
        self._요약갱신()

    def _자간초기화_변경(self):
        """'기존 자간 초기화'·'표 내 자간 정리'를 바꾸면 '자간 정리' 카드를 고른다."""
        if self.running:
            return
        self.selected_mode.set("spacing")
        self._모드_선택됨()

    # ---- 문서·결과 열기 / 작업 결과 표시 ------------------------------
    def _경로_열기(self, path):
        """파일이나 폴더를 연결된 프로그램(탐색기·한글)으로 연다."""
        try:
            if hasattr(os, "startfile"):
                os.startfile(str(path))
            else:  # Windows가 아닌 환경(시험용)
                import subprocess
                subprocess.Popen(["xdg-open", str(path)])
            return True
        except Exception as e:
            messagebox.showerror(APP_NAME, f"열지 못했습니다.\n{path}\n\n{e}", parent=self.root)
            return False

    def _문서_열기(self, event):
        """'01 정리할 문서' 목록에서 파일을 더블클릭하면 그 문서를 연다."""
        if not self.files:
            return
        순번 = self.file_list.nearest(event.y)
        상자 = self.file_list.bbox(순번) if 0 <= 순번 < len(self.files) else None
        if not 상자 or not (상자[1] <= event.y <= 상자[1] + 상자[3]):
            return  # 항목이 없는 빈 곳을 더블클릭한 경우
        경로 = self.files[순번]
        if not os.path.isfile(경로):
            messagebox.showwarning(APP_NAME, f"파일을 찾을 수 없습니다.\n{경로}", parent=self.root)
            return
        self._경로_열기(경로)

    def _원본폴더_버튼_갱신(self):
        """'원본 폴더 열기'는 문서가 하나라도 추가되어 있으면 켜고, 목록이 비면 끈다."""
        self.open_folder_button.config(state="normal" if self.files else "disabled")

    def _원본폴더_열기(self):
        폴더들 = []
        원본들 = list(self.files) or [항목["원본"] for 항목 in self._결과목록]
        for 원본 in 원본들:
            폴더 = str(Path(원본).parent)
            if 폴더 not in 폴더들 and os.path.isdir(폴더):
                폴더들.append(폴더)
        if not 폴더들:
            messagebox.showwarning(APP_NAME, "원본 폴더를 찾을 수 없습니다.", parent=self.root)
            return
        if len(폴더들) > 3 and not messagebox.askyesno(APP_NAME, f"원본 폴더가 {len(폴더들)}곳입니다. 모두 여시겠습니까?", parent=self.root):
            return
        for 폴더 in 폴더들:
            self._경로_열기(폴더)

    def _결과파일_열기(self):
        파일들 = [항목["결과"] for 항목 in self._결과목록 if os.path.isfile(항목["결과"])]
        if not 파일들:
            messagebox.showwarning(APP_NAME, "결과 파일을 찾을 수 없습니다. 옮기거나 지우지 않았는지 확인해 주세요.", parent=self.root)
            return
        if len(파일들) > 1 and not messagebox.askyesno(APP_NAME, f"결과 파일 {len(파일들)}개를 모두 여시겠습니까?", parent=self.root):
            return
        for 파일 in 파일들:
            self._경로_열기(파일)

    def _결과_초기화(self, 결과목록도_지우기=True):
        """이전 작업 결과 표시(결과 버튼 비활성화·작업 결과 문구·절약 시간 메시지)를 되돌린다.

        결과목록도_지우기=False면 '재개 대기' 상태(중단된 작업을 실행 버튼으로
        이어서 진행하는 상태)의 완료 기록을 남겨 둔다.
        """
        if 결과목록도_지우기:
            self._결과목록 = []
            self._재개_대기중 = False
            self._재개_시작_인덱스 = 1
        self.open_result_button.config(state="disabled")
        self._원본폴더_버튼_갱신()      # 원본 폴더 버튼은 목록에 문서가 있으면 계속 켜 둔다.
        self.footer_note_var.set(self.FOOTER_NOTE_DEFAULT)
        self.footer_note.configure(style="Hint.TLabel")
        self._단계_초기화()

    def _작업결과_표시(self, 모두_성공):
        """작업이 끝난 뒤: 결과 버튼, '[작업 결과]' 문구, (모두 성공하면) 절약된 시간을 보여 준다."""
        if not self._결과목록:
            return
        self._원본폴더_버튼_갱신()
        self.open_result_button.config(state="normal")
        이름들 = [Path(항목["결과"]).name for 항목 in self._결과목록]
        문구 = 이름들[0] if len(이름들) == 1 else f"{이름들[0]} 외 {len(이름들) - 1}개"
        self.footer_note_var.set(f"[작업 결과] : {문구}")
        self.footer_note.configure(style="Result.TLabel")
        if 모두_성공:
            총쪽 = sum(항목["쪽수"] for 항목 in self._결과목록)
            수작업분 = 총쪽 * 절약시간_쪽당_분.get(self._작업모드, 5.0)
            걸린분 = (time.monotonic() - (self._작업시작시각 or time.monotonic())) / 60
            절약 = 절약시간_표시(수작업분 - 걸린분)
            self.stage_board.set_result_message(f"이번 작업을 통해 절약된 귀하의 시간은 총 {절약} 입니다.")

    # ---- 작업 범위(쪽 지정) ----------------------------------------
    @staticmethod
    def _쪽_표시(n):
        return "마지막쪽" if n == 0 else str(n)

    @staticmethod
    def _쪽_읽기(text):
        """'마지막쪽'·'0'은 0, 숫자는 그 값, 그 밖에는 None."""
        t = str(text).strip()
        if t in ("마지막쪽", "0"):
            return 0
        try:
            n = int(t)
        except ValueError:
            return None
        return n if n >= 1 else None

    @staticmethod
    def _쪽_목록(시작=1):
        """스핀박스 목록: '마지막쪽' 다음에 시작~999. 1의 아래 단계가 '마지막쪽'이다."""
        return ["마지막쪽"] + [str(i) for i in range(시작, max(시작, 999) + 1)]

    def _범위_끝_설정(self, n):
        """종료쪽을 프로그램이 바꾼다(사용자가 직접 바꾼 것으로 보지 않는다)."""
        self._범위_동기중 = True
        try:
            self.range_end_var.set(self._쪽_표시(n))
        finally:
            self._범위_동기중 = False

    def _범위_값목록_갱신(self):
        """종료쪽 선택 범위는 '시작쪽 ~ 마지막쪽'이다."""
        시작 = self._쪽_읽기(self.range_start_var.get())
        if 시작 is None:
            return
        self.range_end_spin.configure(values=["마지막쪽"] if 시작 == 0 else self._쪽_목록(시작))

    def _범위_시작_변경(self, *args):
        if self._범위_동기중:
            return
        시작 = self._쪽_읽기(self.range_start_var.get())
        if 시작 is None:
            return  # 입력 도중(빈 칸 등)에는 종료쪽을 건드리지 않는다.
        self._범위_값목록_갱신()
        끝 = self._쪽_읽기(self.range_end_var.get())
        if not self._범위_끝직접설정:
            self._범위_끝_설정(시작)            # 종료쪽 기본값 = 시작쪽
        elif 시작 == 0:
            self._범위_끝_설정(0)               # 시작이 마지막쪽이면 종료도 마지막쪽
        elif 끝 not in (None, 0) and 끝 < 시작:
            self._범위_끝_설정(시작)            # 종료쪽은 시작쪽보다 작을 수 없다.

    def _범위_끝_변경(self, *args):
        if not self._범위_동기중:
            self._범위_끝직접설정 = True        # 이후로는 사용자가 정한 값을 유지한다.

    def _작업범위_초기화(self):
        """작업 범위를 기본값(문서 전체, 시작쪽·종료쪽 1)으로 되돌린다."""
        self._범위_동기중 = True
        try:
            self.range_mode_var.set("all")
            self.page_range_var.set(False)
            self.range_start_var.set("1")
            self.range_end_var.set("1")
        finally:
            self._범위_동기중 = False
        self._범위_끝직접설정 = False
        if self.page_range_details.winfo_manager() == "pack":
            self.page_range_details.pack_forget()
        self._범위_값목록_갱신()
        self._범위_상태_갱신()

    def _작업범위_읽기(self):
        """실행할 때마다 작업 범위를 확인한다.

        반환: (성공 여부, 값). 값은 None=문서 전체, (시작쪽, 종료쪽)=쪽 지정이며 0은 '마지막쪽'이다.
        """
        if self.range_mode_var.get() != "pages":
            return True, None
        시작 = self._쪽_읽기(self.range_start_var.get())
        if 시작 is None:
            messagebox.showwarning(APP_NAME, "시작쪽은 ‘마지막쪽’ 또는 1 이상의 숫자로 입력해 주세요.", parent=self.root)
            return False, None
        끝_원문 = str(self.range_end_var.get()).strip()
        if not 끝_원문:
            끝 = 시작                           # 종료쪽 기본값은 시작쪽
        else:
            끝 = self._쪽_읽기(끝_원문)
            if 끝 is None:
                messagebox.showwarning(APP_NAME, "종료쪽은 ‘마지막쪽’ 또는 1 이상의 숫자로 입력해 주세요.", parent=self.root)
                return False, None
        if 시작 == 0 and 끝 != 0:
            messagebox.showwarning(APP_NAME, "시작쪽이 ‘마지막쪽’이면 종료쪽도 ‘마지막쪽’이어야 합니다.", parent=self.root)
            return False, None
        if 시작 != 0 and 끝 != 0 and 끝 < 시작:
            messagebox.showwarning(APP_NAME, "종료쪽은 시작쪽보다 작을 수 없습니다.", parent=self.root)
            return False, None
        # 화면 표시를 확인한 값으로 정리한다(예: 0 → 마지막쪽, 빈 칸 → 시작쪽).
        self._범위_동기중 = True
        try:
            self.range_start_var.set(self._쪽_표시(시작))
            self.range_end_var.set(self._쪽_표시(끝))
        finally:
            self._범위_동기중 = False
        return True, (시작, 끝)

    def _빠른설정(self, name):
        if self.running:
            return
        # 현재 체크 상태를 명시적으로 대체하는 사용자 선택 작업이다.
        self.stdformat_var.set(True)
        if name == "indent":
            for var in self.std_bool_vars.values():
                var.set(False)
            self.std_bool_vars["std_hanging_indent"].set(True)
            self.paren_shrink_var.set(False)
            self.paren_label_bold_var.set(False)
            self.keep_punctuation_set_var.set(False)
        else:
            for key, var in self.std_bool_vars.items():
                var.set(기본_설정[key])
            self.std_bool_vars["std_hanging_indent"].set(True)
            self.paren_shrink_var.set(True)
            self.paren_label_bold_var.set(True)
            self.keep_punctuation_set_var.set(True)
        self.selected_mode.set(self._한번에_모드())
        if self._안내단계 == 2:
            self._안내_설정(3)
        self._표준서식_하위옵션_상태_갱신()
        self._설정_변경됨()
        self.status_var.set("내어쓰기 옵션을 선택했어요. 설정창을 닫고 실행하세요." if name == "indent" else "보고서 기본 옵션을 선택했어요. 설정창을 닫고 실행하세요.")

    def _폴더선택(self):
        if self.running:
            return
        folder = askdirectory(parent=self.root, title="한글 문서가 있는 폴더 선택 (현재 폴더의 파일만 추가)")
        if folder:
            added = self.폴더추가(folder)
            self.status_var.set(f"{added}개 추가 · 총 {len(self.files)}개 문서")

    def _선택삭제(self):
        if self.running:
            return
        for index in reversed(self.file_list.curselection()):
            del self.files[index]
            self.file_list.delete(index)
        self.file_count.configure(text=f"{len(self.files)}개 문서")
        self._실행버튼_상태("normal" if self.files else "disabled")
        self._원본폴더_버튼_갱신()
        self._재개_대기중 = False     # 목록이 바뀌면 이전 중단 지점은 더 이상 유효하지 않음
        if not self.files:
            self._안내_설정(1)     # 목록이 비면 다시 문서 추가부터 안내

    def _기록토글(self):
        self._log_visible = not self._log_visible
        if self._log_visible:
            self.log_window.deiconify()
            self.log_window.lift()
        else:
            self.log_window.withdraw()
        self.log_toggle.configure(text="처리 기록 닫기" if self._log_visible else "▸ 처리 기록 보기")

    def _기록닫기(self):
        self._log_visible = False
        self.log_window.withdraw()
        self.log_toggle.configure(text="▸ 처리 기록 보기")

    def _프로파일_전역반영(self, profile):
        global 표준서식_설정
        global 표_헤더서식_헤더_폰트, 표_헤더서식_헤더_크기, 표_헤더서식_헤더_굵게
        global 표_헤더서식_본문_폰트, 표_헤더서식_본문_크기, 표_헤더서식_본문_굵게
        global 활성_정밀표_프로필, 활성_서식표_프로필, 활성_표서식_프로필
        서식_기본값_전역_복원()
        표준서식_설정 = copy.deepcopy(profile["format"])
        table = profile.get("table_format", {})
        표_헤더서식_헤더_폰트 = table.get("header_font", 표_헤더서식_헤더_폰트)
        표_헤더서식_헤더_크기 = table.get("header_size", 표_헤더서식_헤더_크기)
        표_헤더서식_헤더_굵게 = table.get("header_bold", 표_헤더서식_헤더_굵게)
        표_헤더서식_본문_폰트 = table.get("body_font", 표_헤더서식_본문_폰트)
        표_헤더서식_본문_크기 = table.get("body_size", 표_헤더서식_본문_크기)
        표_헤더서식_본문_굵게 = table.get("body_bold", 표_헤더서식_본문_굵게)
        활성_정밀표_프로필 = copy.deepcopy(profile.get("precise_tables"))
        활성_서식표_프로필 = copy.deepcopy(profile.get("form_tables")) or None
        활성_표서식_프로필 = copy.deepcopy(profile.get("table_style")) or None
        globals()["활성_머리서식_프로필"] = copy.deepcopy(profile.get("report_header")) or None
        global 괄호_축소_pt
        괄호_축소_pt = float(profile["format"].get("괄호_축소_pt", 2) or 2)
        글꼴형식_등록(profile["format"].get("글꼴형식"))

    def _프로파일_목록갱신(self):
        # 기본 서식을 맨 앞에 두고 기관별로 묶어 이름순으로 보인다(A3).
        ids = [k for k in self._프로파일들 if k]
        ids.sort(key=lambda k: (str(self._프로파일들[k].get("organization") or "￿"), self._프로파일들[k]["name"]))
        self._프로파일_ids = ([""] if "" in self._프로파일들 else []) + ids
        이름들 = [서식프로파일_표시이름(self._프로파일들[k]) for k in self._프로파일_ids]
        현재 = self._프로파일_ids.index(self._활성_서식_프로파일)
        for 콤보이름 in self._프로파일_콤보_이름목록:
            콤보 = getattr(self, 콤보이름, None)
            if 콤보 is not None:
                콤보["values"] = 이름들
                콤보.current(현재)
        삭제버튼 = getattr(self, "delete_format_button", None)
        if 삭제버튼 is not None:
            삭제버튼.config(state="normal" if self._활성_서식_프로파일 else "disabled")
        수정버튼 = getattr(self, "edit_format_button", None)
        if 수정버튼 is not None:
            수정버튼.config(state="normal")

    def _프로파일_선택(self, event=None):
        if self.running: return
        콤보 = event.widget if event is not None and isinstance(event.widget, ttk.Combobox) else self.profile_combo
        self._활성_서식_프로파일 = self._프로파일_ids[콤보.current()]
        profile = self._프로파일들[self._활성_서식_프로파일]
        self._프로파일_전역반영(profile)
        options = profile["options"]
        for key, var in {**self.std_bool_vars, **self.std_parspace_vars}.items():
            var.set(options.get(key, 기본_설정[key]))
        self.paren_shrink_var.set(options.get("paren_shrink", True))
        self.paren_label_bold_var.set(options.get("paren_label_bold", True))
        for symbol, values in options.get("symbol_fonts", {}).items():
            if symbol in self.symbol_font_vars:
                self.symbol_font_vars[symbol]["font"].set(str(values.get("font", "")))
                self.symbol_font_vars[symbol]["size"].set(str(values.get("size", "")))
        self.table_font_vars["header"]["font"].set(str(표_헤더서식_헤더_폰트))
        self.table_font_vars["header"]["size"].set(str(표_헤더서식_헤더_크기))
        self.table_font_vars["body"]["font"].set(str(표_헤더서식_본문_폰트))
        self.table_font_vars["body"]["size"].set(str(표_헤더서식_본문_크기))
        for key, var in self.label_symbol_vars.items():
            var.set(options.get("label_symbols", 기본_설정["label_symbols"]).get(key, True))
        self._설정_변경됨()
        self._프로파일_목록갱신()
        self._표준서식_하위옵션_상태_갱신()
        삭제버튼 = getattr(self, "delete_format_button", None)
        if 삭제버튼 is not None:
            삭제버튼.config(state="normal" if self._활성_서식_프로파일 else "disabled")

    def _서식_이름바꾸기(self):
        """저장된 서식의 이름을 언제든 바꾼다(TODO 6순위). 기본 서식은 바꾸지 않는다."""
        if self.running:
            return
        parent = self.settings_toplevel if self.settings_toplevel and self.settings_toplevel.winfo_viewable() else self.root
        identifier = self._활성_서식_프로파일
        if not identifier:
            messagebox.showinfo(APP_NAME, "기본 문서 서식은 이름을 바꿀 수 없습니다.", parent=parent)
            return
        profile = self._프로파일들[identifier]
        새이름 = simpledialog.askstring(APP_NAME, "서식 이름", parent=parent, initialvalue=profile["name"])
        if 새이름 is None:
            return
        새이름 = 새이름.strip()
        if not 새이름:
            messagebox.showwarning(APP_NAME, "비어 있지 않은 이름을 입력해 주세요.", parent=parent)
            return
        if any(p["name"] == 새이름 for k, p in self._프로파일들.items() if k != identifier):
            messagebox.showwarning(APP_NAME, "이미 사용 중인 서식 이름입니다.", parent=parent)
            return
        새기관 = simpledialog.askstring(APP_NAME, "기관 이름(선택, 비워 두면 기관 없음)", parent=parent,
                                      initialvalue=str(profile.get("organization") or ""))
        if 새기관 is None:
            return
        오류 = self._서식_이름_저장(identifier, 새이름, 새기관)
        if 오류:
            messagebox.showerror(APP_NAME, 오류, parent=parent)

    def _웹화면_모드(self):
        """웹 화면(WebView)이 주 화면이라 Tk 기본 창이 숨겨져 있는지."""
        try:
            return self.root.state() == "withdrawn"
        except tk.TclError:
            return False

    def _서식창_부모(self):
        """서식 관리 대화상자의 부모 창: 열린 설정창, 없으면 기본 창."""
        if self.settings_toplevel and self.settings_toplevel.winfo_exists() and self.settings_toplevel.winfo_viewable():
            return self.settings_toplevel
        return self.root

    def _서식_파일_저장(self, identifier, profile):
        folder = 서식프로파일_폴더()
        folder.mkdir(parents=True, exist_ok=True)
        temp = folder / (identifier + ".tmp")
        temp.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, folder / (identifier + ".json"))

    def _서식_이름_저장(self, identifier, 이름, 기관=""):
        """서식 이름(과 기관)을 바꿔 저장한다. 성공하면 None, 아니면 사용자에게 보일 오류 문구."""
        if self.running:
            return "작업 중에는 서식을 바꿀 수 없습니다."
        if not identifier or identifier not in self._프로파일들:
            return "기본 문서 서식은 이름을 바꿀 수 없습니다."
        이름, 기관 = str(이름 or "").strip(), str(기관 or "").strip()
        if not 이름:
            return "비어 있지 않은 이름을 입력해 주세요."
        if any(p["name"] == 이름 for k, p in self._프로파일들.items() if k != identifier):
            return "이미 사용 중인 서식 이름입니다."
        바뀐 = dict(self._프로파일들[identifier], name=이름)
        if 기관:
            바뀐["organization"] = 기관
        else:
            바뀐.pop("organization", None)
        try:
            self._서식_파일_저장(identifier, 바뀐)
        except Exception as exc:
            return f"서식 이름 저장 실패: {exc}"
        self._프로파일들[identifier] = 바뀐
        self._프로파일_목록갱신()
        self.status_var.set(f"서식 이름을 '{이름}'(으)로 바꿨습니다.")
        return None

    def _서식_삭제(self, identifier):
        """서식을 삭제한다(확인은 부른 쪽이 한다). 쓰던 서식이면 기본 서식으로 돌린다. 성공하면 None."""
        if self.running:
            return "작업 중에는 서식을 바꿀 수 없습니다."
        if not identifier or identifier not in self._프로파일들:
            return "기본 문서 서식은 삭제할 수 없습니다."
        이름 = self._프로파일들[identifier].get("name") or identifier
        try:
            경로 = 서식프로파일_폴더() / (identifier + ".json")
            if 경로.is_file():
                경로.unlink()
            for 예시 in self._서식예시_경로(identifier):      # 보관한 서식 예시도 함께 지운다
                if 예시.is_file():
                    예시.unlink()
        except Exception as exc:
            return f"서식 삭제 실패: {exc}"
        self._프로파일들.pop(identifier, None)
        if self._활성_서식_프로파일 == identifier:
            self._활성_서식_프로파일 = ""
            self._프로파일_목록갱신()
            self._프로파일_선택()
        else:
            self._프로파일_목록갱신()
        self.status_var.set(f"'{이름}' 서식을 삭제했습니다.")
        return None

    def _서식예시_경로(self, identifier):
        """서식마다 하나씩 보관하는 예시 파일과 그 정보 파일의 경로(설정 폴더 format_examples, 서식 식별자로 이름 짓는다)."""
        이름 = re.sub(r'[\/:*?"<>|\s]+', "_", identifier or "").strip("_") or "_기본"
        폴더 = 서식예시_폴더()
        return 폴더 / f"서식예시_{이름}.hwpx", 폴더 / f"서식예시_{이름}.json"

    def _서식예시_확인(self):
        """지금 고른 서식을 예시 보고서에 입혀 한/글로 보여 준다('서식 예시 확인', 2026-10-04 사용자 요청).

        서식마다 예시 파일을 하나씩 만들어 보관하고(설정 폴더 format_examples), 다시 확인할 때는 그 파일을 바로 연다.
        서식 값·예시 글·앱 판이 바뀌어 보관한 예시가 지금 서식과 다르면(서식예시_서명) 새로 만든다.
        새로 만들 때는 예시 글(서식예시_글)을 독립 한/글 세션에서 HWPX로 만든 뒤 '한 번에 적용'(서식 + 자간 정리, 서식예시_작업모드) 작업으로 처리한다.
        정리할 문서 목록과 이전 결과 목록은 바꾸지 않는다.
        """
        if self.running or getattr(self, "_서식예시_준비중", False) or getattr(self, "_서식분석중", False):
            self.status_var.set("지금 하는 작업이 끝난 뒤 서식 예시를 확인해 주세요.")
            return
        identifier = self._활성_서식_프로파일 or ""
        profile = self._프로파일들.get(identifier) or {}
        이름 = str(profile.get("name") or "기본 서식")
        서명 = 서식예시_서명(profile)
        예시경로, 정보경로 = self._서식예시_경로(identifier)
        try:
            정보 = json.loads(정보경로.read_text(encoding="utf-8")) if 정보경로.is_file() else {}
        except Exception:
            정보 = {}
        if 예시경로.is_file() and 정보.get("서명") == 서명:
            self.로그표시(f"서식 예시 확인: 보관한 '{이름}' 서식 예시를 엽니다 — {예시경로}")
            self.status_var.set(f"'{이름}' 서식 예시를 한/글로 열었습니다.")
            self._경로_열기(str(예시경로))
            return
        안전이름 = re.sub(r'[\/:*?"<>|\s]+', "_", 이름).strip("_")[:40] or "서식"
        폴더 = (Path(tempfile.gettempdir()) / "HwpAutoDocFit_서식예시"
                / f"{안전이름}_{_datetime.datetime.now():%Y%m%d-%H%M%S}")
        폴더.mkdir(parents=True, exist_ok=True)
        원본 = 폴더 / f"서식예시_{안전이름}.hwpx"
        self._서식예시_준비중 = True
        self.status_var.set(f"'{이름}' 서식 예시를 만드는 중입니다(처음 한 번만 1분쯤 걸려요)…")
        self.로그표시(f"서식 예시 확인: '{이름}' 서식을 예시 보고서에 입혀 보관합니다.")
        결과 = {}

        def 만들기():
            try:
                텍스트_hwpx_단독변환(서식예시_글, 원본, 라벨_해석=False)
            except Exception as exc:
                결과["오류"] = str(exc) or type(exc).__name__
            결과["끝"] = True

        # 작업 스레드에서는 Tk를 부르지 않고, 화면 스레드가 끝났는지 살핀다(스레드에서 부른 after는 실행되지 않을 수 있다).
        def 살피기():
            if not 결과.get("끝"):
                self.root.after(200, 살피기)
                return
            self._서식예시_시작(원본, {"이름": 이름, "식별자": identifier, "서명": 서명,
                                    "예시경로": 예시경로, "정보경로": 정보경로}, 결과.get("오류"))

        threading.Thread(target=만들기, daemon=True).start()
        self.root.after(200, 살피기)

    def _서식예시_시작(self, 원본, 예시, 오류):
        """만든 예시 문서를 '한 번에 적용'(서식 + 자간 정리)으로 처리한다(정리할 문서 목록은 그대로 두고 예시 문서만 넘긴다)."""
        self._서식예시_준비중 = False
        if 오류 or not Path(원본).is_file():
            self.status_var.set(f"서식 예시 문서를 만들지 못했습니다: {오류 or '파일 없음'}")
            return
        if self.running:
            self.status_var.set("다른 작업이 시작되어 서식 예시 확인을 취소했습니다.")
            return
        이전파일 = list(self.files)
        self._서식예시_작업 = dict(예시, 결과목록=list(self._결과목록))
        self._재개_대기중 = False
        self.files = [str(원본)]
        try:
            self.작업시작(서식예시_작업모드)
        finally:
            self.files = 이전파일
        if not self.running:
            self._서식예시_작업 = None

    def _서식예시_완료(self, item, 중단=False):
        """예시 작업이 끝나면 결과를 서식 예시로 보관해 열고, 작업 상태와 이전 결과 목록을 되돌린다."""
        작업 = self._서식예시_작업
        self._서식예시_작업 = None
        self.running = False
        self._안내_설정(0)
        self.버튼_대기중()
        결과 = [r.get("결과") for r in self._결과목록 if r.get("결과")]
        self.stage_board.finish("중단" if 중단 else ("완료" if 결과 else "오류"))
        self._결과목록 = 작업["결과목록"]
        self.open_result_button.config(state="normal" if self._결과목록 else "disabled")
        if 중단 or not 결과:
            self.status_var.set("서식 예시를 만들지 못했습니다. 작업 로그를 확인해 주세요.")
            return
        경로 = Path(결과[-1])
        try:
            예시경로 = Path(작업["예시경로"])
            예시경로.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(경로, 예시경로)
            Path(작업["정보경로"]).write_text(json.dumps(
                {"서명": 작업["서명"], "이름": 작업["이름"], "식별자": 작업["식별자"], "앱판": APP_VERSION,
                 "만든때": f"{_datetime.datetime.now():%Y-%m-%d %H:%M:%S}"}, ensure_ascii=False, indent=2),
                encoding="utf-8")
            경로 = 예시경로
        except Exception as exc:
            self.로그표시(f"서식 예시를 보관하지 못했습니다(이번 결과만 엽니다): {exc}")
        self.로그표시(f"서식 예시 확인: {경로}")
        if self.autoclose_var.get():
            self.status_var.set(f"'{작업['이름']}' 서식 예시를 한/글로 열었습니다.")
            self._경로_열기(str(경로))
        else:
            self.status_var.set(f"'{작업['이름']}' 서식 예시를 한/글 창에서 확인해 주세요(보관: {경로.name}).")


    def _서식_파일에서_추가(self):
        """예시 HWP/HWPX 파일을 골라 서식을 복제한다(이름은 분석 뒤 세부사항 창에서 고친다)."""
        if self.running or getattr(self, "_서식분석중", False):
            return
        path = askopenfilename(parent=self._서식창_부모(), title="서식을 복제할 예시 보고서",
                               filetypes=[("한글파일", "*.hwp *.hwpx")])
        if path:
            self._서식_분석_시작(path, 이름묻기=False)

    def _서식_예시편집_시작(self):
        """빈 한/글 문서를 열어 사용자가 예시 문서를 직접 쓰게 하고, '분석 시작'을
        누르면 그 문서를 분석해 새 서식으로 등록한다(TODO 6순위)."""
        if self.running or getattr(self, "_서식분석중", False):
            return
        기존창 = getattr(self, "_예시편집_창", None)
        if 기존창 is not None and 기존창.winfo_exists():
            기존창.lift()
            return
        parent = self.settings_toplevel if self.settings_toplevel and self.settings_toplevel.winfo_viewable() else self.root
        try:
            pythoncom.CoInitialize()
            보안모듈_초기화()
            app = 한글_COM_인스턴스_생성(독립=True)
            if not app.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE):
                raise RuntimeError("한글 보안 모듈을 등록하지 못했습니다.")
            app.XHwpWindows.Item(0).Visible = True
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"한글을 열지 못했습니다.\n{exc}", parent=parent)
            return
        self._예시편집_hwp = app
        창 = tk.Toplevel(parent)
        self._예시편집_창 = 창
        창.title("서식 예시 문서 편집")
        창.attributes("-topmost", True)
        창.resizable(False, False)
        ttk.Label(창, text="열린 한/글 창에서 예시 문서를 작성하세요.", font=("맑은 고딕", 11, "bold")).pack(
            anchor="w", padx=14, pady=(12, 2))
        ttk.Label(창, text="□·ㅇ·-·※ 같은 항목기호를 섞어 원하는 계층 구조로 쓰면, 기호별로 가장 많이 쓴 "
                          "글꼴·크기·들여쓰기가 그 기호의 서식이 됩니다. 다 쓰면 '분석 시작'을 누르세요.\n"
                          "서식 이름은 첫 문장의 앞 8글자로 정하며 나중에 '이름 바꾸기…'로 고칠 수 있습니다.",
                  style="Hint.TLabel", wraplength=420, justify="left").pack(anchor="w", padx=14)
        안내 = tk.StringVar(value="")
        ttk.Label(창, textvariable=안내, foreground="#b03030", wraplength=420).pack(anchor="w", padx=14, pady=(6, 0))
        버튼줄 = ttk.Frame(창)
        버튼줄.pack(fill="x", padx=14, pady=12)

        def 한글닫기():
            한글 = getattr(self, "_예시편집_hwp", None)
            self._예시편집_hwp = None
            if 한글 is not None:
                try:
                    한글.Clear(1)
                    한글.Quit()
                except Exception:
                    pass

        def 취소():
            한글닫기()
            창.destroy()
            self._예시편집_창 = None

        def 분석시작():
            한글 = self._예시편집_hwp
            if 한글 is None:
                return
            임시 = Path(tempfile.mkdtemp(prefix="docfit_example_")) / "예시.hwpx"
            try:
                if 한글.SaveAs(str(임시), "HWPX", "") is False:
                    raise RuntimeError("예시 문서를 임시 파일로 저장하지 못했습니다.")
                문단들 = [b.text for b in inspect_hwpx(임시).blocks if b.type == "paragraph"]
            except Exception as exc:
                안내.set(f"예시 문서를 읽지 못했습니다: {exc}")
                return
            if not any(leading_marker(t)[0] for t in 문단들):
                안내.set("항목기호(□·ㅇ·-·※ 등)로 시작하는 문단이 없습니다. 기호를 붙인 문단을 한두 개 이상 써 주세요.")
                return
            이름 = 예시문서_기본이름(문단들)
            한글닫기()
            창.destroy()
            self._예시편집_창 = None
            self._서식_분석_시작(str(임시), 이름묻기=False, 기본이름=이름)

        ttk.Button(버튼줄, text="분석 시작", command=분석시작).pack(side="left")
        ttk.Button(버튼줄, text="취소", command=취소).pack(side="right")
        창.protocol("WM_DELETE_WINDOW", 취소)

    def _서식_삭제하기(self):
        if self.running:
            return
        if not self._활성_서식_프로파일:
            messagebox.showinfo(APP_NAME, "기본 문서 서식은 삭제할 수 없습니다.", parent=self.settings_toplevel)
            return
        profile = self._프로파일들.get(self._활성_서식_프로파일)
        이름 = profile["name"] if profile else self._활성_서식_프로파일
        if not messagebox.askyesno(
            APP_NAME, f"'{이름}' 서식을 삭제하시겠습니까?\n삭제하면 되돌릴 수 없습니다.",
            parent=self.settings_toplevel
        ):
            return
        오류 = self._서식_삭제(self._활성_서식_프로파일)
        if 오류:
            messagebox.showerror(APP_NAME, 오류, parent=self.settings_toplevel)

    def _서식_수정하기(self, identifier=None):
        """서식의 세부값을 고친다(identifier가 없으면 지금 쓰는 서식). 기본 서식을 고치면 새 서식으로 저장한다."""
        if self.running:
            return
        if identifier is None:
            identifier = self._활성_서식_프로파일
        if identifier not in self._프로파일들:
            return
        parent = self._서식창_부모()
        profile = copy.deepcopy(self._프로파일들[identifier])
        if not identifier:
            profile["name"] = "기본 보고서 서식 (사용자 수정)"
        if profile.get("element_analysis"):
            다른이름 = {p["name"] for k, p in self._프로파일들.items() if k != identifier}
            if not self._서식_세부사항_확인(profile, parent, 다른이름):
                return
        elif not self._서식_구조_확인(profile, parent):
            return
        try:
            if not identifier:
                identifier = uuid.uuid4().hex
            self._서식_파일_저장(identifier, profile)
        except Exception as exc:
            self.status_var.set(f"서식 수정 저장 실패: {exc}")
            if not self._웹화면_모드():
                messagebox.showerror(APP_NAME, f"서식 수정 저장 실패\n{exc}", parent=parent)
            return
        self._프로파일들[identifier] = profile
        self._활성_서식_프로파일 = identifier
        self._프로파일_목록갱신()
        self._프로파일_선택()
        self.status_var.set(f"'{profile['name']}' 서식을 수정했습니다.")

    def _문서검토_열기(self):
        """원본을 변경하지 않는 구조·표현 검토 결과와 계층별 훑어보기를 표시한다."""
        if self.running or getattr(self, "_서식분석중", False):
            return
        existing = getattr(self, "_문서검토_창", None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            return
        source = self._고급도구_대상()
        if source is None:
            messagebox.showinfo(APP_NAME, "먼저 검토할 HWP/HWPX 파일을 추가해 주세요.", parent=self.root)
            return
        window = tk.Toplevel(self.root)
        self._문서검토_창 = window
        window.title("문서 구조·가독성 검토 · 읽기 전용")
        window.geometry("1120x740")
        window.transient(self.root)
        body = ttk.Frame(window, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text=f"검토 문서: {source.name}", font=("맑은 고딕", 13, "bold")).pack(anchor="w")
        ttk.Label(body, text="원본을 수정하거나 외부로 전송하지 않습니다. 의미 판단은 사용자가 확인해 주세요.",
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 8))
        options = ttk.Frame(body)
        options.pack(fill="x", pady=(0, 8))
        saved = 설정_불러오기()
        kind = tk.StringVar(value=saved.get("review_document_kind", "보고서"))
        purpose = tk.StringVar(value=saved.get("review_reading_purpose", "상세 설명용"))
        if kind.get() not in DOCUMENT_KINDS: kind.set("보고서")
        if purpose.get() not in PURPOSES: purpose.set("상세 설명용")
        ttk.Label(options, text="문서 유형").pack(side="left")
        ttk.Combobox(options, textvariable=kind, values=DOCUMENT_KINDS, state="readonly", width=12).pack(side="left", padx=(5, 15))
        ttk.Label(options, text="읽기 목적").pack(side="left")
        ttk.Combobox(options, textvariable=purpose, values=PURPOSES, state="readonly", width=17).pack(side="left", padx=5)
        status = tk.StringVar(value="검토를 시작하세요.")
        start_button = ttk.Button(options, text="검토 시작")
        start_button.pack(side="right")
        result_box = {"value": None}
        def export_result():
            if result_box["value"] is None:
                return
            path = asksaveasfilename(parent=window, title="검토 결과 저장",
                                     initialfile=source.stem + "(문서검토).json",
                                     defaultextension=".json", filetypes=[("JSON", "*.json")])
            if not path:
                return
            try:
                Path(path).write_text(json.dumps(result_box["value"], ensure_ascii=False, indent=2), encoding="utf-8")
                status.set(f"검토 결과 저장: {path}")
            except OSError as exc:
                messagebox.showerror(APP_NAME, f"검토 결과를 저장하지 못했습니다.\n{exc}", parent=window)
        export_button = ttk.Button(options, text="결과 JSON 저장…", command=export_result, state="disabled")
        export_button.pack(side="right", padx=(0, 6))
        notebook = ttk.Notebook(body)
        notebook.pack(fill="both", expand=True)
        issue_frame = ttk.Frame(notebook, padding=4)
        outline_frame = ttk.Frame(notebook, padding=4)
        notebook.add(issue_frame, text="검토 후보")
        notebook.add(outline_frame, text="계층 훑어보기")
        columns = ("severity", "category", "location", "message", "context")
        issue_tree = ttk.Treeview(issue_frame, columns=columns, show="headings", selectmode="browse")
        for key, title, width in zip(columns, ("구분", "항목", "위치", "확인할 내용", "원문"),
                                     (90, 140, 135, 385, 290)):
            issue_tree.heading(key, text=title)
            issue_tree.column(key, width=width, anchor="w")
        issue_scroll = ttk.Scrollbar(issue_frame, orient="vertical", command=issue_tree.yview)
        issue_tree.configure(yscrollcommand=issue_scroll.set)
        issue_tree.pack(side="left", fill="both", expand=True)
        issue_scroll.pack(side="right", fill="y")
        outline = ttk.Treeview(outline_frame, columns=("location", "role", "text"), show="headings")
        for key, title, width in (("location", "위치", 145), ("role", "계층", 100), ("text", "내용", 780)):
            outline.heading(key, text=title)
            outline.column(key, width=width, anchor="w")
        outline_scroll = ttk.Scrollbar(outline_frame, orient="vertical", command=outline.yview)
        outline.configure(yscrollcommand=outline_scroll.set)
        outline.pack(side="left", fill="both", expand=True)
        outline_scroll.pack(side="right", fill="y")
        ttk.Label(body, textvariable=status, style="Hint.TLabel").pack(anchor="w", pady=(8, 0))

        def completed(result=None, error=None):
            if not window.winfo_exists():
                return
            start_button.config(state="normal")
            if error:
                status.set("검토 실패")
                messagebox.showerror(APP_NAME, f"문서 검토에 실패했습니다.\n{error}", parent=window)
                return
            result_box["value"] = result
            export_button.config(state="normal")
            issue_tree.delete(*issue_tree.get_children())
            outline.delete(*outline.get_children())
            for item in result["issues"]:
                issue_tree.insert("", "end", values=(item["severity"], item["category"],
                                  item["location"], item["message"], item["context"]))
            for item in result["outline"]:
                outline.insert("", "end", values=(item["location"], item["role"], item["text"]))
            status.set(f"본문 {result['body_count']}개 · 표 셀 문단 {result['cell_count']}개 · "
                       f"검토 후보 {len(result['issues'])}건 · 원문은 변경되지 않았습니다.")

        def start():
            start_button.config(state="disabled")
            status.set("문서 구조와 서식을 분석하고 있습니다…")
            settings = 설정_불러오기()
            settings.update(review_document_kind=kind.get(), review_reading_purpose=purpose.get())
            self.review_document_kind, self.review_reading_purpose = kind.get(), purpose.get()
            설정_저장(settings)
            profile = copy.deepcopy(self._프로파일들.get(self._활성_서식_프로파일))
            selected_kind, selected_purpose = kind.get(), purpose.get()
            def worker():
                try:
                    with tempfile.TemporaryDirectory(prefix="docfit_review_") as folder:
                        snapshot = 교정용_hwpx_준비(source, folder)
                        result = review_document(snapshot, profile, selected_purpose, selected_kind)
                    gui_queue.put(("document_review_done", completed, result, None))
                except Exception as exc:
                    gui_queue.put(("document_review_done", completed, None, str(exc)))
            threading.Thread(target=worker, daemon=True, name="document-review").start()

        start_button.config(command=start)
        start()

    @staticmethod
    def _아웃라인_깊이(줄):
        """한 줄의 계층 깊이와 본문을 읽는다.

        저장 형식: 0단계는 "# 본문"(들여쓰기 없음), N단계(N≥1)는
        ((N-1)*2)칸 들여쓰기 + "- 본문". 이 형식은 outline_pasted_text가
        그대로 읽어 0단계→ㅁ, 1→ㅇ, 2→-, 3단계 이후는 모두 •로 바꾼다.
        """
        본문시작 = 줄.lstrip(" ")
        들여쓰기 = len(줄) - len(본문시작)
        if 본문시작.startswith("# "):
            return 0, 본문시작[2:]
        if 본문시작.startswith("- "):
            return (들여쓰기 // 2) + 1, 본문시작[2:]
        return 0, 본문시작

    @staticmethod
    def _아웃라인_접두(깊이, 본문):
        if 깊이 <= 0:
            return f"# {본문}"
        return " " * ((깊이 - 1) * 2) + f"- {본문}"

    def _아웃라이너_열기(self):
        """워크플로위류 아웃라이너로 새 글을 쓴다.

        Tab/Shift+Tab으로 계층을 넣고 빼며, 저장 형식 자체가 계층 구조를
        그대로 담은 마크다운이다(0단계 "# ", 그 아래는 "- "를 들여쓰기
        깊이만큼 겹쳐 표시). '개조식 텍스트로 추가'는 이 마크다운을
        outline_pasted_text로 ㅁ/ㅇ/-/• 공문서 항목기호로 바꿔 문서
        목록에 추가하고, '마크다운으로 추가'는 원본 그대로 추가해
        고급 문서 엔진(kordoc)이 있을 때 서식을 살려 변환하게 한다.

        1.68 Alpha 6(TODO 5순위): 접기/펼치기(Ctrl+↑/↓), 확대(Alt+→/←),
        항목 이동(Alt+Shift+↑/↓), 완료 표시(Ctrl+Enter, "[x] "), 메모
        (Shift+Enter, "> "), 검색 걸러 보기(Ctrl+F), 저장·열기(Ctrl+S/O)와
        닫을 때 자동 저장한 글을 다음에 이어 쓰기. 줄 계산은
        docfit_core.outline_ops의 순수 함수가 맡는다.
        """
        if self.running:
            return
        existing = getattr(self, "_아웃라이너_창", None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            return
        window = tk.Toplevel(self.root)
        self._아웃라이너_창 = window
        window.title("아웃라이너로 새 글 작성")
        window.geometry("1020x660")
        window.minsize(680, 440)
        window.transient(self.root)
        임시저장_경로 = Path(설정_파일_경로()).with_name("outliner_draft.md")

        body = ttk.Frame(window, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="워크플로위처럼 항목을 쓰고 Tab/Shift+Tab으로 계층을 넣고 빼세요.",
                  font=("맑은 고딕", 12, "bold")).pack(anchor="w")
        ttk.Label(body,
                  text="Enter: 같은 계층의 새 항목 · Tab/Shift+Tab: 들여쓰기/내어쓰기 · "
                       "Ctrl+↑/↓: 접기/펼치기 · Alt+→/←: 확대/전체 보기 · Alt+Shift+↑/↓: 항목 이동 · "
                       "Ctrl+Enter: 완료 표시 · Shift+Enter: 메모 · Ctrl+F: 검색 · Ctrl+S/O: 저장/열기. "
                       "0단계는 ㅁ, 1단계는 ㅇ, 2단계는 -, 3단계 이후는 •, 메모는 ※로 바뀝니다.",
                  style="Hint.TLabel", wraplength=980, justify="left").pack(anchor="w", pady=(2, 6))

        toolbar = ttk.Frame(body)
        toolbar.pack(fill="x", pady=(0, 6))
        ttk.Label(toolbar, text="검색").pack(side="left")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=search_var, width=22)
        search_entry.pack(side="left", padx=(4, 10))

        panes = ttk.Frame(body)
        panes.pack(fill="both", expand=True)
        panes.grid_columnconfigure(0, weight=1)
        panes.grid_columnconfigure(1, weight=1)
        panes.grid_rowconfigure(1, weight=1)

        ttk.Label(panes, text="아웃라인").grid(row=0, column=0, sticky="w")
        ttk.Label(panes, text="공문서 개조식 미리보기").grid(row=0, column=1, sticky="w", padx=(8, 0))

        outline_frame = ttk.Frame(panes)
        outline_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        outline_frame.grid_columnconfigure(0, weight=1)
        outline_frame.grid_rowconfigure(0, weight=1)
        outline_text = tk.Text(outline_frame, wrap="word", undo=True, font=("맑은 고딕", 11))
        outline_text.grid(row=0, column=0, sticky="nsew")
        outline_scroll = ttk.Scrollbar(outline_frame, orient="vertical", command=outline_text.yview)
        outline_scroll.grid(row=0, column=1, sticky="ns")
        outline_text.configure(yscrollcommand=outline_scroll.set)
        # 접기·확대·검색은 줄을 화면에서만 숨긴다(저장 내용은 그대로).
        for 태그 in ("hidden_fold", "hidden_zoom", "hidden_filter"):
            outline_text.tag_configure(태그, elide=True)
        outline_text.tag_configure("done", overstrike=True, foreground="#8a8a8a")
        outline_text.tag_configure("note", foreground="#6b6b6b", font=("맑은 고딕", 10, "italic"))
        outline_text.tag_configure("folded", background="#eef3fb")
        outline_text.tag_configure("found", background="#fff1a8")

        preview_frame = ttk.Frame(panes)
        preview_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 0))
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_text = tk.Text(preview_frame, wrap="word", font=("맑은 고딕", 10), background="#f7f7f7")
        preview_text.grid(row=0, column=0, sticky="nsew")
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_text.yview)
        preview_scroll.grid(row=0, column=1, sticky="ns")
        preview_text.configure(yscrollcommand=preview_scroll.set)

        status = tk.StringVar(value="항목을 입력하고 Enter로 다음 항목을 이어가세요.")

        def 줄목록():
            return outline_text.get("1.0", "end-1c").split("\n")

        def 현재줄번호():
            return int(outline_text.index("insert").split(".")[0]) - 1

        def 줄범위(시작, 끝):
            return f"{시작 + 1}.0", f"{끝 + 1}.0"

        def 모양_갱신(event=None):
            줄들 = 줄목록()
            for 태그 in ("done", "note"):
                outline_text.tag_remove(태그, "1.0", "end")
            for i, 줄 in enumerate(줄들):
                if outline_ops.is_done(줄):
                    outline_text.tag_add("done", f"{i + 1}.0", f"{i + 1}.end")
                elif outline_ops.parse(줄)[0] == "note":
                    outline_text.tag_add("note", f"{i + 1}.0", f"{i + 1}.end")

        def 숨김_해제():
            for 태그 in ("hidden_fold", "hidden_zoom", "hidden_filter", "folded", "found"):
                outline_text.tag_remove(태그, "1.0", "end")

        def 내용_바꾸기(줄들, 커서줄=None, 커서칸="end"):
            숨김_해제()
            outline_text.edit_separator()
            outline_text.delete("1.0", "end")
            outline_text.insert("1.0", "\n".join(줄들))
            outline_text.edit_separator()
            if 커서줄 is not None:
                outline_text.mark_set("insert", f"{커서줄 + 1}.{커서칸}")
                outline_text.see("insert")
            모양_갱신()

        def 현재줄범위():
            return outline_text.index("insert linestart"), outline_text.index("insert lineend")

        def 이전줄_깊이(줄시작):
            행 = int(줄시작.split(".")[0])
            if 행 <= 1:
                return None
            return outline_ops.depth(줄목록(), 행 - 2)

        def 엔터처리(event=None):
            줄시작, 줄끝 = 현재줄범위()
            전체줄 = outline_text.get(줄시작, 줄끝)
            if outline_ops.parse(전체줄)[0] == "note":
                # 메모 줄에서 Enter는 메모가 딸린 항목과 같은 계층의 새 항목을 연다.
                깊이 = outline_ops.depth(줄목록(), 현재줄번호())
                새프리픽스 = self._아웃라인_접두(깊이, "")
                outline_text.insert(줄끝, "\n" + 새프리픽스)
                outline_text.mark_set("insert", f"{int(줄시작.split('.')[0]) + 1}.{len(새프리픽스)}")
                return "break"
            깊이, 본문 = self._아웃라인_깊이(전체줄)
            프리픽스길이 = len(전체줄) - len(본문)
            커서컬럼 = int(outline_text.index("insert").split(".")[1])
            분할지점 = max(프리픽스길이, 커서컬럼)
            앞부분 = 전체줄[프리픽스길이:분할지점]
            뒷부분 = 전체줄[분할지점:]
            outline_text.delete(줄시작, 줄끝)
            outline_text.insert(줄시작, self._아웃라인_접두(깊이, 앞부분))
            새프리픽스 = self._아웃라인_접두(깊이, "")
            outline_text.insert("insert", "\n" + 새프리픽스 + 뒷부분)
            행 = int(줄시작.split(".")[0]) + 1
            outline_text.mark_set("insert", f"{행}.{len(새프리픽스)}")
            return "break"

        def 들여쓰기(event=None):
            줄시작, 줄끝 = 현재줄범위()
            전체줄 = outline_text.get(줄시작, 줄끝)
            if outline_ops.parse(전체줄)[0] == "note":
                return "break"
            깊이, 본문 = self._아웃라인_깊이(전체줄)
            이전깊이 = 이전줄_깊이(줄시작)
            최대깊이 = 0 if 이전깊이 is None else 이전깊이 + 1
            새깊이 = min(깊이 + 1, max(최대깊이, 0), 8)
            if 새깊이 == 깊이:
                return "break"
            이전프리픽스길이 = len(전체줄) - len(본문)
            커서오프셋 = max(0, int(outline_text.index("insert").split(".")[1]) - 이전프리픽스길이)
            새줄 = self._아웃라인_접두(새깊이, 본문)
            outline_text.delete(줄시작, 줄끝)
            outline_text.insert(줄시작, 새줄)
            새프리픽스길이 = len(새줄) - len(본문)
            outline_text.mark_set("insert", f"{줄시작.split('.')[0]}.{새프리픽스길이 + 커서오프셋}")
            return "break"

        def 내어쓰기(event=None):
            줄시작, 줄끝 = 현재줄범위()
            전체줄 = outline_text.get(줄시작, 줄끝)
            if outline_ops.parse(전체줄)[0] == "note":
                return "break"
            깊이, 본문 = self._아웃라인_깊이(전체줄)
            새깊이 = max(깊이 - 1, 0)
            if 새깊이 == 깊이:
                return "break"
            이전프리픽스길이 = len(전체줄) - len(본문)
            커서오프셋 = max(0, int(outline_text.index("insert").split(".")[1]) - 이전프리픽스길이)
            새줄 = self._아웃라인_접두(새깊이, 본문)
            outline_text.delete(줄시작, 줄끝)
            outline_text.insert(줄시작, 새줄)
            새프리픽스길이 = len(새줄) - len(본문)
            outline_text.mark_set("insert", f"{줄시작.split('.')[0]}.{새프리픽스길이 + 커서오프셋}")
            return "break"

        def 접기(event=None):
            줄들 = 줄목록()
            i = outline_ops.item_start(줄들, 현재줄번호())
            끝 = outline_ops.subtree_end(줄들, i)
            if 끝 <= i + 1:
                status.set("접을 하위 항목이 없습니다.")
                return "break"
            outline_text.tag_add("hidden_fold", *줄범위(i + 1, 끝))
            outline_text.tag_add("folded", f"{i + 1}.0", f"{i + 1}.end")
            outline_text.mark_set("insert", f"{i + 1}.end")
            status.set(f"접음 · 하위 {끝 - i - 1}줄 (Ctrl+↓로 펼치기)")
            return "break"

        def 펼치기(event=None):
            줄들 = 줄목록()
            i = outline_ops.item_start(줄들, 현재줄번호())
            끝 = outline_ops.subtree_end(줄들, i)
            outline_text.tag_remove("hidden_fold", *줄범위(i + 1, 끝))
            outline_text.tag_remove("folded", f"{i + 1}.0", f"{i + 1}.end")
            status.set("펼침")
            return "break"

        def 확대(event=None):
            줄들 = 줄목록()
            i = outline_ops.item_start(줄들, 현재줄번호())
            끝 = outline_ops.subtree_end(줄들, i)
            outline_text.tag_remove("hidden_zoom", "1.0", "end")
            if i > 0:
                outline_text.tag_add("hidden_zoom", "1.0", f"{i + 1}.0")
            if 끝 < len(줄들):
                outline_text.tag_add("hidden_zoom", f"{끝}.end", "end")
            status.set(f"확대: {outline_ops.parse(줄들[i])[2][:30]} (Alt+←로 전체 보기)")
            return "break"

        def 전체보기(event=None):
            outline_text.tag_remove("hidden_zoom", "1.0", "end")
            status.set("전체 보기")
            return "break"

        def 이동(up):
            줄들 = 줄목록()
            결과 = outline_ops.move_block(줄들, 현재줄번호(), up)
            if 결과 is None:
                status.set("같은 계층에서 더 옮길 수 없습니다.")
                return "break"
            새줄들, 새번호 = 결과
            내용_바꾸기(새줄들, 새번호)
            status.set("항목을 옮겼습니다.")
            return "break"

        def 완료표시(event=None):
            줄들 = 줄목록()
            i = outline_ops.item_start(줄들, 현재줄번호())
            새줄 = outline_ops.toggle_done(줄들[i])
            if 새줄 != 줄들[i]:
                outline_text.delete(f"{i + 1}.0", f"{i + 1}.end")
                outline_text.insert(f"{i + 1}.0", 새줄)
                모양_갱신()
                status.set("완료 표시" if outline_ops.is_done(새줄) else "완료 표시 해제")
            return "break"

        def 메모추가(event=None):
            줄들 = 줄목록()
            i = outline_ops.item_start(줄들, 현재줄번호())
            j = i + 1
            while j < len(줄들) and outline_ops.parse(줄들[j])[0] == "note":
                j += 1
            접두 = outline_ops.note_prefix(줄들[i])
            outline_text.insert(f"{j}.end", "\n" + 접두)
            outline_text.mark_set("insert", f"{j + 1}.end")
            모양_갱신()
            status.set("메모를 입력하세요(개조식으로 바꿀 때 ※ 부연설명이 됩니다).")
            return "break"

        def 검색(*args):
            outline_text.tag_remove("hidden_filter", "1.0", "end")
            outline_text.tag_remove("found", "1.0", "end")
            검색어 = search_var.get().strip()
            if not 검색어:
                status.set("검색을 지웠습니다.")
                return
            줄들 = 줄목록()
            보일줄 = outline_ops.filter_visible(줄들, 검색어)
            for i in range(len(줄들)):
                if i not in 보일줄:
                    outline_text.tag_add("hidden_filter", *줄범위(i, i + 1))
            시작 = "1.0"
            while True:
                위치 = outline_text.search(검색어, 시작, stopindex="end", nocase=True)
                if not 위치:
                    break
                끝 = f"{위치}+{len(검색어)}c"
                outline_text.tag_add("found", 위치, 끝)
                시작 = 끝
            status.set(f"검색: '{검색어}' — {len([i for i in 보일줄 if 검색어.lower() in 줄들[i].lower()])}줄 (Esc로 해제)")

        def 검색해제(event=None):
            search_var.set("")
            outline_text.focus_set()
            return "break"

        search_var.trace_add("write", 검색)
        search_entry.bind("<Escape>", 검색해제)
        search_entry.bind("<Return>", lambda e: (outline_text.focus_set(), "break")[1])

        outline_text.bind("<Return>", 엔터처리)
        outline_text.bind("<Tab>", 들여쓰기)
        outline_text.bind("<Shift-Tab>", 내어쓰기)
        outline_text.bind("<ISO_Left_Tab>", 내어쓰기)  # 일부 배치에서 Shift+Tab이 이 키심볼로 옴
        outline_text.bind("<Control-Up>", 접기)
        outline_text.bind("<Control-Down>", 펼치기)
        outline_text.bind("<Alt-Right>", 확대)
        outline_text.bind("<Alt-Left>", 전체보기)
        outline_text.bind("<Alt-Shift-Up>", lambda e: 이동(True))
        outline_text.bind("<Alt-Shift-Down>", lambda e: 이동(False))
        outline_text.bind("<Control-Return>", 완료표시)
        outline_text.bind("<Shift-Return>", 메모추가)
        outline_text.bind("<Escape>", 검색해제)
        outline_text.bind("<KeyRelease>", 모양_갱신)
        for 위젯 in (outline_text, search_entry):
            위젯.bind("<Control-f>", lambda e: (search_entry.focus_set(), "break")[1])

        def 기본파일명(내용, 확장자):
            for 줄 in 내용.splitlines():
                _, 본문 = self._아웃라인_깊이(줄)
                본문 = 본문.strip()
                if 본문:
                    안전한줄 = re.sub(r'[\\/:*?"<>|]', " ", 본문).strip()
                    return (안전한줄[:40] or "아웃라이너 글") + 확장자
            return f"아웃라이너 글{확장자}"

        def 미리보기():
            원문 = outline_text.get("1.0", "end-1c")
            if not 원문.strip():
                status.set("작성한 항목이 없습니다.")
                return None
            try:
                결과 = outline_pasted_text(outline_ops.export_markdown(원문.split("\n")))
            except Exception as e:
                messagebox.showerror(APP_NAME, f"개조식 변환 중 오류가 발생했습니다.\n\n{e}", parent=window)
                return None
            preview_text.delete("1.0", "end")
            preview_text.insert("1.0", 결과)
            status.set(f"미리보기 완료 · {len(결과)}자")
            return 결과

        def 개조식으로추가():
            결과 = 미리보기()
            if not 결과:
                return
            경로 = asksaveasfilename(
                parent=window, title="개조식 텍스트를 저장할 위치",
                initialfile=기본파일명(outline_text.get("1.0", "end-1c"), ".txt"),
                defaultextension=".txt", filetypes=[("텍스트 파일", "*.txt")],
            )
            if not 경로:
                return
            try:
                Path(경로).write_text(결과, encoding="utf-8")
            except OSError as e:
                messagebox.showerror(APP_NAME, f"파일 저장 중 오류가 발생했습니다.\n\n{e}", parent=window)
                return
            if self.파일추가(경로):
                status.set(f"개조식 문서로 추가했습니다 · {Path(경로).name}")
                self.status_var.set(f"{len(self.files)}개 문서 선택")
                self.로그표시(f"아웃라이너 글을 개조식 문서로 추가: {Path(경로).name}")
            else:
                status.set("이미 목록에 있는 파일입니다.")

        def 마크다운으로추가():
            원문 = outline_text.get("1.0", "end-1c")
            if not 원문.strip():
                status.set("작성한 항목이 없습니다.")
                return
            경로 = asksaveasfilename(
                parent=window, title="마크다운을 저장할 위치",
                initialfile=기본파일명(원문, ".md"),
                defaultextension=".md", filetypes=[("Markdown", "*.md")],
            )
            if not 경로:
                return
            try:
                Path(경로).write_text(원문, encoding="utf-8")
            except OSError as e:
                messagebox.showerror(APP_NAME, f"파일 저장 중 오류가 발생했습니다.\n\n{e}", parent=window)
                return
            if self.파일추가(경로):
                status.set(f"마크다운 문서로 추가했습니다 · {Path(경로).name}")
                self.status_var.set(f"{len(self.files)}개 문서 선택")
                self.로그표시(f"아웃라이너 글을 마크다운 문서로 추가: {Path(경로).name}")
            else:
                status.set("이미 목록에 있는 파일입니다.")

        def 저장(event=None):
            원문 = outline_text.get("1.0", "end-1c")
            경로 = asksaveasfilename(
                parent=window, title="아웃라인을 저장할 위치(나중에 '열기'로 이어 쓰기)",
                initialfile=기본파일명(원문, ".md"),
                defaultextension=".md", filetypes=[("Markdown", "*.md")],
            )
            if not 경로:
                return "break"
            try:
                Path(경로).write_text(원문, encoding="utf-8")
                status.set(f"저장했습니다 · {Path(경로).name}")
            except OSError as e:
                messagebox.showerror(APP_NAME, f"파일 저장 중 오류가 발생했습니다.\n\n{e}", parent=window)
            return "break"

        def 열기(event=None):
            경로 = askopenfilename(parent=window, title="이어 쓸 아웃라인 열기",
                                   filetypes=[("Markdown", "*.md"), ("텍스트 파일", "*.txt")])
            if not 경로:
                return "break"
            try:
                내용 = Path(경로).read_text(encoding="utf-8-sig")
            except (OSError, UnicodeDecodeError) as e:
                messagebox.showerror(APP_NAME, f"파일을 열지 못했습니다.\n\n{e}", parent=window)
                return "break"
            내용_바꾸기(내용.split("\n"), len(내용.split("\n")) - 1)
            status.set(f"불러왔습니다 · {Path(경로).name}")
            return "break"

        def 지우기():
            숨김_해제()
            outline_text.delete("1.0", "end")
            outline_text.insert("1.0", "# ")
            outline_text.mark_set("insert", "1.2")
            preview_text.delete("1.0", "end")
            try:
                임시저장_경로.unlink()
            except OSError:
                pass
            status.set("항목을 입력하고 Enter로 다음 항목을 이어가세요.")

        def 닫기():
            # 닫을 때 쓰던 글을 자동 저장해 다음에 창을 열면 이어 쓸 수 있게 한다.
            원문 = outline_text.get("1.0", "end-1c")
            try:
                if 원문.strip() and 원문.strip() != "#":
                    임시저장_경로.write_text(원문, encoding="utf-8")
                elif 임시저장_경로.exists():
                    임시저장_경로.unlink()
            except OSError:
                pass
            window.destroy()
            self._아웃라이너_창 = None

        window.protocol("WM_DELETE_WINDOW", 닫기)
        for 위젯 in (outline_text, search_entry):
            위젯.bind("<Control-s>", 저장)
            위젯.bind("<Control-o>", 열기)

        for 이름, 명령 in (("접기", 접기), ("펼치기", 펼치기), ("확대", 확대), ("전체 보기", 전체보기),
                         ("위로", lambda: 이동(True)), ("아래로", lambda: 이동(False)),
                         ("완료", 완료표시), ("메모", 메모추가), ("열기…", 열기), ("저장…", 저장)):
            ttk.Button(toolbar, text=이름, command=명령).pack(side="left", padx=(0, 4))

        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="미리보기", command=미리보기).pack(side="left")
        ttk.Button(actions, text="개조식 문서로 추가", command=개조식으로추가).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="마크다운으로 추가", command=마크다운으로추가).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="지우기", command=지우기).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="닫기", command=닫기).pack(side="right")
        ttk.Label(body, textvariable=status, style="Hint.TLabel").pack(anchor="w", pady=(6, 0))

        이전글 = ""
        try:
            if 임시저장_경로.exists():
                이전글 = 임시저장_경로.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            이전글 = ""
        if 이전글.strip():
            내용_바꾸기(이전글.split("\n"), len(이전글.split("\n")) - 1)
            status.set("지난번 작성하던 글을 불러왔습니다(닫을 때 자동 저장). 새로 쓰려면 '지우기'.")
        else:
            outline_text.insert("1.0", "# ")
            outline_text.mark_set("insert", "1.2")
        outline_text.focus_set()

    def _텍스트로_문서추가_열기(self):
        """붙여넣은 텍스트를 파일로 저장해 '01 정리할 문서' 목록에 바로 추가한다.

        자동 저장 폴더를 지정해 두면, 저장 즉시 그 폴더에 HWPX로 변환해
        추가한다(배치 작업과 독립된 한/글 세션 사용). 지정하지 않으면
        기존처럼 저장 위치를 직접 골라 .txt로 추가한다.
        """
        if self.running:
            return
        existing = getattr(self, "_텍스트추가_창", None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            return
        window = tk.Toplevel(self.root)
        self._텍스트추가_창 = window
        window.title("텍스트 붙여넣기로 문서 추가")
        window.geometry("640x520")
        window.minsize(420, 360)
        window.transient(self.root)

        진행중 = {"value": False}

        def closed():
            self._텍스트추가_창 = None

        def 닫기_요청():
            if 진행중["value"]:
                return
            window.destroy()
            closed()
        window.protocol("WM_DELETE_WINDOW", 닫기_요청)

        body = ttk.Frame(window, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="추가할 문서 내용을 붙여넣거나 입력하세요.",
                  font=("맑은 고딕", 12, "bold")).pack(anchor="w")
        ttk.Label(body,
                  text="자동 저장 폴더를 지정하면 저장 즉시 그 폴더에 HWPX로 변환해 문서 목록에 추가합니다. "
                       "비워두면 저장 위치를 직접 골라 .txt로 추가합니다.",
                  style="Hint.TLabel", wraplength=600, justify="left").pack(anchor="w", pady=(2, 8))

        folder_row = ttk.Frame(body)
        folder_row.pack(fill="x", pady=(0, 8))
        ttk.Label(folder_row, text="자동 저장 폴더").pack(side="left")
        folder_entry = ttk.Entry(folder_row, textvariable=self.paste_add_folder_var, width=40)
        folder_entry.pack(side="left", padx=(6, 4), fill="x", expand=True)

        def 폴더_찾아보기():
            시작 = self.paste_add_folder_var.get() or str(Path.home())
            폴더 = askdirectory(title="자동 저장 폴더 선택", initialdir=시작 if Path(시작).exists() else None,
                                parent=window)
            if 폴더:
                self.paste_add_folder_var.set(폴더)

        ttk.Button(folder_row, text="찾아보기…", command=폴더_찾아보기).pack(side="left", padx=(0, 4))
        ttk.Button(folder_row, text="지정 안 함", command=lambda: self.paste_add_folder_var.set("")).pack(side="left")

        text_frame = ttk.Frame(body)
        text_frame.pack(fill="both", expand=True)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        input_text = tk.Text(text_frame, wrap="word", undo=True, font=("맑은 고딕", 10))
        input_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=input_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        input_text.configure(yscrollcommand=scroll.set)

        status = tk.StringVar(value="텍스트를 붙여넣고 ‘문서로 추가’를 눌러 주세요.")

        def 기본이름(내용):
            for 줄 in 내용.splitlines():
                줄 = 줄.strip()
                if 줄:
                    안전한줄 = re.sub(r'[\\/:*?"<>|]', " ", 줄).strip()
                    return 안전한줄[:40] or "붙여넣은 텍스트"
            return "붙여넣은 텍스트"

        def 겹치지않는경로(폴더, 이름, 확장자):
            대상 = Path(폴더) / f"{이름}{확장자}"
            번호 = 2
            while 대상.exists():
                대상 = Path(폴더) / f"{이름} ({번호}){확장자}"
                번호 += 1
            return 대상

        추가_버튼 = None
        지우기_버튼 = None
        닫기_버튼 = None

        def 버튼상태(상태):
            for 위젯 in (추가_버튼, 지우기_버튼, 닫기_버튼, folder_entry):
                if 위젯 is not None:
                    위젯.config(state=상태)

        def 완료(오류, 대상경로):
            진행중["value"] = False
            if not window.winfo_exists():
                return
            버튼상태("normal")
            if 오류:
                messagebox.showerror(APP_NAME, f"HWPX 변환 중 오류가 발생했습니다.\n\n{오류}", parent=window)
                status.set("HWPX 변환에 실패했습니다.")
                return
            if self.파일추가(str(대상경로)):
                status.set(f"HWPX 문서로 추가했습니다 · {대상경로.name}")
                self.status_var.set(f"{len(self.files)}개 문서 선택")
                self.로그표시(f"텍스트를 HWPX 문서로 추가: {대상경로.name}")
            else:
                status.set("이미 목록에 있는 파일입니다.")

        def 문서로추가():
            내용 = input_text.get("1.0", "end-1c")
            if not 내용.strip():
                status.set("붙여넣은 텍스트가 없습니다.")
                return
            폴더 = self.paste_add_folder_var.get().strip()
            if 폴더:
                if not Path(폴더).is_dir():
                    messagebox.showerror(APP_NAME, f"자동 저장 폴더를 찾을 수 없습니다.\n\n{폴더}", parent=window)
                    return
                if self.running:
                    messagebox.showinfo(APP_NAME, "다른 작업이 실행 중입니다. 완료 후 다시 시도해 주세요.",
                                        parent=window)
                    return
                대상경로 = 겹치지않는경로(폴더, 기본이름(내용), ".hwpx")
                진행중["value"] = True
                버튼상태("disabled")
                status.set("HWPX로 변환하는 중입니다… (한/글이 잠시 열립니다)")

                def 작업():
                    오류 = None
                    try:
                        텍스트_hwpx_단독변환(내용, 대상경로)
                    except Exception as e:
                        오류 = str(e)
                    self.root.after(0, 완료, 오류, 대상경로)
                threading.Thread(target=작업, daemon=True, name="paste-add-hwpx").start()
                return
            경로 = asksaveasfilename(
                parent=window, title="텍스트를 저장할 위치",
                initialfile=기본이름(내용) + ".txt", defaultextension=".txt",
                filetypes=[("텍스트 파일", "*.txt")],
            )
            if not 경로:
                return
            try:
                Path(경로).write_text(내용, encoding="utf-8")
            except OSError as e:
                messagebox.showerror(APP_NAME, f"파일 저장 중 오류가 발생했습니다.\n\n{e}", parent=window)
                return
            if self.파일추가(경로):
                status.set(f"문서로 추가했습니다 · {Path(경로).name}")
                self.status_var.set(f"{len(self.files)}개 문서 선택")
                self.로그표시(f"텍스트를 문서로 추가: {Path(경로).name}")
            else:
                status.set("이미 목록에 있는 파일입니다.")

        def 지우기():
            input_text.delete("1.0", "end")
            status.set("텍스트를 붙여넣고 ‘문서로 추가’를 눌러 주세요.")

        # 입력칸보다 먼저 아래쪽에 자리를 잡아야 화면 배율이 커도 버튼이 가려지지 않는다.
        status_label = ttk.Label(body, textvariable=status, style="Hint.TLabel")
        status_label.pack(side="bottom", anchor="w", pady=(6, 0), before=text_frame)
        actions = ttk.Frame(body)
        actions.pack(side="bottom", fill="x", pady=(8, 0), before=status_label)
        추가_버튼 = ttk.Button(actions, text="문서로 추가", command=문서로추가)
        추가_버튼.pack(side="left")
        지우기_버튼 = ttk.Button(actions, text="지우기", command=지우기)
        지우기_버튼.pack(side="left", padx=(6, 0))
        닫기_버튼 = ttk.Button(actions, text="닫기", command=닫기_요청)
        닫기_버튼.pack(side="right")

        try:
            붙여넣기 = window.clipboard_get()
        except tk.TclError:
            붙여넣기 = ""
        if 붙여넣기.strip():
            input_text.insert("1.0", 붙여넣기)
        input_text.focus_set()

    def _붙여넣기_정리_열기(self):
        """제미나이·클로드·챗GPT 등에서 복사한 답변을 정리한다. 파일을 건드리지 않는다."""
        existing = getattr(self, "_붙여넣기_창", None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            return
        window = tk.Toplevel(self.root)
        self._붙여넣기_창 = window
        window.title("붙여넣은 텍스트 정리")
        window.geometry("900x600")
        window.minsize(560, 380)
        window.transient(self.root)

        def closed():
            self._붙여넣기_창 = None
        window.protocol("WM_DELETE_WINDOW", lambda: (window.destroy(), closed()))

        body = ttk.Frame(window, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="제미나이·클로드·챗GPT 채팅창에서 복사한 답변을 붙여넣으세요.",
                  font=("맑은 고딕", 12, "bold")).pack(anchor="w")
        ttk.Label(body,
                  text="‘한 번에 정리’는 마크다운 기호(**, #, - 등)를 지우고 보기 좋은 문장으로 바꾸고,\n"
                       "‘개조식으로 변환’은 제목·글머리 기호의 계층 구조를 ㅁ/ㅇ/-/• 항목기호로 바꿉니다.\n"
                       "‘제목: / 네모: / 원: / 바:’ 라벨 형식은 라벨 그대로 바꿉니다(‘AI 프롬프트…’로 이 형식의 답을 받을 수 있음).",
                  style="Hint.TLabel", justify="left").pack(anchor="w", pady=(2, 8))

        panes = ttk.Frame(body)
        panes.pack(fill="both", expand=True)
        panes.grid_columnconfigure(0, weight=1)
        panes.grid_columnconfigure(1, weight=1)
        panes.grid_rowconfigure(1, weight=1)

        ttk.Label(panes, text="붙여넣은 텍스트").grid(row=0, column=0, sticky="w")
        ttk.Label(panes, text="정리된 결과").grid(row=0, column=1, sticky="w", padx=(8, 0))

        input_frame = ttk.Frame(panes)
        input_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_rowconfigure(0, weight=1)
        input_text = tk.Text(input_frame, wrap="word", undo=True, font=("맑은 고딕", 10))
        input_text.grid(row=0, column=0, sticky="nsew")
        input_scroll = ttk.Scrollbar(input_frame, orient="vertical", command=input_text.yview)
        input_scroll.grid(row=0, column=1, sticky="ns")
        input_text.configure(yscrollcommand=input_scroll.set)

        output_frame = ttk.Frame(panes)
        output_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 0))
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(0, weight=1)
        output_text = tk.Text(output_frame, wrap="word", font=("맑은 고딕", 10), background="#f7f7f7")
        output_text.grid(row=0, column=0, sticky="nsew")
        output_scroll = ttk.Scrollbar(output_frame, orient="vertical", command=output_text.yview)
        output_scroll.grid(row=0, column=1, sticky="ns")
        output_text.configure(yscrollcommand=output_scroll.set)

        status = tk.StringVar(value="텍스트를 붙여넣고 ‘한 번에 정리’를 눌러 주세요.")

        def 변환실행(변환함수, 완료문구):
            원문 = input_text.get("1.0", "end-1c")
            if not 원문.strip():
                status.set("붙여넣은 텍스트가 없습니다.")
                return
            try:
                결과 = 변환함수(원문)
            except Exception as e:
                messagebox.showerror(APP_NAME, f"텍스트 정리 중 오류가 발생했습니다.\n\n{e}", parent=window)
                return
            output_text.delete("1.0", "end")
            output_text.insert("1.0", 결과)
            status.set(f"{완료문구} · {len(결과)}자")

        def 정리하기():
            변환실행(clean_pasted_text, "정리 완료")

        def 개조식으로변환():
            # 제목:/네모:/원: 같은 라벨 형식이면 계층을 추론하지 않고 라벨대로 바꾼다(A1).
            원문 = input_text.get("1.0", "end-1c")
            if looks_labeled(원문):
                변환실행(label_outline_text, "라벨 형식을 개조식으로 변환 완료")
            else:
                변환실행(outline_pasted_text, "개조식 변환 완료")

        def 결과복사():
            결과 = output_text.get("1.0", "end-1c")
            if not 결과.strip():
                status.set("복사할 정리 결과가 없습니다.")
                return
            window.clipboard_clear()
            window.clipboard_append(결과)
            status.set("정리된 텍스트를 클립보드에 복사했습니다.")

        def 지우기():
            input_text.delete("1.0", "end")
            output_text.delete("1.0", "end")
            status.set("텍스트를 붙여넣고 ‘한 번에 정리’를 눌러 주세요.")

        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="한 번에 정리", command=정리하기).pack(side="left")
        ttk.Button(actions, text="개조식으로 변환", command=개조식으로변환).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="결과 복사", command=결과복사).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="AI 프롬프트…", command=lambda: self._AI_프롬프트_열기(window)).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="지우기", command=지우기).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="닫기", command=lambda: (window.destroy(), closed())).pack(side="right")
        ttk.Label(body, textvariable=status, style="Hint.TLabel").pack(anchor="w", pady=(6, 0))

        try:
            붙여넣기 = window.clipboard_get()
        except tk.TclError:
            붙여넣기 = ""
        if 붙여넣기.strip():
            input_text.insert("1.0", 붙여넣기)
        input_text.focus_set()

    def _AI_프롬프트_열기(self, parent=None):
        """생성형 AI에게 공문서 초안을 라벨 형식으로 받는 프롬프트를 만들어 복사한다(A2).

        앱은 AI 서비스에 아무것도 보내지 않는다. 프롬프트를 클립보드에 복사하고
        원하면 브라우저로 AI 사이트를 열 뿐이다.
        """
        parent = parent or self.root
        window = tk.Toplevel(parent)
        window.title("AI 프롬프트 만들기")
        window.geometry("860x600")
        window.minsize(620, 420)
        window.transient(parent)
        body = ttk.Frame(window, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="AI에게 공문서 초안을 받는 프롬프트", font=("맑은 고딕", 12, "bold")).pack(anchor="w")
        ttk.Label(body, text="메모를 적고 서식을 고른 뒤 ‘프롬프트 복사’를 누르세요. AI 답변을 ‘붙여넣은 텍스트 정리’나 "
                             "‘텍스트 붙여넣기’에 넣으면 라벨대로 개조식·제목 상자로 바뀝니다. 앱은 AI에 아무것도 전송하지 않습니다.",
                  style="Hint.TLabel", wraplength=820, justify="left").pack(anchor="w", pady=(2, 8))
        panes = ttk.Frame(body)
        panes.pack(fill="both", expand=True)
        panes.grid_columnconfigure(1, weight=1)
        panes.grid_rowconfigure(1, weight=1)
        panes.grid_rowconfigure(3, weight=2)
        ttk.Label(panes, text="서식").grid(row=0, column=0, sticky="w")
        목록 = ai_prompts.all_prompts()
        listbox = tk.Listbox(panes, exportselection=False, width=24, font=("맑은 고딕", 10))
        for 이름, 설명, _, 라벨 in 목록:
            listbox.insert("end", 이름 + ("" if 라벨 else "  (문장)"))
        listbox.grid(row=1, column=0, rowspan=3, sticky="nsw", padx=(0, 8))
        ttk.Label(panes, text="메모(업무 내용·일시·장소·대상 등)").grid(row=0, column=1, sticky="w")
        memo = tk.Text(panes, height=6, wrap="word", undo=True, font=("맑은 고딕", 10))
        memo.grid(row=1, column=1, sticky="nsew")
        ttk.Label(panes, text="만들어진 프롬프트").grid(row=2, column=1, sticky="w", pady=(6, 0))
        preview = tk.Text(panes, wrap="word", font=("맑은 고딕", 9), background="#f7f7f7")
        preview.grid(row=3, column=1, sticky="nsew")
        status = tk.StringVar(value="서식을 고르세요.")

        def 갱신(event=None):
            선택 = listbox.curselection()
            if not 선택:
                return
            이름 = 목록[선택[0]][0]
            preview.delete("1.0", "end")
            preview.insert("1.0", ai_prompts.build_prompt(이름, memo.get("1.0", "end-1c")))
            status.set(f"{이름} · {목록[선택[0]][1]}")

        def 복사():
            갱신()
            내용 = preview.get("1.0", "end-1c")
            if not 내용.strip():
                status.set("먼저 서식을 고르세요.")
                return
            window.clipboard_clear()
            window.clipboard_append(내용)
            status.set("프롬프트를 복사했습니다. AI 채팅창에 붙여넣으세요.")

        def 사이트열기(주소):
            복사()
            import webbrowser
            webbrowser.open(주소)

        listbox.bind("<<ListboxSelect>>", 갱신)
        memo.bind("<KeyRelease>", 갱신)
        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="프롬프트 복사", command=복사).pack(side="left")
        for 이름, 주소 in ai_prompts.AI_SITES.items():
            ttk.Button(actions, text=f"복사 후 {이름} 열기", command=lambda u=주소: 사이트열기(u)).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="닫기", command=window.destroy).pack(side="right")
        ttk.Label(body, textvariable=status, style="Hint.TLabel").pack(anchor="w", pady=(6, 0))
        listbox.selection_set(0)
        갱신()
        memo.focus_set()

    def _작성도우미_열기(self):
        """금액·날짜·표 계산·나이·번호·회신공문·기관 서식 도구(B1~B6, A5, A3).

        문서 파일을 직접 바꾸지 않는다. 붙여넣은 텍스트에 적용한 결과를 복사해 쓰게 한다.
        """
        existing = getattr(self, "_작성도우미_창", None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            return
        window = tk.Toplevel(self.root)
        self._작성도우미_창 = window
        window.title("작성 도우미")
        window.geometry("900x640")
        window.minsize(640, 480)
        window.transient(self.root)

        def 닫기():
            window.destroy()
            self._작성도우미_창 = None
        window.protocol("WM_DELETE_WINDOW", 닫기)
        body = ttk.Frame(window, padding=10)
        body.pack(fill="both", expand=True)
        notebook = ttk.Notebook(body)
        notebook.pack(fill="both", expand=True)
        self._작성도우미_탭 = notebook
        status = tk.StringVar(value="탭을 고르고 텍스트를 붙여넣은 뒤 버튼을 누르세요. 결과는 오른쪽에 나옵니다.")
        self._작성도우미_입출력 = {}

        def 입출력탭(제목, 안내, 버튼들, 위쪽=None):
            """왼쪽 입력·오른쪽 결과 텍스트와 변환 버튼 줄로 된 공통 탭."""
            tab = ttk.Frame(notebook, padding=8)
            notebook.add(tab, text=제목)
            ttk.Label(tab, text=안내, style="Hint.TLabel", wraplength=840, justify="left").pack(anchor="w")
            if 위쪽:
                위쪽(tab)
            panes = ttk.Frame(tab)
            panes.pack(fill="both", expand=True, pady=(6, 0))
            panes.grid_columnconfigure(0, weight=1)
            panes.grid_columnconfigure(1, weight=1)
            panes.grid_rowconfigure(0, weight=1)
            src = tk.Text(panes, wrap="word", undo=True, font=("맑은 고딕", 10))
            src.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
            dst = tk.Text(panes, wrap="word", font=("맑은 고딕", 10), background="#f7f7f7")
            dst.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
            row = ttk.Frame(tab)
            row.pack(fill="x", pady=(6, 0))

            def 실행(함수, 이름):
                try:
                    결과 = 함수(src.get("1.0", "end-1c"))
                except Exception as exc:
                    messagebox.showerror(APP_NAME, f"{이름} 중 오류가 발생했습니다.\n\n{exc}", parent=window)
                    return
                dst.delete("1.0", "end")
                dst.insert("1.0", 결과)
                status.set(f"{이름} 완료")

            def 복사():
                내용 = dst.get("1.0", "end-1c")
                if 내용.strip():
                    window.clipboard_clear()
                    window.clipboard_append(내용)
                    status.set("결과를 복사했습니다.")

            명령 = {}
            for 이름, 함수 in 버튼들:
                명령[이름] = lambda f=함수, n=이름: 실행(f, n)
                ttk.Button(row, text=이름, command=명령[이름]).pack(side="left", padx=(0, 6))
            ttk.Button(row, text="결과 복사", command=복사).pack(side="right")
            self._작성도우미_입출력[제목] = (src, dst, 명령)
            return src, dst

        wa = writing_aids

        # B1·B4 금액·숫자
        입출력탭("금액·숫자",
                 "금액(예: 1,500,000원)에 한글 금액을 병기하거나 천 단위 쉼표·단위를 바꿉니다.",
                 [("한글 금액 병기", wa.hangulize_amounts),
                  ("쉼표 넣기", wa.add_commas), ("쉼표 빼기", wa.remove_commas),
                  ("원 → 천원(÷1,000)", lambda t: wa.scale_numbers(t, "0.001")),
                  ("천원 → 원(×1,000)", lambda t: wa.scale_numbers(t, 1000)),
                  ("숫자만 한글로", lambda t: re.sub(r"\d{1,3}(?:,\d{3})+|\d+",
                                                     lambda m: wa.number_to_hangul(int(m.group(0).replace(",", ""))), t))])

        # B2 날짜
        날짜형식 = tk.StringVar(value="full")

        def 날짜옵션(tab):
            box = ttk.Frame(tab)
            box.pack(anchor="w", pady=(4, 0))
            ttk.Label(box, text="표기").pack(side="left")
            for 값, 이름 in (("full", "2025. 7. 25.(금)"), ("short", "’25. 7. 25.(금)"), ("plain", "2025. 7. 25.")):
                ttk.Radiobutton(box, text=이름, value=값, variable=날짜형식).pack(side="left", padx=(6, 0))

        def 기준일(t):
            return wa.parse_date(t) or _datetime.date.today()

        def 금요일들(t, offset):
            d = 기준일(t)
            return "\n".join(wa.format_date(x, 날짜형식.get()) for x in wa.weekdays_in_month(d, 4, offset))

        def 기간(t, kind, offset):
            d = 기준일(t)
            if kind == "week":
                a, b = wa.week_of(d, offset)
            elif kind == "month":
                a, b = wa.month_bounds(d, offset)
            else:
                a, b = _datetime.date(d.year + offset, 1, 1), _datetime.date(d.year + offset, 12, 31)
            return wa.date_range_text(a, b, 날짜형식.get())

        def 날짜차이(t):
            찾은 = [wa.parse_date(m.group(0)) for m in wa._DATE.finditer(t)]
            찾은 = [x for x in 찾은 if x]
            if len(찾은) < 2:
                return "날짜 두 개를 입력하세요. 예: 2025. 7. 1. ~ 2025. 7. 25."
            a, b = 찾은[:2]
            return (f"{wa.format_date(a, 날짜형식.get())} ~ {wa.format_date(b, 날짜형식.get())}: "
                    f"{wa.days_between(a, b)}일 차이(양 끝 포함 {wa.days_between(a, b, True)}일)")

        입출력탭("날짜",
                 "문장 속 날짜에 요일을 붙이거나(틀린 요일은 고침), 입력한 날짜(없으면 오늘)를 기준으로 날짜를 만듭니다.",
                 [("요일 붙이기·고치기", wa.add_weekdays),
                  ("오늘", lambda t: wa.format_date(_datetime.date.today(), 날짜형식.get())),
                  ("이번 달 금요일", lambda t: 금요일들(t, 0)), ("다음 달 금요일", lambda t: 금요일들(t, 1)),
                  ("다음 주", lambda t: 기간(t, "week", 1)), ("이번 달 기간", lambda t: 기간(t, "month", 0)),
                  ("다음 달 기간", lambda t: 기간(t, "month", 1)), ("올해 기간", lambda t: 기간(t, "year", 0)),
                  ("날짜 차이", 날짜차이)], 날짜옵션)

        # B3 표 계산
        def 표계산(op):
            return lambda t: wa.table_to_text(wa.calc_table(wa.parse_table(t), op))
        입출력탭("표 계산",
                 "한/글·엑셀 표를 복사해 붙여넣으세요(칸은 탭 또는 |). 첫 행·첫 열이 글자면 머리글로 보고 계산에서 뺍니다. "
                 "결과를 복사해 한/글 표에 붙여넣으면 됩니다.",
                 [("열 합계", 표계산("col_sum")), ("열 평균", 표계산("col_avg")),
                  ("행 합계", 표계산("row_sum")), ("구성비(%)", 표계산("col_ratio"))])

        # B5 나이·주민번호
        입출력탭("나이·주민번호",
                 "줄마다 생년월일이나 주민등록번호를 찾아 만 나이를 붙입니다. 주민등록번호는 결과에서 뒷자리를 가립니다.",
                 [("만 나이 붙이기", wa.ages_for_lines), ("주민번호 → 생년월일", wa.rrn_to_birth_lines),
                  ("주민번호 가리기", wa.mask_rrn)])

        # B6 번호
        번호형식 = tk.StringVar(value="1.")

        def 번호옵션(tab):
            box = ttk.Frame(tab)
            box.pack(anchor="w", pady=(4, 0))
            ttk.Label(box, text="번호 모양").pack(side="left")
            ttk.Combobox(box, textvariable=번호형식, values=list(wa.NUMBER_STYLES), width=6,
                         state="readonly").pack(side="left", padx=(6, 0))
        입출력탭("번호",
                 "줄마다 기존 번호를 지우고 새 번호를 차례로 붙입니다(빈 줄은 건너뜀).",
                 [("번호 다시 매기기", lambda t: wa.renumber_lines(t, 번호형식.get())),
                  ("번호 지우기", lambda t: "\n".join(wa._EXISTING_NUMBER.sub("", l) for l in t.splitlines()))], 번호옵션)

        # A5 회신공문
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="회신공문")
        ttk.Label(tab, text="요청 공문 정보를 넣으면 ‘관련 → 제출 → 붙임 … 끝.’ 형식의 회신 공문 본문을 만듭니다.",
                  style="Hint.TLabel").pack(anchor="w")
        form = ttk.Frame(tab)
        form.pack(fill="x", pady=(6, 0))
        form.grid_columnconfigure(1, weight=1)
        값들 = {}
        for 순번, (키, 이름, 예시) in enumerate((
                ("title", "요청 공문 제목", "2025년 하반기 교육 실적 자료 제출 요청"),
                ("sender", "요청 기관·부서", "행정안전부 인재개발과"),
                ("doc_no", "문서번호", "인재개발과-1234"),
                ("doc_date", "시행일", "2025. 7. 1."),
                ("attachment", "붙임 이름(선택)", ""),
                ("contact", "문의처(선택)", ""))):
            ttk.Label(form, text=이름).grid(row=순번, column=0, sticky="w", pady=2)
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var).grid(row=순번, column=1, sticky="ew", padx=(8, 0), pady=2)
            if 예시:
                ttk.Label(form, text=f"예: {예시}", style="Hint.TLabel").grid(row=순번, column=2, sticky="w", padx=(8, 0))
            값들[키] = var
        회신결과 = tk.Text(tab, wrap="word", font=("맑은 고딕", 10), background="#f7f7f7", height=10)
        회신결과.pack(fill="both", expand=True, pady=(6, 0))

        def 회신만들기():
            if not 값들["title"].get().strip():
                status.set("요청 공문 제목을 입력하세요.")
                return
            결과 = wa.reply_document(값들["title"].get(), 값들["sender"].get().strip(), 값들["doc_no"].get().strip(),
                                    값들["doc_date"].get().strip(), 값들["attachment"].get(), 값들["contact"].get())
            회신결과.delete("1.0", "end")
            회신결과.insert("1.0", 결과)
            status.set("회신공문 본문을 만들었습니다.")

        def 회신복사():
            window.clipboard_clear()
            window.clipboard_append(회신결과.get("1.0", "end-1c"))
            status.set("회신공문 본문을 복사했습니다.")
        self._작성도우미_회신 = (값들, 회신결과, 회신만들기)
        row = ttk.Frame(tab)
        row.pack(fill="x", pady=(6, 0))
        ttk.Button(row, text="회신공문 만들기", command=회신만들기).pack(side="left")
        ttk.Button(row, text="결과 복사", command=회신복사).pack(side="right")

        # A3 기관 서식
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="기관 서식")
        ttk.Label(tab, text="기관 문서(HWP/HWPX)의 모든 스타일 요소를 분석해 보고서와 예시 서식 HWPX를 원본 옆에 만들고, "
                            "기관 이름을 붙여 문서 서식으로 등록합니다. 등록한 서식은 서식 목록에 ‘[기관] 이름’으로 보입니다.",
                  style="Hint.TLabel", wraplength=840, justify="left").pack(anchor="w")
        기관문서 = tk.StringVar()
        기관이름 = tk.StringVar()
        form = ttk.Frame(tab)
        form.pack(fill="x", pady=(8, 0))
        form.grid_columnconfigure(1, weight=1)
        ttk.Label(form, text="기관 문서").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=기관문서).grid(row=0, column=1, sticky="ew", padx=(8, 4))

        def 문서고르기():
            경로 = askopenfilename(parent=window, title="기관 문서", filetypes=[("한글파일", "*.hwp *.hwpx")])
            if 경로:
                기관문서.set(경로)
                예시경로["path"] = None
        ttk.Button(form, text="찾아보기…", command=문서고르기).grid(row=0, column=2)
        ttk.Label(form, text="기관 이름").grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(form, textvariable=기관이름).grid(row=1, column=1, sticky="ew", padx=(8, 4), pady=(4, 0))
        분석결과 = tk.Text(tab, wrap="word", font=("맑은 고딕", 10), background="#f7f7f7", height=14)
        분석결과.pack(fill="both", expand=True, pady=(8, 0))
        예시경로 = {"path": None, "report": None}

        def 분석하기(등록=False):
            경로 = 기관문서.get().strip()
            if not 경로 or not Path(경로).exists():
                status.set("기관 문서를 고르세요.")
                return
            if self.running:
                status.set("다른 작업이 끝난 뒤 다시 시도하세요.")
                return
            status.set("스타일을 분석하는 중입니다… (HWP는 한/글로 임시 변환)")

            def worker():
                try:
                    결과 = 스타일분석_파일생성(경로)
                    self.root.after(0, 분석완료, 결과, 등록, None)
                except Exception as exc:
                    self.root.after(0, 분석완료, None, False, str(exc))
            threading.Thread(target=worker, daemon=True, name="style-inventory").start()

        def 분석완료(결과, 등록, error):
            if not window.winfo_exists():
                return
            if error:
                status.set("스타일 분석 실패")
                messagebox.showerror(APP_NAME, f"스타일 분석 실패\n{error}", parent=window)
                return
            inventory, stats, report, sample = 결과
            예시경로.update(path=sample, report=report)
            분석결과.delete("1.0", "end")
            분석결과.insert("1.0", 스타일분석_요약(inventory, stats, report, sample))
            status.set("스타일 분석 완료")
            if 등록:
                등록하기()

        def 등록하기():
            if not 예시경로["path"]:
                분석하기(등록=True)
                return
            기관 = 기관이름.get().strip()
            줄기 = Path(기관문서.get()).stem
            기본 = f"{기관} {줄기}" if 기관 and 기관 not in 줄기 else 줄기
            self._서식_분석_시작(str(예시경로["path"]), 이름묻기=True, 기본이름=기본[:40], 기관=기관)

        def 보고서열기():
            if 예시경로["report"]:
                os.startfile(str(예시경로["report"]))

        row = ttk.Frame(tab)
        row.pack(fill="x", pady=(6, 0))
        ttk.Button(row, text="스타일 분석", command=분석하기).pack(side="left")
        ttk.Button(row, text="기관 서식으로 등록", command=등록하기).pack(side="left", padx=(6, 0))
        ttk.Button(row, text="보고서 열기", command=보고서열기).pack(side="left", padx=(6, 0))

        bottom = ttk.Frame(body)
        bottom.pack(fill="x", pady=(6, 0))
        ttk.Label(bottom, textvariable=status, style="Hint.TLabel").pack(side="left")
        ttk.Button(bottom, text="닫기", command=닫기).pack(side="right")

    def _공공언어_검토(self):
        if getattr(self, "_교정_창", None) is not None:
            self._교정_창.lift()
            return
        if self.running or getattr(self, "_서식분석중", False) or getattr(self, "_교정_작업중", False):
            return
        if not self.files:
            messagebox.showinfo(APP_NAME, "먼저 검토할 HWP/HWPX 파일을 추가해 주세요.", parent=self.root)
            return
        try:
            제외경로 = 설정_폴더() / "proofreading_exclusions.json"
            self._교정_제외 = load_exclusions(제외경로)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"교정 제외 목록을 읽지 못했습니다.\n{exc}", parent=self.root)
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("공공언어 바로쓰기 · 한국어 문서 교정")
        dialog.geometry("1050x610")
        dialog.transient(self.root)
        self._교정_창 = dialog
        self._교정_임시폴더 = tempfile.TemporaryDirectory(prefix="docfit_proofread_")
        self._교정_후보 = []
        self._교정_대상 = {}
        body = ttk.Frame(dialog, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="로컬 공공언어·맞춤법 검토", font=("맑은 고딕", 14, "bold")).pack(anchor="w")
        ttk.Label(body, text="문서를 외부에 전송하지 않습니다. 교정안은 제안이며, 선택한 항목만 원본과 별도 HWPX로 저장합니다.",
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 8))
        frame = ttk.Frame(body)
        frame.pack(fill="both", expand=True)
        columns = ("file", "category", "source", "suggestion", "count", "reason", "context")
        labels = ("파일", "유형", "검출 표현", "교정 제안", "횟수", "검토 이유", "문맥")
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
        self._교정_목록 = tree
        for key, label in zip(columns, labels):
            tree.heading(key, text=label)
            tree.column(key, width=270 if key in ("file", "context") else 100, anchor="w")
        ybar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        xbar = ttk.Scrollbar(body, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.pack(side="left", fill="both", expand=True)
        ybar.pack(side="right", fill="y")
        xbar.pack(fill="x")
        상태 = tk.StringVar(value="선택한 문서를 검사하고 있습니다…")
        self._교정_상태 = 상태
        ttk.Label(body, textvariable=상태, style="Hint.TLabel").pack(anchor="w", pady=(8, 4))
        controls = ttk.Frame(body)
        controls.pack(fill="x")
        ttk.Button(controls, text="모두 선택", command=lambda: tree.selection_set(*tree.get_children())).pack(side="left")
        ttk.Button(controls, text="선택 해제", command=lambda: tree.selection_remove(*tree.selection())).pack(side="left", padx=5)
        ttk.Button(controls, text="선택 표현 이후 검색에서 제외", command=self._교정_선택제외).pack(side="left", padx=5)
        ttk.Button(controls, text="제외 목록 관리", command=self._교정_제외관리).pack(side="left", padx=5)
        ttk.Button(controls, text="선택 교정 승인·새 파일 저장", command=self._교정_승인).pack(side="right")
        def close():
            if getattr(self, "_교정_작업중", False):
                messagebox.showinfo(APP_NAME, "검사 또는 저장이 끝난 뒤 닫아 주세요.", parent=dialog)
                return
            self._교정_임시폴더.cleanup()
            self._교정_창 = None
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", close)
        self._교정_작업중 = True
        sources = list(self.files)
        def worker():
            candidates, snapshots, errors = [], {}, []
            for source in sources:
                try:
                    snapshot = 교정용_hwpx_준비(source, self._교정_임시폴더.name)
                    snapshots[source] = snapshot
                    for item in scan_hwpx(snapshot, self._교정_제외):
                        candidates.append({**item, "source_path": source})
                except Exception as exc:
                    errors.append((source, str(exc)))
            gui_queue.put(("proofread_scan_done", candidates, snapshots, errors))
        threading.Thread(target=worker, daemon=True).start()

    def _교정_목록갱신(self):
        tree = self._교정_목록
        children = tree.get_children()
        if children:
            tree.delete(*children)
        for index, item in enumerate(self._교정_후보):
            tree.insert("", "end", iid=str(index), values=(
                Path(item["source_path"]).name, item["category"], item["source"],
                item["suggestion"], item["count"], item["reason"],
                item["examples"][0] if item["examples"] else ""))

    def _교정_선택제외(self):
        if getattr(self, "_교정_작업중", False): return
        selected = {int(item) for item in self._교정_목록.selection()}
        if not selected:
            messagebox.showinfo(APP_NAME, "제외할 표현을 선택해 주세요.", parent=self._교정_창)
            return
        expressions = {self._교정_후보[index]["source"] for index in selected}
        updated = self._교정_제외 | expressions
        try:
            save_exclusions(설정_폴더() / "proofreading_exclusions.json", updated)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"제외 목록 저장 실패\n{exc}", parent=self._교정_창)
            return
        self._교정_제외 = updated
        self._교정_후보 = [item for item in self._교정_후보 if item["source"] not in updated]
        self._교정_목록갱신()
        self._교정_상태.set(f"{len(expressions)}개 표현을 이후 검색에서 제외합니다. 남은 후보 {len(self._교정_후보)}개")

    def _교정_제외관리(self):
        if getattr(self, "_교정_작업중", False): return
        dialog = tk.Toplevel(self._교정_창)
        dialog.title("교정 제외 목록")
        dialog.geometry("430x420")
        dialog.transient(self._교정_창)
        dialog.grab_set()
        body = ttk.Frame(dialog, padding=10)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="검색에서 제외한 표현을 선택해 다시 포함할 수 있습니다.").pack(anchor="w")
        listing = tk.Listbox(body, selectmode="extended")
        listing.pack(fill="both", expand=True, pady=8)
        for item in sorted(self._교정_제외): listing.insert("end", item)
        def restore():
            chosen = {listing.get(index) for index in listing.curselection()}
            if not chosen: return
            try:
                save_exclusions(설정_폴더() / "proofreading_exclusions.json", self._교정_제외 - chosen)
            except Exception as exc:
                messagebox.showerror(APP_NAME, str(exc), parent=dialog)
                return
            self._교정_제외 -= chosen
            dialog.destroy()
            messagebox.showinfo(APP_NAME, "복원한 표현은 다음 검사부터 다시 검색됩니다.", parent=self._교정_창)
        ttk.Button(body, text="선택 표현 다시 검색", command=restore).pack(side="right")

    def _교정_승인(self):
        if getattr(self, "_교정_작업중", False): return
        selected = [self._교정_후보[int(index)] for index in self._교정_목록.selection()]
        if not selected:
            messagebox.showinfo(APP_NAME, "승인할 교정 항목을 선택해 주세요.", parent=self._교정_창)
            return
        grouped = defaultdict(set)
        for item in selected:
            grouped[item["source_path"]].add(item["rule_id"])
        self._교정_작업중 = True
        self._교정_상태.set("승인한 교정안을 새 HWPX 파일에 저장하고 있습니다…")
        def worker():
            results, errors = [], []
            for source, rule_ids in grouped.items():
                try:
                    original = Path(source)
                    base = original.with_name(original.stem + "_공공언어교정.hwpx")
                    target = base
                    number = 2
                    while target.exists():
                        target = base.with_name(base.stem + f" ({number})" + base.suffix)
                        number += 1
                    count = apply_approved_hwpx(self._교정_대상[source], target, rule_ids, self._교정_제외)
                    results.append((str(target), count))
                except Exception as exc:
                    errors.append((source, str(exc)))
            gui_queue.put(("proofread_apply_done", results, errors))
        threading.Thread(target=worker, daemon=True).start()

    def _서식_복사하기(self):
        if self.running or getattr(self, "_서식분석중", False): return
        path = askopenfilename(parent=self.settings_toplevel, title="서식을 복사할 한글파일",
                               filetypes=[("한글파일·PDF", "*.hwp *.hwpx *.pdf")])
        if not path: return
        self._서식_분석_시작(path, 이름묻기=True)

    def _서식_분석_시작(self, path, 이름묻기=False, 기본이름=None, 기관=None):
        if self.running or getattr(self, "_서식분석중", False):
            return
        parent = self.settings_toplevel if self.settings_toplevel and self.settings_toplevel.winfo_viewable() else self.root
        name = 기본이름 or Path(path).stem
        if 이름묻기:
            name = simpledialog.askstring(APP_NAME, "새 문서 서식 이름", parent=parent, initialvalue=name)
        if name is None: return
        name = name.strip()
        if not name:
            messagebox.showwarning(APP_NAME, "비어 있지 않은 이름을 입력해 주세요.", parent=parent)
            return
        if 이름묻기:
            기관 = simpledialog.askstring(APP_NAME, "기관 이름(선택, 비워 두면 기관 없음)", parent=parent,
                                         initialvalue=기관 or "")
            if 기관 is None: return
        기관 = (기관 or "").strip()
        기존이름 = {p["name"] for p in self._프로파일들.values()}
        if name in 기존이름:
            if 이름묻기:
                messagebox.showwarning(APP_NAME, "이미 사용 중인 서식 이름입니다.", parent=parent)
                return
            기본이름, 순번 = name, 2
            while name in 기존이름:
                name = f"{기본이름} ({순번})"
                순번 += 1
        self._서식분석중 = True
        self._서식분석_파일 = Path(path).name
        if getattr(self, "copy_format_button", None) is not None:
            self.copy_format_button.config(state="disabled")
        if hasattr(self, "format_drop_label"):
            self.format_drop_label.configure(text=f"분석 중 · {Path(path).name}")
        self.status_var.set("문서 서식을 분석하고 있습니다…")
        def worker():
            try:
                result = 한글파일_서식_분석(path)
                result["name"] = name
                if 기관:
                    result["organization"] = 기관
                gui_queue.put(("format_copied", result))
            except Exception as exc:
                gui_queue.put(("format_copy_error", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def 서식파일_드롭(self, event):
        if self.running or getattr(self, "_서식분석중", False):
            return
        try:
            items = self.root.tk.splitlist(event.data)
        except Exception:
            items = [event.data]
        candidates = [str(item).strip() for item in items if Path(str(item).strip()).suffix.lower() in (".hwp", ".hwpx", ".pdf")]
        if not candidates:
            messagebox.showwarning(APP_NAME, "HWP 또는 HWPX 예시 문서를 놓아 주세요.", parent=self.root)
            return
        self.selected_mode.set(self._한번에_모드())
        self._서식_분석_시작(candidates[0], 이름묻기=False)

    def _서식_복사완료(self, profile=None, error=None):
        self._서식분석중 = False
        self._서식분석_파일 = ""
        if getattr(self, "copy_format_button", None) is not None:
            self.copy_format_button.config(state="normal")
        parent = self._서식창_부모()
        if error:
            self.status_var.set(f"서식 분석 실패: {error}")
            if hasattr(self, "format_drop_label"):
                self.format_drop_label.configure(text="예시 HWP/HWPX를 여기에 놓으면 분석 후 바로 선택합니다")
            if not self._웹화면_모드():
                messagebox.showerror(APP_NAME, f"서식 복사 실패\n{error}", parent=parent)
            return
        # 예시 문서의 서식 요소 분석 결과가 있으면 이름·세부값을 고치는 세부사항 창을 먼저 보인다
        # (계층 구조 검토는 그 창의 버튼으로 연다).
        if profile.get("element_analysis"):
            확인됨 = self._서식_세부사항_확인(profile, parent, {p["name"] for p in self._프로파일들.values()})
        else:
            확인됨 = self._서식_구조_확인(profile, parent)
        if not 확인됨:
            self.status_var.set("서식 추가를 취소했습니다.")
            return
        identifier = uuid.uuid4().hex
        folder = 서식프로파일_폴더()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            temp = folder / (identifier + ".tmp")
            temp.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, folder / (identifier + ".json"))
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"서식 저장 실패\n{exc}", parent=parent)
            return
        self._프로파일들[identifier] = profile
        self._활성_서식_프로파일 = identifier
        self._프로파일_목록갱신()
        self._프로파일_선택()
        self.selected_mode.set(self._한번에_모드())
        if hasattr(self, "format_drop_label"):
            self.format_drop_label.configure(text=f"적용 준비 완료 · {profile['name']}")
        self.status_var.set(f"새 문서 서식 추가: {profile['name']}")
        if not self._웹화면_모드():
            messagebox.showinfo(APP_NAME, f"'{profile['name']}' 서식을 저장하고 선택했습니다.\n\n{profile['summary']}",
                                parent=parent)

    def _서식_세부사항_확인(self, profile, parent, 다른이름=()):
        """예시 문서에서 분석한 서식 요소의 대표값을 보여 주고, 서식 이름과 세부값을 고치게 한다.

        왼쪽은 영역(쪽 여백·항목기호 문장 계층·서식 표의 칸(A1·A2·B2 …)과 칸 문단·일반 표), 오른쪽은 그
        영역의 요소별 대표값·표본 수·다른 값이다. '확인하고 서식 저장'을 누르면 고친 값을 서식 적용 값과
        보관한 서식 표 예시에 반영한다. 취소하면 profile을 바꾸지 않는다.
        """
        작업본 = copy.deepcopy(profile)
        analysis = 작업본.setdefault("element_analysis", {})
        dialog = tk.Toplevel(parent)
        dialog.title(f"서식 세부사항 검토·수정 · {profile.get('name', '')}")
        dialog.geometry("1120x720")
        dialog.transient(parent)
        dialog.grab_set()
        창_맨앞으로(dialog)
        body = ttk.Frame(dialog, padding=14)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="서식 세부사항", font=("맑은 고딕", 14, "bold")).pack(anchor="w")
        ttk.Label(body, text="예시 문서에서 가장 많이 쓴 값이 대표값입니다. 왼쪽에서 영역을 고르고 항목 값을 바꾸면, "
                             "이 서식으로 문서를 정리할 때 바꾼 값을 씁니다. 글자·문단 크기는 pt, 표·칸 치수는 mm입니다.",
                  style="Hint.TLabel", wraplength=1080, justify="left").pack(anchor="w", pady=(2, 8))
        이름줄 = ttk.Frame(body)
        이름줄.pack(fill="x")
        ttk.Label(이름줄, text="서식 이름").pack(side="left")
        이름 = tk.StringVar(value=str(profile.get("name") or ""))
        ttk.Entry(이름줄, textvariable=이름, width=32).pack(side="left", padx=(6, 18))
        ttk.Label(이름줄, text="기관(선택)").pack(side="left")
        기관 = tk.StringVar(value=str(profile.get("organization") or ""))
        ttk.Entry(이름줄, textvariable=기관, width=22).pack(side="left", padx=6)

        panes = ttk.PanedWindow(body, orient="horizontal")
        panes.pack(fill="both", expand=True, pady=(10, 0))
        왼쪽, 오른쪽 = ttk.Frame(panes), ttk.Frame(panes)
        panes.add(왼쪽, weight=1)
        panes.add(오른쪽, weight=3)
        영역목록 = ttk.Treeview(왼쪽, show="tree", selectmode="browse")
        영역목록.column("#0", width=330)
        영역바 = ttk.Scrollbar(왼쪽, orient="vertical", command=영역목록.yview)
        영역목록.configure(yscrollcommand=영역바.set)
        영역목록.pack(side="left", fill="both", expand=True)
        영역바.pack(side="right", fill="y")
        목록틀 = ttk.Frame(오른쪽)
        목록틀.pack(fill="both", expand=True)
        columns = ("label", "value", "mode", "share", "others")
        요소목록 = ttk.Treeview(목록틀, columns=columns, show="headings", selectmode="browse")
        요소바 = ttk.Scrollbar(목록틀, orient="vertical", command=요소목록.yview)
        요소목록.configure(yscrollcommand=요소바.set)
        for key, heading, width in (("label", "항목", 210), ("value", "대표값", 180), ("mode", "적용 방식", 80),
                                    ("share", "표본(같은 값/전체)", 120), ("others", "다른 값(횟수)", 260)):
            요소목록.heading(key, text=heading)
            요소목록.column(key, width=width, anchor="w")
        요소목록.pack(side="left", fill="both", expand=True)
        요소바.pack(side="right", fill="y")
        편집 = ttk.LabelFrame(오른쪽, text="선택한 항목 값 바꾸기", padding=8)
        편집.pack(fill="x", pady=(8, 0))
        항목이름 = tk.StringVar(value="오른쪽 목록에서 항목을 고르세요")
        ttk.Label(편집, textvariable=항목이름, width=30).grid(row=0, column=0, sticky="w")
        값 = tk.StringVar()
        값상자 = ttk.Combobox(편집, textvariable=값, width=34, state="disabled")
        값상자.grid(row=0, column=1, padx=6)
        현재 = {"path": None, "key": None}
        경로들 = {}

        def 노드키(경로):
            return "/".join(map(str, 경로))

        for 경로, 상위, 글 in 서식요소.detail_nodes(analysis):
            경로들[노드키(경로)] = 경로
            영역목록.insert(노드키(상위) if 상위 else "", "end", iid=노드키(경로), text=글,
                           open=len(경로) <= 2)

        def 요소_표시(path, 고를=None):
            요소목록.delete(*요소목록.get_children())
            for key, item in 서식요소.element_map(analysis, path).items():
                기준값 = item.get("analyzed", item["value"])
                다른값 = ", ".join(f"{서식요소.format_value(key, v)}({n})"
                                  for v, n in item.get("variants", []) if v != 기준값)
                표본 = f"{item.get('votes', 0)}/{item.get('total', 0)} ({item.get('share', 0):.0%})"
                표시 = 서식요소.format_value(key, item["value"])
                if item.get("edited"):
                    표시 += f"  (분석값 {서식요소.format_value(key, 기준값)})"
                이름글 = 서식요소.element_label(key) + ("" if 서식요소.element_editable(key) else " · 표시만")
                요소목록.insert("", "end", iid=key,
                                values=(이름글, 표시, 서식요소.element_mode(key, path), 표본, 다른값))
            if 고를 and 요소목록.exists(고를):
                요소목록.selection_set(고를)

        def 영역_선택(event=None):
            picked = 영역목록.selection()
            if not picked:
                return
            현재.update(path=경로들[picked[0]], key=None)
            요소_표시(현재["path"])
            항목이름.set("오른쪽 목록에서 항목을 고르세요")
            값.set("")
            값상자.configure(state="disabled", values=())

        def 요소_선택(event=None):
            picked = 요소목록.selection()
            if not picked or 현재["path"] is None:
                return
            key = picked[0]
            item = 서식요소.element_map(analysis, 현재["path"]).get(key)
            if item is None:
                return
            현재["key"] = key
            항목이름.set(서식요소.element_label(key))
            선택지 = 서식요소.element_choices(key)
            if key.startswith("border_"):
                선택지 = ("없음", "실선 0.12 mm #000000", "실선 0.4 mm #000000", "이중 실선 0.5 mm #000000")
            elif not 선택지:
                선택지 = tuple(서식요소.format_value(key, v) for v, _ in item.get("variants", []))
            상태값 = ("disabled" if not 서식요소.element_editable(key)
                     else "readonly" if 서식요소.element_choices(key) else "normal")
            값상자.configure(values=선택지, state=상태값)
            값.set(서식요소.format_value(key, item["value"]))

        def 값_바꾸기(event=None):
            key, path = 현재["key"], 현재["path"]
            if key is None or path is None or not 서식요소.element_editable(key):
                return
            try:
                새값 = 서식요소.parse_value(key, 값.get())
            except ValueError as exc:
                messagebox.showerror(APP_NAME, str(exc), parent=dialog)
                return
            서식요소.set_value(analysis, path, key, 새값)
            요소_표시(path, key)

        def 분석값으로():
            key, path = 현재["key"], 현재["path"]
            item = 서식요소.element_map(analysis, path).get(key) if key else None
            if item and "analyzed" in item:
                서식요소.set_value(analysis, path, key, item["analyzed"])
                요소_표시(path, key)
                값.set(서식요소.format_value(key, item["value"]))

        영역목록.bind("<<TreeviewSelect>>", 영역_선택)
        요소목록.bind("<<TreeviewSelect>>", 요소_선택)
        값상자.bind("<Return>", 값_바꾸기)
        ttk.Button(편집, text="값 바꾸기", command=값_바꾸기).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(편집, text="분석값으로 되돌리기", command=분석값으로).grid(row=0, column=3)
        첫영역 = next((iid for iid, path in 경로들.items() if 서식요소.element_map(analysis, path)), None)
        if 첫영역:
            영역목록.see(첫영역)
            영역목록.selection_set(첫영역)
            영역_선택()
        result = {"confirmed": False}

        def 계층검토():
            이전 = copy.deepcopy((작업본.get("style_hierarchy") or {}).get("styles", []))
            if self._서식_구조_확인(작업본, dialog):
                서식요소.sync_from_hierarchy(작업본, 이전)
                if 현재["path"] is not None:
                    요소_표시(현재["path"], 현재["key"])

        def 닫기(confirmed=False):
            if confirmed:
                새이름 = 이름.get().strip()
                if not 새이름:
                    messagebox.showwarning(APP_NAME, "서식 이름을 입력해 주세요.", parent=dialog)
                    return
                if 새이름 in set(다른이름):
                    messagebox.showwarning(APP_NAME, "이미 사용 중인 서식 이름입니다.", parent=dialog)
                    return
                작업본["name"] = 새이름
                if 기관.get().strip():
                    작업본["organization"] = 기관.get().strip()
                else:
                    작업본.pop("organization", None)
                try:
                    서식요소.apply_to_profile(작업본)
                except Exception as exc:
                    messagebox.showerror(APP_NAME, f"세부사항을 서식에 반영하지 못했습니다.\n{exc}", parent=dialog)
                    return
                앞부분 = str(작업본.get("summary", "")).split("\n\n서식 요소 대표값", 1)[0]
                작업본["summary"] = (앞부분 + "\n\n서식 요소 대표값\n"
                                   + "\n".join(서식요소.summary_lines(analysis)))
                profile.clear()
                profile.update(작업본)
                result["confirmed"] = True
            dialog.destroy()

        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="계층 구조 검토…", command=계층검토).pack(side="left")
        ttk.Button(buttons, text="취소", command=닫기).pack(side="right")
        ttk.Button(buttons, text="확인하고 서식 저장", command=lambda: 닫기(True)).pack(side="right", padx=8)
        dialog.protocol("WM_DELETE_WINDOW", 닫기)
        parent.wait_window(dialog)
        return result["confirmed"]

    def _서식_구조_확인(self, profile, parent):
        """Review and edit every repeated or one-off hierarchy style before saving."""
        hierarchy = profile.setdefault("style_hierarchy", {"styles": []})
        if not hierarchy.get("styles") and (
                not hierarchy.get("variants")
                or (not hierarchy.get("reviewed")
                    and all(row.get("kind") == "기본값" for row in hierarchy["variants"]))):
            # 아직 검토·저장하지 않은 기본값 행은 매번 새로 만든다(예전에 장·중제목 없이 만든 행도 바로잡힌다).
            hierarchy["variants"] = 기본_계층_스타일(profile["format"])
        if not hierarchy.get("variants"):
            hierarchy["variants"] = [
                {"role": item["role"], "marker": item["marker"],
                 "count": item["count"], "kind": "반복" if item["count"] > 1 else "비반복",
                 "font": item.get("font"), "size_pt": item.get("size_pt") or 12,
                 "left_hwpunit": item.get("left_hwpunit", 0),
                 "first_line_hwpunit": item.get("first_line_hwpunit", 0),
                 "prev_spacing_hwpunit": item.get("prev_spacing_typical") or 0}
                for item in hierarchy.get("styles", [])]
        rows = copy.deepcopy(hierarchy["variants"])
        dialog = tk.Toplevel(parent)
        dialog.title(f"서식 구조 검토·수정 · {profile['name']}")
        dialog.geometry("1050x690")
        dialog.transient(parent)
        dialog.grab_set()
        창_맨앞으로(dialog)
        body = ttk.Frame(dialog, padding=14)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="계층별 문서 스타일 검토",
                  font=("맑은 고딕", 14, "bold")).pack(anchor="w")
        ttk.Label(body, text="반복·비반복 스타일을 모두 표시합니다. 항목을 선택해 수정하고, 적용할 속성만 체크하세요. 값의 단위는 pt입니다.",
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 10))
        frame = ttk.Frame(body)
        frame.pack(fill="both", expand=True)
        columns = ("kind", "count", "role", "marker", "font", "size", "left", "indent", "spacing")
        headings = ("유형", "횟수", "계층", "항목기호", "글꼴", "크기", "왼쪽 여백", "첫 줄 들여쓰기", "문단 위 여백")
        details = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        bar = ttk.Scrollbar(frame, orient="vertical", command=details.yview)
        details.configure(yscrollcommand=bar.set)
        for key, heading in zip(columns, headings):
            details.heading(key, text=heading)
            details.column(key, width=110 if key == "font" else 85, anchor="center")
        details.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        def display(index):
            row = rows[index]
            return (row["kind"], row["count"], display_role(row["role"]), row["marker"], row.get("font") or "",
                    f"{float(row.get('size_pt') or 0):g}",
                    f"{float(row.get('left_hwpunit') or 0) / 100:g}",
                    f"{float(row.get('first_line_hwpunit') or 0) / 100:g}",
                    f"{float(row.get('prev_spacing_hwpunit') or 0) / 100:g}")
        for index in range(len(rows)):
            details.insert("", "end", iid=str(index), values=display(index))
        editor = ttk.LabelFrame(body, text="선택한 스타일 수정 및 속성별 적용", padding=8)
        editor.pack(fill="x", pady=(8, 0))
        variables = {key: tk.StringVar() for key in ("role", "font", "size", "left", "indent", "spacing")}
        selection = {key: tk.BooleanVar(value=True) for key in STYLE_FIELDS}
        ttk.Label(editor, text="계층").grid(row=0, column=0, padx=3)
        ttk.Combobox(editor, textvariable=variables["role"], values=tuple(map(display_role, STYLE_ROLES)),
                     state="readonly", width=10).grid(row=1, column=0, padx=3)
        labels = (("font", "글꼴"), ("size", "크기"), ("left", "왼쪽 여백"),
                  ("indent", "첫 줄 들여쓰기"), ("spacing", "문단 위 여백"))
        for column, (key, label) in enumerate(labels, 1):
            ttk.Label(editor, text=label).grid(row=0, column=column, padx=3)
            ttk.Entry(editor, textvariable=variables[key], width=14).grid(row=1, column=column, padx=3)
        for column, (key, label) in enumerate((("font", "글꼴 적용"), ("size", "크기 적용"),
                                               ("indent", "들여쓰기 적용"), ("spacing", "문단 위 여백 적용"))):
            ttk.Checkbutton(editor, text=label, variable=selection[key]).grid(row=2, column=column + 1, sticky="w", pady=6)
        ttk.Label(body, text="같은 항목기호에 여러 변형이 있으면 가장 많이 사용된 변형이 적용 기준입니다. 비반복 항목도 검토·수정할 수 있습니다.",
                  style="Hint.TLabel").pack(anchor="w", pady=(5, 0))
        유형 = hierarchy.get("document_type")
        if 유형:
            ttk.Label(body, text=f"문서 유형: {유형} — {DOCUMENT_TYPES.get(유형, '')} "
                                 "(계층: 1 제목 · 2 장 · 3 중제목 · 4 소제목 □ · 5 ㅇ · 6 -)",
                      style="Hint.TLabel").pack(anchor="w", pady=(3, 0))
        warnings = hierarchy.get("warnings", [])
        if warnings:
            ttk.Label(body, text=f"논리 구조 확인 필요: {len(warnings)}건 · {warnings[0]}",
                      style="Hint.TLabel").pack(anchor="w", pady=(3, 0))
        result = {"confirmed": False}
        current = {"index": None}
        def save_current():
            index = current["index"]
            if index is None: return
            row = rows[index]
            row.update(role=stored_role(variables["role"].get()), font=variables["font"].get(),
                       size_pt=variables["size"].get(),
                       left_hwpunit=str(float(variables["left"].get()) * 100),
                       first_line_hwpunit=str(float(variables["indent"].get()) * 100),
                       prev_spacing_hwpunit=str(float(variables["spacing"].get()) * 100),
                       apply={key: var.get() for key, var in selection.items()})
            details.item(str(index), values=display(index))
        def choose(event=None):
            picked = details.selection()
            if not picked: return
            try:
                save_current()
            except ValueError:
                messagebox.showerror(APP_NAME, "여백과 크기는 숫자로 입력해 주세요.", parent=dialog)
                return
            index = int(picked[0])
            current["index"] = index
            row = rows[index]
            shown = display(index)
            for key, value in zip(("role", "font", "size", "left", "indent", "spacing"),
                                  (shown[2], shown[4], shown[5], shown[6], shown[7], shown[8])):
                variables[key].set(value)
            for key in STYLE_FIELDS:
                selection[key].set(row.get("apply", {}).get(key, True))
        details.bind("<<TreeviewSelect>>", choose)
        if rows:
            details.selection_set("0")
            choose()
        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(10, 0))
        def close(confirmed=False):
            if confirmed:
                try:
                    save_current()
                    edited = apply_reviewed_styles(profile, rows)
                except ValueError as exc:
                    messagebox.showerror(APP_NAME, str(exc), parent=dialog)
                    return
                previous_summary = profile.get("summary", "")
                summary_prefix = previous_summary.split("\n\n들여쓰기 →", 1)[0]
                edited["summary"] = (summary_prefix + "\n\n" if summary_prefix else "") + hierarchy_summary(edited["style_hierarchy"])
                profile.clear()
                profile.update(edited)
                result["confirmed"] = True
            dialog.destroy()
        ttk.Button(buttons, text="취소", command=close).pack(side="right")
        ttk.Button(buttons, text="확인하고 서식 저장", command=lambda: close(True)).pack(side="right", padx=8)
        dialog.protocol("WM_DELETE_WINDOW", close)
        parent.wait_window(dialog)
        return result["confirmed"]

    def _색상표시_상태_갱신(self, *args):
        """'자간을 수정한 글자를 색으로 표시하기' On/Off에 따라 색상 선택 라디오를 활성화/비활성화한다."""
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
        '보고서 표준서식적용' On/Off에 따라
        편집 여백 ~ 표 헤더/본문 서식 하위 옵션을 활성화/비활성화한다.
        """
        if getattr(self, "running", False):
            return

        활성 = bool(self.stdformat_var.get())
        상태 = "normal" if 활성 else "disabled"
        # 사용자의 선택값은 보존한다. 실제 실행 여부는 작업_실행에서 제한한다.
        for name in ('paren_label_bold_check', 'paren_shrink_check'):
            widget = getattr(self, name, None)
            if widget is not None: widget.config(state=상태)
        for widget in getattr(self, 'label_symbol_checks', []):
            widget.config(state='normal' if 활성 and self.paren_label_bold_var.get() else 'disabled')

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
        self.settings_toplevel.title("내 문서에 맞게 설정하기")
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        scale = getattr(self, "_ui_scale", 1.0)
        settings_width = min(round(900 * scale), sw - 48)
        settings_height = min(round(760 * scale), sh - 72)
        self.settings_toplevel.geometry(f"{settings_width}x{settings_height}")
        self.settings_toplevel.minsize(min(round(560 * scale), sw - 24),
                                      min(round(460 * scale), sh - 48))
        self.settings_toplevel.configure(bg=UI_COLORS["bg"])
        self.settings_toplevel.transient(self.root)
        self.settings_toplevel.protocol("WM_DELETE_WINDOW", self.settings_toplevel.withdraw)
        heading = ttk.Frame(self.settings_toplevel, padding=(9, 4))
        heading.pack(fill="x")
        heading.columnconfigure(0, weight=1)
        ttk.Label(heading, text="내 문서에 맞게 골라요", font=("맑은 고딕", 20, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(heading, text="선택은 자동 저장돼요. 작업 중에는 설정을 바꿀 수 없어요.", style="Hint.TLabel").grid(row=1, column=0, sticky="w")
        notebook = ttk.Notebook(self.settings_toplevel)
        notebook.pack(fill="both", expand=True, padx=18)
        self.settings_notebook = notebook
        tabs = {}
        for key, title in (("spacing", "간격"), ("format", "서식"),
                           ("layout", "문서"), ("advanced", "고급"),
                           ("log", "기록")):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=title)
            canvas = tk.Canvas(frame, bg=UI_COLORS["bg"], highlightthickness=0)
            scroll = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            body = ttk.Frame(canvas, padding=12)
            window = canvas.create_window((0, 0), window=body, anchor="nw")
            body.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
            canvas.bind("<Configure>", lambda e, c=canvas, w=window: c.itemconfigure(w, width=e.width))
            tabs[key] = body
        # 내어쓰기 단계와 상세 옵션은 서식 적용 설정 안에서 함께 찾도록 통합한다.
        tabs["indent"] = tabs["format"]
        def wheel(event):
            selected = notebook.nametowidget(notebook.select())
            for child in selected.winfo_children():
                if isinstance(child, tk.Canvas):
                    child.yview_scroll(-1 if event.delta > 0 or getattr(event, "num", 0) == 4 else 1, "units")
                    return "break"
        self.settings_toplevel.bind("<MouseWheel>", wheel)
        self.settings_toplevel.bind("<Button-4>", wheel)
        self.settings_toplevel.bind("<Button-5>", wheel)
        ttk.Label(tabs["spacing"], text="글자 사이 간격을 조절하는 기능이에요.\n실행창에서 ‘자간 정리’ 또는 ‘한 번에 적용’을 선택하세요.",
                  style="Hint.TLabel", wraplength=700).pack(anchor="w", pady=(0, 12))
        ttk.Label(tabs["format"],
                  text="서식 적용과 내어쓰기 작업을 함께 설정합니다. "
                       "여기서 켜고 끄면 세부 작업 창에도 그대로 반영됩니다.\n서식 작업의 기본 공백 정리도 함께 실행됩니다.",
                  style="Hint.TLabel", wraplength=700).pack(anchor="w", pady=(0, 8))
        presets = ttk.Frame(tabs["format"])
        presets.pack(fill="x", pady=(0, 12))
        self.preset_buttons = []
        button = ttk.Button(presets, text="보고서 기본 서식 선택", command=lambda: self._빠른설정("report"))
        button.pack(side="left", padx=(0, 8))
        self.preset_buttons.append(button)

        indent_presets = ttk.Frame(tabs["indent"])
        indent_presets.pack(fill="x", pady=(0, 12))
        indent_button = ttk.Button(indent_presets, text="내어쓰기만 선택", command=lambda: self._빠른설정("indent"))
        indent_button.pack(side="left", padx=(0, 8))
        self.preset_buttons.append(indent_button)
        ttk.Label(tabs["advanced"], text="처리 속도와 세부 강조 규칙을 조절해요. 처음에는 기본값을 유지해도 됩니다.",
                  style="Hint.TLabel", wraplength=700).pack(anchor="w", pady=(0, 12))
        update_box = ttk.LabelFrame(tabs["advanced"], text="앱 업데이트", padding=10)
        update_box.pack(fill="x", pady=(0, 12))
        self.check_updates_on_start_check = ttk.Checkbutton(
            update_box,
            text="앱 시작 시 업데이트 확인",
            variable=self.check_updates_on_start_var,
        )
        self.check_updates_on_start_check.pack(anchor="w")
        developer_box = ttk.LabelFrame(tabs["advanced"], text="개발자 모드", padding=10)
        developer_box.pack(fill="x", pady=(0, 12))
        ttk.Checkbutton(developer_box, text="개발자 모드 켜기 (문서 도구 사용)",
                        variable=self.developer_mode_var).pack(anchor="w")
        ttk.Label(developer_box, text="기본값은 꺼짐입니다. 켜면 문서 구조 검토·맞춤법 검토·작성 도우미·Markdown 내보내기·"
                                      "고급 문서 도구 등 문서 도구 메뉴가 나타납니다.",
                  style="Hint.TLabel", wraplength=650).pack(anchor="w", padx=(22, 0), pady=(2, 0))
        ttk.Label(
            update_box,
            text="기본값은 켜짐입니다. 끄더라도 설정 창의 ‘업데이트 확인’ 버튼으로 직접 확인할 수 있습니다.",
            style="Hint.TLabel",
            wraplength=650,
        ).pack(anchor="w", padx=(22, 0), pady=(2, 0))
        window_options = ttk.LabelFrame(tabs["advanced"], text="창 표시", padding=10)
        window_options.pack(fill="x", pady=(0, 12))
        ttk.Checkbutton(window_options, text="앱 창을 항상 위에 표시",
                        variable=self.always_on_top_var).pack(anchor="w")

        idiom_box = ttk.LabelFrame(tabs["advanced"], text="상용구 파일저장", padding=10)
        idiom_box.pack(fill="x", pady=(0, 12))
        ttk.Label(
            idiom_box,
            text="앱에 포함된 상용구 파일(HWP.IDO)을 한/글의 상용구 전용 폴더에 저장합니다.\n"
                 "(예: 한/글 2020 → %AppData%\\HNC\\User\\Hwp\\60)\n"
                 "진행 전에 한/글을 완전히 종료해 주세요.",
            style="Hint.TLabel",
            wraplength=650,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))
        ttk.Button(idiom_box, text="상용구 파일저장", command=self._상용구파일_저장_클릭).pack(anchor="w")
        container = tabs["spacing"]
        ttk.Label(container,
                  text=f"실행창의 ‘자간 정리 · 세부 작업’과 같은 {len(stages_for_mode('spacing'))}단계입니다. 여기서 켜고 끄면 세부 작업 창에도 그대로 반영됩니다.",
                  style="Hint.TLabel", wraplength=680).pack(anchor="w", pady=(0, 10))

        self.spacing_stage_vars = {}
        for number, (key, label) in enumerate(stages_for_mode("spacing"), 1):
            if key == "reset_spacing":
                var = self.reset_spacing_var   # 실행창 카드의 '기존 자간 초기화'와 같은 값
            else:
                var = tk.BooleanVar(value=self.stage_choices["spacing"].get(key, stage_default(key)))
                var.trace_add("write", lambda *_, k=key, v=var: self._설정탭_세부작업_변경("spacing", k, v))
            self.spacing_stage_vars[key] = var
            item = ttk.Frame(container)
            item.pack(fill="x", pady=(4, 7))
            ttk.Checkbutton(item, text=f"{number:02d}. {label}", style="Stage.TCheckbutton",
                            variable=var).pack(anchor="w")
            ttk.Label(item, text=STAGE_EXAMPLES[key], style="Hint.TLabel",
                      wraplength=650, justify="left").pack(anchor="w", padx=(25, 0), pady=(1, 0))
            detail = ttk.Frame(item)
            detail.pack(anchor="w", padx=(25, 0), pady=(4, 0), fill="x")
            self._자간정리_항목_상세(detail, key, 주설정탭=True)

        self.keep_punctuation_set_check = ttk.Checkbutton(
            tabs["layout"],
            text="문단 묶음 분리 및 제목 고립 방지\nㅇ 본문과 이어지는 - 내용·부연설명을 묶고, □·ㅁ 제목은 첫 ㅇ 묶음에 연결합니다.\n쪽별 줄 수로 배치를 조정하며, 저장할 때 문단 페이지 보호를 해제하고 다시 검사합니다.",
            variable=self.keep_punctuation_set_var,
        )
        self.keep_punctuation_set_check.pack(anchor="w", pady=(6, 0))

        linespacing_range_frame = ttk.Frame(tabs["layout"])
        linespacing_range_frame.pack(anchor="w", fill="x", pady=(4, 0), padx=(18, 0))
        ttk.Label(linespacing_range_frame, text="줄간격 조정 범위").pack(side="left")
        self.linespacing_min_spin = ttk.Spinbox(
            linespacing_range_frame, from_=50, to=500, increment=10, width=4,
            textvariable=self.linespacing_min_var, justify="center"
        )
        self.linespacing_min_spin.pack(side="left", padx=(4, 4))
        ttk.Label(linespacing_range_frame, text="% ~").pack(side="left")
        self.linespacing_max_spin = ttk.Spinbox(
            linespacing_range_frame, from_=50, to=500, increment=10, width=4,
            textvariable=self.linespacing_max_var, justify="center"
        )
        self.linespacing_max_spin.pack(side="left", padx=(4, 4))
        ttk.Label(linespacing_range_frame, text="% (이 범위를 벗어나는 조정은 하지 않습니다)").pack(side="left")

        color_frame = ttk.LabelFrame(tabs["layout"], text="수정한 곳 확인하기", padding=10)
        color_frame.pack(anchor="w", fill="x", pady=(6, 0))
        self.color_mark_check = ttk.Checkbutton(
            color_frame, text="자간을 수정한 글자를 색으로 표시하기", variable=self.color_mark_on_var
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

        retry_frame = ttk.LabelFrame(tabs["advanced"], text="정밀 조정 횟수 · 높일수록 시간이 늘어날 수 있어요", padding=10)
        retry_frame.pack(anchor="w", fill="x", pady=(6, 0))
        self.two_pass_check = ttk.Checkbutton(
            retry_frame,
            text="전체 작업 절차를 2회 반복 (기본 1회)",
            variable=self.two_pass_var,
        )
        self.two_pass_check.pack(side="right", padx=(12, 0))
        ttk.Label(retry_frame, text="본문:").pack(side="left")
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
        # 실행창 '서식 정리 · 세부 작업'과 같은 10단계(내어쓰기는 별도 탭)를
        # 번호 순서로 나열하고, 각 단계에 딸린 상세 설정을 그 아래 중첩한다.
        # 자간 정리 탭과 마찬가지로 self.stage_choices["format"]을 그대로
        # 읽고 쓰므로, 실행창의 '세부 작업…'과 항상 같은 값을 공유한다.
        format_container = tabs["format"]
        self.format_stage_vars = {}
        self.std_detail_checks = []
        서식_단계 = list(stages_for_mode("format"))
        내어쓰기_번호 = next(i for i, (key, _) in enumerate(서식_단계) if key == "hanging_indent")
        for number, (key, label) in enumerate(서식_단계[:내어쓰기_번호], 1):
            var = tk.BooleanVar(value=self.stage_choices["format"].get(key, stage_default(key)))
            var.trace_add("write", lambda *_, k=key, v=var: self._설정탭_세부작업_변경("format", k, v))
            self.format_stage_vars[key] = var
            item = ttk.Frame(format_container)
            item.pack(fill="x", pady=(4, 7))
            ttk.Checkbutton(item, text=f"{number:02d}. {label}", style="Stage.TCheckbutton",
                            variable=var).pack(anchor="w")
            ttk.Label(item, text=STAGE_EXAMPLES[key], style="Hint.TLabel",
                      wraplength=650, justify="left").pack(anchor="w", padx=(25, 0), pady=(1, 0))
            detail = ttk.Frame(item)
            detail.pack(anchor="w", padx=(25, 0), pady=(4, 0), fill="x")
            self._서식정리_항목_상세(detail, key, 주설정탭=True)

        # 표준서식/문두 라벨 굵게 토글에 따른 하위 옵션 활성화 이벤트 연결.
        self.stdformat_var.trace_add("write", self._표준서식_하위옵션_상태_갱신)
        self.paren_label_bold_var.trace_add('write', self._표준서식_하위옵션_상태_갱신)
        self._표준서식_하위옵션_상태_갱신()

        # 10. 최종 서식 기준 내어쓰기 — 별도 탭('내어쓰기')에 배치.
        self.indent_stage_vars = {}
        hanging_key, hanging_label = 서식_단계[내어쓰기_번호]
        indent_var = tk.BooleanVar(value=self.stage_choices["format"].get(hanging_key, True))
        indent_var.trace_add(
            "write", lambda *_, k=hanging_key, v=indent_var: self._설정탭_세부작업_변경("format", k, v))
        self.indent_stage_vars[hanging_key] = indent_var
        indent_item = ttk.Frame(tabs["indent"])
        indent_item.pack(fill="x", pady=(4, 7))
        ttk.Checkbutton(indent_item, text=f"{내어쓰기_번호 + 1:02d}. {hanging_label}", style="Stage.TCheckbutton",
                        variable=indent_var).pack(anchor="w")
        ttk.Label(indent_item, text=STAGE_EXAMPLES[hanging_key], style="Hint.TLabel",
                  wraplength=650, justify="left").pack(anchor="w", padx=(25, 0), pady=(1, 0))
        indent_sub = ttk.Frame(indent_item)
        indent_sub.pack(anchor="w", padx=(25, 0), pady=(4, 0), fill="x")
        self._서식정리_항목_상세(indent_sub, hanging_key, 주설정탭=True)


        # 그룹 3: 완료 후 처리
        group3 = ttk.LabelFrame(tabs["layout"], text="검토와 작업 완료", padding=12)
        group3.pack(fill="x", pady=(0, 8))
        self.autoclose_check = ttk.Checkbutton(group3, text="작업 완료 후 한글 문서 창 닫기", variable=self.autoclose_var)
        self.autoclose_check.pack(anchor="w")
        self.unify_result_window_check = ttk.Checkbutton(
            group3, text="서식통일 후 '작업 결과 확인' 창 띄우기 · 꺼 두면 결과는 처리 기록과 최종 검수 보고서에 남아요",
            variable=self.unify_result_window_var)
        self.unify_result_window_check.pack(anchor="w", pady=(6, 0))
        self.verify_check = ttk.Checkbutton(
            group3, text="상세 진단 및 문서 무결성 검사 · 본문·표·이미지·섹션 변화를 확인해요", variable=self.verify_var
        )
        self.verify_check.pack(anchor="w", pady=(6, 0))

        # 처리 기록: 기록 창 열기/닫기, 복사, 지우기
        log_tab = tabs["log"]
        ttk.Label(log_tab, text="작업 중에 일어난 일을 기록한 창이에요. 문제가 생기면 여기서 확인하세요.\n작업 중에도 이 탭은 열 수 있어요.",
                  style="Hint.TLabel", wraplength=700).pack(anchor="w", pady=(0, 12))
        log_buttons = ttk.Frame(log_tab)
        log_buttons.pack(anchor="w")
        self.log_toggle = ttk.Button(log_buttons, text="처리 기록 닫기" if self._log_visible else "▸ 처리 기록 보기",
                                     command=self._기록토글)
        self.log_toggle.pack(side="left")
        self.log_copy_button = ttk.Button(log_buttons, text="기록 복사", command=self.로그전체복사)
        self.log_copy_button.pack(side="left", padx=(8, 0))
        self.clear_button = ttk.Button(log_buttons, text="기록 지우기", command=lambda: self.log_text.delete("1.0", tk.END))
        self.clear_button.pack(side="left", padx=(8, 0))
        if self.running:
            self.clear_button.config(state="disabled")
        log_file_box = ttk.LabelFrame(log_tab, text="로그 파일", padding=10)
        log_file_box.pack(fill="x", pady=(16, 0))
        self.log_file_check = ttk.Checkbutton(log_file_box, text="작업로그 파일 만들기", variable=self.log_file_var)
        self.log_file_check.pack(anchor="w")
        ttk.Label(log_file_box, text="기본값은 꺼짐입니다. 켜면 다음 작업부터 처리 기록을 ‘문서이름(작업로그-날짜시간).log’ 파일로\n첫 번째 문서와 같은 폴더에 저장합니다. 작업 중에는 바꿀 수 없어요.",
                  style="Hint.TLabel", wraplength=680).pack(anchor="w", padx=(22, 0), pady=(2, 0))
        if self.running:
            self.log_file_check.config(state="disabled")
        report_box = ttk.LabelFrame(log_tab, text="검사·검수 보고서", padding=10)
        report_box.pack(fill="x", pady=(12, 0))
        self.integrity_report_file_check = ttk.Checkbutton(
            report_box, text="무결성검사 JSON 파일 만들기", variable=self.integrity_report_file_var)
        self.integrity_report_file_check.pack(anchor="w")
        ttk.Label(
            report_box,
            text="문서 탭의 ‘상세 진단 및 문서 무결성 검사’를 켰을 때 검사 결과를 저장합니다.\n"
                 "기본값은 꺼짐입니다. 끄면 검사는 수행해도 (무결성검사).json 파일은 만들지 않습니다.",
            style="Hint.TLabel", wraplength=680).pack(anchor="w", padx=(22, 0), pady=(2, 8))
        self.final_review_file_check = ttk.Checkbutton(
            report_box, text="최종검수 JSON 파일 만들기", variable=self.final_review_file_var)
        self.final_review_file_check.pack(anchor="w")
        ttk.Label(
            report_box,
            text="기본값은 꺼짐입니다. 켜면 작업 목표 기준의 평가 파일을 저장합니다. 끄더라도 앱 안의 완료 결과·점수 표시는 유지됩니다.",
            style="Hint.TLabel", wraplength=680).pack(anchor="w", padx=(22, 0), pady=(2, 0))
        if self.running:
            self.integrity_report_file_check.config(state="disabled")
            self.final_review_file_check.config(state="disabled")
        footer = ttk.Frame(self.settings_toplevel, padding=(18, 12))
        footer.pack(fill="x")
        ttk.Label(footer, text="만든 이 : 도토리만두", style="Hint.TLabel").pack(side="left")
        ttk.Button(footer, text="완료 · 닫기", style="Start.TButton", command=self.settings_toplevel.withdraw).pack(side="right")
        self.reset_button = ttk.Button(footer, text="기본값으로 되돌리기", command=self._설정_초기화_클릭)
        self.reset_button.pack(side="right", padx=8)
        self.update_button = ttk.Button(
            footer,
            text="업데이트 확인",
            command=lambda: self._자동업데이트_확인_시작(수동=True),
        )
        self.update_button.pack(side="right")

        self.settings_toplevel.withdraw()

    def _설정탭_상태_갱신(self):
        """작업 중에는 '처리 기록' 탭만 쓸 수 있게 하고, 작업이 끝나면 모든 탭을 연다."""
        notebook = getattr(self, "settings_notebook", None)
        if notebook is None:
            return
        try:
            탭들 = notebook.tabs()
            for 순번, 탭 in enumerate(탭들):
                notebook.tab(탭, state="normal" if (not self.running or 순번 == len(탭들) - 1) else "disabled")
            if self.running and 탭들:
                notebook.select(탭들[-1])
        except tk.TclError:
            pass

    def 설정창_열기(self):
        if self.settings_toplevel is None or not self.settings_toplevel.winfo_exists():
            self._설정창_생성()
            self._항상위_적용()
        self._설정탭_상태_갱신()
        self._자간정리탭_갱신()
        self._서식정리탭_갱신()
        self.settings_toplevel.deiconify()
        self.settings_toplevel.lift()

    def _자간정리탭_갱신(self):
        """실행창의 '세부 작업…'에서 바꾼 값을 설정창의 '자간 정리' 탭에도 반영한다."""
        for key, var in getattr(self, "spacing_stage_vars", {}).items():
            var.set(self.stage_choices["spacing"].get(key, True))

    def _서식정리탭_갱신(self):
        """실행창의 '세부 작업…'에서 바꾼 값을 설정창의 '서식 정리'·'내어쓰기' 탭에도 반영한다."""
        for key, var in getattr(self, "format_stage_vars", {}).items():
            var.set(self.stage_choices["format"].get(key, True))
        for key, var in getattr(self, "indent_stage_vars", {}).items():
            var.set(self.stage_choices["format"].get(key, True))

    def _설정_변경됨(self, *args):
        try:
            설정값 = {
                "prevent_word_split": bool(self.prevent_word_split_var.get()),
                "punctuation": bool(self.punctuation_var.get()),
                "punctuation_threshold": str(self.punctuation_threshold_var.get()),
                "keep_punctuation_set_together": bool(self.keep_punctuation_set_var.get()),
                "color_mark_on": bool(self.color_mark_on_var.get()),
                "color": str(self.color_var.get()),
                "autoclose": bool(self.autoclose_var.get()),
                "unify_result_window": bool(self.unify_result_window_var.get()),
                "stdformat": bool(self.stdformat_var.get()),
                "verify": bool(self.verify_var.get()),
                "integrity_report_file": bool(self.integrity_report_file_var.get()),
                "final_review_file": bool(self.final_review_file_var.get()),
                "two_pass_processing": bool(self.two_pass_var.get()),
                "table_spacing": bool(self.table_spacing_var.get()),
                "log_file": bool(self.log_file_var.get()),
                "check_updates_on_start": bool(self.check_updates_on_start_var.get()),
                "developer_mode": bool(self.developer_mode_var.get()),
                "review_document_kind": getattr(self, "review_document_kind", "보고서"),
                "review_reading_purpose": getattr(self, "review_reading_purpose", "상세 설명용"),
                "retry_body": str(self.retry_body_var.get()),
                "retry_table": str(self.retry_table_var.get()),
                "linespacing_min": str(self.linespacing_min_var.get()),
                "linespacing_max": str(self.linespacing_max_var.get()),
                "hwp_font_folder": str(self.font_folder_var.get()),
                "paste_add_folder": str(self.paste_add_folder_var.get()),
                "symbol_fonts": {
                    기호: {"font": v["font"].get(), "size": v["size"].get()}
                    for 기호, v in self.symbol_font_vars.items()
                },
                "table_fonts": {
                    part: {"font": v["font"].get(), "size": v["size"].get()}
                    for part, v in self.table_font_vars.items()
                },
                "label_symbols": {k: v.get() for k, v in self.label_symbol_vars.items()},
                "paren_shrink": bool(self.paren_shrink_var.get()),
                "paren_label_bold": bool(self.paren_label_bold_var.get()),
            }
            for 키, 변수 in self.std_bool_vars.items():
                설정값[키] = bool(변수.get())
            for 키, 변수 in self.std_parspace_vars.items():
                설정값[키] = str(변수.get())
            설정값["always_on_top"] = bool(self.always_on_top_var.get()) if hasattr(self, "always_on_top_var") else True
            설정값["all_include_spacing"] = (bool(self.include_spacing_var.get())
                                           if hasattr(self, "include_spacing_var") else True)
            설정값["all_exclude_tables"] = (bool(self.exclude_tables_var.get())
                                          if hasattr(self, "exclude_tables_var") else False)
            for 키, 이름 in (("all_exclude_pagefit", "all_exclude_pagefit_var"),
                           ("unify_exclude_tables", "unify_exclude_tables_var"),
                           ("unify_exclude_spacing", "unify_exclude_spacing_var"),
                           ("unify_exclude_pagefit", "unify_exclude_pagefit_var"),
                           ("unify_keep_layout", "unify_keep_layout_var")):
                설정값[키] = bool(getattr(self, 이름).get()) if hasattr(self, 이름) else False
            설정값["spacing_reset_existing"] = bool(self.stage_choices["spacing"].get("reset_spacing", True))
            설정값["active_format_profile"] = getattr(self, "_활성_서식_프로파일", "")
            기존_설정 = 설정_불러오기()
            기존_세부작업 = 기존_설정.get("stage_choices", {})
            if isinstance(기존_세부작업, dict) and 기존_세부작업:
                설정값["stage_choices"] = 기존_세부작업
            설정값["abbreviations"] = 기존_설정.get("abbreviations", {})
            설정값["abbreviation_defaults"] = 기존_설정.get("abbreviation_defaults", True)
            설정값["label_symbols_rev"] = 2
            설정값["report_files_rev"] = 2
            설정값["title_owner_text"] = (str(self.title_owner_var.get())
                                        if hasattr(self, "title_owner_var") else "")
            설정_저장(설정값)
            기호글꼴_적용(설정값)
            표글꼴_적용(설정값.get("table_fonts"))
        except Exception:
            pass

    def _휠_콤보박스_바인딩(self, 콤보):
        """아래아 한글의 글꼴 상자처럼, 마우스 휠로 목록을 오르내리며 고를 수 있게 한다."""
        def _이동(방향):
            값목록 = list(콤보["values"])
            if not 값목록:
                return
            현재값 = 콤보.get()
            try:
                idx = 값목록.index(현재값)
            except ValueError:
                idx = -1 if 방향 > 0 else len(값목록)
            새idx = max(0, min(len(값목록) - 1, idx + 방향))
            콤보.set(값목록[새idx])
            콤보.event_generate("<<ComboboxSelected>>")

        def _휠(event):
            방향 = -1 if getattr(event, "delta", 0) > 0 else 1
            _이동(방향)
            return "break"

        콤보.bind("<MouseWheel>", _휠)
        콤보.bind("<Button-4>", lambda e: (_이동(-1), "break"))
        콤보.bind("<Button-5>", lambda e: (_이동(1), "break"))

    def _폰트목록_새로고침(self):
        self._한글_폰트_목록_캐시 = 한글_폰트_목록_전체(self.font_folder_var.get())
        for 콤보 in getattr(self, "symbol_font_combos", {}).values():
            콤보["values"] = self._한글_폰트_목록_캐시
        if not self._한글_폰트_목록_캐시:
            messagebox.showinfo(
                APP_NAME,
                "지정한 폴더와 한컴오피스 번들(HFT) 글꼴 폴더에서 글꼴 파일(ttf/ttc/otf/hft)을 "
                "찾지 못했습니다.\n"
                "한/글 글꼴 폴더를 '찾아보기'로 직접 지정해 주세요. "
                "폴더를 몰라도 이름을 직접 입력해서 쓸 수 있습니다.",
                parent=self.settings_toplevel or self.root,
            )

    def _폰트폴더_찾아보기(self):
        시작 = self.font_folder_var.get() or str(Path.home())
        폴더 = askdirectory(title="한/글 글꼴 폴더 선택", initialdir=시작 if Path(시작).exists() else None,
                            parent=self.settings_toplevel or self.root)
        if 폴더:
            self.font_folder_var.set(폴더)
            self._폰트목록_새로고침()

    def _상용구파일_저장_클릭(self):
        """앱에 포함된 상용구 파일(HWP.IDO)을 한/글의 상용구 전용 폴더에 복사한다."""
        부모창 = self.settings_toplevel or self.root
        원본 = 번들_상용구_파일_찾기()
        if 원본 is None:
            messagebox.showerror(
                APP_NAME,
                f"앱에 포함된 {상용구_파일명} 파일을 찾을 수 없습니다.",
                parent=부모창,
            )
            return
        대상_폴더 = 상용구_전용폴더_찾기()
        if 대상_폴더 is None:
            messagebox.showerror(
                APP_NAME,
                "한/글 상용구 전용 폴더를 찾지 못했습니다.\n"
                "한컴오피스 한/글을 한 번 이상 실행한 뒤 다시 시도해 주세요.\n"
                "(예상 위치: %AppData%\\HNC\\User\\Hwp\\버전폴더, "
                "탐색기에서 '숨긴 항목'을 켜야 보입니다)",
                parent=부모창,
            )
            return
        대상_경로 = 대상_폴더 / 상용구_파일명
        if 대상_경로.exists():
            if not messagebox.askyesno(
                APP_NAME,
                f"이미 상용구 파일이 있습니다.\n{대상_경로}\n\n"
                "앱에 포함된 상용구 파일로 덮어쓸까요?\n"
                "(진행 전에 한/글을 완전히 종료해 주세요)",
                parent=부모창,
            ):
                return
        try:
            대상_폴더.mkdir(parents=True, exist_ok=True)
            shutil.copy2(원본, 대상_경로)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"상용구 파일 저장에 실패했습니다: {e}", parent=부모창)
            return
        messagebox.showinfo(
            APP_NAME,
            f"상용구 파일을 저장했습니다.\n{대상_경로}\n\n한/글을 다시 시작하면 적용됩니다.",
            parent=부모창,
        )

    def _설정_초기화_클릭(self):
        if self.running:
            return
        if not messagebox.askyesno(APP_NAME, "모든 설정을 기본값으로 초기화하시겠습니까?"):
            return
        try:
            설정_저장(dict(기본_설정))
        except Exception as e:
            messagebox.showerror(APP_NAME, f"설정 초기화 오류: {e}")
            return

        self.always_on_top_var.set(기본_설정["always_on_top"])
        self.prevent_word_split_var.set(기본_설정["prevent_word_split"])
        self.punctuation_var.set(기본_설정["punctuation"])
        self.punctuation_threshold_var.set(기본_설정["punctuation_threshold"])
        self.keep_punctuation_set_var.set(기본_설정["keep_punctuation_set_together"])
        self.color_mark_on_var.set(기본_설정["color_mark_on"])
        self.color_var.set(기본_설정["color"])
        self.autoclose_var.set(기본_설정["autoclose"])
        self.unify_result_window_var.set(기본_설정["unify_result_window"])
        self.stdformat_var.set(기본_설정["stdformat"])
        self.verify_var.set(기본_설정["verify"])
        self.integrity_report_file_var.set(기본_설정["integrity_report_file"])
        self.final_review_file_var.set(기본_설정["final_review_file"])
        self.two_pass_var.set(기본_설정["two_pass_processing"])
        self.table_spacing_var.set(기본_설정["table_spacing"])
        self.log_file_var.set(기본_설정["log_file"])
        self.check_updates_on_start_var.set(기본_설정["check_updates_on_start"])
        self.developer_mode_var.set(기본_설정["developer_mode"])
        self.review_document_kind = 기본_설정["review_document_kind"]
        self.review_reading_purpose = 기본_설정["review_reading_purpose"]
        self.retry_body_var.set(기본_설정["retry_body"])
        self.retry_table_var.set(기본_설정["retry_table"])
        self.linespacing_min_var.set(기본_설정["linespacing_min"])
        self.linespacing_max_var.set(기본_설정["linespacing_max"])
        self.font_folder_var.set(기본_설정.get("hwp_font_folder", "") or 한글_폰트_폴더_자동감지())
        self._한글_폰트_목록_캐시 = 한글_폰트_목록_전체(self.font_folder_var.get())
        self.paste_add_folder_var.set(기본_설정.get("paste_add_folder", ""))
        for 기호, v in self.symbol_font_vars.items():
            기본항목 = 기본_설정.get("symbol_fonts", {}).get(기호, {})
            v["font"].set(기본항목.get("font", ""))
            v["size"].set(기본항목.get("size", ""))
            if hasattr(self, "symbol_font_combos") and 기호 in self.symbol_font_combos:
                self.symbol_font_combos[기호]["values"] = self._한글_폰트_목록_캐시
        for part, v in self.table_font_vars.items():
            v["font"].set(기본_설정["table_fonts"][part]["font"])
            v["size"].set(기본_설정["table_fonts"][part]["size"])
            콤보 = getattr(self, "symbol_font_combos", {}).get(f"표_{part}")
            if 콤보 is not None:
                콤보["values"] = self._한글_폰트_목록_캐시
        for key, var in self.label_symbol_vars.items():
            var.set(기본_설정["label_symbols"].get(key, True))
        self.paren_shrink_var.set(기본_설정["paren_shrink"])
        self.paren_label_bold_var.set(기본_설정["paren_label_bold"])

        for 키 in self.std_bool_keys:
            self.std_bool_vars[키].set(기본_설정[키])
        for 키 in self.std_parspace_str_keys:
            self.std_parspace_vars[키].set(기본_설정[키])
        self.title_owner_var.set(기본_설정["title_owner_text"])

        서식_기본값_전역_복원()
        self._활성_서식_프로파일 = ""
        self._프로파일_목록갱신()
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
        if Path(file_path).suffix.lower() not in 지원_확장자:
            return False
        if file_path in self.files:
            return False

        self.files.append(file_path)
        self.file_count.configure(text=f"{len(self.files)}개 문서")
        self.file_list.insert(tk.END, file_path)
        self._원본폴더_버튼_갱신()
        if not self.running:
            self._실행버튼_상태("normal")
            self._작업범위_초기화()      # 새 문서를 추가하면 작업 범위는 기본값(문서 전체)으로
            self._결과_초기화()
            if self._안내단계 in (0, 1):
                self._안내_설정(2)   # 문서를 추가했으니 '02 원하는 작업'을 안내
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
            if path.is_file() and path.suffix.lower() in 지원_확장자:
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
            title="처리할 문서를 선택하세요.",
            initialdir=os.getcwd(),
            filetypes=[
                ("지원하는 모든 문서", "*.hwp *.hwpx *.txt *.md *.doc *.docx *.pdf"),
                ("한/글 파일", "*.hwp *.hwpx"), ("HWP 파일", "*.hwp"), ("HWPX 파일", "*.hwpx"),
                ("텍스트/Markdown", "*.txt *.md"), ("MS Word", "*.doc *.docx"), ("PDF", "*.pdf"),
            ]
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

    def Markdown_내보내기(self):
        if self.running or not self.files:
            return
        선택 = list(self.file_list.curselection())
        대상들 = [self.files[index] for index in 선택] if 선택 else list(self.files)
        self.status_var.set(f"Markdown 변환 중 · {len(대상들)}개 문서")
        for button in self.file_buttons:
            button.config(state="disabled")

        def worker():
            성공, 실패 = [], []
            for source in 대상들:
                try:
                    성공.append(str(문서_markdown_내보내기(source)))
                except Exception as exc:
                    실패.append((str(source), str(exc)))
            gui_queue.put(("markdown_exported", 성공, 실패))

        threading.Thread(target=worker, daemon=True, name="markdown-export").start()

    def _고급도구_대상(self):
        선택 = list(self.file_list.curselection())
        if 선택:
            return Path(self.files[선택[0]])
        if self.files:
            return Path(self.files[0])
        return None

    def _고급도구_비동기(self, 이름, 작업):
        if self.running:
            return
        self.status_var.set(f"{이름} 실행 중")
        def worker():
            try:
                result = 작업()
                self.root.after(0, lambda: self._고급도구_완료(이름, result))
            except Exception as exc:
                self.root.after(0, lambda error=str(exc): self._고급도구_실패(이름, error))
        threading.Thread(target=worker, daemon=True, name="kordoc-advanced-tool").start()

    def _고급도구_완료(self, 이름, result):
        self.status_var.set(f"{이름} 완료")
        self.로그표시(f"{이름} 완료: {result}")
        messagebox.showinfo(APP_NAME, f"{이름}을 완료했습니다.\n\n{result}", parent=self.root)

    def _고급도구_실패(self, 이름, error):
        self.status_var.set(f"{이름} 실패")
        self.로그표시(f"{이름} 실패: {error}")
        messagebox.showerror(APP_NAME, f"{이름}을 완료하지 못했습니다.\n\n{error}", parent=self.root)

    def 고급문서도구_열기(self):
        if self.running:
            return
        if getattr(self, "advanced_tools_toplevel", None) is not None:
            try:
                self.advanced_tools_toplevel.lift()
                return
            except tk.TclError:
                self.advanced_tools_toplevel = None
        window = tk.Toplevel(self.root)
        self.advanced_tools_toplevel = window
        window.title("고급 문서 도구 · kordoc v4")
        window.geometry("620x570")
        window.resizable(True, True)
        window.transient(self.root)
        body = ttk.Frame(window, padding=18)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="구조 분석 · 비교 · 생성", font=("맑은 고딕", 16, "bold")).pack(anchor="w")
        engine_text = tk.StringVar(value="문서 엔진 확인 중…")
        ttk.Label(body, textvariable=engine_text, style="Hint.TLabel").pack(anchor="w", pady=(2, 12))
        def check_engine():
            try: value = f"kordoc {kordoc_engine_version()} · Node.js 선택형 연동"
            except Exception as exc: value = str(exc)
            self.root.after(0, lambda: engine_text.set(value))
        threading.Thread(target=check_engine, daemon=True).start()

        target = self._고급도구_대상()
        target_text = tk.StringVar(value=str(target) if target else "문서 목록에서 대상 파일을 먼저 선택하세요.")
        ttk.Label(body, textvariable=target_text, wraplength=570).pack(anchor="w", pady=(0, 12))
        grid = ttk.Frame(body)
        grid.pack(fill="x")
        for column in range(2): grid.grid_columnconfigure(column, weight=1)

        def require_target():
            selected = self._고급도구_대상()
            if selected is None:
                raise ValueError("문서 목록에서 대상 파일을 먼저 선택해 주세요.")
            return selected
        def page_export():
            pages = simpledialog.askstring(APP_NAME, "페이지 범위를 입력하세요. 예: 1-3, 5", parent=window)
            if pages: self._고급도구_비동기("페이지별 Markdown", lambda: export_advanced_markdown(require_target(), pages))
        def compare_tool():
            other = askopenfilename(parent=window, title="비교할 문서 선택")
            if other: self._고급도구_비동기("블록·셀 신구대조", lambda: compare_documents_advanced(require_target(), other))
        def fill_tool():
            fields = simpledialog.askstring(APP_NAME, "채울 값을 입력하세요.\n예: 성명=홍길동,전화=02-123-4567", parent=window)
            if fields: self._고급도구_비동기("양식 자동 채우기", lambda: fill_form(require_target(), fields))
        def patch_tool():
            edited = askopenfilename(parent=window, title="편집한 Markdown 선택", filetypes=[("Markdown", "*.md")])
            if edited: self._고급도구_비동기("서식 보존 텍스트 패치", lambda: patch_document(require_target(), edited))

        tools = (
            ("고급 Markdown", lambda: self._고급도구_비동기("고급 Markdown", lambda: export_advanced_markdown(require_target()))),
            ("페이지별 Markdown", page_export),
            ("RAG 구조 청크", lambda: self._고급도구_비동기("RAG 구조 청크", lambda: export_rag_chunks(require_target()))),
            ("공통 문서 IR(JSON)", lambda: self._고급도구_비동기("공통 문서 IR", lambda: export_common_ir(require_target()))),
            ("표 추출·분류", lambda: self._고급도구_비동기("표 추출·분류", lambda: analyze_tables(require_target()))),
            ("양식 필드 분석", lambda: self._고급도구_비동기("양식 필드 분석", lambda: analyze_form(require_target()))),
            ("블록·셀 신구대조", compare_tool),
            ("양식 자동 채우기", fill_tool),
            ("서식 보존 텍스트 패치", patch_tool),
            ("공문서 표기법 검수", lambda: self._고급도구_비동기("공문서 표기법 검수", lambda: lint_document(require_target()))),
            ("페이지 이미지 미리보기", lambda: self._고급도구_비동기("페이지 이미지 미리보기", lambda: render_preview(require_target()))),
        )
        for index, (label, command) in enumerate(tools):
            ttk.Button(grid, text=label, command=command).grid(
                row=index // 2, column=index % 2, sticky="ew", padx=4, pady=4
            )

        separator = ttk.Separator(body)
        separator.pack(fill="x", pady=14)
        generate_frame = ttk.LabelFrame(body, text="Markdown → HWPX 생성", padding=10)
        generate_frame.pack(fill="x")
        preset = tk.StringVar(value="보고서")
        ttk.Label(generate_frame, text="프리셋").pack(side="left")
        ttk.Combobox(generate_frame, textvariable=preset, values=("보고서", "계획서", "기안문"),
                     state="readonly", width=10).pack(side="left", padx=8)
        def generate_tool():
            markdown = askopenfilename(parent=window, title="생성할 Markdown 선택", filetypes=[("Markdown", "*.md")])
            if markdown:
                selected_preset = preset.get()
                self._고급도구_비동기(
                    f"{selected_preset} HWPX 생성",
                    lambda: generate_hwpx(markdown, selected_preset),
                )
        ttk.Button(generate_frame, text="HWPX 생성…", command=generate_tool).pack(side="left")
        requirement_frame = ttk.LabelFrame(body, text="고급 문서 도구 필수 구성", padding=10)
        requirement_frame.pack(fill="x", pady=(12, 0))
        ttk.Label(
            requirement_frame,
            text=("고급 문서 도구를 실행하려면 Node.js 18 이상이 설치되어 있어야 합니다. "
                  "설치 후 앱을 다시 실행해 주세요. 기존 문서 편집 기능은 Node.js 없이도 사용할 수 있습니다."),
            style="Hint.TLabel",
            wraplength=410,
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(
            requirement_frame,
            text="Node.js LTS 받기",
            command=lambda: webbrowser.open("https://nodejs.org/ko/download"),
        ).pack(side="right", padx=(10, 0))
        window.protocol("WM_DELETE_WINDOW", lambda: (setattr(self, "advanced_tools_toplevel", None), window.destroy()))

    def 목록지우기(self):
        if self.running:
            return
        self.files.clear()
        self.file_count.configure(text="0개 문서")
        self.file_list.delete(0, tk.END)
        self.status_var.set("")
        self._실행버튼_상태("disabled")
        self._작업범위_초기화()          # 목록을 비우면 작업 범위는 기본값(문서 전체)으로
        self._결과_초기화()
        self._안내_설정(1)

    def 작업기록지우기(self):
        """하단 '작업기록 지우기' — 처리 내역(로그)과 문서 목록을 함께 비운다.
        (기존 '문서목록 비우기' 기능을 이 버튼에 통합했다.)"""
        if self.running:
            return
        # 1) 처리 내역(로그) 비우기
        try:
            self.log_text.config(state="normal")
            self.log_text.delete("1.0", tk.END)
        except Exception:
            pass
        # 2) 진행 다이어그램 초기화
        try:
            self._단계_초기화()
        except Exception:
            pass
        # 3) 문서 목록 비우기
        self.files.clear()
        self.file_count.configure(text="0개 문서")
        self.file_list.delete(0, tk.END)
        self.status_var.set("")
        self._실행버튼_상태("disabled")
        self._작업범위_초기화()
        self._결과_초기화()
        self._안내_설정(1)

    def 버튼_작업중(self):
        for widget in self.mode_buttons + self.file_buttons + self.preset_buttons + [self.tools_button, self.proofread_button, self.stage_details_button, self.reset_button, self.update_button]:
            widget.configure(state="disabled")
        self.profile_combo.config(state="disabled")
        self.main_profile_combo.config(state="disabled")
        self.copy_format_button.config(state="disabled")
        self._설정탭_상태_갱신()   # 세부 설정 버튼은 켜 둔다(처리 기록 탭만 사용 가능)
        self.keep_punctuation_set_check.config(state="disabled")
        self._실행버튼_상태("disabled")
        self.stop_button.config(state="normal")
        self.clear_button.config(state="disabled")
        self.document_review_button.config(state="disabled")
        self.prevent_word_split_check.config(state="disabled")
        self.punctuation_check.config(state="disabled")
        self.punctuation_threshold_spin.config(state="disabled")
        self.table_spacing_check.config(state="disabled")
        self.log_file_check.config(state="disabled")
        for 위젯 in (self.page_range_toggle, self.range_all_radio, self.range_pages_radio,
                     self.range_start_spin, self.range_end_spin):
            위젯.config(state="disabled")
        self.retry_body_spin.config(state="disabled")
        self.retry_table_spin.config(state="disabled")
        self.two_pass_check.config(state="disabled")
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
        for check in self.label_symbol_checks:
            check.config(state="disabled")
        self.verify_check.config(state="disabled")
        self.integrity_report_file_check.config(state="disabled")
        self.final_review_file_check.config(state="disabled")

    def 버튼_대기중(self):
        for widget in self.mode_buttons + self.file_buttons + self.preset_buttons + [self.tools_button, self.proofread_button, self.stage_details_button, self.reset_button, self.update_button]:
            widget.configure(state="normal")
        self._요약갱신()
        self.profile_combo.config(state="readonly")
        self.main_profile_combo.config(state="readonly")
        self.copy_format_button.config(state="normal")
        self.settings_button.config(state="normal")
        self._설정탭_상태_갱신()
        self.keep_punctuation_set_check.config(state="normal")
        self._실행버튼_상태("normal" if self.files else "disabled")
        self.stop_button.config(state="disabled")
        self.clear_button.config(state="normal")
        self.document_review_button.config(state="normal")
        self.prevent_word_split_check.config(state="normal")
        self.punctuation_check.config(state="normal")
        self.punctuation_threshold_spin.config(state="normal")
        self.table_spacing_check.config(state="normal")
        self.log_file_check.config(state="normal")
        self.page_range_toggle.config(state="normal")
        self.range_all_radio.config(state="normal")
        self.range_pages_radio.config(state="normal")
        self._범위_상태_갱신()
        self.retry_body_spin.config(state="normal")
        self.retry_table_spin.config(state="normal")
        self.two_pass_check.config(state="normal")
        self.color_mark_check.config(state="normal")

        self.autoclose_check.config(state="normal")
        self.stdformat_check.config(state="normal")
        self.paren_shrink_check.config(state="normal")
        self.paren_label_bold_check.config(state="normal")
        self.verify_check.config(state="normal")
        self.integrity_report_file_check.config(state="normal")
        self.final_review_file_check.config(state="normal")
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

    def _실행버튼_상태(self, state):
        for button in self.run_buttons:
            button.config(state=state)

    def _단계_초기화(self):
        if hasattr(self, 'stage_board'):
            self.stage_board.reset()

    def _단계_강조(self, 단계):
        if hasattr(self, 'stage_board'):
            self.stage_board.activate(단계)

    def 작업시작(self, mode="all"):
        if getattr(self, "_서식분석중", False):
            messagebox.showinfo(APP_NAME, "서식 분석이 끝난 뒤 실행해 주세요.")
            return
        if getattr(self, "_교정_창", None) is not None:
            messagebox.showinfo(APP_NAME, "공공언어·맞춤법 검토 창을 닫은 뒤 실행해 주세요.", parent=self.root)
            return
        if self.running:
            return
        if not self.files:
            messagebox.showwarning(APP_NAME, "먼저 문서(HWP/HWPX/TXT/MD/DOC(X)/PDF)를 선택하거나 끌어다 놓으세요.", parent=self.root)
            return

        범위_확인, 작업범위 = self._작업범위_읽기()
        if not 범위_확인:
            return

        if mode in ("format", "all"):
            self.stdformat_var.set(True)

        # 중단 버튼으로 멈춘 작업과 같은 모드로 다시 실행하면, 이미 끝낸
        # 문서는 건너뛰고 그 다음 문서부터 이어서 진행한다. 모드가 다르면
        # 새 작업으로 보고 처음부터 다시 시작한다.
        이어서_진행 = self._재개_대기중 and self._재개_모드 == mode
        시작_인덱스 = self._재개_시작_인덱스 if 이어서_진행 else 1
        self._재개_대기중 = False

        self.running = True

        self.settings_toplevel.withdraw()
        self.closing = False
        중단_event.clear()
        self._결과_초기화(결과목록도_지우기=not 이어서_진행)   # 이어서 진행할 때는 이전 결과 기록을 남긴다
        if not 이어서_진행:
            self._작업시작시각 = time.monotonic()
        self._작업모드 = mode
        self.버튼_작업중()

        self.로그표시("")
        if 이어서_진행:
            self.로그표시(f"중단된 작업을 이어서 진행합니다 ({시작_인덱스}/{len(self.files)}번째 문서부터).")
        self.로그표시("=" * 45)
        self.로그표시(f"{APP_NAME} 작업 시작 — {dict(spacing='자간조정', unify='서식통일', format='서식적용', all='일괄적용')[mode]}")
        self.로그표시(f"문서: {len(self.files)}개")
        if 작업범위 is None:
            self.로그표시("작업 범위: 문서 전체")
        else:
            self.로그표시(f"작업 범위: {쪽표시(작업범위[0])} ~ {쪽표시(작업범위[1])}")

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

        try:
            줄간격최소값 = max(10, int(self.linespacing_min_var.get()))
        except Exception:
            줄간격최소값 = 160
            self.linespacing_min_var.set("160")

        try:
            줄간격최대값 = max(10, int(self.linespacing_max_var.get()))
        except Exception:
            줄간격최대값 = 200
            self.linespacing_max_var.set("200")

        if 줄간격최소값 > 줄간격최대값:
            줄간격최소값, 줄간격최대값 = 줄간격최대값, 줄간격최소값
            self.linespacing_min_var.set(str(줄간격최소값))
            self.linespacing_max_var.set(str(줄간격최대값))

        문단위간격_기본값 = {"std_parspace_chapter": 15, "std_parspace_midtitle": 15, "std_parspace_box": 15,
                        "std_parspace_circle": 8, "std_parspace_dash": 4, "std_parspace_note": 0}
        문단위간격_값 = {}
        for 키, 기본값 in 문단위간격_기본값.items():
            try:
                문단위간격_값[키] = max(0, int(self.std_parspace_vars[키].get()))
            except Exception:
                문단위간격_값[키] = 기본값
                self.std_parspace_vars[키].set(str(기본값))
        try:
            복귀배율 = int(self.std_parspace_vars["std_parspace_return_percent"].get())
        except (TypeError, ValueError):
            복귀배율 = 150
        복귀배율 = max(100, min(400, 복귀배율))
        self.std_parspace_vars["std_parspace_return_percent"].set(str(복귀배율))
        문단위간격_값["std_parspace_return_percent"] = 복귀배율

        선택_색상 = COLOR_MAP.get(self.color_var.get()) if self.color_mark_on_var.get() else None
        표준서식_세부_전달 = {키: var.get() for 키, var in self.std_bool_vars.items()}
        표준서식_세부_전달["std_title_subtitle_pt"] = 제목_부제_크기_반영(
            self.std_parspace_vars["std_title_subtitle_pt"].get())
        self.std_parspace_vars["std_title_subtitle_pt"].set(str(제목_부제_크기_pt))   # 잘못된 값은 고친 값으로 보여 준다
        표준서식_세부_전달["title_owner_text"] = 제목_담당자_글_반영(self.title_owner_var.get())
        표준서식_세부_전달["unify_result_window"] = 서식통일_결과창_반영(self.unify_result_window_var.get())
        표준서식_세부_전달["table_fonts"] = {
            part: {"font": v["font"].get(), "size": v["size"].get()}
            for part, v in self.table_font_vars.items()
        }
        # 카드 옵션: '표 제외'(한 번에 적용·서식 통일)는 표 관련 세부 작업을 모두 끄고 표 칸 안 문장도 자간 작업에서
        # 빼고, '페이지 맞춤 제외'는 문단 아래 간격 페이지 맞춤·관련 문단 페이지 배치를 끈다. 서식 통일의 '자간 정리
        # 제외'는 서식통일이 고친 문장의 자간 조정을 끈다.
        if mode == "unify":
            표제외, 쪽맞춤제외 = self.unify_exclude_tables_var.get(), self.unify_exclude_pagefit_var.get()
        elif mode in ("all", "format"):
            표제외, 쪽맞춤제외 = self.exclude_tables_var.get(), self.all_exclude_pagefit_var.get()
        else:
            표제외 = 쪽맞춤제외 = False
        세부작업 = dict(self.stage_choices[mode])
        # 서식 통일의 '자간 정리 제외'는 세부 작업 '서식통일 문장 자간 정리'를 끈 것과 같다(서로 연동).
        자간제외 = mode == "unify" and (bool(self.unify_exclude_spacing_var.get())
                                     or not stage_enabled(세부작업, "unify_spacing", mode))
        if 표제외:
            세부작업 = 표작업_제외(세부작업)
            self.로그표시("표 제외: 표 관련 작업(텍스트 표 변환·기본 표 서식·표 칸 너비·표 정밀 서식·표 머리글 서식·"
                       "표 서식통일·표 안 자간·줄·단어 작업)을 빼고, 표 칸 안 문장도 자간 작업에서 뺍니다. "
                       "제목·개요 서식 표는 정리합니다.")
        if 쪽맞춤제외:
            세부작업 = 페이지맞춤_제외(세부작업)
            self.로그표시("페이지 맞춤 제외: 문단 아래 간격 페이지 맞춤과 관련 문단 페이지 배치를 뺍니다.")
        if 자간제외:
            self.로그표시("자간 정리 제외: 서식통일이 고친 문장의 자간 조정·외톨이 글자 당기기를 하지 않습니다.")
        표준서식_세부_전달["unify_exclude_spacing"] = 자간제외

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
                self.keep_punctuation_set_var.get(),
                self.prevent_word_split_var.get(),
                mode,
                {k: v.get() for k, v in self.label_symbol_vars.items()},
                줄간격최소값,
                줄간격최대값,
                self.table_spacing_var.get() and not 표제외,
                작업범위,
                self.log_file_var.get(),
                세부작업,
                2 if self.two_pass_var.get() else 1,
                시작_인덱스,
                None,
                self.integrity_report_file_var.get(),
                self.final_review_file_var.get(),
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

    def _서식통일_대표값_검토_요청(self, kind, payload):
        요청 = {"payload": payload, "done": threading.Event(), "approved": False}
        event = f"style_unify_{kind}_review"
        gui_queue.put((event, 요청))
        while not 요청["done"].wait(0.1):
            if 중단_요청됨() or self.closing:
                return {"approved": False, "selected": []}
        return 요청

    def _대화상자_부모(self):
        """숨겨진 기본 창 대신 맨 앞에 뜨는 임시 부모를 돌려준다."""
        if (self.root.state() != "withdrawn"
                and not getattr(self.root, "_docfit_hidden_backend", False)):
            return self.root, None
        임시 = tk.Toplevel(self.root)
        임시.wm_transient("")
        임시.overrideredirect(True)
        임시.attributes("-alpha", 0.0)
        임시.attributes("-topmost", True)
        임시.geometry(f"1x1+{임시.winfo_screenwidth() // 2}+{임시.winfo_screenheight() // 3}")
        임시.deiconify()
        임시.lift()
        임시.focus_force()
        return 임시, 임시

    def _알림(self, 함수, *args, **kwargs):
        """웹 화면 모드에서도 메시지 창이 보이도록 임시 부모로 띄운다."""
        부모, 임시 = self._대화상자_부모()
        try:
            return 함수(*args, parent=부모, **kwargs)
        finally:
            if 임시 is not None:
                임시.destroy()

    def _검토창_앞으로(self, window):
        """한글 창에 가려지지 않도록 검토 창을 맨 앞으로 올린다."""
        창_맨앞으로(window)

    def _서식통일_대표서식_검토창(self, 요청):
        """표본 조사값을 보여 주고 적용 전 문서별 표준값을 편집하게 한다."""
        그룹별_표본 = 요청["payload"]
        window = tk.Toplevel(self.root)
        window.title("서식통일 2/5 · 대표 서식 확인")
        window.transient(self.root)
        window.geometry("900x680")
        window.minsize(700, 480)
        host = ttk.Frame(window, padding=16)
        host.pack(fill="both", expand=True)
        ttk.Label(host, text="문서에서 조사한 대표 서식", font=("맑은 고딕", 15, "bold")).pack(anchor="w")
        ttk.Label(host, text="대표값을 확인하면 불일치 부분을 추가 승인 없이 자동 교정합니다. 빈 값은 보정하지 않으며, 필요한 대표값이 없는 문단은 결과 문서에 빨간색으로 표시합니다.",
                  wraplength=850).pack(anchor="w", pady=(5, 10))

        # ※ 표본이 우세값을 만들지 못한 경우 * 표본의 크기와 후보를 함께
        # 제시하되 자동으로 복사하지 않는다. 최종 선택은 사용자가 한다.
        stars = [key for key in 그룹별_표본 if key[0] in ("*", "**")]
        star_sizes = []
        for key in stars:
            profile = _서식통일_문서대표프로필.get(key, {})
            value = profile.get("size", (None, 0))[0]
            if value is not None:
                star_sizes.append(f"{key[0]} {value / 100:g}pt")
        if any(key[0] == "※" and any(v[0] is None for v in _서식통일_문서대표프로필.get(key, {}).values())
               for key in 그룹별_표본):
            note = "※ 대표값이 불명확합니다. *·** 계열의 크기 유사성은 참고 후보일 뿐이며, 자동 선택하지 않습니다."
            if star_sizes:
                note += " 후보: " + ", ".join(star_sizes)
            ttk.Label(host, text=note, foreground="#9a3412", wraplength=850).pack(anchor="w", pady=(0, 8))
            ambiguous = next(key for key in 그룹별_표본 if key[0] == "※"
                             and any(v[0] is None for v in _서식통일_문서대표프로필.get(key, {}).values()))
            candidate_keys = [key for key in stars
                              if _서식통일_문서대표프로필.get(key, {}).get("font", (None, 0))[0] is not None
                              or _서식통일_문서대표프로필.get(key, {}).get("size", (None, 0))[0] is not None]
            if candidate_keys:
                choice_row = ttk.Frame(host)
                choice_row.pack(fill="x", pady=(0, 8))
                choice = ttk.Combobox(choice_row, state="readonly", width=26,
                                      values=[f"{key[0]} 대표값 사용" for key in candidate_keys])
                choice.current(0)
                choice.pack(side="left")

                def use_candidate():
                    selected = candidate_keys[max(0, choice.current())]
                    source = _서식통일_문서대표프로필.get(selected, {})
                    for field, control in editors.get(ambiguous, {}).items():
                        value = source.get(field, (None, 0))[0]
                        if field == "font":
                            control.delete(0, "end")
                            if value is not None:
                                control.insert(0, str(value))
                        elif field == "size":
                            control.delete(0, "end")
                            if value is not None:
                                control.insert(0, f"{value / 100:g}")
                        elif value is not None:
                            control.set(("굵게" if value else "보통") if field.endswith("bold")
                                        else ("적용" if value else "미적용"))
                    self.로그표시(f"※ 대표값 후보로 {selected[0]} 그룹 값을 선택했습니다. 확인 후 필요하면 개별 수정하세요.")

                ttk.Button(choice_row, text="선택한 후보를 ※에 채우기", command=use_candidate).pack(side="left", padx=8)

        canvas = tk.Canvas(host, highlightthickness=0)
        scrollbar = ttk.Scrollbar(host, orient="vertical", command=canvas.yview)
        body = ttk.Frame(canvas)
        body.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        editors = {}
        필드 = (("font", "글꼴"), ("size", "크기(pt)"), ("marker_bold", "문두 굵게"),
                ("label_bold", "괄호라벨 굵게"), ("hanging_indent", "내어쓰기"))
        for row, (key, 항목들) in enumerate(그룹별_표본.items()):
            marker, role, level = key
            frame = ttk.LabelFrame(body, text=f"{marker}  ·  {role}  ·  표본 {len(항목들)}개", padding=8)
            frame.grid(row=row, column=0, sticky="ew", padx=4, pady=4)
            body.grid_columnconfigure(0, weight=1)
            profile = _서식통일_문서대표프로필.get(key, {})
            editors[key] = {}
            for col, (field, label) in enumerate(필드):
                ttk.Label(frame, text=label).grid(row=0, column=col, sticky="w", padx=4)
                pair = profile.get(field, (None, 0))
                value = pair[0]
                if field == "font":
                    shown = "" if value is None else str(value)
                    control = ttk.Entry(frame, width=18)
                    control.insert(0, shown)
                elif field == "size":
                    shown = "" if value is None else f"{value / 100:g}"
                    control = ttk.Entry(frame, width=9)
                    control.insert(0, shown)
                else:
                    options = ("판정 보류", "굵게", "보통") if field in ("marker_bold", "label_bold") else ("판정 보류", "적용", "미적용")
                    shown = "판정 보류" if value is None else (("굵게" if value else "보통") if field.endswith("bold") else ("적용" if value else "미적용"))
                    control = ttk.Combobox(frame, values=options, state="readonly", width=10)
                    control.set(shown)
                control.grid(row=1, column=col, sticky="ew", padx=4, pady=(2, 4))
                editors[key][field] = control
        buttons = ttk.Frame(host)
        buttons.pack(fill="x", pady=(10, 0))

        def finish(approved):
            if approved:
                for key, controls in editors.items():
                    prior = _서식통일_문서대표프로필.get(key, {})
                    updated = dict(prior)
                    for field, control in controls.items():
                        raw = control.get().strip()
                        old_count = prior.get(field, (None, 0))[1]
                        if not raw or raw == "판정 보류":
                            value = None
                        elif field == "font":
                            value = raw
                        elif field == "size":
                            try:
                                value = int(round(float(raw) * 100))
                                if value <= 0:
                                    raise ValueError
                            except ValueError:
                                messagebox.showerror(APP_NAME, f"{key[0]} 크기는 0보다 큰 pt 숫자여야 합니다.", parent=window)
                                return
                        elif field.endswith("bold"):
                            value = raw == "굵게"
                        else:
                            value = raw == "적용"
                        updated[field] = (value, old_count)
                    _서식통일_문서대표프로필[key] = updated
            요청["approved"] = approved
            요청["done"].set()
            window.destroy()

        ttk.Button(buttons, text="취소", command=lambda: finish(False)).pack(side="right")
        ttk.Button(buttons, text="확인한 대표값으로 진행", style="Primary.TButton",
                   command=lambda: finish(True)).pack(side="right", padx=(0, 8))
        window.protocol("WM_DELETE_WINDOW", lambda: finish(False))
        window.grab_set()
        self._검토창_앞으로(window)
        window.focus_set()

    def _서식통일_적용영역_검토창(self, 요청):
        계획 = 요청["payload"]
        후보 = [(index, item) for index, item in enumerate(계획) if item.get("mismatch")]
        window = tk.Toplevel(self.root)
        window.title("서식통일 3/5 · 편집 영역 확인")
        window.transient(self.root)
        window.geometry("1040x700")
        window.minsize(760, 500)
        host = ttk.Frame(window, padding=14)
        host.pack(fill="both", expand=True)
        ttk.Label(host, text="대표 서식 미적용 영역", font=("맑은 고딕", 15, "bold")).pack(anchor="w")
        ttk.Label(host, text="체크된 문장만 적용합니다. 문장을 선택하면 전체 내용과 적용 예정 속성을 확인할 수 있습니다.",
                  wraplength=980).pack(anchor="w", pady=(4, 10))
        columns = ("apply", "marker", "fields", "text")
        tree = ttk.Treeview(host, columns=columns, show="headings", selectmode="browse", height=13)
        for column, title, width in (("apply", "적용", 48), ("marker", "기호/유형", 105),
                                     ("fields", "변경 예정", 250), ("text", "문장 미리보기", 560)):
            tree.heading(column, text=title)
            tree.column(column, width=width, minwidth=45, stretch=column == "text", anchor="w")
        tree_scroll = ttk.Scrollbar(host, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        tree.pack(side="top", fill="both", expand=True)
        tree_scroll.place(in_=tree, relx=1.0, rely=0, relheight=1.0, anchor="ne")
        selected = {index for index, _ in 후보}

        def changed_fields(item):
            fields = []
            if item.get("font_runs"):
                fields.append(f"글꼴 {len(item['font_runs'])}영역 → {item.get('font') or '판정 보류'}")
            if item.get("size_runs"):
                fields.append(f"크기 {len(item['size_runs'])}영역 → {item.get('size') / 100:g}pt")
            if item.get("aside_runs"):
                fields.append(f"괄호 {len(item['aside_runs'])}영역 → {item.get('aside_size') / 100:g}pt")
            if item.get("marker_bold_runs"):
                fields.append(f"문두 굵기 {len(item['marker_bold_runs'])}영역 → {'굵게' if item.get('marker_bold') else '보통'}")
            if item.get("label_bold_runs"):
                fields.append(f"라벨 굵기 {len(item['label_bold_runs'])}영역 → {'굵게' if item.get('label_bold') else '보통'}")
            if item.get("hanging_mismatch"):
                fields.append(f"내어쓰기 → {'적용' if item.get('expected_hanging') else '미적용'}")
            return fields

        for index, item in 후보:
            tree.insert("", "end", iid=str(index), values=("☑", f"{item['marker']} / {item['role']}",
                        ", ".join(changed_fields(item)), item.get("text", "").strip()))

        details = tk.Text(host, height=7, wrap="word", state="disabled")
        details.pack(fill="x", pady=(8, 0))

        def show_detail(_event=None):
            current = tree.selection()
            if not current:
                return
            index = int(current[0])
            item = 계획[index]
            lines = [f"항목기호: {item['marker']}   유형: {item['role']}   계층: {item['level']}",
                     "적용 예정: " + ("; ".join(changed_fields(item)) or "변경 없음"),
                     "문장 전체:", item.get("text", "").strip()]
            details.configure(state="normal")
            details.delete("1.0", "end")
            details.insert("1.0", "\n".join(lines))
            details.configure(state="disabled")

        def toggle(event):
            if tree.identify_column(event.x) != "#1":
                return
            row = tree.identify_row(event.y)
            if row:
                index = int(row)
                if index in selected:
                    selected.remove(index)
                    mark = "☐"
                else:
                    selected.add(index)
                    mark = "☑"
                values = list(tree.item(row, "values"))
                values[0] = mark
                tree.item(row, values=values)
                count.set(f"선택 {len(selected)} / 후보 {len(후보)}개")

        tree.bind("<<TreeviewSelect>>", show_detail)
        tree.bind("<Button-1>", toggle, add="+")
        if 후보:
            tree.selection_set(str(후보[0][0]))
            show_detail()
        else:
            ttk.Label(host, text="대표 서식과 다른 적용 영역이 없습니다. 문서는 변경하지 않습니다.").pack(anchor="w", pady=10)
        footer = ttk.Frame(host)
        footer.pack(fill="x", pady=(10, 0))
        count = tk.StringVar(value=f"선택 {len(selected)} / 후보 {len(후보)}개")
        ttk.Label(footer, textvariable=count).pack(side="left")

        def finish(approved):
            요청["selected"] = sorted(selected) if approved else []
            요청["approved"] = approved
            요청["done"].set()
            window.destroy()

        ttk.Button(footer, text="취소", command=lambda: finish(False)).pack(side="right")
        ttk.Button(footer, text="선택 영역만 적용", style="Primary.TButton",
                   command=lambda: finish(True)).pack(side="right", padx=(0, 8))
        window.protocol("WM_DELETE_WINDOW", lambda: finish(False))
        window.grab_set()
        self._검토창_앞으로(window)
        window.focus_set()

    def _서식통일_결과_확인창(self, 요청):
        result = 요청["payload"] or {}
        window = tk.Toplevel(self.root)
        window.title("서식통일 5/5 · 작업 결과 확인" + (f" · {result['file']}" if result.get("file") else ""))
        window.transient(self.root)
        window.geometry("760x560")
        window.minsize(600, 400)
        host = ttk.Frame(window, padding=16)
        host.pack(fill="both", expand=True)
        status = result.get("status", "error")
        status_text = {"passed": "검수 통과", "failed": "불일치 남음",
                       "incomplete": "일부 판정 보류", "error": "검수 오류",
                       "not_applicable": "검사할 문장 없음"}.get(status, status)
        ttk.Label(host, text=f"저장 결과 확인 · {status_text}",
                  font=("맑은 고딕", 15, "bold")).pack(anchor="w")
        ttk.Label(host, text=f"검사 문장 {result.get('checked', 0)}개 · 불일치 {len(result.get('issues', []))}개 · 판정 보류 그룹 {len(result.get('not_checkable', []))}개",
                  ).pack(anchor="w", pady=(5, 10))
        report = tk.Text(host, wrap="word", state="normal")
        report.pack(fill="both", expand=True)
        report.insert("end", "[남은 불일치]\n")
        for issue in result.get("issues", [])[:100]:
            report.insert("end", f"• {issue.get('text', '')}\n  항목: {', '.join(issue.get('fields', []))}\n")
        if not result.get("issues"):
            report.insert("end", "남은 불일치가 없습니다.\n")
        report.insert("end", "\n[판정 보류]\n")
        for group in result.get("not_checkable", [])[:100]:
            report.insert("end", f"• {group.get('marker')} / {group.get('role')} — {', '.join(group.get('fields', []))}\n")
        if not result.get("not_checkable"):
            report.insert("end", "판정 보류 그룹이 없습니다.\n")
        if result.get("error"):
            report.insert("end", "\n오류: " + str(result["error"]))
        report.insert("end", "\n[대표값 미확정 문단 · 빨간색 표시]\n")
        for item in result.get("unresolved", []):
            marked = "빨간 표시 확인" if item.get("red_marked") else "빨간 표시 미확인"
            report.insert("end", f"• {item.get('text', '')}\n  미확정: {', '.join(item.get('fields', []))} · {marked}\n")
        report.configure(state="disabled")

        def finish():
            요청["approved"] = True
            요청["done"].set()
            window.destroy()

        ttk.Button(host, text="결과 확인", style="Primary.TButton", command=finish).pack(anchor="e", pady=(10, 0))
        window.protocol("WM_DELETE_WINDOW", finish)
        # 작업은 이 창을 기다리지 않고 이어지므로 모달로 잡지 않는다(중단 단추·완료 안내를 막지 않게).
        self._검토창_앞으로(window)
        window.focus_set()

    def queue_처리(self):
        모인_로그 = []
        deadline = time.monotonic() + .012
        try:
            for _ in range(150):
                if time.monotonic() >= deadline:
                    break
                item = gui_queue.get_nowait()
                event = item[0]
                if event in ("style_unify_profile_review", "style_unify_regions_review",
                             "style_unify_result_review"):
                    try:
                        if event == "style_unify_profile_review":
                            self._서식통일_대표서식_검토창(item[1])
                        elif event == "style_unify_regions_review":
                            self._서식통일_적용영역_검토창(item[1])
                        else:
                            self._서식통일_결과_확인창(item[1])
                    except Exception as exc:
                        로그(f"[서식통일] 사용자 확인창 오류: {exc}")
                        item[1]["approved"] = False
                        item[1]["selected"] = []
                        item[1]["done"].set()
                elif event == "format_copied":
                    self._서식_복사완료(profile=item[1])
                elif event == "document_review_done":
                    item[1](result=item[2], error=item[3])
                elif event == "format_copy_error":
                    self._서식_복사완료(error=item[1])
                elif event == "proofread_scan_done":
                    self._교정_작업중 = False
                    if getattr(self, "_교정_창", None) is not None:
                        self._교정_후보, self._교정_대상 = item[1], item[2]
                        self._교정_목록갱신()
                        self._교정_상태.set(f"교정 후보 {len(item[1])}개 표현 · 검사 실패 {len(item[3])}개 파일")
                        if item[3]:
                            messagebox.showwarning(APP_NAME, "검사하지 못한 파일:\n" + "\n".join(
                                f"{Path(path).name}: {error}" for path, error in item[3]), parent=self._교정_창)
                elif event == "proofread_apply_done":
                    self._교정_작업중 = False
                    if getattr(self, "_교정_창", None) is not None:
                        self._교정_상태.set(f"저장 완료 {len(item[1])}개 파일 · 실패 {len(item[2])}개")
                        details = "\n".join(f"{path} ({count}건 교정)" for path, count in item[1])
                        details += "\n" + "\n".join(f"실패: {Path(path).name}: {error}" for path, error in item[2])
                        messagebox.showinfo(APP_NAME, details.strip() or "저장된 결과가 없습니다.", parent=self._교정_창)
                elif event == "markdown_exported":
                    성공, 실패 = item[1], item[2]
                    for button in self.file_buttons:
                        button.config(state="normal")
                    for path in 성공:
                        self.로그표시(f"Markdown 저장 완료: {path}")
                    for source, error in 실패:
                        self.로그표시(f"Markdown 변환 실패: {source}\n{error}")
                    self.status_var.set(f"Markdown 변환 완료 · 성공 {len(성공)}개 / 실패 {len(실패)}개")
                    if 실패:
                        messagebox.showwarning(
                            APP_NAME,
                            f"Markdown 변환을 마쳤습니다.\n\n성공: {len(성공)}개\n실패: {len(실패)}개\n처리 기록을 확인해 주세요.",
                            parent=self.root,
                        )
                    else:
                        messagebox.showinfo(APP_NAME, f"Markdown 파일 {len(성공)}개를 원본 폴더에 저장했습니다.", parent=self.root)
                elif event == "log":
                    self.stage_board.signal()
                    모인_로그.append(str(item[1]))
                    continue
                if 모인_로그:
                    self.로그_여러줄_표시(모인_로그)
                    모인_로그 = []

                if event == "status":
                    self.stage_board.signal(item[1])
                    self.status_var.set(item[1])
                elif event == "step":
                    self._단계_강조(item[1])
                elif event == "step_reset":
                    self._단계_초기화()
                    self._안내키, self._안내지남 = None, set()
                elif event == "guide":
                    key = 진행안내_키(item[1])
                    if key and key != self._안내키:
                        if self._안내키:
                            self._안내지남.add(self._안내키)
                        self._안내키 = key
                elif event == "progress":
                    pass  # 긴 진행 바는 없앴다. 단계 표시(LiveStageBoard)가 진행 상황을 보여 준다.
                elif event == "saved":
                    self._결과목록.append({"원본": item[1], "결과": item[2], "쪽수": item[3]})
                elif event == "document_error":
                    self.stage_board.finish("오류")
                    self.로그표시(f"문서 처리 실패: {item[1]}\n{item[2]}")
                elif event in ("stopped", "finished") and getattr(self, "_서식예시_작업", None):
                    self._서식예시_완료(item, 중단=event == "stopped")
                elif event == "stopped":
                    self.running = False
                    self._안내_설정(0)
                    self.버튼_대기중()
                    self.stage_board.finish("중단")
                    완료수 = len(self._결과목록)
                    # 완료된 문서 수가 전체와 같으면(마지막 문서 저장 직후 중단) 더 이어갈 게 없다.
                    if 0 < 완료수 < len(self.files):
                        self._재개_대기중 = True
                        self._재개_시작_인덱스 = 완료수 + 1
                        self._재개_모드 = self._작업모드
                        안내 = f"작업이 중단되었습니다. ({완료수}/{len(self.files)}개 완료 — 실행을 누르면 이어서 진행합니다.)"
                    else:
                        self._재개_대기중 = False
                        안내 = "작업이 중단되었습니다."
                    self.status_var.set(안내)
                    self.로그표시("=" * 45 + f"\n{안내}\n" + "=" * 45)
                    if not self.closing:
                        messagebox.showinfo(APP_NAME, 안내, parent=self.root)
                elif event == "finished":
                    self.running = False
                    self._안내_설정(0)   # 작업이 끝나면 강조를 기본값으로 되돌린다.
                    self.버튼_대기중()
                    self.stage_board.finish("완료" if item[2] == 0 else "오류")
                    if self._안내키:
                        self._안내지남.add(self._안내키)
                    self._안내키 = "done" if item[2] == 0 else self._안내키
                    self._작업결과_표시(item[2] == 0)
                    최종검수 = item[6] if len(item) >= 8 else None
                    if 최종검수:
                        self.status_var.set(
                            f"처리 완료 · 수행 점수 {최종검수['score']:.1f}/100 · {최종검수['verdict']}"
                        )
                        self.stage_board.set_result_message(
                            f"최종 검수: 수행 점수 {최종검수['score']:.1f}/100 · {최종검수['verdict']}"
                        )
                    else:
                        self.status_var.set(f"처리 완료 · 성공 {item[1]}개 / 실패 {item[2]}개")
                    self.로그표시("=" * 45 + f"\n작업 완료 - 성공 {item[1]}개 / 실패 {item[2]}개\n" + "=" * 45)
                    if not self.closing:
                        안내문 = f"문서 처리가 완료되었습니다.\n\n성공: {item[1]}개\n실패: {item[2]}개"
                        if len(item) >= 6:
                            안내문 += (
                                f"\n\n(세부 작업 항목 기준)\n"
                                f"총 작업건수: {item[3]}건\n"
                                f"성공: {item[4]}건\n"
                                f"실패: {item[5]}건"
                            )
                        if 최종검수:
                            안내문 += (
                                f"\n\n[목표 기준 최종 검수]\n"
                                f"수행 점수: {최종검수['score']:.1f}/100 (규칙 준수율과 별도)\n"
                                f"판정: {최종검수['verdict']}"
                            )
                            if 최종검수["blockers"]:
                                안내문 += "\n확인사항: " + ", ".join(최종검수["blockers"])
                            if item[7]:
                                안내문 += f"\n보고서: {item[7]}"
                            else:
                                안내문 += "\n최종 검수 파일은 저장하지 않았습니다."
                        self._알림(messagebox.showinfo, APP_NAME, 안내문)
                elif event == "fatal_error":
                    self.running = False
                    self._안내_설정(0)
                    self.버튼_대기중()
                    self.stage_board.finish("오류")
                    self.status_var.set("오류 발생 · 처리 기록을 확인해 주세요")
                    self.로그표시(f"치명적 오류:\n{item[1]}")
                    if not self.closing:
                        self._알림(messagebox.showerror, APP_NAME, f"작업 중 오류가 발생했습니다.\n\n{item[1]}")
        except queue.Empty:
            pass
        except Exception as exc:
            # 이벤트 하나의 UI 오류가 큐 polling 자체를 영구 중단하지 않게 한다.
            진단로그(f"[GUI 이벤트] 처리 중 예외(다음 이벤트부터 계속): {exc}")

        if 모인_로그:
            self.로그_여러줄_표시(모인_로그)

        try:
            self._queue_after_id = self.root.after(20 if not gui_queue.empty() else 100, self.queue_처리)
        except tk.TclError:
            pass

    def _루트_파괴시_예약취소(self, event):
        if event.widget is not self.root:
            return
        job = getattr(self, "_queue_after_id", None)
        if job is not None:
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
            self._queue_after_id = None

    def 종료(self):
        if self.closing:
            return
        if self.running:
            if not self._알림(messagebox.askyesno, APP_NAME, "현재 자간 조정 작업이 진행 중입니다.\n\n작업을 중단하고 종료하시겠습니까?"):
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

def _새창_맨앞으로(event_or_window):
    """웹 화면 뒤에 설정·검토 창이 숨지 않도록 새로 뜬 Tk 창을 앞으로 올린다."""
    window = getattr(event_or_window, "widget", event_or_window)
    try:
        if window.winfo_toplevel() is not window or window.overrideredirect():
            return
        window.lift()
        window.attributes("-topmost", True)
        window.after(300, lambda: window.winfo_exists() and window.attributes("-topmost", False))
        window.focus_force()
    except Exception:
        pass


def 웹모드_기본창_숨김(root):
    """Tk 기본 창을 withdraw 대신 화면 중앙의 투명한 1px 창으로 둔다.

    withdraw된 창에 transient로 붙은 설정·검토 창과 메시지 창은 Windows에서
    표시되지 않거나 웹 화면 뒤로 숨어 UI가 멈춘 것처럼 보인다.
    """
    root.overrideredirect(True)
    root.attributes("-alpha", 0.0)
    # 기존 화면의 최소 크기(약 420x400) 때문에 투명 창이 커져 그 영역의 클릭을 가로채지 않도록 1px로 고정한다.
    root._docfit_min_size = root.minsize()
    root.minsize(1, 1)
    root.maxsize(1, 1)
    root.geometry(f"1x1+{root.winfo_screenwidth() // 2}+{root.winfo_screenheight() // 3}")
    root._docfit_hidden_backend = True
    root.bind_class("Toplevel", "<Map>", _새창_맨앞으로, add="+")


def 웹모드_기본창_복원(root):
    """웹 화면을 쓸 수 없을 때 기존 Tk 화면을 정상 창으로 되돌린다."""
    root._docfit_hidden_backend = False
    root.maxsize(root.winfo_screenwidth(), root.winfo_screenheight())
    root.minsize(*(getattr(root, "_docfit_min_size", None) or (420, 400)))
    root.overrideredirect(False)
    root.attributes("-alpha", 1.0)
    root.geometry("1040x760")
    root.deiconify()
    root.lift()


def main():
    import importlib.util

    # WebView2가 있으면 반응형 웹 화면을 주 UI로 사용하고, 문서 처리·설정 창은
    # 기존 Tk 백엔드에 연결한다. WebView 초기화 문제 진단·복구 시 환경변수로
    # 기존 화면을 선택할 수 있고, 연결 패키지가 없을 때도 Tk 화면으로 돌아간다.
    tk_only = os.environ.get("HWP_AUTODOCFIT_UI", "").strip().lower() == "tk"
    if tk_only or importlib.util.find_spec("webview") is None:
        root = TkinterDnD.Tk()
        HwpAutoDocFitGUI(root)
        _새창_맨앞으로(root)
        root.mainloop()
        return

    준비됨 = threading.Event()
    보관 = {}

    def tk_실행():
        try:
            root = TkinterDnD.Tk()
            gui = HwpAutoDocFitGUI(root)
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
        raise RuntimeError("앱 인터페이스를 시작하지 못했습니다.")
    if "오류" in 보관:
        raise RuntimeError("앱 인터페이스를 시작하지 못했습니다.") from 보관["오류"]

    try:
        import desktop_web_ui

        desktop_web_ui.APP_NAME = APP_NAME
        desktop_web_ui.APP_VERSION = APP_VERSION
        desktop_web_ui.STAGE_ORDER = 진행단계_순서
        if not desktop_web_ui.run_webview(보관["gui"]):
            보관["root"].after(0, lambda: 웹모드_기본창_복원(보관["root"]))
            tk_thread.join()
    except Exception as 오류:
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
    main()
