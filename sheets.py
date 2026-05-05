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

    data = sheet.get_all_values()
    CACHE["data"] = data
    CACHE["time"] = now

    return data


def parse_date(value):
    if not value:
        return None

    value = str(value).strip()

    formats = [
        "%d.%m.%Y",
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%d-%b-%Y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except:
            continue

    return None


def get_report(days_limit):
    data = load_data()
    today = datetime.today()

    result = []
    rows = data[2:]  # header skip

    for row in rows:
        try:
            teacher = row[2]
            name = row[3]
            level = row[4]
            end_raw = row[7]
            comment = row[10]

            if not name or not end_raw:
                continue

            # 🎯 FAAT IELTS
            if "ielts" not in str(level).lower():
                continue

            end_date = parse_date(end_raw)
            if not end_date:
                continue

            days_left = (end_date - today).days

            if 0 < days_left <= days_limit:

                # 🔥 STATUS (Apps Script dagi kabi)
                if days_left <= 14:
                    emoji = "🔴"
                else:
                    emoji = "🟡"

                text = f"{emoji} {name} ({level})\n"
                text += f"👨‍🏫 {teacher}\n"
                text += f"⏳ {days_left} kun qoldi\n"

                # status sifatida days_left chiqaramiz (sen oldin shunaqa qilgansan)
                text += f"📌 {days_left}\n"

                if comment:
                    text += f"💬 {comment}\n"

                result.append(text)

        except:
            continue

    if not result:
        return f"📊 {days_limit} kun ichida tugaydigan guruh topilmadi.\nBot vaqti: {today.strftime('%d.%m.%Y')}"

    return "📊 DAILY REPORT\n\n" + "\n".join(result)
