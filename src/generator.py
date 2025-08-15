"""Генерация ответа через Ollama: формирование промпта, очистка вывода и форматирование."""

from typing import List, Tuple, Dict
import ollama
from .config import GEN_MODEL, TOP_K
from .utils import clean_model_output, enforce_three_sentences, linkify_refs

SYSTEM_PROMPT = (
    "Ты — помощник по данным. Отвечай кратко, на русском. "
    "Используй только факты из предоставленного контекста. Если контекст не содержит ответа, честно скажи об этом."
)

def format_context_for_prompt(retrieved: List[Tuple[float, object]]) -> str:
    """
    Формирует контекст для пользователя, проставляя номера источников [n] перед фрагментами.

    Args:
        retrieved: список (score, ChunkMeta)

    Returns:
        Текст контекста (строка).
    """
    lines = []
    # Соберём уникальные URL и нумерацию вне этой функции (в generate_answer)
    for score, ch in retrieved:
        lines.append(f"[source: {ch.url}#chunk-{ch.chunk_id}]\n{ch.text}\n")
    return "\n\n".join(lines)[:6000]

def generate_answer(question: str, retrieved: List[Tuple[float, object]]) -> str:
    """
    Генерирует ответ на вопрос используя retrieved фрагменты.
    Возвращает HTML-ready строку (с кликабельными [n]) — готовую для отправки в Telegram parse_mode="HTML".

    Args:
        question: вопрос пользователя
        retrieved: список (score, ChunkMeta)

    Returns:
        HTML строка ответа.
    """
    # Собираем уникальные URL -> индексы
    urls = []
    seen = set()
    for _, ch in retrieved:
        if ch.url not in seen:
            seen.add(ch.url)
            urls.append(ch.url)
    index_of = {u: i+1 for i, u in enumerate(urls)}
    url_by_index = {i+1: u for i, u in enumerate(urls)}

    # Контекст (с номерами) для промпта
    ctx_lines = []
    for score, ch in retrieved:
        n = index_of[ch.url]
        ctx_lines.append(f"[{n}] {ch.text}\n")
    context = "\n".join(ctx_lines)[:6000]

    # Подготовка пользовательского промпта
    user_prompt =  (
        f"""
        Ты профессиональный продавец-консультант компании. Отвечай ТОЛЬКО на основе предоставленного контекста. 
        Если информации недостаточно – вежливо откажись отвечать. Сохраняй дружелюбный и уверенный тон.

        **Роль:**
        - Эксперт по продуктам/услугам компании
        - Мастер вежливого общения
        - Специалист по решению проблем клиентов

        **Инструкции:**
        1. Анализируй контекст из базы знаний:(фрагменты, каждый пронумерован квадратной ссылкой) <CONTEXT_START>{context}<CONTEXT_END>
        2. Отвечай максимально конкретно на вопрос: {question}
        3. Если в контексте нет ответа: "Извините, эта информация временно недоступна. Уточните детали у менеджера"
        4. Для сложных вопросов разбивай ответ на пункты
        5. Избегай технического жаргона
        6. Ставь числовые ссылки [n] сразу после утверждений, на которые есть опора в соответствующем фрагменте
        7. Не придумывай новых источников и не меняй номера 

        **Стиль ответа:**
        - Используй эмоджи для эмоциональной окраски (1-2 в сообщении)
        - Подчеркивай выгоды клиента
        - Предлагай дополнительные варианты: "Возможно вас также заинтересует..."
        - Завершай вопросом: "Хотите уточнить какие-то детали?"

        **Пример ответа:**
        "Добрый день! <основной ответ из контекста>. 
        Нужны дополнительные подробности? 😊"

        **Технические примечания:**
        - Контекст обрезан до 512 токенов
        - Избегай markdown-разметки
        - Ответ держи в пределах 3 предложений
        """
    )

    resp = ollama.chat(
        model=GEN_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0.2},
    )

    text = resp["message"]["content"]
    text = clean_model_output(text)
    html_ready = linkify_refs(text, url_by_index)
    return html_ready
