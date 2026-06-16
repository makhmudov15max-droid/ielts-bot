from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

from Keyboards.main_menu import get_main_menu, get_back_home_keyboard
from utils.access import check_user_access
from utils.holidays_db import (
    add_holidays_bulk,
    get_all_holidays,
    update_holiday,
    delete_holiday,
    get_holiday_by_id,
    delete_all_holidays,
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
    waiting_for_holidays_bulk = State()       # Bir nechta ta'til kiritish (yangi)
    waiting_for_holiday_edit_select = State() # Qaysi ta'tilni o'zgartirish
    waiting_for_holiday_edit_name = State()   # Yangi nom
    waiting_for_holiday_edit_date = State()   # Yangi sana
    waiting_for_delete_all_confirm = State()  # Barcha ta'tilni o'chirish tasdiqlash


# ================= YORDAMCHI FUNKSIYALAR =================
def parse_date_input(date_str: str):
    """
    Foydalanuvchi kiritgan sanani tekshiradi va DB uchun formatga o'tkazadi.
    Qabul qilinadi: DD-MM-YYYY yoki DD-MM
    Qaytaradi: (db_date, is_repeat) yoki (None, None) — xato bo'lsa
    """
    date_str = date_str.strip()
    # DD-MM-YYYY — faqat o'sha yil uchun
    full = re.match(r"^(\d{2})-(\d{2})-(\d{4})$", date_str)
    # DD-MM — har yili takrorlanadi
    repeat = re.match(r"^(\d{2})-(\d{2})$", date_str)

    if full:
        dd, mm, yyyy = full.group(1), full.group(2), full.group(3)
        return f"{yyyy}-{mm}-{dd}", False   # DB da YYYY-MM-DD saqlaymiz
    elif repeat:
        dd, mm = repeat.group(1), repeat.group(2)
        return f"{mm}-{dd}", True           # DB da MM-DD saqlaymiz
    return None, None


def display_date(db_date: str) -> str:
    """DB dagi sana formatini (YYYY-MM-DD yoki MM-DD) ko'rsatish formatiga o'tkazadi."""
    parts = db_date.split("-")
    if len(parts) == 3:
        # YYYY-MM-DD -> DD-MM-YYYY
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    elif len(parts) == 2:
        # MM-DD -> DD-MM
        return f"{parts[1]}-{parts[0]}"
    return db_date


def parse_bulk_input(text: str):
    """
    Bir nechta ta'til kiritishni parse qiladi.
    Format (har qatorda): Bayram nomi / DD-MM-YYYY yoki DD-MM
    Qaytaradi: (list of (name, db_date, is_repeat), errors)
    """
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    results = []
    errors = []

    for i, line in enumerate(lines, 1):
        if "/" not in line:
            errors.append(f"  {i}-qator: <code>{line}</code> — '/' belgisi topilmadi")
            continue

        parts = line.split("/", 1)
        name = parts[0].strip()
        date_raw = parts[1].strip()

        if len(name) < 2:
            errors.append(f"  {i}-qator: nom juda qisqa — «{name}»")
            continue

        db_date, is_repeat = parse_date_input(date_raw)
        if db_date is None:
            errors.append(
                f"  {i}-qator: noto'g'ri sana <code>{date_raw}</code> "
                f"(to'g'ri: <code>01-01</code> yoki <code>01-01-2026</code>)"
            )
            continue

        results.append((name, db_date, is_repeat))

    return results, errors


# ================= KEYBOARDS =================
def get_holiday_action_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🇺🇿 O'zbekiston bayramlari")],
            [types.KeyboardButton(text="📝 Ta'til kiritish"), types.KeyboardButton(text="✏️ Ta'til o'zgartirish")],
            [types.KeyboardButton(text="🗑 Barcha ta'tilni o'chirish")],
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


# ================= ASOSIY MENU TUGMALARI =================
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


# ================= O'ZBEKISTON BAYRAMLARI PRESET =================
UZBEKISTAN_HOLIDAYS = [
    # Qat'iy bayramlar (har yili takrorlanadi) — DD-MM format
    ("Mustaqillik kuni", "01-09", True),
    ("O'qituvchi va murabbiylar kuni", "01-10", True),
    ("Yangi yil", "01-01", True),
    ("Xotin-qizlar kuni", "08-03", True),
    ("Xotira va qadrlash kuni", "09-05", True),
    # Hayit bayramlari (2026 yil, taxminiy) — DD-MM-YYYY format
    ("Ramazon Hayit (1-kun) ⚠️", "2026-03-20", False),
    ("Ramazon Hayit (2-kun) ⚠️", "2026-03-21", False),
    ("Ramazon Hayit (3-kun) ⚠️", "2026-03-22", False),
    ("Qurbon Hayit (1-kun) ⚠️", "2026-05-25", False),
    ("Qurbon Hayit (2-kun) ⚠️", "2026-05-26", False),
    ("Qurbon Hayit (3-kun) ⚠️", "2026-05-27", False),
]


@holidays_router.message(HolidayStates.waiting_for_action, F.text == "🇺🇿 O'zbekiston bayramlari")
async def holiday_preset_uzbekistan(message: types.Message, state: FSMContext):
    """O'zbekiston bayramlarini bir klikda qo'shish"""
    saved, skipped = await add_holidays_bulk(UZBEKISTAN_HOLIDAYS)

    await message.answer(
        text=(
            f"🇺🇿 <b>O'zbekiston bayramlari qo'shildi!</b>\n\n"
            f"✅ Yangi qo'shilgan: <b>{saved}</b> ta\n"
            f"⏭ O'tkazib yuborilgan (allaqachon mavjud): <b>{skipped}</b> ta\n\n"
            f"⚠️ <b>Hayit sanalari taxminiy.</b> Aniq sana e'lon qilingach,\n"
            f"✏️ Ta'til o'zgartirish orqali yangilang."
        ),
        parse_mode="HTML",
        reply_markup=get_holiday_action_keyboard()
    )
@holidays_router.message(HolidayStates.waiting_for_action, F.text == "📝 Ta'til kiritish")
async def holiday_add_start(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_holidays_bulk)
    await message.answer(
        text=(
            "✍️ <b>Ta'tillarni kiriting</b>\n\n"
            "Har bir ta'tilni <b>yangi qatorga</b> yozing:\n"
            "<code>Bayram nomi / sana</code>\n\n"
            "📅 <b>Sana formatlari:</b>\n"
            "• <code>DD-MM</code> — har yili takrorlanadi\n"
            "• <code>DD-MM-YYYY</code> — faqat o'sha yil uchun\n\n"
            "📌 <b>Misol:</b>\n"
            "<code>Yangi yil / 01-01\n"
            "Navro'z / 21-03\n"
            "Mustaqillik kuni / 01-09-2026</code>"
        ),
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
        repeat_mark = "🔁" if h["is_repeat"] else "📆"
        text += f"{idx}. {repeat_mark} {h['name']} — {display_date(h['date'])}\n"

    text += "\n✏️ O'zgartirmoqchi bo'lgan ta'tilning <b>raqamini</b> yuboring:"

    await message.answer(text=text, parse_mode="HTML", reply_markup=get_back_home_keyboard())



@holidays_router.message(HolidayStates.waiting_for_action, F.text == "🗑 Barcha ta'tilni o'chirish")
async def holiday_delete_all_start(message: types.Message, state: FSMContext):
    holidays = await get_all_holidays()
    if not holidays:
        await message.answer(
            "📭 O'chiradigan ta'til yo'q.",
            reply_markup=get_holiday_action_keyboard()
        )
        return

    await state.set_state(HolidayStates.waiting_for_delete_all_confirm)

    text = f"⚠️ <b>Diqqat!</b> Quyidagi <b>{len(holidays)} ta ta'til</b> butunlay o'chiriladi:\n\n"
    for h in holidays:
        repeat_mark = "🔁" if h["is_repeat"] else "📆"
        text += f"  {repeat_mark} {h['name']} — {display_date(h['date'])}\n"
    text += "\n✅ Tasdiqlaysizmi?"

    confirm_kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="✅ Ha, o'chirilsin"), types.KeyboardButton(text="❌ Yo'q, bekor")],
        ],
        resize_keyboard=True
    )
    await message.answer(text=text, parse_mode="HTML", reply_markup=confirm_kb)


@holidays_router.message(HolidayStates.waiting_for_delete_all_confirm, F.text == "✅ Ha, o'chirilsin")
async def holiday_delete_all_confirm(message: types.Message, state: FSMContext):
    count = await delete_all_holidays()
    await state.clear()
    await message.answer(
        text=f"✅ <b>{count} ta ta'til o'chirildi.</b>",
        parse_mode="HTML",
        reply_markup=get_holiday_action_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_delete_all_confirm, F.text == "❌ Yo'q, bekor")
async def holiday_delete_all_cancel(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_action)
    await message.answer(
        "❌ Bekor qilindi.",
        reply_markup=get_holiday_action_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_delete_all_confirm)
async def holiday_delete_all_invalid(message: types.Message):
    await message.answer("❌ Iltimos, tugmalardan birini tanlang!")

@holidays_router.message(HolidayStates.waiting_for_action)
async def invalid_action_selected(message: types.Message):
    await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_holiday_action_keyboard())


# ================= TA'TIL KIRITISH — BULK =================
@holidays_router.message(HolidayStates.waiting_for_holidays_bulk, F.text == "🏠 Bosh sahifa")
async def holiday_bulk_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_holidays_bulk, F.text == "⬅️ Ortga")
async def holiday_bulk_back(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_action)
    await message.answer(
        text="🌴 <b>Ta'tillarni boshqarish</b>\n\nQanday amalni bajarmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_holiday_action_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_holidays_bulk)
async def holiday_bulk_entered(message: types.Message, state: FSMContext):
    parsed, errors = parse_bulk_input(message.text)

    # Xatolar bo'lsa — ko'rsatib, to'xtatamiz
    if errors:
        err_text = "❌ <b>Quyidagi qatorlarda xatolik bor:</b>\n\n" + "\n".join(errors)
        if parsed:
            err_text += f"\n\n✅ To'g'ri qatorlar: {len(parsed)} ta — ular ham saqlanmadi."
        err_text += (
            "\n\n📌 <b>To'g'ri format:</b>\n"
            "<code>Bayram nomi / DD-MM</code>  yoki\n"
            "<code>Bayram nomi / DD-MM-YYYY</code>\n\n"
            "Iltimos, barcha ta'tillarni qayta yuboring:"
        )
        await message.answer(err_text, parse_mode="HTML")
        return

    if not parsed:
        await message.answer(
            "❌ Hech qanday ta'til topilmadi.\n\n"
            "📌 <b>Format:</b> <code>Bayram nomi / DD-MM</code>\n"
            "Har bir ta'til yangi qatorda bo'lishi kerak.",
            parse_mode="HTML"
        )
        return

    # Hammasini bazaga saqlaymiz
    saved, skipped = await add_holidays_bulk(parsed)

    await state.clear()

    lines = []
    for name, db_date, is_repeat in parsed:
        repeat_mark = "🔁" if is_repeat else "📆"
        lines.append(f"  {repeat_mark} {name} — {display_date(db_date)}")

    summary = "\n".join(lines)
    text = f"✅ <b>{saved} ta ta'til saqlandi!</b>\n\n{summary}"
    if skipped:
        text += f"\n\n⚠️ {skipped} ta ta'til allaqachon mavjud edi (o'tkazib yuborildi)."

    await message.answer(text=text, parse_mode="HTML", reply_markup=get_holiday_action_keyboard())


# ================= TA'TIL O'ZGARTIRISH — SELECT =================
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
        await state.update_data(
            selected_holiday_id=selected["id"],
            selected_holiday_name=selected["name"],
            selected_holiday_date=selected["date"]
        )
        await state.set_state(HolidayStates.waiting_for_holiday_edit_name)

        await message.answer(
            text=f"✏️ <b>Ta'tilni o'zgartirish</b>\n\n"
                 f"Joriy: <b>{selected['name']}</b> — {display_date(selected['date'])}\n\n"
                 f"📌 Yangi ta'til nomini kiriting\n"
                 f"(o'zgarishsiz qoldirish uchun <code>0</code>):",
            parse_mode="HTML",
            reply_markup=get_back_home_keyboard()
        )
    except ValueError:
        await message.answer("❌ Iltimos, faqat raqam kiriting!")


# ================= TA'TIL O'ZGARTIRISH — NOM =================
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
        repeat_mark = "🔁" if h["is_repeat"] else "📆"
        text += f"{idx}. {repeat_mark} {h['name']} — {display_date(h['date'])}\n"
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
        text=f"📅 Yangi sanani kiriting\n\n"
             f"• <code>DD-MM</code> — har yili takrorlanadi\n"
             f"• <code>DD-MM-YYYY</code> — faqat o'sha yil uchun\n\n"
             f"Joriy sana: <b>{display_date(current_date)}</b>\n"
             f"(o'zgarishsiz qoldirish uchun <code>0</code>):",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


# ================= TA'TIL O'ZGARTIRISH — SANA =================
@holidays_router.message(HolidayStates.waiting_for_holiday_edit_date, F.text == "🏠 Bosh sahifa")
async def holiday_edit_date_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@holidays_router.message(HolidayStates.waiting_for_holiday_edit_date, F.text == "⬅️ Ortga")
async def holiday_edit_date_back(message: types.Message, state: FSMContext):
    await state.set_state(HolidayStates.waiting_for_holiday_edit_name)
    await message.answer(
        text="📌 Ta'til nomini qayta kiriting (yoki o'zgarishsiz qoldirish uchun <code>0</code>):",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@holidays_router.message(HolidayStates.waiting_for_holiday_edit_date)
async def holiday_edit_date_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    holiday_id = data.get("selected_holiday_id")
    new_name = data.get("edit_holiday_name")
    current_date = data.get("selected_holiday_date")

    raw = message.text.strip()
    if raw == "0":
        new_db_date = current_date
    else:
        new_db_date, _ = parse_date_input(raw)
        if new_db_date is None:
            await message.answer(
                text="❌ <b>Noto'g'ri format!</b>\n\n"
                     "• <code>DD-MM</code> (masalan: <code>01-01</code>)\n"
                     "• <code>DD-MM-YYYY</code> (masalan: <code>01-09-2026</code>)",
                parse_mode="HTML"
            )
            return

    final_name = new_name if new_name else data.get("selected_holiday_name")
    result = await update_holiday(holiday_id, final_name, new_db_date)

    await state.clear()

    if result:
        await message.answer(
            text=f"✅ <b>Ta'til muvaffaqiyatli o'zgartirildi!</b>\n\n"
                 f"📌 Nom: {final_name}\n"
                 f"📅 Sana: {display_date(new_db_date)}",
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
            text="✅ Ta'til muvaffaqiyatli o'chirildi!",
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
             f"Joriy: <b>{holiday['name']}</b> — {display_date(holiday['date'])}\n\n"
             f"📌 Yangi ta'til nomini kiriting\n"
             f"(o'zgarishsiz qoldirish uchun <code>0</code>):",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )
    await call.answer()
