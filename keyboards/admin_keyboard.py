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


def days_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("24 kun", "25 kun")
    keyboard.add("26 kun", "27 kun")
    keyboard.add("✍️ Boshqa kun")
    keyboard.add("🏠 Bosh sahifa")

    return keyboard


def yes_no_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("✅ Ha", "❌ Yo'q")
    keyboard.add("🏠 Bosh sahifa")

    return keyboard


def conversion_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("50%")
    keyboard.add("✍️ Boshqa")
    keyboard.add("🏠 Bosh sahifa")

    return keyboard


def cover_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("✅ Cover qilgan", "❌ Cover qilmagan")
    keyboard.add("🏠 Bosh sahifa")

    return keyboard
