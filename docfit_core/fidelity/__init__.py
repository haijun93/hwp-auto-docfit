"""원본 보존 경로: 원본 파일·압축 항목 보관, 요소 전수 목록, 원문 위치 맵, 최소 변경 패치, 다층 검증.

STYLE_FIDELITY_DESIGN.md의 첫 구현 범위(HWPX 전수 목록과 무손실 보관 + 단순 내용 패치 + 검증)다.
공문서 후처리(표준서식·서식통일·자간)와 실행 경로를 나누며 자동 교정 단계를 넣지 않는다. 한/글 COM은
쓰지 않는다(실제 한/글 열기 확인은 호출자가 native 검사 함수로 넘긴다).
"""

from .package import PackageSnapshot, UnsupportedPackage, copy_exact, write_package
from .source_map import SourceMap, build_source_map
from .inventory import inventory, coverage
from .patch_hwpx import PatchError, apply_patch, list_objects
from .verify import verify_patch

__all__ = [
    "PackageSnapshot", "UnsupportedPackage", "copy_exact", "write_package",
    "SourceMap", "build_source_map", "inventory", "coverage",
    "PatchError", "apply_patch", "list_objects", "verify_patch",
]
