from aiogram.dispatcher.filters.state import State, StatesGroup


class SalaryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_status = State()
    waiting_for_hours = State()
    waiting_for_days = State()
    waiting_for_individual_plan = State()
    waiting_for_actual_sales = State()
    waiting_for_conversion_plan = State()
    waiting_for_actual_conversion = State()
    waiting_for_active_plan = State()
    waiting_for_team_active = State()
    waiting_for_russian = State()
    waiting_for_ielts = State()
    waiting_for_missed_hours = State()
    waiting_for_cover = State()
