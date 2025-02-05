import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
WEB_APP_URL = "YOUR_APPS_SCRIPT_URL"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply("Привет! Отправь мне количество отработанных часов.")

@dp.message_handler()
async def log_hours(message: types.Message):
    try:
        parts = message.text.split()
        hours = float(parts[0])  # Берём первое слово как число часов
        note = " ".join(parts[1:]) if len(parts) > 1 else "Без комментариев"

        data = {
            "user": message.from_user.full_name,
            "hours": hours,
            "message": note
        }

        response = requests.post(WEB_APP_URL, json=data)
        
        if response.text.strip() == "OK":
            await message.reply(f"✅ Записал {hours} часов в таблицу.")
        else:
            await message.reply("❌ Ошибка при записи данных.")
    
    except Exception as e:
        await message.reply(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    executor.start_polling(dp)
