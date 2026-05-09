from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.admin_keyboard import (
    main_menu_keyboard,
    status_keyboard,
    hours_keyboard,
    days_keyboard,
    yes_no_keyboard,
    conversion_keyboard,
    cover_keyboard
)

from states.admin_states import AdminSalaryStates

from calculators.admin_calc import calculate_admin_salary


async def go_home(message: types.Message, state: FSMContext):

    await state.finish()

    await message.answer(
        "🏠 Bosh sahifa",
        reply_markup=main_menu_keyboard()
    )


def register_admin_handlers(dp):


    @dp.message_handler(lambda message: message.text == "💰 Admin Salary")
    async def salary_start(message: types.Message):

        await message.answer(
            "📋 Statusni tanlang:",
            reply_markup=status_keyboard()
        )

        await AdminSalaryStates.waiting_for_status.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_status)
    async def get_status(message: types.Message, state: FSMContext):

        if message.text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        await state.update_data(status=message.text)

        await message.answer(
            "⏰ Kunlik necha soat ishlaydi?",
            reply_markup=hours_keyboard()
        )

        await AdminSalaryStates.waiting_for_hours.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_hours)
    async def get_hours(message: types.Message, state: FSMContext):

        text = message.text

        if text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        if text == "6 soat":
            hours = 6

        elif text == "7 soat":
            hours = 7

        elif text == "9 soat":
            hours = 9

        elif text == "10 soat":
            hours = 10

        else:

            await message.answer(
                "❌ Soatni tugma orqali tanlang."
            )

            return

        await state.update_data(hours=hours)

        await message.answer(
            "📅 Oyda necha kun ishladi?",
            reply_markup=days_keyboard()
        )

        await AdminSalaryStates.waiting_for_days.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_days)
    async def get_days(message: types.Message, state: FSMContext):

        text = message.text

        if text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        if text == "24 kun":
            days = 24

        elif text == "25 kun":
            days = 25

        elif text == "26 kun":
            days = 26

        elif text == "27 kun":
            days = 27

        else:

            await message.answer(
                "❌ Kunni tugma orqali tanlang."
            )

            return

        await state.update_data(days=days)

        await message.answer(
            "🎯 Individual plan nechta?"
        )

        await AdminSalaryStates.waiting_for_individual_plan.set()
