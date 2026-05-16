from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Asosiy menyu tugmalari
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Add Task"), 
            KeyboardButton(text="List of tasks")
        ] # Ikkalasi bitta qatorda
    ],
    resize_keyboard=True
)

# Task turini tanlash uchun yangi tugmalar (bitta qatorda yonma-yon)
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

# Kuniga necha marta bajarilishini so'rash tugmalari (Yangi qo'shildi)
frequency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Once"),
            KeyboardButton(text="Multiple times")
        ]
    ],
    resize_keyboard=True
)

# "OTHER" bosilganda chiqadigan maxsus Inline klaviatura funksiyasi (Yangi qo'shildi)
def get_inline_days_keyboard(selected_days: list = None) -> InlineKeyboardMarkup:
    if selected_days is None:
        selected_days = []
        
    # Hafta kunlari ro'yxati (kalit va ko'rinadigan matn)
    weeks = {
        "mon": "Dushanba", "tue": "Seshanba", "wed": "Chorshanba",
        "thu": "Payshanba", "fri": "Juma", "sat": "Shanba", "sun": "Yakshanba"
    }
    
    inline_keyboard = []
    
    # Har bir kunni aylanib chiqib, tugma hosil qilamiz
    for code, name in weeks.items():
        # Agar kun tanlangan bo'lsa, yoniga ✅ belgisini qo'shamiz
        text = f"✅ {name}" if code in selected_days else name
        # callback_data orqali bot orqa fonda qaysi kun bosilganini bilib oladi
        inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"day_{code}")])
        
    # Eng oxiriga "Done" (Tayyor) tugmasini qo'shamiz
    inline_keyboard.append([InlineKeyboardButton(text="Done ➡️", callback_data="days_done")])
    
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
