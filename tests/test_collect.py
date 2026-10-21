from collector.collect import _get


def test_get_uses_30_second_timeout(monkeypatch):
    monkeypatch.setattr("collector.collect.time.sleep", lambda _: None)
    calls = {}

    class Response:
        status_code = 200
        headers = {}

        def raise_for_status(self):
            pass

        def json(self):
            return {"data": [{"id": "item"}]}

    class Session:
        def get(self, url, params, timeout):
            calls["timeout"] = timeout
            return Response()

    result = _get(Session(), "https://example.com/api", {})

    assert result == [{"id": "item"}]
    assert calls["timeout"] == 30


def test_run_collects_the_stream_furthest_behind_first(monkeypatch, tmp_path):
    from datetime import datetime, timezone

    from collector.collect import run, write_checkpoint

    write_checkpoint(str(tmp_path), {"posts/A": "2024-01-03"})
    calls = []
    monkeypatch.setattr(
        "collector.collect.fetch_range",
        lambda session, kind, subreddit, start, end: calls.append((kind, subreddit, start)) or [],
    )
    config = {
        "subreddits": ["A"],
        "kinds": ["posts", "comments"],
        "start_date": "2024-01-01",
        "settle_hours": 0,
        "max_days_per_run": 3,
        "curated_format": "jsonl",
    }

    run(config, str(tmp_path), now=datetime(2024, 1, 5, tzinfo=timezone.utc))

    day = 86400
    jan1 = 1704067200
    assert calls == [
        ("comments", "A", jan1),
        ("comments", "A", jan1 + day),
        ("posts", "A", jan1 + 2 * day),
        ("comments", "A", jan1 + 2 * day),
        ("posts", "A", jan1 + 3 * day),
    ]


def test_run_stops_starting_days_after_time_budget(monkeypatch, tmp_path):
    from datetime import datetime, timezone

    from collector.collect import read_checkpoint, run

    clock = iter([0, 0, 1000])
    monkeypatch.setattr("collector.collect.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("collector.collect.fetch_range", lambda *args: [])
    config = {
        "subreddits": ["A"],
        "kinds": ["posts"],
        "start_date": "2024-01-01",
        "settle_hours": 0,
        "max_days_per_run": 3,
        "curated_format": "jsonl",
    }

    run(config, str(tmp_path), now=datetime(2024, 1, 5, tzinfo=timezone.utc), max_minutes=1)

    assert read_checkpoint(str(tmp_path)) == {"posts/A": "2024-01-02"}
