from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

from safety.loader import dp

from states.admin_states import AdminSalaryStates

from calculators.admin_calc import (
    calculate_admin_salary
)

from keyboards.admin_keyboard import (
    owner_panel,
    admin_menu
)


# ================= MENUS =================

status_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

status_keyboard.row(
    KeyboardButton("NOVA"),
    KeyboardButton("PRIME")
)

status_keyboard.row(
    KeyboardButton("APEX"),
    KeyboardButton("LEADER")
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

    if message.from_user.id:

        await message.answer(
            "🏠 Bosh menu",
            reply_markup=owner_panel
        )


# ================= START =================

@dp.message_handler(text="📊 Admin Salary")
async def admin_salary_start(message: types.Message):

    await message.answer(
        "🏅 Status tanlang:",
        reply_markup=status_keyboard
    )

    await AdminSalaryStates.status.set()


# ================= STATUS =================

@dp.message_handler(state=AdminSalaryStates.status)
async def get_status(message: types.Message, state: FSMContext):

    text = message.text.lower()

    if message.text == "⬅️ Ortga":

        await state.finish()

        return await message.answer(
            "🏠 Bosh menu",
            reply_markup=owner_panel
        )

    statuses = [
        "nova",
        "prime",
        "apex",
        "leader"
    ]

    if text not in statuses:

        return await message.answer(
            "Statusni tugmadan tanlang"
        )

    await state.update_data(
        status=text
    )

    await AdminSalaryStates.daily_hours.set()

    await message.answer(
        "⏰ Kunlik ish soatini tanlang:",
        reply_markup=hours_keyboard
    )


# ================= DAILY HOURS =================

@dp.message_handler(state=AdminSalaryStates.daily_hours)
async def get_daily_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.status.set()

        return await message.answer(
            "🏅 Status tanlang:",
            reply_markup=status_keyboard
        )

    if text == "✍️ Boshqa":

        await AdminSalaryStates.custom_daily_hours.set()

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

    await AdminSalaryStates.worked_days.set()

    await message.answer(
        "📅 Ishlagan kunni tanlang:",
        reply_markup=days_keyboard
    )


# ================= CUSTOM HOURS =================

@dp.message_handler(state=AdminSalaryStates.custom_daily_hours)
async def custom_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.daily_hours.set()

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
        daily_hours=value
    )

    await AdminSalaryStates.worked_days.set()

    await message.answer(
        "📅 Ishlagan kunni tanlang:",
        reply_markup=days_keyboard
    )


# ================= WORKED DAYS =================

@dp.message_handler(state=AdminSalaryStates.worked_days)
async def get_days(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.daily_hours.set()

        return await message.answer(
            "⏰ Kunlik ish soatini tanlang:",
            reply_markup=hours_keyboard
        )

    if text == "✍️ Boshqa":

        await AdminSalaryStates.custom_worked_days.set()

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

    await AdminSalaryStates.individual_plan.set()

    await message.answer(
        "🎯 Individual plan kiriting:",
        reply_markup=manual_keyboard
    )


# ================= CUSTOM DAYS =================

@dp.message_handler(state=AdminSalaryStates.custom_worked_days)
async def custom_days(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.worked_days.set()

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
        worked_days=value
    )

    await AdminSalaryStates.individual_plan.set()

    await message.answer(
        "🎯 Individual plan kiriting:",
        reply_markup=manual_keyboard
    )


# ================= UNIVERSAL NUMBER HANDLER =================

async def handle_number(
    message,
    state,
    key,
    next_state,
    question,
    back_state=None,
    back_question=None,
    back_keyboard=None,
    keyboard=manual_keyboard
):

    text = message.text

    if text == "⬅️ Ortga" and back_state:

        await back_state.set()

        return await message.answer(
            back_question,
            reply_markup=back_keyboard
        )

    try:
        value = float(
            text.replace("%", "")
        )

    except:

        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(
        **{key: value}
    )

    await next_state.set()

    await message.answer(
        question,
        reply_markup=keyboard
    )


# ================= KPI FLOW =================

@dp.message_handler(state=AdminSalaryStates.individual_plan)
async def individual_plan(message: types.Message, state: FSMContext):

    await handle_number(
        message,
        state,
        "individual_plan",
        AdminSalaryStates.actual_sales,
        "💰 Actual sales kiriting:",
        AdminSalaryStates.worked_days,
        "📅 Ishlagan kunni tanlang:",
        days_keyboard
    )


@dp.message_handler(state=AdminSalaryStates.actual_sales)
async def actual_sales(message: types.Message, state: FSMContext):

    await handle_number(
        message,
        state,
        "actual_sales",
        AdminSalaryStates.conversion_plan,
        "📈 Conversion plan tanlang:",
        AdminSalaryStates.individual_plan,
        "🎯 Individual plan kiriting:",
        manual_keyboard,
        conversion_keyboard
    )


@dp.message_handler(state=AdminSalaryStates.conversion_plan)
async def conversion_plan(message: types.Message, state: FSMContext):

    await handle_number(
        message,
        state,
        "conversion_plan",
        AdminSalaryStates.actual_conversion,
        "📊 Actual conversion kiriting:",
        AdminSalaryStates.actual_sales,
        "💰 Actual sales kiriting:",
        manual_keyboard
    )


@dp.message_handler(state=AdminSalaryStates.actual_conversion)
async def actual_conversion(message: types.Message, state: FSMContext):

    await handle_number(
        message,
        state,
        "actual_conversion",
        AdminSalaryStates.active_plan,
        "👥 Active plan kiriting:",
        AdminSalaryStates.conversion_plan,
        "📈 Conversion plan tanlang:",
        conversion_keyboard
    )


@dp.message_handler(state=AdminSalaryStates.active_plan)
async def active_plan(message: types.Message, state: FSMContext):

    await handle_number(
        message,
        state,
        "active_plan",
        AdminSalaryStates.actual_active,
        "🔥 Actual active kiriting:",
        AdminSalaryStates.actual_conversion,
        "📊 Actual conversion kiriting:",
        manual_keyboard
    )


@dp.message_handler(state=AdminSalaryStates.actual_active)
async def actual_active(message: types.Message, state: FSMContext):

    await handle_number(
        message,
        state,
        "actual_active",
        AdminSalaryStates.cover,
        "🔄 Cover qilganmi?",
        AdminSalaryStates.active_plan,
        "👥 Active plan kiriting:",
        manual_keyboard,
        yes_no_keyboard
    )


# ================= COVER =================

@dp.message_handler(state=AdminSalaryStates.cover)
async def cover(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.actual_active.set()

        return await message.answer(
            "🔥 Actual active kiriting:",
            reply_markup=manual_keyboard
        )

    if text == "✅ HA":

        await AdminSalaryStates.cover_hours.set()

        return await message.answer(
            "⏰ Necha soat cover qildingiz?",
            reply_markup=manual_keyboard
        )

    if text == "❌ YO‘Q":

        await state.update_data(
            cover_hours=0
        )

        await AdminSalaryStates.has_ielts.set()

        return await message.answer(
            "🎓 IELTS 7+ bormi?",
            reply_markup=yes_no_keyboard
        )


# ================= COVER HOURS =================

@dp.message_handler(state=AdminSalaryStates.cover_hours)
async def cover_hours(message: types.Message, state: FSMContext):

    await handle_number(
        message,
        state,
        "cover_hours",
        AdminSalaryStates.has_ielts,
        "🎓 IELTS 7+ bormi?",
        AdminSalaryStates.cover,
        "🔄 Cover qilganmi?",
        yes_no_keyboard,
        yes_no_keyboard
    )


# ================= IELTS =================

@dp.message_handler(state=AdminSalaryStates.has_ielts)
async def has_ielts(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.cover.set()

        return await message.answer(
            "🔄 Cover qilganmi?",
            reply_markup=yes_no_keyboard
        )

    await state.update_data(
        has_ielts=text == "✅ HA"
    )

    await AdminSalaryStates.knows_russian.set()

    await message.answer(
        "🇷🇺 Rus tili biladimi?",
        reply_markup=yes_no_keyboard
    )


# ================= RUSSIAN =================

@dp.message_handler(state=AdminSalaryStates.knows_russian)
async def russian(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.has_ielts.set()

        return await message.answer(
            "🎓 IELTS 7+ bormi?",
            reply_markup=yes_no_keyboard
        )

    await state.update_data(
        knows_russian=text == "✅ HA"
    )

    await AdminSalaryStates.missed.set()

    await message.answer(
        "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
        reply_markup=yes_no_keyboard
    )


# ================= MISSED =================

@dp.message_handler(state=AdminSalaryStates.missed)
async def missed(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.knows_russian.set()

        return await message.answer(
            "🇷🇺 Rus tili biladimi?",
            reply_markup=yes_no_keyboard
        )

    if text == "✅ HA":

        await AdminSalaryStates.missed_hours.set()

        return await message.answer(
            "⏰ Necha soat ish qoldirdingiz?",
            reply_markup=manual_keyboard
        )

    if text == "❌ YO‘Q":

        await state.update_data(
            missed_hours=0
        )

        data = await state.get_data()

        result = calculate_admin_salary(
            data
        )

        total = result[
            "total_salary"
        ]

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

🔥 {total:,} so'm
"""

        await message.answer(
            text,
            reply_markup=owner_panel
        )

        return await state.finish()


# ================= MISSED HOURS =================

@dp.message_handler(state=AdminSalaryStates.missed_hours)
async def missed_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.missed.set()

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
        missed_hours=value
    )

    data = await state.get_data()

    result = calculate_admin_salary(
        data
    )

    total = result[
        "total_salary"
    ]

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

🔥 {total:,} so'm
"""

    await message.answer(
        text,
        reply_markup=owner_panel
    )

    await state.finish()
