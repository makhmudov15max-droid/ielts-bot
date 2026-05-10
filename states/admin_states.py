from aiogram.fsm.state import State, StatesGroup


class AdminSalaryStates(StatesGroup):
    status = State()

    daily_hours = State()
    worked_days = State()

    individual_plan = State()
    actual_sales = State()

    conversion_plan = State()
    actual_conversion = State()

    active_plan = State()
    actual_active = State()

    knows_russian = State()
    has_ielts = State()

    cover_hours = State()
    missed_hours = State()

    confirm = State()
