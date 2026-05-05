import gspread
from datetime import datetime
import logging
from config import SHEET_ID, GOOGLE_CREDENTIALS

# Loglarni yoqamiz, xato bo'lsa ko'rinishi uchun
logging.basicConfig(level=logging.INFO)

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)
sh = gc.open_by_key(SHEET_ID)
sheet = sh.get_worksheet(0) 

def parse_date(value):
    if not value: return None
    if isinstance(value, datetime): return value
    # Nuqtali (25.04.2026) va boshqa formatlar uchun
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
        # Jadvaldagi barcha qatorlarni olamiz
        data = sheet.get_all_values()
        if not data:
            return "⚠️ Jadval bo'sh yoki ulanishda xato!"

        # Header (Sarlavha) qaysi qatorda ekanini topamiz
        # Chunki ba'zida tepada bo'sh qatorlar bo'lishi mumkin
        start_row = 0
        for i, row in enumerate(data):
            if "Teacher" in row or "Level" in row:
                start_row = i + 1
                break

        today = datetime.today()
        result = []

        # Faqat ma'lumot bor qatorlarni ko'rib chiqamiz
        for row in data[start_row:]:
            # Skrinshotga ko'ra minimal ustunlar soni (K gacha bo'lishi uchun 11 ta)
            if len(row) < 8: continue
            
            # 🔍 IMAGE_E4065F.JPG ASOSIDA ANIQLANGAN INDEXLAR:
            # C ustuni = Teacher (Index 2)
            # D ustuni = Nom (Index 3)
            # E ustuni = Level (Index 4)
            # H ustuni = End Date (Index 7)
            # J ustuni = Status (Index 9)

            teacher = row[2].strip() if len(row) > 2 else ""
            group_name = row[3].strip() if len(row) > 3 else ""
            level = row[4].strip() if len(row) > 4 else ""
            end_date_raw = row[7].strip() if len(row) > 7 else ""
            status = row[9].strip() if len(row) > 9 else ""

            # Zaruriy ma'lumotlar yo'qligini tekshiramiz
            if not group_name or not end_date_raw:
                continue

            # 🎯 FILTR: IELTS guruhlarni aniqlash
            if "IELTS" not in level.upper():
                continue

            end_date = parse_date(end_date_raw)
            if not end_date:
                continue

            # Kunlar farqini hisoblaymiz
            diff = (end_date - today).days

            # Faqat bizga kerakli oraliqdagi guruhlar
            if 0 < diff <= days_limit:
                emoji = "🔴" if diff <= 14 else "🟡"
                
                text = (
                    f"{emoji} <b>{group_name}</b> ({level})\n"
                    f"👨‍🏫 {teacher}\n"
                    f"⏳ {diff} kun qoldi\n"
                    f"📌 {status if status else 'Aktiv'}\n"
                )
                result.append(text)

        if not result:
            return f"📊 Kelgusi {days_limit} kun ichida tugaydigan IELTS guruhlari topilmadi."

        return f"📊 <b>MONITORING ({days_limit} kunlik)</b>\n\n" + "\n".join(result)

    except Exception as e:
        logging.error(f"REPORT ERROR: {e}")
        return f"⚠️ Xatolik yuz berdi: {str(e)}"
