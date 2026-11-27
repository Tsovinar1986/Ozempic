# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-11-27 00:08 UTC.
Oldest stream continues from 2025-06-01._

**Ozempic comments: 72,297 of 100,000 (72.3%)** `██████████████░░░░░░`

## How much data

| | rows |
|---|---:|
| comments | 3,530,845 |
| posts | 232,239 |
| Ozempic export | 72,297 of 100,000 (72.3%) |

## Latest run

The run at 2026-11-27 00:08 UTC added **+7,907 comments**, **+430 posts** and **+119** Ozempic comments (now 72,297 of 100,000 (72.3%)); the oldest stream moved from 2025-05-31 to 2025-06-01.

Recent runs (newest first; full list in `state/run_history.jsonl`):

| run (UTC) | comments added | posts added | export rows added | comments total | posts total | oldest next day |
|---|---:|---:|---:|---:|---:|---|
| 2026-11-27 00:08 | +7,907 | +430 | +119 | 3,530,845 | 232,239 | 2025-06-01 |
| 2026-11-25 23:41 | +1,223 | +0 | +17 | 3,522,938 | 231,809 | 2025-05-31 |
| 2026-11-23 22:14 | +1,467 | +436 | +88 | 3,521,715 | 231,809 | 2025-05-31 |
| 2026-11-22 21:25 | +1,997 | +0 | +8 | 3,520,248 | 231,373 | 2025-05-31 |
| 2026-11-21 21:02 | +9,491 | +567 | +155 | 3,518,251 | 231,373 | 2025-05-30 |
| 2026-11-21 21:01 | +67,318 | +3,614 | +906 | 3,508,760 | 230,806 | 2025-05-29 |
| 2026-11-17 22:34 | +3,437 | +522 | +84 | 3,441,442 | 227,192 | 2025-05-22 |

## Where to get it

| repository | role | clone just the data |
|---|---|---|
| [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api/tree/data) | main copy (private) | `git clone --branch data --single-branch https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data` |
| [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic/tree/data) | synced after every run (public) | `git clone --branch data --single-branch https://github.com/Tsovinar1986/Ozempic.git ozempic-data` |
| [adele-kha/uitbreiden_drug_experience](https://github.com/adele-kha/uitbreiden_drug_experience/tree/data) | synced after every run (private) | `git clone --branch data --single-branch https://github.com/adele-kha/uitbreiden_drug_experience.git ozempic-data` |

## Ozempic export: 72,297 of 100,000 (72.3%)

`██████████████░░░░░░` **72,297 of 100,000 (72.3%)** comments mentioning "ozempic" collected so far.

| | |
|---|---:|
| collected | 72,297 |
| target | 100,000 |
| still to collect | 27,703 |
| added by the latest run | +119 |
| comment dates | 2024-01-01 → 2025-06-01 |

File: `exports/ozempic_100k_comments.csv`. Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 3,530,845 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 1,264,266 | 2024-01-01 | 2025-05-31 |
| tirzepatidecompound | 752,551 | 2024-01-01 | 2025-05-31 |
| Mounjaro | 533,999 | 2024-01-01 | 2025-06-01 |
| Semaglutide | 531,599 | 2024-01-01 | 2025-06-01 |
| Ozempic | 411,786 | 2024-01-01 | 2025-06-01 |
| compoundedsemaglutide | 36,644 | 2024-01-01 | 2025-05-31 |

**Posts: 232,239 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 84,512 | 2024-01-01 | 2025-06-01 |
| Mounjaro | 40,529 | 2024-01-01 | 2025-06-01 |
| Semaglutide | 38,673 | 2024-01-01 | 2025-06-01 |
| tirzepatidecompound | 38,245 | 2024-01-01 | 2025-06-01 |
| Ozempic | 26,843 | 2024-01-01 | 2025-06-01 |
| compoundedsemaglutide | 3,437 | 2024-01-01 | 2025-06-01 |

## Files

| path | contents |
|---|---|
| `curated/comments/subreddit=<name>/date=<YYYY-MM-DD>.jsonl` | one comment per line, schema v1.0; `text` is the field for NLP |
| `curated/posts/subreddit=<name>/date=<YYYY-MM-DD>.jsonl` | one post per line, schema v1.0; join comments with `post_id == fullname` |
| `exports/ozempic_100k_comments.csv` | up to 100,000 most recent comments mentioning "ozempic" |
| `raw/<kind>/subreddit=<name>/date=<YYYY-MM-DD>.jsonl.gz` | the API response, unchanged |
| `state/checkpoint.json` | next day to collect per stream |
| `state/run_history.jsonl` | totals after each run that added data, behind the "Latest run" numbers |
| `state/progress.json` | headline numbers, read by the progress badge in the main README |

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
