from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import logging
import os

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler()
async def echo(message: types.Message):
    print("MESSAGE KELDI:", message.text)
    
    await message.answer(
        f"Siz yozdingiz: {message.text}"
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
