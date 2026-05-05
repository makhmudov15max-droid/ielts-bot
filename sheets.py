import gspread
from datetime import datetime
from config import SHEET_ID, GOOGLE_CREDENTIALS
import time

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)
sheet = gc.open_by_key(SHEET_ID).sheet1

CACHE = {"data": None, "time": 0}
CACHE_DURATION = 60


def load_data():
    now = time.time()

    if CACHE["data"] and now - CACHE["time"] < CACHE_DURATION:
        return CACHE["data"]

    data = sheet.get_all_values()  # 🔥 MUHIM: records emas

    CACHE["data"] = data
    CACHE["time"] = now

    return data


def parse_date(value):
    if not value:
        return None

    formats = ["%d.%m.%Y", "%m/%d/%Y", "%Y-%m-%d"]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except:
            continue

    return None


def get_report(days_limit):
    data = load_data()

    today = datetime.today().date()
    result = []

    # header skip
    rows = data[2:]  # 👈 1 emas, 2! chunki sening sheetda 2-qatordan boshlanadi

    for row in rows:
        try:
            teacher = row[2]
            name = row[3]
            level = row[4]
            end_raw = row[7]
            status = row[9]
            comment = row[10]

            if not name or not end_raw:
                continue

            end_date = parse_date(end_raw)
            if not end_date:
                continue

            days_left = (end_date.date() - today).days

            if 0 < days_left <= days_limit:

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
        return f"📊 {days_limit} kun ichida tugaydigan guruh topilmadi.\nBot vaqti: {today}"

    return "📊 GURUH RADAR 📡\n\n" + "\n".join(result)
