import logging
import json
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = Path("data.json")
if not DATA_FILE.exists():
    DATA_FILE.write_text(json.dumps({}))

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
logging.basicConfig(level=logging.INFO)

class Form(StatesGroup):
    waiting_for_comment = State()

# Загружаем данные
def load_data():
    return json.loads(DATA_FILE.read_text())

# Сохраняем данные
def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2))

# Получить клавиатуру меню
def get_main_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить тренировку", callback_data="add_training")
    kb.button(text="📅 Следующая тренировка", callback_data="next_training")
    kb.button(text="📊 Статистика", callback_data="stats")
    kb.adjust(1)
    return kb.as_markup()

# Получить статус
def get_status(user_id):
    data = load_data()
    user = data.get(str(user_id), {})
    status = f"🎯 Цель: {user.get('goal', 'не задана')}\n"
    status += f"📈 Тренировок: {len(user.get('trainings', []))}\n"
    status += f"📅 Следующая: {user.get('next', 'не запланирована')}\n"
    status += f"💬 Последний коммент: {user.get('last_comment', '—')}"
    return status

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    kb = get_main_keyboard()
    await message.answer(f"Привет, {message.from_user.first_name}!\n\nВот твой статус:\n\n{get_status(message.from_user.id)}", reply_markup=kb)
    await state.clear()

@dp.callback_query(F.data == "add_training")
async def add_training(callback, state: FSMContext):
    data = load_data()
    user_id = str(callback.from_user.id)
    user = data.setdefault(user_id, {"trainings": []})
    user["trainings"].append("✅")
    save_data(data)

    await callback.message.edit_text("Тренировка добавлена ✅\n\nНапиши кратко, как она прошла:", reply_markup=None)
    await state.set_state(Form.waiting_for_comment)
    await callback.answer()

@dp.message(Form.waiting_for_comment)
async def save_comment(message: Message, state: FSMContext):
    data = load_data()
    user_id = str(message.from_user.id)
    comment = message.text
    data.setdefault(user_id, {})["last_comment"] = comment
    save_data(data)

    await message.answer(f"Комментарий сохранён ✅\n\nОбновлённый статус:\n\n{get_status(user_id)}", reply_markup=get_main_keyboard())
    await state.clear()

@dp.callback_query(F.data == "next_training")
async def set_next(callback, state: FSMContext):
    await callback.message.edit_text("Напиши дату следующей тренировки (например, 15 июня):")
    await state.set_state("waiting_for_date")
    await callback.answer()

@dp.message(F.state == "waiting_for_date")
async def save_date(message: Message, state: FSMContext):
    data = load_data()
    user_id = str(message.from_user.id)
    data.setdefault(user_id, {})["next"] = message.text
    save_data(data)

    await message.answer(f"Дата сохранена ✅\n\nОбновлённый статус:\n\n{get_status(user_id)}", reply_markup=get_main_keyboard())
    await state.clear()

@dp.callback_query(F.data == "stats")
async def show_stats(callback, state: FSMContext):
    await callback.message.edit_text(f"📊 Твоя статистика:\n\n{get_status(callback.from_user.id)}", reply_markup=get_main_keyboard())
    await callback.answer()

@dp.message(Command("reset"))
async def reset_user(message: Message, state: FSMContext):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id in data:
        del data[user_id]
        save_data(data)
    await message.answer("Данные сброшены ❌", reply_markup=get_main_keyboard())
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
