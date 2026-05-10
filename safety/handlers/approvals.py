from aiogram import types
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from safety.loader import dp, bot

from safety.db import (
    load_users,
    save_users,
    load_pending,
    save_pending,
    load_blocked,
    save_blocked
)


# =========================================
# OWNER ID
# =========================================

OWNER_ID = 6500594896


# =========================================
# CONTACT SHARE
# =========================================

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact_handler(message: types.Message):

    user_id = str(message.from_user.id)

    full_name = message.from_user.full_name

    phone = message.contact.phone_number


    # =========================================
    # OWNER
    # =========================================

    if int(user_id) == OWNER_ID:

        users = load_users()

        users[user_id] = {
            "role": "owner"
        }

        save_users(users)

        await message.answer(
            "👑 Owner profile aniqlandi.\n\n✅ Access granted."
        )

        return


    # =========================================
    # BLOCK CHECK
    # =========================================

    blocked = load_blocked()

    if user_id in blocked:

        await message.answer(
            "❌ Siz bloklangansiz."
        )

        return


    # =========================================
    # SAVE PENDING
    # =========================================

    pending = load_pending()

    pending[user_id] = {
        "name": full_name,
        "phone": phone
    }

    save_pending(pending)


    # =========================================
    # INLINE BUTTONS
    # =========================================

    keyboard = InlineKeyboardMarkup(
        row_width=2
    )

    keyboard.add(

        InlineKeyboardButton(
            "👨‍💼 Admin",
            callback_data=f"approve_admin_{user_id}"
        ),

        InlineKeyboardButton(
            "💰 Cashier",
            callback_data=f"approve_cashier_{user_id}"
        ),

        InlineKeyboardButton(
            "📊 Manager",
            callback_data=f"approve_manager_{user_id}"
        ),

        InlineKeyboardButton(
            "❌ Reject",
            callback_data=f"reject_{user_id}"
        )
    )


    # =========================================
    # SEND TO OWNER
    # =========================================

    await bot.send_message(
        OWNER_ID,

        f"""
📥 YANGI SO‘ROV

━━━━━━━━━━━━━━━━━━

👤 Ism:
{full_name}

📞 Telefon:
{phone}

🆔 ID:
{user_id}
""",

        reply_markup=keyboard
    )


    # =========================================
    # WAIT MESSAGE
    # =========================================

    await message.answer(
        """
⏳ So‘rovingiz yuborildi.

Admin tasdiqlashini kuting.
"""
    )


# =========================================
# APPROVE
# =========================================

@dp.callback_query_handler(
    lambda c: c.data.startswith("approve_")
)
async def approve_user(callback: types.CallbackQuery):

    data = callback.data.split("_")

    role = data[1]

    user_id = data[2]


    pending = load_pending()


    if user_id not in pending:

        await callback.answer(
            "❌ User topilmadi."
        )
        return


    # =========================================
    # SAVE USER
    # =========================================

    users = load_users()

    users[user_id] = {
        "role": role
    }

    save_users(users)


    # =========================================
    # DELETE PENDING
    # =========================================

    del pending[user_id]

    save_pending(pending)


    # =========================================
    # ROLE TEXT
    # =========================================

    role_text = ""

    if role == "admin":

        role_text = "👨‍💼 Admin"

    elif role == "cashier":

        role_text = "💰 Cashier"

    elif role == "manager":

        role_text = "📊 Manager"


    # =========================================
    # SEND USER
    # =========================================

    await bot.send_message(
        user_id,

        f"""
✅ Siz tasdiqlandingiz.

━━━━━━━━━━━━━━━━━━

🎭 Role:
{role_text}

🔄 Endi /start bosing.
"""
    )


    # =========================================
    # EDIT OWNER MESSAGE
    # =========================================

    await callback.message.edit_text(
        f"""
✅ USER TASDIQLANDI

━━━━━━━━━━━━━━━━━━

🆔 User:
{user_id}

🎭 Role:
{role_text}
"""
    )


    await callback.answer(
        "Tasdiqlandi ✅"
    )


# =========================================
# REJECT
# =========================================

@dp.callback_query_handler(
    lambda c: c.data.startswith("reject_")
)
async def reject_user(callback: types.CallbackQuery):

    user_id = callback.data.split("_")[1]


    pending = load_pending()


    # =========================================
    # DELETE PENDING
    # =========================================

    if user_id in pending:

        del pending[user_id]

        save_pending(pending)


    # =========================================
    # BLOCK USER
    # =========================================

    blocked = load_blocked()

    if user_id not in blocked:

        blocked.append(user_id)

    save_blocked(blocked)


    # =========================================
    # SEND USER
    # =========================================

    await bot.send_message(
        user_id,

        """
❌ So‘rovingiz rad etildi.

Admin bilan bog‘laning.
"""
    )


    # =========================================
    # EDIT OWNER MESSAGE
    # =========================================

    await callback.message.edit_text(
        f"""
❌ USER RAD ETILDI

━━━━━━━━━━━━━━━━━━

🆔 User:
{user_id}

🚫 User bloklandi.
"""
    )


    await callback.answer(
        "Rad etildi ❌"
    )
