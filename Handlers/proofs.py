from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, timezone
import calendar
import logging

from Handlers.states import TaskStates
from Keyboards.main_menu import get_main_menu
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


# ================= YORDAMCHI FUNKSIYALAR =================

def get_proof_employee_keyboard(role_name):
    """Tanlangan role dagi xodimlar ro'yxati (inline)"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    employees = []
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == role_name and u_info.get("name"):
            employees.append((u_id, u_info["name"]))
    
    if not employees:
        return None
    
    keyboard = []
    for u_id, name in employees:
        keyboard.append([InlineKeyboardButton(text=f"👤 {name}", callback_data=f"proof_user_{u_id}")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="proof_back_to_roles")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def format_proof_message(proof, index):
    """Isbotni formatlash"""
    icon = "📸" if proof["proof_type"] == "Photo" else "📹"
    
    return (
        f"{icon} <b>{index}. {proof['task_name']}</b>\n"
        f"👤 <b>Xodim:</b> {proof['user_name']}\n"
        f"📅 <b>Sana:</b> {proof['date']}\n"
        f"⏰ <b>Vaqt:</b> {proof['time']}\n"
        f"📝 <b>Izoh:</b> {proof['task_description'] if proof['task_description'] else 'Mavjud emas'}\n"
    )


async def send_proofs(message: types.Message, proofs_list, title):
    """Isbotlarni yuborish"""
    if not proofs_list:
        await message.answer(
            text=f"📭 <b>{title}</b>\n\nHech qanday isbot topilmadi.",
            parse_mode="HTML"
        )
        return
    
    # Har bir xabarga maksimal 5 ta isbot
    batch_size = 5
    total = len(proofs_list)
    
    await message.answer(
        text=f"📸 <b>{title}</b>\n\n🔍 {total} ta isbot topildi:\n{'-' * 30}",
        parse_mode="HTML"
    )
    
    for i in range(0, total, batch_size):
        batch = proofs_list[i:i+batch_size]
        text = ""
        
        for idx, proof in enumerate(batch, start=i+1):
            text += format_proof_message(proof, idx) + "\n" + "─" * 30 + "\n\n"
        
        # Isbotlarni jo'natish (rasm/video bilan)
        for proof in batch:
            try:
                if proof["proof_type"] == "Photo":
                    await message.bot.send_photo(
                        chat_id=message.chat.id,
                        photo=proof["file_id"],
                        caption=f"📸 {proof['task_name']}\n👤 {proof['user_name']}\n📅 {proof['date']} {proof['time']}"
                    )
                else:
                    await message.bot.send_video_note(
                        chat_id=message.chat.id,
                        video_note=proof["file_id"]
                    )
                    await message.answer(
                        text=f"📹 {proof['task_name']}\n👤 {proof['user_name']}\n📅 {proof['date']} {proof['time']}"
                    )
            except Exception as e:
                logging.error(f"Isbot yuborishda xatolik: {e}")
                await message.answer(f"❌ Isbot yuborishda xatolik: {proof['task_name']}")
        
        await asyncio.sleep(0.5)


# ================= ASOSIY HANDLERLAR =================

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
        await state.update_data(selected_role="all", selected_user_id=None, selected_user_name=None)
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
    
    await state.update_data(selected_role=role)
    
    # Xodimlar bormi tekshirish
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
    
    keyboard = get_proof_employee_keyboard(role)
    if keyboard:
        await state.set_state(TaskStates.waiting_for_proof_user)
        await message.answer(
            text=f"👥 <b>{role}</b> role dagi xodimlardan birini tanlang:",
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
    
    await state.update_data(selected_user_id=user_id, selected_user_name=user_name, selected_role=None)
    await state.set_state(TaskStates.waiting_for_proof_date)
    
    await call.message.delete()
    await call.message.answer(
        text=f"👤 <b>{user_name}</b> tanlandi.\n\n"
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
            text="📅 <b>Sanani kiriting (YYYY-MM-DD formatida):</b>\n\n"
                 "Masalan: <code>2026-05-23</code>\n\n"
                 "Yoki 'Ortga' tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=get_proof_date_keyboard()
        )
        return
    
    else:
        # Custom sana kiritildi
        try:
            custom_date = datetime.strptime(date_choice.strip(), "%Y-%m-%d")
            start_date = custom_date.strftime("%Y-%m-%d")
            end_date = custom_date.strftime("%Y-%m-%d")
            date_text = f"{custom_date.strftime('%Y-%m-%d')} sanadagi isbotlar"
        except ValueError:
            await message.answer(
                text="❌ <b>Notoʻgʻri format!</b> Iltimos, sanani YYYY-MM-DD formatida kiriting.\n\n"
                     "Masalan: <code>2026-05-23</code>",
                parse_mode="HTML"
            )
            return
    
    # Isbotlarni olish
    user_data = await state.get_data()
    selected_role = user_data.get("selected_role")
    selected_user_id = user_data.get("selected_user_id")
    selected_user_name = user_data.get("selected_user_name")
    
    proofs = []
    
    if selected_user_id:
        # Muayyan xodim
        proofs = get_proofs_by_user(selected_user_id, start_date, end_date)
        title = f"{selected_user_name} ning {date_text}"
    
    elif selected_role == "all":
        # Barcha xodimlar
        proofs = get_proofs_by_date_range(start_date, end_date)
        title = f"Barcha xodimlarning {date_text}"
    
    else:
        # Role bo'yicha
        proofs = get_proofs_by_role(selected_role, start_date, end_date)
        title = f"{selected_role} role dagi xodimlarning {date_text}"
    
    await state.clear()
    await send_proofs(message, proofs, title)


# Import asyncio (funksiya ichida ishlatilgan)
import asyncio
from Keyboards.main_menu import get_proof_role_keyboard, get_proof_date_keyboard
