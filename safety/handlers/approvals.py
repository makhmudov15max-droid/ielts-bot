from aiogram import types

from safety.loader import dp, bot
from safety.config import OWNER_ID

from safety.db import (
    load_users,
    save_users,
    load_pending,
    save_pending
)


@dp.message_handler(commands=["approve"])
async def approve_user(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    args = message.get_args().split()

    if len(args) != 2:

        await message.answer(
            "❌ Format:\n/approve USER_ID ROLE"
        )
        return

    user_id = args[0]
    role = args[1]

    pending = load_pending()

    if user_id not in pending:

        await message.answer(
            "❌ User pending listda yo‘q."
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
        int(user_id),
        f"✅ Siz tasdiqlandingiz.\nRole: {role}"
    )

    await message.answer(
        "✅ User muvaffaqiyatli tasdiqlandi."
    )
