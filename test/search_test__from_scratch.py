from modules.vector_db import VectorDB  # Replace with the actual module name


# Create an instance of VectorDB
vector_db = VectorDB()

# Initialize and vectorize using your JSON file containing articles
json_file_path = "data/articles.json"  # Path to your JSON file
vector_db.vectorize(json_file_path, db_path="data/vector_db.faiss")

# Perform a semantic search
query = input("Enter your legal query: ")  # Prompt user for a query
results = vector_db.query_legal_code(query, top_k=10)


# Group chunks by article_number
articles_grouped = {}
for result in results:
    article_num = result["metadata"].get("article_number")
    # Avoid duplicates by storing each article only once.
    if article_num not in articles_grouped:
        articles_grouped[article_num] = vector_db.fetch_article_by_number(vector_db.sql_path, article_num)

# Print the complete article texts retrieved from SQLite
for article_num, full_text in articles_grouped.items():
    if full_text:
        print(f"Article {article_num}:")
        print(full_text)
        print("---")
    else:
        print(f"Article {article_num} not found in the database.")