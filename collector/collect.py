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
import itertools
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
# and then blocks for several minutes. With request latency, a 3s pause still tripped
# blocks every ~10 minutes on long runs, so stay well below that.
REQUEST_PAUSE_S = 4.0
# A request keeps retrying until this much time has passed: rate-limit blocks can last
# well over the old 6 retries (~6 min), which ended long runs early. Each wait is capped
# so a stuck request still gives up well inside the workflow's step timeout.
RETRY_FOR_S = 20 * 60
MAX_WAIT_S = 5 * 60
# When a request gives up during a time-budgeted run (API blocked or down), pause this
# long and retry the same day instead of ending the run.
COOLDOWN_S = 30 * 60

CURATED = {
    "posts": (post_to_schema, POST_FIELDS),
    "comments": (comment_to_schema, COMMENT_FIELDS),
}

log = logging.getLogger("collector")


# --- API ---------------------------------------------------------------------

def _get(session, url, params):
    give_up_at = time.monotonic() + RETRY_FOR_S
    for attempt in itertools.count():
        if time.monotonic() >= give_up_at:
            break
        time.sleep(REQUEST_PAUSE_S)
        try:
            resp = session.get(url, params=params, timeout=30)
        except (requests.ConnectionError, requests.Timeout) as e:
            wait = min(2 ** attempt * 15, MAX_WAIT_S)
            log.warning("%s, retrying in %ds", type(e).__name__, wait)
            time.sleep(wait)
            continue
        # 422 is the API's rate-limit/timeout response. After it, x-ratelimit-reset-at
        # (epoch ms) moves minutes ahead while x-ratelimit-reset still says <60s.
        if resp.status_code in (422, 429) or resp.status_code >= 500:
            reset_at = int(resp.headers.get("x-ratelimit-reset-at", 0)) / 1000
            wait = min(max(reset_at - time.time(), 2 ** attempt * 5) + 5, MAX_WAIT_S)
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


def run(config, dest, now=None, max_minutes=None):
    now = now or datetime.now(timezone.utc)
    deadline = time.monotonic() + max_minutes * 60 if max_minutes else None
    ingested_at = pd.Timestamp(now)
    checkpoint = read_checkpoint(dest)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    start_date = date.fromisoformat(config["start_date"])
    curated_format = config.get("curated_format", "parquet")
    if curated_format not in ("parquet", "jsonl"):
        raise ValueError(f"curated_format must be parquet or jsonl, got {curated_format!r}")

    pending = {}
    for kind in config["kinds"]:
        for subreddit in config["subreddits"]:
            key = f"{kind}/{subreddit}"
            next_day = date.fromisoformat(checkpoint[key]) if key in checkpoint else start_date
            days = days_to_collect(next_day, config["settle_hours"], config["max_days_per_run"], now)
            if days:
                pending[(kind, subreddit)] = days
            else:
                log.info("%s: up to date (next day %s)", key, next_day)

    # Always collect the day of the stream that is furthest behind (ties: config order),
    # so when the job timeout cuts a run short, every stream has advanced evenly.
    while pending:
        if deadline and time.monotonic() >= deadline:
            log.info("time budget of %s min used up; the next run continues from the checkpoint",
                     max_minutes)
            return
        kind, subreddit = min(pending, key=lambda k: pending[k][0])
        day = pending[(kind, subreddit)][0]
        key = f"{kind}/{subreddit}"
        try:
            items = fetch_range(session, kind, subreddit, *day_bounds(day))
        except RuntimeError as e:
            if not deadline:
                raise
            log.warning("%s; pausing %d min, then retrying %s %s", e, COOLDOWN_S // 60, key, day)
            if os.environ.get("GITHUB_ACTIONS"):
                print(f"::warning::Arctic Shift API unavailable, paused collection: {e}", flush=True)
            time.sleep(min(COOLDOWN_S, max(0, deadline - time.monotonic())))
            continue
        pending[(kind, subreddit)].pop(0)
        if not pending[(kind, subreddit)]:
            del pending[(kind, subreddit)]
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
    parser.add_argument("--max-minutes", type=float,
                        help="stop starting new days after this long and exit cleanly")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with open(args.config) as f:
        config = yaml.safe_load(f)
    run(config, args.dest.rstrip("/"), max_minutes=args.max_minutes)


if __name__ == "__main__":
    main()
