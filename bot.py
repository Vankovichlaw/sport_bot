import os
import json
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Путь к файлу базы данных
DB_FILE = "database.json"

# Загрузка данных из файла
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

# Сохранение данных в файл
def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Получение данных пользователя
def get_user_data(user_id):
    data = load_data()
    if str(user_id) not in data:
        data[str(user_id)] = {
            "goal": 0,
            "done": 0,
            "next_training": "не запланирована",
            "last_training": "нет данных",
            "comment": "",
            "rewards": [],
            "sport": "не выбран"
        }
    return data

# Обновление данных пользователя
def update_user_data(user_id, new_info):
    data = get_user_data(user_id)
    data[str(user_id)].update(new_info)
    save_data(data)

# Форматирование статуса пользователя
def format_status(user_id):
    data = get_user_data(user_id)[str(user_id)]
    goal = data["goal"]
    done = data["done"]
    reward = "🏅" if done >= goal and goal > 0 else ""
    return (
        f"<b>🎯 Цель месяца:</b> {done}/{goal} тренировок {reward}\n"
        f"<b>📅 Следующая тренировка:</b> {data['next_training']}\n"
        f"<b>🏋️‍♂️ Последняя тренировка:</b> {data['last_training']}\n"
        f"<b>🏃‍♂️ Вид спорта:</b> {data['sport']}\n"
        f"<b>💬 Комментарий:</b> {data['comment']}"
    )

# Главное меню
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить тренировку"), KeyboardButton(text="✅ Закончить тренировку")],
        [KeyboardButton(text="🎯 Установить цель"), KeyboardButton(text="📅 Запланировать тренировку")],
        [KeyboardButton(text="⚙️ Выбрать спорт"), KeyboardButton(text="🔁 Сбросить всё")],
        [KeyboardButton(text="📊 Мой прогресс")]
    ],
    resize_keyboard=True
)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "<b>Привет! Я спортивный бот 💪</b>\n\n"
        "Вот что я умею:\n"
        "➕ Добавлять тренировки\n"
        "✅ Отмечать завершение\n"
        "🎯 Ставить цель на месяц\n"
        "📅 Планировать следующую тренировку\n"
        "⚙️ Выбирать вид спорта\n"
        "🔁 Сбрасывать прогресс\n"
        "📊 Показывать текущий статус\n\n"
        "Выбери команду ниже:",
        reply_markup=main_kb
    )

# Установка цели
@dp.message(F.text == "🎯 Установить цель")
async def set_goal(message: Message):
    await message.answer("Введите цель: сколько тренировок вы хотите сделать в этом месяце?")
    dp.message.register_once(set_goal_value)

async def set_goal_value(message: Message):
    try:
        goal = int(message.text)
        update_user_data(message.from_user.id, {"goal": goal})
        await message.answer("Цель сохранена ✅\n\n" + format_status(message.from_user.id))
    except ValueError:
        await message.answer("Введите число.")

# Планирование тренировки
@dp.message(F.text == "📅 Запланировать тренировку")
async def plan_next(message: Message):
    await message.answer("Введите дату следующей тренировки (например, 20 июня):")
    dp.message.register_once(save_next_training)

async def save_next_training(message: Message):
    update_user_data(message.from_user.id, {"next_training": message.text})
    await message.answer("Запланировано 📅\n\n" + format_status(message.from_user.id))

# Добавление тренировки
@dp.message(F.text == "➕ Добавить тренировку")
async def add_training(message: Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    data[str(user_id)]["done"] += 1
    save_data(data)
    await message.answer("Тренировка добавлена 💪\nНапиши, как прошла:")
    dp.message.register_once(save_comment)

async def save_comment(message: Message):
    update_user_data(message.from_user.id, {
        "comment": message.text,
        "last_training": datetime.now().strftime("%d %B %Y")
    })
    await message.answer("Комментарий сохранён 📝\n\n" + format_status(message.from_user.id))

# Завершение тренировки
@dp.message(F.text == "✅ Закончить тренировку")
async def finish_training(message: Message):
    await message.answer("Хорошая работа! 💥\n\n" + format_status(message.from_user.id))

# Выбор вида спорта
@dp.message(F.text == "⚙️ Выбрать спорт")
async def choose_sport(message: Message):
    await message.answer("Какой вид спорта? (Например: бег, йога, зал)")
    dp.message.register_once(save_sport)

async def save_sport(message: Message):
    update_user_data(message.from_user.id, {"sport": message.text})
    await message.answer("Вид спорта обновлён ✅\n\n" + format_status(message.from_user.id))

# Сброс данных
@dp.message(F.text == "🔁 Сбросить всё")
async def reset_user(message: Message):
    data = load_data()
    if str(message.from_user.id) in data:
        del data[str(message.from_user.id)]
        save_data(data)
    await message.answer("Данные сброшены 🔁")

# Показ прогресса
@dp.message(F.text == "📊 Мой прогресс")
async def show_progress(message: Message):
    await message.answer(format_status(message.from_user.id))

# Запуск
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
