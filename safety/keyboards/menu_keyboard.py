from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_menu(role):

    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    # =========================
    # FULL ACCESS ROLES
    # =========================

    if role in ["manager", "kordinator"]:

        keyboard.add(
            KeyboardButton("📈 Manager Salary")
        )

        keyboard.add(
            KeyboardButton("📊 Admin Salary")
        )

        keyboard.add(
            KeyboardButton("💰 Cashier Salary")
        )

    # =========================
    # ADMIN
    # =========================

    elif role == "admin":

        keyboard.add(
            KeyboardButton("📊 Admin Salary")
        )

    # =========================
    # CASHIER
    # =========================

    elif role == "kassir":

        keyboard.add(
            KeyboardButton("💰 Cashier Salary")
        )

    return keyboard
