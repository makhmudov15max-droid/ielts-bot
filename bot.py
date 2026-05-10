import logging

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN


logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)


# handlers
import safety.handlers.start
import handlers.cashier_salary
import handlers.admin_salary
import handlers.approvals


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
