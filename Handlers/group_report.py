import os, io, re, json, logging, asyncio
from datetime import datetime, timezone, timedelta
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import config

logger = logging.getLogger(__name__)

report_router = Router()

try:
    ADMIN_ID = int(config.ADMIN_ID)
except:
    ADMIN_ID = 6500594896


# ================= STATES =================
class ReportStates(StatesGroup):
    waiting_for_report_choice = State()
    waiting_for_teacher_choice = State()


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
            if role in ["Admin", "Owner", "Manager"]:
                return True
    from utils.users_db import get_user_role
    role = await get_user_role(str(user_id))
    return role in ["Admin", "Owner", "Manager"]


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
    """LMS export orqali barcha Drujba IELTS guruhlarni olish"""
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
            if status != 2:  # Faqat aktiv/waiting guruhlar (1=draft, 2=aktiv, 3=arxiv)
                continue

            end_str = str(ws.cell(row_idx, end_col).value or "")
            if end_str == "None" or not end_str:
                continue

            try:
                end_dt = datetime.strptime(end_str[:10], "%Y-%m-%d").date()
            except:
                continue

            days_left = (end_dt - today).days
            if days_left < -30:
                continue

            tid = ws.cell(row_idx, teacher_col).value
            if not tid:  # O'qituvchisi yo'q bo'sh guruhlarni o'tkazib yuborish
                continue
            tname = _teacher_map.get(tid, f"ID#{tid}")
            cname = _course_map.get(cid, f"ID#{cid}")

            start_str = str(ws.cell(row_idx, start_col).value or "")
            start_fmt = ""
            if start_str and start_str != "None":
                try:
                    start_fmt = datetime.strptime(start_str[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
                except:
                    pass

            end_fmt = end_dt.strftime("%d.%m.%Y")

            groups.append({
                "teacher": tname,
                "group_name": str(ws.cell(row_idx, name_col).value or ""),
                "level": cname,
                "start_date": start_fmt,
                "end_date": end_fmt,
                "days_left": days_left,
                "status": "Aktiv guruh",  # status=2 = aktiv/waiting
                "comment": "",
            })

        logger.info(f"LMS: {len(groups)} Drujba IELTS groups loaded")
        return groups

    except Exception as e:
        logger.error(f"LMS get_all_groups error: {e}")
        return []


def get_unique_teachers():
    groups = get_all_groups()
    teachers = sorted(set(g["teacher"] for g in groups if g["teacher"] and not g["teacher"].startswith("ID#")))
    return teachers


def get_teacher_scores():
    """LMSda teacher IELTS score yo'q — bo'sh dict"""
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
@report_router.message(F.text == "📑 Guruh Report")
async def group_report_menu(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat administrator va owner uchun!")
        return

    await state.set_state(ReportStates.waiting_for_report_choice)
    await message.answer(
        text="📑 <b>Guruh Report</b>\n\nQaysi turdagi hisobotni ko'rmoqchisiz?\n\n<i>Ma'lumot LMS platformasidan olinadi</i>",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="📊 Barcha muammoli guruhlar")],
                [types.KeyboardButton(text="👨🏻‍🏫 Ustoz bo'yicha guruhlar")],
                [types.KeyboardButton(text="🏠 Bosh sahifa")],
            ],
            resize_keyboard=True,
        ),
    )


@report_router.message(ReportStates.waiting_for_report_choice, F.text == "🏠 Bosh sahifa")
async def report_back_home(message: types.Message, state: FSMContext):
    await state.clear()
    from Keyboards.main_menu import get_main_menu
    role = _USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner") if _USERS_ROLES else "Owner"
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


# ================= BARCHA MUAMMOLI GURUHLAR =================
@report_router.message(ReportStates.waiting_for_report_choice, F.text == "📊 Barcha muammoli guruhlar")
async def show_problematic_groups(message: types.Message, state: FSMContext):
    await message.answer("⏳ LMSdan guruhlar yuklanmoqda...")

    groups = await asyncio.to_thread(get_all_groups)

    if not groups:
        await message.answer("📭 LMSda ma'lumotlar topilmadi yoki ulanib bo'lmadi.")
        return

    report = "📄 <b>MUAMMOLI GURUHLAR</b>\n\n"
    found = False

    for g in groups:
        level = g["level"]
        days_left = g["days_left"]

        # IELTS guruh tugamoqda
        if level in IELTS_LEVELS and 0 < days_left <= 14:
            found = True
            report += (
                f"🚨 <b>IELTS guruh tugamoqda</b>\n\n"
                f"👨🏻‍🏫 {g['teacher']}\n"
                f"📚 {g['group_name']} — {g['level']}\n"
                f"📅 {g['end_date']}\n"
                f"⏳ {days_left} kun qoldi\n"
                f"📌 {g['status']}\n"
            )
            if g["comment"]:
                report += f"📝 {g['comment']}\n"
            report += "\n━━━━━━━━━━\n\n"

    if not found:
        report += "✅ Hozircha muammoli guruh topilmadi"

    await message.answer(report, parse_mode="HTML")


# ================= USTOZ BO'YICHA GURUHLAR =================
@report_router.message(ReportStates.waiting_for_report_choice, F.text == "👨🏻‍🏫 Ustoz bo'yicha guruhlar")
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


@report_router.message(ReportStates.waiting_for_teacher_choice, F.text == "📊 Barcha muammoli guruhlar")
async def switch_to_problematic(message: types.Message, state: FSMContext):
    await state.set_state(ReportStates.waiting_for_report_choice)
    await show_problematic_groups(message, state)


@report_router.message(ReportStates.waiting_for_teacher_choice, F.text == "👨🏻‍🏫 Ustoz bo'yicha guruhlar")
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

    active_groups = [g for g in teacher_groups if g["days_left"] >= 0]
    opening_soon = [g for g in teacher_groups if g["days_left"] < 0 and g["days_left"] >= -30]

    text = f"👨🏻‍🏫 <b>{teacher_name}</b>\n"
    text += f"📊 Jami: {len(active_groups)} ta faol guruh\n\n"

    if active_groups:
        text += "🟢 <b>AKTIV GURUHLAR:</b>\n"
        for g in active_groups:
            days_info = f"({g['days_left']} kun qoldi)" if g["days_left"] <= 14 else f"({g['days_left']} kun)"
            text += (
                f"   📚 {g['group_name']} — {g['level']}\n"
                f"   📅 {g['end_date']} ⏳ {days_info}\n"
                f"   📌 {g['status']}\n"
            )
            if g["comment"]:
                text += f"   📝 {g['comment']}\n"
            text += "\n"

    if opening_soon:
        text += "🟡 <b>YAQINDA TUGAGAN:</b>\n"
        for g in opening_soon:
            text += (
                f"   📚 {g['group_name']} — {g['level']}\n"
                f"   📅 {g['end_date']}\n"
            )
            if g["comment"]:
                text += f"   📝 {g['comment']}\n"
            text += "\n"

    if not active_groups and not opening_soon:
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
