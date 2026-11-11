# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-11-11 19:48 UTC.
Oldest stream continues from 2025-03-26._

## How much data

| | rows |
|---|---:|
| comments | 2,940,929 |
| posts | 195,652 |
| Ozempic export | 64,026 of 100,000 |

Where to get it:

| repository | role | clone just the data |
|---|---|---|
| [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api/tree/data) | data is stored here | `git clone --branch data --single-branch https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data` |

## Ozempic export

`exports/ozempic_100k_comments.csv`: **64,026 of 100,000** comments mentioning "ozempic" (2024-01-01 → 2025-03-26).
Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 2,940,929 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 1,023,245 | 2024-01-01 | 2025-03-26 |
| tirzepatidecompound | 599,591 | 2024-01-01 | 2025-03-25 |
| Semaglutide | 468,437 | 2024-01-01 | 2025-03-26 |
| Mounjaro | 455,645 | 2024-01-01 | 2025-03-26 |
| Ozempic | 366,051 | 2024-01-01 | 2025-03-26 |
| compoundedsemaglutide | 27,960 | 2024-01-01 | 2025-03-26 |

**Posts: 195,652 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 69,802 | 2024-01-01 | 2025-03-26 |
| Mounjaro | 34,383 | 2024-01-01 | 2025-03-26 |
| Semaglutide | 34,263 | 2024-01-01 | 2025-03-26 |
| tirzepatidecompound | 30,603 | 2024-01-01 | 2025-03-26 |
| Ozempic | 23,992 | 2024-01-01 | 2025-03-26 |
| compoundedsemaglutide | 2,609 | 2024-01-01 | 2025-03-26 |

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
