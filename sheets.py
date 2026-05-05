import gspread
from datetime import datetime
from config import SHEET_ID, GOOGLE_CREDENTIALS

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)
# Faylni ochamiz va birinchi varaqni olamiz
sh = gc.open_by_key(SHEET_ID)
sheet = sh.get_worksheet(0) 

def parse_date(value):
    if not value: return None
    if isinstance(value, datetime): return value
    formats = ["%d.%m.%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except:
            continue
    return None

def get_report(days_limit):
    try:
        data = sheet.get_all_values()[1:]
        today = datetime.today()
        result = []

        for row in data:
            if len(row) < 11: continue
            
            teacher = row[2]
            name = row[3]
            level = row[4]
            end_date_raw = row[7]
            status = row[8]
            comment = row[9]
            score_raw = str(row[10]).replace(',', '.') if row[10] else "0"
            score = float(score_raw)

            if not name or not end_date_raw: continue

            # 🎯 IELTS filtrini to'g'irladik
            if "IELTS" not in level.upper():
                continue

            end_date = parse_date(end_date_raw)
            if not end_date: continue

            days_left = (end_date - today).days

            if 0 < days_left <= days_limit:
                # 🔥 Smart status
                current_status = status
                if "general" in level.lower():
                    current_status = "Next level transition"
                if "novice" in level.lower() and score >= 8:
                    current_status = "Need new teacher"

                emoji = "🔴" if days_left <= 14 else "🟡"
                
                report_text = (
                    f"{emoji} {name} ({level})\n"
                    f"👨‍🏫 {teacher}\n"
                    f"⏳ {days_left} kun qoldi\n"
                    f"📌 {current_status if current_status else 'Status yoq'}\n"
                    f"💬 {comment if comment else 'Izoh yoq'}\n"
                )
                result.append(report_text)

        if not result:
            return "📊 Hozircha muammo yo‘q"

        return f"📊 REPORT ({days_limit} kunlik)\n\n" + "\n".join(result)
    except Exception as e:
        return f"⚠️ Xatolik yuz berdi: {str(e)}"
