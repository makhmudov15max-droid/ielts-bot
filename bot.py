from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils import executor

from states import SalaryStates
import logging
import os
import asyncio
from roles import OWNERS
from datetime import datetime

from sheets import (
    get_report,
    update_teacher_score
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

bot = Bot(token=BOT_TOKEN)
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)

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
owner_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

owner_keyboard.add("💰 Salary Panel")
owner_keyboard.add("➕ Add Owner")

# AUTO DAILY REPORT
async def auto_daily_report():

    while True:

        now = datetime.now()

        # Yakshanba emas va vaqt 09:00
        if now.weekday() != 6 and now.hour == 9 and now.minute == 0:

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

    if message.from_user.id in OWNERS:
        await message.answer(
            "✅ Main manager panel",
            reply_markup=owner_keyboard
        )

    else:
        await message.answer(
            "✅ Office manager panel",
            reply_markup=keyboard
        )

# DAILY REPORT
@dp.message_handler(lambda message: message.text == "Daily report")
async def daily_handler(message: types.Message):

    report = get_report()

    await message.answer(report)

@dp.message_handler(lambda message: message.text == "💰 Salary Panel")
async def salary_panel(message: types.Message):

    await message.answer("👤 Admin ism familiyasini kiriting:")

    await SalaryStates.waiting_for_name.set()


@dp.message_handler(state=SalaryStates.waiting_for_name)
async def get_admin_name(message: types.Message, state: FSMContext):

    admin_name = message.text

    await state.update_data(admin_name=admin_name)

    status_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    status_keyboard.add("Nova")
    status_keyboard.add("Prime")
    status_keyboard.add("Apex")
    status_keyboard.add("Leader")

    await message.answer(
        f"✅ Admin: {admin_name}\n\n🏆 Statusni tanlang:",
        reply_markup=status_keyboard
    )

    await SalaryStates.waiting_for_status.set()


@dp.message_handler(state=SalaryStates.waiting_for_status)
async def get_status(message: types.Message, state: FSMContext):

    status = message.text

    await state.update_data(status=status)

    hours_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    await message.answer(
    f"🏆 Status: {status}\n\n⏰ Ish soatini kiriting:",
    reply_markup=types.ReplyKeyboardRemove()
)

    await SalaryStates.waiting_for_hours.set()

@dp.message_handler(state=SalaryStates.waiting_for_hours)
async def get_hours(message: types.Message, state: FSMContext):

    hours = message.text

    await state.update_data(hours=hours)

    await message.answer(
    f"⏰ Ish soati: {hours} soat\n\n📅 Ish kunlari sonini kiriting:",
    reply_markup=types.ReplyKeyboardRemove()
)

    await SalaryStates.waiting_for_days.set()


@dp.message_handler(state=SalaryStates.waiting_for_days)
async def get_days(message: types.Message, state: FSMContext):

    days = message.text

    await state.update_data(days=days)

    await message.answer(
        f"📅 Ish kunlari: {days} kun\n\n🎯 Individual plan kiriting:"
    )

    await SalaryStates.waiting_for_individual_plan.set()


@dp.message_handler(state=SalaryStates.waiting_for_individual_plan)
async def get_individual_plan(message: types.Message, state: FSMContext):

    individual_plan = message.text

    await state.update_data(individual_plan=individual_plan)

    await message.answer(
        f"🎯 Individual plan: {individual_plan}\n\n✅ Amaldagi sotuv sonini kiriting:"
    )

    await SalaryStates.waiting_for_actual_sales.set()

@dp.message_handler(state=SalaryStates.waiting_for_actual_sales)
async def get_actual_sales(message: types.Message, state: FSMContext):

    actual_sales = message.text

    await state.update_data(actual_sales=actual_sales)

    await message.answer(
        f"✅ Amaldagi sotuv: {actual_sales}\n\n📈 Konversiya planini kiriting:"
    )

    await SalaryStates.waiting_for_conversion_plan.set()

@dp.message_handler(state=SalaryStates.waiting_for_conversion_plan)
async def get_conversion_plan(message: types.Message, state: FSMContext):

    conversion_plan = message.text

    await state.update_data(conversion_plan=conversion_plan)

    await message.answer(
        f"📈 Konversiya plani: {conversion_plan}%\n\n📊 Amaldagi konversiyani kiriting:"
    )

    await SalaryStates.waiting_for_actual_conversion.set()


@dp.message_handler(state=SalaryStates.waiting_for_actual_conversion)
async def get_actual_conversion(message: types.Message, state: FSMContext):

    actual_conversion = message.text

    await state.update_data(actual_conversion=actual_conversion)

    await message.answer(
    f"📊 Amaldagi konversiya: {actual_conversion}%\n\n🔔 Aktiv plan kiriting:"
)

    await SalaryStates.waiting_for_active_plan.set()

@dp.message_handler(state=SalaryStates.waiting_for_active_plan)
async def get_active_plan(message: types.Message, state: FSMContext):

    active_plan = message.text

    await state.update_data(active_plan=active_plan)

    await message.answer(
        f"🔔 Aktiv plan: {active_plan}\n\n👥 Jamoaviy aktiv o'quvchilar sonini kiriting:"
    )

    await SalaryStates.waiting_for_team_active.set()


@dp.message_handler(state=SalaryStates.waiting_for_team_active)
async def get_team_active(message: types.Message, state: FSMContext):

    team_active = message.text

    await state.update_data(team_active=team_active)

    russian_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    russian_keyboard.add("✅ Ha")
    russian_keyboard.add("❌ Yo'q")

    await message.answer(
        f"👥 Jamoaviy aktiv o'quvchilar: {team_active}\n\n🌍 Rus tilini biladimi?",
        reply_markup=russian_keyboard
    )

    await SalaryStates.waiting_for_russian.set()


@dp.message_handler(state=SalaryStates.waiting_for_russian)
async def get_russian(message: types.Message, state: FSMContext):

    russian = message.text

    await state.update_data(russian=russian)

    ielts_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    ielts_keyboard.add("✅ Ha")
    ielts_keyboard.add("❌ Yo'q")

    await message.answer(
        f"🌍 Rus tili: {russian}\n\n🎓 IELTS 7+ bormi?",
        reply_markup=ielts_keyboard
    )

    await SalaryStates.waiting_for_ielts.set()


@dp.message_handler(state=SalaryStates.waiting_for_ielts)
async def get_ielts(message: types.Message, state: FSMContext):

    ielts = message.text

    await state.update_data(ielts=ielts)

    await message.answer(
        f"🎓 IELTS: {ielts}\n\n⏳ Necha soat ish qoldirdi?"
    )

    await SalaryStates.waiting_for_missed_hours.set()


@dp.message_handler(state=SalaryStates.waiting_for_missed_hours)
async def get_missed_hours(message: types.Message, state: FSMContext):

    missed_hours = message.text

    await state.update_data(missed_hours=missed_hours)

    cover_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    cover_keyboard.add("✅ Cover qilgan")
    cover_keyboard.add("❌ Cover qilmagan")

    await message.answer(
        f"⏳ Qoldirilgan soat: {missed_hours}\n\n🔄 Cover qilganmi?",
        reply_markup=cover_keyboard
    )

    await SalaryStates.waiting_for_cover.set()


@dp.message_handler(state=SalaryStates.waiting_for_cover)
async def get_cover(message: types.Message, state: FSMContext):

    cover = message.text

    await state.update_data(cover=cover)

    if cover == "✅ Cover qilgan":

        await message.answer(
            "🔄 Necha soat cover qilgan?"
        )

        await SalaryStates.waiting_for_cover_hours.set()

    else:

        data = await state.get_data()

        status = data.get("status")
        hours = int(data.get("hours"))
        days = int(data.get("days"))

    rates = {
        "Nova": 11000,
        "Prime": 12000,
        "Apex": 13000,
        "Leader": 15000
    }

    hourly_rate = rates.get(status, 0)

    fixa = hourly_rate * hours * days

    await message.answer(
        f"💵 Fiksa hisoblandi: {fixa:,} UZS"
    )

    await state.finish()


@dp.message_handler(state=SalaryStates.waiting_for_cover_hours)
async def get_cover_hours(message: types.Message, state: FSMContext):

    cover_hours = message.text

    await state.update_data(cover_hours=cover_hours)

    data = await state.get_data()

    status = data.get("status")
    hours = int(data.get("hours"))
    days = int(data.get("days"))

    rates = {
    "Nova": 11000,
    "Prime": 12000,
    "Apex": 13000,
    "Leader": 15000
}

    hourly_rate = rates.get(status, 0)

    fixa = hourly_rate * hours * days

    await message.answer(
    f"💵 Fiksa hisoblandi: {fixa:,} UZS"
)

    await state.finish()

# TEST AUTO REPORT
@dp.message_handler(commands=["testreport"])
async def test_report(message: types.Message):

    report = get_report()

    await bot.send_message(
        chat_id=GROUP_ID,
        text=report
    )

    await message.answer(
        "✅ Groupga yuborildi"
    )

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
