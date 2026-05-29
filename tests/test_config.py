from pathlib import Path

import pytest

from site_search.config import Config, load_config

SAMPLE_TOML = """\
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
"""


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(SAMPLE_TOML)
    return path


def test_load_config_returns_config_instance(config_file: Path) -> None:
    assert isinstance(load_config(config_file), Config)


def test_load_config_reads_cache_dir(config_file: Path) -> None:
    assert load_config(config_file).storage.cache_dir == Path("./cache")


def test_load_config_reads_chroma_dir(config_file: Path) -> None:
    assert load_config(config_file).storage.chroma_dir == Path("./chroma_db")


def test_load_config_reads_embedding_model(config_file: Path) -> None:
    assert load_config(config_file).embedding.model == "multi-qa-MiniLM-L6-cos-v1"


def test_load_config_reads_top_k(config_file: Path) -> None:
    assert load_config(config_file).retrieval.top_k == 5


def test_load_config_reads_chunking_params(config_file: Path) -> None:
    config = load_config(config_file)
    assert config.chunking.target_size == 800
    assert config.chunking.max_size == 1200


def test_load_config_reads_ollama_params(config_file: Path) -> None:
    config = load_config(config_file)
    assert config.ollama.base_url == "http://localhost:11434"
    assert config.ollama.model == "mistral-nemo:latest"


def test_load_config_returns_defaults_when_file_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path / "nonexistent.toml")
    assert config.storage.cache_dir == Path("./cache")
    assert config.embedding.model == "multi-qa-MiniLM-L6-cos-v1"
    assert config.retrieval.top_k == 5
    assert config.chunking.target_size == 800
    assert config.ollama.model == "mistral-nemo:latest"
