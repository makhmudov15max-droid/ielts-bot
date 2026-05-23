from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, timezone
import asyncio
import logging

from Handlers.states import TaskStates
from Keyboards.main_menu import get_main_menu, get_proof_role_keyboard, get_proof_date_keyboard
from utils.access import check_user_access
from utils.users_json import load_users
from utils.proofs_json import get_proofs_by_user, get_proofs_by_role, get_proofs_by_date_range

proofs_router = Router()

# Global o'zgaruvchilar
USERS_ROLES = None
ADMIN_ID = None


def init_proofs_handler(users_roles, admin_id):
    global USERS_ROLES, ADMIN_ID
    USERS_ROLES = users_roles
    ADMIN_ID = admin_id


def get_proof_employee_keyboard(role_name, include_all=True):
    """Tanlangan role dagi xodimlar ro'yxati (inline)"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    employees = []
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == role_name and u_info.get("name"):
            employees.append((u_id, u_info["name"]))
    
    if not employees:
        return None
    
    keyboard = []
    
    if include_all and len(employees) >= 1:
        keyboard.append([InlineKeyboardButton(text="👥 Barcha xodimlar", callback_data=f"proof_all_{role_name}")])
    
    for u_id, name in employees:
        keyboard.append([InlineKeyboardButton(text=f"👤 {name}", callback_data=f"proof_user_{u_id}")])
    
    keyboard.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="proof_back_to_roles")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def format_proof_message(proof, index):
    icon = "📸" if proof["proof_type"] == "Photo" else "📹" if proof["proof_type"] == "Video message" else "✍️"
    
    content = ""
    if proof["proof_type"] == "Photo":
        content = "📸 Rasm"
    elif proof["proof_type"] == "Video message":
        content = "📹 Dumaloq video"
    else:
        content = f"✍️ Matn: {proof.get('text_content', '')[:100]}"
    
    return (
        f"{icon} <b>{index}. {proof['task_name']}</b>\n"
        f"👤 <b>Xodim:</b> {proof['user_name']}\n"
        f"📅 <b>Sana:</b> {proof['date']}\n"
        f"⏰ <b>Vaqt:</b> {proof['time']}\n"
        f"📝 <b>Izoh:</b> {proof['task_description'] if proof['task_description'] else 'Mavjud emas'}\n"
        f"🔍 <b>Isbot:</b> {content}\n"
    )


async def send_proofs(message: types.Message, proofs_list, title):
    if not proofs_list:
        await message.answer(
            text=f"📭 <b>{title}</b>\n\nHech qanday isbot topilmadi.",
            parse_mode="HTML"
        )
        return
    
    await message.answer(
        text=f"📸 <b>{title}</b>\n\n🔍 {len(proofs_list)} ta isbot topildi:\n{'-' * 30}",
        parse_mode="HTML"
    )
    
    for proof in proofs_list:
        try:
            if proof["proof_type"] == "Photo":
                await message.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=proof["file_id"],
                    caption=f"📸 {proof['task_name']}\n👤 {proof['user_name']}\n📅 {proof['date']} {proof['time']}"
                )
            elif proof["proof_type"] == "Video message":
                await message.bot.send_video_note(
                    chat_id=message.chat.id,
                    video_note=proof["file_id"]
                )
                await message.answer(
                    text=f"📹 {proof['task_name']}\n👤 {proof['user_name']}\n📅 {proof['date']} {proof['time']}"
                )
            else:
                await message.answer(
                    text=f"✍️ <b>{proof['task_name']}</b>\n"
                         f"👤 {proof['user_name']}\n"
                         f"📅 {proof['date']} {proof['time']}\n"
                         f"💬 <i>{proof.get('text_content', '')[:500]}</i>",
                    parse_mode="HTML"
                )
        except Exception as e:
            logging.error(f"Isbot yuborishda xatolik: {e}")
            await message.answer(f"❌ Isbot yuborishda xatolik: {proof['task_name']}")
        
        await asyncio.sleep(0.5)


def get_custom_date_keyboard():
    """60 kunlik sanalar ro'yxati (har bir qatorda 2 tadan)"""
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    tashkent_tz = timezone(timedelta(hours=5))
    now = datetime.now(tashkent_tz)
    
    date_buttons = []
    for i in range(60):
        d = now - timedelta(days=i)
        date_buttons.append(KeyboardButton(text=d.strftime("%Y-%m-%d")))
    
    keyboard = []
    row = []
    for btn in date_buttons:
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


@proofs_router.message(F.text == "📸 Isbotlar")
async def proofs_start_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    await state.set_state(TaskStates.waiting_for_proof_role)
    await message.answer(
        text="📸 <b>Isbotlar arxivi</b>\n\n"
             "Qaysi role dagi xodimlarning isbotlarini koʻrmoqchisiz?\n\n"
             "👇 Quyidagilardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=get_proof_role_keyboard()
    )


@proofs_router.message(TaskStates.waiting_for_proof_role)
async def proof_role_selected_handler(message: types.Message, state: FSMContext):
    role = message.text
    
    if role == "🏠 Bosh sahifa":
        await state.clear()
        role_user = USERS_ROLES[str(message.from_user.id)]["role"]
        await message.answer(
            text="Asosiy menyuga qaytdingiz.",
            reply_markup=get_main_menu(role_user)
        )
        return
    
    if role == "Barcha xodimlar":
        await state.update_data(selected_role="all", selected_user_id=None, selected_user_name=None, selected_role_name=None)
        await state.set_state(TaskStates.waiting_for_proof_date)
        await message.answer(
            text="📅 <b>Sanani tanlang:</b>\n\n"
                 "👇 Quyidagilardan birini tanlang:",
            parse_mode="HTML",
            reply_markup=get_proof_date_keyboard()
        )
        return
    
    valid_roles = ["Admin", "Kassir", "Sanitar", "Manager"]
    if role not in valid_roles:
        await message.answer("❌ Iltimos, tugmalardan birini tanlang!")
        return
    
    await state.update_data(selected_role=role, selected_role_name=role)
    
    employees = []
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == role and u_info.get("name"):
            employees.append(u_id)
    
    if not employees:
        await message.answer(
            text=f"⚠️ <b>{role}</b> role dagi hali tasdiqlangan va ismi kiritilgan xodim mavjud emas!",
            parse_mode="HTML"
        )
        return
    
    keyboard = get_proof_employee_keyboard(role, include_all=True)
    if keyboard:
        await state.set_state(TaskStates.waiting_for_proof_user)
        await message.answer(
            text=f"👥 <b>{role}</b> role dagi xodimlardan birini tanlang:\n\n"
                 f"👥 Barcha xodimlar - o‘sha role dagi barcha xodimlarning isbotlari",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            text=f"⚠️ <b>{role}</b> role dagi xodimlar ro'yxati topilmadi!",
            parse_mode="HTML"
        )


@proofs_router.callback_query(TaskStates.waiting_for_proof_user, F.data.startswith("proof_user_"))
async def proof_user_selected_handler(call: types.CallbackQuery, state: FSMContext):
    user_id = call.data.split("_")[2]
    user_info = USERS_ROLES.get(user_id, {})
    user_name = user_info.get("name", "Noma'lum")
    
    await state.update_data(selected_user_id=user_id, selected_user_name=user_name, selected_role=None, selected_role_name=None)
    await state.set_state(TaskStates.waiting_for_proof_date)
    
    await call.message.delete()
    await call.message.answer(
        text=f"👤 <b>{user_name}</b> tanlandi.\n\n"
             f"📅 <b>Sanani tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_proof_date_keyboard()
    )
    await call.answer()


@proofs_router.callback_query(TaskStates.waiting_for_proof_user, F.data.startswith("proof_all_"))
async def proof_all_in_role_selected_handler(call: types.CallbackQuery, state: FSMContext):
    role_name = call.data.split("_")[2]
    
    await state.update_data(selected_role=role_name, selected_user_id=None, selected_user_name=None, selected_role_name=role_name)
    await state.set_state(TaskStates.waiting_for_proof_date)
    
    await call.message.delete()
    await call.message.answer(
        text=f"👥 <b>{role_name}</b> role dagi barcha xodimlar tanlandi.\n\n"
             f"📅 <b>Sanani tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_proof_date_keyboard()
    )
    await call.answer()


@proofs_router.callback_query(F.data == "proof_back_to_roles")
async def proof_back_to_roles_callback(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_proof_role)
    await call.message.delete()
    await call.message.answer(
        text="📸 <b>Isbotlar arxivi</b>\n\n"
             "Qaysi role dagi xodimlarning isbotlarini koʻrmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_proof_role_keyboard()
    )
    await call.answer()


@proofs_router.message(TaskStates.waiting_for_proof_date)
async def proof_date_selected_handler(message: types.Message, state: FSMContext):
    date_choice = message.text
    tashkent_tz = timezone(timedelta(hours=5))
    now = datetime.now(tashkent_tz)
    
    start_date = None
    end_date = None
    date_text = ""
    
    if date_choice == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES[str(message.from_user.id)]["role"]
        await message.answer(
            text="Asosiy menyuga qaytdingiz.",
            reply_markup=get_main_menu(role)
        )
        return
    
    elif date_choice == "⬅️ Ortga":
        await state.set_state(TaskStates.waiting_for_proof_role)
        await message.answer(
            text="📸 <b>Isbotlar arxivi</b>\n\n"
                 "Qaysi role dagi xodimlarning isbotlarini koʻrmoqchisiz?",
            parse_mode="HTML",
            reply_markup=get_proof_role_keyboard()
        )
        return
    
    elif date_choice == "📅 Bugun":
        start_date = now.strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")
        date_text = "Bugungi isbotlar"
    
    elif date_choice == "📆 Kecha":
        yesterday = now - timedelta(days=1)
        start_date = yesterday.strftime("%Y-%m-%d")
        end_date = yesterday.strftime("%Y-%m-%d")
        date_text = "Kechagi isbotlar"
    
    elif date_choice == "📅 Shu oy":
        start_date = now.replace(day=1).strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")
        date_text = f"{now.strftime('%B')} oyidagi isbotlar"
    
    elif date_choice == "📆 O'tgan oy":
        first_day_current = now.replace(day=1)
        last_day_prev = first_day_current - timedelta(days=1)
        first_day_prev = last_day_prev.replace(day=1)
        start_date = first_day_prev.strftime("%Y-%m-%d")
        end_date = last_day_prev.strftime("%Y-%m-%d")
        date_text = f"{first_day_prev.strftime('%B')} oyidagi isbotlar"
    
    elif date_choice == "✍️ Boshqa sana":
        await message.answer(
            text="📅 <b>Sanani tanlang (oxirgi 60 kun):</b>",
            parse_mode="HTML",
            reply_markup=get_custom_date_keyboard()
        )
        return
    
    else:
        try:
            custom_date = datetime.strptime(date_choice.strip(), "%Y-%m-%d")
            start_date = custom_date.strftime("%Y-%m-%d")
            end_date = custom_date.strftime("%Y-%m-%d")
            date_text = f"{custom_date.strftime('%Y-%m-%d')} sanadagi isbotlar"
        except ValueError:
            await message.answer(
                text="❌ <b>Notoʻgʻri format!</b> Iltimos, sanani YYYY-MM-DD formatida kiriting.",
                parse_mode="HTML"
            )
            return
    
    user_data = await state.get_data()
    selected_role = user_data.get("selected_role")
    selected_user_id = user_data.get("selected_user_id")
    selected_user_name = user_data.get("selected_user_name")
    selected_role_name = user_data.get("selected_role_name")
    
    proofs = []
    
    if selected_user_id:
        proofs = get_proofs_by_user(selected_user_id, start_date, end_date)
        title = f"{selected_user_name} ning {date_text}"
    elif selected_role_name:
        proofs = get_proofs_by_role(selected_role_name, start_date, end_date)
        title = f"{selected_role_name} role dagi barcha xodimlarning {date_text}"
    elif selected_role == "all":
        proofs = get_proofs_by_date_range(start_date, end_date)
        title = f"Barcha xodimlarning {date_text}"
    else:
        proofs = get_proofs_by_role(selected_role, start_date, end_date)
        title = f"{selected_role} role dagi xodimlarning {date_text}"
    
    await state.clear()
    await send_proofs(message, proofs, title)
