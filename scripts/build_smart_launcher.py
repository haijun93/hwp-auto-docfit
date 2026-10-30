"""Build a single-file, cache-backed Windows launcher around the onedir app."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "__DOCFIT_MANIFEST__.txt"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_payload(bundle: Path, output_zip: Path, version: str) -> tuple[str, Path]:
    if not bundle.is_dir():
        raise FileNotFoundError(f"onedir bundle not found: {bundle}")
    files = sorted(p for p in bundle.rglob("*") if p.is_file())
    exe = bundle / "HWP_AutoDocFit.exe"
    if not exe.is_file():
        raise FileNotFoundError(f"onedir app executable not found: {exe}")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output_zip.with_suffix(".manifest.txt")
    records: list[tuple[str, int, str, Path]] = []
    for path in files:
        relative = path.relative_to(bundle).as_posix()
        if relative == "HWP_AutoDocFit.exe":
            relative = "app_main.exe"
        if any(c in relative for c in "\t\r\n"):
            raise ValueError(f"unsupported tab/newline in bundle path: {relative!r}")
        records.append((relative, path.stat().st_size, sha256_file(path), path))
    if not any(name == "app_main.exe" for name, _, _, _ in records):
        raise ValueError("bundle does not contain app_main.exe")

    lines = [f"V\t{version}"]
    lines.extend(f"F\t{digest}\t{size}\t{name}" for name, size, digest, _ in records)
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for name, _, _, source in records:
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            with source.open("rb") as source_stream, archive.open(info, "w", force_zip64=True) as target_stream:
                shutil.copyfileobj(source_stream, target_stream, 1024 * 1024)
    payload_hash = sha256_file(output_zip)
    manifest_path.write_text(
        f"V\t{version}\nP\t{payload_hash}\n" + "\n".join(
            f"F\t{digest}\t{size}\t{name}" for name, size, digest, _ in records
        ) + "\n",
        encoding="utf-8", newline="\n",
    )
    return payload_hash, manifest_path


def find_csc() -> Path:
    candidates = [
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe",
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Microsoft.NET" / "Framework" / "v4.0.30319" / "csc.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(".NET Framework csc.exe was not found; install .NET Framework 4.x developer tools.")


def compile_launcher(
    payload_zip: Path,
    manifest: Path,
    output_exe: Path,
    version: str,
    icon: Path,
    splash: Path,
) -> None:
    if os.name != "nt":
        raise OSError("smart portable launcher compilation requires Windows")
    work = output_exe.parent / "smart-launcher-compiler"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    output_exe.parent.mkdir(parents=True, exist_ok=True)
    csc = find_csc()
    version_match = re.match(r"^(\d+(?:\.\d+){0,3})", version)
    if not version_match:
        raise ValueError(f"version has no numeric file-version prefix: {version}")
    parts = version_match.group(1).split(".")
    numeric_version = ".".join((parts + ["0", "0", "0", "0"])[:4])
    source = ROOT / "launcher" / "smart_launcher.cs"
    if not splash.is_file():
        raise FileNotFoundError(f"native launcher splash image not found: {splash}")
    # 런처는 WinForms·System.Drawing 없이 Win32로 스플래시를 그리므로 PNG를 24비트 BMP로 바꿔 넣는다.
    from PIL import Image

    splash_bmp = work / "splash.bmp"
    with Image.open(splash) as image:
        image.convert("RGB").save(splash_bmp, format="BMP")
    command = [
        str(csc), "/nologo", "/codepage:65001", "/target:winexe", "/optimize+", "/platform:anycpu",
        f"/out:{output_exe}", f"/win32icon:{icon}",
        f"/resource:{payload_zip},DocFitPayload", f"/resource:{manifest},DocFitManifest",
        f"/resource:{splash_bmp},DocFitSplash",
        "/reference:System.IO.Compression.dll",
        "/reference:System.Core.dll", str(source),
    ]
    # csc accepts Assembly* attributes from a generated source file; keep them versioned per build.
    info_source = work / "BuildInfo.cs"
    info_source.write_text(
        "using System.Reflection;\n"
        f"[assembly: AssemblyTitle(\"HWP AutoDocFit Smart Portable\")]\n"
        f"[assembly: AssemblyProduct(\"HWP AutoDocFit\")]\n"
        f"[assembly: AssemblyDescription(\"HWP AutoDocFit cache-backed portable launcher\")]\n"
        f"[assembly: AssemblyFileVersion(\"{numeric_version}\")]\n"
        f"[assembly: AssemblyVersion(\"{numeric_version}\")]\n",
        encoding="utf-8",
    )
    command.append(str(info_source))
    subprocess.run(command, cwd=ROOT, check=True)


def build(bundle: Path, output_exe: Path, version: str) -> tuple[str, Path]:
    if not version or any(c in version for c in "\r\n\t"):
        raise ValueError("version must be a single non-empty line")
    payload = output_exe.parent / "smart-launcher-build" / "payload.zip"
    payload_hash, manifest = make_payload(bundle.resolve(), payload, version)
    compile_launcher(
        payload, manifest, output_exe.resolve(), version,
        ROOT / "resources" / "app_icon.ico", ROOT / "resources" / "splash.png",
    )
    return payload_hash, output_exe.resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=ROOT / "dist" / "HWP_AutoDocFit")
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "HWP_AutoDocFit.exe")
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    digest, output = build(args.bundle, args.output, args.version)
    print(f"Created {output} ({output.stat().st_size:,} bytes); cache payload sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
