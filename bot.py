import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram import magic_filter as F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config import BOT_TOKEN
from sheets import get_report

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Daily Report")
    builder.button(text="Weekly Report")
    builder.button(text="Monthly Report")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("IELTS Monitoring botiga xush kelibsiz!", reply_markup=main_menu())

@dp.message(F.text == "Daily Report")
async def daily(message: types.Message):
    res = get_report(30)
    await message.answer(res)

@dp.message(F.text == "Weekly Report")
async def weekly(message: types.Message):
    res = get_report(60)
    await message.answer(res)

@dp.message(F.text == "Monthly Report")
async def monthly(message: types.Message):
    res = get_report(90)
    await message.answer(res)

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
