from haystack.nodes import PreProcessor, DensePassageRetriever #to handle text splitting and the semantic search
from haystack.document_stores import FAISSDocumentStore # to manage and store the embeddings
from articles_split import ArticlesSplit # imported to split the articles into smaller chunks
from dotenv import load_dotenv
import json # imported to handle the JSON file with the articles
import sqlite3 # imported to manage the simple SQLite database
import logging
import os
logging.basicConfig(level=logging.INFO)

load_dotenv()  # This will read the .env file and set the environment variables accordingly.

class VectorDB:
    """
    VectorDB is a class that manages a vector-based document store using SQLite for
    storing articles and FAISS for managing embeddings.
    """
    def __init__(self,
                 db_path: str = os.getenv("DB_PATH", "data\\sqlite.db"), # it looks for the environment variable DB_PATH, if not found it uses the default value
                 faiss_path: str = os.getenv("FAISS_PATH", "sqlite:///document_store.db"),
                 split_length: int = int(os.getenv("SPLIT_LENGTH", 200)),
                 split_overlap: int = int(os.getenv("SPLIT_OVERLAP", 20)),
                 law_name: str = os.getenv("LAW_NAME", "Example Legal Code"),
                 document_store = None):
        
        """
        Initialize the VectorDB instance with database paths.

        Args:
            db_path (str): Path to the SQLite database file.
            faiss_path (str): SQL URL for the FAISS document store.
             document_store (FAISSDocumentStore, optional): An existing FAISS document store.
        """
        
        self.db_path = db_path # location for the sqlite database file
        self.faiss_path = faiss_path # connection string for the FAISS document store
        self.split_length = split_length
        self.split_overlap = split_overlap
        self.law_name = law_name
        self.document_store = document_store # Optionally an existing FAISS document store
        self.preprocessor = None 
        self.retriever = None

    def initialize_sqlite(self):

        """
        Connect to SQLite, and create the articles table if it does not exist.
        """

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_number INTEGER,
                        text TEXT
                    )
                """)
                conn.commit()  # Explicit commit if needed
        except sqlite3.Error as e:
            # Handle or log the error as needed
            print(f"SQLite error: {e}")


    def initialize_document_store(self):

        """
        Initialize the FAISS DocumentStore that will be used for storing document embeddings.
        """
        if self.document_store is None:
            self.document_store = FAISSDocumentStore(
                sql_url=self.faiss_path,  
                
                # SQLite path to store the documents, note:  the FAISSDocumentStore
                # also uses an SQLite database to store the documents and their metadata
            
                faiss_index_factory_str="Flat", # use a flat (brute-force) index, better results but less efficiency
                return_embedding=True
            )
        else:
            logging.info("Document store already initialized.") 
    def initialize_preprocessor(self):
        """
        Initialize the text preprocessor to split articles into chunks (around 200 tokens each).
        """
        self.preprocessor = PreProcessor(
            split_by="token",
            split_length=self.split_length,  # Each chunk is ~200 tokens
            split_overlap=self.split_overlap,  # Keep 20 tokens overlapping for context retention
            clean_whitespace=True
        )
    def populate_sqlite_from_json(self, json_file_path: str):
        """
        Read articles from a JSON file and insert them into the SQLite database.
        
        Args:
            json_file_path (str): Path to the JSON file containing articles.
        """
        try:
            # Open and load the JSON file
            with open(json_file_path, "r", encoding="utf-8") as f:
                articles = json.load(f)
            
            # Connect to SQLite and insert articles
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for article in articles:
                    cursor.execute(
                        "INSERT INTO articles (article_number, text) VALUES (?, ?)",
                        (article.get("article_number"), article.get("text"))
                    )
                conn.commit()
            print("Articles have been successfully inserted into the SQLite database.")
        except Exception as e:
            print(f"An error occurred while populating the SQLite DB: {e}")
      
      
    def preprocess_articles(self, json_file_path: str):
        """
        Preprocess the articles by reading from a JSON file and splitting them into smaller text chunks using the preprocessor.

        The JSON file should contain a list of dictionaries, each with keys "article_number" and "text".

        Args:
            json_file_path (str): Path to the JSON file with the articles.
        
        Returns:
            list: List of processed document chunks with metadata.
        """
        try:
            # Open and load the JSON file containing the articles
            with open(json_file_path, "r", encoding="utf-8") as file:
                articles = json.load(file)
        except Exception as e:
            raise Exception(f"Error reading JSON file: {e}")

        split_documents = []
        for article in articles:
            # Process each article by splitting the text into chunks
            chunks = self.preprocessor.process([{
                "content": article["text"],
                "meta": {"article_number": article["article_number"], "law_name": self.law_name}
            }])
            # Add chunk numbering to metadata and append each chunk to the list
            for i, chunk in enumerate(chunks):
                chunk.meta["chunk_number"] = i + 1  # Starts numbering at 1
                split_documents.append(chunk)
        return split_documents

    def write_documents(self, documents):
        
        """
        Write the processed document chunks to the document store.

        Args:
            documents (list): List of document chunks to write.
        """

        self.document_store.write_documents(documents)

    def initialize_retriever(self):
        
        """
        Initialize the Dense Passage Retriever used for querying the document store.
        """

        self.retriever = DensePassageRetriever(
            document_store=self.document_store,
            query_embedding_model="facebook/dpr-question_encoder-single-nq-base",
            passage_embedding_model="facebook/dpr-ctx_encoder-single-nq-base",
            use_gpu=False  # Set to True if you have a GPU
        )

    def update_embeddings(self):
        
        """
        Update the document store with embeddings computed by the retriever.
        """

        self.document_store.update_embeddings(self.retriever)
    

    def save_document_store(self, path):
        """
        Save the FAISS document store to a file.

        Args:
            path (str): Path to save the FAISS document store.
        """
        self.document_store.save(path)


    def setup(self):
        self.initialize_sqlite()
        self.initialize_document_store()
        self.initialize_preprocessor()

    def process_articles(self, articles):
        processed_docs = self.preprocess_articles(articles)
        self.write_documents(processed_docs)
        return processed_docs

    def build_retriever_and_index(self, db_path =  None ):
        """
        Build the retriever and index for the document store. 

        """
        self.initialize_retriever()
        self.update_embeddings()
        self.save_document_store(db_path)

    def vectorize(self, articles, db_path = None):
        self.setup()
        self.process_articles(articles)
        self.build_retriever_and_index(db_path)

        

    def query_legal_code(self, query, top_k= 10):

        """
        Retrieve document chunks relevant to the input query.

        Args:
            query (str): The query string.
            top_k (int): The number of top results to return.
        
        Returns:
            list: A list of dictionaries with the chunk content and associated metadata.
        """

        results = self.retriever.retrieve(query=query, top_k=top_k)  # top_k is how many chunks you want back

        response = []
        for doc in results:
            response.append({
                "chunk_content": doc.content,   # The text chunk
                "metadata": doc.meta            # Contains article_number, chunk_number, etc.
            })
        return response


articles = [
        {"article_number": 1, "text": "This is the text of article 1."},
        {"article_number": 2, "text": "This is the text of article 2."},
    ]
