from aiogram import types
from aiogram.dispatcher import FSMContext

from safety.loader import dp

from states.cashier_states import CashierStates

from keyboards.cashier_keyboard import (
    hours_keyboard,
    days_keyboard,
    yes_no_keyboard,
    back_keyboard
)

from keyboards.admin_keyboard import main_menu_keyboard


# =========================
# START
# =========================

@dp.message_handler(lambda message: message.text == "💰 Cashier Salary")
async def cashier_start(message: types.Message):

    await CashierStates.hours.set()

    await message.answer(
        "Kuniga necha soat ishlaysiz?",
        reply_markup=hours_keyboard
    )


# =========================
# HOURS
# =========================

@dp.message_handler(state=CashierStates.hours)
async def get_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return


    if text == "⬅️ Ortga":

        await message.answer(
            "Siz birinchi bosqichdasiz."
        )
        return


    if text == "Boshqa":

        await CashierStates.custom_hours.set()

        await message.answer(
            "Necha soat ishlaysiz?\n\nRaqam kiriting.",
            reply_markup=back_keyboard
        )
        return


    try:

        hours = int(text.split()[0])

    except:

        await message.answer(
            "❌ Tugmalardan foydalaning."
        )
        return


    await state.update_data(hours=hours)

    await CashierStates.days.set()

    await message.answer(
        "Oy davomida necha kun ishladingiz?",
        reply_markup=days_keyboard
    )


# =========================
# CUSTOM HOURS
# =========================

@dp.message_handler(state=CashierStates.custom_hours)
async def custom_hours(message: types.Message, state: FSMContext):

    text = message.text


    if text == "⬅️ Ortga":

        await CashierStates.hours.set()

        await message.answer(
            "Kuniga necha soat ishlaysiz?",
            reply_markup=hours_keyboard
        )
        return


    if text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return


    if not text.isdigit():

        await message.answer(
            "❌ Raqam kiriting."
        )
        return


    await state.update_data(
        hours=int(text)
    )

    await CashierStates.days.set()

    await message.answer(
        "Oy davomida necha kun ishladingiz?",
        reply_markup=days_keyboard
    )


# =========================
# DAYS
# =========================

@dp.message_handler(state=CashierStates.days)
async def get_days(message: types.Message, state: FSMContext):

    text = message.text


    if text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return


    if text == "⬅️ Ortga":

        await CashierStates.hours.set()

        await message.answer(
            "Kuniga necha soat ishlaysiz?",
            reply_markup=hours_keyboard
        )
        return


    if text == "Boshqa":

        await CashierStates.custom_days.set()

        await message.answer(
            "Necha kun ishladingiz?\n\nRaqam kiriting.",
            reply_markup=back_keyboard
        )
        return


    try:

        days = int(text.split()[0])

    except:

        await message.answer(
            "❌ Tugmalardan foydalaning."
        )
        return


    await state.update_data(days=days)

    await CashierStates.cover.set()

    await message.answer(
        "🔄 Cover qildingizmi?",
        reply_markup=yes_no_keyboard
    )


# =========================
# CUSTOM DAYS
# =========================

@dp.message_handler(state=CashierStates.custom_days)
async def custom_days(message: types.Message, state: FSMContext):

    text = message.text


    if text == "⬅️ Ortga":

        await CashierStates.days.set()

        await message.answer(
            "Oy davomida necha kun ishladingiz?",
            reply_markup=days_keyboard
        )
        return


    if text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return


    if not text.isdigit():

        await message.answer(
            "❌ Raqam kiriting."
        )
        return


    await state.update_data(
        days=int(text)
    )

    await CashierStates.cover.set()

    await message.answer(
        "🔄 Cover qildingizmi?",
        reply_markup=yes_no_keyboard
    )
