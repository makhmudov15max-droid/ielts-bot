import gspread
from datetime import datetime
from config import SHEET_ID, GOOGLE_CREDENTIALS

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)
sheet = gc.open_by_key(SHEET_ID).sheet1

def get_report(days_limit):
    data = sheet.get_all_values()[1:]

    today = datetime.today()
    result = []

    for row in data:
        try:
            teacher = row[2]
            name = row[3]
            level = row[4]
            end_date = row[7]
            status = row[8]
            comment = row[9]
            score = float(row[10]) if row[10] else 0

            if not name or not end_date:
                continue

            if "ielts" not in level.lower():
                continue

            end = datetime.strptime(end_date, "%d.%m.%Y")
            days_left = (end - today).days

            if 0 < days_left <= days_limit:

                if "general" in level.lower():
                    status = "Next level transition"

                if "novice" in level.lower() and score >= 8:
                    status = "Need new teacher"

                emoji = "🔴" if days_left <= 14 else "🟡"

                text = f"{emoji} {name} ({level})\n"
                text += f"👨‍🏫 {teacher}\n"
                text += f"⏳ {days_left} kun qoldi\n"

                if status:
                    text += f"📌 {status}\n"

                if comment:
                    text += f"💬 {comment}\n"

                result.append(text)

        except:
            continue

    if not result:
        return "📊 Hozircha muammo yo‘q"

    return "📊 REPORT\n\n" + "\n".join(result)
