import json
from datetime import datetime, timezone

from scripts.write_data_readme import read_history, record_run, render


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
    assert "| comments | 2 |" in text
    assert "| Ozempic export | 1 of 100,000 |" in text
    assert "https://github.com/UitbreidenAI/drug-exp-api.git ozempic-data" in text


def _write_comments(data_dir, n):
    comments = data_dir / "curated" / "comments" / "subreddit=Ozempic"
    comments.mkdir(parents=True, exist_ok=True)
    (comments / "date=2024-01-01.jsonl").write_text('{"id": "a"}\n' * n)


def _write_checkpoint(data_dir, day):
    (data_dir / "state").mkdir(exist_ok=True)
    (data_dir / "state" / "checkpoint.json").write_text(json.dumps({"comments/Ozempic": day}))


def test_latest_run_shows_what_each_run_added(tmp_path):
    t1 = datetime(2026, 11, 17, 6, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 11, 18, 6, 0, tzinfo=timezone.utc)

    _write_comments(tmp_path, 3)
    _write_checkpoint(tmp_path, "2024-01-02")
    record_run(tmp_path, t1)
    assert "No earlier run recorded yet" in render(tmp_path, t1)

    _write_comments(tmp_path, 10)
    _write_checkpoint(tmp_path, "2024-02-01")
    record_run(tmp_path, t2)
    text = render(tmp_path, t2)

    assert "The run at 2026-11-18 06:00 UTC added **+7 comments**" in text
    assert "moved from 2024-01-02 to 2024-02-01" in text
    assert "| 2026-11-18 06:00 | +7 | +0 | +0 | 10 | 0 | 2024-02-01 |" in text


def test_unchanged_run_is_not_recorded_again(tmp_path):
    _write_comments(tmp_path, 3)
    _write_checkpoint(tmp_path, "2024-01-02")
    record_run(tmp_path, datetime(2026, 11, 17, tzinfo=timezone.utc))
    record_run(tmp_path, datetime(2026, 11, 18, tzinfo=timezone.utc))
    assert len(read_history(tmp_path)) == 1


def test_first_run_uses_old_readme_as_baseline(tmp_path):
    (tmp_path / "README.md").write_text(
        "Last update: 2026-11-16 21:10 UTC.\nOldest stream continues from 2024-01-02._\n\n"
        "| comments | 1 |\n| posts | 0 |\n| Ozempic export | 0 of 100,000 |\n"
    )
    _write_comments(tmp_path, 4)
    _write_checkpoint(tmp_path, "2024-01-05")
    now = datetime(2026, 11, 18, tzinfo=timezone.utc)
    record_run(tmp_path, now)
    text = render(tmp_path, now)
    assert "added **+3 comments**" in text
    assert "| 2026-11-16 21:10 |" not in text  # baseline is the start, not a run row
