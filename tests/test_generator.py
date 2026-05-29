from typing import Any
from unittest.mock import MagicMock, patch

from site_search.generator import _build_prompt, generate

BASE_URL = "http://localhost:11434"
MODEL = "mistral-nemo"


def make_chunks(texts: list[str]) -> list[dict[str, Any]]:
    return [
        {"chunk": t, "metadata": {"url": "https://example.com", "title": "Test"}}
        for t in texts
    ]


# --- _build_prompt ---


def test_build_prompt_contains_question() -> None:
    prompt = _build_prompt("What happened in Kenya?", make_chunks(["Some context."]))
    assert "What happened in Kenya?" in prompt


def test_build_prompt_contains_chunk_text() -> None:
    prompt = _build_prompt(
        "What happened?", make_chunks(["Kenya court halted flights."])
    )
    assert "Kenya court halted flights." in prompt


def test_build_prompt_contains_all_chunks() -> None:
    chunks = make_chunks(["First chunk.", "Second chunk.", "Third chunk."])
    prompt = _build_prompt("What happened?", chunks)
    assert "First chunk." in prompt
    assert "Second chunk." in prompt
    assert "Third chunk." in prompt


# --- generate ---


def test_generate_returns_ollama_response() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "The answer."}
    with patch("httpx.post", return_value=mock_resp):
        result = generate("What happened?", make_chunks(["context"]), BASE_URL, MODEL)
    assert result == "The answer."


def test_generate_posts_to_correct_url() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "ok"}
    with patch("httpx.post", return_value=mock_resp) as mock_post:
        generate("What happened?", make_chunks(["context"]), BASE_URL, MODEL)
    assert mock_post.call_args[0][0] == f"{BASE_URL}/api/generate"


def test_generate_sends_model_name_in_payload() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "ok"}
    with patch("httpx.post", return_value=mock_resp) as mock_post:
        generate("What happened?", make_chunks(["context"]), BASE_URL, MODEL)
    assert mock_post.call_args[1]["json"]["model"] == MODEL


def test_generate_sends_prompt_in_payload() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "ok"}
    with patch("httpx.post", return_value=mock_resp) as mock_post:
        generate("What happened?", make_chunks(["context"]), BASE_URL, MODEL)
    assert "prompt" in mock_post.call_args[1]["json"]


def test_generate_with_empty_chunks_still_calls_ollama() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "I don't know."}
    with patch("httpx.post", return_value=mock_resp) as mock_post:
        result = generate("What happened?", [], BASE_URL, MODEL)
    mock_post.assert_called_once()
    assert result == "I don't know."
