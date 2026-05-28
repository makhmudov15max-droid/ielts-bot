from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

from Keyboards.main_menu import get_main_menu, get_back_home_keyboard
from utils.access import check_user_access
from utils.holidays_db import (
    add_holiday,
    get_holidays_by_user,
    get_holidays_by_role,
    update_holiday,
    delete_holiday,
)

holidays_router = Router()

# ================= GLOBAL O'ZGARUVCHILAR =================
USERS_ROLES = None


def init_holidays_handler(users_roles):
    global USERS_ROLES
    USERS_ROLES = users_roles


# ================= STATES =================
class HolidayStates(StatesGroup):
    waiting_for_role = State()
    waiting_for_employee = State()
    waiting_for_holiday_action = State()
    waiting_for_holiday_name = State()
    waiting_for_holiday_date = State()
    waiting_for_holiday_edit_select = State()
    waiting_for_holiday_edit_name = State()
    waiting_for_holiday_edit_date = State()


# ================= KEYBOARDS =================
def get_holiday_role_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Admin"), types.KeyboardButton(text="Kassir")],
            [types.KeyboardButton(text="Sanitar"), types.KeyboardButton(text="Manager")],
            [types.KeyboardButton(text="🏠 Bosh sahifa"), types.KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )


def get_holiday_action_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📝 Ta'til kiritish"), types.KeyboardButton(text="✏️ Ta'til o'zgartirish")],
            [types.KeyboardButton(text="🏠 Bosh sahifa"), types.KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )


def get_holiday_edit_keyboard(holiday_id: int):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="✏️ O'zgartirish", callback_data=f"holiday_edit_{holiday_id}"),
             types.InlineKeyboardButton(text="❌ O'chirish", callback_data=f"holiday_delete_{holiday_id}")]
        ]
    )


def get_all_users_by_role(role: str):
    users = []
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == role and u_info.get("name"):
            users.append((u_id, u_info["name"]))
    return users


def get_user_id_by_name(name: str):
    clean = name.replace("👤 ", "").strip()
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("name") == clean:
            return u_id
    return None


def get_employee_list_keyboard(role: str):
    keyboard = []
    employees = get_all_users_by_role(role)
    if not employees:
        return None
    keyboard.append([types.KeyboardButton(text="👥 Barcha xodimlar")])
    for u_id, name in employees:
        keyboard.append([types.KeyboardButton(text=f"👤 {name}")])
    keyboard.append([types.KeyboardButton(text="🏠 Bosh sahifa"), types.KeyboardButton(text="⬅️ Ortga")])
    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ================= TA'TILLAR ASOSIY HANDLER =================
@holidays_router.message(F.text == "🌴 Ta'tillar")
async def holidays_main_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    await state.set_state(HolidayStates.waiting_for_role)
    await message.answer(
        text="🌴 <b>Ta'tillar boshqaruvi</b>\n\nQaysi bo'lim xodimlarining ta'tillarini ko'rmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_holiday_role_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_role, F.text == "🏠 Bosh sahifa")
async def holidays_role_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_role, F.text == "⬅️ Ortga")
async def holidays_role_back(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_role, F.text.in_(["Admin", "Kassir", "Sanitar", "Manager"]))
async def holidays_role_selected(message: types.Message, state: FSMContext):
    role = message.text
    employees = get_all_users_by_role(role)
    
    if not employees:
        await message.answer(f"📭 Tizimda {role} rolidagi xodimlar topilmadi.", reply_markup=get_holiday_role_keyboard())
        return
    
    await state.update_data(selected_role=role)
    await state.set_state(HolidayStates.waiting_for_employee)
    
    keyboard = get_employee_list_keyboard(role)
    await message.answer(
        text=f"👥 <b>{role}</b> rolidagi xodimlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@holidays_router.message(HolidayStates.waiting_for_role)
async def invalid_role_selected(message: types.Message):
    await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_holiday_role_keyboard())


# ================= XODIM TANLASH =================
@holidays_router.message(HolidayStates.waiting_for_employee, F.text == "🏠 Bosh sahifa")
async def holidays_employee_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_employee, F.text == "⬅️ Ortga")
async def holidays_employee_back(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_role)
    await message.answer("Qaysi bo'lim xodimlarining ta'tillarini ko'rmoqchisiz?", reply_markup=get_holiday_role_keyboard())


@holidays_router.message(HolidayStates.waiting_for_employee, F.text == "👥 Barcha xodimlar")
async def holidays_all_employees_selected(message: types.Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("selected_role")
    await state.update_data(selected_user_id="ALL", selected_user_name=f"Barcha {role}lar")
    await state.set_state(HolidayStates.waiting_for_holiday_action)
    await message.answer(
        text="🌴 <b>Ta'tillar boshqaruvi</b>\n\nQanday amalni bajarmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_holiday_action_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_employee, F.text.startswith("👤 "))
async def holidays_employee_selected(message: types.Message, state: FSMContext):
    text = message.text.strip()
    uid = get_user_id_by_name(text)
    
    if not uid:
        data = await state.get_data()
        role = data.get("selected_role", "Admin")
        await message.answer("❌ Xodim topilmadi.", reply_markup=get_employee_list_keyboard(role))
        return
    
    name = text.replace("👤 ", "").strip()
    await state.update_data(selected_user_id=uid, selected_user_name=name)
    await state.set_state(HolidayStates.waiting_for_holiday_action)
    await message.answer(
        text="🌴 <b>Ta'tillar boshqaruvi</b>\n\nQanday amalni bajarmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_holiday_action_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_employee)
async def invalid_employee_selected(message: types.Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("selected_role", "Admin")
    await message.answer("❌ Iltimos, ro'yxatdan tanlang!", reply_markup=get_employee_list_keyboard(role))


# ================= TA'TIL KIRITISH =================
@holidays_router.message(HolidayStates.waiting_for_holiday_action, F.text == "📝 Ta'til kiritish")
async def holiday_add_start(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_holiday_name)
    await message.answer(
        text="✍️ <b>Yangi ta'til ma'lumotlarini kiriting</b>\n\n"
             "📌 Ta'til nomini kiriting:\n"
             "Masalan: Navro'z bayrami",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_holiday_name, F.text == "🏠 Bosh sahifa")
async def holiday_add_name_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_holiday_name, F.text == "⬅️ Ortga")
async def holiday_add_name_back(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_holiday_action)
    await message.answer(
        text="🌴 <b>Ta'tillar boshqaruvi</b>\n\nQanday amalni bajarmoqchisiz?",
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


@holidays_router.message(HolidayStates.waiting_for_holiday_date)
async def holiday_add_date_entered(message: types.Message, state: FSMContext):
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer("❌ Noto'g'ri format! Iltimos, YYYY-MM-DD formatida kiriting.\nMasalan: <code>2026-03-21</code>", parse_mode="HTML")
        return
    
    data = await state.get_data()
    user_id = data.get("selected_user_id")
    user_name = data.get("selected_user_name")
    role = data.get("selected_role", "")
    holiday_name = data.get("holiday_name")
    
    # Barcha xodimlar uchun
    if user_id == "ALL":
        employees = get_all_users_by_role(role)
        count = 0
        for uid, uname in employees:
            result = await add_holiday(uid, uname, role, holiday_name, date_text)
            if result:
                count += 1
        await state.clear()
        await message.answer(
            text=f"✅ <b>{count} ta xodimga ta'til qo'shildi!</b>\n\n"
                 f"📌 Ta'til: {holiday_name}\n"
                 f"📅 Sana: {date_text}",
            parse_mode="HTML",
            reply_markup=get_holiday_role_keyboard()
        )
    else:
        result = await add_holiday(user_id, user_name, role, holiday_name, date_text)
        await state.clear()
        if result:
            await message.answer(
                text=f"✅ <b>Ta'til muvaffaqiyatli qo'shildi!</b>\n\n"
                     f"👤 Xodim: {user_name}\n"
                     f"📌 Ta'til: {holiday_name}\n"
                     f"📅 Sana: {date_text}",
                parse_mode="HTML",
                reply_markup=get_holiday_role_keyboard()
            )
        else:
            await message.answer("❌ Saqlashda xatolik yuz berdi. Qayta urinib ko'ring.", reply_markup=get_holiday_role_keyboard())


# ================= TA'TIL O'ZGARTIRISH =================
@holidays_router.message(HolidayStates.waiting_for_holiday_action, F.text == "✏️ Ta'til o'zgartirish")
async def holiday_edit_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("selected_user_id")
    role = data.get("selected_role", "")
    
    if user_id == "ALL":
        holidays = await get_holidays_by_role(role)
    else:
        holidays = await get_holidays_by_user(user_id)
    
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


@holidays_router.message(HolidayStates.waiting_for_holiday_edit_select)
async def holiday_edit_select_handler(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
        return
    
    if message.text == "⬅️ Ortga":
        await state.set_state(HolidayStates.waiting_for_holiday_action)
        await message.answer(
            text="🌴 <b>Ta'tillar boshqaruvi</b>\n\nQanday amalni bajarmoqchisiz?",
            parse_mode="HTML",
            reply_markup=get_holiday_action_keyboard()
        )
        return
    
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


@holidays_router.message(HolidayStates.waiting_for_holiday_edit_name)
async def holiday_edit_name_handler(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
        return
    
    if message.text == "⬅️ Ortga":
        await state.set_state(HolidayStates.waiting_for_holiday_edit_select)
        data = await state.get_data()
        holidays = data.get("holidays_list", [])
        text = "📅 <b>Joriy ta'tillar ro'yxati:</b>\n\n"
        for idx, h in enumerate(holidays, 1):
            text += f"{idx}. {h['name']} - {h['date']}\n"
        text += "\n✏️ O'zgartirmoqchi bo'lgan ta'tilning raqamini yuboring:"
        await message.answer(text, parse_mode="HTML", reply_markup=get_back_home_keyboard())
        return
    
    new_name = message.text.strip()
    if new_name == "0":
        new_name = None
    
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


@holidays_router.message(HolidayStates.waiting_for_holiday_edit_date)
async def holiday_edit_date_handler(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
        return
    
    if message.text == "⬅️ Ortga":
        await state.set_state(HolidayStates.waiting_for_holiday_edit_name)
        await message.answer("📌 Ta'til nomini qayta kiriting (yoki o'zgarishsiz qoldirish uchun '0'):", reply_markup=get_back_home_keyboard())
        return
    
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
                 f"📅 Yangi sana: {new_date}",
            parse_mode="HTML",
            reply_markup=get_holiday_role_keyboard()
        )
    else:
        await message.answer("❌ Saqlashda xatolik yuz berdi. Qayta urinib ko'ring.", reply_markup=get_holiday_role_keyboard())


# ================= TA'TIL O'CHIRISH (CALLBACK) =================
@holidays_router.callback_query(F.data.startswith("holiday_delete_"))
async def holiday_delete_callback(call: types.CallbackQuery, state: FSMContext):
    holiday_id = int(call.data.split("_")[2])
    result = await delete_holiday(holiday_id)
    
    if result:
        await call.answer("✅ Ta'til o'chirildi!")
        await call.message.delete()
        await call.message.answer(
            text="✅ Ta'til muvaffaqiyatli o'chirildi!",
            reply_markup=get_holiday_role_keyboard()
        )
    else:
        await call.answer("❌ O'chirishda xatolik yuz berdi!", show_alert=True)
    
    await state.clear()


@holidays_router.callback_query(F.data.startswith("holiday_edit_"))
async def holiday_edit_callback(call: types.CallbackQuery, state: FSMContext):
    holiday_id = int(call.data.split("_")[2])
    
    from utils.holidays_db import get_holiday_by_id
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
