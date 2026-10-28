"""Write README.md for the data branch with current row counts and coverage."""

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

CODE_REPO = "https://github.com/Tsovinar1986/Ozempic"
EXPORT = "exports/ozempic_100k_comments.csv"
DATE_RE = re.compile(r"date=(\d{4}-\d{2}-\d{2})\.")


def _rows(path):
    if path.suffix == ".parquet":
        return pq.ParquetFile(path).metadata.num_rows
    with open(path, "rb") as f:
        return sum(1 for line in f if line.strip())


def curated_stats(data_dir, kind):
    """{subreddit: (rows, first_day, last_day)} for curated/<kind>."""
    stats = {}
    for sub_dir in sorted((data_dir / "curated" / kind).glob("subreddit=*")):
        files = [f for f in sub_dir.iterdir() if f.suffix in (".jsonl", ".parquet")]
        days = sorted(m.group(1) for f in files if (m := DATE_RE.search(f.name)))
        if days:
            stats[sub_dir.name.split("=", 1)[1]] = (sum(_rows(f) for f in files), days[0], days[-1])
    return stats


def export_stats(data_dir):
    """(rows, first created_at day, last created_at day) of the Ozempic export, or None."""
    path = data_dir / EXPORT
    if not path.exists():
        return None
    csv.field_size_limit(sys.maxsize)
    with open(path, newline="", encoding="utf-8-sig") as f:
        days = [row["created_at"][:10] for row in csv.DictReader(f)]
    return (len(days), min(days), max(days)) if days else (0, "", "")


def _table(kind, stats):
    total = sum(rows for rows, _, _ in stats.values())
    lines = [
        f"**{kind}: {total:,} rows**",
        "",
        "| subreddit | rows | from | through |",
        "|---|---:|---|---|",
    ]
    for sub, (rows, first, last) in sorted(stats.items(), key=lambda kv: -kv[1][0]):
        lines.append(f"| {sub} | {rows:,} | {first} | {last} |")
    return "\n".join(lines)


def render(data_dir, now):
    checkpoint_path = data_dir / "state" / "checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {}
    export = export_stats(data_dir)
    export_line = (
        f"**{export[0]:,} of 100,000** comments mentioning \"ozempic\" ({export[1]} → {export[2]})"
        if export else "not generated yet"
    )
    oldest = min(checkpoint.values()) if checkpoint else "n/a"

    return f"""# Ozempic Reddit data

Collected daily from Reddit (via the Arctic Shift API) by the workflow in
[Tsovinar1986/Ozempic]({CODE_REPO}). This branch holds only data; the code, the schema and
how collection works are described in the [main README]({CODE_REPO}#readme).

_Updated automatically after every run. Last update: {now:%Y-%m-%d %H:%M} UTC.
Oldest stream continues from {oldest}._

## Ozempic export

`{EXPORT}`: {export_line}.
Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

{_table("Comments", curated_stats(data_dir, "comments"))}

{_table("Posts", curated_stats(data_dir, "posts"))}

## Files

| path | contents |
|---|---|
| `curated/comments/subreddit=<name>/date=<YYYY-MM-DD>.jsonl` | one comment per line, schema v1.0; `text` is the field for NLP |
| `curated/posts/subreddit=<name>/date=<YYYY-MM-DD>.jsonl` | one post per line, schema v1.0; join comments with `post_id == fullname` |
| `{EXPORT}` | up to 100,000 most recent comments mentioning "ozempic" |
| `raw/<kind>/subreddit=<name>/date=<YYYY-MM-DD>.jsonl.gz` | the API response, unchanged |
| `state/checkpoint.json` | next day to collect per stream |

## Loading

```bash
git clone --branch data --single-branch {CODE_REPO}.git ozempic-data
```

```python
import glob
import pandas as pd

comments = pd.concat(
    pd.read_json(f, lines=True) for f in glob.glob("ozempic-data/curated/comments/subreddit=*/*.jsonl")
)
ozempic = pd.read_csv("ozempic-data/{EXPORT}")
```
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data", help="data branch checkout (default: ./data)")
    args = parser.parse_args()
    data_dir = Path(args.data)
    (data_dir / "README.md").write_text(render(data_dir, datetime.now(timezone.utc)), encoding="utf-8")


if __name__ == "__main__":
    main()
