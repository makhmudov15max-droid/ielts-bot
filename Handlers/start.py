import asyncio
from datetime import datetime, timedelta, timezone
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
import config  
from Keyboards.main_menu import (
    main_menu_keyboard, 
    task_type_keyboard, 
    days_keyboard, 
    frequency_keyboard, 
    get_inline_days_keyboard,
    get_admin_approval_keyboard,
    proof_type_keyboard,
    assign_role_keyboard,
    get_task_complete_keyboard,
    get_remove_tasks_keyboard
)
from Handlers.states import TaskStates

start_router = Router()

try:
    ADMIN_ID = int(config.ADMIN_ID)
except ValueError:
    ADMIN_ID = 6500594896  

# Vaqtincha xotira bazasi (Rollar va Ismlarni saqlaydi)
USERS_ROLES = {
    ADMIN_ID: {"role": "Admin", "name": "Asosiy Administrator"}
}

# Vazifalarni saqlash bazasi
TASKS_DATABASE = []

@start_router.message(CommandStart())
async def command_start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_info = USERS_ROLES.get(user_id)
    
    if isinstance(user_info, dict) and user_info.get("role") == "rejected":
        await message.answer("Assalomu alaykum. Afsuski, tizimdan foydalanish soʻrovingiz administrator tomonidan rad etilgan.")
        return

    if user_id not in USERS_ROLES:
        await message.answer(
            text="Assalomu alaykum, Edu_Control tizimiga xush kelibsiz!\n"
                 "Tizim administratoriga ruxsat soʻrovi yuborildi. Iltimos, soʻrovingiz tasdiqlanishini kuting. Rahmat!"
        )
        
        full_name = message.from_user.full_name
        if message.from_user.username:
            raw_username = message.from_user.username
            user_profile_link = f"https://t.me/{raw_username}"
            username_text = f"@{raw_username} (<a href='{user_profile_link}'>Profilga oʻtish</a>)"
        else:
            username_text = f"Mavjud emas (<a href='tg://user?id={user_id}'>Profilga oʻtish</a>)"
        
        admin_text = (
            f"🔔 <b>Yangi foydalanuvchi ruxsat soʻramoqda!</b>\n\n"
            f"👤 <b>Ism va familiya:</b> {full_name}\n"
            f"🆔 <b>ID raqami:</b> <code>{user_id}</code>\n"
            f"🌐 <b>Telegram sahifasi:</b> {username_text}\n\n"
            f"Iltimos, ushbu foydalanuvchiga tegishli unvonni (rol) bering yoki soʻrovni rad eting 👇"
        )
        
        try:
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_text,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=get_admin_approval_keyboard(user_id)
            )
        except Exception as e:
            print(f"❌ Administratorga xabar yuborishda muammo yuzaga keldi: {e}")
        return

    if isinstance(user_info, dict) and user_info.get("name") is None:
        await message.answer("Iltimos, tizimda roʻyxatdan oʻtish uchun ism va familiyangizni kiriting:")
        await state.set_state(TaskStates.waiting_for_user_name)
        return

    saved_name = user_info.get("name", message.from_user.full_name)
    await message.answer(
        text=f"Assalomu alaykum, {saved_name}! Tizimga xush kelibsiz.\n"
             f"Quyidagi tugmalar orqali botni boshqarishingiz mumkin 👇",
        reply_markup=main_menu_keyboard
    )


# ================= CALLBACK HANDLERS (ADMIN APPROVAL) =================

@start_router.callback_query(F.data.startswith("approve_"))
async def admin_approve_callback(call: types.CallbackQuery, state: FSMContext):
    try:
        data_parts = call.data.split("_")
        role = data_parts[1]
        target_user_id = int(data_parts[2])
        
        USERS_ROLES[target_user_id] = {"role": role, "name": None}
        
        await call.message.edit_text(
            text=f"{call.message.text}\n\n✅ <b>Tasdiqlandi!</b> Foydalanuvchiga <b>{role}</b> unvoni muvaffaqiyatli berildi.",
            parse_mode="HTML"
        )
        
        user_text = f"Sizga administrator tomonidan \"{role}\" unvoni berildi. Iltimos, tizimdan foydalanish uchun ism va familiyangizni kiriting:"
        await call.bot.send_message(
            chat_id=target_user_id,
            text=user_text,
            reply_markup=types.ReplyKeyboardRemove()  
        )
            
    except Exception as e:
        print(f"❌ Tasdiqlash jarayonida xatolik: {e}")
    await call.answer()


@start_router.callback_query(F.data.startswith("reject_"))
async def admin_reject_callback(call: types.CallbackQuery):
    try:
        target_user_id = int(call.data.split("_")[1])
        USERS_ROLES[target_user_id] = {"role": "rejected", "name": None}
        
        await call.message.edit_text(
            text=f"{call.message.text}\n\n❌ <b>Soʻrov rad etildi!</b> Foydalanuvchi bloklandi.",
            parse_mode="HTML"
        )
        await call.bot.send_message(chat_id=target_user_id, text="Sizning botdan foydalanish soʻrovingiz administrator tomonidan rad etildi.")
    except Exception as e:
        print(f"❌ Rad etish jarayonida xatolik: {e}")
    await call.answer()


# ================= FOYDALANUVCHI ISMINI QABUL QILISH =================

@start_router.message(TaskStates.waiting_for_user_name)
async def get_user_real_name_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    input_text = message.text.strip()
    first_name = input_text.split()[0]
    
    if user_id in USERS_ROLES:
        USERS_ROLES[user_id]["name"] = input_text
        await message.answer(
            text=f"Hurmatli {first_name}, siz muvaffaqiyatli roʻyxatdan oʻtdingiz. Endi bot imkoniyatlaridan toʻliq foydalanishingiz mumkin.",
            reply_markup=main_menu_keyboard
        )
        await state.clear()
    else:
        await message.answer("Xatolik yuz berdi. Iltimos, /start buyrugʻini qayta bosing.")


# ================= TARTIBLANGAN VAZIFA YARATISH LOGIKASI =================

def check_user_access(user_id: int) -> bool:
    user_info = USERS_ROLES.get(user_id)
    if not user_info or not isinstance(user_info, dict): return False
    if user_info.get("role") in [None, "rejected"] or user_info.get("name") is None: return False
    return True

# 1-QADAM: Vazifa turini soʻrash
@start_router.message(F.text == "Vazifa qoʻshish")
async def add_task_handler(message: types.Message):
    if not check_user_access(message.from_user.id): return
    await message.answer(text="Qanday turdagi vazifa yaratmoqchisiz?", reply_markup=task_type_keyboard)

# 2-QADAM: Boʻlim (Unvon)ni soʻrash
@start_router.message(F.text.in_(["Muntazam (Doimiy)", "Kunlik (Bir martalik)"]))
async def task_type_selected_handler(message: types.Message, state: FSMContext):
    if not check_user_access(message.from_user.id): return
    await state.update_data(task_type=message.text)
    await message.answer(text="Ushbu vazifa qaysi boʻlim yoki unvon xodimiga tegishli?", reply_markup=assign_role_keyboard)
    await state.set_state(TaskStates.waiting_for_target_role)

# 3-QADAM: Unvonga qarab aniq roʻyxatdan oʻtgan xodimlarni chiqarish
@start_router.message(TaskStates.waiting_for_target_role, F.text.in_(["Admin", "Kassir", "Sanitar", "Menejer"]))
async def get_target_role_handler(message: types.Message, state: FSMContext):
    role_mapping = {"Admin": "Admin", "Kassir": "Cashier", "Sanitar": "Sanitar", "Menejer": "Manager"}
    selected_role_en = role_mapping.get(message.text)
    
    await state.update_data(target_role=selected_role_en)
    
    inline_kb = []
    found_users = False
    
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == selected_role_en and u_info.get("name"):
            found_users = True
            inline_kb.append([types.InlineKeyboardButton(text=u_info.get("name"), callback_data=f"assignuser_{u_id}")])
            
    if not found_users:
        await message.answer(text=f"⚠️ Diqqat! Tizimda hali tasdiqlangan va ismi kiritilgan '{message.text}' unvonidagi xodimlar mavjud emas!")
        return
        
    await message.answer(
        text=f"Aynan qaysi '{message.text}' xodimiga ushbu vazifani biriktirmoqchisiz? Quyidagilardan tanlang 👇", 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )
    await state.set_state(TaskStates.waiting_for_target_user)

# 4-QADAM: Xodim tanlangach - Vazifa nomini soʻrash
@start_router.callback_query(TaskStates.waiting_for_target_user, F.data.startswith("assignuser_"))
async def process_target_user_callback(call: types.CallbackQuery, state: FSMContext):
    target_user_id = int(call.data.split("_")[1])
    employee_name = USERS_ROLES.get(target_user_id, {}).get("name", "Noma'lum xodim")
    
    await state.update_data(assigned_to_id=target_user_id, assigned_to_name=employee_name)
    
    await call.message.delete()
    await call.message.answer(text="Iltimos, vazifa nomini kiriting:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(TaskStates.waiting_for_name)
    await call.answer()

# 5-QADAM: Vazifa nomi kiritilgach - Kunlarni soʻrash
@start_router.message(TaskStates.waiting_for_name)
async def get_task_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_name=message.text.strip())
    await message.answer(text="Vazifa haftaning qaysi kunlari foydalanuvchiga koʻrinsin?", reply_markup=days_keyboard)
    await state.set_state(TaskStates.waiting_for_days)

# 6-QADAM (A-variant): Standart kunlar tanlanganda - Chastotani soʻrash
@start_router.message(TaskStates.waiting_for_days, F.text.in_(["Toq kunlar", "Juft kunlar", "Haftada 6 kun"]))
async def get_task_days_handler(message: types.Message, state: FSMContext):
    day_mapping = {"Toq kunlar": "ODD", "Juft kunlar": "EVEN", "Haftada 6 kun": "6 days a week"}
    await state.update_data(task_days=day_mapping.get(message.text))
    await message.answer(text="Vazifa kuniga necha marta koʻrinishi kerak?", reply_markup=frequency_keyboard)
    await state.set_state(TaskStates.waiting_for_frequency)

# 6-QADAM (B-variant): Boshqa kunlar tanlanganda Inline tanlov chiqarish
@start_router.message(TaskStates.waiting_for_days, F.text == "Boshqa kunlar")
async def other_days_handler(message: types.Message, state: FSMContext):
    await state.update_data(selected_days=[])
    await message.answer(text="Iltimos, kerakli hafta kunlarini bittalab tanlang:", reply_markup=get_inline_days_keyboard([]))

@start_router.callback_query(TaskStates.waiting_for_days, F.data.startswith("day_"))
async def toggle_day_callback(call: types.CallbackQuery, state: FSMContext):
    day_code = call.data.split("_")[1]
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", [])
    if day_code in selected_days: selected_days.remove(day_code)
    else: selected_days.append(day_code)
    await state.update_data(selected_days=selected_days)
    await call.message.edit_reply_markup(reply_markup=get_inline_days_keyboard(selected_days))
    await call.answer()

@start_router.callback_query(TaskStates.waiting_for_days, F.data == "days_done")
async def days_done_callback(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", [])
    if not selected_days:
        await call.answer(text="Iltimos, kamida bitta kunni tanlang!", show_alert=True)
        return
    await state.update_data(task_days=", ".join(selected_days))
    await call.message.delete()
    await call.message.answer(text="Vazifa kuniga necha marta koʻrinishi kerak?", reply_markup=frequency_keyboard)
    await state.set_state(TaskStates.waiting_for_frequency)
    await call.answer()

# 7-QADAM (1-variant): Kuniga 1 marta tanlanganda vaqt soʻrash
@start_router.message(TaskStates.waiting_for_frequency, F.text == "Kuniga 1 marta")
async def once_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Once")
    await message.answer(
        text="Vazifa xodimga qaysi vaqtda yuborilsin?\n\n<b>Format shabloni:</b> <code>11:33</code> koʻrinishida kiriting.", 
        parse_mode="HTML", 
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskStates.waiting_for_once_time)

@start_router.message(TaskStates.waiting_for_once_time)
async def get_once_time_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_times=message.text.strip())
    await message.answer(text="Ushbu vazifani yakunlash uchun qanday turdagi isbot talab etiladi?", reply_markup=proof_type_keyboard)
    await state.set_state(TaskStates.waiting_for_proof_type)

# 7-QADAM (2-variant): Bir necha marta tanlanganda vaqtlarni soʻrash
@start_router.message(TaskStates.waiting_for_frequency, F.text == "Bir necha marta")
async def multiple_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Multiple times")
    await message.answer(
        text="Vazifa xodimga qaysi vaqtlarda yuborilsin?\n\n<b>Format shabloni:</b> Vaqtlarni vaqt oraligʻi yoki vergul bilan ajratib yozing.\nMasalan: <code>08:00, 14:00, 18:00</code> koʻrinishida.", 
        parse_mode="HTML", 
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskStates.waiting_for_multiple_times)

@start_router.message(TaskStates.waiting_for_multiple_times)
async def get_multiple_times_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_times=message.text.strip())
    await message.answer(text="Ushbu vazifani yakunlash uchun qanday turdagi isbot talab etiladi?", reply_markup=proof_type_keyboard)
    await state.set_state(TaskStates.waiting_for_proof_type)

# 8-QADAM: Isbot turi tanlanganda - Saqlash va yakunlash
@start_router.message(TaskStates.waiting_for_proof_type, F.text.in_(["Dumaloq video", "Rasm yuborish"]))
async def finalize_task_creation_handler(message: types.Message, state: FSMContext):
    proof_mapping = {"Dumaloq video": "Video message", "Rasm yuborish": "Photo"}
    proof_type_en = proof_mapping.get(message.text)
    
    user_data = await state.get_data()
    
    task_id = len(TASKS_DATABASE) + 1
    raw_times = user_data.get("task_times", "")
    times_list = [t.strip() for t in raw_times.split(",") if t.strip()]
    
    new_task = {
        "id": task_id,
        "task_name": user_data.get("task_name"),
        "task_days": user_data.get("task_days"), 
        "task_frequency": user_data.get("task_frequency"),
        "task_times": times_list,
        "proof_type": proof_type_en,
        "assigned_to_id": user_data.get("assigned_to_id"),
        "assigned_to_name": user_data.get("assigned_to_name"),
        "sent_today_times": [] 
    }
    
    TASKS_DATABASE.append(new_task)
    
    report_text = (
        f"🎉 <b>Yangi vazifa muvaffaqiyatli yaratildi!</b>\n\n"
        f"📌 <b>Nomi:</b> {new_task['task_name']}\n"
        f"📅 <b>Amal qilish kunlari:</b> {new_task['task_days']}\n"
        f"🔢 <b>Takrorlanish chastotasi:</b> {new_task['task_frequency']}\n"
        f"⏰ <b>Belgilangan vaqt(lar)i:</b> {', '.join(new_task['task_times'])}\n"
        f"📸 <b>Talab etiladigan isbot:</b> {new_task['proof_type']}\n"
        f"👤 <b>Masʻul xodim:</b> {new_task['assigned_to_name']}"
    )
    await message.answer(text=report_text, parse_mode="HTML")
    await message.answer(text="Asosiy menyuga qaytdingiz.", reply_markup=main_menu_keyboard)
    
    # Masʻul xodimga shaxsiy bildirishnoma yuborish
    try:
        await message.bot.send_message(
            chat_id=new_task["assigned_to_id"],
            text=f"🔔 <b>Sizga yangi vazifa yuklatildi!</b>\n\n"
                 f"📌 <b>Vazifa nomi:</b> {new_task['task_name']}\n"
                 f"⏰ <b>Belgilangan vaqt(lar)i:</b> {', '.join(new_task['task_times'])}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"❌ Xodimga bildirishnoma yuborishda xatolik: {e}")
        
    await state.clear()


# ================= VAZIFALAR ROʻYXATINI KOʻRISH =================

@start_router.message(F.text == "Vazifalar roʻyxati")
async def list_of_tasks_handler(message: types.Message):
    if not check_user_access(message.from_user.id): return
    if not TASKS_DATABASE:
        await message.answer(text="📭 Hozircha tizimda hech qanday faol vazifalar va hisobotlar mavjud emas.")
        return
        
    response_text = "📋 <b>Tizimdagi joriy faol vazifalar roʻyxati:</b>\n\n"
    for idx, task in enumerate(TASKS_DATABASE, 1):
        response_text += (
            f"{idx}. <b>{task['task_name']}</b>\n"
            f"   👤 Masʻul: {task['assigned_to_name']}\n"
            f"   ⏰ Vaqti: {', '.join(task['task_times'])}\n"
            f"   📅 Kunlar: {task['task_days']}\n"
            f"   📸 Isbot: {task['proof_type']}\n\n"
        )
    await message.answer(text=response_text, parse_mode="HTML")


# ================= XODIM VAZIFANI BAJARISH BOSQICHI =================

@start_router.callback_query(F.data.startswith("completetask_"))
async def employee_complete_task_callback(call: types.CallbackQuery, state: FSMContext):
    task_id = int(call.data.split("_")[1])
    task = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    if not task:
        await call.answer(text="Kechirasiz, ushbu vazifa tizimdan topilmadi!", show_alert=True)
        return
        
    await state.update_data(active_task_id=task_id, proof_required=task["proof_type"])
    
    if task["proof_type"] == "Photo":
        await call.message.answer(text="Ushbu vazifani tasdiqlash uchun iltimos, <b>Rasm (Photo)</b> yuboring!", parse_mode="HTML")
    else:
        await call.message.answer(text="Ushbu vazifani tasdiqlash uchun iltimos, <b>Dumaloq video (Video message)</b> yuboring!", parse_mode="HTML")
        
    await state.set_state(TaskStates.waiting_for_task_proof)
    await call.answer()


# ================= XODIM ISBOTINI GURUHGA YUBORISH =================

@start_router.message(TaskStates.waiting_for_task_proof)
async def receive_task_proof_handler(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    proof_required = state_data.get("proof_required")
    task_id = state_data.get("active_task_id")
    
    task = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    
    # 🌟 Oʻzingizning guruh ID raqamingizni kiriting (-100 belgisi bilan boshlanishi shart!)
    GROUP_CHAT_ID = -1002233445566  
    
    if proof_required == "Photo" and message.photo:
        await message.answer(text="Vazifa muvaffaqiyatli topshirildi va hisobot guruhga yuborildi.", reply_markup=main_menu_keyboard)
        if task:
            group_text = (
                f"✅ <b>VAZIFA BAJARILDI!</b>\n\n"
                f"📌 <b>Vazifa nomi:</b> {task['task_name']}\n"
                f"👤 <b>Masʻul xodim:</b> {task['assigned_to_name']}\n"
                f"📸 <b>Isbot turi:</b> Rasm (Photo)\n"
                f"⏰ <b>Topshirilgan vaqt:</b> {datetime.now(timezone(timedelta(hours=5))).strftime('%H:%M')}"
            )
            await message.bot.send_message(chat_id=GROUP_CHAT_ID, text=group_text, parse_mode="HTML")
            await message.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=message.photo[-1].file_id)
        await state.clear()
        
    elif proof_required == "Video message" and message.video_note:
        await message.answer(text="Vazifa muvoccofiyatli topshirildi va hisobot guruhga yuborildi.", reply_markup=main_menu_keyboard)
        if task:
            group_text = (
                f"✅ <b>VAZIFA BAJARILDI!</b>\n\n"
                f"📌 <b>Vazifa nomi:</b> {task['task_name']}\n"
                f"👤 <b>Masʻul xodim:</b> {task['assigned_to_name']}\n"
                f"📸 <b>Isbot turi:</b> Dumaloq video (Video message)\n"
                f"⏰ <b>Topshirilgan vaqt:</b> {datetime.now(timezone(timedelta(hours=5))).strftime('%H:%M')}"
            )
            await message.bot.send_message(chat_id=GROUP_CHAT_ID, text=group_text, parse_mode="HTML")
            await message.bot.send_video_note(chat_id=GROUP_CHAT_ID, video_note=message.video_note.file_id)
        await state.clear()
        
    else:
        if proof_required == "Photo":
            await message.answer(text="⚠️ Notoʻgʻri format! Iltimos, ushbu vazifa uchun faqat <b>Rasm (Photo)</b> yuboring.", parse_mode="HTML")
        else:
            await message.answer(text="⚠️ Notoʻgʻri format! Iltimos, ushbu vazifa uchun faqat <b>Dumaloq video (Video message)</b> yuboring.", parse_mode="HTML")


# ================= VAZIFANI OʻCHIRISH LOGIKASI =================

@start_router.message(F.text == "Vazifani oʻchirish")
async def remove_task_menu_handler(message: types.Message):
    if not check_user_access(message.from_user.id): return
    
    if not TASKS_DATABASE:
        await message.answer(text="📭 Hozircha tizimda hech qanday faol vazifalar mavjud emas.")
        return
        
    await message.answer(
        text="🗑 <b>Oʻchirmoqchi boʻlgan vazifangizni tanlang:</b>\n<i>(Tugma bosilishi bilan ushbu vazifa bazadan butunlay oʻchiriladi!)</i>",
        parse_mode="HTML",
        reply_markup=get_remove_tasks_keyboard(TASKS_DATABASE)
    )

@start_router.callback_query(F.data.startswith("removetask_"))
async def process_remove_task_callback(call: types.CallbackQuery):
    task_id = int(call.data.split("_")[1])
    
    global TASKS_DATABASE
    task_to_remove = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    
    if task_to_remove:
        TASKS_DATABASE = [t for t in TASKS_DATABASE if t["id"] != task_id]
        
        await call.message.edit_text(
            text=f"🗑 <b>Vazifa muvaffaqiyatli oʻchirilildi!</b>\n\n📌 <b>Nomi:</b> {task_to_remove['task_name']}\n👤 <b>Masʻul boʻlgan xodim:</b> {task_to_remove['assigned_to_name']}",
            parse_mode="HTML"
        )
    else:
        await call.answer(text="⚠️ Bu vazifa allaqachon oʻchirilgan yoki tizimda mavjud emas!", show_alert=True)
        
    await call.answer()

@start_router.callback_query(F.data == "remove_cancel")
async def cancel_remove_callback(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer(text="Oʻchirish jarayoni bekor qilindi.", reply_markup=main_menu_keyboard)
    await call.answer()


# ================= TAYMER (UZBEKISTAN TIMEZONE) =================

async def auto_task_scheduler(bot):
    last_checked_minute = ""
    tashkent_tz = timezone(timedelta(hours=5))
    
    while True:
        try:
            now = datetime.now(timezone.utc).astimezone(tashkent_tz)
            current_time_str = now.strftime("%H:%M")
            
            current_day_name = now.strftime("%a").strip().lower() 
            day_of_month = now.day
            
            if current_time_str == "00:00":
                for task in TASKS_DATABASE:
                    task["sent_today_times"] = []
            
            if current_time_str != last_checked_minute:
                
                for task in TASKS_DATABASE:
                    if current_time_str in task["task_times"] and current_time_str not in task["sent_today_times"]:
                        
                        day_match = False
                        task_days = str(task["task_days"]).strip()
                        
                        if task_days == "ODD" and day_of_month % 2 != 0:
                            day_match = True
                        elif task_days == "EVEN" and day_of_month % 2 == 0:
                            day_match = True
                        elif task_days == "6 days a week" and current_day_name != "sun":
                            day_match = True
                        else:
                            clean_days = [d.strip().lower() for d in task_days.split(",") if d.strip()]
                            if current_day_name in clean_days:
                                day_match = True
                        
                        if day_match:
                            text_to_employee = f"📌 <b>{task['task_name']}</b>"
                            await bot.send_message(
                                chat_id=task["assigned_to_id"],
                                text=text_to_employee,
                                parse_mode="HTML",
                                reply_markup=get_task_complete_keyboard(task["id"])
                            )
                            task["sent_today_times"].append(current_time_str)
                            print(f"[TAYMER] Eslatma yuborildi: {task['task_name']}")
                
                last_checked_minute = current_time_str
                
        except Exception as e:
            print(f"⚠️ Taymer tizimida xatolik: {e}")
            
        await asyncio.sleep(5)
