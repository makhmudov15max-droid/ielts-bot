from aiogram import types
from aiogram.dispatcher import FSMContext

from safety.loader import dp


@dp.message_handler(text="📊 Admin Salary")
async def admin_salary_test(message: types.Message, state: FSMContext):

    await message.answer("Admin salary ishladi ✅")
