from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)


# HOURS KEYBOARD

hours_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

hours_keyboard.row(
    KeyboardButton("6 soat"),
    KeyboardButton("7 soat")
)

hours_keyboard.row(
    KeyboardButton("8 soat"),
    KeyboardButton("9 soat")
)

hours_keyboard.row(
    KeyboardButton("Boshqa")
)

hours_keyboard.row(
    KeyboardButton("🏠 Bosh sahifa"),
    KeyboardButton("⬅️ Ortga")
)


# DAYS KEYBOARD

days_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

days_keyboard.row(
    KeyboardButton("24 kun"),
    KeyboardButton("25 kun")
)

days_keyboard.row(
    KeyboardButton("26 kun"),
    KeyboardButton("27 kun")
)

days_keyboard.row(
    KeyboardButton("28 kun"),
    KeyboardButton("Boshqa")
)

days_keyboard.row(
    KeyboardButton("🏠 Bosh sahifa"),
    KeyboardButton("⬅️ Ortga")
)


# YES / NO

yes_no_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

yes_no_keyboard.row(
    KeyboardButton("Ha"),
    KeyboardButton("Yo'q")
)

yes_no_keyboard.row(
    KeyboardButton("🏠 Bosh sahifa"),
    KeyboardButton("⬅️ Ortga")
)


# BACK KEYBOARD

back_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

back_keyboard.row(
    KeyboardButton("🏠 Bosh sahifa"),
    KeyboardButton("⬅️ Ortga")
)
