import asyncio
import logging
import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv

# Загрузка токена
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

DB_FILE = "database.json"
def load_data():
    if os.path.exists(DB_FILE):
        return json.load(open(DB_FILE))
    return {}
def save_data(d): json.dump(d, open(DB_FILE, "w"), indent=2)
def get_u(uid):
    d = load_data()
    if str(uid) not in d:
        d[str(uid)] = {"goal":0,"done":0,"next":"—","last":"—","comment":"","sport":"—"}
    return d
def upd(uid, info):
    d = get_u(uid); d[str(uid)].update(info); save_data(d)

def status(uid):
    u = get_u(uid)[str(uid)]
    r = "🏅" if u["done"]>=u["goal"]>0 else ""
    return (
      f"🎯 {u['done']}/{u['goal']} {r}\n"
      f"📅 {u['next']}\n"
      f"🏋️ {u['last']}\n"
      f"🤸 {u['sport']}\n"
      f"💬 {u['comment']}"
    )

kb=ReplyKeyboardMarkup([
  [KeyboardButton("➕ Добавить"),KeyboardButton("✅ Закончить")],
  [KeyboardButton("🎯 Цель"),KeyboardButton("📅 План")],
  [KeyboardButton("⚙️ Спорт"),KeyboardButton("🔁 Сброс")],
  [KeyboardButton("📊 Статус")]
], resize_keyboard=True)

@dp.message(Command("start"))
async def m_start(m:Message):
    await m.answer("Привет! Меню ниже:", reply_markup=kb)

@dp.message(F.text=="🎯 Цель")
async def m_goal(m:Message):
    await m.answer("Сколько в месяц?")
    await dp.current_state(chat=m.chat.id,user=m.from_user.id).set_state("WAIT_GOAL")

@dp.message(F.state=="WAIT_GOAL")
async def m_goal_save(m:Message):
    try:
        g=int(m.text)
        upd(m.from_user.id,{"goal":g})
        await m.answer("Сохранено\n"+status(m.from_user.id))
    except:
        await m.answer("Введи число")
    await dp.current_state(chat=m.chat.id,user=m.from_user.id).clear()

@dp.message(F.text=="➕ Добавить")
async def m_add(m:Message):
    uid=m.from_user.id
    d=load_data(); d[str(uid)]["done"]+=1; save_data(d)
    await m.answer("Напиши коммент:")
    await dp.current_state(chat=m.chat.id,user=uid).set_state("WAIT_COMM")

@dp.message(F.state=="WAIT_COMM")
async def m_comm(m:Message):
    upd(m.from_user.id,{
      "comment":m.text,
      "last":datetime.now().strftime("%d.%m %H:%M")
    })
    await m.answer("Ок\n"+status(m.from_user.id))
    await dp.current_state(chat=m.chat.id,user=m.from_user.id).clear()

@dp.message(F.text=="📅 План")
async def m_plan(m:Message):
    await m.answer("Дата (например 20.06):")
    await dp.current_state(chat=m.chat.id,user=m.from_user.id).set_state("WAIT_PLAN")

@dp.message(F.state=="WAIT_PLAN")
async def m_plan_save(m:Message):
    upd(m.from_user.id,{"next":m.text})
    await m.answer("ОК\n"+status(m.from_user.id))
    await dp.current_state(chat=m.chat.id,user=m.from_user.id).clear()

@dp.message(F.text=="✅ Закончить")
async def m_end(m:Message):
    await m.answer("Готово\n"+status(m.from_user.id))

@dp.message(F.text=="⚙️ Спорт")
async def m_sport(m:Message):
    await m.answer("Вид спорта:")
    await dp.current_state(chat=m.chat.id,user=m.from_user.id).set_state("WAIT_SPORT")

@dp.message(F.state=="WAIT_SPORT")
async def m_sport_save(m:Message):
    upd(m.from_user.id,{"sport":m.text})
    await m.answer("ОК\n"+status(m.from_user.id))
    await dp.current_state(chat=m.chat.id,user=m.from_user.id).clear()

@dp.message(F.text=="🔁 Сброс")
async def m_reset(m:Message):
    d=load_data(); d.pop(str(m.from_user.id),None); save_data(d)
    await m.answer("Сброшено")

@dp.message(F.text=="📊 Статус")
async def m_stat(m:Message):
    await m.answer(status(m.from_user.id))

async def main():
    await dp.start_polling(bot)

if __name__!="__main__":
    # Запуск только на сервере
    asyncio.run(main())
