from aiogram.fsm.state import StatesGroup, State

class TaskStates(StatesGroup):
    # Foydalanuvchi tizimga birinchi marta kirganda ism-familiyasini kutish
    waiting_for_user_name = State()       
    
    # Yangi vazifa yaratish bosqichlari (Siz aytgan ketma-ketlikda)
    waiting_for_target_role = State()     # 1. Qaysi unvonga biriktirishni kutish (Admin/Kassir/...)
    waiting_for_target_user = State()     # 2. Aniq qaysi xodimga biriktirishni kutish (Inline tugma)
    waiting_for_name = State()            # 3. Vazifa nomini kutish
    waiting_for_days = State()            # 4. Kunlarni tanlashni kutish
    waiting_for_frequency = State()       # 5. Kunlik takrorlanish chastotasini kutish
    waiting_for_once_time = State()       # 6A. Kuniga 1 marta bo'lsa, vaqtni kutish
    waiting_for_multiple_times = State()  # 6B. Bir necha marta bo'lsa, vaqtlar ro'yxatini kutish
    waiting_for_proof_type = State()      # 7. Isbot turini kutish (Dumaloq video/Rasm)
    
    # Xodim tomonidan vazifa bajarilganda rasm yoki videoni kutish
    waiting_for_task_proof = State()
