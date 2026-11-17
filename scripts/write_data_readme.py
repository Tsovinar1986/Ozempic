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
# Collection runs in CODE_REPO (public, so Actions minutes are free). The first repository
# is the source of truth; the workflow copies its data branch to the others after every run.
DATA_REPOS = [
    ("UitbreidenAI/drug-exp-api", "main copy (private)"),
    ("Tsovinar1986/Ozempic", "synced after every run (public)"),
    ("adele-kha/uitbreiden_drug_experience", "synced after every run (private)"),
]
EXPORT = "exports/ozempic_100k_comments.csv"
EXPORT_TARGET = 100_000
PROGRESS = "state/progress.json"
HISTORY = "state/run_history.jsonl"  # one line of totals per run that changed the data
RECENT_RUNS = 10
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


def snapshot(data_dir, now):
    """Current totals, as recorded in HISTORY."""
    checkpoint_path = data_dir / "state" / "checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {}
    export = export_stats(data_dir)
    return {
        "time": f"{now:%Y-%m-%d %H:%M}",
        "comments": sum(rows for rows, _, _ in curated_stats(data_dir, "comments").values()),
        "posts": sum(rows for rows, _, _ in curated_stats(data_dir, "posts").values()),
        "export": export[0] if export else 0,
        "oldest": min(checkpoint.values()) if checkpoint else None,
    }


def _from_old_readme(data_dir):
    """Totals from a README written before HISTORY existed, so the first run has a baseline."""
    path = data_dir / "README.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    found = {}
    for key, pattern in [
        ("comments", r"^\| comments \| ([\d,]+) \|"),
        ("posts", r"^\| posts \| ([\d,]+) \|"),
        ("export", r"^\| Ozempic export \| ([\d,]+) of"),
    ]:
        m = re.search(pattern, text, re.M)
        if not m:
            return None
        found[key] = int(m.group(1).replace(",", ""))
    m = re.search(r"Last update: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC", text)
    found["time"] = m.group(1) if m else "before tracking"
    m = re.search(r"Oldest stream continues from (\d{4}-\d{2}-\d{2})", text)
    found["oldest"] = m.group(1) if m else None
    return found


def read_history(data_dir):
    path = data_dir / HISTORY
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def record_run(data_dir, now):
    """Append the current totals to HISTORY if they changed since the last entry."""
    history = read_history(data_dir)
    if not history and (baseline := _from_old_readme(data_dir)):
        history.append(baseline)
    current = snapshot(data_dir, now)
    keys = ("comments", "posts", "export", "oldest")
    if not history or any(current[k] != history[-1].get(k) for k in keys):
        history.append(current)
    path = data_dir / HISTORY
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(entry) + "\n" for entry in history))


def _delta(n):
    return f"+{n:,}" if n >= 0 else f"{n:,}"


def _runs_section(history):
    if len(history) < 2:
        return (
            "## Latest run\n\n"
            "No earlier run recorded yet; how much each run adds is shown from the next run on."
        )
    pairs = list(zip(history, history[1:]))
    prev, last = pairs[-1]
    moved = (
        f"; the oldest stream moved from {prev['oldest']} to {last['oldest']}"
        if prev.get("oldest") and last.get("oldest") and prev["oldest"] != last["oldest"]
        else ""
    )
    lines = [
        "## Latest run",
        "",
        f"The run at {last['time']} UTC added **{_delta(last['comments'] - prev['comments'])} comments**, "
        f"**{_delta(last['posts'] - prev['posts'])} posts** and "
        f"**{_delta(last['export'] - prev['export'])}** Ozempic comments "
        f"(now {export_progress(last['export'])}){moved}.",
        "",
        f"Recent runs (newest first; full list in `{HISTORY}`):",
        "",
        "| run (UTC) | comments added | posts added | export rows added | comments total | posts total | oldest next day |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for prev, cur in reversed(pairs[-RECENT_RUNS:]):
        lines.append(
            f"| {cur['time']} | {_delta(cur['comments'] - prev['comments'])} | "
            f"{_delta(cur['posts'] - prev['posts'])} | {_delta(cur['export'] - prev['export'])} | "
            f"{cur['comments']:,} | {cur['posts']:,} | {cur.get('oldest') or 'n/a'} |"
        )
    return "\n".join(lines)


def _bar(rows, width=20):
    filled = min(width, round(width * rows / EXPORT_TARGET))
    return "█" * filled + "░" * (width - filled)


def export_progress(rows):
    """'69,735 of 100,000 (69.7%)'."""
    return f"{rows:,} of {EXPORT_TARGET:,} ({100 * rows / EXPORT_TARGET:.1f}%)"


def _export_section(export, history):
    rows, first, last = export if export else (0, "", "")
    added = (
        _delta(history[-1]["export"] - history[-2]["export"]) if len(history) >= 2 else "not known yet"
    )
    remaining = (
        f"{EXPORT_TARGET - rows:,}" if rows < EXPORT_TARGET
        else "0: target reached; each run now swaps the oldest comments for newer ones"
    )
    return f"""## Ozempic export: {export_progress(rows)}

`{_bar(rows)}` **{export_progress(rows)}** comments mentioning "ozempic" collected so far.

| | |
|---|---:|
| collected | {rows:,} |
| target | {EXPORT_TARGET:,} |
| still to collect | {remaining} |
| added by the latest run | {added} |
| comment dates | {f"{first} → {last}" if export else "n/a"} |

File: `{EXPORT}`. Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`."""


def write_progress(data_dir, now):
    """state/progress.json: headline numbers for the badge in the main README."""
    snap = snapshot(data_dir, now)
    progress = {
        "updated": f"{snap['time']} UTC",
        "ozempic_export": export_progress(snap["export"]),
        "comments": f"{snap['comments']:,}",
        "posts": f"{snap['posts']:,}",
        "oldest_next_day": snap["oldest"],
    }
    (data_dir / PROGRESS).parent.mkdir(parents=True, exist_ok=True)
    (data_dir / PROGRESS).write_text(json.dumps(progress, indent=2) + "\n")


def render(data_dir, now):
    checkpoint_path = data_dir / "state" / "checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {}
    export = export_stats(data_dir)
    history = read_history(data_dir)
    oldest = min(checkpoint.values()) if checkpoint else "n/a"
    comments = curated_stats(data_dir, "comments")
    posts = curated_stats(data_dir, "posts")
    n_comments = sum(rows for rows, _, _ in comments.values())
    n_posts = sum(rows for rows, _, _ in posts.values())
    repo_rows = "\n".join(
        f"| [{name}](https://github.com/{name}/tree/data) | {note} | "
        f"`git clone --branch data --single-branch https://github.com/{name}.git ozempic-data` |"
        for name, note in DATA_REPOS
    )

    return f"""# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic]({CODE_REPO}). This branch holds only data; the
code, the schema and how collection works are described in the [main README]({CODE_REPO}#readme).

_Updated automatically after every run. Last update: {now:%Y-%m-%d %H:%M} UTC.
Oldest stream continues from {oldest}._

**Ozempic comments: {export_progress(export[0] if export else 0)}** `{_bar(export[0] if export else 0)}`

## How much data

| | rows |
|---|---:|
| comments | {n_comments:,} |
| posts | {n_posts:,} |
| Ozempic export | {export_progress(export[0] if export else 0)} |

{_runs_section(history)}

## Where to get it

| repository | role | clone just the data |
|---|---|---|
{repo_rows}

{_export_section(export, history)}

## Collected so far

{_table("Comments", comments)}

{_table("Posts", posts)}

## Files

| path | contents |
|---|---|
| `curated/comments/subreddit=<name>/date=<YYYY-MM-DD>.jsonl` | one comment per line, schema v1.0; `text` is the field for NLP |
| `curated/posts/subreddit=<name>/date=<YYYY-MM-DD>.jsonl` | one post per line, schema v1.0; join comments with `post_id == fullname` |
| `{EXPORT}` | up to 100,000 most recent comments mentioning "ozempic" |
| `raw/<kind>/subreddit=<name>/date=<YYYY-MM-DD>.jsonl.gz` | the API response, unchanged |
| `state/checkpoint.json` | next day to collect per stream |
| `{HISTORY}` | totals after each run that added data, behind the "Latest run" numbers |
| `{PROGRESS}` | headline numbers, read by the progress badge in the main README |

## Loading

After cloning from any repository above:

```python
import glob
import pandas as pd

comments = pd.concat(
    pd.read_json(f, lines=True) for f in glob.glob("ozempic-data/curated/comments/subreddit=*/*.jsonl")
)
ozempic = pd.read_csv("ozempic-data/{EXPORT}")
```
"""


MAIN_START = "<!-- data-stats:start -->"
MAIN_END = "<!-- data-stats:end -->"


def _compact(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 10_000:
        return f"{n / 1000:.0f}k"
    if n >= 100:
        return f"{n / 1000:.1f}k"
    return str(n)


def _summary_row(kind, stats):
    total = sum(rows for rows, _, _ in stats.values())
    by_sub = " · ".join(
        f"{sub} {_compact(rows)}" for sub, (rows, _, _) in sorted(stats.items(), key=lambda kv: -kv[1][0])
    )
    if not stats:
        return f"| {kind} | 0 | | |"
    first = min(f for _, f, _ in stats.values())
    lasts = sorted(l for _, _, l in stats.values())
    days = f"{first} → {lasts[0]}" if lasts[0] == lasts[-1] else f"{first} → {lasts[0]} … {lasts[-1]}"
    return f"| {kind} | {total:,} | {by_sub} | {days} |"


def main_readme_block(data_dir, now):
    """The numbers block of the code repository's README, between MAIN_START and MAIN_END."""
    export = export_stats(data_dir)
    rows = export[0] if export else 0
    history = read_history(data_dir)
    checkpoint_path = data_dir / "state" / "checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {}
    remaining = f"{EXPORT_TARGET - rows:,} still to collect" if rows < EXPORT_TARGET else "target reached"
    latest = ""
    if len(history) >= 2:
        prev, last = history[-2], history[-1]
        latest = (
            f" The latest run ({last['time']} UTC) added {_delta(last['comments'] - prev['comments'])} comments, "
            f"{_delta(last['posts'] - prev['posts'])} posts and "
            f"{_delta(last['export'] - prev['export'])} Ozempic comments."
        )
    export_days = f"{export[1]} → {export[2]}" if export and export[0] else ""
    return f"""{MAIN_START}
<!-- Written by scripts/write_data_readme.py after every collection run; edits here are overwritten. -->
**Ozempic export: {export_progress(rows)}** `{_bar(rows)}` {remaining}.

_Numbers as of {now:%Y-%m-%d %H:%M} UTC; next day to collect: {min(checkpoint.values()) if checkpoint else "n/a"}.{latest}_

| | rows | by subreddit | days covered |
|---|---:|---|---|
{_summary_row("comments", curated_stats(data_dir, "comments"))}
{_summary_row("posts", curated_stats(data_dir, "posts"))}
| Ozempic export | {export_progress(rows)} | comments from any subreddit mentioning "ozempic" | {export_days} |
{MAIN_END}"""


def update_main_readme(readme, data_dir, now):
    """Replace the block between the markers in readme; True if the file changed."""
    text = readme.read_text(encoding="utf-8")
    start, end = text.find(MAIN_START), text.find(MAIN_END)
    if start < 0 or end < start:
        raise SystemExit(f"{readme}: markers {MAIN_START} / {MAIN_END} not found")
    new = text[:start] + main_readme_block(data_dir, now) + text[end + len(MAIN_END):]
    if new == text:
        return False
    readme.write_text(new, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data", help="data branch checkout (default: ./data)")
    parser.add_argument(
        "--main-readme",
        help="instead: only refresh the numbers block in this README of the code repository",
    )
    args = parser.parse_args()
    data_dir = Path(args.data)
    now = datetime.now(timezone.utc)
    if args.main_readme:
        changed = update_main_readme(Path(args.main_readme), data_dir, now)
        print("main README numbers updated" if changed else "main README numbers unchanged")
        return
    record_run(data_dir, now)
    write_progress(data_dir, now)
    (data_dir / "README.md").write_text(render(data_dir, now), encoding="utf-8")


if __name__ == "__main__":
    main()
