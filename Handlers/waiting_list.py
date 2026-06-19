"""
📋 Kutish ro'yxati handler
"""
import asyncio, re, json, logging, os
from datetime import datetime, timezone, timedelta
from urllib.parse import unquote
from html import unescape
import requests
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import config

waitlist_router = Router()

# KONFIG
LMS_BASE = os.getenv("LMS_BASE_URL", "https://main.ieltszoneapp.uz")
LMS_EMAIL = os.getenv("LMS_EMAIL", "makhmudov15max@gmail.com")
LMS_PASSWORD = os.getenv("LMS_PASSWORD", "1qa2ws3ed")
BRANCH_ID = int(os.getenv("LMS_BRANCH_ID", "3"))

try:
    ADMIN_ID = int(config.ADMIN_ID)
except:
    ADMIN_ID = 6500594896
UZ_TZ = timezone(timedelta(hours=5))



# ================= LMS SESSIYA =================
_lms_session = None


def _lms_login():
    global _lms_session
    if _lms_session is not None:
        return _lms_session
    session = requests.Session()
    resp = session.get(f"{LMS_BASE}/admin/login", timeout=15)
    match = re.search(r'data-page="([^"]*)"', resp.text)
    if not match:
        raise RuntimeError("LMS login: data-page topilmadi")
    page = json.loads(unescape(match.group(1)))
    csrf = page["props"]["csrf_token"]
    session.post(f"{LMS_BASE}/admin/login", data={
        "_token": csrf, "email": LMS_EMAIL, "password": LMS_PASSWORD,
    }, timeout=15)
    _lms_session = session
    return session


def _inertia_get(session, url):
    resp = session.get(url, timeout=20)
    match = re.search(r'data-page="([^"]*)"', resp.text)
    if not match:
        return None
    return json.loads(unescape(match.group(1)))


def _parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _format_date_uz(date_val):
    if date_val is None:
        return "ko'rsatilmagan"
    months = ["yanvar","fevral","mart","aprel","may","iyun",
              "iyul","avgust","sentabr","oktabr","noyabr","dekabr"]
    return f"{date_val.day}-{months[date_val.month-1]}"


def _get_date_diff(date_val):
    if date_val is None:
        return None
    return (date_val - datetime.now(UZ_TZ).date()).days


def _get_latest_comment(student_id, session):
    try:
        url = f"{LMS_BASE}/admin/users/{student_id}/comments"
        resp = session.get(url, headers={"Accept": "application/json"}, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        comments = data.get("comments", [])
        if not comments:
            return None
        latest = max(comments, key=lambda c: c.get("created_at", ""))
        return {
            "text": (latest.get("details") or {}).get("comment", ""),
            "date": latest.get("created_at", ""),
        }
    except Exception:
        return None


def _fetch_waitlist_data():
    session = _lms_login()
    all_items = []
    for pg in [1, 2, 3]:
        url = f"{LMS_BASE}/admin/waiting?branch_id={BRANCH_ID}&sort=id&page={pg}"
        page_data = _inertia_get(session, url)
        if not page_data:
            break
        sd = page_data["props"]["courseStudents"]
        items = sd["data"]
        if not items:
            break
        all_items.extend(items)
        if pg >= sd.get("last_page", 1):
            break
    return all_items


def _format_lead(idx, lead):
    t = f"\n<b>{idx}. 👤 {lead['name']}</b>\n"
    t += f"   📞 {lead['phone']}\n"
    t += f"   📚 {lead['course']}\n"
    t += f"   👨‍💼 Admin: {lead['admin']}\n"
    if lead["planned"]:
        days = lead["days_diff"]
        ds = _format_date_uz(lead["planned"])
        if days is not None and days < 0:
            t += f"   📅 Kelish sanasi: {ds} ⚠️ <b>{abs(days)} kun o'tgan</b>\n"
        elif days == 0:
            t += f"   📅 Kelish sanasi: {ds} — <b>Bugun!</b>\n"
        elif days == 1:
            t += f"   📅 Kelish sanasi: {ds} — ertaga\n"
        else:
            t += f"   📅 Kelish sanasi: {ds} ({days} kun qoldi)\n"
    else:
        t += f"   📅 Kelish sanasi: ko'rsatilmagan ⚠️\n"
    if lead["comment"]:
        t += f"   📝 Izoh: \"{lead['comment']}\"\n"
    else:
        t += "   📝 Izoh: <i>yo'q</i> ❗\n"
    if lead["comment_date"]:
        cd = _parse_date(lead["comment_date"][:10])
        if cd:
            t += f"   🕐 Oxirgi izoh: {_format_date_uz(cd)}\n"
    return t


async def _build_report():
    items = await asyncio.to_thread(_fetch_waitlist_data)
    session = _lms_session
    today = datetime.now(UZ_TZ).date()
    if not items:
        return "📋 Kutish ro'yxati bo'sh yoki LMS ulanishda xatolik."

    latest_comments = {}
    for item in items:
        sid = item["student_id"]
        latest = await asyncio.to_thread(_get_latest_comment, sid, session)
        latest_comments[item["id"]] = latest

    no_date, past_date, future_date = [], [], []
    for item in items:
        name = item["student"]["full_name"]
        phone = item["student"]["phone"]
        course = item["course"]["full_course_name"]
        employee = (item.get("employee") or {}).get("full_name", "—")
        entry_comment = (item.get("comment") or "").strip()
        planned = _parse_date(item.get("planned_first_lesson_date"))
        days_diff = _get_date_diff(planned)
        created = item["created_at"]
        lc = latest_comments.get(item["id"])
        lc_text = lc["text"] if lc else ""
        lc_date = lc["date"] if lc and lc["date"] else created
        lead_info = {
            "name": name, "phone": phone, "course": course,
            "admin": employee, "planned": planned, "days_diff": days_diff,
            "comment": lc_text or entry_comment, "comment_date": lc_date,
        }
        if planned is None:
            no_date.append(lead_info)
        elif days_diff is not None and days_diff < 0:
            past_date.append(lead_info)
        else:
            future_date.append(lead_info)

    today_str = today.strftime("%d-%B, %Y")
    text = f"📋 <b>KUTISH RO'YXATI — Drujba filial</b>\n"
    text += f"📊 Jami: <b>{len(items)} ta</b> lead | {today_str}\n"
    text += "━" * 35 + "\n"
    idx = 0

    if past_date:
        text += "\n🔴 <b>SANA O'TGAN</b>\n"
        for lead in sorted(past_date, key=lambda x: x["days_diff"] or 0):
            idx += 1; text += _format_lead(idx, lead)
    if future_date:
        text += "\n🟢 <b>KELAJAK SANA</b>\n"
        for lead in sorted(future_date, key=lambda x: x["days_diff"] or 999):
            idx += 1; text += _format_lead(idx, lead)
    if no_date:
        text += "\n⚪ <b>SANA KO'RSATILMAGAN</b>\n"
        for lead in no_date:
            idx += 1; text += _format_lead(idx, lead)

    text += "\n" + "━" * 35 + "\n🧠 <b>ANALIZ VA TAVSIYALAR</b>\n\n"

    if past_date:
        text += "⚠️ <b>Sana o'tgan leadlar:</b>\n"
        for lead in past_date:
            d = _format_date_uz(lead["planned"])
            days = abs(lead["days_diff"])
            text += f"   • {lead['name']} — {d} ({days} kun o'tgan)\n"
            if lead["comment"]:
                text += f'     Izoh: "{lead["comment"]}"\n'
            else:
                text += "     ❗ Izoh yo'q — admin <b>gaplashmagan!</b>\n"
        text += "\n"

    vague = []
    no_comment_past = [l for l in past_date if not l["comment"]]
    for lead in past_date + future_date + no_date:
        c = lead["comment"].strip()
        if c and len(c) < 10 and not any(w in c.lower() for w in ["keldi","boshladi","gaplashdim","qongiroq"]):
            vague.append(lead)

    if no_comment_past:
        text += "❗ <b>Admin gaplashmagan:</b>\n"
        for lead in no_comment_past:
            text += f"   • {lead['name']} — bog'lanish kerak!\n"
        text += "\n"
    if vague:
        text += "📌 <b>Izoh aniq emas:</b>\n"
        for lead in vague[:5]:
            text += f'   • {lead["name"]}: "{lead["comment"]}"\n'
        text += "\n"

    soon = [l for l in future_date if l["days_diff"] is not None and l["days_diff"] <= 3]
    if soon:
        text += "📅 <b>Yaqin kunlarda (1-3 kun):</b>\n"
        for lead in soon:
            text += f"   • {lead['name']} — {_format_date_uz(lead['planned'])}\n"
        text += "\n"

    text += "✅ <b>Umumiy holat:</b>\n"
    text += f"   Jami {len(items)} ta lead. "
    if no_date:
        text += f"{len(no_date)} ta leadda sana yo'q. "
    if past_date:
        text += f"{len(past_date)} ta leadning sanasi o'tgan. "
    if not past_date and not no_comment_past:
        text += "Vaziyat nazoratda. "
    text += "\n"
    return text


@waitlist_router.message(F.text == "📋 Kutish ro'yxati")
async def waiting_list_handler(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    from Handlers.group_report import is_admin
    if not await is_admin(int(user_id)):
        await message.answer("❌ Bu bo'lim faqat adminlar uchun.")
        return
    await message.answer("⏳ Kutish ro'yxati yuklanmoqda...", parse_mode="HTML")
    try:
        report = await _build_report()
        if len(report) > 4000:
            parts = []; current = ""
            for line in report.split("\n"):
                if len(current) + len(line) + 1 > 4000:
                    parts.append(current); current = line
                else:
                    current += "\n" + line if current else line
            if current: parts.append(current)
            for part in parts:
                await message.answer(part, parse_mode="HTML")
        else:
            await message.answer(report, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Kutish ro'yxati xatosi: {e}", exc_info=True)
        await message.answer("❌ Kutish ro'yxatini yuklashda xatolik.")
