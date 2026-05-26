from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from Handlers.states import AdminSalaryStates, CashierSalaryStates
from Keyboards.main_menu import get_main_menu
from calculators.admin_calc import calculate_admin_salary
from calculators.cashier_calc import calculate_cashier_salary
from utils.access import check_user_access

salaries_router = Router()

# Global o'zgaruvchilar
USERS_ROLES = None


def init_salaries_handler(users_roles):
    """Salaries handler uchun global o'zgaruvchilarni o'rnatish"""
    global USERS_ROLES
    USERS_ROLES = users_roles


# ================= KLAVIATURALAR =================

def get_status_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="NOVA"), KeyboardButton(text="PRIME")],
        [KeyboardButton(text="APEX"), KeyboardButton(text="LEADER")],
        [KeyboardButton(text="🏠 Bosh sahifa")]
    ], resize_keyboard=True)


def get_hours_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="6"), KeyboardButton(text="7"), KeyboardButton(text="8")],
        [KeyboardButton(text="✍️ Boshqa")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ], resize_keyboard=True)


def get_days_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="24"), KeyboardButton(text="25")],
        [KeyboardButton(text="26"), KeyboardButton(text="27")],
        [KeyboardButton(text="✍️ Boshqa")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ], resize_keyboard=True)


def get_yes_no_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ HA"), KeyboardButton(text="❌ YO‘Q")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ], resize_keyboard=True)


def get_manual_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ], resize_keyboard=True)


def get_cashier_hours_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="6"), types.KeyboardButton(text="7"), types.KeyboardButton(text="8")],
            [types.KeyboardButton(text="✍️ Boshqa")],
            [types.KeyboardButton(text="🏠 Bosh sahifa")]
        ], resize_keyboard=True
    )


def get_cashier_days_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="24"), types.KeyboardButton(text="25"), types.KeyboardButton(text="26")],
            [types.KeyboardButton(text="✍️ Boshqa")],
            [types.KeyboardButton(text="⬅️ Ortga")]
        ], resize_keyboard=True
    )


def get_cashier_yes_no_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="✅ HA"), types.KeyboardButton(text="❌ YO'Q")],
            [types.KeyboardButton(text="⬅️ Ortga")]
        ], resize_keyboard=True
    )


# ================= ADMIN OYLIK =================

@salaries_router.message(F.text == "📊 Admin oylik")
async def start_admin_salary_calc(message: types.Message, state: FSMContext):
    if USERS_ROLES is None:
        await message.answer("⚠️ Tizim xatosi: Ma'lumotlar yuklanmagan. Iltimos /start buyrug'ini yuboring.")
        return
    
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
        
    await state.set_state(AdminSalaryStates.status)
    await message.answer("🏅 Status tanlang:", reply_markup=get_status_keyboard())


@salaries_router.message(AdminSalaryStates(), F.text == "🏠 Bosh sahifa")
async def back_to_home_salary(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES[str(message.from_user.id)]["role"]
    await message.answer("🏠 Bosh sahifaga qaytdingiz.", reply_markup=get_main_menu(role))


@salaries_router.message(AdminSalaryStates.status)
async def process_status(message: types.Message, state: FSMContext):
    if message.text not in ["NOVA", "PRIME", "APEX", "LEADER"]:
        return await message.answer("❌ Iltimos, tugmalardan birini tanlang:")
    await state.update_data(status=message.text.lower())
    await state.set_state(AdminSalaryStates.daily_hours)
    await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_hours_keyboard())


@salaries_router.message(AdminSalaryStates.daily_hours)
async def process_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.status)
        return await message.answer("🏅 Status tanlang:", reply_markup=get_status_keyboard())
    if message.text == "✍️ Boshqa":
        await state.set_state(AdminSalaryStates.custom_daily_hours)
        return await message.answer("⏰ Soatni o'zingiz kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, to'g'ri soatni tanlang yoki raqam kiriting:")
    await state.update_data(daily_hours=int(message.text))
    await state.set_state(AdminSalaryStates.worked_days)
    await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_days_keyboard())


@salaries_router.message(AdminSalaryStates.custom_daily_hours)
async def process_custom_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.daily_hours)
        return await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_hours_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat raqam kiriting (Masalan: 8):")
    await state.update_data(daily_hours=int(message.text))
    await state.set_state(AdminSalaryStates.worked_days)
    await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_days_keyboard())


@salaries_router.message(AdminSalaryStates.worked_days)
async def process_days(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.daily_hours)
        return await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_hours_keyboard())
    if message.text == "✍️ Boshqa":
        await state.set_state(AdminSalaryStates.custom_worked_days)
        return await message.answer("📅 Ishlagan kunni o'zingiz kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, to'g'ri kunni tanlang yoki raqam kiriting:")
    await state.update_data(worked_days=int(message.text))
    await state.set_state(AdminSalaryStates.has_ielts)
    await message.answer("🎓 IELTS bormi?", reply_markup=get_yes_no_keyboard())


@salaries_router.message(AdminSalaryStates.custom_worked_days)
async def process_custom_days(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.worked_days)
        return await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_days_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat raqam kiriting (Masalan: 26):")
    await state.update_data(worked_days=int(message.text))
    await state.set_state(AdminSalaryStates.has_ielts)
    await message.answer("🎓 IELTS bormi?", reply_markup=get_yes_no_keyboard())


@salaries_router.message(AdminSalaryStates.has_ielts)
async def process_ielts(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.worked_days)
        return await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_days_keyboard())
    await state.update_data(has_ielts=message.text)
    await state.set_state(AdminSalaryStates.knows_russian)
    await message.answer("🇷🇺 Rus tili bormi?", reply_markup=get_yes_no_keyboard())


@salaries_router.message(AdminSalaryStates.knows_russian)
async def process_russian(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.has_ielts)
        return await message.answer("🎓 IELTS bormi?", reply_markup=get_yes_no_keyboard())
    await state.update_data(knows_russian=message.text)
    await state.set_state(AdminSalaryStates.missed)
    await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_yes_no_keyboard())


@salaries_router.message(AdminSalaryStates.missed)
async def process_missed(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.knows_russian)
        return await message.answer("🇷🇺 Rus tili bormi?", reply_markup=get_yes_no_keyboard())
    if message.text == "✅ HA":
        await state.set_state(AdminSalaryStates.missed_hours)
        await message.answer("⏰ Necha soat ish qoldirdingiz? (Javobni kiriting):", reply_markup=get_manual_keyboard())
    else:
        await state.update_data(missed_hours=0)
        await state.set_state(AdminSalaryStates.cover)
        await message.answer("🔄 Cover qildingizmi?", reply_markup=get_yes_no_keyboard())


@salaries_router.message(AdminSalaryStates.missed_hours)
async def process_missed_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.missed)
        return await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_yes_no_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, soatni faqat raqamda kiriting:")
    await state.update_data(missed_hours=float(message.text))
    await state.set_state(AdminSalaryStates.cover)
    await message.answer("🔄 Cover qildingizmi?", reply_markup=get_yes_no_keyboard())


@salaries_router.message(AdminSalaryStates.cover)
async def process_cover(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.missed)
        return await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_yes_no_keyboard())
    if message.text == "✅ HA":
        await state.set_state(AdminSalaryStates.cover_hours)
        await message.answer("⏰ Nechi soat cover qildingiz? (Javobni kiriting):", reply_markup=get_manual_keyboard())
    else:
        await state.update_data(cover_hours=0)
        await state.set_state(AdminSalaryStates.individual_plan)
        await message.answer("💰 Individual plan kiriting (Faqat raqam):", reply_markup=get_manual_keyboard())


@salaries_router.message(AdminSalaryStates.cover_hours)
async def process_cover_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.cover)
        return await message.answer("🔄 Cover qildingizmi?", reply_markup=get_yes_no_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, soatni faqat raqamda kiriting:")
    await state.update_data(cover_hours=float(message.text))
    await state.set_state(AdminSalaryStates.individual_plan)
    await message.answer("💰 Individual plan kiriting (Faqat raqam):", reply_markup=get_manual_keyboard())


@salaries_router.message(AdminSalaryStates.individual_plan)
async def process_individual_plan(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.cover)
        return await message.answer("🔄 Cover qildingizmi?", reply_markup=get_yes_no_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, rejani faqat raqamda kiriting:")
    await state.update_data(individual_plan=float(message.text))
    await state.set_state(AdminSalaryStates.actual_sales)
    await message.answer("📊 Actual sales (Faktik savdo) kiriting:", reply_markup=get_manual_keyboard())


@salaries_router.message(AdminSalaryStates.actual_sales)
async def process_actual_sales(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.individual_plan)
        return await message.answer("💰 Individual plan kiriting (Faqat raqam):", reply_markup=get_manual_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, faktik savdoni faqat raqamda kiriting:")
    await state.update_data(actual_sales=float(message.text))
    await state.set_state(AdminSalaryStates.conversion_plan)
    await message.answer("📈 Conversion plan (Konversiya rejasi %) kiriting:", reply_markup=get_manual_keyboard())


@salaries_router.message(AdminSalaryStates.conversion_plan)
async def process_conversion_plan(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.actual_sales)
        return await message.answer("📊 Actual sales (Faktik savdo) kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, konversiya rejasini faqat raqamda kiriting:")
    await state.update_data(conversion_plan=float(message.text))
    await state.set_state(AdminSalaryStates.actual_conversion)
    await message.answer("📉 Actual conversion (Faktik konversiya %) kiriting:", reply_markup=get_manual_keyboard())


@salaries_router.message(AdminSalaryStates.actual_conversion)
async def process_actual_conversion(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.conversion_plan)
        return await message.answer("📈 Conversion plan (Konversiya rejasi %) kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, faktik konversiyani faqat raqamda kiriting:")
    await state.update_data(actual_conversion=float(message.text))
    await state.set_state(AdminSalaryStates.active_plan)
    await message.answer("👥 Active plan (Aktivlar rejasi) kiriting:", reply_markup=get_manual_keyboard())


@salaries_router.message(AdminSalaryStates.active_plan)
async def process_active_plan(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.actual_conversion)
        return await message.answer("📉 Actual conversion (Faktik konversiya %) kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, aktivlar rejasini faqat raqamda kiriting:")
    await state.update_data(active_plan=float(message.text))
    await state.set_state(AdminSalaryStates.actual_active)
    await message.answer("👤 Actual active (Faktik aktivlar) kiriting:", reply_markup=get_manual_keyboard())


@salaries_router.message(AdminSalaryStates.actual_active)
async def process_actual_active_final(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.active_plan)
        return await message.answer("👥 Active plan (Aktivlar rejasi) kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, faktik aktivlarni faqat raqamda kiriting:")
    await state.update_data(actual_active=float(message.text))
    
    data = await state.get_data()
    await state.clear()
    result = calculate_admin_salary(data)
    
    report_text = (
        f"💰 <b>OYLIK HISOB-KITOB PANELI</b>\n\n"
        f"🧑‍💼 <b>Status:</b> {str(data.get('status')).upper()}\n"
        f"⏰ <b>Ish tartibi:</b> {data.get('daily_hours')} soat / {data.get('worked_days')} kun\n\n"
        f"💵 <b>Fixa maosh:</b> {result['fixa']:,} so'm\n"
        f"🏆 <b>KPI Bonus:</b> {result['final_kpi_bonus']:,} so'm\n\n"
        f"🎁 <b>Qo'shimchalar:</b>\n"
        f"🇷🇺 Rus tili bonus: +{result['russian_bonus']:,} so'm\n"
        f"🎓 IELTS bonus: +{result['ielts_bonus']:,} so'm\n"
        f"🔄 Cover bonus: +{result['cover_bonus']:,} so'm\n\n"
        f"📉 <b>Jarima (Ish qoldirish):</b> -{result['penalty']:,} so'm\n"
        f"📊 <b>Umumiy KPI:</b> {result['weighted_kpi']}%\n"
        f"-----------------------------------------\n"
        f"🏁 <b>JAMI OYLIK MAOSH:</b> <u>{result['total_salary']:,} so'm</u>"
    )
    
    role = USERS_ROLES[str(message.from_user.id)]["role"]
    await message.answer(text=report_text, parse_mode="HTML", reply_markup=get_main_menu(role))


# ================= KASSIR OYLIK =================

@salaries_router.message(F.text == "💰 Kassir oylik")
async def start_cashier_salary(message: types.Message, state: FSMContext):
    if USERS_ROLES is None:
        await message.answer("⚠️ Tizim xatosi: Ma'lumotlar yuklanmagan. Iltimos /start buyrug'ini yuboring.")
        return
    
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    await state.set_state(CashierSalaryStates.hours)
    await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_cashier_hours_keyboard())


@salaries_router.message(CashierSalaryStates.hours)
async def process_cashier_hours(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES[str(message.from_user.id)]["role"]
        return await message.answer("Asosiy menyudasiz:", reply_markup=get_main_menu(role))
    if message.text == "✍️ Boshqa":
        await state.set_state(CashierSalaryStates.custom_hours)
        return await message.answer("⏰ Soatni o'zingiz kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, tugmalardan foydalaning yoki raqam kiriting:")
    await state.update_data(hours=int(message.text))
    await state.set_state(CashierSalaryStates.days)
    await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_cashier_days_keyboard())


@salaries_router.message(CashierSalaryStates.custom_hours)
async def process_cashier_custom_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.hours)
        return await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_cashier_hours_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Faqat raqam kiriting:")
    await state.update_data(hours=int(message.text))
    await state.set_state(CashierSalaryStates.days)
    await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_cashier_days_keyboard())


@salaries_router.message(CashierSalaryStates.days)
async def process_cashier_days(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.hours)
        return await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_cashier_hours_keyboard())
    if message.text == "✍️ Boshqa":
        await state.set_state(CashierSalaryStates.custom_days)
        return await message.answer("📅 Ishlagan kunni o'zingiz kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ To'g'ri kun kiriting:")
    await state.update_data(days=int(message.text))
    await state.set_state(CashierSalaryStates.cover)
    await message.answer("🔄 Cover qildingizmi?", reply_markup=get_cashier_yes_no_keyboard())


@salaries_router.message(CashierSalaryStates.custom_days)
async def process_cashier_custom_days(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.days)
        return await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_cashier_days_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Faqat raqam kiriting:")
    await state.update_data(days=int(message.text))
    await state.set_state(CashierSalaryStates.cover)
    await message.answer("🔄 Cover qildingizmi?", reply_markup=get_cashier_yes_no_keyboard())


@salaries_router.message(CashierSalaryStates.cover)
async def process_cashier_cover(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.days)
        return await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_cashier_days_keyboard())
    if message.text == "✅ HA":
        await state.set_state(CashierSalaryStates.cover_hours)
        await message.answer("⏰ Necha soat cover qildingiz? (Faqat raqam):", reply_markup=get_manual_keyboard())
    else:
        await state.update_data(cover_hours=0.0)
        await state.set_state(CashierSalaryStates.missed)
        await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_cashier_yes_no_keyboard())


@salaries_router.message(CashierSalaryStates.cover_hours)
async def process_cashier_cover_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.cover)
        return await message.answer("🔄 Cover qildingizmi?", reply_markup=get_cashier_yes_no_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Soatni raqamda kiriting:")
    await state.update_data(cover_hours=float(message.text))
    await state.set_state(CashierSalaryStates.missed)
    await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_cashier_yes_no_keyboard())


@salaries_router.message(CashierSalaryStates.missed)
async def process_cashier_missed(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.cover)
        return await message.answer("🔄 Cover qildingizmi?", reply_markup=get_cashier_yes_no_keyboard())
    if message.text == "✅ HA":
        await state.set_state(CashierSalaryStates.missed_hours)
        await message.answer("⏰ Necha soat ish qoldirdingiz? (Faqat raqam):", reply_markup=get_manual_keyboard())
    else:
        await state.update_data(missed_hours=0.0)
        await state.set_state(CashierSalaryStates.active_students)
        await message.answer("👥 Active students (Aktiv talabalar) sonini kiriting:", reply_markup=get_manual_keyboard())


@salaries_router.message(CashierSalaryStates.missed_hours)
async def process_cashier_missed_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.missed)
        return await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_cashier_yes_no_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Soatni raqamda kiriting:")
    await state.update_data(missed_hours=float(message.text))
    await state.set_state(CashierSalaryStates.active_students)
    await message.answer("👥 Active students (Aktiv talabalar) sonini kiriting:", reply_markup=get_manual_keyboard())


@salaries_router.message(CashierSalaryStates.active_students)
async def process_active_students(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.missed)
        return await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_cashier_yes_no_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat butun raqam kiriting:")
    await state.update_data(active_students=int(message.text))
    await state.set_state(CashierSalaryStates.active_debtors)
    await message.answer("💸 Active debtors (Aktiv qarzdorlar) sonini kiriting:", reply_markup=get_manual_keyboard())


@salaries_router.message(CashierSalaryStates.active_debtors)
async def process_active_debtors(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.active_students)
        return await message.answer("👥 Active students (Aktiv talabalar) sonini kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat butun raqam kiriting:")
    await state.update_data(active_debtors=int(message.text))
    await state.set_state(CashierSalaryStates.archive_students)
    await message.answer("🗄 Archive students (Arxiv talabalar) sonini kiriting:", reply_markup=get_manual_keyboard())


@salaries_router.message(CashierSalaryStates.archive_students)
async def process_archive_students(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.active_debtors)
        return await message.answer("💸 Active debtors (Aktiv qarzdorlar) sonini kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat butun raqam kiriting:")
    await state.update_data(archive_students=int(message.text))
    await state.set_state(CashierSalaryStates.archive_debtors)
    await message.answer("📉 Archive debtors (Arxiv qarzdorlar) sonini kiriting:", reply_markup=get_manual_keyboard())


@salaries_router.message(CashierSalaryStates.archive_debtors)
async def process_cashier_final(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.archive_students)
        return await message.answer("🗄 Archive students (Arxiv talabalar) sonini kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat raqam kiriting:")
    await state.update_data(archive_debtors=int(message.text))
    data = await state.get_data()
    await state.clear()
    result = calculate_cashier_salary(data)
    
    report_text = (
        f"💰 <b>KASSIR OYLIK HISOB-KITOB PANELI</b>\n\n"
        f"⏰ <b>Ish tartibi:</b> {data.get('hours')} soat / {data.get('days')} kun\n"
        f"📊 <b>Umumiy talabalar:</b> {result['total_students']} ta\n"
        f"💸 <b>Jami qarzdor xodimlar:</b> {result['total_debtors']} ta\n"
        f"📉 <b>Qarzdorlik foizi:</b> {result['debt_percentage']}%\n"
        f"🎯 <b>Natija darajasi:</b> {result['status_text']}\n\n"
        f"💵 <b>Ishbay sof oylik:</b> {result['worked_salary']:,} so'm\n"
        f"🏆 <b>Qarzdorlik karrali bonusi (Multiplier):</b> +{result['kpi_bonus_profit']:,} so'm\n"
        f"🔄 <b>Cover bonus:</b> +{result['cover_bonus']:,} so'm\n"
        f"⚠️ <b>Ish qoldirish jarimasi:</b> -{result['missed_penalty']:,} so'm\n"
        f"-----------------------------------------\n"
        f"🏁 <b>JAMI OYLIK MAOSH:</b> <u>{result['total_salary']:,} so'm</u>"
    )
    
    role = USERS_ROLES[str(message.from_user.id)]["role"]
    await message.answer(text=report_text, parse_mode="HTML", reply_markup=get_main_menu(role))
