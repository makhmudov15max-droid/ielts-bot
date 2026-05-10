from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from safety.loader import dp

from states.admin_states import AdminSalaryStates
from calculators.admin_calc import calculate_admin_salary
from keyboards.admin_keyboard import owner_menu


# ---------------- KEYBOARDS ----------------

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
    KeyboardButton("✍️ Boshqa")
)

conversion_keyboard.row(
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
    KeyboardButton("⬅️ Ortga")
)

yes_no_keyboard.row(
    KeyboardButton("🏠 Bosh menu")
)


manual_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

manual_keyboard.row(
    KeyboardButton("⬅️ Ortga"),
    KeyboardButton("🏠 Bosh menu")
)


# ---------------- GLOBAL BUTTONS ----------------

@dp.message_handler(text="🏠 Bosh menu", state="*")
async def back_to_menu(message: types.Message, state: FSMContext):

    await state.finish()

    await message.answer(
        "🏠 Bosh menu",
        reply_markup=owner_menu
    )


@dp.message_handler(text="📊 Admin Salary")
async def start_admin_salary(message: types.Message, state: FSMContext):

    await state.finish()

    await message.answer(
        "🏅 Status tanlang:",
        reply_markup=status_keyboard
    )

    await AdminSalaryStates.status.set()


# ---------------- STATUS ----------------

@dp.message_handler(state=AdminSalaryStates.status)
async def get_status(message: types.Message, state: FSMContext):

    text = message.text.lower()

    if text not in ["nova", "prime", "apex", "leader"]:
        return await message.answer(
            "Tugmalardan birini tanlang"
        )

    await state.update_data(status=text)

    await message.answer(
        "⏰ Kunlik ish soatini tanlang:",
        reply_markup=hours_keyboard
    )

    await AdminSalaryStates.daily_hours.set()


# ---------------- DAILY HOURS ----------------

@dp.message_handler(state=AdminSalaryStates.daily_hours)
async def get_daily_hours(message: types.Message, state: FSMContext):

    text = message.text

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

    await state.update_data(daily_hours=value)

    await message.answer(
        "📅 Ishlagan kunni tanlang:",
        reply_markup=days_keyboard
    )

    await AdminSalaryStates.worked_days.set()


# ---------------- WORKED DAYS ----------------

@dp.message_handler(state=AdminSalaryStates.worked_days)
async def get_worked_days(message: types.Message, state: FSMContext):

    text = message.text

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

    await state.update_data(worked_days=value)

    await message.answer(
        "🎯 Individual plan kiriting:",
        reply_markup=manual_keyboard
    )

    await AdminSalaryStates.individual_plan.set()


# ---------------- INDIVIDUAL PLAN ----------------

@dp.message_handler(state=AdminSalaryStates.individual_plan)
async def get_individual_plan(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(individual_plan=value)

    await message.answer(
        "💰 Actual sales kiriting:",
        reply_markup=manual_keyboard
    )

    await AdminSalaryStates.actual_sales.set()


# ---------------- ACTUAL SALES ----------------

@dp.message_handler(state=AdminSalaryStates.actual_sales)
async def get_actual_sales(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(actual_sales=value)

    await message.answer(
        "📈 Conversion plan tanlang:",
        reply_markup=conversion_keyboard
    )

    await AdminSalaryStates.conversion_plan.set()


# ---------------- CONVERSION PLAN ----------------

@dp.message_handler(state=AdminSalaryStates.conversion_plan)
async def get_conversion_plan(message: types.Message, state: FSMContext):

    text = message.text

    if text == "50%":
        value = 50

    elif text == "✍️ Boshqa":

        return await message.answer(
            "📈 Conversion plan kiriting:",
            reply_markup=manual_keyboard
        )

    else:

        try:
            value = float(text.replace("%", ""))
        except:
            return await message.answer(
                "Faqat raqam kiriting"
            )

    await state.update_data(conversion_plan=value)

    await message.answer(
        "📊 Actual conversion kiriting:",
        reply_markup=manual_keyboard
    )

    await AdminSalaryStates.actual_conversion.set()


# ---------------- ACTUAL CONVERSION ----------------

@dp.message_handler(state=AdminSalaryStates.actual_conversion)
async def get_actual_conversion(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(actual_conversion=value)

    await message.answer(
        "👥 Active plan kiriting:",
        reply_markup=manual_keyboard
    )

    await AdminSalaryStates.active_plan.set()


# ---------------- ACTIVE PLAN ----------------

@dp.message_handler(state=AdminSalaryStates.active_plan)
async def get_active_plan(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(active_plan=value)

    await message.answer(
        "🔥 Actual active kiriting:",
        reply_markup=manual_keyboard
    )

    await AdminSalaryStates.actual_active.set()


# ---------------- ACTUAL ACTIVE ----------------

@dp.message_handler(state=AdminSalaryStates.actual_active)
async def get_actual_active(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(actual_active=value)

    await message.answer(
        "🇷🇺 Rus tili biladimi?",
        reply_markup=yes_no_keyboard
    )

    await AdminSalaryStates.knows_russian.set()


# ---------------- RUSSIAN ----------------

@dp.message_handler(state=AdminSalaryStates.knows_russian)
async def get_russian(message: types.Message, state: FSMContext):

    text = message.text

    if text not in ["✅ HA", "❌ YO‘Q"]:
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


# ---------------- IELTS ----------------

@dp.message_handler(state=AdminSalaryStates.has_ielts)
async def get_ielts(message: types.Message, state: FSMContext):

    text = message.text

    if text not in ["✅ HA", "❌ YO‘Q"]:
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


# ---------------- COVER ----------------

@dp.message_handler(state=AdminSalaryStates.cover_hours)
async def get_cover_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "✅ HA":

        await message.answer(
            "⏰ Necha soat cover qildingiz?",
            reply_markup=manual_keyboard
        )

        return

    if text == "❌ YO‘Q":

        await state.update_data(
            cover_hours=0
        )

        await message.answer(
            "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
            reply_markup=yes_no_keyboard
        )

        await AdminSalaryStates.missed_hours.set()

        return

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


# ---------------- MISSED HOURS ----------------

@dp.message_handler(state=AdminSalaryStates.missed_hours)
async def get_missed_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "✅ HA":

        return await message.answer(
            "⏰ Necha soat ish qoldirdingiz?",
            reply_markup=manual_keyboard
        )

    if text == "❌ YO‘Q":

        await state.update_data(
            missed_hours=0
        )

        data = await state.get_data()

        result = calculate_admin_salary(data)

        final_text = f"""
╔══════════════════╗
      📊 ADMIN SALARY
╚══════════════════╝

🏅 STATUS
└ {data['status'].upper()}

━━━━━━━━━━━━━━━━━━

💰 FIXA
└ {result['fixa']:,} so'm

📈 INDIVIDUAL KPI
└ {result['individual_kpi']}%

📈 CONVERSION KPI
└ {result['conversion_kpi']}%

📈 ACTIVE KPI
└ {result['active_kpi']}%

📊 WEIGHTED KPI
└ {result['weighted_kpi']}%

━━━━━━━━━━━━━━━━━━

💵 KPI RATE
└ {result['bonus_rate']:,}

🎯 BASE KPI BONUS
└ {result['base_kpi_bonus']:,} so'm

🏆 FINAL KPI BONUS
└ {result['final_kpi_bonus']:,} so'm

━━━━━━━━━━━━━━━━━━

🇷🇺 RUSSIAN BONUS
└ {result['russian_bonus']:,} so'm

🎓 IELTS BONUS
└ {result['ielts_bonus']:,} so'm

🔄 COVER BONUS
└ {result['cover_bonus']:,} so'm

📉 PENALTY
└ {result['penalty']:,} so'm

━━━━━━━━━━━━━━━━━━

💎 JAMI OYLIK:
{result['total_salary']:,} so'm
"""

        await message.answer(
            final_text,
            reply_markup=owner_menu
        )

        await state.finish()

        return

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

    result = calculate_admin_salary(data)

    final_text = f"""
╔══════════════════╗
      📊 ADMIN SALARY
╚══════════════════╝

🏅 STATUS
└ {data['status'].upper()}

━━━━━━━━━━━━━━━━━━

💰 FIXA
└ {result['fixa']:,} so'm

📈 INDIVIDUAL KPI
└ {result['individual_kpi']}%

📈 CONVERSION KPI
└ {result['conversion_kpi']}%

📈 ACTIVE KPI
└ {result['active_kpi']}%

📊 WEIGHTED KPI
└ {result['weighted_kpi']}%

━━━━━━━━━━━━━━━━━━

💵 KPI RATE
└ {result['bonus_rate']:,}

🎯 BASE KPI BONUS
└ {result['base_kpi_bonus']:,} so'm

🏆 FINAL KPI BONUS
└ {result['final_kpi_bonus']:,} so'm

━━━━━━━━━━━━━━━━━━

🇷🇺 RUSSIAN BONUS
└ {result['russian_bonus']:,} so'm

🎓 IELTS BONUS
└ {result['ielts_bonus']:,} so'm

🔄 COVER BONUS
└ {result['cover_bonus']:,} so'm

📉 PENALTY
└ {result['penalty']:,} so'm

━━━━━━━━━━━━━━━━━━

💎 JAMI OYLIK:
{result['total_salary']:,} so'm
"""

    await message.answer(
        final_text,
        reply_markup=owner_menu
    )

    await state.finish()
