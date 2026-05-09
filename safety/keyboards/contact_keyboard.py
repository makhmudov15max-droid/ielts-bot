from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


contact_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

contact_button = KeyboardButton(
    text="📱 Raqam yuborish",
    request_contact=True
)

contact_keyboard.add(contact_button)
