"""
LMS dan dars jadvalini olib, Google Sheets ga MATRITSA formatida yozish.
Foydalanuvchi so'roviga binoan: sheet20 1:1 formati.
"""
import os, json, re, logging
from urllib.parse import unquote
from html import unescape

logger = logging.getLogger(__name__)

SHEET_ID = "1PpGWObeppzsSkaYgGz0fRYP_3zk-3YuxBOXStrn_PCc"
SHEET_NAME = "sheet20"
DRUJBA_BRANCH_ID = 3
LMS_BASE = "https://main.ieltszoneapp.uz"

# Sheet20 dagi vaqt → qator raqami
TIME_TO_ROW = {
    "08:00": 2,
    "10:00": 3,
    "14:00": 4,
    "16:00": 5,
    "18:00": 6,
    "20:00": 7,
}

# LMS xona nomi → sheet20 ustuni
ROOM_NAME_TO_COL = {
    "101": 4, "102": 5, "103": 6, "104": 7, "105": 8,
    "106": 9, "107": 10, "108": 11, "109": 12, "110": 13, "111": 14,
}


def _get_session():
    """LMS sessiyasini yaratish yoki qaytarish."""
    import requests
    from Handlers.group_report import _get_lms_session
    return _get_lms_session()


def fetch_branch_schedule() -> dict:
    """LMS /admin/branches/3 dan dars jadvalini oladi.
    Qaytaradi: {"odd": [lessons], "even": [lessons]}
    """
    import requests
    s = _get_session()
    r = s.get(f"{LMS_BASE}/admin/branches/{DRUJBA_BRANCH_ID}")

    match = re.search(r'data-page="([^"]*)"', r.text)
    if not match:
        raise Exception("LMS branch sahifasidan data-page topilmadi")

    dp = json.loads(unescape(match.group(1)))
    props = dp["props"]

    odd = props.get("oddDaysSchedule", {})
    even = props.get("evenDaysSchedule", {})

    return {
        "odd": odd.get("lessons", []),
        "even": even.get("lessons", []),
        "rooms": odd.get("rooms", []),
        "times": odd.get("times", []),
    }


def _lesson_to_cell(lesson: dict, day_type: str) -> tuple | None:
    """Bitta lesson ni sheet20 katak koordinatasiga o'tkazadi.
    Qaytaradi: (row, col, text) yoki None.
    """
    start_time = str(lesson.get("lesson_start_time", ""))[:5]
    room_name = str(lesson.get("room", {}).get("name", ""))

    row = TIME_TO_ROW.get(start_time)
    col = ROOM_NAME_TO_COL.get(room_name)

    if not row or not col:
        return None

    # Katak matni: #guruh_raqami teacher\nlevel
    gid = lesson.get("id", "?")
    name = lesson.get("name", "")
    # name dan guruh raqamini olish
    group_num = name.split()[0] if name else str(gid)

    teacher = lesson.get("teacher", {}) or {}
    teacher_first = teacher.get("first_name", "")

    course = lesson.get("sub_course", {}) or lesson.get("course", {}) or {}
    level = course.get("name", {}).get("uz", course.get("name", {}).get("en", "—"))

    text = f"#{gid} {teacher_first}\n{level}"

    return row, col, text


def build_matrix_data(schedule: dict, day_type: str) -> list[list[str]]:
    """Berilgan kun turi uchun matrix yasaydi.
    8 qator × 15 ustun (A-O).
    """
    # 8 qator: 0-sarlavha, 1-7 ma'lumot
    matrix = [[""] * 15 for _ in range(8)]

    # Sarlavhalar
    matrix[0][2] = "Dars xonalari"
    matrix[1][1] = "Dars vaqtlari"

    # Xona sarlavhalari (Row 0, Col D-N)
    for i in range(1, 12):
        matrix[0][3 + i] = f"{i} xona"

    # Vaqtlar (Row 1-7, Col C)
    vaqt_label = ["8:00", "10:00", "14:00", "16:00", "18:00", "20:00"]
    for i, v in enumerate(vaqt_label):
        matrix[2 + i][2] = v

    # Darslarni joylashtirish
    lessons = schedule.get(day_type, [])
    for lesson in lessons:
        if lesson.get("status") != 2:
            continue
        result = _lesson_to_cell(lesson, day_type)
        if result:
            row, col, text = result
            # 0-indexed ga o'tkazamiz
            if 0 <= row < len(matrix) and 0 <= col < 15:
                if matrix[row][col]:
                    matrix[row][col] += "\n" + text
                else:
                    matrix[row][col] = text

    return matrix


async def write_schedule_to_sheets() -> str:
    """LMS dan dars jadvalini olib Google Sheets (sheet20) ga matritsa shaklida yozadi."""
    import asyncio
    import gspread

    try:
        # 1. LMS dan schedule olish
        schedule = await asyncio.to_thread(fetch_branch_schedule)
        odd_count = len(schedule["odd"])
        even_count = len(schedule["even"])

        if not schedule["odd"] and not schedule["even"]:
            return "⚠️ LMS dan dars jadvali topilmadi."

        # 2. Google Sheets ga ulanish
        creds_json = os.getenv("GOOGLE_CREDS")
        if not creds_json:
            return "⚠️ GOOGLE_CREDS topilmadi."

        creds = json.loads(creds_json)
        client = gspread.service_account_from_dict(creds)
        spreadsheet = client.open_by_key(SHEET_ID)

        # Sheet20 ni olish yoki yaratish
        try:
            sheet = spreadsheet.worksheet(SHEET_NAME)
        except Exception:
            # Agar topilmasa yoki boshqa xatolik bo'lsa
            try:
                sheet = spreadsheet.add_worksheet(SHEET_NAME, rows=20, cols=15)
            except Exception:
                # Allaqachon mavjud bo'lsa
                sheet = spreadsheet.worksheet(SHEET_NAME)

        # 3. Sheetni tozalash
        sheet.clear()

        # 4. Odd va Even kunlar uchun alohida section yozish
        # Avval Toq kunlar
        odd_matrix = build_matrix_data(schedule, "odd")
        _write_matrix(sheet, odd_matrix, start_row=0)

        # Keyin Juft kunlar (8 qator pastga)
        even_matrix = build_matrix_data(schedule, "even")
        _write_matrix(sheet, even_matrix, start_row=9)

        return (
            f"✅ Dars jadvali Google Sheets ga yozildi!\n\n"
            f"📊 Toq kunlar: {odd_count} ta dars\n"
            f"📊 Juft kunlar: {even_count} ta dars\n"
            f"📋 Sheet: {SHEET_NAME}"
        )

    except gspread.exceptions.WorksheetNotFound:
        return f"⚠️ '{SHEET_NAME}' varag'i topilmadi."
    except Exception as e:
        logger.error(f"Sheets export error: {e}")
        return f"❌ Xatolik: {str(e)[:200]}"


def _write_matrix(sheet, matrix: list[list[str]], start_row: int):
    """Matritsani Google Sheets ga yozadi."""
    cells = []
    for r_idx, row in enumerate(matrix):
        for c_idx, val in enumerate(row):
            if val:
                col_letter = chr(65 + c_idx)  # A, B, C, ...
                cell_ref = f"{col_letter}{start_row + r_idx + 1}"
                cells.append({"range": cell_ref, "values": [[val]]})

    # Batch update qilish
    if cells:
        sheet.batch_update(cells)
