"""원본 패키지 보관과 최소 변경 쓰기.

HWPX(ZIP)의 압축 항목마다 원본 로컬 레코드(로컬 헤더 + 압축 데이터 + 데이터 서술자)와 중앙 디렉터리
레코드를 바이트 그대로 보관한다. 쓰기는 바뀐 항목만 새로 압축하고, 나머지 항목은 원본 압축 바이트·
날짜·속성·주석을 그대로 옮긴 뒤 위치(오프셋)만 고친다. 바꿀 항목이 없으면 원본 파일과 바이트가 같다.

ZIP64·분할 압축·암호화 항목은 위치를 안전하게 다시 계산할 수 없어 지원하지 않는다(UnsupportedPackage).
HWP 5.0 바이너리(CFB)는 원본 보관과 동일 복제만 지원한다.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
import shutil
import struct
import zlib

LOCAL_SIG = b"PK\x03\x04"
CENTRAL_SIG = b"PK\x01\x02"
EOCD_SIG = b"PK\x05\x06"
CFB_SIG = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_LOCAL = struct.Struct("<4sHHHHHIIIHH")      # 30바이트
_CENTRAL = struct.Struct("<4sHHHHHHIIIHHHHHII")   # 46바이트
_EOCD = struct.Struct("<4sHHHHIIH")         # 22바이트


class UnsupportedPackage(ValueError):
    """원문을 잃지 않고 다룰 수 없는 패키지 구성(ZIP64·분할·암호화 등)."""


@dataclass
class ZipEntry:
    name: str
    local: bytes           # 로컬 레코드 원본 바이트(헤더 + 데이터 + 서술자)
    central: bytes         # 중앙 디렉터리 레코드 원본 바이트
    method: int
    flags: int
    crc: int
    compressed_size: int
    size: int
    data_start: int        # local 안에서 압축 데이터가 시작하는 위치
    order: int             # 원본 파일 안 로컬 레코드 순서

    @property
    def raw_sha256(self) -> str:
        return sha256(self.local).hexdigest()


@dataclass
class PackageSnapshot:
    """원본 파일 바이트와 압축 항목 원문. 한 번 읽은 뒤 바꾸지 않는다."""

    path: str
    data: bytes
    sha256: str
    format: str                    # hwpx | hwp | unknown
    entries: "OrderedDict[str, ZipEntry]" = field(default_factory=OrderedDict)
    prefix: bytes = b""            # 첫 로컬 레코드 앞 바이트
    eocd: bytes = b""              # 끝 레코드(주석 포함) 원본
    central_order: list = field(default_factory=list)   # 중앙 디렉터리의 항목 순서

    @classmethod
    def load(cls, path) -> "PackageSnapshot":
        path = Path(path)
        data = path.read_bytes()
        digest = sha256(data).hexdigest()
        if data[:8] == CFB_SIG:
            return cls(str(path), data, digest, "hwp")
        if data[:4] != LOCAL_SIG:
            return cls(str(path), data, digest, "unknown")
        snapshot = cls(str(path), data, digest, "hwpx")
        snapshot._parse_zip()
        return snapshot

    # ---- ZIP 해석 ---------------------------------------------------------
    def _parse_zip(self) -> None:
        data = self.data
        index = data.rfind(EOCD_SIG, max(0, len(data) - 65557))
        if index < 0:
            raise UnsupportedPackage("ZIP 끝 레코드를 찾지 못했습니다.")
        sig, disk, cd_disk, here, total, cd_size, cd_offset, comment_len = _EOCD.unpack_from(data, index)
        if disk or cd_disk or here != total:
            raise UnsupportedPackage("분할 압축 파일은 지원하지 않습니다.")
        if 0xFFFF in (here, total) or 0xFFFFFFFF in (cd_size, cd_offset):
            raise UnsupportedPackage("ZIP64 패키지는 원문 보존 쓰기를 지원하지 않습니다.")
        if index + 22 + comment_len != len(data) or cd_offset + cd_size != index:
            raise UnsupportedPackage("ZIP 끝 레코드 위치가 맞지 않습니다(뒤에 덧붙은 자료가 있음).")
        self.eocd = data[index:]
        records, position = [], cd_offset
        for _ in range(total):
            if data[position:position + 4] != CENTRAL_SIG:
                raise UnsupportedPackage("중앙 디렉터리 레코드가 손상되었습니다.")
            (_, _, _, flags, method, _, _, crc, csize, usize, name_len, extra_len, comment_len2,
             disk_start, _, _, offset) = _CENTRAL.unpack_from(data, position)
            end = position + 46 + name_len + extra_len + comment_len2
            raw_name = data[position + 46:position + 46 + name_len]
            name = raw_name.decode("utf-8" if flags & 0x800 else "cp437")
            if flags & 0x1:
                raise UnsupportedPackage(f"암호화된 항목은 지원하지 않습니다: {name}")
            if 0xFFFFFFFF in (csize, usize, offset) or disk_start:
                raise UnsupportedPackage(f"ZIP64 항목은 지원하지 않습니다: {name}")
            if name in {r[0] for r in records}:
                raise UnsupportedPackage(f"같은 이름의 압축 항목이 둘 있습니다: {name}")
            records.append((name, data[position:end], flags, method, crc, csize, usize, offset))
            position = end
        if position != index:
            raise UnsupportedPackage("중앙 디렉터리 크기가 맞지 않습니다.")
        self.central_order = [r[0] for r in records]
        by_offset = sorted(records, key=lambda r: r[7])
        if by_offset and by_offset[0][7] < 0:
            raise UnsupportedPackage("로컬 레코드 위치가 잘못되었습니다.")
        self.prefix = data[:by_offset[0][7]] if by_offset else b""
        for order, record in enumerate(by_offset):
            name, central, flags, method, crc, csize, usize, offset = record
            end = by_offset[order + 1][7] if order + 1 < len(by_offset) else cd_offset
            local = data[offset:end]
            if local[:4] != LOCAL_SIG:
                raise UnsupportedPackage(f"로컬 레코드가 손상되었습니다: {name}")
            header = _LOCAL.unpack_from(local, 0)
            data_start = 30 + header[9] + header[10]
            if data_start + csize > len(local):
                raise UnsupportedPackage(f"압축 데이터 길이가 맞지 않습니다: {name}")
            self.entries[name] = ZipEntry(name, local, central, method, flags, crc, csize, usize,
                                          data_start, order)
        self.entries = OrderedDict(sorted(self.entries.items(), key=lambda kv: kv[1].order))

    # ---- 읽기 ---------------------------------------------------------------
    def names(self) -> list:
        return list(self.entries)

    def read(self, name: str) -> bytes:
        entry = self.entries[name]
        raw = entry.local[entry.data_start:entry.data_start + entry.compressed_size]
        if entry.method == 0:
            content = raw
        elif entry.method == 8:
            content = zlib.decompressobj(-15).decompress(raw)
        else:
            raise UnsupportedPackage(f"지원하지 않는 압축 방식({entry.method}): {name}")
        if zlib.crc32(content) & 0xFFFFFFFF != entry.crc or len(content) != entry.size:
            raise UnsupportedPackage(f"CRC 또는 크기 검사가 실패했습니다: {name}")
        return content

    def content_sha256(self, name: str) -> str:
        return sha256(self.read(name)).hexdigest()


def _compress(method: int, content: bytes) -> bytes:
    if method == 0:
        return content
    if method == 8:
        compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
        return compressor.compress(content) + compressor.flush()
    raise UnsupportedPackage(f"지원하지 않는 압축 방식({method})")


def build_package(snapshot: PackageSnapshot, replacements: dict) -> bytes:
    """바뀐 항목만 새로 압축한 패키지 바이트. replacements = {항목 이름: 새 내용 바이트}."""
    if snapshot.format != "hwpx":
        raise UnsupportedPackage("원문 보존 쓰기는 HWPX(ZIP)만 지원합니다.")
    unknown = set(replacements) - set(snapshot.entries)
    if unknown:
        raise UnsupportedPackage(f"패키지에 없는 항목은 더할 수 없습니다: {', '.join(sorted(unknown))}")
    if not replacements:
        return snapshot.data
    out = bytearray(snapshot.prefix)
    centrals = {}
    for name, entry in snapshot.entries.items():
        offset = len(out)
        central = bytearray(entry.central)
        if name in replacements:
            content = replacements[name]
            packed = _compress(entry.method, content)
            crc = zlib.crc32(content) & 0xFFFFFFFF
            flags = entry.flags & ~0x08            # 새 레코드는 데이터 서술자를 쓰지 않는다
            header = bytearray(entry.local[:entry.data_start])
            struct.pack_into("<H", header, 6, flags)
            struct.pack_into("<III", header, 14, crc, len(packed), len(content))
            out += header + packed
            struct.pack_into("<H", central, 8, flags)
            struct.pack_into("<III", central, 16, crc, len(packed), len(content))
        else:
            out += entry.local
        struct.pack_into("<I", central, 42, offset)
        centrals[name] = bytes(central)
    cd_offset = len(out)
    for name in snapshot.central_order:
        out += centrals[name]
    eocd = bytearray(snapshot.eocd)
    struct.pack_into("<II", eocd, 12, len(out) - cd_offset, cd_offset)
    out += eocd
    return bytes(out)


def write_package(snapshot: PackageSnapshot, replacements: dict, target) -> str:
    """패키지를 target에 쓰고 결과 SHA-256을 돌려준다. 원본 경로에는 쓰지 않는다."""
    target = Path(target)
    if target.resolve() == Path(snapshot.path).resolve():
        raise ValueError("원본 파일에 덮어쓸 수 없습니다.")
    data = build_package(snapshot, replacements)
    temp = target.with_name(target.name + ".tmp")
    temp.write_bytes(data)
    temp.replace(target)
    return sha256(data).hexdigest()


def copy_exact(source, target) -> dict:
    """원본을 바이트 그대로 복제하고 해시가 같은지 확인한다(서식 해석과 무관한 가장 확실한 보존)."""
    source, target = Path(source), Path(target)
    if target.resolve() == source.resolve():
        raise ValueError("원본과 같은 경로에는 복제할 수 없습니다.")
    original = sha256(source.read_bytes()).hexdigest()
    shutil.copyfile(source, target)
    copied = sha256(target.read_bytes()).hexdigest()
    return {"source_sha256": original, "result_sha256": copied, "identical": original == copied,
            "verdict": "검증된 완전 일치" if original == copied else "실패"}
