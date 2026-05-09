from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from handlers.admin_salary import register_admin_handlers

from config import TOKEN

bot = Bot(token=TOKEN)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):

    await message.answer("Bot ishlayapti ✅")

register_admin_handlers(dp)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

