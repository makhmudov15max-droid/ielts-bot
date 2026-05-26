from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# ========== ASOSIY MENU ==========
def get_main_menu(role: str):
    role = str(role).strip()
    if role in ["Owner", "Manager"]:
        keyboard = [
            [KeyboardButton(text="➕ Vazifa qo'shish"), KeyboardButton(text="📋 Vazifalar ro'yxati")],
            [KeyboardButton(text="👥 Xodimlar"), KeyboardButton(text="🗑 Vazifani o'chirish")],
            [KeyboardButton(text="📊 Admin oylik"), KeyboardButton(text="💰 Kassir oylik")],
            [KeyboardButton(text="🗄 Arxiv"), KeyboardButton(text="📑 Guruh Report")],
            [KeyboardButton(text="👨🏻‍🏫 Ustoz/Ball"), KeyboardButton(text="🎯 Monitoring")],  # ✅ yonma-yon
            [KeyboardButton(text="📸 Isbotlar")]
        ]
    elif role == "Admin":
        keyboard = [
            [KeyboardButton(text="📋 Vazifalar ro'yxati")],
            [KeyboardButton(text="📊 Admin oylik")],
            [KeyboardButton(text="📑 Guruh Report")]
        ]
    elif role == "Kassir":
        keyboard = [
            [KeyboardButton(text="📋 Vazifalar ro'yxati")],
            [KeyboardButton(text="💰 Kassir oylik")]
        ]
    elif role == "Sanitar":
        keyboard = [
            [KeyboardButton(text="📋 Vazifalar ro'yxati")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="📋 Vazifalar ro'yxati")]
        ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ================= ORTGA / BOSH SAHIFA =================
def get_back_home_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Ortga"), KeyboardButton(text="🏠 Bosh sahifa")]],
        resize_keyboard=True
    )


# ================= STATIC KEYBOARDS (BARCHA STEPLAR UCHUN TUGMALAR) =================

# Vazifa turi tanlash (1-step)
task_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Muntazam (Doimiy)"), KeyboardButton(text="Kunlik (Bir martalik)")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ],
    resize_keyboard=True
)

# Unvon tanlash (2-step)
assign_role_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Admin"), KeyboardButton(text="Manager")],
        [KeyboardButton(text="Kassir"), KeyboardButton(text="Sanitar")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ],
    resize_keyboard=True
)

# Kunlar tanlash (doimiy vazifa uchun)
days_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Toq kunlar"), KeyboardButton(text="Juft kunlar")],
        [KeyboardButton(text="Haftada 6 kun"), KeyboardButton(text="Boshqa kunlar")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ],
    resize_keyboard=True
)

# Chastota tanlash (kuniga necha marta)
frequency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Kuniga 1 marta"), KeyboardButton(text="Bir necha marta")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ],
    resize_keyboard=True
)

# Isbot turi tanlash
proof_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Dumaloq video"), KeyboardButton(text="Rasm yuborish")],
        [KeyboardButton(text="✍️ Matn yuborish")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ],
    resize_keyboard=True
)


# ================= INLINE KEYBOARDS =================
def get_inline_days_keyboard(selected_days: list = None):
    if selected_days is None:
        selected_days = []
    days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    inline_keyboard = []
    for day in days:
        text = f"✅ {day}" if day in selected_days else day
        inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"day_{day}")])
    inline_keyboard.append([InlineKeyboardButton(text="✅ Tanlab bo'ldim", callback_data="days_done")])
    inline_keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_task_creation")])
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
    if row:
        inline_keyboard.append(row)
    inline_keyboard.append([InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def get_task_complete_keyboard(task_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"completetask_{task_id}")]]
    )


def get_remove_tasks_keyboard(tasks_list: list):
    inline_keyboard = []
    for task in tasks_list:
        btn_text = f"❌ {task['task_name']} ({task.get('assigned_to_name', 'Noma’lum')})"
        inline_keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"removetask_{task['id']}")])
    inline_keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="remove_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# ================= ISBOTLAR KEYBOARDS =================
def get_proof_role_keyboard():
    keyboard = [
        [KeyboardButton(text="Admin"), KeyboardButton(text="Kassir")],
        [KeyboardButton(text="Sanitar"), KeyboardButton(text="Manager")],
        [KeyboardButton(text="Barcha xodimlar")],
        [KeyboardButton(text="🏠 Bosh sahifa")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_proof_date_keyboard():
    keyboard = [
        [KeyboardButton(text="📅 Bugun"), KeyboardButton(text="📆 Kecha")],
        [KeyboardButton(text="📅 Shu oy"), KeyboardButton(text="📆 O'tgan oy")],
        [KeyboardButton(text="✍️ Boshqa sana")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ================= VAZIFALAR RO'YXATI KEYBOARDS =================
def get_tasks_simple_keyboard():
    """Vazifalar ro'yxati uchun 3 tugma (Bugun, Sana, Bosh sahifa)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Bugun")],
            [KeyboardButton(text="📆 Sana")],
            [KeyboardButton(text="🏠 Bosh sahifa")]
        ],
        resize_keyboard=True
    )


def get_custom_date_keyboard_simple():
    """60 kunlik sanalar ro'yxati (har bir qatorda 2 tadan) + Bosh sahifa va Ortga"""
    from datetime import datetime, timedelta, timezone
    
    tashkent_tz = timezone(timedelta(hours=5))
    now = datetime.now(tashkent_tz)
    
    date_buttons = []
    for i in range(60):
        d = now - timedelta(days=i)
        date_buttons.append(KeyboardButton(text=d.strftime("%Y-%m-%d")))
    
    keyboard = []
    row = []
    for btn in date_buttons:
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([KeyboardButton(text="⬅️ Ortga"), KeyboardButton(text="🏠 Bosh sahifa")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# ================= ADMIN HISOBOT KEYBOARDS =================
