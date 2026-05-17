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
    get_task_complete_keyboard
)
from Handlers.states import TaskStates

start_router = Router()

try:
    ADMIN_ID = int(config.ADMIN_ID)
except ValueError:
    ADMIN_ID = 6500594896  

# Vaqtincha xotira bazasi (Rollar va Ismlarni saqlaydi)
USERS_ROLES = {
    ADMIN_ID: {"role": "Admin", "name": "Asosiy Admin"}
}

# Vazifalarni saqlash bazasi
TASKS_DATABASE = []

@start_router.message(CommandStart())
async def command_start_handler(message: types.Message):
    user_id = message.from_user.id
    user_info = USERS_ROLES.get(user_id)
    
    if isinstance(user_info, dict) and user_info.get("role") == "rejected":
        await message.answer("Assalomu alaykum. Siz botdan foydalana olmaysiz, so'rovingiz rad etilgan.")
        return

    if user_id not in USERS_ROLES:
        await message.answer(
            text="Hello, welcome to Edu_Control. Please wait until the bot administrator approves your request. Thank you!\n"
                 "Assalomu alaykum, Edu_Control’ga xush kelibsiz. Admin tasdiqlaguncha kuting. Rahmat!"
        )
        
        full_name = message.from_user.full_name
        if message.from_user.username:
            raw_username = message.from_user.username
            user_profile_link = f"https://t.me/{raw_username}"
            username_text = f"@{raw_username} (<a href='{user_profile_link}'>Profilga o'tish</a>)"
        else:
            username_text = f"Mavjud emas (<a href='tg://user?id={user_id}'>Profilga o'tish</a>)"
        
        admin_text = (
            f"🔔 <b>Yangi foydalanuvchi ruxsat so'ramoqda!</b>\n\n"
            f"👤 <b>Ism Familiya:</b> {full_name}\n"
            f"🆔 <b>ID Raqami:</b> <code>{user_id}</code>\n"
            f"🌐 <b>Username:</b> {username_text}\n\n"
            f"Iltimos, ushbu foydalanuvchiga unvon (role) bering yoki rad eting 👇"
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
            print(f"❌ Adminga xabar yuborishda muammo: {e}")
        return

    if isinstance(user_info, dict) and user_info.get("name") is None:
        await message.answer("Iltimos, ism va familiyangizni kiriting!")
        return

    saved_name = user_info.get("name", message.from_user.full_name)
    await message.answer(
        text=f"Salom, {saved_name}! Botimizga xush kelibsiz.\n"
             f"Quyidagi tugma orqali vazifalarni ko'rishingiz mumkin 👇",
        reply_markup=main_menu_keyboard
    )


# ================= CALLBACK HANDLERS (ADMIN APPROVAL) =================

@start_router.callback_query(F.data.startswith("approve_"))
async def admin_approve_callback(call: types.CallbackQuery):
    try:
        data_parts = call.data.split("_")
        role = data_parts[1]
        target_user_id = int(data_parts[2])
        
        USERS_ROLES[target_user_id] = {"role": role, "name": None}
        
        await call.message.edit_text(
            text=f"{call.message.text}\n\n✅ <b>Tasdiqlandi!</b> Foydalanuvchiga <b>{role}</b> unvoni berildi.",
            parse_mode="HTML"
        )
        
        user_text = f"Sizga Admin tomonidan \"{role}\" unvoni berildi. Iltimos ism, familiyangizni kiriting!"
        await call.bot.send_message(
            chat_id=target_user_id,
            text=user_text,
            reply_markup=types.ReplyKeyboardRemove()  
        )
            
    except Exception as e:
        print(f"❌ Approval callback xatosi: {e}")
    await call.answer()


@start_router.callback_query(F.data.startswith("reject_"))
async def admin_reject_callback(call: types.CallbackQuery):
    try:
        target_user_id = int(call.data.split("_")[1])
        USERS_ROLES[target_user_id] = {"role": "rejected", "name": None}
        
        await call.message.edit_text(
            text=f"{call.message.text}\n\n❌ <b>So'rov rad etildi!</b> Foydalanuvchi bloklandi.",
            parse_mode="HTML"
        )
        await call.bot.send_message(chat_id=target_user_id, text="Sizning botdan foydalanish so'rovingiz admin tomonidan rad etildi.")
    except Exception as e:
        print(f"❌ Reject callback xatosi: {e}")
    await call.answer()


# ================= FOYDALANUVCHI ISMINI QABUL QILISH =================

@start_router.message(lambda msg: isinstance(USERS_ROLES.get(msg.from_user.id), dict) and USERS_ROLES.get(msg.from_user.id).get("name") is None)
async def get_user_real_name_handler(message: types.Message):
    user_id = message.from_user.id
    input_text = message.text.strip()
    first_name = input_text.split()[0]
    
    USERS_ROLES[user_id]["name"] = input_text
    await message.answer(
        text=f"{first_name} siz ro'yxatdan o'tdingiz. Endi esa bot dan bemalol foydalansangiz bo'ladi",
        reply_markup=main_menu_keyboard
    )


# ================= TASK MANAGING LOGIC =================

def check_user_access(user_id: int) -> bool:
    user_info = USERS_ROLES.get(user_id)
    if not user_info or not isinstance(user_info, dict): return False
    if user_info.get("role") in [None, "rejected"] or user_info.get("name") is None: return False
    return True

@start_router.message(F.text == "Add Task")
async def add_task_handler(message: types.Message):
    if not check_user_access(message.from_user.id): return
    await message.answer(text="Qanday turdagi task yaratmoqchisiz?", reply_markup=task_type_keyboard)

@start_router.message(F.text == "Continuously")
async def continuously_handler(message: types.Message, state: FSMContext):
    if not check_user_access(message.from_user.id): return
    await message.answer(text="Vazifa nomini kiriting!", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(TaskStates.waiting_for_name)

@start_router.message(TaskStates.waiting_for_name)
async def get_task_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await message.answer(text="Vazifa qaysi kunlari ko'rinsin?", reply_markup=days_keyboard)
    await state.set_state(TaskStates.waiting_for_days)

@start_router.message(TaskStates.waiting_for_days, F.text.in_(["ODD", "EVEN", "6 days a week"]))
async def get_task_days_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_days=message.text)
    await message.answer(text="How many times per day? (Once or multiple times?)", reply_markup=frequency_keyboard)
    await state.set_state(TaskStates.waiting_for_frequency)

@start_router.message(TaskStates.waiting_for_days, F.text == "OTHER")
async def other_days_handler(message: types.Message, state: FSMContext):
    await state.update_data(selected_days=[])
    await message.answer(text="Hafta kunlarini tanlang:", reply_markup=get_inline_days_keyboard([]))

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
        await call.answer(text="Iltimos, kamida bitta kun tanlang!", show_alert=True)
        return
    await state.update_data(task_days=", ".join(selected_days))
    await call.message.delete()
    await call.message.answer(text="How many times per day? (Once or multiple times?)", reply_markup=frequency_keyboard)
    await state.set_state(TaskStates.waiting_for_frequency)
    await call.answer()


@start_router.message(TaskStates.waiting_for_frequency, F.text == "Once")
async def once_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Once")
    await message.answer(
        text="What time should the task appear for the user?\n\n<b>Shablon:</b> <code>08:00</code> ko'rinishida kiriting.", 
        parse_mode="HTML", 
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskStates.waiting_for_once_time)

@start_router.message(TaskStates.waiting_for_once_time)
async def get_once_time_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_times=message.text.strip())
    await message.answer(text="What type of proof is required?", reply_markup=proof_type_keyboard)
    await state.set_state(TaskStates.waiting_for_proof_type)

@start_router.message(TaskStates.waiting_for_frequency, F.text == "Multiple times")
async def multiple_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Multiple times")
    await message.answer(
        text="What time should the task appear for the user?\n\n<b>Shablon:</b> Vaqtlarni vergul bilan ajratib yozing.\nMasalan: <code>08:00, 14:00, 18:00</code>", 
        parse_mode="HTML", 
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskStates.waiting_for_multiple_times)

@start_router.message(TaskStates.waiting_for_multiple_times)
async def get_multiple_times_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_times=message.text.strip())
    await message.answer(text="What type of proof is required?", reply_markup=proof_type_keyboard)
    await state.set_state(TaskStates.waiting_for_proof_type)

@start_router.message(TaskStates.waiting_for_proof_type, F.text.in_(["Video message", "Photo"]))
async def get_proof_type_handler(message: types.Message, state: FSMContext):
    await state.update_data(proof_type=message.text)
    await message.answer(text="Who would you like to assign the task to?", reply_markup=assign_role_keyboard)
    await state.set_state(TaskStates.waiting_for_target_role)

@start_router.message(TaskStates.waiting_for_target_role, F.text.in_(["Admin", "Cashier", "Sanitar", "Manager"]))
async def get_target_role_handler(message: types.Message, state: FSMContext):
    selected_role = message.text
    await state.update_data(target_role=selected_role)
    
    inline_kb = []
    found_users = False
    
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == selected_role and u_info.get("name"):
            found_users = True
            inline_kb.append([types.InlineKeyboardButton(text=u_info.get("name"), callback_data=f"assignuser_{u_id}")])
            
    if not found_users:
        await message.answer(text=f"Xatolik: Tizimda hali tasdiqlangan va ismi bor '{selected_role}' xodimlari magenta emas!")
        return
        
    await message.answer(text=f"Aynan qaysi '{selected_role}' xodimiga biriktirmoqchisiz? Tanlang 👇", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb))
    await state.set_state(TaskStates.waiting_for_target_user)

@start_router.callback_query(TaskStates.waiting_for_target_user, F.data.startswith("assignuser_"))
async def finalize_task_assignment_handler(call: types.CallbackQuery, state: FSMContext):
    target_user_id = int(call.data.split("_")[1])
    user_data = await state.get_data()
    
    employee_name = USERS_ROLES.get(target_user_id, {}).get("name", "Noma'lum")
    task_id = len(TASKS_DATABASE) + 1
    
    raw_times = user_data.get("task_times", "")
    times_list = [t.strip() for t in raw_times.split(",") if t.strip()]
    
    new_task = {
        "id": task_id,
        "task_name": user_data.get("task_name"),
        "task_days": user_data.get("task_days"), 
        "task_frequency": user_data.get("task_frequency"),
        "task_times": times_list,
        "proof_type": user_data.get("proof_type"),
        "assigned_to_id": target_user_id,
        "assigned_to_name": employee_name,
        "sent_today_times": [] 
    }
    
    TASKS_DATABASE.append(new_task)
    
    report_text = (
        f"🎉 <b>Vazifa yaratildi!</b>\n\n"
        f"📌 <b>Nomi:</b> {new_task['task_name']}\n"
        f"📅 <b>Kunlar:</b> {new_task['task_days']}\n"
        f"🔢 <b>Chastotasi:</b> {new_task['task_frequency']}\n"
        f"⏰ <b>Vaqtlari:</b> {', '.join(new_task['task_times'])}\n"
        f"📸 <b>Talab etiladi:</b> {new_task['proof_type']}\n"
        f"👤 <b>Mas'ul xodim:</b> {new_task['assigned_to_name']}"
    )
    await call.message.edit_text(text=report_text, parse_mode="HTML")
    await call.message.answer(text="Asosiy menyuga qaytdingiz.", reply_markup=main_menu_keyboard)
    
    try:
        await call.bot.send_message(
            chat_id=target_user_id,
            text=f"🔔 <b>Sizga yangi vazifa yuklatildi!</b>\n\n"
                 f"📌 <b>Vazifa nomi:</b> {new_task['task_name']}\n"
                 f"⏰ <b>Vaqtlari:</b> {', '.join(new_task['task_times'])}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Xodimga sms yuborishda xato: {e}")
        
    await state.clear()
    await call.answer()


# ================= XODIM VAZIFANI BAJARISH BOSQICHI =================

@start_router.callback_query(F.data.startswith("completetask_"))
async def employee_complete_task_callback(call: types.CallbackQuery, state: FSMContext):
    task_id = int(call.data.split("_")[1])
    task = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    if not task:
        await call.answer(text="Vazifa topilmadi!", show_alert=True)
        return
        
    await state.update_data(active_task_id=task_id, proof_required=task["proof_type"])
    
    if task["proof_type"] == "Photo":
        await call.message.answer(text="Ushbu vazifani tasdiqlash uchun iltimos, <b>Rasm (Photo)</b> yuboring!", parse_mode="HTML")
    else:
        await call.message.answer(text="Ushbu vazifani tasdiqlash uchun iltimos, <b>Dumaloq video (Video message)</b> yuboring!", parse_mode="HTML")
        
    await state.set_state(TaskStates.waiting_for_task_proof)
    await call.answer()


# ================= UPDATE: XODIM ISBOTINI GURUHGA YUBORISH HUNDLERI =================

@start_router.message(TaskStates.waiting_for_task_proof)
async def receive_task_proof_handler(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    proof_required = state_data.get("proof_required")
    task_id = state_data.get("active_task_id")
    
    task = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    
    # 🌟 ID RAQAMNI SHU YERGA YOZING (Boshidagi minus -100 belgisi shart!)
    GROUP_CHAT_ID = -5226036627  # <-- O'zingizning guruhingiz ID raqamini shu yerga yozing
    
    if proof_required == "Photo" and message.photo:
        await message.answer(text="Task completed", reply_markup=main_menu_keyboard)
        if task:
            group_text = (
                f"✅ <b>VAZIFA BAJARILDI!</b>\n\n"
                f"📌 <b>Vazifa nomi:</b> {task['task_name']}\n"
                f"👤 <b>Xodim:</b> {task['assigned_to_name']}\n"
                f"📸 <b>Isbot turi:</b> Rasm (Photo)\n"
                f"⏰ <b>Topshirilgan vaqt:</b> {datetime.now(timezone(timedelta(hours=5))).strftime('%H:%M')}"
            )
            # Hisobot va rasmni Telegram guruhga jo'natamiz
            await message.bot.send_message(chat_id=GROUP_CHAT_ID, text=group_text, parse_mode="HTML")
            await message.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=message.photo[-1].file_id)
        await state.clear()
        
    elif proof_required == "Video message" and message.video_note:
        await message.answer(text="Task completed", reply_markup=main_menu_keyboard)
        if task:
            group_text = (
                f"✅ <b>VAZIFA BAJARILDI!</b>\n\n"
                f"📌 <b>Vazifa nomi:</b> {task['task_name']}\n"
                f"👤 <b>Xodim:</b> {task['assigned_to_name']}\n"
                f"📸 <b>Isbot turi:</b> Dumaloq video (Video message)\n"
                f"⏰ <b>Topshirilgan vaqt:</b> {datetime.now(timezone(timedelta(hours=5))).strftime('%H:%M')}"
            )
            # Hisobot va dumaloq videoni Telegram guruhga jo'natamiz
            await message.bot.send_message(chat_id=GROUP_CHAT_ID, text=group_text, parse_mode="HTML")
            await message.bot.send_video_note(chat_id=GROUP_CHAT_ID, video_note=message.video_note.file_id)
        await state.clear()
        
    else:
        if proof_required == "Photo":
            await message.answer(text="⚠️ Noto'g'ri isbot! Iltimos, faqat <b>Rasm (Photo)</b> yuboring.", parse_mode="HTML")
        else:
            await message.answer(text="⚠️ Noto'g'ri isbot! Iltimos, faqat <b>Dumaloq video (Video message)</b> yuboring.", parse_mode="HTML")


# ================= MUKAMMAL TAYMER (UZBEKISTAN TIMEZONE) =================

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
                            print(f"[TAYMER] Eslatma muvaffaqiyatli ketdi: {task['task_name']}")
                
                last_checked_minute = current_time_str
                
        except Exception as e:
            print(f"Taymer tizimida kutilmagan xato: {e}")
            
        await asyncio.sleep(5)
