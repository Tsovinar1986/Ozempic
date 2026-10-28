# Ozempic Reddit data

Collected daily from Reddit (via the Arctic Shift API) by the workflow in
[Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the code, the schema and
how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-10-28 18:02 UTC.
Oldest stream continues from 2024-04-29._

## Ozempic export

`exports/ozempic_100k_comments.csv`: **17,600 of 100,000** comments mentioning "ozempic" (2024-01-01 → 2024-04-28).
Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 572,832 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 215,164 | 2024-01-01 | 2024-04-28 |
| Mounjaro | 134,151 | 2024-01-01 | 2024-04-28 |
| Semaglutide | 106,963 | 2024-01-01 | 2024-04-28 |
| Ozempic | 95,638 | 2024-01-01 | 2024-04-28 |
| tirzepatidecompound | 19,623 | 2024-01-01 | 2024-04-28 |
| compoundedsemaglutide | 1,293 | 2024-01-01 | 2024-04-28 |

**Posts: 141,493 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 44,358 | 2024-01-01 | 2024-11-03 |
| Mounjaro | 34,308 | 2024-01-01 | 2025-03-25 |
| Semaglutide | 34,190 | 2024-01-01 | 2025-03-25 |
| Ozempic | 23,946 | 2024-01-01 | 2025-03-25 |
| tirzepatidecompound | 4,571 | 2024-01-01 | 2024-06-28 |
| compoundedsemaglutide | 120 | 2024-01-01 | 2024-06-28 |

## Files

| path | contents |
|---|---|
| `curated/comments/subreddit=<name>/date=<YYYY-MM-DD>.jsonl` | one comment per line, schema v1.0; `text` is the field for NLP |
| `curated/posts/subreddit=<name>/date=<YYYY-MM-DD>.jsonl` | one post per line, schema v1.0; join comments with `post_id == fullname` |
| `exports/ozempic_100k_comments.csv` | up to 100,000 most recent comments mentioning "ozempic" |
| `raw/<kind>/subreddit=<name>/date=<YYYY-MM-DD>.jsonl.gz` | the API response, unchanged |
| `state/checkpoint.json` | next day to collect per stream |

## Loading

```bash
git clone --branch data --single-branch https://github.com/Tsovinar1986/Ozempic.git ozempic-data
```

```python
import glob
import pandas as pd

comments = pd.concat(
    pd.read_json(f, lines=True) for f in glob.glob("ozempic-data/curated/comments/subreddit=*/*.jsonl")
)
ozempic = pd.read_csv("ozempic-data/exports/ozempic_100k_comments.csv")
```
