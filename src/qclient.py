"""Обёртки для qdrant-client: создание коллекции, апсерты, поиск."""

from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from .config import QDRANT_HOST, QDRANT_PORT

def get_qdrant_client(host: str = QDRANT_HOST, port: int = QDRANT_PORT) -> QdrantClient:
    """
    Возвращает клиент Qdrant.

    Args:
        host: хост Qdrant
        port: порт Qdrant (HTTP)

    Returns:
        QdrantClient
    """
    return QdrantClient(host=host, port=port)

def ensure_collection(client: QdrantClient, collection_name: str, vector_size: int):
    """
    Создаёт коллекцию, если её нет. Использует расстояние COSINE.

    Args:
        client: QdrantClient
        collection_name: имя коллекции
        vector_size: размер вектора
    """
    try:
        _ = client.get_collection(collection_name)
        return
    except Exception:
        # если не существует — создаём/recreate
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=rest_models.VectorParams(size=vector_size, distance=rest_models.Distance.COSINE),
        )
