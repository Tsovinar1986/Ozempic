# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-11-13 19:34 UTC.
Oldest stream continues from 2025-04-06._

## How much data

| | rows |
|---|---:|
| comments | 3,032,443 |
| posts | 201,453 |
| Ozempic export | 65,352 of 100,000 |

Where to get it:

| repository | role | clone just the data |
|---|---|---|
| [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api/tree/data) | data is stored here | `git clone --branch data --single-branch https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data` |

## Ozempic export

`exports/ozempic_100k_comments.csv`: **65,352 of 100,000** comments mentioning "ozempic" (2024-01-01 → 2025-04-05).
Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 3,032,443 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 1,054,585 | 2024-01-01 | 2025-04-05 |
| tirzepatidecompound | 629,584 | 2024-01-01 | 2025-04-05 |
| Semaglutide | 478,051 | 2024-01-01 | 2025-04-05 |
| Mounjaro | 467,193 | 2024-01-01 | 2025-04-05 |
| Ozempic | 373,560 | 2024-01-01 | 2025-04-05 |
| compoundedsemaglutide | 29,470 | 2024-01-01 | 2025-04-05 |

**Posts: 201,453 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 71,965 | 2024-01-01 | 2025-04-06 |
| Mounjaro | 35,352 | 2024-01-01 | 2025-04-06 |
| Semaglutide | 35,049 | 2024-01-01 | 2025-04-06 |
| tirzepatidecompound | 31,852 | 2024-01-01 | 2025-04-05 |
| Ozempic | 24,462 | 2024-01-01 | 2025-04-06 |
| compoundedsemaglutide | 2,773 | 2024-01-01 | 2025-04-06 |

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
