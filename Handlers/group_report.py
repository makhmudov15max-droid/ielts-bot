import os, io, re, json, logging, asyncio
from datetime import datetime, timezone, timedelta
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import config

logger = logging.getLogger(__name__)

report_router = Router()

from utils.group_comments_db import get_comment, set_comment, delete_comment, get_all_comments

try:
    ADMIN_ID = int(config.ADMIN_ID)
except:
    ADMIN_ID = 6500594896


# ================= STATES =================
class ReportStates(StatesGroup):
    waiting_for_report_choice = State()
    waiting_for_teacher_choice = State()
    waiting_for_comment_input = State()
    waiting_for_comment_delete_confirm = State()
    waiting_for_cashbox_detail = State()


# ================= GLOBAL O'ZGARUVCHI =================
_USERS_ROLES = None

def set_users_roles(users_roles):
    global _USERS_ROLES
    _USERS_ROLES = users_roles


async def is_admin(user_id: int) -> bool:
    if _USERS_ROLES:
        user_info = _USERS_ROLES.get(str(user_id))
        if user_info:
            role = user_info.get("role")
            if role in ["Admin", "Owner", "Manager", "Manager Assistant"]:
                return True
    from utils.users_db import get_user_role
    role = await get_user_role(str(user_id))
    return role in ["Admin", "Owner", "Manager", "Manager Assistant"]


# ================= LMS CONFIG =================
LMS_BASE = "https://main.ieltszoneapp.uz"
LMS_EMAIL = config.LMS_EMAIL if hasattr(config, 'LMS_EMAIL') else "makhmudov15max@gmail.com"
LMS_KEY = config.LMS_KEY if hasattr(config, 'LMS_KEY') else os.getenv("LMS_KEY", "1qa2ws3ed")

DRUJBA_BRANCH_ID = 3
IELTS_COURSE_IDS = {7, 8, 9, 10, 12, 15}  # Novice, Standard, Expert, Intensive, Practice, Speaking
UZ_TZ = timezone(timedelta(hours=5))

# Cache
_lms_session = None
_teacher_map = {}
_course_map = {}
_cached_groups = None
_cached_groups_time = 0
CACHE_TTL = 60  # sekund


def _get_lms_session():
    """LMS sessiyasini yaratish yoki qayta ishlatish"""
    global _lms_session, _teacher_map, _course_map

    import requests
    from urllib.parse import unquote
    from html import unescape

    # Agar sessiya mavjud bo'lsa, tekshirib ko'rish
    if _lms_session:
        try:
            r = _lms_session.get(f"{LMS_BASE}/admin/dashboard", timeout=10)
            if r.status_code == 200 and "data-page" in r.text:
                return _lms_session
        except:
            pass

    # Yangi sessiya
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
    })
    s.get(f"{LMS_BASE}/sanctum/csrf-cookie")
    xsrf = s.cookies.get("XSRF-TOKEN", "")
    s.headers["X-XSRF-TOKEN"] = unquote(xsrf)
    s.headers["Content-Type"] = "application/json"
    s.post(f"{LMS_BASE}/admin/login", json={"email": LMS_EMAIL, "password": LMS_KEY})

    # Get teacher + course maps
    if not _teacher_map or not _course_map:
        try:
            r = s.get(f"{LMS_BASE}/admin/unassessed-groups?per_page=1")
            match = re.search(r'data-page="([^"]*)"', r.text)
            if match:
                dp = json.loads(unescape(match.group(1)))
                for c in dp["props"]["courseOptions"]:
                    _course_map[c["id"]] = c["name"].get("uz", c["name"].get("en", ""))
                for t in dp["props"]["teacherOptions"]:
                    _teacher_map[t["id"]] = f"{t.get('first_name','')} {t.get('last_name','')}".strip()

            # Also get from calculated-salaries (all employees)
            r = s.get(f"{LMS_BASE}/admin/calculated-salaries?per_page=200")
            match = re.search(r'data-page="([^"]*)"', r.text)
            if match:
                dp = json.loads(unescape(match.group(1)))
                for emp in dp["props"]["employees"]:
                    if emp["id"] not in _teacher_map:
                        _teacher_map[emp["id"]] = f"{emp.get('first_name','')} {emp.get('last_name','')}".strip()
        except Exception as e:
            logger.warning(f"LMS maps fetch error: {e}")

    _lms_session = s
    return s


def get_all_groups():
    """LMS export orqali barcha Drujba IELTS guruhlarni olish (aktiv + kutilayotgan)"""
    global _cached_groups, _cached_groups_time
    import time

    # Cache ishlatish — 60 soniya davomida qayta yuklanmaydi
    now = time.time()
    if _cached_groups is not None and (now - _cached_groups_time) < CACHE_TTL:
        logger.info(f"LMS cache: {len(_cached_groups)} groups ({(now - _cached_groups_time):.0f}s old)")
        return _cached_groups

    import openpyxl

    try:
        s = _get_lms_session()
        r = s.get(f"{LMS_BASE}/admin/groups/export", timeout=30)
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        ws = wb.active

        headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
        name_col = headers.index("Ism") + 1
        start_col = headers.index("Guruhning boshlanish sanasi") + 1
        end_col = headers.index("craftable-pro.Group End Date") + 1
        status_col = headers.index("Status") + 1
        course_col = headers.index("Kurs Id") + 1
        teacher_col = headers.index("craftable-pro.Teacher Id") + 1
        branch_col = headers.index("Fillial Id") + 1

        today = datetime.now(UZ_TZ).date()
        groups = []

        for row_idx in range(2, ws.max_row + 1):
            bid = ws.cell(row_idx, branch_col).value
            if bid != DRUJBA_BRANCH_ID:
                continue

            cid = ws.cell(row_idx, course_col).value
            if cid not in IELTS_COURSE_IDS:
                continue

            status = ws.cell(row_idx, status_col).value
            if status not in {1, 2}:  # 1=draft/kutilmoqda, 2=aktiv
                continue

            # Teacher ID dan nom olish
            tid = ws.cell(row_idx, teacher_col).value
            tname = _teacher_map.get(tid, f"ID#{tid}") if tid else ""

            # Draft guruhlarda teacher=None bo'lsa, nomidan ajratish
            if not tname or tname.startswith("ID#"):
                gname = str(ws.cell(row_idx, name_col).value or "")
                for _, map_name in sorted(_teacher_map.items(), key=lambda x: -len(x[1])):
                    if map_name.lower() in gname.lower():
                        tname = map_name
                        break

            # Agar teacher aniqlanmasa, guruhni tashlab ketamiz
            if not tname:
                continue

            cname = _course_map.get(cid, f"ID#{cid}")

            start_str = str(ws.cell(row_idx, start_col).value or "")
            start_fmt = ""
            if start_str and start_str != "None":
                try:
                    start_fmt = datetime.strptime(start_str[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
                except:
                    pass

            # End date va days_left
            end_str = str(ws.cell(row_idx, end_col).value or "")
            end_fmt = ""
            days_left = 999
            if end_str and end_str != "None":
                try:
                    end_dt = datetime.strptime(end_str[:10], "%Y-%m-%d").date()
                    end_fmt = end_dt.strftime("%d.%m.%Y")
                    days_left = (end_dt - today).days
                except:
                    pass

            # Status text
            if status == 1:
                status_text = "🗓 Kutilmoqda"
            else:
                status_text = "🟢 Aktiv guruh"

            groups.append({
                "teacher": tname,
                "group_name": str(ws.cell(row_idx, name_col).value or ""),
                "level": cname,
                "start_date": start_fmt,
                "end_date": end_fmt,
                "days_left": days_left,
                "status": status_text,
                "comment": "",
            })

        logger.info(f"LMS: {len(groups)} Drujba IELTS groups loaded (including upcoming)")
        _cached_groups = groups
        _cached_groups_time = time.time()
        return groups

    except Exception as e:
        logger.error(f"LMS get_all_groups error: {e}")
        # Xato bo'lsa, eski cached ma'lumotni qaytarish (agar bor bo'lsa)
        if _cached_groups is not None:
            logger.info("Returning stale cache due to error")
            return _cached_groups
        return []


def get_unique_teachers():
    """Barcha Drujba IELTS ustozlarini qaytaradi: LMS teacher_map + export'dagilar."""
    groups = get_all_groups()
    export_teachers = set(g["teacher"] for g in groups if g["teacher"] and not g["teacher"].startswith("ID#"))

    # _teacher_map dan hamma ustozlarni olish (employees + teacherOptions)
    map_teachers = set()
    # employees da "Test" yoki "Demo" bilan boshlanadiganlarni filtrlab olamiz
    # va faqat haqiqiy ism-familya bo'lganlarni
    for tid, name in _teacher_map.items():
        name = name.strip()
        if not name or name == "None":
            continue
        # Test/Demo akkauntlarni o'tkazib yuborish
        if name.lower().startswith(("test", "demo", "old", "call")):
            continue
        # "None" so'zi bilan tugaganlarni
        if name.endswith(" None"):
            name = name[:-5].strip()
            if not name:
                continue
        # 1 so'zdan iborat bo'lganlar (faqat ism, familyasiz) — odatda test akkauntlar
        if len(name.split()) == 1 and len(name) < 5:
            continue
        map_teachers.add(name)

    # Hamma ustozlarni birlashtirish
    all_teachers = sorted(set(list(export_teachers) + list(map_teachers)))
    return all_teachers


def get_teacher_scores():
    """Google Sheets 'Ustozlar' varag'idan {ism: IELTS ball} lug'atini qaytaradi"""
    try:
        import gspread
        creds_json = os.getenv("GOOGLE_CREDS")
        if not creds_json:
            logger.warning("GOOGLE_CREDS topilmadi — ustoz IELTS ballari tekshirilmaydi")
            return {}
        creds = json.loads(creds_json)
        client = gspread.service_account_from_dict(creds)
        ws = client.open("EduControl").worksheet("Ustozlar")
        vals = ws.get_all_values()
        scores = {}
        for row in vals[1:]:
            if len(row) >= 3:
                name = row[1].strip()
                try:
                    scores[name] = float(row[2])
                except ValueError:
                    pass
        return scores
    except Exception as e:
        logger.warning(f"Google Sheets IELTS scores olishda xato: {e}")
        return {}


def format_date_with_hint(date_str: str) -> str:
    if not date_str:
        return date_str
    try:
        parsed = datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
        today = datetime.now(UZ_TZ).date()
        diff = (parsed - today).days
        if diff == 0:
            return f"Bugun ({date_str})"
        elif diff == 1:
            return f"Ertaga ({date_str})"
        elif diff > 1:
            return f"{diff} kundan keyin ({date_str})"
        else:
            return date_str
    except:
        return date_str


IELTS_LEVELS = ["IELTS Standart", "IELTS Practie", "IELTS Bridge", "IELTS Ekspert", "IELTS Intensiv"]
ACTIVE_STATUSES = ["Aktiv guruh", "Guruh"]


# ================= ASOSIY MENU =================
@report_router.message(F.text == "🌐 LMS")
async def group_report_menu(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat administrator va owner uchun!")
        return

    # Owner ro'li tekshirish
    role = _USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner") if _USERS_ROLES else "Owner"

    await state.set_state(ReportStates.waiting_for_report_choice)

    # Cashbox va Finance Report faqat Owner uchun
    if role == "Owner":
        lms_buttons = [
            [types.KeyboardButton(text="📊 Finishing Groups"), types.KeyboardButton(text="👨🏻‍🏫 Ustoz bo'yicha"), types.KeyboardButton(text="⏳ Waiting Groups")],
            [types.KeyboardButton(text="🏦 Cashbox"), types.KeyboardButton(text="💰 Finance Report"), types.KeyboardButton(text="📋 Dars Jadval")],
            [types.KeyboardButton(text="🏠 Bosh sahifa")],
        ]
    else:
        lms_buttons = [
            [types.KeyboardButton(text="📊 Finishing Groups"), types.KeyboardButton(text="👨🏻‍🏫 Ustoz bo'yicha"), types.KeyboardButton(text="⏳ Waiting Groups")],
            [types.KeyboardButton(text="📋 Dars Jadval")],
            [types.KeyboardButton(text="🏠 Bosh sahifa")],
        ]

    await message.answer(
        text="📑 <b>LMS Panel</b>\n\nQaysi turdagi hisobotni ko'rmoqchisiz?\n\n<i>Ma'lumot LMS platformasidan olinadi</i>",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=lms_buttons,
            resize_keyboard=True,
        ),
    )


@report_router.message(ReportStates.waiting_for_report_choice, F.text == "🏠 Bosh sahifa")
async def report_back_home(message: types.Message, state: FSMContext):
    await state.clear()
    from Keyboards.main_menu import get_main_menu
    role = _USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner") if _USERS_ROLES else "Owner"
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@report_router.message(ReportStates.waiting_for_cashbox_detail, F.text == "🏠 Bosh sahifa")
async def cashbox_back_home(message: types.Message, state: FSMContext):
    await state.clear()
    from Keyboards.main_menu import get_main_menu
    role = _USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner") if _USERS_ROLES else "Owner"
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@report_router.message(ReportStates.waiting_for_report_choice, F.text == "📋 Dars Jadval")
async def export_schedule_to_sheets(message: types.Message, state: FSMContext):
    """LMS dan dars jadvalini olib Google Sheets ga yozadi."""
    await message.answer("⏳ LMS dan dars jadvali yuklanmoqda...\n\nBu biroz vaqt olishi mumkin (30-60 soniya).")

    from utils.sheets_export import write_schedule_to_sheets
    result = await write_schedule_to_sheets()
    await message.answer(result, parse_mode="HTML")


@report_router.message(ReportStates.waiting_for_report_choice, F.text == "💰 Finance Report")
async def show_finance_report(message: types.Message, state: FSMContext):
    # Faqat Owner uchun
    role = _USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner") if _USERS_ROLES else "Owner"
    if role != "Owner":
        await message.answer("⚠️ Bu buyruq faqat Owner uchun!")
        return

    msg = await message.answer("⏳ Finance report tayyorlanmoqda...")

    try:
        import json, re
        from html import unescape

        s = _get_lms_session()

        # 1. Drujba ustozlari (aniq ro'yxat)
        DRUJBA_TEACHERS = [
            "Sardor Komilov",
            "Adxambek Ismoilov",
            "Obidjon Rustamov",
            "Ahmadali Turgunov",
            "Odiljon Jaloliddinov",
            "Farangiz Elamanova",
            "Sevinch Ibrohimova",
            "Xurshid Hazratqulov",
            "Nilufar Karimova",
            "Ibrohim Aliyev",
        ]

        # 2. Balanslarni olish
        r = s.get(f"{LMS_BASE}/admin/calculated-salaries?per_page=200", timeout=15)
        match = re.search(r'data-page="([^"]*)"', r.text)
        api_balances = {}
        if match:
            dp = json.loads(unescape(match.group(1)))
            for emp in dp["props"]["employees"]:
                name = f"{emp.get('first_name','')} {emp.get('last_name','')}".strip()
                eb = emp.get("employee_balance", "0")
                try:
                    eb = float(eb)
                except:
                    eb = 0
                api_balances[name] = eb

        # 3. Nom moslash (API nomi -> expected nom)
        def _match_teacher(expected_name, all_balances):
            parts = expected_name.lower().split()
            for api_name, bal in all_balances.items():
                api_lower = api_name.lower()
                if all(p in api_lower for p in parts):
                    return bal, api_name
            return 0, expected_name

        # 4. Report tuzish (berilgan tartibda)
        text = "💰 <b>DRUJBA — USTOZLAR BALANSI</b>\n\n"
        total_balance = 0
        teacher_count = 0
        for teacher in DRUJBA_TEACHERS:
            bal, matched_name = _match_teacher(teacher, api_balances)
            total_balance += bal
            teacher_count += 1
            if bal >= 0:
                text += f"{teacher_count}. 👨🏻‍🏫 {teacher}\n   💰 {int(bal)} so'm\n\n"
            else:
                text += f"{teacher_count}. 👨🏻‍🏫 {teacher}\n   🔴 {int(bal)} so'm\n\n"

        text += f"━━━━━━━━━━━━━━━━\n"
        text += f"📊 <b>Jami:</b> {teacher_count} ta ustoz\n"
        text += f"💵 <b>Umumiy balans:</b> {int(total_balance)} so'm"

        await msg.edit_text(text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Finance report error: {e}")
        await msg.edit_text(f"⚠️ Xatolik yuz berdi: {e}")


# ================= CASHBOX =================

@report_router.message(ReportStates.waiting_for_report_choice, F.text == "🏦 Cashbox")
async def show_cashboxes(message: types.Message, state: FSMContext):
    """Barcha cashboxlarni listing qiladi"""
    # Faqat Owner uchun
    role = _USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner") if _USERS_ROLES else "Owner"
    if role != "Owner":
        await message.answer("⚠️ Bu buyruq faqat Owner uchun!")
        return

    msg = await message.answer("⏳ Cashboxlar yuklanmoqda...")

    try:
        import json, re
        from html import unescape

        s = _get_lms_session()
        r = s.get(f"{LMS_BASE}/admin/cashboxes", timeout=15)
        match = re.search(r'data-page="([^"]*)"', r.text)
        if not match:
            logger.warning(f"Cashbox data-page not found. Status={r.status_code}, URL={r.url}, len={len(r.text)}")
            await msg.edit_text("⚠️ Cashbox ma'lumotlari topilmadi.")
            return

        dp = json.loads(unescape(match.group(1)))
        cashboxes = dp["props"]["cashboxes"]

        if not cashboxes:
            await msg.edit_text("📭 Hech qanday cashbox topilmadi.")
            return

        # Faqat Drujba filialidagi cashboxlar (branch_id=3)
        drujba_cbs = [cb for cb in cashboxes if cb.get("branch_id") == DRUJBA_BRANCH_ID]
        logger.info(f"Cashboxes: total={len(cashboxes)}, drujba={len(drujba_cbs)}, ids={[c['id'] for c in cashboxes]}")

        if not drujba_cbs:
            await msg.edit_text("📭 Drujba filialida cashbox topilmadi.")
            return

        # Xabarda listing
        text = "🏦 <b>DRUJBA — CASHBOXLAR</b>\n\n"
        from_keyboard = []

        for idx, cb in enumerate(drujba_cbs, 1):
            bal = cb.get("balance", {}) if isinstance(cb.get("balance"), dict) else {}
            total = sum(float(v or 0) for v in bal.values())
            text += f"{idx}. <b>{cb['name']}</b> — 💰 {int(total)} so'm\n"
            from_keyboard.append([types.InlineKeyboardButton(text=f"{cb['name']} — {int(total)} so'm", callback_data=f"cb_{cb['id']}")])

        from_keyboard.append([types.InlineKeyboardButton(text="🏠 Ortga", callback_data="cb_back")])
        inline_kb = types.InlineKeyboardMarkup(inline_keyboard=from_keyboard)

        await state.set_state(ReportStates.waiting_for_cashbox_detail)
        await msg.edit_text(text, parse_mode="HTML", reply_markup=inline_kb)

    except Exception as e:
        logger.error(f"Cashbox list error: {e}")
        await msg.edit_text(f"⚠️ Xatolik yuz berdi: {e}")


@report_router.callback_query(ReportStates.waiting_for_cashbox_detail, F.data.startswith("cb_"))
async def cashbox_callback_handler(call: types.CallbackQuery, state: FSMContext):
    """Cashbox tanlanganda yoki orqaga qaytganda"""
    await call.answer()

    data = call.data
    if data == "cb_back":
        # Back to cashbox listing — re-fetch data
        msg = call.message
        try:
            import json, re
            from html import unescape

            s = _get_lms_session()
            r = s.get(f"{LMS_BASE}/admin/cashboxes", timeout=15)
            match = re.search(r'data-page="([^"]*)"', r.text)
            if not match:
                logger.warning(f"Cashbox data-page not found. Status={r.status_code}, URL={r.url}, len={len(r.text)}")
                await msg.edit_text("⚠️ Cashbox ma'lumotlari topilmadi.")
                return

            dp = json.loads(unescape(match.group(1)))
            cashboxes = dp["props"]["cashboxes"]
            drujba_cbs = [cb for cb in cashboxes if cb.get("branch_id") == DRUJBA_BRANCH_ID]

            text = "🏦 <b>DRUJBA — CASHBOXLAR</b>\n\n"
            from_keyboard = []

            for idx, cb in enumerate(drujba_cbs, 1):
                bal = cb.get("balance", {}) if isinstance(cb.get("balance"), dict) else {}
                total = sum(float(v or 0) for v in bal.values())
                text += f"{idx}. <b>{cb['name']}</b> — 💰 {int(total)} so'm\n"
                from_keyboard.append([types.InlineKeyboardButton(text=f"{cb['name']} — {int(total)} so'm", callback_data=f"cb_{cb['id']}")])

            from_keyboard.append([types.InlineKeyboardButton(text="🏠 Ortga", callback_data="cb_back")])
            inline_kb = types.InlineKeyboardMarkup(inline_keyboard=from_keyboard)

            await msg.edit_text(text, parse_mode="HTML", reply_markup=inline_kb)
        except Exception as e:
            await msg.edit_text(f"⚠️ Xatolik: {e}")
        return

    # Cashbox detail
    cb_id = data.replace("cb_", "")
    msg = call.message

    try:
        import json, re
        from html import unescape

        s = _get_lms_session()
        r = s.get(f"{LMS_BASE}/admin/cashboxes", timeout=15)
        match = re.search(r'data-page="([^"]*)"', r.text)
        if not match:
            logger.warning(f"Cashbox data-page not found. Status={r.status_code}, URL={r.url}, len={len(r.text)}")
            await msg.edit_text("⚠️ Cashbox ma'lumotlari topilmadi.")
            return

        dp = json.loads(unescape(match.group(1)))
        cashboxes = dp["props"]["cashboxes"]
        cb = next((c for c in cashboxes if str(c["id"]) == cb_id), None)

        if not cb:
            await msg.edit_text("⚠️ Cashbox topilmadi.")
            return

        bal = cb.get("balance", {})
        if not isinstance(bal, dict):
            bal = {}

        # Jami
        total = sum(float(v or 0) for v in bal.values())

        text = f"🏦 <b>{cb['name']}</b>\n\n"
        text += f"💰 <b>Jami:</b> {int(total)} so'm\n"
        text += f"━━━━━━━━━━━━━━━━\n\n"

        # Categorized breakdown (user so'ragan tartibda - hamma vaqt ko'rinadi)
        cash_v = float(bal.get('cash', 0) or 0)
        terminal_v = float(bal.get('terminal', 0) or 0)
        qr_v = float(bal.get('qrcode', 0) or 0)
        plastic_v = float(bal.get('card', 0) or 0)
        perech_v = float(bal.get('uzum', 0) or 0) + float(bal.get('payme', 0) or 0) + float(bal.get('click', 0) or 0)
        mchj_v = float(bal.get('llcaccounts', 0) or 0)
        bank_v = float(bal.get('bank', 0) or 0)

        text += f"💵 <b>Naqd:</b> {int(cash_v)} so'm\n"
        text += f"💳 <b>Terminal:</b> {int(terminal_v)} so'm\n"
        text += f"📱 <b>QR:</b> {int(qr_v)} so'm\n"
        text += f"💳 <b>Plastic:</b> {int(plastic_v)} so'm\n"
        text += f"📲 <b>Perchesleniya:</b> {int(perech_v)} so'm\n"
        text += f"🏛 <b>MCHJ hisob raqamlar:</b> {int(mchj_v)} so'm\n"
        text += f"🏦 <b>Bank:</b> {int(bank_v)} so'm\n"

        if total == 0:
            text += "📭 Bu cashboxda pul mavjud emas.\n"

        inline_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🏦 Ortga (Cashboxlar)", callback_data="cb_back")]
            ]
        )

        await msg.edit_text(text, parse_mode="HTML", reply_markup=inline_kb)

    except Exception as e:
        logger.error(f"Cashbox detail error: {e}")
        await msg.edit_text(f"⚠️ Xatolik: {e}")


# ================= WAITING GROUPS =================
def _get_waiting_groups():
    """Drujba status=1 (kutilayotgan) guruhlarni xona va o'quvchilar soni bilan qaytaradi"""
    import openpyxl
    from html import unescape
    s = _get_lms_session()
    BASE = LMS_BASE

    # Export dan status=1 guruh ID larini olish
    r = s.get(f"{BASE}/admin/groups/export", timeout=30)
    wb = openpyxl.load_workbook(io.BytesIO(r.content))
    ws = wb.active

    h = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    id_col = h.index("Id") + 1
    name_col = h.index("Ism") + 1
    status_col = h.index("Status") + 1
    teacher_col = h.index("craftable-pro.Teacher Id") + 1
    course_col = h.index("Kurs Id") + 1
    branch_col = h.index("Fillial Id") + 1

    waiting = []
    for row_idx in range(2, ws.max_row + 1):
        bid = ws.cell(row_idx, branch_col).value
        status = ws.cell(row_idx, status_col).value
        if bid == 3 and status == 1:
            gid = ws.cell(row_idx, id_col).value
            gname = str(ws.cell(row_idx, name_col).value or "")
            tid = ws.cell(row_idx, teacher_col).value
            cid = ws.cell(row_idx, course_col).value
            tname = _teacher_map.get(tid, "❌ Tayinlanmagan") if tid else "❌ Tayinlanmagan"
            cname = _course_map.get(cid, f"ID#{cid}")

            # Har bir guruh uchun detail so'rov
            try:
                r2 = s.get(f"{BASE}/admin/groups/{gid}", timeout=15)
                m2 = re.search(r'data-page="([^"]*)"', r2.text)
                if m2:
                    dp = json.loads(unescape(m2.group(1)))
                    gd = dp["props"]["group"]

                    # Xona
                    rooms = gd.get("rooms", [])
                    room_name = rooms[0]["name"] if rooms else "❌"
                    capacity = rooms[0]["capacity"] if rooms else 20

                    # O'quvchilar — planned guruhlarda "students" arrayida
                    students = gd.get("students", gd.get("newly_added_trial_frozen_active_failed_students", []))
                    active = sum(1 for s in students if s.get("pivot", {}).get("status") == 6)
                    trial = sum(1 for s in students if s.get("pivot", {}).get("status") in (1, 8))
                    frozen = sum(1 for s in students if s.get("pivot", {}).get("status") == 9)

                    waiting.append({
                        "name": gname,
                        "teacher": tname,
                        "level": cname,
                        "room": room_name,
                        "capacity": capacity,
                        "active": active,
                        "trial": trial,
                        "frozen": frozen,
                    })
            except Exception as e:
                logger.warning(f"Waiting group #{gid} fetch error: {e}")
                waiting.append({
                    "name": gname,
                    "teacher": tname,
                    "level": cname,
                    "room": "❌",
                    "capacity": 0,
                    "active": 0,
                    "trial": 0,
                    "frozen": 0,
                })

    return waiting


@report_router.message(ReportStates.waiting_for_report_choice, F.text == "⏳ Waiting Groups")
async def show_waiting_groups(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat administrator va owner uchun!")
        return

    await message.answer("⏳ Kutilayotgan guruhlar yuklanmoqda...")
    groups = await asyncio.to_thread(_get_waiting_groups)
    all_comments = await get_all_comments()

    if not groups:
        await message.answer("📭 Hozircha kutilayotgan guruhlar yo'q.")
        return

    # State ga saqlaymiz
    await state.update_data(waiting_groups=groups, report_type="waiting")

    report, inline_kb = _render_waiting_groups_report(groups, all_comments)
    await message.answer(report, parse_mode="HTML", reply_markup=inline_kb)


def _render_waiting_groups_report(groups: list, all_comments: dict):
    """Waiting groups reportni state cache dan tez yasaydi"""
    text = f"⏳ <b>WAITING GROUPS</b> — {len(groups)} ta guruh\n\n"

    # Raqamli inline tugmalar — har qatorda 5 tadan
    num_rows = []
    row = []
    for idx, g in enumerate(groups):
        has_comment = bool(all_comments.get(g["name"], ""))
        label = f"{idx + 1}{'📝' if has_comment else ''}"
        row.append(types.InlineKeyboardButton(
            text=label,
            callback_data=f"wgp_{idx}"
        ))
        if len(row) >= 5:
            num_rows.append(row)
            row = []
    if row:
        num_rows.append(row)

    inline_kb = types.InlineKeyboardMarkup(inline_keyboard=num_rows) if num_rows else None

    # Ustoz bo'yicha guruhlab chiqamiz
    global_idx = 0
    by_teacher = {}
    for g in groups:
        by_teacher.setdefault(g["teacher"], []).append(g)

    for teacher, gs in sorted(by_teacher.items()):
        text += f"👨🏻‍🏫 <b>{teacher}</b>\n"
        for g in gs:
            global_idx += 1
            comment = all_comments.get(g["name"], "")
            comment_line = f" 📝" if comment else ""
            text += (
                f"   <b>{global_idx}.</b> 📚 {g['name']} — {g['level']}{comment_line}\n"
                f"       👥 {g['active']} + {g['trial']} + {g['frozen']} / {'?' if g['capacity'] == 0 else g['capacity']}\n"
                f"       🏠 Xona: {g['room']}\n\n"
            )

    return text, inline_kb


@report_router.callback_query(F.data.startswith("wgp_"))
async def show_waiting_group_detail_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    idx = int(call.data.split("_")[-1])
    await state.set_state(ReportStates.waiting_for_report_choice)
    await _show_waiting_group_detail(call, state, idx)


async def _show_waiting_group_detail(call: types.CallbackQuery, state: FSMContext, idx: int):
    state_data = await state.get_data()
    groups = state_data.get("waiting_groups", [])
    report_type = state_data.get("report_type", "waiting")

    if idx >= len(groups):
        await call.message.edit_text("⚠️ Guruh topilmadi.")
        return

    g = groups[idx]
    all_comments = await get_all_comments()
    comment = all_comments.get(g["name"], "")

    detail = f"⏳ <b>{g['name']} — {g['level']}</b>\n\n"
    detail += f"👨🏻‍🏫 {g['teacher']}\n"
    detail += f"👥 {g['active']} + {g['trial']} + {g['frozen']} / {'?' if g['capacity'] == 0 else g['capacity']}\n"
    detail += f"🏠 Xona: {g['room']}\n"

    if comment:
        detail += f"\n📝 <b>Izoh:</b> {comment}\n"

    # Eski izoh uchun callback data tayyorlaymiz
    kb = []
    if comment:
        kb.append([
            types.InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"wcmt_e_{idx}"),
            types.InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"wcmt_d_{idx}"),
        ])
    else:
        kb.append([
            types.InlineKeyboardButton(text="➕ Izoh qo'shish", callback_data=f"wcmt_a_{idx}"),
        ])
    kb.append([
        types.InlineKeyboardButton(text="⬅️ Waiting Groups", callback_data="wg_back"),
    ])

    # State ga saqlaymiz
    await state.update_data(comment_group_name=g["name"], comment_group_idx=idx)

    await call.message.edit_text(
        detail,
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
    )


@report_router.callback_query(F.data == "wg_back")
async def back_to_waiting_groups(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    state_data = await state.get_data()
    groups = state_data.get("waiting_groups", [])
    all_comments = await get_all_comments()
    report, inline_kb = _render_waiting_groups_report(groups, all_comments)
    await state.set_state(ReportStates.waiting_for_report_choice)
    await call.message.edit_text(report, parse_mode="HTML", reply_markup=inline_kb)


# Waiting groups uchun izoh callbacklari
@report_router.callback_query(F.data.startswith("wcmt_a_"))
@report_router.callback_query(F.data.startswith("wcmt_e_"))
async def start_waiting_comment_input(call: types.CallbackQuery, state: FSMContext):
    """➕ Izoh qo'shish yoki ✏️ tahrirlash"""
    await call.answer()
    idx = int(call.data.split("_")[-1])
    state_data = await state.get_data()
    groups = state_data.get("waiting_groups", [])

    if idx >= len(groups):
        await call.message.edit_text("⚠️ Guruh topilmadi.")
        return

    g = groups[idx]
    group_name = g["name"]
    all_comments = await get_all_comments()
    old_comment = all_comments.get(group_name, "")

    await state.update_data(comment_group_name=group_name, comment_group_idx=idx)
    await state.set_state(ReportStates.waiting_for_comment_input)

    hint = f"✏️ <b>{group_name}</b>\n\n"
    if old_comment:
        hint += f"📝 Joriy izoh: {old_comment}\n\n"
    hint += "Yangi izoh matnini kiriting (yoki ❌ Bekor qilish):"

    await call.message.edit_text(
        hint,
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"wcmt_cancel_{idx}")]
        ]),
    )


@report_router.callback_query(F.data.startswith("wcmt_cancel_"))
async def cancel_waiting_comment(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    idx = int(call.data.split("_")[-1])
    await _show_waiting_group_detail(call, state, idx)


@report_router.callback_query(F.data.startswith("wcmt_d_"))
async def delete_waiting_comment(call: types.CallbackQuery, state: FSMContext):
    """Izohni o'chirish"""
    await call.answer()
    idx = int(call.data.split("_")[-1])
    state_data = await state.get_data()
    groups = state_data.get("waiting_groups", [])

    if idx >= len(groups):
        await call.message.edit_text("⚠️ Guruh topilmadi.")
        return

    group_name = groups[idx]["name"]
    await delete_comment(group_name)
    await _show_waiting_group_detail(call, state, idx)


# ================= BARCHA MUAMMOLI GURUHLAR =================
@report_router.message(ReportStates.waiting_for_report_choice, F.text == "📊 Finishing Groups")
async def show_problematic_groups(message: types.Message, state: FSMContext):
    await message.answer("⏳ LMSdan guruhlar yuklanmoqda...")

    groups = await asyncio.to_thread(get_all_groups)
    teacher_scores = await asyncio.to_thread(get_teacher_scores)
    all_comments = await get_all_comments()

    if not groups:
        await message.answer("📭 LMSda ma'lumotlar topilmadi yoki ulanib bo'lmadi.")
        return

    report, found_groups, inline_kb = _build_report_data(groups, teacher_scores, all_comments)

    await state.update_data(found_groups=found_groups)

    if found_groups and inline_kb:
        await message.answer(
            report,
            parse_mode="HTML",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb),
        )
    else:
        await message.answer(report, parse_mode="HTML")


# ================= USTOZ BO'YICHA GURUHLAR =================
@report_router.message(ReportStates.waiting_for_report_choice, F.text == "👨🏻‍🏫 Ustoz bo'yicha")
async def show_teachers_list(message: types.Message, state: FSMContext):
    teachers = await asyncio.to_thread(get_unique_teachers)

    if not teachers:
        await message.answer("📭 LMSda o'qituvchilar topilmadi.")
        return

    await state.set_state(ReportStates.waiting_for_teacher_choice)

    inline_kb = []
    for t in teachers:
        inline_kb.append([types.InlineKeyboardButton(
            text=f"👨🏻‍🏫 {t}",
            callback_data=f"teachergroups_{t}",
        )])

    inline_kb.append([types.InlineKeyboardButton(
        text="🏠 Bosh sahifa",
        callback_data="teachergroups_cancel",
    )])

    await message.answer(
        text=f"👨🏻‍🏫 <b>Ustozni tanlang:</b>\n\nJami {len(teachers)} ta o'qituvchi",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb),
    )


@report_router.message(ReportStates.waiting_for_teacher_choice, F.text == "📊 Finishing Groups")
async def switch_to_problematic(message: types.Message, state: FSMContext):
    await state.set_state(ReportStates.waiting_for_report_choice)
    await show_problematic_groups(message, state)


@report_router.message(ReportStates.waiting_for_teacher_choice, F.text == "👨🏻‍🏫 Ustoz bo'yicha")
async def refresh_teachers(message: types.Message, state: FSMContext):
    await show_teachers_list(message, state)


@report_router.message(ReportStates.waiting_for_teacher_choice, F.text == "🏠 Bosh sahifa")
async def teacher_choice_home(message: types.Message, state: FSMContext):
    await state.clear()
    from Keyboards.main_menu import get_main_menu
    role = _USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner") if _USERS_ROLES else "Owner"
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@report_router.callback_query(ReportStates.waiting_for_teacher_choice, F.data == "teachergroups_cancel")
async def cancel_teacher_groups(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    from Keyboards.main_menu import get_main_menu
    role = _USERS_ROLES.get(str(call.from_user.id), {}).get("role", "Owner") if _USERS_ROLES else "Owner"
    await call.message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
    await call.answer()


@report_router.callback_query(ReportStates.waiting_for_teacher_choice, F.data == "teachergroups_back")
async def back_to_teachers_list(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    teachers = get_unique_teachers()
    if not teachers:
        await call.message.edit_text("📭 LMSda o'qituvchilar topilmadi.")
        return

    inline_kb = []
    for t in teachers:
        inline_kb.append([types.InlineKeyboardButton(
            text=f"👨🏻‍🏫 {t}",
            callback_data=f"teachergroups_{t}",
        )])
    inline_kb.append([types.InlineKeyboardButton(
        text="🏠 Bosh sahifa",
        callback_data="teachergroups_cancel",
    )])

    await call.message.edit_text(
        text=f"👨🏻‍🏫 <b>Ustozni tanlang:</b>\n\nJami {len(teachers)} ta o'qituvchi",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb),
    )


@report_router.callback_query(ReportStates.waiting_for_teacher_choice, F.data.startswith("teachergroups_"))
async def show_teacher_groups(call: types.CallbackQuery, state: FSMContext):
    teacher_name = call.data.replace("teachergroups_", "")
    await call.answer()
    await call.message.edit_text(f"⏳ <b>{teacher_name}</b> guruhlari yuklanmoqda...", parse_mode="HTML")

    groups = await asyncio.to_thread(get_all_groups)
    teacher_groups = [g for g in groups if g["teacher"] == teacher_name]

    if not teacher_groups:
        await call.message.edit_text(
            text=f"👨🏻‍🏫 <b>{teacher_name}</b>\n\n📭 Hozirda faol guruhlari topilmadi.",
            parse_mode="HTML",
        )
        return

    active_groups = [g for g in teacher_groups if g["status"] == "🟢 Aktiv guruh" and g["days_left"] >= 0]
    upcoming_groups = [g for g in teacher_groups if g["status"] == "🗓 Kutilmoqda"]

    total_active = len(active_groups) + len(upcoming_groups)
    text = f"👨🏻‍🏫 <b>{teacher_name}</b>\n"
    text += f"📊 Jami: {total_active} ta guruh\n\n"

    if active_groups:
        text += "🟢 <b>AKTIV GURUHLAR:</b>\n"
        for g in active_groups:
            days_info = f"({g['days_left']} kun qoldi)" if g["days_left"] <= 14 else f"({g['days_left']} kun)"
            text += (
                f"   📚 {g['group_name']} — {g['level']}\n"
                f"   📅 {g['end_date']} ⏳ {days_info}\n"
            )
            if g["comment"]:
                text += f"   📝 {g['comment']}\n"
            text += "\n"

    if upcoming_groups:
        text += "🟡 <b>KUTILAYOTGAN GURUHLAR:</b>\n"
        for g in upcoming_groups:
            start_hint = format_date_with_hint(g['start_date']) if g['start_date'] else "Noma'lum"
            text += (
                f"   📚 {g['group_name']} — {g['level']}\n"
                f"   📅 Boshlanishi: {start_hint}\n"
            )
            if g["comment"]:
                text += f"   📝 {g['comment']}\n"
            text += "\n"

    if not active_groups and not upcoming_groups:
        text += "📭 Ko'rsatiladigan guruhlar topilmadi.\n"

    teachers = get_unique_teachers()
    inline_kb = []
    for t in teachers:
        inline_kb.append([types.InlineKeyboardButton(
            text=f"👨🏻‍🏫 {t}",
            callback_data=f"teachergroups_{t}",
        )])
    inline_kb.append([
        types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="teachergroups_back"),
        types.InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="teachergroups_cancel"),
    ])

    await call.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb),
    )


# ================= GURUH IZOHLARI HANDLERLARI =================

def _build_report_data(groups: list, teacher_scores: dict, all_comments: dict) -> tuple:
    """Ixcham raqamli report + raqamli tugmalar.
    Qaytaradi: (report_text, found_groups, inline_keyboard_buttons)
    """
    report = "📄 <b>MUAMMOLI GURUHLAR</b>\n\n"
    found_groups = []
    idx = 0

    for g in groups:
        level = g["level"]
        days_left = g["days_left"]
        group_name = g["group_name"]

        comment = all_comments.get(group_name, "")
        if comment:
            g["comment"] = comment

        should_show = False
        problem_type = None

        if level in IELTS_LEVELS and 0 <= days_left <= 14:
            should_show = True
            problem_type = "ending"

        if "Novice" in level and 0 <= days_left <= 14:
            teacher_score = teacher_scores.get(g["teacher"])
            if teacher_score is not None and teacher_score <= 8.0:
                should_show = True
                problem_type = "teacher_swap"
            else:
                teacher_score = None

        if not should_show:
            continue

        # teacher_score ni data da saqlaymiz
        if problem_type == "teacher_swap":
            g["_teacher_score"] = teacher_scores.get(g["teacher"])
        g["_problem_type"] = problem_type

        found_groups.append({"name": group_name, "idx": idx, "data": g})

        num = idx + 1
        icon = "⚠️" if problem_type == "teacher_swap" else "🚨"
        comment_mark = " 📝" if comment else ""

        report += f"<b>{num}. {icon} {g['group_name']} — {g['level']}{comment_mark}</b>\n"
        report += f"   👨🏻‍🏫 {g['teacher']} | 📅 {g['end_date']} | ⏳ {days_left} kun"

        if problem_type == "teacher_swap":
            report += f" | 🎯 {teacher_scores.get(g['teacher'])} → 8.5+"
        elif comment:
            report += f"\n   📝 {comment[:60]}{'...' if len(comment) > 60 else ''}"

        report += "\n\n"
        idx += 1

    if not found_groups:
        report += "✅ Hozircha muammoli guruh topilmadi"
        return report, found_groups, []

    # Raqamli tugmalar
    num_row = []
    for fg in found_groups:
        has_comment = bool(fg["data"].get("comment", ""))
        label = f"{fg['idx'] + 1}{'📝' if has_comment else ''}"
        num_row.append(types.InlineKeyboardButton(
            text=label,
            callback_data=f"grp_{fg['idx']}"
        ))

    inline_kb = [num_row]

    return report, found_groups, inline_kb

def _find_group(state_data: dict, idx: int) -> dict | None:
    """State ichidan indeks bo'yicha guruhni topadi."""
    found_groups = state_data.get("found_groups", [])
    for fg in found_groups:
        if fg["idx"] == idx:
            return fg
    return None


def _render_report_from_cache(found_groups: list, all_comments: dict) -> tuple:
    """State dagi found_groups va DB izohlardan report + markup yasaydi.
    LMS/Google Sheets ga bormaydi — tez.
    Qaytaradi: (report_text, found_groups, markup)
    """
    report = "📄 <b>MUAMMOLI GURUHLAR</b>\n\n"

    for fg in found_groups:
        g = fg["data"]
        group_name = g["group_name"]
        comment = all_comments.get(group_name, "")
        g["comment"] = comment

        num = fg["idx"] + 1
        problem_type = g.get("_problem_type", "ending")
        icon = "⚠️" if problem_type == "teacher_swap" else "🚨"
        comment_mark = " 📝" if comment else ""

        report += f"<b>{num}. {icon} {g['group_name']} — {g['level']}{comment_mark}</b>\n"
        report += f"   👨🏻‍🏫 {g['teacher']} | 📅 {g['end_date']} | ⏳ {g['days_left']} kun"

        if problem_type == "teacher_swap":
            report += f" | 🎯 {g.get('_teacher_score', '?')} → 8.5+"
        elif comment:
            report += f"\n   📝 {comment[:60]}{'...' if len(comment) > 60 else ''}"

        report += "\n\n"

    # Raqamli tugmalar
    num_row = []
    for fg in found_groups:
        has_comment = bool(all_comments.get(fg["data"]["group_name"], ""))
        label = f"{fg['idx'] + 1}{'📝' if has_comment else ''}"
        num_row.append(types.InlineKeyboardButton(
            text=label,
            callback_data=f"grp_{fg['idx']}"
        ))

    markup = types.InlineKeyboardMarkup(inline_keyboard=[num_row])
    return report, found_groups, markup


async def _refresh_report(call: types.CallbackQuery, state: FSMContext):
    """Reportni qayta yuklab, xabarni yangilaydi."""
    groups = await asyncio.to_thread(get_all_groups)
    teacher_scores = await asyncio.to_thread(get_teacher_scores)
    all_comments = await get_all_comments()

    if not groups:
        await call.message.edit_text("📭 LMSda ma'lumotlar topilmadi.")
        return

    report, found_groups, inline_kb = _build_report_data(groups, teacher_scores, all_comments)
    await state.update_data(found_groups=found_groups)

    if found_groups and inline_kb:
        await call.message.edit_text(
            report,
            parse_mode="HTML",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb),
        )
    else:
        await call.message.edit_text(report, parse_mode="HTML")


@report_router.callback_query(F.data.startswith("cmt_a_"))
@report_router.callback_query(F.data.startswith("cmt_e_"))
async def start_comment_input(call: types.CallbackQuery, state: FSMContext):
    """➕ Izoh qo'shish yoki ✏️ tahrirlash — matn kiritishni so'rash."""
    await call.answer()
    
    idx = int(call.data.split("_")[-1])
    state_data = await state.get_data()
    fg = _find_group(state_data, idx)
    
    if not fg:
        await call.message.edit_text("⚠️ Guruh topilmadi. Iltimos, reportni qayta oching.")
        return

    group_name = fg["name"]
    old_comment = fg["data"].get("comment", "")

    await state.update_data(comment_group_idx=idx, comment_group_name=group_name)
    await state.set_state(ReportStates.waiting_for_comment_input)

    hint = f"✏️ <b>{group_name}</b>\n\n"
    if old_comment:
        hint += f"📝 Joriy izoh: {old_comment}\n\n"
    hint += "Yangi izoh matnini kiriting (yoki ❌ Bekor qilish):"

    await call.message.edit_text(
        hint,
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cmt_cancel")]
        ]),
    )


@report_router.callback_query(F.data == "cmt_cancel")
async def cancel_comment_input(call: types.CallbackQuery, state: FSMContext):
    """Izoh kiritishni bekor qilish — guruh detaliga qaytish."""
    await call.answer()
    state_data = await state.get_data()
    idx = state_data.get("comment_group_idx", 0)
    await state.set_state(ReportStates.waiting_for_report_choice)
    await _show_group_detail(call, state, idx)


@report_router.message(ReportStates.waiting_for_comment_input)
async def save_comment(message: types.Message, state: FSMContext):
    """Admin izoh matnini yozganda saqlash."""
    state_data = await state.get_data()
    group_name = state_data.get("comment_group_name")
    user_id = str(message.from_user.id)

    if not group_name:
        await message.answer("⚠️ Xatolik: guruh topilmadi.")
        await state.set_state(ReportStates.waiting_for_report_choice)
        return

    comment_text = message.text.strip()
    await set_comment(group_name, comment_text, user_id)

    await state.set_state(ReportStates.waiting_for_report_choice)

    # State cache dan foydalanamiz — LMS/Google Sheets ga bormaymiz
    state_data = await state.get_data()
    report_type = state_data.get("report_type", "finishing")

    if report_type == "waiting":
        # Waiting Groups reportini qayta render qilish
        groups = state_data.get("waiting_groups", [])
        if not groups:
            await message.answer("📭 Ma'lumot topilmadi. Iltimos, reportni qayta oching.")
            return
        all_comments = await get_all_comments()
        report, markup = _render_waiting_groups_report(groups, all_comments)
        await message.answer(report, parse_mode="HTML", reply_markup=markup)
        return

    # Finishing Groups reportini qayta render qilish
    found_groups = state_data.get("found_groups", [])

    if not found_groups:
        await message.answer("📭 Ma'lumot topilmadi. Iltimos, reportni qayta oching.")
        return

    all_comments = await get_all_comments()
    report, found_groups, markup = _render_report_from_cache(found_groups, all_comments)
    await state.update_data(found_groups=found_groups)
    await message.answer(report, parse_mode="HTML", reply_markup=markup)


@report_router.callback_query(F.data.startswith("cmt_d_"))
async def confirm_delete_comment(call: types.CallbackQuery, state: FSMContext):
    """🗑 O'chirish — tasdiqlash so'raydi."""
    await call.answer()
    
    idx = int(call.data.split("_")[-1])
    state_data = await state.get_data()
    fg = _find_group(state_data, idx)

    if not fg:
        await call.message.edit_text("⚠️ Guruh topilmadi. Iltimos, reportni qayta oching.")
        return

    group_name = fg["name"]
    await state.update_data(comment_group_idx=idx, comment_group_name=group_name)
    await state.set_state(ReportStates.waiting_for_comment_delete_confirm)

    await call.message.edit_text(
        f"🗑 <b>Izohni o'chirish</b>\n\n"
        f"📚 {group_name}\n\n"
        f"Haqiqatan ham izohni o'chirishni xohlaysizmi?",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Ha, o'chirilsin", callback_data=f"cmt_del_yes_{idx}"),
                types.InlineKeyboardButton(text="❌ Yo'q", callback_data="cmt_del_no"),
            ]
        ]),
    )


@report_router.callback_query(F.data.startswith("cmt_del_yes_"))
async def do_delete_comment(call: types.CallbackQuery, state: FSMContext):
    """✅ Izohni o'chirishni tasdiqlash."""
    await call.answer()
    
    idx = int(call.data.split("_")[-1])
    state_data = await state.get_data()
    fg = _find_group(state_data, idx)

    if not fg:
        await call.message.edit_text("⚠️ Guruh topilmadi.")
        return

    group_name = fg["name"]
    deleted = await delete_comment(group_name)

    if deleted:
        await call.answer("✅ Izoh o'chirildi!", show_alert=False)
    else:
        await call.answer("ℹ️ Izoh allaqachon o'chirilgan.", show_alert=False)

    await state.set_state(ReportStates.waiting_for_report_choice)
    await _show_group_detail(call, state, idx)


@report_router.callback_query(F.data == "cmt_del_no")
async def cancel_delete_comment(call: types.CallbackQuery, state: FSMContext):
    """❌ O'chirishni bekor qilish."""
    await call.answer()
    state_data = await state.get_data()
    idx = state_data.get("comment_group_idx", 0)
    await state.set_state(ReportStates.waiting_for_report_choice)
    await _show_group_detail(call, state, idx)


async def _show_group_detail(call: types.CallbackQuery, state: FSMContext, idx: int):
    """Bitta guruhning to'liq detali + izoh tugmalari."""
    state_data = await state.get_data()
    fg = _find_group(state_data, idx)

    if not fg:
        await call.message.edit_text("⚠️ Guruh topilmadi.")
        return

    g = fg["data"]
    
    # DB dan yangi izohni o'qiymiz
    all_comments = await get_all_comments()
    comment = all_comments.get(g["group_name"], "")
    
    problem_type = g.get("_problem_type", "ending")

    detail = f"📚 <b>{g['group_name']} — {g['level']}</b>\n\n"

    if problem_type == "ending":
        detail += (
            f"🚨 IELTS guruh tugamoqda\n\n"
            f"👨🏻‍🏫 {g['teacher']}\n"
            f"📅 {g['end_date']} | ⏳ {g['days_left']} kun qoldi\n"
            f"📌 {g['status']}\n"
        )
    else:
        teacher_score = g.get("_teacher_score", "?")
        detail += (
            f"⚠️ Ustoz almashtirish kerak\n\n"
            f"👨🏻‍🏫 {g['teacher']}\n"
            f"📅 {g['end_date']} | ⏳ {g['days_left']} kun qoldi\n"
            f"📌 {g['status']}\n"
            f"🎯 IELTS: {teacher_score} → Kerak: 8.5+\n"
        )

    if comment:
        detail += f"\n📝 <b>Izoh:</b> {comment}\n"

    kb = []
    if comment:
        kb.append([
            types.InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"cmt_e_{idx}"),
            types.InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"cmt_d_{idx}"),
        ])
    else:
        kb.append([
            types.InlineKeyboardButton(text="➕ Izoh qo'shish", callback_data=f"cmt_a_{idx}"),
        ])
    kb.append([
        types.InlineKeyboardButton(text="⬅️ Asosiy report", callback_data="report_back"),
    ])

    await call.message.edit_text(
        detail,
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
    )


@report_router.callback_query(F.data.startswith("grp_"))
async def show_group_detail_handler(call: types.CallbackQuery, state: FSMContext):
    """Raqamli tugma bosilganda — guruh detalini ko'rsatish."""
    await call.answer()
    idx = int(call.data.split("_")[-1])
    await state.set_state(ReportStates.waiting_for_report_choice)
    await _show_group_detail(call, state, idx)


@report_router.callback_query(F.data == "report_back")
async def back_to_report(call: types.CallbackQuery, state: FSMContext):
    """⬅️ Asosiy reportga qaytish (STATE dan ma'lumotlar bilan — tez)."""
    try:
        await call.answer()
    except Exception:
        pass

    await state.set_state(ReportStates.waiting_for_report_choice)

    state_data = await state.get_data()
    report_type = state_data.get("report_type", "finishing")

    if report_type == "waiting":
        groups = state_data.get("waiting_groups", [])
        if not groups:
            await call.message.answer("📭 Ma'lumot topilmadi. Iltimos, reportni qayta oching.")
            return
        all_comments = await get_all_comments()
        report, markup = _render_waiting_groups_report(groups, all_comments)
        try:
            await call.message.edit_text(report, parse_mode="HTML", reply_markup=markup)
        except Exception:
            await call.message.answer(report, parse_mode="HTML", reply_markup=markup)
        return

    found_groups = state_data.get("found_groups", [])

    if not found_groups:
        await call.message.answer("📭 Ma'lumot topilmadi. Iltimos, reportni qayta oching.")
        return

    # Faqat izohlarni yangilaymiz — LMS va Google Sheets ga bormaymiz
    all_comments = await get_all_comments()
    report, found_groups, markup = _render_report_from_cache(found_groups, all_comments)
    await state.update_data(found_groups=found_groups)

    try:
        await call.message.edit_text(report, parse_mode="HTML", reply_markup=markup)
    except Exception:
        await call.message.answer(report, parse_mode="HTML", reply_markup=markup)
