from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_menu(role):

    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    # MANAGER
    if role == "manager":

        keyboard.add(
            KeyboardButton("📊 Admin Salary")
        )

        keyboard.add(
            KeyboardButton("💰 Cashier Salary")
        )

    # ADMIN
    elif role == "admin":

        keyboard.add(
            KeyboardButton("📊 Admin Salary")
        )

    # KASSIR
    elif role == "kassir":

        keyboard.add(
            KeyboardButton("💰 Cashier Salary")
        )

    # KORDINATOR
    elif role == "kordinator":

        keyboard.add(
            KeyboardButton("📊 Admin Salary")
        )

        keyboard.add(
            KeyboardButton("💰 Cashier Salary")
        )

    return keyboard
