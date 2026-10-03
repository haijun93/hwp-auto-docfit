"""XML 원문 위치 맵: 요소마다 원본 바이트 구간과 객체 경로를 둔다.

ElementTree는 원문 위치를 주지 않으므로, 한/글이 저장한 XML(DTD 없음)을 태그 단위로 훑어 요소의 시작
태그·내용·끝 태그 바이트 구간을 기록한다. 같은 바이트를 defusedxml로도 읽어 요소 수와 이름 순서가
같은지 확인하고, 다르면 위치 맵을 쓰지 않는다(SourceMapError).

객체 경로는 부모부터 '로컬이름[같은 이름 형제 중 순번]'을 잇는다. 예: /p[3]/run[0]/tbl[0]/tr[1]/tc[0]/subList[0]/p[0].
경로는 원본 리비전 안에서만 유효하다(문서가 바뀌면 위치 맵을 다시 만든다).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import re

from defusedxml import ElementTree as ET

_TOKEN = re.compile(
    rb"<!--.*?-->|<\?.*?\?>|<!\[CDATA\[.*?\]\]>|<!DOCTYPE[^>]*>"
    rb"|<(/?)([^\s/>!?]+)((?:\s+[^\s=/>]+\s*=\s*(?:\"[^\"]*\"|'[^']*'))*)\s*(/?)>",
    re.S)
_ENTITY = re.compile(rb"&(#x[0-9A-Fa-f]+|#[0-9]+|amp|lt|gt|quot|apos);")
_NAMED = {b"amp": "&", b"lt": "<", b"gt": ">", b"quot": '"', b"apos": "'"}
_INLINE = {"fwSpace": " ", "nbSpace": " ", "tab": "\t", "lineBreak": "\n"}


class SourceMapError(ValueError):
    """원문 위치를 확신할 수 없는 XML."""


@dataclass
class Node:
    qname: str
    local: str
    start: int            # '<' 위치
    open_end: int         # 시작 태그 '>' 다음
    close_start: int      # 끝 태그 '<' 위치(빈 요소면 open_end)
    end: int              # 끝 태그 '>' 다음
    parent: "Node | None" = None
    children: list = field(default_factory=list)
    path: str = ""

    def child(self, local):
        return [c for c in self.children if c.local == local]


@dataclass
class SourceMap:
    part: str
    data: bytes
    sha256: str
    root: Node
    by_path: dict

    def text(self, start, end) -> str:
        return unescape(self.data[start:end])

    def segments(self, t_node):
        """t 요소의 글자 구간 목록 [(시작, 끝)]. 안쪽 요소(빈칸·탭·줄바꿈) 사이의 글자만 담는다."""
        result, cursor = [], t_node.open_end
        for child in t_node.children:
            result.append((cursor, child.start))
            cursor = child.end
        result.append((cursor, t_node.close_start))
        return result

    def paragraph_runs(self, p_node):
        """문단 직속 run의 t 요소들(문서 순서)."""
        return [t for run in p_node.child("run") for t in run.child("t")]

    def paragraph_text(self, p_node) -> str:
        """문단 글. 고정폭·묶음 빈칸과 탭·강제 줄바꿈 요소도 해당 글자로 나타낸다."""
        parts = []
        for t in self.paragraph_runs(p_node):
            segments = self.segments(t)
            for index, (start, end) in enumerate(segments):
                parts.append(self.text(start, end))
                if index < len(t.children):
                    parts.append(_INLINE.get(t.children[index].local, ""))
        return "".join(parts)

    def paragraphs(self):
        """모든 문단(표 칸 문단 포함)을 문서 순서로."""
        result = []

        def walk(node):
            if node.local == "p":
                result.append(node)
            for child in node.children:
                walk(child)
        walk(self.root)
        return result


def unescape(raw: bytes) -> str:
    def entity(match):
        name = match.group(1)
        if name.startswith(b"#x"):
            return chr(int(name[2:], 16)).encode("utf-8")
        if name.startswith(b"#"):
            return chr(int(name[1:])).encode("utf-8")
        return _NAMED[name].encode("utf-8")
    return _ENTITY.sub(entity, raw).decode("utf-8")


def escape(text: str) -> bytes:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").encode("utf-8")


def build_source_map(part: str, data: bytes) -> SourceMap:
    if b"<!DOCTYPE" in data[:4096] or b"<!ENTITY" in data:
        raise SourceMapError(f"{part}: DTD·엔티티 선언이 있는 XML은 다루지 않습니다.")
    stack, root = [], None
    position = 0
    for match in _TOKEN.finditer(data):
        if match.start() != position and not data[position:match.start()].strip() == b"" and not stack:
            raise SourceMapError(f"{part}: 루트 밖에 글자가 있습니다.")
        position = match.end()
        closing, name, _, empty = match.group(1), match.group(2), match.group(3), match.group(4)
        if name is None:
            continue
        qname = name.decode("utf-8")
        local = qname.split(":", 1)[-1]
        if closing:
            if not stack or stack[-1].qname != qname:
                raise SourceMapError(f"{part}: 끝 태그가 맞지 않습니다({qname}).")
            node = stack.pop()
            node.close_start, node.end = match.start(), match.end()
            continue
        node = Node(qname, local, match.start(), match.end(), match.end(), match.end(),
                    parent=stack[-1] if stack else None)
        if stack:
            stack[-1].children.append(node)
        elif root is None:
            root = node
        else:
            raise SourceMapError(f"{part}: 루트 요소가 둘 이상입니다.")
        if not empty:
            stack.append(node)
    if stack or root is None:
        raise SourceMapError(f"{part}: 닫히지 않은 요소가 있습니다.")
    by_path = {}

    def assign(node, prefix):
        counts = {}
        for child in node.children:
            index = counts.get(child.local, 0)
            counts[child.local] = index + 1
            child.path = f"{prefix}/{child.local}[{index}]"
            by_path[child.path] = child
            assign(child, child.path)
    root.path = ""
    assign(root, "")
    # 같은 바이트를 안전 파서로 읽어 요소 순서가 같은지 확인한다.
    parsed = [element.tag.rsplit("}", 1)[-1] for element in ET.fromstring(data).iter()]
    mapped = []

    def order(node):
        mapped.append(node.local)
        for child in node.children:
            order(child)
    order(root)
    if parsed != mapped:
        raise SourceMapError(f"{part}: 원문 위치 맵과 XML 해석 결과의 요소 순서가 다릅니다.")
    return SourceMap(part, data, sha256(data).hexdigest(), root, by_path)
