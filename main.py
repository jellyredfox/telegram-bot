import logging
import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ParseMode
from datetime import datetime  # Для работы с датой

# Получаем токен и ссылку на Google Apps Script из переменных окружения
API_TOKEN = '1828791789:AAGgt8DHZVJoiabooHwswxQ2Yl-lEybV5Y8'
WEB_APP_URL = 'https://script.google.com/macros/s/AKfycbwR9lN2B_unWN_W6RTrn6JdPFpFMN0IWCH70GQ1dXutAbB4JEzK-wbr1VUHF_QKcCO0kw/exec'

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
    
    # Получаем текущую дату в формате день-месяц
    today = datetime.now().strftime("%d-%m")  # Форматируем как dd-mm
    
    # Пытаемся разделить сообщение на число (часы) и комментарий
    if ',' in text:
        try:
            # Разделяем по запятой
            hours, comment = text.split(',', 1)  # Берем только первый раздел, остальной текст — это комментарий
            hours = int(hours.strip())  # Преобразуем в число
            comment = comment.strip()  # Убираем лишние пробелы

            # Отправляем данные на Google Apps Script
            response = requests.post(WEB_APP_URL, data={"date": today, "hours": hours, "comment": comment})
            response.raise_for_status()  # Проверяем, что запрос прошел успешно

            await message.reply(f"Вы указали {hours} часов. Комментарий: '{comment}' на {today} сохранен!")
        except ValueError:
            await message.reply("Ошибка! Пожалуйста, отправьте сообщение в формате: 'Часы, Комментарий'.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при отправке данных в Google Apps Script: {e}")
            await message.reply("Произошла ошибка при сохранении данных.")
    else:
        # Если формат не соответствует, обработка только как комментарий или часов
        if text.isdigit():  # Если сообщение состоит только из цифр (например, количество часов)
            hours = int(text)  # Преобразуем в число
            try:
                response = requests.post(WEB_APP_URL, data={"date": today, "hours": hours, "comment": ""})
                response.raise_for_status()  # Проверяем, что запрос прошел успешно
                await message.reply(f"Вы указали {hours} часов на {today}. Информация сохранена!")
            except requests.exceptions.RequestException as e:
                logging.error(f"Ошибка при отправке данных в Google Apps Script: {e}")
                await message.reply("Произошла ошибка при сохранении данных.")
        else:  # Это просто текстовый комментарий
            comment = text
            try:
                response = requests.post(WEB_APP_URL, data={"date": today, "hours": 0, "comment": comment})
                response.raise_for_status()  # Проверяем, что запрос прошел успешно
                await message.reply(f"Комментарий: '{comment}' на {today} сохранен!")
            except requests.exceptions.RequestException as e:
                logging.error(f"Ошибка при отправке данных в Google Apps Script: {e}")
                await message.reply("Произошла ошибка при сохранении данных.")

# Запуск бота
if __name__ == '__main__':
    # Проверка, если приложение работает в правильном потоке с активным loop
    loop = asyncio.get_event_loop()  # Получаем текущий event loop
    loop.run_until_complete(executor.start_polling(dp, skip_updates=True))  # Запускаем polling
