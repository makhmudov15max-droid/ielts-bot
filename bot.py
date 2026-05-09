from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup


class SalaryStates(StatesGroup):
    waiting_for_status = State()
    waiting_for_hours = State()
    waiting_for_days = State()

    waiting_for_individual_plan = State()
    waiting_for_actual_sales = State()

    waiting_for_conversion_plan = State()
    waiting_for_actual_conversion = State()

    waiting_for_active_plan = State()
    waiting_for_actual_active = State()

    waiting_for_russian = State()
    waiting_for_ielts = State()

    waiting_for_missed_work = State()
    waiting_for_missed_hours = State()

    waiting_for_cover = State()
    waiting_for_cover_hours = State()


@dp.message_handler(commands=["salary"])
async def salary_start(message: types.Message):

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Nova")
    keyboard.add("Prime")
    keyboard.add("Apex")
    keyboard.add("Leader")

    await message.answer(
        "📋 Statusni tanlang:",
        reply_markup=keyboard
    )

    await SalaryStates.waiting_for_status.set()


@dp.message_handler(state=SalaryStates.waiting_for_status)
async def get_status(message: types.Message, state: FSMContext):

    await state.update_data(status=message.text)

    await message.answer("⏰ Kunlik necha soat ishlaydi?")

    await SalaryStates.waiting_for_hours.set()


@dp.message_handler(state=SalaryStates.waiting_for_hours)
async def get_hours(message: types.Message, state: FSMContext):

    await state.update_data(hours=message.text)

    await message.answer("📅 Oyda necha kun ishladi?")

    await SalaryStates.waiting_for_days.set()


@dp.message_handler(state=SalaryStates.waiting_for_days)
async def get_days(message: types.Message, state: FSMContext):

    await state.update_data(days=message.text)

    await message.answer("🎯 Individual plan nechta?")

    await SalaryStates.waiting_for_individual_plan.set()


@dp.message_handler(state=SalaryStates.waiting_for_individual_plan)
async def get_individual_plan(message: types.Message, state: FSMContext):

    await state.update_data(individual_plan=message.text)

    await message.answer("📈 Amaldagi sotuv nechta?")

    await SalaryStates.waiting_for_actual_sales.set()


@dp.message_handler(state=SalaryStates.waiting_for_actual_sales)
async def get_actual_sales(message: types.Message, state: FSMContext):

    await state.update_data(actual_sales=message.text)

    await message.answer("📊 Conversion plan nechta?")

    await SalaryStates.waiting_for_conversion_plan.set()


@dp.message_handler(state=SalaryStates.waiting_for_conversion_plan)
async def get_conversion_plan(message: types.Message, state: FSMContext):

    await state.update_data(conversion_plan=message.text)

    await message.answer("📊 Amaldagi conversion nechta?")

    await SalaryStates.waiting_for_actual_conversion.set()


@dp.message_handler(state=SalaryStates.waiting_for_actual_conversion)
async def get_actual_conversion(message: types.Message, state: FSMContext):

    await state.update_data(actual_conversion=message.text)

    await message.answer("👥 Aktiv plan nechta?")

    await SalaryStates.waiting_for_active_plan.set()


@dp.message_handler(state=SalaryStates.waiting_for_active_plan)
async def get_active_plan(message: types.Message, state: FSMContext):

    await state.update_data(active_plan=message.text)

    await message.answer("👥 Amaldagi aktiv nechta?")

    await SalaryStates.waiting_for_actual_active.set()


@dp.message_handler(state=SalaryStates.waiting_for_actual_active)
async def get_actual_active(message: types.Message, state: FSMContext):

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

    await state.update_data(ielts=message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("✅ Ha")
    keyboard.add("❌ Yo'q")

    await message.answer(
        "📉 Ish qoldirdimi?",
        reply_markup=keyboard
    )

    await SalaryStates.waiting_for_missed_work.set()


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


@dp.message_handler(state=SalaryStates.waiting_for_cover)
async def get_cover(message: types.Message, state: FSMContext):

    cover = message.text

    await state.update_data(cover=cover)

    if cover == "✅ Cover qilgan":

        await message.answer(
            "⏰ Necha soat cover qilgan?"
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

    rates = {
        "Nova": 11000,
        "Prime": 12000,
        "Apex": 13000,
        "Leader": 15000
    }

    hourly_rate = rates.get(status, 0)

    hours = float(data.get("hours", 0))
    days = float(data.get("days", 0))
    missed_hours = float(data.get("missed_hours", 0))

    worked_hours = (hours * days) - missed_hours

    fixa = worked_hours * hourly_rate

    russian_bonus = 500000 if data.get("russian") == "✅ Ha" else 0
    ielts_bonus = 1000000 if data.get("ielts") == "✅ Ha" else 0

    cover_hours = float(data.get("cover_hours", 0))
    cover_bonus = cover_hours * hourly_rate

    individual_plan = float(data.get("individual_plan", 1))
    actual_sales = float(data.get("actual_sales", 0))

    conversion_plan = float(data.get("conversion_plan", 1))
    actual_conversion = float(data.get("actual_conversion", 0))

    active_plan = float(data.get("active_plan", 1))
    actual_active = float(data.get("actual_active", 0))

    individual_percentage = (actual_sales / individual_plan) * 100
    conversion_percentage = (actual_conversion / conversion_plan) * 100
    active_percentage = (actual_active / active_plan) * 100

    if individual_percentage <= 49:
        bonus_rate = 0
    elif individual_percentage <= 60:
        bonus_rate = 5000
    elif individual_percentage <= 70:
        bonus_rate = 6000
    elif individual_percentage <= 80:
        bonus_rate = 10000
    elif individual_percentage <= 90:
        bonus_rate = 15000
    elif individual_percentage <= 95:
        bonus_rate = 18000
    elif individual_percentage <= 100:
        bonus_rate = 25000
    elif individual_percentage <= 110:
        bonus_rate = 30000
    elif individual_percentage <= 120:
        bonus_rate = 32000
    elif individual_percentage <= 130:
        bonus_rate = 35000
    else:
        bonus_rate = 40000

    weighted_kpi = (
        (individual_percentage * 0.5) +
        (conversion_percentage * 0.3) +
        (active_percentage * 0.2)
    )

    base_kpi_bonus = actual_sales * bonus_rate

    kpi_bonus = base_kpi_bonus * (weighted_kpi / 100)

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
