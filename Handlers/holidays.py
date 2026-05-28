from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

from Keyboards.main_menu import get_main_menu, get_back_home_keyboard
from utils.access import check_user_access
from utils.holidays_db import (
    add_holiday_for_all,
    get_all_holidays,
    update_holiday,
    delete_holiday,
    get_holiday_by_id,
)

holidays_router = Router()

# ================= GLOBAL O'ZGARUVCHILAR =================
USERS_ROLES = None


def init_holidays_handler(users_roles):
    global USERS_ROLES
    USERS_ROLES = users_roles


# ================= STATES =================
class HolidayStates(StatesGroup):
    waiting_for_action = State()              # Ta'til kiritish / o'zgartirish
    waiting_for_holiday_name = State()        # Ta'til nomi
    waiting_for_holiday_date = State()        # Ta'til sanasi
    waiting_for_holiday_edit_select = State() # Qaysi ta'tilni o'zgartirish
    waiting_for_holiday_edit_name = State()   # Yangi nom
    waiting_for_holiday_edit_date = State()   # Yangi sana


# ================= KEYBOARDS =================
def get_holiday_action_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📝 Ta'til kiritish"), types.KeyboardButton(text="✏️ Ta'til o'zgartirish")],
            [types.KeyboardButton(text="🏠 Bosh sahifa"), types.KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )


# ================= TA'TILLAR ASOSIY HANDLER =================
@holidays_router.message(F.text == "🌴 Ta'tillar")
async def holidays_main_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    await state.set_state(HolidayStates.waiting_for_action)
    await message.answer(
        text="🌴 <b>Ta'tillarni boshqarish</b>\n\nQanday amalni bajarmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_holiday_action_keyboard()
    )


# ================= ASOSIY MENU TUGMALARI (waiting_for_action) =================
@holidays_router.message(HolidayStates.waiting_for_action, F.text == "🏠 Bosh sahifa")
async def holidays_action_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_action, F.text == "⬅️ Ortga")
async def holidays_action_back(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_action, F.text == "📝 Ta'til kiritish")
async def holiday_add_start(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_holiday_name)
    await message.answer(
        text="✍️ <b>Yangi ta'til ma'lumotlarini kiriting</b>\n\n"
             "📌 Ta'til nomini kiriting:\n"
             "Masalan: Navro'z bayrami",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_action, F.text == "✏️ Ta'til o'zgartirish")
async def holiday_edit_start(message: types.Message, state: FSMContext):
    holidays = await get_all_holidays()
    
    if not holidays:
        await message.answer(
            text="📭 Hech qanday ta'til topilmadi.\n\n🆕 Yangi ta'til qo'shish uchun '📝 Ta'til kiritish' tugmasini bosing.",
            reply_markup=get_holiday_action_keyboard()
        )
        return
    
    await state.update_data(holidays_list=holidays)
    await state.set_state(HolidayStates.waiting_for_holiday_edit_select)
    
    text = "📅 <b>Joriy ta'tillar ro'yxati:</b>\n\n"
    for idx, h in enumerate(holidays, 1):
        text += f"{idx}. {h['name']} - {h['date']}\n"
    
    text += "\n✏️ O'zgartirmoqchi bo'lgan ta'tilning raqamini yuboring:"
    
    await message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_action)
async def invalid_action_selected(message: types.Message):
    await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_holiday_action_keyboard())


# ================= TA'TIL KIRITISH (waiting_for_holiday_name) =================
@holidays_router.message(HolidayStates.waiting_for_holiday_name, F.text == "🏠 Bosh sahifa")
async def holiday_add_name_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_holiday_name, F.text == "⬅️ Ortga")
async def holiday_add_name_back(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_action)
    await message.answer(
        text="🌴 <b>Ta'tillarni boshqarish</b>\n\nQanday amalni bajarmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_holiday_action_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_holiday_name)
async def holiday_add_name_entered(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Ta'til nomi kamida 2 harfdan iborat bo'lishi kerak!")
        return
    
    await state.update_data(holiday_name=name)
    await state.set_state(HolidayStates.waiting_for_holiday_date)
    await message.answer(
        text="📅 <b>Ta'til sanasini kiriting (YYYY-MM-DD formatida)</b>\n\n"
             "Masalan: <code>2026-03-21</code>",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


# ================= TA'TIL KIRITISH (waiting_for_holiday_date) =================
@holidays_router.message(HolidayStates.waiting_for_holiday_date, F.text == "🏠 Bosh sahifa")
async def holiday_add_date_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_holiday_date, F.text == "⬅️ Ortga")
async def holiday_add_date_back(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_holiday_name)
    await message.answer(
        text="📌 Ta'til nomini qayta kiriting:",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_holiday_date)
async def holiday_add_date_entered(message: types.Message, state: FSMContext):
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer("❌ Noto'g'ri format! Iltimos, YYYY-MM-DD formatida kiriting.\nMasalan: <code>2026-03-21</code>", parse_mode="HTML")
        return
    
    data = await state.get_data()
    holiday_name = data.get("holiday_name")
    
    # Barcha xodimlar uchun ta'til qo'shish
    result = await add_holiday_for_all(holiday_name, date_text)
    
    await state.clear()
    if result and result > 0:
        await message.answer(
            text=f"✅ <b>Ta'til muvaffaqiyatli qo'shildi!</b>\n\n"
                 f"📌 Ta'til: {holiday_name}\n"
                 f"📅 Sana: {date_text}\n\n"
                 f"👥 {result} ta xodimga qo'shildi.",
            parse_mode="HTML",
            reply_markup=get_holiday_action_keyboard()
        )
    else:
        await message.answer("❌ Saqlashda xatolik yuz berdi. Qayta urinib ko'ring.", reply_markup=get_holiday_action_keyboard())


# ================= TA'TIL O'ZGARTIRISH (waiting_for_holiday_edit_select) =================
@holidays_router.message(HolidayStates.waiting_for_holiday_edit_select, F.text == "🏠 Bosh sahifa")
async def holiday_edit_select_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_holiday_edit_select, F.text == "⬅️ Ortga")
async def holiday_edit_select_back(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_action)
    await message.answer(
        text="🌴 <b>Ta'tillarni boshqarish</b>\n\nQanday amalni bajarmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_holiday_action_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_holiday_edit_select)
async def holiday_edit_select_handler(message: types.Message, state: FSMContext):
    try:
        idx = int(message.text.strip()) - 1
        data = await state.get_data()
        holidays = data.get("holidays_list", [])
        
        if idx < 0 or idx >= len(holidays):
            await message.answer("❌ Noto'g'ri raqam! Iltimos, ro'yxatdagi raqamni kiriting.")
            return
        
        selected = holidays[idx]
        await state.update_data(selected_holiday_id=selected["id"], selected_holiday_name=selected["name"], selected_holiday_date=selected["date"])
        await state.set_state(HolidayStates.waiting_for_holiday_edit_name)
        
        await message.answer(
            text=f"✏️ <b>Ta'tilni o'zgartirish</b>\n\n"
                 f"Joriy: {selected['name']} - {selected['date']}\n\n"
                 f"📌 Yangi ta'til nomini kiriting (yoki o'zgarishsiz qoldirish uchun '0'):",
            parse_mode="HTML",
            reply_markup=get_back_home_keyboard()
        )
    except ValueError:
        await message.answer("❌ Iltimos, faqat raqam kiriting!")


# ================= TA'TIL O'ZGARTIRISH (waiting_for_holiday_edit_name) =================
@holidays_router.message(HolidayStates.waiting_for_holiday_edit_name, F.text == "🏠 Bosh sahifa")
async def holiday_edit_name_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_holiday_edit_name, F.text == "⬅️ Ortga")
async def holiday_edit_name_back(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_holiday_edit_select)
    data = await state.get_data()
    holidays = data.get("holidays_list", [])
    text = "📅 <b>Joriy ta'tillar ro'yxati:</b>\n\n"
    for idx, h in enumerate(holidays, 1):
        text += f"{idx}. {h['name']} - {h['date']}\n"
    text += "\n✏️ O'zgartirmoqchi bo'lgan ta'tilning raqamini yuboring:"
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_home_keyboard())


@holidays_router.message(HolidayStates.waiting_for_holiday_edit_name)
async def holiday_edit_name_handler(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    if new_name == "0":
        new_name = None
    elif len(new_name) < 2:
        await message.answer("❌ Ta'til nomi kamida 2 harfdan iborat bo'lishi kerak!")
        return
    
    await state.update_data(edit_holiday_name=new_name)
    await state.set_state(HolidayStates.waiting_for_holiday_edit_date)
    
    data = await state.get_data()
    current_date = data.get("selected_holiday_date")
    
    await message.answer(
        text=f"📅 Yangi sanani kiriting (YYYY-MM-DD formatida)\n\n"
             f"Joriy sana: {current_date}\n"
             f"(o'zgarishsiz qoldirish uchun '0' yozing):",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


# ================= TA'TIL O'ZGARTIRISH (waiting_for_holiday_edit_date) =================
@holidays_router.message(HolidayStates.waiting_for_holiday_edit_date, F.text == "🏠 Bosh sahifa")
async def holiday_edit_date_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_holiday_edit_date, F.text == "⬅️ Ortga")
async def holiday_edit_date_back(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_holiday_edit_name)
    await message.answer(
        text="📌 Ta'til nomini qayta kiriting (yoki o'zgarishsiz qoldirish uchun '0'):",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_holiday_edit_date)
async def holiday_edit_date_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    holiday_id = data.get("selected_holiday_id")
    new_name = data.get("edit_holiday_name")
    current_date = data.get("selected_holiday_date")
    
    new_date = message.text.strip()
    if new_date == "0":
        new_date = current_date
    elif not re.match(r"\d{4}-\d{2}-\d{2}", new_date):
        await message.answer("❌ Noto'g'ri format! Iltimos, YYYY-MM-DD formatida kiriting.")
        return
    
    final_name = new_name if new_name else data.get("selected_holiday_name")
    
    result = await update_holiday(holiday_id, final_name, new_date)
    
    await state.clear()
    
    if result:
        await message.answer(
            text=f"✅ <b>Ta'til muvaffaqiyatli o'zgartirildi!</b>\n\n"
                 f"📌 Yangi nom: {final_name}\n"
                 f"📅 Yangi sana: {new_date}\n\n"
                 f"⚠️ Eslatma: O'zgartirish barcha xodimlar uchun amal qiladi.",
            parse_mode="HTML",
            reply_markup=get_holiday_action_keyboard()
        )
    else:
        await message.answer("❌ Saqlashda xatolik yuz berdi. Qayta urinib ko'ring.", reply_markup=get_holiday_action_keyboard())


# ================= TA'TIL O'CHIRISH (CALLBACK) =================
@holidays_router.callback_query(F.data.startswith("holiday_delete_"))
async def holiday_delete_callback(call: types.CallbackQuery, state: FSMContext):
    holiday_id = int(call.data.split("_")[2])
    result = await delete_holiday(holiday_id)
    
    if result:
        await call.answer("✅ Ta'til o'chirildi!")
        await call.message.delete()
        await call.message.answer(
            text="✅ Ta'til muvaffaqiyatli o'chirildi!\n\n⚠️ Eslatma: O'chirish barcha xodimlar uchun amal qiladi.",
            reply_markup=get_holiday_action_keyboard()
        )
    else:
        await call.answer("❌ O'chirishda xatolik yuz berdi!", show_alert=True)
    
    await state.clear()


@holidays_router.callback_query(F.data.startswith("holiday_edit_"))
async def holiday_edit_callback(call: types.CallbackQuery, state: FSMContext):
    holiday_id = int(call.data.split("_")[2])
    holiday = await get_holiday_by_id(holiday_id)
    
    if not holiday:
        await call.answer("❌ Ta'til topilmadi!", show_alert=True)
        return
    
    await state.update_data(
        selected_holiday_id=holiday["id"],
        selected_holiday_name=holiday["name"],
        selected_holiday_date=holiday["date"]
    )
    await state.set_state(HolidayStates.waiting_for_holiday_edit_name)
    
    await call.message.delete()
    await call.message.answer(
        text=f"✏️ <b>Ta'tilni o'zgartirish</b>\n\n"
             f"Joriy: {holiday['name']} - {holiday['date']}\n\n"
             f"📌 Yangi ta'til nomini kiriting (yoki o'zgarishsiz qoldirish uchun '0'):",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )
    await call.answer()
