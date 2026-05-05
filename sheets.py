import gspread
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

from config import SHEET_ID, GOOGLE_CREDENTIALS

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)

CACHE = {"data": None, "time": 0}
CACHE_DURATION = 300  # 5 daqiqa

IELTS_LEVELS = ["ielts standard", "ielts intensive", "ielts expert"]

# Ustun indexlari (0-based, A=0)
COL_TEACHER = 2   # C
COL_NOM     = 3   # D
COL_LEVEL   = 4   # E
COL_ENDDATE = 6   # G
COL_COMMENT = 9   # J


def get_sheet():
    return gc.open_by_key(SHEET_ID).sheet1


def parse_date(value):
    """
    Google Sheets dan keladigan barcha sana formatlarini parse qiladi:
      - "05.06.2026"  (FORMATTED_VALUE bilan)
      - "6/5/2026"    (ba'zan shunday keladi)
      - 45000-60000   (serial number — UNFORMATTED_VALUE bilan)
    """
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None

    # Serial number (Google Sheets ichki format)
    try:
        serial = float(raw)
        if 40000 < serial < 70000:
            from datetime import date
            base = datetime(1899, 12, 30)
            return base + timedelta(days=int(serial))
    except ValueError:
        pass

    # Matn formatlar
    for fmt in ("%d.%m.%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d.%m.%y", "%m/%d/%y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    logger.warning(f"parse_date: noma'lum format → '{raw}'")
    return None


def is_ielts(level: str) -> bool:
    level_lower = level.strip().lower()
    return any(il in level_lower for il in IELTS_LEVELS)


def load_data():
    now = time.time()
    if CACHE["data"] and now - CACHE["time"] < CACHE_DURATION:
        return CACHE["data"]

    sheet = get_sheet()
    # FORMATTED_VALUE → sanalar "05.06.2026" ko'rinishida keladi
    data = sheet.get_all_values(value_render_option="FORMATTED_VALUE")
    CACHE["data"] = data
    CACHE["time"] = now
    logger.info(f"Sheets yangilandi: {len(data)} qator")
    return data


def clear_cache():
    CACHE["data"] = None
    CACHE["time"] = 0


def get_graduating_report(days_limit: int = 14) -> str:
    """
    days_limit kun ichida tugaydigan IELTS guruhlarini qaytaradi.
    """
    data = load_data()
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    deadline = today + timedelta(days=days_limit)

    groups = []

    # Qator 0 = bo'sh, Qator 1 = header → data[2:] dan boshlaymiz
    for i, row in enumerate(data[2:], start=3):
        # Juda qisqa yoki to'liq bo'sh qator
        if len(row) <= COL_ENDDATE:
            continue

        teacher  = row[COL_TEACHER].strip()
        nom      = row[COL_NOM].strip()
        level    = row[COL_LEVEL].strip()
        end_raw  = row[COL_ENDDATE].strip()
        comment  = row[COL_COMMENT].strip() if len(row) > COL_COMMENT else ""

        # Bo'sh data qatorlari (merged cell bo'lgan yerlar)
        if not nom and not end_raw:
            continue

        # Faqat IELTS guruhlar
        if not is_ielts(level):
            continue

        # Sanani parse qilish
        end_date = parse_date(end_raw)
        if not end_date:
            logger.warning(f"Qator {i}: sana parse bo'lmadi → '{end_raw}' (guruh: {nom})")
            continue

        days_left = (end_date.date() - today.date()).days

        # Faqat 0 < days_left <= days_limit oralig'idagilar
        if not (0 < days_left <= days_limit):
            continue

        groups.append({
            "teacher": teacher,
            "nom": nom,
            "level": level,
            "end_date": end_date,
            "days_left": days_left,
            "comment": comment,
        })

    logger.info(f"get_graduating_report({days_limit}): {len(groups)} guruh topildi")

    if not groups:
        return (
            f"✅ Yaxshi xabar: keyingi {days_limit} kun ichida\n"
            f"tugaydigan IELTS guruhi yo'q.\n\n"
            f"📅 Bugun: {today.strftime('%d.%m.%Y')}"
        )

    # Qolgan kunlar bo'yicha saralash (eng yaqin avval)
    groups.sort(key=lambda g: g["days_left"])

    lines = [
        f"🎓 *{days_limit} KUN ICHIDA TUGAYDIGAN IELTS GURUHLAR*\n"
        f"📅 Bugun: {today.strftime('%d.%m.%Y')}\n"
        f"{'─' * 30}"
    ]

    for g in groups:
        if g["days_left"] <= 7:
            urgency = "🔴"
        elif g["days_left"] <= 14:
            urgency = "🟡"
        else:
            urgency = "🟢"

        block = (
            f"\n{urgency} *{g['nom']}* — {g['level']}\n"
            f"👨‍🏫 {g['teacher']}\n"
            f"📆 Tugaydi: {g['end_date'].strftime('%d.%m.%Y')} "
            f"(*{g['days_left']} kun*)"
        )
        if g["comment"]:
            block += f"\n💬 {g['comment']}"
        lines.append(block)

    lines.append(f"\n{'─' * 30}\n📊 Jami: {len(groups)} ta guruh")
    return "\n".join(lines)
