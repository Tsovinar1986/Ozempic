# Ozempic Reddit data

Reddit posts and comments from six GLP-1 subreddits, collected daily (via the Arctic Shift
API) by the workflow in [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic). This branch holds only data; the
code, the schema and how collection works are described in the [main README](https://github.com/Tsovinar1986/Ozempic#readme).

_Updated automatically after every run. Last update: 2026-11-21 21:01 UTC.
Oldest stream continues from 2025-05-29._

**Ozempic comments: 71,910 of 100,000 (71.9%)** `██████████████░░░░░░`

## How much data

| | rows |
|---|---:|
| comments | 3,508,760 |
| posts | 230,806 |
| Ozempic export | 71,910 of 100,000 (71.9%) |

## Latest run

The run at 2026-11-21 21:01 UTC added **+67,318 comments**, **+3,614 posts** and **+906** Ozempic comments (now 71,910 of 100,000 (71.9%)); the oldest stream moved from 2025-05-22 to 2025-05-29.

Recent runs (newest first; full list in `state/run_history.jsonl`):

| run (UTC) | comments added | posts added | export rows added | comments total | posts total | oldest next day |
|---|---:|---:|---:|---:|---:|---|
| 2026-11-21 21:01 | +67,318 | +3,614 | +906 | 3,508,760 | 230,806 | 2025-05-29 |
| 2026-11-17 22:34 | +3,437 | +522 | +84 | 3,441,442 | 227,192 | 2025-05-22 |

## Where to get it

| repository | role | clone just the data |
|---|---|---|
| [UitbreidenAI/drug-exp-api](https://github.com/UitbreidenAI/drug-exp-api/tree/data) | main copy (private) | `git clone --branch data --single-branch https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data` |
| [Tsovinar1986/Ozempic](https://github.com/Tsovinar1986/Ozempic/tree/data) | synced after every run (public) | `git clone --branch data --single-branch https://github.com/Tsovinar1986/Ozempic.git ozempic-data` |
| [adele-kha/uitbreiden_drug_experience](https://github.com/adele-kha/uitbreiden_drug_experience/tree/data) | synced after every run (private) | `git clone --branch data --single-branch https://github.com/adele-kha/uitbreiden_drug_experience.git ozempic-data` |

## Ozempic export: 71,910 of 100,000 (71.9%)

`██████████████░░░░░░` **71,910 of 100,000 (71.9%)** comments mentioning "ozempic" collected so far.

| | |
|---|---:|
| collected | 71,910 |
| target | 100,000 |
| still to collect | 28,090 |
| added by the latest run | +906 |
| comment dates | 2024-01-01 → 2025-05-29 |

File: `exports/ozempic_100k_comments.csv`. Columns: `comment_id, subreddit, author, body, score, created_at, permalink`.
Bodies can contain line breaks, so count rows with a CSV reader, not `wc -l`.

## Collected so far

**Comments: 3,508,760 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 1,257,236 | 2024-01-01 | 2025-05-29 |
| tirzepatidecompound | 746,676 | 2024-01-01 | 2025-05-28 |
| Mounjaro | 529,739 | 2024-01-01 | 2025-05-29 |
| Semaglutide | 528,824 | 2024-01-01 | 2025-05-29 |
| Ozempic | 409,902 | 2024-01-01 | 2025-05-29 |
| compoundedsemaglutide | 36,383 | 2024-01-01 | 2025-05-28 |

**Posts: 230,806 rows**

| subreddit | rows | from | through |
|---|---:|---|---|
| Zepbound | 83,962 | 2024-01-01 | 2025-05-29 |
| Mounjaro | 40,224 | 2024-01-01 | 2025-05-29 |
| Semaglutide | 38,506 | 2024-01-01 | 2025-05-29 |
| tirzepatidecompound | 37,969 | 2024-01-01 | 2025-05-29 |
| Ozempic | 26,730 | 2024-01-01 | 2025-05-29 |
| compoundedsemaglutide | 3,415 | 2024-01-01 | 2025-05-29 |

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
