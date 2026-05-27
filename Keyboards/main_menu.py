from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta, timezone


# ================= ASOSIY MENU =================
def get_main_menu(role: str):
    role = str(role).strip()
    if role in ["Owner", "Manager"]:
        keyboard = [
            [KeyboardButton(text="➕ Add Tasks"), KeyboardButton(text="📋 Tasks Lists"), KeyboardButton(text="🗑 Delete Task")],
            [KeyboardButton(text="👥 Staff"), KeyboardButton(text="👨🏻‍🏫 Teacher/Score"), KeyboardButton(text="🎯 Monitoring")],
            [KeyboardButton(text="📊 Admin Salary"), KeyboardButton(text="💰 Cashier Salary"), KeyboardButton(text="📸 Proofs")],
            [KeyboardButton(text="🗄 Archive"), KeyboardButton(text="📑 GR Reports"), KeyboardButton(text="⚙️ Settings")]
        ]
    elif role == "Admin":
        keyboard = [
            [KeyboardButton(text="📍 Arrived"), KeyboardButton(text="📋 Tasks Lists")],
            [KeyboardButton(text="📊 Admin Salary"), KeyboardButton(text="📑 GR Reports")]   
        ]
    elif role == "Kassir":
        keyboard = [
            [KeyboardButton(text="📍 Arrived"), KeyboardButton(text="📋 Vazifalar roʻyxati")],
            [KeyboardButton(text="💰 Cashier Salary")]
        ]
    elif role == "Sanitar":
        keyboard = [
            [KeyboardButton(text="📍 Arrived"), KeyboardButton(text="📋 Tasks Lists")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="📍 Arrived"), KeyboardButton(text="📋 Tasks Lists")]  
        ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ================= ORTGA / BOSH SAHIFA =================
def get_back_home_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Back"), KeyboardButton(text="🏠 Home")]],
        resize_keyboard=True
    )


# ================= SOZLAMALAR UCHUN KEYBOARDS =================
def get_settings_role_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Admin"), KeyboardButton(text="Cashier")],
            [KeyboardButton(text="Sanitar"), KeyboardButton(text="Manager")],
            [KeyboardButton(text="🏠 Home"), KeyboardButton(text="⬅️ Back")]
        ],
        resize_keyboard=True
    )


def get_work_time_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1st shift (08:00 - 14:00)"), KeyboardButton(text="2nd shift (14:00 - 21:00)")],
            [KeyboardButton(text="3rd shift (08:00 - 17:00)"), KeyboardButton(text="✍️ Other")],
            [KeyboardButton(text="🏠 Home"), KeyboardButton(text="⬅️ Back")]
        ],
        resize_keyboard=True
    )


# ================= VAZIFA YARATISH KEYBOARDS =================
task_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔁 Recurring"), KeyboardButton(text="📅 Single Task")],
        [KeyboardButton(text="🏠 Home"), KeyboardButton(text="⬅️ Back")]
    ],
    resize_keyboard=True
)

assign_role_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Admin"), KeyboardButton(text="Manager")],
        [KeyboardButton(text="Cashier"), KeyboardButton(text="Sanitar")],
        [KeyboardButton(text="🏠 Home"), KeyboardButton(text="⬅️ Back")]
    ],
    resize_keyboard=True
)

days_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ODD"), KeyboardButton(text="EVEN")],
        [KeyboardButton(text="📆 6x Week"), KeyboardButton(text="➕ Other")],
        [KeyboardButton(text="🏠 Home"), KeyboardButton(text="⬅️ Back")]
    ],
    resize_keyboard=True
)

frequency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Once a Day"), KeyboardButton(text="🔂 Multi-use")],
        [KeyboardButton(text="🏠 Home"), KeyboardButton(text="⬅️ Back")]
    ],
    resize_keyboard=True
)

proof_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎥 Video Note"), KeyboardButton(text="📸 Pic")],
        [KeyboardButton(text="📝 Text")],
        [KeyboardButton(text="🏠 Home"), KeyboardButton(text="⬅️ Back")]
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
    inline_keyboard.append([InlineKeyboardButton(text="✅ Tanlab boʻldim", callback_data="days_done")])
    inline_keyboard.append([InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_task_creation")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def get_admin_approval_keyboard(user_id: int):
    roles = ["Admin", "Cashier", "Sanitar", "Manager"]
    inline_keyboard = []
    row = []
    for role in roles:
        row.append(InlineKeyboardButton(text=role, callback_data=f"approve_{role}_{user_id}"))
        if len(row) == 2:
            inline_keyboard.append(row)
            row = []
    if row:
        inline_keyboard.append(row)
    inline_keyboard.append([InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def get_task_complete_keyboard(task_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Done", callback_data=f"completetask_{task_id}")]]
    )


def get_remove_tasks_keyboard(tasks_list: list):
    inline_keyboard = []
    for task in tasks_list:
        assigned_name = task.get("assigned_to_name", "Noma'lum")
        btn_text = f"❌ {task['task_name']} ({assigned_name})"
        inline_keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"removetask_{task['id']}")])
    inline_keyboard.append([InlineKeyboardButton(text="❌ Cancel", callback_data="remove_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# ================= ISBOTLAR KEYBOARDS =================
def get_proof_role_keyboard():
    keyboard = [
        [KeyboardButton(text="Admin"), KeyboardButton(text="Cashier")],
        [KeyboardButton(text="Sanitar"), KeyboardButton(text="Manager")],
        [KeyboardButton(text="All Staff"), KeyboardButton(text="🏠 Home")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_proof_date_keyboard():
    keyboard = [
        [KeyboardButton(text="📅 Today"), KeyboardButton(text="📆 Yesterday")],
        [KeyboardButton(text="📅 This Month"), KeyboardButton(text="📆 Last Month")],
        [KeyboardButton(text="✍️ Other")],
        [KeyboardButton(text="🏠 Home"), KeyboardButton(text="⬅️ Back")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ================= VAZIFALAR RO'YXATI KEYBOARDS =================
def get_tasks_simple_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Today")],
            [KeyboardButton(text="📆 Date")],
            [KeyboardButton(text="🏠 Home")]
        ],
        resize_keyboard=True
    )


def get_custom_date_keyboard_simple():
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
    
    keyboard.append([KeyboardButton(text="⬅️ Back"), KeyboardButton(text="🏠 Home")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
