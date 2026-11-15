"""Turn a PDF with numbered Italian articles into the JSON corpus format."""

import argparse
import json
from pathlib import Path

from modules.articles_split import ArticleSplitter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Path to a PDF you have permission to process")
    parser.add_argument("--output", type=Path, default=Path("data/articles.json"))
    args = parser.parse_args()

    if not args.pdf.is_file():
        parser.error(f"PDF not found: {args.pdf}")
    splitter = ArticleSplitter()
    text = splitter.extract_text_from_pdf(str(args.pdf))
    articles = [article for article in splitter.split_articles(text) if article["text"]]
    if not articles:
        parser.error("No numbered articles found. Check the PDF layout and OCR output.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(articles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(articles)} articles to {args.output}")


if __name__ == "__main__":
    main()
