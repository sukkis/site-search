from pathlib import Path

import click

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
    config = load_config()
    urls = urls_file.read_text().splitlines()
    fetch_urls(urls, config.storage.cache_dir)


@cli.command()
def index() -> None:
    config = load_config()
    index_cache(
        config.storage.cache_dir,
        config.storage.chroma_dir,
        config.embedding.model,
    )


@cli.command()
@click.argument("question")
def query(question: str) -> None:
    config = load_config()
    chunks = retrieve(
        question,
        config.storage.chroma_dir,
        config.embedding.model,
        config.retrieval.top_k,
    )
    answer = generate(question, chunks, config.ollama.base_url, config.ollama.model)
    click.echo(answer)
