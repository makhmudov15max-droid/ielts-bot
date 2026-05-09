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


    @dp.message_handler(state=AdminSalaryStates.waiting_for_individual_plan)
    async def get_individual_plan(message: types.Message, state: FSMContext):

        if message.text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        await state.update_data(individual_plan=message.text)

        await message.answer(
            "📈 Amaldagi sotuv nechta?"
        )

        await AdminSalaryStates.waiting_for_actual_sales.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_actual_sales)
    async def get_actual_sales(message: types.Message, state: FSMContext):

        if message.text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        await state.update_data(actual_sales=message.text)

        await message.answer(
            "📊 Conversion plan nechta?",
            reply_markup=conversion_keyboard()
        )

        await AdminSalaryStates.waiting_for_conversion_plan.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_conversion_plan)
    async def get_conversion_plan(message: types.Message, state: FSMContext):

        text = message.text

        if text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        if text == "50%":
            conversion_plan = 50

        else:

            await message.answer(
                "❌ Tugma orqali tanlang."
            )

            return

        await state.update_data(conversion_plan=conversion_plan)

        await message.answer(
            "📊 Amaldagi conversion nechta?"
        )

        await AdminSalaryStates.waiting_for_actual_conversion.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_actual_conversion)
    async def get_actual_conversion(message: types.Message, state: FSMContext):

        if message.text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        await state.update_data(actual_conversion=message.text)

        await message.answer(
            "👥 Aktiv plan nechta?"
        )

        await AdminSalaryStates.waiting_for_active_plan.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_active_plan)
    async def get_active_plan(message: types.Message, state: FSMContext):

        if message.text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        await state.update_data(active_plan=message.text)

        await message.answer(
            "👥 Amaldagi aktiv nechta?"
        )

        await AdminSalaryStates.waiting_for_actual_active.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_actual_active)
    async def get_actual_active(message: types.Message, state: FSMContext):

        if message.text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        await state.update_data(actual_active=message.text)

        await message.answer(
            "🌍 Rus tilini biladimi?",
            reply_markup=yes_no_keyboard()
        )

        await AdminSalaryStates.waiting_for_russian.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_russian)
    async def get_russian(message: types.Message, state: FSMContext):

        if message.text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        await state.update_data(russian=message.text)

        await message.answer(
            "🎓 IELTS 7+ bormi?",
            reply_markup=yes_no_keyboard()
        )

        await AdminSalaryStates.waiting_for_ielts.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_ielts)
    async def get_ielts(message: types.Message, state: FSMContext):

        if message.text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        await state.update_data(ielts=message.text)

        await message.answer(
            "📉 Ish qoldirdimi?",
            reply_markup=yes_no_keyboard()
        )

        await AdminSalaryStates.waiting_for_missed_work.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_missed_work)
    async def get_missed_work(message: types.Message, state: FSMContext):

        text = message.text

        if text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        if text == "✅ Ha":

            await message.answer(
            "⏰ Necha soat ish qoldirdi?",
            reply_markup=home_keyboard()
        )

        await AdminSalaryStates.waiting_for_missed_hours.set()

        return

    elif text == "❌ Yo'q":

        await state.update_data(missed_hours=0)

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

        keyboard.add("✅ Cover qilgan", "❌ Cover qilmagan")
        keyboard.add("🏠 Bosh sahifa")

        await message.answer(
            "🔄 Cover qilganmi?",
            reply_markup=keyboard
        )

        await AdminSalaryStates.waiting_for_cover.set()

        return

    else:

        await message.answer(
            "❌ Variantlardan birini tanlang."
        )


    @dp.message_handler(state=AdminSalaryStates.waiting_for_missed_hours)
    async def get_missed_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":
        await go_home(message, state)
        return

    try:
        value = float(text)

    except:

        await message.answer(
            "❌ To'g'ri raqam kiriting.",
            reply_markup=home_keyboard()
        )

        return

    await state.update_data(missed_hours=value)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("✅ Cover qilgan", "❌ Cover qilmagan")
    keyboard.add("🏠 Bosh sahifa")

    await message.answer(
        "🔄 Cover qilganmi?",
        reply_markup=keyboard
    )

    await AdminSalaryStates.waiting_for_cover.set()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_cover)
    async def get_cover(message: types.Message, state: FSMContext):

        if message.text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        if message.text == "✅ Cover qilgan":

            await message.answer(
                "⏰ Necha soat cover qilgan?"
            )

            await AdminSalaryStates.waiting_for_cover_hours.set()

        else:

            await state.update_data(cover_hours=0)

            data = await state.get_data()

            result = await calculate_admin_salary(data)

            await message.answer(
                f"💰 JAMI OYLIK: {result['total_salary']:,.0f} UZS",
                reply_markup=main_menu_keyboard()
            )

            await state.finish()


    @dp.message_handler(state=AdminSalaryStates.waiting_for_cover_hours)
    async def get_cover_hours(message: types.Message, state: FSMContext):

        if message.text == "🏠 Bosh sahifa":
            await go_home(message, state)
            return

        await state.update_data(cover_hours=message.text)

        data = await state.get_data()

        result = await calculate_admin_salary(data)

        await message.answer(
            f"📈 Individual KPI: {result['individual_percentage']:.1f}%\n"
            f"📊 Conversion KPI: {result['conversion_percentage']:.1f}%\n"
            f"👥 Active KPI: {result['active_percentage']:.1f}%\n\n"

            f"🏆 Weighted KPI: {result['weighted_kpi']:.1f}%\n\n"

            f"🔥 KPI Bonus: {result['kpi_bonus']:,.0f} UZS\n"
            f"🔄 Cover Bonus: +{result['cover_bonus']:,.0f} UZS\n"
            f"📉 Jarima: -{result['penalty']:,.0f} UZS\n\n"

            f"💵 Fiksa: {result['fixa']:,.0f} UZS\n"
            f"🌍 Rus bonusi: +{result['russian_bonus']:,.0f} UZS\n"
            f"🎓 IELTS bonusi: +{result['ielts_bonus']:,.0f} UZS\n\n"

            f"💰 JAMI OYLIK: {result['total_salary']:,.0f} UZS",
            reply_markup=main_menu_keyboard()
        )

        await state.finish()
