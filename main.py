import logging
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = "1828791789:AAGgt8DHZVJoiabooHwswxQ2Yl-lEybV5Y8"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxYXaNP8jPfY82Xju1hYehFtAN1rn3BktRILTHKnBOKYfB8SURVK0_UMyTkxvaQvmkNnQ/exec"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply(
        "Привет!\n"
        "Отправь мне количество часов и описание работы в формате: 3, установка розеток\n"
        "Или введи команду 'мои часы', чтобы узнать, сколько часов ты отработал за текущий спринт."
    )

# Обработчик команды "мои часы"
@dp.message_handler(lambda message: message.text.strip().lower() == "мои часы")
async def handle_my_hours(message: types.Message):
    # Получаем имя пользователя
    user_name = message.from_user.first_name if message.from_user and message.from_user.first_name else "Неизвестный пользователь"
    try:
        # Отправляем GET-запрос с параметрами action=getHours и user=<имя пользователя>
        params = {"action": "getHours", "user": user_name}
        logging.info(f"Запрос к Google Apps Script для получения часов пользователя {user_name}. Параметры: {params}")
        response = requests.get(WEB_APP_URL, params=params)
        response.raise_for_status()  # Проверка успешного запроса
        data = response.json()  # Ожидается JSON, например: {"hours": 15}
        total_hours = data.get("hours", 0)
        await message.reply(f"✅ {user_name}, отработано часов в текущем спринте: {total_hours}")
    except Exception as e:
        logging.error(f"Ошибка получения данных из Google Apps Script: {e}")
        await message.reply("❌ Ошибка при получении данных. Попробуйте позже.")


@dp.message_handler(lambda message: message.text.strip().lower() in ["отчет", "/отчет"])
async def handle_report(message: types.Message):
    try:
        response = requests.get(WEB_APP_URL, params={"action": "sprintReport"})
        response.raise_for_status()
        await message.reply(response.text)
    except Exception as e:
        logging.error(f"Ошибка получения отчёта: {e}")
        await message.reply("❌ Не удалось получить отчёт.")
       

# Обработчик сообщений с данными о часах и работе (POST-запись)
@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_message(message: types.Message):
    text = message.text.strip()

    # Если сообщение совпадает с командой "мои часы", то данный обработчик уже сработал
    if text.lower() == "мои часы":
        return

    # Логируем объект сообщения для диагностики
    logging.info(f"Получено сообщение: {message}")
    logging.info(f"Сообщение имеет структуру: {message.to_python()}")

    # Получаем имя пользователя
    user_name = message.from_user.first_name if message.from_user and message.from_user.first_name else "Неизвестный пользователь"
    logging.info(f"Имя пользователя: {user_name}")

    # Проверка формата сообщения: ожидается наличие запятой
    if "," not in text:
        await message.reply("⚠️ Пожалуйста, отправь данные в формате: 3, установка розеток")
        return

    parts = text.split(",", 1)  # Разделяем по первой запятой
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

    try:
        # Отправляем данные на Google Apps Script (POST-запрос)
        logging.info(f"Отправляем данные: hours={hours}, comment={comment}, user={user_name}")
        response = requests.post(WEB_APP_URL, json={
            "hours": hours,
            "comment": comment,
            "user": user_name
        })
        response.raise_for_status()  # Проверяем, что запрос прошел успешно
        await message.reply(f"✅ Записано: {hours} часов. Комментарий: {comment}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при отправке данных в Google Apps Script: {e}")
        await message.reply("❌ Ошибка при сохранении данных.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
