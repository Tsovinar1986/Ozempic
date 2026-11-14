# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-11-14 16:01 UTC.
Oldest stream continues from 2025-04-14._

## How much data

| | rows |
|---|---:|
| comments | 3,103,823 |
| posts | 205,942 |
| Ozempic export | 66,368 of 100,000 |

Where to get it:

| repository | role | clone just the data |
|---|---|---|
| [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api/tree/data) | data is stored here | `git clone --branch data --single-branch https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data` |

## Ozempic export

`exports/ozempic_100k_comments.csv`: **66,368 of 100,000** comments mentioning "ozempic" (2024-01-01 → 2025-04-14).
Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 3,103,823 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 1,081,365 | 2024-01-01 | 2025-04-13 |
| tirzepatidecompound | 647,165 | 2024-01-01 | 2025-04-13 |
| Semaglutide | 486,838 | 2024-01-01 | 2025-04-14 |
| Mounjaro | 478,463 | 2024-01-01 | 2025-04-14 |
| Ozempic | 379,412 | 2024-01-01 | 2025-04-14 |
| compoundedsemaglutide | 30,580 | 2024-01-01 | 2025-04-13 |

**Posts: 205,942 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 73,624 | 2024-01-01 | 2025-04-14 |
| Mounjaro | 36,120 | 2024-01-01 | 2025-04-14 |
| Semaglutide | 35,625 | 2024-01-01 | 2025-04-14 |
| tirzepatidecompound | 32,890 | 2024-01-01 | 2025-04-14 |
| Ozempic | 24,819 | 2024-01-01 | 2025-04-14 |
| compoundedsemaglutide | 2,864 | 2024-01-01 | 2025-04-14 |

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
