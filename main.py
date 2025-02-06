import logging
import os
import requests
import asyncio
import json  # Добавим поддержку работы с JSON
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ParseMode

# Получаем токен и ссылку на Google Apps Script из переменных окружения
API_TOKEN = '1828791789:AAGgt8DHZVJoiabooHwswxQ2Yl-lEybV5Y8'
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
        data = {
            "user": message.from_user.username,  # Имя пользователя
            "hours": hours,  # Часы
            "message": ""  # Пустое сообщение, так как это цифры
        }
    else:  # Если это текст (например, комментарий)
        comment = text
        data = {
            "user": message.from_user.username,  # Имя пользователя
            "hours": 0,  # Часы равны 0
            "message": comment  # Сообщение
        }
    
    try:
        # Отправляем данные на Google Apps Script в формате JSON
        response = requests.post(WEB_APP_URL, json=data)
        response.raise_for_status()  # Проверяем, что запрос прошел успешно
        await message.reply(f"Ваши данные сохранены!")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при отправке данных в Google Apps Script: {e}")
        await message.reply("Произошла ошибка при сохранении данных.")

# Запуск бота
if __name__ == '__main__':
    # Проверка, если приложение работает в правильном потоке с активным loop
    loop = asyncio.get_event_loop()  # Получаем текущий event loop
    loop.run_until_complete(executor.start_polling(dp, skip_updates=True))  # Запускаем polling