"""
LMS dan dars jadvalini olib, Google Sheets ga MATRITSA formatida yozish.
Sheet20 1:1 — qiymatlar update() orqali, formatlar batch_update orqali.
"""
import os, json, re, logging
from urllib.parse import unquote
from html import unescape

logger = logging.getLogger(__name__)

SHEET_ID = "1PpGWObeppzsSkaYgGz0fRYP_3zk-3YuxBOXStrn_PCc"
SHEET_NAME = "DarsJadval"
DRUJBA_BRANCH_ID = 3
LMS_BASE = "https://main.ieltszoneapp.uz"

TIME_TO_ROW = {"08:00": 3, "10:00": 4, "14:00": 5, "16:00": 6, "18:00": 7, "20:00": 8}
ROOM_NAME_TO_COL = {
    "101": 3, "102": 4, "103": 5, "104": 6, "105": 7,
    "106": 8, "107": 9, "108": 10, "109": 11, "110": 12, "111": 13,
}
TIME_LABELS = ["08:00", "10:00", "14:00", "16:00", "18:00", "20:00"]


def _get_level_color(level_name: str) -> dict:
    ll = level_name.lower().strip()
    if "ielts" in ll:
        return {"red": 1.0, "green": 0.0, "blue": 0.0}
    if any(k in ll for k in ["pre-intermediate", "intermediate", "elementary"]):
        return {"red": 0.0, "green": 1.0, "blue": 0.0}
    if any(k in ll for k in ["beginner", "general english", "novice"]):
        return {"red": 1.0, "green": 1.0, "blue": 0.0}
    return {"red": 1.0, "green": 1.0, "blue": 1.0}


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
            sheet = ss.add_worksheet(SHEET_NAME, rows=25, cols=15)

        # 1. Tozalash
        sheet.clear()

        # 2. MATRITSA QURISH (0-indexed, 22 qator x 15 ustun)
        matrix = [[""] * 15 for _ in range(22)]

        # === TOQ KUNLAR (Row 1-9, 0-indexed) ===
        matrix[1][2] = "Dars xonalari"                         # C2
        for i in range(11):
            matrix[2][3+i] = f"{i+1} xona"                     # D3-N3
        matrix[3][1] = "Dars\nvaqtlari"                        # B4
        for i, t in enumerate(TIME_LABELS):
            matrix[3+i][2] = f"{t}:00"                         # C4-C9

        # === JUFT KUNLAR (Row 10-17, 0-indexed) ===
        matrix[9][2] = "⬆️ TOQ  |  ⬇️ JUFT"                   # C10
        matrix[10][2] = "Dars xonalari"                        # C11
        for i in range(11):
            matrix[10][3+i] = f"{i+1} xona"                    # D11-N11
        matrix[11][1] = "Dars\nvaqtlari"                       # B12
        for i, t in enumerate(TIME_LABELS):
            matrix[11+i][2] = f"{t}:00"                        # C12-C17

        # === DATA ===
        data_levels = {}  # (row_0idx, col_0idx) -> level_name

        for day_type in ["odd", "even"]:
            row_offset = 0 if day_type == "odd" else 8
            for lesson in schedule[day_type]:
                if lesson.get("status") != 2:
                    continue
                st = str(lesson.get("lesson_start_time", ""))[:5]
                rn = str(lesson.get("room", {}).get("name", ""))
                row = TIME_TO_ROW.get(st)
                col = ROOM_NAME_TO_COL.get(rn)
                if not row or not col:
                    continue

                r_idx = row + row_offset  # 0-indexed
                gid = lesson.get("id", "?")
                teacher = (lesson.get("teacher") or {}).get("first_name", "")
                course = (lesson.get("sub_course") or lesson.get("course") or {})
                level = course.get("name", {}).get("uz", course.get("name", {}).get("en", "—"))
                text = f"#{gid} {teacher}\n{level}"

                if matrix[r_idx][col]:
                    matrix[r_idx][col] += "\n" + text
                else:
                    matrix[r_idx][col] = text
                data_levels[(r_idx, col)] = level

        # === LEGEND ===
        matrix[18][2] = "🔴 IELTS (Novice, Standard, Expert, Intensive)"
        matrix[19][2] = "🟩 Pre-Intermediate / Intermediate / Elementary"
        matrix[20][2] = "🟨 Beginner / General English"
        matrix[21][2] = "⬜ Dars yo'q"

        # 3. Qiymatlarni yozish (A1:O22)
        sheet.update("A1:O22", matrix)

        # 4. FORMATLAR (batch_update)
        sheet_id = sheet.id
        border = {"top": {"style": "SOLID"}, "bottom": {"style": "SOLID"},
                  "left": {"style": "SOLID"}, "right": {"style": "SOLID"}}

        def _fmt(sr, sc, er, ec, f):
            """Format range: 1-indexed start_row, start_col, end_row, end_col."""
            return {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": sr-1, "endRowIndex": er,
                              "startColumnIndex": sc-1, "endColumnIndex": ec},
                    "cell": {"userEnteredFormat": f},
                    "fields": "userEnteredFormat",
                }
            }

        requests = [
            # MERGES
            {"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 2, "endColumnIndex": 14}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 2, "endColumnIndex": 14}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 3, "endRowIndex": 9, "startColumnIndex": 1, "endColumnIndex": 2}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 10, "startColumnIndex": 2, "endColumnIndex": 14}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 10, "endRowIndex": 11, "startColumnIndex": 2, "endColumnIndex": 14}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 11, "endRowIndex": 17, "startColumnIndex": 1, "endColumnIndex": 2}, "mergeType": "MERGE_ALL"}},

            # FORMATS
            # C2 (Dars xonalari) — CYAN
            _fmt(2, 3, 9, 14, {"backgroundColor": {"red": 0, "green": 1, "blue": 1}, "textFormat": {"bold": True, "fontSize": 14}, "horizontalAlignment": "CENTER"}),
            # D3-N3 (xonalar Toq) — YELLOW
            _fmt(3, 4, 9, 15, {"backgroundColor": {"red": 1, "green": 1, "blue": 0}, "textFormat": {"bold": True, "fontSize": 10}, "horizontalAlignment": "CENTER"}),
            # B4 — Dars vaqtlari vertikal
            _fmt(4, 2, 23, 3, {"textFormat": {"bold": True, "fontSize": 12}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "textRotation": {"vertical": True}}),
            # C4-C9 vaqtlar
            _fmt(4, 3, 15, 4, {"textFormat": {"fontSize": 10}, "horizontalAlignment": "CENTER"}),
            # C6-C9 14:00+ bold
            _fmt(6, 3, 23, 4, {"textFormat": {"bold": True, "fontSize": 10}, "horizontalAlignment": "CENTER"}),
            # C10 — ajratuvchi
            _fmt(10, 3, 10, 15, {"backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85}, "textFormat": {"bold": True, "fontSize": 10}, "horizontalAlignment": "CENTER"}),
            # C11 (Dars xonalari Juft)
            _fmt(11, 3, 23, 14, {"backgroundColor": {"red": 0, "green": 1, "blue": 1}, "textFormat": {"bold": True, "fontSize": 14}, "horizontalAlignment": "CENTER"}),
            # D12-N12 (xonalar Juft) — YELLOW
            _fmt(12, 4, 23, 15, {"backgroundColor": {"red": 1, "green": 1, "blue": 0}, "textFormat": {"bold": True, "fontSize": 10}, "horizontalAlignment": "CENTER"}),
            # B12 (Juft vaqtlari)
            _fmt(12, 2, 23, 3, {"textFormat": {"bold": True, "fontSize": 12}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "textRotation": {"vertical": True}}),
            # C12-C17 vaqtlar
            _fmt(12, 3, 23, 4, {"textFormat": {"fontSize": 10}, "horizontalAlignment": "CENTER"}),
            # C14-C17 14:00+ bold
            _fmt(14, 3, 23, 4, {"textFormat": {"bold": True, "fontSize": 10}, "horizontalAlignment": "CENTER"}),

            # BARCHA MA'LUMOT KATAKLARIGA BORDER + CENTER (Toq + Juft)
            _fmt(4, 4, 9, 15, {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "borders": border}),
            _fmt(12, 4, 17, 15, {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "borders": border}),
        ]

        # Data kataklari ranglari
        for (r, c), level in data_levels.items():
            color = _get_level_color(level)
            requests.append(_fmt(r+1, c+1, r+1, c+1, {
                "backgroundColor": color,
                "textFormat": {"fontSize": 8},
            }))

        # Ustun kengliklari
        requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
                "properties": {"pixelSize": 70}, "fields": "pixelSize",
            }
        })

        # Alohida-alohida yuborish
        for i, req in enumerate(requests):
            try:
                ss.batch_update({"requests": [req]})
            except Exception as e:
                err = str(e)[:100]
                if "already merged" not in err.lower():
                    logger.warning(f"Request {i} failed: {err}")

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
