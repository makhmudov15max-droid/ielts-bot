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
    teachers = teachers_sheet.get_all_values()

    scores = {}

    for row in teachers[1:]:

        try:
            teacher_name = row[1].strip()

            score = float(row[2])

            scores[teacher_name] = score

        except:
            pass

    return scores


@report_router.message(F.text == "📑 Guruh Report")
async def group_report(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "📊 Guruhlar tekshirilyapti..."
    )

    if not edu_sheet:
        return await message.answer(
            "❌ Google Sheets ulanmagan"
        )

    teacher_scores = get_teacher_scores()

    rows = edu_sheet.get_all_values()

    rows = rows[2:]

    report = "📄 <b>EDUCONTROL REPORT</b>\n\n"

    found = False

    for row in rows:

        try:

            teacher = row[2].strip()

            group_name = row[3].strip()

            level = row[4].strip()

            end_date = row[6].strip()

            days_left = int(row[7])

            status = row[8].strip()

            comment = row[9].strip()

        except:

            continue


        # IELTS GURUH

        if level in IELTS_LEVELS and days_left <=14:

            found=True

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


        # NOVICE

        if level=="IELTS Novice" and days_left<=14:

            teacher_score = teacher_scores.get(
                teacher,
                0
            )

            if teacher_score<=8:

                found=True

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

    if not found:

        report += (
            "✅ Hozircha muammo topilmadi"
        )

    await message.answer(
        report,
        parse_mode="HTML"
    )
