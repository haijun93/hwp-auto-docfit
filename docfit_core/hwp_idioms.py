"""한/글 상용구 파일(HWP.IDO)과 본문 상용구(IDIOM\\*.HWP)를 읽고 고친다(알파, 2026-10-15).

HWP.IDO는 ASCII INI 형식이다(실측: 한/글 2020, %APPDATA%\\HNC\\User\\Hwp\\60).

    [HWPIDIOM]            글자 상용구: 준말 → 본말 글자
    totalcnt=180
    version=50
    idiom0=0000279300092469     4자리 16진 UTF-16 단위: [속성][준말…][0009=탭][본말…]
    [HWPIDIOMHWP]         본문 상용구: 준말 → 이름. 내용은 IDIOM\\<준말 16진>0000.HWP 문서
    totalcnt=17
    version=50
    idiom0=0001d45c0009d45cc11cc2dd       ('표' → '표서식', 파일 IDIOM\\d45c0000.HWP)

첫 단위(속성)의 뜻은 공개돼 있지 않아 읽은 값을 그대로 보존하고, 새 항목은 한/글이 쓰는 값(글자 0, 본문 1)을 쓴다.
"""
from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

IDO_NAME = "HWP.IDO"
BODY_FOLDER = "IDIOM"
TEXT_SECTION, BODY_SECTION = "HWPIDIOM", "HWPIDIOMHWP"
MAX_KEY, MAX_VALUE, MAX_TITLE, MAX_ENTRIES = 20, 500, 100, 2000
BACKUP_FOLDER, BACKUP_KEEP = "docfit-backup", 10


class IdiomError(ValueError):
    """상용구 입력이나 파일이 올바르지 않다."""


@dataclass
class Idiom:
    key: str
    value: str
    attr: int = 0


@dataclass
class IdiomFile:
    text: list = field(default_factory=list)
    body: list = field(default_factory=list)
    versions: dict = field(default_factory=lambda: {TEXT_SECTION: "50", BODY_SECTION: "50"})
    has_body_section: bool = False


def _units(value: str):
    data = value.encode("utf-16-le", "surrogatepass")
    return [int.from_bytes(data[i:i + 2], "little") for i in range(0, len(data), 2)]


def _string(units):
    return b"".join(u.to_bytes(2, "little") for u in units).decode("utf-16-le", "surrogatepass")


def _decode(raw: str) -> Idiom:
    if len(raw) % 4 or not raw or any(c not in "0123456789abcdefABCDEF" for c in raw):
        raise IdiomError("상용구 값 형식이 올바르지 않습니다.")
    units = [int(raw[i:i + 4], 16) for i in range(0, len(raw), 4)]
    attr, rest = units[0], units[1:]
    if 9 not in rest:
        raise IdiomError("상용구 값에 준말과 본말 구분이 없습니다.")
    cut = rest.index(9)
    return Idiom(_string(rest[:cut]), _string(rest[cut + 1:]), attr)


def _encode(item: Idiom) -> str:
    return "".join(f"{u:04x}" for u in [item.attr, *_units(item.key), 9, *_units(item.value)])


def parse(data: bytes) -> IdiomFile:
    """HWP.IDO 내용을 읽는다. 모르는 줄은 무시하지 않고 오류로 알린다(잘못 덮어쓰지 않게)."""
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise IdiomError("상용구 파일 형식이 아닙니다.") from exc
    result, section = IdiomFile(), None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            if section not in (TEXT_SECTION, BODY_SECTION):
                raise IdiomError(f"알 수 없는 상용구 묶음입니다: {section}")
            result.has_body_section |= section == BODY_SECTION
            continue
        name, sep, value = line.partition("=")
        if not sep or section is None:
            raise IdiomError("상용구 파일 형식이 아닙니다.")
        if name == "version":
            result.versions[section] = value
        elif name.startswith("idiom"):
            (result.text if section == TEXT_SECTION else result.body).append(_decode(value))
        elif name != "totalcnt":
            raise IdiomError(f"알 수 없는 상용구 항목입니다: {name}")
    return result


def dump(idioms: IdiomFile) -> bytes:
    lines = []
    sections = [(TEXT_SECTION, idioms.text)]
    if idioms.body or idioms.has_body_section:
        sections.append((BODY_SECTION, idioms.body))
    for name, items in sections:
        lines += [f"[{name}]", f"totalcnt={len(items)}", f"version={idioms.versions.get(name, '50')}"]
        lines += [f"idiom{i}={_encode(item)}" for i, item in enumerate(items)]
    return ("\r\n".join(lines) + "\r\n").encode("ascii")


def body_file_name(key: str) -> str:
    """본문 상용구 문서 이름: 준말의 UTF-16 단위를 16진 4자리씩 + '0000.HWP'(실측: '표' → d45c0000.HWP)."""
    return "".join(f"{u:04x}" for u in _units(key)) + "0000.HWP"


def _check_text(value, label, limit, *, allow_newline=False):
    if not isinstance(value, str) or not value.strip():
        raise IdiomError(f"{label}을(를) 입력해 주세요.")
    if len(value) > limit:
        raise IdiomError(f"{label}은(는) {limit}자까지 쓸 수 있습니다.")
    bad = [c for c in value if ord(c) < 32 and not (allow_newline and c in "\r\n")]
    if bad or "\t" in value:
        raise IdiomError(f"{label}에 쓸 수 없는 문자(탭·제어 문자)가 있습니다.")
    return value


def validate_entries(entries, *, body=False):
    """화면에서 받은 상용구 목록 [{'key','value'|'title','attr'?}]을 검증해 Idiom 목록으로 바꾼다."""
    if not isinstance(entries, list) or len(entries) > MAX_ENTRIES:
        raise IdiomError(f"상용구는 {MAX_ENTRIES}개까지 둘 수 있습니다.")
    seen, result = set(), []
    for entry in entries:
        if not isinstance(entry, dict):
            raise IdiomError("상용구 목록을 확인해 주세요.")
        key = _check_text(entry.get("key"), "준말", MAX_KEY).strip()
        # 한/글은 글자 상용구에 같은 준말을 여러 개 둘 수 있다(실측: 앱 기본 상용구의 '*'). 본문 상용구는
        # 준말로 문서 파일 이름을 지으므로 겹치면 안 된다.
        if body and key in seen:
            raise IdiomError(f"같은 준말이 두 번 있습니다: {key}")
        seen.add(key)
        if body:
            value = _check_text(entry.get("title"), "이름", MAX_TITLE).strip()
        else:
            value = _check_text(entry.get("value"), "본말", MAX_VALUE, allow_newline=True)
        attr = entry.get("attr", 1 if body else 0)
        if not isinstance(attr, int) or not 0 <= attr <= 0xFFFF:
            attr = 1 if body else 0
        result.append(Idiom(key, value, attr))
    return result


def hangul_folder(appdata=None):
    """한/글이 상용구를 읽는 사용자 폴더(%APPDATA%\\HNC\\User\\Hwp\\<버전 번호>). HWP.IDO가 있는 폴더를 우선한다."""
    appdata = appdata or os.environ.get("APPDATA")
    if not appdata:
        return None
    base = Path(appdata) / "HNC" / "User" / "Hwp"
    if not base.is_dir():
        return None
    folders = [p for p in base.iterdir() if p.is_dir() and p.name.isdigit()]
    if not folders:
        return None
    with_file = [p for p in folders if (p / IDO_NAME).is_file()]
    return max(with_file or folders, key=lambda p: int(p.name))


class IdiomStore:
    """한/글 사용자 폴더의 상용구를 고친다. 저장할 때마다 이전 파일을 docfit-backup에 남긴다(최근 10개)."""

    def __init__(self, folder, fallback=None):
        self.folder = Path(folder)
        self.fallback = Path(fallback) if fallback else None

    @property
    def path(self):
        return self.folder / IDO_NAME

    def load(self) -> IdiomFile:
        if self.path.is_file():
            return parse(self.path.read_bytes())
        if self.fallback is not None and self.fallback.is_file():
            return parse(self.fallback.read_bytes())
        return IdiomFile()

    def _backup(self, source: Path):
        if not source.is_file():
            return None
        folder = self.folder / BACKUP_FOLDER
        folder.mkdir(exist_ok=True)
        target = folder / f"{source.name}.{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns() % 1_000_000:06d}"
        shutil.copy2(source, target)
        olds = sorted((p for p in folder.iterdir() if p.name.startswith(source.name + ".")), key=lambda p: p.name)
        for old in olds[:-BACKUP_KEEP]:
            old.unlink(missing_ok=True)
        return target

    def save(self, idioms: IdiomFile):
        if self.folder.is_symlink():
            raise IdiomError("상용구 폴더 경로가 올바르지 않습니다.")
        self.folder.mkdir(parents=True, exist_ok=True)
        data = dump(idioms)
        parse(data)   # 다시 읽혀야만 쓴다
        self._backup(self.path)
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, self.path)

    # ---- 본문 상용구 문서 ----
    def body_path(self, key):
        return self.folder / BODY_FOLDER / body_file_name(key)

    def put_body_file(self, key, source: Path):
        target = self.body_path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._backup(target)
        temporary = target.with_name(target.name + ".tmp")
        shutil.copyfile(source, temporary)
        os.replace(temporary, target)
        return target

    def rename_body_file(self, old_key, new_key):
        old, new = self.body_path(old_key), self.body_path(new_key)
        if old == new or not old.is_file():
            return
        if new.exists():
            raise IdiomError("같은 준말의 본문 상용구 문서가 이미 있습니다.")
        os.replace(old, new)

    def remove_body_file(self, key):
        path = self.body_path(key)
        if path.is_file():
            self._backup(path)
            path.unlink()
