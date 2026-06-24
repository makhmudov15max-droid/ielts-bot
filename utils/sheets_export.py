"""
LMS dan dars jadvalini olib, Google Sheets ga MATRITSA formatida yozish.
Sheet20 1:1 formati — ranglar, merge, border, vertikal matn bilan.
"""
import os, json, re, logging
from urllib.parse import unquote
from html import unescape

logger = logging.getLogger(__name__)

SHEET_ID = "1PpGWObeppzsSkaYgGz0fRYP_3zk-3YuxBOXStrn_PCc"
SHEET_NAME = "DarsJadval"
DRUJBA_BRANCH_ID = 3
LMS_BASE = "https://main.ieltszoneapp.uz"

TIME_TO_ROW = {"08:00": 4, "10:00": 5, "14:00": 6, "16:00": 7, "18:00": 8, "20:00": 9}
ROOM_NAME_TO_COL = {
    "101": 4, "102": 5, "103": 6, "104": 7, "105": 8,
    "106": 9, "107": 10, "108": 11, "109": 12, "110": 13, "111": 14,
}
TIME_LABELS = ["08:00", "10:00", "14:00", "16:00", "18:00", "20:00"]

# LEVEL → RANG (RGBA float 0-1)
def _get_level_color(level_name: str) -> dict:
    level_lower = level_name.lower().strip()
    if "ielts" in level_lower:
        return {"red": 1.0, "green": 0.0, "blue": 0.0}       # RED
    if any(k in level_lower for k in ["pre-intermediate", "intermediate", "elementary"]):
        return {"red": 0.0, "green": 1.0, "blue": 0.0}       # GREEN
    if any(k in level_lower for k in ["beginner", "general english", "novice"]):
        return {"red": 1.0, "green": 1.0, "blue": 0.0}       # YELLOW
    return {"red": 1.0, "green": 1.0, "blue": 1.0}           # WHITE


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
        raise Exception("LMS branch sahifasidan data-page topilmadi")
    dp = json.loads(unescape(match.group(1)))
    props = dp["props"]
    odd = props.get("oddDaysSchedule", {})
    even = props.get("evenDaysSchedule", {})
    return {"odd": odd.get("lessons", []), "even": even.get("lessons", [])}


def _solid_border() -> dict:
    return {
        "top": {"style": "SOLID"},
        "bottom": {"style": "SOLID"},
        "left": {"style": "SOLID"},
        "right": {"style": "SOLID"},
    }


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
        spreadsheet = client.open_by_key(SHEET_ID)

        try:
            sheet = spreadsheet.worksheet(SHEET_NAME)
        except Exception:
            sheet = spreadsheet.add_worksheet(SHEET_NAME, rows=25, cols=15)

        sheet.clear()
        sheet_id = sheet.id

        requests_list = []

        # ======== MERGES ========
        merges = [
            (1, 2, 1, 13),   # C2:N2 — Dars xonalari
            (2, 2, 2, 13),   # C3:N3 — Toq kunlar label
            (3, 1, 8, 1),    # B4:B9 — Dars vaqtlari (Toq)
            (9, 2, 9, 13),   # C10:N10 — Ajratuvchi
            (10, 2, 10, 13), # C11:N11 — Juft kunlar label
            (10, 1, 15, 1),  # B11:B16 — Dars vaqtlari (Juft)
        ]
        for start_row, start_col, end_row, end_col in merges:
            requests_list.append({
                "mergeCells": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": start_row,
                        "endRowIndex": end_row + 1,
                        "startColumnIndex": start_col,
                        "endColumnIndex": end_col + 1,
                    },
                    "mergeType": "MERGE_ALL",
                }
            })

        # ======== VALUES ========
        values_list = [
            # Row 2: Dars xonalari
            (2, 3, "Dars xonalari"),
            # Row 3: Xona sarlavhalari
            *[(3, 4 + i, f"{i+1} xona") for i in range(11)],
            # Row 4-9: Dars vaqtlari + vaqtlar (Toq)
            (4, 2, "Dars\nvaqtlari"),
            *[(4 + i, 3, f"{TIME_LABELS[i]}:00") for i in range(6)],
            # Row 10: Ajratuvchi
            (10, 3, "⬆️ TOQ KUNLAR  |  ⬇️ JUFT KUNLAR"),
            # Row 11: Juft kunlar label
            (11, 3, "Dars xonalari"),
            # Row 11: Xona sarlavhalari (Juft)
            *[(11, 4 + i, f"{i+1} xona") for i in range(11)],
            # Row 12-17: Dars vaqtlari + vaqtlar (Juft)
            (12, 2, "Dars\nvaqtlari"),
            *[(12 + i, 3, f"{TIME_LABELS[i]}:00") for i in range(6)],
            # Legend
            (19, 3, "🔴 IELTS (Novice, Standard, Expert, Intensive)"),
            (20, 3, "🟩 Pre-Intermediate / Intermediate / Elementary"),
            (21, 3, "🟨 Beginner / General English"),
            (22, 3, "⬜ Dars yo'q"),
        ]

        # Ma'lumot kataklari
        data_cells = {}  # (row, col) -> text
        all_levels = {}  # (row, col) -> level_name

        for day_type in ["odd", "even"]:
            row_offset = 0 if day_type == "odd" else 8
            for lesson in schedule[day_type]:
                if lesson.get("status") != 2:
                    continue
                start_time = str(lesson.get("lesson_start_time", ""))[:5]
                room_name = str(lesson.get("room", {}).get("name", ""))
                row = TIME_TO_ROW.get(start_time)
                col = ROOM_NAME_TO_COL.get(room_name)
                if not row or not col:
                    continue

                actual_row = row + row_offset
                gid = lesson.get("id", "?")
                teacher = (lesson.get("teacher") or {}).get("first_name", "")
                course = (lesson.get("sub_course") or lesson.get("course") or {})
                level = course.get("name", {}).get("uz", course.get("name", {}).get("en", "—"))
                text = f"#{gid} {teacher}\n{level}"

                key = (actual_row, col)
                if key in data_cells:
                    data_cells[key] += "\n" + text
                else:
                    data_cells[key] = text
                    all_levels[key] = level

        # Data kataklarini values_list ga qo'shish
        for (row, col), text in data_cells.items():
            values_list.append((row, col, text))

        # Qiymatlarni bitta so'rovda yozish
        for row, col, val in values_list:
            requests_list.append({
                "updateCells": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row - 1,
                        "endRowIndex": row,
                        "startColumnIndex": col - 1,
                        "endColumnIndex": col,
                    },
                    "rows": [{"values": [{"userEnteredValue": {"stringValue": val}}]}],
                    "fields": "userEnteredValue",
                }
            })

        # ======== FORMATS ========
        # Header formats
        fmt_solid = {"style": "SOLID"}
        border = {"top": fmt_solid, "bottom": fmt_solid, "left": fmt_solid, "right": fmt_solid}

        format_specs = [
            # C2:N2 — Cyan sarlavha
            (2, 3, 2, 14, {"backgroundColor": {"red": 0, "green": 1, "blue": 1}, "textFormat": {"bold": True, "fontSize": 14}, "horizontalAlignment": "CENTER", "borders": border}),
            # Row 3 xonalar — Yellow
            (3, 4, 3, 15, {"backgroundColor": {"red": 1, "green": 1, "blue": 0}, "textFormat": {"bold": True, "fontSize": 10}, "horizontalAlignment": "CENTER", "borders": border}),
            # B4:B9 — Dars vaqtlari vertikal
            (4, 2, 9, 3, {"textFormat": {"bold": True, "fontSize": 12}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "textRotation": {"vertical": True}, "borders": border}),
            # C4:C9 — Vaqtlar
            (4, 3, 9, 4, {"textFormat": {"fontSize": 10}, "horizontalAlignment": "CENTER", "borders": border}),
            # C6:C9 — 14:00+ bold
            (6, 3, 9, 4, {"textFormat": {"bold": True, "fontSize": 10}, "horizontalAlignment": "CENTER", "borders": border}),
            # Ma'lumot kataklari (D4:N9) — border + center
            (4, 4, 9, 15, {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "borders": border}),
            # C10:N10 — Ajratuvchi
            (10, 3, 10, 15, {"backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85}, "textFormat": {"bold": True, "fontSize": 10}, "horizontalAlignment": "CENTER", "borders": border}),
            # Row 11 xonalar — Yellow (Juft)
            (11, 4, 11, 15, {"backgroundColor": {"red": 1, "green": 1, "blue": 0}, "textFormat": {"bold": True, "fontSize": 10}, "horizontalAlignment": "CENTER", "borders": border}),
            # B12:B17 — Dars vaqtlari vertikal (Juft)
            (12, 2, 17, 3, {"textFormat": {"bold": True, "fontSize": 12}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "textRotation": {"vertical": True}, "borders": border}),
            # C12:C17 — Vaqtlar (Juft)
            (12, 3, 17, 4, {"textFormat": {"fontSize": 10}, "horizontalAlignment": "CENTER", "borders": border}),
            # C14:C17 — 14:00+ bold
            (14, 3, 17, 4, {"textFormat": {"bold": True, "fontSize": 10}, "horizontalAlignment": "CENTER", "borders": border}),
            # Ma'lumot kataklari (D12:N17) — border + center (Juft)
            (12, 4, 17, 15, {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "borders": border}),
        ]

        for start_row, start_col, end_row, end_col, fmt in format_specs:
            requests_list.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": start_row - 1,
                        "endRowIndex": end_row,
                        "startColumnIndex": start_col - 1,
                        "endColumnIndex": end_col,
                    },
                    "cell": {"userEnteredFormat": fmt},
                    "fields": "userEnteredFormat",
                }
            })

        # Ma'lumot kataklari uchun rang + fontSize=8
        for (row, col), level in all_levels.items():
            color = _get_level_color(level)
            requests_list.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row - 1,
                        "endRowIndex": row,
                        "startColumnIndex": col - 1,
                        "endColumnIndex": col,
                    },
                    "cell": {"userEnteredFormat": {"backgroundColor": color, "textFormat": {"fontSize": 8}}},
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            })

        # ======== USTUN KENGLIKLARI ========
        requests_list.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
                "properties": {"pixelSize": 70},
                "fields": "pixelSize",
            }
        })

        # ======== YUBORISH ========
        # Batch 100 tadan
        for i in range(0, len(requests_list), 100):
            batch = requests_list[i:i+100]
            try:
                spreadsheet.batch_update({"requests": batch})
            except Exception as e:
                logger.warning(f"Batch {i//100} error: {e}")

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
