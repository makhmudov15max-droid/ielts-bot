from aiogram import types
from safety.loader import dp, bot

from safety.db import load_users (
    load_users,
    save_users,
    load_pending,
    save_pending
)


@dp.callback_query_handler(lambda c: c.data.startswith("role_"))
async def approve_user(callback: types.CallbackQuery):

    data = callback.data.split("_")

    role = data[1]
    user_id = data[2]

    users = load_users()
    pending = load_pending()

    user_data = pending[user_id]

    users[user_id] = {
        "name": user_data["name"],
        "username": user_data["username"],
        "phone": user_data["phone"],
        "role": role
    }

    save_users(users)

    del pending[user_id]
    save_pending(pending)

    await bot.send_message(
        int(user_id),
        f"✅ Siz tasdiqlandingiz.\nRole: {role}"
    )

    await callback.message.edit_text(
        f"✅ User approved\nRole: {role}"
    )


@dp.callback_query_handler(lambda c: c.data.startswith("reject_"))
async def reject_user(callback: types.CallbackQuery):

    user_id = callback.data.split("_")[1]

    pending = load_pending()

    del pending[user_id]

    save_pending(pending)

    await bot.send_message(
        int(user_id),
        "❌ Sizning so‘rovingiz rad etildi."
    )

    await callback.message.edit_text(
        "❌ User rejected"
    )
