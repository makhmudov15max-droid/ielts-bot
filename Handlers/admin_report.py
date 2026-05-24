from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from Keyboards.main_menu import (
    get_main_menu,
    get_back_home_keyboard,
    get_admin_report_main_keyboard,
    get_employee_list_keyboard
)
from utils.access import check_user_access

admin_report_router = Router()

# Global o'zgaruvchilar
USERS_ROLES = None


def init_admin_report_handler(users_roles):
    global USERS_ROLES
    USERS_ROLES = users_roles


class AdminReportStates(StatesGroup):
    waiting_for_admin_choice = State()
    waiting_for_report_action = State()


@admin_report_router.message(F.text == "📊 Admin Hisobot")
async def admin_report_main_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    await state.clear()
    await state.set_state(AdminReportStates.waiting_for_admin_choice)
    await message.answer(
        text="📊 <b>Admin Hisobot paneli</b>\n\n"
             "Quyidagi bo'limlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=get_admin_report_main_keyboard()
    )


@admin_report_router.message(AdminReportStates.waiting_for_admin_choice, F.text == "👤 Bitta admin")
async def admin_report_single_admin_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    # Admin rolidagi xodimlarni olish
    employees = []
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == "Admin" and u_info.get("name"):
            employees.append({"id": u_id, "name": u_info["name"]})
    
    if not employees:
        await message.answer(
            text="📭 Hozircha tizimda Admin rolidagi xodimlar mavjud emas.",
            reply_markup=get_back_home_keyboard()
        )
        return
    
    await state.update_data(admin_list=employees)
    await state.set_state(AdminReportStates.waiting_for_report_action)
    await message.answer(
        text="👤 <b>Admin tanlang:</b>\n\n"
             "Hisobot ko'rmoqchi bo'lgan adminni tanlang:",
        parse_mode="HTML",
        reply_markup=get_employee_list_keyboard(employees)
    )


@admin_report_router.message(AdminReportStates.waiting_for_report_action, F.text.startswith("👤 "))
async def admin_report_show_handler(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
        return
    elif message.text == "⬅️ Ortga":
        await state.set_state(AdminReportStates.waiting_for_admin_choice)
        await message.answer(
            text="📊 <b>Admin Hisobot paneli</b>\n\n"
                 "Quyidagi bo'limlardan birini tanlang:",
            parse_mode="HTML",
            reply_markup=get_admin_report_main_keyboard()
        )
        return
    
    # Admin nomini olish
    employee_name = message.text.replace("👤 ", "").strip()
    
    # Hisobot logikasi keyin qo'shiladi
    await message.answer(
        text=f"📊 <b>{employee_name} uchun hisobot</b>\n\n"
             "⚠️ Bu funksiya hozircha ishlab chiqilmoqda.\n\n"
             "📅 Oy davomidagi ish kunlari soni\n"
             "❌ Ish qoldirgan sanalar\n"
             "⏰ Kechikishlar\n"
             "⌛ Jami kechikish vaqti\n"
             "🔥 Current streak\n"
             "🏆 Best streak\n\n"
             "Tez orada qo'shiladi.",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@admin_report_router.message(AdminReportStates.waiting_for_admin_choice, F.text == "🔥 Streak System")
async def admin_report_streak_system_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    # Barcha xodimlarni olish (Owner va rejected dan tashqari)
    employees = []
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("name") and u_info.get("role") not in ["Owner", "rejected"]:
            employees.append({"id": u_id, "name": u_info["name"], "role": u_info["role"]})
    
    if not employees:
        await message.answer(
            text="📭 Hozircha tizimda xodimlar mavjud emas.",
            reply_markup=get_back_home_keyboard()
        )
        return
    
    await state.clear()
    
    # Streak logikasi keyin qo'shiladi
    response_text = "🔥 <b>Streak System</b>\n\n"
    for emp in employees:
        response_text += f"👤 {emp['name']} ({emp['role']})\n"
        response_text += f"   🔥 Current streak: --\n"
        response_text += f"   🏆 Best streak: --\n\n"
    
    response_text += "\n⚠️ Bu funksiya hozircha ishlab chiqilmoqda. Tez orada qo'shiladi."
    
    await message.answer(
        text=response_text,
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@admin_report_router.message(AdminReportStates.waiting_for_admin_choice, F.text == "🏠 Bosh sahifa")
async def admin_report_back_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@admin_report_router.message(AdminReportStates.waiting_for_admin_choice, F.text == "⬅️ Ortga")
async def admin_report_back_main(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
