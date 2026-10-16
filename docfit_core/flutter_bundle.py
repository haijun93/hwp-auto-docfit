"""Fail packaging when the offline Flutter UI bundle is incomplete."""

from pathlib import Path

REQUIRED_FILES = (
    "index.html", "flutter_bootstrap.js", "main.dart.js", "FONT-LICENSE.txt",
    "assets/assets/NotoSansKR.ttf", "canvaskit/canvaskit.js", "canvaskit/canvaskit.wasm",
)


def validate_bundle(directory):
    directory = Path(directory)
    missing = [name for name in REQUIRED_FILES
               if not (directory / name).is_file() or (directory / name).stat().st_size == 0]
    if missing:
        raise ValueError("Flutter UI bundle is incomplete: " + ", ".join(missing))
    return directory
