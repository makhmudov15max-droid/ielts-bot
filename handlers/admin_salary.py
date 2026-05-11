from aiogram import types
from aiogram.dispatcher import FSMContext

from safety.loader import dp

from keyboards.admin_keyboard import (
    admin_menu
)

from states.admin_states import AdminStates


# =========================================
# START
# =========================================

@dp.message_handler(
    lambda message: message.text == "📊 Admin Salary"
)
async def admin_salary_start(message: types.Message):

    await AdminStates.status.set()

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "🥇 Senior",
        "🥈 Middle"
    )

    keyboard.row(
        "🥉 Junior"
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

@dp.message_handler(state=AdminStates.status)
async def get_status(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        return await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=admin_menu
        )

    statuses = [
        "🥇 Senior",
        "🥈 Middle",
        "🥉 Junior"
    ]

    if text not in statuses:

        return await message.answer(
            "❌ Tugmalardan foydalaning."
        )

    await state.update_data(
        status=text
    )

    await AdminStates.hours.set()

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "6 soat",
        "8 soat"
    )

    keyboard.row(
        "10 soat"
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
# HOURS
# =========================================

@dp.message_handler(state=AdminStates.hours)
async def get_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        return await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=admin_menu
        )

    if text == "⬅️ Ortga":

        await AdminStates.status.set()

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.row(
            "🥇 Senior",
            "🥈 Middle"
        )

        keyboard.row(
            "🥉 Junior"
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

    try:

        hours = int(
            text.split()[0]
        )

    except:

        return await message.answer(
            "❌ Tugmalardan foydalaning."
        )

    await state.update_data(
        hours=hours
    )

    await AdminStates.days.set()

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "26 kun",
        "24 kun"
    )

    keyboard.row(
        "22 kun"
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
# DAYS
# =========================================

@dp.message_handler(state=AdminStates.days)
async def get_days(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        return await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=admin_menu
        )

    if text == "⬅️ Ortga":

        await AdminStates.hours.set()

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.row(
            "6 soat",
            "8 soat"
        )

        keyboard.row(
            "10 soat"
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

        days = int(
            text.split()[0]
        )

    except:

        return await message.answer(
            "❌ Tugmalardan foydalaning."
        )

    await state.update_data(
        days=days
    )

    await AdminStates.kpi.set()

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "120%",
        "100%"
    )

    keyboard.row(
        "80%"
    )

    keyboard.row(
        "🏠 Bosh sahifa",
        "⬅️ Ortga"
    )

    await message.answer(
        """
📈 KPI foizini kiriting:
""",
        reply_markup=keyboard
    )


# =========================================
# KPI
# =========================================

@dp.message_handler(state=AdminStates.kpi)
async def get_kpi(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        return await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=admin_menu
        )

    if text == "⬅️ Ortga":

        await AdminStates.days.set()

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.row(
            "26 kun",
            "24 kun"
        )

        keyboard.row(
            "22 kun"
        )

        keyboard.row(
            "🏠 Bosh sahifa",
            "⬅️ Ortga"
        )

        return await message.answer(
            """
📅 Ishlagan kunni tanlang:
""",
            reply_markup=keyboard
        )

    try:

        kpi = int(
            text.replace("%", "")
        )

    except:

        return await message.answer(
            "❌ Foiz kiriting."
        )

    data = await state.get_data()

    status = data["status"]

    hours = data["hours"]

    days = data["days"]


    # =========================================
    # BASE SALARY
    # =========================================

    if status == "🥇 Senior":

        base = 6000000

    elif status == "🥈 Middle":

        base = 4500000

    else:

        base = 3000000


    # =========================================
    # HOURS BONUS
    # =========================================

    if hours == 8:

        base += 1000000

    elif hours == 10:

        base += 2000000


    # =========================================
    # DAYS BONUS
    # =========================================

    if days >= 26:

        base += 500000


    # =========================================
    # KPI
    # =========================================

    final_salary = (
        base * kpi
    ) / 100


    await state.finish()

    await message.answer(
        f"""
✅ ADMIN SALARY HISOBLANDI

━━━━━━━━━━━━━━━━━━

🏅 Status:
{status}

⏰ Ish vaqti:
{hours} soat

📅 Ish kuni:
{days} kun

📈 KPI:
{kpi}%

━━━━━━━━━━━━━━━━━━

💰 UMUMIY OYLIK

{final_salary:,.0f} UZS
""",
        reply_markup=admin_menu
    )
