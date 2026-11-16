# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-11-16 21:10 UTC.
Oldest stream continues from 2025-05-12._

## How much data

| | rows |
|---|---:|
| comments | 3,355,212 |
| posts | 221,526 |
| Ozempic export | 69,735 of 100,000 |

Where to get it:

| repository | role | clone just the data |
|---|---|---|
| [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api/tree/data) | data is stored here | `git clone --branch data --single-branch https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data` |

## Ozempic export

`exports/ozempic_100k_comments.csv`: **69,735 of 100,000** comments mentioning "ozempic" (2024-01-01 → 2025-05-12).
Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 3,355,212 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 1,191,808 | 2024-01-01 | 2025-05-12 |
| tirzepatidecompound | 711,198 | 2024-01-01 | 2025-05-11 |
| Semaglutide | 513,069 | 2024-01-01 | 2025-05-12 |
| Mounjaro | 507,431 | 2024-01-01 | 2025-05-12 |
| Ozempic | 397,262 | 2024-01-01 | 2025-05-12 |
| compoundedsemaglutide | 34,444 | 2024-01-01 | 2025-05-11 |

**Posts: 221,526 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 80,171 | 2024-01-01 | 2025-05-12 |
| Mounjaro | 38,595 | 2024-01-01 | 2025-05-12 |
| Semaglutide | 37,426 | 2024-01-01 | 2025-05-12 |
| tirzepatidecompound | 36,102 | 2024-01-01 | 2025-05-12 |
| Ozempic | 25,991 | 2024-01-01 | 2025-05-12 |
| compoundedsemaglutide | 3,241 | 2024-01-01 | 2025-05-12 |

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
