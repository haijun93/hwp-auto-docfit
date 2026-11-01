"""타임머신: 작업한 문서·이미지를 작업 시각 순 세로 타임라인과 달력으로 보기 위한 색인(순수 파이썬).

설계: TODO.md '타임머신' 항목(사용자 결정 2026-11-01), docs/KAGENT_DESIGN.md(상주 감시는 kagent.exe).
1단계 범위: 규칙·증분 스캔·SQLite 색인·날짜 구간/일별 집계. 썸네일·화면은 다음 단계.
"""
from .rules import KINDS, Rules, cloud_only
from .scan import ScanResult, default_roots, scan_root, scan_roots
from .store import Store, path_key

__all__ = ["KINDS", "Rules", "cloud_only", "ScanResult", "default_roots", "scan_root", "scan_roots", "Store",
           "path_key"]
