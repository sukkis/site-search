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


# --- Langfuse tracing ---


def _make_langfuse_mock() -> tuple[MagicMock, MagicMock]:
    """Return (mock_client, mock_observation) with context-manager wiring."""
    mock_obs = MagicMock()
    mock_obs.__enter__ = MagicMock(return_value=mock_obs)
    mock_obs.__exit__ = MagicMock(return_value=False)
    mock_client = MagicMock()
    mock_client.start_as_current_observation.return_value = mock_obs
    return mock_client, mock_obs


def test_generate_creates_generation_observation() -> None:
    mock_client, _ = _make_langfuse_mock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "answer"}
    with (
        patch("site_search.generator.get_client", return_value=mock_client),
        patch("httpx.post", return_value=mock_resp),
    ):
        generate("q", make_chunks(["ctx"]), BASE_URL, MODEL)
    mock_client.start_as_current_observation.assert_called_once()
    _, kwargs = mock_client.start_as_current_observation.call_args
    assert kwargs.get("as_type") == "generation"
    assert kwargs.get("model") == MODEL


def test_generate_sets_prompt_as_observation_input() -> None:
    mock_client, mock_obs = _make_langfuse_mock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "answer"}
    with (
        patch("site_search.generator.get_client", return_value=mock_client),
        patch("httpx.post", return_value=mock_resp),
    ):
        generate("q", make_chunks(["ctx"]), BASE_URL, MODEL)
    update_calls = mock_obs.update.call_args_list
    inputs = [c.kwargs.get("input") for c in update_calls if "input" in c.kwargs]
    assert any(inputs), "observation.update() was never called with input="


def test_generate_sets_answer_as_observation_output() -> None:
    mock_client, mock_obs = _make_langfuse_mock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "The answer."}
    with (
        patch("site_search.generator.get_client", return_value=mock_client),
        patch("httpx.post", return_value=mock_resp),
    ):
        generate("q", make_chunks(["ctx"]), BASE_URL, MODEL)
    update_calls = mock_obs.update.call_args_list
    outputs = [c.kwargs.get("output") for c in update_calls if "output" in c.kwargs]
    assert "The answer." in outputs


def test_generate_sets_token_usage_from_ollama_response() -> None:
    mock_client, mock_obs = _make_langfuse_mock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "response": "ans",
        "prompt_eval_count": 42,
        "eval_count": 17,
    }
    with (
        patch("site_search.generator.get_client", return_value=mock_client),
        patch("httpx.post", return_value=mock_resp),
    ):
        generate("q", make_chunks(["ctx"]), BASE_URL, MODEL)
    update_calls = mock_obs.update.call_args_list
    usage_values = [
        c.kwargs.get("usage_details")
        for c in update_calls
        if "usage_details" in c.kwargs
    ]
    assert usage_values, "observation.update() was never called with usage_details="
    usage = usage_values[0]
    assert usage["input"] == 42
    assert usage["output"] == 17
