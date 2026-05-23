from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, timezone
import re

from Handlers.states import TaskStates
from Keyboards.main_menu import (
    get_main_menu,
    get_back_home_keyboard,
    get_tasks_list_keyboard,
    get_completed_date_keyboard,
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


async def handle_back_or_home(message: types.Message, state: FSMContext, current_state: str):
    """Ortga yoki Bosh sahifa tugmalarini boshqarish"""
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES[str(message.from_user.id)]["role"]
        await message.answer(
            text="Asosiy menyuga qaytdingiz.",
            reply_markup=get_main_menu(role)
        )
        return True
    elif message.text == "⬅️ Ortga":
        if current_state:
            await state.set_state(current_state)
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
    
    if await handle_back_or_home(message, state, None):
        return
    
    await state.update_data(task_type=message.text)
    await message.answer(
        text="Ushbu vazifa qaysi boʻlim/unvon xodimiga tegishli?",
        reply_markup=assign_role_keyboard
    )
    await state.set_state(TaskStates.waiting_for_target_role)


@tasks_router.message(TaskStates.waiting_for_target_role, F.text.in_(["Admin", "Kassir", "Sanitar", "Manager"]))
async def get_target_role_handler(message: types.Message, state: FSMContext):
    if await handle_back_or_home(message, state, None):
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
async def get_task_name_handler
