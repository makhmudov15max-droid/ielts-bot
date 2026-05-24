from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from Keyboards.main_menu import (
    get_main_menu,
    get_back_home_keyboard,
    get_settings_main_keyboard,
    get_employee_list_keyboard,
    get_work_time_hours_keyboard,
    get_holiday_main_keyboard,
    get_holiday_type_keyboard
)
from utils.access import check_user_access

settings_router = Router()

# Global o'zgaruvchilar
USERS_ROLES = None


def init_settings_handler(users_roles):
    global USERS_ROLES
    USERS_ROLES = users_roles


class SettingsStates(StatesGroup):
    waiting_for_action = State()
    waiting_for_employee = State()
    waiting_for_work_time = State()
    waiting_for_custom_time = State()
    waiting_for_holiday_action = State()
    waiting_for_holiday_date = State()
    waiting_for_holiday_name = State()
    waiting_for_holiday_delete_id = State()


@settings_router.message(F.text == "⚙️ Sozlamalar")
async def settings_main_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    await state.clear()
    await state.set_state(SettingsStates.waiting_for_action)
    await message.answer(
        text="⚙️ <b>Sozlamalar paneli</b>\n\n"
             "Quyidagi bo'limlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=get_settings_main_keyboard()
    )


# ================= HODIM ISH VAQTLARI =================
@settings_router.message(SettingsStates.waiting_for_action, F.text == "👤 Hodim ish vaqtlari")
async def settings_work_time_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    # Barcha xodimlarni olish (Owner va rejected dan tashqari)
    employees = []
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("name") and u_info.get("role") not in ["Owner", "rejected"]:
            employees.append({"id": u_id, "name": u_info["name"]})
    
    if not employees:
        await message.answer(
            text="📭 Hozircha tizimda xodimlar mavjud emas.",
            reply_markup=get_back_home_keyboard()
        )
        return
    
    await state.set_state(SettingsStates.waiting_for_employee)
    await message.answer(
        text="👤 <b>Ish vaqtini belgilamoqchi bo'lgan hodimni tanlang:</b>\n\n"
             "⚠️ Eslatma: Standart ish vaqti 09:00",
        parse_mode="HTML",
        reply_markup=get_employee_list_keyboard(employees, back_button_text="⬅️ Ortga")
    )


@settings_router.message(SettingsStates.waiting_for_employee, F.text.startswith("👤 "))
async def settings_work_time_employee_selected(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
        return
    elif message.text == "⬅️ Ortga":
        await state.set_state(SettingsStates.waiting_for_action)
        await message.answer(
            text="⚙️ <b>Sozlamalar paneli</b>\n\n"
                 "Quyidagi bo'limlardan birini tanlang:",
            parse_mode="HTML",
            reply_markup=get_settings_main_keyboard()
        )
        return
    
    employee_name = message.text.replace("👤 ", "").strip()
    await state.update_data(employee_name=employee_name)
    
    await state.set_state(SettingsStates.waiting_for_work_time)
    await message.answer(
        text=f"👤 <b>{employee_name}</b>\n\n"
             f"⏰ <b>Yangi ish boshlanish vaqtini tanlang:</b>\n\n"
             f"Format: <code>HH:MM</code> (masalan: 09:00)",
        parse_mode="HTML",
        reply_markup=get_work_time_hours_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_work_time)
async def settings_work_time_set_handler(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
        return
    elif message.text == "⬅️ Ortga":
        await state.set_state(SettingsStates.waiting_for_employee)
        employees = []
        for u_id, u_info in USERS_ROLES.items():
            if isinstance(u_info, dict) and u_info.get("name") and u_info.get("role") not in ["Owner", "rejected"]:
                employees.append({"id": u_id, "name": u_info["name"]})
        await message.answer(
            text="👤 Hodimni qayta tanlang:",
            reply_markup=get_employee_list_keyboard(employees)
        )
        return
    elif message.text == "✍️ Boshqa vaqt":
        await state.set_state(SettingsStates.waiting_for_custom_time)
        await message.answer(
            text="⏰ Iltimos, ish vaqtini <code>HH:MM</code> formatida kiriting.\n\n"
                 "Masalan: <code>09:30</code>",
            parse_mode="HTML",
            reply_markup=get_back_home_keyboard()
        )
        return
    
    start_time = message.text.strip()
    
    # Logika keyin qo'shiladi
    user_data = await state.get_data()
    employee_name = user_data.get('employee_name')
    
    await state.clear()
    await state.set_state(SettingsStates.waiting_for_action)
    
    await message.answer(
        text=f"✅ <b>{employee_name}</b> uchun ish boshlanish vaqti <b>{start_time}</b> qilib belgilandi!\n\n"
             f"⚠️ Ma'lumotlar bazasiga saqlash logikasi hozircha ishlab chiqilmoqda.",
        parse_mode="HTML",
        reply_markup=get_settings_main_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_custom_time)
async def settings_work_time_custom_handler(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
        return
    elif message.text == "⬅️ Ortga":
        await state.set_state(SettingsStates.waiting_for_work_time)
        user_data = await state.get_data()
        employee_name = user_data.get('employee_name')
        await message.answer(
            text=f"👤 <b>{employee_name}</b>\n\n"
                 f"⏰ <b>Yangi ish boshlanish vaqtini tanlang:</b>",
            parse_mode="HTML",
            reply_markup=get_work_time_hours_keyboard()
        )
        return
    
    import re
    start_time = message.text.strip()
    if not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", start_time):
        await message.answer(
            text="❌ <b>Noto'g'ri format!</b>\n\n"
                 "Iltimos, vaqtni <code>HH:MM</code> formatida kiriting.\n"
                 "Masalan: <code>09:00</code>",
            parse_mode="HTML"
        )
        return
    
    user_data = await state.get_data()
    employee_name = user_data.get('employee_name')
    
    await state.clear()
    await state.set_state(SettingsStates.waiting_for_action)
    
    await message.answer(
        text=f"✅ <b>{employee_name}</b> uchun ish boshlanish vaqti <b>{start_time}</b> qilib belgilandi!\n\n"
             f"⚠️ Ma'lumotlar bazasiga saqlash logikasi hozircha ishlab chiqilmoqda.",
        parse_mode="HTML",
        reply_markup=get_settings_main_keyboard()
    )


# ================= TA'TIL SANALARI =================
@settings_router.message(SettingsStates.waiting_for_action, F.text == "📅 Ta'til sanalari")
async def settings_holiday_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    await state.set_state(SettingsStates.waiting_for_holiday_action)
    await message.answer(
        text="📅 <b>Ta'til sanalari paneli</b>\n\n"
             "Quyidagi amallardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=get_holiday_main_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_holiday_action, F.text == "➕ Ta'til qo'shish")
async def settings_holiday_add_start(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_holiday_date)
    await message.answer(
        text="📅 <b>Ta'til sanasini kiriting:</b>\n\n"
             "Format: <code>YYYY-MM-DD</code>\n"
             "Masalan: <code>2026-09-01</code>",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_holiday_date)
async def settings_holiday_add_date_handler(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
        return
    elif message.text == "⬅️ Ortga":
        await state.set_state(SettingsStates.waiting_for_holiday_action)
        await message.answer(
            text="📅 <b>Ta'til sanalari paneli</b>\n\n"
                 "Quyidagi amallardan birini tanlang:",
            parse_mode="HTML",
            reply_markup=get_holiday_main_keyboard()
        )
        return
    
    import re
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer(
            text="❌ <b>Noto'g'ri format!</b>\n\n"
                 "Iltimos, sanani <code>YYYY-MM-DD</code> formatida kiriting.\n"
                 "Masalan: <code>2026-09-01</code>",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(holiday_date=date_text)
    await state.set_state(SettingsStates.waiting_for_holiday_name)
    await message.answer(
        text=f"📅 <b>Sana:</b> {date_text}\n\n"
             f"🎉 <b>Bayram turini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_holiday_type_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_holiday_name)
async def settings_holiday_add_name_handler(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
        return
    elif message.text == "⬅️ Ortga":
        await state.set_state(SettingsStates.waiting_for_holiday_date)
        await message.answer(
            text="📅 Sanani qayta kiriting:",
            reply_markup=get_back_home_keyboard()
        )
        return
    elif message.text == "📝 Boshqa":
        await message.answer(
            text="✍️ Iltimos, bayram nomini kiriting:",
            reply_markup=get_back_home_keyboard()
        )
        return
    
    user_data = await state.get_data()
    holiday_date = user_data.get('holiday_date')
    holiday_name = message.text.strip()
    
    await state.clear()
    await state.set_state(SettingsStates.waiting_for_holiday_action)
    
    await message.answer(
        text=f"✅ <b>Bayram muvaffaqiyatli qo'shildi!</b>\n\n"
             f"📅 Sana: {holiday_date}\n"
             f"🎉 Bayram: {holiday_name}\n\n"
             f"⚠️ Ma'lumotlar bazasiga saqlash logikasi hozircha ishlab chiqilmoqda.",
        parse_mode="HTML",
        reply_markup=get_holiday_main_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_holiday_name, F.text == "📝 Boshqa")
async def settings_holiday_add_custom_name(message: types.Message, state: FSMContext):
    await message.answer(
        text="✍️ Iltimos, bayram nomini kiriting:",
        reply_markup=get_back_home_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_holiday_action, F.text == "❌ Ta'tilni o'chirish")
async def settings_holiday_delete_start(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_holiday_delete_id)
    await message.answer(
        text="📋 <b>Ta'tillar ro'yxati</b>\n\n"
             "Hozircha ta'tillar mavjud emas.\n\n"
             "⚠️ Ma'lumotlar bazasiga saqlash logikasi hozircha ishlab chiqilmoqda.\n\n"
             "❌ O'chirmoqchi bo'lgan ta'tilning ID raqamini kiriting:\n"
             "Masalan: <code>2</code>",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_holiday_delete_id)
async def settings_holiday_delete_process(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
        return
    elif message.text == "⬅️ Ortga":
        await state.set_state(SettingsStates.waiting_for_holiday_action)
        await message.answer(
            text="📅 <b>Ta'til sanalari paneli</b>\n\n"
                 "Quyidagi amallardan birini tanlang:",
            parse_mode="HTML",
            reply_markup=get_holiday_main_keyboard()
        )
        return
    
    try:
        holiday_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            text="❌ Iltimos, to'g'ri ID raqamini kiriting!",
            reply_markup=get_back_home_keyboard()
        )
        return
    
    await state.clear()
    await state.set_state(SettingsStates.waiting_for_holiday_action)
    
    await message.answer(
        text=f"✅ <b>Ta'til muvaffaqiyatli o'chirildi!</b>\n\n"
             f"🆔 ID: {holiday_id}\n\n"
             f"⚠️ Ma'lumotlar bazasiga saqlash logikasi hozircha ishlab chiqilmoqda.",
        parse_mode="HTML",
        reply_markup=get_holiday_main_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_holiday_action, F.text == "📋 Ta'til ro'yxati")
async def settings_holiday_list_handler(message: types.Message, state: FSMContext):
    await message.answer(
        text="📅 <b>Ta'til sanalari ro'yxati</b>\n\n"
             "📌 <b>Yanvar</b>\n"
             "   • 2026-01-01 — Yangi yil\n\n"
             "📌 <b>Mart</b>\n"
             "   • 2026-03-21 — Navro'z\n\n"
             "📌 <b>Sentabr</b>\n"
             "   • 2026-09-01 — Mustaqillik kuni\n\n"
             "⚠️ Ma'lumotlar bazasiga saqlash logikasi hozircha ishlab chiqilmoqda.",
        parse_mode="HTML",
        reply_markup=get_holiday_main_keyboard()
    )


@settings_router.message(SettingsStates.waiting_for_holiday_action, F.text == "🏠 Bosh sahifa")
async def settings_holiday_back_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_holiday_action, F.text == "⬅️ Ortga")
async def settings_holiday_back_main(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_action)
    await message.answer(
        text="⚙️ <b>Sozlamalar paneli</b>\n\n"
             "Quyidagi bo'limlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=get_settings_main_keyboard()
    )


# ================= UMUMIY ORTGA VA BOSH SAHIFA =================
@settings_router.message(SettingsStates.waiting_for_action, F.text == "🏠 Bosh sahifa")
async def settings_back_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@settings_router.message(SettingsStates.waiting_for_action, F.text == "⬅️ Ortga")
async def settings_back_main(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
