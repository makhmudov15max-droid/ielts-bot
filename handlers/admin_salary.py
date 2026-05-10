from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminSalaryStates
from services.salary.admin_calculator import calculate_admin_salary

router = Router()


@router.message(F.text == "📊 Admin Salary")
async def start_admin_salary(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Status kiriting:\n(nova / prime / apex / leader)")
    await state.set_state(AdminSalaryStates.status)


@router.message(AdminSalaryStates.status)
async def get_status(message: Message, state: FSMContext):
    status = message.text.lower()

    if status not in ["nova", "prime", "apex", "leader"]:
        return await message.answer("Noto'g'ri status")

    await state.update_data(status=status)

    await message.answer("Kunlik ish soati:")
    await state.set_state(AdminSalaryStates.daily_hours)


@router.message(AdminSalaryStates.daily_hours)
async def get_daily_hours(message: Message, state: FSMContext):
    await state.update_data(daily_hours=float(message.text))

    await message.answer("Ishlagan kun:")
    await state.set_state(AdminSalaryStates.worked_days)


@router.message(AdminSalaryStates.worked_days)
async def get_worked_days(message: Message, state: FSMContext):
    await state.update_data(worked_days=int(message.text))

    await message.answer("Individual plan:")
    await state.set_state(AdminSalaryStates.individual_plan)


@router.message(AdminSalaryStates.individual_plan)
async def get_individual_plan(message: Message, state: FSMContext):
    await state.update_data(individual_plan=float(message.text))

    await message.answer("Actual sales:")
    await state.set_state(AdminSalaryStates.actual_sales)


@router.message(AdminSalaryStates.actual_sales)
async def get_actual_sales(message: Message, state: FSMContext):
    await state.update_data(actual_sales=float(message.text))

    await message.answer("Conversion plan:")
    await state.set_state(AdminSalaryStates.conversion_plan)


@router.message(AdminSalaryStates.conversion_plan)
async def get_conversion_plan(message: Message, state: FSMContext):
    await state.update_data(conversion_plan=float(message.text))

    await message.answer("Actual conversion:")
    await state.set_state(AdminSalaryStates.actual_conversion)


@router.message(AdminSalaryStates.actual_conversion)
async def get_actual_conversion(message: Message, state: FSMContext):
    await state.update_data(actual_conversion=float(message.text))

    await message.answer("Active plan:")
    await state.set_state(AdminSalaryStates.active_plan)


@router.message(AdminSalaryStates.active_plan)
async def get_active_plan(message: Message, state: FSMContext):
    await state.update_data(active_plan=float(message.text))

    await message.answer("Actual active:")
    await state.set_state(AdminSalaryStates.actual_active)


@router.message(AdminSalaryStates.actual_active)
async def get_actual_active(message: Message, state: FSMContext):
    await state.update_data(actual_active=float(message.text))

    await message.answer("Rus tili biladimi? (yes/no)")
    await state.set_state(AdminSalaryStates.knows_russian)


@router.message(AdminSalaryStates.knows_russian)
async def get_russian(message: Message, state: FSMContext):
    await state.update_data(
        knows_russian=message.text.lower() == "yes"
    )

    await message.answer("IELTS 7+ bormi? (yes/no)")
    await state.set_state(AdminSalaryStates.has_ielts)


@router.message(AdminSalaryStates.has_ielts)
async def get_ielts(message: Message, state: FSMContext):
    await state.update_data(
        has_ielts=message.text.lower() == "yes"
    )

    await message.answer("Cover hours:")
    await state.set_state(AdminSalaryStates.cover_hours)


@router.message(AdminSalaryStates.cover_hours)
async def get_cover(message: Message, state: FSMContext):
    await state.update_data(cover_hours=float(message.text))

    await message.answer("Missed hours:")
    await state.set_state(AdminSalaryStates.missed_hours)


@router.message(AdminSalaryStates.missed_hours)
async def get_missed(message: Message, state: FSMContext):
    await state.update_data(missed_hours=float(message.text))

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

    await state.clear()
