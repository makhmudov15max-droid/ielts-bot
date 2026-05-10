from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)


main_menu_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

main_menu_keyboard.add(
    KeyboardButton("📊 Admin Salary")
)

main_menu_keyboard.add(
    KeyboardButton("💰 Cashier Salary")
)

main_menu_keyboard.add(
    KeyboardButton("📈 Manager Salary")
)
