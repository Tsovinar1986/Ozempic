# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-11-23 22:14 UTC.
Oldest stream continues from 2025-05-31._

**Ozempic comments: 72,161 of 100,000 (72.2%)** `██████████████░░░░░░`

## How much data

| | rows |
|---|---:|
| comments | 3,521,715 |
| posts | 231,809 |
| Ozempic export | 72,161 of 100,000 (72.2%) |

## Latest run

The run at 2026-11-23 22:14 UTC added **+1,467 comments**, **+436 posts** and **+88** Ozempic comments (now 72,161 of 100,000 (72.2%)).

Recent runs (newest first; full list in `state/run_history.jsonl`):

| run (UTC) | comments added | posts added | export rows added | comments total | posts total | oldest next day |
|---|---:|---:|---:|---:|---:|---|
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

## Ozempic export: 72,161 of 100,000 (72.2%)

`██████████████░░░░░░` **72,161 of 100,000 (72.2%)** comments mentioning "ozempic" collected so far.

| | |
|---|---:|
| collected | 72,161 |
| target | 100,000 |
| still to collect | 27,839 |
| added by the latest run | +88 |
| comment dates | 2024-01-01 → 2025-05-31 |

File: `exports/ozempic_100k_comments.csv`. Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 3,521,715 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 1,261,079 | 2024-01-01 | 2025-05-30 |
| tirzepatidecompound | 750,783 | 2024-01-01 | 2025-05-30 |
| Mounjaro | 531,267 | 2024-01-01 | 2025-05-30 |
| Semaglutide | 530,822 | 2024-01-01 | 2025-05-31 |
| Ozempic | 411,199 | 2024-01-01 | 2025-05-31 |
| compoundedsemaglutide | 36,565 | 2024-01-01 | 2025-05-30 |

**Posts: 231,809 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 84,352 | 2024-01-01 | 2025-05-31 |
| Mounjaro | 40,431 | 2024-01-01 | 2025-05-31 |
| Semaglutide | 38,623 | 2024-01-01 | 2025-05-31 |
| tirzepatidecompound | 38,161 | 2024-01-01 | 2025-05-31 |
| Ozempic | 26,808 | 2024-01-01 | 2025-05-31 |
| compoundedsemaglutide | 3,434 | 2024-01-01 | 2025-05-31 |

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
