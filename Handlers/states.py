from aiogram.fsm.state import StatesGroup, State

# Task yaratish bosqichlari
class TaskStates(StatesGroup):
    waiting_for_name = State()       # Vazifa nomini kutish holati
    waiting_for_days = State()       # Kunlarni tanlashni kutish holati
    waiting_for_frequency = State()  # Kunlik takrorlanish sonini kutish holati (Yangi qo'shildi)
