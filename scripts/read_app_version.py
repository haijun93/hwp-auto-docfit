"""Print the source app version for Windows packaging scripts."""
import ast
from pathlib import Path


tree = ast.parse((Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py").read_text(encoding="utf-8"))
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "APP_VERSION" for target in node.targets
    ):
        value = ast.literal_eval(node.value)
        if isinstance(value, str) and value:
            print(value)
            break
else:
    raise SystemExit("APP_VERSION not found")
