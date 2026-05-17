from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Asosiy menyu tugmalari
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Vazifa qoʻshish"), 
            KeyboardButton(text="Vazifalar roʻyxati")
        ],
        [
            KeyboardButton(text="Xodimlar"),          
            KeyboardButton(text="Vazifani oʻchirish")
        ],
        [
            KeyboardButton(text="Admin oylik"),       # 🌟 YANGI TUGMA
            KeyboardButton(text="Kassir oylik")       # 🌟 YANGI TUGMA
        ],
        [
            KeyboardButton(text="Arxiv")               
        ]
    ],
    resize_keyboard=True
)

# Vazifa turini tanlash uchun tugmalar
task_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Muntazam (Doimiy)"),
            KeyboardButton(text="Kunlik (Bir martalik)")
        ]
    ],
    resize_keyboard=True
)

# Kunlarni tanlash tugmalari
days_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Toq kunlar"), KeyboardButton(text="Juft kunlar")],
        [KeyboardButton(text="Haftada 6 kun"), KeyboardButton(text="Boshqa kunlar")]
    ],
    resize_keyboard=True
)

# Kuniga necha marta bajarilishini so'rash tugmalari
frequency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Kuniga 1 marta"),
            KeyboardButton(text="Bir necha marta")
        ]
    ],
    resize_keyboard=True
)

# Isbot turi tugmalari
proof_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Dumaloq video"),
            KeyboardButton(text="Rasm yuborish")
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
    inline_keyboard.append([InlineKeyboardButton(text="Tayyor ➡️", callback_data="days_done")])
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
    inline_keyboard.append([InlineKeyboardButton(text="❌ Tizimga kirishni rad etish", callback_data=f"reject_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

# Xodimga boradigan inline 'Bajarildi' tugmasi
def get_task_complete_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Bajarildi ✅", callback_data=f"completetask_{task_id}")]
        ]
    )

# Vazifalarni o'chirish uchun dinamik klaviatura
def get_remove_tasks_keyboard(tasks_list: list) -> InlineKeyboardMarkup:
    inline_keyboard = []
    for task in tasks_list:
        btn_text = f"❌ {task['task_name']} ({task['assigned_to_name']})"
        inline_keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"removetask_{task['id']}")])
    inline_keyboard.append([InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="remove_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
