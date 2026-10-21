"""Incremental Reddit collector: Arctic Shift API -> raw JSONL.gz + curated Parquet/JSONL.

Work is split into whole UTC days per (kind, subreddit). Each day is written to
deterministic paths, so re-running a day overwrites its files instead of
duplicating rows. The checkpoint stores the next day to collect and is only
advanced after both raw and curated files for that day are written.

Layout under DEST (local path or s3://bucket/prefix):
    raw/{kind}/subreddit={sub}/date={YYYY-MM-DD}.jsonl.gz
    curated/{kind}/subreddit={sub}/date={YYYY-MM-DD}.parquet   (or .jsonl, see curated_format)
    state/checkpoint.json
"""

import argparse
import json
import logging
import os
import time
from datetime import date, datetime, timedelta, timezone

import fsspec
import pandas as pd
import requests
import yaml

from collector.schema import COMMENT_FIELDS, POST_FIELDS, comment_to_schema, post_to_schema

API = "https://arctic-shift.photon-reddit.com/api"
USER_AGENT = "ozempic-research-collector/0.1"
PAGE_LIMIT = 100
# Arctic Shift answers 422 "Timeout. Maybe slow down a bit" above ~20 requests/min
# and then blocks for several minutes, so stay below that.
REQUEST_PAUSE_S = 3.0
MAX_RETRIES = 6

CURATED = {
    "posts": (post_to_schema, POST_FIELDS),
    "comments": (comment_to_schema, COMMENT_FIELDS),
}

log = logging.getLogger("collector")


# --- API ---------------------------------------------------------------------

def _get(session, url, params):
    for attempt in range(MAX_RETRIES):
        time.sleep(REQUEST_PAUSE_S)
        try:
            resp = session.get(url, params=params, timeout=30)
        except (requests.ConnectionError, requests.Timeout) as e:
            wait = 2 ** attempt * 15
            log.warning("%s, retrying in %ds", type(e).__name__, wait)
            time.sleep(wait)
            continue
        # 422 is the API's rate-limit/timeout response. After it, x-ratelimit-reset-at
        # (epoch ms) moves minutes ahead while x-ratelimit-reset still says <60s.
        if resp.status_code in (422, 429) or resp.status_code >= 500:
            reset_at = int(resp.headers.get("x-ratelimit-reset-at", 0)) / 1000
            wait = max(reset_at - time.time(), 2 ** attempt * 5) + 5
            log.warning("HTTP %s, retrying in %ds", resp.status_code, wait)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()["data"]
    raise RuntimeError(f"giving up on {url} {params}")


def fetch_range(session, kind, subreddit, start_ts, end_ts):
    """All items with start_ts <= created_utc < end_ts, oldest first.

    The API's `after`/`before` bounds are both exclusive.
    """
    seen, items, cursor = set(), [], start_ts - 1
    while True:
        page = _get(session, f"{API}/{kind}/search", {
            "subreddit": subreddit, "after": cursor, "before": end_ts,
            "sort": "asc", "limit": PAGE_LIMIT,
        })
        new = [x for x in page if x["id"] not in seen]
        for x in new:
            seen.add(x["id"])
        items.extend(new)
        if len(page) < PAGE_LIMIT:
            return items
        # Re-include the last second so items sharing it across pages aren't lost
        # (dedup by id); if a page brought nothing new, step past it to avoid looping.
        last = page[-1]["created_utc"]
        cursor = last - 1 if new else last


# --- Storage -----------------------------------------------------------------

def read_checkpoint(dest):
    path = f"{dest}/state/checkpoint.json"
    fs, _ = fsspec.core.url_to_fs(path)
    if not fs.exists(path):
        return {}
    with fsspec.open(path, "r") as f:
        return json.load(f)


def write_checkpoint(dest, checkpoint):
    with fsspec.open(f"{dest}/state/checkpoint.json", "w", auto_mkdir=True) as f:
        json.dump(checkpoint, f, indent=2, sort_keys=True)


def write_raw(dest, kind, subreddit, day, items):
    path = f"{dest}/raw/{kind}/subreddit={subreddit}/date={day}.jsonl.gz"
    with fsspec.open(path, "wt", compression="gzip", auto_mkdir=True) as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def write_curated(dest, kind, subreddit, day, items, ingested_at, fmt="parquet"):
    transform, fields = CURATED[kind]
    df = pd.DataFrame([transform(item) for item in items], columns=fields)
    df = df.drop_duplicates("id", keep="last")
    df["ingested_at"] = ingested_at
    path = f"{dest}/curated/{kind}/subreddit={subreddit}/date={day}.{fmt}"
    if fmt == "jsonl":
        with fsspec.open(path, "w", encoding="utf-8", auto_mkdir=True) as f:
            df.to_json(f, orient="records", lines=True, date_format="iso", force_ascii=False)
        return
    fs, _ = fsspec.core.url_to_fs(path)
    fs.makedirs(path.rsplit("/", 1)[0], exist_ok=True)
    df.to_parquet(path, index=False)


# --- Orchestration -----------------------------------------------------------

def day_bounds(day):
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    return int(start.timestamp()), int((start + timedelta(days=1)).timestamp())


def days_to_collect(next_day, settle_hours, max_days, now):
    # Last day whose end is at least settle_hours in the past.
    last = (now - timedelta(hours=settle_hours)).date() - timedelta(days=1)
    days, day = [], next_day
    while day <= last and len(days) < max_days:
        days.append(day)
        day += timedelta(days=1)
    return days


def run(config, dest, now=None):
    now = now or datetime.now(timezone.utc)
    ingested_at = pd.Timestamp(now)
    checkpoint = read_checkpoint(dest)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    start_date = date.fromisoformat(config["start_date"])
    curated_format = config.get("curated_format", "parquet")
    if curated_format not in ("parquet", "jsonl"):
        raise ValueError(f"curated_format must be parquet or jsonl, got {curated_format!r}")

    for kind in config["kinds"]:
        for subreddit in config["subreddits"]:
            key = f"{kind}/{subreddit}"
            next_day = date.fromisoformat(checkpoint[key]) if key in checkpoint else start_date
            days = days_to_collect(next_day, config["settle_hours"], config["max_days_per_run"], now)
            if not days:
                log.info("%s: up to date (next day %s)", key, next_day)
            for day in days:
                items = fetch_range(session, kind, subreddit, *day_bounds(day))
                write_raw(dest, kind, subreddit, day, items)
                write_curated(dest, kind, subreddit, day, items, ingested_at, curated_format)
                checkpoint[key] = (day + timedelta(days=1)).isoformat()
                write_checkpoint(dest, checkpoint)
                log.info("%s %s: %d items", key, day, len(items))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default="config/subreddits.yaml")
    parser.add_argument("--dest", default=os.environ.get("DEST_URI", "data"),
                        help="local dir or s3://bucket/prefix (default: $DEST_URI or ./data)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with open(args.config) as f:
        config = yaml.safe_load(f)
    run(config, args.dest.rstrip("/"))


if __name__ == "__main__":
    main()
