from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta, timezone
import calendar
import logging

from Keyboards.main_menu import get_main_menu, get_back_home_keyboard
from utils.access import check_user_access
from utils.attendance_db import (
    add_attendance,
    get_attendance_by_user_and_month,
    get_attendance_by_user_today,
    get_attendance_by_dates,
)
from utils.users_db import get_user_work_time

monitoring_router = Router()

TASHKENT_TZ = timezone(timedelta(hours=5))

# ================= GLOBAL O'ZGARUVCHILAR =================
USERS_ROLES = None


def init_monitoring_handler(users_roles):
    global USERS_ROLES
    USERS_ROLES = users_roles


# ================= STATES =================
class MonitoringStates(StatesGroup):
    waiting_for_late_time = State()
    waiting_for_late_reason = State()
    waiting_for_late_proof = State()
    waiting_for_role = State()
    waiting_for_employee_choice = State()
    waiting_for_period = State()
    waiting_for_custom_dates = State()


# ================= KEYBOARDS =================
def get_role_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Admin")],
            [types.KeyboardButton(text="Kassir")],
            [types.KeyboardButton(text="Sanitar")],
            [types.KeyboardButton(text="Manager")],
            [types.KeyboardButton(text="🏠 Bosh sahifa"), types.KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )


def get_employee_list_keyboard(role: str):
    keyboard = []
    employees = []
    
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == role and u_info.get("name"):
            employees.append((u_id, u_info["name"]))
    
    if not employees:
        return None
    
    keyboard.append([types.KeyboardButton(text="👥 Barcha xodimlar")])
    for u_id, name in employees:
        keyboard.append([types.KeyboardButton(text=f"👤 {name}")])
    
    keyboard.append([types.KeyboardButton(text="🏠 Bosh sahifa"), types.KeyboardButton(text="⬅️ Ortga")])
    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_period_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📅 Bugun")],
            [types.KeyboardButton(text="📅 Bu oy")],
            [types.KeyboardButton(text="📆 Sana (multiple select)")],
            [types.KeyboardButton(text="🏠 Bosh sahifa"), types.KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )


def get_late_proof_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📸 Rasm yuborish")],
            [types.KeyboardButton(text="📹 Video yuborish")],
            [types.KeyboardButton(text="✍️ Isbostsiz davom etish")],
            [types.KeyboardButton(text="🏠 Bosh sahifa"), types.KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )


# ================= HELPERS =================
def get_user_id_by_name(name: str):
    clean = name.replace("👤 ", "").strip()
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("name") == clean:
            return u_id
    return None


def get_all_users_by_role(role: str):
    users = []
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == role and u_info.get("name"):
            users.append((u_id, u_info["name"]))
    return users


def format_attendance_report(records: list, title: str) -> str:
    if not records:
        return f"{title}\n\n📭 Bu davr uchun kech qolish ma'lumotlari topilmadi."

    total_minutes = sum(r.get("late_minutes", 0) for r in records)
    hours, mins = divmod(total_minutes, 60)

    text = f"{title}\n\n"
    text += f"📊 Jami kech qolishlar soni: <b>{len(records)} ta</b>\n"
    text += f"⏱ Jami kechikish vaqti: <b>{hours} soat {mins} daqiqa</b>\n\n"
    text += "─────────────────────\n"

    for i, r in enumerate(records, 1):
        reason = r.get("reason") or "Ko'rsatilmagan"
        isbot = "Bor" if r.get("proof_file_id") else "Yo'q"
        text += (
            f"\n{i}. {r['date']}\n"
            f"   Kelgan vaqt: {r.get('arrived_at', 'Noma\'lum')}\n"
            f"   Kechikish: {r.get('late_minutes', 0)} daqiqa\n"
            f"   Sabab: {reason}\n"
            f"   Isbot: {isbot}\n"
        )

    return text


def get_all_days_in_current_month():
    now = datetime.now(TASHKENT_TZ)
    _, last_day = calendar.monthrange(now.year, now.month)
    dates = []
    for d in range(1, last_day + 1):
        dates.append(f"{now.year}-{now.month:02d}-{d:02d}")
    return dates


# ================= MONITORING ASOSIY MENU =================
@monitoring_router.message(F.text == "🎯 Monitoring")
async def monitoring_main_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    await state.clear()
    await state.set_state(MonitoringStates.waiting_for_role)
    await message.answer(
        text="🎯 <b>Monitoring</b>\n\nQaysi bo'lim xodimlarini ko'rmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_role_keyboard()
    )


# ================= ROLE TANLASH =================
@monitoring_router.message(MonitoringStates.waiting_for_role, F.text == "🏠 Bosh sahifa")
async def monitoring_role_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_role, F.text == "⬅️ Ortga")
async def monitoring_role_back(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_role, F.text.in_(["Admin", "Kassir", "Sanitar", "Manager"]))
async def monitoring_role_selected(message: types.Message, state: FSMContext):
    role = message.text
    employees = get_all_users_by_role(role)
    
    if not employees:
        await message.answer(f"📭 Tizimda {role} rolidagi xodimlar topilmadi.", reply_markup=get_role_keyboard())
        return
    
    await state.update_data(selected_role=role)
    await state.set_state(MonitoringStates.waiting_for_employee_choice)
    
    keyboard = get_employee_list_keyboard(role)
    await message.answer(
        text=f"👤 <b>{role}lardan birini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@monitoring_router.message(MonitoringStates.waiting_for_role)
async def invalid_role_selected(message: types.Message):
    await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_role_keyboard())


# ================= XODIM TANLASH =================
@monitoring_router.message(MonitoringStates.waiting_for_employee_choice, F.text == "🏠 Bosh sahifa")
async def monitoring_employee_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_employee_choice, F.text == "⬅️ Ortga")
async def monitoring_employee_back(message: types.Message, state: FSMContext):
    await state.set_state(MonitoringStates.waiting_for_role)
    await message.answer("Qaysi bo'lim xodimlarini ko'rmoqchisiz?", reply_markup=get_role_keyboard())


@monitoring_router.message(MonitoringStates.waiting_for_employee_choice, F.text == "👥 Barcha xodimlar")
async def monitoring_all_employees_selected(message: types.Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("selected_role")
    await state.update_data(selected_user_id="ALL", selected_name=f"Barcha {role}lar")
    await state.set_state(MonitoringStates.waiting_for_period)
    await message.answer(
        text="📅 <b>Qaysi davr uchun hisobot ko'rmoqchisiz?</b>",
        parse_mode="HTML",
        reply_markup=get_period_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_employee_choice, F.text.startswith("👤 "))
async def monitoring_employee_selected(message: types.Message, state: FSMContext):
    text = message.text.strip()
    uid = get_user_id_by_name(text)
    
    if not uid:
        data = await state.get_data()
        role = data.get("selected_role", "Admin")
        await message.answer("❌ Xodim topilmadi.", reply_markup=get_employee_list_keyboard(role))
        return
    
    name = text.replace("👤 ", "").strip()
    await state.update_data(selected_user_id=uid, selected_name=name)
    await state.set_state(MonitoringStates.waiting_for_period)
    await message.answer(
        text="📅 <b>Qaysi davr uchun hisobot ko'rmoqchisiz?</b>",
        parse_mode="HTML",
        reply_markup=get_period_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_employee_choice)
async def invalid_employee_selected(message: types.Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("selected_role", "Admin")
    await message.answer("❌ Iltimos, ro'yxatdan tanlang!", reply_markup=get_employee_list_keyboard(role))


# ================= DAVR TANLASH =================
@monitoring_router.message(MonitoringStates.waiting_for_period, F.text == "🏠 Bosh sahifa")
async def monitoring_period_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_period, F.text == "⬅️ Ortga")
async def monitoring_period_back(message: types.Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("selected_role", "Admin")
    await state.set_state(MonitoringStates.waiting_for_employee_choice)
    await message.answer(f"👤 {role}lardan birini tanlang:", reply_markup=get_employee_list_keyboard(role))


@monitoring_router.message(MonitoringStates.waiting_for_period, F.text == "📅 Bugun")
async def monitoring_period_today(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("selected_user_id")
    name = data.get("selected_name")
    today = datetime.now(TASHKENT_TZ).strftime("%Y-%m-%d")

    if uid == "ALL":
        await send_all_employees_report(message, today, today, f"📅 Bugungi ({today}) hisobot")
    else:
        records = await get_attendance_by_user_today(uid)
        report = format_attendance_report(records, f"📅 <b>{name} — Bugungi ({today}) hisobot</b>")
        await message.answer(report, parse_mode="HTML", reply_markup=get_period_keyboard())


@monitoring_router.message(MonitoringStates.waiting_for_period, F.text == "📅 Bu oy")
async def monitoring_period_this_month(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("selected_user_id")
    name = data.get("selected_name")
    now = datetime.now(TASHKENT_TZ)

    if uid == "ALL":
        dates = get_all_days_in_current_month()
        await send_all_employees_report(message, dates[0], dates[-1], f"📅 {now.year}-{now.month:02d} oylik hisobot")
    else:
        records = await get_attendance_by_user_and_month(uid, now.year, now.month)
        title = f"📅 <b>{name} — {now.year}-{now.month:02d} oylik hisobot</b>"
        report = format_attendance_report(records, title)
        await message.answer(report, parse_mode="HTML", reply_markup=get_period_keyboard())


@monitoring_router.message(MonitoringStates.waiting_for_period, F.text == "📆 Sana (multiple select)")
async def monitoring_period_custom(message: types.Message, state: FSMContext):
    await state.set_state(MonitoringStates.waiting_for_custom_dates)
    await message.answer(
        text=(
            "📆 <b>Sanalarni kiriting</b>\n\n"
            "Bir yoki bir nechta sanani vergul bilan ajratib yozing:\n"
            "Masalan: <code>2026-05-01, 2026-05-05, 2026-05-10</code>"
        ),
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_period)
async def invalid_period_selected(message: types.Message):
    await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_period_keyboard())


# ================= CUSTOM SANALAR =================
@monitoring_router.message(MonitoringStates.waiting_for_custom_dates, F.text == "🏠 Bosh sahifa")
async def monitoring_custom_dates_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_custom_dates, F.text == "⬅️ Ortga")
async def monitoring_custom_dates_back(message: types.Message, state: FSMContext):
    await state.set_state(MonitoringStates.waiting_for_period)
    await message.answer("Davr tanlang:", reply_markup=get_period_keyboard())


@monitoring_router.message(MonitoringStates.waiting_for_custom_dates)
async def monitoring_custom_dates_entered(message: types.Message, state: FSMContext):
    import re
    raw = message.text.strip()
    dates = [d.strip() for d in raw.split(",") if re.match(r"\d{4}-\d{2}-\d{2}", d.strip())]

    if not dates:
        await message.answer(
            "❌ Noto'g'ri format. Masalan: <code>2026-05-01, 2026-05-05</code>",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    uid = data.get("selected_user_id")
    name = data.get("selected_name")
    dates_str = ", ".join(dates)

    if uid == "ALL":
        await send_all_employees_report(message, dates[0], dates[-1], f"📆 Tanlangan sanalar: {dates_str}")
    else:
        records = await get_attendance_by_dates(uid, dates)
        title = f"📆 <b>{name} — {dates_str}</b>"
        report = format_attendance_report(records, title)
        await message.answer(report, parse_mode="HTML", reply_markup=get_period_keyboard())

    await state.set_state(MonitoringStates.waiting_for_period)


# ================= BARCHA XODIMLAR UCHUN HISOBOT =================
async def send_all_employees_report(message: types.Message, start_date: str, end_date: str, title: str):
    state = await message.bot.get_state(message.from_user.id)
    state_data = {}
    if state and state.data:
        state_data = state.data
    
    role = state_data.get("selected_role", "Admin")
    employees = get_all_users_by_role(role)
    
    if not employees:
        await message.answer("📭 Xodimlar topilmadi.", reply_markup=get_period_keyboard())
        return

    full_text = f"👥 <b>{title}</b>\n\n"
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_list = []
    current = start
    while current <= end:
        date_list.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    for uid, name in employees:
        records = await get_attendance_by_dates(uid, date_list)
        total_min = sum(r.get("late_minutes", 0) for r in records)
        h, m = divmod(total_min, 60)
        full_text += f"👤 <b>{name}</b>\n   📌 Kech qolishlar: {len(records)} ta\n   ⏱ Jami: {h} soat {m} daqiqa\n\n"

    await message.answer(full_text, parse_mode="HTML", reply_markup=get_period_keyboard())


# ================= KECH QOLISH =================
@monitoring_router.message(MonitoringStates.waiting_for_role, F.text == "⏰ Kech qolish")
@monitoring_router.message(F.text == "⏰ Kech qoldim")
async def late_start_handler(message: types.Message, state: FSMContext):
    await state.set_state(MonitoringStates.waiting_for_late_time)
    await message.answer(
        text=(
            "⏰ <b>Kech qolish vaqtini kiriting</b>\n\n"
            "Hozirgi kelgan vaqtingizni yozing:\n"
            "Masalan: <code>09:25</code>"
        ),
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_late_time, F.text == "🏠 Bosh sahifa")
async def late_time_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_late_time, F.text == "⬅️ Ortga")
async def late_time_back(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_late_time)
async def late_time_entered(message: types.Message, state: FSMContext):
    import re
    time_text = message.text.strip()
    if not re.match(r"^([0-1]?\d|2[0-3]):[0-5]\d$", time_text):
        await message.answer("❌ Noto'g'ri format. Masalan: <code>09:25</code>", parse_mode="HTML")
        return

    now = datetime.now(TASHKENT_TZ)
    user_id = str(message.from_user.id)
    
    work_start, work_end = await get_user_work_time(user_id)

    try:
        ws_h, ws_m = map(int, work_start.split(":"))
        ar_h, ar_m = map(int, time_text.split(":"))
        late_min = (ar_h * 60 + ar_m) - (ws_h * 60 + ws_m)
        late_min = max(0, late_min)
    except Exception:
        late_min = 0

    await state.update_data(
        arrived_at=time_text,
        late_minutes=late_min,
        late_date=now.strftime("%Y-%m-%d")
    )
    await state.set_state(MonitoringStates.waiting_for_late_reason)
    await message.answer(
        text=(
            f"⏰ Kelgan vaqt: <b>{time_text}</b> | "
            f"Ish boshlanish: <b>{work_start}</b> | "
            f"Kechikish: <b>{late_min} daqiqa</b>\n\n"
            "✍️ <b>Kech qolish sababini kiriting:</b>"
        ),
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_late_reason, F.text == "🏠 Bosh sahifa")
async def late_reason_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_late_reason, F.text == "⬅️ Ortga")
async def late_reason_back(message: types.Message, state: FSMContext):
    await state.set_state(MonitoringStates.waiting_for_late_time)
    await message.answer(
        "Kelgan vaqtingizni qayta kiriting (masalan: <code>09:25</code>):",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_late_reason)
async def late_reason_entered(message: types.Message, state: FSMContext):
    await state.update_data(reason=message.text.strip())
    await state.set_state(MonitoringStates.waiting_for_late_proof)
    await message.answer(
        text="📸 <b>Isbot yuborish (ixtiyoriy)</b>\n\nRasm yoki video yuboring, yoki isbotsiz davom eting:",
        parse_mode="HTML",
        reply_markup=get_late_proof_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_late_proof, F.text == "🏠 Bosh sahifa")
async def late_proof_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_late_proof, F.text == "⬅️ Ortga")
async def late_proof_back(message: types.Message, state: FSMContext):
    await state.set_state(MonitoringStates.waiting_for_late_reason)
    await message.answer("Sababni qayta kiriting:", reply_markup=get_back_home_keyboard())


@monitoring_router.message(MonitoringStates.waiting_for_late_proof)
async def late_proof_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = str(message.from_user.id)
    user_info = USERS_ROLES.get(user_id, {})
    user_name = user_info.get("name", message.from_user.full_name)
    role = user_info.get("role", "")

    proof_file_id = None
    proof_type = None

    if message.text == "✍️ Isbostsiz davom etish":
        pass
    elif message.photo:
        proof_file_id = message.photo[-1].file_id
        proof_type = "Photo"
    elif message.video_note:
        proof_file_id = message.video_note.file_id
        proof_type = "Video message"
    elif message.text in ("📸 Rasm yuborish", "📹 Video yuborish"):
        await message.answer(
            "Iltimos, rasm yoki video faylni to'g'ridan-to'g'ri yuboring:",
            reply_markup=get_late_proof_keyboard()
        )
        return

    record_id = await add_attendance(
        user_id=user_id,
        user_name=user_name,
        role=role,
        date=data.get("late_date"),
        arrived_at=data.get("arrived_at"),
        late_minutes=data.get("late_minutes", 0),
        reason=data.get("reason"),
        proof_file_id=proof_file_id,
        proof_type=proof_type,
    )

    await state.clear()

    if record_id:
        await message.answer(
            text=(
                f"✅ <b>Kech qolish ma'lumoti saqlandi!</b>\n\n"
                f"📅 Sana: <b>{data.get('late_date')}</b>\n"
                f"⏰ Kelgan vaqt: <b>{data.get('arrived_at')}</b>\n"
                f"⌛ Kechikish: <b>{data.get('late_minutes', 0)} daqiqa</b>\n"
                f"✍️ Sabab: {data.get('reason')}\n"
                f"📸 Isbot: {'✅ Yuborildi' if proof_file_id else '—'}"
            ),
            parse_mode="HTML",
            reply_markup=get_main_menu(role)
        )
    else:
        await message.answer(
            "❌ Saqlashda xatolik yuz berdi. Qayta urinib ko'ring.",
            reply_markup=get_main_menu(role)
        )
