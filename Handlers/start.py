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
# Format: {file_unique_id: {"user_id": xxx, "chat_id": xxx, "timestamp": xxx}}
GLOBAL_VIDEO_TRACKING = {}


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


# ================= ISBOT QABUL QILISH (TO'LIQ HIMOYA BILAN) =================

@start_router.message(TaskStates.waiting_for_task_proof)
async def receive_task_proof_handler(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    proof_required = state_data.get("proof_required")
    task_id = state_data.get("active_task_id")
    
    global TASKS_DATABASE, GLOBAL_VIDEO_TRACKING
    task = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    GROUP_CHAT_ID = -5226036627  
    user_id = str(message.from_user.id)
    current_time = int(time.time())
    
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
    
    # ========== DUMALOQ VIDEO TEKSHIRUVI (YAKUNIY VERSIYA) ==========
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
        
        # 2. FORWARD ANIQLASH (BARCHA USULLAR KOMBINATSIYASI)
        is_forwarded = False
        forward_reason = ""
        
        # Usul A: Yangi API (forward_origin) – Telegram Bot API 6.x+
        if hasattr(message, 'forward_origin') and message.forward_origin is not None:
            is_forwarded = True
            forward_reason = f"forward_origin={message.forward_origin}"
            logging.info(f"❌ Forward aniqlangan: {forward_reason}")
        
        # Usul B: Eski API atributlari
        elif (getattr(message, 'forward_from', None) or 
              getattr(message, 'forward_from_chat', None) or
              getattr(message, 'forward_date', None)):
            is_forwarded = True
            forward_reason = "eski API atributlari (forward_from/chat/date)"
            logging.info(f"❌ Forward aniqlangan: {forward_reason}")
        
        # Usul C: Chat ID != User ID (shaxsiy chatdan yuborilmagan)
        elif str(message.chat.id) != str(message.from_user.id):
            is_forwarded = True
            forward_reason = f"chat.id={message.chat.id} != user.id={message.from_user.id}"
            logging.info(f"❌ Forward aniqlangan: {forward_reason}")
        
        if is_forwarded:
            await message.answer(
                text="❌ <b>Kechirasiz!</b> Forward qilingan video qabul qilinmaydi.\n\n"
                     "Iltimos, <b>hozir, real vaqtda</b> bot bilan shaxsiy chatda yangi video yozib yuboring.\n\n"
                     "📹 <b>Qanday yuborish kerak:</b>\n"
                     "1. Shu chatda mikrofon tugmasini bosing va ushlab turing\n"
                     "2. <b>Video</b> tugmasiga o'ting\n"
                     "3. Yozish tugmasini bosing\n"
                     "4. Yozib bo'lgach, jo'natish tugmasini bosing",
                parse_mode="HTML"
            )
            return
        
        # 3. VIDEO YOSHI TEKSHIRUVI (real vaqtda yozilgan bo'lishi kerak)
        message_time = message.date.timestamp() if hasattr(message, 'date') else current_time
        video_age = current_time - message_time
        
        # 15 sekund – tarmoq kechikishini hisobga olgan holda
        if video_age > 15:
            logging.info(f"❌ VIDEO ESKI: {video_age:.0f} sekund")
            await message.answer(
                text=f"❌ <b>Kechirasiz!</b> Video {int(video_age)} sekund oldin yozilgan.\n\n"
                     "Iltimos, <b>hozir, real vaqtda</b> yangi video yozib yuboring.\n"
                     f"(Maksimal ruxsat: 15 sekund)",
                parse_mode="HTML"
            )
            return
        
        # 4. UNIQUE ID TEKSHIRUVI (bir xil video qayta ishlatilmasligi uchun)
        video_unique_id = message.video_note.file_unique_id
        
        if video_unique_id in GLOBAL_VIDEO_TRACKING:
            old_record = GLOBAL_VIDEO_TRACKING[video_unique_id]
            logging.info(f"❌ VIDEO TAKROR: {video_unique_id[:8]}..., old_user={old_record['user_id']}")
            await message.answer(
                text="❌ <b>Kechirasiz!</b> Bu video avval yuborilgan.\n\n"
                     "Iltimos, <b>yangi, real vaqtda</b> video yozib yuboring.",
                parse_mode="HTML"
            )
            return
        
        # 5. VIDEO QABUL QILINDI
        GLOBAL_VIDEO_TRACKING[video_unique_id] = {
            "user_id": user_id,
            "chat_id": str(message.chat.id),
            "timestamp": current_time
        }
        
        # Xotirani tozalash (1000 dan oshsa eski yozuvlarni o'chirish)
        if len(GLOBAL_VIDEO_TRACKING) > 1000:
            week_ago = current_time - (7 * 24 * 60 * 60)
            to_delete = [k for k, v in GLOBAL_VIDEO_TRACKING.items() if v["timestamp"] < week_ago]
            for k in to_delete:
                del GLOBAL_VIDEO_TRACKING[k]
            logging.info(f"🗑 GLOBAL_VIDEO_TRACKING tozalandi: {len(to_delete)} ta eski yozuv o'chirildi")
        
        logging.info(f"✅ VIDEO QABUL QILINDI: {video_unique_id[:8]}... (yoshi: {video_age:.0f} sekund)")
        
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
                global GLOBAL_VIDEO_TRACKING
                GLOBAL_VIDEO_TRACKING.clear()
                logging.info("🗑 GLOBAL_VIDEO_TRACKING tozalandi (00:00)")
            
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
