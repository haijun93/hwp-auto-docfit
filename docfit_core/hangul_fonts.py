"""한/글이 쓰는 글꼴을 자동으로 찾는다(알파, 2026-10-16).

한/글은 휴먼명조·한컴돋움 같은 자기 글꼴을 Windows에 설치하지 않고 자기 폴더에서 따로 읽는다
(실측: 한컴오피스 NEO `…\\HOffice96\\Shared\\TTF\\Hwp`·`\\All`에 89종). 그래서 앱의 웹 화면(미리보기)·글꼴 목록은
이 글꼴을 모른다. 레지스트리의 한/글 공유 폴더(`HKLM\\SOFTWARE\\(WOW6432Node\\)HNC\\Shared\\Common*` 의
`SharedData Path`)와 흔한 설치 위치에서 `Shared\\TTF` 아래 글꼴을 찾고, Windows·사용자 글꼴 폴더와 합쳐
한국어 이름(글꼴 name 표의 한국어 이름, 없으면 영어 이름) 목록을 만든다. 한/글 전용 HFT(비트맵·고유 형식)는
브라우저가 읽지 못하므로 목록에서 뺀다. 글꼴 파일은 찾은 폴더 안의 TTF·OTF·TTC만 내준다.
"""
from __future__ import annotations

import glob
import os
import struct
from functools import lru_cache
from pathlib import Path

FONT_EXTENSIONS = (".ttf", ".otf", ".ttc")
MAX_FONT_BYTES = 40 * 1024 * 1024


def _registry_shared_dirs():
    """레지스트리에 적힌 한/글 공유 폴더(SharedData Path)."""
    try:
        import winreg
    except ImportError:
        return []
    found = []
    for base in (r"SOFTWARE\WOW6432Node\HNC\Shared", r"SOFTWARE\HNC\Shared"):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
        except OSError:
            continue
        with key:
            index = 0
            while True:
                try:
                    name = winreg.EnumKey(key, index)
                except OSError:
                    break
                index += 1
                if not name.lower().startswith("common"):
                    continue
                try:
                    with winreg.OpenKey(key, name) as sub:
                        value, _ = winreg.QueryValueEx(sub, "SharedData Path")
                        found.append(Path(value))
                except OSError:
                    continue
    return found


def hangul_font_dirs():
    """한/글 전용 트루타입 글꼴 폴더들(있는 것만, 중복 없이)."""
    shared = _registry_shared_dirs()
    for program in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if program:
            shared += [Path(p) for p in glob.glob(os.path.join(program, "HNC", "*", "*", "Shared"))]
    result, seen = [], set()
    for root in shared:
        ttf = root / "TTF"
        for folder in [ttf, *sorted(p for p in ttf.glob("*") if p.is_dir())] if ttf.is_dir() else []:
            key = str(folder).lower()
            if key in seen or not any(folder.glob("*.[tToO][tT][fFcC]")):
                continue
            seen.add(key)
            result.append(folder)
    return result


def system_font_dirs():
    dirs = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(Path(local) / "Microsoft" / "Windows" / "Fonts")
    return [d for d in dirs if d.is_dir()]


def _font_names(path):
    """글꼴 파일(TTC면 들어 있는 글꼴마다)의 (한국어 이름, 영어 이름)."""
    with open(path, "rb") as stream:
        data = stream.read()
    offsets = [0]
    if data[:4] == b"ttcf":
        count = struct.unpack(">I", data[8:12])[0]
        offsets = list(struct.unpack(">%dI" % count, data[12:12 + 4 * count]))
    result = []
    for offset in offsets:
        tables = struct.unpack(">H", data[offset + 4:offset + 6])[0]
        for i in range(tables):
            tag, _, table_offset, _ = struct.unpack(">4sIII", data[offset + 12 + 16 * i:offset + 28 + 16 * i])
            if tag != b"name":
                continue
            _, count, storage = struct.unpack(">HHH", data[table_offset:table_offset + 6])
            names = {}
            for j in range(count):
                platform, _, language, name_id, length, start = struct.unpack(
                    ">HHHHHH", data[table_offset + 6 + 12 * j:table_offset + 18 + 12 * j])
                if platform == 3 and name_id in (1, 16):
                    raw = data[table_offset + storage + start:table_offset + storage + start + length]
                    try:
                        names.setdefault((language, name_id), raw.decode("utf-16-be"))
                    except UnicodeDecodeError:
                        pass
            korean = names.get((0x412, 16)) or names.get((0x412, 1))
            english = names.get((0x409, 16)) or names.get((0x409, 1))
            result.append((korean, english))
    return result


@lru_cache(maxsize=1)
def catalog():
    """글꼴 목록 [{'name', 'path', 'source': 'hangul'|'system'}] — 이름 가나다순, 한/글 전용 글꼴이 같은 이름을 앞선다."""
    entries = {}
    for source, dirs in (("hangul", hangul_font_dirs()), ("system", system_font_dirs())):
        for folder in dirs:
            for path in sorted(folder.iterdir()):
                if path.suffix.lower() not in FONT_EXTENSIONS or not path.is_file():
                    continue
                try:
                    faces = _font_names(path)
                except (OSError, struct.error):
                    continue
                for korean, english in faces:
                    name = (korean or english or "").strip()
                    if name and name not in entries and not name.startswith("@"):
                        entries[name] = {"name": name, "path": str(path), "source": source}
    return sorted(entries.values(), key=lambda e: (not _is_korean(e["name"]), e["name"]))


def _is_korean(name):
    return any("\uac00" <= ch <= "\ud7a3" for ch in name)


def names(korean_only=False):
    return [e["name"] for e in catalog() if not korean_only or _is_korean(e["name"])]


def font_file(name):
    """글꼴 이름의 파일 경로(찾은 폴더 안 TTF·OTF·TTC만). 없으면 None."""
    allowed = [str(d.resolve()).lower() for d in (*hangul_font_dirs(), *system_font_dirs())]
    for entry in catalog():
        if entry["name"] != name:
            continue
        path = Path(entry["path"]).resolve()
        if path.suffix.lower() in FONT_EXTENSIONS and str(path.parent).lower() in allowed \
                and path.is_file() and path.stat().st_size <= MAX_FONT_BYTES:
            return path
    return None


def summary():
    """설정·앱 정보 화면용: 한/글 글꼴 폴더와 찾은 글꼴 수."""
    entries = catalog()
    return {"hangul_dirs": [str(d) for d in hangul_font_dirs()],
            "hangul_count": sum(1 for e in entries if e["source"] == "hangul"),
            "total": len(entries)}
