import os
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

import yaml
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Загрузка токена из переменных окружения
try:
    from dotenv import load_dotenv  # опционально, если пользователь установит python-dotenv
    load_dotenv()
except Exception:
    pass

TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
)
logger = logging.getLogger("sportmaster-bot")

@dataclass
class Intent:
    name: str
    keywords: List[str]
    reply: str

class IntentMatcher:
    def __init__(self, intents: List[Intent], fallback: str):
        self.intents = intents
        self.fallback = fallback

    def match(self, text: str) -> str:
        t = (text or "").lower()
        # Простое правило: наличие любого ключевого слова в тексте сообщения
        for intent in self.intents:
            for kw in intent.keywords:
                if kw in t:
                    return intent.reply
        return self.fallback

def load_intents(file_path: str) -> IntentMatcher:
    data = yaml.safe_load(Path(file_path).read_text(encoding="utf-8"))
    intents = [
        Intent(name=i["name"], keywords=i["keywords"], reply=i["reply"])
        for i in data.get("intents", [])
    ]
    fallback = data.get("fallback", "Запрос не распознан.")
    return IntentMatcher(intents, fallback)

matcher = load_intents("intents.yaml")

MAIN_MENU = ReplyKeyboardMarkup(
    [["Магазины", "Доставка"], ["Возврат", "Клуб"], ["Сервис", "Статус заказа"], ["Помощь"]],
    resize_keyboard=True,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = (
        "Чат-бот ООО «СПОРТМАСТЕР» на ключевых словах. "
        "Доступные темы: магазины, доставка, возврат, клуб, сервис, заказ."
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Напишите коротко тему: магазины, доставка, возврат, клуб, сервис, заказ.",
        reply_markup=MAIN_MENU,
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    reply = matcher.match(text)
    # Спец-кейс: запрос «статус заказа» — подсказка на форму
    if "статус" in text.lower() or "заказ" in text.lower():
        reply += "\n\nПодсказка: отправьте последние 4 цифры номера заказа одним сообщением."
    await update.message.reply_text(reply, reply_markup=MAIN_MENU)

def main() -> None:
    if not TOKEN:
        raise RuntimeError("Не задан TELEGRAM_TOKEN в переменных окружения")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("Бот запущен.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()