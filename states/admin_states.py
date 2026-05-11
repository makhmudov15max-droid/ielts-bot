from aiogram.dispatcher.filters.state import (
    State,
    StatesGroup
)


class AdminStates(StatesGroup):

    status = State()

    hours = State()

    days = State()

    kpi = State()
