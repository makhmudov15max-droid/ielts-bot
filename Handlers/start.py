from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext # FSM bilan ishlash uchun
# Yangi frequency_keyboard tugmasini ham chaqirib oldik
from Keyboards.main_menu import main_menu_keyboard, task_type_keyboard, days_keyboard, frequency_keyboard
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
    # Botga hozir foydalanuvchi nom kiritish bosqichida ekanligini aytamiz
    await state.set_state(TaskStates.waiting_for_name)

# 2. Foydalanuvchi nom kiritganida uni ushlab qolish
@start_router.message(TaskStates.waiting_for_name)
async def get_task_name_handler(message: types.Message, state: FSMContext):
    # Kiritilgan nomni bot xotirasiga saqlaymiz (masalan: "Ishga keldim")
    await state.update_data(task_name=message.text)
    
    # Keyingi savolga o'tamiz va yangi tugmalarni ko'rsatamiz
    await message.answer(
        text="Vazifa qaysi kunlari ko'rinsin?",
        reply_markup=days_keyboard
    )
    # Holatni kunlarni kutish bosqichiga o'tkazamiz
    await state.set_state(TaskStates.waiting_for_days)

# 3. Kunlar tanlanganda (ODD, EVEN yoki 6 days a week) uni ushlab qolish va Chastotani so'rash
# F.text.in_([...]) filtri orqali ushbu 3 ta tugmadan biri bosilganini aniqlaymiz
@start_router.message(TaskStates.waiting_for_days, F.text.in_(["ODD", "EVEN", "6 days a week"]))
async def get_task_days_handler(message: types.Message, state: FSMContext):
    # Tanlangan kun turini bot xotirasiga saqlaymiz
    await state.update_data(task_days=message.text)
    
    # Keyingi bosqich savolini beramiz va "Once" hamda "Multiple times" tugmalarini chiqaramiz
    await message.answer(
        text="How many times per day? (Once or multiple times?)",
        reply_markup=frequency_keyboard
    )
    # Holatni kunlik chastotani kutish bosqichiga o'tkazamiz
    await state.set_state(TaskStates.waiting_for_frequency)
