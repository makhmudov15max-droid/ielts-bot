from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext # FSM bilan ishlash uchun
# get_inline_days_keyboard funksiyasini ham import qilib olamiz
from Keyboards.main_menu import main_menu_keyboard, task_type_keyboard, days_keyboard, frequency_keyboard, get_inline_days_keyboard
from Handlers.states import TaskStates # Holatlarimizni chaqiramiz

start_router = Router()

@start_router.message(CommandStart())
async def command_start_handler(message: types.Message):
    await message.answer(
        text=f"Salom, {message.from_user.full_name}! Botimizga xush kelibsiz.\n"
             f"Quyidagi tugma orqali vazifalarni ko'rishingiz mumkin 👇",
        reply_markup=main_menu_keyboard
    )

@start_router.message(F.text == "Add Task")
async def add_task_handler(message: types.Message):
    await message.answer(
        text="Qanday turdagi task yaratmoqchisiz?",
        reply_markup=task_type_keyboard
    )

# 1. "Continuously" bosilganda nomini so'rash va holatni o'zgartirish
@start_router.message(F.text == "Continuously")
async def continuously_handler(message: types.Message, state: FSMContext):
    await message.answer(
        text="Vazifa nomini kiriting!",
        reply_markup=types.ReplyKeyboardRemove() # Eski tugmalarni vaqtincha yopib turamiz
    )
    await state.set_state(TaskStates.waiting_for_name)

# 2. Foydalanuvchi nom kiritganida uni ushlab qolish
@start_router.message(TaskStates.waiting_for_name)
async def get_task_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await message.answer(
        text="Vazifa qaysi kunlari ko'rinsin?",
        reply_markup=days_keyboard
    )
    await state.set_state(TaskStates.waiting_for_days)

# 3. Kunlar tanlanganda (ODD, EVEN yoki 6 days a week) uni ushlab qolish va Chastotani so'rash
@start_router.message(TaskStates.waiting_for_days, F.text.in_(["ODD", "EVEN", "6 days a week"]))
async def get_task_days_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_days=message.text)
    await message.answer(
        text="How many times per day? (Once or multiple times?)",
        reply_markup=frequency_keyboard
    )
    await state.set_state(TaskStates.waiting_for_frequency)

# 4. "OTHER" tugmasi bosilganda Inline klaviaturani chiqarish
@start_router.message(TaskStates.waiting_for_days, F.text == "OTHER")
async def other_days_handler(message: types.Message, state: FSMContext):
    await state.update_data(selected_days=[])
    await message.answer(
        text="Hafta kunlarini tanlang:",
        reply_markup=get_inline_days_keyboard([])
    )

# 5. Inline kunlar bosilganda checkbox kabi ishlash logikasi
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

# 6. "Done ➡️" tugmasi bosilganda Chastotani so'rashga o'tish
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

# 7. "Once" tugmasi bosilganda bitta vaqtni qo'lda yozishni so'rash
@start_router.message(TaskStates.waiting_for_frequency, F.text == "Once")
async def once_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Once")
    await message.answer(
        text="What time should the task appear?\n\n*Shablon:* `09:00` yoki `11:30` ko'rinishida yozishingiz mumkin.",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskStates.waiting_for_once_time)

# 8. Foydalanuvchi kiritgan bitta vaqtni qabul qilish va yakunlash
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

# 9. "Multiple times" bosilganda bir nechta vaqtni vergul bilan yozishni so'rash
@start_router.message(TaskStates.waiting_for_frequency, F.text == "Multiple times")
async def multiple_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Multiple times")
    await message.answer(
        text="What times should the task appear?\n\n*Shablon:* Vaqtlarni vergul bilan ajratib yozing.\nMasalan: `09:00, 12:30, 15:00, 18:45`",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskStates.waiting_for_multiple_times)

# 10. Foydalanuvchi vergul bilan yozgan ko'p vaqtlarni qabul qilish va yakunlash
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
