"""Обёртки для получения эмбеддингов через Ollama."""

from typing import List
import ollama
from .config import EMBED_MODEL

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Получает эмбеддинги для списка текстов через Ollama.

    Args:
        texts: список строк

    Returns:
        Список векторов (list of float).
    """
    vectors = []
    for t in texts:
        r = ollama.embeddings(model=EMBED_MODEL, prompt=t)
        vec = r.get("embedding")
        if vec is None:
            raise RuntimeError("Ollama embeddings response missing 'embedding'")
        vectors.append([float(x) for x in vec])
    return vectors
