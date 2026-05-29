# Site Search

Ask plain-language questions about any set of web pages and get answers grounded in the actual content — not in what an AI model happens to know from training data.

## How it works

Pages are downloaded and their text extracted. The text is split into passages, and each passage is converted into a vector — a numerical representation of its meaning — using a local embedding model. Those vectors are stored in a local database.

When you ask a question, the question is converted into a vector the same way. The database finds the passages whose meaning is closest to your question, and a local language model reads those passages and writes an answer from them.

This is called RAG (Retrieval-Augmented Generation). The key property is that the model answers from the passages you provide, not from its training data. If a fact is not on the pages you indexed, the model will say so rather than guess.

## Prerequisites

- [Ollama](https://ollama.com) installed and running locally
- The `mistral-nemo` model pulled: `ollama pull mistral-nemo`
- Python 3.14+ and [uv](https://docs.astral.sh/uv/)

## Installation

```bash
uv sync
```

This installs all dependencies into a local virtualenv. The `site-search` command is then available via `uv run site-search`.

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

`config.toml` must be present in the directory where you run the commands.

## Usage

Site search has three commands that form a pipeline. Run them in order.

### 1. Fetch

Download pages and cache their text to disk:

```bash
uv run site-search fetch urls.txt
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
uv run site-search index
```

Re-running after adding new cached pages adds only the new content.

### 3. Query

Ask a question in plain language:

```bash
uv run site-search query "Which countries are affected by the trade dispute?"
```

The answer will be printed to the terminal, grounded in the indexed pages.

## Example session

```bash
# Create a list of articles to index
cat > urls.txt <<EOF
https://www.bbc.com/news/articles/kenya-court-ruling
https://www.bbc.com/news/articles/trade-talks-update
EOF

# Fetch and cache the pages
uv run site-search fetch urls.txt

# Build the vector index
uv run site-search index

# Ask questions
uv run site-search query "What did the Kenyan court decide?"
uv run site-search query "Which industries are most affected by the trade talks?"
```

## Notes

- The embedding model (`config.toml → embedding.model`) must be the same when indexing and querying. Changing it requires re-running `index`.
- Cached pages (`cache/`) and the vector index (`chroma_db/`) are stored locally and not tracked by git.
- All processing — embedding and generation — runs on your machine. No data is sent to any external service.
