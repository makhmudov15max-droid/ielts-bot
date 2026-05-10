from aiogram import types
from aiogram.dispatcher import FSMContext

from safety.loader import dp

from states.admin_states import AdminSalaryStates
from calculators.admin_calc import calculate_admin_salary


@dp.message_handler(text="📊 Admin Salary")
async def start_admin_salary(message: types.Message, state: FSMContext):
    await state.finish()

    await message.answer(
        "Status kiriting:\n"
        "nova / prime / apex / leader"
    )

    await AdminSalaryStates.status.set()


@dp.message_handler(state=AdminSalaryStates.status)
async def get_status(message: types.Message, state: FSMContext):

    status = message.text.lower()

    if status not in ["nova", "prime", "apex", "leader"]:
        return await message.answer("Noto'g'ri status")

    await state.update_data(status=status)

    await message.answer("Kunlik ish soati:")
    await AdminSalaryStates.daily_hours.set()


@dp.message_handler(state=AdminSalaryStates.daily_hours)
async def get_daily_hours(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Raqam kiriting")

    await state.update_data(daily_hours=value)

    await message.answer("Ishlagan kun:")
    await AdminSalaryStates.worked_days.set()


@dp.message_handler(state=AdminSalaryStates.worked_days)
async def get_worked_days(message: types.Message, state: FSMContext):

    try:
        value = int(message.text)
    except:
        return await message.answer("Raqam kiriting")

    await state.update_data(worked_days=value)

    await message.answer("Individual plan:")
    await AdminSalaryStates.individual_plan.set()


@dp.message_handler(state=AdminSalaryStates.individual_plan)
async def get_individual_plan(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Raqam kiriting")

    await state.update_data(individual_plan=value)

    await message.answer("Actual sales:")
    await AdminSalaryStates.actual_sales.set()


@dp.message_handler(state=AdminSalaryStates.actual_sales)
async def get_actual_sales(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Raqam kiriting")

    await state.update_data(actual_sales=value)

    await message.answer("Conversion plan:")
    await AdminSalaryStates.conversion_plan.set()


@dp.message_handler(state=AdminSalaryStates.conversion_plan)
async def get_conversion_plan(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Raqam kiriting")

    await state.update_data(conversion_plan=value)

    await message.answer("Actual conversion:")
    await AdminSalaryStates.actual_conversion.set()


@dp.message_handler(state=AdminSalaryStates.actual_conversion)
async def get_actual_conversion(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Raqam kiriting")

    await state.update_data(actual_conversion=value)

    await message.answer("Active plan:")
    await AdminSalaryStates.active_plan.set()


@dp.message_handler(state=AdminSalaryStates.active_plan)
async def get_active_plan(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Raqam kiriting")

    await state.update_data(active_plan=value)

    await message.answer("Actual active:")
    await AdminSalaryStates.actual_active.set()


@dp.message_handler(state=AdminSalaryStates.actual_active)
async def get_actual_active(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Raqam kiriting")

    await state.update_data(actual_active=value)

    await message.answer("Rus tili biladimi? yes/no")
    await AdminSalaryStates.knows_russian.set()


@dp.message_handler(state=AdminSalaryStates.knows_russian)
async def get_russian(message: types.Message, state: FSMContext):

    answer = message.text.lower()

    if answer not in ["yes", "no"]:
        return await message.answer("Faqat yes yoki no yozing")

    await state.update_data(
        knows_russian=answer == "yes"
    )

    await message.answer("IELTS 7+ bormi? yes/no")
    await AdminSalaryStates.has_ielts.set()


@dp.message_handler(state=AdminSalaryStates.has_ielts)
async def get_ielts(message: types.Message, state: FSMContext):

    answer = message.text.lower()

    if answer not in ["yes", "no"]:
        return await message.answer("Faqat yes yoki no yozing")

    await state.update_data(
        has_ielts=answer == "yes"
    )

    await message.answer("Cover hours:")
    await AdminSalaryStates.cover_hours.set()


@dp.message_handler(state=AdminSalaryStates.cover_hours)
async def get_cover_hours(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Raqam kiriting")

    await state.update_data(cover_hours=value)

    await message.answer("Missed hours:")
    await AdminSalaryStates.missed_hours.set()


@dp.message_handler(state=AdminSalaryStates.missed_hours)
async def get_missed_hours(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer("Raqam kiriting")

    await state.update_data(missed_hours=value)

    data = await state.get_data()

    result = calculate_admin_salary(data)

    text = f"""
📊 ADMIN SALARY

💰 Fixa: {result['fixa']:,}

📈 Individual KPI: {result['individual_kpi']}%
📈 Conversion KPI: {result['conversion_kpi']}%
📈 Active KPI: {result['active_kpi']}%

📊 Weighted KPI: {result['weighted_kpi']}%

🎯 KPI Bonus: {result['final_kpi_bonus']:,}

🇷🇺 Russian Bonus: {result['russian_bonus']:,}
🎓 IELTS Bonus: {result['ielts_bonus']:,}

🔄 Cover Bonus: {result['cover_bonus']:,}
📉 Penalty: {result['penalty']:,}

━━━━━━━━━━━━━━
💵 TOTAL: {result['total_salary']:,}
"""

    await message.answer(text)

    await state.finish()
