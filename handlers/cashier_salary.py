# handlers/cashier_salary.py

import json

from aiogram import types
from aiogram.dispatcher import FSMContext

from safety.loader import dp

from states.cashier_states import (
    CashierStates
)

from calculators.cashier_calc import (
    calculate_cashier_salary
)

from keyboards.admin_keyboard import (
    owner_panel,
    admin_menu,
    cashier_menu
)


USERS_FILE = "safety/database/users.json"


# =========================================
# GET MENU BY ROLE
# =========================================


def get_menu_by_role(role):

    if role in [
        "owner",
        "manager",
        "coordinator"
    ]:

        return owner_panel

    if role == "admin":

        return admin_menu

    return cashier_menu


# =========================================
# KEYBOARDS
# =========================================


def hours_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "6",
        "7"
    )

    keyboard.row(
        "8"
    )

    keyboard.row(
        "✍️ Boshqa"
    )

    keyboard.row(
        "🏠 Bosh sahifa",
        "⬅️ Ortga"
    )

    return keyboard



def days_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "24",
        "25"
    )

    keyboard.row(
        "26",
        "27"
    )

    keyboard.row(
        "✍️ Boshqa"
    )

    keyboard.row(
        "🏠 Bosh sahifa",
        "⬅️ Ortga"
    )

    return keyboard



def yes_no_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "✅ HA",
        "❌ YO‘Q"
    )

    keyboard.row(
        "🏠 Bosh sahifa",
        "⬅️ Ortga"
    )

    return keyboard



def manual_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "🏠 Bosh sahifa",
        "⬅️ Ortga"
    )

    return keyboard


# =========================================
# HOME
# =========================================


@dp.message_handler(
    text="🏠 Bosh sahifa",
    state="*"
)
async def cashier_home(
    message: types.Message,
    state: FSMContext
):

    await state.finish()

    with open(
        USERS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        users = json.load(file)

    role = users[
        str(message.from_user.id)
    ]["role"]

    await message.answer(
        "🏠 Bosh sahifa",
        reply_markup=get_menu_by_role(role)
    )


# =========================================
# START
# =========================================


@dp.message_handler(
    lambda message: message.text == "💰 Cashier Salary"
)
async def cashier_salary_start(
    message: types.Message
):

    await CashierStates.hours.set()

    await message.answer(
        """
💰 CASHIER SALARY

━━━━━━━━━━━━━━━━━━

⏰ Kunlik ish soatini tanlang:
""",
        reply_markup=hours_keyboard()
    )


# =========================================
# HOURS
# =========================================


@dp.message_handler(
    state=CashierStates.hours
)
async def cashier_hours(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await state.finish()

        with open(
            USERS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            users = json.load(file)

        role = users[
            str(message.from_user.id)
        ]["role"]

        return await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=get_menu_by_role(role)
        )

    if text == "✍️ Boshqa":

        await CashierStates.custom_hours.set()

        return await message.answer(
            "⏰ Soat kiriting:",
            reply_markup=manual_keyboard()
        )

    try:

        value = float(text)

    except:

        return await message.answer(
            "❌ Tugmalardan foydalaning."
        )

    await state.update_data(
        hours=value
    )

    await CashierStates.days.set()

    await message.answer(
        """
📅 Ishlagan kunni tanlang:
""",
        reply_markup=days_keyboard()
    )


# =========================================
# CUSTOM HOURS
# =========================================


@dp.message_handler(
    state=CashierStates.custom_hours
)
async def cashier_custom_hours(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.hours.set()

        return await message.answer(
            "⏰ Kunlik ish soatini tanlang:",
            reply_markup=hours_keyboard()
        )

    try:

        value = float(text)

    except:

        return await message.answer(
            "❌ Raqam kiriting."
        )

    await state.update_data(
        hours=value
    )

    await CashierStates.days.set()

    await message.answer(
        "📅 Ishlagan kunni tanlang:",
        reply_markup=days_keyboard()
    )


# =========================================
# DAYS
# =========================================


@dp.message_handler(
    state=CashierStates.days
)
async def cashier_days(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.hours.set()

        return await message.answer(
            "⏰ Kunlik ish soatini tanlang:",
            reply_markup=hours_keyboard()
        )

    if text == "✍️ Boshqa":

        await CashierStates.custom_days.set()

        return await message.answer(
            "📅 Kun kiriting:",
            reply_markup=manual_keyboard()
        )

    try:

        value = float(text)

    except:

        return await message.answer(
            "❌ Tugmalardan foydalaning."
        )

    await state.update_data(
        days=value
    )

    await CashierStates.cover.set()

    await message.answer(
        "🔄 Cover qilganmi?",
        reply_markup=yes_no_keyboard()
    )


# =========================================
# CUSTOM DAYS
# =========================================


@dp.message_handler(
    state=CashierStates.custom_days
)
async def cashier_custom_days(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.days.set()

        return await message.answer(
            "📅 Ishlagan kunni tanlang:",
            reply_markup=days_keyboard()
        )

    try:

        value = float(text)

    except:

        return await message.answer(
            "❌ Raqam kiriting."
        )

    await state.update_data(
        days=value
    )

    await CashierStates.cover.set()

    await message.answer(
        "🔄 Cover qilganmi?",
        reply_markup=yes_no_keyboard()
    )


# =========================================
# COVER
# =========================================


@dp.message_handler(
    state=CashierStates.cover
)
async def get_cover(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.days.set()

        return await message.answer(
            "📅 Ishlagan kunni tanlang:",
            reply_markup=days_keyboard()
        )

    if text == "✅ HA":

        await CashierStates.cover_hours.set()

        return await message.answer(
            "⏰ Necha kun cover qildingiz?",
            reply_markup=manual_keyboard()
        )

    await state.update_data(
        cover_days=0
    )

    await CashierStates.absent.set()

    await message.answer(
        "📉 Ish qoldirdingizmi?",
        reply_markup=yes_no_keyboard()
    )


# =========================================
# COVER HOURS
# =========================================


@dp.message_handler(
    state=CashierStates.cover_hours
)
async def cover_hours(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.cover.set()

        return await message.answer(
            "🔄 Cover qilganmi?",
            reply_markup=yes_no_keyboard()
        )

    try:

        value = float(text)

    except:

        return await message.answer(
            "❌ Raqam kiriting."
        )

    await state.update_data(
        cover_days=value
    )

    await CashierStates.absent.set()

    await message.answer(
        "📉 Ish qoldirdingizmi?",
        reply_markup=yes_no_keyboard()
    )


# =========================================
# ABSENT
# =========================================


@dp.message_handler(
    state=CashierStates.absent
)
async def get_absent(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.cover.set()

        return await message.answer(
            "🔄 Cover qilganmi?",
            reply_markup=yes_no_keyboard()
        )

    if text == "✅ HA":

        await CashierStates.absent_hours.set()

        return await message.answer(
            "⏰ Necha kun ish qoldirdingiz?",
            reply_markup=manual_keyboard()
        )

    await state.update_data(
        missed_days=0
    )

    await CashierStates.active_students.set()

    await message.answer(
        "👨‍🎓 Active students soni:",
        reply_markup=manual_keyboard()
    )
