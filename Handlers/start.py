from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey  # StorageKey import qilindi
import config  
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

try:
    ADMIN_ID = int(config.ADMIN_ID)
except ValueError:
    ADMIN_ID = 6500594896  

# Vaqtincha xotira bazasi (Rol va Ismni saqlaydi)
USERS_ROLES = {
    ADMIN_ID: {"role": "Admin", "name": "Asosiy Admin"}
}

@start_router.message(CommandStart())
async def command_start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # 1. Agar foydalanuvchi rad etilgan bo'lsa
    user_info = USERS_ROLES.get(user_id)
    if isinstance(user_info, dict) and user_info.get("role") == "rejected":
        await message.answer("Assalomu alaykum. Siz botdan foydalana olmaysiz, so'rovingiz rad etilgan.")
        return

    # 2. Agar foydalanuvchi mutlaqo yangi (begona) bo'lsa
    if user_id not in USERS_ROLES:
        await message.answer(
            text="Hello, welcome to Edu_Control. Please wait until the bot administrator approves your request. Thank you!\n"
                 "Assalomu alaykum, Edu_Control’ga xush kelibsiz. Admin tasdiqlaguncha kuting. Rahmat!"
        )
        
        full_name = message.from_user.full_name
        
        if message.from_user.username:
            raw_username = message.from_user.username
            user_profile_link = f"https://t.me/{raw_username}"
            username_text = f"@{raw_username} (<a href='{user_profile_link}'>Profilga o'tish</a>)"
        else:
            username_text = f"Mavjud emas (<a href='tg://user?id={user_id}'>Profilga o'tish</a>)"
        
        admin_text = (
            f"🔔 <b>Yangi foydalanuvchi ruxsat so'ramoqda!</b>\n\n"
            f"👤 <b>Ism Familiya:</b> {full_name}\n"
            f"🆔 <b>ID Raqami:</b> <code>{user_id}</code>\n"
            f"🌐 <b>Username:</b> {username_text}\n\n"
            f"Iltimos, ushbu foydalanuvchiga unvon (role) bering yoki rad eting 👇"
        )
        
        try:
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_text,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=get_admin_approval_keyboard(user_id)
            )
        except Exception as e:
            print(f"❌ Adminga xabar yuborishda muammo: {e}")
        return

    # 3. Agar foydalanuvchiga rol berilganu, lekin hali ismini kiritmagan bo'lsa
    if isinstance(user_info, dict) and not user_info.get("name"):
        await message.answer("Iltimos, ism va familiyangizni kiriting!")
        await state.set_state(TaskStates.waiting_for_user_name)
        return

    # 4. Agar ro'yxatdan to'liq o'tgan bo'lsa
    saved_name = user_info.get("name", message.from_user.full_name)
    await message.answer(
        text=f"Salom, {saved_name}! Botimizga xush kelibsiz.\n"
             f"Quyidagi tugma orqali vazifalarni ko'rishingiz mumkin 👇",
        reply_markup=main_menu_keyboard
    )


# ================= CALLBACK HANDLERS (ADMIN APPROVAL) =================

@start_router.callback_query(F.data.startswith("approve_"))
async def admin_approve_callback(call: types.CallbackQuery):
    try:
        data_parts = call.data.split("_")
        role = data_parts[1]
        target_user_id = int(data_parts[2])
        
        # Rolni saqlaymiz, ism (name) hozircha None
        USERS_ROLES[target_user_id] = {"role": role, "name": None}
        
        # Admin xabarini yangilaymiz
        await call.message.edit_text(
            text=f"{call.message.text}\n\n✅ <b>Tasdiqlandi!</b> Foydalanuvchiga <b>{role}</b> unvoni berildi.",
            parse_mode="HTML"
        )
        
        # FOYDALANUVCHINING HOLATINI (STATE) 100% TO'G'RI O'ZGARTIRISH (YANGI METOD):
        try:
            # Router o'z ichiga olgan asosiy storagedan foydalanamiz
            if start_router.storage:
                user_key = StorageKey(bot_id=call.bot.id, chat_id=target_user_id, user_id=target_user_id)
                user_state = FSMContext(storage=start_router.storage, key=user_key)
                await user_state.set_state(TaskStates.waiting_for_user_name)
                print(f"[OK] Foydalanuvchi {target_user_id} holati waiting_for_user_name ga o'tkazildi.")
            
            # Foydalanuvchiga xabar yuborish
            user_text = f"Sizga Admin tomonidan \"{role}\" unvoni berildi. Iltimos ism, familiyangizni kiriting!"
            await call.bot.send_message(
                chat_id=target_user_id,
                text=user_text,
                reply_markup=types.ReplyKeyboardRemove()  
            )
        except Exception as e:
            print(f"❌ Foydalanuvchiga holat berish yoki xabar yuborishda xato: {e}")
            
    except Exception as general_error:
        print(f"❌ Callback ishlashida umumiy xatolik: {general_error}")
        
    await call.answer()


@start_router.callback_query(F.data.startswith("reject_"))
async def admin_reject_callback(call: types.CallbackQuery):
    try:
        target_user_id = int(call.data.split("_")[1])
        USERS_ROLES[target_user_id] = {"role": "rejected", "name": None}
        
        await call.message.edit_text(
            text=f"{call.message.text}\n\n❌ <b>So'rov rad etildi!</b> Foydalanuvchi bloklandi.",
            parse_mode="HTML"
        )
        
        try:
            await call.bot.send_message(
                chat_id=target_user_id,
                text="Sizning botdan foydalanish so'rovingiz admin tomonidan rad etildi."
            )
        except Exception as e:
            print(f"❌ Foydalanuvchiga rad xabarini yuborishda xato: {e}")
            
    except Exception as general_error:
        print(f"❌ Reject callbackda xatolik: {general_error}")
        
    await call.answer()


# ================= FOYDALANUVCHI ISMINI QABUL QILISH =================

@start_router.message(TaskStates.waiting_for_user_name)
async def get_user_real_name_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    input_text = message.text.strip()
    
    # Ismdan birinchi so'zni ajratib olamiz ("Baxtiyorjon Mahmudov" -> "Baxtiyorjon")
    first_name = input_text.split()[0]
    
    # Bazada foydalanuvchi ma'lumotlarini yangilaymiz
    if user_id in USERS_ROLES and isinstance(USERS_ROLES[user_id], dict):
        USERS_ROLES[user_id]["name"] = input_text
    else:
        USERS_ROLES[user_id] = {"role": "User", "name": input_text}
        
    # Muvaffaqiyatli ro'yxatdan o'tganlik xabari va asosiy menyu
    await message.answer(
        text=f"{first_name} siz ro'yxatdan o'tdingiz. Endi esa bot dan bemalol foydalansangiz bo'ladi",
        reply_markup=main_menu_keyboard
    )
    await state.clear()


# ================= TASK LOGICASI =================

def check_user_access(user_id: int) -> bool:
    user_info = USERS_ROLES.get(user_id)
    if not user_info or not isinstance(user_info, dict):
        return False
    if user_info.get("role") in [None, "rejected"] or not user_info.get("name"):
        return False
    return True

@start_router.message(F.text == "Add Task")
async def add_task_handler(message: types.Message):
    if not check_user_access(message.from_user.id): 
        await message.answer("Siz hali ro'yxatdan o'tmagansiz yoki ruxsatingiz yo'q.")
        return
    await message.answer(text="Qanday turdagi task yaratmoqchisiz?", reply_markup=task_type_keyboard)

@start_router.message(F.text == "Continuously")
async def continuously_handler(message: types.Message, state: FSMContext):
    if not check_user_access(message.from_user.id): return
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
