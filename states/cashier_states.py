from aiogram.dispatcher.filters.state import (
    State,
    StatesGroup
)


class CashierStates(StatesGroup):

    hours = State()
    custom_hours = State()

    days = State()
    custom_days = State()

    cover = State()
    cover_hours = State()

    absent = State()
    absent_hours = State()

    active_students = State()
    active_debtors = State()

    archive_students = State()
    archive_debtors = State()
