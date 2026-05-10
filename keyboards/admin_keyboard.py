from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)


# =========================
# MAIN MENU
# =========================

main_menu_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

main_menu_keyboard.add(
    KeyboardButton("📊 Admin Salary")
)

main_menu_keyboard.add(
    KeyboardButton("💰 Cashier Salary")
)

main_menu_keyboard.add(
    KeyboardButton("📈 Manager Salary")
)


# =========================
# STATUS
# =========================

status_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

status_keyboard.row(
    KeyboardButton("Junior")
)

status_keyboard.row(
    KeyboardButton("Middle")
)

status_keyboard.row(
    KeyboardButton("Senior")
)

status_keyboard.row(
    KeyboardButton("🏠 Bosh sahifa")
)


# =========================
# HOURS
# =========================

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
    KeyboardButton("🏠 Bosh sahifa")
)


# =========================
# DAYS
# =========================

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
    KeyboardButton("28 kun")
)

days_keyboard.row(
    KeyboardButton("🏠 Bosh sahifa")
)


# =========================
# YES / NO
# =========================

yes_no_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

yes_no_keyboard.row(
    KeyboardButton("Ha"),
    KeyboardButton("Yo'q")
)

yes_no_keyboard.row(
    KeyboardButton("🏠 Bosh sahifa")
)


# =========================
# CONVERSION
# =========================

conversion_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

conversion_keyboard.row(
    KeyboardButton("50%"),
    KeyboardButton("60%")
)

conversion_keyboard.row(
    KeyboardButton("70%"),
    KeyboardButton("80%")
)

conversion_keyboard.row(
    KeyboardButton("90%"),
    KeyboardButton("100%")
)

conversion_keyboard.row(
    KeyboardButton("🏠 Bosh sahifa")
)


# =========================
# COVER
# =========================

cover_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

cover_keyboard.row(
    KeyboardButton("Ha"),
    KeyboardButton("Yo'q")
)

cover_keyboard.row(
    KeyboardButton("🏠 Bosh sahifa")
)
