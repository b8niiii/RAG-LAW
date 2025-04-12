from modules.vector_db import VectorDB  # Replace with the actual module name
from haystack.document_stores import FAISSDocumentStore


document_store = FAISSDocumentStore.load("data\\vector_db.faiss")

print("11111111111111111111111111")
vector_db = VectorDB(sql_path= "data\\sqlite.db", faiss_path= "sqlite:///data/document_store.db", document_store = document_store) # For SQLite databases, the connection string should start with sqlite:/// for a relative file path 
print("2222222222222222222222222222")
# Initialize the FAISS document store (this will load your persisted FAISS index)
vector_db.initialize_document_store()
print("33333333333333333333333333")
# Set up the retriever to enable semantic search queries
vector_db.initialize_retriever()
print("44444444444444444444444444")
# Now you can perform searches with your saved index without re-indexing the articles
query = input("Enter your legal query: ")  # Prompt user for a query
results = vector_db.query_legal_code(query, top_k=10)
print("55555555555555555555555555")
# Collect the unique article numbers from the returned chunks.
unique_article_numbers = {result["metadata"].get("article_number") for result in results}

# Loop over each unique article number and fetch the full article text from SQLite.
for article_number in unique_article_numbers:
    # Use the db_path stored in vector_db (ensure this is the correct path to your SQLite file)
    full_article = vector_db.fetch_article_by_number(vector_db.sql_path, article_number)
    if full_article:
        print("Article Number:", article_number)
        print("Full Article Text:", full_article)
        print("-----")
    else:
        print(f"Article with number {article_number} not found.")