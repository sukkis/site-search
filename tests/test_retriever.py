from pathlib import Path
from unittest.mock import patch

import chromadb
import pytest

from site_search.retriever import retrieve

FAKE_DIM = 384


@pytest.fixture
def populated_chroma(tmp_path: Path) -> Path:
    client = chromadb.PersistentClient(path=str(tmp_path))
    collection = client.get_or_create_collection("articles")
    chunks = [
        "Kenya court halted deportation flights.",
        "Trade talks resumed in Geneva.",
        "New climate deal signed at summit.",
        "Tech layoffs continue across sector.",
        "Central bank raises interest rates.",
    ]
    metadatas = [
        {"url": f"https://example.com/{i}", "title": f"Article {i}"}
        for i in range(len(chunks))
    ]
    ids = [f"id{i}" for i in range(len(chunks))]
    embeddings = [[float(i) / 10] * FAKE_DIM for i in range(len(chunks))]
    collection.add(
        documents=chunks, embeddings=embeddings, metadatas=metadatas, ids=ids
    )
    return tmp_path


def fake_embedding() -> list[float]:
    return [0.0] * FAKE_DIM


def test_retrieve_returns_top_k_results(populated_chroma: Path) -> None:
    with patch("site_search.retriever._embed_query", return_value=fake_embedding()):
        results = retrieve(
            "What happened in Kenya?", populated_chroma, "any-model", top_k=3
        )
    assert len(results) == 3


def test_retrieve_result_contains_chunk_and_metadata_fields(
    populated_chroma: Path,
) -> None:
    with patch("site_search.retriever._embed_query", return_value=fake_embedding()):
        results = retrieve(
            "What happened in Kenya?", populated_chroma, "any-model", top_k=1
        )
    assert "chunk" in results[0]
    assert "metadata" in results[0]
    assert isinstance(results[0]["chunk"], str)
    assert isinstance(results[0]["metadata"], dict)


def test_retrieve_metadata_contains_url_and_title(populated_chroma: Path) -> None:
    with patch("site_search.retriever._embed_query", return_value=fake_embedding()):
        results = retrieve(
            "What happened in Kenya?", populated_chroma, "any-model", top_k=1
        )
    assert "url" in results[0]["metadata"]
    assert "title" in results[0]["metadata"]


def test_retrieve_returns_fewer_results_when_collection_is_smaller_than_top_k(
    tmp_path: Path,
) -> None:
    client = chromadb.PersistentClient(path=str(tmp_path))
    collection = client.get_or_create_collection("articles")
    collection.add(
        documents=["Only one chunk."],
        embeddings=[[0.1] * FAKE_DIM],
        metadatas=[{"url": "https://example.com", "title": "One"}],
        ids=["id0"],
    )
    with patch("site_search.retriever._embed_query", return_value=fake_embedding()):
        results = retrieve("anything", tmp_path, "any-model", top_k=5)
    assert len(results) == 1


def test_retrieve_returns_empty_list_for_empty_collection(tmp_path: Path) -> None:
    chromadb.PersistentClient(path=str(tmp_path)).get_or_create_collection("articles")
    with patch("site_search.retriever._embed_query", return_value=fake_embedding()):
        results = retrieve("anything", tmp_path, "any-model", top_k=5)
    assert results == []
