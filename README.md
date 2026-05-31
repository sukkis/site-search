# Site Search

Ask plain-language questions about any set of web pages and get answers grounded in the actual content — not in what an AI model happens to know from training data.

## How it works

Pages are downloaded and their text extracted. The text is split into passages, and each passage is converted into a vector — a numerical representation of its meaning — using a local embedding model. Those vectors are stored in a local database.

When you ask a question, the question is converted into a vector the same way. The database finds the passages whose meaning is closest to your question, and a local language model reads those passages and writes an answer from them.

This is called RAG (Retrieval-Augmented Generation). The key property is that the model answers from the passages you provide, not from its training data. If a fact is not on the pages you indexed, the model will say so rather than guess.

## Features

- **Fully local** — embedding, retrieval, and generation all run on your machine; no data is sent to any external service
- **Incremental** — fetch and index are idempotent; re-running after adding new URLs processes only the new content
- **Configurable** — embedding model, retrieval depth, chunking parameters, and Ollama model are all tunable via `config.toml`
- **Observable** — every query is traced end-to-end with [Langfuse](https://langfuse.com), capturing the question, retrieved context, generated answer, and token usage

## Prerequisites

- [Ollama](https://ollama.com) installed and running locally
- The `mistral-nemo` model pulled: `ollama pull mistral-nemo`
- Python 3.14+ and [uv](https://docs.astral.sh/uv/)
- [Langfuse](https://langfuse.com/docs/deployment/self-host) running locally (for observability)

## Installation

```bash
uv sync
```

This installs all dependencies into a local virtualenv. Activate it once and the `site-search` command is available directly:

```bash
source .venv/bin/activate
site-search --help
```

## Configuration

Copy the example config and adjust as needed:

```toml
# config.toml

[storage]
cache_dir = "./cache"       # where fetched pages are stored
chroma_dir = "./chroma_db"  # where the vector index is stored

[embedding]
model = "multi-qa-MiniLM-L6-cos-v1"  # must match between index and query

[retrieval]
top_k = 5  # number of passages retrieved per query

[chunking]
target_size = 800   # target passage length in characters
max_size = 1200     # hard upper limit

[ollama]
base_url = "http://localhost:11434"
model = "mistral-nemo:latest"
```

If no `config.toml` is present, the defaults above are used automatically. Copy `config.toml.example` to `config.toml` only if you want to change any values.

## Usage

Site search has three commands that form a pipeline. Run them in order.

### 1. Fetch

Download pages and cache their text to disk:

```bash
site-search fetch urls.txt
```

`urls.txt` is a plain text file with one URL per line:

```
https://www.bbc.com/news/articles/example-one
https://www.bbc.com/news/articles/example-two
https://www.bbc.com/news/articles/example-three
```

Already-cached pages are skipped — safe to re-run after adding new URLs.

### 2. Index

Chunk the cached text, embed it, and store it in the vector database:

```bash
site-search index
```

Re-running after adding new cached pages adds only the new content.

### 3. Query

Ask a question in plain language:

```bash
just query "Which countries are affected by the trade dispute?"
```

The answer will be printed to the terminal, grounded in the indexed pages. The `just query` wrapper injects Langfuse credentials so every query is traced automatically.

## Observability

Every `just query` run produces a trace in the Langfuse UI:

- **`site-search-query`** — the full request, with the question as input and the final answer as output
- **`ollama-generate`** — the LLM call, with the full prompt, model name, answer, and token counts (input tokens from `prompt_eval_count`, output tokens from `eval_count` in the Ollama response)

To view traces, open your local Langfuse instance (default: `http://localhost:3000`).

Langfuse credentials are not stored in the repository. See the developer notes in `ARCHITECTURE.md` for the credential injection pattern.

## Example session

```bash
# Create a list of articles to index
cat > urls.txt <<EOF
https://www.bbc.com/news/articles/kenya-court-ruling
https://www.bbc.com/news/articles/trade-talks-update
EOF

# Fetch and cache the pages
site-search fetch urls.txt

# Build the vector index
site-search index

# Ask questions
just query "What did the Kenyan court decide?"
just query "Which industries are most affected by the trade talks?"
```

## Notes

- The embedding model (`config.toml → embedding.model`) must be the same when indexing and querying. Changing it requires re-running `index`.
- Cached pages (`cache/`) and the vector index (`chroma_db/`) are stored locally and not tracked by git.
- All processing — embedding, generation, and tracing — runs on your machine. No data is sent to any external service.
