"""
LMS dan dars jadvalini Google Sheets ga professional formatda yozish.
Spetsifikatsiya: muddatga qarab rang, och kulrang border, 3 qatorli matn.
"""
import os, json, re, logging
from datetime import datetime, timezone, timedelta
from urllib.parse import unquote
from html import unescape

logger = logging.getLogger(__name__)

SHEET_ID = "1PpGWObeppzsSkaYgGz0fRYP_3zk-3YuxBOXStrn_PCc"
SHEET_NAME = "DarsJadval"
DRUJBA_BRANCH_ID = 3
LMS_BASE = "https://main.ieltszoneapp.uz"
UZ_TZ = timezone(timedelta(hours=5))

# 2 soatlik vaqt bloklari
TIME_SLOTS = ["08:00", "10:00", "14:00", "16:00", "18:00", "20:00"]
TIME_TO_MATRIX_ROW = {t: i for i, t in enumerate(TIME_SLOTS)}  # 0-indexed

XONA_COUNT = 11
ROOM_NAME_TO_COL = {
    "101": 0, "102": 1, "103": 2, "104": 3, "105": 4,
    "106": 5, "107": 6, "108": 7, "109": 8, "110": 9, "111": 10,
}

# Ranglar (muddatga qarab)
COLOR_RED = {"red": 0.918, "green": 0.263, "blue": 0.208}        # #EA4335
COLOR_YELLOW = {"red": 0.984, "green": 0.737, "blue": 0.020}     # #FBBC05
COLOR_GREEN = {"red": 0.204, "green": 0.659, "blue": 0.325}      # #34A853
COLOR_GRAY = {"red": 0.788, "green": 0.855, "blue": 0.973}        # #C9DAF8 bo'sh slot
COLOR_HEADER_BG = {"red": 0.85, "green": 0.95, "blue": 1.0}      # och firuza
COLOR_XONA_BG = {"red": 1.0, "green": 0.95, "blue": 0.7}         # och sarg'ish

BORDER_GRAY = {
    "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
    "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
    "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
    "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
}

TODAY = datetime.now(UZ_TZ).date()


def _get_session():
    import requests
    from Handlers.group_report import _get_lms_session
    return _get_lms_session()


def fetch_branch_schedule() -> dict:
    import requests
    s = _get_session()
    r = s.get(f"{LMS_BASE}/admin/branches/{DRUJBA_BRANCH_ID}")
    match = re.search(r'data-page="([^"]*)"', r.text)
    if not match:
        raise Exception("data-page topilmadi")
    dp = json.loads(unescape(match.group(1)))
    p = dp["props"]
    return {"odd": p.get("oddDaysSchedule", {}).get("lessons", []),
            "even": p.get("evenDaysSchedule", {}).get("lessons", [])}


def _days_left(end_date_str: str) -> int:
    """Tugash sanasidan qolgan kunlar soni."""
    try:
        end_date = datetime.strptime(end_date_str[:10], "%Y-%m-%d").date()
        return (end_date - TODAY).days
    except Exception:
        return 999


def _color_by_days(days: int) -> dict:
    if days < 0:
        return COLOR_GRAY      # bo'sh slot
    elif days <= 14:
        return COLOR_RED
    elif days <= 30:
        return COLOR_YELLOW
    else:
        return COLOR_GREEN


async def write_schedule_to_sheets() -> str:
    import asyncio
    import gspread

    try:
        schedule = await asyncio.to_thread(fetch_branch_schedule)
        creds_json = os.getenv("GOOGLE_CREDS")
        if not creds_json:
            return "⚠️ GOOGLE_CREDS topilmadi."
        creds = json.loads(creds_json)
        client = gspread.service_account_from_dict(creds)
        ss = client.open_by_key(SHEET_ID)

        try:
            sheet = ss.worksheet(SHEET_NAME)
        except Exception:
            sheet = ss.add_worksheet(SHEET_NAME, rows=30, cols=16)

        sheet.clear()

        # ====== MATRITSA (0-indexed) ======
        TOTAL_ROWS = 23  # 6+1+6+1+legend
        MATRIX_COLS = 12  # A(vaqt) + B-L(xonalar 1-11)

        matrix = [[""] * MATRIX_COLS for _ in range(TOTAL_ROWS)]
        data_cells = {}  # (row_idx, col_idx) -> {"text": str, "days_left": int}

        def fill_matrix(lessons, start_row: int, label_slot_row: int):
            # Sarlavha
            matrix[start_row][0] = "Dars\nvaqtlari"
            matrix[label_slot_row][1] = "Dars xonalari"
            for x in range(XONA_COUNT):
                matrix[label_slot_row][2 + x] = f"{x+1} xona"

            # Vaqtlar
            for i, t in enumerate(TIME_SLOTS):
                matrix[start_row + 1 + i][0] = t

            # Ma'lumot
            for lesson in lessons:
                if lesson.get("status") != 2:
                    continue
                st = str(lesson.get("lesson_start_time", ""))[:5]
                rn = str(lesson.get("room", {}).get("name", ""))
                time_idx = TIME_TO_MATRIX_ROW.get(st)
                col = ROOM_NAME_TO_COL.get(rn)
                if time_idx is None or col is None:
                    continue

                row_idx = start_row + 1 + time_idx
                gid = lesson.get("id", "?")
                teacher = (lesson.get("teacher") or {}).get("first_name", "")
                course = (lesson.get("sub_course") or lesson.get("course") or {})
                level = course.get("name", {}).get("uz", course.get("name", {}).get("en", "—"))
                end_date = lesson.get("group_end_date", "")
                dl = _days_left(end_date)

                text = f"#{gid}\n{teacher}\n{level}"

                if (row_idx, col + 1) in data_cells:
                    data_cells[(row_idx, col + 1)]["text"] += "\n——\n" + text
                else:
                    data_cells[(row_idx, col + 1)] = {"text": text, "days_left": dl}

            # Bo'sh kataklarni to'ldirish — "Dars yo'q slot"
            for ti in range(len(TIME_SLOTS)):
                for xi in range(XONA_COUNT):
                    ri = start_row + 1 + ti
                    ci = xi + 1
                    if (ri, ci) not in data_cells:
                        matrix[ri][ci] = "Dars yo'q slot"
                        data_cells[(ri, ci)] = {"text": "Dars yo'q slot", "days_left": -1}

        # Toq kunlar (row 0-7)
        fill_matrix(schedule["odd"], start_row=0, label_slot_row=0)
        # Juft kunlar (row 9-16)
        fill_matrix(schedule["even"], start_row=9, label_slot_row=9)

        # Ajratuvchi
        matrix[8][0] = ""

        # Ma'lumotlarni matritsaga yozish
        for (ri, ci), info in data_cells.items():
            if 0 <= ri < TOTAL_ROWS and 0 <= ci < MATRIX_COLS:
                matrix[ri][ci] = info["text"]
            else:
                logger.warning(f"data_cells index xatosi: ri={ri}/{TOTAL_ROWS}, ci={ci}/{MATRIX_COLS}")

        # Legend
        matrix[19][1] = "Ranglar:"
        matrix[20][1] = "Qizil — tugashiga 2 haftadan kam"
        matrix[21][1] = "Sariq — 1 oydan 2 haftagacha"
        matrix[22][1] = "Yashil — 1 oydan ko'p"

        # ====== GOOGLE SHEETS GA YOZISH ======
        sheet.update(f"A1:L{TOTAL_ROWS}", matrix)

        sheet_id = sheet.id

        requests = []

        def _fmt(sr, sc, er, ec, f):
            return {
                "repeatCell": {
                    "range": {"sheetId": sheet_id,
                              "startRowIndex": sr, "endRowIndex": er,
                              "startColumnIndex": sc, "endColumnIndex": ec},
                    "cell": {"userEnteredFormat": f},
                    "fields": "userEnteredFormat",
                }
            }

        def _fmt_merge(sr, er, sc, ec):
            return {"mergeCells": {
                "range": {"sheetId": sheet_id,
                          "startRowIndex": sr, "endRowIndex": er,
                          "startColumnIndex": sc, "endColumnIndex": ec},
                "mergeType": "MERGE_ALL",
            }}

        # === MERGES ===
        # Dars xonalari (Toq) — C2:L2
        requests.append(_fmt_merge(0, 1, 2, 12))
        # Dars vaqtlari (Toq) — A2:A7
        requests.append(_fmt_merge(0, 7, 0, 1))
        # Dars xonalari (Juft) — C11:L11
        requests.append(_fmt_merge(9, 10, 2, 12))
        # Dars vaqtlari (Juft) — A11:A16
        requests.append(_fmt_merge(9, 16, 0, 1))

        # === FORMATS ===
        # Sarlavha: Dars xonalari
        for label_row in [0, 9]:
            requests.append(_fmt(label_row, 1, label_row + 1, 12, {
                "backgroundColor": COLOR_HEADER_BG,
                "textFormat": {"bold": True, "fontSize": 12},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "borders": BORDER_GRAY,
            }))
            # Xona raqamlari
            requests.append(_fmt(label_row, 2, label_row + 1, 12, {
                "backgroundColor": COLOR_XONA_BG,
                "textFormat": {"bold": True, "fontSize": 10},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "borders": BORDER_GRAY,
            }))

        # Dars vaqtlari (vertikal, bold)
        for vaqt_row_start in [0, 9]:
            requests.append(_fmt(vaqt_row_start, 0, vaqt_row_start + 7, 1, {
                "textFormat": {"bold": True, "fontSize": 10},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "borders": BORDER_GRAY,
            }))

        # Vaqt qiymatlari (A3:A8 va A12:A17)
        for base in [1, 10]:
            for i in range(6):
                ri = base + i
                requests.append(_fmt(ri, 0, ri + 1, 1, {
                    "textFormat": {"fontSize": 10},
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "borders": BORDER_GRAY,
                }))

        # BARCHA MA'LUMOT KATAKLARIGA border + center (Toq: B3:L8, Juft: B12:L17)
        requests.append(_fmt(1, 1, 8, 12, {
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
            "borders": BORDER_GRAY,
        }))
        requests.append(_fmt(10, 1, 17, 12, {
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
            "borders": BORDER_GRAY,
        }))

        # Data kataklari: rang + fontSize
        for (ri, ci), info in data_cells.items():
            color = _color_by_days(info["days_left"])
            fmt = {
                "backgroundColor": color,
                "textFormat": {"fontSize": 9},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "borders": BORDER_GRAY,
            }
            if info["days_left"] < 0:
                fmt["textFormat"]["foregroundColor"] = {"red": 0.5, "green": 0.5, "blue": 0.5}
            requests.append(_fmt(ri, ci, ri + 1, ci + 1, fmt))

        # Ustun kengliklari
        requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                "properties": {"pixelSize": 80}, "fields": "pixelSize",
            }
        })
        for ci in range(1, 12):
            requests.append({
                "updateDimensionProperties": {
                    "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": ci, "endIndex": ci + 1},
                    "properties": {"pixelSize": 120}, "fields": "pixelSize",
                }
            })

        # Barcha so'rovlarni yuborish
        for i in range(0, len(requests), 50):
            batch = requests[i:i+50]
            try:
                ss.batch_update({"requests": batch})
            except Exception as e:
                logger.warning(f"Batch {i//50}: {str(e)[:120]}")

        odd_count = len(schedule["odd"])
        even_count = len(schedule["even"])
        return (
            f"✅ Dars jadvali Google Sheets ga yozildi!\n\n"
            f"📊 Toq kunlar: {odd_count} ta dars\n"
            f"📊 Juft kunlar: {even_count} ta dars\n"
            f"📋 Sheet: {SHEET_NAME}"
        )

    except Exception as e:
        logger.error(f"Sheets export error: {e}")
        return f"❌ Xatolik: {str(e)[:200]}"
