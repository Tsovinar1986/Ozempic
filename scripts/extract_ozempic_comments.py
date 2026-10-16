"""Export up to 100,000 curated comments mentioning Ozempic to CSV."""

import argparse
import os
from pathlib import Path

import duckdb
import fsspec


def positive_int(value):
    limit = int(value)
    if limit < 1:
        raise argparse.ArgumentTypeError("limit must be a positive integer")
    return limit


def _pick_format(files, input_dir):
    """Prefer Parquet partitions; fall back to non-empty JSON Lines partitions."""
    for ext in (".parquet", ".jsonl"):
        matched = [file for file in files if file.endswith(ext)]
        if matched:
            return matched, ext
    raise FileNotFoundError(f"No Parquet or JSONL files found under: {input_dir}")


def _curated_files(input_dir):
    if input_dir.startswith("s3://"):
        fs, path = fsspec.core.url_to_fs(input_dir)
        files, ext = _pick_format(sorted(fs.find(path)), input_dir)
        return [fs.unstrip_protocol(file) for file in files], ext, True

    directory = Path(input_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"Curated comments directory not found: {directory}")
    # Days without comments produce empty .jsonl files, which DuckDB cannot read.
    files = sorted(
        str(path) for path in directory.rglob("*")
        if path.is_file() and (path.suffix == ".parquet" or path.stat().st_size > 0)
    )
    files, ext = _pick_format(files, directory)
    return files, ext, False


def extract_ozempic_comments(input_dir, output_file, limit=100_000):
    files, ext, is_s3 = _curated_files(str(input_dir))

    with duckdb.connect() as connection:
        if is_s3:
            region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
            if not region:
                raise RuntimeError("Set AWS_REGION to read curated Parquet files from S3")
            connection.execute("INSTALL httpfs")
            connection.execute("LOAD httpfs")
            connection.execute(
                "CREATE SECRET (TYPE S3, PROVIDER CREDENTIAL_CHAIN, "
                f"REGION '{region}')"
            )
        if ext == ".parquet":
            comments = connection.read_parquet(files)
        else:
            comments = connection.read_json(files, format="newline_delimited")
        connection.register("comments", comments)
        df = connection.execute(
            """
            SELECT comment_id, subreddit, author, body, score, created_at, permalink
            FROM (
                SELECT
                    id AS comment_id,
                    subreddit,
                    author,
                    body,
                    score,
                    created_at,
                    created_utc,
                    permalink
                FROM comments
                WHERE LOWER(COALESCE(body, '')) LIKE '%ozempic%'
                ORDER BY created_utc DESC, subreddit, id DESC
                LIMIT ?
            )
            ORDER BY created_utc, subreddit, comment_id
            """,
            [limit],
        ).df()

    with fsspec.open(output_file, "wt", encoding="utf-8-sig", auto_mkdir=True) as output:
        df.to_csv(output, index=False)
    return len(df)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="data/curated/comments",
        help="local directory or s3:// URI containing curated comment Parquet or JSONL partitions",
    )
    parser.add_argument(
        "--output",
        default="ozempic_100k_comments.csv",
        help="local CSV path or s3:// URI for the CSV export",
    )
    parser.add_argument(
        "--limit",
        type=positive_int,
        default=100_000,
        help="maximum matching comments to export (default: 100000)",
    )
    args = parser.parse_args()

    count = extract_ozempic_comments(args.input, args.output, args.limit)
    print(f"Exported {count} comments to {args.output}")


if __name__ == "__main__":
    main()
