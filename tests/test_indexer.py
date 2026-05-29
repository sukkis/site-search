import json
from pathlib import Path
from unittest.mock import patch

import chromadb
import pytest

from site_search.indexer import (
    _load_records,
    _make_chunk_rows,
    _upsert,
    index_cache,
)

FAKE_EMBEDDING_DIM = 384


@pytest.fixture
def sample_record() -> dict:  # type: ignore[type-arg]
    return {
        "url": "https://example.com/article",
        "title": "Test Article",
        "author": "Test Author",
        "date_published": "2026-05-29",
        "text": "A" * 500 + "\n\n" + "B" * 500,
        "fetched_at": "2026-05-29T12:00:00+00:00",
    }


# --- _load_records ---


def test_load_records_reads_all_json_files(tmp_path: Path) -> None:
    (tmp_path / "a.json").write_text(json.dumps({"url": "a"}))
    (tmp_path / "b.json").write_text(json.dumps({"url": "b"}))
    records = _load_records(tmp_path)
    assert len(records) == 2


def test_load_records_returns_empty_list_for_empty_directory(tmp_path: Path) -> None:
    assert _load_records(tmp_path) == []


# --- _make_chunk_rows ---


def test_make_chunk_rows_returns_one_row_per_chunk(
    sample_record: dict,  # type: ignore[type-arg]
) -> None:
    rows = _make_chunk_rows(sample_record)
    assert len(rows) == 2  # two 500-char paragraphs exceed target_size=800


def test_make_chunk_rows_metadata_contains_article_fields(
    sample_record: dict,  # type: ignore[type-arg]
) -> None:
    rows = _make_chunk_rows(sample_record)
    for row in rows:
        assert row["metadata"]["url"] == sample_record["url"]
        assert row["metadata"]["title"] == sample_record["title"]
        assert row["metadata"]["author"] == sample_record["author"]
        assert row["metadata"]["date_published"] == sample_record["date_published"]


def test_make_chunk_rows_ids_are_unique(
    sample_record: dict,  # type: ignore[type-arg]
) -> None:
    rows = _make_chunk_rows(sample_record)
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))


def test_make_chunk_rows_replaces_none_metadata_with_empty_string() -> None:
    record = {
        "url": "https://example.com/article",
        "title": None,
        "author": None,
        "date_published": None,
        "text": "A" * 500,
        "fetched_at": "2026-05-29T12:00:00+00:00",
    }
    rows = _make_chunk_rows(record)
    assert len(rows) == 1
    meta = rows[0]["metadata"]
    assert meta["title"] == ""
    assert meta["author"] == ""
    assert meta["date_published"] == ""


def test_make_chunk_rows_returns_empty_list_when_text_is_missing() -> None:
    record = {
        "url": "https://example.com/article",
        "title": None,
        "author": None,
        "date_published": None,
        "text": None,
        "fetched_at": "2026-05-29T12:00:00+00:00",
    }
    assert _make_chunk_rows(record) == []


# --- _upsert ---


def test_upsert_stores_all_chunks_in_collection(tmp_path: Path) -> None:
    client = chromadb.PersistentClient(path=str(tmp_path))
    collection = client.get_or_create_collection("test")
    rows = [
        {"id": "id1", "chunk": "chunk one", "metadata": {"url": "a"}},
        {"id": "id2", "chunk": "chunk two", "metadata": {"url": "a"}},
    ]
    embeddings = [[0.1] * FAKE_EMBEDDING_DIM, [0.2] * FAKE_EMBEDDING_DIM]
    _upsert(collection, rows, embeddings)
    assert collection.count() == 2


def test_upsert_is_idempotent(tmp_path: Path) -> None:
    client = chromadb.PersistentClient(path=str(tmp_path))
    collection = client.get_or_create_collection("test")
    rows = [{"id": "id1", "chunk": "chunk one", "metadata": {"url": "a"}}]
    embeddings = [[0.1] * FAKE_EMBEDDING_DIM]
    _upsert(collection, rows, embeddings)
    _upsert(collection, rows, embeddings)
    assert collection.count() == 1


# --- index_cache (integration) ---


def test_index_cache_populates_collection(
    tmp_path: Path,
    sample_record: dict,  # type: ignore[type-arg]
) -> None:
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    chroma_dir = tmp_path / "chroma"
    (cache_dir / "article.json").write_text(json.dumps(sample_record))

    fake_embeddings = [[0.1] * FAKE_EMBEDDING_DIM, [0.2] * FAKE_EMBEDDING_DIM]
    with patch("site_search.indexer._embed", return_value=fake_embeddings):
        index_cache(cache_dir, chroma_dir, "some-model")

    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection("articles")
    assert collection.count() == 2
