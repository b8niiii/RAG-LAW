from modules.vector_db import VectorDB  # Replace with the actual module name

# Create an instance of VectorDB
vector_db = VectorDB()

# Initialize and vectorize using your JSON file containing articles
json_file_path = "data/articles.json"  # Path to your JSON file
vector_db.vectorize(json_file_path)

# Perform a semantic search
query = input("Enter your legal query: ")  # Prompt user for a query
results = vector_db.query_legal_code(query, top_k=10)

# Process and display results
for result in results:
    print("Chunk Content:", result["chunk_content"])
    print("Metadata:", result["metadata"])
    print("---")
