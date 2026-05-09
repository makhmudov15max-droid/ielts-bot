from aiogram.types import ReplyKeyboardMarkup


def main_menu_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("💰 Admin Salary")
    keyboard.add("💵 Cashier Salary")

    return keyboard


def status_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Nova", "Prime")
    keyboard.add("Apex", "Leader")
    keyboard.add("🏠 Bosh sahifa")

    return keyboard
