from modules.articles_split import ArticleSplitter


if __name__ == "__main__":
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

