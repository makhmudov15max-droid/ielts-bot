from aiogram.types import ReplyKeyboardMarkup


def cashier_hours_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("6 soat", "7 soat")
    keyboard.add("8 soat", "9 soat")

    keyboard.add("✍️ Boshqa")

    keyboard.add("🏠 Bosh sahifa")

    return keyboard


def cashier_days_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("24 kun", "25 kun")
    keyboard.add("26 kun", "27 kun")

    keyboard.add("✍️ Boshqa")

    keyboard.add("🏠 Bosh sahifa")

    return keyboard


def yes_no_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("✅ Ha", "❌ Yo'q")

    keyboard.add("🏠 Bosh sahifa")

    return keyboard


def home_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("🏠 Bosh sahifa")

    return keyboard
