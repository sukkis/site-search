# Architecture

## Overview

This is a RAG (Retrieval-Augmented Generation) pipeline that answers plain-language questions about a set of web pages. It is split into three independent pipeline stages, each exposed as a CLI command: `fetch`, `index`, and `query`. The stages communicate through files on disk, which makes each stage independently testable and inspectable without running the full pipeline.

## Data Flow

```
Ingest phase:
  urls.txt ──► fetcher ──► cache/2026-05-29_article-slug.json
                  │
                  └── trafilatura extracts clean text and metadata from HTML

Index phase:
  cache/*.json ──► chunker ──► indexer ──► ChromaDB (chroma_db/)
                      │            │
                      │            └── sentence-transformers embeds each chunk
                      └── splits article text into paragraph-aware chunks

Query phase:
  question ──► retriever ──► generator ──► answer
                   │              │
                   │              └── Ollama (mistral-nemo) generates answer
                   └── embeds question, retrieves top-K chunks from ChromaDB
```

## Pipeline Stages

### Stage 1: Fetch (`site-search fetch urls.txt`)

Reads a plain text file of URLs (one per line), downloads each page, and extracts the article content using trafilatura. The result is cached to disk as one JSON file per URL.

Cache files are skipped if already present on disk, making re-runs cheap. The filename encodes the fetch date and a slug from the URL path: `YYYY-MM-DD_article-slug.json`. Same-day collisions on the same URL slug are accepted in this version.

Each cache file contains:

```json
{
  "url": "https://...",
  "title": "Article title",
  "author": "Author name",
  "date_published": "2026-05-29",
  "text": "Full extracted article text...",
  "fetched_at": "2026-05-29T14:32:00Z"
}
```

### Stage 2: Index (`site-search index`)

Reads all JSON files from the cache directory, splits each article's text into chunks using the chunker, embeds each chunk using a local sentence-transformers model, and stores the vectors in ChromaDB alongside the chunk text and article metadata.

ChromaDB is opened in persistent mode so the index survives between process runs. The index step is idempotent with respect to cache contents: re-running it after adding new cache files adds only the new chunks.

### Stage 3: Query (`site-search query "question"`)

Embeds the question using the same sentence-transformers model used during indexing (a requirement: vectors from different models are incompatible). Retrieves the top-K closest chunks from ChromaDB. Constructs a prompt containing the question and the retrieved chunks, and sends it to the local Ollama instance. Prints the generated answer.

## Modules

| Module | Responsibility |
|---|---|
| `config.py` | Loads `config.toml` using stdlib `tomllib`; exposes a typed config object |
| `fetcher.py` | Downloads URLs, calls trafilatura, writes cache JSON files |
| `chunker.py` | Pure function: takes article text, returns list of string chunks |
| `indexer.py` | Reads cache, calls chunker, embeds chunks, stores in ChromaDB |
| `retriever.py` | Embeds a query, searches ChromaDB, returns top-K chunks with metadata |
| `generator.py` | Constructs a prompt and calls Ollama via HTTP, returns answer string |
| `cli.py` | Click command definitions; thin wrappers that delegate to the modules above |

`chunker.py` is intentionally a pure module with no I/O — it takes text in and returns a list of strings out. This makes it the easiest module to test thoroughly and to reason about in isolation.

## Entry Point

Execution is declared in `pyproject.toml`:

```toml
[project.scripts]
site-search = "site_search.cli:cli"
```

After `uv sync`, the `site-search` command is available in the virtualenv. `cli.py` is the closest thing to a traditional `main` file. The package also supports `python -m site_search` via `__main__.py`, which simply calls `cli()`.

## Dependencies

| Library | Justification |
|---|---|
| `trafilatura` | HTML-to-text extraction purpose-built for news and article content; stripping boilerplate reliably is non-trivial and not the focus of this project |
| `sentence-transformers` | Provides pre-trained embedding models that run locally; training our own model is out of scope |
| `chromadb` | Lightweight vector database that runs in-process with no separate server; suitable for local development |
| `httpx` | HTTP client for calling the Ollama API; more ergonomic than stdlib `urllib` and avoids pulling in the full `openai` SDK for a simple POST call |
| `click` | CLI argument parsing; significantly cleaner than stdlib `argparse` for multi-command CLIs; the de facto standard for Python CLI tooling |

All heavy ML dependencies (`sentence-transformers`, `chromadb`) run fully locally. The LLM is served by Ollama on localhost. No data leaves the machine during normal operation.

## Configuration

All tunable parameters live in `config.toml` at the project root:

```toml
[storage]
cache_dir = "./cache"
chroma_dir = "./chroma_db"

[embedding]
model = "multi-qa-MiniLM-L6-cos-v1"

[retrieval]
top_k = 5

[chunking]
target_size = 800
max_size = 1200

[ollama]
base_url = "http://localhost:11434"
model = "mistral-nemo:latest"
```

The embedding model name must match between the `index` and `query` stages — using a different model for each produces incompatible vector spaces and silently broken retrieval.

## Storage Layout

```
site-search/
├── cache/                  # fetcher output; one JSON file per URL
│   └── 2026-05-29_article-slug.json
├── chroma_db/              # ChromaDB persistent storage; indexer output
├── config.toml             # all tunable parameters
├── site_search/            # application package
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py
│   ├── fetcher.py
│   ├── chunker.py
│   ├── indexer.py
│   ├── retriever.py
│   ├── generator.py
│   └── cli.py
└── tests/
    ├── test_fetcher.py
    ├── test_chunker.py
    ├── test_indexer.py
    ├── test_retriever.py
    └── test_generator.py
```

`cache/`, `chroma_db/`, and `tests/fixtures/` are excluded from version control via `.gitignore`. The test fixture is a real news article HTML file kept locally; a synthetic copyright-free replacement is planned.

## Observability

LangFuse is included in the MVP scope for tracing individual pipeline runs: what chunks were retrieved, what prompt was sent, what the LLM returned, and latency at each step. It runs locally via Docker and no trace data leaves the machine. LangFuse integration is added after the core pipeline is working end-to-end.

## Implementation Order

The modules are built in this order, each with tests written first (TDD):

1. `chunker.py` — pure function, no dependencies, easiest to test
2. `fetcher.py` — introduces trafilatura and disk I/O
3. `indexer.py` — introduces sentence-transformers and ChromaDB
4. `retriever.py` — queries ChromaDB
5. `generator.py` — introduces httpx and Ollama
6. `cli.py` — wires the commands together with click
7. LangFuse — wraps the pipeline with observability traces
