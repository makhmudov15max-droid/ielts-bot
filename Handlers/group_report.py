import os
import json
import gspread
from aiogram import Router, F, types
import config

report_router = Router()

try:
    ADMIN_ID = int(config.ADMIN_ID)
except:
    ADMIN_ID = 6500594896


# ================= ADMIN ROLINI TEKSHIRUVCHI FUNKSIYA (JSON fayldan o'qiydi) =================

def is_admin(user_id: int) -> bool:
    """Foydalanuvchi Admin yoki Owner rolida ekanligini tekshiradi"""
    USERS_FILE = "users.json"
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
                user_info = users.get(str(user_id))
                if user_info:
                    role = user_info.get("role")
                    return role in ["Admin", "Owner"]
    except Exception as e:
        print(f"is_admin() xatosi: {e}")
    return False


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


@report_router.message(F.text == "📑 Guruh Report")
async def group_report(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat administrator va owner uchun!")
        return

    await message.answer("📊 Guruhlar tekshirilyapti...")

    if not edu_sheet:
        return await message.answer("❌ Google Sheets ulanmagan")

    teacher_scores = get_teacher_scores()

    try:
        rows = edu_sheet.get_all_values()
        if len(rows) <= 2:
            await message.answer("📭 Jadvalda ma'lumotlar yetarli emas.")
            return
            
        rows = rows[2:]
        report = "📄 <b>EDUCONTROL REPORT</b>\n\n"
        found = False

        for row in rows:
            try:
                if len(row) < 10:
                    continue
                    
                teacher = row[2].strip() if row[2] else ""
                group_name = row[3].strip() if row[3] else ""
                level = row[4].strip() if row[4] else ""
                end_date = row[6].strip() if row[6] else ""
                
                days_left_raw = row[7] if len(row) > 7 else "0"
                try:
                    days_left = int(float(days_left_raw)) if days_left_raw and days_left_raw.strip() else 0
                except:
                    days_left = 0
                    
                status = row[8].strip() if len(row) > 8 and row[8] else ""
                comment = row[9].strip() if len(row) > 9 and row[9] else ""

                if level in IELTS_LEVELS and days_left <= 14 and days_left > 0:
                    found = True
                    report += (
                        f"🚨 <b>IELTS guruh tugamoqda</b>\n\n"
                        f"👨🏻‍🏫 {teacher}\n"
                        f"📚 {group_name} {level}\n"
                        f"📅 {end_date}\n"
                        f"⏳ {days_left} kun qoldi\n"
                        f"📌 {status}\n"
                        f"📝 {comment}\n"
                        f"\n━━━━━━━━━━\n\n"
                    )

                if level == "IELTS Novice" and days_left <= 14 and days_left > 0:
                    teacher_score = teacher_scores.get(teacher, 0)
                    if teacher_score <= 8:
                        found = True
                        report += (
                            f"⚠️ <b>Ustoz almashtirish kerak</b>\n\n"
                            f"👨🏻‍🏫 {teacher}\n"
                            f"📚 {group_name} {level}\n"
                            f"📅 {end_date}\n"
                            f"⏳ {days_left} kun qoldi\n"
                            f"📌 {status}\n"
                            f"📝 {comment}\n\n"
                            f"🎯 IELTS: {teacher_score}\n"
                            f"Kerak: 8.5 yoki 9.0\n"
                            f"\n━━━━━━━━━━\n\n"
                        )

            except Exception as e:
                print(f"Qatorni o'qishda xato: {e}")
                continue

        if not found:
            report += "✅ Hozircha muammo topilmadi"

        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        print(f"❌ Report generatsiya xatosi: {e}")
        await message.answer("❌ Hisobot tayyorlashda xatolik yuz berdi.")
