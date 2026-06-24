"""
LMS dan dars jadvalini olib, Google Sheets ga MATRITSA formatida yozish.
Sheet20 1:1 formati — ranglar, merge, bold bilan.
"""
import os, json, re, logging
from urllib.parse import unquote
from html import unescape

logger = logging.getLogger(__name__)

SHEET_ID = "1PpGWObeppzsSkaYgGz0fRYP_3zk-3YuxBOXStrn_PCc"
SHEET_NAME = "DarsJadval"
DRUJBA_BRANCH_ID = 3
LMS_BASE = "https://main.ieltszoneapp.uz"

# Vaqt → qator raqami (sheet20 da)
TIME_TO_ROW = {
    "08:00": 4, "10:00": 5, "14:00": 6,
    "16:00": 7, "18:00": 8, "20:00": 9,
}

# LMS xona nomi → ustun raqami (sheet20 da)
ROOM_NAME_TO_COL = {
    "101": 4, "102": 5, "103": 6, "104": 7, "105": 8,
    "106": 9, "107": 10, "108": 11, "109": 12, "110": 13, "111": 14,
}

# Vaqt label
TIME_LABELS = ["08:00", "10:00", "14:00", "16:00", "18:00", "20:00"]

# LEVEL → RANG (RGB float)
LEVEL_COLORS = {
    "ielts": {"red": 1.0, "green": 0.0, "blue": 0.0},       # RED
    "pre-intermediate": {"red": 0.0, "green": 1.0, "blue": 0.0},  # GREEN
    "intermediate": {"red": 0.0, "green": 1.0, "blue": 0.0},
    "elementary": {"red": 0.0, "green": 1.0, "blue": 0.0},
    "beginner": {"red": 1.0, "green": 1.0, "blue": 0.0},     # YELLOW
    "general english": {"red": 1.0, "green": 1.0, "blue": 0.0},
}
DEFAULT_BG = {"red": 1.0, "green": 1.0, "blue": 1.0}  # White

# Odatiy formatlar
CELL_FORMAT = {
    "borders": {
        "top": {"style": "SOLID", "width": 1},
        "bottom": {"style": "SOLID", "width": 1},
        "left": {"style": "SOLID", "width": 1},
        "right": {"style": "SOLID", "width": 1},
    },
}


def _get_session():
    import requests
    from Handlers.group_report import _get_lms_session
    return _get_lms_session()


def fetch_branch_schedule() -> dict:
    """LMS /admin/branches/3 dan dars jadvalini oladi."""
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
    }


def _get_level_color(level_name: str) -> dict:
    """Level nomidan rangni aniqlaydi."""
    level_lower = level_name.lower().strip()
    for key, color in LEVEL_COLORS.items():
        if key in level_lower:
            return color
    return DEFAULT_BG


def _col_letter(col: int) -> str:
    """Ustun raqamidan harf (1=A, 2=B, ...)."""
    result = ""
    while col > 0:
        col, remainder = divmod(col - 1, 26)
        result = chr(65 + remainder) + result
    return result


async def write_schedule_to_sheets() -> str:
    """LMS dan dars jadvalini olib Google Sheets (DarsJadval) ga 1:1 formatda yozadi."""
    import asyncio
    import gspread

    try:
        # 1. LMS dan schedule olish
        schedule = await asyncio.to_thread(fetch_branch_schedule)

        # 2. Google Sheets ga ulanish
        creds_json = os.getenv("GOOGLE_CREDS")
        if not creds_json:
            return "⚠️ GOOGLE_CREDS topilmadi."
        creds = json.loads(creds_json)
        client = gspread.service_account_from_dict(creds)
        spreadsheet = client.open_by_key(SHEET_ID)

        # Sheetni olish
        try:
            sheet = spreadsheet.worksheet(SHEET_NAME)
        except Exception:
            sheet = spreadsheet.add_worksheet(SHEET_NAME, rows=20, cols=15)

        # 3. To'liq tozalash
        sheet.clear()

        # 4. Strukturani qurish
        await _build_sheet20_structure(sheet)

        # 5. Ma'lumotlarni yozish (Odd + Even)
        all_data = {}  # (row, col) -> (text, level_name)

        for day_type in ["odd", "even"]:
            row_offset = 0 if day_type == "odd" else 7
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

                name = lesson.get("name", "")
                gid = lesson.get("id", "?")
                teacher = (lesson.get("teacher") or {}).get("first_name", "")
                course = (lesson.get("sub_course") or lesson.get("course") or {})
                level = course.get("name", {}).get("uz", course.get("name", {}).get("en", "—"))

                text = f"#{gid} {teacher}\n{level}"

                if (actual_row, col) in all_data:
                    all_data[(actual_row, col)]["text"] += "\n" + text
                else:
                    all_data[(actual_row, col)] = {"text": text, "level": level}

        # 6. Kataklarga yozish + formatlash
        batch_updates = []
        for (row, col), info in all_data.items():
            ref = f"{_col_letter(col)}{row}"
            color = _get_level_color(info["level"])
            batch_updates.append({
                "range": ref,
                "values": [[info["text"]]],
            })

        if batch_updates:
            sheet.batch_update(batch_updates)

        # 7. Ma'lumot kataklarini formatlash
        for (row, col), info in all_data.items():
            ref = f"{_col_letter(col)}{row}"
            color = _get_level_color(info["level"])
            try:
                sheet.format(ref, {
                    "backgroundColor": color,
                    "textFormat": {"fontSize": 8, "bold": False},
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "borders": CELL_FORMAT["borders"],
                })
            except Exception:
                pass

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


async def _build_sheet20_structure(sheet):
    """Sheet20 strukturasi va formatini qurish."""
    import gspread

    batch_updates = []

    # === ROW 2: Dars xonalari sarlavhasi ===
    sheet.merge_cells(2, 3, 2, 14)  # C2:N2
    batch_updates.append({"range": "C2", "values": [["Dars xonalari"]]})
    sheet.format("C2:N2", {
        "backgroundColor": {"red": 0.0, "green": 1.0, "blue": 1.0},  # CYAN
        "textFormat": {"bold": True, "fontSize": 14},
        "horizontalAlignment": "CENTER",
        "borders": CELL_FORMAT["borders"],
    })

    # === ROW 3: Xona sarlavhalari ===
    for i in range(1, 12):
        col = i + 3
        ref = f"{_col_letter(col)}3"
        batch_updates.append({"range": ref, "values": [[f"{i} xona"]]})
        sheet.format(ref, {
            "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 0.0},  # YELLOW
            "textFormat": {"bold": True, "fontSize": 10},
            "horizontalAlignment": "CENTER",
            "borders": CELL_FORMAT["borders"],
        })

    # === ROW 4-9 (Toq): Dars vaqtlari + Vaqtlar ===
    sheet.merge_cells(4, 2, 9, 2)  # B4:B9
    batch_updates.append({"range": "B4", "values": [["Dars vaqtlari"]]})
    sheet.format("B4:B9", {
        "textFormat": {"bold": True, "fontSize": 14},
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE",
        "borders": CELL_FORMAT["borders"],
    })

    for i, time_label in enumerate(TIME_LABELS):
        row = 4 + i
        ref = f"C{row}"
        batch_updates.append({"range": ref, "values": [[f"{time_label}:00"]]})
        is_bold = i >= 2  # 14:00 dan boshlab bold
        sheet.format(ref, {
            "textFormat": {"bold": is_bold, "fontSize": 10},
            "horizontalAlignment": "CENTER",
            "borders": CELL_FORMAT["borders"],
        })

    # === ROW 11-16 (Juft): xuddi shunday ===
    sheet.merge_cells(11, 2, 16, 2)  # B11:B16
    batch_updates.append({"range": "B11", "values": [["Dars vaqtlari"]]})
    sheet.format("B11:B16", {
        "textFormat": {"bold": True, "fontSize": 14},
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE",
        "borders": CELL_FORMAT["borders"],
    })

    for i, time_label in enumerate(TIME_LABELS):
        row = 11 + i
        ref = f"C{row}"
        batch_updates.append({"range": ref, "values": [[f"{time_label}:00"]]})
        is_bold = i >= 2
        sheet.format(ref, {
            "textFormat": {"bold": is_bold, "fontSize": 10},
            "horizontalAlignment": "CENTER",
            "borders": CELL_FORMAT["borders"],
        })

    # === ROW 11: Xona sarlavhalari (Juft) ===
    for i in range(1, 12):
        col = i + 3
        ref = f"{_col_letter(col)}10"
        batch_updates.append({"range": ref, "values": [[f"{i} xona"]]})
        sheet.format(ref, {
            "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 0.0},
            "textFormat": {"bold": True, "fontSize": 10},
            "horizontalAlignment": "CENTER",
            "borders": CELL_FORMAT["borders"],
        })

    # === ROW 10: Bo'sh ajratuvchi ===
    sheet.merge_cells(10, 3, 10, 14)  # C10:N10
    batch_updates.append({"range": "C10", "values": [["TOQ KUNLAR ⬆️ | ⬇️ JUFT KUNLAR"]]})
    sheet.format("C10:N10", {
        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
        "textFormat": {"bold": True, "fontSize": 10},
        "horizontalAlignment": "CENTER",
        "borders": CELL_FORMAT["borders"],
    })

    # === LEGEND (Row 18-21) ===
    legend = [
        (18, "🔴 IELTS (Novice, Standard, Expert, Intensive, Practice)"),
        (19, "🟩 Pre-Intermediate / Intermediate / Elementary"),
        (20, "🟨 Beginner / General English"),
        (21, "⬜ Dars yo'q"),
    ]
    for row, text in legend:
        sheet.merge_cells(row, 3, row, 8)
        ref = f"C{row}"
        batch_updates.append({"range": ref, "values": [[text]]})
        sheet.format(ref, {
            "textFormat": {"fontSize": 9},
            "horizontalAlignment": "LEFT",
        })

    # Qiymatlarni batch update
    if batch_updates:
        sheet.batch_update(batch_updates)

    # Ustun kengliklari
    sheet.resize(cols=14)  # N gacha
    sheet.resize(rows=21)

    # Ustun kengliklari
    try:
        body = {
            "requests": [
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet.id,
                            "dimension": "COLUMNS",
                            "startIndex": 1,
                            "endIndex": 2,
                        },
                        "properties": {"pixelSize": 75},
                        "fields": "pixelSize",
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet.id,
                            "dimension": "COLUMNS",
                            "startIndex": 2,
                            "endIndex": 3,
                        },
                        "properties": {"pixelSize": 100},
                        "fields": "pixelSize",
                    }
                },
            ]
        }
        sheet.spreadsheet.batch_update({"requests": body["requests"]})
    except Exception:
        pass
