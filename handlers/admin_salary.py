from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

from safety.loader import dp

from states.admin_states import AdminSalaryStates
from calculators.admin_calc import calculate_admin_salary
from keyboards.admin_keyboard import owner_menu


# ================= KEYBOARDS =================

status_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

status_keyboard.row(
    KeyboardButton("nova"),
    KeyboardButton("prime")
)

status_keyboard.row(
    KeyboardButton("apex"),
    KeyboardButton("leader")
)

status_keyboard.row(
    KeyboardButton("⬅️ Ortga"),
    KeyboardButton("🏠 Bosh menu")
)


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


conversion_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

conversion_keyboard.row(
    KeyboardButton("50%")
)

conversion_keyboard.row(
    KeyboardButton("✍️ Boshqa")
)

conversion_keyboard.row(
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


# ================= HELPERS =================

async def finish_salary(message, state):

    data = await state.get_data()

    result = calculate_admin_salary(data)

    text = f"""
🎉 Oylik hisoblandi!

🧑‍💼 Status: {data['status'].upper()}

💰 Fixa ........ {result['fixa']:,}
🏆 KPI Bonus ... {result['final_kpi_bonus']:,}

🎁 Qo‘shimchalar
🇷🇺 Rus tili ..... +{result['russian_bonus']:,}
🎓 IELTS ........ +{result['ielts_bonus']:,}
🔄 Cover ........ +{result['cover_bonus']:,}

⚠️ Jarima
📉 Missed ....... -{result['penalty']:,}

━━━━━━━━━━━━

💎 Yakuniy oylik:

🔥 {result['total_salary']:,} so'm
"""

    await message.answer(
        text,
        reply_markup=owner_menu
    )

    await state.finish()


# ================= GLOBAL =================

@dp.message_handler(text="🏠 Bosh menu", state="*")
async def back_menu(message: types.Message, state: FSMContext):

    await state.finish()

    await message.answer(
        "🏠 Bosh menu",
        reply_markup=owner_menu
    )


@dp.message_handler(text="📊 Admin Salary")
async def start_salary(message: types.Message):

    await message.answer(
        "🏅 Status tanlang:",
        reply_markup=status_keyboard
    )

    await AdminSalaryStates.status.set()


# ================= STATUS =================

@dp.message_handler(state=AdminSalaryStates.status)
async def get_status(message: types.Message, state: FSMContext):

    text = message.text.lower()

    if text == "⬅️ ortga":

        await state.finish()

        return await message.answer(
            "🏠 Bosh menu",
            reply_markup=owner_menu
        )

    if text not in [
        "nova",
        "prime",
        "apex",
        "leader"
    ]:
        return await message.answer(
            "Tugmalardan foydalaning"
        )

    await state.update_data(
        status=text
    )

    await message.answer(
        "⏰ Kunlik ish soatini tanlang:",
        reply_markup=hours_keyboard
    )

    await AdminSalaryStates.daily_hours.set()


# ================= DAILY HOURS =================

@dp.message_handler(state=AdminSalaryStates.daily_hours)
async def get_daily_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "🏅 Status tanlang:",
            reply_markup=status_keyboard
        )

        return await AdminSalaryStates.status.set()

    if text == "✍️ Boshqa":

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
        daily_hours=value
    )

    await message.answer(
        "📅 Ishlagan kunni tanlang:",
        reply_markup=days_keyboard
    )

    await AdminSalaryStates.worked_days.set()


# ================= WORKED DAYS =================

@dp.message_handler(state=AdminSalaryStates.worked_days)
async def get_worked_days(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "⏰ Kunlik ish soatini tanlang:",
            reply_markup=hours_keyboard
        )

        return await AdminSalaryStates.daily_hours.set()

    if text == "✍️ Boshqa":

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
        worked_days=value
    )

    await message.answer(
        "🎯 Individual plan kiriting:",
        reply_markup=manual_keyboard
    )

    await AdminSalaryStates.individual_plan.set()


# ================= INDIVIDUAL PLAN =================

@dp.message_handler(state=AdminSalaryStates.individual_plan)
async def get_individual_plan(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "📅 Ishlagan kunni tanlang:",
            reply_markup=days_keyboard
        )

        return await AdminSalaryStates.worked_days.set()

    try:
        value = float(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        individual_plan=value
    )

    await message.answer(
        "💰 Actual sales kiriting:",
        reply_markup=manual_keyboard
    )

    await AdminSalaryStates.actual_sales.set()


# ================= ACTUAL SALES =================

@dp.message_handler(state=AdminSalaryStates.actual_sales)
async def get_actual_sales(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "🎯 Individual plan kiriting:",
            reply_markup=manual_keyboard
        )

        return await AdminSalaryStates.individual_plan.set()

    try:
        value = float(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        actual_sales=value
    )

    await message.answer(
        "📈 Conversion plan tanlang:",
        reply_markup=conversion_keyboard
    )

    await AdminSalaryStates.conversion_plan.set()


# ================= CONVERSION PLAN =================

@dp.message_handler(state=AdminSalaryStates.conversion_plan)
async def get_conversion_plan(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "💰 Actual sales kiriting:",
            reply_markup=manual_keyboard
        )

        return await AdminSalaryStates.actual_sales.set()

    if text == "50%":

        value = 50

    elif text == "✍️ Boshqa":

        return await message.answer(
            "📈 Conversion plan kiriting:",
            reply_markup=manual_keyboard
        )

    else:

        try:
            value = float(
                text.replace("%", "")
            )
        except:
            return await message.answer(
                "Faqat raqam kiriting"
            )

    await state.update_data(
        conversion_plan=value
    )

    await message.answer(
        "📊 Actual conversion kiriting:",
        reply_markup=manual_keyboard
    )

    await AdminSalaryStates.actual_conversion.set()


# ================= ACTUAL CONVERSION =================

@dp.message_handler(state=AdminSalaryStates.actual_conversion)
async def get_actual_conversion(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "📈 Conversion plan tanlang:",
            reply_markup=conversion_keyboard
        )

        return await AdminSalaryStates.conversion_plan.set()

    try:
        value = float(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        actual_conversion=value
    )

    await message.answer(
        "👥 Active plan kiriting:",
        reply_markup=manual_keyboard
    )

    await AdminSalaryStates.active_plan.set()


# ================= ACTIVE PLAN =================

@dp.message_handler(state=AdminSalaryStates.active_plan)
async def get_active_plan(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "📊 Actual conversion kiriting:",
            reply_markup=manual_keyboard
        )

        return await AdminSalaryStates.actual_conversion.set()

    try:
        value = float(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        active_plan=value
    )

    await message.answer(
        "🔥 Actual active kiriting:",
        reply_markup=manual_keyboard
    )

    await AdminSalaryStates.actual_active.set()


# ================= ACTUAL ACTIVE =================

@dp.message_handler(state=AdminSalaryStates.actual_active)
async def get_actual_active(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "👥 Active plan kiriting:",
            reply_markup=manual_keyboard
        )

        return await AdminSalaryStates.active_plan.set()

    try:
        value = float(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        actual_active=value
    )

    await message.answer(
        "🇷🇺 Rus tili biladimi?",
        reply_markup=yes_no_keyboard
    )

    await AdminSalaryStates.knows_russian.set()


# ================= RUSSIAN =================

@dp.message_handler(state=AdminSalaryStates.knows_russian)
async def get_russian(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "🔥 Actual active kiriting:",
            reply_markup=manual_keyboard
        )

        return await AdminSalaryStates.actual_active.set()

    if text not in [
        "✅ HA",
        "❌ YO‘Q"
    ]:
        return await message.answer(
            "Tugmalardan foydalaning"
        )

    await state.update_data(
        knows_russian=text == "✅ HA"
    )

    await message.answer(
        "🎓 IELTS 7+ bormi?",
        reply_markup=yes_no_keyboard
    )

    await AdminSalaryStates.has_ielts.set()


# ================= IELTS =================

@dp.message_handler(state=AdminSalaryStates.has_ielts)
async def get_ielts(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "🇷🇺 Rus tili biladimi?",
            reply_markup=yes_no_keyboard
        )

        return await AdminSalaryStates.knows_russian.set()

    if text not in [
        "✅ HA",
        "❌ YO‘Q"
    ]:
        return await message.answer(
            "Tugmalardan foydalaning"
        )

    await state.update_data(
        has_ielts=text == "✅ HA"
    )

    await message.answer(
        "🔄 Cover qilganmi?",
        reply_markup=yes_no_keyboard
    )

    await AdminSalaryStates.cover_hours.set()


# ================= COVER ASK =================

@dp.message_handler(state=AdminSalaryStates.cover_hours)
async def ask_cover(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "🎓 IELTS 7+ bormi?",
            reply_markup=yes_no_keyboard
        )

        return await AdminSalaryStates.has_ielts.set()

    if text == "✅ HA":

        await message.answer(
            "⏰ Necha soat cover qildingiz?",
            reply_markup=manual_keyboard
        )

        return await AdminSalaryStates.cover_input.set()

    if text == "❌ YO‘Q":

        await state.update_data(
            cover_hours=0
        )

        await message.answer(
            "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
            reply_markup=yes_no_keyboard
        )

        return await AdminSalaryStates.missed_hours.set()

    return await message.answer(
        "Tugmalardan foydalaning"
    )


# ================= COVER INPUT =================

@dp.message_handler(state=AdminSalaryStates.cover_input)
async def cover_input(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "🔄 Cover qilganmi?",
            reply_markup=yes_no_keyboard
        )

        return await AdminSalaryStates.cover_hours.set()

    try:
        value = float(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        cover_hours=value
    )

    await message.answer(
        "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
        reply_markup=yes_no_keyboard
    )

    await AdminSalaryStates.missed_hours.set()


# ================= MISSED ASK =================

@dp.message_handler(state=AdminSalaryStates.missed_hours)
async def ask_missed(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "🔄 Cover qilganmi?",
            reply_markup=yes_no_keyboard
        )

        return await AdminSalaryStates.cover_hours.set()

    if text == "✅ HA":

        await message.answer(
            "⏰ Necha soat ish qoldirdingiz?",
            reply_markup=manual_keyboard
        )

        return await AdminSalaryStates.missed_input.set()

    if text == "❌ YO‘Q":

        await state.update_data(
            missed_hours=0
        )

        return await finish_salary(
            message,
            state
        )

    return await message.answer(
        "Tugmalardan foydalaning"
    )


# ================= MISSED INPUT =================

@dp.message_handler(state=AdminSalaryStates.missed_input)
async def missed_input(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await message.answer(
            "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
            reply_markup=yes_no_keyboard
        )

        return await AdminSalaryStates.missed_hours.set()

    try:
        value = float(text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        missed_hours=value
    )

    await finish_salary(
        message,
        state
    )
