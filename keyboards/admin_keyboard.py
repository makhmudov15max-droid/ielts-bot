from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from safety.keyboards.menu_keyboard import get_menu


# =========================
# MAIN MENU
# =========================

def main_menu_keyboard():
    return get_menu("admin")


# =========================
# HOURS KEYBOARD
# =========================

def hours_keyboard():

    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        KeyboardButton("6 soat"),
        KeyboardButton("7 soat")
    )

    keyboard.add(
        KeyboardButton("8 soat"),
        KeyboardButton("9 soat")
    )

    keyboard.add(
        KeyboardButton("✍️ Boshqa")
    )

    keyboard.add(
        KeyboardButton("🏠 Bosh sahifa")
    )

    return keyboard


# =========================
# DAYS KEYBOARD
# =========================

def days_keyboard():

    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        KeyboardButton("24 kun"),
        KeyboardButton("25 kun")
    )

    keyboard.add(
        KeyboardButton("26 kun"),
        KeyboardButton("27 kun")
    )

    keyboard.add(
        KeyboardButton("✍️ Boshqa")
    )

    keyboard.add(
        KeyboardButton("🏠 Bosh sahifa")
    )

    return keyboard


# =========================
# YES / NO
# =========================

def status_keyboard():

    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        KeyboardButton("✅ Ha"),
        KeyboardButton("❌ Yo'q")
    )

    keyboard.add(
        KeyboardButton("🏠 Bosh sahifa")
    )

    return keyboard
