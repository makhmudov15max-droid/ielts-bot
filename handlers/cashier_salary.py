from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from safety.loader import dp

from safety.db import load_users

from safety.keyboards.menu_keyboard import get_menu

from keyboards.admin_keyboard import (
    days_keyboard,
    status_keyboard
)


# =========================================
# STATES
# =========================================

class CashierSalaryState(StatesGroup):

    worked_days = State()
    daily_salary = State()
    debt_percentage = State()
    cover = State()
    missed = State()


# =========================================
# START
# =========================================

@dp.message_handler(lambda message: message.text == "💰 Cashier Salary")
async def cashier_salary_start(message: types.Message):

    await message.answer(
        "📅 Necha kun ishladingiz?",
        reply_markup=days_keyboard()
    )

    await CashierSalaryState.worked_days.set()


# =========================================
# WORKED DAYS
# =========================================

@dp.message_handler(state=CashierSalaryState.worked_days)
async def worked_days_handler(message: types.Message, state: FSMContext):

    text = message.text.replace(" kun", "")

    if not text.isdigit():

        await message.answer(
            "❌ Raqam kiriting."
        )
        return

    await state.update_data(
        worked_days=int(text)
    )

    await message.answer(
        "💵 Kunlik maoshingizni kiriting:"
    )

    await CashierSalaryState.daily_salary.set()


# =========================================
# DAILY SALARY
# =========================================

@dp.message_handler(state=CashierSalaryState.daily_salary)
async def daily_salary_handler(message: types.Message, state: FSMContext):

    text = message.text.replace(" ", "")

    if not text.isdigit():

        await message.answer(
            "❌ Raqam kiriting."
        )
        return

    await state.update_data(
        daily_salary=int(text)
    )

    await message.answer(
        "📉 Qarzdorlik foizini kiriting:"
    )

    await CashierSalaryState.debt_percentage.set()


# =========================================
# DEBT
# =========================================

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
        "🔄 Cover qildingizmi?",
        reply_markup=status_keyboard()
    )

    await CashierSalaryState.cover.set()


# =========================================
# COVER
# =========================================

@dp.message_handler(state=CashierSalaryState.cover)
async def cover_handler(message: types.Message, state: FSMContext):

    text = message.text.lower()

    if "ha" in text:
        cover_bonus = 50000
    else:
        cover_bonus = 0

    await state.update_data(
        cover_bonus=cover_bonus
    )

    await message.answer(
        "📉 Ish qoldirdingizmi?",
        reply_markup=status_keyboard()
    )

    await CashierSalaryState.missed.set()


# =========================================
# MISSED
# =========================================

@dp.message_handler(state=CashierSalaryState.missed)
async def missed_handler(message: types.Message, state: FSMContext):

    text = message.text.lower()

    if "ha" in text:
        penalty = 100000
    else:
        penalty = 0

    data = await state.get_data()

    worked_days = data["worked_days"]
    daily_salary = data["daily_salary"]
    debt_percentage = data["debt_percentage"]
    cover_bonus = data["cover_bonus"]

    worked_salary = worked_days * daily_salary

    if debt_percentage <= 5:
        multiplier = 1.2

    elif debt_percentage <= 10:
        multiplier = 1.1

    else:
        multiplier = 1

    bonus = worked_salary * (multiplier - 1)

    final_salary = (
        worked_salary +
        bonus +
        cover_bonus -
        penalty
    )

    users = load_users()

    user_id = str(message.from_user.id)

    role = users[user_id]["role"]

    await message.answer(
        f"💰 CASHIER SALARY\n\n"

        f"📅 Ish kunlari: {worked_days}\n"

        f"💵 Kunlik maosh: "
        f"{daily_salary:,.0f} UZS\n\n"

        f"📉 Qarzdorlik: "
        f"{debt_percentage}%\n\n"

        f"📈 Bonus: "
        f"{bonus:,.0f} UZS\n\n"

        f"🔄 Cover bonus: "
        f"{cover_bonus:,.0f} UZS\n\n"

        f"📌 Jarima: "
        f"-{penalty:,.0f} UZS\n\n"

        f"━━━━━━━━━━━━━━━\n\n"

        f"🏦 Yakuniy oylik:\n"
        f"{final_salary:,.0f} UZS",

        reply_markup=get_menu(role)
    )

    await state.finish()


# =========================================
# REGISTER
# =========================================

def register_cashier_handlers(dp):
    pass
