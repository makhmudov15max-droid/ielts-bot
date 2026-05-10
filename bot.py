from aiogram import executor

from safety.loader import dp

# IMPORT HANDLERS

import handlers.start
import handlers.approvals

import handlers.admin_salary
import handlers.cashier_salary


# START BOT

if __name__ == "__main__":

    executor.start_polling(
        dp,
        skip_updates=True
    )
