from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)


# =========================================
# OWNER MENU
# =========================================

owner_menu = ReplyKeyboardMarkup(
    resize_keyboard=True
)

owner_menu.row(
    KeyboardButton("💰 Cashier Salary")
)

owner_menu.row(
    KeyboardButton("👨‍💼 Admin Salary")
)

owner_menu.row(
    KeyboardButton("📊 Manager Salary")
)


# =========================================
# CASHIER MENU
# =========================================

cashier_menu = ReplyKeyboardMarkup(
    resize_keyboard=True
)

cashier_menu.row(
    KeyboardButton("💰 Cashier Salary")
)


# =========================================
# MANAGER MENU
# =========================================

manager_menu = ReplyKeyboardMarkup(
    resize_keyboard=True
)

manager_menu.row(
    KeyboardButton("📊 Manager Salary")
)


# =========================================
# ADMIN MENU
# =========================================

admin_menu = ReplyKeyboardMarkup(
    resize_keyboard=True
)

admin_menu.row(
    KeyboardButton("👨‍💼 Admin Salary")
)

# =========================================
# DEFAULT MAIN MENU
# =========================================

main_menu_keyboard = owner_menu

# =========================================
# OLD COMPATIBILITY
# =========================================

status_keyboard = owner_menu
