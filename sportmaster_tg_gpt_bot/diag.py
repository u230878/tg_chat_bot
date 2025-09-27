import os, importlib, pkgutil, sys

print("Python:", sys.version)
print("sys.executable:", sys.executable)

# Проверка telegram
found = pkgutil.find_loader("telegram")
if not found:
    print("Модуль 'telegram' не найден — установите зависимости.")
    sys.exit(1)
mod = importlib.import_module("telegram")
print("telegram module path:", getattr(mod, "__file__", "?"))
try:
    from telegram import Update
    print("PTB OK: класс Update найден.")
except Exception as e:
    print("Проблема с импортом Update:", e)
    print("Удалите пакеты 'telegram', 'telebot', 'pyTelegramBotAPI' и установите 'python-telegram-bot'.")
    raise

# Проверка OpenAI
try:
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY")
    if key:
        client = OpenAI()
        print("GPT OK: клиент создан.")
    else:
        print("GPT предупреждение: OPENAI_API_KEY не задан.")
except Exception as e:
    print("Проблема с OpenAI клиентом:", e)
    raise