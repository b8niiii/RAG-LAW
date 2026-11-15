"""Serve semantic retrieval through FastAPI."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field, StringConstraints

from modules.vector_db import DEMO_CORPUS, VectorDB


@asynccontextmanager
async def lifespan(app: FastAPI):
    corpus = Path(os.environ.get("RAGLAW_CORPUS_PATH", DEMO_CORPUS)).resolve()
    model = os.environ.get("RAGLAW_MODEL_PATH")
    with TemporaryDirectory(prefix="rag-law-") as directory:
        app.state.index = VectorDB(corpus, Path(directory) / "articles.sqlite3", model)
        app.state.is_demo = corpus == DEMO_CORPUS
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


@app.get("/")
def read_root(text: str = ""):
    if text:
        return text
    return {"service": "RAG-LAW", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health(request: Request):
    index = request.app.state.index
    return {
        "status": "ready",
        "articles": index.article_count,
        "passages": index.index.ntotal,
        "demo_corpus": request.app.state.is_demo,
    }


@app.post("/search", response_model=SearchResponse)
def search_legal_articles(body: QueryRequest, request: Request):
    return {
        "query": body.query,
        "results": request.app.state.index.query_legal_code(body.query, body.top_k),
    }
