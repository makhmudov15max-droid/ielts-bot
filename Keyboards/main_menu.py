from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Asosiy menyu tugmalari (Remove task qo'shildi)
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Task qo'shish"), 
            KeyboardButton(text="Takslar ro'yxati")
        ],
        [
            KeyboardButton(text="Task o'chirish")  # <-- YANGI TUGMA
        ]
    ],
    resize_keyboard=True
)

# Task turini tanlash uchun tugmalar
task_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Uzluksiz"),
            KeyboardButton(text="Bir martta")
        ]
    ],
    resize_keyboard=True
)

# Kunlarni tanlash tugmalari
days_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Toq"), KeyboardButton(text="Juft")],
        [KeyboardButton(text="Haftada 6"), KeyboardButton(text="Boshqa")]
    ],
    resize_keyboard=True
)

# Kuniga necha marta bajarilishini so'rash tugmalari
frequency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Bir martta"),
            KeyboardButton(text="Ko'p martta")
        ]
    ],
    resize_keyboard=True
)

# Isbot turi tugmalari
proof_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Video isbot"),
            KeyboardButton(text="Rasm isbot")
        ]
    ],
    resize_keyboard=True
)

# Vazifani qaysi unvonga topshirish tugmalari
assign_role_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Admin"), KeyboardButton(text="Kassir")],
        [KeyboardButton(text="Sanitar"), KeyboardButton(text="Manager")]
    ],
    resize_keyboard=True
)

# Hafta kunlarini bittalab tanlash uchun Inline klaviatura
def get_inline_days_keyboard(selected_days: list) -> InlineKeyboardMarkup:
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
    roles = ["Admin", "Kassir", "Sanitar", "Manager"]
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
            [InlineKeyboardButton(text="Bajarildi (Completed) ✅", callback_data=f"completetask_{task_id}")]
        ]
    )

# 🌟 YANGI QO'SHILGAN: Vazifalarni o'chirish uchun dinamik klaviatura
def get_remove_tasks_keyboard(tasks_list: list) -> InlineKeyboardMarkup:
    inline_keyboard = []
    for task in tasks_list:
        # Har bir tugmaga vazifa nomi va uning kimga biriktirilganini yozamiz
        btn_text = f"❌ {task['task_name']} ({task['assigned_to_name']})"
        inline_keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"removetask_{task['id']}")])
        
    inline_keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="remove_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
