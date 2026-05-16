from aiogram.fsm.state import StatesGroup, State

# Task yaratish bosqichlari
class TaskStates(StatesGroup):
    waiting_for_name = State()  # Vazifa nomini kutish holati
    waiting_for_days = State()  # Kunlarni tanlashni kutish holati
