"""Query a running RAG-LAW API."""

import argparse
import json
import os

import requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5, choices=range(1, 21))
    parser.add_argument("--api-url", default=os.getenv("RAGLAW_API_URL", "http://127.0.0.1:8000"))
    args = parser.parse_args()
    try:
        response = requests.post(
            f"{args.api_url.rstrip('/')}/search",
            json={"query": args.query, "top_k": args.top_k},
            timeout=(3, 30),
        )
        response.raise_for_status()
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    except requests.exceptions.RequestException as error:
        parser.exit(1, f"Search failed: {error}\n")


if __name__ == "__main__":
    main()
