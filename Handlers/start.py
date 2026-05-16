from aiogram import Router, types, F  # <--- F filtrini qo'shdik
from aiogram.filters import CommandStart
from Keyboards.main_menu import main_menu_keyboard, task_type_keyboard # <--- Yangi tugmani ham chaqirdik

start_router = Router()

@start_router.message(CommandStart())
async def command_start_handler(message: types.Message):
    await message.answer(
        text=f"Salom, {message.from_user.full_name}! Botimizga xush kelibsiz.\n"
             f"Quyidagi tugma orqali vazifalarni ko'rishingiz mumkin 👇",
        reply_markup=main_menu_keyboard
    )

# "Add Task" tugmasi bosilganda ishlaydigan yangi qism
@start_router.message(F.text == "Add Task")
async def add_task_handler(message: types.Message):
    await message.answer(
        text="Qanday turdagi task yaratmoqchisiz?",
        reply_markup=task_type_keyboard # Yangi Continuously va Daily tugmalarini ko'rsatamiz
    )
