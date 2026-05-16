from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Yonma-yon turadigan tugmalar
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Tasklar ro'yxati"), 
            KeyboardButton(text="Task yaratish")
        ] # Ikkalasi bitta qatorda
    ],
    resize_keyboard=True
)
