from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, ADMIN_ID  # config ichidan token va admin ID ni olamiz
from Keyboards.main_menu import (
    main_menu_keyboard, 
    task_type_keyboard, 
    days_keyboard, 
    frequency_keyboard, 
    get_inline_days_keyboard,
    get_admin_approval_keyboard  # Yangi yaratilgan tugmalar funksiyasi
)
from Handlers.states import TaskStates

start_router = Router()

# Vaqtincha ma'lumotlar bazasi (In-memory storage)
# Kalit sifatida user_id, qiymat sifatida uning roli ("Admin", "Cashier", va h.k.) saqlanadi
# Agar foydalanuvchi "rejected" bo'lsa, botdan butunlay bloklanadi.
USERS_ROLES = {
    ADMIN_ID: "Admin"  # Asosiy admin avtomatik tarzda tizimga kiritiladi
}


@start_router.message(CommandStart())
async def command_start_handler(message: types.Message):
    user_id = message.from_user.id
    
    # 1. Agar foydalanuvchi rad etilgan (bloklangan) bo'lsa
    if USERS_ROLES.get(user_id) == "rejected":
        await message.answer("Assalomu alaykum. Siz botdan foydalana olmaysiz, so'rovingiz rad etilgan.")
        return

    # 2. Agar foydalanuvchiga hali hech qanday rol berilmagan bo'lsa (Yangi begona odam)
    if user_id not in USERS_ROLES:
        # Foydalanuvchining o'ziga kutish xabarini yuboramiz
        await message.answer(
            text="Hello, welcome to Edu_Control. Please wait until the bot administrator approves your request. Thank you!\n\n"
                 "Assalomu alaykum, Edu_Control’ga xush kelibsiz. Admin tasdiqlaguncha kuting. Rahmat!"
        )
        
        # Asosiy adminga foydalanuvchi ma'lumotlari bilan so'rov yuboramiz
        username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
        full_name = message.from_user.full_name
        
        admin_text = (
            f"🔔 *Yangi foydalanuvchi ruxsat so'ramoqda!*\n\n"
            f"👤 *Ism Familiya:* {full_name}\n"
            f"🆔 *ID Raqami:* `{user_id}`\n"
            f"🌐 *Username:* {username}\n\n"
            f"Iltimos, ushbu foydalanuvchiga unvon (role) bering yoki rad eting 👇"
        )
        
        # Adminga tugmalar bilan birga xabarni yuboramiz
        await message.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="Markdown",
            reply_markup=get_admin_approval_keyboard(user_id)
        )
        return

    # 3. Agar foydalanuvchi allaqachon tasdiqlangan bo'lsa, asosiy menyuni ko'rsatamiz
    await message.answer(
        text=f"Salom, {message.from_user.full_name}! Botimizga xush kelibsiz.\n"
             f"Quyidagi tugma orqali vazifalarni ko'rishingiz mumkin 👇",
        reply_markup=main_menu_keyboard
    )


# ================= ADMIN TASDIQLASH CALLBACK'LARI =================

# Admin biror rolni tanlaganda (approve_Role_ID)
@start_router.callback_query(F.data.startswith("approve_"))
async def admin_approve_callback(call: types.CallbackQuery):
    # Callback ma'lumotlarini ajratib olamiz (Masalan: approve_Cashier_123456)
    data_parts = call.data.split("_")
    role = data_parts[1]
    target_user_id = int(data_parts[2])
    
    # Foydalanuvchiga tanlangan rolni biriktiramiz
    USERS_ROLES[target_user_id] = role
    
    # Adminga tasdiqlanganligi haqida xabar beramiz va tugmalarni o'chiramiz
    await call.message.edit_text(
        text=f"{call.message.text}\n\n✅ *Tasdiqlandi!* Ushbu foydalanuvchiga *{role}* unvoni berildi.",
        parse_mode="Markdown"
    )
    
    # Foydalanuvchining o'ziga quvondiq xabarni yuboramiz
    try:
        user_text = (
            f"You have been assigned the \"{role}\" role by the Admin. Welcome and good luck!\n\n"
            f"Sizga Admin tomonidan \"{role}\" unvoni berildi. Vaqtingizni maroqli o'tqazing, omad!"
        )
        await call.bot.send_message(
            chat_id=target_user_id,
            text=user_text,
            reply_markup=main_menu_keyboard # Endi unga asosiy menyuni beramiz
        )
    except Exception as e:
        print(f"Foydalanuvchiga xabar yuborishda xatolik: {e}")
        
    await call.answer()


# Admin "Rad etish" tugmasini bosganda (reject_ID)
@start_router.callback_query(F.data.startswith("reject_"))
async def admin_reject_callback(call: types.CallbackQuery):
    target_user_id = int(call.data.split("_")[1])
    
    # Foydalanuvchini bazada rad etilgan holatga o'tkazamiz
    USERS_ROLES[target_user_id] = "rejected"
    
    # Adminga rad etilganini ko'rsatamiz
    await call.message.edit_text(
        text=f"{call.message.text}\n\n❌ *So'rov rad etildi!* Foydalanuvchi botga bloklandi.",
        parse_mode="Markdown"
    )
    
    # Foydalanuvchining o'ziga xabar yuboramiz
    try:
        await call.bot.send_message(
            chat_id=target_user_id,
            text="Sizning botdan foydalanish so'rovingiz admin tomonidan rad etildi."
        )
    except Exception as e:
        print(f"Foydalanuvchiga xabar yuborishda xatolik: {e}")
        
    await call.answer()


# ================= ESKI TASK YARATISH LOGIKALARI =================

# Begona odamlar boshqa tugmalarni bossa ham ishlamasligi uchun har bir handler tepasiga tekshiruv kerak bo'ladi, 
# lekin hozircha asosiylari quyidagicha qoladi:

@start_router.message(F.text == "Add Task")
async def add_task_handler(message: types.Message):
    # Faqat tasdiqlangan foydalanuvchilar ishlata olishi uchun oddiy tekshiruv
    if USERS_ROLES.get(message.from_user.id) in [None, "rejected"]:
        return
    await message.answer(
        text="Qanday turdagi task yaratmoqchisiz?",
        reply_markup=task_type_keyboard
    )

@start_router.message(F.text == "Continuously")
async def continuously_handler(message: types.Message, state: FSMContext):
    if USERS_ROLES.get(message.from_user.id) in [None, "rejected"]: return
    await message.answer(
        text="Vazifa nomini kiriting!",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskStates.waiting_for_name)

@start_router.message(TaskStates.waiting_for_name)
async def get_task_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await message.answer(
        text="Vazifa qaysi kunlari ko'rinsin?",
        reply_markup=days_keyboard
    )
    await state.set_state(TaskStates.waiting_for_days)

@start_router.message(TaskStates.waiting_for_days, F.text.in_(["ODD", "EVEN", "6 days a week"]))
async def get_task_days_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_days=message.text)
    await message.answer(
        text="How many times per day? (Once or multiple times?)",
        reply_markup=frequency_keyboard
    )
    await state.set_state(TaskStates.waiting_for_frequency)

@start_router.message(TaskStates.waiting_for_days, F.text == "OTHER")
async def other_days_handler(message: types.Message, state: FSMContext):
    await state.update_data(selected_days=[])
    await message.answer(
        text="Hafta kunlarini tanlang:",
        reply_markup=get_inline_days_keyboard([])
    )

@start_router.callback_query(TaskStates.waiting_for_days, F.data.startswith("day_"))
async def toggle_day_callback(call: types.CallbackQuery, state: FSMContext):
    day_code = call.data.split("_")[1]
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", [])
    
    if day_code in selected_days:
        selected_days.remove(day_code)
    else:
        selected_days.append(day_code)
        
    await state.update_data(selected_days=selected_days)
    await call.message.edit_reply_markup(
        reply_markup=get_inline_days_keyboard(selected_days)
    )
    await call.answer()

@start_router.callback_query(TaskStates.waiting_for_days, F.data == "days_done")
async def days_done_callback(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", [])
    
    if not selected_days:
        await call.answer(text="Iltimos, kamida bitta kun tanlang!", show_alert=True)
        return
        
    await state.update_data(task_days=", ".join(selected_days))
    await call.message.delete()
    await call.message.answer(
        text="How many times per day? (Once or multiple times?)",
        reply_markup=frequency_keyboard
    )
    await state.set_state(TaskStates.waiting_for_frequency)
    await call.answer()

@start_router.message(TaskStates.waiting_for_frequency, F.text == "Once")
async def once_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Once")
    await message.answer(
        text="What time should the task appear?\n\n*Shablon:* `09:00` yoki `11:30` ko'rinishida yozishingiz mumkin.",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskStates.waiting_for_once_time)

@start_router.message(TaskStates.waiting_for_once_time)
async def get_once_time_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_times=message.text)
    user_data = await state.get_data()
    
    await message.answer(
        text=f"🎉 *Vazifa muvaffaqiyatli yaratildi!*\n\n"
             f"📌 *Nomi:* {user_data.get('task_name')}\n"
             f"📅 *Kunlar:* {user_data.get('task_days')}\n"
             f"🔢 *Chastotasi:* {user_data.get('task_frequency')}\n"
             f"⏰ *Vaqti:* {user_data.get('task_times')}",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard
    )
    await state.clear()

@start_router.message(TaskStates.waiting_for_frequency, F.text == "Multiple times")
async def multiple_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Multiple times")
    await message.answer(
        text="What times should the task appear?\n\n*Shablon:* Vaqtlarni vergul bilan ajratib yozing.\nMasalan: `09:00, 12:30, 15:00, 18:45`",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskStates.waiting_for_multiple_times)

@start_router.message(TaskStates.waiting_for_multiple_times)
async def get_multiple_times_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_times=message.text)
    user_data = await state.get_data()
    
    await message.answer(
        text=f"🎉 *Vazifa muvaffaqiyatli yaratildi!*\n\n"
             f"📌 *Nomi:* {user_data.get('task_name')}\n"
             f"📅 *Kunlar:* {user_data.get('task_days')}\n"
             f"🔢 *Chastotasi:* {user_data.get('task_frequency')}\n"
             f"⏰ *Vaqtlari:* {user_data.get('task_times')}",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard
    )
    await state.clear()
