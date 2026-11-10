# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-11-10 19:59 UTC.
Oldest stream continues from 2025-03-21._

## How much data

| | rows |
|---|---:|
| comments | 2,895,563 |
| posts | 193,635 |
| Ozempic export | 63,400 of 100,000 |

Where to get it:

| repository | role | clone just the data |
|---|---|---|
| [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api/tree/data) | data is stored here | `git clone --branch data --single-branch https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data` |

## Ozempic export

`exports/ozempic_100k_comments.csv`: **63,400 of 100,000** comments mentioning "ozempic" (2024-01-01 → 2025-03-21).
Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 2,895,563 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 1,006,889 | 2024-01-01 | 2025-03-21 |
| tirzepatidecompound | 585,294 | 2024-01-01 | 2025-03-20 |
| Semaglutide | 463,712 | 2024-01-01 | 2025-03-21 |
| Mounjaro | 450,103 | 2024-01-01 | 2025-03-21 |
| Ozempic | 362,514 | 2024-01-01 | 2025-03-21 |
| compoundedsemaglutide | 27,051 | 2024-01-01 | 2025-03-21 |

**Posts: 193,635 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 68,742 | 2024-01-01 | 2025-03-21 |
| Mounjaro | 34,308 | 2024-01-01 | 2025-03-25 |
| Semaglutide | 34,190 | 2024-01-01 | 2025-03-25 |
| tirzepatidecompound | 29,923 | 2024-01-01 | 2025-03-21 |
| Ozempic | 23,946 | 2024-01-01 | 2025-03-25 |
| compoundedsemaglutide | 2,526 | 2024-01-01 | 2025-03-21 |

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
