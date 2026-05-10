from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard(role=None):

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

        return keyboard


    # KASSIR
    elif role == "kassir":

        keyboard.add(
            KeyboardButton("💰 Cashier Salary")
        )

        return keyboard


    # MANAGER
    elif role == "manager":

        keyboard.add(
            KeyboardButton("📊 Manager Salary")
        )

        return keyboard


    # KOORDINATOR
    elif role == "kordinator":

        keyboard.add(
            KeyboardButton("📈 Coordinator Salary")
        )

        return keyboard


    # DEFAULT
    keyboard.add(
        KeyboardButton("🏠 Bosh sahifa")
    )

    return keyboard

def status_keyboard():
    return get_menu("admin")
