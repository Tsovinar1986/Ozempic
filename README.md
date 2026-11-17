# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-11-17 21:10 UTC.
Oldest stream continues from 2025-05-21._

## How much data

| | rows |
|---|---:|
| comments | 3,438,005 |
| posts | 226,670 |
| Ozempic export | 70,920 of 100,000 |

Where to get it:

| repository | role | clone just the data |
|---|---|---|
| [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api/tree/data) | data is stored here | `git clone --branch data --single-branch https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data` |

## Ozempic export

`exports/ozempic_100k_comments.csv`: **70,920 of 100,000** comments mentioning "ozempic" (2024-01-01 → 2025-05-21).
Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 3,438,005 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 1,227,291 | 2024-01-01 | 2025-05-21 |
| tirzepatidecompound | 730,677 | 2024-01-01 | 2025-05-20 |
| Semaglutide | 521,890 | 2024-01-01 | 2025-05-21 |
| Mounjaro | 519,235 | 2024-01-01 | 2025-05-21 |
| Ozempic | 403,524 | 2024-01-01 | 2025-05-21 |
| compoundedsemaglutide | 35,388 | 2024-01-01 | 2025-05-20 |

**Posts: 226,670 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 82,277 | 2024-01-01 | 2025-05-21 |
| Mounjaro | 39,459 | 2024-01-01 | 2025-05-21 |
| Semaglutide | 38,048 | 2024-01-01 | 2025-05-21 |
| tirzepatidecompound | 37,183 | 2024-01-01 | 2025-05-21 |
| Ozempic | 26,378 | 2024-01-01 | 2025-05-21 |
| compoundedsemaglutide | 3,325 | 2024-01-01 | 2025-05-21 |

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
