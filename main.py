"""Run a semantic search from a terminal with a local corpus."""

import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from modules.vector_db import DEMO_CORPUS, VectorDB


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=3, choices=range(1, 21))
    parser.add_argument("--corpus", type=Path, default=DEMO_CORPUS)
    args = parser.parse_args()
    if not args.query.strip():
        parser.error("Provide a non-empty query.")

    with TemporaryDirectory(prefix="rag-law-") as directory:
        index = VectorDB(
            args.corpus,
            Path(directory) / "articles.sqlite3",
            os.environ.get("RAGLAW_MODEL_PATH"),
        )
        for result in index.query_legal_code(args.query, args.top_k):
            print(f"Article {result['article_number']}")
            print(result["full_article"])
            print()


if __name__ == "__main__":
    main()
