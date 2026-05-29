import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from site_search.fetcher import (
    _extract_and_write,
    cache_path,
    fetch_urls,
    url_to_slug,
)


@pytest.fixture(scope="session")
def test_html() -> str:
    return Path("tests/fixtures/bbc_article.html").read_text(encoding="utf-8")


# --- url_to_slug ---


def test_url_to_slug_uses_last_path_segment() -> None:
    url = "https://www.bbc.com/news/articles/world-africa-kenya-court"
    assert url_to_slug(url) == "world_africa_kenya_court"


def test_url_to_slug_truncates_long_slug_to_80_chars() -> None:
    long_segment = "a-very-long-segment-" * 6  # 120 chars
    url = f"https://www.bbc.com/news/articles/{long_segment}"
    slug = url_to_slug(url)
    assert len(slug) == 80
    assert slug.endswith("_")


def test_url_to_slug_does_not_truncate_short_slugs() -> None:
    url = "https://www.bbc.com/news/articles/kenya-court"
    slug = url_to_slug(url)
    assert len(slug) <= 80
    assert not slug.endswith("_")


# --- cache_path ---


def test_cache_path_contains_today_date_and_slug(tmp_path: Path) -> None:
    url = "https://www.bbc.com/news/articles/kenya-court"
    path = cache_path(url, tmp_path)
    assert path.parent == tmp_path
    assert path.name.startswith(date.today().isoformat())
    assert "kenya_court" in path.name
    assert path.suffix == ".json"


# --- fetch_urls ---


def test_fetch_urls_skips_already_cached_url(tmp_path: Path) -> None:
    url = "https://www.bbc.com/news/articles/kenya-court"
    cache_path(url, tmp_path).write_text("{}")
    with patch("trafilatura.fetch_url") as mock_fetch:
        fetch_urls([url], tmp_path)
    mock_fetch.assert_not_called()


def test_fetch_urls_skips_url_when_fetch_returns_none(tmp_path: Path) -> None:
    url = "https://www.bbc.com/news/articles/kenya-court"
    with patch("trafilatura.fetch_url", return_value=None):
        fetch_urls([url], tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_fetch_urls_writes_one_cache_file_per_url(
    tmp_path: Path, test_html: str
) -> None:
    urls = [
        "https://www.bbc.com/news/articles/kenya-court",
        "https://www.bbc.com/news/articles/trade-talks",
    ]
    with patch("trafilatura.fetch_url", return_value=test_html):
        fetch_urls(urls, tmp_path)
    assert len(list(tmp_path.iterdir())) == 2


# --- _extract_and_write ---


def test_extract_and_write_produces_correct_json_fields(
    tmp_path: Path, test_html: str
) -> None:
    url = "https://www.bbc.com/news/articles/test"
    out = tmp_path / "article.json"
    _extract_and_write(test_html, url, out)
    assert out.exists()
    record = json.loads(out.read_text())
    assert record["url"] == url
    assert isinstance(record["text"], str) and record["text"]
    assert "title" in record
    assert "author" in record
    assert "date_published" in record
    assert "fetched_at" in record


def test_extract_and_write_skips_file_when_extraction_fails(tmp_path: Path) -> None:
    out = tmp_path / "article.json"
    _extract_and_write("<html><body></body></html>", "https://example.com", out)
    assert not out.exists()
