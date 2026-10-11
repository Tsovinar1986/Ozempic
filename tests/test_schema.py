import json
from datetime import date, datetime, timezone
from pathlib import Path

import jsonschema

from collector.collect import days_to_collect
from collector.schema import to_schema

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schema"

RAW_POST = {
    "id": "1x33ulp", "name": "t3_1x33ulp", "subreddit": "Ozempic", "author": "someone",
    "created_utc": 1791710996, "title": "Recently feeling very hungry!!", "selftext": "Week 6 on 0.5mg.",
    "url": "https://www.reddit.com/r/Ozempic/comments/1x33ulp/", "permalink": "/r/Ozempic/comments/1x33ulp/",
    "link_flair_text": "Question", "score": 3, "upvote_ratio": 0.8, "num_comments": 4, "is_self": True,
    "over_18": False, "removed_by_category": None, "edited": False, "retrieved_on": 1791711000,
}
RAW_COMMENT = {
    "id": "pf7b7xr", "subreddit": "Ozempic", "author": "[deleted]", "created_utc": 1791705551,
    "body": "[removed]", "link_id": "t3_1x2s6fs", "parent_id": "t1_pf6zzzz", "is_submitter": False,
    "permalink": "/r/Ozempic/comments/1x2s6fs/_/pf7b7xr/", "score": 1, "controversiality": 0,
    "edited": 1791706000.0, "retrieved_on": 1791705600,
}


def validate(rec):
    schema = json.loads((SCHEMA_DIR / f"{rec['type']}.schema.json").read_text())
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(rec)


def test_post():
    rec = to_schema(RAW_POST)
    validate(rec)
    assert rec["type"] == "post" and rec["fullname"] == "t3_1x33ulp"
    assert rec["text"] == "Recently feeling very hungry!!\n\nWeek 6 on 0.5mg."
    assert rec["created_at"] == "2026-10-11T09:29:56Z"
    assert rec["permalink"] == "https://www.reddit.com/r/Ozempic/comments/1x33ulp/"
    assert rec["edited_utc"] is None and not rec["is_removed"]


def test_removed_comment_by_deleted_user():
    rec = to_schema(RAW_COMMENT)
    validate(rec)
    assert rec["type"] == "comment"
    assert rec["author"] is None and rec["body"] is None and rec["text"] == ""
    assert rec["is_removed"] and not rec["is_top_level"]
    assert rec["post_id"] == "t3_1x2s6fs" and rec["edited_utc"] == 1791706000


def test_link_post_without_body():
    rec = to_schema({**RAW_POST, "selftext": "", "is_self": False, "removed_by_category": "moderator"})
    validate(rec)
    assert rec["body"] is None and rec["text"] == RAW_POST["title"] and rec["is_removed"]


def test_days_to_collect_respects_settle_window_and_cap():
    now = datetime(2026, 10, 11, 9, 0, tzinfo=timezone.utc)
    # now - 72h = Oct 8 09:00, so Oct 7 is the last fully settled day.
    assert days_to_collect(date(2026, 10, 5), 72, 30, now) == [date(2026, 10, d) for d in (5, 6, 7)]
    assert days_to_collect(date(2026, 10, 5), 72, 2, now) == [date(2026, 10, 5), date(2026, 10, 6)]
    assert days_to_collect(date(2026, 10, 8), 72, 30, now) == []
