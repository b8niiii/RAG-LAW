from haystack.nodes import PreProcessor, DensePassageRetriever
from haystack.document_stores import FAISSDocumentStore
import sqlite3

class VectorDB:
    def __init__(self, db_path="my_database.db", faiss_path="sqlite:///document_store.db"):
        self.db_path = db_path
        self.faiss_path = faiss_path
        self.document_store = None
        self.preprocessor = None
        self.retriever = None

    def initialize_sqlite(self):
        # Connect to SQLite (creates the file if it doesn't exist)
        conn = sqlite3.connect(self.db_path)

        # Create a cursor object to execute SQL commands
        cursor = conn.cursor()

        # Create a table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_number INTEGER,
            text TEXT
        )
        """)

        # Commit changes and close connection
        conn.commit()
        conn.close()

    def initialize_document_store(self):
        # Initialize FAISS DocumentStore (is the one that will store the embeddings)
        self.document_store = FAISSDocumentStore(
            sql_url=self.faiss_path,  # SQLite path to store the documents
            faiss_index_factory_str="Flat",
            return_embedding=True
        )

    def initialize_preprocessor(self):
        # Initialize text preprocessor (splitting into ~200-token chunks)
        self.preprocessor = PreProcessor(
            split_by="token",
            split_length=200,  # Each chunk is ~200 tokens
            split_overlap=20,  # Keep 20 tokens overlapping for context retention
            clean_whitespace=True
        )

    def preprocess_articles(self, articles): # List of articles
        split_documents = []
        for article in articles: # Each article is a dictionary with keys "article_number" and "text"
            chunks = self.preprocessor.process([{
                "content": article["text"],
                "meta": {"article_number": article["article_number"], "law_name": "Example Legal Code"}
            }])
            # Add chunk numbers to metadata
            for i, chunk in enumerate(chunks):
                chunk.meta["chunk_number"] = i + 1
                split_documents.append(chunk)
        return split_documents

    def write_documents(self, documents):
        # Write documents to the document store
        self.document_store.write_documents(documents)

    def initialize_retriever(self):
        # Initialize retriever
        self.retriever = DensePassageRetriever(
            document_store=self.document_store,
            query_embedding_model="facebook/dpr-question_encoder-single-nq-base",
            passage_embedding_model="facebook/dpr-ctx_encoder-single-nq-base",
            use_gpu=False  # Set to True if you have a GPU
        )

    def update_embeddings(self):
        # Update document store with embeddings
        self.document_store.update_embeddings(self.retriever)


