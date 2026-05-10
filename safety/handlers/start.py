from aiogram import types

from safety.loader import dp

from safety.db import load_users

from keyboards.admin_keyboard import (
    owner_menu,
    cashier_menu,
    manager_menu,
    admin_menu
)


# =========================================
# START
# =========================================

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):

    user_id = str(message.from_user.id)

    users = load_users()


    # =========================================
    # USER NOT FOUND
    # =========================================

    if user_id not in users:

        kb = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        kb.add(
            types.KeyboardButton(
                "📱 Telefon raqam yuborish",
                request_contact=True
            )
        )

        await message.answer(
            """
👋 Assalomu alaykum

Botdan foydalanish uchun
telefon raqamingizni yuboring.
""",

            reply_markup=kb
        )

        return


    # =========================================
    # GET ROLE
    # =========================================

    role = users[user_id]["role"]


    # =========================================
    # OWNER
    # =========================================

    if role == "owner":

        await message.answer(
            """
👑 OWNER PANEL
""",

            reply_markup=owner_menu
        )

        return


    # =========================================
    # CASHIER
    # =========================================

    if role == "cashier":

        await message.answer(
            """
💰 CASHIER PANEL
""",

            reply_markup=cashier_menu
        )

        return


    # =========================================
    # MANAGER
    # =========================================

    if role == "manager":

        await message.answer(
            """
📊 MANAGER PANEL
""",

            reply_markup=manager_menu
        )

        return


    # =========================================
    # ADMIN
    # =========================================

    if role == "admin":

        await message.answer(
            """
👨‍💼 ADMIN PANEL
""",

            reply_markup=admin_menu
        )

        return
