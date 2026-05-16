from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Asosiy menyu tugmalari
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Add Task"), 
            KeyboardButton(text="List of tasks")
        ]
    ],
    resize_keyboard=True
)

# Task turini tanlash uchun yangi tugmalar
task_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Continuously"),
            KeyboardButton(text="Daily")
        ]
    ],
    resize_keyboard=True
)

# Kunlarni tanlash tugmalari
days_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ODD"), KeyboardButton(text="EVEN")],
        [KeyboardButton(text="6 days a week"), KeyboardButton(text="OTHER")]
    ],
    resize_keyboard=True
)

# Kuniga necha marta bajarilishini so'rash tugmalari
frequency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Once"),
            KeyboardButton(text="Multiple times")
        ]
    ],
    resize_keyboard=True
)

# --- YANGI QO'SHILGAN KLAVIATURALAR ---

# Isbot turi tugmalari
proof_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Video message"),
            KeyboardButton(text="Photo")
        ]
    ],
    resize_keyboard=True
)

# Vazifani qaysi unvonga topshirish tugmalari
assign_role_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Admin"), KeyboardButton(text="Cashier")],
        [KeyboardButton(text="Sanitar"), KeyboardButton(text="Manager")]
    ],
    resize_keyboard=True
)

# "OTHER" bosilganda chiqadigan maxsus Inline klaviatura funksiyasi
def get_inline_days_keyboard(selected_days: list = None) -> InlineKeyboardMarkup:
    if selected_days is None:
        selected_days = []
        
    weeks = {
        "mon": "Dushanba", "tue": "Seshanba", "wed": "Chorshanba",
        "thu": "Payshanba", "fri": "Juma", "sat": "Shanba", "sun": "Yakshanba"
    }
    
    inline_keyboard = []
    
    for code, name in weeks.items():
        text = f"✅ {name}" if code in selected_days else name
        inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"day_{code}")])
        
    inline_keyboard.append([InlineKeyboardButton(text="Done ➡️", callback_data="days_done")])
    
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

# Admin uchun ruxsat berish va rollarni tanlash Inline klaviaturasi
def get_admin_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    roles = ["Admin", "Cashier", "Sanitar", "Manager"]
    inline_keyboard = []
    row = []
    
    for role in roles:
        row.append(InlineKeyboardButton(text=role, callback_data=f"approve_{role}_{user_id}"))
        if len(row) == 2:
            inline_keyboard.append(row)
            row = []
            
    inline_keyboard.append([InlineKeyboardButton(text="❌ Rad etish (Reject)", callback_data=f"reject_{user_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

# Xodimga boradigan inline 'Completed' tugmasi
def get_task_complete_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Completed", callback_data=f"completetask_{task_id}")]
        ]
    )
