from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
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
@dp.message_handler(commands=['start'], state="*")
async def start_handler(message: types.Message, state: FSMContext):

    await state.finish()

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("💰 Salary Panel")

    await message.answer(
        "🏠 Asosiy menu",
        reply_markup=keyboard
    )

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

class SalaryStates(StatesGroup):

    waiting_for_name = State()
    waiting_for_status = State()
    waiting_for_hours = State()
    waiting_for_days = State()

    waiting_for_individual_plan = State()
    waiting_for_actual_sales = State()

    waiting_for_conversion_plan = State()
    waiting_for_actual_conversion = State()

    waiting_for_active_plan = State()
    waiting_for_team_active = State()

    waiting_for_russian = State()
    waiting_for_ielts = State()
    
    waiting_for_missed_work = State()
    waiting_for_missed_hours = State()
    
    waiting_for_cover = State()
    waiting_for_cover_hours = State()


@dp.message_handler(lambda message: message.text == "💰 Salary Panel")
async def salary_panel(message: types.Message):

    await message.answer(
        "👤 Admin ism familiyasini kiriting:"
    )

    await SalaryStates.waiting_for_name.set()


@dp.message_handler(state=SalaryStates.waiting_for_name)
async def get_admin_name(message: types.Message, state: FSMContext):

    await state.update_data(admin_name=message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Nova")
    keyboard.add("Prime")
    keyboard.add("Apex")
    keyboard.add("Leader")

    await message.answer(
        "🏆 Statusni tanlang:",
        reply_markup=keyboard
    )

    await SalaryStates.waiting_for_status.set()


@dp.message_handler(state=SalaryStates.waiting_for_status)
async def get_status(message: types.Message, state: FSMContext):

    await state.update_data(status=message.text)

    await message.answer(
        "⏰ Ish soatini kiriting:"
    )

    await SalaryStates.waiting_for_hours.set()


@dp.message_handler(state=SalaryStates.waiting_for_hours)
async def get_hours(message: types.Message, state: FSMContext):

    await state.update_data(hours=message.text)

    await message.answer(
        "📅 Ish kunlari sonini kiriting:"
    )

    await SalaryStates.waiting_for_days.set()


@dp.message_handler(state=SalaryStates.waiting_for_days)
async def get_days(message: types.Message, state: FSMContext):

    await state.update_data(days=message.text)

    await message.answer(
        "🎯 Individual plan:"
    )

    await SalaryStates.waiting_for_individual_plan.set()


@dp.message_handler(state=SalaryStates.waiting_for_individual_plan)
async def get_individual_plan(message: types.Message, state: FSMContext):

    await state.update_data(individual_plan=message.text)

    await message.answer(
        "💸 Actual sales:"
    )

    await SalaryStates.waiting_for_actual_sales.set()


@dp.message_handler(state=SalaryStates.waiting_for_actual_sales)
async def get_actual_sales(message: types.Message, state: FSMContext):

    await state.update_data(actual_sales=message.text)

    await message.answer(
        "📊 Conversion plan:"
    )

    await SalaryStates.waiting_for_conversion_plan.set()


@dp.message_handler(state=SalaryStates.waiting_for_conversion_plan)
async def get_conversion_plan(message: types.Message, state: FSMContext):

    await state.update_data(conversion_plan=message.text)

    await message.answer(
        "📈 Actual conversion:"
    )

    await SalaryStates.waiting_for_actual_conversion.set()


@dp.message_handler(state=SalaryStates.waiting_for_actual_conversion)
async def get_actual_conversion(message: types.Message, state: FSMContext):

    await state.update_data(actual_conversion=message.text)

    await message.answer(
        "👥 Active students plan:"
    )

    await SalaryStates.waiting_for_active_plan.set()


@dp.message_handler(state=SalaryStates.waiting_for_active_plan)
async def get_active_plan(message: types.Message, state: FSMContext):

    await state.update_data(active_plan=message.text)

    await message.answer(
        "👥 Actual active students:"
    )

    await SalaryStates.waiting_for_team_active.set()


@dp.message_handler(state=SalaryStates.waiting_for_team_active)
async def get_team_active(message: types.Message, state: FSMContext):

    await state.update_data(actual_active=message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("✅ Ha")
    keyboard.add("❌ Yo'q")

    await message.answer(
        "🌍 Rus tilini biladimi?",
        reply_markup=keyboard
    )

    await SalaryStates.waiting_for_russian.set()


@dp.message_handler(state=SalaryStates.waiting_for_russian)
async def get_russian(message: types.Message, state: FSMContext):

    await state.update_data(russian=message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("✅ Ha")
    keyboard.add("❌ Yo'q")

    await message.answer(
        "🎓 IELTS 7+ bormi?",
        reply_markup=keyboard
    )

    await SalaryStates.waiting_for_ielts.set()


@dp.message_handler(state=SalaryStates.waiting_for_ielts)
async def get_ielts(message: types.Message, state: FSMContext):
    
    @dp.message_handler(state=SalaryStates.waiting_for_missed_work)
async def get_missed_work(message: types.Message, state: FSMContext):

    missed_work = message.text

    await state.update_data(missed_work=missed_work)

    if missed_work == "✅ Ha":

        await message.answer(
            "⏰ Necha soat ish qoldirdi?"
        )

        await SalaryStates.waiting_for_missed_hours.set()

    else:

        await state.update_data(missed_hours=0)

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

        keyboard.add("✅ Cover qilgan")
        keyboard.add("❌ Cover qilmagan")

        await message.answer(
            "🔄 Cover qilganmi?",
            reply_markup=keyboard
        )

        await SalaryStates.waiting_for_cover.set()

@dp.message_handler(state=SalaryStates.waiting_for_missed_hours)
async def get_missed_hours(message: types.Message, state: FSMContext):

    await state.update_data(missed_hours=message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("✅ Cover qilgan")
    keyboard.add("❌ Cover qilmagan")

    await message.answer(
        "🔄 Cover qilganmi?",
        reply_markup=keyboard
    )

    await SalaryStates.waiting_for_cover.set()

    await state.update_data(ielts=message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("✅ Ha")
    keyboard.add("❌ Yo'q")

    await message.answer(
        "📉 Ish qoldirdimi?",
        reply_markup=keyboard
    )

    await SalaryStates.waiting_for_missed_work.set()


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

        await state.update_data(cover_hours=0)

        await calculate_salary(message, state)


@dp.message_handler(state=SalaryStates.waiting_for_cover_hours)
async def get_cover_hours(message: types.Message, state: FSMContext):

    await state.update_data(cover_hours=message.text)

    await calculate_salary(message, state)


async def calculate_salary(message: types.Message, state: FSMContext):

    data = await state.get_data()

    status = data.get("status")

    hours = int(data.get("hours", 0))
    days = int(data.get("days", 0))

    individual_plan = float(data.get("individual_plan", 0))
    actual_sales = float(data.get("actual_sales", 0))

    conversion_plan = float(data.get("conversion_plan", 0))
    actual_conversion = float(data.get("actual_conversion", 0))

    active_plan = float(data.get("active_plan", 0))
    actual_active = float(data.get("actual_active", 0))

    cover_hours = float(data.get("cover_hours", 0))

    russian = data.get("russian")
    ielts = data.get("ielts")

    rates = {
        "Nova": 11000,
        "Prime": 12000,
        "Apex": 13000,
        "Leader": 15000
    }

    hourly_rate = rates.get(status, 0)

    fixa = hourly_rate * hours * days

    russian_bonus = 500000 if russian == "✅ Ha" else 0
    ielts_bonus = 1000000 if ielts == "✅ Ha" else 0

    individual_percentage = (actual_sales / individual_plan) * 100
    conversion_percentage = (actual_conversion / conversion_plan) * 100
    active_percentage = (actual_active / active_plan) * 100

    weighted_kpi = (
        (individual_percentage * 0.5) +
        (conversion_percentage * 0.3) +
        (active_percentage * 0.2)
    )

    if weighted_kpi <= 49:
        bonus_rate = 0

    elif weighted_kpi <= 60:
        bonus_rate = 5000

    elif weighted_kpi <= 70:
        bonus_rate = 6000

    elif weighted_kpi <= 80:
        bonus_rate = 10000

    elif weighted_kpi <= 90:
        bonus_rate = 15000

    elif weighted_kpi <= 95:
        bonus_rate = 18000

    elif weighted_kpi <= 100:
        bonus_rate = 25000

    elif weighted_kpi <= 110:
        bonus_rate = 30000

    elif weighted_kpi <= 120:
        bonus_rate = 32000

    elif weighted_kpi <= 130:
        bonus_rate = 35000

    else:
        bonus_rate = 40000

    base_kpi_bonus = actual_sales * bonus_rate

    kpi_bonus = base_kpi_bonus * (weighted_kpi / 100)

    cover_bonus = cover_hours * hourly_rate

    total_salary = (
        fixa +
        russian_bonus +
        ielts_bonus +
        cover_bonus +
        kpi_bonus
    )

    await message.answer(
        f"📈 Individual KPI: {individual_percentage:.1f}%\n"
        f"📊 Conversion KPI: {conversion_percentage:.1f}%\n"
        f"👥 Active KPI: {active_percentage:.1f}%\n\n"

        f"🏆 Weighted KPI: {weighted_kpi:.1f}%\n\n"

        f"🔥 KPI Bonus: {kpi_bonus:,.0f} UZS\n"
        f"🔄 Cover bonus: +{cover_bonus:,.0f} UZS\n\n"

        f"💵 Fiksa: {fixa:,.0f} UZS\n"
        f"🌍 Rus bonusi: +{russian_bonus:,.0f} UZS\n"
        f"🎓 IELTS bonusi: +{ielts_bonus:,.0f} UZS\n\n"

        f"💰 JAMI OYLIK: {total_salary:,.0f} UZS"
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
