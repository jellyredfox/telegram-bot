import logging
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import User

API_TOKEN = "1828791789:AAGgt8DHZVJoiabooHwswxQ2Yl-lEybV5Y8"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxzq9EdmcCl48qOn6j1lF5Qdin1D6S3yoPML9ExD8526782glFPpq7zCwUcA3hbFmq7Uw/exec"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне количество часов и описание работы в формате: 3, установка розеток")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_message(message: types.Message):
    text = message.text.strip()

    # Проверяем, есть ли запятая
    if "," not in text:
        await message.reply("⚠️ Пожалуйста, отправь данные в формате: 3, установка розеток")
        return

    parts = text.split(",", 1)  # Разделяем по первому вхождению запятой
    hours_part = parts[0].strip()
    comment = parts[1].strip() if len(parts) > 1 else ""

    # Проверяем, что первая часть — число
    if not hours_part.isdigit():
        await message.reply("⚠️ Первым должно быть указано число (количество часов), например: 3, укладка плитки")
        return

    hours = int(hours_part)

    # Проверяем, что комментарий не пустой
    if not comment:
        await message.reply("⚠️ После запятой добавьте описание работы, например: 3, укладка плитки")
        return

    # Получаем имя пользователя
    user_name = message.from_.first_name
    if message.from_.last_name:
        user_name += f" {message.from_.last_name}"

    try:
        # Отправляем данные на Google Apps Script
        response = requests.post(WEB_APP_URL, json={
            "hours": hours,
            "comment": comment,
            "user": user_name  # Добавляем имя пользователя
        })
        response.raise_for_status()  # Проверяем, что запрос прошел успешно
        await message.reply(f"✅ Записано: {hours} часов. Комментарий: {comment}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при отправке данных в Google Apps Script: {e}")
        await message.reply("❌ Ошибка при сохранении данных.")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(executor.start_polling(dp, skip_updates=True))
