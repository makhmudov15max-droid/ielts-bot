import json

from aiogram import types

from safety.loader import dp

from keyboards.admin_keyboard import (
    owner_panel,
    cashier_menu
)


USERS_FILE = "safety/database/users.json"


# ================= LOAD USERS =================

def load_users():

    try:

        with open(
            USERS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except:

        return {}


# ================= START =================

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):

    users = load_users()

    user_id = str(message.from_user.id)

    # ================= USER NOT FOUND =================

    if user_id not in users:

        return await message.answer(
            "⛔ Sizga hali access berilmagan"
        )

    user = users[user_id]

    role = user.get("role")

    fullname = user.get(
        "fullname",
        message.from_user.full_name
    )

    # ================= OWNER =================

    if role == "owner":

        return await message.answer(
            f"""
👋 Xush kelibsiz, {fullname}

🎭 Role: OWNER
""",
            reply_markup=owner_panel
        )

    # ================= CASHIER =================

    if role == "cashier":

        return await message.answer(
            f"""
👋 Xush kelibsiz, {fullname}

🎭 Role: CASHIER
""",
            reply_markup=cashier_menu
        )

    # ================= OTHER ROLES =================

    return await message.answer(
        f"""
👋 Xush kelibsiz, {fullname}

🎭 Role: {role.upper()}
"""
    )
