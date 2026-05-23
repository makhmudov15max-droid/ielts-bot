import asyncio
from datetime import datetime, timedelta, timezone
import time
import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from Handlers.states import TaskStates
from Keyboards.main_menu import get_main_menu, get_admin_approval_keyboard, get_task_complete_keyboard
from utils.users_json import save_users, set_user_busy, set_user_free, is_user_busy, get_user_active_task
from utils.tasks_json import save_tasks, update_task_status, load_tasks, get_task_by_id
from utils.proofs_json import add_proof
from utils.access import check_user_access
from Handlers.tasks import tasks_router, init_tasks_handler
from Handlers.employees import employees_router, init_employees_handler
from Handlers.salaries import salaries_router, init_salaries_handler
from Handlers.callback_handlers import callback_router, init_callback_handler
from Handlers.teachers_sheets import sheets_router
from Handlers.group_report import report_router

start_router = Router()

# ================= GLOBAL O'ZGARUVCHILAR =================
USERS_ROLES = None
TASKS_DATABASE = None
ADMIN_ID = None


# ================= INIT FUNKSIYASI =================
def init_all_handlers(users_roles, tasks_database, admin_id):
    """Barcha handlerlar uchun global o'zgaruvchilarni o'rnatish"""
    global USERS_ROLES, TASKS_DATABASE, ADMIN_ID
    USERS_ROLES = users_roles
    TASKS_DATABASE = tasks_database
    ADMIN_ID = admin_id
    
    init_tasks_handler(USERS_ROLES, TASKS_DATABASE)
    init_employees_handler(USERS_ROLES, ADMIN_ID)
    init_salaries_handler(USERS_ROLES)
    init_callback_handler(USERS_ROLES, TASKS_DATABASE, ADMIN_ID)


# ================= /START COMMAND =================
@start_router.message(CommandStart())
async def command_start_handler(message: types.Message):
    user_id = str(message.from_user.id)
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
                reply_markup=get_admin_approval_keyboard(int(user_id))
            )
        except Exception as e:
            print(f"❌ Administratorga xabar yuborishda muammo: {e}")
        return

    saved_name = user_info.get("name", message.from_user.full_name)
    role = user_info.get("role")

    await message.answer(
        text=f"Assalomu alaykum, {saved_name}! "
             f"Tizimga xush kelibsiz.\n"
             f"Quyidagi tugmalar orqali botni boshqarishingiz mumkin 👇",

        reply_markup=get_main_menu(role)
    )


# ================= USER NAME HANDLER =================
@start_router.message(
    lambda msg:
    isinstance(
        USERS_ROLES.get(str(msg.from_user.id)),
        dict
    )
    and USERS_ROLES.get(
        str(msg.from_user.id)
    ).get("name") is None
)
async def get_user_real_name_handler(message: types.Message):
    user_id = str(message.from_user.id)
    input_text = message.text.strip()
    first_name = input_text.split()[0]
    
    USERS_ROLES[user_id]["name"] = input_text
    save_users(USERS_ROLES)

    await message.answer(
        text=f"Hurmatli {first_name}, siz muvaffaqiyatli roʻyxatdan oʻtdingiz. "
             f"Endi bot imkoniyatlaridan foydalanishingiz mumkin.",

        reply_markup=get_main_menu(
            USERS_ROLES[user_id]["role"]
        )
    )


# ================= VAZIFA YAKUNLASH (FINALIZE) =================
@start_router.message(TaskStates.waiting_for_proof_type, F.text.in_(["Dumaloq video", "Rasm yuborish", "✍️ Matn yuborish"]))
async def finalize_task_creation_handler(message: types.Message, state: FSMContext):
    proof_mapping = {
        "Dumaloq video": "Video message", 
        "Rasm yuborish": "Photo",
        "✍️ Matn yuborish": "Text"
    }
    
    user_data = await state.get_data()
    task_id = len(TASKS_DATABASE) + 1
    
    is_daily = user_data.get("task_type") == "Kunlik (Bir martalik)"
    raw_times = user_data.get("task_times", "")
    times_list = [t.strip() for t in raw_times.split(",") if t.strip()] if not is_daily else []
    
    new_task = {
        "id": task_id,
        "task_type": user_data.get("task_type"),
        "task_name": user_data.get("task_name"),
        "task_description": user_data.get("task_description", "Mavjud emas"),
        "task_days": user_data.get("task_days", "Kunlik vazifa"), 
        "task_frequency": user_data.get("task_frequency", "Bir martalik"),
        "task_times": times_list,
        "proof_type": proof_mapping.get(message.text),
        "assigned_to_id": user_data.get("assigned_to_id"),
        "assigned_to_name": user_data.get("assigned_to_name"),
        "sent_today_times": [],
        "status": "pending",
        "completed_at": None,
        "completed_by": None
    }
    
    TASKS_DATABASE.append(new_task)
    save_tasks(TASKS_DATABASE)
    
    report_text = (
        f"🎉 <b>Yangi vazifa muvaffaqiyatli yaratildi!</b>\n\n"
        f"📋 <b>Turi:</b> {new_task['task_type']}\n"
        f"📌 <b>Nomi:</b> {new_task['task_name']}\n"
    )
    if is_daily:
        report_text += f"📝 <b>Izoh:</b> {new_task['task_description']}\n"
    else:
        report_text += (
            f"📅 <b>Amal qilish kunlari:</b> {new_task['task_days']}\n"
            f"🔢 <b>Takrorlanish chastotasi:</b> {new_task['task_frequency']}\n"
            f"⏰ <b>Belgilangan vaqt(lar)i:</b> {', '.join(new_task['task_times'])}\n"
        )
    report_text += (
        f"📸 <b>Talab etiladigan isbot:</b> {message.text}\n"
        f"👤 <b>Masʻul xodim:</b> {new_task['assigned_to_name']}\n"
        f"📊 <b>Holat:</b> ⏳ Kutilmoqda"
    )
    
    await message.answer(text=report_text, parse_mode="HTML")

    role = USERS_ROLES[str(message.from_user.id)]["role"]
    await message.answer(text="Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
    
    try:
        if is_daily:
            employee_text = (
                f"🔔 <b>Sizga yangi kunlik vazifa yuklatildi!</b>\n\n"
                f"📌 <b>Vazifa nomi:</b> {new_task['task_name']}\n"
                f"📝 <b>Izoh (Admin eslatmasi):</b> {new_task['task_description']}\n\n"
                f"Vazifani bajarib, quyidagi tugma orqali hisobot (isbot) yuboring 👇"
            )
            await message.bot.send_message(
                chat_id=new_task["assigned_to_id"],
                text=employee_text,
                parse_mode="HTML",
                reply_markup=get_task_complete_keyboard(new_task["id"])
            )
        else:
            await message.bot.send_message(
                chat_id=new_task["assigned_to_id"],
                text=f"🔔 <b>Sizga yangi muntazam vazifa yuklatildi!</b>\n\n"
                     f"📌 <b>Vazifa nomi:</b> {new_task['task_name']}\n"
                     f"⏰ <b>Belgilangan vaqt(lar)i:</b> {', '.join(new_task['task_times'])}",
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Xodimga bildirishnoma yuborishda xatolik: {e}")
        
    await state.clear()


# ================= ISBOT QABUL QILISH =================
@start_router.message(TaskStates.waiting_for_task_proof)
async def receive_task_proof_handler(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    proof_required = state_data.get("proof_required")
    task_id = state_data.get("active_task_id")
    
    global TASKS_DATABASE
    task = get_task_by_id(task_id) if task_id else None
    GROUP_CHAT_ID = -5226036627  
    user_id = str(message.from_user.id)
    
    # Foydalanuvchini band qilish
    set_user_busy(user_id, task_id)
    
    # ========== MATN TEKSHIRUVI ==========
    if proof_required == "Text" and message.text and not message.photo and not message.video_note:
        role = USERS_ROLES[user_id]["role"]
        
        proof = add_proof(
            user_id=message.from_user.id,
            user_name=USERS_ROLES[user_id].get("name", "Noma'lum"),
            task_id=task["id"] if task else 0,
            task_name=task["task_name"] if task else "Noma'lum",
            task_description=task.get("task_description", "") if task else "",
            proof_type="Text",
            file_id=None,
            group_chat_id=GROUP_CHAT_ID,
            text_content=message.text
        )
        
        if task:
            update_task_status(task_id, "completed", user_id)
            TASKS_DATABASE = load_tasks()
        
        set_user_free(user_id)
        
        await message.answer(
            text="✅ Vazifa muvaffaqiyatli topshirildi va hisobot guruhga yuborildi.",
            reply_markup=get_main_menu(role)
        )
        
        if task:
            group_text = (
                f"✅ <b>VAZIFA BAJARILDI!</b>\n\n"
                f"📋 <b>Turi:</b> {task['task_type']}\n"
                f"📌 <b>Vazifa nomi:</b> {task['task_name']}\n"
                f"👤 <b>Masʻul xodim:</b> {task['assigned_to_name']}\n"
                f"✍️ <b>Isbot turi:</b> Matn\n"
                f"📝 <b>Javob:</b> {message.text}\n"
                f"⏰ <b>Topshirilgan vaqt:</b> {datetime.now(timezone(timedelta(hours=5))).strftime('%H:%M')}"
            )
            await message.bot.send_message(chat_id=GROUP_CHAT_ID, text=group_text, parse_mode="HTML")
            
            if task.get("task_type") == "Kunlik (Bir martalik)":
                TASKS_DATABASE = [t for t in TASKS_DATABASE if t["id"] != task_id]
                save_tasks(TASKS_DATABASE)
        
        await state.clear()
    
    # ========== RASM TEKSHIRUVI ==========
    elif proof_required == "Photo" and message.photo:
        role = USERS_ROLES[user_id]["role"]
        
        proof = add_proof(
            user_id=message.from_user.id,
            user_name=USERS_ROLES[user_id].get("name", "Noma'lum"),
            task_id=task["id"] if task else 0,
            task_name=task["task_name"] if task else "Noma'lum",
            task_description=task.get("task_description", "") if task else "",
            proof_type="Photo",
            file_id=message.photo[-1].file_id,
            group_chat_id=GROUP_CHAT_ID,
            text_content=None
        )
        
        if task:
            update_task_status(task_id, "completed", user_id)
            TASKS_DATABASE = load_tasks()
        
        set_user_free(user_id)
        
        await message.answer(
            text="✅ Vazifa muvaffaqiyatli topshirildi va hisobot guruhga yuborildi.",
            reply_markup=get_main_menu(role)
        )
        if task:
            group_text = (
                f"✅ <b>VAZIFA BAJARILDI!</b>\n\n"
                f"📋 <b>Turi:</b> {task['task_type']}\n"
                f"📌 <b>Vazifa nomi:</b> {task['task_name']}\n"
                f"👤 <b>Masʻul xodim:</b> {task['assigned_to_name']}\n"
                f"📸 <b>Isbot turi:</b> Rasm (Photo)\n"
                f"⏰ <b>Topshirilgan vaqt:</b> {datetime.now(timezone(timedelta(hours=5))).strftime('%H:%M')}"
            )
            await message.bot.send_message(chat_id=GROUP_CHAT_ID, text=group_text, parse_mode="HTML")
            await message.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=message.photo[-1].file_id)
            
            if task.get("task_type") == "Kunlik (Bir martalik)":
                TASKS_DATABASE = [t for t in TASKS_DATABASE if t["id"] != task_id]
                save_tasks(TASKS_DATABASE)
        await state.clear()
    
    # ========== VIDEO TEKSHIRUVI ==========
    elif proof_required == "Video message":
        
        if not message.video_note:
            await message.answer(
                text="❌ <b>Notoʻgʻri format!</b> Iltimos, dumaloq video (video message) yuboring.\n\n"
                     "📹 <b>Qanday yuborish kerak:</b>\n"
                     "1. Mikrofon tugmasini bosing va ushlab turing\n"
                     "2. <b>Video</b> tugmasiga o'ting\n"
                     "3. Yozish tugmasini bosing\n"
                     "4. Yozib bo'lgach, jo'natish tugmasini bosing",
                parse_mode="HTML"
            )
            return
        
        role = USERS_ROLES[user_id]["role"]
        
        proof = add_proof(
            user_id=message.from_user.id,
            user_name=USERS_ROLES[user_id].get("name", "Noma'lum"),
            task_id=task["id"] if task else 0,
            task_name=task["task_name"] if task else "Noma'lum",
            task_description=task.get("task_description", "") if task else "",
            proof_type="Video message",
            file_id=message.video_note.file_id,
            group_chat_id=GROUP_CHAT_ID,
            text_content=None
        )
        
        if task:
            update_task_status(task_id, "completed", user_id)
            TASKS_DATABASE = load_tasks()
        
        set_user_free(user_id)
        
        await message.answer(
            text="✅ Vazifa muvaffaqiyatli topshirildi va hisobot guruhga yuborildi.",
            reply_markup=get_main_menu(role)
        )
        
        if task:
            group_text = (
                f"✅ <b>VAZIFA BAJARILDI!</b>\n\n"
                f"📋 <b>Turi:</b> {task['task_type']}\n"
                f"📌 <b>Vazifa nomi:</b> {task['task_name']}\n"
                f"👤 <b>Masʻul xodim:</b> {task['assigned_to_name']}\n"
                f"📸 <b>Isbot turi:</b> Dumaloq video (Video message)\n"
                f"⏰ <b>Topshirilgan vaqt:</b> {datetime.now(timezone(timedelta(hours=5))).strftime('%H:%M')}"
            )
            await message.bot.send_message(chat_id=GROUP_CHAT_ID, text=group_text, parse_mode="HTML")
            await message.bot.send_video_note(chat_id=GROUP_CHAT_ID, video_note=message.video_note.file_id)
            
            if task.get("task_type") == "Kunlik (Bir martalik)":
                TASKS_DATABASE = [t for t in TASKS_DATABASE if t["id"] != task_id]
                save_tasks(TASKS_DATABASE)
        
        await state.clear()
    
    else:
        if proof_required == "Photo":
            await message.answer(
                text="⚠️ Notoʻgʻri format! Iltimos, ushbu vazifa uchun faqat <b>Rasm (Photo)</b> yuboring.", 
                parse_mode="HTML"
            )
        elif proof_required == "Text":
            await message.answer(
                text="⚠️ Notoʻgʻri format! Iltimos, ushbu vazifa uchun <b>Matn</b> yuboring.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                text="⚠️ Notoʻgʻri format! Iltimos, ushbu vazifa uchun faqat <b>Dumaloq video (Video message)</b> yuboring.\n\n"
                     "📹 <b>Qanday yuborish kerak:</b>\n"
                     "1. Mikrofon tugmasini bosing va ushlab turing\n"
                     "2. <b>Video</b> tugmasiga o'ting\n"
                     "3. Yozish tugmasini bosing\n"
                     "4. Yozib bo'lgach, jo'natish tugmasini bosing",
                parse_mode="HTML"
            )


# ================= TAYMER (AUTO TASK SCHEDULER) =================
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
                save_tasks(TASKS_DATABASE)
            
            if current_time_str != last_checked_minute:
                for task in TASKS_DATABASE:
                    if task.get("task_type") == "Kunlik (Bir martalik)":
                        continue
                    
                    if task.get("status") == "completed":
                        continue
                        
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
                            save_tasks(TASKS_DATABASE)
                last_checked_minute = current_time_str
        except Exception as e:
            print(f"Taymer tizimida xato: {e}")
        await asyncio.sleep(5)
