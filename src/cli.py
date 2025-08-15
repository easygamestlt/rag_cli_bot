"""CLI-обёртка для индексации и запуска бота."""

import argparse
import sys
from pathlib import Path
from .indexer import build_index_from_urls
from .telegram_bot import run_bot
from .config import CHUNK_SIZE, CHUNK_OVERLAP

def main():
    parser = argparse.ArgumentParser(description="RAG + Qdrant + Ollama")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_index = sub.add_parser("index")
    p_index.add_argument("urls_file", type=Path)
    p_index.add_argument("--collection", type=str, default="rag_collection")
    p_index.add_argument("--batch-size", type=int, default=64)
    p_index.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    p_index.add_argument("--chunk-overlap", type=int, default=CHUNK_OVERLAP)

    p_bot = sub.add_parser("bot")
    p_bot.add_argument("--collection", type=str, default="rag_collection")
    p_bot.add_argument("--telegram-token", type=str, required=True)

    args = parser.parse_args()
    if args.cmd == "index":
        if not args.urls_file.exists():
            print("URLs file not found.")
            sys.exit(1)
        urls = [line.strip() for line in args.urls_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        build_index_from_urls(urls, args.collection, args.batch_size, args.chunk_size, args.chunk_overlap)
    elif args.cmd == "bot":
        run_bot(args.collection, args.telegram_token)

if __name__ == "__main__":
    main()
