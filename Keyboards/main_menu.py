from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Asosiy menyu tugmalari
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Add Task"), 
            KeyboardButton(text="List of tasks")
        ] # Ikkalasi bitta qatorda
    ],
    resize_keyboard=True
)

# Task turini tanlash uchun yangi tugmalar (bitta qatorda yonma-yon)
task_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Continuously"),
            KeyboardButton(text="Daily")
        ]
    ],
    resize_keyboard=True
)

# Kunlarni tanlash tugmalari
days_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ODD"), KeyboardButton(text="EVEN")],
        [KeyboardButton(text="6 days a week"), KeyboardButton(text="OTHER")]
    ],
    resize_keyboard=True
)

# Kuniga necha marta bajarilishini so'rash tugmalari (Yangi qo'shildi)
frequency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Once"),
            KeyboardButton(text="Multiple times")
        ]
    ],
    resize_keyboard=True
)
