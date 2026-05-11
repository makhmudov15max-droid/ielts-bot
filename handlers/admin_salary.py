import json

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

    return admin_menu


# =========================================
# KEYBOARDS
# =========================================

def status_keyboard():

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

    return keyboard


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


def conversion_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "50%"
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
async def back_home(
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
    lambda message: message.text == "📊 Admin Salary"
)
async def admin_salary_start(
    message: types.Message
):

    await AdminSalaryStates.status.set()

    await message.answer(
        """
📊 ADMIN SALARY

━━━━━━━━━━━━━━━━━━

🏅 Status tanlang:
""",
        reply_markup=status_keyboard()
    )


# =========================================
# STATUS
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.status
)
async def get_status(
    message: types.Message,
    state: FSMContext
):

    text = message.text

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

    await message.answer(
        """
⏰ Kunlik ish soatini tanlang:
""",
        reply_markup=hours_keyboard()
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

    if text == "⬅️ Ortga":

        await AdminSalaryStates.status.set()

        return await message.answer(
            """
🏅 Status tanlang:
""",
            reply_markup=status_keyboard()
        )

    if text == "✍️ Boshqa":

        await AdminSalaryStates.custom_daily_hours.set()

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
        daily_hours=value
    )

    await AdminSalaryStates.worked_days.set()

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
    state=AdminSalaryStates.custom_daily_hours
)
async def custom_daily_hours(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.daily_hours.set()

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
        daily_hours=value
    )

    await AdminSalaryStates.worked_days.set()

    await message.answer(
        """
📅 Ishlagan kunni tanlang:
""",
        reply_markup=days_keyboard()
    )


# =========================================
# WORKED DAYS
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.worked_days
)
async def worked_days(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.daily_hours.set()

        return await message.answer(
            """
⏰ Kunlik ish soatini tanlang:
""",
            reply_markup=hours_keyboard()
        )

    if text == "✍️ Boshqa":

        await AdminSalaryStates.custom_worked_days.set()

        return await message.answer(
            "📅 Kun kiriting:",
            reply_markup=manual_keyboard()
        )

    try:

        value = int(text)

    except:

        return await message.answer(
            "❌ Tugmalardan foydalaning."
        )

    await state.update_data(
        worked_days=value
    )

    await AdminSalaryStates.has_ielts.set()

    await message.answer(
        "🎓 IELTS 7+ bormi?",
        reply_markup=yes_no_keyboard()
    )


# =========================================
# CUSTOM DAYS
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.custom_worked_days
)
async def custom_worked_days(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.worked_days.set()

        return await message.answer(
            """
📅 Ishlagan kunni tanlang:
""",
            reply_markup=days_keyboard()
        )

    try:

        value = int(text)

    except:

        return await message.answer(
            "❌ Raqam kiriting."
        )

    await state.update_data(
        worked_days=value
    )

    await AdminSalaryStates.has_ielts.set()

    await message.answer(
        "🎓 IELTS 7+ bormi?",
        reply_markup=yes_no_keyboard()
    )


# =========================================
# IELTS
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.has_ielts
)
async def has_ielts(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.worked_days.set()

        return await message.answer(
            """
📅 Ishlagan kunni tanlang:
""",
            reply_markup=days_keyboard()
        )

    await state.update_data(
        has_ielts=text == "✅ HA"
    )

    await AdminSalaryStates.knows_russian.set()

    await message.answer(
        "🇷🇺 Rus tili biladimi?",
        reply_markup=yes_no_keyboard()
    )


# =========================================
# RUSSIAN
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.knows_russian
)
async def knows_russian(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.has_ielts.set()

        return await message.answer(
            "🎓 IELTS 7+ bormi?",
            reply_markup=yes_no_keyboard()
        )

    await state.update_data(
        knows_russian=text == "✅ HA"
    )

    await AdminSalaryStates.missed.set()

    await message.answer(
        "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
        reply_markup=yes_no_keyboard()
    )


# =========================================
# MISSED
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.missed
)
async def missed(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.knows_russian.set()

        return await message.answer(
            "🇷🇺 Rus tili biladimi?",
            reply_markup=yes_no_keyboard()
        )

    if text == "✅ HA":

        await AdminSalaryStates.missed_hours.set()

        return await message.answer(
            "⏰ Necha soat ish qoldirdingiz?",
            reply_markup=manual_keyboard()
        )

    await state.update_data(
        missed_hours=0
    )

    await AdminSalaryStates.cover.set()

    await message.answer(
        "🔄 Cover qilganmi?",
        reply_markup=yes_no_keyboard()
    )


# =========================================
# MISSED HOURS
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.missed_hours
)
async def missed_hours(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.missed.set()

        return await message.answer(
            "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
            reply_markup=yes_no_keyboard()
        )

    try:

        value = float(text)

    except:

        return await message.answer(
            "❌ Raqam kiriting."
        )

    await state.update_data(
        missed_hours=value
    )

    await AdminSalaryStates.cover.set()

    await message.answer(
        "🔄 Cover qilganmi?",
        reply_markup=yes_no_keyboard()
    )


# =========================================
# COVER
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.cover
)
async def cover(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.missed.set()

        return await message.answer(
            "📉 Ish qoldirgan kunlaringiz bo'ldimi?",
            reply_markup=yes_no_keyboard()
        )

    if text == "✅ HA":

        await AdminSalaryStates.cover_hours.set()

        return await message.answer(
            "⏰ Necha soat cover qildingiz?",
            reply_markup=manual_keyboard()
        )

    await state.update_data(
        cover_hours=0
    )

    await AdminSalaryStates.individual_plan.set()

    await message.answer(
        "🎯 Individual plan kiriting:",
        reply_markup=manual_keyboard()
    )


# =========================================
# COVER HOURS
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.cover_hours
)
async def cover_hours(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.cover.set()

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
        cover_hours=value
    )

    await AdminSalaryStates.individual_plan.set()

    await message.answer(
        "🎯 Individual plan kiriting:",
        reply_markup=manual_keyboard()
    )

    # =========================================
# UNIVERSAL NUMBER INPUT
# =========================================

async def number_input(
    message,
    state,
    key,
    next_state,
    question,
    back_state,
    back_question,
    back_keyboard,
    keyboard=manual_keyboard()
):

    text = message.text

    if text == "⬅️ Ortga":

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
            "❌ Raqam kiriting."
        )

    await state.update_data(
        **{key: value}
    )

    await next_state.set()

    await message.answer(
        question,
        reply_markup=keyboard
    )


# =========================================
# INDIVIDUAL PLAN
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.individual_plan
)
async def individual_plan(
    message: types.Message,
    state: FSMContext
):

    await number_input(
        message,
        state,
        "individual_plan",
        AdminSalaryStates.actual_sales,
        "💰 Actual sales kiriting:",
        AdminSalaryStates.cover,
        "🔄 Cover qilganmi?",
        yes_no_keyboard()
    )


# =========================================
# ACTUAL SALES
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.actual_sales
)
async def actual_sales(
    message: types.Message,
    state: FSMContext
):

    await number_input(
        message,
        state,
        "actual_sales",
        AdminSalaryStates.conversion_plan,
        "📈 Conversion plan tanlang:",
        AdminSalaryStates.individual_plan,
        "🎯 Individual plan kiriting:",
        manual_keyboard(),
        conversion_keyboard()
    )


# =========================================
# CONVERSION PLAN
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.conversion_plan
)
async def conversion_plan(
    message: types.Message,
    state: FSMContext
):

    await number_input(
        message,
        state,
        "conversion_plan",
        AdminSalaryStates.actual_conversion,
        "📊 Actual conversion kiriting:",
        AdminSalaryStates.actual_sales,
        "💰 Actual sales kiriting:",
        manual_keyboard()
    )


# =========================================
# ACTUAL CONVERSION
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.actual_conversion
)
async def actual_conversion(
    message: types.Message,
    state: FSMContext
):

    await number_input(
        message,
        state,
        "actual_conversion",
        AdminSalaryStates.active_plan,
        "👥 Active plan kiriting:",
        AdminSalaryStates.conversion_plan,
        "📈 Conversion plan tanlang:",
        conversion_keyboard()
    )


# =========================================
# ACTIVE PLAN
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.active_plan
)
async def active_plan(
    message: types.Message,
    state: FSMContext
):

    await number_input(
        message,
        state,
        "active_plan",
        AdminSalaryStates.actual_active,
        "🔥 Actual active kiriting:",
        AdminSalaryStates.actual_conversion,
        "📊 Actual conversion kiriting:",
        manual_keyboard()
    )


# =========================================
# FINAL RESULT
# =========================================

@dp.message_handler(
    state=AdminSalaryStates.actual_active
)
async def actual_active(
    message: types.Message,
    state: FSMContext
):

    text = message.text

    if text == "⬅️ Ortga":

        await AdminSalaryStates.active_plan.set()

        return await message.answer(
            "👥 Active plan kiriting:",
            reply_markup=manual_keyboard()
        )

    try:

        value = float(text)

    except:

        return await message.answer(
            "❌ Raqam kiriting."
        )

    await state.update_data(
        actual_active=value
    )

    data = await state.get_data()

    result = calculate_admin_salary(data)

    with open(
        USERS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        users = json.load(file)

    role = users[
        str(message.from_user.id)
    ]["role"]

    final_menu = get_menu_by_role(role)

    await state.finish()

    await message.answer(
        f"""
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
""",
        reply_markup=final_menu
    )
