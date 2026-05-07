# bot.py dagi taxminiy handlerlar strukturasi:

@dp.message_handler(text="Ustozlar")
async def teachers_menu(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Upgrade score", "Number of groups")
    keyboard.add("⬅️ Orqaga")
    await message.answer("Kerakli bo'limni tanlang:", reply_markup=keyboard)

@dp.message_handler(text="Number of groups")
async def choose_teacher_for_workload(message: types.Message):
    # Bu yerda jadvaldan ustozlar ro'yxatini inline tugma qilib chiqarasiz
    # Xuddi hozirgi Upgrade score dagi kabi
    await message.answer("Choose a teacher (Workload):", reply_markup=teachers_inline_markup())

# Ustoz tanlangandagi callback handler:
@dp.callback_query_handler(lambda c: c.data.startswith('workload_'))
async def process_workload(callback_query: types.CallbackQuery):
    teacher_name = callback_query.data.split('_')[1]
    await bot.answer_callback_query(callback_query.id)
    
    report = get_teacher_workload(teacher_name) # sheets.py dagi yangi funksiya
    await bot.send_message(callback_query.from_user.id, report, parse_mode="HTML")
