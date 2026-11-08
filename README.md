# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-11-08 16:31 UTC.
Oldest stream continues from 2025-03-01._

## How much data

| | rows |
|---|---:|
| comments | 2,697,818 |
| posts | 185,772 |
| Ozempic export | 60,890 of 100,000 |

Where to get it:

| repository | role | clone just the data |
|---|---|---|
| [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api/tree/data) | data is stored here | `git clone --branch data --single-branch https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data` |

## Ozempic export

`exports/ozempic_100k_comments.csv`: **60,890 of 100,000** comments mentioning "ozempic" (2024-01-01 → 2025-03-01).
Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 2,697,818 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 939,155 | 2024-01-01 | 2025-02-28 |
| tirzepatidecompound | 515,383 | 2024-01-01 | 2025-02-28 |
| Semaglutide | 441,866 | 2024-01-01 | 2025-03-01 |
| Mounjaro | 429,258 | 2024-01-01 | 2025-02-28 |
| Ozempic | 348,735 | 2024-01-01 | 2025-03-01 |
| compoundedsemaglutide | 23,421 | 2024-01-01 | 2025-02-28 |

**Posts: 185,772 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 64,714 | 2024-01-01 | 2025-03-01 |
| Mounjaro | 34,308 | 2024-01-01 | 2025-03-25 |
| Semaglutide | 34,190 | 2024-01-01 | 2025-03-25 |
| tirzepatidecompound | 26,411 | 2024-01-01 | 2025-03-01 |
| Ozempic | 23,946 | 2024-01-01 | 2025-03-25 |
| compoundedsemaglutide | 2,203 | 2024-01-01 | 2025-03-01 |

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
