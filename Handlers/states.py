from aiogram.fsm.state import StatesGroup, State

# Tizim bosqichlari
class TaskStates(StatesGroup):
    waiting_for_user_name = State()       # Foydalanuvchi ism-familiyasini kutish (Yangi)
    waiting_for_name = State()            # Vazifa nomini kutish holati
    waiting_for_days = State()            # Kunlarni tanlashni kutish holati
    waiting_for_frequency = State()       # Kunlik takrorlanish sonini kutish holati
    waiting_for_once_time = State()       # Bitta aniq vaqtni matn ko'rinishida kutish
    waiting_for_multiple_times = State()  # Bir nechta vaqtni vergul bilan kutish
