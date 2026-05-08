from aiogram.dispatcher.filters.state import State, StatesGroup


class SalaryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_status = State()
    waiting_for_hours = State()
    waiting_for_days = State()
