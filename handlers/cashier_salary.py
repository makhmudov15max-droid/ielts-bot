import json

from aiogram import types
from aiogram.dispatcher import FSMContext

from safety.loader import dp

from calculators.cashier_calc import (
    calculate_cashier_salary
)

from states.cashier_states import (
    CashierStates
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
            """
⏰ Kunlik ish soatini tanlang:
""",
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
        """
📅 Ishlagan kunni tanlang:
""",
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
            """
📅 Ishlagan kunni tanlang:
""",
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


# ================= CUSTOM DAYS =================

@dp.message_handler(state=CashierStates.custom_days)
async def custom_days(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.days.set()

        return await message.answer(
            "📅 Ishlagan kunni tanlang:",
            reply_markup=days_keyboard()
        )

    try:
        value = int(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        days=value
    )

    await CashierStates.cover.set()

    await message.answer(
        "🔄 Cover qilganmi?",
        reply_markup=yes_no_keyboard
    )


# ================= COVER =================

@dp.message_handler(state=CashierStates.cover)
async def get_cover(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.days.set()

        return await message.answer(
            "📅 Ishlagan kunni tanlang:",
            reply_markup=days_keyboard()
        )

    if text == "✅ HA":

        await CashierStates.cover_input.set()

        return await message.answer(
            "⏰ Necha soat cover qildingiz?",
            reply_markup=manual_keyboard
        )

    if text == "❌ YO‘Q":

        await state.update_data(
            cover_hours=0
        )

        await CashierStates.absent.set()

        return await message.answer(
            "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
            reply_markup=yes_no_keyboard()
        )

    return await message.answer(
        "Tugmalardan foydalaning"
    )


# ================= COVER INPUT =================

@dp.message_handler(state=CashierStates.cover_input)
async def get_cover_input(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.cover.set()

        return await message.answer(
            "🔄 Cover qilganmi?",
            reply_markup=yes_no_keyboard
        )

    try:
        value = float(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        cover_hours=value
    )

    await CashierStates.absent.set()

    await message.answer(
        "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
        reply_markup=yes_no_keyboard
    )


# ================= ABSENT =================

@dp.message_handler(state=CashierStates.absent)
async def get_absent(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.cover.set()

        return await message.answer(
            "🔄 Cover qilganmi?",
            reply_markup=yes_no_keyboard
        )

    if text == "✅ HA":

        await CashierStates.absent_input.set()

        return await message.answer(
            "⏰ Necha soat ish qoldirdingiz?",
            reply_markup=manual_keyboard()
        )

    if text == "❌ YO‘Q":

        await state.update_data(
            absent_hours=0
        )

        await CashierStates.active_students.set()

        return await message.answer(
            "🟢 Aktiv students sonini kiriting:",
            reply_markup=manual_keyboard
        )

    return await message.answer(
        "Tugmalardan foydalaning"
    )


# ================= ABSENT INPUT =================

@dp.message_handler(state=CashierStates.absent_input)
async def get_absent_input(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.absent.set()

        return await message.answer(
            "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
            reply_markup=yes_no_keyboard
        )

    try:
        value = float(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        absent_hours=value
    )

    await CashierStates.active_students.set()

    await message.answer(
        "🟢 Aktiv students sonini kiriting:",
        reply_markup=manual_keyboard
    )


# ================= ACTIVE STUDENTS =================

@dp.message_handler(state=CashierStates.active_students)
async def active_students(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.absent.set()

        return await message.answer(
            "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
            reply_markup=yes_no_keyboard
        )

    try:
        value = int(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        active_students=value
    )

    await CashierStates.active_debtors.set()

    await message.answer(
        "💳 Aktiv qarzdorlar sonini kiriting:",
        reply_markup=manual_keyboard
    )


# ================= ACTIVE DEBTORS =================

@dp.message_handler(state=CashierStates.active_debtors)
async def active_debtors(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.active_students.set()

        return await message.answer(
            "🟢 Aktiv students sonini kiriting:",
            reply_markup=manual_keyboard
        )

    try:
        value = int(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        active_debtors=value
    )

    await CashierStates.archive_students.set()

    await message.answer(
        "📦 Archive students sonini kiriting:",
        reply_markup=manual_keyboard
    )


# ================= ARCHIVE STUDENTS =================

@dp.message_handler(state=CashierStates.archive_students)
async def archive_students(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.active_debtors.set()

        return await message.answer(
            "💳 Aktiv qarzdorlar sonini kiriting:",
            reply_markup=manual_keyboard
        )

    try:
        value = int(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        archive_students=value
    )

    await CashierStates.archive_debtors.set()

    await message.answer(
        "🧾 Archive qarzdorlar sonini kiriting:",
        reply_markup=manual_keyboard
    )


# ================= FINAL =================

@dp.message_handler(state=CashierStates.archive_debtors)
async def finish_cashier(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.archive_students.set()

        return await message.answer(
            "📦 Archive students sonini kiriting:",
            reply_markup=manual_keyboard
        )

    try:
        archive_debtors = int(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    data = await state.get_data()

    hours = data["hours"]
    days = data["days"]

    cover_hours = data["cover_hours"]
    absent_hours = data["absent_hours"]

    active_students = data["active_students"]
    active_debtors = data["active_debtors"]

    archive_students = data["archive_students"]

    # ================= FIXA =================

    if hours <= 8:

        daily_salary = hours * 15000

    else:

        extra = hours - 8

        daily_salary = (
            (8 * 15000)
            + (extra * 20000)
        )

    fix_salary = (
        daily_salary * days
    )

    # ================= KPI =================

    total_students = (
        active_students
        + archive_students
    )

    total_debtors = (
        active_debtors
        + archive_debtors
    )

    if total_students == 0:

        debt_percent = 0

    else:

        debt_percent = (
            total_debtors /
            total_students
        ) * 100

    if debt_percent == 0:
        multiplier = 2.5

    elif debt_percent <= 2:
        multiplier = 2.0

    elif debt_percent <= 5:
        multiplier = 1.8

    elif debt_percent <= 7:
        multiplier = 1.7

    elif debt_percent <= 10:
        multiplier = 1.6

    elif debt_percent <= 15:
        multiplier = 1.5

    elif debt_percent <= 20:
        multiplier = 1.4

    elif debt_percent <= 30:
        multiplier = 1.2

    else:
        multiplier = 1.0

    salary_with_bonus = (
        fix_salary *
        multiplier
    )

    kpi_bonus = (
        salary_with_bonus -
        fix_salary
    )

    # ================= BONUS =================

    cover_bonus = (
        cover_hours * 15000
    )

    penalty = (
        absent_hours * 15000
    )

    final_salary = (
        salary_with_bonus
        + cover_bonus
        - penalty
    )

    # ================= UI =================

    text = f"""
🎉 Oylik hisoblandi!

🧑‍💼 Status: CASHIER

💰 Fixa ........ {int(fix_salary):,}
🏆 KPI Bonus ... {int(kpi_bonus):,}

📊 KPI Natijalari
📉 Qarzdorlik ... {debt_percent:.1f}%
📈 Koeffitsient . {multiplier}x

🎁 Qo‘shimchalar
🔄 Cover ........ +{int(cover_bonus):,}

⚠️ Jarima
📉 Missed ....... -{int(penalty):,}

━━━━━━━━━━━━

💎 Yakuniy oylik:

🔥 {int(final_salary):,} so'm
"""

    await message.answer(
        text,
        reply_markup=cashier_menu
    )

    await state.finish()
