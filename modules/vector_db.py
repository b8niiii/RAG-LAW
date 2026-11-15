"""Build and query an immutable FAISS and SQLite index."""

from contextlib import closing
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

import faiss

from modules.encoder import MODEL_ID, MODEL_REVISION, MiniLMEncoder


DEMO_CORPUS = Path(__file__).resolve().parents[1] / "examples" / "italian_demo.json"
INDEX_VERSION = 1


def read_corpus(path: Path) -> tuple[dict, list[tuple]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as file:
        payload = json.load(file)
    source = {"name": "Imported articles", "kind": "custom"}
    if path.resolve() == DEMO_CORPUS:
        source = {"name": "Italian demo corpus", "kind": "demo"}
    if isinstance(payload, dict):
        source = {"name": source["name"], "kind": source["kind"], **payload["source"]}
        payload = payload["articles"]
    if not isinstance(payload, list) or not payload:
        raise ValueError("The corpus must hold a non-empty JSON list of articles.")

    rows = []
    for article in payload:
        if not isinstance(article, dict):
            raise ValueError("Every article must be a JSON object.")
        number = article.get("article_number")
        text = article.get("text")
        title = article.get("title")
        if type(number) not in (int, str) or not str(number).strip():
            raise ValueError("Every article needs an article_number.")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Article {number} has no text.")
        if title is not None and not isinstance(title, str):
            raise ValueError(f"Article {number} has an invalid title.")
        rows.append((number, title, text.strip()))
    return source, rows


def build_index(corpus_path: Path, destination: Path, model: MiniLMEncoder) -> None:
    """Write a complete index to a new directory, then make it visible."""
    if destination.exists():
        raise FileExistsError(f"Index destination already exists: {destination}")
    source, articles = read_corpus(corpus_path)
    passages = [
        (article_id, excerpt)
        for article_id, (_, _, body) in enumerate(articles, start=1)
        for excerpt in model.passages(body)
    ]
    if not passages:
        raise ValueError("The corpus contains no encodable passages.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    vectors = model.encode([excerpt for _, excerpt in passages])
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    manifest = {
        "format": INDEX_VERSION,
        "model": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "weights": model.weights,
        "articles": len(articles),
        "passages": len(passages),
        "dimensions": index.d,
        "corpus_sha256": hashlib.sha256(corpus_path.read_bytes()).hexdigest(),
        "corpus": source,
    }

    with TemporaryDirectory(prefix=".index-", dir=destination.parent) as temporary:
        staged = Path(temporary) / "index"
        staged.mkdir()
        faiss.write_index(index, str(staged / "passages.faiss"))
        with closing(sqlite3.connect(staged / "articles.sqlite3")) as db, db:
            db.executescript("""
                CREATE TABLE articles (id INTEGER PRIMARY KEY, number, title TEXT, body TEXT);
                CREATE TABLE passages (id INTEGER PRIMARY KEY, article_id REFERENCES articles(id), text TEXT);
            """)
            db.executemany("INSERT INTO articles (number, title, body) VALUES (?, ?, ?)", articles)
            db.executemany(
                "INSERT INTO passages (id, article_id, text) VALUES (?, ?, ?)",
                ((index_id, article_id, text) for index_id, (article_id, text) in enumerate(passages)),
            )
        (staged / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        staged.rename(destination)


class VectorDB:
    """Load a prepared FAISS index and look up matching articles from SQLite."""

    def __init__(self, directory: Path, model: MiniLMEncoder):
        self.model = model
        self.manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        identity = (INDEX_VERSION, MODEL_ID, MODEL_REVISION, model.weights)
        expected = tuple(self.manifest[field] for field in ("format", "model", "model_revision", "weights"))
        if identity != expected:
            raise ValueError("Rebuild the index for this RAG-LAW release and CPU architecture.")
        self.index = faiss.read_index(str(directory / "passages.faiss"))
        self.sqlite_uri = f"{(directory / 'articles.sqlite3').resolve().as_uri()}?mode=ro&immutable=1"
        with closing(sqlite3.connect(self.sqlite_uri, uri=True)) as db:
            database_articles = db.execute("SELECT count(*) FROM articles").fetchone()[0]
            database_passages = db.execute("SELECT count(*) FROM passages").fetchone()[0]
        if (
            self.index.d != self.manifest["dimensions"]
            or self.index.ntotal != self.manifest["passages"]
            or self.index.ntotal != database_passages
            or self.manifest["articles"] != database_articles
        ):
            raise ValueError("SQLite, FAISS and manifest disagree. Rebuild the index.")

    def query_legal_code(self, query: str, top_k: int = 5) -> list[dict]:
        vector = self.model.encode([query])
        _, indices = self.index.search(vector, min(top_k, self.index.ntotal))
        with closing(sqlite3.connect(self.sqlite_uri, uri=True)) as db:
            results = []
            for index_id in indices[0]:
                row = db.execute("""
                    SELECT a.number, a.title, p.text, a.body FROM passages p
                    JOIN articles a ON p.article_id = a.id WHERE p.id = ?
                """, (int(index_id),)).fetchone()
                results.append(dict(zip(("article_number", "title", "chunk_content", "full_article"), row)))
        return results
