import asyncio
import logging
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from Handlers.start import start_router, auto_task_scheduler
from Handlers.teachers_sheets import sheets_router
from Handlers.group_report import report_router

# ================= LOGGING TIZIMI =================

LOG_FILE = "bot.log"

# Log formatini sozlash
log_format = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Root logger ni sozlash
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Konsolga chiqarish (Railway da ko'rinadi)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(log_format, date_format))
root_logger.addHandler(console_handler)

# Faylga saqlash (backup uchun)
try:
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.WARNING)  # WARNING va undan yuqori darajalar faylga yoziladi
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)
    logging.info(f"Log faylga yozish yo'lga qo'yildi: {LOG_FILE}")
except Exception as e:
    logging.warning(f"Log faylga yozish yo'lga qo'yilmadi: {e}")

# Aiogram loglarini kamaytirish (faqat WARNING va undan yuqori)
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)
logging.getLogger("aiogram.dispatcher").setLevel(logging.WARNING)

# Gspread loglarini kamaytirish
logging.getLogger("gspread").setLevel(logging.WARNING)
logging.getLogger("google.auth").setLevel(logging.WARNING)

logging.info("🚀 Bot ishga tushmoqda...")


async def main():
    logging.info("📡 Bot token tekshirilmoqda...")
    bot = Bot(token=BOT_TOKEN)
    
    logging.info("🔄 Dispatcher yaratilmoqda...")
    dp = Dispatcher()
    
    # Routerlarni ulash
    dp.include_router(start_router)
    dp.include_router(sheets_router)
    dp.include_router(report_router)
    logging.info("✅ Routerlar ulandi")

    # Orqa fon taymerini ishga tushirish
    asyncio.create_task(auto_task_scheduler(bot))
    logging.info("⏰ Task scheduler ishga tushdi")

    logging.info("✅ Bot polling boshlandi")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"Bot pollingda xatolik: {e}", exc_info=True)
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
