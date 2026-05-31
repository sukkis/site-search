import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_DEFAULTS = {
    "storage": {"cache_dir": "./cache", "chroma_dir": "./chroma_db"},
    "embedding": {"model": "multi-qa-MiniLM-L6-cos-v1"},
    "retrieval": {"top_k": 5},
    "chunking": {"target_size": 800, "max_size": 1200},
    "ollama": {"base_url": "http://localhost:11434", "model": "mistral-nemo:latest"},
}


@dataclass
class StorageConfig:
    cache_dir: Path
    chroma_dir: Path


@dataclass
class EmbeddingConfig:
    model: str


@dataclass
class RetrievalConfig:
    top_k: int


@dataclass
class ChunkingConfig:
    target_size: int
    max_size: int


@dataclass
class OllamaConfig:
    base_url: str
    model: str


@dataclass
class Config:
    storage: StorageConfig
    embedding: EmbeddingConfig
    retrieval: RetrievalConfig
    chunking: ChunkingConfig
    ollama: OllamaConfig


def _build(data: dict[str, Any]) -> Config:
    s = data["storage"]
    e = data["embedding"]
    r = data["retrieval"]
    c = data["chunking"]
    o = data["ollama"]
    return Config(
        storage=StorageConfig(
            cache_dir=Path(s["cache_dir"]),
            chroma_dir=Path(s["chroma_dir"]),
        ),
        embedding=EmbeddingConfig(model=e["model"]),
        retrieval=RetrievalConfig(top_k=r["top_k"]),
        chunking=ChunkingConfig(
            target_size=c["target_size"],
            max_size=c["max_size"],
        ),
        ollama=OllamaConfig(base_url=o["base_url"], model=o["model"]),
    )


def load_config(path: Path = Path("config.toml")) -> Config:
    if not path.exists():
        return _build(_DEFAULTS)
    with open(path, "rb") as f:
        return _build(tomllib.load(f))
