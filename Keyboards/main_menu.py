from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Asosiy menyu tugmalari (Toza va xatosiz format)
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=
        [
            KeyboardButton(text="➕ Vazifa qoʻshish"), 
            KeyboardButton(text="📋 Vazifalar roʻyxati")
        ],
        [
            KeyboardButton(text="👥 Xodimlar"),          
            KeyboardButton(text="🗑 Vazifani oʻchirish")
        ],
        [
            KeyboardButton(text="📊 Admin oylik"),       
            KeyboardButton(text="💰 Kassir oylik")       
        ],
        [
            KeyboardButton(text="🗄 Arxiv"),
            KeyboardButton(text="📑 Guruh report")
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
            KeyboardButton(text="Kuniga bir nechta marta")
        ]
    ],
    resize_keyboard=True
)

# Isbot turi tugmalari
proof_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Video xabar (Kruglyash)"),
            KeyboardButton(text="Rasm (Photo)")
        ]
    ],
    resize_keyboard=True
)

# Vazifani qaysi unvonga topshirish tugmalari
assign_role_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Kassir"), KeyboardButton(text="Sanitar")],
        [KeyboardButton(text="Manager"), KeyboardButton(text="Hamma xodimlarga")]
    ],
    resize_keyboard=True
)

# Kunlarni inline formatda tanlash (Boshqa kunlar uchun)
def get_inline_days_keyboard() -> InlineKeyboardMarkup:
    days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakirshanba"]
    inline_keyboard = []
    for day in days:
        inline_keyboard.append([InlineKeyboardButton(text=day, callback_data=f"day_{day}")])
    inline_keyboard.append([InlineKeyboardButton(text="✅ Tanlab bo'ldim (Done)", callback_data="days_done")])
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
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# ================== 🌟 YANGI USTOZ/BALL TUGMALARI ==================

# Ustozlar ro'yxatini chiqarish (Botdan foydalanmaydiganlar uchun)
def get_static_teachers_keyboard(teachers_db: dict) -> InlineKeyboardMarkup:
    inline_keyboard = []
    for t_id, t_info in teachers_db.items():
        btn_text = f"👨‍🏫 {t_info['name']} (IELTS: {t_info['ielts_score']})"
        inline_keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"viewstatict_{t_id}")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

# Ustozni tanlaganda chiqadigan variantlar
def get_static_teacher_options_keyboard(teacher_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ IELTS balini o'zgartirish", callback_data=f"editstaticscore_{teacher_id}")],
            [InlineKeyboardButton(text="⬅️ Ro'yxatga qaytish", callback_data="back_to_static_teachers")]
        ]
    )

# Yangi ballarni tanlash klaviaturasi
def get_static_ielts_scores_keyboard(teacher_id: int) -> InlineKeyboardMarkup:
    scores = ["6.5", "7.0", "7.5", "8.0", "8.5", "9.0"]
    inline_keyboard = []
    row = []
    for score in scores:
        row.append(InlineKeyboardButton(text=score, callback_data=f"setstaticscore_{score}_{teacher_id}"))
        if len(row) == 3:
            inline_keyboard.append(row)
            row = []
    inline_keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_static_teachers")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
