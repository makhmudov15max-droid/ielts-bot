import gspread
from config import SHEET_ID, GOOGLE_CREDENTIALS

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)

sheet = gc.open_by_key(SHEET_ID).worksheet("EduControl")


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
        data = sheet.get_all_values()

        result = "📊 DAILY REPORT\n\n"

        found = False

        for row in data[2:]:

            try:
                teacher = row[2].strip()   # C
                group_name = row[3].strip() # D
                level = row[4].strip()      # E
                days_left = row[7].strip()  # H
                status = row[9].strip()     # J
                comment = row[10].strip()   # K

                if not days_left.isdigit():
                    continue

                days_left = int(days_left)

                if days_left > 14:
                    continue

                allowed_levels = [
                    "IELTS Standard",
                    "IELTS Expert",
                    "IELTS Intensive"
                ]

                novice_warning = False

                if level == "IELTS Novice":

                    teacher_score = IELTS_TEACHERS.get(teacher)

                    if teacher_score == 8.0:
                        novice_warning = True
                    else:
                        continue

                elif level not in allowed_levels:
                    continue

                found = True

                emoji = "🔴" if days_left <= 7 else "🟡"

                result += f"{emoji} {group_name} ({level})\n\n"

                result += f"👨‍🏫 {teacher}\n"

                result += f"⏳ {days_left} kun qoldi\n\n"

                if novice_warning:
                    result += "⚠️ Boshqa ustoz topish kerak\n\n"

                if status:
                    result += f"📌 {status}\n\n"

                if comment:
                    result += f"💬 {comment}\n\n"

            except:
                continue

        if not found:
            return "📊 Hozircha muammo yo'q"

        return result

    except Exception as e:
        return f"❌ Error:\n{e}"
