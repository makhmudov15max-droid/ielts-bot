from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup

TOKEN = "8679587093:AAGjXpGVMiAexuNKPzRpQjASQRb8K2DYvyg"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# =====================================
# STATES
# =====================================

class AdminSalaryStates(StatesGroup):

    waiting_for_status = State()

    waiting_for_hours = State()
    waiting_for_days = State()

    waiting_for_individual_plan = State()
    waiting_for_actual_sales = State()

    waiting_for_conversion_plan = State()
    waiting_for_actual_conversion = State()

    waiting_for_active_plan = State()
    waiting_for_actual_active = State()

    waiting_for_russian = State()
    waiting_for_ielts = State()

    waiting_for_missed_work = State()
    waiting_for_missed_hours = State()

    waiting_for_cover = State()
    waiting_for_cover_hours = State()
