import logging
import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ParseMode

# Получаем токен и ссылку на Google Apps Script из переменных окружения
TOKEN = '1828791789:AAHvMA095PX9LPWNyVwcPzOJkGTvBDgx8GY'
WEB_APP_URL = 'https://script.google.com/macros/s/AKfycbxCwMASb2tiVt_YZus07sgRIz7hpXE7d8KfBbanNr21JPDZayAoxyE7DZfx4JNCVELxOQ/exec'

# Проверка, что токен был передан
if not API_TOKEN or not WEB_APP_URL:
    raise ValueError("Не указан токен или URL для Google Apps Script!")

# Настроим логирование
logging.basicConfig(level=logging.INFO)

# Создаем бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Команда /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне количество отработанных часов или сообщение, и я занесу это в таблицу.")

# Обработка всех текстовых сообщений
@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_message(message: types.Message):
    text = message.text.strip()
    
    if text.isdigit():  # Если сообщение состоит только из цифр (например, количество часов)
        hours = int(text)  # Преобразуем в число
        try:
            # Отправляем данные на Google Apps Script
            response = requests.post(WEB_APP_URL, data={"hours": hours, "comment": ""})
            response.raise_for_status()  # Проверяем, что запрос прошел успешно
            await message.reply(f"Вы указали {hours} часов. Информация сохранена!")
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при отправке данных в Google Apps Script: {e}")
            await message.reply("Произошла ошибка при сохранении данных.")
    else:  # Если это текст (например, комментарий)
        comment = text
        try:
            # Отправляем данные на Google Apps Script
            response = requests.post(WEB_APP_URL, data={"hours": 0, "comment": comment})
            response.raise_for_status()  # Проверяем, что запрос прошел успешно
            await message.reply(f"Комментарий: '{comment}' сохранен!")
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при отправке данных в Google Apps Script: {e}")
            await message.reply("Произошла ошибка при сохранении данных.")

# Запуск бота
if __name__ == '__main__':
    # Проверка, если приложение работает в правильном потоке с активным loop
    loop = asyncio.get_event_loop()  # Получаем текущий event loop
    loop.run_until_complete(executor.start_polling(dp, skip_updates=True))  # Запускаем polling

