from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def approval_keyboard(user_id):

    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton(
            "👑 Admin",
            callback_data=f"approve_admin:{user_id}"
        ),

        InlineKeyboardButton(
            "💰 Kassir",
            callback_data=f"approve_kassir:{user_id}"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "📊 Kordinator",
            callback_data=f"approve_kordinator:{user_id}"
        ),

        InlineKeyboardButton(
            "🚀 Manager",
            callback_data=f"approve_manager:{user_id}"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "❌ Rad etish",
            callback_data=f"reject:{user_id}"
        )
    )

    return keyboard
