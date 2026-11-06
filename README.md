# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-11-06 19:23 UTC.
Oldest stream continues from 2025-01-30._

## How much data

| | rows |
|---|---:|
| comments | 2,441,591 |
| posts | 176,326 |
| Ozempic export | 56,536 of 100,000 |

Where to get it:

| repository | role | clone just the data |
|---|---|---|
| [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api/tree/data) | data is stored here | `git clone --branch data --single-branch https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data` |

## Ozempic export

`exports/ozempic_100k_comments.csv`: **56,536 of 100,000** comments mentioning "ozempic" (2024-01-01 → 2025-01-30).
Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 2,441,591 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 844,425 | 2024-01-01 | 2025-01-29 |
| tirzepatidecompound | 447,260 | 2024-01-01 | 2025-01-29 |
| Semaglutide | 412,069 | 2024-01-01 | 2025-01-30 |
| Mounjaro | 395,346 | 2024-01-01 | 2025-01-30 |
| Ozempic | 323,870 | 2024-01-01 | 2025-01-30 |
| compoundedsemaglutide | 18,621 | 2024-01-01 | 2025-01-29 |

**Posts: 176,326 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 58,977 | 2024-01-01 | 2025-01-30 |
| Mounjaro | 34,308 | 2024-01-01 | 2025-03-25 |
| Semaglutide | 34,190 | 2024-01-01 | 2025-03-25 |
| Ozempic | 23,946 | 2024-01-01 | 2025-03-25 |
| tirzepatidecompound | 23,135 | 2024-01-01 | 2025-01-30 |
| compoundedsemaglutide | 1,770 | 2024-01-01 | 2025-01-30 |

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
