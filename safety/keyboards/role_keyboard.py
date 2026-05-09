from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def role_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton(
            "👑 Manager",
            callback_data=f"role_manager_{user_id}"
        ),

        InlineKeyboardButton(
            "🛡 Admin",
            callback_data=f"role_admin_{user_id}"
        ),

        InlineKeyboardButton(
            "💰 Kassir",
            callback_data=f"role_cashier_{user_id}"
        ),

        InlineKeyboardButton(
            "📋 Kordinator",
            callback_data=f"role_coordinator_{user_id}"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "❌ Reject",
            callback_data=f"reject_{user_id}"
        )
    )

    return keyboard
