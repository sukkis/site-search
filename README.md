# Site Search

A semantic search tool for websites. Given a set of URLs, it ingests the page content, builds a vector index, and answers plain-language questions about that content — returning answers grounded in the actual text rather than LLM training data.

## How it works

Pages are scraped and cleaned, split into chunks, and embedded into vectors using a pre-trained model. At query time the question is embedded the same way, the closest matching chunks are retrieved from the vector store, and an LLM generates an answer from those chunks.

## Stack

- **trafilatura** — extract clean article text from HTML
- **sentence-transformers** — local embedding model
- **ChromaDB** — lightweight in-process vector store
