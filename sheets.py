import gspread
from datetime import datetime
from config import SHEET_ID, GOOGLE_CREDENTIALS

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)
sh = gc.open_by_key(SHEET_ID)
sheet = sh.get_worksheet(0) 

def parse_date(value):
    if not value: return None
    if isinstance(value, datetime): return value
    # Jadvaldagi 25.04.2026 formatini o'qish uchun
    formats = ["%d.%m.%Y", "%m/%d/%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except:
            continue
    return None

def get_report(days_limit):
    try:
        # Hamma ma'lumotlarni olamiz (Header'ni skip qilish uchun 1-indexdan boshlaymiz)
        data = sheet.get_all_values()[1:] 
        today = datetime.today()
        result = []

        for row in data:
            # Ustunlar soni kamida J gacha (10 ta) bo'lishi kerak
            if len(row) < 10: continue
            
            # SKRINSHOTDAGI HARFLARGA MOS INDEXLAR:
            teacher = row[2].strip()   # C ustuni
            name = row[3].strip()      # D ustuni (Nom)
            level = row[4].strip()     # E ustuni (Level)
            end_date_raw = row[7].strip() # H ustuni (End Date)
            status = row[9].strip()    # J ustuni (Status)
            comment = row[10].strip() if len(row) > 10 else "" # K ustuni

            if not name or not end_date_raw:
                continue

            # Faqat Levelda "IELTS" bo'lsa
            if "IELTS" not in level.upper():
                continue

            end_date = parse_date(end_date_raw)
            if not end_date:
                continue

            days_left = (end_date - today).days

            # Faqat so'ralgan muddat ichidagilar
            if 0 < days_left <= days_limit:
                emoji = "🔴" if days_left <= 14 else "🟡"
                
                report_text = (
                    f"{emoji} {name} ({level})\n"
                    f"👨‍🏫 {teacher}\n"
                    f"⏳ {days_left} kun qoldi\n"
                    f"📌 {status}\n"
                )
                if comment:
                    report_text += f"💬 {comment}\n"
                
                result.append(report_text)

        if not result:
            return f"📊 Kelgusi {days_limit} kun ichida tugaydigan IELTS guruhlari topilmadi."

        return f"📊 MONITORING ({days_limit} kunlik)\n\n" + "\n".join(result)

    except Exception as e:
        return f"⚠️ Xatolik: {str(e)}"
