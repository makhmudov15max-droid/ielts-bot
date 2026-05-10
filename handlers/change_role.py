import json

from aiogram import types
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from safety.loader import dp

from states.role_states import RoleStates


USERS_FILE = "safety/database/users.json"


# ================= LOAD USERS =================

def load_users():

    with open(
        USERS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def save_users(data):

    with open(
        USERS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ================= SHOW USERS =================

@dp.message_handler(text="🔄 Change Role")
async def change_role_menu(message: types.Message):

    users = load_users()

    if not users:

        return await message.answer(
            "Userlar topilmadi"
        )

    for user_id, user_data in users.items():

        fullname = user_data.get(
            "fullname",
            "No name"
        )

        phone = user_data.get(
            "phone",
            "No phone"
        )

        role = user_data.get(
            "role",
            "No role"
        )

        keyboard = InlineKeyboardMarkup()

        keyboard.add(
            InlineKeyboardButton(
                text="🔄 Change Role",
                callback_data=f"change_{user_id}"
            )
        )

        text = f"""
👤 {fullname}

🆔 {user_id}

📞 {phone}

🎭 {role}
"""

        await message.answer(
            text,
            reply_markup=keyboard
        )


# ================= ROLE BUTTONS =================

@dp.callback_query_handler(
    lambda c: c.data.startswith("change_")
)
async def select_role(callback: types.CallbackQuery):

    user_id = callback.data.split("_")[1]

    keyboard = InlineKeyboardMarkup(
        row_width=2
    )

    roles = [
        "owner",
        "coordinator",
        "cashier",
        "admin",
        "teacher"
    ]

    buttons = []

    for role in roles:

        buttons.append(
            InlineKeyboardButton(
                text=role.upper(),
                callback_data=f"role_{user_id}_{role}"
            )
        )

    keyboard.add(*buttons)

    await callback.message.edit_text(
        f"🆔 {user_id}\n\nYangi role tanlang:",
        reply_markup=keyboard
    )


# ================= UPDATE ROLE =================

@dp.callback_query_handler(
    lambda c: c.data.startswith("role_")
)
async def update_role(callback: types.CallbackQuery):

    data = callback.data.split("_")

    user_id = data[1]

    new_role = data[2]

    users = load_users()

    if user_id not in users:

        return await callback.answer(
            "User topilmadi",
            show_alert=True
        )

    users[user_id]["role"] = new_role

    save_users(users)

    await callback.message.edit_text(
        f"""
✅ Role updated

🆔 {user_id}

🎭 New role: {new_role.upper()}
"""
    )
