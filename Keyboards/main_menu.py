from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ================= ASOSIY MENU =================
def get_main_menu(role: str):
    role = str(role).strip()

    if role in ["Owner", "Manager"]:
        keyboard = [
            [KeyboardButton(text="➕ Vazifa qoʻshish"), KeyboardButton(text="📋 Vazifalar roʻyxati")],
            [KeyboardButton(text="👥 Xodimlar"), KeyboardButton(text="🗑 Vazifani oʻchirish")],
            [KeyboardButton(text="📊 Admin oylik"), KeyboardButton(text="💰 Kassir oylik")],
            [KeyboardButton(text="🗄 Arxiv"), KeyboardButton(text="📑 Guruh Report")],
            [KeyboardButton(text="👨🏻‍🏫 Ustoz/Ball")],
            [KeyboardButton(text="📸 Isbotlar")]  # <-- YANGI
        ]
    elif role == "Admin":
        keyboard = [
            [KeyboardButton(text="📋 Vazifalar roʻyxati")],
            [KeyboardButton(text="📊 Admin oylik")],
            [KeyboardButton(text="📑 Guruh Report")],
            [KeyboardButton(text="📸 Isbotlar")]  # <-- YANGI
        ]
    elif role == "Kassir":
        keyboard = [
            [KeyboardButton(text="📋 Vazifalar roʻyxati")],
            [KeyboardButton(text="💰 Kassir oylik")]
        ]
    elif role == "Sanitar":
        keyboard = [
            [KeyboardButton(text="📋 Vazifalar roʻyxati")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="📋 Vazifalar roʻyxati")]
        ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ================= BOSHQA KLAVIATURALAR =================
task_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Muntazam (Doimiy)"), KeyboardButton(text="Kunlik (Bir martalik)")]],
    resize_keyboard=True
)

assign_role_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Admin"), KeyboardButton(text="Manager")],
        [KeyboardButton(text="Kassir"), KeyboardButton(text="Sanitar")]
    ],
    resize_keyboard=True
)

days_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Toq kunlar"), KeyboardButton(text="Juft kunlar")],
        [KeyboardButton(text="Haftada 6 kun"), KeyboardButton(text="Boshqa kunlar")]
    ],
    resize_keyboard=True
)

frequency_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Kuniga 1 marta"), KeyboardButton(text="Bir necha marta")]],
    resize_keyboard=True
)

proof_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Dumaloq video"), KeyboardButton(text="Rasm yuborish")]],
    resize_keyboard=True
)

# Inline kunlar uchun
def get_inline_days_keyboard(selected_days: list = None):
    if selected_days is None:
        selected_days = []
    days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    inline_keyboard = []
    for day in days:
        text = f"✅ {day}" if day in selected_days else day
        inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"day_{day}")])
    inline_keyboard.append([InlineKeyboardButton(text="✅ Tanlab bo'ldim", callback_data="days_done")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def get_admin_approval_keyboard(user_id: int):
    roles = ["Admin", "Kassir", "Sanitar", "Manager"]
    inline_keyboard = []
    row = []
    for role in roles:
        row.append(InlineKeyboardButton(text=role, callback_data=f"approve_{role}_{user_id}"))
        if len(row) == 2:
            inline_keyboard.append(row)
            row = []
    inline_keyboard.append([InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def get_task_complete_keyboard(task_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Bajarildi ✅", callback_data=f"completetask_{task_id}")]]
    )


def get_remove_tasks_keyboard(tasks_list: list):
    inline_keyboard = []
    for task in tasks_list:
        btn_text = f"❌ {task['task_name']} ({task.get('assigned_to_name', 'Noma’lum')})"
        inline_keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"removetask_{task['id']}")])
    inline_keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="remove_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# ================= ISBOTLAR UCHUN KLAVIATURALAR =================

def get_proof_role_keyboard():
    """Role tanlash tugmalari"""
    keyboard = [
        [KeyboardButton(text="Admin"), KeyboardButton(text="Kassir")],
        [KeyboardButton(text="Sanitar"), KeyboardButton(text="Manager")],
        [KeyboardButton(text="Barcha xodimlar")],
        [KeyboardButton(text="🏠 Bosh sahifa")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_proof_date_keyboard():
    """Sana tanlash tugmalari"""
    keyboard = [
        [KeyboardButton(text="📅 Bugun"), KeyboardButton(text="📆 Kecha")],
        [KeyboardButton(text="📅 Shu oy"), KeyboardButton(text="📆 O'tgan oy")],
        [KeyboardButton(text="✍️ Boshqa sana")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
