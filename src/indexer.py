"""Логика индексации: fetch -> chunk -> embed -> upsert в Qdrant."""

from typing import List
from .fetcher import fetch_html, html_to_text, chunk_text
from .embedder import embed_texts
from .qclient import get_qdrant_client, ensure_collection
from qdrant_client.http import models as rest_models

from dataclasses import dataclass

@dataclass
class ChunkMeta:
    """Метаданые для чанка."""
    url: str
    doc_id: str
    chunk_id: int
    text: str

def build_index_from_urls(urls: List[str], collection_name: str, batch_size: int,
                          chunk_size: int, overlap: int):
    """
    Индексирует список URL: скачивает, парсит, дробит на чанки, получает эмбеддинги
    и загружает в Qdrant по батчам.

    Args:
        urls: список URL
        collection_name: имя коллекции в Qdrant
        batch_size: размер батча для embed+upsert
        chunk_size: длина чанка (символы)
        overlap: перекрытие чанков
    """
    client = get_qdrant_client()
    all_chunks: List[ChunkMeta] = []
    for i, url in enumerate(urls):
        try:
            html = fetch_html(url)
            text = html_to_text(html)
            pieces = chunk_text(text, chunk_size, overlap)
            for j, p in enumerate(pieces):
                all_chunks.append(ChunkMeta(url=url, doc_id=f"doc{i}", chunk_id=j, text=p))
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")

    if not all_chunks:
        raise RuntimeError("No chunks to index.")

    vector_dim = None
    next_id = 0
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        texts = [c.text for c in batch]
        vectors = embed_texts(texts)
        if vector_dim is None:
            vector_dim = len(vectors[0])
            ensure_collection(client, collection_name, vector_dim)
        points = []
        for vec, c in zip(vectors, batch):
            payload = {"url": c.url, "doc_id": c.doc_id, "chunk_id": c.chunk_id, "text": c.text}
            points.append(rest_models.PointStruct(id=next_id, vector=vec, payload=payload))
            next_id += 1
        client.upsert(collection_name=collection_name, points=points)
        print(f"Upserted batch {i//batch_size + 1} ({len(points)} points)")
    print("Indexing finished.")
