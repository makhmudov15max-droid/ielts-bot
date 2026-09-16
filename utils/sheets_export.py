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

# ====== USTOZLAR BAND/BO'SH SLOT JADVALI (O ustundan boshlab) ======
# Jadval O2:AA14 da joylashadi — DarsJadval matritsasining yonida.
# Ustozlar LMS teacher ID lari bo'yicha aniqlanadi.
TEACHER_SLOTS_COL_START = 15          # O ustuni (1-based: O = 15)
TEACHER_SLOTS_ROW_START = 2           # O2
# (ko'rsatiladigan nom, LMS teacher_id, nom bo'yicha qidiruv kalitlari)
# LMS'da teacher_id bo'sh bo'lgan guruhlar bor — ular guruh nomidan aniqlanadi.
# Masalan "125/4 pm Akhmadali T SENTABR OXIRIGA OCHILADI" → Ahmadali
TEACHER_COLUMNS = [
    ("Adxambek I",       380,   ["adkhambek", "adxambek", "adxam"]),
    ("Sardor",           374,   ["sardor"]),
    ("Ahmadali",         382,   ["akhmadali", "ahmadali", "axmadali"]),
    ("Otabek",           38,    ["otabek"]),
    ("Obidjon",          384,   ["obidjon"]),
    ("Xurshid",          6844,  ["khurshid", "xurshid"]),
    ("Odiljon",          11506, ["odiljon"]),
    ("Ibrohim",          24010, ["ibrokhim", "ibrohim"]),
    ("Farangiz",         6836,  ["farangiz e"]),   # Farangiz Elamanova
    ("Nilufar",          485,   ["nilufar"]),
    ("Diyora",           20105, ["diyora"]),
    ("Farangiz (freya)", 27737, ["farangiz i", "freya"]),  # Farangiz Izzatullayeva
]
TEACHER_SLOT_TIMES = ["8:00", "10:00", "14:00", "16:00", "18:00"]
# Google Sheets vaqt yorliqlarini avtomatik parse qilmasligi uchun apostrof bilan himoyalaymiz
TEACHER_SLOT_TIMES_SAFE = ["'8:00", "'10:00", "'14:00", "'16:00", "'18:00"]

# Ranglar (namuna jadvaldan olingan)
TS_HEADER_BG = {"red": 0.7176471, "green": 0.7176471, "blue": 0.7176471}  # #B7B7B7
TS_HEADER_BG2 = {"red": 0.8509804, "green": 0.8509804, "blue": 0.8509804} # #D9D9D9
TS_TRUE_BG = {"red": 0.0, "green": 1.0, "blue": 0.0}                      # yashil — band
TS_FALSE_BG = {"red": 1.0, "green": 1.0, "blue": 1.0}                     # oq — ochiq
TS_FALSE_EARLY_BG = {"red": 0.95686275, "green": 0.8, "blue": 0.8}        # qizg'ish — 8:00 ochiq

# Vaqt bloklari — 18:30/19:00 → 18:00 ga birlashadi
TIME_SLOTS = ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00"]
TIME_TO_MATRIX_ROW = {t: i for i, t in enumerate(TIME_SLOTS)}

XONALAR = ["101", "102", "103", "104", "105", "106", "107", "108", "109", "110", "111"]
XONA_COUNT = len(XONALAR)
ROOM_NAME_TO_COL = {rn: i for i, rn in enumerate(XONALAR)}

def _normalize_time(st: str) -> str:
    """18:00 dan keyin boshlangan hamma dars → 18:00"""
    st = st[:5]
    if st >= "18:00":
        return "18:00"
    return st

# Ranglar
COLOR_RED = {"red": 0.918, "green": 0.263, "blue": 0.208}       # #EA4335
COLOR_YELLOW = {"red": 0.984, "green": 0.737, "blue": 0.020}    # #FBBC05
COLOR_GREEN = {"red": 0.204, "green": 0.659, "blue": 0.325}     # #34A853
COLOR_BLUE = {"red": 0.788, "green": 0.855, "blue": 0.973}      # #C9DAF8 bo'sh slot
COLOR_HEADER = {"red": 0.004, "green": 0.945, "blue": 0.698}    # #01F1B2 sarlavha

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
    if r.status_code in (401, 403):
        raise Exception("LMS ga kira olmadim (401) — parol o'zgargan bo'lishi mumkin. "
                        "Railway env'da LMS_KEY ni yangilang.")
    match = re.search(r'data-page="([^"]*)"', r.text)
    if not match:
        raise Exception(f"data-page topilmadi (HTTP {r.status_code}, {len(r.text)} bayt). "
                        "LMS paroli o'zgargan yoki sahifa formati o'zgargan.")
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
    if days == -2:
        return COLOR_HEADER           # ⏳ ochilishi kutilmoqda
    elif days < 0:
        return COLOR_BLUE              # bo'sh slot
    elif days <= 14:
        return COLOR_RED
    elif days <= 30:
        return COLOR_YELLOW
    else:
        return COLOR_GREEN


def _build_teacher_slots(schedule: dict):
    """Ustozlar band/bo'sh slot matritsasini hisoblaydi.

    Returns: (busy_odd, busy_even) — har biri {teacher_id: set(vaqt label)}
    Status 1 (kutilayotgan) va 2 (aktiv) = band; boshqalar hisobga olinmaydi.
    teacher_id bo'sh bo'lsa guruh nomidan ustoz aniqlanadi (LMS quirk).
    """
    busy_odd = {}
    busy_even = {}

    slot_map = {"08:00": "8:00", "10:00": "10:00", "12:00": "10:00",
                "14:00": "14:00", "16:00": "16:00", "18:00": "18:00"}

    def resolve_teacher_id(lesson):
        """LMS teacher_id yoki guruh nomidan aniqlangan ID."""
        tid = (lesson.get("teacher") or {}).get("id") or lesson.get("teacher_id")
        if tid:
            return tid
        # teacher_id bo'sh — guruh nomidan qidiramiz
        gname = (lesson.get("name") or "").lower()
        if not gname:
            return None
        for _, t_id, keys in TEACHER_COLUMNS:
            for k in keys:
                if k in gname:
                    return t_id
        return None

    for lessons, busy in ((schedule.get("odd", []), busy_odd),
                          (schedule.get("even", []), busy_even)):
        for lesson in lessons:
            if lesson.get("status") not in (1, 2):
                continue
            tid = resolve_teacher_id(lesson)
            st = str(lesson.get("lesson_start_time", ""))[:5]
            if st >= "18:00":
                st = "18:00"
            label = slot_map.get(st)
            if label is None or tid is None:
                continue
            busy.setdefault(tid, set()).add(label)

    return busy_odd, busy_even


def write_teacher_slots(sheet, schedule, sheet_id, requests_out):
    """DarsJadval ichida O ustundan boshlab ustozlar band/bo'sh slot jadvalini yozadi.

    TOQ bloki: O2:AA7 | JUFT bloki: O9:AA14
    TRUE = band (yashil) | FALSE = slot ochiq (oq / 8:00 da qizg'ish)
    """
    busy_odd, busy_even = _build_teacher_slots(schedule)

    ncols = len(TEACHER_COLUMNS)
    start_col = TEACHER_SLOTS_COL_START
    start_row = TEACHER_SLOTS_ROW_START

    def col_letter(idx):
        s = ""
        while idx > 0:
            idx, rem = divmod(idx - 1, 26)
            s = chr(65 + rem) + s
        return s

    matrix = []
    for block, busy_map in (("TOQ", busy_odd), ("JUFT", busy_even)):
        matrix.append([block] + [name for name, _tid, _keys in TEACHER_COLUMNS])
        for label, label_safe in zip(TEACHER_SLOT_TIMES, TEACHER_SLOT_TIMES_SAFE):
            row = [label_safe]
            for _, tid, _keys in TEACHER_COLUMNS:
                row.append("TRUE" if label in busy_map.get(tid, set()) else "FALSE")
            matrix.append(row)
        matrix.append([""] * (ncols + 1))

    matrix = matrix[:-1]

    end_row = start_row + len(matrix) - 1
    rng = f"{col_letter(start_col)}{start_row}:{col_letter(start_col + ncols)}{end_row}"
    sheet.update(rng, matrix, value_input_option="USER_ENTERED")

    # ===== FORMATLASH =====
    def _fmt(sr, er, sc, ec, f):
        return {
            "repeatCell": {
                "range": {"sheetId": sheet_id,
                          "startRowIndex": sr, "endRowIndex": er,
                          "startColumnIndex": sc, "endColumnIndex": ec},
                "cell": {"userEnteredFormat": f},
                "fields": "userEnteredFormat",
            }
        }

    sc0 = start_col - 1
    ec0 = sc0 + ncols

    # TOQ sarlavha: start_row-1 = O2 (index 1). JUFT sarlavha: O9 (index 8)
    block_starts = [start_row, start_row + len(TEACHER_SLOT_TIMES) + 2]
    busy_maps = [busy_odd, busy_even]

    for bi, bs in enumerate(block_starts):
        # sarlavha qatori (ustoz ismlari) — namuna: birinchi 5 ta #B7B7B7, qolgani #D9D9D9
        requests_out.append(_fmt(bs - 1, bs, sc0, sc0 + 6, {
            "backgroundColor": TS_HEADER_BG,
            "textFormat": {"bold": False, "fontSize": 10},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "borders": BORDER_GRAY,
        }))
        requests_out.append(_fmt(bs - 1, bs, sc0 + 6, ec0, {
            "backgroundColor": TS_HEADER_BG2,
            "textFormat": {"bold": False, "fontSize": 10},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "borders": BORDER_GRAY,
        }))
        # vaqt ustuni
        requests_out.append(_fmt(bs, bs + len(TEACHER_SLOT_TIMES), sc0, sc0 + 1, {
            "backgroundColor": TS_FALSE_BG,
            "textFormat": {"bold": False, "fontSize": 10},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "borders": BORDER_GRAY,
        }))

        for ri, label in enumerate(TEACHER_SLOT_TIMES):
            abs_row = bs + ri
            for ci, (_, tid, _keys) in enumerate(TEACHER_COLUMNS):
                is_true = label in busy_maps[bi].get(tid, set())
                bg = TS_TRUE_BG if is_true else TS_FALSE_BG
                requests_out.append(_fmt(abs_row, abs_row + 1, sc0 + 1 + ci, sc0 + 2 + ci, {
                    "backgroundColor": bg,
                    "textFormat": {"bold": False, "fontSize": 9},
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "borders": BORDER_GRAY,
                }))

    # Ustun kengligi
    for ci in range(sc0, ec0):
        requests_out.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                          "startIndex": ci, "endIndex": ci + 1},
                "properties": {"pixelSize": 85 if ci == sc0 else 105},
                "fields": "pixelSize",
            }
        })

    # ===== CHECKBOX (Data Validation) =====
    # TRUE/FALSE qiymatlari checkbox bo'lib ko'rinadi — namuna jadvaldagi kabi.
    requests_out.append({
        "setDataValidation": {
            "range": {"sheetId": sheet_id,
                      "startRowIndex": block_starts[0],
                      "endRowIndex": block_starts[0] + len(TEACHER_SLOT_TIMES),
                      "startColumnIndex": sc0 + 1, "endColumnIndex": ec0},
            "rule": {"condition": {"type": "BOOLEAN"}, "strict": False, "showCustomUi": True},
        }
    })
    requests_out.append({
        "setDataValidation": {
            "range": {"sheetId": sheet_id,
                      "startRowIndex": block_starts[1],
                      "endRowIndex": block_starts[1] + len(TEACHER_SLOT_TIMES),
                      "startColumnIndex": sc0 + 1, "endColumnIndex": ec0},
            "rule": {"condition": {"type": "BOOLEAN"}, "strict": False, "showCustomUi": True},
        }
    })

    busy_count = sum(len(busy_odd.get(tid, set())) for _, tid, _keys in TEACHER_COLUMNS)
    busy_count += sum(len(busy_even.get(tid, set())) for _, tid, _keys in TEACHER_COLUMNS)
    return busy_count


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
            sheet = ss.add_worksheet(SHEET_NAME, rows=30, cols=13)

        sheet.clear()

        sheet_id = sheet.id
        MC = 1 + XONA_COUNT  # 12 cols: A(vaqt) + B-L(xonalar)

        # ====== MATRITSA ======
        TIME_COUNT = len(TIME_SLOTS)

        def build_section(lessons, base_row, section_label):
            data = {}
            # Section label
            matrix[base_row][0] = section_label
            # Soat / xona header
            matrix[base_row + 1][0] = "Soat / xona"
            for xi, xona in enumerate(XONALAR):
                matrix[base_row + 1][1 + xi] = xona
            # Time rows
            for ti, tm in enumerate(TIME_SLOTS):
                matrix[base_row + 2 + ti][0] = tm

            for lesson in lessons:
                if lesson.get("status") != 2:
                    continue
                st = _normalize_time(str(lesson.get("lesson_start_time", ""))[:5])
                rn = str(lesson.get("room", {}).get("name", ""))
                ti = TIME_TO_MATRIX_ROW.get(st)
                ci = ROOM_NAME_TO_COL.get(rn)
                if ti is None or ci is None:
                    continue

                ri = base_row + 2 + ti
                dc = ci + 1

                gid = lesson.get("id", "?")
                teacher = (lesson.get("teacher") or {}).get("first_name", "")
                course_obj = lesson.get("sub_course") or lesson.get("course") or {}
                level = course_obj.get("name", {}).get("uz", "?")
                end_date = lesson.get("group_end_date", "")
                dl = _days_left(end_date)
                text = f"#{gid}\n{teacher}\n{level}"

                key = (ri, dc)
                if key in data:
                    data[key]["text"] += f"\n——\n{text}"
                    data[key]["days"] = min(data[key]["days"], dl)
                else:
                    data[key] = {"text": text, "days": dl}

            # Bo'sh kataklar
            for ti in range(TIME_COUNT):
                for xi in range(XONA_COUNT):
                    ri = base_row + 2 + ti
                    dc = xi + 1
                    if (ri, dc) not in data:
                        s = "Dars yo'q slot"
                        matrix[ri][dc] = s
                        data[(ri, dc)] = {"text": s, "days": -1}

            return data

        # Build TOQ + JUFT, track which time rows are fully empty
        toq_base = 0
        juft_base = TIME_COUNT + 3  # TOQ(label+header+data) + separator

        # First pass: collect data without full matrix (we'll build after removing empties)
        def collect_raw(lessons):
            """Collect lessons by (time_idx, room_col). Returns (active, planned)."""
            active = {}
            planned = {}  # status=1 — kutilayotgan guruhlar
            for lesson in lessons:
                status = lesson.get("status")
                if status not in (1, 2):
                    continue
                st = _normalize_time(str(lesson.get("lesson_start_time", ""))[:5])
                rn = str(lesson.get("room", {}).get("name", ""))
                ti = TIME_TO_MATRIX_ROW.get(st)
                ci = ROOM_NAME_TO_COL.get(rn)
                if ti is None or ci is None:
                    continue
                key = (ti, ci)
                if status == 2:
                    gid = lesson.get("id", "?")
                    teacher = (lesson.get("teacher") or {}).get("first_name", "")
                    course_obj = lesson.get("sub_course") or lesson.get("course") or {}
                    level = course_obj.get("name", {}).get("uz", "?")
                    end_date = lesson.get("group_end_date", "")
                    dl = _days_left(end_date)
                    text = f"#{gid}\n{teacher}\n{level}"
                    if key in active:
                        active[key]["text"] += f"\n——\n{text}"
                        active[key]["days"] = min(active[key]["days"], dl)
                    else:
                        active[key] = {"text": text, "days": dl}
                else:  # status == 1
                    planned[key] = True
            return active, planned

        raw_odd, planned_odd = collect_raw(schedule["odd"])
        raw_even, planned_even = collect_raw(schedule["even"])

        # Determine which time slots have ANY data across both sections
        active_times = set()
        for (ti, _) in list(raw_odd.keys()) + list(raw_even.keys()):
            active_times.add(ti)
        # Also include times from planned groups
        for ti in list(planned_odd.keys()) + list(planned_even.keys()):
            active_times.add(ti)
        # Also keep 18:00 as minimum (always show it)
        active_times.add(TIME_TO_MATRIX_ROW.get("18:00", 5))

        # Build filtered time slots (only active ones)
        filtered_slots = [t for i, t in enumerate(TIME_SLOTS) if i in active_times]
        filtered_count = len(filtered_slots)
        # Remap time_idx to new row positions
        old_to_new = {}
        new_idx = 0
        for i, t in enumerate(TIME_SLOTS):
            if i in active_times:
                old_to_new[i] = new_idx
                new_idx += 1

        # Calculate total rows
        toq_end = 2 + filtered_count  # label(1) + header(1) + data
        sep1_row = toq_end
        juft_start = sep1_row + 1
        juft_end = juft_start + 2 + filtered_count
        sep2_row = juft_end
        leg_start = sep2_row + 1
        TOTAL_ROWS = leg_start + 5  # ranglar + qizil + sariq + yashil + ⏳

        matrix = [[""] * MC for _ in range(TOTAL_ROWS)]
        all_data = {}

        def fill_filtered(raw, base_row, section_label):
            data = {}
            # Section label
            matrix[base_row][0] = section_label
            # Soat / xona header
            matrix[base_row + 1][0] = "Soat / xona"
            for xi, xona in enumerate(XONALAR):
                matrix[base_row + 1][1 + xi] = xona
            # Time rows
            for old_ti, new_ti in old_to_new.items():
                matrix[base_row + 2 + new_ti][0] = TIME_SLOTS[old_ti]

            # Fill data
            for (old_ti, ci), info in raw.items():
                new_ti = old_to_new.get(old_ti)
                if new_ti is None:
                    continue
                ri = base_row + 2 + new_ti
                dc = ci + 1
                matrix[ri][dc] = info["text"]
                data[(ri, dc)] = {"text": info["text"], "days": info["days"]}

            # Bo'sh kataklar
            for new_ti in range(filtered_count):
                for xi in range(XONA_COUNT):
                    ri = base_row + 2 + new_ti
                    dc = xi + 1
                    if (ri, dc) not in data:
                        s = "Dars yo'q slot"
                        matrix[ri][dc] = s
                        data[(ri, dc)] = {"text": s, "days": -1}

            return data

        toq_data = fill_filtered(raw_odd, toq_base, "TOQ")
        all_data.update(toq_data)
        juft_data = fill_filtered(raw_even, juft_start, "JUFT")
        all_data.update(juft_data)

        # Planned guruhlarni overlay — faqat "Dars yo'q slot" kataklarga ⏳
        planned_count = 0
        for planned_dict, base_row in [(planned_odd, toq_base), (planned_even, juft_start)]:
            for (old_ti, ci) in planned_dict:
                new_ti = old_to_new.get(old_ti)
                if new_ti is None:
                    continue
                ri = base_row + 2 + new_ti
                dc = ci + 1
                current = matrix[ri][dc] if ri < len(matrix) and dc < len(matrix[ri]) else ""
                if current == "Dars yo'q slot":
                    matrix[ri][dc] = "⏳"
                    all_data[(ri, dc)] = {"text": "⏳", "days": -2}  # -2 = planned
                    planned_count += 1

        # Legend
        matrix[leg_start][0] = "Ranglar:"
        matrix[leg_start + 1][0] = "Qizil — 2 haftadan kam"
        matrix[leg_start + 2][0] = "Sariq — 1 oygacha"
        matrix[leg_start + 3][0] = "Yashil — 1 oydan ko'p"
        matrix[leg_start + 4][0] = "⏳ — ochilishi kutilmoqda"

        # ====== WRITE DATA ======
        last_col = chr(65 + MC - 1)
        sheet.update(f"A1:{last_col}{TOTAL_ROWS}", matrix)

        # ====== USTOZLAR BAND/BO'SH SLOT JADVALI (O:AA) ======
        requests = []
        # Eski slot jadvalini tozalash (O:AC ustunlari)
        try:
            sheet.batch_clear(["O1:AC30"])
        except Exception as e:
            logger.warning(f"slot clear: {str(e)[:100]}")

        busy_count = write_teacher_slots(sheet, schedule, sheet_id, requests)

        # ====== FORMATTING ======

        def _fmt(sr, er, sc, ec, f):
            return {
                "repeatCell": {
                    "range": {"sheetId": sheet_id,
                              "startRowIndex": sr, "endRowIndex": er,
                              "startColumnIndex": sc, "endColumnIndex": ec},
                    "cell": {"userEnteredFormat": f},
                    "fields": "userEnteredFormat",
                }
            }

        # Section labels (TOQ/JUFT)
        for sr in [toq_base, juft_start]:
            requests.append(_fmt(sr, sr + 1, 0, MC, {
                "textFormat": {"bold": True, "fontSize": 11},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "borders": BORDER_GRAY,
            }))

        # Soat / xona headers
        for sr in [toq_base + 1, juft_start + 1]:
            requests.append(_fmt(sr, sr + 1, 0, MC, {
                "backgroundColor": COLOR_HEADER,
                "textFormat": {"bold": True, "fontSize": 10},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "borders": BORDER_GRAY,
            }))

        # Time labels (A column, bold)
        for base in [toq_base + 2, juft_start + 2]:
            requests.append(_fmt(base, base + filtered_count, 0, 1, {
                "textFormat": {"bold": True, "fontSize": 10},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "borders": BORDER_GRAY,
            }))

        # All data cells: base format
        for base in [toq_base + 2, juft_start + 2]:
            requests.append(_fmt(base, base + filtered_count, 0, MC, {
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "wrapStrategy": "WRAP",
                "borders": BORDER_GRAY,
            }))

        # Individual cell colors
        for (ri, dc), info in all_data.items():
            clr = _color_by_days(info["days"])
            font_size = 15 if info["days"] == -2 else 9  # ⏳ kattaroq
            cell_fmt = {
                "backgroundColor": clr,
                "textFormat": {"fontSize": font_size},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "borders": BORDER_GRAY,
            }
            if info["days"] < 0 and info["days"] != -2:
                cell_fmt["textFormat"]["foregroundColor"] = {"red": 0.5, "green": 0.5, "blue": 0.5}
            requests.append(_fmt(ri, ri + 1, dc, dc + 1, cell_fmt))

        # Legend: color blocks + borders
        legend_colors = [
            (leg_start, COLOR_BLUE),
            (leg_start + 1, COLOR_RED),
            (leg_start + 2, COLOR_YELLOW),
            (leg_start + 3, COLOR_GREEN),
            (leg_start + 4, COLOR_HEADER),
        ]
        for lr, clr in legend_colors:
            requests.append(_fmt(lr, lr + 1, 0, 1, {
                "backgroundColor": clr,
                "textFormat": {"fontSize": 9},
                "borders": BORDER_GRAY,
            }))
            requests.append(_fmt(lr, lr + 1, 1, MC, {
                "textFormat": {"fontSize": 9},
                "borders": BORDER_GRAY,
            }))

        # Column widths
        requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                          "startIndex": 0, "endIndex": 1},
                "properties": {"pixelSize": 80}, "fields": "pixelSize",
            }
        })
        for ci in range(1, MC):
            requests.append({
                "updateDimensionProperties": {
                    "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                              "startIndex": ci, "endIndex": ci + 1},
                    "properties": {"pixelSize": 120}, "fields": "pixelSize",
                }
            })

        # Row heights
        for ri in range(TOTAL_ROWS):
            is_label = ri in [toq_base, juft_start, toq_base + 1, juft_start + 1]
            h = 50 if is_label else 45
            requests.append({
                "updateDimensionProperties": {
                    "range": {"sheetId": sheet_id, "dimension": "ROWS",
                              "startIndex": ri, "endIndex": ri + 1},
                    "properties": {"pixelSize": h}, "fields": "pixelSize",
                }
            })

        # Batch execute
        for i in range(0, len(requests), 50):
            batch = requests[i:i + 50]
            try:
                ss.batch_update({"requests": batch})
            except Exception as e:
                logger.warning(f"Batch {i // 50}: {str(e)[:120]}")

        odd_count = len(schedule["odd"])
        even_count = len(schedule["even"])
        return (
            f"✅ Dars jadvali Google Sheets ga yozildi!\n\n"
            f"📊 Toq kunlar: {odd_count} ta dars\n"
            f"📊 Juft kunlar: {even_count} ta dars\n"
            f"⏳ Kutilayotgan guruhlar: {planned_count} ta\n"
            f"👨🏻‍🏫 Ustozlar slot jadvali: O2:AA14 ({len(TEACHER_COLUMNS)} ustoz, {busy_count} ta band slot)\n"
            f"📋 Sheet: {SHEET_NAME}\n"
            f"⏰ Vaqtlar: {', '.join(TIME_SLOTS)}"
        )

    except Exception as e:
        logger.error(f"Sheets export error: {e}")
        return f"❌ Xatolik: {str(e)[:200]}"
