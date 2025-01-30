from haystack.nodes import PreProcessor
from haystack.document_stores import FAISSDocumentStore


# Inizialize FAISS DocumentStore
document_store = FAISSDocumentStore(
    sql_url="sqlite:///document_store.db",
    faiss_index_factory_str="Flat",
    return_embedding=True
)

# Initialize text preprocessor (splitting into ~200-token chunks)
preprocessor = PreProcessor(
    split_by="token",
    split_length=200,  # Each chunk is ~200 tokens
    split_overlap=20,  # Keep 20 tokens overlapping for context retention
    clean_whitespace=True)

"""
Ali articles'code

"""
split_documents = []
for article in articles:
    chunks = preprocessor.process([{
        "content": article["text"],
        "meta": {"article_number": article["article_number"], "law_name": "Example Legal Code"}
    }])
    # Add chunk numbers to metadata
    for i, chunk in enumerate(chunks):
        chunk["meta"]["chunk_number"] = i + 1
        split_documents.append(chunk)

# Store in FAISS
document_store.write_documents(split_documents)