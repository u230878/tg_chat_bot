import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import re

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from openai import OpenAI

from matcher import IntentMatcher

load_dotenv()

# Настройки
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "Помогай клиентам спортивной розницы кратко и по делу.")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
SYSTEM_PROMPT = 'Помогай клиентам спортивной розницы кратко и по делу.'

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
)
logger = logging.getLogger("sportmaster-tg-gpt-bot")

# Инициализация GPT клиента (если ключ задан)
gpt_client = None
if OPENAI_API_KEY:
    try:
        gpt_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI клиент инициализирован успешно")
    except Exception as e:
        logger.error("Ошибка инициализации OpenAI клиента: %s", e)
        gpt_client = None
else:
    logger.warning("OPENAI_API_KEY не задан — GPT-ответы будут недоступны.")

# Загрузка интентов
matcher = IntentMatcher.from_yaml("intents.yaml")

MAIN_MENU = ReplyKeyboardMarkup(
    [["Магазины", "Доставка"], ["Возврат", "Клуб"], ["Сервис", "Статус заказа"], ["Помощь"]],
    resize_keyboard=True,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Чат-бот «СПОРТМАСТЕР». Сначала отвечаю по ключевым словам, затем — GPT при необходимости."
        "Темы: магазины, доставка, возврат, клуб, сервис, заказ."
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Напишите коротко тему: магазины, доставка, возврат, клуб, сервис, заказ.",
        reply_markup=MAIN_MENU,
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    user_id = update.effective_user.id if update.effective_user else "-"
    logger.info("Message from %s: %s", user_id, text)

    # 1) Пытаемся ответить по интентам
    quick = matcher.match(text)
    if quick and quick != matcher.fallback:
        # Спец-дополнение для статуса заказа
        if "заказ" in text.lower() or "статус" in text.lower():
            quick += "\n\nПодсказка: отправьте последние 4 цифры номера заказа."
        await update.message.reply_text(quick, reply_markup=MAIN_MENU)
        return

    # 2) GPT-ответ (если доступен)
    if gpt_client:
        try:
            completion = gpt_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=TEMPERATURE,
            )
            answer = completion.choices[0].message.content
            await update.message.reply_text(answer or matcher.fallback, reply_markup=MAIN_MENU)
            return
        except Exception as e:
            logger.exception("Ошибка GPT: %s", e)
            await update.message.reply_text("Временно не могу ответить через GPT.", reply_markup=MAIN_MENU)
            return

    # 3) Фолбэк, если GPT недоступен
    await update.message.reply_text(matcher.fallback, reply_markup=MAIN_MENU)

def main() -> None:
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Не задан TELEGRAM_TOKEN в окружении.")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Бот запущен.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()