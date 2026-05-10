from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


owner_menu = ReplyKeyboardMarkup(
    resize_keyboard=True
)

owner_menu.add(
    KeyboardButton("💰 Cashier Salary")
)

owner_menu.add(
    KeyboardButton("📊 Admin Salary")
)

owner_menu.add(
    KeyboardButton("👥 Pending Users")
)

owner_menu.add(
    KeyboardButton("🏠 Bosh sahifa")
)


admin_menu = ReplyKeyboardMarkup(
    resize_keyboard=True
)

admin_menu.add(
    KeyboardButton("📊 Admin Salary")
)

admin_menu.add(
    KeyboardButton("🏠 Bosh sahifa")
)


cashier_menu = ReplyKeyboardMarkup(
    resize_keyboard=True
)

cashier_menu.add(
    KeyboardButton("💰 Cashier Salary")
)

cashier_menu.add(
    KeyboardButton("🏠 Bosh sahifa")
)
