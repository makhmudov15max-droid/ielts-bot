from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN

from handlers.admin_salary import register_admin_handlers

from keyboards.admin_keyboard import main_menu_keyboard


bot = Bot(token=TOKEN)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):

    await message.answer(
        "🏠 Bosh sahifa",
        reply_markup=main_menu_keyboard()
    )


register_admin_handlers(dp)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
