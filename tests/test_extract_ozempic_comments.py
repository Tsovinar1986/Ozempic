import pandas as pd

from scripts.extract_ozempic_comments import extract_ozempic_comments


def make_comment(comment_id, body, created_utc):
    return {
        "id": comment_id,
        "subreddit": "Ozempic",
        "author": "tester",
        "body": body,
        "score": 1,
        "created_at": "2026-10-01T00:00:00Z",
        "created_utc": created_utc,
        "permalink": f"https://reddit.com/{comment_id}",
    }


def test_extracts_latest_matching_comments_in_order_and_respects_limit(tmp_path):
    input_dir = tmp_path / "curated" / "comments" / "subreddit=Ozempic"
    input_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            make_comment("later", "I take OZEMPIC", 2),
            make_comment("unrelated", "No medication mentioned", 1),
            make_comment("earlier", "ozempic helped", 1),
            make_comment("removed", None, 3),
        ]
    ).to_parquet(input_dir / "comments.parquet", index=False)
    output_file = tmp_path / "exports" / "comments.csv"

    count = extract_ozempic_comments(input_dir.parent, output_file, limit=1)

    result = pd.read_csv(output_file)
    assert count == 1
    assert result["comment_id"].tolist() == ["later"]


def test_missing_parquet_directory_fails_explicitly(tmp_path):
    input_dir = tmp_path / "comments"
    input_dir.mkdir()

    try:
        extract_ozempic_comments(input_dir, tmp_path / "comments.csv")
    except FileNotFoundError as error:
        assert "No Parquet or JSONL files found" in str(error)
    else:
        raise AssertionError("Expected missing Parquet input to fail")


def test_reads_jsonl_partitions_and_skips_empty_days(tmp_path):
    input_dir = tmp_path / "curated" / "comments" / "subreddit=Ozempic"
    input_dir.mkdir(parents=True)
    pd.DataFrame(
        [make_comment("a", "Ozempic day one", 1), make_comment("b", "nothing", 2)]
    ).to_json(input_dir / "date=2026-10-01.jsonl", orient="records", lines=True)
    (input_dir / "date=2026-10-02.jsonl").write_text("")
    output_file = tmp_path / "comments.csv"

    count = extract_ozempic_comments(input_dir.parent, output_file)

    assert count == 1
    assert pd.read_csv(output_file)["comment_id"].tolist() == ["a"]
