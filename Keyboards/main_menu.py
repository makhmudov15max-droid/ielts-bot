from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# "Tasklar ro'yxati" tugmasini yaratamiz
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Tasklar ro'yxati") # Tugma nomi
        ]
    ],
    resize_keyboard=True # Tugma ekran o'lchamiga moslashishi uchun
)
