from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
import config  # config faylini to'liqligicha import qilamiz
from Keyboards.main_menu import (
    main_menu_keyboard, 
    task_type_keyboard, 
    days_keyboard, 
    frequency_keyboard, 
    get_inline_days_keyboard,
    get_admin_approval_keyboard
)
from Handlers.states import TaskStates

start_router = Router()

# config ichidagi ADMIN_ID ni har qanday holatda raqam (int) ekanligiga ishonch hosil qilamiz
try:
    ADMIN_ID = int(config.ADMIN_ID)
except ValueError:
    ADMIN_ID = 6500594896  # Agar xatolik bo'lsa xavfsiz ID

# Vaqtincha xotira bazasi
USERS_ROLES = {
    ADMIN_ID: "Admin"  # Asosiy admin avtomatik tizimda bo'ladi
}

@start_router.message(CommandStart())
async def command_start_handler(message: types.Message):
    user_id = message.from_user.id
    
    # 1. Agar foydalanuvchi rad etilgan bo'lsa
    if USERS_ROLES.get(user_id) == "rejected":
        await message.answer("Assalomu alaykum. Siz botdan foydalana olmaysiz, so'rovingiz rad etilgan.")
        return

    # 2. Agar foydalanuvchi mutlaqo yangi (begona) bo'lsa
    if user_id not in USERS_ROLES:
        # Foydalanuvchiga kutish xabarini beramiz
        await message.answer(
            text="Hello, welcome to Edu_Control. Please wait until the bot administrator approves your request. Thank you!\n"
                 "Assalomu alaykum, Edu_Control’ga xush kelibsiz. Admin tasdiqlaguncha kuting. Rahmat!"
        )
        
        full_name = message.from_user.full_name
        
        # Username bor-yo'qligini aniqlab, havolali matn tayyorlaymiz
        if message.from_user.username:
            raw_username = message.from_user.username
            user_profile_link = f"https://t.me/{raw_username}"
            username_text = f"@{raw_username} ([Profilga o'tish]({user_profile_link}))"
        else:
            username_text = f"Mavjud emas ([Profilga o'tish](tg://user?id={user_id}))"
        
        # Markdown formatidagi chiroyli report xabari
        admin_text = (
            f"🔔 *Yangi foydalanuvchi ruxsat so'ramoqda!*\n\n"
            f"👤 *Ism Familiya:* {full_name}\n"
            f"🆔 *ID Raqami:* `{user_id}`\n"
            f"🌐 *Username:* {username_text}\n\n"
            f"Iltimos, ushbu foydalanuvchiga unvon (role) bering yoki rad eting 👇"
        )
        
        try:
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=get_admin_approval_keyboard(user_id)
            )
            print(f"[OK] Approval xabari havolalar bilan adminga yuborildi.")
        except Exception as e:
            print(f"❌ [XATOLIK] Markdown xatosi: {e}. Zaxira varianti ishga tushdi.")
            backup_username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 Yangi foydalanuvchi ruxsat so'ramoqda:\n\n"
                     f"👤 Ism: {full_name}\n"
                     f"🆔 ID: {user_id}\n"
                     f"🌐 Username: {backup_username}",
                reply_markup=get_admin_approval_keyboard(user_id)
            )
        return

    # 3. Agar foydalanuvchi tasdiqlangan bo'lsa
    await message.answer(
        text=f"Salom, {message.from_user.full_name}! Botimizga xush kelibsiz.\n"
             f"Quyidagi tugma orqali vazifalarni ko'rishingiz mumkin 👇",
        reply_markup=main_menu_keyboard
    )


# ================= CALLBACK HANDLERS (ADMIN APPROVAL) =================

@start_router.callback_query(F.data.startswith("approve_"))
async def admin_approve_callback(call: types.CallbackQuery):
    data_parts = call.data.split("_")
    role = data_parts[1]
    target_user_id = int(data_parts[2])
    
    USERS_ROLES[target_user_id] = role
    
    await call.message.edit_text(
        text=f"{call.message.text}\n\n✅ *Tasdiqlandi!* Foydalanuvchiga *{role}* unvoni berildi.",
        parse_mode="Markdown"
    )
    
    try:
        user_text = (
            f"You have been assigned the \"{role}\" role by the Admin. Welcome and good luck!\n"
            f"Sizga Admin tomonidan \"{role}\" unvoni berildi. Vaqtingizni maroqli o'tqazing, omad!"
        )
        await call.bot.send_message(
            chat_id=target_user_id,
            text=user_text,
            reply_markup=main_menu_keyboard
        )
    except Exception as e:
        print(f"Xabar yuborishda xatolik: {e}")
        
    await call.answer()


@start_router.callback_query(F.data.startswith("reject_"))
async def admin_reject_callback(call: types.CallbackQuery):
    target_user_id = int(call.data.split("_")[1])
    USERS_ROLES[target_user_id] = "rejected"
    
    await call.message.edit_text(
        text=f"{call.message.text}\n\n❌ *So'rov rad etildi!*",
        parse_mode="Markdown"
    )
    
    try:
        await call.bot.send_message(
            chat_id=target_user_id,
            text="Sizning botdan foydalanish so'rovingiz admin tomonidan rad etildi."
        )
    except Exception as e:
        print(f"Xabar yuborishda xatolik: {e}")
        
    await call.answer()


# ================= TASK LOGICASI =================

@start_router.message(F.text == "Add Task")
async def add_task_handler(message: types.Message):
    if USERS_ROLES.get(message.from_user.id) in [None, "rejected"]: return
    await message.answer(text="Qanday turdagi task yaratmoqchisiz?", reply_markup=task_type_keyboard)

@start_router.message(F.text == "Continuously")
async def continuously_handler(message: types.Message, state: FSMContext):
    if USERS_ROLES.get(message.from_user.id) in [None, "rejected"]: return
    await message.answer(text="Vazifa nomini kiriting!", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(TaskStates.waiting_for_name)

@start_router.message(TaskStates.waiting_for_name)
async def get_task_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await message.answer(text="Vazifa qaysi kunlari ko'rinsin?", reply_markup=days_keyboard)
    await state.set_state(TaskStates.waiting_for_days)

@start_router.message(TaskStates.waiting_for_days, F.text.in_(["ODD", "EVEN", "6 days a week"]))
async def get_task_days_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_days=message.text)
    await message.answer(text="How many times per day? (Once or multiple times?)", reply_markup=frequency_keyboard)
    await state.set_state(TaskStates.waiting_for_frequency)

@start_router.message(TaskStates.waiting_for_days, F.text == "OTHER")
async def other_days_handler(message: types.Message, state: FSMContext):
    await state.update_data(selected_days=[])
    await message.answer(text="Hafta kunlarini tanlang:", reply_markup=get_inline_days_keyboard([]))

@start_router.callback_query(TaskStates.waiting_for_days, F.data.startswith("day_"))
async def toggle_day_callback(call: types.CallbackQuery, state: FSMContext):
    day_code = call.data.split("_")[1]
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", [])
    
    if day_code in selected_days: selected_days.remove(day_code)
    else: selected_days.append(day_code)
        
    await state.update_data(selected_days=selected_days)
    await call.message.edit_reply_markup(reply_markup=get_inline_days_keyboard(selected_days))
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
    await call.message.answer(text="How many times per day? (Once or multiple times?)", reply_markup=frequency_keyboard)
    await state.set_state(TaskStates.waiting_for_frequency)
    await call.answer()

@start_router.message(TaskStates.waiting_for_frequency, F.text == "Once")
async def once_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Once")
    await message.answer(text="What time should the task appear?\n\n*Shablon:* `09:00` yoki `11:30` ko'rinishida yozing.", parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(TaskStates.waiting_for_once_time)

@start_router.message(TaskStates.waiting_for_once_time)
async def get_once_time_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_times=message.text)
    user_data = await state.get_data()
    await message.answer(text=f"🎉 *Vazifa yaratildi!*\n\n📌 *Nomi:* {user_data.get('task_name')}\n📅 *Kunlar:* {user_data.get('task_days')}\n🔢 *Chastotasi:* {user_data.get('task_frequency')}\n⏰ *Vaqti:* {user_data.get('task_times')}", parse_mode="Markdown", reply_markup=main_menu_keyboard)
    await state.clear()

@start_router.message(TaskStates.waiting_for_frequency, F.text == "Multiple times")
async def multiple_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Multiple times")
    await message.answer(text="What times should the task appear?\n\n*Shablon:* Vaqtlarni vergul bilan ajratib yozing.\nMasalan: `09:00, 12:30, 15:00`", parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(TaskStates.waiting_for_multiple_times)

@start_router.message(TaskStates.waiting_for_multiple_times)
async def get_multiple_times_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_times=message.text)
    user_data = await state.get_data()
    await message.answer(text=f"🎉 *Vazifa yaratildi!*\n\n📌 *Nomi:* {user_data.get('task_name')}\n📅 *Kunlar:* {user_data.get('task_days')}\n🔢 *Chastotasi:* {user_data.get('task_frequency')}\n⏰ *Vaqtlari:* {user_data.get('task_times')}", parse_mode="Markdown", reply_markup=main_menu_keyboard)
    await state.clear()
