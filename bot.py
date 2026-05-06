from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils import executor

import logging
import os
import asyncio
from datetime import datetime

from sheets import (
    get_report,
    update_teacher_score
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# MEMORY
selected_teacher = {}

# MAIN MENU
keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

keyboard.row(
    KeyboardButton("Daily report"),
    KeyboardButton("Teachers")
)

# AUTO DAILY REPORT
async def auto_daily_report():

    while True:

        now = datetime.now()

        # Yakshanba emas va vaqt 09:00
        if now.weekday() != 6 and now.hour == 2 and now.minute == 55:

            try:

                report = get_report()

                await bot.send_message(
                    chat_id=GROUP_ID,
                    text=report
                )

                print("✅ DAILY REPORT YUBORILDI")

                # Duplicate yubormaslik uchun
                await asyncio.sleep(60)

            except Exception as e:

                print(f"❌ AUTO REPORT ERROR: {e}")

        await asyncio.sleep(20)

# STARTUP
async def on_startup(dp):

    asyncio.create_task(
        auto_daily_report()
    )

# START
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):

    await message.answer(
        "Assalomu aalaykum 😇 sizga qanday yordam bera olaman 🙃",
        reply_markup=keyboard
    )

# DAILY REPORT
@dp.message_handler(lambda message: message.text == "Daily report")
async def daily_handler(message: types.Message):

    report = get_report()

    await message.answer(report)

# TEACHERS BUTTON
@dp.message_handler(lambda message: message.text == "Teachers")
async def teacher_menu(message: types.Message):

    markup = InlineKeyboardMarkup(row_width=2)

    teachers = [
        "Adkhambek I",
        "Sardorbek K",
        "Akhmadali T",
        "Obidjon R",
        "Otabek M",
        "Ilkhom A",
        "Sevinch I",
        "Khurshid Kh",
        "Nilufar K",
        "Farangiz E"
    ]

    buttons = []

    for teacher in teachers:

        buttons.append(
            InlineKeyboardButton(
                teacher,
                callback_data=f"teacher_{teacher}"
            )
        )

    markup.add(*buttons)

    await message.answer(
        "👨‍🏫 Ustozni tanlang",
        reply_markup=markup
    )

# TEACHER SELECT
@dp.callback_query_handler(lambda c: c.data.startswith("teacher_"))
async def teacher_selected(callback: types.CallbackQuery):

    teacher_name = callback.data.replace("teacher_", "")

    selected_teacher[callback.from_user.id] = teacher_name

    markup = InlineKeyboardMarkup(row_width=2)

    markup.row(
        InlineKeyboardButton(
            "8.5",
            callback_data="score_8.5"
        ),

        InlineKeyboardButton(
            "9.0",
            callback_data="score_9.0"
        )
    )

    await callback.message.answer(
        f"{teacher_name} ustozning yangilangan bali nechchi? 🧐",
        reply_markup=markup
    )

# SCORE SELECT
@dp.callback_query_handler(lambda c: c.data.startswith("score_"))
async def score_selected(callback: types.CallbackQuery):

    score = callback.data.replace("score_", "")

    teacher_name = selected_teacher.get(
        callback.from_user.id
    )

    if not teacher_name:

        await callback.message.answer(
            "❌ Ustoz topilmadi"
        )

        return

    update_teacher_score(
        teacher_name,
        score
    )

    await callback.message.answer(
        f"✅ {teacher_name} ustozimizning IELTS natijasi yangilandi 🙂"
    )

# OTHER
@dp.message_handler()
async def other_handler(message: types.Message):

    await message.answer(
        "Tugmalardan foydalaning 👇"
    )

# RUN
if __name__ == "__main__":

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup
    )
