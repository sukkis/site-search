import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import trafilatura


def fetch_urls(urls: list[str], cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    for url in urls:
        path = cache_path(url, cache_dir)
        if path.exists():
            continue
        _fetch_and_cache(url, path)


def cache_path(url: str, cache_dir: Path) -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = url_to_slug(url)
    return cache_dir / f"{today}_{slug}.json"


def url_to_slug(url: str) -> str:
    path = urlparse(url).path
    segments = [s for s in path.split("/") if s]
    raw = segments[-1] if segments else "page"
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", raw).strip("_")
    if len(slug) > 80:
        return slug[:79] + "_"
    return slug


def _fetch_and_cache(url: str, path: Path) -> None:
    html = trafilatura.fetch_url(url)
    if html is None:
        return
    _extract_and_write(html, url, path)


def _extract_and_write(html: str, url: str, path: Path) -> None:
    data = trafilatura.extract(html, output_format="json", with_metadata=True)
    if data is None:
        return
    parsed = json.loads(data)
    record = {
        "url": url,
        "title": parsed.get("title"),
        "author": parsed.get("author"),
        "date_published": parsed.get("date"),
        "text": parsed.get("text"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
