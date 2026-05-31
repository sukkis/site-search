from typing import Any

import httpx


def _build_prompt(question: str, chunks: list[dict[str, Any]]) -> str:
    parts = [
        f"Context {i}:\n{chunk['chunk']}" for i, chunk in enumerate(chunks, start=1)
    ]
    context = "\n\n".join(parts)
    return f"{context}\n\nQuestion: {question}\nAnswer:"


def generate(
    question: str,
    chunks: list[dict[str, Any]],
    base_url: str,
    model: str,
) -> str:
    prompt = _build_prompt(question, chunks)
    response = httpx.post(
        f"{base_url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120.0,
    )
    return str(response.json()["response"])
