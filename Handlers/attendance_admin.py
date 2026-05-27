from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from utils.access import check_user_access
from utils.attendance_db import clear_all_attendance
from Keyboards.main_menu import get_main_menu

attendance_admin_router = Router()

# ================= GLOBAL O'ZGARUVCHILAR =================
USERS_ROLES = None


def init_attendance_admin_handler(users_roles):
    global USERS_ROLES
    USERS_ROLES = users_roles


# ================= ATTENDANCE REMOVE HANDLER =================
@attendance_admin_router.message(F.text == "🗑 Attendance Remove")
async def attendance_remove_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    user_role = USERS_ROLES.get(str(message.from_user.id), {}).get("role")
    if user_role not in ["Owner", "Manager"]:
        await message.answer("⚠️ Bu buyruq faqat Owner va Manager uchun!")
        return
    
    # Tasdiqlash so'rash
    await state.set_state("waiting_attendance_confirm")
    await message.answer(
        text="⚠️ <b>DIQQAT!</b>\n\n"
             "Bu amal barcha foydalanuvchilarning 'Ishga keldim' tarixini butunlay o'chirib tashlaydi!\n\n"
             "O'chirishni tasdiqlaysizmi?\n\n"
             "✅ HA - o'chirish\n"
             "❌ YO'Q - bekor qilish",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="✅ HA"), types.KeyboardButton(text="❌ YO'Q")],
                [types.KeyboardButton(text="🏠 Bosh sahifa")]
            ],
            resize_keyboard=True
        )
    )


@attendance_admin_router.message(lambda msg: msg.text in ["✅ HA", "❌ YO'Q", "🏠 Bosh sahifa"])
async def attendance_remove_confirm(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != "waiting_attendance_confirm":
        return
    
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
        return
    
    if message.text == "❌ YO'Q":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("❌ Bekor qilindi. Hech qanday ma'lumot o'chirilmadi.", reply_markup=get_main_menu(role))
        return
    
    if message.text == "✅ HA":
        # O'chirishni bajarish
        deleted_count = await clear_all_attendance()
        
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        
        if deleted_count > 0:
            await message.answer(
                text=f"✅ <b>Muvaffaqiyatli o'chirildi!</b>\n\n"
                     f"📊 Jami {deleted_count} ta yozuv o'chirildi.\n\n"
                     f"Barcha 'Ishga keldim' tarixi tozalandi.",
                parse_mode="HTML",
                reply_markup=get_main_menu(role)
            )
        else:
            await message.answer(
                text="ℹ️ O'chiriladigan ma'lumot topilmadi. Baza allaqachon bo'sh.",
                reply_markup=get_main_menu(role)
            )
