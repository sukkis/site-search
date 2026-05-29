from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from site_search.cli import cli
from site_search.config import (
    ChunkingConfig,
    Config,
    EmbeddingConfig,
    OllamaConfig,
    RetrievalConfig,
    StorageConfig,
)


@pytest.fixture
def fake_config() -> Config:
    return Config(
        storage=StorageConfig(
            cache_dir=Path("./cache"), chroma_dir=Path("./chroma_db")
        ),
        embedding=EmbeddingConfig(model="test-model"),
        retrieval=RetrievalConfig(top_k=3),
        chunking=ChunkingConfig(target_size=800, max_size=1200),
        ollama=OllamaConfig(
            base_url="http://localhost:11434", model="mistral-nemo"
        ),
    )


def test_fetch_command_calls_fetch_urls(
    tmp_path: Path, fake_config: Config
) -> None:
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text("https://example.com\n")
    runner = CliRunner()
    with (
        patch("site_search.cli.load_config", return_value=fake_config),
        patch("site_search.cli.fetch_urls") as mock_fetch,
    ):
        result = runner.invoke(cli, ["fetch", str(urls_file)])
    assert result.exit_code == 0
    mock_fetch.assert_called_once()


def test_fetch_command_passes_urls_from_file(
    tmp_path: Path, fake_config: Config
) -> None:
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text("https://example.com\nhttps://other.com\n")
    runner = CliRunner()
    with (
        patch("site_search.cli.load_config", return_value=fake_config),
        patch("site_search.cli.fetch_urls") as mock_fetch,
    ):
        runner.invoke(cli, ["fetch", str(urls_file)])
    urls_arg = mock_fetch.call_args[0][0]
    assert "https://example.com" in urls_arg
    assert "https://other.com" in urls_arg


def test_index_command_calls_index_cache(fake_config: Config) -> None:
    runner = CliRunner()
    with (
        patch("site_search.cli.load_config", return_value=fake_config),
        patch("site_search.cli.index_cache") as mock_index,
    ):
        result = runner.invoke(cli, ["index"])
    assert result.exit_code == 0
    mock_index.assert_called_once()


def test_query_command_prints_answer(fake_config: Config) -> None:
    runner = CliRunner()
    with (
        patch("site_search.cli.load_config", return_value=fake_config),
        patch("site_search.cli.retrieve", return_value=[]),
        patch("site_search.cli.generate", return_value="The answer."),
    ):
        result = runner.invoke(cli, ["query", "What happened?"])
    assert result.exit_code == 0
    assert "The answer." in result.output


def test_query_command_passes_question_to_retrieve(fake_config: Config) -> None:
    runner = CliRunner()
    with (
        patch("site_search.cli.load_config", return_value=fake_config),
        patch("site_search.cli.retrieve", return_value=[]) as mock_retrieve,
        patch("site_search.cli.generate", return_value="ok"),
    ):
        runner.invoke(cli, ["query", "What happened in Kenya?"])
    assert mock_retrieve.call_args[0][0] == "What happened in Kenya?"


def test_query_command_passes_chunks_to_generate(fake_config: Config) -> None:
    fake_chunks = [{"chunk": "some text", "metadata": {}}]
    runner = CliRunner()
    with (
        patch("site_search.cli.load_config", return_value=fake_config),
        patch("site_search.cli.retrieve", return_value=fake_chunks),
        patch("site_search.cli.generate", return_value="ok") as mock_gen,
    ):
        runner.invoke(cli, ["query", "What happened?"])
    assert mock_gen.call_args[0][1] == fake_chunks
