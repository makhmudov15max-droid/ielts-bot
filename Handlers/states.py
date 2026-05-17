from aiogram.fsm.state import StatesGroup, State

# Tizim bosqichlari
class TaskStates(StatesGroup):
    waiting_for_user_name = State()       # Foydalanuvchi ism-familiyasini kutish
    waiting_for_name = State()            # Vazifa nomini kutish holati
    waiting_for_days = State()            # Kunlarni tanlashni kutish holati
    waiting_for_frequency = State()       # Kunlik takrorlanish sonini kutish holati
    waiting_for_once_time = State()       # Bitta aniq vaqtni matn ko'rinishida kutish
    waiting_for_multiple_times = State()  # Bir nechta vaqtni vergul bilan kutish
    
    # --- YANGI QO'SHILGAN FEATURE BOSQICHLARI ---
    waiting_for_proof_type = State()      # Isbot turini kutish (Photo/Video)
    waiting_for_target_role = State()     # Qaysi unvonga biriktirishni kutish
    waiting_for_target_user = State()     # Aniq qaysi xodimga biriktirishni kutish
    waiting_for_task_proof = State()      # Xodim tomonidan rasm yoki videoni kutish
    
    # YANGI: Kunlik (bir martalik) vazifa uchun izoh kutish holati
    waiting_for_description = State()     # Admin tomonidan izoh kiritilishini kutish

    # YANGI FEATURE: Xodimlarni tahrirlash bosqichi
    waiting_for_edit_staff = State()       
    
    # YANGI FEATURE: Arxivni boshqarish bosqichi
    waiting_for_archive_staff = State()    
    
    # YANGI FEATURE: Oyliklarni boshqarish bosqichi
    waiting_for_salary_management = State()

# ADMIN OYLIK HISOBLASH BOSQICHLARI
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

# Kassir oylik bosqichlari
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
