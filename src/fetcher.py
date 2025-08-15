"""Загрузка HTML и преобразование его в текст."""

from typing import List
import requests
from bs4 import BeautifulSoup
import html2text
from .config import HEADERS, TIMEOUT

def fetch_html(url: str) -> str:
    """
    Загружает HTML по URL.

    Args:
        url: ссылка на страницу

    Returns:
        Содержимое HTML в виде строки.

    Raises:
        HTTPError при ошибке запроса.
    """
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text

def html_to_text(html_content: str) -> str:
    """
    Превращает HTML в плоский текст (markdown-like) с удалением скриптов и лишних блоков.

    Args:
        html_content: HTML как строка

    Returns:
        Чистый текст.
    """
    soup = BeautifulSoup(html_content, "lxml")
    for tag in soup(["script", "style", "noscript", "iframe", "svg", "header", "footer", "nav"]):
        tag.decompose()
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.body_width = 0
    text = h.handle(str(soup))
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Разбивает длинный текст на перекрывающиеся чанки.

    Args:
        text: исходный текст
        chunk_size: максимальная длина чанка (символы)
        overlap: перекрытие между соседними чанками

    Returns:
        Список чанков (строк).
    """
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks
