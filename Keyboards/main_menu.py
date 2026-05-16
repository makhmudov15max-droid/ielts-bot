from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Yonma-yon turadigan tugmalar
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Add Task"), 
            KeyboardButton(text="List of tasks")
        ] # Ikkalasi bitta qatorda
    ],
    resize_keyboard=True
)
