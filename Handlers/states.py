from aiogram.fsm.state import StatesGroup, State

class TaskStates(StatesGroup):
    # Asosiy state lar
    waiting_for_user_name = State()
    waiting_for_name = State()
    waiting_for_days = State()
    waiting_for_frequency = State()
    waiting_for_once_time = State()
    waiting_for_multiple_times = State()
    
    # Vazifa yaratish
    waiting_for_proof_type = State()
    waiting_for_target_role = State()
    waiting_for_target_user = State()
    waiting_for_task_proof = State()
    waiting_for_description = State()

    # Xodimlarni tahrirlash
    waiting_for_edit_staff = State()
    waiting_for_new_name = State()
    
    # Arxiv
    waiting_for_archive_staff = State()
    
    # Oylik
    waiting_for_salary_management = State()
    
    # Isbotlar
    waiting_for_proof_role = State()
    waiting_for_proof_user = State()
    waiting_for_proof_date = State()
    
    # Vazifalar ro'yxati (YANGI)
    waiting_for_tasks_list_choice = State()
    waiting_for_completed_date = State()


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


class CashierSalaryStates(StatesGroup):
    hours = State()
    custom_hours = State()
    days = State()
    custom_days = State()
    cover = State()
    cover_hours = State()
    missed = State()
    missed_hours = State()
    active_students = State()
    active_debtors = State()
    archive_students = State()
    archive_debtors = State()
