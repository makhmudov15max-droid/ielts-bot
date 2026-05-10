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
# CONTACT HANDLER
# =========================================

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact_handler(message: types.Message):

    try:

        user_id = str(message.from_user.id)

        full_name = message.from_user.full_name

        username = message.from_user.username or "username yo'q"

        phone = message.contact.phone_number


        # =========================================
        # OWNER AUTO ACCESS
        # =========================================

        if int(user_id) == OWNER_ID:

            users = load_users()

            users[user_id] = {
                "role": "owner"
            }

            save_users(users)

            await message.answer(
                """
👑 OWNER PROFILE

━━━━━━━━━━━━━━━━━━

✅ Access granted.
"""
            )

            return


        # =========================================
        # BLOCK CHECK
        # =========================================

        blocked = load_blocked()

        if user_id in blocked:

            await message.answer(
                """
❌ ACCESS DENIED

━━━━━━━━━━━━━━━━━━

Siz bloklangansiz.
"""
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
        # INLINE KEYBOARD
        # =========================================

        keyboard = InlineKeyboardMarkup(
            row_width=2
        )

        keyboard.add(

            InlineKeyboardButton(
                "👨‍💼 Admin",
                callback_data=f"approve_admin:{user_id}"
            ),

            InlineKeyboardButton(
                "💰 Kassir",
                callback_data=f"approve_cashier:{user_id}"
            ),

            InlineKeyboardButton(
                "📊 Kordinator",
                callback_data=f"approve_manager:{user_id}"
            ),

            InlineKeyboardButton(
                "❌ Rad etish",
                callback_data=f"reject:{user_id}"
            )
        )


        # =========================================
        # SEND TO OWNER
        # =========================================

        await bot.send_message(
            OWNER_ID,

            f"""
🆕 YANGI FOYDALANUVCHI

━━━━━━━━━━━━━━━━━━

👤 Ism:
{full_name}

📛 Username:
@{username}

📞 Telefon:
{phone}

🆔 ID:
{user_id}
""",

            reply_markup=keyboard
        )


        # =========================================
        # USER WAIT MESSAGE
        # =========================================

        await message.answer(
            """
⏳ So‘rovingiz yuborildi.

Admin tasdiqlashini kuting.
"""
        )

    except Exception as e:

        print("CONTACT ERROR:", e)


# =========================================
# APPROVE USER
# =========================================

@dp.callback_query_handler(
    lambda c: c.data.startswith("approve_")
)
async def approve_user(callback: types.CallbackQuery):

    try:

        print("APPROVE BOSILDI")


        # =========================================
        # PARSE CALLBACK
        # =========================================

        data = callback.data.replace(
            "approve_",
            ""
        )

        role, user_id = data.split(":")

        print(role, user_id)


        # =========================================
        # LOAD USERS
        # =========================================

        users = load_users()

        users[user_id] = {
            "role": role
        }

        save_users(users)

        print("USER SAVED")


        # =========================================
        # DELETE PENDING
        # =========================================

        pending = load_pending()

        if user_id in pending:

            del pending[user_id]

            save_pending(pending)

        print("PENDING CLEARED")


        # =========================================
        # ROLE TEXT
        # =========================================

        role_text = ""

        if role == "admin":

            role_text = "👨‍💼 Admin"

        elif role == "cashier":

            role_text = "💰 Kassir"

        elif role == "manager":

            role_text = "📊 Kordinator"

        else:

            role_text = role.title()


        # =========================================
        # SEND USER
        # =========================================

        await bot.send_message(
            int(user_id),

            f"""
✅ SO‘ROV TASDIQLANDI

━━━━━━━━━━━━━━━━━━

🎭 Role:
{role_text}

🔄 Endi /start bosing.
"""
        )

        print("USER MESSAGE SENT")


        # =========================================
        # CALLBACK ANSWER
        # =========================================

        await callback.answer(
            "Tasdiqlandi ✅"
        )


        # =========================================
        # EDIT OWNER MESSAGE
        # =========================================

        try:

            await callback.message.edit_text(
                f"""
✅ USER TASDIQLANDI

━━━━━━━━━━━━━━━━━━

🆔 User ID:
{user_id}

🎭 Role:
{role_text}
"""
            )

        except Exception as e:

            print("EDIT ERROR:", e)


        print("SUCCESS")


    except Exception as e:

        print("APPROVE ERROR:", e)

        await callback.answer(
            f"Xatolik: {e}",
            show_alert=True
        )


# =========================================
# REJECT USER
# =========================================

@dp.callback_query_handler(
    lambda c: c.data.startswith("reject:")
)
async def reject_user(callback: types.CallbackQuery):

    try:

        user_id = callback.data.split(":")[1]


        # =========================================
        # DELETE PENDING
        # =========================================

        pending = load_pending()

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
            int(user_id),

            """
❌ SO‘ROV RAD ETILDI

━━━━━━━━━━━━━━━━━━

Admin bilan bog‘laning.
"""
        )


        # =========================================
        # CALLBACK ANSWER
        # =========================================

        await callback.answer(
            "Rad etildi ❌"
        )


        # =========================================
        # EDIT OWNER MESSAGE
        # =========================================

        try:

            await callback.message.edit_text(
                f"""
❌ USER RAD ETILDI

━━━━━━━━━━━━━━━━━━

🆔 User ID:
{user_id}

🚫 User bloklandi.
"""
            )

        except Exception as e:

            print("EDIT ERROR:", e)


    except Exception as e:

        print("REJECT ERROR:", e)

        await callback.answer(
            f"Xatolik: {e}",
            show_alert=True
        )
