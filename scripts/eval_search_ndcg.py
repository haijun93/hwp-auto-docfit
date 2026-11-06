#!/usr/bin/env python3
"""Compare klib and the existing SQLite FTS5 search using query<TAB>relevant path TSV."""
from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def canonical_path(path):
    return os.path.normcase(os.path.abspath(path)).replace("\\", "/")


def ndcg(ranked, relevant, k=10):
    gains = [float(relevant.get(path, 0)) for path in ranked[:k]]
    dcg = sum((2**gain - 1) / math.log2(i + 2) for i, gain in enumerate(gains))
    ideal = sorted((float(v) for v in relevant.values()), reverse=True)[:k]
    idcg = sum((2**gain - 1) / math.log2(i + 2) for i, gain in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def load_qrels(tsv):
    queries = {}
    for number, line in enumerate(Path(tsv).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) not in (2, 3):
            raise ValueError(f"TSV {number}행: query<TAB>path[<TAB>relevance] 형식이어야 합니다.")
        query, path = cols[:2]
        relevance = int(cols[2]) if len(cols) == 3 else 1
        queries.setdefault(query, {})[canonical_path(path)] = relevance
    return queries


def fts_search(db_path, query, limit):
    db = sqlite3.connect(db_path)
    try:
        # Mirrors ContentSearchIndex.search: literal FTS phrase and rank ordering.
        phrase = '"' + query.replace('"', '""') + '"'
        return [canonical_path(path) for (path,) in db.execute(
            "SELECT path FROM content_fts WHERE content_fts MATCH ? ORDER BY rank LIMIT ?", (phrase, limit))]
    finally:
        db.close()


def klib_search(exe, query, limit, box_id=None):
    # The command helper is useful for local scripted evaluations when klib has
    # a testable one-shot request mode; otherwise the caller may provide JSONL.
    payload = {"cmd": "search", "query": query, "limit": limit}
    if box_id is not None:
        payload["box_id"] = box_id
    proc = subprocess.run([str(exe), "--request-json", json.dumps(payload, ensure_ascii=False)],
                          capture_output=True, text=True, encoding="utf-8", timeout=30)
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or f"klib exit {proc.returncode}")
    result = json.loads(proc.stdout)
    if not result.get("ok"):
        raise RuntimeError(result.get("message", "klib search failed"))
    return [canonical_path(row["path"]) for row in result.get("results", [])]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qrels_tsv", help="query<TAB>relevant_path[<TAB>relevance] rows")
    parser.add_argument("--fts-db", required=True, help="SQLite database containing content_fts")
    parser.add_argument("--klib", required=True, help="klib.exe")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--box-id", type=int)
    args = parser.parse_args(argv)
    qrels = load_qrels(args.qrels_tsv)
    totals = {"FTS5": [], "Tantivy": []}
    for query, relevant in qrels.items():
        ranked = {"FTS5": fts_search(args.fts_db, query, args.limit),
                  "Tantivy": klib_search(args.klib, query, args.limit, args.box_id)}
        scores = {name: ndcg(paths, relevant, args.limit) for name, paths in ranked.items()}
        print(f"{query}\tFTS5={scores['FTS5']:.4f}\tTantivy={scores['Tantivy']:.4f}")
        for name in totals:
            totals[name].append(scores[name])
    count = len(qrels)
    for name, scores in totals.items():
        print(f"mean nDCG@{args.limit} {name}: {sum(scores) / count if count else 0.0:.4f} ({count} queries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
