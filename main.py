"""Minimal semantic-search example for an existing RAG-LAW index."""

from haystack.document_stores import FAISSDocumentStore

from modules.vector_db import VectorDB


def main() -> None:
    document_store = FAISSDocumentStore.load("data/vector_db.faiss")
    vector_db = VectorDB(
        sql_path="data/sqlite.db",
        faiss_path="sqlite:///data/document_store.db",
        document_store=document_store,
    )
    vector_db.initialize_retriever()

    query = input("Enter a legal query: ")
    for result in vector_db.query_legal_code(query=query, top_k=5):
        article_number = result["metadata"].get("article_number")
        print(f"Article {article_number}: {result['chunk_content']}\n")


if __name__ == "__main__":
    main()
