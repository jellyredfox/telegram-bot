import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
import requests

# Получаем токен и URL из переменных окружения
TOKEN = os.getenv("TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL")

# Проверка, если токен или URL пустые
if not TOKEN or not WEB_APP_URL:
    raise ValueError("TOKEN или WEB_APP_URL не установлены!")

# Создание экземпляра бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я бот для учета часов. Просто напиши количество отработанных часов.")

# Обработчик текста (количество часов)
@dp.message_handler()
async def record_hours(message: types.Message):
    try:
        hours = int(message.text.strip())  # Преобразуем сообщение в целое число (часы)
        if hours < 0:
            raise ValueError("Количество часов не может быть отрицательным.")

        # Отправляем данные в Google Sheets через Apps Script
        payload = {
            "hours": hours,
            "user": message.from_user.full_name,
            "chat_id": message.from_user.id
        }

        response = requests.post(WEB_APP_URL, json=payload)

        if response.status_code == 200:
            await message.reply(f"Записано {hours} часов!")
        else:
            await message.reply("Не удалось записать данные. Попробуйте позже.")
    
    except ValueError:
        await message.reply("Пожалуйста, отправьте количество часов в виде числа.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
