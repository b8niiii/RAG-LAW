"""Index passages with FAISS and keep complete articles in SQLite."""

from contextlib import closing
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3

import faiss

from modules.encoder import MiniLMEncoder


DEMO_CORPUS = Path(__file__).resolve().parents[1] / "examples" / "italian_demo.json"


@dataclass(frozen=True)
class Passage:
    article_id: int
    text: str


class VectorDB:
    """A read-only retrieval index built once per API process."""

    def __init__(
        self,
        corpus_path: Path,
        sqlite_path: Path,
        model_path: str | None = None,
    ):
        source = json.loads(corpus_path.read_text(encoding="utf-8"))
        if not isinstance(source, list) or not source:
            raise ValueError("The corpus must contain a non-empty JSON list of articles.")

        rows = []
        for article in source:
            if not isinstance(article, dict):
                raise ValueError("Every article must be a JSON object.")
            number = article.get("article_number")
            body = article.get("text")
            title = article.get("title")
            if type(number) not in (int, str) or not str(number).strip():
                raise ValueError("Every article needs an article_number.")
            if not isinstance(body, str) or not body.strip():
                raise ValueError(f"Article {number} has no text.")
            if title is not None and not isinstance(title, str):
                raise ValueError(f"Article {number} has an invalid title.")
            rows.append((number, title, body.strip()))

        self.model = MiniLMEncoder(model_path)
        self.passages = [
            Passage(article_id, excerpt)
            for article_id, (_, _, body) in enumerate(rows, start=1)
            for excerpt in self.model.passages(body)
        ]
        if not self.passages:
            raise ValueError("The corpus contains no passages the model can encode.")
        vectors = self.model.encode([passage.text for passage in self.passages])
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

        self.sqlite_uri = f"{sqlite_path.resolve().as_uri()}?mode=ro"
        with closing(sqlite3.connect(sqlite_path)) as connection, connection:
            connection.execute(
                "CREATE TABLE articles (id INTEGER PRIMARY KEY, number, title TEXT, body TEXT)"
            )
            connection.executemany(
                "INSERT INTO articles (number, title, body) VALUES (?, ?, ?)", rows
            )
        self.article_count = len(rows)

    def query_legal_code(self, query: str, top_k: int = 5) -> list[dict]:
        vector = self.model.encode([query])
        _, indices = self.index.search(vector, min(top_k, self.index.ntotal))

        results = []
        with closing(sqlite3.connect(self.sqlite_uri, uri=True)) as connection:
            for index in indices[0]:
                passage = self.passages[index]
                number, title, body = connection.execute(
                    "SELECT number, title, body FROM articles WHERE id = ?",
                    (passage.article_id,),
                ).fetchone()
                results.append({
                    "article_number": number,
                    "title": title,
                    "chunk_content": passage.text,
                    "full_article": body,
                })
        return results
