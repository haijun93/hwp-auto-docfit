"""Compare two HWPX files by resolved paragraph and character formatting.

HWP assigns new style IDs whenever a user changes formatting.  Comparing raw
XML therefore produces a lot of noise.  This tool resolves those IDs through
Contents/header.xml and reports the paragraphs whose effective formatting or
line layout actually changed.
"""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
from zipfile import ZipFile

from defusedxml import ElementTree as ET


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalized_element(element: ET.Element, ignored: set[str] | None = None):
    ignored = ignored or set()
    return (
        local_name(element.tag),
        tuple(sorted((key, value) for key, value in element.attrib.items() if key not in ignored)),
        (element.text or "").strip(),
        tuple(normalized_element(child, ignored) for child in element),
    )


def flatten_format(value, path="") -> dict[str, str]:
    if value is None:
        return {}
    tag, attributes, text, children = value
    here = f"{path}/{tag}" if path else tag
    result = {f"{here}/@{key}": item for key, item in attributes}
    if text:
        result[f"{here}/#text"] = text
    occurrences: dict[str, int] = {}
    for child in children:
        child_tag = child[0]
        child_index = occurrences.get(child_tag, 0)
        occurrences[child_tag] = child_index + 1
        result.update(flatten_format(child, f"{here}/{child_tag}[{child_index}]"))
    return result


def property_delta(before, after) -> dict[str, dict[str, str | None]]:
    left = flatten_format(before)
    right = flatten_format(after)
    return {
        key: {"before": left.get(key), "after": right.get(key)}
        for key in sorted(set(left) | set(right))
        if left.get(key) != right.get(key)
    }


def definitions(root: ET.Element, element_name: str) -> dict[str, tuple]:
    result = {}
    for element in root.iter():
        if local_name(element.tag) == element_name and "id" in element.attrib:
            result[element.attrib["id"]] = normalized_element(element, {"id"})
    return result


def effective_runs(runs):
    """Ignore empty runs and arbitrary splits with identical formatting."""
    result = []
    for run in runs:
        text, shape = run["text"], run["char_format"]
        if not text:
            continue
        if result and result[-1][1] == shape:
            result[-1] = (result[-1][0] + text, shape)
        else:
            result.append((text, shape))
    return result


def own_text(element: ET.Element) -> str:
    parts: list[str] = []

    def visit(node: ET.Element, is_root: bool = False) -> None:
        if not is_root and local_name(node.tag) == "p":
            return
        if local_name(node.tag) == "t" and node.text:
            parts.append(node.text)
        for child in node:
            visit(child)

    visit(element, True)
    return "".join(parts)


def line_segments(paragraph: ET.Element) -> tuple:
    for child in paragraph:
        if local_name(child.tag) == "linesegarray":
            return tuple(
                tuple(sorted(segment.attrib.items()))
                for segment in child
                if local_name(segment.tag) == "lineseg"
            )
    return ()


def load_document(path: Path):
    with ZipFile(path) as archive:
        header = ET.fromstring(archive.read("Contents/header.xml"))
        section = ET.fromstring(archive.read("Contents/section0.xml"))

    char_defs = definitions(header, "charPr")
    para_defs = definitions(header, "paraPr")
    paragraphs = []
    for element in section.iter():
        if local_name(element.tag) != "p":
            continue
        runs = []
        for child in element:
            if local_name(child.tag) != "run":
                continue
            ref = child.attrib.get("charPrIDRef", "")
            runs.append({
                "text": own_text(child),
                "char_ref": ref,
                "char_format": char_defs.get(ref),
                "char_properties": flatten_format(char_defs.get(ref)),
            })
        para_ref = element.attrib.get("paraPrIDRef", "")
        paragraphs.append({
            "text": own_text(element),
            "para_ref": para_ref,
            "para_format": para_defs.get(para_ref),
            "runs": runs,
            "lines": line_segments(element),
        })
    return paragraphs


def concise_format_delta(before, after):
    if before == after:
        return None
    return {"before": before, "after": after}


def compare(before_path: Path, after_path: Path) -> dict:
    before = load_document(before_path)
    after = load_document(after_path)
    changes = []
    matcher = difflib.SequenceMatcher(
        None,
        [paragraph["text"] for paragraph in before],
        [paragraph["text"] for paragraph in after],
        autojunk=False,
    )

    aligned: list[tuple[int | None, int | None]] = []
    for operation, before_start, before_end, after_start, after_end in matcher.get_opcodes():
        if operation == "equal":
            aligned.extend(zip(range(before_start, before_end), range(after_start, after_end)))
        elif operation == "delete":
            aligned.extend((index, None) for index in range(before_start, before_end))
        elif operation == "insert":
            aligned.extend((None, index) for index in range(after_start, after_end))
        else:
            shared = min(before_end - before_start, after_end - after_start)
            aligned.extend((before_start + offset, after_start + offset) for offset in range(shared))
            aligned.extend((index, None) for index in range(before_start + shared, before_end))
            aligned.extend((None, index) for index in range(after_start + shared, after_end))

    for before_index, after_index in aligned:
        left = before[before_index] if before_index is not None else None
        right = after[after_index] if after_index is not None else None
        if left is None or right is None:
            changes.append({
                "before_index": before_index,
                "after_index": after_index,
                "before_text": left["text"] if left else None,
                "after_text": right["text"] if right else None,
            })
            continue
        change = {
            "before_index": before_index,
            "after_index": after_index,
            "text": right["text"],
        }
        if left["text"] != right["text"]:
            change["text_change"] = {"before": left["text"], "after": right["text"]}
        if left["para_format"] != right["para_format"]:
            change["paragraph_format"] = {
                "before_ref": left["para_ref"],
                "after_ref": right["para_ref"],
                "delta": property_delta(left["para_format"], right["para_format"]),
            }
        before_runs = effective_runs(left["runs"])
        after_runs = effective_runs(right["runs"])
        if before_runs != after_runs:
            change["character_format"] = {
                "before": [
                    {"text": r["text"], "ref": r["char_ref"], "properties": r["char_properties"]}
                    for r in left["runs"]
                ],
                "after": [
                    {"text": r["text"], "ref": r["char_ref"], "properties": r["char_properties"]}
                    for r in right["runs"]
                ],
            }
        if left["lines"] != right["lines"]:
            change["line_layout"] = {"before": left["lines"], "after": right["lines"]}
        if len(change) > 3 or "text_change" in change:
            changes.append(change)
    return {
        "before": str(before_path),
        "after": str(after_path),
        "paragraph_count": {"before": len(before), "after": len(after)},
        "changed_paragraphs": changes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare(args.before, args.after)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
