import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import BOT_TOKEN
from sheets import get_graduating_report, clear_cache

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

ALLOWED_IDS = []  # Bo'sh qoldirsangiz hamma foydalana oladi
                   # [123456789, 987654321] — faqat shu IDlar uchun


def is_allowed(user_id: int) -> bool:
    if not ALLOWED_IDS:
        return True
    return user_id in ALLOWED_IDS


@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    if not is_allowed(message.from_user.id):
        return
    await message.answer(
        "👋 Salom! Men IELTS guruhlar botiman.\n\n"
        "📋 *Buyruqlar:*\n"
        "/report — 14 kun ichida tugaydigan IELTS guruhlar\n"
        "/report7 — 7 kun ichida tugaydigan guruhlar\n"
        "/report30 — 30 kun ichida tugaydigan guruhlar\n"
        "/refresh — Keshni tozalash (yangi ma'lumot olish)"
    )


@dp.message_handler(commands=["report"])
async def cmd_report(message: types.Message):
    if not is_allowed(message.from_user.id):
        return
    await message.answer("⏳ Ma'lumot olinmoqda...")
    text = get_graduating_report(days_limit=14)
    await message.answer(text)


@dp.message_handler(commands=["report7"])
async def cmd_report7(message: types.Message):
    if not is_allowed(message.from_user.id):
        return
    await message.answer("⏳ Ma'lumot olinmoqda...")
    text = get_graduating_report(days_limit=7)
    await message.answer(text)


@dp.message_handler(commands=["report30"])
async def cmd_report30(message: types.Message):
    if not is_allowed(message.from_user.id):
        return
    await message.answer("⏳ Ma'lumot olinmoqda...")
    text = get_graduating_report(days_limit=30)
    await message.answer(text)


@dp.message_handler(commands=["refresh"])
async def cmd_refresh(message: types.Message):
    if not is_allowed(message.from_user.id):
        return
    clear_cache()
    await message.answer("✅ Kesh tozalandi. Keyingi /report yangi ma'lumot oladi.")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
