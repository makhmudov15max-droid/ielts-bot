import gspread
from datetime import datetime
from config import SHEET_ID, GOOGLE_CREDENTIALS

# Google Sheets ulanish
gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)
sh = gc.open_by_key(SHEET_ID)
sheet = sh.get_worksheet(0) 

def parse_date(value):
    if not value: return None
    if isinstance(value, datetime): return value
    # Jadvaldagi 11.05.2026 formatini o'qish
    val_str = str(value).strip()
    formats = ["%d.%m.%Y", "%m/%d/%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(val_str, fmt)
        except:
            continue
    return None

def get_report(days_limit):
    try:
        # Hamma ma'lumotlarni o'qiymiz
        data = sheet.get_all_values()
        if not data:
            return "⚠️ Jadval bo'sh!"

        # Sarlavha qatorini topamiz (odatda 1- yoki 2-qator)
        start_row = 0
        for i, row in enumerate(data):
            if "Teacher" in row or "Level" in row:
                start_row = i + 1
                break
        
        today = datetime.today()
        result = []

        for row in data[start_row:]:
            # Siz bergan tartib bo'yicha (A=0, B=1, C=2, D=3, E=4, H=7, J=9, K=10)
            if len(row) < 10: continue
            
            teacher = row[2].strip()      # C ustuni
            group_id = row[3].strip()     # D ustuni
            level = row[4].strip()        # E ustuni
            end_date_raw = row[7].strip() # H ustuni
            status = row[9].strip()       # J ustuni
            comment = row[10].strip() if len(row) > 10 else "" # K ustuni

            if not group_id or not end_date_raw:
                continue

            # Faqat Levelda "IELTS" bo'lsa
            if "IELTS" not in level.upper():
                continue

            end_date = parse_date(end_date_raw)
            if not end_date:
                continue

            # Kunlar farqini hisoblaymiz
            days_left = (end_date - today).days

            # 30, 60 yoki 90 kunlik limit ichida bo'lsa
            # (Guruh tugagan bo'lsa ham 2 kun ko'rsatib tursin: -2)
            if -2 <= days_left <= days_limit:
                emoji = "🔴" if days_left <= 14 else "🟡"
                if days_left < 0: emoji = "❌"
                
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
            return f"📊 Kelgusi {days_limit} kun ichida tugaydigan IELTS guruhlari topilmadi.\nBot vaqti: {today.strftime('%d.%m.%Y')}"

        return f"📊 <b>MONITORING ({days_limit} kunlik)</b>\n\n" + "\n\n".join(result)

    except Exception as e:
        return f"⚠️ Xato yuz berdi: {str(e)}"
