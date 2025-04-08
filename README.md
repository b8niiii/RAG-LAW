To add Poppler to your PATH on Windows, follow these steps:
download it from https://github.com/oschwartz10612/poppler-windows/releases 
1. **Locate the Bin Folder:**  
   After extracting Release-24.08.0-0.zip, find the directory where it's extracted. Inside, locate the `bin` folder (e.g., `C:\poppler-24.08.0\bin`).

2. **Open Environment Variables:**
   - Press the **Windows key** and type "Environment Variables."
   - Click on **"Edit the system environment variables."**
   - In the System Properties window that opens, click on the **"Environment Variables..."** button.

3. **Edit the PATH Variable:**
   - In the Environment Variables window, under **User variables** (or **System variables** if you want the change to be system-wide), select the variable named **PATH** and click **"Edit..."**.
   - Click **"New"** and enter the full path to the `bin` folder (e.g., `C:\poppler-24.08.0\bin`).
   - Click **OK** to close each window.

4. **Restart Your Terminal:**  
   Close and reopen your terminal or command prompt to ensure the new PATH is loaded.

Once added, your Python scripts using pdf2image should be able to locate Poppler automatically. If you prefer not to modify your PATH, you can also specify the `poppler_path` parameter in your code:

```python
pages = convert_from_path(pdf_path, poppler_path=r"C:\poppler-24.08.0\bin")
```

This ensures that pdf2image knows exactly where to find Poppler without relying on the system PATH.

Document Store (FAISSDocumentStore instance):
This object encapsulates the FAISS index functionality, meaning it creates and manages the vector index (the “FAISS index”) that holds the document embeddings for fast similarity searches. It provides a unified interface to query against these embeddings.

faiss_path (or sql_url):
This attribute specifies the connection URL for the SQL database (typically SQLite) that the FAISSDocumentStore uses to store the document texts and metadata (but not the embeddings themselves). The SQL database keeps track of the document details and other metadata needed for your application.

