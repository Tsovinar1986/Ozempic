# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/UitbreidenAI/drug-exp-api#readme).

_Updated automatically after every run. Last update: 2026-11-19 16:44 UTC.
Oldest stream continues from 2025-05-23._

## How much data

| | rows |
|---|---:|
| comments | 3,456,412 |
| posts | 227,712 |
| Ozempic export | 71,137 of 100,000 |

Where to get it:

| repository | role | clone just the data |
|---|---|---|
| [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api/tree/data) | code on main, data on data | `git clone --branch data --single-branch https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data` |

## Ozempic export

`exports/ozempic_100k_comments.csv`: **71,137 of 100,000** comments mentioning "ozempic" (2024-01-01 → 2025-05-23).
Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 3,456,412 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 1,235,191 | 2024-01-01 | 2025-05-23 |
| tirzepatidecompound | 734,887 | 2024-01-01 | 2025-05-22 |
| Semaglutide | 523,628 | 2024-01-01 | 2025-05-23 |
| Mounjaro | 521,740 | 2024-01-01 | 2025-05-23 |
| Ozempic | 405,260 | 2024-01-01 | 2025-05-23 |
| compoundedsemaglutide | 35,706 | 2024-01-01 | 2025-05-23 |

**Posts: 227,712 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 82,703 | 2024-01-01 | 2025-05-23 |
| Mounjaro | 39,634 | 2024-01-01 | 2025-05-23 |
| Semaglutide | 38,169 | 2024-01-01 | 2025-05-23 |
| tirzepatidecompound | 37,393 | 2024-01-01 | 2025-05-23 |
| Ozempic | 26,461 | 2024-01-01 | 2025-05-23 |
| compoundedsemaglutide | 3,352 | 2024-01-01 | 2025-05-23 |

## Files

| path | contents |
|---|---|
| `curated/comments/subreddit=<name>/date=<YYYY-MM-DD>.jsonl` | one comment per line, schema v1.0; `text` is the field for NLP |
| `curated/posts/subreddit=<name>/date=<YYYY-MM-DD>.jsonl` | one post per line, schema v1.0; join comments with `post_id == fullname` |
| `exports/ozempic_100k_comments.csv` | up to 100,000 most recent comments mentioning "ozempic" |
| `raw/<kind>/subreddit=<name>/date=<YYYY-MM-DD>.jsonl.gz` | the API response, unchanged |
| `state/checkpoint.json` | next day to collect per stream |

## Loading

After cloning from any repository above:

```python
import glob
import pandas as pd

comments = pd.concat(
    pd.read_json(f, lines=True) for f in glob.glob("ozempic-data/curated/comments/subreddit=*/*.jsonl")
)
ozempic = pd.read_csv("ozempic-data/exports/ozempic_100k_comments.csv")
```
