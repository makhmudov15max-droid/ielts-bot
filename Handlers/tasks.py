from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, timezone
import re

from Handlers.states import TaskStates
from Keyboards.main_menu import (
    get_main_menu,
    get_back_home_keyboard,
    get_tasks_simple_keyboard,
    get_custom_date_keyboard_simple,
    task_type_keyboard,
    days_keyboard,
    frequency_keyboard,
    get_inline_days_keyboard,
    proof_type_keyboard,
    assign_role_keyboard,
    get_task_complete_keyboard,
    get_remove_tasks_keyboard
)
from utils.access import check_user_access
from utils.users_json import save_users
from utils.tasks_json import save_tasks, load_tasks

tasks_router = Router()

# ================= GLOBAL O'ZGARUVCHILAR =================
USERS_ROLES = None
TASKS_DATABASE = None


# ================= INIT & HELPERS =================
def init_tasks_handler(users_roles, tasks_database):
    """Tasks handler uchun global o'zgaruvchilarni o'rnatish"""
    global USERS_ROLES, TASKS_DATABASE
    USERS_ROLES = users_roles
    TASKS_DATABASE = tasks_database


# ================= UNIVERSAL BACK/HOME HANDLER =================
async def handle_back_or_home_global(message: types.Message, state: FSMContext, target_state=None):
    """Ortga yoki Bosh sahifa tugmalarini boshqarish - universal"""
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer(
            text="🏠 Asosiy menyuga qaytdingiz.",
            reply_markup=get_main_menu(role)
        )
        return True
    elif message.text == "⬅️ Ortga":
        if target_state:
            await state.set_state(target_state)
            return True
    return False


# ================= VAZIFA YARATISH (ADD) =================
@tasks_router.message(F.text == "➕ Vazifa qoʻshish")
async def add_task_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    await state.clear()
    await message.answer(
        text="Qanday turdagi vazifa yaratmoqchisiz?",
        reply_markup=task_type_keyboard
    )


@tasks_router.message(F.text.in_(["Muntazam (Doimiy)", "Kunlik (Bir martalik)"]))
async def task_type_selected_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    if await handle_back_or_home_global(message, state, None):
        return
    
    await state.update_data(task_type=message.text)
    await message.answer(
        text="Ushbu vazifa qaysi boʻlim/unvon xodimiga tegishli?",
        reply_markup=assign_role_keyboard
    )
    await state.set_state(TaskStates.waiting_for_target_role)


@tasks_router.message(TaskStates.waiting_for_target_role, F.text.in_(["Admin", "Kassir", "Sanitar", "Manager"]))
async def get_target_role_handler(message: types.Message, state: FSMContext):
    if await handle_back_or_home_global(message, state, None):
        return
    
    selected_role = message.text
    await state.update_data(target_role=selected_role)
    
    inline_kb = []
    found_users = False
    
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == selected_role and u_info.get("name"):
            found_users = True
            inline_kb.append([types.InlineKeyboardButton(text=u_info.get("name"), callback_data=f"assignuser_{u_id}")])
            
    if not found_users:
        await message.answer(text=f"⚠️ Diqqat! Tizimda hali tasdiqlangan va ismi kiritilgan '{selected_role}' xodimlari topilmadi!")
        return
        
    await message.answer(
        text=f"Aynan qaysi '{selected_role}' xodimiga ushbu vazifani biriktirmoqchisiz? Quyidagilardan tanlang 👇", 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )
    await state.set_state(TaskStates.waiting_for_target_user)


@tasks_router.callback_query(TaskStates.waiting_for_target_user, F.data.startswith("assignuser_"))
async def process_target_user_callback(call: types.CallbackQuery, state: FSMContext):
    target_user_id = call.data.split("_")[1]
    employee_name = USERS_ROLES.get(target_user_id, {}).get("name", "Noma'lum xodim")
    
    await state.update_data(assigned_to_id=int(target_user_id), assigned_to_name=employee_name)
    
    await call.message.delete()
    await call.message.answer(
        text="Iltimos, vazifa nomini kiriting:",
        reply_markup=get_back_home_keyboard()
    )
    await state.set_state(TaskStates.waiting_for_name)
    await call.answer()


@tasks_router.message(TaskStates.waiting_for_name)
async def get_task_name_handler(message: types.Message, state: FSMContext):
    if await handle_back_or_home_global(message, state, TaskStates.waiting_for_target_user):
        return
    
    await state.update_data(task_name=message.text.strip())
    user_data = await state.get_data()
    
    if user_data.get("task_type") == "Kunlik (Bir martalik)":
        await message.answer(
            text="Izoh (bu yerda admin tomonidan yozilgan taskning izohi):",
            reply_markup=get_back_home_keyboard()
        )
        await state.set_state(TaskStates.waiting_for_description)
    else:
        await message.answer(
            text="Vazifa haftaning qaysi kunlari foydalanuvchiga koʻrinsin?",
            reply_markup=days_keyboard
        )
        await state.set_state(TaskStates.waiting_for_days)


@tasks_router.message(TaskStates.waiting_for_description)
async def get_task_description_handler(message: types.Message, state: FSMContext):
    if await handle_back_or_home_global(message, state, TaskStates.waiting_for_name):
        return
    
    await state.update_data(task_description=message.text.strip())
    await message.answer(
        text="Ushbu vazifani yakunlash uchun qanday turdagi isbot talab etiladi?",
        reply_markup=proof_type_keyboard
    )
    await state.set_state(TaskStates.waiting_for_proof_type)


# ================= KUNLARNI TANLASH (DOIMIY) =================
@tasks_router.message(TaskStates.waiting_for_days, F.text.in_(["Toq kunlar", "Juft kunlar", "Haftada 6 kun"]))
async def get_task_days_handler(message: types.Message, state: FSMContext):
    if await handle_back_or_home_global(message, state, TaskStates.waiting_for_name):
        return
    
    day_mapping = {"Toq kunlar": "ODD", "Juft kunlar": "EVEN", "Haftada 6 kun": "6 days a week"}
    await state.update_data(task_days=day_mapping.get(message.text))
    await message.answer(
        text="Vazifa kuniga necha marta koʻrinishi kerak?",
        reply_markup=frequency_keyboard
    )
    await state.set_state(TaskStates.waiting_for_frequency)


@tasks_router.message(TaskStates.waiting_for_days, F.text == "Boshqa kunlar")
async def other_days_handler(message: types.Message, state: FSMContext):
    if await handle_back_or_home_global(message, state, TaskStates.waiting_for_name):
        return
    
    await state.update_data(selected_days=[])
    await message.answer(
        text="Iltimos, kerakli hafta kunlarini bittalab tanlang:",
        reply_markup=get_inline_days_keyboard([])
    )


@tasks_router.callback_query(TaskStates.waiting_for_days, F.data.startswith("day_"))
async def toggle_day_callback(call: types.CallbackQuery, state: FSMContext):
    day_code = call.data.split("_")[1]
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", [])
    if day_code in selected_days:
        selected_days.remove(day_code)
    else:
        selected_days.append(day_code)
    await state.update_data(selected_days=selected_days)
    await call.message.edit_reply_markup(reply_markup=get_inline_days_keyboard(selected_days))
    await call.answer()


@tasks_router.callback_query(TaskStates.waiting_for_days, F.data == "days_done")
async def days_done_callback(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", [])
    if not selected_days:
        await call.answer(text="Iltimos, kamida bitta kunni tanlang!", show_alert=True)
        return
    await state.update_data(task_days=", ".join(selected_days))
    await call.message.delete()
    await call.message.answer(
        text="Vazifa kuniga necha marta koʻrinishi kerak?",
        reply_markup=frequency_keyboard
    )
    await state.set_state(TaskStates.waiting_for_frequency)
    await call.answer()


# ================= KUNIGA 1 MARTA =================
@tasks_router.message(TaskStates.waiting_for_frequency, F.text == "Kuniga 1 marta")
async def once_frequency_handler(message: types.Message, state: FSMContext):
    if await handle_back_or_home_global(message, state, TaskStates.waiting_for_days):
        return
    
    await state.update_data(task_frequency="Once")
    await message.answer(
        text="Vazifa xodimga qaysi vaqtda yuborilsin?\n\n<b>Format shabloni:</b> <code>11:33</code> koʻrinishida kiriting.", 
        parse_mode="HTML", 
        reply_markup=get_back_home_keyboard()
    )
    await state.set_state(TaskStates.waiting_for_once_time)


@tasks_router.message(TaskStates.waiting_for_once_time)
async def get_once_time_handler(message: types.Message, state: FSMContext):
    if await handle_back_or_home_global(message, state, TaskStates.waiting_for_frequency):
        return
    
    await state.update_data(task_times=message.text.strip())
    await message.answer(
        text="Ushbu vazifani yakunlash uchun qanday turdagi isbot talab etiladi?",
        reply_markup=proof_type_keyboard
    )
    await state.set_state(TaskStates.waiting_for_proof_type)


# ================= BIR NECHA MARTA =================
@tasks_router.message(TaskStates.waiting_for_frequency, F.text == "Bir necha marta")
async def multiple_frequency_handler(message: types.Message, state: FSMContext):
    if await handle_back_or_home_global(message, state, TaskStates.waiting_for_days):
        return
    
    await state.update_data(task_frequency="Multiple times")
    await message.answer(
        text="Vazifa xodimga qaysi vaqtlarda yuborilsin?\n\n<b>Format shabloni:</b> Vaqtlarni vergul bilan ajratib yozing.\nMasalan: <code>08:00, 14:00, 18:00</code>", 
        parse_mode="HTML", 
        reply_markup=get_back_home_keyboard()
    )
    await state.set_state(TaskStates.waiting_for_multiple_times)


@tasks_router.message(TaskStates.waiting_for_multiple_times)
async def get_multiple_times_handler(message: types.Message, state: FSMContext):
    if await handle_back_or_home_global(message, state, TaskStates.waiting_for_frequency):
        return
    
    await state.update_data(task_times=message.text.strip())
    await message.answer(
        text="Ushbu vazifani yakunlash uchun qanday turdagi isbot talab etiladi?",
        reply_markup=proof_type_keyboard
    )
    await state.set_state(TaskStates.waiting_for_proof_type)


# ================= ISBOT TURINI QABUL QILISH (TEXT + MEDIA) =================
@tasks_router.message(TaskStates.waiting_for_proof_type, F.text.in_(["Dumaloq video", "Rasm yuborish", "✍️ Matn yuborish"]))
async def finalize_task_creation_handler(message: types.Message, state: FSMContext):
    proof_mapping = {
        "Dumaloq video": "Video message", 
        "Rasm yuborish": "Photo",
        "✍️ Matn yuborish": "Text"
    }
    
    tashkent_tz = timezone(timedelta(hours=5))
    
    user_data = await state.get_data()
    task_id = len(TASKS_DATABASE) + 1
    
    is_daily = user_data.get("task_type") == "Kunlik (Bir martalik)"
    raw_times = user_data.get("task_times", "")
    times_list = [t.strip() for t in raw_times.split(",") if t.strip()] if not is_daily else []
    
    new_task = {
        "id": task_id,
        "task_type": user_data.get("task_type"),
        "task_name": user_data.get("task_name"),
        "task_description": user_data.get("task_description", "Mavjud emas"),
        "task_days": user_data.get("task_days", "Kunlik vazifa"), 
        "task_frequency": user_data.get("task_frequency", "Bir martalik"),
        "task_times": times_list,
        "proof_type": proof_mapping.get(message.text),
        "assigned_to_id": user_data.get("assigned_to_id"),
        "assigned_to_name": user_data.get("assigned_to_name"),
        "sent_today_times": [],
        "status": "pending",
        "completed_at": None,
        "completed_by": None,
        "created_at": datetime.now(tashkent_tz).isoformat()
    }
    
    TASKS_DATABASE.append(new_task)
    save_tasks(TASKS_DATABASE)
    
    report_text = (
        f"🎉 <b>Yangi vazifa muvaffaqiyatli yaratildi!</b>\n\n"
        f"📋 <b>Turi:</b> {new_task['task_type']}\n"
        f"📌 <b>Nomi:</b> {new_task['task_name']}\n"
    )
    if is_daily:
        report_text += f"📝 <b>Izoh:</b> {new_task['task_description']}\n"
    else:
        report_text += (
            f"📅 <b>Amal qilish kunlari:</b> {new_task['task_days']}\n"
            f"🔢 <b>Takrorlanish chastotasi:</b> {new_task['task_frequency']}\n"
            f"⏰ <b>Belgilangan vaqt(lar)i:</b> {', '.join(new_task['task_times'])}\n"
        )
    report_text += (
        f"📸 <b>Talab etiladigan isbot:</b> {message.text}\n"
        f"👤 <b>Masʻul xodim:</b> {new_task['assigned_to_name']}\n"
        f"📊 <b>Holat:</b> ⏳ Kutilmoqda"
    )
    
    await message.answer(text=report_text, parse_mode="HTML")

    role = USERS_ROLES[str(message.from_user.id)]["role"]
    await message.answer(text="Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
    
    try:
        if is_daily:
            employee_text = (
                f"🔔 <b>Sizga yangi kunlik vazifa yuklatildi!</b>\n\n"
                f"📌 <b>Vazifa nomi:</b> {new_task['task_name']}\n"
                f"📝 <b>Izoh (Admin eslatmasi):</b> {new_task['task_description']}\n\n"
                f"Vazifani bajarib, quyidagi tugma orqali hisobot (isbot) yuboring 👇"
            )
            await message.bot.send_message(
                chat_id=new_task["assigned_to_id"],
                text=employee_text,
                parse_mode="HTML",
                reply_markup=get_task_complete_keyboard(new_task["id"])
            )
        else:
            await message.bot.send_message(
                chat_id=new_task["assigned_to_id"],
                text=f"🔔 <b>Sizga yangi muntazam vazifa yuklatildi!</b>\n\n"
                     f"📌 <b>Vazifa nomi:</b> {new_task['task_name']}\n"
                     f"⏰ <b>Belgilangan vaqt(lar)i:</b> {', '.join(new_task['task_times'])}",
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Xodimga bildirishnoma yuborishda xatolik: {e}")
        
    await state.clear()


# ================= VAZIFALAR RO'YXATI (2 TUGMA) =================
@tasks_router.message(F.text == "📋 Vazifalar roʻyxati")
async def tasks_simple_menu_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    await state.set_state(TaskStates.waiting_for_tasks_simple_choice)
    await message.answer(
        text="📋 <b>Vazifalar roʻyxati</b>\n\n"
             "Qaysi kun uchun vazifalarni koʻrmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_tasks_simple_keyboard()
    )


# ================= BUGUNGI VAZIFALAR (TUZATILGAN) =================
@tasks_router.message(TaskStates.waiting_for_tasks_simple_choice, F.text == "📅 Bugun")
async def show_today_all_tasks(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    # Back/Home tekshiruvi
    if await handle_back_or_home_global(message, state, None):
        return
    
    tashkent_tz = timezone(timedelta(hours=5))
    now = datetime.now(tashkent_tz)
    today = now.strftime("%Y-%m-%d")
    current_hour = now.hour
    
    TASKS_DATABASE = load_tasks()
    
    # Barcha vazifalarni yig'ish (kechasi faqat doimiy, kunduzi hammasi)
    show_only_recurring = current_hour >= 0 and current_hour < 6
    
    all_tasks = []
    for task in TASKS_DATABASE:
        task_type = task.get("task_type")
        
        if task_type == "Muntazam (Doimiy)":
            all_tasks.append(task)
        elif task_type == "Kunlik (Bir martalik)":
            if not show_only_recurring:
                all_tasks.append(task)
    
    if not all_tasks:
        if show_only_recurring:
            await message.answer(
                text=f"📭 Hozir (kechasi {current_hour}:00) faqat doimiy vazifalar ko'rinadi.\n\n"
                     "Doimiy vazifalar mavjud emas.",
                reply_markup=get_tasks_simple_keyboard()
            )
        else:
            await message.answer(
                text=f"📭 Bugun ({today}) uchun vazifalar topilmadi.",
                reply_markup=get_tasks_simple_keyboard()
            )
        return
    
    response_text = f"📅 <b>{today} kungi vazifalar:</b>\n\n"
    for idx, task in enumerate(all_tasks, 1):
        if task.get("status") == "completed":
            completed_by = USERS_ROLES.get(str(task.get("completed_by")), {}).get("name", "Noma'lum")
            status_text = f"✅ Holat: Bajarildi (👤 {completed_by})"
        else:
            status_text = "⌛️ Holat: Bajarilmadi"
        
        if task.get("task_type") == "Kunlik (Bir martalik)":
            response_text += (
                f"{idx}. <b>[KUNLIK] {task['task_name']}</b>\n"
                f"   👤 Masʻul: {task['assigned_to_name']}\n"
                f"   📝 Izoh: {task['task_description']}\n"
                f"   📸 Isbot: {task['proof_type']}\n"
                f"   {status_text}\n\n"
            )
        else:
            response_text += (
                f"{idx}. <b>[DOIMIY] {task['task_name']}</b>\n"
                f"   👤 Masʻul: {task['assigned_to_name']}\n"
                f"   ⏰ Vaqti: {', '.join(task['task_times'])}\n"
                f"   📅 Kunlar: {task['task_days']}\n"
                f"   📸 Isbot: {task['proof_type']}\n"
                f"   {status_text}\n\n"
            )
    
    await message.answer(text=response_text, parse_mode="HTML", reply_markup=get_tasks_simple_keyboard())


# ================= SANA TANLASH =================
@tasks_router.message(TaskStates.waiting_for_tasks_simple_choice, F.text == "📆 Sana")
async def ask_for_custom_date_tasks(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    # Back/Home tekshiruvi
    if await handle_back_or_home_global(message, state, None):
        return
    
    await state.set_state(TaskStates.waiting_for_custom_date)
    await message.answer(
        text="📅 <b>Sanani tanlang (oxirgi 60 kun):</b>",
        parse_mode="HTML",
        reply_markup=get_custom_date_keyboard_simple()
    )


@tasks_router.message(TaskStates.waiting_for_custom_date)
async def show_tasks_by_selected_date(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    # Back/Home tekshiruvi
    if await handle_back_or_home_global(message, state, TaskStates.waiting_for_tasks_simple_choice):
        return
    
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer(
            text="❌ <b>Notoʻgʻri format!</b> Iltimos, sanani YYYY-MM-DD formatida kiriting.\n\n"
                 "Masalan: <code>2026-05-23</code>",
            parse_mode="HTML",
            reply_markup=get_custom_date_keyboard_simple()
        )
        return
    
    TASKS_DATABASE = load_tasks()
    
    all_tasks = []
    for task in TASKS_DATABASE:
        task_type = task.get("task_type")
        
        if task_type == "Muntazam (Doimiy)":
            all_tasks.append(task)
        elif task_type == "Kunlik (Bir martalik)":
            created_at = task.get("created_at", "")
            if created_at:
                created_date = created_at.split("T")[0]
                if created_date == date_text:
                    all_tasks.append(task)
    
    if not all_tasks:
        await message.answer(
            text=f"📭 {date_text} sanada vazifalar topilmadi.",
            reply_markup=get_custom_date_keyboard_simple()
        )
        return
    
    response_text = f"📅 <b>{date_text} kungi vazifalar:</b>\n\n"
    for idx, task in enumerate(all_tasks, 1):
        if task.get("status") == "completed":
            completed_by = USERS_ROLES.get(str(task.get("completed_by")), {}).get("name", "Noma'lum")
            status_text = f"✅ Holat: Bajarildi (👤 {completed_by})"
        else:
            status_text = "⌛️ Holat: Bajarilmadi"
        
        if task.get("task_type") == "Kunlik (Bir martalik)":
            response_text += (
                f"{idx}. <b>[KUNLIK] {task['task_name']}</b>\n"
                f"   👤 Masʻul: {task['assigned_to_name']}\n"
                f"   📝 Izoh: {task['task_description']}\n"
                f"   📸 Isbot: {task['proof_type']}\n"
                f"   {status_text}\n\n"
            )
        else:
            response_text += (
                f"{idx}. <b>[DOIMIY] {task['task_name']}</b>\n"
                f"   👤 Masʻul: {task['assigned_to_name']}\n"
                f"   ⏰ Vaqti: {', '.join(task['task_times'])}\n"
                f"   📅 Kunlar: {task['task_days']}\n"
                f"   📸 Isbot: {task['proof_type']}\n"
                f"   {status_text}\n\n"
            )
    
    await message.answer(text=response_text, parse_mode="HTML", reply_markup=get_custom_date_keyboard_simple())


# ================= VAZIFA O'CHIRISH =================
@tasks_router.message(F.text == "🗑 Vazifani oʻchirish")
async def remove_task_menu_handler(message: types.Message):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    TASKS_DATABASE = load_tasks()
    pending_tasks = [t for t in TASKS_DATABASE if t.get("status") != "completed"]
    
    if not pending_tasks:
        await message.answer(text="📭 Hozircha o'chiriladigan faol vazifalar mavjud emas (barcha vazifalar bajarilgan).")
        return
    
    await message.answer(
        text="🗑 <b>Oʻchirmoqchi boʻlgan vazifangizni tanlang:</b>\n<i>(Tugma bosilishi bilan vazifa bazadan butunlay oʻchadi!)</i>\n\n"
             "⚠️ <b>Diqqat:</b> Bajarilgan vazifalar o'chirilmaydi!",
        parse_mode="HTML",
        reply_markup=get_remove_tasks_keyboard(pending_tasks)
    )
