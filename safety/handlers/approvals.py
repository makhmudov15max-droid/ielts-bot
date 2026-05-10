from aiogram import types

from safety.loader import dp, bot
from safety.config import OWNER_ID

from safety.db import (
    load_users,
    save_users,
    load_pending,
    save_pending,
    load_blocked,
    save_blocked
)


@dp.callback_query_handler(lambda c: c.data.startswith("approve_"))
async def approve_user(callback: types.CallbackQuery):

    if callback.from_user.id != OWNER_ID:
        return

    data = callback.data.split(":")

    role_data = data[0]
    user_id = data[1]

    role = role_data.replace("approve_", "")

    pending = load_pending()

    if user_id not in pending:

        await callback.answer("User topilmadi", show_alert=True)
        return

    users = load_users()

    users[user_id] = {
        "role": role
    }

    save_users(users)

    del pending[user_id]

    save_pending(pending)

    await bot.send_message(
        int(user_id),
        f"✅ Siz tasdiqlandingiz.\n"
        f"🎭 Role: {role}\n\n"
        f"🔄 Endi botni qayta ochish uchun /start bosing."
)

    await callback.message.edit_text(
        f"✅ User tasdiqlandi.\n\n"
        f"🆔 {user_id}\n"
        f"🎭 Role: {role}"
    )


@dp.callback_query_handler(lambda c: c.data.startswith("reject"))
async def reject_user(callback: types.CallbackQuery):

    if callback.from_user.id != OWNER_ID:
        return

    user_id = callback.data.split(":")[1]

    blocked = load_blocked()

    blocked[user_id] = True

    save_blocked(blocked)

    pending = load_pending()

    if user_id in pending:

        del pending[user_id]

    save_pending(pending)

    await bot.send_message(
        int(user_id),
        "❌ Sizning so‘rovingiz rad etildi."
    )

    await callback.message.edit_text(
        f"❌ User rad etildi.\n\n"
        f"🆔 {user_id}"
    )
