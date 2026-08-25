from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta, timezone

from Keyboards.main_menu import get_main_menu
from utils.access import check_user_access
from utils.fines_db import (
    get_user_fines_for_month,
    get_user_active_fines_total,
    has_active_fine_in_month,
    get_fine_by_id,
    cancel_fine,
)
from utils.database import get_pool

fines_router = Router()

# ================= GLOBAL =================
USERS_ROLES = None
ADMIN_ID = None

TASHKENT_TZ = timezone(timedelta(hours=5))
BONUS_AMOUNT = 100000

def init_fines_panel_handler(users_roles, admin_id):
    global USERS_ROLES, ADMIN_ID
    USERS_ROLES = users_roles
    ADMIN_ID = admin_id


# ================= STATES =================
class FinesPanelStates(StatesGroup):
    # Xodim paneli
    emp_waiting_month = State()       # xodim oy tanlash
    emp_waiting_detail = State()      # xodim kechikishlar ro'yxati
    # Owner paneli
    owner_waiting_role = State()      # owner rol tanlash
    owner_waiting_employee = State()  # owner xodim tanlash
    owner_waiting_month = State()     # owner oy tanlash
    owner_waiting_edit_amount = State()  # owner yangi summa kiritish


# ================= YORDAMCHILAR =================
def get_month_options(base_year: int, base_month: int, count: int):
    """Oxirgi `count` oyni ro'yxatga oladi (joriy + o'tgan)"""
    months = []
    y, m = base_year, base_month
    for _ in range(count):
        months.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return months  # eng yangisidan eng eskasiga


def month_label(y: int, m: int):
    names = {1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel", 5: "May", 6: "Iyun",
             7: "Iyul", 8: "Avgust", 9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr"}
    return f"{names[m]} {y}"


def employees_of_role(role: str):
    result = []
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == role and u_info.get("name"):
            result.append((str(u_id), u_info["name"]))
    return sorted(result, key=lambda x: x[1])


def is_active_sql_fine(f):
    return f.get("status") == "active"


# ============================================================
#  XODIM PANELI — "💵 Bonus/Jarima" (Admin/Head Admin) va "💵 jarimalarim" (boshqa)
# ============================================================

@fines_router.message(F.text == "💵 Bonus/Jarima")
async def emp_bonus_jarima(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    await emp_show_month_choice(message, state)


@fines_router.message(F.text == "💵 jarimalarim")
async def emp_jarimalarim(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    await emp_show_month_choice(message, state)


async def emp_show_month_choice(message: types.Message, state: FSMContext):
    """Xodimga 2 oyni ko'rsatish (joriy + o'tgan)"""
    now = datetime.now(TASHKENT_TZ)
    months = get_month_options(now.year, now.month, 2)

    kb = []
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "")
    is_admin = role in ["Admin", "Head Admin"]
    label = "Bonus/Jarima" if is_admin else "jarimalarim"

    for y, m in months:
        kb.append([types.InlineKeyboardButton(text=f"📅 {month_label(y, m)}", callback_data=f"e_month_{y}_{m}")])
    kb.append([types.InlineKeyboardButton(text="❌ Yopish", callback_data="e_close")])

    await state.set_state(FinesPanelStates.emp_waiting_month)
    await message.answer(
        text=f"💵 <b>{label}</b>\n\nQaysi oydagi ma'lumotni ko'rmoqchisiz?",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )


@fines_router.callback_query(FinesPanelStates.emp_waiting_month, F.data.startswith("e_month_"))
async def emp_month_selected(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    y = int(parts[2])
    m = int(parts[3])
    user_id = str(call.from_user.id)
    u_info = USERS_ROLES.get(user_id, {})
    role = u_info.get("role", "")
    name = u_info.get("name", "Xodim")

    fines = await get_user_fines_for_month(user_id, y, m)
    active_total = sum(f["amount"] for f in fines if f["status"] == "active")
    has_fine = any(f["status"] == "active" for f in fines)
    is_admin = role in ["Admin", "Head Admin"]

    # Bonus sharti: Admin bo'lsa va faol jarima bo'lmasa
    is_admin = role == "Admin"
    bonus_elig = is_admin and not has_fine

    await call.message.delete()

    if is_admin:
        if bonus_elig:
            text = (
                f"💵 <b>{month_label(y, m)}</b>\n\n"
                f"Bonus: Tabriklaymiz 🙃 {BONUS_AMOUNT:,} UZS\n"
                f"Jarima: 0 UZS 😎"
            ).replace(",", " ")
            reply_markup = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🗓 Kechikishlar", callback_data=f"e_details_{y}_{m}")],
                [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="e_back")]
            ])
        else:
            text = (
                f"💵 <b>{month_label(y, m)}</b>\n\n"
                f"Bonus💰: 0 UZS\n"
                f"Jarima: {active_total:,} UZS\n"
            ).replace(",", " ")
            reply_markup = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🗓 Kechikishlar", callback_data=f"e_details_{y}_{m}")],
                [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="e_back")]
            ])
    else:
        text = (
            f"💵 <b>{month_label(y, m)}</b>\n\n"
            f"Jarimalarim: {active_total:,} UZS\n"
        ).replace(",", " ")
        kb = []
        if fines:
            kb.append([types.InlineKeyboardButton(text="🗓 Kechikishlar", callback_data=f"e_details_{y}_{m}")])
        kb.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="e_back")])
        reply_markup = types.InlineKeyboardMarkup(inline_keyboard=kb)

    await state.set_state(FinesPanelStates.emp_waiting_detail)
    await call.message.answer(text, parse_mode="HTML", reply_markup=reply_markup)
    await call.answer()


@fines_router.callback_query(FinesPanelStates.emp_waiting_detail, F.data.startswith("e_details_"))
async def emp_details(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    y = int(parts[2])
    m = int(parts[3])
    user_id = str(call.from_user.id)

    fines = await get_user_fines_for_month(user_id, y, m)

    await call.message.delete()
    if not fines:
        await call.message.answer(f"📭 <b>{month_label(y, m)}</b> — kechikishlar yo'q.", parse_mode="HTML")
    else:
        lines = [f"📅 <b>{month_label(y, m)} — kechikishlar/jarimalar</b>\n"]
        active_total = 0
        for f in fines:
            date_str = f["date"]
            amt = f["amount"]
            reason = "ishga chiqmagan" if f["reason"] == "absent" else f"kechikish ({f['late_minutes']} daq)"
            if f["status"] == "active":
                active_total += amt
                status_txt = f"💰 {amt:,} so'm".replace(",", " ")
            else:
                status_txt = "❌ bekor qilindi"
            lines.append(f"• {date_str} — {reason}: {status_txt}")
        lines.append(f"\n<b>Jami:</b> {active_total:,} so'm".replace(",", " "))
        await call.message.answer("\n".join(lines), parse_mode="HTML")

    await state.set_state(FinesPanelStates.emp_waiting_month)
    reply = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="e_back")]
    ])
    await call.message.answer("Nima qilamiz?", reply_markup=reply)
    await call.answer()


@fines_router.callback_query(F.data == "e_back")
async def emp_back(call: types.CallbackQuery, state: FSMContext):
    await emp_show_month_choice(call.message, state)
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer()


@fines_router.callback_query(F.data == "e_close")
async def emp_close(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(call.from_user.id), {}).get("role", "Owner")
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
    await call.answer()


# ============================================================
#  OWNER PANELI — "💵 Bonus&Jarima" (rol -> xodimlar -> 6 oy)
# ============================================================

VALID_ROLES = ["Admin", "Kassir", "Sanitar", "Manager", "Maintenance", "Head Admin", "Manager Assistant"]

@fines_router.message(F.text == "💵 Bonus&Jarima")
async def owner_bonus_jarima(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role")
    if role not in ["Owner", "Manager"]:
        return

    kb = []
    row = []
    for r in VALID_ROLES:
        row.append(types.InlineKeyboardButton(text=r, callback_data=f"orole_{r}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([types.InlineKeyboardButton(text="❌ Yopish", callback_data="o_close")])

    await state.set_state(FinesPanelStates.owner_waiting_role)
    await message.answer(
        text="💵 <b>Bonus&Jarima</b>\n\nBiror rolni tanlang:",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )


@fines_router.callback_query(FinesPanelStates.owner_waiting_role, F.data.startswith("orole_"))
async def owner_role_selected(call: types.CallbackQuery, state: FSMContext):
    role = call.data.split("_")[1]
    employees = employees_of_role(role)

    await call.message.delete()
    if not employees:
        await call.message.answer(f"⚠️ <b>{role}</b> rolida xodimlar topilmadi.")
        await call.answer()
        return

    kb = []
    for u_id, nm in employees:
        kb.append([types.InlineKeyboardButton(text=f"👤 {nm}", callback_data=f"oemp_{u_id}")])
    kb.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="o_back_role")])

    await state.update_data(owner_role=role)
    await state.set_state(FinesPanelStates.owner_waiting_employee)
    await call.message.answer(
        text=f"👥 <b>{role}</b> rolidagi xodimlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await call.answer()


@fines_router.callback_query(FinesPanelStates.owner_waiting_employee, F.data.startswith("oemp_"))
async def owner_employee_selected(call: types.CallbackQuery, state: FSMContext):
    u_id = call.data.split("_")[1]
    u_info = USERS_ROLES.get(u_id, {})
    name = u_info.get("name", "Xodim")
    role = u_info.get("role", "")

    # 6 oylik
    now = datetime.now(TASHKENT_TZ)
    months = get_month_options(now.year, now.month, 6)

    kb = []
    for y, m in months:
        kb.append([types.InlineKeyboardButton(text=f"📅 {month_label(y, m)}", callback_data=f"omonth_{y}_{m}")])
    kb.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="o_back_emp")])

    await state.update_data(owner_user=u_id, owner_user_name=name)
    await state.set_state(FinesPanelStates.owner_waiting_month)
    await call.message.delete()
    await call.message.answer(
        text=f"👤 <b>{name}</b> ({role})\n\nQaysi oy ma'lumotini ko'rmoqchisiz?",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await call.answer()


@fines_router.callback_query(FinesPanelStates.owner_waiting_month, F.data.startswith("omonth_"))
async def owner_month_selected(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    y = int(parts[1])
    m = int(parts[2])
    data = await state.get_data()
    u_id = data.get("owner_user")
    name = data.get("owner_user_name")
    u_info = USERS_ROLES.get(u_id, {})
    role = u_info.get("role", "")

    fines = await get_user_fines_for_month(u_id, y, m)
    active_total = sum(f["amount"] for f in fines if f["status"] == "active")
    has_fine = any(f["status"] == "active" for f in fines)
    is_admin = role in ["Admin", "Head Admin"]

    await call.message.delete()

    lines = [f"💵 <b>{name}</b> — {month_label(y, m)}\n"]
    if not fines:
        lines.append("Bu oyda kechikishlar yo'q.")
        if is_admin:
            lines.append(f"\n✅ {name} bu oyda umuman kech qolmadilar, natijada {BONUS_AMOUNT:,} bonusga ega bo'ldilar".replace(",", " "))
    else:
        for f in fines:
            date_str = f["date"]
            amt = f["amount"]
            rsn = "ishga chiqmagan" if f["reason"] == "absent" else (f"kechikish ({f['late_minutes']} daq)" if f["late_minutes"] else "xabar")
            if f["status"] == "active":
                lines.append(f"• {date_str} — {rsn}: 💰 {amt:,} so'm".replace(",", " "))
            else:
                lines.append(f"• {date_str} — {rsn}: {amt:,} so'm (❌ bekor qilingan)".replace(",", " "))
        if has_fine:
            lines.append(f"\n<b>Umumiy jarima:</b> {active_total:,} so'm".replace(",", " "))
        # Admin jarimasiz bo'lsa (lekin bekor qilinganlar bo'lsa) bonus bermaydi
        elif is_admin:
            lines.append(f"{name} bu oyda faol jarimaga ega emas.")
        else:
            lines.append(f"\n<b>Umumiy jarima:</b> 0 so'm")

    # Owner bekor/ozgartirish tugmalari (faol jarimalar uchun)
    active_kb = []
    for f in fines:
        if f["status"] == "active":
            active_kb.append([
                types.InlineKeyboardButton(text=f"✏️ #{f['date']} o'zgartirish", callback_data=f"oedit_{f['id']}"),
                types.InlineKeyboardButton(text=f"🗑 #{f['date']} bekor", callback_data=f"ocancel_{f['id']}")
            ])
    active_kb.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="o_back_month")])

    await state.set_state(FinesPanelStates.owner_waiting_month)
    await call.message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=active_kb) if fines else None
    )
    await call.answer()


# ================= OWNER ORTGA/JOPISH =================

@fines_router.callback_query(F.data == "o_back_role")
async def owner_back_to_role(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(FinesPanelStates.owner_waiting_role)
    kb = []
    row = []
    for r in VALID_ROLES:
        row.append(types.InlineKeyboardButton(text=r, callback_data=f"orole_{r}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([types.InlineKeyboardButton(text="❌ Yopish", callback_data="o_close")])
    await call.message.delete()
    await call.message.answer(
        text="💵 <b>Bonus&Jarima</b>\n\nBiror rolni tanlang:",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await call.answer()


@fines_router.callback_query(F.data == "o_back_emp")
async def owner_back_to_employee(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    role = data.get("owner_role", "Admin")
    employees = employees_of_role(role)
    kb = []
    for u_id, nm in employees:
        kb.append([types.InlineKeyboardButton(text=f"👤 {nm}", callback_data=f"oemp_{u_id}")])
    kb.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="o_back_role")])
    await state.set_state(FinesPanelStates.owner_waiting_employee)
    await call.message.delete()
    await call.message.answer(
        text=f"👥 <b>{role}</b> rolidagi xodimlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await call.answer()


@fines_router.callback_query(F.data == "o_back_month")
async def owner_back_to_month(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    u_id = data.get("owner_user")
    name = data.get("owner_user_name")
    now = datetime.now(TASHKENT_TZ)
    months = get_month_options(now.year, now.month, 6)
    kb = []
    for y, m in months:
        kb.append([types.InlineKeyboardButton(text=f"📅 {month_label(y, m)}", callback_data=f"omonth_{y}_{m}")])
    kb.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="o_back_emp")])
    await call.message.delete()
    await call.message.answer(
        text=f"👤 <b>{name}</b>\n\nQaysi oy ma'lumotini ko'rmoqchisiz?",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await call.answer()


@fines_router.callback_query(F.data == "o_close")
async def owner_close(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(call.from_user.id), {}).get("role", "Owner")
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
    await call.answer()


# ============================================================
#  JARIMA QISQARTIRISH / BEKOR QILISH (owner inline tugmalar)
#  callback: fine_edit_{id} / fine_cancel_{id} (monitoring dan)
#            oedit_{id} / ocancel_{id} (owner panelidan)
# ============================================================

@fines_router.callback_query(F.data.startswith("fine_cancel_"))
@fines_router.callback_query(F.data.startswith("ocancel_"))
async def fine_cancel_callback(call: types.CallbackQuery, state: FSMContext):
    # fine_cancel_123 yoki ocancel_123
    parts = call.data.split("_")
    fine_id = int(parts[-1])
    fine = await get_fine_by_id(fine_id)
    if not fine:
        await call.answer("Jarima topilmadi.")
        return

    await cancel_fine(fine_id)

    # Xodimga xabar yuborish
    try:
        await call.message.bot.send_message(
            chat_id=int(fine["user_id"]),
            text=f"Assalomu alaykum, {fine['user_name']}. Sizga belgilangan jarima ma'muriyat tomonidan bekor qilindi. E'tiboringiz uchun rahmat."
        )
    except Exception as e:
        import logging
        logging.error(f"Jarima bekor xabari xatolik: {e}")

    await call.answer("✅ Jarima bekor qilindi.")
    await call.message.delete()


@fines_router.callback_query(F.data.startswith("fine_edit_"))
@fines_router.callback_query(F.data.startswith("oedit_"))
async def fine_edit_callback(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    fine_id = int(parts[-1])
    fine = await get_fine_by_id(fine_id)
    if not fine:
        await call.answer("Jarima topilmadi.")
        return

    await state.update_data(edit_fine_id=fine_id, edit_user_id=fine["user_id"], edit_user_name=fine["user_name"])
    await state.set_state(FinesPanelStates.owner_waiting_edit_amount)
    await call.message.delete()
    await call.message.answer(
        text=f"✏️ <b>Jarimani o'zgartirish</b>\n\n"
             f"👤 {fine['user_name']}\n"
             f"📅 {fine['date']}\n"
             f"💰 Joriy summa: {fine['amount']:,} so'm\n\n"
             f"Yangi sumaani kiriting (so'mda):",
        parse_mode="HTML"
    )
    await call.answer()


@fines_router.message(FinesPanelStates.owner_waiting_edit_amount)
async def owner_enter_new_amount(message: types.Message, state: FSMContext):
    text = message.text.strip().replace(" ", "").replace(",", "").replace(".", "")
    if not text.isdigit() or int(text) <= 0:
        await message.answer("❌ Iltimos, musbat butun son kiriting (so'mda).")
        return

    new_amount = int(text)
    data = await state.get_data()
    _ = await state.get_state()

    # Agar absent (ishga chiqmaganlik) holatida bo'lsa — yangi fine qo'shiladi
    absent_user = data.get("absent_user")
    if absent_user:
        from utils.fines_db import add_fine
        fine_id = await add_fine(
            user_id=str(absent_user),
            user_name=data.get("absent_name", "Xodim"),
            role=data.get("absent_role", ""),
            date=data.get("absent_date", ""),
            late_minutes=0,
            amount=new_amount,
            reason="absent"
        )
        if fine_id:
            # Xodimga C-xabar
            try:
                await message.bot.send_message(
                    chat_id=int(absent_user),
                    text=f"Assalomu alaykum, {data.get('absent_name', 'Xodim')}. Sizni bugungi ishga kelmaganingiz sababli jarima belgilandi. Iltimos, kelajakda ish jadvaliga rioya qiling."
                )
            except Exception as e:
                import logging
                logging.error(f"Absent jarima xabari xatolik: {e}")
            role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
            await state.clear()
            await message.answer(
                text=f"✅ <b>{data.get('absent_name', 'Xodim')}</b> uchun ishga chiqmaganlik jarimasi <b>{new_amount:,} so'm</b> qo'yildi.".replace(",", " "),
                parse_mode="HTML",
                reply_markup=get_main_menu(role)
            )
        else:
            await message.answer("❌ Jarimani saqlashda xatolik. Qayta urinib ko'ring.")
        return

    # Oddiy (kechikish) jarima summasini yangilash
    fine_id = data.get("edit_fine_id")
    user_id = data.get("edit_user_id")
    user_name = data.get("edit_user_name")

    from utils.fines_db import cancel_fine as update_fine_amount
    await update_fine_amount(fine_id, new_amount)

    try:
        await message.bot.send_message(
            chat_id=int(user_id),
            text=f"Assalomu alaykum, {user_name}. Sizga jarima belgilangandi, biroq ma'muriyat tomonidan qayta ko'rib chiqilib, miqdori {new_amount} so'mga o'zgartirildi."
        )
    except Exception as e:
        import logging
        logging.error(f"Jarima o'zgarish xabari xatolik: {e}")

    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await state.clear()
    await message.answer(
        text=f"✅ Jarima summasi <b>{new_amount:,} so'm</b> ga o'zgartirildi.".replace(",", " "),
        parse_mode="HTML",
        reply_markup=get_main_menu(role)
    )


# ============================================================
#  ISHGA CHIQMAGANLIK — owner summa kiritadi (qo'lda)
#  callback: absent_fine_{user_id}_{date}
# ============================================================

@fines_router.callback_query(F.data.startswith("absent_fine_"))
async def absent_fine_callback(call: types.CallbackQuery, state: FSMContext):
    # absent_fine_{user_id}_{date}
    parts = call.data.split("_")
    # parts = ["absent","fine","{user_id}","{date}"]
    user_id = parts[2]
    date = parts[3] if len(parts) > 3 else ""
    u_info = USERS_ROLES.get(str(user_id), {})
    name = u_info.get("name", "Xodim")
    role = u_info.get("role", "")

    await state.update_data(absent_user=str(user_id), absent_name=name, absent_role=role, absent_date=date)
    await state.set_state(FinesPanelStates.owner_waiting_edit_amount)
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        text=f"🚫 <b>Ishga chiqmaganlik jarimasi</b>\n\n"
             f"👤 {name} ({role})\n"
             f"📅 {date}\n\n"
             f"Ishga chiqmaganlik uchun jarima summasini kiriting (so'mda):",
        parse_mode="HTML"
    )
    await call.answer()

