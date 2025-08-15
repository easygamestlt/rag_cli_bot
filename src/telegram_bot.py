"""Telegram bot: принимает сообщение, делает retrieval -> generation -> отвечает в HTML."""

from .retriever import retrieve_from_qdrant
from .generator import generate_answer
from .config import TOP_K
import telebot

def run_bot(collection_name: str, telegram_token: str):
    """
    Запускает телеграм-бота с parse_mode="HTML".

    Args:
        collection_name: коллекция Qdrant
        telegram_token: токен бота
    """
    bot = telebot.TeleBot(telegram_token, parse_mode="HTML", threaded=True)

    @bot.message_handler(commands=["start", "help"])
    def welcome(msg):
        bot.reply_to(msg, "Привет! Я RAG-бот (Qdrant + Ollama). Пришли вопрос — отвечу кратко и добавлю источники.")

    @bot.message_handler(func=lambda m: True)
    def handle(msg):
        q = msg.text.strip()
        if not q:
            bot.reply_to(msg, "Пустой запрос.")
            return
        try:
            retrieved = retrieve_from_qdrant(q, collection_name, top_k=TOP_K)
            if not retrieved:
                bot.reply_to(msg, "Ничего не найдено в индексе.")
                return
            answer_html = generate_answer(q, retrieved)
            # Разделяем, если очень длинно
            if len(answer_html) <= 4000:
                bot.reply_to(msg, answer_html)
            else:
                # разбиение по строкам (наивно)
                parts = []
                cur = []
                cur_len = 0
                for line in answer_html.split("\n"):
                    if cur_len + len(line) + 1 > 3800:
                        parts.append("\n".join(cur))
                        cur = [line]
                        cur_len = len(line) + 1
                    else:
                        cur.append(line)
                        cur_len += len(line) + 1
                if cur:
                    parts.append("\n".join(cur))
                for p in parts:
                    bot.reply_to(msg, p)
        except Exception as e:
            bot.reply_to(msg, f"Ошибка: {e}")

    print("[bot] Running. Ctrl+C to stop.")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("[bot] stopped")
