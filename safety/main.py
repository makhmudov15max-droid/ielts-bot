from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import BOT_TOKEN


bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


import handlers.start
import handlers.approvals


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
