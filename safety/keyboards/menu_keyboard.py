from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_menu(role):

    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True
    )


    # ADMIN
    if role == "admin":

        keyboard.add(
            KeyboardButton("📊 Admin Salary")
        )

        keyboard.add(
            KeyboardButton("💰 Cashier Salary")
        )


    # KASSIR
    elif role == "kassir":

        keyboard.add(
            KeyboardButton("💰 Cashier Salary")
        )


    # MANAGER
    elif role == "manager":

        keyboard.add(
            KeyboardButton("📈 Manager Salary")
        )


    # KORDINATOR
    elif role == "kordinator":

        keyboard.add(
            KeyboardButton("📋 Coordinator Salary")
        )


    return keyboard
