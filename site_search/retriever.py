from pathlib import Path
from typing import Any, cast

import chromadb
from sentence_transformers import SentenceTransformer


def _embed_query(query: str, model: str) -> list[float]:
    return cast(list[float], SentenceTransformer(model).encode(query).tolist())


def retrieve(
    query: str,
    chroma_dir: Path,
    model: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection("articles")

    count = collection.count()
    if count == 0:
        return []

    embedding = _embed_query(query, model)
    results = collection.query(
        query_embeddings=[embedding],  # type: ignore[arg-type]
        n_results=min(top_k, count),
        include=["documents", "metadatas"],
    )

    documents = results["documents"]
    metadatas = results["metadatas"]
    if documents is None or metadatas is None:
        raise RuntimeError("ChromaDB returned None for documents or metadatas")
    return [
        {"chunk": doc, "metadata": dict(meta)}
        for doc, meta in zip(documents[0], metadatas[0])
    ]
