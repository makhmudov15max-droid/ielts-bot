import logging

from aiogram import executor

from safety.loader import dp


logging.basicConfig(level=logging.INFO)


# safety handlers
import safety.handlers.start
import safety.handlers.approvals


# salary handlers
import handlers.cashier_salary
import handlers.admin_salary


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
