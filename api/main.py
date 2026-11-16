"""Serve semantic retrieval through FastAPI."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field, StringConstraints

from modules.encoder import MiniLMEncoder
from modules.vector_db import DEMO_CORPUS, VectorDB, build_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    corpus_path = os.environ.get("RAGLAW_CORPUS_PATH")
    index_path = os.environ.get("RAGLAW_INDEX_PATH")
    model = MiniLMEncoder(os.environ.get("RAGLAW_MODEL_PATH"))
    with TemporaryDirectory(prefix="rag-law-") as directory:
        if corpus_path or not index_path:
            index = Path(directory) / "index"
            build_index(Path(corpus_path) if corpus_path else DEMO_CORPUS, index, model)
        else:
            index = Path(index_path)
        app.state.index = VectorDB(index, model)
        yield


app = FastAPI(
    title="RAG-LAW",
    description="Semantic search over Italian legal articles.",
    version="0.2.0",
    lifespan=lifespan,
)


class QueryRequest(BaseModel):
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    article_number: str | int
    title: str | None
    chunk_content: str
    full_article: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    corpus: dict


@app.get("/")
def read_root(text: str = ""):
    if text:
        return text
    return {"service": "RAG-LAW", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health(request: Request):
    manifest = request.app.state.index.manifest
    return {
        "status": "ready",
        "articles": manifest["articles"],
        "passages": manifest["passages"],
        "demo_corpus": manifest["corpus"]["kind"] == "demo",
        "corpus": manifest["corpus"],
    }


@app.post("/search", response_model=SearchResponse)
def search_legal_articles(body: QueryRequest, request: Request):
    return {
        "query": body.query,
        "results": request.app.state.index.query_legal_code(body.query, body.top_k),
        "corpus": request.app.state.index.manifest["corpus"],
    }
