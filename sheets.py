import gspread
from datetime import datetime
from config import SHEET_ID, GOOGLE_CREDENTIALS

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)
sh = gc.open_by_key(SHEET_ID)
sheet = sh.get_worksheet(0) 

def parse_date(value):
    if not value: return None
    if isinstance(value, datetime): return value
    # Jadvaldagi 11.05.2026 kabi formatlarni o'qish
    formats = ["%d.%m.%Y", "%m/%d/%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except:
            continue
    return None

def get_report(days_limit):
    try:
        # Jadvalni o'qiymiz
        data = sheet.get_all_values()[1:] # Sarlavhani olib tashlaymiz
        today = datetime.today()
        result = []

        for row in data:
            # Kamida J ustunigacha ma'lumot borligini tekshiramiz (10 ta ustun)
            if len(row) < 10: continue
            
            # SIZ BERGAN TARTIB (INDEX):
            teacher = row[2].strip()      # C ustuni (2)
            group_id = row[3].strip()     # D ustuni (3)
            level = row[4].strip()        # E ustuni (4)
            end_date_raw = row[7].strip() # H ustuni (7) - End Date
            status = row[9].strip()       # J ustuni (9) - Status
            comment = row[10].strip() if len(row) > 10 else "" # K ustuni (10)

            if not group_id or not end_date_raw:
                continue

            # Faqat Levelda "IELTS" bo'lsa
            if "IELTS" not in level.upper():
                continue

            # Sanani hisoblash
            end_date = parse_date(end_date_raw)
            if not end_date:
                continue

            # Bugundan boshlab qancha qolganini aniq hisoblaymiz
            days_left = (end_date - today).days

            # Faqat bizga kerakli muddatdagilarni olamiz
            if 0 <= days_left <= days_limit:
                # 🔴 14 kundan kam qolsa qizil, bo'lmasa sariq
                emoji = "🔴" if days_left <= 14 else "🟡"
                
                report_text = (
                    f"{emoji} <b>{group_id}</b> ({level})\n"
                    f"👨‍🏫 {teacher}\n"
                    f"⏳ {days_left} kun qoldi\n"
                    f"📌 {status if status else 'Aktiv'}"
                )
                if comment:
                    report_text += f"\n💬 {comment}"
                
                result.append(report_text)

        if not result:
            return f"📊 Kelgusi {days_limit} kun ichida tugaydigan IELTS guruhlari topilmadi."

        return f"📊 <b>MONITORING ({days_limit} kunlik)</b>\n\n" + "\n\n".join(result)

    except Exception as e:
        return f"⚠️ Xatolik yuz berdi: {str(e)}"
