from aiogram import types
from aiogram.dispatcher import FSMContext

from safety.loader import dp

from keyboards.admin_keyboard import (
    owner_panel,
    admin_menu
)

from states.admin_states import (
    AdminSalaryStates
)

from calculators.admin_calc import (
    calculate_admin_salary
)


# =========================================
# START
# =========================================

@dp.message_handler(
    lambda message: message.text == "📊 Admin Salary"
)
async def admin_salary_start(message: types.Message):

    await AdminSalaryStates.status.set()

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "NOVA",
        "PRIME"
    )

    keyboard.row(
        "APEX",
        "LEADER"
    )

    keyboard.row(
        "🏠 Bosh sahifa"
    )

    await message.answer(
        """
📊 ADMIN SALARY

━━━━━━━━━━━━━━━━━━

🏅 Status tanlang:
""",
        reply_markup=keyboard
    )


# =========================================
# STATUS
# =========================================

@dp.message_handler(state=AdminSalaryStates.status)
async def get_status(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        return await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=admin_menu
        )

    statuses = [
        "NOVA",
        "PRIME",
        "APEX",
        "LEADER"
    ]

    if text not in statuses:

        return await message.answer(
            "❌ Tugmalardan foydalaning."
        )

    await state.update_data(
        status=text.lower()
    )

    await AdminSalaryStates.daily_hours.set()

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

    await message.answer(
        """
⏰ Kunlik ish soatini tanlang:
""",
        reply_markup=keyboard
    )


# =========================================
# DAILY HOURS
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.daily_hours
)
async def get_daily_hours(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        return await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=admin_menu
        )

    if text == "⬅️ Ortga":

        await AdminSalaryStates.status.set()

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.row(
            "NOVA",
            "PRIME"
        )

        keyboard.row(
            "APEX",
            "LEADER"
        )

        keyboard.row(
            "🏠 Bosh sahifa"
        )

        return await message.answer(
            """
🏅 Status tanlang:
""",
            reply_markup=keyboard
        )

    if text == "✍️ Boshqa":

        await AdminSalaryStates.custom_daily_hours.set()

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.row(
            "🏠 Bosh sahifa",
            "⬅️ Ortga"
        )

        return await message.answer(
            "⏰ Soat kiriting:",
            reply_markup=keyboard
        )

    try:

        value = float(text)

    except:

        return await message.answer(
            "❌ Tugmalardan foydalaning."
        )

    await state.update_data(
        daily_hours=value
    )

    await AdminSalaryStates.worked_days.set()

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

    await message.answer(
        """
📅 Ishlagan kunni tanlang:
""",
        reply_markup=keyboard
    )


# =========================================
# CUSTOM HOURS
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.custom_daily_hours
)
async def custom_daily_hours(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.daily_hours.set()

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

        return await message.answer(
            """
⏰ Kunlik ish soatini tanlang:
""",
            reply_markup=keyboard
        )

    try:

        value = float(text)

    except:

        return await message.answer(
            "❌ Raqam kiriting."
        )

    await state.update_data(
        daily_hours=value
    )

    await AdminSalaryStates.worked_days.set()

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

    await message.answer(
        """
📅 Ishlagan kunni tanlang:
""",
        reply_markup=keyboard
    )
