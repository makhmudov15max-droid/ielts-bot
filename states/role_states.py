from aiogram.dispatcher.filters.state import (
    State,
    StatesGroup
)


class RoleStates(StatesGroup):

    waiting_role = State()
