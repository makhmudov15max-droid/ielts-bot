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

    await message.answer(
        "Bekor qilindi ✅"
    )


@dp.message_handler(commands=["start"], state="*")
async def restart(message: types.Message, state: FSMContext):

    await state.finish()

    await message.answer(
        "Bosh menyu"
    )


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
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(daily_hours=value)

    await message.answer(
        "Ishlagan kunni kiriting:"
    )

    await AdminSalaryStates.worked_days.set()


@dp.message_handler(state=AdminSalaryStates.worked_days)
async def get_worked_days(message: types.Message, state: FSMContext):

    try:
        value = int(message.text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(worked_days=value)

    data = await state.get_data()

    result = calculate_admin_salary({
        "status": data["status"],
        "daily_hours": data["daily_hours"],
        "worked_days": value,
    })

    text = f"""
📊 ADMIN SALARY

🏅 Status: {data['status'].upper()}

💰 Fixa: {result['fixa']:,}

━━━━━━━━━━━━━━
💵 TOTAL: {result['total_salary']:,}
"""

    await message.answer(text)

    await state.finish()
