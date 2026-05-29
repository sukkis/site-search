import hashlib
import json
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from site_search.chunker import chunk_text


def index_cache(cache_dir: Path, chroma_dir: Path, model_name: str) -> None:
    records = _load_records(cache_dir)
    all_rows = [row for record in records for row in _make_chunk_rows(record)]
    if not all_rows:
        return
    chunks = [row["chunk"] for row in all_rows]
    embeddings = _embed(chunks, model_name)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection("articles")
    _upsert(collection, all_rows, embeddings)


def _load_records(cache_dir: Path) -> list[dict[str, Any]]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(cache_dir.glob("*.json"))
    ]


def _make_chunk_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    text = record.get("text")
    if not text:
        return []
    chunks = chunk_text(text)
    url = record.get("url", "")
    metadata = {
        "url": url,
        "title": record.get("title") or "",
        "author": record.get("author") or "",
        "date_published": record.get("date_published") or "",
    }
    return [
        {
            "id": hashlib.sha256(f"{url}::{i}".encode()).hexdigest(),
            "chunk": chunk,
            "metadata": metadata,
        }
        for i, chunk in enumerate(chunks)
    ]


def _embed(chunks: list[str], model_name: str) -> list[list[float]]:
    model = SentenceTransformer(model_name)
    vectors = model.encode(chunks, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def _upsert(
    collection: Any,
    rows: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> None:
    all_ids = [row["id"] for row in rows]
    existing = set(collection.get(ids=all_ids)["ids"])
    new = [
        (row, emb) for row, emb in zip(rows, embeddings) if row["id"] not in existing
    ]
    if not new:
        return
    new_rows, new_embeddings = zip(*new)
    collection.add(
        ids=[row["id"] for row in new_rows],
        embeddings=list(new_embeddings),
        documents=[row["chunk"] for row in new_rows],
        metadatas=[row["metadata"] for row in new_rows],
    )
