"""Утилиты: очистка вывода модели, разбиение на предложения, безопасная подстановка ссылок."""

import re
import html

THINK_RE = re.compile(r"<think>.*?</think>\s*", flags=re.DOTALL | re.IGNORECASE)
REF_MARK_RE = re.compile(r"\[(\d+)\]")

def clean_model_output(text: str) -> str:
    """
    Удаляет блочные теги рассуждений вроде <think>...</think> и тримит пробелы.

    Args:
        text: Строка, возвращённая моделью.

    Returns:
        Очищенная строка.
    """
    if not text:
        return ""
    return THINK_RE.sub("", text).strip()

def enforce_three_sentences(text: str) -> str:
    """
    Обрезает текст до первых трёх предложений (грубое деление по .!?).

    Args:
        text: Входной текст (до списка источников).

    Returns:
        Текст, содержащий не более трёх предложений.
    """
    parts = text.split("\n\nСписок источников:")
    body = parts[0].strip()
    refs = ("\n\nСписок источников:" + parts[1]) if len(parts) > 1 else ""
    sents = re.split(r"(?<=[.!?])\s+", body)
    body_short = " ".join(sents[:3]).strip()
    return (body_short + refs).strip()

def linkify_refs(text: str, url_by_index: dict[int, str]) -> str:
    """
    Безопасно превращает [n] в кликабельную ссылку <a href="...">[n]</a>.
    Подход:
      1) помечаем [n] токенами @@REF_n@@
      2) экранируем весь текст
      3) подставляем <a> для токенов

    Args:
        text: Текст с [n]
        url_by_index: словарь n->url

    Returns:
        HTML-ready строка (безопасно экранированная, только <a> оставлены).
    """
    if not text:
        return ""
    def mark(m):
        return f"@@REF_{m.group(1)}@@"
    marked = REF_MARK_RE.sub(mark, text)
    escaped = html.escape(marked, quote=False)
    def replace_token(m):
        n = int(m.group(1))
        url = url_by_index.get(n)
        if not url:
            return f"[{n}]"
        url_esc = html.escape(url, quote=True)
        return f'<a href="{url_esc}">[{n}]</a>'
    return re.sub(r"@@REF_(\d+)@@", replace_token, escaped)

