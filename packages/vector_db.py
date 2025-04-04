from haystack.nodes import PreProcessor, DensePassageRetriever
from haystack.document_stores import FAISSDocumentStore
import sqlite3

class VectorDB:
    """
    VectorDB is a class that manages a vector-based document store using SQLite for
    storing articles and FAISS for managing embeddings.
    """
    def __init__(self, db_path="my_database.db", faiss_path="sqlite:///document_store.db", document_store = None):
        
        """
        Initialize the VectorDB instance with database paths.

        Args:
            db_path (str): Path to the SQLite database file.
            faiss_path (str): SQL URL for the FAISS document store.
             document_store (FAISSDocumentStore, optional): An existing FAISS document store.
        """
        
        self.db_path = db_path
        self.faiss_path = faiss_path
        self.document_store = document_store
        self.preprocessor = None
        self.retriever = None

    def initialize_sqlite(self):

        """
        Connect to SQLite, and create the articles table if it does not exist.
        """

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

        """
        Initialize the FAISS DocumentStore that will be used for storing document embeddings.
        """

        self.document_store = FAISSDocumentStore(
            sql_url=self.faiss_path,  # SQLite path to store the documents
            faiss_index_factory_str="Flat",
            return_embedding=True
        )

    def initialize_preprocessor(self):
        """
        Initialize the text preprocessor to split articles into chunks (around 200 tokens each).
        """
        self.preprocessor = PreProcessor(
            split_by="token",
            split_length=200,  # Each chunk is ~200 tokens
            split_overlap=20,  # Keep 20 tokens overlapping for context retention
            clean_whitespace=True
        )
      
    def split_articles(self, code):

        """
        Process or split the raw articles if needed. 
        
        Currently, this is a placeholder that returns the articles unchanged.

        Args:
            articles (list): List of article dictionaries, each with keys "article_number" and "text".
        
        Returns:
            list: Processed articles.
        """

        splitted_art = code
        return splitted_art #returns a list 
      
    def preprocess_articles(self, splitted_art): # Splitted_art is a list of articles
        
        """
        Preprocess the articles by splitting them into smaller text chunks using the preprocessor.

        Args:
            splitted_art (list): List of article dictionaries with "article_number" and "text".
        
        Returns:
            list: List of processed document chunks with metadata.
        """
        
        split_documents = []
        for article in splitted_art: # Each article is a dictionary with keys "article_number" and "text"
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

    def query_legal_code(self, query, top_k=5):

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
    

    def save_document_store(self, path):
        """
        Save the FAISS document store to a file.

        Args:
            path (str): Path to save the FAISS document store.
        """
        self.document_store.save(path)


    def vectorize(self, articles):

        """
        Run the full pipeline: initialize components, preprocess articles, write to the document store,
        initialize the retriever, and update the embeddings.

        Args:
            articles (list): List of articles (each as a dict with keys "article_number" and "text").
        """

        self.initialize_sqlite()
        self.initialize_document_store()
        self.initialize_preprocessor()
        splitted_art = self.split_articles(articles)
        preprocessed_articles = self.preprocess_articles(splitted_art)
        self.write_documents(preprocessed_articles)
        self.initialize_retriever()
        self.update_embeddings()
        self.save_document_store("document_store.db")
articles = [
        {"article_number": 1, "text": "This is the text of article 1."},
        {"article_number": 2, "text": "This is the text of article 2."},
    ]
    
