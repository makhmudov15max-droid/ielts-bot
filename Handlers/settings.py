from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

from Keyboards.main_menu import get_main_menu, get_back_home_keyboard, get_settings_role_keyboard, get_work_time_keyboard
from utils.access import check_user_access
from utils.users_db import set_user_work_time, get_user_work_time

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
    waiting_for_role = State()
    waiting_for_employee = State()
    waiting_for_work_time = State()
    waiting_for_custom_time = State()


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
    
    await state.set_state(SettingsStates.waiting_for_role)
    await message.answer(
        text="⚙️ <b>Sozlamalar</b>\n\nQaysi bo'lim xodimlarining ish vaqtini o'zgartirmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_settings_role_keyboard()
    )


# ================= ROL TANLASH =================
@settings_router.message(SettingsStates.waiting_for_role, F.text == "🏠 Bosh sahifa")
async def settings_role_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_role, F.text == "⬅️ Ortga")
async def settings_role_back(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_role, F.text.in_(["Admin", "Kassir", "Sanitar", "Manager"]))
async def select_role_for_settings(message: types.Message, state: FSMContext):
    role = message.text
    employees = get_employees_by_role(role)
    
    if not employees:
        await message.answer(f"⚠️ <b>{role}</b> rolida xodimlar topilmadi!", parse_mode="HTML")
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
async def invalid_role_selected(message: types.Message):
    await message.answer("❌ Iltimos, tugmalardan birini tanlang!")


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
