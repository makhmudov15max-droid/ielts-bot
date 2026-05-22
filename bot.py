import asyncio
import logging
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from Handlers.start import start_router, auto_task_scheduler, init_all_handlers
from Handlers.teachers_sheets import sheets_router
from Handlers.group_report import report_router
from Handlers.tasks import tasks_router
from Handlers.employees import employees_router
from Handlers.salaries import salaries_router
from Handlers.callback_handlers import callback_router
from utils.users_json import load_users
from utils.tasks_json import load_tasks
from utils.access import is_admin

# ================= LOGGING TIZIMI =================

LOG_FILE = "bot.log"

log_format = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(log_format, date_format))
root_logger.addHandler(console_handler)

try:
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)
    logging.info(f"Log faylga yozish yo'lga qo'yildi: {LOG_FILE}")
except Exception as e:
    logging.warning(f"Log faylga yozish yo'lga qo'yilmadi: {e}")

logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("gspread").setLevel(logging.WARNING)

logging.info("🚀 Bot ishga tushmoqda...")


async def main():
    try:
        ADMIN_ID = 6500594896  # config.ADMIN_ID dan olish mumkin
        
        logging.info("📡 Ma'lumotlar yuklanmoqda...")
        USERS_ROLES = load_users(ADMIN_ID)
        TASKS_DATABASE = load_tasks()
        logging.info(f"✅ {len(USERS_ROLES)} ta foydalanuvchi, {len(TASKS_DATABASE)} ta vazifa yuklandi")
        
        # Barcha handlerlar uchun global o'zgaruvchilarni o'rnatish
        init_all_handlers(USERS_ROLES, TASKS_DATABASE, ADMIN_ID)
        
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        
        # Barcha routerlarni ulash
        dp.include_router(start_router)
        dp.include_router(tasks_router)
        dp.include_router(employees_router)
        dp.include_router(salaries_router)
        dp.include_router(callback_router)
        dp.include_router(sheets_router)
        dp.include_router(report_router)
        
        logging.info("✅ Barcha routerlar ulandi")
        
        # Taymerni ishga tushirish
        asyncio.create_task(auto_task_scheduler(bot))
        logging.info("⏰ Task scheduler ishga tushdi")
        
        logging.info("✅ Bot polling boshlandi")
        await dp.start_polling(bot)
        
    except Exception as e:
        logging.critical(f"Bot ishga tushishda xatolik: {e}", exc_info=True)
    finally:
        logging.info("🛑 Bot to'xtatildi")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("👋 Bot foydalanuvchi tomonidan to'xtatildi")
    except Exception as e:
        logging.critical(f"Kutilmagan xatolik: {e}", exc_info=True)
        sys.exit(1)
