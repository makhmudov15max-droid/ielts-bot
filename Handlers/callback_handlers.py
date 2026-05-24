from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, timezone

from Handlers.states import TaskStates
from Keyboards.main_menu import (
    get_main_menu,
    get_admin_approval_keyboard,
    get_task_complete_keyboard,
    get_remove_tasks_keyboard
)
from utils.access import is_admin
from utils.users_db import save_users, set_user_busy
from utils.tasks_db import save_tasks, load_tasks, update_task_status

callback_router = Router()

# ================= GLOBAL O'ZGARUVCHILAR =================
USERS_ROLES = None
TASKS_DATABASE = None
ADMIN_ID = None


# ================= INIT FUNKSIYASI =================
def init_callback_handler(users_roles, tasks_database, admin_id):
    """Callback handler uchun global o'zgaruvchilarni o'rnatish"""
    global USERS_ROLES, TASKS_DATABASE, ADMIN_ID
    USERS_ROLES = users_roles
    TASKS_DATABASE = tasks_database
    ADMIN_ID = admin_id


# ================= VAZIFA YARATISHNI BEKOR QILISH =================
@callback_router.callback_query(F.data == "cancel_task_creation")
async def cancel_task_creation_callback(call: types.CallbackQuery, state: FSMContext):
    """Vazifa yaratishni bekor qilish - xodim tanlash bosqichidan"""
    await state.clear()
    role = USERS_ROLES.get(str(call.from_user.id), {}).get("role", "Owner")
    await call.message.delete()
    await call.message.answer(
        text="❌ Vazifa yaratish bekor qilindi. Asosiy menyuga qaytdingiz.",
        reply_markup=get_main_menu(role)
    )
    await call.answer()


# ================= ADMIN APPROVAL CALLBACKS =================
@callback_router.callback_query(F.data.startswith("approve_"))
async def admin_approve_callback(call: types.CallbackQuery, state: FSMContext):
    try:
        data_parts = call.data.split("_")
        role = data_parts[1]
        target_user_id = int(data_parts[2])
        
        USERS_ROLES[str(target_user_id)] = {
            "role": role,
            "name": None,
            "active_task": None,
            "is_waiting_for_proof": False
        }
        await save_users(USERS_ROLES)
        
        await call.message.edit_text(
            text=f"{call.message.text}\n\n✅ <b>Tasdiqlandi!</b> Foydalanuvchiga <b>{role}</b> unvoni muvaffaqiyatli berildi.",
            parse_mode="HTML"
        )
        
        await state.set_state(TaskStates.waiting_for_user_name)
        
        user_text = f"Sizga administrator tomonidan \"{role}\" unvoni berildi. Iltimos, tizimda foydalanish uchun ism va familiyangizni kiriting:"
        await call.bot.send_message(
            chat_id=target_user_id,
            text=user_text,
            reply_markup=types.ReplyKeyboardRemove()  
        )
            
    except Exception as e:
        print(f"❌ Tasdiqlash jarayonida xatolik: {e}")
    await call.answer()


@callback_router.callback_query(F.data.startswith("reject_"))
async def admin_reject_callback(call: types.CallbackQuery):
    try:
        target_user_id = int(call.data.split("_")[1])
        USERS_ROLES[str(target_user_id)] = {
            "role": "rejected",
            "name": None,
            "active_task": None,
            "is_waiting_for_proof": False
        }
        await save_users(USERS_ROLES)
        
        await call.message.edit_text(
            text=f"{call.message.text}\n\n❌ <b>Soʻrov rad etildi!</b> Foydalanuvchi bloklandi.",
            parse_mode="HTML"
        )
        await call.bot.send_message(chat_id=target_user_id, text="Sizning botdan foydalanish soʻrovingiz administrator tomonidan rad etildi.")
    except Exception as e:
        print(f"❌ Rad etish jarayonida xatolik: {e}")
    await call.answer()


# ================= VAZIFA BAJARISH CALLBACKS =================
@callback_router.callback_query(F.data.startswith("completetask_"))
async def employee_complete_task_callback(call: types.CallbackQuery, state: FSMContext):
    task_id = int(call.data.split("_")[1])
    
    # Eng so'nggi ma'lumotlarni yuklash
    global TASKS_DATABASE
    TASKS_DATABASE = await load_tasks()
    
    task = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    if not task:
        await call.answer(text="Kechirasiz, ushbu vazifa tizimdan topilmadi yoki oʻchirilgan!", show_alert=True)
        return
    
    # Vazifa allaqachon bajarilganmi?
    if task.get("status") == "completed":
        await call.answer(text="⚠️ Bu vazifa allaqachon bajarilgan!", show_alert=True)
        return
    
    # Foydalanuvchini band qilish
    user_id = str(call.from_user.id)
    await set_user_busy(user_id, task_id)
    
    await state.update_data(active_task_id=task_id, proof_required=task["proof_type"])
    
    if task["proof_type"] == "Photo":
        await call.message.answer(
            text="📸 Ushbu vazifani tasdiqlash uchun iltimos, <b>Rasm (Photo)</b> yuboring!\n\n"
                 "⚠️ Isbot yubormaguningizcha boshqa amallarni bajara olmaysiz.\n"
                 "Bekor qilish uchun /cancel buyrug'ini yuboring.",
            parse_mode="HTML"
        )
    elif task["proof_type"] == "Video message":
        await call.message.answer(
            text="📹 Ushbu vazifani tasdiqlash uchun iltimos, <b>Dumaloq video (Video message)</b> yuboring!\n\n"
                 "⚠️ Isbot yubormaguningizcha boshqa amallarni bajara olmaysiz.\n"
                 "Bekor qilish uchun /cancel buyrug'ini yuboring.",
            parse_mode="HTML"
        )
    elif task["proof_type"] == "Text":
        await call.message.answer(
            text="✍️ Ushbu vazifani tasdiqlash uchun iltimos, <b>Matn (Text)</b> yuboring!\n\n"
                 "⚠️ Isbot yubormaguningizcha boshqa amallarni bajara olmaysiz.\n"
                 "Bekor qilish uchun /cancel buyrug'ini yuboring.",
            parse_mode="HTML"
        )
    else:
        await call.message.answer(
            text="⚠️ Iltimos, isbot yuboring!\n\n"
                 "Bekor qilish uchun /cancel buyrug'ini yuboring.",
            parse_mode="HTML"
        )
        
    await state.set_state(TaskStates.waiting_for_task_proof)
    await call.answer()


# ================= VAZIFA O'CHIRISH CALLBACKS =================
@callback_router.callback_query(F.data.startswith("removetask_"))
async def process_remove_task_callback(call: types.CallbackQuery):
    task_id = int(call.data.split("_")[1])
    global TASKS_DATABASE
    
    # Eng so'nggi ma'lumotlarni yuklash
    TASKS_DATABASE = await load_tasks()
    
    task_to_remove = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    
    if task_to_remove:
        # Faqat pending (bajarilmagan) vazifalarni o'chirish
        if task_to_remove.get("status") == "completed":
            await call.answer(text="⚠️ Bajarilgan vazifani o'chirib bo'lmaydi!", show_alert=True)
            return
        
        TASKS_DATABASE = [t for t in TASKS_DATABASE if t["id"] != task_id]
        await save_tasks(TASKS_DATABASE)
        
        await call.message.edit_text(
            text=f"🗑 <b>Vazifa muvaffaqiyatli oʻchirildi!</b>\n\n"
                 f"📌 <b>Nomi:</b> {task_to_remove['task_name']}\n"
                 f"👤 <b>Masʻul boʻlgan xodim:</b> {task_to_remove['assigned_to_name']}",
            parse_mode="HTML"
        )
        
        await call.message.answer(
            text="✅ Vazifa bazadan butunlay o'chirildi.\n\n"
                 "📋 Yangilangan ro'yxatni ko'rish uchun '📋 Vazifalar roʻyxati' tugmasini bosing.",
            parse_mode="HTML"
        )
    else:
        await call.answer(text="⚠️ Bu vazifa allaqachon oʻchirilgan yoki topilmadi!", show_alert=True)
    await call.answer()


@callback_router.callback_query(F.data == "remove_cancel")
async def cancel_remove_callback(call: types.CallbackQuery):
    await call.message.delete()
    role = USERS_ROLES[str(call.from_user.id)]["role"]
    await call.message.answer(
        text="O‘chirish jarayoni bekor qilindi.",
        reply_markup=get_main_menu(role)
    )
    await call.answer()
