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

def hours_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("6 soat", "7 soat")
    keyboard.add("9 soat", "10 soat")
    keyboard.add("✍️ Boshqa soat")
    keyboard.add("🏠 Bosh sahifa")

    return keyboard
