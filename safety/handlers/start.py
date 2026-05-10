import json

from aiogram import types
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from safety.loader import dp

from keyboards.admin_keyboard import (
    owner_panel,
    cashier_menu
)


USERS_FILE = "safety/database/users.json"

PENDING_FILE = "safety/database/pending_users.json"


OWNER_ID = 6500594896
# <-- O'Z TELEGRAM ID'INGIZNI YOZING


# ================= LOAD JSON =================

def load_json(path):

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except:

        return {}


def save_json(path, data):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ================= START =================

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):

    users = load_json(
        USERS_FILE
    )

    pending = load_json(
        PENDING_FILE
    )

    user_id = str(
        message.from_user.id
    )

    fullname = (
        message.from_user.full_name
    )

    # ================= APPROVED USER =================

    if user_id in users:

        role = users[user_id]["role"]

        # OWNER

        if role == "owner":

            return await message.answer(
                f"""
👋 Xush kelibsiz, {fullname}

🎭 Role: OWNER
""",
                reply_markup=owner_panel
            )

        # CASHIER

        if role == "cashier":

            return await message.answer(
                f"""
👋 Xush kelibsiz, {fullname}

🎭 Role: CASHIER
""",
                reply_markup=cashier_menu
            )

        # OTHER

        return await message.answer(
            f"""
👋 Xush kelibsiz, {fullname}

🎭 Role: {role.upper()}
"""
        )

    # ================= ALREADY PENDING =================

    if user_id in pending:

        return await message.answer(
            "⏳ Sizning profilingiz tasdiqlanishi kutilmoqda"
        )

    # ================= NEW REQUEST =================

    pending[user_id] = {

        "fullname": fullname,

        "phone": "No phone"
    }

    save_json(
        PENDING_FILE,
        pending
    )

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
                callback_data=f"approve_{user_id}_{role}"
            )
        )

    buttons.append(

        InlineKeyboardButton(
            text="❌ REJECT",
            callback_data=f"reject_{user_id}"
        )
    )

    keyboard.add(*buttons)

    text = f"""
🆕 Yangi user zaprosi

👤 {fullname}

🆔 {user_id}

Approve qilish uchun role tanlang:
"""

    await dp.bot.send_message(
        OWNER_ID,
        text,
        reply_markup=keyboard
    )

    await message.answer(
        "⏳ So'rovingiz moderatorga yuborildi"
    )


# ================= APPROVE =================

@dp.callback_query_handler(
    lambda c: c.data.startswith("approve_")
)
async def approve_user(callback: types.CallbackQuery):

    data = callback.data.split("_")

    user_id = data[1]

    role = data[2]

    users = load_json(
        USERS_FILE
    )

    pending = load_json(
        PENDING_FILE
    )

    if user_id not in pending:

        return await callback.answer(
            "User topilmadi",
            show_alert=True
        )

    users[user_id] = {

        "fullname": pending[user_id]["fullname"],

        "phone": pending[user_id]["phone"],

        "role": role
    }

    save_json(
        USERS_FILE,
        users
    )

    del pending[user_id]

    save_json(
        PENDING_FILE,
        pending
    )

    await callback.message.edit_text(
        f"""
✅ User approved

🆔 {user_id}

🎭 Role: {role.upper()}
"""
    )

    await dp.bot.send_message(
        user_id,
        f"""
✅ Siz tasdiqlandingiz

🎭 Role: {role.upper()}

Qayta /start bosing
"""
    )


# ================= REJECT =================

@dp.callback_query_handler(
    lambda c: c.data.startswith("reject_")
)
async def reject_user(callback: types.CallbackQuery):

    user_id = callback.data.split("_")[1]

    pending = load_json(
        PENDING_FILE
    )

    if user_id in pending:

        del pending[user_id]

    save_json(
        PENDING_FILE,
        pending
    )

    await callback.message.edit_text(
        f"""
❌ User reject qilindi

🆔 {user_id}
"""
    )

    await dp.bot.send_message(
        user_id,
        "❌ So'rovingiz rad etildi"
    )
