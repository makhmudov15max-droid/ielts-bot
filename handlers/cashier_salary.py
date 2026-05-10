from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

from safety.loader import dp

from states.cashier_states import CashierStates
from keyboards.admin_keyboard import cashier_menu


# ================= KEYBOARDS =================

hours_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

hours_keyboard.row(
    KeyboardButton("6"),
    KeyboardButton("7"),
    KeyboardButton("8")
)

hours_keyboard.row(
    KeyboardButton("✍️ Boshqa")
)

hours_keyboard.row(
    KeyboardButton("⬅️ Ortga"),
    KeyboardButton("🏠 Bosh menu")
)


days_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

days_keyboard.row(
    KeyboardButton("24"),
    KeyboardButton("25")
)

days_keyboard.row(
    KeyboardButton("26"),
    KeyboardButton("27")
)

days_keyboard.row(
    KeyboardButton("✍️ Boshqa")
)

days_keyboard.row(
    KeyboardButton("⬅️ Ortga"),
    KeyboardButton("🏠 Bosh menu")
)


yes_no_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

yes_no_keyboard.row(
    KeyboardButton("✅ HA"),
    KeyboardButton("❌ YO‘Q")
)

yes_no_keyboard.row(
    KeyboardButton("⬅️ Ortga"),
    KeyboardButton("🏠 Bosh menu")
)


manual_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

manual_keyboard.row(
    KeyboardButton("⬅️ Ortga"),
    KeyboardButton("🏠 Bosh menu")
)


# ================= GLOBAL =================

@dp.message_handler(text="🏠 Bosh menu", state="*")
async def back_menu(message: types.Message, state: FSMContext):

    await state.finish()

    await message.answer(
        "🏠 Bosh menu",
        reply_markup=cashier_menu
    )


@dp.message_handler(text="💰 Cashier Salary")
async def cashier_start(message: types.Message):

    await message.answer(
        "⏰ Kunlik ish soatini tanlang:",
        reply_markup=hours_keyboard
    )

    await CashierStates.hours.set()


# ================= HOURS =================

@dp.message_handler(state=CashierStates.hours)
async def get_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await state.finish()

        return await message.answer(
            "🏠 Bosh menu",
            reply_markup=cashier_menu
        )

    if text == "✍️ Boshqa":

        await CashierStates.custom_hours.set()

        return await message.answer(
            "⏰ Soat kiriting:",
            reply_markup=manual_keyboard
        )

    try:
        value = float(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        hours=value
    )

    await CashierStates.days.set()

    await message.answer(
        "📅 Ishlagan kunni tanlang:",
        reply_markup=days_keyboard
    )


# ================= CUSTOM HOURS =================

@dp.message_handler(state=CashierStates.custom_hours)
async def custom_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.hours.set()

        return await message.answer(
            "⏰ Kunlik ish soatini tanlang:",
            reply_markup=hours_keyboard
        )

    try:
        value = float(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        hours=value
    )

    await CashierStates.days.set()

    await message.answer(
        "📅 Ishlagan kunni tanlang:",
        reply_markup=days_keyboard
    )


# ================= DAYS =================

@dp.message_handler(state=CashierStates.days)
async def get_days(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.hours.set()

        return await message.answer(
            "⏰ Kunlik ish soatini tanlang:",
            reply_markup=hours_keyboard
        )

    if text == "✍️ Boshqa":

        await CashierStates.custom_days.set()

        return await message.answer(
            "📅 Kun kiriting:",
            reply_markup=manual_keyboard
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


# ================= CUSTOM DAYS =================

@dp.message_handler(state=CashierStates.custom_days)
async def custom_days(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await CashierStates.days.set()

        return await message.answer(
            "📅 Ishlagan kunni tanlang:",
            reply_markup=days_keyboard
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
            reply_markup=days_keyboard
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
            reply_markup=yes_no_keyboard
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
            reply_markup=manual_keyboard
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

    # ================= SALARY =================

    if hours <= 8:

        daily_salary = hours * 15000

    else:

        extra = hours - 8

        daily_salary = (
            8 * 15000
        ) + (
            extra * 20000
        )

    fix_salary = daily_salary * days

    total_students = (
        active_students +
        archive_students
    )

    total_debtors = (
        active_debtors +
        archive_debtors
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

    cover_bonus = (
        cover_hours *
        15000
    )

    penalty = (
        absent_hours *
        15000
    )

    final_salary = (
        salary_with_bonus +
        cover_bonus -
        penalty
    )

    text = f"""
🎉 Oylik hisoblandi!

🧑‍💼 Status: CASHIER

💰 Fixa ........ {int(fix_salary):,}
🏆 KPI Bonus ... {int(salary_with_bonus - fix_salary):,}

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
