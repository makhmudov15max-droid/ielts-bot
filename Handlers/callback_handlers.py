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
from utils.users_json import save_users
from utils.tasks_json import save_tasks

callback_router = Router()

# Global o'zgaruvchilar (start.py dan import qilinadi)
USERS_ROLES = None
TASKS_DATABASE = None
ADMIN_ID = None


def init_callback_handler(users_roles, tasks_database, admin_id):
    """Callback handler uchun global o'zgaruvchilarni o'rnatish"""
    global USERS_ROLES, TASKS_DATABASE, ADMIN_ID
    USERS_ROLES = users_roles
    TASKS_DATABASE = tasks_database
    ADMIN_ID = admin_id


# ================= ADMIN APPROVAL CALLBACKS =================

@callback_router.callback_query(F.data.startswith("approve_"))
async def admin_approve_callback(call: types.CallbackQuery, state: FSMContext):
    try:
        data_parts = call.data.split("_")
        role = data_parts[1]
        target_user_id = int(data_parts[2])
        
        USERS_ROLES[str(target_user_id)] = {
            "role": role,
            "name": None
        }
        save_users(USERS_ROLES)
        
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
            "name": None
        }
        save_users(USERS_ROLES)
        
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
    task = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    if not task:
        await call.answer(text="Kechirasiz, ushbu vazifa tizimdan topilmadi yoki oʻchirilgan!", show_alert=True)
        return
        
    await state.update_data(active_task_id=task_id, proof_required=task["proof_type"])
    
    if task["proof_type"] == "Photo":
        await call.message.answer(text="Ushbu vazifani tasdiqlash uchun iltimos, <b>Rasm (Photo)</b> yuboring!", parse_mode="HTML")
    else:
        await call.message.answer(text="Ushbu vazifani tasdiqlash uchun iltimos, <b>Dumaloq video (Video message)</b> yuboring!", parse_mode="HTML")
        
    await state.set_state(TaskStates.waiting_for_task_proof)
    await call.answer()


# ================= VAZIFA O'CHIRISH CALLBACKS =================

@callback_router.callback_query(F.data.startswith("removetask_"))
async def process_remove_task_callback(call: types.CallbackQuery):
    task_id = int(call.data.split("_")[1])
    global TASKS_DATABASE
    task_to_remove = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    
    if task_to_remove:
        TASKS_DATABASE = [t for t in TASKS_DATABASE if t["id"] != task_id]
        save_tasks(TASKS_DATABASE)
        await call.message.edit_text(
            text=f"🗑 <b>Vazifa muvaffaqiyatli oʻchirildi!</b>\n\n📌 <b>Nomi:</b> {task_to_remove['task_name']}\n👤 <b>Masʻul boʻlgan xodim:</b> {task_to_remove['assigned_to_name']}",
            parse_mode="HTML"
        )
    else:
        await call.answer(text="⚠️ Bu vazifa allaqachon oʻchirilgan yoki topilmadi!", show_alert=True)
    await call.answer()


@callback_router.callback_query(F.data == "remove_cancel")
async def cancel_remove_callback(call: types.CallbackQuery):
    await call.message.delete()
    role = USERS_ROLES[str(call.from_user.id)]["role"]
    await call.message.answer(text="O‘chirish jarayoni bekor qilindi.", reply_markup=get_main_menu(role))
    await call.answer()
