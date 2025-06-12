import asyncio
import os
import json
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from datetime import datetime, timedelta
from random import choice

# ✅ Получаем токен из переменных окружения
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения TOKEN не установлена!")

# ✅ Инициализация бота
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

DATA_FILE = "user_data.json"

# ============================ FSM ============================

class TrainingStates(StatesGroup):
    choosing_sport = State()
    setting_goal = State()
    setting_next_training = State()
    adding_comment = State()

# ============================ КНОПКИ ============================

main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="➕ Добавить тренировку")],
    [KeyboardButton(text="📅 Следующая тренировка"), KeyboardButton(text="📊 Статистика")],
    [KeyboardButton(text="🔄 Сбросить все данные")]
], resize_keyboard=True)

# ============================ ХРАНИЛИЩЕ ============================

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ============================ МОТИВАЦИЯ ============================

quotes = [
    "💪 Каждый шаг приближает тебя к цели!",
    "🔥 Сегодняшняя тренировка — вклад в завтрашнюю победу!",
    "🏆 Постоянство важнее мотивации!",
    "🚀 Не сдавайся, ты уже начал!",
    "⏱️ Лучшая тренировка — та, что сделана!"
]

# ============================ ОБНОВЛЕНИЕ СТАТУСА ============================

async def send_status(message: Message, user_data: dict):
    uid = str(message.from_user.id)
    u = user_data.get(uid, {})
    text = f"<b>🏋️ Текущий статус:</b>\n\n"
    text += f"🎯 Цель месяца: {u.get('goal', 'не указана')}\n"
    text += f"🏃‍♂️ Вид спорта: {u.get('sport', 'не выбран')}\n"
    text += f"📅 Следующая тренировка: {u.get('next_training', 'не запланирована')}\n"
    text += f"✅ Тренировок в этом месяце: {u.get('trainings', 0)}\n"
    text += f"🏅 Награды: {u.get('awards', 0)}\n"
    comment = u.get("last_comment")
    if comment:
        text += f"💬 Последний комментарий: {comment}\n"
    text += f"\n🧠 {choice(quotes)}"
    await message.answer(text, reply_markup=main_kb)

# ============================ ОБРАБОТЧИКИ ============================

@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await message.answer("👋 Привет! Я помогу тебе следить за тренировками.\n\nДавай начнём с создания профиля!")
    await message.answer("💬 Какой у тебя вид спорта? (Например: бег, йога, зал)")
    await state.set_state(TrainingStates.choosing_sport)

@dp.message(TrainingStates.choosing_sport)
async def choose_sport(message: Message, state: FSMContext):
    uid = str(message.from_user.id)
    data = load_data()
    data.setdefault(uid, {})["sport"] = message.text
    save_data(data)
    await message.answer("🎯 Укажи цель на этот месяц (например: 12 тренировок):")
    await state.set_state(TrainingStates.setting_goal)

@dp.message(TrainingStates.setting_goal)
async def set_goal(message: Message, state: FSMContext):
    uid = str(message.from_user.id)
    data = load_data()
    data.setdefault(uid, {})["goal"] = message.text
    data[uid]["trainings"] = 0
    data[uid]["awards"] = 0
    save_data(data)
    await message.answer("📅 Когда следующая тренировка? (например: 2025-06-15)")
    await state.set_state(TrainingStates.setting_next_training)

@dp.message(TrainingStates.setting_next_training)
async def set_next_training(message: Message, state: FSMContext):
    uid = str(message.from_user.id)
    data = load_data()
    data.setdefault(uid, {})["next_training"] = message.text
    save_data(data)
    await message.answer("✅ Профиль создан!")
    await send_status(message, data)
    await state.clear()

@dp.message(F.text == "➕ Добавить тренировку")
async def add_training(message: Message, state: FSMContext):
    uid = str(message.from_user.id)
    data = load_data()
    user = data.setdefault(uid, {})
    user["trainings"] = user.get("trainings", 0) + 1

    # Награда за каждые 5 тренировок
    if user["trainings"] % 5 == 0:
        user["awards"] = user.get("awards", 0) + 1
        await message.answer("🏅 Поздравляем! Ты получил награду за регулярность!")

    save_data(data)
    await message.answer("🗒️ Как прошла тренировка? Напиши короткий комментарий:")
    await state.set_state(TrainingStates.adding_comment)

@dp.message(TrainingStates.adding_comment)
async def add_comment(message: Message, state: FSMContext):
    uid = str(message.from_user.id)
    data = load_data()
    data.setdefault(uid, {})["last_comment"] = message.text
    save_data(data)
    await message.answer("✅ Спасибо за отзыв! Всё сохранено.")
    await send_status(message, data)
    await state.clear()

@dp.message(F.text == "📅 Следующая тренировка")
async def show_next(message: Message):
    uid = str(message.from_user.id)
    data = load_data()
    next_training = data.get(uid, {}).get("next_training", "не запланирована")
    await message.answer(f"📅 Следующая тренировка: <b>{next_training}</b>")

@dp.message(F.text == "📊 Статистика")
async def stats(message: Message):
    uid = str(message.from_user.id)
    data = load_data()
    u = data.get(uid, {})
    await message.answer(
        f"📊 <b>Твоя статистика:</b>\n"
        f"Тренировок в этом месяце: {u.get('trainings', 0)}\n"
        f"Цель: {u.get('goal', 'не указана')}\n"
        f"Награды: {u.get('awards', 0)}"
    )

@dp.message(F.text == "🔄 Сбросить все данные")
async def reset_data(message: Message):
    uid = str(message.from_user.id)
    data = load_data()
    if uid in data:
        del data[uid]
        save_data(data)
    await message.answer("♻️ Данные сброшены. Напиши /start чтобы начать заново.")

# ============================ ЗАПУСК ============================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
