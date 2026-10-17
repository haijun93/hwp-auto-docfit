"""Offline smoke test for the Pandoc executable included in the runtime pack."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def main(runtime: Path) -> int:
    pandoc = runtime / "pandoc" / "pandoc.exe"
    if not pandoc.is_file():
        raise SystemExit(f"Bundled Pandoc missing: {pandoc}")
    version = subprocess.run([str(pandoc), "--version"], capture_output=True, text=True,
                             timeout=30, check=True).stdout.splitlines()[0]
    if "3.12.1" not in version:
        raise SystemExit(f"Unexpected Pandoc version: {version}")
    with tempfile.TemporaryDirectory(prefix="docfit-pandoc-smoke-") as directory:
        root = Path(directory)
        markdown = root / "fixture.md"
        markdown.write_text("# Offline conversion check\n\nA bundled test.\n", encoding="utf-8")
        for extension, format_name, required_member in (
                ("docx", "docx", "word/document.xml"),
                ("epub", "epub3", "mimetype")):
            output = root / f"fixture.{extension}"
            subprocess.run([str(pandoc), str(markdown), f"--to={format_name}",
                            "--output", str(output)], capture_output=True, text=True,
                           timeout=60, check=True)
            if not output.is_file() or output.stat().st_size == 0:
                raise SystemExit(f"Pandoc did not create {extension.upper()}")
            with zipfile.ZipFile(output) as archive:
                if required_member not in archive.namelist():
                    raise SystemExit(f"Invalid {extension.upper()} package: {required_member} missing")
        html = root / "fixture.html"
        subprocess.run([str(pandoc), str(markdown), "--from=markdown", "--to=html5",
                        "--standalone", "--embed-resources", "--output", str(html)], capture_output=True, text=True,
                       timeout=60, check=True)
        contents = html.read_text(encoding="utf-8")
        if "<!DOCTYPE html>" not in contents or "Offline conversion check" not in contents:
            raise SystemExit("Pandoc did not create a valid standalone HTML document")
        html_source = root / "source.html"
        html_source.write_text("<!doctype html><html><body><h1>HTML input check</h1><p>Round trip.</p></body></html>",
                               encoding="utf-8")
        for extension, format_name, required_member in (
                ("docx", "docx", "word/document.xml"),
                ("epub", "epub3", "mimetype")):
            output = root / f"from-html.{extension}"
            subprocess.run([str(pandoc), str(html_source), "--from=html", f"--to={format_name}",
                            "--output", str(output)], capture_output=True, text=True,
                           timeout=60, check=True)
            with zipfile.ZipFile(output) as archive:
                if required_member not in archive.namelist():
                    raise SystemExit(f"HTML to {extension.upper()} conversion failed")
    print(f"Bundled Pandoc {version}: HTML↔DOCX/EPUB/Markdown conversion passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
