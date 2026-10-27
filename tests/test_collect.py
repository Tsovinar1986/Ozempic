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


def test_get_keeps_retrying_rate_limits_until_time_limit(monkeypatch):
    clock = {"now": 0.0}
    monkeypatch.setattr("collector.collect.time.monotonic", lambda: clock["now"])
    monkeypatch.setattr("collector.collect.time.time", lambda: 0.0)
    monkeypatch.setattr(
        "collector.collect.time.sleep", lambda s: clock.__setitem__("now", clock["now"] + s)
    )
    statuses = iter([422] * 8 + [200])  # more than the old 6-retry limit

    class Response:
        headers = {}

        def __init__(self, status):
            self.status_code = status

        def raise_for_status(self):
            pass

        def json(self):
            return {"data": [{"id": "item"}]}

    class Session:
        def get(self, url, params, timeout):
            return Response(next(statuses))

    assert _get(Session(), "https://example.com/api", {}) == [{"id": "item"}]
    assert clock["now"] < 20 * 60


def test_get_gives_up_after_time_limit(monkeypatch):
    import pytest

    clock = {"now": 0.0}
    monkeypatch.setattr("collector.collect.time.monotonic", lambda: clock["now"])
    monkeypatch.setattr("collector.collect.time.time", lambda: 0.0)
    monkeypatch.setattr(
        "collector.collect.time.sleep", lambda s: clock.__setitem__("now", clock["now"] + s)
    )

    class Response:
        status_code = 422
        headers = {}

    class Session:
        def get(self, url, params, timeout):
            return Response()

    with pytest.raises(RuntimeError):
        _get(Session(), "https://example.com/api", {})
    assert 20 * 60 <= clock["now"] < 20 * 60 + 5 * 60 + 10


def test_run_pauses_and_retries_day_when_api_is_unavailable(monkeypatch, tmp_path):
    from datetime import datetime, timezone

    from collector.collect import read_checkpoint, run

    clock = {"now": 0.0}
    monkeypatch.setattr("collector.collect.time.monotonic", lambda: clock["now"])
    monkeypatch.setattr(
        "collector.collect.time.sleep", lambda s: clock.__setitem__("now", clock["now"] + s)
    )
    attempts = []

    def fetch_range(session, kind, subreddit, start, end):
        attempts.append(start)
        if len(attempts) == 1:
            raise RuntimeError("giving up")
        return []

    monkeypatch.setattr("collector.collect.fetch_range", fetch_range)
    config = {
        "subreddits": ["A"],
        "kinds": ["posts"],
        "start_date": "2024-01-01",
        "settle_hours": 0,
        "max_days_per_run": 2,
        "curated_format": "jsonl",
    }

    run(config, str(tmp_path), now=datetime(2024, 1, 5, tzinfo=timezone.utc), max_minutes=300)

    jan1 = 1704067200
    assert attempts == [jan1, jan1, jan1 + 86400]
    assert clock["now"] == 30 * 60
    assert read_checkpoint(str(tmp_path)) == {"posts/A": "2024-01-03"}
