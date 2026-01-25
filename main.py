import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import os
import re
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_TOKEN = TOKEN

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzWBw4DZ9cqTIHvZIxG4DYbJoWHCaYjS6djtNp3KW1gGu729CHNjXP6y9HbV6LSZ5p5_A/exec"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def extract_spreadsheet_id(text: str) -> str | None:
    """
    Accepts either:
    - spreadsheet id directly
    - google sheets url
    Returns spreadsheet_id or None
    """
    t = text.strip()

    # If it's a URL like https://docs.google.com/spreadsheets/d/<ID>/edit...
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", t)
    if m:
        return m.group(1)

    # If it's already an ID (usually long, contains letters/digits/-/_)
    # We keep it permissive but require length to avoid accidental matches.
    if re.fullmatch(r"[a-zA-Z0-9-_]{25,}", t):
        return t

    return None


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply(
        "Отправь количество часов и описание в формате:\n"
        "3, установка розеток\n\n"
        "Команды:\n"
        "- мои часы\n"
        "- /все\n"
        "- /отчет\n"
        "- /bind <ID или ссылка на таблицу>\n"
        "- /where"
    )


@dp.message_handler(commands=['bind'])
async def handle_bind(message: types.Message):
    """
    Bind current chat to a spreadsheet.
    Usage:
      /bind <spreadsheet_id>
      /bind <google sheets url>
    """
    chat_id = message.chat.id
    args = message.get_args().strip()

    if not args:
        await message.reply("⚠️ Использование: /bind <ID таблицы или ссылка Google Sheets>")
        return

    spreadsheet_id = extract_spreadsheet_id(args)
    if not spreadsheet_id:
        await message.reply("⚠️ Не понял ID таблицы. Пришли ID или ссылку вида https://docs.google.com/spreadsheets/d/<ID>/edit")
        return

    try:
        params = {
            "action": "bind",
            "chat_id": str(chat_id),
            "spreadsheet_id": spreadsheet_id,
            "name": message.chat.title or ""
        }
        logging.info(f"Bind chat_id={chat_id} to spreadsheet_id={spreadsheet_id}")
        response = requests.get(WEB_APP_URL, params=params, timeout=20)
        response.raise_for_status()
        await message.reply("✅ Чат привязан к таблице. Теперь записи из этого чата будут идти в неё.")
    except Exception as e:
        logging.error(f"Ошибка bind: {e}")
        await message.reply("❌ Не удалось привязать таблицу. Проверь, что Web App обновлён и доступ открыт.")


@dp.message_handler(commands=['where'])
async def handle_where(message: types.Message):
    chat_id = message.chat.id
    try:
        params = {"action": "where", "chat_id": str(chat_id)}
        response = requests.get(WEB_APP_URL, params=params, timeout=20)
        response.raise_for_status()
        await message.reply(f"ℹ️ {response.text}")
    except Exception as e:
        logging.error(f"Ошибка where: {e}")
        await message.reply("❌ Не удалось получить привязку.")


@dp.message_handler(lambda message: message.text and message.text.strip().lower() == "мои часы")
async def handle_my_hours(message: types.Message):
    user_name = message.from_user.first_name if message.from_user and message.from_user.first_name else "Неизвестный пользователь"
    chat_id = message.chat.id

    try:
        params = {"action": "getHours", "user": user_name, "chat_id": str(chat_id)}
        logging.info(f"GET getHours user={user_name} chat_id={chat_id}")
        response = requests.get(WEB_APP_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        total_hours = data.get("hours", 0)
        await message.reply(f"✅ {user_name}, часов в текущем спринте: {total_hours}")
    except Exception as e:
        logging.error(f"Ошибка получения часов: {e}")
        await message.reply("❌ Ошибка при получении данных. Попробуйте позже.")


@dp.message_handler(lambda message: message.text and message.text.strip().lower() in ["все часы", "/все"])
async def handle_all_hours(message: types.Message):
    chat_id = message.chat.id
    try:
        params = {"action": "allHours", "chat_id": str(chat_id)}
        response = requests.get(WEB_APP_URL, params=params, timeout=20)
        response.raise_for_status()
        await message.reply(response.text)
    except Exception as e:
        logging.error(f"Ошибка получения всех часов: {e}")
        await message.reply("❌ Не удалось получить данные за всё время.")


@dp.message_handler(lambda message: message.text and message.text.strip().lower() in ["отчет", "/отчет"])
async def handle_report(message: types.Message):
    chat_id = message.chat.id
    try:
        params = {"action": "sprintReport", "chat_id": str(chat_id)}
        response = requests.get(WEB_APP_URL, params=params, timeout=20)
        response.raise_for_status()
        await message.reply(response.text)
    except Exception as e:
        logging.error(f"Ошибка получения отчёта: {e}")
        await message.reply("❌ Не удалось получить отчёт.")


@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_message(message: types.Message):
    text = message.text.strip()
    if not text:
        return

    # Skip commands (so /bind, /where etc. don't fall here)
    if text.startswith("/"):
        return

    # If message is "мои часы" it is already handled
    if text.lower() == "мои часы":
        return

    user_name = message.from_user.first_name if message.from_user and message.from_user.first_name else "Неизвестный пользователь"
    chat_id = message.chat.id

    if "," not in text:
        await message.reply("⚠️ Формат: 3, установка розеток")
        return

    hours_part, comment = text.split(",", 1)
    hours_part = hours_part.strip()
    comment = comment.strip()

    # Allow 1.5 hours? If you want only integers, keep isdigit check.
    if not hours_part.isdigit():
        await message.reply("⚠️ Первым должно быть число часов, например: 3, укладка плитки")
        return

    hours = int(hours_part)

    if not comment:
        await message.reply("⚠️ После запятой добавь описание работы, например: 3, укладка плитки")
        return

    try:
        payload = {
            "hours": hours,
            "comment": comment,
            "user": user_name,
            "chat_id": str(chat_id)
        }
        logging.info(f"POST add hours={hours} user={user_name} chat_id={chat_id}")
        response = requests.post(WEB_APP_URL, json=payload, timeout=20)
        response.raise_for_status()
        await message.reply(f"✅ Записано: {hours} часов. Комментарий: {comment}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка POST: {e}")
        await message.reply("❌ Ошибка при сохранении данных.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
