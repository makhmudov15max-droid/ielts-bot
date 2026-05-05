import gspread
import json
from datetime import datetime
from config import SHEET_ID, GOOGLE_CREDENTIALS

# Google bilan ulanish
try:
    service_account_info = json.loads(GOOGLE_CREDENTIALS)
    gc = gspread.service_account_from_dict(service_account_info)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.get_worksheet(0)
except Exception as e:
    print(f"Google Sheets ulanishda xato: {e}")

def get_report(days_limit: int):
    try:
        data = worksheet.get("A2:K1000")
        today = datetime.now()
        report_items = []

        for row in data:
            if len(row) < 11: continue
            
            level = row[4].strip() # E ustuni
            end_date_str = row[7].strip() # H ustuni
            
            if "IELTS" not in level.upper() or not end_date_str:
                continue

            try:
                # Sanani formatlash (25.05.2024 kabi bo'lishi kerak)
                end_date = datetime.strptime(end_date_str, "%d.%m.%Y")
                days_left = (end_date - today).days
                
                if 0 < days_left <= days_limit:
                    teacher = row[2]
                    group_name = row[3]
                    comment = row[9] if len(row) > 9 else "Yo'q"
                    teacher_score_raw = row[10].replace(',', '.') if len(row) > 10 and row[10] else "0"
                    teacher_score = float(teacher_score_raw)
                    
                    status = "Oddiy holat"
                    if "general" in level.lower():
                        status = "Next level transition"
                    elif "novice" in level.lower() and teacher_score >= 8:
                        status = "Need new teacher"

                    emoji = "🔴" if days_left <= 14 else "🟡"
                    
                    item = (f"{emoji} {group_name} ({level})\n"
                            f"👨‍🏫 {teacher}\n"
                            f"⏳ {days_left} kun qoldi\n"
                            f"📌 {status}\n"
                            f"💬 {comment}")
                    report_items.append(item)
            except:
                continue

        if not report_items:
            return "📊 Hozircha muammoli guruhlar yo'q"
        
        return "📊 HISOBOT\n\n" + "\n\n".join(report_items)
    except Exception as e:
        return f"Xatolik yuz berdi: {e}"
