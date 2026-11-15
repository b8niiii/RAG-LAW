"""Build the SQLite and FAISS files once before serving a corpus."""

import argparse
import os
from pathlib import Path

from modules.encoder import MiniLMEncoder
from modules.vector_db import build_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"The output directory already exists: {args.output}")
    build_index(args.corpus, args.output, MiniLMEncoder(os.environ.get("RAGLAW_MODEL_PATH")))
    print(f"Prepared SQLite and FAISS in {args.output}")


if __name__ == "__main__":
    main()
