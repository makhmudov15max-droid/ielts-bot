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
# COVER
# =========================

@dp.message_handler(state=CashierStates.cover)
async def get_cover(message: types.Message, state: FSMContext):

    text = message.text.lower()

    if message.text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return

    if message.text == "⬅️ Ortga":

        await CashierStates.days.set()

        await message.answer(
            "Oy davomida necha kun ishladingiz?",
            reply_markup=days_keyboard
        )
        return

    if text == "ha":

        await CashierStates.cover_hours.set()

        await message.answer(
            "Necha soat cover qildingiz?",
            reply_markup=back_keyboard
        )
        return

    if text == "yo'q":

        await state.update_data(
            cover_hours=0
        )

        await CashierStates.absent.set()

        await message.answer(
            "📉 Ish qoldirdingizmi?",
            reply_markup=yes_no_keyboard
        )
        return

    await message.answer(
        "❌ Tugmalardan foydalaning."
    )


# =========================
# COVER HOURS
# =========================

@dp.message_handler(state=CashierStates.cover_hours)
async def get_cover_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return

    if text == "⬅️ Ortga":

        await CashierStates.cover.set()

        await message.answer(
            "🔄 Cover qildingizmi?",
            reply_markup=yes_no_keyboard
        )
        return

    if not text.isdigit():

        await message.answer(
            "❌ Raqam kiriting."
        )
        return

    await state.update_data(
        cover_hours=int(text)
    )

    await CashierStates.absent.set()

    await message.answer(
        "📉 Ish qoldirdingizmi?",
        reply_markup=yes_no_keyboard
    )


# =========================
# ABSENT
# =========================

@dp.message_handler(state=CashierStates.absent)
async def get_absent(message: types.Message, state: FSMContext):

    text = message.text.lower()

    if message.text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return

    if message.text == "⬅️ Ortga":

        await CashierStates.cover.set()

        await message.answer(
            "🔄 Cover qildingizmi?",
            reply_markup=yes_no_keyboard
        )
        return

    if text == "ha":

        await CashierStates.absent_hours.set()

        await message.answer(
            "Necha soat ish qoldirdingiz?",
            reply_markup=back_keyboard
        )
        return

    if text == "yo'q":

        await state.update_data(
            absent_hours=0
        )

        await CashierStates.active_students.set()

        await message.answer(
            "Oy yakunidagi Aktiv o'quvchilar sonini kiriting!",
            reply_markup=back_keyboard
        )
        return

    await message.answer(
        "❌ Tugmalardan foydalaning."
    )


# =========================
# ABSENT HOURS
# =========================

@dp.message_handler(state=CashierStates.absent_hours)
async def get_absent_hours(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return

    if text == "⬅️ Ortga":

        await CashierStates.absent.set()

        await message.answer(
            "📉 Ish qoldirdingizmi?",
            reply_markup=yes_no_keyboard
        )
        return

    if not text.isdigit():

        await message.answer(
            "❌ Raqam kiriting."
        )
        return

    await state.update_data(
        absent_hours=int(text)
    )

    await CashierStates.active_students.set()

    await message.answer(
        "Oy yakunidagi Aktiv o'quvchilar sonini kiriting!",
        reply_markup=back_keyboard
    )


# =========================
# ACTIVE STUDENTS
# =========================

@dp.message_handler(state=CashierStates.active_students)
async def get_active_students(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return

    if text == "⬅️ Ortga":

        await CashierStates.absent.set()

        await message.answer(
            "📉 Ish qoldirdingizmi?",
            reply_markup=yes_no_keyboard
        )
        return

    if not text.isdigit():

        await message.answer(
            "❌ Iltimos raqam kiriting."
        )
        return

    await state.update_data(
        active_students=int(text)
    )

    await CashierStates.active_debtors.set()

    await message.answer(
        "Aktiv o'quvchilarning nechtasi qarzdor?",
        reply_markup=back_keyboard
    )


# =========================
# ACTIVE DEBTORS
# =========================

@dp.message_handler(state=CashierStates.active_debtors)
async def get_active_debtors(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return

    if text == "⬅️ Ortga":

        await CashierStates.active_students.set()

        await message.answer(
            "Oy yakunidagi Aktiv o'quvchilar sonini kiriting!",
            reply_markup=back_keyboard
        )
        return

    if not text.isdigit():

        await message.answer(
            "❌ Iltimos raqam kiriting."
        )
        return

    await state.update_data(
        active_debtors=int(text)
    )

    await CashierStates.archive_students.set()

    await message.answer(
        "Archive o'quvchilar sonini kiriting...",
        reply_markup=back_keyboard
    )


# =========================
# ARCHIVE STUDENTS
# =========================

@dp.message_handler(state=CashierStates.archive_students)
async def get_archive_students(message: types.Message, state: FSMContext):

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return

    if text == "⬅️ Ortga":

        await CashierStates.active_debtors.set()

        await message.answer(
            "Aktiv o'quvchilarning nechtasi qarzdor?",
            reply_markup=back_keyboard
        )
        return

    if not text.isdigit():

        await message.answer(
            "❌ Iltimos raqam kiriting."
        )
        return

    await state.update_data(
        archive_students=int(text)
    )

    await CashierStates.archive_debtors.set()

    await message.answer(
        "Archive o'quvchilardagi qarzdorlar sonini kiriting...",
        reply_markup=back_keyboard
    )


# =========================
# FINAL
# =========================

@dp.message_handler(state=CashierStates.archive_debtors)
async def finish_cashier(message: types.Message, state: FSMContext):

    print("FINAL STATE ISHLADI")

    text = message.text

    if text == "🏠 Bosh sahifa":

        await state.finish()

        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=main_menu_keyboard
        )
        return

    if text == "⬅️ Ortga":

        await CashierStates.archive_students.set()

        await message.answer(
            "Archive o'quvchilar sonini kiriting...",
            reply_markup=back_keyboard
        )
        return

    if not text.isdigit():

        await message.answer(
            "❌ Iltimos raqam kiriting."
        )
        return


    # =========================
    # DATA
    # =========================

    data = await state.get_data()

    hours = data.get("hours", 0)

    days = data.get("days", 0)

    cover_hours = data.get("cover_hours", 0)

    absent_hours = data.get("absent_hours", 0)

    active_students = data.get("active_students", 0)

    active_debtors = data.get("active_debtors", 0)

    archive_students = data.get("archive_students", 0)

    archive_debtors = int(text)


    # =========================
    # DAILY SALARY
    # =========================

    if hours <= 8:

        daily_salary = hours * 15000

    else:

        extra_hours = hours - 8

        daily_salary = (
            (8 * 15000) +
            (extra_hours * 20000)
        )


    # =========================
    # FIX SALARY
    # =========================

    fix_salary = daily_salary * days


    # =========================
    # DEBT PERCENT
    # =========================

    total_students = (
        active_students +
        archive_students
    )

    total_debtors = (
        active_debtors +
        archive_debtors
    )

    if total_students > 0:

        debt_percent = (
            total_debtors / total_students
        ) * 100

    else:

        debt_percent = 0


    # =========================
    # BONUS SCALE
    # =========================

    if debt_percent == 0:

        bonus_coef = 2.5

    elif debt_percent <= 2:

        bonus_coef = 2.0

    elif debt_percent <= 5:

        bonus_coef = 1.8

    elif debt_percent <= 7:

        bonus_coef = 1.7

    elif debt_percent <= 10:

        bonus_coef = 1.6

    elif debt_percent <= 15:

        bonus_coef = 1.5

    elif debt_percent <= 20:

        bonus_coef = 1.4

    elif debt_percent <= 30:

        bonus_coef = 1.2

    else:

        bonus_coef = 1.0


    # =========================
    # FINAL CALCULATION
    # =========================

    total_salary = (
        fix_salary * bonus_coef
    )

    cover_bonus = (
        cover_hours * 15000
    )

    penalty = (
        absent_hours * 15000
    )

    final_salary = (
        total_salary +
        cover_bonus -
        penalty
    )


    await state.finish()


    # =========================
    # RESULT
    # =========================

    await message.answer(
        f"""
🏦 CASHIER SALARY REPORT

━━━━━━━━━━━━━━━━━━

💵 FIKS MAOSH
{fix_salary:,.0f} UZS

━━━━━━━━━━━━━━━━━━

📅 Kunlik maosh:
{daily_salary:,.0f} UZS

🟢 Qarzdorlik foizi:
{debt_percent:.2f}%

📈 Bonus koeffitsienti:
{bonus_coef}x

🔄 Cover bonusi:
+{cover_bonus:,.0f} UZS

📉 Jarima:
-{penalty:,.0f} UZS

━━━━━━━━━━━━━━━━━━

💰 UMUMIY OYLIK
{final_salary:,.0f} UZS
""",
        reply_markup=main_menu_keyboard
    )
