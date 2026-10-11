"""Raw Reddit JSON (Arctic Shift / Pushshift / Reddit API) -> schema v1.0 records.

See schema/post.schema.json and schema/comment.schema.json for field definitions.
"""

from datetime import datetime, timezone

SCHEMA_VERSION = "1.0"
REMOVED_MARKERS = {"[removed]", "[deleted]", "[ Removed by Reddit ]"}
POST_FIELDS = [
    "schema_version", "type", "id", "fullname", "subreddit", "author", "created_utc",
    "created_at", "title", "body", "text", "url", "permalink", "flair", "score",
    "upvote_ratio", "num_comments", "is_self", "over_18", "is_removed", "removed_by",
    "edited_utc", "source", "retrieved_utc",
]
COMMENT_FIELDS = [
    "schema_version", "type", "id", "fullname", "subreddit", "author", "created_utc",
    "created_at", "body", "text", "post_id", "parent_id", "is_top_level", "is_submitter",
    "permalink", "score", "controversiality", "is_removed", "edited_utc", "source",
    "retrieved_utc",
]


def detect_kind(raw):
    if "title" in raw or str(raw.get("name", "")).startswith("t3_"):
        return "post"
    if "link_id" in raw or str(raw.get("name", "")).startswith("t1_"):
        return "comment"
    raise ValueError(f"cannot tell post from comment: id={raw.get('id')}")


def to_schema(raw, source="arctic_shift"):
    return post_to_schema(raw, source) if detect_kind(raw) == "post" else comment_to_schema(raw, source)


def post_to_schema(raw, source="arctic_shift"):
    body = _text(raw.get("selftext"))
    title = raw.get("title") or ""
    removed_by = raw.get("removed_by_category")
    return {
        "schema_version": SCHEMA_VERSION,
        "type": "post",
        **_common(raw, "t3_"),
        "title": title,
        "body": body,
        "text": f"{title}\n\n{body}" if body else title,
        "url": raw.get("url"),
        "flair": raw.get("link_flair_text"),
        "score": _int(raw.get("score")),
        "upvote_ratio": _float(raw.get("upvote_ratio")),
        "num_comments": _int(raw.get("num_comments")),
        "is_self": bool(raw.get("is_self", False)),
        "over_18": bool(raw.get("over_18", False)),
        "is_removed": removed_by is not None or raw.get("selftext") in REMOVED_MARKERS,
        "removed_by": removed_by,
        "edited_utc": _edited(raw.get("edited")),
        "source": source,
        "retrieved_utc": _int(raw.get("retrieved_on")),
    }


def comment_to_schema(raw, source="arctic_shift"):
    body = _text(raw.get("body"))
    parent_id = raw["parent_id"]
    return {
        "schema_version": SCHEMA_VERSION,
        "type": "comment",
        **_common(raw, "t1_"),
        "body": body,
        "text": body or "",
        "post_id": raw["link_id"],
        "parent_id": parent_id,
        "is_top_level": parent_id.startswith("t3_"),
        "is_submitter": bool(raw.get("is_submitter", False)),
        "score": _int(raw.get("score")),
        "controversiality": _int(raw.get("controversiality")),
        "is_removed": raw.get("body") in REMOVED_MARKERS,
        "edited_utc": _edited(raw.get("edited")),
        "source": source,
        "retrieved_utc": _int(raw.get("retrieved_on")),
    }


def _common(raw, prefix):
    created = int(float(raw["created_utc"]))
    author = raw.get("author")
    permalink = raw.get("permalink") or ""
    return {
        "id": raw["id"],
        "fullname": f"{prefix}{raw['id']}",
        "subreddit": raw["subreddit"],
        "author": None if author in (None, "[deleted]") else author,
        "created_utc": created,
        "created_at": datetime.fromtimestamp(created, timezone.utc).isoformat().replace("+00:00", "Z"),
        "permalink": permalink if permalink.startswith("http") else f"https://www.reddit.com{permalink}",
    }


def _text(value):
    if value is None or value in REMOVED_MARKERS or not value.strip():
        return None
    return value


def _edited(value):
    # Reddit uses `false` for never edited, otherwise the edit timestamp.
    return None if value in (None, False, True) else int(float(value))


def _int(value):
    return None if value is None else int(value)


def _float(value):
    return None if value is None else float(value)
