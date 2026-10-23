"""Check formatter moves against the pinned pre-split Git revision (no COM)."""
import argparse
import ast
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "3aaa6c3da23c0dfa6b0f27f46e51526f9de527b6"


def definitions(source):
    installer = next(n for n in ast.parse(source).body
                     if isinstance(n, ast.FunctionDef) and n.name == "_install")
    return {n.name: n for branch in installer.body if isinstance(branch, ast.If)
            for n in branch.body if isinstance(n, ast.FunctionDef)}


def verify():
    original = subprocess.check_output(
        ["git", "show", f"{BASE}:docfit_engine/formatter.py"], cwd=ROOT).decode("utf-8")
    before = definitions(original)
    manifest = json.loads((ROOT / "scripts/formatter_split_manifest.json").read_text(encoding="utf-8"))
    assert manifest["base"] == BASE
    locations = {"docfit_engine/formatter.py": definitions(
        (ROOT / "docfit_engine/formatter.py").read_text(encoding="utf-8"))}
    for module, names in manifest["modules"].items():
        path = f"docfit_engine/{module}.py"
        locations[path] = definitions((ROOT / path).read_text(encoding="utf-8"))
        assert set(locations[path]) == set(names), f"manifest mismatch: {path}"
    after = {}
    for path, functions in locations.items():
        for name, node in functions.items():
            assert name not in after, f"duplicate: {name}"
            after[name] = node
    assert before.keys() == after.keys(), "missing or added formatter functions"
    for name, node in before.items():
        assert ast.dump(node, include_attributes=False) == ast.dump(after[name], include_attributes=False), name
    moved = sum(len(names) for names in manifest["modules"].values())
    return {"base": BASE, "functions": len(before), "moved": moved,
            "unchanged": len(before) - moved, "ast_mismatches": 0,
            "modules": {path: len(functions) for path, functions in locations.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = verify()
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
