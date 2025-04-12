# Import FastAPI for creating the API application
from fastapi import FastAPI

# Import BaseModel from Pydantic to define data schemas for request validation
from pydantic import BaseModel

# Import the custom VectorDB module for handling vector-based operations and queries
from modules.vector_db import VectorDB

# Import the FAISSDocumentStore to work with a FAISS-based document store for efficient vector searches
from haystack.document_stores import FAISSDocumentStore

# ---------------------------------------------------------------------------------
# Initialize the FastAPI application instance.
# ---------------------------------------------------------------------------------
app = FastAPI(
    title = "Legal Code Search",  # Title of the API for documentation purposes.
    description = "API for searching legal articles using semantic search.",  # Description of the API.
    version = "0.1.0",  # Version of the API.
)

# ---------------------------------------------------------------------------------
# Load the FAISS document store once at startup.
# This loads the pre-built vector index stored in the file "data/vector_db.faiss".
# ---------------------------------------------------------------------------------
document_store = FAISSDocumentStore.load("data/vector_db.faiss")

# ---------------------------------------------------------------------------------
# Initialize the VectorDB instance with specific paths:
# - sql_path: Points to the SQLite database used for additional data persistence.
# - faiss_path: Points to the FAISS document store, SQLite db that stores metadata and textual content of embeddings.
# - document_store: The FAISS document store loaded above.
#
# This setup allows VectorDB to manage both the SQLite database and the FAISS vector store.
# ---------------------------------------------------------------------------------
vector_db = VectorDB(
    sql_path="data/sqlite.db",                       # Path to the SQLite database.
    faiss_path="sqlite:///data/document_store.db",    # Connection string to the FAISS document store.
    document_store=document_store                   # Loaded FAISS document store.
)

# ---------------------------------------------------------------------------------
# Initialize the retriever component once at startup.
# This prepares the VectorDB to efficiently process semantic search queries.
# ---------------------------------------------------------------------------------
vector_db.initialize_retriever()

# ---------------------------------------------------------------------------------
# Define a data model for the incoming request using Pydantic.
# The QueryRequest model ensures that every POST to /search has a 'query' string and an optional 'top_k' integer.
# ---------------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str         # The search query to look up legal articles.
    top_k: int = 5     # The number of top results to return; defaults to 5 if not provided.

# ---------------------------------------------------------------------------------
# Define a root endpoint to test API availability.
# A GET request to the "/" endpoint returns a simple status message.
# ---------------------------------------------------------------------------------
@app.get("/")
def read_root(text: str = ""):
    if not text:
        return f"Try to append ?text=something in the URL!"
    else:
        return text
# ---------------------------------------------------------------------------------
# Define the semantic search endpoint for processing POST requests.
# This endpoint receives a JSON payload matching QueryRequest, performs a semantic search,
# and returns the search results along with additional article information.
# ---------------------------------------------------------------------------------
@app.post("/search")
def search_legal_articles(request: QueryRequest):
    # Use the VectorDB instance to query the legal code with the provided query and top_k value.
    results = vector_db.query_legal_code(request.query, request.top_k)
    
    # Initialize an empty list to store the formatted results.
    response = []

    # Iterate over each result returned by the semantic search.
    for res in results:
        # Extract the article number from the result metadata.
        article_num = res["metadata"]["article_number"]
        
        # Fetch the full article text from the SQLite database based on the article number.
        full_text = vector_db.fetch_article_by_number(vector_db.sql_path, article_num)
        
        # Append a dictionary containing the article number, chunk of content from the search,
        # and the full article text to the response list.
        response.append({
            "article_number": article_num,
            "chunk_content": res["chunk_content"],
            "full_article": full_text
        })

    # Return a JSON object that includes the original query and the list of search results.
    return {
        "query": request.query,
        "results": response
    }
