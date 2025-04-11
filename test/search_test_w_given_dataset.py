from modules.vector_db import VectorDB  # Replace with the actual module name

vector_db = VectorDB(sql_path= "none", faiss_path= "sqlite///document_store.db") # For SQLite databases, the connection string should start with sqlite:/// for a relative file path 

# Initialize the FAISS document store (this will load your persisted FAISS index)
vector_db.initialize_document_store()

# Set up the retriever to enable semantic search queries
vector_db.initialize_retriever()

# Now you can perform searches with your saved index without re-indexing the articles
query = "What is the procedure for filing an appeal?"
results = vector_db.query_legal_code(query, top_k=10)

# Print or process the results
for result in results:
    print("Chunk Content:", result["chunk_content"])
    print("Metadata:", result["metadata"])
    print("-----")

# If needed, you can also fetch a full article from SQLite

full_article = vector_db.fetch_article_by_number(sql_path = "document_store.db", article_number=5)
if full_article:
    print("Full article text:", full_article)
else:
    print("Article not found.")
