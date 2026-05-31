from typing import Any

import httpx
from langfuse import get_client


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
    langfuse = get_client()
    prompt = _build_prompt(question, chunks)
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="ollama-generate",
        model=model,
    ) as obs:
        response = httpx.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120.0,
        )
        data = response.json()
        answer = str(data["response"])
        obs.update(
            input=prompt,
            output=answer,
            usage_details={
                "input": data.get("prompt_eval_count"),
                "output": data.get("eval_count"),
            },
        )
        return answer
