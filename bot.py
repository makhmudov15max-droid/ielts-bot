from aiogram import executor

from safety.loader import dp

import safety.handlers.start
import safety.handlers.approvals

import handlers.cashier_salary
import handlers.admin_salary


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
