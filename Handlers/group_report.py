import os
import json
import gspread
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import config

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
    """Global users roles ni o'rnatish"""
    global _USERS_ROLES
    _USERS_ROLES = users_roles


# ================= ADMIN ROLINI TEKSHIRUVCHI FUNKSIYA (PostgreSQL dan) =================
async def is_admin(user_id: int) -> bool:
    """Foydalanuvchi Admin, Owner yoki Manager rolida ekanligini tekshiradi"""
    if _USERS_ROLES:
        user_info = _USERS_ROLES.get(str(user_id))
        if user_info:
            role = user_info.get("role")
            if role in ["Admin", "Owner", "Manager"]:
                return True
    
    from utils.users_db import get_user_role
    role = await get_user_role(str(user_id))
    return role in ["Admin", "Owner", "Manager"]


# ===== GOOGLE ULANISH =====
try:
    creds = json.loads(os.getenv("GOOGLE_CREDS"))
    client = gspread.service_account_from_dict(creds)
    edu_sheet = client.open("EduControl").worksheet("EduControl")
    teachers_sheet = client.open("EduControl").worksheet("Ustozlar")
    print("✅ REPORT Google Sheets ulandi")
except Exception as e:
    print(f"❌ REPORT XATO: {e}")
    edu_sheet = None
    teachers_sheet = None


IELTS_LEVELS = [
    "IELTS Standard",
    "IELTS Practice",
    "IELTS Bridge",
    "IELTS Expert",
    "IELTS Intensive"
]

ALL_LEVELS = IELTS_LEVELS + ["IELTS Novice", "General English", "Pre-IELTS"]


def get_teacher_scores():
    if not teachers_sheet:
        return {}
    try:
        teachers = teachers_sheet.get_all_values()
        scores = {}
        for row in teachers[1:]:
            try:
                if len(row) >= 3:
                    teacher_name = row[1].strip()
                    score = float(row[2])
                    scores[teacher_name] = score
            except:
                pass
        return scores
    except Exception as e:
        print(f"❌ Teacher scores olishda xato: {e}")
        return {}


def get_all_groups():
    """Google Sheets dan barcha guruhlarni o'qish"""
    if not edu_sheet:
        return []
    rows = edu_sheet.get_all_values()
    if len(rows) <= 2:
        return []
    
    groups = []
    for row in rows[2:]:
        try:
            if len(row) < 7:
                continue
            
            teacher = row[2].strip() if len(row) > 2 and row[2] else ""
            group_name = row[3].strip() if len(row) > 3 and row[3] else ""
            level = row[4].strip() if len(row) > 4 and row[4] else ""
            end_date = row[6].strip() if len(row) > 6 and row[6] else ""
            
            days_left_raw = row[7] if len(row) > 7 else "0"
            try:
                days_left = int(float(days_left_raw)) if days_left_raw and days_left_raw.strip() else 0
            except:
                days_left = 0
            
            status = row[8].strip() if len(row) > 8 and row[8] else ""
            comment = row[9].strip() if len(row) > 9 and row[9] else ""
            
            if teacher and group_name:
                groups.append({
                    "teacher": teacher,
                    "group_name": group_name,
                    "level": level,
                    "end_date": end_date,
                    "days_left": days_left,
                    "status": status,
                    "comment": comment,
                })
        except Exception as e:
            print(f"Qatorni o'qishda xato: {e}")
            continue
    
    return groups


def get_unique_teachers():
    """Barcha unikal o'qituvchilar ro'yxati"""
    groups = get_all_groups()
    teachers = sorted(set(g["teacher"] for g in groups if g["teacher"]))
    return teachers


# ================= ASOSIY MENU =================
@report_router.message(F.text == "📑 Guruh Report")
async def group_report_menu(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat administrator va owner uchun!")
        return

    if not edu_sheet:
        return await message.answer("❌ Google Sheets ulanmagan")

    await state.set_state(ReportStates.waiting_for_report_choice)
    await message.answer(
        text="📑 <b>Guruh Report</b>\n\nQaysi turdagi hisobotni ko'rmoqchisiz?",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="📊 Barcha muammoli guruhlar")],
                [types.KeyboardButton(text="👨🏻‍🏫 Ustoz bo'yicha guruhlar")],
                [types.KeyboardButton(text="🏠 Bosh sahifa")],
            ],
            resize_keyboard=True
        )
    )


@report_router.message(ReportStates.waiting_for_report_choice, F.text == "🏠 Bosh sahifa")
async def report_back_home(message: types.Message, state: FSMContext):
    await state.clear()
    from Keyboards.main_menu import get_main_menu
    role = _USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


# ================= BARCHA MUAMMOLI GURUHLAR (ESKI HISOBOT) =================
@report_router.message(ReportStates.waiting_for_report_choice, F.text == "📊 Barcha muammoli guruhlar")
async def show_problematic_groups(message: types.Message, state: FSMContext):
    await message.answer("⏳ Guruhlar tekshirilyapti...")

    teacher_scores = get_teacher_scores()
    groups = get_all_groups()
    
    if not groups:
        await message.answer("📭 Jadvalda ma'lumotlar yetarli emas.")
        return

    report = "📄 <b>MUAMMOLI GURUHLAR</b>\n\n"
    found = False

    for g in groups:
        level = g["level"]
        days_left = g["days_left"]
        teacher = g["teacher"]
        
        # IELTS guruh tugamoqda
        if level in IELTS_LEVELS and 0 < days_left <= 14:
            found = True
            report += (
                f"🚨 <b>IELTS guruh tugamoqda</b>\n\n"
                f"👨🏻‍🏫 {teacher}\n"
                f"📚 {g['group_name']} {level}\n"
                f"📅 {g['end_date']}\n"
                f"⏳ {days_left} kun qoldi\n"
                f"📌 {g['status']}\n"
                f"📝 {g['comment']}\n"
                f"\n━━━━━━━━━━\n\n"
            )

        # Ustoz almashtirish kerak
        if level == "IELTS Novice" and 0 < days_left <= 14:
            teacher_score = teacher_scores.get(teacher, 0)
            if teacher_score <= 8:
                found = True
                report += (
                    f"⚠️ <b>Ustoz almashtirish kerak</b>\n\n"
                    f"👨🏻‍🏫 {teacher}\n"
                    f"📚 {g['group_name']} {level}\n"
                    f"📅 {g['end_date']}\n"
                    f"⏳ {days_left} kun qoldi\n"
                    f"📌 {g['status']}\n"
                    f"📝 {g['comment']}\n\n"
                    f"🎯 IELTS: {teacher_score}\n"
                    f"Kerak: 8.5 yoki 9.0\n"
                    f"\n━━━━━━━━━━\n\n"
                )

    if not found:
        report += "✅ Hozircha muammoli guruh topilmadi"

    await message.answer(report, parse_mode="HTML")


# ================= USTOZ BO'YICHA GURUHLAR =================
@report_router.message(ReportStates.waiting_for_report_choice, F.text == "👨🏻‍🏫 Ustoz bo'yicha guruhlar")
async def show_teachers_list(message: types.Message, state: FSMContext):
    teachers = get_unique_teachers()
    
    if not teachers:
        await message.answer("📭 Google Sheetsda o'qituvchilar topilmadi.")
        return
    
    await state.set_state(ReportStates.waiting_for_teacher_choice)
    
    # Inline tugmalar - har bir ustoz uchun
    inline_kb = []
    for t in teachers:
        inline_kb.append([types.InlineKeyboardButton(
            text=f"👨🏻‍🏫 {t}", 
            callback_data=f"teachergroups_{t}"
        )])
    
    inline_kb.append([types.InlineKeyboardButton(
        text="🏠 Bosh sahifa", 
        callback_data="teachergroups_cancel"
    )])
    
    await message.answer(
        text=f"👨🏻‍🏫 <b>Ustozni tanlang:</b>\n\n"
             f"Jami {len(teachers)} ta o'qituvchi",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )


@report_router.callback_query(ReportStates.waiting_for_teacher_choice, F.data == "teachergroups_cancel")
async def cancel_teacher_groups(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    from Keyboards.main_menu import get_main_menu
    role = _USERS_ROLES.get(str(call.from_user.id), {}).get("role", "Owner")
    await call.message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
    await call.answer()


@report_router.callback_query(ReportStates.waiting_for_teacher_choice, F.data.startswith("teachergroups_"))
async def show_teacher_groups(call: types.CallbackQuery):
    teacher_name = call.data.replace("teachergroups_", "")
    
    await call.message.edit_text(f"⏳ <b>{teacher_name}</b> guruhlari yuklanmoqda...", parse_mode="HTML")
    
    groups = get_all_groups()
    teacher_groups = [g for g in groups if g["teacher"] == teacher_name]
    
    if not teacher_groups:
        await call.message.edit_text(
            text=f"👨🏻‍🏫 <b>{teacher_name}</b>\n\n"
                 f"📭 Hozirda faol guruhlari topilmadi.",
            parse_mode="HTML"
        )
        await call.answer()
        return
    
    # Faol (kun qolgan) va tugagan guruhlarga ajratish
    active = [g for g in teacher_groups if g["days_left"] > 0]
    ended = [g for g in teacher_groups if g["days_left"] <= 0]
    
    text = f"👨🏻‍🏫 <b>{teacher_name}</b>\n"
    text += f"📊 Jami: {len(teacher_groups)} ta guruh"
    
    teacher_scores = get_teacher_scores()
    score = teacher_scores.get(teacher_name)
    if score:
        text += f" | 🎯 IELTS: {score}\n\n"
    else:
        text += "\n\n"
    
    if active:
        text += "✅ <b>FAOL GURUHLAR:</b>\n"
        for g in active:
            days_info = f"({g['days_left']} kun qoldi)" if g["days_left"] <= 14 else f"({g['days_left']} kun)"
            text += (
                f"   📚 {g['group_name']} — {g['level']}\n"
                f"   📅 {g['end_date']} ⏳ {days_info}\n"
                f"   📌 {g['status']}\n\n"
            )
    
    if ended:
        text += "⚫ <b>TUGAGAN GURUHLAR:</b>\n"
        for g in ended:
            text += f"   📚 {g['group_name']} — {g['level']}\n"
    
    # "Boshqa ustoz" tugmasi
    teachers = get_unique_teachers()
    inline_kb = []
    for t in teachers:
        inline_kb.append([types.InlineKeyboardButton(
            text=f"👨🏻‍🏫 {t}", 
            callback_data=f"teachergroups_{t}"
        )])
    
    inline_kb.append([types.InlineKeyboardButton(
        text="🏠 Bosh sahifa", 
        callback_data="teachergroups_cancel"
    )])
    
    await call.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )
    await call.answer()
