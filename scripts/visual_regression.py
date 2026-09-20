"""Create or verify deterministic SHA-256 baselines for rendered document pages."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("documents", nargs="+", type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    actual: dict[str, list[str]] = {}
    with tempfile.TemporaryDirectory(prefix="docfit_visual_regression_") as folder:
        root = Path(folder)
        for index, document in enumerate(args.documents):
            output = root / f"doc-{index:03d}"
            command = ["npx.cmd", "-y", "kordoc@^4", "render", str(document.resolve()),
                       "--format", "png", "-d", str(output), "--silent"]
            subprocess.run(command, check=True)
            actual[str(document)] = [hash_file(path) for path in sorted(output.glob("*.png"))]
    if args.update or not args.baseline.exists():
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(json.dumps(actual, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"baseline updated: {args.baseline}")
        return 0
    expected = json.loads(args.baseline.read_text(encoding="utf-8"))
    if actual != expected:
        print(json.dumps({"expected": expected, "actual": actual}, ensure_ascii=False, indent=2))
        return 1
    print(f"visual regression passed: {len(actual)} document(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
