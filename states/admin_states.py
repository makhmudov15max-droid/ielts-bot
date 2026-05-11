from aiogram.dispatcher.filters.state import (
    State,
    StatesGroup
)


class AdminSalaryStates(StatesGroup):

    status = State()

    daily_hours = State()
    custom_daily_hours = State()

    worked_days = State()
    custom_worked_days = State()

    has_ielts = State()

    knows_russian = State()

    missed = State()
    missed_hours = State()

    cover = State()
    cover_hours = State()

    individual_plan = State()
    actual_sales = State()

    conversion_plan = State()
    actual_conversion = State()

    active_plan = State()
    actual_active = State()
