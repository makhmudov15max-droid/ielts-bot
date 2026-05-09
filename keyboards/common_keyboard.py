from aiogram.types import ReplyKeyboardMarkup


def home_keyboard():

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("🏠 Bosh sahifa")

    return keyboard
