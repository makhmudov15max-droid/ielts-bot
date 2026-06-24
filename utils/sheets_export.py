"""
LMS dan dars jadvalini olib, Google Sheets ga yozish.
Foydalanuvchi so'roviga binoan: 2026-06-24
"""
import io, os, json, re, logging
from urllib.parse import unquote
from html import unescape
from datetime import datetime

logger = logging.getLogger(__name__)

SHEET_ID = "1PpGWObeppzsSkaYgGz0fRYP_3zk-3YuxBOXStrn_PCc"
SHEET_NAME = "DarsJadval"
DRUJBA_BRANCH_ID = 3
LMS_BASE = "https://main.ieltszoneapp.uz"


def _get_session():
    """LMS sessiyasini yaratish yoki qaytarish (group_report dagi bilan bir xil)."""
    import requests
    from Handlers.group_report import _get_lms_session
    return _get_lms_session()


def fetch_schedule_from_lms() -> list[dict]:
    """LMS dan aktiv Drujba guruhlarini olib, dars jadvali ro'yxatini qaytaradi."""
    import requests
    s = _get_session()

    all_groups = []
    page = 1

    while True:
        r = s.get(f"{LMS_BASE}/admin/unassessed-groups?per_page=200&page={page}")
        match = re.search(r'data-page="([^"]*)"', r.text)
        if not match:
            break

        dp = json.loads(unescape(match.group(1)))
        groups = dp["props"]["groups"]["data"]
        if not groups:
            break

        for g in groups:
            # Faqat Drujba + aktiv guruhlar
            if g.get("branch_id") != DRUJBA_BRANCH_ID:
                continue
            if g.get("status") != 2:
                continue

            # Guruh raqami (name dan olamiz: "110 Novice B/T st:03.06.2026" → 110)
            name = g.get("name", "")
            group_num = name.split()[0] if name else "—"

            # Kurs nomi
            course = g.get("course", {})
            level = course.get("name", {}).get("uz", course.get("name", {}).get("en", "—"))

            # Teacher to'liq ismi
            teacher = g.get("teacher", {})
            teacher_name = f"{teacher.get('first_name', '')} {teacher.get('last_name', '')}".strip()
            if not teacher_name:
                teacher_name = "—"

            # Kun turi: 1 = Toq, 2 = Juft
            days = g.get("days", 1)
            day_type = "Toq" if days == 1 else "Juft"

            # Vaqt
            start_time = str(g.get("lesson_start_time", ""))[:5] or "—"
            end_time = str(g.get("lesson_end_time", ""))[:5] or "—"

            all_groups.append({
                "group_num": group_num,
                "name": name,
                "level": level,
                "teacher": teacher_name,
                "room": "—",
                "day_type": day_type,
                "start_time": start_time,
                "end_time": end_time,
            })

        # Keyingi sahifa
        last_page = dp["props"]["groups"].get("last_page", 1)
        if page >= last_page:
            break
        page += 1

    logger.info(f"Dars jadvali: {len(all_groups)} ta guruh olindi")
    return all_groups


async def write_schedule_to_sheets() -> str:
    """LMS dan dars jadvalini olib Google Sheets ga yozadi.
    Qaytaradi: muvaffaqiyat xabari yoki xatolik matni.
    """
    import asyncio
    import gspread

    try:
        # 1. LMS dan ma'lumot olish
        groups = await asyncio.to_thread(fetch_schedule_from_lms)

        if not groups:
            return "⚠️ LMS dan hech qanday aktiv guruh topilmadi."

        # 2. Google Sheets ga ulanish
        creds_json = os.getenv("GOOGLE_CREDS")
        if not creds_json:
            return "⚠️ GOOGLE_CREDS topilmadi. .env faylini tekshiring."

        creds = json.loads(creds_json)
        client = gspread.service_account_from_dict(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

        # 3. Sheetni to'liq tozalash
        sheet.clear()

        # 4. Sarlavhalar yozish
        headers = ["Guruh #", "Guruh nomi", "Level", "Teacher", "Xona", "Kun turi", "Boshlanish", "Tugash"]
        sheet.update("A1:H1", [headers])

        # 5. Ma'lumotlarni yozish (A2 dan boshlab)
        rows = []
        for g in groups:
            rows.append([
                g["group_num"],
                g["name"],
                g["level"],
                g["teacher"],
                g["room"],
                g["day_type"],
                g["start_time"],
                g["end_time"],
            ])

        sheet.update(f"A2:H{len(rows) + 1}", rows)

        return f"✅ Dars jadvali Google Sheets ga yozildi!\n\n📊 Jami: {len(rows)} ta guruh\n📋 Sheet: {SHEET_NAME}"

    except gspread.exceptions.WorksheetNotFound:
        return f"⚠️ '{SHEET_NAME}' varag'i topilmadi. Iltimos, Google Sheets da shu nomli varaq yarating."
    except Exception as e:
        logger.error(f"Sheets export error: {e}")
        return f"❌ Xatolik: {str(e)[:200]}"
