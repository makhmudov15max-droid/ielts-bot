import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from sheets import get_report

logging.basicConfig(level=logging.INFO)

# 🔑 Token Railway variables dan olinadi
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# 🔘 Tugmalar
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("Daily report"),
    KeyboardButton("Weekly report"),
    KeyboardButton("Monthly report")
)

# 🚀 START
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("Bot ishlayapti ✅", reply_markup=keyboard)

# 📊 Daily
@dp.message_handler(lambda message: message.text == "Daily report")
async def daily(message: types.Message):
    report = get_report(30)
await message.answer(report)

# 📊 Weekly
@dp.message_handler(lambda message: message.text == "Weekly report")
async def weekly(message: types.Message):
    report = get_report(60)
await message.answer(report)

# 📊 Monthly
@dp.message_handler(lambda message: message.text == "Monthly report")
async def monthly(message: types.Message):
    report = get_report(90)
await message.answer(report)

# ❗ boshqa message
@dp.message_handler()
async def other(message: types.Message):
    await message.answer("Tugmalardan birini tanlang")

# 🚀 RUN
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
