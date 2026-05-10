from aiogram.fsm.state import State, StatesGroup

class AdminSalaryStates(StatesGroup):
    fixed_salary = State()

    individual_kpi = State()
    conversion_kpi = State()
    active_kpi = State()

    bonus = State()
    penalty = State()

    confirm = State()
