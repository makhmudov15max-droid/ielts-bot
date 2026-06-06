import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
import redis.asyncio as redis
import os

from Handlers.attendance_admin import attendance_admin_router, init_attendance_admin_handler
from config import BOT_TOKEN
from Handlers.start import start_router, auto_task_scheduler, init_all_handlers
from Handlers.teachers_sheets import sheets_router, set_users_roles as set_teachers_users_roles
from Handlers.group_report import report_router, set_users_roles as set_report_users_roles
from Handlers.tasks import tasks_router, init_tasks_handler
from Handlers.employees import employees_router, init_employees_handler
from Handlers.salaries import salaries_router, init_salaries_handler
from Handlers.callback_handlers import callback_router, init_callback_handler
from Handlers.proofs import proofs_router, init_proofs_handler
from Handlers.monitoring import monitoring_router, init_monitoring_handler
from Handlers.settings import settings_router, init_settings_handler
from Handlers.holidays import holidays_router, init_holidays_handler
from utils.database import init_db, close_db
from utils.users_db import load_users
from utils.tasks_db import load_tasks

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logging.getLogger("aiogram").setLevel(logging.WARNING)

logging.info("🚀 Bot ishga tushmoqda...")


async def main():
    try:
        ADMIN_ID = 6500594896

        # PostgreSQL ni ulash
        await init_db()

        # Redis ni ulash (FSM uchun)
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url)
        storage = RedisStorage(redis=redis_client)

        logging.info("📡 Ma'lumotlar yuklanmoqda...")
        USERS_ROLES = await load_users()
        TASKS_DATABASE = await load_tasks()
        logging.info(f"✅ {len(USERS_ROLES)} ta foydalanuvchi, {len(TASKS_DATABASE)} ta vazifa yuklandi")
        logging.info(f"DEBUG: USERS_ROLES type: {type(USERS_ROLES)}, is None: {USERS_ROLES is None}")

        # Global users roles ni teachers_sheets va group_report ga o'tkazish
        set_teachers_users_roles(USERS_ROLES)
        set_report_users_roles(USERS_ROLES)

        # Barcha handlerlar uchun global o'zgaruvchilarni o'rnatish
        init_all_handlers(USERS_ROLES, TASKS_DATABASE, ADMIN_ID)
        init_tasks_handler(USERS_ROLES, TASKS_DATABASE)
        init_employees_handler(USERS_ROLES, ADMIN_ID)
        init_salaries_handler(USERS_ROLES)
        init_callback_handler(USERS_ROLES, TASKS_DATABASE, ADMIN_ID)
        init_proofs_handler(USERS_ROLES, ADMIN_ID)
        init_monitoring_handler(USERS_ROLES)
        init_settings_handler(USERS_ROLES, ADMIN_ID)
        init_attendance_admin_handler(USERS_ROLES)
        init_holidays_handler(USERS_ROLES)

        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=storage)

        # ============================================================
        # WEBHOOK NI O'CHIRISH (Sherlock yoki boshqa bot qoldirgan)
        # ============================================================
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("✅ Webhook o'chirildi, eski xabarlar tozalandi")

        # Barcha kutilayotgan xabarlarni tozalash (offset flush)
        try:
            updates = await bot.get_updates(offset=-1, limit=1, timeout=0)
            if updates:
                await bot.get_updates(offset=updates[-1].update_id + 1, limit=1, timeout=0)
                logging.info(f"✅ Pending updates tozalandi (last_id={updates[-1].update_id})")
        except Exception:
            pass

        # Routerlarni ulash
        dp.include_router(start_router)
        dp.include_router(tasks_router)
        dp.include_router(employees_router)
        dp.include_router(salaries_router)
        dp.include_router(callback_router)
        dp.include_router(proofs_router)
        dp.include_router(monitoring_router)
        dp.include_router(sheets_router)
        dp.include_router(report_router)
        dp.include_router(settings_router)
        dp.include_router(attendance_admin_router)
        dp.include_router(holidays_router)

        logging.info("✅ Barcha routerlar ulandi")

        # Taymerni ishga tushirish
        asyncio.create_task(auto_task_scheduler(bot))
        logging.info("⏰ Task scheduler ishga tushdi")

        logging.info("✅ Bot polling boshlandi")
        await dp.start_polling(bot, drop_pending_updates=True)

    except Exception as e:
        logging.critical(f"Bot ishga tushishda xatolik: {e}", exc_info=True)
    finally:
        await close_db()
        logging.info("🛑 Bot to'xtatildi")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("👋 Bot foydalanuvchi tomonidan to'xtatildi")
    except Exception as e:
        logging.critical(f"Kutilmagan xatolik: {e}", exc_info=True)
        sys.exit(1)
