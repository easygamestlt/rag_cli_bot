"""Поиск в Qdrant: встраивание запроса и возврат топ-K результатов."""

from typing import List, Tuple
from .embedder import embed_texts
from .qclient import get_qdrant_client
from .indexer import ChunkMeta

def retrieve_from_qdrant(query: str, collection_name: str, top_k: int = 5) -> List[Tuple[float, ChunkMeta]]:
    """
    Встраивает запрос, запрашивает Qdrant и возвращает топ-K результатов с payload.

    Args:
        query: пользовательский запрос
        collection_name: имя коллекции в Qdrant
        top_k: число возвращаемых результатов

    Returns:
        Список кортежей (score, ChunkMeta)
    """
    client = get_qdrant_client()
    qvec = embed_texts([query])[0]
    search_result = client.search(collection_name=collection_name, query_vector=qvec, limit=top_k,
                                  with_payload=True, with_vectors=False)
    results = []
    for item in search_result:
        score = float(item.score) if item.score is not None else 0.0
        payload = item.payload or {}
        ch = ChunkMeta(url=payload.get("url", ""), doc_id=payload.get("doc_id", ""),
                       chunk_id=payload.get("chunk_id", -1), text=payload.get("text", ""))
        results.append((score, ch))
    return results
