from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext # FSM bilan ishlash uchun
from Keyboards.main_menu import main_menu_keyboard, task_type_keyboard, days_keyboard
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
