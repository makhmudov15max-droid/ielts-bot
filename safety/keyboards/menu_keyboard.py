from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_menu(role):

    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    if role == "manager":

        keyboard.add("📊 Admin Salary")
        keyboard.add("💰 Kassir Salary")
        keyboard.add("👥 Users")

    elif role == "admin":

        keyboard.add("📊 Admin Salary")

    elif role == "cashier":

        keyboard.add("💰 Kassir Salary")

    elif role == "coordinator":

        keyboard.add("📊 Admin Salary")
        keyboard.add("💰 Kassir Salary")

    return keyboard
