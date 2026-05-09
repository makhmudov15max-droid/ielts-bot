from aiogram import types
from aiogram.dispatcher import FSMContext

from states.cashier_states import CashierSalaryStates

from calculators.cashier_calc import calculate_cashier_salary

from keyboards.admin_keyboard import main_menu_keyboard

from keyboards.cashier_keyboard import (
    cashier_hours_keyboard,
    cashier_days_keyboard,
    yes_no_keyboard,
    home_keyboard
)


async def go_home(message: types.Message, state: FSMContext):

    await state.finish()

    await message.answer(
        "🏠 Bosh sahifa",
        reply_markup=main_menu_keyboard()
    )


def register_cashier_handlers(dp):


    @dp.message_handler(lambda message: message.text == "💵 Cashier Salary")
    async def cashier_start(message: types.Message):

        await message.answer(
            "⏰ Kunlik ish soati?",
            reply_markup=cashier_hours_keyboard()
        )

        await CashierSalaryStates.waiting_for_hours.set()


    @dp.message_handler(state=CashierSalaryStates.waiting_for_hours)
    async def get_hours(message: types.Message, state: FSMContext):

        text = message.text


        if text == "🏠 Bosh sahifa":

            await go_home(message, state)

            return


        if text == "6 soat":

            hours = 6

        elif text == "7 soat":

            hours = 7

        elif text == "8 soat":

            hours = 8

        elif text == "9 soat":

            hours = 9

        elif text == "✍️ Boshqa":

            await message.answer(
                "⏰ Necha soat ishlaydi?",
                reply_markup=home_keyboard()
            )

            return

        else:

            try:

                hours = float(text)

            except:

                await message.answer(
                    "❌ To'g'ri raqam kiriting."
                )

                return


        await state.update_data(hours=hours)

        await message.answer(
            "📅 Bu oy necha kun ishladilar?",
            reply_markup=cashier_days_keyboard()
        )

        await CashierSalaryStates.waiting_for_days.set()

    @dp.message_handler(state=CashierSalaryStates.waiting_for_days)
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

        elif text == "✍️ Boshqa":

            await message.answer(
                "📅 Necha kun ishladi?",
                reply_markup=home_keyboard()
            )

            return

        else:

            try:

                days = float(text)

            except:

                await message.answer(
                    "❌ To'g'ri raqam kiriting."
                )

                return


        await state.update_data(days=days)


        await message.answer(
            "📉 Ish qoldirdimi?",
            reply_markup=yes_no_keyboard()
        )


        await CashierSalaryStates.waiting_for_missed_work.set()

    @dp.message_handler(state=CashierSalaryStates.waiting_for_missed_work)
    async def get_missed_work(message: types.Message, state: FSMContext):

        text = message.text


        if text == "🏠 Bosh sahifa":

            await go_home(message, state)

            return


        if text == "✅ Ha":

            await message.answer(
                "📉 Necha soat ishga chiqmadingiz?",
                reply_markup=home_keyboard()
            )

            await CashierSalaryStates.waiting_for_missed_days.set()


        else:

            await state.update_data(missed_days=0)

            await message.answer(
                "🔄 Cover qildingizmi?",
                reply_markup=yes_no_keyboard()
            )

            await CashierSalaryStates.waiting_for_cover.set()



    @dp.message_handler(state=CashierSalaryStates.waiting_for_missed_days)
    async def get_missed_days(message: types.Message, state: FSMContext):

        text = message.text


        if text == "🏠 Bosh sahifa":

            await go_home(message, state)

            return


        try:

            missed_days = float(text)

        except:

            await message.answer(
                "❌ To'g'ri raqam kiriting."
            )

            return


        await state.update_data(missed_days=missed_days)


        await message.answer(
            "🔄 Cover qilganmi?",
            reply_markup=yes_no_keyboard()
        )

        await CashierSalaryStates.waiting_for_cover.set()

    @dp.message_handler(state=CashierSalaryStates.waiting_for_cover)
    async def get_cover(message: types.Message, state: FSMContext):

        text = message.text


        if text == "🏠 Bosh sahifa":

            await go_home(message, state)

            return


        if text == "✅ Ha":

            await message.answer(
                "🔄 Necha soat cover qildingiz?",
                reply_markup=home_keyboard()
            )

            await CashierSalaryStates.waiting_for_cover_days.set()


        else:

            await state.update_data(cover_days=0)

            await message.answer(
                "👥 Aktiv o‘quvchilar soni?",
                reply_markup=home_keyboard()
            )

            await CashierSalaryStates.waiting_for_active_students.set()



    @dp.message_handler(state=CashierSalaryStates.waiting_for_cover_days)
    async def get_cover_days(message: types.Message, state: FSMContext):

        text = message.text


        if text == "🏠 Bosh sahifa":

            await go_home(message, state)

            return


        try:

            cover_days = float(text)

        except:

            await message.answer(
                "❌ To'g'ri raqam kiriting."
            )

            return


        await state.update_data(cover_days=cover_days)


        await message.answer(
            "👥 Aktiv o‘quvchilar soni?",
            reply_markup=home_keyboard()
        )

        await CashierSalaryStates.waiting_for_active_students.set()



    @dp.message_handler(state=CashierSalaryStates.waiting_for_active_students)
    async def get_active_students(message: types.Message, state: FSMContext):

        text = message.text


        if text == "🏠 Bosh sahifa":

            await go_home(message, state)

            return


        try:

            active_students = float(text)

        except:

            await message.answer(
                "❌ To'g'ri raqam kiriting."
            )

            return


        await state.update_data(active_students=active_students)


        await message.answer(
            "📉 Aktiv qarzdorlar soni?",
            reply_markup=home_keyboard()
        )

        await CashierSalaryStates.waiting_for_active_debtors.set()

    @dp.message_handler(state=CashierSalaryStates.waiting_for_active_debtors)
    async def get_active_debtors(message: types.Message, state: FSMContext):

        text = message.text


        if text == "🏠 Bosh sahifa":

            await go_home(message, state)

            return


        try:

            active_debtors = float(text)

        except:

            await message.answer(
                "❌ To'g'ri raqam kiriting."
            )

            return


        await state.update_data(active_debtors=active_debtors)


        await message.answer(
            "🗂 Archive o‘quvchilar soni?",
            reply_markup=home_keyboard()
        )

        await CashierSalaryStates.waiting_for_archive_students.set()



    @dp.message_handler(state=CashierSalaryStates.waiting_for_archive_students)
    async def get_archive_students(message: types.Message, state: FSMContext):

        text = message.text


        if text == "🏠 Bosh sahifa":

            await go_home(message, state)

            return


        try:

            archive_students = float(text)

        except:

            await message.answer(
                "❌ To'g'ri raqam kiriting."
            )

            return


        await state.update_data(archive_students=archive_students)


        await message.answer(
            "📉 Archive qarzdorlar soni?",
            reply_markup=home_keyboard()
        )

        await CashierSalaryStates.waiting_for_archive_debtors.set()



    @dp.message_handler(state=CashierSalaryStates.waiting_for_archive_debtors)
    async def get_archive_debtors(message: types.Message, state: FSMContext):

        text = message.text


        if text == "🏠 Bosh sahifa":

            await go_home(message, state)

            return


        try:

            archive_debtors = float(text)

        except:

            await message.answer(
                "❌ To'g'ri raqam kiriting."
            )

            return


        await state.update_data(
            archive_debtors=archive_debtors
        )


        data = await state.get_data()

        result = await calculate_cashier_salary(data)


        await message.answer(

                            debt_emoji = "🟢"

        if result['debt_percentage'] >= 10:
            debt_emoji = "🟡"

        if result['debt_percentage'] >= 20:
            debt_emoji = "🔴"


        await message.answer(

            f"🏦 CASHIER SALARY REPORT\n\n"

            f"━━━━━━━━━━━━━━━━━━\n\n"

            f"💵 FIKS MAOSH\n"
            f"{result['worked_salary']:,.0f} UZS\n\n"

            f"━━━━━━━━━━━━━━━━━━\n\n"

            f"📅 Kunlik maosh: "
            f"{result['daily_salary']:,.0f} UZS\n\n"

            f"{debt_emoji} Qarzdorlik foizi: "
            f"{result['debt_percentage']:.2f}%\n\n"

            f"📈 Bonus koeffitsienti: "
            f"{result['multiplier']}x\n\n"

            f"🔄 Cover bonusi: "
            f"+{result['cover_bonus']:,.0f} UZS\n\n"

            f"📉 Jarima: "
            f"-{result['missed_penalty']:,.0f} UZS\n\n"

            f"━━━━━━━━━━━━━━━━━━\n\n"

            f"💰 UMUMIY OYLIK\n"
            f"{result['final_salary']:,.0f} UZS",

            reply_markup=main_menu_keyboard()
        )

        await state.finish()
