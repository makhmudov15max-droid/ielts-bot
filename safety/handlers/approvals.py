from aiogram import types

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
# APPROVE
# =========================================

@dp.callback_query_handler(lambda c: c.data.startswith("approve_"))
async def approve_user(callback: types.CallbackQuery):

    data = callback.data.split("_")

    role = data[1]
    user_id = data[2]

    pending = load_pending()

    if user_id not in pending:

        await callback.answer(
            "User topilmadi."
        )
        return

    users = load_users()

    users[user_id] = {
        "role": role
    }

    save_users(users)

    del pending[user_id]

    save_pending(pending)

    await bot.send_message(
        user_id,
        f"✅ Siz tasdiqlandingiz.\n"
        f"🎭 Role: {role}\n\n"
        f"🔄 Endi /start bosing."
    )

    await callback.message.edit_text(
        f"✅ User tasdiqlandi.\n"
        f"Role: {role}"
    )

    await callback.answer()


# =========================================
# REJECT
# =========================================

@dp.callback_query_handler(lambda c: c.data.startswith("reject_"))
async def reject_user(callback: types.CallbackQuery):

    user_id = callback.data.split("_")[1]

    pending = load_pending()

    if user_id in pending:

        del pending[user_id]

        save_pending(pending)

    blocked = load_blocked()

    if user_id not in blocked:

        blocked.append(user_id)

    save_blocked(blocked)

    await bot.send_message(
        user_id,
        "❌ Sizning so‘rovingiz rad etildi."
    )

    await callback.message.edit_text(
        "❌ User rad etildi va bloklandi."
    )

    await callback.answer()
