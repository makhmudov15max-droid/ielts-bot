"""
Debtors — LMS qarzdor talabalarni Google Sheets "Debs Drujba" jadvaliga yozish.
Format (dizayn proof ko`rsatilgan):
  A1  →  1-qator: sarlavhalar Ism&Familiya | Number | Balance | Deadline | Teacher&Gr ID | Latest Comment
  A2  →  --- 📌 DEBTORS ---
        DEBTORS qatorlari (Balance 0 UZS / manfiy? — status=6 debtors)
  A.. →  --- 📌 PARTIAL DEBTORS ---
        PARTIAL qatorlari (Balance musbat ijobiy)
  A.. →  --- 📌 DEBS MORE THAN A MONTH ---
        MORE qatorlari (Balance manfiy)
Balance har doim "X UZS" (Sumdagi miqdor + " UZS").
Teacher&Gr ID  →  "#<group_id> <teacher ism familiya>"
Latest Comment →  "<employee.full_name> | <dd.mm HH:MM> | <details.comment>"
"""
import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import unquote
from html import unescape

logger = logging.getLogger(__name__)

LMS_BASE = "https://main.ieltszoneapp.uz"
SHEET_ID = "1PpGWObeppzsSkaYgGz0fRYP_3zk-3YuxBOXStrn_PCc"
SHEET_NAME = "Debs Drujba"
UZ_TZ = timezone(timedelta(hours=5))

# LMS dashboard debtors tiplari
TYPE_DEBTOR = "debtor"              # asosiy qarzdorlar (status=6)
TYPE_PARTIAL = "partial-debtor"     # qisman to`laganlar (musbat qarzdorlik)
TYPE_MORE = "debtor2x"              # bir oydan ortiq qarzdorlar (manfiy)

SECTION_DEBTORS = "--- 📌 DEBTORS ---"
SECTION_PARTIAL = "--- 📌 PARTIAL DEBTORS ---"
SECTION_MORE = "--- 📌 DEBS MORE THAN A MONTH ---"

HEADERS = ["Ism&Familiya", "Number", "Balance", "Deadline", "Teacher&Gr ID", "Latest Comment"]


_lms_session = None
_teacher_map = {}


def _get_lms_session():
    """LMS'ga login va sessiya qaytaradi. Mustaqil (bot-ga bog'lanmaydi)."""
    global _lms_session, _teacher_map
    import requests
    import config

    _BASE = config.LMS_BASE if hasattr(config, 'LMS_BASE') else LMS_BASE
    _EM = getattr(config, 'LMS_EMAIL', 'makhmudov15max@gmail.com')
    # LMS_KEY — Railway'da eski env o`rnatilgan bo`lsa ham, hozirgi ishlaydigan parolni ishlatamiz.
    # (kodga maxsus yozilgan, chunki LMS paroli muhim infratuzilma kaliti)
    _KEY = 'Mahmudov02'

    if _lms_session:
        try:
            r = _lms_session.get(f"{_BASE}/admin/dashboard", timeout=10)
            if r.status_code == 200 and "data-page" in r.text:
                return _lms_session
        except Exception:
            pass

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
    })
    s.get(f"{_BASE}/sanctum/csrf-cookie")
    xsrf = s.cookies.get("XSRF-TOKEN", "")
    s.headers["X-XSRF-TOKEN"] = unquote(xsrf)
    s.headers["Content-Type"] = "application/json"
    r = s.post(f"{_BASE}/admin/login", json={"email": _EM, "password": _KEY})
    logger.info(f"debtors LMS login: {r.status_code}")

    # teacher map
    if not _teacher_map:
        try:
            r = s.get(f"{_BASE}/admin/unassessed-groups?per_page=1")
            m = re.search(r'data-page="([^"]*)"', r.text)
            if m:
                dp = json.loads(unescape(m.group(1)))
                for t in dp["props"].get("teacherOptions", []):
                    _teacher_map[t["id"]] = f"{t.get('first_name','')} {t.get('last_name','')}".strip()
            r = s.get(f"{_BASE}/admin/calculated-salaries?per_page=200")
            m = re.search(r'data-page="([^"]*)"', r.text)
            if m:
                dp = json.loads(unescape(m.group(1)))
                for emp in dp["props"].get("employees", []):
                    if emp["id"] not in _teacher_map:
                        _teacher_map[emp["id"]] = f"{emp.get('first_name','')} {emp.get('last_name','')}".strip()
        except Exception as e:
            logger.warning(f"teacher map fetch error: {e}")
    _lms_session = s
    return s


def _parse_date(dstr: str) -> str:
    """'2026-09-22' → '22.09.2026'"""
    if not dstr:
        return ""
    try:
        return datetime.strptime(str(dstr)[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except Exception:
        return str(dstr)


def _fmt_balance(balance) -> str:
    """Balansni '0 UZS' / '810000 UZS' / '-152307 UZS' qilish."""
    try:
        n = int(float(balance or 0))
    except Exception:
        n = 0
    return f"{n} UZS"


def _fmt_comment_ts(created_at: str) -> str:
    """ISO sana → 'dd.mm HH:MM' (Uzbekistan tz)."""
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00")).astimezone(UZ_TZ)
        return dt.strftime("%d.%m %H:%M")
    except Exception:
        return ""


# ---- Rang xilma-xilligi (deadline o'tgan kunlar bo'yicha) ----
COLOR_YELLOW = {"red": 1.0, "green": 1.0, "blue": 0.6}       # sariq (1-6 debtors / 1-10 partial)
COLOR_LIGHT_RED = {"red": 1.0, "green": 0.6, "blue": 0.6}    # och qizil (7-10 debtors)
COLOR_DARK_RED = {"red": 0.7, "green": 0.1, "blue": 0.1}      # to'q qizil (11+ / more)

def _is_26(note):
    """note ichida '2+6' (har xil yozilish) borligini tekshiradi."""
    if not note:
        return False
    n = str(note).lower().replace(" ", "").replace("\u00a0", "")
    return "2+6" in n


def _days_past_deadline(deadline_str: str) :
    """deadline'dan bugungacha o'tgan kunlar soni. Kelajakda bo'lsa manfiy/0."""
    try:
        dl = datetime.strptime(str(deadline_str)[:10], "%d.%m.%Y")
    except Exception:
        try:
            dl = datetime.strptime(str(deadline_str)[:10], "%Y-%m-%d")
        except Exception:
            return None
    dl = dl.replace(tzinfo=UZ_TZ)  # aware qilish
    today = datetime.now(UZ_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    return (today - dl).days


def _row_color(dtype, deadline_str, is_26_note):
    """Qator uchun fon rangini qaytaradi (dict) yoki None (ranglanmaydi)."""
    if is_26_note:
        return None  # 2+6 loyiha o'quvchilari ranglanmaydi
    if dtype == TYPE_MORE:
        return COLOR_DARK_RED
    days = _days_past_deadline(deadline_str)
    if days is None or days <= 0:
        return None  # deadline kelajakda/bugun — hali vaqti bor
    if dtype == TYPE_DEBTOR:
        if 1 <= days <= 6:
            return COLOR_YELLOW
        if 7 <= days <= 10:
            return COLOR_LIGHT_RED
        return COLOR_DARK_RED
    if dtype == TYPE_PARTIAL:
        if 1 <= days <= 10:
            return COLOR_YELLOW
        return COLOR_DARK_RED
    return None


def fetch_debtor_page(session, dtype: str, page: int):
    """Bir sahifadagi qarzdorlar. Dict qaytaradi yoki None xatolikda."""
    import requests
    url = f"{LMS_BASE}/admin/dashboard/debtors?search=&status=6&type={dtype}&page={page}"
    r = session.get(url, timeout=30)
    if r.status_code != 200:
        logger.error(f"debtors fetch fail {dtype} page {page}: {r.status_code}")
        return None
    m = re.search(r'data-page="([^"]*)"', r.text)
    if not m:
        return None
    dp = json.loads(unescape(m.group(1)))
    return dp.get("props", {}).get("students", {})


def _last_comment(session, student_id: int):
    """Oxirgi izohni qaytaradi.
    Qaytaradi: (matn_str, created_at_iso, author_full_name)
    matn: 'Muallif | dd.mm HH:MM | matn' ko`rinishida.
    """
    try:
        r = session.get(f"{LMS_BASE}/admin/users/{student_id}/comments", timeout=15)
        if r.status_code != 200:
            return ("", "", "")
        data = r.json()
        comments = data.get("comments", [])
        if not comments:
            return ("", "", "")
        c = comments[-1]  # oxirgi = eng yangi
        emp = (c.get("employee") or {})
        author = emp.get("full_name", "") or ""
        ts = _fmt_comment_ts(c.get("created_at", ""))
        text = (c.get("details") or {}).get("comment", "") or ""
        parts = [p for p in [author, ts, text] if p]
        return (" | ".join(parts), c.get("created_at", ""), author)
    except Exception as e:
        logger.warning(f"comments fail {student_id}: {e}")
        return ("", "", "")


def _teacher_for_group(tmap, sg: dict) -> str:
    """'#1311 Ahmadali Turgunov' yoki faqat guruh nomi."""
    gid = sg.get("id")
    tid = sg.get("teacher_id")
    if tid:
        name = tmap.get(tid, "")
    else:
        name = ""
    # agar teacher nomaqbul, guruh nomini ishlatamiz
    if not name:
        name = (sg.get("name") or "").strip()
    return f"#{gid} {name}".strip()


def _deadline_for_group(sg: dict) -> str:
    """pivot.payment_date → '22.09.2026'"""
    default = sg.get("next_write_off_date") or (sg.get("group_end_date") or "")
    try:
        pd = (sg.get("pivot") or {}).get("payment_date")
    except Exception:
        pd = None
    return _parse_date(pd or default or "")


def fetch_all_students(session, dtype: str, tmap: dict):
    """Barcha sahifalarni aylanib, ishlangan satrlar va comment statistika qaytaradi.
    Qaytaradi: (rows, stats) — stats = {'dates': {...}, 'authors': {...}}
    """
    page = 1
    rows = []
    stats = {"dates": {}, "authors": {}}  # '18.08' -> count, author -> count
    colors = []  # har row uchun fon rangi (dict yoki None)
    while True:
        pg = fetch_debtor_page(session, dtype, page)
        if not pg:
            break
        data = pg.get("data", []) or []
        for st in data:
            sg = (st.get("student_groups") or [{}])[0]  # asosiy guruh
            comment_text, created_at, author = _last_comment(session, st.get("id"))
            # '2+6' loyiha o'quvchisi — eslatma (note) maydonida
            note = st.get("note") or ""
            is_26 = _is_26(note)
            full_name = st.get("full_name", "")
            if is_26:
                full_name = f"{full_name} (2+6)"
            deadline = _deadline_for_group(sg or {})
            row = [
                full_name,
                str(st.get("phone", "") or ""),
                _fmt_balance(st.get("student_balance")),
                deadline,
                _teacher_for_group(tmap, sg or {}),
                comment_text,
            ]
            rows.append(row)
            colors.append(_row_color(dtype, deadline, is_26))
            logger.info(f"  [{dtype}] {row[0]} balance={row[2]} comment={comment_text[:40]}")

            # statistika — izoh sanasi (dd.mm) va muallif
            if created_at:
                dkey = _fmt_comment_ts(created_at).split(" ")[0]  # '25.08'
                stats["dates"][dkey] = stats["dates"].get(dkey, 0) + 1
            if author:
                stats["authors"][author] = stats["authors"].get(author, 0) + 1
        pag = pg.get("current_page", 1)
        last = pg.get("last_page", pag)
        if pag >= last:
            break
        page += 1
    return rows, stats, colors


def _write_to_sheets(all_rows: dict, all_colors: dict = None):
    """Bo`limlar ketma-ketligida jadvalga yozish. all_colors: {dtype: [color|None, ...]}"""
    import gspread
    creds_json = os.getenv("GOOGLE_CREDS")
    if not creds_json:
        raise RuntimeError("GOOGLE_CREDS topilmadi")
    creds = json.loads(creds_json)
    client = gspread.service_account_from_dict(creds)
    ss = client.open_by_key(SHEET_ID)
    ws = ss.worksheet(SHEET_NAME)

    # Jadvalni tozalash (A1:F210 kontenti)
    ws.clear()

    # Butun F hududini oddiy formatga qaytarish (oq bg, bold emas, font size 10, Arial)
    # — eski qo'lda qo'yilgan ko'k/bold/katta font format yangi qatorlarga ko'chmasligi uchun
    try:
        ws.format("A1:F500", {
            "backgroundColor": {"red": 1, "green": 1, "blue": 1},
            "textFormat": {
                "bold": False,
                "fontSize": 10,
                "fontFamily": "Arial",
                "foregroundColor": {"red": 0, "green": 0, "blue": 0}
            }
        })
    except Exception as _e:
        logger.warning(f"format reset fail: {_e}")

    # Bo`limlar ketma-ketligini qurish
    blocks = [
        (SECTION_DEBTORS, TYPE_DEBTOR, all_rows.get(TYPE_DEBTOR, [])),
        (SECTION_PARTIAL, TYPE_PARTIAL, all_rows.get(TYPE_PARTIAL, [])),
        (SECTION_MORE, TYPE_MORE, all_rows.get(TYPE_MORE, [])),
    ]

    # Sarlavha + barcha qatorlarni yig`amiz
    grid = []
    grid.append(HEADERS)
    row_color_map = {}  # sheet row index (0-based) -> color dict
    for section, dtype, rows in blocks:
        if not rows:
            continue
        grid.append([section, "", "", "", "", ""])
        # Bu bo'limga tegishli colors ro'yxati
        c_list = (all_colors or {}).get(dtype, [])
        for i, r in enumerate(rows):
            grid.append(r)
            col = c_list[i] if i < len(c_list) else None
            if col:
                row_color_map[len(grid) - 1] = col

    start = "A1"
    end = f"F{len(grid)}"
    ws.update(range_name=f"{start}:{end}", values=grid, value_input_option="USER_ENTERED")

    # Sarlavha qalin + bo`lim sarlavhalari rangli
    ws.format("A1:F1", {"textFormat": {"bold": True}})

    # Horizontal align qoidasi (A=LEFT, B=RIGHT, C-F=LEFT) — barcha qatorlar
    try:
        from google.oauth2 import service_account as _saH
        from googleapiclient.discovery import build as _buildH
        _scopeH = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        _crH = _saH.Credentials.from_service_account_info(json.loads(creds_json), scopes=_scopeH)
        _svcH = _buildH("sheets", "v4", credentials=_crH)
        align_reqs = [
            {"repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 0, "endRowIndex": 500, "startColumnIndex": 0, "endColumnIndex": 1},
                            "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat.horizontalAlignment"}},
            {"repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 0, "endRowIndex": 500, "startColumnIndex": 1, "endColumnIndex": 2},
                            "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat.horizontalAlignment"}},
            {"repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 0, "endRowIndex": 500, "startColumnIndex": 2, "endColumnIndex": 6},
                            "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat.horizontalAlignment"}},
        ]
        _svcH.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": align_reqs}).execute()
    except Exception as _eh:
        logger.warning(f"align fail: {_eh}")

    # Bo`lim sarlavhalari (--- 📌 ... ---) to`q ko`k fon + oq qalin
    reqs_format = []
    for row_i, row in enumerate(grid):
        if row and row[0].startswith("---"):
            reqs_format.append({
                "repeatCell": {
                    "range": {"sheetId": ws.id, "startRowIndex": row_i, "endRowIndex": row_i + 1, "startColumnIndex": 0, "endColumnIndex": 6},
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": {"red": 0.13, "green": 0.32, "blue": 0.58},
                        "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
                    }},
                    "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat.bold,userEnteredFormat.textFormat.fontSize,userEnteredFormat.textFormat.foregroundColor"
                }
            })
    # Qarzdorlik darajasi bo'yicha rangli qatorlar (deadline o'tgan kunlarga qarab)
    for row_i, col in row_color_map.items():
        reqs_format.append({
            "repeatCell": {
                "range": {"sheetId": ws.id, "startRowIndex": row_i, "endRowIndex": row_i + 1, "startColumnIndex": 0, "endColumnIndex": 6},
                "cell": {"userEnteredFormat": {"backgroundColor": col}},
                "fields": "userEnteredFormat.backgroundColor"
            }
        })
    if reqs_format:
        from google.oauth2 import service_account as _sa2
        from googleapiclient.discovery import build as _build2
        _scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        _c2 = _sa2.Credentials.from_service_account_info(json.loads(creds_json), scopes=_scopes)
        _svc2 = _build2("sheets", "v4", credentials=_c2)
        _svc2.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": reqs_format}).execute()
    return len(grid)


def _create_charts(all_stats: dict):
    """Har bir bo`lim uchun 2 tadan diagramma (bar sana + pie hodim) yaratadi.
    Joylashuv: foydalanuvchi qo`lda belgilagan aniq koordinatalar:
      DEBTORS: bar (col6, row0), pie (col10, row0)
      PARTIAL: bar (col6, row13), pie (col10, row13)
      MORE:    bar (col6, row28), pie (col10, row28)
    Diagramma data'si H/K ustunlarda, matn rangi oq (ko`rinmaydi).
    """
    import gspread
    from google.oauth2 import service_account as _sa
    from googleapiclient.discovery import build as _build

    creds_json = os.getenv("GOOGLE_CREDS")
    if not creds_json:
        return
    _scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    _creds = _sa.Credentials.from_service_account_info(json.loads(creds_json), scopes=_scopes)
    _svc = _build("sheets", "v4", credentials=_creds)

    client = gspread.service_account_from_dict(json.loads(creds_json))
    ss = client.open_by_key(SHEET_ID)
    ws = ss.worksheet(SHEET_NAME)
    GID = ws.id

    # Avval mavjud diagrammalarni o`chirish (qayta run uchun)
    try:
        meta = _svc.spreadsheets().get(spreadsheetId=SHEET_ID, fields="sheets(properties(title),charts(chartId))").execute()
    except Exception:
        meta = None
    if meta:
        del_reqs = []
        for s in meta.get("sheets", []):
            if s.get("properties", {}).get("title") == SHEET_NAME:
                for ch in s.get("charts", []):
                    del_reqs.append({"deleteEmbeddedObject": {"objectId": ch["chartId"]}})
                break
        if del_reqs:
            try:
                _svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": del_reqs}).execute()
            except Exception:
                pass

    # Bugundan 6 kun orqaga sanalar (dd.mm)
    from datetime import datetime, timezone, timedelta
    now = datetime.now(UZ_TZ)
    days = [(now - timedelta(days=i)).strftime("%d.%m") for i in reversed(range(6))]
    # days = [21.08, 22.08, ..., 26.08]

    # Bo`limlar uchun diagramma koordinatalari (foydalanuvchi belgilagan)
    layout = {
        TYPE_DEBTOR: {"anchor_row": 0, "data_row": 1},
        TYPE_PARTIAL: {"anchor_row": 13, "data_row": 14},
        TYPE_MORE: {"anchor_row": 28, "data_row": 24},
    }

    reqs = []
    sect_titles = {
        TYPE_DEBTOR: "DEBTORS",
        TYPE_PARTIAL: "PARTIAL",
        TYPE_MORE: "MORE",
    }
    for dtype, stats in all_stats.items():
        if not stats:
            continue
        anchor_row = layout[dtype]["anchor_row"]
        ar = anchor_row  # row index (0-based) — siz belgilagan

        # sana bo'yicha data → data zonalariga yozamiz
        # sana stat (stats['dates'] '25.08' -> count)
        # 6 kunlik oynaga to`g`rilab data qatorini quramiz
        sana_rows = [["Sana", "Izohlar"]]
        for d in days:
            sana_rows.append([d, stats["dates"].get(d, 0)])

        # hodim stat
        hodim_rows = [["Hodim", "Izohlar"]]
        for k, v in sorted(stats["authors"].items(), key=lambda x: -x[1]):
            hodim_rows.append([k, v])

        # Sana data: H ustun (col7) — anchor_row+1 dan
        h_start = anchor_row + 1
        # Hodim data: K ustun (col10) — anchor_row+1 dan
        # Diagramma data'sini hujayralarga yozamiz (updateCells, raqam int)
        def _write_block(cell_row, cell_col, rows):
            nonlocal reqs
            reqs.append({
                "updateCells": {
                    "range": {
                        "sheetId": GID,
                        "startRowIndex": cell_row,
                        "endRowIndex": cell_row + len(rows),
                        "startColumnIndex": cell_col,
                        "endColumnIndex": cell_col + 2,
                    },
                    "rows": [{"values": [{
                        "userEnteredValue": ({"numberValue": v} if isinstance(v, int) else {"stringValue": v}),
                        "userEnteredFormat": {"textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}}}
                    } for v in row]} for row in rows],
                    "fields": "userEnteredValue,userEnteredFormat.textFormat.foregroundColor"
                }
            })

        _write_block(h_start, 7, sana_rows)        # H ustun: sana data
        _write_block(h_start, 10, hodim_rows)       # K ustun: hodim data

        # Bar chart (sana) — anchor col6, offX=4
        reqs.append({
            "addChart": {
                "chart": {
                    "spec": {
                        "title": f"📅 {sect_titles[dtype]} — Izohlar sanasi",
                        "basicChart": {
                            "chartType": "COLUMN", "legendPosition": "BOTTOM_LEGEND",
                            "axis": [{"position": "BOTTOM_AXIS", "title": "Sana"}, {"position": "LEFT_AXIS", "title": "Soni"}],
                            "domains": [{"domain": {"sourceRange": {"sources": [{"sheetId": GID, "startRowIndex": h_start, "endRowIndex": h_start + len(sana_rows), "startColumnIndex": 7, "endColumnIndex": 8}]}}}],
                            "series": [{"series": {"sourceRange": {"sources": [{"sheetId": GID, "startRowIndex": h_start, "endRowIndex": h_start + len(sana_rows), "startColumnIndex": 8, "endColumnIndex": 9}]}}, "targetAxis": "LEFT_AXIS"}],
                            "headerCount": 1
                        }
                    },
                    "position": {"overlayPosition": {"anchorCell": {"sheetId": GID, "rowIndex": ar, "columnIndex": 6}, "offsetXPixels": 4, "offsetYPixels": 0 if dtype == TYPE_DEBTOR else 21, "widthPixels": 420, "heightPixels": 280}}
                }
            }
        })
        # Pie chart (hodim) — anchor col10, offX=41
        reqs.append({
            "addChart": {
                "chart": {
                    "spec": {
                        "title": f"👤 {sect_titles[dtype]} — Hodimlar",
                        "pieChart": {
                            "legendPosition": "RIGHT_LEGEND",
                            "domain": {"sourceRange": {"sources": [{"sheetId": GID, "startRowIndex": h_start, "endRowIndex": h_start + len(hodim_rows), "startColumnIndex": 10, "endColumnIndex": 11}]}},
                            "series": {"sourceRange": {"sources": [{"sheetId": GID, "startRowIndex": h_start, "endRowIndex": h_start + len(hodim_rows), "startColumnIndex": 11, "endColumnIndex": 12}]}}
                        }
                    },
                    "position": {"overlayPosition": {"anchorCell": {"sheetId": GID, "rowIndex": ar, "columnIndex": 10}, "offsetXPixels": 41, "offsetYPixels": 0 if dtype == TYPE_DEBTOR else 21, "widthPixels": 420, "heightPixels": 280}}
                }
            }
        })

    if reqs:
        _svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": reqs}).execute()


def run_export() -> dict:
    """Barcha tiplarni yig`ib, sheets ga yozadi + diagrammalar yaratadi."""
    s = _get_lms_session()
    tmap = _teacher_map

    result = {}
    all_stats = {}
    all_colors = {}
    for dtype in [TYPE_DEBTOR, TYPE_PARTIAL, TYPE_MORE]:
        rows, stats, colors = fetch_all_students(s, dtype, tmap)
        result[dtype] = rows
        all_stats[dtype] = stats
        all_colors[dtype] = colors
    total = sum(len(v) for v in result.values())

    # Sheets'ga yozish
    rows_written = _write_to_sheets(result, all_colors)
    # Diagrammalar
    _create_charts(all_stats)
    return {"rows": result, "total": total, "rows_written": rows_written}
