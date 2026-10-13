"""Validate the required UI/font/renderer files before EXE packaging."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from docfit_core.flutter_bundle import validate_bundle


if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "desktop_web/flutter"
    try:
        validate_bundle(directory)
    except (ValueError, OSError) as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    print("Flutter UI bundle verified (entrypoint, font, license, local CanvasKit).")
