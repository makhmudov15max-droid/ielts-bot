from aiogram import Router, types
from aiogram.filters import CommandStart
# Boya yaratgan tugmamizni bu yerga chaqirib (import qilib) olamiz
from Keyboards.main_menu import main_menu_keyboard

# Handlers (boshqaruvchilar) uchun Router yaratamiz
start_router = Router()

# Foydalanuvchi /start bosganida ishlaydigan funksiya
@start_router.message(CommandStart())
async def command_start_handler(message: types.Message):
    await message.answer(
        text=f"Salom, {message.from_user.full_name}! Botimizga xush kelibsiz.\n"
             f"Quyidagi tugma orqali vazifalarni ko'rishingiz mumkin 👇",
        reply_markup=main_menu_keyboard # Boyagi tugmani xabarga biriktiramiz
    )
