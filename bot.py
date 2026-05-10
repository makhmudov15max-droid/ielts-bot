from aiogram import executor

from safety.loader import dp

from handlers.admin_salary import register_admin_handlers
from handlers.cashier_salary import register_cashier_handlers

import safety.handlers.start
import safety.handlers.approvals


register_admin_handlers(dp)
register_cashier_handlers(dp)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
