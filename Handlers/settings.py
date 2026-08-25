from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

from Keyboards.main_menu import get_main_menu, get_back_home_keyboard, get_settings_role_keyboard, get_work_time_keyboard, get_settings_main_keyboard
from utils.access import check_user_access
from utils.users_db import set_user_work_time, get_user_work_time
from utils.fines_db import get_tariffs_for_role, save_tariffs_for_role

settings_router = Router()

# ================= GLOBAL O'ZGARUVCHILAR =================
USERS_ROLES = None
ADMIN_ID = None


def init_settings_handler(users_roles, admin_id):
    global USERS_ROLES, ADMIN_ID
    USERS_ROLES = users_roles
    ADMIN_ID = admin_id


# ================= STATES =================
class SettingsStates(StatesGroup):
    waiting_for_main_choice = State()   # Ta'tillar / Ish smena
    waiting_for_role = State()
    waiting_for_employee = State()
    waiting_for_work_time = State()
    waiting_for_custom_time = State()
    # Jarimalar (tarif belgilash)
    waiting_for_fine_role = State()     # Jarimalar -> rol tanlash
    waiting_for_fine_amount = State()   # interval summasi kiritish
    waiting_for_fine_interval = State() # interval (min-max) kiritish


# ================= YORDAMCHI FUNKSIYA =================
def get_employees_by_role(role: str):
    employees = []
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == role and u_info.get("name"):
            employees.append((u_id, u_info["name"]))
    return employees


# ================= SOZLAMALAR ASOSIY MENU =================
@settings_router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    user_role = USERS_ROLES.get(str(message.from_user.id), {}).get("role")
    if user_role not in ["Owner", "Manager"]:
        await message.answer("⚠️ Bu bo'lim faqat Owner va Manager uchun!")
        return
    
    await state.set_state(SettingsStates.waiting_for_main_choice)
    await message.answer(
        text="⚙️ <b>Sozlamalar</b>\n\nQaysi bo'limni sozlamoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_settings_main_keyboard()
    )


# ================= TA'TIL VA ISH SMENA TANLASH =================
@settings_router.message(SettingsStates.waiting_for_main_choice, F.text == "🌴 Ta'tillar")
async def settings_holidays_choice(message: types.Message, state: FSMContext):
    # To'g'ridan-to'g'ri holidays handleriga o'tish
    from Handlers.holidays import HolidayStates, get_holiday_action_keyboard
    await state.clear()
    await state.set_state(HolidayStates.waiting_for_action)
    await message.answer(
        text="🌴 <b>Ta'tillarni boshqarish</b>\n\nQanday amalni bajarmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_holiday_action_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_main_choice, F.text == "🏢 Ish smena")
async def settings_worktime_choice(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_role)
    await message.answer(
        text="Qaysi bo'lim xodimlarining ish vaqtini o'zgartirmoqchisiz?",
        reply_markup=get_settings_role_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_main_choice, F.text == "🏠 Bosh sahifa")
async def settings_main_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_main_choice, F.text == "⬅️ Ortga")
async def settings_main_back(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_main_choice)
async def invalid_main_choice(message: types.Message):
    await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_settings_main_keyboard())


# ================= ROL TANLASH (ISH SMENA UCHUN) =================
@settings_router.message(SettingsStates.waiting_for_role, F.text == "🏠 Bosh sahifa")
async def settings_role_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_role, F.text == "⬅️ Ortga")
async def settings_role_back(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_main_choice)
    await message.answer(
        text="⚙️ <b>Sozlamalar</b>\n\nQaysi bo'limni sozlamoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_settings_main_keyboard()
    )


VALID_ROLES_FOR_SETTINGS = ["Admin", "Kassir", "Sanitar", "Manager", "Maintenance", "Head Admin", "Manager Assistant"]

@settings_router.message(SettingsStates.waiting_for_role, F.text.in_(VALID_ROLES_FOR_SETTINGS))
async def select_role_for_settings(message: types.Message, state: FSMContext):
    role = message.text.strip()
    if role not in VALID_ROLES_FOR_SETTINGS:
        await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_settings_role_keyboard())
        return
    employees = get_employees_by_role(role)
    
    if not employees:
        await message.answer(
            f"⚠️ <b>{role}</b> rolida xodimlar topilmadi!",
            parse_mode="HTML",
            reply_markup=get_settings_role_keyboard()
        )
        return
    
    await state.update_data(selected_role=role)
    
    inline_keyboard = []
    for u_id, name in employees:
        inline_keyboard.append([types.InlineKeyboardButton(text=f"👤 {name}", callback_data=f"set_worktime_{u_id}")])
    inline_keyboard.append([types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_settings")])
    
    await state.set_state(SettingsStates.waiting_for_employee)
    await message.answer(
        text=f"👥 <b>{role}</b> rolidagi xodimlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    )


@settings_router.message(SettingsStates.waiting_for_role)
async def invalid_role_selected(message: types.Message, state: FSMContext):
    # Strip qilib qayta tekshiramiz (encoding muammosi uchun)
    role = message.text.strip() if message.text else ""
    if role in VALID_ROLES_FOR_SETTINGS:
        return await select_role_for_settings(message, state)
    await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_settings_role_keyboard())


# ================= XODIM TANLASH =================
@settings_router.callback_query(SettingsStates.waiting_for_employee, F.data.startswith("set_worktime_"))
async def select_employee_for_settings(call: types.CallbackQuery, state: FSMContext):
    user_id = call.data.split("_")[2]
    user_info = USERS_ROLES.get(user_id, {})
    user_name = user_info.get("name", "Noma'lum")
    
    work_start, work_end = await get_user_work_time(user_id)
    
    await state.update_data(target_user_id=user_id, target_user_name=user_name)
    await state.set_state(SettingsStates.waiting_for_work_time)
    
    await call.message.delete()
    await call.message.answer(
        text=f"👤 <b>{user_name}</b>\n\n"
             f"⏰ <b>Joriy ish vaqti:</b> {work_start} - {work_end}\n\n"
             f"Yangi ish vaqtini tanlang:",
        parse_mode="HTML",
        reply_markup=get_work_time_keyboard()
    )
    await call.answer()


@settings_router.callback_query(F.data == "cancel_settings")
async def cancel_settings_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(call.from_user.id), {}).get("role", "Owner")
    await call.message.delete()
    await call.message.answer("❌ Bekor qilindi.", reply_markup=get_main_menu(role))
    await call.answer()


# ================= ISH VAQTINI TANLASH =================
@settings_router.message(SettingsStates.waiting_for_work_time, F.text == "🏠 Bosh sahifa")
async def settings_worktime_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_work_time, F.text == "⬅️ Ortga")
async def settings_worktime_back(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_role)
    await message.answer(
        text="Qaysi bo'lim xodimlarining ish vaqtini o'zgartirmoqchisiz?",
        reply_markup=get_settings_role_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_work_time, F.text == "✍️ Boshqa vaqt")
async def ask_custom_worktime(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_custom_time)
    await message.answer(
        text="✍️ <b>Ish vaqtini kiriting</b>\n\n"
             "Format: <code>09:00 - 18:00</code>\n\n"
             "Masalan: <code>08:00 - 14:00</code> yoki <code>14:00 - 21:00</code>",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_work_time)
async def set_worktime_handler(message: types.Message, state: FSMContext):
    shift_name = message.text
    shift_map = {
        "1-smena (08:00 - 14:00)": ("08:00", "14:00"),
        "2-smena (14:00 - 21:00)": ("14:00", "21:00"),
        "3-smena (09:00 - 18:00)": ("09:00", "18:00"),
    }
    
    if shift_name not in shift_map:
        await message.answer("❌ Iltimos, tugmalardan birini tanlang!")
        return
    
    start_time, end_time = shift_map[shift_name]
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    target_user_name = data.get("target_user_name")
    
    await set_user_work_time(target_user_id, start_time, end_time)
    
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer(
        text=f"✅ <b>{target_user_name}</b> uchun ish vaqti belgilandi!\n\n"
             f"⏰ <b>Yangi ish vaqti:</b> {start_time} - {end_time}",
        parse_mode="HTML",
        reply_markup=get_main_menu(role)
    )


# ================= CUSTOM VAQT =================
@settings_router.message(SettingsStates.waiting_for_custom_time, F.text == "🏠 Bosh sahifa")
async def custom_time_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_custom_time, F.text == "⬅️ Ortga")
async def custom_time_back(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_work_time)
    await message.answer(
        text="Yangi ish vaqtini tanlang:",
        reply_markup=get_work_time_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_custom_time)
async def set_custom_worktime(message: types.Message, state: FSMContext):
    time_text = message.text.strip()
    match = re.match(r"(\d{2}:\d{2})\s*[-–]\s*(\d{2}:\d{2})", time_text)
    
    if not match:
        await message.answer(
            text="❌ <b>Noto'g'ri format!</b>\n\n"
                 "Iltimos, quyidagi formatlardan birini ishlating:\n"
                 "• <code>09:00 - 18:00</code>\n"
                 "• <code>08:00-14:00</code>\n"
                 "• <code>14:00–21:00</code>",
            parse_mode="HTML"
        )
        return
    
    start_time, end_time = match.groups()
    
    time_pattern = re.compile(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    if not time_pattern.match(start_time) or not time_pattern.match(end_time):
        await message.answer("❌ Vaqt noto'g'ri formatda! Masalan: <code>09:00</code>", parse_mode="HTML")
        return
    
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    target_user_name = data.get("target_user_name")
    
    await set_user_work_time(target_user_id, start_time, end_time)
    
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer(
        text=f"✅ <b>{target_user_name}</b> uchun ish vaqti belgilandi!\n\n"
             f"⏰ <b>Yangi ish vaqti:</b> {start_time} - {end_time}",
        parse_mode="HTML",
        reply_markup=get_main_menu(role)
    )


# ================= YORDAMCHI FUNKSIYALAR (HOLIDAYS UCHUN) =================
def get_holiday_action_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Ta'til kiritish"), KeyboardButton(text="✏️ Ta'til o'zgartirish")],
            [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )


# ================= JARIMALAR (TARIF BELGILASH) =================

VALID_FINE_ROLES = ["Admin", "Kassir", "Sanitar", "Manager", "Maintenance", "Head Admin", "Manager Assistant"]

def get_fine_role_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Admin"), KeyboardButton(text="Kassir")],
            [KeyboardButton(text="Sanitar"), KeyboardButton(text="Manager")],
            [KeyboardButton(text="Maintenance"), KeyboardButton(text="Head Admin")],
            [KeyboardButton(text="Manager Assistant")],
            [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )

def get_fine_actions_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Interval qo'shish"), KeyboardButton(text="🗑 Barcha intervallarni o'chirish")],
            [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )


@settings_router.message(SettingsStates.waiting_for_main_choice, F.text == "💰 Jarimalar")
async def settings_fines_choice(message: types.Message, state: FSMContext):
    """💰 Jarimalar tugmasi bosilganda - rol tanlash"""
    await state.set_state(SettingsStates.waiting_for_fine_role)
    await message.answer(
        text="💰 <b>Jarimalar</b>\n\nQaysi rol uchun jarima tariflarini belgilamoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_fine_role_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_fine_role, F.text == "🏠 Bosh sahifa")
async def fine_role_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_fine_role, F.text == "⬅️ Ortga")
async def fine_role_back(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_main_choice)
    await message.answer(
        text="⚙️ <b>Sozlamalar</b>\n\nQaysi bo'limni sozlamoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_settings_main_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_fine_role)
async def select_fine_role(message: types.Message, state: FSMContext):
    role = message.text.strip()
    if role not in VALID_FINE_ROLES:
        await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_fine_role_keyboard())
        return

    await state.update_data(fine_role=role)
    await state.set_state(SettingsStates.waiting_for_fine_interval)

    # Hozirgi tariflarni ko'rsatish
    tariffs = await get_tariffs_for_role(role)
    if tariffs:
        text_lines = [f"<b>{role}</b> uchun joriy jarima tariflari:\n"]
        for t in tariffs:
            text_lines.append(f"• {t['min_minutes']}-{t['max_minutes']} daqiqa → {t['amount']:,} so'm".replace(",", " "))
        text_lines.append("\nO'zgartirish uchun quyidagi tugmalardan foydalaning:")
        tariff_text = "\n".join(text_lines)
    else:
        tariff_text = f"<b>{role}</b> uchun hozircha tarif belgilanmagan.\n\n"
        tariff_text += "Biror interval qo'shishingiz mumkin."

    await message.answer(
        text=tariff_text,
        parse_mode="HTML",
        reply_markup=get_fine_actions_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_fine_interval, F.text == "➕ Interval qo'shish")
async def fine_add_interval_prompt(message: types.Message):
    await message.answer(
        text="➕ <b>Yangi interval</b>\n\n"
             "Kechikish daqiqalari oralig'ini kiriting (min-max):\n"
             "• <code>1-5</code> → 1 dan 5 daqiqagacha\n"
             "• <code>6-15</code> → 6 dan 15 daqiqagacha\n\n"
             "Masalan: <code>1-5</code>",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_fine_interval, F.text == "🗑 Barcha intervallarni o'chirish")
async def fine_clear_intervals(message: types.Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("fine_role")
    if role:
        from utils.fines_db import clear_tariffs_for_role
        await clear_tariffs_for_role(role)
    await message.answer(
        text=f"🗑 <b>{role}</b> uchun barcha jarima tariflari o'chirildi.\n\n"
             f"Endi bu rol xodimi kech qolsa, jarima qo'yilmaydi (eski tizim).",
        parse_mode="HTML",
        reply_markup=get_fine_actions_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_fine_interval, F.text == "🏠 Bosh sahifa")
async def fine_interval_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_fine_interval, F.text == "⬅️ Ortga")
async def fine_interval_back(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_fine_role)
    await message.answer(
        text="💰 <b>Jarimalar</b>\n\nQaysi rol uchun jarima tariflarini belgilamoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_fine_role_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_fine_interval)
async def fine_parse_interval(message: types.Message, state: FSMContext):
    """Interval matnini parse qilish (masalan 1-5)"""
    text = message.text.strip()
    match = re.match(r"^(\d+)\s*[-–]\s*(\d+)$", text)
    if not match:
        await message.answer("❌ Noto'g'ri format! Masalan: <code>1-5</code> yoki <code>6-15</code>", parse_mode="HTML")
        return
    min_m = int(match.group(1))
    max_m = int(match.group(2))
    if min_m < 0 or max_m <= min_m:
        await message.answer("❌ Noto'g'ri interval! Min 0 dan kichik emas, max dan katta bo'lishi kerak.")
        return

    # Yangi intervalni mavjudlariga tekshirish (bir-biriga kirib ketmasligi)
    data = await state.get_data()
    role = data.get("fine_role")

    # Interval bir-biriga kirib ketmasligini tekshirish
    tariffs = await get_tariffs_for_role(role)
    for t in tariffs:
        if not (max_m < t["min_minutes"] or min_m > t["max_minutes"]):
            await message.answer(
                f"❌ Bu interval ({min_m}-{max_m}) allaqachon mavjud tarif bilan kesishadi "
                f"({t['min_minutes']}-{t['max_minutes']} → {t['amount']} so'm).",
                parse_mode="HTML"
            )
            return

    await state.update_data(pending_min=min_m, pending_max=max_m)
    await state.set_state(SettingsStates.waiting_for_fine_amount)
    await message.answer(
        text=f"📝 <b>{min_m}-{max_m} daqiqa</b> kechikish uchun jarima summasini kiriting (so'mda):\n\n"
             f"Masalan: <code>10000</code>",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_fine_amount, F.text == "🏠 Bosh sahifa")
async def fine_amount_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_fine_amount, F.text == "⬅️ Ortga")
async def fine_amount_back(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_fine_interval)
    data = await state.get_data()
    role = data.get("fine_role")
    await message.answer(
        text=f"<b>{role}</b> uchun jarima tariflari:",
        parse_mode="HTML",
        reply_markup=get_fine_actions_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_fine_amount)
async def fine_parse_amount(message: types.Message, state: FSMContext):
    text = message.text.strip().replace(" ", "").replace(",", "").replace(".", "")
    if not text.isdigit() or int(text) <= 0:
        await message.answer("❌ Iltimos, musbat butun son kiriting (so'mda). Masalan: <code>10000</code>", parse_mode="HTML")
        return

    amount = int(text)
    data = await state.get_data()
    role = data.get("fine_role")
    min_m = data.get("pending_min")
    max_m = data.get("pending_max")

    # Tariflarni saqlash (avvalgisini olib + yangi)
    existing = await get_tariffs_for_role(role)
    new_tariffs = [(t["min_minutes"], t["max_minutes"], t["amount"]) for t in existing]
    new_tariffs.append((min_m, max_m, amount))
    new_tariffs.sort(key=lambda x: x[0])
    await save_tariffs_for_role(role, new_tariffs)

    await state.set_state(SettingsStates.waiting_for_fine_interval)
    tariff_text = f"✅ <b>{min_m}-{max_m} daqiqa</b> → <b>{amount:,} so'm</b> saqlandi.\n\n".replace(",", " ")
    tariff_text += f"<b>{role}</b> uchun joriy tariflar:\n"
    for mn, mx, amt in new_tariffs:
        tariff_text += f"• {mn}-{mx} daqiqa → {amt:,} so'm\n".replace(",", " ")

    await message.answer(
        text=tariff_text,
        parse_mode="HTML",
        reply_markup=get_fine_actions_keyboard()
    )

