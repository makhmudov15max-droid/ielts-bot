import gspread
from datetime import datetime
from config import SHEET_ID, GOOGLE_CREDENTIALS
import time

# 🔗 Google Sheets ulanish
gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)
sheet = gc.open_by_key(SHEET_ID).sheet1

# ⚡ CACHE (tezlik uchun)
CACHE = {
    "data": None,
    "time": 0
}
CACHE_DURATION = 60  # sekund


def load_data():
    now = time.time()

    if CACHE["data"] and now - CACHE["time"] < CACHE_DURATION:
        return CACHE["data"]

    data = sheet.get_all_records()

    CACHE["data"] = data
    CACHE["time"] = now

    return data


def parse_date(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
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
    rows = load_data()

    today = datetime.today().date()
    result = []

    for row in rows:
        try:
            # 🔴 SHEET COLUMN NOMLARI
            name = row.get("Nom")
            level = row.get("Level")
            teacher = row.get("Teacher")
            end_raw = row.get("End Date")
            status = row.get("Status")
            comment = row.get("Comment")

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
