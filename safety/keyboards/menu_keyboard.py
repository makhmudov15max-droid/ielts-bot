from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_menu(role):

    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    # =========================
    # OWNER / MANAGER
    # =========================

    if role == "manager":

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

    # =========================
    # COORDINATOR
    # =========================

    elif role == "kordinator":

        keyboard.add(
            KeyboardButton("📈 Manager Salary")
        )

    return keyboard
