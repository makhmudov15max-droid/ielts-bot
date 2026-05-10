from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)


# ================= OWNER / MANAGER / COORDINATOR =================

owner_panel = ReplyKeyboardMarkup(
    resize_keyboard=True
)

owner_panel.row(
    KeyboardButton("📊 Admin Salary"),
    KeyboardButton("💰 Cashier Salary")
)

owner_panel.row(
    KeyboardButton("🔄 Change Role")
)


# ================= ADMIN =================

admin_menu = ReplyKeyboardMarkup(
    resize_keyboard=True
)

admin_menu.row(
    KeyboardButton("📊 Admin Salary")
)


# ================= CASHIER =================

cashier_menu = ReplyKeyboardMarkup(
    resize_keyboard=True
)

cashier_menu.row(
    KeyboardButton("💰 Cashier Salary")
)
