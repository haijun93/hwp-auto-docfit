"""앱과 함께 배포하는 kordoc 실행 꾸러미(Node.js + kordoc)를 찾고 설치한다.

폐쇄망 PC에서는 npm으로 kordoc을 받을 수 없으므로, 빌드할 때 고정 버전의
Node.js와 kordoc을 한 꾸러미로 만들어 실행 파일과 함께 전달한다.

꾸러미 구조(폴더 또는 같은 구조의 ZIP):
    runtime.json                         {"kordoc": "4.21.30", "node": "22.23.3", ...}
    node/node.exe                        공식 Node.js 실행 파일
    app/node_modules/kordoc/dist/cli.js  kordoc 진입점

찾는 순서:
1. 실행 파일 옆 'kordoc-runtime' 폴더(그대로 사용, 설치 불필요)
2. %LOCALAPPDATA%\\HwpAutoDocFit\\kordoc-runtime\\<버전> (꾸러미 ZIP에서 설치한 것)
실행 파일 옆에 꾸러미 ZIP만 있으면 처음 쓸 때 2번 위치에 안전하게 풀어 둔다.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import uuid
import zipfile
import re
from docfit_infra.storage.process_lock import ProcessLock
from pathlib import Path, PurePosixPath

RUNTIME_FOLDER_NAME = "kordoc-runtime"
RUNTIME_PACK_NAME = "HWP_AutoDocFit_kordoc_runtime.zip"
MANIFEST_NAME = "runtime.json"
MAX_PACK_FILES = 20_000
MAX_PACK_BYTES = 700 * 1024 * 1024


class RuntimePackError(RuntimeError):
    pass


def app_directory() -> Path:
    """실행 파일(배포본) 또는 소스 저장소의 최상위 폴더."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def installed_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    return (Path(base) if base else Path.home() / ".hwp_auto_docfit") / "HwpAutoDocFit" / RUNTIME_FOLDER_NAME


def model_cache_dir() -> Path:
    """kordoc OCR·수식 모델 위치(폐쇄망에서는 'kordoc models --import'로 미리 넣는다)."""
    base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    return (Path(base) if base else Path.home() / ".hwp_auto_docfit") / "HwpAutoDocFit" / "kordoc-models"


def _node_in(folder: Path) -> Path | None:
    for candidate in (folder / "node" / "node.exe", folder / "node" / "bin" / "node", folder / "node" / "node"):
        if candidate.is_file():
            return candidate
    return None


def runtime_in(folder: Path, version: str) -> tuple[str, str] | None:
    """folder가 지정 버전의 완전한 꾸러미이면 (node, cli.js) 경로를 돌려준다."""
    try:
        manifest = json.loads((folder / MANIFEST_NAME).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    if not isinstance(manifest, dict) or manifest.get("kordoc") != version:
        return None
    node = _node_in(folder)
    cli = folder / "app" / "node_modules" / "kordoc" / "dist" / "cli.js"
    if node is None or not cli.is_file():
        return None
    return str(node), str(cli)


def find_runtime(version: str) -> tuple[str, str] | None:
    for folder in (app_directory() / RUNTIME_FOLDER_NAME, installed_root() / version):
        found = runtime_in(folder, version)
        if found:
            return found
    return None


def bundled_pack() -> Path | None:
    pack = app_directory() / RUNTIME_PACK_NAME
    return pack if pack.is_file() else None


def _safe_member(name: str) -> PurePosixPath:
    """ZIP 항목 이름이 꾸러미 폴더 안의 상대 경로인지 확인한다(절대 경로·상위 폴더·드라이브 금지)."""
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (not path.parts or normalized.startswith("/") or ".." in path.parts
            or any(":" in part for part in path.parts)):
        raise RuntimePackError(f"꾸러미에 허용되지 않는 경로가 있습니다: {name}")
    return path


def install_pack(pack: str | Path, version: str, root: str | Path | None = None) -> Path:
    """Serialize first installation across callers and reuse the winner."""
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise RuntimePackError("kordoc 버전 형식이 올바르지 않습니다.")
    root = Path(root) if root is not None else installed_root()
    with ProcessLock(root / (version + ".install.lock")):
        return _install_pack_locked(pack, version, root)


def _install_pack_locked(pack, version, root):
    """꾸러미 ZIP을 검사한 뒤 root/<version>에 원자적으로 푼다. 이미 있으면 그대로 쓴다."""
    pack = Path(pack)
    root = Path(root) if root is not None else installed_root()
    destination = root / version
    if runtime_in(destination, version):
        return destination
    try:
        archive = zipfile.ZipFile(pack)
    except (OSError, zipfile.BadZipFile) as exc:
        raise RuntimePackError(f"kordoc 꾸러미를 열 수 없습니다: {pack.name}") from exc
    with archive:
        members = archive.infolist()
        if len(members) > MAX_PACK_FILES:
            raise RuntimePackError("kordoc 꾸러미의 파일 수가 너무 많습니다.")
        if sum(member.file_size for member in members) > MAX_PACK_BYTES:
            raise RuntimePackError("kordoc 꾸러미의 압축 해제 크기가 너무 큽니다.")
        names = {str(_safe_member(member.filename)).rstrip("/") for member in members}
        if MANIFEST_NAME not in names:
            raise RuntimePackError("kordoc 꾸러미에 runtime.json이 없습니다.")
        try:
            manifest = json.loads(archive.read(MANIFEST_NAME).decode("utf-8"))
        except (KeyError, ValueError) as exc:
            raise RuntimePackError("kordoc 꾸러미의 runtime.json을 읽을 수 없습니다.") from exc
        if not isinstance(manifest, dict) or manifest.get("kordoc") != version:
            raise RuntimePackError(
                f"kordoc 꾸러미 버전이 다릅니다(필요 {version}, 꾸러미 {manifest.get('kordoc') if isinstance(manifest, dict) else '?'}).")
        root.mkdir(parents=True, exist_ok=True)
        staging = root / f".installing-{uuid.uuid4().hex}"
        try:
            for member in members:
                relative = _safe_member(member.filename)
                target = staging.joinpath(*relative.parts)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output, 1024 * 1024)
            if not runtime_in(staging, version):
                raise RuntimePackError("kordoc 꾸러미에 node 또는 kordoc 실행 파일이 없습니다.")
            if destination.exists():
                shutil.rmtree(destination, ignore_errors=True)
            os.replace(staging, destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
    return destination


def ensure_runtime(version: str) -> tuple[str, str] | None:
    """준비된 꾸러미를 찾고, 없으면 실행 파일 옆 꾸러미 ZIP을 설치해서라도 돌려준다."""
    found = find_runtime(version)
    if found:
        return found
    pack = bundled_pack()
    if pack is None:
        return None
    return runtime_in(install_pack(pack, version), version)


OCR_MODEL_FILES = ("det.onnx", "rec_korean.onnx", "rec_korean.yml")


def ocr_models_present() -> bool:
    folder = model_cache_dir() / "ppocr"
    return all((folder / name).is_file() and (folder / name).stat().st_size > 0 for name in OCR_MODEL_FILES)
