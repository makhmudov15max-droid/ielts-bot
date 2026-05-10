from aiogram import types

from safety.loader import dp, bot
from safety.config import OWNER_ID
from aiogram.types import ReplyKeyboardRemove

from safety.keyboards.contact_keyboard import contact_keyboard
from safety.keyboards.menu_keyboard import get_menu

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

    # Agar user approved bo‘lsa
    if user_id in users:

        role = users[user_id]["role"]
        await message.answer(
            "✅ Menu yuklandi",
            reply_markup=ReplyKeyboardRemove()
        )
        
        await message.answer(
            "🏠 Bosh sahifa",
            reply_markup=get_menu(role)
        )
        return

    # Pending userlarni tekshirish
    pending = load_pending()

    if user_id in pending:

        await message.answer(
            "⏳ So‘rovingiz adminga yuborilgan.\nTasdiqlanishini kuting."
        )
        return

    # Telefon raqam so‘rash
    await message.answer(
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=contact_keyboard
    )


@dp.message_handler(content_types=types.ContentType.CONTACT)
async def get_contact(message: types.Message):

    user_id = str(message.from_user.id)

    pending = load_pending()

    pending[user_id] = {
        "full_name": message.from_user.full_name,
        "username": message.from_user.username,
        "phone": message.contact.phone_number
    }

    save_pending(pending)

    text = (
        f"🆕 Yangi foydalanuvchi!\n\n"
        f"👤 Ism: {message.from_user.full_name}\n"
        f"📛 Username: @{message.from_user.username}\n"
        f"📞 Telefon: {message.contact.phone_number}\n"
        f"🆔 ID: {message.from_user.id}"
    )

    await bot.send_message(OWNER_ID, text)

    await message.answer(
        "✅ So‘rovingiz yuborildi.\nAdmin tasdiqlashini kuting."
    )
