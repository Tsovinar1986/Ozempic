"""Convert raw Reddit JSON into schema v1.0 posts/comments files.

Inputs can be files or directories (searched recursively) in any of these forms:
.jsonl / .ndjson, .json (an array or {"data": [...]}), optionally .gz or .zst compressed
(.zst needs `pip install zstandard`). Posts and comments are detected per record.

Writes to --out: posts.jsonl, comments.jsonl and, with --csv, posts.csv/comments.csv.
Records are de-duplicated by id (last occurrence wins, i.e. the latest snapshot).

    python scripts/raw_to_schema.py data/raw --out data/share --csv --validate
"""

import argparse
import gzip
import io
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collector.schema import COMMENT_FIELDS, POST_FIELDS, to_schema  # noqa: E402

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schema"
SUFFIXES = (".jsonl", ".ndjson", ".json")


def open_text(path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    if path.suffix == ".zst":
        import zstandard
        stream = zstandard.ZstdDecompressor(max_window_size=2**31).stream_reader(path.open("rb"))
        return io.TextIOWrapper(stream, encoding="utf-8")
    return path.open(encoding="utf-8")


def iter_records(path):
    base = path.name.removesuffix(".gz").removesuffix(".zst")
    with open_text(path) as f:
        if base.endswith(".json"):
            data = json.load(f)
            yield from data["data"] if isinstance(data, dict) else data
            return
        for line in f:
            if line.strip():
                yield json.loads(line)


def find_inputs(paths):
    for p in map(Path, paths):
        candidates = sorted(p.rglob("*")) if p.is_dir() else [p]
        for c in candidates:
            if c.is_file() and c.name.removesuffix(".gz").removesuffix(".zst").endswith(SUFFIXES):
                yield c


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("inputs", nargs="+", help="raw files or directories")
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument("--source", default="arctic_shift", help="value for the `source` field")
    parser.add_argument("--csv", action="store_true", help="also write CSV copies")
    parser.add_argument("--validate", action="store_true", help="check every record against schema/*.json")
    args = parser.parse_args()

    records = {"post": {}, "comment": {}}
    skipped = 0
    for path in find_inputs(args.inputs):
        for raw in iter_records(path):
            try:
                rec = to_schema(raw, args.source)
            except (KeyError, ValueError, TypeError) as e:
                skipped += 1
                print(f"skip {path.name} id={raw.get('id')}: {e!r}", file=sys.stderr)
                continue
            records[rec["type"]][rec["id"]] = rec

    if args.validate:
        import jsonschema
        for kind, recs in records.items():
            schema = json.loads((SCHEMA_DIR / f"{kind}.schema.json").read_text())
            validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
            for rec in recs.values():
                validator.validate(rec)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for kind, fields in (("post", POST_FIELDS), ("comment", COMMENT_FIELDS)):
        recs = sorted(records[kind].values(), key=lambda r: (r["subreddit"], r["created_utc"]))
        with (out / f"{kind}s.jsonl").open("w", encoding="utf-8") as f:
            for rec in recs:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if args.csv:
            # utf-8-sig so Excel/Sheets detect the encoding (emoji, accents).
            pd.DataFrame(recs, columns=fields).to_csv(out / f"{kind}s.csv", index=False, encoding="utf-8-sig")
        print(f"{kind}s: {len(recs)}")
    if skipped:
        print(f"skipped {skipped} unparseable records", file=sys.stderr)


if __name__ == "__main__":
    main()
