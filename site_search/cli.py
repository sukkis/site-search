from pathlib import Path

import click
from langfuse import get_client

from site_search.config import load_config
from site_search.fetcher import fetch_urls
from site_search.generator import generate
from site_search.indexer import index_cache
from site_search.retriever import retrieve


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("urls_file", type=click.Path(exists=True, path_type=Path))
def fetch(urls_file: Path) -> None:
    """Download and cache pages from a list of URLs."""
    config = load_config()
    urls = urls_file.read_text().splitlines()
    fetch_urls(urls, config.storage.cache_dir)


@cli.command()
def index() -> None:
    """Embed cached pages and store them in the vector index."""
    config = load_config()
    index_cache(
        config.storage.cache_dir,
        config.storage.chroma_dir,
        config.embedding.model,
    )


@cli.command()
@click.argument("question")
def query(question: str) -> None:
    """Ask a plain-language question about the indexed pages."""
    config = load_config()
    langfuse = get_client()
    with langfuse.start_as_current_observation(
        as_type="span",
        name="site-search-query",
        input=question,
    ) as trace:
        chunks = retrieve(
            question,
            config.storage.chroma_dir,
            config.embedding.model,
            config.retrieval.top_k,
        )
        answer = generate(question, chunks, config.ollama.base_url, config.ollama.model)
        trace.update(output=answer)
    langfuse.flush()
    click.echo(answer)
