import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
# Handlers papkasidagi start.py ichidan routerni chaqirib olamiz
from Handlers.start import start_router

# Bot ishga tushganda terminalda ma'lumotlarni chiroyli ko'rsatib turishi uchun logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def main():
    # Botni token orqali ro'yxatdan o'tkazamiz
    bot = Bot(token=BOT_TOKEN)
    
    # Dispatcher - bu barcha routerlarni o'ziga jamlovchi asosiy markaz
    dp = Dispatcher()
    
    # Boyagi start_router'ni asosiy dispatcherga ulaymiz
    dp.include_router(start_router)

    asyncio.create_task(auto_task_scheduler(bot))

    # Botni yangi xabarlarni kutish rejimida ishga tushiramiz (Polling)
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Loyihani ishga tushirish
    asyncio.run(main())
