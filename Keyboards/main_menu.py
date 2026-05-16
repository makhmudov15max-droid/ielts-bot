from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Yonma-yon turadigan tugmalar
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Task yaratish"), 
            KeyboardButton(text="Tasklar ro'yxati")
        ] # Ikkalasi bitta qatorda
    ],
    resize_keyboard=True
)
