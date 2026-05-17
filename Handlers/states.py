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
    
    # 🌟 YANGI: Kunlik (bir martalik) vazifa uchun izoh kutish holati
    waiting_for_description = State()     # Admin tomonidan izoh kiritilishini kutish

    # 🌟 YANGI FEATURE: Xodimlarni tahrirlash bosqichi
    waiting_for_edit_staff = State()
