import json
import os
import argparse
from modules.articles_split import ArticleSplitter

# to give the output file a name run "poetry run python -m your_script.py --output custom_filename.json

def main():
    # Set up argument parsing to allow passing the output file name from the terminal
    parser = argparse.ArgumentParser(
        description="Extract articles from a PDF and save them to a JSON file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="articles.json",
        help="Name of the output JSON file (default: articles.json)"
    )
    args = parser.parse_args()

    try:
        splitter = ArticleSplitter()
        pdf_path = "codes\\cod_civ\\libri.pdf"
        
        print("Starting PDF processing...")
        raw_text = splitter.extract_text_from_pdf(pdf_path)
        
        print("Splitting text into articles...")
        articles = splitter.split_articles(raw_text)
        
        print(f"Found {len(articles)} articles")
        print("\nFirst 3 articles preview:")
        for article in articles[:3]:
            print(f"Article {article['article_number']}:")
            print(f"Preview: {article['text'][:200]}")
            print("-" * 40)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return

    # Ensure the "data" folder exists
    data_folder = "data"
    os.makedirs(data_folder, exist_ok=True)

    # Create the full output file path using the name provided via command line argument
    output_file = os.path.join(data_folder, args.output)

    # Write the articles to the JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"Articles have been saved to {output_file}")

if __name__ == "__main__":
    main()
