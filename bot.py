from aiogram import executor

from safety.loader import dp

from handlers.admin_salary import router as admin_salary_router

dp.include_router(admin_salary_router)


# SAFETY HANDLERS

import safety.handlers.start
import safety.handlers.approvals


# MAIN HANDLERS

#import handlers.admin_salary
import handlers.cashier_salary


# START BOT

if __name__ == "__main__":

    executor.start_polling(
        dp,
        skip_updates=True
    )
