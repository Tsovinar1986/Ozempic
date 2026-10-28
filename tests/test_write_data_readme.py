import json
from datetime import datetime, timezone

from scripts.write_data_readme import render


def test_render_counts_rows_and_coverage(tmp_path):
    comments = tmp_path / "curated" / "comments" / "subreddit=Ozempic"
    comments.mkdir(parents=True)
    (comments / "date=2024-01-01.jsonl").write_text('{"id": "a"}\n{"id": "b"}\n')
    (comments / "date=2024-01-02.jsonl").write_text("")
    posts = tmp_path / "curated" / "posts" / "subreddit=Zepbound"
    posts.mkdir(parents=True)
    (posts / "date=2024-03-05.jsonl").write_text('{"id": "p"}\n')
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "checkpoint.json").write_text(
        json.dumps({"comments/Ozempic": "2024-01-03", "posts/Zepbound": "2024-03-06"})
    )
    (tmp_path / "exports").mkdir()
    (tmp_path / "exports" / "ozempic_100k_comments.csv").write_text(
        "comment_id,subreddit,author,body,score,created_at,permalink\n"
        'a,Ozempic,x,"two\nlines",1,2024-01-01T10:00:00Z,/a\n'
    )

    text = render(tmp_path, datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc))

    assert "**Comments: 2 rows**" in text
    assert "| Ozempic | 2 | 2024-01-01 | 2024-01-02 |" in text
    assert "| Zepbound | 1 | 2024-03-05 | 2024-03-05 |" in text
    assert "**1 of 100,000**" in text
    assert "continues from 2024-01-03" in text
    assert "2026-10-28 12:00 UTC" in text
