"""HWPX 폴더에서 검토용 학습 목록을 작성하거나 승인한 데이터 표를 프로필로 추출한다."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from docfit_core.style_learning import build_learning_catalog, learn_reviewed_data_table


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    index = sub.add_parser("index")
    index.add_argument("folder", type=Path)
    index.add_argument("--output", type=Path, required=True)
    index.add_argument("--organization", default="미확인")
    learn = sub.add_parser("learn-table")
    learn.add_argument("source", type=Path)
    learn.add_argument("--catalog", type=Path, required=True)
    learn.add_argument("--candidate", required=True, help="목록의 표 id")
    learn.add_argument("--approve-role", choices=["data"], required=True)
    learn.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("출력 파일이 이미 있습니다. 다른 경로를 지정하세요.")
    if args.command == "index":
        if not args.folder.is_dir():
            parser.error("HWPX 원본 폴더가 없습니다.")
        paths = sorted(p for p in args.folder.rglob("*") if p.suffix.lower() == ".hwpx")
        if not paths:
            parser.error("HWPX 문서가 없습니다. HWP는 먼저 사본을 변환하세요.")
        result = build_learning_catalog(paths, root=args.folder, organization=args.organization)
    else:
        catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
        matches = [r for d in catalog["documents"] for r in d["tables"] if r["id"] == args.candidate]
        if len(matches) != 1:
            parser.error("후보 id는 목록에서 정확히 하나여야 합니다.")
        result = learn_reviewed_data_table(args.source, matches[0], approved_role=args.approve_role)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result.get("summary", {"role": result.get("role")}), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
