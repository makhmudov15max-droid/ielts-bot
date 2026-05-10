from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


admin_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

admin_keyboard.add(
    KeyboardButton("💰 Cashier Salary")
)

admin_keyboard.add(
    KeyboardButton("📊 Admin Salary")
)

admin_keyboard.add(
    KeyboardButton("🏠 Bosh sahifa")
)
