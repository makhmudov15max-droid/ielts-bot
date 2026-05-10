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

    data = await state.get_data()

    result = calculate_admin_salary({
        "status": data["status"],
        "daily_hours": data["daily_hours"],
        "worked_days": data["worked_days"],

        "individual_plan": 100,
        "actual_sales": 100,

        "conversion_plan": 100,
        "actual_conversion": 100,

        "active_plan": 100,
        "actual_active": 100,

        "knows_russian": False,
        "has_ielts": False,

        "cover_hours": 0,
        "missed_hours": 0,
    })

    await message.answer(
        f"💰 Fixa: {result['fixa']:,}\n\n"
        f"💵 TOTAL: {result['total_salary']:,}"
    )

    await state.finish()
