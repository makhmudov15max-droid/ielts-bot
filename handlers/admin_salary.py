from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.admin_keyboard import (
    status_keyboard,
    main_menu_keyboard,
    hours_keyboard
)

from states.admin_states import AdminSalaryStates


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
