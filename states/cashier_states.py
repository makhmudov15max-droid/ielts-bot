from aiogram.dispatcher.filters.state import State, StatesGroup


class CashierSalaryStates(StatesGroup):

    waiting_for_hours = State()

    waiting_for_days = State()

    waiting_for_missed_work = State()
    waiting_for_missed_days = State()

    waiting_for_cover = State()
    waiting_for_cover_days = State()

    waiting_for_active_students = State()
    waiting_for_active_debtors = State()

    waiting_for_archive_students = State()
    waiting_for_archive_debtors = State()
