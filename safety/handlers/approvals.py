@dp.callback_query_handler(
    lambda c: c.data.startswith("approve_")
)
async def approve_user(callback: types.CallbackQuery):

    try:

        print("APPROVE BOSILDI")

        data = callback.data.split("_")

        print(data)

        role = data[1]

        user_id = data[2]

        print(role, user_id)


        users = load_users()

        print("USERS LOADED")


        users[user_id] = {
            "role": role
        }

        print("USER ADDED")


        save_users(users)

        print("USERS SAVED")


        pending = load_pending()

        if user_id in pending:

            del pending[user_id]

            save_pending(pending)

        print("PENDING CLEARED")


        await bot.send_message(
            int(user_id),

            f"""
✅ So‘rovingiz tasdiqlandi.

🎭 Role:
{role}

🔄 Endi /start bosing.
"""
        )

        print("USERGA XABAR KETDI")


        await callback.answer(
            "Tasdiqlandi ✅"
        )


        await callback.message.edit_text(
            f"""
✅ USER TASDIQLANDI

🆔 ID:
{user_id}

🎭 Role:
{role}
"""
        )

        print("SUCCESS")


    except Exception as e:

        print("APPROVE ERROR:")
        print(e)

        await callback.answer(
            f"Xato: {e}",
            show_alert=True
        )
