import gspread
from datetime import datetime
from config import SHEET_ID, GOOGLE_CREDENTIALS

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)
sh = gc.open_by_key(SHEET_ID)
sheet = sh.get_worksheet(0) 

def parse_date(value):
    if not value: return None
    if isinstance(value, datetime): return value
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
        # Barcha ma'lumotlarni o'qiymiz
        all_data = sheet.get_all_values()
        if not all_data: return "⚠️ Jadval bo'sh!"

        today = datetime.today()
        result = []
        
        # Ustunlar indeksi (Siz bergan aniq tartib bo'yicha)
        # C=2 (Teacher), D=3 (Nom), E=4 (Level), H=7 (End Date), J=9 (Status)
        t_idx, n_idx, l_idx, e_idx, s_idx = 2, 3, 4, 7, 9

        count_checked = 0
        for row in all_data:
            # Ustunlar soni yetarli emas qatorlarni tashlab ketamiz
            if len(row) < 8: continue
            
            group_id = row[n_idx].strip()
            level = row[l_idx].strip()
            end_date_raw = row[e_idx].strip()

            # Agar bu sarlavha qatori bo'lsa yoki kerakli ma'lumot bo'lmasa o'tkazib yuboramiz
            if group_id == "Nom" or not group_id or not end_date_raw:
                continue

            count_checked += 1

            # FILTR: IELTS (Katta-kichik harfga qaramaymiz)
            if "IELTS" not in level.upper():
                continue

            end_date = parse_date(end_date_raw)
            if not end_date: continue

            days_left = (end_date - today).days

            # Muddatni tekshirish
            if -1 <= days_left <= days_limit:
                emoji = "🔴" if days_left <= 14 else "🟡"
                if days_left < 0: emoji = "❌"
                
                res = (
                    f"{emoji} <b>{group_id}</b> ({level})\n"
                    f"👨‍🏫 {row[t_idx].strip()}\n"
                    f"⏳ {days_left} kun qoldi\n"
                    f"📌 {row[s_idx].strip() if len(row) > 9 else ''}"
                )
                result.append(res)

        if not result:
            return (f"📊 Topilmadi.\n"
                    f"Bot vaqti: {today.strftime('%d.%m.%Y')}\n"
                    f"Tekshirilgan ma'lumotli qatorlar: {count_checked}")

        return f"📊 <b>MONITORING ({days_limit} kun)</b>\n\n" + "\n\n".join(result)

    except Exception as e:
        return f"⚠️ Xatolik: {str(e)}"
