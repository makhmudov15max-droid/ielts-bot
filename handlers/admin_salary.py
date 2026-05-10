from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from safety.loader import dp

from states.admin_states import AdminSalaryStates
from calculators.admin_calc import calculate_admin_salary


status_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

status_keyboard.add(
    KeyboardButton("nova"),
    KeyboardButton("prime")
)

status_keyboard.add(
    KeyboardButton("apex"),
    KeyboardButton("leader")
)

status_keyboard.add(
    KeyboardButton("❌ Bekor qilish")
)


cancel_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

cancel_keyboard.add(
    KeyboardButton("❌ Bekor qilish")
)


@dp.message_handler(text="❌ Bekor qilish", state="*")
async def cancel_process(message: types.Message, state: FSMContext):

    await state.finish()

    await message.answer("Bekor qilindi ✅")


@dp.message_handler(text="📊 Admin Salary")
async def start_admin_salary(message: types.Message, state: FSMContext):

    await state.finish()

    await message.answer(
        "Status tanlang:",
        reply_markup=status_keyboard
    )

    await AdminSalaryStates.status.set()


@dp.message_handler(state=AdminSalaryStates.status)
async def get_status(message: types.Message, state: FSMContext):

    status = message.text.lower()

    if status not in ["nova", "prime", "apex", "leader"]:
        return await message.answer(
            "Tugmalardan birini tanlang"
        )

    await state.update_data(status=status)

    await message.answer(
        "Kunlik ish soatini kiriting:",
        reply_markup=cancel_keyboard
    )

    await AdminSalaryStates.daily_hours.set()


@dp.message_handler(state=AdminSalaryStates.daily_hours)
async def get_daily_hours(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Faqat raqam kiriting")

    await state.update_data(daily_hours=value)

    await message.answer("Ishlagan kunni kiriting:")

    await AdminSalaryStates.worked_days.set()


@dp.message_handler(state=AdminSalaryStates.worked_days)
async def get_worked_days(message: types.Message, state: FSMContext):

    try:
        value = int(message.text)
    except:
        return await message.answer("Faqat raqam kiriting")

    await state.update_data(worked_days=value)

    await message.answer("Individual plan kiriting:")

    await AdminSalaryStates.individual_plan.set()


@dp.message_handler(state=AdminSalaryStates.individual_plan)
async def get_individual_plan(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Faqat raqam kiriting")

    await state.update_data(individual_plan=value)

    await message.answer("Actual sales kiriting:")

    await AdminSalaryStates.actual_sales.set()


@dp.message_handler(state=AdminSalaryStates.actual_sales)
async def get_actual_sales(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Faqat raqam kiriting")

    await state.update_data(actual_sales=value)

    await message.answer("Conversion plan kiriting:")

    await AdminSalaryStates.conversion_plan.set()


@dp.message_handler(state=AdminSalaryStates.conversion_plan)
async def get_conversion_plan(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Faqat raqam kiriting")

    await state.update_data(conversion_plan=value)

    await message.answer("Actual conversion kiriting:")

    await AdminSalaryStates.actual_conversion.set()


@dp.message_handler(state=AdminSalaryStates.actual_conversion)
async def get_actual_conversion(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Faqat raqam kiriting")

    await state.update_data(actual_conversion=value)

    await message.answer("Active plan kiriting:")

    await AdminSalaryStates.active_plan.set()


@dp.message_handler(state=AdminSalaryStates.active_plan)
async def get_active_plan(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Faqat raqam kiriting")

    await state.update_data(active_plan=value)

    await message.answer("Actual active kiriting:")

    await AdminSalaryStates.actual_active.set()


@dp.message_handler(state=AdminSalaryStates.actual_active)
async def get_actual_active(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Faqat raqam kiriting")

    await state.update_data(actual_active=value)

    data = await state.get_data()

    result = calculate_admin_salary(data)

    text = f"""
📊 ADMIN SALARY

🏅 Status: {data['status'].upper()}

💰 Fixa: {result['fixa']:,}

📈 Individual KPI: {result['individual_kpi']}%

📈 Conversion KPI: {result['conversion_kpi']}%

📈 Active KPI: {result['active_kpi']}%

📊 Weighted KPI: {result['weighted_kpi']}%

━━━━━━━━━━━━━━
💵 TOTAL: {result['total_salary']:,}
"""

    await message.answer(text)

    await state.finish()
