from aiogram import types
from safety.loader import dp, bot
from config import OWNER_ID

from keyboards.contact_keyboard import contact_keyboard
from keyboards.role_keyboard import role_keyboard
from keyboards.menu_keyboard import get_menu

from safety.db import (
    load_users,
    save_users,
    load_pending,
    save_pending
)

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):

    user_id = str(message.from_user.id)

    users = load_users()
    pending = load_pending()

    # APPROVED USER
    if user_id in users:

        role = users[user_id]["role"]

        await message.answer(
            f"✅ Xush kelibsiz\nRole: {role}",
            reply_markup=get_menu(role)
        )

        return

    # PENDING USER
    if user_id in pending:

        await message.answer(
            "⏳ So‘rovingiz ko‘rib chiqilmoqda."
        )

        return

    # NEW USER
    await message.answer(
        "📱 Davom etish uchun raqamingizni yuboring",
        reply_markup=contact_keyboard
    )


@dp.message_handler(content_types=types.ContentType.CONTACT)
async def get_contact(message: types.Message):

    user_id = str(message.from_user.id)

    pending = load_pending()

    if user_id in pending:
        return

    pending[user_id] = {
        "name": message.from_user.full_name,
        "username": message.from_user.username,
        "phone": message.contact.phone_number
    }

    save_pending(pending)

    text = (
        f"🆕 Yangi foydalanuvchi\n\n"
        f"👤 Ism: {message.from_user.full_name}\n"
        f"📛 Username: @{message.from_user.username}\n"
        f"🆔 ID: {user_id}\n"
        f"📱 {message.contact.phone_number}"
    )

    await bot.send_message(
        OWNER_ID,
        text,
        reply_markup=role_keyboard(user_id)
    )

    await message.answer(
        "✅ So‘rovingiz yuborildi.\nTasdiqlanishni kuting."
    )
