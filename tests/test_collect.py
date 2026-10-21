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
