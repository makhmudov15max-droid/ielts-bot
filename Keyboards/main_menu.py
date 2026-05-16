from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Ustma-ust tushadigan tugmalar
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Task qo'shish")], # 1-qator
        [KeyboardButton(text="Tasklar ro'yxati")] # 2-qator
    ],
    resize_keyboard=True
)
