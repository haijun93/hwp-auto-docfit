"""Frozen package import gate; never creates Tk windows or Hancom COM objects."""
import argparse
import importlib
import json
import pkgutil
from pathlib import Path

PACKAGES = ("docfit_core", "docfit_engine", "docfit_app", "docfit_ui")


def check():
    modules, errors = [], []
    for name in PACKAGES:
        try:
            package = importlib.import_module(name)
            names = [name] + [item.name for item in pkgutil.walk_packages(package.__path__, name + ".")]
            for module_name in names:
                importlib.import_module(module_name)
                modules.append(module_name)
        except Exception as exc:
            errors.append({"module": name, "error": str(exc)})
    try:
        from desktop_web_ui import DesktopWebBridge, _BrowserApi
        from docfit_engine.pipeline import PipelineCallbacks
        for name in ("security", "com_driver", "spacing", "formatter", "page_fit", "pipeline"):
            assert callable(importlib.import_module("docfit_engine." + name)._install)
        assert callable(DesktopWebBridge) and callable(_BrowserApi) and callable(PipelineCallbacks)
    except Exception as exc:
        errors.append({"module": "bridge/engine-symbols", "error": str(exc)})
    return {"ok": not errors, "modules": modules, "errors": errors}


def finish(result, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-test-report")
    args = parser.parse_args()
    if namespace is not None:
        names = ("작업_실행", "문서_처리_1회", "_문서_처리_1회",
                 "한글_문서_열기", "표준서식_선행_적용", "HwpAutoDocFitGUI")
        for name in names:
            if not callable(namespace.get(name)):
                result["errors"].append({"symbol": name, "error": "bootstrap symbol missing"})
        result["bootstrap_symbols"] = list(names)
        result["ok"] = not result["errors"]
    if args.self_test_report:
        Path(args.self_test_report).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return 0 if result["ok"] else 1


def main():
    return finish(check())
