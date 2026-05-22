import asyncio
from datetime import datetime, timedelta, timezone
import time
import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from Handlers.states import TaskStates
from Keyboards.main_menu import get_main_menu, get_admin_approval_keyboard, get_task_complete_keyboard
from utils.users_json import save_users
from utils.tasks_json import save_tasks
from utils.access import check_user_access
from Handlers.tasks import tasks_router, init_tasks_handler
from Handlers.employees import employees_router, init_employees_handler
from Handlers.salaries import salaries_router, init_salaries_handler
from Handlers.callback_handlers import callback_router, init_callback_handler
from Handlers.teachers_sheets import sheets_router
from Handlers.group_report import report_router

start_router = Router()

# Global o'zgaruvchilar
USERS_ROLES = None
TASKS_DATABASE = None
ADMIN_ID = None

# Yuborilgan videolarni saqlash (cheating oldini olish uchun)
# Format: {user_id: [file_unique_id1, file_unique_id2, ...]}
SENT_VIDEOS = {}


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


# ================= ISBOT QABUL QILISH (LOG BILAN) =================

@start_router.message(TaskStates.waiting_for_task_proof)
async def receive_task_proof_handler(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    proof_required = state_data.get("proof_required")
    task_id = state_data.get("active_task_id")
    
    global TASKS_DATABASE, SENT_VIDEOS
    task = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    GROUP_CHAT_ID = -5226036627  
    user_id = str(message.from_user.id)
    current_time = int(time.time())
    
    # ========== VIDEO KELGANDA LOGGA CHIQARISH (VAQTINCHALIK) ==========
    if message.video_note:
        logging.info("=" * 60)
        logging.info("📹 VIDEO NOTE QABUL QILINDI")
        logging.info(f"👤 User ID: {message.from_user.id}")
        logging.info(f"👤 Username: @{message.from_user.username}" if message.from_user.username else "👤 Username: None")
        logging.info(f"🆔 Message ID: {message.message_id}")
        logging.info(f"💬 Chat ID: {message.chat.id}")
        logging.info(f"📊 Chat Type: {message.chat.type}")
        logging.info(f"📅 Message Date: {message.date}")
        logging.info(f"⏰ Current Time: {datetime.fromtimestamp(current_time)}")
        
        # Forward atributlarini tekshirish
        forward_from = getattr(message, 'forward_from', None)
        forward_from_chat = getattr(message, 'forward_from_chat', None)
        forward_date = getattr(message, 'forward_date', None)
        forward_origin = getattr(message, 'forward_origin', None)
        
        logging.info(f"🔄 forward_from: {forward_from}")
        logging.info(f"🔄 forward_from_chat: {forward_from_chat}")
        logging.info(f"🔄 forward_date: {forward_date}")
        logging.info(f"🔄 forward_origin: {forward_origin}")
        
        # Video ma'lumotlari
        if message.video_note:
            logging.info(f"🎬 Video file_unique_id: {message.video_note.file_unique_id}")
            logging.info(f"🎬 Video file_id: {message.video_note.file_id[:50]}...")
            logging.info(f"🎬 Video duration: {message.video_note.duration} sekund")
        
        logging.info("=" * 60)
    
    # ========== RASM TEKSHIRUVI ==========
    if proof_required == "Photo" and message.photo:
        role = USERS_ROLES[user_id]["role"]
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
    
    # ========== DUMALOQ VIDEO TEKSHIRUVI ==========
    elif proof_required == "Video message":
        
        # 1. VIDEO FORMATNI TEKSHIRISH
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
        
        # 2. FORWARD TEKSHIRUVI (barcha usullar)
        is_forwarded = False
        forward_from_text = ""
        
        if hasattr(message, 'forward_from') and message.forward_from:
            is_forwarded = True
            forward_from_text = f"user: {message.forward_from.id}"
        elif hasattr(message, 'forward_from_chat') and message.forward_from_chat:
            is_forwarded = True
            forward_from_text = f"chat: {message.forward_from_chat.id}"
        elif hasattr(message, 'forward_date') and message.forward_date:
            is_forwarded = True
            forward_from_text = f"date: {message.forward_date}"
        elif hasattr(message, 'forward_origin') and message.forward_origin:
            is_forwarded = True
            forward_from_text = "origin mavjud"
        
        if is_forwarded:
            logging.info(f"❌ FORWARD ANIQLANDI: {forward_from_text}")
            await message.answer(
                text="❌ <b>Kechirasiz!</b> Forward qilingan video qabul qilinmaydi.\n\n"
                     f"📋 Aniqlangan: {forward_from_text}\n\n"
                     "Iltimos, <b>hozir, real vaqtda</b> yangi video yozib yuboring.\n\n"
                     "📹 <b>Qanday yuborish kerak:</b>\n"
                     "1. Mikrofon tugmasini bosing va ushlab turing\n"
                     "2. <b>Video</b> tugmasiga o'ting\n"
                     "3. Yozish tugmasini bosing\n"
                     "4. Yozib bo'lgach, jo'natish tugmasini bosing",
                parse_mode="HTML"
            )
            return
        
        # 3. FAQAT SHAXSIY CHAT TEKSHIRUVI
        if message.chat.type != "private":
            logging.info(f"❌ CHAT TYPE PRIVATE EMAS: {message.chat.type}")
            await message.answer(
                text="❌ <b>Kechirasiz!</b> Video faqat bot bilan shaxsiy chatda yozilishi kerak.\n\n"
                     "Iltimos, bot bilan shaxsiy chatda yangi video yozib yuboring.",
                parse_mode="HTML"
            )
            return
        
        # 4. VIDEO YOSHI TEKSHIRUVI (real vaqtda yozilgan bo'lishi kerak)
        message_time = message.date.timestamp() if hasattr(message, 'date') else current_time
        video_age = current_time - message_time
        
        if video_age > 10:
            logging.info(f"❌ VIDEO ESKI: {video_age:.0f} sekund")
            await message.answer(
                text=f"❌ <b>Kechirasiz!</b> Video {int(video_age)} sekund oldin yozilgan.\n"
                     "Bu saved message dan olingan bo'lishi mumkin.\n\n"
                     "Iltimos, <b>hozir, real vaqtda</b> yangi video yozib yuboring.\n"
                     f"(Video {video_age:.0f} sekund eski, maksimal 10 sekund ruxsat)",
                parse_mode="HTML"
            )
            return
        
        # 5. UNIQUE ID TEKSHIRUVI
        video_unique_id = message.video_note.file_unique_id
        
        if user_id not in SENT_VIDEOS:
            SENT_VIDEOS[user_id] = []
        
        if video_unique_id in SENT_VIDEOS[user_id]:
            logging.info(f"❌ VIDEO TAKROR: {video_unique_id}")
            await message.answer(
                text="❌ <b>Kechirasiz!</b> Bu video avval yuborilgan.\n\n"
                     "Iltimos, <b>yangi, real vaqtda</b> video yozib yuboring.",
                parse_mode="HTML"
            )
            return
        
        # 6. MESSAGE_ID TEKSHIRUVI
        if message.message_id < 50 and video_age > 5:
            logging.info(f"❌ MESSAGE_ID JUDA KICHIK: {message.message_id}")
            await message.answer(
                text="❌ <b>Kechirasiz!</b> Eski xabarni qayta yuborish mumkin emas.\n\n"
                     "Iltimos, <b>hozir</b> yangi video yozib yuboring.",
                parse_mode="HTML"
            )
            return
        
        # ========== BAJARILDI ==========
        logging.info(f"✅ VIDEO QABUL QILINDI: {video_unique_id[:8]}... (yoshi: {video_age:.0f} sekund)")
        
        SENT_VIDEOS[user_id].append(video_unique_id)
        
        if len(SENT_VIDEOS[user_id]) > 10:
            SENT_VIDEOS[user_id] = SENT_VIDEOS[user_id][-10:]
        
        role = USERS_ROLES[user_id]["role"]
        await message.answer(
            text=f"✅ Vazifa muvaffaqiyatli topshirildi va hisobot guruhga yuborildi.\n\n"
                 f"📹 Video qabul qilindi (yozilgan vaqt: {video_age:.0f} sekund oldin)",
            reply_markup=get_main_menu(role),
            parse_mode="HTML"
        )
        
        if task:
            group_text = (
                f"✅ <b>VAZIFA BAJARILDI!</b>\n\n"
                f"📋 <b>Turi:</b> {task['task_type']}\n"
                f"📌 <b>Vazifa nomi:</b> {task['task_name']}\n"
                f"👤 <b>Masʻul xodim:</b> {task['assigned_to_name']}\n"
                f"📸 <b>Isbot turi:</b> Dumaloq video (Video message)\n"
                f"⏰ <b>Topshirilgan vaqt:</b> {datetime.now(timezone(timedelta(hours=5))).strftime('%H:%M')}\n"
                f"🆔 <b>Video ID:</b> {video_unique_id[:8]}..."
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


# ================= TAYMER (VAZIFALARNI AVTOMATIK YUBORISH) =================

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
                global SENT_VIDEOS
                SENT_VIDEOS.clear()
                logging.info("🗑 SENT_VIDEOS tozalandi (00:00)")
            
            if current_time_str != last_checked_minute:
                for task in TASKS_DATABASE:
                    if task.get("task_type") == "Kunlik (Bir martalik)":
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
                            from Keyboards.main_menu import get_task_complete_keyboard
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
            logging.error(f"Taymer tizimida xato: {e}")
        await asyncio.sleep(5)
