import asyncio
from datetime import datetime, timedelta, timezone
import time
import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from Handlers.states import TaskStates
from Keyboards.main_menu import get_main_menu, get_admin_approval_keyboard, get_task_complete_keyboard
from utils.attendance_db import has_checkin_today, mark_missed_for_date
from utils.users_db import get_user_work_time
from utils.users_db import save_users, set_user_busy, set_user_free, is_user_busy, get_user_active_task
from utils.tasks_db import save_tasks, update_task_status, load_tasks, get_task_by_id, reset_sent_today_times
from utils.proofs_db import add_proof
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
    await save_users(USERS_ROLES)  # ASYNC + AWAIT

    await message.answer(
        text=f"Hurmatli {first_name}, siz muvaffaqiyatli roʻyxatdan oʻtdingiz. "
             f"Endi bot imkoniyatlaridan foydalanishingiz mumkin.",

        reply_markup=get_main_menu(
            USERS_ROLES[user_id]["role"]
        )
    )


# ================= ISBOT QABUL QILISH (VAZIFA BAJARISH) =================
@start_router.message(TaskStates.waiting_for_task_proof)
async def receive_task_proof_handler(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    proof_required = state_data.get("proof_required")
    task_id = state_data.get("active_task_id")
    
    global TASKS_DATABASE
    task = await get_task_by_id(task_id) if task_id else None  # ASYNC + AWAIT
    GROUP_CHAT_ID = -5226036627  
    user_id = str(message.from_user.id)
    
    # Foydalanuvchini band qilish
    await set_user_busy(user_id, task_id)  # ASYNC + AWAIT
    
    # ========== MATN TEKSHIRUVI ==========
    if proof_required == "Text" and message.text and not message.photo and not message.video_note:
        role = USERS_ROLES[user_id]["role"]
        
        proof = await add_proof(  # ASYNC + AWAIT
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
            await update_task_status(task_id, "completed", user_id)  # ASYNC + AWAIT
            TASKS_DATABASE = await load_tasks()  # ASYNC + AWAIT
        
        await set_user_free(user_id)  # ASYNC + AWAIT
        
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
        
        await state.clear()
    
    # ========== RASM TEKSHIRUVI ==========
    elif proof_required == "Photo" and message.photo:
        role = USERS_ROLES[user_id]["role"]
        
        proof = await add_proof(  # ASYNC + AWAIT
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
            await update_task_status(task_id, "completed", user_id)  # ASYNC + AWAIT
            TASKS_DATABASE = await load_tasks()  # ASYNC + AWAIT
        
        await set_user_free(user_id)  # ASYNC + AWAIT
        
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
        
        proof = await add_proof(  # ASYNC + AWAIT
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
            await update_task_status(task_id, "completed", user_id)  # ASYNC + AWAIT
            TASKS_DATABASE = await load_tasks()  # ASYNC + AWAIT
        
        await set_user_free(user_id)  # ASYNC + AWAIT
        
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
    last_daily_check_date = ""
    tashkent_tz = timezone(timedelta(hours=5))
    
    while True:
        try:
            now = datetime.now(timezone.utc).astimezone(tashkent_tz)
            current_time_str = now.strftime("%H:%M")
            current_day_name = now.strftime("%a").strip().lower()
            day_of_month = now.day
            today_str = now.strftime("%Y-%m-%d")
            
            # ========== 1. KUNLIK RESET (00:00) ==========
            if current_time_str == "00:00":
                await reset_sent_today_times()
                for task in TASKS_DATABASE:
                    task["sent_today_times"] = []
            
            # ========== 2. ISHGA KELISH ESLATMALARI (30 daqiqa oldin) ==========
            # Har bir xodimni tekshirish
            for user_id, user_info in USERS_ROLES.items():
                if not isinstance(user_info, dict):
                    continue
                role = user_info.get("role")
                if role in ["Owner", "Manager"]:
                    continue  # Faqat oddiy xodimlarga eslatma
                
                # Ish vaqtini olish
                work_start, work_end = await get_user_work_time(user_id)
                
                # 30 daqiqa oldin vaqtni hisoblash
                try:
                    ws_h, ws_m = map(int, work_start.split(":"))
                    reminder_time = (ws_h * 60 + ws_m) - 30
                    reminder_h = reminder_time // 60
                    reminder_m = reminder_time % 60
                    reminder_str = f"{reminder_h:02d}:{reminder_m:02d}"
                except Exception:
                    continue
                
                # Eslatma vaqtiga yetganda va bugun hali tasdiqlanmagan bo'lsa
                if current_time_str == reminder_str:
                    # Bugun allaqachon tasdiqlaganmi?
                    if not await has_checkin_today(str(user_id)):
                        try:
                            await bot.send_message(
                                chat_id=int(user_id),
                                text=(
                                    f"⏰ <b>30 daqiqadan so'ng Ish smenangiz boshlanadi!</b>\n\n"
                                    f"📋 Ish vaqtingiz: {work_start} - {work_end}\n\n"
                                    f"✅ Iltimos, ishga kelganingizni tasdiqlash uchun "
                                    f"<b>'✅ Ishga keldim'</b> tugmasini bosing va dumaloq video yuboring.",
                                    parse_mode="HTML"
                                )
                            )
                            logging.info(f"Eslatma yuborildi: user_id={user_id}, vaqt={reminder_str}")
                        except Exception as e:
                            logging.error(f"Eslatma yuborishda xatolik: {e}")
            
            # ========== 3. KUN OXIRIDA TEKSHIRUV (23:59) ==========
            if current_time_str == "23:59" and last_daily_check_date != today_str:
                logging.info(f"Kun oxiri tekshiruvi boshlandi: {today_str}")
                
                # Barcha oddiy xodimlarni tekshirish
                for user_id, user_info in USERS_ROLES.items():
                    if not isinstance(user_info, dict):
                        continue
                    role = user_info.get("role")
                    if role in ["Owner", "Manager"]:
                        continue
                    
                    # Bugun tasdiqlaganmi?
                    if not await has_checkin_today(str(user_id)):
                        await mark_missed_for_date(str(user_id), today_str)
                        logging.info(f"Marked as missed: user_id={user_id}, date={today_str}")
                
                last_daily_check_date = today_str
                logging.info(f"Kun oxiri tekshiruvi tugadi: {today_str}")
            
            # ========== 4. VAZIFALARNI YUBORISH ==========
            if current_time_str != last_checked_minute:
                # ... (vazifalarni yuborish kodi o'zgarishsiz qoladi)
                
                last_checked_minute = current_time_str
                
        except Exception as e:
            print(f"Taymer tizimida xato: {e}")
        await asyncio.sleep(5)
