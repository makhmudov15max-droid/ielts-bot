from aiogram.dispatcher.filters.state import State, StatesGroup


class AdminSalaryStates(StatesGroup):

    status = State()

    daily_hours = State()

    worked_days = State()
