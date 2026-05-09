from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN

bot = Bot(token=TOKEN)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
