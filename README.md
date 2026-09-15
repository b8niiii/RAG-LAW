# RAG-LAW

Semantic search over legal codes using dense embeddings, FAISS and SQLite.

This university project explores a retrieval pipeline for turning legal PDFs into structured articles, indexing their text and retrieving the most relevant provisions for a natural-language query. It is a search system, not a source of legal advice.

## What it does

1. Extracts text from a legal PDF.
2. Splits the document into numbered articles.
3. Stores complete articles and metadata in SQLite.
4. Chunks and embeds the articles with a multilingual sentence-transformer.
5. Builds a FAISS index for semantic retrieval.
6. Returns the full text of the highest-ranking articles.

## Architecture

```text
PDF
 └─> article extraction
      └─> JSON articles
           ├─> SQLite: full text and metadata
           └─> preprocessing and embeddings
                └─> FAISS semantic index
                     └─> natural-language query
```

The main implementation is in `modules/vector_db.py`. PDF and article parsing utilities are under `modules/`, runnable helpers under `scripts/`, and end-to-end examples under `test/`.

## Tech stack

- Python 3.9+
- Haystack 1.x
- FAISS
- Sentence Transformers
- SQLite
- PyPDF2, pdf2image and Tesseract for document processing
- Poetry for dependency management

## Setup

```bash
git clone https://github.com/b8niiii/RAG-LAW.git
cd RAG-LAW
poetry install
```

Some PDF workflows require external tools: [Poppler](https://poppler.freedesktop.org/) and [Tesseract OCR](https://github.com/tesseract-ocr/tesseract).

Do not commit copyrighted legal corpora or generated databases. Place local inputs under `codes/` and generated files under `data/`; both should remain environment-specific.

## Usage

Prepare a PDF path in `scripts/article_splitter.py`, then extract its articles:

```bash
poetry run python scripts/article_splitter.py --output articles.json
```

Build the SQLite/FAISS index and run a query:

```bash
poetry run python test/search_test_from_scratch.py
```

To reuse an existing index:

```bash
poetry run python test/search_test_w_given_dataset.py
```

The scripts currently serve as reproducible examples rather than a stable command-line API. Paths may need to be adapted to the local legal corpus.

## Repository structure

```text
.
├── main.py                  # minimal query example
├── modules/
│   ├── articles_split.py    # article extraction
│   ├── pdf_split.py         # PDF utilities
│   └── vector_db.py         # storage, embeddings and retrieval
├── scripts/
│   └── article_splitter.py
├── test/                    # end-to-end usage examples
├── pyproject.toml
└── poetry.lock
```

## Current status and limitations

This is an educational prototype.

- Retrieval quality has not yet been evaluated against a labelled benchmark.
- OCR quality depends on the source PDF and local Poppler/Tesseract installation.
- The code targets Haystack 1.x and uses a CPU FAISS index.
- The repository does not distribute a legal corpus or pre-built index.
- Retrieved passages must be verified against an authoritative legal source.

## Roadmap

- Add a small redistributable example corpus.
- Replace example scripts with a documented CLI.
- Add retrieval metrics such as Recall@k and MRR.
- Add automated tests and continuous integration.
- Upgrade or isolate the legacy Haystack dependency.

## License

Released under the MIT License.
