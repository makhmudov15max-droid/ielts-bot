from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import logging
import os

from sheets import get_report

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Keyboard
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("Daily report")
)

# START
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer(
        "✅ Bot ishlayapti",
        reply_markup=keyboard
    )

# DAILY REPORT
@dp.message_handler(lambda message: message.text == "Daily report")
async def daily_handler(message: types.Message):
    report = get_report()
    await message.answer(report)

# OTHER
@dp.message_handler()
async def other_handler(message: types.Message):
    await message.answer("Tugmadan foydalaning 👇")

# RUN
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
