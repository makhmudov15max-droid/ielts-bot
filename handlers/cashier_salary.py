from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from safety.loader import dp
from safety.keyboards.menu_keyboard import get_menu
from safety.db import load_users


# =========================
# STATES
# =========================

class CashierSalaryState(StatesGroup):

    worked_days = State()
    daily_salary = State()
    debt_percentage = State()
    cover_count = State()
    missed_days = State()


# =========================
# START
# =========================

@dp.message_handler(lambda message: message.text == "💰 Cashier Salary")
async def cashier_salary_start(message: types.Message):

    await message.answer(
        "📅 Necha kun ishladingiz?"
    )

    await CashierSalaryState.worked_days.set()


# =========================
# WORKED DAYS
# =========================

@dp.message_handler(state=CashierSalaryState.worked_days)
async def worked_days_handler(message: types.Message, state: FSMContext):

    if not message.text.isdigit():

        await message.answer(
            "❌ Raqam kiriting."
        )
        return

    await state.update_data(
        worked_days=int(message.text)
    )

    await message.answer(
        "💵 Kunlik maoshingizni kiriting:"
    )

    await CashierSalaryState.daily_salary.set()


# =========================
# DAILY SALARY
# =========================

@dp.message_handler(state=CashierSalaryState.daily_salary)
async def daily_salary_handler(message: types.Message, state: FSMContext):

    if not message.text.isdigit():

        await message.answer(
            "❌ Raqam kiriting."
        )
        return

    await state.update_data(
        daily_salary=int(message.text)
    )

    await message.answer(
        "📉 Qarzdorlik foizini kiriting:"
    )

    await CashierSalaryState.debt_percentage.set()


# =========================
# DEBT %
# =========================

@dp.message_handler(state=CashierSalaryState.debt_percentage)
async def debt_handler(message: types.Message, state: FSMContext):

    try:
        debt = float(message.text)
    except:
        await message.answer(
            "❌ To‘g‘ri foiz kiriting."
        )
        return

    await state.update_data(
        debt_percentage=debt
    )

    await message.answer(
        "🔄 Nechta cover qildingiz?"
    )

    await CashierSalaryState.cover_count.set()


# =========================
# COVER
# =========================

@dp.message_handler(state=CashierSalaryState.cover_count)
async def cover_handler(message: types.Message, state: FSMContext):

    if not message.text.isdigit():

        await message.answer(
            "❌ Raqam kiriting."
        )
        return

    await state.update_data(
        cover_count=int(message.text)
    )

    await message.answer(
        "📌 Necha kun qoldirdingiz?"
    )

    await CashierSalaryState.missed_days.set()


# =========================
# FINAL
# =========================

@dp.message_handler(state=CashierSalaryState.missed_days)
async def final_handler(message: types.Message, state: FSMContext):

    if not message.text.isdigit():

        await message.answer(
            "❌ Raqam kiriting."
        )
        return

    missed_days = int(message.text)

    data = await state.get_data()

    worked_days = data["worked_days"]
    daily_salary = data["daily_salary"]
    debt_percentage = data["debt_percentage"]
    cover_count = data["cover_count"]

    # =========================
    # CALCULATIONS
    # =========================

    worked_salary = worked_days * daily_salary

    if debt_percentage <= 5:
        multiplier = 1.2
    elif debt_percentage <= 10:
        multiplier = 1.1
    else:
        multiplier = 1

    bonus = worked_salary * (multiplier - 1)

    cover_bonus = cover_count * 50000

    missed_penalty = missed_days * 100000

    final_salary = (
        worked_salary +
        bonus +
        cover_bonus -
        missed_penalty
    )

    # =========================
    # ROLE MENU
    # =========================

    users = load_users()

    user_id = str(message.from_user.id)

    role = users[user_id]["role"]

    # =========================
    # RESULT
    # =========================

    await message.answer(
        f"💰 CASHIER SALARY\n\n"

        f"📅 Ish kunlari: {worked_days}\n"
        f"💵 Kunlik maosh: {daily_salary:,} UZS\n\n"

        f"📉 Qarzdorlik: {debt_percentage}%\n"
        f"📈 Bonus: {bonus:,.0f} UZS\n\n"

        f"🔄 Cover bonus: {cover_bonus:,} UZS\n"
        f"📌 Jarima: -{missed_penalty:,} UZS\n\n"

        f"━━━━━━━━━━━━━━━\n\n"

        f"🏦 Yakuniy oylik:\n"
        f"{final_salary:,.0f} UZS",

        reply_markup=get_menu(role)
    )

    await state.finish()


# =========================
# REGISTER
# =========================

def register_cashier_handlers(dp):
    pass
