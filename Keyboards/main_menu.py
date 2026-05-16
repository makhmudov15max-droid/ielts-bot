from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# "Vazifalar" tugmasini yaratamiz
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Vazifalar") # Tugma nomi
        ]
    ],
    resize_keyboard=True # Tugma ekran o'lchamiga moslashishi uchun
)
