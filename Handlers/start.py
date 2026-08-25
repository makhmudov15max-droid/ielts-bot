from Keyboards.main_menu import get_main_menu, get_admin_approval_keyboard, get_task_complete_keyboard, get_check_in_reminder_keyboard
import asyncio
from datetime import datetime, timedelta, timezone
import time
import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from utils.users_db import save_users
from utils.tasks_db import save_tasks, load_tasks, reset_sent_today_times
from utils.access import check_user_access
from utils.attendance_db import has_checkin_today, mark_missed_for_date, get_attendance_by_user_and_date
from utils.users_db import get_user_work_time
from utils.holidays_db import is_today_global_holiday
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
            text="🌐 <b>ORBIT HQ</b> — Ish boshqaruv tizimiga xush kelibsiz!\n\n"
                 "Bu bot orqali siz:\n"
                 "✅ Ishga kelganingizni tasdiqlaysiz\n"
                 "📋 Kundalik vazifalaringizni olasiz\n"
                 "📊 O'z davomatingizni kuzatasiz\n\n"
                 "⏳ So'rovingiz administratorga yuborildi.\n"
                 "Tasdiqlangach sizga xabar beriladi.",
            parse_mode="HTML"
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
    
    # ===== XAVFSIZLIK: Ism kiritilmagan bo'lsa, menyuni ko'rsatma =====
    if not user_info.get("name"):
        await message.answer(
            text=f"Sizga administrator tomonidan <b>{role}</b> unvoni berilgan.\n\n"
                 f"Iltimos, tizimdan foydalanish uchun avval <b>ism va familiyangizni</b> kiriting:",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    await message.answer(
        text=f"🌐 <b>ORBIT HQ</b> ga xush kelibsiz, {saved_name}!\n"
             f"🎖 Lavozimingiz: <b>{role}</b>\n\n"
             f"Quyidagi tugmalar orqali botni boshqaring 👇",
        parse_mode="HTML",
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
    await save_users(USERS_ROLES)

    await message.answer(
        text=f"🎉 <b>Tabriklaymiz, {first_name}!</b>\n\n"
             f"Siz ORBIT HQ tizimida <b>{USERS_ROLES[user_id]['role']}</b> sifatida ro'yxatdan o'tdingiz.\n\n"
             f"Endi quyidagi imkoniyatlardan foydalanishingiz mumkin:\n"
             f"✅ <b>Ishga keldim</b> — har kuni ishga kelganingizni tasdiqlang\n"
             f"📋 <b>Vazifalar ro'yxati</b> — kundalik topshiriqlaringizni ko'ring",
        parse_mode="HTML",
        reply_markup=get_main_menu(USERS_ROLES[user_id]["role"])
    )


async def auto_task_scheduler(bot):
    last_checked_minute = ""
    last_daily_check_date = ""
    tashkent_tz = timezone(timedelta(hours=5))
    
    # Kunlik eslatma yuborilganligini kuzatish (faqat asosiy sikl uchun)
    reminder_sent_today = {}
    
    # ========== BOT RESTART QILGANDA O'TKAZIB YUBORILGAN ESLATMALARNI QAYTA YUBORISH ==========
    now = datetime.now(timezone.utc).astimezone(tashkent_tz)
    current_time_str = now.strftime("%H:%M")
    today_str = now.strftime("%Y-%m-%d")
    
    # RESTART CHECK UCHUN ALOHIDA DICTIONARY
    restart_reminder_sent = {}
    
    for user_id, user_info in USERS_ROLES.items():
        if not isinstance(user_info, dict):
            continue
        role = user_info.get("role")
        if role in ["Owner", "Manager"]:
            continue
        
        if await has_checkin_today(str(user_id)):
            continue
        
        work_start, work_end = await get_user_work_time(user_id)
        
        try:
            ws_h, ws_m = map(int, work_start.split(":"))
            reminder_minutes = (ws_h * 60 + ws_m) - 30
            if reminder_minutes < 0:
                reminder_minutes += 24 * 60
            
            reminder_h = reminder_minutes // 60
            reminder_m = reminder_minutes % 60
            reminder_str = f"{reminder_h:02d}:{reminder_m:02d}"
            
            current_minutes = int(current_time_str.split(":")[0]) * 60 + int(current_time_str.split(":")[1])
            ish_minutes = ws_h * 60 + ws_m
            
            print(f"🔍 RESTART CHECK: user={user_id}, work_start={work_start}, reminder={reminder_str}, current={current_time_str}, ish={ish_minutes}")
            
            if reminder_minutes <= current_minutes < ish_minutes and restart_reminder_sent.get(user_id) != today_str:
                print(f"✅✅✅ RESTART ESLATMA YUBORILDI! user={user_id}")
                try:
                    await bot.send_message(
                        chat_id=int(user_id),
                        text=f"⏰ <b>30 daqiqadan so'ng ish smenangiz boshlanadi!</b>\n\n📋 Ish vaqtingiz: {work_start} - {work_end}\n\n✅ Iltimos, ishga kelganingizni tasdiqlash uchun <b>'✅ Ishga keldim'</b> tugmasini bosing.",
                        parse_mode="HTML",
                        reply_markup=get_check_in_reminder_keyboard()
                    )
                    restart_reminder_sent[user_id] = today_str
                    logging.info(f"Restartda o'tkazib yuborilgan eslatma yuborildi: user_id={user_id}")
                except Exception as e:
                    logging.error(f"Restart eslatmasi yuborishda xatolik: {e}")
        except Exception as e:
            logging.error(f"Restart eslatmasi hisoblashda xatolik: {e}")
            continue
    
    # ========== ASOSIY SIKL ==========
    # Smena yakunida ishga kelmaganlar uchun xabar yuborilganligini kuzatish
    missed_notified = {}
    while True:
        try:
            now = datetime.now(timezone.utc).astimezone(tashkent_tz)
            current_time_str = now.strftime("%H:%M")
            current_day_name = now.strftime("%a").strip().lower()
            day_of_month = now.day
            today_str = now.strftime("%Y-%m-%d")
            
            # ===== BUGUN BAYRAM KUNI EKANLIGINI TEKSHIRISH =====
            is_holiday = await is_today_global_holiday()
            
            if current_time_str == "00:00":
                await reset_sent_today_times()
                for task in TASKS_DATABASE:
                    task["sent_today_times"] = []
                reminder_sent_today.clear()
                missed_notified.clear()
            
            # Agar bayram kuni bo'lsa, ishga kelish eslatmalarini YUBORMA
            if not is_holiday:
                for user_id, user_info in USERS_ROLES.items():
                    if not isinstance(user_info, dict):
                        continue
                    role = user_info.get("role")
                    if role in ["Owner", "Manager"]:
                        continue
                    
                    if reminder_sent_today.get(user_id) == today_str:
                        continue
                    
                    if await has_checkin_today(str(user_id)):
                        reminder_sent_today[user_id] = today_str
                        continue
                    
                    work_start, work_end = await get_user_work_time(user_id)
                    
                    try:
                        ws_h, ws_m = map(int, work_start.split(":"))
                        
                        reminder_minutes = (ws_h * 60 + ws_m) - 30
                        if reminder_minutes < 0:
                            reminder_minutes += 24 * 60
                        
                        reminder_h = reminder_minutes // 60
                        reminder_m = reminder_minutes % 60
                        reminder_str = f"{reminder_h:02d}:{reminder_m:02d}"
                        
                        if current_time_str == reminder_str:
                            print(f"✅✅✅ ESLATMA YUBORILDI! user={user_id}, time={reminder_str}")
                            try:
                                await bot.send_message(
                                    chat_id=int(user_id),
                                    text=f"⏰ <b>30 daqiqadan so'ng ish smenangiz boshlanadi!</b>\n\n📋 Ish vaqtingiz: {work_start} - {work_end}\n\n✅ Iltimos, ishga kelganingizni tasdiqlash uchun <b>'✅ Ishga keldim'</b> tugmasini bosing.",
                                    parse_mode="HTML",
                                    reply_markup=get_check_in_reminder_keyboard()
                                )
                                reminder_sent_today[user_id] = today_str
                                logging.info(f"Ishga kelish eslatmasi yuborildi: user_id={user_id}, time={work_start}")
                            except Exception as e:
                                logging.error(f"Eslatma yuborishda xatolik: {e}")
                    except Exception as e:
                        continue
            
            # Kun oxiri tekshiruvi (bayram kunida missed deb belgilama)
            if not is_holiday:
                if current_time_str == "23:59" and last_daily_check_date != today_str:
                    logging.info(f"Kun oxiri tekshiruvi boshlandi: {today_str}")
                    for user_id, user_info in USERS_ROLES.items():
                        if not isinstance(user_info, dict):
                            continue
                        role = user_info.get("role")
                        if role in ["Owner", "Manager"]:
                            continue
                        if not await has_checkin_today(str(user_id)):
                            await mark_missed_for_date(str(user_id), today_str)
                    last_daily_check_date = today_str

                    # ===== OY OXIRI: Admin larga bonus xabari =====
                    # Oyning oxirgi kuni ekanligini tekshiramiz
                    import calendar as _cal
                    last_day = _cal.monthrange(now.year, now.month)[1]
                    if now.day == last_day:
                        try:
                            from utils.fines_db import has_active_fine_in_month
                            for u_id, u_info in USERS_ROLES.items():
                                if not isinstance(u_info, dict):
                                    continue
                                brole = u_info.get("role")
                                if brole != "Admin":
                                    continue
                                if u_info.get("name") is None:
                                    continue
                                has_fine = await has_active_fine_in_month(str(u_id), now.year, now.month)
                                if not has_fine:
                                    await bot.send_message(
                                        chat_id=int(u_id),
                                        text=(
                                            f"🎉 <b>Tabriklaymiz, {u_info.get('name', 'Xodim')}!</b>\n\n"
                                            f"Bu oy hech qachon kech kelmadingiz. Sizga <b>100,000 so'm</b> bonus berildi. 🎉"
                                        ),
                                        parse_mode="HTML"
                                    )
                        except Exception as e:
                            logging.error(f"Oy oxiri bonus xabari xatolik: {e}")

                # ===== SMENA YAKUNI: ishga kelmaganlar uchun owner xabari =====
                # Har xodimning work_end + 1 daqiqasida, agar ishga kelmagan bo'lsa,
                # owner/manager ga "Ishga kelmadi" xabari + jarima tugmasi
                for user_id, user_info in USERS_ROLES.items():
                    if not isinstance(user_info, dict):
                        continue
                    srole = user_info.get("role")
                    if srole in ["Owner", "Manager"]:
                        continue
                    skey = f"{user_id}:{today_str}"
                    if missed_notified.get(skey):
                        continue
                    if await has_checkin_today(str(user_id)):
                        missed_notified[skey] = True
                        continue
                    try:
                        ws_, we_ = await get_user_work_time(str(user_id))
                        we_h, we_m = map(int, we_.split(":"))
                        we_plus = we_h * 60 + we_m + 1
                        we_h2 = (we_plus // 60) % 24
                        we_m2 = we_plus % 60
                        end_plus_str = f"{we_h2:02d}:{we_m2:02d}"
                    except Exception:
                        continue
                    if current_time_str != end_plus_str:
                        continue

                    # Smena yakunlandi va xodim kelmadi -> owner xabar
                    missed_notified[skey] = True
                    sname = user_info.get("name", "Xodim")
                    boss_ids = [
                        int(uid) for uid, ui in USERS_ROLES.items()
                        if isinstance(ui, dict) and ui.get("role") in ["Owner", "Manager"]
                    ]
                    for bid in boss_ids:
                        try:
                            await bot.send_message(
                                chat_id=bid,
                                text=(
                                    f"🚫 <b>Ishga kelmadi</b>\n\n"
                                    f"👤 <b>Xodim:</b> {sname}\n"
                                    f"🎖 <b>Lavozim:</b> {srole}\n"
                                    f"📅 <b>Sana:</b> {today_str}\n\n"
                                    f"Ushbu xodim ish smenasi yakuniga qadar ishga kelmadi. Jarima belgilashingiz mumkin:"
                                ),
                                parse_mode="HTML",
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                    [InlineKeyboardButton(text="💰 Jarima belgilash",
                                                           callback_data=f"absent_fine_{user_id}_{today_str}")]
                                ])
                            )
                        except Exception as e:
                            logging.error(f"Smena yakuni xabari xatolik: {e}")

                # ===== XAVFSIZLIK TARMOG'I: 00:05 da kechagi kun uchun tekshiruv =====
                # Agar bot 23:59 da restart bo'lib qolgan bo'lsa, kechagi kun
                # missed belgilanmagan bo'lishi mumkin. Shu yerda tekshiramiz.
                if current_time_str == "00:05":
                    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
                    logging.info(f"Kechagi kun xavfsizlik tekshiruvi: {yesterday}")
                    for user_id, user_info in USERS_ROLES.items():
                        if not isinstance(user_info, dict):
                            continue
                        role = user_info.get("role")
                        if role in ["Owner", "Manager"]:
                            continue
                        existing = await get_attendance_by_user_and_date(str(user_id), yesterday)
                        if not existing:
                            await mark_missed_for_date(str(user_id), yesterday)
                            logging.info(f"Xavfsizlik: {user_id} kechagi kun ({yesterday}) missed belgilandi")
            
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
                            await bot.send_message(
                                chat_id=task["assigned_to_id"],
                                text=f"📌 <b>{task['task_name']}</b>",
                                parse_mode="HTML",
                                reply_markup=get_task_complete_keyboard(task["id"])
                            )
                            task["sent_today_times"].append(current_time_str)
                            await save_tasks(TASKS_DATABASE)
                last_checked_minute = current_time_str
                
        except Exception as e:
            print(f"Taymer tizimida xato: {e}")
        await asyncio.sleep(5)
