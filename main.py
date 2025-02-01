import os
import sqlite3
from haystack.document_stores import FAISSDocumentStore
from haystack.nodes import DensePassageRetriever
from packages.vector_db import VectorDB

civ_cod = VectorDB(db_path="my_database.db", faiss_path="sqlite:///document_store.db")
civ_cod.initialize_document_store()
civ_cod.initialize_retriever()

results = civ_cod.query_legal_code(query="your search query", top_k=5)
print(results)
