import gspread
from config import SHEET_ID, GOOGLE_CREDENTIALS

# Google Sheets ulanish
gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)

# EduControl sheet
sheet = gc.open_by_key(SHEET_ID).worksheet("EduControl")

# IELTS teacher score
IELTS_TEACHERS = {
    "Adkhambek I": 9.0,
    "Sardorbek K": 9.0,
    "Akhmadali T": 8.5,
    "Obidjon R": 8.5,
    "Otabek M": 8.5,
    "Ilkhom A": 8.0,
    "Sevinch I": 8.0,
    "Khurshid Kh": 8.0,
    "Nilufar K": 8.0,
    "Farangiz E": 8.0,
}


def get_report():
    try:

        # Barcha ma'lumotlarni olish
        data = sheet.get_all_values()

        report = "📊 DAILY REPORT\n\n"

        found = False

        # Headerlarni skip qilish
        for row in data[2:]:

            try:

                # USTUNLAR
                teacher = row[2].strip()      # C
                group_name = row[3].strip()   # D
                level = row[4].strip()        # E

                days_left = row[7].strip()    # H

                status = row[8].strip()       # I
                comment = row[9].strip()      # J

                # Days left tekshirish
                if not days_left.isdigit():
                    continue

                days_left = int(days_left)

                # 14 kundan katta bo'lsa skip
                if days_left > 14:
                    continue

                # IELTS group filter
                allowed_levels = [
                    "IELTS Standard",
                    "IELTS Expert",
                    "IELTS Intensive"
                ]

                novice_warning = False

                # IELTS Novice logikasi
                if level == "IELTS Novice":

                    teacher_score = IELTS_TEACHERS.get(teacher)

                    # Faqat 8.0 teacher bo'lsa chiqariladi
                    if teacher_score == 8.0:
                        novice_warning = True
                    else:
                        continue

                # Beginner va boshqa GE group skip
                elif level not in allowed_levels:
                    continue

                found = True

                # Emoji
                if days_left <= 7:
                    emoji = "🔴"
                else:
                    emoji = "🟡"

                # REPORT
                report += f"{emoji} {group_name} ({level})\n"

                report += f"👨‍🏫 {teacher}\n"

                report += f"⏳ {days_left} kun qoldi\n"

                # Novice warning
                if novice_warning:
                    report += "⚠️ Boshqa ustoz topish kerak\n"

                # Status
                if status:
                    report += f"📌 {status}\n"

                # Comment
                if comment:
                    report += f"💬 {comment}\n"

                report += "\n"

            except:
                continue

        if not found:
            return "📊 Hozircha muammo yo'q"

        return report

    except Exception as e:
        return f"❌ Error:\n{e}"
