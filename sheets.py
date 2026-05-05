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

        # 1. Sarlavhalarni aniqlab olamiz (Ustunlar o'zgarsa ham adashmaslik uchun)
        headers = all_data[1] # Odatda 2-qatorda sarlavhalar bo'ladi
        try:
            t_idx = headers.index("Teacher")
            n_idx = headers.index("Nom")
            l_idx = headers.index("Level")
            e_idx = headers.index("End Date")
            s_idx = headers.index("Status")
        except ValueError:
            # Agar sarlavhalar topilmasa, siz bergan qat'iy indekslarni ishlatamiz
            t_idx, n_idx, l_idx, e_idx, s_idx = 2, 3, 4, 7, 9

        today = datetime.today()
        result = []

        # 2. Ma'lumotlarni tahlil qilish
        for row in all_data[2:]: # Ma'lumotlar 3-qatordan boshlanadi deb hisoblaymiz
            if len(row) <= max(t_idx, n_idx, l_idx, e_idx, s_idx): continue
            
            group_id = row[n_idx].strip()
            level = row[l_idx].strip()
            end_date_raw = row[e_idx].strip()
            
            if not group_id or not end_date_raw: continue

            # 3. FILTR: IELTS so'zi borligini tekshirish
            # Ba'zida "IELTS" so'zi orasida ko'rinmas bo'shliqlar bo'lishi mumkin
            clean_level = level.upper().replace(" ", "")
            if "IELTS" not in clean_level:
                continue

            end_date = parse_date(end_date_raw)
            if not end_date: continue

            days_left = (end_date - today).days

            # 4. Hisobotga qo'shish
            if -1 <= days_left <= days_limit:
                emoji = "🔴" if days_left <= 14 else "🟡"
                if days_left < 0: emoji = "❌"
                
                res = (
                    f"{emoji} <b>{group_id}</b> ({level})\n"
                    f"👨‍🏫 {row[t_idx].strip()}\n"
                    f"⏳ {days_left} kun qoldi\n"
                    f"📌 {row[s_idx].strip()}"
                )
                result.append(res)

        if not result:
            return f"📊 30 kunlikda hech narsa topilmadi.\nBot vaqti: {today.strftime('%d.%m.%Y')}\nTekshirilgan qatorlar: {len(all_data)-2}"

        return f"📊 <b>MONITORING ({days_limit} kun)</b>\n\n" + "\n\n".join(result)

    except Exception as e:
        return f"⚠️ Xatolik: {str(e)}"
